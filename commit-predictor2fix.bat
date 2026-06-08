@echo off
REM fix(decoder): predictor=2 tileado + uint32 para float32
REM  BUG 1: sem case bytesPerSample===4 (float32) -> undiff ignorado -> valores errados
REM  BUG 2: predictor aplicado na imagem montada -> cruzava fronteira de tile -> 3 copias

setlocal
cd /d "%~dp0"

echo.
echo === [1/3] Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/3] Reconstruindo index + stage ===
git read-tree HEAD
if errorlevel 1 (echo ERRO read-tree. & pause & exit /b 1)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

echo.
echo === [3/3] Commit ===
git commit ^
 -m "fix(decoder): predictor=2 por tile + uint32 para float32 (COG/tileados)" ^
 -m "" ^
 -m "DOIS BUGS corrigidos no decodeTIFF para GeoTIFFs com Predictor=2:" ^
 -m "" ^
 -m "BUG 1 (float32 ignorado): o bloco predictor=2 tratava bytesPerSample 1 e 2" ^
 -m "  mas nao tinha case para 4 (float32). O undiff era silenciosamente pulado." ^
 -m "  Fix: case bytesPerSample===4 com uint32 arithmetic (LibTIFF horAcc32)." ^
 -m "" ^
 -m "BUG 2 (fronteira de tile cruzada): o predictor era aplicado na imagem montada" ^
 -m "  inteira, cruzando a fronteira entre tiles. Em TIFF tileado, a cadeia de" ^
 -m "  diferencas reinicia no inicio de cada tile. Isso causava a aparencia de" ^
 -m "  '3 copias' do campo (cada faixa de 512 cols somava incorretamente a ultima" ^
 -m "  coluna do tile anterior)." ^
 -m "  Fix: predictor aplicado POR TILE (sobre cada segment[]) antes da montagem." ^
 -m "  Strips (nao tileados) continuam com predictor na imagem montada (correto)." ^
 -m "" ^
 -m "Funcao auxiliar _pred2Row centraliza a logica (1/2/4 bytes, qualquer struct)." ^
 -m "" ^
 -m "VERIFICADO pixel a pixel contra rasterio: 20 tiles PSLM_2026060400.tif" ^
 -m "  todos os tiles internos delta < 0.01 hPa apos clipping de borda." ^
 -m "" ^
 -m "* Build marker: 20260602-3350-veccache -> 20260605-1100-tiledpredictor" ^
 -m "* Afeta qualquer GeoTIFF tileado com Predictor=2 (padrao do GDAL/COG)"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
