#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# XFCE Generic Monitor Script for Docker
# -----------------------------------------------------------------------------

# Absolute path to this plugin's directory
DIR="/home/matias/Develop/Projects/docker-xfce-plugin"

ICON_ONLINE="$DIR/docker_icon.svg"
ICON_OFFLINE="$DIR/docker_icon_offline.svg"
MENU_EXEC="$DIR/docker_menu.py"

# Try to run docker ps with a 2-second timeout to avoid locking the panel if docker hangs
if timeout 2 docker ps >/dev/null 2>&1; then
    # Docker is active and running
    RUNNING_COUNT=$(docker ps -q | wc -l)
    TOTAL_COUNT=$(docker ps -a -q | wc -l)
    
    # Output to the XFCE Genmon panel
    echo "<img>$ICON_ONLINE</img>"
    
    # If there are running containers, show the count in the panel
    if [ "$RUNNING_COUNT" -gt 0 ]; then
        echo "<txt> $RUNNING_COUNT</txt>"
    else
        echo "<txt></txt>" # Empty means just show the icon, keeping the panel clean
    fi
    
    echo "<click>$MENU_EXEC</click>"
    echo "<txtclick>$MENU_EXEC</txtclick>"
    echo "<tool><b>Docker Active</b>&#10;Containers: $RUNNING_COUNT running / $TOTAL_COUNT total&#10;Click to open the Dashboard</tool>"
else
    # Docker daemon is stopped, not responding, or user lacks permissions
    echo "<img>$ICON_OFFLINE</img>"
    echo "<txt> off</txt>"
    echo "<click>$MENU_EXEC</click>"
    echo "<txtclick>$MENU_EXEC</txtclick>"
    echo "<tool><b>Docker Inactive</b>&#10;The Docker service or socket is not responding.&#10;Check: systemctl status docker.&#10;Click to open the manager.</tool>"
fi
