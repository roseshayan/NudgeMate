#!/usr/bin/env bash

# ==============================================================================
# NudgeMate - Uninstaller Script
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] لطفاً این اسکریپت را با sudo یا root اجرا کنید.${NC}"
  exit 1
fi

echo -e "${YELLOW}${BOLD}آیا از حذف کامل NudgeMate مطمئن هستید؟ (y/n)${NC}"
read -r -p "[y/n]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
    echo "عملیات لغو شد."
    exit 0
fi

echo -e "\nدر حال متوقف کردن و حذف سرویس systemd..."
systemctl stop nudgemate 2>/dev/null || true
systemctl disable nudgemate 2>/dev/null || true
rm -f /etc/systemd/system/nudgemate.service
systemctl daemon-reload

echo "در حال حذف دستورات میانبر..."
rm -f /usr/local/bin/nudgemate
rm -f /usr/local/bin/nudgemate-update

echo -e "${YELLOW}آیا مایل به حذف داده‌ها و دیتابیس در /opt/nudgemate هستید؟ (y/n)${NC}"
read -r -p "[y/n]: " DEL_DATA
if [[ "$DEL_DATA" =~ ^[Yy] ]]; then
    rm -rf /opt/nudgemate
    echo "دایرکتوری /opt/nudgemate حذف شد."
fi

echo -e "\n${GREEN}✔ NudgeMate با موفقیت از سرور شما پاکسازی شد.${NC}"
