---
artifact: KA_GRAHA_SANCARA_KA_DASHA_KALA_DOSSIER
version: 1.0
status: DRAFT
prepared_on: 2026-09-20
role: Field-contract research dossier for the two L3 Kāla service-type assets (ka_graha_sancara, ka_dasha_kala) targeted for terminal acceptance in the L3 data-plane elevation campaign — read-only research input for a later acceptance-test-building packet.
---

# KA_GRAHA_SANCARA + KA_DASHA_KALA — Field-Contract Dossier v1.0

Scope note: this dossier is read-only research. Every claim below is sourced to an
exact file path (and, where useful, a line anchor) actually read during this pass.
Where the source code did not answer a question the task asked, that gap is stated
explicitly rather than filled in — per this project's own doctrine (CLAUDE.md §I
B.10, §L "Do not... produce generic astrology / fabricate").

---

## 1. `ka_graha_sancara`

### 1.1 Identity / type — CONFIRMED: service, not a writer

Registered writer: `platform/python-sidecar/pipeline/orchestrator/writers/ka_graha_sancara.py`,
`@register("ka_graha_sancara")` → `class KaGrahaSancaraWriter(WriterBase)`. Its own docstring
states plainly: *"This is a SERVICE-KIND asset. The writer does NOT insert domain rows."*
`run(ctx)` always returns `WriterResult(rows_inserted=0, ...)` on success, and — per an
in-code §N.8 fix note — **raises** `RuntimeError` if the self-test is unhealthy, specifically
so the orchestrator's `mark_asset_error` path fires instead of silently promoting the asset
to `'lit'` on a failed self-test (a documented prior defect, fixed in place). Confirmed from
reading the actual `run()`/`_run_selftest()` code, not asserted from a label.

The actual compute engine lives at `platform/python-sidecar/services/ka_graha_sancara/engine.py`
(438 lines) + `services/ka_graha_sancara/__init__.py`, exporting `get_ephemeris()`,
`EphemerisResult`, `GrahaState`. This package is a plain importable Python module, not itself
`@register`-decorated — only the writer shim registers the asset_id with the orchestrator.

### 1.2 Qualified purpose / which L3 value question it improves

Per `services/ka_graha_sancara/__init__.py`'s docstring and `engine.py`'s header comment: this
is "Ephemeris-at-T" — sidereal graha longitude/speed/sign/nakshatra/retrograde state and an
applying/separating helper (`GrahaState.applying_or_separating()`, engine.py:84-126), computed
at an **arbitrary instant** the caller supplies, global/chart-agnostic (no `chart_id` parameter
anywhere in `get_ephemeris()`'s signature).

Of the campaign's stated "value question" families (what is active now/why; nearest-vs-strongest;
mechanism engaged; timing-method agreement/disagreement), this asset's actual code answers
**none of them directly** — it answers a lower-level question: "where is graha X at time T, and
is it approaching or receding from a given longitude?" It is infrastructure other questions
build on (transit search, muhurta scoring) rather than itself producing a "what is active now"
verdict. The applying/separating helper is the one piece of interpretive value beyond a bare
position lookup — it lets a caller determine, e.g., whether a transiting Saturn is closing on
or moving away from a natal degree, which is the raw ingredient a "timing window opening/closing"
question would need.

### 1.3 Exact source/import closure

Read directly from `engine.py`:

- **PATH-A (day-grade, in-range)**: for dates `1900-01-01`..`2150-12-31` with a `db_conn`
  supplied, reads `ephemeris_daily` (columns: `body, tropical_longitude, speed_dps,
  is_retrograde`, filtered `WHERE date = %s AND ayanamsha_id = 'tropical'`) — this is the
  **L0 Brahmagyan** table (`bg_ephemeris_engine` asset, per `routers/ephemeris.py`'s
  `_EPHEMERIS_REGISTRY_GENERATION = "bg_ephemeris_engine@migration-624"`), not an L1 table.
  Tropical longitude is then converted to sidereal via
  `brahmagyan.l0_ephemeris.derive_sidereal(trop_lon, jd, ayanamsha)` — again L0, not L1.
- **PATH-B (live)**: out-of-range dates, `db_conn=None`, or `force_live=True` delegate to
  `platform/scripts/temporal/compute_transits.get_transit_states` (pyswisseph + Moshier),
  which is a pure live computation with **no DB read at all**.

