---
artifact: STAGE_4_T2_SPAN_SCOPED_DISPATCH
type: UAT-DARPANA Stage-4 dispatch record
version: 1.0
status: DISPATCHED-MONITORING
date: 2026-07-24
---

# UAT-DARPANA Stage 4 — T-2 Span-Scoped Materialization Dispatch

## Span-set derivation (from the stamped battery)

Read `UAT_BATTERY_v1_0.md`'s S3 (timing) stream + Stream SN for every date/window a graded
query bears on:

- **Named LEL specimen years** (native directive): 2010–11 (windfall), 2013 (marriage).
- **Battery timing queries:** S3-01 (wealth-opening window), S3-02 (next-18-months best/worst,
  i.e. 2026–2027), S3-04 (present moment, 2026), S3-06 (retrodiction ~2015, pre-2020 per DR-20),
  S3-08 (current Saturn transit).
- **Standing-prediction / Stream-SN windows:** 2027 Saturn–Jupiter, Ketu Mahadasha onset
  (~2027–2029), Venus Mahadasha 2033–2036.
- **S4-06** (post-2020 probe, "what happened in 2023") — DR-20 permits reading the live LEL for
  serving (not for scoring); included for honest-handling coverage.

Combined: roughly 2010–2016, 2023, 2025–2029, 2033–2036 — consistent with the native's own
"~10–14 distinct years" framing.

## Honest scope-mismatch finding (recorded, not glossed over)

`ka_gochara_sweep`'s `plan_substeps` (`services/ka_gochara_sweep/writer.py`,
`_substep_sort_key`) already prioritizes dispatch order in exactly the right shape — tier 0
named specimen years, tier 1 remaining scoring-span years (birth_year..2027) for pre-registered
event classes, tier 2/3 forward span — but it has **no arbitrary "only these calendar years"
filter**. A dispatched run still plans one substep per `(event_class × year)` across the full
birth→birth+100y grid; it is only the *processing order* that is span-aware, not the *planned
scope*. The native's "~10–14 years / ~2.5–3.5h" estimate assumes a narrower selective-year
capability that does not exist in the current writer. Adding one would be a genuine writer-logic
change requiring review — correctly out of a bounded data-dispatch script's scope; not attempted
here under time pressure per the "fix-for-real, never fabricate a match" doctrine.

**Disposition:** dispatched the existing prioritized sweep as-is (script:
`platform/scripts/dispatch_uat_darpana_t2_span_scoped_gochara_rebuild.py`, governed path,
same precedent pattern as prior dispatches). 165 substeps / 3,227 rows already banked in
`build_substep_progress` from prior attempts resume cleanly (idempotent per `(event_class, year)`
key). The run is monitored and will be evaluated against the battery's actually-needed years
(named above) rather than assumed to reach full completion in the estimated window — if the
named years are served before the run reaches them naturally (unlikely given tier ordering
already surfaces them first) or after a bounded monitoring window, that is reported honestly
either way.

## Dispatch record

- `build_run 5a4b6d2f-c55e-459e-bca4-4843e89fba72`, scope=`asset_set`, target=`ka_gochara_sweep`,
  chart `482012f1-710e-4a25-994a-93821f5871aa`.
- Dispatched via `gcloud run jobs execute brahma-build-pipeline-job` (execution
  `brahma-build-pipeline-job-x26g9`).
- **Guard (native directive, binding):** serving views must return an honest `empty_reason`
  ("window not materialized") outside scoped spans — this is verified once the run has produced
  enough real coverage to test both an in-span and an out-of-span probe (see follow-up section
  of the eventual close report).
