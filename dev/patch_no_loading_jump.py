#!/usr/bin/env python3
"""
Patch: não mostrar mensagem "Carregando URL..." no #gtInfo, que causava
quebra de linha (URL longa) e o painel "saltava" durante a animação.
O #gtInfo mantém o último estado válido (dimensões/bbox/nodata) enquanto
o próximo passo é decodificado. Em caso de erro, a mensagem aparece.
Também trava altura mínima maior + nowrap para nunca refluir.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Remover o textContent='Carregando URL…' antes do fetch
OLD = '''        const info = document.getElementById('gtInfo');
        if (info) info.textContent = 'Carregando ' + url + '…';
        try {'''
NEW = '''        const info = document.getElementById('gtInfo');
        // Não sobrescreve o #gtInfo com "Carregando..." (URL longa causava
        // reflow/salto durante animação). Mantém o estado anterior enquanto
        // o próximo passo decodifica. Só atualiza em caso de erro.
        try {'''

# (2) Estilizar #gtInfo: nowrap + ellipsis + altura travada para nunca refluir
OLD_INFO_HTML = '''<div id="gtInfo" style="color:var(--text-muted);font-size:12px;margin-bottom:8px;min-height:1em">Abra um arquivo .tif/.tiff para visualizar.</div>'''
NEW_INFO_HTML = '''<div id="gtInfo" style="color:var(--text-muted);font-size:12px;margin-bottom:8px;height:1.4em;line-height:1.4em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Abra um arquivo .tif/.tiff para visualizar.</div>'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    # Idempotência
    if "Não sobrescreve o #gtInfo com" in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD,           NEW,           'remove loading msg')
    src = rep(src, OLD_INFO_HTML, NEW_INFO_HTML, 'fix info height')

    if src == original: return False
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(src)-len(original):+d})")
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
