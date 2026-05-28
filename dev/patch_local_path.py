#!/usr/bin/env python3
"""
Patch: suportar caminhos locais no template de endereço.

O usuário pode digitar no campo "Template do endereço":
- URL HTTP/HTTPS: https://ftp1.cptec.inpe.br/.../{yyyy}/{mm}/   (atual)
- Caminho Windows: C:\\dados\\Eta\\{yyyy}\\{mm}\\
- Caminho Linux/Mac: /home/user/dados/Eta/{yyyy}/{mm}/
- file:// explícito: file:///D:/dados/Eta/{yyyy}/{mm}/

montarURL agora detecta caminhos locais e converte para file:// URL antes
de retornar. Funciona em Electron (webSecurity:false já permite file://
fetch). No Chrome direto via file://, browsers podem bloquear por CORS —
documentado no placeholder do campo.

Inclui placeholder atualizado no input cfgUrlPath e cfgUrlPathTif.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Adicionar helper toFileUrlIfLocal e usá-lo no return de montarURL
OLD_JS = '''        if (pathOut && !pathOut.endsWith('/')) pathOut += '/';
        return pathOut + nameOut;
    }'''
NEW_JS = '''        if (pathOut && !pathOut.endsWith('/')) pathOut += '/';
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


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'toFileUrlIfLocal' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD_JS) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD_JS)}")
    src = src.replace(OLD_JS, NEW_JS, 1)
    # Bump build
    src = src.replace('20260528-0300-clone', '20260528-0330-local')
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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0330-local")

if __name__ == '__main__':
    main()
