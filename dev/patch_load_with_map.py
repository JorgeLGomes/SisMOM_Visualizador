#!/usr/bin/env python3
"""
Patch: ao recarregar um GeoTIFF (mudança de modelo/variavel/data/passo),
quando o slot está com mapa ativado, empurrar o novo raster para o
canvas SisMOM_Map do slot em vez do <img>+blob (que está oculto).

Antes: carregarGeoTIFFParaSlot sempre escrevia no <img>, então a figura
não atualizava enquanto o canvas do mapa permanecia com o raster antigo.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            gtSlotDecoded[slotIdx] = decoded;
            if (slotIdx === (gtActivePanel || 0)) {
                gtLastDecoded = decoded;
                try { gtAtualizarInfoEMinMax(decoded); } catch (_) {}
                try { gtDesenharColorbar(); } catch (_) {}
                try { gtRenderOverlayColorbars(); } catch (_) {}
            }
            const opts = gtSlotApplyOpts(slotIdx);
            const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
            const canvas = document.createElement('canvas');
            canvas.width = decoded.width; canvas.height = decoded.height;
            canvas.getContext('2d').putImageData(imgData, 0, 0);
            const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
            const blobUrl = URL.createObjectURL(blob);
            if (reqId !== activeRequests[slotIdx]) { URL.revokeObjectURL(blobUrl); return; }
            if (!gtBlobUrls[slotIdx]) gtBlobUrls[slotIdx] = { a: null, b: null };
            const oldUrl = gtBlobUrls[slotIdx][backKey];
            gtBlobUrls[slotIdx][backKey] = blobUrl;
            back.onload = () => {
                if (reqId !== activeRequests[slotIdx]) return;
                back.classList.add('active');
                front.classList.remove('active');
                buf.active = backKey;
                loadingEl.classList.remove('visible');
                errorEl.classList.remove('visible');
                lastLoadedURL[slotIdx] = url;
                if (oldUrl) URL.revokeObjectURL(oldUrl);
            };
            back.onerror = () => {
                if (reqId !== activeRequests[slotIdx]) return;
                loadingEl.classList.remove('visible');
                errorEl.classList.add('visible');
                URL.revokeObjectURL(blobUrl);
            };
            back.src = blobUrl;
        } catch (e) {'''
NEW = '''            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            gtSlotDecoded[slotIdx] = decoded;
            if (slotIdx === (gtActivePanel || 0)) {
                gtLastDecoded = decoded;
                try { gtAtualizarInfoEMinMax(decoded); } catch (_) {}
                try { gtDesenharColorbar(); } catch (_) {}
                try { gtRenderOverlayColorbars(); } catch (_) {}
            }
            const opts = gtSlotApplyOpts(slotIdx);
            const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
            // Se o slot está com mapa ativo, empurra o raster no SisMOM_Map do slot
            const _gtSt = getGtSlotState(slotIdx);
            if (_gtSt.mapEnabled && decoded.bbox) {
                const m = gtSlotEnsureMap(slotIdx);
                if (m) {
                    const _box = slotEl(slotIdx);
                    const _cvEl = _box && _box.querySelector('.map-canvas-gt');
                    if (_cvEl) _cvEl.style.display = '';
                    if (_box) _box.classList.add('gt-map-active');
                    m.setTileProvider(_gtSt.mapProvider || 'esri');
                    try { m.fitTo(decoded.bbox); } catch (_) {}
                    const _op = (_gtSt.opacity == null) ? 0.85 : _gtSt.opacity;
                    await m.setRasterOverlay(imgData, decoded.bbox, _op);
                    if (reqId !== activeRequests[slotIdx]) return;
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                    lastLoadedURL[slotIdx] = url;
                    return;
                }
            }
            const canvas = document.createElement('canvas');
            canvas.width = decoded.width; canvas.height = decoded.height;
            canvas.getContext('2d').putImageData(imgData, 0, 0);
            const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
            const blobUrl = URL.createObjectURL(blob);
            if (reqId !== activeRequests[slotIdx]) { URL.revokeObjectURL(blobUrl); return; }
            if (!gtBlobUrls[slotIdx]) gtBlobUrls[slotIdx] = { a: null, b: null };
            const oldUrl = gtBlobUrls[slotIdx][backKey];
            gtBlobUrls[slotIdx][backKey] = blobUrl;
            back.onload = () => {
                if (reqId !== activeRequests[slotIdx]) return;
                back.classList.add('active');
                front.classList.remove('active');
                buf.active = backKey;
                loadingEl.classList.remove('visible');
                errorEl.classList.remove('visible');
                lastLoadedURL[slotIdx] = url;
                if (oldUrl) URL.revokeObjectURL(oldUrl);
            };
            back.onerror = () => {
                if (reqId !== activeRequests[slotIdx]) return;
                loadingEl.classList.remove('visible');
                errorEl.classList.add('visible');
                URL.revokeObjectURL(blobUrl);
            };
            back.src = blobUrl;
        } catch (e) {'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_gtSt.mapEnabled && decoded.bbox' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
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
