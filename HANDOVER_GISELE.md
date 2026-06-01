# GISELE — Documento de Handover

**Repositório:** `C:\Projetos\Visualizador`
**Versão atual:** v2.11.0 — Build marker `20260601-12300-pngmenu`
**Arquivos críticos (sempre em lockstep):**
- `figuras_SisMOM_v23.html` (raiz)
- `electron-app/figuras_SisMOM_v23.html` (cópia idêntica para o build Electron)
- `miscelaneas/manifest.json` + `miscelaneas/*.geojson` (raiz + electron-app)

> **Importante:** todo patch no HTML deve ser aplicado nos DOIS arquivos. Validar com `node --check` e `md5sum` antes de seguir. O Edit tool tem tendência a truncar o tail; SEMPRE checar `</html>` final e reconstruir a partir do `gt-misc-data-corais_br` se faltar.

> **Mudanças de UI v2.4 → v2.5:** o painel direito foi reorganizado em árvore ERMA-style (Background / Miscelânea / Camadas / Ferramentas) com sub-menu **Configuração da Camada** por nó (paleta/min-max/clip/contornos/calc per-layer) movido fisicamente por `appendChild`. Nova **Calculadora dupla**: expressão livre entre camadas em Ferramentas + operador-escalar per-layer na Configuração da Camada. Item **"Abrir TIF local (inspeção)"** foi removido do menu Ferramentas (use **+ Adicionar GeoTIFF/GeoJSON** ou a aba dedicada do header).

> **Mudanças v2.5 → v2.6:** (1) Nova **Calculadora Temporal** em Configuração da Camada com sintaxe `tN`/`hN`, ranges `t1..t24`, funções `sum/mean/max/min/count`. (2) **Exportar GeoJSON** (raster→nuvem de pontos): campo cheio, polígono/retângulo desenhado, ou recorte por camada vetorial carregada. Também **série temporal de ponto → GeoJSON**. (3) **Importar Shapefile** (.shp standalone ou .zip) como camada vetorial — parser puro JS embarcado + ZIP reader via `DecompressionStream`. (4) Fix HUD lat/lon/valor (default ON + toggle na árvore ERMA). (5) Botão `👁/⊘` explícito em cada camada com dim de row ao ocultar. (6) Renderer respeita `style.noVertices` (linha pura sem bolinhas em cada vértice — essencial para shapes com centenas de vértices).

> **Mudanças v2.6 → v2.7:** (1) **Python helper opcional** (FastAPI + rasterio + httpx) embedado no Electron como subprocess — acelera extração temporal, calculadora temporal e perfil de linha com fetches paralelos (~10× speedup esperado). Frontend tem **fallback transparente** para JS quando o helper está offline. Badge UI no canto inferior direito mostra status `⚡ Python` ou `JS only`. (2) Sub-menu da árvore ERMA renomeado de `⚙ Configuração da Camada` → `🛠 Ferramentas`. (3) **Slider de opacidade** adicionado no painel (sincroniza com a camada ativa ao expandir nós). (4) Widget de calculadora escalar per-layer (op + escalar + Aplicar) removido — coberto pelo textarea de Tempos. (5) **Marching squares otimizado** (single-pass + máscara pré-computada Uint8Array + early-skip por cellMin/cellMax + zero closures no hot loop): ~8-15× mais rápido. (6) **Cache de contornos** com fingerprint dos dados (URL do TIF para primary) + LRU true (touch on hit) + cap 100 — animações com contornos ligados ficam quase instantâneas após primeira passagem.

> **Mudanças v2.7 → v2.8:** (1) **Estatísticas no GeoJSON exportado**: `metadata.stats` inclui min, max, soma, média, média ponderada pela área (Soma / Área km²) e área total em m². (2) **Popup de resultado** após Polígono/Retângulo/Por camada/Área total — não auto-salva mais; usuário vê tabela com stats e decide via botão **💾 Salvar GeoJSON**. (3) **Reorganização da árvore Exportar GeoJSON** — 5 opções top-level: ⏱ Série temporal em ponto, ▦ Por polígono, ▭ Por retângulo, 🗂️ Por camada vetorial, 🌐 Área total da camada. (4) **Ícone "?" com popup de help** em cada seção (Calculadora, Exportar, Tempos) substituindo descrições inline; gtShowHelpPopup com auto-posicionamento. (5) **Highlight visual da opção selecionada** em Exportar GeoJSON — borda + background cyan + bullet `●` enquanto a ferramenta está ativa; flash animado na Área total.

