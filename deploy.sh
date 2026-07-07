#!/bin/bash
set -e

# Branch to deploy. Override with: BRANCH=some/branch bash deploy.sh
BRANCH="${BRANCH:-claude/elegant-cori-n1rsvu}"

echo "=========================================="
echo "  AI Realtor Doc Generator - Deployment"
echo "  Branch: $BRANCH"
echo "=========================================="

# 1. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[1/4] Installing Docker..."
    apt-get update
    apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo "Docker installed successfully."
else
    echo "[1/4] Docker already installed. Skipping."
fi

# 2. Set up project directory
APP_DIR="/opt/realtor-bot"
echo "[2/4] Setting up project in $APP_DIR..."

if [ -d "$APP_DIR" ]; then
    echo "Directory exists. Pulling latest changes..."
    cd "$APP_DIR"
    git fetch origin "$BRANCH"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    echo "Enter your GitHub Personal Access Token (create one at github.com/settings/tokens):"
    read -s GH_TOKEN
    git clone https://${GH_TOKEN}@github.com/rayrocket-ai/claudecode.git "$APP_DIR"
    cd "$APP_DIR"
    git checkout "$BRANCH"
fi

# 3. Set up .env if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[3/4] Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env with your credentials:"
    echo "  nano $APP_DIR/.env"
    echo ""
    echo "Required values:"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - REALM_USERNAME & REALM_PASSWORD"
    echo "  - BROKERAGE_NAME, PHONE, EMAIL, ADDRESS"
    echo ""
    read -p "Press Enter after you've edited .env, or Ctrl+C to edit later..."
else
    echo "[3/4] .env already exists. Skipping."
fi

# 3b. Auto-generate a dashboard token if none is set yet
if ! grep -q "^DASHBOARD_TOKEN=..*" "$APP_DIR/.env"; then
    DASH_TOKEN=$(openssl rand -hex 24)
    if grep -q "^DASHBOARD_TOKEN=" "$APP_DIR/.env"; then
        sed -i "s/^DASHBOARD_TOKEN=.*/DASHBOARD_TOKEN=${DASH_TOKEN}/" "$APP_DIR/.env"
    else
        printf "\nDASHBOARD_TOKEN=%s\n" "$DASH_TOKEN" >> "$APP_DIR/.env"
    fi
    echo "Generated a dashboard access token."
else
    DASH_TOKEN=$(grep "^DASHBOARD_TOKEN=" "$APP_DIR/.env" | head -1 | cut -d= -f2-)
fi

# 4. Build and run
echo "[4/4] Building and starting the bot..."
cd "$APP_DIR"
mkdir -p storage
docker compose down 2>/dev/null || true
docker compose up -d --build

SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
DASH_PORT=$(grep "^DASHBOARD_PORT=" "$APP_DIR/.env" 2>/dev/null | head -1 | cut -d= -f2-)
DASH_PORT="${DASH_PORT:-8000}"

echo ""
echo "=========================================="
echo "  Deployment complete!"
echo "=========================================="
echo ""
if [ -n "$DASH_TOKEN" ]; then
    echo "Deal dashboard:"
    echo "  http://${SERVER_IP:-<server-ip>}:${DASH_PORT}/?token=${DASH_TOKEN}"
    echo "  (If unreachable, allow port ${DASH_PORT} in your Hetzner Cloud"
    echo "   Firewall / ufw. Keep the token secret — it grants read access"
    echo "   to all deal data.)"
    echo ""
fi
echo "Useful commands:"
echo "  View logs:    docker compose -f $APP_DIR/docker-compose.yml logs -f"
echo "  Stop:         docker compose -f $APP_DIR/docker-compose.yml down"
echo "  Restart:      docker compose -f $APP_DIR/docker-compose.yml restart"
echo "  Edit config:  nano $APP_DIR/.env"
echo ""
