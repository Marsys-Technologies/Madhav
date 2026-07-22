---
artifact: QUARANTINE_B1_FULL_RERUN
type: INCIDENT RECORD (QUARANTINE NOTICE)
version: 1.0
status: PERMANENT — this branch and every artifact on it is quarantined by name, by native
  ruling, 2026-07-22. Do not merge. Do not cite its scores, deltas, or DR-12 adjudication as
  data anywhere. Its only legitimate use is as evidence in this incident record and in
  DR-20/CR-123 below.
---

# QUARANTINE NOTICE — branch `wave/D-4b/B1-full-rerun`

**Branch state at quarantine (2026-07-22, tip `0aa69c06`): QUARANTINED-SEALED-SPLIT-BREACH.**

## What happened

The D-4b B-1 chunked re-run's full anti-gaming verifier (fresh-context, independent) found that
all 3 checkpointed batches scored events on/after 2026-07-22's sealed test-split boundary
(`life_events.event_date >= '2020-01-01'`), in breach of `ESCALATION_POLICY_v1_0.md §4`:

- `pratyantar_lord` scored 20 post-2020 events (`EVT.2021.01.XX.01` through `EVT.2026.04.08.01`)
  with real CRPS values and DR-17 grades.
- All 12 PERMISSION-system contenders + `hierarchical_ensemble` scored `EVT.2025.07.XX.01` (a
  2025 marriage event) as one of only 3 scored events each.

Five of six required anti-gaming confirmations passed cleanly (manifest-hash consistency, zero
negative CRPS, full event accounting, aggregate re-derivation matching the assembled summary,
DR-12's NO_WINNER call being arithmetically honest on the data it had). The sixth — "no
test-split event touched anywhere" — failed, and per the verifier's own charge that failure is
dispositive regardless of how clean everything else was.

## Disposition (native ruling, 2026-07-22)

**QUARANTINE, not partial salvage.** A run that touched the sealed split is wholly disqualified —
"partial salvage is exactly the rationalization the seal exists to forbid." This applies even
though `pratyantar_lord`'s pre-2020 (TRAIN) events were scored honestly and correctly within the
same run: the contamination is at the RUN level, not per-event, because the run's own controls,
seed derivation, and adjudication were computed with knowledge of (and inputs from) the
sealed-split scores sitting alongside the legitimate ones.

**Every number from this branch is VOID:** the DR-12 `NO_WINNER` adjudication, every contender's
CRPS/hit-rate/skill figure, every control delta. None may be cited as data by B-2, B-3, B-6, or
any future session. The branch stays unmerged, permanently, as evidence only.

**Merge agent's decline and the conductor's refusal to self-fix under the retained invariant are
commended in the record** — the governance architecture caught a real breach, three verification
altitudes deep from where it originated but still before `main`, `B-2`, or `B-3` were ever
touched. See `NATIVE_PROXY_LEDGER_D4B.md` NP-D4B-007 for the full commendation and DR-20 for the
structural fix this incident produced.

## What supersedes this branch

`wave/D-4b/B1-full-rerun-2` (or the next available lane-name suffix) — a clean re-run on the
DR-20-fixed harness, training-split only, chunked/checkpointed per the standing pattern, with the
sealed-split assertion now structural at every verification altitude (per-batch, assembly, final
anti-gaming) rather than instruction-only.
