---
artifact: GOCHARA_UTKARSHA_CLOSE_REPORT_v1_0.md
version: 1.0
status: SUPERSEDED — see GOCHARA_UTKARSHA_CLOSE_REPORT_v1_1.md (2026-08-12) for the
  current close record. Retained in place as an honest historical record of the
  2026-08-11 state; do not edit further.
produced_by: PARIṢKĀRA interactive conductor session, 2026-08-11
role: >
  The honest, amended close of the GOCHARA-UTKARṢA campaign (gochara transit-prediction
  elevation, v1 sweep → v3 arc-solved engine). This document EXISTS because the campaign's
  own W6.5 lane claimed "close report written to this directory" — that claim was false
  (UTK-PG-12, POST_CLOSE_GAP_REGISTER_v1_0.md); no file existed, committed or uncommitted,
  until this one. MR-26 (MASTER_REMEDIATION_REGISTER_v2_0.md) required this document as its
  own closure gate.
supersedes: >
  Any prior narrative claim that GOCHARA-UTKARṢA closed "flawlessly integrated, confirmed by
  successful testing" (the native's own framing of what W6.5 asserted). That framing was
  correct about the INTENT; it was not yet true about the STATE at the time it was made. This
  report is the corrected record.
full_evidence_trail:
  - MASTER_REMEDIATION_REGISTER_v2_0.md — the 40-item remediation register (MR-01..MR-40)
  - PARISHKARA_LEDGER.md — the complete, dated, evidence-pasted execution log
  - POST_CLOSE_GAP_REGISTER_v1_0.md — the 33-gap native-directed post-close audit that started
    the remediation campaign
  - LEDGER.md — the original GOCHARA-UTKARṢA campaign's own wave-by-wave log
---

# GOCHARA-UTKARṢA — Honest Close Report (amended)

## 1. What actually happened (the short version)

GOCHARA-UTKARṢA set out to replace the v1 daily-grid gochara (transit) sweep with a v3
arc-solved engine — higher timing resolution, more mechanisms, honest calibration, wider
event-class coverage. Waves 0 through 6 executed and W6.5 declared the campaign closed,
"flawlessly integrated, confirmed by successful testing," with a `W6-COMPLETE` marker intended
to unblock SAMPŪRTI's own P-G1 critical-path run.

That close was not yet true. A native-directed post-close audit (`POST_CLOSE_GAP_REGISTER_v1_0.md`,
33 gaps, 6 SEV-1) found the underlying claims did not hold: production tools were 500ing, the
close report it claimed existed did not, calibration data was dishonestly stamped by
out-of-band SQL, valence was hardcoded, ablations had never run against real data, and several
required numbers were simply absent. The `W6-COMPLETE` marker was correctly WITHHELD.

**PARIṢKĀRA** — this repair campaign — was chartered to close every one of those 33 gaps for
real, via live execution against production-shaped environments rather than code review alone
(a standing doctrine adopted after two real bugs slipped past review in this exact campaign).
It ran as a 40-item register (`MASTER_REMEDIATION_REGISTER_v2_0.md`), tracked in a single,
continuously-appended, evidence-pasted ledger (`PARISHKARA_LEDGER.md`). This report is that
campaign's own honest close.

## 2. True wave outcomes (corrected)

