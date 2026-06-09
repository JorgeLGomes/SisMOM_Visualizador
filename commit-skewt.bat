@echo off
REM v2.14.0 GISELE - sessao 09/06/2026 (Skew-T log-P + CAPE/CINE + performance + seguir-mapa)
REM Cobre todo o delta nao commitado desde a v2.13.0 (F22):
REM   - Skew-T log-P por ponto: termodinamica, metodo da parcela (LCL/LFC/EL, CAPE/CINE)
REM   - Performance P1-P3 (httpx global, sw.js, minify HTML, orjson, cache index)
REM   - "Seguir mapa" em perfil/corte/serie + remocao do Leaflet
REM   - HTML raiz + electron-app sincronizados (md5 e00e9d80aa48add89972e3fa467b7448)

setlocal
cd /d "%~dp0"

echo.
echo === [1/4] Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\refs\heads\main.lock .git\index_new.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/4] Status pre-commit ===
git update-index --refresh > nul 2>&1
git status --short

echo.
echo === [3/4] Adicionando todas as mudancas ===
git add -A
if errorlevel 1 (echo ERRO ao executar git add. & pause & exit /b 1)

echo.
echo === [4/4] Commit v2.14.0 ===
git commit ^
 -m "feat(gt): v2.14.0 — Skew-T log-P por ponto (termodinamica + CAPE/CINE) + performance + seguir-mapa" ^
 -m "" ^
 -m "SKEW-T LOG-P (figuras_SisMOM_v23.html):" ^
 -m "  - Botao na toolbar GeoTIFF (data-tool=skewt) -> gtOpenSkewTDialog" ^
 -m "  - Amostra Temperatura 3D + Umidade 3D nos niveis do ponto; Td via UR ou umidade especifica" ^
 -m "  - Diagrama: isotermas inclinadas 45, isobaras log-P, adiabaticas secas, pseudoadiabaticas," ^
 -m "    razao de mistura, curvas T/Td e pontos dos niveis do modelo" ^
 -m "  - Niveis: faixa base/topo OU base pela pressao de superficie (PSLC) recalculada por ponto/tempo" ^
 -m "  - Metodo da parcela (_skComputeParcel): LCL (base), LFC, EL (topo), CAPE e CINE" ^
 -m "    com curva da parcela, sombreado CAPE/CINE e caixa de valores no grafico" ^
 -m "  - Interacao: zoom/pan + reset, painel de camadas (liga/desliga componentes)," ^
 -m "    inspecao seguindo o perfil de T (10 hPa interpolado), seguir cliques no mapa," ^
 -m "    exportar CSV e PNG (alta-res com titulo) e marcador do ponto no mapa (__skewtMarker)" ^
 -m "  - Helpers: _skEsat/_skWsat/_skTdFromRH/_skTdFromQ/_skDryT/_skMoist; sampler 2D _skSampleSurface" ^
 -m "" ^
 -m "PERFORMANCE (P1-P3):" ^
 -m "  - Helper Python: cliente httpx global via lifespan; orjson (ORJSONResponse) + --hidden-import=orjson" ^
 -m "  - Service Worker sw.js (cache de assets); minificacao do HTML no build (scripts/minify-html.js)" ^
 -m "  - Animacao servida como PNG pelo helper; indice de cache em memoria" ^
 -m "  - Leaflet removido (vendor/ esvaziado) — nao era utilizado" ^
 -m "" ^
 -m "SEGUIR MAPA (gtPointFollow + _gtWireFollowBtn):" ^
 -m "  - Perfil vertical, perfil temporal, serie temporal em ponto, corte vertical e Skew-T:" ^
 -m "    clicar novo ponto re-renderiza o grafico sem fechar o pop-up; acompanha navegacao no tempo" ^
 -m "" ^
 -m "DOCUMENTACAO / VERSAO:" ^
 -m "  - electron-app/package.json 2.13.0 -> 2.14.0; build marker 20260609-skewt-cape" ^
 -m "  - HANDOVER_GISELE.md, docs/RELEASE_NOTES.md e README.md atualizados" ^
 -m "  - ANALISE_PERFORMANCE.md adicionado" ^
 -m "  - HTML raiz + electron-app em lockstep (md5 e00e9d80aa48add89972e3fa467b7448, ~23999 linhas)"

if errorlevel 1 (echo. & echo ERRO no commit. & pause & exit /b 1)

echo.
echo === Log dos ultimos 5 commits ===
git log --oneline -5

echo.
echo Commit v2.14.0 concluido com sucesso.
echo Para enviar ao remoto: git push origin main
pause
