# ------------------------
# Базовый образ с PyTorch + CUDA
# ------------------------
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# ------------------------
# Окружение
# ------------------------
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

WORKDIR /app

# ------------------------
# 1. Системные зависимости + компилятор + Python пакеты
# ------------------------
COPY requirements.txt . 
COPY external/whisper-diarization/requirements.txt external/whisper-diarization/requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        git \
        cython3 \
        build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip uv --no-cache-dir \
    && grep -v -E '^git+|^torch|^torchaudio' external/whisper-diarization/requirements.txt > /tmp/regular_req.txt \
    && grep -v -E '^torch|^torchaudio' requirements.txt > /tmp/clean_req.txt \
    && uv pip install --system --no-cache -r /tmp/clean_req.txt \
    && uv pip install --system --no-cache -r /tmp/regular_req.txt \
    && grep '^git+' external/whisper-diarization/requirements.txt | xargs -n 1 uv pip install --system --no-cache \
    && uv pip install --system --force-reinstall --no-cache torchaudio \
    && rm -rf /tmp/*.txt

# ------------------------
# 2. Копируем весь проект
# ------------------------
COPY . /app

# ------------------------
# 3. Submodules
# ------------------------
RUN git submodule update --init --recursive || true

# ------------------------
# 4. Права
# ------------------------
RUN chmod +x /app/orchestrator/run_pipeline.sh

# ------------------------
# 5. Точка входа
# ------------------------
ENTRYPOINT ["/app/orchestrator/run_pipeline.sh"]

# # 1. Сборка образа
# cd /home/user/wav-parser
# docker build -t audio_parser -f orchestrator/Dockerfile . --no-cache

# # 2. Указание конкретных путей
# docker run --rm \
#   -v /home/user/papkamusik/gg:/input \
#   -v /home/user/wav-parser/audio/results:/output \
#   audio_parser \
#   /input /app/clips /output

# или если жестко привязать пути то
# docker run --rm wav-parse