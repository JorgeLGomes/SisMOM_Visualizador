@echo off
REM feat(gt): F22 — perfil vertical temporal (evolucao nivel x tempo)

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
git add HANDOVER_GISELE.md
git add commit-f21-vprofile.bat commit-f22-temporal-profile.bat
git add commit-resize.bat commit-scroll-fix.bat commit-bases-fix.bat commit-wind-vector.bat
git add commit-3d-niveis.bat commit-3d-nivel-fix.bat commit-cfg-fix.bat commit-cfg-polish.bat commit-cfg-tabs.bat
git add commit-config-reorder.bat commit-config-sections.bat commit-fix-nivel-slot-ui.bat
git add commit-fix-nivel-vazio.bat commit-fix-save-config-sync.bat commit-highlight-fix.bat
git add commit-nivel-compact-layout.bat commit-passo0-url.bat commit-predictor2fix.bat
git add commit-tif-template.bat commit-toolbar-passo0.bat commit-ts-passo0.bat

echo.
echo === [3/3] Commit ===
git commit ^
 -m "feat(gt): F22 — perfil vertical temporal (nivel x passo de previsao)" ^
 -m "" ^
 -m "FEATURE:" ^
 -m "  Modo de evolucao temporal no dialog de perfil vertical." ^
 -m "  Eixo X = passo de previsao ou data/hora de validade, Eixo Y = pressao (log)." ^
 -m "  Renderizacao por Sombreado, Isolinhas ou Sombreado+Contorno." ^
 -m "" ^
 -m "COMPONENTES:" ^
 -m "  - gtOpenVProfileDialog:" ^
 -m "      * Toggle Instantaneo / Evolucao Temporal" ^
 -m "      * Fonte: Segoe UI / system-ui" ^
 -m "      * Temporal: passo inicial/final, tipo viz (shaded/isoline/both)" ^
 -m "      * Paleta removida do dialog (gerenciada via engrenagem no popup)" ^
 -m "  - gtSampleTemporalProfile(slotIdx, lat, lon, niveis, pIni, pFim, freq):" ^
 -m "      * Itera sobre todos os (nivel, passo) gerando matriz nNiveis x nSteps" ^
 -m "      * Usa _buildGtUrlForNivel + _gtFetchAndDecode (cache compartilhado)" ^
 -m "      * Retorna { steps, niveis, matrix, vmin, vmax, lat, lon }" ^
 -m "  - gtRunTemporalProfile: progress dialog + dispatch (inclui runDateStr)" ^
 -m "  - gtOpenTemporalProfilePopup (reescrito):" ^
 -m "      * Shaded: putImageData por pixel com interpolacao bilinear" ^
 -m "      * Isolinhas: Marching Squares com LUT padrao de 16 casos" ^
 -m "      * Both: shaded + isolinhas sobrepostas (linhas escuras)" ^
 -m "      * Engrenagem (gear) no header abre painel flutuante de paleta" ^
 -m "        (viridis/plasma/jet/rdbu/rdylbu/spectral/coolwarm/turbo)" ^
 -m "      * Botao +Xh/data para alternar eixo X entre horas e datetime" ^
 -m "        (format DD/MM HHZ, calculado a partir de runDateStr=YYYYMMDDHH)" ^
 -m "      * Zoom 2D: rubber-band (arrastar canvas), scroll (roda do mouse)," ^
 -m "        duplo-clique e botao reset para restaurar visao completa" ^
 -m "      * Escala Y sempre log (pressao)" ^
 -m "      * Tooltip: nivel + label X + valor ao hover" ^
 -m "      * Barra inferior: lat/lon + Baixar CSV + Salvar PNG" ^
 -m "      * Salvar PNG via canvas.toDataURL('image/png')" ^
 -m "      * Posicionado no canto inferior direito (right:20px; bottom:20px)" ^
 -m "      * Tamanho 792x550px (+10% vs versao anterior)" ^
 -m "      * Cor do select de visualizacao corrigida (color:#1f2937)" ^
 -m "      * Arrastavel + resize pelo browser" ^
 -m "      * Fonte: Segoe UI / system-ui" ^
 -m "" ^
 -m "fix(gt): area preenchida removida do perfil vertical instantaneo" ^
 -m "  Perfil instantaneo agora plota apenas linha + pontos (sem shading)" ^
 -m "" ^
 -m "* Build marker: f21-vprofile -> f22-temporal-profile"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
