#!/usr/bin/env bash
# ============================================================
#  GISELE — Helper Python (micro-serviço local) · Linux/macOS
#
#  Sobe o gisele-python-helper em http://127.0.0.1:8765
#  (aceleração + ferramenta "Baixar dados"). Necessário apenas
#  quando o GISELE roda NO NAVEGADOR; no Electron sobe sozinho.
#
#  Uso:  ./iniciar_helper.sh [porta]      (default: 8765)
# ============================================================
set -e
PORTA="${1:-8765}"
DIR="$(cd "$(dirname "$0")/../../electron-app/python-helper" && pwd)"
[ -f "$DIR/server.py" ] || { echo "ERRO: server.py não encontrado em $DIR"; exit 1; }
cd "$DIR"
if [ ! -x ".venv-helper/bin/python" ]; then
    echo "Primeira execução: criando ambiente Python (.venv-helper)…"
    python3 -m venv .venv-helper
    .venv-helper/bin/python -m pip install --upgrade pip
    .venv-helper/bin/python -m pip install -r requirements.txt
fi
echo "============================================================"
echo " GISELE — Helper Python               em 127.0.0.1:$PORTA"
echo " Deixe este terminal aberto enquanto usa o GISELE no navegador."
echo "============================================================"
exec .venv-helper/bin/python server.py --port "$PORTA"
