FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Окружение
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

WORKDIR /app

# 1. Копируем весь проект
COPY . /app

# 2. Устанавливаем git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 3. Инициализируем submodules
RUN git submodule update --init --recursive || true

# 4. Устанавливаем зависимости строго по вашему алгоритму
RUN pip install -r external/whisper-diarization/requirements.txt && \
    pip install praat-parselmouth==0.4.7 openai && \
    pip uninstall -y torch torchaudio torchvision && \
    pip uninstall -y nvidia-cublas nvidia-cudnn nvidia-cuda-runtime nvidia-cusolver nvidia-cusparse || true && \
    pip install torch==2.4.1+cu121 torchaudio==2.4.1+cu121 torchvision==0.19.1+cu121 \
        --index-url https://download.pytorch.org/whl/cu121 && \
    pip uninstall -y nemo-toolkit || true && \
    pip install nemo-toolkit==2.6.0

# 5. Права на исполнение скрипта
RUN chmod +x /app/orchestrator/run_pipeline.sh
ENTRYPOINT ["/app/orchestrator/run_pipeline.sh"]

# # Как запускать первый Docktrfile
# docker build --rm --force-rm --no-cache -t wav-stage2 -f orchestrator/Stage_3_6/Dockerfile .

# docker run --rm \
#   -v $(pwd)/orchestrator/state:/shared/state \
#   -v $(pwd)/audio:/data \
#   wav-stage2