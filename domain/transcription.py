import os


def segments_to_text(segments):
    return "\n".join(segment.text for segment in segments)


def output_path_for(input_path):
    base, _ext = os.path.splitext(input_path)
    return f"{base}_transcription.txt"
