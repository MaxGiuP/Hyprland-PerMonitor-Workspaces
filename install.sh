#!/bin/bash
set -e

SCRIPT_NAME="renumber-daemon.py"
SERVICE_NAME="renumber-daemon.service"

SCRIPT_PATH="$HOME/.config/hypr/scripts/$SCRIPT_NAME"
SERVICE_PATH="$HOME/.config/systemd/user/$SERVICE_NAME"

mkdir -p "$HOME/.config/hypr/scripts"
mkdir -p "$HOME/.config/systemd/user"

cp "$SCRIPT_NAME" "$SCRIPT_PATH"
chmod +x "$SCRIPT_PATH"
cp "$SERVICE_NAME" "$SERVICE_PATH"

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"

echo "Installed and started $SERVICE_NAME"
