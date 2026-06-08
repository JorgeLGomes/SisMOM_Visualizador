@echo off
REM feat(config): select-all PNG/TIF + fonte abas +10% + espaco scrollbars

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
 -m "feat(config): select-all PNG/TIF + fonte abas +10%% + espaco scrollbars" ^
 -m "" ^
 -m "1. Checkbox selecionar/desmarcar tudo nos cabecalhos PNG e TIF da tabela" ^
 -m "   de variaveis. Estado indeterminado quando selecao e parcial." ^
 -m "   Implementado em _setupAllCb() chamado por renderConfigPane()." ^
 -m "" ^
 -m "2. Fonte das abas de modelos: 12.5px -> 13.5px (+8%%)." ^
 -m "" ^
 -m "3. Padding-bottom do .modal-tabs: 0 -> 6px, criando espaco entre a" ^
 -m "   barra de rolagem horizontal das abas e o conteudo abaixo." ^
 -m "" ^
 -m "* Build marker: 20260607-0200-cfg-tabs -> 20260607-0300-cfg-polish"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
