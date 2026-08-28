#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p ~/.local/bin ~/.config/autostart ~/.config/systemd/user

install -m 755 "$HERE/orca-gui-watch.sh"      ~/.local/bin/orca-gui-watch.sh
install -m 644 "$HERE/orca-ide.desktop"       ~/.config/autostart/orca-ide.desktop
install -m 644 "$HERE/orca-gui-watch.service" ~/.config/systemd/user/orca-gui-watch.service
install -m 644 "$HERE/orca-gui-watch.timer"   ~/.config/systemd/user/orca-gui-watch.timer

systemctl --user daemon-reload
systemctl --user enable --now orca-gui-watch.timer
loginctl enable-linger "$USER"

echo "--- 安装完成，自检 ---"
systemctl --user cat orca-gui-watch.service | grep ExecStart
systemctl --user is-enabled orca-gui-watch.timer
loginctl show-user "$USER" -p Linger
orca-ide status --json | python3 -c \
  'import json,sys; print("desktopWindowStatus:", json.load(sys.stdin)["result"]["app"]["desktopWindowStatus"])'
