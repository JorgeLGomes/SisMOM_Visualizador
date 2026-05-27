#!/usr/bin/env python3
"""
Patch: multi-painel no modo GeoTIFF.
- No modo gtiff, mantém os painéis Mi visíveis (não esconde mainPNG, não
  mostra mainGT dashboard). Layouts 1/2/3/4 funcionam.
- carregarImagem deriva URL para TIF quando appMode=gtiff (já chama
  carregarGeoTIFFParaSlot que existe). Aplica também a regra de
  url_path_tif/file_name_tif se configurado.
- Dashboard de 1 painel (modal #modalGeoTIFF inline) deixa de ser ativado
  por padrão; continua acessível via botão "Abrir GeoTIFF local" do header.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) setAppMode: não esconde mainPNG no modo gtiff; não mostra mainGT
OLD_SET = '''        if (mode === 'gtiff') {
            if (modal && mainGT && modal.parentNode !== mainGT) {
                _gtModalParent = modal.parentNode;
                mainGT.appendChild(modal);
            }
            if (modal) { modal.classList.add('inline'); modal.classList.add('open'); }
            if (mainPNG) mainPNG.style.display = 'none';
            if (mainGT)  mainGT.style.display  = '';
            try { gtBindToolbar(); gtSyncToolbarFromState(); } catch (_) {}
            gtLoadFromState().catch(() => {});
        } else {
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
    }'''
NEW_SET = '''        // Sempre devolve o modal para fora do mainGT (volta a ser modal pop-up)
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

# (2) carregarImagem: também intercepta quando appMode='gtiff'
OLD_CARREGAR = '''    function carregarImagem(slotIdx, url) {
        // GeoTIFF: usa fluxo dedicado (fetch+decode+paleta) se o modelo for .tif/.tiff
        const _gtS = state.slots[slotIdx];
        if (_gtS && typeof SisMOM_GeoTIFF !== 'undefined' && SisMOM_GeoTIFF.isGeoTiffModel(modelos[_gtS.modelo])) {
            return carregarGeoTIFFParaSlot(slotIdx, url);
        }'''
NEW_CARREGAR = '''    function carregarImagem(slotIdx, url) {
        // GeoTIFF: usa fluxo dedicado se o modelo é nativo TIF OU se appMode='gtiff'
        const _gtS = state.slots[slotIdx];
        const _gtM = _gtS && modelos[_gtS.modelo];
        const _isNativeGt = _gtM && typeof SisMOM_GeoTIFF !== 'undefined' && SisMOM_GeoTIFF.isGeoTiffModel(_gtM);
        const _isGtMode = (typeof appMode !== 'undefined' && appMode === 'gtiff');
        if (_gtS && (_isNativeGt || _isGtMode)) {
            // Se o modo gtiff e o modelo NÃO é nativo TIF, deriva a URL
            let urlTif = url;
            if (_isGtMode && !_isNativeGt) {
                try {
                    // Se o modelo tem rota TIF própria, monta com substituição temporária do modelo
                    const hasOwnTifRoute = _gtM && ((_gtM.url_path_tif && !_gtM.same_url_for_tif) || (_gtM.file_name_tif && !_gtM.same_name_for_tif));
                    if (hasOwnTifRoute) {
                        const mTif = Object.assign({}, _gtM, {
                            url_path: _gtM.same_url_for_tif ? _gtM.url_path : (_gtM.url_path_tif || _gtM.url_path),
                            file_name: _gtM.same_name_for_tif ? _gtM.file_name : (_gtM.file_name_tif || _gtM.file_name),
                            extensao: _gtM.extensao_tif || '.tif'
                        });
                        const orig = modelos[_gtS.modelo];
                        modelos[_gtS.modelo] = mTif;
                        try {
                            const passo = getEffectivePasso(slotIdx);
                            urlTif = montarURL({ modelo: _gtS.modelo, data: _gtS.data, variavel: _gtS.variavel, passo });
                        } finally { modelos[_gtS.modelo] = orig; }
                    } else {
                        urlTif = (typeof gtDeriveTifUrl === 'function') ? gtDeriveTifUrl(url) : url;
                    }
                } catch (e) { console.error('deriva tif para slot', slotIdx, e); }
            }
            return carregarGeoTIFFParaSlot(slotIdx, urlTif);
        }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_isGtMode' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_SET,      NEW_SET,      'setAppMode multi-panel')
    src = rep(src, OLD_CARREGAR, NEW_CARREGAR, 'carregarImagem gtiff')

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
