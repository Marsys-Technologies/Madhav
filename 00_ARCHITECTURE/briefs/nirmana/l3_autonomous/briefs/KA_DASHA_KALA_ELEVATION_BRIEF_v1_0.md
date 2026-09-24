---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_DASHA_KALA_ELEVATION_BRIEF
version: "1.2"
status: PROPOSED_FOR_NATIVE_RULING      # v1.0 REWORK (25) → v1.1 ACCEPT_WITH_CORRECTIONS (23 resolved, 2 partial, 18 new) → v1.2 folds all 18
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
asset_or_interface_ids: ["ka_dasha_kala", "IP-9 (call_dasha_eligibility default + cap)", "SC-6 producer (clock concurrence rows)", "L1 amendment request: applies_to_this_chart_flag detector + conditions_for_use clauses"]
goal_objective: "Make ka_dasha_kala the clock authority the blueprint names it (§3.5 row 2): the served daśā routes obtain hierarchy, atomic-segment agreement and per-system applicability from this service under the binding's temporal and qualification fields, referencing L1's own flags rather than restating or ignoring them, with every existing scalar labelled for what it is and every cap disclosed."
source_revision: "9feac52d7 (l3/kala-layer-briefs); every cited code path re-verified identical at 27b0146f3 (2026-09-24)"
accepted_upstream_contract: "L1_CONDITION_RELATION_CLOCK_CONTRACT/1.0/blob-99953b54749a794efee48760d718e387bc8743e2 — establishes start_iso/end_iso as half-open (:59-63) and nothing else cited here. The four further columns this brief relies on (sandhi_flag, next_dasha_start_iso, is_truncated_at_window_*, applies_to_this_chart_flag) are established by migration 881:57 and ga_dashas_writer.py:1062-1095, not by that blob. The W2 fail-closed dasha contract landed via fa9857f00 (#2607); 47131772b is the reviewed W2 tip, not an ancestor of this base"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agents, fresh context; reports at briefs/reviews/REVIEW_KA_DASHA_KALA_v1_0.md (REWORK) and _v1_1.md (ACCEPT_WITH_CORRECTIONS)"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_dasha_kala/{service,tree_walk,eligibility,intersection,writer}.py", "platform/python-sidecar/tests/l3/test_ka_dasha_kala*.py, tests/l3/test_w2_first_frontier_service_contracts.py (dasha rows)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:272-399 (call_dasha_eligibility) — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/dasha_sandhi.ts — Pūrṇa-owned; L3 owns only the sentinel test under platform/python-sidecar/tests/l3/"]
must_not_touch: ["chart_dashas / ga_writers/ga_dashas_writer.py (L1 authority, §N.5 — the :1717 hardcoded Aṣṭottarī applicability is raised as an L1 amendment, not edited here)", "brahmagyan/l0_dasha_systems.py (L0; the conditions_for_use qualification is an L0 request)", "pipeline/orchestrator/service_probes.py:871-899 (DB-free proxy probe fixed by ruling D-CND-34, #2071)", "services/ph_nimitta/dasha_consensus.py (L4 reader)", "pipeline/orchestrator/writers/ka_sangam.py, services/ka_sangam/engine.py:1395-1449 (readers; Saṅgam-owned)", "platform-mcp/src/tools/kala_views/**", ".github/workflows/deploy.yml", "applied migrations", "WriterBase / orchestrator transaction contract"]
target_state_data_plane: "PRODUCER_READY for the service contract (stage 3); CONSUMER_INTEGRATED requires IP-9 to land in Pūrṇa's tree and the L3-owned sentinel to pass"
target_state_campaign: "ANALYZED (this brief) → ENRICHED at stage 3; no t3 event exists for this asset today"
wave: "W2 (service proof); concurrence rows data-bound W5"
shape: single asset, service/probe
evidence_base: >
  Source read directly on 9feac52d7 [V]; claims re-verified at source by two independent reviewers
  and adopted here are marked [R]; Lane D §3, T1 Frontier row, Lane E §3.1/§1 Q-K01/K03/K13, Lane F
  §2a/§2d, STATE.md ★, dossiers/KA_GRAHA_SANCARA_KA_DASHA_KALA_DOSSIER (2026-09-20/22) marked [A];
  no database query was run for this brief.
does_not_authorize: any code, migration, grant, build or serving change. This brief proposes; the native rules.
changelog:
  - "1.2 (2026-09-24): v1.1 re-review dispositions (18 findings) — N1 `as_of` is OPTIONAL (window mode unchanged; membership is a separate entry point), so the payload stays additive and neither fenced caller breaks; N2 `hours_to_boundary` re-defined as the signed distance to the NEAREST boundary of the containing row (next_dasha_start_iso is the next sibling's start, ga_dashas_writer.py:2945+), and the boundary row no longer claims `sandhi_flag` is unchanged across the two sides; N3 the ablation states the alignment it runs under and reports the row-membership delta as a fifth, labelled difference (the service prunes MD subtrees below min_band, the route returns flat rows); N4 seven systems BY DEFAULT, caller may restrict, coverage over active_systems; N5 irrelevant control replaced with one the code can fail; N6 the four L1 columns attributed to migration 881/the writer, not the clock-contract blob; N7 the one alias map is platform-mcp/src/lib/ayanamsha.ts; N8 unknown chart id → empty result WITH coverage; N9 SC-3's period-identity tuple adopted verbatim; N10 resolution:'exact'; N11 the two TS paths moved out of may_touch; N12 `unavailable` is result-level; N13 sentinel carries a sentinel-specific reason; N14 §12 wording; N15 Foundation F23; N16 'the blueprint names it the clock authority'; N17 stale HEAD sha; N18 L4's own confidence_multiplier recorded as part of the coordinated packet."
  - "1.1 (2026-09-24): v1.0 REWORK dispositions (25 findings) — see §12."
  - "1.0 (2026-09-24): first issue."
