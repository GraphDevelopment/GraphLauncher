"""Workshop — fetches pack catalogue from GitHub and downloads packs."""

import json
import re
import shutil
import subprocess
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

_WINRAR_PATHS = [
    r"C:\Program Files\WinRAR\WinRAR.exe",
    r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
]
_SEVENZ_PATHS = [
    r"C:\Program Files\7-Zip\7z.exe",
    r"C:\Program Files (x86)\7-Zip\7z.exe",
]


def _find_extractor() -> tuple[str, str] | tuple[None, None]:
    for p in _SEVENZ_PATHS:
        if Path(p).exists():
            return ("7z", p)
    for p in _WINRAR_PATHS:
        if Path(p).exists():
            return ("winrar", p)
    return (None, None)


def fetch_workshop() -> dict:
    try:
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
    if "rar" in ct:
        return ".rar"
    return Path(download_url.split("?")[0]).suffix.lower()


def _extract_zip(tmp_file: Path, pack_dest: Path, progress_cb: Callable | None) -> None:
    with zipfile.ZipFile(tmp_file) as zf:
        names = zf.namelist()
        for i, name in enumerate(names):
            zf.extract(name, pack_dest)
            if progress_cb and names:
                progress_cb(76 + int((i + 1) / len(names) * 22), f"Extraction… {i + 1}/{len(names)}")


def _extract_rar(tmp_file: Path, pack_dest: Path, progress_cb: Callable | None) -> None:
    kind, exe = _find_extractor()
    if kind is None:
        raise RuntimeError(
            "Aucun extracteur .rar trouvé. Installez 7-Zip ou WinRAR."
        )

    pack_dest.mkdir(parents=True, exist_ok=True)
    dest_str = str(pack_dest)

    if kind == "7z":
        cmd = [exe, "x", str(tmp_file), f"-o{dest_str}", "-y"]
    else:  # winrar
        cmd = [exe, "x", "-y", "-inul", str(tmp_file), dest_str + "\\"]

    if progress_cb:
        progress_cb(78, "Extraction .rar…")

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode not in (0, 1):  # WinRAR returns 1 for warnings
        raise RuntimeError(result.stderr.decode(errors="replace").strip() or "Erreur d'extraction")

    if progress_cb:
        progress_cb(100, "Terminé")


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
            if ext not in (".zip", ".rar"):
                return {
                    "success": False,
                    "error": f"Format '{ext or '?'}' non supporté — utilisez .zip ou .rar.",
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

        if ext == ".zip":
            _extract_zip(tmp_file, pack_dest, progress_cb)
        else:
            _extract_rar(tmp_file, pack_dest, progress_cb)

        if progress_cb:
            progress_cb(100, "Terminé")

        logger.info("Workshop pack extracted: %s → %s", pack_name, pack_dest)
        return {"success": True, "path": str(pack_dest)}

    except Exception as exc:
        logger.error("download_and_extract: %s", exc)
        return {"success": False, "error": str(exc)}

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
