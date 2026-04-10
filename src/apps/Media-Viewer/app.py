################################################################################
# Media Viewer Backend for Sanctum Station
################################################################################

import mimetypes
import os
import base64

from backend import FileManagerAPI

FILE_MANAGER = FileManagerAPI()

SUPPORTED_IMAGE_EXTENSIONS = {
    ".avif", ".bmp", ".gif", ".ico", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp"
}
SUPPORTED_VIDEO_EXTENSIONS = {
    ".avi", ".mkv", ".mov", ".mp4", ".webm"
}
SUPPORTED_AUDIO_EXTENSIONS = {
    ".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"
}
SUPPORTED_SUBTITLE_EXTENSIONS = {
    ".srt", ".vtt"
}

MAX_EMBEDDED_MEDIA_BYTES = 100 * 1024 * 1024


def _extension_for_path(path):
    return os.path.splitext(str(path or ""))[1].strip().lower()


def get_media_contract():
    return {
        "success": True,
        "contract": {
            "name": "Media Viewer",
            "supports": {
                "image_extensions": sorted(SUPPORTED_IMAGE_EXTENSIONS),
                "video_extensions": sorted(SUPPORTED_VIDEO_EXTENSIONS),
                "audio_extensions": sorted(SUPPORTED_AUDIO_EXTENSIONS),
                "subtitle_extensions": sorted(SUPPORTED_SUBTITLE_EXTENSIONS),
            },
            "playback_model": "best_effort",
            "notes": [
                "Playback support depends on platform WebView/codec availability.",
                "No transcoding is performed by the Media Viewer.",
                "Unsupported files should return capability details for frontend fallback UX."
            ]
        }
    }


def inspect_media_path(path):
    raw_path = str(path or "").strip()
    if not raw_path:
        return {
            "success": False,
            "error": "Path is required."
        }

    if not FILE_MANAGER.exists(raw_path):
        return {
            "success": False,
            "error": "File not found.",
            "path": raw_path
        }

    extension = _extension_for_path(raw_path)
    mime_type, _ = mimetypes.guess_type(raw_path)
    metadata = FILE_MANAGER.get_metadata(raw_path) or {}

    media_type = "unsupported"
    if extension in SUPPORTED_IMAGE_EXTENSIONS:
        media_type = "image"
    elif extension in SUPPORTED_VIDEO_EXTENSIONS:
        media_type = "video"
    elif extension in SUPPORTED_AUDIO_EXTENSIONS:
        media_type = "audio"
    elif extension in SUPPORTED_SUBTITLE_EXTENSIONS:
        media_type = "subtitle"

    return {
        "success": True,
        "path": raw_path,
        "extension": extension,
        "mime_type": mime_type,
        "playback_model": "best_effort",
        "media_type": media_type,
        "is_supported": media_type != "unsupported",
        "fallback": None if media_type != "unsupported" else {
            "reason": "unsupported-file-type",
            "message": "This file type is not currently supported by Media Viewer.",
            "hint": "Use a file with an extension listed by get_media_contract()."
        },
        "metadata": {
            "size": metadata.get("size"),
            "modified": metadata.get("modified"),
            "created": metadata.get("created"),
            "is_directory": metadata.get("is_directory", False)
        }
    }


def _resolve_absolute_path(path):
    raw_path = str(path or "").strip()
    if not raw_path:
        return ""

    if os.path.isabs(raw_path):
        return raw_path

    return FILE_MANAGER.get_storage_path(raw_path, True)


def _default_mime_for_type(media_type):
    if media_type == "image":
        return "image/png"
    if media_type == "video":
        return "video/mp4"
    if media_type == "audio":
        return "audio/mpeg"
    if media_type == "subtitle":
        return "text/plain"
    return "application/octet-stream"


def get_media_data_url(path):
    info = inspect_media_path(path)
    if not info.get("success"):
        return info

    if not info.get("is_supported"):
        return {
            "success": False,
            "error": "Unsupported file type for Media Viewer.",
            "fallback": info.get("fallback"),
            "path": path
        }

    media_type = info.get("media_type")
    if media_type == "subtitle":
        return {
            "success": False,
            "error": "Subtitle files should be loaded as text, not media binary.",
            "path": path
        }

    absolute_path = _resolve_absolute_path(path)
    if not absolute_path or not os.path.isfile(absolute_path):
        return {
            "success": False,
            "error": "File not found for media loading.",
            "path": path
        }

    byte_size = os.path.getsize(absolute_path)
    if byte_size > MAX_EMBEDDED_MEDIA_BYTES:
        mb_size = round(byte_size / (1024 * 1024), 2)
        mb_limit = round(MAX_EMBEDDED_MEDIA_BYTES / (1024 * 1024), 2)
        return {
            "success": False,
            "error": f"Media file is too large to embed ({mb_size} MB > {mb_limit} MB).",
            "path": path,
            "limit_bytes": MAX_EMBEDDED_MEDIA_BYTES,
            "byte_size": byte_size
        }

    mime_type = info.get("mime_type") or _default_mime_for_type(media_type)

    with open(absolute_path, "rb") as source_file:
        media_bytes = source_file.read()

    encoded_data = base64.b64encode(media_bytes).decode("utf-8")
    return {
        "success": True,
        "path": path,
        "media_type": media_type,
        "mime_type": mime_type,
        "byte_size": byte_size,
        "data_url": f"data:{mime_type};base64,{encoded_data}"
    }


def open_file(path):
    info = inspect_media_path(path)
    if not info.get("success"):
        return info

    media_type = info.get("media_type")
    if media_type not in {"subtitle"}:
        return {
            "success": False,
            "error": "open_file currently supports subtitle text files only.",
            "media_type": media_type,
            "path": path
        }

    content = FILE_MANAGER.read_file(path)
    return {
        "success": True,
        "path": path,
        "content": content
    }


def save_file(path, content):
    extension = _extension_for_path(path)
    if extension not in SUPPORTED_SUBTITLE_EXTENSIONS:
        return {
            "success": False,
            "error": "save_file currently supports subtitle text files only.",
            "path": path
        }

    success = FILE_MANAGER.write_file(path, content)
    return {
        "success": bool(success),
        "path": path
    }