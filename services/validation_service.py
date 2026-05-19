from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

_GTAV_REQUIRED = {"GTA5.exe", "GTAVLauncher.exe", "x64b.rpf", "x64v.rpf"}

# FiveM data folder — name changed between versions
# Newer : FiveM.app   |   Older : FiveM Application Data
_FIVEM_DATA_CANDIDATES = ["FiveM.app", "FiveM Application Data"]


class ValidationService:
    def validate_gtav(self, path: str) -> dict:
        p = Path(path)
        if not p.exists() or not p.is_dir():
            return {"valid": False, "error": "Le dossier GTA V n'existe pas."}

        missing = [f for f in _GTAV_REQUIRED if not (p / f).exists()]
        if missing:
            return {
                "valid": False,
                "error": f"Fichiers GTA V manquants : {', '.join(missing)}",
            }

        logger.info("GTA V path validated: %s", path)
        return {"valid": True}

    def validate_fivem(self, path: str) -> dict:
        p = Path(path)

        if p.is_file() and p.suffix.lower() == ".exe":
            parent = p.parent
        elif p.is_dir():
            parent = p
        else:
            return {"valid": False, "error": "Chemin FiveM invalide (sélectionnez FiveM.exe)."}

        # Try every known data-folder name (case-insensitive on Windows)
        data_dir: Path | None = None
        for name in _FIVEM_DATA_CANDIDATES:
            candidate = parent / name
            if candidate.exists() and candidate.is_dir():
                data_dir = candidate
                break

        # Last-resort: scan the parent for any folder that looks like the data dir
        if data_dir is None:
            for item in parent.iterdir():
                if item.is_dir() and "fivem" in item.name.lower() and "app" in item.name.lower():
                    data_dir = item
                    logger.info("FiveM data dir found by fuzzy search: %s", item)
                    break

        if data_dir is None:
            searched = ", ".join(f"'{n}'" for n in _FIVEM_DATA_CANDIDATES)
            return {
                "valid": False,
                "error": (
                    f"Dossier de données FiveM introuvable dans '{parent}'.\n"
                    f"Cherché : {searched}.\n"
                    f"Vérifiez que FiveM a déjà été lancé au moins une fois."
                ),
            }

        logger.info("FiveM validated: %s  data_dir=%s", path, data_dir)
        return {"valid": True, "data_dir": str(data_dir)}
