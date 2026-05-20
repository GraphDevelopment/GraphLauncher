"""Backup / rollback system.

Before every install we snapshot the destination files that will be
overwritten into data/backups/<pack_name>_<timestamp>/.
A manifest.json file lists every backed-up file and its original location
so that a rollback can restore everything precisely.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from utils.logger import get_logger
from utils.paths import get_backups_dir

logger = get_logger(__name__)


class BackupManager:
    # ------------------------------------------------------------------ #
    #  Create                                                              #
    # ------------------------------------------------------------------ #

    def create(self, pack_name: str, files_to_backup: list[Path]) -> Path:
        """Copy *files_to_backup* into a timestamped backup folder.

        Returns the backup directory path.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in pack_name)
        backup_dir = get_backups_dir() / f"{safe_name}_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        manifest: list[dict] = []
        for src in files_to_backup:
            if not src.exists():
                continue
            rel = Path(*src.parts[1:])  # strip drive letter
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            manifest.append({"original": str(src), "backup": str(dst)})
            logger.debug("Backed up %s", src)

        (backup_dir / "manifest.json").write_text(
            json.dumps({"pack": pack_name, "created": ts, "files": manifest}, indent=2),
            encoding="utf-8",
        )
        logger.info("Backup created for '%s': %d files -> %s", pack_name, len(manifest), backup_dir)
        return backup_dir

    # ------------------------------------------------------------------ #
    #  Rollback                                                            #
    # ------------------------------------------------------------------ #

    def rollback(self, backup_dir: Path) -> dict:
        manifest_path = backup_dir / "manifest.json"
        if not manifest_path.exists():
            return {"success": False, "error": "Manifest de sauvegarde introuvable."}

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        restored, failed = [], []

        for entry in manifest.get("files", []):
            src = Path(entry["backup"])
            dst = Path(entry["original"])
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                restored.append(str(dst))
            except OSError as exc:
                logger.error("Rollback failed for %s: %s", dst, exc)
                failed.append(str(dst))

        logger.info(
            "Rollback '%s': %d restored, %d failed",
            manifest.get("pack", "?"),
            len(restored),
            len(failed),
        )
        return {"success": not failed, "restored": restored, "failed": failed}

    # ------------------------------------------------------------------ #
    #  List                                                                #
    # ------------------------------------------------------------------ #

    def list_backups(self) -> list[dict]:
        backups = []
        for d in sorted(get_backups_dir().iterdir(), reverse=True):
            if not d.is_dir():
                continue
            manifest_path = d / "manifest.json"
            if not manifest_path.exists():
                continue
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            backups.append(
                {
                    "path": str(d),
                    "pack": m.get("pack", d.name),
                    "created": m.get("created", ""),
                    "file_count": len(m.get("files", [])),
                }
            )
        return backups
