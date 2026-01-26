# Используем Python 3.9 slim
FROM python:3.9-slim

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

# По умолчанию запускаем пайплайн
CMD ["/app/orchestrator/run_pipeline.sh"]
