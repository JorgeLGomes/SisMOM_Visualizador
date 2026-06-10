# POC — amostragem por ponto via range-read (/vsicurl)

**Data:** 2026-06-10 · Fase 1 (validação) + POC do `/v1/timeseries/point`
**Objetivo:** ler **só o tile do ponto** (HTTP range request) em vez de baixar o TIF inteiro,
para acelerar as ferramentas por ponto (série/evolução temporal, perfil vertical, SkewT).

## Resultado do teste local (mecanismo provado)

GeoTIFF sintético **tiled (128) + deflate + predictor=3**, 1024×768, ~2,6 MiB, servido por HTTP
com suporte a Range. Amostragem por `/vsicurl/` (mesma lógica do `_dl_sample_tif`):

| ponto | valor esperado | vsicurl | bytes lidos | % do arquivo |
|---|---|---|---|---|
| j=200 i=300 | -22.089 | **-22.089** | 80 KiB | **3.1%** |
| j=10 i=1000 | 47.025 | **47.025** | 64 KiB | **2.5%** |
| j=700 i=50 | 34.576 | **34.576** | 64 KiB | **2.5%** |
| j=383 i=765 | 5.186 | **5.186** | 80 KiB | **3.1%** |

- Valores **idênticos** ao array (paridade total).
- Cada ponto leu **2,5–3,1%** do arquivo (header + 1 tile), via HTTP **206**.
- Fora do bbox → `None` sem baixar nada (0 byte).

**Conclusão:** o mecanismo funciona e, com range requests, uma série de N passos passa de
"N arquivos inteiros" para "N × ~3%" de tráfego. Onde mais pesa: SkewT e perfis verticais.

## Não testado aqui (e por quê)

O sandbox **bloqueia o FTP do CPTEC** por allowlist (`blocked-by-allowlist`), então a validação
contra `ftp1.cptec.inpe.br` precisa rodar na **máquina do helper**. Script pronto para isso:
`electron-app/python-helper/poc_vsicurl_validate.py`.

## Como validar e usar (na sua máquina)

1. **Validar range no servidor real (decide tudo):**
   ```
   cd electron-app/python-helper
   python3 poc_vsicurl_validate.py "https://ftp1.cptec.inpe.br/pesquisa/SisMOM/sismom_fig/Figuras_Eta/saida/tif/2026060600/ZGEO/ZGEO_50hPa_2026060600.tif"
   ```
   - "RANGE SUPORTADO" + amostra correta → seguir.
   - "RANGE NAO detectado" → o /vsicurl baixaria tudo; gere COG e/ou sirva por host com range.

2. **Aplicar o POC no endpoint (aditivo, com backup):**
   ```
   python3 poc_vsicurl_patch.py            # gera server.py.bak
   # reinicie o helper
   ```
   - Adiciona o campo `use_vsicurl` ao `POST /v1/timeseries/point`. Padrão `false` → nada muda.
   - `use_vsicurl:true` → amostra por range-read (`_dl_sample_tif`), em paralelo.
   - A resposta passa a trazer `sampler` ("vsicurl" | "full-download") e `elapsed_seconds`.
   - Rollback: `python3 poc_vsicurl_patch.py --revert`.

3. **Benchmark A/B:** mesmo payload do frontend, comparar `elapsed_seconds` com `use_vsicurl`
   false vs true (mesmo ponto, ~120 passos).

## Arquivos entregues

- `electron-app/python-helper/poc_vsicurl_patch.py` — aplica/reverte o POC no `server.py`.
- `electron-app/python-helper/poc_vsicurl_validate.py` — valida range + vsicurl no dado real.
- `docs/AVALIACAO_microservico_ponto.md` — avaliação arquitetural completa (todas as ferramentas).

## Próximos passos (após validar o range no dado real)

- **Fase 2:** confirmar o ganho de tempo no benchmark real (série ~120 passos).
- **Fase 3:** generalizar para `/v1/point/series` (atende série, **perfil vertical** e **SkewT** —
  só muda a lista de itens: variar passo p/ tempo, nível p/ vertical) e **fazer o wiring no frontend**
  dessas ferramentas (com fallback JS quando o helper estiver offline).
- **Fase 4:** `/v1/line/sample` (janela do bbox) p/ perfil ao longo da linha e corte vertical.
- **Dado:** gerar COG (tiled + overviews + PREDICTOR=3) para minimizar os range reads.

---

## `/v1/point/series` — endpoint genérico (pronto e TESTADO)

