# Snapshot: 20260528-0400-untruncate-pre-localdir

**Estado capturado:** logo após o fix do tail truncado, antes do patch de pasta local (FSA API).

**Build marker:** `20260528-0400-untruncate`

**Funcionalidades nesta versão:**
- Todo o trabalho desta sessão (modo GeoTIFF completo, sidebar, mapa por slot, cache, paletas, calculadora, etc.)
- Botão "Clonar modelo" na configuração
- Default ao abrir: PNG/GIF + Eta
- Bicópia raiz / electron-app idênticas (443.551 bytes, md5 `81f83b6...`)

**Arquivos preservados:**
- `figuras_SisMOM_v23.html` — raiz
- `electron-app__figuras_SisMOM_v23.html` — eletronapp cópia
- `electron-app__package.json` — v2.0.0 com files PWA
- `electron-app__main.js` — Electron entry com webSecurity:false

**Para restaurar:**
- Windows: `RESTAURAR.bat`
- Linux/Mac: `chmod +x RESTAURAR.sh && ./RESTAURAR.sh`

Ambos os scripts copiam os 4 arquivos de volta para suas posições originais. Os outros artefatos do projeto (dev/, docs/, etc.) NÃO são afetados — só o HTML duplo e a config do Electron.
