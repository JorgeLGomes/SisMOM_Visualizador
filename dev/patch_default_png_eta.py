#!/usr/bin/env python3
"""
Patch: ao abrir o app, sempre iniciar na aba PNG/GIF com o modelo Eta,
independentemente do estado salvo na sessão anterior.

- appMode forçado a 'png' no startup (ignora localStorage).
- O estado salvo de gtiff em localStorage continua preservado: ao
  usuário clicar na aba GeoTIFF, ele retoma de onde parou.
- O modelo Eta já é forçado em state.slots[0] no inicializar(); apenas
  garantir que ele aparece em qualquer aba que tem tem_png !== false.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''    let appMode = (function () {
        try { return localStorage.getItem('sismom_app_mode') || 'png'; } catch (_) { return 'png'; }
    })();'''
NEW = '''    // Padrão de abertura: SEMPRE PNG/GIF (ignora localStorage). O estado salvo
    // por aba (sismom_state_gtiff) continua disponível: ao clicar na aba GeoTIFF
    // o usuário retoma a configuração anterior daquela aba.
    let appMode = 'png';
    try { localStorage.setItem('sismom_app_mode', 'png'); } catch (_) {}'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if "Padrão de abertura: SEMPRE PNG/GIF" in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    src = src.replace('20260528-0120-filter', '20260528-0150-defpng')
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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0150-defpng")

if __name__ == '__main__':
    main()
