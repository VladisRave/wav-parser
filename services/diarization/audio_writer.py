import numpy as np
import soundfile as sf


def write_speaker_audio(diarization, y, sr, speaker, role, out_path):
    """
    diarization: объект диаризации
    y, sr: аудиосигнал и частота дискретизации
    speaker: id спикера
    role: 'target' или 'operator'
    out_path: путь для сохранения
    """
    chunks = [
        y[int(seg.start*sr):int(seg.end*sr)]
        for seg, _, spk in diarization.itertracks(yield_label=True)
        if spk == speaker
    ]

    if not chunks:
        raise RuntimeError(f"No audio found for speaker {speaker}")

    audio = np.concatenate(chunks)

    sf.write(out_path, audio, sr)
    return out_path
