---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_DASHA_KALA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review; APPROVED_FOR_EXECUTION only by native record
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / blob 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference (blueprint v5.0 §17.1); B-rows offered/demanded in §7
asset_or_interface_ids: ["ka_dasha_kala", "IP-9 (kala_dasha_eligibility default)", "SC-6 producer (clock concurrence rows)"]
goal_objective: "Make ka_dasha_kala the clock authority its registration claims: every served daśā answer carries per-system applicability, exact instants, sandhi and cross-system agreement from this service, and no served path re-implements the clock query against raw L1 with its own defaults."
source_revision: "9feac52d7 (l3/kala-layer-briefs; = origin/l3/kala-elevation-readiness tip 2026-09-24)"
accepted_upstream_contract: "L1_CONDITION_RELATION_CLOCK_CONTRACT/1.0/blob-99953b54749a794efee48760d718e387bc8743e2 (chart_dashas: start_iso/end_iso, sandhi_flag, next_dasha_start_iso, is_truncated_at_window_*); W2 first-frontier source 47131772b (dasha fails the whole request on one system read failure)"
implementation_owner: "<one writer, named at stage 3 — not the author of this brief>"
independent_review_owner: "Fable 5.1 review agent, fresh context (blueprint §17.1); report at briefs/reviews/REVIEW_KA_DASHA_KALA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_dasha_kala/{service,tree_walk,eligibility,intersection,writer}.py", "platform/python-sidecar/tests/l3/test_ka_dasha_kala*.py", "platform/python-sidecar/pipeline/orchestrator/service_probes.py (ka_dasha_kala clause only)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:296-360 (call_dasha_eligibility), platform-mcp/src/tools/kala_views/dasha_sandhi.ts"]
must_not_touch: ["chart_dashas / any ga_* writer (L1 authority, §N.5)", "platform-mcp/src/tools/kala_views/** except as an interface packet", "services/ph_nimitta/dasha_consensus.py (L4 reader; compatibility constraint)", "pipeline/orchestrator/writers/ka_sangam.py (reader; Saṅgam-owned)", "applied migrations", "WriterBase / orchestrator transaction contract"]
target_state_data_plane: "PRODUCER_READY for the service contract (stage 3); CONSUMER_INTEGRATED requires IP-9 to land in Pūrṇa's tree and the L3-owned sentinel to pass"
target_state_campaign: "ANALYZED (this brief) → OPTIMIZED/ENRICHED at stage 3; no t3 event exists for this asset today"
wave: "W2 (service proof); data-bound use of the concurrence rows W5"
shape: single asset, service/probe
evidence_base: >
  Source read directly on 9feac52d7 (marked [V]); Lane D §3 and T1 Frontier row for
  ka_dasha_kala, Lane E §3.1/§1 Q-K01/K03/K13, Lane F §2a/§2d, STATE.md ★ finding
  (2026-09-20/22, marked [A]); no database query was run for this brief.
does_not_authorize: any code, migration, grant, build or serving change. This brief proposes; the native rules.
changelog:
  - "1.0 (2026-09-24): first issue, from the six-stage template; awaiting independent review."
---

# `ka_dasha_kala` elevation brief — the clock authority

## §0 — The recommendation, in one paragraph

`ka_dasha_kala` is registered as the layer's clock authority and is, in code, the only asset that
knows which of the seven daśā systems **apply** to a chart, where their intervals **intersect**,
and where they **agree or fall silent** — exactly the three things L3-Q01, L3-Q05 and L3-Q13 ask
of a clock. None of that reaches the person: the served daśā route re-implements the clock query
as raw SQL over L1 with its own grouping and a wrong default ayanāṃśa, and the sandhi tool reads
L1 directly, so the service's applicability, agreement and hierarchy are computed for a self-test
and consumed by Saṅgam and L4 only. Recommendation: **`INTEGRATE` + `ENRICH_CORRECT`** — keep
the kernel (it is correct and already fail-closed), bind its result to the synergy binding's
temporal and qualification fields (instants from L1's `start_iso/end_iso`, `inclusivity`,
per-system `completeness_state`, `independence_group` = the shared natal-Moon root), make it the
first producer of **clock concurrence rows** (SC-6), and route `call_dasha_eligibility` and
`kala_dasha_sandhi_get` through it via one interface packet (IP-9). No table, no rows, no
orchestrator change. The one decision for the native: wire the live route to the service, or
declare the bypass intentional and retire the traversal API to research-only (§10).

