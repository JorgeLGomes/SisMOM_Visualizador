// Extrai o módulo SisMOM_GeoTIFF do HTML patcheado e re-roda smoke tests.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync('/sessions/optimistic-relaxed-davinci/mnt/Visualizador/figuras_SisMOM_v23.html', 'utf8');

// Isola o IIFE do SisMOM_GeoTIFF
const m = html.match(/const SisMOM_GeoTIFF = \(function \(\) \{[\s\S]+?\}\)\(\);/);
if (!m) { console.error('bloco não encontrado'); process.exit(2); }

// Cria contexto mínimo
globalThis.ImageData = class ImageData { constructor(data, w, h) { this.data = data; this.width = w; this.height = h; } };

// Executa
vm.runInThisContext(m[0] + '\nglobalThis.SisMOM_GeoTIFF = SisMOM_GeoTIFF;');
const { decodeTIFF, aplicarPaleta, GT_PALETTES, isGeoTiffModel } = globalThis.SisMOM_GeoTIFF;

// Constrói TIFF mínimo float32, sem compressão
function makeFloat32TIFF(width, height) {
    const u32 = (v) => { const b = new Uint8Array(4); new DataView(b.buffer).setUint32(0, v, true); return b; };
    const u16 = (v) => { const b = new Uint8Array(2); new DataView(b.buffer).setUint16(0, v, true); return b; };
    const tags = [
        { code:256, type:4, count:1, val:u32(width) },
        { code:257, type:4, count:1, val:u32(height) },
        { code:258, type:3, count:1, val:u16(32) },
        { code:259, type:3, count:1, val:u16(1) },
        { code:262, type:3, count:1, val:u16(1) },
        { code:273, type:4, count:1, val:u32(0) }, // patched
        { code:277, type:3, count:1, val:u16(1) },
        { code:278, type:4, count:1, val:u32(height) },
        { code:279, type:4, count:1, val:u32(0) }, // patched
        { code:339, type:3, count:1, val:u16(3) },
    ];
    const N = width * height;
    const px = new Uint8Array(N * 4);
    const pxv = new DataView(px.buffer);
    for (let i = 0; i < N; i++) pxv.setFloat32(i * 4, i / (N - 1) * 50, true);

    const headerSize = 8, stripOffset = headerSize, stripEnd = stripOffset + px.length;
    const ifdOffset = stripEnd + (stripEnd & 1);
    const total = ifdOffset + 2 + tags.length * 12 + 4;
    const buf = new Uint8Array(total);
    const dv = new DataView(buf.buffer);
    buf[0]=0x49; buf[1]=0x49; dv.setUint16(2,42,true); dv.setUint32(4,ifdOffset,true);
    buf.set(px, stripOffset);
    dv.setUint16(ifdOffset, tags.length, true);
    tags.forEach((t,idx) => {
        const eo = ifdOffset + 2 + idx*12;
        dv.setUint16(eo, t.code, true);
        dv.setUint16(eo+2, t.type, true);
        dv.setUint32(eo+4, t.count, true);
        if (t.code === 273) dv.setUint32(eo+8, stripOffset, true);
        else if (t.code === 279) dv.setUint32(eo+8, px.length, true);
        else for (let k = 0; k < t.val.length; k++) buf[eo+8+k] = t.val[k];
    });
    dv.setUint32(ifdOffset + 2 + tags.length*12, 0, true);
    return buf.buffer.slice(0);
}

(async () => {
    const buf = makeFloat32TIFF(16, 8);
    const r = await decodeTIFF(buf);
    if (r.width !== 16 || r.height !== 8) throw new Error('dims');
    if (Math.abs(r.min) > 1e-3) throw new Error('min ' + r.min);
    if (Math.abs(r.max - 50) > 1e-2) throw new Error('max ' + r.max);
    const img = aplicarPaleta(r, { paleta: 'turbo' });
    if (img.width !== 16 || img.height !== 8) throw new Error('imgdata');
    if (img.data[3] !== 255) throw new Error('alpha');
    if (!isGeoTiffModel({ extensao: '.tiff' })) throw new Error('isGeoTiffModel');
    console.log('OK — módulo embarcado funciona após o patch (decode+paleta+helper)');
})().catch(e => { console.error('FAIL:', e); process.exit(1); });
