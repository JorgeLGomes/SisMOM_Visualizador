@echo off
REM feat(gt): F21 — perfil vertical por ponto para variáveis 3D

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
 -m "feat(gt): F21 — perfil vertical por ponto (variavel 3D)" ^
 -m "" ^
 -m "FEATURE:" ^
 -m "  Nova ferramenta na HUD do mapa GeoTIFF para gerar perfil vertical" ^
 -m "  de variaveis 3D (ex: Geopotencial, Temperatura em niveis de pressao)." ^
 -m "" ^
 -m "COMPONENTES:" ^
 -m "  - Botao na HUD (data-tool='vprofile') apos serie temporal por ponto" ^
 -m "  - Dialog de configuracao (gtOpenVProfileDialog):" ^
 -m "      * Lista niveis disponiveis do modelo" ^
 -m "      * Selects de nivel inicial e final (default: todos os niveis)" ^
 -m "      * Inputs lat/lon + botao 'Clicar no mapa'" ^
 -m "      * Toggle escala Y: Log (pressao) / Linear" ^
 -m "  - Amostragem assincrona (gtSampleVerticalProfile):" ^
 -m "      * Para cada nivel: monta URL via montarURL({nivel, tif:true})" ^
 -m "      * Busca/decodifica GeoTIFF via _gtFetchAndDecode (com cache)" ^
 -m "      * Amostra pixel via gtSampleDecodedAtLatLon" ^
 -m "  - Popup com grafico Canvas2D (gtOpenVProfilePopup):" ^
 -m "      * Eixo X = valor da variavel; Eixo Y = pressao (invertido)" ^
 -m "      * 1000 hPa na base, valores menores no topo" ^
 -m "      * Escala log (pressao) ou linear, alternavel no header" ^
 -m "      * Linha + area preenchida + pontos por nivel" ^
 -m "      * Tooltip ao hover mostrando nivel + valor" ^
 -m "      * Botao download CSV" ^
 -m "      * Arrastavel; resize pelo browser" ^
 -m "" ^
 -m "fix(gt): passoH=0 corrigido (usa getEffectivePasso no click OK)" ^
 -m "fix(gt): z-index popup elevado (100005) para nao ser coberto" ^
 -m "fix(gt): try/catch em gtOpenVProfilePopup com alert de erro" ^
 -m "fix(gt): _buildGtUrlForNivel cobre 3 casos (native/ownRoute/derive)" ^
 -m "feat(gt): zoom eixo Y no perfil vertical (scroll/drag/dblclick/reset)" ^
 -m "" ^
 -m "* Build marker: nivel-compact-layout -> f21-vprofile"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
