---
title: "BHISMA Phase 1 Round 1 — CI Planner Regression Gate"
brief_id: BHISMA_CI_S1
version: 1.0
status: COMPLETE
created_date: 2026-05-04
session_id: BHISMA-CI-S1
executor: claude-sonnet-4-6
active_phase: "BHISMA Phase 1 — CI / Hardening"
isolation_tier: BHISMA_ONLY
blocked_by: none
must_complete_before: none
parallel_safe_with: BHISMA_CLEANUP_S1
---

# BHISMA-CI-S1 — CI Planner Regression Gate

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context

Lever 2 is closed (2026-05-04). `LLM_FIRST_PLANNER_ENABLED=true` is now the production default. The planner prompt (`PLANNER_PROMPT_v1_0.md` v1.6) achieved recall=0.940 / precision=0.945 on the 29-case golden set.

A mocked regression gate already exists at `platform/tests/eval/planner_regression_gate.test.ts` and is wired to `npm run eval:planner-regression` in `package.json`. This session creates the CI workflow file that runs this gate on every pull request, preventing accidental regressions before they reach main.

**No live LLM calls required.** The regression gate test is fully mocked — it replays `tests/eval/fixtures/regression_baseline.json` through the scoring path. No `NVIDIA_NIM_API_KEY` or other secrets are needed.

---

## §1 Pre-Work Audit

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Confirm no ci.yml exists yet
ls .github/workflows/

# Confirm the regression gate test file exists
ls platform/tests/eval/planner_regression_gate.test.ts

# Confirm the baseline fixture exists (required by the test)
ls platform/tests/eval/fixtures/regression_baseline.json

# Confirm the npm script exists
cat platform/package.json | grep eval:planner-regression

# Confirm the test passes locally (quick sanity check — mocked, no LLM)
cd platform && npm run eval:planner-regression 2>&1 | tail -20
```

All of the above should succeed. If `planner_regression_gate.test.ts` or `regression_baseline.json` is missing, STOP and report — do not create a CI workflow without a working test.

---

## §2 Scope of Work

### Create `.github/workflows/ci.yml`

Create the file at project root (not inside `platform/`):

```yaml
name: CI

on:
  pull_request:
    branches:
      - main

jobs:
  planner-regression:
    name: Planner Regression Gate
    runs-on: ubuntu-latest

    permissions:
      contents: read

    defaults:
      run:
        working-directory: platform

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: platform/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Planner regression gate (mocked — no LLM)
        # Replays fixtures/regression_baseline.json through the scoring path.
        # Asserts tool_recall >= RECALL_THRESHOLD and tool_precision >= PRECISION_THRESHOLD
        # as defined in planner_smoke_runner.ts. No live LLM calls; no secrets required.
        run: npm run eval:planner-regression
```

---

## §3 File Scope

### may_touch
```
.github/workflows/ci.yml     [CREATE — new file]
```

### must_not_touch
```
.github/workflows/deploy.yml
platform/src/**
platform/tests/**
00_ARCHITECTURE/**
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
CLAUDE.md
/Users/Dev/Vibe-Coding/Apps/Ustad/**
```

---

## §4 Acceptance Criteria

- [ ] `.github/workflows/ci.yml` exists and is valid YAML
- [ ] Workflow triggers on `pull_request` to `main`
- [ ] Job runs `npm run eval:planner-regression` inside `platform/`
- [ ] No secrets referenced (test is mocked — none needed)
- [ ] `deploy.yml` is untouched (verify with `git diff .github/workflows/deploy.yml` = no output)
- [ ] The new workflow lints without error: `cat .github/workflows/ci.yml | python3 -c "import yaml,sys; yaml.safe_load(sys.stdin); print('YAML OK')"`

---

## §5 Hard Constraints

1. **Do not modify `deploy.yml`** — it is the production deployment gate. This session creates a new file only.
2. **Do not add secrets** — the regression gate test is fully mocked. Adding `NVIDIA_NIM_API_KEY` or similar would imply live LLM calls, which this test does not make.
3. **Do not modify any TypeScript source files** — this is a CI workflow session only.
4. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter and commit the new `ci.yml`.

---

## §6 How to Start

Open a new Antigravity window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:
```
Read CLAUDECODE_BRIEF_BHISMA_CI_S1_v1_0.md and execute it.
```
