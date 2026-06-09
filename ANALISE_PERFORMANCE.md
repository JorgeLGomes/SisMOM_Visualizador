# GISELE — Análise de Performance e Propostas de Melhoria

**Projeto:** GISELE (Visualizador de modelos meteorológicos CPTEC/INPE) · v2.13.0
**Data:** 08/06/2026
**Escopo analisado:** frontend (`figuras_SisMOM_v23.html`), backend Python (`electron-app/python-helper/server.py`), empacotamento Electron e `api-client`.

---

## Status de implementação (08/06/2026)

| Item | Status | Observação |
|------|--------|-----------|
| **P1.2** — cliente httpx global | ✅ Aplicado | `server.py`: `lifespan` + `_shared_http()` reusam o pool em 4 rotas (timeseries point/polygon, calc/temporal, profile/line). `py_compile` OK. |
| **P1.3** — minificação no build | ✅ Aplicado | `scripts/minify-html.js` + integração em `build.bat`/`build.sh`/`build-mac.sh` e `package.json`. **Medido: 1803 KB → 1325 KB (−26,5%)**, sem `mangle` (worker via `toString()` preservado) e blocos JSON intactos. |
| **P2.2** — service worker | ✅ Aplicado | `sw.js` cache-first criado e empacotado (electron-builder + standalone). Corrige o registro 404. |
| **P1.1** — remover GeoJSON inline | ⛔ **Não aplicado** | Quebraria o modo arquivo único (`file://`), que é o uso primário (COMO-USAR.txt). Ver nota abaixo. |
| **P2.3** — orjson no backend | ✅ Aplicado | `ORJSONResponse` como `default_response_class` + `orjson==3.10.7` em requirements e `--hidden-import=orjson` no PyInstaller. `py_compile` OK. |
| **P2.1** — animação via PNG do servidor | ✅ Aplicado (opt-in) | Liga/desliga clicando no badge "⚡ Python". Desligado por padrão. Terceiriza a aplicação de paleta (`renderTilePNG`) só para rasters crus, paletas padrão, sem clip/band/flip; fallback local. Cores ~aproximadas (colormaps matplotlib). |
| **HTML truncado** (cidades_br) | ✅ Corrigido | Reconstruído com os 240 registros de `miscelaneas/cidades_brasil.geojson` e tags `</script></body></html>` fechadas. |

### Por que o P1.1 foi mantido (não aplicado)

Ao implementar, três fatos mudaram o cálculo de risco do P1.1:

1. **O modo `file://` é primário.** COMO-USAR.txt e os launchers (`SisMOM.bat`/`.sh`) abrem o HTML direto no navegador. Sobre `file://`, `fetch('miscelaneas/...')` é **bloqueado por CORS** — o GeoJSON inline é justamente o que faz as camadas (corais/plataformas/cidades) funcionarem nesse modo. Removê-lo quebraria a "Opção 1 — uso imediato".
2. **O custo de *startup* do inline é quase nulo.** O código faz `JSON.parse` **sob demanda** (só ao ativar a camada), não no carregamento. O ganho que o relatório supôs ("sempre parseados") não existe.
3. **As coordenadas já estão em 4 casas decimais (~11 m)** — não há ganho fácil em trimar precisão; os 409 KB do corais são volume real de geometria.

A minificação (**P1.3**, já aplicada) cobre o objetivo de "arquivo menor" sem quebrar nada (−26,5% no total). Se no futuro o uso `file://` for descontinuado (somente Electron/servidor HTTP), o P1.1 passa a ser seguro **desde que** `miscelaneas/` seja empacotado.

### ✅ (Resolvido) HTML-fonte truncado

`figuras_SisMOM_v23.html` terminava truncado no meio do bloco JSON de cidades (`gt-misc-data-cidades_br`), sem `</script>` final nem `</body></html>` — a camada "Cidades brasileiras" tinha só 146 de 240 registros (cortada em "Resende"). **Corrigido:** bloco reconstruído com os 240 registros completos de `miscelaneas/cidades_brasil.geojson` e tags de fechamento adicionadas. Os três blocos inline (plataformas/corais/cidades) validados como JSON íntegro.

---

## Resumo executivo

A plataforma **já tem uma base de performance sólida** e bem pensada: pool de Web Workers para decodificar GeoTIFFs em paralelo, caches LRU em memória (display + raster dedicado de até 1 GB), deduplicação de *fetch* em voo, proxy Python local com cache em disco (10 GB) e em RAM, renderização opcional de PNG no servidor e cliente HTTP/2. Não há "erros grosseiros" de arquitetura.

As melhorias abaixo são **incrementais** e focam em três frentes: (1) reduzir o custo de *startup* do frontend, (2) reutilizar conexões no backend e (3) terceirizar mais decodificação para o servidor. Os ganhos maiores e mais baratos estão nos itens **P1**.

---

## Top oportunidades (priorizadas)

