#!/usr/bin/env python3
"""
Patch: ao trocar modelo/variável na toolbar do dashboard GeoTIFF, chamar
atualizarMaxPassos() para recalcular state.maxPassos/stepFreq, fazer snap
do passoAtual e re-renderizar o painel PASSOS DE TEMPO da sidebar.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD_M = '''        if (ms) { ms._gtBound = true; ms.addEventListener('change', () => {
            const id = ms.value;
            state.slots[0].modelo = id;
            // Atualiza variável para a primeira do novo modelo
            const m = modelos[id];
            if (m && Array.isArray(m.variaveis) && m.variaveis.length) {
                state.slots[0].variavel = m.variaveis[0].id;
            }
            gtSyncToolbarFromState();
            try { renderTudo(); } catch (_) {}
        }); }
        if (vs) vs.addEventListener('change', () => {
            state.slots[0].variavel = vs.value;
            gtSyncToolbarFromState();
            try { renderTudo(); } catch (_) {}
        });'''
NEW_M = '''        if (ms) { ms._gtBound = true; ms.addEventListener('change', () => {
            const id = ms.value;
            state.slots[0].modelo = id;
            const m = modelos[id];
            if (m && Array.isArray(m.variaveis) && m.variaveis.length) {
                state.slots[0].variavel = m.variaveis[0].id;
            }
            // Recalcula state.maxPassos/stepFreq + snap do passoAtual e repinta o painel PASSOS DE TEMPO
            try { atualizarMaxPassos(); } catch (_) {}
            gtSyncToolbarFromState();
            try { renderTudo(); } catch (_) {}
        }); }
        if (vs) vs.addEventListener('change', () => {
            state.slots[0].variavel = vs.value;
            try { atualizarMaxPassos(); } catch (_) {}
            gtSyncToolbarFromState();
            try { renderTudo(); } catch (_) {}
        });'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'atualizarMaxPassos(); } catch (_) {}\n            gtSyncToolbarFromState' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD_M) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD_M)}")
    new = src.replace(OLD_M, NEW_M, 1)
    if dry: print(f"[{path.name}] dry-run: {len(new)-len(src):+d} bytes"); return True
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
