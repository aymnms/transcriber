from domain.audio_files import FILE_DIALOG_PATTERN, is_supported_audio_extension


def test_accepts_known_audio_extension():
    assert is_supported_audio_extension("interview.mp3") is True


def test_accepts_known_extension_case_insensitively():
    assert is_supported_audio_extension("interview.MP3") is True


def test_rejects_unsupported_extension():
    assert is_supported_audio_extension("document.pdf") is False


def test_rejects_path_without_extension():
    assert is_supported_audio_extension("interview") is False


def test_file_dialog_pattern_lists_every_supported_extension():
    assert "*.mp3" in FILE_DIALOG_PATTERN
    assert "*.wav" in FILE_DIALOG_PATTERN
    assert "*.m4a" in FILE_DIALOG_PATTERN
