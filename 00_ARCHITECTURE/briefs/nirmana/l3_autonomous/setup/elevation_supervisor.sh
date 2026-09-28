#!/usr/bin/env bash
# ==============================================================================
# elevation_supervisor.sh — unattended supervisor for the L3 KĀLA ELEVATION
# campaign.  Phase 1.4 of the pre-elevation setup.
#
# Adapted from /Users/Dev/madhav-l3/audit_supervisor.sh (the read-only audit's
# supervisor), per LANE_G_ENVIRONMENT_SPEC_v1_0 §2: "this spec assumes [it] is
# copied to elevation_supervisor.sh and adapted (not overwritten in place, since
# the audit's own supervisor is a historical artifact of a different, read-only
# campaign)."  audit_supervisor.sh is NOT edited by this phase.
#
# CANONICAL LOCATION: this file, in the repository, under
#   00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/
# — the same place the repo already keeps an overnight supervisor
# (00_ARCHITECTURE/briefs/overnight_campaign_plans/ekv_supervisor.sh).  It is run
# from a checkout; it is NOT copied to /Users/Dev/madhav-l3/, because a script
# living outside every repo (as audit_supervisor.sh does) is unversioned,
# unreviewable and undiffable — which is exactly how defects C and D survived a
# whole campaign unnoticed.
#
#   elevation_supervisor.sh preflight | run | status | stop
#
# WHAT CHANGED vs audit_supervisor.sh (and why):
#   1.4a  progress detector — was: hash of HEAD + `git status --porcelain` +
#         state-file shasum + `ls` of two directories, i.e. ANY file touch read
#         as progress, so the 3-strikes halt could never fire.  Now: lib/
#         progress.sh's progress_fingerprint(), which measures committed
#         advance, the Accepted N/22 counter, the state file's SUBSTANTIVE
#         section content, and tracked-file content diffs excluding liveness
#         churn (logs, heartbeats, EVENTS.jsonl, untracked scratch).
#   1.4b  idle backoff — was: one 30s tier for everything short of 3 crashes.
#         Now: 30s normal / 300s on the 1st no-progress cycle / 900s on the 2nd,
#         distinct from the 300s crash tier.
#   1.4c  permission scope — was: --dangerously-skip-permissions with no
#         allow/deny list anywhere.  Now: --permission-mode bypassPermissions
#         (never blocks on a prompt at 3am) PLUS the project .claude/
#         settings.json deny list, which is verified to bind under BOTH that
#         flag and --dangerously-skip-permissions (see PHASE1_4 record §1.4c).
#   1.4d  session persistence — set in three independent places (see below).
#   NEW   `preflight` — refuses to start if any of the above is not actually in
#         effect.  A control that is silently absent is worse than no control.
# ==============================================================================
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"

# --- 1.4d, place 1 of 3: process environment -------------------------------
# Inherited by the `claude` process this script launches and by every in-process
# Agent-tool subagent it spawns.  CLAUDE_CODE_CHILD_SESSION must be UNSET (a
# settings.json `env` block can set a variable but cannot unset an inherited
# one) or transcripts silently stop persisting and the session is unresumable.
unset CLAUDE_CODE_CHILD_SESSION
export CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib/progress.sh"

# --- configuration (env-overridable; no secret is ever read or printed here) --
ROOT="${ROOT:-/Users/Dev/madhav-l3}"
WT="${WT:-$ROOT/kala-frontier}"                 # the campaign worktree to supervise
LOGD="${LOGD:-$ROOT/elevation_logs}"
A="$WT/00_ARCHITECTURE/briefs/nirmana/l3_autonomous"
STATE="${STATE:-$A/KALA_ELEVATION_STATE.md}"
SETTINGS="$WT/.claude/settings.json"
DONE="$A/ELEVATION_DONE"; HOLD="$ROOT/ELEVATION_HOLD"; SUPLOG="$LOGD/supervisor.log"
MODEL="${MODEL:-claude-sonnet-5}"; EFFORT="${EFFORT:-high}"
MAX_CYCLES="${MAX_CYCLES:-40}"; MAX_CYCLE_SECS="${MAX_CYCLE_SECS:-5400}"; MAX_WALL="${MAX_WALL:-$((16*3600))}"
# CYCLE_SLEEP / CRASH_SLEEP / IDLE_SLEEP_1 / IDLE_SLEEP_N default in lib/progress.sh
mkdir -p "$LOGD"

