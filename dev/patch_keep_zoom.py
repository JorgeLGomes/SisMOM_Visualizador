#!/usr/bin/env python3
"""
Patch: durante animação no modo GeoTIFF, gtLoadFromState chama
_gtMap.fitTo() a cada step, perdendo o zoom do usuário. Correção:
só re-fit se a bbox da nova camada mudou (modelo/variável diferente).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Adiciona helper _bboxEqual e variável _gtLastFitBbox antes de gtLoadFromState
OLD_ANCHOR = '''    async function gtLoadFromState() {'''
NEW_ANCHOR = '''    let _gtLastFitBbox = null;
    function _bboxEqual(a, b) {
        if (!a || !b) return a === b;
        const eps = 1e-6;
        return Math.abs(a.minX - b.minX) < eps && Math.abs(a.maxX - b.maxX) < eps
            && Math.abs(a.minY - b.minY) < eps && Math.abs(a.maxY - b.maxY) < eps;
    }
    async function gtLoadFromState() {'''

# (2) Em gtLoadFromState: só fitTo se bbox diferente
OLD_FIT_FTP = '''            if (typeof _gtMap !== 'undefined' && _gtMap && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);'''
NEW_FIT_FTP = '''            if (typeof _gtMap !== 'undefined' && _gtMap && gtLastDecoded.bbox && !_bboxEqual(gtLastDecoded.bbox, _gtLastFitBbox)) {
                _gtMap.fitTo(gtLastDecoded.bbox);
                _gtLastFitBbox = gtLastDecoded.bbox;
            }'''

# (3) Em file picker: também aplica a mesma lógica
OLD_FIT_FILE = '''                if (_gtMap && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);'''
NEW_FIT_FILE = '''                if (_gtMap && gtLastDecoded.bbox && !_bboxEqual(gtLastDecoded.bbox, _gtLastFitBbox)) {
                    _gtMap.fitTo(gtLastDecoded.bbox);
                    _gtLastFitBbox = gtLastDecoded.bbox;
                }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if '_gtLastFitBbox' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_ANCHOR,   NEW_ANCHOR,   'helpers')
    src = rep(src, OLD_FIT_FTP,  NEW_FIT_FTP,  'fit ftp guard')
    src = rep(src, OLD_FIT_FILE, NEW_FIT_FILE, 'fit file guard')

    if not src: return False
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
