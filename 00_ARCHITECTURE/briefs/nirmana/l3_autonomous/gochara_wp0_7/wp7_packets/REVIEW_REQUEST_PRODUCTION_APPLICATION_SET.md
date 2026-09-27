---
artifact: WP7_REVIEW_REQUEST_PRODUCTION_APPLICATION_SET
packet_id: "§7.C-production-application-set"
version: "1.0"
status: DRAFT_AWAITING_NATIVE
date: 2026-09-27
author: "subagent (l3/gochara-autonomous-wp0-7, ADK-0018 runway item c)"
design_file: "GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md §12.9/§12.13; REMAINDER_FINAL_REPORT_v1_0.md §7.C; ADHIKARIN_RULINGS.md ADK-0017/ADK-0018"
commit: "4ccc01768 (step06a wiring), f93704433 (12.10c runbook) on l3/gochara-autonomous-wp0-7"
---

# REVIEW REQUEST — Production application set for the WP10 '4.0' cutover (steps 6–10)

**Status is DRAFT_AWAITING_NATIVE. Nothing in this packet is marked REVIEWED,
nothing here authorizes a production write, and no step below has been run
against production by this lane.** This packet assembles, for native review,
the complete three-link chain that would take the WP10 §7.C tranche 2 from
"halted at step 6 (E-018)" to the authority flip, now that the branch-local
prerequisite (class-context permission wiring, ADK-0017 carried block 4) is
closed by step06a.

## The three-link chain

### Link 1 — §12.9 production overlay fingerprint rebuild (E-018 item ii)

Production `kala_vedha_gochara` / `kala_moorti_nirnaya` overlay rows for the
two authority charts (`1c826d5a-…`, `482012f1-…`) still carry **NULL
`upstream_fingerprint`**. The step-6 driver (and step06b, via exit 7) refuses
stale or unfingerprinted overlays by design, so this rebuild is the first
production move.

- Machinery: `platform/python-sidecar/services/ka_vedha_gochara/freshness.py`
  (`current_fingerprint` / `current_moorti_fingerprint`) plus the overlay
  writers in `services/ka_vedha_gochara/writer.py` — the rebuild recomputes
  both fingerprints from live rule sources and re-stamps every overlay row for
  the two charts.
- Expected post-state: **non-NULL `upstream_fingerprint` on every overlay row**
  for charts `1c826d5a-…` and `482012f1-…`, with the fingerprints equal to the
  freshly computed values; the step06b §12.9 gate then passes without a
  rehearsal bypass.

### Link 2 — Candidate build production run (step 6, full sequence)

With fingerprints fresh, the candidate pipeline runs in order against
production (read path + candidate-scoped writes only — generation `'4.0'`
stays a candidate throughout this link):

1. `step06_enumerate_episodes.py` — episode enumeration for the horizon.
2. `step06_candidate_build.py` — candidate contact ledger (`'4.0'`).
3. `step06a_class_context.py` — **class-context permission wiring** (new this
   packet; see below): emits the `--class-context-json` from the real L1
   permission machinery, per class, union of `systems_active` over the class's
   candidate-contact `t_exact` instants. Honest skip: a class whose targets do
   not resolve is omitted, never fabricated; the writer then records it in
   `skipped_classes` with zero projected windows.
4. `step06b_windows_projection.py --class-context-json <step06a output>` —
   projects the candidate into `kala_gochara_windows` generation `'4.0'`.

Candidate parameter set is the **E-018 candidate-1 flags**:
`activity_shape=linear_no_box`, `orb_max_deg=5.0`. Candidate 2 (1.0° orb)
remains unratified and the writer refuses it.

### Link 3 — Authority flip (steps 7–10)

1. `step07_flip_gates.py` — all five gates including `windows_present` (now
   reachable via the real writer, not a seeded stand-in).
2. `step08_flip.py` — the authority flip itself, keyed by
   **`evidence_ref = manifest_id`** of the published `'4.0'` manifest.
3. `step09_soak_checklist.md` — soak per checklist.
4. `step10_n11_disposition.sql` — N-11 disposition.

## Evidence bundle index

- Branch-local test evidence (disposable DBs only, never production):
  - **344/344** pre-work `tests/l3/gochara/` baseline; **363/363** current
    (344 + 13 step06b + 6 step06a), all PRAMĀṆIN-reproduced against the
    disposable WP6 container (`localhost:55435`).
  - RED→GREEN gate evidence: step07 `windows_present` RED → run step06b →
    step07 GREEN exit 0 (`test_step06b_windows_projection.py`, 13 passed);
    `test_wp10_cutover.py` 17 passed with the synthetic window stand-in
    removed; `test_step06a_class_context.py` 6 passed (union semantics, honest
    zero, omission-never-fabricate, wired-JSON→writer end-to-end,
    skipped-class zero-window guarantee, exit 4/exit 3 negatives);
    `test_wp6_ledger.py` 12 passed (honest `row_counts.windows`).
