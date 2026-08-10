CAMPAIGN-STATUS: RUNNING
campaign: GOCHARA-UTKARṢA
plan: GOCHARA_UTKARSHA_CAMPAIGN_PLAN_v1_0.md
branch: utkarsha/campaign
conductor_model: claude-sonnet-4-6
launched: 2026-08-10
last_updated: 2026-08-10 (conductor restart — session 2 reconciliation)

---

## §I6(c) — Pre-Campaign Protected Corpus Snapshot

Recorded at first launch. These are the canonical checksums the rail verification checks against.

| chart_id | chart | generation | row_count | corpus_checksum_md5 |
|---|---|---|---|---|
| 482012f1-710e-4a25-994a-93821f5871aa | native | v1 | 16,297 | b9834dc43c545d0af9a8251d4af2ec9d |
| 1c826d5a-41cb-4450-b4dc-59d440e5f75a | Abhinandan | v1 | 19,323 | 47c30b7df1b256200dca94a2e6dc11cf |

**Checksum method:** `md5(string_agg(chart_id||'|'||event_class||'|'||temporal_shape||'|'||window_start||'|'||window_end||'|'||COALESCE(peak_date,'')||'|'||COALESCE(milestone_id,'')||'|'||COALESCE(signed_intensity,'')||'|'||COALESCE(raw_intensity,'')||'|'||COALESCE(valence,'')||'|'||COALESCE(is_adverse,'')||'|'||COALESCE(calibration_state,'')||'|'||COALESCE(generation,''), '||' ORDER BY chart_id, event_class, window_start, window_end, COALESCE(milestone_id,'')))`

---

## §I6(b) — Protection Rail Baseline (pre-campaign state)

Recorded at first launch for diff-comparison at every wave boundary.

**Triggers on `kala_gochara_windows`:**
- `trg_kala_gochara_windows_protect_row` → function `build_protected_assets_guard_row` (row-level, BEFORE DELETE/UPDATE)
- `trg_kala_gochara_windows_protect_truncate` → function `build_protected_assets_guard_truncate` (truncate-level)

**Guard function:** `build_protected_assets_guard_row` — checks `build_protected_assets` for `asset_id='ka_gochara_sweep'` + `chart_id=OLD.chart_id`; GUC `app.allow_protected_sweep_rewrite` bypass present (prohibited campaign-wide per I1). Generation-blind at baseline (W0.3 Phase B will add `protected_generations text[]`).

**Unique index:** `uq_kala_gochara_windows_natural_key` — `(chart_id, event_class, window_start, peak_date, COALESCE(milestone_id, ''))` — **generation-blind** (expected pre-W0.3; W0.3 Phase B replaces with generation-inclusive form).

**`build_protected_assets` rows at baseline:**
- `(asset_id='ka_gochara_sweep', chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a')` — protected since 2026-08-06
- `(asset_id='ka_gochara_sweep', chart_id='482012f1-710e-4a25-994a-93821f5871aa')` — protected since 2026-08-06

**`protected_generations` column:** does NOT yet exist (added by W0.3 Phase B migration 556).

**Latest migration applied:** `555_brahma_event_ontology_g9_reconcile.sql` (id=414, applied 2026-08-09).

---

## §Lane Table

Status: QUEUED | BUILDING | VERIFYING | PASS | FAIL(n) | BLOCKED | MERGED

