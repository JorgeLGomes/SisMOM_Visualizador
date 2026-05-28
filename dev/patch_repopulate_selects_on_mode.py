#!/usr/bin/env python3
"""
Patch: forçar atualizarSlotsControles ao trocar de aba.

populateModeloSelect filtra modelos por appMode (PNG vs GeoTIFF), mas só
roda dentro de atualizarSlotsControles. Em setAppMode:
- Se houver snapshot salvo da aba destino, _stateRestore chama setLayout
  que chama atualizarSlotsControles → filtro aplica.
- Se NÃO houver snapshot, nada chama atualizarSlotsControles → o select
  permanece com as opções da aba anterior. Resultado: modelos sem TIF
  (ex: MERGE com tem_tif=false) aparecem no dashboard GeoTIFF.

Correção: setAppMode sempre chama atualizarSlotsControles após a troca
de modo, garantindo que os <select data-cfg="modelo"> sejam filtrados
conforme a aba atual.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''        document.body.classList.toggle('gt-mode-active', mode === 'gtiff');
        if (mode === 'png') {
            // Limpa artefatos do modo gtiff: classe gt-map-active e canvas do mapa
            document.querySelectorAll('.map-box.gt-map-active').forEach(b => {
                b.classList.remove('gt-map-active');
            });
            document.querySelectorAll('.map-canvas-gt').forEach(c => {
                c.style.display = 'none';
            });
            // Força re-render dos slots com URLs PNG (caso _stateRestore não tenha disparado)
            try { renderTudo(); } catch (_) {}
        }'''
NEW = '''        document.body.classList.toggle('gt-mode-active', mode === 'gtiff');
        // Sempre repopular os selects (modelo/variavel) com filtro da nova aba.
        // Sem isso, modelos com tem_tif=false ainda apareceriam no GeoTIFF e
        // vice-versa quando não há snapshot salvo da aba destino.
        try { if (typeof atualizarSlotsControles === 'function') atualizarSlotsControles(); } catch (_) {}
        if (mode === 'png') {
            // Limpa artefatos do modo gtiff: classe gt-map-active e canvas do mapa
            document.querySelectorAll('.map-box.gt-map-active').forEach(b => {
                b.classList.remove('gt-map-active');
            });
            document.querySelectorAll('.map-canvas-gt').forEach(c => {
                c.style.display = 'none';
            });
            // Força re-render dos slots com URLs PNG (caso _stateRestore não tenha disparado)
            try { renderTudo(); } catch (_) {}
        }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if "Sempre repopular os selects (modelo/variavel) com filtro da nova aba" in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    src = src.replace('20260528-0200-mapenable', '20260528-0230-repopulate')
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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0230-repopulate")

if __name__ == '__main__':
    main()
