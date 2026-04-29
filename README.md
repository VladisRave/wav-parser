# wav-parser

Данный репозиторий содержит парсер аудио для автоматического разделения телефонных разговоров колл-центра по ролям (звонящий, робот, ассистент). Пайплайн последовательно выполняет удаление музыки, шумоподавление, диаризацию, транскрибацию, определение ролей с помощью LLM, разделение аудио по ролям и извлечение голосовых признаков.

## Возможности

- Удаление музыкальных фрагментов с помощью YAMNet
- Шумоподавление: фильтр высоких частот, динамическое усиление тихих участков, снижение пиков, ресемплинг до 16 кГц
- Диаризация и транскрибация: Whisper + NeMo MSDD
- Определение ролей спикеров (USER / ASSISTANT / ROBOT) через LLM
- Разделение аудио по ролям (отдельные WAV-файлы)
- Извлечение голосовых признаков (feature vector)
- Модульность: каждый сервис может запускаться независимо
- Два изолированных Docker-контейнера для обработки множества файлов (разделение конфликтующих зависимостей)
- Воспроизводимость и удобство отладки

## Структура проекта

```text
wav-parser/
├── services/
│   ├── music_removal/          # удаление музыки (YAMNet)
│   │   ├── model_loader.py
│   │   ├── music_detector.py
│   │   └── main.py
│   │ 
│   ├── denoise/                # шумоподавление
│   │   ├── denoise.py
│   │   └── main.py
│   │ 
│   ├── diarization/            # диаризация + транскрибация
│   │   ├── model.py            # Whisper + NeMo MSDD
│   │   ├── utils.py
│   │   └── main.py
│   │ 
│   ├── role_parser/            # определение ролей через LLM
│   │   ├── detect_roles.py
│   │   ├── llm.py              # загрузка Qwen или ChatGPT
│   │   └── main.py
│   │ 
│   ├── audio_separation/       # разделение аудио по ролям
│   │   ├── audio_utils.py
│   │   ├── splitter.py
│   │   ├── srt_parser.py
│   │   └── main.py
│   │ 
│   ├── voice_params/           # извлечение голосовых признаков
│   │   ├── feature_extractor.py
│   │   ├── file_utils.py
│   │   ├── gender_control.py   # загрузка модели ECAPA_gender
│   │   └── main.py
│   └── vizualization/          # в процессе разработки
│ 
├── external/
│   ├── voice-gender-classifier
│   └── whisper-diarization/    # субмодуль форка whisper-diarization
│ 
├── orchestrator/               # Docker-сборка и оркестрация
│   ├── Stage_1_2/ 
│   │   ├── Docker
│   │   ├── requirements.txt
│   │   └── run_stage.sh
│   │
│   └── Stage_3_6/ 
│       ├── Docker
│       ├── requirements.txt
│       └── run_stage.sh
│  
├── .env                        # переменные среды
└── docker-compose.yml          # описание двух сервисов: stage1 и stage2
```

## Пайплайн: 6 шагов

1. **music_removal** — удаление фоновой музыки  
2. **denoise** — шумоподавление  
3. **diarization** — диаризация и транскрибация (SRT, TXT)  
4. **role_parser** — определение ролей спикеров (JSON)  
5. **audio_separation** — разделение аудио по ролям (WAV на каждую роль)  
6. **voice_params** — извлечение голосовых признаков (CSV)

## Выходные данные

| Шаг | Результат |
| --- | --------- |
| 1. music_removal | Аудиофайл без музыки |
| 2. denoise | Аудио с подавленным шумом |
| 3. diarization | `.srt` (таймкоды со спикерами) и `.txt` (транскрипция) |
| 4. role_parser | `_roles.json` — соответствие спикеров ролям |
| 5. audio_separation | `_user.wav`, `_assistant.wav`, `_robot.wav` |
| 6. voice_params | `features.csv` — вектор признаков для каждой роли |

## Модели

### YAMNet