Patch independente: `electron-app/python-helper/point_series_patch.py`
(aplica/reverte; usa o `_dl_sample_tif` que já existe; não depende do POC anterior).

**Ideia:** o frontend manda a **lista de itens** (cada um = 1 URL) + o ponto. Variando os
campos, a MESMA rota atende as três ferramentas:

```jsonc
// Série / evolução temporal — variam o 'passo'
{ "lat": -23.5, "lon": -46.6, "parallel_limit": 8,
  "items": [ {"url": "...T2M_...0600.tif", "passo": 6,  "rodada": "2026060600"},
             {"url": "...T2M_...1200.tif", "passo": 12, "rodada": "2026060600"} ] }

// Perfil vertical — variam o 'nivel'
{ "lat": -23.5, "lon": -46.6,
  "items": [ {"url": "...ZGEO_50hPa_...tif",  "nivel": "50",  "var": "ZGEO"},
             {"url": "...ZGEO_500hPa_...tif", "nivel": "500", "var": "ZGEO"} ] }

// SkewT-LogP — variam 'var' (T, Td) x 'nivel' (+ 1 item 2D de superfície p/ PSLC)
{ "lat": -23.5, "lon": -46.6,
  "items": [ {"url": "...TEMP_850hPa_...tif", "nivel": "850", "var": "T"},
             {"url": "...UR_850hPa_...tif",   "nivel": "850", "var": "Td"} ] }
```

**Resposta** (eco dos campos + valor; ordem preservada por `idx`):
```jsonc
{ "sampler": "vsicurl", "count": N, "fetched": N, "failed": 0, "elapsed_seconds": 0.x,
  "samples": [ {"idx":0, "passo":6, "nivel":null, "var":"ZGEO", "rodada":"2026060600",
                "validade":"2026-06-06 06:00", "value": 18811.5, "error": null}, ... ] }
```

**Teste local (stub patcheado + servidor com range):** 3 níveis amostrados em paralelo →
valores **idênticos** ao esperado; `validade` calculada; ponto fora do bbox → `value: null`
sem falha. `RESULTADO: ENDPOINT /v1/point/series OK`.

**Aplicar:** `python3 point_series_patch.py` (backup `server.py.bak_ps`; reinício do helper).

**Falta (próximo passo):** wiring no frontend — fazer série/perfil-vertical/SkewT montarem a
lista de itens e chamarem `/v1/point/series` quando o helper estiver disponível (fallback JS atual).

---

## Wiring no frontend — SkewT-LogP (APLICADO)

`figuras_SisMOM_v23.html` (+ electron-app, md5 lockstep) — função nova `_skBatchSampleHelper`
e uso em `gtSampleSkewT`:

- Quando o helper está disponível, o SkewT monta a lista de itens (**T e Td × todos os níveis**)
  e faz **uma única** chamada `POST /v1/point/series` (range-read paralelo) em vez de baixar
  ~2×L TIFs inteiros. Os valores voltam num mapa por nível e alimentam o loop existente
  (conversões T/Td, parcela, CAPE/CINE — inalteradas).
- **Fallback automático:** se o helper estiver offline, a chamada falhar, ou o batch não trouxer
  nenhum T válido (`nFinT===0`) → cai no caminho JS atual (`_skSampleVar` por nível). Zero regressão.
- **Chave de escape:** no console, `window.GISELE_SKEWT_HELPER = false` desliga o wiring
  (volta ao JS) — útil se aparecer divergência de paridade.
- A pressão de superfície (PSLC, p/ recortar níveis pela `psfc`) segue no caminho atual (1 amostra).

**Como testar:** reinicie o helper (carrega `/v1/point/series`), recarregue o viewer (Ctrl+Shift+R),
abra um SkewT num ponto. No DevTools → Network deve aparecer **um** POST a `/v1/point/series`
(em vez de vários GET de .tif). Confira se o perfil/CAPE/CINE batem com o modo JS
(`window.GISELE_SKEWT_HELPER=false` para comparar).

**Próximos (mesma primitiva):** perfil vertical por ponto e série/evolução temporal — montar a
lista de itens (variando nível ou passo) e chamar `/v1/point/series` com o mesmo fallback.

---

## Wiring no frontend — Perfil vertical por ponto e Série temporal (APLICADO)

`figuras_SisMOM_v23.html` (+ electron-app, md5 lockstep). Novo helper genérico reutilizável
`_gtPointSeriesValues(urls, lat, lon)` (POST `/v1/point/series`, alinha valores por `idx`,
fallback se helper off / falha / sem finito).

