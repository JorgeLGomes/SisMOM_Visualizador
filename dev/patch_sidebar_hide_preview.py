#!/usr/bin/env python3
"""
Patch: no modo gt-sidebar (multi-painel), esconder a miniatura/preview do
GeoTIFF que estava aparecendo dentro do próprio painel direito.

O painel direito agora é só de CONTROLES: paleta, min/max, UNDEF/clip,
camadas extras, calculadora etc. A figura grande no centro (Mi ativo) é
o único elemento visualizado.

Esconde:
- .gt-main-col (toda a coluna principal do modal: canvas raster, mapa,
  HUD de zoom, gtInfo com nome do arquivo, attribution)
- #gtCanvas, #gtMapCanvas, #gtInfo, #gtAttrib, .gt-bottom-hud
  (redundância caso o gt-main-col não exista)

Faz o aside#gtSidePanel ocupar 100% da largura no modo sidebar.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''        #modalGeoTIFF.gt-sidebar > .modal > .modal-body { flex: 1; overflow-y: auto; padding: 8px 10px; }
        body.gt-mode-active main.main { padding-right: 340px; }'''
NEW = '''        #modalGeoTIFF.gt-sidebar > .modal > .modal-body { flex: 1; overflow-y: auto; padding: 8px 10px; }
        /* Em modo sidebar, esconde a "preview" do GeoTIFF (canvas raster + mapa + HUD): o painel direito é só de controles. */
        #modalGeoTIFF.gt-sidebar .gt-main-col { display: none !important; }
        #modalGeoTIFF.gt-sidebar #gtCanvas,
        #modalGeoTIFF.gt-sidebar #gtMapCanvas,
        #modalGeoTIFF.gt-sidebar #gtAttrib,
        #modalGeoTIFF.gt-sidebar .gt-bottom-hud { display: none !important; }
        /* Side panel ocupa toda a largura */
        #modalGeoTIFF.gt-sidebar #gtSidePanel { width: 100% !important; max-width: none !important; flex: 1 1 auto !important; }
        body.gt-mode-active main.main { padding-right: 340px; }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'esconde a "preview" do GeoTIFF' in src:
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
