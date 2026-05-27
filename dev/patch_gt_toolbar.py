#!/usr/bin/env python3
"""
Patch Fase 1: toolbar no #mainGT com [Modelo] [Variável] [Data] [Passo ← →].
Modifica state.slots[0] do modo GeoTIFF; gtLoadFromState() é chamado em
cada mudança para refletir no painel.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) HTML: criar toolbar dentro de #mainGT (que está vazio)
OLD_MAIN = '''<section id="mainGT" style="display:none" aria-label="Dashboard GeoTIFF"></section>'''
NEW_MAIN = '''<section id="mainGT" style="display:none" aria-label="Dashboard GeoTIFF">
    <div id="gtToolbar" style="display:flex;gap:8px;padding:6px 12px;background:rgba(255,255,255,0.04);border-bottom:1px solid rgba(255,255,255,0.08);align-items:center;flex-wrap:wrap;font-size:12px;color:var(--text,#cbd6e6)">
        <label style="display:inline-flex;align-items:center;gap:4px">Modelo
            <select id="gtModeloSel" style="min-width:140px;font-size:12px"></select>
        </label>
        <label style="display:inline-flex;align-items:center;gap:4px">Variável
            <select id="gtVariavelSel" style="min-width:160px;font-size:12px"></select>
        </label>
        <label style="display:inline-flex;align-items:center;gap:4px">Data
            <input type="date" id="gtDataInp" style="font-size:12px">
        </label>
        <span style="display:inline-flex;align-items:center;gap:4px">
            <button class="btn btn-ghost" id="btnGtPassoPrev" type="button" title="Passo anterior" style="padding:2px 8px">◀</button>
            <span id="gtPassoLabel" style="min-width:54px;text-align:center;font-family:ui-monospace,monospace;background:rgba(0,0,0,0.30);padding:2px 6px;border-radius:3px">—</span>
            <button class="btn btn-ghost" id="btnGtPassoNext" type="button" title="Próximo passo" style="padding:2px 8px">▶</button>
        </span>
        <span id="gtToolbarHint" style="margin-left:auto;color:var(--text-muted,#aab);font-size:11px"></span>
    </div>
</section>'''

# (2) JS: funções de toolbar antes de setAppMode (anchor estável)
OLD_FN = '''    function setAppMode(mode, opts) {'''
NEW_FN = '''    /* ─── Toolbar do dashboard GeoTIFF (Fase 1) ─── */
    function gtPopulateModeloSelect() {
        const sel = document.getElementById('gtModeloSel');
        if (!sel) return;
        const prev = sel.value;
        const opts = [];
        for (const id of Object.keys(modelos)) {
            const m = modelos[id];
            if (!m) continue;
            const protec = m.requires2FA ? ' 🔒' : '';
            opts.push('<option value="' + id + '">' + (m.nome || id) + protec + '</option>');
        }
        sel.innerHTML = opts.join('');
        if (prev && sel.querySelector('option[value="' + prev + '"]')) sel.value = prev;
    }
    function gtPopulateVariavelSelect(modeloId) {
        const sel = document.getElementById('gtVariavelSel');
        if (!sel) return;
        const m = modelos[modeloId];
        const prev = sel.value;
        const opts = [];
        if (m && Array.isArray(m.variaveis)) {
            for (const v of m.variaveis) {
                const lbl = (v.label || v.id) + (v.unidade ? ' (' + v.unidade + ')' : '');
                opts.push('<option value="' + v.id + '">' + lbl + '</option>');
            }
        }
        sel.innerHTML = opts.join('');
        if (prev && sel.querySelector('option[value="' + prev + '"]')) sel.value = prev;
    }
    function gtFormatPassoLabel(passo, maxPassos) {
        const v = (typeof passo === 'number' && isFinite(passo)) ? passo : 0;
        return String(v).padStart(4, '0') + 'h' + (maxPassos ? ' /' + maxPassos : '');
    }
    function gtFmtDateInput(dataFTP) {
        if (!dataFTP || dataFTP.length < 8) return '';
        // dataFTP típico: YYYYMMDD ou YYYYMMDDHH
        const y = dataFTP.slice(0, 4), m = dataFTP.slice(4, 6), d = dataFTP.slice(6, 8);
        return y + '-' + m + '-' + d;
    }
    function gtDateInputToFTP(val, hourHH) {
        // val: 'YYYY-MM-DD'; hourHH: '00' default
        if (!val) return '';
        const parts = val.split('-');
        if (parts.length !== 3) return '';
        return parts[0] + parts[1] + parts[2] + (hourHH || '00');
    }
    function gtSyncToolbarFromState() {
        const s = state.slots[0]; if (!s) return;
        gtPopulateModeloSelect();
        const ms = document.getElementById('gtModeloSel');
        if (ms && s.modelo) ms.value = s.modelo;
        gtPopulateVariavelSelect(s.modelo);
        const vs = document.getElementById('gtVariavelSel');
        if (vs && s.variavel) vs.value = s.variavel;
        const di = document.getElementById('gtDataInp');
        if (di) di.value = gtFmtDateInput(s.data);
        const pl = document.getElementById('gtPassoLabel');
        if (pl) {
            const max = (modelos[s.modelo] && modelos[s.modelo].maxPassos) || state.maxPassos || 24;
            pl.textContent = gtFormatPassoLabel(state.passoAtual, max);
        }
        const hint = document.getElementById('gtToolbarHint');
        if (hint) {
            const m = modelos[s.modelo];
            const isGeo = m && (typeof SisMOM_GeoTIFF !== 'undefined' && SisMOM_GeoTIFF.isGeoTiffModel(m));
            hint.textContent = isGeo ? '' : '(URL .tif será derivada da extensão .png/.gif)';
        }
    }
    function gtBindToolbar() {
        const ms = document.getElementById('gtModeloSel');
        const vs = document.getElementById('gtVariavelSel');
        const di = document.getElementById('gtDataInp');
        const bPrev = document.getElementById('btnGtPassoPrev');
        const bNext = document.getElementById('btnGtPassoNext');
        if (!ms || ms._gtBound) return;
        if (ms) { ms._gtBound = true; ms.addEventListener('change', () => {
            const id = ms.value;
            state.slots[0].modelo = id;
            // Atualiza variável para a primeira do novo modelo
            const m = modelos[id];
            if (m && Array.isArray(m.variaveis) && m.variaveis.length) {
                state.slots[0].variavel = m.variaveis[0].id;
            }
            gtSyncToolbarFromState();
            try { renderTudo(); } catch (_) {}
        }); }
        if (vs) vs.addEventListener('change', () => {
            state.slots[0].variavel = vs.value;
            gtSyncToolbarFromState();
            try { renderTudo(); } catch (_) {}
        });
        if (di) di.addEventListener('change', () => {
            // Mantém hora do data anterior (ou 00)
            const cur = state.slots[0].data || '';
            const hh = (cur.length >= 10) ? cur.slice(8, 10) : '00';
            state.slots[0].data = gtDateInputToFTP(di.value, hh);
            gtSyncToolbarFromState();
            try { renderTudo(); } catch (_) {}
        });
        function stepPasso(delta) {
            const max = (modelos[state.slots[0].modelo] && modelos[state.slots[0].modelo].maxPassos) || state.maxPassos || 24;
            let p = (state.passoAtual || 1) + delta;
            if (p < 1) p = 1; else if (p > max) p = max;
            state.passoAtual = p;
            gtSyncToolbarFromState();
            try { setStepIndicatorUI(); } catch (_) {}
            try { renderTudo(); } catch (_) {}
        }
        if (bPrev) bPrev.addEventListener('click', () => stepPasso(-1));
        if (bNext) bNext.addEventListener('click', () => stepPasso(+1));
    }

    function setAppMode(mode, opts) {'''

# (3) Ao entrar em gtiff, sincronizar a toolbar
OLD_SET = '''            if (mainPNG) mainPNG.style.display = 'none';
            if (mainGT)  mainGT.style.display  = '';
            gtLoadFromState().catch(() => {});'''
NEW_SET = '''            if (mainPNG) mainPNG.style.display = 'none';
            if (mainGT)  mainGT.style.display  = '';
            try { gtBindToolbar(); gtSyncToolbarFromState(); } catch (_) {}
            gtLoadFromState().catch(() => {});'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtBindToolbar' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_MAIN, NEW_MAIN, 'mainGT toolbar HTML')
    src = rep(src, OLD_FN,   NEW_FN,   'toolbar JS fns')
    src = rep(src, OLD_SET,  NEW_SET,  'setAppMode sync')

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
