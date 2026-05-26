#!/usr/bin/env python3
"""
Patch que adiciona camada de mapa-base custom ao modal local de GeoTIFF.
- Injeta módulo SisMOM_Map (canvas, sem dependência externa) dentro do IIFE.
- Substitui o container do canvas no modal por: toggle "Mostrar mapa" +
  slider opacidade + HUD coordenadas + canvas raster + canvas mapa.
- Registra listeners em bindGeoTIFFUI.
Aplica nas duas cópias do HTML em lockstep. Idempotente.

NÃO mexe nos painéis Mi (essa parte fica para iteração B).
"""

import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']
MAP_JS = (ROOT / 'dev' / 'map_module.js').read_text(encoding='utf-8')

# ─── (1) Bloco do módulo SisMOM_Map + integração (injetado dentro do IIFE) ───
MAP_BLOCK = r"""
    /* ╔═══════════════════════════════════════════════════════════╗
       ║  Mapa-base custom (canvas, sem dependência externa).      ║
       ║  Costa da América do Sul + cidades + grade lat/lon.       ║
       ║  Overlay do raster GeoTIFF sincronizado com viewport.     ║
       ╚═══════════════════════════════════════════════════════════╝ */
__MAP_MODULE_BODY__

    /* ─── Integração do mapa com o modal GeoTIFF local ─── */
    let _gtMap = null;
    async function gtSyncMapOverlay() {
        const toggle = document.getElementById('gtShowMap');
        if (!toggle || !toggle.checked) return;
        if (!gtLastDecoded || !gtLastDecoded.bbox) return;
        if (!_gtMap) {
            const mapCv = document.getElementById('gtMapCanvas');
            _gtMap = SisMOM_Map(mapCv);
            _gtMap.onCursor(p => {
                const el = document.getElementById('gtCoord');
                if (el) el.textContent = `${p.lat.toFixed(3)}°, ${p.lon.toFixed(3)}°`;
            });
            _gtMap.fitTo(gtLastDecoded.bbox);
        }
        const pal = document.getElementById('gtPaleta').value;
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
    }
    function gtToggleMapUI() {
        const toggle = document.getElementById('gtShowMap');
        const rasterCv = document.getElementById('gtCanvas');
        const mapCv = document.getElementById('gtMapCanvas');
        const opLabel = document.getElementById('gtOpacityLabel');
        const show = !!(toggle && toggle.checked);
        if (rasterCv) rasterCv.style.display = show ? 'none' : '';
        if (mapCv)    mapCv.style.display    = show ? '' : 'none';
        if (opLabel)  opLabel.style.display  = show ? 'inline-flex' : 'none';
        if (show) gtSyncMapOverlay();
    }
    function gtUpdateMapToggleEnabled() {
        const toggle = document.getElementById('gtShowMap');
        if (!toggle) return;
        const hasGeo = !!(gtLastDecoded && gtLastDecoded.bbox);
        toggle.disabled = !hasGeo;
        toggle.title = hasGeo ? 'Sobrepor o raster a um mapa-base'
                              : 'GeoTIFF sem georreferência (tags 33550/33922 ausentes)';
        if (!hasGeo && toggle.checked) {
            toggle.checked = false;
            gtToggleMapUI();
        }
    }
""".replace('__MAP_MODULE_BODY__', MAP_JS.rstrip())

# ─── (2) Substituir o container do canvas no modal por o novo (com mapa) ───
CANVAS_OLD = '''            <div style="display:flex;justify-content:center;background:var(--bg-elev,#0e1622);padding:8px;border-radius:6px;overflow:auto;max-height:60vh">
                <canvas id="gtCanvas" style="max-width:100%;image-rendering:pixelated"></canvas>
            </div>'''
CANVAS_NEW = '''            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
                <label style="display:inline-flex;align-items:center;gap:6px"><input type="checkbox" id="gtShowMap" disabled> Mostrar mapa</label>
                <label id="gtOpacityLabel" style="display:none;align-items:center;gap:6px;color:var(--text-muted,#aab)">Opacidade <input type="range" id="gtOpacity" min="0" max="100" value="85" style="width:140px"></label>
                <span id="gtCoord" style="font-family:ui-monospace,monospace;color:var(--text-muted,#aab);margin-left:auto">—</span>
            </div>
            <div style="display:flex;justify-content:center;background:var(--bg-elev,#0e1622);padding:8px;border-radius:6px;overflow:hidden;max-height:60vh;position:relative">
                <canvas id="gtCanvas" style="max-width:100%;image-rendering:pixelated"></canvas>
                <canvas id="gtMapCanvas" style="display:none;width:100%;height:60vh;cursor:grab"></canvas>
            </div>'''

