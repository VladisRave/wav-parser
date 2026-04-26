#!/bin/bash
set -e

TZ=UTC date -d "+3 hours" '+%H:%M:%S'

STATE_DIR="/shared/state"
WORK_DIR="/shared/work"
INPUT_DIR="/shared/input"
LOG_DIR="/app/orchestrator/logs"
SERVICES_DIR="/app/services"

mkdir -p "$STATE_DIR" "$WORK_DIR" "$LOG_DIR"

PROCESSED_LOG="$STATE_DIR/processed.log"
STEP_LOG="$STATE_DIR/completed_steps"
PIPELINE_LOG="$LOG_DIR/stage.log"

touch "$PROCESSED_LOG"
touch "$STEP_LOG"
touch "$PIPELINE_LOG"

# диапазон шагов (ВАЖНО)
FROM_STEP=${FROM_STEP:-${1:-1}}
TO_STEP=${TO_STEP:-${2:-2}}

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$PIPELINE_LOG"
}

step_done() {
    grep -qFx "step_$1" "$STEP_LOG" 2>/dev/null
}

mark_step() {
    echo "step_$1" >> "$STEP_LOG"
}

log "========================"
log " STAGE 1–2 START ($FROM_STEP → $TO_STEP)"
log "========================"

# STEP 1 — music removal
if [ "$FROM_STEP" -le 1 ] && [ "$TO_STEP" -ge 1 ]; then
    if ! step_done 1; then
        log "STEP 1: music removal"

        python3 "$SERVICES_DIR/music_removal/main.py" \
            --input "$INPUT_DIR" \
            --output "$WORK_DIR"

        mark_step 1
        log "STEP 1 DONE"
    else
        log "STEP 1 SKIP"
    fi
fi

# STEP 2 — denoise
if [ "$FROM_STEP" -le 2 ] && [ "$TO_STEP" -ge 2 ]; then
    if ! step_done 2; then
        log "STEP 2: denoise"

        python3 "$SERVICES_DIR/denoise/main.py" \
            --input "$WORK_DIR" \
            --output "$WORK_DIR"

        mark_step 2
        log "STEP 2 DONE"
    else
        log "STEP 2 SKIP"
    fi
fi

log "========================"
log " STAGE 1–2 END"
log "========================"