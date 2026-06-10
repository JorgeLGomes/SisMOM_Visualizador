# GISELE — Handover da sessão 2026-06-10

> Documento focado **nesta sessão** (continuação do v2.14.0). Para o panorama geral do
> projeto veja `HANDOVER_GISELE.md`. Objetivo: permitir que **outro modelo/assistente**
> continue o trabalho sem perda de contexto.

**Repositório:** `C:\Projetos\Visualizador`
**Versão:** v2.14.0 → **v2.15.0**
**Build marker:** `20260609-skewt-cape` → **`20260610-predictor3-cache`**
**MD5 do HTML (raiz == electron-app):** `303df5f67462215afd06e65054a048e2`
**Linhas do HTML:** 24541

**Regra de ouro:** todo patch no HTML vale para os DOIS arquivos
(`figuras_SisMOM_v23.html` raiz **e** `electron-app/figuras_SisMOM_v23.html`); manter md5 idêntico.
Validar com `vm.Script`/`node --check` + teste de minificação (terser) + `md5sum` dos dois.

---

## 1. Resumo executivo

Dois problemas foram investigados e resolvidos:

1. **Decodificação de GeoTIFF float com *floating-point predictor* (predictor=3).** O decodificador
   só tratava predictor 1 e 2. TIFs float32 com predictor=3 caíam sem reconstrução → campo
   distorcido com "deslocamento horizontal que muda com o campo" (dependente dos dados).
   **Implementado `_pred3Row`** (TIFF TechNote 3), com round-trip **verificado (erro 0)**.

2. **Causa raiz do "campo continua errado mesmo após regerar os dados": CACHE.** Os arquivos
   foram regerados na **mesma URL**, e tanto o **cache em disco do helper Python**
   (`~/.gisele/tiff-cache/<sha256 da URL>.bin`, indexado só pela URL) quanto o **cache do
   navegador** (`Cache-Control: public, max-age=86400`) continuavam servindo os **bytes antigos
   (predictor=2)**. Por isso o decode nem rodava de novo (o console não atualizava ao trocar de
   campo). **Implementada a correção** (botão "🔄 Atualizar dados" + `no-cache` no helper).

---

## 2. Mudanças no código (o que foi alterado e onde)

### 2.1 Decodificador GeoTIFF — predictor 3 (`SisMOM_GeoTIFF.decodeTIFF`)
Função aninhada **`_pred3Row(buf, lineOff, lineW)`** (logo após `_pred2Row`, ~linha 9375).
Algoritmo (decode do float predictor): acumula bytes na horizontal com `stride = samplesPerPixel`
e depois **reordena os planos de bytes** (MSB-first no arquivo) para a ordem de leitura do float,
respeitando o byte-order (`little`). Ativada nos dois caminhos:
- **tiles** (~9396): `else if (predictor === 3) { for row in tileH: _pred3Row(seg, row*tileW*bpp, tileW); }`
- **strips** (~9421): `else if (predictor === 3) { for y in height: _pred3Row(raw, y*width*bpp, width); }`

Como `decodeTIFF` é serializada para o Web Worker via `decodeTIFF.toString()` (e `_pred3Row` é
**aninhada** nela), a correção propaga automaticamente para o pool de workers.

**Verificação:** round-trip encode→decode de uma linha float com erro máximo **0** (script de
teste descartável). Zero risco de regressão para predictor 1/2 (branch novo só dispara em `=== 3`).

### 2.2 Log de diagnóstico do decode (enriquecido)
`console.log('[GISELE/TIFF] decode', {...})` (~linha 9329) agora inclui
`tileW, tileH, nSeg, planar` além de `w, h, bps, sampleFormat, comp, predictor, tiled, rowsPerStrip,
spp, little`. Foi decisivo para comparar Eta (512×512, predictor=2 inteiro — correto) vs
Global-BESM_AS (64×64, float com sample_minmax absurdo — errado).

### 2.3 Correção de cache (a que de fato resolveu o sintoma do usuário)
**Viewer (`figuras_SisMOM_v23.html`):**
- `let _gtForceFresh = false;` — quando true, o `fetch` usa `cache: 'reload'` (fura o cache do navegador).
- `_gtFetchAndDecode`: os dois `fetch` (proxy e fallback direto) passam
  `{ cache: _gtForceFresh ? 'reload' : 'default' }`.
- `_gtTsRasterClear()` — limpa o cache dedicado de série (`_gtTsRasterCache` + `_gtTsRasterBytes=0`).
- **`gtForceFreshData()`** (também exposta em `window.gtForceFreshData`): (1) limpa caches em memória
  do viewer — `gtCacheClear()`, `_gtTsRasterClear()`, `_gtBitmapCache`; (2) `POST /cache/clear` no
  helper; (3) com `_gtForceFresh=true`, re-busca todos os `lastLoadedURL[ap]` via
  `carregarGeoTIFFParaSlot` e re-busca as `gtExtraLayers` por `source.url`; (4) toast de status.
