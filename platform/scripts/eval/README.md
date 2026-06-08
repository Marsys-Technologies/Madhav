---
artifact: platform/scripts/eval/README.md
authored_by: Claude Code KARN-W7-R3-EVAL-HARNESS (2026-04-30)
status: CURRENT
---

# Eval Harness — Ground-Truth Fixtures + Runner + A/B Scoring

The eval harness measures the consume-pipeline's answer quality on a fixed
set of ground-truth queries about Abhisek Mohanty's chart. It is the M2
quality-gate instrument: the per-tool planner A/B branch (W6-R2 D7) is
evaluated against a planner-off control here.

## Files

| File | Role |
|---|---|
| `fixtures.json` | 24 ground-truth query fixtures across 6 types |
| `scorer.py` | Scoring primitives (keyword / signal / synthesis / weighted) |
| `runner.py` | Single-branch runner — calls the consume API and scores results |
| `ab_runner.py` | A/B driver — runs both planner-off and planner-on, emits delta + verdict |

Run results are stored under `00_ARCHITECTURE/EVAL/`:

| File | Role |
|---|---|
| `BASELINE_RUN_W7.json` | Planner-OFF baseline established at W7-R3 close |
| `AB_RUN_<date>.json` | Optional A/B comparison runs |

## Fixture types (4 each, 24 total)

| Code | Type | What it tests |
|---|---|---|
| A | factual | L1 retrieval — exact chart facts (positions, dashas) |
| B | signal_recall | MSR signal retrieval — specific SIG.MSR.NNN hit |
| C | cross_domain | CDLM + CGM cross-domain bridges |
| D | temporal | Dasha / sade-sati / eclipse / retrograde tools |
| E | remedial | Remedial-codex retrieval (gemstone, mantra, devata) |
| F | holistic | Whole-Chart-Read protocol (B.11) — MSR + UCN + CGM together |

## Fixture authoring rules

1. **No fabrication.** Every `expected_signals` ID must be verified against
   `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` before being added. Every
   `expected_keywords` value must be verifiably true from FORENSIC v8.0
   or MSR v3.0.
2. **Weights sum to 1.0.** `scoring_weights = {keyword_recall, signal_recall, synthesis}`.
   Run `python3 platform/scripts/eval/scorer.py` to validate.
3. **Tool list is suggestive, not strict.** `expected_tools_used` is a set
   of *plausible* tools — score does not penalize a different valid tool.
   Future stricter scoring should rewrite this column to a required-set vs.
   accepted-set distinction.
4. **`gold_answer_summary` is the judge anchor.** One sentence, fact-dense.
   The Haiku judge sees only this and the response excerpt, so it must
   carry the full ground truth.

## Scoring rubric

```
keyword_recall = (count of expected_keywords found case-insensitive in response) / total
signal_recall  = (count of expected_signals found in response) / total      # 1.0 if list empty
synthesis      = Haiku judge score 0.0..1.0 against gold_answer_summary     # 0.5 on judge failure
weighted       = keyword_recall * w_kw + signal_recall * w_sig + synthesis * w_syn
```

Weights vary per fixture so factual queries lean keyword-heavy and signal-recall
queries lean toward exact MSR-id hits. Holistic queries lean synthesis-heavy.

## Usage — single branch

```bash
# Required env (or pass --chart-id / --session-cookie):
export SMOKE_CHART_ID=$(psql ... -tAc 'SELECT id FROM charts LIMIT 1;')
export SMOKE_SESSION_COOKIE='<__session value from browser DevTools>'
export ANTHROPIC_API_KEY=...   # without this, synthesis_score returns 0.5

# Planner OFF (control)
python3 platform/scripts/eval/runner.py --planner-off \
  --base-url http://localhost:3000 \
  --output 00_ARCHITECTURE/EVAL/BASELINE_RUN_W7.json

# Planner ON (treatment)
python3 platform/scripts/eval/runner.py --planner-on \
  --base-url http://localhost:3000 \
  --output 00_ARCHITECTURE/EVAL/PLANNER_ON_RUN.json

# Subset of fixtures
python3 platform/scripts/eval/runner.py --fixture-ids F001,F005,F021 ...

# Skip Haiku judge entirely (synthesis defaults to 0.5)
python3 platform/scripts/eval/runner.py --no-judge ...
```

The runner streams a per-fixture line and finishes with a summary table.
With `--output`, the full structured results JSON is written for archival.

## Usage — A/B comparison

```bash
python3 platform/scripts/eval/ab_runner.py \
  --base-url http://localhost:3000 \
  --output 00_ARCHITECTURE/EVAL/AB_RUN_$(date -u +%Y-%m-%d).json
```

The A/B runner runs the full fixture set twice (control then treatment) and
emits a verdict:

| Verdict | Condition |
|---|---|
| `PLANNER_HELPS` | weighted delta > +0.05 |
| `PLANNER_NEUTRAL` | abs(weighted delta) ≤ 0.05 |
| `PLANNER_HURTS` | weighted delta < -0.05 |

## Planner flag handling

The planner is gated by `MARSYS_FLAG_PER_TOOL_PLANNER_ENABLED`. The runner
sets this env var before invocation, but for an external server (Cloud Run)
the flag must be set server-side and the runner trusts the trace's
`planner_active` field instead. See [feature_flags.ts:60](../../src/lib/config/feature_flags.ts#L60)
for the default and [route.ts:238](../../src/app/api/chat/consume/route.ts#L238)
for the read site.

## Results interpretation

- **Aggregate weighted ≥ 0.7** — strong baseline. Use this as the M2 close criterion.
- **Aggregate weighted 0.5–0.7** — viable; identify lowest-scoring fixture types and triage.
- **Aggregate weighted < 0.5** — pipeline degradation; halt before claiming M2 ready.
- **Per-type deltas matter.** A planner that helps holistic queries but hurts
  factual queries can be a wash on aggregate; read the per-fixture delta column.

## Failure modes

| Symptom | Likely cause |
|---|---|
| All fixtures `error: HTTP 401` | `SMOKE_SESSION_COOKIE` expired or missing |
| All fixtures `error: HTTP 404` | Wrong `--chart-id` |
| All `synthesis = 0.5` | `ANTHROPIC_API_KEY` not set, or anthropic SDK not installed |
| `planner_active = null` everywhere | Server is older than W6-R2 D7 deploy (no plan_per_tool trace step) |

## See also

- [00_ARCHITECTURE/EVAL/](../../../00_ARCHITECTURE/EVAL/) — committed run results
- [BRIEFS/CLAUDECODE_BRIEF_M2_F3_EVAL_HARNESS.md](../../../00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_F3_EVAL_HARNESS.md) — authoring brief
- [025_HOLISTIC_SYNTHESIS/MSR_v3_0.md](../../../025_HOLISTIC_SYNTHESIS/MSR_v3_0.md) — signal reference
- [99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md](../../../99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) — fact reference (FORENSIC v8.0 archived; live source = chart_facts via forensic_render)
