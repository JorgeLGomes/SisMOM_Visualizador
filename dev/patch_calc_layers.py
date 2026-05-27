#!/usr/bin/env python3
"""
Patch: calculadora de camadas (raster algebra).
A op B → nova camada, onde B pode ser outra camada (geotiff) ou escalar.
Operadores: + - * /. NoData propaga; div por 0 vira nodata.
Resultado entra como camada extra com nome descritivo.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) HTML: linha da calculadora após a linha "Camadas extras"
OLD_HTML = '''                <span id="gtLayerChips" style="display:inline-flex;gap:6px;flex-wrap:wrap;align-items:center"></span>
            </div>
            <canvas id="gtColorbar"'''
NEW_HTML = '''                <span id="gtLayerChips" style="display:inline-flex;gap:6px;flex-wrap:wrap;align-items:center"></span>
            </div>
            <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
                <span style="color:var(--text-muted,#aab);font-size:12px;font-weight:600">Calc:</span>
                <select id="gtCalcA" title="Camada A" style="max-width:140px;font-size:12px"></select>
                <select id="gtCalcOp" title="Operador" style="font-size:12px;width:48px">
                    <option value="+">+</option>
                    <option value="-">−</option>
                    <option value="*" selected>×</option>
                    <option value="/">÷</option>
                </select>
                <select id="gtCalcB" title="Camada B ou valor escalar" style="max-width:140px;font-size:12px">
                    <option value="__scalar__">(valor escalar)</option>
                </select>
                <input type="number" id="gtCalcScalar" step="any" placeholder="ex: 1000" style="width:90px;font-size:12px">
                <button class="btn btn-ghost" id="btnGtCalc" type="button" title="Cria uma nova camada A op B">Calcular</button>
            </div>
            <canvas id="gtColorbar"'''

# (2) Funções JS — inserir antes de gtSampleAtLatLon (anchor estável)
OLD_ANCHOR = '''    function gtSampleAtLatLon(lat, lon) {'''
NEW_ANCHOR = '''    /* ─── Calculadora de camadas (raster algebra) ─── */
    function gtRenderCalcSelects() {
        const selA = document.getElementById('gtCalcA');
        const selB = document.getElementById('gtCalcB');
        if (!selA || !selB) return;
        const prevA = selA.value, prevB = selB.value;
        const opts = [];
        const all = gtAllLayers();
        for (const l of all) {
            if (l.type !== 'geotiff' || !l.decoded) continue;
            opts.push(`<option value="${l.id}">${(l.name || l.id).replace(/&/g, '&amp;').replace(/</g, '&lt;').slice(0, 60)}</option>`);
        }
        selA.innerHTML = opts.join('');
        selB.innerHTML = '<option value="__scalar__">(valor escalar)</option>' + opts.join('');
        if (prevA && selA.querySelector(`option[value="${prevA}"]`)) selA.value = prevA;
        if (prevB && selB.querySelector(`option[value="${prevB}"]`)) selB.value = prevB;
        gtUpdateCalcScalarVisibility();
    }
    function gtUpdateCalcScalarVisibility() {
        const selB = document.getElementById('gtCalcB');
        const inp = document.getElementById('gtCalcScalar');
        if (!selB || !inp) return;
        inp.style.display = (selB.value === '__scalar__') ? '' : 'none';
    }
    async function gtCalcularNovaCamada() {
        const selA = document.getElementById('gtCalcA');
        const selB = document.getElementById('gtCalcB');
        const selOp = document.getElementById('gtCalcOp');
        const inpS = document.getElementById('gtCalcScalar');
        if (!selA || !selB || !selOp) return;
        const a = gtGetLayerObj(selA.value);
        if (!a || !a.decoded) { alert('Camada A inválida'); return; }
        const op = selOp.value;
        let useScalar = false, bScalar = NaN, b = null;
        if (selB.value === '__scalar__') {
            useScalar = true;
            bScalar = parseFloat(inpS.value);
            if (!isFinite(bScalar)) { alert('Valor escalar inválido'); return; }
        } else {
            b = gtGetLayerObj(selB.value);
            if (!b || !b.decoded) { alert('Camada B inválida'); return; }
            if (b.decoded.width !== a.decoded.width || b.decoded.height !== a.decoded.height) {
                alert(`Camadas precisam ter mesma dimensão (A: ${a.decoded.width}×${a.decoded.height}, B: ${b.decoded.width}×${b.decoded.height})`);
                return;
            }
        }
        const decA = a.decoded, decB = b ? b.decoded : null;
        const N = decA.data.length;
        const result = new Float32Array(N);
        const RESULT_ND = -9999;
        const ndA = decA.nodata;
        const extrasA = decA.nodataExtras || null;
        const ndB = decB ? decB.nodata : null;
        const extrasB = decB ? decB.nodataExtras : null;
        function maskA(v) {
            if (!isFinite(v)) return true;
            if (ndA != null && v === ndA) return true;
            if (extrasA) for (let k = 0; k < extrasA.length; k++) if (v === extrasA[k]) return true;
            return false;
        }
        function maskB(v) {
            if (!isFinite(v)) return true;
            if (ndB != null && v === ndB) return true;
            if (extrasB) for (let k = 0; k < extrasB.length; k++) if (v === extrasB[k]) return true;
            return false;
        }
        for (let i = 0; i < N; i++) {
            const av = decA.data[i];
            if (maskA(av)) { result[i] = RESULT_ND; continue; }
            const bv = useScalar ? bScalar : decB.data[i];
            if (!useScalar && maskB(bv)) { result[i] = RESULT_ND; continue; }
            let r;
            switch (op) {
                case '+': r = av + bv; break;
                case '-': r = av - bv; break;
                case '*': r = av * bv; break;
                case '/': r = (bv === 0) ? RESULT_ND : av / bv; break;
                default: r = av;
            }
            result[i] = r;
        }
        let mn = Infinity, mx = -Infinity;
        for (let i = 0; i < N; i++) {
            const v = result[i];
            if (!isFinite(v) || v === RESULT_ND) continue;
            if (v < mn) mn = v; if (v > mx) mx = v;
        }
        if (!isFinite(mn)) { mn = 0; mx = 1; }
        const nameA = a.name || a.id;
        const nameB = useScalar ? String(bScalar) : (b.name || b.id);
        const opSym = { '+': '+', '-': '−', '*': '×', '/': '÷' }[op] || op;
        const newName = `(${nameA} ${opSym} ${nameB})`;
        const id = 'calc_' + (++gtLayerSeq) + '_' + Date.now();
        const decoded = {
            width: decA.width, height: decA.height, data: result,
            nodata: RESULT_ND, nodataExtras: null,
            bbox: decA.bbox, scale: decA.scale,
            min: mn, max: mx
        };
        const paleta = (document.getElementById('gtPaleta') || {}).value || 'viridis';
        const layer = { id, type: 'geotiff', name: newName, visible: true, opacity: 0.85,
            decoded, paleta,
            props: { paleta, autoMinMax: true, customMin: null, customMax: null,
                      undefRaw: '', clipBelow: null, clipAbove: null }
        };
        gtExtraLayers.push(layer);
        gtLayerEnsureMap();
        await gtLayerPushToMap(layer);
        gtRenderLayerChips();
        gtRenderOverlayColorbars();
        gtRenderCalcSelects();
    }
    function gtSampleAtLatLon(lat, lon) {'''

# (3) Binding na inicialização (em bindGeoTIFFUI, depois do bind do clear)
OLD_BIND_AFTER_CLEAR = '''        if (btnClearAll) btnClearAll.addEventListener('click', () => {'''
NEW_BIND_AFTER_CLEAR = '''        // Calculadora de camadas
        const btnCalc = document.getElementById('btnGtCalc');
        const selCalcB = document.getElementById('gtCalcB');
        if (btnCalc) btnCalc.addEventListener('click', () => gtCalcularNovaCamada());
        if (selCalcB) selCalcB.addEventListener('change', gtUpdateCalcScalarVisibility);
        // Popula selects da calculadora ao iniciar
        try { gtRenderCalcSelects(); } catch (_) {}
        if (btnClearAll) btnClearAll.addEventListener('click', () => {'''

# (4) Atualizar selects quando o set de camadas muda: hooks em gtRenderLayerChips
OLD_CHIPS_END = '''            item.addEventListener('click', () => gtSetActiveLayer(l.id));
            container.appendChild(item);
        });
    }

    function gtTogglePrimaryVisible() {'''
NEW_CHIPS_END = '''            item.addEventListener('click', () => gtSetActiveLayer(l.id));
            container.appendChild(item);
        });
        // Mantém selects da calculadora sincronizados com a lista
        try { gtRenderCalcSelects(); } catch (_) {}
    }

    function gtTogglePrimaryVisible() {'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if 'gtCalcularNovaCamada' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_HTML,             NEW_HTML,             'html calc row')
    src = rep(src, OLD_ANCHOR,           NEW_ANCHOR,           'calc functions')
    src = rep(src, OLD_BIND_AFTER_CLEAR, NEW_BIND_AFTER_CLEAR, 'bind calc')
    src = rep(src, OLD_CHIPS_END,        NEW_CHIPS_END,        'chips → resync calc')

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
        print("OK - " + str(len(a)) + " bytes em ambas")

if __name__ == "__main__":
    main()