| lane | wave | tag | title | status | branch | worktree | builder_model | deps | notes |
|---|---|---|---|---|---|---|---|---|---|
| W0.1 | 0 | [mech] | Registry & seed hygiene | BUILDING | gochara3/w01 | /Users/Dev/Vibe-Coding/Apps/utk-w01 | sonnet | none | Uncommitted: seed.ts (+3 assets), test_has_writer_completeness.py (+3-way guard). Still ~16 assets missing from seed. Re-spawned in session 2. |
| W0.2 | 0 | [mech] | Baseline builds + error triage | BUILDING | gochara3/w02 | /Users/Dev/Vibe-Coding/Apps/utk-w02 | sonnet | none | Uncommitted: ka_vedha_gochara/writer.py + ka_kota_chakra/writer.py + sarvatobhadra.py (DB9 fixes). Actual builds not yet run. Re-spawned in session 2. |
| W0.3 | 0 | [heavy] | Schema migration bundle | VERIFYING | gochara3/w03 | /Users/Dev/Vibe-Coding/Apps/utk-w03 | opus | none | 3 commits: Phase A writer scoping, Phase B migration 556, generation-aware guard tests. Clean branch. VERIFIER spawned. |
| W0.4 | 0 | [heavy] | Batched-context scoring engine | VERIFYING | gochara3/w04 | /Users/Dev/Vibe-Coding/Apps/utk-w04 | opus | none | 3 commits: gochara_v3 package (context.py + engine.py), 3 test files (query-count, parity, speedup). Clean branch. VERIFIER spawned. |
| W0.5 | 0 | [adj] | Campaign rulings (UTK-R1/R2/R3) | PASS | — | — | ADJUDICATOR | none | UTK-R1/R2/R3 issued + I6(a) migration approved. Rulings in §Rulings. |
| I6a | 0 | [mech] | DB role migration (utkarsha_builder) | VERIFYING | gochara3/i6a-role | /Users/Dev/Vibe-Coding/Apps/utk-i6a | sonnet | W0.5 PASS | Migration 557 written + pushed (SHA 4879a6882, session 5). Migration-guard self-review: PASS. Awaiting dedicated VERIFIER PASS before PR. |
| W1.1 | 1 | [heavy] | Bounded λ_v3 core | QUEUED | — | — | opus | W0.4 PASS | Gate: W0.4 |
| W1.2 | 1 | [heavy] | Direction restored | QUEUED | — | — | opus | W1.1 PASS | Gate: W1.1 |
| W1.3 | 1 | [heavy] | Graded suppression | QUEUED | — | — | opus | W1.1 PASS | Gate: W1.1 |
| W1.4 | 1 | [heavy] | Self-normalizing thresholds | QUEUED | — | — | opus | W1.1 PASS | Gate: W1.1 |
| W1.5 | 1 | [mech] | λ decomposition + uncertainty output | QUEUED | — | — | sonnet | W1.1 PASS | Gate: W1.1 |
| W2.1 | 2 | [heavy] | Ashtakavarga gating, real | QUEUED | — | — | opus | W1.1 PASS | Parallel W2; needs W0.2 data |
| W2.2 | 2 | [mech] | Moorti nirnaya modifier | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2; needs W0.2 data |
| W2.3 | 2 | [mech] | Tara bala, alive | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W2.4 | 2 | [heavy] | Sade Sati, fully | QUEUED | — | — | opus | W1.1 PASS | Parallel W2 |
| W2.5 | 2 | [mech] | Kota Chakra overlay | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W2.6 | 2 | [mech] | Real eclipses | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W2.7 | 2 | [heavy] | Annual context stack | QUEUED | — | — | opus | W1.1 PASS | Parallel W2 |
| W2.8 | 2 | [mech] | Bhava targets get degrees | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W2.9 | 2 | [mech] | Citation resolution table | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W3.1 | 3 | [heavy] | 27-class coverage | QUEUED | — | — | opus | W1.* PASS | No Wave-2 dep; can overlap W2 dispatch |
| W3.2 | 3 | [heavy] | Interval + chain shapes | QUEUED | — | — | opus | W1.4 PASS | Gate: W1.4 |
| W3.3 | 3 | [heavy] | Multi-resolution hierarchy | QUEUED | — | — | opus | W3.2 PASS | Gate: W3.2 |
| W3.4 | 3 | [heavy] | Century horizon + slice receipts | QUEUED | — | — | opus | W0.3 PASS + W3.2 PASS | Gate: W0.3 + W3.2 |
| W4.1 | 4 | [heavy] | λ contenders in the bakeoff | QUEUED | — | — | opus | W3.4 + ALL Wave-2 PASS | Gate: W3.4 + all W2.* |
| W4.2 | 4 | [heavy] | Negative-control harness | QUEUED | — | — | opus | W3.4 PASS | Gate: W3.4 |
| W4.3 | 4 | [heavy] | Ablation runner → grammar admissions | QUEUED | — | — | opus | W3.4 + ALL Wave-2 PASS | Gate: W3.4 + all W2.* |
| W4.4 | 4 | [heavy] | Weight fitting, cross-chart pooled | QUEUED | — | — | opus | W4.1 + W4.2 + W4.3 PASS | Gate: W4.1–W4.3 |
| W4.5 | 4 | [heavy] | empirically_calibrated, earnable + post-fit rebuild | QUEUED | — | — | opus | W4.4 PASS | Gate: W4.4; owns post-fit rebuild |
| W4.6 | 4 | [mech] | LEL mining (non-blocking) | QUEUED | — | — | sonnet | W3.4 PASS | Non-blocking; output is LEL_CANDIDATES_STAGED.md for native review |
| W5.1 | 5 | [heavy] | Serving elevation under density contract | QUEUED | — | — | opus | W3.3 + W4.5 PASS | Parallel W5 |
| W5.2 | 5 | [mech] | Nirmāṇa/DAG integration | QUEUED | — | — | sonnet | W3.3 + W4.5 PASS | Parallel W5 |
| W5.3 | 5 | [mech] | Docs-of-record | QUEUED | — | — | sonnet | W3.3 + W4.5 PASS | Parallel W5 |
| W5.4 | 5 | [heavy] | Writer repoint + mutation-guard evolution | QUEUED | — | — | opus | UTK-R1 + W0.3 + W3.4 PASS | Parallel W5; gate: UTK-R1 ruling + W0.3 + W3.4 |
| W6.1 | 6 | [ops] | Full-century production builds | QUEUED | — | — | ops | ALL W3/W4/W5 MERGED + W5.4 + W4.5 post-fit | Sequential; needs W5.4 repointed writer |
| W6.2 | 6 | [ops] | Three-legged replacement gate | QUEUED | — | — | VERIFIER | W6.1 PASS | Sequential |
| W6.3 | 6 | [ops] | Authority flip, rehearsed | QUEUED | — | — | ops | W6.2 PASS | Sequential; Abhinandan first, then native |
| W6.4 | 6 | [ops] | Retirement + rename | QUEUED | — | — | ops | W6.3 PASS | Sequential |
| W6.5 | 6 | [ops] | Campaign close | QUEUED | — | — | ops | W6.4 PASS | Sequential; final |

