#!/usr/bin/env python3
"""
Patch: gtDeriveTifUrl também troca o segmento /fig/ por /geotiff/ no path,
além de trocar a extensão .png/.gif/.jpg por .tif. Necessário para o
FTP do CPTEC onde PNGs ficam em .../fig/ e TIFFs em .../geotiff/.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''    function gtDeriveTifUrl(url) {
        // Substitui a extensão final png/gif/jpg/jpeg por tif, preservando query string.
        return String(url || '').replace(/\\.(png|gif|jpe?g)(\\?.*)?$/i, '.tif$2');
    }'''
NEW = '''    function gtDeriveTifUrl(url) {
        // Para o FTP do CPTEC: PNGs ficam em .../fig/ e TIFFs em .../geotiff/.
        // Substitui o segmento /fig/ por /geotiff/ (literal, não toca nomes tipo fig_uvo)
        // e troca a extensão final png/gif/jpg/jpeg por tif, preservando query string.
        let u = String(url || '');
        u = u.replace(/\\/fig\\//g, '/geotiff/');
        u = u.replace(/\\.(png|gif|jpe?g)(\\?.*)?$/i, '.tif$2');
        return u;
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if '/fig/' in src and 'geotiff/' in src and 'gtDeriveTifUrl' in src and 'fig_uvo' in src:
        # Heurística simples
        if "u.replace(/\\/fig\\//" in src:
            print(f"[{path.name}] já patcheado; pulando.")
            return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    new = src.replace(OLD, NEW, 1)
    if dry:
        print(f"[{path.name}] dry-run: {len(new)-len(src):+d} bytes")
        return True
    path.write_text(new, encoding='utf-8')
    print(f"[{path.name}] ok ({len(new)-len(src):+d})")
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
