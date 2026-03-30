# WAV-Parser

**WAV-Parser** — парсер аудио для обработки телефонных записей:

* Удаление музыкальных фоновых паттернов
* Шумоподавление (денойзинг)
* Диаризация и транскрибация (Whisper + NeMo MSDD)
* Определение ролей спикеров через LLM (USER / ASSISTANT / ROBOT)
* Разделение аудио по ролям
* Извлечение голосовых признаков (features)

Сервисы можно запускать независимо или объединять в единый пайплайн через `orchestrator/run_pipeline.sh`.

---

## Структура проекта

```text
wav-parser/
│
├── audio/
│   └── clips/
│       └── cutoff_music.wav
│
├── services/
│   ├── music_removal/
│   │   ├── main.py            # Точка входа для удаления музыки
│   │   └── music_search.py    # Модуль детекции музыки
│   │
│   ├── denoise/
│   │   ├── main.py            # Точка входа для денойзинга
│   │   └── denoise.py         # Модуль денойзинга
│   │
│   ├── diarization/
│   │   ├── main.py            # Точка входа для диаризации
│   │   ├── model.py           # Whisper + NeMo MSDD модели
│   │   └── utils.py           # Поиск аудиофайлов, форматы и расширения
│   │
│   ├── role_parser/
│   │   ├── main.py            # Точка входа для определения роли спикера
│   │   ├── llm.py             # Загрузка LLM (Qwen2.5-7B-Instruct, 4-bit)
│   │   └── detect_roles.py    # Определение ролей спикеров через промты
│   │
│   ├── audio_separation/
│   │   ├── main.py            # Запуск сервиса разделения аудио
│   │   ├── audio_utils.py     # RMS нормализация, объединение сегментов
│   │   ├── models.py          # Таймкоды и блоки спикеров
│   │   ├── splitter.py        # Разделение аудио по ролям
│   │   └── srt_parser.py      # Парсинг SRT файлов и извлечение спикеров
│   │
│   ├── voice_params/
│   │   ├── main.py            # Точка входа для извлечения характеристик
│   │   ├── pipeline.py        # Пайплайн обработки аудио
│   │   ├── hash_generator.py  # Генерация hash-кодов для аудиофайлов
│   │   ├── file_utils.py      # Рекурсивный поиск файлов и директорий
│   │   └── feature_extractor.py # Извлечение признаков аудиосигнала
│   │
│   └── vizualization/
│       └── pca_builder.ipyb
│
├── external/
│   └── whisper-diarization/   # Субмодуль диаризации
│
├── orchestrator/
│   ├── Dockerfile
│   └── run_pipeline.sh
│
├── requirements.txt
└── docker-compose.yml
```

---

## Пайплайн: 6 шагов

```
Шаг 1: music_removal   →  Удаление музыки из аудио
Шаг 2: denoise          →  Шумоподавление
Шаг 3: diarization      →  Диаризация + транскрибация (SRT, TXT)
Шаг 4: role_parser      →  Определение ролей спикеров (JSON)
Шаг 5: audio_separation →  Разделение аудио по ролям (WAV на каждую роль)
Шаг 6: voice_params     →  Извлечение голосовых признаков (features.csv)
```

### Выходные данные

| Шаг | Результат |
| --- | --------- |
| 1. music_removal | Очищенный аудиофайл (без фоновой музыки) |
| 2. denoise | Аудио с подавленным шумом |
| 3. diarization | `.srt` (таймкоды + спикеры) и `.txt` (транскрипция) |
| 4. role_parser | `_roles.json` — маппинг спикеров на роли |
| 5. audio_separation | `_user.wav`, `_assistant.wav`, `_robot.wav` |
| 6. voice_params | `features.csv` — признаки голоса, `hash_mapping.json` |

### Модели

* **Whisper** (`services/diarization/model.py`) — по умолчанию `large-v3`
* **Qwen LLM** (`services/role_parser/llm.py`) — по умолчанию `Qwen2.5-7B-Instruct` с 4-bit квантизацией (BitsAndBytes)

| Модель Whisper | VRAM | Комментарий |
| -------------- | ---- | ----------- |
| tiny | ~0.5 GB | Минимальное качество, очень быстро |
| base | ~1.5 GB | Базовое качество |
| small | ~2 GB | Среднее качество |
| medium | ~5 GB | Хорошее качество, баланс VRAM/точность |
| large-v2 | ~10 GB | Высокое качество |
| large-v3 | 10–12 GB | Максимальная точность, рекомендуется для production |

---

## Запуск через Docker (рекомендуется)

### 1. Сборка образа

```bash
git clone --recurse-submodules https://github.com/VladisRave/wav-parser.git
cd wav-parser
docker build -t wav-parser -f orchestrator/Dockerfile . --no-cache
```

### 2. Запуск всего пайплайна

```bash
sudo docker run -d --rm --gpus all \
  -e PYTHONUNBUFFERED=1 \
  -v /path/to/input:/input \
  -v /path/to/output:/output \
  --name wav-parser-run \
  wav-parser
```

