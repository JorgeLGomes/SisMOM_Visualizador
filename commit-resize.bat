@echo off
REM feat(config): resize de colunas da tabela de variaveis + resize do modal

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
 -m "feat(config): resize de colunas da tabela + resize do modal" ^
 -m "" ^
 -m "1. Colunas da tabela de variaveis redimensionaveis:" ^
 -m "   Drag handle vertical no limite direito de cada cabecalho (<th>)." ^
 -m "   Larguras persistidas em localStorage (gisele_vartbl_colw)." ^
 -m "   Handle realca em azul no hover/drag. Implementado em _initVarTableColResize()." ^
 -m "" ^
 -m "2. Modal de configuracao redimensionavel:" ^
 -m "   Handle de resize no canto inferior-direito do modal." ^
 -m "   Altera width + maxHeight do elemento .modal via inline style." ^
 -m "   Tamanho persistido em localStorage (gisele_modal_size)." ^
 -m "   Implementado em _initModalResize(), chamado em openConfigModal()." ^
 -m "" ^
 -m "* Build marker: 20260607-0400-wind-vector -> 20260607-0500-resize"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
