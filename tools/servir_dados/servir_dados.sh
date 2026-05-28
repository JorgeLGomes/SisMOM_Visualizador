#!/usr/bin/env bash
# ============================================================
#  GISELE - Servidor local de dados (Linux / macOS)
#
#  Uso:
#    ./servir_dados.sh                       # serve a pasta atual em :8765
#    ./servir_dados.sh /caminho/pasta        # serve essa pasta em :8765
#    ./servir_dados.sh /caminho/pasta 9000   # idem em :9000
#
#  Requer: Python 3 OU Node.js. Detecta automaticamente.
# ============================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DATA_DIR="${1:-$PWD}"
PORTA="${2:-8765}"

if [ ! -d "$DATA_DIR" ]; then
    echo "ERRO: \"$DATA_DIR\" não é uma pasta válida." >&2
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then
    echo "Iniciando servidor com Python 3..."
    exec python3 "$SCRIPT_DIR/servir_dados.py" --dir "$DATA_DIR" --port "$PORTA"
fi

if command -v python >/dev/null 2>&1; then
    # Confirma que é Python 3
    if python -c 'import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)' 2>/dev/null; then
        echo "Iniciando servidor com Python..."
        exec python "$SCRIPT_DIR/servir_dados.py" --dir "$DATA_DIR" --port "$PORTA"
    fi
fi

if command -v node >/dev/null 2>&1; then
    echo "Iniciando servidor com Node.js..."
    exec node "$SCRIPT_DIR/servir_dados.js" --dir "$DATA_DIR" --port "$PORTA"
fi

cat <<EOF >&2

============================================================
 ERRO: nem Python 3 nem Node.js encontrados no PATH.
============================================================

 Instale UM dos dois (qualquer um basta):
   Python 3:  sudo apt install python3   (Debian/Ubuntu)
              brew install python3        (macOS)
   Node.js:   https://nodejs.org/

EOF
exit 1
