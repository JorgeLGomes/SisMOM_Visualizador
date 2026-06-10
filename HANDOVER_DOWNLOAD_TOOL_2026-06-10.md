# GISELE — Ferramenta de download de dados (micro-serviço local) · 2026-06-10

> Sessão posterior à do predictor-3/cache (ver `HANDOVER_SESSAO_2026-06-10.md`).
> **Feature nova:** ferramenta de micro-serviço para **baixar os dados para a máquina
> local**, como opção de uso da plataforma (offline/auditoria).

**Versão:** v2.15.0 → **v2.16.0** · helper Python **0.6.0 → 0.7.0**
**Build marker:** `20260610-predictor3-cache` → **`20260610-form-campos`**
**MD5 final:** `c80ad6c365a448c4babf6bee1652fe57`
**Refinamentos finais:** CSVs do ponto POR VARIÁVEL (2D juntas em `*_2D.csv`, uma
coluna por variável; cada 3D em arquivo próprio, uma coluna por nível na ordem da
requisição — `_dl_series_write`/`gravar_wide`); resumo por variável ok/sem
valor/falhas no job, na janela e na API (`pt_stats`); formulário com bbox em 4
caixas N/W/E/S (layout bússola), ponto em caixas Lat/Lon, seção de níveis visível
apenas com variável 3D selecionada (`dlNivWrap`), checkboxes iniciando todos
desmarcados e formato padrão GeoTIFF.
**MD5 do HTML (raiz == electron-app):** `7ddc09d154bb1e90b22e13cb177549b1`
**Linhas do HTML:** 25641
**CSV do ponto reorganizado (formato wide, pedido do usuário):**
- variáveis **2D**: UM arquivo `serie_ponto_<lat>_<lon>_2D.csv` — colunas
  `rodada,validade,VAR1,VAR2,…` (ordem = ordem das variáveis na requisição);
- cada variável **3D**: arquivo próprio `…_<VAR>.csv` — colunas
  `rodada,validade,<nivel1>,<nivel2>,…` (ordem = níveis explicitados na requisição);
- requisições mistas seguem os dois padrões; a mescla entre rodadas continua
  (dedup por rodada+validade+coluna, ordenação por validade, regravação atômica).
Implementado em `_dl_merge_wide`/`_dl_series_write` (helper, que agora recebe
`rodada` por item e calcula a validade) e `gravar_wide`/`extrair_ponto` (API gerada).
Testado nos dois caminhos com 2D+3D (níveis 1000/850) e duas rodadas acumulando.
**Helper:** VERSION **0.8.0**. Guarda de versão no frontend: ponto/bbox com helper
antigo em execução agora é **bloqueado com alerta** (antes o helper antigo ignorava
o campo `point` desconhecido e baixava os TIFs inteiros silenciosamente — caso real
observado: 131 TIFs salvos em vez do CSV).

## 3.5 Requisição de apenas UM PONTO (série temporal em CSV)

1. **Formulário:** campo opcional **"Apenas um ponto lat,lon"** (ex.: `-23.5,-46.6`),
   mutuamente exclusivo com bbox; exige formato GeoTIFF (ou Ambos). Em vez de salvar
   os arquivos, o job amostra cada `.tif` na coordenada e grava
   `serie_ponto_<lat>_<lon>.csv` (colunas `variavel,nivel,passo_h,valor,arquivo,url`).
2. **Helper:** `DownloadStartRequest.point` + `DownloadItemReq.{var,passo,nivel}` +
   `_dl_sample_tif()` (rasterio `src.sample` via `/vsicurl` — bytes mínimos em COG;
   nodata/fora da cobertura → vazio). PNGs no job são pulados.
3. **API gerada:** `--ponto=lat,lon` (default = `CONFIG.ponto` do formulário; o shim
   do argv cobre `--bbox` e `--ponto` com valores negativos sem `=`), funções
   `amostrar_ponto()`/`extrair_ponto()`, itens com metadados `(url, rel, var, passo,
   nivel)`. Testado: 3 validades → CSV ordenado com 3 amostras; idem pelo helper.
