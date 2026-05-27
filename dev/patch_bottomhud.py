#!/usr/bin/env python3
"""
Patch: HUD inferior central com navegação (zoom +/-, reset) e
coordenada/valor sob o cursor. Flutua absolute sobre o canvas.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) CSS para a barra HUD
OLD_CSS = '#mainGT { padding: 8px 12px; height: calc(100vh - 60px); box-sizing: border-box; }'
NEW_CSS = '''#mainGT { padding: 8px 12px; height: calc(100vh - 60px); box-sizing: border-box; }
        /* HUD inferior central — navegação + valor */
        .gt-bottom-hud {
            position: absolute;
            left: 50%; transform: translateX(-50%);
            bottom: 16px;
            z-index: 10;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(10,18,30,0.78);
            color: var(--text, #cbd6e6);
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.10);
            backdrop-filter: blur(6px);
            font-family: ui-monospace, monospace;
            font-size: 12px;
            pointer-events: auto;
            user-select: none;
        }
        .gt-bottom-hud .gt-hud-sep { width: 1px; height: 18px; background: rgba(255,255,255,0.12); margin: 0 4px; }
        .gt-bottom-hud button {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.06);
            color: inherit;
            cursor: pointer;
            width: 26px; height: 26px;
            border-radius: 4px;
            font-size: 14px; font-weight: 700;
            line-height: 22px; padding: 0;
            display: inline-flex; align-items: center; justify-content: center;
        }
        .gt-bottom-hud button:hover { background: rgba(255,255,255,0.18); }
        .gt-bottom-hud button:active { transform: scale(0.95); }
        .gt-bottom-hud .gt-hud-coord {
            min-width: 220px;
            text-align: center;
            padding: 0 8px;
        }'''

# (2) Adicionar zoomBy/zoomReset no SisMOM_Map (antes do return)
OLD_MAP_RETURN_ANCHOR = '''        return {
            setViewport, fitTo, setRasterOverlay, clearOverlay, setOpacity,
            addRasterOverlay, removeRasterOverlay, setOverlayVisible, setOverlayOpacity,
            addGeoJSON, removeGeoJSON, setGeoJSONVisible, clearGeoJSON,'''
NEW_MAP_RETURN_ANCHOR = '''        function zoomBy(factor) {
            const lonC = (self.vp[1] + self.vp[3]) / 2;
            const lonW = (self.vp[3] - self.vp[1]) * factor;
            self.vp[1] = lonC - lonW / 2; self.vp[3] = lonC + lonW / 2;
            if (isMercator()) {
                const yTop = latToMercY(self.vp[2]);
                const yBot = latToMercY(self.vp[0]);
                const yCenter = (yTop + yBot) / 2;
                const yH = (yTop - yBot) * factor;
                self.vp[2] = mercYToLat(yCenter + yH / 2);
                self.vp[0] = mercYToLat(yCenter - yH / 2);
            } else {
                const latC = (self.vp[0] + self.vp[2]) / 2;
                const latH = (self.vp[2] - self.vp[0]) * factor;
                self.vp[0] = latC - latH / 2; self.vp[2] = latC + latH / 2;
            }
            adjustViewportToAspect();
            draw();
        }
        return {
            setViewport, fitTo, setRasterOverlay, clearOverlay, setOpacity,
            addRasterOverlay, removeRasterOverlay, setOverlayVisible, setOverlayOpacity,
            addGeoJSON, removeGeoJSON, setGeoJSONVisible, clearGeoJSON,
            zoomBy,'''

# (3) gtReorganizeLayout: ao montar o canvas-wrap, insere o HUD inferior
OLD_REORG_END = '''            // Container que contém os canvases (#gtCanvas e #gtMapCanvas)
            if (el.querySelector && (el.querySelector('#gtCanvas') || el.querySelector('#gtMapCanvas'))) {
                el.classList.add('gt-canvas-wrap');
                el.style.display = 'flex';
                el.style.alignItems = 'center';
                el.style.justifyContent = 'center';
                main.appendChild(el); continue;
            }'''
NEW_REORG_END = '''            // Container que contém os canvases (#gtCanvas e #gtMapCanvas)
            if (el.querySelector && (el.querySelector('#gtCanvas') || el.querySelector('#gtMapCanvas'))) {
                el.classList.add('gt-canvas-wrap');
                el.style.display = 'flex';
                el.style.alignItems = 'center';
                el.style.justifyContent = 'center';
                // Insere HUD inferior dentro do wrap (position:absolute)
                if (!el.querySelector('.gt-bottom-hud')) {
                    const hud = document.createElement('div');
                    hud.className = 'gt-bottom-hud';
                    hud.innerHTML = '' +
                        '<button type="button" id="gtBtnZoomIn"  title="Aproximar">+</button>' +
                        '<button type="button" id="gtBtnZoomOut" title="Afastar">−</button>' +
                        '<button type="button" id="gtBtnZoomReset" title="Recentrar">⟲</button>' +
                        '<span class="gt-hud-sep"></span>' +
                        '<span class="gt-hud-coord" id="gtCoordHud">—</span>';
                    el.appendChild(hud);
                }
                main.appendChild(el); continue;
            }'''

# (4) gtAtualizarCoord: espelhar valor em #gtCoordHud (além do #gtCoord existente)
OLD_HUD = '''    function gtAtualizarCoord(lat, lon) {
        const el = document.getElementById('gtCoord');
        if (!el) return;
        const coord = `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;
        const samp = gtSampleAtLatLon(lat, lon);
        if (!samp.valid) { el.textContent = coord; return; }
        if (samp.noData) { el.textContent = `${coord} · NoData`; return; }
        // Formatação adaptativa: número grande/pequeno usa exponencial
        const v = samp.value;
        const abs = Math.abs(v);
        const fmt = (abs !== 0 && (abs < 1e-3 || abs >= 1e6)) ? v.toExponential(3) : v.toFixed(3);
        el.textContent = `${coord} · valor = ${fmt}`;
    }'''
NEW_HUD = '''    function gtAtualizarCoord(lat, lon) {
        const els = [document.getElementById('gtCoord'), document.getElementById('gtCoordHud')].filter(Boolean);
        if (!els.length) return;
        const coord = `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;
        const samp = gtSampleAtLatLon(lat, lon);
        let txt;
        if (!samp.valid) txt = coord;
        else if (samp.noData) txt = `${coord} · NoData`;
        else {
            const v = samp.value;
            const abs = Math.abs(v);
            const fmt = (abs !== 0 && (abs < 1e-3 || abs >= 1e6)) ? v.toExponential(3) : v.toFixed(3);
            txt = `${coord} · valor = ${fmt}`;
        }
        for (const el of els) el.textContent = txt;
    }'''

# (5) gtSampleAtCanvasXY: idem para escrever em ambos
OLD_XY_NO = '''        if (gtIsMasked(v)) {
            el.textContent = `col ${col}, row ${row} · NoData`;
        } else {
            const abs = Math.abs(v);
            const fmt = (abs !== 0 && (abs < 1e-3 || abs >= 1e6)) ? v.toExponential(3) : v.toFixed(3);
            el.textContent = `col ${col}, row ${row} · valor = ${fmt}`;
        }
    }'''
NEW_XY_NO = '''        let txt;
        if (gtIsMasked(v)) txt = `col ${col}, row ${row} · NoData`;
        else {
            const abs = Math.abs(v);
            const fmt = (abs !== 0 && (abs < 1e-3 || abs >= 1e6)) ? v.toExponential(3) : v.toFixed(3);
            txt = `col ${col}, row ${row} · valor = ${fmt}`;
        }
        const hud = document.getElementById('gtCoordHud');
        el.textContent = txt;
        if (hud) hud.textContent = txt;
    }'''

# (6) gtClearCoord limpa também o HUD
OLD_CLEAR = '''    function gtClearCoord() {
        const el = document.getElementById('gtCoord');
        if (el) el.textContent = '—';
    }'''
NEW_CLEAR = '''    function gtClearCoord() {
        const el = document.getElementById('gtCoord');
        const hud = document.getElementById('gtCoordHud');
        if (el) el.textContent = '—';
        if (hud) hud.textContent = '—';
    }'''

# (7) Binding dos botões no bindGeoTIFFUI (depois do reorganize)
OLD_BIND_REORG = '''        try { gtReorganizeLayout(); } catch (e) { console.error('gtReorganizeLayout', e); }'''
NEW_BIND_REORG = '''        try { gtReorganizeLayout(); } catch (e) { console.error('gtReorganizeLayout', e); }
        // Botões de zoom do HUD inferior
        const bIn = document.getElementById('gtBtnZoomIn');
        const bOut = document.getElementById('gtBtnZoomOut');
        const bRst = document.getElementById('gtBtnZoomReset');
        if (bIn)  bIn.addEventListener('click',  () => { if (_gtMap && _gtMap.zoomBy) _gtMap.zoomBy(0.7); });
        if (bOut) bOut.addEventListener('click', () => { if (_gtMap && _gtMap.zoomBy) _gtMap.zoomBy(1.4); });
        if (bRst) bRst.addEventListener('click', () => {
            if (_gtMap && gtLastDecoded && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
        });'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gt-bottom-hud' in src:
        print(f"[{path.name}] já patcheado (gt-bottom-hud); pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS,              NEW_CSS,              'css hud')
    src = rep(src, OLD_MAP_RETURN_ANCHOR, NEW_MAP_RETURN_ANCHOR, 'zoomBy in map')
    src = rep(src, OLD_REORG_END,        NEW_REORG_END,        'reorganize add hud')
    src = rep(src, OLD_HUD,              NEW_HUD,              'gtAtualizarCoord mirror')
    src = rep(src, OLD_XY_NO,            NEW_XY_NO,            'gtSampleAtCanvasXY mirror')
    src = rep(src, OLD_CLEAR,            NEW_CLEAR,            'gtClearCoord mirror')
    src = rep(src, OLD_BIND_REORG,       NEW_BIND_REORG,       'bind hud buttons')

    if src == original: return False
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok (+{len(src)-len(original)})")
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
