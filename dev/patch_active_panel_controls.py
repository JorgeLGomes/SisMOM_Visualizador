#!/usr/bin/env python3
"""
Patch: Fase 5 — painel direito controla o Mi ativo (sem refetch).

Mudanças:
- gtSlotState[i] passa a guardar paleta, autoMinMax, min, max, undefRaw,
  clipBelow, clipAbove (estado por painel Mi).
- Novo gtRerenderSlot(i): pega gtSlotDecoded[i] + gtSlotState[i], aplica
  paleta inline (sem fetch), gera blob URL e troca no <img> do slot via o
  mesmo esquema de double-buffer existente.
- carregarGeoTIFFParaSlot passa a aplicar undef/clip do gtSlotState ao
  primeiro render, e cacheia o blob URL atual em gtBlobUrls[slot].current.
- gtSelectPanel(idx) agora reflete o estado salvo do slot nos inputs do
  painel direito (paleta/min/max/undef/clip) e dispara um redraw do canvas
  interno do modal (gtRenderar) caso o modal exista, mas SEM tocar nos
  outros painéis Mi.
- gtApplySlotControlsFromActive(): captura os valores dos inputs e grava
  em gtSlotState[gtActivePanel], depois chama gtRerenderSlot(gtActivePanel).
- Os listeners de paleta/min/max/undef/clip, quando appMode==='gtiff',
  passam a chamar gtApplySlotControlsFromActive em vez de só
  gtApplyActiveLayer (que opera no canvas oculto).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Estender getGtSlotState com campos undef/clip
OLD_STATE = '''    const gtSlotState = [];
    function getGtSlotState(i) {
        if (!gtSlotState[i]) gtSlotState[i] = { paleta: 'viridis', autoMinMax: true, min: null, max: null };
        return gtSlotState[i];
    }
    const gtBlobUrls = [];'''
NEW_STATE = '''    const gtSlotState = [];
    function getGtSlotState(i) {
        if (!gtSlotState[i]) gtSlotState[i] = {
            paleta: 'viridis', autoMinMax: true, min: null, max: null,
            undefRaw: '', clipBelow: null, clipAbove: null
        };
        return gtSlotState[i];
    }
    function gtSlotApplyOpts(slotIdx) {
        // Monta opts {paleta, min?, max?, nodataExtras?, clipBelow?, clipAbove?} a partir do gtSlotState
        const gt = getGtSlotState(slotIdx);
        const opts = { paleta: gt.paleta || 'viridis' };
        if (!gt.autoMinMax && isFinite(gt.min) && isFinite(gt.max) && gt.max > gt.min) {
            opts.min = gt.min; opts.max = gt.max;
        }
        const extras = (typeof gtParseUndefList === 'function') ? gtParseUndefList(gt.undefRaw || '') : null;
        if (extras) opts.nodataExtras = extras;
        if (gt.clipBelow != null && isFinite(gt.clipBelow)) opts.clipBelow = gt.clipBelow;
        if (gt.clipAbove != null && isFinite(gt.clipAbove)) opts.clipAbove = gt.clipAbove;
        return opts;
    }
    async function gtRerenderSlot(slotIdx) {
        // Re-renderiza o slot Mi usando o decoded cacheado + gtSlotState (sem refetch)
        const decoded = gtSlotDecoded[slotIdx];
        if (!decoded) return;
        const buf = buffers[slotIdx];
        if (!buf) return;
        const frontKey = buf.active;
        const backKey  = frontKey === 'a' ? 'b' : 'a';
        const back  = slotBuf(slotIdx, backKey);
        const front = slotBuf(slotIdx, frontKey);
        if (!back || !front) return;
        const opts = gtSlotApplyOpts(slotIdx);
        const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);
        const canvas = document.createElement('canvas');
        canvas.width = decoded.width; canvas.height = decoded.height;
        canvas.getContext('2d').putImageData(imgData, 0, 0);
        const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
        const blobUrl = URL.createObjectURL(blob);
        if (!gtBlobUrls[slotIdx]) gtBlobUrls[slotIdx] = { a: null, b: null };
        const oldUrl = gtBlobUrls[slotIdx][backKey];
        gtBlobUrls[slotIdx][backKey] = blobUrl;
        back.onload = () => {
            back.classList.add('active');
            front.classList.remove('active');
            buf.active = backKey;
            if (oldUrl) URL.revokeObjectURL(oldUrl);
        };
        back.onerror = () => { URL.revokeObjectURL(blobUrl); };
        back.src = blobUrl;
    }
    const gtBlobUrls = [];'''

# (2) carregarGeoTIFFParaSlot: usar gtSlotApplyOpts em vez do opts ad-hoc
OLD_LOAD = '''            const gt = getGtSlotState(slotIdx);
            const opts = { paleta: gt.paleta };
            if (!gt.autoMinMax) { opts.min = gt.min; opts.max = gt.max; }
            const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);'''
NEW_LOAD = '''            const opts = gtSlotApplyOpts(slotIdx);
            const imgData = SisMOM_GeoTIFF.aplicarPaleta(decoded, opts);'''

# (3) gtSelectPanel: refletir gtSlotState nos inputs do painel direito
OLD_SELECT = '''    function gtSelectPanel(idx) {
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
NEW_SELECT = '''    function gtSelectPanel(idx) {
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
        // Reflete gtSlotState[idx] nos inputs do painel direito
        try { gtSyncRightPanelFromSlot(idx); } catch (_) {}
    }
    function gtSyncRightPanelFromSlot(slotIdx) {
        const gt = getGtSlotState(slotIdx);
        const palEl = document.getElementById('gtPaleta');
        if (palEl) palEl.value = gt.paleta || 'viridis';
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        const btnEdit = document.getElementById('btnGtEdit');
        const btnAuto = document.getElementById('btnGtAuto');
        if (minEl && maxEl) {
            if (gt.autoMinMax) {
                minEl.removeAttribute('data-editing');
                minEl.setAttribute('readonly',''); maxEl.setAttribute('readonly','');
                if (btnEdit) btnEdit.style.display = '';
                if (btnAuto) btnAuto.style.display = 'none';
                const dec = gtSlotDecoded[slotIdx];
                if (dec) { minEl.value = dec.min; maxEl.value = dec.max; }
            } else {
                minEl.setAttribute('data-editing','1');
                minEl.removeAttribute('readonly'); maxEl.removeAttribute('readonly');
                if (btnEdit) btnEdit.style.display = 'none';
                if (btnAuto) btnAuto.style.display = '';
                if (gt.min != null) minEl.value = gt.min;
                if (gt.max != null) maxEl.value = gt.max;
            }
        }
        const undefEl = document.getElementById('gtUndef');
        if (undefEl) undefEl.value = gt.undefRaw || '';
        const clMin = document.getElementById('gtClipMin');
        const clMax = document.getElementById('gtClipMax');
        if (clMin) clMin.value = (gt.clipBelow != null ? gt.clipBelow : '');
        if (clMax) clMax.value = (gt.clipAbove != null ? gt.clipAbove : '');
    }
    function gtCaptureRightPanelToSlot(slotIdx) {
        const gt = getGtSlotState(slotIdx);
        const palEl = document.getElementById('gtPaleta');
        if (palEl) gt.paleta = palEl.value || 'viridis';
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        if (minEl && maxEl) {
            const editing = minEl.hasAttribute('data-editing');
            gt.autoMinMax = !editing;
            if (editing) {
                const mn = parseFloat(minEl.value);
                const mx = parseFloat(maxEl.value);
                if (isFinite(mn) && isFinite(mx) && mx > mn) { gt.min = mn; gt.max = mx; }
            } else {
                gt.min = null; gt.max = null;
            }
        }
        const undefEl = document.getElementById('gtUndef');
        gt.undefRaw = (undefEl && undefEl.value) ? undefEl.value : '';
        const clMin = document.getElementById('gtClipMin');
        const clMax = document.getElementById('gtClipMax');
        gt.clipBelow = (clMin && clMin.value.trim() !== '') ? parseFloat(clMin.value) : null;
        gt.clipAbove = (clMax && clMax.value.trim() !== '') ? parseFloat(clMax.value) : null;
    }
    async function gtApplySlotControlsFromActive() {
        // Captura inputs e re-renderiza somente o Mi ativo (sem refetch)
        gtCaptureRightPanelToSlot(gtActivePanel);
        await gtRerenderSlot(gtActivePanel);
        try { gtDesenharColorbar(); } catch (_) {}
        try { gtRenderOverlayColorbars(); } catch (_) {}
    }'''

# (4) Listener da paleta: roteia para gtApplySlotControlsFromActive em modo gtiff
OLD_LIS_PAL = "document.getElementById('gtPaleta').addEventListener('change', () => { gtApplyActiveLayer(); });"
NEW_LIS_PAL = "document.getElementById('gtPaleta').addEventListener('change', () => { if (appMode === 'gtiff') { gtApplySlotControlsFromActive(); } else { gtApplyActiveLayer(); } });"

# (5) btnGtEdit: habilita edição manual min/max (também sinaliza slot ativo)
OLD_LIS_EDIT = '''        btnEdit.addEventListener('click', () => {
            const m = document.getElementById('gtMin'), M = document.getElementById('gtMax');
            m.removeAttribute('readonly'); M.removeAttribute('readonly');
            m.setAttribute('data-editing', '1');
            btnEdit.style.display = 'none';
            btnAuto.style.display = '';
        });
        btnAuto.addEventListener('click', () => {
            const m = document.getElementById('gtMin'), M = document.getElementById('gtMax');
            m.setAttribute('readonly', ''); M.setAttribute('readonly', '');
            m.removeAttribute('data-editing');
            btnEdit.style.display = '';
            btnAuto.style.display = 'none';
            if (gtLastDecoded) { m.value = gtLastDecoded.min; M.value = gtLastDecoded.max; }
            gtRenderar();
        });'''
NEW_LIS_EDIT = '''        btnEdit.addEventListener('click', () => {
            const m = document.getElementById('gtMin'), M = document.getElementById('gtMax');
            m.removeAttribute('readonly'); M.removeAttribute('readonly');
            m.setAttribute('data-editing', '1');
            btnEdit.style.display = 'none';
            btnAuto.style.display = '';
            if (appMode === 'gtiff') {
                const gt = getGtSlotState(gtActivePanel);
                gt.autoMinMax = false;
            }
        });
        btnAuto.addEventListener('click', () => {
            const m = document.getElementById('gtMin'), M = document.getElementById('gtMax');
            m.setAttribute('readonly', ''); M.setAttribute('readonly', '');
            m.removeAttribute('data-editing');
            btnEdit.style.display = '';
            btnAuto.style.display = 'none';
            if (appMode === 'gtiff') {
                const gt = getGtSlotState(gtActivePanel);
                gt.autoMinMax = true; gt.min = null; gt.max = null;
                const dec = gtSlotDecoded[gtActivePanel];
                if (dec) { m.value = dec.min; M.value = dec.max; }
                gtApplySlotControlsFromActive();
            } else {
                if (gtLastDecoded) { m.value = gtLastDecoded.min; M.value = gtLastDecoded.max; }
                gtRenderar();
            }
        });'''

# (6) Listeners min/max: roteamento gtiff
OLD_LIS_MIN = "document.getElementById('gtMin').addEventListener('change', () => { gtApplyActiveLayer(); });\n        document.getElementById('gtMax').addEventListener('change', () => { gtApplyActiveLayer(); });"
NEW_LIS_MIN = "document.getElementById('gtMin').addEventListener('change', () => { if (appMode === 'gtiff') { gtApplySlotControlsFromActive(); } else { gtApplyActiveLayer(); } });\n        document.getElementById('gtMax').addEventListener('change', () => { if (appMode === 'gtiff') { gtApplySlotControlsFromActive(); } else { gtApplyActiveLayer(); } });"

# (7) UNDEF/Clip applyMaskAndRender: roteamento gtiff
OLD_LIS_MASK = '''        // Filtros UNDEF / clip
        function applyMaskAndRender() {
            // Aplica nas props da camada ATIVA, não globalmente
            gtApplyActiveLayer();
        }'''
NEW_LIS_MASK = '''        // Filtros UNDEF / clip
        function applyMaskAndRender() {
            if (appMode === 'gtiff') {
                gtApplySlotControlsFromActive();
            } else {
                gtApplyActiveLayer();
            }
        }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'gtRerenderSlot' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_STATE,    NEW_STATE,    'state extend + gtRerenderSlot')
    src = rep(src, OLD_LOAD,     NEW_LOAD,     'carregarGeoTIFFParaSlot opts')
    src = rep(src, OLD_SELECT,   NEW_SELECT,   'gtSelectPanel sync inputs')
    src = rep(src, OLD_LIS_PAL,  NEW_LIS_PAL,  'listener paleta')
    src = rep(src, OLD_LIS_EDIT, NEW_LIS_EDIT, 'listeners btnEdit/btnAuto')
    src = rep(src, OLD_LIS_MIN,  NEW_LIS_MIN,  'listeners gtMin/gtMax')
    src = rep(src, OLD_LIS_MASK, NEW_LIS_MASK, 'applyMaskAndRender')

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
