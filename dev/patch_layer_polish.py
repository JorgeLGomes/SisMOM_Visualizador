#!/usr/bin/env python3
"""
Patch: três melhorias na gerência de camadas.
 (1) Nome do arquivo carregado substitui '(camada base)' no chip da primary.
     - File picker: usa f.name
     - FTP: usa o último segmento da URL como nome
 (2) Slider de opacidade afeta a CAMADA ATIVA (qualquer uma, não só primary).
     - Reflete a opacity da ativa quando o usuário troca de camada.
 (3) Botão 'Limpar' na linha de camadas extras: remove todas as extras
     (base permanece).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1.a) Variável gtPrimaryName + uso em gtGetLayerObj ───
OLD_PRI_DECL = '''    let gtPrimaryVisible = true;
    // Props por camada (primary tem props globais; extras têm props no objeto)'''
NEW_PRI_DECL = '''    let gtPrimaryVisible = true;
    let gtPrimaryName = '';   // nome do arquivo da camada base (file picker ou último segmento da URL)
    // Props por camada (primary tem props globais; extras têm props no objeto)'''

OLD_GET_PRI = '''        if (id === 'primary') {
            return {
                id: 'primary', type: 'geotiff',
                name: (gtLastDecoded && '(camada base)') || '—',
                visible: gtPrimaryVisible,
                decoded: gtLastDecoded,
                props: gtPrimaryProps
            };
        }'''
NEW_GET_PRI = '''        if (id === 'primary') {
            return {
                id: 'primary', type: 'geotiff',
                name: gtPrimaryName || (gtLastDecoded && '(camada base)') || '—',
                visible: gtPrimaryVisible,
                decoded: gtLastDecoded,
                opacity: ((typeof _gtMap !== 'undefined' && _gtMap && _gtMap.getOverlayOpacity)
                          ? _gtMap.getOverlayOpacity('primary') : 0.85),
                props: gtPrimaryProps
            };
        }'''

# ─── (1.b) File picker: armazenar nome ───
OLD_FILE_PICKER = '''        fileInput.addEventListener('change', async (e) => {
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
NEW_FILE_PICKER = '''        fileInput.addEventListener('change', async (e) => {
            const f = e.target.files[0];
            if (!f) return;
            try {
                const ab = await f.arrayBuffer();
                gtLastDecoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
                gtPrimaryName = f.name || '';
                gtAtualizarInfoEMinMax(gtLastDecoded);
                gtRenderar();
                gtUpdateMapToggleEnabled();
                if (_gtMap && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
                gtSyncMapOverlay();
                gtSetActiveLayer('primary');
            } catch (err) {
                alert('Erro ao decodificar GeoTIFF: ' + ((err && err.message) || err));
            }
        });'''

# ─── (1.c) gtLoadFromState (FTP): extrair último segmento da URL ───
OLD_FTP_LOAD = '''        try {
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
    }'''
NEW_FTP_LOAD = '''        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const ab = await resp.arrayBuffer();
            gtLastDecoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            try { gtPrimaryName = (url.split('?')[0].split('/').pop()) || ''; } catch (_) { gtPrimaryName = ''; }
            gtAtualizarInfoEMinMax(gtLastDecoded);
            try { gtUpdateMapToggleEnabled(); } catch (_) {}
            if (typeof _gtMap !== 'undefined' && _gtMap && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
            gtRenderar();
            try { gtRenderLayerChips(); } catch (_) {}
        } catch (e) {
            if (info) info.textContent = 'Falha ao carregar GeoTIFF: ' + ((e && e.message) || e);
        }
    }'''

# ─── (2.a) Adicionar getOverlayOpacity no mapa ───
OLD_GETIDX = '''        function getOverlayIndex(id) { return self.overlays.findIndex(o => o.id === id); }'''
NEW_GETIDX = '''        function getOverlayIndex(id) { return self.overlays.findIndex(o => o.id === id); }
        function getOverlayOpacity(id) {
            const o = self.overlays.find(x => x.id === id);
            return o ? o.opacity : null;
        }'''

# ─── (2.b) Expor getOverlayOpacity no return ───
OLD_RETURN = '''            moveOverlay, getOverlayIndex,'''
NEW_RETURN = '''            moveOverlay, getOverlayIndex, getOverlayOpacity,'''

# ─── (2.c) Slider de opacidade afeta a camada ativa + reflete ao trocar ───
OLD_OP_LIST = '''        if (op) op.addEventListener('input', () => {
            if (_gtMap) _gtMap.setOpacity(parseInt(op.value, 10) / 100);
        });'''
NEW_OP_LIST = '''        if (op) op.addEventListener('input', () => {
            const val = parseInt(op.value, 10) / 100;
            if (_gtMap && _gtMap.setOverlayOpacity) {
                _gtMap.setOverlayOpacity(gtActiveLayerId, val);
            }
            // Atualiza opacity no objeto da camada (para persistência ao reordenar)
            const layer = (gtActiveLayerId !== 'primary')
                ? gtExtraLayers.find(l => l.id === gtActiveLayerId)
                : null;
            if (layer) layer.opacity = val;
        });'''

# ─── (2.d) gtSetActiveLayer: refletir opacity da camada ativa no slider ───
OLD_SETACT_END = '''        gtRenderLayerChips();
        gtDesenharColorbar();
        gtRenderOverlayColorbars();
        gtRenderar();
    }'''
NEW_SETACT_END = '''        // Atualiza slider de opacidade para refletir a camada ativa
        const opEl = document.getElementById('gtOpacity');
        if (opEl) {
            let opVal = null;
            if (_gtMap && _gtMap.getOverlayOpacity) opVal = _gtMap.getOverlayOpacity(id);
            if (opVal == null) {
                if (id === 'primary') opVal = 0.85;
                else { const lx = gtExtraLayers.find(l => l.id === id); opVal = (lx && lx.opacity) || 0.85; }
            }
            opEl.value = Math.round(opVal * 100);
        }
        gtRenderLayerChips();
        gtDesenharColorbar();
        gtRenderOverlayColorbars();
        gtRenderar();
    }'''

# ─── (3.a) Botão Limpar na UI: adicionar ao lado do '+ Adicionar' ───
OLD_ADD_BTN = '''                <button class="btn btn-ghost" id="btnGtAddLayer" type="button">+ Adicionar GeoTIFF/GeoJSON…</button>'''
NEW_ADD_BTN = '''                <button class="btn btn-ghost" id="btnGtAddLayer" type="button">+ Adicionar GeoTIFF/GeoJSON…</button>
                <button class="btn btn-ghost" id="btnGtClearLayers" type="button" title="Remover todas as camadas extras">Limpar</button>'''

# ─── (3.b) Listener do botão Limpar ───
OLD_BIND_TAIL = '''        // Camadas extras
        const btnAdd = document.getElementById('btnGtAddLayer');
        const extraFile = document.getElementById('gtExtraFile');
        if (btnAdd && extraFile) {
            btnAdd.addEventListener('click', () => extraFile.click());
            extraFile.addEventListener('change', async (e) => {'''
NEW_BIND_TAIL = '''        // Camadas extras
        const btnAdd = document.getElementById('btnGtAddLayer');
        const extraFile = document.getElementById('gtExtraFile');
        const btnClearAll = document.getElementById('btnGtClearLayers');
        if (btnClearAll) btnClearAll.addEventListener('click', () => {
            if (!gtExtraLayers.length) return;
            const ok = window.confirm('Remover todas as camadas extras? (a camada base permanece)');
            if (!ok) return;
            // Remove cada extra do mapa e do array
            if (_gtMap) {
                for (const l of gtExtraLayers) {
                    if (l.type === 'geotiff') _gtMap.removeRasterOverlay(l.id);
                    else if (l.type === 'geojson') _gtMap.removeGeoJSON(l.id);
                }
            }
            gtExtraLayers.length = 0;
            // Se a ativa era uma extra, volta pra primary
            if (gtActiveLayerId !== 'primary') gtSetActiveLayer('primary');
            else { gtRenderLayerChips(); gtRenderOverlayColorbars(); }
        });
        if (btnAdd && extraFile) {
            btnAdd.addEventListener('click', () => extraFile.click());
            extraFile.addEventListener('change', async (e) => {'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'btnGtClearLayers' in src and 'gtPrimaryName' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_PRI_DECL,    NEW_PRI_DECL,    'primary name decl')
    src = rep(src, OLD_GET_PRI,     NEW_GET_PRI,     'primary getLayer name')
    src = rep(src, OLD_FILE_PICKER, NEW_FILE_PICKER, 'file picker name')
    src = rep(src, OLD_FTP_LOAD,    NEW_FTP_LOAD,    'ftp load name')
    src = rep(src, OLD_GETIDX,      NEW_GETIDX,      'getOverlayOpacity fn')
    src = rep(src, OLD_RETURN,      NEW_RETURN,      'expose getOverlayOpacity')
    src = rep(src, OLD_OP_LIST,     NEW_OP_LIST,     'op slider active layer')
    src = rep(src, OLD_SETACT_END,  NEW_SETACT_END,  'setActive reflect op')
    src = rep(src, OLD_ADD_BTN,     NEW_ADD_BTN,     'btn clear html')
    src = rep(src, OLD_BIND_TAIL,   NEW_BIND_TAIL,   'btn clear listener')

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
        print('OK - ' + str(len(a)) + ' bytes em ambas')

if __name__ == '__main__':
    main()
