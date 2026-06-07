@echo off
REM feat(gt): campo vetorial de vento (setas/streamlines) + coluna formula na config

setlocal
cd /d "%~dp0"

echo.
echo === [1/3] Limpando locks ===
for %%F in (.git\index.lock .git\refs\heads\main.lock) do (
    if exist "%%F" del /F /Q "%%F" 2>nul
)

echo.
echo === [2/3] Reconstruindo index + stage ===
git read-tree HEAD
if errorlevel 1 (echo ERRO read-tree. & pause & exit /b 1)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html

echo.
echo === [3/3] Commit ===
git commit ^
 -m "feat(gt): campo vetorial de vento (setas/streamlines) + coluna formula" ^
 -m "" ^
 -m "FEATURE 1 — Coluna Formula na tabela de variaveis:" ^
 -m "  Nova coluna 'Formula' (input de texto) na tabela de vars da config." ^
 -m "  Permite definir expressoes como sqrt({U}^2+{V}^2) onde {ID} referencia" ^
 -m "  outra variavel do mesmo modelo. Implementado em _gtEvalFormula()." ^
 -m "  Colunas U-vent e V-vent: IDs das variaveis componentes zonal/meridional." ^
 -m "" ^
 -m "FEATURE 2 — Campo vetorial de vento (setas e streamlines):" ^
 -m "  Novo seletor 'Vento' na toolbar GT (aparece apenas quando a variavel" ^
 -m "  selecionada tem vec_u e vec_v configurados). Opcoes:" ^
 -m "    - Desligado: sem renderizacao vetorial" ^
 -m "    - Setas: grade de setas proporcionais a magnitude do vento" ^
 -m "    - Streamlines: linhas de corrente com seta de direcao no meio" ^
 -m "" ^
 -m "Implementacao:" ^
 -m "  - SisMOM_Map.setVectorField(uDec, vDec, mode, opts): armazena campo" ^
 -m "  - SisMOM_Map.clearVectorField(): limpa campo vetorial" ^
 -m "  - drawVectorField(): renderizador interno (bilinear + setas/streamlines)" ^
 -m "  - carregarGeoTIFFParaSlot: apos primary TIF, busca U/V e chama setVectorField" ^
 -m "  - getGtSlotState: adicionado vecMode:'off' ao estado por slot" ^
 -m "  - gtBindToolbar: listener do select gtVecModeSel" ^
 -m "  - gtSyncToolbarFromState: show/hide do seletor de vento" ^
 -m "" ^
 -m "* Build marker: 20260607-0300-cfg-polish -> 20260607-0400-wind-vector"

if errorlevel 1 (echo ERRO commit. & pause & exit /b 1)

echo.
git log --oneline -4
echo.
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo Lockstep: IDENTICOS || echo ATENCAO: divergem!
echo.
git push origin main
if errorlevel 1 (echo AVISO: push falhou - rode: git push origin main) else (echo Push OK.)
pause