---

## §1 — Already established (stage 0: reconcile, cite, do not re-derive)

| record | what it says | delta on this base |
|---|---|---|
| Contribution register §5 (REGISTER:137) | *"Clock retrieval, ancestry and system traversal. P/E/I/Q: precise ISO intervals, actual overlap and applicability/failed-system coverage; label approximate subdivisions. DP07/08."* | unchanged; the "label approximate subdivisions" obligation binds `_subdivide_prana` (§2.2) |
| Strategy §6.1 **L3-A02** | service probe across seven systems, zero rows; *"expose actual hierarchy, applicability, intervals, failed/silent systems and qualified overlap; no layer-local clock restatement."* W2 | unchanged |
| CURRENT_STATE §4.1 | service only; accepted L1 clocks; Sangam/Jivana/Kshetra; *"independent proof after physical clock data"* | Jivana **declares** it, does not read it (§2.3); Kṣetra reads `chart_dashas` via its own S3 |
| W0 field register | `service query → KaDashaKalaResult/EligibleWindow`; service-only payload with zero domain DML | unchanged |
| W2 first-frontier source `47131772b` | *"Dasha now fails the whole request when one named system read fails rather than returning a partial payload as complete"* [A: CURRENT_STATE §4.5] | present on this base (§2.2) |
| Lane D §3, T1 Frontier | writer = self-test only; **NOT-FOUND consumer** for the traversal API within `platform-mcp/src/tools`, `platform/src/lib/retrieval`, `routers/` | **corrected here [V]**: `KaDashaKalaService` is imported by `pipeline/orchestrator/writers/ka_sangam.py`, `services/ka_sangam/engine.py` and `services/ph_nimitta/dasha_consensus.py` (grep on this base, tests excluded). The gap is narrower and sharper: *no served route* uses it (§3) |
| Lane F §2a | `call_service_wrappers.ts:328` defaults `ayanamsha_id` to bare `'lahiri'`; an omitted parameter returns zero rows silently | **still true on this base [V]** — `:328` `?? 'lahiri'` while `:227` and `:595` in the same file use `DEFAULT_AYANAMSHA`; PR #2695 (open, not on `main`) carries the fix |
| Lane F §2d | `chart_dashas` is flat one-row-per-level (`level_n` + `lord_graha`); DP07 wants parent/child hierarchy | `tree_walk._fetch_level1/_fetch_children` reconstruct the hierarchy (§2.2) — the reconstruction rule is the thing to test |
| Synergy audit / binding B1 | no stream imports `ka_temporal`; `date.today()` and DATE grain across the spine | this service's `EligibleWindow` grain is the question §3 answers |
| Blueprint v5.0 §3.5 row 2, §16.2 | hub imported by Avadhi (constant), Saṅgam (service), L4 `dasha_consensus`; **inside the frozen L4 digest closure** — changes are a coordinated cross-stream packet | binds §8 |
| KALA_DELEGATED_DECISIONS D-H | `CONSUMER_INTEGRATED` is an acceptance record with a live call path + L3-owned sentinel | binds §9 |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Identity and registration [V seed]
`asset_registry_seed.ts:2252-2260`: `storage_type: 'service'`, `target_table: null`, `count_sql:
null`, `depends_on: ['ga_dashas']`, `scope: 'per_chart'`, `estimated_seconds: null` (correctly
null — no detector), `asset_kind: 'service'`, `catalog_status: 'DRAFT'`. Live registry agrees
(Lane D §3 [A]).

