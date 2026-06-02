@echo off
REM Commit v2.12.1 GISELE - sessao 02/06/2026
REM   Render do raster GeoTIFF: interpolado (bilinear) + modos Sombreado
REM   (Suavizado | Bandas | Pixel) + BANDAS POR NIVEL (faixas = niveis do contorno).
REM   HEAD (v2.12.0 = 0e5647a) ficou no marker 18500-cfgpath; isto agrupa todo o
REM   trabalho de render desde entao. bump 2.12.0 -> 2.12.1.

setlocal
cd /d "%~dp0"

echo.
echo === Removendo locks travados (.git\*.lock) ===
for %%F in (.git\index.lock .git\index_new.lock) do (
    if exist "%%F" ( del /F /Q "%%F" 2>nul & if exist "%%F" (echo AVISO: nao removeu %%F) else (echo OK: %%F removido.) )
)

echo.
echo === Reconstruindo o index a partir do HEAD ===
git read-tree HEAD
if errorlevel 1 (echo ERRO ao reconstruir o index. & pause & exit /b 1)

echo.
echo === Revertendo ruido de fim-de-linha (CRLF) fora do escopo ===
git checkout -- vendor/leaflet.css COMO-USAR.txt SisMOM.bat 2>nul

echo.
echo === Adicionando v2.12.1 (HTMLs + handover + versao) ===
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html
git add HANDOVER_GISELE.md
git add electron-app/package.json electron-app/package-lock.json

echo.
echo === Status pre-commit ===
git update-index --refresh > nul 2>&1
git status --short

echo.
echo === Commit v2.12.1 ===
git commit ^
 -m "v2.12.1 GISELE: raster GeoTIFF interpolado + modos Suavizado/Bandas/Pixel + bandas por nivel" ^
 -m "" ^
 -m "RENDER (continuacao do v2.12.0; HEAD estava em marker 18500-cfgpath):" ^
 -m "  - Raster GeoTIFF INTERPOLADO (bilinear): _drawOneRaster com imageSmoothingEnabled +" ^
 -m "    bitmap pre-upscalado (_smoothRasterBitmap) -> shading suave, nao pixelado (inclusive" ^
 -m "    na vertical do fatiamento Mercator)." ^
 -m "  - Seletor 'Sombreado' no painel de config (abaixo de Contornos): Suavizado | Bandas |" ^
 -m "    Pixel. gtSetRasterMode (localStorage gisele.raster.mode) seta estaticas" ^
 -m "    SisMOM_Map.rasterSmooth (interpola, lida por _drawOneRaster) e SisMOM_GeoTIFF.setBands." ^
 -m "  - Bandas (shaded) = paleta quantizada + interpolacao das bordas -> definicao sem borrar." ^
 -m "  - BANDAS POR NIVEL: as faixas do shaded seguem os MESMOS niveis do contorno (campo" ^
 -m "    Niveis custom, ou N no modo auto) via gtUpdateBandLevels -> SisMOM_GeoTIFF.setBandLevels;" ^
 -m "    aplicarPaleta mapeia v->faixa pelos limites e usa a cor do ponto medio. Mudar Niveis/N" ^
 -m "    no modo Bandas re-renderiza o shaded (handler nos inputs de contorno -> gtRerenderAllRasters)." ^
 -m "    Contorno e shaded passam a compartilhar exatamente os mesmos niveis." ^
 -m "  - Trocar de modo limpa _gtImgDataCache/_gtBlobUrlCache e re-renderiza (gtRerenderAllRasters" ^
 -m "    -> gtRerenderSlot por slot + re-push das geotiff extras + redraw)." ^
 -m "" ^
 -m "INFRA: package.json + package-lock.json 2.12.0 -> 2.12.1" ^
 -m "* Build marker: 20260601-18500-cfgpath -> 20260601-20400-bandlevels"

if errorlevel 1 (echo. & echo ERRO no commit. & pause & exit /b 1)

echo.
echo === Limpando script de commit obsoleto ===
del /F /Q commit-v2.12.0.bat 2>nul

echo.
echo === Log dos ultimos 5 commits ===
git log --oneline -5

echo.
echo === Enviando para origin/main (git push) ===
git push origin main
if errorlevel 1 (
    echo.
    echo AVISO: o push falhou. Verifique conexao/credenciais e rode manualmente:  git push origin main
) else (
    echo Push para origin/main concluido.
)

echo.
echo Commit + push v2.12.1 concluidos.
echo (rode rebuild-electron.bat p/ gerar o .exe se quiser distribuir.)
pause
