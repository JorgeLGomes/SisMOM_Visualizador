#!/usr/bin/env python3
"""
Patch v2: substitui o SisMOM_Map antigo (sem tiles) pelo v2 (com Mercator + tiles XYZ).
Aplica nas duas cópias do HTML. Adiciona seletor de provider e elemento de atribuição
no modal local. Idempotente (detecta TILE_PROVIDERS).
"""

import sys, re
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']
MAP_JS = (ROOT / 'dev' / 'map_module.js').read_text(encoding='utf-8').rstrip().rstrip('\x00').rstrip()

# Regex para encontrar o bloco do SisMOM_Map antigo (IIFE inteira)
# Começa em "(function (root) {" precedido por "use strict" + comentário do mapa
# Termina em "})(typeof window !== 'undefined' ? window : globalThis);"
OLD_MODULE_RE = re.compile(
    r"\(function \(root\) \{\s+'use strict';\s+/\* ───── Costa simplificada[\s\S]+?"
    r"root\.SisMOM_Map\.CITIES = CITIES;\s+\}\)\(typeof window[^;]+;",
    re.MULTILINE
)

# Bloco antigo do toggle/opacity no modal — vou expandir adicionando seletor de provider
OLD_CONTROLS = '''<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
                <label style="display:inline-flex;align-items:center;gap:6px"><input type="checkbox" id="gtShowMap" disabled> Mostrar mapa</label>
                <label id="gtOpacityLabel" style="display:none;align-items:center;gap:6px;color:var(--text-muted,#aab)">Opacidade <input type="range" id="gtOpacity" min="0" max="100" value="85" style="width:140px"></label>
                <span id="gtCoord" style="font-family:ui-monospace,monospace;color:var(--text-muted,#aab);margin-left:auto">—</span>
            </div>'''
NEW_CONTROLS = '''<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
                <label style="display:inline-flex;align-items:center;gap:6px"><input type="checkbox" id="gtShowMap" disabled> Mostrar mapa</label>
                <label id="gtTileLabel" style="display:none;align-items:center;gap:6px;color:var(--text-muted,#aab)">Camada:
                    <select id="gtTileProvider">
                        <option value="esri" selected>Satélite (Esri)</option>
                        <option value="osm">Ruas (OSM)</option>
                        <option value="topo">Topo (OpenTopoMap)</option>
                        <option value="none">Sem tiles (offline)</option>
                    </select>
                </label>
                <label id="gtOpacityLabel" style="display:none;align-items:center;gap:6px;color:var(--text-muted,#aab)">Opacidade <input type="range" id="gtOpacity" min="0" max="100" value="85" style="width:140px"></label>
                <span id="gtCoord" style="font-family:ui-monospace,monospace;color:var(--text-muted,#aab);margin-left:auto">—</span>
            </div>'''

# Bloco antigo do container do mapa — adiciona div de atribuição absoluta
OLD_MAP_CONTAINER = '''<div style="display:flex;justify-content:center;background:var(--bg-elev,#0e1622);padding:8px;border-radius:6px;overflow:hidden;max-height:60vh;position:relative">
                <canvas id="gtCanvas" style="max-width:100%;image-rendering:pixelated"></canvas>
                <canvas id="gtMapCanvas" style="display:none;width:100%;height:60vh;cursor:grab"></canvas>
            </div>'''
NEW_MAP_CONTAINER = '''<div style="display:flex;justify-content:center;background:var(--bg-elev,#0e1622);padding:8px;border-radius:6px;overflow:hidden;max-height:60vh;position:relative">
                <canvas id="gtCanvas" style="max-width:100%;image-rendering:pixelated"></canvas>
                <canvas id="gtMapCanvas" style="display:none;width:100%;height:60vh;cursor:grab"></canvas>
                <span id="gtAttrib" style="position:absolute;right:10px;bottom:10px;font-size:10px;color:#cbd6e6;background:rgba(0,0,0,0.55);padding:2px 6px;border-radius:3px;pointer-events:none"></span>
            </div>'''

# bindGeoTIFFUI atual já liga gtShowMap e gtOpacity; vamos adicionar gtTileProvider
OLD_BIND_END = '''        const op = document.getElementById('gtOpacity');
        if (op) op.addEventListener('input', () => {
            if (_gtMap) _gtMap.setOpacity(parseInt(op.value, 10) / 100);
        });
    }'''
NEW_BIND_END = '''        const op = document.getElementById('gtOpacity');
        if (op) op.addEventListener('input', () => {
            if (_gtMap) _gtMap.setOpacity(parseInt(op.value, 10) / 100);
        });
        const tp = document.getElementById('gtTileProvider');
        if (tp) tp.addEventListener('change', () => {
            if (_gtMap) _gtMap.setTileProvider(tp.value);
        });
    }'''

