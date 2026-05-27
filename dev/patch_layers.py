#!/usr/bin/env python3
"""
Patch: sobreposição de camadas extras (GeoTIFF e GeoJSON).
- Estende SisMOM_Map para múltiplos raster overlays (overlays[]) + GeoJSON com id
- UI: linha 'Camadas extras' com botão '+ Adicionar...' e chips de camadas
- gtExtraLayers[]: cada camada {id, type, name, visible, opacity, decoded|data, paleta, color}
- File picker aceita .tif/.tiff/.geojson/.json; detecção pelo nome
- Extras aparecem no mapa Mercator. No canvas raster (sem mapa), só a camada base.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1) SisMOM_Map: estender estado e API ───
# Substitui "overlay: null, extraLayers: []," → "overlay: null, overlays: [], extraLayers: [],"
OLD_STATE = '''            overlay: null, extraLayers: [],'''
NEW_STATE = '''            overlay: null, overlays: [], extraLayers: [],'''

# drawRaster: depois de desenhar self.overlay, itera sobre self.overlays
OLD_DRAW_RASTER = '''        function drawRaster() {
            if (!self.overlay) return;
            const { bbox, bitmap, opacity } = self.overlay;
            if (!bitmap || !bbox) return;
            const ctx = self.ctx;
            const x0 = lonToX(bbox.minX), x1 = lonToX(bbox.maxX);
            const y0 = latToY(bbox.maxY), y1 = latToY(bbox.minY);
            ctx.save();
            ctx.globalAlpha = (opacity == null ? 0.85 : opacity);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(bitmap, x0, y0, x1 - x0, y1 - y0);
            ctx.restore();
            ctx.strokeStyle = self.style.bbox;
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 3]);
            ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
            ctx.setLineDash([]);
        }'''
NEW_DRAW_RASTER = '''        function _drawOneRaster(o, drawBox) {
            if (!o || !o.bitmap || !o.bbox) return;
            const ctx = self.ctx;
            const x0 = lonToX(o.bbox.minX), x1 = lonToX(o.bbox.maxX);
            const y0 = latToY(o.bbox.maxY), y1 = latToY(o.bbox.minY);
            ctx.save();
            ctx.globalAlpha = (o.opacity == null ? 0.85 : o.opacity);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(o.bitmap, x0, y0, x1 - x0, y1 - y0);
            ctx.restore();
            if (drawBox) {
                ctx.strokeStyle = self.style.bbox;
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 3]);
                ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
                ctx.setLineDash([]);
            }
        }
        function drawRaster() {
            // Camadas raster extras primeiro (abaixo da base)
            for (const o of self.overlays) {
                if (o.visible === false) continue;
                _drawOneRaster(o, false);
            }
            // Camada base (primária) por cima
            _drawOneRaster(self.overlay, true);
        }'''

# Adicionar setRasterOverlay e novas funções addOverlay/removeOverlay
OLD_API = '''        async function setRasterOverlay(imageDataOrBitmap, bbox, opacity) {
            let bmp = imageDataOrBitmap;
            if (bmp && typeof ImageData !== 'undefined' && bmp instanceof ImageData) {
                bmp = await createImageBitmap(bmp);
            }
            self.overlay = { bitmap: bmp, bbox, opacity: (opacity == null ? 0.85 : opacity) };
            draw();
        }
        function clearOverlay() { self.overlay = null; draw(); }
        function setOpacity(o) { if (self.overlay) { self.overlay.opacity = o; draw(); } }
        function addGeoJSON(data, style) {
            self.extraLayers.push({ type: 'geojson', data, style: style || { stroke: '#4dd0e1', lineWidth: 0.8 } });
            draw();
        }
        function clearGeoJSON() { self.extraLayers = []; draw(); }'''
NEW_API = '''        async function setRasterOverlay(imageDataOrBitmap, bbox, opacity) {
            let bmp = imageDataOrBitmap;
            if (bmp && typeof ImageData !== 'undefined' && bmp instanceof ImageData) {
                bmp = await createImageBitmap(bmp);
            }
            self.overlay = { bitmap: bmp, bbox, opacity: (opacity == null ? 0.85 : opacity) };
            draw();
        }
        function clearOverlay() { self.overlay = null; draw(); }
        function setOpacity(o) { if (self.overlay) { self.overlay.opacity = o; draw(); } }
        async function addRasterOverlay(id, imageDataOrBitmap, bbox, opacity) {
            let bmp = imageDataOrBitmap;
            if (bmp && typeof ImageData !== 'undefined' && bmp instanceof ImageData) {
                bmp = await createImageBitmap(bmp);
            }
            // Substitui se já existe id
            const i = self.overlays.findIndex(o => o.id === id);
            const entry = { id, bitmap: bmp, bbox, opacity: (opacity == null ? 0.7 : opacity), visible: true };
            if (i >= 0) self.overlays[i] = entry; else self.overlays.push(entry);
            draw();
        }
        function removeRasterOverlay(id) {
            self.overlays = self.overlays.filter(o => o.id !== id);
            draw();
        }
        function setOverlayVisible(id, v) {
            const o = self.overlays.find(x => x.id === id);
            if (o) { o.visible = !!v; draw(); }
        }
        function setOverlayOpacity(id, op) {
            const o = self.overlays.find(x => x.id === id);
            if (o) { o.opacity = op; draw(); }
        }
        function addGeoJSON(data, style, id) {
            const entry = { type: 'geojson', data, style: style || { stroke: '#4dd0e1', lineWidth: 0.8 }, id };
            const i = id ? self.extraLayers.findIndex(l => l.id === id) : -1;
            if (i >= 0) self.extraLayers[i] = entry; else self.extraLayers.push(entry);
            draw();
        }
        function removeGeoJSON(id) {
            self.extraLayers = self.extraLayers.filter(l => l.id !== id);
            draw();
        }
        function setGeoJSONVisible(id, v) {
            const l = self.extraLayers.find(x => x.id === id);
            if (l) { l.visible = !!v; draw(); }
        }
        function clearGeoJSON() { self.extraLayers = []; draw(); }'''

# Atualizar drawGeoJSON para respeitar visible
OLD_DRAW_GJ = '''            for (const layer of self.extraLayers) {
                if (layer.type === 'geojson') drawGeoJSON(layer.data, layer.style || {});
            }'''
NEW_DRAW_GJ = '''            for (const layer of self.extraLayers) {
                if (layer.visible === false) continue;
                if (layer.type === 'geojson') drawGeoJSON(layer.data, layer.style || {});
            }'''

# Estender retorno do SisMOM_Map
OLD_RETURN = '''        return {
            setViewport, fitTo, setRasterOverlay, clearOverlay, setOpacity,
            addGeoJSON, clearGeoJSON,
            setTileProvider, setProjection, setAttributionElement,
            redraw: draw,
            setStyle(s) { Object.assign(self.style, s); draw(); },
            onCursor(fn) { self.onCursor = fn; },
            destroy() { ro.disconnect(); self.tileCache.clear(); }
        };'''
NEW_RETURN = '''        return {
            setViewport, fitTo, setRasterOverlay, clearOverlay, setOpacity,
            addRasterOverlay, removeRasterOverlay, setOverlayVisible, setOverlayOpacity,
            addGeoJSON, removeGeoJSON, setGeoJSONVisible, clearGeoJSON,
            setTileProvider, setProjection, setAttributionElement,
            redraw: draw,
            setStyle(s) { Object.assign(self.style, s); draw(); },
            onCursor(fn) { self.onCursor = fn; },
            destroy() { ro.disconnect(); self.tileCache.clear(); }
        };'''

# ─── (2) UI HTML: nova linha 'Camadas extras' antes da colorbar ───
OLD_UI_BEFORE_CB = '''            <canvas id="gtColorbar" style="width:100%;height:38px;display:block;margin:6px 0 8px;border-radius:4px"></canvas>'''
NEW_UI_BEFORE_CB = '''            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
                <span style="color:var(--text-muted,#aab);font-size:12px">Camadas extras:</span>
                <input type="file" id="gtExtraFile" accept=".tif,.tiff,.geojson,.json" style="display:none">
                <button class="btn btn-ghost" id="btnGtAddLayer" type="button">+ Adicionar GeoTIFF/GeoJSON…</button>
                <span id="gtLayerChips" style="display:inline-flex;gap:6px;flex-wrap:wrap;align-items:center"></span>
            </div>
            <canvas id="gtColorbar" style="width:100%;height:38px;display:block;margin:6px 0 8px;border-radius:4px"></canvas>'''

# ─── (3) Bloco JS: gerência de camadas extras (insere antes de gtSampleAtLatLon) ───
OLD_ANCHOR_FN = '''    function gtSampleAtLatLon(lat, lon) {'''
NEW_ANCHOR_FN = '''    /* ─── Camadas extras (GeoTIFF / GeoJSON) ─── */
    const gtExtraLayers = [];   // [{id,type,name,visible,opacity,decoded?,data?,paleta?,color?}]
    let gtLayerSeq = 0;
    const GJ_PALETTE = ['#4dd0e1','#ffeb3b','#ff9800','#e91e63','#9c27b0','#3f51b5','#8bc34a','#f44336'];

    function gtLayerEnsureMap() {
        // Garante que o mapa esteja inicializado (já ativa toggle de mapa)
        const tg = document.getElementById('gtShowMap');
        if (tg && !tg.checked && !tg.disabled) { tg.checked = true; gtToggleMapUI(); }
    }

    async function gtAddExtraLayerFromFile(file) {
        const name = file.name || ('camada' + (++gtLayerSeq));
        const lower = name.toLowerCase();
        const id = 'ext_' + (++gtLayerSeq) + '_' + Date.now();
        if (lower.endsWith('.tif') || lower.endsWith('.tiff')) {
            const ab = await file.arrayBuffer();
            const decoded = await SisMOM_GeoTIFF.decodeTIFF(ab);
            const layer = { id, type: 'geotiff', name, visible: true, opacity: 0.7,
                decoded, paleta: (document.getElementById('gtPaleta')||{}).value || 'viridis' };
            gtExtraLayers.push(layer);
            gtLayerEnsureMap();
            await gtLayerPushToMap(layer);
        } else if (lower.endsWith('.geojson') || lower.endsWith('.json')) {
            const txt = await file.text();
            let data;
            try { data = JSON.parse(txt); } catch (e) { throw new Error('JSON inválido: ' + e.message); }
            const color = GJ_PALETTE[gtExtraLayers.filter(l => l.type==='geojson').length % GJ_PALETTE.length];
            const layer = { id, type: 'geojson', name, visible: true, opacity: 1, data, color };
            gtExtraLayers.push(layer);
            gtLayerEnsureMap();
            gtLayerPushToMap(layer);
        } else {
            throw new Error('Extensão não reconhecida: ' + name);
        }
        gtRenderLayerChips();
    }

    async function gtLayerPushToMap(layer) {
        if (!_gtMap) return;
        if (layer.type === 'geotiff') {
            const d = layer.decoded;
            const img = SisMOM_GeoTIFF.aplicarPaleta(d, { paleta: layer.paleta });
            await _gtMap.addRasterOverlay(layer.id, img, d.bbox, layer.opacity);
            _gtMap.setOverlayVisible(layer.id, layer.visible);
        } else if (layer.type === 'geojson') {
            _gtMap.addGeoJSON(layer.data, { stroke: layer.color, lineWidth: 1.2 }, layer.id);
            _gtMap.setGeoJSONVisible(layer.id, layer.visible);
        }
    }

    async function gtSyncAllExtrasToMap() {
        if (!_gtMap) return;
        for (const layer of gtExtraLayers) await gtLayerPushToMap(layer);
    }

    function gtRemoveExtraLayer(id) {
        const i = gtExtraLayers.findIndex(l => l.id === id);
        if (i < 0) return;
        const l = gtExtraLayers[i];
        gtExtraLayers.splice(i, 1);
        if (_gtMap) {
            if (l.type === 'geotiff') _gtMap.removeRasterOverlay(l.id);
            else if (l.type === 'geojson') _gtMap.removeGeoJSON(l.id);
        }
        gtRenderLayerChips();
    }

    function gtToggleExtraLayer(id) {
        const l = gtExtraLayers.find(x => x.id === id);
        if (!l) return;
        l.visible = !l.visible;
        if (_gtMap) {
            if (l.type === 'geotiff') _gtMap.setOverlayVisible(l.id, l.visible);
            else if (l.type === 'geojson') _gtMap.setGeoJSONVisible(l.id, l.visible);
        }
        gtRenderLayerChips();
    }

    function gtRenderLayerChips() {
        const container = document.getElementById('gtLayerChips');
        if (!container) return;
        container.innerHTML = '';
        for (const l of gtExtraLayers) {
            const chip = document.createElement('span');
            chip.style.cssText = 'display:inline-flex;align-items:center;gap:4px;padding:2px 6px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);border-radius:12px;font-size:11px;color:var(--text,#cbd6e6)';
            const dot = document.createElement('span');
            dot.style.cssText = 'width:8px;height:8px;border-radius:50%;background:' + (l.type==='geojson' ? l.color : '#4caf50');
            const label = document.createElement('span');
            label.textContent = l.name;
            label.style.maxWidth = '160px';
            label.style.overflow = 'hidden';
            label.style.textOverflow = 'ellipsis';
            label.style.whiteSpace = 'nowrap';
            label.style.opacity = l.visible ? '1' : '0.45';
            const eye = document.createElement('button');
            eye.type = 'button';
            eye.title = l.visible ? 'Ocultar' : 'Mostrar';
            eye.textContent = l.visible ? '👁' : '⊘';
            eye.style.cssText = 'background:none;border:0;color:inherit;cursor:pointer;padding:0 2px;font-size:12px';
            eye.addEventListener('click', () => gtToggleExtraLayer(l.id));
            const x = document.createElement('button');
            x.type = 'button';
            x.title = 'Remover';
            x.textContent = '×';
            x.style.cssText = 'background:none;border:0;color:#f88;cursor:pointer;padding:0 2px;font-size:14px;font-weight:700';
            x.addEventListener('click', () => gtRemoveExtraLayer(l.id));
            chip.appendChild(dot); chip.appendChild(label); chip.appendChild(eye); chip.appendChild(x);
            container.appendChild(chip);
        }
    }

    function gtSampleAtLatLon(lat, lon) {'''

# ─── (4) Listeners em bindGeoTIFFUI ───
OLD_BIND_END = '''        // Mouse sobre o canvas raster (modo sem mapa): também sample o valor
        const rcv = document.getElementById('gtCanvas');'''
NEW_BIND_END = '''        // Camadas extras
        const btnAdd = document.getElementById('btnGtAddLayer');
        const extraFile = document.getElementById('gtExtraFile');
        if (btnAdd && extraFile) {
            btnAdd.addEventListener('click', () => extraFile.click());
            extraFile.addEventListener('change', async (e) => {
                for (const f of (e.target.files || [])) {
                    try { await gtAddExtraLayerFromFile(f); }
                    catch (err) { alert('Erro ao adicionar camada: ' + ((err && err.message) || err)); }
                }
                extraFile.value = '';
            });
        }
        // Mouse sobre o canvas raster (modo sem mapa): também sample o valor
        const rcv = document.getElementById('gtCanvas');'''

# ─── (5) Sync extras quando o mapa é criado pela primeira vez ───
OLD_MAP_INIT = '''            _gtMap.setTileProvider(initialProvider);
            _gtMap.fitTo(gtLastDecoded.bbox);
        }'''
NEW_MAP_INIT = '''            _gtMap.setTileProvider(initialProvider);
            _gtMap.fitTo(gtLastDecoded.bbox);
            // Empurra camadas extras já adicionadas para o mapa
            gtSyncAllExtrasToMap();
        }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtExtraLayers' in src:
        print(f"[{path.name}] já patcheado (gtExtraLayers); pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_STATE, NEW_STATE, 'state overlays')
    src = rep(src, OLD_DRAW_RASTER, NEW_DRAW_RASTER, 'drawRaster')
    src = rep(src, OLD_API, NEW_API, 'map api')
    src = rep(src, OLD_DRAW_GJ, NEW_DRAW_GJ, 'drawGeoJSON visible')
    src = rep(src, OLD_RETURN, NEW_RETURN, 'map return')
    src = rep(src, OLD_UI_BEFORE_CB, NEW_UI_BEFORE_CB, 'ui layers row')
    src = rep(src, OLD_ANCHOR_FN, NEW_ANCHOR_FN, 'extra layers block')
    src = rep(src, OLD_BIND_END, NEW_BIND_END, 'bind add layer')
    src = rep(src, OLD_MAP_INIT, NEW_MAP_INIT, 'sync extras on map init')

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
        print('OK - ' + str(len(a)) + ' bytes em ambas')

if __name__ == '__main__':
    main()
