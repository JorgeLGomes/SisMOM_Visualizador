#!/usr/bin/env python3
"""
Patch: rotas distintas PNG/GIF e TIF nos modelos.
 - Novos campos: tem_png, tem_tif (booleans), extensao_tif, url_path_tif,
   file_name_tif, same_url_for_tif, same_name_for_tif
 - Cada variável ganha disp_png e disp_tif (substituem visualmente os
   inputs Esc1/Esc2 da tabela; os escopo1/escopo2 originais ainda existem
   no schema, controlados pelo cabeçalho ESCOPO do modelo, não pela tabela)
 - Modal de config: novos checkboxes/inputs
 - Filtrar modelos por aba (PNG só mostra tem_png=true; GeoTIFF só tem_tif)
 - gtLoadFromState usa url_path_tif/file_name_tif quando setados
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1) HTML do modal: novos campos depois de cfgFileName ───
OLD_FORM = '''                <label for="cfgUrlPath">Template do endereço</label>
                <input type="text" id="cfgUrlPath" placeholder="https://.../{yyyy}{mm}{dd}{hh}/{escopo1}/{escopo2}/fig">
                <label for="cfgFileName">Template Nome Arq.</label>
                <input type="text" id="cfgFileName" placeholder="{prefixo}{f%3}{ext}">'''
NEW_FORM = '''                <label for="cfgUrlPath">Template do endereço (PNG/GIF)</label>
                <input type="text" id="cfgUrlPath" placeholder="https://.../{yyyy}{mm}{dd}{hh}/{escopo1}/{escopo2}/fig">
                <label for="cfgFileName">Template Nome Arq. (PNG/GIF)</label>
                <input type="text" id="cfgFileName" placeholder="{prefixo}{f%3}{ext}">
                <label style="grid-column:1/-1;display:flex;gap:14px;align-items:center;margin-top:6px;padding-top:6px;border-top:1px solid var(--border-subtle)">
                    <span style="font-weight:600;color:var(--text)">Formatos disponíveis no FTP:</span>
                    <label style="display:inline-flex;gap:4px;align-items:center;font-weight:normal;color:var(--text)"><input type="checkbox" id="cfgTemPng" checked> PNG/GIF</label>
                    <label style="display:inline-flex;gap:4px;align-items:center;font-weight:normal;color:var(--text)"><input type="checkbox" id="cfgTemTif"> GeoTIFF (.tif)</label>
                </label>
                <label for="cfgExtensaoTif">Sufixo do arquivo TIF</label>
                <select id="cfgExtensaoTif">
                    <option value=".tif" selected>.tif</option>
                    <option value=".tiff">.tiff</option>
                </select>
                <label for="cfgUrlPathTif" style="display:flex;align-items:center;gap:8px">
                    <span>Template do endereço (TIF)</span>
                    <label style="font-weight:normal;font-size:11px;color:var(--text-muted);display:inline-flex;gap:4px;align-items:center"><input type="checkbox" id="cfgSameUrlForTif" checked> usar o mesmo do PNG</label>
                </label>
                <input type="text" id="cfgUrlPathTif" placeholder="https://.../{yyyy}{mm}{dd}{hh}/{escopo1}/{escopo2}/geotiff">
                <label for="cfgFileNameTif" style="display:flex;align-items:center;gap:8px">
                    <span>Template Nome Arq. (TIF)</span>
                    <label style="font-weight:normal;font-size:11px;color:var(--text-muted);display:inline-flex;gap:4px;align-items:center"><input type="checkbox" id="cfgSameNameForTif" checked> usar o mesmo do PNG</label>
                </label>
                <input type="text" id="cfgFileNameTif" placeholder="{prefixo}{f%3}.tif">'''

# ─── (2) Cabeçalhos da tabela de variáveis (Esc1/Esc2 → PNG/TIF) ───
OLD_TH = '''<th class="col-esc1" title="Sobrescreve o escopo 1 do modelo (deixe vazio = usa o do modelo)">Esc1</th>
                            <th class="col-esc2" title="Sobrescreve o escopo 2 do modelo (deixe vazio = usa o do modelo)">Esc2</th>'''
NEW_TH = '''<th class="col-esc1" title="Variável disponível em PNG/GIF">PNG</th>
                            <th class="col-esc2" title="Variável disponível em TIF (GeoTIFF)">TIF</th>'''

# ─── (3) makeVarRow: trocar inputs por checkboxes ───
OLD_ROW = '''            <td class="col-esc1"><input data-vrow="${idx}" data-vfield="escopo1" value="${escAttr(v.escopo1)}" placeholder="(modelo)"></td>
            <td class="col-esc2"><input data-vrow="${idx}" data-vfield="escopo2" value="${escAttr(v.escopo2)}" placeholder="(modelo)"></td>'''
NEW_ROW = '''            <td class="col-esc1" style="text-align:center"><input type="checkbox" data-vrow="${idx}" data-vfield="disp_png" ${v.disp_png === false ? '' : 'checked'}></td>
            <td class="col-esc2" style="text-align:center"><input type="checkbox" data-vrow="${idx}" data-vfield="disp_tif" ${v.disp_tif === true ? 'checked' : ''}></td>'''

# ─── (4) renderConfigPane: popular novos campos ───
OLD_RENDER = '''        document.getElementById('cfgUrlPath').value = m.url_path || '';
        document.getElementById('cfgFileName').value = m.file_name || '';'''
NEW_RENDER = '''        document.getElementById('cfgUrlPath').value = m.url_path || '';
        document.getElementById('cfgFileName').value = m.file_name || '';
        // Novos: disponibilidade e templates TIF
        const cbPng = document.getElementById('cfgTemPng');
        const cbTif = document.getElementById('cfgTemTif');
        cbPng.checked = (m.tem_png !== false);  // default true
        cbTif.checked = !!m.tem_tif;
        const extTifSel = document.getElementById('cfgExtensaoTif');
        if (extTifSel) extTifSel.value = m.extensao_tif || '.tif';
        const sameUrl = document.getElementById('cfgSameUrlForTif');
        const sameName = document.getElementById('cfgSameNameForTif');
        sameUrl.checked = (m.same_url_for_tif !== false);  // default true
        sameName.checked = (m.same_name_for_tif !== false);
        document.getElementById('cfgUrlPathTif').value = m.url_path_tif || '';
        document.getElementById('cfgFileNameTif').value = m.file_name_tif || '';
        // Aplicar visibilidade dos campos TIF (hide quando "same...")
        function updTifVis() {
            const showUrl = !sameUrl.checked;
            const showNm = !sameName.checked;
            document.getElementById('cfgUrlPathTif').style.display = showUrl ? '' : 'none';
            document.getElementById('cfgFileNameTif').style.display = showNm ? '' : 'none';
        }
        sameUrl.onchange = updTifVis;
        sameName.onchange = updTifVis;
        updTifVis();'''

# ─── (5) syncCurrentPaneToDraft: salvar novos campos ───
OLD_SYNC = '''        m.url_path = document.getElementById('cfgUrlPath').value;
        m.file_name = document.getElementById('cfgFileName').value;'''
NEW_SYNC = '''        m.url_path = document.getElementById('cfgUrlPath').value;
        m.file_name = document.getElementById('cfgFileName').value;
        m.tem_png = !!document.getElementById('cfgTemPng').checked;
        m.tem_tif = !!document.getElementById('cfgTemTif').checked;
        m.extensao_tif = document.getElementById('cfgExtensaoTif').value || '.tif';
        m.same_url_for_tif = !!document.getElementById('cfgSameUrlForTif').checked;
        m.same_name_for_tif = !!document.getElementById('cfgSameNameForTif').checked;
        m.url_path_tif = document.getElementById('cfgUrlPathTif').value;
        m.file_name_tif = document.getElementById('cfgFileNameTif').value;'''

# ─── (6) Salvamento da row: tratar checkboxes ───
OLD_ROWSAVE = '''        rows.forEach(tr => {
            const inputs = tr.querySelectorAll('input[data-vfield]');
            const v = {};
            inputs.forEach(inp => {
                let val = inp.value;
                if (inp.dataset.vfield === 'frequencia') {
                    const nf = Number(val);
                    val = (isFinite(nf) && nf >= 0) ? nf : 1;  // 0 = observação / análise / reanálise
                } else if (inp.dataset.vfield === 'horizonte') {
                    val = Math.max(1, Number(val) || 1);
                }
                if (inp.dataset.vfield === 'escopo1' || inp.dataset.vfield === 'escopo2') {
                    val = String(val).trim();
                }
                v[inp.dataset.vfield] = val;
            });
            if (v.id && String(v.id).trim()) newVars.push(v);
        });'''
NEW_ROWSAVE = '''        rows.forEach(tr => {
            const inputs = tr.querySelectorAll('input[data-vfield]');
            const v = {};
            inputs.forEach(inp => {
                let val;
                if (inp.type === 'checkbox') {
                    val = !!inp.checked;
                } else {
                    val = inp.value;
                    if (inp.dataset.vfield === 'frequencia') {
                        const nf = Number(val);
                        val = (isFinite(nf) && nf >= 0) ? nf : 1;
                    } else if (inp.dataset.vfield === 'horizonte') {
                        val = Math.max(1, Number(val) || 1);
                    }
                }
                v[inp.dataset.vfield] = val;
            });
            if (v.id && String(v.id).trim()) newVars.push(v);
        });'''

# ─── (7) addVarRow defaults: incluir disp_png/disp_tif ───
OLD_ADD = '''    function addVarRow() {
        const tbody = document.getElementById('varTableBody');
        const idx = tbody.querySelectorAll('tr').length;
        const v = { id: '', label: '', unidade: '', arquivo: '', frequencia: 1, horizonte: 120 };'''
NEW_ADD = '''    function addVarRow() {
        const tbody = document.getElementById('varTableBody');
        const idx = tbody.querySelectorAll('tr').length;
        const v = { id: '', label: '', unidade: '', arquivo: '', frequencia: 1, horizonte: 120, disp_png: true, disp_tif: false };'''

# ─── (8) gtLoadFromState: usar url_path_tif/file_name_tif quando disponíveis ───
OLD_LOAD = '''        const passo = getEffectivePasso(0);
        let url;
        try {
            url = montarURL({ modelo: s.modelo, data: s.data, variavel: s.variavel, passo });
        } catch (e) {
            const info = document.getElementById('gtInfo');
            if (info) info.textContent = 'Erro ao montar URL: ' + (e && e.message);
            return;
        }
        // Se o modelo não é GeoTIFF nativo, deriva a URL substituindo a extensão
        if (!SisMOM_GeoTIFF.isGeoTiffModel(m)) {
            const derived = gtDeriveTifUrl(url);
            if (derived === url) {
                const info = document.getElementById('gtInfo');
                if (info) info.textContent = 'Não foi possível derivar URL .tif (extensão não reconhecida): ' + url;
                return;
            }
            url = derived;
        }'''
NEW_LOAD = '''        const passo = getEffectivePasso(0);
        let url;
        try {
            // Se o modelo tem rota TIF própria, usa essa; senão deriva do PNG
            const hasOwnTifRoute = (m.url_path_tif && !m.same_url_for_tif) || (m.file_name_tif && !m.same_name_for_tif);
            if (hasOwnTifRoute) {
                const mTif = Object.assign({}, m, {
                    url_path: m.same_url_for_tif ? m.url_path : (m.url_path_tif || m.url_path),
                    file_name: m.same_name_for_tif ? m.file_name : (m.file_name_tif || m.file_name),
                    extensao: m.extensao_tif || '.tif'
                });
                // Substituir temporariamente o modelo no map global e montar URL
                const orig = modelos[s.modelo];
                modelos[s.modelo] = mTif;
                try { url = montarURL({ modelo: s.modelo, data: s.data, variavel: s.variavel, passo }); }
                finally { modelos[s.modelo] = orig; }
            } else {
                url = montarURL({ modelo: s.modelo, data: s.data, variavel: s.variavel, passo });
                if (!SisMOM_GeoTIFF.isGeoTiffModel(m)) {
                    const derived = gtDeriveTifUrl(url);
                    if (derived === url) {
                        const info = document.getElementById('gtInfo');
                        if (info) info.textContent = 'Não foi possível derivar URL .tif (extensão não reconhecida): ' + url;
                        return;
                    }
                    url = derived;
                }
            }
        } catch (e) {
            const info = document.getElementById('gtInfo');
            if (info) info.textContent = 'Erro ao montar URL: ' + (e && e.message);
            return;
        }'''

# ─── (9) Filtrar modelos no select da toolbar GeoTIFF ───
OLD_POP_MOD = '''    function gtPopulateModeloSelect() {
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
    }'''
NEW_POP_MOD = '''    function gtPopulateModeloSelect() {
        const sel = document.getElementById('gtModeloSel');
        if (!sel) return;
        const prev = sel.value;
        const opts = [];
        for (const id of Object.keys(modelos)) {
            const m = modelos[id];
            if (!m) continue;
            // Só mostra modelos disponíveis em TIF (default false; se nunca configurado, aceita derivação)
            const hasTif = !!m.tem_tif || (m.tem_tif !== false && !m.tem_png); // legacy: se nem PNG nem TIF setados, aceita
            if (m.tem_tif === false) continue;
            if (m.tem_png === true && m.tem_tif === false) continue;  // só PNG → não aparece no GeoTIFF
            const protec = m.requires2FA ? ' 🔒' : '';
            opts.push('<option value="' + id + '">' + (m.nome || id) + protec + '</option>');
        }
        sel.innerHTML = opts.join('');
        if (prev && sel.querySelector('option[value="' + prev + '"]')) sel.value = prev;
    }'''

# ─── (10) Filtrar variáveis no select da toolbar (só disp_tif=true) ───
OLD_POP_VAR = '''    function gtPopulateVariavelSelect(modeloId) {
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
    }'''
NEW_POP_VAR = '''    function gtPopulateVariavelSelect(modeloId) {
        const sel = document.getElementById('gtVariavelSel');
        if (!sel) return;
        const m = modelos[modeloId];
        const prev = sel.value;
        const opts = [];
        if (m && Array.isArray(m.variaveis)) {
            for (const v of m.variaveis) {
                // Filtrar: var só aparece no GeoTIFF se disp_tif !== false (default true se modelo é só TIF)
                if (v.disp_tif === false) continue;
                const lbl = (v.label || v.id) + (v.unidade ? ' (' + v.unidade + ')' : '');
                opts.push('<option value="' + v.id + '">' + lbl + '</option>');
            }
        }
        sel.innerHTML = opts.join('');
        if (prev && sel.querySelector('option[value="' + prev + '"]')) sel.value = prev;
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'cfgTemPng' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_FORM,    NEW_FORM,    'form modal')
    src = rep(src, OLD_TH,      NEW_TH,      'thead vars')
    src = rep(src, OLD_ROW,     NEW_ROW,     'row vars')
    src = rep(src, OLD_RENDER,  NEW_RENDER,  'renderConfigPane')
    src = rep(src, OLD_SYNC,    NEW_SYNC,    'syncToDraft')
    src = rep(src, OLD_ROWSAVE, NEW_ROWSAVE, 'row save checkboxes')
    src = rep(src, OLD_ADD,     NEW_ADD,     'addVarRow defaults')
    src = rep(src, OLD_LOAD,    NEW_LOAD,    'gtLoadFromState routes')
    src = rep(src, OLD_POP_MOD, NEW_POP_MOD, 'filter modelos')
    src = rep(src, OLD_POP_VAR, NEW_POP_VAR, 'filter variaveis')

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
