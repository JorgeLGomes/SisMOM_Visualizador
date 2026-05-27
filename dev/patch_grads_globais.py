#!/usr/bin/env python3
"""
Patch: corrigir 2 bugs revelados pelo arquivo temp-0010 (1).tif (GrADS global).
 (1) Normalização de longitude 0..360 -> -180..180 estava aplicando por
     tiepoint isoladamente, quebrando GeoTIFFs globais com extremos
     (-181, 181). Agora só normaliza se TODAS as longitudes estão em [0, 360]
     E alguma > 180 (caso clássico GrADS-Pacífico).
 (2) Detecção heurística de NoData implícito: se um arquivo não tem
     GDAL_NODATA explícito mas o min calculado é absurdamente menor que max
     (|min - max| > 1e6), o valor extremo é tratado como NoData implícito,
     o min/max recalculados ignoram esses pixels, e o decoded.nodata é
     populado para que aplicarPaleta/gtSampleAtLatLon mascarem.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1+2) Bloco bbox + heurística de nodata implícito ───
OLD_BLOCK = '''            let bbox = null, scale = null;
            function _normLon(x) { return (x > 180) ? x - 360 : x; }
            if (tags[33550] && tags[33922]) {
                // Caso típico: 1 tiepoint + ModelPixelScale
                const sx = tags[33550][0], sy = tags[33550][1];
                const tp = tags[33922];
                const I = tp[0], J = tp[1];
                let X = tp[3]; const Y = tp[4];
                X = _normLon(X);
                const minX = X - I * sx;
                const maxY = Y + J * sy;
                const maxX = minX + width * sx;
                const minY = maxY - height * sy;
                bbox = { minX, minY, maxX, maxY };
                scale = { sx, sy };
            } else if (tags[33922] && tags[33922].length >= 6 && tags[33922].length % 6 === 0) {
                // Caso GrADS / multi-tiepoint sem ModelPixelScale:
                // pega min/max das longitudes/latitudes dos tiepoints (assume cantos do raster).
                const tp = tags[33922];
                let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
                for (let i = 0; i < tp.length; i += 6) {
                    const X = _normLon(tp[i + 3]);
                    const Y = tp[i + 4];
                    if (X < mnX) mnX = X; if (X > mxX) mxX = X;
                    if (Y < mnY) mnY = Y; if (Y > mxY) mxY = Y;
                }
                if (isFinite(mnX) && mxX > mnX && mxY > mnY) {
                    bbox = { minX: mnX, minY: mnY, maxX: mxX, maxY: mxY };
                }
            }'''
NEW_BLOCK = '''            let bbox = null, scale = null;
            // Heurística de normalização de longitude:
            // Só subtrai 360 se TODAS as longitudes do(s) tiepoint(s) estão em [0, 360]
            // E alguma > 180 (caso clássico GrADS-Pacífico). Se já tem negativas, mantém.
            function _shouldNormalizeLon(xs) {
                let anyNeg = false, anyOver180 = false;
                for (const x of xs) { if (x < 0) anyNeg = true; if (x > 180) anyOver180 = true; }
                return (!anyNeg && anyOver180);
            }
            if (tags[33550] && tags[33922]) {
                // Caso típico: 1 tiepoint + ModelPixelScale
                const sx = tags[33550][0], sy = tags[33550][1];
                const tp = tags[33922];
                const I = tp[0], J = tp[1];
                let X = tp[3]; const Y = tp[4];
                if (_shouldNormalizeLon([X, X + width * sx])) X -= 360;
                const minX = X - I * sx;
                const maxY = Y + J * sy;
                const maxX = minX + width * sx;
                const minY = maxY - height * sy;
                bbox = { minX, minY, maxX, maxY };
                scale = { sx, sy };
            } else if (tags[33922] && tags[33922].length >= 6 && tags[33922].length % 6 === 0) {
                // Caso GrADS / multi-tiepoint sem ModelPixelScale:
                const tp = tags[33922];
                const xs = []; for (let i = 0; i < tp.length; i += 6) xs.push(tp[i + 3]);
                const norm = _shouldNormalizeLon(xs);
                let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
                for (let i = 0; i < tp.length; i += 6) {
                    const X = norm ? (tp[i + 3] - 360) : tp[i + 3];
                    const Y = tp[i + 4];
                    if (X < mnX) mnX = X; if (X > mxX) mxX = X;
                    if (Y < mnY) mnY = Y; if (Y > mxY) mxY = Y;
                }
                if (isFinite(mnX) && mxX > mnX && mxY > mnY) {
                    bbox = { minX: mnX, minY: mnY, maxX: mxX, maxY: mxY };
                }
            }'''

# ─── (2) Heurística de NoData implícito ───
OLD_MIN_MAX = '''            let mn = Infinity, mx = -Infinity;
            for (let i = 0; i < N; i++) {
                const v = data[i];
                if (!isFinite(v)) continue;
                if (nodata != null && v === nodata) continue;
                if (v < mn) mn = v;
                if (v > mx) mx = v;
            }
            if (!isFinite(mn)) { mn = 0; mx = 1; }
            return { width, height, data, nodata, bbox, scale, min: mn, max: mx };'''
NEW_MIN_MAX = '''            let mn = Infinity, mx = -Infinity;
            for (let i = 0; i < N; i++) {
                const v = data[i];
                if (!isFinite(v)) continue;
                if (nodata != null && v === nodata) continue;
                if (v < mn) mn = v;
                if (v > mx) mx = v;
            }
            if (!isFinite(mn)) { mn = 0; mx = 1; }
            // Heurística: se min está absurdamente longe de max (diff > 1e6) e arquivo não tem
            // GDAL_NODATA explícito, trata o valor extremo como NoData implícito e recalcula.
            let effectiveNoData = nodata;
            if (nodata == null && mx - mn > 1e6) {
                const sentinel = (Math.abs(mn) > Math.abs(mx)) ? mn : mx;
                effectiveNoData = sentinel;
                mn = Infinity; mx = -Infinity;
                for (let i = 0; i < N; i++) {
                    const v = data[i];
                    if (!isFinite(v) || v === sentinel) continue;
                    if (v < mn) mn = v;
                    if (v > mx) mx = v;
                }
                if (!isFinite(mn)) { mn = 0; mx = 1; }
            }
            return { width, height, data, nodata: effectiveNoData, bbox, scale, min: mn, max: mx };'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if '_shouldNormalizeLon' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_BLOCK,   NEW_BLOCK,   'bbox normalize fix')
    src = rep(src, OLD_MIN_MAX, NEW_MIN_MAX, 'nodata heuristic')

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
