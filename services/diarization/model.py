import os
import re
import gc
import sys
import torch
import logging
import numpy as np
import faster_whisper

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
WHISPER_DIARIZATION_DIR = BASE_DIR / "external" / "whisper-diarization"
sys.path.insert(0, str(WHISPER_DIARIZATION_DIR))


from ctc_forced_aligner import (
    generate_emissions,
    get_alignments,
    get_spans,
    load_alignment_model,
    postprocess_results,
    preprocess_text,
)
from helpers import (
    get_realigned_ws_mapping_with_punctuation,
    get_sentences_speaker_mapping,
    get_speaker_aware_transcript,
    get_words_speaker_mapping,
    langs_to_iso,
    write_srt,
)
from diarization import MSDDDiarizer

WHISPER_MODEL = os.getenv("WHISPER_MODEL_SIZE")
BATCH_SIZE = 16
LANGUAGE = "ru"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MTYPES = {"cpu": "int8", "cuda": "float16"}

class DiarizationEngine:
    def __init__(self):
        self.whisper_model = None
        self.whisper_pipeline = None
        self.alignment_model = None
        self.alignment_tokenizer = None
        self.diarizer = None
        self.suppress_tokens = None

    def load_models(self):
        """
        Загружает все модели пайплайна диаризации.

        Result:
            - модели загружены в GPU/CPU
            - установлены suppress_tokens
            - выведено использование VRAM (если CUDA)
        """
        print("Loading Whisper model...")

        self.whisper_model = faster_whisper.WhisperModel(
            WHISPER_MODEL,
            device=DEVICE,
            compute_type=MTYPES[DEVICE],
        )

        self.whisper_pipeline = faster_whisper.BatchedInferencePipeline(
            self.whisper_model
        )

        self.suppress_tokens = [-1]

        print("Loading alignment model...")

        self.alignment_model, self.alignment_tokenizer = load_alignment_model(
            DEVICE,
            dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        )

        print("Loading NeMo MSDD diarizer...")

        self.diarizer = MSDDDiarizer(device=DEVICE)

        allocated = (
            torch.cuda.memory_allocated() / 1024**3
            if DEVICE == "cuda"
            else 0
        )

        print(f"All models loaded. VRAM used: {allocated:.2f} GB")

    def process_file(self, audio_path: Path, output_dir: Path):
        """
        Полный пайплайн обработки одного аудиофайла:
        транскрипция > выравнивание > диаризация > сохранение.

        Args:
            audio_path: путь к аудиофайлу (.wav)
            output_dir: директория для сохранения результатов

        Input:
            - audio_path (Path): входной аудиофайл
            - output_dir (Path): папка для результатов

        Output:
            - .txt файл с расшифровкой
            - .srt файл с таймингами и спикерами

        """
        file_id = audio_path.stem
        result_dir = output_dir / file_id
        result_dir.mkdir(parents=True, exist_ok=True)

        audio_waveform = faster_whisper.decode_audio(str(audio_path))

        transcript_segments, info = self.whisper_pipeline.transcribe(
            audio_waveform,
            LANGUAGE,
            suppress_tokens=self.suppress_tokens,
            batch_size=BATCH_SIZE,
        )

        full_transcript = "".join(seg.text for seg in transcript_segments)

        if not full_transcript.strip():
            logging.warning(
                f"Empty transcript for {audio_path.name}, skipping"
            )
            return
        
        emissions, stride = generate_emissions(
            self.alignment_model,
            torch.from_numpy(audio_waveform)
            .to(self.alignment_model.dtype)
            .to(self.alignment_model.device),
            batch_size=BATCH_SIZE,
        )

        tokens_starred, text_starred = preprocess_text(
            full_transcript,
            romanize=True,
            language=langs_to_iso[info.language],
        )

        segments, scores, blank_token = get_alignments(
            emissions,
            tokens_starred,
            self.alignment_tokenizer,
        )

        spans = get_spans(tokens_starred, segments, blank_token)

        word_timestamps = postprocess_results(
            text_starred,
            spans,
            stride,
            scores,
        )

        speaker_ts = self.diarizer.diarize(
            torch.from_numpy(audio_waveform).unsqueeze(0)
        )


        wsm = get_words_speaker_mapping(
            word_timestamps,
            speaker_ts,
            "start",
        )

        wsm = get_realigned_ws_mapping_with_punctuation(wsm)

        ssm = get_sentences_speaker_mapping(wsm, speaker_ts)

        txt_path = result_dir / f"{file_id}.txt"
        srt_path = result_dir / f"{file_id}.srt"

        with open(txt_path, "w", encoding="utf-8-sig") as f:
            get_speaker_aware_transcript(ssm, f)

        with open(srt_path, "w", encoding="utf-8-sig") as f:
            write_srt(ssm, f)

        del audio_waveform
        del emissions
        del speaker_ts

        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def unload(self):
        """
        Освобождает все загруженные модели и очищает GPU память.
        """
        del self.whisper_model
        del self.whisper_pipeline
        del self.alignment_model
        del self.alignment_tokenizer
        del self.diarizer

        if torch.cuda.is_available():
            torch.cuda.empty_cache()