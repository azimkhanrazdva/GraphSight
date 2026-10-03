from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from uuid import uuid4

from PIL import Image

ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp"}
ALLOWED_SUFFIX = {".png", ".jpg", ".jpeg", ".webp"}


class UploadRejected(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_image_upload(path: Path, original_name: str, max_mb: int, max_pixels: int) -> tuple[str, str]:
    suffix = Path(original_name).suffix.lower()
    guessed_mime = mimetypes.guess_type(original_name)[0] or ""
    if suffix not in ALLOWED_SUFFIX or guessed_mime not in ALLOWED_MIME:
        raise UploadRejected("Unsupported file type.")
    if path.stat().st_size > max_mb * 1024 * 1024:
        raise UploadRejected("File exceeds upload limit.")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width * image.height > max_pixels:
                raise UploadRejected("Image dimensions exceed configured limit.")
    except UploadRejected:
        raise
    except Exception as exc:
        raise UploadRejected("Uploaded file is not a valid image.") from exc
    internal_name = f"{uuid4().hex}{suffix}"
    return internal_name, guessed_mime

