# GISELE — Visualizador

Plataforma de visualização de modelos meteorológicos e oceanográficos
**GISELE** — *Gestão Integrada de Soluções Estratégicas e Inteligência*
(CPTEC · INPE · MCTI). Aplicativo de página única (`figuras_SisMOM_v23.html`)
empacotado em **executáveis** para Windows (`.exe`), macOS (`.dmg`) e
Linux (`AppImage`/`.deb`).

> **Versão atual:** v2.16.0 — build `20260610-form-campos`.
> Dois modos de operação: **PNG/GIF** (figuras pré-renderizadas do FTP do
> CPTEC) e **GeoTIFF** (dado bruto decodificado no navegador, paleta editável).
> Veja a seção 4 e o manual completo em `docs/GISELE_Manual_Uso.pdf`.

---

## 1. Gerar os executáveis

### Pré-requisito (uma vez)

Instale o **Node.js LTS** — https://nodejs.org (inclui o `npm`).

> Builde **fora do OneDrive**. Arquivos "somente na nuvem" do OneDrive
> corrompem o ícone/JSON do build. Trabalhe num caminho local como
> `C:\Projetos\Visualizador` ou `~/Projetos/Visualizador`.

Dentro da pasta do projeto, entre em `electron-app` e instale as dependências
uma única vez por sistema:

```bash
cd electron-app
npm install
```

### Windows (.exe) — rode no Windows

```powershell
npm run dist
```

