---
artifact: B1_CLEAN_RERUN_STATUS
type: BAKEOFF ASSEMBLY + DR-12 ADJUDICATION RECORD
wave: D-4b — Calibration Ignition + Grand Bakeoff, Lane B-1 (clean re-run, attempt #3, post CR-123/DR-20)
version: 2.0
status: FINAL — DR-12 adjudicated, NO_WINNER
branch: wave/D-4b/B1-full-rerun-2
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
authored_by: Claude Code (Sonnet 5), assembly session, 2026-07-23
supersedes: nothing live — B-1's only prior full-run artifact, wave/D-4b/B1-full-rerun's assembly,
  is QUARANTINED (QUARANTINE_B1_FULL_RERUN_v1_0.md, that branch, never merged) and every
  score/delta/adjudication from it is VOID, cited nowhere in this record.
sibling_artifacts:
  - B1_CLEAN_RERUN_VERIFICATION_v2_0.json (manifest-hash consistency + sealed-split re-confirmation)
  - B1_CLEAN_RERUN_PER_EVENT_v2_0.json (full per-event, per-contender table, all 14 contenders)
  - B1_CLEAN_RERUN_SUMMARY_v2_0.json (CRPS skill + hit-rate + significance-test summary per contender)
---

# B1_CLEAN_RERUN_STATUS — assembly + DR-12 adjudication

## §0 — DR-19 pre-check (performed before any substantive work)

- Current branch: `wave/D-4b/B1-full-rerun-2`. Confirmed via `git branch --show-current`.
- `CLAUDECODE_BRIEF.md` (project root): `status: ACTIVE`, `current_wave: D-4b (OPEN — NOT
  CAMPAIGN-CLOSED)`. Branch belongs to the active D-4b campaign.
- `STATE_D4B.md`: lane `"B-1 run manifest + batch-runner harness"` (`wave/D-4b/B1-full-rerun-2`,
  commit `51290123`) is `merged_component`, verified sound (8/8 unit tests, tsc clean). The three
  batch commits (`e97ddce7`, `be24219e`, `5c01a67c`) are this same branch's continuation of that
  lane, not a duplicate or a different campaign's work.
- `next_action` recorded in `STATE_D4B.md`: "...Then ONE clean, chunked/checkpointed B-1 re-run,
  training-split only, on the fixed harness. Pre-committed outcome: a genuine NO_WINNER on clean
  data closes B-1 honestly — the campaign does not chase a champion." This assembly session is
  that re-run's assembly step, on the correct branch, continuing in-progress work — not
  re-litigating a closed lane.

## §1 — Inputs re-verified this session

`git fetch origin main` run first (no new commits on `main` since this branch's fork point that
touch this lane). All 3 batch commits confirmed present on `wave/D-4b/B1-full-rerun-2`:

| batch | commit | contenders | batch verifier receipt (supplied) |
|---|---|---|---|
| 1 | `e97ddce7` | pratyantar_lord, vimshottari, yogini, ashtottari, chara_karaka | ACCEPT |
| 2 | `be24219e` | naisargika, mudda, kalachakra, narayana, sade_sati | ACCEPT |
| 3 | `5c01a67c` | guru_shani_double_transit, av_threshold, planetary_return, hierarchical_ensemble | ACCEPT |

Artifacts live at `bakeoff_results/b1_batches_v2/batch_batch{1,2,3}.json`, each carrying
`chart_id=482012f1-710e-4a25-994a-93821f5871aa`, `packet_blob_sha=9b6713db8c2551a937ff2070e498da1f12526966`,
`manifest_version=2.0` — identical across all 3, cross-checked live (`B1_CLEAN_RERUN_VERIFICATION_v2_0.json`
§`batch_metadata_cross_check`).

## §2 — Manifest-hash consistency check (FAIL LOUDLY on mismatch — none found)

`hashManifestFile()`'s own algorithm (sha256 of the manifest file's exact committed bytes,
`b1_batch_artifact_io.ts`) was independently re-derived against the live committed
`B1_RUN_MANIFEST_v2_0.json`:

