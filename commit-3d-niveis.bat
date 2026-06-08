@echo off
REM feat(config): suporte a variaveis 3D com niveis de pressao

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
 -m "feat(config): variaveis 3D com niveis de pressao" ^
 -m "" ^
 -m "Permite marcar variaveis como 3D e associar niveis de pressao" ^
 -m "(ex: 1000,925,850,700,500,300,250,200 hPa) a um modelo." ^
 -m "" ^
 -m "Config do modelo:" ^
 -m "  - Novo campo 'Niveis de pressao (hPa)' — lista separada por virgula." ^
 -m "    Armazenado em m.niveis (string)." ^
 -m "" ^
 -m "Config de variaveis:" ^
 -m "  - Nova coluna '3D' (checkbox is3d) na tabela de variaveis." ^
 -m "  - Quando marcada, a variavel usa o placeholder {nivel} no" ^
 -m "    template do arquivo (ex: {prefixo}_{nivel}hPa_{yyyymmddhh}{ext})." ^
 -m "" ^
 -m "Toolbar GeoTIFF:" ^
 -m "  - Seletor 'Nivel' (gtNivelWrap / gtNivelSel) aparece apenas" ^
 -m "    quando a variavel ativa tem is3d=true." ^
 -m "  - Opcoes populadas com os niveis do modelo (ex: '1000 hPa')." ^
 -m "  - Nivel selecionado salvo em gtSlotState.nivelAtual." ^
 -m "" ^
 -m "montarURL:" ^
 -m "  - Novo parametro 'nivel' (opcional)." ^
 -m "  - Placeholder {nivel} substituido pelo valor (ex: 1000)." ^
 -m "" ^
 -m "Propagacao do nivel:" ^
 -m "  - carregarImagem: passa nivel ao montar URL TIF (nativo e rota propria)." ^
 -m "  - gtSampleTimeSeries: _buildUrlFor recebe _nivel3dTs." ^
 -m "  - gtSamplePolygonTimeSeries: _buildUrlFor recebe _nivel3dPoly." ^
 -m "" ^
 -m "Exemplo de uso:" ^
 -m "  Modelo ZGEO: niveis = '1000,925,850,700,500,300,250,200'" ^
 -m "  Variavel ZGEO: is3d=true, arquivo='ZGEO'" ^
 -m "  Template TIF: {prefixo}_{nivel}hPa_{yyyy}{mm}{dd}{hh}{ext}" ^
 -m "  Resultado: ZGEO_1000hPa_2026060600.tif" ^
 -m "" ^
 -m "* Build marker: 20260607-0800-tif-template -> 20260608-0900-3d-niveis"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
