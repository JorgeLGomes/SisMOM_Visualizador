# GISELE — Documento de Handover

**Repositório:** `C:\Projetos\Visualizador`
**Versão atual:** v2.2.0 — Build marker `20260529-1900-videofitfps`
**Arquivos críticos (sempre em lockstep):**
- `figuras_SisMOM_v23.html` (raiz)
- `electron-app/figuras_SisMOM_v23.html` (cópia idêntica para o build Electron)
- `miscelaneas/manifest.json` + `miscelaneas/*.geojson` (raiz + electron-app)

> **Importante:** todo patch no HTML deve ser aplicado nos DOIS arquivos. Validar com `node --check` e `md5sum` antes de seguir. O Edit tool tem tendência a truncar o tail; SEMPRE checar `</html>` final e reconstruir a partir do `gt-misc-data-corais_br` se faltar.

---

## 1. Arquitetura geral

- **Single-page HTML** (~1 MB), JavaScript em IIFE no `<script>` final. Toda lógica num único namespace, sem framework.
- **Dois modos de operação** controlados por `appMode`:
  - `png` (PNG/GIF): imagens estáticas/animadas do FTP do CPTEC carregadas em `<img>`.
  - `gtiff` (GeoTIFF): TIF decodificado em ArrayBuffer + paleta + render num `<canvas class="map-canvas-gt">`.
- **Estado por aba** salvo em `localStorage` chaves `sismom_state_png` e `sismom_state_gtiff`. Restaurado em `_stateRestore` quando troca de tab.
- **Multi-painel** (1/2/3/4 slots = M1..M4) via grid CSS no `.map-container`. Layout muda em `setLayout`.
- **Decodificador GeoTIFF próprio** em `SisMOM_GeoTIFF.decodeTIFF(buffer)` (não usa lib externa — só UTIF para descompactação LZW se necessário).
- **Sistema de paletas** em `aplicarPaleta(decoded, opts)`: Viridis, Jet, RdBu, Grayscale, Turbo, + 10 paletas matplotlib/ColorBrewer.
- **Canvas custom `SisMOM_Map`** com projeção Mercator/PlateCarrée, tiles XYZ (Esri/OSM/OpenTopo), pan/zoom, anotações, overlays raster e GeoJSON.

---

## 2. Funcionalidades operacionais (por categoria)

### 2.1. Carregamento e renderização

| Feature | Prompts originais (resumo) | Ferramentas |
|---|---|---|
| Decodificação GeoTIFF nativa + paletas | "Implementar decodeGeoTIFF e paletas (Viridis, Jet, RdBu, Grayscale, Turbo)" | Read/Edit (figuras_SisMOM_v23.html), node --check |
| Botão "Abrir GeoTIFF local" | "Botão Abrir GeoTIFF local (arquivo avulso)" | Edit, Read |
| Multi-paletas extra (matplotlib/ColorBrewer) | "10 paletas extras" | Edit |
| Cache de blob URL + ImageData por (url+opts) | "Cache de blob URL: evitar putImageData+toBlob por step (Eta gigante)" | Edit, Read, console diagnostic |
| Heurística multi-sentinel NoData | "Múltiplos sentinels + min/max via percentil (Eta10 com 5.87e+9)" | Edit, Read |
| Render por scanline em Mercator (256 strips) | "Renderizar bitmap por scanline em Mercator" | Edit |
| Auto flip-Y quando tiepoint J indica linha de baixo | "Auto flipY quando tiepoint J indica linha de baixo" | Edit |
| Ler GTRasterTypeGeoKey p/ ajustar bbox (PixelIsPoint/Area) | "Fix Eta: ler GTRasterTypeGeoKey p/ ajustar bbox" | Edit, console diagnostic |
| Botão manual "Inverter Y" | "Botão 'Inverter Y' na sidebar" | Edit |

