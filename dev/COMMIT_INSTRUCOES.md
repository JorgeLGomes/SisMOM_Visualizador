# Instruções de commit — v2.0.0 GISELE (sessão 2026-05-28)

**Repo:** `https://github.com/JorgeLGomes/SisMOM_Visualizador.git`
**Branch:** `main`
**Versão alvo:** `2.0.0` build `20260528-0500-gisele`

---

## ✅ Caminho rápido (1 commit único)

Cole as 4 linhas abaixo no PowerShell:

```powershell
cd C:\Projetos\Visualizador
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock }
git add -A
git commit -m "v2.0.0 GISELE: rebrand, GeoTIFF cache, servidor HTTP local, manual PDF 18p, build Win/Mac/Linux"
git push origin main
```

E a tag de release:

```powershell
git tag -a v2.0.0 -m "GISELE 2.0.0 - Gestao Integrada de Solucoes Estrategicas e Inteligencia"
git push origin v2.0.0
```

Pronto. Pule pro passo 5 (gerar distribuição).

---

## 📦 Caminho organizado (6 commits temáticos)

Histórico mais legível e fácil de reverter ponto a ponto.

### Commit 1 — Performance GeoTIFF + animação

```powershell
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html `
        dev/patch_cache_e_loading.py `
        dev/patch_perf_optimize.py `
        dev/patch_anim_monotonic_gate.py `
        dev/patch_revert_render_cache.py `
        dev/patch_skip_gtloadstate.py `
        dev/patch_versao_marker.py `
        dev/patch_perf_v2.py `
        dev/patch_use_imgdata_cache.py `
        dev/patch_simplify_no_gate.py `
        dev/patch_bloburl_cache.py
git commit -m "Performance GeoTIFF: cache decoded/imageData/blobUrl, dedup in-flight, build marker, monotonic gate"
```

### Commit 2 — UX bugfixes

```powershell
git add dev/patch_mode_switch_cleanup.py `
        dev/patch_filter_modelos_by_mode.py `
        dev/patch_default_png_eta.py `
        dev/patch_enable_mostrar_mapa.py `
        dev/patch_repopulate_selects_on_mode.py `
        dev/patch_calc_selects_refresh.py `
        dev/patch_load_with_map.py
git commit -m "UX: troca de aba limpa, filtros PNG/TIF por aba, default PNG/Eta, Mostrar mapa pos-decode, primary na calculadora"
```

### Commit 3 — Clonar modelo + sidebar fixes + tail truncado + snapshots

```powershell
git add dev/patch_clone_modelo.py `
        dev/patch_sidebar_left_fix.py `
        dev/patch_sidebar_hide_preview.py `
        dev/patch_panel_pin_pos.py `
        dev/patch_local_path.py `
        dev/patch_revert_local_path.py `
        dev/snapshots/
git commit -m "Config: Clonar modelo; sidebar GeoTIFF fixes; tail untruncate; snapshots de versao"
```

### Commit 4 — Rebrand GISELE

```powershell
git add dev/patch_rebrand_gisele.py
git commit -m "Rebrand: SisMOM Visualizador -> GISELE (Gestao Integrada de Solucoes Estrategicas e Inteligencia)"
```

### Commit 5 — Distribuição (Windows + macOS + Linux + servidor HTTP local)

```powershell
git add electron-app/package.json `
        electron-app/main.js `
        electron-app/build.bat `
        electron-app/build.sh `
        electron-app/build-mac.sh `
        electron-app/LEIA-ME-build.txt `
        electron-app/manifest.webmanifest `
        electron-app/sismom-icon-192.png `
        electron-app/sismom-icon-512.png `
        manifest.webmanifest `
        tools/
git commit -m "Distribuicao v2.0.0 GISELE: Win NSIS+portable, macOS dmg (arm64+x64)+zip, Linux AppImage+deb, standalone, servidor HTTP local"
```

### Commit 6 — Documentação

```powershell
git add docs/GISELE_Manual_Uso.pdf `
        docs/RELEASE_NOTES.md `
        dev/gerar_manual_uso.py `
        dev/COMMIT_INSTRUCOES.md
