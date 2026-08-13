import pytest

from platform_.transcriber import transcribe_to_file, TranscriptionError


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeModel:
    def __init__(self, segments):
        self._segments = segments

    def transcribe(self, audio_path):
        return self._segments, {"audio_path": audio_path}


def test_transcribe_to_file_writes_transcription_next_to_input(tmp_path):
    audio_path = tmp_path / "meeting.mp3"
    audio_path.write_bytes(b"fake audio bytes")
    model = FakeModel([FakeSegment("Bonjour"), FakeSegment("le monde")])

    output_path = transcribe_to_file(str(audio_path), model_factory=lambda: model)

    expected_output = tmp_path / "meeting_transcription.txt"
    assert output_path == str(expected_output)
    assert expected_output.read_text(encoding="utf-8") == "Bonjour\nle monde"


def test_transcribe_to_file_raises_transcription_error_on_failure(tmp_path):
    audio_path = tmp_path / "corrupt.mp3"
    audio_path.write_bytes(b"not really audio")

    def failing_model_factory():
        raise RuntimeError("model failed to load")

    with pytest.raises(TranscriptionError):
        transcribe_to_file(str(audio_path), model_factory=failing_model_factory)


def test_transcribe_to_file_does_not_leave_partial_output_on_failure(tmp_path):
    audio_path = tmp_path / "corrupt.mp3"
    audio_path.write_bytes(b"not really audio")

    class ExplodingModel:
        def transcribe(self, audio_path):
            raise RuntimeError("decoding error")

    with pytest.raises(TranscriptionError):
        transcribe_to_file(str(audio_path), model_factory=lambda: ExplodingModel())

    assert not (tmp_path / "corrupt_transcription.txt").exists()
