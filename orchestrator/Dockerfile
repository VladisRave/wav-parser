# Используем официальный Python 3.10 slim
FROM python:3.10-slim

# ------------------------
# 1. Системные зависимости
# ------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    git \
    cython3 \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ------------------------
# 2. Рабочая директория
# ------------------------
WORKDIR /app

# ------------------------
# 3. Копируем файлы с зависимостями
# ------------------------
COPY requirements.txt .
COPY external/whisper-diarization/requirements.txt external/whisper-diarization/requirements.txt

# ------------------------
# 4. Устанавливаем PyPI пакеты
# ------------------------
# Сначала обычные PyPI зависимости
RUN pip install --upgrade pip && \
    # Берем все пакеты кроме git+
    grep -v '^git+' external/whisper-diarization/requirements.txt > /tmp/regular_req.txt && \
    pip install --prefer-binary -r requirements.txt && \
    pip install --prefer-binary -r /tmp/regular_req.txt

# ------------------------
# 5. Устанавливаем Git-пакеты отдельно
# ------------------------
RUN grep '^git+' external/whisper-diarization/requirements.txt | xargs -n 1 pip install --no-cache-dir

# ------------------------
# 6. Копируем весь код проекта
# ------------------------
COPY . /app

# ------------------------
# 7. Инициализация submodules (если нужны)
# ------------------------
RUN git submodule update --init --recursive

# ------------------------
# 8. Разрешения на запуск пайплайна
# ------------------------
RUN chmod +x /app/orchestrator/run_pipeline.sh

# ------------------------
# 9. Entry point
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