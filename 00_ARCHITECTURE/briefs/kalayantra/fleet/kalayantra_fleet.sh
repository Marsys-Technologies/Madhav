#!/usr/bin/env bash
# KĀLA-YANTRA fleet supervisor v1.1 — the Codex port of the Nirmāṇa v2.3 supervised-cycle loop, corrected per
# reviews/ASTRA_REVIEW_KALAYANTRA_CHARTER_v1_0.md (KY-04, KY-12, KY-13, KY-21, KY-27).
#
#   kalayantra_fleet.sh up               snapshot this folder to $KY_ROOT/fleet_live and start every lane loop from the snapshot,
#                                        fully detached (idempotent: lane locks prevent duplicates)
#   kalayantra_fleet.sh lane <name>      supervise ONE lane in this terminal (sutradhara adhikarin v1 v2 k1..k6)
#   kalayantra_fleet.sh status           one-screen fleet status (log timestamps + tracker; not proof of progress — use `ky audit`)
#   kalayantra_fleet.sh down             write STOP files for every lane; active cycles finish inside their cap
#   kalayantra_fleet.sh resume           remove HOLD and STOP files and start loops
#
# Pool size is a FILE the conductor writes, never an environment default: run/KY_WORKERS (absent = 0 — no implementation worker
# runs before launch acceptance B-7) and run/KY_VERIFIERS (absent = 1 — one verifier until atomic claims land at B-2).
# Secrets: this process MUST NOT hold a production credential. It refuses to start if one is in its environment.
# Agents get an allow-listed environment (env -i). Production operations go through fleet/executor.py (operator-run).
set -u

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
PY=/opt/homebrew/bin/python3
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
KY_REPO_MAIN="${KY_REPO_MAIN:-/Users/Dev/Vibe-Coding/Apps/Madhav}"   # object store for `git worktree add`; its files are never written
CAMP="$KY_ROOT/wt/campaign"
BRIEF="$CAMP/00_ARCHITECTURE/briefs/kalayantra"
RUN="$KY_ROOT/run"; LOGD="$KY_ROOT/logs"; WT="$KY_ROOT/wt"
HOLD="$KY_ROOT/HOLD"

CYCLE_SLEEP="${KY_CYCLE_SLEEP:-60}"
CRASH_SLEEP="${KY_CRASH_SLEEP:-120}"
IDLE_SLEEP="${KY_IDLE_SLEEP:-600}"                       # after a cycle that printed IDLE-OK: no paid minute-by-minute polling
MAX_CYCLE_SECS="${KY_MAX_CYCLE_SECS:-5400}"
KY_QUOTA_BACKOFF_S="${KY_QUOTA_BACKOFF_S:-1800}"
KY_MAX_CYCLES_PER_DAY="${KY_MAX_CYCLES_PER_DAY:-400}"
WORKER_CEILING=6
CODEX_PROFILE="${KY_CODEX_PROFILE:-madhav-parity}"          # the repository's owner-authorised autonomy profile (GIP §P.4)

MODEL_WORKER="${KY_MODEL_WORKER:-gpt-6.1-sol}";         EFFORT_WORKER="${KY_EFFORT_WORKER:-high}"
MODEL_SUTRADHARA="${KY_MODEL_SUTRADHARA:-gpt-6.1-sol}"; EFFORT_SUTRADHARA="${KY_EFFORT_SUTRADHARA:-high}"
MODEL_ADHIKARIN="${KY_MODEL_ADHIKARIN:-gpt-6-astra}";   EFFORT_ADHIKARIN="${KY_EFFORT_ADHIKARIN:-xhigh}"
MODEL_PARIKSAKA="${KY_MODEL_PARIKSAKA:-gpt-6-astra}";   EFFORT_PARIKSAKA="${KY_EFFORT_PARIKSAKA:-xhigh}"
SE_EPHE_PATH="${SE_EPHE_PATH:-$KY_ROOT/ephe}"

