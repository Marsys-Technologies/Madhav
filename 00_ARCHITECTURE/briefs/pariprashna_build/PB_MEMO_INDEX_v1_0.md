---
artifact: PB_MEMO_INDEX
canonical_id: PB_MEMO_INDEX
version: 1.0
status: LIVE
date: 2026-07-30
authored_by: SAMĀPTI / B-DOCS-GOVERNANCE (Scribe)
governing: SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §12.1 (T12.1, register item PB-MEMO-INDEX)
---

# PB Memo Index — the PB campaign's rulings, ledgers, and parks in one place

**Why this exists.** The PB (Paripraśna Build) campaign produced seven governance-adjacent
artifacts across its waves — a Pratinidhi ruling, a ledger authority map, a park-with-costed-spec,
a first-class follow-up, three wave-close reports, and two wave briefs — with no single document
cross-referencing them. `SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md` §12.1 named this gap (register item
`PB-MEMO-INDEX`); this file closes it. It is an index, not a restatement — each entry states what
the artifact is, its live status, and points to the source rather than duplicating its content.

**Naming note:** this index cites the PB-0→PB-4 campaign-close artifact as `PB_CAMPAIGN_CLOSE_v1_0.md`
throughout, not `REPORT_PB.md` as `SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md` §12.2 names it — a
subagent-`Write`-tool policy block on new report-pattern filenames forced the rename; see that file's
own opening note for the full account (also relevant to register item `INF-3`).

## The seven artifacts

| # | Artifact | Path | Status (as authored) | What it is |
|---|---|---|---|---|
| 1 | `MEMO_PB-3_0` | `00_ARCHITECTURE/briefs/pariprashna_build/MEMO_PB-3_0.md` | EXECUTED | The Pratinidhi ruling on OT-11 ledger reconciliation — the first act of PB-3, executed under `CAMPAIGN_PB_MASTER_BRIEF_v1_0.md`'s "Pratinidhi replaces every human gate" delegation. Settles which of the (then) three prediction-tracking tables (`mimamsa_predictions`, `mcp_predictions`, `brahma_prospective_ledger`) is authoritative, on evidence assembled by lane X-5 under PC-8 (facts only, no choice) — the choice itself is this memo's act. |
| 2 | `LEDGER_MAP_PB-3` | `00_ARCHITECTURE/briefs/pariprashna_build/LEDGER_MAP_PB-3.md` | LIVE — authoritative | Executes `MEMO_PB-3_0` item 4: the single place that says, for any caller touching "prediction" or "outcome," which of the four tables is authoritative. Written because X-5 found no such map existed pre-PB-3, and that absence is what let two tools both named `record_outcome` silently diverge onto two different tables. **Known-stale line, corrected by `REPORT_PB-3`'s own corrections section:** describes `outcome.py` as "currently broken" — actually already retired by PR #725 (2026-07-23), before L-5 opened; not touched, not broken. This index does not re-edit `LEDGER_MAP_PB-3.md` itself (out of this lane's declared scope) — flagging the correction here so a reader hits it before the stale line. |
| 3 | `PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE` | `00_ARCHITECTURE/briefs/pariprashna_build/PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md` | **OPEN — parked, awaiting a Pratinidhi MEMO** (unchanged by this session; see `PB_CAMPAIGN_CLOSE_v1_0.md` §4 for this run's disposition) | Lane L-5's park-with-costed-spec: persisting a conversational calibration row into `mimamsa_calibration` needs a schema change (Option A: extend the shared `mi_pramana` table with a discriminator column; Option B, recommended: a new `mimamsa_conversational_calibration` table) that L-5 cannot self-authorize. The Brier computation and the ledger-side outcome write were built and round-trip for real; only the final persistence sink is parked. |
| 4 | `FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE` | `00_ARCHITECTURE/briefs/pariprashna_build/FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md` | OPEN — unscheduled, no owner assigned (as of PB-2 close) | First-class follow-up (explicitly not "partial coverage"): PB-2's golden byte-equality gate is a false-confidence gate — SAMĀPTI's A7-N8-AUDIT lane independently re-confirmed and sharpened this exact finding as F-33 (see `SAMAPTI_N8_EARNED_SIGNAL_REGISTER_v1_0.md`, branch `samapti/n8-audit`): the gate performs a real, mutation-sensitive comparison, but against a test-owned reimplementation ("the reducer path"), never against the shipped `s1LiveAdapter.ts`, and over one inline fixture rather than the full 12-file corpus. |
| 5 | `REPORT_PB-3` | `00_ARCHITECTURE/briefs/pariprashna_build/REPORT_PB-3.md` | CLOSED, disposition SHIP-DEGRADED | PB-3 SAMĪKṢĀ wave close. Six lanes merged and individually tested, but the loop was inert in production at close (no live entry, no live exit) — carried forward as `BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE.md`. §G item 9 re-graded this session — see `PB_CAMPAIGN_CLOSE_v1_0.md` §3 and the item's own row in `REPORT_PB-3.md`. |
| 6 | `BRIEF_PB-3` | `00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-3.md` | **CONFIRMED ABSENT** — never committed to git anywhere (register item WT-2, independently re-confirmed by `A1-PRESERVE` against `origin/main` and by this lane against the same). `REPORT_PB-3.md` §G item 1 and its "Corrections" section both record this gap. Nothing to index — this row exists so a reader searching for the file learns it is genuinely lost, not merely unindexed. | The wave brief PB-3 itself executed against; lost. |
| 7 | `BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE` | `00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE.md` | READY-FOR-EXECUTION (per `REPORT_PB-3.md`; SAMĀPTI's own queue tracks its G1–G5 gaps as lanes `A4-LOOP-G1`, `A5-LOOP-G2G3`, `B-LOOP-G4G5`, `B-PB6-GEOMETRY`) | The parked follow-up spec from PB-3's close: G1 (mount the missing confirm entry point — the single highest-leverage fix), G2/G3 (daily-job secret + CI DB-integration), G4 (one outcome map with a live caller), G5 (calibration-leak guard with a real call site). Priority tags in `REPORT_PB-3.md` §"Parked follow-up spec" match this brief's G1–G5 exactly. |

## Cross-reference note (not a PB artifact, cited because it governs the whole campaign)

- `CAMPAIGN_PB_MASTER_BRIEF_v1_0.md` (`00_ARCHITECTURE/briefs/pariprashna_build/CAMPAIGN_PB_MASTER_BRIEF_v1_0.md`,
  recovered on branch `samapti/preserve-work-at-risk`, PR #896, not yet on `origin/main` as of this
  writing) — the multi-wave campaign brief that establishes the Pratinidhi delegation `MEMO_PB-3_0`
  and this run's own PB-4 gate both operate under.
- `BRIEF_PB-4.md` (`00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-4.md`, same recovered branch)
  — PB-4 PŪRṆATĀ's wave brief, `status: FROZEN — opens when PB-3 closes green (or ship-degraded per
  Pratinidhi MEMO)`. PB-3 closed SHIP-DEGRADED (item 5 above), satisfying the brief's own opening
  condition; PB-4's execution status is tracked in `PB_CAMPAIGN_CLOSE_v1_0.md` §5, not here.

## What this index does not do

It does not re-adjudicate any artifact's content, re-open a closed wave, or restate row-level
findings already recorded in the source documents. See `PB_CAMPAIGN_CLOSE_v1_0.md` for the campaign-level close
disposition (PB-0 → PB-4) this run produced.

*End of PB_MEMO_INDEX v1.0.*