- Tranche-1 production evidence (already reviewed, ADK-0013): steps 0/1/3/4/5
  green; step-5 resumed-green commit `3fcf6a586` (corrected 1091 applied as
  `amjis_app`, `integrity_passed = t`); step 2 restore-drill honestly NOT_RUN.
- Per-step evidence files:
  `platform/python-sidecar/scripts/kala_gochara_cutover/evidence/step00…step06_evidence.md`
  (07–10 are templates — to be filled at execution time, by the executor).
- Four disclosures carried from the §12.13 packet
  (`wp7_packets/REVIEW_REQUEST_12_13_E012_windows_projection.md`):
  1. **`era_slice_key` is NULL on every '4.0' row, deliberately** (1091
     conjunct (g) reads a non-null value as foreign-writer contamination);
     decade-scoped `g3_%` consumers will not see '4.0' rows — the pinned
     contract's own boundary.
  2. **Pinned date bucketing floors midnight peaks to the prior day**
     (`int(jd − 2440588.0)`); midnight contacts read one day early.
  3. ~~Permission-system class context deferred~~ — **now RESOLVED on-branch
     by step06a** (ADK-0017 carried block 4); the production run consumes the
     wired context, not the rehearsal-synthetic one. The disclosure that
     survives: the wiring is a **static per-class union over the class's
     candidate-contact instants**, disclosed on every emitted row via
     `context_source = "l1_permission_wiring:v1 (…)"`.
  4. **Candidate parameter set is E-018 candidate-1** (`linear_no_box`,
     orb 5.0°); candidate 2 unratified, refused by the writer.

## Preconditions checklist (all must hold before Link 1 starts)

- [ ] `PRODUCTION_TRANCHE_2_AUTHORIZED` flag set by the native (the 2026-09-24
      ruling admitted entry into tranche 2; this packet requests authorization
      to **resume** it past the E-018 halt point).
- [ ] Tranche-1 green state stands: `3fcf6a586` applied, conjuncts (a)–(k)
      verified, temporary CREATE grant revoked and verified `=f`.
- [ ] M-1 ratification (`linear_no_box` decay shape) confirmed as the shape
      the projection writer implements — it is the pinned algebra term-for-term.
- [ ] The 12.10c merge-hygiene runbook
      (`MERGE_HYGIENE_12_10c_RUNBOOK.md`, ADK-0018 item b) acknowledged as
      merge-time work for the second merger — **not** part of this set.
- [ ] Standing-grant question and secret rotation (transcript-scope, verified
      no-commit 2026-09-26) remain the native's calls.

## Rollback story, per link

- **Link 1 (overlay rebuild):** overlay re-stamp is a metadata UPDATE on
  `kala_vedha_gochara`/`kala_moorti_nirnaya`; reversal is restoring the prior
  `detail`/`upstream_fingerprint` values from the pre-run snapshot the executor
  must capture. The underlying rule sources are untouched.
- **Link 2 (candidate build):** fully reversible by construction — the
  candidate ledger writer and step06b both do **idempotent delete-then-insert
  scoped to (chart, generation `'4.0'`)**; `'v1'`/`'3.0'` rows are untouched
  (asserted in tests). Rollback = delete the `'4.0'` rows; the generation is
  still a candidate, so no published state exists to unwind.
- **Link 3 (authority flip):** reversal scripts exist and are rehearsed:
  `scripts/kala_gochara_cutover/step03_reversal.sql` (guard N-6a reversal) and
  `scripts/kala_gochara_cutover/step05_reversal.sql` (registry re-pin
  reversal); the step-8 flip's own reverse path is gated by
  `step07_flip_gates.py` evidence. Rehearsal status: 17/17 wp10 cutover tests
  on the disposable DB cover the flip and its refusals.

## Owed ledger backfill (same-session native item)

The owed-ledger backfill (E-019 / HOLD_STATE triples) is a **same-session
native item**, bundled here so it is not lost: seven migrations —
**1080, 1081, 1082, 1083, 1084, 1087, 1091** — are applied to production but
absent from `_migrations_applied`. Backfilling the ledger is a bookkeeping
write only; it changes no schema and no served data, but it should land in the
same reviewed session as Link 1 so the ledger and the applied state agree
before the flip.

## Explicit non-claims

1. No production writes were performed for this packet; the disposable
   containers (`localhost:55435` / `localhost:55434`) carried all test runs.
2. Nothing above is marked REVIEWED; this packet requests review, it does not
   assert it.
3. The conjunct-(j)/1072 interplay note stands (1072 NOT applied;
   `target_table` stays `kala_gochara_windows`; do not apply 1072, do not
   re-add 1085/1086 to the APPLY_SET guard).
