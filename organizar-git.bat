@echo off
REM ============================================================================
REM  organizar-git.bat  -  Finaliza os commits pendentes da GISELE (idempotente)
REM   [1] Limpa locks/sobras em .git   [2] Reverte CRLF (SisMOM.bat, leaflet.css)
REM   [3] Limpa rascunhos do brand\    [4] Apaga temporarios de teste
REM   [5] Remove leftover do HANDOVER (o PDF novo ja foi commitado)
REM   [6] Commits: brand + chore + docs(COMO-USAR) + fix(monitoramento)
REM       (brand/chore/docs ja podem estar commitados; o git pula o que nao mudou)
REM   [7] Status, log e lockstep.  Commits LOCAIS; envie com: git push
REM ============================================================================
setlocal
cd /d "%~dp0"

echo.
echo === [1/7] Limpando locks/sobras em .git ===
del /F /Q ".git\index.lock*"          2>nul
del /F /Q ".git\zzjunk_*"             2>nul
del /F /Q ".git\refs\heads\main.lock*" 2>nul
del /F /Q ".git\HEAD.lock"            2>nul
echo OK.

echo.
echo === [2/7] Revertendo CRLF (so SisMOM.bat e leaflet.css; COMO-USAR tem rebrand) ===
git checkout -- SisMOM.bat vendor/leaflet.css 2>nul
echo OK.

echo.
echo === [3/7] Limpando rascunhos do logo em brand\ (mantem entregaveis) ===
pushd brand
del /F /Q _check_final.png _tmp_mark_v1.png _tmp_mark_v1.svg badge.png cmask512.png core_grad.png dropA.png dropB.png dropC.png dropgrad.png dropgradF.png dropgrad_flat.png dropgrad_r.png droplet.png "gisele-icon-512-0.png" "gisele-icon-512-1.png" gisele_icon_preview.png grad_bg.png hi.png mask_badge.png mask_drop.png red512.png singlegrad.png tC.png tD.png tE.png testA.png testB.png waves.png waves_raw.png 2>nul
popd
echo OK.

echo.
echo === [4/7] Apagando temporarios de teste (_fscap_*, _ov_*) ===
del /F /Q _fscap_*.tmp _fscap_*.txt _ov_*.tmp 2>nul
echo OK.

echo.
echo === [5/7] Removendo leftover docs\HANDOVER_GISELE.NOVO.pdf (PDF ja commitado) ===
del /F /Q "docs\HANDOVER_GISELE.NOVO.pdf" 2>nul
echo OK.

echo.
echo === [6/7] Commits tematicos (o git pula automaticamente o que ja foi commitado) ===
echo  -- Commit 1: identidade visual (brand)
git add brand/gisele_logo.svg brand/gisele_logomark.svg brand/gisele_logomark_mono.svg brand/gisele-icon-192.png brand/gisele-icon-512.png
git commit -m "feat(brand): identidade visual GISELE - logo, logomark e icones" -m "Assets finais da nova marca GISELE (01/06): gisele_logo.svg (1320x360), gisele_logomark.svg + _mono (simbolo), gisele-icon-192/512.png (icones)."
echo  -- Commit 2: chore (.gitignore + helper de release)
git add .gitignore commit-v2.12.1.bat
git commit -m "chore: ignora artefatos (brand rascunhos, api-client CSV) + helper release v2.12.1"
echo  -- Commit 3: COMO-USAR.txt (rebrand que faltou no commit docs)
git add COMO-USAR.txt
git commit -m "docs: rebrand COMO-USAR.txt para GISELE (faltou no commit docs anterior)"
echo  -- Commit 4: fix Monitoramento (proxy CORS no navegador)
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html
git commit -m "fix(monitoramento): acessa Queimadas via fallback de proxy CORS no navegador" -m "gtMonitFetch tenta o fetch direto (nativo no Electron) e, se falhar por CORS (navegador/file://, pois o INPE nao envia Access-Control-Allow-Origin), recorre a proxies CORS (corsproxy.io -> allorigins -> thingproxy) com timeout de 12s/tentativa; erro claro se todos falharem. Toast indica '(via proxy CORS)'. Marker -> 20260602-1300-monitproxy. Aplicado nos DOIS HTML (lockstep)."

echo.
echo === [7/7] Estado final ===
echo --- git status (curto) ---
git status --short
echo.
echo --- ultimos commits ---
git log --oneline -8
echo.
echo --- lockstep dos HTML (raiz x electron-app) ---
fc /b figuras_SisMOM_v23.html electron-app\figuras_SisMOM_v23.html >nul 2>&1 && echo IDENTICOS (lockstep OK) || echo ATENCAO: HTMLs diferem!
echo.
echo  Pronto. Para enviar ao remoto:  git push
echo  Depois pode apagar:  organizar-git.bat  e  brand\_limpar_temporarios.bat
pause
