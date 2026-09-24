---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_DASHA_KALA_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_DASHA_KALA_v1_0.md, 25 findings); v1.1 dispositions each; → PROPOSED_FOR_NATIVE_RULING on re-verification
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows offered/demanded in §7
asset_or_interface_ids: ["ka_dasha_kala", "IP-9 (call_dasha_eligibility default + cap)", "SC-6 producer (clock concurrence rows)", "L1 amendment request: applies_to_this_chart_flag detector + conditions_for_use clauses"]
goal_objective: "Make ka_dasha_kala the clock authority its registration claims: the served daśā routes obtain hierarchy, atomic-segment agreement and per-system applicability from this service under the binding's temporal and qualification fields, referencing L1's own flags rather than restating or ignoring them, with every existing scalar labelled for what it is and every cap disclosed."
source_revision: "9feac52d7 (l3/kala-layer-briefs; platform/ and platform-mcp/ byte-identical to HEAD 4d8c6aa9b)"
accepted_upstream_contract: "L1_CONDITION_RELATION_CLOCK_CONTRACT/1.0/blob-99953b54749a794efee48760d718e387bc8743e2 (chart_dashas: start_iso/end_iso half-open, sandhi_flag, next_dasha_start_iso, is_truncated_at_window_*, applies_to_this_chart_flag); the W2 fail-closed dasha contract as landed via fa9857f00 (#2607) — 47131772b is the reviewed W2 tip, not an ancestor of this base"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; v1.0 report at briefs/reviews/REVIEW_KA_DASHA_KALA_v1_0.md; re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_dasha_kala/{service,tree_walk,eligibility,intersection,writer}.py", "platform/python-sidecar/tests/l3/test_ka_dasha_kala*.py, tests/l3/test_w2_first_frontier_service_contracts.py (dasha rows)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:272-399 (call_dasha_eligibility), platform-mcp/src/tools/kala_views/dasha_sandhi.ts"]
must_not_touch: ["chart_dashas / ga_writers/ga_dashas_writer.py (L1 authority, §N.5 — the :1717 hardcoded Aṣṭottarī applicability is raised as an L1 amendment, not edited here)", "brahmagyan/l0_dasha_systems.py (L0; the conditions_for_use qualification is an L0 request)", "pipeline/orchestrator/service_probes.py:871-899 (DB-free proxy probe fixed by ruling D-CND-34, #2071 — changing it re-opens a ruling)", "services/ph_nimitta/dasha_consensus.py (L4 reader)", "pipeline/orchestrator/writers/ka_sangam.py, services/ka_sangam/engine.py:1395-1449 (readers; Saṅgam-owned)", "platform-mcp/src/tools/kala_views/** except as an interface packet", "applied migrations", "WriterBase / orchestrator transaction contract"]
target_state_data_plane: "PRODUCER_READY for the service contract (stage 3); CONSUMER_INTEGRATED requires IP-9 to land in Pūrṇa's tree and the L3-owned sentinel to pass"
target_state_campaign: "ANALYZED (this brief) → ENRICHED at stage 3; no t3 event exists for this asset today"
wave: "W2 (service proof); concurrence rows data-bound W5"
shape: single asset, service/probe
evidence_base: >
  Source read directly on 9feac52d7 [V]; claims re-verified at source by the independent reviewer
  and adopted here are marked [R] with the reviewer's file:line; Lane D §3, T1 Frontier row, Lane E
  §3.1/§1 Q-K01/K03/K13, Lane F §2a/§2d, STATE.md ★, dossiers/KA_GRAHA_SANCARA_KA_DASHA_KALA_DOSSIER
  (2026-09-20/22) marked [A]; no database query was run for this brief.
does_not_authorize: any code, migration, grant, build or serving change. This brief proposes; the native rules.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions — F1 the L1 applies_to_this_chart_flag exists (constant-detector) and the service's applicability delta now references it; F2 §0 states what the service computes today; F3 baseline corrected (the route already returns start_iso/end_iso and an exact-pair agreement count; the service is DATE-grain today; ordering constraint added); F4 sandhi_flag is a <20-day heuristic — served boundary proximity is a derivation over next_dasha_start_iso; F5 the existing eligibility_score/high_agreement_count scalars labelled; F6 three service ids have no L0 row; F7 claim_grain enum + source_qualification='algorithmic_approximation'; F8 coverage in the B5 seven-key shape and the LIMIT 400 cap disclosed; F9 alias row replaced (canonical id required at the service, alias resolution at the wrapper); F10–F25 citation/wording corrections; B3 position stated."
  - "1.0 (2026-09-24): first issue."
