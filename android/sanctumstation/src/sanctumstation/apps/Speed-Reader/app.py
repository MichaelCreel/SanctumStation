################################################################################
# Speed Reader Backend for Sanctum Station
################################################################################

from backend import FileManagerAPI
import yaml

FILE_MANAGER = FileManagerAPI()

MIN_WPM = 20
MAX_WPM = 3600
DEFAULT_SETTINGS = {
    "wpm": 350,
    "lengthen_long_words": True,
    "center_letter_color": "#7300FF"
}

SETTINGS_PATH = "speed_reader/settings.yaml"


def _normalize_wpm(value):
    try:
        parsed = int(value)
    except Exception:
        parsed = DEFAULT_SETTINGS["wpm"]
    return max(MIN_WPM, min(MAX_WPM, parsed))


def _normalize_bool(value, fallback=True):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return bool(fallback)


def _normalize_color(value):
    text = str(value or "").strip()
    if len(text) == 7 and text.startswith("#"):
        hex_part = text[1:]
        if all(ch in "0123456789abcdefABCDEF" for ch in hex_part):
            return f"#{hex_part.upper()}"
    return DEFAULT_SETTINGS["center_letter_color"]


def _settings_payload(settings):
    return {
        "wpm": _normalize_wpm(settings.get("wpm", DEFAULT_SETTINGS["wpm"])),
        "lengthen_long_words": _normalize_bool(
            settings.get("lengthen_long_words", DEFAULT_SETTINGS["lengthen_long_words"]),
            DEFAULT_SETTINGS["lengthen_long_words"]
        ),
        "center_letter_color": _normalize_color(
            settings.get("center_letter_color", DEFAULT_SETTINGS["center_letter_color"])
        )
    }


def _ensure_settings_dir():
    FILE_MANAGER.create_directory("speed_reader")


def _read_settings():
    if not FILE_MANAGER.exists(SETTINGS_PATH):
        return dict(DEFAULT_SETTINGS)

    try:
        raw_content = FILE_MANAGER.read_file(SETTINGS_PATH)
        parsed = yaml.safe_load(raw_content) or {}
        if not isinstance(parsed, dict):
            return dict(DEFAULT_SETTINGS)
        return _settings_payload(parsed)
    except Exception:
        return dict(DEFAULT_SETTINGS)


def _write_settings(settings):
    safe_settings = _settings_payload(settings)
    _ensure_settings_dir()
    FILE_MANAGER.write_file(SETTINGS_PATH, yaml.safe_dump(safe_settings, sort_keys=False))
    return safe_settings


def separate_text(text):
    raw_text = str(text or "")
    words = []
    current_word = []

    for char in raw_text:
        if char.isspace():
            if current_word:
                words.append("".join(current_word))
                current_word = []
        else:
            current_word.append(char)

    if current_word:
        words.append("".join(current_word))

    return words


def calculate_word_display_time(word, wpm, lengthen_long_words=True):
    safe_wpm = _normalize_wpm(wpm)
    base_ms = 60000.0 / float(safe_wpm)
    word_text = str(word or "")

    if not lengthen_long_words:
        return int(round(base_ms))

    length = len(word_text)
    multiplier = 1.0
    if length >= 10:
        multiplier += 0.70
    elif length >= 7:
        multiplier += 0.40
    elif length >= 5:
        multiplier += 0.20

    if word_text.endswith((".", "!", "?")):
        multiplier += 0.35
    elif word_text.endswith((",", ";", ":")):
        multiplier += 0.20

    ms = base_ms * multiplier
    return max(1, int(round(ms)))


def calculate_word_timings(words, wpm, lengthen_long_words=True):
    sequence = words if isinstance(words, list) else []
    return [
        calculate_word_display_time(word, wpm, lengthen_long_words)
        for word in sequence
    ]


def get_settings():
    settings = _read_settings()
    _write_settings(settings)
    return {
        "success": True,
        "settings": settings,
        "limits": {
            "min_wpm": MIN_WPM,
            "max_wpm": MAX_WPM,
            "wpm_step": 10
        }
    }


def update_settings(wpm=None, lengthen_long_words=None, center_letter_color=None):
    current = _read_settings()

    if wpm is not None:
        current["wpm"] = _normalize_wpm(wpm)
    if lengthen_long_words is not None:
        current["lengthen_long_words"] = _normalize_bool(lengthen_long_words, current["lengthen_long_words"])
    if center_letter_color is not None:
        current["center_letter_color"] = _normalize_color(center_letter_color)

    saved = _write_settings(current)
    return {
        "success": True,
        "settings": saved
    }


def prepare_session(text, wpm=None, lengthen_long_words=None):
    settings = _read_settings()
    effective_wpm = _normalize_wpm(settings["wpm"] if wpm is None else wpm)
    effective_lengthen = settings["lengthen_long_words"] if lengthen_long_words is None else _normalize_bool(lengthen_long_words, settings["lengthen_long_words"])

    words = separate_text(text)
    timings_ms = calculate_word_timings(words, effective_wpm, effective_lengthen)

    return {
        "success": True,
        "words": words,
        "timings_ms": timings_ms,
        "word_count": len(words),
        "wpm": effective_wpm,
        "lengthen_long_words": effective_lengthen
    }