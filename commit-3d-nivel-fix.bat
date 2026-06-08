@echo off
REM fix(gt): dropdown niveis 3D — posicao, transicao e URL

setlocal
cd /d "%~dp0"

echo.
echo === [1/3] Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/3] Stage ===
git read-tree HEAD
if errorlevel 1 (echo ERRO read-tree. & pause & exit /b 1)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

echo.
echo === [3/3] Commit ===
git commit ^
 -m "fix(gt): dropdown niveis 3D — posicao, transicao e URL" ^
 -m "" ^
 -m "POSICAO do dropdown:" ^
 -m "  - gtNivelWrap movido para logo apos gtVariavelSel na toolbar" ^
 -m "  - Aparece: Variavel > [Nivel] > Data > Passo" ^
 -m "" ^
 -m "LOGICA de transicao ao trocar variavel:" ^
 -m "  - 2D -> 3D: reseta nivelAtual=null, forcando selecao do primeiro nivel" ^
 -m "  - 3D -> 3D: mantem nivelAtual (nivel preservado entre variaveis 3D)" ^
 -m "  - Mudanca de modelo: reseta nivelAtual=null (novo modelo, nova lista de niveis)" ^
 -m "" ^
 -m "NIVEL propagado para montarURL:" ^
 -m "  - Novo helper _getSlotNivel(slotIdx): retorna nivelAtual se var e 3D, undefined caso contrario" ^
 -m "  - Render loop principal (linha ~4159): nivel: _getSlotNivel(i)" ^
 -m "  - carregarAnaliseComFallback (2 chamadas): nivel: _getSlotNivel(slotIdx)" ^
 -m "  - Info panel ARQUIVO/CAMINHO: nivel: _getSlotNivel(i)" ^
 -m "  - Resultado: {nivel} no template e substituido pelo valor real (ex: 1000)" ^
 -m "" ^
 -m "FIX info panel (ARQUIVO/CAMINHO):" ^
 -m "  - Em modo GT, o painel agora exibe a URL TIF real (mesma logica de carregarImagem):" ^
 -m "    hasOwnTifRoute -> substituicao temporaria do modelo (url_path_tif + file_name_tif)" ^
 -m "    nativo/derivado -> tif:true para {ext} resolver para extensao_tif" ^
 -m "  - Antes: sempre mostrava URL PNG (ex: TP2M_2026060600.png)" ^
 -m "  - Depois: mostra URL TIF (ex: TP2M_2026060600.tif)" ^
 -m "" ^
 -m "Exemplo:" ^
 -m "  Template: {prefixo}_{nivel}hPa_{yyyy}{mm}{dd}{hh}{ext}" ^
 -m "  Variavel ZGEO (is3d=true), nivel=1000" ^
 -m "  -> ZGEO_1000hPa_2026060600.tif" ^
 -m "" ^
 -m "FIX _buildMTifModel — extensao auto-completada:" ^
 -m "  - Novo helper centralizado _buildMTifModel(m) substitui todos os" ^
 -m "    Object.assign inline (7 locais): carregarImagem, info panel, gtSampleTimeSeries," ^
 -m "    gtSamplePolygonTimeSeries, gtSampleCalcTimeSeries, gtBindOpenTifBtn, outros" ^
 -m "  - Se file_name_tif nao tem {ext} nem extensao literal (ex: apenas {prefixo})," ^
 -m "    acrescenta {ext} automaticamente -> {prefixo}.tif em vez de {prefixo} nu" ^
 -m "  - Garante consistencia: URL do info panel = URL efetivamente carregada" ^
 -m "" ^
 -m "* Build marker: 20260608-1000-config-reorder -> 20260608-1100-3d-nivel-fix"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
