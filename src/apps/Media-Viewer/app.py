################################################################################
# Media Viewer Backend for Sanctum Station
################################################################################

import mimetypes
import os
import base64
import re
import shutil
import subprocess
import wave

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


def _text_to_data_url(text_content, mime_type="text/plain"):
    encoded = base64.b64encode(str(text_content or "").encode("utf-8")).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _ensure_vtt_header(vtt_content):
    text = str(vtt_content or "").lstrip("\ufeff").strip()
    if text.startswith("WEBVTT"):
        return text
    return f"WEBVTT\n\n{text}" if text else "WEBVTT\n"


def _srt_to_vtt(srt_content):
    text = str(srt_content or "").lstrip("\ufeff")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"(?P<a>\d{2}:\d{2}:\d{2}),(?P<b>\d{3})", r"\g<a>.\g<b>", normalized)
    return _ensure_vtt_header(normalized)


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

    result = FILE_MANAGER.get_file_data_url(
        path,
        MAX_EMBEDDED_MEDIA_BYTES,
        _default_mime_for_type(media_type)
    )

    if not result.get("success"):
        return result

    result["media_type"] = media_type
    return result


def save_media_data_url(path, data_url):
    output_path = str(path or "").strip()
    if not output_path:
        return {
            "success": False,
            "error": "Output path is required."
        }

    extension = _extension_for_path(output_path)
    if extension not in SUPPORTED_IMAGE_EXTENSIONS:
        return {
            "success": False,
            "error": "Only image output is currently supported for save_media_data_url.",
            "path": output_path,
            "extension": extension
        }

    raw_data_url = str(data_url or "").strip()
    if not raw_data_url.startswith("data:") or "," not in raw_data_url:
        return {
            "success": False,
            "error": "Invalid data URL payload.",
            "path": output_path
        }

    header, encoded_payload = raw_data_url.split(",", 1)
    if ";base64" not in header:
        return {
            "success": False,
            "error": "Only base64 data URLs are supported.",
            "path": output_path
        }

    try:
        payload = base64.b64decode(encoded_payload.encode("utf-8"), validate=True)
    except Exception as decode_error:
        return {
            "success": False,
            "error": f"Could not decode data URL payload: {decode_error}",
            "path": output_path
        }

    try:
        resolved_path = FILE_MANAGER._resolve_path(output_path)
        output_dir = os.path.dirname(resolved_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(resolved_path, "wb") as output_file:
            output_file.write(payload)

        return {
            "success": True,
            "path": resolved_path,
            "byte_size": len(payload)
        }
    except Exception as write_error:
        return {
            "success": False,
            "error": str(write_error),
            "path": output_path
        }


def _run_ffmpeg_trim(input_path, output_path, start_seconds, end_seconds):
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return {
            "success": False,
            "error": "ffmpeg is not available on this system."
        }

    start_text = f"{float(start_seconds):.6f}"
    end_text = f"{float(end_seconds):.6f}"

    copy_command = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        start_text,
        "-to",
        end_text,
        "-i",
        input_path,
        "-c",
        "copy",
        output_path,
    ]

    copy_process = subprocess.run(copy_command, capture_output=True, text=True)
    if copy_process.returncode == 0 and os.path.isfile(output_path):
        return {
            "success": True,
            "mode": "ffmpeg-copy"
        }

    reencode_command = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        start_text,
        "-to",
        end_text,
        "-i",
        input_path,
        output_path,
    ]
    reencode_process = subprocess.run(reencode_command, capture_output=True, text=True)
    if reencode_process.returncode == 0 and os.path.isfile(output_path):
        return {
            "success": True,
            "mode": "ffmpeg-reencode"
        }

    stderr_text = (reencode_process.stderr or copy_process.stderr or "").strip()
    return {
        "success": False,
        "error": stderr_text or "ffmpeg trim command failed."
    }


def _trim_wav_pcm(input_path, output_path, start_seconds, end_seconds):
    with wave.open(input_path, "rb") as source:
        frame_rate = source.getframerate()
        total_frames = source.getnframes()
        start_frame = max(0, min(total_frames, int(float(start_seconds) * frame_rate)))
        end_frame = max(start_frame, min(total_frames, int(float(end_seconds) * frame_rate)))

        source.setpos(start_frame)
        frame_data = source.readframes(end_frame - start_frame)
        params = source.getparams()

    with wave.open(output_path, "wb") as target:
        target.setparams(params)
        target.writeframes(frame_data)