### 2.2 What the code is [V]
- **Writer** `services/ka_dasha_kala/writer.py:1-40`: self-test only — asserts the seven systems
  (`vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra`) are present in
  `chart_dashas` for the canonical chart under `lahiri_chitrapaksha`, that a query window returns
  non-empty valid intervals (`start_date < end_date`), writes `service_health`/`selftest_detail`
  to `asset_registry`, returns `WriterResult(rows_written=0)`. Never commits; never writes
  `asset_throughput`. Conformant to the frozen contract.
- **Service** `service.py:77-252`: `KaDashaKalaService(db_conn).query(...)` →
  `KaDashaKalaResult` of `EligibleWindow`s plus `CrossDashaAgreement` (`:32,:39,:59`);
  `confirm_systems_present` (`:252`).
- **Traversal** `tree_walk.py:47-168`: `DashaInterval`; `_fetch_level1` / `_fetch_children`
  rebuild the parent/child hierarchy from the flat L1 rows; `walk_eligible_intervals`;
  **`_subdivide_prana(interval, n_subdivisions=9)`** (`:125`) — an *approximated* subdivision
  (nine equal parts), not an L1 fact.
- **Eligibility** `eligibility.py:18-69`: `EligibilityBand` enum; `score_eligibility`;
  `is_eligible_for_pruning` — the band-pruning that Saṅgam consumes.
- **Intersection** `intersection.py:38-108`: `SupporterRef`, `IntersectionSegment`,
  `intersect_segments(intervals)` (actual interval intersection, not date equality — U02's
  requirement), `agreement_for(start, end, segments) → AgreementSummary`.
- **Failure semantics**: one named system read failing fails the whole request (W2 source
  `47131772b` [A]; the assertion in `writer.py` self-test reads the same contract).

### 2.3 Consumers (search boundary: `platform/python-sidecar`, `platform-mcp/src`, `platform/src`, tests excluded) [V]
| consumer | what it reads | role |
|---|---|---|
| `pipeline/orchestrator/writers/ka_sangam.py`, `services/ka_sangam/engine.py` | `KaDashaKalaService` (daśā score per date; R-6 RRV-08 marks `availability['dasha']='unavailable'` when no service) | `applicability` / `computation` |
| `services/ph_nimitta/dasha_consensus.py` | `KaDashaKalaService` (L4 daśā consensus; default `ayanamsha_id='lahiri'` at `:157` [A: Lane F]) | `computation` (L4, sealed) |
| `pipeline/orchestrator/service_probes.py:871+` | DB-free proxy probe (D-CND-34) | probe |
| `writers/ka_avadhi.py:29` | `ALL_DASHA_SYSTEMS` constant from `tree_walk` (undeclared edge, vocabulary only) | `relevance_navigation` |
| `writers/ka_jivana_parva.py` | **declares** `ka_dasha_kala` in `depends_on`; reads `chart_dashas` directly (`:85-90` [V]) | declared, not read |
| **served routes** | `call_dasha_eligibility` (`call_service_wrappers.ts:296-360`): raw `SELECT … FROM chart_dashas` with its own grouping and `?? 'lahiri'` (`:328,:357`) [V]; `kala_dasha_sandhi_get` (`kala_views/dasha_sandhi.ts`): reads L1 directly [A: T1] | **bypass** |

**Live-path statement.** The service's applicability, hierarchy and agreement reach Saṅgam and
L4 today and reach **no served answer**. The bypass route is live and user-reachable.

