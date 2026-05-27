#!/usr/bin/env python3
"""
Patch: corrigir navegação em bbox global. Bbox como (-181, 181) com margem 10%
fazia o viewport ir a (-217, 217), > 360° de span, gerando coordenadas absurdas
no HUD e zoom/pan errado.

 (1) fitTo: limita margem total para não passar de [-180, 180] em lon nem 90° em lat.
 (2) adjustViewportToAspect: clampa lonSpan <= 360° (não pode dar mais que uma volta).
 (3) Helper wrapLon(): normaliza longitude para [-180, 180] antes de exibir no HUD/grid.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# ─── (1) fitTo: limita margem ───
OLD_FITTO = '''        function fitTo(bbox, margin) {
            const m = (margin == null ? 0.10 : margin);
            const lonW = bbox.maxX - bbox.minX, latH = bbox.maxY - bbox.minY;
            // Define viewport pelo bbox com margem
            self.vp = [bbox.minY - latH * m, bbox.minX - lonW * m, bbox.maxY + latH * m, bbox.maxX + lonW * m];'''
NEW_FITTO = '''        function fitTo(bbox, margin) {
            const m = (margin == null ? 0.10 : margin);
            const lonW = bbox.maxX - bbox.minX, latH = bbox.maxY - bbox.minY;
            // Limita a margem para não ultrapassar valores globais.
            // Sem isso, bbox (-181, 181) com margem 10% gerava viewport > 360° (mais de uma volta).
            const lonMargin = Math.min(lonW * m, Math.max(0, (360 - lonW) / 2));
            const latMargin = Math.min(latH * m, Math.max(0, (170 - latH) / 2));
            self.vp = [bbox.minY - latMargin, bbox.minX - lonMargin,
                       bbox.maxY + latMargin, bbox.maxX + lonMargin];'''

# ─── (2) adjustViewportToAspect: clampa lonSpan <= 360° ───
OLD_ADJUST = '''        function adjustViewportToAspect() {
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
        }'''
NEW_ADJUST = '''        function adjustViewportToAspect() {
            const r = rectPx();
            if (r.width < 4 || r.height < 4) return;
            const aspect = r.width / r.height;
            // Clampa lonSpan para nunca passar de 360° (mais que uma volta do globo).
            let lonSpan = self.vp[3] - self.vp[1];
            if (lonSpan > 360) {
                const lonC = (self.vp[1] + self.vp[3]) / 2;
                self.vp[1] = lonC - 180; self.vp[3] = lonC + 180;
                lonSpan = 360;
            }
            if (isMercator()) {
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
                const latC = (self.vp[0] + self.vp[2]) / 2;
                let desiredLat = lonSpan / aspect;
                if (desiredLat > 170) desiredLat = 170;
                self.vp[0] = latC - desiredLat / 2;
                self.vp[2] = latC + desiredLat / 2;
            }
        }'''

# ─── (3) wrapLon helper + uso no HUD da coordenada ───
# Adiciona function wrapLon antes de gtAtualizarCoord e usa lá
OLD_HUD_FN = '''    function gtAtualizarCoord(lat, lon) {
        const els = [document.getElementById('gtCoord'), document.getElementById('gtCoordHud')].filter(Boolean);
        if (!els.length) return;
        const coord = `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;'''
NEW_HUD_FN = '''    function gtWrapLon(lon) {
        // Normaliza qualquer longitude para [-180, 180]
        let x = ((lon + 180) % 360 + 360) % 360 - 180;
        if (x === -180) x = 180;
        return x;
    }
    function gtAtualizarCoord(lat, lon) {
        const els = [document.getElementById('gtCoord'), document.getElementById('gtCoordHud')].filter(Boolean);
        if (!els.length) return;
        const lonN = gtWrapLon(lon);
        const coord = `${lat.toFixed(3)}°, ${lonN.toFixed(3)}°`;'''

# E a chamada de gtSampleAtLatLon (que usa lat/lon para indexar bbox) — usar lonN
OLD_SAMP = '''        const coord = `${lat.toFixed(3)}°, ${lonN.toFixed(3)}°`;
        const samp = gtSampleAtLatLon(lat, lon);'''
NEW_SAMP = '''        const coord = `${lat.toFixed(3)}°, ${lonN.toFixed(3)}°`;
        const samp = gtSampleAtLatLon(lat, lonN);'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtWrapLon' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_FITTO,  NEW_FITTO,  'fitTo margin clamp')
    src = rep(src, OLD_ADJUST, NEW_ADJUST, 'adjust aspect lon clamp')
    src = rep(src, OLD_HUD_FN, NEW_HUD_FN, 'wrapLon helper')
    src = rep(src, OLD_SAMP,   NEW_SAMP,   'sample with wrapped lon')

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
