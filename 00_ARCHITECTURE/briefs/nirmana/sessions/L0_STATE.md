---
artifact: L0_STATE.md
canonical_id: NIRMANA_V21_L0_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L0
layer: L0 — Brahmagyan
owner: the L0 session (this file is yours alone — charter C5)
last_updated: 2026-09-07 — 39/40 frozen (bg_yogas/bg_rules/bg_concordance froze via D-NATIVE-06); only
  bg_cohort remains, held on Conductor's C12 carve-out. Issue #2122/PR #2153 arc FULLY CLOSED —
  merged, force-deployed, live-verified end-to-end (actual tool call confirms correct served
  content). #2169 (the systemic deploy-gap this surfaced) stays open, Conductor's call. Back to
  standard IDLE-OK cadence.
---

# L0 — Brahmagyan — SESSION STATE

Charter C9: this file is your memory — update every loop, commit with every PR and at milestones,
so re-pasting the prompt into a fresh session is safe at any moment.

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → `resume/RESUME_L0.md` → this file →
`git fetch origin main` → `gh issue view 1713` + your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 · **Migration range:** 645–649 is Conductor; **L0 uses the existing
  6xx L0 numbers already applied** (640–644) — new L0 registry corrections take the next free number,
  confirmed against `platform/migrations/` before writing.