# ─── (3) Registrar listeners em bindGeoTIFFUI ───
BIND_OLD = '''        document.getElementById('gtMin').addEventListener('change', gtRenderar);
        document.getElementById('gtMax').addEventListener('change', gtRenderar);
    }'''
BIND_NEW = '''        document.getElementById('gtMin').addEventListener('change', gtRenderar);
        document.getElementById('gtMax').addEventListener('change', gtRenderar);
        // Mapa
        const tm = document.getElementById('gtShowMap');
        if (tm) tm.addEventListener('change', gtToggleMapUI);
        const op = document.getElementById('gtOpacity');
        if (op) op.addEventListener('input', () => {
            if (_gtMap) _gtMap.setOpacity(parseInt(op.value, 10) / 100);
        });
    }'''

# ─── (4) Após carregar arquivo: habilitar/desabilitar toggle e refit ───
RENDER_OLD = '''                gtAtualizarInfoEMinMax(gtLastDecoded);
                gtRenderar();'''
RENDER_NEW = '''                gtAtualizarInfoEMinMax(gtLastDecoded);
                gtRenderar();
                gtUpdateMapToggleEnabled();
                if (_gtMap && gtLastDecoded.bbox) _gtMap.fitTo(gtLastDecoded.bbox);
                gtSyncMapOverlay();'''

# ─── (5) Quando paleta/min/max mudarem, refletir no mapa também ───
GTRENDERAR_OLD = '''    function gtRenderar() {
        if (!gtLastDecoded) return;'''
GTRENDERAR_NEW = '''    function gtRenderar() {
        if (!gtLastDecoded) return;
        // Espelha no mapa-base se ativo
        try { gtSyncMapOverlay(); } catch (_) {}'''

# ─── (6) Anchor de injeção (mesmo do GeoTIFF, agora já consumido — usar outro) ───
# Após o patch anterior, "if (document.readyState === 'loading')" ainda é único.
INJECT_ANCHOR = "    if (document.readyState === 'loading') {"


def patch_file(path: Path, dry: bool = False) -> bool:
    src = path.read_text(encoding='utf-8')
    original = src

    if 'SisMOM_Map' in src:
        print(f"[{path.name}] já patcheado (contém 'SisMOM_Map'); pulando.")
        return False

    def replace_unique(haystack: str, old: str, new: str, label: str) -> str:
        n = haystack.count(old)
        if n != 1:
            raise RuntimeError(f"[{path.name}] anchor '{label}' aparece {n}× (esperado 1)")
        return haystack.replace(old, new, 1)

    src = replace_unique(src, CANVAS_OLD, CANVAS_NEW, 'canvas container')
    src = replace_unique(src, BIND_OLD, BIND_NEW, 'bind listeners')
    src = replace_unique(src, RENDER_OLD, RENDER_NEW, 'after file picker')
    src = replace_unique(src, GTRENDERAR_OLD, GTRENDERAR_NEW, 'gtRenderar hook')
    src = replace_unique(src, INJECT_ANCHOR, MAP_BLOCK + '\n' + INJECT_ANCHOR, 'inject map module')

    if src == original:
        print(f"[{path.name}] nenhuma mudança")
        return False
    if dry:
        print(f"[{path.name}] dry-run: +{len(src) - len(original)} bytes")
        return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok ({len(original)} -> {len(src)} bytes, +{len(src) - len(original)})")
    return True


def main():
    dry = '--dry-run' in sys.argv
    changed = 0
    for f in FILES:
        if not f.exists():
            print(f"[ERRO] arquivo ausente: {f}")
            sys.exit(2)
        if patch_file(f, dry=dry):
            changed += 1
    if changed == len(FILES) and not dry:
        a = FILES[0].read_bytes(); b = FILES[1].read_bytes()
        if a != b:
            print("[ERRO] as duas cópias divergem após patch!")
            sys.exit(3)
        print(f"OK — {len(a)} bytes em ambas, idênticas")


if __name__ == '__main__':
    main()
