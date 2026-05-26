// Extrai SisMOM_Map do HTML patcheado e valida API básica.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync('/sessions/optimistic-relaxed-davinci/mnt/Visualizador/figuras_SisMOM_v23.html', 'utf8');
const m = html.match(/\(function \(root\) \{\s+'use strict';\s+\/\* ───── Costa simplificada[\s\S]+?root\.SisMOM_Map\.CITIES = CITIES;\s+\}\)\(typeof window[^;]+;/);
if (!m) { console.error('módulo SisMOM_Map não localizado no HTML'); process.exit(2); }

// Mock mínimo de DOM para o construtor não explodir
class FakeCanvas {
    constructor() { this.width = 0; this.height = 0; this._listeners = {}; this.style = {}; }
    getContext() {
        const noop = () => {};
        return {
            setTransform: noop, fillRect: noop, beginPath: noop, moveTo: noop, lineTo: noop,
            stroke: noop, fill: noop, fillText: noop, save: noop, restore: noop,
            arc: noop, strokeRect: noop, setLineDash: noop, drawImage: noop,
            set fillStyle(v){}, set strokeStyle(v){}, set lineWidth(v){}, set font(v){},
            set globalAlpha(v){}, set imageSmoothingEnabled(v){}
        };
    }
    getBoundingClientRect() { return { width: 800, height: 400, left: 0, top: 0 }; }
    addEventListener(t, fn) { (this._listeners[t] = this._listeners[t] || []).push(fn); }
}
globalThis.window = globalThis;
globalThis.addEventListener = () => {};
globalThis.document = { addEventListener: () => {} };
globalThis.ResizeObserver = class { observe(){} disconnect(){} };
globalThis.devicePixelRatio = 1;

vm.runInThisContext(m[0]);

const canvas = new FakeCanvas();
const map = SisMOM_Map(canvas);
if (typeof map.setViewport !== 'function') throw new Error('setViewport ausente');
if (typeof map.fitTo !== 'function') throw new Error('fitTo ausente');
if (typeof map.setRasterOverlay !== 'function') throw new Error('setRasterOverlay ausente');
if (typeof map.setOpacity !== 'function') throw new Error('setOpacity ausente');
if (typeof map.addGeoJSON !== 'function') throw new Error('addGeoJSON ausente');

map.setViewport(-30, -60, 5, -30);
map.fitTo({ minX: -50, minY: -25, maxX: -40, maxY: -15 });
map.setOpacity(0.5);

// Costas e cidades embutidas
if (!Array.isArray(SisMOM_Map.SA_COAST) || SisMOM_Map.SA_COAST.length < 30) throw new Error('SA_COAST muito curto');
if (!Array.isArray(SisMOM_Map.CITIES) || SisMOM_Map.CITIES.length < 10) throw new Error('CITIES muito curto');

// addGeoJSON tolerante a FeatureCollection
map.addGeoJSON({ type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[-50,-20],[-40,-15]] }, properties: {} }
] }, { stroke: '#fff' });
map.clearGeoJSON();

console.log('OK — SisMOM_Map funciona: viewport, fit, overlay, opacidade, geojson, dados embutidos');
console.log("SA_COAST:", SisMOM_Map.SA_COAST.length, "pts | CITIES:", SisMOM_Map.CITIES.length);
