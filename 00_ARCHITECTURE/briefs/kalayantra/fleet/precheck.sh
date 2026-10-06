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

step "1/9 TypeScript (platform src; platform-mcp)"
( cd platform && npx tsc --noEmit -p tsconfig.json ) && ok "tsc platform" || fail "tsc platform"
( cd platform-mcp && npx tsc --noEmit ) && ok "tsc platform-mcp" || fail "tsc platform-mcp"

step "2/9 Unit tests + migration number guard"
( cd platform && npm run -s guard:migration-numbers ) && ok "migration numbers" || fail "migration number guard"
( cd platform && npx vitest run --reporter=dot ) && ok "vitest" || fail "vitest"

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

step "6/9 Governance tool tests (scrubbed environment, as CI runs them)"
( cd platform && env -u KY_BUILDER_DATABASE_URL -u KY_OWNER_DATABASE_URL DATABASE_URL='' PGHOST='' "$PYV" -m pytest -q scripts/governance 2>/dev/null ) && ok "governance pytest" || fail "governance pytest"

step "7/9 The item's explicit tests (run/tests/<ITEM>.txt or TESTS env; paths relative to repo root)"
ADMIN_DSN="postgresql://postgres:postgres@127.0.0.1:${KY_PG_PORT:-55433}/postgres"   # the lane rehearsal server: throwaway databases only
MANIFEST="${TESTS:-}"; [ -z "$MANIFEST" ] && [ -n "${KY_ITEM:-}" ] && [ -f "$KY_ROOT/run/tests/$KY_ITEM.txt" ] && MANIFEST="$(cat "$KY_ROOT/run/tests/$KY_ITEM.txt")"
if [ -n "$MANIFEST" ]; then
  while IFS= read -r t; do [ -z "$t" ] && continue
    case "$t" in *.py|*::*) ( cd platform/python-sidecar && env -u DATABASE_URL KALA_ADMIN_DSN="$ADMIN_DSN" KALA_REQUIRE_DB=1 GOCHARA_A53_ADMIN_DSN="$ADMIN_DSN" SE_EPHE_PATH="${SE_EPHE_PATH:-$KY_ROOT/ephe}" "$PYV" -m pytest -q -rs "$ROOT/$t" ) && ok "pytest $t" || fail "pytest $t" ;;
                 *.test.ts|*.spec.ts) ( cd platform && npx vitest run "$t" ) && ok "vitest $t" || fail "vitest $t" ;;
                 *) fail "unknown test path type: $t" ;; esac
  done <<< "$MANIFEST"
else echo "   • no explicit test manifest for this item — PARĪKṢAKA will treat that as a finding for a code item"; fi

step "8/9 Migrations in the diff → applied to this lane's database through the project's runner"
if echo "$CHANGED" | grep -qE '^platform/(supabase/)?migrations/.*\.sql$'; then
  if [ -n "$LANE" ]; then
    URL="postgresql://postgres:postgres@127.0.0.1:55433/ky_$LANE"
    ( cd platform && DATABASE_URL="$URL" npx tsx scripts/migrate.ts ) > "$KY_ROOT/run/precheck_migrate_${LANE}.log" 2>&1 && ok "migrate.ts applied pending migrations to ky_$LANE" || fail "migrate.ts failed on ky_$LANE (see run/precheck_migrate_${LANE}.log)"
  else fail "migration in diff but KY_LANE unset — cannot apply to a lane database"; fi
else ok "no migration in diff"; fi

step "9/9 Hygiene"
WF='\.github/workflows/|'; [ "${KY_ITEM:-}" = "K0a-0" ] && WF=''   # K0a-0 is the one item that adds the campaign's CI job
echo "$CHANGED" | grep -qE '^(CLAUDECODE_BRIEF\.md|CLAUDE\.md|\.codex/|'"$WF"'platform/src/lib/retrieval/registry/knowledge/|00_ARCHITECTURE/briefs/(nirmana|suvarna|sampurti|purna_anvesana)/|platform/python-sidecar/pipeline/orchestrator/(asset_runner|runner|staleness)\.py|platform/python-sidecar/pipeline/orchestrator/writers/__init__\.py)$' && fail "diff touches a frozen or forbidden path" || ok "no frozen/forbidden paths"
git diff --cached --name-only | grep -qE '\.(env|pem|key)$|pgenv' && fail "credential-like file staged" || ok "no credential-like files staged"
if echo "$CHANGED" | grep -qE 'pipeline/orchestrator/writers/ka_.*\.py'; then echo "$CHANGED" | grep -q 'nirmana-writer-digests.json' && ok "writer digest regenerated with the writer change" || fail "writer changed but nirmana-writer-digests.json not regenerated (CI provenance check)"; fi

echo; if [ $FAIL -eq 0 ]; then echo "PRECHECK GREEN (local; CI and verdict still required)"; else echo "PRECHECK RED — do not push"; fi
exit $FAIL
