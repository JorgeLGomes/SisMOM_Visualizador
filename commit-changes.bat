@echo off
REM Script para finalizar o commit das mudancas do GISELE
REM (ferramentas + Miscelaneas + hachura + cor + popup info + manual atualizado).
REM Remove um index.lock travado e executa o commit com mensagem detalhada.

setlocal
cd /d "%~dp0"

echo.
echo === Removendo lock travado (.git\index.lock) ===
if exist ".git\index.lock" (
    del /F /Q ".git\index.lock"
    if exist ".git\index.lock" (
        echo ERRO: nao foi possivel remover .git\index.lock.
        echo Verifique se algum git/editor esta aberto.
        pause
        exit /b 1
    )
    echo OK: lock removido.
) else (
    echo OK: nao ha lock pendente.
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
echo === Atualizando status do working tree ===
git update-index --refresh
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
git commit -m "v2.1.0 GISELE: ferramentas (perfil/distancia/area/retangulo/circulo), Miscelaneas (Plataformas offshore + Corais BR), hachura diagonal, cor configuravel, popup info por shape, manual PDF 21p" -m "" -m "* Ferramentas: distancia (Haversine), area esferica, retangulo (lat/lon), circulo (raio km / area km2), polilinha simples, texto, perfil." -m "* Perfil: amostra a camada ATIVA ao longo da polilinha. Popup branco responsivo com tooltip lat/lon/distancia/valor + botao Salvar PNG." -m "* Fix wheel duplo (canvas + mapBody) em modo GeoTIFF; ferramentas seguem disponiveis durante zoom/pan." -m "* Miscelaneas: dir miscelaneas/ com manifest.json e dois GeoJSON (plataformas offshore + corais da costa brasileira)." -m "* Plataformas offshore (107 pontos rotulados, popup com operadora/campo/bacia/status/oleo/historico de derramamentos)." -m "* Corais brasileiros (shapefile WCMC008 -> 11 polygons na costa, filtrados por point-in-polygon real)." -m "* Hachura diagonal nos poligonos via CanvasPattern (cache local por cor/spacing); fill translucido por baixo." -m "* Color picker no chip de cada camada misc -> recolore stroke + hachura + fill rgba preservando alpha." -m "* Click no shape (Pan mode) -> popup branco com infoProps; point-in-polygon respeita buracos; pontos tolerancia ~10px." -m "* Tags <script type='application/json' id='gt-misc-*'> inline -> funciona em file:// (sem fetch)." -m "* Manual PDF atualizado (21 paginas): novas secoes 10 (Ferramentas) e 11 (Miscelaneas); secoes seguintes renumeradas." -m "* Build markers: 20260528-4500-coraistail -> 4600-notoggle."

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
pause
