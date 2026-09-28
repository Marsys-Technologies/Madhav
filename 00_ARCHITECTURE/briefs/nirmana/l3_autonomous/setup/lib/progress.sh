#!/usr/bin/env bash
# ==============================================================================
# progress.sh — progress detector + idle backoff for the L3 Kāla elevation
# supervisor.  Phase 1.4a / 1.4b of the pre-elevation setup.
#
# Implements LANE_G_ENVIRONMENT_SPEC_v1_0 §2.1 (confirmed defect C: the audit
# supervisor's progress detector counts ANY file change as progress, so the
# three-strikes idle halt can never fire) and §2.2 (confirmed defect D: no
# backoff scales with a no-progress streak).
#
# This file is deliberately a separate, sourceable library rather than two
# functions buried in the supervisor, so the detector can be exercised directly
# by tests/test_progress_and_backoff.sh.  A halt condition that has never been
# observed reading FALSE is not a detector (root CLAUDE.md §N.8).
#
# USAGE
#   source lib/progress.sh                      # as a library
#   lib/progress.sh fingerprint  <WT> <STATE>   # new detector (1.4a)
#   lib/progress.sh legacy       <WT> <STATE> <DIR> <WORKDIR>   # old detector
#   lib/progress.sh backoff      <crash> <noprog>               # new backoff
#   lib/progress.sh legacy-backoff <crash> <noprog>             # old backoff
# ==============================================================================

# ------------------------------------------------------------------------------
# WHAT COUNTS AS PROGRESS — and why.
#
# These sessions run under a cycle contract (LANE_G §3.5, AUDIT_CHARTER
# foreground-subagent law) which states: "a cycle is complete only if it pushed a
# commit and rewrote the state file with its own cycle number."  Progress is
# therefore defined as what SURVIVES INTO GIT plus what the campaign's own
# declared counters say — never as "a file somewhere changed".
#
# A cycle makes progress iff at least one of these four moved:
#   1. head        — HEAD advanced on the campaign branch (a real commit landed).
#   2. accepted    — the campaign's headline counter ("Accepted N/22") advanced.
#   3. state_sub   — the CONTENT of the state file's substantive sections
#                    (## Position .. ## End) changed.  Not its mtime, not its
#                    timestamp header, not a "last seen cycle N" line.
#   4. tracked     — the CONTENT of uncommitted edits to TRACKED files changed,
#                    excluding the liveness churn listed below.
#
# What is deliberately EXCLUDED, because a stuck session still produces it:
#   * untracked files entirely — a scratch note in _work/ is not progress.  If it
#     were real work the cycle contract requires it committed by cycle end.
#   * *.log, *.ndjson, **/logs/** — supervisor logs, stream captures, redact logs.
#   * EVENTS.jsonl and 00_ARCHITECTURE/autonomy/state/*.jsonl (HEARTBEAT, SPEND)
#     — appended every cycle precisely to show the session is alive.
#   * the state file itself in the tracked-diff term; its substantive sections are
#     measured separately by (3) so a bumped timestamp line cannot mask a stall.
#   * .DS_Store.
#
# Residual risk, named honestly (LANE_G §2.1 carries the same note): a cycle could
# still move `head` with a cosmetic no-op commit.  This detector does not close
# that adversarial case — the honest-stop rule (LANE_G §3.6) is the defence
# against a dishonest agent; this is the defence against an honest one's
# accidental false positive, which is what defect C actually was.
# ------------------------------------------------------------------------------

PROGRESS_EXCLUDES=(
  ':(exclude,glob)**/*.log'
  ':(exclude,glob)**/*.ndjson'
  ':(exclude,glob)**/logs/**'
  ':(exclude,glob)**/EVENTS.jsonl'
  ':(exclude,glob)00_ARCHITECTURE/autonomy/state/*.jsonl'
  ':(exclude,glob)**/.DS_Store'
)

