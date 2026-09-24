---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_GRAHA_SANCARA_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_GRAHA_SANCARA_v1_0.md, 20 findings); v1.1 dispositions each; → PROPOSED_FOR_NATIVE_RULING on re-verification
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows in §7; one enum amendment proposed (§4 item 2)
asset_or_interface_ids: ["ka_graha_sancara", "SC-8 (convention vector — the node-frame computation delta and the field-name mapping)", "SC-10 (ayanāṃśa vocabulary via L0's AYANAMSHA_MAP)", "L0 question: l0_ephemeris.py:77 'Mean North Node' comment over swe_id 11 (TRUE_NODE)"]
goal_objective: "Make ka_graha_sancara one honest position service: its registered engine stops claiming instant precision it does not compute, stops carrying a TRUE-node frame after the mean ruling, validates ayanāṃśa ids against L0's existing map, and is bound by golden-value tests to the served route's computation (the bg_ephemeris_engine surface) that is already instant-grain, MEAN-node and backend-asserting — so the probe that gates the served route's availability certifies the computation callers actually receive."
source_revision: "9feac52d7 (l3/kala-layer-briefs; the five cited code files byte-identical to HEAD 4d8c6aa9b)"
accepted_upstream_contract: "L0 bg_ephemeris / ephemeris_daily (accepted L0 revision f6fed12c7); L0 AYANAMSHA_MAP + _resolve_read_ayanamsha (brahmagyan/l0_ephemeris.py:91-156); BLOCKER: the node-frame/epoch row declarations (L0 items 6–7, PR #2727, migrations 1075–1079) are NOT in this tree — highest migration here is 1072 — their 'applied to production' status is the L0 repair session's claim and is a DEMAND with a named blocker, not an accepted contract"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; v1.0 report at briefs/reviews/REVIEW_KA_GRAHA_SANCARA_v1_0.md; re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_graha_sancara/engine.py", "platform/python-sidecar/pipeline/orchestrator/writers/ka_graha_sancara.py", "platform/scripts/temporal/compute_transits.py (the engine's live-path delegate: 00:00-UT jd at :77-79,:183; TRUE_NODE :54,:63; FLG_MOSEPH forced :83; retflag discarded :84; constant ephe_mode :216 — its other consumers traced at stage 3)", "platform/python-sidecar/routers/ephemeris.py:27-73 (_service_context), :140-173 (_calculate_sidereal_positions), :176-197 (natal endpoint, co-user), :200-291 (ephemeris_at_t route) — coordinated, it is the live path and the natal endpoint shares its helpers", "platform/python-sidecar/tests/test_ka_graha_sancara.py, tests/l3/test_m3_graha_sancara_defects.py, tests/l3/test_ephemeris_at_t_sidecar_route.py, tests/test_ephemeris_ayanamsha.py", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:170-262 (probe-contract digest re-pin), platform/python-sidecar/routers/nirmana_probe.py:69,107, pipeline/orchestrator/service_probes.py:546-548,582-583,618"]
must_not_touch: ["brahmagyan/l0_ephemeris.py and ephemeris_daily (L0 authority — the :77 comment mislabel is raised, not edited)", "panchang_engine/swiss_state.py (shared serialization span, DP-SD-010)", "pipeline/transit_search.py (frozen L0 digest closure)", "brahmagyan/phala/muhurta.py:737 (L4 caller of PATH-A; compatibility constraint)", "pyjhora_adapter/transits.py (a caller; its own owner)", "services/ka_kota_chakra, ka_moorti_nirnaya, ka_sudarshana_varsha, ka_vedha_gochara (import constants only; their briefs)", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the qualified service contract; CONSUMER_INTEGRATED when the golden-value tests bind the served route and the availability probe certifies the served computation"
target_state_campaign: "ANALYZED (this brief) → OPTIMIZED/JUSTIFIED at stage 3; no t3 event today"
wave: "W2 (service proof)"
shape: single asset, service/probe, global scope
evidence_base: >
  Source read directly on 9feac52d7 [V]; claims re-verified at source by the independent reviewer
  and adopted here are marked [R] with the reviewer's file:line (including one pure in-process
  swisseph computation the reviewer ran, Moshier, no DB); Lane D §4, T1 Frontier row, STATE.md ★
  (:219-235), Lane F §2a, blueprint chronicle §11.18 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions — F1 the engine's live path computes at 00:00 UT of the query date (not the instant): both engine paths are date-grain, the forensic anchor passes by coincidence of sign, may_touch gains compute_transits.py; F2 both engine paths are TRUE-node while the route is MEAN — stated as a computation delta with ripple, node_convention='true' asserted until changed; F3 the four overlay writers import constants only — real callers listed; F4 the route already asserts backend per call under the L0 probe vocabulary — adopted, no rival names; F5 retflag discarded in compute_transits.py; F6 the reference is the route's bg_ephemeris_engine computation, not the engine's live path — §10.1 flipped; F7 migrations 1075–1079 absent from this tree — DEMAND with blocker; F8 HTTP 422 at the route preserved; F9 Value row re-specified as a golden-value mutation at the served envelope; F10 L0's AYANAMSHA_MAP is the resolver; F11 cache date-keyed → QUALIFY_LIMIT; F12 naive-datetime Asia/Kolkata default named; F13 is_retrograde on nodes in the parity contract; F14 ranges/paths fixed; F15 §11.18 cited, G4 retracted noted; F16 estimated_seconds removed; F17 §0/§2.3 made consistent; F18 the availability contract gated on the engine probe cited; F19/F20 typed PATH-A failure, service_asset_id, 'mixed' dropped."
  - "1.0 (2026-09-24): first issue."
---

# `ka_graha_sancara` elevation brief — the position substrate, honestly graded

## §0 — The recommendation, in one paragraph

`ka_graha_sancara` is registered as the layer's position/motion service. What its engine
**actually** computes [R]: on PATH-A, stored tropical `bg_ephemeris` rows at **date** grain with
sidereal derived at read (`engine.py:173-279`); on the "live" path, a delegate
(`platform/scripts/temporal/compute_transits.py`) that discards the time of day and computes at
**00:00 UT of the query date** (`:77-79,:183` [R]; `engine.py:312-313` passes `query_dt` into the
birth-instant slot [R]), forces Moshier (`:83`), discards `retflag` (`:84`), and uses **TRUE
node** on both paths (`engine.py:19-20`; `compute_transits.py:54,63` [R]) — after the native ruled
mean (D6). The forensic self-test "at 10:43 IST" passes by coincidence of sign: the Moon at
00:00 UT is 324.48°, at the birth instant 327.06°, both Aquarius [R]. Meanwhile the served route
`/api/compute/ephemeris_at_t` is the L0 `bg_ephemeris_engine` surface reused as-is
(`routers/ephemeris.py:11-12,45-46,211-213` [R]): true instant, MEAN node (`:82`), Swiss-file
with observed fallback and a per-call backend assertion (`:12-24,:154-156`), a typed
`_service_context` (`:27-73`), HTTP 422 on an unknown id (`:250-258`). And **no L3 writer consumes
the engine's computation** — the four overlay writers import constants only
(`ka_kota_chakra/writer.py:56`, `ka_moorti_nirnaya/writer.py:49`, `ka_sudarshana_varsha/writer.py:34`,
`ka_vedha_gochara/writer.py:60` [R]) and read `ephemeris_daily` themselves; the engine's real
callers are its own self-test, `service_probes.py:618`, `pyjhora_adapter/transits.py:82-86` (no
caller of it found within scope) and **L4** `brahmagyan/phala/muhurta.py:737` (PATH-A, literal
`"lahiri"`) [R]. Yet the served route's *availability* is gated on the engine's probe
(`call_service_wrappers.ts:215-219`, `max_age_seconds: 900` [R]) — the unqualified implementation
certifies the qualified one. Recommendation: **`INTEGRATE` + `QUALIFY_LIMIT` +
`RETIRE_AFTER_MIGRATION` (the 00:00-UT live path)** — the route's computation is the reference
for instants; the engine's live path delegates to it (or to the same shared kernel) with MEAN
node; PATH-A is kept and graded `date_grain`/`noon_ut_knot` for stored-knot reads; ayanāṃśa ids
validated against L0's existing `AYANAMSHA_MAP` (no fourth vocabulary); the served route's
existing convention-vector field names adopted, not rivalled; the self-test made a detector for
instant precision and node frame; the probe-contract digest re-pinned as a Pūrṇa packet.
Decision for the native: confirm the reference and the node-frame computation change with its
ripple (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:136) | *"Position/motion service. P/I/Q: arbitrary instant/frame provenance; self-test is bounded service proof. DP07."* | unchanged — and "arbitrary instant" is exactly what the engine's live path does not do (§3) |
| Strategy §6.1 **L3-A01** (`:271`) | *"prove exact conventions, time, arbitrary-chart input, provenance and failures; a canonical probe is not full service qualification."* W2 | unchanged |
| W0 field register #7 | `service get_ephemeris → EphemerisResult/GrahaState`, zero DML | `EphemerisResult.source` documents `'mixed'`, never produced (`engine.py:134` [R]) |
| Lane D §4 / T1 | DIVERGENT consumer: `call_ephemeris_at_t` → the route with its own swisseph (deliberate) | confirmed and sharpened: the route is the **L0 `bg_ephemeris_engine` surface** (`service_asset_id`, `registry_generation = bg_ephemeris_engine@migration-624`, `:11-12,45-46` [R]), not merely "its own integration" |
| STATE.md ★ `:219-235` | two vocabularies; a value test on the engine certifies nothing a caller touches | confirmed; **stronger**: the route's availability is certified by the engine's probe (F18) |
| Lane F §2a | `engine.py:302-306` hard `'lahiri'` gate on the live path | `:306-310` [V]; the delegate additionally hard-codes `SIDM_LAHIRI` and `FLG_MOSEPH` (`compute_transits.py:79-80,:83` [R]) |
| Blueprint chronicle §11.18 (not "G4" — G4 was **retracted** at v2.6/v3.5/v4.0 [R]) | the ephemeris backend is process-global and unowned; `panchang_engine/__init__.py:71,149,252,347` `set_ephe_path(None)` [R] | this engine sets no path and asserts no backend [V]; the **route does** (F4) |
| L0 items 6–7 / PR #2727 | node frame + epoch declared on `ephemeris_daily` rows; "applied to production" | **not in this tree** — highest migration 1072; no migration adds `node_mode`/`epoch_convention` to `ephemeris_daily` (grep → only `624_…probe_contract.sql`) [R]; blueprint `:383` "PR #2727 open and RED" vs `:189,:287` "applied" — the blueprint contradicts itself and is corrected in v5.1 |
| L0 `brahmagyan/l0_ephemeris.py` [R] | `:77` `{"name": "Rahu", "swe_id": 11}` with a *"Mean North Node"* comment; `:287` `swe.calc_ut(jd, 11, …)` — **11 is `TRUE_NODE`** (`MEAN_NODE=10`); `:277` noon UT; `AYANAMSHA_MAP` `:91-119` holds the six legacy keys **and** `lahiri_chitrapaksha`, `true_chitra`, `surya_siddhanta_classical` (EL-39); `_resolve_read_ayanamsha` `:139-156`; `_DEFAULT_READ_AYANAMSHA='lahiri_chitrapaksha'` `:137`; the map is `{}` without swisseph (`:118-119`) | the stored knots are TRUE-node under a mean comment — an **L0 question**, raised (§10.4); the resolver the engine should use exists |
| Synergy audit `:59` vs this brief | audit: "Kṣetra reads mean via `ephemeris_daily`"; code: L0 stores `swe_id 11` = TRUE | artifacts disagree; code sides with TRUE; recorded as the same L0 question |
| STATE.md `chart_facts` id set [A] | `{lahiri_chitrapaksha, true_chitra, krishnamurti, raman, surya_siddhanta_classical}` | confirmed by code at `routers/jaimini.py:76-80`, `constants.ts:2`, `l0_ephemeris.py:107-113` [R] — **not** in `CHART_FACTS_SCHEMA.json` (v1.0 §11.5 pointer wrong) |
| Blueprint v5.0 §3.5 row 1 (`:317`), §16.2 (`:899`), SC-8/SC-10 | "engine import hub for four overlay writers" | **wrong** — constants only (F3); corrected in blueprint v5.1 |
| L3 probe contract | `service_probes.py:582-583` rejects any `forensic_ayanamsha` but `'lahiri'`; digest `nirmana_probe.py:69,107`; `call_service_wrappers.ts:215-219` gates the route on `graha_sancara_forensic` with `probe_contract_sha256`, `max_age_seconds: 900` [R] | moving the probe to the canonical id changes a digest pinned in a Pūrṇa-owned wrapper — coordinated packet (§5) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Identity and registration [V]
`platform/scripts/seed/asset_registry_seed.ts:2230-2245`: `storage_type: 'service'`, no table,
`depends_on: ['bg_ephemeris']`, `scope: 'global'`, `asset_kind: 'service'`. The served route
self-identifies as `service_asset_id: "bg_ephemeris_engine"` (`routers/ephemeris.py:45` [R]) —
two registered identities behind one tool name.

### 2.2 The code [V]/[R]
- **Writer** `writers/ka_graha_sancara.py`: FORENSIC self-test at 1984-02-05 10:43 IST — six
  checks (`:118-248` [R]), raises on unhealthy (`:94` [R]); writes `service_health` +
  `last_selftest_at`; `WriterResult(rows_inserted=0)`. The "exact birth instant" value it checks
  (`:172`) is the **00:00 UT** value (F1).
- **Engine** `services/ka_graha_sancara/engine.py`:
  - `SUPPORTED_AYANAMSHAS = {"lahiri","raman","kp","krishnamurti","yukteshwar","surya_siddhanta"}`
    (`:64`) — a stale hand-copied subset of L0's `AYANAMSHA_MAP` [R]; validated at `:376-379`.
  - **PATH-A** `_read_from_bg_ephemeris` (`:173-279`): stored **tropical** rows at `date`
    (`:220`), `derive_sidereal(trop_lon, jd, ayanamsha)` (`:253`, already accepts the canonical id
    [R]); returns `None` on any failure (`:228,:248,:256` [R]) → falls to the live path
    (`:425-427`) → for a non-lahiri *in-range* request that surfaces as `NotImplementedError`
    (`:306`) — a read failure wearing a vocabulary error (F19).
  - **Live path** `_compute_live` (`:284-339`): `if ayanamsha != "lahiri": raise NotImplementedError`
    (`:306-310`); `get_transit_states(query_dt, q_date, ayanamsha=…)` (`:313`) → `platform/scripts/
    temporal/compute_transits.py:158-161` whose first positional is `birth_dt`; positions at
    `jd = _sidereal_jd_ut(query_date)` = `swe.julday(y, m, d, 0.0)` (`:77-79,:183`) — **00:00 UT
    of the date, time-of-day discarded**; `SIDM_LAHIRI` hard-coded (`:79-80`); `FLG_MOSEPH` forced
    (`:83`); `pos, _ = swe.calc_ut(...)` discards `retflag` (`:84`); `"ephe_mode": "moshier"`
    constant (`:216`); `swe.TRUE_NODE` (`:54,:63`); nodes `is_retrograde` forced `False`
    (`:187,:197-198`) [R].
  - TRUE node on PATH-A too (`engine.py:19-20` "TRUE_NODE everywhere"; L0 stores `swe_id 11`) [R];
    `is_retrograde` for nodes forced `False` (`:263`) [R].
  - Cache keyed `(date_str, ayanamsha)` (`:143-168`; key `:151-152`) — with a caller-supplied
    `_cache` (`:396-407`) any later instant on the same date returns the first instant's grahas [R].
  - Naive datetimes assumed **Asia/Kolkata** (`:381-391`); `q_date = dt.date()` in that zone
    (`:393`) selects the PATH-A knot [R] — a global-scope service with a native-specific default.
  - `GrahaState.applying_or_separating(target_lon_deg)` (`:84`).
- **Served route** `routers/ephemeris.py`: `_ephemeris_backend(retflag)` (`:12-24`), per-body
  `retflag` (`:154-156`), `_service_context` (`:27-73`) emitting `node_mode`, `frame`,
  `ayanamsha_id`, `input_precision`, **`ephemeris_backends_observed`** ∈ `{jpl_file,
  swiss_ephemeris_file, moshier_analytic_fallback}`, `backend_observation_state`,
  `backend_qualification_state`, `failure_contract` (`unknown_ayanamsha: "HTTP_422"`, `:66`);
  `('Rahu', swe.MEAN_NODE)` (`:82`), `"node_mode": "mean"` (`:48`); retrograde = `speed < 0`
  (`:128`); canonical-id → `SIDM_*` map (`:226-232`), default (`:233`), note on the two Lahiri
  names (`:223-225`); route decorator `:241`, body `:242-291`; naive datetime rejected
  (`:264-268`); shared helper `_calculate_sidereal_positions` (`:140-173`) also used by the natal
  endpoint (`:176-197`) [R]. The engine is not imported (`:200,:244` comment only [V]).
- **TS wrapper** `call_service_wrappers.ts:170-262`: default `DEFAULT_AYANAMSHA` (`:227`);
  `PYTHON_SIDECAR_URL` guard (`:235-240`); availability contract gated on the **engine's** probe
  (`:215-219`).

### 2.3 Consumers (search boundary: sidecar `services/`, `routers/`, `pipeline/`, `brahmagyan/`, `pyjhora_adapter/`; `platform-mcp/src`; `platform/src/lib/retrieval`; tests excluded) [R]
| consumer | reads | role |
|---|---|---|
| the four overlay writers (`ka_kota_chakra/writer.py:56`, `ka_moorti_nirnaya/writer.py:49`, `ka_sudarshana_varsha/writer.py:34`, `ka_vedha_gochara/writer.py:60`) | **constants only** (e.g. `NAKSHATRAS` ordering); their positions come from their own SQL on `ephemeris_daily` (`kota :96`, `moorti :77`, `vedha :106`) | vocabulary |
| `writers/ka_graha_sancara.py:120,176,232`; `service_probes.py:618` | `get_ephemeris` (self-test / probe) | probe |
| `pyjhora_adapter/transits.py:82-86` | `get_ephemeris(force_live=True)` — *"precise live computation"* (F1 applies) | `computation`; **no caller of this adapter found within scope** |
| `brahmagyan/phala/muhurta.py:737` (**L4**) | PATH-A, literal `"lahiri"` | `computation` (cross-layer; outside the L3 search boundary v1.0 declared) |
| the served route | **its own computation** (the L0 surface) | the divergence |
| `pipeline/transit_search.py`, `panchang_engine`, `w2g`, Saṅgam scanner | their own swisseph integrations (SC-8) | siblings |

**Live-path statement.** The engine's computation is live for **no L3 writer**; it is live for the
pyjhora adapter (no caller found within scope — not asserted unused) and for L4 muhūrta (PATH-A).
The served route is live on the L0 surface. The engine's probe gates the served route's
availability — live.

### 2.4 Epistemic class of the important quantities
| quantity | class | authority | note |
|---|---|---|---|
| tropical longitude/speed at a knot | `COMPUTED_FACT_CONFIGURATION` | L0 `ephemeris_daily` (noon UT `:277`; `swe_id 11` TRUE node `:77,:287`) | PATH-A: `time_basis='noon_ut_knot'`, `claim_grain='date_grain'` |
| sidereal longitude (PATH-A) | computed fact | `derive_sidereal` under a named ayanāṃśa | `ayanamsa_application` declared |
| "live" positions | computed fact **at 00:00 UT of the date** | `compute_transits.py` (Moshier forced, TRUE node) | not an instant; not in the B1 `time_basis` enum — §4 item 2 |
| route positions | computed fact at the instant | L0 `bg_ephemeris_engine` surface; MEAN node; backend observed per call | the qualified computation |
| `service_health` | status | six checks at one instant, on the 00:00-UT value | cannot detect the instant defect or the node frame — §N.8 |
| `is_retrograde` (nodes) | convention | engine: forced `False` both paths; route: `speed < 0` | parity contract item (F13) |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; the W2 service-payload freeze at `47131772b` is **unverified** (that commit's
stat does not name this asset [R]). t3: no event. Cost: unmeasured.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Ask the **registered engine** for positions at 1984-02-05 05:13 UT (the birth instant) on its live path: it returns the Moon at 324.4787° (00:00 UT), not 327.0550° (05:13 UT) — 2.58° off, TRUE node, Moshier, `ephe_mode` constant — and its self-test calls that value "the exact birth instant" (`writers/ka_graha_sancara.py:172`; `service_probes.py:546-548`; `tests/l3/test_m3_graha_sancara_defects.py:71-74` [R]). Ask the **served route** the same: it returns the instant, MEAN node (1.02° from TRUE at that instant [R]), with `ephemeris_backends_observed` asserted. Two answers, two frames, and the served route's availability is certified by the probe of the one that is wrong |
| Evidence | `compute_transits.py:77-79,:183,:54,:63,:79-80,:83,:84,:216`; `engine.py:19-20,:312-313,:306-310,:64`; `routers/ephemeris.py:82,:48,:12-24,:154-156`; `call_service_wrappers.ts:215-219` — all [R]; reviewer's swisseph run (Moshier): Moon 324.4787° / 327.0550° / 330.4060° (00:00 UT / 05:13 UT / 12:00 UT knot); true−mean 1.0213° |
| Expected contract | L3-A01 (*exact conventions, time, arbitrary-chart input, provenance, failures*); D6 (mean node) = Kṣetra 7 = Gochara N-4a = Saṅgam M-1; DP01 (no rival definitions); DP03 (pinned context); Foundation F28 (a status names the path that can turn it false); binding B1 (`time_basis`), B6 (node = mean) |
| Defect class | **wrong authority** (the unqualified implementation's probe certifies the qualified route) + **detector mismatch** (`service_health` cannot see the instant or frame defect) + **wrong context** (frame and epoch differ between the two) + **stale vocabulary** |
| Impact | Q09 substrate: a convention-sensitivity answer built on the engine would compare against the wrong frame; any consumer that trusts `force_live` (the pyjhora adapter) gets a midnight value; L4 muhūrta reads PATH-A under a legacy id; the served route can go dark on a probe that measures the other implementation |
| Non-claim | The reviewer's figures are Moshier; Swiss-file values differ at arc-second level, not the degree level these findings rest on; whether the pyjhora adapter has a live caller is unresolved; which node `ephemeris_daily` physically stores is inferred from `l0_ephemeris.py:77,287`, not queried |

---

## §4 — The semantic delta (contract §4) — smallest sufficient change

1. **L3-Q served.** Substrate for Q01/Q03; directly Q09 (convention sensitivity — five ayanāṃśas
   at one instant; `comparable_with='different_convention'` between them). No window question.
2. **Grading before repair (B1).** PATH-A: `time_basis='noon_ut_knot'`, `claim_grain='date_grain'`,
   `inclusivity` n/a. The engine's current live path: a 00:00-UT knot — **not in the B1 enum**;
   this brief proposes the binding amendment `time_basis += 'midnight_ut_knot'` only so the
   *retiring* path can be labelled honestly for one generation; it is never a served basis.
3. **The reference is the route's computation (F6).** The `bg_ephemeris_engine` surface (true
   instant, MEAN node, Swiss with observed fallback, `SWISS_STATE_LOCK`-serialised) is the
   reference for instants. The engine's live path **delegates to it** (or both call one shared
   kernel extracted from `_calculate_sidereal_positions` `:140-173`); the 00:00-UT delegate is
   `RETIRE_AFTER_MIGRATION` (one generation, labelled). PATH-A stays for stored-knot date-grain reads.
