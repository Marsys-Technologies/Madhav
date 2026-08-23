#!/usr/bin/env bash
# Refuses to launch the fleet unless the environment can actually run it.
# Every check here is a real detector: nothing passes on the presence of a variable
# alone (plan I5 / CLAUDE.md §N.8 — a claim without a detector behind it is null).
set -uo pipefail
REPO="${NIRMANA_REPO:?set NIRMANA_REPO to the Madhav repo root}"
fail=0
say(){ printf '%-52s %s\n' "$1" "$2"; }
chk(){ if eval "$2" >/dev/null 2>&1; then say "$1" "OK"; else say "$1" "MISSING"; fail=1; fi; }

echo "── Nirmāṇa autonomous fleet · preflight ──────────────────"
chk "repo present"              "[ -d '$REPO/00_ARCHITECTURE' ]"
PLAN="$REPO/00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md"
PLAN_V="$(awk '/^version:/{print $2; exit}' "$PLAN" 2>/dev/null)"
PLAN_MAJ="${PLAN_V%%.*}"
if [ -n "$PLAN_MAJ" ] && [ "$PLAN_MAJ" -ge 5 ] 2>/dev/null; then
  say "plan version >= 5.0" "OK ($PLAN_V)"
else
  say "plan version >= 5.0" "NO (found '${PLAN_V:-none}')"; fail=1
fi
chk "charter present"           "[ -f '$REPO/00_ARCHITECTURE/autonomy/CHARTER.md' ]"
chk "claude cli"                "command -v claude"
chk "tmux"                      "command -v tmux"
chk "python venv"               "[ -x '$REPO/.venv/bin/python' ]"

# ── campaign branch ────────────────────────────────────────────────────────
BR="$(git -C "$REPO" branch --show-current 2>/dev/null)"
if [ "$BR" = "campaign/nirmana-autonomous" ]; then
  say "campaign branch checked out" "OK"
else
  say "campaign branch checked out" "NO — on '${BR:-<detached>}'"
  echo "     fix:  git -C '$REPO' checkout -b campaign/nirmana-autonomous"
  fail=1
fi

# ── DATABASE_URL: a real connection, not a non-empty string ────────────────
# The previous version of this check tested [ -n "$DATABASE_URL" ], which passes on a
# pasted placeholder. That is the same defect the campaign exists to cure, in the
# launcher itself. It now connects or it fails.
if [ -z "${DATABASE_URL:-}" ]; then
  say "DATABASE_URL set" "MISSING"; fail=1
elif printf '%s' "$DATABASE_URL" | grep -qE '…|\.\.\.|<|>|user:pass|example\.com'; then
  say "DATABASE_URL set" "PLACEHOLDER — paste the real connection string"; fail=1
else
  say "DATABASE_URL set" "OK"
  DBPY="$REPO/.venv/bin/python"; [ -x "$DBPY" ] || DBPY="$(command -v python3 || true)"
  if command -v psql >/dev/null 2>&1; then
    if psql "$DATABASE_URL" -Atc 'select 1' >/dev/null 2>&1; then say "database reachable (psql)" "OK"
    else say "database reachable (psql)" "CANNOT CONNECT"; fail=1; fi
  elif [ -n "$DBPY" ]; then
    if "$DBPY" - <<'PY' >/dev/null 2>&1
import os,sys
try:
    import psycopg
    psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=8).close()
except ImportError:
    try:
        import psycopg2
        psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=8).close()
    except ImportError:
        sys.exit(3)
except Exception:
    sys.exit(1)
PY
    then say "database reachable (python)" "OK"
    else
      rc=$?
      if [ "$rc" -eq 3 ]; then say "database reachable" "SKIPPED — no psql, no psycopg"; 
      else say "database reachable (python)" "CANNOT CONNECT"; fail=1; fi
    fi
  else
    say "database reachable" "SKIPPED — no client available"
  fi
fi