def save_trimmed_media(path, output_path, start_seconds, end_seconds):
    info = inspect_media_path(path)
    if not info.get("success"):
        return info

    media_type = info.get("media_type")
    if media_type not in {"audio", "video"}:
        return {
            "success": False,
            "error": "save_trimmed_media currently supports audio and video files only.",
            "path": path,
            "media_type": media_type
        }

    raw_output_path = str(output_path or "").strip()
    if not raw_output_path:
        return {
            "success": False,
            "error": "Output path is required.",
            "path": path
        }

    try:
        start_value = float(start_seconds)
        end_value = float(end_seconds)
    except Exception:
        return {
            "success": False,
            "error": "Invalid trim range values.",
            "path": path
        }

    if start_value < 0:
        start_value = 0.0

    if end_value <= start_value:
        return {
            "success": False,
            "error": "Trim end must be greater than trim start.",
            "path": path,
            "start_seconds": start_value,
            "end_seconds": end_value
        }

    resolved_input = FILE_MANAGER._resolve_path(path)
    resolved_output = FILE_MANAGER._resolve_path(raw_output_path)
    if os.path.exists(resolved_output):
        return {
            "success": False,
            "error": "Output file already exists.",
            "path": raw_output_path
        }

    output_dir = os.path.dirname(resolved_output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    ffmpeg_result = _run_ffmpeg_trim(resolved_input, resolved_output, start_value, end_value)
    if ffmpeg_result.get("success"):
        return {
            "success": True,
            "path": resolved_output,
            "mode": ffmpeg_result.get("mode"),
            "start_seconds": start_value,
            "end_seconds": end_value,
            "duration_seconds": end_value - start_value
        }

    input_extension = _extension_for_path(resolved_input)
    output_extension = _extension_for_path(resolved_output)
    if media_type == "audio" and input_extension == ".wav" and output_extension == ".wav":
        try:
            _trim_wav_pcm(resolved_input, resolved_output, start_value, end_value)
            return {
                "success": True,
                "path": resolved_output,
                "mode": "wave-fallback",
                "start_seconds": start_value,
                "end_seconds": end_value,
                "duration_seconds": end_value - start_value
            }
        except Exception as wav_error:
            return {
                "success": False,
                "error": str(wav_error),
                "path": raw_output_path
            }

    return {
        "success": False,
        "error": ffmpeg_result.get("error") or "Trim save failed.",
        "path": raw_output_path,
        "hint": "Install ffmpeg for trim export support on this format."
    }


def get_subtitle_track(path, preferred_lang="en", preferred_label="Default"):
    info = inspect_media_path(path)
    if not info.get("success"):
        return info

    if info.get("media_type") != "video":
        return {
            "success": False,
            "error": "Subtitle tracks are only available for video files.",
            "path": path,
            "media_type": info.get("media_type")
        }

    base_path = os.path.splitext(str(path))[0]
    candidate_paths = [f"{base_path}.vtt", f"{base_path}.srt"]

    for subtitle_path in candidate_paths:
        if not FILE_MANAGER.exists(subtitle_path):
            continue

        subtitle_text = FILE_MANAGER.read_file(subtitle_path)
        if not subtitle_text:
            continue

        extension = _extension_for_path(subtitle_path)
        if extension == ".srt":
            vtt_text = _srt_to_vtt(subtitle_text)
            source_format = "srt-converted"
        else:
            vtt_text = _ensure_vtt_header(subtitle_text)
            source_format = "vtt"

        return {
            "success": True,
            "path": subtitle_path,
            "source_format": source_format,
            "srclang": str(preferred_lang or "en"),
            "label": str(preferred_label or "Default"),
            "data_url": _text_to_data_url(vtt_text, "text/vtt")
        }

    return {
        "success": False,
        "error": "No sidecar subtitle file found.",
        "path": path,
        "checked": candidate_paths
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