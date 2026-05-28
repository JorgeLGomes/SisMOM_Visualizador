#!/usr/bin/env python3
"""
Patch v2 de performance:

- ImageData cache por (url + opts). aplicarPaleta só roda 1x por
  configuração. 2ª passada de animação fica rápida.
- ImageBitmap pré-criado antes de chamar setRasterOverlay (elimina o
  await interno, reduzindo a janela em que draws podem ocorrer com o
  overlay antigo).
- Gate monotônico para evitar que paints fora-de-ordem sobrescrevam
  frames mais novos.

Estado mantido:
- Cache de decoded por URL (já existia)
- Dedup in-flight de fetch
- Scratch canvas reutilizado
- Skip setTileProvider/fitTo quando inalterado
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# Inserir helpers após `_gtApplyMapView`
OLD = '''    function _gtApplyMapView(slotIdx, m, provider, bbox) {
        if (_gtSlotLastProvider[slotIdx] !== provider) {
            try { m.setTileProvider(provider); } catch (_) {}
            _gtSlotLastProvider[slotIdx] = provider;
        }
        if (!_bboxEqExact(_gtSlotLastBbox[slotIdx], bbox)) {
            try { m.fitTo(bbox); } catch (_) {}
            _gtSlotLastBbox[slotIdx] = bbox;
        }
    }
    function gtSlotEnsureMap(slotIdx) {'''
NEW = '''    function _gtApplyMapView(slotIdx, m, provider, bbox) {
        if (_gtSlotLastProvider[slotIdx] !== provider) {
            try { m.setTileProvider(provider); } catch (_) {}
            _gtSlotLastProvider[slotIdx] = provider;
        }
        if (!_bboxEqExact(_gtSlotLastBbox[slotIdx], bbox)) {
            try { m.fitTo(bbox); } catch (_) {}
            _gtSlotLastBbox[slotIdx] = bbox;
        }
    }
    // Cache ImageData por (url + opts). aplicarPaleta só roda 1x por configuração.
    const _gtImgDataCache = new Map();
    const _GT_IMGDATA_MAX = 60;
    function _gtOptsKey(opts) {
        return (opts.paleta||'') + '|' +
               (opts.min==null?'':opts.min) + '|' +
               (opts.max==null?'':opts.max) + '|' +
               (opts.nodataExtras?opts.nodataExtras.join(','):'') + '|' +
               (opts.clipBelow==null?'':opts.clipBelow) + '|' +
               (opts.clipAbove==null?'':opts.clipAbove);
    }
    function _gtImgDataKey(url, opts) { return (url||'') + '#' + _gtOptsKey(opts); }
    function gtGetImageData(url, decoded, opts) {
        const k = _gtImgDataKey(url, opts);
        const cached = _gtImgDataCache.get(k);
        if (cached) {
            _gtImgDataCache.delete(k); _gtImgDataCache.set(k, cached); // LRU bump
            return cached;
        }
        const img = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
        _gtImgDataCache.set(k, img);
        while (_gtImgDataCache.size > _GT_IMGDATA_MAX) {
            const fk = _gtImgDataCache.keys().next().value;
            _gtImgDataCache.delete(fk);
        }
        return img;
    }
    // Gate monotônico por slot (evita paints fora-de-ordem)
    const _gtSlotLastApplied = [];
    function _gtTryApply(slotIdx, reqId) {
        const last = _gtSlotLastApplied[slotIdx] || 0;
        if (reqId < last) return false;
        _gtSlotLastApplied[slotIdx] = reqId;
        return true;
    }
    try { if (typeof window !== 'undefined') window.gtRenderCacheStats = () => ({ imgData: _gtImgDataCache.size, max: _GT_IMGDATA_MAX }); } catch (_) {}
    function gtSlotEnsureMap(slotIdx) {'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_gtImgDataCache' in src:
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
