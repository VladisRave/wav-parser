# Используем Python 3.9 slim
FROM python:3.9-slim

# Вставьте ниже свой токен
ENV HF_TOKEN="ENTER YOUR API KEY"

# Системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем код и requirements
COPY . /app
COPY requirements.txt /app/requirements.txt

# Установка зависимостей
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Скрипт для запуска пайплайна
RUN chmod +x /app/orchestrator/run_pipeline.sh

# Точка входа - наш скрипт
ENTRYPOINT ["/app/orchestrator/run_pipeline.sh"]

# Информация о том, как использовать
CMD ["--help"]

# # 1. Сборка образа
# cd /home/user/wav-parser
# docker build -t wav-parse -f orchestrator/Dockerfile . --no-cache

# # 2. Указание конкретных путей
# docker run --rm \
#   -v /home/user/papkamusik/archive:/input \
#   -v /home/user/papkamusik/results:/output \
#   wav-parse \
#   /input /app/clips /output

# или если жестко привязать пути то
# docker run --rm wav-parse