SUPPORTED_MODELS = ("tiny", "base", "small", "medium", "large")

DEFAULT_MODEL = "base"


def is_valid_model_name(name):
    return name in SUPPORTED_MODELS
