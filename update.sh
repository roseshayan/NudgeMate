#!/usr/bin/env bash

# ==============================================================================
# NudgeMate - One-Click Updater Script
# ==============================================================================

set -e

# ANSI Color Codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\n${CYAN}${BOLD}▶ Starting NudgeMate update process...${NC}"

OLD_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo -e "${YELLOW}Current Version: ${OLD_COMMIT}${NC}"

# 1. Fetch and reset to latest remote main
echo -e "${BLUE}▶ Fetching latest changes from GitHub...${NC}"
git fetch origin main
git reset --hard origin/main

NEW_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo -e "${GREEN}New Version Downloaded: ${NEW_COMMIT}${NC}"

# 2. Update Python dependencies if needed
if [ -d "venv" ]; then
    echo -e "${BLUE}▶ Updating Python dependencies & fixing package versions...${NC}"
    ./venv/bin/pip install -r requirements.txt
    
    echo -e "${BLUE}▶ Verifying Whisper speech-to-text AI model cache...${NC}"
    ./venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')" 2>/dev/null || true
fi

# 3. Ensure permissions
chmod +x install.sh update.sh uninstall.sh 2>/dev/null || true

# 4. Restart systemd service if running
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet nudgemate 2>/dev/null; then
    echo -e "${BLUE}▶ Restarting nudgemate systemd service...${NC}"
    if [ "$EUID" -eq 0 ]; then
        systemctl daemon-reload
        systemctl restart nudgemate
    else
        sudo systemctl daemon-reload
        sudo systemctl restart nudgemate
    fi
    echo -e "${GREEN}✔ NudgeMate service restarted successfully.${NC}"
fi

echo -e "\n${GREEN}${BOLD}✔ Update completed successfully! (${OLD_COMMIT} -> ${NEW_COMMIT})${NC}\n"
