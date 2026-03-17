#!/bin/bash

set -e

INPUT_DIR=/input
MUSIC_DIR=/app/audio/clips
SERVICES_DIR="/app/services"
OUTPUT_DIR=/output

INPUT_FILES=$(find "$INPUT_DIR" -type f -name "*.mp3" | wc -l)
mkdir -p "$OUTPUT_DIR"
start_total=$SECONDS

echo "Старт"

# CHECKING
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ Нет INPUT_DIR: $INPUT_DIR"
    exit 1
fi

if [ ! -d "$MUSIC_DIR" ]; then
    echo "❌ Нет MUSIC_DIR: $MUSIC_DIR"
    exit 1
fi

if [ "$INPUT_FILES" -eq 0 ]; then
    echo "❌ Нет MP3 файлов"
    exit 1
fi

echo "Найдено файлов: $INPUT_FILES"

# 1. MUSIC REMOVAL
echo "Шаг 1: Удаление музыки"
start_step=$SECONDS

python3 "$SERVICES_DIR/music_removal/main.py" \
    --input "$INPUT_DIR" \
    --music_dir "$MUSIC_DIR" \
    --output "$OUTPUT_DIR"

step_time_1=$((SECONDS - start_step))

# 2. DENOISE
echo "Шаг 2: Шумоподавление"
start_step=$SECONDS

python3 "$SERVICES_DIR/denoise/main.py" \
    --input "$OUTPUT_DIR" \
    --output "$OUTPUT_DIR"

step_time_2=$((SECONDS - start_step))

# 3. DIARIZATION
echo "Шаг 3: Диаризация"
start_step=$SECONDS

python3 "$SERVICES_DIR/diarization/main.py" \
    --input "$OUTPUT_DIR" \
    --output "$OUTPUT_DIR"

step_time_3=$((SECONDS - start_step))

# 4. AUDIO SEPARATION
echo "Шаг 4: Разделение аудио"
start_step=$SECONDS

python3 "$SERVICES_DIR/audio_separation/main.py" \
    --input "$OUTPUT_DIR" \
    --output "$OUTPUT_DIR"

step_time_4=$((SECONDS - start_step))

# 5. VOICE PARAMS
echo "Шаг 5: Признаки голоса"
start_step=$SECONDS

python3 "$SERVICES_DIR/voice_params/main.py" \
    --input "$OUTPUT_DIR" \
    --output "$OUTPUT_DIR"

step_time_5=$((SECONDS - start_step))

# FINAL
total_time=$((SECONDS - start_total))

echo " Пайплайн завершен "
echo " Входных файлов: $INPUT_FILES"
echo " ------------------------------ "
echo " Шаг 1 занял: ${step_time_1} сек"
echo " Шаг 2 занял: ${step_time_2} сек"
echo " Шаг 3 занял: ${step_time_3} сек"
echo " Шаг 4 занял: ${step_time_4} сек"
echo " Шаг 5 занял: ${step_time_5} сек"
echo " ------------------------------ "
echo " Общее время: ${total_time} сек"

exit 0