### 2.2. Mapa base (tiles)

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Projeção Web Mercator + tiles XYZ | "Adicionar projeção Web Mercator + Camada de tiles XYZ (3 providers + seletor)" | Edit |
| Mapa-base por painel Mi (toggle individual) | "Mapa-base + opacidade por Mi panel (toggle por slot)" | Edit |
| **Mapa-base padrão por modelo** (NOVO) | "setar nas configurações o mapa que irá entrar por padrão para cada modelo" + "Consta a opção do mapa na configuração, porém a mesma não entra por padrão quando eu faço o swap" | Edit (cfgMapProvider HTML/JS, gtSelectPanel, captureControlsToActive), bicópia + node --check |
| Atribuição (Esri, OSM) | "Atribuição de créditos (Esri, OSM)" | Edit |

### 2.3. Painel multi-Mi (slots M1..M4)

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Layout 1/2/3/4 painéis | (parte do design original) | Edit (CSS grid + setLayout) |
| Painel direito como sidebar + Mi ativo | "Painel direito como sidebar + seleção de painel Mi ativo" | Edit, Read |
| Listeners por slot (gtSlotState) | "Listeners do painel direito gravam em gtSlotState[gtActivePanel]" | Edit |
| Pino "Painel Mi" para selecionar slot ativo | "Reposicionar botão Painel Mi para não sobrepor ícones do header" | Edit |
| HUD horizontal por slot (zoom, lat/lon, valor) | "HUD horizontal com zoom + lat/lon + valor (canto inferior esq)" | Edit |
| Recalcular passos ao trocar modelo/variável | "Recalcular passos ao trocar modelo/variável na toolbar GeoTIFF" | Edit |

### 2.4. Camadas extras + calculadora

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Sobreposição GeoTIFF + GeoJSON local | "Sobreposição de camadas extras (GeoTIFF + GeoJSON)" | Edit (input file + addGeoJSON/addRasterOverlay) |
| Adicionar do FTP (modelo+variável+data+passo) | "Sobreposição: adicionar modelo/variável como camada extra" | Edit |
| Reordenar (↑/↓) | "Reordenação de camadas (↑/↓)" | Edit |
| Olho/× nos chips | "Camada ativa + controles por camada" | Edit |
| Calculadora raster (A+B, A−B, A×B, A÷B, escalar) | "Calculadora de camadas (raster algebra)" | Edit |

### 2.5. Contornos (isolinhas)

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Marching squares + UI por camada | "Contornos: marching squares + UI + por-camada" | Edit |
| **keepFill = true por padrão** (NOVO) | "MOM-Regional. Está plotando os contornos, mas o shaded não" | Edit (3 locais: HTML checkbox + lógica primary + lógica extras) |
| Contornos no topo + chip dedicado | "Contornos: stale após troca de modelo + sempre no topo + chip" | Edit |
| Respeitam mesma máscara do shaded | "Fix: contornos respeitam mesma máscara que o shaded" | Edit |
| Convenção de coordenada corner/center | "Fix: contornos deslocados — usar convenção de corner" + "Reverter pos() para convenção center (+0.5)" | Edit, diagnóstico console |

