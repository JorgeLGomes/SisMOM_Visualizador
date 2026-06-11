# GISELE 2.16.0

Build: `20260610-form-campos`
Data: 2026-06-11

## Novidades v2.16.0

### Leitura por *range-read* (/vsicurl) — ferramentas por ponto e por linha
Amostragem que lê só o(s) tile(s) do ponto/janela do GeoTIFF remoto (HTTP range request),
em vez de baixar o arquivo inteiro. Validado contra o FTP do CPTEC (suporta Range + CORS).

- **Helper (server.py)** — novos endpoints (aplicáveis pelos scripts em `electron-app/python-helper/`):
  - `POST /v1/point/series` (`point_series_patch.py`) — amostragem genérica por ponto: atende **série
    temporal**, **perfil vertical por ponto** e **SkewT-LogP** (varia passo/nível/variável).
  - `POST /v1/line/sample` (`line_sample_patch.py`) — amostra uma **linha** por leitura janelada
    (1 leitura por nível cobrindo o bbox da linha): **corte vertical**.
  - `use_vsicurl` em `POST /v1/timeseries/point` (`poc_vsicurl_patch.py`) — série temporal por range-read.
- **Frontend** — SkewT, perfil vertical por ponto, série temporal e corte vertical passam a usar esses
  endpoints quando o helper está disponível, com **fallback automático** para o caminho JS (sem regressão).
  Chaves de escape: `window.GISELE_POINTSERIES=false`, `window.GISELE_SKEWT_HELPER=false`.
- **Pré-requisitos:** `orjson` instalado no Python do helper; aplicar os patches; reiniciar o helper.
- Docs: `docs/AVALIACAO_microservico_ponto.md` (avaliação) e `docs/POC_vsicurl_resultados.md` (POC + testes).
- **Requisitar trecho visível** — botão `⊡ Requisitar trecho visível (servidor)` na config da camada: pede ao servidor apenas o **recorte do viewport** (bbox visível) do campo ativo via `GET /v1/tile/window` (`window_patch.py`, leitura janelada `_dl_clip_tif`), recortando aos **dados válidos** da cobertura, e carrega como camada (`gtRequestViewportWindow`).


### Sombreado em Bandas (filled contour) na configuração da camada
- Novo sub-painel **Bandas** (aparece em Sombreado → "Bandas (shaded)") com: **Mín/Máx** da escala
  (+ automático) e definição das bandas por **Nº de bandas (automático)** ou **intervalos explícitos**.
- Cada banda recebe **uma cor chapada** (sem gradiente). A suavização de cor (`rasterSmooth`) passa a
  valer **só** no modo Suavizado.
- **Filled contour:** no modo Bandas, os **dados** são interpolados (bilinear) para uma grade fina e só
  então classificados — **bordas suaves/curvas** entre as classes, como nas figuras GIF de referência.
  Bordas de NoData preservadas no pixel mais próximo.

### Divisão política no Background (estados BR + países da América do Sul)
- Nova seção **🗺 Divisão política** no nó **Background**, com toggles **Estados (Brasil)** e
  **Países (América do Sul)** — overlay vetorial desenhado direto no mapa (não vira "Camada").
- Dados: `miscelaneas/divisao_estados_br.geojson` (27 UFs) e `divisao_paises_sa.geojson` (13 países),
  derivados do Natural Earth (admin_1/admin_0, via `sane-topojson`), com nomes (`nome`/`sigla`/`iso3`).
- **Inicia com os estados do Brasil ligados** por padrão (preferência salva em `gisele.divisions.v1`).
- **Cores e espessura** das linhas configuráveis (estados e países), persistidas em `gisele.divisions.style.v1`.

### Divisão política na Miscelânea (cada feição como camada selecionável)
- Nova seção **🗺 Divisão política** na **Miscelânea**, hierárquica: **América do Sul ▸ países** e
  **Brasil ▸ 27 estados** — cada polígono é uma feição que pode ser ligada/desligada individualmente.
- O que já estava no Background foi mantido; aqui cada feição vira camada própria (ids `mdiv_<tipo>_<chave>`),
  com preferência salva em `gisele.misc.div.v1`.

