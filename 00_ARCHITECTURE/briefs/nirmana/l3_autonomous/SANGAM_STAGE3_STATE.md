---
artifact: SANGAM_STAGE3_STATE
canonical_id: SANGAM_STAGE3_STATE
version: "1.0"
status: COMPLETE
layer: L3
asset: ka_sangam
campaign_id: sangam-stage3
branch: sangam/stage3 (off origin/l3/kala-elevation-readiness)
maintained_by: "Saṅgam stage-3 executor (Kimi Code session)"
resumes_from: "Re-paste SANGAM_STAGE3_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md into a fresh session in /Users/Dev/madhav-l3/readiness"
---

# Saṅgam stage-3 — durable state

**Campaign status: COMPLETE 2026-09-23.** Phases 0–5 all PASSED with detector-backed evidence (final suite 20/20 positive + 20/20 negative controls, `OUTPUT_2026-09-23T192333.txt`). E1/E3 remain gated on N-7 by design (blocker B-1) — that gate is part of the plan, not an unmet exit. Open blockers B-1…B-6 stand below with their unblock conditions; none belongs to this campaign's scope.

## Phase status

| Phase | Status | Exit evidence |
|---|---|---|
| 0 — Entry gate | **PASSED 2026-09-23** | (a) packet read in order; (b) D-8 discharged — Astra third review `ASTRA_REVIEW_SANGAM_ALGO_PLAN_v1_0.md` = PROCEED_WITH_AMENDMENTS, RRV-01…09 dispositioned in plan §10 + brief changelog + inline [S3-E] amendments; (c) evidence suite re-run `OUTPUT_2026-09-23T050513.txt` SUITE-PASS 13/13 + 13/13 NEG (4 scripts spot-verified by hand, exit 1 under NEG=1); reviewer independently re-ran + mutation-tested (`OUTPUT_2026-09-23T051310.txt`); (d) DB reachable via Cloud SQL proxy **127.0.0.1:5434** (5433 down; `source /Users/Dev/madhav-l3/dbenv.sh`); D-6 staged SQL executed, 100 chunks read, no nodal aspect grant — recorded in DIS.031 `amendment_2026_09_23_predicate_level_recheck` (ground upgraded ATTRIBUTED→CONFIRMED, OCR/400-char limits stated). |
| 1 — R-5 harness | **PASSED 2026-09-23** | Identity D-R5-1 implemented (`r5_identity.py`: contact_uuid uuid5 over the 8-field tuple with peak_date deliberately excluded; episode_uuid over sorted-member set-hash; FIELD_EXCLUSIONS = surrogate id / computed_at / generation-head pointers, named in code at :38-43). Five-rule rebuild/mapping (no-op / supersede / decisive-geometry-reattach / **ambiguous fail-closed** / explicit-withdrawal-only) with journal + replay, in a schema-faithful SQLite mirror of the §5.2 cascade graph (245/247 CASCADE, 249 SET NULL, 363 CASCADE, 334 CASCADE, 331/332 SET NULL, 339 FK-free resolved semantically). Seven §6.3 attacks executable (40 assertions, VERDICT PASS): empty rebuild, moved date (identity stable, content v+1), one-to-many split, many-to-one merge, ambiguous match (no auto-reattach; adjudicated re-run reattaches exactly then), interrupted/resumed (byte-identical manifest, exactly-once), unchanged-count content-swap (per-id canonical diff fires). S14 joined the manifest (`r5_harness/S14_r5_preservation_harness.py\|0\|1`); suite re-run `OUTPUT_2026-09-23T060527.txt` SUITE-PASS 14/14 + 14/14 NEG; NEG mutation = `FAIL_CLOSED_AMBIGUOUS` flipped to False (evidence-bearing: six attack-5 propositions read false on a genuinely re-attached DB). |
| 2 — R-1…R-4, R-6 | **PASSED 2026-09-23** | all six repairs detector-backed — R-6, R-1, R-3(b), R-4, R-2 each with a new MANIFEST entry; suite `OUTPUT_2026-09-23T132601.txt` SUITE-PASS 17/17 + 17/17 NEG; full `tests/l3` minus ka_kshetra 1104 passed / 2 failed = the two known pre-existing pollution flakes (pristine-tree identical). Details per repair below. |
| 3 — E2, E5 | **PASSED 2026-09-23** | E2: verdict-based own-BAV + SAV repair landed engine-side; 235 targeted tests pass; evidence suite `OUTPUT_2026-09-23T143516.txt` SUITE-PASS 17/17 + 17/17 NEG (S3 post-fix detector). E5: station-loop episodes group contacts by child contact interval (`_loop_for_contact` replaces `_loop_for_peak`); aborted approaches whose interval overlaps a loop are included and labelled `loop_phase='approach'` with `approached_never_perfected=True`; horizon-truncated loops mark `perfected=False`; singletons pass through unchanged. Targeted tests 11 passed (`tests/l3/test_ka_sangam_e5_episodes.py`); broader ka_sangam regression 163 passed; full `tests/l3 -k 'not ka_kshetra'` 989 passed / 1 failed = known pre-existing pyswisseph parity flake. Evidence suite `OUTPUT_2026-09-23T150956.txt` SUITE-PASS 18/18 + 18/18 NEG; S18 joined MANIFEST. |
| 4 — E4 + annual-Tājika gate | **PASSED 2026-09-23** | typed natal/clock conditioning (`natal_dignity_strong`, `retrograde_at_peak`, `day_birth`, `kendra_from_lagna`) stamped into `constituent_factors` for all four ka_sangam modes (A/B/C/D); annual-Tājika scheduled-contract gate reports `availability['tajika']='computed'` with `typed_conditions['tajika_covering']=True` only when a covering varṣa exists, else `'unavailable'`/`False`; writer enrichment context fetches D1 dignity, lagna sign, and day-birth from L1. Targeted pytest `test_ka_sangam_e4_typed_conditions.py` 11/11 passed; broader ka_sangam regression 174/174 passed; full `tests/l3 -k 'not ka_kshetra'` 1000 passed / 1 failed = the known pre-existing pyswisseph parity flake `test_transit_search_cache.py::test_cached_call_matches_direct_swe_calc_ut`. Evidence `S19_e4_typed_conditions_and_tajika_gate.py` joined MANIFEST (`|0|1`); suite `OUTPUT_2026-09-23T163312.txt` SUITE-PASS 19/19 + 19/19 NEG; NEG control flips every E4/Tājika expectation. `RUN_ALL.sh` interpreter path corrected to the repo-local `.venv` (was hardcoded to a different clone). D30 falsifier-first gate remains unopened — no D30 rows shipped; the contract is pinned and will be verified before any D30 use in Phase 5. |
| 5 — E6 (E3 gated on N-7) | **PASSED 2026-09-23** | E6 evaluation boundary shipped DB-free: `services/ka_sangam/exposure.py` (exposure manifest by stratum + outcome records + binomial gates, D-1/D-2/D-3 exact). D-1 numbers reproduced from exact binomial tails, not transcribed: per-stratum α=0.034357 (n=35, c≥12), power 0.804825 at 0.40; instrument α=0.034152 (n=100, c≥28), power 0.832450 at 0.32. Writer attaches manifest JSON via `WriterResult.notes` in both substeps (frozen contract — notes is the only carrier). Targeted pytest 22/22 (`test_ka_sangam_e6_exposure.py`); full `tests/l3 -k 'not ka_kshetra'` 1022 passed / 1 failed = the known pre-existing pyswisseph parity flake (verified identical with the writer change stashed). Evidence `S20_e6_exposure_and_gates.py` joined MANIFEST (`\|0\|1`); suite `OUTPUT_2026-09-23T192333.txt` SUITE-PASS 20/20 + 20/20 NEG. |

