# gisele_ts — Cliente Python para extração de série temporal GISELE

Cliente Python que envelopa o endpoint `/v1/timeseries/point` do helper GISELE. Permite extrair séries temporais de modelos numéricos (Eta, BAM, GFS, MERGE, ...) num ponto (lat, lon) diretamente de scripts, notebooks ou pipelines.

## Instalação

```bash
# Em modo desenvolvimento (recomendado)
cd api-client
pip install -e .

# Dependências em runtime
pip install requests pandas   # pandas opcional, para .dataframe()
```

## Pré-requisitos

O helper Python precisa estar rodando. Opções:

**1) Standalone (recomendado para uso fora do Electron):**
```bash
cd electron-app/python-helper
pip install -r requirements.txt
python server.py --port 8000
# helper agora em http://127.0.0.1:8000
```

**2) Subprocesso do Electron** (porta default 8765, gerenciada pelo app GISELE rodando):
- Abra o app GISELE — ele inicia o helper automaticamente.
- Verifique no badge inferior direito: ⚡ Python (ativo) ou JS only (offline).

## Uso

### Como biblioteca (Python)

```python
from gisele_ts import GiseleClient, MODELS, VARIABLES

client = GiseleClient(base_url="http://127.0.0.1:8000")

# Health check
print(client.health())

# Extração de TS num ponto
ts = client.timeseries(
    modelo=MODELS["Eta_5km"],
    variavel=VARIABLES["PREC"],
    data_rodada="2026053000",   # YYYYMMDDHH UTC
    lat=-20.0, lon=-45.0,
    passo_min=6, passo_max=72,  # opcional: 1ª e última hora de previsão
    parallel_limit=16,
)

print(f"{ts.layer_name}: {len(ts)} passos, {ts.valid_count()} válidos")
for s in ts:
    print(f"  +{s.passo_h:3d}h  {s.time_utc}  {s.value}")

# Conversões
ts.to_csv("eta_prec.csv")
df = ts.dataframe()        # pandas DataFrame
print(df.head())
print(ts.to_json(indent=2))
```

### Multi-ponto

```python
points = [(-20, -45), (-3.1, -60), (-23.5, -46.6)]
results = client.timeseries_multi(
    modelo=MODELS["Eta_5km"],
    variavel=VARIABLES["PREC"],
    data_rodada="2026053000",
    points=points,
)
for ts in results:
    print(ts.lat, ts.lon, ts.valid_count(), "passos válidos")
```

### Saída GeoJSON (compatível QGIS)

```python
gj = client.timeseries_geojson(
    modelo=MODELS["BAM"],
    variavel=VARIABLES["T2M"],
    data_rodada="2026053000",
    lat=-3.1, lon=-60.0,
)
import json
with open("bam_t2m.geojson", "w") as f:
    json.dump(gj, f)
```

### Modelo customizado

Se o modelo não está no registry, monte o dict manualmente:

```python
custom = {
    "nome": "Meu modelo",
    "url_path": "https://meu-servidor/dados/{yyyy}/{mm}/{dd}/{hh}/",
    "file_name": "var_{prefixo}_{yyyymmddhh}_{F%3}.tif",
    "extensao": ".tif", "extensao_tif": ".tif",
    "same_url_for_tif": True, "same_name_for_tif": True,
    "escopo1": "", "escopo2": "", "maxPassos": 240,
}
ts = client.timeseries(modelo=custom, variavel=VARIABLES["PREC"],
                       data_rodada="2026053000", lat=-20, lon=-45)
```

Placeholders aceitos nos templates: `{yyyy} {mm} {dd} {hh} {yyyymmddhh} {escopo1} {escopo2} {prefixo} {N} {N%4} {F} {F%3} {fct} {ext}`.

## CLI

```bash
# Listar modelos / variáveis registrados
python -m gisele_ts --list-models
python -m gisele_ts --list-vars

# Health check
python -m gisele_ts --url http://127.0.0.1:8000 --health

# Extrair e salvar CSV
python -m gisele_ts \
    --url http://127.0.0.1:8000 \
    --model Eta_5km --var PREC \
    --date 2026053000 \
    --lat -20.0 --lon -45.0 \
    --passo-min 6 --passo-max 120 \
    -o eta_prec.csv

# JSON na saída padrão
python -m gisele_ts --model BAM --var T2M --date 2026053000 --lat -3.1 --lon -60.0
```

## Estrutura da resposta

```python
TimeSeries(
    samples=[TimeSeriesSample(idx, passo_h, time_utc, value), ...],
    layer_name="Eta 5 km · Precipitacao",
    lat=-20.0, lon=-45.0,
    run_date_utc="2026-05-30T00:00:00+00:00",
    elapsed_seconds=2.347,
    fetched=48, failed=0,
)
```

Cada sample:
- `idx`: índice 1-based
- `passo_h`: horas de previsão (ex: 24 = +24h)
- `time_utc`: validade ISO 8601 (rodada + passo_h)
- `value`: valor amostrado no pixel (ou `None` se NoData)

## Performance

- O helper usa **HTTP/2 + conexão pool reutilizada + asyncio.Semaphore** para fetches paralelos
- **Cache em disco** (SHA-256 por URL, LRU 500MB) — fetches repetidos em segunda chamada são instantâneos
- **Cache decoded em memória** (256 rasters LRU) — múltiplas amostragens no mesmo arquivo são instantâneas
- Típico: 48 passos do Eta 5km em ~2-5s na primeira corrida, <0.5s nas subsequentes

## Endpoints subjacentes

| Endpoint | Descrição |
|---|---|
| `GET /health` | Status do helper + stats de cache |
| `POST /v1/timeseries/point` | Série temporal num ponto (este client) |
| `POST /v1/timeseries/point/geojson` | Idem, saída GeoJSON FeatureCollection |
| `POST /v1/profile/line` | Perfil ao longo de polilinha |
| `POST /v1/calc/temporal` | Calculadora temporal (somas/médias entre passos) |
| `GET /v1/render/png` | Render PNG server-side com paleta |
| `GET /v1/tile/fetch` | Proxy de tile (com cache) |

Para detalhes completos: `electron-app/python-helper/server.py`.

## Licença

MIT — mesma do GISELE.
