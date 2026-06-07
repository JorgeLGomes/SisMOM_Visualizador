@echo off
REM fix(config): restaurar Base de dados + aumentar fonte das abas de modelos

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
 -m "fix(config): restaurar Base de dados + aumentar fonte abas" ^
 -m "" ^
 -m "BUG — Base de dados sumia ao abrir a aba:" ^
 -m "  showBasesPane(true) convertia #modalBody em flex-container via" ^
 -m "  body.style.display='flex', quebrando o layout e esvaziando o conteudo." ^
 -m "  Fix: revertida a funcao para show/hide simples:" ^
 -m "    pane.style.display = on ? '' : 'none'" ^
 -m "  O scroll ja funciona naturalmente via .modal-body { overflow-y: auto }," ^
 -m "  que cobre toda a area de conteudo (o <footer> esta FORA do #modalBody)." ^
 -m "  Removido tambem o style duplo 'display:none;display:flex' do HTML" ^
 -m "  do cfgBasesPane (o segundo valor sobrescrevia o primeiro)." ^
 -m "" ^
 -m "MELHORIA — Abas dos modelos mais largas:" ^
 -m "  .modal-tab { font-size: 15px; padding: 11px 16px }" ^
 -m "  (era 13.5px / 8px 14px)" ^
 -m "" ^
 -m "* Build marker: 20260607-0600-scroll-fix -> 20260607-0700-bases-fix"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
