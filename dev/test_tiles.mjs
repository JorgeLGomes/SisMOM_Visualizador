// Smoke test do SisMOM_Map v2 extraído do HTML patcheado.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync('/sessions/optimistic-relaxed-davinci/mnt/Visualizador/figuras_SisMOM_v23.html', 'utf8');
const m = html.match(/\(function \(root\) \{\s+'use strict';\s+const SA_COAST[\s\S]+?root\.SisMOM_Map\.TILE_PROVIDERS = TILE_PROVIDERS;\s+\}\)\(typeof window[^;]+;/);
if (!m) { console.error('módulo SisMOM_Map v2 não localizado'); process.exit(2); }

class FakeCanvas {
    constructor() { this.width = 0; this.height = 0; this.style = {}; this._cbs = {}; }
    getContext() {
        const noop = () => {};
        const obj = {};
        for (const k of ['setTransform','fillRect','beginPath','moveTo','lineTo','stroke','fill','fillText','save','restore','arc','strokeRect','setLineDash','drawImage','rect']) obj[k] = noop;
        for (const k of ['fillStyle','strokeStyle','lineWidth','font','globalAlpha','imageSmoothingEnabled']) Object.defineProperty(obj, k, { set(){}, get(){} });
        return obj;
    }
    getBoundingClientRect() { return { width: 800, height: 400, left: 0, top: 0 }; }
    addEventListener(t, fn) { (this._cbs[t] = this._cbs[t] || []).push(fn); }
}
globalThis.window = globalThis;
globalThis.addEventListener = () => {};
globalThis.document = { addEventListener: () => {} };
globalThis.ResizeObserver = class { observe(){} disconnect(){} };
globalThis.requestAnimationFrame = (cb) => setTimeout(cb, 0);
globalThis.devicePixelRatio = 1;
// Image: nunca dispara load (sem rede no sandbox)
globalThis.Image = class {
    constructor() { this.onload = null; this.onerror = null; this._src = ''; }
    set src(v) { this._src = v; }
    get src() { return this._src; }
};

vm.runInThisContext(m[0]);

// Asserções
const map = SisMOM_Map(new FakeCanvas());
if (!SisMOM_Map.TILE_PROVIDERS) throw new Error('TILE_PROVIDERS ausente');
const provs = Object.keys(SisMOM_Map.TILE_PROVIDERS);
for (const p of ['none','osm','esri','topo']) {
    if (!provs.includes(p)) throw new Error('provider ausente: ' + p);
}
if (!SisMOM_Map.TILE_PROVIDERS.esri.url.includes('arcgisonline')) throw new Error('esri url errada');
if (typeof map.setTileProvider !== 'function') throw new Error('setTileProvider');
if (typeof map.setProjection !== 'function') throw new Error('setProjection');
if (typeof map.setAttributionElement !== 'function') throw new Error('setAttribution');

// Toggle de provider força Mercator
map.setTileProvider('esri');                       // implica projection=mercator
map.setTileProvider('osm');
map.setTileProvider('topo');
map.setTileProvider('none');
// Mudança de viewport não deve quebrar
map.setViewport(-35, -75, 5, -30);
map.fitTo({ minX: -50, minY: -25, maxX: -40, maxY: -15 });
// addGeoJSON ainda funciona
map.addGeoJSON({ type: 'LineString', coordinates: [[-50,-20],[-40,-15]] }, { stroke: '#ff0' });
map.clearGeoJSON();

console.log("OK SisMOM_Map v2:", provs.length, "providers,", SisMOM_Map.SA_COAST.length, "pts costa,", SisMOM_Map.CITIES.length, "cidades");
