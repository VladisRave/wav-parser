#!/bin/bash

set -e  # Выход при первой ошибке

if [ $# -ne 3 ]; then
    echo "ОШИБКА: Неверное количество аргументов!"
    echo ""
    show_help
    exit 1
fi


INPUT_DIR=/input                # Задайте жестко путь на вашем сервере чтобы все работало исправно
MUSIC_DIR=/app/audio/clips      # Файл находится в образе позже будет сделан так чтобы можно было все задавать в образе
OUTPUT_ROOT=/output             # Задайте жестко путь на вашем сервере чтобы все работало исправно


# Проверка существования входных директорий
for dir in "$INPUT_DIR" "$MUSIC_DIR"; do
    if [ ! -d "$dir" ]; then
        echo "ОШИБКА: Директория не существует: $dir"
        exit 1
    fi
done

# Создание структуры выходных папок
CLEAN_AUDIO_DIR="$OUTPUT_ROOT/clean_audio"
FILT_AUDIO_DIR="$OUTPUT_ROOT/filt_audio"
RESULT_DIR="$OUTPUT_ROOT/result"

mkdir -p "$CLEAN_AUDIO_DIR"
mkdir -p "$FILT_AUDIO_DIR"
mkdir -p "$RESULT_DIR"

# Путь к сервисам
SERVICES_DIR="/app/services"

# Проверка доступности сервисов
SERVICES=("music_removal" "denoise" "diarization")
for service in "${SERVICES[@]}"; do
    if [ ! -f "$SERVICES_DIR/$service/main.py" ]; then
        echo "ОШИБКА: Сервис $service не найден!"
        echo "Проверьте путь: $SERVICES_DIR/$service/main.py"
        exit 1
    fi
done

# Подсчет файлов
INPUT_FILES=$(find "$INPUT_DIR" -type f \( -name "*.mp3" \) | wc -l)
if [ "$INPUT_FILES" -eq 0 ]; then
    echo "ПРЕДУПРЕЖДЕНИЕ: Нет MP3 файлов в $INPUT_DIR"
    exit 1
fi

echo "Найдено файлов для обработки: $INPUT_FILES"
echo ""

# Шаг 1: Удаление музыки
echo "ШАГ 1: УДАЛЕНИЕ МУЗЫКИ"

if ! python3 "$SERVICES_DIR/music_removal/main.py" \
    --input "$INPUT_DIR" \
    --music_dir "$MUSIC_DIR" \
    --output "$CLEAN_AUDIO_DIR"; then
    echo "ОШИБКА: Сервис music_removal завершился с ошибкой"
    exit 1
fi

CLEAN_FILES=$(find "$CLEAN_AUDIO_DIR" -type f -name "*.wav" | wc -l)
echo "Шаг 1 завершен. Обработано файлов: $CLEAN_FILES"

# Проверка наличия файлов после первого шага
if [ "$CLEAN_FILES" -eq 0 ]; then
    echo "ОШИБКА: Нет файлов для дальнейшей обработки"
    echo "Проверьте сервис music_removal и входные данные"
    exit 1
fi

# Шаг 2: Шумоподавление
echo "ШАГ 2: ШУМОПОДАВЛЕНИЕ"

if ! python3 "$SERVICES_DIR/denoise/main.py" \
    --input "$CLEAN_AUDIO_DIR" \
    --output "$FILT_AUDIO_DIR"; then
    echo "❌ ОШИБКА: Сервис denoise завершился с ошибкой"
    exit 1
fi

FILT_FILES=$(find "$FILT_AUDIO_DIR" -type f -name "*.wav" | wc -l)
echo ""
echo "Шаг 2 завершен. Обработано файлов: $FILT_FILES"

# Шаг 3: Диаризация
echo "ШАГ 3: ДИАРИЗАЦИЯ"
echo ""

if ! python3 "$SERVICES_DIR/diarization/main.py" \
    --input "$FILT_AUDIO_DIR" \
    --output "$RESULT_DIR"; then
    echo "ОШИБКА: Сервис diarization завершился с ошибкой"
    exit 1
fi

RESULT_FILES=$(find "$RESULT_DIR" -type f -name "*.wav" | wc -l)
echo "Шаг 3 завершен. Обработано файлов: $RESULT_FILES"

# Шаг 4: Выделение признаков
echo "ШАГ 3: ДИАРИЗАЦИЯ"
echo ""

if ! python3 "$SERVICES_DIR/voice_params/main.py" \
    --input "$RESULT_DIR" \
    --output "$RESULT_DIR"; then
    echo "ОШИБКА: Сервис voice_params завершился с ошибкой"
    exit 1
fi

RESULT_FILES=$(find "$RESULT_DIR" -type f -name "*.wav" | wc -l)
echo "Шаг 4 завершен. Обработано файлов: $RESULT_FILES"

echo ""

# Итоговая статистика
echo "======================================="
echo " ПАЙПЛАЙН УСПЕШНО ЗАВЕРШЕН"
echo "======================================="
echo " СТАТИСТИКА:"
echo " Входных файлов:    $INPUT_FILES"
echo " После удаления музыки: $CLEAN_FILES"
echo " После шумоподавления:  $FILT_FILES"
echo " Финальных результатов: $RESULT_FILES"

exit 0