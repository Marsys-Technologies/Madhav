---
artifact: L3_W1_ANALYSIS_BATCH_C
canonical_id: L3_W1_ANALYSIS_BATCH_C
version: "1.0"
status: DRAFT-FOR-W2
produced_on: 2026-09-05
campaign_id: nirmana-elevation
layer: L3
batch: C
theme: "The four L3 service assets — probe truth, serving reality, and the currents they were built to feed"
assets:
  - ka_graha_sancara
  - ka_muhurta_seva
  - ka_dasha_kala
  - ka_tulana
analyst: W1 analysis subagent (read-only)
db_read_path: ".l3-tools/q.sh (role amjis_app, SELECT only)"
canonical_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
---

# L3 W1 ANALYSIS — BATCH C: the four L3 services

## Batch summary

1. **F-L3-3 is resolved: `ka_graha_sancara` is genuinely broken, and it is a check-correction
   PLUS a real code defect — not stale state.** The recorded `selftest_detail` error
   `"ephemeris computation failed: 0"` is `str(KeyError(0))`. `services/ka_graha_sancara/engine.py`
   `_read_from_bg_ephemeris()` indexes fetched rows **positionally** (`row[0]`, `row[1]`…) while the
   orchestrator's connection is built with `row_factory=psycopg.rows.dict_row`
   (`pipeline/orchestrator/db.py:57`). Rows come back as dicts; `row[0]` raises `KeyError: 0`;
   `str()` of that is the bare string `0`. **Independent documentary corroboration:**
   `brahmagyan/phala/muhurta.py:_transiting_sign_ids()`'s own docstring already states —
   *"A tuple-row connection is opened deliberately: that helper indexes rows positionally (`row[0]`),
   so the module-default `dict_row` factory used elsewhere in this file would break it."* A different
   author, in a different layer, found this defect and worked around it at their call site instead of
   fixing the engine.