---

# `ka_dasha_kala` elevation brief — the clock authority

## §0 — The recommendation, in one paragraph

`ka_dasha_kala` is what the blueprint names the layer's clock authority (§3.5 row 2); the registry
calls it the "Daśā Eligibility Service" (`asset_registry_seed.ts:2246-2262`). What it computes
**today** [R]: a parent/child hierarchy reconstructed from L1's flat `chart_dashas` rows — all seven
systems **by default**, a caller may pass a subset (`service.py:100,:145-155` [R]) — a
target-relative eligibility band (`eligibility.py:59-66`, scored against caller-supplied lords, not
applicability), and **atomic-segment agreement** across systems (`intersection.py:72,108-121`), the
one distinction the live route lacks, because the route computes agreement by exact
`(start_date, end_date)` pair equality (`call_service_wrappers.ts:367-380` [R]) — the F-13 defect
`intersection.py:1-9` was written to replace. The service is DATE-grain (`DashaInterval.start_date:
date`, `tree_walk.py:55-56,80,111` [R]) while the route already serves `start_iso/end_iso`
(`:349-359` [R]); the route defaults `ayanamsha_id` to bare `'lahiri'` (`:328` [V]) and caps at
`LIMIT 400` (`:362` [R]) undisclosed. Neither reads L1's own `applies_to_this_chart_flag`
(`ga_dashas_writer.py:1028,1093` [R]) — a flag whose value is a constant `True` default with the
canonical chart's Aṣṭottarī condition hardcoded for every chart (`:1717` [R]).
Recommendation: **`INTEGRATE` + `ENRICH_CORRECT` + `QUALIFY_LIMIT`** — route the served tools
through the service **after** the service carries the binding's B1 instants (never before, or the
hour grain the route already serves is lost); atomic-segment agreement as the concurrence producer
(SC-6); L1's flag referenced and stamped `unqualified` while its detector is a constant; the
existing soft scalars labelled; caps and coverage in the B5 shape. Every addition is **additive** —
`as_of` is optional, the payload only grows — so neither fenced caller changes first. Decision for
the native: wire the routes, or declare the bypass intentional (§10).

---

## §1 — Already established (stage 0: reconcile, cite, do not re-derive)