**DB status re-check (Phase 4 start, 2026-09-23):** `127.0.0.1:5434` is currently refusing connections (`psql: connection to server ... failed: Connection refused`). The prior "DB reachable via 5434" claim in Phase 0 is therefore stale. Code and evidence work for Phase 4 proceed using cached / DB-free paths only; any DB-dependent verification is blocked until the Cloud SQL proxy is restored.

## Phase 3 progress

### E2 — Aṣṭakavarga signed verdicts (PASSED 2026-09-23)

**Design pins applied (plan §3 E2 + M-7 + ASTRA [S3-E] RRV-01/RRV-11):**
- `services/ka_sangam/engine.py`: replaced the held-null `_c7_ashtakavarga_potency` with `_c7_ashtakavarga_verdict` (own-BAV verdict: ≥5 support, 4 indeterminate-leaning-adverse, ≤3 obstruct; returns `None` when the planet is not in the producer’s `computed_planets` receipt). Verdict is wired into `separate_kernel` for Modes A/B (indeterminate −0.1, obstruct −0.2 valence modulation) and removed from the positive supporting combiner. Added `_sav_verdict` for Mode D using BPHS bands (>30 support, 25–30 indeterminate, <25 obstruct) with a retained Phaladīpiká alternate (>28/<28).
- Mode D scans signs with SAV ≥ 25 (`_SAV_SCAN_THRESHOLD = 25`), keeps the classical `_SAV_STRONG_THRESHOLD = 28`, and records the structured `sav_verdict` on every window.
- `pipeline/orchestrator/writers/ka_sangam.py`: `ashtakavarga_transit_potency` current now fires only on `c7_ashtakavarga_verdict.verdict == 'support'` (Mode A/B) or `sav_verdict.verdict == 'support'` (Mode D).
- `ga_writers/ga_strength_writer.py` already emits `ashtakavarga_completeness_receipt` and `ashtakavarga_school_primary`; E2 relies on these columns as the producer receipt.

