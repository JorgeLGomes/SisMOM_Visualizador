@echo off
setlocal
title SisMOM - Visualizador
set "HTML=%~dp0figuras_SisMOM_v23.html"
if not exist "%HTML%" (
  echo.
  echo  [ERRO] Nao encontrei "figuras_SisMOM_v23.html" nesta pasta.
  echo  Mantenha este .bat na MESMA pasta do arquivo HTML.
  echo.
  pause
  exit /b 1
)
set "URL=file:///%HTML:\=/%"

rem --- Procura Microsoft Edge ---
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
rem --- Procura Google Chrome ---
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"

if exist "%EDGE%" (
  start "" "%EDGE%" --app="%URL%" --window-size=1440,900
) else if exist "%CHROME%" (
  start "" "%CHROME%" --app="%URL%" --window-size=1440,900
) else (
  rem Sem Edge/Chrome: abre no navegador padrao
  start "" "%URL%"
)
endlocal
