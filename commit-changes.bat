@echo off
REM Commit v2.4.0 GISELE — sessao 29/05/2026
REM Cobre TUDO desde o ultimo commit estavel:
REM   - Arvore ERMA-style + Configuracao da Camada por no
REM   - Calculadora dupla (expressao entre camadas + per-layer scalar)
REM   - Serie temporal + video MP4 + mapa default por modelo
REM   - Miscelaneas (plataformas + corais com hachura/cor)
REM   - --strict-cors flag + Preset FTP CPTEC
REM   - Manual PDF 25p + HANDOVER PDF + ESPECIFICACOES PDF 18p

setlocal
cd /d "%~dp0"

echo.
echo === Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\index_staging.lock .git\idx_new1.lock .git\idx_v24.lock .git\index_new.lock) do (
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
for %%F in (.git\index_staging .git\idx_new1 .git\idx_v24 .git\index_new .git\index.broken) do (
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
echo === Commit v2.4.0 ===
git commit ^
 -m "v2.4.0 GISELE: arvore ERMA + Configuracao da Camada por no + Calculadora dupla + Serie temporal + Video MP4 + Miscelaneas + --strict-cors + Preset CPTEC + manual 25p + handover + especificacoes 18p" ^
 -m "" ^
 -m "* Painel direito reorganizado em arvore ERMA com 4 grupos colapsaveis (Background/Miscelanea/Camadas/Ferramentas), botao Collapse/Expand folders toggle no topo." ^
 -m "* Configuracao da Camada como sub-menu por no: painel unico (#gtLayerConfigPanel) movido fisicamente entre #gtLayerConfigHome invisivel e .gt-tree-config-host de cada camada. Layout vertical responsivo. Click handler em summary com preventDefault evita loop recursivo de toggle. So um sub-menu aberto por vez." ^
 -m "* Background com radios mutuamente exclusivos por slot, sincroniza com tile provider + Mostrar mapa classicos." ^
 -m "* Miscelanea com checkboxes que adicionam/removem camadas (Plataformas offshore 107 pts + Corais brasileiros 11 pol)." ^
 -m "* Camadas com cor inline (geojson), visibilidade, remover, e Configuracao da Camada (raster). Tree re-render a cada gtRenderLayerChips." ^
 -m "* Ferramentas: Adicionar GeoTIFF/GeoJSON, Adicionar Modelo (form movido fisicamente pra dentro do no), Abrir TIF local, e nova sub-secao Calculadora." ^
 -m "* Calculadora dupla:" ^
 -m "  - Ferramentas: parser proprio de expressao algebrica segura (numeros, identificadores, + - * / parens), tokens clicaveis Camada1..N, avaliacao per-pixel com mascara NoData propagada." ^
 -m "  - Configuracao da Camada: operador + escalar aplicado a camada ativa, reusa engine gtCreateLayerFromExpression." ^
 -m "* Serie temporal: clique em ponto -> varre passos do slot, grafico tempo x valor, CSV + PNG. Fix horizonte para BESM Global PREC freq=24 horizonte=720." ^
 -m "* Salvar video MP4: pre-busca todos os frames, drawImage em canvas off-screen respeitando object-fit + zoom/pan, MediaRecorder 30fps + holdAndPaint, codec MP4 -> WebM fallback. Funciona em PNG/GIF e GeoTIFF, passagem unica." ^
 -m "* Mapa-base padrao por modelo: cfgMapProvider na config (none/esri/osm/topo), auto-aplica em gtSelectPanel com flags _lastModelForMap / _mapProviderUserSet." ^
 -m "* Miscelaneas com hachura diagonal (CanvasPattern cached), color picker no chip, click point-in-polygon abre popup branco. Inline gt-misc-* tags para file://." ^
 -m "* Fixes: contornos keepFill default=true, swap PNG->GeoTIFF re-snapa passo, profile chart fundo branco com tooltip." ^
 -m "* --strict-cors flag (main.js): re-ativa webSecurity:true. Default permissivo (webSecurity:false) pra video MP4 PNG. Log diagnostico CORS mode em launch.log." ^
 -m "* Preset FTP CPTEC na config: marca PNG+TIF, deriva URL TIF de PNG (/fig/->/geotiff/), nome arquivo {prefixo}-{F%%%%4}.tif." ^
 -m "* Smoke test do decoder GeoTIFF (Node + TIF sintetico 32x32 Float32)." ^
 -m "* Manual PDF: 25 paginas (Salvar video, Mapa default, Calculadora, Preset CPTEC, --strict-cors)." ^
 -m "* HANDOVER_GISELE.md + .pdf: consolidado com features+prompts+ferramentas+padroes criticos+glossario." ^
 -m "* ESPECIFICACOES_GISELE.md + .pdf (18 paginas): documento para reimplementacao do zero com 14 secoes (arquitetura, 13 RFs, RNFs, modelo de dados completo, APIs, riscos, cronograma 33 semanas)." ^
 -m "* Build markers: 20260528-4500-coraistail -> 20260529-3000-calc."

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
