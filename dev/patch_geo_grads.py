#!/usr/bin/env python3
"""
Patch: ampliar suporte georreferência no decoder para:
 - Multi-tiepoint sem ModelPixelScale (caso GrADS: 4 tiepoints nos cantos)
 - Normalizar longitudes 0..360 → -180..180 quando aplicável
Também aproveita para habilitar pan/zoom no canvas raster quando o arquivo
não tem bbox, para o usuário poder navegar mesmo assim.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1) decodeTIFF: ampliar derivação da bbox ───
OLD_BBOX = '''            let bbox = null, scale = null;
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
            }'''
NEW_BBOX = '''            let bbox = null, scale = null;
            function _normLon(x) { return (x > 180) ? x - 360 : x; }
            if (tags[33550] && tags[33922]) {
                // Caso típico: 1 tiepoint + ModelPixelScale
                const sx = tags[33550][0], sy = tags[33550][1];
                const tp = tags[33922];
                const I = tp[0], J = tp[1];
                let X = tp[3]; const Y = tp[4];
                X = _normLon(X);
                const minX = X - I * sx;
                const maxY = Y + J * sy;
                const maxX = minX + width * sx;
                const minY = maxY - height * sy;
                bbox = { minX, minY, maxX, maxY };
                scale = { sx, sy };
            } else if (tags[33922] && tags[33922].length >= 6 && tags[33922].length % 6 === 0) {
                // Caso GrADS / multi-tiepoint sem ModelPixelScale:
                // pega min/max das longitudes/latitudes dos tiepoints (assume cantos do raster).
                const tp = tags[33922];
                let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
                for (let i = 0; i < tp.length; i += 6) {
                    const X = _normLon(tp[i + 3]);
                    const Y = tp[i + 4];
                    if (X < mnX) mnX = X; if (X > mxX) mxX = X;
                    if (Y < mnY) mnY = Y; if (Y > mxY) mxY = Y;
                }
                if (isFinite(mnX) && mxX > mnX && mxY > mnY) {
                    bbox = { minX: mnX, minY: mnY, maxX: mxX, maxY: mxY };
                }
            }'''

# ─── (2) Pan/zoom no canvas raster (sem mapa) ───
# Adiciona CSS para transform + JS handlers
OLD_CSS_HUD = '''.gt-bottom-hud .gt-hud-coord {
            min-width: 220px;
            text-align: center;
            padding: 0 8px;
        }'''
NEW_CSS_HUD = '''.gt-bottom-hud .gt-hud-coord {
            min-width: 220px;
            text-align: center;
            padding: 0 8px;
        }
        /* Canvas raster (modo sem mapa) com pan/zoom via transform CSS */
        #gtCanvas { transform-origin: center center; transition: transform .08s linear; cursor: grab; }
        #gtCanvas:active { cursor: grabbing; }'''

# ─── (3) Estado + funções de transform do canvas + listeners ───
# Insere depois de gtClearCoord
OLD_CLEAR = '''    function gtClearCoord() {
        const el = document.getElementById('gtCoord');
        const hud = document.getElementById('gtCoordHud');
        if (el) el.textContent = '—';
        if (hud) hud.textContent = '—';
    }'''
NEW_CLEAR = '''    function gtClearCoord() {
        const el = document.getElementById('gtCoord');
        const hud = document.getElementById('gtCoordHud');
        if (el) el.textContent = '—';
        if (hud) hud.textContent = '—';
    }
    /* ─── Pan/zoom do canvas raster (usado quando GeoTIFF não tem bbox e o mapa é indisponível) ─── */
    const gtCanvasView = { scale: 1, tx: 0, ty: 0, dragging: false, lastX: 0, lastY: 0 };
    function gtApplyCanvasTransform() {
        const cv = document.getElementById('gtCanvas');
        if (!cv) return;
        cv.style.transform = `translate(${gtCanvasView.tx}px, ${gtCanvasView.ty}px) scale(${gtCanvasView.scale})`;
    }
    function gtCanvasZoomBy(factor) {
        gtCanvasView.scale = Math.max(0.1, Math.min(50, gtCanvasView.scale * (1 / factor)));
        gtApplyCanvasTransform();
    }
    function gtCanvasZoomReset() {
        gtCanvasView.scale = 1; gtCanvasView.tx = 0; gtCanvasView.ty = 0;
        gtApplyCanvasTransform();
    }
    function gtBindCanvasNavigation() {
        const cv = document.getElementById('gtCanvas');
        if (!cv || cv._gtNavBound) return;
        cv._gtNavBound = true;
        cv.addEventListener('wheel', (e) => {
            if (cv.style.display === 'none') return;  // mapa ativo
            e.preventDefault();
            const f = e.deltaY < 0 ? 0.8 : 1.25;
            gtCanvasZoomBy(f);
        }, { passive: false });
        cv.addEventListener('mousedown', (e) => {
            if (cv.style.display === 'none') return;
            gtCanvasView.dragging = true; gtCanvasView.lastX = e.clientX; gtCanvasView.lastY = e.clientY;
            cv.style.transition = 'none';
        });
        window.addEventListener('mouseup', () => {
            if (gtCanvasView.dragging) {
                gtCanvasView.dragging = false;
                const cv2 = document.getElementById('gtCanvas');
                if (cv2) cv2.style.transition = '';
            }
        });
        cv.addEventListener('mousemove', (e) => {
            if (!gtCanvasView.dragging) return;
            gtCanvasView.tx += (e.clientX - gtCanvasView.lastX);
            gtCanvasView.ty += (e.clientY - gtCanvasView.lastY);
            gtCanvasView.lastX = e.clientX; gtCanvasView.lastY = e.clientY;
            gtApplyCanvasTransform();
        });
    }'''

# ─── (4) HUD buttons: caminho dual (mapa ou canvas) ───
OLD_HUD_BIND = '''        if (bIn)  bIn.addEventListener('click',  () => { if (_gtMap && _gtMap.zoomBy) _gtMap.zoomBy(0.7); });
        if (bOut) bOut.addEventListener('click', () => { if (_gtMap && _gtMap.zoomBy) _gtMap.zoomBy(1.4); });
        if (bRst) bRst.addEventListener('click', () => {
            if (_gtMap && gtLastDecoded && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
        });'''
NEW_HUD_BIND = '''        function _canvasActive() {
            const cv = document.getElementById('gtCanvas');
            return cv && cv.style.display !== 'none';
        }
        if (bIn)  bIn.addEventListener('click',  () => {
            if (_canvasActive()) gtCanvasZoomBy(0.7);
            else if (_gtMap && _gtMap.zoomBy) _gtMap.zoomBy(0.7);
        });
        if (bOut) bOut.addEventListener('click', () => {
            if (_canvasActive()) gtCanvasZoomBy(1.4);
            else if (_gtMap && _gtMap.zoomBy) _gtMap.zoomBy(1.4);
        });
        if (bRst) bRst.addEventListener('click', () => {
            if (_canvasActive()) gtCanvasZoomReset();
            else if (_gtMap && gtLastDecoded && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
        });
        // Liga pan/zoom no canvas raster
        try { gtBindCanvasNavigation(); } catch (e) { console.error('canvas nav', e); }'''

# ─── (5) Reset do transform ao carregar novo arquivo ───
OLD_FILE_END = '''                gtLastDecoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
                gtPrimaryName = f.name || '';'''
NEW_FILE_END = '''                gtLastDecoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
                gtPrimaryName = f.name || '';
                try { gtCanvasZoomReset(); } catch (_) {}'''

# ─── (6) Tooltip mais clara no toggle quando disabled (já existe; ajuste) ───
OLD_TT = '''        toggle.title = hasGeo ? 'Sobrepor o raster a um mapa-base'
                              : 'GeoTIFF sem georreferência (tags 33550/33922 ausentes)';'''
NEW_TT = '''        toggle.title = hasGeo ? 'Sobrepor o raster a um mapa-base'
                              : 'GeoTIFF sem georreferência (use o pan/zoom direto no canvas)';'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtCanvasView' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_BBOX,     NEW_BBOX,     'decodeTIFF multi-tiepoint')
    src = rep(src, OLD_CSS_HUD,  NEW_CSS_HUD,  'css canvas pan')
    src = rep(src, OLD_CLEAR,    NEW_CLEAR,    'canvas nav fns')
    src = rep(src, OLD_HUD_BIND, NEW_HUD_BIND, 'hud bind dual')
    src = rep(src, OLD_FILE_END, NEW_FILE_END, 'reset transform on file')
    src = rep(src, OLD_TT,       NEW_TT,       'tooltip explanation')

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