ALL_LANES=(sutradhara adhikarin v1 v2 k1 k2 k3 k4 k5 k6)
mkdir -p "$RUN" "$LOGD" "$WT" "$RUN/claims" "$RUN/verdicts" "$RUN/reviews" "$RUN/ops/requests" "$RUN/ops/receipts" "$RUN/ops/acceptance" "$RUN/ops/sql"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$(ts) [sup:$1] $2" >> "$LOGD/supervisor.log"; }

refuse_secrets() {
  local v
  for v in DATABASE_URL KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL PGPASSWORD; do
    if [ -n "${!v:-}" ]; then echo "REFUSED: $v is set in the supervisor's environment. Secrets belong only to the executor's shell (charter §7)." >&2; exit 78; fi
  done
}

valid_lane() { case "$1" in sutradhara|adhikarin|v1|v2|k1|k2|k3|k4|k5|k6) return 0 ;; *) echo "invalid lane: $1" >&2; return 2 ;; esac; }
role_of()   { case "$1" in sutradhara) echo SUTRADHARA;; adhikarin) echo ADHIKARIN;; v*) echo PARIKSAKA;; k*) echo KARAKA;; esac; }
stream_of() { case "$1" in sutradhara) echo S;; adhikarin) echo N;; v*) echo V;; k*) echo K;; esac; }
model_of()  { case "$1" in sutradhara) echo "$MODEL_SUTRADHARA";; adhikarin) echo "$MODEL_ADHIKARIN";; v*) echo "$MODEL_PARIKSAKA";; k*) echo "$MODEL_WORKER";; esac; }
effort_of() { case "$1" in sutradhara) echo "$EFFORT_SUTRADHARA";; adhikarin) echo "$EFFORT_ADHIKARIN";; v*) echo "$EFFORT_PARIKSAKA";; k*) echo "$EFFORT_WORKER";; esac; }

wanted() {   # wanted <file> <default-when-absent> <ceiling>  → an integer in [0, ceiling]; malformed → the default
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); default = int(sys.argv[2]); ceiling = int(sys.argv[3])
try:
    n = int(p.read_text().strip(), 10) if p.exists() else default
except (OSError, ValueError):
    n = default
print(max(0, min(ceiling, n)))
PYEOF
}
workers_wanted()   { wanted "$RUN/KY_WORKERS" 0 "$WORKER_CEILING"; }
verifiers_wanted() { wanted "$RUN/KY_VERIFIERS" 1 2; }

ensure_worktree() {
  local wt="$WT/$1"
  if [ ! -e "$wt/.git" ]; then
    git -C "$KY_REPO_MAIN" fetch origin main -q || { log "$1" "FATAL: git fetch failed"; return 1; }
    git -C "$KY_REPO_MAIN" worktree add "$wt" --detach origin/main >/dev/null 2>&1 || { log "$1" "FATAL: cannot create worktree $wt"; return 1; }
    log "$1" "worktree created at $wt"
  fi
  [ -d "$wt/platform" ] || { log "$1" "FATAL: $wt is not a Madhav checkout"; return 1; }
  return 0
}

# ---- fleet-wide backoff and reservations (locked, fail-closed on malformed state) --------------------------------
quota_backoff_active() {
  "$PY" - "$RUN" <<'PYEOF'
import fcntl, pathlib, sys, time
root = pathlib.Path(sys.argv[1]); f = root / "KY_QUOTA_BACKOFF"
with (root / "backoff.lock").open("a+") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    if not f.exists(): sys.exit(1)
    try: until = int(f.read_text().strip())
    except ValueError: sys.exit(0)          # malformed → treat as active (fail closed); the supervisor logs it
    if time.time() < until: sys.exit(0)
    f.unlink(); sys.exit(1)
PYEOF
}
mark_quota_backoff() {
  "$PY" - "$RUN" "$KY_QUOTA_BACKOFF_S" <<'PYEOF'
import fcntl, pathlib, sys, time
root = pathlib.Path(sys.argv[1]); f = root / "KY_QUOTA_BACKOFF"; new = int(time.time()) + int(sys.argv[2])
with (root / "backoff.lock").open("a+") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    try: cur = int(f.read_text().strip()) if f.exists() else 0
    except ValueError: cur = 0
    f.write_text(str(max(cur, new)))
PYEOF
  log "$1" "quota/rate-limit marker in the current cycle log — fleet backs off ${KY_QUOTA_BACKOFF_S}s"
}
reserve_cycle() {   # prints the cycle number; exit 75 when the fleet cap (or the 80 % worker cap) is reached
  "$PY" - "$RUN" "$1" "$KY_MAX_CYCLES_PER_DAY" <<'PYEOF'
import datetime, fcntl, json, os, pathlib, sys
root = pathlib.Path(sys.argv[1]); lane = sys.argv[2]; cap = int(sys.argv[3])
with (root / "CYCLE_STARTS.lock").open("a+") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    p = root / "CYCLE_STARTS.jsonl"
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    today = sum(1 for r in rows if r["ts"][:10] == now[:10])
    limit = cap if not lane.startswith("k") else int(cap * 0.8)
    if today >= limit: sys.exit(75)
    n = 1 + sum(1 for r in rows if r["lane"] == lane)
    with p.open("a") as out:
        out.write(json.dumps({"ts": now, "lane": lane, "cycle": n}) + "\n"); out.flush(); os.fsync(out.fileno())
    print(n)
PYEOF
}

