@echo off
REM fix(gt): saveConfig nao ressincronizava toolbar GT apos alterar is3d/niveis

setlocal
cd /d "%~dp0"

echo.
echo === [1/3] Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/3] Stage ===
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

echo.
echo === [3/3] Commit ===
git commit ^
 -m "fix(gt): saveConfig nao sincronizava toolbar GT" ^
 -m "" ^
 -m "PROBLEMA:" ^
 -m "  Ao salvar configuracao com is3d=true em uma variavel (ex: Geopotencial)," ^
 -m "  o dropdown de nivel nao aparecia imediatamente no toolbar GeoTIFF." ^
 -m "  Root cause: saveConfig() nao chamava gtSyncToolbarFromState() — entao" ^
 -m "  gtNivelWrap continuava display:none mesmo com a variavel 3D selecionada." ^
 -m "" ^
 -m "FIX:" ^
 -m "  Adicionado try { gtSyncToolbarFromState() } apos atualizarSlotsControles()" ^
 -m "  e renderTudo() em saveConfig(). Agora ao salvar:" ^
 -m "    - Se variavel ativa no GT for 3D -> dropdown Nivel aparece imediatamente" ^
 -m "    - Se variavel nao for 3D -> dropdown Nivel permanece oculto" ^
 -m "    - Niveis de pressao sao recarregados do modelo recem-salvo" ^
 -m "" ^
 -m "* Build marker: fix-nivel-dropdown -> fix-save-config-sync"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
