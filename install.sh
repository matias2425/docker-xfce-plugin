#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# Docker XFCE Panel Plugin - Installer & Configuration Guide
# -----------------------------------------------------------------------------

# Colors for premium console output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}${BOLD}========================================================"
echo -e "      🐳 Docker XFCE Panel Plugin Installer"
echo -e "========================================================${NC}\n"

# 1. Check if xfce4-genmon-plugin is installed
echo -e "${CYAN}[1/4] Checking xfce4-genmon-plugin...${NC}"
if pacman -Qs xfce4-genmon-plugin >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ xfce4-genmon-plugin is already installed.${NC}"
else
    echo -e "  ${YELLOW}⚠ xfce4-genmon-plugin is not installed.${NC}"
    echo -e "  Trying to install with pacman..."
    sudo pacman -S --needed --noconfirm xfce4-genmon-plugin
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ xfce4-genmon-plugin installed successfully.${NC}"
    else
        echo -e "  ${RED}✗ Could not install xfce4-genmon-plugin automatically.${NC}"
        echo -e "    Please install it manually by running: ${BOLD}sudo pacman -S xfce4-genmon-plugin${NC}"
        exit 1
    fi
fi
echo ""

# 2. Check Docker access
echo -e "${CYAN}[2/4] Checking Docker access...${NC}"
if docker ps >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Successfully connected to the Docker daemon.${NC}"
else
    echo -e "  ${RED}✗ Cannot access the Docker socket.${NC}"
    echo -e "    Is the Docker service running? (systemctl start docker)"
    echo -e "    Does your user belong to the 'docker' group?"
    echo -e "    To add your user to the docker group, run:"
    echo -e "      ${BOLD}sudo usermod -aG docker \$USER${NC}"
    echo -e "    and then restart your session."
    echo -e "    ${YELLOW}Continuing with the installation anyway...${NC}"
fi
echo ""

# 3. Configure file permissions
echo -e "${CYAN}[3/4] Setting execution permissions...${NC}"
chmod +x docker_genmon.sh docker_menu.py
echo -e "  ${GREEN}✓ docker_genmon.sh and docker_menu.py set as executable.${NC}"
echo ""

# 4. Instructions for XFCE Panel
echo -e "${BLUE}${BOLD}========================================================"
echo -e "      ⚙️  STEPS TO ADD THE PLUGIN TO THE XFCE PANEL"
echo -e "========================================================${NC}"
echo -e "To add the plugin to your panel, follow these steps:"
echo -e "  1. Right-click on an empty area of your XFCE panel."
echo -e "  2. Select ${BOLD}Panel -> Add New Items...${NC}"
echo -e "  3. Search for ${CYAN}Generic Monitor${NC} and click ${BOLD}Add${NC}."
echo -e "  4. Right-click on the new plugin in your panel and select ${BOLD}Properties${NC}."
echo -e "  5. Configure the following fields:"
echo -e "     • ${BOLD}Command:${NC} $(pwd)/docker_genmon.sh"
echo -e "     • ${BOLD}Period (s):${NC} 10"
echo -e "     • ${BOLD}Label:${NC} Uncheck / Disable (to show only the icon)"
echo -e "  6. Click ${BOLD}Close${NC}."
echo -e "${BLUE}========================================================${NC}\n"

# Verify if we should run a test
echo -e "${CYAN}[4/4] Do you want to test the interactive Dashboard now?${NC}"
read -p "Press ENTER to open the test dashboard, or Ctrl+C to exit..."

echo -e "Launching test dashboard..."
./docker_menu.py
echo -e "${GREEN}✓ Test run complete.${NC}"