# gtToggleMapUI atual: adiciona linkagem da label do seletor de camada
OLD_TOGGLE = '''        if (rasterCv) rasterCv.style.display = show ? 'none' : '';
        if (mapCv)    mapCv.style.display    = show ? '' : 'none';
        if (opLabel)  opLabel.style.display  = show ? 'inline-flex' : 'none';
        if (show) gtSyncMapOverlay();
    }'''
NEW_TOGGLE = '''        if (rasterCv) rasterCv.style.display = show ? 'none' : '';
        if (mapCv)    mapCv.style.display    = show ? '' : 'none';
        if (opLabel)  opLabel.style.display  = show ? 'inline-flex' : 'none';
        const tileLabel = document.getElementById('gtTileLabel');
        if (tileLabel) tileLabel.style.display = show ? 'inline-flex' : 'none';
        if (show) gtSyncMapOverlay();
    }'''

# gtSyncMapOverlay atual: na primeira chamada já configura tile provider + atribuição
OLD_SYNC_INIT = '''        if (!_gtMap) {
            const mapCv = document.getElementById('gtMapCanvas');
            _gtMap = SisMOM_Map(mapCv);
            _gtMap.onCursor(p => {
                const el = document.getElementById('gtCoord');
                if (el) el.textContent = `${p.lat.toFixed(3)}°, ${p.lon.toFixed(3)}°`;
            });
            _gtMap.fitTo(gtLastDecoded.bbox);
        }'''
NEW_SYNC_INIT = '''        if (!_gtMap) {
            const mapCv = document.getElementById('gtMapCanvas');
            _gtMap = SisMOM_Map(mapCv);
            _gtMap.onCursor(p => {
                const el = document.getElementById('gtCoord');
                if (el) el.textContent = `${p.lat.toFixed(3)}°, ${p.lon.toFixed(3)}°`;
            });
            const attribEl = document.getElementById('gtAttrib');
            if (attribEl) _gtMap.setAttributionElement(attribEl);
            const tpSel = document.getElementById('gtTileProvider');
            const initialProvider = (tpSel && tpSel.value) || 'esri';
            _gtMap.setTileProvider(initialProvider);
            _gtMap.fitTo(gtLastDecoded.bbox);
        }'''


def patch_file(path: Path, dry: bool = False) -> bool:
    src = path.read_text(encoding='utf-8')
    original = src

    if 'TILE_PROVIDERS' in src:
        print(f"[{path.name}] já patcheado v2 (contém 'TILE_PROVIDERS'); pulando.")
        return False
    if 'SisMOM_Map' not in src:
        print(f"[{path.name}] não tem SisMOM_Map v1 — rode patch_map.py primeiro.")
        return False

    # Substitui o IIFE inteiro do mapa
    matches = OLD_MODULE_RE.findall(src)
    if len(matches) != 1:
        print(f"[{path.name}] IIFE do SisMOM_Map: {len(matches)} matches (esperado 1)")
        return False
    src = OLD_MODULE_RE.sub(MAP_JS, src, count=1)

    def replace_unique(haystack, old, new, label):
        n = haystack.count(old)
        if n != 1:
            raise RuntimeError(f"[{path.name}] anchor '{label}' aparece {n}× (esperado 1)")
        return haystack.replace(old, new, 1)

    src = replace_unique(src, OLD_CONTROLS, NEW_CONTROLS, 'controls bar')
    src = replace_unique(src, OLD_MAP_CONTAINER, NEW_MAP_CONTAINER, 'map container')
    src = replace_unique(src, OLD_BIND_END, NEW_BIND_END, 'bind tile listener')
    src = replace_unique(src, OLD_TOGGLE, NEW_TOGGLE, 'toggle tile label')
    src = replace_unique(src, OLD_SYNC_INIT, NEW_SYNC_INIT, 'sync map init tile')

    if src == original:
        return False
    if dry:
        print(f"[{path.name}] dry-run: +{len(src) - len(original)} bytes")
        return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(original)} -> {len(src)} bytes, {len(src) - len(original):+d})")
    return True


def main():
    dry = '--dry-run' in sys.argv
    changed = 0
    for f in FILES:
        if not f.exists():
            print(f"[ERRO] arquivo ausente: {f}"); sys.exit(2)
        if patch_file(f, dry=dry):
            changed += 1
    if changed == len(FILES) and not dry:
        a = FILES[0].read_bytes(); b = FILES[1].read_bytes()
        if a != b:
            print("[ERRO] cópias divergem após patch!"); sys.exit(3)
        print(f"OK — {len(a)} bytes em ambas, idênticas")


if __name__ == '__main__':
    main()