- **Botão "🔄 Atualizar dados (limpar cache)"** (`id=gtTreeRefreshData`) no nó **Camadas**, logo abaixo
  de "＋ Adicionar Modelo"; handler em ~linha 23494 (após o wire do `gtTreeAddModel`).

**Helper (`electron-app/python-helper/server.py`):**
- `Cache-Control: public, max-age=86400` → **`no-cache`** nas 4 respostas de dados
  (`/v1/tile/fetch` HIT/MISS e `/v1/render/png` ×2). O helper é local (loopback), então re-servir é
  barato; isso elimina a obsolescência de 24h no navegador. O cache **em disco** do helper continua
  (performance), mas agora é a única camada — e é furável pelo botão / `POST /cache/clear`.

> **Importante:** a mudança no `server.py` exige **reiniciar o helper Python** para valer.

---

## 3. Como o próximo modelo deve testar

1. Regerar os TIFs (já com `cog.predictor: 3` no YAML — ver `config_glob2eta.yaml`).
2. **Reiniciar o helper Python** (carrega o `server.py` com `no-cache`).
3. No viewer: clicar **"🔄 Atualizar dados"** no nó Camadas (ou `Ctrl+Shift+R` na 1ª vez).
4. Abrir o campo: o console deve logar `[GISELE/TIFF] decode … predictor: 3` (novo arquivo) e o
   campo deve cair correto e suave.
5. Conferência rápida: `sample_minmax` plausível para a variável (ex.: pressão ~ 950–1030 hPa).

Comando manual equivalente ao botão (Linux do helper):
```bash
rm -rf ~/.gisele/tiff-cache/*   # ou: curl -X POST http://127.0.0.1:8765/cache/clear
```

---

## 4. Pendências / pontos em aberto

- **"Andes defasado" (georreferenciamento):** após o predictor/cache resolvidos, o campo de
  pressão ficou suave e globalmente coerente, mas o usuário relatou que a assinatura dos Andes
  parece levemente deslocada. **A confirmar** se é (a) deslocamento constante de ~½–1 célula
  (questão de registro **PixelIsPoint vs PixelIsArea** / meio-pixel — o decode aplica
  `halfX=sx/2`/`halfY=sy/2` quando `pixelIsPoint`, ver ~linha 9481), (b) cisalhamento (variável),
  ou (c) apenas a **resolução grossa** do Global-BESM_AS (grade 1,875° ≈ 200 km, que posiciona os
  Andes na coluna de grade mais próxima — não seria bug). Caracterizar antes de mexer.
- **Seletor automático de predictor (não implementado):** se aparecerem TIFs float com
  `predictor=2` **mal rotulados** (bytes codificados como float-predictor), a abordagem limpa é
  regerar com `PREDICTOR=3`. Se for preciso lidar com arquivos legados sem regerar, a alternativa
  é decodificar dos dois jeitos e escolher o campo **espacialmente mais suave** (custa decode duplo).
  **Decisão tomada nesta sessão:** corrigir na geração (predictor=3), que é o caminho correto.
- **Commit pendente:** o delta desta sessão (predictor=3, log, cache-fix, versão, docs) **não foi
  commitado**. Atualizar/rodar o script de commit no Windows.

---

## 5. Mapa rápido de funções/arquivos tocados

| Item | Arquivo | Âncora |
|---|---|---|
| `_pred3Row` | `figuras_SisMOM_v23.html` | ~9375 (aninhada em `decodeTIFF`) |
| Branches predictor 3 | idem | ~9396 (tile) / ~9421 (strip) |
| Log de decode enriquecido | idem | ~9329 |
| `_gtForceFresh` / `gtForceFreshData` / `_gtTsRasterClear` | idem | antes do pool de workers (~9778) |
| `fetch(..., {cache})` | idem | `_gtFetchAndDecode` (~9861 e ~9866) |
| Botão "Atualizar dados" (HTML) | idem | nó Camadas (~2333) |
| Wire do botão | idem | ~23494 |
| Build marker | idem | ~9118 |
| `Cache-Control: no-cache` | `electron-app/python-helper/server.py` | `tile_fetch` (1116/1132) + `render/png` (1252/1297) |
| Versão 2.15.0 | `electron-app/package.json` | `"version"` |

---

## 6. Conceitos-chave reaproveitados (referência)

- **Predictors TIFF:** 1=nenhum, 2=diferenciação horizontal (inteiro; `_pred2Row` faz acúmulo
  uint32 para 32-bit), 3=floating-point predictor (`_pred3Row`). GDAL recomenda **PREDICTOR=3**
  para Float32/64.
