import importlib

from domain.whisper_models import DEFAULT_MODEL, SUPPORTED_MODELS


def test_app_whisper_imports_without_creating_a_display():
    # Importing must not instantiate tk.Tk() (guarded behind __main__), so this
    # is safe to run headlessly (no X server / no window session) on any OS.
    app_whisper = importlib.import_module("app_whisper")

    assert app_whisper.model_choice == DEFAULT_MODEL
    assert app_whisper.model_choice in SUPPORTED_MODELS
    assert callable(app_whisper.browse_file)
    assert callable(app_whisper.run_transcription)
    assert callable(app_whisper.setup_main_window)
