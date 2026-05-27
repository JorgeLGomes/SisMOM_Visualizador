#!/usr/bin/env python3
"""
Patch: adiciona 10 paletas científicas extras ao GT_PALETTES.
- Plasma, Inferno, Magma, Cividis (matplotlib)
- Spectral, RdYlBu, BrBG (divergentes ColorBrewer)
- Terrain, Ocean (relevo/batimetria)
- Seismic, Coolwarm (anomalias divergentes)
Estende os <select> da paleta no modal local e na toolbar.
"""
import sys
from pathlib import Path

ROOT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador')
FILES = [ROOT / 'figuras_SisMOM_v23.html', ROOT / 'electron-app' / 'figuras_SisMOM_v23.html']

# (1) GT_PALETTES: adicionar novas paletas
OLD_PAL = '''        const GT_PALETTES = {
            viridis: makeRamp([[68,1,84],[72,35,116],[64,67,135],[52,94,141],[41,120,142],[32,144,140],[34,167,132],[68,190,112],[121,209,81],[189,222,38],[253,231,36]]),
            jet:     makeRamp([[0,0,131],[0,60,170],[5,255,255],[255,255,0],[250,0,0],[128,0,0]]),
            rdbu:    makeRamp([[5,48,97],[33,102,172],[67,147,195],[146,197,222],[209,229,240],[247,247,247],[253,219,199],[244,165,130],[214,96,77],[178,24,43],[103,0,31]]),
            gray:    makeRamp([[0,0,0],[255,255,255]]),
            turbo:   makeRamp([[48,18,59],[70,107,227],[40,191,224],[70,250,162],[186,252,67],[255,192,33],[243,95,30],[165,25,8],[122,4,3]])
        };'''
NEW_PAL = '''        const GT_PALETTES = {
            viridis:  makeRamp([[68,1,84],[72,35,116],[64,67,135],[52,94,141],[41,120,142],[32,144,140],[34,167,132],[68,190,112],[121,209,81],[189,222,38],[253,231,36]]),
            plasma:   makeRamp([[13,8,135],[75,3,161],[125,3,168],[168,34,150],[203,71,119],[230,107,90],[248,149,64],[253,195,40],[240,249,33]]),
            inferno:  makeRamp([[0,0,4],[40,11,84],[101,21,110],[159,42,99],[212,72,66],[245,125,21],[250,193,39],[252,255,164]]),
            magma:    makeRamp([[0,0,4],[40,11,84],[101,21,110],[158,47,127],[212,80,121],[247,137,118],[253,201,141],[252,253,191]]),
            cividis:  makeRamp([[0,32,76],[24,59,107],[55,86,118],[87,113,123],[122,142,128],[160,172,130],[202,202,127],[244,234,80],[253,231,37]]),
            jet:      makeRamp([[0,0,131],[0,60,170],[5,255,255],[255,255,0],[250,0,0],[128,0,0]]),
            turbo:    makeRamp([[48,18,59],[70,107,227],[40,191,224],[70,250,162],[186,252,67],[255,192,33],[243,95,30],[165,25,8],[122,4,3]]),
            rdbu:     makeRamp([[5,48,97],[33,102,172],[67,147,195],[146,197,222],[209,229,240],[247,247,247],[253,219,199],[244,165,130],[214,96,77],[178,24,43],[103,0,31]]),
            rdylbu:   makeRamp([[165,0,38],[215,48,39],[244,109,67],[253,174,97],[254,224,144],[255,255,191],[224,243,248],[171,217,233],[116,173,209],[69,117,180],[49,54,149]]),
            spectral: makeRamp([[158,1,66],[213,62,79],[244,109,67],[253,174,97],[254,224,139],[255,255,191],[230,245,152],[171,221,164],[102,194,165],[50,136,189],[94,79,162]]),
            brbg:     makeRamp([[84,48,5],[140,81,10],[191,129,45],[223,194,125],[246,232,195],[245,245,245],[199,234,229],[128,205,193],[53,151,143],[1,102,94],[0,60,48]]),
            seismic:  makeRamp([[0,0,76],[0,0,255],[127,127,255],[255,255,255],[255,127,127],[255,0,0],[127,0,0]]),
            coolwarm: makeRamp([[59,76,192],[123,165,228],[197,222,233],[221,221,221],[240,200,166],[225,128,108],[180,4,38]]),
            terrain:  makeRamp([[51,51,153],[38,128,179],[126,179,77],[217,179,77],[128,77,51],[230,210,180],[255,255,255]]),
            ocean:    makeRamp([[0,0,0],[0,40,127],[0,90,140],[40,127,140],[127,170,127],[191,212,153],[255,255,255]]),
            gray:     makeRamp([[0,0,0],[255,255,255]])
        };'''

# (2) Estender <select id="gtPaleta"> com todas as paletas
OLD_SEL = '''<select id="gtPaleta">
                        <option value="viridis" selected>Viridis</option>
                        <option value="jet">Jet</option>
                        <option value="rdbu">RdBu</option>
                        <option value="gray">Cinza</option>
                        <option value="turbo">Turbo</option>
                    </select>'''
NEW_SEL = '''<select id="gtPaleta">
                        <optgroup label="Sequenciais (matplotlib)">
                            <option value="viridis" selected>Viridis</option>
                            <option value="plasma">Plasma</option>
                            <option value="inferno">Inferno</option>
                            <option value="magma">Magma</option>
                            <option value="cividis">Cividis</option>
                        </optgroup>
                        <optgroup label="Sequenciais clássicas">
                            <option value="jet">Jet</option>
                            <option value="turbo">Turbo</option>
                            <option value="gray">Cinza</option>
                        </optgroup>
                        <optgroup label="Divergentes (anomalia)">
                            <option value="rdbu">RdBu (vermelho–azul)</option>
                            <option value="rdylbu">RdYlBu</option>
                            <option value="spectral">Spectral</option>
                            <option value="brbg">BrBG (marrom–verde)</option>
                            <option value="seismic">Seismic</option>
                            <option value="coolwarm">Coolwarm</option>
                        </optgroup>
                        <optgroup label="Topográficas">
                            <option value="terrain">Terrain</option>
                            <option value="ocean">Ocean</option>
                        </optgroup>
                    </select>'''


def patch_file(path: Path, dry=False):
    src = path.read_text(encoding='utf-8')
    if 'plasma:' in src and 'cividis:' in src:
        print(f"[{path.name}] já patcheado; pulando.")
        return False

    def rep(h, o, n, label):
        c = h.count(o)
        if c != 1: raise RuntimeError(f"[{path.name}] anchor '{label}' = {c}")
        return h.replace(o, n, 1)

    src = rep(src, OLD_PAL, NEW_PAL, 'GT_PALETTES extras')
    src = rep(src, OLD_SEL, NEW_SEL, 'select gtPaleta optgroups')

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
        print("OK - " + str(len(a)) + " bytes em ambas")

if __name__ == '__main__':
    main()
