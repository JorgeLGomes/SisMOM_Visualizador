#!/usr/bin/env python3
"""
Patch: reposicionar o botão "Painel Mi" para não sobrepor os ícones de
informação/copiar/download/maximizar do .map-header.

- O pin agora é anexado a .map-body (não mais a .map-box), ficando dentro
  da área do mapa em si.
- Posição: canto superior esquerdo do map-body (acima das informações
  laterais e da viewport), z-index alto pra ficar acima do canvas/img.
- Sem mais conflito com .map-tools (top-right do header).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) CSS — atualizar posicionamento do pin
OLD_CSS = '''        .map-box .gt-panel-pin { position: absolute; top: 6px; right: 6px; z-index: 4;
                                  background: rgba(40,55,80,0.85); color: var(--text); border: 1px solid rgba(255,255,255,0.14);
                                  border-radius: 4px; padding: 2px 6px; font-size: 11px; cursor: pointer; display: none; }
        body.gt-mode-active .map-box .gt-panel-pin { display: inline-block; }
        body.gt-mode-active .map-box.gt-active .gt-panel-pin { background: var(--accent-cyan, #4dd0e1); color: #0b1220; }'''
NEW_CSS = '''        .map-body .gt-panel-pin { position: absolute; top: 8px; left: 8px; z-index: 7;
                                  background: rgba(40,55,80,0.85); color: var(--text); border: 1px solid rgba(255,255,255,0.14);
                                  border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;
                                  cursor: pointer; display: none; backdrop-filter: blur(8px); }
        body.gt-mode-active .map-body .gt-panel-pin { display: inline-block; }
        body.gt-mode-active .map-box.gt-active .map-body .gt-panel-pin { background: var(--accent-cyan, #4dd0e1); color: #0b1220; border-color: rgba(0,0,0,0.2); }'''

# (2) JS — anexar a .map-body (em vez de .map-box)
OLD_JS = '''    function gtRenderPanelPins() {
        document.querySelectorAll('.map-box').forEach((box, idx) => {
            // só painéis dentro de mainPNG
            const inMain = box.closest && box.closest('#main-content');
            if (!inMain) return;
            let pin = box.querySelector('.gt-panel-pin');
            if (!pin) {
                pin = document.createElement('button');
                pin.type = 'button';
                pin.className = 'gt-panel-pin';
                pin.addEventListener('click', (e) => { e.stopPropagation(); gtSelectPanel(idx); });
                box.appendChild(pin);
            }
            pin.textContent = 'Painel M' + (idx + 1);
            box.classList.toggle('gt-active', idx === gtActivePanel);
        });
    }'''
NEW_JS = '''    function gtRenderPanelPins() {
        document.querySelectorAll('.map-box').forEach((box, idx) => {
            // só painéis dentro de mainPNG
            const inMain = box.closest && box.closest('#main-content');
            if (!inMain) return;
            const body = box.querySelector('.map-body');
            if (!body) return;
            // Limpa pin antigo no .map-box (de versões anteriores)
            const stale = box.querySelector(':scope > .gt-panel-pin');
            if (stale) stale.remove();
            let pin = body.querySelector(':scope > .gt-panel-pin');
            if (!pin) {
                pin = document.createElement('button');
                pin.type = 'button';
                pin.className = 'gt-panel-pin';
                pin.addEventListener('click', (e) => { e.stopPropagation(); gtSelectPanel(idx); });
                body.appendChild(pin);
            }
            pin.textContent = 'Painel M' + (idx + 1);
            box.classList.toggle('gt-active', idx === gtActivePanel);
        });
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '.map-body .gt-panel-pin' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS, NEW_CSS, 'css pin reposition')
    src = rep(src, OLD_JS,  NEW_JS,  'js pin attach to map-body')

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
        print("OK - " + str(len(a)) + " bytes em ambas")

if __name__ == '__main__':
    main()
