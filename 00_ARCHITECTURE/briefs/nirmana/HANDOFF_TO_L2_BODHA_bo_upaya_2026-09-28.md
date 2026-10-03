---
artifact: HANDOFF_TO_L2_BODHA_BO_UPAYA
version: "1.0"
status: OPEN — owner action required; not Nikaṣa's to fix
produced_on: 2026-09-28
from: campaign nikasha-test (/Users/Dev/madhav-nikasha, campaign/nikasha-test, PR #2736)
per: NIKASHA_CHANGE_REGISTER_v2_0.md v2.6, row R244 and its native ruling; R220 discipline (a campaign registers
  a finding and hands off work outside its own `may_touch`, it does not do that work)
---

# Handoff — bo_upaya cannot be rebuilt; a native ruling has fixed the direction, not the code

## The defect, in one line

`bo_upaya`'s rebuild will raise a foreign-key violation on every chart with referencing rows. It has not
failed yet only because nothing has rebuilt it since 2026-09-09 (before the change that broke it).

## What broke it, and when

Commit `fa9857f00` (#2607, 2026-09-16) removed the call to `replace_prior_rm_dasha_windowed()` from
`bo_upaya.py`'s rebuild path, while leaving `replace_prior_rm_prescriptions()` in place. The legacy table
`bodha_rm_dasha_windowed_prescriptions` holds a live, validated, non-deferrable `NO ACTION` foreign key onto
the prescriptions table. Before #2607 (commit `aa26d83bb`), the windowed table was deleted first, in the
correct child-before-parent order. After #2607, it is never deleted, so the prescriptions delete a rebuild
must perform hits rows still referenced by the legacy table.

Referencing-row counts, live (as of 2026-09-27): **5 on the canonical chart `482012f1-710e-4a25-994a-93821f5871aa`,
9 on `1c826d5a`, 6 on `cb73cd3d`.** All are Venus-mahādaśā timing windows dated from the last build, already
superseded, and still served un-flagged as current by `query_rm_dasha_windowed_prescriptions.ts:94`.

## The native ruling (2026-09-28) — what to do, and why

**Fix by restoring the delete.** Put `replace_prior_rm_dasha_windowed()` back in front of
`replace_prior_rm_prescriptions()`, in the order `aa26d83bb` had it.

The reasoning, so the owner doesn't have to re-derive it: #2607's removal was apparently done to satisfy
DP-SD-015 ("existing history remains readable"). Reading DP-SD-015 itself
(`MADHAV_DATA_PLANE_L2_BODHA_STRATEGY_v1_0.md` §5 row `services.ka_temporal`, §6), it asks L2 to **stop
producing** timing windows and to **retain the legacy schema** for compatibility, "explicitly
non-authoritative" — it does not ask for legacy **rows** to survive a rebuild. The "neither deletes nor
appends" wording that drove #2607 traces to an implementer's comment at `bo_upaya.py:1942-1944` and three
execution write-ups (`…L2_COMPATIBILITY_CORRECTION_ROLLBACK_v1_0.md:37`, `…INVESTIGATOR_CONTRACT_v1_0.md:51`,
`…CURRENT_STATE_AND_DISPOSITION_v1_0.md:103`), not to the decision text. The rows in question are the last
run's stale guesses, already superseded by the very rebuild they'd block — deleting them on rebuild is more
faithful to DP-SD-015's intent than keeping them, not less.

**Two alternatives were considered and rejected** (full reasoning in the register row R244's ruling text):
skipping/upserting the referenced rows (breaks the one-`build_id`-per-generation partition migration 1013
declares, and accretes instead of replacing); changing the FK to `CASCADE`/`SET NULL` (the referencing column
is `NOT NULL` per `migrations/325…:782`, so `SET NULL` needs a schema change for 20 dead rows, and `CASCADE`
gets the same end state as restoring the delete while leaving the writer's own comment false).

## What to actually change

1. `bo_upaya.py:1942-1945` — restore the call before the prescriptions delete; the helper already exists,
   uncalled, at `bodha_writers/_idempotency.py:455`. Rewrite the adjacent comment: DP-SD-015 asks for the
   schema to remain, not for rows to be appended — every row of a replaced generation is deleted like any
   other, per §N.3.
2. A source-order test (in the style of `test_ba_p25_4_bo_upaya_resonance_wiring.py:609ff`) asserting the
   windowed delete precedes the prescriptions delete. The existing DP-SD-015 tests only forbid the INSERT
   path and stay green under this fix.
3. Correct the three execution write-ups' stale sentence, and `MADHAV_DATA_PLANE_L2_BODHA_STRATEGY_v1_0.md`
   §6's "history remains readable" phrasing → "schema remains; rows are replaced per §N.3", so the record
   matches the ruling.
4. Do not edit migration 1013 (applied) or `cr_status.ts:171` beyond what the fix makes naturally true again.
5. **Proof:** one live orchestrator rebuild of `bo_upaya` on `482012f1`, read-only-verified afterward: 0 rows
   in `bodha_rm_dasha_windowed_prescriptions` for that chart, all prescriptions under a single `build_id`.
   This is also the `accepted_rebuild_observed` evidence the Nirmāṇa L2 cycle already needs for `bo_upaya`.

Rough scope: about half a day, plus the proof rebuild.

## What stays broken until this lands

Nikaṣa's inspector will keep reporting `bo_upaya-Idem.pattern` as a genuine, unresolved gap (it is one). Any
future `--emit-gaps` run must manually withhold the appended `bo_upaya-Idem.pattern` CLOSED line before
promoting the result to production — the procedure is written out in
`nikasha_test/wave2/W2-3_C1_REVIEW.md` §7 — because the inspector's own delegation-following detector reads
this asset as PASS today and cannot yet see the FK it would violate (that mechanical check is register row
R246, ruled YES and queued, but sequenced to land *after* this fix so it proves the fix rather than fighting
it).

## What this is not

This is not a Nikaṣa defect. The inspector's report is correct: the asset really cannot rebuild. Nikaṣa
found it, and the native ruled the direction of the fix; the fix itself belongs to whoever owns the L2 Bodha
writers, as its own PR, outside this campaign's `may_touch`.