# progress_fingerprint <worktree> <state-file>
# Prints "head|accepted|state_sub|tracked".  Identical output across two cycles
# means NO PROGRESS.  Never fails the caller: missing inputs degrade to literal
# sentinels, which is itself a stable (i.e. no-progress) value.
progress_fingerprint() {
  local wt="$1" state="$2" rel head accepted state_sub tracked
  head=$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo NO-HEAD)
  accepted=$(grep -oE 'Accepted[[:space:]]+[0-9]+/[0-9]+' "$state" 2>/dev/null | head -1)
  state_sub=$(awk '/^## Position/{f=1} /^## End/{if(f){print;exit}} f{print}' "$state" 2>/dev/null \
              | shasum | cut -c1-16)
  rel="${state#"$wt"/}"
  tracked=$( cd "$wt" 2>/dev/null \
             && git diff HEAD -- . "${PROGRESS_EXCLUDES[@]}" ":(exclude)$rel" 2>/dev/null \
             | shasum | cut -c1-16 )
  printf '%s|%s|%s|%s\n' "${head:0:12}" "${accepted:-NO-COUNTER}" "$state_sub" "$tracked"
}

# legacy_fingerprint <worktree> <state-file> <dir> <workdir>
# EXACT reproduction of audit_supervisor.sh line 17, kept so the test can
# demonstrate the old detector's vacuity rather than assert it.
legacy_fingerprint() {
  { git -C "$1" rev-parse HEAD
    git -C "$1" status --porcelain
    shasum "$2" 2>/dev/null
    ls -1 "$3" "$4" 2>/dev/null
  } | shasum | cut -c1-16
}

# ------------------------------------------------------------------------------
# 1.4b — idle backoff (LANE_G §2.2).
#
# Tiers, and the cost each prevents:
#   crash >= 3          -> CRASH_SLEEP   (300s, unchanged from the audit script)
#   no-progress == 1    -> IDLE_SLEEP_1  (300s)
#   no-progress >= 2    -> IDLE_SLEEP_N  (900s)
#   otherwise           -> CYCLE_SLEEP   (30s, unchanged)
#
# Values 300/900 are taken from LANE_G §2.2 verbatim, not invented here; they are
# exported as env-overridable so an operator can tune without editing logic.
# Justification against the real failure they prevent: the audit run spent five
# consecutive cycles at ~$0.80 each re-polling CI with nothing to do, fired 30s
# apart.  With an honest detector (§2.1) plus this backoff, the same stall costs
# three cycles spread over ~20 minutes instead of three fired inside 90 seconds,
# and the existing 3-strike halt still fires at exactly the same strike count —
# only the money and wall-clock spent reaching it change.  There is deliberately
# no third idle tier: the halt at strike 3 makes one unreachable.
# ------------------------------------------------------------------------------
: "${CYCLE_SLEEP:=30}" "${CRASH_SLEEP:=300}" "${IDLE_SLEEP_1:=300}" "${IDLE_SLEEP_N:=900}"

# backoff_secs <crash-streak> <noprogress-streak>
backoff_secs() {
  local crash="${1:-0}" noprog="${2:-0}"
  if   [ "$crash"  -ge 3 ]; then echo "$CRASH_SLEEP"
  elif [ "$noprog" -ge 2 ]; then echo "$IDLE_SLEEP_N"
  elif [ "$noprog" -ge 1 ]; then echo "$IDLE_SLEEP_1"
  else                           echo "$CYCLE_SLEEP"
  fi
}

# legacy_backoff_secs <crash> <noprog> — audit_supervisor.sh line 63, verbatim logic.
legacy_backoff_secs() {
  if [ "${1:-0}" -ge 3 ]; then echo "$CRASH_SLEEP"; else echo "$CYCLE_SLEEP"; fi
}

# ---- CLI dispatch (only when executed, not when sourced) ---------------------
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  case "${1:-}" in
    fingerprint)     shift; progress_fingerprint "$@" ;;
    legacy)          shift; legacy_fingerprint "$@" ;;
    backoff)         shift; backoff_secs "$@" ;;
    legacy-backoff)  shift; legacy_backoff_secs "$@" ;;
    *) echo "usage: $0 fingerprint|legacy|backoff|legacy-backoff ..." >&2; exit 2 ;;
  esac
fi
