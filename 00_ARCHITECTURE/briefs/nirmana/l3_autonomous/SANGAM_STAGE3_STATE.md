---
artifact: SANGAM_STAGE3_STATE
canonical_id: SANGAM_STAGE3_STATE
version: "1.0"
status: IN_PROGRESS
layer: L3
asset: ka_sangam
campaign_id: sangam-stage3
branch: sangam/stage3 (off origin/l3/kala-elevation-readiness)
maintained_by: "Saṅgam stage-3 executor (Kimi Code session)"
resumes_from: "Re-paste SANGAM_STAGE3_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md into a fresh session in /Users/Dev/madhav-l3/readiness"
---

# Saṅgam stage-3 — durable state

## Phase status

| Phase | Status | Exit evidence |
|---|---|---|
| 0 — Entry gate | **PASSED 2026-09-23** | (a) packet read in order; (b) D-8 discharged — Astra third review `ASTRA_REVIEW_SANGAM_ALGO_PLAN_v1_0.md` = PROCEED_WITH_AMENDMENTS, RRV-01…09 dispositioned in plan §10 + brief changelog + inline [S3-E] amendments; (c) evidence suite re-run `OUTPUT_2026-09-23T050513.txt` SUITE-PASS 13/13 + 13/13 NEG (4 scripts spot-verified by hand, exit 1 under NEG=1); reviewer independently re-ran + mutation-tested (`OUTPUT_2026-09-23T051310.txt`); (d) DB reachable via Cloud SQL proxy **127.0.0.1:5434** (5433 down; `source /Users/Dev/madhav-l3/dbenv.sh`); D-6 staged SQL executed, 100 chunks read, no nodal aspect grant — recorded in DIS.031 `amendment_2026_09_23_predicate_level_recheck` (ground upgraded ATTRIBUTED→CONFIRMED, OCR/400-char limits stated). |
| 1 — R-5 harness | **PASSED 2026-09-23** | Identity D-R5-1 implemented (`r5_identity.py`: contact_uuid uuid5 over the 8-field tuple with peak_date deliberately excluded; episode_uuid over sorted-member set-hash; FIELD_EXCLUSIONS = surrogate id / computed_at / generation-head pointers, named in code at :38-43). Five-rule rebuild/mapping (no-op / supersede / decisive-geometry-reattach / **ambiguous fail-closed** / explicit-withdrawal-only) with journal + replay, in a schema-faithful SQLite mirror of the §5.2 cascade graph (245/247 CASCADE, 249 SET NULL, 363 CASCADE, 334 CASCADE, 331/332 SET NULL, 339 FK-free resolved semantically). Seven §6.3 attacks executable (40 assertions, VERDICT PASS): empty rebuild, moved date (identity stable, content v+1), one-to-many split, many-to-one merge, ambiguous match (no auto-reattach; adjudicated re-run reattaches exactly then), interrupted/resumed (byte-identical manifest, exactly-once), unchanged-count content-swap (per-id canonical diff fires). S14 joined the manifest (`r5_harness/S14_r5_preservation_harness.py\|0\|1`); suite re-run `OUTPUT_2026-09-23T060527.txt` SUITE-PASS 14/14 + 14/14 NEG; NEG mutation = `FAIL_CLOSED_AMBIGUOUS` flipped to False (evidence-bearing: six attack-5 propositions read false on a genuinely re-attached DB). |
| 2 — R-1…R-4, R-6 | **IN PROGRESS** — R-6, R-1, R-3(b), R-4 PASSED 2026-09-23; R-2 remains | see "Phase 2 progress" below |
| 3 — E2, E5 | NOT STARTED | — |
| 4 — E4 + annual-Tājika gate | NOT STARTED | — |
| 5 — E6 (E3 gated on N-7) | NOT STARTED | — |

## Binding pins added at the gate (D-8 dispositions — plan §10)

