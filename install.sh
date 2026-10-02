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
echo "        دستیار هوشمند مدیریت تسک و یادآوری پیگیر        "
echo "================================================================="
echo -e "${NC}"
echo -e "${CYAN}شروع فرآیند نصب و راه‌اندازی NudgeMate روی اوبونتو 24...${NC}\n"

# 1. Check Root Privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] لطفاً این اسکریپت را با دسترسی root یا sudo اجرا کنید:${NC}"
  echo "sudo bash install.sh"
  exit 1
fi

# 2. Update System Packages & Install Dependencies
echo -e "${BLUE}▶ در حال بررسی و نصب پیش‌نیازهای سیستمی (Python3, FFMPEG, Git, Curl)...${NC}"
apt-get update -qq
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    git \
    curl \
    jq > /dev/null

echo -e "${GREEN}✔ پیش‌نیازهای سیستمی با موفقیت نصب شدند.${NC}\n"

# 3. Clone or Update Repository
if [ -d "$APP_DIR/.git" ]; then
    echo -e "${YELLOW}پوشه $APP_DIR از قبل موجود است. در حال دریافت آخرین نسخه...${NC}"
    cd "$APP_DIR"
    git fetch origin
    git reset --hard origin/main
else
    echo -e "${BLUE}▶ در حال دانلود سورس کد NudgeMate از گیت‌هاب...${NC}"
    mkdir -p "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

echo -e "\n${BOLD}====================================================="
echo -e "       مرحله پیکربندی و اعتبارسنجی ورودی‌ها         "
echo -e "=====================================================${NC}\n"

# 4. Strict Validation: Telegram Bot Token
while true; do
    echo -e "${CYAN}۱. لطفاً توکن ربات تلگرام خود را وارد کنید:${NC}"
    echo -e "${YELLOW}(توکن دریافتی از @BotFather به فرمت 123456:ABC-DEF...)${NC}"
    read -r -p "Telegram Bot Token: " TG_TOKEN
    TG_TOKEN=$(echo "$TG_TOKEN" | xargs)

    if [ -z "$TG_TOKEN" ]; then
        echo -e "${RED}✖ خطا: توکن نمی‌تواند خالی باشد!${NC}\n"
        continue
    fi

    echo -e "${BLUE}در حال بررسی صحت توکن در سرور تلگرام...${NC}"
    TG_CHECK=$(curl -s "https://api.telegram.org/bot${TG_TOKEN}/getMe")
    IS_OK=$(echo "$TG_CHECK" | jq -r '.ok // false')

    if [ "$IS_OK" == "true" ]; then
        BOT_USERNAME=$(echo "$TG_CHECK" | jq -r '.result.username')
        BOT_NAME=$(echo "$TG_CHECK" | jq -r '.result.first_name')
        echo -e "${GREEN}✔ توکن معتبر است! نام ربات: ${BOLD}${BOT_NAME} (@${BOT_USERNAME})${NC}\n"
        break
    else
        ERROR_DESC=$(echo "$TG_CHECK" | jq -r '.description // "توکن وارد شده معتبر نیست"')
        echo -e "${RED}✖ خطا در اعتبارسنجی: ${ERROR_DESC}${NC}"
        echo -e "${YELLOW}لطفاً توکن را مجدداً با دقت وارد کنید.${NC}\n"
    fi
done

# 5. Strict Validation: Admin Telegram ID
while true; do
    echo -e "${CYAN}۲. لطفاً شناسه عددی (Chat ID) تلگرام مدیر را وارد کنید:${NC}"
    echo -e "${YELLOW}(می‌توانید با ارسال پیام به ربات @userinfobot یا @userinfobot شناسه‌تان را ببینید، مثلاً 98765432)${NC}"
    read -r -p "Admin Telegram Chat ID: " ADMIN_ID
    ADMIN_ID=$(echo "$ADMIN_ID" | xargs)

    if [[ "$ADMIN_ID" =~ ^[0-9]+$ ]] && [ "$ADMIN_ID" -gt 0 ]; then
        echo -e "${GREEN}✔ شناسه کاربری تایید شد: ${ADMIN_ID}${NC}\n"
        break
    else
        echo -e "${RED}✖ خطا: شناسه تلگرام باید یک مقدار عددی صحیح و بزرگتر از صفر باشد!${NC}\n"
    fi
done

# 6. Dahl AI Configuration: Automatic Email Registration or Manual Key
echo -e "${CYAN}۳. نحوه تنظیم هوش مصنوعی Dahl:${NC}"
echo -e "   ${BOLD}[1]${NC} ${GREEN}ساخت خودکار اکانت Dahl با ایمیل و تخصیص ۱۰۰ میلیون توکن هدیه (پیشنهادی 🌟)${NC}"
echo -e "   ${BOLD}[2]${NC} وارد کردن کلید API به صورت دستی (اگر از قبل اکانت دارید)"