4. **Node frame is a computation delta, not a label (F2).** TRUE → MEAN on the engine's instant
   path via item 3; PATH-A depends on **what L0 stores** (`swe_id 11` = TRUE under a "mean"
   comment) — raised to L0 as a question (§10.4); until changed, the engine asserts
   `node_convention='true'` on PATH-A, never `'mean'` (§N.7 items 3/6). Ripple: the four overlay
   writers are unaffected (constants only); `pyjhora_adapter/transits.py` and L4 `muhurta.py:737`
   are named as consumers whose values move.
5. **Convention vector — adopt the route's existing names (F4).** `ephemeris_backends_observed`,
   `backend_observation_state`, `backend_qualification_state`, `node_mode`, `frame`,
   `ayanamsha_id`, `input_precision`, `failure_contract` are the L0 probe-contract vocabulary
   (`nirmana_probe_contracts.json`; `service_probes.py:292,342-347` [R]); the engine emits the same
   names. The build-side spellings in Saṅgam's `frame_vector` (`node_convention`,
   `ayanamsa_application`, `epoch_convention`) are **mapped, not rivalled** — this brief's mapping
   table: `node_mode ↔ node_convention`; `frame ↔ ayanamsa_application`; `ephemeris_backends_observed
   ↔ ephemeris_backend`; `epoch_convention` (build-side only). SC-8's packet fixes one spelling in
   the binding; until then both sides declare the mapping.