| # | Item | Área | Impacto | Esforço |
|---|------|------|---------|---------|
| P1.1 | Remover ~494 KB de GeoJSON inline e carregar sob demanda | Frontend | Alto | Baixo |
| P1.2 | Reutilizar `httpx.AsyncClient` global (lifespan) em vez de criar por requisição | Backend | Alto | Baixo |
| P1.3 | Minificar/gzip o HTML na distribuição | Build | Médio-Alto | Baixo |
| P2.1 | Usar render PNG do servidor para animação (terceirizar decode+paleta) | Front+Back | Alto | Médio |
| P2.2 | Service worker `sw.js` ausente — corrigir ou remover registro | Frontend | Médio | Baixo |
| P2.3 | `orjson` no backend para respostas grandes (séries/polígono) | Backend | Médio | Baixo |
| P3.1 | Auditar `innerHTML`/`querySelectorAll` em laços (delegação + fragmentos) | Frontend | Médio | Médio |
| P3.2 | Evição do cache de disco sem varrer diretório a cada escrita | Backend | Baixo-Médio | Médio |

---

## 1. Frontend (`figuras_SisMOM_v23.html`)

O arquivo é monolítico: **1,8 MB**, ~22.447 linhas, com ~19.800 linhas de JS *inline* analisadas (parse) a cada inicialização.

### P1.1 — GeoJSON embutido e duplicado (ganho rápido, alto)

Ao final do HTML há três blocos `<script type="application/json">` embutidos:

- `corais_br` → **~409 KB**
- `plataformas_br` → ~60 KB
- `cidades_br` → ~25 KB

Total: **~494 KB sempre baixados e parseados**, mesmo que o usuário nunca ative essas camadas. Pior: **os mesmos dados já existem como arquivos** em `miscelaneas/` (`corais_brasil.geojson`, etc.), ou seja, são uma duplicação.

**Proposta:** remover os blocos inline e carregar via `fetch('miscelaneas/<arquivo>.geojson')` **sob demanda**, no clique de ativação da camada (com cache em memória após o primeiro carregamento). A infraestrutura de leitura por `id` (`document.getElementById('gt-misc-data-' + id)`) já existe e pode ser trocada por um *loader* assíncrono. O `corais` em particular é uma camada de nicho que raramente justifica seu custo no *startup*.

**Ganho estimado:** −~490 KB no download e no tempo de parse inicial; *startup* perceptivelmente mais rápido.

### P1.3 — Minificação e compressão na distribuição

O HTML é servido/embarcado sem minificação. Para o build Electron e qualquer *deploy* web:

- **Minificar** HTML+CSS+JS (ex.: `html-minifier-terser`) como passo de build — tipicamente reduz 30–45% antes de gzip.
- Em *deploy* web, garantir **gzip/brotli** no servidor (o `<link rel="preconnect">` para o FTP do INPE já mostra essa preocupação).

Recomendo manter o fonte legível e gerar a versão minificada apenas em `electron-app/` no `prebuild`, preservando o desenvolvimento.

### P2.2 — Service worker referenciado mas inexistente

O `<head>` registra `navigator.serviceWorker.register('sw.js')`, mas **`sw.js` não existe** no projeto. Em *deploy* web isso gera um 404 a cada carga (o registro é silenciosamente ignorado no Electron por usar `file://`).

**Proposta:** ou (a) adicionar um `sw.js` real com *cache-first* para os ativos estáticos (HTML, ícones, `vendor/leaflet.*`, GeoJSON de miscelâneas) — o que dá *startup* quase instantâneo em visitas repetidas no navegador —, ou (b) remover o registro se o alvo é só Electron. A opção (a) é a mais valiosa para uso web/PWA (já há `manifest.webmanifest`).

### P3.1 — Manipulação de DOM

Heurísticas encontradas: **98** atribuições `innerHTML`, **71** `querySelectorAll`, **406** `addEventListener`. Não são problemas por si só, mas valem uma auditoria nos caminhos quentes (montagem de listas/legendas/tabelas e *re-render* durante animação):

- Trocar reconstruções repetidas de listas grandes por **`DocumentFragment`** + uma única inserção.
- **Delegação de eventos** em listas dinâmicas (um listener no container em vez de N nos itens) reduz tanto memória quanto o custo de remontagem.
- Evitar *layout thrashing*: agrupar leituras (`offsetWidth`, `getBoundingClientRect`) separadas das escritas de estilo.

### Pontos já bem resolvidos (manter)

Pool de Workers dimensionado por `hardwareConcurrency` (2–6), *fallback* transparente para a thread principal, cache LRU de display (80) + raster dedicado (1 GB com teto em bytes), dedup de *fetch* em voo, proxy via helper. Boa engenharia — não mexer sem necessidade.

---

## 2. Backend (`electron-app/python-helper/server.py`)

FastAPI + httpx assíncrono, com *fetch* paralelo (`asyncio.gather` + `Semaphore`), offload de CPU para thread pool (`asyncio.to_thread` em máscaras e estatísticas zonais), cache em disco (LRU por `atime`, 10 GB) e cache de decodificados em RAM. Arquitetura muito boa.

