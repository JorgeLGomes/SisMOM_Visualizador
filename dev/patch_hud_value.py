#!/usr/bin/env python3
"""
Patch: HUD do valor do raster sob o cursor.
- Adiciona função gtSampleAtLatLon(lat, lon) que devolve {value, valid, noData}
- Estende o onCursor do mapa para exibir 'lat, lon · valor = X' (ou '· NoData')
- Adiciona listeners de mousemove/mouseleave no #gtCanvas (modo sem mapa)
Aplica nas duas cópias do HTML. Idempotente (detecta gtSampleAtLatLon).
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) Substitui o onCursor simples por versão que sample o valor
OLD_ONCURSOR = '''            _gtMap.onCursor(p => {
                const el = document.getElementById('gtCoord');
                if (el) el.textContent = `${p.lat.toFixed(3)}°, ${p.lon.toFixed(3)}°`;
            });'''
NEW_ONCURSOR = '''            _gtMap.onCursor(p => {
                gtAtualizarCoord(p.lat, p.lon);
            });'''

# (2) Insere as funções helper antes de gtToggleMapUI
OLD_HELPER_ANCHOR = '''    function gtToggleMapUI() {'''
NEW_HELPER_BLOCK = '''    function gtSampleAtLatLon(lat, lon) {
        if (!gtLastDecoded || !gtLastDecoded.bbox) return { valid: false };
        const { bbox, width, height, data, nodata } = gtLastDecoded;
        if (lon < bbox.minX || lon > bbox.maxX || lat < bbox.minY || lat > bbox.maxY) return { valid: false };
        const col = Math.min(width - 1,  Math.max(0, Math.floor((lon - bbox.minX) / (bbox.maxX - bbox.minX) * width)));
        const row = Math.min(height - 1, Math.max(0, Math.floor((bbox.maxY - lat) / (bbox.maxY - bbox.minY) * height)));
        const v = data[row * width + col];
        if (!isFinite(v) || (nodata != null && v === nodata)) return { valid: true, value: null, noData: true };
        return { valid: true, value: v, col, row };
    }
    function gtAtualizarCoord(lat, lon) {
        const el = document.getElementById('gtCoord');
        if (!el) return;
        const coord = `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;
        const samp = gtSampleAtLatLon(lat, lon);
        if (!samp.valid) { el.textContent = coord; return; }
        if (samp.noData) { el.textContent = `${coord} · NoData`; return; }
        // Formatação adaptativa: número grande/pequeno usa exponencial
        const v = samp.value;
        const abs = Math.abs(v);
        const fmt = (abs !== 0 && (abs < 1e-3 || abs >= 1e6)) ? v.toExponential(3) : v.toFixed(3);
        el.textContent = `${coord} · valor = ${fmt}`;
    }
    function gtSampleAtCanvasXY(canvas, e) {
        if (!gtLastDecoded) return;
        const rect = canvas.getBoundingClientRect();
        const fx = (e.clientX - rect.left) / rect.width;
        const fy = (e.clientY - rect.top)  / rect.height;
        if (fx < 0 || fx > 1 || fy < 0 || fy > 1) return;
        // Se há bbox, converte para lat/lon e reaproveita o pipeline; senão mostra col/row + valor
        if (gtLastDecoded.bbox) {
            const lon = gtLastDecoded.bbox.minX + fx * (gtLastDecoded.bbox.maxX - gtLastDecoded.bbox.minX);
            const lat = gtLastDecoded.bbox.maxY - fy * (gtLastDecoded.bbox.maxY - gtLastDecoded.bbox.minY);
            gtAtualizarCoord(lat, lon);
            return;
        }
        const col = Math.floor(fx * gtLastDecoded.width);
        const row = Math.floor(fy * gtLastDecoded.height);
        const v = gtLastDecoded.data[row * gtLastDecoded.width + col];
        const el = document.getElementById('gtCoord');
        if (!el) return;
        if (!isFinite(v) || (gtLastDecoded.nodata != null && v === gtLastDecoded.nodata)) {
            el.textContent = `col ${col}, row ${row} · NoData`;
        } else {
            const abs = Math.abs(v);
            const fmt = (abs !== 0 && (abs < 1e-3 || abs >= 1e6)) ? v.toExponential(3) : v.toFixed(3);
            el.textContent = `col ${col}, row ${row} · valor = ${fmt}`;
        }
    }
    function gtClearCoord() {
        const el = document.getElementById('gtCoord');
        if (el) el.textContent = '—';
    }
    function gtToggleMapUI() {'''

# (3) Em bindGeoTIFFUI, adiciona listeners ao gtCanvas para o modo sem mapa
OLD_BIND_TAIL = '''        const tp = document.getElementById('gtTileProvider');
        if (tp) tp.addEventListener('change', () => {
            if (_gtMap) _gtMap.setTileProvider(tp.value);
        });
    }'''
NEW_BIND_TAIL = '''        const tp = document.getElementById('gtTileProvider');
        if (tp) tp.addEventListener('change', () => {
            if (_gtMap) _gtMap.setTileProvider(tp.value);
        });
        // Mouse sobre o canvas raster (modo sem mapa): também sample o valor
        const rcv = document.getElementById('gtCanvas');
        if (rcv) {
            rcv.addEventListener('mousemove', (e) => gtSampleAtCanvasXY(rcv, e));
            rcv.addEventListener('mouseleave', gtClearCoord);
        }
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtSampleAtLatLon' in src:
        print(f"[{path.name}] já patcheado (gtSampleAtLatLon); pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c} (esperado 1)")
        return h.replace(o, n, 1)

    src = rep(src, OLD_ONCURSOR, NEW_ONCURSOR, 'onCursor')
    src = rep(src, OLD_HELPER_ANCHOR, NEW_HELPER_BLOCK, 'helpers')
    src = rep(src, OLD_BIND_TAIL, NEW_BIND_TAIL, 'bind raster mousemove')

    if src == original: return False
    if dry:
        print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(original)} -> {len(src)}, {len(src)-len(original):+d})")
    return True


def main():
    dry = '--dry-run' in sys.argv
    changed = 0
    for f in FILES:
        if not f.exists(): print('falta', f); sys.exit(2)
        if patch_file(f, dry=dry): changed += 1
    if changed == len(FILES) and not dry:
        a = FILES[0].read_bytes(); b = FILES[1].read_bytes()
        if a != b: print('divergem'); sys.exit(3)
        print(f"OK — {len(a)} bytes em ambas")

if __name__ == '__main__':
    main()
