@echo off
REM feat(config): template TIF unificado com preview de split automatico

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
 -m "feat(config): template TIF unificado com preview de split" ^
 -m "" ^
 -m "ANTES: dois campos separados para TIF (Template do endereco + Template" ^
 -m "Nome Arq.), cada um com seu proprio checkbox 'usar o mesmo do PNG'." ^
 -m "" ^
 -m "AGORA: um unico campo 'Template TIF (diretorio/arquivo)' onde o usuario" ^
 -m "digita a URL completa do TIF numa so linha, e o sistema detecta" ^
 -m "automaticamente onde o diretorio termina e o arquivo comeca." ^
 -m "" ^
 -m "Comportamento:" ^
 -m "  - Checkbox 'usar o mesmo do PNG' esconde o campo (usa url_path +file_name)" ^
 -m "  - Ao digitar, um preview em tempo real mostra:" ^
 -m "      dir: https://.../geotiff/   (azul)" ^
 -m "      arquivo: {prefixo}-{F%3}.tif   (verde)" ^
 -m "  - A deteccao do ponto de corte usa o ultimo '/' antes de um placeholder" ^
 -m "    de arquivo ({prefixo}, {f%%N}, {F%%N}, {N%%N}, {passo4?}, {ext})" ^
 -m "  - Ao salvar, o campo e auto-dividido em url_path_tif + file_name_tif" ^
 -m "    (modelo de dados interno nao muda — compatibilidade total)" ^
 -m "" ^
 -m "Novos elementos:" ^
 -m "  - CSS: .tif-split-preview (.tsp-dir, .tsp-sep, .tsp-file)" ^
 -m "  - HTML: cfgTifTemplate (input) + cfgSameTif (checkbox) + cfgTifSplitPreview" ^
 -m "  - JS: _tifTemplateSplit(combined) -> { path, name }" ^
 -m "  - Preset FTP CPTEC atualizado para preencher o campo unificado" ^
 -m "" ^
 -m "* Build marker: 20260607-0700-bases-fix -> 20260607-0800-tif-template"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
