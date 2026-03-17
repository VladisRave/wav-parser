# WAV-Parser

**WAV-Parser** — это парсер аудио, предназначенный для:

* Удаления музыкальных фоновых паттернов
* Повышения качества аудиозаписей
* Выделения голоса целевого пользователя из телефонной речи
* Определения пользователя, оператора (опционально) и роботов-голосовых помощников

Проект организован как набор сервисов, которые можно запускать независимо или объединять в единый пайплайн, что и представлено в папке `orchestrator`.

---

## Структура проекта

```text
wav-parser/
│
├── audio/
│   ├── clips/
│   │   └── cutoff_music.wav
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
│   │   ├── model.py           # Инициация модели из внешнего репозитория
│   │   └── utils.py           # Поддержка для main файла, форматы аудио и расширения
│   │
│   ├── role_parser/
│   │   ├── main.py            # Точка входа для определения роли спикера
│   │   ├── llm.py             # Инициация LLM модели
│   │   └── detect_roles.py    # Определение ролей спикеров через промты
│   │
│   ├── audio_separation/
│   │   ├── main.py            # Запуск сервиса разделения аудио
│   │   ├── audio_utils.py     # RMS нормализация, объединение сегментов
│   │   ├── models.py          # Таймкоды и блоки спикеров
│   │   ├── splitter.py        # Разделение строки на составляющие
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
│   └── whisper-diarization/   # Вспомогательные функции
│
├── orchestrator/
│   ├── Dockerfile
│   └── run_pipeline.sh
│
├── requirements.txt
└── docker-compose.yml
```

---

## Алгоритм работы

Последовательность обработки аудио:

```
music_removal -> denoise -> diarization -> role_parser -> audio_separation -> voice_params
```

* Для диаризации используется модель Whisper, рассчитанная на разные размеры и VRAM.
* LLM модель по умолчанию — `Qwen2.5-7B-Instruct`. Ее можно поменять в `llm.py`.

Возможные модели Whisper:

| Модель   | VRAM     | Комментарий                                         |
| -------- | -------- | --------------------------------------------------- |
| tiny     | ~0.5 GB  | Минимальное качество, очень быстро                  |
| base     | ~1.5 GB  | Базовое качество                                    |
| small    | ~2 GB    | Среднее качество                                    |
| medium   | ~5 GB    | Хорошее качество, баланс VRAM/точность              |
| large-v2 | ~10 GB   | Высокое качество                                    |
| large-v3 | 10–12 GB | Максимальная точность, рекомендуется для production |

---

## Требования к системе на которой запускался пайпалайн

* GPU: GeForce 4060 GTX, VRAM 8GB
* CPU: Intel Core i7, 2.4 GHz
* RAM: 16 GB

> Использование только CPU может привести к зависаниям на этапе диаризации.

---

## Запуск проекта

### Через Docker (рекомендуется для сервера)

1. Клонируем репозиторий:

```bash
git clone https://github.com/VladisRave/wav-parser.git
cd wav-parser
```

2. Собираем образ:

```bash
docker build -t wav-parser -f orchestrator/Dockerfile . --no-cache
```

3. Запускаем пайплайн:

```bash
docker run --rm \
  -v /home/user/input:/input \
  -v /home/user/output:/output \
  wav-parser \
  /input /app/audio/clips /output
```

4. Или через скрипт orchestrator:

```bash
chmod +x orchestrator/run_pipeline.sh
./orchestrator/run_pipeline.sh
```

Все сервисы будут запускаться автоматически в пайплайне.

---

### Локальный запуск через терминал

1. Создаем и активируем окружение:

```bash
git clone --recurse-submodules https://github.com/VladisRave/wav-parser.git
cd wav-parser

conda create -n wav_parser python=3.10
conda activate wav_parser

pip install cython
sudo apt update && sudo apt install ffmpeg
pip install -c constraints.txt -r requirements.txt
```

2. Подготовка данных:

```text
audio/
└── tracks/
    ├── file1.mp3
    ├── file2.mp3
```

3. Запуск сервисов по отдельности:

```bash
python services/music_removal/main.py --input audio/tracks --music_dir audio/clips --output audio/clean_audio
python services/denoise/main.py --input audio/clean_audio --output audio/denoised
python services/diarization/main.py --input audio/denoised --output audio/diarized
python services/role_parser/main.py --input audio/diarized --output audio/roles
python services/audio_separation/main.py --input audio/roles --output audio/splitted
python services/voice_params/main.py --input audio/splitted --output audio/features
```

> Каждый `main.py` можно запускать независимо.

---

## Конфигурация моделей

* Whisper (`services/diarization/model.py`)
* Qwen LLM (`services/role_parser/llm.py`)

Можно заменить на любую HuggingFace модель с учетом доступной VRAM.

---

## Выходные данные пайплайна

| Этап             | Результат                          |
| ---------------- | ---------------------------------- |
| music_removal    | Очищенный аудиофайл                |
| denoise          | Улучшенное аудио                   |
| diarization      | SRT файл с таймкодами и сегментами и TXT файл |
| role_parser      | JSON с ролями спикеров             |
| audio_separation | Аудио по спикерам                  |
| voice_params     | Признаки (features)                |

---

## Attribution

Проект использует внешнюю реализацию диаризации:

[https://github.com/MahmoudAshraf97/whisper-diarization](https://github.com/MahmoudAshraf97/whisper-diarization)

Все права на оригинальную реализацию принадлежат авторам. В проекте используется интеграция и модификации для пайплайна.


![alt text](working.gif)