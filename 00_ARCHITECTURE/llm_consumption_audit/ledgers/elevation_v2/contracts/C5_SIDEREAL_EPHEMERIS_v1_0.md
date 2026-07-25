---
contract_id: C5
title: sidereal ephemeris — ayanamsha_id param semantics + sidereal-primary response shape
version: 1.0
status: FROZEN
authored_by: β (elev/beta, lane β.C — sidereal ephemeris & panchāṅga), published late
  (T0+3h deadline missed; see proxy/beta.md [LANE-C] entry for the reconnect/worktree-recovery
  rationale — this file was prioritized ahead of finishing the lane so γ.F is unblocked)
owner: β
consumers: γ (lane F — target-graha transit-condition checks inside muhūrta window scoring)
grounded_in:
  - platform/python-sidecar/brahmagyan/l0_ephemeris.py (query_planet_position, query_planet_transit,
    query_aspects_at_time, query_retrograde_periods, derive_sidereal, AYANAMSHA_MAP)
  - platform/python-sidecar/brahmagyan/ephemeris_routes.py (GET /brahmagyan/ephemeris/planet_position,
    /planet_transit, /aspects, /retrograde_periods, /all_bodies_range)
  - platform/migrations/ws2_l0_ephemeris.sql (ephemeris_daily: sign_number/degree_in_sign/
    nakshatra_number are GENERATED ALWAYS AS ... STORED columns computed directly from
    tropical_longitude — the EL-39 root cause; the table stores exactly one row per (date, body),
    ayanamsha_id='tropical', always)
  - platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_planet_position.ts (α-owned
    serving proxy; pass-through fetch to the sidecar route above — see "Required α-side change"
    below for the exact edit this contract asks α to make)
  - 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md EL-39 (lines ~468-486)
---

# C5 — sidereal ephemeris: `ayanamsha_id` param + sidereal-primary response shape

## Problem this closes (EL-39)

`ephemeris_daily` physically stores ONE row per `(date, body)`, always `ayanamsha_id='tropical'`.
`sign_number`, `degree_in_sign`, `nakshatra_number` are Postgres `GENERATED ALWAYS AS ... STORED`
columns computed directly from `tropical_longitude` — i.e. they are tropical values under sidereal-
sounding names. The four HTTP read routes (`planet_position`, `planet_transit`, `aspects`,
`retrograde_periods`) accepted an `ayanamsha_id` query param but used it only as a raw `WHERE
ayanamsha_id = %s` filter against this tropical-only table — so passing anything other than
`'tropical'` silently returned **zero rows**, and the default (`'tropical'`) served a nakshatra
number that is wrong under every ayanamsha (nakshatra is an inherently sidereal division).
Live-confirmed: Venus 2026-08-15 served `tropical_longitude: 188.565`, `sign_number: 7` (tropical
Libra) while sidereal Lahiri is Virgo — the debilitation a muhūrta/election reading depends on.

## Fix (frozen shape)

The DB storage is unchanged (still one tropical row per date/body — rebuilding it per-ayanamsha
would be wasteful and is not required). The fix is **read-time derivation**: every query always
reads the stored tropical row (`WHERE ayanamsha_id = 'tropical'`), then derives the caller's
requested ayanamsha via `derive_sidereal(tropical_longitude, jd, ayanamsha_key)` (pyswisseph
`set_sid_mode` + `get_ayanamsa_ut`, noon-UT Julian day — matches how the row was stored) and returns
the **sidereal values as the primary field names**, not as a separate corroborating set.

### `ayanamsha_id` param (frozen)

```
ayanamsha_id?: string   // optional on every one of the 4 GET routes below.
                        // default: "lahiri_chitrapaksha"  (SIDEREAL-FIRST — never "tropical")
```

Canonical 5-value vocabulary (matches `routers/jaimini.py::_VALID_AYANAMSHAS` and TS
`registry/constants.ts::DEFAULT_AYANAMSHA`, the vocabulary already used for stored `chart_facts` /
`bodha_*` / `kala_*` / `phala_*` ayanamsha_id):

```
"lahiri_chitrapaksha" | "true_chitra" | "krishnamurti" | "raman" | "surya_siddhanta_classical"
```

`"tropical"` is still accepted **explicitly** (never the default). Any other value is a **422 /
`ok:false` error** carrying an `[EXTERNAL_COMPUTATION_REQUIRED]`-prefixed message listing the valid
set — never a silent fallback to tropical or to a different ayanamsha (B.10).

### Response shape — sidereal request (default or any of the 5 canonical ids)

Applies to `GET /brahmagyan/ephemeris/planet_position` (and the analogous per-row shape inside
`planet_transit`'s `rows[]` and `retrograde_periods`'s `stations[]`):

