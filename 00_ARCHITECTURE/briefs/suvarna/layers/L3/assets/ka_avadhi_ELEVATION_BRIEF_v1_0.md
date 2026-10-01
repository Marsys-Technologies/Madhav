---
asset_id: ka_avadhi
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
disposition_proposal_approver: "Steward (G16); the output changes in FD-1, FD-3 go to SS (R5)"
decisions_applied: "none specific to L3 yet; SS rulings of 2026-10-01 given for L0 (Q2 Dens, Q11 Build.history, Q13 Carr) are applied by analogy where stated and are PROVISIONAL until the J1 review"
track_i_items: [TI-L3-10, TI-L3-11, TI-L3-14, TI-L3-15, TI-L3-16]
ledger_gap_ids: ["ka_avadhi-Build.completion", "ka_avadhi-Earn.build_record", "ka_avadhi-Cost.baseline", "ka_avadhi-Dens.served", "ka_avadhi-Build.history", "ka_avadhi-Build.dep_liveness", "ka_avadhi-Carr.detector", "new: avadhi-N1", "new: avadhi-N2", "new: avadhi-N3", "new: avadhi-N4", "new: avadhi-N5"]
---

# ka_avadhi — Period dossiers over the MD and AD levels of the dasha systems

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in `INDEX.md` section 9. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_avadhi.py`.*

Registry: layer kala, kind data, per-chart, light writer. `ka_avadhi.py:1-17`: for each chart it reads `chart_dashas` MD and AD rows of every dasha system at one ayanamsha (`_CANONICAL_AYANAMSHA = lahiri_chitrapaksha`, `:71`; systems from the service-owned `ALL_DASHA_SYSTEMS`, `:37`) and stores one dossier row per period in `kala_avadhi` (12 columns; natural key `(chart_id, system_id, level_n, period_start)`, `ON CONFLICT` at `:155`). The `dossier` JSON carries `lord_condition_fact_refs` (up to 10 `fact_id` references under `fact_category = 'graha_position'`, references only, `:132`), `activated_pratijna_ids` (up to 10 `bodha_pratijna` ids whose domain is in a hand-written list for the lord, `:40`, `:283`), and for AD rows `sublord_modulation {graha, note}` (`:291`). `quality` is `{domains}` (the same hand list), `citations` is one fixed string, `formula_version = ka_avadhi_v1.0`. The writer refuses with a preserved partition when a system has no MD or no AD rows (`:221`) and replaces only after the whole candidate is assembled (`:323-327`). Served as the per-period dossier by `kala.timeline` / `query_dasha_dossier.ts`.

**Canonical chart (482012f1): `error`.** `kala_avadhi` holds 1,169 canonical rows from the 2026-08-12 generation; `asset_throughput` reads `error` (three runs on 2026-09-10 — `a40c5e9f`, `7cdd60a9`, `474811e3` — each `post-write integrity check failed: integrity_check_sql → False`; the runs rolled back, so 1,169 is the surviving older generation); 19 errors and 9 aborts on record. Stored content is stale against two merged fixes: the I-1 note on 1,043 of the 1,169 rows still reads the swapped roles (rebuild plan section 4.2: example `AD lord Moon modulates MD lord Venus`; the md5 of the ordered notes is `a041ac2f18c66a677e52b168518fec25` today and must differ after) and `lord_condition_fact_refs` is empty on 1,169 of 1,169 (the M4 fix is in the writer, not in the rows). Other charts: 1,160 (Abhinandan) and 1,291 rows. The integrity failure is real on main at the census base (I-7: conjunct (c) fails on every graha-lord row of all three charts, 771/771 canonical, and the rebuild plan finds conjunct (e) false too — 4,129 `activated_pratijna_ids` that do not resolve to `bodha_pratijna` — so the table-wide AND could not turn true on a canonical-only rebuild); the fix is I-8 (PR #2827, migration 1215, branch `suvarna/land/TI-i8-avadhi-integrity-001`, NOT merged at base). A canonical rebuild also adds 262 `chara_karaka` rows (21 MD + 241 AD) that were never stored (the writer moved to the L1 vocabulary in `fa9857f00`). In the rebuild plan (v1.0 numbering): wave 2, after `bo_pratijna`, and only after I-1 is deployed. **The five Kāla tables emptied by the MSR cascade (I-6) do not include this one.**

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2362` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_avadhi.py:175`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_avadhi`; count_sql tables: kala_avadhi | census |
| live rows / floor | 1,169 / 1,169 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `error`; freshness no freshness row; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ga_dashas`, `bo_pratijna`, `bg_ghatana` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 1 / transitive 1 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_taranga` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/retrieval/kala_temporal.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/query_dasha_dossier.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): none | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_dasha_dossier.ts:93` reads `kala_avadhi`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=1169, live=1169, chart 482012f1) — see Build.history |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 474811e3 error/no disposition (2026-09-10) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 474811e3 error/no disposition (2026-09-10) |
| Dens | Dens.served † | FAIL | 1 module(s): query_dasha_dossier.ts; declaring density_contract: 0 |
| Build | Build.history | FAIL | most recent run error (2026-09-10); 19 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-09-10): post-write integrity check failed: integrity_check_sql → False |
| Build | Build.dep_liveness | PARTIAL | 2/3 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_pratijna (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = ["dossier.$.sublord_modulation.note"] (the cells would be measured by a fresh census; the Null check needs the database, so none could be run offline) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Count.floor; Complete.depth; Vocab.identity; Build.exercised.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 2 module(s) reach it by code: L3_kala/query_dasha_dossier.ts, platform-mcp/src/tools/retrieval/kala_temporal.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 3 declared edge(s); exists: all 3 are active registry assets (every layer); cycle: ka_avadhi is on no dependency cycle (registry-wide graph); reads-match: 3 read(s) of other assets' tables, every one covered by a declared edge; 1 chart_facts read(s) satisfied by a producer in the declared transitive closure (ga_condition, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati, ga_sensitive, ga_strength, ga_structural; dag_edge_guard SOFT tier): satisfied…

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_avadhi-Build.completion | Build | real | state `error`: the post-write integrity check fails; cause established in I-7 (table-wide conjuncts + non-canonical stale rows); fix I-8 in flight; verified here against `ka_avadhi.py:323-332` (the writer itself is correct on its own rows) |
| ka_avadhi-Build.history | Build | history | 19 errors, 9 aborts; most recent run error 2026-09-10; no edit changes it (CF-10) |
| ka_avadhi-Build.dep_liveness | Build | stale | `bo_pratijna` stale at the census; a coherent rebuild in level order clears it; not an asset defect |
| ka_avadhi-Dens.served | Dens | Dens rev-1 reading | offline rev-7 reading FAIL (2 modules reach it: `query_dasha_dossier.ts`, `kala_temporal.ts`; no `density_contract`; no tier column on the table, so a contract alone cannot give PASS) |
| ka_avadhi-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05 |
| ka_avadhi-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| ka_avadhi-Carr.detector | Carr | detector | no D1/D2/D3 detector; D3 is available: the integrity conjunct (a) joins every period to `chart_dashas`; CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | `citations` is not in `CITATION_COLUMNS`; CF-08 |
| new: avadhi-N1 | Ldgr / Carr | real | `citations` is the same one-element list on every row of all seven systems (`ka_avadhi.py:306`): "BPHS ch. Vimshottari-Dasha / Classical dasha lord tables", a generic string that names no verse and does not apply to Yogini, Ashtottari, Kalachakra, Mudda, Naisargika or Chara-karaka rows (B.3: no claim rests on 'per tradition' without a source) |
| new: avadhi-N2 | Vocab / Carr | real + SS question | `_GRAHA_DOMAINS` (`:40`) is a hand-written graha → domain table that disagrees with the one `ka_taranga` uses (CF-30); it decides `activated_pratijna_ids` and `quality.domains` |
| new: avadhi-N3 | Narr | real | the docstring says `sublord_modulation: {graha, strength_factor, note} based on the AD lord` (`:15`); the code emits no `strength_factor`, and `graha` carries the parent (MD) lord (`:292`); after I-1 the sentence is right but the role-neutral key names still mislead |
| new: avadhi-N4 | honesty | real | the pratijna and fact-reference reads are SAVEPOINT-guarded and, on failure, log at debug and continue with an empty list (`:247`, `:275`) — an unavailable input is stored as "none" (CF-29; the M4 comment records the same defect at 100% of rows) |
| new: avadhi-N5 | information | information | `activated_pratijna_ids` is cut to 10 in domain-list order, not by grade (`:290`: the query orders by grade, but ids are appended domain by domain); the docstring still states `DAG: ka_yojaka → ka_avadhi` (`:17`), an edge the seed comment says was dropped |
| census: Null/Narr | Null, Narr | detector | declared `prose_fields` = `dossier.$.sublord_modulation.note` (writer line cited in the declaration); no fidelity test measured; CF-25 |

## 3 · Disposition

**keep (P)** — the writer is the careful end of L3: references only for L1 facts (never restated values), a complete-candidate-before-delete discipline, a refusal on incomplete system coverage, an exact spine join to L1 that its own integrity contract re-checks. The open items are one honest provenance gap (FD-1), two ratification questions (FD-1, FD-3), additive role keys (FD-2), and a build-state problem that is already being fixed (I-8). Retained capital with one declared dependent (`ka_taranga`, an edge the writer never reads, CF-23) and real consumers in serving.

Approver under Track A brief §10: **Steward (G16); the output changes in FD-1, FD-3 go to SS (R5)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Honest provenance for `citations` (Ldgr and Carr)

- **Answers:** new avadhi-N1; census Ldgr no reading; CF-08, CF-07
- **Change:** replace the fixed classical string by what each row actually derives from: the period spine is an L1 row, so carry the `chart_dashas.dasha_row_id` of the period (select it in `_FETCH_MD_SQL` / `_FETCH_AD_SQL`, `:73`, `:84`) and the L1 fact ids already cited in `lord_condition_fact_refs`; keep a classical source only per system where one is supplied and verified (no invented citation, B.10); mark rows whose system has no supplied source `unsourced` (the same explicit-state approach as L0 CF-11 / SS Q3, by analogy)
- **Files / declaration / migration:** `ka_avadhi.py:306` and the two fetch SQLs; no migration if the state lives in the `citations` array / `quality` JSON, a migration only if SS wants a column
- **Failing-first test and mutation:** Failing-first: for each stored system the row carries the L1 `dasha_row_id` of its period and no row carries the old generic string; a Yogini row without a supplied source reads `unsourced`; mutation: restore the constant → fails.
- **Output change:** yes — the `citations` array of every row (and `quality` if the state lives there) → SS (R5)
- **Blast radius:** served and passed through by `query_dasha_dossier.ts:93` (`SELECT … citations …`) and the `kala.timeline` timeline excerpt in `kala_temporal.ts`; no python writer reads `kala_avadhi` (grep); a consumer that parses the old string is not traced and is not expected
- **Rebuild:** needs production rebuild of `ka_avadhi` (already planned in wave 2 for I-1/M4/I-8; the output change should ride that single run, which is why SS should decide before it)
- **Gate it moves:** Ldgr (no reading → PASS/FAIL), Carr
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined); the `dasha_row_id` reference itself is tier-independent

### FD-2 · Role-named dossier keys (additive) and the stale docstring

- **Answers:** new avadhi-N3; CF-25
- **Change:** add `md_lord` and `ad_lord` beside `graha` in `sublord_modulation` (keep `graha` as it is for readers), correct the docstring (`:15`) and either compute `strength_factor` from an L1 fact (output) or drop it from the docstring (no output); extend the I-1 test to assert both roles from a fixture
- **Files / declaration / migration:** `ka_avadhi.py:291-294`; `tests/l3/test_ti_i1_avadhi_sublord_roles.py`
- **Failing-first test and mutation:** Failing-first: an AD fixture row with MD lord Venus and AD lord Moon stores `md_lord = Venus`, `ad_lord = Moon`, note `AD lord Moon modulates MD lord Venus`; mutation: swap the arguments → fails.
- **Output change:** additive JSON keys (no existing key changes meaning)
- **Blast radius:** `dossier` JSON served as is by `query_dasha_dossier.ts:88-92`; consumers that ignore unknown keys are unaffected (not verified for every consumer)
- **Rebuild:** rides the planned rebuild; no separate run
- **Gate it moves:** Narr (golden test)
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · One authority for the graha → domain map (and a visible truncation order)

- **Answers:** new avadhi-N2, N5; CF-30
- **Change:** replace the local table (`:40`) by the single authority SS names (CF-30); order the 10-id cut by grade then `pratijna_id` across domains (`:290`) so the cut keeps the strongest, deterministically
- **Files / declaration / migration:** `ka_avadhi.py:40-50`, `:283-290`
- **Failing-first test and mutation:** Failing-first: a fixture with 12 matching pratijnas keeps the ten with the highest grade; two row orders give the same ten; mutation: restore domain-list order → fails.
- **Output change:** yes — `activated_pratijna_ids` and `quality.domains` may change → SS (R5)
- **Blast radius:** same consumers as FD-1; `bodha_pratijna` ids are read, never written
- **Rebuild:** rides the planned rebuild
- **Gate it moves:** Vocab / Carr
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-dependent for the choice of authority (SS); the ordering is tier-independent

### FD-4 · Say when an input was unavailable (additive)

- **Answers:** new avadhi-N4; CF-29
- **Change:** when the pratijna read or a lord's fact-reference read is skipped (`:247`, `:275`) record `dossier.inputs_unavailable = [...]` and count the skips in the `WriterResult` notes, instead of an empty list that reads as "none"
- **Files / declaration / migration:** `ka_avadhi.py:229-276`
- **Failing-first test and mutation:** Failing-first: with the pratijna table missing the rows carry `inputs_unavailable = [pratijna]`; with it present the key is absent; mutation: swallow silently → fails.
- **Output change:** additive key
- **Blast radius:** none beyond FD-2 readers
- **Rebuild:** rides the planned rebuild
- **Gate it moves:** honesty (no census criterion)
- **Fix class:** writer code; **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

- **I-1 (MD/AD roles) — merged, PR #2823 (`066c58587`, the base of this lane).** `ka_avadhi.py:293` now reads `AD lord {lord} modulates MD lord {sublord}`; stored rows keep the swapped sentence until the asset is rebuilt (canary SQL and md5 in rebuild plan section 4.2).
- **I-7 / I-8 (integrity check) — PR #2827 (migration 1215) NOT merged at base.** Scopes conjuncts (a)-(e) to the canonical chart, replaces `'chara'` by `'chara_karaka'` in conjunct (b), adds the non-vacuity conjunct (f). Disclosed trade-off: Abhinandan and `cb73cd3d` stop being measured by this check until their own rebuild.
- **M4 (lord fact refs) — in the writer since `97fd08e1c`**, not yet in the 1,169 stored rows.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* floor 1,169 becomes 1,431 after the first canonical rebuild (1,169 + 262 `chara_karaka` rows, I-7); informational, refresh after the rebuild
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL; no tier column on the table, so `uniform_authority` or a real tier is the question (see FD list in INDEX)
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument absent
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3: reuse integrity conjunct (a), the join of every period to `chart_dashas`
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* `citations` unrecognised; FD-1
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 19 errors / 9 aborts
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* the declared dependent `ka_taranga` never reads this table; removing that edge takes the declared radius 1 → 0
- **CF-25** — Narr fidelity (golden-value) tests per L3 narration writer. *This asset:* golden test for the `note` sentence (the I-1 test is the seed)
- **CF-29** — Honest absence versus unavailable: swallowed detector failures, proxy fallbacks and soft reads that degrade to empty. *This asset:* FD-4
- **CF-30** — Duplicated hand-written reference tables in L3 writers (graha -> domain, natural malefics, combustion orbs, Rikta set). *This asset:* FD-3
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* this asset is the I-7/I-8 model case: its table-wide check was the one that failed

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, system_id, level_n, period_start)` (DB UNIQUE; census `Vocab.identity` 0 duplicates). Volatile columns excluded: `avadhi_id` (surrogate), `computed_at`. `dossier` content is deterministic given L1 facts and the pratijna set; the `fact_id` / `pratijna_id` values inside it are references whose stability depends on L1/L2 identity: compare them normalised to `(fact_subject, fact_key)` and `(event_class_id)` if an upstream rebuild regenerates ids (not established). Rebuild expectation: 1,169 → 1,431 rows once (the 262 `chara_karaka` rows), otherwise identical period columns (integrity conjunct (a)).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the L1-inherited period spine, the references-only discipline for facts, the refusal on incomplete system coverage, the replace-after-assembly order.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation): every served period equals a `chart_dashas` row on (system, level, start, end, lord) at the canonical ayanamsha — the existing integrity conjunct (a) registered as the detector, run on a stratified sample for the cell.
- **Opportunities (never blocking):** the dossier carries references only; resolving the cited L1 facts into a displayed lord condition at query time (a serving opportunity, not a gate); `strength_factor` if an L1 strength fact is to be cited.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L3-02** — FD-1: is a per-row `attribution_state` (or the L1 `dasha_row_id` as the spine source) acceptable in place of the generic classical string, and who supplies verified per-system sources?
- **Q-L3-04** — FD-3 / CF-30: which graha → domain table is canonical?

**Track I items arising (see INDEX section 10):** TI-L3-10, TI-L3-11, TI-L3-14, TI-L3-15, TI-L3-16.
