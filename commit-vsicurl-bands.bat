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
echo (os dois md5 acima DEVEM ser iguais: 6622c41436f1f89930202b88b3ab34d4)

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
 -m "feat: v2.16.0 - leitura por range-read (/vsicurl) + bandas filled-contour" ^
 -m "" ^
 -m "RANGE-READ (micro-servico de amostragem por ponto/linha):" ^
 -m "  - server.py: POST /v1/point/series (point_series_patch.py) - serie, perfil vertical, SkewT" ^
 -m "  - server.py: POST /v1/line/sample (line_sample_patch.py) - corte vertical (leitura janelada)" ^
 -m "  - server.py: use_vsicurl em /v1/timeseries/point (poc_vsicurl_patch.py)" ^
 -m "  - _dl_sample_tif (ponto) e _dl_sample_line (janela por nivel) via /vsicurl + rasterio" ^
 -m "  - frontend: _skBatchSampleHelper (SkewT), _gtPointSeriesValues (perfil vertical)," ^
 -m "    use_vsicurl (serie), _gtLineSampleValues (corte) - todos com fallback JS" ^
 -m "  - validado contra CPTEC (HTTP 206 + Accept-Ranges + CORS); paridade exata nos testes" ^
 -m "  - docs/AVALIACAO_microservico_ponto.md e docs/POC_vsicurl_resultados.md" ^
 -m "  - poc_vsicurl_validate.py (valida range/tiling de um TIF real)" ^
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
 -m "  - HTML raiz + electron-app em lockstep (md5 6622c41436f1f89930202b88b3ab34d4, 25899 linhas)"

if errorlevel 1 (echo. & echo ERRO no commit. & pause & exit /b 1)

echo.
echo === Log dos ultimos 5 commits ===
git log --oneline -5

echo.
echo Commit v2.16.0 concluido. Para enviar: git push origin main
pause
