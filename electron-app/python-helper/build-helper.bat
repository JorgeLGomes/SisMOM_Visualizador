@echo off
REM Build do gisele-python-helper.exe via PyInstaller.
REM Saida: python-helper\dist\gisele-python-helper.exe
REM
REM Pre-requisitos:
REM   - Python 3.11+ instalado e no PATH
REM   - pip install -r requirements.txt && pip install pyinstaller

setlocal
cd /d "%~dp0"

echo.
echo === Limpando builds anteriores ===
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist gisele-python-helper.spec del /Q gisele-python-helper.spec

echo.
echo === Verificando dependencias ===
python -c "import fastapi, uvicorn, httpx, rasterio, numpy" 2>nul
if errorlevel 1 (
    echo ERRO: instale as dependencias primeiro:
    echo   pip install -r requirements.txt
    echo   pip install pyinstaller
    pause
    exit /b 1
)

echo.
echo === Buildando gisele-python-helper.exe ===
pyinstaller --onefile --name gisele-python-helper ^
    --console ^
    --hidden-import=rasterio ^
    --hidden-import=rasterio.sample ^
    --hidden-import=rasterio._shim ^
    --hidden-import=rasterio.vrt ^
    --hidden-import=rasterio._features ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=uvicorn.loops ^
    --hidden-import=uvicorn.loops.auto ^
    --hidden-import=uvicorn.protocols ^
    --hidden-import=uvicorn.protocols.http ^
    --hidden-import=uvicorn.protocols.http.auto ^
    --hidden-import=uvicorn.protocols.websockets ^
    --hidden-import=uvicorn.protocols.websockets.auto ^
    --hidden-import=uvicorn.lifespan ^
    --hidden-import=uvicorn.lifespan.on ^
    --hidden-import=orjson ^
    --collect-submodules rasterio ^
    server.py

if errorlevel 1 (
    echo ERRO no PyInstaller.
    pause
    exit /b 1
)

echo.
echo === Saidas ===
dir /b dist\
echo.
echo OK: dist\gisele-python-helper.exe pronto.
echo.
echo Proximo passo:
echo   cd ..
echo   npm run dist:win    (empacota com electron-builder)
echo.
pause
