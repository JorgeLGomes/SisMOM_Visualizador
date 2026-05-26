/* ============================================================
 * SisMOM Map — mapa-base custom, em canvas, sem dependência.
 *   - Viewport em lat/lon (EPSG:4326 simples, sem reprojeção)
 *   - Costa da América do Sul codificada (~50 pontos curados)
 *   - Grade de paralelos/meridianos (configurável)
 *   - Pan/zoom/wheel; toggle de visibilidade do mapa-base
 *   - Overlay do raster GeoTIFF com bbox em lat/lon (ImageBitmap)
 *   - Suporta carregar GeoJSON adicional via API (window.SisMOM_Map.addGeoJSON)
 * Limitação consciente: projeção plate carrée (lat/lon -> x/y linear).
 * Adequada para visualização local; não para áreas polares ou globais.
 * ============================================================ */
(function (root) {
    'use strict';

    /* ───── Costa simplificada da América do Sul (lat, lon) ─────
       Curada manualmente (cidades costeiras + cantos), suficiente
       para dar contexto geográfico ao usuário do CPTEC. Não é
       cartograficamente precisa: pretende ser uma silhueta. */
    const SA_COAST = [
        // Norte (Guianas → Caribe colombiano/venezuelano)
        [10.6, -61.0], [10.6, -66.9], [10.7, -71.6], [10.4, -75.5], [8.6, -77.0],
        // Pacífico colombiano → equatoriano
        [3.9, -77.0], [1.0, -79.7], [-2.2, -80.0],
        // Pacífico peruano
        [-4.9, -81.3], [-9.0, -78.6], [-12.0, -77.0], [-17.0, -71.4],
        // Pacífico chileno
        [-20.2, -70.1], [-23.7, -70.4], [-29.9, -71.3], [-33.0, -71.6],
        [-36.8, -73.0], [-41.5, -73.0], [-45.0, -73.8], [-50.0, -74.6],
        [-53.0, -71.0],
        // Estreito de Magalhães / Cabo de Hornos
        [-55.5, -68.0], [-54.9, -65.0],
        // Atlântico argentino
        [-52.0, -68.5], [-47.8, -65.9], [-42.8, -64.6], [-39.0, -62.0],
        [-38.0, -57.5], [-34.6, -58.5],
        // Uruguai
        [-34.9, -54.9], [-34.0, -53.5],
        // Sul/Sudeste do Brasil
        [-32.0, -52.1], [-29.4, -49.7], [-27.5, -48.5], [-25.5, -48.0],
        [-23.0, -43.2], [-22.0, -41.0], [-20.0, -40.0], [-18.0, -39.5],
        // Nordeste
        [-13.0, -38.5], [-9.4, -35.5], [-8.0, -34.9], [-5.8, -35.2],
        [-3.7, -38.5], [-2.5, -44.0], [-1.5, -48.5],
        // Foz do Amazonas → Guiana → fecha
        [0.5, -50.0], [4.4, -51.6], [5.5, -54.0], [5.2, -57.5], [6.8, -58.2],
        [8.0, -59.5], [8.5, -60.0]
    ];

    /* ───── Cidades-âncora (para orientação visual) ───── */
    const CITIES = [
        ['São Paulo', -23.55, -46.63],
        ['Rio de Janeiro', -22.91, -43.17],
        ['Brasília', -15.78, -47.93],
        ['Salvador', -12.97, -38.51],
        ['Fortaleza', -3.73, -38.54],
        ['Recife', -8.05, -34.88],
        ['Belém', -1.46, -48.49],
        ['Manaus', -3.12, -60.02],
        ['Porto Alegre', -30.03, -51.23],
        ['Curitiba', -25.43, -49.27],
        ['Belo Horizonte', -19.92, -43.94],
        ['Buenos Aires', -34.61, -58.38],
        ['Santiago', -33.45, -70.67],
        ['Lima', -12.05, -77.04],
        ['Bogotá', 4.71, -74.07],
        ['Caracas', 10.49, -66.88],
        ['Montevidéu', -34.90, -56.16]
    ];

    /* ───── Mapa em si ───── */
    function SisMOM_Map(canvas, opts) {
        const self = {
            canvas,
            ctx: canvas.getContext('2d'),
            // viewport [lat_min, lon_min, lat_max, lon_max]
            vp: [-60, -90, 15, -30],
            // estilo
            style: Object.assign({
                ocean: '#0e1622',
                land:  '#1a2434',
                coast: '#3a4a5e',
                grid:  'rgba(200,210,225,0.10)',
                gridStrong: 'rgba(220,230,245,0.22)',
                city:  '#9fb6d6',
                cityLabel: '#cbd6e6',
                bbox:  '#4caf50',
                showCities: true,
                showCoast: true,
                showGrid:  true
            }, (opts && opts.style) || {}),
            // overlay raster
            overlay: null,   // { bbox: {minX,minY,maxX,maxY}, bitmap: ImageBitmap, opacity: 0..1 }
            extraLayers: [], // [{ type:'geojson', data, style }]
            // interação
            isDragging: false,
            lastX: 0, lastY: 0,
            onCursor: null    // callback({lat, lon})
        };

        function resize() {
            const dpr = window.devicePixelRatio || 1;
            const r = canvas.getBoundingClientRect();
            canvas.width  = Math.max(1, Math.round(r.width  * dpr));
            canvas.height = Math.max(1, Math.round(r.height * dpr));
            self.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            draw();
        }

        function lonToX(lon) {
            const r = canvas.getBoundingClientRect();
            return (lon - self.vp[1]) / (self.vp[3] - self.vp[1]) * r.width;
        }
        function latToY(lat) {
            const r = canvas.getBoundingClientRect();
            return (self.vp[2] - lat) / (self.vp[2] - self.vp[0]) * r.height;
        }
        function xToLon(x) {
            const r = canvas.getBoundingClientRect();
            return self.vp[1] + (x / r.width) * (self.vp[3] - self.vp[1]);
        }
        function yToLat(y) {
            const r = canvas.getBoundingClientRect();
            return self.vp[2] - (y / r.height) * (self.vp[2] - self.vp[0]);
        }

        function drawGrid() {
            if (!self.style.showGrid) return;
            const ctx = self.ctx;
            const r = canvas.getBoundingClientRect();
            const [latMin, lonMin, latMax, lonMax] = self.vp;
            const lonSpan = lonMax - lonMin;
            const latSpan = latMax - latMin;
            // Passo dinâmico: 10° por padrão, ajusta com zoom
            const step = lonSpan > 60 ? 20 : lonSpan > 20 ? 10 : lonSpan > 8 ? 5 : lonSpan > 3 ? 2 : 1;
            ctx.lineWidth = 1;
            ctx.font = '10px sans-serif';
            ctx.fillStyle = self.style.cityLabel;
            // Meridianos
            const lonStart = Math.ceil(lonMin / step) * step;
            for (let lon = lonStart; lon <= lonMax; lon += step) {
                ctx.strokeStyle = (lon === 0) ? self.style.gridStrong : self.style.grid;
                const x = lonToX(lon);
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, r.height); ctx.stroke();
                ctx.fillText(lon + '°', x + 2, 11);
            }
            // Paralelos
            const latStart = Math.ceil(latMin / step) * step;
            for (let lat = latStart; lat <= latMax; lat += step) {
                ctx.strokeStyle = (lat === 0) ? self.style.gridStrong : self.style.grid;
                const y = latToY(lat);
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(r.width, y); ctx.stroke();
                ctx.fillText(lat + '°', 2, y - 2);
            }
        }

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
            if (!self.style.showCoast) return;
            // Costa SA: polígono fechado preenchido como "terra" + traço de costa
            const ctx = self.ctx;
            // Como o polígono é só a costa, fechamos voltando ao primeiro ponto.
            drawPolyline(SA_COAST.concat([SA_COAST[0]]), {
                fill: self.style.land,
                stroke: self.style.coast,
                lineWidth: 1.3
            });
        }

        function drawGeoJSON(gj, style) {
            // Implementação mínima: features de tipo Polygon, MultiPolygon, LineString, MultiLineString
            const ctx = self.ctx;
            ctx.strokeStyle = style.stroke || '#888';
            ctx.lineWidth = style.lineWidth || 1;
            ctx.fillStyle = style.fill || 'rgba(0,0,0,0)';

            function drawRing(ring) {
                if (!ring.length) return;
                ctx.beginPath();
                ctx.moveTo(lonToX(ring[0][0]), latToY(ring[0][1])); // GeoJSON: [lon, lat]
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
                else if (g.type === 'MultiPolygon') g.coordinates.forEach(poly => poly.forEach(drawRing));
                else if (g.type === 'LineString') drawLine(g.coordinates);
                else if (g.type === 'MultiLineString') g.coordinates.forEach(drawLine);
            }
        }

        function drawCities() {
            if (!self.style.showCities) return;
            const ctx = self.ctx;
            ctx.fillStyle = self.style.city;
            ctx.font = '11px sans-serif';
            const r = canvas.getBoundingClientRect();
            const lonSpan = self.vp[3] - self.vp[1];
            // Filtra cidades pelo zoom: só mostra capitais menores quando zoomado
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
            const w = x1 - x0, h = y1 - y0;
            ctx.save();
            ctx.globalAlpha = (opacity == null ? 0.85 : opacity);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(bitmap, x0, y0, w, h);
            ctx.restore();
            // Moldura da bbox
            ctx.strokeStyle = self.style.bbox;
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 3]);
            ctx.strokeRect(x0, y0, w, h);
            ctx.setLineDash([]);
        }

        function draw() {
            const ctx = self.ctx;
            const r = canvas.getBoundingClientRect();
            ctx.fillStyle = self.style.ocean;
            ctx.fillRect(0, 0, r.width, r.height);
            drawCoast();
            for (const layer of self.extraLayers) {
                if (layer.type === 'geojson') drawGeoJSON(layer.data, layer.style || {});
            }
            drawRaster();
            drawGrid();
            drawCities();
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
            if (bmp && bmp instanceof ImageData) {
                bmp = await createImageBitmap(bmp);
            }
            self.overlay = { bitmap: bmp, bbox, opacity: (opacity == null ? 0.85 : opacity) };
            draw();
        }
        function clearOverlay() { self.overlay = null; draw(); }
        function setOpacity(o) {
            if (self.overlay) { self.overlay.opacity = o; draw(); }
        }
        function addGeoJSON(data, style) {
            self.extraLayers.push({ type: 'geojson', data, style: style || { stroke: '#4dd0e1', lineWidth: 0.8 } });
            draw();
        }
        function clearGeoJSON() { self.extraLayers = []; draw(); }

        // Interação: pan
        canvas.addEventListener('mousedown', (e) => {
            self.isDragging = true; self.lastX = e.clientX; self.lastY = e.clientY;
            canvas.style.cursor = 'grabbing';
        });
        window.addEventListener('mouseup', () => { self.isDragging = false; canvas.style.cursor = ''; });
        canvas.addEventListener('mousemove', (e) => {
            const r = canvas.getBoundingClientRect();
            if (self.onCursor) self.onCursor({ lat: yToLat(e.clientY - r.top), lon: xToLon(e.clientX - r.left) });
            if (!self.isDragging) return;
            const dx = e.clientX - self.lastX, dy = e.clientY - self.lastY;
            self.lastX = e.clientX; self.lastY = e.clientY;
            const lonPerPx = (self.vp[3] - self.vp[1]) / r.width;
            const latPerPx = (self.vp[2] - self.vp[0]) / r.height;
            self.vp[1] -= dx * lonPerPx; self.vp[3] -= dx * lonPerPx;
            self.vp[0] += dy * latPerPx; self.vp[2] += dy * latPerPx;
            draw();
        });
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const r = canvas.getBoundingClientRect();
            const mx = e.clientX - r.left, my = e.clientY - r.top;
            const lon0 = xToLon(mx), lat0 = yToLat(my);
            const factor = e.deltaY < 0 ? 0.8 : 1.25;
            const lonW = (self.vp[3] - self.vp[1]) * factor;
            const latH = (self.vp[2] - self.vp[0]) * factor;
            const fx = mx / r.width, fy = my / r.height;
            self.vp[1] = lon0 - fx * lonW; self.vp[3] = self.vp[1] + lonW;
            self.vp[2] = lat0 + fy * latH; self.vp[0] = self.vp[2] - latH;
            draw();
        }, { passive: false });

        const ro = new ResizeObserver(resize);
        ro.observe(canvas);
        resize();

        return {
            setViewport, fitTo, setRasterOverlay, clearOverlay, setOpacity,
            addGeoJSON, clearGeoJSON,
            redraw: draw,
            setStyle(s) { Object.assign(self.style, s); draw(); },
            onCursor(fn) { self.onCursor = fn; },
            destroy() { ro.disconnect(); }
        };
    }

    root.SisMOM_Map = SisMOM_Map;
    root.SisMOM_Map.SA_COAST = SA_COAST;
    root.SisMOM_Map.CITIES = CITIES;
})(typeof window !== 'undefined' ? window : globalThis);