- RRV-03: within-class ordering key per `comparability_class` = `activity DESC, contact instant ASC`; valence/applicability/availability carried as data, never pooled; SQL-level partitioning enforcement.
- RRV-05/06: taranga unit = occupied-day union per month per (contract × valence-sign), month boundary = chart birth tz; aborted approaches = labelled children. E6 numerator inclusion of aborted approaches NOT ruled — recorded open, native to settle before E6 numerator definition; until then excluded, convention stated on output.
- RRV-08: static daśā prior → `availability.dasha = unavailable`, zero manufactured support.
- RRV-01: E2 receipt computed stage-3-side via L1 chart_facts join (fabricated_zero vs measured_zero); L1-producer column amendment routed as L1-owner packet (follow-up, not blocker).
- RRV-02: step-3 scanner-dependent detector SPECs gate on N-7 like E1/E3; scanner-independent scope proceeds.
- RRV-09: §6.3 canonical serialization with field-exclusion list; schema-faithful disposable DB; dependent map += mimamsa_convergence_adjustment, mi_adhilepa.
- RRV-04: consumer set += mi_adhilepa, ph_nimitta (+UNRESOLVED_USE "disclose or bind" first pass at Phase 2 exit).
- RRV-13/14/15/16: carried — RRV-13 pins at Phase 5; RRV-14 authored with the event-consumption interface; RRV-15 permanent review discipline; RRV-16 inline at §0R M-1.

## Open blockers (with unblock conditions)