2. **`ka_graha_sancara`'s self-test carries a SECOND, independent defect that survives the first
   fix: FORENSIC check 4 is structurally unsatisfiable on the read path it exercises.** Check 4
   asserts natal Moon = Aquarius at 1984-02-05 10:43 IST, but PATH-A reads `ephemeris_daily`, which is
   computed **at 12:00 UT** (`brahmagyan/l0_ephemeris.py:267,275` — *"Compute tropical positions … at
   12:00 UT"*; `_tropical_to_jd` = `swe.julday(y,m,d,12.0)`, docstring *"noon UT"*). Measured:
   stored tropical Moon on 1984-02-05 = **354.036588°**; measured Lahiri ayanamsha for that instant
   (derived from L1's own Sun: tropical-at-birth 315.5878 − L1 sidereal 291.962617 = **23.625°**)
   gives PATH-A sidereal Moon = **330.41° = Pisces**, not Aquarius. L1's natal Moon is **327.0552°,
   Aquarius, Purva Bhadrapada pada 3** — a **3.36° / 6.8-hour** difference that is exactly the
   birth-instant-to-noon-UT gap. **This check has never been green in the writer's real execution
   path.** The 19/19 passing unit tests never exercise it: `test_ac7_forensic_moon_aquarius` calls
   `get_ephemeris(..., db_conn=None)` → PATH-B live compute at the true instant → Aquarius; and the
   only PATH-A test feeds a `MagicMock` returning **tuples** with **synthetic** longitudes. This is
   the C12 / §N.8 case verbatim: **a check that has never been green is a PROPOSAL, not a gate.**
3. **Nothing anywhere reads `asset_registry.service_health` as a gate.** Grep across `platform/` and
   `platform-mcp/` finds only writes. Measured consequence: `ka_graha_sancara` is
   `asset_throughput.state = 'lit'` (last_built_at 2026-08-02 13:50:52) **while**
   `service_health='unhealthy'`. Its writer even computes the verdict
   (`status = "success" if health == "healthy" else "error"`,
   `writers/ka_graha_sancara.py:83`) and then **discards it** — `WriterResult` has no status field
   and the orchestrator treats any non-raising return as success. `ka_muhurta_seva`'s writer is the
   already-in-repo correct pattern and says so in a comment: *"Raise so `_run_data_writer` catches it
   and calls `mark_asset_error` — the only signal path that prevents the orchestrator from marking
   this asset 'lit'. A returned WriterResult is always treated as success…"* Three of four batch-C
   writers (`ka_graha_sancara`, `ka_dasha_kala`, `ka_tulana`) return instead of raising.
4. **The `ka_muhurta_seva → ka_graha_sancara` edge that makes the E-gate look blocked is
   DECLARED-BUT-UNREAD.** `services/ka_muhurta_seva/` imports `panchang_engine` and `muhurat.finder`
   only; its own `__init__.py:27` says *"Depends on: ka_graha_sancara (planned)"*. Correcting the
   registry edge to the real dependency (`bg_panchanga`) unblocks the spine **without weakening any
   gate** — it makes the registry true, which is the opposite of a weakening.
5. **Two 100%-measured leverage failures, both one-word root causes.**
   (a) `ka_muhurta_seva`'s only production consumption — `_c_panchanga_quality()` in
   `services/ka_sangam/engine.py:471` — calls `muhurta_service.score(..., event='general')`, but
   `'general'` is not in `EVENTS_MVP`; `score_muhurat` raises `ValueError`, the `except` swallows it
   at debug level, and the function returns `0.0`. Measured on the native's chart:
   `c_panchanga_quality = 0.0` in **1128 / 1128 (100.0%)** Mode-A `kala_convergence` rows, max value
   `0.0`. (b) `ka_dasha_kala`'s eligibility prior reaches the composite in only **49 / 1128 (4.3%)**
   of Mode-A rows — `dasha_score` is the static fallback `0.5` in **1079 / 1128 (95.7%)** and takes
   exactly **2 distinct values** chart-wide (`0.5` static, `0.85` = the EXACT band). The RELATED band
   (`0.50`) is **unreachable** because `mode_a_search` passes `related_lords=set()`, so the
   three-tier soft prior the service implements collapses to binary.
6. **`ka_tulana` is unambiguous shelf inventory, and the missing piece is ~30 lines.** Zero reverse
   dependency edges in `asset_registry`; zero production importers (only its own writer + tests). Its
   `WindowInput` dataclass is a **field-for-field match** to `kala_convergence`
   (`convergence_id/mode/peak_date/window_start/window_end/convergence_score/confidence_label/
   rarity_years/signal_id/source_citation/domain`) plus `kala_darshana.net_label` — and those tables
   hold **14,868** and **750** rows for the native, with **100% fill** on every field the ranker
   needs (`domain` 14,390/14,868 = 96.8%). The adapter that would feed them in **does not exist**.
   Meanwhile the served `call_priority_ranking` tool reimplements a *different* ranking in TypeScript
   over `bodha_msr_signals ⨝ kala_activation`, using none of convergence / rarity / proximity /
   confidence, and offering neither `compare(A,B)` nor the attention map.
7. **The registry's own service metadata is uniformly empty for all four.** `health_probe` NULL,
   `provides_apis` NULL, `count_sql` NULL, `integrity_check_sql` NULL, `expected_volume_formula` /
   `expected_volume_inputs` NULL, `rebuild_on_probe_fail` false, `catalog_status` DRAFT,
   `last_invoked_at` NULL on all four. `target_floor` is inconsistent (NULL / NULL / 0 / 0) across
   four assets of identical kind. Templates for the two missing JSONBs already exist in-repo:
   `bg_panchanga` and `bg_ephemeris_engine` carry populated `provides_apis` **and** `health_probe`,
   and `service_probes.py` already implements an `ephemeris_engine` probe type.
8. **One serving-plane correctness defect, measured to zero rows.** `call_dasha_eligibility`
   hard-codes `ayanamsha_id` default `'lahiri'` (a string literal, not `DEFAULT_AYANAMSHA`).
   `chart_dashas` contains **no** `'lahiri'` rows — the five stored values are
   `lahiri_chitrapaksha / true_chitra / krishnamurti / raman / surya_siddhanta_classical`. Measured:
   the default call returns **0 rows**; the same call with `lahiri_chitrapaksha` returns **3,401**.

---

## ka_graha_sancara

**One-line identity:** Ephemeris-at-T service — sidereal positions for all 9 grahas at an arbitrary
instant, via a cheap `ephemeris_daily` day-grain path (1900–2150) or a live swisseph fallback.

**Temporal question (D-TIME):** *"Where was every graha, sidereally, at this exact instant — and was
it applying to or separating from a given point?"*

### 1. Instrument fit
Serves **D-TIME** as the layer's zero-th primitive (every other L3 engine ultimately asks "where is
the sky at T?") and **D-GROUNDING P3** by being purely computational — its outputs are `pratyaksa`
and need no classical claim. It is still the right instrument *in concept*; **it is not the
instrument actually being used** (see §6 — the served endpoint is a second, independent swisseph
integration that never touches this engine).

### 2. Dependencies (declared vs real)
- **Declared:** `{bg_ephemeris}`. `bg_ephemeris` resolves (asset exists; `target_table =
  ephemeris_daily`). **Real and read** — PATH-A `SELECT body, tropical_longitude, speed_dps,
  is_retrograde FROM ephemeris_daily WHERE date=%s AND ayanamsha_id='tropical'`. VERIFIED: 9 rows
  exist for 1984-02-05; 825,084 rows total = 9 bodies × 91,676 days (1900-01-01→2150-12-31), an exact
  product.
- **Undeclared real reads (hidden edges):**
  (a) `brahmagyan.l0_ephemeris.derive_sidereal` / `_tropical_to_jd` — the L0 ayanamsha derivation,
      which itself requires pyswisseph. (b) `platform/scripts/temporal/compute_transits.
      get_transit_states` (PATH-B) — pyswisseph + Moshier, i.e. an effective `bg_ephemeris_engine`
      edge. Neither is declared.
- **Vocabulary split (INFERRED consequence, not yet a measured failure):** the engine's
  `SUPPORTED_AYANAMSHAS = {lahiri, raman, kp, krishnamurti, yukteshwar, surya_siddhanta}` is a
  *different* vocabulary from the canonical stored one (`lahiri_chitrapaksha`, …). Passing the
  canonical id to `get_ephemeris()` raises `ValueError("Unknown ayanamsha")`.

### 3. Leverage / NULL check
The asset has **no target table**, so the classical NULL check does not apply. The equivalent
question — *is a designed consumer getting nothing where this asset computes an answer?* — has a
sharp answer: **the served surface never calls this engine at all.**
`platform/src/.../call_service_wrappers.ts` `callEphemerisAtTCapability` POSTs to the sidecar's
`/api/compute/ephemeris_at_t`, and `routers/ephemeris.py`'s `ephemeris_at_t()` performs its **own**
`swe.set_sid_mode` / `swe.calc_ut` loop with its own `_AT_T_AYANAMSHA_MAP`. It imports nothing from
`services/ka_graha_sancara/`. The engine's two-path design, its `(date, ayanamsha)` memo cache, and
its `applying_or_separating()` helper are all unused at serve time.
In-process consumers of `get_ephemeris()` are exactly two: `pyjhora_adapter/transits.py`
(`db_conn=None, force_live=True` → PATH-B, unaffected by the bug) and
`brahmagyan/phala/muhurta.py` (opens a **deliberate tuple-row** connection to route around the bug).
Every `ka_*` writer that "imports ka_graha_sancara" (`ka_moorti_nirnaya`, `ka_sudarshana_varsha`,
`ka_kota_chakra`, `ka_vedha_gochara`) imports only the module **constants** `SIGNS`, `NAKSHATRAS`,
`ALL_GRAHAS`, `NAK_SIZE_DEG` — never `get_ephemeris`. **Net: PATH-A has zero live callers today; the
defect is currently latent for everyone except the self-test itself.**

### 4. Grounding tier
`pratyaksa` throughout, and correctly so — this is instrument output, not a classical claim. No
`sruti`/`yukti` labelling is owed. The one place a classical claim leaks in is the self-test's
FORENSIC anchor, which is a *verification* assertion, not a served output.

### 5. Temporal identity + arbitration
Overlapping temporal engines that answer "where is the sky at T": (i) this engine's PATH-A
(`ephemeris_daily`, **day-grain at 12:00 UT**); (ii) this engine's PATH-B (live swisseph,
**instant-grain**); (iii) `routers/ephemeris.py`'s `ephemeris_at_t` (live swisseph, instant-grain,
**independent implementation**); (iv) `pipeline/transit_search.find_aspect_events` (swisseph);
(v) L1 `chart_facts.graha_position` (instant-grain, the birth-chart authority).
**Arbitration rule this batch recommends for the Temporal Concordance Contract:** **L1 `chart_facts`
is authoritative for the natal instant (§N.5); for any non-natal instant, the instant-grain live path
is authoritative and PATH-A is a day-grain approximation that MUST declare its 12:00-UT epoch.** The
current code has no such rule, which is precisely how a natal-instant assertion (Moon=Aquarius) ended
up pointed at a noon-UT day row. A same-day query of PATH-A can be off by up to ~12° for the Moon
(0.494°/hour measured from the stored `speed_dps` 11.8585608).

### 6. Service
- **Serving capability:** `marsys://tool/L3/call_ephemeris_at_t` (MCP `call_ephemeris_at_t`), in the
  D5 fanout roster and `descriptor_defaults`. **It is a real, wired consumer — of the sidecar route,
  not of this asset's engine** (§3).
- **`provides_apis`: NULL.** The asset publishes `get_ephemeris(dt, ayanamsha, db_conn, force_live)`,
  `EphemerisResult`, `GrahaState.applying_or_separating(target_lon)` and the shared constants — none
  declared. `bg_ephemeris_engine` shows the intended shape.
- **Density (§N.6): not declared.** `callEphemerisAtTCapability` has no `density_contract` and no
  `empty_reason` discipline, while ~10 L1 capabilities do. It also does not surface which read path
  produced the answer, so a caller cannot tell a day-grain result from an instant-grain one.
- **Drill to L1 in ≤2 hops:** no — `grounds_to: { l1_fact_ids: false }`, and no `fact_id` is emitted.
  For a chart-agnostic ephemeris service that is honest, not a defect.

### 7. Measured cost
- `estimated_seconds = 1`. Real evidence: `asset_throughput.last_built_at = 2026-08-02
  13:50:52.04152+00`, `asset_registry.last_selftest_at = 2026-08-02 13:50:52.009718+00` → **~32 ms**
  between the health write and the throughput write. **This is a fast-fail, not a healthy-run cost** —
  check 1 raised immediately and checks 2–5 never ran. A healthy-run build cost is **unmeasured**.
- `last_invoked_at` is **NULL** — the registry has never recorded a service invocation.
- Serve cost of the (bypassing) sidecar route: **unmeasured**.

### 8. Findings

