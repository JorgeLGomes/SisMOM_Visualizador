#!/usr/bin/env python3
"""
Patch incremental: forçar redraw do mapa quando o painel lateral colapsa/expande
(a transição CSS leva ~250ms; o ResizeObserver pode demorar a disparar).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''        tgl.addEventListener('click', () => {
            const collapsed = side.classList.toggle('collapsed');
            tgl.textContent = collapsed ? '‹' : '›';
            tgl.title = collapsed ? 'Mostrar painel' : 'Ocultar painel';
        });'''
NEW = '''        tgl.addEventListener('click', () => {
            const collapsed = side.classList.toggle('collapsed');
            tgl.textContent = collapsed ? '‹' : '›';
            tgl.title = collapsed ? 'Mostrar painel' : 'Ocultar painel';
            // Força redraw do mapa após a transição CSS (250ms)
            setTimeout(() => {
                if (typeof _gtMap !== 'undefined' && _gtMap && _gtMap.redraw) _gtMap.redraw();
                // Re-render canvas raster também
                try { if (typeof gtRenderar === 'function') gtRenderar(); } catch (_) {}
                try { if (typeof gtDesenharColorbar === 'function') gtDesenharColorbar(); } catch (_) {}
            }, 280);
        });'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'transição CSS (250ms)' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    c = src.count(OLD)
    if c != 1: raise RuntimeError(f"[{path.name}] anchor = {c}")
    src = src.replace(OLD, NEW, 1)
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok (+{len(src)-len(original)})")
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
