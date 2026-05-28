#!/usr/bin/env python3
"""
Rebrand: SisMOM Visualizador  →  GISELE (Gestão Integrada de Soluções
Estratégicas e Inteligência).

Estratégia:
  - User-facing: tudo renomeado para GISELE.
  - Internos (filename, classes JS, localStorage keys): preservados
    para compatibilidade com dados/configs já salvos.

Itens renomeados:
  HTML
   - <title>
   - <meta name=description>
   - .brand-title  (frase longa do header)
   - .brand-sub
   - build marker "[SisMOM] build = ..." → "[GISELE] build = ..."
   - Build tag: 20260528-0400-untruncate → 20260528-0500-gisele

Itens preservados (NÃO mudar):
   - Filename: figuras_SisMOM_v23.html
   - SisMOM_Map, SisMOM_GeoTIFF (vars JS)
   - localStorage: sismom_state_*, sismom_app_mode, sismom_gt_*
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

SUBS = [
    # <title>
    ('<title>SisMOM · Monitoramento de Óleo no Mar — Dashboard</title>',
     '<title>GISELE · Gestão Integrada de Soluções Estratégicas e Inteligência</title>'),
    # <meta description>
    ('<meta name="description" content="SisMOM Dashboard — Visualização de modelos meteorológicos operacionais do CPTEC/INPE">',
     '<meta name="description" content="GISELE — Gestão Integrada de Soluções Estratégicas e Inteligência. Visualização de modelos meteorológicos operacionais do CPTEC/INPE.">'),
    # Brand title
    ('<div class="brand-title">Sistema Multiusuário de Detecção, Previsão e Monitoramento de Derrame de Óleo no Mar</div>',
     '<div class="brand-title">GISELE — Gestão Integrada de Soluções Estratégicas e Inteligência</div>'),
    # Brand sub
    ('<div class="brand-sub">SisMOM · MCTI</div>',
     '<div class="brand-sub">SisMOM · CPTEC/INPE · MCTI</div>'),
    # Build marker prefix
    ("'[SisMOM] build = ", "'[GISELE] build = "),
    # Build tag
    ('20260528-0400-untruncate', '20260528-0500-gisele'),
]


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    for old, new in SUBS:
        if old in src:
            src = src.replace(old, new)
    if src == original:
        print(f"[{path.name}] nada a fazer; já rebranded.")
        return False
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
        print(f"OK - {len(a)} bytes em ambas - build 20260528-0500-gisele")


if __name__ == '__main__':
    main()
