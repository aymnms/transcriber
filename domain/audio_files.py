import os

SUPPORTED_EXTENSIONS = (
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".flac",
    ".mp4",
    ".mkv",
    ".amr",
    ".dss",
    ".dvf",
    ".bmf",
    ".tta",
    ".tak",
    ".ape",
    ".alac",
    ".ra",
    ".rm",
    ".wma",
    ".opus",
    ".aac",
    ".pcm",
    ".raw",
    ".au",
    ".aiff",
)

FILE_DIALOG_PATTERN = " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)


def is_supported_audio_extension(path):
    _base, ext = os.path.splitext(path)
    return ext.lower() in SUPPORTED_EXTENSIONS
