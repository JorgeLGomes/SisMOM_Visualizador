#!/usr/bin/env python3
"""
Patch: simplifica o pipeline de render removendo o cache de imageData/
bitmap/blobUrl que estava causando "campo não atualiza" durante animação.

Mantém:
- Cache de decoded por URL (_gtDecodedCache) — evita fetch+decode repetido
- Dedup in-flight (_gtInflight) — evita fetch duplicado concorrente
- Reuso de scratch canvas
- Skip de setTileProvider/fitTo quando inalterado

Remove (volta ao comportamento anterior, mais simples):
- _gtRenderCache (cache de imageData/bitmap/blobUrl por url+opts)
- gtGetRenderEntry, gtGetBitmap, gtGetBlobUrl
- Gate monotônico (_gtSlotLastApplied / _gtTryApply)

Volta para: cada chamada de carregarGeoTIFFParaSlot ou gtRerenderSlot
roda aplicarPaleta fresh, gera blob/setRasterOverlay direto. Mais simples
e correto. A performance vinda do cache de decoded já elimina o maior
custo (fetch + decode); aplicarPaleta sozinha é rápida o suficiente.

reqId check: apenas no início (após fetch). Sem checagem entre os awaits
da renderização — deixa o pipeline natural ordenar (FIFO via event loop).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Substituir os helpers do bloco "performance" — remove render cache, gate, etc.
OLD_HELPERS = '''    function gtCacheClear() { _gtDecodedCache.clear(); }
    /* ─── Helpers de performance: dedup de fetch + render cache ─── */
    const _gtInflight = new Map(); // url -> Promise<decoded>
    async function _gtFetchAndDecode(url) {
        const cached = gtCacheGet(url);
        if (cached) return cached;
        if (_gtInflight.has(url)) return _gtInflight.get(url);
        const p = (async () => {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const ab = await resp.arrayBuffer();
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            gtCachePut(url, decoded);
            return decoded;
        })().finally(() => { _gtInflight.delete(url); });
        _gtInflight.set(url, p);
        return p;
    }
    // Render cache: chave (url + opts) -> { imageData, bitmap?, blobUrl? }
    const _gtRenderCache = new Map();
    const _GT_RENDER_MAX = 60;
    function _gtOptsKey(opts) {
        return (opts.paleta||'') + '|' +
               (opts.min==null?'':opts.min) + '|' +
               (opts.max==null?'':opts.max) + '|' +
               (opts.nodataExtras?opts.nodataExtras.join(','):'') + '|' +
               (opts.clipBelow==null?'':opts.clipBelow) + '|' +
               (opts.clipAbove==null?'':opts.clipAbove);
    }
    function _gtRenderKey(url, opts) { return (url||'') + '#' + _gtOptsKey(opts); }
    function gtGetRenderEntry(url, decoded, opts) {
        const k = _gtRenderKey(url, opts);
        let e = _gtRenderCache.get(k);
        if (e) { _gtRenderCache.delete(k); _gtRenderCache.set(k, e); return e; }
        const imageData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
        e = { imageData, bitmap: null, blobUrl: null };
        _gtRenderCache.set(k, e);
        while (_gtRenderCache.size > _GT_RENDER_MAX) {
            const fk = _gtRenderCache.keys().next().value;
            const fe = _gtRenderCache.get(fk);
            if (fe && fe.blobUrl) { try { URL.revokeObjectURL(fe.blobUrl); } catch (_) {} }
            if (fe && fe.bitmap && fe.bitmap.close) { try { fe.bitmap.close(); } catch (_) {} }
            _gtRenderCache.delete(fk);
        }
        return e;
    }
    async function gtGetBitmap(entry) {
        if (entry.bitmap) return entry.bitmap;
        if (typeof createImageBitmap === 'function') {
            try { entry.bitmap = await createImageBitmap(entry.imageData); } catch (_) {}
        }
        return entry.bitmap || entry.imageData;
    }
    // Scratch canvas reutilizado
    let _gtScratchEl = null;
    function _gtScratchCanvas(w, h) {
        if (!_gtScratchEl) _gtScratchEl = document.createElement('canvas');
        if (_gtScratchEl.width !== w)  _gtScratchEl.width = w;
        if (_gtScratchEl.height !== h) _gtScratchEl.height = h;
        return _gtScratchEl;
    }
    async function gtGetBlobUrl(entry, w, h) {
        if (entry.blobUrl) return entry.blobUrl;
        const c = _gtScratchCanvas(w, h);
        c.getContext('2d').putImageData(entry.imageData, 0, 0);
        const blob = await new Promise(res => c.toBlob(res, 'image/png'));
        entry.blobUrl = URL.createObjectURL(blob);
        return entry.blobUrl;
    }
    // Skip setTileProvider / fitTo quando não muda
    const _gtSlotLastBbox = [];
    const _gtSlotLastProvider = [];
    function _bboxEqExact(a, b) {
        if (!a || !b) return false;
        return a.minX === b.minX && a.maxX === b.maxX && a.minY === b.minY && a.maxY === b.maxY;
    }
    function _gtApplyMapView(slotIdx, m, provider, bbox) {
        if (_gtSlotLastProvider[slotIdx] !== provider) {
            try { m.setTileProvider(provider); } catch (_) {}
            _gtSlotLastProvider[slotIdx] = provider;
        }
        if (!_bboxEqExact(_gtSlotLastBbox[slotIdx], bbox)) {
            try { m.fitTo(bbox); } catch (_) {}
            _gtSlotLastBbox[slotIdx] = bbox;
        }
    }
    try { if (typeof window !== 'undefined') window.gtRenderCacheStats = () => ({ size: _gtRenderCache.size, max: _GT_RENDER_MAX }); } catch (_) {}
    // Gate monotônico para evitar que frames antigos sobrescrevam novos durante animação.
    const _gtSlotLastApplied = [];
    function _gtTryApply(slotIdx, reqId) {
        const last = _gtSlotLastApplied[slotIdx] || 0;
        if (reqId < last) return false;
        _gtSlotLastApplied[slotIdx] = reqId;
        return true;
    }
    function gtSlotEnsureMap(slotIdx) {'''
NEW_HELPERS = '''    function gtCacheClear() { _gtDecodedCache.clear(); }
    /* ─── Dedup de fetch + scratch canvas + skip de view repetida ─── */
    const _gtInflight = new Map(); // url -> Promise<decoded>
    async function _gtFetchAndDecode(url) {
        const cached = gtCacheGet(url);
        if (cached) return cached;
        if (_gtInflight.has(url)) return _gtInflight.get(url);
        const p = (async () => {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const ab = await resp.arrayBuffer();
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            gtCachePut(url, decoded);
            return decoded;
        })().finally(() => { _gtInflight.delete(url); });
        _gtInflight.set(url, p);
        return p;
    }
    // Scratch canvas reutilizado (em vez de createElement a cada render)
    let _gtScratchEl = null;
    function _gtScratchCanvas(w, h) {
        if (!_gtScratchEl) _gtScratchEl = document.createElement('canvas');
        if (_gtScratchEl.width !== w)  _gtScratchEl.width = w;
        if (_gtScratchEl.height !== h) _gtScratchEl.height = h;
        return _gtScratchEl;
    }
    // Skip setTileProvider / fitTo quando inalterado por slot
    const _gtSlotLastBbox = [];
    const _gtSlotLastProvider = [];
    function _bboxEqExact(a, b) {
        if (!a || !b) return false;
        return a.minX === b.minX && a.maxX === b.maxX && a.minY === b.minY && a.maxY === b.maxY;
    }
    function _gtApplyMapView(slotIdx, m, provider, bbox) {
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

# (2) Substituir gtRerenderSlot — sem render cache, sem gate
OLD_RER = '''    async function gtRerenderSlot(slotIdx) {
        // Re-renderiza o slot Mi usando o decoded cacheado + gtSlotState (sem refetch).
        // Usa render cache (aplicarPaleta só roda na 1a vez por (url,opts)).
        const decoded = gtSlotDecoded[slotIdx];
        if (!decoded) return;
        const buf = buffers[slotIdx];
        if (!buf) return;
        const box = slotEl(slotIdx);
        const gt = getGtSlotState(slotIdx);
        const opts = gtSlotApplyOpts(slotIdx);
        const url = lastLoadedURL[slotIdx] || ('__slot' + slotIdx);
        const entry = gtGetRenderEntry(url, decoded, opts);
        if (gt.mapEnabled && decoded.bbox) {
            const m = gtSlotEnsureMap(slotIdx);
            if (!m) return;
            const cvEl = box && box.querySelector('.map-canvas-gt');
            if (cvEl) cvEl.style.display = '';
            if (box) box.classList.add('gt-map-active');
            _gtApplyMapView(slotIdx, m, gt.mapProvider || 'esri', decoded.bbox);
            const bmp = await gtGetBitmap(entry);
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
        const blobUrl = await gtGetBlobUrl(entry, decoded.width, decoded.height);
        back.onload = () => {
            back.classList.add('active');
            front.classList.remove('active');
            buf.active = backKey;
        };
        back.src = blobUrl;
    }'''
NEW_RER = '''    async function gtRerenderSlot(slotIdx) {
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

# (3) Substituir carregarGeoTIFFParaSlot — sem render cache, sem gate
OLD_LOAD = '''    async function carregarGeoTIFFParaSlot(slotIdx, url) {
        const reqId = ++activeRequests[slotIdx];
        const buf = buffers[slotIdx];
        const frontKey = buf.active;
        const backKey  = frontKey === 'a' ? 'b' : 'a';
        const front = slotBuf(slotIdx, frontKey);
        const back  = slotBuf(slotIdx, backKey);
        const loadingEl = slotLoading(slotIdx);
        const errorEl   = slotError(slotIdx);
        const box       = slotEl(slotIdx);
        const hasImg    = front.classList.contains('active');
        const hasMapCv  = !!(box && box.classList.contains('gt-map-active'));
        const hasContent = hasImg || hasMapCv || !!gtSlotDecoded[slotIdx];
        if (!hasContent) loadingEl.classList.add('visible');
        errorEl.classList.remove('visible');
        try {
            const decoded = await _gtFetchAndDecode(url);
            if (reqId !== activeRequests[slotIdx]) return;
            gtSlotDecoded[slotIdx] = decoded;
            if (slotIdx === (gtActivePanel || 0)) {
                gtLastDecoded = decoded;
                try { gtAtualizarInfoEMinMax(decoded); } catch (_) {}
                try { gtDesenharColorbar(); } catch (_) {}
                try { gtRenderOverlayColorbars(); } catch (_) {}
            }
            lastLoadedURL[slotIdx] = url;
            const opts = gtSlotApplyOpts(slotIdx);
            const entry = gtGetRenderEntry(url, decoded, opts);
            const gt = getGtSlotState(slotIdx);
            if (gt.mapEnabled && decoded.bbox) {
                const m = gtSlotEnsureMap(slotIdx);
                if (m) {
                    const cvEl = box && box.querySelector('.map-canvas-gt');
                    if (cvEl) cvEl.style.display = '';
                    if (box) box.classList.add('gt-map-active');
                    _gtApplyMapView(slotIdx, m, gt.mapProvider || 'esri', decoded.bbox);
                    const bmp = await gtGetBitmap(entry);
                    if (!_gtTryApply(slotIdx, reqId)) return;
                    const op = (gt.opacity == null) ? 0.85 : gt.opacity;
                    await m.setRasterOverlay(bmp, decoded.bbox, op);
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                    return;
                }
            }
            const blobUrl = await gtGetBlobUrl(entry, decoded.width, decoded.height);
            if (!_gtTryApply(slotIdx, reqId)) return;
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
        } catch (e) {
            if (reqId !== activeRequests[slotIdx]) return;
            loadingEl.classList.remove('visible');
            errorEl.classList.add('visible');
            const msg = errorEl.querySelector('span');
            if (msg) msg.textContent = 'GeoTIFF: ' + ((e && e.message) || 'erro ao carregar');
            lastLoadedURL[slotIdx] = null;
        }
    }'''
NEW_LOAD = '''    async function carregarGeoTIFFParaSlot(slotIdx, url) {
        const reqId = ++activeRequests[slotIdx];
        const buf = buffers[slotIdx];
        const frontKey = buf.active;
        const backKey  = frontKey === 'a' ? 'b' : 'a';
        const front = slotBuf(slotIdx, frontKey);
        const back  = slotBuf(slotIdx, backKey);
        const loadingEl = slotLoading(slotIdx);
        const errorEl   = slotError(slotIdx);
        const box       = slotEl(slotIdx);
        const hasImg    = front.classList.contains('active');
        const hasMapCv  = !!(box && box.classList.contains('gt-map-active'));
        const hasContent = hasImg || hasMapCv || !!gtSlotDecoded[slotIdx];
        if (!hasContent) loadingEl.classList.add('visible');
        errorEl.classList.remove('visible');
        try {
            const decoded = await _gtFetchAndDecode(url);
            if (reqId !== activeRequests[slotIdx]) return;
            gtSlotDecoded[slotIdx] = decoded;
            if (slotIdx === (gtActivePanel || 0)) {
                gtLastDecoded = decoded;
                try { gtAtualizarInfoEMinMax(decoded); } catch (_) {}
                try { gtDesenharColorbar(); } catch (_) {}
                try { gtRenderOverlayColorbars(); } catch (_) {}
            }
            lastLoadedURL[slotIdx] = url;
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
            back.src = blobUrl;
        } catch (e) {
            if (reqId !== activeRequests[slotIdx]) return;
            loadingEl.classList.remove('visible');
            errorEl.classList.add('visible');
            const msg = errorEl.querySelector('span');
            if (msg) msg.textContent = 'GeoTIFF: ' + ((e && e.message) || 'erro ao carregar');
            lastLoadedURL[slotIdx] = null;
        }
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_gtRenderCache' not in src:
        print(f"[{path.name}] já está simplificado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HELPERS, NEW_HELPERS, 'helpers simplify')
    src = rep(src, OLD_RER,     NEW_RER,     'gtRerenderSlot simplify')
    src = rep(src, OLD_LOAD,    NEW_LOAD,    'carregarGeoTIFFParaSlot simplify')

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