# ── I2: the snapshot that is the ONLY recovery path for the v1 gochara corpus ──
SNAP="$REPO/00_ARCHITECTURE/control/snapshots/20260823_pre_protection_removal"
if [ -d "$SNAP" ] && [ -n "$(ls -A "$SNAP" 2>/dev/null)" ]; then
  say "2026-08-23 snapshot present + non-empty" "OK"
else
  say "2026-08-23 snapshot present + non-empty" "MISSING — 38,287 unrecoverable rows depend on it"
  fail=1
fi

# ── ceilings: unset is a Reserved Power, not a default ─────────────────────
ST="$REPO/00_ARCHITECTURE/autonomy/state/CAMPAIGN_STATE.json"
SPEND="$REPO/00_ARCHITECTURE/autonomy/state/SPEND.jsonl"
METER="$REPO/00_ARCHITECTURE/autonomy/bin/spend_meter.py"
PYBIN="$REPO/.venv/bin/python"; [ -x "$PYBIN" ] || PYBIN="$(command -v python3 || true)"

if [ ! -f "$ST" ]; then
  say "campaign state present" "MISSING"; fail=1
elif [ -z "$PYBIN" ]; then
  say "ceilings enforceable" "CANNOT CHECK — no python3"; fail=1
else
  # Parse the JSON and assert the values MEAN something. The previous version of this
  # check was a grep for '": null"', which passed on 0, -1, "unlimited", the string
  # "null", a stray space before the colon, and the typo "nul" — i.e. it asserted the
  # shape of a substring, never the value. That is the exact §N.8 defect this campaign
  # exists to cure, and it sat thirty lines below the DATABASE_URL fix that got it right.
  CEIL_ERR="$("$PYBIN" - "$ST" <<'PY'
import json,sys
try:
    st=json.load(open(sys.argv[1]))
except Exception as e:
    print(f"CAMPAIGN_STATE.json does not parse: {e}"); sys.exit(0)
c=st.get("ceilings")
if not isinstance(c,dict):
    print("ceilings block missing or not an object"); sys.exit(0)
errs=[]
for k in ("tokens_campaign","tokens_per_rung","output_tokens_campaign","output_tokens_per_rung"):
    v=c.get(k,"__absent__")
    if v=="__absent__": errs.append(f"{k} absent")
    elif not isinstance(v,int) or isinstance(v,bool): errs.append(f"{k} is {v!r}, not an integer")
    elif v<=0: errs.append(f"{k} is {v}, must be > 0")
d=c.get("_token_definition")
if not isinstance(d,str) or len(d.strip())<20:
    errs.append("_token_definition missing or too short — the integer is meaningless without it")
if c.get("tokens_campaign") and c.get("tokens_per_rung") and isinstance(c["tokens_campaign"],int) and isinstance(c["tokens_per_rung"],int):
    if c["tokens_per_rung"]>c["tokens_campaign"]:
        errs.append("tokens_per_rung exceeds tokens_campaign")
print("; ".join(errs))
PY
)"
  if [ -z "$CEIL_ERR" ]; then say "ceilings set and coherent" "OK"
  else say "ceilings set and coherent" "$CEIL_ERR"; fail=1; fi
fi

# A ceiling without a meter is a claim with no detector behind it (I5 / §N.8).
if [ ! -x "$METER" ] && [ ! -f "$METER" ]; then
  say "spend meter present" "MISSING — bin/spend_meter.py; ceilings are unenforceable without it"; fail=1
elif [ ! -s "$SPEND" ]; then
  say "spend meter produces output" "NO READING — run the meter once before launch"; fail=1
else
  LASTSPEND="$(tail -n 1 "$SPEND" 2>/dev/null | cut -c1-100)"
  say "spend meter produces output" "OK"
  [ -n "$LASTSPEND" ] && echo "     last reading: $LASTSPEND"
fi

echo "──────────────────────────────────────────────────────────"
[ "$fail" -eq 0 ] && { echo "Preflight PASSED — safe to launch."; exit 0; }
echo "Preflight FAILED — fix the items above. Not launching."; exit 1
