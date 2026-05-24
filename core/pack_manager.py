"""Pack detection, tagging and installation engine."""

import re
from pathlib import Path

from database.db_manager import DatabaseManager
from services.file_service import FileService
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Tag detection rules ────────────────────────────────────────────────────── #

_TAG_RULES: dict[str, list[str]] = {
    "MODS":       ["mods"],
    "CITIZEN":    ["citizen"],
    "PLUGIN":     ["plugins", "plugin"],
    "RESHADE":    ["reshade-shaders", "reshade_shaders", "reshade shaders", "reshade"],
    "ENB":        ["enbseries", "enb"],
    "SOUND PACK": ["pack son", "pack_son", "sound pack", "sound_pack", "audio", "sfx", "sons"],
}

_RESHADE_FILES = {"reshade.ini", "reshade32.dll", "reshade64.dll", "reshade-shaders"}
_ENB_FILES = {"enbseries.ini", "enblocal.ini", "enb"}

# Directories that map to FiveM Application Data sub-folders
_FIVEM_SUBDIRS = {"mods", "plugins", "citizen"}

# Directories whose *content* is copied to GTA V root
_GTA_DIRS = {"gta5", "gta v", "gta_v", "gta"}

# Directories whose *content* is copied to FiveM Application Data root
_FIVEM_ROOT_DIRS = {"fivem"}

# Sound pack source folder names
_SOUND_DIRS = {"pack son", "pack_son", "sound pack", "sound_pack", "audio", "sfx", "sons", "sound"}


def _norm(name: str) -> str:
    return name.strip().lower()


# ── Public types ───────────────────────────────────────────────────────────── #

class PackInfo:
    def __init__(self, path: Path, installed: bool, tags: list[str]) -> None:
        self.path = path
        self.name = path.name
        self.installed = installed
        self.tags = tags

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": str(self.path),
            "installed": self.installed,
            "tags": self.tags,
        }


# ── PackManager ────────────────────────────────────────────────────────────── #

