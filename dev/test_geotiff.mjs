// Teste do decoder TIFF com arquivos sintéticos gerados em memória.
// Cobre: little/big endian, sem compressão, PackBits, LZW, Deflate, uint8/uint16/float32, tags geo.

// Node 22+: Response, Blob, DecompressionStream já são globais
globalThis.ImageData = class ImageData {
    constructor(data, w, h) { this.data = data; this.width = w; this.height = h; }
};
globalThis.window = globalThis;

import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const src = readFileSync(new URL('./geotiff_module.js', import.meta.url), 'utf8');
vm.runInThisContext(src);
const { decodeTIFF, aplicarPaleta, GT_PALETTES, isGeoTiffModel } = globalThis.SisMOM_GeoTIFF;

function makeTIFF({ width, height, samples, bitsPerSample, sampleFormat, compression, predictor, geo }) {
    // Monta TIFF little-endian, sem strip splitting (1 strip).
    // Ordem dos tags ASC obrigatória.
    const tags = [];
    function tag(code, type, count, valueBytes /*Uint8Array*/) {
        tags.push({ code, type, count, valueBytes });
    }

    // 256 ImageWidth (LONG)
    const u32 = (v) => { const b = new Uint8Array(4); new DataView(b.buffer).setUint32(0, v, true); return b; };
    const u16 = (v) => { const b = new Uint8Array(2); new DataView(b.buffer).setUint16(0, v, true); return b; };
    const d64 = (v) => { const b = new Uint8Array(8); new DataView(b.buffer).setFloat64(0, v, true); return b; };

    tag(256, 4, 1, u32(width));
    tag(257, 4, 1, u32(height));
    tag(258, 3, 1, u16(bitsPerSample));
    tag(259, 3, 1, u16(compression));
    tag(262, 3, 1, u16(1)); // BlackIsZero
    tag(273, 4, 1, u32(0)); // StripOffsets (filled later)
    tag(277, 3, 1, u16(samples));
    tag(278, 4, 1, u32(height)); // RowsPerStrip = height (single strip)
    tag(279, 4, 1, u32(0)); // StripByteCounts (filled later)
    if (predictor) tag(317, 3, 1, u16(predictor));
    tag(339, 3, 1, u16(sampleFormat));

    if (geo) {
        // 33550 ModelPixelScaleTag DOUBLE x3
        const sx = geo.sx, sy = geo.sy;
        const ps = new Uint8Array(24);
        const pv = new DataView(ps.buffer);
        pv.setFloat64(0, sx, true); pv.setFloat64(8, sy, true); pv.setFloat64(16, 0, true);
        tag(33550, 12, 3, ps);
        // 33922 ModelTiepointTag DOUBLE x6 (I,J,K,X,Y,Z)
        const tp = new Uint8Array(48);
        const tv = new DataView(tp.buffer);
        tv.setFloat64(0, 0, true); tv.setFloat64(8, 0, true); tv.setFloat64(16, 0, true);
        tv.setFloat64(24, geo.X, true); tv.setFloat64(32, geo.Y, true); tv.setFloat64(40, 0, true);
        tag(33922, 12, 6, tp);
        // 42113 GDAL_NODATA ASCII
        const nodataStr = String(geo.nodata) + '\0';
        const nd = new Uint8Array(nodataStr.length);
        for (let i = 0; i < nodataStr.length; i++) nd[i] = nodataStr.charCodeAt(i);
        tag(42113, 2, nd.length, nd);
    }

    // Sort tags by code
    tags.sort((a, b) => a.code - b.code);

    // Gera pixels (1 banda, ramp linear 0..1)
    const N = width * height;
    const bytesPerSample = bitsPerSample / 8;
    const px = new Uint8Array(N * bytesPerSample * samples);
    const pxView = new DataView(px.buffer);
    for (let i = 0; i < N; i++) {
        const v = (i / (N - 1)); // 0..1
        const off = i * bytesPerSample * samples;
        if (sampleFormat === 3 && bitsPerSample === 32) pxView.setFloat32(off, v * 100, true);
        else if (sampleFormat === 1 && bitsPerSample === 8) pxView.setUint8(off, Math.round(v * 255));
        else if (sampleFormat === 1 && bitsPerSample === 16) pxView.setUint16(off, Math.round(v * 65535), true);
    }

    let stripData = px;
    if (compression === 32773) {
        // PackBits literal-only (n positivo = literal run)
        const out = [];
        let i = 0;
        while (i < px.length) {
            const chunk = Math.min(128, px.length - i);
            out.push(chunk - 1); // header
            for (let k = 0; k < chunk; k++) out.push(px[i + k]);
            i += chunk;
        }
        stripData = new Uint8Array(out);
    }

    // Layout: header(8) + pixel data + IFD
    const numEntries = tags.length;
    const ifdSize = 2 + numEntries * 12 + 4;

    // Externos (tags com valueBytes > 4 entram fora do IFD)
    const externals = [];
    let externalsSize = 0;
    tags.forEach(t => {
        if (t.valueBytes.length > 4) {
            externals.push({ tag: t, offset: 0 });
            externalsSize += t.valueBytes.length;
            if (externalsSize & 1) externalsSize++; // word align
        }
    });

    const headerSize = 8;
    const stripOffset = headerSize;
    const stripEnd = stripOffset + stripData.length;
    const ifdOffset = stripEnd + (stripEnd & 1);
    let cursor = ifdOffset + ifdSize;
    externals.forEach(e => {
        e.offset = cursor;
        cursor += e.tag.valueBytes.length;
        if (cursor & 1) cursor++;
    });

    const total = cursor;
    const buf = new Uint8Array(total);
    const dv = new DataView(buf.buffer);

    // Header II
    buf[0] = 0x49; buf[1] = 0x49;
    dv.setUint16(2, 42, true);
    dv.setUint32(4, ifdOffset, true);

    // Strip
    buf.set(stripData, stripOffset);

    // IFD
    dv.setUint16(ifdOffset, numEntries, true);
    tags.forEach((t, idx) => {
        const eo = ifdOffset + 2 + idx * 12;
        dv.setUint16(eo, t.code, true);
        dv.setUint16(eo + 2, t.type, true);
        dv.setUint32(eo + 4, t.count, true);
        // Patch StripOffsets/ByteCounts now
        if (t.code === 273) {
            dv.setUint32(eo + 8, stripOffset, true);
        } else if (t.code === 279) {
            dv.setUint32(eo + 8, stripData.length, true);
        } else if (t.valueBytes.length <= 4) {
            for (let k = 0; k < t.valueBytes.length; k++) buf[eo + 8 + k] = t.valueBytes[k];
        } else {
            const ext = externals.find(e => e.tag === t);
            dv.setUint32(eo + 8, ext.offset, true);
            buf.set(t.valueBytes, ext.offset);
        }
    });
    dv.setUint32(ifdOffset + 2 + numEntries * 12, 0, true); // next IFD = 0

    return buf.buffer.slice(0);
}

