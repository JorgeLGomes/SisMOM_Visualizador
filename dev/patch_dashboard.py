#!/usr/bin/env python3
"""
Patch: dashboard GeoTIFF como aba/tab no header.
- Adiciona tabs [PNG/GIF] [GeoTIFF] no header (CSS + HTML)
- Cria <section id="mainGT"> ao lado do <main> existente
- Em modo gtiff: move o conteúdo do modal local para dentro de mainGT (sem backdrop)
- gtLoadFromState() puxa GeoTIFF do FTP via montarURL(state.slots[0])
- Hook em renderTudo() chama gtLoadFromState quando appMode==='gtiff'
- Persiste em localStorage
Aplica nas duas cópias. Idempotente.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) CSS: adicionar regras das tabs (e da classe .inline do modal)
OLD_CSS_ANCHOR = '.header-actions { display: flex; align-items: center; gap: 6px; }'
NEW_CSS_BLOCK = '''.header-actions { display: flex; align-items: center; gap: 6px; }
        .mode-tabs { display: inline-flex; gap: 4px; margin-left: 14px; }
        .mode-tab { padding: 5px 14px; border-radius: 6px; background: transparent; color: var(--text-muted, #aab); border: 1px solid var(--border-subtle, #233); cursor: pointer; font-size: 13px; font-weight: 600; letter-spacing: 0.3px; transition: background .15s, color .15s, border-color .15s; }
        .mode-tab:hover { color: var(--text, #cbd6e6); }
        .mode-tab.active { background: rgba(77,208,225,0.15); color: var(--accent-cyan, #4dd0e1); border-color: var(--accent-cyan, #4dd0e1); }
        #modalGeoTIFF.inline { position: static; background: transparent; padding: 0; display: block !important; height: auto; }
        #modalGeoTIFF.inline > .modal { max-width: none; width: 100%; box-shadow: none; border-radius: 0; max-height: none; }
        #modalGeoTIFF.inline > .modal > .modal-header { display: none; }
        #mainGT { padding: 12px 16px; }'''

# (2) HTML: inserir tabs antes de header-actions
OLD_HEADER = '''        <div class="header-actions">
            <button class="icon-btn" id="btnOpenGeoTIFF"'''
NEW_HEADER = '''        <div class="mode-tabs" role="tablist" aria-label="Modo de visualização">
            <button type="button" class="mode-tab active" data-app-mode="png" role="tab" aria-selected="true">PNG/GIF</button>
            <button type="button" class="mode-tab" data-app-mode="gtiff" role="tab" aria-selected="false">GeoTIFF</button>
        </div>
        <div class="header-actions">
            <button class="icon-btn" id="btnOpenGeoTIFF"'''

# (3) HTML: depois do </main> do main principal, inserir <section id="mainGT">
OLD_MAIN_END = '''        <div class="map-container" id="mapContainer" data-layout="2"></div>
    </main>
</div>'''
NEW_MAIN_END = '''        <div class="map-container" id="mapContainer" data-layout="2"></div>
    </main>
    <section id="mainGT" style="display:none" aria-label="Dashboard GeoTIFF"></section>
</div>'''

# (4) JS: inserir bloco do dashboard antes de "if (document.readyState === 'loading') {"
INJECT_ANCHOR = "    if (document.readyState === 'loading') {"
DASH_BLOCK = '''    /* ╔═══════════════════════════════════════════════════════════╗
       ║  Dashboard GeoTIFF — tabs PNG/GIF | GeoTIFF                ║
       ║  Em modo gtiff, move o conteúdo do modal local para        ║
       ║  dentro de #mainGT (sem backdrop) e o conecta ao slot 0.   ║
       ╚═══════════════════════════════════════════════════════════╝ */
    let appMode = (function () {
        try { return localStorage.getItem('sismom_app_mode') || 'png'; } catch (_) { return 'png'; }
    })();
    let _gtModalParent = null;  // onde o conteúdo do modal "morava" antes de virar dashboard

    function setAppMode(mode, opts) {
        if (mode !== 'png' && mode !== 'gtiff') return;
        appMode = mode;
        try { localStorage.setItem('sismom_app_mode', mode); } catch (_) {}
        // Tabs visual
        document.querySelectorAll('.mode-tab').forEach(b => {
            const on = b.getAttribute('data-app-mode') === mode;
            b.classList.toggle('active', on);
            b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        const mainPNG = document.getElementById('main-content');
        const mainGT  = document.getElementById('mainGT');
        const modal   = document.getElementById('modalGeoTIFF');
        if (mode === 'gtiff') {
            // Move modal pra dentro de mainGT
            if (modal && mainGT && modal.parentNode !== mainGT) {
                _gtModalParent = modal.parentNode;
                mainGT.appendChild(modal);
            }
            if (modal) { modal.classList.add('inline'); modal.classList.add('open'); }
            if (mainPNG) mainPNG.style.display = 'none';
            if (mainGT)  mainGT.style.display  = '';
            // Carrega do FTP via slot 0
            gtLoadFromState().catch(() => {});
        } else {
            // Volta modal pra onde estava (body)
            if (modal) {
                modal.classList.remove('inline');
                modal.classList.remove('open');
                if (_gtModalParent && modal.parentNode !== _gtModalParent) {
                    _gtModalParent.appendChild(modal);
                }
            }
            if (mainPNG) mainPNG.style.display = '';
            if (mainGT)  mainGT.style.display  = 'none';
        }
    }

    async function gtLoadFromState() {
        if (appMode !== 'gtiff') return;
        if (!state || !state.slots || !state.slots[0]) return;
        const s = state.slots[0];
        if (!s.data || !s.modelo || !s.variavel) return;
        // Só faz sentido se o modelo for GeoTIFF
        const m = modelos[s.modelo];
        if (!m || !SisMOM_GeoTIFF.isGeoTiffModel(m)) {
            const info = document.getElementById('gtInfo');
            if (info) info.textContent = 'Modelo "' + (m && m.nome || s.modelo) + '" não é GeoTIFF (extensão ≠ .tif/.tiff). Configure um modelo com sufixo .tif/.tiff.';
            return;
        }
        const passo = getEffectivePasso(0);
        let url;
        try {
            url = montarURL({ modelo: s.modelo, data: s.data, variavel: s.variavel, passo });
        } catch (e) {
            const info = document.getElementById('gtInfo');
            if (info) info.textContent = 'Erro ao montar URL: ' + (e && e.message);
            return;
        }
        const info = document.getElementById('gtInfo');
        if (info) info.textContent = 'Carregando ' + url + '…';
        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const ab = await resp.arrayBuffer();
            gtLastDecoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            gtAtualizarInfoEMinMax(gtLastDecoded);
            try { gtUpdateMapToggleEnabled(); } catch (_) {}
            if (typeof _gtMap !== 'undefined' && _gtMap && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
            gtRenderar();
        } catch (e) {
            if (info) info.textContent = 'Falha ao carregar GeoTIFF: ' + ((e && e.message) || e);
        }
    }

    function bindModeTabs() {
        document.querySelectorAll('.mode-tab').forEach(b => {
            b.addEventListener('click', () => setAppMode(b.getAttribute('data-app-mode')));
        });
    }
'''

# (5) Init: ligar tabs e aplicar appMode salvo após inicialização normal
OLD_INIT_BIND = '''        // Liga UI de visualização GeoTIFF (botão no header + modal)
        try { bindGeoTIFFUI(); } catch (e) { console.error('bindGeoTIFFUI', e); }'''
NEW_INIT_BIND = '''        // Liga UI de visualização GeoTIFF (botão no header + modal)
        try { bindGeoTIFFUI(); } catch (e) { console.error('bindGeoTIFFUI', e); }
        // Liga tabs de modo (PNG/GIF | GeoTIFF) e aplica modo persistido
        try { bindModeTabs(); setAppMode(appMode); } catch (e) { console.error('mode tabs', e); }'''

# (6) Hook em renderTudo: se gtiff, recarrega
OLD_RENDERTUDO_HEAD = '''    function renderTudo() {
        applyAnalysisDates();
        atualizarRunReadout();
        atualizarInfoSummary();
        atualizarProgresso();
        atualizarTooltipsInfo();
        for (let i = 0; i < state.layout; i++) renderSlot(i);'''
NEW_RENDERTUDO_HEAD = '''    function renderTudo() {
        applyAnalysisDates();
        atualizarRunReadout();
        atualizarInfoSummary();
        atualizarProgresso();
        atualizarTooltipsInfo();
        for (let i = 0; i < state.layout; i++) renderSlot(i);
        if (appMode === 'gtiff') { try { gtLoadFromState(); } catch (_) {} }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'sismom_app_mode' in src:
        print(f"[{path.name}] já patcheado (dashboard); pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS_ANCHOR, NEW_CSS_BLOCK, 'css tabs')
    src = rep(src, OLD_HEADER, NEW_HEADER, 'html tabs')
    src = rep(src, OLD_MAIN_END, NEW_MAIN_END, 'main end')
    src = rep(src, INJECT_ANCHOR, DASH_BLOCK + '\n' + INJECT_ANCHOR, 'js block')
    src = rep(src, OLD_INIT_BIND, NEW_INIT_BIND, 'init bind')
    src = rep(src, OLD_RENDERTUDO_HEAD, NEW_RENDERTUDO_HEAD, 'renderTudo hook')

    if src == original: return False
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(original)} -> {len(src)}, {len(src)-len(original):+d})")
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
        print(f"OK -- {len(a)} bytes em ambas")

if __name__ == '__main__':
    main()
