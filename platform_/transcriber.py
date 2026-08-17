from domain.transcription import output_path_for, segments_to_text


class TranscriptionError(Exception):
    pass


def transcribe_to_file(audio_path, model_factory):
    try:
        print("[DEBUG] loading model...", flush=True)
        model = model_factory()
        print("[DEBUG] model loaded, transcribing...", flush=True)
        segments, _info = model.transcribe(audio_path)
        text = segments_to_text(segments)
        print(f"[DEBUG] transcription done, {len(text)} chars, writing file...", flush=True)
        output_path = output_path_for(audio_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print("[DEBUG] file written:", output_path, flush=True)
        return output_path
    except Exception as exc:
        print("[DEBUG] EXCEPTION:", repr(exc), flush=True)
        raise TranscriptionError(str(exc)) from exc
