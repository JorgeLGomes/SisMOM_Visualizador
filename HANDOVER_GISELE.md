# GISELE — Documento de Handover

**Repositório:** `C:\Projetos\Visualizador`
**Versão atual:** v2.14.0 — Build marker `20260609-skewt-cape`
**Commit HEAD:** `4982322 docs: HANDOVER atualizado sessao 08/06/2026` (Skew-T + performance + seguir-mapa pendentes — ver `commit-skewt.bat`)
**Arquivos críticos (sempre em lockstep — md5 idêntico):**
- `figuras_SisMOM_v23.html` (raiz)
- `electron-app/figuras_SisMOM_v23.html` (cópia idêntica para o build Electron)
- `miscelaneas/manifest.json` + `miscelaneas/*.geojson` (raiz + electron-app)

**MD5 atual:** `e00e9d80aa48add89972e3fa467b7448`
**Linhas do HTML:** ~23 999

> **Regra de ouro:** todo patch no HTML deve ser aplicado nos DOIS arquivos. Validar sempre com:
> ```
> python3 -c "import re,subprocess,tempfile,os; html=open('figuras_SisMOM_v23.html',encoding='utf-8').read(); scripts=re.findall(r'<script(?:(?!\btype\b)[^>])*>(.*?)</script>',html,re.DOTALL); all_js='\n;\n'.join(scripts); f=tempfile.NamedTemporaryFile(suffix='.js',delete=False,mode='w',encoding='utf-8'); f.write(all_js); fname=f.name; f.close(); r=subprocess.run(['node','--check',fname],capture_output=True,text=True); os.unlink(fname); print(r.stderr or 'OK')"
> cp figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html
> md5sum figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html
> ```

> **Estado do git (09/06/2026):** o HTML (raiz + electron-app) e o backend têm grande delta **não commitado** desta sessão (performance P1–P3, remoção do Leaflet, "seguir mapa" em perfil/corte/série, e o **Skew-T log-P** completo). Rodar no Windows o script pronto:
> ```
> commit-skewt.bat
> git push origin main
> ```

---

## 0. Mudanças da sessão 09/06/2026 (v2.13.0 → v2.14.0)

**Skew-T log-P (sondagem termodinâmica por ponto)** — novo botão na toolbar GeoTIFF (`data-tool="skewt"`) → `gtOpenSkewTDialog`:
- Diálogo: variável de **Temperatura 3D**, variável de **Umidade 3D** (UR **ou** umidade específica → ponto de orvalho via Magnus/pressão de vapor), faixa de níveis (base/topo) e **base pela pressão de superfície** (corta níveis com `p > Psfc`, recalculado por ponto/tempo).
- Diagrama (`gtOpenSkewTPopup`/`paint`): isotermas inclinadas 45°, isóbaras log-P, adiabáticas secas, pseudoadiabáticas, razão de mistura, curvas **T/Td** e pontos dos níveis do modelo.
- **Método da parcela** (`_skComputeParcel`): LCL (base da nuvem), LFC, EL (topo), **CAPE/CINE** por integração da flutuabilidade — curva da parcela tracejada, sombreado CAPE/CINE, marcas LCL/LFC/EL e caixa de valores no gráfico.
- Interação: **navegar** (zoom scroll + pan arrastar + duplo-clique/⤢ reset), painel **🎚 camadas** (liga/desliga cada componente), **inspeção** (clique ativa; mover o cursor segue o perfil de T mostrando o nível interpolado a 10 hPa), **seguir** cliques no mapa, **CSV**, **PNG** (alta-res com título) e **marcador do ponto no mapa** (`gtSetSkewTMarker`/`__skewtMarker`).
- Helpers termodinâmicos globais: `_skEsat`, `_skWsat`, `_skTdFromRH`, `_skTdFromQ`, `_skDryT`, `_skMoist`; sampler 2D de superfície sem nível: `_buildGtUrlForVar2D`/`_skSampleSurface`.

**Performance (P1–P3):** cliente `httpx` global no helper (lifespan), Service Worker `sw.js`, minificação do HTML no build (`scripts/minify-html.js`), `orjson` no backend (`ORJSONResponse` + `--hidden-import=orjson`), animação via PNG do servidor e índice de cache em memória. Leaflet removido (`vendor/` esvaziado) — não era usado.

