#!/usr/bin/env bash
# KĀLA-YANTRA fast local precheck v1.1 — run from a lane worktree root BEFORE pushing.
# THIS IS NOT EQUIVALENT TO THE SIX REQUIRED GITHUB CHECKS. Required CI and PARĪKṢAKA's exact-head verdict remain the merge gate.
# What runs here: tsc (platform, platform-mcp) · vitest · migration-number guard · secret scan · drift/schema within CI's
# accepted baselines (exit 3 accepted; ceilings 79 / 43 from ci.yml, DVA Ruling 4) · TAP-6 grep · governance pytest in a scrubbed
# environment · the item's EXPLICIT tests (run/tests/<ITEM>.txt or TESTS= env, one path per line) · real application of any
# migration in the diff to this lane's database through migrate.ts · hygiene.
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; PYV="${KY_PY:-$KY_ROOT/venv/bin/python}"; LANE="${KY_LANE:-}"
FAIL=0; step() { echo; echo "── $1"; }; fail() { echo "   ✗ $1"; FAIL=1; }; ok() { echo "   ✓ $1"; }
CHANGED="$( (git diff --name-only origin/main...HEAD; git diff --name-only; git diff --name-only --cached) 2>/dev/null | sort -u)"

# The whole-repository TypeScript check and the 1,500-file unit suite are heavy; four lanes running them at once exhaust the
# machine's open-file limit and time out (k1, 2026-10-07). They take turns under one fleet-wide lock, with a raised file limit.
ulimit -n 65536 2>/dev/null || ulimit -n 10240 2>/dev/null || true
heavy_lock() {   # heavy_lock <command...> — run under $KY_ROOT/run/precheck_heavy.lock (waits up to 40 min for the lane ahead)
  "$PYV" - "$KY_ROOT/run/precheck_heavy.lock" "$@" <<'PYEOF'
import fcntl, subprocess, sys, time
lock = open(sys.argv[1], "a+"); deadline = time.time() + 2400
while True:
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); break
    except BlockingIOError:
        if time.time() > deadline: print("precheck: another lane held the heavy-step lock for 40 minutes", file=sys.stderr); sys.exit(75)
        time.sleep(15)
sys.exit(subprocess.call(sys.argv[2:]))
PYEOF
}
step "1/9 TypeScript (platform src; platform-mcp)"
# Match ci.yml's required "TypeScript (src only)" job: declaration and test-only
# diagnostics are outside that job's gate. Capture tsc's output before filtering
# so a test-only error does not turn this local approximation red.
TSC_OUT="$(heavy_lock bash -c 'cd platform && npx tsc --noEmit --skipLibCheck' 2>&1)" || true
TSC_NON_TEST="$(printf '%s\n' "$TSC_OUT" | grep 'error TS' | grep -Ev '(tests/|__tests__/)' || true)"
if [ -n "$TSC_NON_TEST" ]; then printf '%s\n' "$TSC_NON_TEST"; fail "tsc platform src"; else ok "tsc platform src"; fi
heavy_lock bash -c 'cd platform-mcp && npx tsc --noEmit' && ok "tsc platform-mcp" || fail "tsc platform-mcp"

step "2/9 Unit tests + migration number guard"
( cd platform && npm run -s guard:migration-numbers ) && ok "migration numbers" || fail "migration number guard"
heavy_lock bash -c 'cd platform && npx vitest run --reporter=dot --maxWorkers=4' && ok "vitest" || fail "vitest"

step "3/9 Secret scan (CI semantics: the bash rule set over every file git would carry; CI has no gitleaks)"
# gitleaks over the whole repository reports pre-existing findings CI never sees, so the project scan runs here on a PATH without it;
# gitleaks then runs on THIS DIFF'S files only, which is stricter than CI for the change at hand.
CI_PATH=/usr/bin:/bin:/usr/sbin:/sbin
env PATH=$CI_PATH bash platform/scripts/governance/secret_scan.sh --self-test >/dev/null && env PATH=$CI_PATH bash platform/scripts/governance/secret_scan.sh >/dev/null && ok "secret scan (CI path)" || fail "secret scan (CI path)"
if command -v gitleaks >/dev/null 2>&1 && [ -n "$CHANGED" ]; then
  GL="$(mktemp -d)"; while IFS= read -r f; do [ -f "$f" ] && mkdir -p "$GL/$(dirname "$f")" && cp "$f" "$GL/$f"; done <<< "$CHANGED"
  gitleaks detect --no-git --redact --no-banner -s "$GL" >/dev/null 2>&1 && ok "gitleaks on the diff's files" || fail "gitleaks flags a file in this diff (run: gitleaks detect --no-git --redact -s <file>)"; rm -rf "$GL"
fi

step "4/9 Governance baselines (CI semantics: exit 0 or 3, count within ceiling)"
baseline_gate() {  # name ceiling sed-pattern
  local name="$1" ceiling="$2" pattern="$3" output rc=0 count
  output="$(python3 "platform/scripts/governance/$name.py" 2>&1)" || rc=$?
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 3 ]; then fail "$name exit=$rc (CI accepts 0 or 3)"; return; fi
  count="$(printf '%s\n' "$output" | sed -n "$pattern" | tail -1)"
  if [[ ! "$count" =~ ^[0-9]+$ ]]; then fail "$name count unreadable (CI refuses an unreadable gate)"; return; fi
  if [ "$count" -gt "$ceiling" ]; then fail "$name $count exceeds the CI baseline ceiling $ceiling"; else ok "$name $count ≤ $ceiling"; fi
}
baseline_gate drift_detector 79 's/^drift_detector: \([0-9]*\) findings.*/\1/p'
baseline_gate schema_validator 43 's/^schema_validator: \([0-9]*\) violations.*/\1/p'
python3 platform/scripts/governance/check_fact_category_pinning.py >/dev/null 2>&1 && ok "fact-category-pin lint" || fail "fact-category-pin lint"

