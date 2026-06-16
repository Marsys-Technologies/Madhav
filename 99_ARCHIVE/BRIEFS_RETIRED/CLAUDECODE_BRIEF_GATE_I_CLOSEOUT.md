---
brief_id: GATE-I-CLOSEOUT-R1
version: 1.0
status: ACTIVE
authored_by: Claude Opus 4.7 (Gate I Design / Closeout Round 1) — 2026-05-12
purpose: >
  Close every pending / open item from the Gate I — Performance Command
  Center executor session of 2026-05-12, so the feature/gate1-perf-command-center
  branch is fully merge-ready for the Gate IV intake. This brief is a
  paste-ready prompt for a Claude Code Sonnet 4.6 session in VS Code
  Antigravity (--dangerously-skip-permissions), working in the worktree at
  /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center.
executor: Claude Code Sonnet 4.6 (Anti-Gravity, VS Code)
working_directory: /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
branch: feature/gate1-perf-command-center (do NOT touch main)
inputs:
  - 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_I_v1_0.md  (original brief, status COMPLETE)
  - GATE_I_AUDIT.md                                          (W0 audit from prior session)
  - 00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md     (master plan)
  - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md    (§H session-close)
  - 00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md         (§F known_residuals)
outputs:
  - CLOSEOUT_PREFLIGHT.md
  - GATE_I_KNOWN_RESIDUALS.md (under 00_ARCHITECTURE/known_residuals/)
  - SESSION_LOG.md (appended entry)
---

# Gate I — Closeout Round 1 — Paste-Ready Prompt

Copy the block below verbatim into the Claude Code Sonnet 4.6 session pointed at the worktree
`/Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center`. The block is self-contained — every
command the executor needs is embedded; no separate terminal steps required from the native.

---

You are Claude Code Sonnet 4.6 running in VS Code Antigravity with `--dangerously-skip-permissions`. Your job is to finalize Gate I — Performance Command Center — by closing every pending and open item from the 2026-05-12 executor session, so this branch (`feature/gate1-perf-command-center`) is fully merge-ready for the Gate IV intake. The original Gate I brief is COMPLETE; this is the closeout round to discharge what the prior session correctly flagged as deferred (live DB verification, SESSION_LOG append, pre-existing test-failure audit, golden-set reconciliation, rebase onto current main).

**Working directory (non-negotiable):**
```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
```

You are on branch `feature/gate1-perf-command-center`. Do **not** touch `main`. Do **not** merge.

---

## Mandatory reading (in order, before any work)

