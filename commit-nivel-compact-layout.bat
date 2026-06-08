@echo off
REM fix(gt): nivel dropdown compacto entre data e variavel; data com hora inline

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
 -m "fix(gt): nivel dropdown compacto + hora-label na data no map-config" ^
 -m "" ^
 -m "PROBLEMA:" ^
 -m "  O select de nivel aparecia apos o select de variavel e ocupava" ^
 -m "  espaco excessivo no header do painel de mapa." ^
 -m "" ^
 -m "FIX — layout compact do map-config:" ^
 -m "  - Reordem: modelo | [date-nivel-wrap] | sync | variavel" ^
 -m "  - date-nivel-wrap: div inline-flex com date + hora-label + nivel" ^
 -m "  - data: width 108px (fixo, sem flex-grow)" ^
 -m "  - hora-label: span monospace mostrando hora da rodada (ex: '12Z')" ^
 -m "      * Alimentado por _updateHoraLabel(slotIdx) via s.data.slice(8,10)" ^
 -m "      * Chamado em atualizarSlotsControles para todos os slots" ^
 -m "  - nivel: width 74px (fixo, sem flex-grow); oculto quando variavel 2D" ^
 -m "  - Resultado visual: [06/06/2026] [12Z] [850 hPa] | [sync] | [variavel]" ^
 -m "" ^
 -m "NOVOS CSS:" ^
 -m "  .date-nivel-wrap  { inline-flex, gap 4px, flex-shrink 0 }" ^
 -m "  .hora-label       { 11px monospace, min-width 26px }" ^
 -m "  input[date]       { width 108px, flex none }" ^
 -m "  select[nivel]     { width 74px,  flex none }" ^
 -m "" ^
 -m "NOVA FUNCAO:" ^
 -m "  _updateHoraLabel(slotIdx) — extrai s.data.slice(8,10) e seta .textContent" ^
 -m "" ^
 -m "* Build marker: fix-nivel-slot-ui -> nivel-compact-layout"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
