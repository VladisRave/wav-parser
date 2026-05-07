FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Python 3.10 и системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.10 \
        python3-pip \
        python3-dev \
        git \
        ffmpeg \
        sox \
        libsndfile1 \
        build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.10 /usr/local/bin/python \
    && ln -s /usr/bin/python3.10 /usr/local/bin/python3

RUN python -m pip install --upgrade pip setuptools wheel

WORKDIR /app

# Копируем requirements и удаляем оттуда упоминания torch
# (чтобы не ставилась случайная версия)
COPY external/whisper-diarization/requirements.txt /tmp/whisper-requirements.txt
RUN sed -i '/torch/d' /tmp/whisper-requirements.txt

COPY . /app

RUN if [ -d ".git" ]; then \
        git submodule update --init --recursive; \
    else \
        echo "No .git found, assuming submodule content is already present"; \
    fi

# 1. Зависимости whisper-diarization (без torch)
RUN pip install --no-cache-dir -r /tmp/whisper-requirements.txt

# 2. Дополнительные пакеты
RUN pip install --no-cache-dir praat-parselmouth==0.4.7 openai

# 3. Чистая установка нужного PyTorch (как у вас локально)
RUN pip install --no-cache-dir \
        torch==2.4.1+cu121 \
        torchaudio==2.4.1+cu121 \
        torchvision==0.19.1+cu121 \
        --index-url https://download.pytorch.org/whl/cu121

# 4. NeMo Toolkit (удаляем старый, если был, и ставим нужный)
RUN pip uninstall -y nemo-toolkit || true \
    && pip install --no-cache-dir nemo-toolkit==2.6.0

RUN chmod +x /app/orchestrator/Stage_3_6/run_stage.sh

ENTRYPOINT ["/app/orchestrator/Stage_3_6/run_stage.sh"]