**Qualification:**
- `tests/l3/test_ka_sangam_a3_fixes.py` — Mode D threshold assertions updated to the 25-scan model; `_SAV_SCAN_THRESHOLD` import and test added.
- `tests/test_u3_convergence_currents.py` — `TestAshtakavarga` rewritten for verdict semantics.
- `tests/l3/test_panchanga_term_honest_null.py` — C7 section rewritten for verdict semantics.
- Targeted pytest run (235 tests): `tests/l3/test_ka_sangam.py tests/l3/test_panchanga_term_honest_null.py tests/l3/test_ka_sangam_r6_kernel.py tests/l3/test_ka_sangam_r1_r4_repairs.py tests/l3/test_ka_sangam_r2_intersection.py tests/test_u3_convergence_currents.py tests/l3/test_ka_sangam_a3_fixes.py` → **235 passed**.
- Full `tests/l3 -k 'not ka_kshetra'`: **978 passed, 1 failed, 7 skipped, 626 deselected**; the single failure is the known pre-existing pyswisseph parity flake `tests/l3/test_transit_search_cache.py::test_cached_call_matches_direct_swe_calc_ut`.
- Evidence suite `OUTPUT_2026-09-23T143516.txt`: **SUITE-PASS 17/17 positive + 17/17 NEG**; S3 rewritten as a post-fix detector (producer receipt, sign-keyed reader, BAV/SAV verdict bands, missing-planet unavailable).

### E5 — Station-loop episodes by child contact interval (PASSED 2026-09-23)

