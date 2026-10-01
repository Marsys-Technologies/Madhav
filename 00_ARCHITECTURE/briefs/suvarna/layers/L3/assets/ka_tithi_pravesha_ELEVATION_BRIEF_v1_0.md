---
asset_id: ka_tithi_pravesha
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
disposition_proposal_approver: "Steward (G16); the definition question (Q-L3-14) is an acharya/SS ruling, not a tier clause"
decisions_applied: "none specific to L3 yet; L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-09, TI-L3-10, TI-L3-20, TI-L3-25]
ledger_gap_ids: ["ka_tithi_pravesha-Earn.build_record", "ka_tithi_pravesha-Cost.baseline", "ka_tithi_pravesha-Dens.served", "ka_tithi_pravesha-Build.history", "ka_tithi_pravesha-Carr.detector", "new: tithi-N1", "new: tithi-N2"]
---

# ka_tithi_pravesha — Tithi-Praveśa annual chart per year of life: lunar-return instant, annual chart and a verification state

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in `INDEX.md` section 9. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/services/ka_tithi_pravesha/writer.py`.*

`services/ka_tithi_pravesha/writer.py` (+ `logic.py`): reads the natal Moon's sidereal longitude from L1 (`graha_position`, `longitude_sidereal`; the same fact `ka_moorti_nirnaya` reads), and for each of 120 praveśa years (`DEFAULT_MAX_PRAVESHA_YEAR`, `logic.py:82`) finds by two-stage root-finding the instant the transiting Moon returns to that exact natal longitude nearest the solar-birthday anniversary, casts the annual chart for that instant with the L1 engine (`pyjhora_adapter`, the engine `ga_tajaka` uses for the solar-return chart), and stores the window (this return to the next), the praveśa lagna, the nine-graha positions as a JSON composite, the root-find audit (`ephemeris_audit_jsonb`), `natal_moon_longitude_deg`, `moon_fact_id`, and a verification state. The earned signal is the model for L3: `verification_pass_status = 'two_pass_verified'` exactly when the root-find converged AND the annual chart's own Moon longitude equals natal within `LUNAR_RETURN_TOL_DEG = 0.01` (`:208`), else `divergent_flagged`; the registry integrity contract re-derives the status from the stored audit in both directions (migration 670, conjuncts (b)-(c)). The citation is honest: `classical_source_citation = 'not_in_corpus'` on every row (`:65`). Replace-after-assembly; served by `query_tithi_pravesha.ts:91` and the `now` view.

**Canonical chart: `lit`, fresh, 120 rows.** Registry state: throughput `lit`, freshness `fresh`, spec present; latest run `8d74930c` complete/skip_no_delta 2026-09-07; 3 errors and 3 aborts (latest error 2026-08-08, `KeyError: 1`, fixed). Floor 120 = live 120. This is the leaf asset the canonical-chart rebuild plan uses for its smoke build (S0): nothing depends on it, so no downstream asset can be marked stale. Nirmāṇa-frozen under t0 (2026-09-07).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2558` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/services/ka_tithi_pravesha/writer.py:234`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_tithi_pravesha`; count_sql tables: kala_tithi_pravesha | census |
| live rows / floor | 120 / 120 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `lit`; freshness `fresh`; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ga_positions` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 0 / transitive 0 (census blocking_radius, every layer); named (REG 2026-09-30): none | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/kala_views/now.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/query_tithi_pravesha.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `services/gochara_v3/mechanisms/w27_annual_stack.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_tithi_pravesha.ts:91` reads `kala_tithi_pravesha`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t0, 2026-09-07 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8d74930c complete/skip_no_delta (2026-09-07) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8d74930c complete/skip_no_delta (2026-09-07) |
| Dens | Dens.served † | FAIL | 1 module(s): query_tithi_pravesha.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 3 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-08): KeyError: 1 Traceback (most recent call last):   File "/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/pipeline/orchestrator/asset_runner.py", line 562, in _run_data_writer     rows_inserte |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Build.exercised; Build.dep_liveness.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 2 module(s) reach it by code: L3_kala/query_tithi_pravesha.ts, platform-mcp/src/tools/kala_views/now.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract; a tier column is selected without a contract in: L3_kala/query_tithi_pravesha.ts

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 1 declared edge(s); exists: all 1 are active registry assets (every layer); cycle: ka_tithi_pravesha is on no dependency cycle (registry-wide graph); reads-match: 1 read(s) of other assets' tables, every one covered by a declared edge; static scan of 34 code unit(s), 2 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_tithi_pravesha-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL: "a tier column is selected without a contract" (`verification_pass_status`) — the contract plus tier route to PASS (CF-04) |
| ka_tithi_pravesha-Build.history | Build | history | 3 errors, 3 aborts; latest 2026-08-08 `KeyError: 1` (fixed); CF-10 |
| ka_tithi_pravesha-Earn.build_record | Earn | detector | CF-05; the `verification_pass_status` claim already has a real detector (the integrity contract) |
| ka_tithi_pravesha-Cost.baseline | Cost | information | CF-05 |
| ka_tithi_pravesha-Carr.detector | Carr | detector | D3: re-find a sampled return instant by root-finding on the stored positions; the status re-derivation is the existing check (CF-07) |
| census: Ldgr (no reading) | Ldgr | detector | `classical_source_citation` not in `CITATION_COLUMNS` (CF-08); its value `not_in_corpus` is an honest absence, which a presence-based cell would misread as populated |
| new: tithi-N1 | honesty | real or not (acharya question) | definition: the registry item and the module call it Tithi-Praveśa, but the module defines it (`logic.py:7-20`) as the Moon's return to its natal sidereal LONGITUDE nearest the solar birthday — a lunar return — from "established Jyotiṣa doctrine per the CLAUDECODE task brief's explicit framing" and the glossary entry "Tithi-Praveśa (annual lunar-return chart)" of `KALA_TRANSFORMATION_HANDOFF_v1_0.md`; it states that no spec document beyond the one-line registry item exists. A return to the natal Moon LONGITUDE is a lunar return; by its name a tithi return would be the recurrence of the birth tithi (Sun–Moon elongation), a different instant. That reading is an inference from the name and is not verified against a primary source in this lane; the cited honesty (`not_in_corpus`) is the right posture, and the question is whether the name matches the computation |
| new: tithi-N2 | Carr | information | the two passes of `two_pass_verified` both call `pyjhora_adapter` (the root-find through `_moon_longitude` and the annual chart through `_annual_chart`, `:25`): an internal-consistency check, not an independent derivation (the registry contract states it as a re-derivation of the status from the audit, which is what it is) |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null: stores a sign name from `reference_signs`, positions and audit numbers, no composed text; proposed `[]`; CF-06 |

## 3 · Disposition

**keep (P)** — the asset the others should look like: L1 fact by id, an earned verification state with a detector that can read false, an honest `not_in_corpus`. The only substantive item is whether the technique is named correctly (an acharya question, not a defect of the build).

Approver under Track A brief §10: **Steward (G16); the definition question (Q-L3-14) is an acharya/SS ruling, not a tier clause**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Settle the definition and the name

- **Answers:** new tithi-N1
- **Change:** an acharya or SS ruling on whether the asset should compute the birth-tithi recurrence, keep the lunar-return definition and rename (`lunar_return_annual`), or keep both as separate labelled series; whichever is chosen, the registry description, the served tool text and the module header must say the same thing
- **Files / declaration / migration:** registry description, `query_tithi_pravesha.ts` descriptor text, `logic.py` header (no code change if only the label moves)
- **Failing-first test and mutation:** Failing-first: a golden fixture for the chosen definition (a known tithi return for the canonical natal data computed by hand); mutation: perturb the anchor → fails.
- **Output change:** a rename is text only; computing the tithi recurrence would change all 120 windows → SS (R5)
- **Blast radius:** served as the Tithi-Praveśa view (`query_tithi_pravesha.ts`, `kala_views/now.ts`); `gochara_v3/mechanisms/w27_annual_stack.py` reads the table by name (Pravāha-owned code: notify before any change); no registry dependents (leaf)
- **Rebuild:** a rename: none; a recomputation: needs production rebuild (REVIEW for SS)
- **Gate it moves:** Carr / honesty
- **Fix class:** registry/declaration (rename) or writer code (+ SS/acharya ruling); **buildable before J1:** tier-independent

### FD-2 · Declare carriage and prose

- **Answers:** census Ldgr (no reading), Null/Narr; CF-06, CF-08
- **Change:** `carriage` declaration naming `classical_source_citation` as the source column with value `not_in_corpus` as a declared honest absence, and `moon_fact_id` as the L1 anchor; `prose_fields: []` with evidence `writer.py`
- **Files / declaration / migration:** `asset_declarations.json`
- **Failing-first test and mutation:** inspector Ldgr reads the declared column and does not count `not_in_corpus` as sourced; declarations validation
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Ldgr, Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01

### FD-3 · Carr detector: independent return-instant check

- **Answers:** census Carr; CF-07 and new tithi-N2
- **Change:** D3: for a sample of years, find the return instant by root-finding on the stored graha positions or on a second ephemeris read (different flags) and compare to `window_start` within the tolerance; keep the existing status re-derivation as the D2 check
- **Files / declaration / migration:** detector (Track E); `tests/l3/test_ka_tithi_pravesha.py`
- **Failing-first test and mutation:** Failing-first: a seeded perturbed instant is reported; zero on the real rows; mutation: shift one `window_start` by a day → count ≥ 1.
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02

### Landed or in flight (not designs of this lane)

No Track I item touches this asset. It is the smoke-build leaf of the canonical-chart rebuild plan (S0).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL with a tier column: the contract plus tier route to PASS
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 + the existing D2
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* `classical_source_citation`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 3 / 3
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* table-wide `integrity_check_sql` (audit; none measured false)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, pravesha_year)` (DB UNIQUE). Volatile columns excluded: `id`, `computed_at`. `window_start`/`window_end` are timestamps from a root-find (stable to the convergence tolerance, 0.01° ≈ 1.1 minutes of Moon motion): compare within a tolerance, not byte-for-byte; `ephemeris_audit_jsonb` carries iteration details that may vary in the last digits. No as-of dependence. Rebuild expectation: 120 rows, same lagna signs, windows equal within tolerance.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the L1 anchor by fact id, the two-stage root-find (a documented fix for the wrap-discontinuity trap), the earned verification state and its re-derivation contract, `not_in_corpus`.
- **Carriage check chosen (T4 §4.1; one only):** D3: re-find sampled return instants independently (root-finding on stored positions or a second ephemeris read); the existing integrity conjuncts (b)-(d) are the D2 re-derivation of status and anchor.
- **Opportunities (never blocking):** the full Tājika apparatus is out of scope by declaration (owned by `ga_tajaka`); a second series for the birth-tithi recurrence if SS rules both.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L3-14** — FD-1: does the asset compute Tithi-Praveśa (birth-tithi recurrence) or a lunar return; rename, recompute, or both?

**Track I items arising (see INDEX section 10):** TI-L3-09, TI-L3-10, TI-L3-20, TI-L3-25.
