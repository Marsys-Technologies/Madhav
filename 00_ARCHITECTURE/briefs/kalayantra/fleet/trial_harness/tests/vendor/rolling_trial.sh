#!/bin/bash
# SR-A10 L2 rolling 4-class trial: on every advance of origin/kalayantra/od1-integration, run the T1 harness (window stage + inline
# sharded-capable verify + numerical gate) on THAT head, 4 ruled classes, policy window_qualification/1. One run at a time (lock).
# Defects (gate verdict not PASS, or any G-1..G-7 failure) -> PAGES.log. Deterministic tooling, no agent. launchd: in.marsys.kalayantra.rolling-trial
set -u
F=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast
R=/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-review
H=$F/jobs/X-20261021T105440Z-od1-T1-harness/harness/run_trial.sh
OUT=/Users/Dev/scratch.noindex/claude/madhav/20261021-rolling-trial; mkdir -p "$OUT"
LOCK="$OUT/.lock"; LAST="$OUT/last_head"; LOG="$OUT/rolling.log"
log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
if ! mkdir "$LOCK" 2>/dev/null; then
  [ -n "$(find "$LOCK" -maxdepth 0 -mmin +120 2>/dev/null)" ] && { log "stale lock removed"; rmdir "$LOCK"; mkdir "$LOCK"; } || exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
pg_isready -q -h 127.0.0.1 -p 55433 || { log "test DB down; skip"; echo "$(date -u +%FT%TZ) PAGE rolling-trial: test DB 55433 down" >> "$F/PAGES.log"; exit 0; }
git -C "$R" fetch -q origin kalayantra/od1-integration || { log "fetch failed"; exit 0; }
head=$(git -C "$R" rev-parse origin/kalayantra/od1-integration)
[ "$head" = "$(cat "$LAST" 2>/dev/null)" ] && exit 0
run="$OUT/run-${head:0:12}-$(date -u +%Y%m%dT%H%M%SZ)"; src="$run/src"; mkdir -p "$src"
git -C "$R" archive "$head" | tar -x -C "$src" || { log "archive failed $head"; exit 0; }
log "START head=${head:0:12} [DIAGNOSTIC until TRIAL_READY/1 holds - SR-A10-1]"
TRIAL_CODE_HEAD="$head" TRIAL_POLICY=window_qualification/1 TRIAL_VERIFY=1 TRIAL_CROSSCHECK=1 \
TRIAL_CLASSES=bereavement,chronic_onset,illness_acute,major_loss TRIAL_LABEL=diagnostic-rolling-${head:0:12} \
  bash "$H" "$src" "$run/out" > "$run/trial.log" 2>&1
rc=$?; echo "$head" > "$LAST"
verdict=$(python3 -c "
import json,sys
import glob
try: d=json.load(open((sorted(glob.glob('$run/out/*_report.json'))+['$run/out/trial_report.json'])[0]))
except Exception as e: print('NO_REPORT'); sys.exit()
g=d.get('gate') or {}; t=d.get('totals') or {}; a=d.get('anomalies') or {}; v=d.get('verification') or {}
n=t.get('windows_total') or 0
print(g.get('status') or g.get('verdict'), 'numbered', n-(t.get('blank') or 0), 'of', n, 'defects', sum(x for x in a.values() if isinstance(x,int)) if isinstance(a,dict) else len(a),
      'verify', 'ran' if v.get('ran') else ('NOT_RUN '+str(v.get('not_run_reason') or '')[:80]))" 2>&1)
log "END head=${head:0:12} rc=$rc $verdict"
case "$verdict" in PASS*|PASSED*) ;; *) echo "$(date -u +%FT%TZ) PAGE rolling-trial head=${head:0:12} rc=$rc: $verdict (report $run/out)" >> "$F/PAGES.log";; esac
rm -rf "$src"
