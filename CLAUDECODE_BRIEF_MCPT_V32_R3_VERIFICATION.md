---
artifact: CLAUDECODE_BRIEF_MCPT_V32_R3_VERIFICATION.md
session: MCPT-V32-R3-VERIFICATION
workstream: MCPT v3.2 Quality Tightening (final verification)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: main (/Users/Dev/Vibe-Coding/Apps/Madhav)
target_revision: amjis-mcp-00011-9zv (post-merge prod)
expected_result: 30/30 (was 28/30 first run, 29/30 ceiling after AMBIGUOUS fix in PR #155)
estimated_duration: 5-10 minutes
cost: ~$0.05-0.20 in Haiku tokens
---

# Claude Code Brief — MCPT v3.2 R3 Verification

## Scope

MCPT v3.2 only. The DESC_TUNE for `chart_summary` landed in commit `1868ce31` and merged to main in `fa8b203b`. Re-run R3 against the new revision to confirm the description change actually pushed the routing-eval result from 28/30 (first run, pre-fix) → 30/30 (post-fix).

**In scope (touch these):**
- New eval result + diff files under `eval-results/`
- Append "Final Verification" section to `Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md`

**Out of scope (do NOT touch):**
- `platform/tests/providers/anthropic/PROBE_anthropic_tools_forwarding.test.ts` (R11 stream)
- `evals/mcp-routing/results_b9f372a3.json` (scratch artifact, leave untracked)
- Anything under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/`
- CLAUDE.md, .geminirules

## Preconditions

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git rev-parse --abbrev-ref HEAD                    # main
git pull --ff-only origin main
git log --oneline -3 | grep -q "fa8b203b" || echo "STOP: merge commit not in last 3"
gcloud run services describe amjis-mcp --region asia-south1 --format='value(status.latestReadyRevisionName)'
# expect: amjis-mcp-00011-9zv (or newer if hotfix)
```

If any precondition fails, STOP and report.

## Steps

### 1 — Get the API key
Ask native for `ANTHROPIC_API_KEY`. Do not echo, log, or write to disk. Export to shell:
```bash
export ANTHROPIC_API_KEY='<key>'
```

### 2 — Run the eval against post-merge prod
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

MCP_BASE_URL=https://amjis-mcp-qm256lasva-el.a.run.app \
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  npm run eval:routing:capture -- \
    --tier super_admin \
    --output ../eval-results/routing_eval_verification_$TIMESTAMP.json
```

If `eval:routing:capture` script differs, use:
```bash
npx tsx ../evals/mcp-routing/runner.ts \
  --base-url https://amjis-mcp-qm256lasva-el.a.run.app \
  --tier super_admin \
  --output ../eval-results/routing_eval_verification_$TIMESTAMP.json
```

### 3 — Compute the diff vs prior result
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

PRIOR=$(ls -t eval-results/routing_eval_postprod_*.json | grep -v verification | head -1)
HEAD_FILE=$(ls -t eval-results/routing_eval_verification_*.json | head -1)

node -e "
const fs = require('fs');
const prior = JSON.parse(fs.readFileSync('$PRIOR'));
const head  = JSON.parse(fs.readFileSync('$HEAD_FILE'));
const priorPct = prior.accuracy_pct ?? prior.first_tool_choice_accuracy_pct;
const headPct  = head.accuracy_pct ?? head.first_tool_choice_accuracy_pct;
const priorPass = prior.passed_count ?? (priorPct * 0.3);
const headPass  = head.passed_count ?? (headPct * 0.3);
const totalCount = head.total_count ?? 30;
const delta   = +(headPct - priorPct).toFixed(1);
const verdict = headPct === 100 ? 'PERFECT_30_30' : (headPct > priorPct ? 'IMPROVED' : 'NO_CHANGE');
const out = {
  prior_pct: priorPct,
  head_pct: headPct,
  prior_pass: priorPass,
  head_pass: headPass,
  total: totalCount,
  delta_pp: delta,
  verdict,
  prior_revision_inferred: 'amjis-mcp-00011-9zv (pre-DESC_TUNE merge)',
  head_revision: 'amjis-mcp-00011-9zv (post-merge, includes 1868ce31)',
  prior_commit: prior.commit_sha ?? 'unknown',
  head_commit: 'fa8b203b'
};
const outFile = 'eval-results/routing_eval_verification_diff_$TIMESTAMP.json';
fs.writeFileSync(outFile, JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
"
```

### 4 — Append verification note to the failures doc
Append to `/Users/Dev/Vibe-Coding/Apps/Madhav/Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md`:

```markdown
## Final Verification — 2026-05-23 (post-DESC_TUNE merge)

After commit `1868ce31` (merged via PR #155 / fa8b203b) added explicit
"navamsa" + "D9" mentions to the `chart_summary` description, R3 was
re-run against revision amjis-mcp-00011-9zv:

| Metric | Value |
|---|---|
| Prior result (post-prod, pre-DESC_TUNE) | <prior_pass>/<total> = <prior_pct>% |
| Post-DESC_TUNE result | <head_pass>/<total> = <head_pct>% |
| Delta | <delta_pp>pp |
| Verdict | <verdict> |

Raw result: `eval-results/routing_eval_verification_<TS>.json`
Diff: `eval-results/routing_eval_verification_diff_<TS>.json`

MCPT v3.2 routing eval acceptance is now fully closed.
```

Substitute the real numbers from Step 3 output. Save the file.

### 5 — Commit + push (MCPT v3.2 files ONLY)
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Stage only the verification artifacts
git add eval-results/routing_eval_verification_*.json
git add Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md

# Verify staging — exactly 3 files
git diff --cached --name-only
# Expected:
#   Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md
#   eval-results/routing_eval_verification_<TS>.json
#   eval-results/routing_eval_verification_diff_<TS>.json
# If anything else appears, unstage with `git restore --staged <file>`.

git commit -m "eval(mcpt-v32): R3 verification post-DESC_TUNE — <verdict>

Re-run of the routing eval against amjis-mcp-00011-9zv after commit
1868ce31 (merged via fa8b203b) added 'navamsa' + 'D9' to the
chart_summary description.

Prior: <prior_pass>/<total> (<prior_pct>%)
Post-DESC_TUNE: <head_pass>/<total> (<head_pct>%)
Delta: <delta_pp>pp
Verdict: <verdict>

Closes MCPT v3.2 routing eval acceptance.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push origin main
```

## Acceptance — done when

- [ ] `eval-results/routing_eval_verification_<TS>.json` and its diff file committed on main.
- [ ] `Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md` has the "Final Verification" section.
- [ ] If verdict is `PERFECT_30_30`: MCPT v3.2 routing acceptance fully closed.
- [ ] If verdict is `IMPROVED` but < 100%: report the remaining failed prompts to native.
- [ ] If verdict is `NO_CHANGE`: report to native — the DESC_TUNE didn't help, investigate.

## Final report to Cowork (the native)

1. **Result**: `<head_pass>/<total>` (e.g. "30/30" or "29/30").
2. **Delta** vs prior run.
3. **Verdict**: `PERFECT_30_30`, `IMPROVED`, or `NO_CHANGE`.
4. **Commit SHA** of the verification commit.
5. **If not 30/30**: which prompt(s) still failed; whether the failures are AMBIGUOUS / DESC_TUNE / GOLD_WRONG / MODEL_ERROR per the existing classification.
6. **Cost** in Haiku tokens (rough estimate).

## Failure modes

| Failure | Action |
|---|---|
| Prior result file (`routing_eval_postprod_*.json` excluding verification) missing | Use `Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md` for the 28/30 reference; compute against that |
| New eval fails with API key error | STOP, ask native for different key |
| Result is < 28/30 (regression) | STOP. Surface to native immediately. This would indicate something broke between PR #155 merge and now |
| Result is exactly 30/30 | Perfect. Standard close-out per Step 5 |
| Anything wants to stage outside the 3 expected files | STOP. Unstage. Investigate |

## Out of scope

- Re-running bench or accuracy harnesses (those passed and aren't affected by description changes).
- Posting to any GitHub issue (#154 is closed, no observation window).
- Modifying tool descriptions (this is a measurement, not a tuning pass).
- Anything outside MCPT v3.2 scope.
