import os
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """Root of the source tree (dev) or directory containing the exe (frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    """
    Writable user-data directory.
    Frozen : %LOCALAPPDATA%\Graph Launcher\  (survives Program Files UAC)
    Dev    : <repo>/data/
    """
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Graph Launcher"
    else:
        base = get_app_dir() / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_logs_dir() -> Path:
    d = get_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_backups_dir() -> Path:
    d = get_data_dir() / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_database_path() -> Path:
    return get_data_dir() / "launcher.db"


def get_baseline_path() -> Path:
    return get_data_dir() / "clean_files.json"


def get_frontend_dir() -> Path:
    """
    Frozen : files are extracted by PyInstaller to sys._MEIPASS/frontend/
    Dev    : <repo>/frontend/
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "frontend"
    return get_app_dir() / "frontend"


def get_index_html() -> str:
    return str(get_frontend_dir() / "index.html")
