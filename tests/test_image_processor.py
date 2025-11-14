import base64
from io import BytesIO

import pytest
from PIL import Image

from core.engine.image import ImageProcessor


def _create_sample_image(
    size=(120, 60),
    color=(200, 100, 50),
    fmt="PNG",
) -> bytes:
    image = Image.new("RGB", size=size, color=color)
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


class _DummyResponse:
    def __init__(self, chunks, status_code=200):
        self._chunks = list(chunks)
        self.status_code = status_code
        self.closed = False

    def iter_content(self, chunk_size=1024):
        yield from self._chunks

    def raise_for_status(self):
        if self.status_code >= 400:
            pytest.fail("HTTP error in dummy response")

    def close(self):
        self.closed = True


def test_load_from_base64_supports_data_uri():
    processor = ImageProcessor()
    image_bytes = _create_sample_image()
    data_uri = "data:image/png;base64," + base64.b64encode(image_bytes).decode()

    decoded = processor.load_from_base64(data_uri)

    assert decoded == image_bytes


def test_load_from_base64_invalid_input():
    processor = ImageProcessor()

    with pytest.raises(ValueError):
        processor.load_from_base64("not-valid-base64")


def test_load_from_path(tmp_path):
    processor = ImageProcessor()
    image_bytes = _create_sample_image()
    path = tmp_path / "image.png"
    path.write_bytes(image_bytes)

    loaded = processor.load_from_path(str(path))

    assert loaded == image_bytes


def test_resize_preserves_aspect_ratio():
    processor = ImageProcessor()
    image_bytes = _create_sample_image(size=(400, 200))

    resized = processor.resize(image_bytes, max_width=100, max_height=80)
    with Image.open(BytesIO(resized)) as img:
        assert img.width <= 100
        assert img.height <= 80
        assert img.width / img.height == pytest.approx(2, rel=0.1)


def test_convert_format_and_identify():
    processor = ImageProcessor()
    image_bytes = _create_sample_image(fmt="PNG")

    jpeg_bytes = processor.convert_format(image_bytes, "jpg")
    fmt = processor.identify_format(jpeg_bytes)

    assert fmt == "JPG"


def test_placeholder_image_is_png():
    processor = ImageProcessor()

    placeholder = processor.get_placeholder_image(width=120, height=60, text="Missing")
    fmt = processor.identify_format(placeholder)

    assert fmt == "PNG"


def test_load_from_url(monkeypatch):
    processor = ImageProcessor()
    image_bytes = _create_sample_image()
    response = _DummyResponse([image_bytes])

    monkeypatch.setattr(
        "core.engine.image.requests.get",
        lambda url, timeout, stream: response,
    )

    loaded = processor.load_from_url("https://example.com/image.png")

    assert loaded == image_bytes
    assert response.closed


def test_load_from_url_respects_size_limit(monkeypatch):
    processor = ImageProcessor(max_download_size=10)
    chunk = b"x" * 8
    response = _DummyResponse([chunk, chunk])

    monkeypatch.setattr(
        "core.engine.image.requests.get",
        lambda url, timeout, stream: response,
    )

    with pytest.raises(ValueError):
        processor.load_from_url("https://example.com/image.png")

