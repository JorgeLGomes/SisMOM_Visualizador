#!/usr/bin/env python3
"""
Patch: em modo gtiff multi-painel, gtLoadFromState() é redundante e
potencialmente perigoso: ele faz um fetch+decode separado do mesmo URL
para popular o pipeline antigo do modal (gtCanvas/gtMap, ambos escondidos
em .gt-sidebar), e sobrescreve gtLastDecoded em paralelo com o pipeline
do slot.

Concorrência com o pipeline do slot (carregarGeoTIFFParaSlot do slot 0):
- Os dois rodam em paralelo via Promise.all-ish (sem await em
  renderTudo). gtLoadFromState pode escrever em gtLastDecoded DEPOIS do
  slot ter atualizado a UI (colorbar, info), levando a estado
  inconsistente.
- gtRenderar dentro de gtLoadFromState chama gtSyncMapOverlay e
  aplicarPaleta novamente (custo CPU duplicado) e pode pintar o
  gtCanvas oculto, gerando atividade desnecessária no event loop.

Correção: gtLoadFromState abandona cedo se appMode==='gtiff'. Tudo que
era necessário acontecer (colorbar, info, render do slot) já é feito
pelo pipeline novo de slot. A função permanece intacta para casos
legados (modal pop-up manual).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''    async function gtLoadFromState() {
        if (appMode !== 'gtiff') return;
        if (!state || !state.slots || !state.slots[0]) return;'''
NEW = '''    async function gtLoadFromState() {
        // Em modo gtiff multi-painel, o pipeline novo (carregarGeoTIFFParaSlot
        // do slot 0) já cuida do fetch+decode+render. Este caminho legado é
        // do modal pop-up; rodá-lo em paralelo gera concorrência e CPU
        // desnecessária. Abandona-se cedo.
        return;
        if (appMode !== 'gtiff') return;
        if (!state || !state.slots || !state.slots[0]) return;'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'Em modo gtiff multi-painel, o pipeline novo' in src:
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
