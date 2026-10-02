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

# 3. Synchronize .env configuration with new variables
if [ -f ".env" ]; then
    echo -e "${BLUE}▶ Checking and synchronizing configuration (.env)...${NC}"
    
    # Auto-add missing keys from new features
    if ! grep -q "^MELIPAYAMAK_API_TOKEN=" .env 2>/dev/null; then
        echo "MELIPAYAMAK_API_TOKEN=0cd932c7f08946509b95519513bbc4be" >> .env
        echo -e "${YELLOW}  + Added default MELIPAYAMAK_API_TOKEN to .env${NC}"
    fi
    if ! grep -q "^MELIPAYAMAK_FROM_NUMBER=" .env 2>/dev/null; then
        echo "MELIPAYAMAK_FROM_NUMBER=" >> .env
    fi
    if ! grep -q "^MELIPAYAMAK_SHARED_BODY_ID=" .env 2>/dev/null; then
        echo "MELIPAYAMAK_SHARED_BODY_ID=0" >> .env
    fi
    if ! grep -q "^REQUIRED_CHANNEL=" .env 2>/dev/null; then
        echo "REQUIRED_CHANNEL=" >> .env
        echo -e "${YELLOW}  + Added REQUIRED_CHANNEL to .env${NC}"
    fi
    if ! grep -q "^CHANNEL_INVITE_LINK=" .env 2>/dev/null; then
        echo "CHANNEL_INVITE_LINK=" >> .env
    fi

    # Interactive prompt if running inside an interactive terminal
    if [ -t 0 ] && [ -e /dev/tty ]; then
        echo -e "\n${CYAN}⚙️  Check New Configuration Options:${NC}"
        CUR_MELI=$(grep "^MELIPAYAMAK_API_TOKEN=" .env 2>/dev/null | cut -d '=' -f2-)
        CUR_CHAN=$(grep "^REQUIRED_CHANNEL=" .env 2>/dev/null | cut -d '=' -f2-)
        echo -e " • MeliPayamak SMS Token : ${YELLOW}${CUR_MELI:-Not set}${NC}"
        echo -e " • Mandatory Channel     : ${YELLOW}${CUR_CHAN:-None (Disabled)}${NC}"
        
        read -r -t 15 -p "Do you want to update SMS Token or Channel settings now? (y/N): " EDIT_CONF < /dev/tty || true
        if [[ "$EDIT_CONF" =~ ^[Yy]$ ]]; then
            read -r -p "Enter MeliPayamak API Token [Press enter to keep current]: " NEW_TOKEN < /dev/tty || true
            NEW_TOKEN=$(echo "$NEW_TOKEN" | xargs)
            if [ -n "$NEW_TOKEN" ]; then
                sed -i "s|^MELIPAYAMAK_API_TOKEN=.*|MELIPAYAMAK_API_TOKEN=${NEW_TOKEN}|" .env
                echo -e "${GREEN}✔ MeliPayamak Token updated.${NC}"
            fi

            read -r -p "Enter Mandatory Telegram Channel (e.g. @MyChannel or empty to disable) [Press enter to keep]: " NEW_CHAN < /dev/tty || true
            NEW_CHAN=$(echo "$NEW_CHAN" | xargs)
            if [ -n "$NEW_CHAN" ]; then
                if [ "$NEW_CHAN" == "none" ] || [ "$NEW_CHAN" == "off" ]; then
                    sed -i "s|^REQUIRED_CHANNEL=.*|REQUIRED_CHANNEL=|" .env
                    echo -e "${GREEN}✔ Mandatory Channel disabled.${NC}"
                else
                    sed -i "s|^REQUIRED_CHANNEL=.*|REQUIRED_CHANNEL=${NEW_CHAN}|" .env
                    echo -e "${GREEN}✔ Mandatory Channel set to ${NEW_CHAN}.${NC}"
                fi
            fi
        fi
    fi
fi

# 4. Ensure permissions & refresh CLI shortcut
chmod +x install.sh update.sh uninstall.sh 2>/dev/null || true

if [ -f "/usr/local/bin/nudgemate" ] && [ "$EUID" -eq 0 ]; then
    cat << 'EOF' > /usr/local/bin/nudgemate
#!/usr/bin/env bash
case "$1" in
    start)
        sudo systemctl start nudgemate
        echo "NudgeMate started."
        ;;
    stop)
        sudo systemctl stop nudgemate
        echo "NudgeMate stopped."
        ;;
    restart)
        sudo systemctl restart nudgemate
        echo "NudgeMate restarted."
        ;;
    status)
        sudo systemctl status nudgemate
        ;;
    logs)
        sudo journalctl -u nudgemate -f -n 50
        ;;
    update)
        bash /opt/nudgemate/update.sh
        ;;
    config)
        sudo nano /opt/nudgemate/.env
        echo "Restarting NudgeMate to apply changes..."
        sudo systemctl restart nudgemate
        ;;
    *)
        echo "Usage: nudgemate {start|stop|restart|status|logs|update|config}"
        exit 1
        ;;
esac
EOF
    chmod +x /usr/local/bin/nudgemate 2>/dev/null || true
fi

# 5. Restart systemd service if running
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

echo -e "\n${GREEN}${BOLD}✔ Update completed successfully! (${OLD_COMMIT} -> ${NEW_COMMIT})${NC}"
echo -e "${CYAN}💡 Tip: Use 'nudgemate config' to edit tokens or settings anytime.${NC}\n"
