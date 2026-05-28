@echo off
REM Restaura o estado do projeto para o snapshot 20260528-0400-untruncate-pre-localdir
REM (versao apos o fix do tail truncado, antes do patch de pasta local).
setlocal
cd /d "%~dp0..\..\..\"
echo Restaurando figuras_SisMOM_v23.html (raiz)...
copy /Y "dev\snapshots\20260528-0400-untruncate-pre-localdir\figuras_SisMOM_v23.html" "figuras_SisMOM_v23.html" >nul
echo Restaurando electron-app\figuras_SisMOM_v23.html...
copy /Y "dev\snapshots\20260528-0400-untruncate-pre-localdir\electron-app__figuras_SisMOM_v23.html" "electron-app\figuras_SisMOM_v23.html" >nul
echo Restaurando electron-app\package.json...
copy /Y "dev\snapshots\20260528-0400-untruncate-pre-localdir\electron-app__package.json" "electron-app\package.json" >nul
echo Restaurando electron-app\main.js...
copy /Y "dev\snapshots\20260528-0400-untruncate-pre-localdir\electron-app__main.js" "electron-app\main.js" >nul
echo.
echo OK - estado restaurado para build 20260528-0400-untruncate.
pause
endlocal