### Recorte do campo por polígono (máscara) + aquisição do *box* no servidor
- Em qualquer camada de polígono, a ação **Recortar** plota o campo **somente dentro do polígono**,
  mascarando todo o exterior (`setClipPolygon` no mapa; recorte aplicado no desenho dos rasters).
- A mesma ação **requisita ao servidor apenas o *box* que contém o polígono** (`GET /v1/tile/window`,
  leitura janelada `/vsicurl`), carregando o recorte como camada `… · box` — **sem `fitTo`** (não muda o zoom).
- Durante a **animação**, a camada do *box* (estática) fica **oculta** automaticamente — vale a máscara
  sobre o campo que está animando ao vivo; ao **parar**, o *box* do servidor reaparece. Requer o helper (⚡).

### Animação mais estável
- **Preservar zoom na troca de data/passo:** o reenquadre automático (`fitTo`) passa a ocorrer **só na
  primeira vez** que o painel mostra um modelo. Trocar a **rodada/data** ou avançar o **passo** mantém o
  zoom do usuário; trocar de **modelo** reenquadra.
- **Filtro de frames anômalos:** durante a animação, frames cujo **domínio é muito maior** que a referência
  do painel (ex.: TIF global com span de longitude `>150°` e `>2,5×` a referência) são **pulados**, mantendo
  o último frame bom — evita o "pulo" causado por passos cujo dado sai em grade/domínio diferente
  (desligável via `window.GISELE_SKIP_ANOMALOUS_FRAMES=false`).
  - **Nota:** o caso observado (precipitação saindo **global a cada 24h**) é da **geração do dado**
    (TIF de acumulada em grade diferente nos passos 24/48/72h), não da lógica do visualizador.

---

# GISELE 2.15.0

Build: `20260610-predictor3-cache`
Data: 2026-06-10

## Novidades v2.15.0

### GeoTIFF — suporte ao *floating-point predictor* (predictor=3)
- O decodificador passou a tratar **predictor=3** (TIFF TechNote 3) para dados float32/64, além de 1 e 2. TIFs float com predictor=3 antes apareciam distorcidos (deslocamento horizontal dependente dos valores); agora decodificam corretamente. Correção verificada por round-trip (erro 0) e propagada ao pool de Web Workers.
- Log de diagnóstico do decode enriquecido (`tileW`, `tileH`, `nSeg`, `planar`).

### Atualizar dados / correção de cache
- Novo botão **"🔄 Atualizar dados (limpar cache)"** no nó **Camadas**: limpa os caches em memória do viewer, limpa o cache em disco do helper Python (`POST /cache/clear`) e re-busca os campos carregados furando o cache do navegador. Use depois de **regerar dados/rodadas** (ex.: troca de predictor) — antes, arquivos regerados na mesma URL continuavam sendo servidos do cache.
- Helper: respostas de TIF/PNG passam a usar `Cache-Control: no-cache` (elimina a obsolescência de 24h no navegador; o cache em disco do helper continua para performance). **Requer reiniciar o helper Python.**

### Recomendação de geração de dados
- Para campos **Float32/64**, gere os GeoTIFFs com **`PREDICTOR=3`** (padrão correto do GDAL para ponto flutuante). Já refletido em `config_glob2eta.yaml` (`cog.predictor: 3`).

---

# GISELE 2.14.0

Build: `20260609-skewt-cape`
Data: 2026-06-09

## Novidades v2.14.0

### Skew-T log-P — sondagem termodinâmica por ponto
- Novo botão na toolbar do GeoTIFF: amostra **Temperatura 3D** e **umidade 3D** nos níveis de pressão do ponto e desenha o diagrama Skew-T log-P.
- Ponto de orvalho derivado de **umidade relativa** ou **umidade específica** (escolha no diálogo; Magnus / pressão de vapor).
- Diagrama completo: isotermas inclinadas a 45°, isóbaras (log-P), adiabáticas secas, pseudoadiabáticas, linhas de razão de mistura, curvas de **T** e **Td** e pontos dos níveis do modelo.
- **Definição de níveis**: faixa base/topo, ou **nível inferior pela pressão de superfície** (PSLC) — descarta níveis abaixo do terreno, recalculado por ponto e por passo de tempo.
- **Método da parcela**: base da nuvem (**LCL**), **LFC**, topo da nuvem (**EL**) e cálculo de **CAPE** e **CINE**, com curva da parcela, sombreado das áreas e caixa de valores no gráfico.
- **Interatividade**: zoom (scroll) e pan (arrastar) com reset, painel **🎚 camadas** para ligar/desligar cada componente, **inspeção** que segue o perfil de T (valores interpolados a 10 hPa ao mover o cursor), **seguir** cliques no mapa, exportação **CSV** e **PNG** (alta resolução com título) e **marcador do ponto no mapa**.

