@echo off
REM ============================================================================
REM  regenerar_pdfs.bat  -  Regenera todos os PDFs da documentacao GISELE
REM  Requer: Python 3.x + reportlab (pip install reportlab)
REM  Gera:
REM    docs\GISELE_Manual_Uso.pdf      (dev\gerar_manual_uso.py)
REM    docs\HANDOVER_GISELE.pdf        (dev\gerar_pdf_md.py)
REM    docs\ESPECIFICACOES_GISELE.pdf  (dev\gerar_pdf_md.py)
REM    docs\ADEQUACAO_COPERNICUS.pdf   (dev\gerar_pdf_md.py)
REM    docs\BACKEND_PROPOSTA.pdf       (dev\gerar_pdf_md.py)
REM ============================================================================
setlocal
cd /d "%~dp0"

echo.
echo === [1/4] Verificando dependencias ===
python -c "import reportlab" 2>nul
if errorlevel 1 (
    echo Instalando reportlab...
    pip install reportlab
)
echo OK.

echo.
echo === [2/4] Gerando Manual de Uso (reportlab) ===
python dev\gerar_manual_uso.py
if errorlevel 1 (echo ERRO no manual. & pause & exit /b 1)

echo.
echo === [3/4] Gerando PDFs dos documentos Markdown ===
python dev\gerar_pdf_md.py ^
  HANDOVER_GISELE.md        docs\HANDOVER_GISELE.pdf ^
  ESPECIFICACOES_GISELE.md  docs\ESPECIFICACOES_GISELE.pdf ^
  ADEQUACAO_COPERNICUS.md   docs\ADEQUACAO_COPERNICUS.pdf ^
  BACKEND_PROPOSTA.md       docs\BACKEND_PROPOSTA.pdf
if errorlevel 1 (echo ERRO nos PDFs MD. & pause & exit /b 1)

echo.
echo === [4/4] Limpando scripts temporarios de restauracao ===
del /F /Q dev\restore_ADEQUACAO_COPERNICUS.py dev\restore_BACKEND_PROPOSTA.py 2>nul
echo OK.

echo.
echo === Todos os PDFs gerados ===
dir docs\*.pdf
pause
