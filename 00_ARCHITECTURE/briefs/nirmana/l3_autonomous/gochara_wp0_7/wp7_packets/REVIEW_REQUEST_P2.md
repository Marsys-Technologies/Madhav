---
artifact: WP7_REVIEW_REQUEST_P2
packet_id: P-2
status: IMPLEMENTED_AWAITING_REVIEW
date: 2026-09-24
branch: l3/gochara-autonomous-wp0-7
---

# REVIEW REQUEST — P-2 (reading checklist: contact_id / completeness_state / peak_basis through the cap)

## What landed

`platform/src/lib/retrieval/registry/layers/reading_checklist.ts` (`fetchGocharaSweep`):

- SQL projection (+4 columns, all present since migrations 527/564; v1 rows
  arrive NULL): `w.peak_basis`, `w.generation`, `w.active_sentences`,
  `w.completeness_state`.
- `GocharaSweepWindow` extended (existing fields untouched): `peak_basis`,
  `generation`, `completeness_state`, `contact_ids` (parsed from
  `active_sentences` jsonb; `[]` on NULL/non-array/non-string members — never
  fabricated), `is_confirmed` (completeness in confirmed set AND peak_basis in
  `GENUINE_PEAK_BASES = {'gochara_lambda_v3_argmax'}`, mirrored from
  `register_gochara_windows.ts:372`).
- `GocharaSweepResult` extended: `confirmed_rows_in_page`,
  `context_only_rows_in_page`, `catalog_only_note` (wording mirrors
  `summarizeResolutionDisclosure`'s pattern), `provenance { generation,
  manifest_id }`. `note` gains one sentence when context-only rows are served.
- Trim discipline unchanged: first-N stored order (`slice(0, 5)`), never
  re-rank / re-admit (H-5); the 200-row SQL cap and `upcoming_window_count`
  raw-match semantics (with its existing disclosure comment) are untouched.

## Test evidence

- New `__tests__/reading_checklist.fetch_gochara_sweep_p2.test.ts` — 4 tests:
  (a) confirmed '4.0' row serves `contact_ids` + `is_confirmed`; (b)
  unqualified/non-argmax row counts context-only with counts 1/1 and the note;
  (c) v1 NULL columns degrade to nulls/`[]` without error; trim stays first-N
  stored order over a 7-row page; empty page keeps zero counts and null note.
- Pre-existing ADJUDICATION-6 + past-peak sweep tests: green unchanged.
- Full `src/lib/retrieval/registry/layers` battery: **1415 passed / 0 failed
  (159 files)** — D8/D9 compile and their sweep legs pass with no changes on
  their side (packet acceptance item).
- `npx tsc --noEmit --skipLibCheck` in platform: 0 errors.

## Items flagged for independent review

1. **Confirmed-set membership**: the packet says "completeness_state in the
   confirmed set" but nowhere enumerates the F06 six states; its own fixture
   uses `'confirmed'` while the WP6 writer vocab
   (`gochara_kernel/episodes.py`, `gochara_v3/interval_solver.py`) uses
   `'qualified'`. `CONFIRMED_COMPLETENESS_STATES = {'confirmed', 'qualified'}`
   covers both; if the F06 registry names additional confirmed-family states
   (e.g. `'confirmed_partial'`) the set should be extended — flagged rather
   than guessed further.
2. **`provenance.manifest_id` is null by design**: the publication manifest
   read is P-4's capability; P-2's packet names the field but not the join.
   It ships null rather than a guessed query — wire it when P-4 lands.
3. **Authority COALESCE left in place** (packet §5 explicitly declines to
   change it here) — see REVIEW_REQUEST_P1 flag 3: the reading layer still
   falls back to `'v1'` where the serving tools now say `unpublished`.
   Cross-packet ruling needed.
4. Live-DB acceptance (disposable-DB fixture) is not runnable in this
   environment; tests are mocked-query per the file's existing convention.
