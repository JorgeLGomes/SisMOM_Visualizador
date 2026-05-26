#!/usr/bin/env python3
"""
Patch para adicionar visualização de GeoTIFF ao SisMOM Visualizador.
Aplica TODAS as mudanças em lockstep nas duas cópias do HTML:
  - figuras_SisMOM_v23.html (raiz)
  - electron-app/figuras_SisMOM_v23.html

Mudanças:
  1) Injeta módulo GeoTIFF (decoder + paletas + helpers) no IIFE principal
  2) Adiciona botão "Abrir GeoTIFF local" no header
  3) Adiciona modal de visualização GeoTIFF (canvas + paleta + min/max)
  4) Intercepta carregarImagem() para usar fluxo GeoTIFF quando modelo.extensao = .tif/.tiff
  5) Liga UI no init()

Uso: python3 patch_geotiff.py [--dry-run]
"""

import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ───────────────────────────── Patches ─────────────────────────────

# ─── (1) Módulo GeoTIFF (será injetado no IIFE principal) ───
# Conteúdo: decoder + paletas + funções de UI (slot integration + modal local)
GEOTIFF_BLOCK = r"""
    /* ╔═══════════════════════════════════════════════════════════╗
       ║  GeoTIFF — leitura inline, sem dependência externa.       ║
       ║  Cobre TIFF baseline + LZW/Deflate/PackBits, GeoKeys,     ║
       ║  GDAL_NODATA, predictor 2, tiles e strips, uint/int/float ║
       ╚═══════════════════════════════════════════════════════════╝ */
    const SisMOM_GeoTIFF = (function () {
        function makeRamp(stops) {
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
            viridis: makeRamp([[68,1,84],[72,35,116],[64,67,135],[52,94,141],[41,120,142],[32,144,140],[34,167,132],[68,190,112],[121,209,81],[189,222,38],[253,231,36]]),
            jet:     makeRamp([[0,0,131],[0,60,170],[5,255,255],[255,255,0],[250,0,0],[128,0,0]]),
            rdbu:    makeRamp([[5,48,97],[33,102,172],[67,147,195],[146,197,222],[209,229,240],[247,247,247],[253,219,199],[244,165,130],[214,96,77],[178,24,43],[103,0,31]]),
            gray:    makeRamp([[0,0,0],[255,255,255]]),
            turbo:   makeRamp([[48,18,59],[70,107,227],[40,191,224],[70,250,162],[186,252,67],[255,192,33],[243,95,30],[165,25,8],[122,4,3]])
        };
        function decompressPackBits(input) {
            const out = [];
            let i = 0;
            while (i < input.length) {
                const n = input[i] > 127 ? input[i] - 256 : input[i];
                i++;
                if (n >= 0) { for (let k = 0; k <= n && i < input.length; k++, i++) out.push(input[i]); }
                else if (n !== -128) { const b = input[i++]; for (let k = 0; k < (1 - n); k++) out.push(b); }
            }
            return new Uint8Array(out);
        }
        function decompressLZW(input) {
            const MIN_CODE_SIZE = 8, CLEAR = 256, EOI = 257;
            const out = [];
            const dict = [];
            function resetDict() {
                dict.length = 0;
                for (let i = 0; i < 256; i++) dict.push([i]);
                dict.push(null); dict.push(null);
            }
            let codeSize = MIN_CODE_SIZE + 1;
            let bitPos = 0, byteLen = input.length;
            function readCode() {
                if (bitPos + codeSize > byteLen * 8) return -1;
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
                if (code === CLEAR) { resetDict(); codeSize = MIN_CODE_SIZE + 1; prev = null; continue; }
                let entry;
                if (code < dict.length) entry = dict[code];
                else if (prev) entry = prev.concat(prev[0]);
                else break;
                for (let k = 0; k < entry.length; k++) out.push(entry[k]);
                if (prev) dict.push(prev.concat(entry[0]));
                prev = entry;
                if (dict.length === ((1 << codeSize) - 1) && codeSize < 12) codeSize++;
            }
            return new Uint8Array(out);
        }
        async function decompressDeflate(input) {
            const stream = new Response(new Blob([input])).body.pipeThrough(new DecompressionStream('deflate'));
            const ab = await new Response(stream).arrayBuffer();
            return new Uint8Array(ab);
        }
        const TYPE_SIZES = {1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8};
        function readTagValue(view, entry, little) {
            const {type, count, valueOffset} = entry;
            const sz = TYPE_SIZES[type] || 1;
            const total = sz * count;
            const base = total <= 4 ? entry.entryOffset + 8 : valueOffset;
            const out = [];
            for (let i = 0; i < count; i++) {
                const off = base + i * sz;
                switch (type) {
                    case 1: case 7: case 2: out.push(view.getUint8(off)); break;
                    case 3: out.push(view.getUint16(off, little)); break;
                    case 4: out.push(view.getUint32(off, little)); break;
                    case 5: { const n=view.getUint32(off,little),d=view.getUint32(off+4,little); out.push(d?n/d:0); break; }
                    case 6: out.push(view.getInt8(off)); break;
                    case 8: out.push(view.getInt16(off, little)); break;
                    case 9: out.push(view.getInt32(off, little)); break;
                    case 10:{ const n=view.getInt32(off,little),d=view.getInt32(off+4,little); out.push(d?n/d:0); break; }
                    case 11: out.push(view.getFloat32(off, little)); break;
                    case 12: out.push(view.getFloat64(off, little)); break;
                    default: out.push(view.getUint8(off));
                }
            }
            return out;
        }
        function tagAscii(arr) {
            let s = '';
            for (let i = 0; i < arr.length; i++) { if (arr[i] === 0) break; s += String.fromCharCode(arr[i]); }
            return s;
        }
        async function decodeTIFF(arrayBuffer) {
            const view = new DataView(arrayBuffer);
            if (arrayBuffer.byteLength < 8) throw new Error('TIFF: arquivo muito pequeno');
            const b0 = view.getUint8(0), b1 = view.getUint8(1);
            let little;
            if (b0 === 0x49 && b1 === 0x49) little = true;
            else if (b0 === 0x4D && b1 === 0x4D) little = false;
            else throw new Error('TIFF: header inválido (não é II nem MM)');
            const magic = view.getUint16(2, little);
            if (magic !== 42) throw new Error('TIFF: magic ' + magic + ' (BigTIFF não suportado)');
            const ifdOffset = view.getUint32(4, little);
            const numEntries = view.getUint16(ifdOffset, little);
            const tags = {};
            for (let i = 0; i < numEntries; i++) {
                const eo = ifdOffset + 2 + i * 12;
                const entry = { entryOffset: eo,
                    tag: view.getUint16(eo, little), type: view.getUint16(eo+2, little),
                    count: view.getUint32(eo+4, little), valueOffset: view.getUint32(eo+8, little) };
                tags[entry.tag] = readTagValue(view, entry, little);
            }
            const width = tags[256] && tags[256][0];
            const height = tags[257] && tags[257][0];
            const bitsPerSample = (tags[258] && tags[258][0]) || 8;
            const compression = (tags[259] && tags[259][0]) || 1;
            const samplesPerPixel = (tags[277] && tags[277][0]) || 1;
            const sampleFormat = (tags[339] && tags[339][0]) || 1;
            const planar = (tags[284] && tags[284][0]) || 1;
            const predictor = (tags[317] && tags[317][0]) || 1;
            if (!width || !height) throw new Error('TIFF: dimensões ausentes');
            if (samplesPerPixel > 1 && planar === 2) throw new Error('TIFF: planar 2 não suportado');
            let segOffsets, segByteCounts, isTiled = false, tileW = 0, tileH = 0;
            if (tags[324]) { isTiled = true; segOffsets = tags[324]; segByteCounts = tags[325]; tileW = tags[322][0]; tileH = tags[323][0]; }
            else { segOffsets = tags[273] || []; segByteCounts = tags[279] || []; }
            const segments = [];
            for (let s = 0; s < segOffsets.length; s++) {
                const raw = new Uint8Array(arrayBuffer, segOffsets[s], segByteCounts[s]);
                let dec;
                switch (compression) {
                    case 1: dec = raw; break;
                    case 5: dec = decompressLZW(raw); break;
                    case 8: case 32946: dec = await decompressDeflate(raw); break;
                    case 32773: dec = decompressPackBits(raw); break;
                    default: throw new Error('TIFF: compressão ' + compression + ' não suportada');
                }
                segments.push(dec);
            }
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
            if (predictor === 2) {
                for (let y = 0; y < height; y++) {
                    const rowOff = y * width * bytesPerPixel;
                    for (let x = 1; x < width; x++) {
                        for (let c = 0; c < samplesPerPixel; c++) {
                            const off = rowOff + (x * samplesPerPixel + c) * bytesPerSample;
                            const prev = rowOff + ((x-1) * samplesPerPixel + c) * bytesPerSample;
                            if (bytesPerSample === 1) raw[off] = (raw[off] + raw[prev]) & 0xff;
                            else if (bytesPerSample === 2) {
                                const v = (raw[off] | (raw[off+1] << 8)) + (raw[prev] | (raw[prev+1] << 8));
                                raw[off] = v & 0xff; raw[off+1] = (v >> 8) & 0xff;
                            }
                        }
                    }
                }
            }
            const N = width * height;
            const data = new Float32Array(N);
            const rawView = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);
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
                if (flipY) { const y = (i / width) | 0; const x = i - y * width; dst = (height - 1 - y) * width + x; }
                const o = dst * 4;
                if (isNoData) { rgba[o]=0; rgba[o+1]=0; rgba[o+2]=0; rgba[o+3]=0; }
                else {
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
        function isGeoTiffModel(m) {
            if (!m) return false;
            if (m.formato === 'geotiff') return true;
            const ext = (m.extensao || '').toLowerCase();
            return ext === '.tif' || ext === '.tiff';
        }
        return { decodeTIFF, aplicarPaleta, GT_PALETTES, isGeoTiffModel };
    })();
    // Disponível também para testes externos
    try { if (typeof window !== 'undefined') window.SisMOM_GeoTIFF = SisMOM_GeoTIFF; } catch(_) {}

    /* ─── Integração GeoTIFF com painéis Mi ─── */
    const gtSlotState = [];
    function getGtSlotState(i) {
        if (!gtSlotState[i]) gtSlotState[i] = { paleta: 'viridis', autoMinMax: true, min: null, max: null };
        return gtSlotState[i];
    }
    const gtBlobUrls = [];
    async function carregarGeoTIFFParaSlot(slotIdx, url) {
        const reqId = ++activeRequests[slotIdx];
        const buf = buffers[slotIdx];
        const frontKey = buf.active;
        const backKey  = frontKey === 'a' ? 'b' : 'a';
        const front = slotBuf(slotIdx, frontKey);
        const back  = slotBuf(slotIdx, backKey);
        const loadingEl = slotLoading(slotIdx);
        const errorEl   = slotError(slotIdx);
        const hasVisibleImage = front.classList.contains('active');
        if (!hasVisibleImage) loadingEl.classList.add('visible');
        errorEl.classList.remove('visible');
        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const ab = await resp.arrayBuffer();
            if (reqId !== activeRequests[slotIdx]) return;
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            const gt = getGtSlotState(slotIdx);
            const opts = { paleta: gt.paleta };
            if (!gt.autoMinMax) { opts.min = gt.min; opts.max = gt.max; }
            const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
            const canvas = document.createElement('canvas');
            canvas.width = decoded.width; canvas.height = decoded.height;
            canvas.getContext('2d').putImageData(imgData, 0, 0);
            const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
            const blobUrl = URL.createObjectURL(blob);
            if (reqId !== activeRequests[slotIdx]) { URL.revokeObjectURL(blobUrl); return; }
            if (!gtBlobUrls[slotIdx]) gtBlobUrls[slotIdx] = { a: null, b: null };
            const oldUrl = gtBlobUrls[slotIdx][backKey];
            gtBlobUrls[slotIdx][backKey] = blobUrl;
            back.onload = () => {
                if (reqId !== activeRequests[slotIdx]) return;
                back.classList.add('active');
                front.classList.remove('active');
                buf.active = backKey;
                loadingEl.classList.remove('visible');
                errorEl.classList.remove('visible');
                lastLoadedURL[slotIdx] = url;
                if (oldUrl) URL.revokeObjectURL(oldUrl);
            };
            back.onerror = () => {
                if (reqId !== activeRequests[slotIdx]) return;
                loadingEl.classList.remove('visible');
                errorEl.classList.add('visible');
                URL.revokeObjectURL(blobUrl);
            };
            back.src = blobUrl;
        } catch (e) {
            if (reqId !== activeRequests[slotIdx]) return;
            loadingEl.classList.remove('visible');
            errorEl.classList.add('visible');
            const msg = errorEl.querySelector('span');
            if (msg) msg.textContent = 'GeoTIFF: ' + ((e && e.message) || 'erro ao carregar');
            lastLoadedURL[slotIdx] = null;
        }
    }

    /* ─── Modal "Abrir GeoTIFF local" ─── */
    let gtLastDecoded = null;
    function abrirModalGeoTIFF() {
        const m = document.getElementById('modalGeoTIFF');
        if (m) m.classList.add('open');
    }
    function fecharModalGeoTIFF() {
        const m = document.getElementById('modalGeoTIFF');
        if (m) m.classList.remove('open');
    }
    function gtRenderar() {
        if (!gtLastDecoded) return;
        const pal = document.getElementById('gtPaleta').value;
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        const editing = minEl.hasAttribute('data-editing');
        const opts = { paleta: pal };
        if (editing) {
            const mn = parseFloat(minEl.value);
            const mx = parseFloat(maxEl.value);
            if (isFinite(mn) && isFinite(mx) && mx > mn) { opts.min = mn; opts.max = mx; }
        }
        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);
        const cv = document.getElementById('gtCanvas');
        cv.width = gtLastDecoded.width; cv.height = gtLastDecoded.height;
        cv.getContext('2d').putImageData(img, 0, 0);
    }
    function gtAtualizarInfoEMinMax(decoded) {
        const info = document.getElementById('gtInfo');
        const parts = [`${decoded.width} × ${decoded.height}`];
        if (decoded.bbox) parts.push(`bbox [${decoded.bbox.minX.toFixed(3)}, ${decoded.bbox.minY.toFixed(3)}, ${decoded.bbox.maxX.toFixed(3)}, ${decoded.bbox.maxY.toFixed(3)}]`);
        if (decoded.nodata != null) parts.push(`nodata ${decoded.nodata}`);
        info.textContent = parts.join(' · ');
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        if (!minEl.hasAttribute('data-editing')) {
            minEl.value = decoded.min;
            maxEl.value = decoded.max;
        }
    }
    function bindGeoTIFFUI() {
        const btn = document.getElementById('btnOpenGeoTIFF');
        if (!btn) return;
        btn.addEventListener('click', abrirModalGeoTIFF);
        document.getElementById('btnGtClose').addEventListener('click', fecharModalGeoTIFF);
        const fileInput = document.getElementById('gtFile');
        document.getElementById('btnGtPick').addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', async (e) => {
            const f = e.target.files[0];
            if (!f) return;
            try {
                const ab = await f.arrayBuffer();
                gtLastDecoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
                gtAtualizarInfoEMinMax(gtLastDecoded);
                gtRenderar();
            } catch (err) {
                alert('Erro ao decodificar GeoTIFF: ' + ((err && err.message) || err));
            }
        });
        document.getElementById('gtPaleta').addEventListener('change', gtRenderar);
        const btnEdit = document.getElementById('btnGtEdit');
        const btnAuto = document.getElementById('btnGtAuto');
        btnEdit.addEventListener('click', () => {
            const m = document.getElementById('gtMin'), M = document.getElementById('gtMax');
            m.removeAttribute('readonly'); M.removeAttribute('readonly');
            m.setAttribute('data-editing', '1');
            btnEdit.style.display = 'none';
            btnAuto.style.display = '';
        });
        btnAuto.addEventListener('click', () => {
            const m = document.getElementById('gtMin'), M = document.getElementById('gtMax');
            m.setAttribute('readonly', ''); M.setAttribute('readonly', '');
            m.removeAttribute('data-editing');
            btnEdit.style.display = '';
            btnAuto.style.display = 'none';
            if (gtLastDecoded) { m.value = gtLastDecoded.min; M.value = gtLastDecoded.max; }
            gtRenderar();
        });
        document.getElementById('gtMin').addEventListener('change', gtRenderar);
        document.getElementById('gtMax').addEventListener('change', gtRenderar);
    }
"""