say()    { echo "[sup] $(TZ=Asia/Kolkata date '+%F %H:%M:%S IST') $*" | tee -a "$SUPLOG"; }
notify() { osascript -e "display notification \"$1\" with title \"Kāla elevation\"" >/dev/null 2>&1 || true; }

ensure_proxy() { if ! lsof -nP -iTCP:5434 -sTCP:LISTEN >/dev/null 2>&1; then
    nohup cloud-sql-proxy --address 127.0.0.1 --port 5434 madhav-astrology:asia-south1:amjis-postgres >"$LOGD/proxy.log" 2>&1 &
    echo $! > "$LOGD/proxy.pid"; sleep 6; say "cloud-sql-proxy started on 5434 (pid $(cat "$LOGD/proxy.pid"))"; fi; }

# ------------------------------------------------------------------------------
# preflight — every control this phase installs, asserted to be actually in
# effect before a single paid cycle runs.  Each check names the claim it makes
# and would read FALSE if the control were missing (CLAUDE.md §N.8).
# ------------------------------------------------------------------------------
preflight() {
  local bad=0 ok
  ok() { printf '  OK    %s\n' "$*"; }
  no() { printf '  FAIL  %s\n' "$*"; bad=1; }
  echo "── preflight ──────────────────────────────────────────────"
  [ -d "$WT" ]      && ok "worktree exists: $WT"                || no "worktree missing: $WT"
  [ -f "$STATE" ]   && ok "state file exists: ${STATE#$WT/}"    || no "state file missing: $STATE"
  [ "${CLAUDE_CODE_FORCE_SESSION_PERSISTENCE:-}" = "1" ] \
      && ok "1.4d env set in supervisor process"                || no "1.4d CLAUDE_CODE_FORCE_SESSION_PERSISTENCE not 1"
  [ -z "${CLAUDE_CODE_CHILD_SESSION:-}" ] \
      && ok "1.4d CLAUDE_CODE_CHILD_SESSION unset"              || no "1.4d CLAUDE_CODE_CHILD_SESSION still set"
  if [ -f "$SETTINGS" ] && python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$SETTINGS" 2>/dev/null; then
    ok "1.4c settings.json present and parses"
    python3 - "$SETTINGS" <<'PY' || bad=1
import json,sys
d=json.load(open(sys.argv[1])); p=d.get("permissions",{})
env=d.get("env",{})
fail=0
if env.get("CLAUDE_CODE_FORCE_SESSION_PERSISTENCE")=="1": print("  OK    1.4d env declared in settings.json")
else: print("  FAIL  1.4d env block does not declare CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1"); fail=1
n=len(p.get("deny",[]))
if n: print(f"  OK    1.4c deny list non-empty ({n} rules)")
else: print("  FAIL  1.4c deny list empty — the scope is decorative"); fail=1
dead=[r for r in p.get("allow",[])+p.get("deny",[])
      if r.split("(")[0] in ("Write","Glob","NotebookEdit","MultiEdit") and "(" in r]
if dead: print(f"  FAIL  1.4c dead rule form(s), never matched by the harness: {dead}"); fail=1
else: print("  OK    1.4c no dead rule forms (Write/Glob/NotebookEdit path rules)")
sys.exit(fail)
PY
  else no "1.4c settings.json missing or unparseable: $SETTINGS"; fi
  # 1.4a/1.4b: the detector and the backoff answer, and the backoff is tiered.
  local f; f="$(progress_fingerprint "$WT" "$STATE")"
  case "$f" in *'|'*'|'*'|'*) ok "1.4a detector returns a 4-term fingerprint: $f" ;; *) no "1.4a detector output malformed: $f" ;; esac
  if [ "$(backoff_secs 0 0)" -lt "$(backoff_secs 0 1)" ] && [ "$(backoff_secs 0 1)" -lt "$(backoff_secs 0 2)" ]; then
    ok "1.4b idle backoff is tiered: $(backoff_secs 0 0)s / $(backoff_secs 0 1)s / $(backoff_secs 0 2)s"
  else no "1.4b idle backoff is not tiered"; fi
  command -v gtimeout >/dev/null && ok "gtimeout present" || no "gtimeout missing (brew install coreutils)"
  [ -x "$ROOT/redact.py" ] && ok "redact.py present" || no "redact.py missing at $ROOT/redact.py"
  echo "───────────────────────────────────────────────────────────"
  [ $bad -eq 0 ] && echo "preflight: PASS" || echo "preflight: FAIL — supervisor will not start"
  return $bad
}

