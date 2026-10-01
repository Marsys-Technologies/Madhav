---
asset_id: ka_bhavishya_lekha
layer: L3 Kāla (ka_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L3 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L3/L3_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 066c58587"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); output changes (FD-2, FD-3) and the D-1 design go to SS (R5)"
decisions_applied: "none specific to L3 yet; SS rulings of 2026-10-01 for L0 (Q2, Q11, Q13) by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-05, TI-L3-06, TI-L3-07, TI-L3-08, TI-L3-10, TI-L3-11, TI-L3-17, TI-L3-19, TI-L3-20]
ledger_gap_ids: ["ka_bhavishya_lekha-Build.completion", "ka_bhavishya_lekha-Earn.build_record", "ka_bhavishya_lekha-Cost.baseline", "ka_bhavishya_lekha-Count.floor", "ka_bhavishya_lekha-Complete.depth", "ka_bhavishya_lekha-Dens.served", "ka_bhavishya_lekha-Build.history", "ka_bhavishya_lekha-Build.dep_liveness", "ka_bhavishya_lekha-Carr.detector", "new: bhavishya-N1", "new: bhavishya-N2", "new: bhavishya-N3", "new: bhavishya-N4", "new: bhavishya-N5"]
---

# ka_bhavishya_lekha — Probabilistic forward projection artifact (top future darshana windows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in `INDEX.md` section 9. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py`.*

`ka_bhavishya_lekha.py`: reads up to 100 future `kala_darshana` windows (`peak_date` between today and today + 5 years, `net_label` not `obstructed_severe`, ordered by `effective_score` then `peak_date`, `convergence_id`; `:168-179`) joined to `kala_convergence`, and writes one projection per window into `kala_bhavishya`: `projection_rank`, `probability_tier` (cuts 0.70 / 0.45, `:450`), `domain` (the convergence row's `domain` when present, else keyword inference from the signal type id, `:493`), a falsifiability hook (±21 days around the peak, `:507`), a source chain and a four-field narrative whose caveat states the score is an uncalibrated structural prior (`:562`). It is the one L3 writer that protects history: outcomes (`outcome_recorded`, `outcome_notes`) are re-attached by `(signal_id, peak_date)` and rows referenced by `phala_anchors.bhavishya_id` keep their ids, so a rebuild updates matched rows in place, inserts new identities and prunes only proven-unreferenced stale ids (`:360-442`), refusing with a `RuntimeError` rather than rewriting a protected claim (`:393`). A per-chart advisory lock serialises the window (`:8`).

**Canonical chart: `stale`, 0 rows (cascade-shaped).** `kala_bhavishya` has 0 canonical rows while `asset_throughput` reads `stale`, `rows_written` 100, `last_built_at` 2026-08-13 01:15; Abhinandan holds 100 rows, the third chart 0 (I-6 table). Cause: the MSR replacement cascade (CF-24); the last `complete` build was run `cbd6ea44` (2026-08-13) and none has touched the chart since. Dependencies: 1 of 4 declared dependencies lit (`ka_kala_darshana`, `ka_vighnakara`, `ka_sangam` stale); `ka_kala_darshana` and `ka_sangam` are themselves empty for the chart, so a build now would find no darshana windows and, with no existing rows to protect, would return the no-windows note (`:209`). Wave 6 of the rebuild plan (v1.0 numbering, v1.1.1 keeps the order) (last of the Kāla chain, before `ph_nimitta`); not Nirmāṇa-frozen. The outcome-protection logic has nothing to protect on the canonical chart today (0 rows; the saved Complete.depth reads `outcome_notes` never populated on the 100 Abhinandan rows).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2437` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py:78`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_bhavishya`; count_sql tables: kala_bhavishya | census |
| live rows / floor | 0 / 100 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness no freshness row; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_kala_darshana`, `ka_vighnakara`, `ka_sangam`, `bo_laksana` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 1 / transitive 18 (census blocking_radius, every layer); named (REG 2026-09-30): L4 `ph_nimitta` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/lib/ahead_autofile.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`, `platform-mcp/src/tools/kala_views/now.ts`, `platform-mcp/src/tools/kala_views/promise_gate.ts`, `platform-mcp/src/tools/register_p1_aliases.ts`, `src/lib/retrieval/registry/knowledge/editorial.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/query_projections.ts`, `registry/layers/L3_kala/query_temporal_activation.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `bodha_writers/_idempotency.py`, `brahmagyan/domain_vocabulary.py`, `pipeline/orchestrator/kala_derivation_completeness_guard.py`, `pipeline/orchestrator/writers/ph_nimitta.py`, `services/ph_nimitta/engine.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_projections.ts:251` reads `kala_bhavishya`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | empty: live=0 (count_sql over the target table; chart 482012f1) and the registry does not declare zero rows complete (target_floor=100); build record rows_written=100 |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | FAIL | live=0, floor=100, delta=-100 |
| Complete (information, D3) | Complete.depth | PARTIAL | 100 rows, 18 cols; fully populated 17; NEVER populated ['outcome_notes'] |
| Dens | Dens.served † | FAIL | 2 module(s): query_projections.ts, query_temporal_activation.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 28 error(s) and 13 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) ka_kala_darshana, ka_sangam, ka_vighnakara did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 1/4 declared dependencies lit at chart 482012f1 (or global); stale: ['ka_kala_darshana (stale, chart 482012f1)', 'ka_vighnakara (stale, chart 482012f1)', 'ka_sangam (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = ["narrative.$.headline", "narrative.$.probability_statement", "narrative.$.domain_context", "narrative.$.caveat", "falsifiability.$.confirm_observable", "falsifiability.$.deny_observable"] (the cells would be measured by a fresh census; the Null check needs the database, so none could be run offline) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Vocab.identity; Build.exercised; Ldgr.source_presence.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 5 module(s) reach it by code: L3_kala/query_projections.ts, L3_kala/query_temporal_activation.ts, platform-mcp/src/tools/kala_views/ahead.ts, platform-mcp/src/tools/kala_views/now.ts, platform-mcp/src/tools/register_p1_aliases.ts; 5 served select(s) of its table; no referencing capability that serves it declares density_contract; a tier column is selected without a contract in: L3_kala/query_projections.ts, L3_kala/query_temporal_activation.ts

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **FAIL** — 4 declared edge(s); exists: all 4 are active registry assets (every layer); cycle: ka_bhavishya_lekha is on no dependency cycle (registry-wide graph); reads-match: FAIL — back-read: ka_bhavishya_lekha reads phala_anchors (ka_bhavishya_lekha.py:269), the product of ph_nimitta, which already depends on ka_bhavishya_lekha (chain ph_nimitta -> ka_bhavishya_lekha); an edge ka_bhavishya_lekha -> ph_nimitta would create a cycle

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_bhavishya_lekha-Build.completion | Build | real (cascade-shaped) | empty: live 0 against floor 100 and `rows_written` 100; cause I-6; clears with the rebuild chain (CF-24) |
| ka_bhavishya_lekha-Count.floor | Count | information | live 0 vs floor 100; floor equals the writer cap (`LIMIT 100`), not an achieved distribution |
| ka_bhavishya_lekha-Complete.depth | Complete | information | `outcome_notes` never populated (by design until an outcome is recorded; the table-wide census counts Abhinandan's 100 rows) |
| ka_bhavishya_lekha-Dens.served | Dens | Dens rev-1 reading | offline rev-7 reading FAIL (5 modules reach it, 5 served selects, no `density_contract`; `probability_tier` is selected without a contract, so the contract-plus-tier route applies, CF-04) |
| ka_bhavishya_lekha-Build.history | Build | history | 28 errors, 13 aborts; latest error 2026-08-12 is a cascade `BLOCKED` (CF-10) |
| ka_bhavishya_lekha-Build.dep_liveness | Build | stale | 1 of 4 declared dependencies lit; clears with the chain order |
| ka_bhavishya_lekha-Earn.build_record | Earn | detector | CF-05 |
| ka_bhavishya_lekha-Cost.baseline | Cost | information | CF-05 |
| ka_bhavishya_lekha-Carr.detector | Carr | detector | CF-07 (D2: the projection restates its darshana row) |
| census: Ldgr | Ldgr | information | PASS on `source_citation` populated 100/100 rows — table-wide (Abhinandan's rows) and a build tag (`ka_bhavishya_lekha:v1.0:rank=<n>`, `:345`), CF-08 |
| new: bhavishya-N1 | Idem / Build | real | `date(today.year + 5, today.month, today.day)` (`:180`) raises `ValueError` on 29 February (the next such build date is 2028-02-29, since 2033 is not a leap year); the window also moves with the build date (CF-28) |
| new: bhavishya-N2 | Vocab / honesty | real + SS question | domain inference is first-match over overlapping keyword lists (`:471`): `fourth` is listed under education, family and residence, `fifth` under education and progeny, `twelfth` under spirituality, travel and transition, `eighth` under health and transition, and the first listed domain wins, so a signal type id naming the fourth house maps to education (the first of the three lists containing it) unless an earlier-listed domain's keyword also matches; used only when `kala_convergence.domain` is absent (how often that is: not measurable, the canonical `kala_convergence` is empty) |
| new: bhavishya-N3 | honesty | real + SS question | the falsifiability window is a constant ±21 days for every domain and tier (`:536`) although the row carries its own `window_start`/`window_end`; the confirm text asserts "Observable within ±21 days" without a derivation |
| new: bhavishya-N4 | Build.dag | design (Track I D-1) | back-read: the writer reads `phala_anchors` (`:268-271`; E6 and Track I D-1 cite `:269`) while `ph_nimitta` already depends on it, so the E6 reads-match detector reports FAIL "back-read, an edge would create a cycle" and no edge can be added; the declared edge to `ka_vighnakara` is never read (CF-23) |
| new: bhavishya-N5 | Idem | information | DELETE-then-return is NOT present here (the writer raises on an empty plan while rows exist, `:198`) — the CF-21 model; recorded so the gate does not read it as a gap |
| census: Null/Narr | Null, Narr | detector | six declared `prose_fields` paths (headline, probability_statement, domain_context, caveat, confirm_observable, deny_observable); no fidelity test measured; CF-25 |

## 3 · Disposition

**keep (P)** — the most careful L3 writer on history and honesty (outcome re-attachment, protected rows, a caveat that states the score is uncalibrated, an explicit `general` instead of rotating domains). Its defects are a date-arithmetic bug, an order-dependent keyword map, a constant falsifier window and a DAG design item; none argues for a different disposition.

Approver under Track A brief §10: **Steward (G16); output changes (FD-2, FD-3) and the D-1 design go to SS (R5)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Calendar-safe horizon and a pinned as-of

- **Answers:** new bhavishya-N1; CF-28
- **Change:** compute the end of the window with month arithmetic that clamps 29 February (or `timedelta(days=…)` of a stated length) and take `as_of_date` from the run config (default `date.today()`, recorded in the build note), the same key `ka_jivana_parva` already reads
- **Files / declaration / migration:** `ka_bhavishya_lekha.py:83`, `:180`
- **Failing-first test and mutation:** Failing-first: with `today` = 2028-02-29 the current code raises, after the fix the window ends 2033-02-28; two runs with the same pinned as-of select the same windows; mutation: restore the arithmetic → fails.
- **Output change:** none on non-leap days
- **Blast radius:** writer code; the selected 100 windows are the same on every non-29-February build for a given as-of
- **Rebuild:** none (exercised by the next rebuild)
- **Gate it moves:** Build / Idem (deterministic rebuild)
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-2 · Domain inference with an explicit precedence (or no inference)

- **Answers:** new bhavishya-N2; CF-30
- **Change:** replace first-match substring scanning by an explicit mapping from signal type id to domain with a documented precedence and an explicit `general` for ambiguous ids (a signal type id that matches two domains is ambiguous), or drop inference and require `kala_convergence.domain`; keep `kc.domain` preferred as now (`:310`)
- **Files / declaration / migration:** `ka_bhavishya_lekha.py:471-504`
- **Failing-first test and mutation:** Failing-first: a fourth-house signal type id no longer maps to education; an id matching two domains reads `general`; mutation: restore list order → fails.
- **Output change:** yes — `domain` of affected rows → SS (R5)
- **Blast radius:** rows referenced by `phala_anchors.bhavishya_id` or carrying a recorded outcome are immutable in this writer (`RuntimeError` at `:393`): a domain change on such a row makes the rebuild refuse, so this fix must land before any anchor or outcome references the rows, or SS accepts the refusal (on the canonical chart `kala_bhavishya` is empty and `phala_anchors` holds 4 rows at the census, whether they reference these ids is not measured); consumers: `query_projections.ts`, `ahead.ts`, `now.ts`, `promise_gate.ts`, `ahead_autofile.ts`, `ph_nimitta`
- **Rebuild:** needs production rebuild (REVIEW for SS); sequence before `ph_nimitta` rebuilds
- **Gate it moves:** Vocab / honesty
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-independent for the precedence mechanics; the mapping itself is a domain ruling

### FD-3 · Derive the falsifier window from the window, or ratify the constant

- **Answers:** new bhavishya-N3; CF-27
- **Change:** state the evaluation window as a function of the stored window (`window_start`/`window_end`) or record ±21 days as a ratified approximation with a decision id and surface that in `falsifiability` (`evaluation_window_days` already exists); the text then names the actual window
- **Files / declaration / migration:** `ka_bhavishya_lekha.py:507-536`
- **Failing-first test and mutation:** Failing-first: the confirm and deny strings quote the stored window; mutation: restore ±21 → fails.
- **Output change:** yes — `falsifiability` text and `evaluation_window_days` → SS (R5)
- **Blast radius:** `falsifiability` is read by `ahead.ts`/`ahead_autofile.ts` (auto-filing of predictions: `platform-mcp/src/lib/ahead_autofile.ts` references the table) — a window change moves what an auto-filed prediction is evaluated against; `mimamsa` outcome matching by `(signal_id, peak_date)` is unaffected
- **Rebuild:** needs production rebuild (REVIEW for SS)
- **Gate it moves:** Narr / Carr
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-independent

### FD-4 · Split the anchor-existence guard (back-read design, Track I D-1)

- **Answers:** new bhavishya-N4; CF-23
- **Change:** move the "which bhavishya ids already have anchors" guard to the L4 side (an L4 consumer refuses to orphan), or have `ph_nimitta` stop reading `kala_bhavishya`, so the dependency runs one way; remove the unread `ka_vighnakara` edge (CF-23). Not designed further here: it needs an L4 owner.
- **Files / declaration / migration:** design only
- **Failing-first test and mutation:** the reads-match detector reads PASS for this asset after the split; mutation: restore the read → FAIL back-read.
- **Output change:** none
- **Blast radius:** `kala_bhavishya` ↔ `phala_anchors` coupling; `ph_nimitta` is not Nirmāṇa-frozen
- **Rebuild:** none
- **Gate it moves:** Build.dag
- **Fix class:** registry/declaration + writer code (two layers); **buildable before J1:** tier-independent in content, a DAG design: own review

### FD-5 · Narr golden-value test for the projection narrative

- **Answers:** census Narr (declared six paths); CF-25
- **Change:** fixture-based golden test: tier label, effective score, confidence, cycle length and the caveat all equal what the cited row carries; the `tier_basis`-driven caveat branch is asserted both ways
- **Files / declaration / migration:** `tests/l3/test_ka_bhavishya_lekha.py` (extend) / a new golden file
- **Failing-first test and mutation:** Failing-first: a projection whose narrated score differs from the stored `effective_score` fails; mutation: change one composed value → fails.
- **Output change:** none
- **Blast radius:** none (tests)
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** detector/tooling (tests); **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset. Track I D-1 (the back-read) is FD-4.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `catalog_status` DRAFT vs CURRENT live
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D2: the projection restates its darshana row (tier from score and label, source chain from the convergence row)
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* build tag in `source_citation`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 28 errors / 13 aborts
- **CF-21** — Replace-after-candidate: DELETE runs before the empty-upstream early return (five writers). *This asset:* the CF-21 model: the writer refuses rather than deleting on an empty plan
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* FD-4 and the unread `ka_vighnakara` edge
- **CF-24** — L2 -> L3 cascade keys and rebuild order (F-3 / migration 1214): four emptied tables and the dangling predicate set. *This asset:* table emptied for the canonical chart; wave 6
- **CF-25** — Narr fidelity (golden-value) tests per L3 narration writer. *This asset:* FD-5
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* FD-3; tier cuts 0.70/0.45
- **CF-28** — Rolling-horizon writers: as-of pin, calendar-safe horizon, floors that move with the build date. *This asset:* FD-1
- **CF-30** — Duplicated hand-written reference tables in L3 writers (graha -> domain, natural malefics, combustion orbs, Rikta set). *This asset:* FD-2
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* table-wide `integrity_check_sql` (audit; none measured false)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(signal_id, peak_date)` (the writer's own outcome identity, `:30`); `id` is retained across rebuilds by design (FK from `phala_anchors`). Volatile columns excluded: `id`, `computed_at`; `projection_rank` moves with re-ranking and is part of the claim only through `effective_score`. Fingerprint taken at a pinned as-of window (CF-28). Outcome columns (`outcome_recorded`, `outcome_notes`) are observations, not derived: excluded from the derived-content comparison and compared separately (they must survive). Rebuild expectation: unchanged rows are skipped (`rows_skipped`), so a converged rerun reports `rows_written` = changed rows only (the L0 CF-01 convention applies).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** outcome re-attachment and protected-row logic, the explicit `general` domain, the uncalibrated-prior caveat, the advisory lock.
- **Carriage check chosen (T4 §4.1; one only):** D2 (witness carriage): the stored tier, effective score and source chain restate the cited `kala_darshana`/`kala_convergence` row; the check re-derives tier from score and label with the writer's own thresholds.
- **Opportunities (never blocking):** record outcomes (the L5 loop) so `outcome_notes` is populated; the `falsifiability` hook is the natural input for an evaluation tab; a calibrated tier would need L5 data.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L3-05** — FD-2/FD-3: is the keyword precedence a domain ruling for SS or an acharya, and is ±21 days a ratified constant?
- **Q-L3-08** — FD-4: which side owns the anchor-existence guard (L3 or L4)?

**Track I items arising (see INDEX section 10):** TI-L3-05, TI-L3-06, TI-L3-07, TI-L3-08, TI-L3-10, TI-L3-11, TI-L3-17, TI-L3-19, TI-L3-20.
