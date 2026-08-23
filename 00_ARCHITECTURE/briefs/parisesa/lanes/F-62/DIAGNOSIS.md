---
lane: F-62
stream: S6_ADHARA
stage: D (DIAGNOSE) — COMPLETE (backfilled onto adopted BRANCH-EXISTS work)
author: ADHARA-LEAD (sonnet)
---

# F-62 — dignity classification: missing/over-emitting moolatrikona tier, no shared oracle

## 1. Live reproduction / adoption status

Adopted, not re-diagnosed from scratch: `ekv/b-01-dignity-oracle` (5 pre-existing commits,
HEAD `dfbdfe620` before this session) already implements the fix. Both
`origin/ekv/b-01-dignity-oracle` and `origin/ekv/b-01-dignity-oracle-fix` pointed to the
identical commit `dfbdfe620` at session start — confirmed directly via `git log --oneline`
on both refs, not taken on faith. Per the plan-named branch, this session worked
`ekv/b-01-dignity-oracle` (the `-fix` ref is a duplicate pointer to the same content, to be
deleted at campaign close, never separately merged).

**New finding this session (not in the original corpus):** rebasing the adopted branch onto
`origin/main` (5ff46c2a0) produced an add/add conflict on
`platform/python-sidecar/brahmagyan/__tests__/test_dignity_oracle.py` — an unrelated PR
(#1297, "F-109 Rahu/Ketu aspects") had already merged a near-identical copy of this test file
to `main` (163/164 lines identical, one docstring wording difference), but **without**
`dignity_oracle.py` itself. Confirmed live: on `origin/main` today, `pytest
brahmagyan/__tests__/test_dignity_oracle.py` fails collection with
`ModuleNotFoundError: No module named 'brahmagyan.dignity_oracle'` — main's test collection
is currently broken by this ghost file. Landing F-62 fixes this incidentally (adds the
missing module). Flagging so INTEGRATOR/conductor knows this isn't a new regression F-62
introduces — it's a pre-existing main-branch break this lane happens to resolve.

## 2. Claim decomposition

Three sub-claims (confirmed against plan's own framing):
- **C1** — `ga_structural_writer.py` (`_build_varga_relationship_rows`, was line ~4872-4884)
  computed dignity from a local 4-way if/elif (exalted/debilitated/own/neutral) with **no
  moolatrikona tier at all**.
- **C2** — `ga_vargas_writer._compute_dignity` computed dignity from a local `DIGNITY_TABLE`
  that checked moolatrikona **before** own with **no degree gate** — MT fired for the entire
  sign, not just the classical degree range, over-emitting MT where classical rule says "own."
- **C3** — no shared oracle: the two writers (plus `bo_pratijna_v4_engine.dignity_of`) each
  had their own local dignity logic, structurally guaranteed to diverge over time (the
  general defect class CLAUDE.md §N.7 targets).

## 3. Mechanism (file:line, read directly)

- `platform/python-sidecar/ga_writers/ga_structural_writer.py` — dignity block was inline at
  (pre-fix) lines 4872-4884; fix replaces it with `classify_dignity(g_name, sign,
  get_degree(g_name))` imported from the new `brahmagyan/dignity_oracle.py`.
- `platform/python-sidecar/ga_writers/ga_vargas_writer.py::_compute_dignity` — pre-fix used a
  local `DIGNITY_TABLE` dict with sign-only (not degree-gated) MT comparison, checked before
  own. Fix delegates to the same `classify_dignity`, adds a `degree_in_sign` parameter
  threaded through all 3 call sites (`_build_dignity_rows`, `_build_vimsopaka_rows`,
  `_build_rollup_rows`), and Title-cases the oracle's lowercase result to preserve callers'
  existing string comparisons ("Exalted"/"Moolatrikona"/"Own"/"Neutral" — "Friend"/"Enemy"
  tiers from the old table are not produced by the oracle and were verified as unused by
  downstream comparisons before removal).
- `platform/python-sidecar/brahmagyan/dignity_oracle.py` (new) — single shared
  `classify_dignity(graha, sign_name, degree_in_sign) -> str`, priority order exalted →
  debilitated → node-early-exit → moolatrikona (half-open `[mt_from, mt_to)`) → own →
  neutral. **Updated (VERIFIER Stage R deficiency 1 — this note described a since-
  superseded state of the branch):** data source is no longer a static reproduction.
  Per PAR-R-6, `brahmagyan/l0_dignity_reference.py` (new, stdlib-only) is now the single
  Python source; `dignity_oracle._DATA` is derived from its `DIGNITY_REFERENCE` list via
  a dict comprehension, and `bg_dignity_reference.py` imports the same
  `DIGNITY_REFERENCE` object rather than declaring its own copy. **Verified this
  session** (not assumed): `bg_dignity_reference._DIGNITY_REFERENCE is
  l0_dignity_reference.DIGNITY_REFERENCE` (object identity, confirmed via a live
  Python check and asserted permanently by
  `test_data_matches_bg_dignity_reference_source_of_truth`), plus a second test
  (`test_l0_dignity_reference_matches_seeded_migration_250`) cross-checking the shared
  module against migration 250's actual seeded SQL rows.
- `platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna_v4_engine.py
  ::dignity_of` — third consumer, wired to the same oracle in the adopted branch.

## 4. Sibling census

**CORRECTION (post-CI):** the first pass of this census (manual grep, pre-CI) was
incomplete and said "none found beyond the three wired consumers." CI's `D-01b — No Local
Dignity Table` check caught two real sibling sites this session's manual grep missed:

1. **`ga_writers/ga_vargas_writer.py:135` `DIGNITY_TABLE`, used a second time at line
   ~1739 inside `_build_saptavargaja_rows`** — a wholly separate MT check
   (`sign_idx == dtab["mt"]`, no degree gate) from the one `_compute_dignity` fixed. Same
   defect class as C2, same file, different function. **Fixed this session** (see SPEC.md
   §2) — routed through `classify_dignity()` with real `degree_in_sign`. The "own" lookup
   a few lines below the MT check still reads the local `DIGNITY_TABLE` dict directly
   (pure static sign-membership data, no degree gate applies) — left as-is, residual noted
   in SPEC.md §5. D-01b will still flag this file for that reason; the substantive
   classical-accuracy bug (missing degree gate) is closed.
2. **`brahmagyan/ganita/l1_strength.py:65` `PLANET_DIGNITY`** — a fourth, previously
   unknown consumer, used for Shadbala Sthana Bala (BPHS Ch.27). **Not fixed in this
   PR — correction to the exclusion reason (VERIFIER Stage R deficiency 2):** this was
   originally flagged as "out of S6's lease." That reason is now false:
   `LEASES.json`'s `S6_ADHARA.owns` array was updated post-Phase-0 to add exactly this
   file ("4th dignity-oracle consumer site found during F-62 build, kept with the same
   team already touching the other 3 sites"). The lease is granted; the real reason it
   stays unfixed here is the one already named below and left undecided — a genuine
   open classical-semantics question, not a routing/ownership question. Tracked as an
   explicit follow-up lane in `lanes/F-62/SPEC.md` §4 rather than silently dropped now
   that the lease question is resolved.
   Sthana Bala's own moolatrikona handling should be checked against the same degree-gate
   question (does BPHS's Sthana Bala also want a degree-gated MT distinct from own-sign
   credit, or does classical Shadbala treat MT as sign-wide there? — not determined this
   session, needs its own diagnosis).

## 5. Blast radius

- CL-00: none of the 27 controls are dignity-specific; this lane does not touch CL-00
  directly, but per plan §5 "F-62 must land before any Ṣaḍbala-consuming lane in any stream
  re-tests" — Ṣaḍbala scoring consumes dignity classification downstream.
- Test suite: `platform/python-sidecar/tests/test_ga6_writer.py` has **131 pre-existing
  failures on `origin/main` today**, confirmed unrelated to this lane (identical failure
  count/set reproduced on a clean `origin/main` worktree before any F-62 changes were
  applied) — not introduced or worsened by this branch. Flagging for the conductor as a
  separate, out-of-scope corpus item; not touched here.
- CI: `D-01b — No Local Dignity Table (WARN)` is a real, already-existing advisory lint in
  this repo's CI (`EKV — Ekavākyatā Lint Gates`, Stream D battery) that appears designed to
  catch exactly the local-copy pattern in `dignity_oracle.py._DATA`. It is WARN-only
  (non-blocking) — see SPEC.md §6 for disposition.