Без аргументов `--from` / `--to` выполняются все 6 шагов.

### 3. Запуск отдельных шагов

Флаги `--from N` и `--to M` позволяют выполнить только нужный диапазон шагов (1–6):

```bash
# Только диаризация (шаг 3)
sudo docker run -d --rm --gpus all \
  -v /path/to/input:/input \
  -v /path/to/output:/output \
  wav-parser --from 3 --to 3

# Шаги 4–6 (role_parser → audio_separation → voice_params)
sudo docker run -d --rm --gpus all \
  -v /path/to/input:/input \
  -v /path/to/output:/output \
  wav-parser --from 4 --to 6
```

### 4. Разработка: монтирование кода с хоста

Чтобы не пересобирать образ при изменении кода, можно подключить сервисы и оркестратор с хоста:

```bash
sudo docker run -d --rm --gpus all \
  -e PYTHONUNBUFFERED=1 \
  -v /path/to/input:/input \
  -v /path/to/output:/output \
  -v /path/to/wav-parser/orchestrator/run_pipeline.sh:/app/orchestrator/run_pipeline.sh \
  -v /path/to/wav-parser/services:/app/services \
  --name wav-parser-run \
  wav-parser
```

### 5. Мониторинг

```bash
# Статус контейнера
sudo docker ps | grep wav-parser-run

# Логи в реальном времени
sudo docker logs -f wav-parser-run

# Последние N строк
sudo docker logs --tail 50 wav-parser-run
```

> **Важно:** при использовании `-d --rm` контейнер удаляется после завершения (в том числе при ошибке), и логи теряются. Для отладки убирайте `--rm`, чтобы посмотреть логи после падения, а затем удаляйте контейнер вручную через `docker rm`.

### 6. Запуск отдельного сервиса напрямую

Можно обойти `run_pipeline.sh` и вызвать конкретный сервис:

```bash
sudo docker run --rm --gpus all \
  --entrypoint python3 \
  -v /path/to/output:/output \
  -v /path/to/wav-parser/services:/app/services \
  wav-parser \
  /app/services/voice_params/main.py --input /output --output /output
```

---

## Механизм работы пайплайна

### Рабочая директория

Пайплайн создаёт временную директорию `output/.work/`, в которой хранятся промежуточные результаты всех шагов. После успешного завершения всех 6 шагов результаты копируются в `output/`, а `.work/` удаляется.

### Отслеживание прогресса

* **`.work/.completed_steps`** — отслеживает завершённые шаги текущего батча. Если контейнер упал, при перезапуске уже завершённые шаги пропускаются.
* **`output/processed.log`** — список уже обработанных файлов (по имени MP3). При следующем запуске эти файлы автоматически пропускаются.

### Кэширование моделей HuggingFace

Модели (Whisper, Qwen) скачиваются внутрь контейнера при первом запуске. Чтобы не скачивать их каждый раз и не занимать место в overlay-FS контейнера, подключите кэш с хоста:

```bash
-v ~/.cache/huggingface:/root/.cache/huggingface
```

---

## Локальный запуск

### 1. Установка окружения

```bash
git clone --recurse-submodules https://github.com/VladisRave/wav-parser.git
cd wav-parser

conda create -n wav_parser python=3.10
conda activate wav_parser

pip install cython
sudo apt update && sudo apt install ffmpeg
pip install -c constraints.txt -r requirements.txt
```

### 2. Запуск сервисов по отдельности

```bash
python services/music_removal/main.py --input audio/tracks --music_dir audio/clips --output audio/clean_audio
python services/denoise/main.py --input audio/clean_audio --output audio/denoised
python services/diarization/main.py --input audio/denoised --output audio/diarized
python services/role_parser/main.py --input audio/diarized --output audio/roles
python services/audio_separation/main.py --input_dir audio/roles --output_dir audio/splitted
python services/voice_params/main.py --input audio/splitted --output audio/features
```

> Каждый `main.py` можно запускать независимо.

---

## Известные ограничения

* **GPU обязателен** для шагов 3 (diarization) и 4 (role_parser). Работа на CPU может привести к зависаниям или крайне медленной обработке.
* **Длинные транскрипции** (>6000 символов) автоматически обрезаются перед отправкой в LLM на шаге 4. Для определения ролей достаточно начала разговора.
* **Шаг 4 (role_parser)** ловит OOM-ошибки и пропускает файлы, на которых не хватает VRAM, вместо остановки всего батча.
* **Дисковое пространство:** шаги 1–3 генерируют промежуточные WAV-файлы. Убедитесь, что на диске достаточно места (в том числе для скачивания моделей HuggingFace).

---

## Attribution

Проект использует внешнюю реализацию диаризации:

[https://github.com/MahmoudAshraf97/whisper-diarization](https://github.com/MahmoudAshraf97/whisper-diarization)

Все права на оригинальную реализацию принадлежат авторам. В проекте используется интеграция и модификации для пайплайна.