### Performance (P1–P3)
- Cliente HTTP global (`httpx`) reaproveitado via *lifespan* no helper Python.
- **Service Worker** (`sw.js`) para cache de assets estáticos.
- **Minificação do HTML** no build standalone (`scripts/minify-html.js`).
- **orjson** no backend (respostas mais rápidas) e índice de cache em memória.
- Animação servida como PNG pelo helper; **Leaflet removido** (não era utilizado).

### Perfis verticais 3D — ponto, tempo e linha
- **Perfil vertical por ponto**: variável 3D num ponto (nível × valor), escala log/linear, fixação do mín/máx do eixo X (cadeado), reamostragem automática ao trocar variável/nível.
- **Evolução temporal do perfil**: seção nível × tempo num ponto (Sombreado / Isolinhas / Sombreado+Contorno), com colorbar, seletor de paleta, eixo X em horas ou data e zoom 2D.
- **Corte vertical (ao longo de uma linha)**: seção pressão × distância para variável 3D, com **edição de vértices** (arrastar pontos re-renderiza o caminho), eixo X em distância **ou** lat/lon, zoom navegável e apontamento do ponto no mapa ao percorrer o gráfico.

### "Seguir mapa" nos gráficos
- Perfil vertical por ponto, perfil temporal, série temporal em ponto, corte vertical e Skew-T ganharam o botão **📍 seguir**: clicar um novo ponto no mapa re-renderiza o gráfico sem fechar o pop-up; o gráfico também acompanha a navegação no tempo.

---

# GISELE 2.13.0

Build: `20260602-3350-veccache`
Data: 2026-06-05

## Novidades v2.13.0

### METAR — Estações meteorológicas em tempo real
- Base default `metar_br` no Monitoramento: busca dados da API aviationweather.gov
- Decoder próprio `gtDecodeMETAR`: temperatura, ponto de orvalho, umidade, vento, visibilidade, nuvens, teto, pressão QNH, tempo presente
- **Station model visual** escalado por zoom: cobertura de nuvens, bárbulas de vento (kt), T/Td/Pressão no símbolo clássico
- 251 estações (Brasil + Am. do Sul/Central/Caribe) em `miscelaneas/estacoes_metar.json`
- Filtro interativo de estações; `gtMetarRebuildIndex` sincroniza índice ICAO→props

### Spatial Bookmarks (🔖)
- Botão 🔖 no header salva/restaura visões completas: viewport, modelo ativo, visibilidade de camadas, layout de painéis
- Topics/categorias para organizar bookmarks
- Persistido em `localStorage` chave `gisele.bookmarks.v1`

### Exportar PDF cartográfico (botão PDF)
- Captura canvas atual + legenda + seta-norte + barra de escala em PDF-1.4 puro JS (sem libs externas)
- Dialog com título e subtítulo; download direto como `.pdf`

### Série temporal por polígono (📈)
- Novo modo no Exportar GeoJSON: extrai max/min/mean por passo para um ou mais polígonos
- Cache dedicado de rasters (~1 GB LRU) evita re-download entre feições do mesmo passo
- Python helper: endpoint `/v1/timeseries/polygon` com máscara NumPy (~10× mais rápido)

### Web Worker pool para decodificação GeoTIFF
- Pool de N workers paralelos (= `hardwareConcurrency`, máx 4); fallback transparente para thread principal
- `SisMOM_GeoTIFF.__workerSrc`: fonte autocontida serializada — sem arquivo Worker externo
- UI não trava durante decode de grades grandes na animação e na série temporal

### Cache de bitmaps renderizados (~1 GB LRU)
- Bitmaps `createImageBitmap` cacheados por `(url, opts)`; troca de frame na animação só substitui bitmap
- `_gtTsRasterCache` separado (~1 GB) para série temporal; reutiliza entre feições do mesmo passo
- Tetos em bytes (não só contagem) para memória previsível em grades de alta resolução