### 2.4 Epistemic class and authority of the important fields
| field | class (F04) | authority | note |
|---|---|---|---|
| interval bounds | `COMPUTED_FACT_CONFIGURATION` | L1 `chart_dashas` (`start_iso/end_iso`, `start_date/end_date`) | the service must reference, never restate (§N.5) |
| `sandhi_flag`, `next_dasha_start_iso`, truncation flags | computed fact | L1 | present at L1 [A: Lane E §3.1]; whether `tree_walk` carries them is **not verified here** (§11) |
| eligibility band | `INTERPRETIVE_INFERENCE` (engineered) | this service | must be labelled as such, never as a classical rule |
| per-system applicability | `QUALIFIED_RULE` **where an admitted rule exists**; else `unqualified` | L0 (DP02) — **no admitted applicability rule per system is cited anywhere in this service** [V: no citation strings in `eligibility.py`/`tree_walk.py`] | §4 item 3 |
| prāṇa subdivision | approximation | this service | must be labelled `approximated` (register obligation) |
| `CrossDashaAgreement` | computed relation over computed facts | this service | the concurrence producer (SC-6) |

### 2.5 Position on both ladders
Data-plane: `PLAN_REVIEWED`; W2 service source accepted at `47131772b` — `PRODUCER_READY` for the
*self-test* contract only. t3: **no event**. Cost: trivially buildable (bounded reads of
`chart_dashas`, no ephemeris); service-call latency **unmeasured** (never cite
`estimated_seconds`, which is correctly null here).

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Ask the served daśā question for the canonical chart with `ayanamsha_id` omitted → `call_dasha_eligibility` runs `SELECT … FROM chart_dashas WHERE chart_id=$1 AND ayanamsha_id='lahiri' …` → **zero rows**, no error, presented as "no active windows" [V code path; zero-row outcome A: Lane F §2a, canonical rows are under `lahiri_chitrapaksha`]. Ask the same with the id supplied → rows, but **no per-system applicability, no agreement, no sandhi hour** — the service that computes those is not on the path |
| Evidence | `call_service_wrappers.ts:328` (`?? 'lahiri'`), `:336-357` (own grouping over the flat rows); `service.py:90` (`query`), `intersection.py:108` (`agreement_for`) unreached from any served route [V]; `dasha_sandhi.ts` reads L1 directly [A: T1] |
| Expected contract | Strategy L3-A02 (*"expose actual hierarchy, applicability, intervals, failed/silent systems and qualified overlap"*); L3-U02 (*actual simultaneous interval intersections with parent hierarchy, applicability and silent/failed states*); Product §7.1 (*"none found" must not become reassurance*); SC-10 |
| Defect class | **unserved** (the qualified object exists and is not on the served path) + **wrong context** (a default that silently changes the subject's convention) |
| Impact | L3-Q01's *"which qualified clocks are engaged"* and Q-K01's *applicable vs merely computable* are unanswerable at the served surface; Q-K13's boundary-to-the-hour is unanswerable (date grain); Q-K06's cross-clock agreement is re-derived per surface or asserted empty (`dissent: []`); a silent empty masquerades as "no eligible window" |
| Non-claim | Live incidence of the empty-result path is not measured here; doctrinal validity of any system's applicability rule is not established (it is L0's, §4 item 3); no claim that the service's output is *better* than the raw query — that is the ablation (§4.7) |

---

## §4 — The semantic delta (contract §4) — smallest sufficient change

1. **L3-Q served.** Q01 (*which exact clocks are engaged* — hierarchy + applicability), Q05 (*why
   timing methods disagree* — `CrossDashaAgreement` as data, silent/failed systems distinct from
   dissent), Q13 (*what reaches the person* — the served route carries the same object the
   service computes). Partially Q06 (chapter boundaries). Cannot serve Q02/Q08 (no windows, no
   search). Lane E's Q-K01, K03, K06, K13 are the working forms.
2. **Typed qualification (binding B2), no scalar.** Every `EligibleWindow` carries
   `epistemic_class` (`COMPUTED_FACT_CONFIGURATION` for bounds; `INTERPRETIVE_INFERENCE` for the
   eligibility band), per-system `completeness_state` ∈ the six F06 values — **`applied` only where
   an admitted applicability rule exists for that system and chart; `unqualified` where the system
   is computed but no rule is cited; `unavailable` where the L1 read failed; `inapplicable` where
   a cited rule excludes it** — `operator_role='applicability'`, `comparable_with` (`self` within
   one system; `different_convention` across systems — a Vimśottarī AD and a Yoginī period are
   not the same scale), `tier_basis='relative_uncalibrated'` on the band.
