"""GTA V clean-baseline system.

On first creation we hash every file in the GTA V directory and persist the
result to data/clean_files.json.  The cleaner uses this index to decide which
files are official (never delete) vs. added by mods (safe to delete).
"""

import json
from pathlib import Path

from services.hash_service import file_fingerprint
from utils.logger import get_logger
from utils.paths import get_baseline_path

logger = get_logger(__name__)


class BaselineManager:
    def __init__(self) -> None:
        self._baseline: dict[str, dict] | None = None

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #

    def _load(self) -> dict[str, dict]:
        if self._baseline is not None:
            return self._baseline
        path = get_baseline_path()
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._baseline = data.get("files", {})
            logger.info("Baseline loaded: %d entries", len(self._baseline))
        else:
            self._baseline = {}
        return self._baseline

    def _save(self, baseline: dict[str, dict]) -> None:
        path = get_baseline_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"files": baseline}, f, indent=2, ensure_ascii=False)
        self._baseline = baseline
        logger.info("Baseline saved: %d entries", len(baseline))

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def exists(self) -> bool:
        return get_baseline_path().exists()

    def create(
        self,
        gtav_path: str,
        progress_cb=None,
    ) -> dict:
        root = Path(gtav_path)
        if not root.exists():
            return {"success": False, "error": "Dossier GTA V introuvable."}

        all_files = [f for f in root.rglob("*") if f.is_file()]
        total = max(len(all_files), 1)
        baseline: dict[str, dict] = {}

        for i, fp in enumerate(all_files, 1):
            try:
                rel = str(fp.relative_to(root))
                fingerprint = file_fingerprint(fp)
                baseline[rel] = fingerprint
            except (OSError, ValueError) as exc:
                logger.warning("Skipped %s: %s", fp, exc)

            if progress_cb:
                progress_cb(int(i / total * 100), f"Analyse : {fp.name}")

        self._save(baseline)
        logger.info("GTA V baseline created: %d files", len(baseline))
        return {"success": True, "file_count": len(baseline)}

    def is_official(self, gtav_root: Path, file_path: Path) -> bool:
        """Return True if *file_path* is listed in the clean baseline."""
        baseline = self._load()
        if not baseline:
            return False
        try:
            rel = str(file_path.relative_to(gtav_root))
        except ValueError:
            return False
        return rel in baseline

    def get_unknown_files(self, gtav_root: Path) -> list[Path]:
        """Return files present in *gtav_root* that are NOT in the baseline."""
        baseline = self._load()
        if not baseline:
            return []

        unknown: list[Path] = []
        for fp in gtav_root.rglob("*"):
            if not fp.is_file():
                continue
            try:
                rel = str(fp.relative_to(gtav_root))
            except ValueError:
                continue
            if rel not in baseline:
                unknown.append(fp)
        return unknown

    def stats(self) -> dict:
        baseline = self._load()
        return {"exists": self.exists(), "file_count": len(baseline)}
