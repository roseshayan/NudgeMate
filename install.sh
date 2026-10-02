#!/usr/bin/env bash

# ==============================================================================
# NudgeMate - Automated Installer for Ubuntu 24.04 LTS
# GitHub: https://github.com/roseshayan/NudgeMate
# ==============================================================================

set -e

# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

APP_DIR="/opt/nudgemate"
REPO_URL="https://github.com/roseshayan/NudgeMate.git"

clear
echo -e "${PURPLE}${BOLD}"
echo "================================================================="
echo "   _   _           _            __  __       _       "
echo "  | \ | |_   _  __| | __ _  ___|  \/  | __ _| |_ ___ "
echo "  |  \| | | | |/ _\` |/ _\` |/ _ \ |\/| |/ _\` | __/ _ \ "
echo "  | |\  | |_| | (_| | (_| |  __/ |  | | (_| | ||  __/ "
echo "  |_| \_|\__,_|\__,_|\__, |\___|_|  |_|\__,_|\__\___| "
echo "                     |___/                            "
echo "      AI-Powered Task Manager & Voice Reminder Bot       "
echo "================================================================="
echo -e "${NC}"
echo -e "${CYAN}Starting NudgeMate installation on Ubuntu 24.04...${NC}\n"

# 1. Check Root Privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Please run this script with root privileges or sudo:${NC}"
  echo "sudo bash install.sh"
  exit 1
fi

# 2. Update System Packages & Install Dependencies
echo -e "${BLUE}▶ Step 1/4: Installing required system dependencies...${NC}"

echo -e "${CYAN}  [1/4] Updating apt package lists...${NC}"
apt-get update

echo -e "${CYAN}  [2/4] Installing Python 3, pip, and venv...${NC}"
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv

echo -e "${CYAN}  [3/4] Installing FFMPEG (for voice message decoding)...${NC}"
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg

echo -e "${CYAN}  [4/4] Installing Git, Curl, and JQ...${NC}"
DEBIAN_FRONTEND=noninteractive apt-get install -y git curl jq

echo -e "${GREEN}✔ System dependencies installed successfully.${NC}\n"

# 3. Clone or Update Repository
echo -e "${BLUE}▶ Step 2/4: Preparing NudgeMate codebase...${NC}"
if [ -d "$APP_DIR/.git" ]; then
    echo -e "${YELLOW}  Directory $APP_DIR already exists. Pulling latest code...${NC}"
    cd "$APP_DIR"
    git fetch origin
    git reset --hard origin/main
else
    echo -e "${CYAN}  Cloning repository to $APP_DIR...${NC}"
    mkdir -p "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi
echo -e "${GREEN}✔ Codebase ready at $APP_DIR.${NC}\n"

# 4. Interactive Configuration & Validation
echo -e "${BOLD}====================================================="
echo -e "         Step 3/4: Configuration & Setup            "
echo -e "=====================================================${NC}\n"

# 4.1. Telegram Bot Token
while true; do
    echo -e "${CYAN}1. Enter your Telegram Bot Token:${NC}"
    echo -e "${YELLOW}(Obtain this from @BotFather, e.g. 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)${NC}"
    read -r -p "Telegram Bot Token: " TG_TOKEN < /dev/tty
    TG_TOKEN=$(echo "$TG_TOKEN" | xargs)

    if [ -z "$TG_TOKEN" ]; then
        echo -e "${RED}✖ Error: Bot token cannot be empty!${NC}\n"
        continue
    fi

    echo -e "${BLUE}Validating token with Telegram API...${NC}"
    TG_CHECK=$(curl -s "https://api.telegram.org/bot${TG_TOKEN}/getMe")
    IS_OK=$(echo "$TG_CHECK" | jq -r '.ok // false' 2>/dev/null || echo "false")

    if [ "$IS_OK" == "true" ]; then
        BOT_USERNAME=$(echo "$TG_CHECK" | jq -r '.result.username')
        BOT_NAME=$(echo "$TG_CHECK" | jq -r '.result.first_name')
        echo -e "${GREEN}✔ Valid token! Connected to: ${BOLD}${BOT_NAME} (@${BOT_USERNAME})${NC}\n"
        break
    else
        ERROR_DESC=$(echo "$TG_CHECK" | jq -r '.description // "Invalid bot token"' 2>/dev/null || echo "Invalid token")
        echo -e "${RED}✖ Verification failed: ${ERROR_DESC}${NC}"
        echo -e "${YELLOW}Please re-enter your bot token carefully.${NC}\n"
    fi