3. **Applicability is a source obligation, not a service invention.** The service today has no
   admitted per-system applicability rule (BPHS's conditions for Aṣṭottarī, Ṣoḍaśottarī etc. are
   classical doctrine that L0 must qualify — DP02). Until L0 admits them, every non-Vimśottarī
   system is served `unqualified`, honestly. This brief **raises the L0 request** (a bounded
   amendment: `bg_dasha_systems` applicability clauses with page-grain citations) and does not
   fabricate the rule.
4. **DP07 fields.** `t_start`, `t_end` as `timestamptz` from L1 `start_iso/end_iso` (never the DATE
   columns), `inclusivity='closed_open'` declared, `time_basis='event_instant'`,
   `claim_grain='instant_grain'`; parent id; `sandhi_flag`, `next_dasha_start_iso`,
   `is_truncated_at_window_start/end` carried through; prāṇa subdivisions stamped
   `claim_grain='approximated'` with `n_subdivisions`.
5. **Concurrence rows (SC-6 offer).** `agreement_for` becomes the producer of
   `{chart, interval, clock_id, verdict ∈ {supports, opposes, silent, not_applicable},
   jurisdiction, method_version}` — `not_applicable` for a system without an admitted rule,
   `silent` for a system that ran and named nothing — with `independence_group` declaring the
   shared root: the nakṣatra-family systems (Vimśottarī, Yoginī, Aṣṭottarī, Kālacakra) share the
   natal Moon's nakṣatra; `basis='declared_lineage'`, never "demonstrated".
6. **Time discipline (SC-1).** No `date.today()`; `as_of` is a parameter and is echoed in the
   result; the birth instant's tz offset, never the server's.
7. **Interface packet IP-9.** `call_dasha_eligibility` and `kala_dasha_sandhi_get` obtain their
   rows from the service (sidecar route) and their default from `DEFAULT_AYANAMSHA`; the raw SQL
   path is retired *after* the sentinel passes. Pūrṇa owns the TS code; L3 owns the sentinel.
8. **Old vs new.** Positive: the canonical chart with `ayanamsha_id` omitted → rows under the
   canonical id, with per-system states. Negative: a system whose L1 read fails → whole request
   `unavailable` (unchanged, W2). Boundary: an instant inside a sandhi → `sandhi_flag=true` and
   the hour survives. Missing: a system with no rule → `unqualified`, never dropped. Duplicated:
   four nakṣatra-family systems agreeing → one `independence_group`, not four witnesses.
9. **Competent simpler baseline.** The current raw query over `chart_dashas` by date with the
   caller-supplied ayanāṃśa: lords and date-grain bounds, no applicability, no agreement.
10. **Ablation.** Route the served tool through the service and then remove the service (raw
    query): the served envelope must lose exactly `completeness_state` per system, `sandhi` at hour
    grain, and the concurrence rows, and nothing else. If it loses nothing, the service adds
    nothing and this brief's disposition is wrong.

---

## §5 — Preservation, migration, history, rollback (contract §5) + fences

- **Preserved kernels** (`PRESERVE`): `tree_walk` hierarchy reconstruction; `intersect_segments`
  (real intersection); `agreement_for`; the eligibility bands (as engineered inference, labelled);
  the fail-whole-request semantics; the self-test's seven-system assertion.
- **Changed** (`ENRICH_CORRECT`): the result payload gains the B1/B2 fields; `_subdivide_prana`
  gains its `approximated` label; `query` takes `as_of`.
- **Integrated** (`INTEGRATE`): IP-9 route; concurrence rows offered to SC-6's owner.
- **Never restated** (§N.5): bounds and flags are references to L1 rows; a service value that
  disagrees with `chart_dashas` is a halt-worthy bug, not a stored divergence.
