#!/usr/bin/env bash
# Restaura o estado do projeto para o snapshot 20260528-0400-untruncate-pre-localdir
# (versao apos o fix do tail truncado, antes do patch de pasta local).
set -e
cd "$(dirname "$0")/../../.."
echo "Restaurando figuras_SisMOM_v23.html (raiz)..."
cp -f dev/snapshots/20260528-0400-untruncate-pre-localdir/figuras_SisMOM_v23.html ./figuras_SisMOM_v23.html
echo "Restaurando electron-app/figuras_SisMOM_v23.html..."
cp -f dev/snapshots/20260528-0400-untruncate-pre-localdir/electron-app__figuras_SisMOM_v23.html ./electron-app/figuras_SisMOM_v23.html
echo "Restaurando electron-app/package.json..."
cp -f dev/snapshots/20260528-0400-untruncate-pre-localdir/electron-app__package.json ./electron-app/package.json
echo "Restaurando electron-app/main.js..."
cp -f dev/snapshots/20260528-0400-untruncate-pre-localdir/electron-app__main.js ./electron-app/main.js
echo
echo "OK - estado restaurado para build 20260528-0400-untruncate."
