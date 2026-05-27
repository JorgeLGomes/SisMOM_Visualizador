#!/usr/bin/env python3
"""
Patch 1: main.js do Electron com webSecurity:false (CORS desligado para
arquivos hospedados localmente). Permite fetch ao FTP do CPTEC sem
restrição.
Patch 2: melhorar mensagem de erro no HTML mostrando a URL que falhou +
dica sobre webSecurity (caso o usuário esteja em browser).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']
MAIN_JS = ROOT / 'electron-app' / 'main.js'

# (1) main.js: adicionar webSecurity:false
OLD_MAIN = '''    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }'''
NEW_MAIN = '''    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      // Permite fetch a URLs HTTPS externas sem CORS bloqueando (caso do FTP do CPTEC).
      // Como o app é carregado de arquivo local e o tráfego é só leitura de figuras,
      // o risco é baixo. Sem isto, decodificar GeoTIFFs do servidor não funciona.
      webSecurity: false,
      allowRunningInsecureContent: true
    }'''

# (2) HTML: melhorar a mensagem de erro de fetch
OLD_ERR = '''        } catch (e) {
            if (info) info.textContent = 'Falha ao carregar GeoTIFF: ' + ((e && e.message) || e);
        }
    }

    function bindModeTabs() {'''
NEW_ERR = '''        } catch (e) {
            const msg = (e && e.message) || String(e);
            const isCors = /failed to fetch|networkerror|cors/i.test(msg);
            const tip = isCors
                ? ' — Provável CORS: rode no Electron com webSecurity:false (já configurado no main.js após atualizar), ou use um proxy.'
                : '';
            if (info) info.textContent = 'Falha ao carregar GeoTIFF: ' + msg + tip + ' [URL: ' + url + ']';
            console.error('[gtLoadFromState] erro carregando', url, e);
        }
    }

    function bindModeTabs() {'''


def patch_main(dry=False):
    if not MAIN_JS.exists():
        print(f"[main.js] não encontrado em {MAIN_JS}")
        return False
    src = MAIN_JS.read_text(encoding='utf-8')
    if 'webSecurity: false' in src:
        print(f"[main.js] já tem webSecurity:false; pulando.")
        return False
    if src.count(OLD_MAIN) != 1:
        print(f"[main.js] anchor webPreferences não único")
        return False
    new = src.replace(OLD_MAIN, NEW_MAIN, 1)
    if dry:
        print(f"[main.js] dry-run: {len(new)-len(src):+d} bytes")
        return True
    MAIN_JS.write_text(new, encoding='utf-8')
    print(f"[main.js] ok ({len(new)-len(src):+d})")
    return True


def patch_html(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'Provável CORS' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD_ERR) != 1:
        raise RuntimeError(f"[{path.name}] anchor de erro fetch = {src.count(OLD_ERR)}")
    new = src.replace(OLD_ERR, NEW_ERR, 1)
    if dry:
        print(f"[{path.name}] dry-run: {len(new)-len(src):+d} bytes")
        return True
    path.write_text(new, encoding='utf-8')
    print(f"[{path.name}] ok ({len(new)-len(src):+d})")
    return True


def main():
    dry = '--dry-run' in sys.argv
    patch_main(dry=dry)
    changed = 0
    for f in FILES:
        if not f.exists(): sys.exit(2)
        if patch_html(f, dry=dry): changed += 1
    if changed == len(FILES) and not dry:
        a, b = FILES[0].read_bytes(), FILES[1].read_bytes()
        if a != b: sys.exit(3)
        print("OK - HTMLs idênticos: " + str(len(a)) + " bytes")


if __name__ == '__main__':
    main()