> Ou rode **`rebuild-electron.bat`** na raiz (build robusto: sincroniza os HTML em lockstep, limpa `dist\` e decide sucesso pela existência do `.exe`).

Saída em `electron-app\dist\`:
- `GISELE Setup 2.12.1.exe` — **instalador** (cria atalho na área de trabalho e no menu Iniciar)
- `GISELE-2.12.1-portable.exe` — **portátil** (roda sem instalar)

### Linux (AppImage / .deb) — rode no Linux ou WSL

```bash
npm run dist:linux
```

Saída em `electron-app/dist/`:
- `GISELE-2.12.1.AppImage` — executável único, portátil
- `gisele_2.12.1_amd64.deb` — instalador Debian/Ubuntu

> No Windows, use **WSL** (`wsl --install` no PowerShell admin) para gerar os
> alvos Linux. Não é possível empacotar AppImage/.deb diretamente do Windows
> (faltam `mksquashfs`/`fakeroot`).

### Comandos auxiliares

| Comando | O que faz |
|---|---|
| `npm start` | Abre o app no Electron para testar (sem empacotar) |
| `npm run dist` | Build Windows (`.exe`) |
| `npm run dist:win` | Idem |
| `npm run dist:linux` | Build Linux (AppImage + `.deb`) |
| `npm run dist:all` | Windows + Linux (precisa de host compatível) |

---

## 2. Instalação

### Windows

- **Instalador:** duplo-clique em `GISELE Setup 2.12.1.exe`,
  escolha a pasta de instalação, conclua. Aparecem atalhos na área de trabalho
  e no menu Iniciar.
- **Portátil:** copie `GISELE-2.12.1-portable.exe` para qualquer pasta e
  abra com duplo-clique. Não instala nada.

### Linux

- **AppImage** (qualquer distribuição):
  ```bash
  chmod +x "GISELE-2.12.1.AppImage"
  ./"GISELE-2.12.1.AppImage"
  ```
  Pode exigir FUSE: `sudo apt install libfuse2`.

- **.deb** (Debian/Ubuntu/derivados):
  ```bash
  sudo dpkg -i gisele_2.12.1_amd64.deb
  sudo apt -f install     # caso falte alguma dependência
  ```
  Depois aparece **"GISELE"** no menu de aplicativos.

---

## 3. Manual de operação

### 3.1. Visão geral

A interface tem três áreas:

- **Cabeçalho** (topo) — logo, título, e botões à direita: ⚙ configuração,
  ❓ atalhos, 🌓 tema claro/escuro, ▭ ocultar/exibir painel lateral.
- **Painel lateral** (esquerda) — escolha do **layout de mapas (1–4)**,
  controles de **animação**, **rodada (Mapa 1)** e **passos de tempo**.
- **Área central** — um a quatro mapas, cada um com sua barra de configuração.

### 3.2. Layout de mapas

No painel lateral, em "Layout de mapas", clique para mostrar **1, 2, 3 ou 4
mapas**. O Mapa 1 é a **referência** (define modelo, variável e rodada base);
os demais entram em cascata (rodada −1 dia, −2 dias, ...) para comparação por
*lead time*.

### 3.3. Cabeçalho de cada mapa

Em cada mapa, na barra superior:

- **Modelo** — escolha entre os modelos cadastrados (ex.: *Regional · Eta 3km*,
  *Global · BESM T062*, *MOM6 Global*, *Mom6 Regional*, *merge*).
- **Data (rodada)** — data da condição inicial do modelo.
- **Botão Sincronizar (🔄)** — só nos mapas posteriores: trava a data igual
  à do Mapa 1 (em vez de cair em cascata).
- **Variável** — campo do modelo a ser exibido.
- **Ferramentas** (direita): 📋 copiar URL da figura · ⬇ baixar imagem ·
  ⤢ tela cheia.

### 3.4. Navegação de rodada (Mapa 1)

No painel lateral, em "Rodada (Mapa 1)":

- **◀** Rodada anterior (−1 dia)
- **Botão central** mostra a rodada atual; clique para ir ao **dia corrente**.
- **▶** Rodada seguinte (+1 dia)

Sempre que a rodada do M1 muda, os mapas posteriores acompanham
automaticamente (cascata −N dias) e o passo volta ao **início da rodada**.

### 3.5. Animação e passos

- **Animar / Pausar** — botão central (▶/⏸). Atalho: **Espaço**.
- **Passo anterior / próximo** — botões ⏮ ⏭. Atalhos: **←** **→**.
- **Parar** — volta ao 1º passo.
- **Velocidade** — 0,2 / 0,5 / 1 / 2 s entre quadros.
- **Barra de tempo** + **grade de passos** — selecione o passo de previsão.
  A grade respeita a `Freq(h)` da variável e o `Horizonte(h)` máximo.

### 3.6. Zoom e arraste

Dentro do mapa:

- **Scroll do mouse** — zoom no ponto do cursor.
- **Duplo clique** — zoom rápido / resetar.
- **Arrastar** — move a imagem (com zoom aplicado).
- **Pinça** (toque) — zoom em telas touch.
- **Atalhos:** **+** / **−** zoom · **R** resetar · **F** tela cheia (Mapa 1).

### 3.7. Tela cheia

Botão ⤢ na barra do mapa ou tecla **F**. Em tela cheia há um controle de
animação flutuante (anterior, play/pause, parar, próximo, velocidade).

### 3.8. Quadro flutuante de informação

Passe o mouse sobre um mapa para ver: modelo, variável, rodada, passo,
**data válida** e o **caminho/arquivo** da figura no servidor.

### 3.9. Configuração de modelos e variáveis (⚙)

Botão ⚙ no cabeçalho abre o modal:

- **Abas** — um modelo por aba; *+ Novo modelo* cria outro.
- **Identidade** do modelo: ID, nome, subsistema, escopo 1/2, sufixo do
  arquivo, máx. passos.
- **Templates de URL** (caminho e nome do arquivo) com placeholders.
- **Tabela de variáveis** — ID, nome longo, unidade, **Freq (h)**, **Horiz (h)**,
  prefixo do arquivo, escopo 1/2 (por variável).
- **Exportar / Importar** — salva/carrega toda a configuração (modelos + painéis)
  como `.json`. Use para levar a configuração entre máquinas.
- **Restaurar padrão** — recoloca os 5 modelos de fábrica.

#### Placeholders nos templates

No **caminho**, datas referem-se à **rodada**; no **nome do arquivo**, à
**data de validade**.

| Placeholder | Significado |
|---|---|
| `{yyyy}` `{mm}` `{dd}` `{hh}` | Componentes de data |
| `{yyyymmddhh}` (e parciais `{yyyy}`, `{yyyymm}`, `{yyyymmdd}`) | Data combinada |
| `{data}` | Rodada completa (`YYYYMMDDHH`) |
| `{N}` ou `{N%n}` | Índice sequencial da figura (`N × Freq` = validade) |
| `{F}` ou `{F%n}` | Hora de previsão (`F` h após a rodada = validade) |
| `{fct}` / `{f%n}` / `{passo}` / `{passo4}` | Formas alternativas (legado) |
| `{escopo1}` `{escopo2}` `{prefixo}` `{ext}` | Escopo do modelo/variável, prefixo e extensão |

**Três modos de validade** (definido pelo nome do arquivo):

1. **Índice + Freq:** `prec-{N%3}{ext}` → `prec-001.png` (validade = rodada + N × Freq)
2. **Horas:** `prec-f{F%3}{ext}` → `prec-f024.png` (validade = rodada + F horas)
3. **Data direta:** `prec-{yyyymmddhh}{ext}` → `prec-2026052700.png`
   (parciais para média anual/mensal/diária)

#### Análise / Observação / Reanálise

Defina **Freq (h) = 0** na variável: o campo é tratado como análise (sem passo
de previsão; validade = a rodada). Quando o **Mapa 1 é análise**, os mapas de
previsão posteriores se alinham automaticamente à data dele. Quando um mapa
**posterior é análise**, ele segue a **data de validade** do que está sendo
verificado.

### 3.10. Comportamento padrão e cache

- Abre com **1 painel**, modelo **Eta · 3km**, na **data atual do sistema**.
- Se a rodada do dia não existir, **recua um dia por vez** até achar uma
  rodada disponível.
- Sempre posiciona no **início da rodada** (1º passo).
- Tema, layout, velocidade, painéis e config de modelos são **salvos**
  automaticamente entre sessões.
- Modelos de fábrica que estejam faltando no cache são **restaurados** ao abrir.

### 3.11. Atalhos de teclado

| Tecla | Ação |
|---|---|
| **Espaço** | Animar / pausar |
| **← / →** | Passo anterior / próximo |
| **+ / −** | Zoom |
| **R** | Resetar zoom |
| **F** | Tela cheia (Mapa 1) |
| **S** | Ocultar/exibir painel lateral |
| **T** | Tema claro / escuro |
| **1 / 2 / 3 / 4** | Quantidade de mapas |
| **?** | Lista de atalhos |
| **Esc** | Fechar modal |

---

## 4. Modo GeoTIFF e recursos avançados

Além do modo **PNG/GIF**, o GISELE tem um modo **GeoTIFF** que decodifica o
dado bruto no navegador e o renderiza com paleta editável. Principais recursos
(passo a passo em `docs/GISELE_Manual_Uso.pdf`):

- **Decodificador GeoTIFF nativo** (sem dependências) + **15+ paletas**
  científicas (Viridis, Turbo, RdBu, ...), com sombreado **Suavizado / Bandas /
  Pixel** e bandas alinhadas aos níveis do contorno.
- **Multi-painel (1–4)** com mapa-base por painel (Esri / OSM / OpenTopo),
  sincronização de viewport, trava e replicação de anotações entre painéis.
- **Árvore ERMA** no painel direito — *Background · Miscelânea · Monitoramento ·
  Camadas · Ferramentas* — com **Configuração da Camada** por camada (paleta,
  min/max, clip, contornos, sombreado).
- **Calculadora dupla**: álgebra entre camadas por expressão
  (`Camada1*1000+Camada2`) e **calculadora temporal** (`t1..t24`,
  `sum/mean/max/min/count`).
- **Contornos** (marching squares, com cache) e **ferramentas** de distância,
  área, perfil de linha e **série temporal** num ponto (gráficos interativos
  com zoom e exportação CSV/PNG).
- **Perfil vertical** e **corte vertical** para variáveis 3D, com **"seguir
  mapa"** (clicar um novo ponto re-renderiza o gráfico sem fechar o pop-up).
- **Skew-T log-P (v2.14)**: sondagem termodinâmica por ponto — isotermas
  inclinadas, adiabáticas secas/úmidas, razão de mistura, curvas de T e Td
  (orvalho via UR ou umidade específica), base inferior pela **pressão de
  superfície**, e **método da parcela** com **LCL/LFC/EL** e **CAPE/CINE**.
- **Miscelâneas**: plataformas offshore, corais, cidades por UF — vetores de
  referência com cor, hachura e popup de atributos.
- **Monitoramento (v2.12)**: rotas de dados genéricos **KML/GeoJSON** — ex.:
  **Queimadas recentes (INPE)**, com atualização ao vivo e filtro Ativas/Inativas.
- **Importar/Exportar**: shapefile/GeoJSON como camada; exportar campo ou
  recorte para **GeoJSON** (com estatísticas); polígonos do usuário salvos.
- **Exportar vídeo MP4** da evolução temporal (nos modos PNG e GeoTIFF).

> **Identidade visual:** a marca GISELE (logo, logomark e ícones) está em
> `brand/`. Os ícones do app ainda apontam para os arquivos legados
> `sismom-icon-*`; a troca para a marca nova está prevista para um próximo passo.

---

## Solução de problemas rápida

- **AppImage não abre no Linux** — instale o FUSE: `sudo apt install libfuse2`.
- **`npm` não encontrado** — instale o Node.js e reabra o terminal.
