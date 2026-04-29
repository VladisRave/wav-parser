#!/bin/bash
set -e

TZ=UTC date -d "+3 hours" '+%H:%M:%S'

SERVICES_DIR="/app/services"

WORK_DIR="${WORK_DIR:-/shared/work}"
STATE_DIR="${STATE_DIR:-/shared/state}"
LOG_DIR="${LOG_DIR:-/shared/logs}"

mkdir -p "$WORK_DIR" "$STATE_DIR" "$LOG_DIR"

STEP_LOG="$STATE_DIR/completed_steps"
PIPELINE_LOG="$LOG_DIR/stage.log"

touch "$STEP_LOG" "$PIPELINE_LOG"

FROM_STEP=${FROM_STEP:-${1:-3}}
TO_STEP=${TO_STEP:-${2:-6}}

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
log " STAGE 3–6 START ($FROM_STEP → $TO_STEP)"
log "========================"

# STEP 3 — diarization
if [ "$FROM_STEP" -le 3 ] && [ "$TO_STEP" -ge 3 ]; then
    if ! step_done 3; then
        log "STEP 3 diarization"
        python3 "$SERVICES_DIR/diarization/main.py" \
            --input "$WORK_DIR" --output "$WORK_DIR"
        mark_step 3
        log "STEP 3 DONE"
    else
        log "STEP 3 SKIP"
    fi
fi

# STEP 4 — role parsing
if [ "$FROM_STEP" -le 4 ] && [ "$TO_STEP" -ge 4 ]; then
    if ! step_done 4; then
        log "STEP 4 role parsing"
        python3 "$SERVICES_DIR/role_parser/main.py" \
            --input "$WORK_DIR" --output "$WORK_DIR"
        mark_step 4
        log "STEP 4 DONE"
    else
        log "STEP 4 SKIP"
    fi
fi

# STEP 5 — audio separation
if [ "$FROM_STEP" -le 5 ] && [ "$TO_STEP" -ge 5 ]; then
    if ! step_done 5; then
        log "STEP 5 audio separation"
        python3 "$SERVICES_DIR/audio_separation/main.py" \
            --input_dir "$WORK_DIR" --output_dir "$WORK_DIR"
        mark_step 5
        log "STEP 5 DONE"
    else
        log "STEP 5 SKIP"
    fi
fi

# STEP 6 — voice params
if [ "$FROM_STEP" -le 6 ] && [ "$TO_STEP" -ge 6 ]; then
    if ! step_done 6; then
        log "STEP 6 voice params"
        python3 "$SERVICES_DIR/voice_params/main.py" \
            --input "$WORK_DIR" --output "$WORK_DIR"
        mark_step 6
        log "STEP 6 DONE"
    else
        log "STEP 6 SKIP"
    fi
fi

log "========================"
log " STAGE 3–6 END"
log "========================"