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
- Identidade visual GISELE (brand/) ainda não conectada ao app (favicon/manifest/ícone Electron) — pendente
- Paleta/min/max default por variável (persistência) — Fase 3 pendente
- Controles de paleta por painel Mi no header — Fase 4 pendente
- Assinatura digital do .exe — requer certificado pago (~ USD 200/ano), distribuído sem assinatura por ora
- Web Worker para `aplicarPaleta` — 1ª passada da animação ainda é CPU-bound em modelos grandes (Eta)

## Histórico de versões

- **2.12.1** (2026-06-02): raster GeoTIFF interpolado + sombreado Suavizado/Bandas/Pixel + bandas por nível.
- **2.12.0** (2026-06-01): Base de dados (KML/GeoJSON) + menu Monitoramento (Queimadas INPE).
- **2.11.x** (2026-06-01): desenho no PNG + fix MERGE multipainel + série temporal consolidada + caneta de tela.
- **2.10.0** (2026-05-31): Cidades brasileiras (por UF) + cliente Python `gisele_ts`.
- **2.9.0** (2026-05-31): multi-painel (sync/lock/replicação) + polígonos do usuário + gráficos interativos.
- **2.6.0–2.8.0** (2026-05-29/30): Calculadora Temporal, Exportar/Importar GeoJSON e Shapefile, helper Python, perf de contornos.
- **2.4.0–2.5.0** (2026-05-28): árvore ERMA + Configuração da Camada + calculadora dupla + Miscelâneas.
- **2.1.0–2.3.0** (2026-05-28): ferramentas de medição, série temporal, vídeo MP4, mapa-base por modelo.
- **2.0.0** (2026-05-28): Modo GeoTIFF completo, multi-painel com mapa, cache, paletas extras, calculadora.
- **1.0.0** (2026-05-25): Versão inicial PNG/GIF apenas.