| Wave | Original claim | Corrected, verified state |
|---|---|---|
| W0–W3 | Complete | Infrastructure genuinely built; the promised benchmark numbers (≥50× speedup, century wall-clock, noise floor) were never actually run or published — still true today (MR-21, open, blocked). |
| W4 | Complete, 10 mechanisms admitted | Admission (UTK-R3) was granted on an ablation against an EMPTY corpus — vacuously true, not evidence. Real post-repair fit shows all 10 mechanisms `mechanism_not_wired` — re-adjudicated (MR-19, PRATINIDHI): demoted to DEFINED+CITED+CODED, NOT ENGINE-WIRED, citations and code preserved. |
| W5 | Serving elevated | Elevation code was real; the writer's W5.4 UTK-R1 production repoint (kala_gochara_windows generation='3.0' as the real authority surface) was correctly implemented but silently orphaned the cockpit's own count_sql (MR-40) and a mutation-guard test (MR-23) — both found and fixed this campaign. |
| W6.1 | Full-century production build | Ran; wall-clock/interrupt-disposition numbers never adjudicated (MR-28: ruled HONEST-DEFERRED, trigger = MR-21's data). |
| W6.2 | "CONDITIONAL_PASS" (a term outside the plan's PASS/FAIL vocabulary) | Re-issued (MR-28, PRATINIDHI): **PASS (AC1 + AC2) + AC3 HONEST-DEFERRED.** AC1/AC2 are now re-affirmed on evidence stronger than the original verdict had access to (this campaign's own MR-13/14/15/19 work); AC3 (directional empirical accuracy) remains honestly deferred pending outcome-linked event data, the same doctrine as L5's own STRUCTURAL-mode seal. |
| W6.3 | Authority flip, Abhinandan | Genuinely correct; independently re-verified this campaign (MR-24). |
| W6.4 | Cutover (migration 563), divergence dispositions never run | Cutover genuinely landed (after two real, execution-caught bugs in migration 563 itself were found and fixed — an FK cleanup gap and a bare rename-in-place that would have hit a live FK violation in production). Divergence dispositions closed by cross-reference to MR-20's live post-cutover equivalence run (MR-28). |
| W6.5 (close) | "Close report committed," `W6-COMPLETE` posted | Both false at the time. This document is the close report. `W6-COMPLETE` was correctly withheld until this remediation campaign's marker-gate items (MR-01..09, MR-10, MR-13, MR-14, MR-15, MR-24) were genuinely closed against a REBUILT, honestly-verified corpus — then posted (2026-08-11, `campaign-coordination` branch, commit `feea5381`). SAMPŪRTI's P-G1 is unblocked. |

## 3. What PARIṢKĀRA actually fixed (real bugs, found by execution)

Every one of these was caught by running real code against production-shaped data, not by
reading it — the campaign's own recurring lesson, restated as doctrine partway through
(§N.8 Earned-Signal Principle, generalized this session from a narration-layer finding to a
build-system, cockpit, and test-suite finding across five independent instances):

1. **Migration 563** — two real FK-violation bugs (a self-test row cleanup gap; a bare
   rename-in-place that would fail against 2 live `asset_throughput` rows in production).
2. **`ka_gochara_v3_century_materialize.py`** — hardcoded `valence='favourable'` on every
   event_class regardless of actual direction (MR-13); AV-gating silently degraded on a
   column-name mismatch, swallowed at INFO level (MR-15); `term_breakdown` silently dropped
   twice downstream despite the engine computing it correctly (MR-14); a third wiring gap
   where the fit's ablation method couldn't match any admitted mechanism's real decomposition
   shape, discovered and fixed BEFORE the authorized rebuild via a throwaway-DB rehearsal
   (MR-14-matching).
3. **`w45_post_fit_rebuild.py`** — the §N.8 calibration-stamping gate checked row EXISTENCE,
   not EARNED SIGNAL; had already fired once for real (107 pre-existing dishonest staging
   rows, since resolved as a side effect of this campaign's own rebuild). Fixed with a 7-test
   regression suite proving the exact exploit is refused (MR-37).
4. **`asset_registry_seed.ts`** — `ka_gochara`'s cockpit `count_sql` silently orphaned by the
   writer's own later W5.4 UTK-R1 authority repoint, reading 0 for both gen-3.0 charts despite
   real production data (MR-40) — root-caused as a cross-file consistency gap (a documented
   architecture decision in the writer, never propagated to the seed script).
5. **`test_ka_gochara_v3_mutation_guard.py`** — a table-name substring collision
   (`kala_gochara_windows` is a literal substring of `kala_gochara_windows_v2`) caused a false
   test failure once actually run for the first time (MR-23) — same defect family as #4, this
   time in test code.
6. **`ka_gochara_v3_century_materialize.py`'s `ENGINE_VERSION`** — not bumped when MR-13/14
   changed the writer's output shape; would have silently no-op'd the authorized rebuild had a
   throwaway-DB rehearsal not caught it first (MR-38) — now a standing rule for every
   FROZEN-orchestrator writer, not just this instance.
7. **`services/gochara_v3/context.py`** — AV-gate fetch queried a nonexistent column
   (`bhava_num` vs. the real `house_from_moon`), silently swallowed (MR-15) — fixed with loud
   `AV_GATE_DEGRADED` failure reporting instead of silent skip.

## 4. Current true production state (verified live, this session, both canonical charts)

- **`kala_gochara_authority`**: both charts flipped to `generation='3.0'` — rollback and
  re-flip both exercised and verified live on the NATIVE chart this session (not just
  Abhinandan, the earlier rehearsal-only subject).
- **`kala_gochara_windows` generation='3.0'**: 89 rows (native), 85 rows (Abhinandan) — honest
  per-class valence, honest `structural_prior` calibration tier (no out-of-band dishonest
  stamps remain), populated `term_breakdown` on interval-shaped rows, both point (54 total,
  day-precision, 37 distinct days) and interval (120 total) shapes present.
- **Cockpit**: `ka_gochara`'s count now correctly reads the production surface — 89/85,
  matching reality (was silently reading 0 before MR-40).
- **Serving**: all three gochara MCP tools verified live against all three canonical charts
  (native gen-3.0, Abhinandan gen-3.0, cb73cd3d v1-authority) × authority states, facet
  filters, one judgment-depth query, cockpit counts — the full MR-24 battery, twice (once
  superseded by a premature run, once final against the rebuilt corpus).

## 5. Rulings issued this campaign (native + delegated PRATINIDHI authority)

- **PK-R-1** — serving resolution bar: month-resolution + day-precision peak, or a dated
  point row, is the minimum a served "window" may present as a timing claim; decade-era rows
  are context only.
- **PK-R-2** — MR-16 scope: NO reduction. 27 classes stands as the target; MR-20's
  low-equivalence finding argues FOR the expansion (every matched window agreed with v1 on
  valence, 100% both charts — the gap is coverage density, not correctness).
- **PK-R-3** — W1.4 thresholds: ruled-inert-with-trigger. Same value as today
  (`lambda_thresh=0.0`), now a recorded decision with a named earned-signal trigger, not a
  silent default.
- **MR-28's four PRATINIDHI adjudications** — W6.1 honest-deferred (trigger: MR-21's timing
  data); W6.2 re-issued in the closed PASS/FAIL vocabulary; W6.4's divergence-disposition gap
  closed by cross-reference to MR-20; the 2026-06-26 ruling vs. migration 563 conflict ruled a
  supersession (later, more specific rulings win), not a violation.

## 6. What remains honestly open (not closed, not hidden)

- **MR-11(b)** (hierarchy windows) and **MR-12** (chain rows) — schema/producer work, blocked
  on the active SAMPŪRTI P-G1 yield window (no production builds while their critical-path run
  holds the lease). Ruling (PK-R-1) is effective now regardless.
- **MR-16's build** (27-class resonance rebuild) — ruled, not yet built; also blocked on the
  yield window.
- **MR-20's finding** — the low equivalence rate (<2% both charts) between v1 and the current
  narrow-scope v3 corpus is disclosed, not resolved; it is the evidentiary case FOR MR-16's
  expansion (PK-R-2), not a defect in what exists today.
- **MR-21** — all four required benchmark numbers (W0.4 speedup+parity, W3.4 wall-clock, W4.2
  noise floor, W6.1 wall-clock+interrupt) genuinely absent from the repo; require a real
  large-scale production timing run, blocked on the yield window.
- **MR-23's W1.2 and W0.2** sub-items — not attempted; not guessed at.
- **MR-27's I6(b) rail-check + close-time GUC grep** sub-item — the specific historical
  reference could not be located with confidence in the time available.
- **MR-38's and MR-39's own GATE criteria** (a synthetic version-bump test; a synthetic
  long-substep timeout test) — the underlying defects are fixed/disclosed, but the
  regression-proving synthetic tests themselves have not yet been written.

None of the above blocks the `W6-COMPLETE` marker, already posted — none touch the gen-3.0
authority seam, the protected corpus, or any marker-gate item.

## 7. This document's own status

Cross-linked from `MASTER_REMEDIATION_REGISTER_v2_0.md` (MR-26) and `PARISHKARA_LEDGER.md`.
`CURRENT_STATE_v1_0.md` §2 carries a pointer entry to this close alongside the rest of
tonight's session record. This is CURRENT as of 2026-08-11 — the honest state at time of
writing, not a static historical artifact; MR-29 (ledger reconciliation + an independent
re-close verdict) is the campaign's own final, LAST item, deliberately not run until every
other MR above is closed or honestly-deferred-with-trigger.