class PackManager:
    def __init__(self) -> None:
        self.db = DatabaseManager()
        self.fs = FileService()

    # ------------------------------------------------------------------ #
    #  Scanning                                                            #
    # ------------------------------------------------------------------ #

    def scan_packs(self, directory: str) -> list[dict]:
        root = Path(directory)
        if not root.exists():
            logger.warning("Pack directory not found: %s", directory)
            return []

        installed_names = {p["name"] for p in self.db.get_installed_packs()}
        packs: list[dict] = []

        for item in sorted(root.iterdir()):
            if not item.is_dir():
                continue
            tags = self._detect_tags(item)
            info = PackInfo(
                path=item,
                installed=item.name in installed_names,
                tags=tags,
            )
            packs.append(info.to_dict())
            logger.debug("Found pack: %s  tags=%s", item.name, tags)

        logger.info("Scanned %d packs in %s", len(packs), directory)
        return packs

    def _detect_tags(self, pack_path: Path) -> list[str]:
        tags: set[str] = set()

        for item in pack_path.iterdir():
            n = _norm(item.name)

            if item.is_dir():
                for tag, patterns in _TAG_RULES.items():
                    if any(n == p or n.startswith(p) for p in patterns):
                        tags.add(tag)
                if n in _GTA_DIRS:
                    tags.add("GTA")
                if n in _FIVEM_ROOT_DIRS:
                    tags.add("FIVEM")

            elif item.is_file():
                if n in _RESHADE_FILES or n.startswith("reshade"):
                    tags.add("RESHADE")
                if n in _ENB_FILES or n.startswith("enb"):
                    tags.add("ENB")
                if n.endswith(".rpf"):
                    tags.add("SOUND PACK")

        return sorted(tags)

    # ------------------------------------------------------------------ #
    #  Installation                                                        #
    # ------------------------------------------------------------------ #

    def install_pack(
        self,
        pack_path: str,
        fivem_data_dir: str,
        gtav_dir: str,
        progress_cb=None,
    ) -> dict:
        pack = Path(pack_path)
        fivem_data = Path(fivem_data_dir)
        gtav = Path(gtav_dir)

        if not pack.exists():
            return {"success": False, "error": "Dossier du pack introuvable."}

        manifest: dict[str, list[str]] = {"copied": []}
        errors: list[str] = []

        def _progress(pct: int, msg: str) -> None:
            if progress_cb:
                progress_cb(pct, msg)

        # Unwrap single-root archives: if the pack folder contains exactly one
        # subfolder that doesn't match any known installation pattern, treat its
        # contents as the real pack root (common with poorly-structured archives).
        _known = _FIVEM_SUBDIRS | _FIVEM_ROOT_DIRS | _GTA_DIRS | _SOUND_DIRS
        _top = [i for i in pack.iterdir() if not i.name.startswith('.')]
        if len(_top) == 1 and _top[0].is_dir() and _norm(_top[0].name) not in _known:
            pack = _top[0]
            logger.info("Single-root archive detected, unwrapping to: %s", pack)

        _progress(0, "Analyse du pack…")
        total_steps = max(sum(1 for i in pack.iterdir() if i.is_dir() or i.is_file()), 1)
        step = 0

        for item in pack.iterdir():
            n = _norm(item.name)
            step += 1
            base_pct = int(step / total_steps * 90)
            _progress(base_pct, f"Traitement : {item.name}")

            try:
                # ── FiveM sub-directories ──────────────────────────────
                if item.is_dir() and n in _FIVEM_SUBDIRS:
                    dst = fivem_data / n  # always lowercase
                    copied = self.fs.copy_directory(item, dst, lowercase_dst=True)
                    manifest["copied"].extend(copied)
                    logger.info("Installed %s -> %s", item.name, dst)

                # ── FiveM root content ─────────────────────────────────
                elif item.is_dir() and n in _FIVEM_ROOT_DIRS:
                    copied = self.fs.copy_directory(item, fivem_data)
                    manifest["copied"].extend(copied)
                    logger.info("Installed FiveM root content -> %s", fivem_data)

                # ── GTA V root content ─────────────────────────────────
                elif item.is_dir() and n in _GTA_DIRS:
                    copied = self.fs.copy_directory(item, gtav)
                    manifest["copied"].extend(copied)
                    logger.info("Installed GTA5 root content -> %s", gtav)

                # ── Sound pack (.rpf files) ────────────────────────────
                elif item.is_dir() and n in _SOUND_DIRS:
                    sfx_dst = gtav / "x64" / "audio" / "sfx"
                    rpf_files = list(item.rglob("*.rpf"))
                    if rpf_files:
                        copied = self.fs.copy_files(rpf_files, sfx_dst)
                        manifest["copied"].extend(copied)
                        logger.info("Installed %d .rpf files -> %s", len(rpf_files), sfx_dst)

                # ── ReShade (root-level files) ─────────────────────────
                elif item.is_file() and (
                    _norm(item.name) in _RESHADE_FILES
                    or _norm(item.name).startswith("reshade")
                ):
                    copied = self.fs.copy_files([item], fivem_data)
                    manifest["copied"].extend(copied)

                # ── ENB (root-level) ───────────────────────────────────
                elif item.is_dir() and n.startswith("enb"):
                    copied = self.fs.copy_directory(item, fivem_data / item.name)
                    manifest["copied"].extend(copied)

            except Exception as exc:  # noqa: BLE001
                logger.error("Error installing %s: %s", item.name, exc)
                errors.append(str(exc))

        _progress(95, "Enregistrement en base…")
        tags = self._detect_tags(pack)
        self.db.add_installed_pack(pack.name, str(pack), tags, manifest)
        self.db.add_history(
            "install",
            pack.name,
            f"Fichiers copiés : {len(manifest['copied'])}",
            "success" if not errors else "partial",
        )

        _progress(100, "Installation terminée !")
        logger.info("Pack '%s' installed: %d files", pack.name, len(manifest["copied"]))
        return {
            "success": True,
            "pack_name": pack.name,
            "files_copied": len(manifest["copied"]),
            "errors": errors,
        }

    # ------------------------------------------------------------------ #
    #  Uninstall                                                           #
    # ------------------------------------------------------------------ #

    def uninstall_pack(self, pack_name: str) -> dict:
        manifest = self.db.get_pack_manifest(pack_name)
        copied = manifest.get("copied", [])

        deleted, failed = self.fs.safe_delete_files(copied)

        self.db.remove_installed_pack(pack_name)
        self.db.add_history(
            "uninstall",
            pack_name,
            f"Fichiers supprimés : {len(deleted)}, échecs : {len(failed)}",
        )
        logger.info("Pack '%s' uninstalled: %d deleted, %d failed", pack_name, len(deleted), len(failed))
        return {"success": True, "deleted": len(deleted), "failed": failed}
