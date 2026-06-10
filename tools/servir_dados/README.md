# SisMOM — Servidor HTTP local de dados

> **Porta:** o padrão é **8770**. A porta **8765 é reservada ao helper Python**
> do GISELE (aceleração + ferramenta de download) — não use 8765 aqui.


Pequeno script (Python ou Node.js) que serve uma pasta local em
`http://localhost:8770/`. Permite ao GISELE ler arquivos do
disco local em **qualquer navegador** (Safari, Firefox, Chrome, Edge) e
**sem precisar selecionar a pasta a cada sessão**.

## Quando usar

- Você quer abrir o app em **Safari** (que não tem File System Access API).
- Você não quer instalar o app Electron, só rodar o HTML em browser.
- Os dados estão em disco local (ou em pasta de rede acessível como
  arquivo) e você quer animar / navegar passos sem latência de rede.

## Como funciona

O script sobe um servidor HTTP local. Você configura no template do
modelo do SisMOM uma URL `http://localhost:8770/...`. O app trata como
URL HTTP normal — `fetch` lê os arquivos via localhost com CORS
liberado.

```
+----------------+      HTTP localhost      +-------------------+
|   SisMOM HTML  |  <-----------------------|  servir_dados.py  |
|  (no browser)  |   GET /Eta3km/.../*.tif  |   ↓ lê do disco   |
+----------------+                          +-------------------+
                                                     |
                                            C:\dados\meteorologia\
                                            └── Eta3km\
                                                ├── 2026\
                                                │   └── 05\
                                                │       ...
```

## Instalação

