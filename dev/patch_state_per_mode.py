#!/usr/bin/env python3
"""
Patch: estado independente por aba PNG/GIF vs GeoTIFF.
Snapshot serializável do `state` ao sair de uma aba, restauração ao
voltar. Persistido em localStorage por modo.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# Patch no setAppMode: salvar estado anterior e carregar novo, com restore de UI.
OLD = '''    function setAppMode(mode, opts) {
        if (mode !== 'png' && mode !== 'gtiff') return;
        appMode = mode;
        try { localStorage.setItem('sismom_app_mode', mode); } catch (_) {}
        // Tabs visual
        document.querySelectorAll('.mode-tab').forEach(b => {
            const on = b.getAttribute('data-app-mode') === mode;
            b.classList.toggle('active', on);
            b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        const mainPNG = document.getElementById('main-content');
        const mainGT  = document.getElementById('mainGT');
        const modal   = document.getElementById('modalGeoTIFF');
        if (mode === 'gtiff') {
            // Move modal pra dentro de mainGT
            if (modal && mainGT && modal.parentNode !== mainGT) {
                _gtModalParent = modal.parentNode;
                mainGT.appendChild(modal);
            }
            if (modal) { modal.classList.add('inline'); modal.classList.add('open'); }
            if (mainPNG) mainPNG.style.display = 'none';
            if (mainGT)  mainGT.style.display  = '';
            // Carrega do FTP via slot 0
            gtLoadFromState().catch(() => {});
        } else {
            // Volta modal pra onde estava (body)
            if (modal) {
                modal.classList.remove('inline');
                modal.classList.remove('open');
                if (_gtModalParent && modal.parentNode !== _gtModalParent) {
                    _gtModalParent.appendChild(modal);
                }
            }
            if (mainPNG) mainPNG.style.display = '';
            if (mainGT)  mainGT.style.display  = 'none';
        }
    }'''
NEW = '''    function _stateSnapshot() {
        // Serializável: omite handles não-serializáveis (interval).
        return {
            layout: state.layout,
            passoAtual: state.passoAtual,
            maxPassos: state.maxPassos,
            stepFreq: state.stepFreq,
            tempo: state.tempo,
            animando: false,  // ao restaurar nunca queremos retomar animando automaticamente
            slots: (state.slots || []).map(s => ({
                modelo: s.modelo, variavel: s.variavel, data: s.data,
                passoBase: s.passoBase, sync: s.sync
            }))
        };
    }
    function _stateRestore(snap) {
        if (!snap) return;
        try { if (typeof pararAnimacao === 'function' && state.animando) pararAnimacao(); } catch (_) {}
        if (snap.layout != null) state.layout = snap.layout;
        if (snap.passoAtual != null) state.passoAtual = snap.passoAtual;
        if (snap.maxPassos != null) state.maxPassos = snap.maxPassos;
        if (snap.stepFreq != null) state.stepFreq = snap.stepFreq;
        if (snap.tempo != null) state.tempo = snap.tempo;
        if (Array.isArray(snap.slots)) {
            for (let i = 0; i < snap.slots.length && i < state.slots.length; i++) {
                const s = snap.slots[i] || {};
                if (s.modelo) state.slots[i].modelo = s.modelo;
                if (s.variavel) state.slots[i].variavel = s.variavel;
                if (s.data) state.slots[i].data = s.data;
                if (s.passoBase != null) state.slots[i].passoBase = s.passoBase;
                if (s.sync != null) state.slots[i].sync = s.sync;
            }
        }
        // Re-aplica layout (re-renderiza painéis e re-popula selects/datas)
        try { if (typeof setLayout === 'function') setLayout(state.layout, true); } catch (_) {}
        try { if (typeof setStepIndicatorUI === 'function') setStepIndicatorUI(); } catch (_) {}
        try { if (typeof renderTudo === 'function') renderTudo(); } catch (_) {}
    }
    function _stateStorageKey(mode) { return 'sismom_state_' + mode; }
    function _saveStateForMode(mode) {
        try { localStorage.setItem(_stateStorageKey(mode), JSON.stringify(_stateSnapshot())); } catch (_) {}
    }
    function _loadStateForMode(mode) {
        try {
            const raw = localStorage.getItem(_stateStorageKey(mode));
            if (raw) return JSON.parse(raw);
        } catch (_) {}
        return null;
    }

    function setAppMode(mode, opts) {
        if (mode !== 'png' && mode !== 'gtiff') return;
        if (mode === appMode) return;  // não faz nada se for o modo atual
        // Salva estado da aba que estamos saindo (para restaurar depois)
        try { _saveStateForMode(appMode); } catch (_) {}
        // Para animação em curso (timers são globais; precisam parar ao trocar de aba)
        try { if (state.animando && typeof pararAnimacao === 'function') pararAnimacao(); } catch (_) {}
        appMode = mode;
        try { localStorage.setItem('sismom_app_mode', mode); } catch (_) {}
        // Tabs visual
        document.querySelectorAll('.mode-tab').forEach(b => {
            const on = b.getAttribute('data-app-mode') === mode;
            b.classList.toggle('active', on);
            b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        // Carrega snapshot da nova aba, se existir
        const snap = _loadStateForMode(mode);
        if (snap) _stateRestore(snap);

        const mainPNG = document.getElementById('main-content');
        const mainGT  = document.getElementById('mainGT');
        const modal   = document.getElementById('modalGeoTIFF');
        if (mode === 'gtiff') {
            if (modal && mainGT && modal.parentNode !== mainGT) {
                _gtModalParent = modal.parentNode;
                mainGT.appendChild(modal);
            }
            if (modal) { modal.classList.add('inline'); modal.classList.add('open'); }
            if (mainPNG) mainPNG.style.display = 'none';
            if (mainGT)  mainGT.style.display  = '';
            gtLoadFromState().catch(() => {});
        } else {
            if (modal) {
                modal.classList.remove('inline');
                modal.classList.remove('open');
                if (_gtModalParent && modal.parentNode !== _gtModalParent) {
                    _gtModalParent.appendChild(modal);
                }
            }
            if (mainPNG) mainPNG.style.display = '';
            if (mainGT)  mainGT.style.display  = 'none';
        }
    }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    original = src
    if '_stateSnapshot' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor setAppMode = {src.count(OLD)}")
    new = src.replace(OLD, NEW, 1)
    if dry:
        print(f"[{path.name}] dry-run: {len(new)-len(src):+d} bytes")
        return True
    path.write_text(new, encoding='utf-8')
    print(f"[{path.name}] ok ({len(new)-len(src):+d})")
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

if __name__ == '__main__':
    main()