### 2.6. Ferramentas de medição/análise

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Distância (Haversine) | "Ferramentas: distância, área, texto, linha" | Edit |
| Área esférica | (idem) | Edit |
| Retângulo + Círculo | "Ferramentas: retângulo + círculo + perfil de linha" | Edit |
| Polilinha simples (draw-line) | (idem) | Edit |
| Anotação de texto | (idem) | Edit |
| Perfil ao longo de polilinha | (idem) — depois: "Melhorar o gráfico, fundo branco. Tem como o gráfico ser responsivo? Passar o mouse sobre o gráfico tráz a lat/lon do ponto" | Edit (gtOpenProfilePopup, _gtDrawProfileChart, ResizeObserver, tooltip) |
| Salvar PNG do perfil | "Opção de salvar o gráfico no formato png" | Edit (toDataURL + download) |
| Baixar CSV do perfil | (parte do design) | Edit |
| Perfil usa camada ATIVA (não top) | "Mapeando totalmente errado a região onde eu estou traçando" | Edit + console diagnostic |
| **Série temporal em ponto** (NOVO) | "dado um ponto marcado com o mouse na área do gráfico, gerar um gráfico, similar ao do caminho, para a evolução temporal da variável. eixo x tempo, eixo Y valor. usar a mesma função da rota, com as funções de salvamento do csv e gif" | Edit (gtSampleTimeSeries + gtOpenTimeSeriesPopup + _gtDrawTimeSeriesChart + _gtDownloadTimeSeriesCSV) |
| **Fix horizonte da série temporal** | "Para o modelo Eta a série temporal foi extraída corretamente. Ao mudar para o modelo Global. não extraíu somente um horário" | Edit (trocar `Math.min(v.horizonte, m.maxPassos)` por `v.horizonte || m.maxPassos`) |
| Wheel zoom funciona durante uso de ferramentas | "Permitir wheel zoom durante uso de ferramentas" + "Fix ferramentas indisponíveis após zoom" + "Fix: mousemove bloqueado mata preview de tools" + "Fix: wheel zoom assimétrico em latitude" + "Fix: wheel duplo (canvas + mapBody) em modo gtiff" — após o user uploadar vídeo: "Quando o zoom é feito com o +/- e navega com o mover/pan, mapeia corretamente, quando o zoom é feito com o scrool do mouse, ele perde a navegação" | Edit (e.stopPropagation no wheel handler do canvas, NÃO bloquear mousemove) |
| Toolbar persistente no top do .map-header | "Mover toolbar pra .map-header em vez de viewport" | Edit |

### 2.7. Miscelâneas (camadas vetoriais de referência)

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Diretório + manifest + plataformas offshore | "Incluir diretório para armazenar camadas de micelanias, em formatos diversos, tais como csv, gejson, shapefile. Exemplo as informações das plataformas de prospecção de petróleo. colocar uma opção de plotar a posição das mesmas, indicando a sigla, quando clicar sobre o ponto, abrir uma janela com as informações da plataforma" | Bash (mkdir miscelaneas/), Write (manifest.json), copy GeoJSON do upload |
| Embed inline para file:// | "Em modo GeoTIFF, no painel direito procure o bloco Miscelâneas. Deve aparecer Plataformas offshore (Brasil) no dropdown. Não apareceu" | Bash + Python (substituir `<script type="application/json" id="gt-misc-*">` inline), reescrita do `gtLoadMiscManifest` para ler primeiro do DOM |
| **Corais brasileiros (shapefile WCMC)** (NOVO) | "Arquivo zip com as informações, em shapefile, dos corais. Utilizar somente os que estão na costa brasileira. implementar a opção de visualização no micelanea" | Bash (unzip), Python pure (leitor `.shp/.dbf` sem GDAL/pyshp porque sandbox sem rede), filtro point-in-polygon real (bbox global da feature falhou por features atravessando antimeridiana), 11 polígonos válidos na costa BR |
| **Hachura diagonal nos polígonos** (NOVO) | "preencher o shape com um achurado na diagornal" | Edit (CanvasPattern com cache local em `_hatchCache`, fill translúcido por baixo + pattern por cima) |
| **Color picker no chip** (NOVO) | "possibilidade de mudar a cor do shape" | Edit (input type=color no chip → `gtSetMiscLayerColor` → recolore stroke/hachura/fill rgba preservando alpha) |
| **Click no shape → popup info** (NOVO) | "quando clicar com o mouse em cima, abrir uma janela com a informação do shape" | Edit (`_gtPointInRing` ray-casting + extensão de `gtFindMiscFeatureAtLatLon` para Polygon/MultiPolygon respeitando buracos) |

