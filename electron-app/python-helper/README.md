# gisele-python-helper

Servidor Python local que acelera operações pesadas do GISELE (extração temporal, perfil de linha, calculadora temporal).

Roda como **subprocess do Electron** em `127.0.0.1:8765`. Quando online, o frontend GISELE o usa automaticamente; quando offline, cai no fallback JS transparentemente.

## Status

| Endpoint | Função | Speedup vs JS |
|---|---|---|
| `GET /health` | Status do serviço | — |
| `POST /v1/timeseries/point` | Extração temporal num ponto (fetch paralelo de N TIFs) | ~10× para 72 passos |
| `POST /v1/timeseries/point/geojson` | Idem, saída GeoJSON FeatureCollection | ~10× |
| `POST /v1/calc/temporal` | Calculadora temporal: `sum/mean/max/min(t_i..t_j)` | ~6× |
| `POST /v1/profile/line` | Perfil ao longo de polilinha sobre 1 TIF | ~3× |

## Rodar localmente (dev)

```bash
cd electron-app/python-helper
pip install -r requirements.txt
python server.py --port 8765
# em outro terminal:
curl http://127.0.0.1:8765/health | jq
```

O Electron faz isso automaticamente: ao iniciar, `python-spawner.js` spawna `python server.py` (modo dev) ou `gisele-python-helper.exe` (modo packaged). Para desabilitar: `electron . --no-python-helper`.

## Empacotar como .exe (PyInstaller)

```bash
cd electron-app/python-helper
pip install pyinstaller
pyinstaller --onefile --name gisele-python-helper server.py \
  --hidden-import=rasterio --hidden-import=rasterio.sample \
  --hidden-import=rasterio._shim --hidden-import=rasterio.vrt \
  --hidden-import=rasterio._features --collect-submodules rasterio
# Saída: dist/gisele-python-helper.exe
```

O `electron-builder` (via `extraResources` em `package.json`) copia `python-helper/dist/` para `resources/python-helper/` no app empacotado.

## Arquitetura

```
Browser (figuras_SisMOM_v23.html)
   │
   │ fetch http://127.0.0.1:8765/v1/...
   ▼
gisele-python-helper (FastAPI + uvicorn)
   │
   ├─ url_builder.py   ← porta de montarURL() do JS
   │
   ├─ sampler.py       ← rasterio + numpy (decode + sample no ponto)
   │
   └─ server.py        ← endpoints, fetch paralelo via httpx.AsyncClient
                          │
                          └─ FTP CPTEC: N fetches concorrentes
                                         (semáforo controla concurrency)
```

## Filosofia

- **Stateless.** O frontend é a fonte da verdade. Envia model_config + variavel_config em cada request.
- **Convenção idêntica ao frontend.** bbox `{minX, minY, maxX, maxY}`, row top-down (j=0 → latMax).
- **Fallback transparente.** Frontend tenta Python; se falhar (timeout, processo morto, erro de rede), cai no JS sem o usuário perceber.
- **Loopback only.** Bind em `127.0.0.1`, nunca em `0.0.0.0`.
