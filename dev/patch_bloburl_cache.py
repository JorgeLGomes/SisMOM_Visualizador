#!/usr/bin/env python3
"""
Patch: cache de blob URL para modelos pesados (Eta etc.).

O cache de imageData economiza aplicarPaleta, mas para grids grandes os
passos seguintes ainda fazem:
  putImageData(img) [memcpy] + toBlob(image/png) [encode PNG, custoso]
  + createObjectURL

Adicionando cache de blob URL por (url+opts), revisitas pulam tudo isso
e só fazem `back.src = blobUrl` — instantâneo. Cache com LRU=40 entradas;
URLs evictadas são revogadas para liberar memória.

Hit/miss stats no console:
  window.gtCacheReport() → { decoded, imgData, blobUrl, hits, misses }
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Inserir cache de blob URL + função helper
OLD_HELPER = '''    function gtGetImageData(url, decoded, opts) {
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
    }'''
NEW_HELPER = '''    function gtGetImageData(url, decoded, opts) {
        const k = _gtImgDataKey(url, opts);
        const cached = _gtImgDataCache.get(k);
        if (cached) {
            _gtImgDataCache.delete(k); _gtImgDataCache.set(k, cached); // LRU bump
            _gtCacheStats.imgHit++;
            return cached;
        }
        _gtCacheStats.imgMiss++;
        const img = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
        _gtImgDataCache.set(k, img);
        while (_gtImgDataCache.size > _GT_IMGDATA_MAX) {
            const fk = _gtImgDataCache.keys().next().value;
            _gtImgDataCache.delete(fk);
        }
        return img;
    }
    // Cache de blob URL por (url+opts). Evita putImageData + toBlob em revisitas.
    const _gtBlobUrlCache = new Map();
    const _GT_BLOB_MAX = 40;
    const _gtCacheStats = { imgHit: 0, imgMiss: 0, blobHit: 0, blobMiss: 0 };
    async function gtGetCachedBlobUrl(url, opts, imageData, w, h) {
        const k = _gtImgDataKey(url, opts);
        const cached = _gtBlobUrlCache.get(k);
        if (cached) {
            _gtBlobUrlCache.delete(k); _gtBlobUrlCache.set(k, cached); // LRU bump
            _gtCacheStats.blobHit++;
            return cached;
        }
        _gtCacheStats.blobMiss++;
        const canvas = document.createElement('canvas');
        canvas.width = w; canvas.height = h;
        canvas.getContext('2d').putImageData(imageData, 0, 0);
        const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
        const blobUrl = URL.createObjectURL(blob);
        _gtBlobUrlCache.set(k, blobUrl);
        while (_gtBlobUrlCache.size > _GT_BLOB_MAX) {
            const fk = _gtBlobUrlCache.keys().next().value;
            const old = _gtBlobUrlCache.get(fk);
            try { URL.revokeObjectURL(old); } catch (_) {}
            _gtBlobUrlCache.delete(fk);
        }
        return blobUrl;
    }
    try { if (typeof window !== 'undefined') {
        window.gtCacheReport = () => ({
            decoded: _gtDecodedCache.size,
            imgData: _gtImgDataCache.size,
            blobUrl: _gtBlobUrlCache.size,
            stats: Object.assign({}, _gtCacheStats)
        });
    }} catch (_) {}'''

# (2) Img path em carregarGeoTIFFParaSlot: usar gtGetCachedBlobUrl
OLD_IMG = '''            // Img mode: canvas dedicado por chamada (sem race em scratch compartilhado)
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
NEW_IMG = '''            // Img mode: blob URL com cache (revisitas pulam putImageData + toBlob)
            const blobUrl = await gtGetCachedBlobUrl(url, opts, imgData, decoded.width, decoded.height);
            // Se a img de back já está com esse src, força reload setando '' antes
            if (back.src === blobUrl) {
                back.classList.add('active');
                front.classList.remove('active');
                buf.active = backKey;
                loadingEl.classList.remove('visible');
                errorEl.classList.remove('visible');
            } else {
                back.onload = () => {
                    back.classList.add('active');
                    front.classList.remove('active');
                    buf.active = backKey;
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                };
                back.onerror = () => {
                    loadingEl.classList.remove('visible');
                    errorEl.classList.add('visible');
                };
                back.src = blobUrl;
            }'''

# (3) gtRerenderSlot: mesma otimização para a re-renderização (paleta change etc.)
OLD_RER_IMG = '''        const canvas = _gtScratchCanvas(decoded.width, decoded.height);
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
NEW_RER_IMG = '''        const blobUrl = await gtGetCachedBlobUrl(url, opts, imgData, decoded.width, decoded.height);
        if (back.src === blobUrl) {
            back.classList.add('active');
            front.classList.remove('active');
            buf.active = backKey;
        } else {
            back.onload = () => {
                back.classList.add('active');
                front.classList.remove('active');
                buf.active = backKey;
            };
            back.src = blobUrl;
        }
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'gtGetCachedBlobUrl' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HELPER,  NEW_HELPER,  'helpers blob cache')
    src = rep(src, OLD_IMG,     NEW_IMG,     'carregar img path')
    src = rep(src, OLD_RER_IMG, NEW_RER_IMG, 'rerender img path')
    # Bump build
    src = src.replace('20260528-0040-nogate', '20260528-0050-blobcache')

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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0050-blobcache")

if __name__ == '__main__':
    main()