### Base de pontos + Nova base de dados
- "+ Nova base de pontos" no modal de Configuração: carrega CSV ou GeoJSON de pontos do usuário
- `gtOpenShapeClassConfig`: classificação visual de camadas por campo com esquema de cores

### Botões "🧹 Limpar" e "👁 Visualizar" no header
- Substituem o antigo "Abrir GeoTIFF local"
- "Limpar" remove camadas e desmarca visão ativa; "Visualizar" renderiza o modelo configurado na toolbar

### Documento ADEQUACAO_COPERNICUS.md
- Análise de aderência GISELE × Plataforma COPERNICUS (MPSP/INPE)
- Diagnóstico dos 4 cards, tabela ✅/🟡/❌ por requisito, plano de adequação em fases

---

# GISELE 2.12.1

Build: `20260601-20400-bandlevels`
Data: 2026-06-02

## Novidades principais (vs 1.0.0)

### Modo GeoTIFF (novo)
- Aba **GeoTIFF** ao lado de PNG/GIF, com pipeline próprio
- Decodificador TIFF inline (sem dependências externas) — LZW, Deflate, PackBits, float32/int16/uint8, predictor 2, tiles+strips, multi-tiepoint (GrADS)
- Detecção iterativa de sentinelas (NoData) + fallback por percentil 1%/99% para grids com escalas absurdas
- **15 paletas científicas**: Viridis, Plasma, Inferno, Magma, Cividis, Jet, Turbo, Cinza, RdBu, RdYlBu, Spectral, BrBG, Seismic, Coolwarm, Terrain, Ocean

### Multi-painel com mapa-base
- Suporta layouts 1/2/3/4 painéis no modo GeoTIFF
- Cada painel Mi tem seu próprio mapa-base (canvas) com tiles XYZ (Esri Satélite, OSM Ruas, OpenTopoMap)
- Controle de opacidade do raster sobre o mapa, por painel
- Seleção do painel ativo via pin "Painel Mi" no canto do mapa

### Painel direito (sidebar)
- Controles agrupados em seções colapsáveis: Arquivo / Visual, NoData / Clip, Camadas, Calculadora
- Edições no painel afetam **apenas o painel Mi ativo** (gtSlotState por slot)
- Camadas extras (GeoTIFF + GeoJSON) com reordenação, opacidade, visibilidade
- Calculadora de raster: A op B (+, −, ×, ÷) ou A op escalar, gera nova camada derivada

### Filtros e clipping
- UNDEF manual (lista de sentinelas, ex: `-999, -9999`)
- Clip ≥ / Clip ≤ para mascarar fora de faixa
- Recálculo automático de min/max ignorando mascarados

### HUD e navegação
- Valor sob o cursor (lat/lon + valor da célula) na barra inferior
- Pan/zoom no canvas raster (mesmo sem mapa-base)
- Aspect ratio preservado em todos os redimensionamentos

### Performance
- **Cache LRU** de TIFFs decodificados (URL → decoded), imageData (URL+opts → ImageData), blob URL (URL+opts → blob:)
- Dedup in-flight de fetches (mesma URL pedida em paralelo compartilha promessa)
- Reuse de canvas scratch
- Skip de `setTileProvider`/`fitTo` quando inalterado
- Resultado: 2ª passada da animação fica praticamente instantânea após a 1ª caching

### Rotas distintas PNG/TIF por modelo
- Modelo pode declarar `tem_png` / `tem_tif` (formato disponível no FTP)
- Variável pode declarar `disp_png` / `disp_tif`
- Modelos sem TIF são automaticamente filtrados da aba GeoTIFF
- Templates separados de URL/nome para PNG e TIF, com toggle "usar o mesmo do PNG"

### Default ao abrir
- Sempre inicia em PNG/GIF + modelo Eta (estado da aba GeoTIFF preservado em localStorage)

### Empacotamento Electron
- `webSecurity: false` para fetch direto do FTP (CORS bypass)
- `package.json` v2.0.0 com arquivos PWA (manifest, icons múltiplos)
- Scripts `build.bat` e `build.sh` automatizados: sincronizam HTML da raiz, instalam deps, limpam dist/, geram instalador

