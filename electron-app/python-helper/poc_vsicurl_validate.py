#!/usr/bin/env python3
"""Valida, contra um TIF REAL, se a leitura por range-request (/vsicurl) e viavel.

Passo decisivo da Fase 1: se o servidor de dados aceitar HTTP Range, o sampler
por ponto le so o tile do pixel (poucos KB) em vez do arquivo inteiro.

USO:
    python3 poc_vsicurl_validate.py "https://host/.../arquivo.tif" [lat lon]
    CPL_DEBUG=ON python3 poc_vsicurl_validate.py "<url>" 2>&1 | grep -i vsicurl
"""
import sys, subprocess

if len(sys.argv) < 2:
    print(__doc__); sys.exit(1)
URL = sys.argv[1]
lat = float(sys.argv[2]) if len(sys.argv) > 3 else None
lon = float(sys.argv[3]) if len(sys.argv) > 3 else None

print("== 1) Servidor aceita HTTP Range? ==")
try:
    out = subprocess.run(["curl", "-sI", "-H", "Range: bytes=0-1023", URL],
                         capture_output=True, text=True, timeout=30).stdout
    print(out.strip() or "(sem cabecalhos)")
    low = out.lower()
    first = out.splitlines()[0] if out.splitlines() else ""
    has_range = ("206" in first) or ("content-range" in low) or ("accept-ranges: bytes" in low)
    if has_range:
        print("=> RANGE SUPORTADO -- leitura janelada eficiente.")
    else:
        print("=> RANGE NAO detectado -- /vsicurl baixaria o arquivo inteiro (sem ganho).")
except Exception as e:
    print("curl falhou:", e)

print("")
print("== 2) GDAL /vsicurl: abre e amostra so o(s) tile(s) ==")
try:
    import rasterio
    is_tiled = False
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff",
                      GDAL_HTTP_MULTIRANGE="YES"):
        with rasterio.open("/vsicurl/" + URL) as src:
            is_tiled = bool(src.profile.get("tiled"))
            print("  tiled :", src.profile.get("tiled"),
                  "| block:", src.block_shapes[:1],
                  "| size:", str(src.width) + "x" + str(src.height),
                  "| dtype:", src.dtypes[0],
                  "| nodata:", src.nodata)
            b = src.bounds
            print("  bounds: W=%.3f S=%.3f E=%.3f N=%.3f" % (b.left, b.bottom, b.right, b.top))
            if lat is None:
                lat = (b.bottom + b.top) / 2.0
                lon = (b.left + b.right) / 2.0
            inside = (b.left <= lon <= b.right and b.bottom <= lat <= b.top)
            print("  amostra lat=%.3f lon=%.3f (dentro=%s):" % (lat, lon, inside))
            if inside:
                for val in src.sample([(lon, lat)]):
                    print("    valor =", float(val[0]))
    if is_tiled:
        print("  OK: arquivo e tiled -- favoravel a leitura janelada.")
    else:
        print("  AVISO: arquivo NAO e tiled -- gere COG (tiled+overviews) p/ range reads finos.")
except Exception as e:
    print("  rasterio/vsicurl falhou:", e)

print("")
print("Dica: para CONTAR os bytes lidos, rode com CPL_DEBUG=ON e veja as linhas VSICURL.")
print("")
print("== 3) Benchmark A/B do endpoint (payload.json com modelo/variavel do frontend) ==")
print("  Atual  : POST /v1/timeseries/point com o payload (full-download).")
print("  POC    : mesmo payload + use_vsicurl:true (range-read).")
print("  A resposta traz os campos 'sampler' e 'elapsed_seconds' para comparar.")
