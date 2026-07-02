#!/bin/bash
set -e

echo "=========================================="
echo "  AI Realtor Doc Generator - Deployment"
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

REPO_URL="https://github.com/rayrocket-ai/claudecode.git"
BRANCH="claude/ai-realtor-doc-generator-ov4Xa"

if [ -d "$APP_DIR" ]; then
    echo "Directory exists. Pulling latest changes..."
    cd "$APP_DIR"
    if ! git pull origin "$BRANCH"; then
        # Private repo — ask for a token but use it only for this one
        # fetch so it is never written to .git/config
        echo "Enter your GitHub Personal Access Token (create one at github.com/settings/tokens):"
        read -s GH_TOKEN
        git pull "https://${GH_TOKEN}@github.com/rayrocket-ai/claudecode.git" "$BRANCH"
        unset GH_TOKEN
    fi
else
    echo "Enter your GitHub Personal Access Token (create one at github.com/settings/tokens):"
    read -s GH_TOKEN
    git clone --branch "$BRANCH" "https://${GH_TOKEN}@github.com/rayrocket-ai/claudecode.git" "$APP_DIR"
    cd "$APP_DIR"
    # Strip the token from the persisted remote URL
    git remote set-url origin "$REPO_URL"
    unset GH_TOKEN
fi

# 3. Set up .env if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[3/4] Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env with your credentials:"
    echo "  nano /opt/realtor-bot/.env"
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

# 4. Build and run
echo "[4/4] Building and starting the bot..."
cd "$APP_DIR"
mkdir -p storage
docker compose down 2>/dev/null || true
docker compose up -d --build

echo ""
echo "=========================================="
echo "  Deployment complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  View logs:    docker compose -f $APP_DIR/docker-compose.yml logs -f"
echo "  Stop bot:     docker compose -f $APP_DIR/docker-compose.yml down"
echo "  Restart bot:  docker compose -f $APP_DIR/docker-compose.yml restart"
echo "  Edit config:  nano $APP_DIR/.env"
echo ""