**F-KGS-1 · MUST · (§N.8 / C12 / B.10)** — `_read_from_bg_ephemeris()` indexes `dict_row` rows
positionally (`row[0]`, `row[1]`, `row[2]`, `row[3]`, `engine.py` body-map loop). Under the
orchestrator's `dict_row` connection this raises `KeyError: 0`, which is verbatim the stored
`selftest_detail` error `"ephemeris computation failed: 0"`. **This is a real code defect, not stale
state.** Fix: accept both row shapes at the read site, exactly as
`services/ka_dasha_kala/service.py:confirm_systems_present()` already does
(`if isinstance(rows[0], dict): …`). Cost: **~5 lines, one file, ~15 min**, plus a PATH-A test whose
mock cursor returns dicts (the current mock returns tuples, which is why CI never caught it).
Downstream bonus: the deliberate tuple-row workaround in `brahmagyan/phala/muhurta.py` becomes
unnecessary — **flag as an L4 hand-off, do not touch it from L3.**

**F-KGS-2 · MUST · (§N.8 "a check that has never been green is a PROPOSAL, not a gate"; §N.7 item 5)**
— Self-test check 4 asserts `_FORENSIC_MOON_SIGN = "Aquarius"` against a PATH-A read whose epoch is
**12:00 UT**, while the anchor is a **10:43 IST (05:13 UT)** birth instant. Measured: PATH-A yields
sidereal Moon 330.41° (Pisces); L1 holds 327.0552° (Aquarius, PBh pada 3). The check cannot pass on
the path it exercises, and never has. Fix (check-correction, **not** a gate weakening): the FORENSIC
natal anchor must be asserted against the **instant-grain** path (`force_live=True` or
`db_conn=None`), and PATH-A must get its own honest, path-appropriate assertion — e.g. *"PATH-A's
sidereal longitude for date D equals `derive_sidereal(stored_tropical, jd_noon_UT, ayanamsha)` to
within 1e-6°, and PATH-A declares `source='bg_ephemeris'` and its noon-UT epoch."* Cost: **~20 lines
in the writer + 1 new test, ~45 min.** Both F-KGS-1 and F-KGS-2 must land before a probe of this
asset can be honestly green — this is a **check-correction plus a real fix**, not stale-state-only.

**F-KGS-3 · MUST · (§N.8 — the earned-signal principle at the build layer)** — The writer computes
`status = "success" if health == "healthy" else "error"` and **never uses the variable**;
`WriterResult` carries no status field; the orchestrator marks any non-raising service writer `lit`.
Measured proof: `state='lit'` with `service_health='unhealthy'`. Fix: raise on failure, copying
`services/ka_muhurta_seva/writer.py`'s already-correct pattern and its explanatory comment verbatim.
Cost: **~6 lines, ~10 min.** Applies identically to `ka_dasha_kala` and `ka_tulana` (see F-KDK-3,
F-KTU-2) — one shared pattern, three sites.

**F-KGS-4 · NOW · (C12 registry-health)** — `health_probe` NULL. `service_probes.py` already ships an
`ephemeris_engine` probe type and `bg_ephemeris_engine` already carries a populated spec (forensic_jd,
expected_sun_sign, ephemeris file SHA-256s). Authoring a `ka_graha_sancara` `health_probe` — asserting
the *instant-grain* FORENSIC Moon sign and the PATH-A noon-UT identity, **not** a `count(*)=N` pin —
plus `rebuild_on_probe_fail=true` would give the C12 "current GREEN probe" a real mechanism.
Cost: **1 migration + probe-spec authoring, ~1–2 h.**

