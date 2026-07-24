#!/usr/bin/env bash
# elev_setup.sh — Elevation Campaign v2.1, Mode 2 pre-launch setup + verification.
# Run with:  bash /Users/Dev/Vibe-Coding/Apps/Madhav/elev_setup.sh
# Idempotent. Safe to re-run. Reports PASS/FAIL per item and exits non-zero if anything is wrong.

set -u

SRC="/Users/Dev/Vibe-Coding/Apps/Madhav"
SHARED="$HOME/elev-v2-shared"
CLONES=("$HOME/madhav-alpha" "$HOME/madhav-beta" "$HOME/madhav-gamma")
CAMPAIGN_DIR="00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign"
REGISTER="00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md"
FAILS=0

say()  { printf '\n\033[1m== %s\033[0m\n' "$1"; }
pass() { printf '  \033[32mPASS\033[0m  %s\n' "$1"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAILS=$((FAILS+1)); }
warn() { printf '  \033[33mNOTE\033[0m  %s\n' "$1"; }

# ─────────────────────────────────────────────────────────────────────────────
say "0. Source repo sanity"
if [ -d "$SRC/.git" ]; then pass "source repo found: $SRC"; else fail "source repo missing: $SRC"; exit 1; fi
if [ -f "$SRC/$CAMPAIGN_DIR/ELEVATION_CAMPAIGN_CHARTER_v2_1.md" ]; then
  pass "charter v2.1 present in source"
else
  fail "charter v2.1 MISSING in source — re-deliver it before launching"; exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
say "1. Commit + push campaign docs to main (they are currently untracked)"
# WHY THIS MATTERS: git clone copies only COMMITTED history. The charter, the register and the
# updated CLAUDECODE_BRIEF.md are untracked in the source repo, so the three clones do not have
# them. Every stream would abort at "read the charter".
cd "$SRC" || exit 1
git add -A -- CLAUDECODE_BRIEF.md "$CAMPAIGN_DIR" "$REGISTER" 2>/dev/null
if git diff --cached --quiet; then
  pass "nothing new to commit (already committed)"
else
  if git commit -q -m "docs(elevation): campaign charter v2.1, Mode 2 kickoff prompts, register v1.1

Governing artifacts for the SATYA-KAVACA + PURNA-GRAHANA autonomous elevation run.
Charter supersedes v1.0/v2.0 (archived). Register v1.1 adds EL-36..EL-61."; then
    pass "committed campaign docs"
  else
    fail "commit failed — inspect 'git status' in $SRC"
  fi
fi
if git push -q origin main 2>/dev/null; then
  pass "pushed to origin/main"
else
  warn "push to main was rejected (branch protection?) — NOT fatal."
  warn "The docs are copied directly into each clone below, so the run can still proceed."
  warn "If you want them on main first, push a branch and merge, then re-run this script."
fi

# ─────────────────────────────────────────────────────────────────────────────
say "2. Sync each clone and copy the campaign docs in directly"
for c in "${CLONES[@]}"; do
  name=$(basename "$c")
  if [ ! -d "$c/.git" ]; then fail "$name: clone missing"; continue; fi
  ( cd "$c" && git fetch -q origin && git checkout -q main && git pull -q --ff-only origin main ) 2>/dev/null \
    && pass "$name: synced to origin/main" \
    || warn "$name: pull reported an issue (continuing — docs are copied directly next)"
  # Belt and braces: copy the docs in regardless of git state, so the agents can always READ them.
  mkdir -p "$c/$CAMPAIGN_DIR"
  cp -R "$SRC/$CAMPAIGN_DIR/." "$c/$CAMPAIGN_DIR/" 2>/dev/null
  cp "$SRC/$REGISTER" "$c/$REGISTER" 2>/dev/null
  cp "$SRC/CLAUDECODE_BRIEF.md" "$c/CLAUDECODE_BRIEF.md" 2>/dev/null
done

# ─────────────────────────────────────────────────────────────────────────────
say "3. Copy environment files into each clone"
ENVS=("platform/.env" "platform/.env.local" ".env" ".env.rag")
for c in "${CLONES[@]}"; do
  name=$(basename "$c")
  copied=""
  for e in "${ENVS[@]}"; do
    if [ -f "$SRC/$e" ]; then
      mkdir -p "$(dirname "$c/$e")"
      cp "$SRC/$e" "$c/$e" 2>/dev/null && copied="$copied $e"
    fi
  done
  if [ -n "$copied" ]; then pass "$name: env files ->$copied"; else fail "$name: no env files copied"; fi
done

# ─────────────────────────────────────────────────────────────────────────────
say "4. Shared coordination state (outside every checkout)"
mkdir -p "$SHARED/locks" "$SHARED/implementations" "$SHARED/heartbeat" "$SHARED/proxy" "$SHARED/contracts"
for d in locks implementations heartbeat proxy contracts; do
  [ -d "$SHARED/$d" ] && pass "$SHARED/$d" || fail "could not create $SHARED/$d"
done
# Clear any stale flags from a previous attempt so the start gate is honest.
rm -f "$SHARED"/PHASE0_*.flag "$SHARED"/STREAM_*_COMPLETE.flag 2>/dev/null
pass "cleared stale phase/completion flags"

# ─────────────────────────────────────────────────────────────────────────────
say "5. Credentials"
gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q . \
  && pass "gcloud has an active account" || fail "gcloud has no active account"
( cd "$HOME/madhav-alpha" && git push --dry-run -q origin main 2>/dev/null ) \
  && pass "git push to origin works from alpha clone" || fail "git push from alpha clone failed"

# ─────────────────────────────────────────────────────────────────────────────
say "6. Final verification — can each stream actually read what its prompt requires?"
for c in "${CLONES[@]}"; do
  name=$(basename "$c")
  ok=1
  for f in "CLAUDECODE_BRIEF.md" \
           "$CAMPAIGN_DIR/ELEVATION_CAMPAIGN_CHARTER_v2_1.md" \
           "$CAMPAIGN_DIR/KICKOFF_PROMPTS_v2_1.md" \
           "$REGISTER" \
           "CLAUDE.md" \
           "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"; do
    [ -f "$c/$f" ] || { fail "$name: MISSING $f"; ok=0; }
  done
  [ "$ok" = "1" ] && pass "$name: all required reading present"
done

# ─────────────────────────────────────────────────────────────────────────────
printf '\n'
if [ "$FAILS" -eq 0 ]; then
  printf '\033[32m════ SETUP COMPLETE — 0 failures ════\033[0m\n'
  printf 'Launch order:\n'
  printf '  Terminal 1:  cd ~/madhav-alpha   -> paste the STREAM alpha prompt   (LAUNCH FIRST)\n'
  printf '  ...wait for "PHASE 0 COMPLETE" (~45-60 min)...\n'
  printf '  Terminal 2:  cd ~/madhav-beta    -> paste the STREAM beta prompt\n'
  printf '  Terminal 3:  cd ~/madhav-gamma   -> paste the STREAM gamma prompt\n\n'
  exit 0
else
  printf '\033[31m════ %s FAILURE(S) — fix before launching ════\033[0m\n\n' "$FAILS"
  exit 1
fi
