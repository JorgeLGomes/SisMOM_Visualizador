#!/usr/bin/env python3
"""
Patch: filtrar modelos e variáveis no dashboard conforme a aba ativa.

- Aba PNG/GIF: só lista modelos com tem_png !== false e variáveis com
  disp_png !== false (default true).
- Aba GeoTIFF: só lista modelos com tem_tif === true (ou modelos legacy
  sem tem_png/tem_tif setados — aceita) e variáveis com disp_tif !== false.

Aplicado em populateModeloSelect e populateVariavelSelect (que populam
os <select data-cfg="modelo"> / data-cfg="variavel"> nos painéis Mi).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD_MOD = '''    function populateModeloSelect(selEl, currentValue) {
        selEl.innerHTML = '';
        // só lista modelos acessíveis (protegidos exigem 2FA desbloqueado)
        const ids = modelosAcessiveis();
        ids.forEach(id => {
            const opt = document.createElement('option');
            opt.value = id;
            opt.textContent = modelos[id].nome || id;
            selEl.appendChild(opt);
        });
        if (currentValue && ids.includes(currentValue)) {
            selEl.value = currentValue;
        } else if (ids.length) {
            selEl.value = ids[0];
        }
    }'''
NEW_MOD = '''    function _modeloFitsMode(id, mode) {
        const m = modelos[id]; if (!m) return false;
        if (mode === 'gtiff') {
            // GeoTIFF: requer tem_tif === true. Modelos legacy (sem flags) também aceitos.
            if (m.tem_tif === false) return false;
            if (m.tem_png === true && m.tem_tif !== true) return false;
            return true;
        }
        // png/gif: requer tem_png !== false (default true)
        if (m.tem_png === false) return false;
        if (m.tem_tif === true && m.tem_png !== true) return false;
        return true;
    }
    function populateModeloSelect(selEl, currentValue) {
        selEl.innerHTML = '';
        // só lista modelos acessíveis (protegidos exigem 2FA desbloqueado) E compatíveis com a aba
        const mode = (typeof appMode !== 'undefined') ? appMode : 'png';
        const ids = modelosAcessiveis().filter(id => _modeloFitsMode(id, mode));
        ids.forEach(id => {
            const opt = document.createElement('option');
            opt.value = id;
            opt.textContent = modelos[id].nome || id;
            selEl.appendChild(opt);
        });
        if (currentValue && ids.includes(currentValue)) {
            selEl.value = currentValue;
        } else if (ids.length) {
            selEl.value = ids[0];
        }
    }'''

OLD_VAR = '''    function populateVariavelSelect(selEl, modeloId, currentValue) {
        selEl.innerHTML = '';
        const m = modelos[modeloId];
        if (!m || !m.variaveis) return;
        m.variaveis.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.textContent = v.label + (v.unidade ? ` (${v.unidade})` : '');
            selEl.appendChild(opt);
        });
        if (currentValue && m.variaveis.some(v => v.id === currentValue)) {
            selEl.value = currentValue;
        } else if (m.variaveis.length) {
            selEl.value = m.variaveis[0].id;
        }
    }'''
NEW_VAR = '''    function _varFitsMode(v, mode) {
        if (!v) return false;
        if (mode === 'gtiff') return v.disp_tif !== false;
        return v.disp_png !== false;
    }
    function populateVariavelSelect(selEl, modeloId, currentValue) {
        selEl.innerHTML = '';
        const m = modelos[modeloId];
        if (!m || !m.variaveis) return;
        const mode = (typeof appMode !== 'undefined') ? appMode : 'png';
        const vars = m.variaveis.filter(v => _varFitsMode(v, mode));
        vars.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.textContent = v.label + (v.unidade ? ` (${v.unidade})` : '');
            selEl.appendChild(opt);
        });
        if (currentValue && vars.some(v => v.id === currentValue)) {
            selEl.value = currentValue;
        } else if (vars.length) {
            selEl.value = vars[0].id;
        }
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_modeloFitsMode' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_MOD, NEW_MOD, 'populateModeloSelect filter')
    src = rep(src, OLD_VAR, NEW_VAR, 'populateVariavelSelect filter')
    # Bump build
    src = src.replace('20260528-0100-modeswitch', '20260528-0120-filter')
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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0120-filter")

if __name__ == '__main__':
    main()
