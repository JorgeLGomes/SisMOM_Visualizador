#!/usr/bin/env python3
"""
Patch:
  1) HUD inferior alinhado à esquerda; atribuição à direita.
  2) Pilha de mini-colorbars sobre o canvas (acima do HUD), uma por
     camada raster visível, com o nome da camada à frente.
  3) Habilitar toggle 👁 também para a camada base (primary); ela passa
     a respeitar gtPrimaryVisible no render/sync e no chip.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Posições: HUD → esquerda; atribuição → direita
OLD_HUD_POS = '''.gt-bottom-hud {
            position: absolute;
            right: 12px; left: auto; transform: none;
            bottom: 14px;'''
NEW_HUD_POS = '''.gt-bottom-hud {
            position: absolute;
            left: 12px; right: auto; transform: none;
            bottom: 14px;'''

OLD_ATTRIB = '#modalGeoTIFF.inline #gtAttrib { right: auto; left: 8px; bottom: 8px; }'
NEW_ATTRIB = '#modalGeoTIFF.inline #gtAttrib { right: 8px; left: auto; bottom: 8px; }'

# (2) CSS para a pilha de colorbars overlay
OLD_CSS_END = '''.gt-bottom-hud .gt-hud-coord {
            min-width: 220px;
            text-align: center;
            padding: 0 8px;
        }'''
NEW_CSS_END = '''.gt-bottom-hud .gt-hud-coord {
            min-width: 220px;
            text-align: center;
            padding: 0 8px;
        }
        /* Pilha de mini-colorbars overlay (canto inferior esquerdo, acima do HUD) */
        .gt-cb-stack {
            position: absolute;
            left: 12px; bottom: 62px;
            z-index: 9;
            display: flex; flex-direction: column-reverse; gap: 4px;
            pointer-events: none;
            max-width: 420px;
        }
        .gt-cb-item {
            display: flex; align-items: center; gap: 8px;
            background: rgba(10,18,30,0.78);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 6px;
            padding: 4px 8px;
            color: var(--text, #cbd6e6);
            font-family: ui-monospace, monospace;
            font-size: 11px;
            backdrop-filter: blur(6px);
        }
        .gt-cb-item .gt-cb-name {
            max-width: 140px;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
            font-weight: 600;
        }
        .gt-cb-item canvas { display: block; }
        .gt-cb-item .gt-cb-minmax { color: var(--text-muted, #aab); font-size: 10px; min-width: 80px; }'''

# (3) gtReorganizeLayout: também inserir o container da pilha de colorbars
OLD_REORG = '''                if (!el.querySelector('.gt-bottom-hud')) {
                    const hud = document.createElement('div');
                    hud.className = 'gt-bottom-hud';
                    hud.innerHTML = '' +
                        '<button type="button" id="gtBtnZoomIn"  title="Aproximar">+</button>' +
                        '<button type="button" id="gtBtnZoomOut" title="Afastar">−</button>' +
                        '<button type="button" id="gtBtnZoomReset" title="Recentrar">⟲</button>' +
                        '<span class="gt-hud-sep"></span>' +
                        '<span class="gt-hud-coord" id="gtCoordHud">—</span>';
                    el.appendChild(hud);
                }'''
NEW_REORG = '''                if (!el.querySelector('.gt-bottom-hud')) {
                    const hud = document.createElement('div');
                    hud.className = 'gt-bottom-hud';
                    hud.innerHTML = '' +
                        '<button type="button" id="gtBtnZoomIn"  title="Aproximar">+</button>' +
                        '<button type="button" id="gtBtnZoomOut" title="Afastar">−</button>' +
                        '<button type="button" id="gtBtnZoomReset" title="Recentrar">⟲</button>' +
                        '<span class="gt-hud-sep"></span>' +
                        '<span class="gt-hud-coord" id="gtCoordHud">—</span>';
                    el.appendChild(hud);
                }
                if (!el.querySelector('.gt-cb-stack')) {
                    const stack = document.createElement('div');
                    stack.className = 'gt-cb-stack';
                    stack.id = 'gtCbStack';
                    el.appendChild(stack);
                }'''

# (4) gtPrimaryVisible + atualizar gtRenderar / gtSyncMapOverlay para respeitar
OLD_PRIMARY_DECL = '''    /* ─── Camada ativa: controles operam sobre a camada selecionada ─── */
    let gtActiveLayerId = 'primary';
    // Props por camada (primary tem props globais; extras têm props no objeto)
    const gtPrimaryProps = { paleta: 'viridis', autoMinMax: true, customMin: null, customMax: null,
                              undefRaw: '', clipBelow: null, clipAbove: null };'''
NEW_PRIMARY_DECL = '''    /* ─── Camada ativa: controles operam sobre a camada selecionada ─── */
    let gtActiveLayerId = 'primary';
    let gtPrimaryVisible = true;
    // Props por camada (primary tem props globais; extras têm props no objeto)
    const gtPrimaryProps = { paleta: 'viridis', autoMinMax: true, customMin: null, customMax: null,
                              undefRaw: '', clipBelow: null, clipAbove: null };'''

# (5) gtGetLayerObj — primary agora carrega visible: gtPrimaryVisible
OLD_GETLAYER = '''        if (id === 'primary') {
            return {
                id: 'primary', type: 'geotiff',
                name: (gtLastDecoded && '(camada base)') || '—',
                visible: true,
                decoded: gtLastDecoded,
                props: gtPrimaryProps
            };
        }'''
NEW_GETLAYER = '''        if (id === 'primary') {
            return {
                id: 'primary', type: 'geotiff',
                name: (gtLastDecoded && '(camada base)') || '—',
                visible: gtPrimaryVisible,
                decoded: gtLastDecoded,
                props: gtPrimaryProps
            };
        }'''

# (6) Chips: liberar 👁 da primary
OLD_EYE_PRIMARY = '''            eye.title = (l.visible === false) ? 'Mostrar' : 'Ocultar';
            eye.textContent = (l.visible === false) ? '⊘' : '👁';
            eye.disabled = (l.id === 'primary');
            eye.addEventListener('click', (e) => { e.stopPropagation(); gtToggleExtraLayer(l.id); });'''
NEW_EYE_PRIMARY = '''            eye.title = (l.visible === false) ? 'Mostrar' : 'Ocultar';
            eye.textContent = (l.visible === false) ? '⊘' : '👁';
            eye.addEventListener('click', (e) => {
                e.stopPropagation();
                if (l.id === 'primary') gtTogglePrimaryVisible();
                else gtToggleExtraLayer(l.id);
            });'''

# (7) Função gtTogglePrimaryVisible — adicionar antes de gtMoveLayer
OLD_MOVE_ANCHOR = '''    async function gtMoveLayer(id, delta) {'''
NEW_MOVE_ANCHOR = '''    function gtTogglePrimaryVisible() {
        gtPrimaryVisible = !gtPrimaryVisible;
        if (gtPrimaryVisible) {
            // Re-aplica overlay primary no mapa
            if (typeof gtSyncMapOverlay === 'function') gtSyncMapOverlay();
        } else {
            // Remove overlay do mapa
            if (typeof _gtMap !== 'undefined' && _gtMap) _gtMap.clearOverlay();
        }
        gtRenderar();
        gtRenderLayerChips();
        gtRenderOverlayColorbars();
    }
    async function gtMoveLayer(id, delta) {'''

# (8) gtRenderar: se primary invisível, não desenha no gtCanvas
OLD_RENDERAR_BODY = '''        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);
        const cv = document.getElementById('gtCanvas');
        cv.width = gtLastDecoded.width; cv.height = gtLastDecoded.height;
        cv.getContext('2d').putImageData(img, 0, 0);
        gtDesenharColorbar();
    }'''
NEW_RENDERAR_BODY = '''        const cv = document.getElementById('gtCanvas');
        if (!gtPrimaryVisible) {
            cv.width = 1; cv.height = 1;
            cv.getContext('2d').clearRect(0,0,1,1);
            gtDesenharColorbar();
            gtRenderOverlayColorbars();
            return;
        }
        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);
        cv.width = gtLastDecoded.width; cv.height = gtLastDecoded.height;
        cv.getContext('2d').putImageData(img, 0, 0);
        gtDesenharColorbar();
        gtRenderOverlayColorbars();
    }'''

# (9) gtSyncMapOverlay: se primary invisível, não empurra overlay primary
OLD_SYNC_PUSH = '''        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);
        const op = (parseInt(document.getElementById('gtOpacity').value, 10) || 85) / 100;
        await _gtMap.setRasterOverlay(img, gtLastDecoded.bbox, op);
        gtDesenharColorbar();
    }'''
NEW_SYNC_PUSH = '''        if (!gtPrimaryVisible) {
            if (_gtMap) _gtMap.clearOverlay();
            gtDesenharColorbar();
            gtRenderOverlayColorbars();
            return;
        }
        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);
        const op = (parseInt(document.getElementById('gtOpacity').value, 10) || 85) / 100;
        await _gtMap.setRasterOverlay(img, gtLastDecoded.bbox, op);
        gtDesenharColorbar();
        gtRenderOverlayColorbars();
    }'''

# (10) Nova função gtRenderOverlayColorbars (insere antes de gtDesenharColorbar)
OLD_CB_ANCHOR = '''    function gtDesenharColorbar() {'''
NEW_CB_ANCHOR = '''    function gtRenderOverlayColorbars() {
        const stack = document.getElementById('gtCbStack');
        if (!stack) return;
        stack.innerHTML = '';
        // Coleta camadas raster visíveis (primary se visível + extras geotiff visíveis)
        const items = [];
        const all = (typeof gtAllLayers === 'function') ? gtAllLayers() : [];
        for (const l of all) {
            if (l.type !== 'geotiff') continue;
            if (l.visible === false) continue;
            const dec = (l.id === 'primary') ? gtLastDecoded : l.decoded;
            if (!dec) continue;
            const p = (l.props || (l.id === 'primary' ? gtPrimaryProps : null)) || {};
            const palName = p.paleta || (l.id === 'primary' ? 'viridis' : 'viridis');
            let mn, mx;
            if (!p.autoMinMax && isFinite(p.customMin) && isFinite(p.customMax) && p.customMax > p.customMin) {
                mn = p.customMin; mx = p.customMax;
            } else { mn = dec.min; mx = dec.max; }
            items.push({ id: l.id, name: l.name || l.id, palName, mn, mx });
        }
        // Ordem do mais recente (extras topo do array) para a base; queremos visualmente:
        // camada extra mais "alta" no topo da pilha. column-reverse no CSS faz o último item ir mais para cima.
        for (const it of items) {
            const row = document.createElement('div');
            row.className = 'gt-cb-item';
            row.dataset.layer = it.id;
            const name = document.createElement('span'); name.className = 'gt-cb-name'; name.textContent = it.name;
            const cv = document.createElement('canvas'); cv.width = 140; cv.height = 12;
            const ctx = cv.getContext('2d');
            const PAL = (window.SisMOM_GeoTIFF && SisMOM_GeoTIFF.GT_PALETTES) ? SisMOM_GeoTIFF.GT_PALETTES[it.palName] : null;
            if (PAL) {
                const img = ctx.createImageData(cv.width, 1);
                const a = img.data;
                for (let i = 0; i < cv.width; i++) {
                    const t = i / Math.max(1, cv.width - 1);
                    const idx = Math.min(255, Math.max(0, (t * 255) | 0));
                    a[i*4]   = PAL[idx*3];
                    a[i*4+1] = PAL[idx*3+1];
                    a[i*4+2] = PAL[idx*3+2];
                    a[i*4+3] = 255;
                }
                const off = document.createElement('canvas'); off.width = cv.width; off.height = 1;
                off.getContext('2d').putImageData(img, 0, 0);
                ctx.imageSmoothingEnabled = false;
                ctx.drawImage(off, 0, 0, cv.width, cv.height);
            }
            const mm = document.createElement('span'); mm.className = 'gt-cb-minmax';
            const fmt = (v) => { const a = Math.abs(v); return (a !== 0 && (a < 1e-3 || a >= 1e6)) ? v.toExponential(2) : v.toFixed(a >= 100 ? 1 : 2); };
            mm.textContent = `${fmt(it.mn)} … ${fmt(it.mx)}`;
            row.appendChild(name); row.appendChild(cv); row.appendChild(mm);
            stack.appendChild(row);
        }
    }
    function gtDesenharColorbar() {'''

# (11) Atualizar pontos que mexem em camadas para chamar gtRenderOverlayColorbars
# gtToggleExtraLayer
OLD_TOGGLE_EXTRA_END = '''        gtRenderLayerChips();
    }

    function gtRenderLayerChips() {'''
NEW_TOGGLE_EXTRA_END = '''        gtRenderLayerChips();
        gtRenderOverlayColorbars();
    }

    function gtRenderLayerChips() {'''

# (12) gtRemoveExtraLayer também atualiza colorbars
OLD_REMOVE_END = '''        gtRenderLayerChips();
    }

    function gtToggleExtraLayer(id) {'''
NEW_REMOVE_END = '''        gtRenderLayerChips();
        gtRenderOverlayColorbars();
    }

    function gtToggleExtraLayer(id) {'''

# (13) gtMoveLayer já chama gtRenderLayerChips; vamos adicionar overlay colorbars
OLD_MOVE_END = '''            await gtSyncAllExtrasToMap();
        }
        gtRenderLayerChips();
    }'''
NEW_MOVE_END = '''            await gtSyncAllExtrasToMap();
        }
        gtRenderLayerChips();
        gtRenderOverlayColorbars();
    }'''

# (14) gtSetActiveLayer já chama gtDesenharColorbar; chamamos também overlay colorbars
OLD_SETACTIVE_END = '''        gtRenderLayerChips();
        gtDesenharColorbar();
        gtRenderar();
    }'''
NEW_SETACTIVE_END = '''        gtRenderLayerChips();
        gtDesenharColorbar();
        gtRenderOverlayColorbars();
        gtRenderar();
    }'''

# (15) gtApplyActiveLayer extra (geotiff): atualiza overlay colorbars
OLD_APPLY_GEO = '''            const img = SisMOM_GeoTIFF.aplicarPaleta(dec, opts);
            await _gtMap.addRasterOverlay(layer.id, img, dec.bbox, layer.opacity);
            gtDesenharColorbar();
        } else {
            gtDesenharColorbar();
        }
    }'''
NEW_APPLY_GEO = '''            const img = SisMOM_GeoTIFF.aplicarPaleta(dec, opts);
            await _gtMap.addRasterOverlay(layer.id, img, dec.bbox, layer.opacity);
            gtDesenharColorbar();
            gtRenderOverlayColorbars();
        } else {
            gtDesenharColorbar();
            gtRenderOverlayColorbars();
        }
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gt-cb-stack' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HUD_POS,         NEW_HUD_POS,         'hud pos left')
    src = rep(src, OLD_ATTRIB,          NEW_ATTRIB,          'attrib pos right')
    src = rep(src, OLD_CSS_END,         NEW_CSS_END,         'css stack')
    src = rep(src, OLD_REORG,           NEW_REORG,           'reorganize add stack')
    src = rep(src, OLD_PRIMARY_DECL,    NEW_PRIMARY_DECL,    'primary visible decl')
    src = rep(src, OLD_GETLAYER,        NEW_GETLAYER,        'getLayer primary visible')
    src = rep(src, OLD_EYE_PRIMARY,     NEW_EYE_PRIMARY,     'eye primary enable')
    src = rep(src, OLD_MOVE_ANCHOR,     NEW_MOVE_ANCHOR,     'togglePrimary fn')
    src = rep(src, OLD_RENDERAR_BODY,   NEW_RENDERAR_BODY,   'renderar primary visible')
    src = rep(src, OLD_SYNC_PUSH,       NEW_SYNC_PUSH,       'sync primary visible')
    src = rep(src, OLD_CB_ANCHOR,       NEW_CB_ANCHOR,       'overlay colorbars fn')
    src = rep(src, OLD_TOGGLE_EXTRA_END,NEW_TOGGLE_EXTRA_END,'toggle ext hook')
    src = rep(src, OLD_REMOVE_END,      NEW_REMOVE_END,      'remove ext hook')
    src = rep(src, OLD_MOVE_END,        NEW_MOVE_END,        'move hook')
    src = rep(src, OLD_SETACTIVE_END,   NEW_SETACTIVE_END,   'setActive hook')
    src = rep(src, OLD_APPLY_GEO,       NEW_APPLY_GEO,       'apply geo hook')

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