Coloque a pasta `servir_dados/` em algum lugar fixo da sua máquina
(ex: `C:\Programas\SisMOM\servir_dados\` ou `~/sismom/`).

Requer **Python 3.6+** OU **Node.js 14+** — qualquer um basta. O launcher
detecta automaticamente.

### Verificar o que tem instalado

```bash
# Windows (PowerShell)
python --version
node --version

# Linux/macOS
python3 --version
node --version
```

## Uso rápido

### Windows (drag-and-drop)

1. **Arraste a pasta de dados sobre `servir_dados.bat`**.
2. Janela do terminal abre mostrando:
   ```
   ==============================================================
    GISELE — Servidor local de dados
   ==============================================================
    Diretório:  C:\dados\meteorologia
    URL base:   http://localhost:8770/
    CORS:       habilitado
   ```
3. **Deixe a janela aberta** enquanto usa o app. `Ctrl+C` para parar.

### Linux / macOS

```bash
chmod +x servir_dados.sh
./servir_dados.sh /home/usuario/dados/meteorologia
```

### CLI direto (qualquer SO)

```bash
# Python
python servir_dados.py --dir /caminho/pasta --port 8770

# Node
node servir_dados.js --dir /caminho/pasta --port 8770
```

Opções:
- `--dir`, `-d` — pasta a servir (default: diretório atual)
- `--port`, `-p` — porta TCP (default: 8770)
- `--bind`, `-b` — interface (default: `127.0.0.1`; use `0.0.0.0` pra expor na rede local)

## Configurar no SisMOM

1. Inicie o servidor (acima).
2. Abra o GISELE.
3. **Configurar > Editar > escolha o modelo** (ou Clonar).
4. No campo **"Template do endereço (PNG/GIF)"** digite:
   ```
   http://localhost:8770/Eta3km/png/{yyyy}/{mm}/{dd}{hh}/
   ```
5. No campo **"Template do endereço (TIF)"** digite:
   ```
   http://localhost:8770/Eta3km/geotiff/{yyyy}/{mm}/{dd}{hh}/
   ```
6. **Template Nome Arq.**: `{prefixo}{f%3}{ext}` (mesma sintaxe de sempre).
7. **Salvar e aplicar**.

Pronto — animação, troca de modelo, calculadora, tudo funciona normal.

## Estrutura de pasta esperada

Não há estrutura obrigatória — você coloca os placeholders no template
para refletir como SUA pasta está organizada. Exemplos:

### Exemplo 1: por modelo + data + variável

```
dados/
├── Eta3km/
│   └── png/
│       └── 2026/05/27/00/
│           ├── temp-001.png
│           ├── temp-002.png
│           └── ...
```

Template:
```
http://localhost:8770/Eta3km/png/{yyyy}/{mm}/{dd}/{hh}/
{prefixo}{f%3}{ext}
```
(variável "temperatura" com prefixo=`temp` no SisMOM)

### Exemplo 2: tudo no mesmo nível, com data no nome

```
dados/
├── prec-2026052700-001.png
├── prec-2026052700-002.png
```

Template:
```
http://localhost:8770/
{prefixo}-{yyyymmddhh}-{f%3}{ext}
```

## Iniciar automaticamente no boot

### Windows
1. Crie um atalho de `servir_dados.bat` apontando para a pasta dos dados:
   ```
   "C:\Programas\SisMOM\servir_dados\servir_dados.bat" "C:\dados\meteorologia"
   ```
2. Cole o atalho em `shell:startup`
   (Win+R → digite `shell:startup` → Enter → pasta abre).
3. No próximo login o servidor sobe sozinho.

### Linux (systemd user)
Crie `~/.config/systemd/user/sismom-server.service`:
```ini
[Unit]
Description=SisMOM local data server
After=network.target

[Service]
ExecStart=/caminho/servir_dados.sh /caminho/dados
Restart=on-failure

[Install]
WantedBy=default.target
```
Depois:
```bash
systemctl --user enable --now sismom-server
```

### macOS (launchd)
Crie `~/Library/LaunchAgents/br.inpe.sismom.server.plist` — peça ajuda
ao administrador local.

## Troubleshooting

**"Porta 8770 já está em uso"**
- Outro processo está nessa porta. Use `--port 9000` (ou outra livre).
- Para descobrir quem usa: Windows `netstat -ano | findstr 8770`; Linux/Mac `lsof -i :8770`.

**Browser dá "Failed to fetch" ou erro de rede**
- Verifique que o servidor está rodando (janela do terminal aberta).
- Teste no browser: abra `http://localhost:8770/` — deve mostrar listing.
- Verifique se o template aponta para a porta correta.

**Arquivo retorna 404**
- Acesse `http://localhost:8770/` no browser para navegar e confirmar o caminho exato dos arquivos.
- Verifique placeholders no template (`{yyyy}` vs `{yyyymm}` etc.).

**Safari bloqueia localhost**
- Em geral Safari permite `http://localhost`. Se bloquear, verifique:
  - Privacidade > impedir rastreamento entre sites: pode interferir.
  - Tente `--bind 127.0.0.1` (já é o default).

**Quero expor para outra máquina na rede**
- Use `--bind 0.0.0.0`. ATENÇÃO: qualquer um na sua rede poderá ler a pasta. Use só em rede confiável.

## Segurança

- Por default `--bind 127.0.0.1` — só conexões da própria máquina.
- Anti path-traversal: o servidor recusa pedidos para fora da pasta raiz (`../../etc/passwd` → 403).
- **Não use para servir arquivos sensíveis.** É um servidor simples sem autenticação.

## Performance

- Servidor é multi-threaded (atende vários painéis em paralelo).
- Velocidade típica em disco SSD local: 200–500 MB/s.
- Latência HTTP localhost: < 1 ms.
- Para datasets grandes (TBs): considere indexar em SSD dedicado.

## Arquivos do pacote

- `servir_dados.py` — implementação Python (stdlib pura, sem dependências)
- `servir_dados.js` — implementação Node.js (stdlib pura)
- `servir_dados.bat` — launcher Windows (detecta Python ou Node)
- `servir_dados.sh` — launcher Linux/macOS
- `README.md` — este arquivo

Ambas implementações são equivalentes; use a que tiver runtime disponível.
