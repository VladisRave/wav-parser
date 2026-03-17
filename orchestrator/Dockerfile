FROM python:3.10-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsndfile1 \
    git \
    cython3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ВАЖНО: копируем ВСЁ (включая .git если нужно)
COPY . /app

# Инициализация submodules
RUN git submodule update --init --recursive

# pip
RUN pip install --no-cache-dir --upgrade pip

# Основные зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Внешний репозиторий
RUN pip install --no-cache-dir -r external/whisper-diarization/requirements.txt

# Скрипт
RUN chmod +x /app/orchestrator/run_pipeline.sh

ENTRYPOINT ["/app/orchestrator/run_pipeline.sh"]


# # 1. Сборка образа
# cd /home/user/wav-parser
# docker build -t wav-parse -f orchestrator/Dockerfile . --no-cache

# # 2. Указание конкретных путей
# docker run --rm \
#   -v /home/user/papkamusik/start:/input \
#   -v /home/user/papkamusik/results:/output \
#   first-parse \
#   /input /app/clips /output

# или если жестко привязать пути то
# docker run --rm wav-parse