# ─── (2) Botão no header ───
HEADER_BTN_OLD = '''        <div class="header-actions">
            <button class="icon-btn" id="btnConfig" title="Configurar modelos e variáveis" aria-label="Configurações">'''
HEADER_BTN_NEW = '''        <div class="header-actions">
            <button class="icon-btn" id="btnOpenGeoTIFF" title="Abrir GeoTIFF local" aria-label="Abrir GeoTIFF">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/><polyline points="21 15 16 10 5 21"/></svg>
            </button>
            <button class="icon-btn" id="btnConfig" title="Configurar modelos e variáveis" aria-label="Configurações">'''

# ─── (3) Modal "Abrir GeoTIFF local" ───
# Inserido logo antes do <template id="mapBoxTpl"> que aparece após o último modal
MODAL_GT_ANCHOR = '<template id="mapBoxTpl">'
MODAL_GT_HTML = '''<!-- ====================== MODAL "ABRIR GEOTIFF LOCAL" ====================== -->
<div class="modal-backdrop" id="modalGeoTIFF" role="dialog" aria-modal="true">
    <div class="modal" style="max-width:980px">
        <header class="modal-header">
            <h2>Visualizar GeoTIFF</h2>
            <button class="icon-btn" id="btnGtClose" aria-label="Fechar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </header>
        <div class="modal-body">
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px">
                <input type="file" id="gtFile" accept=".tif,.tiff" style="display:none">
                <button class="btn btn-primary" id="btnGtPick">Abrir arquivo…</button>
                <label style="display:inline-flex;align-items:center;gap:6px">Paleta:
                    <select id="gtPaleta">
                        <option value="viridis" selected>Viridis</option>
                        <option value="jet">Jet</option>
                        <option value="rdbu">RdBu</option>
                        <option value="gray">Cinza</option>
                        <option value="turbo">Turbo</option>
                    </select>
                </label>
                <label style="display:inline-flex;align-items:center;gap:6px">Min: <input type="number" id="gtMin" step="any" readonly style="width:110px"></label>
                <label style="display:inline-flex;align-items:center;gap:6px">Max: <input type="number" id="gtMax" step="any" readonly style="width:110px"></label>
                <button class="btn btn-ghost" id="btnGtEdit">Editar escala</button>
                <button class="btn btn-ghost" id="btnGtAuto" style="display:none">Auto</button>
            </div>
            <div id="gtInfo" style="color:var(--text-muted);font-size:12px;margin-bottom:8px;min-height:1em">Abra um arquivo .tif/.tiff para visualizar.</div>
            <div style="display:flex;justify-content:center;background:var(--bg-elev,#0e1622);padding:8px;border-radius:6px;overflow:auto;max-height:60vh">
                <canvas id="gtCanvas" style="max-width:100%;image-rendering:pixelated"></canvas>
            </div>
        </div>
    </div>
</div>

<template id="mapBoxTpl">'''

