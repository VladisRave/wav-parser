#!/bin/bash

set -e

# =============================================================================
# Configuration
# =============================================================================
INPUT_DIR=/input
MUSIC_DIR=/app/audio/clips
SERVICES_DIR="/app/services"
OUTPUT_DIR=/output
WORK_DIR="$OUTPUT_DIR/.work"
PROCESSED_LOG="$OUTPUT_DIR/processed.log"
STEP_LOG="$WORK_DIR/.completed_steps"

# =============================================================================
# Parse arguments: --from N --to M (default: 1 to 6)
# =============================================================================
STEP_FROM=1
STEP_TO=6

while [[ $# -gt 0 ]]; do
    case "$1" in
        --from) STEP_FROM="$2"; shift 2 ;;
        --to)   STEP_TO="$2";   shift 2 ;;
        *)      shift ;;
    esac
done

if [ "$STEP_FROM" -lt 1 ] || [ "$STEP_FROM" -gt 6 ] || \
   [ "$STEP_TO" -lt 1 ]   || [ "$STEP_TO" -gt 6 ]   || \
   [ "$STEP_FROM" -gt "$STEP_TO" ]; then
    echo "Invalid step range: --from $STEP_FROM --to $STEP_TO (must be 1-6)"
    exit 1
fi

# =============================================================================
# Directories
# =============================================================================
mkdir -p "$OUTPUT_DIR" "$WORK_DIR"
touch "$PROCESSED_LOG"
touch "$STEP_LOG"

# =============================================================================
# Filter out already-processed files (only relevant when starting from step 1)
# =============================================================================
WORK_INPUT="$WORK_DIR/input"
mkdir -p "$WORK_INPUT"

