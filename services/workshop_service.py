"""Workshop — fetches pack catalogue from GitHub and downloads packs."""

import json
import re
import shutil
import tempfile
import time
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
        # Append timestamp so GitHub raw CDN never serves a stale cached response
        url = f"{WORKSHOP_URL}?_t={int(time.time())}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "GraphLauncher",
                "Cache-Control": "no-cache, no-store",
                "Pragma": "no-cache",
            },
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


def _detect_ext(resp, download_url: str) -> str:
    """Return file extension from Content-Disposition, Content-Type, or URL."""
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r'filename=["\']?([^"\';\s]+)', cd, re.IGNORECASE)
    if m:
        ext = Path(m.group(1)).suffix.lower()
        if ext:
            return ext
    ct = resp.headers.get("Content-Type", "").lower()
    if "zip" in ct:
        return ".zip"
    return Path(download_url.split("?")[0]).suffix.lower()


def download_and_extract(
    download_url: str,
    pack_name: str,
    dest_dir: str,
    progress_cb: Callable[[int, str], None] | None = None,
) -> dict:
    dest = Path(dest_dir)
    if not dest.is_dir():
        return {"success": False, "error": "Dossier de packs introuvable."}

    tmp_dir = tempfile.mkdtemp(prefix="graphlauncher_ws_")
    tmp_file = Path(tmp_dir) / "pack_download"

    try:
        if progress_cb:
            progress_cb(5, "Connexion au serveur…")

        req = urllib.request.Request(
            download_url, headers={"User-Agent": "GraphLauncher"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            ext = _detect_ext(resp, download_url)
            if ext != ".zip":
                return {
                    "success": False,
                    "error": f"Format '{ext or '?'}' non supporté — utilisez .zip.",
                }

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