6. **Vocabulary (SC-10, F10).** `SUPPORTED_AYANAMSHAS` is replaced by validation against L0's
   `AYANAMSHA_MAP` (import, no L0 edit) with `DEFAULT_AYANAMSHA` as the default; unknown → the
   engine's typed `ValueError` (`:376-379`, already right); **the route keeps HTTP 422** (F8) — an
   unknown token is a caller error, not F06 `unavailable`; `unavailable` is reserved for
   out-of-range and PATH-A read failures (`reason='path_a_read_failed'`, F19).
7. **Naive datetimes (F12).** Rejected, as the route does (`:264-268`); the Asia/Kolkata default
   (`:381-391`) is removed — tz from the caller or the chart, never a native-specific constant.
8. **Cache (F11).** Keyed on the instant when computing at an instant; PATH-A's date key kept and
   labelled `QUALIFY_LIMIT`.
9. **Self-test as a detector (F1, F18).** The writer adds: a non-midnight instant checked against
   the reference (fails on today's code by 2.58° on the Moon); node frame checked against the
   ruled convention (fails on today's TRUE); the canonical id accepted; backend observed. Then
   `service_health` has real ways to read `unhealthy`; the probe contract's `forensic_ayanamsha`
   allowlist (`service_probes.py:582-583`) and digest (`nirmana_probe.py:69,107`,
   `call_service_wrappers.ts:215-219`) are re-pinned in a **coordinated Pūrṇa packet** — a digest
   change is a Pūrṇa-owned surface.
10. **Old vs new.** Positive: 05:13 UT via the engine → 327.06°, MEAN Rāhu, backend observed.
    Negative: `'kp'` → typed `ValueError` in the engine / 422 at the route. Boundary: 2150-12-31
    23:59 UTC → instant path answers; PATH-A `unavailable(out_of_range)`. Missing: `.se1` absent →
    `moshier_analytic_fallback` observed, never silent. Duplicated: the same instant via PATH-A and
    the instant path → `time_basis` differs, longitudes within the date-grain tolerance.
11. **Simpler baseline.** The route as it is today (already qualified) and the engine as it is.
12. **Ablation (F9).** A **golden-value fixture at the served envelope**: mutate the reference
    kernel (e.g. one `SIDM_*` entry, or `MEAN_NODE → TRUE_NODE`) → the golden values fail. Parity
    engine ↔ route is a **transition-commit** test only (the two must agree before the engine
    delegates); after delegation there is one computation and the golden fixture is the detector.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: PATH-A (stored knots + sidereal derivation), the memo cache (labelled), `applying_or_
  separating`, the route's `_service_context` and 422 contract, the forensic anchor (re-based on
  the true instant).
- `QUALIFY_LIMIT`: PATH-A `date_grain`/`noon_ut_knot`; PATH-A `node_convention='true'` until L0
  answers; the date-keyed cache.
- `INTEGRATE`: one vocabulary (L0's map), one reference computation, golden-value tests.
- `RETIRE_AFTER_MIGRATION`: the 00:00-UT live delegate (`compute_transits.py` for this caller) —
  its other consumers traced at stage 3 before retirement.
- **Consumers whose values move**: `pyjhora_adapter/transits.py` (no caller found in scope), L4
  `brahmagyan/phala/muhurta.py:737` (PATH-A — unchanged unless L0's stored node changes). The four
  overlay writers: unaffected.
- **Coordinated Pūrṇa packet**: probe-contract digest re-pin (`call_service_wrappers.ts:215-219`);
  the natal endpoint (`routers/ephemeris.py:176-197`) shares the helpers — its tests run.
- **DEMAND with blocker (F7)**: L0 items 6–7 (row declarations) are not in this tree; the engine
  asserts its vector from its own constants meanwhile (noon UT `l0_ephemeris.py:277`; node per
  item 4).
- **SC-8 boundary**: this brief asserts the vector *in this engine and its delegate*; it does not
  set the process path and does not touch `panchang_engine`, `transit_search.py`, `w2g`.
- No table, no migration, no rows; rollback = the engine's delegation is one flag; PATH-A untouched.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_graha_sancara`, L3 service, global; epistemic: astronomical computation; two registered identities behind one tool (`bg_ephemeris_engine` at the route); `INTEGRATE + QUALIFY_LIMIT + RETIRE_AFTER_MIGRATION` |
| B | `bg_ephemeris` declared and real (PATH-A); the delegate script is an undeclared code dependency (now in `may_touch`); no hidden table; fan-out: constants ×4, adapter, L4, the probe → route availability |
| C | invariants: instant path = reference within tolerance; `node_convention` = ruled convention; sidereal = tropical − ayanāṃśa(jd) under the declared method; nodes' `is_retrograde` convention stated; golden values at the served envelope. Detectors: the re-based self-test, the golden fixture |
| D | n/a (service) |
| E | real callers per §2.3; the served route is the qualified sibling; the engine's probe gates it |
| F | every response carries the route's context vocabulary; unknown id typed |
| G | no hotspot measured; **justified no-change** |
| H | idempotent; no writes; the route's `SWISS_STATE_LOCK` preserved |
| I | files in `may_touch`; W2; coordinated Pūrṇa digest packet; consumer trace of `compute_transits.py` at stage 3 |
| J | this brief; §7; both reports; the golden fixture output |

---

## §7 — Proof matrix

| proof | fixture | expected | invariant | detector fails when… |
|---|---|---|---|---|
| Positive | 1984-02-05 05:13 UT, canonical id, engine instant path | Moon 327.06° ± tol; Rāhu MEAN; `ephemeris_backends_observed` asserted | instant, not midnight | 324.48° (today's value) |
| Negative | `'kp'` at the engine / at the route | typed `ValueError` / HTTP 422 | route contract kept | 200-and-`unavailable` |
| Relevant influence | `lahiri_chitrapaksha → raman` | Δ = Δayanāṃśa; `node_mode` unchanged **after** item 4 (today it is `true`; asserted as such) | Δayanāṃśa | Δ ≠ Δayanāṃśa |
| Irrelevant control | `'lahiri'` alias vs canonical via L0's map; `is_retrograde` convention on nodes declared | identical longitudes; nodes' flag per declared convention on both sides | alias-invariant | differ |
| Duplication | same instant PATH-A vs instant path | `time_basis` differs; longitudes within date-grain tolerance; Rāhu differs by ~1° until L0 answers (declared) | labelled | labels equal |
| Context | `.se1` absent | `moshier_analytic_fallback` in `ephemeris_backends_observed` | observed | missing |
| Boundary | 1900-01-01 00:00 / 2150-12-31 23:59 UTC; 0°/360° seam | instant path answers; PATH-A `unavailable(out_of_range)` | seam-safe | mishandled |
| Delivery | sentinel `claim_grain='date_grain'` on a PATH-A answer | reaches the served envelope | survives | absent |
| Revision | L0 `ephemeris_daily` regenerated | PATH-A changes; instant path unchanged | no cache | stale |
| Value (F9) | mutate the reference kernel (`MEAN_NODE → TRUE_NODE`) | golden values at the served envelope fail | detector | passes under mutation |
| Transition | engine ↔ route parity at N instants incl. the forensic instant, a station, the seam | agree within tol before delegation | one computation after | disagree |

Binding: **OFFERS** B1 (`time_basis`, `claim_grain`), B2 (`epistemic_class='COMPUTED_FACT_
CONFIGURATION'`, `completeness_state`, `operator_role='computation'`, `comparable_with=
'different_convention'` across ayanāṃśas), the SC-8 vector under the route's names with the
mapping to the binding's build-side names. **DEMANDS** L0 items 6–7 (blocker: not in tree) and an
L0 answer on the stored node frame. `tier_basis`, `independence_group`: n/a (no score, no
testimony) — stated.

---

## §8 — Prioritization

(1) grade honestly (labels that are true today: `date_grain`, `node_convention='true'`; a self-test
that can fail) → (2) vocabulary via L0's map (SC-10) → (3) delegate the instant path to the
reference (the real repair; retire the midnight delegate) → (4) node frame with L0's answer → (5)
the probe-digest re-pin (Pūrṇa). T0, W2; no P-candidate; unblocks nothing downstream in L3
(constants only) — it unblocks the *honesty* of the served route's availability signal.

---

## §9 — Disposition and target state

`INTEGRATE` + `QUALIFY_LIMIT` + `RETIRE_AFTER_MIGRATION`. Data-plane: `PRODUCER_READY` after §7;
`CONSUMER_INTEGRATED` when the served route's availability probe certifies the served computation
and the golden fixture is on `main`. Campaign: `ANALYZED` → `OPTIMIZED/JUSTIFIED`. Non-claims: no
`DATA_ACCEPTED`; no `VALUE_EVALUATED` (this asset's value is the absence of a wrong frame or a
midnight value under an instant label, shown by detectors, not by a reading delta); which node
the store holds is an inference until L0 answers.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Reference computation for instants: the served route's `bg_ephemeris_engine` surface (or a shared kernel extracted from it); the engine's 00:00-UT live delegate retired after one labelled generation** | **yes** — the reviewer's evidence flips v1.0's recommendation |
| 2 | Adopt L0's `AYANAMSHA_MAP` as the one vocabulary; `DEFAULT_AYANAMSHA` default | yes (SC-10) |
| 3 | Node frame TRUE → MEAN on the engine's instant path now (via delegation); PATH-A follows L0 | yes; ripple named (adapter, L4 muhūrta) |
| 4 | **L0 question:** `l0_ephemeris.py:77/287` computes `swe_id 11` (TRUE) under a "Mean North Node" comment — is the stored knot set intended TRUE (then the comment is wrong) or MEAN (then the store is)? | route to L0's owner with the synergy audit's row (`:59`) which assumed mean |
| 5 | Binding amendment: `time_basis += 'midnight_ut_knot'` for the retiring path's one labelled generation | yes, narrowly |
| 6 | Tolerance for the golden fixture | set from measurement at stage 3 (Swiss vs Moshier differ at arc-seconds) |

---

## §11 — Not verified here

1. Production state (`service_health`, `.se1` on the host, live incidence) — no DB, no network.
2. Whether `pyjhora_adapter.transits.compute_transits` has a live caller — none found in sidecar
   non-test scope; not asserted unused.
3. "Service payload frozen at `47131772b`" — unverified (that commit's stat does not name this asset).
4. Which node `ephemeris_daily` physically stores — inferred from `l0_ephemeris.py:77,287`.
5. Per-call latency.
6. The reviewer's swisseph figures are Moshier (no `.se1` on that host); Swiss-file values differ
   at arc-second level.

## §12 — Review dispositions (v1.0 → v1.1)

F1 accepted (§0, §2.2, §2.4, §3, §4.2/3/9, `may_touch`); F2 accepted (§0, §2.4, §4.4, §7, §10.3–4);
F3 accepted (goal, §0, §2.3, §5); F4 accepted (§4.5); F5 accepted (`may_touch`, §4.3); F6 accepted —
§10.1 flipped; F7 accepted (frontmatter, §1, §5); F8 accepted (§4.6, §7 negative); F9 accepted (§4.12,
§7 value/transition); F10 accepted (§4.6); F11 accepted (§4.8, §5); F12 accepted (§2.2, §4.7); F13
accepted (§2.4, §7 irrelevant control); F14 accepted (ranges, paths, `may_touch`); F15 accepted (§1);
F16 accepted (removed); F17 accepted (§0, §2.3); F18 accepted (§1, §4.9, §5); F19 accepted (§2.2,
§4.6); F20 accepted (§2.1, §1).
