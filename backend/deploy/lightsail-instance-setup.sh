#!/bin/bash
# Run on a fresh Ubuntu Lightsail instance (SSH in from Lightsail console).
# Plan: at least 2 GB RAM ($12/mo tier).
set -euo pipefail

sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

APP_DIR="$HOME/vton-api"
REPO_URL="${REPO_URL:-https://github.com/hammadqureshi5/ecommerce-webpage.git}"

if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo ">>> Edit $APP_DIR/backend/.env and set FLUX_BASE_URL, then run:"
  echo "    sudo systemctl restart vton-api"
fi

sudo tee /etc/systemd/system/vton-api.service >/dev/null <<EOF
[Unit]
Description=VTON API
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR/backend
EnvironmentFile=$APP_DIR/backend/.env
ExecStart=$APP_DIR/backend/.venv/bin/gunicorn --bind 0.0.0.0:8080 --timeout 300 --workers 1 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vton-api
sudo systemctl restart vton-api

echo "API should be on port 8080. Open Lightsail networking: allow HTTP 8080."
echo "Note: Vercel needs HTTPS — prefer Lightsail Container Service for automatic HTTPS."
