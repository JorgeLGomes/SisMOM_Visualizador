#!/usr/bin/env python3
"""Adiciona o endpoint GENERICO POST /v1/point/series (amostragem por ponto via
range-read /vsicurl). A MESMA rota atende serie/evolucao temporal (variando passo),
perfil vertical (variando nivel) e SkewT (variando var x nivel).

Independente do poc_vsicurl_patch.py: usa o _dl_sample_tif que ja existe.

USO (na maquina com o server.py completo):
    cd electron-app/python-helper
    python3 point_series_patch.py            # aplica (gera server.py.bak_ps)
    python3 point_series_patch.py --revert   # restaura do .bak_ps
"""
import sys, os, py_compile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "server.py")
BAK = F + ".bak_ps"

if "--revert" in sys.argv:
    if os.path.exists(BAK):
        shutil.copy2(BAK, F); print("revertido de", BAK)
    else:
        print("nada a reverter (sem .bak_ps)")
    sys.exit(0)

s = open(F, encoding="utf-8").read()
if "/v1/point/series" in s:
    print("Patch ja aplicado (/v1/point/series presente). Abortando."); sys.exit(0)

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n:
        print(f"ABORTADO [{label}]: ocorrencias={c} (esperado {n}). Nada gravado."); sys.exit(2)
    s = s.replace(old, new)
    print(f"  ok [{label}]")

# 1) Modelos (apos TimeSeriesSample)
rep(
'''class TimeSeriesSample(BaseModel):
    idx: int
    passo_h: int
    time_utc: Optional[str] = None
    value: Optional[float] = None''',
'''class TimeSeriesSample(BaseModel):
    idx: int
    passo_h: int
    time_utc: Optional[str] = None
    value: Optional[float] = None


class PointSeriesItem(BaseModel):
    url: str
    passo: Optional[int] = None      # horas -> eixo TEMPO (serie/evolucao)
    nivel: Optional[str] = None      # hPa  -> eixo VERTICAL (perfil/SkewT)
    var: Optional[str] = None        # rotulo da variavel (SkewT: T, Td, ...)
    rodada: Optional[str] = None     # AAAAMMDDHH -> validade


class PointSeriesRequest(BaseModel):
    items: list[PointSeriesItem]
    lat: float
    lon: float
    nodata_extras: Optional[list[float]] = None
    parallel_limit: int = Field(DEFAULT_PARALLEL, ge=1, le=32,
                                description="Leituras de ponto concorrentes")''',
"models")

# 2) Endpoint + sampler (antes do /v1/timeseries/point/geojson)
rep(
'''@app.post("/v1/timeseries/point/geojson")
async def timeseries_point_geojson(req: TimeSeriesPointRequest):''',
'''async def _ps_sample_async(url, lat, lon, nodata_extras=None):
    """Amostra 1 ponto por range-read (/vsicurl). Independente do POC: usa o
    _dl_sample_tif existente (2 args) e checa nodata_extras aqui."""
    def _do():
        v = _dl_sample_tif(url, [lat, lon])
        if v is not None and nodata_extras:
            for _x in nodata_extras:
                try:
                    if v == float(_x):
                        return None
                except (TypeError, ValueError):
                    pass
        return v
    try:
        return (await asyncio.to_thread(_do), None)
    except Exception as e:
        return (None, f"vsicurl_err: {e}")


@app.post("/v1/point/series")
async def point_series(req: PointSeriesRequest):
    """Amostragem GENERICA por ponto via range-read (/vsicurl).

    O frontend manda a lista de itens (cada um = 1 URL) + o ponto. Variando os
    campos, a MESMA rota atende:
      - serie / evolucao temporal -> itens variam 'passo'
      - perfil vertical           -> itens variam 'nivel'
      - SkewT-LogP                -> itens variam 'var' (T, Td) x 'nivel'
    Le so o(s) tile(s) do pixel; a resposta ecoa os campos do item + 'value'.
    """
    t0 = time.time()
    sem = asyncio.Semaphore(req.parallel_limit)
    out: list = [None] * len(req.items)
    fetched = 0
    failed = 0

    async def worker(idx: int, it: PointSeriesItem):
        nonlocal fetched, failed
        async with sem:
            v, err = await _ps_sample_async(it.url, req.lat, req.lon, req.nodata_extras)
        if err:
            failed += 1
        else:
            fetched += 1
        validade = None
        if it.rodada is not None and it.passo is not None:
            try:
                validade = _dl_validade(it.rodada, it.passo)
            except Exception:
                validade = None
        out[idx] = {
            "idx": idx, "passo": it.passo, "nivel": it.nivel,
            "var": it.var, "rodada": it.rodada, "validade": validade,
            "value": v, "error": err,
        }

    await asyncio.gather(*(worker(i, it) for i, it in enumerate(req.items)))
    return {
        "samples": out,
        "lat": req.lat, "lon": req.lon,
        "count": len(req.items), "fetched": fetched, "failed": failed,
        "sampler": "vsicurl",
        "elapsed_seconds": round(time.time() - t0, 3),
        "parallel_limit_used": req.parallel_limit,
    }


@app.post("/v1/timeseries/point/geojson")
async def timeseries_point_geojson(req: TimeSeriesPointRequest):''',
"endpoint")

shutil.copy2(F, BAK)
open(F, "w", encoding="utf-8").write(s)
try:
    py_compile.compile(F, doraise=True)
    print("\nOK — /v1/point/series adicionado. Backup:", BAK)
    print("Reinicie o helper. Rollback: python3 point_series_patch.py --revert")
except py_compile.PyCompileError as e:
    shutil.copy2(BAK, F); print("\nFALHA py_compile — revertido.", e); sys.exit(3)
