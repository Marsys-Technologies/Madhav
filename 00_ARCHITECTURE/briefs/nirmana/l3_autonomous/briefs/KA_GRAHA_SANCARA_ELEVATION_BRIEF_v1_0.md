---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_GRAHA_SANCARA_ELEVATION_BRIEF
version: "1.2"
status: PROPOSED_FOR_NATIVE_RULING      # v1.0 REWORK (20) → v1.1 ACCEPT_WITH_CORRECTIONS (17 resolved, 3 partial, 17 new) → v1.2 folds all 17
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
asset_or_interface_ids: ["ka_graha_sancara", "SC-8 (convention vector: the node-frame and ayanāṃśa-application deltas plus the field-name mapping)", "SC-10 (ayanāṃśa vocabulary via L0's AYANAMSHA_MAP)", "IP (NEW): the served route's _service_context reaching the TS wrapper — today dropped", "L0 hygiene note: l0_ephemeris.py:77 'Mean North Node' comment over swe_id 11 (TRUE_NODE)"]
goal_objective: "Make ka_graha_sancara one honest position service: its registered engine stops claiming instant precision it does not compute, adopts the ruled node frame and one ayanāṃśa-application convention, validates ayanāṃśa ids against L0's existing map, and is bound by golden-value tests to the served route's computation (the bg_ephemeris_engine surface) that is already instant-grain, MEAN-node and backend-asserting — so the probe that gates the served route's availability certifies the computation callers actually receive."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code re-verified identical at 27b0146f3 (2026-09-24)"
accepted_upstream_contract: "L0 bg_ephemeris / ephemeris_daily (accepted L0 revision f6fed12c7); L0 AYANAMSHA_MAP + _resolve_read_ayanamsha (brahmagyan/l0_ephemeris.py:91-158). NODE FRAME IS NOT AN OPEN QUESTION: L0_REPAIR_EXECUTION_PROMPT_v1_0.md:85-87 item 7 records that ephemeris_daily stores the TRUE node under a contract asserting mean, at a noon-UT epoch, declaring neither, and that both must be declared on the row; item 6 (:77-83) gives the degree-level anchor (TRUE 50.049248°, MEAN 49.033044° at JD 2445735.717361). The remedy in tree is Saṅgam M-1 disposition (b) — 'true L0 knots retained, mean derived at read in the L0 service, the 1.016204° / 3658.3″ mean↔true gap declared per row' (SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md:44, marked [A] author-layer; the mean ruling itself [N]) — with RRV-16 noting the mean convention is not executable inside Saṅgam today (scanner hardcoded TRUE_NODE, frozen, Gochara-owned). BLOCKER: the L0 row declarations (items 6–7, PR #2727, migrations 1075–1079) are NOT in this tree — highest migration here is 1072 — so they are a DEMAND with a named blocker, not an accepted contract"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agents, fresh context; reports at briefs/reviews/REVIEW_KA_GRAHA_SANCARA_v1_0.md (REWORK) and _v1_1.md (ACCEPT_WITH_CORRECTIONS)"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_graha_sancara/engine.py", "platform/python-sidecar/pipeline/orchestrator/writers/ka_graha_sancara.py", "platform/scripts/temporal/compute_transits.py (the engine's live-path delegate: 00:00-UT jd at :73-75,:183; TRUE_NODE :54,:63; FLG_MOSEPH forced :83; retflag discarded :84; constant ephe_mode :217; Ketu speed negated :199 — its other consumers are platform/scripts/temporal/signal_activator.py:46 and its own CLI main())", "platform/python-sidecar/routers/ephemeris.py:12-24 (_ephemeris_backend), :27-73 (_service_context), :136-170 (_calculate_sidereal_positions), :173-197 (natal endpoint, co-user), :210-291 (ephemeris_at_t route) — coordinated: it is the live path and the natal endpoint shares its helpers", "platform/python-sidecar/tests/test_ka_graha_sancara.py, tests/l3/test_m3_graha_sancara_defects.py, tests/l3/test_ephemeris_at_t_sidecar_route.py, tests/test_ephemeris_ayanamsha.py", "platform/python-sidecar/routers/nirmana_probe.py:69,107 and pipeline/orchestrator/service_probes.py:546-548,578-579,618 (probe-contract re-pin, coordinated Pūrṇa packet)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:215-217 (availability contract digest) and :253-260 (the response forward that today DROPS service_context) — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["brahmagyan/l0_ephemeris.py and ephemeris_daily (L0 authority — the :77 comment mislabel is raised as an L0 hygiene note, not edited)", "panchang_engine/swiss_state.py (shared serialization span, DP-SD-010)", "pipeline/transit_search.py (frozen L0 digest closure; Gochara-owned)", "brahmagyan/phala/muhurta.py:737 (L4 caller of PATH-A; compatibility constraint)", "pyjhora_adapter/transits.py (a caller; its own owner)", "services/ka_kota_chakra, ka_moorti_nirnaya, ka_sudarshana_varsha, ka_vedha_gochara (import constants only; their briefs)", "platform-mcp/src/tools/kala_views/**", ".github/workflows/deploy.yml", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the qualified service contract; CONSUMER_INTEGRATED when the golden-value tests bind the served route, the availability probe certifies the served computation, and the route's convention vector survives the TS forward"
target_state_campaign: "ANALYZED (this brief) → OPTIMIZED/JUSTIFIED at stage 3; no t3 event today"
wave: "W2 (service proof)"
shape: single asset, service/probe, global scope
evidence_base: >
  Source read directly on 9feac52d7 [V]; claims re-verified at source by two independent reviewers
  and adopted here are marked [R] (including pure in-process swisseph computations, Moshier, no DB);
  Lane D §4, T1 Frontier row, STATE.md ★ (:219-235), Lane F §2a, blueprint chronicle §11.18 [A]; no
  database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.2 (2026-09-24): v1.1 re-review dispositions (17 findings) — N1 the node frame is NOT an open L0 question: item 7 and Saṅgam disposition (b) already record that the store is TRUE and stays TRUE with mean derived at read and the 1.016204° gap declared; §10.4 becomes a ratification ask, not a question, and nothing waits on 'L0's answer'; N2 a THIRD convention divergence named — PATH-A applies the ayanāṃśa by derive_sidereal (set_sid_mode + get_ayanamsa_ut = mean_get_ayanamsa_ut) while the route and the delegate use FLG_SIDEREAL (apparent_flg_sidereal) — and the mapping corrected (`frame` has no build-side counterpart; `ayanamsa_application` has no served counterpart and must be added); N3 the Delivery row re-specified against the envelope PATH-A actually reaches (EphemerisResult at muhurta.py:737) plus a new row for the route's _service_context, which the TS wrapper drops today (:253-260) — the real delivery defect; N4 Ketu's speed sign differs between route (same signed speed as Rāhu) and engine (negated), which flips applying_or_separating; N5 nakṣatra spellings differ and the route rounds to 4 dp — the tolerance floor; N6 the route labels itself UNQUALIFIED_BACKEND and its two gates named; N7 no Python DEFAULT_AYANAMSHA symbol exists in L0; N8 no blueprint v5.1 yet; N9 the binding enum amendment withdrawn in favour of same-commit retirement; N10 line numbers; N11 2150-12-31 is in range; N12 the shared kernel's module and owner named as an inverted-dependency risk; N13 the two fixed must_not_touch entries; N14 compute_transits' other consumers named; N15 golden-value provenance and tolerance; N16 §4.4/§5 L4 contradiction resolved; N17 'mixed' disposition stated."
  - "1.1 (2026-09-24): v1.0 REWORK dispositions (20 findings) — see §12."
  - "1.0 (2026-09-24): first issue."
---

# `ka_graha_sancara` elevation brief — the position substrate, honestly graded

## §0 — The recommendation, in one paragraph

`ka_graha_sancara` is registered as the layer's position/motion service. What its engine **actually**
computes [R]: on PATH-A, stored tropical `bg_ephemeris` rows at **date** grain with sidereal derived
at read (`engine.py:173-279`); on the "live" path, a delegate (`platform/scripts/temporal/
compute_transits.py`) that discards the time of day and computes at **00:00 UT of the query date**
(`:73-75,:183` [R]; `engine.py:312-313` passes `query_dt` into the birth-instant slot [R]), forces
Moshier (`:83`), discards `retflag` (`:84`), and uses **TRUE node** on both paths (`engine.py:19-20`;
`compute_transits.py:54,63` [R]). The forensic self-test "at 10:43 IST" passes by coincidence of
sign: the Moon at 00:00 UT is 324.4787°, at the birth instant 327.0550°, both Aquarius [R].
Meanwhile the served route `/api/compute/ephemeris_at_t` is the L0 `bg_ephemeris_engine` surface
reused as-is (`routers/ephemeris.py:11-12,43-44,210-212` [R]): true instant, MEAN node (`:82`),
Swiss-file with observed fallback and a per-call backend assertion (`:12-24,:154-156`), a typed
`_service_context` (`:27-73`), HTTP 422 on an unknown id (`:253-260`). And **no L3 writer consumes
the engine's computation** — the four overlay writers import constants only
(`ka_kota_chakra/writer.py:56`, `ka_moorti_nirnaya/writer.py:49`, `ka_sudarshana_varsha/writer.py:34`,
`ka_vedha_gochara/writer.py:60` [R]) and read `ephemeris_daily` themselves; the engine's real callers
are its own self-test, `service_probes.py:618`, `pyjhora_adapter/transits.py:82-86` (no caller found
in scope) and **L4** `brahmagyan/phala/muhurta.py:737` (PATH-A, literal `"lahiri"`) [R]. Yet the
served route's *availability* is gated on the engine's probe (`call_service_wrappers.ts:215-217`,
`max_age_seconds: 900` [R]) — the unqualified implementation certifies the qualified one, and the
same wrapper then **drops the route's `_service_context` on the way out** (`:253-260` forwards only
`datetime_utc, ayanamsha_id, jd, positions, count` [R]), so the convention vector the route computes
per call reaches no caller. Recommendation: **`INTEGRATE` + `QUALIFY_LIMIT` +
`RETIRE_AFTER_MIGRATION` (the 00:00-UT live path)** — the route's computation is the reference for
instants; the engine's live path delegates to it (or to the same shared kernel) with MEAN node;
PATH-A is kept and graded `date_grain`/`noon_ut_knot` for stored-knot reads, with mean derived at
read per the in-tree disposition and the 1.016204° gap declared; ayanāṃśa ids validated against L0's
existing `AYANAMSHA_MAP`; **one ayanāṃśa-application convention** (the two paths differ today);
the route's context vocabulary adopted and carried through the wrapper; the self-test made a detector
for instant precision, node frame and application method; the probe-contract digest re-pinned as a
Pūrṇa packet. Decision for the native: confirm the reference and ratify the node disposition (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:136) | *"Position/motion service. P/I/Q: arbitrary instant/frame provenance; self-test is bounded service proof. DP07."* | unchanged — and "arbitrary instant" is exactly what the engine's live path does not do (§3) |
| Strategy §6.1 **L3-A01** (`:271`) | *"prove exact conventions, time, arbitrary-chart input, provenance and failures; a canonical probe is not full service qualification."* W2 | unchanged |
| W0 field register #7 | `service get_ephemeris → EphemerisResult/GrahaState`, zero DML | `EphemerisResult.source` documents `'mixed'`, never produced (`engine.py:134` [R]) — disposition in §4.13 (N17) |
| Lane D §4 / T1 | DIVERGENT consumer: `call_ephemeris_at_t` → the route with its own swisseph (deliberate) | confirmed and sharpened: the route is the **L0 `bg_ephemeris_engine` surface** (`service_asset_id`, `registry_generation = bg_ephemeris_engine@migration-624`, `:43-44` [R]) |
| STATE.md ★ `:219-235` | two vocabularies; a value test on the engine certifies nothing a caller touches | confirmed; **stronger**: the route's availability is certified by the engine's probe, and the route's own context is dropped by the wrapper (§3) |
| Lane F §2a | `engine.py:302-306` hard `'lahiri'` gate on the live path | `:306-310` [V]; the delegate additionally hard-codes `SIDM_LAHIRI` and `FLG_MOSEPH` (`compute_transits.py:78-79,:83` [R]) |
| Blueprint chronicle §11.18 (G4 was **retracted** at v2.6/v3.5/v4.0 [R]) | the ephemeris backend is process-global and unowned; `panchang_engine/__init__.py:71,149,252,347` `set_ephe_path(None)` [R] | this engine sets no path and asserts no backend [V]; the **route does** |
| **L0 items 6–7** (`L0_REPAIR_EXECUTION_PROMPT_v1_0.md:77-87`) [R] | item 6: replace migration 624's sign-level node anchor with a **degree-level** one (TRUE 50.049248°, MEAN 49.033044° at JD 2445735.717361) — 624 is applied, supersede by a new migration. item 7: *"The table stores the **TRUE** node under a contract asserting mean, at a **noon-UT** epoch, and declares neither. Both must be declared on the row."* | **the store's frame is recorded, not undecided** (N1). The declarations are **not in this tree** — highest migration 1072; no migration adds `node_mode`/`epoch_convention` to `ephemeris_daily` [R] — so this is a DEMAND with a named blocker |
| **Saṅgam M-1 row** (`SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md:44`) [R] | **[A]** disposition (b): *"true L0 knots retained, mean derived at read in the L0 service, the 1.016204° / 3658.3″ mean↔true gap declared per row"*; convention vector `ephemeris_backend`, `epoch_convention`, `ayanamsa_application` (= `apparent_flg_sidereal`); **[S3-E RRV-16]** the mean convention is *not executable inside Saṅgam today* (scanner hardcoded TRUE_NODE, `transit_search.py:10,64`, frozen, Gochara-owned) | the mechanism this brief adopts for PATH-A; author-layer, so §10.4 asks for ratification, not for an answer |
| L0 `brahmagyan/l0_ephemeris.py` [R] | `:77` `{"name": "Rahu", "swe_id": 11}` with a *"Mean North Node"* comment; `:289` `swe.calc_ut(jd, 11, …)` — **11 is `TRUE_NODE`** (`MEAN_NODE=10`, re-verified in-process); `:278` noon UT; `AYANAMSHA_MAP` `:91-119` holds the six legacy keys **and** `lahiri_chitrapaksha`, `true_chitra`, `surya_siddhanta_classical`; `_resolve_read_ayanamsha` `:140-158`; `_DEFAULT_READ_AYANAMSHA='lahiri_chitrapaksha'` `:137` (**private**; there is no public Python `DEFAULT_AYANAMSHA` — N7); the map is `{}` without swisseph (`:118-119`); `derive_sidereal` `:167-172` = `set_sid_mode()` + `get_ayanamsa_ut()` | the resolver the engine should use exists; the comment mislabel is an L0 hygiene note (§10.5) |
| Synergy audit `:59` | *"Kṣetra reads mean via `ephemeris_daily`"* | artifacts disagree with code; item 7 settles it — the store is TRUE; the audit row is corrected by reference, not re-litigated |
| Blueprint v5.0 §3.5 row 1 (`:317`), §16.2 (`:899`), SC-8/SC-10 | "engine import hub for four overlay writers" | **wrong** — constants only; to be corrected in the blueprint's next version (N8; no v5.1 exists today) |
| L3 probe contract | `service_probes.py:578-579` rejects any `forensic_ayanamsha` but `'lahiri'`; digest `nirmana_probe.py:69,107`; `call_service_wrappers.ts:215-217` gates the route on `graha_sancara_forensic` with `probe_contract_sha256`, `max_age_seconds: 900` [R] | moving the probe to the canonical id changes a digest pinned in a Pūrṇa-owned wrapper — coordinated packet (§5) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Identity and registration [V]
`platform/scripts/seed/asset_registry_seed.ts:2230-2245`: `storage_type: 'service'`, no table,
`depends_on: ['bg_ephemeris']`, `scope: 'global'`, `asset_kind: 'service'`. The served route
self-identifies as `service_asset_id: "bg_ephemeris_engine"` (`routers/ephemeris.py:43` [R]) — two
registered identities behind one tool name.

### 2.2 The code [V]/[R]
- **Writer** `writers/ka_graha_sancara.py`: FORENSIC self-test at 1984-02-05 10:43 IST — six checks
  (`:118-248` [R]), raises on unhealthy (`:94` [R]); writes `service_health` + `last_selftest_at`;
  `WriterResult(rows_inserted=0)`. The "exact birth instant" value it checks (`:172`) is the
  **00:00 UT** value.
- **Engine** `services/ka_graha_sancara/engine.py`:
  - `SUPPORTED_AYANAMSHAS = {"lahiri","raman","kp","krishnamurti","yukteshwar","surya_siddhanta"}`
    (`:64`) — a stale hand-copied subset of L0's `AYANAMSHA_MAP` [R]; validated at `:376-379`.
  - **PATH-A** `_read_from_bg_ephemeris` (`:173-279`): stored **tropical** rows at `date` (`:220`),
    `derive_sidereal(trop_lon, jd, ayanamsha)` (`:253`, accepts the canonical id [R]) — i.e.
    **`ayanamsa_application = mean_get_ayanamsa_ut`** (`l0_ephemeris.py:167-172`, N2); returns `None`
    on any failure (`:228,:248,:256` [R]) → falls to the live path (`:425-427`) → for a non-lahiri
    *in-range* request that surfaces as `NotImplementedError` (`:306`) — a read failure wearing a
    vocabulary error. `is_retrograde` for nodes forced `False` (`:263`) [R].
  - **Live path** `_compute_live` (`:284-339`): `if ayanamsha != "lahiri": raise NotImplementedError`
    (`:306-310`); `get_transit_states(query_dt, q_date, ayanamsha=…)` (`:313`) →
    `compute_transits.py:158-161` whose first positional is `birth_dt`; positions at
    `jd = _sidereal_jd_ut(query_date)` = `swe.julday(y, m, d, 0.0)` (`:73-75,:183`) — **00:00 UT of
    the date, time-of-day discarded**; `SIDM_LAHIRI` + **`FLG_SIDEREAL`** hard-coded (`:78-79`) —
    i.e. **`ayanamsa_application = apparent_flg_sidereal`**, the *other* convention (N2);
    `FLG_MOSEPH` forced (`:83`); `pos, _ = swe.calc_ut(...)` discards `retflag` (`:84`);
    `"ephe_mode": "moshier"` constant (`:217`); `swe.TRUE_NODE` (`:54,:63`); nodes `is_retrograde`
    forced `False` (`:190,:197-200`); **Ketu's speed negated** (`:199`) [R].
  - TRUE node on PATH-A too (`engine.py:19-20`; L0 stores `swe_id 11`) [R].
  - Cache keyed `(date_str, ayanamsha)` (`:143-168`; key `:151-152`) — with a caller-supplied
    `_cache` (`:396-407`) any later instant on the same date returns the first instant's grahas [R].
  - Naive datetimes assumed **Asia/Kolkata** (`:381-391`); `q_date = dt.date()` in that zone (`:393`)
    selects the PATH-A knot [R] — a global-scope service with a native-specific default.
  - `NAKSHATRAS` spelled `"Mula"`, `"PurvaPhalguni"` (`:43-51`) — the tuple the four overlay writers
    import; the route spells `'Moola'`, `'Purva Phalguni'` (`routers/ephemeris.py:90-96`) (N5).
  - `GrahaState.applying_or_separating(target_lon_deg)` (`:84-126`) branches on `speed_dps` sign —
    so Ketu's sign convention is load-bearing (N4).
  - `EphemerisResult.source` documents `'mixed'`; never produced (`:134`).
- **Served route** `routers/ephemeris.py`: `_ephemeris_backend(retflag)` (`:12-24`), per-body
  `retflag` (`:154-156`), `_service_context` (`:27-73`) emitting `node_mode` (`:49` `"mean"`),
  `frame` (`:47` `"geocentric_sidereal"`), `ayanamsha_id`, `input_precision`,
  **`ephemeris_backends_observed`** ∈ `{jpl_file, swiss_ephemeris_file, moshier_analytic_fallback}`,
  `backend_observation_state`, **`backend_qualification_state: "UNQUALIFIED_BACKEND"`** with
  `qualification_requires: VERIFIED_REGISTRY_PROBE_RECEIPT` and detector `_probe_ephemeris_engine`
  (`:54-58,:69-70`) [R], `failure_contract` (`unknown_ayanamsha: "HTTP_422"`, `:66`);
  `('Rahu', swe.MEAN_NODE)` (`:82`); **`FLG_SWIEPH | FLG_SIDEREAL | FLG_SPEED`** (`:147`) — the
  *apparent* application; **Ketu takes Rāhu's own signed speed** (`:163-168`) [R]; retrograde =
  `speed < 0` (`:128-131`); longitudes rounded to 4 dp, speeds to 6 dp (`:126,:131`) — the golden
  fixture's tolerance floor (N5); canonical-id → `SIDM_*` map (`:226-232`), default (`:233`), note on
  the two Lahiri names (`:223-225`); route decorator `:241`, body `:242-291`; naive datetime rejected
  (`:267-271`); shared helper `_calculate_sidereal_positions` (`:136-170`) also used by the natal
  endpoint (`:173-197`) [R]. The engine is not imported (`:200,:244` comment only [V]).
- **TS wrapper** `call_service_wrappers.ts:170-262`: default `DEFAULT_AYANAMSHA` (`:227`);
  `PYTHON_SIDECAR_URL` guard (`:235-240`); availability contract gated on the **engine's** probe
  (`:215-217`); **the response forward at `:253-260` carries only `datetime_utc, ayanamsha_id, jd,
  positions, count` — `service_context` is dropped** [R] (N3).

### 2.3 Consumers (boundary: sidecar `services/`, `routers/`, `pipeline/`, `brahmagyan/`, `pyjhora_adapter/`, `platform/scripts/`; `platform-mcp/src`; `platform/src/lib/retrieval`; tests excluded) [R]
| consumer | reads | role |
|---|---|---|
| the four overlay writers (`ka_kota_chakra/writer.py:56`, `ka_moorti_nirnaya/writer.py:49`, `ka_sudarshana_varsha/writer.py:34`, `ka_vedha_gochara/writer.py:60`) | **constants only** (`NAKSHATRAS`, `SIGNS`, `NAK_SIZE_DEG`); positions come from their own SQL on `ephemeris_daily` (`kota :96`, `moorti :77`, `vedha :106`) | vocabulary |
| `writers/ka_graha_sancara.py:120,176,232`; `service_probes.py:618` | `get_ephemeris` (self-test / probe) | probe |
| `pyjhora_adapter/transits.py:82-86` | `get_ephemeris(force_live=True)` — *"precise live computation"* | `computation`; **no caller of this adapter found within scope** |
| `brahmagyan/phala/muhurta.py:737` (**L4**) | PATH-A, literal `"lahiri"` | `computation` (cross-layer) |
| **`compute_transits.py`'s other consumers** (N14) | `platform/scripts/temporal/signal_activator.py:46` (`get_transit_states, parse_iso8601, SIGNS`) and its own CLI `main()` | must be traced before the delegate retires |
| the served route | **its own computation** (the L0 surface) | the divergence |
| `pipeline/transit_search.py`, `panchang_engine`, `w2g`, Saṅgam scanner | their own swisseph integrations (SC-8) | siblings |

**Live-path statement.** The engine's computation is live for **no L3 writer**; it is live for the
pyjhora adapter (no caller found in scope — not asserted unused) and for L4 muhūrta (PATH-A). The
served route is live on the L0 surface. The engine's probe gates the served route's availability —
live. The route's own convention vector reaches no caller — the wrapper drops it.

### 2.4 Epistemic class of the important quantities
| quantity | class | authority | note |
|---|---|---|---|
| tropical longitude/speed at a knot | `COMPUTED_FACT_CONFIGURATION` | L0 `ephemeris_daily` (noon UT `:278`; `swe_id 11` TRUE node `:77,:289`) | PATH-A: `time_basis='noon_ut_knot'`, `claim_grain='date_grain'` |
| sidereal longitude (PATH-A) | computed fact | `derive_sidereal` under a named ayanāṃśa | `ayanamsa_application='mean_get_ayanamsa_ut'` (N2) |
| "live" positions | computed fact **at 00:00 UT of the date** | `compute_transits.py` (Moshier forced, TRUE node, `FLG_SIDEREAL`) | not an instant; `ayanamsa_application='apparent_flg_sidereal'` — the *other* convention |
| route positions | computed fact at the instant | L0 `bg_ephemeris_engine` surface; MEAN node; `apparent_flg_sidereal`; backend observed per call | the qualified-by-receipt computation (N6) |
| Rāhu/Ketu node frame | convention | store: TRUE (item 7); route: MEAN; engine: TRUE both paths | the ruled target is mean, derived at read (disposition (b)); gap 1.016204° declared |
| `is_retrograde` (nodes); Ketu `speed_dps` | convention | engine: flag forced `False`, **speed negated** (`compute_transits.py:199`); route: `speed < 0`, **Ketu carries Rāhu's signed speed** (`:163-168`) | `applying_or_separating` branches on the sign — a silent verdict flip after delegation (N4) |
| `service_health` | status | six checks at one instant, on the 00:00-UT value | cannot detect the instant defect, the node frame or the application method — §N.8 |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; the W2 service-payload freeze at `47131772b` is **unverified** (that commit's stat
does not name this asset [R]). t3: no event. Cost: unmeasured.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Ask the **registered engine** for positions at 1984-02-05 05:13 UT (the birth instant) on its live path: it returns the Moon at 324.4787° (00:00 UT), not 327.0550° (05:13 UT) — 2.58° off, TRUE node, Moshier, `ephe_mode` constant — and its self-test calls that value "the exact birth instant" (`writers/ka_graha_sancara.py:172`; `service_probes.py:546-548`; `tests/l3/test_m3_graha_sancara_defects.py:71-74` [R]). Ask the **served route** the same: it returns the instant, MEAN node (1.0213° from TRUE at that instant [R]), under a *different* ayanāṃśa-application convention from PATH-A, with `ephemeris_backends_observed` asserted — and the TS wrapper then drops that whole context (`:253-260`). Two answers, three convention elements, and the served route's availability is certified by the probe of the one that is wrong |
| Evidence | `compute_transits.py:73-75,:183,:54,:63,:78-79,:83,:84,:199,:217`; `engine.py:19-20,:253,:306-310,:312-313,:64`; `routers/ephemeris.py:47,:49,:82,:147,:163-168,:12-24,:154-156`; `call_service_wrappers.ts:215-217,:253-260` — all [R]; reviewer's swisseph run (Moshier): Moon 324.4787° / 327.0550° / 330.4060° (00:00 UT / 05:13 UT / 12:00 UT knot); true−mean 1.0213° |
| Expected contract | L3-A01 (*exact conventions, time, arbitrary-chart input, provenance, failures*); D6 (mean node) = Kṣetra 7 = Gochara N-4a = Saṅgam M-1; DP01 (no rival definitions); DP03 (pinned context); Foundation F28 (a status names the path that can turn it false); binding B1 (`time_basis`), B6 (node = mean) |
| Defect class | **wrong authority** (the unqualified implementation's probe certifies the qualified route) + **detector mismatch** (`service_health` cannot see the instant, frame or application defect) + **wrong context** (frame, epoch and ayanāṃśa-application differ between the two) + **dropped provenance** (the route computes a convention vector the wrapper discards) + **stale vocabulary** |
| Impact | Q09 substrate: a convention-sensitivity answer built on the engine would compare against the wrong frame and the wrong application; any consumer that trusts `force_live` (the pyjhora adapter) gets a midnight value; L4 muhūrta reads PATH-A under a legacy id; the served route can go dark on a probe that measures the other implementation; no caller can see which backend actually answered |
| Non-claim | The reviewer's figures are Moshier; Swiss-file values differ at arc-second level, not the degree level these findings rest on; whether the pyjhora adapter has a live caller is unresolved; the physical node frame in `ephemeris_daily` is taken from L0 item 7's own record, not queried |

---

## §4 — The semantic delta (contract §4) — smallest sufficient change

1. **L3-Q served.** Substrate for Q01/Q03; directly Q09 (convention sensitivity — five ayanāṃśas at
   one instant; `comparable_with='different_convention'` between them). No window question.
2. **Grading before repair (B1).** PATH-A: `time_basis='noon_ut_knot'`, `claim_grain='date_grain'`.
   The engine's current live path is a 00:00-UT knot — not in the B1 enum. **The v1.1 amendment ask
   is withdrawn (N9):** the delegate is retired in the same commit that lands the delegation, so no
   generation is served under a new enum value; if the native prefers a rollback flag, the flagged
   path is `completeness_state='unqualified'` with `time_basis` null and reason
   `midnight_ut_knot_legacy`, never a new enum member.
3. **The reference is the route's computation.** The `bg_ephemeris_engine` surface (true instant,
   MEAN node, Swiss with observed fallback, `SWISS_STATE_LOCK`-serialised) is the reference for
   instants. The engine's live path **delegates to it**, or both call one shared kernel extracted
   from `_calculate_sidereal_positions` (`:136-170`). **Kernel placement is a real decision (N12):**
   that helper is L0-identified (`service_asset_id: bg_ephemeris_engine`) but lives in a FastAPI
   router module, and `brahmagyan/` is `must_not_touch` — so delegating means `services/` (and
   transitively L4 `muhurta.py`) importing from `routers/`, an inverted dependency. §10.6 asks where
   the kernel lives and who owns it; if L0's, it is a DEMAND like items 6–7. The engine consumes only
   `(lon, speed, retflag)` from the kernel and keeps its own decomposition, so the `NAKSHATRAS`
   spellings the four overlay writers import do not change (N5).
4. **Node frame — a computation delta with a recorded disposition (N1).** TRUE → MEAN on the engine's
   instant path via item 3. PATH-A follows **disposition (b)**: the true knots stay stored, mean is
   derived at read in the L0 service, and the 1.016204° / 3658.3″ gap is declared per row. Until that
   derivation exists in code, PATH-A asserts `node_convention='true'` honestly (§N.7 items 3/6) —
   this is a *build order*, not a question awaiting an answer. Ripple: the four overlay writers are
   unaffected (constants only); `pyjhora_adapter/transits.py` and L4 `brahmagyan/phala/muhurta.py:737`
   are the consumers whose Rāhu/Ketu values move **once PATH-A's read-time mean derivation lands**
   (N16 — §5 says the same, not the opposite).
5. **Ketu's speed sign and node retrograde convention (N4).** One convention across both paths,
   declared on the row: the route's (Ketu carries the node's signed speed) or the engine's (negated).
   `applying_or_separating` is pinned by a golden test under the chosen convention, because its
   branch is the sign.
6. **One ayanāṃśa application (N2).** PATH-A uses `mean_get_ayanamsa_ut`; the route and the delegate
   use `apparent_flg_sidereal`. Saṅgam's declared vector fixes `ayanamsa_application =
   apparent_flg_sidereal`; this brief therefore **adds `ayanamsa_application` to the route's
   `_service_context`** (in `may_touch`) and declares PATH-A's value as the other member of the enum,
   with the difference stated per row rather than absorbed at date-grain tolerance.
7. **Convention vector — adopt the route's existing names, with a corrected mapping (N2).**
   `ephemeris_backends_observed`, `backend_observation_state`, `backend_qualification_state`,
   `node_mode`, `frame`, `ayanamsha_id`, `input_precision`, `failure_contract` are the L0
   probe-contract vocabulary (`nirmana_probe_contracts.json`; `service_probes.py:292,342-347` [R]);
   the engine emits the same names. Mapping to Saṅgam's build-side spellings:
   `node_mode ↔ node_convention`; `ephemeris_backends_observed ↔ ephemeris_backend` (set ↔ scalar —
   declared); `epoch_convention` ↔ the route's `input_precision`/`instant_utc` statement;
   **`ayanamsa_application` exists build-side and must be ADDED served-side (item 6); `frame`
   (`"geocentric_sidereal"`) has no build-side counterpart and is not a mapping of
   `ayanamsa_application`** — the v1.1 mapping row was wrong. SC-8's packet fixes one spelling in the
   binding; until then both sides declare the mapping.
8. **Vocabulary (SC-10).** `SUPPORTED_AYANAMSHAS` is replaced by validation against L0's
   `AYANAMSHA_MAP` (import, no L0 edit). **There is no public Python `DEFAULT_AYANAMSHA` (N7):** L0's
   are private (`_DEFAULT_AYANAMSHA = "lahiri"` `:121`, `_DEFAULT_READ_AYANAMSHA =
   "lahiri_chitrapaksha"` `:137`), and the two importable sidecar symbols of that name
   (`pyjhora_adapter/_ayanamsha.py:42`, `panchang_engine/ayanamsha.py:15`) are both the **legacy**
   `'lahiri'`; the canonical default lives in TS (`constants.ts:2`). The engine therefore resolves
   through `_resolve_read_ayanamsha` (`:140-158`) and, if a public alias is wanted, it is an L0 DEMAND
   (L0 is `must_not_touch`). Unknown → the engine's typed `ValueError` (`:376-379`, already right);
   **the route keeps HTTP 422** — an unknown token is a caller error, not F06 `unavailable`, which is
   reserved for out-of-range and PATH-A read failures (`reason='path_a_read_failed'`).
9. **Naive datetimes.** Rejected, as the route does (`:267-271`); the Asia/Kolkata default
   (`:381-391`) is removed — tz from the caller or the chart, never a native-specific constant.
10. **Cache.** Keyed on the instant when computing at an instant; PATH-A's date key kept and labelled
    `QUALIFY_LIMIT`.
11. **Self-test as a detector.** The writer adds: a non-midnight instant checked against the reference
    (fails on today's code by 2.58° on the Moon); node frame checked against the declared convention
    (fails on today's TRUE where mean is asserted); `ayanamsa_application` checked; the canonical id
    accepted; backend observed. Then `service_health` has real ways to read `unhealthy`; the probe
    contract's `forensic_ayanamsha` allowlist (`service_probes.py:578-579`) and digest
    (`nirmana_probe.py:69,107`, `call_service_wrappers.ts:215-217`) are re-pinned in a **coordinated
    Pūrṇa packet**.
12. **The dropped context (N3) — a second interface packet.** `call_service_wrappers.ts:253-260`
    forwards five fields and discards `service_context`; the packet adds it to the forward so a
    caller can see `node_mode`, `ayanamsa_application`, `ephemeris_backends_observed` and
    `backend_qualification_state`. Pūrṇa owns the TS; L3 owns the sentinel.
13. **`'mixed'` (N17).** `EphemerisResult.source` documents a value nothing produces; it is **struck**
    from the docstring and the type in the same commit (an honest null beats a documented ghost).
14. **Old vs new.** Positive: 05:13 UT via the engine → 327.06°, MEAN Rāhu, `ayanamsa_application`
    declared, backend observed. Negative: `'kp'` → typed `ValueError` in the engine / HTTP 422 at the
    route. Boundary: **2151-01-01 00:00 UTC** → PATH-A `unavailable(out_of_range)` (the range ends
    `<= 2150-12-31`, `engine.py:58,:416`, so 2150-12-31 23:59 is **in** range — N11); the instant path
    answers. Missing: `.se1` absent → `moshier_analytic_fallback` observed, never silent. Duplicated:
    the same instant via PATH-A and the instant path → `time_basis` and `ayanamsa_application` differ,
    longitudes within the date-grain tolerance, Rāhu differs by ~1° until PATH-A's read-time mean
    derivation lands (declared).
15. **Simpler baseline.** The route as it is today (already instrumented) and the engine as it is.
16. **Ablation (N15).** A **golden-value fixture at the served envelope**: mutate the reference kernel
    (e.g. one `SIDM_*` entry, or `MEAN_NODE → TRUE_NODE`) → the golden values fail. Provenance: the
    values are **kernel-pinned**, so the fixture detects mutation and regression, not astronomical
    truth (§N.4: no JH-parity oracle); the one independent ground is the FORENSIC instant. Tolerance
    ≥ the route's own rounding floor, 0.5e-4° (`:126`). Parity engine ↔ route is a
    **transition-commit** test only; after delegation there is one computation and the golden fixture
    is the detector.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: PATH-A (stored knots + sidereal derivation), the memo cache (labelled),
  `applying_or_separating` (pinned under the chosen sign convention), the route's `_service_context`
  and 422 contract, the forensic anchor (re-based on the true instant), the engine's own `NAKSHATRAS`
  spellings (the overlay writers' vocabulary).
- `QUALIFY_LIMIT`: PATH-A `date_grain`/`noon_ut_knot`; PATH-A `node_convention='true'` until the
  read-time mean derivation lands; PATH-A `ayanamsa_application='mean_get_ayanamsa_ut'`; the
  date-keyed cache.
- `INTEGRATE`: one vocabulary (L0's map), one reference computation, one ayanāṃśa application,
  golden-value tests, the `_service_context` forward.
- `RETIRE_AFTER_MIGRATION`: the 00:00-UT live delegate (`compute_transits.py` for this caller) —
  **its other consumers are `signal_activator.py:46` and its own CLI (N14)**, both traced before
  retirement; and `EphemerisResult.source = 'mixed'`.
- **Consumers whose values move**: `pyjhora_adapter/transits.py` (no caller found in scope) and L4
  `brahmagyan/phala/muhurta.py:737` — the latter reads PATH-A, so it moves **when PATH-A's read-time
  mean derivation lands (item 4)**, not at delegation (N16). The four overlay writers: unaffected.
- **Coordinated Pūrṇa packets**: (i) probe-contract digest re-pin
  (`call_service_wrappers.ts:215-217`); (ii) the `service_context` forward (`:253-260`). The natal
  endpoint (`routers/ephemeris.py:173-197`) shares the helpers — its tests run.
- **DEMAND with blocker**: L0 items 6–7 (row declarations) are not in this tree; the engine asserts
  its vector from its own constants meanwhile (noon UT `l0_ephemeris.py:278`; node per item 4).
- **SC-8 boundary**: this brief asserts the vector *in this engine, its delegate and the route*; it
  does not set the process path and does not touch `panchang_engine`, `transit_search.py`, `w2g`.
- No table, no migration, no rows; rollback = the engine's delegation is one flag (and under item 2
  that flagged path is `unqualified`, not a new enum value); PATH-A untouched.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_graha_sancara`, L3 service, global; epistemic: astronomical computation; two registered identities behind one tool (`bg_ephemeris_engine` at the route); `INTEGRATE + QUALIFY_LIMIT + RETIRE_AFTER_MIGRATION` |
| B | `bg_ephemeris` declared and real (PATH-A); the delegate script is an undeclared code dependency (now in `may_touch`, with its own consumers named); no hidden table; fan-out: constants ×4, adapter, L4, the probe → route availability |
| C | invariants: instant path = reference within tolerance; `node_convention` = the declared convention; `ayanamsa_application` one value per path, declared; sidereal = tropical − ayanāṃśa(jd) under the declared method; Ketu's speed sign and nodes' `is_retrograde` convention stated and pinned; golden values at the served envelope. Detectors: the re-based self-test, the golden fixture |
| D | n/a (service) |
| E | real callers per §2.3; the served route is the qualified sibling; the engine's probe gates it; the wrapper drops its context |
| F | every response carries the route's context vocabulary **and it survives the wrapper**; unknown id typed |
| G | no hotspot measured; **justified no-change** |
| H | idempotent; no writes; the route's `SWISS_STATE_LOCK` preserved |
| I | files in `may_touch`; W2; two coordinated Pūrṇa packets; consumer trace of `compute_transits.py` done (N14); kernel placement decided at §10.6 |
| J | this brief; §7; three reports; the golden fixture output |

---

## §7 — Proof matrix

| proof | fixture | expected | invariant | detector fails when… |
|---|---|---|---|---|
| Positive | 1984-02-05 05:13 UT, canonical id, engine instant path | Moon 327.06° ± tol; Rāhu MEAN; `ayanamsa_application` and `ephemeris_backends_observed` asserted | instant, not midnight | 324.48° (today's value); application absent |
| Negative | `'kp'` at the engine / at the route | typed `ValueError` / HTTP 422 | route contract kept | 200-and-`unavailable` |
| Relevant influence | `lahiri_chitrapaksha → raman` | Δ = Δayanāṃśa under the declared application; `node_mode` unchanged | Δayanāṃśa | Δ ≠ Δayanāṃśa |
| Irrelevant control | `'lahiri'` alias vs canonical via L0's map | identical longitudes | alias-invariant | differ |
| Convention control | Ketu's `speed_dps` sign and nodes' `is_retrograde` on both paths | one declared convention; `applying_or_separating` verdict pinned | declared | the verdict flips after delegation |
| Duplication | same instant PATH-A vs instant path | `time_basis` **and** `ayanamsa_application` differ; longitudes within date-grain tolerance; Rāhu differs by ~1.0162° until PATH-A's mean derivation lands (declared) | labelled | labels equal; the gap undeclared |
| Context | `.se1` absent | `moshier_analytic_fallback` in `ephemeris_backends_observed` | observed | missing |
| Boundary | 1900-01-01 00:00; **2150-12-31 23:59 (in range)**; **2151-01-01 00:00 (out)**; 0°/360° seam | instant path answers; PATH-A `unavailable(out_of_range)` only past 2150-12-31 | seam-safe; range per `engine.py:58,:416` | mishandled; 2150-12-31 refused |
| Delivery (PATH-A) | sentinel `claim_grain='date_grain'` on a PATH-A answer | reaches the envelope PATH-A actually reaches — `EphemerisResult`, observed at its L4 consumer (`muhurta.py:737`) | survives in-process | absent |
| Delivery (route) | the route's `_service_context` on a live call | survives the TS forward (`call_service_wrappers.ts:253-260`) to the capability's `content` | context not dropped | absent (today's behaviour) |
| Revision | L0 `ephemeris_daily` regenerated | PATH-A changes; instant path unchanged | no cache | stale |
| Value | mutate the reference kernel (`MEAN_NODE → TRUE_NODE`; one `SIDM_*`) | golden values at the served envelope fail; tolerance ≥ 0.5e-4° (the route's rounding floor); provenance = kernel-pinned, FORENSIC instant the one independent ground | detector | passes under mutation |
| Transition | engine ↔ route parity at N instants incl. the forensic instant, a station, the seam | agree within tol before delegation | one computation after | disagree |
| Evaluation | n/a (no claim issued) | — | — | — |

Binding: **OFFERS** B1 (`time_basis`, `claim_grain`), B2 (`epistemic_class='COMPUTED_FACT_
CONFIGURATION'`, `completeness_state`, `operator_role='computation'`, `comparable_with=
'different_convention'` across ayanāṃśas), the SC-8 vector under the route's names with the corrected
mapping to the binding's build-side names. **DEMANDS** L0 items 6–7 (blocker: not in tree) and, if a
public default symbol is wanted, an L0 alias. `tier_basis`, `independence_group`: n/a (no score, no
testimony) — stated. **Asset-local:** `ayanamsa_application` (until SC-8 fixes one spelling),
`path` (`A`/`instant`), `n_subdivisions` n/a here.

---

## §8 — Prioritization

(1) grade honestly (labels true today: `date_grain`, `node_convention='true'`,
`ayanamsa_application` per path; a self-test that can fail) → (2) vocabulary via L0's map (SC-10) →
(3) delegate the instant path to the reference and retire the midnight delegate in the same commit
(the real repair) → (4) one ayanāṃśa application + Ketu's sign convention → (5) PATH-A's read-time
mean derivation per disposition (b) → (6) the two Pūrṇa packets (digest re-pin; context forward).
T0, W2; no P-candidate; it unblocks the *honesty* of the served route's availability signal.

---

## §9 — Disposition and target state

`INTEGRATE` + `QUALIFY_LIMIT` + `RETIRE_AFTER_MIGRATION`. Data-plane: `PRODUCER_READY` after §7;
`CONSUMER_INTEGRATED` when the served route's availability probe certifies the served computation,
the golden fixture is on `main`, and the context survives the wrapper. Campaign: `ANALYZED` →
`OPTIMIZED/JUSTIFIED`. Non-claims: no `DATA_ACCEPTED`; no `VALUE_EVALUATED` (this asset's value is the
absence of a wrong frame, a wrong application or a midnight value under an instant label, shown by
detectors, not by a reading delta); the store's physical node frame is L0 item 7's record, not a
query.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Reference computation for instants: the served route's `bg_ephemeris_engine` surface (or a shared kernel extracted from it); the engine's 00:00-UT delegate retired in the same commit** | **yes** |
| 2 | Adopt L0's `AYANAMSHA_MAP` as the one vocabulary; resolve through `_resolve_read_ayanamsha` (no public Python default symbol exists) | yes (SC-10) |
| 3 | Node frame TRUE → MEAN on the engine's instant path via delegation; PATH-A follows disposition (b) — mean derived at read, 1.016204° gap declared | yes; ripple named (adapter, L4 muhūrta, at PATH-A's derivation) |
| 4 | **Ratify Saṅgam M-1 disposition (b) as the layer-wide node mechanism** — it is currently marked `[A]` author-layer, and RRV-16 records it is not executable inside Saṅgam today | ratify, with the Gochara-owned scanner's exemption stated |
| 5 | **L0 hygiene note:** `l0_ephemeris.py:77` computes `swe_id 11` (TRUE) under a "Mean North Node" comment; item 7 already records the substance | route the one-line comment fix to L0's owner; no decision needed |
| 6 | **Where does the shared kernel live, and who owns it?** Today it is an L0-identified helper inside a FastAPI router; delegating creates a `services/ → routers/` dependency | name a module and owner; if L0's, add it to items 6–7 as a DEMAND |
| 7 | One ayanāṃśa application across both paths (`apparent_flg_sidereal` per Saṅgam's vector) and one Ketu-speed/node-retrograde convention | yes |
| 8 | Tolerance for the golden fixture | ≥ 0.5e-4° (the route's rounding floor); set precisely from measurement at stage 3 |

---

## §11 — Not verified here

1. Production state (`service_health`, `.se1` on the host, live incidence, PR #2727 / migrations
   1075–1079 applied) — no DB, no network.
2. Whether `pyjhora_adapter.transits.compute_transits` has a live caller — none found in sidecar
   non-test scope; not asserted unused.
3. "Service payload frozen at `47131772b`" — unverified (that commit's stat does not name this asset).
4. Which node `ephemeris_daily` physically stores — taken from L0 item 7's own record and
   `l0_ephemeris.py:77,289`, not queried.
5. Per-call latency.
6. The reviewers' swisseph figures are Moshier (no `.se1` on those hosts); Swiss-file values differ at
   arc-second level.
7. Whether Saṅgam disposition (b) has been ratified by the native — it is marked `[A]` author-layer;
   §10.4 asks.

## §12 — Review dispositions

**v1.0 → v1.1 (20 findings, all accepted).** F1 (§0, §2.2, §2.4, §3, §4, `may_touch`); F2 (§4.4, §7,
§10); F3 (goal, §0, §2.3, §5); F4 (§4.7); F5 (`may_touch`, §4.3); F6 — §10.1 flipped; F7
(frontmatter, §1, §5); F8 (§4.8, §7 negative); F9 (§4.16, §7 value/transition); F10 (§4.8); F11
(§4.10, §5); F12 (§2.2, §4.9); F13 (§2.4, §7 convention control); F14 (ranges, paths, `may_touch`);
F15 (§1); F16 (removed); F17 (§0, §2.3); F18 (§1, §4.11, §5); F19 (§2.2, §4.8); F20 (§2.1, §1).

**v1.1 → v1.2 (17 findings, all accepted).** N1 (frontmatter `accepted_upstream_contract`, §1 two new
rows, §4.4, §5, §10.3–5 — the node frame is a recorded disposition, not an open question); N2 (§2.2,
§2.4, §3, §4.6, §4.7 corrected mapping, §7 duplication); N3 (§0, §2.2, §2.3, §4.12, §7 two Delivery
rows, §5 second packet); N4 (§2.2, §2.4, §4.5, §7 convention control); N5 (§2.2, §4.3, §4.16); N6
(§2.2, §2.4 "qualified-by-receipt"); N7 (§4.8); N8 (§1); N9 (§4.2 — amendment withdrawn); N10 (line
numbers throughout); N11 (§4.14, §7 boundary); N12 (§4.3, §10.6); N13 (`must_not_touch`); N14 (§2.3,
§5); N15 (§4.16, §7 value); N16 (§4.4 and §5 now agree); N17 (§4.13).