### P1.2 — Reaproveitar o cliente HTTP entre requisições (alto, barato)

Cada endpoint cria seu próprio cliente:

```python
async with httpx.AsyncClient(follow_redirects=True, limits=limits, http2=True, ...) as client:
    ...
```

Como o `async with` **fecha o cliente ao fim de cada requisição**, o *pool* de conexões e as sessões HTTP/2 para o servidor do INPE **não são reaproveitados** entre chamadas — paga-se *handshake* TCP/TLS repetido, que é justamente a latência dominante contra o FTP remoto.

**Proposta:** criar **um único `AsyncClient` no `lifespan` do app** (startup/shutdown) e injetá-lo nos endpoints. Mantém HTTP/2 e `keep-alive` vivos entre requisições. É a mudança de melhor relação custo/benefício no backend.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    app.state.client = httpx.AsyncClient(follow_redirects=True, http2=True,
                                         limits=httpx.Limits(max_connections=..., max_keepalive_connections=...))
    yield
    await app.state.client.aclose()

app = FastAPI(lifespan=lifespan)
```

### P2.3 — Serialização JSON

As respostas de série temporal e de polígono podem ser grandes (muitos passos × células). O `json` da stdlib é o gargalo de serialização nesses casos.

**Proposta:** usar **`ORJSONResponse`** (`orjson`) como `default_response_class` do FastAPI. Ganho típico de 2–5× na serialização de respostas grandes, com mudança mínima.

### P3.2 — Evição do cache de disco

`_maybe_evict()` precisa varrer o diretório e ordenar por `atime` para decidir o que remover. Com muitos arquivos no cache de 10 GB, isso pode ficar caro se chamado a cada escrita.

**Proposta:** manter um índice em memória (ou SQLite leve) de `{hash → (tamanho, atime)}` atualizado incrementalmente, e só varrer o disco na inicialização para reconstruir o índice. Reduz a varredura de O(N) por escrita para O(1) amortizado.

### Pontos já bem resolvidos (manter)

`http2=True`, semáforo de concorrência, offload de CPU para threads, *lazy import* do matplotlib (pesado), caches em camadas (disco + RAM decodificada + PNG). Sólido.

---

## 3. Terceirizar mais decodificação para o servidor (P2.1)

Hoje o servidor **já sabe** renderizar PNG a partir do GeoTIFF (`_render_png_from_decoded`, matplotlib Agg + Pillow, com cache de PNG em RAM). O cliente, porém, ainda decodifica o TIFF e aplica a paleta localmente no caminho de exibição/animação.

**Proposta:** no modo animação/série (quando o helper Python está disponível), buscar **PNGs já renderizados pelo servidor** em vez de TIFFs, eliminando do cliente tanto o *decode* quanto a aplicação de paleta. O servidor faz isso uma vez e serve do cache de PNG para todos os passos/clientes.

**Trade-off conhecido:** o comentário em `server.py` indica que hoje a paleta é aplicada no frontend "para byte-identidade". Portanto, isto vale para o **caminho de exibição/animação** (onde fidelidade exata de bytes não é crítica), mantendo o caminho de amostragem/exportação como está. Reduz CPU no cliente e suaviza a animação em máquinas modestas.

---

## 4. Empacotamento / distribuição

- **Minificação no build** (ver P1.3) aplicada só ao artefato Electron/web.
- **`vendor/leaflet.js` (147 KB)** — confirmar se o Leaflet ainda é usado; o caminho de mapa parece usar canvas próprio (`decodeTIFF`/`gtMapCanvas`). Se não for mais referenciado, remover do pacote elimina peso morto.
- Há **muitos `.bat` de commit e `dev/patch_*.py`** na raiz do repositório (não afetam runtime, mas poluem o pacote se incluídos). Confirmar que `build.files` no `package.json` os exclui — atualmente a lista de `files` é explícita, então provavelmente OK; vale checar o `.gitignore`/empacotamento.

---

## Plano sugerido (ordem de execução)

1. **Semana 1 (quick wins):** P1.1 (GeoJSON sob demanda), P1.2 (cliente httpx global), P1.3 (minificação no build), P2.2 (sw.js). Baixo risco, ganho imediato de *startup* e latência.
2. **Semana 2:** P2.3 (orjson), P2.1 (animação via PNG do servidor). Ganho de fluidez e throughput.
3. **Backlog:** P3.1 (auditoria de DOM), P3.2 (índice de cache). Refinamentos de médio prazo.

**Como medir:** registrar antes/depois com `performance.now()` no *startup* do frontend e no `/health` (que já expõe estatísticas de cache e *in-flight* peak) do backend; comparar tempo até o primeiro mapa renderizado e latência média por passo na animação.

---

*Observação: a análise foi estática (leitura de código). Recomenda-se validar os ganhos com profiling em execução real — Performance panel do DevTools no frontend e os contadores já expostos pelo `/health` no backend.*
