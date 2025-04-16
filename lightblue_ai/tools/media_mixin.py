import io
import math
from pathlib import Path

import imageio.v3 as iio
import numpy as np

from lightblue_ai.log import logger


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

    def _resized_image(  # noqa: C901
        self,
        file: Path | bytes,
        max_size: int = 1092 * 1092,
    ) -> bytes:
        """Resize an image while maintaining original proportions.

        If the image is already smaller than max_size (in total pixels),
        it will be returned unchanged. Otherwise, it will be resized
        proportionally so that width * height <= max_size.

        Args:
            file: Path to the image file
            max_size: Maximum number of pixels (width * height)

        Returns:
            The resized image as bytes

        TODO: Not tested with gif and webp
        """
        try:
            # Read the image using imageio
            img = iio.imread(file)

            # Get current dimensions
            height, width = img.shape[:2]
            current_size = width * height

            # If image is already smaller than max_size, return it unchanged
            if current_size <= max_size:
                return file.read_bytes() if isinstance(file, Path) else file

            # Calculate the scaling factor to maintain proportions
            scale_factor = math.sqrt(max_size / current_size)

            # Calculate new dimensions
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            # Create output array with new dimensions
            if len(img.shape) == 3 and img.shape[2] == 4:  # RGBA image
                resized_img = np.zeros((new_height, new_width, 4), dtype=img.dtype)
            elif len(img.shape) == 3:  # RGB image
                resized_img = np.zeros((new_height, new_width, 3), dtype=img.dtype)
            else:  # Grayscale image
                resized_img = np.zeros((new_height, new_width), dtype=img.dtype)

            # Calculate scaling ratios
            x_ratio = width / new_width
            y_ratio = height / new_height

            # Perform resizing using numpy (nearest neighbor approach)
            for y in range(new_height):
                for x in range(new_width):
                    src_x = min(width - 1, int(x * x_ratio))
                    src_y = min(height - 1, int(y * y_ratio))
                    resized_img[y, x] = img[src_y, src_x]
            logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            # Convert the resized image back to bytes
            output_bytes = io.BytesIO()

            # Get the file extension and use it to determine the format
            if isinstance(file, Path):
                file_ext = file.suffix.lower()
                if file_ext in (".jpg", ".jpeg"):
                    ext = "JPEG"
                elif file_ext == ".png":
                    ext = "PNG"
                elif file_ext == ".gif":
                    ext = "GIF"
                elif file_ext == ".bmp":
                    ext = "BMP"
                elif file_ext == ".webp":
                    ext = "WEBP"
                else:
                    # Default to PNG if format can't be determined
                    ext = "PNG"
            else:
                ext = "PNG"

            # Write the image to the BytesIO object with explicit format
            iio.imwrite(output_bytes, resized_img, extension=f".{ext.lower()}")

            # Get the bytes from the BytesIO object
            return output_bytes.getvalue()

        except Exception as e:
            logger.warning(f"Failed to resize image: {e}")
            # Return original content if resizing fails
            return file.read_bytes() if isinstance(file, Path) else file