while true; do
    read -r -p "گزینه مورد نظر را انتخاب کنید [1/2] (پیش‌فرض: 1): " DAHL_CHOICE
    DAHL_CHOICE=${DAHL_CHOICE:-1}

    if [ "$DAHL_CHOICE" == "1" ]; then
        # Automatic Signup via Email
        while true; do
            echo -e "\n${CYAN}لطفاً ایمیل خود را برای ساخت اکانت وارد کنید:${NC}"
            echo -e "${YELLOW}(برای ساخت شناسه و ثبت در سیستم هوش مصنوعی استفاده می‌شود)${NC}"
            read -r -p "Email: " USER_EMAIL
            USER_EMAIL=$(echo "$USER_EMAIL" | xargs)

            if [[ "$USER_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                echo -e "${BLUE}در حال ساخت خودکار اکانت و اختصاص ۱۰۰ میلیون توکن در Dahl Global...${NC}"
                
                # Execute Python auth helper
                AUTH_RESULT=$(python3 "$APP_DIR/nudgemate/utils/dahl_auth.py" "$USER_EMAIL" 2>/dev/null || true)
                AUTH_SUCCESS=$(echo "$AUTH_RESULT" | jq -r '.success // false' 2>/dev/null || echo "false")

                if [ "$AUTH_SUCCESS" == "true" ]; then
                    DAHL_KEY=$(echo "$AUTH_RESULT" | jq -r '.api_key')
                    DAHL_USER=$(echo "$AUTH_RESULT" | jq -r '.username')
                    DAHL_FP=$(echo "$AUTH_RESULT" | jq -r '.fingerprint')
                    DAHL_TOKENS=$(echo "$AUTH_RESULT" | jq -r '.allocated_tokens // 100000000')

                    echo -e "\n${GREEN}${BOLD}✔ اکانت هوش مصنوعی شما با موفقیت ساخته شد! 🎉${NC}"
                    echo -e "👤 نام کاربری: ${BOLD}${DAHL_USER}${NC}"
                    echo -e "🔑 کلید API: ${BOLD}${DAHL_KEY:0:15}...${NC}"
                    echo -e "🎁 توکن‌های اختصاص‌یافته: ${BOLD}${DAHL_TOKENS}${NC}"
                    echo -e "🔐 اثر انگشت (کلمه عبور جهت ورود به سایت): ${YELLOW}${BOLD}${DAHL_FP}${NC}"
                    
                    # Save credentials securely to a hidden file
                    cat <<CRED_EOF > "$APP_DIR/.dahl_credentials"
EMAIL=${USER_EMAIL}
USERNAME=${DAHL_USER}
FINGERPRINT=${DAHL_FP}
API_KEY=${DAHL_KEY}
ALLOCATED_TOKENS=${DAHL_TOKENS}
CRED_EOF
                    chmod 600 "$APP_DIR/.dahl_credentials"
                    echo -e "${CYAN}ℹ️ این مشخصات در فایل ${APP_DIR}/.dahl_credentials ذخیره شد.${NC}\n"
                    break 2
                else
                    AUTH_ERR=$(echo "$AUTH_RESULT" | jq -r '.error // "خطای ناشناخته در ارتباط با سرور Dahl"')
                    echo -e "${RED}✖ خطا در ساخت خودکار اکانت: ${AUTH_ERR}${NC}"
                    echo -e "${YELLOW}آیا می‌خواهید با ایمیل دیگری امتحان کنید؟ (y/n): ${NC}"
                    read -r -p "[y/n]: " RETRY_SIGNUP
                    if [[ "$RETRY_SIGNUP" =~ ^[Nn] ]]; then
                        echo -e "${YELLOW}تغییر به حالت وارد کردن دستی کلید API...${NC}\n"
                        DAHL_CHOICE="2"
                        break
                    fi
                fi
            else
                echo -e "${RED}✖ خطا: فرمت ایمیل نامعتبر است! لطفاً ایمیل صحیح وارد کنید.${NC}"
            fi
        done
    fi

    if [ "$DAHL_CHOICE" == "2" ]; then
        # Manual API Key Input
        while true; do
            echo -e "\n${CYAN}لطفاً کلید API سرویس Dahl Inference را وارد کنید:${NC}"
            echo -e "${YELLOW}(از سایت https://inference.dahl.global/account کلید را کپی کنید)${NC}"
            read -r -p "Dahl API Key: " DAHL_KEY
            DAHL_KEY=$(echo "$DAHL_KEY" | xargs)

            if [ -z "$DAHL_KEY" ]; then
                echo -e "${RED}✖ خطا: کلید API نمی‌تواند خالی باشد!${NC}\n"
                continue
            fi

            echo -e "${BLUE}در حال بررسی اعتبار کلید API در سرویس Dahl...${NC}"
            DAHL_CHECK=$(curl -s -m 10 "https://inference.dahl.global/tokens/current" -H "Authorization: Bearer ${DAHL_KEY}" || true)
            
            if echo "$DAHL_CHECK" | grep -q "available_tokens"; then
                AVAIL_TOKENS=$(echo "$DAHL_CHECK" | jq -r '.available_tokens // "موجود"')
                echo -e "${GREEN}✔ کلید Dahl معتبر است! توکن‌های تخصیص‌یافته: ${AVAIL_TOKENS}${NC}\n"
                break 2
            elif echo "$DAHL_CHECK" | grep -q "402"; then
                echo -e "${YELLOW}⚠ کلید معتبر است اما موجودی توکن آن 0 است. بعد از نصب می‌توانید در سایت به کلید توکن اختصاص دهید.${NC}\n"
                break 2
            else
                echo -e "${RED}✖ کلید API وارد شده معتبر نیست یا سرور در دسترس نیست!${NC}"
                echo -e "${YELLOW}آیا می‌خواهید دوباره وارد کنید؟ (y/n): ${NC}"
                read -r -p "[y/n]: " RETRY_KEY
                if [[ "$RETRY_KEY" =~ ^[Nn] ]]; then
                    echo -e "${YELLOW}استفاده از کلید وارد شده ادامه می‌یابد.${NC}\n"
                    break 2
                fi
            fi
        done
    else
        echo -e "${RED}✖ لطفاً عدد 1 یا 2 را انتخاب کنید.${NC}"
    fi
done

# 7. Timezone Configuration
echo -e "${CYAN}۴. منطقه زمانی (پیش‌فرض: Asia/Tehran):${NC}"
read -r -p "Timezone [Asia/Tehran]: " USER_TZ
USER_TZ=${USER_TZ:-Asia/Tehran}
echo -e "${GREEN}✔ منطقه زمانی تنظیم شد: ${USER_TZ}${NC}\n"

# 8. Create .env file
echo -e "${BLUE}▶ در حال ذخیره تنظیمات در فایل .env...${NC}"
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

# 9. Setup Python Virtual Environment
echo -e "${BLUE}▶ در حال راه‌اندازی محیط مجازی پایتون (venv) و نصب پکیج‌ها...${NC}"
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q
echo -e "${GREEN}✔ پکیج‌های پایتون با موفقیت نصب شدند.${NC}\n"

# 10. Setup Systemd Service
echo -e "${BLUE}▶ در حال تنظیم سرویس خودکار systemd...${NC}"
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

# Ensure permissions
chown -R "${CURRENT_USER}:${CURRENT_USER}" "$APP_DIR"
chmod +x "$APP_DIR/update.sh" 2>/dev/null || true

systemctl daemon-reload
systemctl enable nudgemate.service
systemctl restart nudgemate.service

# 11. Create Quick CLI Shortcuts
echo -e "${BLUE}▶ در حال ایجاد دستورات تک‌خطی در سیستم...${NC}"

# nudgemate-update command
cat << 'EOF' > /usr/local/bin/nudgemate-update
#!/usr/bin/env bash
bash /opt/nudgemate/update.sh
EOF
chmod +x /usr/local/bin/nudgemate-update

# nudgemate management command
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
echo "       🎉 تبریک! NudgeMate با موفقیت نصب و فعال شد!             "
echo "=================================================================${NC}"
echo -e "${CYAN}همین الان می‌توانید وارد ربات تلگرام خود شوید و دکمه /start را بزنید:${NC}"
echo -e "👉 ${BOLD}https://t.me/${BOT_USERNAME}${NC}\n"
echo -e "${PURPLE}دستورات مفید ترمینال:${NC}"
echo -e " • ${BOLD}nudgemate status${NC}   : بررسی وضعیت سرویس"
echo -e " • ${BOLD}nudgemate logs${NC}     : مشاهده زنده لاگ‌ها و پیام‌ها"
echo -e " • ${BOLD}nudgemate restart${NC}  : راه‌اندازی مجدد ربات"
echo -e " • ${BOLD}nudgemate-update${NC}   : بروزرسانی مستقیم به آخرین نسخه گیت‌هاب\n"