> **Mudanças v2.8 → v2.9:**
>
> **Python helper estendido:** (1) **Cache decoded em memória** (`OrderedDict` LRU 256 entradas) + **endpoint `/v1/render/png`** que aplica paleta server-side via matplotlib (viridis/plasma/RdBu_r/terrain/...) + Pillow, com hierarquia de 4 níveis (png cache → decoded cache → disk cache → FTP). Auto vmin/vmax por percentil 5-95 quando não passado; NoData → alpha=0. `/health` reporta stats dos dois caches. (2) **Bridge JS `gtPyHelper.renderTilePNG(url, opts)`** retorna `ImageBitmap` pronto para `drawImage` (fallback `HTMLImageElement` quando `createImageBitmap` indisponível). Opt-in, não altera caminho principal de animação.
>
> **Polígonos do usuário (novo módulo completo):** (1) Storage `gtSavedPolygons` em `localStorage` (chave `gisele.savedPolygons.v1`) com `save/list/getById/exists/remove/rename/setColor/clearAll`. Em Electron, persiste em disco (`%APPDATA%\GISELE\Local Storage`). (2) **Submenu "👤 Polígonos do usuário"** dentro de Ferramentas com lista colapsável `📋 Lista de salvos (N)`, ações `✏️ Desenhar e salvar` / `📥 Exportar` / `📤 Importar`. Cada linha: checkbox de visualização (toggle on/off no mapa, cor magenta default) + nome + **⚙ gerenciar** (renomeia + mostra perímetro/área/bbox/data) + **color picker** (contorno) + **🗑 excluir**. (3) `gtAddUserPolyLayer(savedId)` converte registro salvo em `gtExtraLayer` `isUserPoly=true` (geojson FeatureCollection com 1 Polygon). Toggled-on layers aparecem automaticamente em **🗂️ Por camada vetorial** do Exportar GeoJSON com origem "Polígono do usuário". (4) **Drawing flow**: novo intent `_gtDrawIntent='save-only'` salva o polígono sem extração; `'export'` (default) abre dialog com opção de salvar + extrair. Após salvar, ativa visualização automática. (5) Export/Import via arquivo `.geojson` (FeatureCollection com metadados `# M1=…`).
>
> **Reorganização UI massiva:** (1) **Lat/Lon/Valor** movido da toolbar para `<li>` dentro de Ferramentas (título capitalizado). (2) **Polígonos do usuário** dentro de Ferramentas (não mais em Miscelânea). (3) **Drag-and-drop reorder** das ferramentas via grip `⋮⋮` à esquerda de cada `<li>` — ordem persistida em `localStorage` chave `gisele.tools.order.v1`. Implementação via HTML5 DnD com `data-tool-id`. (4) **Boot sempre colapsado**: todas as 4 seções top-level (Background/Miscelânea/Camadas/Ferramentas) sem atributo `open`; botão Collapse folders → "Expand folders". (5) **Camadas: gear ⚙ inline + 🗑 trash** substituem `<details>` "🛠 Ferramentas" e botão `×`. Gear abre painel de Configuração inline embaixo da linha; estado ativo destaca em cyan. (6) **Polígonos do usuário no `gtRenderTreeUserPoly`** com lista colapsável memorizada entre re-renders.
>
> **Multi-painel: bbox sync + travamento + replicação:** (1) `SisMOM_Map` ganhou API `getViewport`/`applyViewportRaw(vp)`/`setViewportChangeListener(cb)`. `_fireVp()` dispara após pan/wheel/zoomBy/fitTo/resize. Flag `_vpSilent` em `applyViewportRaw` evita loop. (2) `_gtMakeViewportPropagator(srcIdx)` copia vp do slot fonte para todos os outros via `applyViewportRaw`; guard `_gtSyncingVp` previne recursão. Novo slot copia vp do painel 1 ao ser criado. (3) **`_gtApplyMapView` lock no painel 1**: para slots ≠ 0, copia `_gtSlotMap[0].getViewport()` em vez de `fitTo(bbox)` do layer — preserva área do painel 1 ao trocar modelo em Mi 2/3/4. (4) Ao **trocar modelo em slot ≠ 0** para um diferente do painel 1, `s.data = s0.data` (alinha condição inicial; valid time alinha via `getEffectivePasso`). (5) **Lock por painel** (🔒/🔓 botão ao lado do pin): `gtLockedPanels: Set<number>`. Ações replicadas para travados: distância, linha, texto, perfil, **limpar anotações**. (6) **Perfil combinado**: amostra todos painéis-alvo, plota curvas coloridas por painel (paleta fixa azul/vermelho/verde/roxo), tooltip multi-série, CSV combinado `value_M1/M2/...`. (7) **Série temporal multi-painel**: amostragem **paralela** via `Promise.all` com progress agregado `M1:48/48✓ · M2:24/48 · M3:✗`, drawing incremental, sort por `slotIdx`, CSV combinado.
>
> **Gráficos interativos (TS + Perfil):** (1) **Toggle on/off por chip da legenda** — click no chip alterna `ts.visible`; chip OFF tem `⊘` + strikethrough + opacity 0.4. Y range auto-zooma sobre só os visíveis. (2) **Ícone 👁** nos chips ajuda a descobrir a affordance. (3) **Zoom por click-and-drag** (rubber-band) sobre a área do plot; mouseup aplica zoom; double-click ou botão "↻ zoom" reseta. Hint "arraste para zoom · duplo-clique reseta" no canto. CSS `.gt-chart-zoom-rect` / `.gt-chart-zoom-reset`. (4) **Clipping** (`ctx.save()` + `rect(margin.l, margin.t, plotW, plotH)` + `ctx.clip()` + `ctx.restore()`) ao redor das curvas — quando zoomado, valores fora do range não extrapolam para os eixos/labels.

