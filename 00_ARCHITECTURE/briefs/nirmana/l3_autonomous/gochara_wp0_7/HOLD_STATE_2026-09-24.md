---
artifact: HOLD_STATE
version: 1.0
date: 2026-09-24
branch: l3/gochara-autonomous-wp0-7
status: HELD — awaiting consolidation merge; do not resume without explicit release
---

# HOLD STATE — Gochara WP0-7 session (2026-09-24)

Held per native HOLD REQUEST of 2026-09-24 for the layer-wide consolidation merge.
This branch must not move until released.

## Where the campaign stopped

- §12 delta of `briefs/GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md`: 12.5, 12.3 (4.13a–i),
  12.4 DONE and pushed. 12.9 and 12.10a/12.10b DONE by the parallel L3 session on this
  same branch. 12.10c is merge-time work for whoever merges second.
- WP10 §7.A rehearsal: GREEN (16/16, re-verified).
- WP10 §7.B tranche 1 (production): **COMPLETE, GREEN** — steps 0, 1, 3, 4, 5 green;
  step 2 restore-drill honestly NOT_RUN (no dump locally).
- WP10 §7.C tranche 2: **ENTERED under the native ruling of 2026-09-24 ("Approved on
  point number two. Go ahead to everything."), then HALTED at step 6 — E-018.**
  Steps 6–10 NOT RUN.

## Production surface — frozen by the hold

Migrations applied to production this campaign: **1080, 1081, 1082, 1083, 1084, 1087,
1091**. 1084 applied as committed (the `ka_kshetra→ka_gochara` edge deliberately held
out per K-1). 1085 is RETIRED (E-010, `G9_DISPOSITION_v1_0.md`) — never apply it.
1086 was renamed to the L1 lane (`l1_…`). Generations `v1=38287` and `3.0=1830`
untouched; both chart authorities remain `'3.0'`; century writer `is_active=false`;
no `'4.0'` rows exist. Registry re-pin (1091) is live. No temporary grants outstanding
(the step-3 CREATE grant to `amjis_app` was revoked and verified revoked).

**Per the hold: apply NO further migrations. The §12.9 staleness gate on production
overlays (135/135 + 72/72 and 132/132 + 71/71 rows with NULL upstream_fingerprint,
0 mismatched) is RED BY DESIGN — do not weaken, bypass, or re-scope it.**

## Open gates / escalations awaiting the native

- **E-018** (blocks 7.C): (1) §12.9 gate RED on production — the prescribed overlay
  rebuild rewrites live-served rows and must be its own reviewed change; (2) the step-6
  episode-enumeration driver (`--episodes-json`/`--coverage-json`) does not exist —
  it is the '4.0' writer's core and must not be improvised; (3) **E-012** still in
  force: no windows projection writer, so step 7's `windows_present` gate is RED by
  design and the authority flip is physically unreachable.
- **E-016 resolved** (1082–1084/1087 applied under the ruling); **E-017 resolved**
  (corrected 1091 applied; defect was `'[...]'` vs `text[]`, root-caused to a
  rehearsal-harness fidelity gap — rehearsal declared the column TEXT).
- **Security follow-up (native ops call):** four secrets were echoed to a session
  transcript early in the E-015 work (`nirmana-campaign-control-db-password`,
  `nirmana-evidence-ingress-db-password`, `retrieval-census-ro-db-password`,
  `amjis-inquiry-db-password`) — rotation recommended; not rotated by this session.
- Review requests in `wp7_packets/` (12.3, 12.4, 12.5, 7.B v2.1, 7.C v1.0) are all
  IMPLEMENTED_AWAITING_REVIEW / STOPPED_AWAITING_NATIVE — **nothing marked REVIEWED**.
  O-2 (K3 review) belongs to the native's session.

## What a merger needs to know that is not obvious from the diff

- PR **#2731** targets `main` and carries P-1, WP9 §5.2, N-19, and all §12 work.
  The 7.C merge-state preconditions were **ruled satisfied by the native's verbal
  ruling** (recorded in ESCALATIONS.md and the step-4/5/6 evidence) — the consolidation
  merge itself now satisfies them literally.
- 12.10c merge hygiene: whoever merges second regenerates `nirmana-writer-digests.json`,
  re-admits the L3 pin, and regenerates `capability_estate_census.json` under
  `NATIVE-2026-09-24-L0-REPAIR-REPIN`.
- The step04 APPLY_SET machinery has a REFUSED-migrations guard (1085/1086) that exits 3 —
  do not "fix" it by re-adding those numbers.
- Migration numbering: 1088–1090 belong to the Saṅgam stream; 1091 is ours (registry
  re-pin). Next free number requires a fresh cross-branch scan + `npm run guard:migration-numbers`.
- A `cloud-sql-proxy` (`madhav-astrology:asia-south1:amjis-postgres --port=5433`) was left
  running on the workstation for native use; log `/tmp/cloud-sql-proxy-5433.log`.
  Both disposable rehearsal DB containers were torn down; both temp password files shredded.
- Session close for the pre-tranche phase: `SESSION_CLOSE_WP07_REMAINDER_v1_1.yaml`
  (schema_validator exit 0). A supplementary close note for the tranche phase is due
  when the hold is released and the campaign actually ends — none written now because
  the campaign is held, not closed.