Используется предобученная модель [YAMNet](https://tfhub.dev/google/yamnet/1) для детекции музыкальных фрагментов.

### Whisper + NeMo MSDD (диаризация)

Основано на репозитории [whisper-diarization](https://github.com/MahmoudAshraf97/whisper-diarization).  
Пайплайн включает:

- Извлечение вокального трека для повышения точности эмбеддингов
- Генерация транскрипции через Whisper
- Коррекция таймстемпов через ctc-forced-aligner
- VAD и сегментация (MarbleNet)
- Извлечение эмбеддингов спикеров (TitaNet)
- Постобработка с выравниванием по знакам препинания

**Параметры моделей Whisper и требования к VRAM:**

| Модель        | VRAM (GB) | Качество | Скорость |
|---------------|-----------|----------|----------|
| tiny          | ~0.5      | Минимальное | Очень быстро |
| base          | ~1.5      | Базовое     | Быстро   |
| small         | ~2.0      | Среднее     | Средне   |
| medium        | ~5.0      | Хорошее     | Медленно |
| large-v2      | ~10.0     | Высокое     | Очень медленно |
| large-v3      | 10–12     | Максимальное | Медленно, рекомендуется для production |

### LLM для определения ролей

Для локального запуска используется **Qwen2.5-7B-Instruct** с 4-битной квантизацией (bitsandbytes).  
Для серверного запуска может использоваться **ChatGPT (версии 4.1–5)**.

**Ориентировочное потребление VRAM для Qwen:**

| Режим         | VRAM (GB) |
|---------------|-----------|
| FP16 (оригинал) | ~14       |
| 4-bit (квант.)  | ~6        |

При недостатке VRAM рекомендуется уменьшить размер модели (например, Qwen2.5-3B) или увеличить квантизацию.

**ChatGPT (через API):** не требует локальной VRAM, но необходим доступ к API и соответствующий ключ.

### LLM для определения пола пользователя
Для задачи определения пола говорящего используется модель ECAPA‑Gender (архитектура ECAPA‑TDNN), обученная на наборах голосовых данных для бинарной классификации (мужской/женский голос).
Модель загружается из репозитория Hugging Face: JaesungHuh/voice-gender-classifier.

Особенности:

- Принимает на вход аудиофайл (WAV, моно, частота 16 кГц).
- Возвращает метку: "male" или "female".
- Работает в пайплайне после отделения голоса пользователя.

Используется в pipeline как пост‑процессор для дальнейшего анализа данных (добавление колонки defined_gender в CSV с акустическими признаками).

**Примечание:** при первом запуске модель автоматически загружается с Hugging Face Hub. Для работы в среде без интернета можно предварительно скачать веса и указать локальный путь.

## Требования к системе

- **GPU (обязателен)** для шагов 3 (diarization) и 4 (role_parser). На CPU работа крайне медленная или невозможна.
- **Рекомендуемый объём VRAM:** от 8 ГБ (для Qwen 4-bit + Whisper medium).
- **RAM:** от 16 ГБ.
- **Дисковое пространство:** от 20 ГБ (модели + промежуточные WAV).
- **ОС:** Linux (рекомендуется Ubuntu 20.04+) или WSL2.

## Установка и запуск

### Запуск через Docker (рекомендуется)

Проект использует два изолированных контейнера из-за конфликта зависимостей:

- **stage1** — шаги 1–2 (music_removal, denoise)
- **stage2** — шаги 3–6 (diarization, role_parser, audio_separation, voice_params, gender_classification)

Оба сервиса описаны в `orchestrator/docker-compose.yml`.

#### 1. Подготовка

Склонируйте репозиторий с субмодулями:

```bash
git clone --recurse-submodules https://github.com/VladisRave/wav-parser.git
cd wav-parser
```

Используйте файл `.env` расположенный в папке `orchestrator/` и замените данные по умолчанию на необходимые для вашего запуска. Основные переменные:

| Переменная | Описание | Значение по умолчанию |
| ---------- | -------- | --------------------- |
| `DATA_DIR` | Путь к входным аудиофайлам | `./input` |
| `WHISPER_MODEL_SIZE` | Размер модели Whisper | `large-v3` |
| `LLM_MODE` | `local` (Qwen) или `openai` | `server` |
| `OPENAI_API_KEY` | Ключ для ChatGPT | (пусто) |
| `FROM_STEP` | Начальный шаг (1-6) | 1 |
| `TO_STEP` | Конечный шаг (1-6) | 6 |

Задание параметров происходит двумя способами:

```bash
# через .env в orchestrator/
FROM_STEP=3
TO_STEP=5
```

```bash
# или через командную строку docker
docker run -e FROM_STEP=3 -e TO_STEP=5 --rm stage2
```

#### 2. Сборка и запуск

```bash
cd orchestrator
docker-compose build
```

Запуск всех шагов (сначала stage1, затем stage2):

```bash
docker-compose run --rm stage1 && docker-compose run --rm stage2
```

Флаг `--rm` удаляет контейнер после завершения. Если вы хотите сохранить контейнер для отладки, уберите `--rm`.

#### 3. Запуск отдельных шагов

В каждом сервисе можно задать диапазон шагов через переменные окружения `FROM_STEP` и `TO_STEP`. Например, для stage2 выполнить только шаги 3–4:

```bash
docker-compose run -e FROM_STEP=3 -e TO_STEP=4 --rm stage2
```

#### 4. Монтирование кэша HuggingFace

Чтобы избежать повторной загрузки моделей при каждом запуске, подключите кэш с хоста:

```bash
docker-compose run --rm -v ~/.cache/huggingface:/root/.cache/huggingface stage2
```

### Локальный запуск (без Docker)

#### 1. Окружение

```bash
conda create -n wav_parser python=3.10
conda activate wav_parser
pip install cython
sudo apt update && sudo apt install ffmpeg
pip install -c constraints.txt -r requirements.txt
```

#### 2. Запуск сервисов по отдельности

```bash
python services/music_removal/main.py --input audio/tracks --music_dir audio/clips --output audio/clean_audio
python services/denoise/main.py --input audio/clean_audio --output audio/denoised
python services/diarization/main.py --input audio/denoised --output audio/diarized
python services/role_parser/main.py --input audio/diarized --output audio/roles
python services/audio_separation/main.py --input_dir audio/roles --output_dir audio/splitted
python services/voice_params/main.py --input audio/splitted --output audio/features
```

Каждый `main.py` поддерживает независимый запуск и имеет встроенную справку (`--help`).

## Механизм работы пайплайна

### Рабочая директория

Пайплайн создаёт временную папку `output/work/`, где хранит промежуточные результаты. После успешного выполнения всех 6 шагов данные копируются в `output/`, а `work/` удаляется.

### Отслеживание прогресса

- `work/completed_steps` — список завершённых шагов для текущей сессии. При повторном запуске уже выполненные шаги пропускаются.
- `output/processed.log` — список обработанных аудиофайлов (по именам). При последующих запусках эти файлы игнорируются.

### Кэширование моделей

Модели (Whisper, Qwen, ChatGPT) загружаются из HuggingFace и кэшируются в `~/.cache/huggingface`. Рекомендуется монтировать эту папку в контейнер, чтобы избежать повторной загрузки.

## Мониторинг

Для контейнеров, запущенных без `--rm`:

```bash
# Статус
docker ps | grep wav-parser

# Логи в реальном времени
docker logs -f <container_name>

# Последние 50 строк
docker logs --tail 50 <container_name>
```

Если контейнер запущен с `--rm`, логи теряются после остановки. Для отладки временно убирайте этот флаг.

## Известные ограничения

- **GPU обязателен** для шагов 3 и 4. На CPU возможны зависания или экстремально медленная работа.
- **Длинные транскрипции** (>6000 символов) обрезаются перед отправкой в LLM (для определения ролей достаточно начала разговора).
- **OOM (out of memory)** на шаге 4 приводит к пропуску файла, но не останавливает обработку всей пачки.
- **Дисковое пространство:** шаги 1–5 генерируют промежуточные WAV-файлы. Убедитесь, что достаточно места (минимум 10 ГБ свободно для обработки сотен файлов).
- **Конфликт зависимостей** между music_removal/denoise и остальными шагами решён разделением на два Docker-контейнера.

## Attribution

Проект использует следующие внешние реализации:

[https://github.com/MahmoudAshraf97/whisper-diarization](https://github.com/MahmoudAshraf97/whisper-diarization)

[https://github.com/JaesungHuh/voice-gender-classifier](https://github.com/JaesungHuh/voice-gender-classifier)

Все права на оригинальные реализации принадлежат авторам. В проекте используется интеграция и модификации для пайплайна.

---

## Лицензия

Проект сделан под лицензией MIT license