> **Mudanças v2.9 → v2.10:**
>
> **Cidades brasileiras (nova miscelânea agrupada por UF):** (1) Novo item `cidades_br` no `manifest.json` — 240 cidades (capitais + principais), props `nome/uf/regiao/populacao/capital`, com dois campos novos de manifesto: `groupByProp` (agrupa por UF) + `groupOrder` (ordem por região, N→S). (2) Novo render hierárquico `_gtRenderMiscGroupedItem`: `<details>` por item → `<details>` por UF (lazy-load no `toggle`); cada UF vira camada própria com id `cidades_br::SP` (checkbox liga/desliga TODAS as cidades do estado de uma vez). (3) Cabeçalho com contador (`240 em 27 grupos`) + ações globais `✓ Todos` / `👁 Limpar`; dentro de cada estado, filtro de texto `🔍 Filtrar cidades…` + ações locais `☑ Todas` / `👁 Nenhuma`. (4) GeoJSON embarcado inline (`<script id="gt-misc-data-cidades_br">`) para `file://`. (5) Script gerador `dev/baixar_cidades_brasil.py`. Bicópia raiz↔electron sincronizada (manifest + geojson, md5 confere).
>
> **Cliente Python `gisele_ts` (`api-client/`):** módulo standalone que envelopa o endpoint `/v1/timeseries/point` do helper Python — extração de série temporal num ponto (lat, lon) a partir de scripts/notebooks/pipelines. Componentes: `gisele_ts/client.py` + `models.py` + CLI (`__main__.py`) + `examples/extract_ts.py` + `setup.py` (`pip install -e .`). README com instruções de uso standalone (`python server.py --port 8000`).
>
> **Infra/versão:** `.gitignore` ganhou patterns Python (`__pycache__/`, `*.pyc`, `*.egg-info/`). `package.json` + `package-lock.json` 2.9.0 → 2.10.0. Build marker `20260531-11500-collapsed` → `20260601-12000-cidades`.
>
> **Mudanças v2.10.0 → v2.11.0 (release atual):**
>
> **Correção multipainel — MERGE/análise com recuo automático de data:** painéis de análise (`frequencia=0`, ex.: MERGE) em M2–M4 continuam alinhados à data de **validade do M1**, mas quando não há imagem no FTP nessa data (ex.: MERGE do dia ainda não publicado) agora **recuam automaticamente** dia a dia (passo = `freq_rodadas`, 1 dia p/ MERGE) até a observação mais recente disponível (até `ANA_FALLBACK_MAX = 14` tentativas). Nova `carregarAnaliseComFallback` (probe via `new Image()` + cache por alvo `s._anaCache`); `applyAnalysisDates` ficou **idempotente** (`s._anaAlignTarget` impede resetar a data já resolvida em re-renders); badge **↩ RECUADO** no resumo do topo quando a data exibida difere da validade do M1; "Tentar novamente" limpa o cache. Não afeta animação (cai no caminho simples de carga) nem o fluxo GeoTIFF.
>
> **Desenho no modo PNG/GIF (linha, área, texto) + seleção/lock/replicação por painel:** novo módulo paralelo ao do GeoTIFF. (1) Cada painel ganha uma **toolbar no topo** (`.png-toolbar`, só em modo PNG): seletor de painel ativo (M1..M4), 🔒 lock, ✋ pan, ╱ linha, ▭ área, T texto, ⌫ borracha, seletor de cor e 🗑 limpar. (2) Anotações num `<canvas class="png-anno">` dentro do `.map-viewport`, em **coords normalizadas ao conteúdo da imagem** (`object-fit:contain` via `pngContentRect`), acompanhando zoom/pan pelo `transform` CSS do viewport — PNG é imagem estática, sem georreferência. (3) Linha/área multi-vértice (clique adiciona, duplo-clique/Enter finaliza, Esc cancela), texto via prompt, borracha por hit-test (vértice/segmento). (4) **Lock + replicação**: desenhar num painel travado replica a anotação clonada para todos os travados na mesma posição relativa (`pngTargets`/`pngCommit`). (5) Redesenho em load de imagem (anima também), `ResizeObserver` por viewport, troca de modo/layout. Estado em memória (`pngAnnots`/`pngLockedPanels`/`pngActivePanel`/`pngColor`). Isolado: não toca no GeoTIFF (lat/lon) nem na animação. Hooks via try/catch.
>
> **Versão:** `package.json` + `package-lock.json` 2.10.0 → 2.11.0. Build marker `20260601-12000-cidades` → `20260601-12300-pngmenu`. (v2.11.0 agrupa o fix do MERGE + o desenho no PNG num único release.)

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
| Calculadora raster v1 (A+B, A−B, A×B, A÷B, escalar) | "Calculadora de camadas (raster algebra)" | Edit |
| **Calculadora v2 — expressão entre camadas** (NOVO) | "dentro do menu Ferramentas inserir uma aba Calculadora… cálculos entre camadas, que pode ser definido através de uma expressão (ex: Camada1*1000+Camada1)" | Edit (parser recursive-descent `gtParseExpr` + `gtCreateLayerFromExpression`, tokens clicáveis, sub-nó Ferramentas) |
| **Calculadora v2 — per-layer (op + escalar)** (NOVO) | (idem prompt) | Edit (gtBuildLayerConfigPanel adiciona linha `🧮 Calc: camada [op] [esc] [Aplicar]`, monta expressão `CamadaN op esc`) |

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
| **ESPECIFICACOES_GISELE (.md + 18p PDF)** (NOVO) | "Gerar um relatório com as especificações para o desenvolvimento dessa plataforma do zero. Gerar um pdf" | Write `.md` + pandoc/xelatex |
| **Manual v2.4 — seção 6 ERMA tree, seção 9 calculadora dupla, seção 11 checkbox Miscelânea** (NOVO) | "atualizar a documentação e commit" | Edit `dev/gerar_manual_uso.py` |

