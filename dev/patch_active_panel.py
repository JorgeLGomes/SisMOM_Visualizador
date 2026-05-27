#!/usr/bin/env python3
"""
Patch: painel direito como sidebar em modo gtiff + seleção do painel Mi ativo.
- Modal #modalGeoTIFF vira sidebar fixa à direita (sem backdrop) em modo gtiff
- mainPNG ganha padding-right pra não ficar embaixo da sidebar
- gtActivePanel rastreia o painel Mi atualmente sendo controlado
- Cada painel Mi pode ser selecionado por clique (borda ciano marca o ativo)
- Cache: gtSlotDecoded[i] guarda o decoded de cada slot
- Painel direito sincroniza com gtSlotState[gtActivePanel] e gtSlotDecoded[gtActivePanel]
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) CSS: modo sidebar do modal
OLD_CSS = '''#modalGeoTIFF.inline { position: static; background: transparent; padding: 0; display: block !important; height: auto; }'''
NEW_CSS = '''#modalGeoTIFF.inline { position: static; background: transparent; padding: 0; display: block !important; height: auto; }
        /* Modo sidebar: usado no dashboard multi-painel (modo gtiff) */
        #modalGeoTIFF.gt-sidebar { position: fixed; top: 60px; right: 0; bottom: 0; width: 340px;
                                     background: var(--bg-elev-1, #0e1622); border-left: 1px solid var(--border-subtle);
                                     z-index: 30; padding: 0; display: block !important; overflow: hidden; }
        #modalGeoTIFF.gt-sidebar > .modal { width: 100%; max-width: none; height: 100%; box-shadow: none;
                                              border-radius: 0; max-height: none; display: flex; flex-direction: column; }
        #modalGeoTIFF.gt-sidebar > .modal > .modal-header { display: none; }
        #modalGeoTIFF.gt-sidebar > .modal > .modal-body { flex: 1; overflow-y: auto; padding: 8px 10px; }
        body.gt-mode-active main.main { padding-right: 340px; }
        /* Marca visual de painel Mi ativo */
        .map-box.gt-active { outline: 2px solid var(--accent-cyan, #4dd0e1); outline-offset: -2px; }
        .map-box .gt-panel-pin { position: absolute; top: 6px; right: 6px; z-index: 4;
                                  background: rgba(40,55,80,0.85); color: var(--text); border: 1px solid rgba(255,255,255,0.14);
                                  border-radius: 4px; padding: 2px 6px; font-size: 11px; cursor: pointer; display: none; }
        body.gt-mode-active .map-box .gt-panel-pin { display: inline-block; }
        body.gt-mode-active .map-box.gt-active .gt-panel-pin { background: var(--accent-cyan, #4dd0e1); color: #0b1220; }'''

# (2) setAppMode: ativar sidebar mode
OLD_SET = '''        // Sempre devolve o modal para fora do mainGT (volta a ser modal pop-up)
        if (modal) {
            modal.classList.remove('inline');
            modal.classList.remove('open');
            if (_gtModalParent && modal.parentNode !== _gtModalParent) {
                _gtModalParent.appendChild(modal);
            }
        }
        // Em ambos os modos, mainPNG (painéis Mi) fica visível; mainGT é oculto
        if (mainPNG) mainPNG.style.display = '';
        if (mainGT)  mainGT.style.display  = 'none';
        if (mode === 'gtiff') {
            // Apenas re-renderiza os painéis Mi (que agora vão chamar carregarGeoTIFFParaSlot via carregarImagem)
            try { renderTudo(); } catch (_) {}
        }
    }'''
NEW_SET = '''        // Sempre devolve o modal para fora do mainGT (volta a ser modal pop-up)
        if (modal) {
            modal.classList.remove('inline');
            modal.classList.remove('gt-sidebar');
            modal.classList.remove('open');
            if (_gtModalParent && modal.parentNode !== _gtModalParent) {
                _gtModalParent.appendChild(modal);
            }
        }
        if (mainPNG) mainPNG.style.display = '';
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

# (3) Adicionar gtActivePanel + gtSlotDecoded + funções de gerência
OLD_PRI_DECL = '''    let gtPrimaryVisible = true;
    let gtPrimaryName = '';   // nome do arquivo da camada base (file picker ou último segmento da URL)'''
NEW_PRI_DECL = '''    let gtPrimaryVisible = true;
    let gtPrimaryName = '';   // nome do arquivo da camada base (file picker ou último segmento da URL)
    let gtActivePanel = 0;    // índice do painel Mi sendo controlado pelo painel direito
    const gtSlotDecoded = []; // cache do decoded por slot Mi (para painel direito refletir)
    function gtRenderPanelPins() {
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
    }
    function gtSelectPanel(idx) {
        if (typeof idx !== 'number' || idx < 0) idx = 0;
        gtActivePanel = idx;
        // Marca visual
        document.querySelectorAll('.map-box').forEach((box, i) => {
            box.classList.toggle('gt-active', i === idx);
        });
        // Carrega o decoded cacheado deste slot na variável global
        const dec = gtSlotDecoded[idx];
        if (dec) {
            gtLastDecoded = dec;
            try { gtAtualizarInfoEMinMax(dec); } catch (_) {}
            try { gtDesenharColorbar(); } catch (_) {}
            try { gtRenderOverlayColorbars(); } catch (_) {}
        }
        // Atualiza nome no painel direito
        const s = state.slots && state.slots[idx];
        const m = s && modelos[s.modelo];
        const v = s && m && (Array.isArray(m.variaveis) ? m.variaveis.find(x => x.id === s.variavel) : null);
        gtPrimaryName = (m && v) ? (m.nome + ' · ' + (v.label || v.id)) : ('Painel M' + (idx + 1));
    }'''

# (4) carregarGeoTIFFParaSlot: cachear decoded por slot
OLD_CACHE = '''            const ab = await resp.arrayBuffer();
            if (reqId !== activeRequests[slotIdx]) return;
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);'''
NEW_CACHE = '''            const ab = await resp.arrayBuffer();
            if (reqId !== activeRequests[slotIdx]) return;
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            gtSlotDecoded[slotIdx] = decoded;
            if (slotIdx === (gtActivePanel || 0)) {
                gtLastDecoded = decoded;
                try { gtAtualizarInfoEMinMax(decoded); } catch (_) {}
                try { gtDesenharColorbar(); } catch (_) {}
                try { gtRenderOverlayColorbars(); } catch (_) {}
            }'''

# (5) renderTudo: chamar gtRenderPanelPins quando em modo gtiff
OLD_RT = '''    function renderTudo() {
        applyAnalysisDates();
        atualizarRunReadout();
        atualizarInfoSummary();
        atualizarProgresso();
        atualizarTooltipsInfo();
        for (let i = 0; i < state.layout; i++) renderSlot(i);
        if (appMode === 'gtiff') { try { gtLoadFromState(); } catch (_) {} }'''
NEW_RT = '''    function renderTudo() {
        applyAnalysisDates();
        atualizarRunReadout();
        atualizarInfoSummary();
        atualizarProgresso();
        atualizarTooltipsInfo();
        for (let i = 0; i < state.layout; i++) renderSlot(i);
        if (appMode === 'gtiff') {
            try { gtLoadFromState(); } catch (_) {}
            try { gtRenderPanelPins(); } catch (_) {}
            // Se painel ativo virou inválido (layout mudou), volta pra 0
            if (gtActivePanel >= state.layout) try { gtSelectPanel(0); } catch (_) {}
        }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'gtSelectPanel' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS,      NEW_CSS,      'css sidebar')
    src = rep(src, OLD_SET,      NEW_SET,      'setAppMode sidebar')
    src = rep(src, OLD_PRI_DECL, NEW_PRI_DECL, 'gtActivePanel decl')
    src = rep(src, OLD_CACHE,    NEW_CACHE,    'cache decoded per slot')
    src = rep(src, OLD_RT,       NEW_RT,       'renderTudo pins')

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
