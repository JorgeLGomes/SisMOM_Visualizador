#!/usr/bin/env python3
"""
Patch: aproveitamento de altura total no dashboard GeoTIFF inline.
- Modal inline ocupa height: calc(100vh - <header>)
- Container canvas+mapa SEM max-height:60vh; cresce com flex:1
- Canvas e canvas do mapa em height:100%
- Side panel com altura total + scroll interno
- Atribuição reposicionada para não sobrepor controles
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# CSS atual da classe .inline: vamos expandir e adicionar regras de altura cheia
OLD_CSS = '''#modalGeoTIFF.inline { position: static; background: transparent; padding: 0; display: block !important; height: auto; }
        #modalGeoTIFF.inline > .modal { max-width: none; width: 100%; box-shadow: none; border-radius: 0; max-height: none; }
        #modalGeoTIFF.inline > .modal > .modal-header { display: none; }
        #mainGT { padding: 12px 16px; }'''
NEW_CSS = '''#modalGeoTIFF.inline { position: static; background: transparent; padding: 0; display: block !important; height: auto; }
        #modalGeoTIFF.inline > .modal { max-width: none; width: 100%; box-shadow: none; border-radius: 0; max-height: none; height: calc(100vh - 70px); display: flex; flex-direction: column; }
        #modalGeoTIFF.inline > .modal > .modal-header { display: none; }
        #modalGeoTIFF.inline > .modal > .modal-body { flex: 1 1 auto; min-height: 0; overflow: hidden; padding: 8px 12px; }
        #modalGeoTIFF.inline .modal-body.gt-organized { height: 100%; align-items: stretch; }
        #modalGeoTIFF.inline .gt-main-col { height: 100%; min-height: 0; }
        /* O div que envolve os canvases (raster + mapa) ocupa toda altura disponível */
        #modalGeoTIFF.inline .gt-main-col > div { max-height: none !important; }
        #modalGeoTIFF.inline .gt-main-col > div:has(#gtMapCanvas),
        #modalGeoTIFF.inline .gt-main-col > div:has(#gtCanvas) { flex: 1 1 auto; min-height: 0; height: 100%; }
        #modalGeoTIFF.inline #gtMapCanvas { height: 100% !important; width: 100% !important; }
        #modalGeoTIFF.inline #gtCanvas { max-width: 100%; max-height: 100%; width: auto; height: auto; }
        #modalGeoTIFF.inline #gtAttrib { right: 6px; bottom: 6px; }
        #mainGT { padding: 8px 12px; height: calc(100vh - 60px); box-sizing: border-box; }'''

# Também precisamos garantir que o JS de gtReorganizeLayout marque o container do canvas
# para o CSS poder localizar. Vou adicionar uma classe no container quando movido pro main-col.
OLD_REORG_MOVE = '''            // Container que contém os canvases (#gtCanvas e #gtMapCanvas)
            if (el.querySelector && (el.querySelector('#gtCanvas') || el.querySelector('#gtMapCanvas'))) {
                main.appendChild(el); continue;
            }'''
NEW_REORG_MOVE = '''            // Container que contém os canvases (#gtCanvas e #gtMapCanvas)
            if (el.querySelector && (el.querySelector('#gtCanvas') || el.querySelector('#gtMapCanvas'))) {
                el.classList.add('gt-canvas-wrap');
                el.style.display = 'flex';
                el.style.alignItems = 'center';
                el.style.justifyContent = 'center';
                main.appendChild(el); continue;
            }'''

# Substituir a regra CSS dependente de :has (compat) por classe explícita
OLD_CSS2 = '''        #modalGeoTIFF.inline .gt-main-col > div:has(#gtMapCanvas),
        #modalGeoTIFF.inline .gt-main-col > div:has(#gtCanvas) { flex: 1 1 auto; min-height: 0; height: 100%; }'''
NEW_CSS2 = '''        #modalGeoTIFF.inline .gt-main-col > .gt-canvas-wrap { flex: 1 1 auto; min-height: 0; height: 100%; }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gt-canvas-wrap' in src:
        print(f"[{path.name}] já patcheado (gt-canvas-wrap); pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS,        NEW_CSS,        'css inline fullheight')
    src = rep(src, OLD_CSS2,       NEW_CSS2,       'css canvas-wrap class')
    src = rep(src, OLD_REORG_MOVE, NEW_REORG_MOVE, 'add gt-canvas-wrap class')

    if src == original: return False
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(original)} -> {len(src)}, {len(src)-len(original):+d})")
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
