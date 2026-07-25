---
contract_id: C4
title: house/sign convention + estate-safety normalisation
version: 1.0
status: FROZEN
authored_by: Stream β (elev/beta), lane D — investigation-required ruling (charter M2.4)
consumers:
  - Stream α — serving-gate enforcement (α.K1 convention gate) + estate-safety normalisation
  - Stream γ — planner/assessor primitives that count houses from a (varga) lagna
owner: β
grounded_in:
  - platform/python-sidecar/ga_writers/ga_sensitive_writer.py:309 (_house_d1 — the defect + fix)
  - platform/python-sidecar/ga_writers/ga_sensitive_writer.py:1434,1470,1570 (arudha/bhava_arudha house_d1 emit)
  - platform/python-sidecar/ga_writers/ga_vargas_writer.py:845 (varga_position keys; house was None — EL-47)
  - platform/python-sidecar/ga_writers/ga_structural_writer.py:4390 (_load_special_points reads house_d1 as house — blast radius)
  - platform/python-sidecar/ga_writers/ga_positions_writer.py (graha_position.house — already correct whole-sign, the reference convention)
live_evidence: chart 482012f1 (Abhisek, lagna 12.43° Aries), lahiri_chitrapaksha, probed 2026-07-25
---

# C4 — house/sign convention + estate-safety normalisation

## Problem this closes (EL-30, EL-47)

`house_*` fields in `chart_facts` did not follow one convention:

- **`graha_position.house` was already correct** whole-sign (SUN Capricorn→10,
  MOON Aquarius→11, MAR/SAT Libra→7 from an Aries lagna). This is the reference.
- **`arudha_pada.house_d1` / `bhava_arudha.house_d1` (and every other
  `_house_d1` consumer in `ga_sensitive_writer`: upagraha, karaka_chara) were
  WRONG.** `_house_d1` computed a **degree-arc** count
  `int((long − lagna) % 360 / 30) + 1`, which silently disagrees with whole-sign
  counting whenever the lagna sits mid-sign. Live on 482012f1 (lagna 12.43°
  Aries): ARUDHA_A1 Capricorn served `house_d1=9` (true 10), A7 Aquarius `=10`
  (true 11), A10 Aries at 0° served `=12` (true 1 — the "0° wraparound" that fit
  NEITHER a house nor a sign-index convention). All one defect: arc-count, not
  whole-sign-count.
- **`varga_position` served `house: null`** — the house-from-varga-lagna was left
  for the consumer to derive client-side (EL-47, a §N.5/B.10 exposure).

## The ONE convention (frozen)

1. **A field named `house_*` is a WHOLE-SIGN house counted from the relevant
   lagna, 1-indexed, range 1..12.** For D1 fields the lagna is the D1 (rasi)
   lagna; for a varga field it is that varga's own lagna. The lagna's sign is
   always house 1.
   Formula: `house = ((body_sign_idx − lagna_sign_idx) mod 12) + 1`, where
   `sign_idx = floor(longitude_sidereal / 30)`, Aries=0 … Pisces=11.
2. **A field named `house_*` MUST NEVER hold a sign index, a degree-arc count, or
   a 0-indexed value.** Bhava-chalit (unequal/cusp houses) lives in its own
   `house_chalit` category and is never conflated with `house_*`.
3. **Signs are 1..12 Aries-origin** (`sign_id = sign_idx + 1`), and a `sign`
   text field carries the sign NAME. Sign fields never hold a house.

## Field inventory governed by C4

| category | key | convention after β.D | marker |
|---|---|---|---|
| `arudha_pada` | `house_d1` | whole-sign from D1 lagna | `formula_id` stamp (below) |
| `bhava_arudha` | `house_d1` | whole-sign from D1 lagna | `formula_id` stamp |
| `varga_position` | `house_from_varga_lagna` | whole-sign from varga lagna | key-name is self-marking (new) |
| `graha_position` | `house` | whole-sign from D1 lagna (already correct) | — reference |

Note: `upagraha_position`, `karaka_chara_position` and other `_house_d1`
consumers in `ga_sensitive_writer` inherit the corrected `_house_d1` at rebuild;
their `house_d1` is now whole-sign but is NOT `formula_id`-stamped in v1.0 (only
the two EL-30-named arudha categories are). Serving MUST treat any `house_*` row
lacking the v2 marker under the estate-safety fallback (§Estate safety).

## Estate safety — MANDATORY normalisation (charter red-team finding #2)

β rebuilds only the two canonical charts; the other ~5,564 prod subjects keep
legacy degree-arc `house_d1` rows. **Chosen mitigation: (a) per-row convention
tag + serving normalisation by tag.** β's responsibility (writer output) is DONE;
α's responsibility (the consuming half) is specified here precisely:

**Writer output (β — shipped):**
- `arudha_pada.house_d1` and `bhava_arudha.house_d1` rows are stamped
  `chart_facts.formula_id = "wholesign_from_lagna:1indexed:v2"`
  (constant `HOUSE_CONVENTION_ID`, ga_sensitive_writer.py).
- `varga_position` emits a NEW key `house_from_varga_lagna`. The key exists ONLY
  on convention-corrected rows — there is no legacy `house_from_varga_lagna` to
  confuse it with, so it is self-marking and serving may trust it unconditionally.
- **The `sign` (name) and `sign_id` of every row — legacy and rebuilt — are
  correct.** This is the load-bearing fact for the fallback.

**Serving normalisation (α — to implement):**
For any `house_*` row α serves:
1. If the row carries `formula_id = "wholesign_from_lagna:1indexed:v2"`, OR its
   key is `house_from_varga_lagna`, OR the category is `graha_position` (already
   whole-sign) → **serve the stored value as-is.**
2. Otherwise the row predates the fix (legacy degree-arc). **α MUST re-derive the
   house from the row's own `sign` field** (which is present and correct) using
   `((sign_idx − lagna_sign_idx) mod 12) + 1`, where `lagna_sign_idx` is the
   sign of that chart's lagna (D1 for `house_d1`; the varga lagna for varga
   rows). Never serve the raw legacy `house_d1` integer.
This keeps every non-rebuilt estate chart reading correct houses without a
full-estate rebuild.

**α.K1 convention gate:** assert that no served `house_*` value exceeds [1,12],
and that for stamped/rebuilt rows `house == ((sign_idx − lagna_sign_idx) mod 12)
+ 1` for the row's own sign. A `house_*` row whose value equals a raw sign index
(fails the derivation) fails the gate.

## Proof captured (β.D ledger)

- Canonical rebuild (482012f1, 1c826d5a): A1→10, A7→11, A10→1; varga rows carry
  `house_from_varga_lagna` matching sign arithmetic.
- Third chart `acdf0d66-…` (Arunima, non-canonical, NOT rebuilt): its
  `arudha_pada` rows are untouched (before==after), lack the v2 stamp, and carry
  correct `sign` values — i.e. α's fallback derivation reconstructs her houses
  correctly. Evidence blocks in
  `00_ARCHITECTURE/llm_consumption_audit/ledgers/BETA_D.md`.

## Non-goals
- Does NOT change `graha_position.house` (already correct) or `house_chalit`.
- Does NOT itself implement α's serving normalisation — it freezes the contract
  α builds the consuming half against.
- The EL-38 argala matrix is sign-indexed by design; its house-from-lagna
  resolution is an α.B serving concern, not a C4 writer field.
