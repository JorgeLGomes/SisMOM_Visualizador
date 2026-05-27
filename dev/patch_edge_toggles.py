#!/usr/bin/env python3
"""
Patch: botão de ocultação edge para a sidebar esquerda + reposicionar
o botão da direita (que estava sobrepondo o texto).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) CSS: corrigir posição do botão direito (right 312 → 320) + adicionar regras pro botão da esquerda
OLD_CSS_RIGHT = '''.gt-side:not(.collapsed) ~ .gt-side-toggle { right: 312px; }'''
NEW_CSS_RIGHT = '''.gt-side:not(.collapsed) ~ .gt-side-toggle { right: 320px; border-radius: 4px 0 0 4px; }
        .gt-side.collapsed ~ .gt-side-toggle { border-radius: 4px 0 0 4px; }
        /* Botão "edge" para a sidebar esquerda — análogo ao do painel direito */
        .sidebar-edge-toggle {
            position: fixed;
            left: var(--sidebar-w, 280px);
            top: 78px;
            z-index: 15;
            width: 22px; height: 28px;
            background: rgba(40,55,80,0.92);
            color: var(--text, #cbd6e6);
            border: 1px solid rgba(255,255,255,0.14);
            border-left: 0;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            font-size: 14px; line-height: 26px;
            padding: 0;
            transition: left 0.35s var(--ease-out, cubic-bezier(.2,.6,.2,1));
        }
        .sidebar-edge-toggle:hover { background: rgba(60,80,110,0.95); }
        .app.sidebar-collapsed .sidebar-edge-toggle { left: 0; }'''

# (2) HTML: adicionar o botão edge da esquerda, logo após o <aside class="sidebar"> (ou no body geral)
# Vou adicionar antes do <aside class="sidebar" id="sidebar"> para ficar no markup top-level
OLD_HTML_SIDEBAR = '''    <aside class="sidebar" id="sidebar" aria-label="Controles">'''
NEW_HTML_SIDEBAR = '''    <button type="button" id="btnSidebarEdgeToggle" class="sidebar-edge-toggle" title="Ocultar/mostrar painel lateral (S)" aria-label="Painel lateral">›</button>
    <aside class="sidebar" id="sidebar" aria-label="Controles">'''

# (3) JS: ligar o botão edge ao toggleSidebar existente; e atualizar o texto ‹/› conforme estado
# Hook após bindModeTabs (que já é uma área de binding no init)
OLD_BIND_TABS = '''        // Liga tabs de modo (PNG/GIF | GeoTIFF) e aplica modo persistido
        try { bindModeTabs(); setAppMode(appMode); } catch (e) { console.error('mode tabs', e); }'''
NEW_BIND_TABS = '''        // Liga tabs de modo (PNG/GIF | GeoTIFF) e aplica modo persistido
        try { bindModeTabs(); setAppMode(appMode); } catch (e) { console.error('mode tabs', e); }
        // Liga botão "edge" da sidebar esquerda (reusa toggleSidebar existente)
        try {
            const edge = document.getElementById('btnSidebarEdgeToggle');
            if (edge) {
                const sync = () => {
                    const collapsed = DOM.app.classList.contains('sidebar-collapsed');
                    edge.textContent = collapsed ? '›' : '‹';
                    edge.title = (collapsed ? 'Mostrar' : 'Ocultar') + ' painel lateral (S)';
                };
                edge.addEventListener('click', () => { toggleSidebar(); sync(); });
                // Observa mudanças (S no teclado, ou clique no header)
                new MutationObserver(sync).observe(DOM.app, { attributes: true, attributeFilter: ['class'] });
                sync();
            }
        } catch (e) { console.error('sidebar edge', e); }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'sidebar-edge-toggle' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS_RIGHT,    NEW_CSS_RIGHT,    'css right + edge')
    src = rep(src, OLD_HTML_SIDEBAR, NEW_HTML_SIDEBAR, 'html edge button')
    src = rep(src, OLD_BIND_TABS,    NEW_BIND_TABS,    'js bind edge')

    if src == original: return False
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok (+{len(src)-len(original)})")
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
        print('OK - ' + str(len(a)) + ' bytes em ambas')

if __name__ == '__main__':
    main()