NEW_COUNT=0
SKIP_COUNT=0
for mp3 in "$INPUT_DIR"/*.mp3; do
    [ -f "$mp3" ] || continue
    fname=$(basename "$mp3")
    if grep -qFx "$fname" "$PROCESSED_LOG"; then
        SKIP_COUNT=$((SKIP_COUNT + 1))
    else
        if [ ! -L "$WORK_INPUT/$fname" ] && [ ! -f "$WORK_INPUT/$fname" ]; then
            ln -sf "$mp3" "$WORK_INPUT/$fname"
        fi
        NEW_COUNT=$((NEW_COUNT + 1))
    fi
done

echo "============================================"
echo " Pipeline: steps $STEP_FROM → $STEP_TO"
echo "============================================"
echo " Всего MP3 в input: $((NEW_COUNT + SKIP_COUNT))"
echo " Уже обработано:    $SKIP_COUNT"
echo " Новых для обработки: $NEW_COUNT"
echo "============================================"

if [ "$NEW_COUNT" -eq 0 ] && [ "$STEP_FROM" -eq 1 ]; then
    echo "Нет новых MP3 файлов для обработки"
    exit 0
fi

# Checks
if [ ! -d "$INPUT_DIR" ]; then
    echo "Нет INPUT_DIR: $INPUT_DIR"
    exit 1
fi

if [ ! -d "$MUSIC_DIR" ]; then
    echo "Нет MUSIC_DIR: $MUSIC_DIR"
    exit 1
fi

# =============================================================================
# Helper: check if step was already completed in this batch
# =============================================================================
step_done() {
    grep -qFx "step_$1" "$STEP_LOG" 2>/dev/null
}

mark_step() {
    echo "step_$1" >> "$STEP_LOG"
}

# =============================================================================
# Pipeline steps
# =============================================================================
start_total=$SECONDS
declare -A step_times

# --- Step 1: Music Removal ---
if [ "$STEP_FROM" -le 1 ] && [ "$STEP_TO" -ge 1 ]; then
    if step_done 1; then
        echo "Шаг 1: Пропуск (уже выполнен)"
    else
        echo "Шаг 1: Удаление музыки"
        start_step=$SECONDS
        python3 "$SERVICES_DIR/music_removal/main.py" \
            --input "$WORK_INPUT" \
            --music_dir "$MUSIC_DIR" \
            --output "$WORK_DIR"
        step_times[1]=$((SECONDS - start_step))
        mark_step 1
    fi
fi

# --- Step 2: Denoise ---
if [ "$STEP_FROM" -le 2 ] && [ "$STEP_TO" -ge 2 ]; then
    if step_done 2; then
        echo "Шаг 2: Пропуск (уже выполнен)"
    else
        echo "Шаг 2: Шумоподавление"
        start_step=$SECONDS
        python3 "$SERVICES_DIR/denoise/main.py" \
            --input "$WORK_DIR" \
            --output "$WORK_DIR"
        step_times[2]=$((SECONDS - start_step))
        mark_step 2
    fi
fi

# --- Step 3: Diarization ---
if [ "$STEP_FROM" -le 3 ] && [ "$STEP_TO" -ge 3 ]; then
    if step_done 3; then
        echo "Шаг 3: Пропуск (уже выполнен)"
    else
        echo "Шаг 3: Диаризация"
        start_step=$SECONDS
        python3 "$SERVICES_DIR/diarization/main.py" \
            --input "$WORK_DIR" \
            --output "$WORK_DIR"
        step_times[3]=$((SECONDS - start_step))
        mark_step 3
    fi
fi

# --- Step 4: Role Parsing ---
if [ "$STEP_FROM" -le 4 ] && [ "$STEP_TO" -ge 4 ]; then
    if step_done 4; then
        echo "Шаг 4: Пропуск (уже выполнен)"
    else
        echo "Шаг 4: Определение ролей"
        start_step=$SECONDS
        python3 "$SERVICES_DIR/role_parser/main.py" \
            --input "$WORK_DIR" \
            --output "$WORK_DIR"
        step_times[4]=$((SECONDS - start_step))
        mark_step 4
    fi
fi

# --- Step 5: Audio Separation ---
if [ "$STEP_FROM" -le 5 ] && [ "$STEP_TO" -ge 5 ]; then
    if step_done 5; then
        echo "Шаг 5: Пропуск (уже выполнен)"
    else
        echo "Шаг 5: Разделение аудио"
        start_step=$SECONDS
        python3 "$SERVICES_DIR/audio_separation/main.py" \
            --input_dir "$WORK_DIR" \
            --output_dir "$WORK_DIR"
        step_times[5]=$((SECONDS - start_step))
        mark_step 5
    fi
fi

# --- Step 6: Voice Params ---
if [ "$STEP_FROM" -le 6 ] && [ "$STEP_TO" -ge 6 ]; then
    if step_done 6; then
        echo "Шаг 6: Пропуск (уже выполнен)"
    else
        echo "Шаг 6: Признаки голоса"
        start_step=$SECONDS
        python3 "$SERVICES_DIR/voice_params/main.py" \
            --input "$WORK_DIR" \
            --output "$WORK_DIR"
        step_times[6]=$((SECONDS - start_step))
        mark_step 6
    fi
fi

# =============================================================================
# Finalize: if all 6 steps done, move results and mark files as processed
# =============================================================================
if step_done 6; then
    echo "Все шаги завершены. Перемещение результатов..."
    # Copy results to final output (skip the .work dir itself and input symlinks)
    find "$WORK_DIR" -mindepth 1 -maxdepth 1 \
        ! -name "input" ! -name ".completed_steps" \
        -exec cp -r --force {} "$OUTPUT_DIR"/ \;

    # Mark files as processed
    for mp3 in "$WORK_INPUT"/*.mp3; do
        [ -f "$mp3" ] || [ -L "$mp3" ] || continue
        echo "$(basename "$mp3")" >> "$PROCESSED_LOG"
    done

    # Clean up work dir for next batch
    rm -rf "$WORK_DIR"
    echo "Рабочая директория очищена."
fi

# =============================================================================
# Summary
# =============================================================================
total_time=$((SECONDS - start_total))

echo ""
echo "============================================"
echo " Пайплайн завершен (шаги $STEP_FROM → $STEP_TO)"
echo "============================================"
for i in $(seq "$STEP_FROM" "$STEP_TO"); do
    if [ -n "${step_times[$i]+x}" ]; then
        echo " Шаг $i занял: ${step_times[$i]} сек"
    fi
done
echo " ------------------------------ "
echo " Общее время: ${total_time} сек"
echo "============================================"

exit 0
