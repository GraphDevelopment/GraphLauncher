import logging
from logging.handlers import RotatingFileHandler

from utils.paths import get_logs_dir

_logger: logging.Logger | None = None


def setup_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logs_dir = get_logs_dir()   # %LOCALAPPDATA%\Graph Launcher\logs\ when frozen

    logger = logging.getLogger("graph_launcher")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger(name: str = "graph_launcher") -> logging.Logger:
    if _logger is None:
        setup_logger()
    return logging.getLogger(name)