---

# `ka_dasha_kala` elevation brief — the clock authority

## §0 — The recommendation, in one paragraph

`ka_dasha_kala` is registered as the layer's clock authority. What it computes **today** [R]: a
parent/child hierarchy reconstructed from L1's flat `chart_dashas` rows for all seven systems
unconditionally (`service.py:145-155`; `tree_walk.py:79-92,110-119`), a target-relative
eligibility band (`eligibility.py:59-66`, scored against caller-supplied lords — not
applicability), and **atomic-segment agreement** across systems (`intersection.py:72,108-121`) —
the one distinction the live route lacks, because the route computes agreement by exact
`(start_date, end_date)` pair equality (`call_service_wrappers.ts:367-380` [R]), the defect F-13
that `intersection.py:1-9` was written to replace. The service is DATE-grain (`DashaInterval.
start_date: date`, `tree_walk.py:55-56,80,111` [R]) while the route already serves
`start_iso/end_iso` (`:349-359` [R]); the route defaults `ayanamsha_id` to bare `'lahiri'`
(`:328` [V]) and caps at `LIMIT 400` (`:362` [R]) undisclosed. Neither the service nor the route
reads L1's own `applies_to_this_chart_flag` (`ga_dashas_writer.py:1028,1093` [R]) — a flag whose
value is a constant `True` default with the canonical chart's Aṣṭottarī condition hardcoded for
every chart (`:1717` [R]). Recommendation: **`INTEGRATE` + `ENRICH_CORRECT` + `QUALIFY_LIMIT`** —
route through the service **after** the service carries the binding's B1 instants (never before,
or hour grain is lost); atomic-segment agreement as the concurrence producer (SC-6); L1's flag
referenced and stamped `unqualified` while its detector is a constant; the existing soft scalars
labelled; caps and coverage in the B5 shape; the L1/L0 amendment requests raised, not fabricated.
Decision for the native: wire the routes, or declare the bypass intentional (§10).

---

## §1 — Already established (stage 0: reconcile, cite, do not re-derive)

