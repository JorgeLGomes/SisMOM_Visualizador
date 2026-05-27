// Inspect TIFF tags
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const html = readFileSync('/sessions/optimistic-relaxed-davinci/mnt/Visualizador/figuras_SisMOM_v23.html', 'utf8');
const m = html.match(/const SisMOM_GeoTIFF = \(function \(\) \{[\s\S]+?\}\)\(\);/);
globalThis.ImageData = class { constructor(d,w,h){this.data=d;this.width=w;this.height=h;}};
vm.runInThisContext(m[0] + '\nglobalThis.SisMOM_GeoTIFF = SisMOM_GeoTIFF;');

const ab = readFileSync('/tmp/Prec-0001.tif').buffer;
const r = await SisMOM_GeoTIFF.decodeTIFF(ab);
console.log('Dimensions:', r.width, 'x', r.height);
console.log('Min/Max:', r.min, '/', r.max);
console.log('NoData:', r.nodata);
console.log('BBox:', r.bbox);
console.log('Scale:', r.scale);
console.log('Data type sample:', r.data.constructor.name, 'len:', r.data.length);
console.log('First 10 values:', Array.from(r.data.slice(0, 10)));

// Inspect raw TIFF tags
const view = new DataView(ab);
const little = view.getUint8(0) === 0x49;
const ifdOff = view.getUint32(4, little);
const numEntries = view.getUint16(ifdOff, little);
console.log('\nNum tags:', numEntries);
const tagNames = {
    256: 'ImageWidth', 257: 'ImageLength', 258: 'BitsPerSample', 259: 'Compression',
    262: 'PhotoMetricInterp', 273: 'StripOffsets', 277: 'SamplesPerPixel',
    278: 'RowsPerStrip', 279: 'StripByteCounts', 284: 'PlanarConfig',
    317: 'Predictor', 322: 'TileWidth', 323: 'TileLength',
    324: 'TileOffsets', 325: 'TileByteCounts', 339: 'SampleFormat',
    33550: 'ModelPixelScale', 33922: 'ModelTiepoint',
    34735: 'GeoKeyDirectory', 34736: 'GeoDoubleParams', 34737: 'GeoAsciiParams',
    42112: 'GDAL_METADATA', 42113: 'GDAL_NODATA'
};
for (let i = 0; i < numEntries; i++) {
    const eo = ifdOff + 2 + i * 12;
    const tag = view.getUint16(eo, little);
    const type = view.getUint16(eo+2, little);
    const count = view.getUint32(eo+4, little);
    console.log('  Tag', tag, '(' + (tagNames[tag] || '?') + ') type=' + type + ' count=' + count);
}
