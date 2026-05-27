#!/usr/bin/env python3
"""
Patch: tirar o privilégio da base de ficar sempre em primeiro plano.
A camada base agora participa do mesmo array de overlays do mapa, com
um flag isPrimary apenas para sinalizar a moldura tracejada da bbox.
Permite reordenar a base com ↑/↓ junto com as demais.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1) drawRaster: itera só overlays[] e passa isPrimary ───
OLD_DRAW = '''        function drawRaster() {
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
NEW_DRAW = '''        function drawRaster() {
            // Todas as camadas raster (incluindo a base com id='primary') estão em self.overlays.
            // Desenha de TRÁS pra FRENTE: overlays[N-1] primeiro (fundo) → overlays[0] por último (topo).
            // A entrada com isPrimary=true ganha moldura tracejada da bbox.
            for (let i = self.overlays.length - 1; i >= 0; i--) {
                const o = self.overlays[i];
                if (!o || o.visible === false) continue;
                _drawOneRaster(o, !!o.isPrimary);
            }
        }'''

# ─── (2) setRasterOverlay / clearOverlay / setOpacity passam a delegar para a entry 'primary' ───
OLD_PRIM_API = '''        async function setRasterOverlay(imageDataOrBitmap, bbox, opacity) {
            let bmp = imageDataOrBitmap;
            if (bmp && typeof ImageData !== 'undefined' && bmp instanceof ImageData) {
                bmp = await createImageBitmap(bmp);
            }
            self.overlay = { bitmap: bmp, bbox, opacity: (opacity == null ? 0.85 : opacity) };
            draw();
        }
        function clearOverlay() { self.overlay = null; draw(); }
        function setOpacity(o) { if (self.overlay) { self.overlay.opacity = o; draw(); } }'''
NEW_PRIM_API = '''        async function setRasterOverlay(imageDataOrBitmap, bbox, opacity) {
            let bmp = imageDataOrBitmap;
            if (bmp && typeof ImageData !== 'undefined' && bmp instanceof ImageData) {
                bmp = await createImageBitmap(bmp);
            }
            const op = (opacity == null ? 0.85 : opacity);
            const i = self.overlays.findIndex(o => o.id === 'primary');
            if (i >= 0) {
                // Mantém posição lógica da primary onde estava
                self.overlays[i] = { id: 'primary', bitmap: bmp, bbox, opacity: op, visible: self.overlays[i].visible !== false, isPrimary: true };
            } else {
                // Primeira vez: vai pro topo (índice 0 = renderizado por último = em cima)
                self.overlays.unshift({ id: 'primary', bitmap: bmp, bbox, opacity: op, visible: true, isPrimary: true });
            }
            self.overlay = self.overlays[self.overlays.findIndex(o => o.id === 'primary')]; // compat
            draw();
        }
        function clearOverlay() {
            self.overlays = self.overlays.filter(o => o.id !== 'primary');
            self.overlay = null;
            draw();
        }
        function setOpacity(o) {
            const e = self.overlays.find(x => x.id === 'primary');
            if (e) { e.opacity = o; draw(); }
        }
        function moveOverlay(id, delta) {
            const i = self.overlays.findIndex(o => o.id === id);
            if (i < 0) return false;
            const j = Math.max(0, Math.min(self.overlays.length - 1, i + delta));
            if (i === j) return false;
            const [moved] = self.overlays.splice(i, 1);
            self.overlays.splice(j, 0, moved);
            draw();
            return true;
        }
        function getOverlayIndex(id) { return self.overlays.findIndex(o => o.id === id); }'''

# ─── (3) Expor moveOverlay / getOverlayIndex no return ───
OLD_RET = '''            setViewport, fitTo, setRasterOverlay, clearOverlay, setOpacity,
            addRasterOverlay, removeRasterOverlay, setOverlayVisible, setOverlayOpacity,'''
NEW_RET = '''            setViewport, fitTo, setRasterOverlay, clearOverlay, setOpacity,
            addRasterOverlay, removeRasterOverlay, setOverlayVisible, setOverlayOpacity,
            moveOverlay, getOverlayIndex,'''

# ─── (4) gtMoveLayer agora trata id==='primary' ───
OLD_MOVE = '''    async function gtMoveLayer(id, delta) {
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
NEW_MOVE = '''    async function gtMoveLayer(id, delta) {
        console.debug('[gtMoveLayer]', id, 'delta', delta);
        if (id === 'primary') {
            // Move a entry 'primary' diretamente no array do mapa
            if (_gtMap && _gtMap.moveOverlay) {
                _gtMap.moveOverlay('primary', delta);
                if (_gtMap.redraw) _gtMap.redraw();
            }
            gtRenderLayerChips();
            gtRenderOverlayColorbars();
            return;
        }
        const i = gtExtraLayers.findIndex(l => l.id === id);
        if (i < 0) return;
        const j = Math.max(0, Math.min(gtExtraLayers.length - 1, i + delta));
        if (i === j) return;
        const [moved] = gtExtraLayers.splice(i, 1);
        gtExtraLayers.splice(j, 0, moved);
        // Re-empurra extras ao mapa na nova ordem (mantendo a primary onde está)
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

# ─── (5) gtAllLayers: usar a ordem real do mapa quando disponível ───
OLD_ALL = '''    function gtAllLayers() {
        const out = [gtGetLayerObj('primary')];
        for (const l of gtExtraLayers) out.push(l);
        return out;
    }'''
NEW_ALL = '''    function gtAllLayers() {
        // Se o mapa existe, usa a ordem real do array self.overlays para colocar a primary na posição certa.
        const primary = gtGetLayerObj('primary');
        if (_gtMap && _gtMap.getOverlayIndex) {
            const idx = _gtMap.getOverlayIndex('primary');
            const out = [...gtExtraLayers];
            if (idx >= 0) {
                // Mapeia o índice da primary no array do mapa para a posição na lista unificada (raster only).
                // O array do mapa = [primary?, extras geotiff]. Encontramos a posição relativa entre rasters.
                // Como nosso array já é só rasters (extras geotiff) sem a primary, inserimos em idx clipped.
                const safe = Math.max(0, Math.min(out.length, idx));
                out.splice(safe, 0, primary);
            } else {
                out.unshift(primary);
            }
            return out;
        }
        return [primary, ...gtExtraLayers];
    }'''

# ─── (6) Chips: ↑/↓ habilitados para primary; índice usa all.length ───
OLD_UP = '''            up.disabled = (l.id === 'primary' || idx <= 1);
            up.addEventListener('click', (e) => { e.stopPropagation(); gtMoveLayer(l.id, -1); });
            const dn = document.createElement('button');
            dn.type = 'button'; dn.title = 'Descer'; dn.textContent = '↓';
            dn.disabled = (l.id === 'primary' || idx >= all.length - 1);'''
NEW_UP = '''            up.disabled = (idx <= 0);
            up.addEventListener('click', (e) => { e.stopPropagation(); gtMoveLayer(l.id, -1); });
            const dn = document.createElement('button');
            dn.type = 'button'; dn.title = 'Descer'; dn.textContent = '↓';
            dn.disabled = (idx >= all.length - 1);'''

# ─── (7) gtTogglePrimaryVisible: usar setOverlayVisible em vez de clearOverlay ───
OLD_TOGGLE_PR = '''    function gtTogglePrimaryVisible() {
        gtPrimaryVisible = !gtPrimaryVisible;
        if (gtPrimaryVisible) {
            // Re-aplica overlay primary no mapa
            if (typeof gtSyncMapOverlay === 'function') gtSyncMapOverlay();
        } else {
            // Remove overlay do mapa
            if (typeof _gtMap !== 'undefined' && _gtMap) _gtMap.clearOverlay();
        }
        gtRenderar();
        gtRenderLayerChips();
        gtRenderOverlayColorbars();
    }'''
NEW_TOGGLE_PR = '''    function gtTogglePrimaryVisible() {
        gtPrimaryVisible = !gtPrimaryVisible;
        if (_gtMap && _gtMap.setOverlayVisible) {
            _gtMap.setOverlayVisible('primary', gtPrimaryVisible);
        } else if (!gtPrimaryVisible && _gtMap && _gtMap.clearOverlay) {
            _gtMap.clearOverlay();
        } else if (gtPrimaryVisible && typeof gtSyncMapOverlay === 'function') {
            gtSyncMapOverlay();
        }
        gtRenderar();
        gtRenderLayerChips();
        gtRenderOverlayColorbars();
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'isPrimary=true para sinalizar' in src or 'moveOverlay' in src and 'getOverlayIndex' in src:
        # checagem simples por moveOverlay no return
        if 'moveOverlay, getOverlayIndex' in src:
            print(f"[{path.name}] já patcheado; pulando.")
            return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_DRAW,      NEW_DRAW,      'drawRaster unified')
    src = rep(src, OLD_PRIM_API,  NEW_PRIM_API,  'primary api unified')
    src = rep(src, OLD_RET,       NEW_RET,       'expose move/getIndex')
    src = rep(src, OLD_MOVE,      NEW_MOVE,      'gtMoveLayer primary')
    src = rep(src, OLD_ALL,       NEW_ALL,       'gtAllLayers from map')
    src = rep(src, OLD_UP,        NEW_UP,        'chips primary up/down')
    src = rep(src, OLD_TOGGLE_PR, NEW_TOGGLE_PR, 'togglePrimaryVisible')

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
