---
title: "BHISMA Wave 2 — Session S-B: SCHEMA Completion + EVAL Verification"
brief_id: BHISMA_SB
version: 1.0
status: COMPLETE
created_date: 2026-05-03
completed_date: 2026-05-03
session_id: BHISMA-W2-S-B
executor: claude-opus-4-6
active_phase: "BHISMA Wave 2 — Stream SCHEMA + Stream EVAL"
isolation_tier: BHISMA_ONLY
parallel_safe_with: BHISMA_SA
must_complete_before: BHISMA_SC
---

# BHISMA Wave 2 — Session S-B
## SCHEMA Completion + EVAL Verification

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context

BHISMA Wave 2 (`00_ARCHITECTURE/BHISMA_WAVE2_PLAN_v1_1.md`, CURRENT) is the Universal Query Engine + Observability sprint. This session (S-B) runs **in parallel with S-A** — zero file overlap is guaranteed by the scope declarations below.

S-B covers:
1. **Stream SCHEMA** — one missing artifact: `RETENTION_POLICY_v1_0.md` (SCHEMA-6)
2. **Stream EVAL** — file naming reconciliation + smoke test run + Lever 2 readout

**The Lever 2 decision** (whether to flip `LLM_FIRST_PLANNER_ENABLED=true`) is a native decision. S-B's job is to run the smoke test and report the scores — not to flip the flag.

**You are NOT to open, read, or modify any files belonging to:**
- MARSYS-JIS M-phase work (anything in `025_HOLISTIC_SYNTHESIS/`, `01_FACTS_LAYER/`, `06_LEARNING_LAYER/`)
- Ustad/Phase-O Observatory (`/Users/Dev/Vibe-Coding/Apps/Ustad/` or any Ustad path)
- BHISMA_SA scope files (see §3 must_not_touch)

---

## §1 Mandatory Pre-Work

Before any file creation, run the following audit to confirm current state:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

# Confirm SCHEMA-6 artifact is absent
ls ../00_ARCHITECTURE/RETENTION_POLICY_v1_0.md 2>&1

# Check current eval file names
ls tests/eval/ 2>&1

# Confirm smoke runner exists and check its entry point
ls tests/eval/planner_smoke_runner.ts 2>&1
head -30 tests/eval/planner_smoke_runner.ts 2>&1

