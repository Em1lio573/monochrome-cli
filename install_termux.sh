#!/data/data/com.termux/files/usr/bin/bash
# Monochrome CLI - Instalador automático para Termux en Android

set -e

echo "=================================================="
echo "    Instalador de Monochrome CLI para Termux"
echo "=================================================="
echo ""

echo "[1/4] Actualizando paquetes e instalando Python y FFmpeg..."
pkg update -y
pkg install -y python ffmpeg git libjpeg-turbo

echo ""
echo "[2/4] Solicitando permisos de almacenamiento en Android..."
termux-setup-storage || true

echo ""
echo "[3/4] Instalando dependencias de Python..."
pip install --upgrade pip
pip install yt-dlp mutagen rich requests setuptools

echo ""
echo "[4/4] Configurando comando global 'mono' y 'monochrome'..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pip install -e "$SCRIPT_DIR/cli" || true

# Configurar alias directo de respaldo en bashrc
ALIAS_LINE="alias mono='python3 $SCRIPT_DIR/mono.py'"
ALIAS_LINE2="alias monochrome='python3 $SCRIPT_DIR/mono.py'"

if [ -f "$HOME/.bashrc" ]; then
    grep -qxF "$ALIAS_LINE" "$HOME/.bashrc" || echo "$ALIAS_LINE" >> "$HOME/.bashrc"
    grep -qxF "$ALIAS_LINE2" "$HOME/.bashrc" >> "$HOME/.bashrc" 2>/dev/null || true
fi

if [ -f "$HOME/.zshrc" ]; then
    grep -qxF "$ALIAS_LINE" "$HOME/.zshrc" || echo "$ALIAS_LINE" >> "$HOME/.zshrc"
    grep -qxF "$ALIAS_LINE2" "$HOME/.zshrc" >> "$HOME/.zshrc" 2>/dev/null || true
fi

echo ""
echo "=================================================="
echo "  ✔ ¡Instalación de Monochrome CLI completada!"
echo "=================================================="
echo ""
echo "Puedes iniciar la app ejecutando:"
echo "   mono"
echo ""
echo "O buscar directamente una canción con:"
echo "   mono "nombre de la cancion""
echo "   mono -f flac "nombre de la cancion""
echo ""
