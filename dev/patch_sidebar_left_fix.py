#!/usr/bin/env python3
"""
Patch: corrigir posicionamento da sidebar GeoTIFF que estava esticando até a
borda esquerda da tela. .modal-backdrop tem `inset: 0` (= left:0 também), e
meu CSS sobrescrevia só top/right/bottom/width — left herdado permanecia.
Adicionado `left: auto !important` (e !important nos outros para garantir).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''        #modalGeoTIFF.gt-sidebar { position: fixed; top: 60px; right: 0; bottom: 0; width: 340px;
                                     background: var(--bg-elev-1, #0e1622); border-left: 1px solid var(--border-subtle);
                                     z-index: 30; padding: 0; display: block !important; overflow: hidden; }'''
NEW = '''        #modalGeoTIFF.gt-sidebar { position: fixed !important; top: 60px !important; right: 0 !important;
                                     bottom: 0 !important; left: auto !important; width: 340px !important;
                                     background: var(--bg-elev-1, #0e1622); border-left: 1px solid var(--border-subtle);
                                     z-index: 30; padding: 0; display: block !important; overflow: hidden;
                                     align-items: stretch !important; justify-content: flex-start !important;
                                     backdrop-filter: none !important; }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'left: auto !important' in src and 'gt-sidebar' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    new = src.replace(OLD, NEW, 1)
    if dry: print(f"[{path.name}] dry-run"); return True
    path.write_text(new, encoding='utf-8')
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
        print("OK")

if __name__ == '__main__':
    main()
