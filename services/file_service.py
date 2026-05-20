import os
import shutil
import threading
from collections.abc import Callable
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

ProgressCb = Callable[[int, str], None]

# Paths that must never be touched
_SYSTEM_ROOTS = {
    Path("C:/Windows"),
    Path("C:/System32"),
    Path(os.environ.get("SYSTEMROOT", "C:/Windows")),
}


def _is_safe_path(path: Path) -> bool:
    resolved = path.resolve()
    for root in _SYSTEM_ROOTS:
        try:
            resolved.relative_to(root.resolve())
            return False
        except ValueError:
            pass
    return True


class FileService:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Copy helpers                                                        #
    # ------------------------------------------------------------------ #

    def copy_directory(
        self,
        src: Path,
        dst: Path,
        progress: ProgressCb | None = None,
        lowercase_dst: bool = False,
    ) -> list[str]:
        """Copy *src* tree into *dst*.  Returns list of copied destination paths."""
        if not _is_safe_path(dst):
            raise PermissionError(f"Destination refusée (chemin système) : {dst}")

        dst.mkdir(parents=True, exist_ok=True)
        all_files = list(src.rglob("*"))
        total = max(len(all_files), 1)
        copied: list[str] = []

        for i, item in enumerate(all_files, 1):
            rel = item.relative_to(src)
            rel_str = str(rel).lower() if lowercase_dst else str(rel)
            target = dst / rel_str

            if progress:
                progress(int(i / total * 100), f"Copie : {item.name}")

            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
                copied.append(str(target))
                logger.debug("Copied %s -> %s", item, target)

        return copied

    def copy_files(
        self,
        files: list[Path],
        dst_dir: Path,
        progress: ProgressCb | None = None,
    ) -> list[str]:
        """Copy individual *files* into *dst_dir*."""
        if not _is_safe_path(dst_dir):
            raise PermissionError(f"Destination refusée : {dst_dir}")

        dst_dir.mkdir(parents=True, exist_ok=True)
        total = max(len(files), 1)
        copied: list[str] = []

        for i, f in enumerate(files, 1):
            target = dst_dir / f.name
            if progress:
                progress(int(i / total * 100), f"Copie : {f.name}")
            shutil.copy2(f, target)
            copied.append(str(target))
            logger.debug("Copied file %s -> %s", f, target)

        return copied

    # ------------------------------------------------------------------ #
    #  Delete helpers                                                      #
    # ------------------------------------------------------------------ #

    def safe_delete(self, path: Path, *, dry_run: bool = False) -> bool:
        """Delete file or directory.  Returns True on success."""
        if not _is_safe_path(path):
            logger.error("Refused to delete system path: %s", path)
            return False

        if not path.exists():
            return True

        try:
            if dry_run:
                logger.info("[DRY-RUN] Would delete: %s", path)
                return True
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.info("Deleted: %s", path)
            return True
        except OSError as exc:
            logger.error("Failed to delete %s: %s", path, exc)
            return False

    def safe_delete_files(
        self,
        paths: list[str],
        *,
        dry_run: bool = False,
    ) -> tuple[list[str], list[str]]:
        """Delete a list of path strings.  Returns (deleted, failed)."""
        deleted, failed = [], []
        for p_str in paths:
            p = Path(p_str)
            if self.safe_delete(p, dry_run=dry_run):
                deleted.append(p_str)
            else:
                failed.append(p_str)
        return deleted, failed
