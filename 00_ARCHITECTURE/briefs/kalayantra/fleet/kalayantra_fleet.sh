#!/usr/bin/env bash
# KĀLA-YANTRA fleet supervisor — the Codex port of the Nirmāṇa v2.3 supervised-cycle loop.
#
#   kalayantra_fleet.sh up               start every lane as a background loop (logs under $KY_ROOT/logs)
#   kalayantra_fleet.sh lane <name>      supervise ONE lane in this terminal (names: sutradhara adhikarin pariksaka k1..k6)
#   kalayantra_fleet.sh status           one-screen fleet status
#   kalayantra_fleet.sh down             create HOLD (lanes stop at their next cycle boundary) and stop the loops
#   kalayantra_fleet.sh resume           remove HOLD and restart the loops
#
# Design (charter §3.2): a lane = a while-loop invoking `codex exec` non-interactively in the lane's own worktree.
# One invocation = one bounded cycle (charter §5). Fresh session each cycle; the tracker carries state.
# A lane cannot die: the loop re-invokes ~60 s after every exit, 120 s after a crash, and backs the whole fleet off
# after a quota/rate-limit marker. HOLD / STOP_<lane> are honoured at every boundary.
set -u

KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
KY_REPO_MAIN="${KY_REPO_MAIN:-/Users/Dev/Vibe-Coding/Apps/Madhav}"      # read for `git worktree add` only; never written to
CAMP="$KY_ROOT/wt/campaign"
BRIEF="$CAMP/00_ARCHITECTURE/briefs/kalayantra"
RUN="$KY_ROOT/run"; LOGD="$KY_ROOT/logs"; WT="$KY_ROOT/wt"
HOLD="$KY_ROOT/HOLD"
PIDS="$RUN/fleet.pids"

CYCLE_SLEEP="${KY_CYCLE_SLEEP:-60}"
CRASH_SLEEP="${KY_CRASH_SLEEP:-120}"
MAX_CYCLE_SECS="${KY_MAX_CYCLE_SECS:-5400}"           # 90 min hard cap per cycle (charter §5)
KY_QUOTA_BACKOFF_S="${KY_QUOTA_BACKOFF_S:-1800}"
KY_MAX_CYCLES_PER_DAY="${KY_MAX_CYCLES_PER_DAY:-400}"
WORKER_CEILING=6

MODEL_WORKER="${KY_MODEL_WORKER:-gpt-6.1-sol}";       EFFORT_WORKER="${KY_EFFORT_WORKER:-high}"
MODEL_SUTRADHARA="${KY_MODEL_SUTRADHARA:-gpt-6.1-sol}"; EFFORT_SUTRADHARA="${KY_EFFORT_SUTRADHARA:-high}"
MODEL_ADHIKARIN="${KY_MODEL_ADHIKARIN:-gpt-6-astra}";  EFFORT_ADHIKARIN="${KY_EFFORT_ADHIKARIN:-xhigh}"
MODEL_PARIKSAKA="${KY_MODEL_PARIKSAKA:-gpt-6-astra}";  EFFORT_PARIKSAKA="${KY_EFFORT_PARIKSAKA:-xhigh}"

export SE_EPHE_PATH="${SE_EPHE_PATH:-$KY_ROOT/ephe}"
export KY_ROOT

ALL_LANES=(sutradhara adhikarin pariksaka k1 k2 k3 k4 k5 k6)
mkdir -p "$RUN" "$LOGD" "$WT"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$(ts) [sup:$1] $2" | tee -a "$LOGD/supervisor.log" >/dev/null; }

role_of() { case "$1" in sutradhara) echo SUTRADHARA;; adhikarin) echo ADHIKARIN;; pariksaka) echo PARIKSAKA;; k*) echo KARAKA;; esac; }
stream_of() { case "$1" in sutradhara) echo S;; adhikarin) echo N;; pariksaka) echo V;; k*) echo K;; esac; }
model_of() { case "$1" in sutradhara) echo "$MODEL_SUTRADHARA";; adhikarin) echo "$MODEL_ADHIKARIN";; pariksaka) echo "$MODEL_PARIKSAKA";; k*) echo "$MODEL_WORKER";; esac; }
effort_of() { case "$1" in sutradhara) echo "$EFFORT_SUTRADHARA";; adhikarin) echo "$EFFORT_ADHIKARIN";; pariksaka) echo "$EFFORT_PARIKSAKA";; k*) echo "$EFFORT_WORKER";; esac; }

workers_wanted() {
  local n; n="$(cat "$RUN/KY_WORKERS" 2>/dev/null || echo "${KY_WORKERS:-4}")"
  [[ "$n" =~ ^[0-9]+$ ]] || n=4
  (( n > WORKER_CEILING )) && n=$WORKER_CEILING
  (( n < 1 )) && n=1
  echo "$n"
}