```
expected_hash (sha256 of live committed manifest) = ac56aa45c6fbe4e17cd78e33878d8454252aeac366ed97bdde135a861669395b
batch_batch1.json manifestHash = ac56aa45c6fbe4e17cd78e33878d8454252aeac366ed97bdde135a861669395b  MATCH
batch_batch2.json manifestHash = ac56aa45c6fbe4e17cd78e33878d8454252aeac366ed97bdde135a861669395b  MATCH
batch_batch3.json manifestHash = ac56aa45c6fbe4e17cd78e33878d8454252aeac366ed97bdde135a861669395b  MATCH
```

**Result: CONSISTENT.** No mismatch was found; the loud-failure path (which would have raised
`SystemExit` in the assembly script and halted this session before any DR-12 adjudication) was
not triggered. Full machine-readable record: `B1_CLEAN_RERUN_VERIFICATION_v2_0.json`
§`manifest_hash_consistency_check`.

## §3 — Sealed-split boundary re-confirmation (performed explicitly, independent of the harness's own internal + each driver's own defense-in-depth calls)

Per the instruction to re-confirm this myself: every `event_date` in every batch artifact was
read and checked against the 2020-01-01 boundary — **without ever querying `life_events` for any
row `>= 2020-01-01`**, per the hard constraint. The method:

1. Extracted the full set of **unique `eventId`s actually scored** (i.e. `harness`-bearing, not
   `skipped`) across all 3 batch artifacts / all 14 contenders: **31 unique events**, identical
   across all 3 batches (each of the 14 contenders was scored against the same 31-event TRAIN set
   — confirms "identical everything" per BRIEF_D4B §1's hard rule).
2. Cross-referenced every one of those 31 `eventId`s against the **byte-identical**
   `eventDate`/`intervalStart`/`intervalEnd` table embedded in all three
   `b1_batch{1,2,3}_driver_v2_0.ts` files (verified byte-identical across all three drivers by
   direct comparison — not assumed).
3. Checked **every date field** an event carries (point `eventDate`, or interval
   `intervalStart`/`intervalEnd` for interval-shaped events) against the boundary — mirroring
   `sealed_split_guard.ts`'s own `datesOf()`/`assertNoSealedSplitEvents()` semantics (an interval
   event is sealed if ANY of its dates touches the boundary, not just its onset).

**Result: CLEAN. Zero breaches.** All 31 scored events' full date sets are `< 2020-01-01`. No
event required STOP-and-report treatment. Full machine-readable record:
`B1_CLEAN_RERUN_VERIFICATION_v2_0.json` §`sealed_split_reconfirmation`.