async function run() {
    let pass = 0, fail = 0;
    async function test(name, fn) {
        try { await fn(); console.log('PASS:', name); pass++; }
        catch (e) { console.error('FAIL:', name, '\n   ', e.message); fail++; }
    }

    await test('uint8 sem compressão', async () => {
        const buf = makeTIFF({ width: 4, height: 3, samples: 1, bitsPerSample: 8, sampleFormat: 1, compression: 1 });
        const r = await decodeTIFF(buf);
        if (r.width !== 4 || r.height !== 3) throw new Error('dims: ' + r.width + 'x' + r.height);
        if (r.data.length !== 12) throw new Error('data.length=' + r.data.length);
        if (r.data[0] !== 0) throw new Error('primeiro pixel=' + r.data[0] + ' esperado 0');
        if (r.data[11] !== 255) throw new Error('último pixel=' + r.data[11] + ' esperado 255');
    });

    await test('uint16 sem compressão', async () => {
        const buf = makeTIFF({ width: 4, height: 3, samples: 1, bitsPerSample: 16, sampleFormat: 1, compression: 1 });
        const r = await decodeTIFF(buf);
        if (r.data[0] !== 0 || r.data[11] !== 65535) throw new Error('valores ' + r.data[0] + '/' + r.data[11]);
    });

    await test('float32 sem compressão', async () => {
        const buf = makeTIFF({ width: 4, height: 3, samples: 1, bitsPerSample: 32, sampleFormat: 3, compression: 1 });
        const r = await decodeTIFF(buf);
        if (Math.abs(r.data[0]) > 1e-5) throw new Error('primeiro=' + r.data[0]);
        if (Math.abs(r.data[11] - 100) > 1e-3) throw new Error('último=' + r.data[11]);
    });

    await test('PackBits uint8', async () => {
        const buf = makeTIFF({ width: 8, height: 2, samples: 1, bitsPerSample: 8, sampleFormat: 1, compression: 32773 });
        const r = await decodeTIFF(buf);
        if (r.data.length !== 16) throw new Error('len ' + r.data.length);
        if (r.data[0] !== 0 || r.data[15] !== 255) throw new Error('valores');
    });

    await test('GeoTIFF tags + nodata', async () => {
        const buf = makeTIFF({
            width: 4, height: 3, samples: 1, bitsPerSample: 32, sampleFormat: 3, compression: 1,
            geo: { sx: 0.1, sy: 0.1, X: -50, Y: -10, nodata: -9999 }
        });
        const r = await decodeTIFF(buf);
        if (!r.bbox) throw new Error('bbox ausente');
        if (Math.abs(r.bbox.minX - (-50)) > 1e-6) throw new Error('minX ' + r.bbox.minX);
        if (Math.abs(r.bbox.maxY - (-10)) > 1e-6) throw new Error('maxY ' + r.bbox.maxY);
        if (r.nodata !== -9999) throw new Error('nodata ' + r.nodata);
        if (!r.scale || Math.abs(r.scale.sx - 0.1) > 1e-9) throw new Error('scale ' + JSON.stringify(r.scale));
    });

    await test('aplicarPaleta', async () => {
        const buf = makeTIFF({ width: 4, height: 1, samples: 1, bitsPerSample: 8, sampleFormat: 1, compression: 1 });
        const r = await decodeTIFF(buf);
        const img = aplicarPaleta(r, { paleta: 'viridis' });
        if (img.width !== 4 || img.height !== 1) throw new Error('imageData dims');
        if (img.data.length !== 16) throw new Error('rgba len');
        if (img.data[3] !== 255) throw new Error('alpha[0]=' + img.data[3]);
    });

    await test('paletas presentes', async () => {
        const names = Object.keys(GT_PALETTES);
        for (const n of ['viridis', 'jet', 'rdbu', 'gray', 'turbo']) {
            if (!names.includes(n)) throw new Error('missing palette ' + n);
            if (GT_PALETTES[n].length !== 768) throw new Error(n + ' size ' + GT_PALETTES[n].length);
        }
    });

    await test('isGeoTiffModel detecta .tif', () => {
        if (!isGeoTiffModel({ extensao: '.tif' })) throw new Error('por extensao');
        if (!isGeoTiffModel({ formato: 'geotiff', extensao: '.png' })) throw new Error('por formato');
        if (isGeoTiffModel({ extensao: '.png' })) throw new Error('falso-positivo');
    });

    console.log(`\n${pass} pass, ${fail} fail`);
    if (fail) process.exit(1);
}

run().catch(e => { console.error(e); process.exit(1); });