**Design pins applied (plan §3 E5 + M-5 + RRV-05/06 + ASTRA [S3-E] E5 amendments):**
- `services/ka_sangam/engine.py`: `group_station_loop_episodes` now assigns each contact to its station loop using `_loop_for_contact(window_start, window_end, loops)` instead of `_loop_for_peak(peak, loops)`. A contact whose interval overlaps the loop belongs to the episode even if its peak falls before the retrograde station (aborted approach). Horizon-truncated opening/closing halves remain included so boundary contacts are not silently dropped.
- Child summaries carry `loop_phase` (`approach` / `retrograde` / `direct`) and `approached_never_perfected` (`True` when the contact peaks before an in-horizon SR that the loop actually reaches; `False` otherwise), preserving the RRV-06 aborted-approach label.
- `perfected` is `True` only when both the SR and SD of the loop lie inside the horizon; truncated-start or truncated-end loops are `perfected=False`.
- `pipeline/orchestrator/writers/ka_sangam.py` already calls `group_station_loop_episodes` after window generation and persists the episode columns.
- `pipeline/orchestrator/writers/ka_taranga.py` already consumes `episode_children` for occupancy union in the chart's birth timezone.
- Migration `1072_kala_convergence_episodes.sql` adds `is_episode`, `episode_uuid`, `episode_children`, `episode_hull`, `perfected` (additive-only, no existing column/table touched).

**Qualification:**
- `tests/l3/test_ka_sangam_e5_episodes.py` (new, 11 tests): single-loop multi-contact grouping; singleton pass-through; horizon-truncated loop marks `perfected=False`; no-service pass-through; different `signal_id` contracts do not group; aborted-approach child labelled `approach` + `approached_never_perfected=True`; taranga birth-timezone occupancy helpers.
- Broader regression: `test_ka_sangam.py + test_ka_sangam_r6_kernel.py + test_ka_sangam_r1_r4_repairs.py + test_ka_sangam_r2_intersection.py + test_ka_sangam_a3_fixes.py + test_ka_sangam_e5_episodes.py` = **163 passed**.
- Full `tests/l3 -k 'not ka_kshetra'`: **989 passed, 1 failed, 7 skipped, 626 deselected**; the single failure is the known pre-existing pyswisseph parity flake `tests/l3/test_transit_search_cache.py::test_cached_call_matches_direct_swe_calc_ut`.
- Evidence: `S18_e5_station_loop_episodes.py` joined MANIFEST (`|0|1`); suite `OUTPUT_2026-09-23T150956.txt` **SUITE-PASS 18/18 positive + 18/18 NEG**; NEG control flips every E5 expectation (aborted approach not grouped, retrograde child marked approached, singleton grouped, horizon-truncated loop marked perfected).

## Phase 4 progress

### E4 + annual-Tājika gate — PASSED 2026-09-23

**Design pins applied (plan §3 E4 + M-4 + M-7 + ASTRA [S3-E] RRV-03/RRV-08):**
- `services/ka_sangam/engine.py`: `_e4_typed_conditions` assembles the four boolean lineage flags (`natal_dignity_strong`, `retrograde_at_peak`, `day_birth`, `kendra_from_lagna`) using helpers `_e4_natal_dignity_strong_flag`, `_e4_retrograde_flag`, `_e4_day_birth_flag`, `_e4_kendra_flag`. Strong dignities = {Exalted, Moolatrikona, Own}. Retrograde = speed < 0 at exact contact. Day birth = `is_day_birth=True`. Kendra = transit sign is 1st/4th/7th/10th from natal lagna sign.
- All four modes stamp `typed_conditions` inside `constituent_factors`: Mode A/B at the per-contact window, Mode C/D at the sign-level window (retrograde is `False` by construction on sign-level routes; the other three flags are meaningful).
- Annual-Tājika scheduled-contract gate: `_c12_tajika_score` returns `None` when no covering varṣa row exists. `tajika_available = c12 is not None` drives `availability['tajika']` and `typed_conditions['tajika_covering']`. No varṣa → `'unavailable'`/`False`; covering varṣa → `'computed'`/`True`.
- `pipeline/orchestrator/writers/ka_sangam.py`: `_build_enrichment_context` fetches `d1_dignity_by_graha` from `chart_divisionals` (varga='D1', fact_category='varga_dignity', fact_key='dignity', Title-cased), `lagna_sign` from `chart_facts` (fact_subject='LAGNA', fact_key='sign'), and `is_day_birth` from `ctx.config.get('birth_params')` with a `public.charts` fallback via `fetch_birth_params`, soft-failing to `None` so missing birth data never blocks convergence. `EnrichmentContext` carries all three fields plus the existing tajika-year-lords list.

