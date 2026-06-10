#!/usr/bin/env python3
"""Adiciona POST /v1/line/sample — amostragem de uma LINHA por leitura JANELADA
(/vsicurl): para cada item (raster de um nivel/passo), faz UMA leitura da janela
que cobre o bbox da linha e amostra os N pontos dela localmente. Ideal para corte
vertical e perfil ao longo da linha (L leituras/passo em vez de L*N).

Independente dos outros patches. USO:
    cd electron-app/python-helper
    python3 line_sample_patch.py            # aplica (backup server.py.bak_ls)
    python3 line_sample_patch.py --revert
"""
import sys, os, py_compile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "server.py")
BAK = F + ".bak_ls"
if "--revert" in sys.argv:
    if os.path.exists(BAK): shutil.copy2(BAK, F); print("revertido de", BAK)
    else: print("nada a reverter (sem .bak_ls)")
    sys.exit(0)
s = open(F, encoding="utf-8").read()
if "/v1/line/sample" in s:
    print("Patch ja aplicado (/v1/line/sample presente). Abortando."); sys.exit(0)

ANCHOR = '''@app.get("/v1/tile/fetch")
async def tile_fetch(url: str):'''
if s.count(ANCHOR) != 1:
    print("ABORTADO: ancora /v1/tile/fetch nao unica (", s.count(ANCHOR), "). Nada gravado."); sys.exit(2)

BLOCK = '''class LineSampleItem(BaseModel):
    url: str
    nivel: Optional[str] = None
    var: Optional[str] = None
    passo: Optional[int] = None
    rodada: Optional[str] = None


class LineSampleRequest(BaseModel):
    items: list[LineSampleItem]
    points: list[list[float]]   # [[lat,lon],...] JA densificados pelo frontend
    nodata_extras: Optional[list[float]] = None
    parallel_limit: int = Field(DEFAULT_PARALLEL, ge=1, le=32)


def _dl_sample_line(url, points, nodata_extras=None):
    """Le UMA janela (bbox dos pontos) do COG remoto via /vsicurl e amostra os
    pontos (nearest). Retorna lista alinhada a points (None onde nodata/fora)."""
    import math, rasterio
    from rasterio.windows import from_bounds, Window
    from rasterio.transform import rowcol
    n = len(points)
    out = [None] * n
    if n == 0:
        return out
    lats = [p[0] for p in points]; lons = [p[1] for p in points]
    minlat, maxlat = min(lats), max(lats); minlon, maxlon = min(lons), max(lons)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff",
                      GDAL_HTTP_MULTIRANGE="YES"):
        with rasterio.open("/vsicurl/" + url) as src:
            b = src.bounds
            wl = max(minlon, b.left); wr = min(maxlon, b.right)
            wb = max(minlat, b.bottom); wt = min(maxlat, b.top)
            if wr <= wl or wt <= wb:
                return out
            win = from_bounds(wl, wb, wr, wt, transform=src.transform)
            col0 = max(0, int(math.floor(win.col_off)))
            row0 = max(0, int(math.floor(win.row_off)))
            col1 = min(src.width, int(math.ceil(win.col_off + win.width)))
            row1 = min(src.height, int(math.ceil(win.row_off + win.height)))
            if col1 <= col0 or row1 <= row0:
                return out
            win2 = Window(col0, row0, col1 - col0, row1 - row0)
            arr = src.read(1, window=win2)
            wtf = src.window_transform(win2)
            nd = src.nodata
            H, W = arr.shape
            for k in range(n):
                lat, lon = points[k][0], points[k][1]
                if not (b.left <= lon <= b.right and b.bottom <= lat <= b.top):
                    continue
                r, c = rowcol(wtf, lon, lat)
                if 0 <= r < H and 0 <= c < W:
                    v = float(arr[r, c])
                    if (nd is not None and v == float(nd)) or math.isnan(v):
                        continue
                    if nodata_extras:
                        bad = False
                        for x in nodata_extras:
                            try:
                                if v == float(x):
                                    bad = True; break
                            except (TypeError, ValueError):
                                pass
                        if bad:
                            continue
                    out[k] = v
    return out


@app.post("/v1/line/sample")
async def line_sample(req: LineSampleRequest):
    """Amostra uma linha (corte vertical / perfil ao longo da linha) por leitura
    janelada. Cada item = 1 raster; resposta ecoa nivel/var/passo + 'values'
    (alinhado a points)."""
    t0 = time.time()
    pts = [(float(p[0]), float(p[1])) for p in req.points]
    sem = asyncio.Semaphore(req.parallel_limit)
    out = [None] * len(req.items)
    fetched = 0
    failed = 0

    async def worker(idx, it):
        nonlocal fetched, failed
        try:
            async with sem:
                vals = await asyncio.to_thread(_dl_sample_line, it.url, pts, req.nodata_extras)
            fetched += 1
        except Exception:
            vals = [None] * len(pts); failed += 1
        validade = None
        if it.rodada is not None and it.passo is not None:
            try:
                validade = _dl_validade(it.rodada, it.passo)
            except Exception:
                validade = None
        out[idx] = {"idx": idx, "nivel": it.nivel, "var": it.var, "passo": it.passo,
                    "rodada": it.rodada, "validade": validade, "values": vals}

    await asyncio.gather(*(worker(i, it) for i, it in enumerate(req.items)))
    return {"samples": out, "count": len(req.items), "npts": len(pts),
            "fetched": fetched, "failed": failed, "sampler": "vsicurl-window",
            "elapsed_seconds": round(time.time() - t0, 3),
            "parallel_limit_used": req.parallel_limit}


'''

s = s.replace(ANCHOR, BLOCK + ANCHOR)
shutil.copy2(F, BAK)
open(F, "w", encoding="utf-8").write(s)
try:
    py_compile.compile(F, doraise=True)
    print("OK — /v1/line/sample adicionado. Backup:", BAK)
except py_compile.PyCompileError as e:
    shutil.copy2(BAK, F); print("FALHA py_compile — revertido.", e); sys.exit(3)
