#!/usr/bin/env python3
"""
Patch: permitir definir valores UNDEF manualmente + clipping min/max visível.
- Estende aplicarPaleta para aceitar nodataExtras[], clipBelow, clipAbove
- Estende gtSampleAtLatLon e gtSampleAtCanvasXY para consultar os mesmos filtros
- Adiciona nova linha de controles no modal: input UNDEF + clipBelow + clipAbove
- gtMaskOpts global, parseMaskFromUI, gtRecomputeMinMaxAuto
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1) aplicarPaleta: aceitar nodataExtras/clipBelow/clipAbove ───
OLD_APLICAR = '''        function aplicarPaleta(decoded, opts) {
            const { width, height, data, nodata } = decoded;
            const palName = (opts && opts.paleta) || 'viridis';
            const pal = GT_PALETTES[palName] || GT_PALETTES.viridis;
            const min = (opts && opts.min != null) ? opts.min : decoded.min;
            const max = (opts && opts.max != null) ? opts.max : decoded.max;
            const range = (max - min) || 1;
            const flipY = opts && opts.flipY === true;
            const N = width * height;
            const rgba = new Uint8ClampedArray(N * 4);
            for (let i = 0; i < N; i++) {
                const v = data[i];
                const isNoData = (!isFinite(v)) || (nodata != null && v === nodata);
                let dst = i;
                if (flipY) { const y = (i / width) | 0; const x = i - y * width; dst = (height - 1 - y) * width + x; }
                const o = dst * 4;
                if (isNoData) { rgba[o]=0; rgba[o+1]=0; rgba[o+2]=0; rgba[o+3]=0; }
                else {
                    let t = (v - min) / range;
                    if (t < 0) t = 0; else if (t > 1) t = 1;
                    const idx = (t * 255) | 0;
                    rgba[o]     = pal[idx * 3];
                    rgba[o + 1] = pal[idx * 3 + 1];
                    rgba[o + 2] = pal[idx * 3 + 2];
                    rgba[o + 3] = 255;
                }
            }
            return new ImageData(rgba, width, height);
        }'''
NEW_APLICAR = '''        function aplicarPaleta(decoded, opts) {
            const { width, height, data, nodata } = decoded;
            const palName = (opts && opts.paleta) || 'viridis';
            const pal = GT_PALETTES[palName] || GT_PALETTES.viridis;
            const min = (opts && opts.min != null) ? opts.min : decoded.min;
            const max = (opts && opts.max != null) ? opts.max : decoded.max;
            const range = (max - min) || 1;
            const flipY = opts && opts.flipY === true;
            // Filtros adicionais
            const extras = (opts && Array.isArray(opts.nodataExtras)) ? opts.nodataExtras : null;
            const nExtras = extras ? extras.length : 0;
            const clipBelow = (opts && opts.clipBelow != null && isFinite(opts.clipBelow)) ? opts.clipBelow : null;
            const clipAbove = (opts && opts.clipAbove != null && isFinite(opts.clipAbove)) ? opts.clipAbove : null;
            const N = width * height;
            const rgba = new Uint8ClampedArray(N * 4);
            for (let i = 0; i < N; i++) {
                const v = data[i];
                let masked = (!isFinite(v)) || (nodata != null && v === nodata);
                if (!masked && nExtras) { for (let k = 0; k < nExtras; k++) if (v === extras[k]) { masked = true; break; } }
                if (!masked && clipBelow != null && v < clipBelow) masked = true;
                if (!masked && clipAbove != null && v > clipAbove) masked = true;
                let dst = i;
                if (flipY) { const y = (i / width) | 0; const x = i - y * width; dst = (height - 1 - y) * width + x; }
                const o = dst * 4;
                if (masked) { rgba[o]=0; rgba[o+1]=0; rgba[o+2]=0; rgba[o+3]=0; }
                else {
                    let t = (v - min) / range;
                    if (t < 0) t = 0; else if (t > 1) t = 1;
                    const idx = (t * 255) | 0;
                    rgba[o]     = pal[idx * 3];
                    rgba[o + 1] = pal[idx * 3 + 1];
                    rgba[o + 2] = pal[idx * 3 + 2];
                    rgba[o + 3] = 255;
                }
            }
            return new ImageData(rgba, width, height);
        }'''

# ─── (2) Adicionar gtMaskOpts + helpers antes de gtSampleAtLatLon ───
OLD_HELPER_ANCHOR = '''    function gtSampleAtLatLon(lat, lon) {'''
NEW_HELPER_BLOCK = '''    /* ─── Filtros NoData / clipping definidos pelo usuário ─── */
    let gtMaskOpts = { extras: null, clipBelow: null, clipAbove: null };
    function gtParseMaskFromUI() {
        const undefIn = document.getElementById('gtUndef');
        const minIn   = document.getElementById('gtClipMin');
        const maxIn   = document.getElementById('gtClipMax');
        const extras = [];
        if (undefIn && undefIn.value.trim()) {
            for (const tok of undefIn.value.split(/[,;\\s]+/)) {
                const x = parseFloat(tok);
                if (isFinite(x)) extras.push(x);
            }
        }
        const cb = minIn && minIn.value.trim() !== '' ? parseFloat(minIn.value) : null;
        const ca = maxIn && maxIn.value.trim() !== '' ? parseFloat(maxIn.value) : null;
        gtMaskOpts = {
            extras: extras.length ? extras : null,
            clipBelow: (cb != null && isFinite(cb)) ? cb : null,
            clipAbove: (ca != null && isFinite(ca)) ? ca : null
        };
        return gtMaskOpts;
    }
    function gtIsMasked(v) {
        if (!gtLastDecoded) return false;
        if (!isFinite(v)) return true;
        if (gtLastDecoded.nodata != null && v === gtLastDecoded.nodata) return true;
        if (gtMaskOpts.extras) { for (const e of gtMaskOpts.extras) if (v === e) return true; }
        if (gtMaskOpts.clipBelow != null && v < gtMaskOpts.clipBelow) return true;
        if (gtMaskOpts.clipAbove != null && v > gtMaskOpts.clipAbove) return true;
        return false;
    }
    function gtRecomputeMinMaxAuto() {
        // Só se 'Auto' estiver ativo (não em modo Editar)
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        if (!minEl || !maxEl || minEl.hasAttribute('data-editing')) return;
        if (!gtLastDecoded) return;
        let mn = Infinity, mx = -Infinity;
        const d = gtLastDecoded.data;
        for (let i = 0; i < d.length; i++) {
            const v = d[i];
            if (gtIsMasked(v)) continue;
            if (v < mn) mn = v;
            if (v > mx) mx = v;
        }
        if (!isFinite(mn)) { mn = 0; mx = 1; }
        gtLastDecoded.min = mn; gtLastDecoded.max = mx;
        minEl.value = mn; maxEl.value = mx;
    }
    function gtSampleAtLatLon(lat, lon) {'''

# ─── (3) Atualizar gtSampleAtLatLon para usar gtIsMasked ───
OLD_SAMPLE_LL = '''        const v = data[row * width + col];
        if (!isFinite(v) || (nodata != null && v === nodata)) return { valid: true, value: null, noData: true };
        return { valid: true, value: v, col, row };
    }'''
NEW_SAMPLE_LL = '''        const v = data[row * width + col];
        if (gtIsMasked(v)) return { valid: true, value: null, noData: true };
        return { valid: true, value: v, col, row };
    }'''

# ─── (4) gtSampleAtCanvasXY (caminho sem bbox) ───
OLD_SAMPLE_XY = '''        if (!isFinite(v) || (gtLastDecoded.nodata != null && v === gtLastDecoded.nodata)) {
            el.textContent = `col ${col}, row ${row} · NoData`;
        } else {'''
NEW_SAMPLE_XY = '''        if (gtIsMasked(v)) {
            el.textContent = `col ${col}, row ${row} · NoData`;
        } else {'''

# ─── (5) gtRenderar e gtSyncMapOverlay: passar mask opts ───
OLD_RENDER = '''    function gtRenderar() {
        if (!gtLastDecoded) return;
        // Espelha no mapa-base se ativo
        try { gtSyncMapOverlay(); } catch (_) {}
        const pal = document.getElementById('gtPaleta').value;
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        const editing = minEl.hasAttribute('data-editing');
        const opts = { paleta: pal };
        if (editing) {
            const mn = parseFloat(minEl.value);
            const mx = parseFloat(maxEl.value);
            if (isFinite(mn) && isFinite(mx) && mx > mn) { opts.min = mn; opts.max = mx; }
        }
        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);'''
NEW_RENDER = '''    function gtRenderar() {
        if (!gtLastDecoded) return;
        // Espelha no mapa-base se ativo
        try { gtSyncMapOverlay(); } catch (_) {}
        const pal = document.getElementById('gtPaleta').value;
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        const editing = minEl.hasAttribute('data-editing');
        const opts = { paleta: pal };
        if (editing) {
            const mn = parseFloat(minEl.value);
            const mx = parseFloat(maxEl.value);
            if (isFinite(mn) && isFinite(mx) && mx > mn) { opts.min = mn; opts.max = mx; }
        }
        if (gtMaskOpts.extras)    opts.nodataExtras = gtMaskOpts.extras;
        if (gtMaskOpts.clipBelow != null) opts.clipBelow = gtMaskOpts.clipBelow;
        if (gtMaskOpts.clipAbove != null) opts.clipAbove = gtMaskOpts.clipAbove;
        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);'''

OLD_SYNC = '''        const pal = document.getElementById('gtPaleta').value;
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        const editing = minEl.hasAttribute('data-editing');
        const opts = { paleta: pal };
        if (editing) {
            const mn = parseFloat(minEl.value), mx = parseFloat(maxEl.value);
            if (isFinite(mn) && isFinite(mx) && mx > mn) { opts.min = mn; opts.max = mx; }
        }
        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);
        const op = (parseInt(document.getElementById('gtOpacity').value, 10) || 85) / 100;
        await _gtMap.setRasterOverlay(img, gtLastDecoded.bbox, op);
    }'''
NEW_SYNC = '''        const pal = document.getElementById('gtPaleta').value;
        const minEl = document.getElementById('gtMin');
        const maxEl = document.getElementById('gtMax');
        const editing = minEl.hasAttribute('data-editing');
        const opts = { paleta: pal };
        if (editing) {
            const mn = parseFloat(minEl.value), mx = parseFloat(maxEl.value);
            if (isFinite(mn) && isFinite(mx) && mx > mn) { opts.min = mn; opts.max = mx; }
        }
        if (gtMaskOpts.extras)    opts.nodataExtras = gtMaskOpts.extras;
        if (gtMaskOpts.clipBelow != null) opts.clipBelow = gtMaskOpts.clipBelow;
        if (gtMaskOpts.clipAbove != null) opts.clipAbove = gtMaskOpts.clipAbove;
        const img = SisMOM_GeoTIFF.aplicarPaleta(gtLastDecoded, opts);
        const op = (parseInt(document.getElementById('gtOpacity').value, 10) || 85) / 100;
        await _gtMap.setRasterOverlay(img, gtLastDecoded.bbox, op);
    }'''

# ─── (6) UI: nova linha de controles no modal ───
OLD_UI = '''            <div id="gtInfo" style="color:var(--text-muted);font-size:12px;margin-bottom:8px;min-height:1em">Abra um arquivo .tif/.tiff para visualizar.</div>'''
NEW_UI = '''            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
                <label style="display:inline-flex;align-items:center;gap:6px">UNDEF: <input type="text" id="gtUndef" placeholder="ex: -999, -9999" style="width:160px"></label>
                <label style="display:inline-flex;align-items:center;gap:6px">Clip ≥: <input type="number" id="gtClipMin" step="any" placeholder="—" style="width:110px"></label>
                <label style="display:inline-flex;align-items:center;gap:6px">Clip ≤: <input type="number" id="gtClipMax" step="any" placeholder="—" style="width:110px"></label>
                <button class="btn btn-ghost" id="btnGtUndefClear" type="button" title="Limpar filtros">Limpar</button>
            </div>
            <div id="gtInfo" style="color:var(--text-muted);font-size:12px;margin-bottom:8px;min-height:1em">Abra um arquivo .tif/.tiff para visualizar.</div>'''

# ─── (7) Ligar listeners em bindGeoTIFFUI ───
OLD_BIND = '''        const rcv = document.getElementById('gtCanvas');
        if (rcv) {
            rcv.addEventListener('mousemove', (e) => gtSampleAtCanvasXY(rcv, e));
            rcv.addEventListener('mouseleave', gtClearCoord);
        }
    }'''
NEW_BIND = '''        const rcv = document.getElementById('gtCanvas');
        if (rcv) {
            rcv.addEventListener('mousemove', (e) => gtSampleAtCanvasXY(rcv, e));
            rcv.addEventListener('mouseleave', gtClearCoord);
        }
        // Filtros UNDEF / clip
        function applyMaskAndRender() {
            gtParseMaskFromUI();
            gtRecomputeMinMaxAuto();
            gtRenderar();
        }
        ['gtUndef','gtClipMin','gtClipMax'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', applyMaskAndRender);
        });
        const btnClr = document.getElementById('btnGtUndefClear');
        if (btnClr) btnClr.addEventListener('click', () => {
            ['gtUndef','gtClipMin','gtClipMax'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = '';
            });
            applyMaskAndRender();
        });
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtMaskOpts' in src:
        print(f"[{path.name}] já patcheado (gtMaskOpts); pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_APLICAR, NEW_APLICAR, 'aplicarPaleta')
    src = rep(src, OLD_HELPER_ANCHOR, NEW_HELPER_BLOCK, 'gtSample helper anchor')
    src = rep(src, OLD_SAMPLE_LL, NEW_SAMPLE_LL, 'sample latlon')
    src = rep(src, OLD_SAMPLE_XY, NEW_SAMPLE_XY, 'sample canvas xy')
    src = rep(src, OLD_RENDER, NEW_RENDER, 'gtRenderar opts')
    src = rep(src, OLD_SYNC, NEW_SYNC, 'gtSync opts')
    src = rep(src, OLD_UI, NEW_UI, 'UI undef')
    src = rep(src, OLD_BIND, NEW_BIND, 'bind undef listeners')

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