done

# 4.2. Admin Telegram Chat ID
while true; do
    echo -e "${CYAN}2. Enter Admin Telegram User ID (numeric):${NC}"
    echo -e "${YELLOW}(Send a message to @userinfobot on Telegram to get your numeric ID, e.g. 98765432)${NC}"
    read -r -p "Admin Telegram Chat ID: " ADMIN_ID < /dev/tty
    ADMIN_ID=$(echo "$ADMIN_ID" | xargs)

    if [[ "$ADMIN_ID" =~ ^[0-9]+$ ]] && [ "$ADMIN_ID" -gt 0 ]; then
        echo -e "${GREEN}✔ Admin ID verified: ${ADMIN_ID}${NC}\n"
        break
    else
        echo -e "${RED}✖ Error: Chat ID must be a positive integer!${NC}\n"
    fi
done

# 4.3. Dahl AI Configuration: Automatic Email Registration or Manual Key
echo -e "${CYAN}3. Configure Dahl AI Engine:${NC}"
echo -e "   ${BOLD}[1]${NC} ${GREEN}Automatic account creation with Email + 100M free tokens (Recommended 🌟)${NC}"
echo -e "   ${BOLD}[2]${NC} Enter existing Dahl API Key manually"

while true; do
    read -r -p "Select option [1/2] (Default: 1): " DAHL_CHOICE < /dev/tty
    DAHL_CHOICE=${DAHL_CHOICE:-1}

    if [ "$DAHL_CHOICE" == "1" ]; then
        # Automatic Signup via Email
        while true; do
            echo -e "\n${CYAN}Enter your email address to create Dahl AI account:${NC}"
            echo -e "${YELLOW}(Used to register your account and allocate 100M free tokens)${NC}"
            read -r -p "Email: " USER_EMAIL < /dev/tty
            USER_EMAIL=$(echo "$USER_EMAIL" | xargs)

            if [[ "$USER_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                echo -e "${BLUE}Registering account and allocating 100M tokens on Dahl Global...${NC}"
                
                AUTH_RESULT=$(python3 "$APP_DIR/nudgemate/utils/dahl_auth.py" "$USER_EMAIL" 2>/dev/null || true)
                AUTH_SUCCESS=$(echo "$AUTH_RESULT" | jq -r '.success // false' 2>/dev/null || echo "false")

                if [ "$AUTH_SUCCESS" == "true" ]; then
                    DAHL_KEY=$(echo "$AUTH_RESULT" | jq -r '.api_key')
                    DAHL_USER=$(echo "$AUTH_RESULT" | jq -r '.username')
                    DAHL_FP=$(echo "$AUTH_RESULT" | jq -r '.fingerprint')
                    DAHL_TOKENS=$(echo "$AUTH_RESULT" | jq -r '.allocated_tokens // 100000000')

                    echo -e "\n${GREEN}${BOLD}✔ Dahl AI account created successfully! 🎉${NC}"
                    echo -e "👤 Username: ${BOLD}${DAHL_USER}${NC}"
                    echo -e "🔑 API Key: ${BOLD}${DAHL_KEY:0:15}...${NC}"
                    echo -e "🎁 Allocated Tokens: ${BOLD}${DAHL_TOKENS}${NC}"
                    echo -e "🔐 Fingerprint (Your password for website login): ${YELLOW}${BOLD}${DAHL_FP}${NC}"
                    
                    cat <<CRED_EOF > "$APP_DIR/.dahl_credentials"
EMAIL=${USER_EMAIL}
USERNAME=${DAHL_USER}
FINGERPRINT=${DAHL_FP}
API_KEY=${DAHL_KEY}
ALLOCATED_TOKENS=${DAHL_TOKENS}
CRED_EOF
                    chmod 600 "$APP_DIR/.dahl_credentials"
                    echo -e "${CYAN}ℹ️ Credentials saved to ${APP_DIR}/.dahl_credentials${NC}\n"
                    break 2
                else
                    AUTH_ERR=$(echo "$AUTH_RESULT" | jq -r '.error // "Unknown connection error with Dahl server"')
                    echo -e "${RED}✖ Failed to create account automatically: ${AUTH_ERR}${NC}"
                    echo -e "${YELLOW}Would you like to try with another email? (y/n): ${NC}"
                    read -r -p "[y/n]: " RETRY_SIGNUP < /dev/tty
                    if [[ "$RETRY_SIGNUP" =~ ^[Nn] ]]; then
                        echo -e "${YELLOW}Switching to manual API Key entry...${NC}\n"
                        DAHL_CHOICE="2"
                        break
                    fi
                fi
            else
                echo -e "${RED}✖ Error: Invalid email format! Please enter a valid email address.${NC}"
            fi
        done
    fi

    if [ "$DAHL_CHOICE" == "2" ]; then
        # Manual API Key Input
        while true; do
            echo -e "\n${CYAN}Enter your Dahl Inference API Key:${NC}"
            echo -e "${YELLOW}(Copy your key from https://inference.dahl.global/account)${NC}"
            read -r -p "Dahl API Key: " DAHL_KEY < /dev/tty
            DAHL_KEY=$(echo "$DAHL_KEY" | xargs)

            if [ -z "$DAHL_KEY" ]; then
                echo -e "${RED}✖ Error: API key cannot be empty!${NC}\n"
                continue
            fi

            echo -e "${BLUE}Verifying API key with Dahl Global...${NC}"
            DAHL_CHECK=$(curl -s -m 10 "https://inference.dahl.global/tokens/current" -H "Authorization: Bearer ${DAHL_KEY}" || true)
            
            if echo "$DAHL_CHECK" | grep -q "available_tokens"; then
                AVAIL_TOKENS=$(echo "$DAHL_CHECK" | jq -r '.available_tokens // "available"')
                echo -e "${GREEN}✔ Valid Dahl Key! Allocated tokens: ${AVAIL_TOKENS}${NC}\n"
                break 2
            elif echo "$DAHL_CHECK" | grep -q "402"; then
                echo -e "${YELLOW}⚠ Key is valid but has 0 allocated tokens. Please allocate tokens from your pool at /account.${NC}\n"
                break 2
            else
                echo -e "${RED}✖ API Key is invalid or expired!${NC}"
                echo -e "${YELLOW}Would you like to re-enter your key? (y/n): ${NC}"
                read -r -p "[y/n]: " RETRY_KEY < /dev/tty
                if [[ "$RETRY_KEY" =~ ^[Nn] ]]; then
                    echo -e "${YELLOW}Continuing with entered key...${NC}\n"
                    break 2
                fi
            fi
        done
    else
        echo -e "${RED}✖ Please select either 1 or 2.${NC}"
    fi
done

# 4.4. Timezone Configuration
echo -e "${CYAN}4. Configure Server Timezone (Default: Asia/Tehran):${NC}"
read -r -p "Timezone [Asia/Tehran]: " USER_TZ < /dev/tty
USER_TZ=${USER_TZ:-Asia/Tehran}
echo -e "${GREEN}✔ Timezone set to: ${USER_TZ}${NC}\n"

# 4.5. Write .env file
echo -e "${BLUE}▶ Writing configuration to .env file...${NC}"
cat <<EOF > "$APP_DIR/.env"
TELEGRAM_BOT_TOKEN=${TG_TOKEN}
ADMIN_CHAT_ID=${ADMIN_ID}
DAHL_API_KEY=${DAHL_KEY}
DAHL_BASE_URL=https://inference.dahl.global/v1
DAHL_MODEL=MiniMaxAI/MiniMax-M2.7
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
TIMEZONE=${USER_TZ}
NAG_INTERVAL_MINUTES=15
MAX_NAG_COUNT=3
DAILY_BRIEFING_ENABLED=true
DAILY_BRIEFING_TIME=08:30
CHECK_UPDATES=true
UPDATE_CHECK_INTERVAL_HOURS=2
GITHUB_REPO=roseshayan/NudgeMate
DATABASE_PATH=data/nudgemate.db
TEMP_AUDIO_DIR=temp_audio
EOF

# 5. Setup Python Virtual Environment
echo -e "\n${BLUE}▶ Step 4/4: Setting up Python environment & systemd service...${NC}"
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    echo -e "${CYAN}  → Creating virtualenv in $APP_DIR/venv...${NC}"
    python3 -m venv venv
fi

echo -e "${CYAN}  → Upgrading pip...${NC}"
./venv/bin/pip install --upgrade pip

echo -e "${CYAN}  → Installing Python packages (faster-whisper, aiogram, openai, apscheduler)...${NC}"
echo -e "${YELLOW}    (Downloading packages and AI libraries, please wait)...${NC}"
./venv/bin/pip install -r requirements.txt
echo -e "${GREEN}✔ Python packages installed successfully.${NC}\n"

echo -e "${CYAN}  → Pre-downloading Whisper AI speech-to-text model (base)...${NC}"
./venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')" || true
echo -e "${GREEN}✔ Whisper AI speech model cached successfully.${NC}\n"

# 6. Setup Systemd Service
echo -e "${CYAN}  → Configuring systemd background service (nudgemate.service)...${NC}"
CURRENT_USER=$(logname 2>/dev/null || echo "$SUDO_USER")
if [ -z "$CURRENT_USER" ] || [ "$CURRENT_USER" == "root" ]; then
    CURRENT_USER="root"
fi

cat <<EOF > /etc/systemd/system/nudgemate.service
[Unit]
Description=NudgeMate AI Telegram Bot
After=network.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/python -m nudgemate.main
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
EnvironmentFile=${APP_DIR}/.env

[Install]
WantedBy=multi-user.target
EOF

# Permissions
chown -R "${CURRENT_USER}:${CURRENT_USER}" "$APP_DIR"
chmod +x "$APP_DIR/update.sh" "$APP_DIR/uninstall.sh" 2>/dev/null || true

systemctl daemon-reload
systemctl enable nudgemate.service
systemctl restart nudgemate.service

# 7. Global CLI Shortcuts
echo -e "${CYAN}  → Registering global CLI shortcuts (nudgemate, nudgemate-update)...${NC}"

cat << 'EOF' > /usr/local/bin/nudgemate-update
#!/usr/bin/env bash
bash /opt/nudgemate/update.sh
EOF
chmod +x /usr/local/bin/nudgemate-update

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
    *)
        echo "Usage: nudgemate {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF
chmod +x /usr/local/bin/nudgemate

echo -e "\n${GREEN}${BOLD}================================================================="
echo "       🎉 Congratulations! NudgeMate is installed & active!     "
echo "=================================================================${NC}"
echo -e "${CYAN}Open your Telegram app and send /start to your bot:${NC}"
echo -e "👉 ${BOLD}https://t.me/${BOT_USERNAME}${NC}\n"
echo -e "${PURPLE}Useful Terminal Commands:${NC}"
echo -e " • ${BOLD}nudgemate status${NC}   : Check service status"
echo -e " • ${BOLD}nudgemate logs${NC}     : View live logs & events"
echo -e " • ${BOLD}nudgemate restart${NC}  : Restart the bot"
echo -e " • ${BOLD}nudgemate-update${NC}   : Pull latest GitHub release\n"
