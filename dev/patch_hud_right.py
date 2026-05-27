#!/usr/bin/env python3
"""
Patch: reposicionar HUD inferior alinhado à direita (canto inferior direito)
e atribuição (gtAttrib) para o canto inferior esquerdo — padrão de mapas
estilo Leaflet (zoom controls direita-inferior, créditos esquerda-inferior).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) HUD: de centro para direita
OLD_HUD_POS = '''.gt-bottom-hud {
            position: absolute;
            left: 50%; transform: translateX(-50%);
            bottom: 16px;'''
NEW_HUD_POS = '''.gt-bottom-hud {
            position: absolute;
            right: 12px; left: auto; transform: none;
            bottom: 14px;'''

# (2) Atribuição: mudar do canto direito para canto esquerdo (.inline override)
OLD_ATTRIB = '''#modalGeoTIFF.inline #gtAttrib { right: 6px; bottom: 6px; }'''
NEW_ATTRIB = '''#modalGeoTIFF.inline #gtAttrib { right: auto; left: 8px; bottom: 8px; }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'right: 12px; left: auto;' in src and 'left: 8px; bottom: 8px' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HUD_POS, NEW_HUD_POS, 'hud right anchor')
    src = rep(src, OLD_ATTRIB,  NEW_ATTRIB,  'attrib left anchor')

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
        print('OK - ' + str(len(a)) + ' bytes em ambas')

if __name__ == '__main__':
    main()
