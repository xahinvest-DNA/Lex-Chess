#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/lex-chess"
REPO_URL="https://github.com/xahinvest-DNA/Lex-Chess.git"

apt-get update
apt-get install -y ca-certificates curl git

install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.asc ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
fi

. /etc/os-release
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
git pull --ff-only

mkdir -p deploy
if [ ! -f deploy/bot.env ]; then
  cp deploy/bot.env.example deploy/bot.env
fi
if [ ! -f deploy/site.env ]; then
  cp deploy/site.env.example deploy/site.env
fi

echo "Bootstrap complete."
echo "Next: edit $APP_DIR/deploy/bot.env and $APP_DIR/deploy/site.env, then run:"
echo "cd $APP_DIR && docker compose up -d --build"
