#!/usr/bin/env python3
"""
Patch: simplificar img mode (sem mapa) removendo o gate e o scratch canvas
compartilhado. Possíveis causas do flick/anim travada:

1. Scratch canvas compartilhado: dois steps concorrentes putImageData no
   MESMO canvas antes do toBlob terminar. Spec da Canvas API garante
   snapshot mas implementações podem variar — melhor não compartilhar.
2. Gate monotônico _gtTryApply: pode estar bloqueando passos por algum
   edge case (ex: estado inconsistente após erro/cancelamento). Em img
   mode, ordering é tratado pela própria <img> (último back.src vence).

Mudanças:
- Img path: cria canvas dedicado por chamada (não compartilha _gtScratchEl).
- Img path: remove _gtTryApply (browser já cancela load anterior).
- Img path: remove gestão de oldSrc/revoke (simplifica).
- Map path: mantém pre-bitmap mas tira o gate (que estava entre bitmap e
  setRasterOverlay).

Mantido: cache de decoded, cache de imageData, dedup in-flight.

Build marker atualizado para 20260528-0040-nogate.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD_LOAD = '''            lastLoadedURL[slotIdx] = url;
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
                    let bmp = imgData;
                    if (typeof createImageBitmap === 'function') {
                        try { bmp = await createImageBitmap(imgData); } catch (_) {}
                    }
                    const op = (gt.opacity == null) ? 0.85 : gt.opacity;
                    await m.setRasterOverlay(bmp, decoded.bbox, op);
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                    return;
                }
            }
            // Img mode: canvas dedicado por chamada (sem race em scratch compartilhado)
            const canvas = document.createElement('canvas');
            canvas.width = decoded.width; canvas.height = decoded.height;
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


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'Img mode: canvas dedicado por chamada' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD_LOAD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD_LOAD)}")
    src = src.replace(OLD_LOAD, NEW_LOAD, 1)
    # Atualiza build marker
    src = src.replace('20260528-0030-imgcache', '20260528-0040-nogate')
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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0040-nogate")

if __name__ == '__main__':
    main()
