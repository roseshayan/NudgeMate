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
  echo -e "${RED}[ERROR] Please run this script with root or sudo privileges.${NC}"
  exit 1
fi

echo -e "${YELLOW}${BOLD}Are you sure you want to completely uninstall NudgeMate? (y/n)${NC}"
read -r -p "[y/n]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
    echo "Uninstallation canceled."
    exit 0
fi

echo -e "\nStopping and disabling systemd service..."
systemctl stop nudgemate 2>/dev/null || true
systemctl disable nudgemate 2>/dev/null || true
rm -f /etc/systemd/system/nudgemate.service
systemctl daemon-reload

echo "Removing CLI command shortcuts..."
rm -f /usr/local/bin/nudgemate
rm -f /usr/local/bin/nudgemate-update

echo -e "${YELLOW}Would you also like to delete data & database in /opt/nudgemate? (y/n)${NC}"
read -r -p "[y/n]: " DEL_DATA
if [[ "$DEL_DATA" =~ ^[Yy] ]]; then
    rm -rf /opt/nudgemate
    echo "Directory /opt/nudgemate has been removed."
fi

echo -e "\n${GREEN}✔ NudgeMate has been cleanly uninstalled from your server.${NC}"