step "5/9 TAP-6 method-audit grep set"
( cd platform && npm run -s tap:6-method-grep ) && ok "TAP-6" || fail "TAP-6"

step "6/9 Governance tool tests — only what this diff can affect (CI runs the whole suite in five shards; locally it takes over half an hour)"
GOVCH="$(echo "$CHANGED" | grep -E '^platform/scripts/governance/' || true)"
if [ -z "$GOVCH" ]; then ok "not affected by this diff (no change under platform/scripts/governance/)"
else
  if [ -z "$(echo "$GOVCH" | grep -vE '^platform/scripts/governance/pravaha_tracker/')" ]; then GOVT="scripts/governance/pravaha_tracker/tests"; else GOVT="scripts/governance"; fi
  ( cd platform && env -u KY_BUILDER_DATABASE_URL -u KY_OWNER_DATABASE_URL DATABASE_URL='' PGHOST='' "$PYV" -m pytest -q "$GOVT" 2>/dev/null ) && ok "governance pytest ($GOVT)" || fail "governance pytest ($GOVT)"
fi

step "7/9 The item's explicit tests (run/tests/<ITEM>.txt or TESTS env; paths relative to repo root)"
ADMIN_DSN="postgresql://postgres:postgres@127.0.0.1:${KY_PG_PORT:-55433}/postgres"   # the lane rehearsal server: throwaway databases only
MANIFEST="${TESTS:-}"; [ -z "$MANIFEST" ] && [ -n "${KY_ITEM:-}" ] && [ -f "$KY_ROOT/run/tests/$KY_ITEM.txt" ] && MANIFEST="$(cat "$KY_ROOT/run/tests/$KY_ITEM.txt")"
if [ -n "$MANIFEST" ]; then
  while IFS= read -r t; do [ -z "$t" ] && continue
    case "$t" in platform/scripts/governance/*.py|platform/scripts/governance/*::*) ( cd platform && env -u DATABASE_URL "$PYV" -m pytest -q -rs "${t#platform/}" ) && ok "pytest $t" || fail "pytest $t" ;;
                 *.py|*::*) ( cd platform/python-sidecar && env -u DATABASE_URL KALA_ADMIN_DSN="$ADMIN_DSN" KALA_REQUIRE_DB=1 GOCHARA_A53_ADMIN_DSN="$ADMIN_DSN" SE_EPHE_PATH="${SE_EPHE_PATH:-$KY_ROOT/ephe}" "$PYV" -m pytest -q -rs "$ROOT/$t" ) && ok "pytest $t" || fail "pytest $t" ;;
                 *.test.ts|*.spec.ts) ( cd platform && npx vitest run "$t" ) && ok "vitest $t" || fail "vitest $t" ;;
                 *) fail "unknown test path type: $t" ;; esac
  done <<< "$MANIFEST"
else
  if echo "$CHANGED" | grep -qE '\.(py|ts|tsx|sql|sh)$|^\.github/workflows/'; then fail "this diff changes code but there is no explicit test manifest — export KY_ITEM=<item id> (with run/tests/<ITEM>.txt) or TESTS"
  else echo "   • no code change and no test manifest"; fi
fi

step "8/9 Migrations in the diff → applied to this lane's database through the project's runner"
if echo "$CHANGED" | grep -qE '^platform/(supabase/)?migrations/.*\.sql$'; then
  if [ -n "$LANE" ]; then
    URL="postgresql://postgres:postgres@127.0.0.1:55433/ky_$LANE"
    ( cd platform && DATABASE_URL="$URL" npx tsx scripts/migrate.ts ) > "$KY_ROOT/run/precheck_migrate_${LANE}.log" 2>&1 && ok "migrate.ts applied pending migrations to ky_$LANE" || fail "migrate.ts failed on ky_$LANE (see run/precheck_migrate_${LANE}.log)"
  else fail "migration in diff but KY_LANE unset — cannot apply to a lane database"; fi
else ok "no migration in diff"; fi

step "9/9 Hygiene"
WF='\.github/workflows/.*|'; [ "${KY_ITEM:-}" = "K0a-0" ] && WF=''   # K0a-0 is the one item that adds the campaign's CI job
echo "$CHANGED" | grep -qE '^(CLAUDECODE_BRIEF\.md|CLAUDE\.md|\.codex/.*|'"$WF"'platform/src/lib/retrieval/registry/knowledge/.*|platform/src/lib/purna/.*|00_ARCHITECTURE/briefs/(nirmana|suvarna|sampurti|purna_anvesana)/.*|platform/python-sidecar/pipeline/orchestrator/(asset_runner|runner|staleness)\.py|platform/python-sidecar/pipeline/orchestrator/writers/__init__\.py)$' \
  && fail "diff touches a frozen or forbidden path" || ok "no frozen/forbidden paths"
git diff --cached --name-only | grep -qE '\.(env|pem|key)$|pgenv' && fail "credential-like file staged" || ok "no credential-like files staged"
if echo "$CHANGED" | grep -qE 'pipeline/orchestrator/writers/ka_.*\.py'; then echo "$CHANGED" | grep -q 'nirmana-writer-digests.json' && ok "writer digest regenerated with the writer change" || fail "writer changed but nirmana-writer-digests.json not regenerated (CI provenance check)"; fi

echo; if [ $FAIL -eq 0 ]; then echo "PRECHECK GREEN (local; CI and verdict still required)"; else echo "PRECHECK RED — do not push"; fi
exit $FAIL