4. **Linha do tempo em UM ÚNICO ARQUIVO (`serie-unica`):** o CSV ganhou colunas
   `validade` (rodada+passo, `YYYY-MM-DD HH:00`) e `rodada`, e passou a ser
   **mesclado** a cada execução (`_dl_serie_merge` no helper / `gravar_serie` na API):
   dedup por rodada+variável+nível+passo, ordenação por validade, regravação atômica.
   A pasta do modo ponto é **estável** (`<modelo>_serie_ponto/`, sem a rodada no
   nome) — rodadas sucessivas (ex.: agendadas) acumulam no mesmo
   `serie_ponto_<lat>_<lon>.csv`. Testado: 2 execuções (rodadas 0600/0700) →
   6 amostras acumuladas no mesmo arquivo, sem duplicatas ao repetir.
**Fix argparse:** `--bbox -50,-35,-30,5` falhava (argparse lia o valor negativo como
opção); o script gerado agora pré-processa o argv juntando em `--bbox=VALOR` — as
duas formas funcionam. Workaround p/ scripts já gerados: usar `--bbox=-50,...`.
**UX fix:** toast subiu de z-index 500 → 2000 (ficava ATRÁS da janela flutuante de
download, z-index 1000); erros do "Iniciar download" agora também aparecem num
**alerta inline dentro da janela** (`dlFormAlert`), com re-sonda automática do helper
no clique e dica específica quando o helper em execução é versão antiga (HTTP 404).

---

## 1. O que a ferramenta faz

1. Botão **"⬇ Dados"** no cabeçalho abre um **pop-up** (`modalDownload`) com a lista do
   que está cadastrado nas configurações: **🗄 Bases de dados** (`basesDados` — queimadas,
   METAR etc.; `kind:'points'` é omitido por ser local) e **🌐 Modelos** (`modelos`).
