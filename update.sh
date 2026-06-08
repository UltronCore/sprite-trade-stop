#!/usr/bin/env bash
# Safe one-command update for Sprite Trade Stop.
# Pulls the latest code, updates deps, and restarts the systemd service.
# Usage:  ./update.sh
#
# ROLLBACK: this script records the current commit before pulling. If the new
# version misbehaves, roll back with:
#     git reset --hard "$(cat .last_good_commit)" && sudo systemctl restart sprite-trade-stop
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Recording current commit for rollback"
git rev-parse HEAD > .last_good_commit
echo "    saved $(cat .last_good_commit) to .last_good_commit"

echo "==> Pulling latest"
git pull --ff-only

echo "==> Updating dependencies"
if [ -d .venv ]; then
  ./.venv/bin/pip install -q -r requirements.txt
else
  pip install -q -r requirements.txt
fi

echo "==> Restarting service (if installed)"
if systemctl list-units --type=service 2>/dev/null | grep -q sprite-trade-stop; then
  sudo systemctl restart sprite-trade-stop
  echo "    restarted sprite-trade-stop.service"
else
  echo "    no systemd service found — restart the bot however you run it."
fi

echo "==> Done. If something broke, roll back with:"
echo "    git reset --hard \$(cat .last_good_commit) && sudo systemctl restart sprite-trade-stop"
