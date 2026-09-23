---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_GRAHA_SANCARA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review; APPROVED_FOR_EXECUTION only by native record
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / blob 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows in §7
asset_or_interface_ids: ["ka_graha_sancara", "SC-8 (convention vector: backend assertion)", "SC-10 (ayanāṃśa vocabulary)"]
goal_objective: "Make ka_graha_sancara one service with one ayanāṃśa vocabulary, an asserted ephemeris backend and typed failure semantics, whose live route and registered engine are provably the same computation — so that the position substrate four overlay writers and every arbitrary-instant query stand on is qualified beyond a single forensic instant."
source_revision: "9feac52d7 (l3/kala-layer-briefs; = origin/l3/kala-elevation-readiness tip 2026-09-24)"
accepted_upstream_contract: "L0 bg_ephemeris (accepted L0 revision f6fed12c7); L0 items 6–7 applied (node frame + epoch declared on ephemeris_daily rows, PR #2727, migrations 1075–1079 applied to production)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_GRAHA_SANCARA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_graha_sancara/engine.py", "platform/python-sidecar/pipeline/orchestrator/writers/ka_graha_sancara.py", "platform/python-sidecar/routers/ephemeris.py:200-260 (the ephemeris_at_t route; coordinated — it is the live path)", "platform/python-sidecar/tests/l3/test_ka_graha_sancara*.py, tests/test_m3_graha_sancara_defects.py"]
must_not_touch: ["brahmagyan/l0_ephemeris.py and ephemeris_daily (L0 authority)", "panchang_engine/swiss_state.py (shared serialization span, DP-SD-010)", "pipeline/transit_search.py (frozen L0 digest closure)", "services/ka_kota_chakra, ka_moorti_nirnaya, ka_sudarshana_varsha, ka_vedha_gochara (importers; their briefs)", "platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts (Pūrṇa; interface packet only)", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the qualified service contract; CONSUMER_INTEGRATED when the parity test binds the live route"
target_state_campaign: "ANALYZED (this brief) → OPTIMIZED/JUSTIFIED at stage 3; no t3 event today"
wave: "W2 (service proof)"
shape: single asset, service/probe, global scope
evidence_base: >
  Source read directly on 9feac52d7 [V]; Lane D §4, T1 Frontier row, STATE.md ★ finding
  (divergent implementations), Lane F §2a, synergy audit §2 (backend/G4) [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_graha_sancara` elevation brief — the position substrate

## §0 — The recommendation, in one paragraph

`ka_graha_sancara` is the layer's position/motion service and the import hub for four overlay
writers (Kota, Moorti, Sudarśana, Vedha). It is correct at the one instant its self-test checks,
and unqualified everywhere else: it carries a six-name ayanāṃśa vocabulary that is not the
`chart_facts` vocabulary, hard-gates its live path to the literal `'lahiri'`, never asserts which
ephemeris backend answered, and is **not the code the live `call_ephemeris_at_t` route runs** —
that route has its own swisseph integration with its own vocabulary map. Two implementations of
one service, no parity test between them, and a self-test that certifies the one nobody calls
(STATE.md ★). Recommendation: **`INTEGRATE` + `QUALIFY_LIMIT`** — one canonical vocabulary (the
`chart_facts` ids) in both; the engine declared the reference and the router bound to it by a
parity test at N instants; `ephemeris_backend`, `time_basis` (`noon_ut_knot` for the stored path,
`event_instant` for the live path), `claim_grain`, `node_mode` and `ayanamsha_id` asserted on every
response; failure semantics typed (`unavailable`, never an exception across the route boundary);
the self-test extended from one forensic instant to arbitrary-instant, out-of-range and
non-lahiri cases. No rows, no table, no orchestrator change. The decision for the native: which
implementation is the reference (§10).

---

## §1 — Already established

| record | what it says | delta on this base |
|---|---|---|
| Contribution register §5 (REGISTER:136) | *"Position/motion service. P/I/Q: arbitrary instant/frame provenance; self-test is bounded service proof. DP07."* | unchanged |
| Strategy §6.1 **L3-A01** | *"Preserve numerical service and state safety. Prove exact conventions, time, arbitrary-chart input, provenance and failures; a canonical probe is not full service qualification."* W2 | unchanged; this brief is that qualification |
| W0 field register #7 | `service get_ephemeris → EphemerisResult/GrahaState`, zero DML | unchanged |
| Lane D §4 / T1 | self-test writes `service_health`; **DIVERGENT** consumer: `call_ephemeris_at_t` → `/api/compute/ephemeris_at_t` with its own `import swisseph` (documented, deliberate) | confirmed [V]: `routers/ephemeris.py:5` `import swisseph as swe`; `:200-260` the `ephemeris_at_t` route with `_AT_T_DEFAULT_AYANAMSHA` and a canonical-id→`SIDM_*` map noting *"Lahiri and Lahiri (Chitrapaksha) are the same ayanamsha under two names"* (`:215-223`) |
| STATE.md ★ (2026-09-20) | the two paths have **different ayanāṃśa vocabularies** and can silently drift; a value test on the engine certifies something no caller touches | confirmed [V]: engine `SUPPORTED_AYANAMSHAS = {"lahiri","raman","kp","krishnamurti","yukteshwar","surya_siddhanta"}` (`engine.py:64`); `chart_facts` ids are `{lahiri_chitrapaksha, true_chitra, krishnamurti, raman, surya_siddhanta_classical}` [A] |
| Lane F §2a | `engine.py:302-306` hard equality gate `if ayanamsha != "lahiri": raise NotImplementedError` on the live path | on this base at `:306-309` [V]; default `ayanamsha="lahiri"` at `:346` [V] |
| Synergy audit §2 / blueprint G4 | the ephemeris backend is process-global and unowned; `panchang_engine` forces Moshier; nothing asserts per call | this engine sets no path and asserts no backend [V: no `set_ephe_path`/`retflag` in `engine.py`] |
| L0 items 6–7 (PR #2727) | node frame (mean) and epoch (noon UT) declared on `ephemeris_daily` rows | the engine's PATH-A reads `bg_ephemeris` rows at `date` grain (`:173-260`) — whether it surfaces those declarations is the delta (§4) |
| Blueprint v5.0 §3.5 row 1, §16.2 | hub for kota/moorti/sudarśana/vedha (engine import) | digest ripple to four writers — coordinated packet (§5) |
| Elevation plan §6 item 5 | *"the divergent-implementation finding is unverified by me"* | **verified here [V]** (this brief's §2.3) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Identity and registration [V seed]
`asset_registry_seed.ts:2236-2244`: `storage_type: 'service'`, no table, `depends_on:
['bg_ephemeris']`, `scope: 'global'`, `estimated_seconds: null`, `asset_kind: 'service'`.

### 2.2 What the code is [V]
- **Writer** `writers/ka_graha_sancara.py:1-30`: FORENSIC self-test at 1984-02-05 10:43 IST — nine
  grahas present with non-null speeds, natal Moon sign = Aquarius (the CLAUDE.md §B anchor);
  writes `service_health='healthy'` + `last_selftest_at`; `WriterResult(rows_inserted=0)`;
  honours `dry_run`; never commits or writes `asset_throughput`. Conformant.
- **Engine** `services/ka_graha_sancara/engine.py`:
  - `get_ephemeris(..., ayanamsha="lahiri")` (`:344-378`): validates against
    `SUPPORTED_AYANAMSHAS` (`:64,:376`); two paths.
  - **PATH-A** `_read_from_bg_ephemeris` (`:173-260`): reads stored **tropical** rows at
    `date` (`:220` `WHERE date = %s AND ayanamsha_id = 'tropical'`) and applies
    `derive_sidereal(trop_lon, jd, ayanamsha)` (`:253`) — so PATH-A is **day-grain** (one row per
    date) with sidereal derived at read; a failed derivation logs a warning (`:255`).
  - **Live path** `_compute_live` (`:284-313`): `if ayanamsha != "lahiri": raise
    NotImplementedError(...)` (`:306-309`); delegates to `get_transit_states(query_dt, q_date,
    ayanamsha=...)` (`:313`).
  - Per-call memo keyed `(date_str, ayanamsha)` (`:141-167`); `GrahaState.applying_or_separating
    (target_lon_deg)` (`:84`) — a Contact-object primitive.
- **Live route** `routers/ephemeris.py:200-260`: `POST /api/compute/ephemeris_at_t` — its own
  `swe` calls, `_AT_T_DEFAULT_AYANAMSHA`, canonical-id → `SIDM_*` mapping (`:215-238`), docstring
  *"Graha longitudes at an arbitrary UTC instant (ka_graha_sancara service)"* (`:244`) — the name
  is borrowed; the engine is not imported (`grep ka_graha_sancara routers/ephemeris.py` → the
  comment only [V]).
- **TS wrapper** `call_service_wrappers.ts:170-240`: `call_ephemeris_at_t` → the sidecar route,
  default `DEFAULT_AYANAMSHA` (`:227`), `PYTHON_SIDECAR_URL` guard (`:239`).

### 2.3 Consumers (search boundary: sidecar `services/`, `routers/`, `pipeline/`; `platform-mcp/src`; `platform/src/lib/retrieval`; tests excluded) [V]
| consumer | reads | role |
|---|---|---|
| `services/ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_sudarshana_varsha`, `ka_vedha_gochara` | engine (`NAKSHATRAS` ordering, transit states) — the hub | `computation` |
| `routers/ephemeris.py` (the served path) | **its own swisseph**, not the engine | the divergence |
| `pipeline/transit_search.py`, `panchang_engine`, `w2g`, Saṅgam scanner | their own swisseph integrations (frozen L0 closure; SC-8 owns backend ownership) | siblings, not consumers |
| `service_probes.py` | DB-free probe | probe |

**Live-path statement.** The engine is live for four overlay writers at build time and for
**no served query**; the served query is live on the router's parallel implementation. Both
reachable today.

### 2.4 Epistemic class of the important fields
| field | class | authority | note |
|---|---|---|---|
| tropical longitude/speed at a knot | `COMPUTED_FACT_CONFIGURATION` | L0 `bg_ephemeris`/`ephemeris_daily` (noon-UT knots, TRUE node stored, mean derived — L0 items 6–7) | PATH-A; `time_basis='noon_ut_knot'` |
| sidereal longitude | computed fact | `derive_sidereal` under a named ayanāṃśa | the ayanāṃśa-application convention (L1 arbitrates `FLG_SIDEREAL`, chronicle §11.10) must be **declared on the response** |
| live instant positions | computed fact | swisseph under the process-global backend (G4) | `time_basis='event_instant'`; backend **unasserted today** |
| applying/separating | computed relation | this engine | Contact primitive; fine |
| `service_health` | status | self-test at one instant | **a detector for one instant only** — §N.8: it cannot go false for the failure classes §3 names |

### 2.5 Ladders and cost
Data-plane `PLAN_REVIEWED`; W2 source accepted (`47131772b`, service payload frozen). t3: no
event. Cost: trivially buildable; per-call latency unmeasured (`estimated_seconds` null — correct).

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Ask for positions at an arbitrary instant with `ayanamsha_id='lahiri_chitrapaksha'` (the canonical `chart_facts` id): the served route accepts it (its `SIDM_*` map treats the two names as one, `routers/ephemeris.py:215-223`); the registered engine **rejects it** (`engine.py:376` `Unknown ayanamsha` — `lahiri_chitrapaksha ∉ SUPPORTED_AYANAMSHAS`) and, on the live path, rejects everything but the literal `'lahiri'` (`:306`). Two answers to "which ayanāṃśa names does this service accept," and no test that would notice if the two implementations' longitudes diverged |
| Evidence | `engine.py:64,306-309,346,376`; `routers/ephemeris.py:5,200-260`; `grep -n ka_graha_sancara routers/ephemeris.py` → naming comment only [V] |
| Expected contract | L3-A01 (*exact conventions, arbitrary-chart input, provenance, failures*); DP01 (*canonical aliases… local representations cannot diverge in meaning*); DP03 (*ayanāṃśa/frame/node… pinned context*); SC-8, SC-10; F28 (a status names the path that can turn it false) |
| Defect class | **wrong authority** (two implementations, no reference) + **detector mismatch** (`service_health` certifies the unused path at one instant) + **wrong context** (vocabulary divergence) |
| Impact | Q-K01/Q03 substrate: a caller using the canonical id gets one answer from the route and an exception from the engine; the four overlay writers stand on an engine whose backend, epoch and node convention are unasserted; any future drift between the two swisseph integrations is invisible (STATE.md ★) |
| Non-claim | No numerical divergence between the two paths is asserted — none was measured; that is the parity test's job (§7). No claim about `transit_search.py` or `panchang_engine` — siblings under SC-8 |

---

## §4 — The semantic delta (contract §4) — smallest sufficient change

1. **L3-Q served.** Substrate for Q01/Q03/Q09 (positions, contacts, convention sensitivity);
   directly Q09 (*what changes with convention* — five ayanāṃśas, one instant, declared method).
   Cannot serve any window question by itself.
2. **One vocabulary (SC-10).** `SUPPORTED_AYANAMSHAS` becomes the `chart_facts` id set
   (`lahiri_chitrapaksha, true_chitra, krishnamurti, raman, surya_siddhanta_classical`) with
   `DEFAULT_AYANAMSHA` as the default; legacy names accepted through one declared alias map
   (`'lahiri' → 'lahiri_chitrapaksha'`) that the router already has (`:215-223`) — moved to one
   place both import. Unknown → `unavailable` with the offending name, never a bare exception at
   the route boundary.
3. **One reference implementation (§10 decision).** Recommended: the engine is the reference;
   `routers/ephemeris.py`'s route delegates to `get_ephemeris` on the live path (or, if the native
   prefers the router as reference, the engine's `_compute_live` delegates to it). Either way a
   **parity test** binds them: N instants (incl. the forensic instant, a station, the 0°/360°
   seam, 1900-01-01 and 2150-12-31 boundaries) → identical longitudes within a declared tolerance
   and identical `ayanamsha_id`, `node_mode`, `ephemeris_backend`.
4. **Convention vector on every response (SC-8, binding B1).** `ephemeris_backend ∈ {swieph,
   moshier}` asserted from the call's own `retflag` (never inferred from a global); `time_basis`
   (`noon_ut_knot` PATH-A / `event_instant` live); `claim_grain` (`date_grain` PATH-A /
   `instant_grain` live); `node_mode='mean'` (D6) with `epoch_convention` from the row (L0 item 7);
   `ayanamsha_application` (`FLG_SIDEREAL` vs subtraction — chronicle §11.10); `ayanamsha_id`.
5. **Failure semantics typed (B2).** Out of `bg_ephemeris` range with a non-lahiri ayanāṃśa →
   `completeness_state='unavailable'` with reason; `derive_sidereal` failure → `unavailable` for
   that graha, never a silently missing key; `epistemic_class='COMPUTED_FACT_CONFIGURATION'`;
   `operator_role='computation'`.
6. **Self-test extended (F28).** The writer's self-test adds: an arbitrary non-forensic instant
   reproduced by the parity fixture; the canonical id accepted; a deliberately out-of-range
   non-lahiri request returning `unavailable`; the backend asserted. `service_health` then has
   four ways to read `unhealthy`.
7. **Old vs new.** Positive: canonical id at the forensic instant → Moon in Aquarius, backend
   named. Negative: `'kp'` (not a `chart_facts` id) → `unavailable(unknown_ayanamsha)` unless
   aliased. Boundary: 2150-12-31 23:59 UTC PATH-A vs live → parity or a declared `unavailable`.
   Missing: `.se1` absent → `ephemeris_backend='moshier'` **asserted**, not silent. Duplicated: n/a.
8. **Simpler baseline.** The current route's own swisseph answer with the current engine unused.
9. **Ablation.** Swap the route to the engine and back: the served longitudes must be identical
   within tolerance (parity) — the elevation is *qualification*, and the test that would show
   value is the one that would have caught a drift (a mutation: change the router's `SIDM_*` for
   one id → parity fails).

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the two-path design (stored knots vs live), the memo cache, `applying_or_separating`,
  the forensic anchor in the self-test.
- `QUALIFY_LIMIT`: PATH-A declared `date_grain` — it must never be reused as an instant answer
  (the Moon moves ~13°/day; a date-grain Moon is not a contact).
- `INTEGRATE`: one vocabulary, one reference, one parity test.
- **Hub rule**: four overlay writers import the engine; their digests shift on any change — the
  packet is coordinated with briefs 7–10 and 22 (Vedha, Gochara family) and re-pinned once.
- **SC-8 boundary**: this brief asserts the backend *per call in this engine*; it does not set
  `set_ephe_path` for the process and does not touch `panchang_engine`, `transit_search.py`, `w2g`
  — those are SC-8's packet.
- No table, no migration, no rows; rollback = revert the route delegation (feature flag at the
  router) and the vocabulary alias map.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_graha_sancara`, L3 service, global scope; epistemic: astronomical computation over L0 knots + live swisseph; placement correct (L3's contact substrate); disposition `INTEGRATE + QUALIFY_LIMIT` |
| B | `bg_ephemeris` declared and real; live path reads swisseph (declared through `bg_ephemeris`'s own dependency); no hidden table read; hub fan-out 4 + the served route |
| C | invariants: monotone JD; sidereal = tropical − ayanāṃśa(jd) under the declared method; node = mean; parity within tolerance; boundary cases at range edges and the seam. Detectors: parity fixture, backend assertion, vocabulary test |
| D | n/a (service); enrichment = qualification fields, not data |
| E | four overlay writers (real); served route (parallel implementation — the defect); siblings under SC-8 |
| F | every response machine-readable with backend/grain/basis; unknown ayanāṃśa typed |
| G | no hotspot measured; PATH-A per-call memo already; **justified no-change** |
| H | idempotent; no writes; timeout from measured latency; no credentials |
| I | files in `may_touch`; W2; coordinated digest re-pin for four importers |
| J | this brief; §7 results; review report; parity fixture output retained |

---

## §7 — Proof matrix

| proof | fixture | expected | invariant | detector fails when… |
|---|---|---|---|---|
| Positive | forensic instant, canonical id | 9 grahas, Moon Aquarius, `ephemeris_backend` asserted | anchor holds | anchor fails or backend absent |
| Negative | `'kp'`, out-of-range date | `unavailable(unknown_ayanamsha)` / `unavailable(out_of_range)` | no exception crosses the route | exception or silent empty |
| Relevant influence | change `ayanamsha_id` `lahiri_chitrapaksha → raman` | longitudes shift by the ayanāṃśa difference; `node_mode` unchanged | delta = Δayanāṃśa | delta ≠ Δayanāṃśa |
| Irrelevant control | alias `'lahiri'` vs canonical | identical payload | alias-invariant | differs |
| Duplication | same instant via PATH-A and live | `time_basis` differs, longitudes within the day-grain tolerance | both labelled | labels equal |
| Context | `.se1` path removed in the fixture | `ephemeris_backend='moshier'` asserted; `retflag` recorded | never silent | backend missing |
| Boundary | 1900-01-01 00:00 and 2150-12-31 23:59 UTC; 0°/360° seam | parity or declared `unavailable` | no wrap error | seam mis-handled |
| Delivery | sentinel `claim_grain='date_grain'` on a PATH-A answer | reaches `call_ephemeris_at_t`'s envelope | survives the wrapper | absent |
| Revision | L0 `ephemeris_daily` regenerated | PATH-A values change, live unchanged | no cache | stale |
| Value | mutation: alter one `SIDM_*` mapping in the router | parity test fails | the test is a detector | passes under mutation |

Binding: **OFFERS** B1 (`time_basis`, `claim_grain`, `inclusivity` n/a), B2 (`epistemic_class`,
`completeness_state`, `operator_role`), SC-8 fields (`ephemeris_backend`, `node_mode`,
`ayanamsha_application`). **DEMANDS** L0's row declarations (items 6–7, applied).

---

## §8 — Prioritization

(1) vocabulary + default (correctness; SC-10) → (2) parity test + reference decision (wrong
authority) → (3) backend/basis/grain assertions (SC-8) → (4) extended self-test. T0 hub; W2; no
P-candidate; blocks nothing downstream except the qualification of the four overlays' inputs.

---

## §9 — Disposition and target state

`INTEGRATE` + `QUALIFY_LIMIT` (service terminal rule: availability, correctness, failure semantics,
**product consumer** — the route — verified; no row-count proxy). Data-plane: `PRODUCER_READY`
after §7; `CONSUMER_INTEGRATED` when the route is bound to the reference at a `file:line` on
`main` with the parity sentinel. Campaign: `ANALYZED` → `OPTIMIZED/JUSTIFIED`. Non-claims: no
`DATA_ACCEPTED` (no data); no `VALUE_EVALUATED` (this asset's value is the absence of drift, shown
by a mutation test, not a reading delta).

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Reference implementation: the registered engine or the router?** | **The engine** — it is the registered asset, the hub the overlays import, and carries the stored-knot path; the router delegates on the live path |
| 2 | Adopt the `chart_facts` ayanāṃśa ids as the one vocabulary, with a single alias map? | Yes (SC-10) |
| 3 | Tolerance for the parity test | propose 0.01″ for identical-backend runs, 1″ across backends — **to be set from measurement at stage 3**, not asserted here |

---

## §11 — Not verified here

1. Any numerical difference between the two paths — not measured; the parity test is the
   instrument.
2. Whether `get_transit_states` (`:313`) sets or asserts the backend — not read; SC-8's packet.
3. Whether PATH-A surfaces L0's new `node_mode`/`epoch_convention` columns — the SELECT at `:220`
   reads tropical rows only; the delta requires it either way.
4. Per-call latency — unmeasured.
5. The `chart_facts` id set is STATE.md's [A]; re-read at stage 3 from `CHART_FACTS_SCHEMA.json`.