**This asset never reads `chart_facts` or any other L1 table.** It is chart-agnostic by
construction — it computes graha positions for a UTC instant, not for a specific native's
chart. §N.5 ("an L2+/L3 signal never restates an L1 fact as its own truth") is therefore
not directly engaged by this asset's core computation: there is no L1 fact being restated,
because there is no L1 input in the first place.

### 1.4 Field/partition semantics — N/A (not a `ga_dashas`-consuming asset)

Not applicable to `ka_graha_sancara`; this field only meaningfully applies to `ka_dasha_kala`
(see §2.4). No local recompute of an L1 value was found, because no L1 value is read.

### 1.5 Actual input/output contract

Two distinct code paths expose overlapping but **not identical** contracts — this
divergence is itself a finding (see §1.9):

**(a) `services.ka_graha_sancara.engine.get_ephemeris()`** (the actual named service, called
by the writer's self-test and by the health probe):
```
get_ephemeris(dt: datetime, ayanamsha: str = "lahiri", db_conn: Any = None, *,
              force_live: bool = False, _cache: _EphemerisCache | None = None)
    -> EphemerisResult
```
- `dt`: naive datetimes are assumed IST (`Asia/Kolkata`, with a manual UTC+5:30 fallback if
  `zoneinfo` fails) — engine.py:381-391.
- `ayanamsha`: must be one of `SUPPORTED_AYANAMSHAS = {"lahiri", "raman", "kp", "krishnamurti",
  "yukteshwar", "surya_siddhanta"}` (engine.py:64) — **note this vocabulary differs from the
  router's** (§1.9).
- Returns `EphemerisResult(query_dt, ayanamsha, source, grahas: dict[str, GrahaState])` for
  all 9 grahas (`ALL_GRAHAS`, TRUE_NODE Rahu; Ketu = Rahu+180). `source` is one of
  `'bg_ephemeris' | 'swisseph_live'`.

**(b) `POST /api/compute/ephemeris_at_t`** (`platform/python-sidecar/routers/ephemeris.py`,
`compute_router`, the endpoint actually reachable over HTTP and the one the TS consumer calls):
```python
class EphemerisAtTRequest(BaseModel):
    datetime_utc: str              # ISO 8601 UTC instant
    ayanamsha_id: str = "lahiri_chitrapaksha"
```
Returns `{datetime_utc, ayanamsha_id, jd, positions: [PlanetPosition...], service_context}`
where `PlanetPosition = {planet, longitude, sign, deg_in_sign, nakshatra, pada, retrograde,
speed}` for 9 grahas (`PLANETS` list + derived Ketu).

**This router endpoint does NOT call `services.ka_graha_sancara.engine.get_ephemeris()` at
all.** It has its own independent swisseph integration (`_calculate_sidereal_positions`,
`_position_from_lon`, module-level `PLANETS`/`SIGNS`/`NAKSHATRAS` constants) that predates
this endpoint (shared with the natal-chart `compute_natal_positions` handler at the top of
the same file). This is confirmed by reading the full file — `ephemeris_at_t()` never imports
from `services.ka_graha_sancara`.

### 1.6 Bounds and error behavior

From `routers/ephemeris.py::ephemeris_at_t()` (the live consumer path):
- Unrecognized `ayanamsha_id` (not in `_AT_T_AYANAMSHA_MAP = {lahiri_chitrapaksha,
  true_chitra, krishnamurti, raman, surya_siddhanta_classical}`) → **HTTP 422**, loud, with
  an explicit `[EXTERNAL_COMPUTATION_REQUIRED]`-prefixed message (§N doctrine phrasing used
  literally in the error string).
- Invalid `datetime_utc` string → **HTTP 400** (`ValueError` from `datetime.fromisoformat`
  caught and re-raised as HTTPException).
- `datetime_utc` without a timezone offset/`Z` → **HTTP 400**, explicit message.
- No missing-chart case exists for this endpoint — it takes no `chart_id`. No explicit
  out-of-range-date guard: swisseph itself will simply compute (or silently degrade) for
  dates far outside any sane ephemeris range; nothing in this router bounds-checks the date
  before calling `swe.julday`/`swe.calc_ut`.

From `engine.get_ephemeris()` (the self-test/probe path):
- Unsupported `ayanamsha` → raises `ValueError` (loud), engine.py:376-379.
- Live path (`_compute_live`) only supports `ayanamsha == "lahiri"` — any other value raises
  `NotImplementedError` (loud), engine.py:306-310.
- Missing `chart_id`: N/A, none accepted.
- Silent-degrade behavior found: if PATH-A's `_read_from_bg_ephemeris` fails for *any* reason
  (missing rows, import failure, `derive_sidereal` exception, or a body missing from the
  stored set), it returns `None` and `get_ephemeris()` **silently falls through to PATH-B**
  (engine.py:409-428) rather than surfacing why PATH-A failed. This is intentional graceful
  degradation, not a bug, but it does mean a caller cannot distinguish "PATH-A was never
  attempted" from "PATH-A was attempted and quietly failed" without inspecting the returned
  `source` field and, even then, without a reason code.

### 1.7 Consumer route

TS side: `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`,
`callEphemerisAtTCapability` (tool name `call_ephemeris_at_t`, uri
`marsys://tool/L3/call_ephemeris_at_t`), lines 172-267. Its `handler()` does a bare `fetch()`
to `${PYTHON_SIDECAR_URL}/api/compute/ephemeris_at_t` with `{datetime_utc, ayanamsha_id}` and
passes the sidecar's JSON straight through (`positions`, `jd`, `count`). Registered/re-exported
via `platform/src/lib/retrieval/registry/layers/L3_kala/index.ts` (confirmed present in that
file's own header comment listing `call_ephemeris_at_t — ka_graha_sancara`).

**Note on the task's stated names**: the task briefing named the consumer handlers
`call_ephemeris_at_t` / `query_planet_transit`. Only `call_ephemeris_at_t` was found — a
targeted search (`grep -n "query_planet_transit"` across the `L3_kala` directory and the
repo generally) returned no matches anywhere in the codebase. This is reported honestly as
**not found** rather than assumed to be a typo for something else.

The capability descriptor's `availability_contracts` (line 215-219) pins a required health
probe: `probe_id: 'graha_sancara_forensic'`, `endpoint_identity:
'nirmana-elevation:health-probe:ka_graha_sancara'`, `probe_contract_sha256:
'2e7108591fc10fc0c435c9129b2336f18d79ec4348d765008aa0b5521f4bd8a6'`, `max_age_seconds: 900` —
i.e. this tool binding is only "available" per the registry's own contract when a fresh
(≤15 min old) authenticated probe receipt exists, sourced from
`platform/python-sidecar/scripts/nirmana_probe_contracts.json` and
`platform/python-sidecar/routers/nirmana_probe.py`.

### 1.8 Concrete value-test sketch

Grounded in the actual code: `engine.get_ephemeris()`'s applying/separating computation
(`GrahaState.applying_or_separating`) is the one piece of genuine interpretive logic in this
asset. A falsifiable test:

> Call `get_ephemeris(dt=<birth instant, 1984-02-05T10:43 IST>, ayanamsha='lahiri',
> db_conn=None, force_live=True)`. Take the returned Moon `GrahaState` (per the writer's own
> FORENSIC self-test and the nirmana probe, this must be sidereal Aquarius,
> `sidereal_lon_deg` ≈ 324.4787°, per `writers/ka_graha_sancara.py`'s own inline comment
> recording a verified live value). Call `moon.applying_or_separating(target_lon_deg=X)` for
> an X a few degrees ahead of the Moon's longitude in its direction of motion (Moon's
> `speed_dps` is always positive — it is never shown retrograde per engine.py:263, `is_retro`
> forced `False` for Sun/Moon/Rahu/Ketu) — expect `"applying"`. For an X a few degrees
> *behind* the Moon, expect `"separating"`. This is a genuine behavior change driven by the
> target longitude argument, not a trivial echo, and it directly falsifies against the
> documented formal rule in the method's own docstring (engine.py:84-126).

A second, router-level test: call `POST /api/compute/ephemeris_at_t` twice for the same
`datetime_utc` with `ayanamsha_id='lahiri_chitrapaksha'` vs `ayanamsha_id='krishnamurti'` (KP)
— every graha's returned `longitude`/`sign` must differ by the ayanamsha offset between Lahiri
and KP (a few arcminutes, not enough to flip most signs but a real, checkable numeric
difference) — this exercises the endpoint's actual sidereal-mode branching
(`_AT_T_AYANAMSHA_MAP`) rather than a value that would be identical regardless of the
parameter.

### 1.9 Missing-data / failure-mode gaps found

1. **Two independent, divergent implementations of the same computation.** The service
   package (`services/ka_graha_sancara/engine.py`) and the live HTTP endpoint
   (`routers/ephemeris.py::ephemeris_at_t`) are separate code paths that do not call each
   other. They use **different ayanamsha vocabularies**
   (`engine.SUPPORTED_AYANAMSHAS = {lahiri, raman, kp, krishnamurti, yukteshwar,
   surya_siddhanta}` vs router's `_AT_T_AYANAMSHA_MAP = {lahiri_chitrapaksha, true_chitra,
   krishnamurti, raman, surya_siddhanta_classical}` — overlapping but not identical string
   sets, e.g. `"kp"` vs absent, `"true_chitra"` present only in the router, `"yukteshwar"`
   present only in engine.py). This means the asset's health probe/self-test path
   (which exercises `engine.get_ephemeris`) and its actual live-served path
   (which exercises the router) can silently drift out of sync — a change to one's
   ayanamsha handling would not be caught by testing the other. This is exactly the kind of
   "which mechanism is actually live" ambiguity the campaign's acceptance work should pin
   down explicitly, since a GREEN self-test does not prove the router's independent
   implementation is correct.
2. **PATH-A silent fallback with no distinguishing reason code** (§1.6 above) — a caller
   cannot tell "no DB connection supplied" from "DB read failed" from "date out of range"
   without inspecting logs.
3. **No upper/lower date sanity bound on the live router path** — dates wildly outside any
   sane ephemeris range are not rejected before being handed to `swe.julday`/`swe.calc_ut`.

---

## 2. `ka_dasha_kala`

### 2.1 Identity / type — CONFIRMED: service, not a writer

Registered writer: `platform/python-sidecar/services/ka_dasha_kala/writer.py`. Registration
happens via a factory function `_build_writer_class()` (to avoid a circular import at module
load time) which defines `@register("ka_dasha_kala") class KaDashaKalaWriter(WriterBase)`,
then the module-level line `KaDashaKalaWriter = _build_writer_class()` triggers registration
on import. Its own docstring: *"The writer does NOT insert rows into chart_dashas or any
L1/L2 table... Returns WriterResult(rows_written=0) -- service asset, no data rows."*
Confirmed by reading `run()`: it only calls `_run_selftest(conn)` (delegates to
`KaDashaKalaService.confirm_systems_present` + `.query()`) and
`_update_registry_health(conn, ok, detail)` (an `UPDATE asset_registry ... WHERE asset_id =
'ka_dasha_kala'`), then returns `WriterResult(rows_inserted=0, ...)`.

### 2.2 Qualified purpose / which L3 value question it improves

Per `services/ka_dasha_kala/__init__.py` and `service.py`'s docstrings: a "Daśā-Eligibility
Service" that runs a **lazy pruning tree-walk** over `chart_dashas` (levels 1-4: Mahā/Antar/
Pratyantar/Sookshma) across the 7 production dasha systems (`vimshottari, yogini, ashtottari,
chara_karaka, naisargika, mudda, kalachakra` — KP is explicitly a Vimshottari sub-level via
`kp_sublevel`, not an 8th system), scores each surviving lord by an `EligibilityBand`
(`EXACT`/`RELATED`/`NEUTRAL`, `eligibility.py`) against caller-supplied `target_lords` /
`related_lords` sets, and reports **cross-dasha agreement** — how many of the 7 independent
systems produce a window with identical `(start_date, end_date)` boundaries (`service.py:
196-239`).

Of the campaign's "value question" families, this most directly serves **"timing method
agreement/disagreement"** — the `cross_dasha_agreement` / `high_agreement_count` fields exist
specifically to surface when multiple independent dasha systems converge on the same window
(a stronger timing signal than any single system alone), and **"which mechanism engaged"**
in the narrower sense of "which dasha lord(s), at which level, are eligible for a given
target signature over a date range" — i.e. this is the eligibility/pruning half of a
"what is active now and does it matter" question, not itself a full activation verdict.

### 2.3 Exact source/import closure

Read directly from `tree_walk.py`'s `_fetch_level1()` and `_fetch_children()`: the sole data
source is the `chart_dashas` table, read via raw SQL:
```sql
SELECT dasha_row_id, lord_graha, start_date, end_date, kp_sublevel, kp_sub_lord
FROM chart_dashas
WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = %s AND level_n = 1
  AND start_date < %s AND end_date > %s
```
and, for children, `SELECT ... FROM chart_dashas WHERE parent_row_id = %s AND start_date < %s
AND end_date > %s`. No other table is read anywhere in `service.py`, `eligibility.py`,
`tree_walk.py`, or `writer.py`. `eligibility.py`'s scoring is pure in-memory logic over the
`lord_graha` string already returned by the SQL — it consults no additional table.

Per migration `platform/supabase/migrations/1035_data_plane_l1_producer_history.sql` line
1781 (`WHEN 'chart_dashas' THEN 'ga_dashas'`), `chart_dashas` is protected-L1 and its
producer/owner asset_id is **`ga_dashas`** — confirmed exactly as the task briefing stated.

### 2.4 Field/partition semantics — L1 consumption confirmed; no §N.5 violation found

`ka_dasha_kala` consumes, per row of `chart_dashas`: `dasha_row_id` (natural key, carried
through unmodified as `EligibleWindow.dasha_row_id`), `lord_graha`, `start_date`, `end_date`,
`level_n`, `parent_row_id`, `kp_sublevel`, `kp_sub_lord`, `system_id`, `ayanamsha_id`,
`chart_id`. All of these are **passed through verbatim** into `DashaInterval` /
`EligibleWindow` — none are recomputed. The only two values this service computes itself are
(a) `eligibility_band`/`eligibility_score`, which are a new derived signal (a soft prior over
`lord_graha` against caller-supplied signature sets) — not a restatement of any existing L1
fact, so §N.5 does not apply to it — and (b) the optional in-memory level-5 (Prāṇa)
subdivision (`_subdivide_prana`, `tree_walk.py:125-165`), which is explicitly documented as
"an approximation" (equal-duration proportional split, not classical Prāṇa ratios) and is
**guaranteed never persisted** — `chart_dashas` itself enforces `level_n <= 4` via a CHECK
constraint per the module docstring, and the writer never inserts into `chart_dashas` at all
(confirmed: no `INSERT`/`UPDATE ... chart_dashas` anywhere in the `ka_dasha_kala` package).

**No §N.5 violation was found.** The service never restates an L1-computed `start_date`,
`end_date`, or `lord_graha` value as its own; it only reads and re-scores/re-groups them.
The Prāṇa subdivision is a disclosed, ephemeral, in-memory approximation clearly out of
scope of §N.5's "L1 authority" concern (it is a level the L1 layer never computes or claims
at all — `chart_dashas` stops at level 4).

### 2.5 Actual input/output contract

**(a) `KaDashaKalaService.query()`** (`service.py:94-255`, the actual named service — but see
§2.9 for whether this is on the live consumer path at all):
```python
def query(self, chart_id: str, ayanamsha_id: str, target_lords: Set[str],
          related_lords: Set[str], date_start: date, date_end: date,
          max_level: int = 4, min_band: EligibilityBand = EligibilityBand.RELATED,
          prana_grain: bool = False, systems: Optional[Set[str]] = None,
          _query_counter: Optional[list] = None) -> KaDashaKalaResult
```
Returns `KaDashaKalaResult(chart_id, ayanamsha_id, target_lords, related_lords, date_start,
date_end, max_level, prana_grain, systems_queried, windows: list[EligibleWindow], kp_windows,
total_windows, high_agreement_count)`. Each `EligibleWindow` carries
`cross_dasha_agreement: CrossDashaAgreement(count, systems_agreeing)`.

**(b) `POST /api/compute/...`** — **no FastAPI route exists for this service.** A targeted
search (`grep -rn "KaDashaKalaService\|ka_dasha_kala" platform/python-sidecar/main.py
platform/python-sidecar/routers/*.py`) found exactly one hit, and it is only the probe-type
name mapping in `routers/nirmana_probe.py:25` (`"ka_dasha_kala": "dasha_kala_proxy_integrity"`)
— not an invocation of the service. `KaDashaKalaService` is only ever instantiated inside
`writer.py`'s self-test (in-process, given the orchestrator's own `ctx.db_conn`) and inside
its own test suite. This is reported as a genuine finding, not assumed.

**(c) The live TS consumer tool `call_dasha_eligibility`** (§2.8) does **not** call
`KaDashaKalaService` either — it issues its own independent SQL query directly against
`chart_dashas` and computes its own, simpler cross-system-agreement grouping in TypeScript.
Its actual input/output contract (`call_service_wrappers.ts:271-403`):
```
inputs:  chart_id (required), ayanamsha_id (default 'lahiri'), date_from (default today),
         date_to (default today+3y), target_lords (string[], optional filter on lord_graha
         at any level — no related_lords / eligibility-band distinction is applied here)
outputs: { chart_id, ayanamsha_id, date_from, date_to, target_lords, dasha_windows,
           cross_system_windows, high_agreement_count, count }
```

### 2.6 Bounds and error behavior

From `KaDashaKalaService.query()` (the Python service — self-test path only, see §2.9):
- `max_level` outside `[1,4]` → raises `ValueError` (loud), `service.py:140-141`.
- `date_start >= date_end` → raises `ValueError` (loud), `service.py:143-147`.
- `systems` explicitly provided but empty → raises `ValueError`; unknown system name(s) in
  `systems` → raises `ValueError` listing the unknown ones (`service.py:152-158`).
- **A per-system query failure is never silently absorbed into a partial result** — an
  explicit in-code §N.8-style comment (`service.py:184-192`) states the rationale: *"A result
  that lists a failed system in systems_queried is indistinguishable from complete evidence
  to callers... never downgrade a system read failure to an apparently valid partial
  result"* — any exception from `walk_eligible_intervals` for one system re-raises as
  `RuntimeError` and aborts the whole call, rather than returning 6-of-7 systems silently.
  This is a genuinely strong, verified fail-loud guarantee.
- **Missing/nonexistent `chart_id`**: no explicit existence check anywhere in the service or
  the tree-walk. A chart_id with zero rows in `chart_dashas` simply returns an empty
  `windows` list with `total_windows=0` — indistinguishable from "this chart legitimately has
  no eligible windows in this range" vs. "this chart_id does not exist at all." This is a
  genuine gap (see §2.10).
- Writer's own self-test (`writer.py`) treats any failure as `service_health='degraded'` and
  then **raises** `RuntimeError` so the orchestrator's error path fires (same §N.8 pattern as
  `ka_graha_sancara`'s writer) — confirmed not merely a labeled status.

From the live TS consumer (`call_dasha_eligibility`, `call_service_wrappers.ts`):
- Missing `chart_id` → returns `{error: 'chart_id is required'}, is_error: true` (handled in
  TS before any SQL runs).
- A SQL error (e.g. DB unavailable) is caught and returned as `{error: String(err), chart_id},
  is_error: true` — never thrown uncaught.
- No existence check for `chart_id` here either — same gap as the Python service: an unknown
  chart_id returns `count: 0` with `is_error: false`, not a distinguishable "chart not found."
- No dasha-system-unsupported handling exists in this TS path at all, because it does not use
  `eligibility.py`'s system/band vocabulary — it queries raw rows and groups by
  `(start_date, end_date)` regardless of which `system_id` values are present.

### 2.7 Field/partition semantics recap — table of what is/is not touched

| Value | Source | Recomputed locally? |
|---|---|---|
| `dasha_row_id`, `parent_row_id` | `chart_dashas` (L1, owner `ga_dashas`) | No — passed through |
| `lord_graha`, `start_date`, `end_date`, `level_n`, `system_id`, `kp_sublevel`, `kp_sub_lord` | `chart_dashas` | No — passed through |
| `eligibility_band` / `eligibility_score` | Derived in `eligibility.py` from `lord_graha` + caller's `target_lords`/`related_lords` | New derived signal, not an L1 restatement |
| `cross_dasha_agreement` | Derived in `service.py` by grouping already-fetched rows on identical `(start_date, end_date)` | Grouping logic, not a value restatement |
| Level-5 (Prāṇa) sub-intervals | In-memory equal-duration proportional split of a level-4 row (`tree_walk._subdivide_prana`) | Disclosed approximation; never persisted; not an L1 value in the first place |

### 2.8 Consumer route

TS: `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`,
`callDashaEligibilityCapability` (tool name `call_dasha_eligibility`, uri
`marsys://tool/L3/call_dasha_eligibility`), lines 271-403. Registered via the same
`layers/L3_kala/index.ts` file (confirmed in its header comment listing the five `call_*`
service wrappers). No entry for `ka_dasha_kala` was found under
`platform-mcp/src/tools/kala_views/` — that directory's dasha-adjacent file,
`platform-mcp/src/tools/kala_views/dasha_sandhi.ts` (backing the `kala_dasha_sandhi_get`
MCP tool), was checked via `grep -n "ka_dasha_kala|KaDashaKalaService"` across
`platform-mcp/src` and returned no match — `kala_dasha_sandhi_get` is a separate capability
not wired to this service package. This is reported as **searched and not found**, per the
task's own instruction to state that explicitly rather than assume a plausible-sounding
connection.

### 2.9 The central finding: the named "service" and the live consumer are two different implementations

This is the most important finding of this dossier and mirrors the same shape found for
`ka_graha_sancara` (§1.9.1). Three independent pieces of code all claim the
`ka_dasha_kala` identity, and they diverge:

1. **`services/ka_dasha_kala/{service,eligibility,tree_walk}.py`** — the "real" service with
   lazy pruning, `EligibilityBand` scoring, and Prāṇa subdivision. Exercised only by
   `writer.py`'s self-test (in-process orchestrator context, canonical chart only) and by its
   own unit tests.
2. **`pipeline/orchestrator/service_probes.py::_probe_dasha_kala`** — the authenticated
   nirmana health probe. Its own extensive in-code comment (lines 871-900) is explicit and
   important: this probe is a **ruled, deliberate DB-free PROXY check** (D-CND-34 ruling,
   PR #2071/#2067) because `run_health_probe()` has no `db_conn` parameter by architectural
   design. It verifies exactly two things — (1) `KaDashaKalaService`/`walk_eligible_intervals`/
   `ALL_DASHA_SYSTEMS` import cleanly, and (2) the 7-system constant set exactly matches
   `nirmana_probe_contracts.json`'s `expected_systems` list (no rename/add/remove). It
   explicitly does **not** verify `chart_dashas` correctness or any live-DB-backed behavior,
   and the code carries an in-line `_DASHA_KALA_SCOPE_NOTE` string attached to every check
   specifically so this scope limitation travels with the result rather than living only in
   a comment (a real §N.8-style disclosure, verified by reading the actual check code, not
   assumed from the docstring).
3. **`call_service_wrappers.ts`'s `call_dasha_eligibility` handler** — the actual live path a
   retrieval-plane caller reaches. It bypasses the Python service package entirely: no HTTP
   call to the sidecar for this tool (unlike `call_ephemeris_at_t` and `call_transit_search`,
   which do `fetch()` a sidecar endpoint), no import of `KaDashaKalaService`. It queries
   `chart_dashas` directly via the TS `query()` DB client and reimplements its own,
   simpler cross-system-agreement grouping — with no eligibility-band scoring
   (`target_lords`-only filtering, no `related_lords` distinction, no
   EXACT/RELATED/NEUTRAL banding, no pruning tree-walk — it fetches all matching rows in one
   flat query with `LIMIT 400`).

**Consequence for acceptance-test design**: a test that proves `KaDashaKalaService.query()`'s
eligibility-band pruning is correct does not prove anything about what
`call_dasha_eligibility` actually returns to a real caller, because the two never share code
path. Any "terminal acceptance" claim for this asset needs to be explicit about which of these
three surfaces it is certifying — the self-test-only Python service, the DB-free proxy probe,
or the actually-reachable TS tool — because a GREEN on one says nothing about the other two.

### 2.10 Concrete value-test sketch

Grounded in the actual code, at the level that is genuinely live (the TS `call_dasha_eligibility`
tool, §2.8):

> For the canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`), call
> `call_dasha_eligibility` with `target_lords=['Saturn','Rahu']`,
> `date_from='2010-01-01'`, `date_to='2030-12-31'`. This is the exact window the writer's own
> self-test uses (`writer.py:58-64`) and is asserted there to return a non-empty result — so a
> genuinely broken query (e.g. a wrong `lord_graha IN (...)` binding, or an `ayanamsha_id`
> mismatch between `chart_dashas`'s stored value and the default `'lahiri'` the TS handler
> passes) should make `dasha_windows` come back empty or malformed, falsifying the test. A
> second, sharper check: compare `high_agreement_count` for `target_lords=['Saturn','Rahu']`
> against the same call with an empty/omitted `target_lords` (all lords) over the same window
   — the filtered call's `cross_system_windows` should be a strict subset by
   `(start_date, end_date)` key of the unfiltered call's, and the composition of
   `agreeing_systems` for any shared key must be identical between the two calls (the filter
   only removes rows by `lord_graha`, it cannot change which systems agree on a boundary that
   survives the filter) — this is a genuine invariant the actual grouping code in
   `call_service_wrappers.ts:370-383` must satisfy, not a trivial echo test.

Separately, the **self-test-only Python service** offers its own falsifiable case
(`writer.py`'s own assertions): `KaDashaKalaService.query(chart_id=<canonical>,
ayanamsha_id='lahiri_chitrapaksha', target_lords={'Saturn','Rahu'},
related_lords={'Mercury','Venus'}, date_start=date(2010,1,1), date_end=date(2030,12,31),
max_level=2)` must return `result.windows` non-empty and every window's `start_date <
end_date`. If Saturn is not among the surviving MD lords in this window for the native's
chart, this becomes a real failure the pruning logic could plausibly produce (e.g. if the
Saturn MD does not actually fall inside 2010-2030) — this is worth confirming against the
chart's actual Vimshottari MD sequence before relying on it as a fixed acceptance fixture.

### 2.11 Missing-data/failure-mode gaps found

1. **The named service (§2.9 item 1) is not on the live consumer path.** This is the single
   biggest gap: an acceptance packet that only exercises `KaDashaKalaService` (or only the
   DB-free proxy probe) would certify something a real caller never touches.
2. **No chart_id existence check** anywhere in either the Python service or the TS consumer
   — an unknown `chart_id` returns an empty/zero-count success rather than a distinguishable
   not-found signal (§2.6).
3. **`call_dasha_eligibility`'s `ayanamsha_id` default (`'lahiri'`) vs. the writer/probe's
   canonical value (`'lahiri_chitrapaksha'`)** are different strings (`call_service_wrappers.ts:328`
   vs. `writer.py:26`/`nirmana_probe_contracts.json`). If `chart_dashas` rows for the
   canonical chart are stored under `'lahiri_chitrapaksha'` (as the writer's self-test uses)
   and a caller of `call_dasha_eligibility` omits `ayanamsha_id`, the TS handler's default of
   `'lahiri'` would silently return zero rows rather than erroring — this is a plausible,
   concrete "silent empty result from a naming mismatch" risk worth an explicit acceptance
   check (compare `chart_dashas.ayanamsha_id` values actually present for the canonical chart
   against both defaults). This was flagged from reading the two default values side by side;
   whether `chart_dashas` actually stores `'lahiri'` or `'lahiri_chitrapaksha'` (or both) was
   **not verified against the live table in this pass** — a DB read was outside this dossier's
   read-only, no-execution scope for this file-level research task, and is called out here as
   an explicit follow-up rather than assumed either way.
4. **`call_dasha_eligibility`'s eligibility semantics are simpler than the service package's
   name promises** — no `EligibilityBand`/pruning is exposed to a live caller at all, only a
   raw lord-graha filter. A dossier reader relying on the tool's description text ("dasha
   eligibility windows... eligibility thresholds") without reading the handler code would be
   misled about what is actually computed.

---

## 3. Summary table

| | `ka_graha_sancara` | `ka_dasha_kala` |
|---|---|---|
| Asset kind (confirmed from code) | service, 0 rows | service, 0 rows |
| L1/L0 tables read | `ephemeris_daily` (L0) via PATH-A only; live swisseph otherwise | `chart_dashas` (L1, owner `ga_dashas`) |
| §N.5 local-recompute violation found? | N/A — no L1 fact consumed | No — values passed through verbatim; only a new derived score + disclosed ephemeral approximation added |
| Named service actually on the live consumer path? | No — router has its own independent swisseph implementation | No — TS tool queries `chart_dashas` directly, bypassing the Python service package |
| Authenticated health probe scope | Live FORENSIC compute (birth-instant Moon=Aquarius) + 9-graha/speed completeness — genuinely live | Ruled DB-free PROXY (import + 7-system constant-set identity only) — explicitly does not touch `chart_dashas` |
| Fail-loud discipline | Writer raises on unhealthy self-test (§N.8 fix); router 422/400 on bad input | Writer raises on failed self-test; service raises RuntimeError on per-system failure (never silently partial) |
