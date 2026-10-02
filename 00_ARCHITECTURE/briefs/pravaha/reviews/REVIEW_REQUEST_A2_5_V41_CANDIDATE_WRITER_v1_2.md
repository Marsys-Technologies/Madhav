---
artifact: REVIEW_REQUEST_A2_5_V41_CANDIDATE_WRITER
version: "1.2"
author: "Stream A (Karma) — Kimi Code"
date: "2026-10-01"
subject_pr: "#2799"
reviewed_commit: cb004ff00
authority: "Review request only; authorizes nothing. Reviews are the steward's to dispatch (PRAVAHA_EXECUTION_ARCHITECTURE §5.10)."
---

# Review request — PR #2799: ka_gochara_v4_41_candidate ('4.1' candidate chain inside the governed pipeline)

**Head under review:** `cb004ff00` (branch `pravaha/a25-v41-candidate-writer`), which is PR #2799's
original changeset **plus** merge commits `92bf58a43` (#2769 `fedc5ae50` merged in) and `eab8c67d2`
(`origin/main` through `8bb37e482` merged in), **plus** `cb004ff00` (test-isolation fix, below),
per steward M20261001T015033-e3a8. **CI green on `cb004ff00`**: Ganga Quality Gate (run
36824880749), Deploy to Cloud Run (36824880743), TAP CI, EKV all success.

**v1.1 addendum — `cb004ff00`:** the merge-round CI caught a test-isolation defect in the PR's
own new test file: `os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")` in
`test_dispatch_single_transaction_committed_end_state_is_inert` leaked process-wide, so CI's
DB-gated tests (b1_forensic_gate, r6a1, r6a3, dhara_parity ×3) attempted connections to host
'fake' instead of skipping (7 failures in Governance Gates on `eab8c67d2`). Fixed by set+restore
scoped to the test; proof: the four victim files run in the same pytest process with
DATABASE_URL unset — 66 passed, 7 skipped (previously 7 failed). Production code untouched by
this commit. (The bo_bimba Governance-Tool-Tests failure seen on main at `8bb37e482`/`088d7dc5e`
did NOT reproduce on this branch's green run.)

## 1. What the PR does

Runs the `'4.1'` gochara **candidate** chain (`scripts/kala_gochara_cutover` step06 enumerate →
candidate build → class context → windows projection) as a governed heavy writer inside
`brahma-build-pipeline-job`, replacing the deleted bespoke Cloud Run job. Steward decision
M20260930T195042-a4a0 (Option A); all five ratification conditions implemented.

- New writer `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py`
  (399 lines). Parameters live in the asset identity (`ctx.config` untouched): generation fixed
  `'4.1'` (candidate only), horizon fixed `[1998-01-01, 2026-04-18)`. Substeps `manifest` →
  `body:<Body>` ×8 → `windows`, each idempotent delete-then-insert scoped chart × `'4.1'` ×
  sub-span, all on `ctx.db_conn` — the writer never commits/closes/opens a connection
  (source-guarded by tests).
- step06 conn-injection: `enumerate_core`, `build_candidate_core`, `build_all_class_contexts`,
  `project_windows_core` take an injected connection; every CLI `main()` keeps its own
  connect/commit/close and exit codes (byte-identical behaviour, source-guarded).
- `gochara_kernel/ledger.py`: `write_contacts`/`write_coverage` gain optional `bodies=` scope
  (default byte-identical); per-body substeps replace exactly their own rows; foreign-body
  payloads refuse.
- Candidate-only, three undefended-in-depth layers, none weakened: ledger
  `_require_not_published`/`publish_candidate` refusals; serving-side
  `AUTHORITATIVE_GENERATION_FILTER` (this writer never touches `kala_gochara_authority`, never
  calls `ledger.publish()` — source-guarded); DB generation guard trigger (v1/'3.0' rows
  untouchable).
- `platform/scripts/dispatch_a25_v41_candidate_job.py` — stages the registry row idempotently,
  single-transaction `is_active` flip (UPDATE true → stage → UPDATE false → one COMMIT; no other
  session ever observes `is_active=true` under READ COMMITTED), forces throughput dormant,
  inserts an `asset_set` build_run naming only this asset. **Ships in the PR but runs ONLY on
  steward go**, after merge + a green main deploy. Teardown DELETEs in `--help`.
- Seed row `asset_registry_seed.ts` (`ka_gochara_v4_41_candidate`, sort_order 141,
  `is_active: false`, `depends_on: []`) — inert to all planners.

## 2. Merge resolution over #2769 (steward condition)

Resolved by keeping #2769's reviewed logic and re-applying the conn-injection on top. Evidence:

- `tests/l3/gochara` + `test_ka_gochara_resonance.py` + `test_resonance_rebuild_rehearsal.py`:
  **735 passed, 84 skipped, 9 xfailed** (10.08s) on `eab8c67d2`. #2769's resonance/vedha/dasha
  suites pass unchanged.
- `pipeline/orchestrator`: **1179 passed, 67 skipped** (13.38s).
- Two #2769 test files carry disclosed, semantics-preserving adaptations (both pass):
  - `test_vedha_interval_gate.py` — the source guard now inspects `project_windows_core`
    (the executable path) instead of the thin `main()` wrapper; same `make_vedha_gate(vedha_rows)`
    assertion.
  - `test_step06b_per_instant_permission.py` — two AST source guards retargeted from `main` to
    `project_windows_core` / `build_all_class_contexts` for the same reason; assertions
    unchanged.
- Committed `platform/src/generated/nirmana-analysis-layer-pins.json` on the branch is
  **byte-identical to `origin/main`'s** (protected baseline untouched).

## 3. Needs native ruling

**`SUPPORTING_WRITER_IDS` addition.** `platform/scripts/__tests__/asset_registry_seed_dag_parity.test.ts:131`
adds `ka_gochara_v4_41_candidate` to `SUPPORTING_WRITER_IDS` (alongside `bo_grounding`). The
D-NATIVE-11 comment at that site states: *"Adding a name here requires its own native ruling."*
The addition was steward-directed (M20260930T195042-a4a0, Option A); the reviewer should confirm
the implementation matches the ruling's intent (128-identity denominator unchanged; supporting
writers registered but never planned), and the steward is asked to route the ruling itself to the
native.

## 4. Question for the reviewer — cockpit inactive row

The seed row is `is_active: false` with `has_writer: true, has_substeps: true`. Claimed inert:
`runPreparation.ts:183` (`WHERE is_active = true`) and `recalibrationEnqueue.ts:141`
(`is_active = true AND has_writer = true`) never select it. **Please verify independently:**
(a) no planner/scheduler/enqueue path picks up an inactive row; (b) the cockpit/AssetRow surfaces
render (or filter) an inactive, never-built candidate row without breaking; (c) the dispatch
script's single-transaction flip really is unobservable to other sessions and restores
`is_active=false` on every failure path (round-2b amendment `231ea9c34`).

## 5. Governance open item (flagged to steward, does not block review)

The PR adds a **new L3 writer** — a pins membership change. The committed pins file is
byte-identical to main's, so the L3 inventory derived from the branch tree (23 `ka_` writers)
diverges from the pinned 22-writer inventory. CI does not run the pins check
(NIRMANA-SUPERSESSION), but admitting the L3 successor requires a steward decision
(D-PINS-A2.5 or equivalent) before merge, on the D-PINS-A5.4 precedent. Stream A has **not**
self-admitted; this is reported to the steward alongside this packet.

## 6. What is NOT in this PR

No dispatch, no production write, no flip. The `'4.1'` build runs only on steward go after merge
+ a green main deploy puts the writer in the job image. No local century enumeration (ADK-0028).

## 7. Suggested review focus

1. Writer substeps' idempotency and scope (chart × `'4.1'` × sub-span delete-then-insert on
   `ctx.db_conn`; never-commits proof).
