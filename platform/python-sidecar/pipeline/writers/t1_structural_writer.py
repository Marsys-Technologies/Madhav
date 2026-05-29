"""
t1_structural_writer.py — MARSYS-JIS A8 T1 Structural writer
A8-S1: Aspect matrix (Parashari + Jaimini Rasi-drishti) + Dispositor chains.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A8_t1_structural"
ASSET_LABEL = "T1 Structural Combinations"
ENGINE_VERSION = "natal_engine/0.2.0"

# ── Parashari aspect rules ────────────────────────────────────────────────────
# Maps graha_id -> list of house offsets (from graha's own house) it aspects.
# All classical grahas aspect the 7th. Mars adds 4th+8th. Jupiter adds 5th+9th.
# Saturn adds 3rd+10th. Rahu/Ketu follow Jupiter (5th+9th per most traditions).
PARASHARI_SPECIAL_ASPECTS = {
    "sun":     [],                 # 7th only (universal)
    "moon":    [],                 # 7th only
    "mars":    [4, 8],             # 4th + 8th special
    "mercury": [],                 # 7th only
    "jupiter": [5, 9],             # 5th + 9th special
    "venus":   [],                 # 7th only
    "saturn":  [3, 10],            # 3rd + 10th special
    "rahu":    [5, 9],             # 5th + 9th (Jupiter-like)
    "ketu":    [5, 9],             # 5th + 9th (Jupiter-like)
}

_ALL_GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

# ── Sign lords (Parashari) ────────────────────────────────────────────────────
SIGN_LORDS = {
    "aries":       "mars",
    "taurus":      "venus",
    "gemini":      "mercury",
    "cancer":      "moon",
    "leo":         "sun",
    "virgo":       "mercury",
    "libra":       "venus",
    "scorpio":     "mars",
    "sagittarius": "jupiter",
    "capricorn":   "saturn",
    "aquarius":    "saturn",
    "pisces":      "jupiter",
}

# ── Jaimini Rasi-drishti ──────────────────────────────────────────────────────
_MOVEABLE = ["aries", "cancer", "libra", "capricorn"]
_FIXED    = ["taurus", "leo", "scorpio", "aquarius"]
_DUAL     = ["gemini", "virgo", "sagittarius", "pisces"]

# Sign adjacency by index (0-based zodiac order)
_SIGN_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]
_SIGN_INDEX = {s: i for i, s in enumerate(_SIGN_ORDER)}


def _are_adjacent(sign_a: str, sign_b: str) -> bool:
    """True if sign_b is immediately before or after sign_a in the zodiac (circular)."""
    ia = _SIGN_INDEX[sign_a]
    ib = _SIGN_INDEX[sign_b]
    diff = abs(ia - ib)
    return diff == 1 or diff == 11  # circular adjacency


def _build_jaimini_drishti_pairs():
    """Return list of (from_sign, to_sign) where rasi-drishti applies."""
    pairs = []
    all_signs = _SIGN_ORDER

    for from_sign in all_signs:
        if from_sign in _MOVEABLE:
            targets = _FIXED
        elif from_sign in _FIXED:
            targets = _MOVEABLE
        else:  # dual
            targets = _DUAL

        for to_sign in targets:
            if to_sign == from_sign:
                continue
            if _are_adjacent(from_sign, to_sign):
                continue
            pairs.append((from_sign, to_sign))

    return pairs


_JAIMINI_PAIRS = _build_jaimini_drishti_pairs()


# ── Row helpers (mirror panchanga_writer_a4 pattern exactly) ──────────────────

def make_fact_id(category, subject, key, chart_id, ayanamsha_id, build_id):
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_citation_ref(category, subject, key, chart_id, ayanamsha_id):
    return (
        f"{category}.{subject}.{key}"
        f"@chart={chart_id[:8]}"
        f":ay={ayanamsha_id}"
        f":eng={ENGINE_VERSION}"
    )


def _row(
    chart_id, ayanamsha_id, build_id,
    fact_category, fact_subject, fact_key,
    value_text, value_number,
    citation_ref, citation_human,
    source_calc,
):
    fact_id = make_fact_id(fact_category, fact_subject, fact_key, chart_id, ayanamsha_id, build_id)
    provenance = json.dumps({
        "writer": "t1_structural_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,            # category (legacy col — mirrors fact_category)
        "D1",                     # divisional_chart
        "t1_structural_writer",   # source_section
        provenance,
        fact_category, fact_subject, fact_key,
        value_text, value_number,
        citation_ref, citation_human,
        source_calc,
        "single",                 # verification_pass_status
        ENGINE_VERSION,
        datetime.now(timezone.utc).isoformat(),  # computed_at_iso
    )


_INSERT_SQL = """
INSERT INTO chart_facts
  (fact_id, chart_id, ayanamsha_id, build_id,
   category, divisional_chart, source_section, provenance,
   fact_category, fact_subject, fact_key,
   value_text, value_number,
   citation_ref, citation_human,
   source_calculation, verification_pass_status,
   engine_version, computed_at_iso)
VALUES %s
ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
DO UPDATE SET
  value_text = EXCLUDED.value_text,
  value_number = EXCLUDED.value_number,
  computed_at_iso = EXCLUDED.computed_at_iso
