# Avaliação — reusar o micro-serviço de download (ponto/janela) nas ferramentas por ponto

**Data:** 2026-06-10 · **Contexto:** v2.15.0
**Pergunta:** usar a estrutura do micro-serviço de download (recorte de **região** e **ponto** do TIF)
para que as ferramentas que consomem dado em ponto acionem essa leitura janelada e plotem a
evolução temporal / perfis, em vez de baixar o TIF inteiro.

---

## 1. Conclusão executiva

**É viável e recomendável.** O micro-serviço já tem exatamente as duas primitivas necessárias,
lendo **apenas os bytes do(s) tile(s)** do ponto/janela via *HTTP range request* (`/vsicurl/`),
sem baixar o arquivo inteiro:

- **`_dl_sample_tif(url, [lat,lon])`** — amostra 1 ponto (`rasterio.open('/vsicurl/'+url).sample(...)`).
- **`_dl_clip_tif(url, target, bbox=[W,S,E,N])`** — recorta uma janela (leitura janelada `rasterio.windows`).

Hoje as ferramentas por ponto fazem o **oposto**: baixam o **TIF inteiro** (no cliente via
`_gtFetchAndDecode`, ou no helper via `_fetch_and_sample` → `_fetch_one`) só para ler **um pixel**.
Trocar isso pela leitura janelada reduz o tráfego por amostra de "arquivo inteiro" para "1 tile + header"
(tipicamente **<5%** do arquivo), e mantém o resultado idêntico.

**A frase do usuário está correta:** *toda série é uma requisição por ponto repetida nos passos/níveis.*
A mesma primitiva (`_dl_sample_tif`) serve, variando apenas a lista de URLs (passos no tempo, níveis na
vertical) e a coordenada.

**Pré-requisito crítico (validar antes de tudo):** o servidor de dados precisa suportar
**range requests** (HTTP 206 / `Accept-Ranges: bytes`). Se suportar, o ganho é enorme. Se **não**
suportar, o `/vsicurl/` cai para baixar o arquivo inteiro — sem ganho (mas sem quebrar). Ver §4.

---

## 2. Onde estamos hoje (gargalo)

| Ferramenta | Caminho atual | Custo por amostra |
|---|---|---|
| Série temporal por ponto | helper `/v1/timeseries/point` → `_fetch_and_sample` (baixa TIF inteiro + decode + 1 pixel) | 1 TIF inteiro / passo |
| Evolução temporal do perfil | cliente: `_gtFetchAndDecode` por (nível, passo) | 1 TIF inteiro / (nível×passo) |
| Perfil vertical por ponto | cliente: `_gtFetchAndDecode` por nível | 1 TIF inteiro / nível |
| Corte vertical / perfil ao longo de linha | cliente/helper: TIF inteiro por (nível, passo) | 1 TIF inteiro / camada |
| **SkewT-LogP** | cliente: `_skSampleVar` → `_gtFetchAndDecode` por nível (T e Td) | ~2×L TIFs inteiros / sondagem |

O SkewT e os perfis verticais são os mais penalizados: baixam **dezenas de TIFs inteiros** para ler
**um pixel em cada**.

---

## 3. Avaliação por ferramenta

Legenda: ⭐⭐⭐ encaixe perfeito · ⭐⭐ bom (com estratégia de janela) · nota de cuidado.

### 3.1 Evolução temporal por ponto / Série temporal — ⭐⭐⭐
- N passos × 1 ponto → **N leituras de ponto** (`_dl_sample_tif`) em paralelo.
- É o caso mais direto e de maior retorno. **Plano:** trocar o sampler interno de
  `/v1/timeseries/point` por `_dl_sample_tif` (mantendo a API que o frontend já usa).
- Bônus: a "evolução temporal do perfil" (nível × tempo) é só o produto cartesiano
  (L níveis × N passos) das mesmas leituras de ponto.

### 3.2 Perfil vertical por ponto — ⭐⭐⭐
- L níveis (= L URLs) × 1 ponto → **L leituras de ponto**. Substitui L downloads inteiros.