ensure_worktree() {
  local wt="$WT/$1"
  if [ ! -e "$wt/.git" ]; then
    git -C "$KY_REPO_MAIN" fetch origin main -q || { log "$1" "FATAL: git fetch failed"; return 1; }
    git -C "$KY_REPO_MAIN" worktree add "$wt" --detach origin/main >/dev/null 2>&1 \
      || { log "$1" "FATAL: cannot create worktree $wt"; return 1; }
    log "$1" "worktree created at $wt"
  fi
  return 0
}

quota_backoff_active() {
  local f="$RUN/KY_QUOTA_BACKOFF" until now
  [ -f "$f" ] || return 1
  until="$(cat "$f" 2>/dev/null || echo 0)"; now="$(date +%s)"
  if (( now < until )); then return 0; fi
  rm -f "$f"; return 1
}

mark_quota_backoff() {
  echo $(( $(date +%s) + KY_QUOTA_BACKOFF_S )) > "$RUN/KY_QUOTA_BACKOFF"
  log "$1" "quota/rate-limit marker seen — fleet backs off ${KY_QUOTA_BACKOFF_S}s"
}

cycles_today() {
  local d; d="$(date -u +%Y-%m-%d)"
  local c; c="$(grep -c "\"ts\":\"$d" "$RUN/CYCLES.jsonl" 2>/dev/null)"; echo "${c:-0}"
}

