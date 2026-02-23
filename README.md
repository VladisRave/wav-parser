# WAV-Parser

![Python](https://img.shields.io/badge/Python-3.9-blue)
![Torch](https://img.shields.io/badge/Torch-2.2.2-orange)
![HuggingFace](https://img.shields.io/badge/HuggingFace-models-yellow)

**WAV-Parser** — это парсер аудио, предназначенный для:

* Удаления музыкальных фоновых паттернов
* Повышения качества аудиозаписей
* Выделения голоса целевого пользователя из телефонной речи
* Определения роботов, операторов (опционально) и фоновой музыки (опционально)

Проект организован как набор сервисов, которые можно запускать независимо или объединять в единый пайплайн.

---

## Структура проекта

```text
audio-pipeline/
│
├── services/
│   ├── music_removal/
│   │   ├── main.py            # Точка входа для удаления музыки
│   │   ├── music_search.py    # Модуль детекции музыки
│   │   └── silence_replace.py # Замена тишины в аудио
│   │
│   ├── denoise/
│   │   ├── main.py            # Точка входа для денойзинга
│   │   └── denoise.py         # Модуль денойзинга
│   │
│   ├── diarization/
│   │   ├── main.py                # CLI для диаризации
│   │   ├── pipeline.py            # Оркестратор пайплайна
│   │   ├── diarize.py             # Диаризация с pyannote
│   │   ├── asr.py                 # Распознавание речи (ASR)
│   │   ├── robot_detector.py      # NLP-модуль для определения роботов
│   │   ├── speaker_selector.py    # Классификация человек/робот
│   │   └── audio_writer.py        # Сохранение обработанного аудио
│
├── common/
│   ├── audio_io.py        # Вспомогательные функции ввода/вывода аудио
│   ├── logging.py         # Настройка логирования
│   └── utils.py           # Общие утилиты
│
├── orchestrator/
│   ├── Dockerfile         # Конфигурация Docker
│   └── run_pipeline.sh    # Скрипт запуска полного пайплайна
│
└── docker-compose.yml     # Docker Compose конфигурация
```

---

## Быстрый старт

Существует два варианта использования проекта:

### Через Docker (рекомендуется для сервера)

1. Клонируем репозиторий:

```bash
git clone https://github.com/VladisRave/wav-parser.git
cd wav-parser
```

2. Откройте `Dockerfile` и укажите ваш **Hugging Face Token** для работы моделей pyannote и GigaAM.

3. Постройте и запустите контейнер:

```bash
docker build -t wav-parser .
./orchestrator/run_pipeline.sh
```

> Все сервисы будут работать в пайплайне автоматически.

---

### Локальное использование через терминал

1. Клонируем репозиторий и устанавливаем зависимости:

```bash
git clone https://github.com/VladisRave/wav-parser.git
cd wav-parser
pip install -r requirements.txt
```

2. Создайте папку `audio/tracks/` и положите туда ваши mp3-файлы:

```text
audio/
└── tracks/
    ├── file1.mp3
    ├── file2.mp3
    └── ...
```

3. Запускайте любой из сервисов вручную:

```bash
python ./services/diarization/main.py --input audio/tracks/ --output audio/result
python ./services/music_removal/main.py --input audio/tracks/ --output audio/cleaned
python ./services/denoise/main.py --input audio/tracks/ --output audio/denoised
```

> Каждый `main.py` можно запускать независимо.

---

## Примечания

* Проект находится в активной разработке. В первую очередь ведётся работа над диаризацией и ASR.
* Убедитесь, что ваша среда соответствует всем зависимостям из `requirements.txt`.
* Docker настроен для быстрого развёртывания и воспроизводимости окружения.

---

## Планируемое развитие

* [ ] Рабочий `docker-compose.yaml`
* [ ] Добавить анализ средней частоты и формант всех аудиофайлов
* [ ] Ускорить производительность диаризации и транскрибации с помощью GPU

---

![alt text](working.gif)


Как запускать контейнер
есть папка с mp3 файлами на выходе csv. 
Один оркестратор и три модуля один оркестратор делает. Входные папки как аргумент в контейнере запустить. Дефолтные пути в оркестраторе
1 секунду голоса на проверку(Вдруг плохо диаризировалось) написать в среднем как и прочие проблемы



Docker|-----> Папка|Подпапка(csv)|

docker build \
  -t wav-parse \
  -f Dockerfile \ 
  . \
  --no-cache