- **No table, no migration, no rows.** The service stays a service (A01–A04); concurrence rows are
  an *offer* to whichever partition SC-6's owner ruling names (blueprint §3.3 proposes
  `ka_kala_darshana`), not a table this brief creates.
- **Hub rule.** `services/ka_dasha_kala` sits inside the frozen **L4** digest closure via
  `ph_nimitta/dasha_consensus.py`; any change here shifts L4's writer digest. Execution is a
  coordinated cross-stream packet with a named owner (elevation plan §4 rules), not an in-stream
  edit; backward-compatible payload (additive fields) so `dasha_consensus.py` and `ka_sangam.py`
  need no change at first.
- **Cascade**: none (no owned table). **Rollback**: the additive payload is feature-flagged at the
  service boundary; IP-9's route change rolls back by re-pointing the wrapper.
- **Protected classes**: untouched.

---

## §6 — Analysis lenses A–J (skill contract)

| lens | answer |
|---|---|
| A identity | `ka_dasha_kala`, L3, service/probe; epistemic type: deterministic derivation over L1 facts + one engineered inference (band) + one approximation (prāṇa); layer placement correct — it temporalizes L1 clocks for L3 consumers; disposition `INTEGRATE + ENRICH_CORRECT` |
| B inputs/DAG | declared `ga_dashas` only — correct; Avadhi's constant import and Jivana's declared-not-read edge are documentation-only (cluster: hub §16.1). No hidden read. Critical path: T0; fan-out 3 (Saṅgam, L4, Avadhi-vocab) |
| C correctness | invariants: intervals non-overlapping within a system+level; child ⊂ parent; intersection commutative; whole-request failure on one system failure. Golden: the canonical chart's seven systems; boundary: a sandhi instant; differential: service vs raw query on the same `as_of` (must differ only in the added fields). Detectors: the self-test + the new fixtures in §7 |
| D data sufficiency | n/a for rows; **applicability rules are the genuine gap** (L0, DP02) — not this service's to fill |
| E consumers | Saṅgam, L4, Avadhi-vocab (real); served routes (bypass — the defect); Jivana (declared, not read: either read it or drop the edge — Jivana brief) |
| F AI/product | machine-readable states per system; `dissent` populated from concurrence rows (IP-2); honest `unqualified` shown, not hidden; the empty-with-wrong-default becomes impossible |
| G efficiency | no measured hotspot; bounded reads; **justified no-change** on performance |
| H reliability | idempotent (no writes); no resume needed; timeout from measured call latency (to be measured at stage 3); no credential exposure |
| I change packet | files in `may_touch`; base `9feac52d7`; additive payload; tests in §7; W2; coordinated L4-digest re-pin |
| J final evidence | pre-change: this brief + the W2 acceptance; post-change: §7 results, review report, IP-9 sentinel |

---

## §7 — Proof matrix (contract §6) — executable, detector named

| proof | fixture / boundary | expected | invariant | detector (fails when…) |
|---|---|---|---|---|
| Positive | canonical chart, `as_of`=a known AD midpoint, `ayanamsha_id` omitted | rows under `lahiri_chitrapaksha`; seven systems each with a `completeness_state` | bounds equal L1 `start_iso/end_iso` | any bound ≠ L1 row; any system missing a state |
| Negative | one system's L1 read raises | whole request `unavailable` | no partial payload | a partial result is returned |
| Relevant influence | flip one system's admitted-rule fixture from absent to present | that system `unqualified → applied`; nothing else changes | other systems' states unchanged | a second system's state moves |
| Irrelevant control | reorder the seven systems in the request; alias `Lahiri` vs `lahiri_chitrapaksha` | identical payload | order-invariant | payload hash differs |
| Duplication/correlation | four nakṣatra-family systems agree on an interval | one `independence_group` (roots: natal Moon nakṣatra) | `declared_current_count`=1 | count = 4 |
| Context/missingness | wrong chart id; a system that ran and found nothing vs one with no rule | reject; `silent` vs `not_applicable` distinct | states never collapse | both read the same |
| Boundary/precision | `as_of` = `end_iso` − 1 s and + 1 s of an AD | membership flips; `sandhi_flag` true inside | `closed_open` | date-grain answer (same for both) |
| Delivery (sentinel) | a sentinel `completeness_state='unqualified'` on Kālacakra only | reaches `call_dasha_eligibility`'s response and the saved reading | survives the wrapper | absent from the served envelope |
| Revision | L1 regenerates `chart_dashas` | payload changes; nothing cached | no stale cache | old bounds served |
| Value | frozen L3-Q01/Q05 questions before/after (baseline) | the applicability and agreement distinctions appear; the raw query cannot show them | — | no distinction in the delta |
| Evaluation | n/a (no claim issued) | — | — | — |