```jsonc
{
  "ok": true,
  "date": "2026-08-15",
  "ayanamsha_id": "lahiri_chitrapaksha",     // echoes the resolved request
  "positions": [
    {
      "body": "Venus",
      "longitude": 165.02...,                // PRIMARY — sidereal, degrees [0,360)
      "sign_number": 6,                       // PRIMARY — sidereal sign, 1=Aries..12=Pisces (Virgo=6)
      "degree_in_sign": 15.02...,             // PRIMARY — sidereal
      "nakshatra_number": 14,                 // sidereal-derived (was previously wrong under every ayanamsha)
      "pada": 2,
      "ayanamsha_offset": 24.15...,           // degrees subtracted from tropical to reach this sidereal value
      "is_retrograde": false,
      "speed_dps": 1.18...,
      "tropical_longitude": 189.17...,        // labelled EXTRA — never the primary field, never bare "longitude"
      "source_citation": "pyswisseph + Swiss Ephemeris .se1"
    }
  ],
  "count": 9,
  "provenance_envelope": { "...": "unchanged shape, ayanamsha_id now the resolved sidereal id" }
}
```

### Response shape — explicit `ayanamsha_id="tropical"` request

`sign_number`/`degree_in_sign` remain meaningful tropically (tropical sign is a real, if non-Vedic,
concept) and are served as before. **`nakshatra_number`/`pada` are suppressed** (nakshatra is
inherently sidereal — there is no honest "tropical nakshatra") and replaced with a `nakshatra_note`
explaining the omission. Never serve a tropical-derived nakshatra unlabelled.

```jsonc
{
  "ok": true,
  "ayanamsha_id": "tropical",
  "positions": [
    {
      "body": "Venus",
      "tropical_longitude": 188.565,
      "sign_number": 7,                       // tropical Libra — legitimately tropical, kept
      "degree_in_sign": 8.565,
      "nakshatra_number": null,
      "nakshatra_note": "nakshatra is an inherently sidereal division; omitted under ayanamsha_id='tropical' — request a sidereal ayanamsha_id to get nakshatra_number/pada.",
      "is_retrograde": false, "speed_dps": 1.18, "source_citation": "..."
    }
  ]
}
```

### `aspects` and `retrograde_periods` — invariance note

Angular differences between two bodies are **ayanamsha-invariant** (subtracting the same offset from
both longitudes preserves their difference), so `aspects[].aspect/exact_angle/actual_diff/orb` do
not change with `ayanamsha_id`. What changes is the **labelling** of the absolute longitudes
reported alongside each aspect (`longitude_b1`/`longitude_b2` become sidereal-primary, with
`tropical_longitude_b1`/`_b2` as labelled extras) — this was the leak: `ayanamsha_id` was accepted
but silently ignored for the reported absolute longitudes, and non-`'tropical'` values returned zero
rows due to the WHERE-filter bug above. Similarly, retrograde **station dates** are ayanamsha-
invariant (station is a speed-sign event); `stations[].sign_number` is now sidereal-primary with
`tropical_sign_number` retained as a labelled extra.

## Non-goals

- Does not change the `ephemeris_daily` table schema or storage convention (still tropical-only,
  additive-migration not required for this contract).
- Does not unify the THREE pre-existing, independent ayanamsha-key vocabularies in this codebase
  (this file's own `AYANAMSHA_MAP` build-time keys, `panchang_engine`/`pyjhora_adapter`'s short
  keys, and the canonical 5-value vocabulary this contract uses) — out of scope, logged as a residual
  in `BETA_C.md`.
- Does not address `ref_ephemeris_year_get` in this row (separate but same-class fix, documented in
  `BETA_C.md`'s EL-39 evidence block — γ.F does not consume that route per its stated need).

## Required α-side change (β cannot edit `platform/src/lib/retrieval/**`)

`query_planet_position.ts`'s handler already forwards `date`/`planet` as query params and passes the
sidecar JSON body through verbatim — so it inherits the new sidereal-first default **with zero
changes**. To let a caller request a specific ayanamsha (including explicit `tropical`), add to
`input_schema.properties`:

```ts
ayanamsha_id: {
  type: 'string',
  description: "Ayanamsha for sidereal derivation (default 'lahiri_chitrapaksha'). " +
    "One of lahiri_chitrapaksha|true_chitra|krishnamurti|raman|surya_siddhanta_classical, " +
    "or 'tropical' to request tropical coordinates explicitly (nakshatra suppressed under tropical).",
  enum: ['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical','tropical'],
},
```

and forward it in the handler: `if (ayanamsha_id) params.set('ayanamsha_id', ayanamsha_id)`. The
same two-line addition applies to `query_planet_transit.ts`, `query_aspects_at_time.ts`, and
`query_retrograde_periods.ts` (all three are pure pass-throughs with no `ayanamsha_id` param today —
none require any other change to pick up sidereal-first defaults). Also update the four
`description` strings, which currently say "tropical coordinates — subtract Lahiri ayanamsha to get
sidereal" / "tropical sign number" — this is now false and is the exact B.10 exposure EL-39 named.
