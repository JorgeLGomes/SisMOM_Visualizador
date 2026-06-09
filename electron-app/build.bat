@echo off
REM ============================================================
REM  GISELE - Build automatizado (Windows)
REM ============================================================
REM  1) Sincroniza o HTML da raiz para electron-app/
REM  2) Garante dependencias instaladas
REM  3) Limpa dist/ antiga
REM  4) Gera instalador NSIS + portavel via electron-builder
REM  5) Monta pacote "standalone" (HTML sem precisar instalar nada)
REM  6) Zipa o standalone
REM
REM  Pre-requisito: Node.js LTS instalado (https://nodejs.org)
REM  Saida: electron-app\dist\
REM ============================================================

setlocal enableextensions

cd /d "%~dp0"

echo.
echo [1/6] Sincronizando figuras_SisMOM_v23.html da raiz...
copy /Y "..\figuras_SisMOM_v23.html" "figuras_SisMOM_v23.html" >nul
if errorlevel 1 (
    echo ERRO: nao foi possivel copiar o HTML da raiz.
    pause
    exit /b 1
)
rem Service worker (P2.2) — copia da raiz para o pacote
if exist "..\sw.js" copy /Y "..\sw.js" "sw.js" >nul

echo.
echo [2/6] Instalando dependencias (npm install)...
call npm install
if errorlevel 1 (
    echo ERRO: npm install falhou.
    pause
    exit /b 1
)

echo.
echo [2b/6] Minificando HTML (P1.3 — falha aqui nao interrompe o build)...
call npm run minify

echo.
echo [3/6] Limpando dist\ antiga...
if exist dist rmdir /s /q dist

echo.
echo [4/6] Gerando instalador Windows (NSIS + portavel)...
call npm run dist:win
if errorlevel 1 (
    echo ERRO: electron-builder falhou.
    pause
    exit /b 1
)

echo.
echo [5/6] Montando pacote standalone (HTML sem instalacao)...
for /f "tokens=2 delims=:," %%v in ('findstr /c:"\"version