## Novidades 2.1.0 → 2.12.1

> Cada versão abaixo é um release; detalhes completos no `HANDOVER_GISELE.md`.

- **2.1.0–2.3.0** — Ferramentas de medição/análise (distância, área, retângulo, círculo, **perfil de linha** e **série temporal num ponto** com gráficos interativos), **vídeo MP4** da evolução temporal (PNG e GeoTIFF), **mapa-base padrão por modelo**, Miscelâneas (Plataformas offshore + Corais BR com hachura/cor/popup), flag `--strict-cors` e Preset FTP CPTEC.
- **2.4.0** — Reorganização do painel direito em **árvore ERMA** (Background/Miscelânea/Camadas/Ferramentas) + **Configuração da Camada por nó** + **calculadora dupla** (expressão entre camadas e op per-layer).
- **2.5.0** — Fix do Background Esri no executável + correções das Miscelâneas (v1–v4) + remoção de "Abrir TIF local".
- **2.6.0** — **Calculadora Temporal** (`t1..t24`, `sum/mean/...`), **Exportar GeoJSON** (raster→nuvem de pontos) e **Importar Shapefile** (parser JS puro + ZIP via DecompressionStream).
- **2.7.0** — **Helper Python** local opcional (FastAPI + rasterio) com fallback transparente; marching squares ~8–15× mais rápido + cache de contornos; opacidade/rename/calc.
- **2.8.0** — Exportar GeoJSON com **estatísticas** (min/max/soma/média/área) + popup de confirmação + reorganização da UX de exportação.
- **2.9.0** — **Multi-painel** (bbox sync + lock + replicação + perfil/série combinados) + **Polígonos do usuário** (salvar/exportar) + gráficos interativos (toggle por legenda, zoom drag).
- **2.10.0** — **Cidades brasileiras** (miscelânea agrupada por UF) + cliente Python `gisele_ts` (extração de série temporal standalone).
- **2.11.0 / 2.11.1** — **Desenho no modo PNG/GIF** (linha/área/texto com seleção/lock/replicação por painel) + fix do MERGE multipainel (recuo automático de data); série temporal consolidada multi-camada/cálculo; **anotação livre na tela** (caneta).
- **2.12.0** — **Base de dados** (rotas genéricas KML/GeoJSON) + menu **📡 Monitoramento** na árvore ERMA, com **Queimadas recentes (INPE)** out-of-the-box (atualização ao vivo, filtro Ativas/Inativas, popup de atributos, marcador 🔥) e config persistente em arquivo (Electron).
- **2.12.1** — Render do raster GeoTIFF **interpolado** (bilinear) + modos de sombreado **Suavizado / Bandas / Pixel**, com **bandas alinhadas aos níveis do contorno**.

## Como gerar a distribuição

Veja `electron-app/LEIA-ME-build.txt`. Resumo:

**Windows:**
```
cd electron-app
rebuild-electron.bat   (ou build.bat, legado)
```
Saída em `electron-app/dist/`:
- `GISELE Setup 2.12.1.exe` — instalador NSIS
- `GISELE-2.12.1-portable.exe` — portátil

**Linux:**
```
cd electron-app
chmod +x build.sh && ./build.sh
```
Saída em `electron-app/dist/`:
- `GISELE-2.12.1.AppImage`
- `gisele_2.12.1_amd64.deb`

## Verificações pós-build

- [ ] Instalador NSIS executa e cria atalho
- [ ] App abre em PNG/GIF com Eta carregado
- [ ] Troca para GeoTIFF mostra o TIF do passo atual
- [ ] "Mostrar mapa" habilita tiles e opacidade
- [ ] Animação completa uma vez (cache populado)
- [ ] Animação 2ª volta é fluida
- [ ] Volta para PNG/GIF mostra a imagem PNG
- [ ] Configurar > Exportar/Importar funciona
- [ ] Portátil (sem instalação) abre normalmente

## Pendências conhecidas

- Pasta local com varredura (webkitdirectory) — feature solicitada, não implementada
- Identidade visual GISELE (brand/) ainda não conectada ao app (favicon/manifest/ícone Electron) —