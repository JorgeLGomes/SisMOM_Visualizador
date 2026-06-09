#!/usr/bin/env bash
# ============================================================
#  GISELE - Build automatizado (macOS)
# ============================================================
#  1) Sincroniza o HTML da raiz para electron-app/
#  2) Garante dependencias instaladas
#  3) Limpa dist/ antiga
#  4) Gera .dmg (Intel x64 + Apple Silicon arm64) + .zip
#  5) Monta pacote standalone (HTML sem precisar instalar nada)
#  6) Zipa o standalone
#
#  Pre-requisito:
#    - macOS (electron-builder gera .dmg apenas em macOS)
#    - Node.js LTS (https://nodejs.org)
#    - Xcode Command Line Tools (xcode-select --install)
#
#  Saida: electron-app/dist/
# ============================================================

set -e
cd "$(dirname "$0")"

# Verifica que estamos no macOS
if [ "$(uname)" != "Darwin" ]; then
    echo "AVISO: este script roda no macOS. Para Linux use build.sh; para Windows build.bat."
fi

echo
echo "[1/6] Sincronizando figuras_SisMOM_v23.html da raiz..."
cp -f ../figuras_SisMOM_v23.html ./figuras_SisMOM_v23.html
# Service worker (P2.2) — copia da raiz para o pacote
[ -f ../sw.js ] && cp -f ../sw.js ./sw.js || true

echo
echo "[2/6] Instalando dependencias (npm install)..."
npm install

echo
echo "[2b/6] Minificando HTML (P1.3 — falha aqui nao interrompe o build)..."
npm run minify || true

echo
echo "[3/6] Limpando dist/ antiga..."
rm -rf dist

echo
echo "[4/6] Gerando .dmg + .zip (Intel x64 + Apple Silicon arm64)..."
npm run dist:mac

echo
echo "[5/6] Montando pacote standalone (HTML sem instalacao)..."
VERSION=$(node -p "require('./package.json').version" 2>/dev/null || echo "2.0.0")
STAND="dist/GISELE-${VERSION}-standalone"
rm -rf "$STAND"
mkdir -p "$STAND"

cp -f figuras_SisMOM_v23.html "$STAND/"
cp -f manifest.webmanifest    "$STAND/"
cp -f sismom-icon-192.png     "$STAND/"
cp -f sismom-icon-512.png     "$STAND/"
cp -f ../SisMOM.bat           "$STAND/" 2>/dev/null || true
cp -f ../SisMOM.sh            "$STAND/" 2>/dev/null || true
chmod +x "$STAND/SisMOM.sh" 2>/dev/null || true

cat > "$STAND/LEIA-ME.txt" <<EOF
GISELE ${VERSION} - Versao STANDALONE
=====================================================

Esta pasta contem o aplicativo como HTML puro, que roda
direto no navegador, SEM precisar instalar nada.

COMO USAR
----------
 macOS:
   Duplo-clique em figuras_SisMOM_v23.html (Safari/Chrome)
   OU
   chmod +x SisMOM.sh && ./SisMOM.sh

 Windows:
   Duplo-clique em SisMOM.bat (Edge/Chrome em modo --app)
   OU duplo-clique em figuras_SisMOM_v23.html

 Linux:
   chmod +x SisMOM.sh && ./SisMOM.sh

LIMITACAO IMPORTANTE
---------------------
Ao rodar como HTML direto no navegador via file://, o navegador
pode bloquear o download dos arquivos GeoTIFF do FTP do CPTEC por
causa de CORS (politica de seguranca). Se isso acontecer:
 - Use a versao .dmg (Mac) / .exe (Win) / .AppImage (Linux).
 - O Electron app vem com webSecurity:false e nao tem essa restricao.
 - Alternativa universal: rode o servidor HTTP local (tools/servir_dados/).
EOF

echo
echo "[6/6] Zipando pacote standalone..."
if command -v zip >/dev/null 2>&1; then
  (cd dist && zip -qr "GISELE-${VERSION}-standalone.zip" "GISELE-${VERSION}-standalone")
  echo "  OK: dist/GISELE-${VERSION}-standalone.zip"
fi

echo
echo "============================================================"
echo " Build concluido."
echo " Arquivos em: $(pwd)/dist/"
echo "============================================================"
echo
ls -lh dist/*.dmg dist/*.zip 2>/dev/null || true
echo "  Pasta standalone: $STAND/"
