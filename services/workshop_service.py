"""Workshop — fetches pack catalogue from GitHub and downloads packs."""

import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

from utils.logger import get_logger

logger = get_logger(__name__)

WORKSHOP_URL = (
    "https://raw.githubusercontent.com/GraphDevelopment/GraphLauncher/main/workshop.json"
)


def fetch_workshop() -> dict:
    try:
        req = urllib.request.Request(
            WORKSHOP_URL, headers={"User-Agent": "GraphLauncher"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "success": True,
            "packs": data.get("packs", []),
            "updated": data.get("updated", ""),
        }
    except Exception as exc:
        logger.error("fetch_workshop: %s", exc)
        return {"success": False, "error": str(exc), "packs": []}


def download_and_extract(
    download_url: str,
    pack_name: str,
    dest_dir: str,
    progress_cb: Callable[[int, str], None] | None = None,
) -> dict:
    dest = Path(dest_dir)
    if not dest.is_dir():
        return {"success": False, "error": "Dossier de packs introuvable."}

    ext = Path(download_url.split("?")[0]).suffix.lower()
    if ext != ".zip":
        return {
            "success": False,
            "error": f"Format '{ext}' non supporté — utilisez .zip.",
        }

    tmp_dir = tempfile.mkdtemp(prefix="graphlauncher_ws_")
    tmp_file = Path(tmp_dir) / f"pack{ext}"

    try:
        if progress_cb:
            progress_cb(5, "Connexion au serveur…")

        req = urllib.request.Request(
            download_url, headers={"User-Agent": "GraphLauncher"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            with open(tmp_file, "wb") as f:
                while chunk := resp.read(65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total and progress_cb:
                        pct = int(downloaded / total * 70) + 5
                        progress_cb(pct, f"Téléchargement… {downloaded / 1_048_576:.1f} Mo")

        if progress_cb:
            progress_cb(76, "Extraction…")

        pack_dest = dest / pack_name
        pack_dest.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(tmp_file) as zf:
            names = zf.namelist()
            for i, name in enumerate(names):
                zf.extract(name, pack_dest)
                if progress_cb and names:
                    progress_cb(76 + int((i + 1) / len(names) * 22), f"Extraction… {i + 1}/{len(names)}")

        if progress_cb:
            progress_cb(100, "Terminé")

        logger.info("Workshop pack extracted: %s → %s", pack_name, pack_dest)
        return {"success": True, "path": str(pack_dest)}

    except Exception as exc:
        logger.error("download_and_extract: %s", exc)
        return {"success": False, "error": str(exc)}

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
