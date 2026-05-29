@echo off
REM Commit v2.5.0 GISELE - sessao 29/05/2026 (final)
REM Cobre tudo desde o commit v2.4.0:
REM   - Fix Background Esri nao plota (mapEnabled default + apply tiles ao trocar radio)
REM   - Fix Miscelaneas v1..v4 (plot + ordem canvas + resize() + ReferenceError gtFindMiscLayerByConfigId)
REM   - Remover "Abrir TIF local (inspecao)" do menu Ferramentas
REM   - bump versao 2.0.0 -> 2.4.0 (electron-app/package.json)
REM   - rebuild-electron.bat com taskkill agressivo
REM   - Atualizacao do manual PDF (secao 6 arvore ERMA, secao 9 calc dupla, secao 11 checkbox)
REM   - Atualizacao do HANDOVER (v2.5.0 + secao 2.13 UI v2.4+)
REM   - Regeneracao dos 3 PDFs (Manual, HANDOVER, ESPECIFICACOES)

setlocal
cd /d "%~dp0"

echo.
echo === Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\index_staging.lock .git\idx_new1.lock .git\idx_v24.lock .git\idx_v25.lock .git\index_new.lock) do (
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
for %%F in (.git\index_staging .git\idx_new1 .git\idx_v24 .git\idx_v25 .git\index_new .git\index.broken) do (
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
echo === Commit v2.5.0 ===
git commit ^
 -m "v2.5.0 GISELE: fix Background Esri + fix Miscelaneas v1..v4 + remove Abrir TIF local + bump 2.4.0 + docs v2.4+" ^
 -m "" ^
 -m "* Fix Background Esri nao plota no executavel: cfgMapEnabled default=true + cfgMapProvider='esri' em gtSlotState; radio change chama _gtApplyMapView imediatamente em vez de esperar o proximo gtRerenderSlot." ^
 -m "* Fix Miscelaneas (Plataformas/Corais) nao plotam:" ^
 -m "  - v1: gtLayerPushToMap retornava early se maps.length===0 (slot sem TIF nao tinha mapa); agora cria SisMOM_Map mesmo sem raster com bbox default Brasil." ^
 -m "  - v2: ordem critica em gtLayerEnsureMap: box.classList.add('gt-map-active') ANTES de cvEl.style.display='' ANTES de void cvEl.offsetWidth (reflow) ANTES de gtSlotEnsureMap." ^
 -m "  - v3: SisMOM_Map API expoe resize() e getCanvasRect(); chamado apos push extra layer pra recalcular dims do canvas." ^
 -m "  - v4 (REAL FIX): Uncaught ReferenceError: gtFindMiscLayerByConfigId is not defined. Funcao foi removida no commit anterior (remocao do toggle Liga/Desliga) mas o tree handler ainda a chamava. Re-adicionei + chamadas defensivas com typeof." ^
 -m "* Remover do menu Ferramentas o sub-no 'Abrir TIF local (inspecao)' (gt-tree-tif-inspect): use '+ Adicionar GeoTIFF/GeoJSON' ou a aba dedicada do header." ^
 -m "* Bump versao 2.0.0 -> 2.4.0 (electron-app/package.json) pra forcar nome de artifact novo e evitar 'output file is locked for writing' no electron-builder." ^
 -m "* rebuild-electron.bat com taskkill /F /IM GISELE-*.exe + WMIC node electron-builder + ping 4 (3s wait) + clean dist + npm install + npm run dist:win." ^
 -m "* Manual PDF atualizado:" ^
 -m "  - Secao 6 'Painel direito' reescrita pra descrever a arvore ERMA com 4 grupos colapsaveis (Background/Miscelanea/Camadas/Ferramentas), Configuracao da Camada como sub-menu por no, botao Collapse/Expand folders." ^
 -m "  - Secao 9 'Camadas e calculadora dupla' descreve as duas modalidades: Ferramentas (expressao livre entre camadas com tokens clicaveis) + Configuracao da Camada (operador + escalar per-layer)." ^
 -m "  - Secao 11 'Miscelaneas' atualiza fluxo de adicao via checkbox marcado/desmarcado em vez de dropdown + botao." ^
 -m "* HANDOVER_GISELE.md/.pdf atualizado pra v2.5.0:" ^
 -m "  - Build marker 20260529-3600-removetiflocal." ^
 -m "  - Bloco de mudancas v2.4 -> v2.5 no topo." ^
 -m "  - Tabela 2.4 estendida com Calculadora v2 (expressao + per-layer)." ^
 -m "  - Nova secao 2.13 'UI v2.4+ (arvore ERMA-style)' documentando 17 mudancas com prompts originais + ferramentas." ^
 -m "  - Secao 2.12 'Documentacao' lista ESPECIFICACOES_GISELE + manual v2.4." ^
 -m "* PDFs regerados:" ^
 -m "  - docs/GISELE_Manual_Uso.pdf (reportlab via gerar_manual_uso.py)." ^
 -m "  - docs/HANDOVER_GISELE.pdf (reportlab via parser markdown proprio - pandoc/xelatex falhou no C:\Projetos backslash)." ^
 -m "  - docs/ESPECIFICACOES_GISELE.pdf (mantido)." ^
 -m "* Build markers: 20260529-3000-calc -> 20260529-3600-removetiflocal."

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
