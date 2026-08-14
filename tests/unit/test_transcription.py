from domain.transcription import output_path_for, segments_to_text


class FakeSegment:
    def __init__(self, text):
        self.text = text


def test_segments_to_text_joins_segments_with_newline():
    segments = [FakeSegment("Bonjour"), FakeSegment("le monde")]

    assert segments_to_text(segments) == "Bonjour\nle monde"


def test_segments_to_text_returns_empty_string_for_no_segments():
    assert segments_to_text([]) == ""


def test_output_path_for_appends_transcription_suffix_next_to_input():
    assert output_path_for("/audio/interview.mp3") == "/audio/interview_transcription.txt"


def test_output_path_for_strips_original_extension():
    assert output_path_for("recording.wav") == "recording_transcription.txt"
