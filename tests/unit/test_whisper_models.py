from domain.whisper_models import is_valid_model_name, SUPPORTED_MODELS, DEFAULT_MODEL


def test_default_model_is_base():
    assert DEFAULT_MODEL == "base"


def test_supported_models_match_original_menu_order():
    assert SUPPORTED_MODELS == ("tiny", "base", "small", "medium", "large")


def test_accepts_known_model_name():
    assert is_valid_model_name("small") is True


def test_rejects_unknown_model_name():
    assert is_valid_model_name("huge") is False
