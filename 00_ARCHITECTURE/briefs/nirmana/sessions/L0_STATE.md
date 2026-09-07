---
artifact: L0_STATE.md
canonical_id: NIRMANA_V21_L0_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L0
layer: L0 — Brahmagyan
owner: the L0 session (this file is yours alone — charter C5)
last_updated: 2026-09-07 — **L0 IS 40/40 FROZEN.** `bg_cohort`, the last holdout (blocked on the C12
  service-dependency provenance wall / D-L0-II), froze end-to-end this session: Conductor ruled #2240
  resolved-by-existing-fix (PR #1851, stale local worktree was the real cause) → fresh worktree
  re-dispatch cleared both guards → fresh Cloud SQL backup → committed dispatch → discovered/fixed a
  `build_run_authorized` race-window gap → `accepted_rebuild_observed` accepted on a genuine
  `receipt_state=proven` build → a separate verifier subagent (D-CND-35) submitted `integrity_verified`
  + `asset_frozen`. Independently re-verified myself via direct DB query (not just trusting the
  subagent): `bg_cohort`'s full 5-event chain is real, `count(DISTINCT entity_id) WHERE layer='L0' AND
  event_type='asset_frozen'` = 40. Posted the milestone to #1713. **What remains open, NOT L0's own
  lane**: the campaign-wide W6 stage-transition-acceptance ceremony (#1945) has its own unrelated
  blockers (invalidated-analysis backlog, deploy lag) — that's Conductor/cross-layer scoped, not
  something to force from here. L0's own asset-freeze work is done.
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

**40/40 FROZEN — L0 IS COMPLETE.** bg_gochara_arcs, bg_dasha_systems, bg_doshas, bg_vidhi_floors,
bg_parihara_rules, bg_compendium_index, bg_rules, bg_text_index, bg_concordance, bg_yogas all froze
across the sessions between the last detailed heartbeat entry below and 2026-09-06/07 (see heartbeat
log for the bg_yogas/D-NATIVE-06 account — the fullest-documented one; the others' individual
W1→freeze accounts were not re-transcribed into this file session-by-session and are recoverable
from their PRs/issue #1713 history if ever needed). **`bg_cohort` — the last holdout, blocked on
Conductor's C12 carve-out — froze 2026-09-07** once PR #2234 (D-NATIVE-07) shipped, deployed, and
was correctly re-dispatched (full account in the heartbeat log below: the stale-worktree trap, the
build_run_authorized race-window gap, the separate verifier subagent's integrity_verified+asset_frozen
submission). Independently re-verified by me (not just trusting the subagent's narrative): live query
confirms `bg_cohort`'s full 5-event chain and `count(DISTINCT entity_id) WHERE layer='L0' AND
event_type='asset_frozen'` = **40**. **What's NOT yet closed**: L0's formal W6 layer-freeze *ceremony*
is a separate, campaign-wide `stage_transition_accepted` mechanism (issue #1945, Conductor/cross-layer
scoped — "zero stage-spine receipts exist, W6 will be rejected") with its own open blockers (22
invalidated analyses backlog, ordinary deploy lag) unrelated to L0's own asset count. That is not
L0's own lane to fix unilaterally; posted the 40/40 milestone to #1713 for Conductor visibility.
Separately, **issue #2122** (F-D21/F-D23: `bg_vidhi_primitives`'
`from_moon_view` Vidhi primitive pointed at an inert `reference_point` arg on
`ganita_chart_facts_get`) surfaced via a Conductor fleet-status post on #1713 — this is NEW L0 work,
independent of the freeze-tracking count above (it does not un-freeze `bg_vidhi_primitives`; it
corrects a served primitive's routing). Fixed and shipped as **PR #2153, merged, force-deployed, and
live-verified end-to-end — the arc is CLOSED** (see heartbeat for the full account, including the
deploy-pipeline gap it surfaced, filed as `#2169`, still open at the systemic level).

## The 1 unfrozen asset — RESOLVED 2026-09-07

| asset | route | status / blocker |
|---|---|---|
| ~~bg_cohort~~ | rebuild_only | **FROZEN 2026-09-07.** Was held on Conductor's C12 carve-out (dep on `bg_ephemeris_engine` service semantics) — PR #2234 shipped+deployed, re-dispatched successfully, full evidence chain complete. L0 is now 40/40. |

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
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced with an unrelated L5 state PR (#2188). #1713
  tail unchanged, `bg_cohort` carve-out file still untouched. Nothing eligible.
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
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced several more cycles (L1/L3/L5 own state PRs +
  L3-W3 volume-formula batches, #2185-#2196) -- all unrelated to L0. #1713 tail unchanged, `bg_cohort`
  carve-out file still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** #1713's only new activity is L1's own `ga_positions` slot
  claim (5-wave rebuild coordination, unrelated to L0). `bg_cohort` carve-out file still untouched.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** `main` advanced with an unrelated L1 W3 PR (#2193). #1713
  tail unchanged, `bg_cohort` carve-out file still untouched. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** #1713's only new activity is L1's own `ga_positions` slot
  release (wave 0 of a coordinated rebuild, unrelated to L0). `bg_cohort` carve-out file still
  untouched. Nothing eligible.
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
- 2026-09-07 — **IDLE-OK (verified).** Conductor's fleet-status post (cycle 724) confirms 39 bg/L0
  frozen (unchanged) — `bg_cohort` still not among them, no mention of the C12 service-dependency
  carve-out being addressed. 6 adjudications closed this stretch, none L0-relevant. `bg_cohort`
  carve-out file still untouched. Nothing eligible.
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
- 2026-09-07 — **IDLE-OK (verified).** #1713's only new activity is Conductor flagging L2's
  liveness (stalled/dead session concern), unrelated to L0. `bg_cohort` carve-out file still
  untouched. Nothing eligible.
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
- 2026-09-07 — **Conductor broadcast (#2224/#1945): re-verify accepted-analysis freshness before any
  wave-1 dispatch — measured 22/70 accepted analyses invalidated campaign-wide by ordinary W3 work
  landing after acceptance, spanning `bg_*`/`ga_*`/`ka_*`. Acted on it for L0's own case, not just
  noted.** `bg_cohort` is L0's only asset with standing W2 evidence not yet consumed by a freeze
  (`asset_analysis_accepted`/`optimization_verdict_accepted`, both 2026-09-04T19:09:55Z,
  `registry_fingerprint_sha256 = dbfd673c...`). Recomputed the live registry fingerprint using the
  exact recipe Conductor named (`dispatch_nirmana_campaign_wave.py`'s `_live_registry_fingerprint` /
  `_live_registry_contract` — asset_id + layer + sorted depends_on + the 14
  `REGISTRY_CONTRACT_FIELDS`, stable-JSON sha256) against `bg_cohort`'s current live `asset_registry`
  row, fetched fresh via direct `psql` (not assumed unchanged) and replicated byte-for-byte in Python
  (not hand-derived) — **live fingerprint MATCHES the stored `dbfd673c...` exactly.** bg_cohort's W2
  evidence is NOT stale; no re-stamp needed. Confirms bg_cohort remains genuinely dispatch-ready the
  moment Conductor's C12 service-dependency carve-out lands — nothing else blocking it. Nothing
  eligible to act on beyond this verification; `bg_cohort` carve-out file itself still untouched.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle (only new #1713 comment is my own
  prior post). Nothing eligible.
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
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle (one transient network error on
  first `gh` call, succeeded on retry). Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. Nothing eligible.
- 2026-09-07 — **THE C12 CARVE-OUT HAS LANDED — PR #2234, native-authorized D-NATIVE-07, already
  `is:queued` and healthy.** Not my PR to manage (Conductor's, under the shared bot identity — not
  something for L0 to touch), but directly unblocks `bg_cohort`, L0's last unfrozen asset. Root cause
  exactly matches this file's own D-L0-II finding from 09-05/09-06: `bg_cohort` built correctly
  (10,000 rows) but `compute_upstream_hash` required its sole dependency's (`bg_ephemeris_engine`,
  service-kind) OWN receipt to be `proven` — impossible for a service with no relational output to
  spec. Fix (`asset_runner.py`'s `load_upstream_receipts`/`compute_upstream_hash`): accept a
  dependency whose receipt isn't proven ONLY when live `asset_kind='service'` AND
  `service_health='healthy'` (checked fresh, never trusted from a stale receipt). **Verified both
  sides myself, live, before assuming anything**: `bg_ephemeris_engine.service_health = 'healthy'`
  (confirmed via direct `psql`) and `bg_cohort`'s `asset_provenance_receipts` row still shows exactly
  the described stuck state (`receipt_state='unknown'`, `unknown_reasons=['upstream_digest_unavailable']`,
  real `output_digest` already present — genuinely built, just stuck on provenance). Nothing
  surprising awaits. NEXT: watch #2234 merge + deploy (not mine to rush), then re-dispatch
  `bg_cohort` under the normal identity-separated path (executor SA build/authorize, verifier SA
  `integrity_verified`/`asset_frozen`) — the PR's own test plan hands this off to L0 explicitly. This
  is now THE highest-priority eligible work the instant the fix is live. `bg_cohort`'s own W2
  evidence already independently reverified fresh (prior cycle) — no re-stamp needed at dispatch time.
- 2026-09-07 — **IDLE-OK (verified).** PR #2234 (D-NATIVE-07) still `is:queued`, not yet merged.
  `main` advanced with an unrelated L5 state PR (#2232). #1713 tail unchanged. Watching for the merge.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. PR #2234 still `is:queued`.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No change since last cycle. PR #2234 still `is:queued`.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** PR #2234 still `is:queued`, but confirmed ALL its own checks
  are genuinely green (`gh pr checks` — 20+ passing, rest benign `skipping`, nothing red/pending) —
  it's just waiting its turn in the shared queue, not stalled. Not mine to rush (Conductor's PR).
  Nothing eligible.
- 2026-09-07 — **PR #2234 (D-NATIVE-07) CONFIRMED MERGED — but a stale `gh pr view` call initially
  said otherwise; caught it via direct GraphQL, not trusted blindly.** `gh pr view 2234` reported
  `mergedAt: null, state: OPEN` across several cycles; a direct `gh api graphql` query against the
  PR's own `mergeQueueEntry`/`state` fields revealed `state: MERGED` — confirmed via a second,
  independent `gh pr view` call afterward (`mergedAt: 2026-09-07T05:41:20Z`, merge commit
  `fd64055ee...`), and via `git merge-base --is-ancestor` against `origin/main`. **Exactly the
  "is:queued is the only truth, don't trust a single stale read" discipline, one layer deeper — even
  a direct PR-state read can be stale; cross-check with a second, independent method before acting.**
  Then checked the ACTUAL deployed pipeline-job image directly (`gcloud run jobs describe
  brahma-build-pipeline-job`) rather than assuming merged=deployed: the live image
  (`7f87adc13d6...`) does NOT include the fix — confirmed via `git merge-base --is-ancestor` returning
  false. **Did not dispatch `bg_cohort` against stale code** (would have hit the exact same wall
  again, wasting a real production dispatch). Instead used the same safe, intended
  `workflow_dispatch` escape hatch as the earlier #2153 deploy-gap (`force_all_services: true`,
  `ci_gate: require-ci-green` — CI already passed on this exact commit as part of the PR itself): run
  `34087944016`, targeting `46f7b7257` (current main tip, confirmed to include `fd64055ee` as an
  ancestor), dispatched and spinning up as of this heartbeat. NEXT: verify this deploy completes and
  the pipeline-job image genuinely updates (direct `gcloud` check, not the workflow's own conclusion
  alone); only THEN re-dispatch `bg_cohort` under the normal executor/verifier-SA identity-separated
  path to take L0 to 40/40 — the exact handoff #2234's own test plan names.
- 2026-09-07 — **IDLE-OK (verified).** Force-deploy `34087944016` progressing (`Build & Deploy
  Pipeline Job Image` genuinely `in_progress` — the job that matters for `bg_cohort`), not done yet.
  #1713's only new activity is my own prior post. Nothing else eligible.
- 2026-09-07 — **IDLE-OK (verified).** Force-deploy `34087944016` still `in_progress`, no change.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** Force-deploy progressing: Sidecar + DB Migrations done,
  `Build & Deploy Pipeline Job Image` (the one that matters) still `in_progress`. Nothing eligible.
- 2026-09-07 — **Force-deploy `34087944016` CONFIRMED COMPLETE and its image CONFIRMED live** — fresh
  `gcloud run jobs describe brahma-build-pipeline-job` read shows image tag `46f7b7257e...`, and
  `git merge-base --is-ancestor fd64055ee 46f7b7257e` = true: the deployed pipeline-job genuinely
  includes #2234's fix. Attempted re-dispatch: `dispatch_nirmana_campaign_wave.py --layer L0 --wave 1
  --assets bg_cohort --definition-revision t0-2026-09-01-0e5b06fb --reviewed-deployment-sha
  46f7b7257e...` (today's deploy SHA) — **failed again** with "accepted asset analysis does not match
  the current live registry contract for bg_cohort", even though the registry fingerprint itself was
  independently re-verified to match exactly (twice now). **Root-caused by reading
  `validate_wave_evidence_bindings` in full**: `--reviewed-deployment-sha` isn't "today's deployed
  commit" — it's the exact commit bg_cohort's *existing accepted evidence* already cites in its
  `source_ref`. I had the semantics backwards. Independently recomputed bg_cohort's canonical
  `analysis_digest` from scratch (replicating `_canonical_analysis_digest` exactly: writer_digest from
  `nirmana-writer-digests.json` + live registry contract + the separately-pinned
  `nirmana-analysis-layer-pins.json` L0 convergence_commit `49bb5c98b8...`) — it matched the stored
  evidence's digest (`8682fa43...`) byte-for-byte, proving the analysis is genuinely unchanged; nothing
  to re-stamp. (Tried resubmitting fresh evidence bound to today's SHA anyway first, via the
  reconstructed `l0_submit_evidence.sh` OIDC executor-SA route — got a clean 409 "conflicting lifecycle
  receipt already exists for this registry/analysis generation," confirming receipts key on
  (fingerprint, digest), not source_ref.) Re-ran with the *correct*, pre-existing
  `--reviewed-deployment-sha 4f7a9cc872714c74111ca8ae38ad4257c462cd3e` — **the evidence-binding wall
  cleared entirely.** New wall immediately behind it: `"a run already exists for this frozen campaign
  wave; duplicate execution refused"`. Queried `build_runs` directly: `a9446885-2a21-49ae-baac-
  d3b7cc1f317b`, `state='completed'`, created 2026-09-05 17:44:37 UTC — **before** #2234 was even
  merged. This is the exact run whose receipt is stuck at `receipt_state=unknown`
  (`unknown_reasons=["upstream_digest_unavailable"]`, real `output_digest` already present — the
  writer itself succeeded, only the service-dependency receipt bookkeeping choked on the now-fixed
  bug). The dedup guard blocks re-dispatch unconditionally on `triggered_by`, regardless of the old
  run's state, and the fix lives in `asset_runner.py`'s live receipt-computation path — it cannot
  retroactively repair a receipt already persisted from the old buggy run. No CLI override, no
  separate receipt-recompute tool found. **Not mine to bypass unilaterally** (adjacent to the FROZEN
  orchestrator contract's dispatch invariants, and may not be unique to bg_cohort — any asset whose
  build completed while receipt computation was broken by a now-fixed bug would hit the same wall).
  Filed **#2240** (both findings: the `--reviewed-deployment-sha` semantics correction, flagged for
  other layers too per #2224's cross-layer concern; and the build_runs dedup-vs-stuck-receipt
  blocker, asking for a sanctioned path forward). D-L0-II's underlying wall is now provably fixed and
  deployed — what remains is purely this dispatch-mechanics gap. NEXT: await #2240's ruling.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs (last work was a direct push to this heartbeat
  branch, nothing queued). Posted #2240's findings to #1713 for Conductor visibility. #2240 itself has
  no comments yet (filed last cycle). Checked #1713's tail before posting — no new Conductor activity
  since the force-deploy announcement. Nothing else eligible: `bg_cohort` is L0's only gap and it's
  correctly blocked pending #2240's ruling — not mine to force past the dedup guard. Idle-waiting.
- 2026-09-07 — **#2240 RULED (Conductor): resolved-by-existing-fix, PR #1851, not a new dedup-guard
  change.** My own diagnosis was right about the mechanism but wrong about the state: the guard I
  hit was already narrowed to `state = ANY(['planned','running','paused'])` on `origin/main` — my
  session's own long-lived worktree/branch had a stale copy of `dispatch_nirmana_campaign_wave.py`
  (the exact "shared-file fix predates your branch's tree" trap this session has hit and documented
  before, e.g. #1852). Diffed local vs `origin/main` directly to confirm — Conductor's ruling was
  exactly right. **Fix: ran everything from a fresh `git worktree add --detach ... origin/main`
  instead of trusting this branch's own tree for shared scripts.**
  - Re-ran the dry-run from the fresh worktree: both guards (evidence-binding, dedup) cleared. Took a
    fresh, verified Cloud SQL on-demand backup (`1788762136231`) before committing (bg_cohort's own
    `bg_synthetic_cohort_md` is a same-asset CASCADE child, 100k rows, self-contained per D-L0-I —
    prudent, not cross-layer).
  - First real `--commit` attempt failed with "runner manifest no longer matches the reviewed
    dry-run preview" — root cause: `--snapshot-ref` is folded into the manifest digest, so the
    dry-run used to generate `--expected-manifest-digest` must pass the SAME `--snapshot-ref` as the
    commit, not omit it. Fixed, re-ran, committed successfully (`d35590e5-...`, execution
    `brahma-build-pipeline-job-vkdgk`).
  - Cloud Run execution succeeded; `asset_provenance_receipts` for this new build_id came back
    `receipt_state='proven'`, `unknown_reasons=[]`, real `output_digest` — **first structural proof
    the C12/#2234 fix genuinely works**, not just theoretically. (A first attempt at this, run
    `09d48143-...`, also proved the fix works at the receipt level but its evidence chain turned out
    to be dead — see next bullet — so it doesn't count toward the freeze chain, only as fix
    confirmation.)
  - Attempted `accepted_rebuild_observed` for `09d48143-...` and discovered a THIRD, previously
    undocumented gap: `requireAcceptedRebuildProvenance` (`definitions.ts`) requires a
    `build_run_authorized` event recorded (by the executor identity, `source_kind=
    campaign_authorization`) strictly BEFORE `build_runs.started_at` — and
    `dispatch_nirmana_campaign_wave.py --commit` triggers the Cloud Run execution immediately with
    no pause, so authorization can only ever be submitted in the few-second race window between
    commit returning and the orchestrator's own container picking up the job and stamping
    `started_at`. Confirmed the pattern against `bg_yogas`'s own already-frozen chain (authorization
    recorded ~12s before its `started_at` — this is how the other 39 assets actually did it, I just
    hadn't hit it before since D-L0-II blocked bg_cohort at an earlier stage every previous cycle).
    `09d48143-...`'s `started_at` was already years^H^H^Hminutes in the past with no authorization on
    record — that specific run's evidence chain is permanently dead (the data itself was fine, real
    proven receipt, just uncertifiable now). **Re-dispatched a second time** (`d35590e5-...`,
    superseding it under the same triggered_by key — the completed/dead prior run doesn't block a
    new one, per #2240's ruling), this time firing `build_run_authorized` immediately after capturing
    the commit's `run_id` (recorded 06:32:33, `started_at` 06:32:43 — a ~9.4s window, held). Computed
    `authorization_sha256` as a deterministic sha256 of `{campaign_id, definition_revision, layer,
    wave_index, asset_ids}` (only checked for format + cross-event equality, not a canonical formula
    match, per `requireBuildRunAuthorizationProvenance`'s actual validation code — read in full before
    computing anything, not assumed). `build_run_authorized` accepted (HTTP 201).
  - Computed `decision_digest` as `sha256(stableJson(bg_cohort's exact stored optimization_verdict_
    accepted payload))`, matching `canonicalNirmanaOptimizationVerdictDigest`'s exact formula read
    from `definitions.ts` — verified byte-for-byte against a hand-typed AND a fresh-DB-fetched copy
    of the payload (both produced the identical hash, ruling out transcription error). Submitted
    `accepted_rebuild_observed` for `d35590e5-...` with this run's real `output_digest`/
    `output_digest_spec_sha256` from its own fresh receipt — **ACCEPTED (HTTP 201).**
  - **D-L0-II is now fully, provably closed for `bg_cohort`: the service-dependency provenance wall
    that blocked this asset since it was first attempted no longer exists, confirmed via a real
    accepted rebuild receipt, not a theoretical read of the fix.**
  - Dispatched a genuinely separate verifier subagent (D-CND-35: verifier-role submissions must never
    be the same identity/session as the executor) to independently re-derive `bg_cohort`'s integrity
    check result and the `lifecycle_digest` reconstruction, and submit `integrity_verified` +
    `asset_frozen` under the verifier SA. Awaiting its report — not fabricating a result before it
    lands. NEXT: confirm its work, log the final freeze, post the 40/40 milestone to #1713.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. #1713/#2240 unchanged since last cycle —
  nothing new to react to. Verifier subagent (integrity_verified + asset_frozen for `bg_cohort`)
  still running, not done yet — not polling its transcript or predicting its result, per this
  session's own no-race discipline; will confirm and log for real once its completion notification
  lands. Nothing else eligible this cycle.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. #1713/#2240 unchanged. Verifier subagent
  still running (~5min in — reading validator code, live-checking bg_cohort's integrity_check_sql,
  and minting/submitting two evidence events is genuinely multi-step work, not stuck). Nothing else
  eligible.
- 2026-09-07 — **VERIFIER SUBAGENT REPORTED: `integrity_verified` + `asset_frozen` both ACCEPTED
  (HTTP 201). L0 IS 40/40 FROZEN.** Did not just trust the narrative — independently re-verified via
  a fresh, direct DB query of my own: `bg_cohort`'s chain now reads `asset_analysis_accepted` →
  `optimization_verdict_accepted` → `accepted_rebuild_observed` → `integrity_verified` →
  `asset_frozen`, all 5 events present and correctly ordered, and
  `count(DISTINCT entity_id) FROM ... WHERE layer='L0' AND event_type='asset_frozen'` = **40**. The
  subagent's own account (worth keeping for audit trail): it ran `bg_cohort`'s `integrity_check_sql`
  live itself first (returned true) before submitting anything; the server independently re-ran the
  same detector server-side at request time and overwrote the submitted `detector_observation`/
  `result_digest` with its own live recomputation (`detector_sql_sha256:
  e4884b03cf06ed96f8e7129702294c29a0cc6ccaf0f9db3f4cd03ff571543280`) — meaning the integrity claim is
  a real, server-verified detector result, not a self-reported one (§N.8 discipline satisfied).
  `lifecycle_digest` was computed as sha256(stableJson(the 4 prior accepted events' canonical
  fields)), matching `requireFreezeProvenance`'s exact reconstruction (validated by the 201 itself).
  Also ran `capsule_audit.sql` (pulled read-only from `origin/main`, not present on this branch) against
  the live DB: §1 (incomplete chains) = 0 rows; §2 (identity-crossing) = all rows `ok`, zero crossings
  — `asset_frozen`/`integrity_verified` correctly written by the verifier identity, everything else by
  the executor identity, exactly as D-CND-35 requires; §3 = `L0 | 40 | 40 | 0 | 0 | 100.0`. **D-L0-II is
  closed. bg_cohort is frozen. L0's own asset-level work is complete.**
  - **Posted the 40/40 milestone to #1713** for Conductor/campaign visibility.
  - **Checked #1945** (open, Conductor/cross-layer scoped: "zero stage-spine receipts exist — L0's W6
    freeze ceremony will be rejected") before claiming anything more than the asset count: this is a
    SEPARATE, campaign-wide `stage_transition_accepted` mechanism with its own open blockers (a
    22-event invalidated-analysis backlog, and an ordinary ~2-commit deploy-lag gap) — not an L0-only
    concern, not something to force from this session. L0's 40/40 asset freeze and the campaign's W6
    ceremony are two different things; only the former is done. Not overclaiming the latter.
  - **What's actually left for this session going forward**: monitor #1945/W6 for when it's ready
    (not L0's to drive), keep doing PR hygiene + heartbeat cycles, and pick up any new L0-scoped work
    that surfaces (registry drift, new adjudications, etc.) — L0 has no more of its own 40 assets to
    process.
- 2026-09-07 — **IDLE-OK (verified), first cycle of the post-40/40 era.** No open L0 PRs. Ran
  `egate.sql -v layer=L0` directly against the live DB as the ground-truth check (not just trusting
  yesterday's count): **0 rows** — confirms zero unfrozen L0 assets remain, nothing pending. Checked
  the full `nirmana-adjudication` open-issue list: nothing new targets L0 specifically (#1945 is
  still open but is the campaign-wide W6 mechanism, Conductor/cross-layer scoped, not L0's to act on;
  #2224 is L1's cross-layer flag, already cross-referenced). #1713's tail is still my own 40/40 post,
  no new activity since. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0` re-run fresh: still 0
  rows. Adjudication list and #1713 tail both unchanged since last cycle. Nothing eligible.
- 2026-09-07 — **Proactive hygiene sweep: full L0 registry-fingerprint drift check across all 40
  frozen assets (the #2224/#1945 "invalidated analysis" mechanism, applied to L0's own layer before
  it bites a future rebuild).** For each of the 40, recomputed the live `registry_fingerprint_sha256`
  and compared against the stored accepted-analysis fingerprint. First pass found 6 "drifted"
  (`bg_dasha_systems`, `bg_doshas`, `bg_gochara_arcs`, `bg_parihara_rules`, `bg_vidhi_primitives`,
  `bg_yogas`) and attempted to re-stamp all 6 — **all 12 submissions correctly bounced (409s), which
  surfaced a real bug in my OWN analysis, not a platform defect: I'd picked each asset's "latest"
  accepted-analysis row via `ORDER BY event_id DESC`, but `event_id` is `gen_random_uuid()` — not
  time-ordered at all. 5 of the 6 were false positives from comparing against the wrong (non-latest)
  row; my computed digests for those 5 were ALSO wrong for a second, independent reason (read
  `nirmana-writer-digests.json`/`nirmana-analysis-layer-pins.json` from this branch's own stale
  worktree instead of a fresh `origin/main` checkout — the SAME trap from #2240, self-repeated one
  cycle later).** No harm done — evidence is append-only and idempotency/conflict guards rejected all
  6 bad submissions cleanly; nothing corrupted. Redid the check correctly: `ORDER BY recorded_at DESC`
  for "latest," fresh worktree for the generated files. **Real result: only 1 asset genuinely
  drifted — `bg_vidhi_primitives`** (last accepted 2026-09-04, before PR #2153's `from_moon_view`
  routing fix changed its writer digest 93469b4c...→63f0a35a...; the other 5 had already been
  correctly re-stamped by whoever did that work, I just couldn't see it through my own ordering bug).
  Also learned along the way: the evidence route's git-commit check validates against the LIVE
  SERVER's own `NIRMANA_DEPLOYED_SHA` env var (`assertNirmanaGitCommitMatchesDeployment` in
  `definitions.ts`), not just any valid main-branch commit — fetched the actually-deployed SHA from
  `amjis-web`'s own live serving revision's `commit-sha` label (`7d3008f08...`) rather than guessing.
  Re-stamped `bg_vidhi_primitives` correctly with the fresh digest bound to that exact deployed SHA —
  **both `asset_analysis_accepted` and `optimization_verdict_accepted` accepted (HTTP 201).** All 40
  L0 assets' accepted analyses now genuinely match their live registry contracts. Lesson for future
  cycles, logged plainly: `event_id` is a random UUID in this schema — never use it as a recency
  proxy; always `ORDER BY recorded_at`. And: always compute against a fresh `origin/main` worktree
  for `src/generated/*.json`, never this branch's own copy — this is the second time this exact
  mistake nearly shipped wrong evidence, worth remembering for good.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0` re-run fresh: still 0
  rows — all 40 stay frozen, no regression from yesterday's re-stamp. Adjudication list and #1713
  tail both unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Checked #1945 directly: still OPEN, no change. Adjudication list and #1713 tail unchanged.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows. #1713 has
  new activity: Conductor's fleet-status post (cycle 853) independently confirms L0 is genuinely
  40/40 frozen (live-verified on their side too) and notes "L0's W6 layer-freeze ceremony can now
  close" — informational, not an action request directed at L0; the actual W6 stage-transition
  mechanism (#1945) remains open/parked, correctly not forced from here. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged since last cycle. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **D-NATIVE-08 fleet refocus posted by Conductor**: asset-frontier overrides
  sub-wave batching campaign-wide; only 2 assets are currently eligible fleet-wide
  (`ga_positions` L1, `ka_gochara_resonance` L3) — neither is L0's. Conductor also posted an
  L0 close-out status: 40/40 confirmed again independently, but the formal W6
  `stage_transition_accepted` ceremony still hasn't fired (needs all 5 Foundation Lanes;
  Lane C — 22 invalidated analyses — and Lane D — deploy lag — still block it) and Conductor is
  picking up Lane C/D themselves as their own next priority. **Responded with a genuinely useful,
  bounded, non-duplicating contribution**: re-ran the full 40-asset registry-fingerprint freshness
  check with the corrected method (fresh worktree, `recorded_at`-ordered) — confirmed 0/40 drifted,
  meaning L0's own contribution to Lane C's invalidated-analysis count is now zero (the one real
  drift, `bg_vidhi_primitives`, was already fixed last cycle). Posted this to #1713 to help
  Conductor's Lane C bookkeeping without stepping on their claimed work. Not touching
  `ga_positions`/`ka_gochara_resonance` — not L0's assets. Nothing else eligible for L0 itself.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows. New
  adjudication #2258 is L2's own grounding-lane design question, not L0-relevant. #1713 tail is my
  own prior post (already logged). Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified), but noting a genuine correction to my prior post's assumption.**
  Conductor re-investigated #1945 Lane C with the actual validator logic (`definitions.ts`
  `assertLaneReceipt`'s Lane-C branch, ~L2516-2519): `invalidated_analysis_count` counts EVERY
  historical `asset_analysis_accepted` event ever recorded, not just the latest-per-asset — an
  append-only log that structurally can never shrink via re-stamping alone, since old stale events
  are never superseded/removed. This means my prior post's claim ("if your Lane C count still
  includes an L0 asset, it should now be safe to drop it") was based on a wrong assumption about
  how the metric is computed — Conductor's real count is 26, including 8 `bg_*` HISTORICAL entries
  (`bg_doshas`, `bg_yogas`, `bg_parihara_rules`×2, `bg_compendium_index`, `bg_dasha_systems`,
  `bg_gochara_arcs`, `bg_vidhi_floors`, `bg_vidhi_primitives`) that can never be zeroed by
  re-stamping under the current query — only a scoped-to-latest query change would do it, and
  Conductor correctly flagged that as a validator-contract change outside their own standing
  authority, escalating for a native ruling rather than patching it unilaterally. **Not correcting
  my own prior post** — Conductor's reply already supersedes it precisely; a "thanks, noted"
  follow-up would be pure noise, not useful signal. `egate.sql -v layer=L0` re-run: still 0 rows —
  no impact on L0's own asset-freeze status, which was never in question (freeze != Lane C's
  historical-count metric). Nothing actionable for L0 here; this is Conductor→native, not
  delegated to any layer. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  #2180's new activity is Conductor's ruling on L1/L2's ga_positions/fact_id-scheme sequencing —
  not L0-relevant. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows. Hit a
  transient network error (`connection reset by peer`) on the first `gh issue list` call this cycle
  — retried the `#1713` tail check independently rather than assume anything from the failed call,
  confirmed unchanged. Adjudication list unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  `ga_positions` (L1) froze this cycle, cascading the eligible-frontier from 2 to 16 assets
  campaign-wide — but all 16 are L1/L2/L3 (`ga_*`/`bo_sudarshana`/`ka_*`), none L0's. Nothing
  eligible for L0.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Conductor nudged L1/L2/L3 on the 16-asset eligible frontier (zero movement yet) — none of the
  16 are L0's. Nothing eligible for L0.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Conductor flagged a stalled ga_dashas evidence-submission step and 15 untouched frontier assets —
  all L1/L2/L3, none L0's. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Conductor found L3's evidence-submission blocker was a wrong (browser-session) route; the fix is
  the sanctioned `nrec` OIDC tool — matches the discipline this session already follows via
  `l0_submit_evidence.sh`. Not L0-actionable. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows. New
  activity on #1770 is L2's own self-correction on a bo_sudarshana/CASCADE blast-radius doctrine
  question — not L0-relevant. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  #1713's new activity is L2's cross-post of the same #1770 bo_sudarshana blast-radius hold —
  not L0-relevant. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  L1's merged PR mentioned a "fleet-wide `asset_output_digest_specs` gap" — checked whether L0 was
  exposed: 38/39 `bg_*` writer assets have a spec row; the one exception, `bg_sign_medical`, is
  producer-covered by `bg_medical_mappings` (the `fixedProducerCoverage` map in `definitions.ts`),
  a correct, different evidence path (`producer_covered`, not its own `accepted_rebuild_observed`) —
  not a gap. All 40 L0 assets already reached `asset_frozen` independent of this table, confirming
  L0 was never exposed to L1's issue. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows. New
  adjudication #2276 (L1): `dispatch_nirmana_campaign_wave.py` has no supported redispatch path
  once ANY `accepted_rebuild_observed` exists for an asset, even a stale one from a superseded
  registry generation — a genuine structural gap that could bite L0 too in the future if a
  post-freeze registry-only fix is ever needed on an already-frozen `bg_*` asset. Not currently
  actionable (no L0 asset needs this); noted for future awareness. Awaiting Conductor/native
  ruling, not L0's to act on. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows. New
  activity on #1713 (L1's ga_vargas dispatch + ga_dashas blocker recap) and #1770 (L2 restating its
  bo_sudarshana blast-radius hold under new dispatch-first pressure) — both L1/L2's own progress,
  not L0-relevant. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows. #1770's
  new activity is L2's own scoped CASCADE-exposure measurement for bo_sudarshana — not L0-relevant.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Conductor's new activity is enforcement pressure on L1/L2/L3's frontier drain — not L0-relevant.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  `ga_vargas` (L1) froze this cycle — campaign progress, not L0-actionable. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. Hit a transient `git fetch` ref-lock error
  this cycle (`cannot lock ref 'refs/remotes/origin/main'`) — a concurrent-fetch race, not a real
  problem; retried once and it succeeded cleanly. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  L1 dispatched `ga_sensitive` — continued frontier drain, not L0-relevant. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  L1 dispatched `ga_panchanga` in parallel with `ga_sensitive` — continued frontier drain, not
  L0-relevant. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  `ga_sensitive` (L1) froze this cycle — campaign progress, not L0-actionable. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  `ga_panchanga` (L1) froze this cycle — campaign progress, not L0-actionable. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  L1 dispatched `ga_prashna` — continued frontier drain, not L0-relevant. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  L1 dispatched `ga_nakshatra` in parallel with `ga_prashna` — continued frontier drain, not
  L0-relevant. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  `ga_prashna` (L1) froze this cycle — campaign progress, not L0-actionable. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Conductor pushed L2/L3 to deprioritize their own heartbeat cadence in favor of frontier-drain
  (they have non-empty eligible frontiers, `bo_sudarshana`/6 `ka_*` assets). This directive does not
  apply to L0's situation: `egate.sql` confirms L0's own eligible frontier is genuinely empty (0
  rows), so heartbeat-only cycles remain the correct behavior here, not something to override.
  Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  Adjudication list and #1713 tail unchanged. Nothing eligible.
- 2026-09-07 — **IDLE-OK (verified).** No open L0 PRs. `egate.sql -v layer=L0`: still 0 rows.
  `ga_nakshatra` (L1) froze — 5 L1 assets frozen this cycle total (ga_vargas, ga_sensitive,
  ga_panchanga, ga_prashna, ga_nakshatra) — campaign progress, not L0-actionable. Nothing eligible.
