#!/usr/bin/env python3
"""
Patch: cache LRU de GeoTIFFs decodificados + suprimir spinner em re-render
do mesmo slot quando já há figura visível.

(1) Cache em memória (Map url -> decoded), com LRU e tamanho máximo
    configurável (_GT_CACHE_MAX = 80).
(2) carregarGeoTIFFParaSlot consulta o cache antes de fazer fetch. Em hit,
    pula fetch + decode (rápido). Em miss, decodifica e armazena.
(3) O spinner "Carregando..." só aparece se:
    - não há raster ativo no <img> E não há canvas de mapa visível, OU
    - é a primeira carga do slot (sem decoded anterior).
    Caso contrário, a troca é "silenciosa" — figura nova substitui a
    antiga sem flash de loading.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Declarar cache logo após gtSlotEnsureMap (ou outro ponto inicial)
OLD_DECL = '''    const _gtSlotMap = [];
    function gtSlotEnsureMap(slotIdx) {'''
NEW_DECL = '''    const _gtSlotMap = [];
    /* ─── Cache LRU em memória de TIFFs decodificados (por URL) ─── */
    const _gtDecodedCache = new Map();
    const _GT_CACHE_MAX = 80;
    function gtCacheGet(url) {
        if (!url) return null;
        const e = _gtDecodedCache.get(url);
        if (!e) return null;
        // LRU: remove e re-adiciona pra ficar no fim
        _gtDecodedCache.delete(url);
        _gtDecodedCache.set(url, e);
        return e;
    }
    function gtCachePut(url, decoded) {
        if (!url || !decoded) return;
        _gtDecodedCache.set(url, decoded);
        while (_gtDecodedCache.size > _GT_CACHE_MAX) {
            const firstKey = _gtDecodedCache.keys().next().value;
            _gtDecodedCache.delete(firstKey);
        }
    }
    function gtCacheClear() { _gtDecodedCache.clear(); }
    try { if (typeof window !== 'undefined') window.gtCacheStats = () => ({ size: _gtDecodedCache.size, max: _GT_CACHE_MAX }); } catch (_) {}
    function gtSlotEnsureMap(slotIdx) {'''

# (2) Substituir o trecho de fetch + decode por: consulta cache → fetch + decode → cache.put
OLD_LOAD = '''    async function carregarGeoTIFFParaSlot(slotIdx, url) {
        const reqId = ++activeRequests[slotIdx];
        const buf = buffers[slotIdx];
        const frontKey = buf.active;
        const backKey  = frontKey === 'a' ? 'b' : 'a';
        const front = slotBuf(slotIdx, frontKey);
        const back  = slotBuf(slotIdx, backKey);
        const loadingEl = slotLoading(slotIdx);
        const errorEl   = slotError(slotIdx);
        const hasVisibleImage = front.classList.contains('active');
        if (!hasVisibleImage) loadingEl.classList.add('visible');
        errorEl.classList.remove('visible');
        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const ab = await resp.arrayBuffer();
            if (reqId !== activeRequests[slotIdx]) return;
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            gtSlotDecoded[slotIdx] = decoded;'''
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
            gtSlotDecoded[slotIdx] = decoded;'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_gtDecodedCache' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_DECL, NEW_DECL, 'cache decl')
    src = rep(src, OLD_LOAD, NEW_LOAD, 'carregar cache+loading')

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
