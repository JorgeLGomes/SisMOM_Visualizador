#!/usr/bin/env python3
"""POC v2.15 — amostragem por /vsicurl (range-read) no /v1/timeseries/point.

Aplica, de forma ADITIVA e segura, o sampler por leitura janelada (range request)
ao endpoint /v1/timeseries/point do helper. Não altera o comportamento padrão:
só age quando a requisição manda use_vsicurl=true.

USO (na máquina onde está o server.py completo):
    cd electron-app/python-helper
    python3 poc_vsicurl_patch.py            # aplica (gera server.py.bak)
    python3 poc_vsicurl_patch.py --revert   # desfaz (restaura do .bak)

O script faz backup, valida com py_compile e aborta sem gravar se algum
trecho-âncora não casar exatamente (protege contra aplicar em arquivo errado).
"""
import sys, os, py_compile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "server.py")
BAK = F + ".bak"

if "--revert" in sys.argv:
    if os.path.exists(BAK):
        shutil.copy2(BAK, F); print(f"revertido de {BAK}")
    else:
        print("nada a reverter (sem .bak)")
    sys.exit(0)

s = open(F, encoding="utf-8").read()

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n:
        print(f"ABORTADO [{label}]: ocorrencias={c} (esperado {n}). Nada gravado.")
        sys.exit(2)
    s = s.replace(old, new)
    print(f"  ok [{label}]")

if "use_vsicurl" in s:
    print("Patch ja parece aplicado (use_vsicurl presente). Abortando."); sys.exit(0)

# 1) _dl_sample_tif aceita nodata_extras + GDAL_HTTP_MULTIRANGE
rep(
'''def _dl_sample_tif(url: str, point: list) -> Optional[float]:
    """Amostra um GeoTIFF/COG remoto em (lat, lon). Em COG via /vsicurl o GDAL
    busca apenas o(s) tile(s) do pixel — bytes mínimos. None se nodata/fora."""
    import math
    import rasterio
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff"):
        with rasterio.open("/vsicurl/" + url) as src:
            lat, lon = float(point[0]), float(point[1])
            b = src.bounds
            if not (b.left <= lon <= b.right and b.bottom <= lat <= b.top):
                return None
            for val in src.sample([(lon, lat)]):
                v = float(val[0])
                nd = src.nodata
                if (nd is not None and v == float(nd)) or math.isnan(v):
                    return None
                return v
    return None''',
'''def _dl_sample_tif(url: str, point: list, nodata_extras: Optional[list] = None) -> Optional[float]:
    """Amostra um GeoTIFF/COG remoto em (lat, lon). Em COG via /vsicurl o GDAL
    busca apenas o(s) tile(s) do pixel — bytes mínimos. None se nodata/fora.
    nodata_extras: sentinelas adicionais (ex.: -2.56e33, -9999) -> None."""
    import math
    import rasterio
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff",
                      GDAL_HTTP_MULTIRANGE="YES"):
        with rasterio.open("/vsicurl/" + url) as src:
            lat, lon = float(point[0]), float(point[1])
            b = src.bounds
            if not (b.left <= lon <= b.right and b.bottom <= lat <= b.top):
                return None
            for val in src.sample([(lon, lat)]):
                v = float(val[0])
                nd = src.nodata
                if (nd is not None and v == float(nd)) or math.isnan(v):
                    return None
                if nodata_extras:
                    for _x in nodata_extras:
                        try:
                            if v == float(_x):
                                return None
                        except (TypeError, ValueError):
                            pass
                return v
    return None''',
"_dl_sample_tif")

# 2) campo use_vsicurl no request
rep(
'''    passoMax: Optional[int] = Field(None, ge=1,
                                    description="Ultimo passo em HORAS (opcional). Padrao: horizonte completo.")


class TimeSeriesSample(BaseModel):''',
'''    passoMax: Optional[int] = Field(None, ge=1,
                                    description="Ultimo passo em HORAS (opcional). Padrao: horizonte completo.")
    use_vsicurl: bool = Field(False,
                              description="POC: amostra por range-read (/vsicurl) em vez de baixar o TIF inteiro.")


class TimeSeriesSample(BaseModel):''',
"use_vsicurl-field")

# 3) sampler async (rasterio bloqueante -> thread)
rep(
'''def _resolve_steps(freq: int, horizonte: Optional[int], max_passos: int) -> list[int]:''',
'''async def _vsicurl_sample_async(url, lat, lon, nodata_extras=None):
    """POC: amostra 1 ponto por range-read (/vsicurl), sem baixar o TIF inteiro.
    Roda o rasterio (bloqueante) num thread para nao travar o event loop."""
    try:
        v = await asyncio.to_thread(_dl_sample_tif, url, [lat, lon], nodata_extras)
        return (v, None)
    except Exception as e:
        return (None, f"vsicurl_err: {e}")


def _resolve_steps(freq: int, horizonte: Optional[int], max_passos: int) -> list[int]:''',
"_vsicurl_sample_async")

# 4) branch no worker
rep(
'''                v_val, err = await _fetch_and_sample(client, url, req.lat, req.lon, req.nodata_extras)''',
'''                if req.use_vsicurl:
                    v_val, err = await _vsicurl_sample_async(url, req.lat, req.lon, req.nodata_extras)
                else:
                    v_val, err = await _fetch_and_sample(client, url, req.lat, req.lon, req.nodata_extras)''',
"worker-branch")

# 5) campo 'sampler' na resposta
rep(
'''        "parallel_limit_used": req.parallel_limit,
    }
    return resp_obj''',
'''        "parallel_limit_used": req.parallel_limit,
        "sampler": "vsicurl" if req.use_vsicurl else "full-download",
    }
    return resp_obj''',
"response-sampler")

shutil.copy2(F, BAK)
open(F, "w", encoding="utf-8").write(s)
try:
    py_compile.compile(F, doraise=True)
    print(f"\nOK — patch aplicado. Backup em {BAK}")
    print("Reinicie o helper. Teste: POST /v1/timeseries/point com use_vsicurl=true.")
    print("Rollback: python3 poc_vsicurl_patch.py --revert")
except py_compile.PyCompileError as e:
    shutil.copy2(BAK, F)
    print(f"\nFALHA py_compile — revertido. {e}")
    sys.exit(3)
