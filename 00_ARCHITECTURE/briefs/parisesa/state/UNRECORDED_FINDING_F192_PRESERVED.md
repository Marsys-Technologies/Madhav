---
title: UNRECORDED FINDING F-192 — preserved verbatim
canonical_id: UNRECORDED_FINDING_F192_PRESERVED
version: 1.0
status: PRESERVED_NOT_FILED
campaign: PARISESA-V4 (CLOSED BY OWNER DECISION, 2026-08-22)
created: 2026-08-22
authored_by: PARISESA-V4 loose-ends investigation session (investigate-and-report only)
---

# F-192 — preserved, NOT filed to the campaign ledger

## Why this file exists

F-192 was triaged into the **local-only** `parisesa/campaign-state` worktree at
`/Users/Dev/par-night/parisesa-v4-state` (journal seq 1009, inside local commit
`0d8eb2225`). That commit was never pushed. Meanwhile
`origin/parisesa/campaign-state` advanced independently to journal head seq 1098
(`CLOSED_BY_OWNER_DECISION`) on a **divergent hash chain** — the two chains fork
immediately after seq 1007.

Verified 2026-08-22 against `origin/parisesa/campaign-state`:

- `ledger.json` `findings` dict contains **197** findings; there is **no `F-192` key**.
- The highest-numbered finding on origin is **F-191**, so the identifier `F-192`
  is free — no collision if it is ever filed.
- The string `F-192` appears **0 times** in origin's `journal.ndjson` (1098 lines).

The campaign is closed by explicit owner decision. Appending a new finding to a
closed campaign's ledger/journal would be new work on a paused campaign, which
the closure record explicitly forbids without fresh authorization. So the finding
is preserved here verbatim instead, and **has not been filed**.

## The finding, verbatim (journal seq 1009)

```json
{
  "confidence": "MEDIUM",
  "disposition": "PARKED",
  "event_sha256": "0542be70ef96cf38bcca00d539ce3201397ca1bb32ee744e0d62ae3d888f0e7f",
  "event_type": "finding_status",
  "evidence_summary": "Newly discovered during F-23 Lane 2 execution, disclosed as its own finding rather than silently swept into Lane 2's scope. 20 remedy_type='japa' rows and 9 remedy_type='yantra' rows show the identical mantra_text double-duty/missing pattern Lane 2 just fixed for remedy_type='mantra' rows -- but the ledger's own cohort for F-23 was scoped to remedy_type='mantra' specifically, so these were correctly left untouched rather than having scope quietly widened mid-execution.",
  "finding_id": "F-192",
  "next_action": "Apply the same mechanical mantra_text backfill (from existing corpus content, zero external lookup needed) to the 20 japa + 9 yantra rows, following Lane 2's exact method.",
  "pr_url": null,
  "prev_sha256": "8c434f0075a18248a445fe73e7291f6d99fc56fc08307e2f4d56ecc7650648f3",
  "seq": 1009,
  "source_batch": "PARISESA-V4-OWNER-RULINGS-20260821",
  "status": "DECISION_PARKED",
  "terminal_status": null
}
```

The `ledger.json` `findings["F-192"]` entry in the same local worktree is
byte-identical to the JSON above (same keys, same values).

## Plain-language restatement

While executing F-23 Lane 2 (the `mantra_text` column-double-duty backfill for
`remedy_type='mantra'` rows), the executing agent found the *same* defect pattern
in two adjacent cohorts it was **not** scoped to touch:

- **20 rows** with `remedy_type='japa'`
- **9 rows** with `remedy_type='yantra'`

Same symptom: the recitation form is stranded in the wrong column (or missing),
exactly as it was for the `mantra` cohort. The agent deliberately did **not**
widen its own scope mid-execution — it disclosed the adjacent gap as a separate
finding rather than silently sweeping it in. That disclosure is F-192.

Severity is low-to-moderate and the fix is described as mechanical: the same
backfill method as Lane 2, sourced entirely from existing corpus content, with no
external lookup required.

## Important context a future session needs

**F-192's parent work (F-23 Lanes 2–3) also never reached origin.** The Lanes 2–3
engineering — the `mantra_text` backfill, the one real GRETIL-sourced attestation,
21 honest nulls, 17 new tests, and a migration numbered 583 — was committed only
inside a sandboxed agent environment and its PR was never opened (a
machine-wide network outage at push time). Verified 2026-08-22:

- No PR matching that work exists on the repository.
- No ref anywhere in this repository contains a `58x/59x` mantra/remedy/attestation
  backfill migration, and no ref since 2026-08-20 touches
  `classical_attestation_text` in `l0_remedy_corpus.py`.
- Migration slot **583 is now occupied** by
  `platform/migrations/583_llm_pricing_versions_seed.sql` (a Pariprasna change),
  so the F-23 Lanes 2–3 migration would need renumbering if it were ever recovered.

Origin's own F-23 record (seq 1008, Fable-5 final ruling, `DATA_PARKED`) makes no
mention of the Lanes 2–3 execution at all — it rules on the state of F-23 as of
PR #1429 only. So if F-192 is ever picked up, the reviewer should first establish
whether Lane 2's fix actually landed anywhere, because F-192's stated method
("following Lane 2's exact method") points at work that does not currently exist
in the repository.

## Status of this file

- **Not committed, not pushed** as of authoring.
- Nothing was appended to the closed campaign's `ledger.json` or `journal.ndjson`
  on `origin/parisesa/campaign-state`.
- No decision has been made about whether F-192 should ever be filed. That is the
  owner's call.
