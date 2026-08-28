#!/bin/bash
log="$HOME/.orca-gui-watch.log"
status=$(orca-ide status --json 2>/dev/null | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin)["result"]["app"]["desktopWindowStatus"])
except Exception:
    print("parse-error")
' 2>/dev/null)
[ "$status" = "available" ] && exit 0
echo "$(date -Is) status=${status:-empty} -> reopen" >> "$log"
orca-ide open --json >/dev/null 2>&1