**Perfis verticais 3D** (documentados no Manual, cap. 10): **perfil vertical por ponto** (`gtRunVerticalProfile`/`gtOpenVProfilePopup` — escala log/linear, cadeado mín/máx do eixo X, reamostragem ao trocar variável/nível), **evolução temporal** (`gtRunTemporalProfile` — nível × tempo, sombreado/isolinhas, colorbar, paleta, zoom 2D) e **corte vertical ao longo de linha** (`gtRunCrossSection` — pressão × distância, edição de vértices `gtVertexEdit`, eixo X distância/lat-lon, apontamento do ponto no mapa ao navegar).

**"Seguir mapa"** (controlador `gtPointFollow` + `_gtWireFollowBtn`): adicionado ao perfil vertical por ponto, perfil temporal, série temporal em ponto, corte vertical e Skew-T — clicar novo ponto re-renderiza sem fechar o pop-up.

---

## 1. Arquitetura geral

- **Single-page HTML** (~1 MB), JavaScript em IIFE no `<script>` final. Toda lógica num único namespace, sem framework.
- **Dois modos de operação** controlados por `appMode`:
  - `png` (PNG/GIF): imagens estáticas/animadas do FTP do CPTEC carregadas em `<img>`.
  - `gtiff` (GeoTIFF): TIF decodificado em ArrayBuffer + paleta + render num `<canvas class="map-canvas-gt">`.
- **Estado por aba** salvo em `localStorage` chaves `sismom_state_png` e `sismom_state_gtiff`. Restaurado em `_stateRestore` quando troca de tab.
- **Multi-painel** (1/2/3/4 slots = M1..M4) via grid CSS no `.map-container`. Layout muda em `setLayout`.
- **Decodificador GeoTIFF próprio** em `SisMOM_GeoTIFF.decodeTIFF(buffer)` (não usa lib externa — só UTIF para descompactação LZW se necessário).
- **`SisMOM_GeoTIFF` IIFE:** `const SisMOM_GeoTIFF = (function() { ... })()` — contém `makeRamp`, `GT_PALETTES`, `decodeTIFF`, `aplicarPaleta`, `isGeoTiffModel`, `setBands`, `setBandLevels`, `__workerSrc`. **`GT_PALETTES` é `const` interno — acessar sempre via `SisMOM_GeoTIFF.GT_PALETTES`**, nunca como global.
- **Sistema de paletas** em `aplicarPaleta(decoded, opts)`: viridis, plasma, inferno, magma, cividis, jet, turbo, rdbu, rdylbu, spectral + coolwarm. Lookup: `pal[idx*3]`, `pal[idx*3+1]`, `pal[idx*3+2]`.
- **Canvas custom `SisMOM_Map`** com projeção Mercator/PlateCarrée, tiles XYZ (Esri/OSM/OpenTopo), pan/zoom, anotações, overlays raster e GeoJSON.

---

## 2. Sessão 08/06/2026 — F21 + F22: Perfil vertical e temporal

### 2.1. Funções implementadas e suas localizações

| Função | Linha aprox. | Descrição |
|---|---|---|
| `gtOpenVProfileDialog(slotIdx)` | 4429 | Dialog de configuração (Instantâneo / Evolução Temporal) |
| `gtSampleTemporalProfile(...)` | 4618 | Amostragem assíncrona nível×passo → matriz |
| `gtRunTemporalProfile(...)` | 4664 | Progress dialog + dispatch para popup |
| `gtOpenTemporalProfilePopup(result, opts)` | 4704 | Popup Canvas2D com shaded/isolinhas/both + zoom + gear |
| `_buildGtUrlForNivel(slotIdx, passoH, nivel)` | 5156 | Monta URL GeoTIFF para dado nível (3 caminhos) |
| `gtSampleVerticalProfile(...)` | 5189 | Amostragem assíncrona por nível (perfil instantâneo) |
| `gtOpenVProfilePopup(result, opts)` | 5260 | Popup Canvas2D do perfil instantâneo |
| `_gtFmtVpValue(v, unidade)` | 5592 | Formata valor numérico com unidade |

### 2.2. Fluxo do perfil temporal

```
gtOpenVProfileDialog
  → modo "Evolução Temporal" selecionado
  → OK: chama gtRunTemporalProfile(slotIdx, lat, lon, niveisArr, passoMin, passoMax, passoFreq, vizType, paleta, varName)
      → abre progress dialog
      → chama gtSampleTemporalProfile → itera (nivel, passo) via _buildGtUrlForNivel + _gtFetchAndDecode
      → retorna { steps, niveis, matrix[nNiveis][nSteps], vmin, vmax, lat, lon }
      → chama gtOpenTemporalProfilePopup(result, { vizType, paleta, varName, unidade, mNome, runDateStr })
```

