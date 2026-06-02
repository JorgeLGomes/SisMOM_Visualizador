# GISELE — Briefing para nova sessão (histórico)

> Documento de transferência de contexto. Cole/anexe no início da próxima sessão (Opus 4.6 ou modelo mais robusto) para continuar de onde paramos.
>
> **Nota (02/06/2026):** documento **histórico** (maio/2026, quando o projeto ainda usava o nome SisMOM). Para o estado atual (v2.12.1, features e arquitetura correntes) consulte sempre o `HANDOVER_GISELE.md`.

---

## 1. Identificação

- **Usuário:** Jorge Luis Gomes (CPTEC/INPE) — jorge.gomes@inpe.br
- **Projeto:** Visualizador de figuras de modelos meteorológicos do CPTEC (FTP)
- **Tipo:** Single-page HTML (~252 KB) com JS embutido (IIFE), empacotável como `.exe` (Windows) e AppImage/`.deb` (Linux) via Electron
- **Repositório:** GitHub (já consolidado, push feito com `--force` na primeira vez)

## 2. Caminhos importantes

| O quê | Onde |
|---|---|
| Pasta de desenvolvimento ativa | `C:\Projetos\Visualizador` (fora do OneDrive) |
| HTML principal (raiz) | `C:\Projetos\Visualizador\figuras_SisMOM_v23.html` |
| HTML embutido no Electron | `C:\Projetos\Visualizador\electron-app\figuras_SisMOM_v23.html` |
| Build config Electron | `C:\Projetos\Visualizador\electron-app\package.json` |
| Main process Electron | `C:\Projetos\Visualizador\electron-app\main.js` |
| Launcher Windows | `SisMOM.bat` (Edge/Chrome `--app`) |
| Launcher Linux | `SisMOM.sh`, `SisMOM.desktop`, `instalar-atalho.sh` |
| Pasta OneDrive (legada) | `C:\Users\jorge\OneDrive\Projetos\SisMOM\2026\Meta4\Visualizador` — **NÃO buildar aqui** (corrompeu `package.json` e ícone) |

**Regra fundamental:** as duas cópias do HTML (raiz e `electron-app/`) devem ficar **idênticas**. Toda alteração é aplicada nas duas em lockstep, geralmente via script Python que faz o mesmo patch nos dois arquivos.

## 3. Arquitetura do app

- Single-file: HTML + CSS + JS dentro de uma IIFE
- Painéis M1..Mn com double-buffering (`buffers[i].active = 'a'|'b'`) e race-cancellation (`activeRequests[i]`)
- Configuração de modelos via `DEFAULT_MODELOS` (5 modelos embutidos: `global`, `MOM6`, `modelo_4` Mom6 Regional, `Eta`, `MERGE`)
- Estado persistido em `localStorage` (painéis, datas, velocidade, config dos modelos, segredo 2FA) e `sessionStorage` (flags de desbloqueio)
- PWA manifest + service worker (skip em `file://`)

### Sistema de placeholders (URLs)

`montarURL` resolve 3 modos no template do path/nome:
1. `prec-0001.png` → sequência relativa ao step
2. `prec024.png` → horas de previsão
3. `prec2026052700.png` → data de validade absoluta

Sintaxe: `{}` (não `[]`). Contexto importante:
- **Path** = data da rodada (condição inicial)
- **Nome** = data de validade
- `Freq=0` ⇒ campo é análise/observação/reanálise → painéis subsequentes seguem a data de **validade** do M1

### Memória por modelo

`lastVarByModel`: ao trocar de modelo num slot, lembra a última variável usada naquele modelo (evita o bug MERGE→Eta com `PREC24` herdado errado).

## 4. 2FA — TOTP RFC 6238

- HMAC-SHA-1 via Web Crypto API
- Base32 encoding, janela ±1 (clock skew)
- Código de recuperação: SHA-256 via `crypto.subtle.digest`
- QR Code: **gerador inline próprio** (ISO/IEC 18004, byte mode, versões 1-40, ECC L/M/Q/H, Reed-Solomon GF(256), 8-mask penalty scoring, BCH(15,5) format info, BCH(18,6) version info)
- **CDN é proibido** — quebra uso offline em Electron (`file://`)
- Segredo em `localStorage` (por-origem). Usuário aceita essa limitação.

### Bug corrigido no QR (não recriar)

`placeFmt` estava com row/col transposto — gerava QR que não era reconhecido. Correção: 1ª cópia desce coluna 8 (linhas 0..5), depois `m[7][8]`, `m[8][8]`, `m[8][7]`, depois `m[8][14-i]` para i=9..15. Indentação interna no IIFE é **8 espaços** (não 4) — patches que erram a indentação falham silenciosamente.

### Dois níveis de desbloqueio (estado atual)

