# evals/k2 — Lane K2 (consumption metric + standing battery upgrades)

Elevation Campaign v2.1, Stream γ (PŪRṆA), Lane K2 · `ELEVATION_CAMPAIGN_CHARTER_v2_1.md` §γ.K2 ·
EL-04, EL-05, EL-06, EL-09, EL-10, EL-22, EL-23, EL-60a.

All scripts here are plain `tsx`-runnable TypeScript with no build step and no dependency on
`platform/node_modules` (only Node built-ins + the optional dynamic `pg` import in
`auditor.ts`'s bonus DB-check tier). Run any of them from the repo root:

```
npx tsx evals/k2/<script>.ts [args]
```

## Files

| File | Sub-item | What it does |
|---|---|---|
| `types.ts`, `transcript_utils.ts` | — | Shared transcript/accounting loading + normalization. |
| `consumption_grader.ts` | 1 | consumption_ratio (Ω3 accounting) + accounting_completeness (honesty check) + volunteered_findings_count (EL-05). |
| `TWO_PASS_GRADING_LAW_v1_0.md`, `auditor.ts` | 2 | The LAW doc + its executable enforcement — grader pass + methodologically-independent DB-verifying auditor pass; disagreements logged, never silently resolved. |
| `instrumentation_tracks.ts` | 3 | Captures experience telemetry + I1–I5 / V1–V5 / RE1–RE5 raw ledgers from a transcript. |
| `benchmark_pairs_v1_0.json`, `benchmark_pairs_runner.ts` | 4 | 6 naive-vs-expert question pairs (wealth ×3, career ×3) + the delta-grading runner. |
| `varga_depth_probe.ts` | 5 | Checks domain-appropriate divisional-chart (varga) depth beyond D1; reads Ω8's `REGENERATED_FLOORS_v1_0.json` when present, else a verified fallback. |
| `classical_attribution_table_v1_0.json`, `classical_attribution_checker.ts` | 6 | 20 core classical-Jyotish attributions + a grep-style prose checker. |
| `reading_notes_accretion_check.ts`, `EL60A_PARKED_HONEST_v1_0.md` | 7 | Verifies `reading_notes_get` does not auto-accrete (static lookup only) and documents the gap as PARKED-HONEST (fix is outside this lane's manifest). |
| `run_k2_battery.ts` | orchestrator | Runs items 1/2/3/5/6 together over one transcript into a single `K2_BATTERY_REPORT`. |

## Quickstart

```
npx tsx evals/k2/run_k2_battery.ts --smoke
```

Runs the full battery (consumption + two-pass audit + instrumentation capture + varga depth +
classical-attribution scan) against the bundled synthetic `wealth_expert_smoke` fixture.

To grade a REAL captured transcript from the sealed evaluator harness
(`~/elev-v2-shared/ledgers/SEALED_EVALUATOR_HARNESS_v1_0.md`, frozen):

```
npx tsx evals/k2/run_k2_battery.ts <transcript.json> <domain> <chart_id>
```

Transcript format: either the bare `evals/omega7/harness_runs/*.json` shape
(`[{tool, arguments, result_raw}, ...]`) or the richer
`{calls, final_answer, query?, domain?, chart_id?, ...}` shape — see `types.ts`.

## Fixtures

`__fixtures__/` holds small SYNTHETIC transcripts used only to smoke-test these scripts. They are
not real harness output (that lives in `evals/omega7/harness_runs/` on Lane Ω7, or in future
sealed-harness runs this campaign produces) — every script that consumes a fixture says so in its
own output/comments so a reader never mistakes a smoke result for a graded finding.