- **Caches do projeto:** viewer tem 3 (display `_gtDecodedCache`, série dedicada
  `_gtTsRasterCache` ~1 GB, bitmaps suavizados `_gtBitmapCache`); helper tem cache em **disco**
  (`~/.gisele/tiff-cache`) + decodificado em memória. Todos por **URL** — regerar no mesmo caminho
  exige furar cache.
- **Worker de decode:** `__workerSrc` concatena `decodeTIFF.toString()`; funções **aninhadas**
  propagam, funções **externas** precisam ser concatenadas explicitamente.

---

## 7. Continuação da sessão — range-read (/vsicurl) + bandas (v2.16.0)

**MD5 do HTML (lockstep):** `6622c41436f1f89930202b88b3ab34d4` · **linhas:** 25899 ·
**build:** `20260610-form-campos` · **versão:** 2.16.0

### 7.1 Micro-serviço de amostragem por range-read
Em vez de baixar o TIF inteiro para ler um ponto, lê só o(s) tile(s) via `/vsicurl/` (HTTP range).
Validado contra o CPTEC (Apache: 206 + Accept-Ranges + CORS `*`). Documentação detalhada e POC com
testes em `docs/AVALIACAO_microservico_ponto.md` e `docs/POC_vsicurl_resultados.md`.

Endpoints (patches independentes em `electron-app/python-helper/`, com backup `.bak*` e `--revert`):

| Patch | Endpoint | Função-núcleo | Atende |
|---|---|---|---|
| `poc_vsicurl_patch.py` | `/v1/timeseries/point` (campo `use_vsicurl`) | `_dl_sample_tif` | série temporal |
| `point_series_patch.py` | `POST /v1/point/series` | `_dl_sample_tif` (paralelo) | série, perfil vertical, SkewT |
| `line_sample_patch.py` | `POST /v1/line/sample` | `_dl_sample_line` (janela por nível) | corte vertical |

`poc_vsicurl_validate.py` valida o range/tiling de um TIF real (rodar no host do helper).

### 7.2 Wiring no frontend (HTML, lockstep)
- SkewT: `_skBatchSampleHelper` em `gtSampleSkewT` → 1 POST `/v1/point/series` (T e Td × níveis).
- Perfil vertical por ponto: `_gtPointSeriesValues` (helper genérico) em `_gtSampleSourceVProfile`.
- Série temporal: `use_vsicurl:true` no POST `/v1/timeseries/point` de `gtPyHelper.sampleTimeSeries`.
- Corte vertical: `_gtLineSampleValues` em `gtSampleCrossSection` → 1 POST `/v1/line/sample`.
- Todos com **fallback JS**. Escapes: `window.GISELE_POINTSERIES=false`, `window.GISELE_SKEWT_HELPER=false`.

### 7.3 Bandas (filled contour) na config da camada
- Sub-painel `gtCfgBandsPanel` (após o select Sombreado, ~linha 22865): Mín/Máx (+auto), modo
  **Nº de bandas (auto)** | **intervalos explícitos**; grava na escala (gt.min/max) + `gtContourCount`/
  `gtContourLevels`; chama `gtUpdateBandLevels` + `gtDesenharColorbar` + `gtRerenderAllRasters`.
- `_gtApplyRasterModeStatics`: `rasterSmooth = (gtRasterMode === 'smooth')` (bandas/pixel sem smoothing).
- `aplicarPaleta` (~9734): no modo bandas (`_bandsActive`), interpola os DADOS (bilinear, fator ~640px
  no menor lado, até 16×) ANTES de classificar → bordas suaves (filled contour) com cor chapada.

### 7.4 Pré-requisitos / operação do helper
- Instalar **`orjson`** (`python -m pip install orjson`) — sem ele o helper dá **500** em tudo (ORJSONResponse).
- Garantir que quem ocupa a **porta 8765** é o `server.py` patchado (matar processo anterior / fechar
  GISELE empacotado, cujo helper embutido é o código antigo).

### 7.5 Bandas — RESOLVIDO
O "pixelado" relatado no modo bandas era o **service worker** (`sw.js`) servindo o **HTML antigo** em
cache — os patches de filled-contour não estavam carregando. Após *Application → Service Workers →
Unregister* + *Clear site data* + Ctrl+Shift+R, as bandas funcionam como desejado: cor chapada por banda
com bordas suaves (filled contour), controláveis por Mín/Máx + Nº de bandas (auto) ou intervalos
explícitos. **Lição de operação:** depois de qualquer patch no HTML, limpar o service worker para a
versão nova carregar (um Ctrl+Shift+R comum não basta). (Melhoria opcional, não solicitada: desenhar a
colorbar em blocos discretos para casar com o campo.)
