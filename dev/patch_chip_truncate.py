#!/usr/bin/env python3
"""
Patch: truncar nomes longos em chips de camadas.
Nomes resultantes de cálculos repetidos viravam '(((A + 273) + A) + B...)' que
expandiam horizontalmente, empurrando ↑ ↓ 👁 ✕ pra fora do painel.
- chip ocupa 100% da largura do painel
- gl-name tem min-width:0 + ellipsis + tooltip com nome completo
- botões com flex-shrink:0 para não encolherem
- painel lateral com overflow-x: hidden
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) CSS: estende regras dos chips para travar largura e impedir overflow
OLD_CSS = '''.gt-layer-item { display: flex; align-items: center; gap: 4px; padding: 4px 6px; border-radius: 4px;
                          background: rgba(255,255,255,0.04); margin-bottom: 4px; cursor: pointer;
                          border: 1px solid transparent; }
        .gt-layer-item.active { border-color: var(--accent-cyan, #4dd0e1); background: rgba(77,208,225,0.10); }
        .gt-layer-item .gl-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; }
        .gt-layer-item button { background: none; border: 0; color: inherit; cursor: pointer; padding: 0 3px;
                                  font-size: 12px; line-height: 1; }
        .gt-layer-item .gl-dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; }
        .gt-layer-item .gl-rm { color: #f88; font-size: 14px; font-weight: 700; }'''
NEW_CSS = '''.gt-layer-item { display: flex; align-items: center; gap: 4px; padding: 4px 6px; border-radius: 4px;
                          background: rgba(255,255,255,0.04); margin-bottom: 4px; cursor: pointer;
                          border: 1px solid transparent;
                          width: 100%; box-sizing: border-box; min-width: 0; max-width: 100%; }
        .gt-layer-item.active { border-color: var(--accent-cyan, #4dd0e1); background: rgba(77,208,225,0.10); }
        .gt-layer-item .gl-name { flex: 1 1 0; min-width: 0; overflow: hidden; text-overflow: ellipsis;
                                    white-space: nowrap; font-size: 12px; }
        .gt-layer-item button { background: none; border: 0; color: inherit; cursor: pointer; padding: 0 3px;
                                  font-size: 12px; line-height: 1; flex: 0 0 auto; }
        .gt-layer-item .gl-dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; }
        .gt-layer-item .gl-rm { color: #f88; font-size: 14px; font-weight: 700; }
        /* Container dos chips: full width vertical (cada chip ocupa uma linha) */
        #gtLayerChips { display: flex !important; flex-direction: column; width: 100%; min-width: 0; gap: 4px; }
        /* Painel lateral: trava overflow horizontal para não criar scroll lateral */
        #gtSidePanel, .gt-side { overflow-x: hidden; }'''

# (2) gtRenderLayerChips: adicionar tooltip com nome completo no .gl-name
OLD_NAME = '''            const name = document.createElement('span');
            name.className = 'gl-name';
            name.textContent = l.name || l.id;
            name.style.opacity = (l.visible === false) ? '0.45' : '1';'''
NEW_NAME = '''            const name = document.createElement('span');
            name.className = 'gl-name';
            const fullName = l.name || l.id;
            name.textContent = fullName;
            name.title = fullName;
            name.style.opacity = (l.visible === false) ? '0.45' : '1';'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gt-layer-item .gl-name { flex: 1 1 0' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS,  NEW_CSS,  'css chip truncate')
    src = rep(src, OLD_NAME, NEW_NAME, 'name tooltip')

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
