@echo off
REM ============================================================
REM  GISELE - Servidor local de dados (Windows)
REM
REM  Uso:
REM    1) Duplo-clique para servir a pasta ATUAL (do .bat).
REM    2) Arraste uma pasta SOBRE este .bat para servir aquela.
REM    3) Linha de comando:  servir_dados.bat [pasta] [porta]
REM
REM  Requer: Python 3 OU Node.js (qualquer um). Detecta automaticamente.
REM ============================================================

setlocal enableextensions
title GISELE - Servidor local de dados

REM ---- Argumentos ----
set "DATA_DIR=%~1"
set "PORTA=%~2"
if "%DATA_DIR%"=="" set "DATA_DIR=%CD%"
if "%PORTA%"=="" set "PORTA=8770"

REM ---- Verifica pasta ----
if not exist "%DATA_DIR%\" (
    echo ERRO: "%DATA_DIR%" nao e uma pasta valida.
    pause
    exit /b 1
)

cd /d "%~dp0"

REM ---- Tenta Python 3 ----
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo Iniciando servidor com Python...
    echo.
    python "%~dp0servir_dados.py" --dir "%DATA_DIR%" --port %PORTA%
    echo.
    pause
    exit /b %errorlevel%
)

REM ---- Tenta py (Windows Python launcher) ----
where py >nul 2>nul
if %errorlevel% equ 0 (
    echo Iniciando servidor com Python (py launcher)...
    echo.
    py "%~dp0servir_dados.py" --dir "%DATA_DIR%" --port %PORTA%
    echo.
    pause
    exit /b %errorlevel%
)

REM ---- Fallback: Node.js ----
where node >nul 2>nul
if %errorlevel% equ 0 (
    echo Iniciando servidor com Node.js...
    echo.
    node "%~dp0servir_dados.js" --dir "%DATA_DIR%" --port %PORTA%
    echo.
    pause
    exit /b %errorlevel%
)

REM ---- Nenhum dos dois disponivel ----
echo.
echo ============================================================
echo  ERRO: nem Python nem Node.js encontrados no PATH.
echo ============================================================
echo.
echo  Instale UM dos dois (qualquer um basta):
echo    Python 3:  https://www.python.org/downloads/
echo    Node.js:   https://nodejs.org/
echo.
echo  Apos instalar, reabra este .bat.
echo.
pause
endlocal
