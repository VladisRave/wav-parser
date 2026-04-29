FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

WORKDIR /app

# 1. System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-dev \
        ffmpeg \
        libsndfile1 \
        git \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip uv

# 2. Copy requirements
COPY external/whisper-diarization/requirements.txt /tmp/whisper.txt
COPY orchestrator/Stage_3_6/requirements.txt /tmp/main.txt

# 3. Whisper installation
RUN uv pip install --system --no-cache -r /tmp/whisper.txt

# 4. Install other requirements (without Torch)
RUN grep -v -E '^torch|^torchaudio|^transformers' /tmp/main.txt > /tmp/main_clean.txt \
    && uv pip install --system --no-cache -r /tmp/main_clean.txt \
    && rm /tmp/main_clean.txt

# 5. Copy project
COPY . /app

RUN chmod +x /app/orchestrator/Stage_3_6/run_stage.sh
ENTRYPOINT ["/app/orchestrator/Stage_3_6/run_stage.sh"]

# # Как запускать первый Docktrfile
# docker build --rm --force-rm --no-cache -t wav-stage2 -f orchestrator/Stage_3_6/Dockerfile .

# docker run --rm \
#   -v $(pwd)/orchestrator/state:/shared/state \
#   -v $(pwd)/audio:/data \
#   wav-stage2