@echo off
REM fix(map): destaque de feicao aparece imediatamente ao clicar (nao so apos zoom)

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
 -m "fix(map): destaque de feicao aparece imediatamente ao clicar" ^
 -m "" ^
 -m "CAUSA RAIZ: _blitVectorLayers() cacheia o canvas vetorial pela chave" ^
 -m "  (canvas.width x canvas.height @ vp # _extraVer). O flag _gtHl nao" ^
 -m "  fazia parte da chave, entao ao clicar numa feicao o cache nao era" ^
 -m "  invalidado — o destaque so aparecia na proxima mudanca de viewport" ^
 -m "  (zoom/pan), que forcava um cache miss." ^
 -m "" ^
 -m "FIX:" ^
 -m "  1. SisMOM_Map expoe invalidateVectors() que incrementa _extraVer." ^
 -m "  2. Handler de click chama invalidateVectors() em todos os mapas" ^
 -m "     ativos antes do redraw(), forcando reconstrucao do canvas vetorial" ^
 -m "     com o novo estado de destaque." ^
 -m "" ^
 -m "* Build marker: 20260605-2500-cfg-fix -> 20260607-0100-highlight-fix"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