**F-KGS-5 · NOW · (§N.6 item 4, D-SERVICE)** — `provides_apis` NULL despite a real published API
surface; `callEphemerisAtTCapability` declares no `density_contract` and never reports which read
path answered. Fix: populate `provides_apis` (template: `bg_ephemeris_engine`), and add a
`source`/`grain` field to the served envelope. Cost: **~1 h** (registry) + **~1 h** (serving; note the
serving change is a TS edit and should be checked against L3's write-set before W3 schedules it).

**F-KGS-6 · NOW · (rubric 2, D-TIME)** — The served `/api/compute/ephemeris_at_t` is a **second,
independent** swisseph integration that bypasses this asset's engine, with its own ayanamsha map. The
route's own comment concedes the vocabularies are "pre-existing, independent naming conventions this
endpoint does not attempt to unify." Two implementations of the same question is exactly the
condition the Temporal Concordance Contract exists to arbitrate. Recommend W2 record it as a
concordance-contract entry (which path is authoritative, and why) rather than a merge in W3.
Cost: **spec text only in W3; a merge is ~1 day and is NOT recommended this wave.**

**F-KGS-7 · NEVER-LATER · (§N.4)** — `target_floor` NULL, `expected_volume_formula` /
`expected_volume_inputs` NULL. For a service that writes zero rows by contract, the honest fix is an
explicit declaration, not a number: `expected_volume_formula = 'rows = 0 (service asset; output is a
response, not rows)'` with `target_floor` NULL. Bundle into F-KGS-4's migration; **no standalone
work**.

**Route recommendation (W2 input):** `changed` — the asset cannot honestly take the `probe` route
until F-KGS-1, F-KGS-2 and F-KGS-3 land; two of the three are real code defects and the third is a
check that has never been green. Combined cost of the gating three: **~1.5 h of edits plus test
work.** **Do NOT nominate this asset as the E-gate canary until they land.**

---

## ka_muhurta_seva

**One-line identity:** Deterministic panchāṅga / muhūrta scoring service — wraps `panchang_engine` +
`muhurat.finder` with a hard "location is mandatory" contract and a live Tāra-Bala native overlay.

**Temporal question (D-TIME):** *"How auspicious is this specific calendar day, at this specific
place, for this specific class of undertaking?"*

### 1. Instrument fit
Serves **D-TIME** (calendar-grain quality) and **D-SERVICE** (a real, callable scoring primitive).
Its self-test is the strongest in the batch: **five FORENSIC anchors verified live** (tithi 3, vara 1,
nakshatra 25, yoga 20, karana 5 — all recorded PASS in `selftest_detail`), plus a live Tāra-Bala
check and a knockout check. This is the right instrument and it works.

### 2. Dependencies (declared vs real)
- **Declared:** `{ka_graha_sancara}` — **declared but NOT read.** `services/ka_muhurta_seva/`
  imports `panchang_engine`, `panchang_engine.types`, `panchang_engine.tara_bala`, and
  `muhurat.finder`. It imports nothing from `services/ka_graha_sancara/`. The package's own
  `__init__.py:27` says *"Depends on: ka_graha_sancara (planned)"*.
- **Undeclared real reads (hidden edges):** `bg_panchanga` (the `panchanga_instant` /
  `compute_panchang` engine — the L0 asset that actually carries a populated `health_probe` with the
  same five FORENSIC anchors this writer re-asserts), `muhurat.finder` / `EVENTS_MVP` /
  `panchang_engine.shastra_tables`, and transitively `bg_ephemeris_engine` (swisseph).
- **Consequence for the E-gate:** the single edge that makes this asset look blocked behind an
  unhealthy `ka_graha_sancara` is **fictional**. Repointing it at `bg_panchanga` is a registry-truth
  correction, not a gate weakening.

### 3. Leverage / NULL check
**This is the batch's cleanest measured leverage failure.** The service's only production consumption
is `_c_panchanga_quality()` (`services/ka_sangam/engine.py:457–474`), which calls
`muhurta_service.score(peak_date, native_location, event='general')`. `'general'` is **not** in
`EVENTS_MVP` (`vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation,
upaya_ritual, sadhana_initiation`); `score_muhurat` raises `ValueError` on line 161–162; the
`except Exception` logs at `debug` and returns `0.0`.

Measured on the native's chart (`kala_convergence`, `mode='A'`, n = **1128**):

| current | zero rows | max value |
|---|---|---|
| `c_panchanga_quality` | **1128 / 1128 (100.0%)** | **0.0** |

The `panchanga_quality` term of every convergence score the system has ever computed for this native
is dead, and the writer's own `constituent_factors` faithfully records the zero — so the evidence has
been sitting in the data the whole time. **A working service is producing nothing because of a
one-word vocabulary mismatch at the call site.**

Second, smaller leverage failure at a different consumer: `ka_vighnakara`'s
`_check_panchanga_obstruction()` imports `KaMuhurtaSevaService`, instantiates it, and then **never
calls any of its methods** — it calls `panchang_engine.compute_panchang` directly and uses the
service instance purely as a truthiness flag. Worse, the emitted provenance is
`'source': 'panchang_engine' if muhurta_service else 'day_mod_proxy'`: if `compute_panchang` raises,
`tithi` silently falls back to `(peak_date.day % 15) or 15` **while the row still claims
`source='panchang_engine'`**. That is a provenance label with no detector behind it (§N.7 item 4 /
§N.8).

### 4. Grounding tier
Mixed and mostly honest. The panchāṅga computation itself is `pratyaksa` (instrument output). The
event-class quality tables and the Rikta-tithi rule are `sruti`-adjacent — the code carries real
citations (*Muhurta-Chintamani §Tithi*; *MC §Rahu Kalam + §DurMuhurta* for the compound knockout).
The per-event **weights** are `yukti` (YAML-configured, principle-derived) and should be labelled as
such; they are currently unlabelled. Recommend: `sruti` for the quality tables with their existing
citations, `yukti` for the weights, `pratyaksa` for the computed anga state.

### 5. Temporal identity + arbitration
Overlapping engines: (i) this service; (ii) `ph_muhurta` / `muhurta_finder` at L4, which calls
`score_muhurat()` **directly** for its `panchanga_quality` sub-score — the MCP descriptor for
`call_muhurta_score` says so explicitly; (iii) `scripts/panchanga_daily_writer.py`; (iv)
`ga_panchanga` at L1; (v) `bg_panchanga` at L0. **Five surfaces, one primitive
(`score_muhurat`/`compute_panchang`).** This is the healthiest overlap in the batch because all five
converge on the same primitive rather than reimplementing it — the repo enforces that
(`tests/test_ph_wave4.py` asserts `ph_muhurta`'s engine must **not** contain panchāṅga math). For the
Temporal Concordance Contract: **`score_muhurat`/`compute_panchang` is the single arbiter; every
caller is a wrapper and none may re-derive.** The one thing the contract must add is a rule that
callers pass a **valid `EVENTS_MVP` key** — the absence of such a rule is F-KMS-1.

### 6. Service
- **Serving capability:** `marsys://tool/L3/call_muhurta_score` → sidecar
  `/api/compute/muhurta_score` (`routers/muhurta_score.py`, which genuinely wraps
  `score_muhurat()`). **A real, correctly-wired consumer** — the only one of the four whose serving
  path actually reaches the asset's own primitive.
- **`provides_apis`: NULL** despite a clean published surface (`KaMuhurtaSevaService.score`,
  `.find_windows`, and the module-level `score` / `find_windows`).
- **Density (§N.6): not declared.** No `density_contract`; the descriptor does correctly enumerate
  the 8-value `event_class` enum and states the Lahiri-only limitation, which is honest.
- **Drill to L1 in ≤2 hops:** `grounds_to: { l1_fact_ids: false }`. The score's inputs (tithi,
  nakshatra, vara, yoga) are returned in the response, so a caller can re-derive; no fact_id chain.
  Acceptable for a global, chart-agnostic service.

### 7. Measured cost
- `estimated_seconds = 1`. Real evidence: `last_selftest_at = 2026-08-02 13:50:52.061909+00` →
  `asset_throughput.last_built_at = 2026-08-02 13:50:52.126596+00` → **~65 ms** between the health
  write and the throughput write. Caveat: this measures the tail of the run, not the full writer
  duration (no start timestamp is recorded); the true build cost is **unmeasured but bounded above by
  ~0.12 s**, since `ka_graha_sancara` and `ka_muhurta_seva` both completed inside the same 0.12-s wall
  window in that run.
- `last_invoked_at`: **NULL**. Serve cost: **unmeasured**.

### 8. Findings

**F-KMS-1 · MUST · (§N.8; D-TIME; §N.7 item 6 "an honest null beats an invented judgment")** —
`_c_panchanga_quality` passes `event='general'`, which `EVENTS_MVP` does not contain; the resulting
`ValueError` is swallowed and `0.0` returned, measured in **1128/1128 (100.0%)** Mode-A convergence
rows. `0.0` is not "no panchāṅga support" — it is "the call failed", and the two are being conflated.
Fix: pass a real `EVENTS_MVP` key (or add an explicit baseline event class to `EVENTS_MVP` with its
own weight table), **and** stop returning a scoring-scale value on exception — return `None` and
record the abstention, so a dead current can never again masquerade as a scored zero. Cost: **~10
lines in `services/ka_sangam/engine.py` + the composite's None-handling; ~1 h. Adding a new event
class with a real weight table is a further ~half-day and needs a classical basis — recommend the
cheap fix now, the new class as a separate NOW item.** Note: this fix changes convergence scores, so
it needs a `ka_sangam` rebuild to take effect.

**F-KMS-2 · MUST · (rubric 2; C12 dependency-assert; unblocks the E-gate)** — `depends_on =
{ka_graha_sancara}` is declared-but-unread; the real edge is `bg_panchanga` (plus `bg_ephemeris_engine`
transitively). Correct the registry edge. This is the **cheapest and highest-value item in the batch**:
it makes the registry true and, as a side effect, removes the fictional block on
`ka_muhurta_seva → ka_sangam → the artifact spine` without touching any gate. Cost: **1 migration
line, ~15 min.** Requires W2 to confirm the campaign accepts a registry edge correction as
in-scope for L3.

**F-KMS-3 · NOW · (§N.7 item 4 / §N.8 — a flag needs a real detector or it is null)** —
`ka_vighnakara._check_panchanga_obstruction` labels `source='panchang_engine'` based on whether a
service object exists, not on whether the panchāṅga computation succeeded; on failure it emits a
`day % 15` proxy tithi under the `panchang_engine` label. Fix: derive `source` from which branch
actually produced `tithi`. Cost: **~3 lines, ~10 min.** (In L3's write-set — `ka_vighnakara` is an L3
writer.)

**F-KMS-4 · NOW · (§N.7 item 3 — no wrapper-local constant may shadow an L1-computed value)** —
`services/ka_muhurta_seva/service.py:31–34` defines `NATIVE_BIRTH_NAKSHATRA_ID=25`,
`NATIVE_BIRTH_LAGNA_SIGN_ID=1`, `NATIVE_MOON_SIGN_ID=11`, and
`NATIVE_ACTIVE_DASHA_LORD="Jupiter"  # current period; update as dasha changes`. **All four are dead
— grep finds no reader anywhere outside their own definition** — and the last one is **factually
wrong**: measured, the native's current Vimśottarī mahādaśā lord is **Mercury** (2010-08-18 →
2027-08-18, `chart_dashas`, `lahiri_chitrapaksha`). This is the identical shape to the
`_BIRTH_LAT`/`_BIRTH_LON` "latent contamination trap" already deleted from `ka_graha_sancara` in
commit `c776dd81f`. Apply the same remedy: delete. Cost: **4 lines removed, ~5 min.**