| Estado | Storage | Significado |
|---|---|---|
| Sessão geral | `sessionStorage['sismom_auth_unlocked']` | App aberto, modelos comuns visíveis |
| Modelos protegidos | `sessionStorage['sismom_auth_prot_unlocked']` | Modelos com `requires2FA:true` visíveis |

Funções-chave:
- `pedirCodigoBloqueio(razao, opts)` — `opts.kind = 'session' | 'protected'`
- `submeterCodigoBloqueio` — se `_authKind === 'protected'`, marca os **dois** flags (protegido implica sessão)
- `desbloquearProtegidos()` / `bloquearProtegidos()` — botões dedicados no modal Segurança
- `isModeloAcessivel(id)` — verifica `isProtectedUnlocked()` quando `m.requires2FA`

**Usuário não pode usar bypass `000000`** — rejeitou explicitamente.

## 5. Build / Distribuição

### Windows
```bash
cd C:\Projetos\Visualizador\electron-app
npm install
npm run dist:win    # NSIS + portable, icon.ico
```

### Linux
- **Não buildar AppImage/.deb no Windows nativo** (faltam mksquashfs etc.). Usar WSL ou Docker.
- `package.json` precisa: `homepage`, `author.email`, `build.linux.maintainer`
- `linux.desktop` schema exige propriedades dentro de `entry`: `"desktop": { "entry": { "Name": "...", "Comment": "..." } }`

```bash
# Em WSL:
cd /mnt/c/Projetos/Visualizador/electron-app
npm run dist:linux
```

### GitHub Actions
- Matrix: `windows-latest`, `ubuntu-latest`
- Workflow: `.github/workflows/release.yml`
- LICENSE: MIT

## 6. Padrões de trabalho que o usuário espera

1. **Editar HTML pela UI** — não no editor de texto (já truncou o arquivo 2x; final `</body></html>` perdido; restaurado da cópia electron-app)
2. **Patches Python que tocam as duas cópias** — qualquer mudança no HTML aplicada em `figuras_SisMOM_v23.html` (raiz) **e** `electron-app/figuras_SisMOM_v23.html`, com validação `node --check` ou equivalente, e diff/identidade verificada
3. **Sem `bullet 1` e `bullet 2`** em soluções de problemas no README (preferência editorial)
4. **Logo SisMOM** aplicada em todos os pontos, círculo inteiro (sem cortar)
5. **MERGE em maiúsculas** (não `merge`)
6. **Início da rodada sempre setado** — se data atual indisponível, recua dia a dia até achar; data inicial padrão = hoje no painel M1
7. **Modal de configuração** abre em modo somente-leitura; botão Editar libera campos
8. **Painel flutuante de info** só aparece com clique no botão `?` (não auto no hover)

## 7. Defaults atuais

- 1 painel aberto (M1)
- Modelo: `Eta` · 3 km
- Data: data local do sistema (corrente)
- Modelos embutidos: `global`, `MOM6`, `modelo_4`, `Eta`, `MERGE`

## 8. Bugs já resolvidos (não revisitar a menos que regrida)

- OneDrive corrompendo arquivos → projeto movido para `C:\Projetos\Visualizador`
- `electron-builder` schema `linux.desktop` → wrapped em `entry`
- mksquashfs ausente no Windows → documentado uso de WSL
- `.deb` faltando metadados → adicionados `homepage`/`author.email`/`maintainer`
- `git push` rejeitado por README remoto → `--force` na primeira vez
- MERGE→Eta imagem travada → `clearImageBuffer(slotIdx)` + `lastVarByModel`
- QR não escaneável → `placeFmt` com row/col corretos (validado round-trip 16/16)
- Patch falhando por indentação 4 em vez de 8 espaços → atenção a contexto IIFE
- Modelos protegidos compartilhando flag de sessão → flag separado `sismom_auth_prot_unlocked`

## 9. Estado atual / último commit pendente

**Última mudança aplicada:** **fix: sidebar GeoTIFF estava na esquerda**. O `.modal-backdrop` tem `inset: 0` (= left:0 entre outros). Minha regra `.gt-sidebar` sobrescrevia top/right/bottom/width mas o `left: 0` herdado esticava o elemento até a borda esquerda da tela, cobrindo a sidebar PNG. Correção: `left: auto !important` + `!important` em top/right/bottom/width para anular tudo do `.modal-backdrop`. Também desligado `backdrop-filter` herdado.

**Antes disso:** **painel direito como sidebar + seleção de painel ativo**. Em modo gtiff, o `#modalGeoTIFF` ganha classe `.gt-sidebar`: `position: fixed; right: 0; top: 60px; bottom: 0; width: 340px` — vira sidebar lateral fixa (sem backdrop, sem header de modal). `body.gt-mode-active main.main { padding-right: 340px }` reserva espaço pros painéis Mi. Cada `.map-box` recebe um botão flutuante **"Painel Mi"** no canto superior direito; clicar marca o painel como **ativo** (borda ciano `.gt-active`). Novo estado `gtActivePanel` rastreia, `gtSlotDecoded[i]` cacheia o decoded por slot. Trocar de painel ativo via `gtSelectPanel(idx)` copia o decoded cacheado para `gtLastDecoded` e atualiza info/colorbar/colorbars overlay do painel direito. +4 KB no HTML (417 → 421).

