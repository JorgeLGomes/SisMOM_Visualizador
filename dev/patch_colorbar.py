#!/usr/bin/env python3
"""
Patch: colorbar (barra de escala de cores) no modal local de GeoTIFF.
- <canvas id="gtColorbar"> entre a linha UNDEF/Clip e o div #gtInfo
- função gtDesenharColorbar() que pinta gradient da paleta corrente + ticks
- chamada em: gtRenderar, gtSyncMapOverlay (sucesso) e gtAtualizarInfoEMinMax
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) HTML: canvas da colorbar
OLD_HTML_INFO = '''            <div id="gtInfo" style="color:var(--text-muted);font-size:12px;margin-bottom:8px;min-height:1em">Abra um arquivo .tif/.tiff para visualizar.</div>'''
NEW_HTML_INFO = '''            <canvas id="gtColorbar" style="width:100%;height:38px;display:block;margin:6px 0 8px;border-radius:4px"></canvas>
            <div id="gtInfo" style="color:var(--text-muted);font-size:12px;margin-bottom:8px;min-height:1em">Abra um arquivo .tif/.tiff para visualizar.</div>'''

# (2) Função gtDesenharColorbar — insere antes de gtSampleAtLatLon (anchor que ainda é único)
OLD_ANCHOR = '''    function gtSampleAtLatLon(lat, lon) {'''
NEW_BLOCK = '''    function gtDesenharColorbar() {
        const cv = document.getElementById('gtColorbar');
        if (!cv) return;
        const ctx = cv.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const rect = cv.getBoundingClientRect();
        if (rect.width < 4) return;
        cv.width  = Math.round(rect.width * dpr);
        cv.height = Math.round(rect.height * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        const W = rect.width, H = rect.height;
        // Fundo
        ctx.fillStyle = 'rgba(255,255,255,0.04)';
        ctx.fillRect(0, 0, W, H);
        // Paleta corrente
        const palSel = document.getElementById('gtPaleta');
        const palName = (palSel && palSel.value) || 'viridis';
        const PAL = (typeof SisMOM_GeoTIFF !== 'undefined' && SisMOM_GeoTIFF.GT_PALETTES)
            ? (SisMOM_GeoTIFF.GT_PALETTES[palName] || SisMOM_GeoTIFF.GT_PALETTES.viridis)
            : null;
        if (!PAL) return;
        // Min/max correntes
        let mn = null, mx = null;
        const minEl = document.getElementById('gtMin'), maxEl = document.getElementById('gtMax');
        if (minEl && maxEl && minEl.value !== '' && maxEl.value !== '') {
            mn = parseFloat(minEl.value); mx = parseFloat(maxEl.value);
        } else if (gtLastDecoded) {
            mn = gtLastDecoded.min; mx = gtLastDecoded.max;
        }
        // Gradient (256 stops da paleta)
        const barTop = 2, barH = Math.max(8, Math.min(18, H - 18));
        const img = ctx.createImageData(Math.max(1, Math.round(W * dpr)), 1);
        const arr = img.data;
        for (let i = 0; i < img.width; i++) {
            const t = i / Math.max(1, img.width - 1);
            const idx = Math.min(255, Math.max(0, (t * 255) | 0));
            arr[i*4]   = PAL[idx*3];
            arr[i*4+1] = PAL[idx*3+1];
            arr[i*4+2] = PAL[idx*3+2];
            arr[i*4+3] = 255;
        }
        // Coloca a linha em um canvas off-screen pra esticar verticalmente
        const off = document.createElement('canvas');
        off.width = img.width; off.height = 1;
        off.getContext('2d').putImageData(img, 0, 0);
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(off, 0, barTop, W, barH);
        // Moldura
        ctx.strokeStyle = 'rgba(255,255,255,0.18)';
        ctx.lineWidth = 1;
        ctx.strokeRect(0.5, barTop + 0.5, W - 1, barH - 1);
        // Ticks (min/max + 3 intermediários)
        if (mn == null || mx == null || !isFinite(mn) || !isFinite(mx) || mx <= mn) return;
        ctx.fillStyle = 'rgba(220,230,245,0.9)';
        ctx.strokeStyle = 'rgba(220,230,245,0.6)';
        ctx.font = '10px ui-monospace, monospace';
        ctx.textBaseline = 'top';
        const labelsY = barTop + barH + 3;
        const fracs = [0, 0.25, 0.5, 0.75, 1];
        const fmt = (v) => {
            const a = Math.abs(v);
            return (a !== 0 && (a < 1e-3 || a >= 1e6)) ? v.toExponential(2) : v.toFixed(Math.abs(v) >= 100 ? 1 : 2);
        };
        for (const f of fracs) {
            const x = f * W;
            ctx.beginPath();
            ctx.moveTo(x, barTop + barH - 4);
            ctx.lineTo(x, barTop + barH + 2);
            ctx.stroke();
            const v = mn + f * (mx - mn);
            const label = fmt(v);
            const tw = ctx.measureText(label).width;
            let lx = x - tw / 2;
            if (lx < 1) lx = 1; else if (lx + tw > W - 1) lx = W - 1 - tw;
            ctx.fillText(label, lx, labelsY);
        }
    }
    function gtSampleAtLatLon(lat, lon) {'''

# (3) Chamadas: depois de gtRenderar pinta canvas; em gtAtualizarInfoEMinMax e gtSyncMapOverlay também
# Em gtRenderar — após desenhar no canvas raster
OLD_RENDER_TAIL = '''        const cv = document.getElementById('gtCanvas');
        cv.width = gtLastDecoded.width; cv.height = gtLastDecoded.height;
        cv.getContext('2d').putImageData(img, 0, 0);
    }'''
NEW_RENDER_TAIL = '''        const cv = document.getElementById('gtCanvas');
        cv.width = gtLastDecoded.width; cv.height = gtLastDecoded.height;
        cv.getContext('2d').putImageData(img, 0, 0);
        gtDesenharColorbar();
    }'''

# Em gtSyncMapOverlay — após setRasterOverlay
OLD_SYNC_TAIL = '''        await _gtMap.setRasterOverlay(img, gtLastDecoded.bbox, op);
    }'''
NEW_SYNC_TAIL = '''        await _gtMap.setRasterOverlay(img, gtLastDecoded.bbox, op);
        gtDesenharColorbar();
    }'''

# Em gtAtualizarInfoEMinMax — após atualizar info text (para refletir quando muda min/max via Auto/Editar)
OLD_INFO_TAIL = '''        if (!minEl.hasAttribute('data-editing')) {
            minEl.value = decoded.min;
            maxEl.value = decoded.max;
        }
    }'''
NEW_INFO_TAIL = '''        if (!minEl.hasAttribute('data-editing')) {
            minEl.value = decoded.min;
            maxEl.value = decoded.max;
        }
        gtDesenharColorbar();
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtDesenharColorbar' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HTML_INFO, NEW_HTML_INFO, 'html canvas colorbar')
    src = rep(src, OLD_ANCHOR, NEW_BLOCK, 'fn gtDesenharColorbar')
    src = rep(src, OLD_RENDER_TAIL, NEW_RENDER_TAIL, 'hook gtRenderar')
    src = rep(src, OLD_SYNC_TAIL, NEW_SYNC_TAIL, 'hook gtSync')
    src = rep(src, OLD_INFO_TAIL, NEW_INFO_TAIL, 'hook gtInfo')

    if src == original: return False
    if dry: print(f"[{path.name}] dry-run: {len(src)-len(original):+d} bytes"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(original)} -> {len(src)}, {len(src)-len(original):+d})")
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
        print(f"OK — {len(a)} bytes em ambas")

if __name__ == '__main__':
    main()
