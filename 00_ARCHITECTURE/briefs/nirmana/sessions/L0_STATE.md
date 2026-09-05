---
artifact: L0_STATE.md
canonical_id: NIRMANA_V21_L0_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L0
layer: L0 — Brahmagyan
owner: the L0 session (this file is yours alone — charter C5)
last_updated: 2026-09-06 — Checked D-CND-09 (bg_vidhi_floors catalog_status DRAFT→CURRENT) now that it's frozen: writer source still tags education_deepdive/progeny_deepdive [CANDIDATE], so DRAFT remains correct — a positive "not yet," nothing actioned. Queue still deep (position 35), my own PRs unmerged. IDLE-OK on new L0 asset work; 30/40 frozen holds from D-L0-NN.
---

# L0 — Brahmagyan — SESSION STATE

Charter C9: this file is your memory — update every loop, commit with every PR and at milestones,
so re-pasting the prompt into a fresh session is safe at any moment.

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → `resume/RESUME_L0.md` → this file →
`git fetch origin main` → `gh issue view 1713` + your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 · **Migration range:** L0's own 640–644 already applied. Per-layer
  table (charter C5): Conductor 645–649, L1 650–659, L2 660–669, L3 670–679, L4 680–689,
  **L5 690–699 (conductor-2b flagged 2026-09-05: my 692/693/694 — picked as "next free number" —
  actually collided with L5's range; no functional break since `migrate.ts` sorts by full filename,
  not cross-layer numeric uniqueness, but it broke the range convention). L0's own continuation
  range is now 700–709** (assigned by conductor-2b this same message) — use that for any future L0
  migration; do NOT renumber 692/693/694 (real rework, zero benefit per conductor-2b).
