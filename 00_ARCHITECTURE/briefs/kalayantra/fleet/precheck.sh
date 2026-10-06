#!/usr/bin/env bash
# KĀLA-YANTRA local pre-check — run from a lane worktree root BEFORE pushing. Mirrors the six required checks of
# ruleset 20141220 (TypeScript src-only · Unit Tests · Secret Scan · Governance Gates · TAP-6 · Governance Tool Tests)
# as closely as a laptop can, plus the py-sidecar tests for the packages the diff touches. Red here = do not push.
#
# B-3 ALIGNMENT (SŪTRADHĀRA): compare every step below with the corresponding job's `run:` lines in
# .github/workflows/ci.yml and tap-ci.yml at origin/main and correct this file; record the alignment in the ledger.
# The Governance Gates job also runs ~20 real-Postgres migration-contract tests that need provisioned databases; those
# run only in CI (or against ky_<lane> when a lane's diff touches a migration — see step 7).
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
FAIL=0; step() { echo; echo "── $1"; }; fail() { echo "   ✗ $1"; FAIL=1; }; ok() { echo "   ✓ $1"; }
CHANGED="$(git diff --name-only origin/main...HEAD 2>/dev/null; git diff --name-only; git diff --name-only --cached)"

step "1/8 TypeScript (src only) — platform"
( cd platform && npx tsc --noEmit -p tsconfig.json ) && ok "tsc platform" || fail "tsc platform"

step "2/8 TypeScript — platform-mcp"
( cd platform-mcp && npx tsc --noEmit ) && ok "tsc platform-mcp" || fail "tsc platform-mcp"

step "3/8 Unit tests (vitest) + migration number guard"
( cd platform && npm run -s guard:migration-numbers ) && ok "migration numbers" || fail "migration number guard"
( cd platform && npx vitest run --reporter=dot ) && ok "vitest" || fail "vitest"

step "4/8 Secret scan (self-test + tree)"
bash platform/scripts/governance/secret_scan.sh --self-test >/dev/null && bash platform/scripts/governance/secret_scan.sh && ok "secret scan" || fail "secret scan"

step "5/8 Governance gates (drift / schema / native-literal) — static part"
python3 platform/scripts/governance/drift_detector.py >/dev/null 2>&1 && ok "drift_detector" || fail "drift_detector (run it directly to see why)"
python3 platform/scripts/governance/schema_validator.py --repo-root "$ROOT" >/dev/null 2>&1 && ok "schema_validator" || fail "schema_validator"
python3 platform/scripts/governance/check_fact_category_pinning.py >/dev/null 2>&1 && ok "fact-category-pin lint" || fail "fact-category-pin lint"

step "6/8 TAP-6 method-audit grep set"
( cd platform && npm run -s tap:6-method-grep ) && ok "TAP-6" || fail "TAP-6"

step "7/8 Governance tool tests (pytest, governance scripts) + py-sidecar tests for touched packages"
( cd platform && python-sidecar/venv/bin/python -m pytest -q scripts/governance 2>/dev/null ) && ok "governance pytest" || fail "governance pytest"
PKGS="$(echo "$CHANGED" | grep -oE 'platform/python-sidecar/(services/[^/]+|pipeline/orchestrator/writers|ga_writers|brahmagyan)' | sort -u)"
if [ -n "$PKGS" ]; then
  for p in $PKGS; do
    t="$(echo "$p" | sed 's#platform/python-sidecar/##')"
    ( cd platform/python-sidecar && venv/bin/python -m pytest -q "tests" -k "$(basename "$t")" --maxfail=1 2>/dev/null ) && ok "pytest -k $(basename "$t")" || fail "pytest -k $(basename "$t")"
  done
else ok "no py-sidecar package touched"; fi
if echo "$CHANGED" | grep -q 'supabase/migrations/.*\.sql$'; then
  echo "   • migration(s) in diff: apply them to your ky_<lane> database before pushing (fleet/local_db.sh db <lane>) and attach the psql output to the PR"
fi

step "8/8 Hygiene"
echo "$CHANGED" | grep -qE '^(CLAUDECODE_BRIEF\.md|\.codex/|00_ARCHITECTURE/briefs/(nirmana|suvarna|sampurti|purna_anvesana)/)' && fail "diff touches a forbidden path (another campaign's files or the root brief)" || ok "no forbidden paths"
git diff --cached --name-only | grep -qE '\.(env|pem|key)$' && fail "credential-like file staged" || ok "no credential-like files staged"

echo; if [ $FAIL -eq 0 ]; then echo "PRECHECK GREEN"; else echo "PRECHECK RED — do not push"; fi
exit $FAIL