2. Ao selecionar o item, aparece um **formulário** para definir o **diretório de destino**
   na máquina. O botão **📁 Escolher…** abre o diálogo nativo do SO no Electron; no
   **navegador** (file:// ou http) abre um **navegador de diretórios inline** servido
   pelo helper (`GET /v1/fs/browse`): atalhos 🏠 Início e 💽 drives (Windows), ⬆ Acima,
   lista de subpastas clicáveis e **"✓ Usar esta pasta"**. Para modelos há ainda: **rodada (AAAAMMDDHH)**, **formato**
   (PNG / GeoTIFF / ambos), **intervalo de passos (h)** e **seleção de variáveis**
   (variáveis 3D iteram os níveis de `m.niveis`). Mostra estimativa de nº de arquivos.
3. O download roda no **helper Python** (job assíncrono, 6 conexões paralelas), com
   barra de progresso por polling (800 ms), contagem de falhas, **cancelamento** e, ao
   final, **📂 Abrir pasta**. Cada job grava um **`_manifesto.json`** (auditoria/offline).

Filosofia preservada: **o frontend é a fonte da verdade** — monta as URLs com
`montarURL()` (PNG/TIF, com `_buildMTifModel`/`gtDeriveTifUrl` para rotas TIF) e
`gtBaseUrl()` (bases; METAR ganha `?format=json&bbox=`), e envia `{url, filename}`.
O backend só baixa, grava atomicamente (`.part` → rename) e relata progresso.

## 2. Mudanças por arquivo

| Arquivo | Mudança |
|---|---|
| `figuras_SisMOM_v23.html` (raiz **e** electron-app, md5 idêntico) | Botão `#btnDownloadData` no header; modal `#modalDownload` (antes do `modalHelp`); módulo JS `dl*` no fim da IIFE (antes do wire do `gtBootstrapConfigFromFile`): `dlOpenModal/dlRenderList/dlRenderForm/dlBuildModelItems/dlBuildBaseItems/dlStart/dlPollOnce/dlCancel/dlRenderJob`. Dir persistido em `localStorage['gisele_dl_dir']`. |
| `electron-app/python-helper/server.py` | VERSION 0.7.0. Novo bloco "Micro-serviço de DOWNLOAD": `POST /v1/download/validate_dir`, `POST /v1/download/start` (job_id; máx. 5000 itens), `GET /v1/download/status`, `POST /v1/download/cancel`. Sanitização `_dl_safe_relpath` (sem `..`/absolutos — testado), gravação atômica, `_manifesto.json`, eviction de jobs antigos (30). **`GET /v1/fs/browse`** — lista subpastas/drives/home (só leitura) para o seletor de destino no navegador. |
| `electron-app/main.js` | IPC `gisele-fs:choose-dir` (`dialog.showOpenDialog` openDirectory+createDirectory) e `gisele-fs:open-dir` (`shell.openPath`). |
| `electron-app/preload.js` | `window.GISELE_FS = { chooseDir, openDir }`. |
| `electron-app/package.json` | `"version": "2.16.0"`. |

## 3. Validação executada

- JS: extração dos 5 blocos `<script>` + `vm.Script` **OK** + minificação **terser OK**.
- `md5sum` raiz == electron-app (`d858eaae…`).
- Python: `ast.parse` OK; teste E2E real (uvicorn + http.server local):
  health v0.7.0 → validate_dir cria/valida → job com 5 itens = **4 baixados,
  1 falha HTTP 404 corretamente reportada**, bytes íntegros (`cmp`), manifesto gravado,
  **path traversal `../../../etc/evil.bin` contido dentro do destino**, cancel idempotente.
- Dependência: o helper usa o `httpx` já existente; nada novo em `requirements.txt`.

## 3.1 Conflito de porta com `tools/servir_dados` (corrigido)

O usuário rodava o **servidor local de dados** (`tools/servir_dados`) na porta **8765**
— a mesma do helper Python. O viewer sondava `:8765/health`, recebia **404** do
servidor estático e concluía "micro-serviço indisponível". Correções:

1. **`tools/servir_dados`** (py/js/sh/bat/README): porta padrão **8765 → 8770**, com
   nota no README de que 8765 é reservada ao helper. **Atenção:** templates de modelo
   que apontavam para `http://localhost:8765/...` devem passar a usar `:8770`.
2. **`electron-app/python-spawner.js`**: implementado o fallback de porta que o
   comentário já prometia — `findFreePort` (bind-test via `net.createServer`) tenta
   **8765..8768** antes de spawnar.
3. **Viewer (`gtPyHelper.refresh`)**: o fallback do browser standalone agora **varre
   127.0.0.1:8765..8768** e confirma a identidade (`h.service === 'gisele-python-helper'`),
   ignorando outros serviços na porta.

Teste real: servir_dados ocupando 8765 (404 no /health) + helper em 8766 → sonda
descarta 8765 e conecta em 8766; `/v1/fs/browse` respondendo.

## 3.2 Iniciador do helper para uso no navegador (`tools/iniciar_helper/`)

No navegador (file://) o helper não sobe sozinho como no Electron. Criados
**`iniciar_helper.bat`** (Windows; cria `.venv-helper` na primeira execução e instala
`requirements.txt`), **`iniciar_helper.sh`** (Linux/macOS) e `README.md` com a tabela
de portas (helper 8765–8768 · servir_dados 8770). `.venv-helper/` adicionado ao
`.gitignore`. O aviso do pop-up "⬇ Baixar dados" agora instrui exatamente isso
(app Electron OU `tools\iniciar_helper\iniciar_helper.bat` + "↻ Verificar de novo").

## 3.3 Melhorias do formulário (sessão `20260610-dl-api3d`)

1. **Seções "Variáveis 2D" e "Variáveis 3D"** no formulário (botões todas/nenhuma por
   seção). Para as 3D, os **níveis disponíveis** (`m.niveis`, hPa) são explicitados e
   selecionáveis (`.dl-nivel`); 3D sem nível selecionado/cadastrado é ignorada no
   download (com aviso quando o modelo não tem níveis cadastrados).
2. **Janela flutuante:** `#modalDownload` não escurece nem bloqueia a plataforma
   (backdrop com `pointer-events:none`), o diálogo é `position:fixed` e **arrastável
   pelo cabeçalho**. A visualização continua utilizável com o pop-up aberto.
3. **Botão "🐍 API"** no rodapé do formulário: gera um **script Python standalone**
   (`gisele_api_<id>.py`) com a seleção do usuário embutida (CONFIG JSON: modelo,
   rodada, variáveis 2D/3D, níveis, passos, formato, destino) para **consumo
   automatizado** — porta fiel do `montarURL()` (rodada no caminho, validade no nome,
   `{N}/{F}/{nivel}/{fct}/{passo4}` etc.), download paralelo (`ThreadPoolExecutor`),
   `_manifesto.json` e CLI `--rodada/--dest/--workers/--listar`. A caixa oferece
   **📋 Copiar**, **⬇ baixar o .py** e **⬇ requirements.txt** (`requests`).
   Template em `DL_PY_TEMPLATE` (String.raw); geração em `dlBuildPyCode()`.
   **Testado de verdade:** script gerado com modelo fictício 2D+3D → `--listar` com
   14 URLs corretas (níveis 1000/850, png+tif) e download real com manifesto.
   **Fix `nivelfix`:** o CONFIG agora exporta `file_name_tif_3d` e o `montar_url` do
   script segue a precedência do `_buildMTifModel` (3D-TIF > TIF > 3D > 2D, com
   auto-`{ext}` no `file_name_tif`) — URLs 3D TIF batem com o padrão real do FTP
   (`ZGEO_50hPa_2026060600.tif`); verificado com config equivalente ao Eta 3km.

## 3.4 Recorte espacial de GeoTIFF/COG — bbox (`20260610-dl-cogclip`)

Os TIFs do projeto são **COG**, então dá para trazer **só a fração desejada** por
HTTP range requests (GDAL lê o cabeçalho/índice e busca apenas os tiles da janela):

1. **Formulário:** campo opcional **"Recorte bbox W,S,E,N"** (graus; ex.:
   `-60,-35,-30,5`). Vale só para `.tif` — PNG vem sempre inteiro.
2. **Helper (`server.py`):** `DownloadStartRequest.bbox` + `_dl_clip_tif()` — leitura
   janelada `rasterio` sobre `/vsicurl/`, executada em `asyncio.to_thread`, gravação
   `.part`→rename, saída GTiff deflate com `window_transform` correto.
3. **API Python gerada:** `recortar_cog()` + CLI `--bbox W,S,E,N` (default =
   `CONFIG.bbox` do formulário); `requirements.txt` ganhou `rasterio` (marcado como
   opcional, só p/ --bbox). Manifesto registra o bbox usado.

**Teste real (sandbox):** COG 720×360 (0,5°, tiled 256, ~1,2 MB) servido com range
requests (RangeHTTPServer) → bbox −60,−35,−30,5 → recorte **61×81 px, bounds
(−60,−35.5,−29.5,5), 17,6 KB** — tanto pela API gerada quanto pelo job do helper.

## 4. Pendências

- **Commit pendente** (junto com o delta predictor-3/cache da sessão anterior).
- Reiniciar o helper Python para carregar os endpoints novos.
- Possíveis evoluções: retomar downloads interrompidos (range requests), agendamento
  de espelhamento periódico, e leitura dos dados baixados pelo viewer em modo offline
  (apontar `url_path` para `file://`/pasta local).
