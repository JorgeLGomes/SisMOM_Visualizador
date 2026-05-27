#!/usr/bin/env python3
"""
Patch: reposicionar o botão de ocultar o painel direito (›/‹) para o centro
vertical, longe do chevron do accordion. Também move o chevron das seções
para a borda DIREITA do header (em vez de inicio), separando ainda mais os
dois controles.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Mover botão para centro vertical
OLD_CSS_BTN = '''.gt-side-toggle { position: absolute; right: 0; top: 6px; z-index: 5; background: rgba(40,55,80,0.92);
                           color: var(--text, #cbd6e6); border: 1px solid rgba(255,255,255,0.14);
                           border-radius: 4px 0 0 4px; cursor: pointer; width: 22px; height: 28px;
                           font-size: 14px; line-height: 26px; padding: 0; transition: right .25s ease; }'''
NEW_CSS_BTN = '''.gt-side-toggle { position: absolute; right: 0; top: 50%; transform: translateY(-50%);
                           z-index: 5; background: rgba(40,55,80,0.92);
                           color: var(--text, #cbd6e6); border: 1px solid rgba(255,255,255,0.14);
                           border-radius: 4px 0 0 4px; cursor: pointer; width: 22px; height: 44px;
                           font-size: 14px; line-height: 42px; padding: 0; transition: right .25s ease; }'''

# (2) Header com chevron à direita (space-between)
OLD_CSS_HEAD = '''.gt-side h4.gt-section-header { cursor: pointer; user-select: none;
                                          display: flex; align-items: center; gap: 4px; transition: color .15s; }'''
NEW_CSS_HEAD = '''.gt-side h4.gt-section-header { cursor: pointer; user-select: none;
                                          display: flex; align-items: center; justify-content: space-between;
                                          gap: 4px; transition: color .15s; }'''

# (3) Inverter onde o chevron é inserido — no JS, era no início; vamos colocar no fim
OLD_CHEV_INS = '''            h.classList.add('gt-section-header');
            const chev = document.createElement('span');
            chev.className = 'gt-section-chevron';
            chev.textContent = '▾';
            h.insertBefore(chev, h.firstChild);'''
NEW_CHEV_INS = '''            h.classList.add('gt-section-header');
            const chev = document.createElement('span');
            chev.className = 'gt-section-chevron';
            chev.textContent = '▾';
            h.appendChild(chev);'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'top: 50%; transform: translateY(-50%);\n                           z-index: 5' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS_BTN,  NEW_CSS_BTN,  'css btn vertical center')
    src = rep(src, OLD_CSS_HEAD, NEW_CSS_HEAD, 'css header space-between')
    src = rep(src, OLD_CHEV_INS, NEW_CHEV_INS, 'chev appended right')

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
