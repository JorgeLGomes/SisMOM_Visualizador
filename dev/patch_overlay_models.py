#!/usr/bin/env python3
"""
Sobreposição de modelos/variáveis no mesmo painel GeoTIFF.

Adiciona ao lado de "+ Adicionar GeoTIFF/GeoJSON..." um botão
"+ Adicionar do modelo" que abre um mini-formulário com seletores de
modelo, variável, data e passo. Ao clicar Adicionar:
  - Monta a URL via montarURL (já existente)
  - Faz fetch+decode via _gtFetchAndDecode (já existente, com cache)
  - Cria entry em gtExtraLayers com mesma forma das camadas locais
  - Aciona gtRenderLayerChips e gtRenderCalcSelects

Como gtExtraLayers já é o array unificado de camadas extras (raster +
geojson), as novas camadas herdam automaticamente:
  - Controle de paleta/min/max/UNDEF/clip por camada (gtSetActiveLayer)
  - Reorder, ocultar, remover
  - Opacidade por camada
  - Calculadora (A op B onde B é outro modelo, A é primária, etc.)
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) HTML: adicionar botão + form inline ao lado do "Adicionar GeoTIFF/GeoJSON..."
OLD_HTML = '''                <button class="btn btn-ghost" id="btnGtAddLayer" type="button">+ Adicionar GeoTIFF/GeoJSON…</button>
                <button class="btn btn-ghost" id="btnGtClearLayers" type="button" title="Remover todas as camadas extras">Limpar</button>
                <span id="gtLayerChips" style="display:inline-flex;gap:6px;flex-wrap:wrap;align-items:center"></span>
            </div>'''
NEW_HTML = '''                <button class="btn btn-ghost" id="btnGtAddLayer" type="button">+ Adicionar GeoTIFF/GeoJSON…</button>
                <button class="btn btn-ghost" id="btnGtAddFromModel" type="button" title="Adicionar uma camada do FTP escolhendo modelo/variável/data/passo">+ Adicionar do modelo</button>
                <button class="btn btn-ghost" id="btnGtClearLayers" type="button" title="Remover todas as camadas extras">Limpar</button>
                <span id="gtLayerChips" style="display:inline-flex;gap:6px;flex-wrap:wrap;align-items:center"></span>
            </div>
            <div id="gtAddFromModelForm" style="display:none;padding:8px 10px;background:var(--bg-elev-1,#0e1622);border:1px solid var(--border-subtle);border-radius:6px;margin-bottom:8px">
                <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
                    <span style="color:var(--text-muted,#aab);font-size:11px;font-weight:600">Sobrepor:</span>
                    <select id="gtOvModelo" title="Modelo" style="font-size:12px;max-width:140px"></select>
                    <select id="gtOvVariavel" title="Variável" style="font-size:12px;max-width:160px"></select>
                </div>
                <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
                    <input type="date" id="gtOvData" style="font-size:12px;width:130px">
                    <select id="gtOvHora" style="font-size:12px;width:60px" title="Hora UTC">
                        <option value="00" selected>00Z</option>
                        <option value="06">06Z</option>
                        <option value="12">12Z</option>
                        <option value="18">18Z</option>
                    </select>
                    <input type="number" id="gtOvPasso" placeholder="passo (h)" min="0" max="999" step="1" style="font-size:12px;width:90px" title="Passo de previsão (horas)">
                    <button class="btn btn-primary" id="btnGtDoAddFromModel" type="button" style="font-size:12px">Adicionar</button>
                    <button class="btn btn-ghost" id="btnGtCancelAddFromModel" type="button" style="font-size:12px">Cancelar</button>
                </div>
                <div id="gtOvStatus" style="font-size:11px;color:var(--text-muted,#aab);margin-top:4px;min-height:1em"></div>
            </div>'''

# (2) JS: nova função + bindings dos listeners
OLD_JS_BTN = '''        const btnAdd = document.getElementById('btnGtAddLayer');
        const extraFile = document.getElementById('gtExtraFile');'''
NEW_JS_BTN = '''        const btnAdd = document.getElementById('btnGtAddLayer');
        const extraFile = document.getElementById('gtExtraFile');
        // ─── Adicionar camada do FTP (modelo + var + data + passo) ───
        const btnAddFromModel    = document.getElementById('btnGtAddFromModel');
        const formAddFromModel   = document.getElementById('gtAddFromModelForm');
        const btnDoAddFromModel  = document.getElementById('btnGtDoAddFromModel');
        const btnCancelAddFromModel = document.getElementById('btnGtCancelAddFromModel');
        const ovStatus = document.getElementById('gtOvStatus');
        function _ovSetStatus(msg, isErr) {
            if (!ovStatus) return;
            ovStatus.textContent = msg || '';
            ovStatus.style.color = isErr ? 'var(--accent-rose,#ff7a90)' : 'var(--text-muted,#aab)';
        }
        function _ovPopulateModelos() {
            const sel = document.getElementById('gtOvModelo');
            if (!sel) return;
            const prev = sel.value;
            sel.innerHTML = '';
            const ids = Object.keys(modelos).filter(id => {
                const m = modelos[id];
                if (!m) return false;
                if (m.tem_tif === false) return false;
                if (m.tem_png === true && m.tem_tif !== true) return false;
                return true;
            });
            ids.forEach(id => {
                const opt = document.createElement('option');
                opt.value = id; opt.textContent = modelos[id].nome || id;
                sel.appendChild(opt);
            });
            if (prev && ids.includes(prev)) sel.value = prev;
        }
        function _ovPopulateVars() {
            const selM = document.getElementById('gtOvModelo');
            const selV = document.getElementById('gtOvVariavel');
            if (!selM || !selV) return;
            const m = modelos[selM.value];
            const prev = selV.value;
            selV.innerHTML = '';
            const vars = (m && m.variaveis) ? m.variaveis.filter(v => v.disp_tif !== false) : [];
            vars.forEach(v => {
                const opt = document.createElement('option');
                opt.value = v.id;
                opt.textContent = (v.label || v.id) + (v.unidade ? ' (' + v.unidade + ')' : '');
                selV.appendChild(opt);
            });
            if (prev && vars.some(v => v.id === prev)) selV.value = prev;
        }
        if (btnAddFromModel) btnAddFromModel.addEventListener('click', () => {
            const show = formAddFromModel.style.display === 'none';
            formAddFromModel.style.display = show ? '' : 'none';
            if (show) {
                _ovPopulateModelos();
                _ovPopulateVars();
                // Default: copia data do slot ativo / passo atual
                const s = state.slots[gtActivePanel || 0];
                if (s && s.data && s.data.length >= 10) {
                    const d = document.getElementById('gtOvData');
                    if (d) d.value = s.data.slice(0,4) + '-' + s.data.slice(4,6) + '-' + s.data.slice(6,8);
                    const h = document.getElementById('gtOvHora');
                    if (h) h.value = s.data.slice(8,10);
                }
                const passoEl = document.getElementById('gtOvPasso');
                if (passoEl && state.passoAtual) passoEl.value = state.passoAtual;
                _ovSetStatus('');
            }
        });
        if (btnCancelAddFromModel) btnCancelAddFromModel.addEventListener('click', () => {
            formAddFromModel.style.display = 'none';
            _ovSetStatus('');
        });
        const selOvModelo = document.getElementById('gtOvModelo');
        if (selOvModelo) selOvModelo.addEventListener('change', _ovPopulateVars);
        if (btnDoAddFromModel) btnDoAddFromModel.addEventListener('click', async () => {
            try {
                const modeloId = document.getElementById('gtOvModelo').value;
                const variavelId = document.getElementById('gtOvVariavel').value;
                const dataISO = document.getElementById('gtOvData').value;
                const hora = document.getElementById('gtOvHora').value || '00';
                const passo = parseInt(document.getElementById('gtOvPasso').value, 10);
                if (!modeloId || !variavelId || !dataISO || !isFinite(passo)) {
                    _ovSetStatus('Preencha modelo, variável, data e passo.', true); return;
                }
                const dataFTP = dataISO.replace(/-/g, '') + hora;
                // Monta URL preferindo rota TIF
                const m = modelos[modeloId];
                if (!m) { _ovSetStatus('Modelo não encontrado.', true); return; }
                const hasOwnTifRoute = (m.url_path_tif && !m.same_url_for_tif) || (m.file_name_tif && !m.same_name_for_tif);
                let url;
                if (hasOwnTifRoute) {
                    const mTif = Object.assign({}, m, {
                        url_path: m.same_url_for_tif ? m.url_path : (m.url_path_tif || m.url_path),
                        file_name: m.same_name_for_tif ? m.file_name : (m.file_name_tif || m.file_name),
                        extensao: m.extensao_tif || '.tif'
                    });
                    const orig = modelos[modeloId];
                    modelos[modeloId] = mTif;
                    try { url = montarURL({ modelo: modeloId, data: dataFTP, variavel: variavelId, passo }); }
                    finally { modelos[modeloId] = orig; }
                } else {
                    url = montarURL({ modelo: modeloId, data: dataFTP, variavel: variavelId, passo });
                    if (m && !(SisMOM_GeoTIFF.isGeoTiffModel(m))) {
                        const derived = (typeof gtDeriveTifUrl === 'function') ? gtDeriveTifUrl(url) : url;
                        url = derived;
                    }
                }
                if (!url) { _ovSetStatus('Não foi possível montar a URL.', true); return; }
                _ovSetStatus('Baixando...');
                btnDoAddFromModel.disabled = true;
                const decoded = await _gtFetchAndDecode(url);
                if (!decoded) throw new Error('decode falhou');
                const v = m.variaveis.find(x => x.id === variavelId);
                const labelV = v ? (v.label || v.id) : variavelId;
                const dataLabel = dataISO.slice(8,10) + '/' + dataISO.slice(5,7) + ' ' + hora + 'Z +' + String(passo).padStart(3,'0') + 'h';
                const name = (m.nome || modeloId) + ' · ' + labelV + ' · ' + dataLabel;
                const id = 'ext_' + (++gtLayerSeq) + '_' + Date.now();
                const paleta = (document.getElementById('gtPaleta')||{}).value || 'viridis';
                const layer = { id, type: 'geotiff', name, visible: true, opacity: 0.85,
                    decoded, paleta,
                    source: { modeloId, variavelId, data: dataFTP, passo, url },
                    props: { paleta, autoMinMax: true, customMin: null, customMax: null,
                              undefRaw: '', clipBelow: null, clipAbove: null }
                };
                gtExtraLayers.push(layer);
                try { gtLayerEnsureMap(); } catch (_) {}
                try { await gtLayerPushToMap(layer); } catch (_) {}
                try { gtRenderLayerChips(); } catch (_) {}
                try { gtRenderCalcSelects(); } catch (_) {}
                _ovSetStatus('Adicionado: ' + name);
                btnDoAddFromModel.disabled = false;
                // Mantém form aberto para o usuário adicionar mais facilmente
            } catch (e) {
                _ovSetStatus('Erro: ' + ((e && e.message) || e), true);
                btnDoAddFromModel.disabled = false;
            }
        });'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'btnGtAddFromModel' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HTML, NEW_HTML, 'html: botao + form Adicionar do modelo')
    src = rep(src, OLD_JS_BTN, NEW_JS_BTN, 'js: bindings e gtAddExtraLayerFromModel')

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
        print(f"OK - {len(a)} bytes em ambas")

if __name__ == '__main__':
    main()
