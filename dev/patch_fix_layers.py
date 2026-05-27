#!/usr/bin/env python3
"""
Patch: dois bugs reportados.
 (A) Segunda camada não respeita a paleta porque gtLayerPushToMap só passa
     {paleta} para aplicarPaleta. Aqui passamos props completas (paleta,
     min/max custom, undef extras, clip below/above) se layer.props existir.
     Também inicializamos layer.props ao adicionar a extra.
 (B) Reordenação ↑/↓ não tem efeito visual porque drawRaster desenhava
     overlays[0] primeiro (fica embaixo). Invertemos a iteração para que
     overlays[0] seja desenhado por ÚLTIMO entre as extras (= em cima).
     Assim ↑ ("subir na lista") corresponde a "ficar mais por cima no mapa".
     Também ajustamos a pilha de colorbars para refletir a mesma ordem.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (A1) gtLayerPushToMap usa layer.props
OLD_PUSH = '''    async function gtLayerPushToMap(layer) {
        if (!_gtMap) return;
        if (layer.type === 'geotiff') {
            const d = layer.decoded;
            const img = SisMOM_GeoTIFF.aplicarPaleta(d, { paleta: layer.paleta });
            await _gtMap.addRasterOverlay(layer.id, img, d.bbox, layer.opacity);
            _gtMap.setOverlayVisible(layer.id, layer.visible);
        } else if (layer.type === 'geojson') {
            _gtMap.addGeoJSON(layer.data, { stroke: layer.color, lineWidth: 1.2 }, layer.id);
            _gtMap.setGeoJSONVisible(layer.id, layer.visible);
        }
    }'''
NEW_PUSH = '''    async function gtLayerPushToMap(layer) {
        if (!_gtMap) return;
        if (layer.type === 'geotiff') {
            const d = layer.decoded;
            const p = layer.props || {};
            const opts = { paleta: (p.paleta || layer.paleta || 'viridis') };
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                opts.min = p.customMin; opts.max = p.customMax;
            }
            const extras = (typeof gtParseUndefList === 'function') ? gtParseUndefList(p.undefRaw) : null;
            if (extras) opts.nodataExtras = extras;
            if (p.clipBelow != null) opts.clipBelow = p.clipBelow;
            if (p.clipAbove != null) opts.clipAbove = p.clipAbove;
            const img = SisMOM_GeoTIFF.aplicarPaleta(d, opts);
            await _gtMap.addRasterOverlay(layer.id, img, d.bbox, layer.opacity);
            _gtMap.setOverlayVisible(layer.id, layer.visible);
        } else if (layer.type === 'geojson') {
            _gtMap.addGeoJSON(layer.data, { stroke: layer.color, lineWidth: 1.2 }, layer.id);
            _gtMap.setGeoJSONVisible(layer.id, layer.visible);
        }
    }'''

# (A2) gtAddExtraLayerFromFile: inicializa layer.props (geotiff)
OLD_ADD = '''        if (lower.endsWith('.tif') || lower.endsWith('.tiff')) {
            const ab = await file.arrayBuffer();
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            const layer = { id, type: 'geotiff', name, visible: true, opacity: 0.7,
                decoded, paleta: (document.getElementById('gtPaleta')||{}).value || 'viridis' };
            gtExtraLayers.push(layer);
            gtLayerEnsureMap();
            await gtLayerPushToMap(layer);
        }'''
NEW_ADD = '''        if (lower.endsWith('.tif') || lower.endsWith('.tiff')) {
            const ab = await file.arrayBuffer();
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            const paleta = (document.getElementById('gtPaleta')||{}).value || 'viridis';
            const layer = { id, type: 'geotiff', name, visible: true, opacity: 0.85,
                decoded, paleta,
                props: { paleta, autoMinMax: true, customMin: null, customMax: null,
                          undefRaw: '', clipBelow: null, clipAbove: null }
            };
            gtExtraLayers.push(layer);
            gtLayerEnsureMap();
            await gtLayerPushToMap(layer);
        }'''

# (B1) drawRaster do mapa: inverter iteração das overlays
OLD_DRAW = '''        function drawRaster() {
            // Camadas raster extras primeiro (abaixo da base)
            for (const o of self.overlays) {
                if (o.visible === false) continue;
                _drawOneRaster(o, false);
            }
            // Camada base (primária) por cima
            _drawOneRaster(self.overlay, true);
        }'''
NEW_DRAW = '''        function drawRaster() {
            // Camadas raster extras: desenha de TRÁS pra FRENTE (overlays[N-1] primeiro = fundo,
            // overlays[0] por último = mais por cima entre as extras). Assim ↑ na lista
            // (vai para idx menor) corresponde a "ficar mais por cima no mapa".
            for (let i = self.overlays.length - 1; i >= 0; i--) {
                const o = self.overlays[i];
                if (o.visible === false) continue;
                _drawOneRaster(o, false);
            }
            // Camada base (primária) por cima de tudo
            _drawOneRaster(self.overlay, true);
        }'''

# (B2) Pilha de colorbars: trocar column-reverse por column (ordem natural: array → top->bottom)
OLD_STACK = '''.gt-cb-stack {
            position: absolute;
            left: 12px; bottom: 62px;
            z-index: 9;
            display: flex; flex-direction: column-reverse; gap: 4px;
            pointer-events: none;
            max-width: 420px;
        }'''
NEW_STACK = '''.gt-cb-stack {
            position: absolute;
            left: 12px; bottom: 62px;
            z-index: 9;
            display: flex; flex-direction: column; gap: 4px;
            pointer-events: none;
            max-width: 420px;
        }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    # idempotência por marcador combinado
    if "Camadas raster extras: desenha de TRÁS" in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_PUSH,  NEW_PUSH,  'gtLayerPushToMap props')
    src = rep(src, OLD_ADD,   NEW_ADD,   'gtAdd init props')
    src = rep(src, OLD_DRAW,  NEW_DRAW,  'drawRaster reverse')
    src = rep(src, OLD_STACK, NEW_STACK, 'stack column natural')

    if src == original: return False
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(src)-len(original):+d})")
    return True


def main():
    dry = '--dry-run' in sys.argv
    changed = 0
    for f in FILES:
        if not f.exists(): sys.exit(2)
        if patch_file(f, dry=dry): changed += 1
    if changed == len(FILES) and not dry:
        a, b = FILES[0].read_bytes(), FILES[1].read_bytes()
        if a != b: sys.exit(3)
        print('OK - ' + str(len(a)) + ' bytes em ambas')

if __name__ == '__main__':
    main()