**Qualification:**
- `tests/l3/test_ka_sangam_e4_typed_conditions.py` (new, 11 tests): helper unit contracts; mode A all-True/all-False; mode C/D typed_conditions stamped; tajika computed/unavailable.
- Broader regression: `test_ka_sangam.py + test_ka_sangam_r6_kernel.py + test_ka_sangam_r1_r4_repairs.py + test_ka_sangam_r2_intersection.py + test_ka_sangam_a3_fixes.py + test_ka_sangam_e5_episodes.py + test_ka_sangam_e4_typed_conditions.py` = **174 passed**.
- Full `tests/l3 -k 'not ka_kshetra'`: **1000 passed, 1 failed**; the single failure is the known pre-existing pyswisseph parity flake `tests/l3/test_transit_search_cache.py::test_cached_call_matches_direct_swe_calc_ut`.
- Evidence: `S19_e4_typed_conditions_and_tajika_gate.py` joined MANIFEST (`|0|1`); suite `OUTPUT_2026-09-23T163312.txt` **SUITE-PASS 19/19 + 19/19 NEG**; NEG control flips every E4/Tājika proposition. `RUN_ALL.sh` interpreter path corrected from a hardcoded foreign-clone `venv` to the repo-local `platform/python-sidecar/.venv`.

**D30 falsifier-first gate:** still held. No D30 rows are shipped by E4; the exclusion contract is pinned in code (D30 only as `secondary_dosha`, excluded from score paths) and the falsifier will be added to MANIFEST and pass before any D30 consumer use in Phase 5.

## Phase 5 progress

### E6 — evaluation boundary (exposure manifest + outcome record + binomial gates) — PASSED 2026-09-23

