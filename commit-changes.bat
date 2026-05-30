@echo off
REM Commit v2.9.0 GISELE - sessao 30/05/2026 (Multipainel + Poligonos do usuario + UI reorg + Graficos)
REM Cobre tudo desde v2.8.0:
REM   - Python helper: in-memory decoded cache + endpoint /v1/render/png (matplotlib) + bridge JS renderTilePNG
REM   - Poligonos do usuario: storage localStorage + dialog + tree + gear/trash/color/perimetro + import/export GeoJSON
REM   - UI reorg: Lat/Lon/Valor em Ferramentas, DnD reorder, boot colapsado, gear inline em Camadas
REM   - Multipainel: viewport sync, lock per slot, replicacao acoes, perfil/TS combinados
REM   - Graficos: toggle on/off com olho, zoom drag, clipping, amostragem paralela TS

setlocal
cd /d "%~dp0"

echo.
echo === Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\idx_v28.lock .git\idx_v29.lock .git\index_new.lock) do (
    if exist "%%F" (
        del /F /Q "%%F" 2>nul
        if exist "%%F" (echo AVISO: nao removeu %%F) else (echo OK: %%F removido.)
    )
)

echo.
echo === Limpando index intermediarios ===
for %%F in (.git\idx_v28 .git\idx_v29 .git\index_new .git\index.broken) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === Reconstruindo o index a partir do HEAD ===
git read-tree HEAD
if errorlevel 1 (echo ERRO ao reconstruir o index. & pause & exit /b 1)

echo.
echo === Status pre-commit ===
git update-index --refresh > nul 2>&1
git status --short

echo.
echo === Adicionando todas as mudancas ===
git add -A
if errorlevel 1 (echo ERRO ao executar git add. & pause & exit /b 1)

echo.
echo === Commit v2.9.0 ===
git commit ^
 -m "v2.9.0 GISELE: Multipainel + Poligonos do usuario + UI reorg + Graficos interativos" ^
 -m "" ^
 -m "PYTHON HELPER (server.py v0.6.0):" ^
 -m "  - In-memory decoded cache (LRU OrderedDict, GISELE_DECODED_CACHE_MAX=256)" ^
 -m "  - Endpoint /v1/render/png: aplica paleta matplotlib + auto vmin/vmax percentil 5-95 + NoData->alpha=0" ^
 -m "  - Hierarquia 4 niveis: png cache -> decoded cache -> disk cache -> FTP" ^
 -m "  - /health reporta stats decoded_cache + png_cache" ^
 -m "  - requirements.txt: matplotlib==3.9.2, Pillow==10.4.0, h2==4.1.0" ^
 -m "" ^
 -m "BRIDGE JS (figuras_SisMOM_v23.html):" ^
 -m "  - gtPyHelper.renderTilePNG(url, opts) retorna ImageBitmap (createImageBitmap)" ^
 -m "  - Opt-in, nao altera caminho principal de animacao" ^
 -m "" ^
 -m "POLIGONOS DO USUARIO (modulo novo):" ^
 -m "  - gtSavedPolygons localStorage backing (gisele.savedPolygons.v1)" ^
 -m "  - Submenu Ferramentas -> 'Poligonos do usuario' com lista colapsavel" ^
 -m "  - Acoes: Desenhar e salvar / Exportar GeoJSON / Importar GeoJSON" ^
 -m "  - Por linha: checkbox visualizacao + gear (renomeia/perimetro/area) + color picker + trash" ^
 -m "  - Toggled ON aparece em 'Por camada vetorial' (Exportar GeoJSON) automaticamente" ^
 -m "" ^
 -m "REORGANIZACAO UI:" ^
 -m "  - Lat/Lon/Valor movido toolbar -> Ferramentas (titulo capitalizado)" ^
 -m "  - DnD reorder de Ferramentas via grip (gisele.tools.order.v1)" ^
 -m "  - Boot sempre colapsado (4 secoes top-level sem 'open')" ^
 -m "  - Camadas: gear inline + trash substituem details 'Ferramentas' + botao x" ^
 -m "" ^
 -m "MULTIPAINEL:" ^
 -m "  - SisMOM_Map ganhou getViewport/applyViewportRaw/setViewportChangeListener" ^
 -m "  - Pan/zoom em qualquer painel propaga para todos (sync de viewport)" ^
 -m "  - _gtApplyMapView: slots !=0 copiam vp do painel 1 ao trocar modelo (preserva area)" ^
 -m "  - Trocar modelo em slot !=0 alinha data inicial ao painel 1" ^
 -m "  - Lock por painel (botao 🔒/🔓 ao lado do pin)" ^
 -m "  - Replicacao para travados: distancia, linha, texto, perfil, limpar anotacoes" ^
 -m "  - Perfil combinado: amostra todos paineis-alvo, curvas coloridas, CSV combinado" ^
 -m "  - Serie temporal: amostragem PARALELA via Promise.all + progress agregado + CSV combinado" ^
 -m "" ^
 -m "GRAFICOS INTERATIVOS (TS + Perfil):" ^
 -m "  - Toggle on/off por chip da legenda (icone olho/proibido)" ^
 -m "  - Zoom por click-and-drag (rubber-band) + double-click reseta + botao reset" ^
 -m "  - Clipping (ctx.save + rect + clip + restore) evita curvas vazando fora do plot" ^
 -m "  - Y range auto-zoom sobre series visiveis" ^
 -m "" ^
 -m "DOCUMENTACAO:" ^
 -m "  - HANDOVER_GISELE.md v2.8.0 -> v2.9.0 com bloco 'Mudancas v2.8 -> v2.9'" ^
 -m "  - electron-app/package.json 2.8.0 -> 2.9.0" ^
 -m "" ^
 -m "* Build markers: 20260529-7100-pyhelper -> 20260530-9600-clip"

if errorlevel 1 (echo. & echo ERRO no commit. & pause & exit /b 1)

echo.
echo === Log dos ultimos 5 commits ===
git log --oneline -5

echo.
echo Commit v2.9.0 concluido com sucesso.
echo Para enviar ao remoto: git push origin main
pause
