from pathlib import Path


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