### 2.3. Estrutura dos dados do perfil temporal

```javascript
result = {
    steps:  [0, 6, 12, ..., 72],        // horas de previsão
    niveis: [100, 200, ..., 1000],       // pressão hPa, ordem crescente
    matrix: [[...], [...], ...],          // matrix[ni][si] — ni=nivelIdx, si=stepIdx
    vmin: float, vmax: float,
    lat: float, lon: float
}
opts = {
    vizType:    'shaded' | 'isoline' | 'both',
    paleta:     'viridis' | 'plasma' | 'jet' | ...,
    varName:    string,
    unidade:    string,
    mNome:      string,
    runDateStr: 'YYYYMMDDHH'   // s.data do slot, para cálculo de datetime no eixo X
}
```

### 2.4. `_buildGtUrlForNivel` — 3 caminhos de URL

```javascript
// Cobre: (1) modelo nativo GeoTIFF, (2) rota TIF própria, (3) derivação de PNG
function _buildGtUrlForNivel(slotIdx, passoH, nivel) {
    const isNativeGt = SisMOM_GeoTIFF.isGeoTiffModel(m);
    const isGtMode   = appMode === 'gtiff';
    if (isNativeGt)   → montarURL({ ..., tif:true })
    if (isGtMode && hasOwnTifRoute) → _buildMTifModel + montarURL
    if (isGtMode && !hasOwnTifRoute) → gtDeriveTifUrl(pngUrl)
    else → montarURL({ ..., tif:true })
}
```

### 2.5. `gtOpenTemporalProfilePopup` — estrutura do popup

**Posição:** canto inferior direito (`right:20px; bottom:20px`)
**Dimensões:** 792×550 px (mínimo 480×352), redimensionável (`resize:both`)
**Fonte:** `'Segoe UI', system-ui, -apple-system, Arial, sans-serif`

**Layout:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Perfil Temporal · ModeloNome · VarName  +0h→+72h  [viz▼][⚙][+Xh][⟲][×] │ ← header
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                     <canvas id="gtVTPCanvas">                       │ ← chart
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ 📍 lat -16.8936° · lon -46.7369°      [Baixar CSV] [Salvar PNG]    │ ← footer bar
└─────────────────────────────────────────────────────────────────────┘
```

**IDs dos elementos:**
- `gtVTProfPopup` — container principal
- `gtVTPHeader` — cabeçalho arrastável
- `gtVTPVizType` — `<select>` tipo de visualização (`color:#1f2937` explícito)
- `gtVTPGear` — botão `⚙` que abre painel de paleta
- `gtVTPXMode` — botão `+Xh`/`📅` toggle eixo X
- `gtVTPZoomReset` — botão reset zoom (hidden quando sem zoom)
- `gtVTPClose` — botão fechar
- `gtVTPCanvas` — canvas principal
- `gtVTPZoomBand` — div rubber-band de zoom
- `gtVTPTip` — tooltip hover
- `gtVTPPalPanel` — painel flutuante de paleta (8 radios)
- `gtVTPDownload` — botão Baixar CSV (footer)
- `gtVTPSavePNG` — botão Salvar PNG (footer, `canvas.toDataURL('image/png')`)

**Estado interno da função:**
```javascript
let vizType    = 'shaded' | 'isoline' | 'both'
let paleta     = 'viridis' | ... (8 opções)
let xZoom      = null | { si0: float, si1: float }    // índices de passo
let yZoom      = null | { pMin: float, pMax: float }  // pressão hPa
let xAxisMode  = 'hours' | 'datetime'
let dragState  = null | { startMx, startMy, endMx, endMy }
```

**`_draw()` — render interno:**
- Margem: `{t:20, b:46, l:64, r:20}`
- Eixo Y: escala log de pressão (`Math.log`)
- Eixo X: índices de passo com zoom
- Shaded: `ctx.createImageData(plotW, plotH)` + interpolação bilinear + `SisMOM_GeoTIFF.GT_PALETTES[paleta]`
- Isolinhas: Marching Squares (`_marchSquares`) com LUT 16 casos, 10 níveis HSL
- Both: shaded primeiro, depois isolinhas em `rgba(0,0,0,0.7)`
- Salva `canvas._vtMeta` para uso no tooltip e nos handlers de zoom