| # | Blocker | Unblock condition | Owner |
|---|---|---|---|
| B-1 | N-7 unruled → E1/E3 gated; R-3/R-4 scanner-dependent SPECs gated | Native rules N-7 on the Gochara brief, or names the Path-A `transit_search` amendment owner | Native / Gochara stream |
| B-2 | Path-A owner unnamed (K3 Q9#1) | Native names the owner | Native |
| B-3 | Aborted-approach E6 numerator question unruled | Native answers (Kimi leans yes as `perfected: false`) | Native |
| B-4 | E2 producer-column receipt at ga_strength_writer | L1-owner bounded packet (receipt columns only) | L1 owner |
| B-5 | ephemeris_daily node-frame undeclared contract (§11.1) | L0 owner repair (outside this campaign's scope) | L0 owner |

## Fences in force (from the prompt §3/§6 — restated so no session re-derives them)

Frozen orchestrator · delete-then-insert per chart × natural key · cascade proof before first destructive rebuild (migration 363 phala_anchors CASCADE; 403 kala_* cascade) · no fabricated values · L1 authority (§N.5) · no post-apply migration edits · floors from achieved counts · E1/E3 (and scanner-dependent R-3/R-4 SPECs) gated on N-7 · D30 falsifier-first (contract pinned, MANIFEST entry with NEG control passing, BEFORE first D30 row) · no Kshetra/Gochara/transit_search edits, never remove w30_modifier · never trigger ka_gochara_v3_century_materialize.

## Decisions taken (executor-scope, this campaign)

- D-8 disposition mechanism: in-place [S3-E] amendments + plan §10 + brief changelog correction, matching the packet's own [AMENDED …] idiom. Rationale: review demanded disposition "in the plan/brief text"; separate artifact would not satisfy the gate condition.
- DB path: 5434 proxy is the same amjis database the 5433 MCP config points at; recording 5433 outage noted, 5434 used read-only (PGOPTIONS read-only in dbenv.sh).
- Ruling-vs-plan discrepancies RRV-05/06: ruling sheet resolution table is the binding document; plan text amended, discrepancy recorded (not smoothed, not re-opened — §2 hierarchy).

## Phase 1 — R-5 identity design (executor decision D-R5-1, binding for the harness and later production code)

**Harness ratifications (2026-09-23, executor):** (i) manifest line carries the `r5_harness/` path — correct, since RUN_ALL checks the path relative to evidence_sangam/; (ii) geometry-match rule 3 additionally requires same chart_id and method_contract_version (cross-chart/contract matches are never the same testimony) — adopted; (iii) split/merge/adjudicated reattachments are declared inputs (authorized successor) to the rebuild — matches the attack specs; (iv) split children must differ in an identity field (orb), since peak-only differences collide on contact_uuid by design — a design property, exercised as such; (v) attack 7's load-bearing property is the per-id canonical comparison, not any aggregate hash.

**Design:**

**Contact identity** `contact_uuid` = UUIDv5 over the canonical tuple
`(chart_id, method_contract_version, graha, target_fact_id, directed_angle_deg, frame_vector, orb_deg, contact_kind)`:
- `target_fact_id` = the L1 `chart_facts.fact_id` the target is bound to (R-1: provenance, never a longitude; unresolvable target → `unavailable`, no row, no identity).
- `frame_vector` = `(ayanamsha_id, ephemeris_backend, epoch_convention, ayanamsa_application, node_convention, house_frame)` — R-3's convention vector; two frames never coalesce.
- `contact_kind` ∈ {exact_contact, sign_interval, ingress}.
- **Deliberately excluded:** peak_date, interval start/end, orb shoulders — algorithm-versioned *content*, not identity. A peak move within one `method_contract_version` = same identity, new content version + supersession edge. A contract-version change = new identity family; old rows carried as legacy, never pooled.

**Episode identity** `episode_uuid` = UUIDv5 over `(chart_id, method_contract_version, graha, target_fact_id, directed_angle_deg, frame_vector, set_hash(sorted member contact_uuids))` — deterministic, rebuild-stable when membership is unchanged; membership changes produce split/merge edges from the old episode.

**Claim attachment**: dependent claims bind to `contact_uuid` (natural, stable), never the surrogate `convergence_id` — mi_adhilepa's surrogate binding (RRV-04) is the defect this removes; production migration resolves existing bindings semantically via the manifest *before* any key change (D-7's condition).

**Rebuild/mapping (candidate generation)** — five rules:
1. Candidate uuid + identical content-hash → keep (no-op).
2. Candidate uuid + different content → supersede: new content version, supersession edge, claims re-point via the same uuid (successor = self, version+1).
3. New candidate, no uuid match → geometry match against unmatched originals (same target fact, angle, frame, overlapping orb). Exactly one decisive match → reattach + supersession edge. Zero or >1 plausible → **AMBIGUOUS: original retained, claim NOT reattached (fail-closed), flagged `ambiguous_needs_adjudication`** — never silently re-pointed.
4. Original with no candidate successor and no explicit withdrawal → retained (nothing deletes implicitly). Explicit withdrawal (e.g. invalidated geometry like a defaulted-0° target) → withdrawn with recorded reason; claims mapped only to an authorized successor, else flagged.
5. Interrupted/resume: mapping decisions journaled; resume replays the journal; assertions prove exactly-once effects.

**Manifest (§6.3 + RRV-09)**: keyed by stable id. Per id: canonical serialization of full claim content with explicit field-exclusion list (surrogate row id, `computed_at`, generation-head pointers; JSONB sorted-keys framing), version, exposure; outcome bytes (`outcome_recorded`/`outcome_notes` verbatim); every dependent binding resolved semantically incl. FK-free `top_anchor_id`; successor mappings. Comparison = exact content per id, never counts/hashes of unframed content. Every rebuild declares its expected delta.

## Phase 2 progress

### R-6 score-kernel separation — PASSED 2026-09-23 (first repair landed, engine-side)

**Design pins applied (plan §3 R-6 + M-7 + ASTRA [S3-E] RRV-03/RRV-08):**
- `engine.py` gains `separate_kernel` (modes A/B: I-16 form minus dignity — activity = Π(orb presence, vedha modulator) × saturating support, valence = 2·dignity−1, applicability F06-per-method, availability stance vocabulary), `separate_kernel_sign_level` (modes C/D: severity / SAV fraction IS the activity — these routes have no supporting combinator, so the saturating form would multiply real intensity to 0), and `ordering_key` (RRV-03: `(comparability_class, −activity, contact instant)` — activity DESC, contact ASC, valence/applicability/availability carried as data, never pooled).
- Dignity LEAVES the necessary product on the new path; the legacy `convergence_score` (dignity inside) is computed and carried UNCHANGED on every new window, labelled `kernel_version='separated_v2'` (`legacy_i16` reserved for pre-R-6 rows) — coexistence by labelling, never re-derived from the four fields.
- RRV-08: `_dasha_score_for_date` now reports its source; a static-fallback score (no service / query failed / no covering window) is an availability state — `availability['dasha']='unavailable'`, `applicability['constituent_lord_transit']=False`, term OMITTED from kernel support (zero manufactured support). Mode B's structural zeros likewise recorded absent. C11 vedha unavailability recorded `availability['vedha']='unavailable'` + `applicability['vedha_cancellation']=False` — not folded into a silent neutral 1.0 (legacy factor still reported in constituent_factors for the legacy reading).
- All four mode sorts move from `convergence_score DESC` to `ordering_key` — within one call dignity is a per-predicate constant, so relative order is preserved (ties gain the deterministic contact-ASC tiebreak).

**Qualification:** `tests/l3/test_ka_sangam_r6_kernel.py` — 15 tests, all fixtures from SPEC R-6 + ASTRA §B/R-6: dignity-0 intensely active (activity>0, valence −1.0, legacy 0.0); legacy reconstruction cross-check; no-service dasha unavailable + no manufactured support (reconstructed-activity equality, abs 1e-4); covering-window dasha computed; ordering key (DESC/ASC, opposite-valence page-cut survival, class partitioning, determinism under shuffle); vedha unavailable ≠ neutral; mode C/D kernel fields + sort. Run: 98 passed (15 new + 83 existing sangam/convergence) — `venv/bin/python -m pytest tests/l3/test_ka_sangam_r6_kernel.py tests/l3/test_ka_sangam.py tests/l3/test_l3_convergence.py -q`. Full `tests/l3` (minus ka_kshetra): 1062 passed, 2 failed — BOTH pre-existing test-pollution flakes, verified identical on the pristine tree (git stash A/B): `test_m3_graha_sancara_defects.py::test_the_forensic_anchor_actually_holds_on_that_path` (passes in isolation) and `test_transit_search_cache.py::test_cached_call_matches_direct_swe_calc_ut`.
**Evidence:** `S15_r6_kernel_adverse_visible.py` joined MANIFEST (`|0|1`); suite `OUTPUT_2026-09-23T120120.txt` SUITE-PASS 15/15 + 15/15 NEG; NEG mutant = a "separated" kernel that secretly keeps dignity in the product and reports valence 0.0 (all nine propositions read false under it).
**Scope note:** engine-side fields only; writer persistence of the new columns and consumer SQL partitioning (RRV-03 enforcement vehicle) ride with the Phase-2 contact-changing cluster + consumer work, not this increment.

### R-1 target binding, R-3(b) fail-loud lagna, R-4 withdrawals — PASSED 2026-09-23

**R-1 (RR-03) target provenance:**
- Writer (`pipeline/orchestrator/writers/ka_sangam.py`) is now the ONLY place target defaulting is allowed: `_fetch_target_fact_cache` reads L1 `chart_facts` (graha_position/longitude_sidereal + bhava_cusps/sripati_madhya, ayanamsha `lahiri_chitrapaksha`); `_enrich_predicate_target` stamps each predicate's `transit_trigger_jsonb` with sourced `target_longitude_deg` + provenance (`target_fact_id`, `target_type`, `frame`, `ayanamsha_id`, `derivation`). Coverage: DIGNITY → the graha's own natal sidereal longitude; DISPOSITOR_RELATIONAL → the house cusp longitude (new `house_num` enrichment field); YOGA → first resolvable constituent lord (declared partial target). All other classes return None — the engine then refuses the scan.
- Engine (`services/ka_sangam/engine.py`): a trigger with NEITHER `target_longitude_deg` (key presence) NOR writer-stamped provenance is unresolvable — `mode_a_search`/`mode_b_sweep` log a warning naming signal_id and return `[]` (no Aries-point default scan). A present key with value 0.0 remains valid (sourced 0°). Sourced provenance is copied into each window's `constituent_factors['target_provenance']` and `availability['target']='computed'`; otherwise `'unavailable'`.
- Writer TRIGGER suppression (`apply_trigger_suppression`) now takes `target_lon=None` when unresolved and is skipped — no silent 0.0 mechanism longitude.
- Persistence: additive-only migration `1071_kala_convergence_target_provenance.sql` adds `kala_convergence.target_provenance JSONB` + `kala_convergence.availability JSONB` (IF NOT EXISTS, comments only — no existing column/table touched).

**R-3(b) (CR-87 lagna read):** `_build_house_lord_map` is fail-loud — any missing lagna row (query now also pins `ayanamsha_id='lahiri_chitrapaksha'`) or unrecognised sign name raises RuntimeError; the `lagna_sign = 'Aries'` default assignment and its fallback docstring are removed.

**R-4 (RR-06) C9/C4 withdrawal:** `benefic_dristi` and `transit_to_transit` are removed from the scored supporting dict in modes A and B (legacy I-16 and R-6 kernel alike). `SUPPORTING_WEIGHTS` is intentionally NOT renormalised — the combiner iterates all declared weights, so withdrawn mass is inert (`sup.get(key, 0.0)`), never redistributed. Measured values stay in `constituent_factors` as lineage (`c_benefic_dristi`, `c9_transit_to_transit`) with `_withdrawn` reason keys stating why no qualified classical method binds them; applicability records both as False.

**Qualification:**
- `tests/l3/test_ka_sangam_r1_r4_repairs.py` (new, 11 tests): mode B refuses unresolvable target; provenance/availability stamping; applicability False for withdrawn terms + lineage keys present; writer resolution for DIGNITY/DISPOSITOR/YOGA/unresolvable; enrichment stamps provenance; lagna fail-loud on missing row and invalid sign.
- Existing pins updated to the new contract (verified as post-fix updates, not silent re-pins): `test_ka_sangam_a3_fixes.py` domain-param index 16 after the two new INSERT columns; `test_ka_sangam_r6_kernel.py` legacy/kernel reconstructions exclude withdrawn terms.
- Runs: `test_ka_sangam_r1_r4_repairs.py + test_ka_sangam_r6_kernel.py + test_ka_sangam_a3_fixes.py` = 58 passed; `test_ka_sangam.py + test_l3_convergence.py` = 83 passed; full `tests/l3` minus ka_kshetra: **1088 passed, 2 failed — both the known pre-existing pollution flakes** (`test_m3_graha_sancara_defects` forensic anchor, `test_transit_search_cache` cached-call parity), identical to pristine-tree baseline.
- **Evidence:** `S1_target_default_zero.py` and `S12_lagna_default_aries.py` rewritten as POST-FIX detectors (positive = guard exists, negative control removes the guard); `S16_r1_r4_post_fix.py` joined MANIFEST. Suite `OUTPUT_2026-09-23T130106.txt` SUITE-PASS 16/16 positive + 16/16 negative controls.
- Executor independently re-reviewed every diff (engine combiner math — withdrawn weights inert not renormalised; migration additive-only; test edits legitimate) before accepting the subagent's implementation.

## Last commit

`656369bda` — "sangam stage3: Phase 2a — R-6 score-kernel separation landed engine-side".

## Evidence artifacts this phase

- `evidence_sangam/OUTPUT_2026-09-23T050513.txt` (executor run) · `OUTPUT_2026-09-23T051310.txt` (reviewer run)
- `ASTRA_REVIEW_SANGAM_ALGO_PLAN_v1_0.md` (D-8 gate output)
- DIS.031 `amendment_2026_09_23_predicate_level_recheck` (D-6 corpus ground)
- /tmp/d6_node_drishti_recheck.txt (raw SQL output, 100 rows; regenerable from the staged SQL)