cycle_prompt() { cat <<EOF
You are cycle $1 of the unattended L3 KĀLA ELEVATION campaign (fresh context — your files are your memory).
Working directory: $WT. No human is available. Never ask, never wait.
Read IN FULL, in this order, then follow the cycle contract exactly:
 1. 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/readiness/_work/LANE_G_ENVIRONMENT_SPEC.md §3 (cycle contract)
 2. 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md
 3. ${STATE#$WT/}
Supervisor facts for this cycle: cycle=$1 of max $MAX_CYCLES; consecutive no-progress cycles so far=$2
(3 halts the run); hard cycle timeout=${MAX_CYCLE_SECS}s — finish, commit, push and rewrite the state file
well before it.

HOW THIS SUPERVISOR MEASURES PROGRESS (LANE_G §2.1, Phase 1.4a). A cycle counts as progress ONLY if it
moves one of: a new commit on this branch; the "Accepted N/22" counter; the CONTENT of the state file's
"## Position .. ## End" sections; or the content of a tracked, non-log file. Appending to EVENTS.jsonl,
HEARTBEAT.jsonl or any *.log, bumping the state file's timestamp header, or dropping an untracked scratch
note in _work/ does NOT count and never will. Do NOT try to satisfy the detector — LANE_G §3.6: an honest
stop beats invented activity. If nothing is eligible, print
  CYCLE $1: IDLE-OK <exact reason> -> next: <what unblocks it>
with zero git writes, and EXIT. Three of those in a row is a correct, intended halt.

All parallelism goes through in-process Agent-tool subagents with run_in_background:false. NEVER launch a
second top-level \`claude\` process from inside a cycle: it would not inherit this supervisor's session
environment (LANE_G Gap #1).
Fan out the wave; verify claims; integrate; commit+push; rewrite the state file; print one 'CYCLE $1: ...'
line; EXIT. Do not wait in-session for CI or deploys.
EOF
}

case "${1:-run}" in
 preflight) preflight; exit $? ;;
 status)
   echo "── Kāla elevation ── $(TZ=Asia/Kolkata date '+%H:%M IST') ── DONE:$([ -f "$DONE" ] && echo YES || echo no) HOLD:$([ -f "$HOLD" ] && echo YES || echo no)"
   tail -6 "$SUPLOG" 2>/dev/null; echo "--- last cycle lines"; grep -E "^CYCLE " "$LOGD/cycles.log" 2>/dev/null | tail -4 | cut -c1-200
   echo "--- headline"; grep -oE 'Accepted[[:space:]]+[0-9]+/[0-9]+' "$STATE" 2>/dev/null | head -1 ;;
 stop) touch "$HOLD"; pkill -f "elevation_supervisor.sh run" 2>/dev/null; echo "HOLD created; supervisor signalled." ;;
 run)
   [ -f "$HOLD" ] && { echo "ELEVATION_HOLD exists — remove $HOLD first."; exit 1; }
   preflight || { echo "refusing to run: see preflight failures above"; exit 1; }
   trap 'say "supervisor exiting"; [ -f "$LOGD/proxy.pid" ] && kill "$(cat "$LOGD/proxy.pid")" 2>/dev/null' EXIT
   trap 'say "interrupted"; exit 130' INT TERM
   cd "$WT" || { echo "no worktree $WT"; exit 1; }
   say "START model=$MODEL effort=$EFFORT worktree=$WT base=$(git rev-parse --short=9 HEAD)"
   T0=$(date +%s); n=0; noprog=0; crash=0
   while [ ! -f "$DONE" ] && [ ! -f "$HOLD" ] && [ $n -lt $MAX_CYCLES ] && [ $(( $(date +%s) - T0 )) -lt $MAX_WALL ]; do
     n=$((n+1)); ensure_proxy
     before=$(progress_fingerprint "$WT" "$STATE"); raw="$LOGD/cycle_$n.ndjson"
     say "CYCLE $n START (no-progress streak=$noprog)"
     # --- 1.4d, place 2 of 3: the env is re-asserted on the launch line itself,
     # so the cycle cannot inherit a stale value from an interactive shell that
     # re-exported CLAUDE_CODE_CHILD_SESSION between cycles.
     # --- 1.4c: bypassPermissions never blocks on a prompt at 3am, and the
     # project settings.json deny list is verified to still bind under it.
     env -u CLAUDE_CODE_CHILD_SESSION CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1 \
       gtimeout "$MAX_CYCLE_SECS" claude -p --permission-mode bypassPermissions \
        --model "$MODEL" --effort "$EFFORT" \
        --output-format stream-json --include-partial-messages --verbose "$(cycle_prompt "$n" "$noprog")" \
        < /dev/null 2>>"$LOGD/stderr.log" \
        | python3 -u "$ROOT/redact.py" 2>>"$LOGD/redact.log" \
        | tee "$raw" | "$ROOT/stream_format.sh" | tee -a "$LOGD/cycles.log"
     rc=${PIPESTATUS[0]}
     # Credentials must never persist: the pipe above redacts logs + terminal;
     # this scrubs the agent's own transcripts.  Defence in depth — the launch
     # line above deliberately never echoes or logs the environment at all.
     say "$(python3 "$ROOT/redact.py" --scrub "$LOGD" "$HOME"/.claude/projects/*madhav-l3* 2>/dev/null | tail -1)"
     after=$(progress_fingerprint "$WT" "$STATE")
     line=$(grep -E "^CYCLE " "$LOGD/cycles.log" | tail -1 | cut -c1-220)
     if [ "$before" = "$after" ]; then noprog=$((noprog+1)); else noprog=0; fi
     say "CYCLE $n END rc=$rc progress=$([ "$before" = "$after" ] && echo NO || echo yes) fp=$after | ${line:-<no CYCLE line>}"
     if [ $rc -ne 0 ]; then crash=$((crash+1)); else crash=0; fi
     if [ $noprog -ge 3 ]; then say "HALT: 3 consecutive no-progress cycles"; notify "HALTED — 3 no-progress cycles"; touch "$LOGD/STALLED"; break; fi
     if [ $crash -ge 6 ]; then say "HALT: 6 consecutive non-zero exits"; notify "HALTED — repeated crashes"; break; fi
     sleep_for=$(backoff_secs "$crash" "$noprog")
     [ "$sleep_for" != "$CYCLE_SLEEP" ] && say "backoff: crash=$crash no-progress=$noprog -> sleeping ${sleep_for}s"
     sleep "$sleep_for"
   done
   if [ -f "$DONE" ]; then say "ELEVATION COMPLETE after $n cycles"; notify "COMPLETE after $n cycles";
   elif [ -f "$HOLD" ]; then say "stopped by HOLD after $n cycles";
   else say "loop ended after $n cycles (cap, wall-clock or halt)"; notify "ended after $n cycles — check supervisor.log"; fi ;;
 *) echo "usage: $0 preflight|run|status|stop"; exit 2 ;;
esac
