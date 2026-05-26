#!/usr/bin/env bash
# Instala um atalho "SisMOM Visualizador" no menu de aplicativos do Linux
# (abre o painel via SisMOM.sh, sem precisar do AppImage).
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SH="$DIR/SisMOM.sh"
ICON="$DIR/sismom_icon.png"

[ -f "$SH" ]   || { echo "Erro: nao achei SisMOM.sh em $DIR"; exit 1; }
[ -f "$ICON" ] || ICON="$DIR/sismom_logo_icon.png"
chmod +x "$SH" 2>/dev/null || true

APPS="$HOME/.local/share/applications"
mkdir -p "$APPS"
DESKTOP="$APPS/sismom-visualizador.desktop"
cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=SisMOM Visualizador
GenericName=Visualizador de modelos meteorologicos
Comment=Visualizador de modelos do SisMOM (CPTEC/INPE)
Exec=bash "$SH"
Icon=$ICON
Terminal=false
Categories=Science;Education;
StartupNotify=true
EOF
chmod +x "$DESKTOP" 2>/dev/null || true
update-desktop-database "$APPS" 2>/dev/null || true

echo "OK! Atalho instalado em:"
echo "  $DESKTOP"
echo "Procure por 'SisMOM Visualizador' no menu de aplicativos."
echo "(Para remover: rm \"$DESKTOP\")"