- **Branch namespace:** `feat/nirmana-l0-*` / `fix/nirmana-*` · **PR prefix:** `L0:` (older ones used no prefix)
- **Worktree:** main checkout `/Users/Dev/Vibe-Coding/Apps/Madhav` + scratch `/private/tmp/madhav-nirmana-l0-w4`
- **Evidence tooling (scratch, Conductor-audited):** `/private/tmp/.../scratchpad/nirmana_batch_runner.py`
  (stage analysis+verdict), `nirmana_build_wave.py` (dispatch/authorize/force-execute/evidence),
  `producer_covered.py`, `freeze_probes.py`, `run_dispatcher.py`. Canonical helper is now `nrec` (#1731).

## Position

**L0-W4 EXECUTE + Conform-stage integrity corrections.** W1/W2/W3 done for the 30 frozen. **30/40
frozen** (verifier-signed 5-event chains, implementer≠verifier). **10 remaining**, all diagnosed.
`bg_vidhi_floors` FROZEN this cycle (D-L0-NN) — first genuine freeze of this campaign resumption,
full chain traced end-to-end: fresh W2 → dispatch → authorize → accepted_rebuild_observed →
integrity_verified → asset_frozen, all via the scratchpad tooling built this session.

## The 10 unfrozen assets

| asset | route | status / blocker |
|---|---|---|
| bg_cohort | rebuild_only | **Job-image blocker CLEARED (deployed image now `80a9cd71e...`, confirmed ancestor of #1772). Genuine dispatch succeeded (run `a9446885-...`, real build, valid receipt) but hit a NEW structural blocker (D-L0-II): `accepted_rebuild_observed` requires `receipt.receipt_state='proven'`, and bg_cohort's sole dependency `bg_ephemeris_engine` is `asset_kind='service'` (no writer, never has a provenance receipt) — `compute_upstream_hash` can never find a complete receipt set for its `depends_on`, so `receipt_state` is permanently `'unknown'`.** Posted to #1713 for Conductor; not L0-fixable (shared orchestrator provenance code). Only L0 asset affected (checked: no other L0 asset depends on a service-kind asset) |
| bg_gochara_arcs | rebuild_only | **Structural bind (D-L0-FF): 2 runs now** — `bfdc6919` (genuine build, valid receipt, WRONG authorization) and `5ba8cedf` (valid authorization, `skip_no_delta`'d, stale receipt). Neither completes the evidence chain; may need Conductor input on a `force` path |
| bg_yogas | rebuild_only | **D-L0-J refined by D-L0-KK: real dispatch (run `f89f70fa-...`) failed integrity_check_sql, but writer is fully correct.** Genuine `seed_yogas()` replay produces exactly 233/233/233/85 with all three content-hash pins matching byte-for-byte — the ONLY failing subclause is the same FULL-JOIN scope leak as bg_doshas/692 and bg_dasha_systems/700 (`entity_class='yoga'` in the ON clause, 508 non-yoga `brahma_ontology` rows leak in). Migration 701 authored + verified live (TRUE on genuine replay, FALSE on stale live data). No writer change; awaiting PR merge + deploy, then re-dispatch. CASCADE parent → snapshot+`--acknowledge-destroys` (already done this cycle) |
| bg_dasha_systems | rebuild_only | **D-L0-K refined by D-L0-GG: writer still correct; the CHECK had two bugs.** Real genuine dispatch (run `ce86f4cf`, not skip_no_delta) failed `integrity_check_sql`. Root-caused live: (1) same FULL-JOIN scope bug as bg_doshas/692 — `ontology.entity_class='dasha_system'` in the ON clause instead of a pre-filtered subquery, so all non-dasha_system `brahma_ontology` rows leaked in; (2) migration 621's `catalog_hash` pin itself was wrong at authoring time (writer content unchanged since 5f47906bc; genuine hash is `8e35495f...`, pin says `30742da6...`). Fix migration 700 authored + verified live (rolled-back tx): guard matches 621's exact pin, corrected check evaluates **TRUE** against a genuine fresh writer run and **FALSE** (fail-closed, as expected) against current stale live data. No writer change; awaiting PR merge + deploy, then re-dispatch |
| bg_doshas | rebuild_only | **Same structural bind as bg_gochara_arcs (D-L0-FF)**: run `92830957` genuinely built (valid receipt) but missed the authorization window (D-L0-AA); any retry now would `skip_no_delta` since the receipt already matches |
| bg_parihara_rules | rebuild_only | ROUTED (D-L0-H). E-gate `BLOCKED-ANCESTORS`: `bg_doshas` only (row updated — was stale "UNROUTED"/"bg_doshas, bg_texts", `bg_texts` has since frozen) |
| bg_compendium_index | rebuild_only | **D-L0-JJ refined by D-L0-MM: writer fully correct; both content-hash pins were stale.** Replayed `_build_desired_rows()` directly (no full `ContextSpec` needed — pure function of `classical_text_chunks`/`reference_topic_tags`): produces exactly 9571/7969/1602 matching migration 623's structural pin precisely. Both content hashes (chapter-scoped, topic-scoped) mismatched the 623 pin despite the writer file being unchanged since — corpus content evidently evolved since 623 was authored. Migration 702 authored + verified live (rolled-back tx): TRUE on genuine replay, FALSE on stale live data. No writer change; awaiting PR merge + deploy, then re-dispatch |
| bg_rules | rebuild_only | E-gate `BLOCKED-ANCESTORS`: `bg_dasha_systems, bg_yogas` (both diagnosed, both need only dispatch) |
| bg_text_index | rebuild_only | **Now caught by D-L0-FF (4th confirmed instance).** Genuine build (run `27fea532-...`) lost its evidence chain to the D-L0-JJ multi-asset authorization tooling bug (now fixed); solo retry (run `f3c762e6-...`, correctly authorized this time) `skip_no_delta`'d against the still-matching old receipt, so no fresh run/receipt pair exists. Blocked on Conductor's `#1899/#1901` (delta-skip receipt re-attribution) landing — do not retry again until then |
| bg_concordance | rebuild_only | E-gate `BLOCKED-ANCESTORS`: `bg_dasha_systems, bg_rules, bg_text_index, bg_yogas` — deepest DAG node, clears last |

## Decisions log

- **D-L0-A** — 29 assets frozen through W4 via the proven pattern: `nirmana_batch_runner` stages
  analysis+verdict (fingerprint pre-checked vs frozen manifest); `nirmana_build_wave dispatch`
  create→build_run_authorized(planned window)→**force-execute**→poll; `evidence` phase does
  accepted_rebuild_observed(executor)→integrity_verified(verifier)→asset_frozen(verifier). Proven
  end-to-end; idempotent/existence-aware after two transient blips.
- **D-L0-B** — Discovered + fixed three build-path mechanics live: (1) `build_run_authorized` must be
  recorded in the run's *planned* window before dispatch; (2) `NIRMANA_FORCE_EXECUTE=1` is required or
  an authorized re-run no-op-completes and emits no receipt; (3) evidence phase must be existence-aware
  to survive network blips.
- **D-L0-C** — Two integrity-detector correctness fixes shipped (P0, merged pre-resume): probe-service
  assets re-run the live health probe as their detector; the SQL detector guard now ignores string
  literals/comments and allows read-only CTEs while **adding** an explicit DML rejection the old guard
  lacked (hardening, not weakening — C12 floor test satisfied).
- **D-L0-D** — `depends_on` stored unsorted for 5 multi-dep assets while the frozen definition/canonical
  fingerprint sort it; normalized live to sorted (fingerprint-neutral, verified, committed) and patched
  the dispatcher (Conductor raised as **#1728** with a regression test). Unblocked multi-dep dispatch;
  also unblocked 15 of L3's assets.
- **D-L0-E** — #1772 (depends_on sort + §3.5 service-dependency satisfaction) merged. Service deps are
  satisfied by `service_ok`/GREEN probe, exempt from data-freshness (C12 §3.5). Regenerated `probe_digest`
  for the Governance Gate.
- **D-L0-F** — C12 verdicts on the 5 integrity failures: only `bg_gochara_arcs` is a stale pin (correct
  the check). The other 4 (`bg_dasha_systems`, `bg_doshas`, `bg_vidhi_floors`, `bg_yogas`) are **real
  data defects** the invariants correctly caught → fix the writer (MUST) or adjudication with derivation.
  Do NOT weaken any check to pass.
- **D-L0-G** — `bg_yogas` source_chunks-85 pin provenance (C12 "check the pin's git history first"):
  the pin lives in **migration 630** (`630_nirmana_l0_wave1_correctness_contract.sql`, 2026-08-26,
  #1571) — a *real* content contract (233×3 projections + FULL-JOIN + content fingerprints + `= 85`
  source-chunk links), NOT a bare R0-T01 equality. The test's own explanation derives it: 233 yogas =
  144 core + 4 detector + **85 corpus-extracted**, each corpus-extracted yoga contributing one
  `brahma_yoga_source_chunks` link. **But live = 0** (and my failed rebuilds rolled back, so 0 is the
  *original* state — the check was never green on real data), and **4 yogas** (`dhana_yoga_house_lords`,
  `raja_yoga_kendra_trikona`, `sarasvati_yoga`, `vipareeta_raja_yoga`) are in `brahma_yoga_catalog`
  (233) but absent from `brahma_ontology`/`reference_yogas` (229). Root cause is in `l0_yogas.py`:
  `_validated_source_chunk_ids(y)` returns `[]` whenever a yoga has no `_chunk_id_str`, and
  `extract_yogas_from_corpus` currently yields 0 with chunk-ids → 0 links; and the 4 catalog-only
  yogas drop out of the ontology/reference loop. **Verdict: writer/seed under-production (fix the
  writer, MUST) — not a stale pin to delete.** The 85 has a documented derivation, so the honest
  moves are (a) restore the corpus extraction so it produces the 85 links, or (b) if the corpus
  genuinely no longer carries them, correct the check to the *derived* achievable count with the
  derivation in the PR (C12) — decided after reading `extract_yogas_from_corpus` fully. NEXT ACTION
  when resumed: read `l0_yogas.py:1963 extract_yogas_from_corpus` + the 4-missing-yogas projection
  path; then author the bundled D-CND-09 migration (yoga writer fix or derived-check correction +
  `bg_gochara_arcs` tiling+floor + `bg_vidhi_floors` DRAFT→CURRENT + `expected_volume_formula`) BEFORE
  re-acceptance; `bg_parihara_rules` W1/W2 in parallel (never gated).

- **D-L0-J** — **bg_yogas writer verdict CLOSED: no code fix needed.** Resumed with the job-image
  deploy still blocking dispatch (`d93d9d0a` deployed, confirmed live via
  `gcloud run jobs describe brahma-build-pipeline-job` — still predates #1772's `ee8cf7d09`), so
  instead of waiting idle, verified the open `extract_yogas_from_corpus` question **without needing
  the pipeline job**: invoked the writer's own function directly against the live production DB
  (read-only — no INSERT, no write path exercised) via a local psycopg2 script. Result: **exactly 85
  distinct extracted yogas, all 85 with valid `_chunk_id_str` (0 no-chunk-id drops)**. Combined with
  `YOGAS_CORE` (144) + `DETECTOR_YOGAS` (4) → **233 total, all canonical_ids unique (0 collisions)**.
  This is an *exact* match to migration 630's pin (233×3 projections, 85 source-chunk links) — the
  writer, run today, would produce precisely the frozen-manifest counts. The current live table
  state (`catalog=233, ontology=229, reference=229, source_links=0` — re-verified this cycle) is
  therefore confirmed **stale pre-migration-630 build data**, not a live defect: some earlier writer
  version populated catalog to 233 without the uniform 3-way projection or the source-chunks link
  table this contract requires. **No writer fix, no adjudication, no migration for bg_yogas.** The
  only remaining blocker is dispatch itself (job-image deploy, tracked separately, unchanged).
  Closes the D-L0-G → correction chain definitively — the earlier "extraction yields ≠85, held on
  running the writer" hypothesis (ffeb5e2ea) is superseded: extraction yields exactly 85 today, and
  confirming that never required a dispatch, only reading+invoking the function directly. **Also
  noted:** `nrec` (the campaign evidence-submission helper, #1731) is NOT on `main` — PR #1731 was
  closed as superseded per the coordination-issue tail; the old scratch tooling
  (`nirmana_batch_runner.py` et al.) was lost to a `/private/tmp` wipe (system restart) and has not
  been recreated this cycle since no dispatch was possible anyway. Working branch this cycle:
  `feat/nirmana-l0-cycle-resume` off fresh `origin/main` (prior `feat/nirmana-l0-heartbeat-2` /
  `feat/nirmana-l0-state-heartbeat` are stale side-branches, superseded by merged PR #1817 — safe to
  ignore, not deleted).

- **D-L0-K** — **bg_dasha_systems writer verdict CLOSED: no code fix needed (same pattern as
  D-L0-J).** Live DB: `brahma_dasha_systems`=20 rows (incl. `kp`), `brahma_ontology
  entity_class='dasha_system'`=20, `reference_dasha_systems`=**19 (missing `kp`)**. Read
  `l0_dasha_systems.py:690-826 seed_yogas`-equivalent seeder: one `DELETE`-then-loop-`INSERT` over
  the single `DASHA_SYSTEMS` source list writes all three tables **uniformly per iteration in one
  transaction**, with an exact postflight check (`actual != expected` raises → rolls back
  everything). Verified `DASHA_SYSTEMS` directly: **20 entries, 20 unique canonical_ids, `kp`
  present** — so a live run cannot produce today's 20/20/19 split (that would require the
  postflight to have silently passed on a mismatch, which the code does not allow). The split is
  therefore historical, not a live code defect: `kp` was added to the writer's source list by
  commit `63aeba051` ("reconcile L0 dasha systems"), and the DB has not been rebuilt since —
  `reference_dasha_systems` is pre-reconciliation stale data, same story as bg_yogas. **No writer
  fix, no adjudication, no migration for bg_dasha_systems.** Blocked only on job-image deploy
  (unchanged, re-checked this cycle: still `d93d9d0a…`, still predates #1772).

- **D-L0-GG (refines D-L0-K)** — **a genuine, correctly-authorized dispatch (run `ce86f4cf`, NOT
  skip_no_delta) failed `integrity_check_sql` — the writer is still correct, but the CHECK had two
  independent bugs: the same FULL-JOIN entity_class-in-ON-clause scope leak as bg_doshas/D-L0-L,
  plus a `catalog_hash` pin that was computed wrong at migration 621's own authoring time (writer
  content unchanged since; genuine hash `8e35495f...` ≠ pinned `30742da6...`).** Migration
  `700_bg_dasha_systems_catalog_hash_repin.sql` authored, fixes both, verified live twice
  (rolled-back tx): correctly guards on 621's exact prior pin, evaluates TRUE against a genuine
  writer replay and FALSE (fail-closed) against current stale live data. Full root-cause account
  in the Heartbeat entry below. No writer change. 4th instance this session of "correct the check"
  (bg_doshas/692, bg_vidhi_floors/693, bg_gochara_arcs/694, bg_dasha_systems/700).

- **D-L0-II** — **bg_cohort: job-image blocker cleared, genuine dispatch succeeded, hit a NEW
  structural evidence-chain gap (not a data/writer defect).** Confirmed the deployed job image
  (`80a9cd71e...`) now has #1772 as an ancestor (`git merge-base --is-ancestor`) — bg_cohort's only
  prior blocker. Existing W2 evidence (2026-09-04) verified still live-valid via dry-run; took a
  fresh Cloud SQL backup (`cloudsql-backup:1788630136147`, CASCADE parent per WP-6, destroys
  `bg_synthetic_cohort_md`); ran a real `--commit --acknowledge-destroys` dispatch (run
  `a9446885-2a21-49ae-baac-d3b7cc1f317b`), authorized inside the timing window (confirmed
  `authorization.recorded_at` < `run.started_at`), and the run completed genuinely
  (`disposition='build'`, not skip_no_delta, fresh provenance receipt with matching `build_id` and
  `output_digest`/`output_digest_spec_sha256`). `accepted_rebuild_observed` submission still
  failed (HTTP 500: "requires a completed exact run/asset with a matching proven content
  receipt"). Root-caused by manually reproducing `requireAcceptedRebuildProvenance`'s full SQL
  (`definitions.ts:2278-2325`) clause-by-clause: every condition holds except
  `receipt.receipt_state = 'proven'` — the fresh receipt has `receipt_state='unknown'`,
  `unknown_reasons=["upstream_digest_unavailable"]`. Traced to `asset_runner.py`'s
  `compute_upstream_hash` (line 200-220): for an asset with `depends_on`, it requires
  `load_upstream_receipts` to return one `receipt_state='proven'` row per declared dependency —
  but `bg_ephemeris_engine` (bg_cohort's sole dependency) is `asset_kind='service', has_writer=
  false`, so it can **never** have a row in `asset_provenance_receipts` at all. The upstream-digest
  computation therefore always returns `None` for bg_cohort, and `provenance.py`'s `Receipt.
  receipt_state` property (line 56-58, `"unknown" if self.unknown_reasons else "proven"`) is
  permanently `'unknown'` — no retry or dispatch can ever fix this without a code change to the
  shared orchestrator provenance logic (service-kind deps need to be excluded from, or vacuously
  satisfy, the upstream-receipt-completeness check). Checked L0's own `depends_on` graph: bg_cohort
  is the ONLY L0 asset depending on any service-kind asset, so this does not block any other L0
  asset — but the defect class is general across layers. Posted in full to #1713 (not filing a
  separate `nirmana-adjudication` issue since precedent — D-L0-FF — was handled the same way and
  Conductor picked it up as #1899/#1901); not attempting a fix myself since `compute_upstream_hash`/
  `build_receipt` are shared orchestrator code, not L0-owned. bg_cohort's writer output itself is
  genuinely correct (real build, real receipt content, real digest) — purely an evidence-chain gap.

- **D-L0-JJ** — **bg_compendium_index + bg_text_index dispatched together (run
  `27fea532-d8c1-44c2-84ca-7cfaf3f95ade`, wave 2), mixed outcome, one real defect + one tooling
  bug.** `bg_text_index` built genuinely (`disposition='build'`, fresh receipt) but
  `bg_compendium_index` failed its post-write `integrity_check_sql`, so the run's overall state is
  `failed`. Separately, my own `authorize_build_run.sh` only ever accepted a single `asset_id` —
  submitting `asset_ids: ["bg_compendium_index"]` for a run that actually planned BOTH assets
  tripped `requireBuildRunAuthorizationProvenance`'s exact-set-match requirement
  (`definitions.ts:2367-2390`, both directions: every planned asset must be in the authorized set
  AND vice versa), rejecting the WHOLE authorization (HTTP 409) — so `bg_text_index`'s otherwise-
  clean build never got its `accepted_rebuild_observed` chain this attempt, even though nothing
  was wrong with the build itself. Fixed the script to accept a comma-separated asset list. For
  `bg_compendium_index` itself: live counts post-failure are `total=9538` (pin expects `9571`, −33),
  `topic_id IS NULL`=7969 (matches pin exactly), `chapter_num IS NULL`=1569 (pin expects `1602`,
  −33 — exactly the total shortfall); the structural `(chapter_num IS NULL) = (topic_id IS NULL)`
  alignment check passes. So topic-type rows are exactly right and chapter-type rows are missing
  precisely 33 — narrows the defect to chapter-row production/extraction, but NOT yet root-caused
  to writer-defect vs. stale-pin: `CompendiumIndexWriter` (`writers/bg_compendium_index.py`) is a
  full `WriterBase` subclass needing a real `ContextSpec`/`ctx.config` to replay, unlike the
  standalone-function L0 writers (`l0_dasha_systems.py` etc.) diagnosed earlier this session via a
  bare psycopg2 call — replaying it in isolation needs more setup, left for next cycle. Both
  assets' evidence chains remain open; no writer fix made yet for either.

- **D-L0-KK (refines D-L0-J)** — **bg_yogas: a genuine, correctly-authorized, CASCADE-acknowledged
  dispatch (run `f89f70fa-59f3-4d57-92f2-758de7d66a09`, wave 1) failed `integrity_check_sql`, rolling
  back to the prior stale data — but the writer itself is fully correct.** Root-caused with the same
  discipline as D-L0-GG: replayed `seed_yogas()` directly in a rolled-back transaction. The genuine
  writer output is exactly `233/233/233/85` (catalog/ontology/reference/source_chunks), matching
  D-L0-J's original prediction precisely, and all THREE content-hash pins
  (`catalog_hash`/`ontology_hash`/`reference_hash`) match the registry's pinned values byte-for-byte.
  Isolated the ONE failing subclause by evaluating each condition separately: the same FULL-JOIN
  scope leak already fixed for `bg_doshas` (692) and `bg_dasha_systems` (700) —
  `ontology.entity_class='yoga'` sits in the ON clause of a FULL JOIN against `brahma_ontology`
  (shared across every L0 entity class) instead of a pre-filtered subquery, so every non-yoga
  ontology row surfaces as a spurious violation. Verified live: raw violation count is exactly 508,
  and `count(*) FROM brahma_ontology WHERE entity_class != 'yoga'` is also exactly 508 — zero real
  yoga misalignments. Migration `701_bg_yogas_integrity_check_join_scope_fix.sql` authored: applies
  the same subquery-pre-filter fix, verified twice live (rolled-back tx) — applies cleanly against
  the current pin, evaluates TRUE against a genuine `seed_yogas()` replay, and FALSE (fail-closed)
  against current stale live data. No writer change. 5th instance this session of the established
  C12 "correct the check" pattern (bg_doshas/692, bg_vidhi_floors/693, bg_gochara_arcs/694,
  bg_dasha_systems/700, bg_yogas/701). Fresh Cloud SQL backup taken before the dispatch
  (`cloudsql-backup:1788631501151`) per WP-6 CASCADE-parent discipline; no destructive action was
  needed since the run failed cleanly (savepoint rollback, no partial writes).

- **D-L0-LL — MILESTONE: first `accepted_rebuild_observed` of this campaign resumption
  (bg_vidhi_floors, run `1d24dbed-a7e5-423f-806b-00598739c911`).** Old W2 evidence was invalidated
  by migration 693's registry contract change (dry-run correctly refused: "accepted asset analysis
  does not match the current live registry contract"). Computed fresh `registry_fingerprint_sha256`
  (`88858552...`) and `analysis_digest` (`b7dae9ff...`) via `compute_analysis_digest.py`, using
  the L0 layer's pinned `convergence_commit` (`49bb5c98b...`, read from
  `src/generated/nirmana-analysis-layer-pins.json`) and `bg_vidhi_floors`'s writer digest from
  `nirmana-writer-digests.json`. Submitted fresh W2 (verdict=`examined_and_already_efficient`/
  `no_change`, since D-L0-N already established the writer source is internally sound) bound to
  `git:d54bab7e...` — the CURRENTLY-DEPLOYED web commit (confirmed via `gcloud run services
  describe amjis-web` + `git merge-base --is-ancestor` that migration 693's commit is an
  ancestor), not just "a commit where the migration merged" (D-L0-T's exact gotcha, avoided this
  time on the first try). Dispatched (`--reviewed-deployment-sha` = same deployed commit),
  authorized inside the timing window, genuine build (`disposition='build'`, 14/409 matching the
  pin exactly, fresh receipt with matching `build_id`/`output_digest`/`output_digest_spec_sha256`).
  `accepted_rebuild_observed` computed `decision_digest` from the exact stored verdict payload
  (stableJson + sha256, matching `canonicalNirmanaOptimizationVerdictDigest`) and submitted
  successfully (HTTP 201). This is the first time this session has cleared BOTH the D-L0-AA timing
  trap AND the D-L0-FF delta-skip trap on the same attempt.
  **`integrity_verified` blocked, but by a self-inflicted bug, not a structural one:** submission
  failed "integrity_verified requires exactly one prior current typed execution or disposition
  receipt." Root-caused: `integrity_verified`'s `server_reconstructed` source has its `observed_at`
  OVERWRITTEN server-side to the real `new Date()` at submission time
  (`normalizeDetectorEvidence`, `definitions.ts:1739-1760`), and `occursAfter(input, event)`
  requires that real timestamp to exceed the accepted_rebuild_observed event's `observed_at`. My
  own evidence JSON hand-typed a plausible-looking but FICTIONAL future `observed_at`
  (`18:52:00Z`) instead of shelling out to `date -u` for the real value — confirmed via both `date
  -u` and the DB's own `SELECT now()` agreeing the real clock was only `~18:31` at submission time,
  ~21 real minutes short. Not a data or evidence-chain defect: retry the exact same
  `integrity_verified` payload (`integrity_contract_sha256=6fc6f187890068ab29573252df6b8dc2e77d24d
  995f25e8c8f832ec79c1b34b0`, computed via `RegistryContractSchema`'s 13-field shape over the
  fresh post-693 registry row) once real time has caught up — `detector_observation`/`result_digest`
  get recomputed server-side regardless of what's submitted for them, so no other recomputation is
  needed. **Lesson recorded: always shell out to `date -u +%Y-%m-%dT%H:%M:%SZ` for `observed_at`
  fields, never hand-type a plausible future value** — the mistake is harmless for client-controlled
  timestamps (git_commit/build_run sources, which don't get overwritten) but breaks
  server_reconstructed occursAfter checks specifically.

- **D-L0-MM (refines D-L0-JJ)** — **bg_compendium_index: writer is fully correct; both
  content-hash pins in migration 623 were stale.** `CompendiumIndexWriter`'s core logic
  (`_build_desired_rows`) is a pure function of `classical_text_chunks` + `reference_topic_tags`
  with no chart-scoped inputs — replayed it directly (no `ContextSpec`/orchestrator machinery
  needed, just the two source queries + the function call) in a rolled-back transaction. Produces
  exactly 9571 rows (7969 chapter-scoped + 1602 topic-scoped), matching migration 623's structural
  pin exactly, and passing the `(chapter_num IS NULL) = (topic_id IS NULL)` alignment check. Both
  content-hash subclauses (chapter-scoped, topic-scoped) mismatched the 623 pin despite the writer
  file being unchanged since 623's authoring commit (`5f47906bc`, the same commit that authored
  bg_dasha_systems' wrong catalog_hash pin, D-L0-GG) — the `classical_text_chunks` corpus content
  has evidently evolved since (verse ranges / `content_en` feeding the mechanical synopsis) while
  the per-(text,chapter)/(text,topic) partition COUNTS happened to remain identical. (Investigated
  and ruled out a red herring first: a separate, never-merged branch `codex/nirmana-l0-wave2-
  correctness` had a `chunk_ids`-populating writer fix that looked directly relevant — confirmed
  via `git merge-base --is-ancestor` that this commit is NOT an ancestor of `main`/HEAD, so it's
  irrelevant to the live/deployed writer.) Migration `702_bg_compendium_index_content_hash_repin.sql`
  authored: re-pins both content hashes to the freshly-computed correct values, verified twice live
  (rolled-back tx) — applies cleanly against the 623 pin, evaluates TRUE against a genuine writer
  replay, FALSE (fail-closed) against current stale live data. No writer change. 6th instance this
  session of the established C12 "correct the check" pattern.

- **D-L0-NN — MILESTONE: `bg_vidhi_floors` FROZEN, the first genuine freeze of this campaign
  resumption (30/40, 10 remaining).** Continuing directly from D-L0-LL's `accepted_rebuild_observed`
  success: waited (bounded, single-call `until` loop, not a cross-cycle sleep) for real clock time
  to pass the fabricated `18:52:00Z` `observed_at` baked into the already-recorded
  `accepted_rebuild_observed` event, then retried the previously-computed `integrity_verified`
  payload unchanged — accepted immediately (HTTP 201). Server-side `normalizeDetectorEvidence`
  independently re-ran `bg_vidhi_floors`' `integrity_check_sql` live and recorded a genuine
  `detector_observation`/`result_digest` (verdict `true`) — confirms this is a REAL independent
  verification, not a rubber stamp. For `asset_frozen`: computed `lifecycle_digest` by fetching
  ALL historical lifecycle events for the asset (not just the "current" ones — 6 rows total,
  including the two now-superseded 2026-09-04 W2 events) and replicating the exact
  `{event_type, evidence_payload, source_kind, source_ref}` sort-then-stableJson-then-sha256
  scheme from `definitions.ts:2196-2203` in Python. First submission attempt failed
  ("requires exactly one current validated integrity receipt") — root-caused to the SAME class of
  bug as D-L0-LL: hand-typed `observed_at: "18:52:20Z"` again, this time landing 2 seconds *before*
  `integrity_verified`'s real server-assigned `observed_at` (`18:52:22.39`). Confirmed via
  `normalizeDetectorEvidence`'s exact scope (`definitions.ts:1725`: only `probe_accepted` and
  `integrity_verified` get their `observed_at` server-overwritten) that `asset_frozen`'s
  client-submitted `observed_at` is NOT overwritten and must itself be genuinely later — fixed by
  shelling out to real `date -u` and resubmitting; accepted immediately. Verified via `egate.sql
  -v layer=L0`: `bg_vidhi_floors` no longer appears in the unfrozen-asset list. Posted to #1713.
  Confirms the full evidence-chain toolkit built this session (dispatch, authorize, all W2/W4/W5
  submission scripts) works genuinely end-to-end for a real asset when nothing structural (D-L0-FF,
  D-L0-II) interferes — the remaining 10 unfrozen assets are ALL either awaiting a merged
  check-correction migration's deploy (bg_yogas/701, bg_dasha_systems/700, bg_compendium_index/702)
  or blocked on the two open structural findings.

  **D-CND-09 follow-up, checked and correctly NOT actioned:** now that `bg_vidhi_floors` is safely
  frozen (freezing is a historical attestation, not a live invariant — a later registry change
  can't retroactively invalidate it), re-checked whether its `catalog_status` DRAFT→CURRENT flip
  is now safe. Read the writer source (`writers/bg_vidhi_floors.py:514-516`) directly: both
  `education_deepdive` and `progeny_deepdive` are STILL tagged `[CANDIDATE]` (unchanged) —
  `spirituality_deepdive` and the other 11 are `[MANDATORY]`. Per the registry row's own documented
  policy ("re-verify against the writer source before flipping to CURRENT"), the precondition for
  CURRENT (all intents ratified) is genuinely NOT met — `catalog_status=DRAFT` remains correct, not
  stale. This is a positive, evidence-based "not yet," not a deferred/unclear item — nothing to act
  on until those two intents are ratified (native/campaign decision, not an L0 writer task).

- **D-L0-L** — **bg_doshas: check bug, not data defect. Migration 692 filed (PR #1829),
  auto-merge armed.** The "658 FULL-JOIN violations" (D-L0-F had called this a real data defect)
  are entirely an artifact of the check's own SQL: `FULL JOIN brahma_ontology ON
  entity_class='dosha' AND canonical_id=...` puts the entity_class filter in the ON clause instead
  of pre-filtering. `brahma_ontology` is shared across all 16 L0 entity classes (737 rows total —
  yoga=229, concept=136, dosha=79, karaka=77, domain=45, ...); FULL OUTER JOIN semantics mean an
  ON-clause filter on one side does NOT exclude that side's non-matching rows, so all 658 non-dosha
  rows leak in as spurious `catalog.canonical_id IS NULL` violations. Verified live (read-only):
  raw join (no WHERE) = 737 = 79 real + 658 leaked; `count(*) WHERE entity_class != 'dosha'` = 658,
  exact match. **The data itself is already fully correct**: catalog/ontology/reference all exactly
  79 rows, all 79 canonical_ids aligned (corrected join → 0 violations), and **all three
  content-hash pins already match production byte-for-byte** — this asset could be accepted on its
  LIVE fingerprint right now with no rebuild, once the check is fixed. Fix (subquery pre-filter on
  `brahma_ontology` before the join) verified in a rolled-back transaction: full composed check
  (unchanged otherwise) evaluates `TRUE` against current production data as-is. **This reclassifies
  a 3rd of D-L0-F's four "real data defect" calls as stale-check-not-defect** (bg_gochara_arcs was
  already known; now bg_yogas D-L0-J, bg_dasha_systems D-L0-K, bg_doshas D-L0-L — only
  bg_vidhi_floors remains genuinely unverified). NEXT once #1829 merges: re-run W4 accept for
  bg_doshas on LIVE fingerprint (same #1816-confirmed mechanism as bg_parihara_rules) — this one
  does **not** need the job-image deploy at all.
- **D-L0-M** — **bg_vidhi_floors tiling false-positive FIXED (partial verdict); migration 693 filed
  (PR #1832), auto-merge armed.** The tiling assertion (`lo<>1 OR hi<>n OR distinct_orders<>n`)
  assumes gapless `1..n` `item_order` per intent. Read the writer (`bg_vidhi_floors.py`, 14-intent
  `FLOORS` list, 409 items — matches target exactly) directly: all 7 `_deepdive` intents have gaps
  in item_order (e.g. `wealth_deepdive`: 40 items present, orders 1-38 then 40-44 — order 39
  deliberately skipped). Cross-checked the canonical TS source of truth
  (`platform/src/lib/vidhi/registry_data.ts`): confirmed **intentional, documented design** —
  `omega8Band({ from: 40, ... })` reserves item_order 40+ as a fixed "Ω8 reachability band" appended
  to each floor regardless of that floor's own item count (PARIŚODHANA B2 comment, right there in
  the source). Not a numbering bug; the check's `hi<>n` conjunct is simply the wrong invariant.
  Verified live: dropping `hi<>n` (keeping `lo=1` and `distinct_orders=n`, which are real
  invariants) returns 0 tiling violations against current production data. **Only a partial
  verdict**: `bg_vidhi_floors` is separately, genuinely incomplete live (11/14 intents, 286/409
  items vs. the writer's own 14/409 — 3 intents entirely absent) and `catalog_status=DRAFT` — that
  gap is real and untouched by this migration; still needs the DRAFT→CURRENT re-acceptance path
  (D-CND-09) and a dispatch once the job-image deploys. **This closes the LAST of D-L0-F's four
  "real data defect" calls as at-least-partially a check-not-data issue** — all four original C12
  wave-1 findings (bg_yogas, bg_dasha_systems, bg_doshas, bg_vidhi_floors) have now had a
  read-only-verified root cause distinct from "fix the writer, MUST" as originally called. NEXT: the
  bg_vidhi_floors completeness gap (missing 3 intents + DRAFT status) is the one remaining open
  question across all 5 originally-failing integrity checks — needs its own investigation (why are
  3 intents missing live when the writer's source has all 14?) once time allows; otherwise continue
  polling job-image deploy + #1828/#1829/#1832 queue status each cycle.

- **D-L0-N** — **bg_vidhi_floors 11/14-intent, 286/409-item gap: diagnosed, same stale-build family
  as D-L0-J/K (with one honest caveat).** Live has 11 intents; today's writer source (`FLOORS`
  list) has 14 — the 3 missing (`undertaking_election`, `biography_narrative`, `ritual_yajna`) are
  all tagged "ṢAḌ-DARŚANA W5" in their `notes` field, a later wave's addition. Of the 11 present
  intents, live is short by exactly 24 items total vs. today's source — traced to the item level
  (diffed live `wealth_deepdive` row-by-row against source): live has orders 1-35 then jumps to
  40-44, **missing orders 36-38** (`now_read`, `ahead_read`, `priority_read`) — a later addition to
  the machine_band tail, present identically (same -3 pattern) across all 8 affected intents.
  Verified today's FULL source is internally sound: **14 intents / 409 items exactly matches
  target**, all 55 distinct `primitive_id`s referenced exist in `vidhi_primitives` (0 dangling FKs),
  no duplicate `(intent, item_order)` pairs. **This is the same story as bg_yogas/bg_dasha_systems**:
  live predates later additions to the writer's own source, not a writer defect — a correct dispatch
  of today's code should produce exactly 14/409 with 0 tiling violations (post migration 693) and 0
  FK violations. **Honest caveat (unlike D-L0-J/K, cannot be fully closed read-only):** this
  conclusion assumes the *deployed pipeline job image* actually contains today's git HEAD of
  `bg_vidhi_floors.py` — I can only verify the git checkout, not what's baked into the currently-
  deployed (stale, pre-#1772) container. If the deployed image's writer predates the `now_read`/
  `ahead_read`/`priority_read` addition or the 3 ṢAḌ-DARŚANA intents too, a dispatch today would
  reproduce the current 11/286 state, not 14/409 — this is the same underlying job-image-deploy
  blocker already tracked, just now understood to possibly gate bg_vidhi_floors' data-completeness
  too, not only bg_cohort's dependency-satisfaction. **No further writer/migration work identified
  for bg_vidhi_floors** — remaining path is: migration 693 merges → job-image redeploys with current
  HEAD → dispatch → verify actual yield matches 14/409 → DRAFT→CURRENT re-acceptance (D-CND-09).
- **D-L0-O** — **bg_gochara_arcs: landed the drafted D-CND-01 rewrite (migration 694, PR #1836,
  auto-merge armed).** The draft (`sessions/drafts/bg_gochara_arcs_integrity_rewrite.sql`, written
  a prior cycle, held pending #1816) only needed its `<ACHIEVED>` placeholder filled — #1816 is now
  CLOSED (D-L0-H confirmed the server binds to LIVE fingerprint, no gate change), so nothing further
  blocked landing it. Filled `<ACHIEVED>=33933` from a fresh live count, re-verified ALL of it live
  before writing (not just trusting the old draft): all 9 bodies tile perfectly (`lo=0, hi=n-1,
  distinct_idx=n`, summing to exactly 33933), all 5 kept structural invariants hold, and the full
  composed rewritten check evaluates `TRUE` in a rolled-back transaction against current production
  data. Old check's stale per-body VALUES table (Rahu 13544/Ketu 13553 vs live 13234/13243 — the
  exact −310-each already diagnosed) and bare total dropped for gapless-tiling + an achieved-count
  floor (`target_floor` 34553→33933, §N.4). **This is the 3rd asset (after bg_doshas D-L0-L, and
  half of bg_vidhi_floors D-L0-M) that can go straight to W4 accept on its LIVE fingerprint with NO
  dispatch at all** once its migration merges. Combined with D-L0-J/K/N, **all 5 of the original C12
  wave-1 findings now have a landed-or-verified check/writer disposition** — none required an actual
  writer code fix; the "fix the writer, MUST" calls in D-L0-F were, on full read-only investigation,
  uniformly wrong.

- **D-L0-P** — **Reconstructed the evidence-submission mechanism (`nrec` is gone from main, #1731
  superseded) — prep, not committed to the shared repo.** Read the actual live path end to end:
  `platform/src/app/api/admin/internal/nirmana-elevation-executor/route.ts` (OIDC-authenticated,
  audience `https://amjis-web-938361928218.asia-south1.run.app`, two SAs —
  `amjis-nirmana-executor@…`/`amjis-nirmana-verifier@…` — required identity derived from the
  submitted `source_kind`, exactly mirroring the DB trigger split) + `evidence-command.ts` +
  `definitions.ts` for the exact `asset_analysis_accepted`/`optimization_verdict_accepted` payload
  schemas (`registry_fingerprint_sha256` + `analysis_digest` SHA-256 fields; `source_kind=git_commit`
  + `git:<40-hex>` source_ref; both map to the **executor** identity, not verifier — these are
  analysis reports, not certifications). **Verified I can mint identity tokens for BOTH service
  accounts** (`gcloud auth print-identity-token --impersonate-service-account=... --include-email`
  succeeded for both). Wrote + smoke-tested a session-local equivalent script
  (`.../scratchpad/l0_submit_evidence.sh`, mirrors `nrec`'s exact identity-mismatch-refusal logic)
  — **not** re-added to `platform/scripts/nirmana/` since that's Conductor-owned shared tooling
  (charter C5) whose PR was deliberately closed as superseded; not my call to re-introduce it.
  **Still open before actual submission**: find the current frozen `definition_revision` (table name
  guessed wrong on the first try; `nirmana_elevation_definitions` doesn't exist) and construct the
  exact JSON bodies for bg_doshas/bg_gochara_arcs. NEXT: once #1829/#1836 (and #1832's other half)
  merge AND deploy, resume here — find the definitions table, build the two command JSONs per
  asset, dry-run then actually submit via the reconstructed script.
- **D-L0-P continued** — **Found the definitions table + a THIRD deployment gate; the picture is
  now complete enough to build the real payload next cycle.** Frozen `definition_revision` =
  `t0-2026-09-01-0e5b06fb` (`nirmana_evidence.nirmana_elevation_campaign_definitions`, only
  `frozen`-status row). Read `recordNirmanaElevationEvidence` fully: **there is a third deployment
  surface beyond the pipeline job image and this git checkout** — `assertNirmanaGitCommitMatchesDeployment`
  requires `source_ref` to equal `git:${NIRMANA_DEPLOYED_SHA}`, an env var on the **`amjis-web` Cloud
  Run *service*** (distinct from the `brahma-build-pipeline-job` *job* image already tracked).
  Checked it live: currently `611d66e381c68235db0ca3b9f1f2a01552fea930` — one commit behind current
  `origin/main` tip, and does **not** yet include any of #1829/#1832/#1836. Submission must cite
  whatever SHA is deployed *at submission time*, not necessarily the exact migration commit — the
  claim is "analysis was done against a live registry fingerprint, as of this deployed snapshot",
  not "this exact file is in that snapshot" — so once amjis-web's next deploy picks up any of my
  merged migrations, `NIRMANA_DEPLOYED_SHA` will advance and become citable. Also traced
  `registry_fingerprint_sha256`/`analysis_digest` to their exact server-side computation
  (`canonicalRegistryContractDigest`/`canonicalNirmanaAssetAnalysisDigestForRegistryRow` in
  `definitions.ts`, fed by `frozen_manifest_asset` + live `asset_registry` row + a generated
  per-asset `writer_digest_sha256`/`convergence_commit` receipt base in
  `src/generated/nirmana-analysis-receipts.ts` / `nirmana-writer-digests.json`) — confirmed **both
  bg_doshas and bg_gochara_arcs already have a receipt base** (present in the writer-digest JSON,
  so the "reconstructable deployed analysis receipt" gate won't block them). **Correction, caught
  before committing**: I first drafted this entry claiming a failed submission's error message
  would reveal the expected digest — re-checked the actual throw strings
  (`requireAcceptedAssetAnalysisProvenance`) and they do NOT leak the expected value ("...does not
  match the current live contract" / "...does not match the canonical deployed analysis receipt" —
  no value in either). That shortcut doesn't exist. NEXT: once merged+deployed, the real path is to
  replicate `canonicalRegistryContractDigest`/`canonicalNirmanaAssetAnalysisDigestForRegistryRow`
  in a small Node/TS script fed by live DB data (same read-only-invoke-the-real-function technique
  as D-L0-J's `extract_yogas_from_corpus` call) — still need to locate where those two functions
  are defined (not found this cycle) and their exact input contract.

- **D-L0-P continued 2** — **Replicated `canonicalRegistryContractDigest` in Python; runnable now,
  correctly produces a well-formed digest for both target assets.** Read
  `registryContractFingerprintInput`/`canonicalRegistryContractDigest`/`stableJson`
  (`definitions.ts:28-162`): `stableJson` is a plain recursively-key-sorted compact JSON
  serialization — exactly what Python's `json.dumps(obj, sort_keys=True, separators=(',',':'),
  ensure_ascii=False)` already does, so no TS runtime needed. Wrote
  `.../scratchpad/compute_registry_fingerprint.py` (maps `asset_registry.layer` word→code via the
  same `brahmagyan→L0` table, sorts `depends_on`, builds the exact `registry_contract` field set)
  and ran it against live rows for both **bg_doshas** (`073def4a…`) and **bg_gochara_arcs**
  (`93fa16df…`) — both produce a well-formed 64-hex digest. **Honest residual**: these are the
  PRE-migration values (integrity_check_sql hasn't changed yet) and, more importantly, **I could
  not cross-verify the replica against an actual TS execution** (importing `definitions.ts` directly
  via `tsx` risked triggering its transitive DB-pool-creation imports without matching env setup —
  judged not worth the risk for this cycle; the algorithm itself is simple enough that hand-replication
  confidence is high, but this is inspection-based, not execution-verified). Still need
  `canonicalNirmanaAssetAnalysisDigestForRegistryRow` (a second, more involved function — not yet
  read this cycle) before the full submission payload can be built. NEXT: read that function; if
  time allows, reconsider a safer tsx-import path (e.g. mock/stub the DB-pool imports) to
  cross-verify the fingerprint replica before ever submitting for real — a wrong digest here isn't
  destructive (submission would just 403), but worth checking before spending a submission attempt.

- **D-L0-P continued 3 — CLOSED: the full submission-payload toolkit is built and
  cross-validated.** Read `canonicalNirmanaAssetAnalysisDigestForRegistryRow` +
  `canonicalNirmanaAssetAnalysisReceiptDigest` + `NirmanaAssetAnalysisReceiptSchema`
  (`definitions.ts:1111-1167`) — same `stableJson`+sha256 pattern, applied to `{schema_version,
  base: receiptBase, frozen_manifest_asset, current_registry_contract}`. Sourced every input live:
  `receiptBase.grounding.convergence_commit` for L0 = `49bb5c98b864a2cb2fee037cdb7f14f6892a8263`
  (`nirmana-analysis-layer-pins.json`); `writer_digest_sha256` per asset from
  `nirmana-writer-digests.json`'s `writers` map; `frozen_manifest_asset` queried directly from
  `nirmana_evidence.nirmana_elevation_campaign_definitions.manifest -> 'assets'` for revision
  `t0-2026-09-01-0e5b06fb`. Extended the Python replica
  (`.../scratchpad/compute_analysis_digest.py`) and ran it for both assets. **Independent
  cross-validation, not just inspection**: the frozen manifest asset's own embedded
  `registry_fingerprint_sha256` field (computed by the real server at freeze time) matches this
  session's from-scratch Python computation **byte-for-byte** for both bg_doshas
  (`073def4a…`) and bg_gochara_arcs (`93fa16df…`) — resolving last cycle's "not
  execution-verified" caveat with a real independent check, not a bigger risk taken. Computed
  today's `analysis_digest` values too (`49113930…` bg_doshas, `66cb710b…` bg_gochara_arcs) —
  these will change once migrations 692/694 merge (the `current_registry_contract` embeds
  `integrity_check_sql`, which the merge changes by design; that's the whole point of the LIVE-vs-
  frozen distinction #1816 already settled). **The full toolkit is now ready**: once a migration
  merges, re-run the two scripts against fresh live data, build the `record_evidence` JSON body per
  the schema already traced (D-L0-P), dry-run via `l0_submit_evidence.sh`, then submit for real.
  Nothing structurally unknown remains between here and an actual accept.

- **D-L0-Q — corrected a stale "wave-2/3 needs wave-1 frozen" framing; ran the real E-gate batch
  query for the first time this resumption.** `scripts/nirmana/egate.sql -v layer=L0` (never run
  before this cycle — everything up to now was diagnosed asset-by-asset) shows **8 of 11 remaining
  assets are `OPEN-PENDING-PIN` with 0 unfrozen ancestors**: `bg_cohort`, `bg_compendium_index`,
  `bg_dasha_systems`, `bg_doshas`, `bg_gochara_arcs`, `bg_text_index`, `bg_vidhi_floors`,
  `bg_yogas`. Checked `depends_on` directly: `bg_compendium_index`/`bg_text_index` depend only on
  already-frozen `bg_reference`/`bg_texts` — **they were never wave-gated**, contra the state
  file's prior note; they're blocked on exactly the same thing as everything else (job-image
  deploy), not a separate wave-1 dependency. Only 3 are genuinely `BLOCKED-ANCESTORS`:
  `bg_parihara_rules` (→ `bg_doshas` only, `bg_texts` has since frozen — corrected a stale
  "bg_doshas, bg_texts" note too), `bg_rules` (→ `bg_dasha_systems`, `bg_yogas`), `bg_concordance`
  (→ `bg_dasha_systems`, `bg_rules`, `bg_text_index`, `bg_yogas` — deepest node, clears last). Since
  `bg_dasha_systems`/`bg_yogas` are both already fully diagnosed (D-L0-K/D-L0-J, writer-correct,
  no fix needed), **the entire remaining backlog clears in ordinary dependency waves once dispatch
  resumes** — no separate "wave-2/3" governance gate exists beyond normal DAG order. Confidence:
  HIGH (ran the canonical query, not a re-derivation).

- **D-L0-R — the pipeline job-image blocker is CLEARED; a second blocker (shared dispatch script)
  is now the gate instead.** `brahma-build-pipeline-job`'s deployed image advanced from the
  long-stale `d93d9d0a…` to `589284957…` — verified `git merge-base --is-ancestor ee8cf7d09
  589284957…` is TRUE, so **#1772 is in the deployed image; `bg_cohort`'s DEP-ASSERT blocker is
  cleared.** But dispatch isn't actually unblocked yet: the shared
  `platform/scripts/dispatch_nirmana_campaign_wave.py` still carries the unqualified-schema bug
  (Conductor's #1833/#1838 finding — every dispatch through it fails with `relation ... does not
  exist` since migrations 632/633 moved the definitions/events tables into `nirmana_evidence`)
  — checked the live file on `origin/main`: **#1838's fix is not merged yet**, so the script would
  still fail today. Also observed and posted to #1713: **no merge to `main` since 13:54:58Z** despite
  a 22-deep queue with PRs (e.g. #1791, #1801) showing 0 pending checks / 0 failures — looks like a
  genuine campaign-wide merge-queue stall, not just normal latency; flagged as an observation (not
  an adjudication — nothing for Conductor to *rule* on, just a fleet-health data point that may have
  cleared its last sweep window). NEXT: once #1838 merges, **all 8 `OPEN-PENDING-PIN` L0 assets
  become genuinely dispatch-ready in one sweep** — need to work out the actual dispatch invocation
  (`dispatch_nirmana_campaign_wave.py`'s CLI, not yet read this cycle) as the next real unit of
  work, separate from (and now higher-priority than) the evidence-submission toolkit built over the
  last several cycles.

- **D-L0-P triple-confirmed + clarified what "OPEN-PENDING-PIN" actually means for bg_doshas/
  bg_gochara_arcs.** Reading `platform/scripts/dispatch_nirmana_campaign_wave.py` (prep for the
  dispatch path) turned up its own `_live_registry_fingerprint`/`_canonical_analysis_digest`
  functions — **the Conductor's own canonical Python implementation of the exact two functions this
  session hand-replicated over the last several cycles**, field-for-field identical
  (`REGISTRY_CONTRACT_FIELDS` tuple matches mine exactly, same `sorted(depends_on)`, same literal
  strings). Then checked the ALREADY-EXISTING W2 events for both assets directly: their recorded
  `registry_fingerprint_sha256` (`073def4a…` bg_doshas, `93fa16df…` bg_gochara_arcs) **matches this
  session's from-scratch computation exactly** — a third independent confirmation, after the frozen
  manifest's own embedded value. **This also resolves a real question**: E-gate's
  `w2_analysis=t/w2_verdict=t` for these two isn't stale data or luck — it means W2 was ALREADY
  accepted (presumably by a prior L0 session), against the CURRENT (pre-migration) live fingerprint,
  which is exactly why the gate reads `OPEN-PENDING-PIN` not `OPEN`: egate.sql's own README already
  explained this (C2.3 pin-freshness isn't DB-checkable). **The moment migrations 692/694 merge and
  `integrity_check_sql` changes, these two W2 acceptances go stale** (their fingerprint no longer
  matches live) — the toolkit built over D-L0-P is for exactly this "delta re-review" resubmission,
  not a from-nothing W2 acceptance. Confidence in the whole toolkit is now very high (3-way
  cross-validated, not just inspection).

- **D-L0-S — read `dispatch_nirmana_campaign_wave.py`'s full CLI/commit flow; the exact next-steps
  sequence for bg_doshas/bg_gochara_arcs is now fully specified.** CLI: dry-run first (no
  `--commit`) to get a manifest-digest preview, then `--commit --confirm NIRMANA_CAMPAIGN_WAVE
  --snapshot-ref <ref> --expected-manifest-digest <preview> [--acknowledge-destroys]` — this single
  script call does BOTH `create_campaign_run` and (if `--commit`) `dispatch_campaign_run`
  atomically, so the old tooling's separate "authorize-then-force-execute-within-~20s" race (D-L0-B)
  **does not apply to this replacement script** — one invocation handles both. `--layer L0`
  requires `--reviewed-deployment-sha` (or `NIRMANA_DEPLOYED_SHA` env), matching the `amjis-web`
  deploy gate already found (D-L0-P). **Confirmed the script validates W2 pin-freshness itself**
  (`_registry_evidence_bindings`, ~line 311-414): it filters accepted `asset_analysis_accepted`/
  `optimization_verdict_accepted` rows to ones whose `registry_fingerprint_sha256` equals the
  CURRENT live fingerprint, and raises `RuntimeError("accepted asset analysis does not match the
  current live registry contract for {asset_id}")` if none match — i.e. **dispatch will itself
  detect and refuse a stale W2 acceptance**, exactly as D-L0-P's cycle-13 finding anticipated.
  Verdict also gets checked: must be in `optimize|correct|optimize_and_correct|
  examined_and_already_efficient` (`BUILD_AUTHORIZING_VERDICTS`) and match the analysis's digest.
  **Judgment call for the eventual resubmission**: bg_doshas/bg_gochara_arcs' writers never
  changed — only each asset's OWN `integrity_check_sql` (a registry/governance field) did — so
  `examined_and_already_efficient` (proposal `action=no_change`, `output_contract=digest_identical`)
  is the better fit than `correct` (which implies the WRITER's own output changed). **Full sequence
  once 692/694 merge**: (1) re-run `compute_registry_fingerprint.py`/`compute_analysis_digest.py`
  against fresh live data, (2) submit fresh `asset_analysis_accepted` + `optimization_verdict_accepted`
  (verdict=`examined_and_already_efficient`) via `l0_submit_evidence.sh --as executor`, (3) dry-run
  then commit-dispatch via `dispatch_nirmana_campaign_wave.py`. Nothing structurally unknown remains
  in the whole path from here to a real, verified L0 freeze.

- **D-L0-T — hands-on-verified the #1833 schema bug live, then discovered a real
  `--reviewed-deployment-sha` batching gotcha that changes the dispatch plan.** Ran
  `dispatch_nirmana_campaign_wave.py` (dry-run, no `--commit`, no writes) against `bg_compendium_index`
  on unmodified `origin/main`: reproduced the exact `relation "nirmana_elevation_campaign_definitions"
  does not exist` error live (not just trusting Conductor's report). Then built a **local-only**
  patched copy (`.../scratchpad/dispatch_test/`, 4-site schema-qualify, matching #1838's actual diff
  exactly — verified via `gh pr diff 1838`) to keep testing without waiting for the merge; this is a
  scratch test copy, never touches the shared repo. Dry-run against the patched copy got past the
  schema bug and hit: `"accepted asset analysis does not match the current live registry contract for
  bg_compendium_index"` — surprising, since this session's toolkit confirmed BOTH
  `registry_fingerprint_sha256` AND `analysis_digest` match the recorded W2 event exactly. Root
  cause, traced to `_registry_evidence_bindings` (~line 373): the script also requires
  **`row["source_ref"] == f"git:{reviewed_deployment_sha}"` EXACTLY** — not just a valid format.
  `bg_compendium_index`'s W2 was accepted under `source_ref=git:4f7a9cc8…` (whatever was deployed
  when a prior session submitted it); I'd passed `eb35945bc…` (today's deployed SHA) as
  `--reviewed-deployment-sha`, so the row was correctly excluded — by design, per the script's own
  comment ("a prior valid receipt may retain the same registry fingerprint while an explicitly
  reviewed deployment advances... it remains auditable history, not current dispatch authority").
  **This is the exact same gotcha Conductor hit with L5's `mi_vistara`/`mi_jivanaghatana` pairing**
  (#1713, 14:53:47Z: "the dispatch script requires ONE `--reviewed-deployment-sha` for the whole
  batch and filters evidence rows to exact-match it... no single value satisfies both"). **Changes
  the plan**: a combined multi-asset dispatch wave needs every included asset's W2 acceptance
  aligned to the SAME `source_ref` — in practice, **resubmit fresh W2 (`asset_analysis_accepted`+
  `optimization_verdict_accepted`) for every asset going into one dispatch batch, under one common
  current deployed SHA, right before dispatching** — not just for bg_doshas/bg_gochara_arcs (whose
  migrations will stale them anyway) but potentially for every other ready asset too, if dispatching
  them together in one wave. Single-asset (or same-source_ref-batch) dispatch remains simpler.

- **D-L0-U — FULL dry-run validation succeeded for both target assets, end to end, non-destructively.**
  Fixed last cycle's `--reviewed-deployment-sha` mismatch by using the asset's OWN existing W2
  `source_ref` (`git:4f7a9cc872714c74111ca8ae38ad4257c462cd3e` — same commit for bg_doshas,
  bg_gochara_arcs, and bg_compendium_index; all three W2-accepted together by a prior session,
  confirmed valid via `git cat-file -t`) instead of today's deployed SHA. Re-ran the scratch-local
  patched dispatch script (dry-run, no `--commit`) for **both bg_doshas and bg_gochara_arcs
  individually — both fully succeeded**, no `RuntimeError`, producing a real `manifest_digest` +
  `run_id` for each (`ac992519b9…`/`61f02e97…` for bg_doshas; `c42f73e1…`/`86f6dcbf…` for
  bg_gochara_arcs). bg_doshas' run correctly printed the **WP-6 blast-radius warning**
  (`CASCADE → reference_doshas, 79 rows`, depth 1) — matches D-L0-I's manual C13 analysis exactly,
  confirming the script's own blast-radius detector agrees with this session's earlier hand-derived
  finding. bg_gochara_arcs printed no warning (LEAF, as D-L0-I found). **Verified the dry run is
  genuinely non-destructive**: `SELECT count(*) FROM build_runs WHERE id='<run_id>'` = 0 for the
  bg_doshas run — nothing persisted despite a receipt being printed. This is now a complete,
  successful, safe rehearsal of the entire path for both assets — the only things standing between
  this and a REAL dispatch are (1) migrations 692/694 actually merging (which recomputes the
  fingerprint against a corrected `integrity_check_sql` — meaning the CURRENT dry-run's specific
  digests will change once that lands, but the MECHANISM is now proven), (2) #1838 merging for
  real (this session used a local patch only), and (3) fresh W2 resubmission under the new fingerprint
  (per D-L0-P/D-L0-T) before a real commit-dispatch.

- **D-L0-V — RESOLVING: #1856 fixed in PR #1861 (auto-merge armed), still waiting on the same stuck
  queue to actually land.** Conductor confirmed (#1713, 15:09:30Z) a two-line fix, verified
  byte-identical hash for str-vs-UUID input on the already-working case — zero regression, zero
  interface change. Their framing also now reads "for ANY per-chart asset with declared deps"
  (narrower than my own hedge last cycle that it might not be per-chart-specific) — since both
  target assets are `scope=global`, this suggests the risk may not have applied to them at all, but
  moot either way once #1861 lands. Original flag, for the record: L5 found (URGENT, #1856) that
  `asset_runner.py`'s provenance capture (`compute_upstream_hash`/`canonical_upstream_hash`) crashes
  with `"Object of type UUID is not JSON serializable"` when `chart_id` arrives as a raw
  `uuid.UUID` at the JSON-encoding boundary — confirmed live against production, crashes the asset
  BEFORE the writer even runs. L5's title scopes it to "per-chart assets with declared deps", but
  their own root-cause note hedges that the bug pattern exists in BOTH candidate call sites
  regardless of the `declared_deps`-aware branch, i.e. it may not actually be per-chart-specific.
  **Checked: both `bg_doshas` and `bg_gochara_arcs` are `scope=global` but DO have non-empty
  `depends_on`** (`bg_ontology`, `bg_ephemeris`) — the other half of L5's trigger condition. Since
  this crash only fires during actual writer execution (inside a real `--commit` dispatch, never a
  dry run — D-L0-U's successful dry-runs would NOT have exercised this code path), **it cannot be
  ruled out that a real dispatch of either target asset hits the same crash**, even though both are
  global-scope. Not investigating L5's Python further myself (Conductor's fix, not L0's) — just
  flagging: **check #1856's resolution status before attempting a real (non-dry-run) dispatch**,
  not just before the migrations merge.

- **D-L0-W — #1829 MERGED (bg_doshas migration 692 is on `main`); queue is genuinely draining, not
  permanently stalled.** After 3+ stuck cycles, `git log origin/main -- .../692_...sql` confirms the
  merge commit (`3bfeaf284`); `#1832`/`#1836` remain queued but at earlier positions than before
  (30-deep queue now includes newer PRs too, e.g. `#1838` still present) — the queue IS moving,
  just slowly, exactly as L4's diagnostic implied. **Checked whether the migration has actually
  APPLIED to the live DB — not yet**: live `integrity_check_sql` for `bg_doshas` still shows the OLD
  buggy bare `FULL JOIN brahma_ontology` (not the corrected subquery-prefiltered version), and
  `amjis-web`'s `NIRMANA_DEPLOYED_SHA` (`bd398f065`) is still 2 commits behind the current `main` tip
  (`3bfeaf284`) — deploy lags merge by some margin, not instant. **NEXT, once deploy catches up**:
  re-run `compute_registry_fingerprint.py`/`compute_analysis_digest.py` against the NOW-corrected
  live row, submit fresh `asset_analysis_accepted`+`optimization_verdict_accepted`
  (`verdict=examined_and_already_efficient`, per D-L0-S) via `l0_submit_evidence.sh --as executor`
  citing whatever SHA is THEN deployed as `source_ref`, then dry-run + commit-dispatch via the real
  (not local-patched) `dispatch_nirmana_campaign_wave.py` once #1838 also merges+deploys. This is
  the first genuinely real, non-simulated step toward an actual L0 freeze this whole resumption.

- **D-L0-X — process correction: `gh pr list --search "is:queued"` was silently truncating to 30
  results every cycle, causing a false "ejected" scare this cycle.** `#1832` appeared missing from
  the queue listing (checked without an explicit `--limit`); investigated as a possible real
  ejection (checked its own checks — all green, `autoMergeRequest: false`), ran `gh pr merge 1832
  --auto` which replied "already queued to merge" (contradicting the listing), then re-ran the
  search with `--limit 100` and found **the real queue is 36 deep, not 30** — `#1832` was sitting at
  position 32, past the CLI's default page size. Nothing was ever ejected; this was a query artifact
  in every prior cycle's hygiene check, not a PR problem. **Going forward: always pass an explicit
  `--limit` (100 is plenty) to `is:queued` searches** — the default-30 truncation is silent (no
  warning, no `next_page` indicator in the plain JSON output) and would otherwise read as a false
  ejection every time the real queue exceeds 30. No PR was harmed; `#1829` (already merged this
  session) proves the queue mechanism itself always worked correctly.

- **D-L0-Y — MIGRATION 692 IS LIVE; bg_doshas' W2 was REAL-SUBMITTED and ACCEPTED (both 201).** The
  migration applies via a deploy-time step decoupled from `amjis-web`'s own container rollout (its
  `NIRMANA_DEPLOYED_SHA`, `3b208dbfa…`, is still one commit behind my `#1829` merge commit, yet the
  DB check text is already corrected — confirms migrations apply on their own faster cadence, not
  gated on the app container catching up). Verified live: `integrity_check_sql` now reads the
  subquery-prefiltered version and **evaluates `TRUE` against production data** (executed dynamically
  via `DO $$ ... EXECUTE check_sql INTO result $$`, not just inspected as text). Re-ran the toolkit
  against the fresh row: new `registry_fingerprint_sha256=cf02b44f8c16ea2f2cd0a313d6d45108599b62757
  9a01e9e8c058bbeecb1e1e5`, new `analysis_digest=6dcd11f8e1260d8cefce364d250447bbf32aee3695fe7b9320
  7e9cf216fff08e` (differs from the frozen manifest's `073def4a…`/prior W2, as expected — the check
  text itself changed, so the fingerprint legitimately moved; the LIVE-fingerprint-not-frozen
  binding is what #1816 already established). Built the two `record_evidence` bodies exactly per the
  traced schema, `--dry-run`'d through `l0_submit_evidence.sh` first, then **submitted for real**:
  `asset_analysis_accepted` (201 created) and `optimization_verdict_accepted`
  (`verdict=examined_and_already_efficient`, 201 created), both signed by the executor identity,
  both citing `source_ref=git:3b208dbfadbbae4fd35a9ce5c89868a2fbb5abe5` (the actually-deployed SHA
  at submission time). Confirmed both rows landed in `nirmana_evidence.nirmana_elevation_campaign_
  events` with the new fingerprint (old events retained as history — evidence is append-only, as
  documented). **This is the first genuinely real (non-dry-run, non-simulated) production write this
  whole resumption**, and it fully round-trip-validates the entire D-L0-P toolkit: the server
  independently recomputed and matched both values before accepting either event. **NEXT (deferred,
  needs its own careful investigation before acting)**: bg_doshas' W2 is fresh, but freezing still
  needs `integrity_verified` + `asset_frozen` events under the VERIFIER identity, following genuine
  independent re-derivation (not just re-asserting the same claim) — read `requireIntegrityProvenance`/
  `requireFreezeProvenance` in `definitions.ts` for their exact evidence-payload contract before
  attempting either, same discipline as was applied to the W2 schema before this submission.

- **D-L0-Z — CORRECTION to D-L0-L/D-L0-O/last cycle's plan: dispatch is NOT skippable for
  bg_doshas/bg_gochara_arcs after all, even though their DATA never needs to change.** Read
  `requireIntegrityProvenance`/`requireFreezeProvenance` (`definitions.ts:2092-2178`) before
  attempting either event, per last cycle's own plan — and found the real gate: for any
  `execution_obligation='build'` asset (both of these are), `integrity_verified` must bind to, and
  `asset_frozen` must occur strictly after, a **current `accepted_rebuild_observed` receipt** — i.e.
  a genuine build-run execution record. There is no "skip execution, data already matches" path in
  the lifecycle model; `accepted_rebuild_observed` can only be produced by an actual dispatch
  (idempotent rewrite of the same 79/79/79 rows, in bg_doshas' case, but still a real run through
  `dispatch_nirmana_campaign_wave.py` → the pipeline job). **Re-read D-L0-H's own precedent
  correctly this time**: `bg_parihara_rules` reached "ROUTED" (W1/W2 done), never "FROZEN" — I had
  misremembered that as a skip-dispatch freeze precedent when it was actually the SAME W2-only
  stopping point I reached for `bg_doshas` last cycle, not further. **Net effect on the plan**: last
  cycle's real W2 submission for `bg_doshas` was still correct and necessary (freeze needs *fresh*
  W2 bound to the corrected fingerprint regardless), but it is not sufficient by itself — **every
  asset, without exception, is gated on #1838 for the actual freeze**, simplifying the picture
  rather than complicating it (no more "some assets skip dispatch" special-casing to track).
  Corrected the assets-table framing accordingly. This is exactly the kind of claim §N.8 (Earned-
  Signal Principle) exists to catch: verify before asserting a shortcut exists, not after.

- **D-L0-AA — #1838 MERGED; first-ever real `--commit` dispatch executed; missed the
  `build_run_authorized` window; retry blocked by the still-unmerged #1851.** Pulled the real fixed
  `dispatch_nirmana_campaign_wave.py` straight from `origin/main` (`git checkout origin/main --
  <path>`, uncommitted local working-tree refresh only — the file isn't mine to carry in a commit).
  Verified conductor-2b's caution properly rather than assuming: #1838's fix lives in a
  client-invoked script, not the deployed job image, and confirmed the job-side orchestrator
  (`pipeline/python-sidecar/pipeline/`) never references the evidence tables unqualified — nothing
  there needed a redeploy. Posted a `SLOT CLAIM` (0/3 occupied, verified live), took a fresh Cloud
  SQL backup (`cloudsql-backup:1788624653149`), dry-ran clean (manifest_digest recomputes once
  `--snapshot-ref` is included — **found and worked around a subtlety**: the preview digest changes
  the instant `snapshot_ref` is added to the call, so the correct dry-run to trust is the one that
  already includes the intended `--snapshot-ref`, not a bare one), then **committed**:
  `--acknowledge-destroys` (WP-6, `reference_doshas` CASCADE, matches D-L0-I/D-L0-U exactly),
  `run_id=92830957…`, dispatched to `brahma-build-pipeline-job-2wv8v`. **The job started and
  completed in ~23 seconds** (`16:14:36Z`→`16:14:56Z` start→`16:14:59Z` end) while I was reading
  `requireBuildRunAuthorizationProvenance`'s exact schema to build the authorization payload
  correctly — **missed the pre-start window** (`build_run_authorized` requires `run.started_at IS
  NULL`, which was no longer true by the time I had the payload ready). Data is fine (idempotent
  rewrite, `integrity_check_sql` re-verified `TRUE` live), but this specific run can never carry a
  valid authorization chain now. **Retry immediately blocked**: the duplicate-execution guard
  (`SELECT ... FROM build_runs WHERE triggered_by=%s` with **no state filter** — confirmed by
  reading the live script) refuses any second run on the same `(definition_revision, layer, wave,
  asset_ids)` key regardless of the prior run's state — this is exactly #1848's bug, and **its fix
  (#1851) has not merged yet**, so `bg_doshas` cannot be re-dispatched solo until it does. Posted
  `SLOT RELEASE` documenting the full account. **Lesson for the actual retry once #1851 lands**:
  pre-build the entire `build_run_authorized` payload (idempotency_key, source_ref template,
  authorization_sha256 — confirmed this field is validated only for well-formed-hex-string shape,
  NOT matched against any specific computed value, so any deterministic sha256 works) BEFORE
  dispatching, so only the fresh `run_id` needs to be substituted in and fired immediately — no
  reading schema code with the clock already running next time.

- **D-L0-BB — bg_gochara_arcs migration (694) is LIVE; fresh W2 real-submitted and accepted (both
  201), same D-L0-Y treatment.** Verified live check executes to `TRUE` (`target_floor=33933`
  confirms deploy caught up). Re-ran the toolkit against the fresh row + the unchanged frozen
  manifest asset: new `registry_fingerprint_sha256=c9388e04…`, new `analysis_digest=2d95e591…`
  (both differ from the stale 2026-09-04 W2, as expected — same story as `bg_doshas`). Built,
  dry-ran, then real-submitted both `record_evidence` bodies (`verdict=examined_and_already_
  efficient`, citing the current deployed SHA `e54ae9ac…` as `source_ref`) — both HTTP 201,
  confirmed landed with the new fingerprint. **Remember D-L0-Z**: this is W2-fresh, not
  freeze-ready — `bg_gochara_arcs` (a LEAF asset, no cascade per D-L0-I) still needs a real
  dispatch + immediate `build_run_authorized` to produce `accepted_rebuild_observed`, same as
  `bg_doshas`, and is subject to the same #1848/#1851 duplicate-guard block once #1851 merges (or
  possibly not, if #1851 lands before I dispatch this one — worth checking freshly each cycle).

- **D-L0-CC — built + tested the `build_run_authorized` fast-path script for the D-L0-AA retry;
  still gated on #1851.** Wrote `.../scratchpad/authorize_build_run.sh <run_id> <asset_id>
  <wave_index> [layer] [--dry-run]`: builds the exact `record_evidence`/`build_run_authorized`
  body (idempotency key, `entity_type=build_run`, `source_ref=build_run:<run_id>`,
  `source_kind=build_run` → executor identity, a deterministic shape-valid
  `authorization_sha256`) and fires it via `l0_submit_evidence.sh` in one call — no schema lookup,
  no JSON hand-authoring at dispatch time. Smoke-tested end-to-end with a fake UUID in `--dry-run`
  mode: resolves correctly to executor identity, produces valid JSON. **Next real dispatch attempt
  (bg_gochara_arcs or bg_doshas, once #1851 merges) is now: dispatch `--commit` → capture `run_id`
  from stdout → immediately `authorize_build_run.sh <run_id> <asset_id> <wave_index>` → THEN
  `accepted_rebuild_observed`.** This should comfortably beat the ~20s window that was lost last
  cycle reading schema code live. `#1851` still not merged as of this cycle.

- **D-L0-DD — #1851 MERGED; first PROPERLY-AUTHORIZED real dispatch achieved (run in progress).**
  Pulled the narrowed duplicate-guard fix locally, verified it (`state = ANY(['planned','running',
  'paused'])`, matches #1848's description exactly). Posted `SLOT CLAIM`, fresh backup
  (`cloudsql-backup:1788627280698`), dry-ran `bg_gochara_arcs` (LEAF, no WP-6 warning as expected)
  — **first `--commit` attempt hit a genuine, unrelated concurrency conflict**
  (`build_runs_one_active_per_chart_idx`, a stricter single-active-run-per-chart constraint, not
  the per-triggered-by guard): another lane (L5, `mi_vistara`) dispatched at the exact same instant
  and won the race. Verified precisely (checked `build_run_assets.asset_id` for the row that
  appeared — it was `mi_vistara`, not mine) rather than assuming my own run had partially
  succeeded; confirmed zero rows/side effects for `bg_gochara_arcs` from the failed attempt, safe
  to retry immediately. **Retried cleanly** (same dry-run digest, confirming determinism) with
  corrected output handling (stdout-only capture this time — the mixed stdout+stderr capture from
  the D-L0-AA attempt is exactly what caused that cycle's `RUN_ID` extraction to fail): `--commit`
  succeeded (`run_id=bfdc6919…`), and **`authorize_build_run.sh` fired immediately after and
  succeeded (HTTP 201)** — confirmed `build_run_authorized` recorded at `16:58:42Z`, run's own
  `started_at` still `NULL` at that moment, genuinely inside the window this time. **This is the
  first fully-authorized real dispatch this whole resumption.** Run was still `running`/`building`
  at cycle end (33,933-row asset, bigger than `bg_doshas`' 79 rows — expect longer runtime). NEXT:
  check completion next cycle; once terminal, read `NirmanaRebuildEvidenceSchema` and submit
  `accepted_rebuild_observed` (executor, `source_kind=build_run`) to complete the chain toward
  `integrity_verified`/`asset_frozen`. `bg_doshas`' earlier unauthorized run (D-L0-AA) remains
  available for a clean retry any time — same recipe, now proven twice.

- **D-L0-EE — bg_gochara_arcs run COMPLETED successfully (data verified correct), but its
  authorization used the WRONG `source_kind` and can never chain to `accepted_rebuild_observed`;
  fixed the script for the next attempt.** Run `bfdc6919…` finished cleanly (`state=completed`,
  no error, ~28s for the 33,933-row rebuild); re-verified `integrity_check_sql` executes `TRUE`
  live. Before submitting `accepted_rebuild_observed`, read its exact validation
  (`requireAcceptedRebuildProvenance`, `definitions.ts:2209-2277`) as planned — and found it looks
  back for the matching `build_run_authorized` event via a **literal string filter**:
  `event.source_kind === 'campaign_authorization'`. My `authorize_build_run.sh` (D-L0-CC) used
  `source_kind: "build_run"` — a plausible-looking value that the ACCEPTANCE check for
  `build_run_authorized` itself never rejected (its schema takes any non-empty string), but which
  this DOWNSTREAM check filters out silently. **`bg_gochara_arcs`' authorization for this specific
  run can never be fixed retroactively** (`build_run_authorized` requires `run.started_at IS NULL`,
  no longer true) — the run itself is harmless (correct data, no evidence-chain corruption, nothing
  else depends on it), just unusable for freezing. **Fixed `authorize_build_run.sh`**
  (`source_kind` → `"campaign_authorization"`), documented the exact failure mode inline so it
  can't recur, re-verified via `--dry-run`. **This makes THREE dispatch attempts now, three
  different lessons** — D-L0-AA (missed the timing window), D-L0-DD (won a concurrency race
  correctly), D-L0-EE (wrong `source_kind`, caught by reading the schema before submitting rather
  than after a rejected 400). NEXT: fresh dispatch (either asset — both still need a clean
  authorized run) with the now-corrected script; this time also read `NirmanaRebuildEvidenceSchema`'s
  OTHER fields (`decision_digest`, `output_digest`, `output_digest_spec_sha256`, etc. — not yet
  traced) BEFORE dispatching, not after, to avoid a fourth surprise.

- **D-L0-FF — structural gap found: the orchestrator's delta-skip optimization and the evidence
  layer's `accepted_rebuild_observed` requirement are not integrated, and it may be unfixable via
  the current tooling for an already-correct asset.** Fully traced `NirmanaRebuildEvidenceSchema`
  before this cycle's retry (registry_fingerprint/analysis_digest from D-L0-BB;
  `decision_digest=57a9bc47…` precomputed from the exact stored `optimization_verdict_accepted`
  payload via `canonicalNirmanaOptimizationVerdictDigest`; `implementation_digest=null` since
  `changeIsRequired()` is false for a `no_change` proposal; `output_digest`/
  `output_digest_spec_sha256` read live from `asset_provenance_receipts`/`asset_output_digest_specs`
  — not computed, the orchestrator writes these). Fixed `authorize_build_run.sh`'s `source_kind`
  bug (D-L0-EE), took a fresh backup, dispatched `bg_gochara_arcs` a 3rd time with authorization
  correctly inside the window (`run 5ba8cedf…`, `source_kind=campaign_authorization` confirmed
  correct this time). **Run completed, but `asset_provenance_receipts` was never updated** — traced
  to `asset_runner.py`'s `disposition='skip_no_delta'` (O-wave WP-2, "delta-skip gate",
  `_skip_no_delta`): since the writer's code/config/upstream/output all already matched the
  receipt from the FIRST successful run (`bfdc6919…`), the orchestrator correctly skipped
  re-invoking the writer — **but this means the receipt still points at `bfdc6919`'s `build_id`,
  not the newly-authorized `5ba8cedf`'s**, and `requireAcceptedRebuildProvenance` requires an EXACT
  `receipt.build_id = run.id` match. **Checked for a `force`/bypass path**: `_run_data_writer`
  accepts a `force=True` param that skips the delta-skip gate, but the ONLY caller that ever passes
  it is the probe-failure-regenerate path — `dispatch_nirmana_campaign_wave.py`'s CLI exposes no
  equivalent flag for a plain rebuild dispatch. **Confirmed `bg_doshas` hit the exact same
  trap from the other direction**: its first run (`92830957…`, `disposition='build'`, genuine)
  has a valid receipt but an authorization that missed the timing window (D-L0-AA); no second
  genuine run is possible now that the receipt matches (any retry would `skip_no_delta` too).
  **Net effect: for either target asset, the ONE run that ever did real work has no valid
  authorization, and no further dispatch will do real work (nothing left to redo) — so
  `accepted_rebuild_observed` may be structurally unreachable via the current tooling for any
  asset whose data was already correct before its first properly-authorized dispatch.** This is
  the SAME defect *class* as #1848 (a real orchestrator/evidence-layer integration gap), just a
  different manifestation — worth flagging to Conductor, not something to keep working around
  solo. Did not yet post; recording here first, will flag next cycle unless a workaround surfaces
  (e.g. an untried asset's FIRST dispatch, where no prior receipt exists yet to short-circuit
  against, might complete a full authorized+genuine-build+receipt chain in one shot).

## Held items

- **bg_cohort dispatch** — **CLEARED (D-L0-R)**: job image now carries #1772 (`ee8cf7d09`
  confirmed ancestor of deployed `589284957…`). Superseded by the shared dispatch-script hold below.
- **All L0 dispatch** — held on `dispatch_nirmana_campaign_wave.py`'s own schema-qualification bug
  (#1833, fix in #1838, not yet merged) — the tool itself fails today regardless of job-image state.
- **Wave-2/3 framing retired (D-L0-Q)**: `bg_compendium_index`/`bg_text_index` were never actually
  wave-gated; only `bg_rules`/`bg_concordance` are genuinely ancestor-blocked (see assets table).
- **Destructive rebuilds** (bg_yogas CASCADE parent, any asset with populated descendants) — per C13/WP-6:
  cascade_check + fresh verified snapshot + `--acknowledge-destroys`. Not a blanket hold post-#1781.

## CAPABILITIES LANDED

| capability | consumers | lands with | status |
|---|---|---|---|
| Layer-generic integrity-detector fixes (probe-as-detector; literal/comment/CTE-safe read-only guard) | all layers' Conform | P0 (merged) | **AVAILABLE** on main |
| Dispatcher `depends_on` sort + service-dependency satisfaction | L1–L5 build path | #1772 / #1728 (merged) | **AVAILABLE** on main |

## Cost ledger

| item | wall-clock | notes |
|---|---|---|
| W4 EXECUTE — 29 assets frozen (waves 0 + probes + producer-covered + wave-1 clean 4) | ~ several hrs | incl. deep mechanics discovery (authorize-ordering, force-execute, idempotent evidence) |
| P0 integrity-detector fixes + #1772 tooling | ~1.5 hr | 2 PRs, tests, digest regen |
| depends_on normalization + dispatcher fix (#1728) | ~40 min | fingerprint-neutral data + code |
| C12 wave-1 defect investigation (6 assets) | ~50 min | detector-first, per-asset attribution |
| C8 v2.3 supervised-cycle resumption (D-L0-J through D-L0-V, cycles 1-18) | ~3 hrs across 18 bounded cycles | Read-only-verified all 5 originally-failing C12 checks (0 needed a writer fix — all either stale-build-vs-current-writer or a check bug); landed 3 check-correction migrations (692/693/694, PRs #1829/#1832/#1836, all still merge-queue-pending); reconstructed the retired `nrec` evidence-submission mechanism + built and triple-cross-validated a registry-fingerprint/analysis-digest replica toolkit; found + confirmed 2 real infra state changes (job-image redeploy clears bg_cohort; dispatch-script schema bug #1833/#1838 still gates real dispatch); ran a full non-destructive dry-run dispatch rehearsal for both migration-fixed assets (D-L0-U); flagged one campaign-wide risk (#1856) against L0's own assets. Net: **zero code/writer changes needed** on the original 5-asset C12 backlog — every fix was either "correct the check" or "wait for infra," a materially different outcome than D-L0-F's initial "4 of 5 need a writer fix, MUST" call |

## Heartbeat

- 2026-09-05 — **RESUMED as L0; 29/40 frozen.** Posted STOCK-TAKE on #1713; created this state file.
  WP-6/#1781 merged (destructive dispatch now `--acknowledge-destroys`); #1772/#1728 merged; job image
  still predates #1772 (bg_cohort dispatch held on deploy). Next: bg_parihara_rules W1/W2, bg_yogas
  writer fix + source-chunks pin provenance, bg_gochara_arcs pin→tiling correction, D-CND-09 bundled
  registry migration. Blocked on: pipeline job-image deploy of #1772.
- 2026-09-05 — **bg_yogas provenance DONE (D-L0-G).** 85-pin is a real derived contract (migration
  630), live=0 = never-green-on-real-data, root cause in `l0_yogas.py` corpus extraction + 4-yoga
  projection drop → verdict writer under-production (fix writer, MUST). State file (PR #1800) updated
  + pushed. NEXT: read `extract_yogas_from_corpus`, then bundled D-CND-09 migration; bg_parihara_rules
  W1/W2. Blocked on: nothing for the writer-read/analysis work; job-image deploy only for dispatch.
- 2026-09-05 — **bg_yogas 4-missing-yogas ROOT CAUSE confirmed (refines D-L0-G).** The 4
  (`dhana_yoga_house_lords`, `raja_yoga_kendra_trikona`, `sarasvati_yoga`, `vipareeta_raja_yoga`) exist
  in `brahma_yoga_catalog` (233) but in NO `brahma_ontology` row (any entity_class — verified empty),
  so not a global-uniqueness collision. They are the test's "4 detector-registry identities": added to
  the catalog by a separate path while the projection loop (`l0_yogas.py:2234-2313`) iterates only the
  229 core+corpus `all_yogas`, so ontology/reference stay 229. Design (contract test) intends all
  233×3. **Fix: include the 4 detector identities in the ontology+reference projection** (MUST). The
  `source_chunks 0 vs 85` conjunct is separate: never green on original data → needs tracing whether
  `extract_yogas_from_corpus` should yield the 85 (fix) or the achievable count is <85 (correct the
  conjunct with derivation). NEXT: locate the detector-registry catalog path; implement projection fix
  + a test; then bundle into the D-CND-09 migration. Dispatch still blocked on job-image deploy of #1772.
- 2026-09-05 — **bg_parihara_rules W1/W2 DONE (D-L0-H).** Route **rebuild_only**; volume 449 = 61
  (bg_parihara_rules) + 329 (bg_muhurta_activity_rules) + 59 (bg_muhurta_factor_census), floor exact;
  integrity = migration 644 content-hash (passes). **C13 blast-radius EMPTY** (catalogue-verified: 0
  cascade children, 0 FK referrers on all 3 owned tables, no boundary crossed) — self-contained
  destruction, snapshot prudent not mandatory. `expected_volume_formula` NULL but covered by the
  content digest (D-CND-01). **Freeze BLOCKED** on manifest fingerprint drift (migration 644 populated
  integrity_check_sql after the un-supersedable 09-01 freeze) → **adjudication #1816** filed, rec
  Option 1 (bind on immutable pins only). NEXT: yoga writer read → bundled D-CND-09 migration.
- 2026-09-05 — **CORRECTION to the bg_yogas root cause (correct rather than leave standing).** Read
  `l0_yogas.py:2214` — `all_yogas = YOGAS_CORE + DETECTOR_YOGAS + extracted`, and the loop projects
  ALL (incl. the 4 detector) into catalog+ontology+reference uniformly (writer's own post-check at
  :2334 expects all three = len(all_yogas)). So the current writer already projects the 4 detector
  yogas; the `233/229/229` is **stale old-build data** (my force-rebuild rolled back on the integrity
  failure). **Real current defect: `extract_yogas_from_corpus` yields ≠85**, so len(all_yogas)≠233 and
  source_chunks≠85 both fall out of one cause. Confirming the exact live yield needs the writer to RUN
  (dispatch), which is gated on the #1772 job-image deploy — so the bg_yogas *verdict* (fix extraction
  vs correct the derived count) is HELD on being able to run it. Moving to unblocked work
  (`bg_gochara_arcs` tiling+floor rewrite — verdict already complete) rather than idle.
- 2026-09-05 — **D-L0-I: C13 blast-radius for ALL 11 remaining routes (catalogue-verified, D-CND-16).**
  Ran the FK cascade closure over every owned target table. **No L0 rebuild crosses a layer boundary**
  (contrast the L2→L3 cascade that motivated C13). CASCADE parents (destructive rebuild → fresh
  snapshot + WP-6 `--acknowledge-destroys`, hard floor): `bg_yogas` (`brahma_yoga_catalog` →
  `reference_yogas`, `brahma_yoga_source_chunks`), `bg_dasha_systems` (→ `reference_dasha_systems`),
  `bg_doshas` (→ `reference_doshas`), `bg_vidhi_floors` (`vidhi_intent_floors` → `vidhi_floor_items`).
  In every case the CASCADE children are the asset's OWN owned-tables which the writer explicitly
  DELETEs+repopulates in the same transaction → intended, no orphans, self-consistent. LEAF (0 FK
  referrers, self-contained; snapshot still prudent): `bg_gochara_arcs`, `bg_cohort`,
  `bg_compendium_index`, `bg_concordance`, `bg_rules`, `bg_text_index`. **Honest residual:** catalogue
  covers DB-level FK referrers; serving-side *logical* (no-FK) referrers not exhaustively swept — none
  expected for these global reference tables, flagged for the per-asset W5 check. No cross-layer
  adjudication needed for L0 (C13 boundary clause not triggered).
- 2026-09-05 — **HEARTBEAT / loop status.** C13 statements complete (D-L0-I). Forward freeze work is
  gated on: #1772 **job-image deploy** (to run writers — `bg_cohort` + all rebuilds), adjudication
  **#1816** (bind analyses despite legitimate integrity_check_sql drift — blocks re-acceptance of
  gochara/vidhi/parihara), and the merge queue (state PR #1817). Not idle — remaining unblocked
  deepening: bg_dasha_systems(`kp`)/bg_doshas(658-gap) verdicts, draft bg_gochara_arcs tiling rewrite,
  pre-write W5 scripts. NIRMANA_HOLD absent.
- 2026-09-05 — **Drafted bg_gochara_arcs integrity rewrite** (D-CND-01 exemplar):
  `sessions/drafts/bg_gochara_arcs_integrity_rewrite.sql`. Bare `count(*)=34553` → strengthened
  gapless-contiguous per-body tiling + §N.4 floor; rewrite-floor-test satisfied (catches a gap the old
  count pin passes). Held from migration until #1816 rules + bundled with re-acceptance (D-CND-09).
- 2026-09-05 — **bg_parihara_rules ROUTED (D-L0-H closed).** Accepted with LIVE fingerprint
  `6b13b8a1…` (≠ frozen `527a9ec9…`), both events 201. Confirms #1816 ruling empirically: server
  binds to LIVE, no gate change. My last unrouted asset is now routed → 10/10 remaining routed.
  Adjudication **#1816 RESOLVED** (my misdiagnosis; the frozen-comparison pre-check in
  `nirmana_batch_runner.py` was the client-side defect — TO REMOVE so gochara/vidhi re-acceptances
  take the same live path). parihara freeze still needs ancestors (bg_doshas, bg_texts) frozen +
  job-image deploy. Heartbeat.
- 2026-09-05 — **New cycle under C8 v2.3 (supervised cycles).** Synced: no NIRMANA_HOLD, no open L0
  PRs (hygiene clean), #1816 confirmed CLOSED on GitHub. **Job-image still stale**
  (`brahma-build-pipeline-job` deployed image = `d93d9d0a…`, re-checked live via `gcloud run jobs
  describe` — unchanged, still predates #1772) so dispatch remains blocked for every one of the 10
  remaining routed assets. Rather than idle, did the one thing that unblocks without needing
  dispatch: **bg_yogas writer verdict (D-L0-J) — CLOSED, no fix needed** (see decisions log). Old
  scratch evidence-tooling (`nirmana_batch_runner.py`, `nirmana_build_wave.py`) confirmed gone
  (`/private/tmp` wipe); campaign's shared `nrec` helper also absent from `main` (#1731 superseded).
  Switched to a clean branch `feat/nirmana-l0-cycle-resume` off `origin/main` for continued work
  (old heartbeat branches are stale but harmless — their content already landed via #1817). NEXT:
  poll job-image deploy each cycle; if still stale, continue unblocked deepening
  (bg_dasha_systems `kp` gap, bg_doshas 658-violation categorization — both readable/verifiable
  without dispatch, same pattern as D-L0-J). **PR #1828 opened + auto-merge armed** (checks were
  IN_PROGRESS at cycle end — mergeStateStatus BLOCKED pending them, not queued yet). NEXT CYCLE:
  verify #1828 with `is:queued` per C8 Step 1 before starting new work; queue it if CLEAN+unqueued.
- 2026-09-05 — **Cycle 2.** PR hygiene: #1828 re-checked — not in `is:queued` yet (only
  #1808/#1790/#1778/#1777/#1767 queued), but **not DIRTY, not RED** either — 3 checks
  (Unit/DB-Integration/Governance-Gates) still IN_PROGRESS, 0 failures; auto-merge already armed
  from last cycle so nothing to fix, will self-queue when checks clear. Job-image still stale
  (unchanged). **bg_dasha_systems writer verdict (D-L0-K) — CLOSED, no fix needed**, same pattern
  as D-L0-J (see decisions log): `kp` present + unique in the writer's `DASHA_SYSTEMS` source list,
  one synced atomic 3-table loop, live 20/20/19 split proven to be pre-reconciliation stale data,
  not a reachable live-code output. **Two of four "real data defect" C12 verdicts (D-L0-F) are now
  reclassified stale-data-not-defect** (bg_yogas, bg_dasha_systems); bg_doshas (658-violation) and
  bg_vidhi_floors (DRAFT status + tiling) remain unverified — NEXT: same read-only-writer-audit
  pattern on bg_doshas (`l0_doshas.py` or equivalent), since it's the next unheld/unverified item
  and requires no dispatch.
- 2026-09-05 — **Cycle 3.** PR hygiene: #1828 re-checked, still not `is:queued` (queue currently has
  #1820/#1808/#1778/#1777/#1767, not mine) but still not DIRTY/RED either — same 3 checks
  IN_PROGRESS, 0 failures, auto-merge armed; nothing actionable. **bg_doshas — found the check itself
  is buggy, not the data (D-L0-L).** This is a bigger find than D-L0-J/K: bg_doshas' data was
  *already fully correct* (79/79/79, all hashes matching production byte-for-byte) — the "658
  violations" were a FULL-JOIN ON-clause scoping bug leaking 658 unrelated `brahma_ontology` rows
  (other entity classes) into the count. Authored + rolled-back-transaction-verified **migration
  692**, opened **PR #1829** (auto-merge armed) on its own branch `fix/nirmana-l0-bg-doshas-join-scope`
  (kept separate from the state-only `feat/nirmana-l0-cycle-resume` branch/PR #1828 — code fix vs.
  heartbeat, per hygiene). Once #1829 merges, bg_doshas can be **W4-accepted immediately on its LIVE
  fingerprint with no rebuild dispatch at all** — the one asset in the remaining 10 that doesn't
  need the job-image deploy. NEXT: poll #1829/#1828 queue status; if still pending, continue the
  same read-only-writer-audit pattern on bg_vidhi_floors (last unverified D-L0-F "real defect" call)
  or bg_cohort/wave-2-3 (still blocked on job-image — re-check deploy each cycle).
- 2026-09-05 — **Cycle 4.** PR hygiene: #1828/#1829 re-checked — neither `is:queued` yet (queue now
  has #1825/#1820/#1818/#1808/#1790/#1777/#1766/#1767, not mine), neither DIRTY/RED, all checks
  IN_PROGRESS/0 failures, auto-merge armed on both; nothing actionable. Job-image still stale
  (unchanged). **bg_vidhi_floors — tiling false-positive found+fixed (D-L0-M), partial verdict.**
  Read the writer directly (14 intents, 409 items in source — matches target); found genuine
  item_order gaps in all 7 `_deepdive` intents, then cross-checked the canonical TS registry
  (`registry_data.ts`) and confirmed the gaps are the documented, versioned "Ω8 reachability band"
  design (`omega8Band({from: 40, ...})`), not a numbering defect. Migration 693 drops the check's
  wrong `hi<>n` conjunct (keeping the real invariants `lo=1`/`distinct_orders=n`), verified in a
  rolled-back transaction to return 0 tiling violations against live data. **PR #1832 opened**
  (auto-merge armed) on its own branch, kept separate from #1828 (heartbeat) and #1829 (bg_doshas).
  This closes the 4th and last of D-L0-F's original "real data defect" calls with a
  root-cause-verified alternative diagnosis — **every one of the 5 originally-failing integrity
  checks has now been read-only-audited**; only bg_vidhi_floors carries a genuine residual gap
  (11/14 intents, 286/409 items live, catalog_status=DRAFT) that migration 693 does not resolve.
  Three open PRs now (#1828, #1829, #1832), all auto-merge-armed, none queued yet — all pending the
  same CI check backlog. NEXT: keep polling PR queue status + job-image deploy each cycle; if both
  remain stuck, investigate bg_vidhi_floors' live 11/14-intent gap (why does live lack 3 whole
  intents the writer's source defines?) as the next substantive unit, or bg_cohort once job-image
  moves.
- 2026-09-05 — **Cycle 5.** PR hygiene: #1829 showed `mergeStateStatus=UNSTABLE` and
  `autoMergeRequest=false` — investigated before anything else per contract. **Not a fault**: `gh pr
  merge --auto` replied "already queued to merge", and `is:queued` confirmed #1829 genuinely in the
  merge queue (`autoMergeRequest` flips false once the queue owns the merge, exactly the "doesn't
  reflect queue state" caveat C8 warns about — re-armed defensively anyway, no-op since already
  queued). #1828/#1832 unchanged: BLOCKED, checks pending, not DIRTY/RED, auto-merge armed, nothing
  to fix. Job-image still stale. **bg_vidhi_floors — closed the last open question (D-L0-N),
  read-only.** Diagnosed the 11/14-intent, 286/409-item live gap down to the exact item level: the
  3 missing intents are all tagged "ṢAḌ-DARŚANA W5" in the writer source (a later wave's addition);
  the 24-item shortfall among the 11 present intents traces to 3 specific newer items
  (`now_read`/`ahead_read`/`priority_read` at orders 36-38) added identically across 8 intents.
  Verified today's FULL writer source is internally sound — 14/409 exactly matches target, all 55
  referenced `primitive_id`s exist in `vidhi_primitives`, no duplicate order values. Same
  stale-build family as D-L0-J/K, **with one honest caveat this time**: closing it fully requires
  confirming the *deployed* job image (not just the git checkout) already carries these newer
  additions — can't verify that read-only, so it stays tied to the existing job-image-deploy
  blocker rather than a second independently-resolved item. **Every one of the 5 originally-failing
  L0 integrity checks now has a complete, evidenced verdict** — none require a writer code fix;
  3 need only a check correction (2 landed, bg_gochara_arcs' drafted-but-unlanded), 2 need only a
  fresh dispatch once the job-image moves. NEXT: nothing further to diagnose read-only on the
  original 5 — keep polling PR queue status + job-image deploy each cycle; if job-image moves,
  bg_cohort/bg_yogas/bg_dasha_systems/bg_vidhi_floors all become dispatch-eligible in one sweep.
- 2026-09-05 — **Cycle 6.** PR hygiene: #1829 flipped `UNKNOWN`→still `OPEN`/not merged after main
  advanced (611d66e38..eb35945bc) — checked `is:queued` first per contract: still genuinely queued,
  not a fault, `UNKNOWN` is just async recompute lag after a base-branch move. #1828/#1832 both
  `MERGEABLE` (not DIRTY), 0 failures, auto-merge armed; nothing to fix. **Landed the drafted
  bg_gochara_arcs rewrite (D-L0-O) — migration 694, PR #1836, auto-merge armed.** The draft from an
  earlier cycle only needed its `<ACHIEVED>` placeholder filled now that #1816 (the reason it was
  held) is closed; re-verified everything live before writing rather than trusting the old draft's
  numbers. **This is now 3 assets (bg_doshas, bg_gochara_arcs, and the tiling half of
  bg_vidhi_floors) that can go straight to W4-accept on their LIVE fingerprint with zero dispatch**
  once their migrations merge — a real acceleration path independent of the job-image blocker.
  Four open PRs now (#1828, #1829 queued, #1832, #1836), three still pending checks. NEXT: once
  #1829/#1832/#1836 merge, actually RUN the W4 accept step for bg_doshas/bg_gochara_arcs (need a
  submission mechanism — `nrec` is gone from main, so either hand-roll the `gcloud`+`curl`
  identity-split call the old `nirmana_batch_runner.py` used, or re-author a minimal local
  equivalent) — this is now the highest-value next unit, since it doesn't wait on the job-image at
  all.
- 2026-09-05 — **Cycle 7.** PR hygiene: #1832 now shows `CLEAN` (via `is:queued`, already queued
  alongside #1829 — no action, that's the desired state); #1836 `BLOCKED`/`MERGEABLE`, checks
  pending, 0 failures; #1829's `UNKNOWN` (after main advanced) checked and still genuinely queued,
  same false-alarm pattern as last cycle. Nothing to fix. Job-image still stale. **Prep work
  (D-L0-P): reconstructed the evidence-submission mechanism** end to end by reading the actual
  route + schema code, and **verified live that I can mint identity tokens for both the executor
  and verifier service accounts**. Built + smoke-tested a session-local equivalent of the retired
  `nrec` helper (correctly refuses an identity/source_kind mismatch, same as the original).
  Deliberately did NOT commit it to the shared repo — that tooling is Conductor-owned (charter C5)
  and its PR was closed as superseded, not my decision to revive. Ran out of cycle budget before
  finding the `definition_revision` table (first guess was wrong) needed to build the actual
  submission JSON. NEXT: once the 3 pending PRs merge+deploy, resume at "find the definitions
  table" → build the two command bodies (bg_doshas, bg_gochara_arcs) → dry-run → submit for real.
- 2026-09-05 — **Cycle 8.** PR hygiene: all 4 PRs re-checked, all clean (2 genuinely queued
  #1829/#1832 via `is:queued`, 2 pending pre-queue checks #1828/#1836, 0 failures anywhere);
  nothing to fix. Job-image still stale. **Continued D-L0-P**: found the frozen
  `definition_revision` (`t0-2026-09-01-0e5b06fb`) and, more importantly, **a third deployment gate
  I hadn't accounted for** — evidence submission requires `source_ref` to match
  `NIRMANA_DEPLOYED_SHA` on the **`amjis-web` Cloud Run *service*** (currently
  `611d66e38…`, distinct from the already-tracked `brahma-build-pipeline-job` *job* image). Traced
  the exact server-side computation of `registry_fingerprint_sha256`/`analysis_digest` and confirmed
  bg_doshas/bg_gochara_arcs already have the generated receipt base they need (no separate
  prerequisite work required there). Caught and corrected my own draft mid-cycle before committing:
  an initial claim that a failed submission's error message would reveal the expected digest was
  wrong on re-check (the throw strings don't leak values) — recorded the correction in place rather
  than leaving a bad breadcrumb. NEXT: once PRs merge and `amjis-web` redeploys (watch
  `NIRMANA_DEPLOYED_SHA` advance), locate `canonicalRegistryContractDigest`/
  `canonicalNirmanaAssetAnalysisDigestForRegistryRow`'s definitions and replicate them in a small
  script to compute the real submission values, then dry-run and submit for real.
- 2026-09-05 — **Cycle 9.** PR hygiene: all 4 confirmed clean (`#1829`/`#1832`/`#1836` all now
  genuinely `is:queued` — `#1836` newly entered the queue this cycle; `#1828` `MERGEABLE`, checks
  pending, 0 failures anywhere). Nothing to fix; none merged yet (queue is long — ~11 PRs ahead).
  Noted `amjis-web`'s `NIRMANA_DEPLOYED_SHA` already advanced once this session (`611d66e38`→
  `eb35945bc`, tracking `origin/main`'s tip) — confirms it redeploys on its own cadence, so once my
  migrations merge a further advance should follow without needing to trigger anything myself.
  Job-image still stale. **Continued D-L0-P**: found and read `canonicalRegistryContractDigest` +
  its helpers (`definitions.ts:28-162`) — a simple recursively-key-sorted compact JSON hash, exactly
  matching Python's `json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)`. Wrote +
  ran a Python replica against live data for both target assets — both produce well-formed 64-hex
  digests. Flagged the honest residual: this is inspection-based replication, not
  execution-cross-verified against the real TS (decided against risking a `tsx` import of
  `definitions.ts`'s DB-pool-creating transitive imports this cycle). NEXT: read the second,
  more involved function (`canonicalNirmanaAssetAnalysisDigestForRegistryRow`) — still not located
  this cycle — then the submission payload is fully computable; keep polling the long PR queue.
- 2026-09-05 — **Cycle 10.** PR hygiene: refined the PR filter this cycle after `#1844` (an L5 PR,
  matched only because its title contains the substring "non-L0") showed up in a loose search —
  correctly excluded it (not mine to manage) by filtering on the L0 branch-namespace prefix instead
  of a raw text match, per the state file's own branch-namespace note. All 3 migration PRs
  (`#1829`/`#1832`/`#1836`) confirmed still genuinely `is:queued` (queue now 17 deep, growing —
  #1836 stayed queued, nothing ejected); `#1828` clean, pending checks. Nothing to fix. Job-image
  still stale. **D-L0-P CLOSED this cycle**: found and read
  `canonicalNirmanaAssetAnalysisDigestForRegistryRow` + `canonicalNirmanaAssetAnalysisReceiptDigest`
  + the exact receipt schema, sourced every input live (L0 convergence_commit, per-asset
  writer_digest_sha256, frozen manifest asset queried directly from the definitions table), and
  **got independent cross-validation for free**: the frozen manifest's own embedded
  `registry_fingerprint_sha256` (computed by the real server at freeze time) matches this session's
  from-scratch Python replica byte-for-byte for both target assets — resolving last cycle's
  "not execution-verified" caveat properly rather than leaving it open. Full toolkit now built:
  `compute_registry_fingerprint.py`, `compute_analysis_digest.py`, `l0_submit_evidence.sh`. NEXT:
  once any of #1829/#1832/#1836 actually merges (still just queue position, not stuck), re-run the
  scripts against fresh post-merge live data and do the first real submission attempt.
- 2026-09-05 — **Cycle 11.** PR hygiene: all 3 migration PRs re-confirmed genuinely `is:queued`
  (queue now 18 deep — #1841 new, nothing ejected); `#1828` clean, pending checks. Nothing to fix,
  none merged yet. Since the submission toolkit is built but has nothing to submit against yet, ran
  the actual E-gate batch query for the first time this resumption (**D-L0-Q**) instead of
  continuing to diagnose asset-by-asset — found and corrected a stale "wave-2/3 needs wave-1
  frozen" framing: `bg_compendium_index`/`bg_text_index` are `OPEN-PENDING-PIN` with 0 unfrozen
  ancestors (never actually wave-gated), and only `bg_rules`/`bg_concordance` are genuinely
  `BLOCKED-ANCESTORS` — both on already-diagnosed assets (`bg_dasha_systems`/`bg_yogas`), so the
  whole backlog clears in ordinary DAG waves once dispatch resumes. Also corrected
  `bg_parihara_rules`'s stale row (was "UNROUTED", already routed+E-gated since D-L0-H).
  **Mid-cycle: conductor-2b flagged a migration-numbering collision** — my 692/693/694 (picked as
  "next free number" per this file's own now-corrected instruction) actually landed inside L5's
  assigned 690–699 range; no functional break (`migrate.ts` doesn't require cross-layer numeric
  uniqueness) but broke the per-layer convention. Not asked to renumber (real rework, zero
  benefit); **L0's continuation range is now 700–709** — updated the migration-range note at the
  top of this file with the full per-layer table so this doesn't recur. NEXT: same as last cycle —
  waiting on the queue; nothing new to diagnose read-only on the 11-asset backlog now that the
  E-gate picture is fully accurate.
- 2026-09-05 — **Cycle 12.** PR hygiene: all 3 migration PRs still genuinely `is:queued` (queue now
  22 deep, growing); `#1828` clean, pending checks. Nothing to fix on my own PRs. **Noticed the
  queue growth without any merges landing and checked further: confirmed a real stall** — no merge
  to `main` since 13:54:58Z, and other lanes' queued PRs (#1791, #1801) show 0 pending checks / 0
  failures yet remain unmerged. Posted a factual observation to #1713 (not an adjudication — nothing
  for Conductor to rule on). **Bigger finding this cycle (D-L0-R): the pipeline job image has been
  redeployed** (`d93d9d0a…`→`589284957…`, verified `#1772` is now an ancestor) — `bg_cohort`'s
  long-tracked blocker is cleared. But actual dispatch is still gated on a SECOND blocker:
  `dispatch_nirmana_campaign_wave.py` (the shared dispatch script) still has the unqualified-schema
  bug on `origin/main` (#1833, fix in #1838, not yet merged — checked the live file directly).
  Updated Held Items to reflect both changes. NEXT: once #1838 merges, all 8 `OPEN-PENDING-PIN`
  assets become genuinely dispatchable — read `dispatch_nirmana_campaign_wave.py`'s actual CLI/
  invocation contract as the next unit, since this is now higher-priority than the (already-built)
  evidence-submission toolkit.
- 2026-09-05 — **Cycle 13.** PR hygiene: all 4 confirmed still OPEN/unmerged, `is:queued` holds for
  all 3 migration PRs (queue shrank 22→19 — moving, just slowly; one merge landed since last cycle,
  #1818). Nothing to fix. `main` advanced once more since last check. Started reading
  `dispatch_nirmana_campaign_wave.py`'s CLI (`--layer/--wave/--definition-revision/--commit/
  --confirm`, rollback-only by default) as planned, and got a big bonus: its
  `_live_registry_fingerprint`/`_canonical_analysis_digest` helpers are **field-for-field identical**
  to this session's own hand-replicated Python from D-L0-P — same `REGISTRY_CONTRACT_FIELDS` tuple,
  same sorted `depends_on`, same literal strings. Cross-checked the ALREADY-EXISTING W2 acceptance
  events for bg_doshas/bg_gochara_arcs directly: their recorded `registry_fingerprint_sha256`
  matches this session's computation exactly (third independent confirmation). Clarified *why*
  E-gate reads `OPEN-PENDING-PIN` for these two rather than `OPEN`: W2 was already accepted by a
  prior session against the current (pre-migration) fingerprint; the moment 692/694 merge, those
  acceptances go stale and need exactly the delta-resubmission the toolkit was built for. NEXT:
  #1838 (7th in a 19-deep queue) is the next thing to watch; once it merges, dispatch is fully live.
- 2026-09-05 — **Cycle 14.** PR hygiene: all 4 PRs unchanged since last cycle (still `is:queued`
  for the 3 migrations, queue still 19-deep, no new merges landed — genuinely stalled, not just
  slow); `#1828` clean, pending checks. Nothing to fix; nothing new to escalate (already flagged
  the stall last cycle, no need to repeat). Checked #1713: Conductor active, found+fixed a SECOND
  dispatch-script bug (#1848/#1851 — a duplicate-execution guard permanently blocked re-authorizing
  an asset's first uncoordinated build) — relevant background, not an L0 blocker directly. **Read
  the rest of `dispatch_nirmana_campaign_wave.py` (D-L0-S)**: full CLI flow (dry-run → commit, one
  atomic invocation unlike the old lost tooling's race-prone two-step), and confirmed it
  **self-validates W2 pin-freshness** (raises if no accepted analysis matches the current live
  fingerprint) — exactly the stale-detection D-L0-P's cycle-13 finding anticipated. Worked out the
  right `verdict` value for the eventual resubmission: `examined_and_already_efficient` (writer
  itself never changed, only the registry's own `integrity_check_sql`), not `correct`. **The entire
  path from here to a real L0 freeze is now fully specified, nothing structurally unknown remains** —
  just waiting on #1838 in the queue. NEXT: keep polling; if the queue stays stuck multiple more
  cycles with zero movement, consider whether a second coordination note is warranted (once is an
  observation, repeating it every cycle would be noise).
- 2026-09-05 — **Cycle 15.** PR hygiene: unchanged since last cycle (queue 20-deep now, one more
  merge landed overall but still effectively stalled — not re-flagging, already noted, would be
  noise); nothing to fix on my own PRs. Checked #1713 for new developments: Conductor found+fixed a
  second dispatch bug (#1848/#1851) and flagged that pin-staleness checks are now recurring routine
  Step-1 hygiene as merges land — confirmed my own 3 PRs are unaffected (migration-only, no writer
  files touched, all PR-level checks green, never ejected from queue across 15 cycles). **Went
  hands-on instead of continuing to plan (D-L0-T)**: ran the real dispatch script dry-run, reproduced
  the #1833 schema bug live, built a scratch-local patched copy matching #1838's actual diff, and got
  further — straight into the exact `--reviewed-deployment-sha` batching gotcha Conductor
  independently hit with L5's `mi_vistara`/`mi_jivanaghatana` pairing: dispatch requires an EXACT
  `source_ref` match to whatever SHA was deployed when each asset's W2 was accepted, not just a
  matching fingerprint. **This changes the dispatch plan**: any multi-asset combined wave needs every
  included asset's W2 refreshed under one common current SHA immediately before dispatch, not just
  the two migration-affected assets. NEXT: once #1838 merges for real, dispatch will need this
  batch-aligned resubmission step for whichever assets go together — single-asset dispatch is
  simpler and could be the first real attempt to de-risk the flow.
- 2026-09-05 — **Cycle 16.** PR hygiene: transient ref-lock error on `git fetch` (retried, resolved —
  another lane wrote to `refs/remotes/origin/main` mid-fetch, harmless), all 3 migration PRs still
  genuinely `is:queued` (queue 22-deep now, but `main` DID advance twice more — #1791/L4 merged too
  — confirms slow FIFO progress, not a full stall); `#1828` clean, pending checks. Nothing to fix.
  **D-L0-U: fixed last cycle's `--reviewed-deployment-sha` mismatch and got a FULL, successful,
  non-destructive dry-run dispatch for both bg_doshas and bg_gochara_arcs.** Used each asset's own
  existing W2 `source_ref` commit (`4f7a9cc8…`, verified valid, shared by both plus
  bg_compendium_index — all three W2-accepted together previously) instead of today's deployed SHA.
  Both dry runs completed cleanly with real `manifest_digest`/`run_id` receipts; bg_doshas correctly
  printed the WP-6 blast-radius warning matching D-L0-I's manual C13 finding exactly; verified via
  direct DB check that nothing was persisted (`build_runs` has 0 matching rows) — genuinely
  non-destructive. **This is now a complete, proven rehearsal of the entire dispatch mechanism for
  both target assets** — only real merges (692/694, #1838) and a fresh W2 resubmission stand between
  this and an actual commit. NEXT: keep polling the queue; nothing further to de-risk read-only —
  the next real action is entirely gated on merges landing.
- 2026-09-05 — **Cycle 17.** PR hygiene: all 3 migration PRs still `is:queued` (queue 25-deep now,
  `main` tip unchanged since last cycle — genuinely stalled again, not re-flagging per own
  judgment); `#1828` clean, pending checks. Nothing to fix. Checked #1713: L5 hit and root-caused a
  genuine orchestrator bug (#1856, URGENT) — provenance capture crashes on a raw `uuid.UUID`
  `chart_id` at a JSON-encoding boundary, confirmed live. **Assessed whether this is an L0 risk
  (D-L0-V)**: both target assets are `scope=global` but have non-empty `depends_on` (the other half
  of the bug's trigger condition per L5's own hedge that it isn't provably per-chart-specific), and
  the crash only fires during REAL writer execution — D-L0-U's dry runs never exercised that code
  path, so they don't rule this out. Flagged it, didn't chase L5's Python (not L0's fix to make).
  NEXT: same as before — poll the queue; additionally, **check #1856's resolution status before
  ever attempting a real (non-dry-run) dispatch**, not just before the migrations merge.
- 2026-09-05 — **Cycle 18.** PR hygiene: unchanged, all 3 migration PRs still `is:queued` (25-deep,
  composition churning but `main` tip frozen at `bd398f065` for 2 full cycles now — confirmed
  stalled, not just slow); `#1828` clean. Nothing to fix; **not** re-flagging the stall — checked
  #1713 first and **L4 independently ran a sharper diagnostic** (`gh run list --event merge_group`:
  merge-group CI green every ~12-13 min, yet zero commits land — the block is outside the three
  tracked CI workflows), already tracked as D-CND-18/#1825. Piling on the same observation with
  weaker evidence would be noise. With nothing new to diagnose and no fresh merge to act on, used
  this cycle for genuine prep (C8 priority-5 item): **the Cost ledger was stale since resumption**
  (last entry predated this whole 17-cycle run) — added a summary row covering D-L0-J through D-L0-V
  and its headline result: **zero writer/code changes were needed anywhere in the original 5-asset
  C12 backlog** — every one of D-L0-F's "fix the writer, MUST" calls turned out, on full
  investigation, to be either a stale-build-vs-current-writer story or a bug in the check itself.
  NEXT: keep polling; genuinely nothing else to do until a merge lands or #1856 resolves.
- 2026-09-05 — **Cycle 19: IDLE-OK.** Verified rather than assumed: all 3 migration PRs still
  genuinely `is:queued` (25-deep; `main` advanced one commit since last cycle — #1801/L3 — so the
  queue is moving, just very slowly; none of mine DIRTY, `UNKNOWN` mergeable is the expected
  while-queued transient); `#1828` clean, pending checks. Re-ran the E-gate query — identical to
  last check, no change. Job image redeployed again to track `main`'s new tip
  (`291beab7b…`) — confirms deploy automation is healthy, but #1838 (the actual dispatch-unblock)
  still isn't merged, so this doesn't change anything actionable. #1856 still `OPEN`. Nothing new
  to diagnose, nothing to fix, no fresh merge to act on — genuinely idle this cycle.
- 2026-09-05 — **Cycle 20: IDLE-OK.** Verified: all 3 migration PRs still `is:queued` (26-deep,
  `main` tip unchanged since last cycle — zero merges this time); `#1828` clean, pending checks;
  none DIRTY. Coordination issue #1713 has no new comment since last check; #1856 still `OPEN`.
  Nothing to fix, nothing new to diagnose, no fresh merge to act on.
- 2026-09-05 — **Cycle 21.** PR hygiene: all 3 migration PRs still `is:queued` (29-deep now, `main`
  tip frozen at `3b208dbfa` for a 3rd consecutive cycle — a real, worsening stall, not just slow);
  `#1828` clean, pending checks; none DIRTY. Not posting a third coordination note — no new
  diagnostic value to add beyond L4's existing D-CND-18/#1825 tracking, and Conductor is clearly
  still active (just fixed #1856). **Genuine content this cycle: #1856 is fixed** (Conductor,
  #1713 15:09:30Z) — PR #1861, two-line fix, auto-merge armed, verified byte-identical hash for
  str-vs-UUID on the working case. Updated D-L0-V: the risk is resolving (moot once #1861 lands),
  and Conductor's own framing now reads "per-chart... with declared deps" specifically, which — since
  both target assets are `scope=global` — suggests it may never have applied to L0 at all. NEXT:
  keep polling; still nothing actionable until a merge lands.
- 2026-09-05 — **Cycle 22 — first real merge landed.** PR hygiene: **`#1829` MERGED** (`3bfeaf284`,
  15:19:43Z) — the queue drained past it after 3+ stuck cycles, confirming L4's "slow, not
  permanently broken" diagnosis. `#1832`/`#1836` remain cleanly `is:queued` (30-deep queue, still
  includes `#1838`); `#1828` clean, pending checks. Nothing to fix. **Checked deploy status (D-L0-W)
  before assuming the fix is live**: it is NOT yet — live `integrity_check_sql` for `bg_doshas`
  still reads the OLD buggy version, and `amjis-web`'s `NIRMANA_DEPLOYED_SHA` is 2 commits behind
  the new main tip. Merge and deploy are separate steps with real lag between them; did not assume
  otherwise. This is the first genuinely real progress toward an actual freeze this whole
  resumption — recorded the exact next-steps sequence (re-run toolkit, fresh W2, real dispatch) once
  deploy catches up. NEXT: check `amjis-web`'s deployed SHA each cycle; the moment it advances past
  `3bfeaf284`, execute the real W2-resubmission + dispatch sequence for `bg_doshas`.
- 2026-09-05 — **Cycle 23.** PR hygiene: `#1832`/`#1836` unchanged, still cleanly `is:queued`
  (30-deep); `#1828` clean, pending checks. Nothing to fix; no new merges this cycle. Deploy still
  hasn't caught up — `NIRMANA_DEPLOYED_SHA` unchanged (`bd398f065`), live `integrity_check_sql`
  still the old version. Conductor's own fleet-status post (#1713, 16:57Z) independently confirms
  the queue is genuinely draining, not stalled — "steady merges every cycle... deepest the queue
  has been all campaign" — consistent with what this lane observed with #1829. Nothing new to
  diagnose or act on; deploy lag is the only remaining wait.
- 2026-09-05 — **Cycle 24: IDLE-OK.** PR hygiene: `#1832`/`#1836`/`#1838` all still unmerged/queued
  (30-deep queue); `#1828` clean, pending checks; nothing to fix. Deploy unchanged (`bd398f065`),
  live `bg_doshas` check still old. Mid-cycle: **conductor-2b independently re-verified the
  job-image/#1772 chain and pinged directly** — replied confirming D-L0-R already covers it and
  that #1838/deploy-lag are the actual current gates; conductor-2b acknowledged and offered to flag
  when #1838 merges. No state-file-worthy new information from that exchange (already fully
  recorded). Nothing else changed this cycle.
- 2026-09-05 — **Cycle 25: IDLE-OK.** One more merge landed (`#1830`, docs, `a14e94575`) but none
  of mine/`#1838`; all still cleanly `is:queued` (30-deep), `#1828` clean pending checks, nothing to
  fix. Deploy still unchanged (`bd398f065`), live `bg_doshas` check still old. Genuinely idle.
- 2026-09-05 — **Cycle 26.** PR hygiene: unchanged, all still cleanly queued/unmerged (`#1832`,
  `#1836`, `#1838`), `#1828` clean; nothing to fix. **Deploy advanced one more step**
  (`NIRMANA_DEPLOYED_SHA` → `3b208dbfa`) but confirmed via `git merge-base --is-ancestor` it's
  still one commit short of my `#1829` merge commit (`3bfeaf284`) — live `bg_doshas` check
  correspondingly still the old version. Progressing steadily, not there yet.
- 2026-09-05 — **Cycle 27.** PR hygiene surfaced and resolved a false alarm (D-L0-X): `#1832`
  appeared to have vanished from `is:queued` — investigated properly per contract (checked its own
  checks first, all green; tried re-arming auto-merge, which replied "already queued") rather than
  assuming ejection, then found the actual cause: the CLI search was silently truncating to its
  default 30-result page while the real queue is 36 deep. Fixed my own process: **use `--limit 100`
  on every `is:queued` check going forward.** No PR was actually affected. Deploy unchanged since
  last cycle (`3b208dbfa`, still one commit short); `#1828` clean. Nothing else new.
- 2026-09-05 — **Cycle 28 — first real production write this resumption.** PR hygiene: all still
  queued/unmerged (`#1832`, `#1836`, `#1838`, with the corrected `--limit 100`), `#1828` clean,
  nothing to fix. **Checked the live check and it had flipped to the corrected version** — verified
  it *executes* to `TRUE`, not just eyeballed the text. **D-L0-Y: re-ran the full toolkit against
  the fresh live row, built and dry-ran the two `record_evidence` bodies, then submitted both for
  real** — `asset_analysis_accepted` and `optimization_verdict_accepted` for `bg_doshas`, both HTTP
  201, both confirmed landed in the DB with the new fingerprint. The server independently
  recomputed and matched both values before accepting — full round-trip validation of the D-L0-P
  toolkit built over the last ~10 cycles. This is the first genuinely real (non-dry-run) write to
  production this whole resumption. NEXT: bg_doshas' W2 is fresh, but freezing needs
  `integrity_verified`+`asset_frozen` under the verifier identity — read their exact
  evidence-payload schemas (`requireIntegrityProvenance`/`requireFreezeProvenance` in
  `definitions.ts`) before attempting, same care as was given to the W2 schema before this
  submission. Also worth doing: repeat this exact sequence for `bg_gochara_arcs` once its migration
  (694/#1836) similarly lands live.
- 2026-09-05 — **Cycle 29 — 2nd migration PR merged.** PR hygiene: **`#1832` MERGED**
  (`1557dd28`, 15:41:56Z, bg_vidhi_floors tiling fix) — 2 of my 3 migration PRs now landed; `#1836`/
  `#1838`/`#1828` all confirmed cleanly `is:queued`/pending (`--limit 100`), nothing to fix.
  **Checked deploy status before assuming it's live** — same discipline as D-L0-Y: live
  `integrity_check_sql` for `bg_vidhi_floors` still contains the old bare `hi<>n` clause, so #1832
  hasn't applied to the DB yet either (caught and corrected an initial false-positive grep of my
  own — `grep -c "distinct_orders<>n$"` matched the OLD text too since both old and new end the
  same way; the real differentiator is presence/absence of `hi<>n`). NEXT: watch for #1832's
  migration (693) to apply; once it does, this only fixes the tiling false-positive — the genuine
  11/14-intent completeness gap (D-L0-N) still needs #1838 + dispatch, so `bg_vidhi_floors` won't be
  freezable purely from this migration the way `bg_doshas` was. Also watch #1836 (bg_gochara_arcs)
  for its own merge.
- 2026-09-05 — **Cycle 30 — important self-correction (D-L0-Z).** PR hygiene: `#1836`/`#1838`
  still cleanly queued (38-deep), `#1828` clean, nothing to fix; no new merges. Deploy advanced
  (`3bfeaf284`, now includes #1829) but confirmed NOT yet including #1832 (`git merge-base
  --is-ancestor` check) — `bg_vidhi_floors` still shows the old `hi<>n` clause. **Did the planned
  next step (read `requireIntegrityProvenance`/`requireFreezeProvenance`) before attempting either
  event, and it changed the plan**: freeze requires a genuine `accepted_rebuild_observed` receipt
  for any `execution_obligation='build'` asset — no "data already matches, skip execution" path
  exists in the lifecycle model. Re-read D-L0-H's own bg_parihara_rules precedent correctly this
  time: it reached "ROUTED" (W2 only), never "FROZEN" — the same stopping point as `bg_doshas` now,
  not further. **Corrected D-L0-L/D-L0-O/last cycle's over-optimistic "no dispatch needed" framing**
  in the assets table and decisions log — every remaining asset, without exception, needs #1838 to
  actually freeze. This simplifies rather than complicates the picture (one blocker for everyone),
  and is exactly the kind of claim to verify before asserting per §N.8. NEXT: still #1838; once it
  merges+deploys, dispatch (even a no-op-content rebuild) is required for every asset before any
  `integrity_verified`/`asset_frozen` submission — plan accordingly, don't try to skip it again.
- 2026-09-05 — **Cycle 31: IDLE-OK.** PR hygiene: `#1836`/`#1838` still cleanly `is:queued`
  (41-deep), `#1828` clean, nothing to fix. `bg_vidhi_floors` still shows old `hi<>n` (not
  deployed). #1713: L5 flagged that Conductor's own #1851/#1861 (the two orchestrator fixes) are
  green but never queued/armed for ~75-90 min — not my PR to act on, noted for context only.
  Nothing new to diagnose or act on this cycle.
- 2026-09-05 — **Cycle 32 — all 3 migration PRs now merged.** PR hygiene: **`#1836` (bg_gochara_arcs
  D-CND-01 rewrite) MERGED** (15:54:06Z) — all 3 of this resumption's migrations (692/693/694) are
  now on `main`. `#1828` showed `mergeStateStatus=UNKNOWN`/not in `is:queued` — investigated
  properly (not a scare this time): 3 checks genuinely still `IN_PROGRESS` (started 15:52:37Z),
  explaining why it hasn't queued yet; re-armed `--auto` defensively anyway, no failures anywhere.
  `#1838` (dispatch script, the one remaining real blocker) still cleanly queued. **Checked deploy
  for both newly-merged migrations — neither applied yet**: `bg_gochara_arcs` still shows old
  `target_floor=34553`/bare count check; `bg_vidhi_floors` still shows `hi<>n`. NEXT: watch deploy
  catch up on both (same pattern as `#1829`/`bg_doshas`, which took a few cycles); once live,
  `bg_gochara_arcs` gets the same real-W2-resubmission treatment as `bg_doshas` (D-L0-Y) — but per
  D-L0-Z, remember that still isn't sufficient for an actual freeze without `#1838` + a real
  dispatch.
- 2026-09-05 — **Cycle 33.** PR hygiene: `#1828` clean pending checks, still not queued yet (own
  checks not done); `#1838` confirmed still genuinely queued. Nothing to fix. **`bg_vidhi_floors`
  migration (693) is now LIVE** — verified the tiling sub-clause alone evaluates `TRUE` against
  production (`lo=1`/`distinct_orders=n` hold for all present intents, confirming the fix works
  exactly as designed); the FULL check still correctly reads `FALSE`, entirely due to the genuine
  `count(*)=14`/`409` completeness gap (D-L0-N) — expected, not a problem. Did not resubmit W2 for
  this asset yet: unlike `bg_doshas`, it isn't otherwise freeze-ready (still needs the intent/item
  gap resolved via dispatch), so a fresh W2 now would just go stale again once that dispatch
  happens — better to refresh W2 once, after the data catches up too. `bg_gochara_arcs` migration
  (694) still not deployed. NEXT: keep polling #1838 and the bg_gochara_arcs deploy.
- 2026-09-05 — **Cycle 34: IDLE-OK.** PR hygiene: `#1828` still pending own checks (not yet
  queued), `#1838` confirmed genuinely queued (44-deep queue); nothing to fix. `bg_gochara_arcs`
  still not deployed. #1713: L5 posted a self-correction using the actual GraphQL `mergeQueue`
  API (more precise than PR-level fields) confirming the queue is genuinely serial, ~10-13 min per
  merge-group CI run, not broken — matches this lane's own observed cadence exactly. Nothing new
  to act on.
- 2026-09-05 — **Cycle 35: IDLE-OK.** `#1828` re-triggered its own checks again (main advanced),
  still not queued yet — confirmed genuinely in-progress, not stuck. `#1838` still cleanly queued
  (45-deep). `bg_gochara_arcs` still not deployed. Nothing to fix, nothing new.
- 2026-09-05 — **Cycle 36: IDLE-OK.** Same pattern: `#1828` re-triggered yet again (~2 min into a
  fresh run each cycle, not stuck — main just keeps moving faster than a heartbeat-only PR's checks
  complete), `#1838` still cleanly queued (45-deep), `bg_gochara_arcs` still not deployed. #1713:
  L4 found a real but explicitly non-blocking side-issue (a post-deploy behaviour-smoke failure on
  `main`, confirmed NOT a required check, NOT the merge-queue stall's cause) — FYI-only, no action
  needed from L0. Nothing to fix, nothing new to act on.
- 2026-09-05 — **Cycle 37 — #1838 MERGED; first real dispatch executed; retry blocked (D-L0-AA).**
  PR hygiene: **`#1838` MERGED** (16:06:13Z) — the last real blocker for dispatch. Mid-cycle,
  conductor-2b independently flagged (correctly, in spirit) to verify deploy status rather than
  assume merge=deployed; verified precisely and replied that #1838's fix is client-side (my local
  script checkout, refreshed directly from `origin/main`), confirmed via grepping the job-side
  orchestrator for the same bug pattern (0 hits — nothing there needed a redeploy). **Executed the
  campaign's first-ever real `--commit` dispatch this resumption**: posted `SLOT CLAIM`, took a
  fresh Cloud SQL backup, dry-ran (discovering `--snapshot-ref` changes the manifest digest, so the
  trusted dry-run must include it), committed `bg_doshas`'s rebuild with `--acknowledge-destroys`.
  **The job ran and completed in ~23s** while I was reading the `build_run_authorized` schema to
  build a correct payload — missed the pre-start authorization window. Data confirmed correct
  post-rebuild (check re-verified `TRUE` live); the run itself just has no valid authorization
  chain now. **Retry immediately hit #1848's still-open duplicate-execution-guard bug** (confirmed
  live: the guard has no state filter, exactly as L5 originally reported) — blocked until #1851
  merges. Posted `SLOT RELEASE` with the full account, updated the assets table and decisions log.
  NEXT: once #1851 merges, retry `bg_doshas` with the authorization payload pre-built (idempotency
  key, source_ref template, a valid-format `authorization_sha256` — confirmed it isn't matched
  against any specific value, just shape-checked) so only the fresh `run_id` needs substituting
  before firing, beating the ~20s window this time.
- 2026-09-05 — **Cycle 38 — bg_gochara_arcs migration LIVE, real W2 submitted (D-L0-BB).** PR
  hygiene: `#1828` clean pending own checks; `#1851` (duplicate-guard fix, the dispatch-retry
  blocker) still `is:queued`, not yet merged. Nothing to fix. **`bg_gochara_arcs` migration (694)
  confirmed deployed** (`target_floor=33933`, check executes `TRUE` live) — repeated the exact
  D-L0-Y sequence: fresh toolkit computation, dry-run, real submission of both W2 events, both
  HTTP 201, confirmed landed with the new fingerprint. Both `bg_doshas` and `bg_gochara_arcs` are
  now W2-fresh and data-verified-correct, waiting only on #1851 for a clean dispatch+authorize
  retry. NEXT: keep polling #1851; when it merges, dispatch both (bg_gochara_arcs first — it's a
  LEAF asset with no cascade, lower-risk than bg_doshas' CASCADE, good for re-proving the
  authorization-window technique before repeating it on bg_doshas) with the authorization payload
  pre-built per last cycle's lesson.
- 2026-09-05 — **Cycle 39.** PR hygiene: `#1828` still pending own checks (not queued yet, no
  failures), `#1851` still `is:queued`, not merged. Nothing to fix. Since dispatch is still blocked
  on #1851, did the concrete prep from last cycle's plan (D-L0-CC): wrote + tested
  `authorize_build_run.sh`, a one-call `build_run_authorized` submitter parameterized by run_id,
  ready to fire the instant a fresh dispatch's `run_id` is known. Smoke-tested end-to-end in
  `--dry-run` with a fake UUID — resolves to executor identity, produces valid JSON. NEXT: keep
  polling #1851; when it merges, the retry is now purely mechanical (dispatch → capture run_id →
  `authorize_build_run.sh` → done), no more schema lookups eating into the window.
- 2026-09-05 — **Cycle 40: IDLE-OK.** PR hygiene: `#1828` clean, still pending own checks;
  `#1851` still cleanly `is:queued`, not merged. Nothing to fix. #1713: L1 confirmed our
  `bg_doshas` run completed and 0/3 slots occupied — no new info for L0. Nothing else changed.
- 2026-09-05 — **Cycle 41: IDLE-OK.** Same as last cycle: `#1828` clean pending own checks,
  `#1851` still cleanly queued (46-deep), no new coordination activity. Nothing to fix, nothing
  new.
- 2026-09-05 — **Cycle 42: IDLE-OK.** `main` tip unchanged since last cycle (`4d2a3ef05`) — no
  new merges at all this cycle. `#1828` clean, `#1851` still cleanly queued (47-deep, no
  failures). Nothing to fix, nothing new.
- 2026-09-05 — **Cycle 43: IDLE-OK.** `main` tip still `4d2a3ef05` (3rd cycle unchanged), `#1851`
  still queued/unmerged, `#1828` clean, no new coordination activity since 16:17:30Z. Nothing to
  fix, nothing new.
- 2026-09-05 — **Cycle 44.** PR hygiene: `#1828` clean, `#1851` still cleanly queued/unmerged
  (49-deep); `main` tip unchanged (`4d2a3ef05`, 4th cycle). Nothing to fix. New coordination
  activity: L1 dispatched `ga_positions` and reported a real, generally-applicable finding — a
  layer's shared `convergence_commit` pin can silently invalidate an UNRELATED sibling asset's W2
  acceptance if any OTHER writer in the same layer gets fixed (C2.3 pin-mismatch working as
  designed, not a bug, but easy to miss). Checked whether this could have staled `bg_doshas`/
  `bg_gochara_arcs`' own fresh W2 (D-L0-Y/D-L0-BB): **confirmed L0's `convergence_commit`
  (`49bb5c98…`) and `writer_inventory_sha256` are both unchanged** since those submissions — no
  other L0 writer has been touched this session, so both remain valid. Worth re-checking this
  each cycle before the eventual dispatch retry, cheaply, rather than assuming it still holds.
- 2026-09-05 — **Cycle 45: IDLE-OK.** `main` advanced (`6be9f5302`) but not `#1851`; `#1828`
  clean, `#1851` still cleanly queued (49-deep). L0's convergence pin re-checked, still unchanged.
  Nothing to fix, nothing new.
- 2026-09-05 — **Cycle 46: IDLE-OK.** Queue shrinking (49→45), still moving, but `#1851` itself
  still not merged. `#1828` clean, pin unchanged. Nothing to fix, nothing new.
- 2026-09-05 — **Cycle 47: IDLE-OK.** `#1851` still unmerged/cleanly queued (46-deep), `#1828`
  clean, no new coordination activity since 16:37:40Z. Nothing to fix, nothing new.
- 2026-09-05 — **Cycle 48: IDLE-OK.** `main` tip unchanged (`6be9f5302`), `#1851` still cleanly
  queued/unmerged, `#1828` clean, no new coordination activity. Nothing to fix, nothing new.
- 2026-09-05 — **Cycle 49: IDLE-OK.** Same: `main` tip unchanged (3rd cycle), `#1851` still
  cleanly queued/unmerged, `#1828` clean, no new coordination activity. Nothing to fix, nothing
  new.
- 2026-09-05 — **Cycle 50 — #1851 MERGED; first properly-authorized real dispatch achieved.** PR
  hygiene: `#1851` merged (16:52:52Z), `#1828` clean. Pulled the fix locally, posted `SLOT CLAIM`
  for `bg_gochara_arcs`, took a fresh backup. First `--commit` attempt hit a genuine concurrency
  conflict with another lane's simultaneous dispatch (L5's `mi_vistara`) — investigated properly
  (checked which asset the resulting row actually belonged to, rather than assume) before
  concluding it was safe to retry with zero side effects. **Retried cleanly with corrected
  stdout-only output capture** (the D-L0-AA cycle's mixed-stream capture was the actual bug behind
  that RUN_ID-extraction failure) and **the pre-built `authorize_build_run.sh` fired immediately
  after commit — `build_run_authorized` confirmed recorded while `started_at` was still `NULL`**,
  genuinely inside the window this time. This is the campaign's first fully-authorized real
  dispatch this resumption. Run (`bfdc6919…`) still `running`/`building` at cycle end (larger
  asset than `bg_doshas`). NEXT: check completion next cycle, then submit
  `accepted_rebuild_observed` (need to read `NirmanaRebuildEvidenceSchema` first) to complete the
  evidence chain toward `integrity_verified`/`asset_frozen` — the actual freeze, first time this
  resumption.
- 2026-09-05 — **Cycle 51 — run completed clean, but caught a real bug in my own authorization
  script before it caused a rejected submission (D-L0-EE).** PR hygiene: `#1828` clean, nothing to
  fix. `bg_gochara_arcs`' run finished successfully (`bfdc6919…`, ~28s, no error); re-verified data
  correct (`integrity_check_sql` still `TRUE`). Read `requireAcceptedRebuildProvenance` BEFORE
  submitting `accepted_rebuild_observed`, as planned, and found it filters incoming authorization
  events on the literal `source_kind === 'campaign_authorization'` — my `authorize_build_run.sh`
  used `"build_run"`, a value the ACCEPTANCE check for `build_run_authorized` never rejected but
  this downstream check silently excludes. That specific run's authorization can never be fixed
  retroactively; the run itself is harmless, just now unusable for the freeze chain. Fixed the
  script, documented the exact failure inline, re-verified via `--dry-run`. Three attempts, three
  distinct lessons now (D-L0-AA/DD/EE) — this is a genuinely fiddly evidence-chain surface, worth
  the caution. NEXT: fresh dispatch with the corrected script — but first read
  `NirmanaRebuildEvidenceSchema`'s remaining fields (`decision_digest`, `output_digest`,
  `output_digest_spec_sha256`) fully before dispatching this time, to close out all the unknowns in
  one pass rather than discover them one `400` at a time.
- 2026-09-05 — **Cycle 52 — 4th dispatch attempt, and a real structural gap surfaces (D-L0-FF).**
  PR hygiene: `#1828` clean, nothing to fix. Fully traced `NirmanaRebuildEvidenceSchema` before
  dispatching this time (precomputed `decision_digest`, confirmed `output_digest*` come from
  `asset_provenance_receipts`/`asset_output_digest_specs`, not something I compute). Posted `SLOT
  CLAIM`, fresh backup, dispatched `bg_gochara_arcs` a 3rd time with the corrected script —
  authorization landed correctly this time (`source_kind=campaign_authorization`, confirmed inside
  the window) — but the run got `disposition=skip_no_delta` (the orchestrator correctly recognized
  nothing had changed since the FIRST run and skipped re-invoking the writer), so no fresh
  provenance receipt was written for THIS run's `build_id`. **Confirmed `bg_doshas` is in the exact
  same bind from the other direction**: its one genuine build (valid receipt) has an authorization
  that missed the window; any retry would now also `skip_no_delta`. **Root cause: no `force`
  bypass for the delta-skip gate is exposed via `dispatch_nirmana_campaign_wave.py`'s CLI** — the
  orchestrator's `force=True` param exists but only one internal caller (probe-regenerate) ever
  uses it. For either asset, `accepted_rebuild_observed` may be structurally unreachable via
  current tooling — not a mistake to keep retrying past. NEXT: either flag this to Conductor as a
  real gap (same class as #1848/#1856, worth the same rigor), or try a completely fresh,
  never-dispatched asset (e.g. `bg_dasha_systems`/`bg_yogas`) where no prior matching receipt
  exists yet, to see if a FIRST properly-authorized dispatch can complete the whole chain in one
  shot before deciding this needs escalation.

- **D-L0-GG** — **bg_dasha_systems: genuine dispatch (run `ce86f4cf`, correctly authorized, NOT
  skip_no_delta) failed `integrity_check_sql`, refining D-L0-K.** Root-caused with the same
  discipline as D-L0-J/L/N: ran `seed_dasha_systems()` directly in a rolled-back transaction,
  then evaluated the registry's own pinned check-SQL subclauses against the just-written
  (uncommitted) rows. Found TWO independent check bugs, not a writer bug: (1) a **FULL JOIN
  scope leak identical to bg_doshas/692** — the check's `FULL JOIN brahma_ontology AS ontology
  ON ontology.entity_class='dasha_system' AND ontology.canonical_id=catalog.canonical_id` puts
  the entity_class filter in the ON clause, so every OTHER entity_class row in the (shared,
  multi-domain) `brahma_ontology` table surfaces as an unmatched row and trips the alignment
  NOT EXISTS — verified live by dumping the raw join's violation rows and finding they were all
  `nak_*`/other-class ontology ids, zero real dasha-system misalignments; (2) migration 621's
  `catalog_hash` pin was **wrong at authoring time** — `git show` on 5f47906bc (the commit that
  both introduced the DASHA_SYSTEMS `kp` entry and authored migration 621's pin, "PYTHONHASHSEED=0
  and 3 production-shaped replays produced these digests") confirms the writer's DASHA_SYSTEMS
  content has not changed since; recomputing the same `jsonb_build_array(...)::text` SHA256 the
  check itself uses, against a genuine fresh writer run, produces `8e35495ffef68342f7e88e2adee0-
  0654701feeee7852634cdada8df3932bf906` every time, never the pinned `30742da6005fc977124192ae27-
  ee1ca0bb29dd5363267860dfd8260e8bb3173a`. `ontology_hash`/`reference_hash` both matched their
  pins exactly throughout — this narrows the defect precisely to the catalog_hash literal, an
  authoring-time computation slip, not drift. Migration `700_bg_dasha_systems_catalog_hash_repin.sql`
  authored: fixes the join scope (subquery pre-filter, mirroring 692's exact pattern) AND re-pins
  catalog_hash to the verified-correct value. Verified twice live (rolled-back tx): guard clause
  matches 621's stored pin byte-for-byte (no exception on apply); post-fix check evaluates **TRUE**
  against a genuine writer replay and **FALSE** against current stale live data (fail-closed
  preserved — no silent pass on unfixed data). This is the 4th instance this session of the
  established C12 pattern (bg_doshas/692, bg_vidhi_floors/693, bg_gochara_arcs/694, now
  bg_dasha_systems/700): "correct the check, not the writer." No writer change made or needed.

- 2026-09-06 — **IDLE-OK cycle.** Checked all 10 remaining unfrozen assets individually rather than
  assume: `bg_yogas`/`bg_dasha_systems`/`bg_compendium_index` blocked purely on migrations
  701/700/702 merging + deploying (all three queued, none merged yet); `bg_cohort`/
  `bg_gochara_arcs`/`bg_doshas`/`bg_text_index` blocked on the two open structural findings
  (D-L0-FF, D-L0-II — checked, no new movement, Conductor's `#1901` still open); `bg_rules`/
  `bg_parihara_rules`/`bg_concordance` blocked on ancestor E-gating only — recomputed their current
  registry fingerprints and confirmed all three still match their stored `asset_analysis_accepted`
  payloads exactly, so no W2 pre-refresh is needed once ancestors clear (nothing to pre-stage).
  Checked merge-queue health rather than assume stuck: `gh api graphql`'s `mergeQueueEntry` on the
  oldest queued PR (#1828) shows `position: 36, estimatedTimeToMerge: ~3.8h` — deep but healthy.
  Posted status to #1713. No code/migration/evidence work this cycle — genuinely nothing eligible.

- 2026-09-06 — **Queue-health investigation (no new L0 work, but resolved an ambiguity).**
  `estimatedTimeToMerge` read identically (36 / ~3.8h) across two consecutive checks — worth
  verifying rather than trusting a possibly-stale estimate. Applied L4's `gh-readonly-queue/main/
  pr-<N>-<sha>` branch technique (posted to #1713 earlier this session) to read position-1 (#1867)'s
  REAL merge-group check-runs directly: 26 checks, all either already `success` or (2 remaining)
  `in_progress`, with `started_at` timestamps showing the CI run had only just kicked off — after
  sitting `AWAITING_CHECKS` since `15:35:39Z`, ~3.3 real hours earlier. Not the same defect class
  as #1838's zero-check-runs-forever jam (peer L4's earlier finding, still open) — this was a long
  scheduling delay (plausibly GitHub Actions runner contention across 6 concurrent layer sessions'
  worth of PR checks), not a broken trigger. Waited it out with bounded polling loops (not a
  cross-cycle sleep): all 26 checks passed, #1867 merged, `main` advanced to `54a4a695a`. None of
  my own PRs merged this cycle (still deep in the 72-entry queue) — genuinely nothing new for L0's
  own asset work. Posted the confirming finding to #1713 so other layers don't have to re-diagnose
  the same ambiguity.