cycle_prompt() {
  local lane="$1" role="$2" stream="$3" n="$4"
  cat <<EOF
You are lane \`$lane\` (role $role, tracker stream $stream, worker id $lane) of the KĀLA-YANTRA campaign, cycle $n, running under
the fleet supervisor in print mode. Working root: $WT/$lane. Charter (authoritative): $BRIEF/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md (v1.1).
Execute exactly ONE cycle per charter §5: STOP/HOLD check → resume-or-sync → PR hygiene on YOUR registered PRs → one unit of
highest-priority work → renew claim, heartbeat → EXIT with one summary line. No questions, no waiting, no sleeps; long jobs are
operations you submit or inspect, not processes you wait for.
Tracker CLI: export PATH=$KY_ROOT/bin:\$PATH; export KY_STREAM=$stream; export KY_LANE=$lane. Runtime paths are absolute under $RUN and $LOGD.
The campaign's documents (charter, prompts, fleet, plan model, and the Kāla plan documents under 00_ARCHITECTURE/briefs/l3_families/)
live in $CAMP until the bootstrap PR B-1 lands them on main; read them there by absolute path — your worktree sits at origin/main.
The root CLAUDECODE_BRIEF.md in this worktree belongs to another workstream and does not govern you; do not edit it.
You hold no production credential; never run env/printenv unfiltered; never source ~/.config/pravaha/pgenv.sh.

---------------- ROLE PROMPT ----------------
$(cat "$BRIEF/prompts/$role.md")
---------------- END ROLE PROMPT ----------------
Begin cycle $n now.
EOF
}

run_cycle() {
  local lane="$1" role stream model effort wt n prompt_file rc start end cycle_log last_file
  role="$(role_of "$lane")"; stream="$(stream_of "$lane")"; model="$(model_of "$lane")"; effort="$(effort_of "$lane")"
  wt="$WT/$lane"
  n="$(reserve_cycle "$lane")" || { rc=$?; [ $rc -eq 75 ] && log "$lane" "daily cycle cap reached — lane waits"; return 75; }
  prompt_file="$(mktemp "$RUN/.prompt.$lane.XXXXXX")" || { log "$lane" "mktemp failed"; return 1; }
  cycle_prompt "$lane" "$role" "$stream" "$n" > "$prompt_file" || { log "$lane" "prompt generation failed"; rm -f "$prompt_file"; return 1; }
  cycle_log="$LOGD/$lane.$n.log"; last_file="$LOGD/$lane.$n.last.md"; LAST_FILE="$last_file"
  local -a envs=( "HOME=$HOME" "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$KY_ROOT/bin" "LANG=en_US.UTF-8" "TERM=dumb"
                  "KY_STREAM=$stream" "KY_LANE=$lane" "KY_ROOT=$KY_ROOT" "KY_PY=$KY_ROOT/venv/bin/python"
                  "SE_EPHE_PATH=$SE_EPHE_PATH" "SWE_EPHE_PATH=$SE_EPHE_PATH" "CODEX_HOME=$HOME/.codex" )
  start=$(date +%s)
  log "$lane" "cycle $n start (profile $CODEX_PROFILE, model $model / $effort)"
  env -i "${envs[@]}" "$PY" - "$MAX_CYCLE_SECS" "$cycle_log" "$prompt_file" \
      codex exec -p "$CODEX_PROFILE" -C "$wt" --skip-git-repo-check -m "$model" -c "model_reasoning_effort=\"$effort\"" -o "$last_file" - <<'PYEOF' &
import os, signal, subprocess, sys
limit = int(sys.argv[1]); logpath = sys.argv[2]; prompt = sys.argv[3]; argv = sys.argv[4:]
with open(logpath, "ab") as logf, open(prompt, "rb") as pin:
    p = subprocess.Popen(argv, stdin=pin, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    def terminate():
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try: os.killpg(p.pid, sig)
            except ProcessLookupError: return
            try: p.wait(timeout=10); return
            except subprocess.TimeoutExpired: continue
    def interrupted(signum, frame):
        terminate(); raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted); signal.signal(signal.SIGINT, interrupted)
    try:
        rc = p.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        terminate(); rc = 124
    finally:
        try: os.killpg(p.pid, signal.SIGKILL)   # reap any tool descendant that outlived codex
        except ProcessLookupError: pass
raise SystemExit(rc)
PYEOF
  local pid=$!
  trap 'kill -TERM "$pid" 2>/dev/null; wait "$pid" 2>/dev/null; exit 143' TERM INT
  wait "$pid"; rc=$?
  trap - TERM INT
  end=$(date +%s)
  rm -f "$prompt_file"
  printf '{"ts":"%s","lane":"%s","cycle":%d,"rc":%d,"secs":%d,"model":"%s"}\n' "$(ts)" "$lane" "$n" "$rc" "$((end-start))" "$model" >> "$RUN/CYCLES.jsonl"
  [ $rc -eq 124 ] && log "$lane" "cycle $n exceeded ${MAX_CYCLE_SECS}s and was terminated; the claim record resumes it next cycle"
  log "$lane" "cycle $n end rc=$rc ($((end-start))s)"
  if grep -qiE '(^|[^0-9])429([^0-9]|$)|usage limit|rate limit|quota (will reset|exceeded)|too many requests' "$cycle_log" 2>/dev/null; then
    mark_quota_backoff "$lane"
  fi
  return $rc
}

supervise_lane() {
  local lane="$1" rc idx
  ensure_worktree "$lane" || { log "$lane" "worktree unavailable — retry in ${CRASH_SLEEP}s"; sleep "$CRASH_SLEEP"; exec bash "$SELF" lane-locked "$lane"; }
  while true; do
    if [ -f "$RUN/STOP_$lane" ]; then log "$lane" "STOP_$lane present — lane stopped"; exit 0; fi
    if [ -f "$HOLD" ]; then sleep 60; continue; fi
    if quota_backoff_active; then sleep 60; continue; fi
    case "$lane" in
      k*) idx="${lane#k}"; if (( idx > $(workers_wanted) )); then sleep 60; continue; fi ;;
      v*) idx="${lane#v}"; if (( idx > $(verifiers_wanted) )); then sleep 60; continue; fi ;;
    esac
    LAST_FILE=""; run_cycle "$lane"; rc=$?
    case $rc in
      0) if [ -n "$LAST_FILE" ] && grep -q 'IDLE-OK' "$LAST_FILE" 2>/dev/null; then sleep "$IDLE_SLEEP"; else sleep "$CYCLE_SLEEP"; fi ;;
      75) sleep 300 ;;
      *) sleep "$CRASH_SLEEP" ;;
    esac
  done
}

locked_lane() {   # one loop per lane, enforced by an exclusive non-blocking lock
  valid_lane "$1" || return 2
  "$PY" - "$RUN/$1.lock" "$SELF" "$1" <<'PYEOF'
import fcntl, subprocess, sys
lock = open(sys.argv[1], "a+")
try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError: raise SystemExit(0)      # already supervised
raise SystemExit(subprocess.call(["bash", sys.argv[2], "lane-locked", sys.argv[3]], pass_fds=(lock.fileno(),)))
PYEOF
}

status() {
  echo "── KĀLA-YANTRA fleet ── $(ts) ── HOLD: $([ -f "$HOLD" ] && echo YES || echo no) ── workers: $(workers_wanted) ── verifiers: $(verifiers_wanted) ── backoff: $(quota_backoff_active && echo ACTIVE || echo no)"
  local lane last n
  for lane in "${ALL_LANES[@]}"; do
    last="$(ls -t "$LOGD"/"$lane".*.last.md 2>/dev/null | head -1)"
    n="$( [ -n "$last" ] && basename "$last" | cut -d. -f2 )"
    printf "%-11s %s  cycle %-4s %s  %s\n" "$lane" "$( [ -f "$RUN/STOP_$lane" ] && echo STOP || echo run )" "${n:-—}" "$( [ -n "$last" ] && date -r "$last" +%H:%M || echo '--:--' )" "$( [ -n "$last" ] && tail -n 1 "$last" | cut -c1-100 )"
  done
  echo "── cycle starts today: $(grep -c "\"ts\":\"$(date -u +%Y-%m-%d)" "$RUN/CYCLE_STARTS.jsonl" 2>/dev/null) / $KY_MAX_CYCLES_PER_DAY ── queued PRs: $(cd "$CAMP" && gh pr list --search 'is:queued' --json number --jq 'length' 2>/dev/null || echo '?')"
  [ -x "$KY_ROOT/bin/ky" ] && KY_STREAM=S "$KY_ROOT/bin/ky" status 2>/dev/null | head -6
  echo "(liveness and earned progress: KY_STREAM=S ky audit --since <ts>)"
}

snapshot_self() {   # supervisors run from a snapshot, so an edit in the working tree can never change a running loop
  local live="$KY_ROOT/fleet_live"
  mkdir -p "$live" && rsync -a --delete "$BRIEF/fleet/" "$live/" || return 1
  echo "$live/kalayantra_fleet.sh"
}
up() {
  refuse_secrets
  [ -f "$HOLD" ] && { echo "HOLD exists at $HOLD; use: $0 resume"; return 1; }
  local lane runner
  runner="$(snapshot_self)" || { echo "cannot snapshot the fleet folder to $KY_ROOT/fleet_live"; return 1; }
  for lane in "${ALL_LANES[@]}"; do
    rm -f "$RUN/STOP_$lane"
    # double-fork into a new session: the loop survives the shell (or the Codex session) that started it
    "$PY" -c 'import os, sys
if os.fork(): os._exit(0)
os.setsid()
if os.fork(): os._exit(0)
log = os.open(sys.argv[3], os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600); null = os.open(os.devnull, os.O_RDONLY)
os.dup2(null, 0); os.dup2(log, 1); os.dup2(log, 2)
os.execvp("bash", ["bash", sys.argv[1], "lane", sys.argv[2]])' "$runner" "$lane" "$LOGD/supervisor.$lane.out"
  done
  sleep 2; log fleet "up requested for ${#ALL_LANES[@]} lanes from $runner (locks dedupe)"; status
}
down() {
  local lane
  for lane in "${ALL_LANES[@]}"; do touch "$RUN/STOP_$lane"; done
  log fleet "down: STOP files written; active cycles finish within the cap"
  echo "Stop requested. Active cycles keep their watchdog and finish within ${MAX_CYCLE_SECS}s; loops then exit."
}

case "${1:-status}" in
  up) up ;;
  down) down ;;
  resume) rm -f "$HOLD"; for lane in "${ALL_LANES[@]}"; do rm -f "$RUN/STOP_$lane"; done; up ;;
  status) status ;;
  lane) refuse_secrets; locked_lane "${2:?lane name required}" ;;
  lane-locked) valid_lane "${2:?}" || exit 2; supervise_lane "$2" ;;
  *) echo "usage: $0 up|down|resume|status|lane <name>"; exit 2 ;;
esac
