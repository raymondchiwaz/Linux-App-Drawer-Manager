#!/usr/bin/env bash
set -euo pipefail
APP_ID="com.example.AppDrawerManager"
DESKTOP_FILE="$HOME/.local/share/applications/${APP_ID}.desktop"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_FILE="$SCRIPT_DIR/app_launcher_manager.py"

mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=App Drawer Manager
Exec=python3 "$PY_FILE"
Terminal=false
Icon=applications-system
Categories=Utility;Settings;
X-Custom-Added=1
EOF

echo "Installed desktop entry: $DESKTOP_FILE"
