# KĀLA-YANTRA — close message

This is the one message the campaign leaves for the native. The finalizer appends the measured shutdown line below it; nothing in this
draft is a measurement. Where a number or a verdict is needed, it is read from the files named here, not from this page.

## Where the facts are

- **Close report (C-1):** `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CLOSE_REPORT_v1_0.md` in the campaign checkout. It attests the acceptance
  set of `ACCEPTANCE_ROOTS_v3.json` as of C-1: each of the five definition-of-done lines is MET or NOT MET there, with the evidence it was judged on.
  Its status is `CLOSED` when every acceptance root is met and `CLOSED-PARTIAL` when a root is NOT MET. The finalizer binds the report by its
  completion digest; if the file changed after C-1, the final receipt fails.
- **Final acceptance (C-4):** the independent review of the five lines, and `run/FINAL_RECEIPT.json` (what the finalizer measured: lanes,
  worktrees, processes and session databases remaining). The receipt is the record of the close chain C-2 → C-3 → C-4, which the close report
  cannot attest because it is written before them.
- **Drain (C-3):** `run/DRAIN_RECEIPT.json`.

## What the campaign set out to do, and what the close reads against

The campaign built the Kāla layer as one engine, took the Gochara 5.0 work to its flip, and left the layer rebuilt, served and carrying its
certification mapping. The close is rooted on the acceptance set the owner fixed in Amendment A9: the rebuilt and published layer with its live
acceptance (K9-4b, K9-6), the sealed and served 5.0 flip (J-6l, J-5s, V-J6), the certification mappings (K8-REG, K-CERT), and the guarded close
chain (V-K9, then C-1 to C-4). The campaign's close is not certification: the Suvarṇa engine certifies the Kāla assets afterwards.

## Deferred, not closed

These are outside the close, each with a re-entry condition. They are listed in the close report and are never reported as closed. Thirteen of them (KR-1, KR-2, J-7a, J-7a-pr3099, J-7a-a62, J-8, J-8a, J-8-b63, J-8-j3, J-4a-a25, J-4a-a26, J-3a-b44, L0-K) were deferred out of the campaign by SR-PARKED-OUT-OF-CAMPAIGN (2026-10-22) and are carried, with their re-entry conditions, in `POST_CAMPAIGN_v1_0.md`.

| Items | Re-entry |
|---|---|
| Legacy clean-up after the flip: J-7a, J-7a-a62, J-7a-pr3099, KR-1, KR-2 | after V-J6 is accepted and the served layer has run one week on 5.0 |
| Tier-2 admissions and the corpus ingestion: D-T2, L0-K | post-flip, on the same condition |
| Predecessor paperwork (Pravāha close report and archive): J-8, J-8-b63, J-8-j3, J-8a | post-campaign, as documentation |
| Rehearsal census: K9-5, K9-5-NB-01 | when Suvarṇa schedules its certification census |
| The 4.1 historical build and its baseline: J-4a-a25, J-4a-a26, J-3a-b44 | when the approved disposition of the 4.1 build is recorded, or a phase brief names it as a measured input |
| The single materializer timeout ruling: D-GOCHARA-TIMEOUT | ruled when the century build's measured duration exists |

Items that ended `not_applicable` by decision (each with its decision id in the report) are gaps or retirements as the report states them; none
is counted as closed.

## Decisions the owner may want to look at

The decisions ledger in the close report lists every surrogate ruling, owner direction and conditional approval, with the ones that were refused
or did not fire first. The deviation from the charter's finalisation text is recorded in the plan model: the finalize step is run by the
finalizer (fleet/finalize.sh), not by a separate reviewer lane.

## Measured costs and lessons

Read from the close report, sections 5 (costs) and the lessons list. Both are measured, not estimated.

This message holds no credential, no personal data and no chart data.
