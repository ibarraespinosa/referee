#!/usr/bin/env bash
set -e

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"

mkdir -p "${BIN_DIR}" "${APP_DIR}"

# 1. Symlink CLI executables (referee and pdf-reviewer)
ln -sf "${INSTALL_DIR}/bin/referee" "${BIN_DIR}/referee"
ln -sf "${INSTALL_DIR}/bin/referee" "${BIN_DIR}/pdf-reviewer"
echo "[✓] Symlinked 'referee' and 'pdf-reviewer' to ${BIN_DIR}/"

# 2. Install Desktop entry
cat << DESKTOP > "${APP_DIR}/referee.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Referee
GenericName=PDF Review & Annotation Editor
Comment=Acrobat-like PDF reader and review editor with text highlights, notes, and report export
Exec=${INSTALL_DIR}/bin/referee %f
Icon=${INSTALL_DIR}/assets/pdf-reviewer.png
Terminal=false
MimeType=application/pdf;
Categories=Office;Graphics;Viewer;Development;
Keywords=pdf;editor;review;annotation;highlight;acrobat;reader;referee;paper;
StartupNotify=true
DESKTOP

chmod +x "${APP_DIR}/referee.desktop"
echo "[✓] Created desktop entry at ${APP_DIR}/referee.desktop"

# 3. Update desktop database if available
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "${APP_DIR}" 2>/dev/null || true
fi

echo ""
echo "=========================================================="
echo " Referee successfully installed!"
echo " You can now:"
echo "   1. Launch from Ubuntu application menu: search 'Referee'"
echo "   2. Open from terminal: referee paper.pdf"
echo "   3. Right-click any PDF in file manager -> Open With -> Referee"
echo "=========================================================="
