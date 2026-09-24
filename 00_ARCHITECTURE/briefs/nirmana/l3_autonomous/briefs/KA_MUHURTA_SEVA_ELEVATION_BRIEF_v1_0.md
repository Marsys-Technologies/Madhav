---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_MUHURTA_SEVA_ELEVATION_BRIEF
version: "1.2"
status: PROPOSED_FOR_NATIVE_RULING      # v1.0 REWORK (20, F1 BLOCKER) → v1.1 ACCEPT_WITH_CORRECTIONS (16 resolved, 4 partial, 18 new) → v1.2 folds all 18
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
asset_or_interface_ids: ["ka_muhurta_seva", "sidecar routes routers/muhurta_score.py + routers/muhurat.py (re-pointed through the service — coordinated)", "IP-10a (NEW, proposed for blueprint §12.2): kala_elect_get DISCLOSURE packet — location_used + personal state from the existing lane_f.tara_bala_status", "cross-asset item (L0+L4, not a packet): panchanga_daily is a single-observer table read by phala/muhurta.py for every chart"]
goal_objective: "Make ka_muhurta_seva the one election engine its registration claims: a typed verdict built as an extension of the finder's existing per-factor breakdown (calendar / personal / weight-source carried separately, vetoes as vetoes, the horizon and cap disclosed, the location actually used typed on every answer, a named comparator from the blueprint's vocabulary) — and route the two sidecar election endpoints through it, so that 'the best window in your range' can never be read as 'a good window'. The chart-bound served election (kala_elect_get) does not touch this service today; its real hazard lives in a single-observer L0 table and is raised, not absorbed."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at bf70a3477 and 27b0146f3 (2026-09-24)"
accepted_upstream_contract: "L0 pañcāṅga engine (panchang_engine; accepted L0 revision f6fed12c7); L0 panchanga_daily is a SINGLE-OBSERVER table (Bhubaneswar: scripts/panchanga_daily_writer.py:42-46,205; migration 427:41-43) — its use for every chart's election is the cross-asset hazard §3b raises; L1 chart_facts janma nakṣatra for the overlay"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agents, fresh context; reports at briefs/reviews/REVIEW_KA_MUHURTA_SEVA_v1_0.md (REWORK) and _v1_1.md (ACCEPT_WITH_CORRECTIONS)"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_muhurta_seva/{service,writer}.py", "platform/python-sidecar/routers/muhurta_score.py and routers/muhurat.py (sidecar served routes; re-pointed through the service — coordinated, they are live)", "platform/python-sidecar/tests/test_ka_muhurta_seva.py, tests/l3/test_muhurta_score_sidecar_route.py", "FENCE DECISION (§10.1): platform/python-sidecar/muhurat/finder.py — NOTE the real path: the finder was MOVED OUT of panchang_engine at the P2 re-arch (finder.py:4-5); panchang_engine/muhurat.py is a 38-line re-export shim. Editing it touches no panchang_engine file, so the fence question is whether muhurat/ (scoring/judgement, sidecar-local, no declared owner in any governance text) is inside this asset's fence", "platform/scripts/seed/asset_registry_seed.ts:2267 (catalog correction line)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:405-513 (call_muhurta_score descriptor/outputs) — Pūrṇa-owned", "IP-10a (proposed): platform-mcp/src/tools/kala_views/elect.ts, platform-mcp/src/tools/muhurta_finder.ts — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["panchang_engine/** (shared Swiss-state span; L0 pañcāṅga authority) — note this does NOT cover muhurat/finder.py, see may_touch", "scripts/panchanga_daily_writer.py, panchanga_daily (L0 table — hazard raised, not edited)", "brahmagyan/phala/muhurta.py (L4 — the served election's actual engine; cross-asset item, own owner)", "pipeline/orchestrator/writers/ph_muhurta.py (L4, sealed — its proxy formula is recorded as an L4-owned item)", "pipeline/orchestrator/writers/ka_sangam.py + services/ka_sangam/engine.py:700-735 (the always-raising .score call is Saṅgam-owned)", "pipeline/orchestrator/writers/ka_vighnakara.py (reads compute_panchang directly; its brief)", "platform-mcp/src/tools/kala_views/**", ".github/workflows/deploy.yml", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the typed verdict (stage 3); CONSUMER_INTEGRATED when routers/muhurat.py + routers/muhurta_score.py serve the verdict through the service with the L3-owned sentinel; kala_elect_get integration is IP-10a's, not this brief's"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; no t3 event today"
wave: "W2 (service proof); W7 (accepted-input use)"
shape: single asset, service/probe, global scope
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted are marked [R]; Lane D §10,
  T1 Frontier row, Lane E Q-K09/K10 §5.8, Lane F P11 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.2 (2026-09-24): v1.1 re-review dispositions (18 findings) — N1 the finder is platform/python-sidecar/muhurat/finder.py (moved out of panchang_engine at the P2 re-arch; panchang_engine/muhurat.py is a shim), so §10.1's fence dichotomy was false and is restated; N2 the recommended no-edit option CANNOT populate B5 exclusions/truncated — find_muhurat drops vetoed days (`if s > 0`) and cuts to top_n before returning — so three real options are named with what each can and cannot produce; N3 tāra Vadha is a GRADE of 0.00 in this engine, not a veto, so presenting it as an existing veto is withdrawn and a veto becomes an explicit NEW rule proposal with its own DP02 source and ranking consequence; N4 the ablation bound is per event (Δ ≤ 100 × weights['native']): 0.10 for five events but 0.20 mantra_initiation and 0.25 upaya_ritual/sadhana_initiation; N5 the three Pūrṇa-owned TS paths removed from may_touch; N6 IP-10 split into a disclosure packet, a cross-asset L0/L4 item and a dropped branch A (its action_type vocabulary has no EVENTS_MVP mapping and the codebase declined to invent one); N7 location typing is response-side (no descriptor change) with coords_source/tz_source separated; N8 line numbers + the stale muhurta_finder.ts:32-34 comment; N9 the knockout requires four conjuncts including Saturday and its tithi set is {4,8,9,14,30}, not rikta {4,9,14}; N10 the Duplication row redefined as the contribution-sum identity; N11 F24 verdict tiers; N12 inclusivity declared on the window, horizon inclusivity inside coverage; N13 weights_hash over the merged per-event dict with the lru_cache caveat; N14 the score path loses panchang_context unless the verdict carries the aṅga names; N15 ka_sangam pays a full compute_panchang before a guaranteed raise; N16 B3 generation/window_ref added and the B4 exemption made a decision; N17 a fourth find_muhurat wrapper with a 330 default; N18 the campaign-ladder pair cited or dropped."
  - "1.1 (2026-09-24): v1.0 REWORK dispositions (20 findings) — see §12."
  - "1.0 (2026-09-24): first issue."
---

# `ka_muhurta_seva` elevation brief — election as three claims, not one number

## §0 — The recommendation, in one paragraph

`ka_muhurta_seva` is registered as the layer's election service, and **nothing served consumes a
value from it** [R]. Three election engines run in this codebase: (1) `services/ka_muhurta_seva/
service.py` → `muhurat/finder.py` — whose only production `.score(` caller,
`ka_sangam/engine.py:722`, **always raises** (`event='general' ∉ EVENTS_MVP`, documented `:700-712`
[R]) after paying a full `compute_panchang` first (`service.py:107-117`, N15); (2) the sidecar routes
`routers/muhurta_score.py:48-50,123` and `routers/muhurat.py:20,139`, which import
`panchang_engine.muhurat` / `muhurat.finder` **directly**; (3) the served chart-bound election
`kala_elect_get` (`elect.ts:62,872` → `muhurta_finder.ts:41` → `L4_phala/query_muhurat.ts:124` →
`brahmagyan/phala/muhurta.py:1894`), which imports neither and derives `panchanga_quality` from
**`panchanga_daily`** (`:1317,:1329-1330`) — a **single-observer table computed at Bhubaneswar**
(`panchanga_daily_writer.py:42-46,205`; migration `427:41-43` [R]) — for every chart. The sealed L4
`ph_muhurta.py` uses a proxy formula with the comment *"ka_muhurta_seva not available at writer
import time"* (`:134-136`, `source:'ka_muhurta_seva_proxy'` `:160` [R]). So the seed's *"Location
mandatory — no silent Bhubaneswar default"* (`asset_registry_seed.ts:2267`) and the descriptor's
*"the same primitive ph_muhurta calls internally"* (`call_service_wrappers.ts:415-416,489-490`) are
both false at source [R]. Recommendation: **`INTEGRATE` + `ENRICH_CORRECT` + `QUALIFY_LIMIT`** — a
typed `MuhurtaVerdict` built as an **extension of the finder's existing per-factor `breakdown`**
(`finder.py:101-141,:247-255`; `tara_bala` present only with a native chart `:139-140` [R] — the
personal-overlay presence is already detectable); the two sidecar routes **re-pointed through the
service** so the registered engine is the served engine on the global surface; `criterion ∈ {nearest,
strongest, robust}` (blueprint Q7 vocabulary); `location_used` typed; coverage in the B5 shape with
the horizon's true inclusivity; and the chart-bound election handled as a **disclosure packet
(IP-10a)** whose real hazard — one observer's sunrise for every chart — is raised to L0/L4 as a
cross-asset item and not pretended to be this service's fix. Decisions: the `muhurat/` fence, the
coverage option, and whether a tāra veto is added at all (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:158) | *"Calendar/action-time computation and search service. P/I/Q: calendar correctness, personal suitability and outcome are distinct; real undertaking constraints and scope. DP07/09."* | the three-claims obligation |
| Strategy §6.1 **L3-A03** (`:273`) | *"Test actual time/location and undertaking constraints; distinguish general calendar from personal feasibility and outcome expectation. Service-health proof alone is insufficient."* | unchanged — and "actual location" is the §3b hazard |
| Strategy **L3-Q10** (`:71`); §3 (`:97`) *"no universal ranking or hidden hard cap"* | value frame | — |
| Product §3.11 (`:168-172`); §10 (`:365`); §5.2 (`:223`) | reusable partial capital; date/location/tz fidelity; no scalar substitutes | binds §9 |
| VA §4.4 (`:152-158`) | the lattice's reference location and midpoint approximation are disclosed; consumers must preserve location/horizon/precision | the disclosure `kala_elect_get` does not carry (IP-10a) |
| W0 register #14 (`:33,:640-644`) | `score / find_windows → float / MuhuratWindow` incl. **`windows[].breakdown`** | the breakdown is registered capital |
| Lane D §10 (`:532-566`) | LIVE, medium confidence; *"not independently re-confirmed beyond that comment"* | **overturned** [R]: the "reuse" is of `score_muhurat` by the routes, not of this service |
| Lane E Q-K09/K10, §5.8 (`:961-967`) | `elect.ts:286-290` honest empty; `:296-298` falsifier about the window — *do not "fix"* | preserved; and `elect.ts` already types the personal overlay: `lane_f.tara_bala_status ∈ {applied, unavailable_no_janma_nakshatra}` (`muhurta_finder.ts:333`), `honestEmptyCoverage('tara_bala_personal_star_veto')` (`elect.ts:314-317`) [R] |
| **`muhurat/finder.py:4-5`** [R] | *"Moved from panchang_engine/muhurat.py (P2 re-arch, 2026-06-09). Scoring/judgement lives here. panchang_engine/ holds only the deterministic core"*; `panchang_engine/muhurat.py:1-8` is a re-export shim (`:16` re-exports `_score_breakdown`) | **the finder is not under `panchang_engine/`** — the v1.1 fence dichotomy was false (N1). No governance text names an owner or fence for `muhurat/` |
| **`panchang_engine/tara_bala.py:40,:44,:116`** [R] | Vipat and **Vadha are grades of `score: 0.00`**, and `compute_tara_bala_score` ranges 0.0–1.0 | **there is no tāra veto in this engine** (N3); the Vadha `hard_veto` at `elect.ts:202-204` belongs to the *phala* path |
| **`muhurat_weights.yaml`** [R] | `native: 0.10` for vivah `:48`, griha_pravesh `:63`, vyapara `:79`, yatra `:96`, property_purchase `:114`; **`0.20`** mantra_initiation `:127`; **`0.25`** upaya_ritual `:148` and sadhana_initiation `:169`; `Version: 1.0` in a comment only (`:19`) | the ablation bound is per event (N4) |
| DAG reconciliation §2 (`:33`); migration 676 | live `depends_on = {}`; seed `['ka_graha_sancara']` (`:2274` [V]) | permanent divergence |
| Blueprint §9 Q7 (`:671`), §12.1 (`:748`) | `criterion ∈ {nearest, strongest, robust}` | v1.0's `nearest_clean/best_scored` withdrawn |
| Blueprint §12.2 (`:751-763`) | **no election interface packet exists** | IP-10a proposed (§4.10) |
| Migration `968:76` | confirms `ph_muhurta`'s proxy | L4-owned item, recorded |
| `now.ts` / `elect.ts` null carriage | `moorti_computed=false` rows carry null grade fields **verbatim, never backfilled** | good; preserved |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`asset_registry_seed.ts:2263-2276`: `storage_type: 'service'`, `depends_on: ['ka_graha_sancara']`
(live `{}`), `scope: 'global'`, `asset_kind: 'service'`; description `:2267` false at source.
Cost: unmeasured (`KALA_COST_PROFILE_v1_0.md` pending).

### 2.2 The code [V]/[R]
- **Writer** `services/ka_muhurta_seva/writer.py`: FORENSIC self-test on **five of the seven**
  CLAUDE.md §B anchors (`:65-69`); knockout check (`:237-273`); `WriterResult(rows_inserted=0)`
  (`:137-142`); it calls `score_muhurat` **directly** (`:220-221`), not the service.
- **Service** `service.py`: `_validate_location` (`:37-60`, raises on None/missing keys);
  `score(...) -> float` on the **0..100** scale (`:78-119`, `:101`), running `_validate_location`
  **and a full `compute_panchang`** before `score_muhurat` (`:107-119`); optional overlay "un-floor"
  (`:93-96`); `find_windows(..., top_n=10)` (`:121-169`, delegating at `:159-169`); module delegates
  (`:178-211`). Imports are `from muhurat.finder import …` (`:110,:157`).
- **Finder** `muhurat/finder.py`: `EVENTS_MVP` — 8 events (`:36-46`); `_in_inauspicious` veto
  (`:58-76`) requiring **four conjuncts**: `rahu_kalam ∧ yamagandam ∧ tithi ∈ {4,8,9,14,30} ∧
  Saturday` — and since `rahu_kalam`/`yamagandam` are emitted for every day
  (`timings.py:196,200`; `panchang_engine/__init__.py:102-103,168`), the live veto reduces to
  **worst-tithi-on-a-Saturday**, whose tithi set is **not** the rikta set {4,9,14} (N9);
  **`_score_breakdown` (`:101-141`)** keys `tithi, nakshatra, vara, yoga, planet` + `tara_bala`
  **only when `native_chart`** (`:139-140`); `score_muhurat` (`:148-196`, 0..100, raising at
  `:161-162` on an unknown event; weights/table at `:164-166`); `find_muhurat` (`:203-261`): horizon
  **inclusive both ends** (`:215,:219,:242`), window instants `sunrise_utc → sunset_utc` (`:250-251`),
  `breakdown` attached per window (`:247-255`), **appends only `if s > 0` (`:246`)** — knockout days
  and true-zero days are dropped indistinguishably and uncounted — and returns
  **`candidates[:top_n]` (`:261`)** [R]. `MuhuratWindow.breakdown` (`panchang_engine/types.py:280`).
  Weights: tāra weight per event (§1); no machine-readable citation field; `config_loader.py:24`
  is `@lru_cache`, merge at `:66-69`, `invalidate_weights_cache` at `:72-79` — **no version or hash
  surface** [R].
- **Routes**: `routers/muhurta_score.py` — request `{datetime_utc, event_class, ayanamsha_id}`
  (`:61-69`), **no chart or location input**, default location (`:35-39,:54`), `score_muhurat` direct
  (`:48-50,:123`), untyped `dict` response (`:73`) with a `note` string (`:131-136`) and
  `panchang_context` (tithi/nakṣatra/vāra/yoga names, `:137-142`), ayanāṃśa validated at `:89-99`;
  `routers/muhurat.py` — `find_muhurat` direct (`:20,:139-148`), `lat`/`lon` **required**
  (`:32-33`), `tz_offset_minutes: int = Field(330, …)` silent IST default (`:34`), 90-day cap
  (`:131`), serves `windows[].breakdown` (`:46`); `_fetch_native_chart` (`:50-119`) stays on the
  route. A **fourth** `find_muhurat` wrapper exists at `panchang_engine/__init__.py:437-475` with its
  own 330 default and no non-test caller (N17).
- **Served election** `elect.ts` → `muhurta_finder.ts:41` (`callPlatformPrimitive`; the comment at
  `:32-34` naming `/api/compute/muhurat` is **stale** — N8) → `query_muhurat.ts:124` →
  `phala/muhurta.py` on `panchanga_daily`; horizon default `new Date()`+90d (`elect.ts:229-232`,
  Pūrṇa-owned); finder input carries no location (`:862-869`); scores on 0..1
  (`muhurta_finder.ts:280`) [R].

### 2.3 Consumers (boundary: `platform/python-sidecar`, `platform/src`, `platform-mcp/src`; tests excluded) [R]
| consumer | reads | role |
|---|---|---|
| `writers/ka_sangam.py:40,329`; `services/ka_sangam/engine.py:722` | `.score(event='general')` — **always raises**, after a full `compute_panchang` has already run inside `score()` (N15) | dead call (Saṅgam-owned) |
| `writers/ka_vighnakara.py:197-198,613-620` | instantiates; calls `compute_panchang` directly; reads tithi only | vocabulary/probe — not a float reader |
| `writers/ph_muhurta.py:134-136,160` (L4 sealed) | **proxy formula**, never this service | none (L4 item) |
| `routers/muhurta_score.py:123`, `routers/muhurat.py:139` | `panchang_engine.muhurat` / `muhurat.finder` **directly** | served, bypass |
| `kala_elect_get` / `muhurta_finder.ts` | `phala/muhurta.py` on `panchanga_daily` | served, different engine |
| `writer.py:220-221`; `service_probes.py:975-1010` | `score_muhurat` direct | probe |

**Live-path statement.** No live value-receiving caller of `service.py` was found within scope. Two
served sidecar routes run the same finder without the service; the chart-bound election runs a third
engine over a single-observer table.

### 2.4 Epistemic class
| quantity | class | authority | note |
|---|---|---|---|
| pañcāṅga at date+location | `COMPUTED_FACT_CONFIGURATION` | L0 engine (live) / `panchanga_daily` (one observer) | the observer *is* the subject of the fact |
| per-family weights (YAML) | `QUALIFIED_RULE` only if cited per family; else engineered | YAML comments name sources; no field | `source_qualification` owed; version = hash of the **merged per-event** dict (N13) |
| tāra-bala overlay | qualified rule (nava-tārā), weight 0.10 / 0.20 / 0.25 by event | finder + L1 janma nakṣatra | present in `breakdown` only with `native_chart`; **Vadha scores 0.00, it does not veto** (N3) |
| composite 0..100 | `INTERPRETIVE_INFERENCE` | finder | one scalar; the breakdown beside it is the un-flattened form |
| `breakdown` | per-factor computed contributions | finder (`:101-141`) | **existing capital**, unregistered as a verdict |
| the knockout | rule (`_in_inauspicious`) | finder `:58-76` | four conjuncts; live form = worst-tithi-on-Saturday; **event-independent** |

### 2.5 Ladders
`PLAN_REVIEWED`; the W2 "four payload shapes" note on `47131772b` is [A] (subject line only).
t3: no event.

---

## §3 — The failure: two problems, one owned here

**§3a (owned).** `score(date, location, event[, native_chart])` returns one 0..100 float; the finder
computes a per-factor `breakdown` whose `tara_bala` key is present iff the overlay ran, and the
service **drops it** (`-> float`, `service.py:78-85`). `find_windows` returns ≤ `top_n` with no
coverage, and the finder it delegates to has **already discarded** every vetoed and zero-scored day
without counting them (`finder.py:246`) and already cut to `top_n` (`:261`) — so the numbers a
coverage object needs do not survive the call (N2). The two sidecar routes bypass the service, so
its location-required contract, its overlay contract and any verdict it might add are **unreachable
from any served path**; the route default location is real (`:35-39,:54`) but declared global at both
ends — a typing gap, not a masquerade. Expected: Register (three claims distinct); L3-Q10; Product
§5.2; Strategy §3 (no hidden cap); F28. Defect class: **unserved** (registered engine bypassed) +
**flattened** (breakdown → float at the service) + **undisclosed cap** + **string-typed context**.

**§3b (raised, not owned).** The chart-bound served election computes pañcāṅga quality from
`panchanga_daily`, a table written for **one observer** (Bhubaneswar) — so every chart's
sunrise-dependent tithi/nakṣatra transitions are Bhubaneswar's, on a personal surface, with no
location field on the `kala_elect_get` envelope (grep: only `chart_id` [R]). This is the Product §10
/ VA §4.4 hazard; it lives in an L0 table and an L4 reader and is a **cross-asset item**, not a
packet this brief can execute (§10.2).

Non-claims: no served answer shown wrong for the native (whose location is Bhubaneswar); YAML
doctrinal validity not judged; cap incidence and latency unmeasured; no DB.

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q10; Q-K09/K10 (blueprint cross-references); Q02's election half under a named
   criterion.
2. **Typed verdict as an extension of `breakdown`.** `MuhurtaVerdict = {calendar, personal,
   weight_source, vetoes[], criterion, vetoed_excluded, coverage, location_used, legacy_score,
   window_id, generation}`:
   - `calendar = {value, contributions: breakdown minus tara_bala, context: {tithi, nakshatra, vara,
     yoga} (N14 — the aṅga names `routers/muhurta_score.py:137-142` serves today, which a bare float
     would lose), completeness_state='applied', source_qualification per family}`;
   - `personal = {value: breakdown.tara_bala | null, completeness_state ∈ {applied, unavailable}}` —
     `applied` iff `'tara_bala' in breakdown` (the detector already exists); declared alias
     `breakdown.tara_bala → personal.value`;
   - `weight_source = {event_class, weights_hash, table}` where **`weights_hash` = sha256 over the
     merged per-event dict** (`config_loader.py:66-69`) serialised canonically
     (`json.dumps(sort_keys=True)`) — there is no version surface today, and the loader is
     `@lru_cache`d, so a YAML edit is invisible until `invalidate_weights_cache()` (N13);
   - `vetoes` = the knockout only (`_in_inauspicious`), described honestly as four conjuncts whose
     live form is worst-tithi-on-a-Saturday over `{4,8,9,14,30}` (N9);
   - `epistemic_class`, `operator_role` (`computation` / `applicability` / `exclusion`),
     `comparable_with='self'` within an event class, `different_convention` across,
     `tier_basis='relative_uncalibrated'`.
3. **A tāra veto would be a NEW rule, not a description (N3).** In this engine Vadha is a **grade of
   0.00** (`tara_bala.py:44`) and the day still ranks. If the native wants Vadha (or Pratyari) to
   exclude a window, that is an `ENRICH_CORRECT` addition needing its own DP02 source, and its
   consequence must be stated: the **returned set** then depends on `native_chart`, which today it
   does not. §10.4 asks; §4.9 carries the case. Until ruled, `vetoes` contains the knockout alone.
4. **Location typed.** `location_used = {lat, lon, tz_offset_minutes, coords_source ∈ {caller,
   canonical_default}, tz_source ∈ {caller, canonical_default}}` — **two sources, because
   `routers/muhurat.py` takes `lat`/`lon` as required and defaults only the tz** (N7). It is a
   **response-side** field: `call_muhurta_score` forwards `{ content: data }`
   (`call_service_wrappers.ts:509`), so **no descriptor change is needed** to carry it; a descriptor
   and request-model change is needed only if `/muhurta_score` is to *accept* a location, which is a
   separate decision (§10.5). On `/muhurta_score` today `coords_source` can only be
   `canonical_default`.
5. **Coverage (B5 shape) — with the option that can produce it (N2).** `coverage = {requested_horizon
   (carrying the horizon's `closed_closed` inclusivity, N12), completed_horizon, resolution:
   'calendar_day', partitions_searched: [event_class], exclusions: [{window_id, reason ∈ {vetoed,
   zero_quality, below_top_n}}], unsearched_regions: [], completion_detector:
   'all_dates_in_horizon_scored'}`. Three ways to populate it, of which only one is free:
   **(a)** edit `muhurat/finder.py` so `find_muhurat` returns all candidates plus counts — exact
   `vetoed` and `zero_quality`, needs the §10.1 fence;
   **(b)** no finder edit: call `find_muhurat` with `top_n = len(horizon)` (≤ 90 on the route,
   `routers/muhurat.py:131`) and apply the cut in the service — yields `below_top_n` and `truncated`
   **exactly**, and `dropped_by_finder = |horizon| − |candidates|` as an **approximate** vetoed count
   in which knockout and true-zero are conflated (declared as such);
   **(c)** the service re-runs the per-day loop — rejected: a second engine iteration doubling
   `compute_panchang`.
   For the single-day `score()` path the service calls `_score_breakdown` directly (re-exported at
   `panchang_engine/muhurat.py:16`), since `score_muhurat` returns a bare float.
6. **Criterion (Q7).** `criterion ∈ {nearest, strongest, robust}`; `vetoed_excluded: true` always;
   `robust` `unavailable` until variants exist.
7. **Time.** Window rows: `t_start = sunrise_utc`, `t_end = sunset_utc` (`finder.py:250-251`),
   `time_basis='event_instant'`, **`inclusivity` declared on the window row** (B1 requires it there,
   not on the horizon — N12; state whether sunset is exclusive); the search horizon's
   `closed_closed` lives in `coverage.requested_horizon`; `claim_grain='date_grain'` on the search.
   The finder iterates dates itself (`:242,:258`) — `resolver` is **not** `date_resolver`, stated.
   **B3:** `window_id = sha256(event_class, date, location, weights_hash)`; `generation =
   weights_hash`; `window_ref = {asset_id, generation, id: window_id}` (N16).
8. **The routes through the service (INTEGRATE).** `routers/muhurta_score.py` and `routers/muhurat.py`
   call `KaMuhurtaSevaService` and serve the verdict; `legacy_score` = today's 0..100 float for their
   real readers (`useMuhuratFinder.ts:62-73`; `muhurta_score.py:129`). `ayanamsha_id` validation
   stays on the route (`:89-99` — the service has no such parameter); `_fetch_native_chart` stays on
   `routers/muhurat.py`.
9. **Old vs new.** Positive: 90-day *vivāha* with native chart → verdict, `personal.applied`.
   Negative: no chart → `personal.unavailable`, `calendar` unchanged; today: `breakdown` lacks
   `tara_bala` and the float is ≤ 90. Boundary: tithi at 05:58 vs 06:40 local at two longitudes →
   different `calendar` and `location_used`. Missing: a **one-day** fixture on a Saturday with tithi
   ∈ {4,8,9,14,30} → every candidate vetoed → empty with coverage (N9: a multi-day all-vetoed horizon
   is not constructible). **If §10.4 adds a tāra veto:** the same fixture with and without
   `native_chart` returns different *sets*, and that difference is the new rule's own proof row.
10. **Ablation / effect size (N4).** Remove `native_chart`: `personal` flips `applied → unavailable`
    and `legacy_score` drops by **≤ 100 × `weights['native']` for that event** — 10 points for the
    five 0.10 events, **20 for mantra_initiation, 25 for upaya_ritual and sadhana_initiation**; the
    detector reads the effective weight from `get_weights_for_event(event)` rather than hard-coding.
    If the top window never changes for the canonical chart, the overlay is decorative for this
    native and the brief says so.
11. **IP-10a (proposed) and the cross-asset item (N6).** Split honestly:
    **(i) disclosure packet (Pūrṇa-owned, L3 sentinel):** `kala_elect_get`'s envelope carries
    `location_used = {…, source:'panchanga_daily_single_observer'}` and a `personal` state derived
    from the **existing** `lane_f.tara_bala_status` (`muhurta_finder.ts:333`) — no new engine, no
    vocabulary change;
    **(ii) cross-asset item (L0 `panchanga_daily` + L4 `phala/muhurta.py` owners):** per-chart
    pañcāṅga, or an explicit disclosure that the calendar is one observer's;
    **(iii) branch A is dropped.** Routing `kala_elect_get` through this service would require
    mapping `action_type ∈ {marriage, travel, business, medical, education, property, general}`
    (`muhurta_finder.ts:83-85`) onto `EVENTS_MVP`; `general` is not in it (the exact mismatch that
    makes `ka_sangam/engine.py:722` raise), the TS bridge maps `education → 'vidya_arambha'`
    (`:498`) and `medical → 'upaya_ritual'` (`:490`), neither a clean analog, and
    `routers/muhurta_score.py:9-13,25-32` records the codebase's own decision **not** to invent that
    mapping. Re-opening it is a native vocabulary ruling, not an interface packet.
12. **Catalog corrections.** Seed `:2267`; descriptor `:415-416,489-490`; and the stale
    `muhurta_finder.ts:32-34` comment naming the wrong endpoint (N8) — the comment that produced this
    brief's own v1.0 error.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: `_validate_location` (regression test); the knockout path; the five anchors; the
  finder's `breakdown`; `elect.ts`'s falsifier, three-state coverage and `tara_bala_status`; the
  route's `panchang_context` aṅga names (carried into `calendar.context`).
- `ENRICH_CORRECT`: the verdict; coverage; `location_used`; `criterion`; `weights_hash`; **and, only
  if §10.4 rules it, a tāra veto — a new rule, not a restatement**.
- `QUALIFY_LIMIT`: `date_grain`; the horizon's `closed_closed` declared; `source_qualification` per
  family; the conflated `dropped_by_finder` count under option (b).
- `INTEGRATE`: the two routes through the service.
- **Fence decision (§10.1):** the finder is `platform/python-sidecar/muhurat/finder.py` — editing it
  touches **no** `panchang_engine` file (the P2 re-arch moved it; `panchang_engine/muhurat.py` is a
  shim). No governance text assigns `muhurat/` an owner. So the question is not "L0 or not" but
  "is sidecar-local scoring/judgement inside this asset's fence": if yes, coverage option (a); if no,
  option (b) with its declared approximation.
- **Real readers of the float:** `routers/muhurat.py` `score` (UI hook), `routers/muhurta_score.py:129`.
  **Not** readers: `ph_muhurta.py` (proxy — L4 item), `ka_vighnakara.py` (tithi only), `ka_sangam`
  (always raises — Saṅgam item, and it pays a `compute_panchang` first).
- No table, no migration; rollback = the routes call the finder again.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_muhurta_seva`, L3 service, global; L0 facts + weighted rules + composite; placement correct; `INTEGRATE + ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | live `depends_on={}`; reads the L0 engine at call time via `muhurat/finder.py`; the routes are undeclared bypasses |
| C | invariants: a veto never returns a window; `calendar` invariant to `native_chart` (**unless §10.4 adds a tāra veto** — then the returned set is not); `personal.applied ⇔ tara_bala in breakdown`; location change → pañcāṅga change; `legacy_score` = finder float; Σ`calendar.contributions` + `personal.value` = `legacy_score` to rounding. Golden: five anchors; boundary: sunrise transition |
| D | rule citations (DP02) |
| E | zero value-receiving consumers; two bypassing routes; one different engine (IP-10a) |
| F | components, states, `location_used`, `criterion` machine-readable |
| G | unmeasured; justified no-change — except `ka_sangam`'s guaranteed-raise path, which pays a Swiss computation per Mode A/B row (Saṅgam's item) |
| H | idempotent; no writes; `routers/muhurat.py` tz default typed; the fourth wrapper (`panchang_engine/__init__.py:437-475`) recorded (N17) |
| I | files in `may_touch`; W2; fence decision; IP-10a proposed to §12.2 |
| J | this brief; §7; three reports; ablation record |

---

## §7 — Proof matrix

Columns: **verdict tier** is F24's; **scope** is `[S]` service-level, `[R]` route-level, `[X]`
cross-asset/IP-10a.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | S | `pytest tests/test_ka_muhurta_seva.py -k verdict` — canonical chart, *vivāha*, 90 d | verdict, `personal.applied`, `legacy_score` = finder float, `calendar.context` = the four aṅga names | equality; context preserved | component missing; float differs; context lost | test file |
| Negative (PRESERVE) | COMPUTATIONAL_CORRECTNESS | S | `-k location_required` — `location=None` | `ValueError` | guard | passes silently | regression test |
| Negative (delta) | COMPUTATIONAL_CORRECTNESS | R | `POST /api/compute/muhurta_score` chart-less | body carries `location_used.coords_source='canonical_default'` typed; **no descriptor change needed** | typed, not `note` | string only / absent | `tests/l3/test_muhurta_score_sidecar_route.py` |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | S | `-k native_chart_flip` over three events (vivah, mantra_initiation, upaya_ritual) | `personal` flips; `calendar` unchanged; Δ`legacy_score` ≤ 100 × `get_weights_for_event(e)['native']` (10 / 20 / 25) | calendar invariant; per-event bound | calendar moves; Δ exceeds the event's own bound | test file |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | S | weights dict reordered | identical verdict; same `weights_hash` (canonical serialisation) | order-invariant | differs | test file |
| Duplication | COMPUTATIONAL_CORRECTNESS | S | any scored day (N10) | Σ`calendar.contributions` + `personal.value` = `legacy_score` to rounding | the identity, not "one contribution" | the sum diverges (a factor double-counted) | test file |
| Context | COMPUTATIONAL_CORRECTNESS | R | `routers/muhurat.py` without `tz_offset_minutes` | `location_used.tz_source='canonical_default'` with `coords_source='caller'` | two sources typed | one conflated source; silent 330 | route test |
| Boundary | COMPUTATIONAL_CORRECTNESS | S | tithi transition 05:58 vs 06:40 at two longitudes; horizon end date | different `calendar`/`location_used`; end date **included** (`closed_closed` in `coverage.requested_horizon`); window `inclusivity` declared | sunrise-dependent; declared inclusivity at both levels | same answer; end excluded; window inclusivity absent | test file |
| Missing | COMPUTATIONAL_CORRECTNESS | S | **one-day** horizon: a Saturday with tithi ∈ {4,8,9,14,30} | empty result with coverage; `exclusions` = that day, `reason='vetoed'` | the knockout's four conjuncts | a non-Saturday fixture expected to veto | test file |
| Delivery | COMPUTATIONAL_CORRECTNESS | R | sentinel `personal.completeness_state='unavailable'` on a chart-less `routers/muhurat.py` call | reaches the route's `windows[]` and `useMuhuratFinder` | survives | absent | route test + UI hook fixture |
| Delivery (IP-10a) | COMPUTATIONAL_CORRECTNESS | X | same sentinel via `kala_elect_get` | **gated** — no path today; passes only when the disclosure packet lands | — | — | IP-10a sentinel |
| Revision | COMPUTATIONAL_CORRECTNESS | S | change one YAML weight **and clear the loader cache** | `weights_hash` changes; `legacy_score` changes | versioned; cache-aware | silent (a stale `@lru_cache` read) | test file |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | R | frozen Q10 / ordinary-period question | the verdict states which claim bound the answer; the float cannot | — | no distinction | baseline |
| Evaluation | — | — | `not_applicable`: an election is an initiation-suitability claim, not an outcome prediction (Product §10) | — | — | — | — |

Binding: **OFFERS** B1 (`t_start/t_end`, `inclusivity` on the window, `time_basis`, `claim_grain`),
B2 (`completeness_state`, `epistemic_class`, `operator_role`, `comparable_with`, `tier_basis`,
`source_qualification` — **not** `corpus_verifiable` or the R-6 four), B3 (`window_id`, `generation`,
`window_ref`), B5 (`coverage`, seven keys). **B4:** proposed n/a — scores here are per-day facts, not
aggregated witnesses — but B4's downstream rule binds "any projection carrying a score", so the
exemption is put to the binding owner as a decision (§10.6), not asserted. **DEMANDS** nothing from
L3; L1 janma nakṣatra by `fact_id`. **Asset-local:** `location_used`, `coords_source`, `tz_source`,
`legacy_score`, `weight_source`, `weights_hash`, `contributions`, `context`, `vetoes`, `criterion`,
`vetoed_excluded`, `candidates_evaluated`, `dropped_by_finder`, `returned`, `top_n`, `truncated`.

---

## §8 — Prioritization

(1) catalog honesty (three false claims incl. the stale comment) → (2) routes through the service
(`INTEGRATE` — makes everything else reachable) → (3) typed verdict from `breakdown`, carrying the
aṅga context → (4) `location_used` typed on both routes → (5) coverage under the §10.2 option + cap
→ (6) `criterion` → (7) citations (DP02) → (8) IP-10a and the single-observer item to their owners.
T0; W2/W7; fan-out: none inside L3 today.

---

## §9 — Disposition, target state, walkthrough

`INTEGRATE` + `ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after the `[S]` rows;
`CONSUMER_INTEGRATED` when both sidecar routes serve the verdict with the sentinel on `main`.
Campaign: `ANALYZED → ENRICHED` (the pair is the campaign ladder named in
`KALA_ACCEPTANCE_RECORD_CONTRACT_v1_0.md`; if it is not, the field carries `PRODUCER_READY` alone —
N18). Non-claims: no `DATA_ACCEPTED`; `VALUE_EVALUATED` N; *"reusable partial capital"* (Product
§3.11); **`kala_elect_get` is not integrated by this brief**.

**Walkthrough (ordinary period).** A person with no chart asks the muhūrat finder for a
*gṛhapraveśa* date next month. Served: three days within 2 points; `criterion='nearest'` names the
earliest un-vetoed day; `personal.completeness_state='unavailable'` (no chart — not a lower number);
`location_used.coords_source='caller'`, `tz_source='canonical_default'`;
`coverage.completed_horizon` = the whole month, `exclusions` = one Saturday Aṣṭamī with
`reason='vetoed'` plus the below-cut days with `reason='below_top_n'`. Nothing dramatic; nothing
invented.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Fence: is `platform/python-sidecar/muhurat/` (scoring/judgement, sidecar-local, no declared owner) inside this asset's fence?** Editing `finder.py` touches no `panchang_engine` file | **yes** — and then take coverage option (a) |
| 2 | **Coverage option: (a) finder returns all candidates + counts; (b) no finder edit, `top_n = len(horizon)` and cut in the service, with `dropped_by_finder` declared as a conflated vetoed/zero count; (c) rejected** | (a) if decision 1 is yes, else (b) with the approximation stamped |
| 3 | **IP-10a + the single-observer item:** the disclosure packet for `kala_elect_get`, and `panchanga_daily`'s one-observer calendar raised to L0/L4 | yes, both; add IP-10a to blueprint §12.2; branch A dropped on vocabulary grounds |
| 4 | **Add a tāra veto?** Today Vadha is a 0.00 grade, not a veto. Adding one is a new rule needing a DP02 source, and it makes the returned *set* depend on `native_chart` | rank by calendar, carry the grade as testimony; add a veto **only** with a cited source and the set-dependence declared |
| 5 | Should `/muhurta_score` accept a caller location (a request-model + descriptor change)? | not required for the verdict; decide separately |
| 6 | **B4 exemption:** this asset carries scores but no aggregated testimony — does `independence_group` bind? | put to the binding owner; the brief does not assert the exemption |
| 7 | `criterion` default for the served routes | `nearest` for "when may I begin"; `strongest` on request |
| 8 | Rule-family citations (DP02) | yes |

---

## §11 — Not verified here

1. Live registry state (`depends_on`, migration 676 applied) — migration text only.
2. Cap incidence, latency — unmeasured.
3. `47131772b` content — subject line only [A].
4. Whether the single-observer location is disclosed anywhere on the `kala_elect_get` envelope —
   grep found no location field; not read end to end.
5. `routers/muhurat.py:34` and `panchang_engine/__init__.py:457` tz defaults of 330 — recorded,
   outside the service.
6. No prior native ruling on the criterion vocabulary was found beyond the blueprint.
7. Whether `ANALYZED`/`ENRICHED` are the campaign ladder's own names — not located in the template,
   guide, Strategy or the acceptance-record contract (N18).

## §12 — Review dispositions

**v1.0 → v1.1 (20 findings).** 16 resolved, 4 partial — F1 (consumer map rewritten); F2 (§3a/§3b);
F3 (`breakdown` as capital); F4 (criterion vocabulary); F5 (float readers); F6 (Negative split);
F7 (Delivery restated); F8 (`weight_source`); F9–F20 (scale, inclusivity, paths, `estimated_seconds`,
weights version, anchors, effect size, tz default, catalog, Evaluation row).

**v1.1 → v1.2 (18 findings, all accepted).** N1 (`may_touch` + §1 + §5 + §10.1 — the finder's real
path and the false dichotomy); N2 (§3a, §4.5 three options, §10.2); N3 (§1, §2.4, §4.3, §4.9, §5,
§6-C, §10.4 — Vadha is a grade; a veto is a new rule); N4 (§1, §4.10, §7 Relevant-influence);
N5 (`may_touch` → `interface_packet_targets_not_may_touch`); N6 (§4.11 — disclosure packet,
cross-asset item, branch A dropped); N7 (§4.4 — response-side, two sources); N8 (§2.2, §4.12 — line
numbers and the stale comment); N9 (§2.2, §2.4, §4.9, §7 Missing, §9 — four conjuncts, `{4,8,9,14,30}`,
one-day fixture); N10 (§7 Duplication = the contribution-sum identity); N11 (§7 verdict-tier column);
N12 (§4.7 — window inclusivity vs horizon inclusivity); N13 (§2.4, §4.2, §7 Revision — merged dict,
canonical serialisation, cache); N14 (§4.2 `calendar.context`, §5 PRESERVE, §7 Positive); N15 (§0,
§2.3, §6-G); N16 (§4.7 B3, §7 binding, §10.6 B4 as a decision); N17 (§2.2, §11.5); N18 (§9, §11.7).
