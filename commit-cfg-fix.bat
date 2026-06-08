@echo off
REM fix(config): CSS col-inicio + passo_inicio em addVarRow e syncCurrentPaneToDraft

setlocal
cd /d "%~dp0"

echo.
echo === Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === Stage + Commit ===
git read-tree HEAD
if errorlevel 1 (echo ERRO read-tree. & pause & exit /b 1)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

git commit ^
 -m "fix(config): CSS col-inicio ausente + passo_inicio em addVarRow/syncDraft" ^
 -m "" ^
 -m "PROBLEMAS:" ^
 -m "  1) .col-inicio nao tinha CSS -> tabela de variaveis overflow horizontal" ^
 -m "     causando layout quebrado no modal (abas de modelo apareciam 'sumidas')" ^
 -m "  2) addVarRow nao incluia passo_inicio no objeto default -> nova variavel" ^
 -m "     nao tinha o campo, gerando undefined na leitura" ^
 -m "  3) syncCurrentPaneToDraft nao fazia coercao de tipo para passo_inicio" ^
 -m "     -> valor ficava como string '0' em vez de number 0" ^
 -m "" ^
 -m "CORRECOES:" ^
 -m "  1) .col-inicio { width: 64px; } adicionado ao lado de .col-freq" ^
 -m "  2) addVarRow default: passo_inicio: 0 adicionado" ^
 -m "  3) syncCurrentPaneToDraft: coerce passo_inicio com Math.max(0, Number(val))" ^
 -m "" ^
 -m "* Build marker: 20260605-2400-ts-passo0 -> 20260605-2500-cfg-fix"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -5
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: OK || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou) else (echo Push OK.)
pause
