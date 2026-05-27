#!/usr/bin/env python3
"""
Patch: no modo GeoTIFF, derivar a URL .tif automaticamente a partir do modelo,
mesmo que o modelo tenha extensão .png/.gif/.jpg/.jpeg. A animação por passos
(play/pause/step do header) continua reusando o estado existente.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''    async function gtLoadFromState() {
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
        }'''
NEW = '''    function gtDeriveTifUrl(url) {
        // Substitui a extensão final png/gif/jpg/jpeg por tif, preservando query string.
        return String(url || '').replace(/\\.(png|gif|jpe?g)(\\?.*)?$/i, '.tif$2');
    }
    async function gtLoadFromState() {
        if (appMode !== 'gtiff') return;
        if (!state || !state.slots || !state.slots[0]) return;
        const s = state.slots[0];
        if (!s.data || !s.modelo || !s.variavel) return;
        const m = modelos[s.modelo];
        if (!m) {
            const info = document.getElementById('gtInfo');
            if (info) info.textContent = 'Modelo "' + s.modelo + '" não encontrado.';
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


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtDeriveTifUrl' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    c = src.count(OLD)
    if c != 1: raise RuntimeError(f"[{path.name}] anchor = {c}")
    src = src.replace(OLD, NEW, 1)
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
