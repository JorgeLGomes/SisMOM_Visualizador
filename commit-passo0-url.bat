@echo off
REM fix: passo=0 (analise T+0) gera URL corretamente

setlocal
cd /d "%~dp0"

echo.
echo === Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === Stage + Commit ===
git read-tree HEAD
if errorlevel 1 (echo ERRO read-tree. & pause & exit /b 1)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

git commit ^
 -m "fix: passo=0 (analise T+0) gera URL corretamente" ^
 -m "" ^
 -m "PROBLEMA: passo=0 era rejeitado em dois pontos:" ^
 -m "  1) montarURL: 'if (file_idx < 1) return null' bloqueava file_idx=0" ^
 -m "     -> retornava null, gerando ARQUIVO=- e CAMINHO=-" ^
 -m "  2) check de range: 'passo < 1' disparava 'fora do alcance desta rodada'" ^
 -m "" ^
 -m "CORRECAO:" ^
 -m "  1) montarURL: 'if (file_idx < 1)' -> 'if (file_idx < 0)'" ^
 -m "     Com passo=0 e freq=1h: file_idx=0, passo_h=0" ^
 -m "     Template {yyyymmddhh} = data da rodada (sem step) -> PSLM_2026060400" ^
 -m "  2) Range check: 'passo < 1' -> 'passo < 0'" ^
 -m "" ^
 -m "* Build marker: 20260605-2200-toolbar-passo0 -> 20260605-2300-passo0-url"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: OK || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou) else (echo Push OK.)
pause
