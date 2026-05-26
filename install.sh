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
echo -e "${CYAN}[1/4] Verificando xfce4-genmon-plugin...${NC}"
if pacman -Qs xfce4-genmon-plugin >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ xfce4-genmon-plugin ya está instalado.${NC}"
else
    echo -e "  ${YELLOW}⚠ xfce4-genmon-plugin no se encuentra instalado.${NC}"
    echo -e "  Intentando instalar con pacman..."
    sudo pacman -S --needed --noconfirm xfce4-genmon-plugin
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ xfce4-genmon-plugin instalado correctamente.${NC}"
    else
        echo -e "  ${RED}✗ No se pudo instalar xfce4-genmon-plugin automáticamente.${NC}"
        echo -e "    Por favor, instálalo manualmente ejecutando: ${BOLD}sudo pacman -S xfce4-genmon-plugin${NC}"
        exit 1
    fi
fi
echo ""

# 2. Check Docker access
echo -e "${CYAN}[2/4] Verificando acceso a Docker...${NC}"
if docker ps >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Conexión exitosa al demonio de Docker.${NC}"
else
    echo -e "  ${RED}✗ No se puede acceder al socket de Docker.${NC}"
    echo -e "    ¿Está corriendo el servicio de Docker? (systemctl start docker)"
    echo -e "    ¿Tu usuario pertenece al grupo 'docker'?"
    echo -e "    Para añadir tu usuario al grupo docker ejecuta:"
    echo -e "      ${BOLD}sudo usermod -aG docker \$USER${NC}"
    echo -e "    y luego reinicia tu sesión."
    echo -e "    ${YELLOW}Continuando con la instalación de todas formas...${NC}"
fi
echo ""

# 3. Configure file permissions
echo -e "${CYAN}[3/4] Configurando permisos de ejecución...${NC}"
chmod +x docker_genmon.sh docker_menu.py
echo -e "  ${GREEN}✓ docker_genmon.sh y docker_menu.py configurados como ejecutables.${NC}"
echo ""

# 4. Instructions for XFCE Panel
echo -e "${BLUE}${BOLD}========================================================"
echo -e "      ⚙️ PASOS PARA INTEGRAR EN EL PANEL DE XFCE"
echo -e "========================================================${NC}"
echo -e "Para añadir el plugin a tu panel superior, sigue estos pasos:"
echo -e "  1. Haz clic derecho en una zona vacía de tu panel de XFCE."
echo -e "  2. Selecciona ${BOLD}Panel -> Añadir nuevos elementos...${NC}"
echo -e "  3. Busca ${CYAN}Generic Monitor${NC} (Monitor genérico) y haz clic en ${BOLD}Añadir${NC}."
echo -e "  4. Haz clic derecho sobre el nuevo plugin en tu panel y selecciona ${BOLD}Propiedades${NC}."
echo -e "  5. Configura los siguientes campos:"
echo -e "     • ${BOLD}Comando:${NC} $(pwd)/docker_genmon.sh"
echo -e "     • ${BOLD}Período (s):${NC} 10"
echo -e "     • ${BOLD}Etiqueta:${NC} Desmarcar / Desactivar (para mostrar solo el icono)"
echo -e "  6. Haz clic en ${BOLD}Cerrar${NC}."
echo -e "${BLUE}========================================================${NC}\n"

# Verify if we should run a test
echo -e "${CYAN}[4/4] ¿Quieres probar el Dashboard interactivo ahora?${NC}"
read -p "Presiona ENTER para abrir el dashboard de prueba, o Ctrl+C para salir..."

echo -e "Lanzando dashboard de prueba..."
./docker_menu.py
echo -e "${GREEN}✓ Ejecución de prueba finalizada.${NC}"
