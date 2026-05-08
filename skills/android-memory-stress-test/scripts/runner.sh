#!/bin/bash
# Memory-leak stress test driver for Android TV apps.
#
# Usage:
#   runner.sh <package-name> <run-dir> [cycles] [play-seconds]
#
# Each cycle: KEYCODE_DPAD_CENTER (open Detail) -> KEYCODE_DPAD_CENTER (Watch Now)
#             -> sleep <play-seconds> -> BACK -> BACK -> capture dumps -> RIGHT x5.
#
# Captures three dumpsys snapshots per checkpoint (M0, then C1..Cn):
#   mem_*.txt   - dumpsys meminfo <package>
#   act_*.txt   - dumpsys activity activities
#   drm_*.txt   - dumpsys media.resource_manager
#
# Parses each into one row of metrics.csv:
#   cycle,elapsed_sec,activities,views,appcontexts,native_kb,pss_kb,drm_active,prodpages,players,mains
#
# The 'activities' column is ActivityThread.mActivities (Java instances retained on
# heap), not the AMS-visible activity stack. That's intentional: leaked Activities
# remain in mActivities even after the AMS considers them finished.

set -u

PKG="${1:?package name required, e.g. com.swank.android}"
RUN_DIR="${2:?run dir required, e.g. /tmp/easel-3.18.4}"
CYCLES="${3:-7}"
PLAY_SECS="${4:-90}"

[[ -d "$RUN_DIR" ]] || { echo "run dir does not exist: $RUN_DIR" >&2; exit 1; }
command -v adb >/dev/null || { echo "adb not on PATH" >&2; exit 1; }
adb get-state >/dev/null 2>&1 || { echo "no adb device attached" >&2; exit 1; }

LOG="$RUN_DIR/detail.log"
CSV="$RUN_DIR/metrics.csv"
START_TS=$(date +%s)

parse_capture() {
  python3 - "$1" "$RUN_DIR" "$CSV" "$START_TS" "$PKG" <<'PY'
import sys, re, time
label, run_dir, csv, start_ts, pkg = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
elapsed = int(time.time()) - start_ts
with open(f"{run_dir}/mem_{label}.txt") as f: mem = f.read()
with open(f"{run_dir}/act_{label}.txt") as f: act = f.read()
with open(f"{run_dir}/drm_{label}.txt") as f: drm = f.read()
def find(rx, s, default=""):
    m = re.search(rx, s)
    return m.group(1) if m else default
activities = find(r"Activities:\s*(\d+)", mem)
views      = find(r"Views:\s*(\d+)", mem)
ctx        = find(r"AppContexts:\s*(\d+)", mem)
native     = find(r"Native Heap\s+(\d+)", mem)
pss        = find(r"TOTAL PSS:\s*(\d+)", mem)
# Active DRM sessions: lines like "    drm-session/<type>:..." in the active listing.
drm_active = sum(1 for ln in drm.splitlines() if re.match(r"^\s+drm-session/", ln))
# Activity-stack scan (informational only; useful for catching zombie t-1 records).
prods   = len(re.findall(r"ProductPageActivity", act))
players = len(re.findall(r"VideoPlayback|TVVideoPlayback|PlayerActivity", act))
mains   = len(re.findall(r"TVMainActivity|MainActivity", act))
print(f"{label} t={elapsed}s | acts={activities} views={views} ctx={ctx} native={native}KB pss={pss}KB drm-active={drm_active} prodpages={prods} players={players} mains={mains}")
with open(csv, "a") as f:
    f.write(f"{label},{elapsed},{activities},{views},{ctx},{native},{pss},{drm_active},{prods},{players},{mains}\n")
PY
}

capture() {
  local label=$1
  adb shell dumpsys meminfo "$PKG"           2>/dev/null > "$RUN_DIR/mem_$label.txt"
  adb shell dumpsys activity activities      2>/dev/null > "$RUN_DIR/act_$label.txt"
  adb shell dumpsys media.resource_manager   2>/dev/null > "$RUN_DIR/drm_$label.txt"
  {
    echo "===== $label  $(date '+%H:%M:%S') ====="
    cat "$RUN_DIR/mem_$label.txt"
    echo "--- activity ---"
    grep -E "${PKG//./\\.}|Resumed|Hist" "$RUN_DIR/act_$label.txt"
    echo "--- drm active ---"
    grep -E "^\s+drm-session/" "$RUN_DIR/drm_$label.txt"
    echo
  } >> "$LOG"
  parse_capture "$label"
}

cycle() {
  local n=$1
  echo ">> cycle $n nav -> detail -> watch -> ${PLAY_SECS}s -> back -> back"
  adb shell input keyevent KEYCODE_DPAD_CENTER
  sleep 4
  adb shell input keyevent KEYCODE_DPAD_CENTER
  sleep "$PLAY_SECS"
  adb shell input keyevent KEYCODE_BACK
  sleep 3
  adb shell input keyevent KEYCODE_BACK
  sleep 5
  capture "C$n"
  for _ in 1 2 3 4 5; do
    adb shell input keyevent KEYCODE_DPAD_RIGHT
    sleep 0.3
  done
  sleep 1
}

echo "cycle,elapsed_sec,activities,views,appcontexts,native_kb,pss_kb,drm_active,prodpages,players,mains" > "$CSV"
capture M0

for n in $(seq 1 "$CYCLES"); do
  cycle "$n"
done

echo ">> done"
