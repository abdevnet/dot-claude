#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
EFFORT=$(echo "$input" | jq -r '.effort.level // ""')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
DIR_BASENAME=$(echo "$DIR" | sed 's|.*[\\/]||')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
TOKENS=$(echo "$input" | jq -r '[.context_window.current_usage.input_tokens, .context_window.current_usage.output_tokens, .context_window.current_usage.cache_creation_input_tokens, .context_window.current_usage.cache_read_input_tokens] | map(. // 0) | add')
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

if [ "$TOKENS" -ge 1000 ]; then
  TOKENS_FMT="$((TOKENS / 1000))k"
else
  TOKENS_FMT="$TOKENS"
fi

CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; RESET='\033[0m'

# Pick bar color based on context usage
if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

FILLED=$((PCT / 10)); EMPTY=$((10 - FILLED))
BAR=$(printf "%${FILLED}s" | tr ' ' '█')$(printf "%${EMPTY}s" | tr ' ' '░')

MINS=$((DURATION_MS / 60000)); SECS=$(((DURATION_MS % 60000) / 1000))

BRANCH=""
git rev-parse --git-dir > /dev/null 2>&1 && BRANCH=" | 🕊️ $(git branch --show-current 2>/dev/null)"

EFFORT_LABEL=""
[ -n "$EFFORT" ] && EFFORT_LABEL=" ${CYAN}(${EFFORT})${RESET}"
echo -e "${GREEN}[$MODEL]${RESET}${EFFORT_LABEL} 📁 ${DIR_BASENAME}$BRANCH"
COST_FMT=$(printf '$%.2f' "$COST")
echo -e "${BAR_COLOR}${BAR}${RESET} ${PCT}% ${TOKENS_FMT} | ${GREEN}${COST_FMT}${RESET} | ⏱️ ${MINS}m ${SECS}s"
