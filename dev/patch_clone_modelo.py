#!/usr/bin/env python3
"""
Patch: botão "Clonar modelo" no modal de configuração.

Adiciona botão entre "Remover modelo" e "Restaurar padrão". Quando
clicado:
- Sincroniza pane atual ao draft (preserva edições em andamento).
- Faz deep clone do modelo da aba ativa.
- Gera novo id "{idOriginal}_copia" (ou _copia2, _copia3... se já existe).
- Nome do clone vira "{nomeOriginal} (cópia)".
- Adiciona como nova aba e ativa-a para edição.
- Variáveis e templates TIF (url_path_tif, file_name_tif, flags) são todos
  copiados.

Inclui no enable/disable de _configEditing (só funciona em modo edição).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) HTML: adicionar botão entre Remover e Restaurar
OLD_HTML = '''                <button class="btn btn-ghost" id="btnDelModel" title="Remover este modelo">Remover modelo</button>
                <button class="btn btn-ghost" id="btnConfigReset" title="Restaurar configuração padrão de fábrica">Restaurar padrão</button>'''
NEW_HTML = '''                <button class="btn btn-ghost" id="btnDelModel" title="Remover este modelo">Remover modelo</button>
                <button class="btn btn-ghost" id="btnCloneModel" title="Clonar este modelo (duplicar como novo)">Clonar modelo</button>
                <button class="btn btn-ghost" id="btnConfigReset" title="Restaurar configuração padrão de fábrica">Restaurar padrão</button>'''

# (2) JS: adicionar função cloneActiveModel após delActiveModel
OLD_JS_FN = '''    async function delActiveModel() {
        if (!(await gateSensitive('Remover modelo'))) return;
        if (!configActiveId) return;
        if (Object.keys(configDraft).length <= 1) {
            showToast('Não é possível remover o último modelo');
            return;
        }
        if (!confirm(`Remover o modelo "${configDraft[configActiveId].nome || configActiveId}"?`)) return;
        delete configDraft[configActiveId];
        configActiveId = Object.keys(configDraft)[0];
        renderConfigTabs();
        renderConfigPane(configActiveId);
    }'''
NEW_JS_FN = '''    async function delActiveModel() {
        if (!(await gateSensitive('Remover modelo'))) return;
        if (!configActiveId) return;
        if (Object.keys(configDraft).length <= 1) {
            showToast('Não é possível remover o último modelo');
            return;
        }
        if (!confirm(`Remover o modelo "${configDraft[configActiveId].nome || configActiveId}"?`)) return;
        delete configDraft[configActiveId];
        configActiveId = Object.keys(configDraft)[0];
        renderConfigTabs();
        renderConfigPane(configActiveId);
    }
    function cloneActiveModel() {
        if (!configActiveId) return;
        // Sincroniza o pane atual no draft pra não perder edições não salvas
        try { syncCurrentPaneToDraft(); } catch (_) {}
        const orig = configDraft[configActiveId];
        if (!orig) return;
        // Deep clone via JSON (modelos não têm funções nem refs circulares)
        const clone = JSON.parse(JSON.stringify(orig));
        clone.nome = (orig.nome || configActiveId) + ' (cópia)';
        // Gera novo id único, prefixando com o original
        let baseId = configActiveId + '_copia';
        let newId = baseId;
        let n = 2;
        while (configDraft[newId]) { newId = baseId + n; n++; }
        configDraft[newId] = clone;
        configActiveId = newId;
        renderConfigTabs();
        renderConfigPane(newId);
        showToast('Modelo clonado como "' + clone.nome + '"');
    }'''

# (3) JS: bind do listener no bindEvents
OLD_JS_BIND = "$('btnDelModel').addEventListener('click', delActiveModel);"
NEW_JS_BIND = """$('btnDelModel').addEventListener('click', delActiveModel);
        $('btnCloneModel').addEventListener('click', cloneActiveModel);"""

# (4) Adicionar btnCloneModel na lista de elementos controlados por _configEditing
OLD_LOCK = "['btnConfigSave','btnDelModel','btnConfigReset','btnConfigImport','btnAddVar'].forEach(id => {"
NEW_LOCK = "['btnConfigSave','btnDelModel','btnCloneModel','btnConfigReset','btnConfigImport','btnAddVar'].forEach(id => {"


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'cloneActiveModel' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HTML,    NEW_HTML,    'html botao Clonar')
    src = rep(src, OLD_JS_FN,   NEW_JS_FN,   'js cloneActiveModel')
    src = rep(src, OLD_JS_BIND, NEW_JS_BIND, 'js bind listener')
    src = rep(src, OLD_LOCK,    NEW_LOCK,    'js lock list')
    # Bump build
    src = src.replace('20260528-0250-calc', '20260528-0300-clone')

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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0300-clone")

if __name__ == '__main__':
    main()
