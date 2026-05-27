#!/usr/bin/env python3
"""
Patch: transformar seções do painel lateral em dropdowns/accordions colapsáveis.
Cada cabeçalho <h4> (Arquivo/Visual, NoData/Clip, Camadas...) vira clicável,
com chevron ▾/▸ e wrapper de body. Clique alterna .collapsed.
Estado por seção persistido em localStorage.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) CSS para accordion
OLD_CSS = '''.gt-side h4 { margin: 8px 0 4px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;
                       color: var(--text-muted, #aab); border-bottom: 1px solid rgba(255,255,255,0.08);
                       padding-bottom: 3px; }'''
NEW_CSS = '''.gt-side h4 { margin: 8px 0 4px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;
                       color: var(--text-muted, #aab); border-bottom: 1px solid rgba(255,255,255,0.08);
                       padding-bottom: 3px; }
        .gt-side h4.gt-section-header { cursor: pointer; user-select: none;
                                          display: flex; align-items: center; gap: 4px; transition: color .15s; }
        .gt-side h4.gt-section-header:hover { color: var(--text, #cbd6e6); }
        .gt-side h4 .gt-section-chevron { display: inline-block; width: 10px; font-size: 9px;
                                            transform: rotate(0deg); transition: transform .2s; }
        .gt-side h4.collapsed .gt-section-chevron { transform: rotate(-90deg); }
        .gt-section-body { overflow: hidden; transition: max-height .25s ease, opacity .2s; opacity: 1; }
        .gt-section-body.collapsed { max-height: 0 !important; opacity: 0; margin: 0; padding: 0; pointer-events: none; }'''

# (2) Função gtMakeAccordion + persistência — inserir antes de gtReorganizeLayout end
OLD_REORG_END = '''        body.appendChild(tgl);
    }

    /* ─── Camada ativa: controles operam sobre a camada selecionada ─── */'''
NEW_REORG_END = '''        body.appendChild(tgl);
        // Transforma cada h4 em dropdown colapsável
        try { gtMakeAccordion(); } catch (e) { console.error('gtMakeAccordion', e); }
    }

    function gtMakeAccordion() {
        const side = document.getElementById('gtSidePanel');
        if (!side || side.classList.contains('gt-accordion-ready')) return;
        side.classList.add('gt-accordion-ready');
        // Carrega estado salvo (quais seções colapsadas)
        let saved = {};
        try { saved = JSON.parse(localStorage.getItem('sismom_gt_sections') || '{}') || {}; } catch (_) {}
        const headers = Array.from(side.querySelectorAll('h4'));
        headers.forEach((h, idx) => {
            const sectionKey = (h.textContent || ('s' + idx)).trim();
            // Wrapper body para os próximos siblings até o próximo h4
            const body = document.createElement('div');
            body.className = 'gt-section-body';
            let next = h.nextSibling;
            while (next && !(next.nodeType === 1 && next.tagName === 'H4')) {
                const cur = next;
                next = next.nextSibling;
                body.appendChild(cur);
            }
            h.parentNode.insertBefore(body, h.nextSibling);
            // Header clicável com chevron
            h.classList.add('gt-section-header');
            const chev = document.createElement('span');
            chev.className = 'gt-section-chevron';
            chev.textContent = '▾';
            h.insertBefore(chev, h.firstChild);
            // Aplica estado salvo
            if (saved[sectionKey]) {
                body.classList.add('collapsed');
                h.classList.add('collapsed');
            }
            h.addEventListener('click', () => {
                const collapsed = body.classList.toggle('collapsed');
                h.classList.toggle('collapsed', collapsed);
                try {
                    const cur = JSON.parse(localStorage.getItem('sismom_gt_sections') || '{}') || {};
                    cur[sectionKey] = collapsed;
                    localStorage.setItem('sismom_gt_sections', JSON.stringify(cur));
                } catch (_) {}
            });
        });
    }

    /* ─── Camada ativa: controles operam sobre a camada selecionada ─── */'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtMakeAccordion' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS,        NEW_CSS,        'css accordion')
    src = rep(src, OLD_REORG_END,  NEW_REORG_END,  'fn gtMakeAccordion')

    if src == original: return False
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(src)-len(original):+d})")
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
