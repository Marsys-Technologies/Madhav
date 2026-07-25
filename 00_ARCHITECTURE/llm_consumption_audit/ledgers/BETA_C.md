---
artifact: BETA_C (Elevation Campaign v2.1, Stream β lane C)
title: Sidereal ephemeris & panchāṅga — EL-39, EL-49
version: 1.0
status: LANE-COMPLETE (code + tests + local/live-G0-verified; G4 production
  re-confirmation is a Stream-Verifier action post-merge+deploy, not performed by
  this lane per charter §9/§10 — builder does not merge or deploy)
owner: β.C (elev/beta-C-sidereal-panchanga)
branch: elev/beta-C-sidereal-panchanga
worktree: .worktrees/beta-C (dedicated, isolated from the shared .worktrees/beta
  directory per the [LANE-C] proxy-log ruling — see proxy/beta.md)
authored_by: Lane β.C builder (autonomous, Native-Proxy per charter §10)
date: 2026-07-25
---

# BETA_C — Sidereal ephemeris & panchāṅga ledger

## Summary

| EL | Title | Disposition |
|---|---|---|
| EL-39 | `ref_planet_position_get` (+ 4 sibling ephemeris routes) tropical-only leak | **PREPARED-FOR-NATIVE** |
| EL-49 | No first-class `panchanga_get(date, location?)` | **PREPARED-FOR-NATIVE** |

Both items: G0 reproduced live against production (evidence below), root-caused in the
sidecar (not a TS-layer bug), fixed with sidereal-first / IST-explicit semantics,
covered by new unit tests (39 new tests across 2 files, all passing), and verified
locally against the EXACT numbers the charter's own evidence blocks cite. Neither is
merged or deployed by this lane (charter §7.3/§10: builder pushes a branch and opens
a PR; only the Stream-Conductor merges). **Disposition is PREPARED-FOR-NATIVE, not
VERIFIED-CLOSED**, because charter §9.3/§9.6 reserves the G4 live-production
re-confirmation and the §15 matrix update to a Verifier acting post-merge+deploy —
this matches the precedent already set by [LANE-D2]'s BETA_D2 entries in
`proxy/beta.md` for the same "code+tests+offline/G0-verified; live landing deferred
to integration" shape.

---

## EL-39 — ephemeris routes serve TROPICAL only, mis-derive nakshatra

### G0 — reproduce-or-reclassify (live production, via `mcp__marsys-jis-direct__*`)

**Reproduced exactly as the register/charter describe.** Five separate live probes,
all against production, all pre-fix:

1. `ref_planet_position_get(date="2026-08-15", planet="Venus")` →
   ```json
   {"ok":true,"date":"2026-08-15","positions":[{"date":"2026-08-15","body":"Venus",
   "tropical_longitude":188.565106,"sign_number":7,"degree_in_sign":8.565,
   "nakshatra_number":15,"is_retrograde":false,"speed_dps":0.9568653,
   "source_citation":"pyswisseph DE441 + Swiss Ephemeris (pyswisseph==2.10.3.2)"}],
   "count":1,"ayanamsha_id":"tropical", ...}
   ```
   Matches the charter's cited evidence byte-for-byte (`tropical_longitude:188.565106`,
   `sign_number:7`). `ayanamsha_id` is not requestable — the field is served, not
   accepted meaningfully.
2. `ref_aspects_at_time_get(date="2026-08-15")` → `"ayanamsha_id":"tropical"`,
   `longitude_b1`/`longitude_b2` unlabelled tropical values.
3. `ref_retrograde_periods_get(planet="Venus", 2026-07-01..2026-09-30)` → 0 stations
   (Venus genuinely not retrograde that window — a true negative, not the bug — but
   the route accepted no ayanamsha_id override at all).
4. `ref_planet_transit_get(planet="Venus", 2026-08-10..2026-08-20)` → 11 rows, all
   `sign_number:7` (tropical Libra) unlabelled, `ayanamsha_id:"tropical"` in the
   envelope, description says "Optional tropical sign filter".
