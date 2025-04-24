import io
import math
from pathlib import Path

from PIL import Image

from lightblue_ai.log import logger
from lightblue_ai.settings import Settings


class MediaMixin:
    binary_extensions = {  # noqa: RUF012
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".ico",
        ".webp",  # Images
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",  # Documents
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".7z",  # Archives
        ".exe",
        ".dll",
        ".so",
        ".dylib",  # Executables
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".flv",
        ".wav",  # Media
    }

    def _get_mime_type(self, path: Path) -> str:
        """Get the MIME type for a file based on its extension.

        Args:
            path: Path to the file

        Returns:
            MIME type string
        """
        extension_to_mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".ico": "image/x-icon",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".rar": "application/vnd.rar",
            ".7z": "application/x-7z-compressed",
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".flv": "video/x-flv",
            ".wav": "audio/wav",
        }

        suffix = path.suffix.lower()
        return extension_to_mime.get(suffix, "application/octet-stream")

    def _resized_image(
        self,
        file: Path | bytes,
        max_size: int = 1092 * 1092,
    ) -> bytes:
        """Resize an image while maintaining original proportions.

        If the image is already smaller than max_size (in total pixels),
        it will be returned unchanged. Otherwise, it will be resized
        proportionally so that width * height <= max_size.

        Args:
            file: Path to the image file or bytes
            max_size: Maximum number of pixels (width * height)

        Returns:
            The resized image as bytes
        """
        if not Settings().auto_resize_images:
            return file.read_bytes() if isinstance(file, Path) else file

        try:
            # Open the image
            img = Image.open(file) if isinstance(file, Path) else Image.open(io.BytesIO(file))

            # Get current dimensions
            width, height = img.size
            current_size = width * height

            # If image is already smaller than max_size, return it unchanged
            if current_size <= max_size:
                return file.read_bytes() if isinstance(file, Path) else file

            # Calculate the scaling factor to maintain proportions
            scale_factor = math.sqrt(max_size / current_size)

            # Calculate new dimensions
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            # Resize the image
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")

            # Convert the resized image back to bytes
            output_bytes = io.BytesIO()
            resized_img.save(output_bytes, format=img.format if img.format else "PNG")

            return output_bytes.getvalue()

        except Exception as e:
            logger.warning(f"Failed to resize image: {e}")
            # Return original content if resizing fails
            return file.read_bytes() if isinstance(file, Path) else file
