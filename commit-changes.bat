@echo off
REM Commit consolidado da sessao GISELE (29/05/2026).
REM Inclui todas as alteracoes da sessao: serie temporal, video MP4,
REM mapa-base padrao por modelo, hachura/cor de miscelaneas, plataformas
REM offshore + corais brasileiros, fixes de swap PNG/GeoTIFF e contornos.

setlocal
cd /d "%~dp0"

echo.
echo === Removendo lock travado (.git\index.lock) ===
if exist ".git\index.lock" (
    del /F /Q ".git\index.lock"
    if exist ".git\index.lock" (
        echo ERRO: nao foi possivel remover .git\index.lock.
        echo Feche qualquer git/editor que possa estar travando o repo.
        pause
        exit /b 1
    )
    echo OK: lock removido.
) else (
    echo OK: sem lock pendente.
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
echo === Commit ===
git commit ^
 -m "v2.2.0 GISELE: serie temporal + video MP4 + mapa-base padrao por modelo + Miscelaneas (plataformas/corais com hachura/cor) + fixes swap PNG/GT, contornos, manual PDF 24p" ^
 -m "" ^
 -m "* Serie temporal: clique em ponto -> varre passos do slot ativo, grafico tempo x valor, CSV + PNG. Reutiliza pipeline montarURL + gtSampleDecodedAtLatLon. Fix horizonte para modelos com m.maxPassos < v.horizonte (BESM Global PREC freq=24 horizonte=720)." ^
 -m "* Salvar video MP4: pre-busca todos os passos, drawImage em canvas off-screen com object-fit/zoom-pan-clip preservados, MediaRecorder 30fps + holdAndPaint forcando emissao de frames, codec fallback MP4 -> WebM. Funciona em PNG/GIF e GeoTIFF, passagem unica do primeiro ao ultimo passo." ^
 -m "* Mapa-base padrao por modelo: campo cfgMapProvider na configuracao do modelo (none/esri/osm/topo). Auto-aplica em gtSelectPanel quando modelo muda (com flags _lastModelForMap / _mapProviderUserSet / _mapEnabledUserSet para preservar override do usuario). Ordem corrigida em setAppMode (gtSelectPanel antes de renderTudo)." ^
 -m "* Miscelaneas Plataformas offshore (107 pontos) + Corais brasileiros (11 poligonos, shapefile WCMC008 filtrado por point-in-polygon real)." ^
 -m "* Polygons com hachura diagonal via CanvasPattern (cache local), fill translucido, color picker no chip da camada, click point-in-polygon abre popup branco com infoProps." ^
 -m "* Inline <script type=application/json id=gt-misc-*> manifest + GeoJSONs no HTML para funcionar em file:// sem CORS." ^
 -m "* Fixes: contornos com keepFill default=true (shaded + isolinhas juntas), swap PNG->GeoTIFF re-snapa passo via atualizarMaxPassos + _stateRestore (legacy snap sem passoAtual), wheel zoom propagation, profile chart fundo branco com tooltip lat/lon/distancia + Salvar PNG." ^
 -m "* Manual PDF: 24 paginas. Novas secoes 10 (Ferramentas - inclui serie temporal), 11 (Miscelaneas), expansao da 4 (Salvar video MP4) e 7 (Mapa-base padrao). Troubleshooting expandido com 'Video MP4 sai escuro ou poucos frames'." ^
 -m "* Build markers: 20260528-4600-notoggle -> 20260529-1900-videofitfps."

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