git commit -m "Docs: Manual de Uso GISELE PDF (18 paginas, com macOS) + RELEASE_NOTES + commit instructions"
```

### Push final

```powershell
git push origin main
git tag -a v2.0.0 -m "GISELE 2.0.0 - Gestao Integrada de Solucoes Estrategicas e Inteligencia"
git push origin v2.0.0
```

---

## 🔧 Pré-requisitos (rodar uma vez se necessário)

### Remover `.git/index.lock` se existir

```powershell
cd C:\Projetos\Visualizador
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock }
```

### Remover pasta órfã `SisMOM_Visualizador/` aninhada (opcional)

```powershell
Remove-Item -Recurse -Force C:\Projetos\Visualizador\SisMOM_Visualizador -ErrorAction SilentlyContinue
```

---

## 5. Gerar a distribuição depois do commit

### Windows
```powershell
cd C:\Projetos\Visualizador\electron-app
.\build.bat
```
Saída em `dist\`:
- `GISELE Setup 2.0.0.exe` (instalador NSIS)
- `GISELE-2.0.0-portable.exe`
- `GISELE-2.0.0-standalone/` + `.zip`

### Linux
```bash
cd electron-app
chmod +x build.sh && ./build.sh
```
Saída em `dist/`:
- `GISELE-2.0.0.AppImage`
- `gisele_2.0.0_amd64.deb`
- `GISELE-2.0.0-standalone/` + `.zip`

### macOS
```bash
cd electron-app
chmod +x build-mac.sh && ./build-mac.sh
```
Saída em `dist/`:
- `GISELE-2.0.0-arm64.dmg` (Apple Silicon M1/M2/M3/M4)
- `GISELE-2.0.0-x64.dmg` (Intel Mac)
- `GISELE-2.0.0-mac-arm64.zip` / `GISELE-2.0.0-mac-x64.zip`
- `GISELE-2.0.0-standalone/` + `.zip`

---

## 6. Publicar Release no GitHub

Após `git push origin v2.0.0`:

1. Abra https://github.com/JorgeLGomes/SisMOM_Visualizador/releases
2. **Draft a new release**
3. **Choose a tag**: `v2.0.0`
4. **Release title**: `GISELE 2.0.0`
5. **Description**: cole o conteúdo de `docs/RELEASE_NOTES.md`
6. **Attach binaries** (arraste os artefatos do `electron-app/dist/`):
   - `GISELE Setup 2.0.0.exe`
   - `GISELE-2.0.0-portable.exe`
   - `GISELE-2.0.0-arm64.dmg` + `GISELE-2.0.0-x64.dmg` (se tiver Mac)
   - `GISELE-2.0.0.AppImage` + `.deb` (se tiver Linux)
   - `GISELE-2.0.0-standalone.zip`
   - `GISELE_Manual_Uso.pdf` (manual)
7. **Publish release**.

---

## 🆘 Salvaguarda

Se algo der errado e precisar voltar:

```powershell
# Snapshot pré-rebrand (build 0400-untruncate)
cd C:\Projetos\Visualizador\dev\snapshots\20260528-0410-pre-rebrand
.\RESTAURAR.bat   # ou ./RESTAURAR.sh no Linux/Mac

# Snapshot antes da rota local (build 0400-untruncate, igual ao anterior nesse caso)
cd C:\Projetos\Visualizador\dev\snapshots\20260528-0400-untruncate-pre-localdir
.\RESTAURAR.bat
```

Cada um restaura os 4 arquivos principais (HTML duplo + `package.json` + `main.js`) ao estado conhecido bom.

---

## 📋 Resumo da sessão

### Novidades v2.0.0 GISELE
- **Rebrand**: SisMOM Visualizador → GISELE (filename e localStorage preservados para compatibilidade)
- **Modo GeoTIFF completo**: decodificador inline, 15 paletas, mapa-base com tiles, multi-painel, sidebar
- **Cache de animação**: 3 níveis (decoded / imageData / blob URL) — 2ª volta instantânea
- **Configuração**: Clonar modelo, filtros por aba (PNG/TIF), rotas distintas
- **Distribuição multi-OS**: Windows (.exe), macOS (.dmg arm64/x64), Linux (AppImage/.deb), standalone HTML
- **Servidor HTTP local** (`tools/servir_dados/`): Python+Node, multi-thread, CORS, MIME TIF
- **Manual PDF 18 páginas** com instruções para Windows/macOS/Linux

### Arquivos não versionar (já em `.gitignore`)
- `electron-app/dist/`, `node_modules/`, `*.zip`, `*.log`
