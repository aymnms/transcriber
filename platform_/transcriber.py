from domain.transcription import output_path_for, segments_to_text


class TranscriptionError(Exception):
    pass


def transcribe_to_file(audio_path, model_factory):
    try:
        model = model_factory()
        segments, _info = model.transcribe(audio_path)
        text = segments_to_text(segments)
        output_path = output_path_for(audio_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return output_path
    except Exception as exc:
        raise TranscriptionError(str(exc)) from exc
