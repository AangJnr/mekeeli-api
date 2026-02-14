import base64
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app import schemas
from app.chat.models import get_vision_model_name


UPLOAD_ROOT = Path("data/uploads")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}


def _is_image_attachment(attachment: schemas.Attachment) -> bool:
    if attachment.type and attachment.type.startswith("image/"):
        return True

    for candidate in (attachment.name, attachment.id, attachment.url):
        if not candidate:
            continue
        suffix = Path(candidate).suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            return True
    return False


def get_image_attachments(attachments: list[schemas.Attachment]) -> list[schemas.Attachment]:
    return [attachment for attachment in attachments if _is_image_attachment(attachment)]


def _attachment_to_path(attachment: schemas.Attachment) -> Path:
    # Try URL-based lookup first, then fall back to known upload subdirectories.
    if attachment.url and attachment.url.startswith("/uploads/"):
        relative = attachment.url.replace("/uploads/", "", 1)
        candidate = UPLOAD_ROOT / relative
        if candidate.exists():
            return candidate

    for base in ("attachments", "files"):
        for candidate_name in (attachment.id, attachment.name):
            if not candidate_name:
                continue
            candidate = UPLOAD_ROOT / base / Path(candidate_name).name
            if candidate.exists():
                return candidate

    raise FileNotFoundError(f"Attachment not found on disk: {attachment.id}")


def analyze_images(
    db: Session,
    prompt: str,
    attachments: list[schemas.Attachment],
) -> dict[str, Any]:
    image_attachments = get_image_attachments(attachments)
    if not image_attachments:
        raise ValueError("No image attachments provided")

    model_name = get_vision_model_name(db)
    images: list[str] = []
    for attachment in image_attachments:
        image_path = _attachment_to_path(attachment)
        images.append(base64.b64encode(image_path.read_bytes()).decode("ascii"))

    import ollama

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt, "images": images}],
        stream=False,
    )
    content = response.get("message", {}).get("content", "")
    return {
        "content": content,
        "model": model_name,
        "image_count": len(images),
    }
