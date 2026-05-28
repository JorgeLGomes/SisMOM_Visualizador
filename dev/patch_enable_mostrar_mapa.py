#!/usr/bin/env python3
"""
Patch: habilitar checkbox "Mostrar mapa" após o slot ativo decodificar.

gtShowMap começa disabled. gtSyncRightPanelFromSlot atualiza disabled
baseado em gtSlotDecoded[slot].bbox. Mas é chamado apenas em
gtSelectPanel — que roda em setAppMode ANTES do TIF decodificar.

Solução: em carregarGeoTIFFParaSlot, quando o slot decodificado é o
gtActivePanel, chamar gtSyncRightPanelFromSlot pra refletir a nova
disponibilidade no painel direito.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

OLD = '''            gtSlotDecoded[slotIdx] = decoded;
            if (slotIdx === (gtActivePanel || 0)) {
                gtLastDecoded = decoded;
                try { gtAtualizarInfoEMinMax(decoded); } catch (_) {}
                try { gtDesenharColorbar(); } catch (_) {}
                try { gtRenderOverlayColorbars(); } catch (_) {}
            }'''
NEW = '''            gtSlotDecoded[slotIdx] = decoded;
            if (slotIdx === (gtActivePanel || 0)) {
                gtLastDecoded = decoded;
                try { gtAtualizarInfoEMinMax(decoded); } catch (_) {}
                try { gtDesenharColorbar(); } catch (_) {}
                try { gtRenderOverlayColorbars(); } catch (_) {}
                // Atualiza painel direito (em particular, habilita "Mostrar mapa" agora que tem bbox)
                try { gtSyncRightPanelFromSlot(slotIdx); } catch (_) {}
            }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if "Atualiza painel direito (em particular, habilita" in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    src = src.replace('20260528-0150-defpng', '20260528-0200-mapenable')
    if dry: print(f"[{path.name}] dry-run"); return True
    path.write_text(src, encoding='utf-8')
    print(f"[{path.name}] ok")
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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0200-mapenable")

if __name__ == '__main__':
    main()
