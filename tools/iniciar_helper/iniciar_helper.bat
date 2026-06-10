@echo off
REM ============================================================
REM  GISELE - Helper Python (micro-servico local)
REM
REM  Sobe o gisele-python-helper em http://127.0.0.1:8765
REM  (aceleracao de series temporais + ferramenta "Baixar dados").
REM
REM  Necessario apenas quando o GISELE roda NO NAVEGADOR.
REM  No app GISELE (Electron) o helper sobe automaticamente.
REM
REM  Uso:
REM    1) Duplo-clique. Na primeira vez cria um ambiente Python
REM       em .venv-helper e instala as dependencias (demora alguns
REM       minutos; precisa de internet). Depois e' instantaneo.
REM    2) Linha de comando:  iniciar_helper.bat [porta]
REM
REM  Requer: Python 3.10+ no PATH (python ou py).
REM ============================================================

setlocal enableextensions
title GISELE - Helper Python (micro-servico local)

set "PORTA=%~1"
if "%PORTA%"=="" set "PORTA=8765"

REM ---- Localiza a pasta do helper (relativa a este .bat) ----
set "HELPER_DIR=%~dp0..\..\electron-app\python-helper"
if exist "%HELPER_DIR%\server.py" goto :acha_python
echo ERRO: nao encontrei "%HELPER_DIR%\server.py".
echo Este .bat deve ficar em tools\iniciar_helper\ dentro do projeto.
pause
exit /b 1

:acha_python
set "PY="
where python >nul 2>nul
if %errorlevel% equ 0 set "PY=python"
if defined PY goto :tem_python
where py >nul 2>nul
if %errorlevel% equ 0 set "PY=py"
if defined PY goto :tem_python
echo.
echo ============================================================
echo  ERRO: Python 3 nao encontrado no PATH.
echo  Instale em https://www.python.org/downloads/
echo  e marque "Add python.exe to PATH" no instalador.
echo ============================================================
pause
exit /b 1

:tem_python
cd /d "%HELPER_DIR%"

REM ---- Ambiente virtual dedicado (primeira vez instala tudo) ----
if exist ".venv-helper\Scripts\python.exe" goto :roda

echo Primeira execucao: criando ambiente Python em .venv-helper ...
%PY% -m venv .venv-helper
if errorlevel 1 goto :erro_venv

echo Instalando dependencias - pode demorar alguns minutos...
".venv-helper\Scripts\python.exe" -m pip install --upgrade pip
".venv-helper\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :erro_pip

:roda
echo.
echo ============================================================
echo  GISELE - Helper Python                em 127.0.0.1:%PORTA%
echo  Deixe esta janela ABERTA enquanto usa o GISELE no navegador.
echo  Ctrl+C para parar.
echo ============================================================
echo.
".venv-helper\Scripts\python.exe" server.py --port %PORTA%
echo.
echo O helper terminou. Veja as mensagens acima em caso de erro.
pause
exit /b 0

:erro_venv
echo ERRO ao criar o ambiente .venv-helper. Verifique a instalacao do Python.
pause
exit /b 1

:erro_pip
echo ERRO ao instalar dependencias. Verifique a internet e rode de novo.
pause
exit /b 1
