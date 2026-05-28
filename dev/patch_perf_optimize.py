#!/usr/bin/env python3
"""
Patch: otimização de performance (mantém TODAS as funcionalidades).

(1) In-flight dedup: chamadas simultâneas para a mesma URL compartilham a
    mesma Promise<decoded>.
(2) Render cache: para (url + opts hash) guarda { imageData, bitmap?,
    blobUrl? }. aplicarPaleta (~loop em todos os pixels) só roda uma vez
    por configuração. ImageBitmap e blob URL são gerados on demand e
    também cacheados. LRU de 60 entradas; URLs de blob são revogadas ao
    serem despejadas.
(3) Scratch canvas reutilizado em vez de criar novo <canvas> por render.
(4) _gtApplyMapView: setTileProvider e fitTo só chamam se mudou (evita
    redesenhar tiles e zoom sempre que troca passo).
(5) carregarGeoTIFFParaSlot consolidado: usa _gtFetchAndDecode (cache +
    dedup) e o render cache para o caminho img (blob URL) ou mapa
    (ImageBitmap direto pro SisMOM_Map).

Resultado: animação repetida fica praticamente "grátis" depois da 1ª
passada; trocar paleta/min/max em URLs já vistas é instantâneo; segundo
slot apontando pra mesma URL não refaz o trabalho.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (a) Inserir helpers logo após gtCacheClear e antes de gtSlotEnsureMap
OLD_HELPERS = '''    function gtCacheClear() { _gtDecodedCache.clear(); }
    try { if (typeof window !== 'undefined') window.gtCacheStats = () => ({ size: _gtDecodedCache.size, max: _GT_CACHE_MAX }); } catch (_) {}
    function gtSlotEnsureMap(slotIdx) {'''
NEW_HELPERS = '''    function gtCacheClear() { _gtDecodedCache.clear(); }
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
    function gtSlotEnsureMap(slotIdx) {'''

# (b) Substituir gtRerenderSlot
OLD_RER = '''    async function gtRerenderSlot(slotIdx) {
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
NEW_RER = '''    async function gtRerenderSlot(slotIdx) {
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

# (c) Substituir carregarGeoTIFFParaSlot completo
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
        // Considera "já tem figura" se o <img> está ativo OU o canvas do mapa do slot está visível
        const hasImg    = front.classList.contains('active');
        const hasMapCv  = !!(box && box.classList.contains('gt-map-active'));
        const hasContent = hasImg || hasMapCv || !!gtSlotDecoded[slotIdx];
        if (!hasContent) loadingEl.classList.add('visible');
        errorEl.classList.remove('visible');
        try {
            // (a) Cache hit: pula fetch + decode
            let decoded = gtCacheGet(url);
            if (!decoded) {
                const resp = await fetch(url);
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const ab = await resp.arrayBuffer();
                if (reqId !== activeRequests[slotIdx]) return;
                decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
                gtCachePut(url, decoded);
            }
            if (reqId !== activeRequests[slotIdx]) return;
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
                    if (reqId !== activeRequests[slotIdx]) return;
                    const op = (gt.opacity == null) ? 0.85 : gt.opacity;
                    await m.setRasterOverlay(bmp, decoded.bbox, op);
                    if (reqId !== activeRequests[slotIdx]) return;
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                    return;
                }
            }
            const blobUrl = await gtGetBlobUrl(entry, decoded.width, decoded.height);
            if (reqId !== activeRequests[slotIdx]) return;
            back.onload = () => {
                if (reqId !== activeRequests[slotIdx]) return;
                back.classList.add('active');
                front.classList.remove('active');
                buf.active = backKey;
                loadingEl.classList.remove('visible');
                errorEl.classList.remove('visible');
            };
            back.onerror = () => {
                if (reqId !== activeRequests[slotIdx]) return;
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


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_gtRenderCache' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HELPERS, NEW_HELPERS, 'perf helpers')
    src = rep(src, OLD_RER,     NEW_RER,     'gtRerenderSlot otimizado')
    src = rep(src, OLD_LOAD,    NEW_LOAD,    'carregarGeoTIFFParaSlot otimizado')

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
