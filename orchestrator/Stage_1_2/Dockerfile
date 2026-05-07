FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Объединяем все системные команды в один слой + очистка
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Установка uv и Python-зависимостей (без кэша)
COPY orchestrator/Stage_1_2/requirements.txt .
RUN pip install --no-cache-dir -U uv \
    && uv pip install --system --no-cache -r requirements.txt \
    && rm -rf /root/.cache/pip /root/.cache/uv

# Копируем только необходимые исходники (НЕ весь проект)
COPY services /app/services
COPY orchestrator/Stage_1_2 /app/orchestrator/Stage_1_2
RUN git submodule update --init --recursive || true
RUN chmod +x /app/orchestrator/Stage_1_2/run_stage.sh
ENTRYPOINT ["/app/orchestrator/Stage_1_2/run_stage.sh"]


# # Как запускать первый Docktrfile
# docker build --rm --force-rm --no-cache -t wav-stage1 -f orchestrator/Stage_1_2/Dockerfile .

# docker run --rm \
#   -v $(pwd)/orchestrator/state:/shared/state \
#   -v $(pwd)/audio:/data \
#   wav-stage1