---
artifact: RESONANCE_REBUILD_DECISION_PACKET
version: "1.2"
status: "CLOSED 2026-10-02 — the re-run landed (steward run 82f8802c, 2026-10-01 23:12Z) and passed every §3 check; see RESONANCE_REBUILD_RESULT_v1_0.md. (Earlier status: NATIVE-AUTHORISED REBUILD ATTEMPTED 2026-10-01; production map RESTORED; fix PR #2875.)"
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 — a record of what happened, written from the tracker notes and the evidence files
supersedes: "v1.1 (the pre-run decision packet, retained unedited as RESONANCE_REBUILD_DECISION_PACKET_v1_0.md — its frontmatter reads 1.1)"
authority: "Records facts only; authorises nothing."
---

# Resonance-map rebuild — what actually happened on 2026-10-01

## Bottom line

The rebuild was run on production and **did not stick**: it wrote 623 rows, one of the runbook's
checks failed (a spelling-case bug in the writer), and the steward **put the original map back
from the certified file backup**. Production is exactly as before the attempt: **765 rows,
certificate `3d270ef0a2db00b240a2acb4d45171c0`**. The fix is PR #2875, not yet merged. The rebuild
has to be re-run after it merges.

## Timeline (all 2026-10-01 unless noted)

| Step | What happened | Outcome |
|---|---|---|
| Authorisation | Native authorised the steward to execute the rebuild for chart `482012f1…`. | — |
| Backup form | No reachable role may create tables in `public` (data-plane hardening; even the Cloud SQL admin role is refused), so the planned table snapshot was impossible. **Native decision: a certified FILE backup.** | Backup taken read-only: `gochara_resonance_map_482012f1_20261001071822.jsonl` (+ `.sha256`), 765 rows, joined-md5 `3d270ef0…` = the live certificate exactly; mirrored to `gs://gochara-century-stream/backups/resonance_map/`. |
| Restore tool | PR #2818 (file restore: verifies before any delete, one transaction, rolls back unless the live certificate matches). A production dress-rehearsal passed first, then rolled back. | Merged path; used later. |
| **Attempt 1** (run `8684032d…`) | Failed **before any write**: the builder role lacked a grant on the asset-state audit table. | Fixed by migration **1211** (deployed and verified 17:36Z). |
| **Attempt 2** (run `1865991c`) | Passed that point, then the orchestrator refused: the `bg_transit_rules` receipt was stale (registry changed since 2026-09-23). | **Before any write.** Referred to Suvarṇa to refresh the stale receipts. |
| **Attempt 3** (run `cb3a31f8`, 21:27Z) | Failed at the first read: the builder cannot read `chart_grants`, which the charts table's row-level-security policy references — every per-chart build fails there. | **Before any write.** Referred to Suvarṇa (grant plan owner). |
| **Run `9863849f`** | **Completed: 623 rows written** and passed every runbook §3 check **except R-4**. | See below. |
| Restore | The steward restored from the file backup. | Live = `(765, 3d270ef0…)`, verified. |

## What the completed run showed

- **Passed:** R-1 (0 negative-result sensitive targets; 21 kept = 21 positive facts), reference
  integrity (0 bad refs), R-6 (every row a valid state, partition non-empty), R-2 (67 arudha rows,
  identities both directions 0), R-3 (162 yoga rows, 0 unbacked), R-5, the value invariants and the
  mechanism identity. After-counts: sensitive_degree 21, yoga_constituent 162, mechanism_node 92,
  arudha 67, bhava 67, lord 51, karaka 43, dasha_lord_portfolio 43 (+ gulika_mandi 2,
  yamakantaka 8, bhava_arudha 67) — total **623**; content digest `(623, 2e1b89fa00048d932a2ada2030de7ca7)`.
- **Failed — R-4:** all **51 lord rows** came out `unavailable`, and **10 M-6 rows** the same way.
- **Cause:** the L0 table `reference_signs` stores lord names in **lowercase** (`jupiter`, `mars`, …);
  the writer looked them up in a table keyed in **Title case** (`Mars`), found nothing, and marked every
  lord row unavailable — although the lagna, the 12 rulership rows and all graha positions exist.
  This is a writer defect, not bad chart data.

## Where things stand now

- **Production map:** original 765 rows, certificate `3d270ef0…` (unchanged by the attempt).
- **Fix:** **PR #2875** (Stream A) — the writer normalises lord names through the project's own graha
  normaliser; an unrecognised name is reported and left `unqualified`; the backup SQL and runbook
  joins are made case-insensitive. Reported by Stream A: 8 new tests (4 fail on the old writer),
  180 passing across the resonance suites, the disposable-database rehearsal passes with `lord_rows 51`
  all resolved, and a new rehearsal control that detects the failure. **Not merged.**
- **Asset flags:** `ka_gochara_resonance`'s `lit` / `fresh` flags currently read **FALSE** for that asset
  (they were left reading true from the reverted build — a false flag; Suvarṇa has been told to hold
  `ka_gochara`) until the re-run completes.
- **Evidence** (kept on the steward's machine): `/Users/Dev/pravaha/run/backups/resonance_rebuild_run_9863849f_s3_verification.txt`
  and `…_rebuilt_9863849f.jsonl`.

## What the native needs to do

Nothing now. After #2875 merges the steward re-runs the rebuild under the same authorisation; all
runbook §3 checks must pass (R-4 now included), otherwise the file restore is used again. The
original decision's reasoning (the served map overstates its authority: 154 of 176 sensitive-degree
targets keyed to negative checks) is unchanged and still true of production today.