**Antes disso:** **10 paletas científicas extras**. Adicionadas: **Plasma, Inferno, Magma, Cividis** (matplotlib); **RdYlBu, Spectral, BrBG** (ColorBrewer divergentes); **Seismic, Coolwarm** (anomalias); **Terrain, Ocean** (topográficas). Total: **16 paletas**. Select organizado em `<optgroup>`: Sequenciais (matplotlib) / Sequenciais clássicas / Divergentes (anomalia) / Topográficas. +3 KB no HTML (414 → 417). **Pendente (próximas fases)**: paleta/min/max por variável (salvar default), controles de paleta no header de cada painel Mi.

**Antes disso:** **multi-painel no modo GeoTIFF (Fase 2)**. O modo gtiff agora mantém os painéis Mi visíveis (1/2/3/4 layouts funcionam igual ao PNG). O dashboard de 1 painel grande (modal #modalGeoTIFF inline) deixa de ser ativado automaticamente; continua acessível pelo botão "Abrir GeoTIFF local" do header. `carregarImagem(slotIdx, url)` ganhou intercepção quando `appMode === 'gtiff'`: deriva URL para TIF (`url_path_tif`/`file_name_tif` se setado, senão substituição `/fig/`→`/geotiff/` e `.png`→`.tif`) e delega para `carregarGeoTIFFParaSlot` (que já existia e empurra blob URL pro `<img>` do painel). Cada painel Mi tem seu próprio canvas overlay independente.

**Antes disso:** **rotas distintas PNG/TIF + disponibilidade por modelo e variável**. Schema do modelo ganhou: `tem_png` (default true), `tem_tif` (default false), `extensao_tif` (default .tif), `url_path_tif`, `file_name_tif`, `same_url_for_tif` (default true), `same_name_for_tif` (default true). Cada variável tem `disp_png` (default true) e `disp_tif` (default false). Modal de config tem checkboxes "PNG/GIF" e "TIF" no cabeçalho dos formatos, campos URL/nome TIF (escondidos quando "usar o mesmo do PNG"). Tabela de variáveis: Esc1/Esc2 viraram checkboxes PNG/TIF. `gtLoadFromState` usa `url_path_tif/file_name_tif` quando setados (e cai pra derivação .png→.tif quando não); toolbar GeoTIFF lista só modelos com `tem_tif` e variáveis com `disp_tif`. +6 KB no HTML (406 → 412).

**Antes disso:** **zoom preservado durante animação GeoTIFF**. Bug: a cada step da animação, `gtLoadFromState` chamava `_gtMap.fitTo(bbox)`, resetando o zoom/pan do usuário. Correção: nova variável `_gtLastFitBbox` + helper `_bboxEqual(a, b)` que compara bboxes com tolerância `1e-6`. `fitTo` só é executado se a bbox da nova camada diferir da última aplicada — ou seja, troca de modelo/variável → re-fit; mesma camada, passo seguinte → preserva zoom. Aplicado nos dois caminhos (FTP via `gtLoadFromState` e file picker local).

**Antes disso:** **passos recalculados ao trocar modelo na toolbar GeoTIFF**. Bug: trocar de modelo na toolbar não atualizava o painel PASSOS DE TEMPO da sidebar — passo congelava até alcançar o próximo valor compatível. Causa: listeners da toolbar só chamavam `renderTudo()` mas não `atualizarMaxPassos()`, que é quem recalcula `state.maxPassos`/`stepFreq` e repinta a grade de passos. Correção: ambos listeners (modelo, variável) agora chamam `atualizarMaxPassos()` antes do sync da toolbar e do `renderTudo`. Snap do `passoAtual` ao novo grid acontece automaticamente.

**Antes disso:** **Fase 1 — toolbar de seleção no dashboard GeoTIFF**. Adicionada `#gtToolbar` dentro de `#mainGT` com `[Modelo ▼] [Variável ▼] [Data ▼] [◀ Passo ▶]`. Reflete e modifica `state.slots[0]` do modo GeoTIFF (que já é independente do PNG). Funções: `gtPopulateModeloSelect`, `gtPopulateVariavelSelect`, `gtSyncToolbarFromState`, `gtBindToolbar`. Trocar modelo auto-troca para a 1ª variável dele. Variável e data disparam `renderTudo()` que recarrega o TIF. Hint mostra "(URL .tif será derivada da extensão)" quando o modelo é PNG. +7 KB no HTML (400 → 406). **Fase 2 pendente**: multi-painel completo (M1..Mn no GeoTIFF com canvas+mapa+state por painel).

**Antes disso:** **estado independente por aba PNG/GIF vs GeoTIFF**. Cada aba lembra: modelo, variável, data, passo, layout 1/2/3/4 e tempo de animação. Trocar de aba: (1) salva snapshot do `state` atual em `localStorage['sismom_state_'+mode]`, (2) chama `pararAnimacao()` para liquidar timers, (3) restaura snapshot da outra aba via `Object.assign`, (4) re-aplica via `setLayout(state.layout, true)` + `setStepIndicatorUI()` + `renderTudo()`. Animação nunca é retomada automaticamente. +3 KB no HTML (397 → 400).

**Antes disso:** **não mostrar "Carregando..." no info (sem salto na animação)**. A URL longa no `#gtInfo` antes do fetch causava quebra de linha (1 → 2 linhas) e o painel "saltava" a cada passo da animação. Removido `info.textContent = 'Carregando URL…'`; o info mantém o último estado válido enquanto o próximo passo decodifica. `#gtInfo` agora tem `height: 1.4em` + `white-space: nowrap` + `text-overflow: ellipsis` para nunca refluir. Mensagens de erro ainda aparecem normalmente.

**Antes disso:** **caminho FTP /fig/ → /geotiff/ na derivação do TIF**. O FTP do CPTEC mantém PNGs em `.../regional/mom/fig/` e TIFFs em `.../regional/mom/geotiff/`. `gtDeriveTifUrl` agora aplica duas substituições: (1) troca segmento literal `/fig/` por `/geotiff/` no path (regex `/\/fig\//g` — não confunde com `fig_uvo`, `figure_main`, `sismom_fig`); (2) troca extensão final `.png/.gif/.jpg` por `.tif`. Validado com 5 cenários reais. +0.3 KB no HTML.

**Antes disso:** **CORS no Electron + diagnóstico de fetch**. `Failed to fetch` ao carregar GeoTIFF do FTP era CORS (webSecurity true no Electron). Correções: (1) `main.js` agora tem `webSecurity: false` + `allowRunningInsecureContent: true` em `webPreferences` — permite fetch HTTPS externo sem restrição. (2) Mensagem de erro no HTML detecta padrão de CORS (`failed to fetch|cors|networkerror`) e adiciona dica `"Provável CORS: rode no Electron com webSecurity:false"`. Inclui a URL completa que falhou e `console.error` com detalhes para DevTools. **Importante**: reinicie o app Electron após o patch (`Ctrl+R` no app não recarrega o main.js — feche e reabra).

**Antes disso:** **derivar URL .tif do modelo PNG/GIF**. No modo GeoTIFF, modelos com extensão `.png/.gif/.jpg/.jpeg` agora têm a URL final derivada automaticamente substituindo a extensão por `.tif` (regex `/\.(png|gif|jpe?g)(\?.*)?$/i`). Não é mais necessário cadastrar modelo separado com `.tif`. A animação por passos (play/pause/step do header) continua reusando `state.passoAtual` + hook em `renderTudo` — apertar Play no modo GeoTIFF anima o painel. Modelos com extensão `.tif/.tiff` nativos continuam usando a URL original. Validado com regex contra 7 padrões (preserva query string, case insensitive). +1 KB no HTML.

**Antes disso:** **reposicionar toggle do painel + chevrons à direita**. O botão de ocultar painel direito (`›/‹`) estava em `top: 6px`, colado no chevron `▾/▸` do primeiro header e parecia sobrepor o controle vertical do accordion. Correções: (1) botão movido para `top: 50%; transform: translateY(-50%)`, altura `44px` (área clicável mais confortável e claramente separada do topo). (2) Headers de seção usam `justify-content: space-between` com o **chevron alinhado à direita** (antes era à esquerda do título). +0.1 KB no HTML.

**Antes disso:** **seções do painel direito como dropdowns/accordions**. Cada cabeçalho `<h4>` (Arquivo/Visual, NoData/Clip, Camadas) virou clicável com chevron `▾`/`▸` e wrapper `.gt-section-body` que colapsa com transição CSS (`max-height` + `opacity`). Estado por seção persistido em `localStorage['sismom_gt_sections']`. Nova `gtMakeAccordion()` invocada ao final de `gtReorganizeLayout`. +3 KB no HTML.

**Antes disso:** **truncar nomes longos nos chips**. Nomes resultantes de cálculos repetidos (ex.: `(((temp-0010.tif + 273) + temp-0010.tif) + ...)`) expandiam o chip e empurravam os controles ↑↓👁✕ pra fora. Correção CSS: chip ocupa 100% da largura do painel (`width:100%; min-width:0; max-width:100%`), `.gl-name` ganha `flex:1 1 0 + min-width:0` para encolher com `ellipsis`, botões com `flex-shrink:0` para não encolherem, `#gtLayerChips` em column layout. Painel lateral com `overflow-x:hidden`. Tooltip do nome no hover mostra texto completo. +1 KB no HTML.

**Antes disso:** **calculadora de camadas (raster algebra)**. Nova linha no painel: `Calc: [A ▼] [op ▼] [B ▼ ou escalar] [Calcular]`. Operadores `+ − × ÷`. B pode ser outra camada GeoTIFF (mesma dimensão) ou valor escalar (ex.: ×1000 para converter m→mm). NoData propaga (qualquer fonte com nodata gera nodata no resultado); divisão por zero também. Resultado vira nova camada extra com nome descritivo tipo `(foo.tif × 1000)`. Selects sincronizam automaticamente ao adicionar/remover camadas. Implementado: `gtCalcularNovaCamada()`, `gtRenderCalcSelects()`, `gtUpdateCalcScalarVisibility()`. +7 KB no HTML (385 → 392).

**Antes disso:** **múltiplos sentinels + min/max robusto via percentil**. `Eta10_C00_PREC_2015020201.tif` tinha 2 valores sentinel (`-3.4e+38` e `~5.87e+9`); o detector pegava só o de maior magnitude e o range continuava absurdo, deixando o raster amarelo sólido. Correção: (1) loop iterativo (até 5 passes) detecta múltiplos sentinels, armazenados em `decoded.nodataExtras[]`; (2) se após 5 iterações o range ainda > 1e6, usa **percentis 1%/99%** de uma amostra de ~10k pixels como min/max; (3) `aplicarPaleta` e `gtIsMasked` agora consultam `decoded.nodataExtras` como fallback; (4) info mostra sentinels extras em notação exponencial. +2 KB no HTML (383 → 385).

**Antes disso:** **navegação errada em bbox global** corrigida em 3 frentes. Bbox `(-181, 181)` com margem 10% gerava viewport `(-217.2, 217.2)` — span > 360° (mais que uma volta do mundo), causando coordenadas absurdas no HUD (cursor sobre Argentina mostrando lon=129° em vez de -60°). Correções: (1) `fitTo` limita a margem: `lonMargin = min(lonW * m, max(0, (360 - lonW) / 2))` — sem margem em lon quando bbox já cobre o globo; análogo para lat (170° máx). (2) `adjustViewportToAspect` clampa `lonSpan <= 360°` mesmo após ajuste de aspect. (3) Helper `gtWrapLon(lon)` normaliza qualquer longitude para [-180, 180] (formula `((lon+180) % 360 + 360) % 360 - 180`) antes de exibir no HUD e indexar o raster. Testado com longitudes `-217.2 → 142.8`, `217.2 → -142.8`, `540 → 180`. +1 KB no HTML.

**Antes disso:** **bbox correta para GeoTIFF global + NoData heurístico**. (1) Normalizador de longitude 0..360→-180..180 estava aplicando por tiepoint isolado e quebrava arquivos com cobertura global (-181, 181). Agora `_shouldNormalizeLon(xs)` só retorna true se **todas** as longitudes estão em [0, 360] E alguma > 180 (caso clássico GrADS-Pacífico). (2) Heurística de NoData implícito: se o arquivo não tem `GDAL_NODATA` e o range é absurdo (`|max - min| > 1e6`), o valor extremo é tratado como sentinel; `decoded.nodata` é populado e min/max recalculados ignorando esses pixels. Testado com `temp-0010` (GrADS global, sentinel `-999e6`) e `Prec-0001` (GrADS Pacífico) — ambos com bbox/escala corretas. +1 KB no HTML (381 → 382).

**Antes disso:** **suporte a GeoTIFFs do GrADS (multi-tiepoint) + pan/zoom no canvas sem mapa**. (1) `decodeTIFF` agora extrai bbox de **multi-tiepoint sem ModelPixelScale** (4 tiepoints nos cantos, padrão GrADS), além do caso "1 tiepoint + scale". Normaliza longitudes em **0..360 → -180..180** automaticamente. (2) Para arquivos que ainda não têm bbox, canvas raster ganhou pan/zoom via CSS transform (`#gtCanvas { transform-origin: center }` + listeners de wheel/drag). Botões `+ − ⟲` do HUD detectam canvas ativo vs mapa e atuam no caminho apropriado. Reset do transform ao carregar novo arquivo. +4 KB no HTML (377 → 381).

**Antes disso:** **nome do arquivo, opacidade por camada, botão limpar**. (1) `gtPrimaryName` armazena o nome do arquivo da base — vem de `f.name` do file picker ou do último segmento da URL do FTP. Substitui `(camada base)` no chip. (2) Slider de opacidade agora afeta a **camada ativa** (não só a primary); ao trocar de camada ativa, o slider reflete a opacity dela. Nova função `getOverlayOpacity(id)` exposta no `SisMOM_Map`. (3) Botão **Limpar** ao lado do `+ Adicionar` remove todas as extras (com confirmação) preservando a base; volta a ativa para `primary`. +3 KB no HTML (374 → 377).

**Antes disso:** **camada base unificada no array de overlays**. A base não fica mais sempre em primeiro plano. Agora vive em `self.overlays[]` do `SisMOM_Map` com flag `isPrimary` (apenas para a moldura tracejada da bbox). `setRasterOverlay/clearOverlay/setOpacity` delegam para a entry com id='primary'. Nova `moveOverlay(id, delta)` reordena qualquer camada no array. `gtMoveLayer` agora trata `id='primary'` (chama `_gtMap.moveOverlay`); chips com ↑/↓ habilitados para a base também. `gtAllLayers` usa `getOverlayIndex('primary')` para refletir a posição real. +2 KB no HTML (372 → 374).

**Antes disso:** **clip da camada extra atualiza escala + redraw forçado no reorder**. (A) Novo `gtRecomputeMinMaxForLayer(layer)` que recalcula min/max ignorando pixels mascarados pelos filtros (nodataExtras, clipBelow, clipAbove) e grava em `layer.props.effMin/effMax`. `gtApplyActiveLayer` e `gtLayerPushToMap` agora usam esses valores quando `autoMinMax = true`. Colorbar (canvas + pilha overlay) reflete os efetivos. Inputs `#gtMin/#gtMax` atualizam quando a camada extra é ativa em auto. (B) `gtMoveLayer` chama `_gtMap.redraw()` explícito ao final + `console.debug` para rastrear. +3 KB no HTML.

**Antes disso:** **correção de 2 bugs nas camadas extras**. (A) Paleta monocromática: `gtLayerPushToMap` ignorava `layer.props` e passava só `{paleta}` para `aplicarPaleta`. Agora consulta props completas (paleta + min/max custom + undefRaw + clipBelow/Above). `gtAddExtraLayerFromFile` inicializa props já na criação. Opacidade default da extra subiu para 0.85. (B) Reordenação ↑/↓ sem efeito visual: `drawRaster` iterava `overlays[]` de 0 a N-1, deixando `overlays[0]` no fundo. Invertida iteração para que `overlays[0]` seja desenhado **por último** entre as extras → fica visualmente em cima. Pilha de colorbars com `flex-direction: column` natural (não mais `column-reverse`). +1 KB no HTML.

**Antes disso:** **HUD à esquerda + pilha de colorbars + ocultar base**. (1) HUD inferior agora ancorado à esquerda; atribuição (Esri/OSM/Topo) à direita. (2) Pilha `.gt-cb-stack` posicionada acima do HUD, com mini-colorbar (140×12 px) + nome + min…max para cada camada raster **visível**; empilha em ordem visual com `flex-direction: column-reverse` (camada extra adicionada por último fica no topo, base no fundo). (3) Camada base agora pode ser ocultada via 👁 no chip (antes desabilitado); `gtPrimaryVisible` respeitado em `gtRenderar`, `gtSyncMapOverlay` e overlay colorbars. +6 KB no HTML (362 → 368).

**Antes disso:** **HUD inferior central** com navegação + lat/lon/valor. Barra flutuante (`.gt-bottom-hud`, `position: absolute; bottom: 16px; transform: translateX(-50%)`) sobre o canvas/mapa, contendo botões **+ − ⟲** e o texto de coordenada/valor sob cursor (`#gtCoordHud`). `SisMOM_Map.zoomBy(factor)` ajusta `lonSpan`/`mercYSpan` preservando centro e aspect. Reset chama `fitTo(gtLastDecoded.bbox)`. `gtCoord` e `gtCoordHud` sempre espelhados. +4 KB no HTML.

**Antes disso:** **botões edge nas duas barras + reposicionamento**. (1) Adicionado `#btnSidebarEdgeToggle` fixo na borda direita da sidebar esquerda (estilo `‹/›`) que reusa a `toggleSidebar()` existente; `MutationObserver` sincroniza o ícone quando o estado muda via tecla `S` ou header. (2) `#btnGtSideToggle` (painel direito) repassado para `right: 320px` em vez de `312px` — agora fica encostado **fora** do painel, sem sobrepor o texto "ARQUIVO / VISUAL". +2 KB no HTML.

**Antes disso:** **preservação do aspect ratio do mapa**. Quando o painel lateral colapsa/expande, o canvas mudava de proporção e o conteúdo aparecia esticado. Adicionado `adjustViewportToAspect()` no `SisMOM_Map` que ajusta o `latSpan` (via Mercator y) para casar `canvas.width/height`, preservando o centro. Chamado em `resize`, `fitTo`, `setViewport`, `setProjection`, `setTileProvider`. Toggle do painel agora dispara `redraw + gtRenderar + colorbar` 280 ms após o clique (espera a transição CSS de 250 ms terminar). +3 KB no HTML.

**Antes disso:** **aproveitamento de altura cheia no dashboard**. CSS específico de `.modal-backdrop.inline` agora coloca o modal em `height: calc(100vh - 70px)` com flex column, e o container dos canvases (marcado pela classe `.gt-canvas-wrap` via JS no `gtReorganizeLayout`) ocupa toda altura disponível. Sumiu o `max-height: 60vh` que limitava o mapa a 60% da viewport. Side panel ganha scroll interno se passar da altura. +1 KB no HTML (350 → 351).

**Antes disso:** **painel lateral colapsável + reordenação + camada ativa**. O modal/dashboard ganhou layout em duas colunas: canvas/mapa à esquerda, painel lateral à direita (~320 px) com botão `›/‹` na borda para ocultar/mostrar. Os controles (paleta, min/max edit, UNDEF/Clip, lista de camadas, colorbar) foram movidos para o painel via `gtReorganizeLayout()` no init — sem duplicar HTML. Lista de camadas agora tem botões `↑/↓` para reordenar (re-empurra ao mapa na nova ordem) e clique seleciona como **camada ativa**. Cada camada tem suas próprias props (paleta/min/max/UNDEF/clip): mudar um input afeta só a camada ativa. Colorbar reflete paleta/min/max da ativa. `gtApplyActiveLayer()` orquestra: primary→gtRenderar+recompute; extra→aplicarPaleta+addRasterOverlay com opts específicas. +13 KB no HTML (337 → 350).

**Antes disso:** **sobreposição de camadas extras (GeoTIFF + GeoJSON)** no modal/dashboard. Nova linha "Camadas extras:" com botão "+ Adicionar GeoTIFF/GeoJSON…" — file picker aceita `.tif/.tiff/.geojson/.json` e cria chips visíveis com toggle de olho 👁/⊘ e remover ✕. `SisMOM_Map` agora suporta múltiplos raster overlays (array com id) e GeoJSONs com id e visibilidade. GeoJSONs ganham cor cíclica de uma paleta de 8 cores. Camada base do dashboard (slot 0 / arquivo aberto) fica em cima; extras embaixo. Adicionar uma extra ativa o mapa automaticamente. +9 KB no HTML (329 → 337).

**Antes disso:** **dashboard GeoTIFF como aba/tab no header**. Tabs `[PNG/GIF]` `[GeoTIFF]` no topo persistem modo em `localStorage`. Em modo GeoTIFF, o conteúdo do modal local (com paleta, min/max, mapa Mercator+tiles, colorbar, UNDEF/Clip, HUD do valor, atribuição) é **movido inline** para uma `<section id="mainGT">` via `appendChild`, sem duplicação de UI. O painel se conecta ao slot 0 do state (modelo/variável/data/passo): renderTudo() dispara `gtLoadFromState()` que monta URL via `montarURL` + fetch + decode. Animação por passos reusa todo o sistema existente (play/pause/step). Volta para modo PNG devolve o modal ao body. +6 KB no HTML.

**Antes disso:** **colorbar (barra de escala de cores)**. Canvas #gtColorbar (38 px de altura, largura plena) entre os controles e a área do raster mostra gradient da paleta corrente + 5 ticks (min, 25 %, 50 %, 75 %, max) com labels formatados (fixed/exponential adaptativo). Reflete automaticamente troca de paleta, edição de min/max, novo arquivo, e filtros UNDEF/clip (via recálculo de min/max no modo Auto). HiDPI-aware via devicePixelRatio. +4 KB no HTML.

**Antes disso:** **valores UNDEF e clipping manuais**. Nova linha no modal local: input "UNDEF:" (uma ou várias entradas separadas por vírgula/espaço, ex. `-999, -9999`), inputs "Clip ≥" / "Clip ≤" para máscara por threshold, botão Limpar. Pixels filtrados ficam transparentes na renderização e marcados como NoData no HUD do cursor. Quando min/max está em modo "Auto", o intervalo é recalculado ignorando pixels mascarados. +5 KB no HTML (313 → 318).

**Antes disso:** **HUD do valor do raster sob o cursor**. Ao mover o mouse sobre o mapa OU sobre o canvas do raster, o HUD mostra `lat, lon · valor = X` (notação científica adaptativa, "NoData" quando aplicável). Funciona em ambos os modos (com mapa Mercator e sem mapa). +3 KB no HTML.

**Antes disso:** **camada de mapa-base com tiles online** no modal "Abrir GeoTIFF local". O mapa custom anterior foi estendido para `v2`: agora suporta projeção Web Mercator (além de Plate Carrée) e camadas de tiles XYZ. Três providers embutidos: **Esri World Imagery (satélite, default)**, **OpenStreetMap (ruas)** e **OpenTopoMap (topográfico)**, todos sem API key. Seletor no modal alterna entre os três + opção "Sem tiles (offline)" que volta ao mapa custom anterior. Atribuição automática no canto inferior direito conforme provider ativo. Cache de tiles em RAM (limite 400). Pan/zoom recalculam corretamente em Mercator. HTML: ~304 KB → **~312 KB**. Painéis Mi ainda **diferidos**.

**Antes disso:** camada de mapa-base custom (Plate Carrée). Canvas próprio, costa da América do Sul (~53 pontos curados) + 17 capitais sul-americanas + grade lat/lon dinâmica, pan/zoom/wheel, slider de opacidade, HUD lat/lon do cursor. Sem dependência externa (Leaflet recusado por download corporativo problemático). API `SisMOM_Map` exposta com `addGeoJSON()` para o usuário plugar shapefiles próprios (IBGE/Natural Earth) se quiser detalhes maiores.

**Antes disso:** suporte a **visualização de GeoTIFF**. Decoder TIFF inline (sem dependência externa), 5 paletas (Viridis/Jet/RdBu/Cinza/Turbo), modal "Abrir GeoTIFF local", e integração nos painéis Mi via `m.extensao = '.tif'/'.tiff'`. JS validado, cópias idênticas, 8 testes unitários + smoke test pós-patch verdes.

**Arquivos novos em `dev/`:**
- `geotiff_module.js` — módulo standalone usado para desenvolver/testar fora do HTML
- `test_geotiff.mjs` — 8 testes (uint8/uint16/float32, PackBits, GeoKeys, paleta, helper)
- `test_after_patch.mjs` — smoke test extraindo o bloco do HTML
- `patch_geotiff.py` — aplica o patch nas duas cópias em lockstep, idempotente

**Commit sugerido (ainda não feito):**
```
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html dev/
git commit -m "Adicionar visualizacao de GeoTIFF (decoder inline + paletas + modal local + integracao nos paineis)"
git push
```

**Limites conhecidos:**
- Não cobre JPEG-in-TIFF, BigTIFF (>4GB), CCITT (raros em saídas de modelo meteo)
- Para FTP do CPTEC, leitura usa `fetch()` (sujeito a CORS). PNG/JPG seguem como antes via `<img>`. Se o servidor não tiver CORS, GeoTIFF via FTP só funciona no Electron (que pode bypassar webSecurity); arquivos locais sempre funcionam.
- "Pasta local com varredura" foi diferido (fase 2). Modelo via FTP e arquivo avulso já cobertos.

**Pendente do usuário:**
1. Testar abrir um .tif local → conferir paletas, min/max auto + Editar
2. Configurar um modelo com extensão `.tif` ou `.tiff` (campo "Sufixo do arquivo" no modal de config) e ver se carrega via FTP/Electron
3. Se CORS bloquear no Electron, avaliar habilitar `webSecurity: false` em `main.js`

## 9.1 Histórico anterior (mantido para referência)

Antes do GeoTIFF, a última mudança foi: separação de desbloqueio de sessão vs. modelos protegidos. Os 5 passos de teste do 2FA continuam válidos:
1. Ativar 2FA
2. Marcar modelo como `requires2FA`
3. Recarregar → digitar código → modelo protegido **não** aparece
4. Segurança → "🔓 Desbloquear modelos protegidos" → digitar novo código → aparece
5. "🔒 Bloquear modelos protegidos" → some de novo, sessão geral continua aberta

## 10. Histórico do transcript (referência completa)

Arquivo JSONL com transcript da sessão anterior:
```
C:\Users\jorge\AppData\Roaming\Claude\local-agent-mode-sessions\
  e193a085-f07b-4e32-9fa5-2889f4808d93\
  6992c69a-a984-410d-aea8-bc7c711d02be\
  local_a9d3df75-ec4c-4054-bafa-01a55b6ea4e6\
  .claude\projects\
  C--Users-jorge-AppData-Roaming-Claude-...\
  8345d134-850e-4f7d-9c5b-eda954efd145.jsonl
```

## 11. Como abrir a próxima sessão

1. Abrir Cowork com a pasta `C:\Projetos\Visualizador` selecionada
2. Colar esta mensagem inicial:

> Continuando o projeto SisMOM Visualizador. Leia o briefing em `C:\Projetos\Visualizador\BRIEFING_SESSAO.md` para o contexto completo. Última mudança aplicada: separação de desbloqueio de modelos protegidos vs. sessão geral. Aguardo seu OK para testar ou nova tarefa.

3. (Opcional) Se a tarefa for delicada, anexar também o JSONL do transcript.

---

*Gerado em 2026-05-26. Atualizar sempre que houver mudança estrutural.*
