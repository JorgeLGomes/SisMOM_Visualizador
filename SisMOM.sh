#!/usr/bin/env bash
# Abre o painel SisMOM como janela de aplicativo (Chrome/Chromium) no Linux.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="$DIR/figuras_SisMOM_v23.html"
if [ ! -f "$HTML" ]; then
  echo "Nao encontrei figuras_SisMOM_v23.html nesta pasta."; exit 1
fi
URL="file://$HTML"
for b in google-chrome google-chrome-stable chromium chromium-browser brave-browser microsoft-edge microsoft-edge-stable; do
  if command -v "$b" >/dev/null 2>&1; then
    exec "$b" --app="$URL" --window-size=1440,900
  fi
done
# Sem navegador baseado em Chromium: abre no navegador padrao
xdg-open "$URL" 2>/dev/null || sensible-browser "$URL" 2>/dev/null || echo "Abra manualmente: $URL"
