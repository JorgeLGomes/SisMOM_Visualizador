# SisMOM Visualizador — Briefing para nova sessão

> Documento de transferência de contexto. Cole/anexe no início da próxima sessão (Opus 4.6 ou modelo mais robusto) para continuar de onde paramos.

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

**Última mudança aplicada:** **dashboard GeoTIFF como aba/tab no header**. Tabs `[PNG/GIF]` `[GeoTIFF]` no topo persistem modo em `localStorage`. Em modo GeoTIFF, o conteúdo do modal local (com paleta, min/max, mapa Mercator+tiles, colorbar, UNDEF/Clip, HUD do valor, atribuição) é **movido inline** para uma `<section id="mainGT">` via `appendChild`, sem duplicação de UI. O painel se conecta ao slot 0 do state (modelo/variável/data/passo): renderTudo() dispara `gtLoadFromState()` que monta URL via `montarURL` + fetch + decode. Animação por passos reusa todo o sistema existente (play/pause/step). Volta para modo PNG devolve o modal ao body. +6 KB no HTML.

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