**F-KMS-5 · NOW · (C12 registry-health, §N.6 item 4)** — `health_probe` NULL, `provides_apis` NULL,
`integrity_check_sql` NULL, `expected_volume_formula` NULL, `target_floor` NULL,
`rebuild_on_probe_fail` false. The writer's five FORENSIC assertions are **already** the content of a
real probe and `bg_panchanga`'s populated `panchanga_engine` `health_probe` is the exact template
(same instant, same five expected values). Cost: **1 migration, ~1 h**, mostly transcription.

**F-KMS-6 · NEVER-LATER** — `call_muhurta_score` declares no `density_contract`. Single-instant scalar
response with no pagination; the §N.6 density concern is genuinely thin here. Log with reason: *a
one-row scalar surface has no density layers to signal.*

**Route recommendation (W2 input):** `probe` — the writer's self-test is real, runs against real
FORENSIC anchors, raises correctly on failure, and is currently and honestly green. Route it as a
probe **once F-KMS-2 corrects the fictional `ka_graha_sancara` edge**; the leverage fix (F-KMS-1) is a
`ka_sangam` change and does not gate this asset's own probe.

---

## ka_dasha_kala

**One-line identity:** Daśā-eligibility service — a lazy-pruning tree-walk over `chart_dashas` to
level-4 (Sūkṣma) across 7 systems, returning banded eligibility scores plus a cross-system agreement
count.

**Temporal question (D-TIME):** *"Across all daśā systems, which time windows is this chart
constitutionally eligible for a given signature — and how many independent systems agree?"*

### 1. Instrument fit
Serves **D-TIME** (the chart's own internal clock, as opposed to the sky's clock) and
**D-SYNTHESIS P4** via cross-system agreement. It is the right instrument, and it is the one L3
service whose engine is genuinely consumed in production by another writer (`ka_sangam`). Its
three-tier soft prior (EXACT 0.85 / RELATED 0.50 / NEUTRAL 0.20) is a good design that is currently
being used at ~1/3 of its expressive range.

### 2. Dependencies (declared vs real)
- **Declared:** `{ga_dashas}` (`target_table = chart_dashas`) — **real and read.** `tree_walk.py`
  and `confirm_systems_present()` both query `chart_dashas`. Correct, and the only declared edge.
- **Undeclared:** none of consequence. The service is DB-only and touches no other engine.
- **Registry description is stale/false in one respect:** `english_description` says *"Nārāyaṇa
  absent."* Measured: `chart_dashas` holds **266 `narayana` rows** for the native at
  `lahiri_chitrapaksha` (max `level_n` = 2). The service's own `_EXPECTED_SYSTEMS` frozenset excludes
  `narayana`, and `selftest_detail.systems_found` (2026-08-08) **already lists it**. So the registry
  prose contradicts the asset's own most recent self-test output.

### 3. Leverage / NULL check
Measured on the native's chart, `kala_convergence` `mode='A'` (n = **1128**) — these are the rows
where `ka_sangam` actually consults this service:

| field | measurement |
|---|---|
| `dasha_score` = 0.5 (the **static fallback**, not the service) | **1079 / 1128 = 95.7%** |
| distinct `dasha_score` values chart-wide | **2** (`0.5`, `0.85`) |
| `c_cross_dasha_agreement` = 0.0 | **1079 / 1128 = 95.7%** (max **0.1429**) |

So the service's graded eligibility prior reaches the convergence composite in **4.3%** of Mode-A
rows, and when it does it contributes exactly one value (`0.85` = the EXACT band). Two independent
causes, both at the call site, not in the service:
- `mode_a_search` passes **`related_lords=set()`**, which makes the RELATED band (`0.50`)
  **unreachable by construction** and, combined with the default `min_band=RELATED`, prunes every
  MD whose lord is not literally in `target_lords`. A three-tier prior is being used as a two-tier
  one.
- `_dasha_score_for_date()` returns the static `0.5` whenever no eligible window brackets the
  peak date, so a legitimately narrow eligibility result is indistinguishable from "the service was
  never asked". (Not an empty-lords problem: measured, **40,757 / 50,104 = 81.3%** of
  `kala_activation_predicates` rows for this chart DO carry non-empty `constituent_lords`.)

Serving-plane leverage failure, separately measured: `call_dasha_eligibility` defaults
`ayanamsha_id` to the string literal `'lahiri'`, which does not exist in `chart_dashas`. Measured for
the native over the tool's own default 3-year window: **`'lahiri'` → 0 rows; `'lahiri_chitrapaksha'`
→ 3,401 rows.** Every default-argument call of this tool has been returning an empty, non-error
envelope. Note `DEFAULT_AYANAMSHA = 'lahiri_chitrapaksha'` is imported in the same file and used by
the sibling `call_priority_ranking` — this one handler simply does not use it.

`selftest_detail.high_agreement_count = 0` is, by contrast, an **honest zero, not a broken
detector** — verified: chart-wide, **106 / 1,537** level-2 window boundaries are shared by ≥2
systems, so the detector demonstrably can produce a non-zero; the self-test's narrow
(Saturn/Rahu, 2010–2030, max_level=2) slice genuinely contains none.

