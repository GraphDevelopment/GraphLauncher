"""PyWebView API bridge – all methods callable from JavaScript."""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import webview

from core.backup import BackupManager
from core.baseline import BaselineManager
from core.cleaner import Cleaner
from core.pack_manager import PackManager
from database.db_manager import DatabaseManager
from services.validation_service import ValidationService
from utils.logger import get_logger

logger = get_logger(__name__)


class API:
    def __init__(self) -> None:
        self._window: Any = None   # pywebview.Window (typed as Any for compat)
        self._maximized: bool = False
        self._db = DatabaseManager()
        self._pack_manager = PackManager()
        self._cleaner = Cleaner()
        self._backup_manager = BackupManager()
        self._baseline_manager = BaselineManager()
        self._validator = ValidationService()
        self._busy = False
        self._busy_lock = threading.Lock()

    def set_window(self, window: Any) -> None:
        self._window = window

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _push(self, event: str, data: dict) -> None:
        if not self._window:
            return
        try:
            # Use btoa/atob encoding to safely pass arbitrary JSON
            import base64
            encoded = base64.b64encode(json.dumps(data).encode()).decode()
            js = (
                f"(function(){{"
                f"var d=JSON.parse(atob('{encoded}'));"
                f"window.__pyEvent&&window.__pyEvent('{event}',d);"
                f"}})();"
            )
            self._window.evaluate_js(js)
        except Exception as exc:
            logger.warning("_push failed: %s", exc)

    def _push_progress(self, pct: int, msg: str) -> None:
        self._push("progress", {"percent": pct, "message": msg})

    def _acquire(self) -> bool:
        with self._busy_lock:
            if self._busy:
                return False
            self._busy = True
            return True

    def _release(self) -> None:
        with self._busy_lock:
            self._busy = False

    # ------------------------------------------------------------------ #
    #  Window controls                                                     #
    # ------------------------------------------------------------------ #

    def minimize_window(self) -> None:
        if self._window:
            self._window.minimize()

    def toggle_maximize(self) -> None:
        if not self._window:
            return
        if self._maximized:
            self._window.restore()
            self._maximized = False
        else:
            self._window.maximize()
            self._maximized = True

    def close_window(self) -> None:
        if self._window:
            self._window.destroy()

    # ------------------------------------------------------------------ #
    #  Settings                                                            #
    # ------------------------------------------------------------------ #

    def get_settings(self) -> dict:
        defaults = {
            "packs_dir": "",
            "fivem_exe": "",
            "fivem_data_dir": "",
            "gtav_dir": "",
            "first_run": True,
        }
        stored = self._db.get_all_settings()
        return {**defaults, **stored}

    def save_settings(self, settings: dict) -> dict:
        try:
            self._db.save_settings(settings)
            logger.info("Settings saved")
            return {"success": True}
        except Exception as exc:
            logger.error("save_settings error: %s", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    #  Validation                                                          #
    # ------------------------------------------------------------------ #

    def validate_gtav(self, path: str) -> dict:
        return self._validator.validate_gtav(path)

    def validate_fivem(self, path: str) -> dict:
        result = self._validator.validate_fivem(path)
        if result.get("valid") and "data_dir" in result:
            self._db.set_setting("fivem_data_dir", result["data_dir"])
        return result

    # ------------------------------------------------------------------ #
    #  File dialogs                                                        #
    # ------------------------------------------------------------------ #

    def select_folder(self) -> dict:
        if not self._window:
            return {"success": False, "error": "Window not ready"}
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return {"success": True, "path": result[0]}
        return {"success": False}

    def select_fivem_exe(self) -> dict:
        if not self._window:
            return {"success": False}
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Executable Files (*.exe)", "All Files (*.*)"),
        )
        if result:
            return {"success": True, "path": result[0]}
        return {"success": False}

    # ------------------------------------------------------------------ #
    #  Pack management                                                     #
    # ------------------------------------------------------------------ #

    def scan_packs(self) -> dict:
        packs_dir = self._db.get_setting("packs_dir", "")
        if not packs_dir:
            return {"success": False, "error": "Dossier des packs non configuré."}
        try:
            packs = self._pack_manager.scan_packs(packs_dir)
            return {"success": True, "packs": packs}
        except Exception as exc:
            logger.error("scan_packs error: %s", exc)
            return {"success": False, "error": str(exc)}

    def install_pack(self, pack_path: str) -> dict:
        if not self._acquire():
            return {"success": False, "error": "Une opération est déjà en cours."}

        settings = self.get_settings()
        fivem_data = settings.get("fivem_data_dir", "")
        gtav_dir = settings.get("gtav_dir", "")

        if not fivem_data:
            self._release()
            return {"success": False, "error": "FiveM Application Data non configuré."}
        if not gtav_dir:
            self._release()
            return {"success": False, "error": "Dossier GTA V non configuré."}

        def _run() -> None:
            try:
                self._push("operation-start", {"title": "Installation du pack"})
                result = self._pack_manager.install_pack(
                    pack_path,
                    fivem_data,
                    gtav_dir,
                    progress_cb=self._push_progress,
                )
                self._push("operation-end", result)
            except Exception as exc:
                logger.error("install_pack thread error: %s", exc)
                self._push("operation-end", {"success": False, "error": str(exc)})
            finally:
                self._release()

        threading.Thread(target=_run, daemon=True).start()
        return {"success": True, "message": "Installation démarrée"}

    def uninstall_pack(self, pack_name: str) -> dict:
        if not self._acquire():
            return {"success": False, "error": "Une opération est déjà en cours."}

        def _run() -> None:
            try:
                self._push("operation-start", {"title": "Désinstallation"})
                result = self._pack_manager.uninstall_pack(pack_name)
                self._push("operation-end", result)
            except Exception as exc:
                logger.error("uninstall_pack error: %s", exc)
                self._push("operation-end", {"success": False, "error": str(exc)})
            finally:
                self._release()

        threading.Thread(target=_run, daemon=True).start()
        return {"success": True}

    def open_folder(self, path: str) -> dict:
        p = Path(path)
        if p.exists():
            subprocess.Popen(["explorer", str(p)])
            return {"success": True}
        # Fallback: treat as URL and open in browser
        if path.startswith("http"):
            subprocess.Popen(["start", "", path], shell=True)
            return {"success": True}
        return {"success": False, "error": "Dossier introuvable."}

    # ------------------------------------------------------------------ #
    #  Cleaners                                                            #
    # ------------------------------------------------------------------ #

    def preview_fivem_clean(self) -> dict:
        fivem_data = self._db.get_setting("fivem_data_dir", "")
        if not fivem_data:
            return {"success": False, "error": "FiveM non configuré."}
        return self._cleaner.preview_fivem_clean(fivem_data)

    def clean_fivem(self) -> dict:
        if not self._acquire():
            return {"success": False, "error": "Une opération est déjà en cours."}

        fivem_data = self._db.get_setting("fivem_data_dir", "")
        if not fivem_data:
            self._release()
            return {"success": False, "error": "FiveM non configuré."}

        def _run() -> None:
            try:
                self._push("operation-start", {"title": "Nettoyage FiveM"})
                result = self._cleaner.clean_fivem(fivem_data, self._push_progress)
                self._push("operation-end", result)
            except Exception as exc:
                logger.error("clean_fivem error: %s", exc)
                self._push("operation-end", {"success": False, "error": str(exc)})
            finally:
                self._release()

        threading.Thread(target=_run, daemon=True).start()
        return {"success": True}

    def clean_gtav(self) -> dict:
        if not self._acquire():
            return {"success": False, "error": "Une opération est déjà en cours."}

        gtav_dir = self._db.get_setting("gtav_dir", "")
        if not gtav_dir:
            self._release()
            return {"success": False, "error": "GTA V non configuré."}

        def _run() -> None:
            try:
                self._push("operation-start", {"title": "Nettoyage GTA V"})
                result = self._cleaner.clean_gtav(gtav_dir, self._push_progress)
                self._push("operation-end", result)
            except Exception as exc:
                logger.error("clean_gtav error: %s", exc)
                self._push("operation-end", {"success": False, "error": str(exc)})
            finally:
                self._release()

        threading.Thread(target=_run, daemon=True).start()
        return {"success": True}

    # ------------------------------------------------------------------ #
    #  Baseline                                                            #
    # ------------------------------------------------------------------ #

    def get_baseline_status(self) -> dict:
        return self._baseline_manager.stats()

    def create_gtav_baseline(self) -> dict:
        if not self._acquire():
            return {"success": False, "error": "Une opération est déjà en cours."}

        gtav_dir = self._db.get_setting("gtav_dir", "")
        if not gtav_dir:
            self._release()
            return {"success": False, "error": "GTA V non configuré."}

        def _run() -> None:
            try:
                self._push("operation-start", {"title": "Création de la baseline GTA V"})
                result = self._baseline_manager.create(gtav_dir, self._push_progress)
                self._push("operation-end", result)
            except Exception as exc:
                logger.error("create_baseline error: %s", exc)
                self._push("operation-end", {"success": False, "error": str(exc)})
            finally:
                self._release()

        threading.Thread(target=_run, daemon=True).start()
        return {"success": True}

    # ------------------------------------------------------------------ #
    #  Workshop                                                            #
    # ------------------------------------------------------------------ #

    def get_workshop_packs(self) -> dict:
        from services.workshop_service import fetch_workshop
        return fetch_workshop()

    def download_workshop_pack(self, download_url: str, pack_name: str) -> dict:
        if not self._acquire():
            return {"success": False, "error": "Une opération est déjà en cours."}

        packs_dir = self._db.get_setting("packs_dir", "")
        if not packs_dir:
            self._release()
            return {"success": False, "error": "Dossier de packs non configuré."}

        def _run() -> None:
            from services.workshop_service import download_and_extract
            try:
                self._push("operation-start", {"title": "Téléchargement du pack"})
                result = download_and_extract(
                    download_url, pack_name, packs_dir, self._push_progress
                )
                self._push("operation-end", result)
            except Exception as exc:
                logger.error("download_workshop_pack error: %s", exc)
                self._push("operation-end", {"success": False, "error": str(exc)})
            finally:
                self._release()

        threading.Thread(target=_run, daemon=True).start()
        return {"success": True}

    # ------------------------------------------------------------------ #
    #  Updates                                                             #
    # ------------------------------------------------------------------ #

    def check_for_update(self) -> dict:
        from services.update_service import check_for_update
        return check_for_update()

    # ------------------------------------------------------------------ #
    #  History & Logs                                                      #
    # ------------------------------------------------------------------ #

    def get_history(self, limit: int = 50) -> dict:
        return {"success": True, "history": self._db.get_history(limit)}

    def get_logs(self, limit: int = 100) -> dict:
        return {"success": True, "logs": self._db.get_logs(limit)}

    # ------------------------------------------------------------------ #
    #  App info                                                            #
    # ------------------------------------------------------------------ #

    def get_app_info(self) -> dict:
        from services.update_service import APP_VERSION
        return {
            "version": APP_VERSION,
            "python": sys.version,
            "baseline_exists": self._baseline_manager.exists(),
        }

    # ------------------------------------------------------------------ #
    #  Media helpers                                                       #
    # ------------------------------------------------------------------ #

    def fetch_image_b64(self, url: str) -> dict:
        """Fetch an external image server-side, return as base64 data URI."""
        import base64
        import urllib.request
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                ct = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            b64 = base64.b64encode(data).decode("ascii")
            return {"success": True, "src": f"data:{ct};base64,{b64}"}
        except Exception as exc:
            logger.warning("fetch_image_b64 %s: %s", url, exc)
            return {"success": False, "error": str(exc)}

    def get_video_stream_url(self, youtube_url: str) -> dict:
        """Extract playable stream URLs via yt-dlp.

        Preferred: separate H264 video + AAC audio URLs (up to 1080p+), played
        synchronised in <video>+<audio> elements — no ffmpeg needed.
        Fallback : best pre-muxed format (720p max without ffmpeg).
        """
        try:
            import yt_dlp
            ydl_opts = {"quiet": True, "no_warnings": True, "socket_timeout": 15}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)

            fmts = info.get("formats", [])

            def has_v(f): return f.get("vcodec") not in (None, "none", "")
            def has_a(f): return f.get("acodec") not in (None, "none", "")
            def is_h264(f): return "avc1" in (f.get("vcodec") or "")

            # Best H264 video-only stream
            v_fmts = sorted(
                [f for f in fmts if f.get("url") and has_v(f) and not has_a(f) and is_h264(f) and f.get("height", 0)],
                key=lambda f: (f.get("height", 0), f.get("tbr", 0)),
            )
            # Best AAC/MP4 audio-only stream
            a_fmts = sorted(
                [f for f in fmts if f.get("url") and has_a(f) and not has_v(f) and f.get("ext") in ("m4a", "mp4")],
                key=lambda f: f.get("abr", 0),
            )

            if v_fmts and a_fmts:
                bv, ba = v_fmts[-1], a_fmts[-1]
                return {
                    "success": True, "separate": True,
                    "video_url": bv["url"], "audio_url": ba["url"],
                    "height": bv.get("height", 0),
                    "title": info.get("title", ""),
                }

            # Fallback: best pre-muxed format
            muxed = sorted(
                [f for f in fmts if f.get("url") and has_v(f) and has_a(f)],
                key=lambda f: (f.get("height", 0), f.get("tbr", 0)),
            )
            if muxed:
                bm = muxed[-1]
                return {
                    "success": True, "separate": False,
                    "video_url": bm["url"],
                    "height": bm.get("height", 0),
                    "title": info.get("title", ""),
                }

            return {"success": False, "error": "Aucun format compatible trouvé"}
        except ImportError:
            return {"success": False, "error": "yt-dlp non disponible"}
        except Exception as exc:
            logger.error("get_video_stream_url: %s", exc)
            return {"success": False, "error": str(exc)}

    def open_video_window(self, youtube_url: str, title: str = "") -> dict:
        """Open a YouTube video in a new pywebview window (bypasses iframe embed restrictions)."""
        import re
        m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", youtube_url)
        if not m:
            return {"success": False, "error": "URL YouTube invalide"}
        vid_id = m.group(1)
        embed_url = f"https://www.youtube.com/embed/{vid_id}?autoplay=1&rel=0"
        try:
            webview.create_window(
                title=title or "Aperçu",
                url=embed_url,
                width=1280,
                height=720,
                resizable=True,
            )
            return {"success": True}
        except Exception as exc:
            logger.error("open_video_window: %s", exc)
            return {"success": False, "error": str(exc)}
