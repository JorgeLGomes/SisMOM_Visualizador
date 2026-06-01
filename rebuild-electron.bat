@echo off
REM Reconstroi os instaladores Electron do GISELE.
REM - Limpa processos/handles que travam os EXEs ("output file is locked for writing")
REM - Decide SUCESSO pela existencia do artefato em dist\ (e nao apenas pelo errorlevel,
REM   que pode vir != 0 por avisos benignos, ex.: extraResource python-helper\dist ausente)
REM
REM Causas comuns do lock: GISELE.exe rodando, antivirus, dist\ aberta no Explorer,
REM ou node/electron-builder anterior que nao morreu.

setlocal
cd /d "%~dp0"

echo.
echo =========================================================
echo  REBUILD DO ELECTRON GISELE
echo =========================================================
echo.

echo [1/6] Encerrando processos GISELE/Electron que travam os EXEs...
taskkill /F /IM "GISELE.exe" /T 2>nul
taskkill /F /IM "electron.exe" /T 2>nul
taskkill /F /IM "electron-builder.exe" /T 2>nul
echo Procurando processos node do electron-builder...
wmic process where "name='node.exe' and commandline like '%%electron-builder%%'" call terminate 2>nul

echo.
echo [2/6] Esperando 3 segundos para o sistema liberar os handles...
ping -n 4 127.0.0.1 >nul

echo.
echo [3/6] Limpando pasta dist\ ...
cd electron-app
if exist dist (
    rmdir /S /Q dist
    if exist dist (
        echo AVISO: nao foi possivel remover dist\ completamente.
        echo Feche o Windows Explorer e qualquer EXE do GISELE e rode de novo.
        pause
        exit /b 1
    )
    echo OK: dist\ removida.
) else (
    echo OK: dist\ ja estava limpa.
)

echo.
echo [4/6] Versao do package.json ...
set "PKGVER="
for /f "delims=" %%v in ('node -p "require('./package.json').version" 2^>nul') do set "PKGVER=%%v"
if defined PKGVER (echo   versao atual = %PKGVER%) else (echo   (nao foi possivel ler a versao via node))

echo.
echo [5/6] Reinstalando dependencias (npm install)...
call npm install
if errorlevel 1 (echo ERRO em npm install. & pause & exit /b 1)

echo.
echo [6/6] Gerando instaladores Windows (NSIS + portavel + standalone)...
call npm run dist:win

echo.
echo === Verificando artefatos gerados em dist\ ===
set "BUILT="
if exist "dist\*.exe" set "BUILT=1"

if defined BUILT (
    echo.
    echo =========================================================
    echo  BUILD CONCLUIDO COM SUCESSO  ^(v%PKGVER%^)
    echo =========================================================
    echo Instaladores em electron-app\dist\:
    for %%f in (dist\*.exe) do echo   %%~nxf
    for %%f in (dist\*.zip) do echo   %%~nxf
    echo.
    echo Nota: o aviso "file source doesn't exist ... python-helper\dist" e ESPERADO
    echo quando o helper Python nao foi compilado. O app funciona com fallback JS.
    echo Para empacotar o helper, rode antes: python-helper\build-helper.bat
) else (
    echo.
    echo =========================================================
    echo  ERRO: nenhum instalador .exe foi gerado em dist\
    echo =========================================================