### 4. Grounding tier
The daśā intervals themselves are `pratyaksa` (arithmetic over L1 `chart_dashas`, inheriting L1's
values per §N.5 — the service reads, never re-derives, which is correct). The **eligibility banding**
(EXACT/RELATED/NEUTRAL and the 0.85/0.50/0.20 scores) is `yukti` — principle-derived, with no verse
behind the specific numbers, and the module docstring is admirably honest about it (*"deliberately
soft/probabilistic so that downstream consumers can layer their own weights"*). It should be
**labelled `yukti` explicitly**. The cross-system agreement count is `pratyaksa`.

### 5. Temporal identity + arbitration
Overlapping engines: (i) this service; (ii) the TypeScript `call_dasha_eligibility` handler, which
**reimplements** window selection and cross-system agreement in SQL+TS and never calls this service;
(iii) `services/ph_nimitta/dasha_consensus.py` at L4, which *does* import `KaDashaKalaService`;
(iv) `ka_taranga` and `ka_avadhi`, which read `chart_dashas` directly (their error notes literally say
*"no vimshottari MD rows — run ka_dasha_kala first"*, i.e. they treat the asset as a **producer** it
is not — it writes no rows); (v) L1 `ga_dashas`, the row authority.
**Arbitration rule for the Temporal Concordance Contract:** **L1 `ga_dashas`/`chart_dashas` is the
row authority; `ka_dasha_kala` is the sole authority for *eligibility banding and cross-system
agreement*; no other surface may compute agreement.** The TS handler currently violates that, with a
different agreement definition (see F-KDK-4).
**A caution the contract must record:** exact `(start_date, end_date)` equality on **DATE-truncated**
boundaries is a weak proxy for genuine convergence. Measured chart-wide: of 11,163 windows with ≥2
agreeing systems, **10,136 (90.8%)** are at `level_n=4` with a mean span of **4.10 days** — i.e. the
"agreement" signal is dominated by short-window calendar-day collisions, not by systems genuinely
converging.

### 6. Service
- **Serving capability:** `marsys://tool/L3/call_dasha_eligibility` (MCP `call_dasha_eligibility`).
  **A real consumer of the TABLE, not of this asset** — the handler runs its own
  `SELECT … FROM chart_dashas … LIMIT 400` and its own agreement grouping in TypeScript.
- **Real in-process consumers of the service class:** `ka_sangam` (L3, §3) and
  `ph_nimitta/dasha_consensus.py` (L4). Genuinely not shelf inventory.
- **What a downstream writer gets, precisely:** `KaDashaKalaService.query(chart_id, ayanamsha_id,
  target_lords, related_lords, date_start, date_end, max_level=1..4, min_band, prana_grain,
  systems)` → `KaDashaKalaResult` carrying `windows: list[EligibleWindow]`, each with
  `dasha_row_id, system_id, level_n, lord_graha, start_date, end_date, ancestor_lords,
  eligibility_band, eligibility_score, cross_dasha_agreement(count, systems_agreeing),
  kp_sublevel, kp_sub_lord, is_prana_computed`, plus `kp_windows`, `total_windows`,
  `high_agreement_count`, `systems_queried`. `ka_sangam` consumes exactly **two** of those fields
  (`eligibility_score` via date bracketing, and the agreement count) and calls with `max_level=3`.
  Level-5 (Prāṇa) is computed in memory only and never persisted — correctly.
- **`provides_apis`: NULL** despite that clean surface. **Density: not declared.**
- **Drill to L1 in ≤2 hops:** yes — `grounds_to: { l1_fact_ids: true }`, and every window carries
  `dasha_row_id` → `chart_dashas` → L1. This is the best drill path of the four.

### 7. Measured cost
- `estimated_seconds = 2`. Real evidence: `last_selftest_at = 2026-08-08 00:28:56.606583+00` →
  `asset_throughput.last_built_at = 2026-08-08 00:28:57.200368+00` → **~594 ms** for a self-test that
  walks 7 systems to `max_level=2` over a 20-year window and returned 57 windows. Three chart rows
  exist in `asset_throughput` (native 2026-08-08, Abhinandan 2026-08-06, `cb73cd3d…` 2026-07-27), all
  `lit`, all `rows_written=0` — correct for a service.
- Serve cost: **unmeasured** for the service class. For the bypassing TS handler, the query is a
  single index-backed range scan with `LIMIT 400` — **unmeasured**, but structurally cheap.
- `last_invoked_at`: **NULL**.

### 8. Findings

**F-KDK-1 · MUST · (rubric 3, the NULL check; D-SERVICE)** — `call_dasha_eligibility` hard-codes
`ayanamsha_id` default `'lahiri'`; `chart_dashas` has no such value. Measured: default call → **0
rows**; corrected → **3,401 rows**. The handler returns `is_error: false` with an empty
`dasha_windows` array, so the failure is invisible to the caller. Fix: use the `DEFAULT_AYANAMSHA`
constant already imported in the same file, and add an `empty_reason` so a genuinely empty window is
distinguishable from a vocabulary miss. Cost: **1 line + ~10 lines of empty-reason handling, ~30 min**
(TypeScript — confirm against L3's write-set).

**F-KDK-2 · MUST · (rubric 3; §N.7 item 6)** — `mode_a_search` passes `related_lords=set()` and relies
on `_dasha_score_for_date`'s static-`0.5` fallback, so the service's graded prior reaches the
composite in **4.3%** of Mode-A rows with **2 distinct values**. Two sub-fixes: (a) populate
`related_lords` from the predicate's dispositor/house-lord set so the RELATED band becomes reachable;
(b) distinguish "no eligible window brackets this date" from "the service was not consulted" —
the former is a real, informative low score, the latter is an abstention and must not be silently
rendered as 0.5. Cost: **(b) ~10 lines, ~30 min; (a) needs the predicate to carry related lords —
scope it in W2, likely ~half a day and possibly an L2 hand-off if the field does not exist on
`kala_activation_predicates`.** Both require a `ka_sangam` rebuild to take effect.

**F-KDK-3 · MUST · (§N.8, same class as F-KGS-3)** — `services/ka_dasha_kala/writer.py` returns a
`WriterResult` on self-test failure (with `service_health='degraded'`) instead of raising, so a failed
self-test still marks the asset `lit`. Fix: adopt `ka_muhurta_seva`'s raise pattern. Cost: **~6 lines,
~10 min.** Also note the health verdict vocabulary is inconsistent across the four writers
(`degraded` here and in `ka_tulana`, `unhealthy` in the other two) — worth normalising in the same
edit.

**F-KDK-4 · NOW · (D-TIME concordance; §N.6)** — The served handler reimplements cross-system
agreement in TypeScript with a definition that differs from the service's, and neither surface warns
that DATE-truncated boundary equality at level 4 is dominated by calendar-day collisions
(**90.8%** of all agreeing windows, mean span **4.10 days**). Fix: either route the tool through the
service, or — cheaper and recommended for this wave — have both surfaces emit the agreement
**with its level and span**, so a caller can never read a level-4 4-day collision as multi-system
convergence. Cost: **~1 h** for the disclosure; routing through the service is ~1 day and not
recommended this wave.

**F-KDK-5 · NOW · (B.8 versioning discipline / registry truth)** — `english_description` asserts
*"Nārāyaṇa absent"*; measured, 266 `narayana` rows exist and the asset's own `selftest_detail`
already lists the system as found. Correct the description; decide explicitly whether `narayana`
joins `_EXPECTED_SYSTEMS` (it is level-2-only, so a naive addition would change the self-test's
meaning — state the reason either way rather than leaving the contradiction). Cost: **~30 min.**

**F-KDK-6 · NOW · (C12 registry-health)** — `health_probe` NULL, `provides_apis` NULL,
`integrity_check_sql` NULL, `expected_volume_formula` NULL, `target_floor` = 0 (uninformative for a
zero-row service). A **real** invariant is available here and is NOT a `count(*)=N` pin: *for every
`(chart_id, ayanamsha_id, system_id, level_n, parent_row_id)` sibling group in `chart_dashas`, the
child intervals tile the parent's interval with no gap and no overlap, and every `start_date <
end_date`.* That is an ordering-contiguity/tiling invariant of exactly the kind C12 asks for, and the
service's own self-test already asserts the weaker half of it. Cost: **~2 h** to author and validate
the SQL (note: the invariant is about `chart_dashas`, an L1 table — W2 should confirm whether it
belongs on this asset's row or hands off to L1).

**F-KDK-7 · NEVER-LATER** — `ka_taranga` and `ka_avadhi` emit *"run ka_dasha_kala first"* in their
skip notes, implying this service produces rows. It produces none; the producer is `ga_dashas`. A
misleading operator message, not a correctness defect. Log with reason; fold into any future touch of
those writers.

**Route recommendation (W2 input):** `probe` — the self-test is real, runs against the canonical
chart's actual data, and would correctly fail; the asset itself is sound. F-KDK-3 (raise-on-failure)
should land with it so the probe verdict can actually gate. The leverage items (F-KDK-1, F-KDK-2) are
consumer-side and do not block this asset's own route.

---

## ka_tulana

**One-line identity:** Serve-time cross-pattern prioritization engine — ranks windows across patterns
and life-domains by the ratified I-11 composite, with head-to-head `compare(A,B)` and a multi-domain
attention map.

**Temporal question (D-TIME):** *"Of all the windows now open across every pattern and every life
domain, which one deserves attention first — and if two compete, which wins and why?"*

### 1. Instrument fit
Serves **D-SALIENCE P5** primarily (it is the layer's only attention-allocation engine) and
**D-SYNTHESIS P4** (cross-domain comparison). It is the right instrument for a question the layer
genuinely has, and its I-11 weights are natively ratified (convergence 0.40 / rarity 0.25 /
confidence 0.20 / proximity 0.15, sign-off 2026-06-21). **The instrument is correct and unused.**

### 2. Dependencies (declared vs real)
- **Declared:** `{ka_sangam, ka_vighnakara, ka_kala_darshana}`.
- **Real:** **none of the three.** `services/ka_tulana/ranker.py` contains **no SQL, no cursor, no
  connection** — verified by grep. It is a pure in-memory function over caller-supplied
  `WindowInput` objects. All three declared edges are **declared-but-unread**.
- **Actual real import:** `brahmagyan.domain_vocabulary.CANONICAL_DOMAINS` (the L0 13-domain SSoT) —
  **undeclared**. This is a good, deliberate edge (it replaced a local 7-domain literal in G13/PA-4),
  and it deserves to be in `depends_on`.
- **Reverse edges: ZERO.** No asset in `asset_registry` declares a dependency on `ka_tulana`, and no
  production Python imports it. It is a terminal leaf that nothing consumes.

### 3. Leverage / NULL check
**The highest-leverage single item in the batch, and it is measured to a line count.** The ranker's
`WindowInput` dataclass is a field-for-field match to `kala_convergence` plus one column of
`kala_darshana`:

| `WindowInput` field | source column | native fill (n = 14,868) |
|---|---|---|
| `window_id` | `kala_convergence.convergence_id` | 100% |
| `mode` | `kala_convergence.mode` | **14,868 / 14,868 (100%)** |
| `peak_date` | `kala_convergence.peak_date` | **14,868 (100%)** |
| `window_start` / `window_end` | same names | 100% |
| `convergence_score` | `kala_convergence.convergence_score` | **14,868 (100%)** |
| `confidence_label` | `kala_convergence.confidence_label` | **14,868 (100%)** |
| `rarity_years` | `kala_convergence.rarity_years` | **14,868 (100%)** |
| `signal_id`, `source_citation` | same names | 100% |
| `domains` | `kala_convergence.domain` | 14,390 / 14,868 = **96.8%** |
| `net_label` | `kala_darshana.net_label` | **750 / 750 (100%)** |

Every input the ranker was designed for exists, is populated, and is sitting in two tables the ranker
has never read. The **adapter is the only missing piece**, and it is a `SELECT` with a `LEFT JOIN`.

Meanwhile the served surface (`call_priority_ranking`) computes an **entirely different** ranking:
`bodha_msr_signals.computed_salience × kala_activation.orb_strength` over a
`bodha_msr_signals ⨝ kala_activation` join. It uses **none** of convergence, rarity, proximity, or
confidence; it offers **no** `compare(A,B)`; it produces **no** attention map. Measured: that join
yields **2,941** candidate rows for the native over the tool's default 90-day window, so the served
tool is not empty — it is simply answering a different question under this asset's name.

`target_floor = 0` is **honest but uninformative**: the service truly writes zero rows, so the floor
is trivially satisfied and can never fail. It is not a floor in the §N.4 sense (an achieved count
after a build); it is a tautology occupying a field that C12 wants to carry information.

### 4. Grounding tier
`pratyaksa` for the composite arithmetic and the rank ordering — instrument-emergent, no classical
claim, and an honest `pratyaksa` here is success. The **I-11 weights themselves** are `yukti` at best
and arguably a fourth thing the tier vocabulary does not cover: **native-ratified policy**. They are
not derived from a classical principle; they were chosen and signed off. Recommend labelling them
explicitly as ratified policy with the 2026-06-21 sign-off cited, rather than letting a `yukti` label
imply a derivation that does not exist. The `compare()` verdicts (`proceed` / `defer` /
`proceed_with_mitigation`) are interpretive and would need a tier the moment they are served.

### 5. Temporal identity + arbitration
Overlapping engines answering "what deserves attention now": (i) this ranker (I-11 over
`kala_convergence`/`kala_darshana`); (ii) the TS `call_priority_ranking` handler (salience ×
orb_strength over `bodha_msr_signals`/`kala_activation`); (iii) `kala_priority_get` /
`kala_priority_ranking_get` in the MCP roster; (iv) `ka_kala_darshana`'s own `effective_score` /
`net_label`, which already ranks within a pattern.
**Two engines currently answer the same question with different formulas over different tables under
the same asset name.** For the Temporal Concordance Contract this is the clearest arbitration item in
the batch: **`ka_tulana`'s I-11 composite is the declared, ratified authority for cross-pattern
priority; the salience×orb formula is a distinct, narrower question (which MSR signals are active
now) and must be named as such.** Until that is settled, a caller cannot know which "priority" they
received.

### 6. Service
- **Serving capability:** `marsys://tool/L3/call_priority_ranking` (MCP `call_priority_ranking`).
  It carries genuinely good §N.6/§N.7 discipline — `excluded_internal_markers` with
  `pre_exclusion_rank` disclosure, `neutral_dignity_downranked` flags,
  `headline_label_mapped=false` pass-through, `catalog_only_rows_in_page` — all present and correct.
  **But it does not call `ka_tulana`.**
- **`provides_apis`: NULL** despite a rich published surface (`rank_windows`, `compare`,
  `attention_map`, `WindowInput`, `RankedWindow`, `CompareVerdict`, `FactorBreakdown`).
  `compare()` and `attention_map()` — the two capabilities the registry's `english_description`
  advertises most prominently — are **unreachable from any served tool.**
- **Density (§N.6): no `density_contract` declared**, though the handler's flag/disclosure discipline
  is otherwise exemplary.
- **Drill to L1 in ≤2 hops:** the served surface yes (`signal_id_refs`, `grounds_to.l1_fact_ids:
  true`). The ranker itself carries `signal_id` and `source_citation` on every `WindowInput`, so it
  would also drill cleanly if it were ever wired.

### 7. Measured cost
- `estimated_seconds = 1`. Real evidence: `last_selftest_at = 2026-08-13 01:15:55.114916+00` →
  `asset_throughput.last_built_at = 2026-08-13 01:15:55.289687+00` → **~175 ms** — but that is the
  cost of ranking **two synthetic objects**, not of any real workload. **Real build cost:
  unmeasured** (there is no real workload to measure).
- **Serve cost, MEASURED:** `EXPLAIN (ANALYZE)` of the core join behind `call_priority_ranking` for
  the native over the default 90-day window — **Execution Time 1934.906 ms, Planning Time 20.189 ms**
  (nested loop, 10,003 index-scan loops over `kala_activation`). That is **before** the real query's
  two window functions and its four per-row `unnest(...) WITH ORDINALITY` marker subqueries. **~2 s
  is a high serve cost for a top-20 list** and is worth flagging on its own.
- `asset_throughput` shows `state='stale'` for the native (2026-08-13) and `cb73cd3d…` (2026-07-27),
  `lit` for Abhinandan — while `service_health='healthy'`. A third demonstration that the two signals
  are unrelated.
- `last_invoked_at`: **NULL**.

### 8. Findings

**F-KTU-1 · NOW (recommend elevating to MUST if W2 rules D-SALIENCE in scope) · (rubric 3, the
NULL check; D-SALIENCE P5)** — A complete, natively-ratified I-11 ranker exists and reads nothing;
its exact input tables hold **14,868** and **750** rows for the native with **100% fill** on every
required field. The missing piece is a `kala_convergence LEFT JOIN kala_darshana` → `WindowInput`
adapter, ~30 lines. Cost: **adapter ~2 h; wiring `call_priority_ranking` (or a new
`call_cross_pattern_priority`) to it ~half a day, plus the arbitration decision in F-KTU-4.**
Recommend W2 decide the arbitration first and the wiring second.

**F-KTU-2 · MUST · (§N.8, same class as F-KGS-3/F-KDK-3)** — `services/ka_tulana/writer.py` returns
instead of raising on self-test failure, so `service_health='degraded'` cannot demote the asset.
Cost: **~6 lines, ~10 min.**

**F-KTU-3 · MUST · (§N.8 — "what code path would have to run, and fail, for this signal to correctly
read false?")** — The self-test constructs **two synthetic `WindowInput`s** in which **all four**
I-11 factors favour A (convergence 0.9 vs 0.4, rarity 30.0 vs 2.0, confidence high vs moderate,
identical peak dates) and asserts A outranks B. No weighting error, no normalisation error, no
sign error, and no data problem can make that assertion fail; it touches no chart, no table, and no
connection. `service_health='healthy'` on this asset therefore asserts nothing about the service.
Fix: a self-test that reads real `kala_convergence` rows for the canonical chart and asserts
properties that can actually break — e.g. weights sum to 1.0; a rarity-dominant window outranks a
convergence-dominant one **only** when the weighted difference says so; `rank` is a total order with
no ties; every returned `window_id` resolves to a real `convergence_id`. Cost: **~2 h**, and it
depends on F-KTU-1's adapter (build them together).

**F-KTU-4 · NOW · (D-TIME concordance; D-SERVICE)** — Two engines answer "what deserves attention
now" with different formulas over different tables, one of them under this asset's name in its own
tool description. W2 must rule which is authoritative for *cross-pattern priority* and rename or
re-describe the other. Cost: **decision + description edits, ~1 h**; any code consequence follows
from F-KTU-1.

**F-KTU-5 · NOW · (rubric 2; C12)** — All three declared edges (`ka_sangam`, `ka_vighnakara`,
`ka_kala_darshana`) are unread, and the one real edge (`brahmagyan.domain_vocabulary`) is undeclared.
Note the declared three become **true** the moment F-KTU-1's adapter lands (it reads
`kala_convergence` ← `ka_sangam` and `kala_darshana` ← `ka_kala_darshana`); `ka_vighnakara` would
still be unread unless the adapter also pulls obstruction data. Recommend correcting the edge set
**after** F-KTU-1 is decided, so the registry is corrected once. Cost: **1 migration, ~15 min.**

**F-KTU-6 · NOW · (measured serve cost)** — The served `call_priority_ranking` core join measures
**1.93 s execution + 20 ms planning** for the native's default 90-day window, before the two window
functions and four per-row marker subqueries the production SQL adds. Recommend W2 log a serve-cost
investigation (the plan shows a nested loop with 10,003 index-scan loops and `Rows Removed by Filter`
on the date predicate — an index covering `(chart_id, ayanamsha_id, activation_start,
activation_end)` is the obvious hypothesis, **untested**). Cost: **investigation ~1 h; index change
~30 min if confirmed. Do not add an index on an untested hypothesis.**

**F-KTU-7 · NEVER-LATER · (§N.4 / C12)** — `target_floor = 0` is tautologically satisfied for a
zero-row service and carries no information; `expected_volume_formula` / `expected_volume_inputs`
NULL. Honest fix is a declaration, not a number: `expected_volume_formula = 'rows = 0 (serve-time
service; output is a ranked response, not rows)'`, `target_floor` NULL. Same treatment for
`ka_dasha_kala`'s `target_floor = 0`. Bundle with F-KTU-5's migration; **no standalone work.**

**Route recommendation (W2 input):** `changed` — the `probe` route would certify a self-test that
cannot fail (F-KTU-3), which is the §N.8 line this campaign exists to hold. The asset needs a real
detector before a probe of it means anything; F-KTU-2 and F-KTU-3 are the minimum, and they are
cheapest built alongside F-KTU-1's adapter. If W2 rules D-SALIENCE out of scope for this wave, the
honest alternative route is **not** `probe` but a deferral with the reason recorded.

---

## Cross-asset registry-health summary (measured 2026-09-05)

| field | ka_graha_sancara | ka_muhurta_seva | ka_dasha_kala | ka_tulana |
|---|---|---|---|---|
| `asset_kind` / `asset_type` | service | service | service | service |
| `service_health` | **unhealthy** | healthy | healthy | healthy |
| `asset_throughput.state` | **lit** | lit | lit | **stale** (native) |
| `last_selftest_at` | 2026-08-02 | 2026-08-02 | 2026-08-08 | 2026-08-13 |
| `last_invoked_at` | NULL | NULL | NULL | NULL |
| `health_probe` | NULL | NULL | NULL | NULL |
| `provides_apis` | NULL | NULL | NULL | NULL |
| `count_sql` | NULL | NULL | NULL | NULL |
| `integrity_check_sql` | NULL | NULL | NULL | NULL |
| `expected_volume_formula` / `_inputs` | NULL / NULL | NULL / NULL | NULL / NULL | NULL / NULL |
| `target_floor` | NULL | NULL | **0** | **0** |
| `rebuild_on_probe_fail` | false | false | false | false |
| `catalog_status` | DRAFT | DRAFT | DRAFT | DRAFT |
| declared deps all real? | yes (1/1) | **no (0/1)** | yes (1/1) | **no (0/3)** |
| serving tool calls the asset? | **no** (own swisseph) | **yes** | **no** (own SQL) | **no** (own SQL) |
| writer raises on failure? | **no** | **yes** | **no** | **no** |

Notes on the shared items:
- **`count_sql` NULL is correct** for all four (no target table; the L1 cockpit trap does not apply —
  there are no rows to count). It should stay NULL, with `expected_volume_formula` carrying the
  "rows = 0 by contract" declaration instead.
- **`rebuild_on_probe_fail = false` on all four** means the orchestrator's verify-then-regenerate
  primitive never engages for L3 services; combined with `health_probe = NULL`, the C12 probe path is
  entirely inert at this layer. Turning it on is only meaningful **after** each asset has a real
  `health_probe` (F-KGS-4, F-KMS-5, F-KDK-6).
- **Health-verdict vocabulary is inconsistent**: `unhealthy` (ka_graha_sancara, ka_muhurta_seva) vs
  `degraded` (ka_dasha_kala, ka_tulana), against `service_probes.py`'s own
  `GREEN`/`degraded`/`down`. Three vocabularies for one concept. Normalise in W3.

## Hard-floor compliance

Read-only throughout. No `INSERT`/`UPDATE`/`DELETE`/DDL issued; every DB statement was a `SELECT` or
`EXPLAIN (ANALYZE)` on a `SELECT` via `.l3-tools/q.sh`. No git write commands. No probe was executed.
**No finding in this document proposes weakening a gate, check, or trigger** — F-KMS-2 (correcting a
declared-but-unread dependency edge) makes the registry *truer*, and F-KGS-2 replaces an
unsatisfiable assertion with two satisfiable ones on the paths they actually govern, which is a
check-correction, not a relaxation. **Nothing here touches the `ka_gochara_sweep` v1 corpus or any
snapshots directory.**
