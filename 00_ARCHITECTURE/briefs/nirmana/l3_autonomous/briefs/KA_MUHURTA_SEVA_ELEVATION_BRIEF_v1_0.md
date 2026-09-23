---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_MUHURTA_SEVA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / blob 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows in §7
asset_or_interface_ids: ["ka_muhurta_seva", "interface: kala_elect_get / call_muhurta_score / muhurta_finder (Pūrṇa), routers/muhurta_score.py (sidecar)"]
goal_objective: "Make ka_muhurta_seva's election verdict typed rather than scalar: calendar quality, personal suitability and undertaking constraints carried as three separately-qualified components with vetoes as vetoes, the searched horizon and cap disclosed, the location that was actually used declared on every answer, and a named comparator — so that 'the best window in your range' can never be read as 'a good window', and a chart-less request scored at a default city can never pass as personal."
source_revision: "9feac52d7 (l3/kala-layer-briefs; = origin/l3/kala-elevation-readiness tip 2026-09-24)"
accepted_upstream_contract: "L0 pañcāṅga/calendar substrate (accepted L0 revision f6fed12c7; the Muhūrta lattice's reference-location and midpoint approximation are disclosed in VA §4.4); L1 chart_facts for the native overlay (janma nakṣatra)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_MUHURTA_SEVA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_muhurta_seva/{service,writer}.py", "platform/python-sidecar/routers/muhurta_score.py (sidecar route; coordinated — it is a served path)", "platform/python-sidecar/tests/l3/test_ka_muhurta_seva*.py", "interface packet only: platform-mcp/src/tools/kala_views/elect.ts, platform-mcp/src/tools/muhurta_finder.ts, platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts (call_muhurta_score)"]
must_not_touch: ["panchang_engine/** (shared Swiss-state span; L0 pañcāṅga authority)", "bg_* muhūrta lattice tables (L0)", "pipeline/orchestrator/writers/ph_muhurta.py (L4 reader, sealed — compatibility constraint)", "pipeline/orchestrator/writers/ka_sangam.py, ka_vighnakara.py (readers; their packets)", "platform-mcp/src/tools/kala_views/** except as an interface packet", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the typed verdict (stage 3); CONSUMER_INTEGRATED when elect.ts / call_muhurta_score serve the components with the L3-owned sentinel; data-bound use W7"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; no t3 event today"
wave: "W2 (service proof); W7 (accepted-input use)"
shape: single asset, service/probe, global scope
evidence_base: >
  Source read directly on 9feac52d7 [V]; Lane D §10, T1 Frontier row, Lane E §1 Q-K09/K10 and
  §5.8, Lane F §1d (P11 orphan citation) [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_muhurta_seva` elevation brief — election as three claims, not one number

## §0 — The recommendation, in one paragraph

Election is the layer's **best-served object today**: `kala_elect_get` returns classified empties,
a real falsifier and tāra-bala vetoes as vetoes (Lane E §5.8). Underneath it, the service returns
**one float** for a day (`score(...) -> float`, `service.py:78-85` [V]) that folds together three
claims the register and Product §3.11 say must stay distinct — general calendar quality, personal
suitability (an *optional* native overlay), and undertaking-specific constraints — and its window
search returns the top ten by that float (`find_windows(..., top_n=10)`, `:121-150` [V]) with no
record of how many candidates were evaluated or what resolution. The served `muhurta_score` route
then scores chart-less requests at a **canonical default location (Bhubaneswar)**
(`routers/muhurta_score.py:35-36,54,131-134` [V]) — exactly the "personal relevance from
chart-page placement" Product §10 forbids, in reverse: a general answer wearing a location it
did not receive. Recommendation: **`ENRICH_CORRECT` + `QUALIFY_LIMIT`** — a typed
`MuhurtaVerdict` with the three components carried separately, each with its own
`completeness_state` (personal = `unavailable` when no native chart, never a silently unchanged
number), vetoes as hard vetoes, `coverage` (window, resolution, candidates evaluated, vetoed,
returned, `top_n` disclosed), the location actually used declared on every answer, a named
`criterion` (Q7), and the float kept one generation as `legacy_score` for the four readers. No
table, no rows. Decision for the native: the election criterion, and whether personal
suitability may enter the ranking or only veto (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:158) | *"Calendar/action-time computation and search service. P/I/Q: calendar correctness, personal suitability and outcome are distinct; real undertaking constraints and scope. DP07/09."* | the three-claims obligation is this brief's §3 |
| Strategy §6.1 **L3-A03** | *"Test actual time/location and undertaking constraints; distinguish general calendar from personal feasibility and outcome expectation. Service-health proof alone is insufficient."* W2; real accepted-input use W7 | unchanged |
| Strategy §2 **L3-Q10** | *general calendar, personal suitability, action constraints and outcome expectation remain separate*; proof = *actual interval intersection, location/date fidelity, binding-constraint explanation* | the brief's value frame |
| Product §3.11 | pañcāṅga, Praśna and Muhūrta are distinct practices; *"existing Praśna cast and Muhurat Finder services are reusable partial capital, not proof of fully qualified specialized practice"* | binds §9 non-claims |
| Product §10 (calendar family) | *"date/location/time-zone fidelity"*; initiation suitability must not become guaranteed outcome | the default-location finding (§3) |
| VA §4.4 | the inspected Muhūrta lattice uses a reference location and a disclosed midpoint approximation; consumers must preserve location/horizon/precision | L0's disclosure; this service must carry it |
| W0 field register #14 | `service score / find_windows → float / MuhuratWindow`, zero DML | unchanged |
| W2 source `47131772b` | four service payload shapes frozen DB-free | this brief proposes an additive change to the payload (§5) |
| Lane D §10 / T1 | LIVE, medium confidence: `call_muhurta_score`, `muhurta_finder.ts` reuse `score_muhurat()`; **no proving-journey citation** despite P11; Q7 names it | consumers confirmed and widened here [V] (§2.3) |
| Lane E Q-K09/K10, §5.8 | the layer's best-served object; `elect.ts:288-290` honest "no clean election"; `:296-299` falsifier is about the window, not the outcome — *correct, do not "fix"* | preserved (§5) |
| DAG reconciliation §2 | live `depends_on = {}` by migration 676 (writer touches no producer table); seed still says `['ka_graha_sancara']` — documented permanent divergence | seed on this base still `['ka_graha_sancara']` (`asset_registry_seed.ts:2274` [V]) |
| Elevation plan Q7 | "nearest vs strongest — by which criterion?" names `muhurta_seva` | §10 |
| Blueprint v5.0 §3.5 row 3, §12.1 Comparison/election row, §16.2 | `criterion` named; constraint separation typed; ordinary-period fixture | binds §4 |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V seed]
`asset_registry_seed.ts:2268-2276`: `storage_type: 'service'`, no table, `depends_on:
['ka_graha_sancara']` (live: `{}`), `scope: 'global'`, `estimated_seconds: null`,
`asset_kind: 'service'`.

### 2.2 The code [V]
- **Writer** `services/ka_muhurta_seva/writer.py:1-25`: FORENSIC self-test on the birth pañcāṅga
  (Śukla Tṛtīyā, Ravivāra, Pūrva Bhādrapadā, Śiva, Garaja — the five CLAUDE.md §B anchors) and
  an assertion that the knockout path fires on compound-inauspicious inputs; writes
  `service_health` + `selftest_detail`; `WriterResult(rows_inserted=0)`. Conformant.
- **Service** `services/ka_muhurta_seva/service.py`:
  - `_validate_location` (`:37-60`): `location` **required**, keys `lat, lon,
    tz_offset_minutes`, range-checked; *"never silently assumed"* (`:6`).
  - `KaMuhurtaSevaService.score(date, location, event, native_chart=None, weights=None) -> float`
    (`:78-119`): scores **one local calendar date**; `native_chart` optional — *"When
    birth_nakshatra_id=25 (Purva Bhadrapada), the native overlay is active and will produce a
    real Tāra Bala score instead of being skipped (the 'un-floor' contract)"* (`:91-97`);
    `weights` optional override (*"for testing / overrides"*), else per-event YAML weights.
  - `find_windows(event, window, location, native_chart=None, weights=None, top_n=10) -> list`
    (`:121-150`): *"top-N auspicious windows… sorted by score descending, length <= top_n"*;
    validates `window.date_from/date_to`.
  - module-level `score` / `find_windows` (`:178-207`) delegate to a singleton.
- **Served sidecar route** `routers/muhurta_score.py:73` `muhurta_score(req)`: for chart-less
  requests uses *"the same canonical default location already established for chart-less
  panchang lookups"* (`:35-36`), `# Canonical default location for chart-less panchang compute`
  (`:54`), response `location: {…, note: "canonical default location (Bhubaneswar, IST) — this
  service's …"}` (`:131-134`).
- **`elect.ts`** (Pūrṇa): 3-state coverage entries (`computed` / `not_in_corpus` /
  `honestEmptyCoverage`, `:310-335`), tāra-bala hard veto (`:202-203`), `empty_reason` (`:226`),
  thesis text for the all-vetoed case (`:288-290`), falsifier about the window (`:296-299`).

### 2.3 Consumers (grep on this base, tests excluded) [V]
| consumer | reads | role |
|---|---|---|
| `platform-mcp/src/tools/muhurta_finder.ts`; `kala_views/elect.ts` | `find_windows` / score via the sidecar | `computation` (served) |
| `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` (`call_muhurta_score`), `L3_kala/index.ts`, `L0_brahmagyan/call_panchanga_service.ts`, `service_manifest`, `producer_editorial_review.ts` | the route | served / catalog |
| `routers/muhurta_score.py`, `routers/nirmana_probe.py` | the service | route / probe |
| `writers/ka_sangam.py` | pañcāṅga term | `applicability` |
| `writers/ka_vighnakara.py` | rikta-tithi obstruction | `counterevidence` |
| `writers/ph_muhurta.py` (L4, sealed) | score | `computation` (L4) |
| `writers/ka_graha_sancara.py`, `service_probes.py`, `asset_runner.py` | import / probe | probe |

**Live-path statement.** The service is live on three served surfaces and inside two L3 writers
and one sealed L4 writer. The default-location path is live for chart-less requests. `find_windows`'
`top_n=10` is live on every window search.

### 2.4 Epistemic class of the important quantities
| quantity | class | authority | note |
|---|---|---|---|
| tithi / vāra / nakṣatra / yoga / karaṇa at a date+location | `COMPUTED_FACT_CONFIGURATION` | L0 pañcāṅga engine | location-dependent (sunrise); the route's default location changes the *subject* |
| per-event rule weights (YAML) | `QUALIFIED_RULE` **only if each rule family is cited**; else engineered | this service's YAML — citation status **not verified here** (§11) | `source_qualification` per family owed |
| tāra-bala / personal overlay | qualified rule (nava-tārā) | this service + L1 janma nakṣatra | `unavailable` when no native chart — today the score is simply lower/"skipped" |
| the composite `float` | `INTERPRETIVE_INFERENCE` (engineered composite) | this service | one scalar over three claims — §3 |
| gold/silver/bronze | presentation over the scalar | `elect.ts` | inherits the flattening |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; W2 source accepted. t3: no event. Cost: per-day pañcāṅga compute over a window;
unmeasured (`estimated_seconds` null — correct). `find_windows` over a 90-day window = 90 daily
scores; cheap in aggregate, **unmeasured**.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | `score(date, location, event)` and `score(date, location, event, native_chart)` both return a single float; the second is *different* but carries no field saying the personal overlay was applied, and the first carries none saying it was **absent**. A caller — `elect.ts`, `ph_muhurta`, `muhurta_finder` — receives `0.71` and cannot tell "general calendar 0.71, personal not evaluated" from "calendar 0.80 pulled down by a personal veto that did not quite disqualify". `find_windows` returns ≤ 10 by that float with no `candidates_evaluated`, `resolution` or `truncated`. The served route answers chart-less requests at Bhubaneswar and labels the location in a `note` string, not a typed field |
| Evidence | `service.py:78-85` (`-> float`), `:91-97` (optional overlay "skipped"), `:121-150` (`top_n=10`, `length <= top_n`); `routers/muhurta_score.py:35-36,54,131-134` [V]; `elect.ts:166` (gold/silver/bronze normalisation of *"the ALREADY-COMPUTED score/veto"*) [V] |
| Expected contract | Register: *calendar correctness, personal suitability and outcome are distinct*; L3-Q10: *general calendar, personal suitability, action constraints and outcome expectation remain separate*; Product §5.2 (no scalar substitutes); F06 (no fallback collapses `applied`/`unavailable`); Strategy §3 *Comparison/election* (*"no universal ranking or hidden hard cap"*); Product §10 location fidelity |
| Defect class | **flattened** (three claims → one float) + **detector mismatch** (absent personal input reads as a number, not a state) + **wrong context** (a default location on a served personal-looking answer) + an undisclosed cap |
| Impact | Q-K09's *"the best window in your range is not a good window"* cannot be stated from the payload; Q10's *binding-constraint explanation* is unavailable (which of the three claims bound?); a person outside Bhubaneswar can be served sunrise-dependent tithi transitions for the wrong city as if personal |
| Non-claim | No claim that any specific served answer was wrong for the native (whose location *is* Bhubaneswar); no claim about the YAML rules' doctrinal validity; the cap's live effect (how often > 10 candidates exist) is unmeasured |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q10 directly; Q-K09/K10; Q02's election half under a **named criterion** (Q7).
   Cannot serve Q01–Q08 (not a window/mechanism producer).
2. **Typed verdict (binding B2), the float retired one generation later.** `MuhurtaVerdict =
   {calendar: Component, personal: Component, undertaking: Component, vetoes: [Veto],
   criterion, coverage, location_used, legacy_score}` where `Component = {value, weight_source,
   completeness_state, source_qualification, rule_ids[]}`:
   - `calendar.completeness_state='applied'` always (pañcāṅga computed); `source_qualification`
     per rule family (`verse_cited` / `algorithmic_approximation` / `unsourced`) — the YAML
     families must each cite or be stamped `unsourced` (L0 request where needed, DP02);
   - `personal.completeness_state='unavailable'` when `native_chart` is None; `applied` when the
     nava-tārā overlay ran; **never a silently lower number**;
   - `undertaking.completeness_state='applied'` for the event's declared constraints,
     `inapplicable` for constraints the event does not carry;
   - `vetoes` are **hard** (tāra-bala vadha, rikta on a `disqualifying` event) and separately
     listed, never a penalty folded into `value` (Q-K09: *"hard vetoes applied as vetoes"*);
   - `epistemic_class='INTERPRETIVE_INFERENCE'` on the composite, `COMPUTED_FACT_CONFIGURATION` on
     the pañcāṅga facts; `operator_role` per component (`computation` / `applicability` /
     `exclusion`); `comparable_with='self'` within one event type, `different_convention` across
     events (a *vivāha* score and a *gṛhapraveśa* score are not one scale); `tier_basis='relative_uncalibrated'`.
3. **Location declared, never defaulted on a personal surface (B1).** `location_used = {lat, lon,
   tz_offset_minutes, source ∈ {caller, chart, canonical_default}}` on every answer; the route's
   Bhubaneswar default stays permitted for **chart-less** calls but the field makes it visible,
   and `elect.ts`/`call_muhurta_score` must pass the chart's location for chart-bound calls
   (interface packet).
4. **Coverage (B5) on every search.** `coverage = {requested_horizon, completed_horizon,
   resolution:'calendar_day', candidates_evaluated, vetoed, returned, top_n, truncated: bool,
   completion_detector}`; an empty result is a row with coverage (already `empty_reason` in
   `elect.ts` — the service supplies the numbers).
5. **Criterion (Q7).** `criterion ∈ {nearest_clean, best_scored, robust}`: `nearest_clean` = the
   earliest un-vetoed candidate; `best_scored` = highest `calendar` (with personal applied where
   available); `robust` = un-vetoed under all declared variants (e.g. both tithi-boundary
   conventions) — `unavailable` until variants exist. The served surface names which it used.
6. **Time discipline (SC-1).** Day-grain is honest for muhūrta *search* (`claim_grain='date_grain'`
   declared); the chosen window's instants (sunrise-relative muhūrta boundaries) carry
   `t_start/t_end` as `timestamptz` at the declared location; `inclusivity='closed_open'`; no
   `date.today()` (the horizon is the caller's).
7. **Old vs new.** Positive: canonical chart, 90-day window, *vivāha* → components + vetoes +
   coverage; `personal.applied`. Negative: no native chart → `personal.unavailable`, `calendar`
   unchanged. Boundary: a tithi that changes at 05:58 local at Bhubaneswar vs 06:40 at another
   longitude → different `calendar` **and** different `location_used`. Missing: every candidate
   vetoed → empty with coverage (`vetoed = candidates_evaluated`). Duplicated: n/a.
8. **Simpler baseline.** The current float + gold/silver/bronze.
9. **Ablation.** Remove `native_chart`: today the float changes and nothing says why; after, the
   float (`legacy_score`) changes *and* `personal.completeness_state` flips to `unavailable` — the
   added distinction is that flip. Remove the personal component from the ranking (criterion
   `best_scored` with personal excluded): if the top window never changes for the canonical chart,
   the personal overlay is decorative for this native and the brief says so.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the location-required contract (`:37-60`); the knockout/veto path; the five forensic
  anchors; the per-event YAML weights (as data, citation status to be stamped); `elect.ts`'s
  falsifier and three-state coverage (Lane E §5.8 — *"correctly bounded today"*).
- `ENRICH_CORRECT`: the typed verdict; coverage; `location_used`; `criterion`.
- `QUALIFY_LIMIT`: `claim_grain='date_grain'` on the search; `source_qualification` per rule family.
- **Compatibility**: the float stays as `legacy_score` for one generation — readers: `elect.ts`,
  `muhurta_finder.ts`, `call_muhurta_score`, `routers/muhurta_score.py`, `ka_sangam.py`,
  `ka_vighnakara.py`, **`ph_muhurta.py` (sealed L4)** — the L4 reader must not change; additive
  payload only.
- **Fences**: `panchang_engine` untouched (L0, shared Swiss span); no `kala_views` edits — the
  three TS surfaces change by interface packet with an L3-owned sentinel; the sidecar route
  (`routers/muhurta_score.py`) is L3-adjacent and changes in the same packet.
- No table, no migration, no rows; rollback = payload flag.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_muhurta_seva`, L3 service, global; epistemic: L0 pañcāṅga facts + qualified/engineered election rules + engineered composite; placement correct (election is a Kāla object); `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | live `depends_on={}` (676) — correct for a pure service; seed stale by policy; reads L0 pañcāṅga at call time; no hidden table |
| C | invariants: a hard veto never yields a returned window under `nearest_clean`; `calendar` invariant to `native_chart`; location change → pañcāṅga change; golden: the five forensic anchors; boundary: tithi transition across sunrise |
| D | n/a rows; **rule citations are the data gap** (which YAML families are verse-cited) — DP02 request |
| E | seven consumers (§2.3); no duplication; `ph_muhurta` is the compatibility anchor |
| F | components + states + `location_used` machine-readable; gold/silver/bronze becomes a projection of `calendar`, not of the composite |
| G | unmeasured; a 90-day search = 90 daily pañcāṅga computes — **justified no-change** until measured |
| H | idempotent; no writes; timeout from measured search latency |
| I | files in `may_touch`; W2; interface packet for three TS surfaces |
| J | this brief; §7; review report; the ablation record |

---

## §7 — Proof matrix

| proof | fixture | expected | invariant | detector fails when… |
|---|---|---|---|---|
| Positive | canonical chart, *vivāha*, 90 days, chart location | `MuhurtaVerdict` with three components, `personal.applied`, coverage numbers | `legacy_score` equals today's float | any component missing; float differs |
| Negative | unknown event; `location=None` | `ValueError` (unchanged); `inapplicable` for absent constraints | location never defaulted in the service | a default location appears in a service call |
| Relevant influence | supply vs omit `native_chart` | `personal.completeness_state` flips; `calendar.value` unchanged | calendar invariant | calendar moves |
| Irrelevant control | reorder YAML rule keys; `weights` identical dict in different order | identical verdict | order-invariant | differs |
| Duplication | a rule counted in two families | one `rule_id`, one contribution | no double weight | weight doubles |
| Context | chart-less route call | `location_used.source='canonical_default'` typed | visible | absent / string-only |
| Boundary | tithi transition 05:58 vs 06:40 local at two longitudes | different `calendar` and `location_used` | sunrise-dependent | same answer |
| Delivery | sentinel `personal.completeness_state='unavailable'` | reaches `kala_elect_get`'s envelope and the saved reading | survives `elect.ts` | absent |
| Revision | YAML weights change | `weight_source` version changes; `legacy_score` changes | versioned | silent |
| Value | frozen Q10 / ordinary-period question | the payload states which claim bound the answer; the float cannot | — | no new distinction |

Binding: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `claim_grain`), B2 (all), B5
(`coverage`). **DEMANDS** nothing from another L3 asset; L1 janma nakṣatra by `fact_id`.

---

## §8 — Prioritization

(1) `location_used` + the chart-bound location on served calls (wrong context) → (2) the typed
verdict with `personal.unavailable` (flattening/detector) → (3) coverage + `top_n` disclosure
(Q8 cluster) → (4) `criterion` (Q7) → (5) rule-family citations (DP02). T0 service; W2 proof, W7
data-bound; no P-candidate; fan-out: Saṅgam, Vighnakara, L4 — additive only.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT` (service terminal rule). Data-plane: `PRODUCER_READY` after §7;
`CONSUMER_INTEGRATED` when `elect.ts` serves the components at a `file:line` on `main` with the
sentinel. Campaign: `ANALYZED` → `ENRICHED`. Non-claims: no `DATA_ACCEPTED`; `VALUE_EVALUATED` N
until the baseline's Q10/ordinary-period case shows the distinction; *"reusable partial capital,
not proof of fully qualified specialized practice"* (Product §3.11) — this brief qualifies the
service, it does not make it a complete Muhūrta practice.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Q7 — the election criterion the served surface names** | `nearest_clean` as the default for "when may I initiate"; `best_scored` on request; `robust` when variants exist |
| 2 | **May personal suitability enter the ranking, or only veto?** | **Rank by calendar, veto by personal** — a personal overlay that ranks would re-create the composite; the nava-tārā doctrine is a veto (vadha) and a grade, so carry the grade as testimony, rank on calendar |
| 3 | Chart-less route calls: keep the canonical default location with `location_used` declared, or refuse? | keep, declared — refusing would break the L0 calendar family |
| 4 | Rule-family citations: an L0 request for the YAML families' sources | yes (DP02) |

---

## §11 — Not verified here

1. Which YAML rule families carry a classical citation — the YAML was not read; stamped per family
   at stage 3.
2. The `top_n` cap's live effect — unmeasured.
3. Whether `elect.ts` passes the chart's location or the default for chart-bound calls — the TS
   call path was not traced end to end; the interface packet's sentinel settles it.
4. Search latency — unmeasured.
5. No database query.
