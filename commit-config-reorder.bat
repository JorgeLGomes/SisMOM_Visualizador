@echo off
REM refactor(config): reordenar campos + fix sufixo TIF em {ext}

setlocal
cd /d "%~dp0"

echo.
echo === [1/3] Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/3] Stage ===
git read-tree HEAD
if errorlevel 1 (echo ERRO read-tree. & pause & exit /b 1)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

echo.
echo === [3/3] Commit ===
git commit ^
 -m "refactor(config): reordenar campos + fix sufixo TIF" ^
 -m "" ^
 -m "REORDENACAO dos campos no formulario de configuracao do modelo:" ^
 -m "  Antes: Sufixo PNG > MaxPassos > URL > NomeArq > Formatos > MapProvider > ExtTIF > TemplateTIF" ^
 -m "  Depois: MaxPassos > URL > Sufixo PNG > TemplateTIF > Sufixo TIF > NomeArq > Formatos > MapProvider" ^
 -m "" ^
 -m "LABELS:" ^
 -m "  - 'Sufixo do arquivo' -> 'Sufixo do arquivo (PNG/GIF)'" ^
 -m "  - 'Template Nome Arq. (PNG/GIF)' -> 'Template Nome Arq.'" ^
 -m "    (o template de nome e compartilhado por todos os formatos)" ^
 -m "" ^
 -m "FIX {ext} no TIF:" ^
 -m "  - montarURL() recebe novo parametro 'tif: true'" ^
 -m "  - Quando tif=true, {ext} resolve para m.extensao_tif em vez de m.extensao" ^
 -m "  - Aplicado nos paths isNativeGt (gtSampleTimeSeries, gtSamplePolygonTimeSeries," ^
 -m "    carregarImagem 3D, gtSampleCalcTimeSeries)" ^
 -m "  - Modelos non-native com hasOwnTifRoute ja usavam mTif.extensao (correto)" ^
 -m "" ^
 -m "PREVIEW aprimorado:" ^
 -m "  - {ext} no nome do TIF e resolvido visualmente para o valor do Sufixo TIF" ^
 -m "  - Aviso em vermelho se o template TIF contem extensao PNG/GIF hardcoded" ^
 -m "" ^
 -m "PRESET CPTEC:" ^
 -m "  - Agora gera '{prefixo}-{F%%4}{ext}' (usa {ext}) em vez de '.tif' hardcoded" ^
 -m "" ^
 -m "* Build marker: 20260608-0900-3d-niveis -> 20260608-1000-config-reorder"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