*(Note for the record: this independent re-check is deliberately a SEPARATE code path from
`assertNoSealedSplitEvents()`/`filterToTrainScope()` — it re-derives the same conclusion via a
different mechanism (static cross-reference against the driver's own committed event table)
rather than re-invoking the same TypeScript functions, so a bug shared by both the harness call
and a naive re-invocation would not silently launder itself through this check.)*

## §4 — Assembled per-event tables + CRPS skill / hit-rate per contender

Full per-event tables for all 14 contenders are committed at `B1_CLEAN_RERUN_PER_EVENT_v2_0.json`.
Summary statistics (CRPS skill, hit-rate, significance tests) are committed at
`B1_CLEAN_RERUN_SUMMARY_v2_0.json`. Headline numbers, reproduced here for the adjudication record:

| contender | n scored | n skipped | mean CRPS (real) | mean CRPS (shuffled control) | aggregate skill (1 − mean-ratio) | wins/losses vs. own control | sign-test p (2-sided) | hit-rate (secondary) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **pratyantar_lord** | **31** | 0 | 38.612 | 43.182 | **+0.1058** | 4 / 27 | **3.40e-05** | 0.484 (15/31) |
| vimshottari | 2 | 29 | 76.457 | 43.122 | −0.7731 | 0 / 2 | 0.500 | 0.500 |
| yogini | 2 | 29 | 39.847 | 39.399 | −0.0114 | 0 / 2 | 0.500 | 0.000 |
| ashtottari | 2 | 29 | 39.847 | 39.399 | −0.0114 | 0 / 2 | 0.500 | 0.000 |
| chara_karaka | 2 | 29 | 39.664 | 39.385 | −0.0071 | 0 / 2 | 0.500 | 1.000 |
| naisargika | 2 | 29 | 39.847 | 39.399 | −0.0114 | 0 / 2 | 0.500 | 0.500 |
| mudda | 2 | 29 | 133.135 | 58.031 | −1.2942 | 0 / 2 | 0.500 | 0.500 |
| kalachakra | 2 | 29 | 39.847 | 39.399 | −0.0114 | 0 / 2 | 0.500 | 0.500 |
| narayana | 2 | 29 | 39.847 | 39.399 | −0.0114 | 0 / 2 | 0.500 | 0.000 |
| sade_sati | 2 | 29 | 39.847 | 39.399 | −0.0114 | 0 / 2 | 0.500 | 0.000 |
| guru_shani_double_transit | 2 | 29 | 39.847 | 39.399 | −0.0114 | 0 / 2 | 0.500 | 0.500 |
| av_threshold | 2 | 29 | 64.019 | 69.984 | +0.0852 | 1 / 1 | 1.000 | 0.500 |
| planetary_return | 2 | 29 | 39.847 | 39.399 | −0.0114 | 0 / 2 | 0.500 | 0.000 |
| hierarchical_ensemble | 2 | 29 | 49.203 | 39.642 | −0.2412 | 0 / 2 | 0.500 | 1.000 |

Zero negative CRPS values anywhere in the assembled set (cross-checked against each batch's own
`negative_crps_count: 0`), confirming F-2's `circularShiftCurve` sort fix holds across the full
clean re-run.

### §4.1 — The pratyantar_lord aggregate-skill number is misleading on its own; the honest picture requires the per-event tests

The naive aggregate skill (`1 − mean(CRPS_real)/mean(CRPS_control)` across all 31 events) is
nominally **positive** (+0.1058) — on its face this looks like a win. It is not one, and reporting
it alone would be a violation of DR-12's "genuinely beats its control with statistical
distinguishability, not merely numerically positive" bar. Two independent findings show why:

1. **Per-event win/loss count: 4 wins, 27 losses (13% win rate).** pratyantar_lord's real-chart
   curve has a *higher* (worse) CRPS than its own shuffled-birth control mean on 27 of the 31
   individually-scored events. An exact two-sided binomial sign test on this 4/31 split gives
   **p = 3.40 × 10⁻⁵** — a real, non-fabricated, directly-computed statistic (`math.comb`-based
   exact binomial, not a library approximation) — but the significance runs the WRONG direction
   for a DR-12 win: it says the model is *distinguishably worse* than chance-level parity with its
   own control, not better.
2. **Wilcoxon signed-rank test on the 31 paired (control − real) CRPS differences**, which — unlike
   the sign test — also weighs each event's *magnitude* of difference, confirms the same
   direction: one-sided p = 0.9993 for "model beats control" (essentially no evidence), one-sided
   p = 6.85 × 10⁻⁴ for "model loses to control" (significant). Two-sided p = 0.00137.
3. **Root cause of the positive point-estimate:** one event, `EVT.2002.XX.XX.01` (psychological
   category), carries a CRPS scale roughly an order of magnitude larger than every other event
   (real = 268.9, control = 603.9 — both huge relative to the 10–110 range every other event sits
   in) and happens to be pratyantar_lord's single best relative performance. A plain mean-ratio
   aggregate over heterogeneous-scale CRPS values lets that one event dominate the sum and flips
   the sign of the whole aggregate. This is a known fragility of mean-ratio skill aggregation
   under scale heterogeneity, not a defect in the harness's per-event math (each individual CRPS
   value re-derives correctly; F-2 is confirmed holding; zero negative CRPS anywhere).
4. Against the antiphase control specifically, the naive aggregate skill is already negative
   (−0.0307) even before this correction — the shuffled-control aggregate is the only one of the
   two naive numbers that happened to read positive, and it does so only because of the single
   outlier above.

**Conclusion for pratyantar_lord: it does not beat its control with statistical
distinguishability. The properly-controlled evidence (both the sign test and the magnitude-aware
Wilcoxon test) says the opposite — it is significantly outperformed by its own null control on
the large majority of individually-scored events.**