"""


def _upsert_chart_facts(conn, rows):
    from psycopg2.extras import execute_values
    execute_values(conn, _INSERT_SQL, rows)


# ── Parashari aspect computation ──────────────────────────────────────────────

def _compute_parashari_aspects(chart_id, ayanamsha_id, build_id, planets):
    """
    For each graha, compute which houses it aspects and store one row per
    (graha, aspected_house).  Universal 7th-house aspect + special aspects.
    """
    rows = []

    for graha_id in _ALL_GRAHAS:
        planet = planets.get(graha_id)
        if planet is None:
            continue

        graha_house = planet.get("house")
        if graha_house is None:
            continue

        special_offsets = PARASHARI_SPECIAL_ASPECTS.get(graha_id, [])
        # Build full set of aspected houses: universal 7th + specials
        aspected = {}

        # Universal 7th aspect
        seventh = ((graha_house - 1 + 6) % 12) + 1
        aspected[seventh] = "full_aspect"

        # Special aspects
        for offset in special_offsets:
            house_num = ((graha_house - 1 + offset - 1) % 12) + 1
            label = f"special_{offset}th"
            aspected[house_num] = label

        for house_num, aspect_type in aspected.items():
            cref = make_citation_ref(
                "aspect_matrix_parashari", graha_id,
                f"aspected_house_{house_num}", chart_id, ayanamsha_id,
            )
            rows.append(_row(
                chart_id, ayanamsha_id, build_id,
                "aspect_matrix_parashari",
                graha_id,
                f"aspected_house_{house_num}",
                aspect_type,
                1.0,
                cref,
                "BPHS Ch 26",
                "t1_structural_writer/parashari_aspects",
            ))

    return rows


# ── Jaimini Rasi-drishti computation ─────────────────────────────────────────

def _compute_jaimini_rasi_drishti(chart_id, ayanamsha_id, build_id, planets):
    """
    Store Jaimini rasi-drishti pairs.  Static — does not depend on chart_output
    planet positions, but is stored chart-scoped for retrieval convenience.
    """
    rows = []

    for from_sign, to_sign in _JAIMINI_PAIRS:
        fact_key = f"rasi_drishti_{to_sign}"
        cref = make_citation_ref(
            "aspect_matrix_jaimini", from_sign, fact_key, chart_id, ayanamsha_id,
        )
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "aspect_matrix_jaimini",
            from_sign,
            fact_key,
            "rasi_drishti",
            1.0,
            cref,
            "Jaimini Sutras 1.1.28",
            "t1_structural_writer/jaimini_rasi_drishti",
        ))

    return rows


# ── Dispositor chain computation ──────────────────────────────────────────────

def _dispositor_chain(graha_id: str, planets: dict) -> list:
    """
    Walk the dispositor chain from graha_id until a cycle is detected.
    Returns the chain including the start graha, e.g. ['mars', 'saturn', 'saturn'].
    """
    chain = [graha_id]
    visited = {graha_id}
    current = graha_id

    for _ in range(20):  # safety cap
        planet = planets.get(current)
        if planet is None:
            break
        sign = planet.get("sign", "").lower()
        lord = SIGN_LORDS.get(sign)
        if lord is None:
            break
        chain.append(lord)
        if lord in visited:
            break
        visited.add(lord)
        current = lord

    return chain


def _compute_dispositor_chains(chart_id, ayanamsha_id, build_id, planets):
    rows = []

    for graha_id in _ALL_GRAHAS:
        if graha_id not in planets:
            continue

        chain = _dispositor_chain(graha_id, planets)
        if len(chain) < 2:
            continue

        chain_str = "→".join(chain)
        final = chain[-1]
        chain_length = len(chain) - 1  # exclude start graha

        # chain row
        cref_chain = make_citation_ref(
            "dispositor_chain", graha_id, "dispositor_chain", chart_id, ayanamsha_id,
        )
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "dispositor_chain",
            graha_id,
            "dispositor_chain",
            chain_str,
            float(chain_length),
            cref_chain,
            "BPHS Ch 41 (dispositor theory)",
            "t1_structural_writer/dispositor_chain",
        ))

        # final dispositor row
        cref_final = make_citation_ref(
            "dispositor_chain", graha_id, "final_dispositor", chart_id, ayanamsha_id,
        )
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "dispositor_chain",
            graha_id,
            "final_dispositor",
            final,
            None,
            cref_final,
            "BPHS Ch 41 (dispositor theory)",
            "t1_structural_writer/dispositor_chain",
        ))

    return rows


# ── Public entry point ────────────────────────────────────────────────────────

def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Write A8-S1: aspect matrix (Parashari + Jaimini) + dispositor chains to
    chart_facts.  Returns the number of rows written.
    """
    planet_list = chart_output.get("planets", [])
    if not planet_list:
        logger.info(
            "[T1] %s: no planets in chart_output — 0 rows written "
            "(chart=%s ayanamsha=%s build=%s)",
            ASSET_LABEL, chart_id, ayanamsha_id, build_id,
        )
        return 0

    planets = {p["id"]: p for p in planet_list}

    rows = []
    rows.extend(_compute_parashari_aspects(chart_id, ayanamsha_id, build_id, planets))
    rows.extend(_compute_jaimini_rasi_drishti(chart_id, ayanamsha_id, build_id, planets))
    rows.extend(_compute_dispositor_chains(chart_id, ayanamsha_id, build_id, planets))

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[T1] %s: %d rows written (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