cycle_prompt() {
  local lane="$1" role="$2" stream="$3" n="$4"
  cat <<EOF
You are lane \`$lane\` (role $role, tracker stream $stream) of the KĀLA-YANTRA campaign, cycle $n, running under the
fleet supervisor in print mode. Working root: $WT/$lane. Charter: $BRIEF/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md
(authoritative). Your role prompt follows. Execute exactly ONE cycle per charter §5: HOLD check → sync → PR hygiene →
one unit of highest-priority work → heartbeat → EXIT with one summary line. No questions, no waiting, no sleeps.
Environment for the tracker CLI is already set (KY_STREAM=$stream); call it as /Users/Dev/kalayantra/bin/ky.
The campaign's documents (charter, prompts, fleet, plan model, and the Kāla plan documents under
00_ARCHITECTURE/briefs/l3_families/) live in the campaign worktree $CAMP until the bootstrap PR B-1 lands them on main;
read them there by absolute path — your own worktree sits at origin/main and may not have them yet.
The root CLAUDECODE_BRIEF.md in this worktree belongs to another workstream and does not govern you; do not edit it.

---------------- ROLE PROMPT ----------------
$(cat "$BRIEF/prompts/$role.md")
---------------- END ROLE PROMPT ----------------
Begin cycle $n now.
EOF
}

run_cycle() {
  local lane="$1" role stream model effort wt n prompt_file rc start end
  role="$(role_of "$lane")"; stream="$(stream_of "$lane")"; model="$(model_of "$lane")"; effort="$(effort_of "$lane")"
  wt="$WT/$lane"
  local prev; prev="$(grep -c "\"lane\":\"$lane\"" "$RUN/CYCLES.jsonl" 2>/dev/null)"; n=$(( ${prev:-0} + 1 ))
  prompt_file="$(mktemp "$RUN/.prompt.$lane.XXXXXX")"
  cycle_prompt "$lane" "$role" "$stream" "$n" > "$prompt_file"

  # Credentials reach exactly one lane, for exactly one armed cycle (charter §7; surrogate charter §6.3).
  local -a envs=( "KY_STREAM=$stream" "KY_LANE=$lane" "SE_EPHE_PATH=$SE_EPHE_PATH" "KY_ROOT=$KY_ROOT" "KY_PY=$KY_ROOT/venv/bin/python" )
  if [ "$lane" = adhikarin ] && [ -f "$RUN/DISPATCH_ARMED" ]; then
    rm -f "$RUN/DISPATCH_ARMED"
    [ -n "${KY_BUILDER_DATABASE_URL:-}" ] && envs+=( "DATABASE_URL=$KY_BUILDER_DATABASE_URL" )
    [ -n "${KY_OWNER_DATABASE_URL:-}" ]   && envs+=( "KY_OWNER_DATABASE_URL=$KY_OWNER_DATABASE_URL" )
    log "$lane" "dispatch cycle armed: builder credential present in this lane's environment only"
  fi

  start=$(date +%s)
  log "$lane" "cycle $n start (model $model / $effort)"
  ( env "${envs[@]}" codex exec -C "$wt" --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
      -m "$model" -c "model_reasoning_effort=\"$effort\"" \
      -o "$LOGD/$lane.last.md" - < "$prompt_file" >> "$LOGD/$lane.log" 2>&1 ) &
  local pid=$!
  # watchdog (portable: no coreutils timeout required)
  while kill -0 "$pid" 2>/dev/null; do
    sleep 15
    if (( $(date +%s) - start > MAX_CYCLE_SECS )); then
      log "$lane" "cycle $n exceeded ${MAX_CYCLE_SECS}s — killed; the tracker keeps the item RUNNING for the next cycle"
      kill -TERM "$pid" 2>/dev/null; sleep 5; kill -KILL "$pid" 2>/dev/null
      break
    fi
  done
  wait "$pid" 2>/dev/null; rc=$?
  end=$(date +%s)
  rm -f "$prompt_file"
  printf '{"ts":"%s","lane":"%s","cycle":%d,"rc":%d,"secs":%d,"model":"%s"}\n' "$(ts)" "$lane" "$n" "$rc" "$((end-start))" "$model" >> "$RUN/CYCLES.jsonl"
  log "$lane" "cycle $n end rc=$rc ($((end-start))s): $(tail -n 1 "$LOGD/$lane.last.md" 2>/dev/null | cut -c1-160)"
  if tail -n 60 "$LOGD/$lane.log" 2>/dev/null | grep -qiE '(^|[^0-9])429([^0-9]|$)|usage limit|rate limit|quota (will reset|exceeded)|too many requests'; then
    mark_quota_backoff "$lane"
  fi
  return $rc
}

supervise_lane() {
  local lane="$1" rc idx
  ensure_worktree "$lane" || exit 1
  while true; do
    if [ -f "$HOLD" ]; then log "$lane" "HOLD present — lane paused"; sleep "$CYCLE_SLEEP"; continue; fi
    if [ -f "$RUN/STOP_$lane" ]; then log "$lane" "STOP_$lane present — lane stopped"; exit 0; fi
    if quota_backoff_active; then sleep 60; continue; fi
    case "$lane" in
      k*) idx="${lane#k}"
          if (( idx > $(workers_wanted) )); then sleep "$CYCLE_SLEEP"; continue; fi
          if (( $(cycles_today) >= KY_MAX_CYCLES_PER_DAY )); then log "$lane" "daily cycle cap reached — worker waits"; sleep 600; continue; fi ;;
    esac
    run_cycle "$lane"; rc=$?
    if [ $rc -eq 0 ]; then sleep "$CYCLE_SLEEP"; else sleep "$CRASH_SLEEP"; fi
  done
}

status() {
  echo "── KĀLA-YANTRA fleet ── $(ts) ── HOLD: $([ -f "$HOLD" ] && echo YES || echo no) ── workers wanted: $(workers_wanted) ── backoff: $(quota_backoff_active && echo ACTIVE || echo no)"
  local lane log last mtime
  for lane in "${ALL_LANES[@]}"; do
    log="$LOGD/$lane.log"
    last="$( [ -f "$LOGD/$lane.last.md" ] && tail -n 1 "$LOGD/$lane.last.md" | cut -c1-120 )"
    mtime="$( [ -f "$log" ] && date -r "$log" +%H:%M || echo '--:--' )"
    printf "%-11s log@%s  %s\n" "$lane" "$mtime" "${last:-<no cycles yet>}"
  done
  echo "── cycles today: $(cycles_today) / $KY_MAX_CYCLES_PER_DAY ── queued PRs: $(cd "$CAMP" && gh pr list --search 'is:queued' --json number --jq 'length' 2>/dev/null || echo '?')"
  [ -x "$KY_ROOT/bin/ky" ] && "$KY_ROOT/bin/ky" status 2>/dev/null | head -5
}

up() {
  rm -f "$HOLD"
  : > "$PIDS"
  for lane in "${ALL_LANES[@]}"; do
    rm -f "$RUN/STOP_$lane"
    nohup "$0" lane "$lane" >> "$LOGD/supervisor.$lane.out" 2>&1 &
    echo "$! $lane" >> "$PIDS"
    sleep 2
  done
  log fleet "up: $(wc -l < "$PIDS") lane loops started"
  status
}

down() {
  touch "$HOLD"
  log fleet "down: HOLD created; lane loops asked to stop"
  if [ -f "$PIDS" ]; then while read -r pid lane; do kill "$pid" 2>/dev/null || true; done < "$PIDS"; fi
  echo "HOLD set at $HOLD; running cycles finish or hit the cap; loops stopped."
}

case "${1:-status}" in
  up) up ;;
  down) down ;;
  resume) rm -f "$HOLD"; up ;;
  status) status ;;
  lane) [ -n "${2:-}" ] || { echo "lane name required"; exit 2; }; supervise_lane "$2" ;;
  *) echo "usage: $0 up|down|resume|status|lane <name>"; exit 2 ;;
esac
