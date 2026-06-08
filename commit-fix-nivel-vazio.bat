@echo off
REM fix(gt): nivel vazio no nome da figura 3D + dropdown invisivel

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
 -m "fix(gt): nivel vazio no nome da figura 3D + dropdown invisivel" ^
 -m "" ^
 -m "PROBLEMA 1 — nivel vazio (ZGEO_hPa_2026060601.tif):" ^
 -m "  Root cause: nivelAtual=null no primeiro render (race condition)." ^
 -m "  Codigo anterior usava (nivelAtual || '') → string vazia → {nivel} = ''." ^
 -m "" ^
 -m "FIX — novo helper _resolveNivelAtual(slotIdx):" ^
 -m "  Se nivelAtual != null/vazio → retorna nivelAtual (comportamento normal)." ^
 -m "  Se nivelAtual for null → consulta modelos[s.modelo].niveis, usa o" ^
 -m "  primeiro nivel da lista E persiste em nivelAtual para chamadas futuras." ^
 -m "  Resultado: ZGEO_1000hPa_2026060601.tif (nivel correto desde o 1o render)." ^
 -m "" ^
 -m "Callers atualizados:" ^
 -m "  - carregarImagem: _nivel3d = _resolveNivelAtual(slotIdx)" ^
 -m "  - _getSlotNivel: retorno usa _resolveNivelAtual(slotIdx)" ^
 -m "  - gtSampleTimeSeries: _nivel3dTs = _resolveNivelAtual(slotIdx)" ^
 -m "  - gtSamplePolygonTimeSeries: _nivel3dPoly = _resolveNivelAtual(slotIdx)" ^
 -m "" ^
 -m "PROBLEMA 2 — dropdown de nivel invisivel:" ^
 -m "  Root cause: select sem <option> aparece com largura zero." ^
 -m "  - Se m.niveis vazio: exibe <option disabled>'configure Niveis no modelo'</option>" ^
 -m "  - Wrap sempre inline-flex quando is3d=true (antes era oculto se niveis vazio)" ^
 -m "" ^
 -m "FIX gtSyncToolbarFromState — re-render apos resolver nivel:" ^
 -m "  Quando nivelAtual muda de null para valor real (1a chamada de sync)," ^
 -m "  dispara renderTudo() para atualizar a figura com o nivel correto." ^
 -m "  Evita figura com nivel vazio ao abrir o modo GeoTIFF." ^
 -m "" ^
 -m "* Build marker: 20260608-1300-f19-3d-section -> 20260608-1400-fix-nivel-vazio"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
