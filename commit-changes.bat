@echo off
REM Commit v2.7.0 GISELE - sessao 29-30/05/2026 (Python helper + UX + perf contornos)
REM Cobre tudo desde v2.6.0:
REM   - Python helper subprocess no Electron (FastAPI + rasterio + httpx)
REM     com bridge no frontend (gtPyHelper) e fallback transparente JS
REM   - Slider de opacidade no painel + sync entre camadas
REM   - Rename "Configuracao da Camada" -> "Ferramentas"
REM   - Remocao do widget calc per-layer escalar
REM   - Marching squares otimizado (~8-15x): single-pass + Uint8Array mask
REM   - Cache de contornos com fingerprint dos dados + LRU true + cap 100
REM   - electron-app/package.json 2.6.0 -> 2.7.0
REM   - Manual PDF (16 secoes) + HANDOVER v2.7.0 (sec 2.15) regenerados

setlocal
cd /d "%~dp0"

echo.
echo === Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\index_staging.lock .git\idx_v25.lock .git\idx_v26.lock .git\idx_v27.lock .git\index_new.lock) do (
    if exist "%%F" (
        del /F /Q "%%F" 2>nul
        if exist "%%F" (
            echo AVISO: nao removeu %%F
        ) else (
            echo OK: %%F removido.
        )
    )
)

echo.
echo === Limpando index intermediarios criados em sandbox ===
for %%F in (.git\index_staging .git\idx_v25 .git\idx_v26 .git\idx_v27 .git\index_new .git\index.broken) do (
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
echo === Commit v2.7.0 ===
git commit ^
 -m "v2.7.0 GISELE: Python helper local + UX (opacidade/rename/calc) + perf contornos (~8-15x) + cache" ^
 -m "" ^
 -m "* Python helper opcional subprocess no Electron:" ^
 -m "  - electron-app/python-helper/: server.py 417L (FastAPI), url_builder.py 125L, sampler.py 144L" ^
 -m "  - 4 endpoints: /health, /v1/timeseries/point[/geojson], /v1/calc/temporal, /v1/profile/line" ^
 -m "  - Fetch paralelo via httpx async com semaforo (parallel_limit=8)" ^
 -m "  - rasterio decode + numpy sample no ponto, convencao top-down identica ao JS" ^
 -m "  - python-spawner.js gerencia subprocess: dev (python server.py) ou packaged (.exe via PyInstaller)" ^
 -m "  - preload.js + ipcMain bridge: window.GISELE_PYTHON.getUrl/isAvailable/onStatusChange" ^
 -m "  - main.js: app.whenReady spawna; before-quit mata (taskkill no Win, SIGTERM->SIGKILL Unix)" ^
 -m "  - --no-python-helper desabilita explicitamente" ^
 -m "" ^
 -m "* Bridge gtPyHelper no frontend (~280 linhas no HTML):" ^
 -m "  - Probe /health a cada 5s (tenta window.GISELE_PYTHON.getUrl, fallback 127.0.0.1:8765)" ^
 -m "  - sampleTimeSeries/sampleProfileLine/calcTemporal expostos" ^
 -m "  - Badge UI canto inferior direito: '⚡ Python v0.1.0' (cyan) ou 'JS only' (cinza)" ^
 -m "  - gtSampleTimeSeries guard com fallback transparente: tenta Python -> JS se null/erro" ^
 -m "  - electron-app/package.json: preload.js, python-spawner.js em files; extraResources copia python-helper/dist -> resources/python-helper" ^
 -m "  - build-helper.bat/sh com PyInstaller (--hidden-import=rasterio.*) gerando .exe standalone" ^
 -m "" ^
 -m "* UX no painel da camada:" ^
 -m "  - Slider 'Opacidade' 0-100%% com label sincronizado, aplica via gtApplyOpacityToActive" ^
 -m "  - gtMoveCfgPanelToLayer sincroniza slider com camada-alvo (primary ou extra) ao expandir no" ^
 -m "  - Titulo do sub-menu renomeado '⚙ Configuracao da Camada' -> '🛠 Ferramentas'" ^
 -m "  - Widget calc per-layer (select op + input escalar + btn Aplicar + status) removido" ^
 -m "  - Substituido por header simples '🧮 Calculadora' (com border-top tracejada)" ^
 -m "  - Textarea de Tempos abaixo cobre TODOS os casos (escalar via t1*1000, ranges sum(t1..t24), etc)" ^
 -m "" ^
 -m "* Marching squares otimizado (~8-15x speedup):" ^
 -m "  - Mascara NoData pre-computada como Uint8Array (1 byte/pixel, 1 pass)" ^
 -m "  - Single-pass sobre o grid para TODOS os niveis (era 1 pass por nivel)" ^
 -m "  - Early-skip por cellMin/cellMax: niveis fora da faixa pulam com break (sorted)" ^
 -m "  - Zero closures no hot loop (era 4 closures T/R/B/L por celula)" ^
 -m "  - Float32Array para Larr (acesso indexed mais rapido em V8)" ^
 -m "  - Hoist de dLon, dLat, lat0, lon0 fora do loop" ^
 -m "  - NaN check via v !== v (mais rapido que isFinite)" ^
 -m "  - Bitwise OR para combinar 4 bytes da mascara em um teste" ^
 -m "" ^
 -m "* Cache de contornos com fingerprint:" ^
 -m "  - _gtContourCacheKey aceita dataFingerprint = lastLoadedURL[slot] para primary (era so layer.id)" ^
 -m "  - Para extras, layer.id ja e unico" ^
 -m "  - LRU true via delete+set on hit (Map preserva ordem de insercao)" ^
 -m "  - Cap aumentado 16 -> 100 (cabe rodada Eta de 72 passos + extras)" ^
 -m "  - Remocao da invalidacao agressiva 'primary|*' em gtRerenderSlot — fingerprint ja separa" ^
 -m "  - console.log do hit/miss para diagnostico" ^
 -m "" ^
 -m "* Documentacao:" ^
 -m "  - HANDOVER_GISELE.md v2.6.0 -> v2.7.0 com bloco 'Mudancas v2.6 -> v2.7' + secao 2.15 (Python helper + UX) com 13 features mapeadas" ^
 -m "  - Manual PDF: secao 6 atualiza nome 'Ferramentas' + slider opacidade + calc unificada; nova secao 14 'Acelerador Python' (badge, funcoes aceleradas, deploy embedded vs manual); renumerada para 16 secoes" ^
 -m "  - 3 PDFs regerados" ^
 -m "  - electron-app/package.json 2.6.0 -> 2.7.0" ^
 -m "" ^
 -m "* Build markers: 20260529-5800-pyhelper -> 5900-cfgopcty -> 6000-calcsimpl -> 6100-ctroptim -> 6200-ctrcache."

if errorlevel 1 (
    echo.
    echo ERRO no commit.
    pause
    exit /b 1
)

echo.
echo === Log dos ultimos 5 commits ===
git log --oneline -5

echo.
echo Commit v2.7.0 concluido com sucesso.
echo Para enviar ao remoto: git push origin main
pause
