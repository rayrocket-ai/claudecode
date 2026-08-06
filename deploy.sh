#!/usr/bin/env bash
# One-command deploy for a fresh Hetzner box (Ubuntu/Debian).
# Idempotent: safe to re-run.
#
# Usage on the box:
#   git clone https://github.com/rayrocket-ai/claudecode.git ~/claudecode
#   cd ~/claudecode
#   cp .env.example .env  &&  nano .env    # fill in secrets + DOMAIN
#   ./deploy.sh

set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
    echo "❌  No .env file. Run: cp .env.example .env  &&  nano .env"
    exit 1
fi

# Sanity-check the vars Docker/Caddy actually need.
source .env
: "${DOMAIN:?DOMAIN not set in .env}"
: "${VAPI_SECRET:?VAPI_SECRET not set in .env}"
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY not set in .env}"

if ! command -v docker >/dev/null 2>&1; then
    echo "→ Installing Docker Engine"
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "${USER}" || true
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "❌  'docker compose' plugin missing. Install docker-compose-plugin from your distro's docker repo."
    exit 1
fi

mkdir -p data

echo "→ Building app image"
docker compose build

echo "→ Starting containers"
docker compose up -d

echo
echo "✅  Up. Point https://${DOMAIN}/health at Vapi's server URL as:"
echo "     https://${DOMAIN}/voice/vapi/webhook"
echo
echo "Tail logs:  docker compose logs -f app caddy"
