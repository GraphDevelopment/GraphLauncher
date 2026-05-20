"""PyInstaller build script — run: python build.py"""

import subprocess
import sys
from pathlib import Path

APP_NAME    = "Graph Launcher"
ENTRY_POINT = "main.py"
ICON        = "assets/icon.ico"
VERSION     = "1.2.7"

ROOT = Path(__file__).parent
SEP  = ";" if sys.platform == "win32" else ":"


def build() -> None:
    icon_flag = ["--icon", ICON] if (ROOT / ICON).exists() else []

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",          # single .exe, no folders next to it
        "--windowed",         # no console window
        "--name", APP_NAME.replace(" ", "_"),
        *icon_flag,

        # Data files embedded inside the exe
        "--add-data", f"frontend{SEP}frontend",
        "--add-data", f"assets{SEP}assets",

        # webview (pywebview 6.x) — the package imports as "webview", not "pywebview"
        "--hidden-import", "webview",
        "--hidden-import", "webview.platforms.winforms",
        "--collect-all",   "webview",

        # pythonnet is required by webview on Windows
        "--hidden-import", "clr",
        "--collect-all",   "pythonnet",

        # yt-dlp (YouTube stream extraction for video preview)
        "--hidden-import", "yt_dlp",
        "--hidden-import", "yt_dlp.extractor",
        "--hidden-import", "yt_dlp.extractor.youtube",
        "--collect-all",   "yt_dlp",

        ENTRY_POINT,
    ]

    print("Building:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(ROOT), check=False)

    if result.returncode == 0:
        print(f"\nBuild OK  →  dist/{APP_NAME.replace(' ', '_')}.exe")
    else:
        print("\nBuild failed — check PyInstaller output above")
        sys.exit(1)


if __name__ == "__main__":
    build()
