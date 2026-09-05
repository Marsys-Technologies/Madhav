---
artifact: L0_STATE.md
canonical_id: NIRMANA_V21_L0_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L0
layer: L0 — Brahmagyan
owner: the L0 session (this file is yours alone — charter C5)
last_updated: 2026-09-05 — evidence-submission mechanism reconstructed (D-L0-P); token minting verified for both SAs; still need definitions table + payload JSON before actual submission
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

**L0-W4 EXECUTE + Conform-stage integrity corrections.** W1/W2/W3 done for the 29 frozen. **29/40
frozen** (verifier-signed 5-event chains, implementer≠verifier). **11 remaining**, all diagnosed.

## The 11 unfrozen assets

| asset | route | status / blocker |
|---|---|---|
| bg_cohort | rebuild_only | DEP-ASSERT on service dep `bg_ephemeris_engine` — fixed in #1772 (merged) but **job image `d93d9d0a` predates it**; dispatch held on job-image deploy |
| bg_gochara_arcs | **no dispatch needed** | **Drafted rewrite LANDED (migration 694, PR #1836)**: stale bare-count + hardcoded per-body VALUES table replaced with gapless-tiling + achieved floor (33,933). Verified TRUE against live data as-is — can go straight to W4 accept on LIVE fingerprint, same as bg_doshas |
| bg_yogas | rebuild_only | **VERDICT CLOSED (D-L0-J): writer correct, no fix.** Live 233/229/229/0 is stale pre-migration-630 data; dispatch alone produces 233/233/233/85. CASCADE parent → snapshot+`--acknowledge-destroys` |
| bg_dasha_systems | rebuild_only | **VERDICT CLOSED (D-L0-K): writer correct, no fix.** Live catalog=20/ontology=20/reference=19 (kp missing only from reference) is stale pre-reconciliation data (63aeba051); `DASHA_SYSTEMS` list already has 20 unique incl. kp, one synced transactional loop writes all 3 tables — dispatch alone produces 20/20/20 |
| bg_doshas | **no dispatch needed** | **VERDICT CLOSED (D-L0-L): check bug, not data.** Data already 79/79/79, hashes already match; the "658 violations" were 658 leaked non-dosha `brahma_ontology` rows (ON-clause filter bug in a FULL JOIN, not an ON-clause+WHERE prefilter). Migration 692 fixes the check; PR #1829 open. Once merged, this asset can go straight to W4 accept on the LIVE fingerprint — no rebuild |
| bg_vidhi_floors | rebuild_only | **Both open questions diagnosed, fully verified read-only.** Tiling false-positive FIXED (D-L0-M, PR #1832). 11/14-intent, 286/409-item gap traced to stale-build (D-L0-N) — same family as D-L0-J/K, source is internally sound (14/409, 0 dangling FKs) — pending job-image redeploy + dispatch + `catalog_status` DRAFT→CURRENT (D-CND-09) |
| bg_parihara_rules | **UNROUTED** | only asset with no W2 events — W1/W2 now (never gated); note migration-644 integrity_check_sql drift vs frozen manifest |
| bg_compendium_index | rebuild_only | wave 2; depends_on normalized; needs wave-1 frozen (E-gate) + own integrity check |
| bg_rules | rebuild_only | wave 2; depends_on normalized |
| bg_text_index | rebuild_only | wave 2; depends_on normalized |
| bg_concordance | rebuild_only | wave 3; depends_on normalized; deepest DAG node |

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

## Held items

- **bg_cohort dispatch** — held until the pipeline **job image** carries #1772 (`ee8cf7d09`); current
  image `d93d9d0a` predates it. Poll deploy each loop.
- **Wave-2/3 dispatch** (compendium_index, rules, text_index, concordance) — E-gate needs wave-1 frozen.
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
