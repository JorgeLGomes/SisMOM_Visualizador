#!/usr/bin/env bash
# Build do gisele-python-helper via PyInstaller (Linux/Mac).
# Saida: python-helper/dist/gisele-python-helper

set -e
cd "$(dirname "$0")"

echo "=== Limpando builds anteriores ==="
rm -rf build dist gisele-python-helper.spec

echo
echo "=== Verificando dependencias ==="
python3 -c "import fastapi, uvicorn, httpx, rasterio, numpy" 2>/dev/null || {
    echo "ERRO: instale as dependencias primeiro:"
    echo "  pip install -r requirements.txt"
    echo "  pip install pyinstaller"
    exit 1
}

echo
echo "=== Buildando gisele-python-helper ==="
pyinstaller --onefile --name gisele-python-helper \
    --console \
    --hidden-import=rasterio \
    --hidden-import=rasterio.sample \
    --hidden-import=rasterio._shim \
    --hidden-import=rasterio.vrt \
    --hidden-import=rasterio._features \
    --hidden-import=uvicorn.logging \
    --hidden-import=uvicorn.loops.auto \
    --hidden-import=uvicorn.protocols.http.auto \
    --hidden-import=uvicorn.protocols.websockets.auto \
    --hidden-import=uvicorn.lifespan.on \
    --hidden-import=orjson \
    --collect-submodules rasterio \
    server.py

echo
echo "=== Saidas ==="
ls -la dist/

echo
echo "OK: dist/gisele-python-helper pronto."
