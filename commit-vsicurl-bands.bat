@echo off
REM v2.16.0 GISELE - sessao 10/06/2026 (range-read /vsicurl + bandas filled-contour)
REM Cobre o delta desde a v2.14.0 (inclui v2.15.0 predictor=3/cache, ainda nao commitado).

setlocal
cd /d "%~dp0"

echo.
echo === [1/5] Removendo locks e backups de patch ===
for %%F in (.git\index.lock .git\refs\heads\main.lock .git\index_new.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)
for %%F in (electron-app\python-helper\server.py.bak electron-app\python-helper\server.py.bak_ps electron-app\python-helper\server.py.bak_ls electron-app\python-helper\_patch_poc.py) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/5] Conferindo lockstep do HTML (md5 raiz x electron-app) ===
certutil -hashfile figuras_SisMOM_v23.html MD5 | findstr /R "^[0-9a-f]"
certutil -hashfile electron-app\figuras_SisMOM_v23.html MD5 | findstr /R "^[0-9a-f]"
echo (os dois md5 acima DEVEM ser IGUAIS entre si - raiz x electron-app)

echo.
echo === [3/5] Status pre-commit ===
git update-index --refresh > nul 2>&1
git status --short

echo.
echo === [4/5] Adicionando todas as mudancas ===
git add -A
if errorlevel 1 (echo ERRO ao executar git add. & pause & exit /b 1)

echo.
echo === [5/5] Commit v2.16.0 ===
git commit ^
 -m "feat: v2.16.0 - range-read/vsicurl, bandas, divisao politica, recorte por poligono+box" ^
 -m "" ^
 -m "RANGE-READ (micro-servico de amostragem por ponto/linha):" ^
 -m "  - server.py: POST /v1/point/series (point_series_patch.py) - serie, perfil vertical, SkewT" ^
 -m "  - server.py: POST /v1/line/sample (line_sample_patch.py) - corte vertical (leitura janelada)" ^
 -m "  - server.py: use_vsicurl em /v1/timeseries/point (poc_vsicurl_patch.py)" ^
 -m "  - server.py: GET /v1/tile/window (window_patch.py) - recorte do viewport (requisitar trecho)" ^
 -m "  - _dl_sample_tif (ponto) e _dl_sample_line (janela por nivel) via /vsicurl + rasterio" ^
 -m "  - frontend: _skBatchSampleHelper (SkewT), _gtPointSeriesValues (perfil vertical)," ^
 -m "    use_vsicurl (serie), _gtLineSampleValues (corte) - todos com fallback JS" ^
 -m "  - validado contra CPTEC (HTTP 206 + Accept-Ranges + CORS); paridade exata nos testes" ^
 -m "  - docs/AVALIACAO_microservico_ponto.md e docs/POC_vsicurl_resultados.md" ^
 -m "  - poc_vsicurl_validate.py (valida range/tiling de um TIF real)" ^
 -m "" ^
 -m "REQUISITAR TRECHO VISIVEL (carregar recorte do viewport):" ^
 -m "  - botao na config: gtRequestViewportWindow -> GET /v1/tile/window com o bbox visivel" ^
 -m "  - recorta aos dados validos da cobertura; carrega o recorte como camada extra" ^
 -m "" ^
 -m "BANDAS (filled contour) na config da camada:" ^
 -m "  - sub-painel gtCfgBandsPanel: Min/Max + Nro de bandas (auto) | intervalos explicitos" ^
 -m "  - rasterSmooth so no modo Suavizado (bandas/pixel sem smoothing de cor)" ^
 -m "  - aplicarPaleta: interpola os DADOS antes de classificar -> bordas suaves, cor chapada" ^
 -m "" ^
 -m "DOCS/VERSAO:" ^
 -m "  - package.json 2.16.0; build marker 20260610-form-campos" ^
 -m "  - HANDOVER_GISELE.md, HANDOVER_SESSAO_2026-06-10.md, docs/RELEASE_NOTES.md, README.md" ^
 -m "  - Manual do Usuario (docs/GISELE_Manual_Uso.pdf) regenerado (35 paginas)" ^
 -m "" ^
 -m "DIVISAO POLITICA no Background:" ^
 -m "  - toggles Estados (Brasil) e Paises (America do Sul); overlay vetorial no mapa" ^
 -m "  - miscelaneas/divisao_estados_br.geojson (27 UFs) + divisao_paises_sa.geojson (13 paises)" ^
 -m "  - derivados do Natural Earth via sane-topojson; inicia com estados do Brasil ligados" ^
 -m "" ^
 -m "RECORTE POR POLIGONO (mascara) + correcao do loop:" ^
 -m "  - clip do campo a um poligono (setClipPolygon/_buildClipPath); mascara o exterior" ^
 -m "  - acao Recortar: mascara visual + aquisicao do BOX do poligono no servidor (/v1/tile/window" ^
 -m "    via vsicurl) como camada '... box', SEM fitTo; ocultada na animacao e reexibida ao parar" ^
 -m "  - leitura janelada do viewport tambem disponivel pelo botao '⊡ Requisitar trecho'" ^
 -m "  - _gtApplyMapView: fitTo so na 1a vez que a slot mostra o modelo; trocar data/passo" ^
 -m "    preserva o zoom do usuario (trocar de modelo reenquadra)" ^
 -m "  - filtro de frames anomalos na animacao: pula frame com span de longitude global" ^
 -m "    (>150 graus e >2.5x a referencia do painel) e mantem o ultimo frame bom" ^
 -m "    (window.GISELE_SKIP_ANOMALOUS_FRAMES=false desliga)" ^
 -m "  - NOTA: o 'campo global a cada 24h' e da GERACAO DO DADO (TIF de precip acumulada" ^
 -m "    sai em grade/dominio diferente/global nos passos 24/48/72h), nao da logica da plataforma" ^
 -m "" ^
 -m "DIVISAO POLITICA tambem no Miscelania (cada feicao selecionavel):" ^
 -m "  - America do Sul > paises; Brasil > 27 estados; cor/espessura das linhas configuravel" ^
 -m "" ^
 -m "  - HTML raiz + electron-app em lockstep (md5 c7cf00f318075ca65c66851cf4d9053f, 26275 linhas)"

if errorlevel 1 (echo. & echo ERRO no commit. & pause & exit /b 1)

echo.
echo === Log dos ultimos 5 commits ===
git log --oneline -5

echo.
echo Commit v2.16.0 concluido. Para enviar: git push origin main
pause
