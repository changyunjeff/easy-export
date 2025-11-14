"""
图片处理器模块
负责图片加载（Base64、URL、本地路径）、图片格式转换、图片缩放
"""

import base64
import binascii
import logging
from io import BytesIO
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

logger = logging.getLogger(__name__)

_SUPPORTED_FORMATS = {"PNG", "JPG", "JPEG"}
_DEFAULT_MAX_DOWNLOAD_SIZE = 5 * 1024 * 1024  # 5MB
try:  # Pillow>=9
    RESAMPLE = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
except AttributeError:  # Pillow<9 fallback
    RESAMPLE = Image.LANCZOS


class ImageProcessor:
    """
    图片处理器类
    负责图片加载、格式转换、缩放等
    """

    def __init__(
        self,
        max_download_size: int = _DEFAULT_MAX_DOWNLOAD_SIZE,
        placeholder_background: Tuple[int, int, int] = (240, 240, 240),
        placeholder_text_color: Tuple[int, int, int] = (120, 120, 120),
    ) -> None:
        self.max_download_size = max_download_size
        self.placeholder_background = placeholder_background
        self.placeholder_text_color = placeholder_text_color

    def load_from_base64(self, base64_str: str) -> bytes:
        """
        从Base64字符串加载图片

        Args:
            base64_str: Base64编码的图片字符串（支持data:image/xxx;base64,前缀）

        Returns:
            图片内容（字节）

        Raises:
            ValueError: Base64字符串格式错误
        """
        if not base64_str or not base64_str.strip():
            raise ValueError("Base64字符串不能为空")

        data = base64_str.strip()
        if data.startswith("data:"):
            try:
                data = data.split(",", 1)[1]
            except IndexError as exc:
                raise ValueError("Base64数据URI格式错误") from exc

        normalized = "".join(data.split())
        try:
            return base64.b64decode(normalized, validate=True)
        except binascii.Error as exc:
            logger.error("Base64解码失败: %s", exc)
            raise ValueError("Base64字符串格式错误") from exc

    def load_from_url(
        self,
        url: str,
        timeout: int = 3,
    ) -> bytes:
        """
        从HTTP/HTTPS URL加载图片

        Args:
            url: 图片URL
            timeout: 请求超时时间（秒），默认3秒

        Returns:
            图片内容（字节）

        Raises:
            ValueError: URL非法或图片超出限制
            requests.RequestException: 网络请求失败
        """
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("仅支持HTTP/HTTPS协议图片链接")

        response = requests.get(url, timeout=timeout, stream=True)
        try:
            response.raise_for_status()
            buffer = BytesIO()
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > self.max_download_size:
                    raise ValueError("图片大小超过限制")
                buffer.write(chunk)

            return buffer.getvalue()
        finally:
            response.close()

    def load_from_path(self, path: str) -> bytes:
        """
        从本地文件路径加载图片

        Args:
            path: 本地文件路径

        Returns:
            图片内容（字节）

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 路径非法或不是文件
        """
        if not path:
            raise ValueError("路径不能为空")

        file_path = Path(path).expanduser()
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")

        return file_path.read_bytes()

    def resize(
        self,
        image: bytes,
        max_width: int,
        max_height: int,
        keep_aspect_ratio: bool = True,
    ) -> bytes:
        """
        缩放图片（保持长宽比）

        Args:
            image: 图片内容（字节）
            max_width: 最大宽度
            max_height: 最大高度
            keep_aspect_ratio: 是否保持长宽比，默认True

        Returns:
            缩放后的图片内容（字节）

        Raises:
            ValueError: 输入参数非法或图片无法解析
        """
        if max_width <= 0 or max_height <= 0:
            raise ValueError("最大宽高必须为正数")

        try:
            with Image.open(BytesIO(image)) as img:
                img_format = img.format or "PNG"
                if keep_aspect_ratio:
                    img.thumbnail((max_width, max_height), resample=RESAMPLE)
                else:
                    img = img.resize(
                        (max_width, max_height),
                        RESAMPLE,
                    )
                return self._image_to_bytes(img, img_format)
        except UnidentifiedImageError as exc:
            logger.error("图片无法解析: %s", exc)
            raise ValueError("无法解析图片内容") from exc

    def convert_format(
        self,
        image: bytes,
        target_format: str,
    ) -> bytes:
        """
        转换图片格式

        Args:
            image: 图片内容（字节）
            target_format: 目标格式（PNG/JPG/JPEG）

        Returns:
            转换后的图片内容（字节）

        Raises:
            ValueError: 不支持的格式或图片无法解析
        """
        normalized_format = self._normalize_format(target_format)
        try:
            with Image.open(BytesIO(image)) as img:
                convert_target = normalized_format
                if convert_target == "JPEG" and img.mode in {"RGBA", "LA", "P"}:
                    img = img.convert("RGB")
                return self._image_to_bytes(img, convert_target)
        except UnidentifiedImageError as exc:
            logger.error("图片无法解析: %s", exc)
            raise ValueError("无法解析图片内容") from exc

    def identify_format(self, image: bytes) -> str:
        """
        识别图片格式

        Args:
            image: 图片内容（字节）

        Returns:
            图片格式（PNG/JPG/JPEG等）

        Raises:
            ValueError: 无法识别格式
        """
        try:
            with Image.open(BytesIO(image)) as img:
                img_format = img.format
        except UnidentifiedImageError as exc:
            raise ValueError("无法识别图片格式") from exc

        if not img_format:
            raise ValueError("无法识别图片格式")

        if img_format.upper() == "JPEG":
            return "JPG"

        return img_format.upper()

    def get_placeholder_image(
        self,
        width: int = 200,
        height: int = 200,
        text: str = "Image Not Found",
    ) -> bytes:
        """
        生成占位图（加载失败时使用）

        Args:
            width: 图片宽度
            height: 图片高度
            text: 占位文本

        Returns:
            占位图内容（字节，PNG格式）
        """
        if width <= 0 or height <= 0:
            raise ValueError("占位图宽高必须为正数")

        image = Image.new(
            mode="RGB",
            size=(width, height),
            color=self.placeholder_background,
        )

        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        wrapped_text = ImageProcessor._wrap_text(draw, text, font, width - 20)

        bbox = ImageProcessor._multiline_textbbox(draw, wrapped_text, font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (width - text_width) / 2
        text_y = (height - text_height) / 2

        draw.multiline_text(
            (text_x, text_y),
            wrapped_text,
            font=font,
            fill=self.placeholder_text_color,
            align="center",
        )

        return self._image_to_bytes(image, "PNG")

    def _normalize_format(self, target_format: str) -> str:
        if not target_format:
            raise ValueError("目标格式不能为空")

        fmt = target_format.strip().upper()
        if fmt == "JPG":
            fmt = "JPEG"

        if fmt not in _SUPPORTED_FORMATS | {"JPEG"}:
            raise ValueError(f"不支持的目标格式: {target_format}")

        return fmt

    @staticmethod
    def _image_to_bytes(image: Image.Image, fmt: str) -> bytes:
        buffer = BytesIO()
        image.save(buffer, format=fmt)
        return buffer.getvalue()

    @staticmethod
    def _wrap_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
    ) -> str:
        if not text:
            return ""

        max_width = max(max_width, 10)
        words = text.split()
        if not words:
            return text

        lines = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if ImageProcessor._text_length(draw, candidate, font) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return "\n".join(lines)

    @staticmethod
    def _multiline_textbbox(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
    ) -> Tuple[int, int, int, int]:
        if hasattr(draw, "multiline_textbbox"):
            return draw.multiline_textbbox((0, 0), text, font=font, align="center")

        width, height = draw.multiline_textsize(text, font=font)
        return (0, 0, width, height)

    @staticmethod
    def _text_length(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
    ) -> float:
        if hasattr(draw, "textlength"):
            return draw.textlength(text, font=font)
        width, _ = draw.textsize(text, font=font)
        return width