- **Branch namespace:** `feat/nirmana-l0-*` / `fix/nirmana-*` · **PR prefix:** `L0:` (older ones used no prefix)
- **Worktree:** main checkout `/Users/Dev/Vibe-Coding/Apps/Madhav` + scratch `/private/tmp/madhav-nirmana-l0-w4`
- **Evidence tooling (scratch, Conductor-audited):** `/private/tmp/.../scratchpad/nirmana_batch_runner.py`
  (stage analysis+verdict), `nirmana_build_wave.py` (dispatch/authorize/force-execute/evidence),
  `producer_covered.py`, `freeze_probes.py`, `run_dispatcher.py`. Canonical helper is now `nrec` (#1731).

## Position

**39/40 frozen.** bg_gochara_arcs, bg_dasha_systems, bg_doshas, bg_vidhi_floors, bg_parihara_rules,
bg_compendium_index, bg_rules, bg_text_index, bg_concordance, bg_yogas all froze across the sessions
between the last detailed heartbeat entry below and 2026-09-06/07 (see heartbeat log for the
bg_yogas/D-NATIVE-06 account — the fullest-documented one; the others' individual W1→freeze accounts
were not re-transcribed into this file session-by-session and are recoverable from their PRs/issue
#1713 history if ever needed). **Only `bg_cohort` remains unfrozen**, blocked on Conductor's C12
carve-out (see Held items). Separately, **issue #2122** (F-D21/F-D23: `bg_vidhi_primitives`'
`from_moon_view` Vidhi primitive pointed at an inert `reference_point` arg on
`ganita_chart_facts_get`) surfaced via a Conductor fleet-status post on #1713 — this is NEW L0 work,
independent of the freeze-tracking count above (it does not un-freeze `bg_vidhi_primitives`; it
corrects a served primitive's routing). Fixed and shipped as **PR #2153, merged, force-deployed, and
live-verified end-to-end — the arc is CLOSED** (see heartbeat for the full account, including the
deploy-pipeline gap it surfaced, filed as `#2169`, still open at the systemic level).

## The 1 unfrozen asset

| asset | route | status / blocker |
|---|---|---|
| bg_cohort | rebuild_only | held on Conductor's C12 carve-out (dep on `bg_ephemeris_engine` service semantics) — see Held items |

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

## Held items

- **bg_cohort dispatch** — sole remaining unfrozen L0 asset. Held on Conductor's C12 carve-out; nothing
  eligible for L0 to act on until Conductor rules. IDLE-OK each cycle unless new instructable work
  (e.g. #2122-class discoveries) surfaces via #1713.

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
- **[Honest gap]** Between the entry above and 2026-09-06, `bg_gochara_arcs`, `bg_dasha_systems`,
  `bg_doshas`, `bg_vidhi_floors`, `bg_parihara_rules`, `bg_compendium_index`, `bg_rules`, `bg_text_index`
  all froze — real work landed (per PR/issue history and #1713 posts) but the per-asset heartbeat
  entries for that stretch were not transcribed into this file cycle-by-cycle. Not fabricating them
  here; recoverable from #1713 + each asset's merged PR if ever needed. This entry exists so the gap
  itself is visible rather than silently absent (§N.4/§N.8 discipline: an honest gap beats a fabricated
  one).
- 2026-09-06 — **D-NATIVE-06: bg_yogas root cause fixed and frozen (native-ratified).** `l0_yogas.py`'s
  `extract_yogas_from_corpus` had a dict-row-as-tuple bug silently yielding 0 corpus-extracted yogas on
  every real dispatch (the exact defect class D-L0-G/D-L0-F predicted, now confirmed by actually
  running the writer once the #1772 job-image blocker cleared). Fixed the writer; rebuild produced the
  full 233×3 projection + 85 `brahma_yoga_source_chunks` links; migration 630's pin passed as originally
  authored (no check weakened). This is a **registered writer** — fixing it moved its digest in
  `nirmana-writer-digests.json`, which moved L0's aggregate `writer_inventory_sha256`. Proved via direct
  read of `buildLayerReceipts` (`nirmana-analysis-receipts.ts`) that the per-asset
  `NirmanaAnalysisReceiptBase` hashed into `analysis_digest` consumes only `writer_digest_sha256` +
  `layer` + two static grounding constants — the aggregate is used ONLY as
  `assertNirmanaWriterInventoryMatchesConvergence`'s per-layer availability gate, never as digest input
  — so transparently re-deriving the aggregate cannot retroactively change any OTHER asset's already-
  accepted `analysis_digest`. Re-pinned via the established procedure: regenerated the writer-digest
  inventory (confirmed only `bg_yogas` changed, other 35 frozen L0 writers + `probe_digest` byte-
  identical), re-derived + re-pinned L0's `writer_inventory_sha256` in
  `nirmana_analysis_layer_pins.py`'s `L0_FROZEN_PINS` (dated comment justifying the re-pin), regenerated
  `nirmana-analysis-layer-pins.json` (L0-slice-only splice, L1-L5 byte-identical), updated the one
  hardcoded "L0 preservation" test value in `nirmana-analysis-receipts.test.ts`. bg_yogas, bg_rules,
  bg_concordance all froze off the back of this. **L0 now 39/40** — only `bg_cohort` remains, held on
  Conductor's C12 carve-out. NEXT: nothing eligible for L0 until Conductor rules on bg_cohort; watch
  #1713 for new discoveries in the meantime (this is how #2122 below was found).
- 2026-09-06/07 — **Extended IDLE-OK streak (60+ cycles).** L0 at 39/40, `bg_cohort` genuinely blocked
  on Conductor. No fabricated work; heartbeats recorded `noop: true` per cycle. Interrupted by
  discovering **issue #2122** via a Conductor fleet-status post on #1713.
- 2026-09-07 — **Issue #2122 (F-D21/F-D23) diagnosed, fixed, shipped as PR #2153.**
  `bg_vidhi_primitives`' `from_moon_view` Vidhi primitive's `live_tool`/`tool_args` pointed at
  `ganita_chart_facts_get` with a `reference_point: 'moon'` arg that tool doesn't accept (dead/inert —
  confirmed via `register_p1_ganita.ts`'s Zod schema, no such param). Re-pointed at the real consumer,
  `ganita_transit_anchors_get` (chart_id-only), across all 3 sites: canonical `registry_data.ts`, the
  Python seed-writer mirror `bg_vidhi_primitives.py`, and the generated `platform-mcp` mirror (via
  `npm run codegen:vidhi`, never hand-edited). Migration 705 fixes the stale LIVE production row
  (guarded on exact pre-state, verified via rolled-back replay). 5 test/check suites green locally
  before shipping (registry-completeness, codegen-parity, writer unit test, vidhi-parity census gate,
  offline governance checks). This does **not** affect the 39/40 freeze count — `bg_vidhi_primitives`
  was already frozen; this corrects a served primitive's routing.
- 2026-09-07 — **PR #2153 came back RED on 2 gates; both root-caused and fixed this cycle.**
  (1) **Governance Gates** ("writer digest inventory is stale") — same gotcha class as bg_yogas:
  editing `bg_vidhi_primitives.py` (a registered writer) moved its digest. Fixed via the identical
  re-pin procedure used for D-NATIVE-06 above (regenerated `nirmana-writer-digests.json` — confirmed
  ONLY `bg_vidhi_primitives` changed, `probe_digest` unchanged; re-derived + re-pinned L0's aggregate
  to `5125cccb68715ebc6054c3ce47bc4c047684445249503a4c4dabd85e0d036178` in
  `nirmana_analysis_layer_pins.py`; regenerated `nirmana-analysis-layer-pins.json`, L0-slice-only,
  L1-L5 byte-identical; updated the hardcoded test value). Both offline governance checks
  (`provenance_inventory --check`, `nirmana_analysis_layer_pins --check`) pass locally (exit 0).
  (2) **DB Integration Tests** — a genuinely new discovery, not a repeat of the bg_yogas pattern:
  `nirmana_l0_wave0_remaining_integrity_contract.test.ts`'s "real PostgreSQL behavior" test failed
  executing `bg_vidhi_primitives`' stored `integrity_check_sql`. Root cause: migration 628 (already
  applied, never editable) hardcodes the OLD `from_moon_view` content hash
  (`41463a2be208bc33c645cc943a242a2cd5b4906e8babd3dc68fe5ef566738cce`); the test's own
  `connectPrepared()` fixture populates its throwaway `vidhi_primitives` table by dumping the CURRENT
  (already-corrected) writer via `bg_vidhi_primitives.py --dump-json`, so replaying migration 628 alone
  leaves a check that legitimately fails against the fresh data. This is the C12 "correct the check,
  not the writer" pattern applied to a NEW asset: authored **migration 706**
  (`706_bg_vidhi_primitives_from_moon_view_content_repin.sql`) re-pinning `integrity_check_sql` to the
  corrected content hash (`cc57ac4d59218bcb818dda0288151f2d72107afa0c0ef664df7520cffea90320`), guarded
  on the exact migration-628 pre-state, verified twice via rolled-back replay against live production
  DB (isolation + full 705→706 sequence). Wired `await client.query(migration706)` into the test
  immediately after the first `client.query(migration)` (line ~273, inside the "transitions exact
  predecessors..." test) — confirmed via `CONTRACTS` array inspection that this is the ONLY one of the
  4 `client.query(migration)` call sites in the file whose test reaches `bg_vidhi_primitives` (the
  other 3 assert only on `bg_muhurta_lattice`). Local vitest run confirms the file compiles clean (no
  unused-var diagnostic) and the 3 non-DB-gated tests pass (DB-gated ones correctly skip — no local
  Postgres matching `NIRMANA_L0_WAVE0_REMAINING_TEST_DATABASE_URL`). Committed
  (`0a22f321b`) + pushed to `fix/nirmana-l0-vidhi-from-moon-view-repoint`. PR #2153 CI re-running as of
  this heartbeat (`mergeStateStatus: BLOCKED`, most checks IN_PROGRESS including Governance Gates and
  DB Integration Tests — the two just fixed). NEXT: next cycle's PR-hygiene step re-checks #2153 via
  `is:queued`; once genuinely CLEAN, queue it (`gh pr merge --auto`); once merged+deployed, verify
  migrations 705 AND 706 both applied live (direct DB check, not CI-conclusion alone) and confirm
  `from_moon_view` is correctly wired end-to-end in production. Then revert to IDLE-OK pending
  Conductor's C12 carve-out for `bg_cohort`.
- 2026-09-07 — **PR #2153's DB Integration Tests still RED after the prior cycle's fix; root-caused
  for real and fixed.** `is:queued` showed #2153 not queued, `mergeStateStatus: BLOCKED`. Pulled the
  actual failed job log (`gh api .../jobs/<id>/logs`) rather than trusting the check name alone:
  `migration 628 refuses unknown bg_vidhi_primitives registry contract`, thrown on the test's SECOND
  replay of migration 628 (line ~316) — the prior cycle's fix applied migration706 right after the
  FIRST migration628 application, which correctly satisfied the CONTRACTS loop, but migration 628's
  own guard for `bg_vidhi_primitives` hardcodes the OLD (pre-#2122) content hash, so once 706 had
  already moved that column to the corrected hash, replaying 628 a second time (testing 628's own
  idempotency + a digest-contract-mutation-rejection invariant) legitimately tripped 628's own guard.
  **Fix: reordered the test**, not the migration (628 is immutable, never edited) — moved the
  replay/digest-mutation block to run BEFORE migration706 (confirmed it only touches
  `asset_output_digest_specs`/`catalog_status`, unrelated to the vidhi content fix; confirmed none of
  the three stored `integrity_check_sql` values reference `asset_output_digest_specs`), so migration706
  now applies exactly once, immediately before the CONTRACTS loop — mirroring real production
  sequencing (628→705→706, each exactly once) instead of replaying 628 after 706. **Verified for real
  this time**, not just reasoned through: spun up a throwaway Postgres 16 via Docker locally, ran the
  actual DB-integration suite against it end-to-end — 6/6 pass, including the previously-failing test.
  Also both offline governance checks re-confirmed green. Committed `10d67f74c`, pushed. **Also caught
  and fixed a self-inflicted branch-mismatch this cycle**: made an initial editing pass on the
  `feat/nirmana-l0-heartbeat-2` branch by mistake (this file's continuity branch does not carry the
  PR's commits) before noticing the `migration706` TypeScript diagnostic couldn't resolve — reverted
  that accidental edit (`git checkout --`) before it could be committed, switched to the correct PR
  branch, redid the fix there. NEXT: next cycle's PR-hygiene step re-checks #2153 via `is:queued`
  after this push's CI completes; once genuinely CLEAN, queue it. Once merged+deployed, verify
  migrations 705 AND 706 both applied live (direct DB check) and confirm `from_moon_view` is correctly
  wired end-to-end in production. Then revert to IDLE-OK pending Conductor's C12 carve-out for
  `bg_cohort`.
- 2026-09-07 — **PR #2153 turns up a THIRD, previously-unseen RED gate; root-caused and fixed.**
  DB Integration Tests now genuinely passed (confirms the prior cycle's migration706 reorder fix
  works). But `is:queued`/status check showed a new failure: **Unit Tests** —
  `plan_bridge.test.ts`'s §N.8 pinned-baseline coverage detector
  (`getPlanBridgeCoverage`/`KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE`). Root cause: `from_moon_view`'s
  repoint to `ganita_transit_anchors_get` (#2122) is a genuinely NEW distinct `live_tool`
  (`total_distinct_live_tools` 41→42) with no resolvable mapping in the Pariprashna plan bridge yet
  — confirmed via `web_tool_bridge.generated.json` (`uri: null`, `resolution_kind: "unmapped"`, not
  a stale-generation artifact) and via `compiled_floor_adapter.ts`'s hand-curated
  `LIVE_TOOL_TO_RETRIEVAL` map (absent) — the same class of genuinely un-bridged tool as the two
  already-documented DEFERRED entries there (`ganita_structural_get`/`ganita_condition_get`).
  Followed the test's own documented remediation path exactly (its header comment prescribes this
  exact move): added `ganita_transit_anchors_get` to the pinned baseline (19→20 names), updated
  `total_distinct_live_tools` 41→42; `covered_live_tools` stays 22 (total and uncovered both grew by
  1, cancelling) — **verified via a throwaway script call to `getPlanBridgeCoverage()` directly**,
  not guessed from the failure diff (my first read of the diff direction was backwards; recomputing
  live caught it). Did NOT force-map the tool into the resolver — that's out of this PR's scope
  (Pariprashna/L1 territory), noted inline for that owner. Verified: `plan_bridge.test.ts` 20/20,
  full `src/lib/pariprashna` suite 1498/1498, 0 regressions. Committed `ab9685e77`, pushed. NEXT:
  next cycle's PR-hygiene re-checks #2153 via `is:queued`; given this is now the THIRD distinct gate
  found sequentially rather than all at once, budget for a possible fourth before assuming CLEAN —
  check the full `statusCheckRollup`, not just the previously-failing names. Once genuinely CLEAN,
  queue it. Once merged+deployed, verify migrations 705+706 applied live and `from_moon_view` wired
  end-to-end in production, then IDLE-OK pending Conductor's C12 carve-out for `bg_cohort`.
- 2026-09-07 — **IDLE-OK (verified).** #2153's CI still running against the latest fix (`ab9685e77`,
  `headRefOid` confirmed match); DB Integration Tests and the plan_bridge Unit Tests fix both no
  longer appear in the failing-checks list (fixed, as expected), nothing new RED yet, `mergeStateStatus`
  transient `UNKNOWN` (normal mid-run). Not actionable this cycle — will re-check next cycle. #1713
  tail unchanged since last check (still ends at the 09-06T18:17Z Conductor fleet post); no Conductor
  movement on the bg_cohort carve-out. Nothing else eligible.
- 2026-09-07 — **IDLE-OK (verified).** #2153 progressing well: `gh pr checks` shows DB Integration
  Tests genuinely PASS (2m24s) and every other check green except 4 still pending/in-progress
  (Governance Gates, Unit Tests, Build Check, Gate battery selftest) — nothing red. Not actionable
  this cycle. #1713 tail unchanged. Nothing else eligible.
- 2026-09-07 — **IDLE-OK (verified).** #2153: Unit Tests now also confirmed PASS (join
  DB Integration Tests). Only 2 checks left genuinely running (`Governance Gates`, `Build Check` —
  confirmed via `gh run view` job `startedAt`/`status: in_progress`, not stalled), everything else
  green or benign `skipping`. Not actionable yet. #1713 tail unchanged.
- 2026-09-07 — **IDLE-OK (verified).** Same 2 checks (`Governance Gates`, `Build Check`) still
  `in_progress`, same `startedAt` (19:11:58Z) — ~10min elapsed now, plausible not stalled given this
  pipeline's typical runtimes (Unit Tests alone took ~7min earlier this PR). #1713's only new comment
  is L5's own `mi_kula` slot claim — not L0's concern. Nothing actionable.
- 2026-09-07 — **IDLE-OK (verified).** PR hygiene: #2153 checked via `is:queued` (not queued, expected)
  and `gh pr view --json statusCheckRollup` — confirmed CI running against my latest fix commit
  (`10d67f74c`, matches `headRefOid`), not DIRTY/RED/unqueued-while-clean; nothing actionable this
  cycle, will re-check next cycle by construction. No other open L0-lane PR. Checked #1713 tail (all
  comments after my 09-06T14:37:43Z bg_cohort service-dependency carve-out flag) — no Conductor
  response yet; read Conductor's latest fleet-status post in full (cycle 586, 09-06T18:17Z) — confirms
  39 bg/L0 frozen, #2122 already logged as ruled/assigned-to-L0 (matches my PR #2153 work), no mention
  of the bg_cohort carve-out landing. No new adjudication issues found for bg_cohort/C12 via
  `gh search issues`. Nothing eligible: `bg_cohort` still the sole blocked asset, externally gated.
- 2026-09-07 — **[Hygiene] Fixed a self-inflicted heartbeat-log ordering bug spanning several prior
  entries.** Several consecutive `Edit` calls in earlier cycles matched a non-unique `old_string`
  anchor (`...IDLE-OK pending Conductor's C12 carve-out for \`bg_cohort\`.\n- 2026-09-07 —
  **IDLE-OK (verified).**`, which recurred verbatim across entries), so new content kept landing at
  an EARLIER occurrence of that pattern instead of the file's true end. Net effect: the "DB
  Integration Tests still RED... reorder fix" entry (commit `10d67f74c`) ended up displaced to the
  very end of the file, chronologically AFTER the later "THIRD RED gate" entry (`ab9685e77`) and 5
  subsequent IDLE-OK entries that actually came after it in real time. **No content was lost or
  duplicated** — confirmed via grep before touching anything — purely an ordering defect. Fixed by
  cutting that displaced entry and reinserting it in its correct chronological slot (right after the
  "came back RED on 2 gates" / `0a22f321b` entry, right before the "THIRD RED gate" entry — exactly
  where its own internal cross-references already implied it belonged). Verified: diff is a pure
  27-line move (27 insertions, 27 deletions, net zero), single occurrence of the entry's title
  string post-fix. Going forward: appending new heartbeat entries will anchor on the LAST occurrence
  of any repeated phrase, or read the file's tail fresh each time, to prevent recurrence. #2153
  status this cycle: `Governance Gates` now also confirmed PASS; only `Build Check (PR only)` still
  running (~12.5min elapsed, `mergeStateStatus` transitioned to `UNSTABLE` — still-pending, no
  failures). #1713's only new activity is L5's own `mi_kula` SLOT RELEASE (unrelated). Not
  actionable yet.
- 2026-09-07 — **PR #2153 CLEAN — queued.** All required checks COMPLETED (remainder benign
  `SKIPPED`), `mergeStateStatus: CLEAN`, `mergeable: MERGEABLE`. This was the exact "CLEAN-but-
  unqueued" case from C8 v2.3 Step 1: `gh pr merge 2153 --auto` (queued on the second call after a
  `--squash` flag was rejected — "merge strategy for main is set by the merge queue"). **Verified via
  `is:queued`** (not `autoMergeRequest` — per the standing lesson), confirms #2153 genuinely in the
  queue now. This closes out the multi-cycle RED-fix arc: 3 sequentially-discovered gates
  (Governance Gates writer-inventory re-pin, DB Integration Tests migration-ordering, plan_bridge
  pinned-baseline) all fixed and verified for real (Docker-verified DB tests, direct
  `getPlanBridgeCoverage()` computation, offline governance checks) — none weakened. #1713: only new
  activity is L5's own `mi_kula` W4 dispatch success, unrelated to L0. NEXT: next cycle's PR-hygiene
  step re-verifies #2153 via `is:queued` until it actually merges; once merged+deployed, verify
  migrations 705 AND 706 both applied live (direct DB check, not CI-conclusion alone) and confirm
  `from_moon_view` is correctly wired end-to-end in production. Then IDLE-OK pending Conductor's C12
  carve-out for `bg_cohort`.
- 2026-09-07 — **IDLE-OK (verified).** #2153 still `is:queued` (confirmed), `mergedAt: null` — not
  merged yet. **Noted, no action:** L3 filed `#2159` (TIME-CRITICAL → CONDUCTOR) — `deploy.yml`'s
  `migrate` job checked out a STALE commit for one deploy (a `workflow_run.head_sha` race under fast
  merges), silently skipping migration 850 while the deploy reported success; `deploy-web` already
  self-checks `ACTUAL_SHA` vs `DEPLOY_SHA`, `migrate` doesn't. This is shared CI infra (L3 correctly
  scoped it to Conductor, not unilateral) — **directly validates** why my own NEXT step already reads
  "verify migrations 705+706 applied live via direct DB check, not CI-conclusion alone" rather than
  trusting the deploy job's green checkmark. No action needed from L0 now; will factor this into the
  post-merge verification once #2153 actually merges. Nothing else eligible.
- 2026-09-07 — **IDLE-OK (verified).** #2153 still `is:queued`, `mergedAt: null` — not merged yet, but
  the queue is actively moving (`git log origin/main` shows steady merges from other lanes just this
  past stretch, e.g. #2158/#2157/#2149/#2155). Not stalled, just hasn't reached #2153. #1713 tail
  unchanged. Nothing else eligible.
- 2026-09-07 — **IDLE-OK (verified).** #2153 still `is:queued`, not merged. `main` hasn't advanced
  since last check, but confirmed not stalled: Conductor's `#2161` (DEPLOY_SHA provenance guard fix
  for #2159, also queued) has CI genuinely `IN_PROGRESS` right now — the queue is processing its
  order normally, just hasn't reached #2153 yet. #1713 tail unchanged. Nothing else eligible.
- 2026-09-07 — **PR #2153 MERGED (`c39345c7b`, confirmed on `main`). Production-rollout verification
  found a real, NEW gap — investigated to root cause and remediated.** Migrations 705+706 confirmed
  applied live via direct `psql` query against production (`_migrations_applied` rows present, exact
  timestamps 19:52:17/18Z; `vidhi_primitives.from_moon_view` row content correct;
  `asset_registry.integrity_check_sql` for `bg_vidhi_primitives` evaluates literally TRUE when
  executed against live data). **But** the serving code itself was stale: `amjis-mcp`'s live Cloud
  Run revision ran image `70dbe58b7cb7f54083dbef22adfef395ca62eeac`, confirmed via
  `git merge-base --is-ancestor` to PREDATE my merge — despite PR CI green, the merge landing, and
  multiple subsequent "Deploy to Cloud Run" workflow runs reporting `success`. Root-caused via the
  actual job log (not assumed): `deploy.yml`'s "Gate & detect changed paths" step computes
  `git diff --name-only HEAD~1 HEAD` (a SINGLE commit's diff) to decide whether to rebuild
  sidecar/MCP/pipeline-job — under the fast-merge queue, a deploy run firing for a LATER commit whose
  own single-commit diff doesn't touch `platform-mcp/` silently never rebuilds it, even though MY
  commit (2 merges earlier) genuinely did. **Distinct root cause from `#2159`/`#2161`** (that's the
  `migrate` job's `DEPLOY_SHA`/`workflow_run.head_sha` checkout race; this is the `changes` gate's
  diff-base window) — filed as its own adjudication, **`#2169`**, rather than assumed-covered by
  #2161. Did NOT patch `deploy.yml` myself (shared infra, same precedent as `#1960`/`#2159`) —
  instead closed MY OWN instance of the gap using the workflow's EXISTING, documented
  `workflow_dispatch` escape hatch (`force_all_services: true`, `ci_gate: require-ci-green` — the
  safe default since main's CI already passed): run `34059983414`, dispatched, in progress as of this
  heartbeat. Posted the finding + action to `#1713`. NEXT: verify run `34059983414` completes
  successfully; once it does, re-check `amjis-mcp`'s live image SHA is now a descendant of `c39345c7b`
  (or later) and re-confirm `from_moon_view`'s SERVED behavior (not just the DB row) is correct —
  e.g. via a live MCP tool call exercising the primitive, not just the migration/DB check. Only then
  is "from_moon_view correctly wired end-to-end in production" genuinely closed. Then IDLE-OK pending
  Conductor's C12 carve-out for `bg_cohort` (and #2169's ruling, if any, though that's Conductor's
  clock not L0's blocker).
- 2026-09-07 — **IDLE-OK (verified).** Force-deploy run `34059983414` progressing (`Build & Deploy
  MCP` now genuinely `in_progress`, `Apply DB Migrations` completed `success`), not done yet. **Cross-
  checked L1's own #2122 "verified closed live" claim (PR #2171)** — confirmed via their diff that
  they checked `origin/main`'s source + the live `vidhi_primitives` DB row, but NOT the deployed
  serving code's freshness — i.e. the exact gap `#2169` covers, unaddressed by their check. Not L1's
  lane to fix or mine to correct in their file; noted here as independent confirmation my own
  deeper verification (deployed image SHA, eventually a live tool call) is the one that actually
  closes this. #1713's only new item is my own prior post. Nothing else actionable.
- 2026-09-07 — **Force-deploy `34059983414` COMPLETED. #2122/PR #2153 production rollout fully
  closed, end-to-end, live-verified — not stopping at "the deploy succeeded."** Confirmed directly:
  (1) `amjis-mcp`'s live image is now `6964b5538...`, confirmed via `git merge-base --is-ancestor
  c39345c7b 6964b5538...` that my merge is genuinely an ancestor — the earlier staleness (image
  `70dbe58b...`, predating my merge) is resolved. (2) 100% traffic on the new revision
  (`amjis-mcp-00620-2hp`). (3) **Called the actual live tool** (`ganita_transit_anchors_get`,
  canonical chart `482012f1-710e-4a25-994a-93821f5871aa`, `graha=moon`) — returns
  `natal_house_from_moon` per ayanamsha, exactly the "bhāva reckoned from Moon" semantic
  `from_moon_view` exists to provide. Not merely "a valid tool now resolves" — the served content is
  genuinely the right content, verified against the canonical native's chart. This closes every
  layer: writer code → live DB row → deployed serving code → actual served output. Posted final
  confirmation to `#1713`. **`#2169` (the systemic deploy-pipeline changed-paths gap) stays OPEN** —
  my manual force-deploy closed only THIS instance; the underlying gap for future PRs remains
  Conductor's call, not something I've fixed by working around it once. **This closes the entire
  #2122 arc** (discovery → root-cause → fix → 3 sequentially-found RED gates → merge → deploy-gap
  discovery → remediation → full live verification) across many cycles. L0 is back to **39/40
  frozen, `bg_cohort` the sole remaining blocker**, held on Conductor's C12 carve-out — no other
  eligible work. NEXT: revert to standard IDLE-OK cycles, watching #1713 for (a) Conductor's C12
  carve-out ruling on `bg_cohort`, (b) any ruling on `#2169`, (c) new discoveries of #2122's class
  surfacing from other lanes' work.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PR (`is:queued` and author search both confirm).
  `bg_cohort`'s carve-out still unimplemented — checked `git log` on
  `platform/src/lib/nirmana-elevation/definitions.ts` (the file governing
  `requireAcceptedRebuildProvenance`), no commits since well before D-L0-II was even discovered.
  `#2169` has no comments yet (freshly filed, expected). #1713 tail unchanged since my own closing
  posts. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PR. #1713 tail still ends at my own closing posts;
  `#2169` still 0 comments. Nothing new, nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change: no open L0 PR, `bg_cohort` carve-out file
  untouched, #1713/#2169 quiet. Entering another extended-idle stretch (same shape as the prior
  60+-cycle streak) — will keep verifying each cycle rather than assume, per contract.
- 2026-09-07 — **`#2169` RULED (Conductor) and FIXED — PR #2172, auto-merge armed.** Confirmed my
  root-cause diagnosis correct and distinct from #2159/#2161; fixed by diffing from the last
  successful deploy's `head_sha` (fetched on demand for the shallow checkout) instead of `HEAD~1`,
  falling back byte-identically on lookup failure. Conductor's own independent review caught and
  fixed a real bug in the first draft (the success-run filter also matched PR-triggered build-check-
  only runs) before shipping. Also confirmed my manual `workflow_dispatch` redeploy was "the right
  call — the intended escape hatch, not a workaround." Nothing for L0 to action — #2172 is
  Conductor's PR, not mine to manage. `bg_cohort`'s own C12 carve-out still unmoved. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. No open L0 PR, #1713 tail
  unchanged, `bg_cohort` carve-out file untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced (L3/L5 state PRs, unrelated). #1713's only new
  comment is L5's own `mi_kula` slot claim. `bg_cohort` carve-out still untouched. Conductor's fix PR
  `#2172` still open (`mergeStateStatus: UNKNOWN`, not L0's to manage). Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** #1713's only new activity is L5's own `mi_kula` slot
  release. `bg_cohort` carve-out still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified, broader check).** #1713's only new activity is L5's own `mi_kula`
  freeze milestone. `bg_cohort` carve-out file still untouched; `#2169` still just Conductor's one
  ruling comment (PR #2172); direct `gh search issues "bg_cohort"` finds no dedicated new issue.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** Conductor's fleet-status post (cycle 635) confirms `#2169`
  fully FIXED (PR #2172) alongside `#2159` -- both TIME-CRITICAL deploy-pipeline gaps this session
  helped surface now closed. No mention of the `bg_cohort` C12 service-dependency carve-out.
  45/128 frozen (39 bg/L0, unchanged for L0 specifically). Nothing eligible for L0.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced further (#2172 Conductor's #2169 fix merged,
  plus L1/L3/L4/L5 own state PRs -- all unrelated to L0). #1713 tail unchanged, `bg_cohort` carve-out
  file still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced with an unrelated L5 state PR (#2177). #1713
  tail unchanged, `bg_cohort` carve-out file still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced with an unrelated L1 W3 close-report PR
  (#2179). #1713 tail unchanged, `bg_cohort` carve-out file still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced with an unrelated L3 heartbeat PR (#2181).
  #1713 tail unchanged, `bg_cohort` carve-out file still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced with L1's `depends_on` DAG audit (#2183) and an
  unrelated L5 state PR (#2182) -- checked #2183's scope specifically since it touches `depends_on`
  (bg_cohort's blocker is also depends_on-adjacent), but it's about hidden/false DAG edges within
  L1's own asset graph, not the orchestrator's service-dependency semantics (D-L0-II) -- unrelated.
  #1713 tail unchanged, carve-out file still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced several cycles (L1/L3/L5 own state PRs +
  L3-W3 volume-formula work, #2181-#2187) -- all unrelated to L0. #1713 tail unchanged, `bg_cohort`
  carve-out file still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
