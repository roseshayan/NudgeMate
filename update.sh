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

echo -e "\n${CYAN}${BOLD}▶ در حال شروع فرآیند بروزرسانی NudgeMate...${NC}"

OLD_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo -e "${YELLOW}نسخه فعلی: ${OLD_COMMIT}${NC}"

# 1. Fetch and reset to latest remote main
echo -e "${BLUE}▶ در حال دریافت آخرین تغییرات از گیت‌هاب...${NC}"
git fetch origin main
git reset --hard origin/main

NEW_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo -e "${GREEN}نسخه جدید دریافت شده: ${NEW_COMMIT}${NC}"

# 2. Update Python dependencies if needed
if [ -d "venv" ]; then
    echo -e "${BLUE}▶ در حال بررسی و بروزرسانی پکیج‌های پایتون...${NC}"
    ./venv/bin/pip install -r requirements.txt -q
fi

# 3. Ensure permissions
chmod +x install.sh update.sh 2>/dev/null || true

# 4. Restart systemd service if running
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet nudgemate 2>/dev/null; then
    echo -e "${BLUE}▶ در حال راه‌اندازی مجدد سرویس nudgemate...${NC}"
    if [ "$EUID" -eq 0 ]; then
        systemctl daemon-reload
        systemctl restart nudgemate
    else
        sudo systemctl daemon-reload
        sudo systemctl restart nudgemate
    fi
    echo -e "${GREEN}✔ سرویس با موفقیت ری‌استارت شد.${NC}"
fi

echo -e "\n${GREEN}${BOLD}✔ بروزرسانی با موفقیت به پایان رسید! (از ${OLD_COMMIT} به ${NEW_COMMIT})${NC}\n"
