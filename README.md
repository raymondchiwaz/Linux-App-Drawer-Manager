# App Drawer Manager (Fedora / GNOME)

> Easily create, import, edit and remove custom application launchers for your GNOME Activities overview (Super / Windows key). 
>
> Crafted by **Ray** — discover more projects at **https://rayistec.dev**.

---

<p align="center">
  <img src="https://img.shields.io/badge/GTK-4-blue?logo=gtk" alt="GTK4" />
  <img src="https://img.shields.io/badge/Libadwaita-1.x-6f42c1" alt="Libadwaita" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License: MIT" />
</p>

<p align="center">
  <em>Turn scripts (Python, Shell, Node, AppImage, binaries) into first‑class desktop apps with icons & categories in seconds.</em>
</p>

---

## ✨ Features
- Scan and list custom launchers (tagged with `X-Custom-Added=1`).
- Add from: executable, script (`.py`, `.sh`, `.js`), AppImage, or existing `.desktop` file.
- Auto wrapper detection (python3 / bash / node) + manual override.
- Optional extra arguments, terminal toggle, and executable bit fixer.
- Icon picker (copies into `~/.local/share/icons/hicolor/128x128/apps`).
- Edit existing launchers (name, exec, icon, categories, terminal mode).
- Safe delete with confirmation.
- Instant feedback via toast notifications.
- Modern GTK4 + Libadwaita UI (resizable, responsive list area).

## 🖼 Screenshots
> (Add your screenshots here – e.g. `docs/screenshot-main.png` and `docs/screenshot-add.png`)
```
![Main Window](docs/screenshot-main.png)
![Add Launcher](docs/screenshot-add.png)
```

## 🚀 Quick Start
```bash
# Fedora dependencies
sudo dnf install -y python3 python3-gobject gtk4 libadwaita python3-libadwaita adwaita-icon-theme

# Clone & run
python3 app_launcher_manager.py
```

Install a launcher for the manager itself:
```bash
chmod +x install.sh
./install.sh
```
Then open Activities and search: `App Drawer Manager`.

## 🧩 Adding Applications
1. Click **Add Application**.
2. Pick a file (script, binary, AppImage, etc.).
3. Select wrapper (Auto usually correct) and optionally add arguments.
4. (Optional) Choose / attach an icon image (PNG / SVG). 
5. Set categories (e.g. `Utility;Development;`).
6. Save — it appears in Activities almost immediately.

### Editing
Click the pencil icon to modify an existing launcher (exec, name, icon, terminal, categories).

### Deleting
Click the trash icon → confirm → launcher file is removed from `~/.local/share/applications`.

## 🛠 How It Works
Creates `.desktop` files under:
```
~/.local/share/applications
```
Icons (when you choose a file) are copied to:
```
~/.local/share/icons/hicolor/128x128/apps
```
GNOME indexes these automatically. The marker line:
```
X-Custom-Added=1
```
lets the app distinguish its managed entries.

## 🔍 Troubleshooting
| Issue | Fix |
|-------|-----|
| Launcher not visible | Run `touch ~/.local/share/applications` and reopen Activities. |
| Icon not showing | Ensure image is PNG/SVG, then run (optional) `gtk4-update-icon-cache ~/.local/share/icons/hicolor || true`. |
| Script doesn’t run | Ensure executable bit if using Direct, or use wrapper (python3 / bash). |
| Path with spaces fails | App now quotes paths; re-create or edit & save to regenerate `Exec`. |
| Still cached old icon | Log out/in or restart `gnome-shell` (on Xorg: `Alt+F2`, type `r`). |

## 🧪 Supported File Types
| Type | Auto Behavior |
|------|---------------|
| `.py` | Runs with `python3` unless executable & chosen Direct |
| `.sh` / `.bash` | Runs with `bash` |
| `.js` | Runs with `node` |
| AppImage / Binary | Direct if executable |

## 🗺 Roadmap
- [ ] Drag & drop file to create launcher
- [ ] Bulk import / export
- [ ] Icon preview thumbnail
- [ ] MIME / URL handlers
- [ ] Actions (right-click menus)

## 🤝 Contributing
PRs and issues welcome. Ideas: improve accessibility, add localization, add advanced desktop entry fields.

## 🧾 License
MIT — see `LICENSE` (add one if not present).

## 👨‍💻 Author
**Ray** — more projects & updates at: https://rayistec.dev

If you like this tool, ⭐ the repo and share it.

---

### Security Note
Always review scripts you convert into launchers. Launchers can execute arbitrary code.

### Disclaimer
Tested on Fedora GNOME (GTK4/Libadwaita). Other distros with GNOME 42+ should work; file an issue if not.