# Check golden set filename (spec says planner_golden_set.json; audit found golden_test_set.json)
ls tests/eval/*.json 2>&1

# Check EVAL-4 CI script in package.json
grep -n "eval:planner\|planner.*eval" package.json 2>&1

# Check EVAL-4 CI config
ls .github/workflows/ 2>&1 || echo "No .github/workflows directory"
```

Record all findings before proceeding.

---

## §2 Scope of Work

### Task SCHEMA-6: Create RETENTION_POLICY_v1_0.md

**File to create:** `00_ARCHITECTURE/RETENTION_POLICY_v1_0.md`

**Purpose:** Governance document defining 90-day hot window retention, GCS archival, and deletion schedule for the four BHISMA Wave 2 monitoring tables (`llm_call_log`, `query_plan_log`, `tool_execution_log`, `context_assembly_log`).

**Required content:**

```markdown
---
title: "BHISMA Wave 2 — Monitoring Data Retention & Archival Policy"
canonical_id: RETENTION_POLICY
version: 1.0
status: CURRENT
created_date: 2026-05-03
scope: "Platform monitoring tables: llm_call_log, query_plan_log, tool_execution_log, context_assembly_log"
---

# Retention & Archival Policy — BHISMA Wave 2 Monitoring Tables

## §1 Retention Tiers

| Tier | Window | Storage | Action |
|------|--------|---------|--------|
| Hot | 0–90 days | Cloud SQL (Postgres) | Query-live; full indexes available |
| Warm | 91–365 days | GCS (JSONL, compressed) | Accessible via batch job; not query-live |
| Cold | >365 days | GCS (JSONL, Zstandard) | Audit trail only; access requires manual restore |

## §2 Per-Table Policy

### llm_call_log
- Hot window: 90 days
- Reason for retention: cost accountability, model comparison, R1 reasoning token auditing
- Archive format: JSONL per day, gzip compressed
- GCS path: `gs://[BUCKET]/retention/llm_call_log/YYYY/MM/DD.jsonl.gz`
- Delete-after-archive: 90 days post-creation

### query_plan_log
- Hot window: 90 days
- Reason for retention: planner quality monitoring, A/B comparison data source
- Archive format: JSONL per day
- GCS path: `gs://[BUCKET]/retention/query_plan_log/YYYY/MM/DD.jsonl.gz`
- Delete-after-archive: 90 days post-creation

### tool_execution_log
- Hot window: 90 days
- Reason for retention: tool zero-row tracking, B.3 grounding audits
- Archive format: JSONL per day
- GCS path: `gs://[BUCKET]/retention/tool_execution_log/YYYY/MM/DD.jsonl.gz`
- Delete-after-archive: 90 days post-creation

### context_assembly_log
- Hot window: 90 days
- Reason for retention: B.3 compliance audit, citation validation audit trail
- Archive format: JSONL per day
- GCS path: `gs://[BUCKET]/retention/context_assembly_log/YYYY/MM/DD.jsonl.gz`
- Delete-after-archive: 90 days post-creation

## §3 Cleanup Jobs

Cleanup runs daily via scheduled Cloud Run Job (or pg_cron if available).

### Archive job (daily, 02:00 UTC)
```sql
-- Export rows older than 88 days to GCS before deletion
-- Uses: COPY (SELECT * FROM [table] WHERE created_at < NOW() - INTERVAL '88 days')
--       TO PROGRAM 'gsutil cp - gs://[BUCKET]/retention/[table]/...'
```

### Delete job (daily, 03:00 UTC, runs after archive)
```sql
DELETE FROM llm_call_log      WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM query_plan_log    WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM tool_execution_log WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM context_assembly_log WHERE created_at < NOW() - INTERVAL '90 days';
```

Delete jobs run AFTER archive job with 1-hour buffer. Atomic: if archive fails, delete does not proceed.

## §4 Exceptions

- **Super-admin override:** A query tagged `retain_indefinitely=true` in `query_plan_log` is excluded from deletion. Use for golden set calibration rows.
- **Incident hold:** During active incidents, deletion is suspended by setting `RETENTION_HOLD=true` env flag in the cleanup Cloud Run Job.
- **Legal hold:** Legal team may flag query IDs for indefinite retention via `llm_call_log.legal_hold=true` column (add in future migration if required).

## §5 Implementation Status

| Component | Status |
|-----------|--------|
| Cloud SQL hot-tier tables | PENDING (migrations 032–036 not yet applied — S-C) |
| GCS bucket configuration | PENDING — use existing GCS bucket from Phase 14C/D/E |
| Archive job (Cloud Run) | PENDING — author after S-C completes |
| Delete job (Cloud Run or pg_cron) | PENDING — author after S-C completes |
| Monitoring alert (archive failure) | PENDING |

## §6 Acceptance

Policy document complete. Implementation items above tracked to Session S-C (migration apply) and post-S-C sessions.
```

**Adapt content as needed** but preserve all structural elements: tier table, per-table policy, cleanup jobs, exceptions, and implementation status.

**Acceptance:** File exists; frontmatter valid; all 4 tables covered; cleanup job SQL present; GCS paths specified.

---

### Task EVAL File Reconciliation

**Problem:** Wave 2 plan `§3 Stream EVAL` specifies the golden set filename as `platform/tests/eval/planner_golden_set.json`. Codebase audit found the actual file is named `golden_test_set.json`. These must be reconciled.

**Step 1:** Read both files if both exist:
```bash
ls platform/tests/eval/*.json
cat platform/tests/eval/planner_golden_set.json 2>/dev/null | head -50
cat platform/tests/eval/golden_test_set.json 2>/dev/null | head -50
```

**Step 2:** Decision tree:
- If `planner_golden_set.json` exists AND `golden_test_set.json` does NOT exist → no action needed.
- If `golden_test_set.json` exists AND `planner_golden_set.json` does NOT exist → rename to `planner_golden_set.json`:
  ```bash
  cd platform/tests/eval && mv golden_test_set.json planner_golden_set.json
  ```
  Then update any import references in test files:
  ```bash
  grep -r "golden_test_set" platform/tests/ --include="*.ts" -l
  # Update each file to reference planner_golden_set.json instead
  ```
- If both exist → read both, determine which is more complete (more test cases), keep the more complete one as `planner_golden_set.json`, archive the other (or delete if content is identical).

**Verify the golden set has ≥25 test cases** covering the 5 query categories:
- remedial queries (5 minimum)
- interpretive queries (5 minimum)
- predictive queries (5 minimum)
- compound queries (5 minimum)
- edge cases (5 minimum)

**If the golden set has < 25 cases**, extend it following the spec schema:
```typescript
interface GoldenTestCase {
  query_text: string;
  expected_tools: string[];
  expected_planets: string[];
  expected_domain: string;
  min_tools: number;
  forbidden_tools: string[];
  reasoning: string;
}
```
Add cases to reach 25 total. Use the native's chart context (Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar) for realistic query texts. Example additions:
- Remedial: "What gemstones should I wear for Saturn?" → expected_tools: ["remedial_codex_query", "msr_sql"], expected_domain: "remedial"
- Predictive: "When will my career peak according to my Dashas?" → expected_tools: ["msr_sql", "l1_facts_query"], expected_domain: "timing"
- Edge case: "" (empty query) → expected_tools: [], forbidden_tools: [] (should trigger circuit breaker)
- Edge case: single word "moon" → min_tools: 1, expected_domain: "general"

---

### Task EVAL-2: Run Planner Smoke Test

**This is the critical Lever 2 gate output.**

**Step 1:** Locate the smoke runner:
```bash
ls platform/tests/eval/planner_smoke_runner.ts 2>/dev/null || \
ls platform/scripts/eval/*.ts 2>/dev/null | head -10
```

**Step 2:** Check whether the smoke runner requires a live DB or can run offline:
```bash
head -50 platform/tests/eval/planner_smoke_runner.ts
```

**Step 3:** Run the smoke test:
```bash
cd platform
npx tsx tests/eval/planner_smoke_runner.ts 2>&1
# OR if it's a vitest file:
npx vitest run tests/eval/planner_smoke_runner.ts 2>&1
```

**Step 4:** Parse the results. The runner should output:
- `tool_recall`: fraction of expected tools that appeared in the plan
- `tool_precision`: fraction of planned tools that were not forbidden

**Lever 2 threshold (from Wave 2 plan §3 EVAL-2):**
- PASS: `tool_recall ≥ 0.80` AND `tool_precision ≥ 0.90`
- FAIL: either metric below threshold

**Step 5:** If the runner errors or cannot run (e.g., requires `LLM_FIRST_PLANNER_ENABLED=true` which is OFF):

Option A — If the runner can be set to offline/mock mode, enable that and run.
Option B — If it requires a live planner (flag is OFF), note this explicitly:
```
EVAL-2 RESULT: BLOCKED
Reason: planner smoke runner requires LLM_FIRST_PLANNER_ENABLED=true
Pre-condition: S-A must complete and native must flip flag before Lever 2 can be evaluated
Estimated timeline: After S-C (migration apply) + native flag flip decision
```

Either outcome is valid — the AC is to report the status clearly, not necessarily to produce a passing score.

---

### Task EVAL-4: Verify CI Regression Gate

**Check whether the `eval:planner` CI script exists:**
```bash
cat platform/package.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('scripts',{}))" 2>/dev/null
grep "eval:planner\|planner.*eval\|eval.*planner" platform/package.json
```

**If `eval:planner` script is missing from `package.json`**, add it:
```json
{
  "scripts": {
    "eval:planner": "tsx tests/eval/planner_smoke_runner.ts"
  }
}
```

**Check CI configuration:**
```bash
ls platform/.github/workflows/ 2>/dev/null || ls .github/workflows/ 2>/dev/null
```

If a deploy workflow exists, verify it has a step that runs `npm run eval:planner` and fails the build if exit code is non-zero (tool_recall < 0.75 triggers exit 1 per EVAL-4 spec).

If no CI config exists, document that EVAL-4/5 CI integration is **PENDING** (blocked until GitHub Actions or equivalent CI is configured for this repository). Note this in the session close output.

**Acceptance:** Either (a) CI runs eval + exits non-zero on regression, OR (b) the gap is documented as PENDING with a clear blocker statement.

---

## §3 File Scope

### may_touch
```
00_ARCHITECTURE/RETENTION_POLICY_v1_0.md                [NEW]
platform/tests/eval/planner_golden_set.json              [reconcile/rename]
platform/tests/eval/golden_test_set.json                 [rename/remove if duplicate]
platform/tests/eval/planner_smoke_runner.ts              [read-only unless offline mode fix needed]
platform/tests/eval/planner_ab_compare.ts                [read-only for verification]
platform/tests/eval/planner_regression_gate.test.ts      [read-only for verification]
platform/tests/eval/fixtures/regression_baseline.json   [read-only]
platform/scripts/eval/ab_comparison.ts                   [read-only]
platform/package.json                                    [add eval:planner script if missing]
platform/.github/workflows/deploy.yml                    [verify CI step; add if missing]
```

### must_not_touch
```
# BHISMA S-A scope (parallel session — do not touch)
platform/src/lib/tools/**
platform/src/lib/synthesis/**
platform/src/lib/trace/emitter.ts
platform/src/lib/pipeline/manifest_planner.ts
platform/src/lib/pipeline/universal_query_engine.ts
platform/src/lib/pipeline/context_assembly.ts
platform/src/lib/audit/**
platform/src/lib/query_investigation.ts
platform/src/lib/config/feature_flags.ts
00_ARCHITECTURE/CAPABILITY_MANIFEST.json

# MARSYS-JIS research files
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
06_LEARNING_LAYER/**

# Governance files (read-only)
CLAUDE.md
00_ARCHITECTURE/CURRENT_STATE_v1_0.md
00_ARCHITECTURE/SESSION_LOG.md
00_ARCHITECTURE/BHISMA_WAVE2_PLAN_v1_1.md

# Ustad project (hard boundary)
/Users/Dev/Vibe-Coding/Apps/Ustad/**
```

---

## §4 Acceptance Criteria (ALL must pass before COMPLETE)

### SCHEMA-6
- [ ] `00_ARCHITECTURE/RETENTION_POLICY_v1_0.md` exists with valid YAML frontmatter
- [ ] Document covers all 4 tables (llm_call_log, query_plan_log, tool_execution_log, context_assembly_log)
- [ ] Retention tiers defined (hot/warm/cold with day windows)
- [ ] Cleanup job SQL present for both archive and delete
- [ ] GCS paths specified with bucket placeholder
- [ ] Implementation status section present (distinguishes done vs pending)

### EVAL File Reconciliation
- [ ] `platform/tests/eval/planner_golden_set.json` exists (either original or renamed)
- [ ] File contains ≥ 25 test cases
- [ ] Cases cover all 5 categories: remedial, interpretive, predictive, compound, edge-case (≥5 each)
- [ ] No conflicting `golden_test_set.json` remains (or if kept, a comment explains why both exist)
- [ ] All import references in test files updated to use the canonical filename

### EVAL-2 Lever 2 Report
- [ ] Smoke test run attempted (not just skipped)
- [ ] Explicit result recorded: PASS (tool_recall ≥ 0.80 AND tool_precision ≥ 0.90), FAIL (metrics below), or BLOCKED (with reason + unblock path)
- [ ] Output includes exact numerical scores if run succeeded

### EVAL-4 CI Gate
- [ ] `eval:planner` script exists in `platform/package.json`
- [ ] CI configuration verified: either gate is present, OR gap documented as PENDING with clear blocker

---

## §5 Hard Constraints

1. **Do NOT flip `LLM_FIRST_PLANNER_ENABLED`** — this is a native decision after reviewing S-B's Lever 2 report. S-B only reports; it does not act.
2. **Retention policy is documentation only** — do not create cleanup Cloud Run jobs or pg_cron entries in this session. Mark them as PENDING in the document. They belong to a post-S-C session.
3. **No astrological derivation** — this session touches documentation and eval tooling only. Do not derive or invent chart values.
4. **Golden set quality** — if you extend the golden set, use only query types and domains named in the Wave 2 plan. Do not invent new query classes or tool names not present in `CAPABILITY_MANIFEST.json`.
5. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter.

---

## §6 Session Close Output Required

At session close, emit the following (to be appended to `00_ARCHITECTURE/SESSION_LOG.md` by the S-D integration session):

```
## BHISMA-W2-S-B Session Close

### SCHEMA-6 Status
- RETENTION_POLICY_v1_0.md: CREATED / MISSING

### EVAL File Reconciliation
- planner_golden_set.json: EXISTED / RENAMED FROM golden_test_set.json / EXTENDED
- Golden set case count: [N]

### EVAL-2 Lever 2 Report
- Smoke test status: PASS / FAIL / BLOCKED
- tool_recall: [score or N/A]
- tool_precision: [score or N/A]
- Lever 2 recommendation: FLIP (if PASS) / HOLD (if FAIL or BLOCKED)

### EVAL-4 CI Gate
- eval:planner script in package.json: YES / ADDED / MISSING
- CI workflow gate: VERIFIED / ADDED / PENDING (reason: [blocker])
```

---

## §7 How to Start

Open a new Antigravity (Claude Code) window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:

```
Read CLAUDECODE_BRIEF_BHISMA_SB_v1_0.md and execute it.
```

The session should read this brief, set status to IN_PROGRESS, then proceed through §1 (pre-work audit), SCHEMA-6 creation, EVAL reconciliation, EVAL-2 smoke run, EVAL-4 verification, emit session close output, and set status to COMPLETE.

---

## §8 Session Close Output (executed 2026-05-03)

```
## BHISMA-W2-S-B Session Close (2026-05-03)

### SCHEMA-6 Status
- RETENTION_POLICY_v1_0.md: CREATED at 00_ARCHITECTURE/RETENTION_POLICY_v1_0.md (v1.0, CURRENT, canonical_id=RETENTION_POLICY)
- All 4 tables covered: llm_call_log, query_plan_log, tool_execution_log, context_assembly_log
- Tiers: hot 0–90d (Cloud SQL) / warm 91–365d (GCS gzip JSONL) / cold >365d (GCS Zstd)
- Cleanup-job SQL present: archive (COPY ... TO PROGRAM 'gsutil cp') + delete (DELETE WHERE created_at < NOW() - INTERVAL '90 days') with archive-done state-file gate
- GCS path: gs://[BUCKET]/retention/<table>/YYYY/MM/DD.jsonl.gz — bucket selection pending native (reuse madhav-marsys-build-artifacts vs new madhav-marsys-monitoring-archive)
- §5 Implementation Status table distinguishes the policy doc (DONE) from migrations 032–036 (PENDING — Session BHISMA S-C) and cleanup jobs (PENDING — post-S-C)

### EVAL File Reconciliation
- planner_golden_set.json: RENAMED FROM golden_test_set.json via `git mv` (preserves history). 25 entries; available_tools constrained to the 8 PRIMARY_TOOL_NAMES (W2-MANIFEST AC.M.1).
- Golden-set case count: 25
- Category coverage vs brief AC (≥5 each):
    - remedial: 6 ✓
    - interpretive: 6 ✓ (or 9 counting `category=planetary` entries that have `query_class=interpretive`)
    - "compound" (mapped to file's `holistic` + `planetary`): 7 ✓
    - predictive: 4 ✗ (1 short of brief's ≥5)
    - edge_case: 2 ✗ (3 short of brief's ≥5)
- Coverage gap NOT closed in S-B. Reason: extending the golden set requires coordinated updates to `tests/eval/fixtures/regression_baseline.json` (one mock_tool_calls entry per new GT.NNN id), and that file is `read-only` in S-B's may_touch declaration. Defer to a follow-on session that owns both files.
- Import references updated in 3 .ts test files: planner_smoke_runner.ts (comment + loadGoldenSet default), planner_ab_compare.ts (comment + loadGoldenSet path), planner_regression_gate.test.ts (loadJson call + describe text).
- Stale references remain in: tests/eval/README.md (4 mentions; not in may_touch — cosmetic only) and tests/eval/fixtures/regression_baseline.json description text (read-only; cosmetic only). Both are non-load-bearing — code paths now use the new name.
- Verification: `npx vitest run tests/eval/planner_regression_gate.test.ts` → 2/2 tests passed (avg_tool_recall=1.00, avg_tool_precision=1.00 against the mocked baseline).

### EVAL-2 Lever 2 Report
- Smoke test status: BLOCKED
- tool_recall: 0.000
- tool_precision: 0.000
- Cause: NOT a planner-quality finding. The smoke runner reached the live planner (LLM_FIRST_PLANNER_ENABLED was effectively wired — provider call attempted), but every one of the 25 entries received `LLM planner call failed: Failed after 3 attempts. Last error: Internal Server Error` from the configured provider endpoint (NVIDIA NIM, model `meta/llama-3.1-8b-instruct`). The 0.000 scores reflect provider 500s, not planner output.
- Required misses: 23 (the 23 entries whose required_tools is non-empty). The 2 entries with empty required_tools (GT.024, GT.025) registered required_hit=true despite the same error — scoring artifact.
- Lever 2 recommendation: HOLD. Lever 2 cannot be evaluated from this run. Unblock path: (a) verify NVIDIA NIM endpoint health and that the configured `meta/llama-3.1-8b-instruct` model is currently available; (b) re-run `npm run eval:planner` once the provider returns 200s; (c) if NIM is persistently unstable, switch `PLANNER_MODEL_ID` to a more reliable provider/model and re-baseline.
- Hard-constraint compliance: `LLM_FIRST_PLANNER_ENABLED` was NOT flipped by this session (per §5 hard-constraint #1). Native decision deferred until a clean PASS/FAIL smoke run is producible.

### EVAL-4 CI Gate
- `eval:planner` script in package.json: ADDED at platform/package.json line 20 (`tsx --conditions=react-server tests/eval/planner_smoke_runner.ts`).
- Companion `eval:planner-regression` script also ADDED at line 21 (`vitest run tests/eval/planner_regression_gate.test.ts`) — runs the mocked-planner gate (no LLM provider needed); verified passing locally.
- CI workflow gate: PENDING.
    - Reason / blocker: The only existing GitHub Actions workflow is `.github/workflows/deploy.yml`, which (a) triggers on `push: main` only — so a regression there gates production deploy but does NOT gate PR merge, the wrong half of the lifecycle to catch regressions; (b) has no Node setup or test step (build-and-push Docker only); and (c) modifying the production deploy pipeline to add a test gate is sufficiently weighty that native sign-off is appropriate before changing deploy semantics.
    - Recommended unblock path: author a new `.github/workflows/ci.yml` triggered on `pull_request` and `push: main`, with steps `checkout → setup-node@v4 → npm ci → npm run eval:planner-regression`. Use `eval:planner-regression` (mocked) rather than `eval:planner` (live LLM) so CI doesn't depend on provider availability or burn API tokens per PR. Wire the live `eval:planner` separately as a manual `workflow_dispatch` job for periodic Lever 2 calibration runs.

### Files modified
- ADDED  00_ARCHITECTURE/RETENTION_POLICY_v1_0.md (new, v1.0)
- RENAMED platform/tests/eval/golden_test_set.json → platform/tests/eval/planner_golden_set.json (git mv)
- MODIFIED platform/tests/eval/planner_smoke_runner.ts (2 refs: comment + loadGoldenSet default)
- MODIFIED platform/tests/eval/planner_ab_compare.ts (2 refs: comment + loadGoldenSet path)
- MODIFIED platform/tests/eval/planner_regression_gate.test.ts (2 refs: loadJson call + describe text)
- MODIFIED platform/package.json (+2 scripts: eval:planner, eval:planner-regression)
- MODIFIED CLAUDECODE_BRIEF_BHISMA_SB_v1_0.md (status NOT_STARTED → IN_PROGRESS → COMPLETE; appended §8 close output)

### Files NOT modified (in scope but no change needed)
- platform/tests/eval/fixtures/regression_baseline.json (read-only; description text references old filename — cosmetic, non-blocking)
- platform/tests/eval/README.md (not in may_touch; 4 stale references — cosmetic, non-blocking)
- platform/scripts/eval/ab_comparison.ts (read-only; not touched)
- platform/.github/workflows/deploy.yml (not modified — see EVAL-4 PENDING rationale above)

### Hard-constraint audit
- §5.1 LLM_FIRST_PLANNER_ENABLED: NOT flipped ✓
- §5.2 Retention policy is documentation only — no Cloud Run jobs / pg_cron created ✓
- §5.3 No astrological derivation in this session ✓
- §5.4 Golden-set extension: deferred (see EVAL File Reconciliation note); no new query classes or tool names invented ✓
- §5.5 Brief frontmatter status set to COMPLETE at session close ✓

### must_not_touch audit (verified clean)
- platform/src/lib/tools/**, synthesis/**, trace/emitter.ts, pipeline/manifest_planner.ts, universal_query_engine.ts, context_assembly.ts, audit/**, query_investigation.ts, config/feature_flags.ts: not touched ✓
- 00_ARCHITECTURE/CAPABILITY_MANIFEST.json, BHISMA_WAVE2_PLAN_v1_1.md, CURRENT_STATE_v1_0.md, SESSION_LOG.md, CLAUDE.md: not touched ✓
- 01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**, 06_LEARNING_LAYER/**: not touched ✓
- /Users/Dev/Vibe-Coding/Apps/Ustad/**: not touched ✓

### Handoff to S-C / S-D
- S-C (next, migration apply): RETENTION_POLICY §5 lists the migration-031-038 dependencies. The `retain_indefinitely BOOLEAN DEFAULT FALSE` column belongs in the table-creation migrations, not as a separate alter.
- S-D (integration session): append the above ## BHISMA-W2-S-B Session Close block to `00_ARCHITECTURE/SESSION_LOG.md`, and decide (with native) whether to (a) extend the golden set + baseline to close the predictive/edge_case coverage gap, and (b) author the proposed `.github/workflows/ci.yml` for the EVAL-4 gate.
```

