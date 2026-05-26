# SisMOM — Visualizador

Visualizador de modelos meteorológicos do **SisMOM** (CPTEC/INPE).
Aplicativo de página única (`figuras_SisMOM_v23.html`) que pode ser usado
direto no navegador, como **janela de aplicativo** (Windows/Linux) ou
empacotado como **executável** (`.exe` no Windows, `AppImage`/`.deb` no Linux).

---

## Conteúdo da pasta

| Arquivo | Para que serve |
|---|---|
| `figuras_SisMOM_v23.html` | O aplicativo (abre em qualquer navegador) |
| `SisMOM.bat` | Abrir como janela de app no **Windows** (Edge/Chrome) |
| `SisMOM.sh` | Abrir como janela de app no **Linux** (Chrome/Chromium) |
| `instalar-atalho.sh` | Cria o atalho "SisMOM Visualizador" no **menu do Linux** |
| `SisMOM.desktop` | Modelo de atalho `.desktop` (edição manual) |
| `sismom_icon.png`, `sismom-icon-192/512.png` | Ícones do app/atalho |
| `electron-app/` | Projeto **Electron** para gerar os executáveis |

---

## 1) Uso imediato (sem instalar nada)

- **Windows:** duplo‑clique em `SisMOM.bat`.
- **Linux:** `chmod +x SisMOM.sh` e depois `./SisMOM.sh`.

Ambos abrem o painel numa janela limpa (modo aplicativo). Também é possível
abrir o `figuras_SisMOM_v23.html` direto no navegador.

### Atalho no menu do Linux (opcional)
```bash
bash instalar-atalho.sh
```
Cria o atalho em `~/.local/share/applications/`. Procure por
**"SisMOM Visualizador"** no menu. Para remover:
```bash
rm ~/.local/share/applications/sismom-visualizador.desktop
```

---

## 2) Gerar os executáveis (Electron)

### Pré‑requisito (uma vez)
Instale o **Node.js LTS**: https://nodejs.org (já vem com o `npm`).

> **IMPORTANTE — OneDrive:** gere os executáveis **fora do OneDrive**
> (ex.: copie a pasta `electron-app` para `C:\build\` ou `~/build/`), ou
> marque a pasta como *"Sempre manter neste dispositivo"*. Arquivos
> "somente na nuvem" corrompem o build (ícone/JSON incompletos).

Entre na pasta do projeto e instale as dependências (uma vez por sistema):
```bash
cd electron-app
npm install
```

### Windows (.exe)  — rode no Windows
```bash
npm run dist
```
Saída em `electron-app/dist/`:
- `SisMOM Visualizador Setup 1.0.0.exe` — instalador (cria atalho na área de trabalho)
- `SisMOM Visualizador 1.0.0.exe` — versão **portátil** (roda sem instalar)

### Linux (AppImage / .deb)  — rode no Linux
```bash
npm run dist:linux
```
Saída em `electron-app/dist/`:
- `SisMOM Visualizador-1.0.0.AppImage` — executável único
  ```bash
  chmod +x "SisMOM Visualizador-1.0.0.AppImage"
  ./"SisMOM Visualizador-1.0.0.AppImage"
  ```
- `sismom-visualizador_1.0.0_amd64.deb` — instalador Debian/Ubuntu
  ```bash
  sudo dpkg -i sismom-visualizador_1.0.0_amd64.deb
  ```

> O AppImage pode exigir FUSE: `sudo apt install libfuse2`.

### Apenas testar (sem empacotar)
```bash
npm start
```

### Outros comandos
```bash
npm run dist:win     # só Windows
npm run dist:linux   # só Linux
npm run dist:all     # Windows + Linux (em um host compatível)
```

---

## 3) Atualizar o app dentro do executável

O build empacota o `electron-app/figuras_SisMOM_v23.html`. Se você editar o
HTML por fora, copie a versão nova para dentro de `electron-app/` antes de
rodar o `npm run dist`.

---

## 4) Configuração e modelos

- Já vêm **5 modelos embutidos** (Global · BESM T062, MOM6 Global,
  Mom6 Regional, Regional · Eta 3km, merge).
- A configuração (modelos, variáveis, painéis, tema, velocidade) é salva
  automaticamente no navegador/app.
- Modelos de fábrica que faltarem no cache são **restaurados** ao abrir.
- Em **Configurar modelos e variáveis** há **Exportar/Importar** (.json)
  para levar a configuração entre máquinas.

### Comportamento de abertura
- Abre com **1 painel**, modelo **Eta · 3km**, na **data atual do sistema**.
- Se a rodada do dia não existir, recua para o dia anterior automaticamente.
- Posiciona sempre no **início da rodada** (1º passo).

---

## Solução de problemas

- **Ícone do .exe aparece como o do Electron:** rebuild com o `electron-app/icon.ico`
  presente (não "somente na nuvem"); se persistir no Explorer, limpe o cache:
  `ie4uinit.exe -ClearIconCache`.
- **Build falha / `package.json` corrompido:** sincronização do OneDrive.
  Builde fora do OneDrive.
- **`npm` não encontrado:** instale o Node.js e reabra o terminal.

---

## Versionamento (Git / GitHub)

O repositório já tem `.gitignore`, `LICENSE` (MIT) e um workflow do **GitHub Actions** que builda Windows e Linux automaticamente.

### Inicializar e enviar para o GitHub

Pré‑requisito: ter o **Git** instalado (https://git-scm.com). Crie um repositório vazio no GitHub (sem README/licença/.gitignore para não conflitar).

No PowerShell, dentro de `C:\Projetos\Visualizador`:

```powershell
git init -b main
git config user.name  "Jorge Luis Gomes"
git config user.email "jorge.gomes@inpe.br"
git add .
git commit -m "Initial commit - SisMOM Visualizador v1.0.0"
git remote add origin https://github.com/<seu-usuario>/<seu-repo>.git
git push -u origin main
```

### Lançar uma versão (builds automáticos)

O workflow `.github/workflows/release.yml` builda **Win + Linux** sempre que você cria uma tag `vX.Y.Z` e anexa os artefatos a uma *Release* (rascunho):

```bash
git tag v1.0.0
git push origin v1.0.0
```

Depois, em GitHub → **Actions**, acompanhe o build. Quando terminar, a Release rascunho ficará disponível em GitHub → **Releases** com o `.exe` (instalador e portátil), o `.AppImage` e o `.deb` anexados. Basta publicar.

### Atualizações de rotina

```bash
git add .
git commit -m "Descrição da mudança"
git push
```
