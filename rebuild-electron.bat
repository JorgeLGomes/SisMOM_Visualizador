@echo off
REM Reconstroi os instaladores Electron limpando processos travados.
REM Resolve o erro "output file is locked for writing".
REM
REM Causas comuns do lock:
REM   - GISELE.exe ainda rodando (instalado ou portatil)
REM   - Windows Defender / antivirus segurando o arquivo
REM   - Pasta dist\ aberta no Windows Explorer
REM   - Processo nodejs/electron-builder anterior nao morreu

setlocal
cd /d "%~dp0"

echo.
echo =========================================================
echo  REBUILD DO ELECTRON GISELE - v2.4.0
echo =========================================================
echo.

echo [1/6] Encerrando processos GISELE/Electron que podem estar travando os EXEs...
taskkill /F /IM "GISELE.exe" /T 2>nul
taskkill /F /IM "GISELE Setup 2.0.0.exe" /T 2>nul
taskkill /F /IM "GISELE Setup 2.4.0.exe" /T 2>nul
taskkill /F /IM "GISELE-2.0.0-portable.exe" /T 2>nul
taskkill /F /IM "GISELE-2.4.0-portable.exe" /T 2>nul
taskkill /F /IM "electron-builder.exe" /T 2>nul
taskkill /F /IM "electron.exe" /T 2>nul

REM Tambem mata qualquer node que possa estar rodando o builder
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
        echo Tente fechar o Windows Explorer e qualquer programa que aceda dist\,
        echo depois rode este script novamente.
        pause
        exit /b 1
    )
    echo OK: dist\ removida.
) else (
    echo OK: dist\ ja estava limpa.
)

echo.
echo [4/6] Conferindo versao do package.json ...
findstr /C:"\"version\":" package.json | findstr /C:"2.4.0" >nul
if errorlevel 1 (
    echo AVISO: package.json nao esta em v2.4.0.
    echo Edite manualmente o campo "version" se preciso.
) else (
    echo OK: package.json esta em v2.4.0.
)

echo.
echo [5/6] Reinstalando dependencias (npm install)...
call npm install
if errorlevel 1 (
    echo ERRO em npm install.
    pause
    exit /b 1
)

echo.
echo [6/6] Gerando instaladores Windows (NSIS + portavel)...
call npm run dist:win
if errorlevel 1 (
    echo.
    echo ERRO durante o build.
    echo.
    echo Possiveis causas:
    echo   - Antivirus bloqueando ainda (pausar temporariamente)
    echo   - Falta de permissao de escrita em dist\
    echo   - Processo travado em segundo plano (reiniciar Windows ajuda)
    echo.
    pause
    exit /b 1
)

echo.
echo =========================================================
echo  BUILD CONCLUIDO COM SUCESSO
echo =========================================================
echo.
echo Saidas em electron-app\dist\:
dir /b electron-app\dist\*.exe 2>nul
dir /b electron-app\dist\GISELE-standalone.html 2>nul
echo.

pause