### 2.8. Animação + exportação de vídeo

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Play/Pause/Stop + grid de passos | (design original) | Edit |
| Setas ←/→ + Espaço | (idem) | Edit |
| Velocidade configurável (0.2/0.5/1/2s) | (idem) | Edit |
| Preservar zoom durante animação GeoTIFF | "Preservar zoom durante animação no modo GeoTIFF" | Edit |
| Prefetch de próximos passos em idle | "Prefetch animação: decodificar + paletizar próximos passos em idle" | Edit (requestIdleCallback) |
| Cache de blob URL por step | "Cache de blob URL: evitar putImageData+toBlob por step (Eta gigante)" | Edit |
| **Salvar vídeo MP4 da evolução** (NOVO) | "Opção de salvamento de um vídeo (mp4) da evolução temporal da área visualizada. Essa opção também deve estar disponível na área png. Quando selecionado o vídeo, fazer a evolução do primeiro ao último passo somente 1 vez" | Edit (botão na sidebar + `gravarVideoEvolucaoTemporal`, MediaRecorder + canvas.captureStream, codec MP4 → WebM fallback) |
| **Fix vídeo PNG canvas tainted** | "vídeo da área png continua não funcionando" | Edit (re-fetch via blob → ObjectURL → Image porque drawImage de img cross-origin tainta o canvas e captureStream emite frames pretos) |
| **Pré-busca todos os frames + drawStepFrame síncrono** | "Não salvou a área selecionada e dos 10 frames, salvou apenas 3" | Edit (Phase 1: paralelo fetch via Promise.all → frames[stepIdx][slotIdx]; Phase 2: loop sem fetch) |
| **Aspect ratio + force frame emission** | "capturou a região do zoom, mas não manteve a relação de aspecto e salvou apenas 3 quadros" | Edit (object-fit:contain math → calcula sub-rect dentro do box do `<img>`; `holdAndPaint` redesenha em RAF + pixel anti-dedup pra captureStream emitir frames a cada tick) |

### 2.9. Configuração de modelos

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| CRUD de modelos + variáveis | (design original) | Edit |
| Templates URL com placeholders ({yyyy}, {mm}, {dd}, {hh}, {N%4}, {F%3}, {prefixo}, …) | "Templates de URL e placeholders" | Edit (`montarURL` com placeholder system) |
| Suporte file:// no template | "Suportar caminho local (file://) no template de endereço" | Edit |
| tem_png / tem_tif + disp_png / disp_tif por variável | "Rotas distintas PNG/TIF + disponibilidade por modelo e variável" | Edit |
| Templates TIF próprios (url_path_tif / file_name_tif) | (idem) | Edit |
| Botão "Clonar modelo" | "Botão Clonar modelo na configuração" | Edit |
| Exportar/Importar JSON da configuração | (design original) | Edit |
| **mapProvider por modelo** (NOVO) | "setar nas configurações o mapa que irá entrar por padrão para cada modelo" | Edit (cfgMapProvider select + load/save em syncCurrentPaneToDraft + aplicar em gtSelectPanel) |
| Filtrar modelos sem TIF no seletor GeoTIFF | "Filtrar modelos sem TIF no seletor GeoTIFF" | Edit (`_modeloFitsMode`) |

