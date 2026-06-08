@echo off
REM fix(config): abas de modelos sempre visiveis + Base de dados com abas por base

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
 -m "fix(config): abas de modelos sempre visiveis + Base de dados com abas por base" ^
 -m "" ^
 -m "PROBLEMA 1 — abas de modelos cobrindo o scroll bar:" ^
 -m "  .modal-tabs usava overflow-x:auto, criando scrollbar horizontal quando ha" ^
 -m "  muitos modelos. Em modo de edicao o scroll ficava sobre os botoes das abas." ^
 -m "  Fix: overflow-x:auto -> flex-wrap:wrap. Abas quebram para nova linha se" ^
 -m "  necessario, nunca ficam escondidas." ^
 -m "" ^
 -m "PROBLEMA 2 — Base de dados mostrava todos os registros empilhados:" ^
 -m "  renderBasesPane() renderizava todos os cards de bases em sequencia vertical," ^
 -m "  sem navegacao entre elas." ^
 -m "  Fix: Interface igual a de modelos — barra de abas (#cfgBasesTabs) com uma" ^
 -m "  aba por base + botoes '+ KML/GeoJSON' e '+ Pontos' no final." ^
 -m "  Ao clicar uma aba, so o formulario daquela base e exibido." ^
 -m "" ^
 -m "Implementacao:" ^
 -m "  - renderBasesTabs(): monta abas + botoes de adicao (so em modo edicao)" ^
 -m "  - renderBasesForm(): renderiza formulario da base configActiveBaseId" ^
 -m "  - renderBasesPane(): ponto de entrada (garante selecao + chama os dois)" ^
 -m "  - configActiveBaseId: variavel de estado (similar a configActiveId)" ^
 -m "  - _gtAddBaseDraft / _gtAddPointsBaseDraft: navegam para a nova base" ^
 -m "  - Remocao de base: navega para a anterior (idx-1)" ^
 -m "" ^
 -m "* Build marker: 20260607-0100-highlight-fix -> 20260607-0200-cfg-tabs"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