Binding rows: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `time_basis`, `claim_grain`), B2
(`epistemic_class`, `completeness_state`, `operator_role`, `comparable_with`, `tier_basis`), B4
(`independence_group`), B5 (`coverage` = systems requested/consulted/unavailable). **DEMANDS**
nothing from another L3 asset (L1 only). Tests 5/6/7/9 of the Layer contract are the rows above
marked duplication, context, boundary, delivery.

---

## §8 — Prioritization

Within the asset: (1) the wrong default (correctness; IP-9; one line, PR #2695 content) → (2) the
served bypass (unserved object; the elevation) → (3) applicability states with the L0 request →
(4) concurrence rows → (5) labels on the approximation. In the layer: **T0 hub**, W2, no
P-candidate; fan-out to Saṅgam (chokepoint) and L4 — which is why the payload is additive and the
change is a coordinated packet. Holds: none of this asset's own; IP-9 waits on Pūrṇa's queue.

---

## §9 — Disposition and target state

**Disposition:** `INTEGRATE` + `ENRICH_CORRECT` (service/probe terminal rule: availability,
correctness, failure semantics **and a product consumer** verified; no row-count proxy).
**Data-plane target:** `PRODUCER_READY` for the enriched contract at stage 3;
`CONSUMER_INTEGRATED` only when the IP-9 route is live at a `file:line` on `main` and the sentinel
passes (D-H record). **Campaign target:** `ANALYZED` now; `ENRICHED` at stage 3; `FROZEN` only
after an independent verifier. **Non-claims:** no `DATA_ACCEPTED` (no data); `VALUE_EVALUATED`
is N until the baseline shows the Q01/Q05 delta; applicability rules remain `unqualified` until L0
admits them — *"it cannot earn full completion solely by returning unavailable states"* (Strategy
§7), so the L0 request is on the critical path of this asset's value, not optional.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Wire the served daśā routes to the service (IP-9), or declare the bypass intentional and retire the traversal API to research-only?** | **Wire.** The service is the only place applicability and agreement exist; retiring it would make Q-K01/K06 permanently unanswerable at the surface and leave a bypass with a wrong default as the layer's clock |
| 2 | Raise the L0 request for admitted per-system applicability rules (DP02, page-grain citations in `bg_dasha_systems`)? | **Yes**, as a bounded amendment; until then every non-Vimśottarī system serves `unqualified` |
| 3 | The concurrence rows' owner (SC-6) | this brief only *offers* rows; the owner ruling is the blueprint's (§3.3 SC-6) |

---

## §11 — What is not verified here (§N.8: stated, not guessed)

1. Whether `tree_walk` currently reads `start_iso/end_iso` or the DATE columns — the loader's
   SELECT was not read line-by-line in this session; the delta is stated as a requirement either way.
2. Whether `dasha_sandhi.ts` reads L1 directly — carried from T1 [A], not re-opened.
3. Live incidence of the zero-row default path; the canonical rows' `ayanamsha_id` value is Lane F's
   [A].
4. Service-call latency — never measured; `estimated_seconds` is null and must stay uncited.
5. Whether Saṅgam's and L4's imports *use* the service at run time or only import it — the grep is
   file-level [V]; the call sites are the Saṅgam packet's and L4's to confirm.
6. No database query was run for this brief.
