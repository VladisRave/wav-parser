from pathlib import Path

AUDIO_EXTENSIONS = [".wav"]


def find_audio_files(input_path: Path):
    """
    Find wav files in hash subdirectories, skipping the input/ dir
    and files that already have .srt output (already diarized).
    """
    audio_files = []
    if not input_path.is_dir():
        return audio_files

    for subdir in sorted(input_path.iterdir()):
        if not subdir.is_dir():
            continue
        if subdir.name == "input":
            continue

        for wav in subdir.glob("*.wav"):
            srt = wav.with_suffix(".srt")
            if srt.exists():
                continue
            audio_files.append(wav)

    return audio_files