5. `ref_ephemeris_year_get(year=2026)` → 3285 rows (trimmed to 205 by budget),
   `"ayanamsha_id":"tropical"` — confirms the year route (backs
   `ephemeris_cache_year.ts` → `all_bodies_range`) has the identical leak, via a
   route that **inlined its own ad-hoc SQL bypassing `brahmagyan.l0_ephemeris`
   entirely** (found during root-cause reading, not previously named in the
   charter's file:line citations).

**Root cause (confirmed by reading, not guessed):**
- `platform/migrations/ws2_l0_ephemeris.sql`: `ephemeris_daily.sign_number` /
  `.degree_in_sign` / `.nakshatra_number` are Postgres `GENERATED ALWAYS AS ...
  STORED` columns computed **directly from `tropical_longitude`** — tropical values
  under sidereal-sounding names, baked in at the schema level.
- `ephemeris_daily` physically stores exactly **one row per (date, body)**, always
  `ayanamsha_id='tropical'` (`brahmagyan/l0_ephemeris.py::AYANAMSHA_ID = "tropical"`,
  set at build time).
- All 5 read functions (`query_planet_position`, `query_planet_transit`,
  `query_aspects_at_time`, `query_retrograde_periods`, and the inline SQL in
  `ephemeris_routes.py::get_all_bodies_range`) used `ayanamsha_id` as a raw
  `WHERE ayanamsha_id = %s` filter against this tropical-only table — so a caller
  passing any value other than `'tropical'` got a **silent empty result**, not an
  error and not sidereal data. This is a second, subtler B.10 exposure beyond the
  one the register named (the unlabelled wrong nakshatra).

### Fix

`platform/python-sidecar/brahmagyan/l0_ephemeris.py`:
- Extended `AYANAMSHA_MAP` with the canonical 5-value vocabulary aliases
  (`lahiri_chitrapaksha`, `true_chitra`, `surya_siddhanta_classical` — matching
  `routers/jaimini.py::_VALID_AYANAMSHAS` / TS `registry/constants.ts::DEFAULT_AYANAMSHA`).
- New `_STORED_AYANAMSHA_ID = "tropical"` (what's physically in the DB) vs.
  `_DEFAULT_READ_AYANAMSHA = "lahiri_chitrapaksha"` (the new HTTP-facing default).
- New `_resolve_read_ayanamsha()` — loud `[EXTERNAL_COMPUTATION_REQUIRED]` error for
  an unrecognized ayanamsha_id, never a silent fallback.
- Rewrote all 4 query functions: always read the stored tropical row, then derive
  the requested ayanamsha at read time via the pre-existing `derive_sidereal()`
  (pyswisseph `set_sid_mode`+`get_ayanamsa_ut`). Sidereal fields (`longitude`,
  `sign_number`, `degree_in_sign`, `nakshatra_number`, `pada`, `ayanamsha_offset`)
  are now the **primary** output; `tropical_longitude` is retained as a clearly-
  labelled extra. An explicit `ayanamsha_id="tropical"` request keeps
  `sign_number`/`degree_in_sign` (legitimately tropical) but **suppresses**
  `nakshatra_number`/`pada` with an explanatory `nakshatra_note` (nakshatra is
  inherently sidereal — never served bare-wrong under tropical).
- `query_aspects_at_time`/`query_retrograde_periods`: aspect geometry and station
  dates are **ayanamsha-invariant** (subtracting the same offset from two
  longitudes preserves their difference; station events are speed-sign events,
  unaffected by a ~50″/century ayanamsha drift) — fixed the WHERE-filter bug and
  the absolute-longitude labelling, left the invariant math untouched.
- `query_planet_transit`: `sign_number` filter now matches the **sidereal** sign by
  default (previously matched stored tropical sign_number regardless of the
  ayanamsha_id param — itself a silent-wrong-filter bug).

`platform/python-sidecar/brahmagyan/ephemeris_routes.py`:
- All 4 routes' `ayanamsha_id` Query default changed `"tropical"` →
  `_DEFAULT_READ_AYANAMSHA`; docstrings/descriptions rewritten (removed the "subtract
  Lahiri ayanamsha" instruction — the exact institutionalized-client-arithmetic
  language the register calls out).
- `get_all_bodies_range` (backs `ref_ephemeris_year_get`) rewritten to reuse
  `brahmagyan.l0_ephemeris`'s sidereal-derivation helpers instead of its own inline
  SQL — same fix class as the other 4 routes. `count_only` path unchanged in
  behavior (row count is ayanamsha-invariant: exactly one stored row per
  (date,body) regardless of which ayanamsha is requested for derivation).
- `get_native_lifetime_meta` — **audited, found a residual, PARKED-HONEST, not
  fixed**: uses a fixed linear-approximation ayanamsha constant instead of
  `derive_sidereal()`, and its own lat/lon constants (20.2735/85.8334) are a
  **third** distinct "Bhubaneswar" coordinate pair in this codebase (alongside
  `l0_ephemeris.py`'s NATIVE_LAT/LON 20.2961/85.8245 and
  `panchang_daily_reader.py`'s BHUBANESWAR_LAT/LON 20.27/85.84). Both fields are
  already honestly labelled `_approx` — low severity, not one of the charter's
  named 5 routes, out of bounded scope. Recommend a follow-up unifying all three
  Bhubaneswar coordinate pairs codebase-wide.

### Verification (this lane's evidence — not a G4 Verifier stamp)

**Charter's exact bar: Venus 2026-08-15 → sidereal Lahiri sign = Virgo, correct
sidereal nakshatra.** Reproduced against the EXACT tropical_longitude the live probe
returned (188.565106), via the fixed function directly:

```json
{
  "ok": true, "date": "2026-08-15", "ayanamsha_id": "lahiri_chitrapaksha",
  "positions": [{
    "body": "Venus", "longitude": 164.336139, "sign_number": 6,
    "degree_in_sign": 14.336, "nakshatra_number": 13, "pada": 2,
    "ayanamsha_offset": 24.228967, "is_retrograde": false, "speed_dps": 1.18,
    "tropical_longitude": 188.565106,
    "source_citation": "pyswisseph + Swiss Ephemeris .se1"
  }],
  "count": 1
}
```
`sign_number: 6` = **Virgo** (1=Aries..6=Virgo). ✅ Matches the charter bar exactly.
`nakshatra_number: 13` = Hasta (160°–173°20′ sidereal span; 164.34° falls inside it —
internally consistent, and **not** the old wrong tropical-derived value of 15).

Explicit `ayanamsha_id="tropical"` request on the same row:
```json
{"body":"Venus","tropical_longitude":188.565106,"sign_number":7,"degree_in_sign":8.565106,
 "nakshatra_number":null,
 "nakshatra_note":"nakshatra is an inherently sidereal division; omitted under ayanamsha_id='tropical' — request a sidereal ayanamsha_id (default lahiri_chitrapaksha) to get nakshatra_number/pada."}
```
Confirmed at full HTTP-route level too (`FastAPI TestClient` against
`brahmagyan.ephemeris_routes.router`, mocked DB cursor returning exactly the live
row above) — identical output.

Unrecognized `ayanamsha_id` (e.g. `"bogus"`) → `ok:false`,
`[EXTERNAL_COMPUTATION_REQUIRED]` error, DB never touched (asserted via
`conn.cursor.assert_not_called()`).

**Test coverage:** `tests/test_l0_ephemeris_sidereal_first.py` (16 tests, all
passing) — Venus/Virgo bar, nakshatra-not-15, tropical-suppression,
non-tropical-no-longer-silently-empty (regression guard for the WHERE-filter bug),
all 5 canonical ayanamshas accepted, sign-filter now sidereal for
`query_planet_transit`, aspect-geometry-invariance for `query_aspects_at_time`,
station-detection-invariance for `query_retrograde_periods`. Full existing suite
(`test_l0_ephemeris.py`, `test_ephemeris_ayanamsha.py`, `ka_graha_sancara` tests —
consumers of `derive_sidereal`/`AYANAMSHA_MAP`) re-run: **169 passed, 0 failed, 0
regressions.**

### Disposition: **PREPARED-FOR-NATIVE**

Code complete, unit-tested, G0-reproduced live, locally verified against the exact
live-captured numbers. Awaiting merge + deploy + Stream-Verifier G4 re-confirmation
against production (out of this lane's authority — builder does not merge/deploy
per charter §7.3).

---

## EL-49 — no first-class `panchanga_get(date, location?)`

### G0 — reproduce-or-reclassify

**Partially reclassified — an important nuance the register text predates.**
Investigation found `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/
call_panchanga_service.ts` **already exists and is already wired** to
`POST /api/compute/panchanga` (single date) and `/panchanga/range` (up to 31 days) —
a genuine date-parameterized, any-location panchanga lookup, defaulting to
Bhubaneswar/IST, independent of muhūrta windows. Its own header comment (dated to a
"W2b Batch 3" wave) suggests it was built after EL-49 was originally logged. This
means the register's literal "reachable only through muhūrta windows" claim is
**stale** for the tool-availability question — a direct path already existed.

What genuinely remained missing, confirmed by reading `panchang_engine/serialize.py`
and calling the engine directly (offline, no live DB needed — this is pure
Swiss-Ephemeris compute):
1. **IST-ambiguity**: every timestamp `panchang_to_dict()` emits is UTC-only
   (`*_utc`, ISO-Z). A caller must convert in their head to know which IST calendar
   day a late-UTC timestamp falls on — the exact "ambiguous UTC-midnight-for-an-
   IST-day" risk the task brief named. `call_panchanga_service.ts` passes this
   straight through unchanged.
2. **No named-location convenience** (`location: "Bhubaneswar"` shorthand) — only
   raw lat/lon.
3. **No single-call convenience shape** grouping the "5 angas" + sunrise/sunset +
   hora count the way a consumer would want to read it at a glance (the raw
   `panchang` dict is complete but unopinionated/verbose).

Offline verification (before writing any fix) that the underlying compute is
already correct — this is what confirmed the gap is serving-shape, not math:
```
compute_panchang(date(1984,2,5), 20.27, 85.84, 330):
  tithi=Shukla Tritiya, vara=Ravivara, yoga=Shiva,
  karana_first=Garaja, karana_second=Vanija, nakshatra=Purva Bhadrapada,
  sunrise_utc=1984-02-05 00:51:30+00:00, sunset_utc=1984-02-05 12:09:58+00:00,
  hora: 24 entries
```
All 5 FORENSIC-relevant values already correct, pre-fix — confirms EL-49's fix is
purely about serving shape/explicitness, never about re-deriving the math (§9's
"this IS the correctness oracle, keep fixing until it matches" bar was already met
by the existing engine; nothing needed re-deriving).

**`panchanga_daily` chart-scope check (per the task's explicit ask):** confirmed
`panchanga_daily` is a **compatibility VIEW** (migration `365_w4_l4_schema_drift_fix.sql`
§5), not chart-scoped — it is `WHERE FALSE` (returns 0 rows unconditionally,
by design, as a graceful-empty placeholder replacing an archived table). It is
date-scoped/global in intent (not chart-scoped) — confirms the task's assumption
that **no chart-scoped rebuild is needed for this lane**. This also means
`panchang_daily_reader.fetch_panchanga_range()` (the muhūrta-scoring cache-read
path) is currently a **permanent cache-miss** for every call, silently falling back
to engine-direct compute every time — a real, separate finding, adjacent to but not
literally EL-39/EL-49; noted here for the record, not fixed (out of this lane's
named scope; the fallback is graceful, not a hard failure). `chart_panchanga` (a
different table) IS chart-scoped and already correctly holds the birth-moment
panchāṅga in `chart_facts` via `ga_panchanga_writer.py` — untouched by this lane.

### Fix

Two-pronged, matching the file-ownership boundary (sidecar-only) and maximizing
what actually reaches a live surface today:

1. **New `GET /api/compute/panchanga_get`** (`routers/panchang.py`) — the
   dedicated first-class capability the brief asked for: `date` + optional
   `location` (named gazetteer, currently `"Bhubaneswar"` only — deliberately
   minimal, not a general geocoder; unrecognized names are a loud 422, never a
   silent coordinate guess) or explicit `lat`/`lon`/`tz_offset_minutes`. Returns
   all 5 aṅgas (`angas.karana` = `karana_first`, full `karana_first`/
   `karana_second` pair still available in the nested `panchang` block), sunrise/
   sunset/moonrise/moonset, the complete hora table, choghadiya, auspicious/
   inauspicious windows — every UTC timestamp paired with an explicit local-offset
   sibling (`*_ist` when the resolved location is +330/IST, `*_local` and a
   `timezone_label` otherwise, so a non-Indian timezone is never mislabelled
   "ist"). Not yet wired to any MCP tool (see "Required α-side change" below).
2. **Enriched the ALREADY-LIVE `POST /panchanga` and `/panchanga/range`
   endpoints** with the identical local-time-sibling logic — this reaches
   `call_panchanga_service.ts` (and any other consumer of those two routes)
   with **zero TS-side change required**, since it already passes `panchang`
   through verbatim. This closes the real, live gap immediately rather than
   only on a new unwired endpoint.

### Verification

**FORENSIC birth-date reproduction (the free correctness oracle) — confirmed live
through the actual HTTP route** (`FastAPI TestClient`, real `panchang_engine`
compute, no mocking):
```
GET /api/compute/panchanga_get?date=1984-02-05&location=Bhubaneswar
angas.tithi.name    = "Shukla Tritiya"   ✅
angas.vara.name     = "Ravivara"          ✅
angas.yoga.name      = "Shiva"            ✅
angas.karana.name    = "Garaja"           ✅
angas.nakshatra.name = "Purva Bhadrapada" ✅ (bonus 5th match)
location = {"label":"Bhubaneswar","lat":20.27,"lon":85.84,"tz_offset_minutes":330,
            "timezone_label":"UTC+05:30 (IST)"}
sunrise = {"utc":"1984-02-05T00:51:30Z","ist":"1984-02-05T06:21:30+05:30"}
```
Also confirmed via the **already-live** `POST /api/compute/panchanga` (the exact
route `call_panchanga_service.ts` calls today):
```
tithi: {id:3, name:"Shukla Tritiya", end_utc:"1984-02-05T07:12:47Z", end_ist:"1984-02-05T12:42:47+05:30"}
vara:  {id:1, name:"Ravivara", ...}
karana_first: {id:5, name:"Garaja", ...}
```
Default-location (no `location`/`lat`/`lon` at all) also reproduces FORENSIC exactly
— covers the register's own framing ("a native asking about their own birth chart
with no location typed").

**Forward date (2026-09-18), full panchāṅga in one call:**
```
angas: tithi=Shukla Saptami, nakshatra=Jyeshtha, yoga=Priti, karana=Vanija, vara=Shukravara
sunrise = {"utc":"2026-09-18T00:04:30Z","ist":"2026-09-18T05:34:30+05:30"}
sunset  = {"utc":"2026-09-18T12:16:56Z","ist":"2026-09-18T17:46:56+05:30"}
hora_count = 24 (complete cycle; all 7 classical planets represented; every entry carries start_ist/end_ist)
```

**IST-anchoring correctness:** every anga's `end_utc`/`end_ist` pair verified to
differ in wall-clock value (proves the +5:30 conversion actually ran, not just
relabeled); a non-IST test location (London, UTC+1) verified to get `*_local`
fields, never mislabelled `*_ist`.

**Test coverage:** `tests/test_panchanga_get.py` (21 tests) covering FORENSIC
reproduction (5 tests), forward-date full-panchāṅga (5), IST-anchoring (2),
location resolution incl. the loud-422-on-unknown-location case (3), source
disclosure (1), and the already-live POST-endpoint enrichment (3, including a
field-projection interaction check). All passing. Full panchang-adjacent suite
re-run: 83 passed, 0 regressions.

### Disposition: **PREPARED-FOR-NATIVE**

Code complete, unit-tested (39 tests total across both ELs), FORENSIC-verified
exactly per the brief's non-negotiable bar, both against the new endpoint and the
already-live one. Awaiting merge + deploy. The `panchanga_get` route itself needs
an α-side wiring decision (new tool vs. fold into `call_panchanga_service`) — see
below; this is documented, not performed, per file-ownership boundary.

---

## Required α-side change (β cannot edit `platform/src/lib/retrieval/**`)

1. **C5-documented** (see `~/elev-v2-shared/contracts/C5_SIDEREAL_EPHEMERIS_v1_0.md`):
   add an optional `ayanamsha_id` param to `query_planet_position.ts`,
   `query_planet_transit.ts`, `query_aspects_at_time.ts`,
   `query_retrograde_periods.ts` — all four already pass the sidecar body through
   verbatim, so they inherit sidereal-first defaults with **zero changes**; the
   only reason to touch them is to let a caller request a non-default ayanamsha
   (including explicit `tropical`). Also correct the four `description` strings
   (currently instruct "subtract Lahiri ayanamsha" — now false, and the exact B.10
   exposure EL-39 named).
2. **New for EL-49**: `call_panchanga_service.ts` already gets the IST-timestamp
   fix for free (calls the enriched `/panchanga` and `/panchanga/range` routes
   directly, passes the payload through unchanged — no TS edit needed). The NEW
   `/panchanga_get` endpoint, however, is not wired to any tool yet. Recommended:
   either (a) register a new lightweight `panchanga_get` capability pointing at
   `GET {SIDECAR_URL}/api/compute/panchanga_get?date=...&location=...`, or (b) extend
   `call_panchanga_service.ts`'s existing `mode` enum with a `mode='get'` that calls
   the new route for its convenience shape (grouped `angas`, `location` resolution).
   Left as an α decision — both are equally valid; this lane does not have
   standing to choose since it does not own the TS registry.

## Found-but-parked residuals (not in this lane's bounded scope; logged per §10)

- `get_native_lifetime_meta` (ephemeris_routes.py): approximate ayanamsha offset +
  a third distinct "Bhubaneswar" coordinate pair. PARKED-HONEST — already labelled
  `_approx`, low severity, not one of the charter's 5 named routes.
- `panchang_daily_reader.fetch_panchanga_range()` is a permanent cache-miss today
  (the `panchanga_daily` view it queries is `WHERE FALSE` by design, per migration
  365's own comment). Graceful fallback, not a hard failure — flagged for the
  record, not fixed (adjacent to, not literally, EL-39/EL-49).
- Three independent ayanamsha-key vocabularies coexist in this codebase (this
  file's `AYANAMSHA_MAP` build-time keys, `panchang_engine`/`pyjhora_adapter`'s
  short keys, and the canonical 5-value vocabulary this fix standardizes the read
  API on). Not unified — out of bounded scope, aliases added additively only.

## No DB rebuild required

Confirmed per the task's explicit ask: `panchanga_daily` is date-scoped/global
(currently a degenerate 0-row view, not chart-scoped), and neither EL-39's fix
(read-time derivation over the existing `ephemeris_daily` table) nor EL-49's fix
(engine-direct compute, bypassing the incomplete cache entirely by design) touches
any chart-scoped table. No `db-rebuild` lock was acquired; none was needed.

## Files changed

- `platform/python-sidecar/brahmagyan/l0_ephemeris.py`
- `platform/python-sidecar/brahmagyan/ephemeris_routes.py`
- `platform/python-sidecar/routers/panchang.py`
- `platform/python-sidecar/tests/test_l0_ephemeris_sidereal_first.py` (new)
- `platform/python-sidecar/tests/test_panchanga_get.py` (new)
- `00_ARCHITECTURE/llm_consumption_audit/ledgers/BETA_C.md` (this file, new)

## C5 contract

`~/elev-v2-shared/contracts/C5_SIDEREAL_EPHEMERIS_v1_0.md`,
sha256 `448f8a05803e8c9864c4c4e39c09557ce73d8ea6b7423625ef3649337014163c`. Published
late (past T0+3h) due to a session reconnect mid-investigation — see `[LANE-C]`
entries in `proxy/beta.md` for the honest timeline; design work was complete before
the disconnect, so the delay was purely mechanical, not a difficulty in the design
itself.

## ADDENDUM (Stream-Conductor, 2026-07-25, post-merge-and-deploy G4) — both VERIFIED-CLOSED

Deploy confirmed live: `amjis-sidecar` revision `amjis-sidecar-00912-rv7`, commit-sha label
`8fd9343b8411dcea9843183c27f6b941f2a9ad9c` (the merged `main` head).

**EL-39:** `ref_planet_position_get(date=2026-08-15, planet=Venus)` via the live MCP path →
`sign_number:6` (Virgo, sidereal Lahiri), `ayanamsha_id:"lahiri_chitrapaksha"` (now the default),
`tropical_longitude:188.565106` retained as a labelled extra. Matches the fix exactly.

**EL-49:** live authenticated call to the deployed sidecar's new route,
`GET /api/compute/panchanga_get?date=1984-02-05&location=Bhubaneswar`, reproduces all 5 FORENSIC
pañchāṅga anchors exactly: Tithi=Shukla Tritiya, Nakshatra=Purva Bhadrapada, Yoga=Shiva,
Karana=Garaja, Vara=Ravivara. Full horā table + sunrise/sunset/moonrise/moonset present with
explicit UTC+IST timestamps.

**Disposition updated: both EL-39 and EL-49 `VERIFIED-CLOSED`** — supersedes the `PREPARED-FOR-
NATIVE` status above (which was correct at the time: this lane had no authority to perform the
post-merge+deploy G4 step itself). The α-side capability-registration decision for `panchanga_get`
(documented above, §"Required α-side change") remains open and un-blocking — the route is live and
correct regardless of whether/how α later exposes it as a named MCP capability.
