"""
brahmagyan.l0_vastu_directions — Astrovastu Gate-1 L0 Brahmagyan seed
=======================================================================

Seeds two L0 static reference tables:
  bg_vastu_directions           — 8 compass directions with ruling graha, element,
                                   color, and classical citation (Mayamata Ch.6)
  bg_vastu_direction_remedials  — 2–3 Vastu remedies per direction (~22 rows)

Volume floors:
  bg_vastu_directions:          8 rows (one per compass direction)
  bg_vastu_direction_remedials: >= 16 rows (min 2 per direction)

All rows carry classical_citation — no row is citationless.

Sources: Vastu Shastra (Mayamata Ch.6), Brihat Samhita Ch.53.

Idempotency: L0 pattern — ON CONFLICT (direction) DO UPDATE / ON CONFLICT DO NOTHING.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── Citations ─────────────────────────────────────────────────────────────────

MAYAMATA_CH6 = "Vastu Shastra (Mayamata Ch.6)"
BRIHAT_SAMHITA_CH53 = "Brihat Samhita Ch.53 (Vastu-vidya)"
VASTU_TRADITION = "Vastu Shastra tradition (Nairitya corner)"
VASTU_TRAD_GENERAL = "Vastu Shastra tradition"

# ── Direction seed data ────────────────────────────────────────────────────────

VASTU_DIRECTIONS = [
    {
        "direction": "North",
        "direction_deg": 0,
        "ruling_graha": "Mercury",
        "secondary_graha": None,
        "favorable_color": "Green",
        "element": "Water",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "South",
        "direction_deg": 180,
        "ruling_graha": "Mars",
        "secondary_graha": None,
        "favorable_color": "Red",
        "element": "Fire",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "East",
        "direction_deg": 90,
        "ruling_graha": "Sun",
        "secondary_graha": None,
        "favorable_color": "Orange/Gold",
        "element": "Fire",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "West",
        "direction_deg": 270,
        "ruling_graha": "Saturn",
        "secondary_graha": None,
        "favorable_color": "Grey/Black",
        "element": "Air",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "Northeast",
        "direction_deg": 45,
        "ruling_graha": "Jupiter",
        "secondary_graha": None,
        "favorable_color": "Yellow",
        "element": "Ether",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "Southeast",
        "direction_deg": 135,
        "ruling_graha": "Venus",
        "secondary_graha": None,
        "favorable_color": "White/Pink",
        "element": "Fire",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "Northwest",
        "direction_deg": 315,
        "ruling_graha": "Moon",
        "secondary_graha": None,
        "favorable_color": "White/Silver",
        "element": "Air",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "Southwest",
        "direction_deg": 225,
        "ruling_graha": "Rahu",
        "secondary_graha": None,
        "favorable_color": None,
        "element": "Earth",
        "classical_citation": VASTU_TRADITION,
    },
]

# ── Remedial seed data ────────────────────────────────────────────────────────

VASTU_DIRECTION_REMEDIALS = [
    # North (Mercury/Water)
    {
        "direction": "North",
        "remedy_type": "color",
        "remedy_description": "Use green or blue tones in north-facing rooms to strengthen Mercury energy",
        "classical_citation": BRIHAT_SAMHITA_CH53,
    },
    {
        "direction": "North",
        "remedy_type": "symbol",
        "remedy_description": "Place a Kuber yantra or water feature in the north zone to activate prosperity",
        "classical_citation": VASTU_TRAD_GENERAL,
    },
    {
        "direction": "North",
        "remedy_type": "material",
        "remedy_description": "Use light metals or glass in north walls to enhance Water element conductivity",
        "classical_citation": MAYAMATA_CH6,
    },
    # South (Mars/Fire)
    {
        "direction": "South",
        "remedy_type": "color",
        "remedy_description": "Use red or earthy tones in south zone to honour Mars rulership and protect against loss",
        "classical_citation": BRIHAT_SAMHITA_CH53,
    },
    {
        "direction": "South",
        "remedy_type": "symbol",
        "remedy_description": "Place a triangular Yantra or Mangal image in south to stabilise aggressive Mars energy",
        "classical_citation": VASTU_TRAD_GENERAL,
    },
    {
        "direction": "South",
        "remedy_type": "space",
        "remedy_description": "Keep south zone heavier and closed; avoid large windows or open gates in this direction",
        "classical_citation": MAYAMATA_CH6,
    },
    # East (Sun/Fire)
    {
        "direction": "East",
        "remedy_type": "space",
        "remedy_description": "Keep east zone open and well-lit; sunrise energy strengthens vitality and authority (Sun domain)",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "East",
        "remedy_type": "color",
        "remedy_description": "Use orange or golden hues in east-facing spaces to amplify solar Agni quality",
        "classical_citation": BRIHAT_SAMHITA_CH53,
    },
    {
        "direction": "East",
        "remedy_type": "symbol",
        "remedy_description": "Place Surya image or copper vessel in east to invoke solar blessings",
        "classical_citation": VASTU_TRAD_GENERAL,
    },
    # West (Saturn/Air)
    {
        "direction": "West",
        "remedy_type": "color",
        "remedy_description": "Use grey, indigo, or black in west zone; Saturn governs discipline and karma here",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "West",
        "remedy_type": "symbol",
        "remedy_description": "Place iron objects or Shani yantra in west to balance Saturn energy constructively",
        "classical_citation": BRIHAT_SAMHITA_CH53,
    },
    {
        "direction": "West",
        "remedy_type": "space",
        "remedy_description": "West zone may bear heavier structural loads; Saturn prefers weight and stability",
        "classical_citation": VASTU_TRAD_GENERAL,
    },
    # Northeast (Jupiter/Ether)
    {
        "direction": "Northeast",
        "remedy_type": "space",
        "remedy_description": "Keep northeast (Ishanya) zone clean, open, and free of heavy objects; Jupiter and Ether require lightness",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "Northeast",
        "remedy_type": "color",
        "remedy_description": "Use yellow or gold in northeast puja or meditation space to amplify Guru (Jupiter) grace",
        "classical_citation": BRIHAT_SAMHITA_CH53,
    },
    {
        "direction": "Northeast",
        "remedy_type": "symbol",
        "remedy_description": "Install a puja room or sacred space in northeast; this is the divine corner per Vastu tradition",
        "classical_citation": VASTU_TRAD_GENERAL,
    },
    # Southeast (Venus/Fire)
    {
        "direction": "Southeast",
        "remedy_type": "function",
        "remedy_description": "Place kitchen (fire/Agni zone) in southeast; Venus and Fire element converge here",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "Southeast",
        "remedy_type": "color",
        "remedy_description": "Use white, pink, or cream tones in southeast to harmonise Venus energy and prevent conflicts",
        "classical_citation": BRIHAT_SAMHITA_CH53,
    },
    {
        "direction": "Southeast",
        "remedy_type": "symbol",
        "remedy_description": "Place Shukra yantra or rose quartz in southeast to strengthen relationships and wealth",
        "classical_citation": VASTU_TRAD_GENERAL,
    },
    # Northwest (Moon/Air)
    {
        "direction": "Northwest",
        "remedy_type": "function",
        "remedy_description": "Northwest suits storage rooms, guest rooms, or granaries; Moon governs transitory stays",
        "classical_citation": MAYAMATA_CH6,
    },
    {
        "direction": "Northwest",
        "remedy_type": "color",
        "remedy_description": "Use white or silver tones in northwest to align with lunar energy and invite calm emotions",
        "classical_citation": BRIHAT_SAMHITA_CH53,
    },
    {
        "direction": "Northwest",
        "remedy_type": "symbol",
        "remedy_description": "Place a silver bowl of water or Chandra yantra in northwest to stabilise Moon influence",
        "classical_citation": VASTU_TRAD_GENERAL,
    },
    # Southwest (Rahu/Earth)
    {
        "direction": "Southwest",
        "remedy_type": "space",
        "remedy_description": "Keep southwest (Nairitya) zone heavy, closed, and structurally solid; Rahu/Earth demands stability",
        "classical_citation": VASTU_TRADITION,
    },
    {
        "direction": "Southwest",
        "remedy_type": "color",
        "remedy_description": "Use earthy tones — brown, terracotta — in southwest to ground Rahu energy and prevent instability",
        "classical_citation": BRIHAT_SAMHITA_CH53,
    },
    {
        "direction": "Southwest",
        "remedy_type": "symbol",
        "remedy_description": "Avoid toilets or water bodies in southwest; place heavy furniture or master bedroom here to suppress negative Nairitya influence",
        "classical_citation": MAYAMATA_CH6,
    },
]


# ── Seed function ─────────────────────────────────────────────────────────────

def seed_vastu_directions(
    conn,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = False,
) -> dict[str, int]:
    """Seed bg_vastu_directions and bg_vastu_direction_remedials.

    Returns a dict with row counts keyed by table name.
    If dry_run=True, returns expected counts without writing to DB.
    """
    if dry_run:
        return {
            "bg_vastu_directions": len(VASTU_DIRECTIONS),
            "bg_vastu_direction_remedials": len(VASTU_DIRECTION_REMEDIALS),
        }

    counts: dict[str, int] = {
        "bg_vastu_directions": 0,
        "bg_vastu_direction_remedials": 0,
    }

    with conn.cursor() as cur:
        # ── bg_vastu_directions — ON CONFLICT (direction) DO UPDATE ─────────
        for row in VASTU_DIRECTIONS:
            cur.execute(
                """
                INSERT INTO bg_vastu_directions
                    (direction, direction_deg, ruling_graha, secondary_graha,
                     favorable_color, element, classical_citation)
                VALUES
                    (%(direction)s, %(direction_deg)s, %(ruling_graha)s, %(secondary_graha)s,
                     %(favorable_color)s, %(element)s, %(classical_citation)s)
                ON CONFLICT (direction) DO UPDATE SET
                    direction_deg      = EXCLUDED.direction_deg,
                    ruling_graha       = EXCLUDED.ruling_graha,
                    secondary_graha    = EXCLUDED.secondary_graha,
                    favorable_color    = EXCLUDED.favorable_color,
                    element            = EXCLUDED.element,
                    classical_citation = EXCLUDED.classical_citation
                """,
                row,
            )
            counts["bg_vastu_directions"] += 1

        # ── bg_vastu_direction_remedials — ON CONFLICT DO NOTHING ───────────
        for row in VASTU_DIRECTION_REMEDIALS:
            cur.execute(
                """
                INSERT INTO bg_vastu_direction_remedials
                    (direction, remedy_type, remedy_description, classical_citation)
                VALUES
                    (%(direction)s, %(remedy_type)s, %(remedy_description)s, %(classical_citation)s)
                ON CONFLICT (direction, remedy_type) DO NOTHING
                """,
                row,
            )
            counts["bg_vastu_direction_remedials"] += 1

        if autocommit:
            conn.commit()

    logger.info(
        "bg_vastu_directions seeded: %d directions, %d remedials",
        counts["bg_vastu_directions"],
        counts["bg_vastu_direction_remedials"],
    )
    return counts
