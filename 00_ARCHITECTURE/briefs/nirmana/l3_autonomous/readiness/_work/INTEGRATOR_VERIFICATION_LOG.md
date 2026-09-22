---
artifact: KALA_READINESS_INTEGRATOR_VERIFICATION_LOG
version: "1.0"
status: LIVING — appended as lanes land
date: 2026-09-22
scope: >
  The integrating session's OWN re-measurement of lane claims that would change a decision.
  Lane reports are evidence, not verdicts. Per CLAUDE.md §N.8, a claim is verified at its
  authority (code/schema/live DB), never by re-running the lane's own query.
---

# Integrator verification log

## CONFIRMED — Lane B: 12 per-asset L3 briefs exist; the audit's inventory was wrong

The readiness audit (T4) stated Kshetra and Sangam briefs were "CONFIRMED ABSENT — no file, no
draft, no placeholder." Re-measured at the authority: `ls 00_ARCHITECTURE/briefs/` returns **17**
`CLAUDECODE_BRIEF_L3_*` files, **12 per-asset**, including
`CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md` — 170 lines, `status: AUTHORED`, and its `brief_for:`
line is explicitly tagged **`[ELEVATE]`**. Its §0 describes elevating "the registered `ka_sangam`
(today a thin 'dasha-transit convergence windows') into the full rigor-scored engine", and it
already names the independence discount for correlated evidence and the
generator→narrow→ephemeris-last efficiency spine.

Tag census across the 12: `[ELEVATE]` ×2 (`KA_SANGAM`, `KA_VIGHNAKARA`), `[NEW]` ×4
(`KA_BHAVISHYA_LEKHA`, `KA_JIVANA_PARVA`, `KA_KALA_DARSHANA`, `KA_TULANA`), untagged ×6.

**Governance standing (the nuance Lane B did not resolve):** all 12 are dated **2026-06-21** and
name `parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v0_10.md`, which exists but is a
DIFFERENT campaign plan from the current L3 Kāla Strategy/Execution Brief. So they are
substantively rich and governance-stale: **reconcile, do not re-author.**
**`ka_kshetra` has no brief — that absence is real** (`ls | grep -i kshetra` → none).

## CORRECTED — Lane E: `transit_contribution` is not dead; it is dead in ONE scope

Lane E reported "`transit_contribution = 0.0` on every row group — its source table is empty",
concluding the served activation waveform is merely "a binary lord-domain lookup × promise grade."
**That is not what the data shows.** `transit_contribution` is not a table column at all — it is a
key inside the `components` jsonb. Measured live over all 92,412 canonical-chart rows:

| term | min | max | mean |
|---|---|---|---|
| `dasha_contribution` | 0.15 | 1.00 | 0.653 |
| `promise_contribution` | 0.00 | 0.88 | 0.478 |
| `transit_contribution` | 0.00 | 1.00 | **0.249** |

`activation` itself takes 808 distinct values over [0.033, 0.957] — not degenerate.

**The honest finding, by scope:**

| `scope_kind` | rows | rows with zero transit term | mean transit term |
|---|---|---|---|
| `domain` | 43,488 | 39,552 (**90.9%**) | 0.041 |
| `event_class` | 48,924 | 16,578 (33.9%) | 0.434 |

So for **domain-scoped** waveforms — 47% of the asset's output — the transit term contributes
nothing in 91% of rows, and those waveforms are in practice dasha × promise only. For
`event_class` scope the transit term is live and material. Lane E's conclusion holds for one
scope and is false as a blanket claim. Carry the scoped version forward; discard the blanket one.

## CONFIRMED AND BROADER — Lane E: `dissent: []` is hardcoded across the served surface

Lane E named `priority.ts:280,316`, `story.ts:609`, `explain.ts:302`. Re-measured: the hardcoded
empty-dissent assertion appears in **seven** served `kala_views` tools —
`explain.ts:302`, `now.ts:1312`, `priority.ts:280` and `:316`, `story.ts:609`, `ritual.ts:637`,
`upaya.ts:265`. `ahead.ts` carries the documented fix and states the defect plainly at `:1705`
("F-110: `dissent: []` was hardcoded") and `:1157` ("the empty array `dissent: []` … asserts that
no dissent exists"). This is a §N.8 unearned signal at the serving boundary, repeated seven times,
and it bears directly on the product's promise of inspectable disagreement.

## CONFIRMED — Lane D: four Kāla assets are in `error` state right now

Live `asset_throughput`, canonical chart: `ka_kshetra` (`worker_crash: OperationalError: the
connection is lost`, 1,183,134 rows claimed), `ka_avadhi` (`post-write integrity check failed`),
`ka_gochara_v3_century_materialize` (`BUILD-PROTECTED`, guard working as designed),
`ka_gochara_sweep` (`no writer registered`, retired identity). Diagnosis of the first:
`LANE_A2_KSHETRA_CRASH_DIAGNOSIS.md`.