| record | what it says | delta on this base |
|---|---|---|
| Contribution register §5 (REGISTER:137) | *"Clock retrieval, ancestry and system traversal. P/E/I/Q: precise ISO intervals, actual overlap and applicability/failed-system coverage; label approximate subdivisions. DP07/08."* | unchanged; "label approximate subdivisions" binds `_subdivide_prana` (§2.2) |
| Strategy §6.1 **L3-A02** (`:272`) | service probe across seven systems, zero rows; *"expose actual hierarchy, applicability, intervals, failed/silent systems and qualified overlap; no layer-local clock restatement."* W2 | unchanged |
| Strategy **L3-U02** (`:442`) | *actual simultaneous interval intersections with parent hierarchy, applicability and silent/failed states; no exact-date-equality* | the service has the intersection; the route has the exact-pair defect (§3) |
| Blueprint §3.5 row 2 (`:318`) | names this asset **the clock authority** | the phrase's source; the registry's own name is narrower (§2.1) |
| `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md:144` (§4.1 row) | service only; accepted L1 clocks; Sangam/Jivana/Kshetra; *"independent proof after physical clock data"* | Jivana **declares** it (seed `:2404`), reads `chart_dashas` directly (`ka_jivana_parva.py:85-91` [V]) |
| same, `:242-243` (W2 source) | *"Dasha now fails the whole request when one named system read fails"* | present: `service.py:180-188` [R], landed via `fa9857f00` (#2607); `47131772b` is **not an ancestor** of this base and touches Avadhi/Yojaka only [R] |
| W0 field register `:22, :593-597` | `service query → KaDashaKalaResult/EligibleWindow`; zero DML | unchanged |
| L1 `chart_dashas` — **migration `881:57` + `ga_dashas_writer.py:1062-1095`** (N6: **not** the clock-contract blob, which establishes only half-open `start_iso/end_iso` at `:59-63`) [R] | columns incl. `start_iso/end_iso`, `sandhi_flag` (= `duration_days < 20`, `:1062`), `sandhi_with_next_dasha_lord`, `next_dasha_start_iso` (`:1089-1090`, set by `compute_sandhi_post_pass` `:2945+` to **the next sibling row's `start_iso`**), **`applies_to_this_chart_flag`** (`:1028` default `True`; `:1093` on every row; `:1717` Aṣṭottarī `True` with the comment `FORENSIC: Rahu in 5H → applicable`; `False` only on `scope_cap` rows `:3405`) | the flag is **persisted-but-unused** by both the service and the route; its detector is a constant — §N.8 |
| L0 `brahmagyan/l0_dasha_systems.py` [R] | `conditions_for_use` prose per system (`:115,137-139,171,201`); `computation_method` (`:107,130,164,194`); canonical ids include `chara_jaimini` (`:209`) but **no** `chara_karaka`, `naisargika`, `mudda` | three of the seven service ids (`tree_walk.py:40-43`) have no L0 row under that id; L1 uses the same three (`ga_dashas_writer.py:3205,3213,3217`) |
| Lane D §3 / T1 | writer = self-test; traversal API "NOT-FOUND" consumer | corrected: `KaDashaKalaService` is imported at `ka_sangam.py:38`, instantiated `:321`, used in `ka_sangam/engine.py:1395-1440` (query at `:1410-1423`, **no `as_of`**) and `:1445-1449` (score) [R]; `ph_nimitta/dasha_consensus.py:78-84`, call at `:106-118` [R]. **No served route** uses it (§3) |
| Lane F §2a | `call_service_wrappers.ts:328` `?? 'lahiri'` | still true [V]; `:227` and `:595` use `DEFAULT_AYANAMSHA` (`constants.ts:2` = `lahiri_chitrapaksha` [R]); PR #2695 carries the fix (open; not verifiable from this session) |
| `dossiers/KA_GRAHA_SANCARA_KA_DASHA_KALA_DOSSIER_v1_0.md:285,376` [A] | `eligibility_score` is *"a soft prior"* | labelled in §4 item 5 |
| Blueprint v5.0 §3.5 row 2, §16.2 (`:900`), SC-6/SC-10 | hub imported by Avadhi (constant), Saṅgam, L4 | binds §5 |
| KALA_DELEGATED_DECISIONS D-H (`:351-361`) | `CONSUMER_INTEGRATED` = a record with a live call path + L3 sentinel | binds §9 |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Identity and registration [V]
`platform/scripts/seed/asset_registry_seed.ts:2246-2262`: **"Daśā Eligibility Service"**;
`storage_type: 'service'`, `target_table: null`, `count_sql: null`, `depends_on: ['ga_dashas']`,
`scope: 'per_chart'`, `asset_kind: 'service'`, `catalog_status: 'DRAFT'`.

### 2.2 What the code is [V]/[R]
- **Writer** `services/ka_dasha_kala/writer.py` (172 lines): self-test asserts the seven systems in
  `chart_dashas` for the canonical chart under `lahiri_chitrapaksha` (`:26`) and a non-empty valid
  window; writes `service_health`/`selftest_detail`; **raises `RuntimeError` on a failed self-test**
  (`:156` [R] — the §N.8 fix); `WriterResult(rows_written=0)`; never commits or writes
  `asset_throughput`.
- **Service** `service.py:77-252`: `query(...)` (`:90-103`) — `chart_id`, `ayanamsha_id`,
  `target_lords`, `related_lords`, `date_start`, `date_end` required; `max_level: int = 4`,
  `min_band: EligibilityBand = RELATED`, `prana_grain: bool = False`, **`systems: Optional[Set[str]]
  = None`** (`:100` [R]), `_query_counter` — **there is no `as_of` parameter today**; returns
  `KaDashaKalaResult` (`:59`) of `EligibleWindow` (`:39`, `eligibility_score: float` `:51`) and
  `CrossDashaAgreement` (`:32`), carrying `systems_queried = active_systems` (`:246`). All seven
  systems are queried **by default**; an unknown id in a caller-supplied subset raises (`:150-154`).
  `high_agreement_count` threshold `>= 2` (`:74,:234`); fail-whole-request on one system's read
  failure (`:180-188`); `confirm_systems_present` (`:252`); validation covers `max_level`, the date
  pair and `systems` only (`:136-155`) — **no chart-existence check** (N8).
- **Traversal** `tree_walk.py`: `DashaInterval` with `start_date: date` (`:55-56`);
  `_fetch_level1`/`_fetch_children` select `start_date, end_date` only (`:80,:111`) — **the service
  is DATE-grain**; the canonical ayanāṃśa id is matched by SQL equality (`:84`) with no alias
  resolution, by design; **MD subtrees below `min_band` are pruned before children are queried**
  (`:225-232`, via `is_eligible_for_pruning`) [R]; `_subdivide_prana(interval, n_subdivisions=9)`
  (`:125,:137-146`) — date arithmetic, an approximation.
- **Eligibility** `eligibility.py`: `BAND_SCORE = {0.85, 0.50, 0.20}` (`:26-30`), docstring
  *"deliberately soft/probabilistic"* (`:9`); `score_eligibility` scores a lord against
  caller-supplied `target_lords`/`related_lords` (`:59-66`) — **target relevance, not system
  applicability**; `is_eligible_for_pruning` (`:84-86`).
- **Intersection** `intersection.py`: `[start, end)` (`:34`); `intersect_segments` (`:72`);
  `agreement_for` counts co-supporting systems per atomic segment (`:108-121`); the module header
  names the F-13 exact-pair defect it replaces (`:1-9`).
- **No applicability logic exists** in the service; no `silent`/`not_applicable` state exists [R].

### 2.3 Consumers (search boundary: `platform/python-sidecar`, `platform-mcp/src`, `platform/src`, tests excluded)
| consumer | what it reads | role |
|---|---|---|
| `writers/ka_sangam.py:38,321`; `services/ka_sangam/engine.py:1395-1440` (`query()` at `:1410-1423`, **no `as_of`**), `:1445-1449` (uses `eligibility_score`) [R] | the service, incl. the soft scalar | `applicability` / `computation` — the scalar's blast radius |
| `services/ph_nimitta/dasha_consensus.py:78-84`, call at `:106-118` [R] (L4) | `derive_dasha_consensus(..., ayanamsha_id)`; **and at `:121-133` converts `cross_dasha_agreement.count` into `confidence_multiplier = min(1.0, max(0.5, max_count/7))` and `high_agreement = max_count >= 4`**, reaching `ph_nimitta.py:236,277` as `dasha_consensus_count` [R] | `computation` (L4) — a **second** scalar derived from this payload one layer up (N18); its non-test importer is `kala_permission/permission.py:89` |
| `service_probes.py:871-899,940-952` [R] | DB-free proxy probe (ruling D-CND-34, #2071) | probe — not this brief's to change |
| `writers/ka_avadhi.py:29` | `ALL_DASHA_SYSTEMS` constant | vocabulary |
| `writers/ka_jivana_parva.py` (seed `:2404`) | **declares**, reads `chart_dashas` (`:85-91`) | declared, not read |
| **served routes** | `call_dasha_eligibility` (`call_service_wrappers.ts:272-399`; handler `:322`; SQL `:349-363` incl. `start_iso, end_iso` and `LIMIT 400`; lord filter at any level with **no subtree pruning** `:340-346`, or **all rows** when `target_lords` is empty `:331`; grouping `:367-380` by exact `(start_date,end_date)`; envelope `:385-395` returns `dasha_windows: [], count: 0, is_error: false` on empty — no phrase, no coverage) [R]; `kala_dasha_sandhi_get` (`dasha_sandhi.ts:173-186` via `marsys://tool/L1/get_dashas`; DATE strings `:213-214`) [R] | **bypass** |

**Live-path statement.** The service's hierarchy, band and atomic-segment agreement reach Saṅgam and
L4 today and **no served answer**. The bypass routes are live and user-reachable.

### 2.4 Epistemic class and authority of the important fields
| field | class (F04) | authority | note |
|---|---|---|---|
| interval bounds | `COMPUTED_FACT_CONFIGURATION` | L1 `start_iso/end_iso` (half-open, blob `99953b54…:59-63`) | the service reads the DATE columns today (§3); must reference the instants |
| `applies_to_this_chart_flag` | claimed `QUALIFIED_RULE`; **actually a constant** | L1 (`:1028,:1093,:1717`) | persisted-but-unused; detector = constant → `unqualified` (§4 item 3); `corpus_verifiable=false` |
| `sandhi_flag` | computed **heuristic** (`duration_days < 20`, `:1062`) | L1 | a short-period marker, **not** boundary proximity — never restated as one (§N.7 item 1); it is a property **of a row**, so two adjacent rows may legitimately differ |
| `next_dasha_start_iso`, `sandhi_with_next_dasha_lord` | computed fact (post-pass `:1089-1090`, `:2945+`: the **next sibling's** `start_iso`) | L1 | the input for a *derived* boundary-proximity field (§4 item 4) |
| `eligibility_score`, `BAND_SCORE` | `INTERPRETIVE_INFERENCE`, soft (`eligibility.py:9`) | this service | `tier_basis='relative_uncalibrated'`, `source_qualification='algorithmic_approximation'`, `corpus_verifiable=false`; consumed by Saṅgam `:1445-1449` |
| `high_agreement_count` (≥2) | engineered threshold | this service | labelled likewise; never served as confidence — **and L4 derives its own multiplier from the agreement count (N18)** |
| prāṇa subdivision | approximation (`n_subdivisions=9`) | this service | `claim_grain='date_grain'` + `source_qualification='algorithmic_approximation'` + `corpus_verifiable=false` |
| `CrossDashaAgreement` / `AgreementSummary` | computed relation over computed facts | this service | the concurrence producer (SC-6) |
| system id vocabulary | identity | service `tree_walk.py:40-43` = L1 `:3205-3217`; L0 lacks three | SC-10-class reconciliation (§10 decision 2) |

### 2.5 Position on both ladders
Data-plane: `PLAN_REVIEWED`; the W2 fail-closed contract landed (`fa9857f00`) — `PRODUCER_READY` for
the *self-test* contract only. t3: **no freeze event** (`EVENTS.jsonl` carries only dossier/no-op
rows for this asset). Cost: bounded reads of `chart_dashas`, no ephemeris; service-call latency
**unmeasured**.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | The served daśā route (`call_dasha_eligibility`) re-implements the clock query as raw SQL: it returns `start_iso/end_iso` and an agreement count — but the agreement is **exact `(start_date,end_date)` pair equality** (`:367-380` [R]), so two systems whose periods overlap without identical bounds never "agree" (the F-13 defect `intersection.py` fixed inside the service), the default ayanāṃśa is bare `'lahiri'` (`:328`), the result is capped at `LIMIT 400` (`:362`) undisclosed, and an empty result is `dasha_windows: [], count: 0` with no coverage (`:385-395`). The service that computes atomic-segment agreement is not on the path; L1's `applies_to_this_chart_flag` is read by neither |
| Evidence | `call_service_wrappers.ts:328, 349-363, 367-380, 385-395` [V]/[R]; `intersection.py:1-9, 108-121` [R]; `ga_dashas_writer.py:1028,1093,1717` [R] |
| Expected contract | L3-A02 (*hierarchy, applicability, intervals, failed/silent systems, qualified overlap*); L3-U02 (*no exact-date-equality*); Strategy §3 *Clock interval* (applicability/prerequisites, failure reason); Product §7.1; SC-5 (caps disclosed); SC-10; F28 |
| Defect class | **unserved** (the qualified agreement object exists and is not on the served path) + **wrong context** (a default that silently changes the subject's convention) + **undisclosed cap** + **unqualified** (an applicability flag with a constant detector, read by nobody) |
| Impact | Q-K06's cross-clock agreement is computed by exact-pair at the surface (false negatives on overlap) or asserted empty (`dissent: []`); Q-K01's *applicable vs merely computable* is unanswerable — the only applicability signal is a constant; a silent empty masquerades as "no eligible window"; a >400-row answer is truncated without a flag |
| Non-claim | Live incidence of the zero-row default path is not measured; the canonical rows' `ayanamsha_id` is inferred from `writer.py:26`/`ka_jivana_parva.py:89` pins [R], not queried; doctrinal validity of any system's applicability condition is L0's; no claim that the service's agreement is *better* than exact-pair — that is the ablation (§4.12) |

---

## §4 — The semantic delta (contract §4) — smallest sufficient change

1. **L3-Q served.** Q01 (*which exact clocks are engaged* — hierarchy + applicability), Q05 (*why
   timing methods disagree* — atomic-segment agreement as data, silent/failed/not-applicable
   distinct from dissent), Q13. Partially Q06. Cannot serve Q02/Q08. Lane E's Q-K01, K03, K06, K13.
2. **Instants (binding B1) — the ordering constraint.** The service reads and carries L1's
   `start_iso/end_iso` (`tree_walk.py:80,111` change from the DATE columns), `t_start/t_end` as
   `timestamptz`, `inclusivity='closed_open'` (matches `intersection.py:34` and L1's half-open
   contract), `time_basis='event_instant'`, `claim_grain='instant_grain'`; prāṇa subdivisions
   `claim_grain='date_grain'` + `source_qualification='algorithmic_approximation'` +
   `n_subdivisions`. **IP-9 may route the served tools through the service only after this lands** —
   routing first would *lose* the hour grain the route already serves [R].
3. **Applicability referenced, not invented (B2).** Per system, `completeness_state`:
   - `applied` only where an *admitted* applicability clause exists and its detector is real;
   - **`unqualified` for every system today**, because the only applicability signal L1 carries
     (`applies_to_this_chart_flag`) is a constant `True` default with one canonical-chart condition
     hardcoded for all charts (`:1717`) — a detector that cannot go false (§N.8). The service
     **references** the flag (never ignores or contradicts it — §N.5: a service value disagreeing
     with the L1 row is a halt) and stamps `unqualified` beside it with reason
     `applicability_detector_constant`;
   - `inapplicable` where an admitted clause excludes the system.
   **`unavailable` is a result-level state, not a per-system one** (N12): one system's read failure
   fails the whole request (`:180-188`), so no payload carrying a per-system `unavailable` can be
   produced; the result-level `unavailable` names the failing system as its reason.
   `operator_role='applicability'`; `comparable_with='self'` within a system, `different_convention`
   across systems; `tier_basis='relative_uncalibrated'` on the band; `epistemic_class` per §2.4.
4. **Boundary proximity is a derivation, not L1's `sandhi_flag`.** The served `sandhi` object =
   `{hours_to_boundary, nearest_boundary ∈ {start, end}, next_lord}` where **`hours_to_boundary` is
   the signed distance to the *nearest* boundary of the row containing `as_of`** —
   `min(as_of − start_iso, next_dasha_start_iso − as_of)` — because `next_dasha_start_iso` is the
   *next sibling's* start (`ga_dashas_writer.py:2945+`), so a distance measured only forward jumps to
   a whole period's duration the instant `as_of` crosses a boundary (N2).
   `epistemic_class='COMPUTED_FACT_CONFIGURATION'` (a derived distance). L1's `sandhi_flag` is
   carried through **under its own meaning** (short period, `< 20 d`, a property of its own row) and
   never relabelled; two rows either side of a boundary may carry different flags, and that is
   correct, not a defect.
5. **The existing scalars, labelled.** `eligibility_score` (`BAND_SCORE`) and `high_agreement_count`
   stay in the payload for Saṅgam (`engine.py:1445-1449`), stamped
   `epistemic_class='INTERPRETIVE_INFERENCE'`, `tier_basis='relative_uncalibrated'`,
   `source_qualification='algorithmic_approximation'`, `corpus_verifiable=false`, and are **withheld
   from any served confidence field** (Product §5.2). Their migration off the served path is Saṅgam's
   (amendment 9) **and L4's** — `dasha_consensus.py:121-133` derives a second scalar
   (`confidence_multiplier`) from the same agreement count (N18); both belong to the coordinated
   packet, neither is changed by this brief.
6. **Concurrence rows (SC-6 offer).** `agreement_for` produces `{chart, interval, clock_id, verdict ∈
   {supports, opposes, silent, not_applicable}, jurisdiction, method_version}` per system per atomic
   segment — `not_applicable` where item 3 says `unqualified`/`inapplicable`, `silent` where a system
   ran and covers no lord for the target; `independence_group` declares the shared root of the
   nakṣatra-family systems (natal Moon's nakṣatra — L0 `computation_method` at
   `l0_dasha_systems.py:107,130,164,194` [R]), `basis='declared_lineage'`. **B3 position:** L1's only
   row id is a per-build `uuid4` (`ga_dashas_writer.py:1065` [R]); the service **DEMANDS** SC-3's
   period identity **in SC-3's own vocabulary — `(chart, signal, system, level, t_start)`**
   (blueprint `:885`, N9) — and emits `window_ref` with it; until then rows carry the tuple, not the
   uuid.
7. **Coverage (B5, seven keys) on every result including empty:** `{requested_horizon,
   completed_horizon, resolution:'exact', partitions_searched: active_systems, exclusions: [systems
   excluded with reason], unsearched_regions: [], completion_detector:
   'all_requested_systems_read_or_request_unavailable'}` — `partitions_searched` and the detector are
   over **`active_systems`**, not a constant seven (N4). The route's `LIMIT 400` becomes
   `truncated: bool` + `returned/available` (IP-9).
8. **Time discipline (SC-1) — additive, not breaking (N1).** `as_of` is **optional**:
   `query(..., as_of: Optional[datetime] = None)`. Absent, the method behaves exactly as today (a
   window query over `date_start..date_end`) and both live callers — `ka_sangam/engine.py:1410`,
   `ph_nimitta/dasha_consensus.py:109`, each in `must_not_touch` — are unaffected. Membership at an
   instant is a **separate entry point**, `at(chart_id, ayanamsha_id, as_of, …)`, because a window
   query does not answer a membership question; it echoes `as_of` and carries the §4.4 sandhi object.
   `as_of` is the birth instant's tz, never the server's.
9. **Interface packet IP-9 (Pūrṇa owns the TS; L3 owns the sentinel).** `call_dasha_eligibility` and
   `kala_dasha_sandhi_get` obtain rows from the service (sidecar route) with the canonical id
   required; the wrapper resolves an omitted id to `DEFAULT_AYANAMSHA` (`constants.ts:2`). On alias
   resolution (N7): **the one map in this repository is `platform-mcp/src/lib/ayanamsha.ts:8-27`
   (`resolveChartFactsAyanamsha`, wrapped by `registry_bridge.ts:108`), which the L3 wrapper does not
   import**; adopting it for `call_dasha_eligibility` is part of IP-9's packet — no new map is
   written, and the service keeps requiring the canonical id (`tree_walk.py:84`, by design).
10. **Old vs new.** Positive: canonical chart, a known AD midpoint → seven systems with states,
    instants, atomic-segment agreement. Negative: one system's read fails → result-level
    `unavailable` naming the system (unchanged behaviour). Boundary: `as_of = end_iso − 1 s` →
    membership true; `+ 1 s` → false; `hours_to_boundary` ≈ 0 on **both** sides under the §4.4
    nearest-boundary definition. Missing: a system with no admitted clause → `unqualified`, never
    dropped. Duplicated: four nakṣatra-family systems on one segment → one `independence_group`.
11. **Competent simpler baseline.** The current route: `start_iso/end_iso` at instant grain,
    exact-pair agreement, a constant applicability flag unread, `LIMIT 400`, no coverage.
12. **Ablation — with its alignment stated (N3).** Serve the same question through the service and
    through the route on the same `as_of`. The two selections are **not** the same row set by
    default: the service prunes MD subtrees below `min_band` before querying children
    (`tree_walk.py:225-232`) and descends to `max_level`, while the route returns every overlapping
    row at any level with no pruning (`:340-346`) or all rows when `target_lords` is empty (`:331`),
    capped at 400. The differential therefore runs under a **declared alignment** —
    `min_band=NEUTRAL`, `max_level=4`, `prana_grain=False`, identical non-empty `target_lords`, a
    fixture under 400 rows — and reports **five** differences: (i) agreement computed on atomic
    segments (overlapping-but-unequal periods now agree), (ii) per-system `completeness_state`,
    (iii) coverage/cap disclosure, (iv) `hours_to_boundary`, and (v) the row-membership delta, which
    is labelled a selection difference and **not** counted as elevation. Lords and instants must be
    identical on the intersection. If (i) never differs on the canonical chart, the F-13 fix is
    decorative for this native and the brief says so.

---

## §5 — Preservation, migration, history, rollback (contract §5) + fences

- **Preserved kernels** (`PRESERVE`): `tree_walk` hierarchy reconstruction and its pruning semantics;
  `intersect_segments`; `agreement_for`; `BAND_SCORE` bands (labelled); fail-whole-request; the
  `RuntimeError` on a failed self-test (`writer.py:156`); the seven-system assertion; the
  canonical-id-only SQL match.
- **Changed** (`ENRICH_CORRECT`): instant columns read; B1/B2/B5 fields; the derived boundary object;
  optional `as_of` + the `at()` entry point.
- **Qualified** (`QUALIFY_LIMIT`): the soft scalars; the constant applicability flag; prāṇa.
- **Integrated** (`INTEGRATE`): IP-9; concurrence rows offered to SC-6's owner.
- **Never restated** (§N.5): bounds, flags and `applies_to_this_chart_flag` are references to L1 rows.
- **No table, no migration, no rows; no feature flag exists or is proposed** — the payload is
  additive and `as_of` is optional, so readers ignore new fields until they adopt them and **no
  caller signature changes** (N1).
- **Hub rule.** `services/ka_dasha_kala` is inside the frozen **L4** digest closure via
  `ph_nimitta/dasha_consensus.py`; any change here shifts L4's writer digest → a coordinated
  cross-stream packet with a named owner; additive payload so `dasha_consensus.py` and `ka_sangam.py`
  need no change first.
- **Upstream amendment requests (raised, not fabricated):** (a) **L1** — `applies_to_this_chart_flag`
  needs a real detector, and `ga_dashas_writer.py:1717`'s canonical-chart Aṣṭottarī condition applied
  to all charts is an upstream defect; (b) **L0** — qualify `conditions_for_use` prose into
  executable clauses with page-grain citations, and reconcile the id vocabulary (`chara_karaka`,
  `naisargika`, `mudda` have no L0 row; `chara_jaimini` exists) — DP02.
- **Cascade**: none (no owned table). **Rollback**: IP-9 re-points the wrapper; the service payload
  is additive.
- **Protected classes**: untouched.

---

## §6 — Analysis lenses A–J (skill contract)

| lens | answer |
|---|---|
| A identity | `ka_dasha_kala`, L3, service/probe; epistemic: deterministic hierarchy/intersection over L1 facts + one soft engineered band + one approximation (prāṇa); placement correct; disposition `INTEGRATE + ENRICH_CORRECT + QUALIFY_LIMIT` |
| B inputs/DAG | declared `ga_dashas` — correct and real; Avadhi's constant import and Jivana's declared-not-read edge are documentation-only; no hidden read. T0; fan-out: Saṅgam, L4 (two scalars), Avadhi-vocab |
| C correctness | invariants: intervals half-open and non-overlapping within a system+level; child ⊂ parent; intersection commutative; whole-request failure on one system failure; **a service value ≠ its L1 row is a halt**. Golden: the canonical chart's seven systems; boundary: `end_iso ± 1 s`; differential: service vs route under the §4.12 alignment. Detectors: the self-test's raise; the §7 fixtures |
| D data sufficiency | n/a for rows; **admitted applicability clauses are the gap** (L0/L1 requests) |
| E consumers | Saṅgam, L4 (incl. its own derived multiplier), Avadhi-vocab (real); served routes (bypass — the defect); Jivana (declared, not read) |
| F AI/product | per-system states, atomic-segment `dissent` rows (IP-2), `hours_to_boundary`, coverage machine-readable; `unqualified` shown, not hidden; the empty-with-wrong-default becomes impossible |
| G efficiency | no measured hotspot; **justified no-change** |
| H reliability | idempotent (no writes); self-test raises on failure; timeout from measured latency (stage 3); no credentials |
| I change packet | files in `may_touch`; base `9feac52d7`; additive payload and optional parameter; tests in §7; W2; coordinated L4-digest re-pin; `service_probes.py` untouched (D-CND-34) |
| J final evidence | this brief + the W2 landing (`fa9857f00`); §7 results; three review reports; IP-9 sentinel |

---

## §7 — Proof matrix (contract §6) — executable, detector named

| proof | fixture / boundary | expected | invariant | detector (fails when…) | owner |
|---|---|---|---|---|---|
| Positive | canonical chart, window over a known AD, canonical id, no `as_of` | seven systems, each with `completeness_state` (`unqualified` today) + `t_start/t_end` instants; **signature unchanged for existing callers** | bounds = L1 `start_iso/end_iso` | any bound ≠ L1; any system missing a state; an existing call raising `TypeError` | L3 |
| Positive (subset) | `systems={'vimshottari','yogini'}` | two partitions; `partitions_searched` = those two; unknown id raises | coverage over `active_systems` | coverage reports seven | L3 |
| Positive (wrapper) | `ayanamsha_id` omitted at `call_dasha_eligibility` | resolved to `DEFAULT_AYANAMSHA`; rows returned | wrapper resolves | zero rows / `'lahiri'` | IP-9 (Pūrṇa code, L3 sentinel) |
| Negative | one system's L1 read raises | **result-level** `unavailable` naming that system; no partial payload | no partial payload | a partial result; a per-system `unavailable` | L3 |
| Relevant influence | **gated on §10 decision 2** (no admitted clause exists today; Foundation F23 — a planned test is not a pass): flip one system's admitted-clause fixture | that system `unqualified → applied`; others unchanged | isolation | a second system moves | L3 (after L0) |
| Relevant influence (today) | change `next_dasha_start_iso` in the fixture by 1 h | `hours_to_boundary` changes by 1 when the end is the nearest boundary; lords unchanged | derivation | unchanged | L3 |
| Irrelevant control | permute `related_lords`'s iteration order; and mutate an unread `chart_dashas` column in the fixture (`lord_sign`, `citation_human`) | identical payload hash | insensitive to unread inputs | hash differs | L3 |
| Duplication/correlation | four nakṣatra-family systems agree on a segment | one `independence_group`; `declared_current_count`=1 | shared root | count = 4 | L3 |
| Context/missingness | unknown chart id; a system that ran and covers nothing vs one `unqualified` | **empty result carrying coverage** naming the chart partition and `completion_detector` (no chart-existence check exists today); `silent` ≠ `not_applicable` | B5 on every result incl. empty | a bare empty; the two states read the same | L3 |
| Boundary/precision | `as_of = end_iso − 1 s` / `+ 1 s` via `at()` | membership flips; `hours_to_boundary` ≈ 0 **both** sides (nearest-boundary definition); each side reports **its own row's** `sandhi_flag`, never relabelled | `closed_open` | a date-grain answer; a forward-only distance; `sandhi_flag` restated as proximity | L3 |
| Delivery (sentinel) | sentinel `completeness_state='unqualified'` with `reason='SENTINEL_kalachakra_unqualified'` on Kālacakra only — a reason value no other row carries | reaches `call_dasha_eligibility`'s envelope and the saved reading | survives | absent | L3 |
| Cap disclosure | 401 windows in the fixture | `truncated=true`, `returned=400`, `available=401` | disclosed | silent 400 | IP-9 |
| Revision | L1 regenerates `chart_dashas` | payload changes; no cache | fresh | stale | L3 |
| Value | frozen L3-Q01/Q05 questions before/after (baseline) | atomic-segment agreement and per-system states appear; the exact-pair route cannot show them | — | no distinction | baseline |
| Evaluation | n/a (no claim issued) | — | — | — | — |

Binding rows: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `time_basis`, `claim_grain`), B2
(`epistemic_class`, `completeness_state`, `operator_role`, `comparable_with`, `tier_basis`,
`source_qualification`, `corpus_verifiable` on the band, the constant flag and prāṇa), B4
(`independence_group`, `declared_current_count`), B5 (`coverage`, seven keys, over `active_systems`).
**DEMANDS** B3 — SC-3's period identity `(chart, signal, system, level, t_start)` in its own
vocabulary (L1 offers only a per-build `uuid4`). **Asset-local (not binding vocabulary):** `as_of`,
`hours_to_boundary`, `nearest_boundary`, `next_lord`, `eligibility_score`, `high_agreement_count`,
`truncated`, `returned`, `available`. Layer tests 5/6/7/9 = the duplication, context, boundary and
delivery rows.

---

## §8 — Prioritization

Within the asset: (1) the wrong default + the cap (IP-9; PR #2695 content + `truncated`) → (2) B1
instants in the service (**precondition** for IP-9 routing) → (3) the served bypass (the elevation:
atomic-segment agreement + states) → (4) the scalar labels → (5) concurrence rows → (6) the L1/L0
requests. T0 hub, W2; fan-out to Saṅgam and L4 — additive payload, optional parameter, coordinated
packet. Holds: IP-9 waits on Pūrṇa's queue; `applied` states wait on L0/L1.

---

## §9 — Disposition and target state

`INTEGRATE` + `ENRICH_CORRECT` + `QUALIFY_LIMIT` (service/probe terminal rule: availability,
correctness, failure semantics **and a product consumer** verified; no row-count proxy). Data-plane:
`PRODUCER_READY` for the enriched contract at stage 3; `CONSUMER_INTEGRATED` when IP-9 is live at a
`file:line` on `main` with the sentinel (D-H record). Campaign: `ANALYZED` → `ENRICHED`; `FROZEN`
only after an independent verifier. **Non-claims:** no `DATA_ACCEPTED`; `VALUE_EVALUATED` N until the
baseline shows the Q05 delta; every system serves `unqualified` until L0/L1 supply a real
applicability detector — *"it cannot earn full completion solely by returning unavailable states"*
(Strategy §7), so the upstream requests are on this asset's critical path.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Wire the served daśā routes to the service (IP-9, after the B1 delta), or declare the bypass intentional and retire the traversal API to research-only?** | **Wire, in that order.** The service is the only place atomic-segment agreement exists; the route's exact-pair agreement is the defect the service already fixed |
| 2 | **Raise the L1 amendment (a real detector for `applies_to_this_chart_flag`; the `:1717` hardcoded condition) and the L0 request (executable `conditions_for_use` clauses with page-grain citations; id vocabulary for `chara_karaka`/`naisargika`/`mudda`)?** | **Yes**, both bounded; until then every system serves `unqualified` with the reason |
| 3 | The concurrence rows' owner (SC-6) and the period identity (SC-3, in SC-3's tuple) | offered / demanded here; the owner rulings are the blueprint's |
| 4 | Do `eligibility_score`/`high_agreement_count` leave the payload once Saṅgam retires its `confidence_*` inputs (amendment 9) — **and does L4's own `confidence_multiplier` (`dasha_consensus.py:121-133`) go with them?** | coordinate as one packet with Saṅgam **and L4**; label now, retire together |

---

## §11 — What is not verified here (§N.8: stated, not guessed)

1. PR #2695's content and state — no GitHub access from the author or either reviewer session (the
   `github` MCP failed to connect).
2. Live incidence of the zero-row default path; the canonical rows' `ayanamsha_id` — inferred from
   code pins [R], not queried.
3. Service-call latency — never measured.
4. Whether Kṣetra S3 reads `chart_dashas` — outside this asset's citation set; not checked.
5. `origin/l3/kala-elevation-readiness` remote tip — code identity verified locally instead.
6. No database query was run for this brief or its reviews.

## §12 — Review dispositions

**v1.0 → v1.1 (25 findings, all accepted).** F1 (§2.4, §4.3, §5, §10.2); F2 (§0); F3 (§3, §4.2
ordering, §4.11–12); F4 (§2.4, §4.4, §7 boundary); F5 (§2.4, §4.5, §10.4); F6 (§1, §5, §10.2); F7
(§4.2); F8 (§4.7, §7 cap row); F9 — row replaced (§4.9, §7 wrapper row); F10 (§7 owner column); F11
(§7 gated row); F12 (frontmatter, §1); F13 (§1 file name); F14 (frontmatter "commit"); F15 (§2.3);
F16 (§2.2, §5); F17 (§2.3, §3); F18 (§4.6); F19 — the `A01–A04` claim **removed**, not expanded; F20
(§2.3); F21 — the `availability['dasha']` claim **removed**; F22 (§4.6, §7 DEMANDS); F23 (§5); F24
(§1); F25 (`must_not_touch`).

**v1.1 → v1.2 (18 findings, all accepted).** N1 (§4.8 optional `as_of` + separate `at()`; §5 "no
caller signature changes"; §7 Positive detector); N2 (§2.4, §4.4 nearest-boundary definition, §7
Boundary); N3 (§4.12 declared alignment + fifth labelled difference); N4 (§0, §2.2, §4.7, §7 subset
row); N5 (§7 irrelevant control); N6 (frontmatter `accepted_upstream_contract`, §1 L1 row); N7 (§4.9
— `platform-mcp/src/lib/ayanamsha.ts` named as the one map); N8 (§2.2, §4.7, §7 context row); N9
(§4.6, §7 DEMANDS — SC-3's tuple); N10 (§4.7 `resolution:'exact'`); N11 (frontmatter — TS paths moved
to `interface_packet_targets_not_may_touch`; the two fixed `must_not_touch` entries added); N12 (§4.3
result-level `unavailable`); N13 (§7 delivery sentinel reason); N14 (§12 wording: F19/F21 resolved by
**removal**); N15 (§7 "Foundation F23"); N16 (§0, §2.1, `goal_objective`); N17 (`source_revision`);
N18 (§2.3, §2.4, §4.5, §10.4 — L4's own derived multiplier).