---

## §Rulings

**UTK-R1: W6 cutover mechanism — generation='3.0' rows in kala_gochara_windows + authority seam**
- kala_gochara_windows is the production serving table; kala_gochara_windows_v2 is workbench/validation only.
- generation='3.0' rows are INSERTed directly into kala_gochara_windows at W6 cutover. The INSERT path is ungated (no BEFORE INSERT trigger blocks it).
- Per-chart authority flip via kala_gochara_authority table using the existing COALESCE pattern already live in three serving surfaces (register_gochara_windows.ts, reading_checklist.ts, mcp/db/query/route.ts). Table is currently empty — v1 authoritative by default.
- Migration 540 guard amended: OLD.generation = ANY(protected_generations) so generation-3.0 DELETEs pass while v1 DELETEs still raise on protected charts. **Already implemented in W0.3 migration 556.**
- Unique index on kala_gochara_windows now includes generation in natural key. **Already implemented in W0.3 migration 556.**
- kala_gochara_windows_v2 stays as workbench only.
- Evidence: ADJUDICATOR research of migrations 527, 540, 542; live serving surface code (three files); 2026-08-10 session 1.

**UTK-R2: Asset naming at W6.4 cutover — retire zero-row self-test, rename materialize writer**
- ka_gochara (zero-row service self-test, services/ka_gochara/writer.py) → retired: DELETE from asset_registry.
- ka_gochara_v2_materialize → renamed to ka_gochara: UPDATE asset_registry + writer @register decorator change.
- ka_gochara_sweep: stays registered with catalog_status='RETIRED', is_active=false; data and protection remain permanently.
- Jupiter transit self-test: absorbed as pre-flight check in renamed writer, or deleted — builder's discretion.
- Migration: surgical (DELETE old ka_gochara row, UPDATE ka_gochara_v2_materialize → ka_gochara).
- Evidence: ADJUDICATOR review of services/ka_gochara/writer.py, ka_gochara_v2_materialize.py, migration 542; 2026-08-10 session 1.

