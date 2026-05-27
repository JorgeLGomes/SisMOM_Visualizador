#!/usr/bin/env python3
"""
Patch: detectar múltiplos valores sentinel + min/max robusto via percentis.
Arquivo Eta10_C00_PREC_2015020201.tif tem dois sentinels diferentes:
-3.4e+38 (= -FLT_MAX) e ~5.87e+9 (outro valor extremo). Meu detector
anterior só detectava um. Resultado: paleta com range absurdo, raster
todo na mesma cor.

Mudanças no decoder:
 (1) Loop iterativo de detecção (até 5 iterações ou range < 1e6).
     Cada iteração: pega extremo (mn ou mx) de maior |v| como sentinel.
     Armazena no array decoded.nodataExtras.
 (2) Fallback: se após 5 iterações o range ainda é absurdo, usa
     percentis 1%/99% de amostra (10k pixels) para min/max.
 (3) aplicarPaleta usa decoded.nodataExtras como fallback de opts.nodataExtras.
 (4) gtIsMasked consulta gtLastDecoded.nodataExtras.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Bloco min/max + nodata heurístico → loop iterativo + percentil fallback
OLD_BLOCK = '''            let mn = Infinity, mx = -Infinity;
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
NEW_BLOCK = '''            let mn = Infinity, mx = -Infinity;
            for (let i = 0; i < N; i++) {
                const v = data[i];
                if (!isFinite(v)) continue;
                if (nodata != null && v === nodata) continue;
                if (v < mn) mn = v;
                if (v > mx) mx = v;
            }
            if (!isFinite(mn)) { mn = 0; mx = 1; }
            // Detecção iterativa de múltiplos sentinels: enquanto o range é absurdo (>1e6),
            // pega o extremo (mn ou mx) com maior |v| como sentinel e recalcula.
            let effectiveNoData = nodata;
            const nodataExtras = [];
            for (let iter = 0; iter < 5; iter++) {
                if (!(mx - mn > 1e6)) break;
                const sentinel = (Math.abs(mn) > Math.abs(mx)) ? mn : mx;
                if (effectiveNoData == null) effectiveNoData = sentinel;
                else nodataExtras.push(sentinel);
                mn = Infinity; mx = -Infinity;
                for (let i = 0; i < N; i++) {
                    const v = data[i];
                    if (!isFinite(v)) continue;
                    if (v === effectiveNoData) continue;
                    let isExtra = false;
                    for (let k = 0; k < nodataExtras.length; k++) if (v === nodataExtras[k]) { isExtra = true; break; }
                    if (isExtra) continue;
                    if (v < mn) mn = v;
                    if (v > mx) mx = v;
                }
                if (!isFinite(mn)) { mn = 0; mx = 1; break; }
            }
            // Fallback: se ainda absurdo após 5 iterações, usa percentis 1%/99% de amostra.
            if (mx - mn > 1e6) {
                const step = Math.max(1, Math.floor(N / 10000));
                const sample = [];
                for (let i = 0; i < N; i += step) {
                    const v = data[i];
                    if (!isFinite(v)) continue;
                    if (v === effectiveNoData) continue;
                    let skip = false;
                    for (let k = 0; k < nodataExtras.length; k++) if (v === nodataExtras[k]) { skip = true; break; }
                    if (skip) continue;
                    sample.push(v);
                }
                if (sample.length >= 100) {
                    sample.sort((a, b) => a - b);
                    mn = sample[Math.floor(sample.length * 0.01)];
                    mx = sample[Math.floor(sample.length * 0.99)];
                }
            }
            return { width, height, data, nodata: effectiveNoData, nodataExtras: nodataExtras.length ? nodataExtras : null, bbox, scale, min: mn, max: mx };'''

# (2) aplicarPaleta: fallback para decoded.nodataExtras
OLD_AP_EX = '''            // Filtros adicionais
            const extras = (opts && Array.isArray(opts.nodataExtras)) ? opts.nodataExtras : null;
            const nExtras = extras ? extras.length : 0;'''
NEW_AP_EX = '''            // Filtros adicionais: junta opts.nodataExtras com decoded.nodataExtras (detectados)
            let extras = (opts && Array.isArray(opts.nodataExtras)) ? opts.nodataExtras.slice() : [];
            if (decoded.nodataExtras && Array.isArray(decoded.nodataExtras)) {
                for (const e of decoded.nodataExtras) if (extras.indexOf(e) < 0) extras.push(e);
            }
            if (extras.length === 0) extras = null;
            const nExtras = extras ? extras.length : 0;'''

# (3) gtIsMasked: consultar gtLastDecoded.nodataExtras também
OLD_MASK_FN = '''    function gtIsMasked(v) {
        if (!gtLastDecoded) return false;
        if (!isFinite(v)) return true;
        if (gtLastDecoded.nodata != null && v === gtLastDecoded.nodata) return true;
        if (gtMaskOpts.extras) { for (const e of gtMaskOpts.extras) if (v === e) return true; }
        if (gtMaskOpts.clipBelow != null && v < gtMaskOpts.clipBelow) return true;
        if (gtMaskOpts.clipAbove != null && v > gtMaskOpts.clipAbove) return true;
        return false;
    }'''
NEW_MASK_FN = '''    function gtIsMasked(v) {
        if (!gtLastDecoded) return false;
        if (!isFinite(v)) return true;
        if (gtLastDecoded.nodata != null && v === gtLastDecoded.nodata) return true;
        // Sentinels adicionais detectados pelo decoder
        if (gtLastDecoded.nodataExtras) {
            for (const e of gtLastDecoded.nodataExtras) if (v === e) return true;
        }
        if (gtMaskOpts.extras) { for (const e of gtMaskOpts.extras) if (v === e) return true; }
        if (gtMaskOpts.clipBelow != null && v < gtMaskOpts.clipBelow) return true;
        if (gtMaskOpts.clipAbove != null && v > gtMaskOpts.clipAbove) return true;
        return false;
    }'''

# (4) gtAtualizarInfoEMinMax: mostrar sentinels extras na info
OLD_INFO_BUILD = '''        if (decoded.nodata != null) parts.push(`nodata ${decoded.nodata}`);'''
NEW_INFO_BUILD = '''        if (decoded.nodata != null) parts.push(`nodata ${decoded.nodata}`);
        if (decoded.nodataExtras && decoded.nodataExtras.length) {
            parts.push(`+ sentinels: ${decoded.nodataExtras.map(v => v.toExponential(2)).join(', ')}`);
        }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'nodataExtras' in src and 'iteração' not in src and 'iter < 5' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if 'iter < 5' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_BLOCK,      NEW_BLOCK,      'multi sentinel loop')
    src = rep(src, OLD_AP_EX,      NEW_AP_EX,      'aplicarPaleta extras')
    src = rep(src, OLD_MASK_FN,    NEW_MASK_FN,    'gtIsMasked extras')
    src = rep(src, OLD_INFO_BUILD, NEW_INFO_BUILD, 'info sentinels')

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
