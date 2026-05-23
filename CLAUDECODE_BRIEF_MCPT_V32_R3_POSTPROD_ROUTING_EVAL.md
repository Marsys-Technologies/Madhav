---
artifact: CLAUDECODE_BRIEF_MCPT_V32_R3_POSTPROD_ROUTING_EVAL.md
session: MCPT-V32-R3-POSTPROD-ROUTING-EVAL
workstream: MCPT v3.2 Quality Tightening (post-prod follow-up)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: any (script-only; no branch changes)
plan: Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md (Phase 9.5b acceptance criterion)
trigger: run AFTER tag mcpt-v32-prod exists (i.e. after prod promotion has succeeded)
estimated_duration: 5-10 minutes (compute + Haiku tokens ~$0.05-0.20)
---

# Claude Code Brief — MCPT v3.2 R3 Post-Prod Routing Eval

## Context

During the MCPT v3.2 prod promotion sweep, the live routing eval (R3) was skipped because `ANTHROPIC_API_KEY` was not in the conductor's environment. The dry-run was verified, the harness is wired and committed, and the descriptions are live in prod — but the **≥15pp routing-accuracy improvement** acceptance criterion from `Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md` Phase 9.5b is in `untested-live` state.

This brief closes that gap by running the eval against prod and recording the real number.

## Goal

Produce one verified result row of the form:

```
Routing accuracy (super_admin tier, prod):
  Phase-0 baseline: NN.N%  (captured 2026-05-23, mcpt-v32-baseline tag)
  v3.2 prod (post-promote): NN.N%
  Delta: +NN.Npp
  Verdict: PASS (>= 15pp) | FAIL (< 15pp)
```

…posted to the post-prod observation issue (created by the conductor at Phase 10.10) and committed to `eval-results/` following the existing convention.

## Precondition (verify before running)

1. Tag `mcpt-v32-prod` exists: `git tag --list mcpt-v32-prod` returns a tag.
2. Prod traffic is on the new revision: `gcloud run services describe amjis-mcp --region asia-south1 --format="value(status.traffic[].revisionName,status.traffic[].percent)"` shows 100% on the new revision.
3. The observation issue exists: `gh issue list --label observation --search "MCPT-v3.2"` returns a non-empty result.
4. The routing eval harness is committed: `ls evals/mcp-routing/` shows `prompts.json` + `runner.ts`.

If any precondition fails, STOP and report — do not proceed with the eval.

## Your task

### Step 1 — Get the API key

1. Ask the native (human) for their `ANTHROPIC_API_KEY`. Do not echo it back, do not log it, do not write it to disk.
2. In your shell session: `export ANTHROPIC_API_KEY='<key>'`

### Step 2 — Capture the prod-pointing routing-eval baseline

The eval needs the prod MCP URL so it sees the v3.2 descriptions.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav      # main (not a worktree)
git fetch --tags origin
git checkout mcpt-v32-prod                  # detached HEAD on the prod tag
```

### Step 3 — Run the eval against prod

```bash
cd platform-mcp
npm install                                  # if not already done

# Run against prod
MCP_BASE_URL=https://amjis-mcp-qm256lasva-el.a.run.app \
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  npm run eval:routing:capture -- --tier super_admin --output ../eval-results/routing_eval_postprod_$(date -u +%Y%m%dT%H%M%SZ).json
```

If the npm script name differs, look in `platform-mcp/package.json` `scripts` or fall back to: `npx tsx evals/mcp-routing/runner.ts --base-url https://amjis-mcp-... --tier super_admin --output ...`

### Step 4 — Compare against Phase 0 baseline

