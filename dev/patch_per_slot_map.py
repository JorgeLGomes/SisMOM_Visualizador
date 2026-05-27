#!/usr/bin/env python3
"""
Patch: mapa-base + opacidade por painel Mi (modo GeoTIFF).

- Adiciona <canvas class="map-canvas-gt"> em cada slot, dentro do
  .map-viewport, atrás dos <img>.
- _gtSlotMap[i] = instância de SisMOM_Map por slot (lazy).
- gtSlotState[i] passa a guardar mapEnabled, mapProvider, opacity.
- gtRerenderSlot(i): se mapEnabled, usa SisMOM_Map (tiles + raster overlay
  + opacidade); senão, mantém o caminho atual de <img> + blob.
- Listeners do painel direito (gtShowMap, gtTileProvider, gtOpacity)
  passam a operar por slot quando appMode==='gtiff'.
- gtSyncRightPanelFromSlot reflete e gtCaptureRightPanelToSlot captura
  os 3 campos extras.
- gtSelectPanel: habilita/desabilita gtShowMap conforme bbox do slot.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Template: adicionar canvas atrás dos imgs
OLD_TPL = '''            <div class="map-viewport" data-viewport>
                <img class="map-img" data-buf="a" alt="Mapa" loading="eager" decoding="async">
                <img class="map-img" data-buf="b" alt="" aria-hidden="true" loading="eager" decoding="async">
            </div>'''
NEW_TPL = '''            <div class="map-viewport" data-viewport>
                <canvas class="map-canvas-gt" data-buf="map" style="display:none"></canvas>
                <img class="map-img" data-buf="a" alt="Mapa" loading="eager" decoding="async">
                <img class="map-img" data-buf="b" alt="" aria-hidden="true" loading="eager" decoding="async">
            </div>'''

# (2) CSS: map-canvas-gt
OLD_CSS = '''        .map-img.active { opacity: 1; visibility: visible; }'''
NEW_CSS = '''        .map-img.active { opacity: 1; visibility: visible; }
        .map-canvas-gt {
            position: absolute; inset: 0;
            width: 100%; height: 100%;
            display: block;
            cursor: grab;
            z-index: 1;
        }
        .map-canvas-gt:active { cursor: grabbing; }
        /* Quando o canvas GT está ativo, os <img> ficam ocultos */
        .map-box.gt-map-active .map-img { display: none !important; }'''

# (3) gtSlotState — extender com campos de mapa
OLD_GETSTATE = '''    function getGtSlotState(i) {
        if (!gtSlotState[i]) gtSlotState[i] = {
            paleta: 'viridis', autoMinMax: true, min: null, max: null,
            undefRaw: '', clipBelow: null, clipAbove: null
        };
        return gtSlotState[i];
    }'''
NEW_GETSTATE = '''    function getGtSlotState(i) {
        if (!gtSlotState[i]) gtSlotState[i] = {
            paleta: 'viridis', autoMinMax: true, min: null, max: null,
            undefRaw: '', clipBelow: null, clipAbove: null,
            mapEnabled: false, mapProvider: 'esri', opacity: 0.85
        };
        return gtSlotState[i];
    }
    const _gtSlotMap = [];
    function gtSlotEnsureMap(slotIdx) {
        if (_gtSlotMap[slotIdx]) return _gtSlotMap[slotIdx];
        const box = slotEl(slotIdx);
        if (!box) return null;
        const cv = box.querySelector('.map-canvas-gt');
        if (!cv) return null;
        const m = SisMOM_Map(cv);
        _gtSlotMap[slotIdx] = m;
        const gt = getGtSlotState(slotIdx);
        m.setTileProvider(gt.mapProvider || 'esri');
        return m;
    }'''

# (4) gtRerenderSlot — branchear por mapEnabled
OLD_RER = '''    async function gtRerenderSlot(slotIdx) {
        // Re-renderiza o slot Mi usando o decoded cacheado + gtSlotState (sem refetch)
        const decoded = gtSlotDecoded[slotIdx];
        if (!decoded) return;
        const buf = buffers[slotIdx];
        if (!buf) return;
        const frontKey = buf.active;
        const backKey  = frontKey === 'a' ? 'b' : 'a';
        const back  = slotBuf(slotIdx, backKey);
        const front = slotBuf(slotIdx, frontKey);
        if (!back || !front) return;
        const opts = gtSlotApplyOpts(slotIdx);
        const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
        const canvas = document.createElement('canvas');
        canvas.width = decoded.width; canvas.height = decoded.height;
        canvas.getContext('2d').putImageData(imgData, 0, 0);
        const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
        const blobUrl = URL.createObjectURL(blob);
        if (!gtBlobUrls[slotIdx]) gtBlobUrls[slotIdx] = { a: null, b: null };
        const oldUrl = gtBlobUrls[slotIdx][backKey];
        gtBlobUrls[slotIdx][backKey] = blobUrl;
        back.onload = () => {
            back.classList.add('active');
            front.classList.remove('active');
            buf.active = backKey;
            if (oldUrl) URL.revokeObjectURL(oldUrl);
        };
        back.onerror = () => { URL.revokeObjectURL(blobUrl); };
        back.src = blobUrl;
    }'''
NEW_RER = '''    async function gtRerenderSlot(slotIdx) {
        // Re-renderiza o slot Mi usando o decoded cacheado + gtSlotState (sem refetch)
        const decoded = gtSlotDecoded[slotIdx];
        if (!decoded) return;
        const buf = buffers[slotIdx];
        if (!buf) return;
        const box = slotEl(slotIdx);
        const gt = getGtSlotState(slotIdx);
        const opts = gtSlotApplyOpts(slotIdx);
        const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
        if (gt.mapEnabled && decoded.bbox) {
            // Modo mapa: usa SisMOM_Map do slot (tiles + raster overlay + opacidade)
            const m = gtSlotEnsureMap(slotIdx);
            if (!m) return;
            // Mostra canvas, esconde imgs
            const cvEl = box && box.querySelector('.map-canvas-gt');
            if (cvEl) cvEl.style.display = '';
            if (box) box.classList.add('gt-map-active');
            // Aplica provider + viewport + overlay
            m.setTileProvider(gt.mapProvider || 'esri');
            try { m.fitTo(decoded.bbox); } catch (_) {}
            const op = (gt.opacity == null) ? 0.85 : gt.opacity;
            await m.setRasterOverlay(imgData, decoded.bbox, op);
            return;
        }
        // Modo sem mapa: pipeline original com <img> + blob
        if (box) {
            box.classList.remove('gt-map-active');
            const cvEl = box.querySelector('.map-canvas-gt');
            if (cvEl) cvEl.style.display = 'none';
        }
        const frontKey = buf.active;
        const backKey  = frontKey === 'a' ? 'b' : 'a';
        const back  = slotBuf(slotIdx, backKey);
        const front = slotBuf(slotIdx, frontKey);
        if (!back || !front) return;
        const canvas = document.createElement('canvas');
        canvas.width = decoded.width; canvas.height = decoded.height;
        canvas.getContext('2d').putImageData(imgData, 0, 0);
        const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
        const blobUrl = URL.createObjectURL(blob);
        if (!gtBlobUrls[slotIdx]) gtBlobUrls[slotIdx] = { a: null, b: null };
        const oldUrl = gtBlobUrls[slotIdx][backKey];
        gtBlobUrls[slotIdx][backKey] = blobUrl;
        back.onload = () => {
            back.classList.add('active');
            front.classList.remove('active');
            buf.active = backKey;
            if (oldUrl) URL.revokeObjectURL(oldUrl);
        };
        back.onerror = () => { URL.revokeObjectURL(blobUrl); };
        back.src = blobUrl;
    }'''

# (5) gtSyncRightPanelFromSlot — adicionar campos de mapa
OLD_SYNC = '''        if (clMin) clMin.value = (gt.clipBelow != null ? gt.clipBelow : '');
        if (clMax) clMax.value = (gt.clipAbove != null ? gt.clipAbove : '');
    }
    function gtCaptureRightPanelToSlot(slotIdx) {'''
NEW_SYNC = '''        if (clMin) clMin.value = (gt.clipBelow != null ? gt.clipBelow : '');
        if (clMax) clMax.value = (gt.clipAbove != null ? gt.clipAbove : '');
        // Mapa por slot
        const dec = gtSlotDecoded[slotIdx];
        const hasGeo = !!(dec && dec.bbox);
        const showMap = document.getElementById('gtShowMap');
        if (showMap) {
            showMap.disabled = !hasGeo;
            showMap.checked = !!(hasGeo && gt.mapEnabled);
            showMap.title = hasGeo ? 'Sobrepor o raster a um mapa-base'
                                   : 'GeoTIFF sem georreferência';
        }
        const tileLabel = document.getElementById('gtTileLabel');
        const opLabel = document.getElementById('gtOpacityLabel');
        const showMapOn = !!(hasGeo && gt.mapEnabled);
        if (tileLabel) tileLabel.style.display = showMapOn ? 'inline-flex' : 'none';
        if (opLabel)   opLabel.style.display   = showMapOn ? 'inline-flex' : 'none';
        const tp = document.getElementById('gtTileProvider');
        if (tp) tp.value = gt.mapProvider || 'esri';
        const opEl = document.getElementById('gtOpacity');
        if (opEl) opEl.value = Math.round(((gt.opacity == null ? 0.85 : gt.opacity)) * 100);
    }
    function gtCaptureRightPanelToSlot(slotIdx) {'''

# (6) gtCaptureRightPanelToSlot — adicionar map fields
OLD_CAP = '''        gt.clipBelow = (clMin && clMin.value.trim() !== '') ? parseFloat(clMin.value) : null;
        gt.clipAbove = (clMax && clMax.value.trim() !== '') ? parseFloat(clMax.value) : null;
    }
    async function gtApplySlotControlsFromActive() {'''
NEW_CAP = '''        gt.clipBelow = (clMin && clMin.value.trim() !== '') ? parseFloat(clMin.value) : null;
        gt.clipAbove = (clMax && clMax.value.trim() !== '') ? parseFloat(clMax.value) : null;
        const showMap = document.getElementById('gtShowMap');
        if (showMap && !showMap.disabled) gt.mapEnabled = !!showMap.checked;
        const tp = document.getElementById('gtTileProvider');
        if (tp) gt.mapProvider = tp.value || 'esri';
        const opEl = document.getElementById('gtOpacity');
        if (opEl) {
            const pct = parseInt(opEl.value, 10);
            if (isFinite(pct)) gt.opacity = Math.max(0, Math.min(1, pct / 100));
        }
    }
    async function gtApplySlotControlsFromActive() {'''

# (7) Listeners para gtShowMap, gtTileProvider, gtOpacity — adicionar branches gtiff
# Atualmente: gtShowMap.change → gtToggleMapUI; gtOpacity → _gtMap.setOverlayOpacity;
#             gtTileProvider.change → _gtMap.setTileProvider
OLD_LIS_MAP = '''        // Mapa
        const tm = document.getElementById('gtShowMap');
        if (tm) tm.addEventListener('change', gtToggleMapUI);
        const op = document.getElementById('gtOpacity');
        if (op) op.addEventListener('input', () => {
            const val = parseInt(op.value, 10) / 100;
            if (_gtMap && _gtMap.setOverlayOpacity) {
                _gtMap.setOverlayOpacity(gtActiveLayerId, val);
            }
            // Atualiza opacity no objeto da camada (para persistência ao reordenar)
            const layer = (gtActiveLayerId !== 'primary')
                ? gtExtraLayers.find(l => l.id === gtActiveLayerId)
                : null;
            if (layer) layer.opacity = val;
        });
        const tp = document.getElementById('gtTileProvider');
        if (tp) tp.addEventListener('change', () => {
            if (_gtMap) _gtMap.setTileProvider(tp.value);
        });'''
NEW_LIS_MAP = '''        // Mapa
        const tm = document.getElementById('gtShowMap');
        if (tm) tm.addEventListener('change', () => {
            if (appMode === 'gtiff') {
                gtApplySlotControlsFromActive();
                // Mostrar/ocultar labels associados
                const tlbl = document.getElementById('gtTileLabel');
                const olbl = document.getElementById('gtOpacityLabel');
                const on = !!tm.checked;
                if (tlbl) tlbl.style.display = on ? 'inline-flex' : 'none';
                if (olbl) olbl.style.display = on ? 'inline-flex' : 'none';
            } else {
                gtToggleMapUI();
            }
        });
        const op = document.getElementById('gtOpacity');
        if (op) op.addEventListener('input', () => {
            if (appMode === 'gtiff') {
                gtApplySlotControlsFromActive();
                return;
            }
            const val = parseInt(op.value, 10) / 100;
            if (_gtMap && _gtMap.setOverlayOpacity) {
                _gtMap.setOverlayOpacity(gtActiveLayerId, val);
            }
            const layer = (gtActiveLayerId !== 'primary')
                ? gtExtraLayers.find(l => l.id === gtActiveLayerId)
                : null;
            if (layer) layer.opacity = val;
        });
        const tp = document.getElementById('gtTileProvider');
        if (tp) tp.addEventListener('change', () => {
            if (appMode === 'gtiff') {
                gtApplySlotControlsFromActive();
                return;
            }
            if (_gtMap) _gtMap.setTileProvider(tp.value);
        });'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'map-canvas-gt' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_TPL,      NEW_TPL,      'template canvas-gt')
    src = rep(src, OLD_CSS,      NEW_CSS,      'css map-canvas-gt')
    src = rep(src, OLD_GETSTATE, NEW_GETSTATE, 'getGtSlotState extends + _gtSlotMap')
    src = rep(src, OLD_RER,      NEW_RER,      'gtRerenderSlot branchear')
    src = rep(src, OLD_SYNC,     NEW_SYNC,     'gtSyncRightPanelFromSlot map fields')
    src = rep(src, OLD_CAP,      NEW_CAP,      'gtCaptureRightPanelToSlot map fields')
    src = rep(src, OLD_LIS_MAP,  NEW_LIS_MAP,  'listeners map controls')

    if dry: print(f"[{path.name}] dry-run"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok")
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
        print("OK - " + str(len(a)) + " bytes em ambas")

if __name__ == '__main__':
    main()
