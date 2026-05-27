#!/usr/bin/env python3
"""
Patch: painel lateral colapsável + reordenação de camadas + camada ativa
com controles por camada.

- CSS: .modal-body em flex, .gt-side com width fixa colapsável
- gtReorganizeLayout(): no init, move controles existentes para o aside e
  canvas+info para o main. Adiciona botão de toggle de visibilidade do painel.
- gtActiveLayerId: 'primary' (padrão) ou id de extra. Controles
  (paleta/min/max/UNDEF/clip) operam apenas na camada ativa.
- Chips de camadas ganham ↑/↓ para reordenação; clique seleciona como ativa.
- Colorbar reflete a camada ativa.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1) CSS para o painel lateral ───
OLD_CSS = '#mainGT { padding: 12px 16px; }'
NEW_CSS = '''#mainGT { padding: 12px 16px; }
        /* Layout do dashboard GeoTIFF: main + side panel */
        .modal-body.gt-organized { display: flex; gap: 8px; position: relative; min-height: 0; }
        .gt-main-col { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
        .gt-side { width: 320px; flex: 0 0 320px; min-width: 0; overflow-y: auto; max-height: 78vh;
                   padding: 8px 10px; background: rgba(255,255,255,0.03);
                   border-left: 1px solid rgba(255,255,255,0.08); border-radius: 4px;
                   transition: width .25s ease, flex-basis .25s ease, padding .25s ease, opacity .2s ease; }
        .gt-side.collapsed { width: 0; flex: 0 0 0; padding-left: 0; padding-right: 0; opacity: 0; overflow: hidden; }
        .gt-side-toggle { position: absolute; right: 0; top: 6px; z-index: 5; background: rgba(40,55,80,0.92);
                           color: var(--text, #cbd6e6); border: 1px solid rgba(255,255,255,0.14);
                           border-radius: 4px 0 0 4px; cursor: pointer; width: 22px; height: 28px;
                           font-size: 14px; line-height: 26px; padding: 0; transition: right .25s ease; }
        .gt-side:not(.collapsed) ~ .gt-side-toggle { right: 312px; }
        .gt-side h4 { margin: 8px 0 4px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;
                       color: var(--text-muted, #aab); border-bottom: 1px solid rgba(255,255,255,0.08);
                       padding-bottom: 3px; }
        .gt-layer-item { display: flex; align-items: center; gap: 4px; padding: 4px 6px; border-radius: 4px;
                          background: rgba(255,255,255,0.04); margin-bottom: 4px; cursor: pointer;
                          border: 1px solid transparent; }
        .gt-layer-item.active { border-color: var(--accent-cyan, #4dd0e1); background: rgba(77,208,225,0.10); }
        .gt-layer-item .gl-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; }
        .gt-layer-item button { background: none; border: 0; color: inherit; cursor: pointer; padding: 0 3px;
                                  font-size: 12px; line-height: 1; }
        .gt-layer-item .gl-dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; }
        .gt-layer-item .gl-rm { color: #f88; font-size: 14px; font-weight: 700; }'''

# ─── (2) gtReorganizeLayout(): move DOM na primeira vez que abre o modal/dashboard ───
OLD_BIND_END_ANCHOR = '''    function bindGeoTIFFUI() {
        const btn = document.getElementById('btnOpenGeoTIFF');
        if (!btn) return;'''
NEW_BIND_END_ANCHOR = '''    function gtReorganizeLayout() {
        const modal = document.getElementById('modalGeoTIFF');
        if (!modal) return;
        const body = modal.querySelector('.modal-body');
        if (!body || body.classList.contains('gt-organized')) return;
        body.classList.add('gt-organized');
        // Cria as duas colunas
        const main = document.createElement('div'); main.className = 'gt-main-col';
        const side = document.createElement('aside'); side.id = 'gtSidePanel'; side.className = 'gt-side';
        // Move filhos atuais: container do canvas/mapa e #gtInfo vão pra main; demais (controles) pra side
        const kids = Array.from(body.children);
        for (const el of kids) {
            if (el.classList && el.classList.contains('gt-organized')) continue;
            if (el.id === 'gtInfo') { main.appendChild(el); continue; }
            // Container que contém os canvases (#gtCanvas e #gtMapCanvas)
            if (el.querySelector && (el.querySelector('#gtCanvas') || el.querySelector('#gtMapCanvas'))) {
                main.appendChild(el); continue;
            }
            side.appendChild(el);
        }
        // Cabeçalhos lógicos no painel: adiciona <h4> antes dos blocos relevantes
        // (procura por inputs específicos para identificar blocos)
        const find = (selId) => side.querySelector('#' + selId);
        function addHeaderBefore(target, label) {
            if (!target) return;
            const wrapper = target.closest('div');
            if (!wrapper) return;
            const h = document.createElement('h4'); h.textContent = label;
            side.insertBefore(h, wrapper);
        }
        addHeaderBefore(find('gtFile'),    'Arquivo / Visual');
        addHeaderBefore(find('gtUndef'),   'NoData / Clip');
        addHeaderBefore(find('btnGtAddLayer'), 'Camadas');
        // Colorbar não precisa de header
        // Re-ordena os filhos do body
        body.appendChild(main);
        body.appendChild(side);
        // Botão de toggle do painel
        const tgl = document.createElement('button');
        tgl.id = 'btnGtSideToggle'; tgl.className = 'gt-side-toggle';
        tgl.type = 'button'; tgl.title = 'Ocultar/mostrar painel';
        tgl.textContent = '›';
        tgl.addEventListener('click', () => {
            const collapsed = side.classList.toggle('collapsed');
            tgl.textContent = collapsed ? '‹' : '›';
            tgl.title = collapsed ? 'Mostrar painel' : 'Ocultar painel';
        });
        body.appendChild(tgl);
    }

    /* ─── Camada ativa: controles operam sobre a camada selecionada ─── */
    let gtActiveLayerId = 'primary';
    // Props por camada (primary tem props globais; extras têm props no objeto)
    const gtPrimaryProps = { paleta: 'viridis', autoMinMax: true, customMin: null, customMax: null,
                              undefRaw: '', clipBelow: null, clipAbove: null };

    function gtGetLayerObj(id) {
        if (id === 'primary') {
            return {
                id: 'primary', type: 'geotiff',
                name: (gtLastDecoded && '(camada base)') || '—',
                visible: true,
                decoded: gtLastDecoded,
                props: gtPrimaryProps
            };
        }
        const l = gtExtraLayers.find(x => x.id === id);
        return l || null;
    }
    function gtAllLayers() {
        const out = [gtGetLayerObj('primary')];
        for (const l of gtExtraLayers) out.push(l);
        return out;
    }
    function gtEnsureLayerProps(layer) {
        if (!layer) return;
        if (!layer.props) layer.props = { paleta: layer.paleta || 'viridis', autoMinMax: true,
                                           customMin: null, customMax: null, undefRaw: '',
                                           clipBelow: null, clipAbove: null };
    }
    function gtSetActiveLayer(id) {
        const layer = gtGetLayerObj(id);
        if (!layer) return;
        gtEnsureLayerProps(layer);
        gtActiveLayerId = id;
        // Atualiza inputs com props da ativa
        const p = layer.props || gtPrimaryProps;
        const palEl = document.getElementById('gtPaleta');
        if (palEl) palEl.value = p.paleta || 'viridis';
        const minEl = document.getElementById('gtMin'), maxEl = document.getElementById('gtMax');
        if (minEl && maxEl) {
            if (p.autoMinMax) {
                minEl.removeAttribute('data-editing');
                minEl.setAttribute('readonly',''); maxEl.setAttribute('readonly','');
                const dec = (id === 'primary') ? gtLastDecoded : layer.decoded;
                if (dec) { minEl.value = dec.min; maxEl.value = dec.max; }
            } else {
                minEl.setAttribute('data-editing','1');
                minEl.removeAttribute('readonly'); maxEl.removeAttribute('readonly');
                if (p.customMin != null) minEl.value = p.customMin;
                if (p.customMax != null) maxEl.value = p.customMax;
            }
        }
        const undefEl = document.getElementById('gtUndef');
        if (undefEl) undefEl.value = p.undefRaw || '';
        const clMin = document.getElementById('gtClipMin'), clMax = document.getElementById('gtClipMax');
        if (clMin) clMin.value = (p.clipBelow != null ? p.clipBelow : '');
        if (clMax) clMax.value = (p.clipAbove != null ? p.clipAbove : '');
        // Sync gtMaskOpts global pra ativa
        gtMaskOpts = {
            extras: gtParseUndefList(p.undefRaw),
            clipBelow: p.clipBelow, clipAbove: p.clipAbove
        };
        gtRenderLayerChips();
        gtDesenharColorbar();
        gtRenderar();
    }
    function gtParseUndefList(raw) {
        if (!raw) return null;
        const out = [];
        for (const tok of String(raw).split(/[,;\\s]+/)) {
            const x = parseFloat(tok);
            if (isFinite(x)) out.push(x);
        }
        return out.length ? out : null;
    }
    function gtCaptureControlsToActive() {
        const layer = gtGetLayerObj(gtActiveLayerId);
        if (!layer) return;
        gtEnsureLayerProps(layer);
        const p = layer.props || gtPrimaryProps;
        const palEl = document.getElementById('gtPaleta');
        if (palEl) p.paleta = palEl.value;
        const minEl = document.getElementById('gtMin'), maxEl = document.getElementById('gtMax');
        if (minEl && maxEl) {
            const editing = minEl.hasAttribute('data-editing');
            p.autoMinMax = !editing;
            if (editing) {
                p.customMin = parseFloat(minEl.value);
                p.customMax = parseFloat(maxEl.value);
            }
        }
        const undefEl = document.getElementById('gtUndef');
        if (undefEl) p.undefRaw = undefEl.value || '';
        const clMin = document.getElementById('gtClipMin'), clMax = document.getElementById('gtClipMax');
        p.clipBelow = (clMin && clMin.value.trim() !== '') ? parseFloat(clMin.value) : null;
        p.clipAbove = (clMax && clMax.value.trim() !== '') ? parseFloat(clMax.value) : null;
        // Sincroniza camada base também (props.paleta passa pra layer, decoded, etc.)
        if (layer.id !== 'primary' && layer.type === 'geotiff') {
            layer.paleta = p.paleta;
        }
    }
    async function gtApplyActiveLayer() {
        gtCaptureControlsToActive();
        const layer = gtGetLayerObj(gtActiveLayerId);
        if (!layer) return;
        const p = layer.props || gtPrimaryProps;
        // Atualiza gtMaskOpts global (afeta gtSampleAtLatLon/gtIsMasked, e renderização da primary)
        gtMaskOpts = { extras: gtParseUndefList(p.undefRaw), clipBelow: p.clipBelow, clipAbove: p.clipAbove };
        if (layer.id === 'primary') {
            // Render normal do primário
            gtRecomputeMinMaxAuto();
            gtRenderar();
            gtDesenharColorbar();
        } else if (layer.type === 'geotiff' && _gtMap) {
            // Recolore a camada extra com paleta/min/max próprios e re-empurra ao mapa
            const opts = { paleta: p.paleta };
            const dec = layer.decoded;
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                opts.min = p.customMin; opts.max = p.customMax;
            }
            const extras = gtParseUndefList(p.undefRaw);
            if (extras) opts.nodataExtras = extras;
            if (p.clipBelow != null) opts.clipBelow = p.clipBelow;
            if (p.clipAbove != null) opts.clipAbove = p.clipAbove;
            const img = SisMOM_GeoTIFF.aplicarPaleta(dec, opts);
            await _gtMap.addRasterOverlay(layer.id, img, dec.bbox, layer.opacity);
            gtDesenharColorbar();
        } else {
            gtDesenharColorbar();
        }
    }

    function bindGeoTIFFUI() {
        const btn = document.getElementById('btnOpenGeoTIFF');
        if (!btn) return;'''

# ─── (3) Substitui gtRenderLayerChips por versão com ↑↓ e seleção de ativa ───
OLD_CHIPS = '''    function gtRenderLayerChips() {
        const container = document.getElementById('gtLayerChips');
        if (!container) return;
        container.innerHTML = '';
        for (const l of gtExtraLayers) {
            const chip = document.createElement('span');
            chip.style.cssText = 'display:inline-flex;align-items:center;gap:4px;padding:2px 6px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);border-radius:12px;font-size:11px;color:var(--text,#cbd6e6)';
            const dot = document.createElement('span');
            dot.style.cssText = 'width:8px;height:8px;border-radius:50%;background:' + (l.type==='geojson' ? l.color : '#4caf50');
            const label = document.createElement('span');
            label.textContent = l.name;
            label.style.maxWidth = '160px';
            label.style.overflow = 'hidden';
            label.style.textOverflow = 'ellipsis';
            label.style.whiteSpace = 'nowrap';
            label.style.opacity = l.visible ? '1' : '0.45';
            const eye = document.createElement('button');
            eye.type = 'button';
            eye.title = l.visible ? 'Ocultar' : 'Mostrar';
            eye.textContent = l.visible ? '👁' : '⊘';
            eye.style.cssText = 'background:none;border:0;color:inherit;cursor:pointer;padding:0 2px;font-size:12px';
            eye.addEventListener('click', () => gtToggleExtraLayer(l.id));
            const x = document.createElement('button');
            x.type = 'button';
            x.title = 'Remover';
            x.textContent = '×';
            x.style.cssText = 'background:none;border:0;color:#f88;cursor:pointer;padding:0 2px;font-size:14px;font-weight:700';
            x.addEventListener('click', () => gtRemoveExtraLayer(l.id));
            chip.appendChild(dot); chip.appendChild(label); chip.appendChild(eye); chip.appendChild(x);
            container.appendChild(chip);
        }
    }'''
NEW_CHIPS = '''    function gtRenderLayerChips() {
        const container = document.getElementById('gtLayerChips');
        if (!container) return;
        container.innerHTML = '';
        const all = gtAllLayers();
        all.forEach((l, idx) => {
            const item = document.createElement('div');
            item.className = 'gt-layer-item' + (l.id === gtActiveLayerId ? ' active' : '');
            const dot = document.createElement('span');
            dot.className = 'gl-dot';
            dot.style.background = (l.type === 'geojson') ? (l.color || '#aaa') : (l.id === 'primary' ? '#4dd0e1' : '#4caf50');
            const name = document.createElement('span');
            name.className = 'gl-name';
            name.textContent = l.name || l.id;
            name.style.opacity = (l.visible === false) ? '0.45' : '1';
            const up = document.createElement('button');
            up.type = 'button'; up.title = 'Subir';  up.textContent = '↑';
            up.disabled = (l.id === 'primary' || idx <= 1);
            up.addEventListener('click', (e) => { e.stopPropagation(); gtMoveLayer(l.id, -1); });
            const dn = document.createElement('button');
            dn.type = 'button'; dn.title = 'Descer'; dn.textContent = '↓';
            dn.disabled = (l.id === 'primary' || idx >= all.length - 1);
            dn.addEventListener('click', (e) => { e.stopPropagation(); gtMoveLayer(l.id, +1); });
            const eye = document.createElement('button');
            eye.type = 'button';
            eye.title = (l.visible === false) ? 'Mostrar' : 'Ocultar';
            eye.textContent = (l.visible === false) ? '⊘' : '👁';
            eye.disabled = (l.id === 'primary');
            eye.addEventListener('click', (e) => { e.stopPropagation(); gtToggleExtraLayer(l.id); });
            item.appendChild(dot); item.appendChild(name); item.appendChild(up); item.appendChild(dn); item.appendChild(eye);
            if (l.id !== 'primary') {
                const rm = document.createElement('button');
                rm.type = 'button'; rm.title = 'Remover'; rm.textContent = '×';
                rm.className = 'gl-rm';
                rm.addEventListener('click', (e) => { e.stopPropagation(); gtRemoveExtraLayer(l.id); });
                item.appendChild(rm);
            }
            item.addEventListener('click', () => gtSetActiveLayer(l.id));
            container.appendChild(item);
        });
    }

    async function gtMoveLayer(id, delta) {
        if (id === 'primary') return;
        const i = gtExtraLayers.findIndex(l => l.id === id);
        if (i < 0) return;
        const j = Math.max(0, Math.min(gtExtraLayers.length - 1, i + delta));
        if (i === j) return;
        const [moved] = gtExtraLayers.splice(i, 1);
        gtExtraLayers.splice(j, 0, moved);
        // Re-empurra ao mapa na nova ordem: remove e adiciona todas
        if (_gtMap) {
            // Limpa todas e refaz na nova ordem
            for (const l of gtExtraLayers) {
                if (l.type === 'geotiff') _gtMap.removeRasterOverlay(l.id);
                if (l.type === 'geojson') _gtMap.removeGeoJSON(l.id);
            }
            await gtSyncAllExtrasToMap();
        }
        gtRenderLayerChips();
    }'''

# ─── (4) gtDesenharColorbar: usar paleta/min/max da camada ativa ───
OLD_CB_PAL = '''        const palSel = document.getElementById('gtPaleta');
        const palName = (palSel && palSel.value) || 'viridis';'''
NEW_CB_PAL = '''        // Paleta/min/max da camada ATIVA (não necessariamente da global)
        const activeLayer = (typeof gtGetLayerObj === 'function') ? gtGetLayerObj(gtActiveLayerId) : null;
        const activeProps = activeLayer && activeLayer.props;
        const palSel = document.getElementById('gtPaleta');
        const palName = (activeProps && activeProps.paleta) || (palSel && palSel.value) || 'viridis';'''

OLD_CB_MINMAX = '''        // Min/max correntes
        let mn = null, mx = null;
        const minEl = document.getElementById('gtMin'), maxEl = document.getElementById('gtMax');
        if (minEl && maxEl && minEl.value !== '' && maxEl.value !== '') {
            mn = parseFloat(minEl.value); mx = parseFloat(maxEl.value);
        } else if (gtLastDecoded) {
            mn = gtLastDecoded.min; mx = gtLastDecoded.max;
        }'''
NEW_CB_MINMAX = '''        // Min/max da camada ATIVA
        let mn = null, mx = null;
        if (activeLayer) {
            const dec = (activeLayer.id === 'primary') ? gtLastDecoded : activeLayer.decoded;
            if (activeProps && !activeProps.autoMinMax && isFinite(activeProps.customMin) && isFinite(activeProps.customMax)) {
                mn = activeProps.customMin; mx = activeProps.customMax;
            } else if (dec) {
                mn = dec.min; mx = dec.max;
            }
        }
        if (mn == null) {
            const minEl = document.getElementById('gtMin'), maxEl = document.getElementById('gtMax');
            if (minEl && maxEl && minEl.value !== '' && maxEl.value !== '') { mn = parseFloat(minEl.value); mx = parseFloat(maxEl.value); }
            else if (gtLastDecoded) { mn = gtLastDecoded.min; mx = gtLastDecoded.max; }
        }'''

# ─── (5) Listeners dos controles: chamar gtApplyActiveLayer em vez de gtRenderar direto ───
OLD_LISTENERS_FILE = '''        fileInput.addEventListener('change', async (e) => {
            const f = e.target.files[0];
            if (!f) return;
            try {
                const ab = await f.arrayBuffer();
                gtLastDecoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
                gtAtualizarInfoEMinMax(gtLastDecoded);
                gtRenderar();
                gtUpdateMapToggleEnabled();
                if (_gtMap && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
                gtSyncMapOverlay();
            } catch (err) {
                alert('Erro ao decodificar GeoTIFF: ' + ((err && err.message) || err));
            }
        });'''
NEW_LISTENERS_FILE = '''        fileInput.addEventListener('change', async (e) => {
            const f = e.target.files[0];
            if (!f) return;
            try {
                const ab = await f.arrayBuffer();
                gtLastDecoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
                gtAtualizarInfoEMinMax(gtLastDecoded);
                gtRenderar();
                gtUpdateMapToggleEnabled();
                if (_gtMap && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
                gtSyncMapOverlay();
                // Reset active = primary e reflete novos min/max
                gtSetActiveLayer('primary');
            } catch (err) {
                alert('Erro ao decodificar GeoTIFF: ' + ((err && err.message) || err));
            }
        });'''

OLD_LISTENERS_PAL = '''        document.getElementById('gtPaleta').addEventListener('change', gtRenderar);'''
NEW_LISTENERS_PAL = '''        document.getElementById('gtPaleta').addEventListener('change', () => { gtApplyActiveLayer(); });'''

OLD_LISTENERS_MM = '''        document.getElementById('gtMin').addEventListener('change', gtRenderar);
        document.getElementById('gtMax').addEventListener('change', gtRenderar);'''
NEW_LISTENERS_MM = '''        document.getElementById('gtMin').addEventListener('change', () => { gtApplyActiveLayer(); });
        document.getElementById('gtMax').addEventListener('change', () => { gtApplyActiveLayer(); });'''

OLD_APPLYMASK = '''        function applyMaskAndRender() {
            gtParseMaskFromUI();
            gtRecomputeMinMaxAuto();
            gtRenderar();
        }'''
NEW_APPLYMASK = '''        function applyMaskAndRender() {
            // Aplica nas props da camada ATIVA, não globalmente
            gtApplyActiveLayer();
        }'''

# ─── (6) Chamada de gtReorganizeLayout no init de bindGeoTIFFUI ───
OLD_BTN_BIND = '''        btn.addEventListener('click', abrirModalGeoTIFF);
        document.getElementById('btnGtClose').addEventListener('click', fecharModalGeoTIFF);'''
NEW_BTN_BIND = '''        btn.addEventListener('click', abrirModalGeoTIFF);
        document.getElementById('btnGtClose').addEventListener('click', fecharModalGeoTIFF);
        try { gtReorganizeLayout(); } catch (e) { console.error('gtReorganizeLayout', e); }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtActiveLayerId' in src:
        print(f"[{path.name}] já patcheado (gtActiveLayerId); pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_CSS,             NEW_CSS,             'css side panel')
    src = rep(src, OLD_BIND_END_ANCHOR, NEW_BIND_END_ANCHOR, 'gtReorganize + active layer')
    src = rep(src, OLD_CHIPS,           NEW_CHIPS,           'chips with up/down/active')
    src = rep(src, OLD_CB_PAL,          NEW_CB_PAL,          'colorbar paleta active')
    src = rep(src, OLD_CB_MINMAX,       NEW_CB_MINMAX,       'colorbar minmax active')
    src = rep(src, OLD_LISTENERS_FILE,  NEW_LISTENERS_FILE,  'file listener reset active')
    src = rep(src, OLD_LISTENERS_PAL,   NEW_LISTENERS_PAL,   'paleta listener')
    src = rep(src, OLD_LISTENERS_MM,    NEW_LISTENERS_MM,    'minmax listeners')
    src = rep(src, OLD_APPLYMASK,       NEW_APPLYMASK,       'applyMaskAndRender')
    src = rep(src, OLD_BTN_BIND,        NEW_BTN_BIND,        'reorganize on init')

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
        print('OK - ' + str(len(a)) + ' bytes em ambas')

if __name__ == '__main__':
    main()
