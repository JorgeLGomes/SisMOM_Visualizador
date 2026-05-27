#!/usr/bin/env python3
"""
Patch:
 - Bug "Clip não atualiza escala da camada extra":
   Adiciona gtRecomputeMinMaxForLayer(layer) que recalcula min/max do
   decoded respeitando filtros (nodata extras, clipBelow, clipAbove) e
   armazena em layer.props.{effMin,effMax}. gtApplyActiveLayer usa esses
   valores no aplicarPaleta da extra; gtRenderOverlayColorbars e a UI
   também usam.
 - Bug "reorder não funciona visualmente":
   Adicionado _gtMap.redraw() explícito no fim de gtMoveLayer (após o sync).
   Logging em console.debug para diagnosticar.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (A) Adicionar gtRecomputeMinMaxForLayer antes de gtRecomputeMinMaxAuto ───
OLD_RECOMPUTE = '''    function gtRecomputeMinMaxAuto() {'''
NEW_RECOMPUTE = '''    function gtRecomputeMinMaxForLayer(layer) {
        // Recalcula min/max ignorando pixels mascarados pelos filtros (nodata interno,
        // nodataExtras, clipBelow, clipAbove) e grava em layer.props.{effMin,effMax}.
        if (!layer || !layer.decoded || !layer.props) return;
        if (!layer.props.autoMinMax) return;
        const d = layer.decoded.data;
        const ndInternal = layer.decoded.nodata;
        const extras = (typeof gtParseUndefList === 'function') ? gtParseUndefList(layer.props.undefRaw) : null;
        const cb = (layer.props.clipBelow != null && isFinite(layer.props.clipBelow)) ? layer.props.clipBelow : null;
        const ca = (layer.props.clipAbove != null && isFinite(layer.props.clipAbove)) ? layer.props.clipAbove : null;
        let mn = Infinity, mx = -Infinity;
        for (let i = 0; i < d.length; i++) {
            const v = d[i];
            if (!isFinite(v)) continue;
            if (ndInternal != null && v === ndInternal) continue;
            if (extras) { let skip = false; for (let k = 0; k < extras.length; k++) if (v === extras[k]) { skip = true; break; } if (skip) continue; }
            if (cb != null && v < cb) continue;
            if (ca != null && v > ca) continue;
            if (v < mn) mn = v;
            if (v > mx) mx = v;
        }
        if (!isFinite(mn)) { mn = layer.decoded.min; mx = layer.decoded.max; }
        layer.props.effMin = mn;
        layer.props.effMax = mx;
    }
    function gtRecomputeMinMaxAuto() {'''

# ─── (B) gtApplyActiveLayer: chamar gtRecomputeMinMaxForLayer para extras + usar effMin/effMax ───
OLD_APPLY_GEO = '''        } else if (layer.type === 'geotiff' && _gtMap) {
            // Recolore a camada extra com paleta/min/max próprios e re-empurra ao mapa
            const opts = { paleta: p.paleta };
            const dec = layer.decoded;
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                opts.min = p.customMin; opts.max = p.customMax;
            }
            const extras = gtParseUndefList(p.undefRaw);
            if (extras) opts.nodataExtras = extras;
            if (p.clipBelow != null) opts.clipBelow = p.clipBelow;
            if (p.clipAbove != null) opts.clipAbove = p.clipAbove;
            const img = SisMOM_GeoTIFF.aplicarPaleta(dec, opts);
            await _gtMap.addRasterOverlay(layer.id, img, dec.bbox, layer.opacity);
            gtDesenharColorbar();
            gtRenderOverlayColorbars();
        }'''
NEW_APPLY_GEO = '''        } else if (layer.type === 'geotiff' && _gtMap) {
            // Recalcula min/max efetivos (auto) respeitando filtros
            gtRecomputeMinMaxForLayer(layer);
            // Recolore a camada extra com paleta/min/max próprios e re-empurra ao mapa
            const opts = { paleta: p.paleta };
            const dec = layer.decoded;
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                opts.min = p.customMin; opts.max = p.customMax;
            } else if (isFinite(p.effMin) && isFinite(p.effMax) && p.effMax > p.effMin) {
                // Usa min/max efetivos (que ignoram pixels mascarados pelos filtros)
                opts.min = p.effMin; opts.max = p.effMax;
            }
            const extras = gtParseUndefList(p.undefRaw);
            if (extras) opts.nodataExtras = extras;
            if (p.clipBelow != null) opts.clipBelow = p.clipBelow;
            if (p.clipAbove != null) opts.clipAbove = p.clipAbove;
            const img = SisMOM_GeoTIFF.aplicarPaleta(dec, opts);
            await _gtMap.addRasterOverlay(layer.id, img, dec.bbox, layer.opacity);
            // Reflete novo min/max nos inputs (autoMinMax)
            if (p.autoMinMax) {
                const minEl = document.getElementById('gtMin'), maxEl = document.getElementById('gtMax');
                if (minEl && !minEl.hasAttribute('data-editing') && isFinite(p.effMin)) minEl.value = p.effMin;
                if (maxEl && !maxEl.hasAttribute('data-editing') && isFinite(p.effMax)) maxEl.value = p.effMax;
            }
            gtDesenharColorbar();
            gtRenderOverlayColorbars();
        }'''

# ─── (C) gtRenderOverlayColorbars: usar effMin/effMax para extras se autoMinMax ───
OLD_CBSCAN = '''            const p = (l.props || (l.id === 'primary' ? gtPrimaryProps : null)) || {};
            const palName = p.paleta || (l.id === 'primary' ? 'viridis' : 'viridis');
            let mn, mx;
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                mn = p.customMin; mx = p.customMax;
            } else { mn = dec.min; mx = dec.max; }'''
NEW_CBSCAN = '''            const p = (l.props || (l.id === 'primary' ? gtPrimaryProps : null)) || {};
            const palName = p.paleta || (l.id === 'primary' ? 'viridis' : 'viridis');
            let mn, mx;
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                mn = p.customMin; mx = p.customMax;
            } else if (isFinite(p.effMin) && isFinite(p.effMax) && p.effMax > p.effMin) {
                mn = p.effMin; mx = p.effMax;
            } else { mn = dec.min; mx = dec.max; }'''

# ─── (D) gtLayerPushToMap: também usar effMin/effMax quando autoMinMax ───
OLD_PUSH = '''            const p = layer.props || {};
            const opts = { paleta: (p.paleta || layer.paleta || 'viridis') };
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                opts.min = p.customMin; opts.max = p.customMax;
            }'''
NEW_PUSH = '''            const p = layer.props || {};
            const opts = { paleta: (p.paleta || layer.paleta || 'viridis') };
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                opts.min = p.customMin; opts.max = p.customMax;
            } else if (isFinite(p.effMin) && isFinite(p.effMax) && p.effMax > p.effMin) {
                opts.min = p.effMin; opts.max = p.effMax;
            }'''

# ─── (E) gtMoveLayer: log + redraw explícito ───
OLD_MOVE = '''    async function gtMoveLayer(id, delta) {
        if (id === 'primary') return;
        const i = gtExtraLayers.findIndex(l => l.id === id);
        if (i < 0) return;
        const j = Math.max(0, Math.min(gtExtraLayers.length - 1, i + delta));
        if (i === j) return;
        const [moved] = gtExtraLayers.splice(i, 1);
        gtExtraLayers.splice(j, 0, moved);
        // Re-empurra ao mapa na nova ordem: remove e adiciona todas
        if (_gtMap) {
            // Limpa todas e refaz na nova ordem
            for (const l of gtExtraLayers) {
                if (l.type === 'geotiff') _gtMap.removeRasterOverlay(l.id);
                if (l.type === 'geojson') _gtMap.removeGeoJSON(l.id);
            }
            await gtSyncAllExtrasToMap();
        }
        gtRenderLayerChips();
        gtRenderOverlayColorbars();
    }'''
NEW_MOVE = '''    async function gtMoveLayer(id, delta) {
        if (id === 'primary') return;
        const i = gtExtraLayers.findIndex(l => l.id === id);
        if (i < 0) return;
        const j = Math.max(0, Math.min(gtExtraLayers.length - 1, i + delta));
        if (i === j) return;
        console.debug('[gtMoveLayer]', id, 'from', i, 'to', j, '(delta', delta, ')');
        const [moved] = gtExtraLayers.splice(i, 1);
        gtExtraLayers.splice(j, 0, moved);
        // Re-empurra ao mapa na nova ordem: remove e adiciona todas
        if (_gtMap) {
            for (const l of gtExtraLayers) {
                if (l.type === 'geotiff') _gtMap.removeRasterOverlay(l.id);
                if (l.type === 'geojson') _gtMap.removeGeoJSON(l.id);
            }
            await gtSyncAllExtrasToMap();
            if (_gtMap.redraw) _gtMap.redraw();
        }
        gtRenderLayerChips();
        gtRenderOverlayColorbars();
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtRecomputeMinMaxForLayer' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_RECOMPUTE, NEW_RECOMPUTE, 'recompute for layer')
    src = rep(src, OLD_APPLY_GEO, NEW_APPLY_GEO, 'apply extra geo')
    src = rep(src, OLD_CBSCAN,    NEW_CBSCAN,    'colorbar scan eff')
    src = rep(src, OLD_PUSH,      NEW_PUSH,      'push to map eff')
    src = rep(src, OLD_MOVE,      NEW_MOVE,      'move with redraw')

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
