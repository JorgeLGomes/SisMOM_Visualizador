/* ============================================================
 * SisMOM Map v2 — mapa-base custom (canvas, sem dependência).
 *   - Projeções: Plate Carrée (offline) ou Web Mercator (com tiles)
 *   - Tile providers: OSM (ruas), Esri World Imagery (satélite),
 *     OpenTopoMap (topográfico). Tiles 256x256 XYZ, cache em RAM.
 *   - Costa da América do Sul (53 pts) + 17 capitais como fallback offline
 *   - Overlay do raster GeoTIFF (ImageBitmap, com bbox lat/lon)
 *   - Atribuição automática conforme provider ativo
 *   - Pan/zoom/wheel
 * Limitação consciente: tiles XYZ exigem Mercator (lat ±85°).
 * Em Plate Carrée não há tiles; é o modo "offline only".
 * ============================================================ */
(function (root) {
    'use strict';

    const SA_COAST = [
        [10.6,-61.0],[10.6,-66.9],[10.7,-71.6],[10.4,-75.5],[8.6,-77.0],
        [3.9,-77.0],[1.0,-79.7],[-2.2,-80.0],
        [-4.9,-81.3],[-9.0,-78.6],[-12.0,-77.0],[-17.0,-71.4],
        [-20.2,-70.1],[-23.7,-70.4],[-29.9,-71.3],[-33.0,-71.6],
        [-36.8,-73.0],[-41.5,-73.0],[-45.0,-73.8],[-50.0,-74.6],
        [-53.0,-71.0],[-55.5,-68.0],[-54.9,-65.0],
        [-52.0,-68.5],[-47.8,-65.9],[-42.8,-64.6],[-39.0,-62.0],
        [-38.0,-57.5],[-34.6,-58.5],[-34.9,-54.9],[-34.0,-53.5],
        [-32.0,-52.1],[-29.4,-49.7],[-27.5,-48.5],[-25.5,-48.0],
        [-23.0,-43.2],[-22.0,-41.0],[-20.0,-40.0],[-18.0,-39.5],
        [-13.0,-38.5],[-9.4,-35.5],[-8.0,-34.9],[-5.8,-35.2],
        [-3.7,-38.5],[-2.5,-44.0],[-1.5,-48.5],
        [0.5,-50.0],[4.4,-51.6],[5.5,-54.0],[5.2,-57.5],[6.8,-58.2],
        [8.0,-59.5],[8.5,-60.0]
    ];

    const CITIES = [
        ['São Paulo',-23.55,-46.63],['Rio de Janeiro',-22.91,-43.17],
        ['Brasília',-15.78,-47.93],['Salvador',-12.97,-38.51],
        ['Fortaleza',-3.73,-38.54],['Recife',-8.05,-34.88],
        ['Belém',-1.46,-48.49],['Manaus',-3.12,-60.02],
        ['Porto Alegre',-30.03,-51.23],['Curitiba',-25.43,-49.27],
        ['Belo Horizonte',-19.92,-43.94],['Buenos Aires',-34.61,-58.38],
        ['Santiago',-33.45,-70.67],['Lima',-12.05,-77.04],
        ['Bogotá',4.71,-74.07],['Caracas',10.49,-66.88],
        ['Montevidéu',-34.90,-56.16]
    ];

    const TILE_PROVIDERS = {
        none: { url: null, attrib: '' },
        osm: {
            url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            attrib: '© OpenStreetMap contributors',
            maxZoom: 19
        },
        esri: {
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attrib: 'Tiles © Esri — World Imagery',
            maxZoom: 19
        },
        topo: {
            url: 'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
            attrib: '© OpenTopoMap (CC-BY-SA), © OpenStreetMap',
            maxZoom: 17
        }
    };

    /* ───── Helpers de projeção Mercator ─────
       Em Mercator a latitude vira y = ln(tan(π/4 + φ/2)) (radianos),
       limitado em ±~85°. Mantemos viewport em lat/lon (lat_min..lat_max)
       mas converto via latToY/yToLat. */
    const MERC_LAT_MAX = 85.05112878;
    function clampLat(lat) { return Math.max(-MERC_LAT_MAX, Math.min(MERC_LAT_MAX, lat)); }
    function latToMercY(lat) {
        const phi = clampLat(lat) * Math.PI / 180;
        return Math.log(Math.tan(Math.PI / 4 + phi / 2));
    }
    function mercYToLat(y) {
        return (2 * Math.atan(Math.exp(y)) - Math.PI / 2) * 180 / Math.PI;
    }

    function SisMOM_Map(canvas, opts) {
        const self = {
            canvas,
            ctx: canvas.getContext('2d'),
            vp: [-60, -90, 15, -30],          // [latMin, lonMin, latMax, lonMax]
            projection: (opts && opts.projection) || 'platecarree',
            tileProvider: 'none',
            tileCache: new Map(),             // key -> {img, loaded, failed}
            tileRequestSeq: 0,
            attribEl: null,
            style: Object.assign({
                ocean: '#0e1622', land: '#1a2434', coast: '#3a4a5e',
                grid: 'rgba(200,210,225,0.10)', gridStrong: 'rgba(220,230,245,0.22)',
                city: '#9fb6d6', cityLabel: '#cbd6e6', bbox: '#4caf50',
                showCities: true, showCoast: true, showGrid: true
            }, (opts && opts.style) || {}),
            overlay: null, extraLayers: [],
            isDragging: false, lastX: 0, lastY: 0, onCursor: null
        };

        function rectPx() { return canvas.getBoundingClientRect(); }
        function isMercator() { return self.projection === 'mercator'; }

        // Conversão lat/lon ↔ pixel
        function lonToX(lon) {
            const r = rectPx();
            return (lon - self.vp[1]) / (self.vp[3] - self.vp[1]) * r.width;
        }
        function latToY(lat) {
            const r = rectPx();
            if (isMercator()) {
                const yTop = latToMercY(self.vp[2]);
                const yBot = latToMercY(self.vp[0]);
                const y    = latToMercY(lat);
                return (yTop - y) / (yTop - yBot) * r.height;
            }
            return (self.vp[2] - lat) / (self.vp[2] - self.vp[0]) * r.height;
        }
        function xToLon(x) {
            const r = rectPx();
            return self.vp[1] + (x / r.width) * (self.vp[3] - self.vp[1]);
        }
        function yToLat(y) {
            const r = rectPx();
            if (isMercator()) {
                const yTop = latToMercY(self.vp[2]);
                const yBot = latToMercY(self.vp[0]);
                const yM   = yTop - (y / r.height) * (yTop - yBot);
                return mercYToLat(yM);
            }
            return self.vp[2] - (y / r.height) * (self.vp[2] - self.vp[0]);
        }

        function resize() {
            const dpr = window.devicePixelRatio || 1;
            const r = rectPx();
            canvas.width  = Math.max(1, Math.round(r.width  * dpr));
            canvas.height = Math.max(1, Math.round(r.height * dpr));
            self.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            draw();
        }

        /* ───── Tiles ───── */
        function chooseTileZoom() {
            const provider = TILE_PROVIDERS[self.tileProvider];
            if (!provider || !provider.url) return 0;
            const r = rectPx();
            const lonSpan = self.vp[3] - self.vp[1];
            // 256 px por tile, 360/2^z graus por tile → z = log2(width * 360 / (lonSpan * 256))
            const z = Math.log2(r.width * 360 / (Math.max(1e-6, lonSpan) * 256));
            return Math.max(0, Math.min(provider.maxZoom || 19, Math.round(z)));
        }
        function lonLatToTileXY(lon, lat, z) {
            const n = Math.pow(2, z);
            const x = (lon + 180) / 360 * n;
            const phi = clampLat(lat) * Math.PI / 180;
            const y = (1 - Math.log(Math.tan(phi) + 1 / Math.cos(phi)) / Math.PI) / 2 * n;
            return { x, y };
        }
        function tileToLonLat(x, y, z) {
            const n = Math.pow(2, z);
            const lon = x / n * 360 - 180;
            const lat = Math.atan(Math.sinh(Math.PI * (1 - 2 * y / n))) * 180 / Math.PI;
            return { lon, lat };
        }
        function tileKey(z, x, y) { return self.tileProvider + '/' + z + '/' + x + '/' + y; }
        function buildTileUrl(z, x, y) {
            const p = TILE_PROVIDERS[self.tileProvider];
            if (!p || !p.url) return null;
            return p.url.replace('{z}', z).replace('{x}', x).replace('{y}', y);
        }
        function getTile(z, x, y) {
            const k = tileKey(z, x, y);
            if (self.tileCache.has(k)) return self.tileCache.get(k);
            const url = buildTileUrl(z, x, y);
            const entry = { img: new Image(), loaded: false, failed: false };
            entry.img.crossOrigin = 'anonymous';
            entry.img.onload = () => { entry.loaded = true; scheduleDraw(); };
            entry.img.onerror = () => { entry.failed = true; };
            entry.img.src = url;
            self.tileCache.set(k, entry);
            // Limpeza simples: corta cache se passar de 400 tiles
            if (self.tileCache.size > 400) {
                const firstKey = self.tileCache.keys().next().value;
                self.tileCache.delete(firstKey);
            }
            return entry;
        }
        let drawScheduled = false;
        function scheduleDraw() {
            if (drawScheduled) return;
            drawScheduled = true;
            requestAnimationFrame(() => { drawScheduled = false; draw(); });
        }

        function drawTiles() {
            if (!isMercator()) return;        // tiles XYZ só fazem sentido em Mercator
            const provider = TILE_PROVIDERS[self.tileProvider];
            if (!provider || !provider.url) return;
            const z = chooseTileZoom();
            const tlx = (self.vp[1] + 180) / 360 * Math.pow(2, z);
            const trx = (self.vp[3] + 180) / 360 * Math.pow(2, z);
            const yTop = lonLatToTileXY(0, self.vp[2], z).y;
            const yBot = lonLatToTileXY(0, self.vp[0], z).y;
            const xMin = Math.floor(tlx), xMax = Math.ceil(trx);
            const yMin = Math.floor(yTop), yMax = Math.ceil(yBot);
            const n = Math.pow(2, z);
            for (let ty = yMin; ty <= yMax; ty++) {
                if (ty < 0 || ty >= n) continue;
                for (let tx = xMin; tx <= xMax; tx++) {
                    // wrap longitudinal
                    const wx = ((tx % n) + n) % n;
                    const t = getTile(z, wx, ty);
                    if (!t.loaded) continue;
                    const a = tileToLonLat(tx, ty, z);          // canto NW (lon, lat)
                    const b = tileToLonLat(tx + 1, ty + 1, z);   // canto SE
                    const x0 = lonToX(a.lon), x1 = lonToX(b.lon);
                    const y0 = latToY(a.lat), y1 = latToY(b.lat);
                    self.ctx.drawImage(t.img, x0, y0, x1 - x0, y1 - y0);
                }
            }
        }

        /* ───── Camadas vetoriais (fallback offline) ───── */
        function drawPolyline(pts, style) {
            const ctx = self.ctx;
            if (!pts.length) return;
            ctx.beginPath();
            ctx.moveTo(lonToX(pts[0][1]), latToY(pts[0][0]));
            for (let i = 1; i < pts.length; i++) {
                ctx.lineTo(lonToX(pts[i][1]), latToY(pts[i][0]));
            }
            if (style.fill) { ctx.fillStyle = style.fill; ctx.fill(); }
            if (style.stroke) {
                ctx.strokeStyle = style.stroke;
                ctx.lineWidth = style.lineWidth || 1.2;
                ctx.stroke();
            }
        }
        function drawCoast() {
            // Quando há tiles, a costa fica redundante e atrapalha visualmente
            if (self.tileProvider !== 'none' && isMercator()) return;
            if (!self.style.showCoast) return;
            drawPolyline(SA_COAST.concat([SA_COAST[0]]), {
                fill: self.style.land, stroke: self.style.coast, lineWidth: 1.3
            });
        }
        function drawGeoJSON(gj, style) {
            const ctx = self.ctx;
            ctx.strokeStyle = style.stroke || '#888';
            ctx.lineWidth = style.lineWidth || 1;
            ctx.fillStyle = style.fill || 'rgba(0,0,0,0)';
            function drawRing(ring) {
                if (!ring.length) return;
                ctx.beginPath();
                ctx.moveTo(lonToX(ring[0][0]), latToY(ring[0][1]));
                for (let i = 1; i < ring.length; i++) ctx.lineTo(lonToX(ring[i][0]), latToY(ring[i][1]));
                if (style.fill) ctx.fill();
                if (style.stroke) ctx.stroke();
            }
            function drawLine(coords) {
                if (!coords.length) return;
                ctx.beginPath();
                ctx.moveTo(lonToX(coords[0][0]), latToY(coords[0][1]));
                for (let i = 1; i < coords.length; i++) ctx.lineTo(lonToX(coords[i][0]), latToY(coords[i][1]));
                ctx.stroke();
            }
            const features = (gj.type === 'FeatureCollection') ? gj.features : [gj];
            for (const f of features) {
                const g = f.geometry || f;
                if (!g || !g.coordinates) continue;
                if (g.type === 'Polygon') g.coordinates.forEach(drawRing);
                else if (g.type === 'MultiPolygon') g.coordinates.forEach(p => p.forEach(drawRing));
                else if (g.type === 'LineString') drawLine(g.coordinates);
                else if (g.type === 'MultiLineString') g.coordinates.forEach(drawLine);
            }
        }
        function drawGrid() {
            if (!self.style.showGrid) return;
            const ctx = self.ctx;
            const r = rectPx();
            const lonSpan = self.vp[3] - self.vp[1];
            const step = lonSpan > 60 ? 20 : lonSpan > 20 ? 10 : lonSpan > 8 ? 5 : lonSpan > 3 ? 2 : 1;
            ctx.lineWidth = 1;
            ctx.font = '10px sans-serif';
            ctx.fillStyle = self.style.cityLabel;
            const lonStart = Math.ceil(self.vp[1] / step) * step;
            for (let lon = lonStart; lon <= self.vp[3]; lon += step) {
                ctx.strokeStyle = (lon === 0) ? self.style.gridStrong : self.style.grid;
                const x = lonToX(lon);
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, r.height); ctx.stroke();
                ctx.fillText(lon + '°', x + 2, 11);
            }
            const latStart = Math.ceil(self.vp[0] / step) * step;
            for (let lat = latStart; lat <= self.vp[2]; lat += step) {
                ctx.strokeStyle = (lat === 0) ? self.style.gridStrong : self.style.grid;
                const y = latToY(lat);
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(r.width, y); ctx.stroke();
                ctx.fillText(lat + '°', 2, y - 2);
            }
        }
        function drawCities() {
            if (!self.style.showCities) return;
            const ctx = self.ctx;
            ctx.fillStyle = self.style.city;
            ctx.font = '11px sans-serif';
            const r = rectPx();
            const lonSpan = self.vp[3] - self.vp[1];
            for (const [name, lat, lon] of CITIES) {
                if (lat < self.vp[0] || lat > self.vp[2] || lon < self.vp[1] || lon > self.vp[3]) continue;
                const x = lonToX(lon), y = latToY(lat);
                if (x < 0 || x > r.width || y < 0 || y > r.height) continue;
                ctx.beginPath(); ctx.arc(x, y, 2.5, 0, 6.283); ctx.fill();
                if (lonSpan < 80 || ['São Paulo','Rio de Janeiro','Brasília','Buenos Aires','Lima'].includes(name)) {
                    ctx.fillStyle = self.style.cityLabel;
                    ctx.fillText(name, x + 5, y + 3);
                    ctx.fillStyle = self.style.city;
                }
            }
        }
        function drawRaster() {
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
        }
        function drawAttribution() {
            const p = TILE_PROVIDERS[self.tileProvider];
            if (!p || !p.attrib) { if (self.attribEl) self.attribEl.textContent = ''; return; }
            if (self.attribEl) self.attribEl.textContent = p.attrib;
        }
        function draw() {
            const ctx = self.ctx;
            const r = rectPx();
            ctx.fillStyle = self.style.ocean;
            ctx.fillRect(0, 0, r.width, r.height);
            drawTiles();
            drawCoast();
            for (const layer of self.extraLayers) {
                if (layer.type === 'geojson') drawGeoJSON(layer.data, layer.style || {});
            }
            drawRaster();
            drawGrid();
            drawCities();
            drawAttribution();
        }

        function setViewport(latMin, lonMin, latMax, lonMax) {
            self.vp = [latMin, lonMin, latMax, lonMax];
            draw();
        }
        function fitTo(bbox, margin) {
            const m = (margin == null ? 0.10 : margin);
            const lonW = bbox.maxX - bbox.minX, latH = bbox.maxY - bbox.minY;
            setViewport(bbox.minY - latH * m, bbox.minX - lonW * m, bbox.maxY + latH * m, bbox.maxX + lonW * m);
        }
        async function setRasterOverlay(imageDataOrBitmap, bbox, opacity) {
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
        function clearGeoJSON() { self.extraLayers = []; draw(); }
        function setTileProvider(name) {
            if (!TILE_PROVIDERS[name]) return;
            self.tileProvider = name;
            if (name !== 'none' && self.projection !== 'mercator') self.projection = 'mercator';
            draw();
        }
        function setProjection(name) {
            if (name !== 'platecarree' && name !== 'mercator') return;
            self.projection = name;
            if (name !== 'mercator') self.tileProvider = 'none';
            draw();
        }
        function setAttributionElement(el) { self.attribEl = el; drawAttribution(); }

        canvas.addEventListener('mousedown', (e) => {
            self.isDragging = true; self.lastX = e.clientX; self.lastY = e.clientY;
            canvas.style.cursor = 'grabbing';
        });
        window.addEventListener('mouseup', () => { self.isDragging = false; canvas.style.cursor = ''; });
        canvas.addEventListener('mousemove', (e) => {
            const r = rectPx();
            if (self.onCursor) self.onCursor({ lat: yToLat(e.clientY - r.top), lon: xToLon(e.clientX - r.left) });
            if (!self.isDragging) return;
            const dx = e.clientX - self.lastX, dy = e.clientY - self.lastY;
            self.lastX = e.clientX; self.lastY = e.clientY;
            const lonPerPx = (self.vp[3] - self.vp[1]) / r.width;
            if (isMercator()) {
                const yTop = latToMercY(self.vp[2]);
                const yBot = latToMercY(self.vp[0]);
                const dyM = (yTop - yBot) / r.height * dy;
                self.vp[2] = mercYToLat(yTop + dyM);
                self.vp[0] = mercYToLat(yBot + dyM);
            } else {
                const latPerPx = (self.vp[2] - self.vp[0]) / r.height;
                self.vp[0] += dy * latPerPx; self.vp[2] += dy * latPerPx;
            }
            self.vp[1] -= dx * lonPerPx; self.vp[3] -= dx * lonPerPx;
            draw();
        });
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const r = rectPx();
            const mx = e.clientX - r.left, my = e.clientY - r.top;
            const lon0 = xToLon(mx), lat0 = yToLat(my);
            const factor = e.deltaY < 0 ? 0.8 : 1.25;
            const lonW = (self.vp[3] - self.vp[1]) * factor;
            const fx = mx / r.width, fy = my / r.height;
            self.vp[1] = lon0 - fx * lonW; self.vp[3] = self.vp[1] + lonW;
            if (isMercator()) {
                const yTop = latToMercY(self.vp[2]);
                const yBot = latToMercY(self.vp[0]);
                const yM0  = latToMercY(lat0);
                const yH   = (yTop - yBot) * factor;
                const newTop = yM0 + fy * yH;
                const newBot = newTop - yH;
                self.vp[2] = mercYToLat(newTop); self.vp[0] = mercYToLat(newBot);
            } else {
                const latH = (self.vp[2] - self.vp[0]) * factor;
                self.vp[2] = lat0 + fy * latH; self.vp[0] = self.vp[2] - latH;
            }
            draw();
        }, { passive: false });

        const ro = new ResizeObserver(resize);
        ro.observe(canvas);
        resize();

        return {
            setViewport, fitTo, setRasterOverlay, clearOverlay, setOpacity,
            addGeoJSON, clearGeoJSON,
            setTileProvider, setProjection, setAttributionElement,
            redraw: draw,
            setStyle(s) { Object.assign(self.style, s); draw(); },
            onCursor(fn) { self.onCursor = fn; },
            destroy() { ro.disconnect(); self.tileCache.clear(); }
        };
    }

    root.SisMOM_Map = SisMOM_Map;
    root.SisMOM_Map.SA_COAST = SA_COAST;
    root.SisMOM_Map.CITIES = CITIES;
    root.SisMOM_Map.TILE_PROVIDERS = TILE_PROVIDERS;
})(typeof window !== 'undefined' ? window : globalThis);
