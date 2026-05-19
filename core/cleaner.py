"""FiveM and GTA V cleaning utilities."""

import shutil
from pathlib import Path

from core.baseline import BaselineManager
from database.db_manager import DatabaseManager
from services.file_service import FileService
from utils.logger import get_logger

logger = get_logger(__name__)

# Directories inside FiveM Application Data that pack installs touch
_FIVEM_MOD_DIRS = ["mods", "plugins"]
_FIVEM_RESHADE_PATTERNS = ["reshade*", "dxgi.dll", "d3d11.dll"]

# GTA V known-mod file extensions (never official)
_GTAV_MOD_EXTENSIONS = {".asi", ".log"}
_GTAV_MOD_FILENAMES = {
    "dinput8.dll",
    "scripthookv.dll",
    "scripthookv.net.dll",
    "scripthookv.net2.dll",
    "scripthookv.net3.dll",
    "reshade32.dll",
    "reshade64.dll",
    "dxgi.dll",
}


class Cleaner:
    def __init__(self) -> None:
        self.db = DatabaseManager()
        self.fs = FileService()
        self.baseline = BaselineManager()

    # ------------------------------------------------------------------ #
    #  FiveM cleaner                                                       #
    # ------------------------------------------------------------------ #

    def clean_fivem(self, fivem_data_dir: str, progress_cb=None) -> dict:
        data = Path(fivem_data_dir)
        if not data.exists():
            return {"success": False, "error": "FiveM Application Data introuvable."}

        deleted: list[str] = []
        failed: list[str] = []

        def _prog(pct: int, msg: str) -> None:
            if progress_cb:
                progress_cb(pct, msg)

        _prog(0, "Analyse FiveM…")

        # 1. Remove mod directories
        for d_name in _FIVEM_MOD_DIRS:
            target = data / d_name
            if target.exists():
                _prog(20, f"Suppression {d_name}…")
                if self.fs.safe_delete(target):
                    deleted.append(str(target))
                    logger.info("Deleted FiveM dir: %s", target)
                else:
                    failed.append(str(target))

        # 2. Remove ReShade files
        _prog(50, "Nettoyage ReShade…")
        for pattern in _FIVEM_RESHADE_PATTERNS:
            for f in data.glob(pattern):
                if self.fs.safe_delete(f):
                    deleted.append(str(f))
                else:
                    failed.append(str(f))

        # 3. Remove all tracked installed files
        _prog(70, "Suppression des fichiers de packs…")
        installed_packs = self.db.get_installed_packs()
        for pack in installed_packs:
            manifest = pack.get("install_manifest", {})
            for fp in manifest.get("copied", []):
                p = Path(fp)
                if fivem_data_dir.lower() in str(p).lower():
                    if self.fs.safe_delete(p):
                        deleted.append(fp)
                    else:
                        failed.append(fp)

        # 4. Clear graphics cache
        _prog(85, "Nettoyage du cache…")
        cache_dir = data / "cache" / "game"
        if cache_dir.exists():
            for item in cache_dir.iterdir():
                if self.fs.safe_delete(item):
                    deleted.append(str(item))

        _prog(100, "Nettoyage FiveM terminé !")
        self.db.add_history("clean_fivem", details=f"Supprimé : {len(deleted)} éléments")
        logger.info("FiveM clean: %d deleted, %d failed", len(deleted), len(failed))
        return {"success": True, "deleted": len(deleted), "failed": failed}

    # ------------------------------------------------------------------ #
    #  GTA V cleaner                                                       #
    # ------------------------------------------------------------------ #

    def clean_gtav(self, gtav_dir: str, progress_cb=None) -> dict:
        root = Path(gtav_dir)
        if not root.exists():
            return {"success": False, "error": "Dossier GTA V introuvable."}

        deleted: list[str] = []
        failed: list[str] = []
        protected: list[str] = []

        def _prog(pct: int, msg: str) -> None:
            if progress_cb:
                progress_cb(pct, msg)

        _prog(0, "Analyse GTA V…")

        # 1. Remove pack-tracked files in GTA V
        _prog(15, "Suppression des fichiers de packs…")
        installed_packs = self.db.get_installed_packs()
        for pack in installed_packs:
            manifest = pack.get("install_manifest", {})
            for fp in manifest.get("copied", []):
                p = Path(fp)
                if gtav_dir.lower() in str(p).lower():
                    if self.fs.safe_delete(p):
                        deleted.append(fp)
                    else:
                        failed.append(fp)

        # 2. Scan root for well-known mod files
        _prog(40, "Détection des mods connus…")
        for item in root.iterdir():
            if not item.is_file():
                continue
            n = item.name.lower()
            if n in _GTAV_MOD_FILENAMES or item.suffix.lower() in _GTAV_MOD_EXTENSIONS:
                if self.baseline.is_official(root, item):
                    protected.append(str(item))
                    continue
                if self.fs.safe_delete(item):
                    deleted.append(str(item))
                else:
                    failed.append(str(item))

        # 3. Use baseline to find truly unknown files (if baseline exists)
        if self.baseline.exists():
            _prog(65, "Vérification de la baseline…")
            unknown = self.baseline.get_unknown_files(root)
            for fp in unknown:
                # Only auto-delete safe extensions; leave .rpf, .exe, etc. alone
                if fp.suffix.lower() in _GTAV_MOD_EXTENSIONS or fp.name.lower() in _GTAV_MOD_FILENAMES:
                    if self.fs.safe_delete(fp):
                        deleted.append(str(fp))
                    else:
                        failed.append(str(fp))

        # 4. ReShade / ENB folders
        _prog(85, "Suppression ReShade / ENB…")
        for folder_name in ["reshade-shaders", "enbseries", "enb"]:
            folder = root / folder_name
            if folder.exists():
                if self.fs.safe_delete(folder):
                    deleted.append(str(folder))

        _prog(100, "Nettoyage GTA V terminé !")
        self.db.add_history(
            "clean_gtav",
            details=f"Supprimé : {len(deleted)}, protégé : {len(protected)}",
        )
        logger.info(
            "GTA V clean: %d deleted, %d failed, %d protected",
            len(deleted), len(failed), len(protected),
        )
        return {
            "success": True,
            "deleted": len(deleted),
            "failed": failed,
            "protected": len(protected),
        }

    # ------------------------------------------------------------------ #
    #  Preview (dry-run)                                                   #
    # ------------------------------------------------------------------ #

    def preview_fivem_clean(self, fivem_data_dir: str) -> dict:
        data = Path(fivem_data_dir)
        targets: list[str] = []

        for d_name in _FIVEM_MOD_DIRS:
            t = data / d_name
            if t.exists():
                targets.append(str(t))

        for pattern in _FIVEM_RESHADE_PATTERNS:
            for f in data.glob(pattern):
                targets.append(str(f))

        return {"targets": targets, "count": len(targets)}
