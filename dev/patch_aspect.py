#!/usr/bin/env python3
"""
Patch: preservar aspect ratio do mapa quando o canvas é redimensionado
(ex.: painel lateral colapsa/expande). Em Mercator, ajusta latSpan;
em Plate Carrée, mesma regra mas linear. Centro preservado.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# Adiciona adjustViewportToAspect e o chama em resize/fitTo/setViewport/setProjection/setTileProvider
# Substitui o resize antigo
OLD_RESIZE = '''        function resize() {
            const dpr = window.devicePixelRatio || 1;
            const r = rectPx();
            canvas.width  = Math.max(1, Math.round(r.width  * dpr));
            canvas.height = Math.max(1, Math.round(r.height * dpr));
            self.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            draw();
        }'''
NEW_RESIZE = '''        function adjustViewportToAspect() {
            const r = rectPx();
            if (r.width < 4 || r.height < 4) return;
            const aspect = r.width / r.height;  // px largura / altura
            const lonSpan = self.vp[3] - self.vp[1];
            if (isMercator()) {
                // Em Mercator, lon (em radianos) e mercY (em radianos) têm escala compatível.
                // queremos: lonSpanRad / aspect == mercYSpan
                const lonSpanRad = lonSpan * Math.PI / 180;
                const desiredMercY = lonSpanRad / aspect;
                const yTop = latToMercY(self.vp[2]);
                const yBot = latToMercY(self.vp[0]);
                const yCenter = (yTop + yBot) / 2;
                const newTop = yCenter + desiredMercY / 2;
                const newBot = yCenter - desiredMercY / 2;
                self.vp[2] = mercYToLat(newTop);
                self.vp[0] = mercYToLat(newBot);
            } else {
                // Plate Carrée: latSpan = lonSpan / aspect (centro preservado)
                const latC = (self.vp[0] + self.vp[2]) / 2;
                const desiredLat = lonSpan / aspect;
                self.vp[0] = latC - desiredLat / 2;
                self.vp[2] = latC + desiredLat / 2;
            }
        }
        function resize() {
            const dpr = window.devicePixelRatio || 1;
            const r = rectPx();
            canvas.width  = Math.max(1, Math.round(r.width  * dpr));
            canvas.height = Math.max(1, Math.round(r.height * dpr));
            self.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            adjustViewportToAspect();
            draw();
        }'''

# fitTo: depois de calcular o viewport pela bbox, ajusta aspect ratio
OLD_FITTO = '''        function fitTo(bbox, margin) {
            const m = (margin == null ? 0.10 : margin);
            const lonW = bbox.maxX - bbox.minX, latH = bbox.maxY - bbox.minY;
            setViewport(bbox.minY - latH * m, bbox.minX - lonW * m, bbox.maxY + latH * m, bbox.maxX + lonW * m);
        }'''
NEW_FITTO = '''        function fitTo(bbox, margin) {
            const m = (margin == null ? 0.10 : margin);
            const lonW = bbox.maxX - bbox.minX, latH = bbox.maxY - bbox.minY;
            // Define viewport pelo bbox com margem
            self.vp = [bbox.minY - latH * m, bbox.minX - lonW * m, bbox.maxY + latH * m, bbox.maxX + lonW * m];
            // Ajusta aspect para que TODO o bbox fique visível: se canvas mais alto que largo,
            // expandir lonSpan; se mais largo, expandir latSpan
            const r = rectPx();
            if (r.width >= 4 && r.height >= 4) {
                const canvasAspect = r.width / r.height;
                const bboxAspect = (self.vp[3] - self.vp[1]) / Math.max(1e-9, (self.vp[2] - self.vp[0]));
                if (canvasAspect > bboxAspect) {
                    // Canvas mais largo: expande lon
                    const latSpan = self.vp[2] - self.vp[0];
                    const desiredLon = latSpan * canvasAspect;
                    const lonC = (self.vp[1] + self.vp[3]) / 2;
                    self.vp[1] = lonC - desiredLon / 2;
                    self.vp[3] = lonC + desiredLon / 2;
                } else {
                    // Canvas mais alto: expande lat (em Mercator usa fórmula correta)
                    adjustViewportToAspect();
                }
            }
            draw();
        }'''

# setViewport: garante aspect ratio
OLD_SETVP = '''        function setViewport(latMin, lonMin, latMax, lonMax) {
            self.vp = [latMin, lonMin, latMax, lonMax];
            draw();
        }'''
NEW_SETVP = '''        function setViewport(latMin, lonMin, latMax, lonMax) {
            self.vp = [latMin, lonMin, latMax, lonMax];
            adjustViewportToAspect();
            draw();
        }'''

# setProjection: ao trocar projeção, re-ajusta aspect (Mercator vs Plate Carrée muda escalas)
OLD_SETPROJ = '''        function setProjection(name) {
            if (name !== 'platecarree' && name !== 'mercator') return;
            self.projection = name;
            if (name !== 'mercator') self.tileProvider = 'none';
            draw();
        }'''
NEW_SETPROJ = '''        function setProjection(name) {
            if (name !== 'platecarree' && name !== 'mercator') return;
            self.projection = name;
            if (name !== 'mercator') self.tileProvider = 'none';
            adjustViewportToAspect();
            draw();
        }'''

# setTileProvider já força Mercator; aqui re-ajusta aspect também
OLD_SETTP = '''        function setTileProvider(name) {
            if (!TILE_PROVIDERS[name]) return;
            self.tileProvider = name;
            if (name !== 'none' && self.projection !== 'mercator') self.projection = 'mercator';
            draw();
        }'''
NEW_SETTP = '''        function setTileProvider(name) {
            if (!TILE_PROVIDERS[name]) return;
            self.tileProvider = name;
            if (name !== 'none' && self.projection !== 'mercator') self.projection = 'mercator';
            adjustViewportToAspect();
            draw();
        }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'adjustViewportToAspect' in src:
        print(f"[{path.name}] já patcheado (adjustViewportToAspect); pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_RESIZE,  NEW_RESIZE,  'resize+aspect helper')
    src = rep(src, OLD_FITTO,   NEW_FITTO,   'fitTo with aspect')
    src = rep(src, OLD_SETVP,   NEW_SETVP,   'setViewport adjust')
    src = rep(src, OLD_SETPROJ, NEW_SETPROJ, 'setProjection adjust')
    src = rep(src, OLD_SETTP,   NEW_SETTP,   'setTileProvider adjust')

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
