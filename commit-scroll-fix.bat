@echo off
REM fix(config): scroll vertical bases + handle resize + barra abas fina

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
 -m "fix(config): scroll vertical bases + handle resize + barra abas fina" ^
 -m "" ^
 -m "BUG 1 — Resize handle fora de lugar:" ^
 -m "  .modal nao tinha position:relative, entao o handle position:absolute" ^
 -m "  ficava ancorado ao .modal-backdrop (viewport) em vez de ao modal." ^
 -m "  Fix: adicionado position:relative ao .modal." ^
 -m "" ^
 -m "BUG 2 — Base de dados sem scroll vertical:" ^
 -m "  #cfgBasesPane dentro de #modalBody (overflow-y:auto) nao tinha altura" ^
 -m "  limitada, entao #cfgBasesList nunca ativava seu scroll interno." ^
 -m "  Fix: showBasesPane(true) agora converte #modalBody em flex-column com" ^
 -m "  overflow:hidden e aplica flex:1 1 0 ao #cfgBasesPane, permitindo que" ^
 -m "  #cfgBasesList faca scroll internamente. Revertido em showBasesPane(false)." ^
 -m "" ^
 -m "BUG 3 — Barra horizontal das abas de modelos muito espessa:" ^
 -m "  scrollbar-width:thin + altura de 5px no webkit para o .modal-tabs," ^
 -m "  reduzindo o espaco perdido e o conflito visual com a barra vertical." ^
 -m "" ^
 -m "* Build marker: 20260607-0500-resize -> 20260607-0600-scroll-fix"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
