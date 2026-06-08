@echo off
REM feat: toolbar sticky + passo_inicio por variavel + grid começa em 0000

setlocal
cd /d "%~dp0"

echo.
echo === [1/3] Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/3] Stage ===
git read-tree HEAD
if errorlevel 1 (echo ERRO read-tree. & pause & exit /b 1)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

echo.
echo === [3/3] Commit ===
git commit ^
 -m "feat: toolbar sticky + passo_inicio por variavel + grid começa em 0000" ^
 -m "" ^
 -m "1) TOOLBAR GEOTIFF STICKY: #gtToolbar recebe position:sticky;top:0;z-index:10" ^
 -m "   para permanecer visivel mesmo quando o conteudo abaixo rola. Fundo levemente" ^
 -m "   mais opaco para melhor contraste." ^
 -m "" ^
 -m "2) PASSO_INICIO POR VARIAVEL: novo campo na tabela de configuracao de variaveis" ^
 -m "   — coluna 'Inicio (h)' (data-vfield=passo_inicio, default 0). Permite definir" ^
 -m "   o primeiro passo disponivel por variavel. Valor 0 indica que a analise T+0" ^
 -m "   esta disponivel; valores > 0 pulam os primeiros passos ausentes no FTP." ^
 -m "   Armazenado em v.passo_inicio; lido em atualizarMaxPassos (state.passoInicio)." ^
 -m "" ^
 -m "3) GRID DE PASSOS COMECA EM 0000: quando passo_inicio === 0 (default), o grid" ^
 -m "   de botoes de tempo inclui o passo 0 (T+0h = analise). Antes o grid sempre" ^
 -m "   comecava em stepFreq (primeiro forecast, ex: 1h ou 6h). Agora:" ^
 -m "     - _hStart = 0 quando passoInicio = 0" ^
 -m "     - Loop: h=0, depois h=step, depois h+=step (pula de 0 para step corretamente)" ^
 -m "     - setPasso aceita novo=0 (piMin=0 quando passoInicio=0)" ^
 -m "     - stepRange.min = 0 quando passoInicio = 0" ^
 -m "     - Cache key do grid inclui passoInicio (reconstroi ao mudar)" ^
 -m "   URL gerado para passo=0: file_idx=0, F=0000, N=0 — arquivo de analise." ^
 -m "" ^
 -m "* Build marker: 20260605-1100-tiledpredictor -> 20260605-2200-toolbar-passo0"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou) else (echo Push OK.)
pause
