#!/usr/bin/env python3
"""
Patch: atualizar selects da calculadora quando o TIF do slot ativo carrega.

gtRenderCalcSelects popula com gtAllLayers() (primary + extras). A primary
inclui gtLastDecoded como `decoded`; sem gtLastDecoded, a primary é
filtrada (`if (!l.decoded) continue`).

Quando o usuário troca para GeoTIFF, gtLastDecoded é setado dentro de
carregarGeoTIFFParaSlot quando o slot ativo termina de decodificar — mas
gtRenderCalcSelects não é chamado naquele ponto. Resultado: a camada
ativa não aparece nos selects da calculadora até que o usuário adicione
uma extra (que dispara o re-render).

Correção: chamar gtRenderCalcSelects junto com os outros refreshes da UI
do painel direito quando o slot ativo decodifica.
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
                // Atualiza painel direito (em particular, habilita "Mostrar mapa" agora que tem bbox)
                try { gtSyncRightPanelFromSlot(slotIdx); } catch (_) {}
            }'''
NEW = '''            gtSlotDecoded[slotIdx] = decoded;
            if (slotIdx === (gtActivePanel || 0)) {
                gtLastDecoded = decoded;
                try { gtAtualizarInfoEMinMax(decoded); } catch (_) {}
                try { gtDesenharColorbar(); } catch (_) {}
                try { gtRenderOverlayColorbars(); } catch (_) {}
                // Atualiza painel direito (em particular, habilita "Mostrar mapa" agora que tem bbox)
                try { gtSyncRightPanelFromSlot(slotIdx); } catch (_) {}
                // Re-popula selects da calculadora (primary agora tem decoded)
                try { gtRenderCalcSelects(); } catch (_) {}
                // Atualiza chips de camadas (mostra a primary com nome do arquivo atual)
                try { gtRenderLayerChips(); } catch (_) {}
            }'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if "Re-popula selects da calculadora (primary agora tem decoded)" in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False
    if src.count(OLD) != 1:
        raise RuntimeError(f"[{path.name}] anchor = {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    src = src.replace('20260528-0230-repopulate', '20260528-0250-calc')
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
        print("OK - " + str(len(a)) + " bytes em ambas - build 20260528-0250-calc")

if __name__ == '__main__':
    main()
