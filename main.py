"""Graph Launcher — entry point."""

import site
import sys

# ── Ensure user site-packages are reachable even in elevated terminals ──
# pip installs --user by default when the system site-packages is not
# writable (common on Windows).  When Python runs as Administrator the
# user site directory is silently excluded from sys.path.
try:
    _user_site = site.getusersitepackages()
    if isinstance(_user_site, str) and _user_site not in sys.path:
        sys.path.append(_user_site)  # append — stdlib stays first
except Exception:
    pass

from backend.api import API
from utils.logger import setup_logger
from utils.paths import get_index_html

import webview


def main() -> None:
    setup_logger()

    api = API()

    window = webview.create_window(
        title="Graph Launcher",
        url=get_index_html(),
        js_api=api,
        width=1280,
        height=800,
        min_size=(960, 640),
        resizable=True,
        frameless=True,
        easy_drag=False,
        background_color="#0f0f0f",
    )

    api.set_window(window)

    webview.start(debug="--debug" in sys.argv, http_server=True)


if __name__ == "__main__":
    main()