### §4.2 — Every other contender is structurally too thin to adjudicate at all

The 12 PERMISSION-standalone contenders + `hierarchical_ensemble` each scored only **2 of 31**
TRAIN events — the only 2 that resolve to one of this chart's 3 live-populated
`gochara_resonance_map` classes (`marriage`, `major_gain`) per F-1's disposition; every other
event is honestly `skipped` (`unresolved_event_class`), never silently force-mapped to a
same-category fallback. At n=2, the best possible two-sided sign-test p-value is 0.5 (0 or 2
wins) or 1.0 (1 win, as `av_threshold` shows) — **it is mathematically impossible for any of these
13 contenders to reach statistical distinguishability from this run's coverage**, regardless of
which way the two scored events happened to fall. This is not a new finding — it mirrors (and,
with a slightly thinner n=2 vs. the quarantined run's own n=3, reinforces) the same "too thin"
disposition the prior (VOID) run already reached, but this time on a structurally sealed-split-safe
substrate.

## §5 — DR-12 adjudication (run ONCE, here)

**Verdict: NO_WINNER.** The pre-committed no-winner branch (BRIEF_D4B §1 B-1, verbatim: *"if NO
model beats its coverage-matched shuffled-birth control, the bakeoff reports exactly that"*) is
invoked honestly, not evaded:

- **pratyantar_lord** (the only contender with adequate per-event coverage, n=31): fails the bar.
  Its naive point-estimate skill is positive but non-representative (§4.1); the two independent,
  properly-controlled significance tests computed directly from this run's own data (exact
  binomial sign test, p=3.40e-05; Wilcoxon signed-rank, one-sided p=6.85e-04) both show it is
  *significantly worse* than its own shuffled-birth control on the large majority of events —
  the opposite of a win.
- **Every other contender** (12 PERMISSION-standalone systems + hierarchical_ensemble, n=2 each):
  structurally incapable of reaching statistical distinguishability at this coverage level. Not
  adjudicated as winners or losers — simply too thin, honestly reported as such.
- **midpoint_triangle, transit_kernel**: not evaluable this wave per the manifest's roster
  disposition (CR-120/CR-121) — carried as non-participants, not silently defaulted to any
  verdict.

No contender clears DR-15(b)'s bar ("skill = 1 − CRPS_model/CRPS_control > 0 AND statistically
distinguishable from 0"). **No forced champion.** Per BRIEF_D4B's pre-committed disposition, B-2's
backfill (when dispatched) proceeds against the best-available model with
`model_confidence: none_validated` stamped on every row; campaign close records "no validated
timing model yet — prospective loop is the path" as the honest finding for this lane.

This adjudication runs **once**, in this document, over the full assembled 3-batch result. It is
not re-run per-batch and will not be re-run again for this manifest hash unless the manifest
itself changes (per `b1_batch_artifact_io.ts`'s own re-run-refusal discipline).

## §6 — Scope discipline confirmed

- No DB query was issued against `life_events` for any row `>= 2020-01-01` (or at all — this
  session's sealed-split re-confirmation worked entirely from already-committed batch-artifact
  JSON and driver `.ts` source, never a live query).
- Not touched: `asset_runner.py`, `runner.py`'s `execute_dag`/`_schedule_parallel`, the leakage
  firewall, raw LEL event data, prior gate/regression surfaces, `gochara_grammar`/
  `gochara_intensity`'s core computation.
- `assertNoSealedSplitEvents()` was already called by each batch driver before its own artifact
  write (per each batch's commit message) — this session's §3 re-confirmation is the explicit,
  independent, additional altitude requested on top of that, not a replacement for it.
- Every number in this document and its sibling JSON artifacts cites its live source (batch
  artifact JSON path + JSON key, or a directly-executed computation over that JSON) — none is
  hand-typed from memory or estimated.

---

*End of B1_CLEAN_RERUN_STATUS v2.0 (2026-07-23, D-4b B-1 clean re-run assembly). Sibling
artifacts: `B1_CLEAN_RERUN_VERIFICATION_v2_0.json`, `B1_CLEAN_RERUN_PER_EVENT_v2_0.json`,
`B1_CLEAN_RERUN_SUMMARY_v2_0.json`.*
