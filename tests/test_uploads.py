from pathlib import Path

from PIL import Image

from graphsight.security.uploads import validate_image_upload


def test_validate_image_upload(tmp_path: Path) -> None:
    path = tmp_path / "diagram.png"
    Image.new("RGB", (64, 64), "white").save(path)

    internal, mime = validate_image_upload(path, "diagram.png", max_mb=1, max_pixels=10000)

    assert internal.endswith(".png")
    assert mime == "image/png"

