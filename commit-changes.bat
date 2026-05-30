@echo off
REM Commit v2.8.0 GISELE - sessao 29-30/05/2026 (Export GeoJSON stats + UX)
REM Cobre tudo desde v2.7.0:
REM   - Estatisticas no metadata do GeoJSON exportado (min/max/sum/mean/areaWeightedMean/totalAreaM2)
REM   - Popup com stats + botao Salvar GeoJSON (sem auto-save)
REM   - Reorganizacao da arvore Exportar GeoJSON: 5 opcoes top-level
REM   - Serie temporal em ponto INTEGRADA no Exportar GeoJSON (substitui Por ponto)
REM   - Icone "?" com popup help substituindo descricoes inline
REM   - Highlight visual da opcao selecionada
REM   - electron-app/package.json 2.7.0 -> 2.8.0
REM   - Manual + HANDOVER v2.8.0 regenerados

setlocal
cd /d "%~dp0"

echo.
echo === Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\idx_v27.lock .git\idx_v28.lock .git\index_new.lock) do (
    if exist "%%F" (
        del /F /Q "%%F" 2>nul
        if exist "%%F" (echo AVISO: nao removeu %%F) else (echo OK: %%F removido.)
    )
)

echo.
echo === Limpando index intermediarios ===
for %%F in (.git\idx_v27 .git\idx_v28 .git\index_new .git\index.broken) do (
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
echo === Commit v2.8.0 ===
git commit ^
 -m "v2.8.0 GISELE: Export GeoJSON com stats + popup confirm + reorganizacao UX" ^
 -m "" ^
 -m "* Estatisticas no metadata.stats do GeoJSON exportado:" ^
 -m "  - count, min, max, sum, mean, areaWeightedMean, totalAreaM2" ^
 -m "  - Computadas durante a iteracao do export (sem segundo passe)" ^
 -m "  - Area em m^2 via formula esferica: R^2 * dLon * |sin(latTop)-sin(latBot)| * 1e6" ^
 -m "  - Media ponderada = Soma / Area(km^2) — densidade por area conforme pedido" ^
 -m "" ^
 -m "* Popup de resultado (sem auto-save):" ^
 -m "  - gtExpShowResultDialog: card 380px canto superior direito (fora do mapa)" ^
 -m "  - Tabela formatada: Minimo, Maximo, Soma, Media, Media ponderada, Area total" ^
 -m "  - Formatador inteligente: cientifico para |v| >= 1e6 ou < 0.01; pt-BR locale" ^
 -m "  - Botoes Fechar / Salvar GeoJSON; Enter salva, Esc fecha" ^
 -m "  - pointer-events:auto so no card — permite interagir com o mapa em background" ^
 -m "" ^
 -m "* Reorganizacao da arvore Exportar GeoJSON (5 opcoes top-level flat):" ^
 -m "  - Serie temporal em ponto (substituiu Por ponto single-pixel)" ^
 -m "  - Por poligono (desenhar)" ^
 -m "  - Por retangulo (clicar e arrastar)" ^
 -m "  - Por camada vetorial (shape, geojson)" ^
 -m "  - Area total da camada (era Campo cheio)" ^
 -m "  - Sub-tree separado de Serie temporal removido (consolidado no Exportar)" ^
 -m "  - btnGtExpPoint + tool export-point removidos da UI (funcoes ficam no codigo)" ^
 -m "" ^
 -m "* Icone (?) com popup de help:" ^
 -m "  - CSS .gt-help-icon (circulo 14px) + .gt-help-popup (card branco)" ^
 -m "  - gtShowHelpPopup com auto-posicionamento (reposiciona se sair da tela)" ^
 -m "  - Delegacao global em fase de captura: document.addEventListener('click', ..., true)" ^
 -m "  - Esc fecha; click fora fecha; click dentro do popup nao fecha (permite copiar texto)" ^
 -m "  - Aplicado em: Calculadora, Exportar GeoJSON, Tempos" ^
 -m "  - Descricoes inline removidas das tres secoes" ^
 -m "" ^
 -m "* Highlight visual da opcao selecionada em Exportar GeoJSON:" ^
 -m "  - CSS .gt-tree-action.selected: bg cyan 16%% + border solid cyan + texto cyan + font-weight 600 + bullet pseudo-element" ^
 -m "  - _GT_EXP_TOOL_TO_BTN mapeia tool->botao" ^
 -m "  - gtSetSlotTool sincroniza highlight automaticamente — qualquer caminho que muda tool propaga" ^
 -m "  - Por camada vetorial: highlight manual no open do dialog; clear no Cancel/OK/erro" ^
 -m "  - Area total: animacao gtExpFlash (600ms ease-in-out) como feedback do trigger imediato" ^
 -m "  - Limpeza defensiva em todos os caminhos de erro do confirm dialog" ^
 -m "" ^
 -m "* Documentacao:" ^
 -m "  - HANDOVER_GISELE.md v2.7.0 -> v2.8.0 com bloco 'Mudancas v2.7 -> v2.8' + secao 2.16 (Export stats + UX) com 10 features mapeadas" ^
 -m "  - 3 PDFs regerados (Manual, HANDOVER, ESPECIFICACOES mantido)" ^
 -m "  - electron-app/package.json 2.7.0 -> 2.8.0" ^
 -m "" ^
 -m "* Build markers: 20260529-6300-expstats -> 6400-exppopup -> 6500-areadiv -> 6600-bypoint -> 6700-polynest -> 6800-tsinexp -> 6900-helpicon -> 7000-highlight."

if errorlevel 1 (echo. & echo ERRO no commit. & pause & exit /b 1)

echo.
echo === Log dos ultimos 5 commits ===
git log --oneline -5

echo.
echo Commit v2.8.0 concluido com sucesso.
echo Para enviar ao remoto: git push origin main
pause