**`_stepToDateTime(stepH)` — conversão passo → datetime:**
```javascript
// runDateStr = 'YYYYMMDDHH'
new Date(Date.UTC(yr, mo-1, dy, hr) + stepH*3600000)
// → 'DD/MM HHZ'
```

**Zoom:**
- Rubber-band: mousedown/mousemove/mouseup no canvas → aplica `xZoom`/`yZoom`
- Scroll: `wheel` com `{passive:false}` → zoom ao redor do cursor (fator 1.3/0.77)
- Reset: duplo-clique ou botão `⟲ zoom`

**Painel de paleta (gear):**
- `getBoundingClientRect()` do botão gear → posiciona `gtVTPPalPanel` em `position:fixed`
- Fecha ao clicar fora (`document.addEventListener('click', ...)`)
- 8 radios: viridis, plasma, jet, rdbu, rdylbu, spectral, coolwarm, turbo

---

## 3. Dialog `gtOpenVProfileDialog` — estado atual

**Fonte:** `'Segoe UI', system-ui, -apple-system, Arial, sans-serif`

**Seção temporal (campos presentes):**
- `vpPassoIni` / `vpPassoFim` — inputs passo inicial/final
- `vpVizType` — select: Sombreado / Isolinhas / Sombreado + Contorno
- **Paleta NÃO está no dialog** — gerenciada via engrenagem no popup
- `const paleta = 'viridis';` no OK handler (padrão fixo)

**OK handler — ordem correta (crítico):**
```javascript
// Ler TODOS os valores ANTES de ov.remove()
const passoIni = parseInt(document.getElementById('vpPassoIni').value) || 0;
const passoFim = parseInt(document.getElementById('vpPassoFim').value) || passoMax;
const vizType  = document.getElementById('vpVizType').value;
const paleta   = 'viridis';
ov.remove();  // só então remover o overlay
gtRunTemporalProfile(...);
```

---

## 4. Bugs corrigidos nesta sessão (histórico)

| Bug | Causa | Fix |
|---|---|---|
| `_buildGtUrlForNivel is not defined` | Patch anterior sobrescreveu a função ao substituir bloco de código | Reinserção da função antes de `/* Amostra o valor */` |
| `GT_PALETTES is not defined` | `GT_PALETTES` é `const` dentro da IIFE, não é global | Usar `SisMOM_GeoTIFF.GT_PALETTES` |
| Popup temporal não abria | `ov.remove()` chamado ANTES de ler `getElementById('vpPassoIni')` etc. — elementos já não existiam no DOM | Ler todos os valores antes de `ov.remove()` |
| Assertion `function _buildGtUrlForNivel not in content` | `_buildGtUrlForNivel` estava entre o fim do popup e o marker `/* Amostra o valor */` — a região a ser substituída incluía a função | Mudar `old_popup_end_marker` para `/* Constrói a URL do GeoTIFF */` |

---

## 5. Localizações-chave no HTML (linhas aproximadas)

| Elemento | Linha |
|---|---|
| `gtOpenVProfileDialog` | 4429 |
| `gtSampleTemporalProfile` | 4618 |
| `gtRunTemporalProfile` | 4664 |
| `gtOpenTemporalProfilePopup` | 4704 |
| `_buildGtUrlForNivel` | 5156 |
| `gtSampleVerticalProfile` | 5189 |
| `gtOpenVProfilePopup` | 5260 |
| `_gtFmtVpValue` | 5592 |
| `SisMOM_GeoTIFF` IIFE start | ~7655 |
| `GT_PALETTES` definição | ~7670 |
| `GT_PALETTES` exposto em `return` | ~8122 |
| `_gtFetchAndDecode` | ~8311 |
| `gtSampleDecodedAtLatLon` | ~12151 |

---

## 6. Histórico de versões e mudanças anteriores

### v2.4 → v2.5
Painel direito reorganizado em árvore ERMA-style (Background/Miscelânea/Camadas/Ferramentas) com sub-menu "Configuração da Camada" por nó. Nova Calculadora dupla: expressão livre entre camadas + operador-escalar per-layer. "Abrir TIF local" removido do menu Ferramentas.

