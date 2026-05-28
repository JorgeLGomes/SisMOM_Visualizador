#!/usr/bin/env python3
"""
Reverte o patch de caminho local (toFileUrlIfLocal) por ter quebrado algo.
Volta o return de montarURL ao original, remove a função helper, e
restaura os placeholders dos inputs cfgUrlPath / cfgUrlPathTif.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Reverter montarURL: return original + remove função helper
OLD = '''        if (pathOut && !pathOut.endsWith('/')) pathOut += '/';
        return toFileUrlIfLocal(pathOut + nameOut);
    }
    /* Converte caminho local (Windows C:\\... ou Unix /...) em file:// URL,
       para que fetch consiga ler. URLs http/https/file/blob/data passam direto. */
    function toFileUrlIfLocal(s) {
        if (!s) return s;
        if (/^(https?|file|blob|data):/i.test(s)) return s;
        let u = String(s).replace(/\\\\/g, '/');
        // Windows: "C:/..."
        if (/^[A-Za-z]:\\//.test(u)) return 'file:///' + u;
        // Unix: "/home/..."
        if (u.startsWith('/')) return 'file://' + u;
        // Fallback: relativo ao documento atual (improvável funcionar bem)
        return s;
    }'''
NEW = '''        if (pathOut && !pathOut.endsWith('/')) pathOut += '/';
        return pathOut + nameOut;
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'toFileUrlIfLocal' not in src:
        print(f"[{path.name}] já revertido; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)

    # Reverte placeholders
    src = src.replace(
        '<input type="text" id="cfgUrlPath" placeholder="https://... ou caminho local (C:\\dados\\{yyyy}\\{mm}\\ ou /home/dados/{yyyy}/)" title="Aceita URL HTTP(S) ou caminho local. Local (file://) funciona no Electron app; no Chrome direto pode ser bloqueado por CORS.">',
        '<input type="text" id="cfgUrlPath" placeholder="https://.../{yyyy}{mm}{dd}{hh}/{escopo1}/{escopo2}/fig">'
    )
    src = src.replace(
        '<input type="text" id="cfgUrlPathTif" placeholder="https://... ou caminho local (C:\\geotif\\{yyyy}\\{mm}\\ ou /home/geotif/{yyyy}/)" title="Aceita URL HTTP(S) ou caminho local. Local (file://) funciona no Electron app.">',
        '<input type="text" id="cfgUrlPathTif" placeholder="https://.../{yyyy}{mm}{dd}{hh}/{escopo1}/{escopo2}/geotiff">'
    )
    src = src.replace('20260528-0330-local', '20260528-0340-reverted')

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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0340-reverted")

if __name__ == '__main__':
    main()
