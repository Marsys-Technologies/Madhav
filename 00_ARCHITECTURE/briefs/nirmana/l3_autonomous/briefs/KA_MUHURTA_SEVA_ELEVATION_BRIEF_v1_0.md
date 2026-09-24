---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_MUHURTA_SEVA_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_MUHURTA_SEVA_v1_0.md, 20 findings, F1 BLOCKER); v1.1 dispositions each
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows + asset-local fields in §7
asset_or_interface_ids: ["ka_muhurta_seva", "sidecar routes routers/muhurta_score.py + routers/muhurat.py (re-pointed through the service — coordinated)", "IP-10 (NEW, proposed for blueprint §12.2): kala_elect_get / muhurta_finder election packet — today on the L4 phala path over panchanga_daily, not on this service", "cross-asset item: panchanga_daily single-observer location (L0 table + L4 reader) — raised, not owned"]
goal_objective: "Make ka_muhurta_seva the one election engine its registration claims: a typed verdict built as an extension of the finder's existing per-factor breakdown (calendar / personal / weight-source carried separately, vetoes as vetoes, the horizon and cap disclosed, the location actually used typed on every answer, a named comparator from the blueprint's vocabulary) — and route the two sidecar election endpoints through it, so that 'the best window in your range' can never be read as 'a good window'. The chart-bound served election (kala_elect_get) is a separate packet: it does not touch this service today, and its real hazard lives in a single-observer L0 table."
source_revision: "9feac52d7 (l3/kala-layer-briefs; cited files unchanged to HEAD)"
accepted_upstream_contract: "L0 pañcāṅga engine (panchang_engine; accepted L0 revision f6fed12c7); L0 panchanga_daily is a SINGLE-OBSERVER table (Bhubaneswar: scripts/panchanga_daily_writer.py:42-46,205; migration 427:41-43) — its use for every chart's election is the cross-asset hazard §3b raises; L1 chart_facts janma nakṣatra for the overlay"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; v1.0 report at briefs/reviews/REVIEW_KA_MUHURTA_SEVA_v1_0.md; re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_muhurta_seva/{service,writer}.py", "platform/python-sidecar/routers/muhurta_score.py and routers/muhurat.py (sidecar served routes; re-pointed through the service — coordinated, they are live)", "platform/python-sidecar/tests/test_ka_muhurta_seva.py, tests/l3/test_muhurta_score_sidecar_route.py", "FENCE DECISION (§10.1): platform/python-sidecar/panchang_engine/muhurat/finder.py:101-141 (_score_breakdown) — the typed verdict extends this breakdown; either the service builds the verdict from the returned breakdown (no finder edit) or finder gains fields (needs the fence lifted)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:405-513 (call_muhurta_score descriptor + a typed location_used field), asset_registry_seed.ts:2267 (catalog correction line)", "IP-10 (proposed, Pūrṇa-owned TS + L3 sentinel): platform-mcp/src/tools/kala_views/elect.ts, platform-mcp/src/tools/muhurta_finder.ts, L4_phala/query_muhurat.ts"]
must_not_touch: ["panchang_engine/** except the fence decision above (shared Swiss-state span; L0 pañcāṅga authority)", "scripts/panchanga_daily_writer.py, panchanga_daily (L0 table — hazard raised, not edited)", "brahmagyan/phala/muhurta.py (L4 — the served election's actual engine; IP-10 packet, own owner)", "pipeline/orchestrator/writers/ph_muhurta.py (L4, sealed — its proxy formula is recorded as an L4-owned item)", "pipeline/orchestrator/writers/ka_sangam.py + services/ka_sangam/engine.py:700-735 (the always-raising .score call is Saṅgam-owned)", "pipeline/orchestrator/writers/ka_vighnakara.py (reads compute_panchang directly; its brief)", "platform-mcp/src/tools/kala_views/** except as an interface packet", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the typed verdict (stage 3); CONSUMER_INTEGRATED when routers/muhurat.py + routers/muhurta_score.py serve the verdict through the service with the L3-owned sentinel; kala_elect_get integration is IP-10's, not this brief's"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; no t3 event today"
wave: "W2 (service proof); W7 (accepted-input use)"
shape: single asset, service/probe, global scope
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted are marked [R] with the
  reviewer's file:line; Lane D §10, T1 Frontier row, Lane E Q-K09/K10 §5.8, Lane F P11 [A]; no
  database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions — F1 (BLOCKER) the consumer map was wrong: NO live caller receives a value from service.py (three engines traced; the only .score call, ka_sangam/engine.py:722, always raises); delta re-scoped to the two sidecar routes + a proposed IP-10 for kala_elect_get; F2 the route is declared global with no chart input — the personal-default hazard moved to panchanga_daily (L0 single-observer) read by phala/muhurta.py:1317, raised cross-asset; F3 finder's per-factor breakdown (tara_bala only with native_chart) is existing capital the verdict extends; F4 criterion = {nearest, strongest, robust} + vetoed_excluded boolean; F5 ph_muhurta/ka_vighnakara dropped as float readers, real readers named; F6 Negative split into PRESERVE regression + route-body detector; F7 Delivery restated against routers/muhurat.py, IP-10 proposed with elect.ts's existing tara_bala_status; F8 undertaking → weight_source; F9–F20 scale, inclusivity, test paths, estimated_seconds removed, weights hash, five-of-seven, effect size, tz default recorded, catalog correction, Evaluation row + tiers; binding: B5 shape, B2 overclaim withdrawn, B3 window id, B1 time_basis, B4 n/a stated."
  - "1.0 (2026-09-24): first issue."
---

# `ka_muhurta_seva` elevation brief — election as three claims, not one number

## §0 — The recommendation, in one paragraph

`ka_muhurta_seva` is registered as the layer's election service, and **nothing served consumes a
value from it** [R]. Three election engines run in this codebase: (1) `services/ka_muhurta_seva/
service.py` → `panchang_engine/muhurat/finder.py` — called with a value received only by its own
self-test (`writer.py:220-221` calls `score_muhurat` directly, bypassing even that) and by
`ka_sangam/engine.py:722`, the **sole `.score(` call in production, which always raises**
(`event='general' ∉ EVENTS_MVP`, documented `:700-712` [R]); (2) the sidecar routes
`routers/muhurta_score.py:48-50,123` and `routers/muhurat.py:20,139`, which import
`panchang_engine.muhurat` **directly** [R]; (3) the served chart-bound election `kala_elect_get`
(`elect.ts:62,872` → `muhurta_finder.ts:32-34` → `L4_phala/query_muhurat.ts:124` → `brahmagyan/
phala/muhurta.py:1894`), which imports neither the service nor the finder and derives
`panchanga_quality` from **`panchanga_daily`** (`:1317,:1329-1330`) — a **single-observer table
computed at Bhubaneswar** (`panchanga_daily_writer.py:42-46,205`; migration `427:41-43` [R]) — for
every chart. The sealed L4 `ph_muhurta.py` uses a proxy formula with the comment *"ka_muhurta_seva
not available at writer import time"* (`:134-136`, `source:'ka_muhurta_seva_proxy'` `:160` [R]).
So the seed's *"Location mandatory — no silent Bhubaneswar default"* (`asset_registry_seed.ts:2267`)
and the descriptor's *"the same primitive ph_muhurta calls internally"* (`call_service_wrappers.ts:
415-416,489-490`) are both false at source [R]. Recommendation: **`INTEGRATE` + `ENRICH_CORRECT` +
`QUALIFY_LIMIT`** — a typed `MuhurtaVerdict` built as an **extension of the finder's existing
per-factor `breakdown`** (`finder.py:101-141,246-255`; `tara_bala` present only with a native chart
`:139-140` [R] — the personal-overlay presence is already detectable); the two sidecar routes
**re-pointed through the service** so the registered engine is the served engine on the global
surface; `criterion ∈ {nearest, strongest, robust}` (blueprint Q7 vocabulary); `location_used`
typed; coverage in the B5 shape with the horizon's true inclusivity; and the chart-bound election
handled as a **proposed IP-10** whose real hazard — one observer's sunrise for every chart — is
raised to L0/L4 and not pretended to be this service's fix. Decisions: the finder fence and IP-10 (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:158) | *"Calendar/action-time computation and search service. P/I/Q: calendar correctness, personal suitability and outcome are distinct; real undertaking constraints and scope. DP07/09."* | the three-claims obligation |
| Strategy §6.1 **L3-A03** (`:273`) | *"Test actual time/location and undertaking constraints; distinguish general calendar from personal feasibility and outcome expectation. Service-health proof alone is insufficient."* | unchanged — and "actual location" is the §3b hazard |
| Strategy **L3-Q10** (`:71`); §3 (`:97`) *"no universal ranking or hidden hard cap"* | value frame | — |
| Product §3.11 (`:168-172`); §10 (`:365`) *date/location/time-zone fidelity*; §5.2 (`:223`) | reusable partial capital; fidelity; no scalar substitutes | binds §9 |
| VA §4.4 (`:152-158`) | the lattice's reference location and midpoint approximation are disclosed; consumers must preserve location/horizon/precision | the disclosure `kala_elect_get` does not carry (IP-10) |
| W0 register #14 (`:33,:640-644`) | `score / find_windows → float / MuhuratWindow` incl. **`windows[].breakdown`** | the breakdown is registered capital (F3) |
| Lane D §10 (`:532-566`) | LIVE, medium confidence; *"not independently re-confirmed beyond that comment"* | **overturned** [R]: the "reuse" is of `score_muhurat` by the routes, not of this service |
| Lane E Q-K09/K10, §5.8 (`:961-967`) | `elect.ts:288-290` honest empty; `:296-299` falsifier about the window — *do not "fix"* | preserved; and `elect.ts` already types the personal overlay: `lane_f.tara_bala_status ∈ {applied, unavailable_no_janma_nakshatra}` (`muhurta_finder.ts:333`), `honestEmptyCoverage('tara_bala_personal_star_veto')` (`elect.ts:314-317`) [R] |
| DAG reconciliation §2 (`:33`); migration 676 | live `depends_on = {}`; seed `['ka_graha_sancara']` (`:2274` [V]) — permanent divergence | unchanged |
| Blueprint v5.0 §9 Q7 (`:671`), §12.1 (`:748`) | `criterion ∈ {nearest, strongest, robust}` | v1.0's `nearest_clean/best_scored` **withdrawn** (F4) |
| Blueprint §12.2 (`:751-763`) | **no election interface packet exists** | IP-10 proposed (§4.10) |
| Migration `968:76` | confirms `ph_muhurta`'s proxy | L4-owned item, recorded |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`asset_registry_seed.ts:2263-2276`: `storage_type: 'service'`, `depends_on: ['ka_graha_sancara']`
(live `{}`), `scope: 'global'`, `asset_kind: 'service'`; description `:2267` false at source.
Cost: unmeasured (`KALA_COST_PROFILE_v1_0.md` pending).

### 2.2 The code [V]/[R]
- **Writer** `services/ka_muhurta_seva/writer.py`: FORENSIC self-test on **five of the seven**
  CLAUDE.md §B anchors (`:65-69`); knockout check (`:237-273`); `WriterResult(rows_inserted=0)`
  (`:137-142`); note it calls `score_muhurat` directly (`:220-221`), not the service.
- **Service** `service.py`: `_validate_location` (`:37-60`, raises on None/missing keys);
  `score(...) -> float` on the **0..100** scale (`:78-119`, `:101`); optional overlay "un-floor"
  (`:93-96`); `find_windows(..., top_n=10)` (`:121-169`); module delegates (`:178-211`).
- **Finder** `panchang_engine/muhurat/finder.py`: `_in_inauspicious` event-independent veto
  (`:58-76`); **`_score_breakdown` (`:101-141`)** keys `tithi, nakshatra, vara, yoga, planet` +
  `tara_bala` **only when `native_chart`** (`:139-140`); `score_muhurat` (`:148-196`, 0..100);
  `find_muhurat` (`:203-261`): horizon **inclusive both ends** (`:216`, `while current <= date_to`
  `:243`), window instants `sunrise_utc → sunset_utc` (`:250-251`), attaches `breakdown` per window
  (`:246-255`); `MuhuratWindow.breakdown` (`panchang_engine/types.py:280`) [R]. Weights:
  `muhurat_weights.yaml` — tāra weight **0.10 of 1.00** (`:41,48`); source comments per family
  (MC/BS/MMP/DP abbreviations), no machine-readable citation field; `Version: 1.0` in a comment only
  (`:19`) [R].
- **Routes**: `routers/muhurta_score.py` — request `{datetime_utc, event_class, ayanamsha_id}`
  (`:61-69`), **no chart or location input**, default location (`:35-39,:54`), `score_muhurat`
  direct (`:48-50,:123`), response `note` string (`:131-136`); `routers/muhurat.py` — `find_muhurat`
  direct (`:20,:139`), `tz_offset_minutes: int = Field(330, …)` silent IST default (`:34` [R]),
  serves `windows[].breakdown` (`:44`); UI hook `useMuhuratFinder.ts:62-73` passes tz explicitly.
- **Served election** `elect.ts` → `muhurta_finder.ts` → `phala/muhurta.py` on `panchanga_daily`;
  horizon default `new Date()`+90d (`elect.ts:229-232`, Pūrṇa-owned); finder input carries no
  location (`:862-869`); scores on 0..1 (`muhurta_finder.ts:280`) [R].

### 2.3 Consumers (boundary: `platform/python-sidecar`, `platform/src`, `platform-mcp/src`; tests excluded) [R]
| consumer | reads | role |
|---|---|---|
| `writers/ka_sangam.py:40,329`; `services/ka_sangam/engine.py:722` | `.score(event='general')` — **always raises** | dead call (Saṅgam-owned) |
| `writers/ka_vighnakara.py:197-198,613-620` | instantiates; calls `compute_panchang` directly; reads tithi only | vocabulary/probe — not a float reader |
| `writers/ph_muhurta.py:134-136,160` (L4 sealed) | **proxy formula**, never this service | none (L4 item) |
| `routers/muhurta_score.py:123`, `routers/muhurat.py:139` | `panchang_engine.muhurat` **directly** | served, bypass |
| `kala_elect_get` / `muhurta_finder.ts` | `phala/muhurta.py` on `panchanga_daily` | served, different engine |
| `writer.py:220-221`; `service_probes.py:975-1010` | `score_muhurat` direct | probe |
| `ka_graha_sancara.py:91` | a comment | — |

**Live-path statement.** No live value-receiving caller of `service.py` was found within scope.
Two served sidecar routes run the same finder without the service; the chart-bound election runs
a third engine over a single-observer table.

### 2.4 Epistemic class
| quantity | class | authority | note |
|---|---|---|---|
| pañcāṅga at date+location | `COMPUTED_FACT_CONFIGURATION` | L0 engine (live) / `panchanga_daily` (one observer) | the observer *is* the subject of the fact |
| per-family weights (YAML) | `QUALIFIED_RULE` only if cited per family; else engineered | YAML comments name sources; no field | `source_qualification` owed; version = hash of loaded dict (F15) |
| tāra-bala overlay | qualified rule (nava-tārā), weight 0.10 | finder + L1 janma nakṣatra | present in `breakdown` only with `native_chart`; without it the vivāha maximum is 90/100 (F17) |
| composite 0..100 | `INTERPRETIVE_INFERENCE` | finder | one scalar; the breakdown beside it is the un-flattened form |
| `breakdown` | per-factor computed contributions | finder (`:101-141`) | **existing capital**, unregistered as a verdict |

### 2.5 Ladders
`PLAN_REVIEWED`; the W2 "four payload shapes" note on `47131772b` is [A] (subject line only).
t3: no event.

---

## §3 — The failure: two problems, one owned here

**§3a (owned).** `score(date, location, event[, native_chart])` returns one 0..100 float; the
finder computes a per-factor `breakdown` whose `tara_bala` key is present iff the overlay ran, and
the service **drops it** (`-> float`, `service.py:78-85`). `find_windows` returns ≤ `top_n` with no
coverage. The two sidecar routes bypass the service, so its location-required contract, its
overlay contract and any verdict it might add are **unreachable from any served path**; the route
default location is real (`:35-39,:54`) but declared global at both ends — a typing gap, not a
masquerade (F2). Expected: Register (three claims distinct); L3-Q10; Product §5.2; Strategy §3 (no
hidden cap); F28 (a registered engine no served path would fail without). Defect class:
**unserved** (registered engine bypassed) + **flattened** (breakdown → float at the service) +
**undisclosed cap** + **string-typed context**. Impact: Q-K09's *"best in range ≠ good"* and Q10's
binding-constraint explanation are unavailable from the service; catalog claims false at source.

**§3b (raised, not owned).** The chart-bound served election computes pañcāṅga quality from
`panchanga_daily`, a table written for **one observer** (Bhubaneswar) — so every chart's sunrise-
dependent tithi/nakṣatra transitions are Bhubaneswar's, on a personal surface, with no location
field on the `kala_elect_get` envelope (grep: only `chart_id` [R]). This is the Product §10 / VA
§4.4 hazard, and it lives in an L0 table and an L4 reader. It is **IP-10's** and an L0/L4 item's
(§10.2), and the native is asked to route it there.

Non-claims: no served answer shown wrong for the native (whose location is Bhubaneswar); YAML
doctrinal validity not judged; cap incidence and latency unmeasured; no DB.

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q10; Q-K09/K10; Q02's election half under a named criterion.
2. **Typed verdict as an extension of `breakdown` (F3, F8).** `MuhurtaVerdict = {calendar,
   personal, weight_source, vetoes[], criterion, vetoed_excluded, coverage, location_used,
   legacy_score, window_id}`:
   - `calendar = {value, contributions: breakdown minus tara_bala, completeness_state='applied',
     source_qualification per family}`;
   - `personal = {value: breakdown.tara_bala | null, completeness_state ∈ {applied, unavailable}}` —
     `applied` iff `'tara_bala' in breakdown` (the detector already exists); declared alias
     `breakdown.tara_bala → personal.value`;
   - `weight_source = {event_class, weights_hash: sha256(loaded weights dict), table}` — replaces
     v1.0's `undertaking` component: no per-event constraint set exists (`finder.py:163-166`; the
     only veto is event-independent `:58-76` [R]); a constraint set is `unexplored` with its DP02 source;
   - `vetoes` hard, listed (`_in_inauspicious`; tāra vadha when the overlay ran);
   - `epistemic_class`, `operator_role` (`computation` / `applicability` / `exclusion`),
     `comparable_with='self'` within an event class, `different_convention` across,
     `tier_basis='relative_uncalibrated'`.
3. **Location typed (F2, F6).** `location_used = {lat, lon, tz_offset_minutes, source ∈ {caller,
   canonical_default}}` on the **route body** of `/api/compute/muhurta_score` and on
   `call_muhurta_score`'s `content` — a descriptor change (`:463` inputs, `:502` body), named as
   such; the service's own guard is a PRESERVE regression, not proof of the delta. `routers/
   muhurat.py:34`'s 330 default is recorded (§11) and typed the same way.
4. **Coverage (B5 shape).** `coverage = {requested_horizon, completed_horizon, resolution:
   'calendar_day', partitions_searched: [event_class], exclusions: [{window_id, reason ∈ {vetoed,
   below_top_n}}], unsearched_regions: [], completion_detector: 'all_dates_in_horizon_scored'}`;
   asset-local counters `candidates_evaluated, vetoed, returned, top_n, truncated` beside it.
5. **Criterion (Q7, F4).** `criterion ∈ {nearest, strongest, robust}`; `vetoed_excluded: true`
   always (a veto is never ranked); `robust` `unavailable` until variants exist.
6. **Time discipline (F11).** Horizon `inclusivity='closed_closed'` **as the finder is today**
   (`:216,:243`), declared — not silently changed; window instants `t_start=sunrise_utc,
   t_end=sunset_utc` (`:250-251`), `time_basis='event_instant'`, `claim_grain='date_grain'` on the
   search; the finder iterates dates itself (`:243,:257`) — `resolver` is not `date_resolver`, stated.
   Window identity (B3): `window_id = sha256(event_class, date, location, weights_hash)`.
7. **The routes through the service (INTEGRATE).** `routers/muhurta_score.py` and `routers/
   muhurat.py` call `KaMuhurtaSevaService` and serve the verdict; `legacy_score` = today's 0..100
   float for their real readers (`useMuhuratFinder.ts:62-73`; `muhurta_score.py:129`).
8. **Old vs new.** Positive: 90-day *vivāha* with native chart → verdict, `personal.applied`.
   Negative: no chart → `personal.unavailable`, `calendar` unchanged; today: `breakdown` lacks
   `tara_bala` and the float is ≤ 90. Boundary: tithi at 05:58 vs 06:40 local at two longitudes →
   different `calendar` and `location_used`. Missing: all vetoed → empty with coverage. Ordinary
   period: three candidate days within 2 points → `strongest` names the top with contributions;
   `nearest` names the earliest un-vetoed — the walkthrough (§9).
9. **Simpler baseline.** The routes as they are (finder direct, float + breakdown).
10. **Ablation / effect size (F9, F17).** Remove `native_chart`: `personal` flips `applied →
    unavailable` and `legacy_score` drops by ≤ 10 (tāra weight 0.10) — bounded by construction;
    if the top window never changes for the canonical chart, the overlay is decorative for this
    native and the brief says so. **IP-10 (proposed):** `kala_elect_get` obtains its election from
    this service (or `phala/muhurta.py` adopts the verdict and `location_used` from a per-chart
    location) with an L3-owned sentinel; until then `elect.ts`'s existing `tara_bala_status` is the
    honest personal-overlay signal and the single-observer location is **undisclosed** on that envelope.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: `_validate_location` (regression test); the veto path; the five anchors; the finder's
  `breakdown`; `elect.ts`'s falsifier, three-state coverage and `tara_bala_status`.
- `ENRICH_CORRECT`: the verdict; coverage; `location_used`; `criterion`; `weights_hash`.
- `QUALIFY_LIMIT`: `date_grain`; `closed_closed` declared; `source_qualification` per family.
- `INTEGRATE`: the two routes through the service.
- **Fence decision (§10.1):** build the verdict in the service from the finder's *returned*
  `breakdown` (no `panchang_engine` edit) — recommended; or lift the fence on `finder.py:101-141`.
- **Real readers of the float:** `routers/muhurat.py` `score` (UI hook), `routers/muhurta_score.py:
  129`. **Not** readers: `ph_muhurta.py` (proxy — L4 item), `ka_vighnakara.py` (tithi only),
  `ka_sangam` (always raises — Saṅgam item).
- **Catalog correction (F19):** seed `:2267` and descriptor `:415-416,489-490` — one line each.
- No table, no migration; rollback = the routes call the finder again.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_muhurta_seva`, L3 service, global; L0 facts + weighted rules + composite; placement correct; `INTEGRATE + ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | live `depends_on={}`; reads L0 engine at call time; the routes are undeclared bypasses |
| C | invariants: a veto never returns a window; `calendar` invariant to `native_chart`; `personal.applied ⇔ tara_bala in breakdown`; location change → pañcāṅga change; `legacy_score` = finder float. Golden: five anchors; boundary: sunrise transition |
| D | rule citations (DP02) |
| E | zero value-receiving consumers; two bypassing routes; one different engine (IP-10) |
| F | components, states, `location_used`, `criterion` machine-readable |
| G | unmeasured; justified no-change |
| H | idempotent; no writes; `routers/muhurat.py` tz default typed |
| I | files in `may_touch`; W2; fence decision; IP-10 proposed to §12.2 |
| J | this brief; §7; both reports; ablation record |

---

## §7 — Proof matrix (tier `[S]` service-level, `[R]` route-level, `[X]` cross-asset/IP-10)

| proof | tier | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|
| Positive | S | `pytest tests/test_ka_muhurta_seva.py -k verdict` — canonical chart, *vivāha*, 90 d | verdict, `personal.applied`, `legacy_score` = finder float | equality | component missing; float differs | test file |
| Negative (PRESERVE) | S | `location=None` | `ValueError` | guard | passes silently | regression test |
| Negative (delta) | R | `POST /api/compute/muhurta_score` chart-less | body carries `location_used.source='canonical_default'` typed | typed, not `note` | string only / absent | `tests/l3/test_muhurta_score_sidecar_route.py` |
| Relevant influence | S | supply vs omit `native_chart` | `personal` flips; `calendar` unchanged; Δ`legacy_score` ≤ 10 | calendar invariant | calendar moves; Δ > 10 | test file |
| Irrelevant control | S | weights dict reordered | identical verdict; same `weights_hash` | order-invariant | differs | test file |
| Duplication | S | a factor in two families | one contribution | no double weight | doubles | test file |
| Context | R | `routers/muhurat.py` without `tz_offset_minutes` | `location_used.tz` typed with `source` | visible default | silent 330 | route test |
| Boundary | S | tithi transition 05:58 vs 06:40 at two longitudes; horizon end date | different `calendar`/`location_used`; end date **included** (`closed_closed`) | sunrise-dependent; declared inclusivity | same answer; end excluded | test file |
| Delivery | R | sentinel `personal.completeness_state='unavailable'` on a chart-less `routers/muhurat.py` call | reaches the route's `windows[]` and `useMuhuratFinder` | survives | absent | route test + UI hook fixture |
| Delivery (IP-10) | X | same sentinel via `kala_elect_get` | **gated** — no path today; pass only when IP-10 lands | — | — | IP-10 sentinel |
| Revision | S | change one YAML weight | `weights_hash` changes; `legacy_score` changes | versioned | silent | test file |
| Value | R | frozen Q10 / ordinary-period question | the verdict states which claim bound; the float cannot | — | no distinction | baseline |
| Evaluation | — | `not_applicable`: an election is an initiation-suitability claim, not an outcome prediction (Product §10) | — | — | — | — |

Binding: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `time_basis`, `claim_grain`), B2
(`completeness_state`, `epistemic_class`, `operator_role`, `comparable_with`, `tier_basis`,
`source_qualification` — **not** `corpus_verifiable` or the R-6 four: withdrawn), B3 (`window_id`),
B5 (`coverage`, seven keys). **B4 n/a** (no testimony aggregation; scores are per-day facts, not
witnesses) — stated. **DEMANDS** nothing from L3; L1 janma nakṣatra by `fact_id`. **Asset-local:**
`location_used`, `legacy_score`, `weight_source`, `weights_hash`, `contributions`, `vetoes`,
`criterion`, `vetoed_excluded`, `candidates_evaluated`, `vetoed`, `returned`, `top_n`, `truncated`.

---

## §8 — Prioritization

(1) catalog honesty (two false claims) → (2) routes through the service (`INTEGRATE` — makes
everything else reachable) → (3) typed verdict from `breakdown` → (4) `location_used` typed on
both routes → (5) coverage + cap → (6) `criterion` → (7) citations (DP02) → (8) IP-10 and the
single-observer item routed to their owners. T0; W2/W7; fan-out: none inside L3 today.

---

## §9 — Disposition, target state, walkthrough

`INTEGRATE` + `ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after the `[S]`
rows; `CONSUMER_INTEGRATED` when both sidecar routes serve the verdict with the sentinel on `main`.
Campaign: `ANALYZED → ENRICHED`. Non-claims: no `DATA_ACCEPTED`; `VALUE_EVALUATED` N; *"reusable
partial capital"* (Product §3.11); **`kala_elect_get` is not integrated by this brief**.

**Walkthrough (ordinary period).** A person with no chart asks the muhūrat finder for a
*gṛhapraveśa* date next month. Served: three days within 2 points; `criterion='nearest'` names the
earliest un-vetoed day; `personal.completeness_state='unavailable'` (no chart — not a lower
number); `location_used.source='caller'`; `coverage.completed_horizon` = the whole month,
`exclusions` = the two rikta days with `reason='vetoed'`. Nothing dramatic; nothing invented.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Fence:** build the verdict from the finder's returned `breakdown` (no `panchang_engine` edit) or lift the fence on `finder.py:101-141`? | build from the returned breakdown |
| 2 | **IP-10 + the single-observer item:** route `kala_elect_get`'s election through this service (or adopt the verdict in `phala/muhurta.py`) and raise `panchanga_daily`'s one-observer location to L0/L4 as a disclosure-or-per-chart item | yes, both; add IP-10 to blueprint §12.2 |
| 3 | `criterion` default for the served routes | `nearest` for "when may I begin"; `strongest` on request |
| 4 | Rank by calendar, veto by personal? | yes — the overlay is a veto + a grade carried as testimony, never a ranking term |
| 5 | Rule-family citations (DP02) | yes |

---

## §11 — Not verified here

1. Live registry state (`depends_on`, migration 676 applied) — migration text only.
2. Cap incidence, latency — unmeasured.
3. `config_loader.get_weights_for_event` — not read; the `weights_hash` surface is proposed.
4. `47131772b` content — subject line only [A].
5. Whether the single-observer location is disclosed anywhere on the `kala_elect_get` envelope —
   grep found no location field; not read end-to-end.
6. `routers/muhurat.py:34` tz default 330 — recorded, outside the service; typed under §4.3.
7. No prior native ruling on the criterion vocabulary was found beyond the blueprint.

## §12 — Review dispositions (v1.0 → v1.1)

F1 accepted — consumer map rewritten, delta re-scoped, live-path statement corrected (§0, §2.3,
§3a, §4.7, §9); F2 accepted (§3a/§3b, §4.3, §10.2); F3 accepted (§1, §2.2, §2.4, §4.2); F4
accepted (§4.5); F5 accepted (§2.3, §5); F6 accepted (§4.3, §7 Negative split); F7 accepted (§7
Delivery restated; IP-10 proposed §4.10/§10.2); F8 accepted (§4.2 `weight_source`); F9 accepted
(§2.2); F10 accepted (0..100 throughout); F11 accepted (§4.6); F12 accepted (removed); F13 accepted
(`may_touch`); F14 accepted (§2.5 [A]); F15 accepted (`weights_hash`); F16 accepted; F17 accepted
(§4.10); F18 accepted (§2.2, §4.3, §11); F19 accepted (§5); F20 accepted (§7 tiers + Evaluation);
binding non-conformances all addressed (§4.4, §4.6, §7).
