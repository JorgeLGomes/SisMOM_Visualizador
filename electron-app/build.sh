#!/usr/bin/env bash
# ============================================================
#  GISELE - Build automatizado (Linux)
# ============================================================
#  1) Sincroniza o HTML da raiz para electron-app/
#  2) Garante dependencias instaladas
#  3) Limpa dist/ antiga
#  4) Gera AppImage + .deb via electron-builder
#  5) Monta pacote "standalone" (HTML sem precisar instalar nada)
#  6) Zipa o standalone
#
#  Pre-requisito: Node.js LTS + libfuse2 (sudo apt install libfuse2)
#  Saida: electron-app/dist/
# ============================================================

set -e
cd "$(dirname "$0")"

echo
echo "[1/6] Sincronizando figuras_SisMOM_v23.html da raiz..."
cp -f ../figuras_SisMOM_v23.html ./figuras_SisMOM_v23.html

echo
echo "[2/6] Instalando dependencias (npm install)..."
npm install

echo
echo "[3/6] Limpando dist/ antiga..."
rm -rf dist

echo
echo "[4/6] Gerando AppImage + .deb (Linux)..."
npm run dist:linux

echo
echo "[5/6] Montando pacote standalone (HTML sem instalacao)..."
VERSION=$(node -p "require('./package.json').version" 2>/dev/null || echo "2.0.0")
STAND="dist/SisM