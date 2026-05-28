#!/usr/bin/env python3
"""
Patch: animação não atualizava o raster.

Causa: durante animação, aplicarPaleta (~CPU bound, centenas de ms)
bloqueia a thread principal. A próxima tick do setInterval dispara o
próximo passo, incrementa activeRequests[slotIdx], e o passo corrente
ABORTA na verificação `if (reqId !== activeRequests[slotIdx]) return`
*antes* de chamar setRasterOverlay. Resultado: cada passo atualiza só a
colorbar (parte síncrona pós-fetch) e desiste antes de empurrar o raster
no mapa. O campo congela enquanto a animação roda.

Correção: substituir a checagem `reqId !== activeRequests` (que bloqueia
TODO passo que não seja o último) por um GATE MONOTÔNICO — só aborta se
um passo MAIS NOVO já tiver pintado, garantindo que frames mais antigos
não sobrescrevam frames mais novos, mas permitindo que cada passo
chegue ao setRasterOverlay/blob.

Adicionado _gtSlotLastApplied[i] (último reqId que pintou). _gtTryApply
atualiza-o e retorna true só se reqId >= last. Aplicado em ambos os
caminhos (mapa e img).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Inserir _gtSlotLastApplied + _gtTryApply junto dos outros helpers
OLD_GATE = '''    try { if (typeof window !== 'undefined') window.gtRenderCacheStats = () => ({ size: _gtRenderCache.size, max: _GT_RENDER_MAX }); } catch (_) {}
    function gtSlotEnsureMap(slotIdx) {'''
NEW_GATE = '''    try { if (typeof window !== 'undefined') window.gtRenderCacheStats = () => ({ size: _gtRenderCache.size, max: _GT_RENDER_MAX }); } catch (_) {}
    // Gate monotônico para evitar que frames antigos sobrescrevam novos durante animação.
    const _gtSlotLastApplied = [];
    function _gtTryApply(slotIdx, reqId) {
        const last = _gtSlotLastApplied[slotIdx] || 0;
        if (reqId < last) return false;
        _gtSlotLastApplied[slotIdx] = reqId;
        return true;
    }
    function gtSlotEnsureMap(slotIdx) {'''

# (2) Remover bail antes do setRasterOverlay e usar gate monotônico
OLD_MAP_BAIL = '''                    _gtApplyMapView(slotIdx, m, gt.mapProvider || 'esri', decoded.bbox);
                    const bmp = await gtGetBitmap(entry);
                    if (reqId !== activeRequests[slotIdx]) return;
                    const op = (gt.opacity == null) ? 0.85 : gt.opacity;
                    await m.setRasterOverlay(bmp, decoded.bbox, op);
                    if (reqId !== activeRequests[slotIdx]) return;
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                    return;'''
NEW_MAP_BAIL = '''                    _gtApplyMapView(slotIdx, m, gt.mapProvider || 'esri', decoded.bbox);
                    const bmp = await gtGetBitmap(entry);
                    if (!_gtTryApply(slotIdx, reqId)) return;
                    const op = (gt.opacity == null) ? 0.85 : gt.opacity;
                    await m.setRasterOverlay(bmp, decoded.bbox, op);
                    loadingEl.classList.remove('visible');
                    errorEl.classList.remove('visible');
                    return;'''

# (3) Mesma coisa para o caminho img — remover bail intermediário
OLD_IMG_BAIL = '''            const blobUrl = await gtGetBlobUrl(entry, decoded.width, decoded.height);
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
            back.src = blobUrl;'''
NEW_IMG_BAIL = '''            const blobUrl = await gtGetBlobUrl(entry, decoded.width, decoded.height);
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
            back.src = blobUrl;'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_gtSlotLastApplied' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_GATE,     NEW_GATE,     'gate decl')
    src = rep(src, OLD_MAP_BAIL, NEW_MAP_BAIL, 'map branch gate')
    src = rep(src, OLD_IMG_BAIL, NEW_IMG_BAIL, 'img branch gate')

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