| record | what it says | delta on this base |
|---|---|---|
| Contribution register §5 (REGISTER:137) | *"Clock retrieval, ancestry and system traversal. P/E/I/Q: precise ISO intervals, actual overlap and applicability/failed-system coverage; label approximate subdivisions. DP07/08."* | unchanged; "label approximate subdivisions" binds `_subdivide_prana` (§2.2) |
| Strategy §6.1 **L3-A02** (`:272`) | service probe across seven systems, zero rows; *"expose actual hierarchy, applicability, intervals, failed/silent systems and qualified overlap; no layer-local clock restatement."* W2 | unchanged |
| Strategy **L3-U02** (`:442`) | *actual simultaneous interval intersections with parent hierarchy, applicability and silent/failed states; no exact-date-equality* | the service has the intersection; the route has the exact-pair defect (§3) |
| `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md:144` (§4.1 row) | service only; accepted L1 clocks; Sangam/Jivana/Kshetra; *"independent proof after physical clock data"* | Jivana **declares** it (seed `:2404`), reads `chart_dashas` directly (`ka_jivana_parva.py:85-91` [V]) |
| same, `:242-243` (W2 source) | *"Dasha now fails the whole request when one named system read fails"* | present: `service.py:180-188` [R], landed via `fa9857f00` (#2607); `47131772b` (the reviewed tip) is **not an ancestor** of this base and touches Avadhi/Yojaka only [R] |
| W0 field register `:22, :593-597` | `service query → KaDashaKalaResult/EligibleWindow`; zero DML | unchanged |
| L1 `chart_dashas` (migration `881:57`; `ga_dashas_writer.py:1062-1095`) [R] | columns incl. `start_iso/end_iso`, `sandhi_flag` (= `duration_days < 20`, `:1062`), `sandhi_with_next_dasha_lord`, `next_dasha_start_iso` (`:1089-1090`), **`applies_to_this_chart_flag`** (`:1028` default `True`; `:1093` written to every row; `:1717` Aṣṭottarī `True` with the comment `FORENSIC: Rahu in 5H → applicable`; `False` only on `scope_cap` rows `:3405`) | the flag is **persisted-but-unused** by both the service and the route; its detector is a constant — §N.8 |
| L0 `brahmagyan/l0_dasha_systems.py` [R] | `conditions_for_use` prose per system (`:115,137-139,171,201`); `computation_method` (`:107,130,164,194`); canonical ids include `chara_jaimini` (`:209`) but **no** `chara_karaka`, `naisargika`, `mudda` | three of the seven service ids (`tree_walk.py:40-43`) have no L0 row under that id; L1 uses the same three (`ga_dashas_writer.py:3205,3213,3217`) |
| Lane D §3 / T1 | writer = self-test; traversal API "NOT-FOUND" consumer | corrected: `KaDashaKalaService` is imported at `ka_sangam.py:38` and instantiated `:321`; used in `ka_sangam/engine.py:1395-1440` (query) and `:1445-1449` (score) [R]; `ph_nimitta/dasha_consensus.py:78-84` (`derive_dasha_consensus`, id required) [R]. **No served route** uses it (§3) |
| Lane F §2a | `call_service_wrappers.ts:328` `?? 'lahiri'` | still true [V]; `:227` and `:595` use `DEFAULT_AYANAMSHA` (`constants.ts:2` = `lahiri_chitrapaksha` [R]); PR #2695 carries the fix (open; not verifiable from this session) |
| `dossiers/KA_GRAHA_SANCARA_KA_DASHA_KALA_DOSSIER_v1_0.md:285,376` [A] | `eligibility_score` is *"a soft prior"* | labelled in §4 item 5 |
| Blueprint v5.0 §3.5 row 2 (`:318`), §16.2 (`:900`), SC-6/SC-10 | hub imported by Avadhi (constant), Saṅgam, L4 | binds §5 |
| KALA_DELEGATED_DECISIONS D-H (`:351-361`) | `CONSUMER_INTEGRATED` = a record with a live call path + L3 sentinel | binds §9 |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Identity and registration [V]
`platform/scripts/seed/asset_registry_seed.ts:2246-2262`: `storage_type: 'service'`, `target_table:
null`, `count_sql: null`, `depends_on: ['ga_dashas']`, `scope: 'per_chart'`, `asset_kind:
'service'`, `catalog_status: 'DRAFT'`.

### 2.2 What the code is [V]/[R]
- **Writer** `services/ka_dasha_kala/writer.py` (172 lines): self-test asserts the seven systems in
  `chart_dashas` for the canonical chart under `lahiri_chitrapaksha` (`:26`) and a non-empty valid
  window; writes `service_health`/`selftest_detail`; **raises `RuntimeError` on a failed self-test**
  (`:156` [R] — the §N.8 fix); `WriterResult(rows_written=0)`; never commits or writes
  `asset_throughput`.
- **Service** `service.py:77-252`: `query(...)` (`:90-103`, `ayanamsha_id` a **required
  positional** [R]) → `KaDashaKalaResult` (`:59`) of `EligibleWindow` (`:39`, with
  `eligibility_score: float` `:51`) and `CrossDashaAgreement` (`:32`); all seven systems queried
  unconditionally (`:145-155` [R]); `high_agreement_count` threshold `>= 2` (`:74,:234` [R]);
  fail-whole-request (`:180-188` [R]); `confirm_systems_present` (`:252`).
- **Traversal** `tree_walk.py`: `DashaInterval` with `start_date: date` (`:55-56` [R]);
  `_fetch_level1`/`_fetch_children` select `start_date, end_date` only (`:80,:111` [R]) — **the
  service is DATE-grain**; `_subdivide_prana(interval, n_subdivisions=9)` (`:125,:137-146`) —
  date arithmetic, an approximation.
- **Eligibility** `eligibility.py`: `BAND_SCORE = {0.85, 0.50, 0.20}` (`:26-30` [R]), docstring
  *"deliberately soft/probabilistic"* (`:9` [R]); `score_eligibility` scores a lord against
  caller-supplied `target_lords`/`related_lords` (`:59-66` [R]) — **target relevance, not
  system applicability**; `is_eligible_for_pruning`.
- **Intersection** `intersection.py`: `[start, end)` (`:34` [R]); `intersect_segments` (`:72`);
  `agreement_for` counts co-supporting systems per atomic segment (`:108-121` [R]); the module
  header names the F-13 exact-pair defect it replaces (`:1-9` [R]).
- **No applicability logic exists** in the service; no `silent`/`not_applicable` state exists [R].

### 2.3 Consumers (search boundary: `platform/python-sidecar`, `platform-mcp/src`, `platform/src`, tests excluded)
| consumer | what it reads | role |
|---|---|---|
| `writers/ka_sangam.py:38,321`; `services/ka_sangam/engine.py:1395-1440` (query), `:1445-1449` (uses `eligibility_score`) [R] | the service, incl. the soft scalar | `applicability` / `computation` — the scalar's blast radius |
| `services/ph_nimitta/dasha_consensus.py:78-84` [R] (L4) | `derive_dasha_consensus(..., ayanamsha_id)` — id required; its non-test importer is `kala_permission/permission.py:89` [R] | `computation` (L4) — the `:157` `'lahiri'` default is on `confirm_seven_systems_reachable`, **no live caller found within scope** [R] |
| `service_probes.py:871-899,940-952` [R] | DB-free proxy probe (ruling D-CND-34, #2071) | probe — not this brief's to change |
| `writers/ka_avadhi.py:29` | `ALL_DASHA_SYSTEMS` constant | vocabulary |
| `writers/ka_jivana_parva.py` (seed `:2404`) | **declares**, reads `chart_dashas` (`:85-91`) | declared, not read |
| **served routes** | `call_dasha_eligibility` (`call_service_wrappers.ts:272-399`; handler `:322`; SQL `:349-363` incl. `start_iso, end_iso` and `LIMIT 400`; grouping `:367-380` by exact `(start_date,end_date)` key; envelope `:385-395` returns `dasha_windows: [], count: 0, is_error: false` on empty — no phrase, no coverage) [R]; `kala_dasha_sandhi_get` (`dasha_sandhi.ts:173-186` via `marsys://tool/L1/get_dashas`; DATE strings `:213-214`) [R] | **bypass** |

**Live-path statement.** The service's hierarchy, band and atomic-segment agreement reach Saṅgam
and L4 today and **no served answer**. The bypass routes are live and user-reachable.

### 2.4 Epistemic class and authority of the important fields
| field | class (F04) | authority | note |
|---|---|---|---|
| interval bounds | `COMPUTED_FACT_CONFIGURATION` | L1 `start_iso/end_iso` (half-open, blob `99953b54…:61` [R]) | the service reads the DATE columns today (§3); must reference the instants |
| `applies_to_this_chart_flag` | claimed `QUALIFIED_RULE`; **actually a constant** | L1 (`:1028,:1093,:1717`) | persisted-but-unused; detector = constant → `unqualified` (§4 item 3) |
| `sandhi_flag` | computed **heuristic** (`duration_days < 20`, `:1062`) | L1 | a short-period marker, **not** boundary proximity — must not be restated as one (§N.7 item 1) |
| `next_dasha_start_iso`, `sandhi_with_next_dasha_lord` | computed fact (post-pass `:1089-1090`) | L1 | the input for a *derived* boundary-proximity field (§4 item 4) |
| `eligibility_score`, `BAND_SCORE` | `INTERPRETIVE_INFERENCE`, soft (`eligibility.py:9`) | this service | must carry `tier_basis='relative_uncalibrated'`, `source_qualification='algorithmic_approximation'`; consumed by Saṅgam `:1445-1449` |
| `high_agreement_count` (≥2) | engineered threshold | this service | labelled likewise; never served as confidence |
| prāṇa subdivision | approximation (`n_subdivisions=9`) | this service | `claim_grain='date_grain'` + `source_qualification='algorithmic_approximation'` |
| `CrossDashaAgreement` / `AgreementSummary` | computed relation over computed facts | this service | the concurrence producer (SC-6) |
| system id vocabulary | identity | service `tree_walk.py:40-43` = L1 `:3205-3217`; L0 lacks three | SC-10-class reconciliation (§10 decision 2) |

### 2.5 Position on both ladders
Data-plane: `PLAN_REVIEWED`; the W2 fail-closed contract landed (`fa9857f00`) — `PRODUCER_READY`
for the *self-test* contract only. t3: **no event**. Cost: bounded reads of `chart_dashas`, no
ephemeris; service-call latency **unmeasured**.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | The served daśā route (`call_dasha_eligibility`) re-implements the clock query as raw SQL: it returns `start_iso/end_iso` and an agreement count — but the agreement is **exact `(start_date,end_date)` pair equality** (`:367-380` [R]), so two systems whose periods overlap without identical bounds never "agree" (the F-13 defect `intersection.py` fixed inside the service), the default ayanāṃśa is bare `'lahiri'` (`:328`), the result is capped at `LIMIT 400` (`:362`) undisclosed, and an empty result is `dasha_windows: [], count: 0` with no coverage (`:385-395`). The service that computes atomic-segment agreement is not on the path; L1's `applies_to_this_chart_flag` is read by neither |
| Evidence | `call_service_wrappers.ts:328, 349-363, 367-380, 385-395` [V]/[R]; `intersection.py:1-9, 108-121` [R]; `ga_dashas_writer.py:1028,1093,1717` [R] |
| Expected contract | L3-A02 (*hierarchy, applicability, intervals, failed/silent systems, qualified overlap*); L3-U02 (*no exact-date-equality*); Strategy §3 *Clock interval* (applicability/prerequisites, failure reason); Product §7.1; SC-5 (caps disclosed); SC-10; F28 |
| Defect class | **unserved** (the qualified agreement object exists and is not on the served path) + **wrong context** (a default that silently changes the subject's convention) + **undisclosed cap** + **unqualified** (an applicability flag with a constant detector, read by nobody) |
| Impact | Q-K06's cross-clock agreement is computed by exact-pair at the surface (false negatives on overlap) or asserted empty (`dissent: []`); Q-K01's *applicable vs merely computable* is unanswerable — the only applicability signal is a constant; a silent empty masquerades as "no eligible window"; a >400-row answer is truncated without a flag |
| Non-claim | Live incidence of the zero-row default path is not measured; the canonical rows' `ayanamsha_id` is inferred from `writer.py:26`/`ka_jivana_parva.py:89` pins [R], not queried; doctrinal validity of any system's applicability condition is L0's; no claim that the service's agreement is *better* than exact-pair — that is the ablation (§4.10) |

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
   `n_subdivisions`. **IP-9 may route the served tools through the service only after this lands**
   — routing first would *lose* the hour grain the route already serves [R].
3. **Applicability referenced, not invented (B2; F1).** Per system, `completeness_state`:
   - `applied` only where an *admitted* applicability clause exists and its detector is real;
   - **`unqualified` for every system today**, because the only applicability signal L1 carries
     (`applies_to_this_chart_flag`) is a constant `True` default with one canonical-chart
     condition hardcoded for all charts (`:1717`) — a detector that cannot go false (§N.8). The
     service **references** the flag (never ignores or contradicts it — §N.5: a service value
     disagreeing with the L1 row is a halt) and stamps the `unqualified` beside it with reason
     `applicability_detector_constant`;
   - `unavailable` where the L1 read failed (whole request, unchanged); `inapplicable` where an
     admitted clause excludes the system.
   `operator_role='applicability'`; `comparable_with='self'` within a system, `different_convention`
   across systems; `tier_basis='relative_uncalibrated'` on the band; `epistemic_class` per field
   as §2.4.
4. **Boundary proximity is a derivation, not L1's `sandhi_flag` (F4).** The served `sandhi` object
   = `{hours_to_boundary, next_lord}` computed from L1's `next_dasha_start_iso` and
   `sandhi_with_next_dasha_lord`, `epistemic_class='COMPUTED_FACT_CONFIGURATION'` (a derived
   distance), while L1's `sandhi_flag` is carried through **under its own meaning** (short period,
   `< 20 d`) and never relabelled.
5. **The existing scalars, labelled (F5).** `eligibility_score` (`BAND_SCORE`) and
   `high_agreement_count` stay in the payload for Saṅgam (`engine.py:1445-1449`), stamped
   `epistemic_class='INTERPRETIVE_INFERENCE'`, `tier_basis='relative_uncalibrated'`,
   `source_qualification='algorithmic_approximation'`, and are **withheld from any served
   confidence field** (Product §5.2); their migration off the served path is Saṅgam's (amendment 9
   class), not this brief's.
6. **Concurrence rows (SC-6 offer).** `agreement_for` produces `{chart, interval, clock_id,
   verdict ∈ {supports, opposes, silent, not_applicable}, jurisdiction, method_version}` per
   system per atomic segment — `not_applicable` where item 3 says `unqualified`/`inapplicable`,
   `silent` where a system ran and covers no lord for the target; `independence_group` declares the
   shared root of the nakṣatra-family systems (natal Moon's nakṣatra — L0 `computation_method`
   at `l0_dasha_systems.py:107,130,164,194` [R]), `basis='declared_lineage'`. **B3 position:** L1's
   only row id is a per-build `uuid4` (`ga_dashas_writer.py:1065` [R]); the service **DEMANDS** a
   content-addressed period identity `(chart, system, level, lord, t_start)` from SC-3's packet and
   emits `window_ref` with it; until then rows carry the tuple, not the uuid.
7. **Coverage (B5, F8) on every result including empty:** `{requested_horizon, completed_horizon,
   resolution:'event_instant', partitions_searched: [systems], exclusions: [systems
   unavailable/unqualified with reason], unsearched_regions: [], completion_detector: 'all_seven_
   systems_read_or_whole_request_unavailable'}`; the route's `LIMIT 400` becomes `truncated: bool`
   + `returned/available` (IP-9).
8. **Time discipline (SC-1).** `as_of` is a required parameter echoed in the result; the birth
   instant's tz, never the server's.
9. **Interface packet IP-9 (Pūrṇa owns the TS; L3 owns the sentinel).** `call_dasha_eligibility`
   and `kala_dasha_sandhi_get` obtain rows from the service (sidecar route) with the canonical id
   required; the wrapper resolves the omitted id to `DEFAULT_AYANAMSHA` and any legacy alias
   through the one map (SC-10) **at the wrapper** — the service itself requires the canonical id
   (`service.py:161-165` → SQL equality [R]; no alias resolver in the service, by design).
10. **Old vs new.** Positive: canonical chart, `as_of` a known AD midpoint → seven systems with
    states, instants, atomic-segment agreement. Negative: one system's read fails → whole request
    `unavailable` (unchanged). Boundary: `as_of = end_iso − 1 s` → membership true; `+ 1 s` →
    false; `hours_to_boundary` ≈ 0. Missing: a system with no admitted clause → `unqualified`,
    never dropped. Duplicated: four nakṣatra-family systems on one segment → one
    `independence_group`.
11. **Competent simpler baseline (F3).** The current route: `start_iso/end_iso` at instant grain,
    exact-pair agreement, a constant applicability flag unread, `LIMIT 400`, no coverage.
12. **Ablation (F3).** Serve the same question through the service and through the route on the
    same `as_of`: the served envelope must differ in exactly (i) agreement computed on atomic
    segments (overlapping-but-unequal periods now agree), (ii) per-system `completeness_state`, (iii)
    coverage/cap disclosure, (iv) `hours_to_boundary` — and be **identical** in lords and instants.
    If (i) never differs on the canonical chart, the F-13 fix is decorative for this native and the
    brief says so.

---

## §5 — Preservation, migration, history, rollback (contract §5) + fences

- **Preserved kernels** (`PRESERVE`): `tree_walk` hierarchy reconstruction; `intersect_segments`;
  `agreement_for`; `BAND_SCORE` bands (labelled); fail-whole-request; the `RuntimeError` on a
  failed self-test (`writer.py:156`); the seven-system assertion.
- **Changed** (`ENRICH_CORRECT`): instant columns read; B1/B2/B5 fields; the derived boundary
  object; `as_of`.
- **Qualified** (`QUALIFY_LIMIT`): the soft scalars; the constant applicability flag; prāṇa.
- **Integrated** (`INTEGRATE`): IP-9; concurrence rows offered to SC-6's owner.
- **Never restated** (§N.5): bounds, flags and `applies_to_this_chart_flag` are references to L1
  rows.
- **No table, no migration, no rows; no feature flag exists or is proposed** (F23) — the payload is
  additive; readers ignore new fields until they adopt them.
- **Hub rule.** `services/ka_dasha_kala` is inside the frozen **L4** digest closure via
  `ph_nimitta/dasha_consensus.py`; any change here shifts L4's writer digest → a coordinated
  cross-stream packet with a named owner; additive payload so `dasha_consensus.py` (id required,
  `:78-84`) and `ka_sangam.py` need no change first.
- **Upstream amendment requests (raised, not fabricated):** (a) **L1** — `applies_to_this_chart_flag`
  needs a real detector, and `ga_dashas_writer.py:1717`'s canonical-chart Aṣṭottarī condition
  applied to all charts is an upstream defect; (b) **L0** — qualify `conditions_for_use` prose into
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
| B inputs/DAG | declared `ga_dashas` — correct and real; Avadhi's constant import and Jivana's declared-not-read edge are documentation-only; no hidden read. T0; fan-out: Saṅgam, L4, Avadhi-vocab |
| C correctness | invariants: intervals half-open and non-overlapping within a system+level; child ⊂ parent; intersection commutative; whole-request failure on one system failure; **a service value ≠ its L1 row is a halt**. Golden: the canonical chart's seven systems; boundary: `end_iso ± 1 s`; differential: service vs route (§4.12). Detectors: the self-test's raise; the §7 fixtures |
| D data sufficiency | n/a for rows; **admitted applicability clauses are the gap** (L0/L1 requests) |
| E consumers | Saṅgam, L4, Avadhi-vocab (real); served routes (bypass — the defect); Jivana (declared, not read — Jivana brief decides) |
| F AI/product | per-system states, atomic-segment `dissent` rows (IP-2), `hours_to_boundary`, coverage machine-readable; `unqualified` shown, not hidden; the empty-with-wrong-default becomes impossible |
| G efficiency | no measured hotspot; **justified no-change** |
| H reliability | idempotent (no writes); self-test raises on failure; timeout from measured latency (stage 3); no credentials |
| I change packet | files in `may_touch`; base `9feac52d7`; additive payload; tests in §7; W2; coordinated L4-digest re-pin; `service_probes.py` untouched (D-CND-34) |
| J final evidence | this brief + the W2 landing (`fa9857f00`); §7 results; both review reports; IP-9 sentinel |

---

## §7 — Proof matrix (contract §6) — executable, detector named

| proof | fixture / boundary | expected | invariant | detector (fails when…) | owner |
|---|---|---|---|---|---|
| Positive | canonical chart, `as_of` = a known AD midpoint, canonical id | seven systems, each with `completeness_state` (`unqualified` today) + `t_start/t_end` instants | bounds = L1 `start_iso/end_iso` | any bound ≠ L1; any system missing a state | L3 |
| Positive (wrapper) | `ayanamsha_id` omitted at `call_dasha_eligibility` | resolved to `DEFAULT_AYANAMSHA`; rows returned | wrapper resolves | zero rows / `'lahiri'` | IP-9 (Pūrṇa code, L3 sentinel) |
| Negative | one system's L1 read raises | whole request `unavailable` | no partial payload | a partial result | L3 |
| Relevant influence | **gated on §10 decision 2** (no admitted clause exists today; F23 — a planned test is not a pass): flip one system's admitted-clause fixture | that system `unqualified → applied`; others unchanged | isolation | a second system moves | L3 (after L0) |
| Relevant influence (today) | change `next_dasha_start_iso` in the fixture by 1 h | `hours_to_boundary` changes by 1; lords unchanged | derivation | unchanged | L3 |
| Irrelevant control | reorder the seven systems in the request | identical payload | order-invariant | hash differs | L3 |
| Duplication/correlation | four nakṣatra-family systems agree on a segment | one `independence_group`; `declared_current_count`=1 | shared root | count = 4 | L3 |
| Context/missingness | wrong chart id; a system that ran and covers nothing vs one `unqualified` | reject; `silent` ≠ `not_applicable` | distinct | same reading | L3 |
| Boundary/precision | `as_of = end_iso − 1 s` / `+ 1 s` | membership flips; `hours_to_boundary` ≈ 0 both sides; L1's `sandhi_flag` unchanged (it is a period property) | `closed_open` | a date-grain answer; `sandhi_flag` restated | L3 |
| Delivery (sentinel) | sentinel `completeness_state='unqualified'` with reason on Kālacakra only | reaches `call_dasha_eligibility`'s envelope and the saved reading | survives | absent | L3 |
| Cap disclosure | 401 windows in the fixture | `truncated=true`, `returned=400`, `available=401` | disclosed | silent 400 | IP-9 |
| Revision | L1 regenerates `chart_dashas` | payload changes; no cache | fresh | stale | L3 |
| Value | frozen L3-Q01/Q05 questions before/after (baseline) | atomic-segment agreement and per-system states appear; the exact-pair route cannot show them | — | no distinction | baseline |
| Evaluation | n/a (no claim issued) | — | — | — | — |

Binding rows: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `time_basis`, `claim_grain`), B2
(`epistemic_class`, `completeness_state`, `operator_role`, `comparable_with`, `tier_basis`,
`source_qualification` on the band and prāṇa), B4 (`independence_group`, `declared_current_count`),
B5 (`coverage` in the seven-key shape). **DEMANDS** B3 (a content-addressed period identity from
SC-3's packet — L1 offers only a per-build `uuid4`). Layer tests 5/6/7/9 = the duplication,
context, boundary and delivery rows.

---

## §8 — Prioritization

Within the asset: (1) the wrong default + the cap (IP-9; PR #2695 content + `truncated`) → (2) B1
instants in the service (**precondition** for IP-9 routing) → (3) the served bypass (the
elevation: atomic-segment agreement + states) → (4) the scalar labels → (5) concurrence rows → (6)
the L1/L0 requests. T0 hub, W2; fan-out to Saṅgam and L4 — additive payload, coordinated packet.
Holds: IP-9 waits on Pūrṇa's queue; `applied` states wait on L0/L1.

---

## §9 — Disposition and target state

`INTEGRATE` + `ENRICH_CORRECT` + `QUALIFY_LIMIT` (service/probe terminal rule: availability,
correctness, failure semantics **and a product consumer** verified; no row-count proxy).
Data-plane: `PRODUCER_READY` for the enriched contract at stage 3; `CONSUMER_INTEGRATED` when
IP-9 is live at a `file:line` on `main` with the sentinel (D-H record). Campaign: `ANALYZED` →
`ENRICHED`; `FROZEN` only after an independent verifier. **Non-claims:** no `DATA_ACCEPTED`;
`VALUE_EVALUATED` N until the baseline shows the Q05 delta; every system serves `unqualified` until
L0/L1 supply a real applicability detector — *"it cannot earn full completion solely by returning
unavailable states"* (Strategy §7), so the upstream requests are on this asset's critical path.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Wire the served daśā routes to the service (IP-9, after the B1 delta), or declare the bypass intentional and retire the traversal API to research-only?** | **Wire, in that order.** The service is the only place atomic-segment agreement exists; the route's exact-pair agreement is the defect the service already fixed |
| 2 | **Raise the L1 amendment (a real detector for `applies_to_this_chart_flag`; the `:1717` hardcoded condition) and the L0 request (executable `conditions_for_use` clauses with page-grain citations; id vocabulary for `chara_karaka`/`naisargika`/`mudda`)?** | **Yes**, both bounded; until then every system serves `unqualified` with the reason |
| 3 | The concurrence rows' owner (SC-6) and the period identity (SC-3) | offered / demanded here; the owner rulings are the blueprint's |
| 4 | Do `eligibility_score`/`high_agreement_count` leave the payload once Saṅgam retires its `confidence_*` inputs (amendment 9)? | coordinate with Saṅgam's packet; label now, retire together |

---

## §11 — What is not verified here (§N.8: stated, not guessed)

1. PR #2695's content and state — no GitHub access from either the author or the reviewer session.
2. Live incidence of the zero-row default path; the canonical rows' `ayanamsha_id` — inferred from
   code pins [R], not queried.
3. Service-call latency — never measured.
4. Whether Kṣetra S3 reads `chart_dashas` (row in §1 carried from the disposition record) — not
   checked.
5. `origin/l3/kala-elevation-readiness` remote tip — code identity to HEAD verified locally instead.
6. No database query was run for this brief or its review.

## §12 — Review dispositions (v1.0 → v1.1)

F1 accepted (§2.4, §4.3, §5, §10.2); F2 accepted (§0); F3 accepted (§3, §4.2 ordering, §4.11–12);
F4 accepted (§2.4, §4.4, §7 boundary); F5 accepted (§2.4, §4.5, §10.4); F6 accepted (§1, §5, §10.2);
F7 accepted (§4.2); F8 accepted (§4.7, §7 cap row); F9 accepted — row replaced (§4.9, §7 wrapper
row); F10 accepted (§7 owner column); F11 accepted (§7 gated row); F12 accepted (frontmatter, §1);
F13 accepted (§1 file name); F14 accepted (frontmatter "commit"); F15 accepted (§2.3); F16 accepted
(§2.2, §5); F17 accepted (§2.3, §3); F18 accepted (§4.6); F19 accepted (§5 expanded); F20 accepted
(§2.3); F21 accepted — `dasha_query_state` (§2.3 wording: the score use at `:1445-1449` is what
matters); F22 accepted (§4.6, §7 DEMANDS); F23 accepted (§5); F24 accepted (§1); F25 accepted
(`must_not_touch`).
