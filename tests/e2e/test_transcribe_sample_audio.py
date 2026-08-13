import shutil

import pytest
from faster_whisper import WhisperModel

from platform_.transcriber import transcribe_to_file

SAMPLE_AUDIO = "assets/audios/NewRecording.m4a"


@pytest.mark.e2e
def test_transcribe_sample_audio_end_to_end(tmp_path):
    audio_copy = tmp_path / "NewRecording.m4a"
    shutil.copy(SAMPLE_AUDIO, audio_copy)

    output_path = transcribe_to_file(str(audio_copy), model_factory=lambda: WhisperModel("tiny"))

    with open(output_path, encoding="utf-8") as f:
        text = f.read()

    assert text.strip() != ""
    assert "bonjour" in text.lower()