The Phase 0 baseline routing-accuracy number was captured at the `mcpt-v32-baseline` tag and committed to `eval-results/routing_eval_baseline_*.json` (find the exact filename via `ls eval-results/routing_eval_baseline*` ; if none exists, the baseline is in `bench/baseline.json` or `bench/mcp_test_baseline.log`).

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
node -e "
const baseline = JSON.parse(require('fs').readFileSync('eval-results/routing_eval_baseline_<actual-filename>.json'));
const head     = JSON.parse(require('fs').readFileSync('eval-results/routing_eval_postprod_<actual-filename>.json'));
const baseAcc  = baseline.accuracy_pct;
const headAcc  = head.accuracy_pct;
const delta    = (headAcc - baseAcc).toFixed(1);
const verdict  = (headAcc - baseAcc) >= 15 ? 'PASS' : 'FAIL';
console.log(JSON.stringify({baseline_pct: baseAcc, head_pct: headAcc, delta_pp: delta, verdict, target_pp: 15}, null, 2));
" > eval-results/routing_eval_diff_$(date -u +%Y%m%dT%H%M%SZ).json
cat eval-results/routing_eval_diff_*.json | tail -1
```

If the result JSON shape doesn't match (`.accuracy_pct`), adapt the field names — the goal is one diff JSON with `{baseline_pct, head_pct, delta_pp, verdict}`.

### Step 5 — Commit the result

```bash
git checkout main
git pull --ff-only origin main
git add eval-results/routing_eval_postprod_*.json eval-results/routing_eval_diff_*.json
git commit -m "eval(mcpt-v32): R3 post-prod routing eval — <verdict>, <delta>pp

Live routing-accuracy eval against prod (revision $(gcloud run services describe amjis-mcp --region asia-south1 --format='value(status.latestReadyRevisionName)')) under super_admin tier.

Baseline (mcpt-v32-baseline): <baseline_pct>%
v3.2 prod: <head_pct>%
Delta: <delta_pp>pp
Verdict: <verdict> (target >= 15pp)

Closes the Phase 9.5b acceptance criterion that was deferred during the
prod promotion sweep due to missing ANTHROPIC_API_KEY in the conductor
environment.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push origin main
```

### Step 6 — Post to the observation issue

```bash
ISSUE=$(gh issue list --label observation --search "MCPT-v3.2" --json number --jq '.[0].number')

gh issue comment $ISSUE --body "## R3 Routing Eval — Post-Prod Result

Run against prod ($(gcloud run services describe amjis-mcp --region asia-south1 --format='value(status.url)')) at $(date -u +%Y-%m-%dT%H:%M:%SZ).

| Metric | Value |
|---|---|
| Phase 0 baseline accuracy | <baseline_pct>% |
| v3.2 prod accuracy | <head_pct>% |
| Delta | <delta_pp>pp |
| Target | >= 15pp |
| Verdict | **<verdict>** |

Raw result: \`eval-results/routing_eval_postprod_*.json\` (commit <sha>)
Diff: \`eval-results/routing_eval_diff_*.json\` (commit <sha>)

Phase 9.5b acceptance criterion now closed."
```

### Step 7 — Report back to the native

Report to Cowork (the native) with:
1. Verdict (PASS / FAIL).
2. Delta percentage points.
3. Issue URL.
4. Commit SHA.
5. Any anomalies (failures on specific prompts, latency outliers, cost).

## Acceptance — done when

- [ ] `eval-results/routing_eval_postprod_*.json` exists on main with all 30 prompts evaluated.
- [ ] `eval-results/routing_eval_diff_*.json` exists with `{baseline_pct, head_pct, delta_pp, verdict}`.
- [ ] Observation issue has a comment with the verdict table.
- [ ] Native has been notified with the four-item report.

## Failure modes

| Failure | Action |
|---|---|
| Phase 0 baseline file missing | Run `npm run eval:routing:capture` against `mcpt-v32-baseline` tag first to generate it, then proceed with comparison |
| Haiku quota exhausted | Stop, surface to native. Do not retry without consent — this would inflate cost |
| API key invalid | Stop, ask native for a different key |
| Prod URL unreachable | Stop — there is a prod problem more important than this eval |
| Delta < 15pp (FAIL verdict) | Post the result anyway. This is information, not a problem to hide. Open a follow-up issue for description tuning (Phase 5/6 retrospective) |
| Delta > 15pp (PASS) | Standard close-out per Step 6 + Step 7 |

## Out of scope

- Re-running bench/accuracy harness against prod (already done in the sweep).
- Updating any tool description (this is a measurement, not a fix).
- Touching CLAUDE.md or .geminirules (no architectural change).
- Any modification under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/` — these remain must-not-touch.

## Cost estimate

- Haiku tokens: ~30 prompts × ~3K tokens avg = ~90K input + ~1K output = roughly 5-20 cents.
- gcloud calls: free (read-only).
- gh calls: free.

Total: less than a quarter.