# ─── (4) Intercepta carregarImagem para usar fluxo GeoTIFF ───
CARREGAR_OLD = '''    function carregarImagem(slotIdx, url) {
        const reqId = ++activeRequests[slotIdx];'''
CARREGAR_NEW = '''    function carregarImagem(slotIdx, url) {
        // GeoTIFF: usa fluxo dedicado (fetch+decode+paleta) se o modelo for .tif/.tiff
        const _gtS = state.slots[slotIdx];
        if (_gtS && typeof SisMOM_GeoTIFF !== 'undefined' && SisMOM_GeoTIFF.isGeoTiffModel(modelos[_gtS.modelo])) {
            return carregarGeoTIFFParaSlot(slotIdx, url);
        }
        const reqId = ++activeRequests[slotIdx];'''

# ─── (5) Inserir bloco GeoTIFF antes de "if (document.readyState === 'loading')" e ligar UI no init ───
INJECT_BLOCK_ANCHOR = "    if (document.readyState === 'loading') {"
# Liga UI dentro de inicializar(), antes de aplicarBloqueioInicial()
BIND_OLD = '''        // Bloqueia o app se 2FA estiver ativo no modo "abrir o app".
        aplicarBloqueioInicial();'''
BIND_NEW = '''        // Liga UI de visualização GeoTIFF (botão no header + modal)
        try { bindGeoTIFFUI(); } catch (e) { console.error('bindGeoTIFFUI', e); }
        // Bloqueia o app se 2FA estiver ativo no modo "abrir o app".
        aplicarBloqueioInicial();'''


