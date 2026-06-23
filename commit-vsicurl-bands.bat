@echo off
REM v2.16.0 GISELE - sessao 10/06/2026 (range-read /vsicurl + bandas filled-contour)
REM Cobre o delta desde a v2.14.0 (inclui v2.15.0 predictor=3/cache, ainda nao commitado).

setlocal
cd /d "%~dp0"

echo.
echo === [1/5] Removendo locks e backups de patch ===
for %%F in (.git\index.lock .git\refs\heads\main.lock .git\index_new.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)
for %%F in (electron-app\python-helper\server.py.bak electron-app\python-helper\server.py.bak_ps electron-app\python-helper\server.py.bak_ls electron-app\python-helper\_patch_poc.py) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/5] Conferindo lockstep do HTML (md5 raiz x electron-app) ===
certutil -hashfile figuras_SisMOM_v23.html MD5 | findstr /R "^[0-9a-f]"
certutil -hashfile electron-app\figuras_SisMOM_v23.html MD5 | findstr /R "^[0-9a-f]"
echo (os dois md5 acima DEVEM ser IGUAIS entre si - raiz x electron-app)

echo.
echo === [3/5] Status pre-commit ===
git update-index --refresh > nul 2>&1
git status --short

echo.
echo === [4/5] Adicionando todas as mudancas ===
git add -A
if errorlevel 1 (echo ERRO ao executar git add. & pause & exit /b 1)

echo.
echo === [5/6] Commit v2.16.0 ===
REM Mensagem vem de arquivo (commit-msg.txt) para evitar problemas de aspas/escape no batch.
git commit -F "%~dp0commit-msg.txt"

if errorlevel 1 (echo. & echo ERRO no commit. & pause & exit /b 1)

echo.
echo === [6/6] Criando a tag anotada v2.16.0 (no commit recem-criado) ===
git tag -d v2.16.0 >nul 2>&1
git tag -a v2.16.0 -m "GISELE v2.16.0 - range-read/vsicurl, bandas filled-contour, divisao politica, recorte por poligono+box, animacao estavel"
if errorlevel 1 (echo. & echo ERRO ao criar a tag. & pause & exit /b 1)
echo Tag v2.16.0 criada em:
git rev-parse --short v2.16.0

echo.
echo === Log dos ultimos 5 commits ===
git log --oneline -5

echo.
echo === Tags ===
git tag -l

echo.
echo Commit + tag v2.16.0 concluidos.
echo Para enviar (commit e tag): git push origin main --follow-tags
echo (ou:                        git push origin main ^&^& git push origin v2.16.0)
pause
