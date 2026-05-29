@echo off
REM Commit v2.6.0 GISELE - sessao 29/05/2026 (export GeoJSON + import shapefile + calc temporal)
REM Cobre tudo desde v2.5.0:
REM   - Calculadora Temporal per-layer (tN/hN + ranges + sum/mean/max/min/count)
REM   - Exportar GeoJSON: campo cheio, poligono, retangulo, camada vetorial, serie temporal
REM   - Importar shapefile (.shp/.zip) como camada vetorial + parser puro JS + ZIP via DecompressionStream
REM   - Preview + dialog de confirmacao no upload (canto direito, fora do mapa)
REM   - Renderer style.noVertices p/ shapes finos sem bolinhas
REM   - Botao 👁/⊘ explicito + dim row ao ocultar
REM   - Fix HUD lat/lon/valor default ON + toggle ERMA
REM   - Fix bbox object (decoded.bbox eh {minX,minY,maxX,maxY} nao array)
REM   - Mascara via camada vetorial carregada (substitui o upload de arquivo)
REM   - bump electron-app/package.json 2.4.0 -> 2.6.0
REM   - Atualizacao do Manual PDF + HANDOVER v2.6.0

setlocal
cd /d "%~dp0"

echo.
echo === Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\index_staging.lock .git\idx_new1.lock .git\idx_v24.lock .git\idx_v25.lock .git\idx_v26.lock .git\index_new.lock) do (
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
for %%F in (.git\index_staging .git\idx_new1 .git\idx_v24 .git\idx_v25 .git\idx_v26 .git\index_new .git\index.broken) do (
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
echo === Commit v2.6.0 ===
git commit ^
 -m "v2.6.0 GISELE: Calculadora Temporal + Exportar GeoJSON + Importar Shapefile + UX layers" ^
 -m "" ^
 -m "* Calculadora Temporal (per-layer) — sintaxe tN/hN, ranges tN..tM, funcoes sum/mean/max/min/count." ^
 -m "  - Parser estende gtParseExpr: function calls + ranges; novas funcs gtCollectTimeIdents, gtEvalTimeAst, _gtExpandRangeIdx." ^
 -m "  - Engine gtCreateLayerFromTimeExpression: resolve modelo/var/data da camada-fonte (primary ou extra com .source), fetch+decode sequencial, eval per-pixel propagando NoData." ^
 -m "  - Modal de progresso gtOpenTimeCalcProgress com botao Cancelar (AbortSignal)." ^
 -m "  - UI linha '⏱ Tempos' em gtBuildLayerConfigPanel; placeholder com exemplos sum(t1..t24), mean(h6..h72)*1000." ^
 -m "" ^
 -m "* Exportar GeoJSON (raster -> nuvem de pontos):" ^
 -m "  - Sub-no '📤 Exportar GeoJSON' no menu Ferramentas." ^
 -m "  - Modos: Campo cheio, Poligono (desenhar), Retangulo (drag), Por camada carregada (vetorial), Serie temporal de ponto." ^
 -m "  - Engine gtExportLayerToGeoJsonPointCloud: bbox da mascara restringe iteracao, NoData filtrado, cap 500k features." ^
 -m "  - Convencao top-down: row j=0 -> latMax; centro do pixel lat=latMax-(j+0.5)*dLat." ^
 -m "  - gtSampleTimeSeriesToGeoJson reusa gtSampleTimeSeries; N Features Point com properties {idx, passo_h, time_utc, value}." ^
 -m "  - Tools export-polygon, export-rect, export-timeseries aliases dos measure tools com routes diferentes em gtFinalizeDraft." ^
 -m "" ^
 -m "* Importar Shapefile como camada vetorial extra:" ^
 -m "  - gtAddExtraLayerFromFile aceita .shp e .zip (alem de .tif/.tiff/.geojson/.json)." ^
 -m "  - _gtParseShpBuffer (110 linhas): Polygon, PolygonZ, PolygonM; outer/hole pela orientacao do anel; multi-part c/ point-in-ring." ^
 -m "  - _gtExtractFromZip via DecompressionStream('deflate-raw') nativo: EOCD + central dir + LFH; suporta stored e deflate." ^
 -m "  - Smoke test Node com triangulo sintetico passou." ^
 -m "  - input multiple permite arrastar varios arquivos de uma vez." ^
 -m "" ^
 -m "* Preview + dialog de confirmacao (upload + camada vetorial):" ^
 -m "  - _gtShowPolygonPreview plota poligonos em ciano fininho (lineWidth=0.7, noVertices=true) com fit ao bbox." ^
 -m "  - gtOpenConfirmExtractDialog ancora no canto superior direito (top:14 right:14), sem backdrop fullscreen." ^
 -m "  - pointer-events:auto so no card -> permite interacao com o mapa em background." ^
 -m "  - Enter confirma, Esc cancela. Cleanup de previews em finally/catch." ^
 -m "" ^
 -m "* Substituir 'Upload mascara' por 'Por camada carregada (vetorial)':" ^
 -m "  - Filtro estendido de l.isMisc para l.type==='geojson' -> inclui Miscelaneas + Shapefiles + GeoJSONs." ^
 -m "  - Dialog mostra bolinha de cor + nome + [Origem, N features]." ^
 -m "  - Removido botao Upload e file input + handler 50 linhas." ^
 -m "" ^
 -m "* Renderer style.noVertices p/ shapes finos:" ^
 -m "  - Renderer de poligono (linha 9967+) skipava sempre desenho de circles 3px em cada vertice." ^
 -m "  - Para shapes complexos (100+ vertices) virava um massa cyan grossa." ^
 -m "  - Agora flag style.noVertices=true pula o loop; lineWidth uniforme 0.7." ^
 -m "" ^
 -m "* Toggle 👁/⊘ explicito em cada camada da arvore:" ^
 -m "  - Substituido checkbox pequeno por button 24x22px com cor cyan(on)/cinza(off)." ^
 -m "  - Row inteira recebe opacity:0.5 quando oculta (feedback visual claro)." ^
 -m "  - Funciona p/ todos os tipos: primary, geotiff extra, geojson (shapefile/misc), contour." ^
 -m "" ^
 -m "* Fix HUD lat/lon/valor:" ^
 -m "  - gtNavHudEnabled default era false (toggle escondido em .gt-old-controls)." ^
 -m "  - Agora default true; toggle visivel na toolbar da arvore ERMA espelhando legacy." ^
 -m "" ^
 -m "* Fix bbox object 'object is not iterable':" ^
 -m "  - Engine fazia const [latMin,...] = decoded.bbox; mas bbox eh {minX,minY,maxX,maxY}." ^
 -m "  - Destructuring de array sobre objeto disparava o erro Symbol(Symbol.iterator)." ^
 -m "  - Corrigido p/ leitura por campos + validacao de tipos + convencao top-down." ^
 -m "" ^
 -m "* electron-app/package.json bumped 2.4.0 -> 2.6.0 (evita lock do nome de artifact)." ^
 -m "" ^
 -m "* Documentacao:" ^
 -m "  - Manual PDF: secao 12 nova 'Exportar dados como GeoJSON' + Calc Temporal em secao 9 + import shp em secao 9 + toggle 👁/⊘." ^
 -m "  - HANDOVER v2.6.0 com secao 2.14 'Importar / Exportar dados' documentando 13 features." ^
 -m "  - 3 PDFs regerados (Manual, HANDOVER, ESPECIFICACOES)." ^
 -m "" ^
 -m "* Build markers: 20260529-4200-timecalc -> 20260529-4300-hudfix -> 20260529-4500-exportgj -> 20260529-4600-drawfix -> 20260529-4700-bboxfix -> 20260529-4800-shpzip -> 20260529-4900-previewcfm -> 20260529-5000-cardcorner -> 20260529-5100-thinline -> 20260529-5200-thinner -> 20260529-5300-novertex -> 20260529-5400-importshp -> 20260529-5500-toggleui -> 20260529-5600-vectormask."

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
echo Commit v2.6.0 concluido com sucesso.
echo Para enviar ao remoto: git push origin main
pause