### 3.3 SkewT-LogP — ⭐⭐⭐
- T e Td em L níveis num ponto → ~**2L leituras de ponto** (uma por nível-arquivo).
- Maior ganho relativo (hoje baixa ~2L arquivos inteiros). Cuidado: o SkewT também usa
  variáveis de **superfície** (PSLC para o nível-base) — basta mais 1 leitura de ponto 2D.

### 3.4 Evolução ao longo de uma linha (perfil ao longo da linha) — ⭐⭐
- Uma linha = K pontos. Duas estratégias:
  - **Por ponto:** K leituras de ponto por passo (simples, mas K range reads).
  - **Por janela (recomendado p/ linhas longas):** 1 leitura **janelada** (`_dl_clip_tif`) do
    *bounding box* da linha por passo, e amostra os K pontos localmente. **1 range read / passo**
    em vez de K. Melhor quando o bbox da linha é pequeno/médio.
- **Heurística:** se a área do bbox da linha ≲ X% do raster → janela; se muito grande → fatiar
  em janelas ou cair para por-ponto. Decisão de implementação.

### 3.5 Perfil vertical ao longo da linha (corte vertical) — ⭐⭐
- L níveis × K pontos. Melhor caminho: **1 janela por (nível, passo)** cobrindo a linha,
  amostrando os K pontos dela → **L range reads / passo** (vs L×K pontos ou L downloads inteiros).

---

## 4. Pré-requisito crítico: range requests (validar primeiro)

O ganho inteiro depende do servidor de dados responder a **HTTP Range**. Teste rápido (no host do helper):

```bash
URL="https://<host>/.../arquivo.tif"
# 1) o servidor aceita range?
curl -sI -H "Range: bytes=0-1023" "$URL" | grep -iE "accept-ranges|content-range|^HTTP"
#    Esperado: "HTTP/.. 206 Partial Content" e/ou "Content-Range: bytes 0-1023/..."
# 2) o GDAL consegue amostrar só o tile do ponto?
python3 - <<'PY'
import rasterio
url="https://<host>/.../arquivo.tif"
with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                  CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff",
                  CPL_DEBUG="ON"):           # CPL_DEBUG mostra os range gets
    with rasterio.open("/vsicurl/"+url) as s:
        print("tiled:", s.profile.get("tiled"), "block:", s.block_shapes[:1])
        print(list(s.sample([(s.bounds.left+0.1, s.bounds.bottom+0.1)])))
PY
```

- **206 + poucos GETs pequenos** → seguir com confiança.
- **200 / baixa tudo** → servidor não suporta range; o ganho some. Mitigações: (a) servir os TIFs
  por um host com range (o próprio helper pode reexpor via `/v1/tile/fetch`), (b) priorizar o
  **cache de pontos** (§6) para não repetir downloads, (c) **gerar COG** (abaixo).

**Recomendação de dado:** gerar os GeoTIFFs como **COG** (tiled + *overviews* + layout IFD-first):
```bash
gdal_translate in.tif out.tif -of COG \
  -co COMPRESS=DEFLATE -co PREDICTOR=3 -co BLOCKSIZE=512 -co OVERVIEWS=AUTO
```
COG minimiza os range reads (cabeçalho compacto no início) e habilita leitura por *overview* para
linha/região (downsample barato). Já estamos migrando para `PREDICTOR=3` (v2.15) — encaixa aqui.

---

## 5. Arquitetura recomendada

**Princípio mantido:** o **frontend é a fonte da verdade das URLs** (monta via `montarURL`), o helper
só executa leitura + amostragem. Reusar os blocos já existentes.

Novos endpoints (finos, sobre `_dl_sample_tif`/`_dl_clip_tif`):

- `POST /v1/point/series` — corpo: `{ items:[{url, passo, nivel?, rodada?}], point:[lat,lon],
  nodata_extras? }` → leituras de ponto em paralelo (Semaphore) → `[{rodada, validade, passo,
  nivel, valor}]`. **Cobre série temporal, perfil vertical e SkewT** (o frontend só muda a lista de
  itens: variar `passo` p/ tempo, variar `nivel` p/ vertical).
- `POST /v1/line/sample` — corpo: `{ items:[{url, passo, nivel?}], line:[[lat,lon]...], npts }` →
  por item, 1 janela do bbox da linha + amostragem dos pontos → `[{...por ponto da linha}]`.
  **Cobre perfil ao longo da linha e corte vertical.**

