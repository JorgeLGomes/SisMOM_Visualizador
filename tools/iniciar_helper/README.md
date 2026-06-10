# GISELE — Iniciar o helper Python (micro-serviço local)

O **helper Python** (`gisele-python-helper`) roda em `http://127.0.0.1:8765` e dá ao
GISELE: aceleração das operações pesadas (séries temporais, perfis, calculadora) e o
**micro-serviço da ferramenta "⬇ Dados"** (download das bases de dados/modelos para a
máquina local, com navegação de pastas).

> **No app GISELE (Electron) ele sobe sozinho.** Estes scripts são para quem usa o
> GISELE **no navegador** (abrindo o `figuras_SisMOM_v23.html` direto).

## Como usar

- **Windows:** duplo-clique em `iniciar_helper.bat`. Na primeira vez ele cria um
  ambiente Python (`electron-app/python-helper/.venv-helper`) e instala as dependências
  (alguns minutos, requer internet). Nas próximas, sobe na hora.
- **Linux/macOS:** `./iniciar_helper.sh`

Deixe a janela aberta enquanto usa o GISELE. No pop-up "⬇ Baixar dados", clique em
**↻ Verificar de novo** — o aviso amarelo some quando o helper é detectado.

## Portas

| Serviço | Porta padrão |
|---|---|
| **helper Python** (este) | **8765** (se ocupada, use `iniciar_helper.bat 8766` — o GISELE procura de 8765 a 8768) |
| `tools/servir_dados` (servir dados baixados) | **8770** |

Requer **Python 3.10+** no PATH.
