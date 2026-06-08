@echo off
REM feat: todas as ferramentas iniciam na condicao inicial T+0 (analise 0000h)

setlocal
cd /d "%~dp0"

echo.
echo === Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === Stage + Commit ===
git read-tree HEAD
if errorlevel 1 (echo ERRO read-tree. & pause & exit /b 1)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

git commit ^
 -m "feat: ferramentas iniciam na condicao inicial T+0 (analise 0000h)" ^
 -m "" ^
 -m "Todas as ferramentas que geram listas de passos agora incluem passo=0" ^
 -m "(analise T+0) como primeiro ponto quando passo_inicio da variavel = 0 (default)." ^
 -m "" ^
 -m "FERRAMENTAS AFETADAS:" ^
 -m "  - gtSampleTimeSeries (serie temporal por ponto): idxMin usa passo_inicio" ^
 -m "    em vez de 1 fixo. Para passo_inicio=0: idxMin=0 -> file_idx=0 -> T+0." ^
 -m "  - gtSamplePolygonTimeSeries (serie temporal por poligono): idem." ^
 -m "  - Video MP4 (gravarVideoEvolucaoTemporal): stepValues inclui 0 quando" ^
 -m "    state.passoInicio===0." ^
 -m "  - Calculadora temporal (_gtIdentToFileIdx): t0 e h0 sao validos agora." ^
 -m "" ^
 -m "COMPATIBILIDADE: variavel com passo_inicio=N (N>0) continua comecando em N." ^
 -m "Para variaveis sem analise no FTP, basta configurar passo_inicio=freq na aba" ^
 -m "de configuracoes (ex: passo_inicio=1 para Eta 1h sem analise). Default 0." ^
 -m "" ^
 -m "passoMin agora aceita >=0 (antes so >0) para permitir passoMin=0 explicito." ^
 -m "" ^
 -m "* Build marker: 20260605-2300-passo0-url -> 20260605-2400-ts-passo0"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -5
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: OK || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou) else (echo Push OK.)
pause