- **Perfil vertical por ponto** (`_gtSampleSourceVProfile`): monta a lista de URLs (1 por nível)
  e amostra todos num **único** range-read via `/v1/point/series`. Fallback JS por nível mantido.
  Usa o endpoint que você **já aplicou** (`point_series_patch.py`).
- **Série temporal por ponto** (`gtPyHelper.sampleTimeSeries` → `/v1/timeseries/point`): passa a
  enviar **`use_vsicurl: true`** no corpo. Com o `poc_vsicurl_patch.py` aplicado no server, vira
  range-read; **sem** ele, o campo é ignorado (full-download) — sem quebrar.
- **Escape comum:** `window.GISELE_POINTSERIES = false` no console desliga o wiring do perfil
  vertical e da série (volta ao caminho atual). (SkewT usa `window.GISELE_SKEWT_HELPER = false`.)

### Para a série temporal usar range-read, aplique TAMBÉM no server:
```
cd electron-app/python-helper
python3 poc_vsicurl_patch.py     # adiciona use_vsicurl ao /v1/timeseries/point
# reinicie o helper
```

### Estado do wiring por ferramenta
| Ferramenta | Endpoint | Server patch necessário | Status |
|---|---|---|---|
| SkewT-LogP | /v1/point/series | point_series_patch.py | ✅ aplicado |
| Perfil vertical por ponto | /v1/point/series | point_series_patch.py | ✅ aplicado |
| Série temporal por ponto | /v1/timeseries/point (use_vsicurl) | poc_vsicurl_patch.py | ✅ frontend / aplicar server |

**Teste:** reinicie o helper, recarregue o viewer (Ctrl+Shift+R). No DevTools → Network:
perfil vertical deve mostrar **um** POST `/v1/point/series`; série temporal, **um** POST
`/v1/timeseries/point` com `use_vsicurl:true` no corpo e `sampler:"vsicurl"` na resposta.

---

## Corte vertical ao longo da linha — `/v1/line/sample` (estratégia de janela)

**Server** (`line_sample_patch.py`, independente): novo `POST /v1/line/sample` + `_dl_sample_line`.
Para cada item (raster de um nível), faz **UMA leitura janelada** (`/vsicurl` + `rasterio.windows`)
cobrindo o *bounding box* da linha e amostra os N pontos dela localmente. Resultado: **L leituras
por passo** (L = níveis) em vez de L×N. Corpo: `{ items:[{url,nivel,...}], points:[[lat,lon],...] }`
(pontos já densificados pelo frontend); resposta ecoa `nivel/var` + `values` (alinhado a points).

- **Teste local (paridade):** corte em 3 níveis sobre uma linha de 120 pontos comparado com a
  leitura cheia (`rasterio src.sample`): **maxdiff = 0.000000**, pontos fora do bbox viram `null`
  corretamente. `LINE_SAMPLE OK`. (Numa linha que cruza quase todo o domínio a janela ≈ arquivo
  inteiro; em linhas regionais a janela é uma fração.)

**Frontend** (`figuras_SisMOM_v23.html`, md5 lockstep): helper `_gtLineSampleValues(items, pts)` +
wiring em `gtSampleCrossSection` — monta 1 item por nível e faz **uma** chamada `/v1/line/sample`;
fallback JS por nível mantido. Escape: `window.GISELE_POINTSERIES = false`.

### Aplicar no server
```
cd electron-app/python-helper
python3 line_sample_patch.py     # adiciona /v1/line/sample (backup server.py.bak_ls)
# reinicie o helper
```

### Estado do wiring (atualizado)
| Ferramenta | Endpoint | Server patch | Status |
|---|---|---|---|
| SkewT-LogP | /v1/point/series | point_series_patch.py | ✅ |
| Perfil vertical por ponto | /v1/point/series | point_series_patch.py | ✅ |
| Série temporal por ponto | /v1/timeseries/point (use_vsicurl) | poc_vsicurl_patch.py | ✅ frontend / aplicar server |
| **Corte vertical na linha** | **/v1/line/sample** | **line_sample_patch.py** | ✅ frontend / aplicar server |

> **Pré-requisito de tudo:** instalar **`orjson`** no Python do helper (`python -m pip install orjson`),
> senão o helper devolve 500 em todas as rotas.

**Ainda fora:** perfil (não-vertical) ao longo da linha e evolução temporal do perfil vertical —
mesmas primitivas (`/v1/line/sample` para a linha; `/v1/point/series` variando passo para a evolução).