Reaproveitamento direto: `/v1/timeseries/point` pode passar a chamar `_dl_sample_tif` no lugar de
`_fetch_and_sample` (mesma resposta), virando um caso particular de `/v1/point/series`.

**Wiring no frontend:** os fluxos por ponto já constroem as listas de URL. Roteamento novo:
1. se `gtPyHelper.available` → chamar o endpoint novo;
2. senão → manter o caminho atual em JS (`_gtFetchAndDecode` + sample) como **fallback** transparente.

---

## 6. Cache e concorrência

- O cache em disco atual guarda **TIFs inteiros por URL** — bom para o mapa/animação, mas não para
  leitura janelada. Adicionar um **cache de amostras** leve: chave `(url, lat, lon)` (e `(url,bbox)`),
  valor = float/array pequeno. Evita repetir range reads ao reabrir o mesmo ponto/linha.
- `/vsicurl` reabre o cabeçalho por arquivo; para muitos passos, **paralelizar** (asyncio + Semaphore,
  como já em `/v1/timeseries/point`) e **limitar** a concorrência para não sobrecarregar o FTP do CPTEC.
- `GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR` e `CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif,.tiff` já estão
  setados nas duas funções — manter.

---

## 7. Riscos / cuidados

- **Range não suportado** → sem ganho (mitigações em §4). **Validar antes de implementar.**
- **Georreferenciamento:** `_dl_sample_tif` usa `src.bounds`/`src.sample` (lê o georref do TIF). Tem
  que estar **correto** no arquivo — lembrar dos problemas recentes de bbox/predictor/`yrev`. Conferir
  que `rasterio` e o sampler do viewer concordam no mesmo ponto (teste de paridade).
- **NoData / undef:** `_dl_sample_tif` trata `src.nodata` e NaN; passar também os `nodata_extras`
  (ex.: `-2.56e33`, `-9999`) como no `_fetch_and_sample`.
- **Latência por range read:** cada leitura tem overhead de RTT; ganho real vem da **paralelização**
  e do **COG** (menos GETs por arquivo).
- **Paridade de resultado:** garantir que o valor amostrado pelo helper == valor do caminho JS atual
  (mesma convenção de pixel/centro, mesma interpolação — hoje *nearest*).

---

## 8. Plano de implementação faseado

1. **Validação (1 tarefa):** rodar o teste de range/COG do §4 contra um TIF real do CPTEC. Decide tudo.
2. **POC série temporal:** trocar o sampler de `/v1/timeseries/point` por `_dl_sample_tif`; medir
   tempo vs hoje num ponto com ~120 passos. Fallback JS intacto.
3. **`/v1/point/series` genérico:** atende série, **perfil vertical** e **SkewT** (só muda a lista).
   Wire no frontend dessas três ferramentas.
4. **`/v1/line/sample` (janela):** perfil ao longo da linha + corte vertical.
5. **Cache de amostras** `(url,lat,lon)`/`(url,bbox)`.
6. **(Dado) COG + overviews** na geração — ganho extra e leitura por overview p/ linha/região.

> Ordem por retorno: **1 → 2/3 (ponto: série, vertical, SkewT) → 4 (linha) → 5/6**.

---

### Resumo de viabilidade

| Ferramenta | Encaixe | Estratégia |
|---|---|---|
| Série temporal / evolução por ponto | ⭐⭐⭐ | `_dl_sample_tif`, paralelo |
| Evolução temporal do perfil (nível×tempo) | ⭐⭐⭐ | idem, produto níveis×passos |
| Perfil vertical por ponto | ⭐⭐⭐ | `_dl_sample_tif` por nível |
| SkewT-LogP | ⭐⭐⭐ | `_dl_sample_tif` por nível (T, Td) + 1 ponto 2D (PSLC) |
| Perfil ao longo da linha | ⭐⭐ | `_dl_clip_tif` (janela do bbox) + amostra pontos |
| Corte vertical (perfil vertical na linha) | ⭐⭐ | 1 janela por (nível, passo) |

**Bloqueador único a confirmar:** suporte a **HTTP range requests** no servidor de dados. Tudo o mais
já existe no micro-serviço.
