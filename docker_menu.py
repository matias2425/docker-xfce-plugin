#!/usr/bin/env python3
import sys
import os
import re
import json
import subprocess
import webbrowser
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

class DockerDashboard(Gtk.Window):
    def __init__(self):
        super().__init__(title="Docker Dashboard")
        self.set_name("docker-dashboard-window")
        self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)

        self.containers = []
        self.log_boxes = {}  # container_id -> Gtk.Box for logs
        self.log_texts = {}  # container_id -> Gtk.TextBuffer
        self.loading_pids = set() # running docker operation ids to show loader

        # Load style
        self.load_css()

        # Window Layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)

        # 1. Header Box
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.header_box.get_style_context().add_class("header-box")
        
        # Load docker SVG or default icon
        docker_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docker_icon.svg")
        if os.path.exists(docker_icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(docker_icon_path, 24, 24, True)
                icon_image = Gtk.Image.new_from_pixbuf(pixbuf)
            except Exception:
                icon_image = Gtk.Image.new_from_icon_name("docker", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            icon_image = Gtk.Image.new_from_icon_name("docker", Gtk.IconSize.LARGE_TOOLBAR)
            
        self.header_box.pack_start(icon_image, False, False, 0)

        # Title/Subtitle Vertical Box
        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_label = Gtk.Label(label="Docker Manager")
        title_label.set_xalign(0)
        title_label.get_style_context().add_class("header-title")
        self.status_label = Gtk.Label(label="Loading containers...")
        self.status_label.set_xalign(0)
        self.status_label.get_style_context().add_class("header-subtitle")
        title_vbox.pack_start(title_label, True, True, 0)
        title_vbox.pack_start(self.status_label, True, True, 0)
        self.header_box.pack_start(title_vbox, True, True, 0)

        # Close button
        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("btn-action")
        close_btn.connect("clicked", lambda w: Gtk.main_quit())
        self.header_box.pack_end(close_btn, False, False, 0)

        self.main_box.pack_start(self.header_box, False, False, 0)

        # 2. Search Box
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.get_style_context().add_class("search-entry")
        self.search_entry.set_placeholder_text("Filter containers...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.main_box.pack_start(self.search_entry, False, False, 0)

        # 3. Scrollable list container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.get_style_context().add_class("scroll-viewport")
        self.main_box.pack_start(self.scroll, True, True, 0)

        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.list_box.get_style_context().add_class("containers-list")
        self.scroll.add(self.list_box)

        # 4. Footer Box
        self.footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.footer_box.get_style_context().add_class("footer-box")
        
        self.docker_ver_label = Gtk.Label(label="Docker v...")
        self.docker_ver_label.set_xalign(0)
        self.footer_box.pack_start(self.docker_ver_label, True, True, 0)

        # Prune button
        prune_btn = Gtk.Button(label="Clean Up System")
        prune_btn.get_style_context().add_class("footer-btn")
        prune_btn.connect("clicked", self.on_prune_clicked)
        self.footer_box.pack_end(prune_btn, False, False, 0)

        # Refresh button
        refresh_btn = Gtk.Button(label="Refresh ↻")
        refresh_btn.get_style_context().add_class("footer-btn")
        refresh_btn.connect("clicked", lambda w: self.refresh_data())
        self.footer_box.pack_end(refresh_btn, False, False, 0)

        self.main_box.pack_end(self.footer_box, False, False, 0)

        # Interaction / Window Close events
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("key-press-event", self.on_key_press)

        # Position and size
        self.position_window()
        self.show_all()

        # Load Docker version and start initial load
        self.load_docker_version()
        self.refresh_data()

    def load_css(self):
        css_provider = Gtk.CssProvider()
        css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
        if os.path.exists(css_path):
            try:
                css_provider.load_from_path(css_path)
                screen = Gdk.Screen.get_default()
                Gtk.StyleContext.add_provider_for_screen(
                    screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception as e:
                print(f"Error loading CSS: {e}")

    def position_window(self):
        # Default dimensions
        window_width = 380
        window_height = 520

        display = Gdk.Display.get_default()
        seat = display.get_default_seat()
        pointer = seat.get_pointer()
        screen, x, y = pointer.get_position()

        # Center horizontally on cursor, place 10px below/above cursor
        pos_x = x - (window_width // 2)
        pos_y = y + 10

        # Adjust position if out of screen boundary
        monitor = display.get_monitor_at_point(x, y)
        geom = monitor.get_geometry()

        if pos_x < geom.x:
            pos_x = geom.x + 10
        elif pos_x + window_width > geom.x + geom.width:
            pos_x = geom.x + geom.width - window_width - 10

        if pos_y + window_height > geom.y + geom.height:
            # If it overflows screen at the bottom, show above cursor
            pos_y = y - window_height - 10

        if pos_y < geom.y:
            pos_y = geom.y + 10

        self.move(pos_x, pos_y)
        self.set_default_size(window_width, window_height)

    def on_focus_out(self, widget, event):
        # Quit when user clicks elsewhere
        Gtk.main_quit()

    def on_key_press(self, widget, event):
        # Quit on Escape key
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

    def load_docker_version(self):
        def worker():
            try:
                res = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"], 
                                     capture_output=True, text=True)
                version = res.stdout.strip() if res.returncode == 0 else "Unknown"
                GLib.idle_add(self.docker_ver_label.set_text, f"Docker v{version}")
            except Exception:
                GLib.idle_add(self.docker_ver_label.set_text, "Docker not running")
        threading.Thread(target=worker, daemon=True).start()

    def refresh_data(self):
        self.status_label.set_text("Fetching containers...")
        
        def worker():
            containers = self.get_containers()
            GLib.idle_add(self.update_ui_list, containers)

        threading.Thread(target=worker, daemon=True).start()

    def get_containers(self):
        try:
            res = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{json .}}"],
                capture_output=True, text=True, check=True
            )
            containers = []
            for line in res.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    containers.append(data)
                except json.JSONDecodeError:
                    pass
            
            # Smart URL detection for each container
            for c in containers:
                c["urls"] = self.detect_container_urls(c)
                
            return containers
        except Exception as e:
            print(f"Error reading containers: {e}")
            return []

    def detect_container_urls(self, container):
        urls = []
        ports_str = container.get("Ports", "")
        cid = container.get("ID")
        
        # 1. Check port mappings in the output string of docker ps
        if ports_str:
            # Matches: 0.0.0.0:8000->80/tcp or [::]:8000->80/tcp
            matches = re.findall(r'(?:0\.0\.0\.0|127\.0\.0\.1|\[::\]|localhost):(\d+)->\d+/tcp', ports_str)
            host_ports = sorted(list(set(int(p) for p in matches)))
            for p in host_ports:
                scheme = "https" if p in [443, 8443] else "http"
                urls.append({
                    "label": f"localhost:{p}",
                    "url": f"{scheme}://localhost:{p}"
                })

        # 2. Check labels or Env variables via docker inspect
        if cid:
            try:
                inspect_res = subprocess.run(
                    ["docker", "inspect", cid],
                    capture_output=True, text=True
                )
                if inspect_res.returncode == 0:
                    inspect_data = json.loads(inspect_res.stdout)
                    if inspect_data:
                        config = inspect_data[0].get("Config", {})
                        labels = config.get("Labels", {}) or {}
                        env_list = config.get("Env", []) or []

                        # Traefik rule detection: Host(`domain.local`)
                        for key, val in labels.items():
                            if key.startswith("traefik.http.routers.") and key.endswith(".rule"):
                                host_match = re.search(r'Host\(`([^`]+)`\)', val)
                                if host_match:
                                    domain = host_match.group(1)
                                    urls.append({
                                        "label": domain,
                                        "url": f"http://{domain}"
                                    })

                        # VIRTUAL_HOST env variable detection
                        for env in env_list:
                            if "=" in env:
                                k, v = env.split("=", 1)
                                if k == "VIRTUAL_HOST":
                                    for dom in v.split(","):
                                        dom = dom.strip()
                                        if dom:
                                            urls.append({
                                                "label": dom,
                                                "url": f"http://{dom}"
                                            })
            except Exception as e:
                print(f"Error inspecting container {cid}: {e}")

        # Deduplicate URLs
        seen = set()
        unique = []
        for u in urls:
            if u["url"] not in seen:
                seen.add(u["url"])
                unique.append(u)
        return unique

    def update_ui_list(self, containers):
        self.containers = containers
        
        # Clear current list
        for child in self.list_box.get_children():
            self.list_box.remove(child)

        filter_text = self.search_entry.get_text().lower().strip()
        filtered = []
        running_count = 0

        for c in containers:
            name = c.get("Names", "").lower()
            image = c.get("Image", "").lower()
            state = c.get("State", "")
            
            if state == "running":
                running_count += 1
                
            if filter_text:
                if filter_text not in name and filter_text not in image:
                    continue
            filtered.append(c)

        # Update status header
        self.status_label.set_text(f"{running_count} running / {len(containers)} total")

        if not filtered:
            empty_lbl = Gtk.Label(label="No containers found")
            empty_lbl.set_margin_top(20)
            empty_lbl.set_margin_bottom(20)
            empty_lbl.get_style_context().add_class("header-subtitle")
            self.list_box.pack_start(empty_lbl, True, True, 0)
        else:
            for c in filtered:
                self.list_box.pack_start(self.create_container_row(c), False, False, 0)

        self.list_box.show_all()

    def create_container_row(self, container):
        cid = container.get("ID")
        name = container.get("Names")
        image = container.get("Image")
        status = container.get("Status")
        state = container.get("State")
        urls = container.get("urls", [])

        # Helper to create buttons with standard system-themed icons
        def make_icon_btn(icon_name, tooltip, callback):
            btn = Gtk.Button()
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            btn.set_image(img)
            btn.set_always_show_image(True)
            btn.set_tooltip_text(tooltip)
            btn.get_style_context().add_class("btn-action")
            btn.connect("clicked", callback)
            return btn

        # Outer card box
        card_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card_vbox.get_style_context().add_class("container-row")

        # Top row: info and actions
        top_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        card_vbox.pack_start(top_hbox, True, True, 0)

        # Left status badge
        badge_lbl = Gtk.Label(label="RUNNING" if state == "running" else "STOPPED")
        badge_lbl.get_style_context().add_class("badge")
        badge_lbl.get_style_context().add_class("badge-running" if state == "running" else "badge-stopped")
        badge_lbl.set_valign(Gtk.Align.START)
        top_hbox.pack_start(badge_lbl, False, False, 0)

        # Middle Box (Texts)
        text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        top_hbox.pack_start(text_vbox, True, True, 0)

        name_lbl = Gtk.Label(label=name)
        name_lbl.set_xalign(0)
        name_lbl.get_style_context().add_class("container-name")
        text_vbox.pack_start(name_lbl, False, False, 0)

        image_lbl = Gtk.Label(label=image)
        image_lbl.set_xalign(0)
        image_lbl.get_style_context().add_class("container-image")
        text_vbox.pack_start(image_lbl, False, False, 0)

        status_lbl = Gtk.Label(label=status)
        status_lbl.set_xalign(0)
        status_lbl.get_style_context().add_class("container-status")
        text_vbox.pack_start(status_lbl, False, False, 0)

        # Right Action Buttons Box
        actions_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        actions_hbox.set_valign(Gtk.Align.CENTER)
        top_hbox.pack_end(actions_hbox, False, False, 0)

        if cid in self.loading_pids:
            spinner = Gtk.Spinner()
            spinner.start()
            actions_hbox.pack_start(spinner, False, False, 0)
        else:
            if state == "running":
                # Restart Button (view-refresh)
                restart_btn = make_icon_btn("view-refresh", "Restart container", lambda w, i=cid: self.run_container_action(i, "restart"))
                restart_btn.get_style_context().add_class("btn-restart")
                actions_hbox.pack_start(restart_btn, False, False, 0)

                # Stop Button (media-playback-stop)
                stop_btn = make_icon_btn("media-playback-stop", "Stop container", lambda w, i=cid: self.run_container_action(i, "stop"))
                stop_btn.get_style_context().add_class("btn-stop")
                actions_hbox.pack_start(stop_btn, False, False, 0)
            else:
                # Start Button (media-playback-start)
                start_btn = make_icon_btn("media-playback-start", "Start container", lambda w, i=cid: self.run_container_action(i, "start"))
                start_btn.get_style_context().add_class("btn-start")
                actions_hbox.pack_start(start_btn, False, False, 0)

            # Logs toggle Button (utilities-terminal)
            logs_btn = make_icon_btn("utilities-terminal", "View logs", lambda w, i=cid: self.toggle_logs(i))
            actions_hbox.pack_start(logs_btn, False, False, 0)

        # Bottom row: URL Port badges
        if urls and state == "running":
            urls_flow = Gtk.FlowBox()
            urls_flow.set_valign(Gtk.Align.START)
            urls_flow.set_max_children_per_line(2)
            urls_flow.set_selection_mode(Gtk.SelectionMode.NONE)
            urls_flow.set_row_spacing(4)
            urls_flow.set_column_spacing(6)
            
            for u in urls:
                url_btn = Gtk.Button(label=f" {u['label']}")
                img = Gtk.Image.new_from_icon_name("applications-internet", Gtk.IconSize.MENU)
                url_btn.set_image(img)
                url_btn.set_always_show_image(True)
                url_btn.get_style_context().add_class("port-badge")
                url_btn.set_tooltip_text(f"Open {u['url']} in browser")
                url_btn.connect("clicked", lambda w, target=u['url']: webbrowser.open(target))
                urls_flow.add(url_btn)
                
            card_vbox.pack_start(urls_flow, False, False, 2)

        # Hidden Logs area inside the card
        logs_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        logs_container.get_style_context().add_class("logs-expander")
        logs_container.set_no_show_all(True)
        logs_container.set_visible(False)
        self.log_boxes[cid] = logs_container

        scroll_logs = Gtk.ScrolledWindow()
        scroll_logs.set_min_content_height(100)
        scroll_logs.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        log_view = Gtk.TextView()
        log_view.set_editable(False)
        log_view.get_style_context().add_class("logs-text")
        scroll_logs.add(log_view)
        
        self.log_texts[cid] = log_view.get_buffer()
        logs_container.pack_start(scroll_logs, True, True, 0)

        card_vbox.pack_end(logs_container, False, False, 0)

        return card_vbox

    def toggle_logs(self, container_id):
        box = self.log_boxes.get(container_id)
        if not box:
            return

        is_visible = box.get_visible()
        if is_visible:
            box.hide()
        else:
            box.show()
            for child in box.get_children():
                child.show_all()
            self.fetch_logs(container_id)

    def fetch_logs(self, container_id):
        buffer = self.log_texts.get(container_id)
        if not buffer:
            return
            
        buffer.set_text("Loading logs...")
        
        def worker():
            try:
                res = subprocess.run(
                    ["docker", "logs", "--tail", "50", container_id],
                    capture_output=True, text=True
                )
                output = res.stdout if res.returncode == 0 else res.stderr
                if not output.strip():
                    output = "(No logs available)"
                GLib.idle_add(buffer.set_text, output)
            except Exception as e:
                GLib.idle_add(buffer.set_text, f"Error loading logs: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def run_container_action(self, container_id, action):
        self.loading_pids.add(container_id)
        self.update_ui_list(self.containers)  # Redraw to show spinner

        def worker():
            try:
                subprocess.run(["docker", action, container_id], capture_output=True, check=True)
            except Exception as e:
                print(f"Error performing {action} on {container_id}: {e}")
            
            GLib.idle_add(self.on_action_complete, container_id)

        threading.Thread(target=worker, daemon=True).start()

    def on_action_complete(self, container_id):
        if container_id in self.loading_pids:
            self.loading_pids.remove(container_id)
        self.refresh_data()

    def on_search_changed(self, widget):
        self.update_ui_list(self.containers)

    def on_prune_clicked(self, widget):
        # Ask for confirmation
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Clean up stopped containers?",
        )
        dialog.format_secondary_text(
            "This will run 'docker container prune' and remove all stopped containers. Proceed?"
        )
        
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            self.status_label.set_text("Cleaning up...")
            def worker():
                try:
                    subprocess.run(["docker", "container", "prune", "-f"], capture_output=True)
                except Exception as e:
                    print(f"Error running prune: {e}")
                GLib.idle_add(self.refresh_data)
                
            threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    import traceback
    # Ensure Docker is installed
    try:
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except Exception:
            print("Error: Docker is not installed or not available in PATH.")
            sys.exit(1)

        app = DockerDashboard()
        Gtk.main()
    except Exception as e:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error.log")
        with open(log_path, "w") as f:
            traceback.print_exc(file=f)
        sys.exit(1)
