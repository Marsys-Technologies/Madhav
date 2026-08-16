"""
brahmagyan.l0_dignity_reference — L0 Brahmagyan dignity degree table.

Single, dependency-free source of the classical exaltation / debilitation /
moolatrikona / own-sign reference data for the 9 grahas (7 classical planets +
Rahu/Ketu). Stdlib-only, imports nothing from `pipeline.orchestrator.*` or any
other writer-layer module — matching the established `brahmagyan/l0_*` family
convention (`l0_class_priors.py`, `l0_class_lifetime_counts.py`,
`l0_dasha_systems.py`, `l0_doshas.py`, `l0_formula_constants.py`,
`l0_ephemeris.py`) that every other L0 reference writer already follows.

Extracted from `pipeline/orchestrator/writers/bg_dignity_reference.py` per
PRATINIDHI ruling PAR-R-6 (`00_ARCHITECTURE/briefs/parisesa/LEDGER_PRATINIDHI.md`,
`par/pratinidhi-ledger`): `bg_dignity_reference.py` holding this data inline
(rather than importing it, like its six siblings) was the anomaly, not the
FROZEN-contract-conforming norm — extraction touches none of the five
WriterBase contract points (`@register`, `run(ctx)`, `ctx.db_conn`,
`_telemetry`/`asset_throughput`, `ctx.config`).

Consumers:
  - `pipeline/orchestrator/writers/bg_dignity_reference.py` — the L0 writer
    that seeds the `bg_dignity_reference` DB table (migration
    `250_bg_dignity_reference.sql`) from this data at build time.
  - `brahmagyan/dignity_oracle.py` — the B-01 shared dignity classifier
    (`classify_dignity`) that every L1+ dignity consumer imports, serving-side.

Classical sources: BPHS Ch.3 (Brihat Parashara Hora Shastra) for all 9 rows.
Rahu/Ketu exaltation is the Parashari-mainstream position (Taurus/Scorpio);
`RAHU_VARIANT_TRADITIONS` / `KETU_VARIANT_TRADITIONS` record the documented
minority alternatives with source-authority tagging (SP-1: disclose, don't
silently pick a side).

Single source of truth: any edit to a graha's dignity data belongs here, and
only here — `bg_dignity_reference.py` and `dignity_oracle.py` both read this
module rather than holding their own copies (§N.7 item 3: "no wrapper-local
constant may shadow an L1-computed value, even when the constant's current
value happens to be correct — a constant can drift from its source; a
reference cannot"). The one remaining seam this does NOT close is Python vs.
the seeded DB rows (migration 250) — that seam needs its own detector
(see `brahmagyan/__tests__/test_dignity_oracle.py`
`test_data_matches_bg_dignity_reference_source_of_truth`, re-pointed at this
module per PAR-R-6).
"""
from __future__ import annotations

import json
from typing import Any

# ── Source citations ───────────────────────────────────────────────────────────

BPHS_CH3 = "BPHS Ch.3"

# ── Variant-traditions disclosure data ────────────────────────────────────────
# SOURCE-AUTHORITY-WEIGHTED model: the canonical exaltation_sign is the BPHS-
# primary value at full confidence (1.0). variant_traditions records documented
# alternative positions with explicit authority tagging so downstream consumers
# can display the disagreement without diluting the BPHS reading.
# Populated only for Rahu/Ketu — the only grahas with documented tradition
# disagreement on exaltation sign.

RAHU_VARIANT_TRADITIONS = json.dumps([
    {
        "sign": "Taurus",
        "source": "BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali",
        "authority": "primary",
        "label": "Parashari mainstream",
    },
    {
        "sign": "Gemini",
        "source": "Kerala Jyotish tradition (commentators in the Harihara / Prashna Marga lineage)",
        "authority": "minority",
        "label": "Kerala school",
    },
    {
        "sign": None,
        "source": "Some modern scholars omit nodal exaltation doctrine entirely",
        "authority": "minority",
        "label": "Exclusionist position",
    },
])

KETU_VARIANT_TRADITIONS = json.dumps([
    {
        "sign": "Scorpio",
        "source": "BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — reverse of Rahu",
        "authority": "primary",
        "label": "Parashari mainstream",
    },
    {
        "sign": "Sagittarius",
        "source": "Kerala Jyotish tradition — reverse of Gemini-Rahu position",
        "authority": "minority",
        "label": "Kerala school",
    },
    {
        "sign": None,
        "source": "Some modern scholars omit nodal exaltation doctrine entirely",
        "authority": "minority",
        "label": "Exclusionist position",
    },
])

