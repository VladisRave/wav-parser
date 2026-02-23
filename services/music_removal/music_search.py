# music_search.py
import os
import librosa
import numpy as np
import soundfile as sf



def compute_dtw_similarity_score(cost, chroma_frames):
    d_max = 2.0
    return 1.0 - cost / (chroma_frames * d_max)


def extract_chroma_features(y, sr, n_fft=2048, hop_length=256):
    return librosa.feature.chroma_stft(
        y=y,
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=n_fft,
        window="hann",
        n_chroma=12
    )


def merge_time_intervals(intervals, max_gap=3.0):
    if not intervals:
        return []

    intervals = sorted(intervals, key=lambda x: x[0])
    merged = []
    cur_start, cur_end = intervals[0]

    for s, e in intervals[1:]:
        if s <= cur_end + max_gap:
            cur_end = max(cur_end, e)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = s, e

    merged.append((cur_start, cur_end))
    return merged


def coarse_music_search(y_full, win_len, chroma_reference, step_len, sr, sim_thresh=0.75):
    candidates = []

    for start in range(0, len(y_full) - win_len, step_len):
        y_chunk = y_full[start:start + win_len]
        chroma_chunk = extract_chroma_features(y_chunk, sr)

        D, _ = librosa.sequence.dtw(
            X=chroma_reference,
            Y=chroma_chunk,
            subseq=True
        )

        sim = compute_dtw_similarity_score(D[-1, -1], chroma_reference.shape[1])
        if sim >= sim_thresh:
            candidates.append(start)

    return candidates


def refine_music_search(
    y_full,
    y_reference,
    candidates,
    win_len,
    sr,
    expand_step_sec=0.2,
    sim_thresh=0.7
):
    refined = []
    expand_step = int(sr * expand_step_sec)

    for start in candidates:
        cur_len = win_len
        last_good_end = start + cur_len

        while True:
            end = start + cur_len
            if end > len(y_full):
                break

            y_block = y_full[start:end]
            y_ref = y_reference[:cur_len]
            if len(y_ref) < cur_len:
                break

            chroma_ref = extract_chroma_features(y_ref, sr)
            chroma_block = extract_chroma_features(y_block, sr)

            D, _ = librosa.sequence.dtw(
                X=chroma_ref,
                Y=chroma_block,
                subseq=True
            )

            sim = compute_dtw_similarity_score(D[-1, -1], chroma_ref.shape[1])

            if sim >= sim_thresh:
                last_good_end = end
                cur_len += expand_step
            else:
                break

        refined.append((start, last_good_end))

    return refined


def replace_music_with_silence(
    y_full,
    sr,
    intervals_sec,
    output_path,
    pre_music_sec=4.0,
    silence_duration=3.0
    ):

    silence = np.zeros(int(sr * silence_duration), dtype=y_full.dtype)
    result = []
    cursor = 0
    pre_samples = int(pre_music_sec * sr)

    for start_sec, end_sec in intervals_sec:
        start = max(0, int(start_sec * sr) - pre_samples)
        end = min(len(y_full), int(end_sec * sr))

        if cursor < start:
            result.append(y_full[cursor:start])

        result.append(silence)
        cursor = end

    if cursor < len(y_full):
        result.append(y_full[cursor:])

    y_out = np.concatenate(result)
    sf.write(output_path, y_out, sr)
    return y_out
