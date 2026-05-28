#!/usr/bin/env python3
"""
Patch: marcador de versão visível para diagnosticar cache do browser/Electron.

- console.log com timestamp da build (data atual em segundos)
- atributo data-build no <html> com o mesmo timestamp
- pequeno texto " · build XX" anexado ao tooltip do badge GeoTIFF

Como verificar:
1. Abra DevTools (F12) > Console. Procure a linha "[SisMOM] build = BUILD_TAG".
2. Se NÃO aparecer, o browser/Electron está servindo versão cacheada.
   Faça Ctrl+Shift+R (hard reload) ou feche e reabra a aplicação.
"""
import sys, time
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

BUILD = "20260528-0010-flickfix"

# (1) Substituir marcador antigo (se existir) ou inserir após `function inicializar() {`
OLD = '''    function inicializar() {
        loadModelos();'''
NEW = f'''    function inicializar() {{
        try {{ console.log('[SisMOM] build = {BUILD}'); document.documentElement.setAttribute('data-build', '{BUILD}'); }} catch (_) {{}}
        loadModelos();'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    # Remove qualquer marcador anterior
    import re
    src = re.sub(r"        try \{ console\.log\('\[SisMOM\] build = [^']*'\);[^\n]*\n", "", src)
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
        print("OK - " + str(len(a)) + " bytes em ambas - build " + BUILD)

if __name__ == '__main__':
    main()