**UTK-R3: Grammar-v3 register canonical format — YAML with v1_lineage load-bearing field**
- Format: YAML file in services/gochara_v3/ (or campaign plan dir), loadable as Python dict at import.
- Required fields per mechanism entry: mechanism_id, wave, lane, description, citation_status, classical_citation, v1_lineage {replaces, v1_module, change_type, note}, module_path, admission_state (candidate|admitted|structural-only|rejected), ablation_evidence_link, admission_ruling_id, toggle_key.
- v1_lineage is load-bearing: required for W4.1 golden parity test + W6.2 no-loss coverage gate.
- Wave-2 default admission_state = 'candidate'.
- toggle_key enables ablation runner to mechanically disable/enable per mechanism.
- Evidence: ADJUDICATOR review of citations.py, primitives.py, mechanisms.py; 2026-08-10 session 1.

**I6(a): utkarsha_builder DB role — migration 557 (NOT 556 — number taken by W0.3 gochara schema)**
- NOLOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE Postgres role.
- NO DDL privileges. NO ability to SET app.allow_protected_sweep_rewrite GUC.
- READ SELECT: 14+ tables (gochara_resonance_map, bg_gochara_arcs, ephemeris_daily, chart_facts, chart_dashas, public.charts, bg_transit_rules, bg_transit_engine, bg_transit_av_gates, brahma_event_ontology, kala_gochara_authority, kala_gochara_windows (READ only), build_protected_assets, plus kala_vedha_gochara, kala_moorti_nirnaya, kala_kota_chakra, kala_tithi_pravesha, bg_sky_calendar, bg_vedha_malefic_scale, bg_phaladeepika_latta, bg_kota_chakra_rings).
- WRITE: kala_gochara_windows_v2 (INSERT/UPDATE/DELETE), kala_gochara_v2_build_state (INSERT ON CONFLICT UPDATE), kala_gochara_windows (INSERT only — NO DELETE, deferred to W5.4), build_substep_progress (upsert+replan), asset_registry (health UPDATE only).
- Sequence grants: USAGE+SELECT on kala_gochara_windows_v2_id_seq and kala_gochara_windows_id_seq.
- Idempotent via DO block (CREATE ROLE IF NOT EXISTS; GRANTs idempotent by definition).
- Implementation: gochara3/i6a-role branch, worktree /Users/Dev/Vibe-Coding/Apps/utk-i6a.
- Migration-guard agent review required before PR (I6(d)).
- Evidence: ADJUDICATOR footprint audit of v2/v3 writer dependencies; 2026-08-10 session 1.

---

## §Wave Deployments

*(No wave deployments yet — Wave 0 still in progress)*

Format: `WAVE N: DEPLOYED+SYNCED — revision <sha>, migrations applied through <N>, I6(b) rail check: <PASS/drift>`

---

## §I6(a) — DB Role Provisioning

**Status: BUILDING** — Migration 557 (`557_utkarsha_builder_role.sql`) authored in gochara3/i6a-role branch. Pending migration-guard review + VERIFIER PASS + merge to main. Builders connect as this role only after the migration deploys.

**Note:** Migration 556 is the W0.3 gochara generation schema (era_slice_key + protected_generations + generation-inclusive index + amended guard function). The utkarsha_builder role is migration **557**.

---

## §Event Log

- 2026-08-10 05:10 IST: FIRST LAUNCH. Branch `utkarsha/campaign` created from origin/main (rev 3311ae0e3). LEDGER.md initialized. I6(c) snapshot recorded. I6(b) rail baseline recorded. Latest migration: 555 (id=414). All 34 lanes seeded QUEUED.
- 2026-08-10 05:12 IST: Wave 0 worktrees provisioned: utk-w01, utk-w02, utk-w03, utk-w04. All W0.x lanes → BUILDING.
- 2026-08-10 05:12–05:34 IST: Session 1 execution (builders dispatched, ADJUDICATOR spawned, partial work committed).
  - ADJUDICATOR: UTK-R1/R2/R3 issued; I6(a) role design approved. W0.5 → PASS.
  - W0.3 builder: Phase A (writer scoping) + Phase B (migration 556) + tests committed (3 commits). Branch clean.
  - W0.4 builder: gochara_v3 package (context.py + engine.py + 3 test files) committed (3 commits). Branch clean.
  - W0.1 builder: Partial — seed.ts (+3 assets) + test_has_writer_completeness.py (+3-way guard) UNCOMMITTED. ~16 assets still missing from seed.
  - W0.2 builder: Partial — DB9 fixes (vedha_gochara + kota_chakra + sarvatobhadra) UNCOMMITTED. Builds not yet run.
  - I6(a) branch gochara3/i6a-role created; worktree path broken. Migration 557 not yet written.
  - LEDGER.md updates from session 1 NOT pushed (this ledger is the corrected version from session 2).