### 2.10. Distribuição e empacotamento

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Build Electron Windows (NSIS + portable) | "Criar scripts de build automatizado" | Edit (electron-app/package.json), Bash |
| Build Mac (.dmg / .zip Intel + Apple Silicon) | "Adicionar build Mac (.dmg / .zip) ao package.json" | Edit (electron-builder config) |
| Build Linux (AppImage) | (parte do plano) | Edit |
| HTML standalone sempre incluído via postdist hook | "Standalone sempre incluído via postdist hook" | Edit (npm script) |
| Multi-monitor via --displays / --all-displays / --no-frame / F11 / Ctrl+Q | "Suporte a --displays no main.js (multi-monitor)" | Edit (main.js do Electron) |
| Atalho instalável (Windows .bat, Linux .desktop) | "Atalho instalável" | Write |
| CORS handler no Electron | "CORS no Electron + diagnóstico de erros de fetch" | Edit (main.js webRequest.onBeforeSendHeaders/onHeadersReceived) |
| Servidor HTTP local em Python + Node | "Servidor HTTP local: scripts Python/Node + launchers" | Write (tools/servir_dados/*.py / *.js / .sh / .bat) |

### 2.11. Estado por aba + persistência

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Estado separado PNG vs GeoTIFF em localStorage | "Estado independente por aba (PNG/GIF vs GeoTIFF)" | Edit |
| Default ao abrir: aba PNG/GIF + modelo Eta | "Default ao abrir: aba PNG/GIF + modelo Eta" | Edit |
| Repopular selects ao trocar aba | "Repopular selects de modelo ao trocar aba (sem snap salvo)" | Edit (`atualizarSlotsControles`) |
| **Fix swap PNG→GeoTIFF passo incompatível** (NOVO) | "Quando recarrega a plataforma, entra com o modelo Eta, e faz o swap para geotif, o modelo selecionado é o Global e o passo de tempo está do Eta, quebra o carregamento do campo" + "acho que tenho uma ideia do que está acontecendo, existe um cache que quando eu recarrego, o modelo selecionado para o geotif permanece a ultima seleção, mas o tempo é herdado da seleção png" | Edit (`atualizarMaxPassos` em setAppMode + forçar dentro de `_stateRestore` mesmo quando snap não tem passoAtual) |

### 2.12. Documentação

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| Manual PDF GISELE (15 seções, 24 páginas) | "PDF manual de uso da aplicação" + várias atualizações ("atualizar o manual", "atualizar manual e commit") | Python + reportlab (`dev/gerar_manual_uso.py`) |
| Rebrand SisMOM → GISELE | "Rebrand SisMOM Visualizador → GISELE" | Edit + Python script (`dev/patch_rebrand_gisele.py`) |
| Manual com seções multi-monitor, servidor Linux | "Manual PDF: expandir instruções Linux do servidor HTTP" + "Atualizar manual PDF com seção multi-monitor" | Edit do .py + regenerar |

---

## 3. Ferramentas usadas durante toda a sessão

| Ferramenta | Quando | Por quê |
|---|---|---|
| `Read` | Inspecionar HTML em chunks (offset/limit) | Arquivo de 1MB+ não cabe inteiro no contexto |
| `Edit` (anchor-based replace) | Patches no HTML/JS | Mais seguro que rewrite, mas **trunca o tail** em arquivos grandes — sempre reconstruir |
| `Write` | Arquivos novos (skill manuais, scripts BAT, manifest, HANDOVER) | Substitui inteiro |
| `Grep` (ripgrep) | Localizar símbolos no HTML | Mais rápido que Read full file |
| `Glob` | Listar diretórios | Quando o nome do arquivo é parcialmente conhecido |
| `mcp__workspace__bash` (Python) | Operações pesadas (decode shapefile, regex global, JSON manipulation, copy bicópia, build marker bump) | Edit tool trunca; Python lê/escreve sem problema |
| `node --check` | Validar JS após cada edit | Detecta truncamento ou regressão sintática |
| `md5sum` + `diff` | Garantir bicópia idêntica | Critério de aceitação |
| `TaskCreate / TaskUpdate` | Rastrear progresso | Visível no widget do Cowork |
| `mcp__cowork__present_files` | Compartilhar PDF e .bat finais | Botões para o usuário abrir |
| Snapshot restore (Python regex) | Reconstruir tail truncado | A partir do `gt-misc-data-corais_br` anchor + GeoJSON do disco |

---

## 4. Padrões críticos a respeitar (heurísticas duramente aprendidas)

1. **Bicópia obrigatória.** Toda mudança em `figuras_SisMOM_v23.html` deve ser replicada em `electron-app/figuras_SisMOM_v23.html`. Validar com `md5sum`. O usuário usa Electron como produto final.

2. **Edit tool trunca o tail.** Após qualquer Edit grande no HTML (>200 KB), checar:
   ```python
   html.rstrip().endswith('</html>')
   ```
   Se não, reconstruir do anchor `<script type="application/json" id="gt-misc-data-corais_br">\n` + corais_brasil.geojson do disco + `\n</script>\n</body>\n</html>\n`.

3. **Build marker.** Atualizar `20260529-XXXX-name` em **dois lugares** (console.log + data-build attr). Serve de check pro usuário detectar cache stale.

4. **node --check obrigatório.** Antes de declarar "feito", rodar:
   ```python
   scripts = re.findall(r'<script(?![^>]*type=["\']application/json["\'])(?:[^>]*)>([\s\S]*?)</script>', html)
   combined = '\n;\n'.join(s for s in scripts if s.strip())
   subprocess.run(['node', '--check', tmp])
   ```

5. **JSON inline (file://).** Manifest e GeoJSONs ficam em `<script type="application/json" id="gt-misc-*">` no final do `<body>`. O `gtLoadMiscManifest` lê primeiro do DOM (`document.getElementById`), depois faz fallback de fetch. Crucial pra `file://`.

6. **Canvas-to-video taint.** No PNG/GIF, NÃO desenhar `<img>` cross-origin direto no canvas de gravação — tainta e `captureStream` emite frames pretos. Re-fetch via blob → ObjectURL → new Image. Para captura sair com playback fluido: redesenhar em `requestAnimationFrame` durante toda a janela (force emission).

7. **Snap state.passoAtual.** Ao trocar de modelo (ou de aba), SEMPRE rodar `atualizarMaxPassos()` para recomputar `stepFreq/maxPassos` e clampar `state.passoAtual` ao grid. Modelos legacy têm `m.maxPassos` desatualizado — `v.horizonte` da variável é a verdade.

8. **Lock do git.** Existe um `.git/index.lock` órfão que o sandbox do Cowork não consegue remover (`rm` retorna Operation not permitted). Para commits, gerar `.bat` no Windows que executa: `del .git\index.lock` + `git read-tree HEAD` + `git add -A` + `git commit -m ...`. O arquivo `commit-changes.bat` já existe pronto.

---

## 5. Bugs/escolhas que NÃO devem ser re-introduzidos (lições)

| Comportamento | Por que NÃO |
|---|---|
| `Math.min(v.horizonte, m.maxPassos)` no cálculo de fileMax | `m.maxPassos` é legacy do slider antigo. BESM Global tinha 30 (cap), mas a variável PREC tem horizonte 720. Cortava série temporal em 1 ponto. Usar apenas `v.horizonte || m.maxPassos`. |
| Default `keepFill = false` nos contornos | Escondia o shaded sempre que isolinhas eram ativadas. Padrão deve ser preservar o preenchimento. |
| `drawImage(img cross-origin)` em canvas de gravação | Tainta → MediaRecorder emite frames pretos. Sempre re-fetch via blob. |
| `captureStream(fps)` assume frame rate fixo | Falso. Só emite quando o canvas muda. Para vídeo fluido: forçar redraw em RAF + pixel anti-dedup. |
| Switch "Liga/Desliga" no dropdown de Miscelâneas | Redundante — o chip da camada já tem olho/×. Removido após user reclamar. |
| `<input crossorigin="anonymous">` direto nos `<img>` do FTP | FTP do CPTEC não envia headers CORS → imagem nem carrega. Cross-origin handling deve ser no fetch (Electron CORS handler ou servidor local). |

---

## 6. Estrutura do repositório (paths importantes)

```
C:\Projetos\Visualizador\
├── figuras_SisMOM_v23.html        # HTML principal (raiz)
├── miscelaneas/
│   ├── manifest.json               # [plataformas_br, corais_br]
│   ├── plataformas_offshore_brasil.geojson   # 107 features, ~87 KB
│   └── corais_brasil.geojson       # 11 polígonos, ~410 KB
├── electron-app/
│   ├── figuras_SisMOM_v23.html    # CÓPIA exata da raiz
│   ├── miscelaneas/               # CÓPIA dos GeoJSONs
│   ├── main.js                    # Electron main process
│   ├── package.json               # electron-builder config (Win/Mac/Linux)
│   └── dist/                      # Saídas dos builds (.exe, .dmg, .AppImage)
├── vendor/leaflet.css             # Embed do Leaflet (mas usamos SisMOM_Map próprio)
├── tools/servir_dados/            # Servidor HTTP local (Python + Node)
│   ├── servir_dados.py
│   ├── servir_dados.js
│   ├── servir_dados.sh
│   └── servir_dados.bat
├── docs/
│   ├── GISELE_Manual_Uso.pdf      # Manual gerado por gerar_manual_uso.py (24p)
│   └── SisMOM_Manual_Uso.pdf      # Versão antiga (anterior ao rebrand)
├── dev/
│   ├── gerar_manual_uso.py        # Gerador do PDF (reportlab)
│   ├── patch_rebrand_gisele.py    # Rebrand mass replace
│   ├── snapshots/                 # Backups para restauração de tail
│   └── patch_*.py                 # Patches históricos (referência)
├── commit-changes.bat             # Script que remove lock + commit
├── HANDOVER_GISELE.md             # ESTE arquivo
└── .git/                          # Repo git (tem index.lock órfão)
```

---

## 7. Próximos passos identificados (pendings)

Tasks ainda pendentes no rastreador:

| ID | Tarefa | Sugestão |
|---|---|---|
| #7 | Pasta local com varredura (webkitdirectory) | Input com `webkitdirectory` para o usuário escolher pasta, varrer recursivamente todos `.tif` |
| #62 | Fase 3: paleta/min/max por variável (salvar e carregar default) | Adicionar `defaultPaleta`, `defaultMin`, `defaultMax` em cada variável; aplicar em `gtSelectPanel` similar ao mapProvider |
| #63 | Fase 4: controles de paleta por painel Mi no header | Movê-los para próximo do título de cada slot |

Outras melhorias úteis sugeridas:

- **Vídeo em paralelo:** pré-busca atualmente é paralela mas decode/render é serial. Para Eta (120 passos), 5 painéis paralelos demoram. Worker offline + IndexedDB cache poderiam acelerar.
- **Webhooks/eventos:** uma API JS pública para terceiros embedarem o GISELE e reagirem a passos. Hoje tudo é IIFE encapsulado.
- **Exportar configuração de painel** (modelo+variável+data+paleta+contornos) como link compartilhável.
- **Comparação A−B nativa** para evaluation de modelos (já tem na calculadora, mas UI manual). Botão "Diff" no header de M2..M4 que pega M1 como referência.

---

## 8. Como rodar a verificação completa após mudanças

```bash
# 1. Verifica que ambos HTMLs estão íntegros
md5sum figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html
# Devem ser idênticos

# 2. Termina com </html>?
python3 -c "print(open('figuras_SisMOM_v23.html').read().rstrip().endswith('</html>'))"

# 3. JSON inline parseável?
python3 -c "
import re, json
html = open('figuras_SisMOM_v23.html').read()
for tagid in ['gt-misc-data-plataformas_br', 'gt-misc-data-corais_br', 'gt-misc-manifest']:
    m = re.search(r'<script type=\"application/json\" id=\"' + tagid + r'\">([\\s\\S]*?)</script>', html)
    d = json.loads(m.group(1).strip())
    print(tagid, len(d.get('features', d.get('items', []))))
"

# 4. JS syntax check
python3 -c "
import re, subprocess, tempfile, os
html = open('figuras_SisMOM_v23.html').read()
scripts = re.findall(r'<script(?![^>]*type=[\"\\']application/json[\"\\'])(?:[^>]*)>([\\s\\S]*?)</script>', html)
combined = '\\n;\\n'.join(s for s in scripts if s.strip())
with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
    f.write(combined); tmp = f.name
print(subprocess.run(['node', '--check', tmp], capture_output=True, text=True).returncode)
os.unlink(tmp)
"

# 5. Build marker
grep -n "20260529" figuras_SisMOM_v23.html | head -2
```

---

## 9. Build markers da história recente

| Marker | Conteúdo |
|---|---|
| `20260528-4500-coraistail` | Restaurar tail truncado dos corais |
| `20260528-4600-notoggle` | Remover switch Liga/Desliga do dropdown |
| `20260529-1100-keepfill` | Contornos default keepFill = true |
| `20260529-1200-stepfix` | Fix swap PNG→GeoTIFF passo (parte 1) |
| `20260529-1300-mapdefault` | mapProvider config |
| `20260529-1400-mapenable` | Auto-ativa mapa quando modelo tem mapProvider |
| `20260529-1500-video` | Vídeo MP4 (versão inicial) |
| `20260529-1600-videopng` | Fix PNG taint via blob fetch |
| `20260529-1700-videoprefetch` | Pré-fetch todos os frames antes |
| `20260529-1800-videoclip` | Crop pela área visível (zoom/pan) |
| `20260529-1900-videofitfps` | object-fit math + força emissão de frames |

---

## 10. Glossário de identificadores JS importantes

| Símbolo | Função |
|---|---|
| `appMode` | `'png'` ou `'gtiff'` |
| `state` | Estado global (slots, passoAtual, maxPassos, stepFreq, layout, animando, tempo, interval) |
| `state.slots[i]` | `{modelo, variavel, data, sync, lastVarByModel, passoBase}` |
| `gtSlotState[i]` | Por-slot GeoTIFF: `{paleta, autoMinMax, min, max, undefRaw, clipBelow, clipAbove, mapEnabled, mapProvider, opacity, _lastModelForMap, _mapProviderUserSet, _mapEnabledUserSet}` |
| `gtSlotDecoded[i]` | Cache de decoded TIFF por slot |
| `gtActivePanel` | Índice do Mi ativo (recebe edições da sidebar direita) |
| `gtExtraLayers` | Array de camadas extras (overlays GeoTIFF/GeoJSON) |
| `gtSlotAnnotations[i]` | Anotações por slot (medições, textos, ferramentas) |
| `gtToolDraft[i]` | Rascunho de ferramenta em desenho |
| `montarURL({modelo, data, variavel, passo})` | Build URL com placeholders |
| `getEffectivePasso(slotIdx)` | Passo efetivo do slot (com offset de data) |
| `atualizarMaxPassos()` | Recomputa stepFreq/maxPassos baseado nos slots ativos |
| `_gtFetchAndDecode(url)` | Fetch + decode TIFF + cache |
| `gtSampleDecodedAtLatLon(decoded, lat, lon)` | Amostra valor no ponto |
| `SisMOM_Map(canvas)` | Factory do mapa custom |
| `SisMOM_GeoTIFF.decodeTIFF(buffer)` | Decoder próprio |
| `SisMOM_GeoTIFF.aplicarPaleta(decoded, opts)` | Paletiza para ImageData |
| `gtSelectPanel(idx)` | Ativa painel Mi e aplica mapa-base padrão do modelo |
| `gtCaptureControlsToActive()` | Captura UI da sidebar → gt[gtActivePanel] |
| `gtApplyActiveLayer()` | Aplica mudanças ao mapa |
| `gravarVideoEvolucaoTemporal()` | Grava MP4 da animação |
| `gtSampleTimeSeries(slotIdx, lat, lon, onProgress)` | Série temporal |
| `gtOpenProfilePopup(slotIdx, coords)` | Popup do perfil |
| `_stateRestore(snap)` | Restaura snapshot por aba + snap obrigatório de passoAtual |
| `setAppMode(mode)` | Troca PNG ↔ GeoTIFF + cleanup + re-render |

---

*Documento gerado em 29/05/2026 para handover. Última build verificada: `20260529-1900-videofitfps`.*
