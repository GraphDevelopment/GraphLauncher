"""Graph Launcher — entry point."""

import functools
import http.server
import site
import socket
import sys
import threading

# ── Ensure user site-packages are reachable even in elevated terminals ──
try:
    _user_site = site.getusersitepackages()
    if isinstance(_user_site, str) and _user_site not in sys.path:
        sys.path.append(_user_site)  # append — stdlib stays first
except Exception:
    pass

from backend.api import API
from utils.logger import setup_logger
from utils.paths import get_frontend_dir

import webview


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with access logs suppressed."""
    def log_message(self, fmt, *args):
        pass


def _start_file_server(directory: str, port: int) -> None:
    handler = functools.partial(_SilentHandler, directory=directory)
    http.server.HTTPServer(("127.0.0.1", port), handler).serve_forever()


def main() -> None:
    setup_logger()

    api = API()

    # Serve the frontend over a local HTTP server so WebView2 (which uses
    # file:// by default) can load external resources — external images and
    # YouTube iframes are blocked from a file:// origin by WebView2.
    port = _find_free_port()
    threading.Thread(
        target=_start_file_server,
        args=(str(get_frontend_dir()), port),
        daemon=True,
    ).start()

    window = webview.create_window(
        title="Graph Launcher",
        url=f"http://127.0.0.1:{port}/index.html",
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

    webview.start(debug="--debug" in sys.argv)


if __name__ == "__main__":
    main()