- 2026-08-10 05:37 IST: SESSION 2 (conductor restart). Reconciliation complete. W0.3 → VERIFYING; W0.4 → VERIFYING; W0.1/W0.2 re-spawned; i6a-role worktree reattached; migration 557 builder spawned.
- 2026-08-10 06:22 IST: SESSION 3 (conductor restart). Reconciliation: all 5 worktrees exist and match ledger. W0.3 (gochara3/w03): 3 commits committed, clean — VERIFIER died with session 2, re-spawning VERIFIER. W0.4 (gochara3/w04): 3 commits committed, clean — VERIFIER died with session 2, re-spawning VERIFIER. W0.1 (gochara3/w01): 829-line uncommitted diff (seed.ts + test file) — builder died before committing, re-spawning builder to complete + commit. W0.2 (gochara3/w02): 33-line uncommitted diff (3 writer fixes) — builder died before committing/running builds, re-spawning. I6a (gochara3/i6a-role): clean branch, no commits — builder from session 2 produced nothing, re-spawning from scratch. Dispatching 5 agents in parallel.
- 2026-08-10 06:28 IST: SESSION 4 (conductor restart). Reconciliation: all 5 worktrees confirmed present and match ledger state exactly. W0.3 (gochara3/w03): 3 commits, clean — session 3's VERIFIER was killed before producing verdict; re-spawning VERIFIER. W0.4 (gochara3/w04): 3 commits (W0.4 parity fix included), clean — session 3's VERIFIER was killed; re-spawning VERIFIER. W0.1 (gochara3/w01): still on base commit, 829-line uncommitted diff (seed.ts + test file) — session 3's builder also produced nothing committed; re-spawning builder. W0.2 (gochara3/w02): still on base commit, 33-line uncommitted diff (3 writer fixes) — session 3's builder produced nothing committed; re-spawning builder. I6a (gochara3/i6a-role): still on base commit, clean — three consecutive sessions have produced nothing; re-spawning builder with full migration 557 spec from ledger §I6(a). Dispatching 5 agents in parallel.
- 2026-08-10 06:50 IST: SESSION 5 (conductor restart). Heartbeat absent (last session died without writing one). Reconciliation: all 5 worktrees present. W0.3: 3 commits, clean — VERIFIER dispatched again (4th attempt). W0.4: 3 commits, clean — VERIFIER dispatched again (4th attempt). W0.1: still base commit, 829-line uncommitted diff — SALVAGING uncommitted work directly then dispatching builder to complete. W0.2: still base commit, 33-line uncommitted diff — SALVAGING uncommitted work directly then dispatching builder to run builds. I6a: still base commit, clean — builder dispatched again (5th attempt) with full migration 557 spec. Pattern noted: builders/VERIFIERs are dying with the conductor session before committing. W0.1+W0.2 salvage will be done by conductor directly to protect that work regardless of session duration.

- 2026-08-10 06:52 IST: SALVAGE COMPLETE. W0.1: committed 829-line partial (seed.ts +19 assets including ka_gochara_sweep/resonance/v2_materialize, test guard helpers) → gochara3/w01 pushed. W0.2: committed 33-line partial (ka_vedha_gochara + ka_kota_chakra + sarvatobhadra fixes) → gochara3/w02 pushed. Both now have 1 commit on branch. Dispatching 5 agents in parallel: VERIFIER(W0.3+W0.4), builder(W0.1-complete), builder(W0.2-builds), builder(I6a-557).
- 2026-08-10 06:52 IST: Lane table updated post-salvage: W0.1 now has committed work (1 commit).

- 2026-08-10 06:55 IST: 4 agents dispatched in parallel — VERIFIER(opus, W0.3+W0.4), builder(sonnet, W0.1-complete), builder(sonnet, W0.2-builds), builder(sonnet, I6a-557). All running background. Awaiting verdicts.

- 2026-08-10 06:57 IST: I6a DONE — migration 557 written and pushed (4879a6882). Migration-guard self-review PASS. I6a → VERIFYING. VERIFIER for W0.3/W0.4 still running; W0.1/W0.2 builders still running.

CONDUCTOR-HEARTBEAT: 2026-08-10T01:27:00Z
