@echo off
REM Commit v2.13.0 GISELE - sessao 05/06/2026
REM   Novidades: METAR, Spatial Bookmarks, PDF export, Serie temporal por
REM   poligono, Web Worker decode pool, cache de bitmaps, base de pontos,
REM   botoes Limpar/Visualizar, docs atualizados.

setlocal
cd /d "%~dp0"

echo.
echo === [1/6] Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\index_new.lock) do (
    if exist "%%F" ( del /F /Q "%%F" 2>nul & if exist "%%F" (echo AVISO: nao removeu %%F) else (echo OK: %%F removido.) )
)

echo.
echo === [2/6] Reconstruindo o index a partir do HEAD ===
git read-tree HEAD
if errorlevel 1 (echo ERRO ao reconstruir o index. & pause & exit /b 1)

echo.
echo === [3/6] Stage de todos os arquivos v2.13.0 ===
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html
git add electron-app/python-helper/server.py
git add electron-app/package.json electron-app/package-lock.json
git add miscelaneas/estacoes_metar.json miscelaneas/estacoes_metar_br.csv miscelaneas/pontos_exemplo.csv
git add electron-app/miscelaneas/estacoes_metar.json electron-app/miscelaneas/estacoes_metar_br.csv
git add ADEQUACAO_COPERNICUS.md docs/ADEQUACAO_COPERNICUS.pdf
git add metar_station_model_preview.html
git add HANDOVER_GISELE.md RESUMO_RETOMAR.md docs/RELEASE_NOTES.md
git add vendor/leaflet.css SisMOM.bat organizar-git.bat commit-v2.13.0.bat

echo.
echo === Status pre-commit ===
git update-index --refresh > nul 2>&1
git status --short

echo.
echo === [4/6] Commit v2.13.0 ===
git commit ^
 -m "v2.13.0 GISELE: METAR + Spatial Bookmarks + PDF export + serie temporal por poligono + Web Worker decode + cache bitmaps" ^
 -m "" ^
 -m "METAR:" ^
 -m "  - Base default metar_br no Monitoramento: API aviationweather.gov, decoder proprio" ^
 -m "    gtDecodeMETAR (T, Td, umidade, vento, visibilidade, nuvens, teto, QNH, tempo presente)" ^
 -m "  - Station model visual escalado por zoom (drawStationModel): cobertura, barbulas de" ^
 -m "    vento (kt), T/Td vermelha/verde, pressao, ICAO -- path, nao emoji (Electron/Chromium)" ^
 -m "  - 251 estacoes BR + Am. Sul/Central/Caribe em miscelaneas/estacoes_metar.json" ^
 -m "  - gtMetarFilterSelection / gtMetarApplyFilter / gtMetarRebuildIndex" ^
 -m "" ^
 -m "SPATIAL BOOKMARKS (botao no header):" ^
 -m "  - gtBmkAddCurrent: captura viewport M1 + modelo/variavel/passo + camadas + paineis" ^
 -m "  - gtBmkRestore: restaura viewport, modelo, visibilidade de camadas por _gtBmkLayerKey" ^
 -m "  - Topics/categorias; localStorage gisele.bookmarks.v1" ^
 -m "" ^
 -m "EXPORTAR PDF CARTOGRAFICO (botao PDF no header):" ^
 -m "  - gtExportMapComposePDF: canvas JPEG + legenda + seta-norte + barra de escala" ^
 -m "  - PDF-1.4 puro JS sem libs externas (_gtJpegToPdf, _gtPdfLegend, _gtPdfNorth, _gtPdfScale)" ^
 -m "" ^
 -m "SERIE TEMPORAL POR POLIGONO:" ^
 -m "  - gtSamplePolygonTimeSeries: max/min/mean ponderado por area por passo de tempo" ^
 -m "  - _gtPolygonCellIndices + _gtAggregateInPolys; cache dedicado _gtTsRasterCache ~1GB LRU" ^
 -m "  - Python helper: endpoint /v1/timeseries/polygon com mascara NumPy (zonal_stats ~10x mais rapido)" ^
 -m "" ^
 -m "WEB WORKER POOL (decode paralelo):" ^
 -m "  - Pool N workers (hardwareConcurrency, max 4); fallback main-thread com timeout 30s" ^
 -m "  - SisMOM_GeoTIFF.__workerSrc: fonte autocontida serializada (sem arquivo Worker externo)" ^
 -m "  - _gtGetDecPool / _gtDecodeMaybeWorker / _gtDecPump" ^
 -m "" ^
 -m "CACHE DE BITMAPS ~1GB LRU:" ^
 -m "  - gtGetCachedBitmap: createImageBitmap cacheado por (url+opts); cap ~1GB / 512 entradas" ^
 -m "  - _gtTsRasterCache separado ~1GB: rasters da serie temporal reutilizados entre feicoes" ^
 -m "  - Tetos em bytes para memoria previsivel em grades grandes" ^
 -m "" ^
 -m "BASE DE PONTOS + UI:" ^
 -m "  - + Nova base de pontos (kind=points): CSV/GeoJSON; gtPointsParseCSV/GeoJSON" ^
 -m "  - gtOpenShapeClassConfig: classificacao visual de camadas por campo + esquema de cores" ^
 -m "  - Botoes Limpar (gtBmkClearView) e Visualizar (gtVisualizarSelecao) no header" ^
 -m "    substituem o antigo Abrir GeoTIFF local" ^
 -m "" ^
 -m "DOCS:" ^
 -m "  - ADEQUACAO_COPERNICUS.md: analise GISELE x Plataforma COPERNICUS (4 cards, aderencia)" ^
 -m "  - HANDOVER_GISELE.md, RESUMO_RETOMAR.md, docs/RELEASE_NOTES.md atualizados para v2.13.0" ^
 -m "" ^
 -m "* package.json 2.12.1 -> 2.13.0" ^
 -m "* Build marker: 20260602-1300-monitproxy -> 20260602-3350-veccache"

if errorlevel 1 (echo. & echo ERRO no commit. & pause & exit /b 1)

echo.
echo === [5/6] Limpando scripts de commit obsoletos ===
del /F /Q commit-v2.12.0.bat commit-v2.12.1.bat 2>nul

echo.
echo === [6/6] Log e lockstep ===
git log --oneline -6
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1
if errorlevel 1 (echo ATENCAO: HTMLs diferem!) else (echo Lockstep HTML: IDENTICOS.)

echo.
echo === Enviando para origin/main (git push) ===
git push origin main
if errorlevel 1 (
    echo.
    echo AVISO: push falhou. Rode manualmente: git push origin main
) else (
    echo Push concluido.
)

echo.
echo Commit v2.13.0 concluido.
pause