2. Conn-injected step06 cores: CLI `main()` byte-identical behaviour; ledger `bodies=` default
   byte-identical; foreign-body refusal.
3. Candidate-only layering: nothing in the PR can make `'4.1'` reachable by serving or flip
   authority.
4. Dispatch script: staging idempotency, live no-dependents check, single-transaction flip,
   dormant-throughput forcing, teardown completeness.
5. §3 (native-ruling surface) and §4 (cockpit inactive row) above.

## 6. Pins admission (D-PINS-A2.5, 2026-10-01)

Successor: **`l3:639eece63be3:df2b966b1d97`** — ONE L3 successor over main's protected baseline
`l3:4f4a1993c6ad:1ddd6f117934` (archived whole, never rewritten), admitting the ONE membership
change the PR carries: `ka_gochara_v4_41_candidate` (`approved_intentional_change`; every other
writer's digest unchanged, verified from content-hashed closures of the merged tree vs
`origin/main`). Authority evidence:
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_PINS_A2_5_PINS_READMISSION_AUTHORITY_v1_0.md`
(authority commit `2292ee6b0cebceedc6fdaa80f0fd428e04231c65`; the steward's decision
M20261001T064616-8eed quoted verbatim). Generator authorization entries:
`AUTHORITY_BINDINGS["D-PINS-A2.5"]`, `AUTHORIZED_SOURCE_COMMITS["D-PINS-A2.5"]["L3"] =
{639eece63be38a27fb9840ee778beb4c6c1459fd}`, and `SUPPORTING_WRITERS +=
ka_gochara_v4_41_candidate` (the membership exclusion — see §3, needs native ruling).

Verification:
- Offline `--check` on the branch: residual lines identical to main's plus the analogous
  artifact-ancestor line for the new successor (main itself carries 56 pre-existing L5/L3
  artifact-ancestor lines).
- Delivery-topology squash-sim onto `origin/main` (`2b3e09673`), `--check
  --protected-baseline-commit 2b3e09673 --delivery-topology`: **residual lines byte-identical
  to main's** (L1/L2 pre-existing staleness; no L3 line).
- Pins pytest delivery mode (`NIRMANA_ANALYSIS_PIN_BASELINE_COMMIT=2b3e09673,
  NIRMANA_ANALYSIS_PIN_DELIVERY_TOPOLOGY=1`): **90 passed, 3 skipped, 1 failed** — the one
  failure is main's own pre-existing `readmission_classifications[L1]` (main in the same mode:
  4 failed). The receipts test re-base (rewind convention) adds the `A25_MERGE_REWINDS`
  generation and six a25 tests pinning the successor.
- Census refreshed with `--source-revision` = admission commit `348c8e7fc`.

**§6 addendum (head `1dbb07ef6`):** the admission's first CI round caught the deploy Build Check's
import-time gate (`Expected 23 frozen L3 analysis receipt bases; found 24`) — the generated
receipts module needed the same supporting-writer exclusion. Fixed in `1dbb07ef6`:
`NIRMANA_SUPPORTING_WRITERS += ka_gochara_v4_41_candidate` (D-NATIVE-13 pattern; same §3 native
ruling surface), plus the receipts test re-base: `history.L3` is 9 and the A5.4 successor is
now the archived r7 entry at -1 with its true identity (`l3:4f4a1993c6ad:1ddd6f117934`, source
`4f4a1993c6`) — main's file was stale by one generation since the r7 admission; repaired here,
and a D-PINS-A2.5 test pins the live successor. Module import verified throw-free (tsx;
offline receipt bases 0, same as main). Squash-sim re-verified after the fix: pins residuals
byte-identical to main's; pins pytest delivery mode 90p/3s/1f (main's own L1).
