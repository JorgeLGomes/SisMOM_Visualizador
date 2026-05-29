@echo off
REM Commit consolidado da sessao GISELE.
REM Cobre TUDO desde o ultimo commit estavel:
REM   - Serie temporal + video MP4 + mapa default por modelo
REM   - Miscelaneas (plataformas + corais com hachura/cor)
REM   - Hatching, color picker, popup info ao clicar em shape
REM   - CORS strict flag (--strict-cors) + Preset FTP CPTEC
REM   - Smoke test decoder + manual 25p + HANDOVER

setlocal
cd /d "%~dp0"

echo.
echo === Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\index_staging.lock .git\idx_new1.lock .git\index_new.lock) do (
    if exist "%%F" (
        del /F /Q "%%F" 2>nul
        if exist "%%F" (
            echo AVISO: nao removeu %%F (talvez bloqueado)
        ) else (
            echo OK: %%F removido.
        )
    )
)

echo.
echo === Limpando index intermediarios criados em sandbox ===
for %%F in (.git\index_staging .git\idx_new1 .git\index_new .git\index.broken) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === Reconstruindo o index a partir do HEAD ===
git read-tree HEAD
if errorlevel 1 (
    echo ERRO ao reconstruir o index.
    pause
    exit /b 1
)

echo.
echo === Status pre-commit ===
git update-index --refresh > nul 2>&1
git status --short

echo.
echo === Adicionando todas as mudancas ===
git add -A
if errorlevel 1 (
    echo ERRO ao executar git add.
    pause
    exit /b 1
)

echo.
echo === Commit v2.3.0 ===
git commit ^
 -m "v2.3.0 GISELE: serie temporal + video MP4 + mapa default por modelo + Miscelaneas (plataformas/corais) + --strict-cors + Preset FTP CPTEC + handover + manual 25p" ^
 -m "" ^
 -m "* Serie temporal: clique em ponto -> varre passos do slot, grafico tempo x valor, CSV + PNG. Reutiliza pipeline montarURL + gtSampleDecodedAtLatLon. Fix horizonte para modelos com m.maxPassos < v.horizonte (BESM Global PREC freq=24 horizonte=720)." ^
 -m "* Salvar video MP4: pre-busca todos os frames, drawImage em canvas off-screen respeitando object-fit + zoom/pan, MediaRecorder 30fps + holdAndPaint forcando emissao de frames a cada RAF + pixel anti-dedup, codec fallback MP4 -> WebM. Funciona em PNG/GIF e GeoTIFF, passagem unica do primeiro ao ultimo passo." ^
 -m "* Mapa-base padrao por modelo: campo cfgMapProvider na configuracao (none/esri/osm/topo). Auto-aplica em gtSelectPanel quando modelo muda (flags _lastModelForMap / _mapProviderUserSet / _mapEnabledUserSet). Ordem corrigida em setAppMode (gtSelectPanel antes de renderTudo)." ^
 -m "* Miscelaneas: Plataformas offshore (107 pontos) + Corais brasileiros (11 poligonos, shapefile WCMC008 filtrado por point-in-polygon real). Hachura diagonal via CanvasPattern (cache local), color picker no chip, click point-in-polygon abre popup branco com infoProps. Inline gt-misc-* tags para file://." ^
 -m "* Fixes: contornos keepFill default=true (shaded + isolinhas juntas), swap PNG->GeoTIFF re-snapa passo via atualizarMaxPassos + _stateRestore (legacy snap sem passoAtual), profile chart fundo branco com tooltip + Salvar PNG." ^
 -m "* --strict-cors flag (main.js): re-ativa webSecurity:true + bloqueia conteudo inseguro. Default permissivo (webSecurity:false) pra video MP4 PNG funcionar. Log diagnostico CORS mode em %%APPDATA%%/GISELE/launch.log." ^
 -m "* Preset FTP CPTEC na config: marca PNG+TIF, deriva URL TIF de PNG (/fig/->/geotiff/), nome arquivo {prefixo}-{F%%%%4}.tif." ^
 -m "* Smoke test do decoder GeoTIFF: gerador Python de TIF sintetico 32x32 Float32 + Node testando decodeTIFF + 5 paletas. Confirma bbox/min/max corretos." ^
 -m "* Manual PDF: 25 paginas. Secoes novas: 10 Ferramentas (com serie temporal), 11 Miscelaneas, 4 Salvar video MP4, 7 Mapa-base padrao + Preset CPTEC + .tif locais, 14 CORS --strict-cors + Video MP4 troubleshooting." ^
 -m "* HANDOVER_GISELE.md + .pdf: handover consolidado com features+prompts+ferramentas+padroes criticos+glossario JS, para continuidade com outro modelo." ^
 -m "* Build markers: 20260528-4500-coraistail -> 20260529-2000-cptecpreset."

if errorlevel 1 (
    echo.
    echo ERRO no commit.
    pause
    exit /b 1
)

echo.
echo === Log dos ultimos 3 commits ===
git log --oneline -3

echo.
echo Commit concluido com sucesso.
echo Para enviar ao remoto: git push origin main
pause
