"""Update checker — queries GitHub Releases API."""

import json
import urllib.request

from utils.logger import get_logger

logger = get_logger(__name__)

APP_VERSION = "1.2.8"
RELEASES_API = "https://api.github.com/repos/GraphDevelopment/GraphLauncher/releases/latest"
RELEASES_PAGE = "https://github.com/GraphDevelopment/GraphLauncher/releases/latest"


def check_for_update() -> dict:
    try:
        req = urllib.request.Request(
            RELEASES_API,
            headers={"User-Agent": f"GraphLauncher/{APP_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        latest = data.get("tag_name", "").lstrip("v")
        has_update = bool(latest) and latest != APP_VERSION
        return {
            "success": True,
            "has_update": has_update,
            "current": APP_VERSION,
            "latest": latest,
            "url": RELEASES_PAGE,
        }
    except Exception as exc:
        logger.warning("Update check failed: %s", exc)
        return {"success": False, "has_update": False}
