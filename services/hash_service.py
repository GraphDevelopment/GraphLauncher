import hashlib
from pathlib import Path

CHUNK = 65536


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def file_fingerprint(path: Path) -> dict:
    stat = path.stat()
    return {
        "size": stat.st_size,
        "hash": compute_sha256(path),
    }