### v2.5 → v2.6
(1) Calculadora Temporal per-layer (sintaxe `tN/hN`, ranges `t1..t24`, funções sum/mean/max/min/count). (2) Exportar GeoJSON (raster→nuvem de pontos): campo cheio, polígono/retângulo, camada vetorial. Série temporal de ponto → GeoJSON. (3) Importar Shapefile (.shp/.zip) — parser puro JS. (4) Fix HUD lat/lon/valor. (5) Botão 👁/⊘ por camada. (6) `style.noVertices` no renderer.

### v2.6 → v2.7
(1) Python helper opcional (FastAPI + rasterio) embed no Electron com fallback JS. (2) Slider de opacidade. (3) Marching squares otimizado (~8-15×). (4) Cache de contornos LRU cap 100.

### v2.7 → v2.8
(1) Estatísticas no GeoJSON exportado (min/max/soma/média/área). (2) Popup de resultado após export. (3) Reorganização Exportar GeoJSON (5 opções). (4) Popup de help "?" por seção. (5) Highlight visual da opção selecionada.

### v2.8 → v2.9
Python helper: cache decoded LRU 256 + endpoint `/v1/render/png`. Polígonos do usuário: storage localStorage + submenu Ferramentas + drawing flow `save-only`/`export`. Reorganização UI massiva: DnD reorder, boot colapsado, gear+trash inline nas camadas. Multi-painel: bbox sync, lock por painel (🔒), perfil combinado, série temporal paralela. Gráficos interativos: chips de legenda com toggle, zoom rubber-band, clipping.

### v2.9 → v2.10
Cidades brasileiras (240 cidades, agrupadas por UF, lazy-load). Cliente Python `gisele_ts` para scripts/notebooks.

### v2.10.0 → v2.11.0
Fix multipainel MERGE com fallback automático de data. Desenho no modo PNG (toolbar por painel, canvas de anotações normalizadas, replicação por lock). Anotação livre na tela (caneta global). Série temporal multi-camada com camadas de cálculo (`calcSpec`). Fix MERGE, barra de abas, bug `ov.remove`.

### v2.11.1 → v2.12.0
Base de dados (nova categoria): tipo `kind:'points'`/`'metar'`/genérico, modal 2 níveis. Menu Monitoramento na árvore ERMA. Fetch + parse KML/GeoJSON. Queimadas padrão (INPE/INPE). Station model METAR visual. Bookmarks (visões salvas). Botões Limpar/Visualizar no header. Exportar PDF cartográfico. Série temporal por polígono. Web Worker pool para decodificação. Cache de bitmaps ~1 GB LRU.

### v2.12.1 → v2.13.0 (release base desta sessão)
METAR: 251 estações + station model visual (chama vetorial, não emoji). Spatial Bookmarks completo. Exportar PDF. Série temporal por polígono. Worker pool decode. Cache bitmaps. Base de pontos (`kind:'points'`). `ADEQUACAO_COPERNICUS.md`.

### Sessão 07/06/2026
Vento vetorial (`vec_u`/`vec_v`, setas/streamlines). Coluna Fórmula per-variável. Resize colunas tabela + resize modal. Fix Base de dados (showBasesPane flex→display simples). Scroll horizontal fino nas abas.

### Sessão 08/06/2026 (atual)
F21 + F22 completos + 5 melhorias no popup temporal (ver seções 2 e 3 acima).

---

## 7. Funcionalidades operacionais (tabela por categoria)

### 7.1 Carregamento e renderização

| Feature | Status |
|---|---|
| Decodificação GeoTIFF nativa + paletas (viridis/plasma/jet/rdbu/turbo/...) | ✅ |
| Cache de blob URL + ImageData por (url+opts) | ✅ |
| Heurística multi-sentinel NoData + min/max percentil | ✅ |
| Render por scanline em Mercator | ✅ |
| Auto flip-Y + GTRasterTypeGeoKey | ✅ |
| Shaded suavizado/bandas/pixel (seletor por camada) | ✅ |
| Bandas seguem níveis do contorno (`setBandLevels`) | ✅ |
| Web Worker pool decode (N workers = hardwareConcurrency, teto 4) | ✅ |
| Cache bitmaps renderizados ~1 GB LRU | ✅ |

### 7.2 Ferramentas de análise GeoTIFF

