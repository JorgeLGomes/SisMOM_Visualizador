#!/usr/bin/env python3
"""Adiciona GET /v1/tile/window — recorta a JANELA (bbox) do GeoTIFF remoto via
/vsicurl (leitura janelada) e devolve os bytes do .tif recortado (em memoria).
Reaproveita a 'ferramenta de requisicao de box': mesma logica do _dl_clip_tif,
mas retorna os bytes em vez de salvar em disco — para o viewer exibir o recorte.

Independente. USO (na maquina com o server.py completo):
    cd electron-app/python-helper
    python3 window_patch.py            # aplica (backup server.py.bak_win)
    python3 window_patch.py --revert
"""
import sys, os, py_compile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "server.py")
BAK = F + ".bak_win"
if "--revert" in sys.argv:
    if os.path.exists(BAK): shutil.copy2(BAK, F); print("revertido de", BAK)
    else: print("nada a reverter (sem .bak_win)")
    sys.exit(0)
s = open(F, encoding="utf-8").read()
if "/v1/tile/window" in s:
    print("Patch ja aplicado (/v1/tile/window presente). Abortando."); sys.exit(0)
ANCHOR = '''@app.get("/v1/tile/fetch")
async def tile_fetch(url: str):'''
if s.count(ANCHOR) != 1:
    print("ABORTADO: ancora /v1/tile/fetch nao unica (", s.count(ANCHOR), ")."); sys.exit(2)

BLOCK = '''def _dl_clip_tif_bytes(url, bbox):
    """Recorta a janela bbox=[W,S,E,N] (graus) do COG remoto via /vsicurl e
    retorna os bytes do GeoTIFF recortado (em memoria). None-safe: lanca se o
    bbox nao intersecta a cobertura."""
    import rasterio
    from rasterio.windows import from_bounds, Window
    from rasterio.io import MemoryFile
    env_opts = {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.tiff",
        "GDAL_HTTP_MULTIRANGE": "YES",
    }
    with rasterio.Env(**env_opts):
        with rasterio.open("/vsicurl/" + url) as src:
            b = src.bounds
            wl = max(bbox[0], b.left); wr = min(bbox[2], b.right)
            wb = max(bbox[1], b.bottom); wt = min(bbox[3], b.top)
            if wr <= wl or wt <= wb:
                raise RuntimeError("bbox fora da cobertura do arquivo")
            w = from_bounds(wl, wb, wr, wt, transform=src.transform)
            col0 = max(0, int(w.col_off)); row0 = max(0, int(w.row_off))
            col1 = min(src.width, int(w.col_off + w.width) + 1)
            row1 = min(src.height, int(w.row_off + w.height) + 1)
            if col1 <= col0 or row1 <= row0:
                raise RuntimeError("janela vazia")
            win = Window(col0, row0, col1 - col0, row1 - row0)
            data = src.read(window=win)
            prof = src.profile.copy()
            prof.update(driver="GTiff", width=int(win.width), height=int(win.height),
                        transform=src.window_transform(win), compress="deflate",
                        tiled=True, blockxsize=256, blockysize=256)
            with MemoryFile() as mem:
                with mem.open(**prof) as dst:
                    dst.write(data)
                return mem.read()


@app.get("/v1/tile/window")
async def tile_window(url: str, bbox: str):
    """Recorta o GeoTIFF remoto ao bbox (graus, "W,S,E,N") e devolve o .tif
    recortado. O viewer busca isso, decodifica e exibe so o trecho visivel."""
    try:
        parts = [float(x) for x in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError()
    except Exception:
        raise HTTPException(400, "bbox invalido — use W,S,E,N (graus)")
    try:
        content = await asyncio.to_thread(_dl_clip_tif_bytes, url, parts)
    except Exception as e:
        raise HTTPException(502, f"window err: {e}")
    return Response(content=content, media_type="image/tiff",
                    headers={"Cache-Control": "no-cache", "X-Gisele-Window": "1"})


'''

s = s.replace(ANCHOR, BLOCK + ANCHOR)
shutil.copy2(F, BAK)
open(F, "w", encoding="utf-8").write(s)
try:
    py_compile.compile(F, doraise=True)
    print("OK — /v1/tile/window adicionado. Backup:", BAK)
except py_compile.PyCompileError as e:
    shutil.copy2(BAK, F); print("FALHA py_compile — revertido.", e); sys.exit(3)