# ───────────────────────────── Aplicador ─────────────────────────────

def patch_file(path: Path, dry: bool = False) -> bool:
    src = path.read_text(encoding='utf-8')
    original = src

    def replace_unique(haystack: str, old: str, new: str, label: str) -> str:
        n = haystack.count(old)
        if n == 0:
            raise RuntimeError(f"[{path.name}] anchor '{label}' não encontrado")
        if n > 1:
            raise RuntimeError(f"[{path.name}] anchor '{label}' aparece {n}× (não é único)")
        return haystack.replace(old, new, 1)

    # Idempotência: se já contém marcador do módulo, abortar (evita patch duplo)
    if 'SisMOM_GeoTIFF' in src:
        print(f"[{path.name}] já patcheado (contém 'SisMOM_GeoTIFF'); pulando.")
        return False

    src = replace_unique(src, HEADER_BTN_OLD, HEADER_BTN_NEW, 'header button')
    src = replace_unique(src, MODAL_GT_ANCHOR, MODAL_GT_HTML, 'modal GeoTIFF')
    src = replace_unique(src, CARREGAR_OLD, CARREGAR_NEW, 'carregarImagem interceptor')
    src = replace_unique(src, BIND_OLD, BIND_NEW, 'init bind')
    # Por último: injeta bloco do módulo + integração antes do readyState check
    src = replace_unique(src, INJECT_BLOCK_ANCHOR, GEOTIFF_BLOCK + '\n' + INJECT_BLOCK_ANCHOR, 'inject GeoTIFF block')

    if src == original:
        print(f"[{path.name}] nenhuma mudança")
        return False
    if dry:
        print(f"[{path.name}] dry-run: diff len = {len(src) - len(original)} bytes")
        return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(original)} -> {len(src)} bytes, +{len(src) - len(original)})")
    return True


def main():
    dry = '--dry-run' in sys.argv
    changed = 0
    for f in FILES:
        if not f.exists():
            print(f"[ERRO] arquivo ausente: {f}")
            sys.exit(2)
        if patch_file(f, dry=dry):
            changed += 1
    if changed == len(FILES) and not dry:
        # Validar identidade
        a = FILES[0].read_bytes()
        b = FILES[1].read_bytes()
        if a != b:
            print("[ERRO] as duas cópias divergem após patch!")
            sys.exit(3)
        print(f"OK — {len(a)} bytes em ambas, idênticas")
    elif changed == 0:
        print("Nenhum arquivo modificado.")


if __name__ == '__main__':
    main()
