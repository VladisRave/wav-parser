FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive


# Копируем только requirements (с сохранением структуры)
COPY orchestrator/Stage_3_6/requirements.txt ./orchestrator/Stage_3_6/
COPY external/whisper-diarization/requirements.txt ./external/whisper-diarization/


RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        git \
        cython3 \
        build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip uv --no-cache-dir \
    && grep -v -E '^git+|^torch|^torchaudio' /app/external/whisper-diarization/requirements.txt > /tmp/regular_req.txt \
    && grep -v -E '^torch|^torchaudio' /app/orchestrator/Stage_3_6/requirements.txt > /tmp/clean_req.txt \
    && uv pip install --system --no-cache -r /tmp/clean_req.txt \
    && uv pip install --system --no-cache -r /tmp/regular_req.txt

# Копируем только необходимые исходники (не весь проект!)
COPY services /app/services
COPY external /app/external
COPY orchestrator/Stage_3_6 /app/orchestrator/Stage_3_6

# Submodules
RUN git submodule update --init --recursive || true

# Права на исполнение скрипта
RUN chmod +x /app/orchestrator/Stage_3_6/run_stage.sh

ENTRYPOINT ["/app/orchestrator/Stage_3_6/run_stage.sh"]

# # Как запускать первый Docktrfile
# docker build --rm --force-rm --no-cache -t wav-stage2 -f orchestrator/Stage_3_6/Dockerfile .

# docker run --rm \
#   -v $(pwd)/orchestrator/state:/shared/state \
#   -v $(pwd)/audio:/data \
#   wav-stage2