| Feature | Status |
|---|---|
| Perfil vertical instantâneo (`gtOpenVProfileDialog` modo Instantâneo) | ✅ |
| Perfil vertical temporal — matriz nível×passo (`gtOpenTemporalProfilePopup`) | ✅ |
| Visualização: Sombreado / Isolinhas / Sombreado+Contorno | ✅ |
| Zoom 2D: rubber-band + scroll + reset | ✅ |
| Eixo X alternável: horas de previsão / data/hora de validade | ✅ |
| Paleta via gear icon (sem redimensionar o gráfico) | ✅ |
| Download CSV da matriz | ✅ |
| Salvar PNG do gráfico | ✅ |
| Série temporal em ponto (multi-painel, multi-camada) | ✅ |
| Série temporal por polígono (max/min/mean) | ✅ |
| Perfil ao longo de polilinha | ✅ |
| Calculadora raster (expressão livre + per-layer) | ✅ |
| Calculadora temporal (tN, ranges, sum/mean/max/min) | ✅ |
| Exportar GeoJSON (campo cheio / polígono / retângulo / camada / área total) | ✅ |
| Exportar PDF cartográfico | ✅ |

### 7.3 Camadas e miscelâneas

| Feature | Status |
|---|---|
| Miscelâneas: plataformas offshore, corais, cidades BR | ✅ |
| Monitoramento: fetch KML/GeoJSON, Queimadas INPE, METAR | ✅ |
| Polígonos do usuário: salvar/carregar/visualizar | ✅ |
| Importar shapefile (.shp / .zip) | ✅ |
| Camadas extras do FTP (modelo+variável como overlay) | ✅ |
| Vento vetorial (setas / streamlines, vec_u/vec_v) | ✅ |
| Base de dados customizável (modal "Base de dados") | ✅ |

---

## 8. Estrutura HTML do modal de configurações (referência rápida)

```
.modal (display:flex; flex-direction:column; position:relative; overflow:hidden; max-height:92vh)
  .modal-rsz-h #modalConfigRszH  ← handle SE, position:absolute
  .modal-header
  #modalTopTabs                   ← "Configurar modelos" | "Base de dados"
  .modal-tabs #modalTabs          ← abas dos modelos (overflow-x:auto, scrollbar thin)
  .modal-body #modalBody          ← flex:1; min-height:0; overflow-y:auto; padding:16px 18px
    .form-grid                    ← formulário do modelo (hidden quando bases)
    .var-table-wrap               ← tabela de variáveis (hidden quando bases)
    #cfgBasesPane                 ← pane de bases (display:none por padrão, '' quando ativo)
  footer.modal-footer             ← FORA do #modalBody (sibling direto de .modal)
```

---

## 9. Estado dos commits (08/06/2026)

### Commits realizados (em ordem cronológica relevante)

| Hash | Conteúdo |
|---|---|
| `bda9463` | v2.13.0 — METAR + Bookmarks + PDF export + série temporal por polígono + Worker decode + cache bitmaps |
| `b0cdbb3` | feat(gt): campo vetorial de vento + coluna fórmula + resize modal/tabela + F21 + F22 (commit cumulativo) |
| `427aa2a` | feat(gt): F22 — perfil temporal completo (vizType/paleta/gear/zoom/X-mode/PNG/bottom-bar) ← **HEAD** |

### Pendente de commit (documentação)

```bat
git add HANDOVER_GISELE.md commit-f22-temporal-profile.bat docs/
git commit -m "docs: HANDOVER atualizado sessao 08/06/2026 (F22 temporal profile)"
git push origin main
```

> Os BATs `commit-resize.bat`, `commit-scroll-fix.bat`, `commit-bases-fix.bat` podem ser ignorados — suas mudanças já estão capturadas em `b0cdbb3`.

---

## 10. Próximos desenvolvimentos sugeridos

- **Colorbars / legenda no popup temporal** — barra de cores com rampa horizontal no rodapé do canvas
- **Animação do perfil temporal** — botão play para percorrer os passos de previsão frame a frame
- **Múltiplos pontos simultâneos** — plotar perfis de vários pontos sobrepostos no mesmo popup
- **Perfil temporal para múltiplas variáveis** — ex.: temperatura e umidade no mesmo gráfico (eixo duplo)
- **Export do popup como PNG em alta resolução** — via canvas offscreen 2× ou 3× para relatórios
- **Integração com Python helper** — `gtSampleTemporalProfile` atualmente faz fetch serial; paralelizar via `/v1/timeseries/point` do helper ou fetch paralelo por nível
- **Sincronização do perfil temporal com o mapa** — clicar no popup destaca o passo no mapa principal
