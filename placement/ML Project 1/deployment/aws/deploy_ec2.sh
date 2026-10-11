#!/usr/bin/env bash
# ============================================================
# deploy_ec2.sh - one-shot deployment to a fresh Ubuntu 22.04 EC2
# ============================================================
# Usage (from your laptop):
#   scp -i key.pem deploy_ec2.sh ubuntu@<host>:~
#   ssh -i key.pem ubuntu@<host> 'bash deploy_ec2.sh'
# ============================================================
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/YOUR_USER/symposium.git}"
APP_DIR="${APP_DIR:-$HOME/symposium}"

echo "[1/6] Updating apt + installing prereqs"
sudo apt-get update -y
sudo apt-get install -y git curl ca-certificates gnupg lsb-release

echo "[2/6] Installing Docker"
if ! command -v docker >/dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
fi
sudo systemctl enable --now docker

echo "[3/6] Cloning repo"
if [ ! -d "$APP_DIR" ]; then
    git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

echo "[4/6] Bringing up containers"
if [ ! -f .env ]; then
    echo "[!] Missing .env - copy .env.example and fill in secrets"
    exit 1
fi
sudo docker compose pull || true
sudo docker compose up -d --build

echo "[5/6] Running ETL (first-time seed)"
sudo docker compose exec -T symposium python scripts/run_etl.py --topics history science

echo "[6/6] Training models"
sudo docker compose exec -T symposium python scripts/train_models.py

echo "Done. Open http://$(curl -s ifconfig.me):8501"