1. `CLAUDE.md` (worktree root) — orientation, mandatory-reading sequence, B.10 / B.11 / B.10 fail-closed discipline
2. `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_I_v1_0.md` — the original Gate I brief (status COMPLETE). Re-read §4 ACs and §9 close checklist.
3. `GATE_I_AUDIT.md` (worktree root) — your prior W0 audit. Load-bearing for downstream paths.
4. `00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md` §3.7, §3.8, §9, §10
5. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` §H (session-close requirements) and §K (disagreement protocol if a finding warrants escalation)
6. `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` and `SESSION_CLOSE_TEMPLATE_v1_0.md`
7. `00_ARCHITECTURE/SESSION_LOG.md` — read the **last 5 entries** to learn the project's actual append style (the template is the schema; the last entries are the live pattern)
8. `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` §F (known_residuals whitelist policy + CI exit-code-3 contract)
9. Locate `schema_validator.py` — search with: `find . -name "schema_validator.py" -not -path "*/node_modules/*" -not -path "*/.next/*" 2>/dev/null`

Do not start W1 until all 9 are read.

---

## Session-open handshake

Per `CLAUDE.md §G`, emit a SESSION_OPEN block at the top of your first substantive response. Proposed Cowork thread name: **`MARSYS Gate I — Close-Out Round 1`**. Validate against `SESSION_OPEN_TEMPLATE_v1_0.md`. Declare `may_touch` / `must_not_touch` per below. Halt if validation fails.

**may_touch (closeout scope):**
- `CLOSEOUT_PREFLIGHT.md` (worktree root)
- `00_ARCHITECTURE/known_residuals/GATE_I_KNOWN_RESIDUALS.md` (new)
- `00_ARCHITECTURE/SESSION_LOG.md` (append only)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (only if §2's last_session_id field needs updating — match the project pattern)
- Any file inside the original Gate I `may_touch` list IF and ONLY IF a Gate I test regression surfaces post-rebase and must be fixed

**must_not_touch:**
- `main` branch directly
- `components/trace/**`, `components/consume/**`
- `components/shared/AppShellRail.tsx`, `components/shared/MobileNavSheet.tsx`
- `app/api/chat/consume/route.ts`
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `06_LEARNING_LAYER/**`
- The planner / synthesis golden set file(s) — W7 is research-only
- Any test file in `known_residuals` — those are not Gate I's responsibility

---

## Pre-flight environment check

Run all commands below and append output to a new file `CLOSEOUT_PREFLIGHT.md` at the worktree root. Do **not** delete this file when done.

```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
git status
git log --oneline -20
git fetch origin
git log --oneline HEAD..origin/main | head -30
git diff --name-only main..HEAD
ls platform/migrations/ | tail -10
echo "---ENV---"
echo "DATABASE_URL=${DATABASE_URL:+SET (length=${#DATABASE_URL})}"
echo "DATABASE_URL=${DATABASE_URL:-NOT_SET}"
which psql || echo "psql not found"
echo "---PROXY---"
ps aux | grep -i cloud-sql-proxy | grep -v grep || echo "cloud-sql-proxy not running"
echo "---NODE---"
cd platform && node -v && npm -v
```

Then:
- **If `DATABASE_URL` is set AND `psql "$DATABASE_URL" -c '\dt'` succeeds** → DB is available; proceed to W1 full live-verify path.
- **If DB is NOT available** → do not proceed past W2 dry runs. Halt and report to the native with the exact command(s) they need (start the Cloud SQL Auth Proxy, export `DATABASE_URL`, etc.). Do not fake any AC tick that requires a live DB.

---

## Work items

### W1 — Apply migrations 043 + 044 to live DB

```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
psql "$DATABASE_URL" -f platform/migrations/043_performance_schema.sql
psql "$DATABASE_URL" -f platform/migrations/044_eval_runs_and_judge.sql
psql "$DATABASE_URL" -c '\d performance_queries'
psql "$DATABASE_URL" -c '\d eval_runs'
psql "$DATABASE_URL" -c '\d performance_judge_verdict'
```

Confirm:
- Each migration applies without error.
- The 044 `ALTER TABLE performance_queries ADD CONSTRAINT performance_queries_eval_run_fk` succeeds.
- All CHECK constraints accept the documented values.

Append the full `\d` output to `CLOSEOUT_PREFLIGHT.md` § "W1".

### W2 — Smoke W2/W3 ingestion writers

Start the dev server in the background:
```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center/platform
nohup npm run dev > ../dev_server.log 2>&1 &
echo $! > ../dev_server.pid
sleep 8
tail -50 ../dev_server.log
```

Hit the consume API with a minimal synthetic query (read `app/api/chat/consume/route.ts` first — read-only — to learn the request shape; do not modify). Confirm:
- One row appears in `performance_queries` with `source='consume'`, `plan_accuracy_label='unjudged'`, all required fields populated
- Consume response returns 200

```
psql "$DATABASE_URL" -c "SELECT id, source, query_class, plan_type, latency_total_ms, plan_accuracy_label, b10_violation, b11_violation FROM performance_queries ORDER BY created_at DESC LIMIT 5;"
```

Eval auto-hook smoke — invoke the answer-eval script with a small sample (path per `GATE_I_AUDIT.md` W0.A; typical: `npx tsx platform/scripts/answer_eval.ts --limit=5` or similar — match what the actual script supports):
```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
# Adapt this command to the actual eval-script invocation discovered in W0.A
npx tsx platform/scripts/answer_eval.ts --limit=5 2>&1 | tee CLOSEOUT_EVAL_RUN.log
psql "$DATABASE_URL" -c "SELECT id, golden_set_version, query_count, plan_accuracy_recall, plan_accuracy_precision FROM eval_runs ORDER BY created_at DESC LIMIT 3;"
psql "$DATABASE_URL" -c "SELECT source, count(*) FROM performance_queries WHERE eval_run_id IS NOT NULL GROUP BY source;"
```

### W3 — Smoke W5/W6/W7 APIs

You will need a super-admin session cookie. Either:
- Use the test super-admin auth fixture from your W14 tests
- Or sign in via the dev server browser and copy the `__session` cookie

```
SUPER_ADMIN_COOKIE="__session=<value-from-browser-or-test-fixture>"

curl -s -H "Cookie: $SUPER_ADMIN_COOKIE" \
  "http://localhost:3000/api/performance/kpis?window_start=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ)&window_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)&source=all" | jq .

curl -s -H "Cookie: $SUPER_ADMIN_COOKIE" \
  "http://localhost:3000/api/performance/queries?page=1&page_size=20" | jq '.total, .rows[0]'

curl -s -H "Cookie: $SUPER_ADMIN_COOKIE" \
  "http://localhost:3000/api/performance/eval-runs?page=1" | jq .

LATEST_RUN_ID=$(psql "$DATABASE_URL" -tAc "SELECT id FROM eval_runs ORDER BY created_at DESC LIMIT 1")
curl -s -H "Cookie: $SUPER_ADMIN_COOKIE" \
  "http://localhost:3000/api/performance/eval-runs/$LATEST_RUN_ID" | jq .
```

Confirm all 4 bundle blocks present in `/kpis`, sparklines have 24 buckets, query log paginates, eval-runs detail returns metadata + summary.

### W4 — Smoke W8 judge endpoint

```
SUPER_ADMIN_COOKIE="__session=<value>"

# First run — should judge some rows
curl -s -X POST -H "Cookie: $SUPER_ADMIN_COOKIE" -H "Content-Type: application/json" \
  -d "{\"window_start\":\"$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ)\",\"window_end\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"limit\":10}" \
  http://localhost:3000/api/performance/judge | jq .

# Verify verdicts persisted
psql "$DATABASE_URL" -c "SELECT count(*) AS verdict_count FROM performance_judge_verdict;"
psql "$DATABASE_URL" -c "SELECT plan_accuracy_label, count(*) FROM performance_queries WHERE source='consume' GROUP BY plan_accuracy_label;"

# Idempotency — re-run same window; judged_count should reflect only newly-unjudged rows
curl -s -X POST -H "Cookie: $SUPER_ADMIN_COOKIE" -H "Content-Type: application/json" \
  -d "{\"window_start\":\"$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ)\",\"window_end\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"limit\":10}" \
  http://localhost:3000/api/performance/judge | jq .

# Concurrency — advisory lock 409 path
(
  curl -s -X POST -H "Cookie: $SUPER_ADMIN_COOKIE" -H "Content-Type: application/json" \
    -d "{\"window_start\":\"$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ)\",\"window_end\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"limit\":200}" \
    http://localhost:3000/api/performance/judge > judge_a.out &
  curl -s -X POST -H "Cookie: $SUPER_ADMIN_COOKIE" -H "Content-Type: application/json" \
    -d "{\"window_start\":\"$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ)\",\"window_end\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"limit\":200}" \
    http://localhost:3000/api/performance/judge > judge_b.out &
  wait
)
echo "--- judge_a ---"; cat judge_a.out
echo "--- judge_b ---"; cat judge_b.out
# Exactly one of the two should be HTTP 409 with body {"error":"judge_run_in_progress"}
```

### W5 — Smoke W9–W11 UI

Open `http://localhost:3000/performance` in a browser. Manually verify:
- 4 KPI tiles render with values (or "—" if window has no data)
- Sparklines render
- Time-window picker preset chips switch the data
- Custom date-range picker works
- Query log filter chips work; pagination works
- "Run plan-accuracy judge" affordance opens modal; submit triggers POST; toast on completion
- Click a row → TracePanel opens (or documented fallback to `/audit/[id]`)

Then `/performance/eval-runs` (list view) and `/performance/eval-runs/[id]` (detail view) — both should render.

Document any UI gap in `CLOSEOUT_PREFLIGHT.md` § "W5 — UI smoke results". Screenshots optional — save to `closeout_screenshots/` if your tooling captures them; otherwise prose description per page is sufficient.

### W6 — Pre-existing test-failure audit

```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center/platform
npm test 2>&1 | tee ../npm_test_full.log
echo "exit_code=$?"

# Verify pre-existing vs Gate I regression
cd ..
git stash -u
cd platform
npm test 2>&1 | tee ../npm_test_stashed.log
echo "exit_code=$?"
cd ..
git stash pop

# Diff the failure sets
diff <(grep -E "FAIL" npm_test_full.log | sort -u) <(grep -E "FAIL" npm_test_stashed.log | sort -u)
```

Categorize:
- **(a) Pre-existing on this base** — fails identically with Gate I changes stashed → not a Gate I regression
- **(b) Gate I regression** — fails only with Gate I changes applied → must fix

For category (a), create `00_ARCHITECTURE/known_residuals/GATE_I_KNOWN_RESIDUALS.md` with one line per failing test file:
```
- <relative path to test file> — <one-line suspected cause> — <linked existing issue or "untriaged">
```
Match the format `ONGOING_HYGIENE_POLICIES §F` documents for the CI exit-code-3 whitelist. If §F prescribes a stricter schema (frontmatter, status field, etc.), follow it exactly.

For category (b), fix before proceeding. Do not append to known_residuals to silence Gate I failures.

### W7 — Golden-set count reconciliation

```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
find . -path ./node_modules -prune -o -type f \( -name "planner_golden_set*.json" -o -name "synthesis_golden_set*.json" -o -name "*golden*.json" \) -print 2>/dev/null
```

For each found file: count entries (`jq 'length'` or `jq '.queries | length'` etc. depending on shape) and capture path + count.

Cross-reference:
- `GATE_I_AUDIT.md` W0 findings (your prior audit: 15 synthesis + 29 planner)
- Any `PIPELINE_GAP_PLAN_v1_0.md` or equivalent governance doc claiming v1.2 = 46 entries (`grep -r "46 entries" 00_ARCHITECTURE/ platform/`)
- The `eval_runs.golden_set_version` field's value from the actual eval row created in W2

Determine which is true. Append a 5–10 line "Golden Set Reconciliation Note" to `CLOSEOUT_PREFLIGHT.md` § "W7" with finding + recommendation for the native. **Do not modify the golden set itself.** Reconciliation is research-only here.

### W8 — Rebase onto current main

```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
git fetch origin
git log --oneline HEAD..origin/main | head -30
git rebase origin/main
```

If conflicts arise:
- In Gate I `may_touch` files: resolve, ensuring Gate I tests still pass after resolution
- Outside Gate I `may_touch`: halt and report — those are not Gate I's responsibility

After rebase:
```
cd platform
npm test -- src/lib/performance/ src/app/api/performance/ src/components/performance/ 2>&1 | tee ../post_rebase_gate1_tests.log
npx tsc --noEmit 2>&1 | tee ../post_rebase_tsc.log
npx eslint src/lib/performance src/app/api/performance src/components/performance src/app/performance 2>&1 | tee ../post_rebase_eslint.log
```

All Gate I tests must remain green; tsc and eslint clean on the Gate I surface.

### W9 — Model-registry comment audit

```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
grep -rn "gemini-2.0-flash-lite" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.md" .
```

Every occurrence must be either:
- (a) In a comment explaining the swap to `gemini-2.5-flash-lite`, or
- (b) Already replaced with the live model id

If any unmarked occurrence remains, fix it (preserve the comment trail per the prior session's pattern).

### W10 — Append SESSION_LOG entry

Read the last 5 entries of `00_ARCHITECTURE/SESSION_LOG.md` to anchor the project's actual append style (the template is the schema; the live entries are the pattern).

Author **one well-formed entry** for this closeout session, appended atomically. Match the template's required fields:
- `session_id` (suggestion: `gate1-closeout-r1-2026-05-12`)
- Date range
- Work items completed (closeout W1–W10)
- AC pass/fail (the CA.1–CA.15 checklist below)
- Scope-respect verification (`git diff --name-only main..HEAD` summary)
- Test counts
- Deviations from this prompt with justification
- Known_residuals reference (link to `GATE_I_KNOWN_RESIDUALS.md`)
- `mirror_updates_propagated`: likely empty (Gate I has no Gemini-side counterpart)
- `red_team_due`: 0 (counter reset at M4 close per `CURRENT_STATE_v1_0.md`)

Validate:
```
SCHEMA_VALIDATOR=$(find . -name "schema_validator.py" -not -path "*/node_modules/*" 2>/dev/null | head -1)
if [ -n "$SCHEMA_VALIDATOR" ]; then
  python3 "$SCHEMA_VALIDATOR" --target 00_ARCHITECTURE/SESSION_LOG.md
else
  echo "schema_validator.py not found — document this in CLOSEOUT_PREFLIGHT.md and fall back to manual schema review against SESSION_CLOSE_TEMPLATE_v1_0.md"
fi
```

The append is atomic: only commit after validation passes. Per `CLAUDE.md §H`: "A session whose close-checklist fails validation does not claim close."

### W11 — CURRENT_STATE update (conditional)

Read `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2. If the project pattern requires per-session updates of `last_session_id` / `next_session`, update accordingly. If not (recent sessions don't show per-session updates), leave alone and document the decision in `CLOSEOUT_PREFLIGHT.md`.

### W12 — Commit + branch state

Stage the closeout outputs and commit:
```
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
git add CLOSEOUT_PREFLIGHT.md \
        00_ARCHITECTURE/known_residuals/GATE_I_KNOWN_RESIDUALS.md \
        00_ARCHITECTURE/SESSION_LOG.md
# Add CURRENT_STATE_v1_0.md only if W11 modified it
git status
git commit -m "Gate I closeout R1: live verify + SESSION_LOG + known_residuals + rebase"

git log --oneline -5
git diff --name-only main..HEAD | sort
```

Branch must end clean (no uncommitted changes), all closeout outputs committed.

---

## Closeout acceptance criteria

All must pass before reporting back. One-line evidence per each in the final report.

- [ ] CA.1  Migrations 043 + 044 applied on live DB; `\d` output captured in `CLOSEOUT_PREFLIGHT.md` § W1
- [ ] CA.2  Consume ingestion smoke produced a `performance_queries` row with all required fields populated
- [ ] CA.3  Eval auto-hook smoke produced one `eval_runs` row + N `performance_queries` with `source='eval'`
- [ ] CA.4  `/api/performance/kpis` returns all 4 bundle blocks on a populated window
- [ ] CA.5  `/api/performance/queries` pagination + filters work
- [ ] CA.6  `/api/performance/eval-runs` and `/eval-runs/[id]` return correct data
- [ ] CA.7  `/api/performance/judge`: first run `judged_count > 0`; rerun idempotent; concurrent run returns 409
- [ ] CA.8  `/performance` landing + `/eval-runs` pages render; row click opens TracePanel (or documented fallback)
- [ ] CA.9  `npm test` categorized: 0 Gate I regressions; pre-existing residuals documented in `GATE_I_KNOWN_RESIDUALS.md` per `ONGOING_HYGIENE_POLICIES §F`
- [ ] CA.10 Golden-set reconciliation note authored in `CLOSEOUT_PREFLIGHT.md` § W7
- [ ] CA.11 Rebase onto `origin/main` clean; post-rebase Gate I tests green; tsc + eslint clean on Gate I surface
- [ ] CA.12 `grep gemini-2.0-flash-lite` returns zero unmarked occurrences
- [ ] CA.13 SESSION_LOG entry appended; schema validated (or fallback manual review documented)
- [ ] CA.14 `git diff --name-only main..HEAD` respects `may_touch` — zero scope violations
- [ ] CA.15 Branch clean (no uncommitted changes); all closeout outputs committed; ready for Gate IV intake

---

## DO NOT

- Merge to `main`.
- Touch `main` directly.
- Modify `components/trace/**`, `components/consume/**`, `components/shared/AppShellRail.tsx`, `components/shared/MobileNavSheet.tsx`, or `app/api/chat/consume/route.ts`.
- Modify the golden set file (W7 is research-only).
- Install new npm packages.
- Use Anthropic models for any code path.
- Append a Gate I test regression to `known_residuals` to silence it — those must be fixed.
- Fake any AC tick that requires live DB if the DB isn't reachable. Halt and report instead.

---

## Report format (final response back to the native)

1. **CA.1–CA.15** with PASS / FAIL and one-line evidence per each
2. **Files touched in this closeout** — output of `git diff --name-only <closeout-base>..HEAD`
3. **Deviations from this prompt** with justification (if any)
4. **Anything the native must do manually** before Gate IV intake (e.g. "run the proxy", "merge sequence per OPUS_PLANNING_SESSION §9")

GO.

---

*End of CLAUDECODE_BRIEF_GATE_I_CLOSEOUT.md — paste-ready prompt above. The prompt is the deliverable; this file is your stable reference copy.*
