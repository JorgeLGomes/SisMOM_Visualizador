@echo off
REM docs: atualizar HANDOVER com sessao 07/06/2026

setlocal
cd /d "%~dp0"

echo.
echo === [1/3] Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/3] Stage ===
git add HANDOVER_GISELE.md
git add commit-wind-vector.bat commit-resize.bat commit-scroll-fix.bat commit-bases-fix.bat commit-docs-update.bat 2>nul

echo.
echo === [3/3] Commit ===
git commit ^
 -m "docs: HANDOVER atualizado sessao 07/06/2026" ^
 -m "" ^
 -m "Documenta features desta sessao ja commitadas em 97d2275:" ^
 -m "  - Campo vetorial de vento (setas/streamlines)" ^
 -m "  - Coluna Formula + vec_u/vec_v na config de variaveis" ^
 -m "  - Resize colunas da tabela de variaveis (drag handle, localStorage)" ^
 -m "  - Resize do modal de configuracoes (handle SE, localStorage)" ^
 -m "  - Scroll fino nas abas de modelos (scrollbar-width:thin)" ^
 -m "  - Resize handle ancorado ao .modal (position:relative)" ^
 -m "  - Fonte 15px / padding 11px 16px nas abas de modelos" ^
 -m "  - Fix showBasesPane: revertido para show/hide simples" ^
 -m "    (Base de dados sumia ao abrir a aba)" ^
 -m "" ^
 -m "Tambem inclui os BAT files de commit desta sessao."

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
