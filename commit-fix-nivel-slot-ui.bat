@echo off
REM fix(gt): dropdown de nivel aparece no map-box (controlado pela variavel 3D)

setlocal
cd /d "%~dp0"

echo.
echo === [1/3] Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/3] Stage ===
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

echo.
echo === [3/3] Commit ===
git commit ^
 -m "fix(gt): dropdown nivel 3D no map-box (slot header visivel)" ^
 -m "" ^
 -m "ROOT CAUSE:" ^
 -m "  O selector de nivel estava em #gtToolbar, dentro de #mainGT que e SEMPRE" ^
 -m "  display:none. O modo GeoTIFF funciona via CSS body.gt-mode-active sobre os" ^
 -m "  paineis map-box normais — o #mainGT nao e mostrado em nenhum cenario." ^
 -m "  Por isso o dropdown de nivel nunca aparecia ao utilizador." ^
 -m "" ^
 -m "FIX — selector de nivel movido para map-config do mapBoxTpl:" ^
 -m "  - Adicionado <select data-cfg='nivel'> em mapBoxTpl apos data-cfg='variavel'" ^
 -m "  - Novo helper _syncSlotNivelUI(slotIdx):" ^
 -m "      * Se variavel.is3d=false: oculta o select (display:none)" ^
 -m "      * Se variavel.is3d=true: popula com niveis do modelo, mostra inline" ^
 -m "      * Sincroniza com getGtSlotState(slotIdx).nivelAtual" ^
 -m "      * Se nivelAtual=null: usa primeiro nivel e persiste" ^
 -m "  - onSlotConfigChange:" ^
 -m "      * cfg='modelo': chama _syncSlotNivelUI apos atualizar variavel" ^
 -m "      * cfg='variavel': chama _syncSlotNivelUI apos atualizar variavel" ^
 -m "      * cfg='nivel' (novo): atualiza gtSlotState.nivelAtual e renderTudo" ^
 -m "  - atualizarSlotsControles: chama _syncSlotNivelUI por slot" ^
 -m "  - saveConfig: chama _syncSlotNivelUI para todos os slots apos salvar" ^
 -m "" ^
 -m "COMPORTAMENTO CORRIGIDO:" ^
 -m "  - Abre modelo com variavel 3D (ex: Geopotencial, is3d=true) ->" ^
 -m "    select de nivel aparece no header do painel, entre variavel e tools" ^
 -m "  - Troca para variavel 2D -> select some (display:none)" ^
 -m "  - Seleciona nivel -> URL usa nivel correto imediatamente" ^
 -m "  - Salva config com is3d marcado -> select aparece sem recarregar" ^
 -m "  - Funciona em PNG mode e GeoTIFF mode (ambos usam map-box)" ^
 -m "" ^
 -m "* Build marker: fix-save-config-sync -> fix-nivel-slot-ui"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
