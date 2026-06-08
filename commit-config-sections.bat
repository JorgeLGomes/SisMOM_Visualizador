@echo off
REM refactor(config): secoes Imagem Web / GeoTIFF + remover cfgSameTif

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
 -m "refactor(config): secoes Imagem Web / GeoTIFF + remover cfgSameTif" ^
 -m "" ^
 -m "SECOES no formulario de configuracao do modelo:" ^
 -m "  Secao 1 - Imagem Web (.png/.gif/.jpg):" ^
 -m "    - Cabecalho visual 'IMAGEM WEB' com linha separadora e hint de extensoes" ^
 -m "    - Template do endereco + Sufixo (.png/.gif/.jpg/.jpeg) + Template Nome Arq." ^
 -m "  Secao 2 - GeoTIFF (.tif/.tiff):" ^
 -m "    - Cabecalho visual 'GeoTIFF' com linha separadora e hint de extensoes" ^
 -m "    - Template (caminho/arquivo) — campo full-width sem checkbox 'usar o mesmo'" ^
 -m "    - Sufixo TIF (.tif/.tiff) + preview de split com avisos" ^
 -m "" ^
 -m "REMOCAO de cfgSameTif:" ^
 -m "  - Checkbox 'usar o mesmo do PNG' removido" ^
 -m "  - syncCurrentPaneToDraft: sempre same_url_for_tif=false, same_name_for_tif=false" ^
 -m "  - Template TIF vazio = fallback para rota da Imagem Web (_buildMTifModel)" ^
 -m "  - Retrocompat: modelos antigos com same_*=true e campos TIF vazios continuam" ^
 -m "    funcionando (tifInp.value = '' ao carregar)" ^
 -m "" ^
 -m "SUFIXOS:" ^
 -m "  - cfgExtensao (Imagem Web): .png .gif .jpg .jpeg (removidos .tif e .tiff)" ^
 -m "  - cfgExtensaoTif (GeoTIFF): .tif .tiff (sem alteracao)" ^
 -m "" ^
 -m "FORMATOS DISPONIVEIS:" ^
 -m "  - Label 'PNG/GIF' -> 'PNG/GIF/JPEG' (reflete suporte a JPEG)" ^
 -m "" ^
 -m "PREVIEW TIF:" ^
 -m "  - Aviso amarelo adicionado: nome sem extensao (falta {ext} ou .tif)" ^
 -m "  - Aviso vermelho existente: extensao PNG/GIF no nome TIF" ^
 -m "" ^
 -m "* Build marker: 20260608-1100-3d-nivel-fix -> 20260608-1200-config-sections"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
