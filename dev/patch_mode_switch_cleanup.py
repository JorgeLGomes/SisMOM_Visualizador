#!/usr/bin/env python3
"""
Patch: corrigir bug onde voltar para PNG/GIF mantém a imagem do TIF.

Causas:
1. setAppMode só chama renderTudo() em modo gtiff. Em PNG, depende de
   _stateRestore que pode não rodar se não há snap salvo. Slot fica
   com a img antiga (blob URL do TIF).
2. Se o usuário estava com Mostrar mapa ON no GeoTIFF mode, a classe
   .gt-map-active no .map-box continua aplicada → CSS esconde os <img>
   no PNG mode. Visual: canvas vazio/com TIF.
3. O canvas .map-canvas-gt fica com display:'' (setado em modo mapa) e
   continua visível na frente dos imgs.

Correções em setAppMode:
- Ao sair de gtiff (entrar em png), limpa .gt-map-active de todos boxes,
  esconde canvases .map-canvas-gt, e força renderTudo() para repopular
  os <img> com URLs PNG.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''        if (mainPNG) mainPNG.style.display = '';
        if (mainGT)  mainGT.style.display  = 'none';
        document.body.classList.toggle('gt-mode-active', mode === 'gtiff');
        if (mode === 'gtiff') {
            // Mostra o modal como sidebar à direita
            if (modal) {
                modal.classList.add('gt-sidebar');
                modal.classList.add('open');
            }
            try { renderTudo(); } catch (_) {}
            try { gtRenderPanelPins(); } catch (_) {}
            try { gtSelectPanel(gtActivePanel || 0); } catch (_) {}
        }
    }'''
NEW = '''        if (mainPNG) mainPNG.style.display = '';
        if (mainGT)  mainGT.style.display  = 'none';
        document.body.classList.toggle('gt-mode-active', mode === 'gtiff');
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
        }
        if (mode === 'gtiff') {
            // Mostra o modal como sidebar à direita
            if (modal) {
                modal.classList.add('gt-sidebar');
                modal.classList.add('open');
            }
            try { renderTudo(); } catch (_) {}
            try { gtRenderPanelPins(); } catch (_) {}
            try { gtSelectPanel(gtActivePanel || 0); } catch (_) {}
        }
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if "Limpa artefatos do modo gtiff" in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    # Bump build
    src = src.replace('20260528-0050-blobcache', '20260528-0100-modeswitch')
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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0100-modeswitch")

if __name__ == '__main__':
    main()
