from pathlib import Path

UPLOAD_ROOT = Path("data/uploads")
ATTACHMENTS_DIR = UPLOAD_ROOT / "attachments"
FILES_DIR = UPLOAD_ROOT / "files"


def ensure_storage_dirs() -> None:
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