# ── bg_dignity_reference (9 rows) ─────────────────────────────────────────────
# Columns: graha, exaltation_sign, exaltation_degree, debilitation_sign,
#          debilitation_degree, moolatrikona_sign, moolatrikona_from,
#          moolatrikona_to, own_signs (list), classical_citation, notes

DIGNITY_REFERENCE: list[dict[str, Any]] = [
    {
        "graha": "Sun",
        "exaltation_sign": "Aries",       "exaltation_degree": 10,
        "debilitation_sign": "Libra",      "debilitation_degree": 10,
        "moolatrikona_sign": "Leo",        "moolatrikona_from": 0,  "moolatrikona_to": 20,
        "own_signs": ["Leo"],
        "classical_citation": BPHS_CH3,  "notes": None,
        "variant_traditions": None,
    },
    {
        "graha": "Moon",
        "exaltation_sign": "Taurus",       "exaltation_degree": 3,
        "debilitation_sign": "Scorpio",    "debilitation_degree": 3,
        "moolatrikona_sign": "Taurus",     "moolatrikona_from": 4,  "moolatrikona_to": 30,
        "own_signs": ["Cancer"],
        "classical_citation": BPHS_CH3,  "notes": None,
        "variant_traditions": None,
    },
    {
        "graha": "Mars",
        "exaltation_sign": "Capricorn",    "exaltation_degree": 28,
        "debilitation_sign": "Cancer",     "debilitation_degree": 28,
        "moolatrikona_sign": "Aries",      "moolatrikona_from": 0,  "moolatrikona_to": 12,
        "own_signs": ["Aries", "Scorpio"],
        "classical_citation": BPHS_CH3,  "notes": None,
        "variant_traditions": None,
    },
    {
        "graha": "Mercury",
        "exaltation_sign": "Virgo",        "exaltation_degree": 15,
        "debilitation_sign": "Pisces",     "debilitation_degree": 15,
        "moolatrikona_sign": "Virgo",      "moolatrikona_from": 16, "moolatrikona_to": 20,
        "own_signs": ["Gemini", "Virgo"],
        "classical_citation": BPHS_CH3,  "notes": None,
        "variant_traditions": None,
    },
    {
        "graha": "Jupiter",
        "exaltation_sign": "Cancer",       "exaltation_degree": 5,
        "debilitation_sign": "Capricorn",  "debilitation_degree": 5,
        "moolatrikona_sign": "Sagittarius","moolatrikona_from": 0,  "moolatrikona_to": 10,
        "own_signs": ["Sagittarius", "Pisces"],
        "classical_citation": BPHS_CH3,  "notes": None,
        "variant_traditions": None,
    },
    {
        "graha": "Venus",
        "exaltation_sign": "Pisces",       "exaltation_degree": 27,
        "debilitation_sign": "Virgo",      "debilitation_degree": 27,
        "moolatrikona_sign": "Libra",      "moolatrikona_from": 0,  "moolatrikona_to": 15,
        "own_signs": ["Taurus", "Libra"],
        "classical_citation": BPHS_CH3,  "notes": None,
        "variant_traditions": None,
    },
    {
        "graha": "Saturn",
        "exaltation_sign": "Libra",        "exaltation_degree": 20,
        "debilitation_sign": "Aries",      "debilitation_degree": 20,
        "moolatrikona_sign": "Aquarius",   "moolatrikona_from": 0,  "moolatrikona_to": 20,
        "own_signs": ["Capricorn", "Aquarius"],
        "classical_citation": BPHS_CH3,  "notes": None,
        "variant_traditions": None,
    },
    {
        "graha": "Rahu",
        "exaltation_sign": "Taurus",       "exaltation_degree": None,
        "debilitation_sign": "Scorpio",    "debilitation_degree": None,
        "moolatrikona_sign": None,         "moolatrikona_from": None, "moolatrikona_to": None,
        "own_signs": [],
        "classical_citation": "BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — Parashari consensus: Taurus",
        "notes": "Taurus exaltation per Parashari mainstream (BPHS/Phaladeepika/Saravali/JH/PL); Gemini is a minority Kerala school position",
        "variant_traditions": RAHU_VARIANT_TRADITIONS,
    },
    {
        "graha": "Ketu",
        "exaltation_sign": "Scorpio",      "exaltation_degree": None,
        "debilitation_sign": "Taurus",     "debilitation_degree": None,
        "moolatrikona_sign": None,         "moolatrikona_from": None, "moolatrikona_to": None,
        "own_signs": [],
        "classical_citation": "BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — reverse of Rahu",
        "notes": "Scorpio exaltation per Parashari mainstream; Sagittarius is a minority Kerala school position",
        "variant_traditions": KETU_VARIANT_TRADITIONS,
    },
]
