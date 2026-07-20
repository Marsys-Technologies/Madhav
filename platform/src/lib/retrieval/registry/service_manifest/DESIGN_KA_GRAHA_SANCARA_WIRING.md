---
artifact: DESIGN_KA_GRAHA_SANCARA_WIRING
canonical_id: DESIGN_KA_GRAHA_SANCARA_WIRING
version: 1.1
status: IMPLEMENTED — W2 (2026-07-20). See "W2 IMPLEMENTATION NOTE" below; the design
  text beneath it (§1-5) is retained verbatim as the historical proposal this
  implementation followed.
wave: W1 Lane L1c (design) / W2 dark-set wiring lane (implementation, 2026-07-20)
---

# DESIGN NOTE — wiring `ka_graha_sancara` (GT-50)

## W2 IMPLEMENTATION NOTE (2026-07-20)

**Implemented as designed, with one deferred item.** `POST /api/compute/ephemeris_at_t`
landed in `routers/ephemeris.py`'s `compute_router` (mounted in `main.py` at
`/api/compute`) exactly per §3 items 1-3, 5 below — reuses `_position_from_lon`/
`PLANETS`/`SIGNS`/`NAKSHATRAS` as-is, no second swisseph integration, unrecognized
`ayanamsha_id` fails loud (422). §3 item 4's TS wrapper change landed in
`call_service_wrappers.ts` (`callEphemerisAtTCapability.handler`), mirroring
`callTransitSearchCapability`'s fetch pattern. §3 item 6's test-suite update: the
existing `d5_l3_capabilities.test.ts` descriptor assertions were left as-is (still
true — scope/tool_role/etc. didn't change), and a new dedicated real-compute test
suite was added instead of weakening or replacing that file:
`platform/python-sidecar/tests/l3/test_ephemeris_at_t_sidecar_route.py` (6 tests,
direct in-process calls, no mocks) + `platform/src/lib/retrieval/registry/layers/
L3_kala/__tests__/w2_dark_set_wiring.test.ts` (TS wiring-seam tests, mocked fetch).

**§4's open questions — resolution:** (1) `/ephemeris` was NOT refactored to share a
route with `/ephemeris_at_t` — a genuinely separate `compute_router`/route was added
instead (still reusing the same helper functions at the Python level, just not the
same FastAPI route/request model) — this avoided touching `/ephemeris`'s live natal
contract at all, a more conservative choice than the design note's "recommend
shared-helper" framing, made because `/ephemeris`'s current callers were not
re-audited this pass (the design note's own caveat). (2) `ka_muhurta_seva` WAS
co-wired in the same W2 pass (see `DARK_SET_WIRING_PLAN_v1_0.md`'s W2 wiring log) —
as a fully independent new route/service (`muhurta_score.py`), not reusing
`ephemeris_at_t` as an input (muhurta scoring needs day-grain panchang angas, not
graha longitudes directly).

---

**Below: the original W1 design proposal, retained verbatim for audit trail.** Per the
master brief's sequencing ("DESIGNED in W1, wired in W2"), the actual sidecar endpoint
and TS handler rewrite were out of scope for W1 Lane L1c — that gap is now closed by
the W2 implementation above.

## 1. Current state (as of this wave)

- **MCP-facing capability:** `call_ephemeris_at_t`, registered in
  `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`
  (lines 155–216).
- **Handler body (lines 196–214):** unconditionally returns
  `{ is_error: true, content: { error: 'call_ephemeris_at_t is not yet wired to a
  compute sidecar endpoint', ... } }` — it never attempts a network call. This is the
  exact dark-service stub cited by `GROUND_TRUTH_REGISTER.md` GT-50.
- **Logical service id:** `ka_graha_sancara` (L3 Kāla). `asset_registry.target_table`
  is `null` for this service — by design there is no `ka_graha_sancara_snapshot` table;
  positions at an arbitrary datetime must be computed on demand, not read from a row.
- **Declared contract (`input_schema` in the descriptor):**
  - `datetime_utc` (required, ISO 8601 `YYYY-MM-DDTHH:MM:SSZ`)
  - `ayanamsha_id` (optional, default `lahiri_chitrapaksha` via `DEFAULT_AYANAMSHA`)
  - No `chart_id`, no `lat`/`lng` — this is declared `scope: 'global'`, i.e. graha
    longitudes only (no houses/lagna, which would require a birth place).

## 2. What already exists in the sidecar that is close to this contract

Two existing sidecar code paths do closely related compute, neither of which matches
the contract exactly:

1. **`POST /ephemeris`** (`platform/python-sidecar/routers/ephemeris.py`, mounted at
   the app root, no further prefix). Takes `birth_date` + `birth_time` + `lat` + `lng`
   + `ut_offset`, calls `pyswisseph` (`import swisseph as swe`) directly, and returns
   sidereal-adjusted planet longitude/sign/nakshatra/pada/retrograde/speed for 8 bodies
   (Ketu is derived as Rahu+180 by the caller). **This is the closest existing compute
   primitive** — it already does real-time, sub-day-precision, swisseph-backed
   longitude computation. It is framed as a "natal chart" endpoint (positional
   parameters named `birth_date`/`birth_time`) but the underlying math has no
   dependency on the subject being a birth — any UTC instant works. It does, however,
   require `lat`/`lng` today (only used for the `ut_offset` framing, not for planet
   longitudes, which are geocentric) and does not accept an explicit `ayanamsha_id`
   parameter (worth checking how/whether it applies an ayanamsha — not audited here).

2. **`GET /brahmagyan/ephemeris/planet_position`**
   (`platform/python-sidecar/brahmagyan/ephemeris_routes.py`, L0FR Stream B). Reads
   from the precomputed `ephemeris_daily` table (1900–2150, 9 bodies) via
   `brahmagyan.l0_ephemeris.query_planet_position`. **This is NOT sub-day precision**
   — its `date` parameter is `YYYY-MM-DD` only, tropical coordinates (caller must
   subtract Lahiri ~23.87° for sidereal), no time-of-day. It is DB-backed (fast, no
   live ephemeris compute) but cannot satisfy `call_ephemeris_at_t`'s
   `datetime_utc` (includes `HH:MM:SS`) contract without either (a) a precision
   downgrade the capability's declared contract doesn't allow, or (b) extending
   `ephemeris_daily` to sub-day granularity, which is a much larger change.

**The overlap between these two existing paths and `ka_graha_sancara` is exactly the
kind of ambiguity a real wiring decision needs to resolve** — do not silently pick one
without native sign-off, since `ephemeris_daily`'s bounded 1900–2150 range and daily
grain vs. `/ephemeris`'s arbitrary-instant swisseph compute are materially different
guarantees.

## 3. Proposed shape for a real `/api/compute/ephemeris_at_t` endpoint (W2)

1. **New sidecar route**, e.g. `POST /api/compute/ephemeris_at_t` in a new or existing
   router (candidate: extend `routers/ephemeris.py` with a second endpoint, since it
   already imports `swisseph` and has the sign/nakshatra/pada helper functions
   factored out as `_position_from_lon` — reusable as-is).
2. **Request contract** should mirror `call_ephemeris_at_t`'s existing declared
   `input_schema` exactly (do not silently add required fields the MCP descriptor
   doesn't declare): `datetime_utc` (ISO 8601 UTC), `ayanamsha_id` (optional, default
   `lahiri_chitrapaksha`).
3. **Compute**: convert `datetime_utc` to Julian day (swisseph `swe.julday`), apply
   the requested ayanamsha via `swe.set_sid_mode` (the existing `/ephemeris` handler's
   sidereal-adjustment logic should be extracted into a shared helper rather than
   duplicated — check whether it currently hardcodes Lahiri or already accepts an
   ayanamsha parameter internally; not audited in this pass), then call
   `swe.calc_ut` per body exactly as `/ephemeris` does, reusing `_position_from_lon`
   for the sign/nakshatra/pada/retrograde shaping. **No lat/lng needed** — graha
   longitudes are geocentric; only houses/lagna would need a birth place, and
   `call_ephemeris_at_t`'s contract doesn't ask for houses.
4. **TS wrapper change**: replace the unconditional-error stub in
   `call_service_wrappers.ts` (lines 196–214) with a real `fetch()` to the new
   endpoint, following the exact pattern already used by `callTransitSearchCapability`
   (lines ~113–147 of the same file) — same `PYTHON_SIDECAR_URL` / `x-api-key` /
   error-shape conventions, so the two `call_*` wrappers in this file stay consistent.
5. **Ayanamsha default mismatch to resolve before wiring**: the descriptor's default
   is `DEFAULT_AYANAMSHA` (imported from `../../constants`, resolves to
   `lahiri_chitrapaksha`); `call_dasha_eligibility` in the same file defaults to plain
   `'lahiri'` and `call_muhurta_score`/`call_transit_search` also use
   `DEFAULT_AYANAMSHA`. Confirm which ayanamsha id strings the sidecar's swisseph
   integration actually recognizes before wiring — an unrecognized id should fail
   loud, not silently fall back to tropical.
6. **Test coverage**: `platform/src/lib/retrieval/registry/layers/L3_kala/__tests__/
   d5_l3_capabilities.test.ts` already asserts `callEphemerisAtTCapability.scope ===
   'global'` and exercises it as one of three `serviceCaps` — that suite's shape
   already anticipates a live wiring; a W2 change should keep it green by updating the
   test to assert real success-path behavior once wired, not by weakening the
   assertion.

## 4. Explicitly not decided here

- Whether `/ephemeris` should be refactored to serve both natal AND arbitrary-instant
  use cases (shared helper, two thin route wrappers) vs. building
  `ephemeris_at_t` as a fully independent compute path. Recommend the shared-helper
  approach to avoid a second swisseph integration to maintain, but this needs native
  sign-off given `/ephemeris` is a live, in-use natal-computation endpoint (Stream G
  BRAHMA-G-1 depends on the sibling `/api/pyhora/compute` for the modern natal path —
  worth confirming `/ephemeris` isn't already fully superseded before extending it
  further; not audited in this pass).
- Whether `ka_muhurta_seva` (`call_muhurta_score`, the other dark L3 service found in
  this same file — see `service_manifest.json`'s `dark_set`) should be wired in the
  same W2 pass, given it shares the identical stub shape and could plausibly reuse the
  `ephemeris_at_t` primitive as an input to its scoring logic.

## 5. Non-goals of this note

No code changes are proposed for immediate landing. This note exists so a W2 session
can wire `ka_graha_sancara` without re-deriving "what's already there" from scratch.
