# Graph Launcher

**Graph Launcher** is a Windows desktop application for managing FiveM / GTA V graphic packs. It provides a modern dark UI to install, uninstall, clean, and download community packs — without touching any game system files.

---

## Features

- **Pack Manager** — Scan a local folder, install/uninstall packs into FiveM or GTA V with one click
- **Workshop** — Browse packs by category (Graphic Packs, Sound Packs, Mods) with dynamic filter chips driven entirely by `workshop.json`
- **Video Preview** — Watch YouTube previews of packs inside the app (via yt-dlp, HD quality, no ffmpeg required)
- **FiveM Cleaner** — Remove mods, plugins, ReShade and pack files from FiveM Application Data
- **GTA V Cleaner** — Remove mod files from GTA V while protecting official files via SHA256 baseline
- **Baseline Protection** — Index all official GTA V files (SHA256) so the cleaner never deletes them
- **Auto-update** — Notified on startup when a new version is available on GitHub Releases
- **Bilingual** — Full French and English interface (auto-detected from system locale, switchable in Settings)

---

## Requirements

| Requirement | Details |
|---|---|
| Windows 10/11 | 64-bit |
| [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) | Included in Windows 11. Download for Windows 10. |
| Python 3.11+ | Only for running from source |

To extract `.rar` packs from the Workshop, one of the following must be installed:
- [7-Zip](https://www.7-zip.org/) (recommended, free)
- [WinRAR](https://www.rarlab.com/)

---

## Installation (end users)

Download the latest installer from the [Releases page](https://github.com/GraphDevelopment/GraphLauncher/releases) and run it.

---

## Running from source

```bash
git clone https://github.com/GraphDevelopment/GraphLauncher.git
cd GraphLauncher

pip install -r requirements.txt

python main.py

python main.py --debug
```

---

## Build standalone .exe

```bash
pip install pyinstaller
python build.py
```

Output: `dist/FiveM_Graph_Launcher.exe`

Then compile `installer.iss` with [Inno Setup 6](https://jrsoftware.org/isinfo.php) to generate the installer.

---

## Project structure

```
├── main.py                   # Entry point — starts HTTP server + pywebview window
├── backend/
│   └── api.py                # Python ↔ JavaScript bridge (all pywebview.api.* calls)
├── core/
│   ├── pack_manager.py       # Scan, install, uninstall packs
│   ├── cleaner.py            # FiveM / GTA V cleanup logic
│   ├── backup.py             # Automatic backups before installs
│   └── baseline.py           # SHA256 index for GTA V file protection
├── services/
│   ├── workshop_service.py   # Workshop fetch + download/extract (.zip, .rar)
│   ├── update_service.py     # GitHub Releases version check
│   ├── file_service.py       # Safe file operations
│   ├── validation_service.py # FiveM / GTA V path validation
│   └── hash_service.py       # SHA256 hashing utilities
├── database/
│   └── db_manager.py         # SQLite — settings, install history, logs
├── utils/
│   ├── logger.py
│   └── paths.py              # Frozen/dev path resolution
├── frontend/
│   ├── index.html
│   ├── css/
│   │   ├── base.css
│   │   └── components.css
│   └── js/
│       ├── app.js            # Main UI logic
│       ├── api.js            # JS wrappers for pywebview.api
│       └── i18n.js           # Embedded FR/EN translations
├── build.py                  # PyInstaller build script
├── installer.iss             # Inno Setup installer script
└── workshop.json             # Community pack catalogue (hosted on this repo)
```

---

## Pack installation mapping

Each subfolder inside a pack is routed to its destination based on its name (case-insensitive):

| Pack subfolder | Destination |
|---|---|
| `mods/` | FiveM Application Data/mods/ |
| `plugins/` | FiveM Application Data/plugins/ |
| `citizen/` | FiveM Application Data/citizen/ |
| `fivem/` | FiveM Application Data/ (contents) |
| `pack son/`, `audio/` | GTA V/x64/audio/sfx/ (.rpf files only) |
| `gta5/`, `gta/` | GTA V/ (root) |

---

## Workshop JSON schema

The Workshop reads `workshop.json` from this repository. To add a pack, append an entry to the `packs` array:

```json
{
  "packs": [
    {
      "id": "my-pack-v1",
      "name": "My Pack",
      "author": "Author",
      "version": "1.0",
      "categorie": "graphique",
      "filtres": ["roleplay", "realiste"],
      "description": "Short description.",
      "size_mb": 500,
      "downloads": 0,
      "tags": ["RESHADE", "ENB"],
      "preview_url": "https://i.imgur.com/XXXXXXX.jpg",
      "youtube_url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
      "download_url": "https://example.com/pack.zip"
    }
  ],
  "updated": "2026-01-01"
}
```

### Fields

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Unique slug (lowercase, hyphens) |
| `name` | Yes | Display name |
| `author` | Yes | Pack creator |
| `version` | No | Version string |
| `categorie` | Yes | One of: `graphique`, `son`, `mods` |
| `filtres` | No | Array of filter tags — the app generates filter chips automatically from these values |
| `description` | No | Short description shown on the card |
| `size_mb` | No | File size in MB |
| `downloads` | No | Download counter (cosmetic) |
| `tags` | No | Technical tags shown as badges on the card |
| `preview_url` | No | Thumbnail image URL (loaded via server-side proxy) |
| `youtube_url` | No | YouTube video URL for the in-app HD preview |
| `download_url` | Yes | Direct download link — `.zip` or `.rar` |

### Categories

| Value | Tab shown in app |
|---|---|
| `graphique` | Graphic Packs |
| `son` | Sound Packs |
| `mods` | Mods |

### Filters

The `filtres` array is completely free-form. The app reads all unique values across packs in the active category and renders a filter chip for each one automatically — no code changes needed to add new filters.

**Supported download hosts:** pixeldrain, archive.org, GitHub Releases, or any direct link returning a `.zip` or `.rar` file (detected via `Content-Disposition`, `Content-Type`, or URL extension).

---

## Auto-update

On startup, the app calls the GitHub Releases API and compares the latest tag against the embedded `APP_VERSION`. If a newer version is found, a banner appears with a download link.

To publish a new version:
1. Update `APP_VERSION` in `services/update_service.py`
2. Update `AppVersion` in `installer.iss`
3. Build the exe and installer
4. Create a GitHub Release with a tag matching the version (e.g. `v1.2.9`)

---

## Security

- No operations on system paths (`C:/Windows`, etc.)
- SHA256 baseline protection for GTA V official files
- Automatic backup before every pack installation
- User confirmation required before any clean or uninstall operation
- All file operations sandboxed to configured pack and game directories
