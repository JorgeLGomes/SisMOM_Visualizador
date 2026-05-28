#!/usr/bin/env python3
"""
Patch: usar gtGetImageData cacheado + pre-criar ImageBitmap em
carregarGeoTIFFParaSlot e gtRerenderSlot, aplicar gate monotônico
antes de paintar.

Pré-criar bitmap evita o `await createImageBitmap` interno do
setRasterOverlay, removendo a janela em que draws de tile-load
podem repintar com overlay antigo.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) gtRerenderSlot: usar cache + pre-bitmap
OLD_RER = '''    async function gtRerenderSlot(slotIdx) {
        // Re-renderiza o slot Mi usando o decoded cacheado + gtSlotState (sem refetch).
        const decoded = gtSlotDecoded[slotIdx];
        if (!decoded) return;
        const buf = buffers[slotIdx];
        if (!buf) return;
        const box = slotEl(slotIdx);
        const gt = getGtSlotState(slotIdx);
        const opts = gtSlotApplyOpts(slotIdx);
        const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
        if (gt.mapEnabled && decoded.bbox) {
            const m = gtSlotEnsureMap(slotIdx);
            if (!m) return;
            const cvEl = box && box.querySelector('.map-canvas-gt');
            if (cvEl) cvEl.style.display = '';
            if (box) box.classList.add('gt-map-active');
            _gtApplyMapView(slotIdx, m, gt.mapProvider || 'esri', decoded.bbox);
            const op = (gt.opacity == null) ? 0.85 : gt.opacity;
            await m.setRasterOverlay(imgData, decoded.bbox, op);
            return;
        }
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
        const canvas = _gtScratchCanvas(decoded.width, decoded.height);
        canvas.getContext('2d').putImageData(imgData, 0, 0);
        const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
        const blobUrl = URL.createObjectURL(blob);
        const old = back.src;
        back.onload = () => {
            back.classList.add('active');
            front.classList.remove('active');
            buf.active = backKey;
            if (old && old.startsWith('blob:')) URL.revokeObjectURL(old);
        };
        back.src = blobUrl;
    }'''
NEW_RER = '''    async function gtRerenderSlot(slotIdx) {
        // Re-renderiza usando cache de imageData por (url+opts) — aplicarPaleta só roda 1x.
        const decoded = gtSlotDecoded[slotIdx];
        if (!decoded) return;
        const buf = buffers[slotIdx];
        if (!buf) return;
        const box = slotEl(slotIdx);
        const gt = getGtSlotState(slotIdx);
        const opts = gtSlotApplyOpts(slotIdx);
        const url = lastLoadedURL[slotIdx] || ('__slot' + slotIdx);
        const imgData = gtGetImageData(url, decoded, opts);
        if (gt.mapEnabled && decoded.bbox) {
            const m = gtSlotEnsureMap(slotIdx);
            if (!m) return;
            const cvEl = box && box.querySelector('.map-canvas-gt');
            if (cvEl) cvEl.style.display = '';
            if (box) box.classList.add('gt-map-active');
            _gtApplyMapView(slotIdx, m, gt.mapProvider || 'esri', decoded.bbox);
            // Pre-criar bitmap fora do setRasterOverlay para que o painted seja síncrono
            let bmp = imgData;
            if (typeof createImageBitmap === 'function') {
                try { bmp = await createImageBitmap(imgData); } catch (_) {}
            }
            const op = (gt.opacity == null) ? 0.85 : gt.opacity;
            await m.setRasterOverlay(bmp, decoded.bbox, op);
            return;
        }
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
        const canvas = _gtScratchCanvas(decoded.width, decoded.height);
        canvas.getContext('2d').putImageData(imgData, 0, 0);
        const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
        const blobUrl = URL.createObjectURL(blob);
        const old = back.src;
        back.onload = () => {
            back.classList.add('active');
            front.classList.remove('active');
            buf.active = backKey;
            if (old && old.startsWith('blob:')) URL.revokeObjectURL(old);
        };
        back.src = blobUrl;
    }'''

# (2) carregarGeoTIFFParaSlot: cache + pre-bitmap + gate
OLD_LOAD = '''            lastLoadedURL[slotIdx] = url;
            const opts = gtSlotApplyOpts(slotIdx);
            const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
            const gt = getGtSlotState(slotIdx);
            if (gt.mapEnabled && decoded.bbox) {
                const m = gtSlotEnsureMap(slotIdx);
                if (m) {
                    const cvEl = box && box.querySelector('.map-canvas-gt');
                    if (cvEl) cvEl.style.display = '';
                    if (box) box.classList.add('gt-map-active');
                    _gtApplyMapView(slotIdx, m, gt.mapProvider || 'esri', decoded.bbox);
                    const op = (gt.opacity == null) ? 0.85 : gt.opacity;
                    await m.setRasterOverlay(imgData, decoded.bbox, op);
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                    return;
                }
            }
            const canvas = _gtScratchCanvas(decoded.width, decoded.height);
            canvas.getContext('2d').putImageData(imgData, 0, 0);
            const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
            const blobUrl = URL.createObjectURL(blob);
            const oldSrc = back.src;
            back.onload = () => {
                back.classList.add('active');
                front.classList.remove('active');
                buf.active = backKey;
                loadingEl.classList.remove('visible');
                errorEl.classList.remove('visible');
                if (oldSrc && oldSrc.startsWith('blob:')) { try { URL.revokeObjectURL(oldSrc); } catch (_) {} }
            };
            back.onerror = () => {
                loadingEl.classList.remove('visible');
                errorEl.classList.add('visible');
                try { URL.revokeObjectURL(blobUrl); } catch (_) {}
            };
            back.src = blobUrl;'''
NEW_LOAD = '''            lastLoadedURL[slotIdx] = url;
            const opts = gtSlotApplyOpts(slotIdx);
            const imgData = gtGetImageData(url, decoded, opts);
            const gt = getGtSlotState(slotIdx);
            if (gt.mapEnabled && decoded.bbox) {
                const m = gtSlotEnsureMap(slotIdx);
                if (m) {
                    const cvEl = box && box.querySelector('.map-canvas-gt');
                    if (cvEl) cvEl.style.display = '';
                    if (box) box.classList.add('gt-map-active');
                    _gtApplyMapView(slotIdx, m, gt.mapProvider || 'esri', decoded.bbox);
                    // Pre-criar bitmap pra evitar await interno do setRasterOverlay
                    let bmp = imgData;
                    if (typeof createImageBitmap === 'function') {
                        try { bmp = await createImageBitmap(imgData); } catch (_) {}
                    }
                    if (!_gtTryApply(slotIdx, reqId)) return;
                    const op = (gt.opacity == null) ? 0.85 : gt.opacity;
                    await m.setRasterOverlay(bmp, decoded.bbox, op);
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                    return;
                }
            }
            const canvas = _gtScratchCanvas(decoded.width, decoded.height);
            canvas.getContext('2d').putImageData(imgData, 0, 0);
            const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
            if (!_gtTryApply(slotIdx, reqId)) return;
            const blobUrl = URL.createObjectURL(blob);
            const oldSrc = back.src;
            back.onload = () => {
                back.classList.add('active');
                front.classList.remove('active');
                buf.active = backKey;
                loadingEl.classList.remove('visible');
                errorEl.classList.remove('visible');
                if (oldSrc && oldSrc.startsWith('blob:')) { try { URL.revokeObjectURL(oldSrc); } catch (_) {} }
            };
            back.onerror = () => {
                loadingEl.classList.remove('visible');
                errorEl.classList.add('visible');
                try { URL.revokeObjectURL(blobUrl); } catch (_) {}
            };
            back.src = blobUrl;'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'const imgData = gtGetImageData' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_RER,  NEW_RER,  'gtRerenderSlot cache')
    src = rep(src, OLD_LOAD, NEW_LOAD, 'carregarGeoTIFFParaSlot cache')

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
