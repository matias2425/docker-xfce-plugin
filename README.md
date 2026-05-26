# 🐳 Docker XFCE Panel Plugin

A lightweight Docker panel integration for **XFCE4** built with the Generic Monitor plugin (`xfce4-genmon-plugin`) and a custom **GTK3 Python dashboard**.

Monitor and manage all your Docker containers directly from your taskbar — without opening a terminal.

---

## ✨ Features

- **Live panel indicator** — Shows a Docker icon with a running container count. Turns to a greyed-out "off" state when the Docker daemon is not reachable.
- **Interactive floating dashboard** — Click the panel icon to open a sleek GTK3 popup window with all your containers listed.
- **Container management** — Start, stop, and restart containers with a single click, right from the panel.
- **Real-time log viewer** — Expand an inline log panel per container to tail the last 50 lines of logs.
- **Smart URL detection** — Automatically discovers accessible URLs for each running container through:
  - Exposed port mappings (`0.0.0.0:8080->80/tcp` → `http://localhost:8080`)
  - Traefik reverse proxy labels (`traefik.http.routers.*.rule`)
  - `VIRTUAL_HOST` environment variables
- **Container filtering** — Search/filter containers by name or image in real time.
- **System prune** — One-click `docker container prune` with a confirmation dialog to clean up stopped containers.
- **Premium dark UI** — Glassmorphism-inspired dark theme (Catppuccin-based palette) with smooth hover transitions and color-coded status badges.

---

## 📸 Screenshots

> *Dashboard showing running and stopped containers with action buttons and URL badges.*

---

## 🗂️ Project Structure

```
docker-xfce-plugin/
├── docker_genmon.sh        # Bash script polled by xfce4-genmon-plugin
├── docker_menu.py          # GTK3 Python dashboard (the main UI)
├── docker_icon.svg         # Colored Docker icon (daemon active)
├── docker_icon_offline.svg # Greyscale Docker icon (daemon inactive)
├── style.css               # GTK3 CSS stylesheet for the dashboard
└── install.sh              # Automated installer and setup guide
```

---

## 🔧 Requirements

| Requirement | Notes |
|---|---|
| **XFCE4** | The desktop environment this plugin targets |
| **xfce4-genmon-plugin** | The Generic Monitor panel plugin (`pacman -S xfce4-genmon-plugin`) |
| **Docker** | Must be installed and accessible to the current user |
| **Python 3** | For the dashboard script |
| **PyGObject (GTK3)** | Python GTK3 bindings (`python-gobject` on Arch Linux) |

> **Note:** The installer (`install.sh`) uses `pacman` and targets **Arch Linux** (and Arch-based distros like Manjaro, EndeavourOS). On other distros, install `xfce4-genmon-plugin` and `python-gobject` using your package manager.

---

## 🚀 Installation

### Quick Install (Arch Linux)

Clone the repository and run the installer:

```bash
git clone https://github.com/your-username/docker-xfce-plugin.git
cd docker-xfce-plugin
bash install.sh
```

The installer will:
1. Check for and install `xfce4-genmon-plugin` if missing.
2. Verify Docker daemon access and print troubleshooting tips if needed.
3. Set executable permissions on `docker_genmon.sh` and `docker_menu.py`.
4. Print step-by-step instructions to add the plugin to your XFCE panel.
5. Optionally launch the dashboard immediately for a live test.

### Manual Steps

1. Clone the repo and `cd` into the directory.
2. Make the scripts executable:
   ```bash
   chmod +x docker_genmon.sh docker_menu.py
   ```
3. **Add the plugin to your panel:**
   - Right-click an empty area on your XFCE panel.
   - Go to **Panel → Add New Items…**
   - Search for **Generic Monitor** and click **Add**.
   - Right-click the new plugin → **Properties**.
   - Set the **Command** field to the absolute path of `docker_genmon.sh`:
     ```
     /path/to/docker-xfce-plugin/docker_genmon.sh
     ```
   - Set the **Period (s)** to `10`.
   - Uncheck the **Label** option (to display only the icon).
   - Click **Close**.

> **Tip:** If Docker requires `sudo`, add your user to the `docker` group:
> ```bash
> sudo usermod -aG docker $USER
> # Log out and back in for the change to take effect
> ```

---

## 🖥️ Usage

Once installed, the plugin shows a Docker icon in your panel:

| State | Icon | Label | Tooltip |
|---|---|---|---|
| Docker running | 🔵 Colored icon | `N` (running count) | "N active / M total containers" |
| Docker stopped | ⚫ Greyscale icon | `off` | "Docker is not responding" |

**Click the icon** (or the label) to open the Docker Manager dashboard.

### Dashboard Controls

| Control | Action |
|---|---|
| ▶ (Start) | Start a stopped container |
| ⏹ (Stop) | Stop a running container |
| ↻ (Restart) | Restart a running container |
| 🖥 (Logs) | Toggle the inline log viewer (last 50 lines) |
| URL badge | Open the container's exposed URL in the default browser |
| Search bar | Filter containers by name or image |
| **Actualizar ↻** | Manually refresh the container list |
| **Limpiar Sistema** | Run `docker container prune` (with confirmation) |

Press **Escape** or click outside the window to close the dashboard.

---

## ⚙️ Configuration

Currently all configuration is done by editing the files directly:

- **Poll interval:** Change the **Period (s)** value in the Generic Monitor plugin properties (default: `10` seconds).
- **Dashboard size:** Edit `window_width` and `window_height` at the top of `position_window()` in `docker_menu.py`.
- **Log lines:** Change `--tail 50` in the `fetch_logs()` method in `docker_menu.py`.
- **Theme colors:** Edit `style.css` to customize the color palette.