### 2.13. UI v2.4+ (árvore ERMA-style)

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| **Painel direito como árvore ERMA com 4 grupos colapsáveis** (NOVO) | "Organizar o painel da direita como nesse exemplo da plataforma erma utilizando dropdown menu Background... Miscelânea... Camadas... Ferramentas..." | Edit (HTML tree skeleton + `gtRenderLayerChips` re-render por grupo) |
| **Sub-menu "Configuração da Camada" por nó** (NOVO) | "Essas funcionalidades devem estar disponíveis em um segundo nivel de menu, associado à cada camada Regional Eta .... \|_ Configuração da Camada" + "Os controles da camada já estão presentes na Configuração da Camada, pode remover os campos persistentes" | Edit (`#gtLayerConfigPanel` único movido por `appendChild` entre `#gtLayerConfigHome` invisível e `.gt-tree-config-host`; layout vertical em `gtBuildLayerConfigPanel`) |
| **Fix toggle recursivo do sub-menu** | "O menu Configuração de Camada abre não está respondendo e depois de aberto não fecha" | Edit (click handler em `summary` com `e.preventDefault()` no lugar do toggle event — toggle re-renderiza re-criando `details open=true` e entrando em loop) |
| **Botão Collapse/Expand folders** (NOVO) | "Colocar um botão Collapse folders" | Edit (toolbar topo da árvore, alterna `details[open]` de todos os grupos, rótulo dinâmico) |
| **Fix "Adicionar Modelo" invisível** | "Funcionalidade de Adicionar Modelo não está responsiva" | Edit (form `#gtAddFromModelForm` movido fisicamente por `appendChild` para dentro do nó Ferramentas; antes ficava dentro de `.gt-old-controls` `<details>` fechado) |
| **Calculadora dupla** (NOVO) | "dentro do menu Ferramentas inserir uma aba Calculadora com as opções algébricas básicas (+,-,x,/), colocar essas opções também na configuração da camada. Na configuração da camada, o cálculo será executado na camada específica, no menu ferramentas, estará disponível para cálculos entre camadas, que pode ser definido através de uma expressão (ex: Camada1*1000+Camada1)" | Edit (parser recursive-descent + AST `num/ident/bin/neg` + `gtCreateLayerFromExpression`; tokens clicáveis no sub-nó Ferramentas; linha `🧮 Calc` em `gtBuildLayerConfigPanel`) |
| **Background com radios mutex** (NOVO em v2.4) | "no executável, o geotif entra sem o mapa de background. O satélite (Esri) está selecionado, mas não está sendo plotado" | Edit (default `mapEnabled: true` + `mapProvider: 'esri'` em `gtSlotState`; radio change chama `_gtApplyMapView` imediatamente) |
| **Miscelânea com checkboxes que add/remove** (NOVO em v2.4) | (parte da reestruturação ERMA) | Edit (`onchange` da checkbox chama `gtPushMiscLayer` / `gtRemoveMiscLayer` reusando engine antiga) |
| **Fix Miscelâneas v1: gtLayerPushToMap retorna early sem `maps`** | "Não está plotando os corais e plataformas" | Edit (criar mapa do slot mesmo sem TIF, com bbox default Brasil) |
| **Fix Miscelâneas v2: ordem canvas display vs createMap** | "Continua não plotando" | Edit (`box.classList.add('gt-map-active')` ANTES de `cvEl.style.display=''` ANTES de `void cvEl.offsetWidth` ANTES de `gtSlotEnsureMap`) |
| **Fix Miscelâneas v3: expor resize() na API** | (idem) | Edit (`SisMOM_Map` retorna `resize` + `getCanvasRect`; chamado após push do extra layer) |
| **Fix Miscelâneas v4: ReferenceError gtFindMiscLayerByConfigId** | "nenhuma das duas seleções estão funcionando, não plota nenhuma informação" (com console screenshot) | Edit (restaurar função `gtFindMiscLayerByConfigId(id)` que tinha sido removida em #153; tree handler ainda chamava → ReferenceError abortava todo o handler) |
| **Remover "Abrir TIF local (inspeção)" do menu Ferramentas** (NOVO) | "Remover do menu 'Ferramentas' 'Abrir TIF local (inspeção)'" | Edit (remover `<details class="gt-tree-tif-inspect">` da árvore; aba dedicada no header continua) |
| **Bump v2.4.0 (dist file lock)** | "Travou na geração da dist" + screenshot do `output file is locked for writing` | Edit (`electron-app/package.json` 2.0.0 → 2.4.0 para forçar nome de artifact novo; `rebuild-electron.bat` com `taskkill /F /IM GISELE-*.exe`) |
| **--strict-cors flag (Electron)** | "Avaliar webSecurity:false caso CORS bloqueie" | Edit (`electron-app/main.js`: default `webSecurity:false`, `--strict-cors` reativa `true`; log `CORS mode:` em `launch.log`) |
| **Preset FTP CPTEC na configuração** | "Configurar modelo .tif via FTP" | Edit (botão "Preset FTP CPTEC" marca PNG+TIF, deriva `/fig/` → `/geotiff/`, nome `{prefixo}-{F%4}.tif`) |

### 2.14. Importar / Exportar dados (v2.6+)

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| **Calculadora Temporal (per-layer)** | "Na calculadora da camada, incluir a possibilidade de manipulação de camadas de tempos distintos de uma mesma rodada... t1+t2+t3 ou t1..t3" | Edit (parser estende gtParseExpr com function calls + ranges; `gtCreateLayerFromTimeExpression` + `gtEvalTimeAst` + `_gtExpandRangeIdx`; modal de progresso `gtOpenTimeCalcProgress`) |
| **Fix HUD lat/lon/valor — default ON + toggle ERMA** | "A informação lat, lon e valor do ponto do cursor do mouse não está mais disponível" | Edit (`gtNavHudEnabled = true` default; checkbox `#gtTreeShowNavHud` na toolbar da árvore espelhando o legacy) |
| **Exportar GeoJSON (raster→point cloud)** | "inserir na ferramenta a opção de salvar o dado em formato geojson de uma área selecionada ou todo o campo" | Edit (`gtExportLayerToGeoJsonPointCloud`, `gtDownloadGeoJson`, sub-nó na árvore Ferramentas, 5 modos de recorte) |
| **Exportar série temporal de ponto → GeoJSON** | "incluir uma ferramenta para salvar um geojson da evolução temporal de um ponto" | Edit (`gtSampleTimeSeriesToGeoJson` reusa `gtSampleTimeSeries`; tool `export-timeseries`) |
| **Fix visual draft de polígono/retângulo export** | "problema para mapear a área para exportar o dado" + "Ainda com problema" | Edit (gtMakeAnnotProvider reconhece `export-polygon`/`export-rect`; isDragTool flag; rótulo `📤`) |
| **FIX bbox object: minX/maxY (não array)** | (causa do "object is not iterable") | Edit (`decoded.bbox` é `{minX,minY,maxX,maxY}` — destructuring de array falhava; agora usa campos + valida + iteração top-down) |
| **Parser shapefile .shp puro JS** | "upload shapefile para extração da informação" | Edit (`_gtParseShpBuffer` ~110 linhas: Polygon, PolygonZ, PolygonM; outer/hole por orientação; multi-part); smoke test Node passou |
| **ZIP reader via DecompressionStream** | (idem) | Edit (`_gtExtractFromZip`: EOCD + central dir + LFH + DecompressionStream `deflate-raw`; suporta stored e deflate) |
| **Preview + dialog de confirmação no upload** | "Quando o usuário fizer um upload do shape, geojson.... plotar sobre o mapa e pedir para confirmar a extração" | Edit (`_gtShowPolygonPreview` + `gtOpenConfirmExtractDialog`; fit ao bbox; cleanup de previews; Enter/Esc) |
| **Dialog fora da área do mapa** | "Colocar o box da informação fora da área de visualização do gráfico" | Edit (overlay sem backdrop fullscreen; card `position:fixed; top:14px; right:14px; pointer-events:auto`) |
| **Renderer `style.noVertices`** | "as linhas estão bem grossas" + "deixar na mesma espessura para todas as linhas" | Edit (renderer polígono pula loop de circles em cada vértice quando `style.noVertices === true`; lineWidth uniforme 0.7) |
| **Importar shapefile como camada extra** | "importar shapefile na ferramenta" | Edit (`gtAddExtraLayerFromFile` estendida com `.shp` e `.zip`; `_gtPolygonsToGeoJsonFC` converte para FeatureCollection; label do botão atualizado) |
| **Toggle 👁/⊘ explícito + dim row** | "Opção de ligar e desligar a camada (shape, geojson, etc)" | Edit (no `gtRenderTree` substitui checkbox por button 24×22px com ícone 👁/⊘ colorido; row inteira ganha `opacity:0.5` quando oculta) |
| **Máscara via camada vetorial carregada** | "remover o upload da máscara de extração do geojson e no local disponibilizar a camada que foi carregada" | Edit (remove botão Upload + handler 50 linhas; "🐠 Por shape de Miscelânea" → "🗂️ Por camada carregada" filtra `type==='geojson'`; dialog mostra origem + bolinha de cor) |

### 2.15. Python helper + UX v2.7

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| **Python helper backend (FastAPI subprocess)** | "em uma fase intermediária, é possível migrar a extração temporal do valor de um ponto para backend em python, rodando na máquina do usuário" | Write (electron-app/python-helper/: server.py 417 linhas, url_builder.py 125 linhas, sampler.py 144 linhas, requirements.txt, README.md, build-helper.bat/sh) |
| **electron python-spawner.js (subprocess lifecycle)** | (idem) | Write (python-spawner.js 162 linhas: spawn em dev/packaged, probe /health com retry 15s, taskkill no Windows, SIGTERM→SIGKILL no Unix) |
| **preload.js (IPC bridge)** | (idem) | Write (contextBridge.exposeInMainWorld('GISELE_PYTHON', { getUrl, isAvailable, onStatusChange })) |
| **main.js integração + ipcMain handlers** | (idem) | Edit (app.whenReady spawna helper paralelo; before-quit mata; ipcMain.handle('gisele-python:get-url')) |
| **package.json files + extraResources** | (idem) | Edit (preload.js, python-spawner.js em files; python-helper/dist → resources/python-helper extraResources) |
| **gtPyHelper module no frontend** | (idem) | Edit HTML (~140 linhas: refresh com probe /health a cada 5s, sampleTimeSeries/sampleProfileLine/calcTemporal, badge UI cyan/cinza no canto inferior direito) |
| **gtSampleTimeSeries guard com fallback** | (idem) | Edit (try gtPyHelper.sampleTimeSeries → fallback JS original) |
| **Slider de opacidade + sync ao mover painel** | "falta o controle da opacidade na Configuração da camada" | Edit (gOp row em gtBuildLayerConfigPanel: input range 0-100 + label %; gtMoveCfgPanelToLayer lê opacity da camada-alvo e atualiza slider) |
| **Renomear "⚙ Configuração da Camada" → "🛠 Ferramentas"** | "Mudar o título Configuração da camada para Ferramentas" | Edit (smr.textContent no details summary) |
| **Remover widget calc per-layer escalar** | "não precisa essa opção, pois tem o espaço para expressão. Mudar Calc. camada para Calculadora, remover o dropdown dos sinais" | Edit (gC widget completo — select op + input escalar + btn Aplicar + status — substituído por simples header "🧮 Calculadora" com border-top) |
| **Marching squares otimizado** | "demora para gerar os contornos da variável quando selecionado" | Edit (gtComputeContours reescrito: máscara Uint8Array pré-computada, single-pass com cellMin/cellMax early-skip, Float32Array para Larr, zero closures, inlining de pos/interp, hoist de dLon/dLat/lat0/lon0) — speedup ~8-15× |
| **Cache de contornos com fingerprint** | "Quando gerar os contornos, salvar como camada ou guardar no cache, para economizar tempo de processamento" | Edit (_gtContourCacheKey aceita dataFingerprint = lastLoadedURL[slot] para primary OU layer.id; LRU true via delete+set on hit; cap 100; remoção da invalidação agressiva primary\|* em gtRerenderSlot) |

### 2.16. Export stats + UX v2.8

| Feature | Prompts originais | Ferramentas |
|---|---|---|
| **Estatísticas no metadata do GeoJSON** | "Na opção de exportar geojson, do polígono, inserir no geojson o valor máximo, mínimo, acumulado, médio e a média ponderada pela área" | Edit (gtExportLayerToGeoJsonPointCloud: statMin/statMax/statSum/statAreaWeightSum/statTotalAreaM2 no loop; return inclui `metadata.stats = { count, min, max, sum, mean, areaWeightedMean, totalAreaM2 }`) |
| **Área em m² (não km²)** | "calcular a área em m2" | Edit (statTotalAreaM2 = R² × dΛ × |sin(latTop)−sin(latBot)| × 1e6) |
| **Média ponderada = Soma / Área(km²)** | "o valor média ponderada deve ser calculada Soma (acumulada)/Área em km2" | Edit (removeu Σ(v·cos(lat))/Σcos(lat); agora areaWeightedMean = statSum / (statTotalAreaM2 / 1e6)) |
| **Popup com stats + botão Salvar (sem auto-save)** | "Mostrar esses valores em um quadro popup com a opção de salvar as informações em geojson" | Edit (gtExpShowResultDialog: card 380px canto superior direito com tabela formatada; botões Fechar e 💾 Salvar GeoJSON; Enter salva, Esc fecha; pointer-events:auto só no card) |
| **Separação Exportar GeoJSON ↔ Série temporal** | "separar 'Exportar geojson' e 'Série temporal em ponto' em duas opções de ferramentas" | Edit (tree HTML: duas details separadas; gtExpStatus + gtTsStatus distintos) |
| **Reorganização hierárquica** | "Colocar subtarefas na seção Exportar GeoJSON" + "por polígono inclui Área total / Desenhar polígono / Por camada" | Edit (Por polígono virou details aninhado com 3 sub-opções; depois flat-out na próxima iteração) |
| **Move Série temporal pra Exportar GeoJSON** | "Mover o menu série temporal em ponto para dentro do menu Exportar GeoJSON, substituindo a opção Por ponto" | Edit (Por ponto removido; ⏱ Série temporal em ponto vira primeira opção do Exportar GeoJSON; sub-tree separado removido) |
| **5 opções flat top-level** | "Falta a opção... usar as camadas carregadas... incluir também a opção de área total da camada" | Edit (botões btnGtExpTimeseries/Poly/Rect/Misc/Full no mesmo container, sem nesting) |
| **Ícone "?" com popup de help** | "informação sobre a ferramenta acessada através de uma ? no final do campo... Mover todos os textos de explicação para esse padrão" | Edit (CSS .gt-help-icon + .gt-help-popup; gtShowHelpPopup com auto-position; delegação global `document.addEventListener('click', ...)` em fase de captura; data-help em cada `<span class="gt-help-icon">?</span>`) |
| **Highlight visual da opção ativa** | "Na seleção de Exportar GeoJSON, fazer highlight da seleção" | Edit (CSS .gt-tree-action.selected: bg/border/color cyan + bullet `●`; _GT_EXP_TOOL_TO_BTN mapeia tool→buttonId; gtSetSlotTool sync automático; _gtExpFlash para Área total; _gtExpHighlight/Clear no Misc dialog) |

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
| `md5sum` + `diff` | Garantir bicópia raiz ↔ electron-app idêntica | Build do Electron quebra se HTMLs divergem |
| `ResizeObserver`, `requestAnimationFrame` | Render canvas | Forçar passes diferidos pra pegar layout final do flexbox |

---

## 4. Padrões críticos (NÃO mexer sem entender)

1. **Bicópia obrigatória.** Toda mudança em `figuras_SisMOM_v23.html` (raiz) precisa ir também para `electron-app/figuras_SisMOM_v23.html`. Validar com `md5sum` antes de declarar pronto:
   ```bash
   md5sum figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html
   # devem casar
   ```
   Para Miscelâneas, `manifest.json` e os `.geojson` também precisam estar em ambas as pastas `miscelaneas/`.

2. **Tail truncado pelo Edit.** O Edit tool tem tendência a comer os últimos 50-200 bytes em arquivos grandes (>1MB). SEMPRE checar:
   ```python
   html = open('figuras_SisMOM_v23.html').read()
   html.rstrip().endswith('</html>')
   ```
   Se não, reconstruir do anchor `<script type="application/json" id="gt-misc-data-corais_br">\n` + corais_brasil.geojson do disco + `\n</script>\n</body>\n</html>\n`.

3. **Build marker.** Atualizar `YYYYMMDD-XXXX-name` em **dois lugares** (console.log + data-build attr). Serve de check pro usuário detectar cache stale.

4. **node --check obrigatório.** Antes de declarar "feito", rodar:
   ```python
   scripts = re.findall(r'<script(?![^>]*type=["\']application/json["\'])(?:[^>]*)>([\s\S]*?)</script>', html)
   combined = '\n;\n'.join(s for s in scripts if s.strip())
   subprocess.run(['node', '--check', tmp])
   ```

5. **JSON inline (file://).** Manifest e GeoJSONs ficam em `<script type="application/json" id="gt-misc-*">` no final do `<body>`. O `gtLoadMiscManifest` lê primeiro do DOM (`document.getElementById`), depois faz fallback de fetch. Crucial pra `file://`.

6. **Canvas-to-video taint.** No PNG/GIF, NÃO desenhar `<img>` cross-origin direto no canvas de gravação — tainta e `captureStream` emite frames pretos. Re-fetch via blob → ObjectURL → new Image. Para captura sair com playback fluido: redesenhar em `requestAnimationFrame` durante toda a janela (force emission).

7. **Snap state.passoAtual.** Ao trocar de modelo (ou de aba), SEMPRE rodar `atualizarMaxPassos()` para recomputar `stepFreq/maxPassos` e clampar `state.passoAtual` ao grid. Modelos legacy têm `m.maxPassos` desatualizado — `v.horizonte` da variável é a verdade.

8. **Multipainel: viewport sync via guard.** Em qualquer mutação de `self.vp` (pan/wheel/zoomBy/fitTo/resize), `_fireVp()` chama o listener registrado. Para evitar loop quando propagar para outros slots, usar `applyViewportRaw(vp)` que ativa `_vpSilent = true` antes de mexer no vp. Flag global `_gtSyncingVp` previne re-entrada da camada superior.

9. **Lock do git.** Existe um `.git/index.lock` órfão que o sandbox do Cowork não consegue remover. Para commits, gerar `.bat` no Windows que executa: `del .git\index.lock` + `git read-tree HEAD` + `git add -A` + `git commit -m ...`. O arquivo `commit-changes.bat` já existe pronto para v2.9.0.

---

## 5. Bugs/escolhas que NÃO devem ser re-introduzidos (lições)

| Comportamento | Por que NÃO |
|---|---|
| `Math.min(v.horizonte, m.maxPassos)` no cálculo de fileMax | `m.maxPassos` é legacy do slider antigo. BESM Global tinha 30 (cap), mas a variável PREC tem horizonte 720. Cortava série temporal em 1 ponto. Usar apenas `v.horizonte || m.maxPassos`. |
| Default `keepF