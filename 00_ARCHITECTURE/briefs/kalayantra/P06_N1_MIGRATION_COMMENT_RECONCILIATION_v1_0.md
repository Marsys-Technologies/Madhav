---
artifact: P06_N1_MIGRATION_COMMENT_RECONCILIATION_v1_0.md
version: "1.0"
status: CURRENT
finding: P06-N1
date: 2026-10-16
accepted_head: adc6b81eab68efe11c64211f51c923c1e84ec24c
migration_sha256: bc7a220970b91d2d60b1532368e106df673f63a56d573d88acd78857e665204b
changelog:
  - "1.0: reconcile N1's historical ordering and occurrence-kind comments without editing SQL."
---

# P06-N1 — historical 1308 comments

The accepted P06 review carries N1 at
`/Users/Dev/kalayantra/run/reviews/W4_P06_FINAL_REVIEW_adc6b81ea.md:41`.
This note reconciles `platform/migrations/1308_gochara_near_miss_storage.sql:4,51–57`
at the accepted head above. Never edit the applied migration, including its comments
(CLAUDE.md §N.4). The SHA-256 above identifies the complete accepted file, including
its historical comments; this note changes no SQL, schema, identities or executable behavior.

- **Ordering (lines 4 and 57):** P06 selection: **1305 → 1306 → 1308**. The historical 1307 publication-CHECK slot belongs to P09's new authority migration; it is not a prerequisite of P06's 1308 storage migration. Answer 18 line 13 supersedes the old four-number chain. Stacking is per function (FB-20): the near-miss follow-up replaces 1240's functions, rather than stacking on 1307. This is a contract reconciliation, not an instruction to execute a protected window.
- **Occurrence kind (lines 53–54):** FB-26 is **WITHDRAWN**: no `occurrence_kind` column is added to `ka_gochara_relationship_record` in this scope. The comment's proposed future column is obsolete. Adding it would change existing `to_jsonb` row bytes and state digests. Near-misses retain their separate tables and identity namespace; a future promotion to relationship records requires a separately versioned decision, migration and digest treatment (FB-25/26).
- **Seal integration (lines 51–54):** The digest/completeness work remains deferred, but belongs to **P06b**, not to the withdrawn column proposal. P06b must land before the FB-66 final-rules candidate and before any P08 enablement. Answer 18 §8 requires the stacked state-digest and candidate-gate replacements, per-migration readbacks (including 1308), the `near_miss_layer_version` manifest pin and the independent ephemeris-backed verifier stage. P06's honest state is `near_miss_layer: stored_uncovered`; storage alone does not earn FINAL seal readiness. The layer-absent digest remains unchanged, and near-misses remain unscored and outside scored unions, candidates, ranks and coverage accounting (FB-28/29).

## Source bindings and preparation limits

The accepted Git tree supplies
`00_ARCHITECTURE/briefs/pravaha/decisions/FINAL_BUILD_SCOPE_v1_0.md:104–115`
(FB-19/20/21/23 historical ordering) and
`00_ARCHITECTURE/briefs/pravaha/decisions/FINAL_BUILD_SCOPE_v1_0.md:120–123`
(FB-25/26/28, version 1.2). The superseding ruling is
`/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_18.md:13,32–34`.
These are source contracts, not evidence that migrations or P06b have run.

**(I) INTERPRETATION — destination:** bind this note to the existing campaign brief
directory at `00_ARCHITECTURE/briefs/kalayantra/P06_N1_MIGRATION_COMMENT_RECONCILIATION_v1_0.md`
under Amendment A3 D-23. The alternative is waiting for the cockpit to nominate a
filename; the job's autonomous preparation instruction resolves that unspecified choice.

**(I) INTERPRETATION — upstream absence:** this pre-build base does not yet contain
1308 or the final-scope specification. Bind their accepted P06-head bytes and line
references rather than copying upstream SQL or modifying a historical migration.
The alternative is waiting for J-4c's operational completion. The acceptance test
checks the full migration hash whenever the file is present; absence here is not
an applied-migration or production verification claim.

SR-A4-01 preparation only. Independent review, actual CI/merge/deploy containment
and dependency-ordered tracker completion remain with the cockpit. P06b's candidate,
enablement and FINAL-seal gates remain required. No production activation or data
operation is performed or authorized by this note.