E3 stays gated on N-7 (B-1); Phase 5 scope is E6 only. Entirely DB-free (5434 proxy still refusing connections; no DB-dependent verification was required for this phase's exit).

**Design pins applied (plan §3 E6 + ruling sheet D-1/D-2/D-3):**
- `services/ka_sangam/exposure.py` (new, pure functions, no DB/I/O):
  - **D-1 gate design, computed not transcribed.** `_binomial_sf` (exact upper tail via `math.comb`), `find_critical_value`, `compute_power`. The published numbers are reproduced by the module's own math: per-stratum α = P(X ≥ 12 | Bin(35, 0.20)) = 0.034357 (pub 0.0344), power at 0.40 = 0.804825 (pub 0.805); instrument α = P(X ≥ 28 | Bin(100, 0.20)) = 0.034152 (pub 0.0342), power at 0.32 = 0.832450 (pub 0.833 — the published power figures are normal-approximation roundings; exact values recorded here).
  - **Stratum = (domain × route × method_version)**; method versions never pool (`separated_v2` vs `legacy_i16` key apart). Domain inferred from the signature-class prefix (CAREER/HEALTH/RELATIONSHIP/SPIRITUAL/PSYCHOLOGICAL, else OTHER — never silently dropped). Route defaults to 'A', mirroring the writer insert path.
  - **Exposure manifest**: per-stratum window_count / window_years / issuance_rate over the substep horizon; completeness = 'unavailable' (0 exposure) / 'incomplete' (<30 window-years) / 'complete' (≥30, ruling threshold — the writer's 7-yr near tier will therefore always read 'incomplete', which is the honest answer for a 7-year window).
  - **D-2 outcome record**: five observation states; n_evaluated = hits + misses (ambiguous/censored excluded from n); hit-rate interval [hits/total, (hits+ambiguous)/total]; claim = lower bound; censoring (ambiguous+censored)/total > 10% → elevated label, > 20% → CENSORING_BLOCKED regardless of n.
  - **D-3 eligibility**: `evaluation_eligible=False` or `is_synthetic=True` → NOT_ELIGIBLE. Writer-side default is True with the gap documented — no `evaluation_eligible`/`is_synthetic` field exists anywhere in the codebase today (searched); wiring a real consent/synthetic source is recorded as open item B-6.
  - **Gate semantics**: the α-level test is evaluated against the ACTUAL n (p-value at observed hits/n), with n ≥ 35 as the power precondition; the c≥12/c≥28 criticals are the design point at exactly n=35/n=100. 12 hits in 36 evaluated is correctly BELOW_CRITICAL (P ≈ 0.041 > 0.0344) — pinned by test so it is not later "fixed".
  - Gate vocabulary: NOT_ELIGIBLE / UNAVAILABLE / CENSORING_BLOCKED / PROVISIONAL_INSUFFICIENT_N / BINOMIAL_GATE_PASSED / BELOW_CRITICAL. A passed gate is 'BINOMIAL_GATE_PASSED', **never** 'EMPIRICALLY_EVALUATED' — that state stays closed pending M-6's five conditions.
- `pipeline/orchestrator/writers/ka_sangam.py`: `_substep_near` and `_substep_lifetime` each compute `compute_exposure_manifest(deduped, horizon_start, horizon_end)` and attach `manifest.to_json()` as `WriterResult.notes`. No DB write, no `WriterBase` contract change (frozen) — notes is the only carrier the contract offers. The lifetime early-return (`_birth_year is None`) path keeps its existing explanatory notes unchanged.

**Qualification:**
- `tests/l3/test_ka_sangam_e6_exposure.py` (new, 22 tests): D-1 constants reproduce via exact binomial; find_critical_value recovers 12/28; stratum keying incl. legacy-version non-pooling; manifest counts/rates/completeness/JSON; D-2 n-exclusion, interval + lower-bound claim; gate pass/fail/insufficient-n; censoring elevated-vs-blocked incl. blocked-regardless-of-n; NOT_ELIGIBLE (synthetic + ineligible); UNAVAILABLE; instrument pooling and gate; α-level test at actual n.
- Full `tests/l3 -k 'not ka_kshetra'`: **1022 passed, 1 failed, 7 skipped** — the single failure is the known pre-existing pyswisseph parity flake `test_transit_search_cache.py::test_cached_call_matches_direct_swe_calc_ut`, verified identical with the writer change stashed (fails on the pristine tree in isolation).
- Evidence: `S20_e6_exposure_and_gates.py` joined MANIFEST (`|0|1`) — 27 propositions covering the D-1 exact-number reproduction, D-2 accounting, D-3 eligibility, the EMPIRICALLY_EVALUATED lockout, and the writer wiring (import + both call sites + both notes attachments, checked statically). Suite `OUTPUT_2026-09-23T192333.txt` **SUITE-PASS 20/20 positive + 20/20 negative controls**; the NEG run inverts every proposition.

**Open item recorded:** B-6 — writer-side `evaluation_eligible`/`is_synthetic` have no real source field anywhere in the codebase; the manifest defaults them True/False and the outcome builders take them as parameters. Unblock condition: a consent/synthetic marker lands in chart metadata (owner: native/L1).

**D30 falsifier-first gate:** still held, unopened — no D30 rows shipped by E6; the gate fires before any D30 consumer use.

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
| B-6 | E6 writer-side `evaluation_eligible`/`is_synthetic` have no source field (defaulted True/False, documented) | A consent/synthetic marker lands in chart metadata | Native / L1 |

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

### R-2 clock-intersection oracle — PASSED 2026-09-23 (F-13 repair; closes Phase 2)

**Oracle** (`services/ka_dasha_kala/intersection.py`, pure functions, no DB/I/O):
- `intersect_segments(intervals)` — atomic simultaneous intersection over ALL intervals (every level, every system): every maximal sub-interval with a constant supporter set becomes one `IntersectionSegment` carrying its sorted supporter tuple (`SupporterRef`: system_id, level_n, lord_graha, dasha_row_id, parent_row_id). Degenerate `[d, d)` intervals are inert (support nothing).
- `agreement_for(start, end, segments)` — distinct systems DIRECTLY co-supporting ≥1 atomic segment of `[start, end)`; a degenerate or uncovered interval returns a real, EVALUATED zero.
- **Boundary convention declared: `[start, end)` (S-H)** — start-inclusive, end-exclusive; contiguous daśā chains partition time instead of double-covering boundary instants; `date` and `datetime` flow through the same code path (sub-day boundaries work).
- Anti-transitivity is structural: A∩B and B∩C never makes A agree with C unless they directly share a segment. Nested levels of the SAME system never inflate the count (distinct systems, not intervals; parent identity carried on refs).

**Wiring:**
- `ka_dasha_kala/service.py`: `_build_overlap_key` DELETED. `query()` builds atomic segments once over all walked intervals and computes each `EligibleWindow.cross_dasha_agreement` via the oracle (direct co-support over the window's span — not exact-key grouping, no transitive merging).
- `ka_sangam/engine.py`: `mode_a_search` tracks `dasha_query_state ∈ {not_queried, ok, failed}`. `_dasha_score_for_date` and `_c_cross_dasha_agreement` use the S-H covering test `start <= peak < end`. `max_level=3` (executor rationale in inline comment). The c_cross constituent factors now distinguish three states: covered → `c_cross_dasha_agreement` value key; query succeeded but no window covers peak (or zero windows) → `c_cross_dasha_agreement_evaluated_empty`; query FAILED → `c_cross_dasha_agreement_unavailable` ('FAILED' marker) — evaluated-empty and unavailable are NEVER merged (R-2). `availability['dasha']` reflects the state.

**Qualification:**
- `tests/l3/test_ka_sangam_r2_intersection.py` (new, 16 tests): oracle falsifier cases (unequal-endpoint agreement 305 d; disjoint; anti-transitive chain; nested levels same system; degenerate evaluated-zero; valid empty; contiguous S-H boundaries; sub-day datetimes; convention declared) + service wiring (fake `walk_eligible_intervals` — agreement across unequal endpoints, evaluated-empty) + engine level (S-H boundary coverage, failure → unavailable, no-covering → evaluated-empty, valid-empty, covering-window score).
- Targeted regression: `r2 + r6 + r1_r4 + a3_fixes + ka_sangam + l3_convergence + u3_convergence_currents + w2_first_frontier_service_contracts` = 233 passed — no existing pin relied on exact-endpoint dasha coverage.
- Full `tests/l3` minus ka_kshetra: **1104 passed, 2 failed — both the known pre-existing pollution flakes** (pristine-tree identical).

**Evidence:** `S6_overlap_key_exact_pair.py` rewritten POST-FIX (exact key removed at source + behavioural agreement=2 over the 305-day overlap, NEG flips expectation to interval-count 3); `S17_r2_intersection_oracle.py` joined MANIFEST (falsifier suite, NEG flips the anti-transitive expectation to 3). Suite `OUTPUT_2026-09-23T132601.txt` SUITE-PASS 17/17 positive + 17/17 NEG.

## Last commit

`4a7cd89d8` — "sangam stage3: Phase 5 E6 — exposure manifest + evaluation-boundary gates".

## Evidence artifacts this phase

- `evidence_sangam/OUTPUT_2026-09-23T050513.txt` (executor run) · `OUTPUT_2026-09-23T051310.txt` (reviewer run)
- `evidence_sangam/OUTPUT_2026-09-23T150956.txt` (E5 executor run) · `S18_e5_station_loop_episodes.py` (E5 post-fix detector)
- `evidence_sangam/OUTPUT_2026-09-23T192333.txt` (E6 executor run, final suite) · `S20_e6_exposure_and_gates.py` (E6 post-fix detector)
- `ASTRA_REVIEW_SANGAM_ALGO_PLAN_v1_0.md` (D-8 gate output)
- DIS.031 `amendment_2026_09_23_predicate_level_recheck` (D-6 corpus ground)
- /tmp/d6_node_drishti_recheck.txt (raw SQL output, 100 rows; regenerable from the staged SQL)
