/* ============================================================
 * SisMOM GeoTIFF reader — inline, no external dependencies.
 * Cobre o subset usado por saídas de modelos meteorológicos:
 *   - TIFF baseline (II/MM endianness, 1 IFD, strips ou tiles)
 *   - Compressão: none(1), LZW(5), Deflate(8/32946), PackBits(32773)
 *   - SampleFormat: uint(1), int(2), float(3); BitsPerSample 8/16/32
 *   - GeoTIFF tags: ModelPixelScale(33550), ModelTiepoint(33922),
 *     GDAL_NODATA(42113), GeoKeyDirectory(34735), GeoAscii(34737)
 * NÃO cobre: JPEG-in-TIFF, BigTIFF (>4 GB), CCITT fax, predictor != 1 (floats com pred 3 sim)
 *
 * API pública:
 *   decodeTIFF(arrayBuffer)            -> { width,height,data:Float32Array,nodata?,bbox?,scale?,min,max }
 *   aplicarPaleta(decoded, opts)        -> ImageData (pronto para putImageData)
 *   GT_PALETTES                         -> { viridis,jet,rdbu,gray,turbo }
 *   isGeoTiffModel(modelo)              -> bool
 * ============================================================ */
(function (root) {
    'use strict';

    /* ---------- Paletas (256 RGB cada, geradas por interpolação) ---------- */
    function makeRamp(stops) {
        // stops: [[r,g,b], ...] em N pontos igualmente espaçados; retorna Uint8Array(768)
        const out = new Uint8Array(256 * 3);
        const N = stops.length - 1;
        for (let i = 0; i < 256; i++) {
            const t = (i / 255) * N;
            const k = Math.min(N - 1, Math.floor(t));
            const f = t - k;
            const a = stops[k], b = stops[k + 1];
            out[i * 3]     = (a[0] + (b[0] - a[0]) * f) | 0;
            out[i * 3 + 1] = (a[1] + (b[1] - a[1]) * f) | 0;
            out[i * 3 + 2] = (a[2] + (b[2] - a[2]) * f) | 0;
        }
        return out;
    }

    const GT_PALETTES = {
        // Viridis (matplotlib) — 9 stops aproximados
        viridis: makeRamp([
            [68, 1, 84], [72, 35, 116], [64, 67, 135], [52, 94, 141],
            [41, 120, 142], [32, 144, 140], [34, 167, 132], [68, 190, 112],
            [121, 209, 81], [189, 222, 38], [253, 231, 36]
        ]),
        // Jet — clássico meteo (azul→vermelho)
        jet: makeRamp([
            [0, 0, 131], [0, 60, 170], [5, 255, 255], [255, 255, 0],
            [250, 0, 0], [128, 0, 0]
        ]),
        // RdBu divergente (azul→branco→vermelho, invertido p/ anomalias frio→quente)
        rdbu: makeRamp([
            [5, 48, 97], [33, 102, 172], [67, 147, 195], [146, 197, 222],
            [209, 229, 240], [247, 247, 247], [253, 219, 199], [244, 165, 130],
            [214, 96, 77], [178, 24, 43], [103, 0, 31]
        ]),
        // Grayscale
        gray: makeRamp([[0, 0, 0], [255, 255, 255]]),
        // Turbo (Google, melhor que Jet)
        turbo: makeRamp([
            [48, 18, 59], [70, 107, 227], [40, 191, 224], [70, 250, 162],
            [186, 252, 67], [255, 192, 33], [243, 95, 30], [165, 25, 8],
            [122, 4, 3]
        ])
    };

    /* ---------- Descompressões ---------- */
    function decompressPackBits(input) {
        const out = [];
        let i = 0;
        while (i < input.length) {
            const n = input[i] > 127 ? input[i] - 256 : input[i];
            i++;
            if (n >= 0) {
                for (let k = 0; k <= n && i < input.length; k++, i++) out.push(input[i]);
            } else if (n !== -128) {
                const b = input[i++];
                for (let k = 0; k < (1 - n); k++) out.push(b);
            }
        }
        return new Uint8Array(out);
    }

    function decompressLZW(input) {
        // LZW da spec TIFF: code size começa em 9 bits, CLEAR=256, EOI=257, primeira saída em 258
        const MIN_CODE_SIZE = 8;
        const CLEAR = 256, EOI = 257;
        const out = [];
        const dict = [];
        function resetDict() {
            dict.length = 0;
            for (let i = 0; i < 256; i++) dict.push([i]);
            dict.push(null); // CLEAR
            dict.push(null); // EOI
        }
        let codeSize = MIN_CODE_SIZE + 1;
        let bitPos = 0, byteLen = input.length;
        function readCode() {
            if (bitPos + codeSize > byteLen * 8) return -1;
            // TIFF LZW: bits in MSB order
            let code = 0;
            for (let k = 0; k < codeSize; k++) {
                const bi = bitPos + k;
                const byte = input[bi >> 3];
                const bit = (byte >> (7 - (bi & 7))) & 1;
                code = (code << 1) | bit;
            }
            bitPos += codeSize;
            return code;
        }
        resetDict();
        let prev = null;
        while (true) {
            const code = readCode();
            if (code < 0) break;
            if (code === EOI) break;
            if (code === CLEAR) {
                resetDict();
                codeSize = MIN_CODE_SIZE + 1;
                prev = null;
                continue;
            }
            let entry;
            if (code < dict.length) {
                entry = dict[code];
            } else if (prev) {
                entry = prev.concat(prev[0]);
            } else {
                break;
            }
            for (let k = 0; k < entry.length; k++) out.push(entry[k]);
            if (prev) dict.push(prev.concat(entry[0]));
            prev = entry;
            // Aumenta o code size quando o dicionário enche (com 1-off da spec TIFF: aumenta ANTES)
            if (dict.length === ((1 << codeSize) - 1) && codeSize < 12) codeSize++;
        }
        return new Uint8Array(out);
    }

    async function decompressDeflate(input) {
        // Usa o DecompressionStream nativo do navegador
        const stream = new Response(new Blob([input])).body
            .pipeThrough(new DecompressionStream('deflate'));
        const ab = await new Response(stream).arrayBuffer();
        return new Uint8Array(ab);
    }

    /* ---------- TIFF parsing ---------- */
    const TYPE_SIZES = { 1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8 };

    function readTagValue(view, entry, little) {
        const { type, count, valueOffset } = entry;
        const sz = TYPE_SIZES[type] || 1;
        const total = sz * count;
        const base = total <= 4 ? entry.entryOffset + 8 : valueOffset;
        const out = [];
        for (let i = 0; i < count; i++) {
            const off = base + i * sz;
            switch (type) {
                case 1: case 7: out.push(view.getUint8(off)); break;
                case 2: out.push(view.getUint8(off)); break; // ASCII byte
                case 3: out.push(view.getUint16(off, little)); break;
                case 4: out.push(view.getUint32(off, little)); break;
                case 5: { // RATIONAL
                    const n = view.getUint32(off, little);
                    const d = view.getUint32(off + 4, little);
                    out.push(d ? n / d : 0);
                    break;
                }
                case 6: out.push(view.getInt8(off)); break;
                case 8: out.push(view.getInt16(off, little)); break;
                case 9: out.push(view.getInt32(off, little)); break;
                case 10: { // SRATIONAL
                    const n = view.getInt32(off, little);
                    const d = view.getInt32(off + 4, little);
                    out.push(d ? n / d : 0);
                    break;
                }
                case 11: out.push(view.getFloat32(off, little)); break;
                case 12: out.push(view.getFloat64(off, little)); break;
                default: out.push(view.getUint8(off));
            }
        }
        return out;
    }

    function tagAscii(arr) {
        // Remove null terminators
        let s = '';
        for (let i = 0; i < arr.length; i++) { if (arr[i] === 0) break; s += String.fromCharCode(arr[i]); }
        return s;
    }

    async function decodeTIFF(arrayBuffer) {
        const view = new DataView(arrayBuffer);
        if (arrayBuffer.byteLength < 8) throw new Error('TIFF: arquivo muito pequeno');

        // Endianness + magic
        const b0 = view.getUint8(0), b1 = view.getUint8(1);
        let little;
        if (b0 === 0x49 && b1 === 0x49) little = true;       // II
        else if (b0 === 0x4D && b1 === 0x4D) little = false; // MM
        else throw new Error('TIFF: header inválido (não é II nem MM)');

        const magic = view.getUint16(2, little);
        if (magic !== 42) throw new Error('TIFF: magic ' + magic + ' (esperado 42; BigTIFF não suportado)');

        const ifdOffset = view.getUint32(4, little);

        // Lê IFD
        const numEntries = view.getUint16(ifdOffset, little);
        const tags = {};
        for (let i = 0; i < numEntries; i++) {
            const eo = ifdOffset + 2 + i * 12;
            const entry = {
                entryOffset: eo,
                tag: view.getUint16(eo, little),
                type: view.getUint16(eo + 2, little),
                count: view.getUint32(eo + 4, little),
                valueOffset: view.getUint32(eo + 8, little)
            };
            tags[entry.tag] = readTagValue(view, entry, little);
        }

        const width = tags[256] && tags[256][0];
        const height = tags[257] && tags[257][0];
        const bitsPerSample = (tags[258] && tags[258][0]) || 8;
        const compression = (tags[259] && tags[259][0]) || 1;
        const samplesPerPixel = (tags[277] && tags[277][0]) || 1;
        const sampleFormat = (tags[339] && tags[339][0]) || 1; // default uint
        const planar = (tags[284] && tags[284][0]) || 1;
        const predictor = (tags[317] && tags[317][0]) || 1;

        if (!width || !height) throw new Error('TIFF: dimensões ausentes');
        if (samplesPerPixel > 1 && planar === 2)
            throw new Error('TIFF: planar config 2 (separate) não suportado');

        // Strips ou Tiles
        let segOffsets, segByteCounts, isTiled = false, tileW = 0, tileH = 0;
        if (tags[324]) {
            isTiled = true;
            segOffsets = tags[324];
            segByteCounts = tags[325];
            tileW = tags[322][0];
            tileH = tags[323][0];
        } else {
            segOffsets = tags[273] || [];
            segByteCounts = tags[279] || [];
        }

        // Decodifica/descomprime cada strip/tile
        const segments = [];
        for (let s = 0; s < segOffsets.length; s++) {
            const raw = new Uint8Array(arrayBuffer, segOffsets[s], segByteCounts[s]);
            let dec;
            switch (compression) {
                case 1: dec = raw; break;
                case 5: dec = decompressLZW(raw); break;
                case 8: case 32946: dec = await decompressDeflate(raw); break;
                case 32773: dec = decompressPackBits(raw); break;
                default: throw new Error('TIFF: compressão ' + compression + ' não suportada (use 1/5/8/32773)');
            }
            segments.push(dec);
        }

        // Junta segments em buffer linear (ordem: row-major)
        const bytesPerSample = bitsPerSample / 8;
        const bytesPerPixel = bytesPerSample * samplesPerPixel;
        const totalBytes = width * height * bytesPerPixel;
        const raw = new Uint8Array(totalBytes);
        if (isTiled) {
            const tilesAcross = Math.ceil(width / tileW);
            const tilesDown = Math.ceil(height / tileH);
            for (let ty = 0; ty < tilesDown; ty++) {
                for (let tx = 0; tx < tilesAcross; tx++) {
                    const seg = segments[ty * tilesAcross + tx];
                    for (let row = 0; row < tileH; row++) {
                        const y = ty * tileH + row;
                        if (y >= height) break;
                        const cols = Math.min(tileW, width - tx * tileW);
                        const srcOff = row * tileW * bytesPerPixel;
                        const dstOff = (y * width + tx * tileW) * bytesPerPixel;
                        raw.set(seg.subarray(srcOff, srcOff + cols * bytesPerPixel), dstOff);
                    }
                }
            }
        } else {
            const rowsPerStrip = (tags[278] && tags[278][0]) || height;
            let dst = 0;
            for (let s = 0; s < segments.length; s++) {
                const rowsInThisStrip = Math.min(rowsPerStrip, height - s * rowsPerStrip);
                const need = rowsInThisStrip * width * bytesPerPixel;
                raw.set(segments[s].subarray(0, need), dst);
                dst += need;
            }
        }

        // Predictor 2 (horizontal differencing) — comum em integers com LZW/Deflate
        if (predictor === 2) {
            for (let y = 0; y < height; y++) {
                const rowOff = y * width * bytesPerPixel;
                for (let x = 1; x < width; x++) {
                    for (let c = 0; c < samplesPerPixel; c++) {
                        const off = rowOff + (x * samplesPerPixel + c) * bytesPerSample;
                        const prev = rowOff + ((x - 1) * samplesPerPixel + c) * bytesPerSample;
                        if (bytesPerSample === 1) raw[off] = (raw[off] + raw[prev]) & 0xff;
                        else if (bytesPerSample === 2) {
                            const v = (raw[off] | (raw[off+1] << 8)) + (raw[prev] | (raw[prev+1] << 8));
                            raw[off] = v & 0xff; raw[off+1] = (v >> 8) & 0xff;
                        }
                    }
                }
            }
        }

        // Converte para Float32Array uniforme
        const N = width * height;
        const data = new Float32Array(N);
        const rawView = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);
        // pega só a 1ª banda (samplesPerPixel pode ser >1)
        const stride = bytesPerPixel;
        for (let i = 0; i < N; i++) {
            const off = i * stride;
            let v;
            if (sampleFormat === 3 && bitsPerSample === 32) v = rawView.getFloat32(off, little);
            else if (sampleFormat === 3 && bitsPerSample === 64) v = rawView.getFloat64(off, little);
            else if (sampleFormat === 2 && bitsPerSample === 8)  v = rawView.getInt8(off);
            else if (sampleFormat === 2 && bitsPerSample === 16) v = rawView.getInt16(off, little);
            else if (sampleFormat === 2 && bitsPerSample === 32) v = rawView.getInt32(off, little);
            else if (bitsPerSample === 8)  v = raw[off];
            else if (bitsPerSample === 16) v = rawView.getUint16(off, little);
            else if (bitsPerSample === 32) v = rawView.getUint32(off, little);
            else throw new Error('TIFF: BitsPerSample ' + bitsPerSample + ' não suportado');
            data[i] = v;
        }

        // GeoTIFF tags
        const nodataStr = tags[42113] ? tagAscii(tags[42113]) : null;
        const nodata = (nodataStr != null && nodataStr !== '') ? parseFloat(nodataStr) : null;
        let bbox = null, scale = null;
        if (tags[33550] && tags[33922]) {
            const sx = tags[33550][0], sy = tags[33550][1];
            const tp = tags[33922];
            const I = tp[0], J = tp[1], X = tp[3], Y = tp[4];
            const minX = X - I * sx;
            const maxY = Y + J * sy;
            const maxX = minX + width * sx;
            const minY = maxY - height * sy;
            bbox = { minX, minY, maxX, maxY };
            scale = { sx, sy };
        }

        // min/max (ignorando NaN/nodata)
        let mn = Infinity, mx = -Infinity;
        for (let i = 0; i < N; i++) {
            const v = data[i];
            if (!isFinite(v)) continue;
            if (nodata != null && v === nodata) continue;
            if (v < mn) mn = v;
            if (v > mx) mx = v;
        }
        if (!isFinite(mn)) { mn = 0; mx = 1; }

        return { width, height, data, nodata, bbox, scale, min: mn, max: mx };
    }

    /* ---------- Paleta -> ImageData ---------- */
    function aplicarPaleta(decoded, opts) {
        const { width, height, data, nodata } = decoded;
        const palName = (opts && opts.paleta) || 'viridis';
        const pal = GT_PALETTES[palName] || GT_PALETTES.viridis;
        const min = (opts && opts.min != null) ? opts.min : decoded.min;
        const max = (opts && opts.max != null) ? opts.max : decoded.max;
        const range = (max - min) || 1;
        const flipY = opts && opts.flipY === true;
        const N = width * height;
        const rgba = new Uint8ClampedArray(N * 4);
        for (let i = 0; i < N; i++) {
            const v = data[i];
            const isNoData = (!isFinite(v)) || (nodata != null && v === nodata);
            let dst = i;
            if (flipY) {
                const y = (i / width) | 0;
                const x = i - y * width;
                dst = (height - 1 - y) * width + x;
            }
            const o = dst * 4;
            if (isNoData) {
                rgba[o] = 0; rgba[o + 1] = 0; rgba[o + 2] = 0; rgba[o + 3] = 0;
            } else {
                let t = (v - min) / range;
                if (t < 0) t = 0; else if (t > 1) t = 1;
                const idx = (t * 255) | 0;
                rgba[o]     = pal[idx * 3];
                rgba[o + 1] = pal[idx * 3 + 1];
                rgba[o + 2] = pal[idx * 3 + 2];
                rgba[o + 3] = 255;
            }
        }
        return new ImageData(rgba, width, height);
    }

    /* ---------- Helper: modelo é GeoTIFF? ---------- */
    function isGeoTiffModel(m) {
        if (!m) return false;
        if (m.formato === 'geotiff') return true;
        const ext = (m.extensao || '').toLowerCase();
        return ext === '.tif' || ext === '.tiff';
    }

    // export
    root.SisMOM_GeoTIFF = {
        decodeTIFF, aplicarPaleta, GT_PALETTES, isGeoTiffModel
    };

})(typeof window !== 'undefined' ? window : globalThis);
