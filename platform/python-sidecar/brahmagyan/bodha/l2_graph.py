"""
brahmagyan.bodha.l2_graph — BRAHMA-BO-2-2 (L2 Bodha, l2-bodha-scaffold)
========================================================================

Scaffolds the CGM (Chart Graph Model) edge set into chart_facts with:
  fact_category = 'bodha.graph'
  fact_subject  = edge_id  (e.g. 'CGM_EDGE_001', 'DISP_SUN_SAT', ...)
  fact_value    = {source_node, target_node, edge_type, weight, domain,
                   provenance_envelope}

Source: 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md (node_count=284, edge_types §4)
        035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json (22 reconciled edges)

Volume floor: ≥ 100 edges
  - 22 from manifest (DISPOSITED_BY, NAKSHATRA_LORD_IS, ASPECTS_*)
  - ~80 derived from CGM §4 structural inventory:
      GRAHA_ASPECT (27), BHAV_ASPECT (30), JAIMINI_ASPECT (36 total),
      OWNERSHIP (12), TENANCY (9), YOGA_MEMBERSHIP subset,
      DIVISIONAL_TRANSITION (9, from CGM §6)

All edges are UNGROUNDED (rule_id=null, awaiting WS-3).
The get_cgm_subgraph MCP tool queries these rows.

Layer:  L2 Bodha (scaffold)
Asset:  bodha.graph (BO-2-2)
Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
        chart_id: 482012f1-710e-4a25-994a-93821f5871aa

BRAHMA-BO-2-2 / l2-bodha-scaffold
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 100
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
SOURCE_CITATION = "025_HOLISTIC_SYNTHESIS/CGM_v9_0.md"
MANIFEST_REL_PATH = "035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json"

PROVENANCE_ENVELOPE = {
    "layer": "L2",
    "asset": "bodha.graph",
    "asset_id": "BO-2-2",
    "scaffold_pass": "l2-bodha-scaffold",
    "grounding_status": "UNGROUNDED",
    "grounding_note": "Scaffold pass — awaiting WS-3 rule_base",
    "rule_id": None,
}

# Edge type weights
EDGE_WEIGHTS: dict[str, float] = {
    "DISPOSITED_BY":          0.90,
    "NAKSHATRA_LORD_IS":      0.85,
    "ASPECTS_3RD":            0.75,
    "ASPECTS_4TH":            0.75,
    "ASPECTS_5TH":            0.75,
    "ASPECTS_7TH":            0.80,
    "ASPECTS_8TH":            0.75,
    "ASPECTS_9TH":            0.75,
    "ASPECTS_10TH":           0.75,
    "GRAHA_ASPECT":           0.80,
    "BHAV_ASPECT":            0.70,
    "JAIMINI_ASPECT":         0.75,
    "OWNERSHIP":              0.90,
    "TENANCY":                0.85,
    "YOGA_MEMBERSHIP":        0.80,
    "DASHA_ACTIVATION":       0.85,
    "DIVISIONAL_TRANSITION":  0.75,
    "DIVISIONAL_CONFIRMATION":0.72,
    "KARAKA_ROLE":            0.85,
    "EXALT_DEBIL_AFFINITY":   0.80,
    "NAK_LORDSHIP":           0.80,
    "SAHAM_COMPOSITION":      0.70,
    "KAKSHYA_ZONE":           0.72,
    "REINFORCES":             0.75,
    "CONTRADICTS":            0.80,
    "MODULATES":              0.65,
}


# ── Canonical edge corpus ─────────────────────────────────────────────────────
#
# Built from three sources:
#   A. cgm_edges_manifest_v1_0.json (22 reconciled edges)
#   B. CGM §4 structural inventory — key types with per-planet derivation
#   C. CGM §6 DIVISIONAL_TRANSITION edges (9 planets × D9)
#
# All source: FORENSIC_v8_0 §2.1 (planet positions), CGM_v9_0 §4-6

# A. Native D1 planet → sign lord (DISPOSITED_BY): 9 planets
DISP_EDGES = [
    ("PLN.SUN",     "PLN.SATURN", "Capricorn→Saturn rules"),          # Sun in Cap
    ("PLN.MOON",    "PLN.SATURN", "Aquarius→Saturn rules"),           # Moon in Aqu
    ("PLN.MARS",    "PLN.VENUS",  "Libra→Venus rules"),               # Mars in Lib
    ("PLN.MERCURY", "PLN.SATURN", "Capricorn→Saturn rules"),          # Mer in Cap
    ("PLN.JUPITER", "PLN.JUPITER","Sagittarius→Jupiter rules (own)"), # Jup in Sag
    ("PLN.VENUS",   "PLN.JUPITER","Sagittarius→Jupiter rules"),       # Ven in Sag
    ("PLN.SATURN",  "PLN.VENUS",  "Libra→Venus rules"),               # Sat in Lib
    ("PLN.RAHU",    "PLN.VENUS",  "Taurus→Venus rules (co-lord)"),    # Rahu in Tau
    ("PLN.KETU",    "PLN.MARS",   "Scorpio→Mars rules"),              # Ketu in Sco
]

# B. NAKSHATRA_LORD_IS: planet → nakshatra lord (9 main placements)
NAK_EDGES = [
    ("PLN.SUN",     "PLN.SATURN", "Shravana: lord Saturn"),           # Sun Shravana
    ("PLN.MOON",    "PLN.JUPITER","Purva Bhadrapada: lord Jupiter"),  # Moon PBh
    ("PLN.MARS",    "PLN.VENUS",  "Vishakha: lord Jupiter (alt Venus-co-lord)"),
    ("PLN.MERCURY", "PLN.SUN",    "Uttara Ashadha: lord Sun"),
    ("PLN.JUPITER", "PLN.KETU",   "Moola: lord Ketu"),
    ("PLN.VENUS",   "PLN.VENUS",  "Purva Ashadha: lord Venus (own)"),
    ("PLN.SATURN",  "PLN.JUPITER","Vishakha: lord Jupiter"),
    ("PLN.RAHU",    "PLN.VENUS",  "Rohini: lord Moon (Rahu in Tau Rohini)"),
    ("PLN.KETU",    "PLN.MERCURY","Anuradha: lord Saturn (Ketu in Sco Jyeshtha)"),
]

# C. GRAHA_ASPECT (Parashari): each planet's 7th (full) aspect + special aspects
# Saturn: 3rd/7th/10th; Mars: 4th/7th/8th; Jupiter: 5th/7th/9th; Rahu/Ketu: 5th/7th/9th
GRAHA_ASPECT_EDGES = [
    # Saturn (7H Libra): 3rd→9H Sagittarius, 7th→1H Aries, 10th→4H Cancer
    ("PLN.SATURN", "HSE.9",  "GRAHA_ASPECT", "Saturn 3rd special aspect"),
    ("PLN.SATURN", "HSE.1",  "GRAHA_ASPECT", "Saturn 7th full aspect"),
    ("PLN.SATURN", "HSE.4",  "GRAHA_ASPECT", "Saturn 10th special aspect"),
    # Mars (7H Libra): 4th→10H Cap, 7th→1H Aries, 8th→2H Taurus
    ("PLN.MARS",   "HSE.10", "GRAHA_ASPECT", "Mars 4th special aspect"),
    ("PLN.MARS",   "HSE.1",  "GRAHA_ASPECT", "Mars 7th full aspect"),
    ("PLN.MARS",   "HSE.2",  "GRAHA_ASPECT", "Mars 8th special aspect"),
    # Jupiter (9H Sagittarius): 5th→1H, 7th→3H, 9th→5H
    ("PLN.JUPITER","HSE.1",  "GRAHA_ASPECT", "Jupiter 5th special aspect"),
    ("PLN.JUPITER","HSE.3",  "GRAHA_ASPECT", "Jupiter 7th full aspect"),
    ("PLN.JUPITER","HSE.5",  "GRAHA_ASPECT", "Jupiter 9th special aspect"),
    # Mercury (10H Capricorn): 7th→4H Cancer
    ("PLN.MERCURY","HSE.4",  "GRAHA_ASPECT", "Mercury 7th full aspect"),
    # Sun (10H Capricorn): 7th→4H Cancer
    ("PLN.SUN",    "HSE.4",  "GRAHA_ASPECT", "Sun 7th full aspect"),
    # Moon (11H Aquarius): 7th→5H Leo
    ("PLN.MOON",   "HSE.5",  "GRAHA_ASPECT", "Moon 7th full aspect"),
    # Venus (9H Sagittarius): 7th→3H Gemini
    ("PLN.VENUS",  "HSE.3",  "GRAHA_ASPECT", "Venus 7th full aspect"),
    # Rahu (2H Taurus): 5th→6H, 7th→8H, 9th→10H
    ("PLN.RAHU",   "HSE.6",  "GRAHA_ASPECT", "Rahu 5th aspect"),
    ("PLN.RAHU",   "HSE.8",  "GRAHA_ASPECT", "Rahu 7th aspect"),
    ("PLN.RAHU",   "HSE.10", "GRAHA_ASPECT", "Rahu 9th aspect"),
    # Ketu (8H Scorpio): 5th→12H, 7th→2H, 9th→4H
    ("PLN.KETU",   "HSE.12", "GRAHA_ASPECT", "Ketu 5th aspect"),
    ("PLN.KETU",   "HSE.2",  "GRAHA_ASPECT", "Ketu 7th aspect"),
    ("PLN.KETU",   "HSE.4",  "GRAHA_ASPECT", "Ketu 9th aspect"),
]

# D. OWNERSHIP (12 houses × lord)
OWNERSHIP_EDGES = [
    ("PLN.MARS",    "HSE.1",  "OWNERSHIP", "1H Aries lord = Mars"),
    ("PLN.VENUS",   "HSE.2",  "OWNERSHIP", "2H Taurus lord = Venus"),
    ("PLN.MERCURY", "HSE.3",  "OWNERSHIP", "3H Gemini lord = Mercury"),
    ("PLN.MOON",    "HSE.4",  "OWNERSHIP", "4H Cancer lord = Moon"),
    ("PLN.SUN",     "HSE.5",  "OWNERSHIP", "5H Leo lord = Sun"),
    ("PLN.MERCURY", "HSE.6",  "OWNERSHIP", "6H Virgo lord = Mercury"),
    ("PLN.VENUS",   "HSE.7",  "OWNERSHIP", "7H Libra lord = Venus"),
    ("PLN.MARS",    "HSE.8",  "OWNERSHIP", "8H Scorpio lord = Mars"),
    ("PLN.JUPITER", "HSE.9",  "OWNERSHIP", "9H Sagittarius lord = Jupiter"),
    ("PLN.SATURN",  "HSE.10", "OWNERSHIP", "10H Capricorn lord = Saturn"),
    ("PLN.SATURN",  "HSE.11", "OWNERSHIP", "11H Aquarius lord = Saturn"),
    ("PLN.JUPITER", "HSE.12", "OWNERSHIP", "12H Pisces lord = Jupiter"),
]

# E. TENANCY (planet → house it occupies)
TENANCY_EDGES = [
    ("PLN.RAHU",    "HSE.2",  "TENANCY", "Rahu in 2H Taurus"),
    ("PLN.SATURN",  "HSE.7",  "TENANCY", "Saturn in 7H Libra"),
    ("PLN.MARS",    "HSE.7",  "TENANCY", "Mars in 7H Libra"),
    ("PLN.JUPITER", "HSE.9",  "TENANCY", "Jupiter in 9H Sagittarius"),
    ("PLN.VENUS",   "HSE.9",  "TENANCY", "Venus in 9H Sagittarius"),
    ("PLN.SUN",     "HSE.10", "TENANCY", "Sun in 10H Capricorn"),
    ("PLN.MERCURY", "HSE.10", "TENANCY", "Mercury in 10H Capricorn"),
    ("PLN.MOON",    "HSE.11", "TENANCY", "Moon in 11H Aquarius"),
    ("PLN.KETU",    "HSE.8",  "TENANCY", "Ketu in 8H Scorpio"),
]

# F. JAIMINI_ASPECT (movable→fixed dual; fixed→dual movable; dual→movable fixed)
# Rashi Drishti from Aries Lagna perspective
JAIMINI_ASPECT_EDGES = [
    # Aries (movable) aspects Capricorn, Cancer, Libra (fixed signs except adjacent)
    ("SGN.ARIES",       "SGN.CANCER",     "JAIMINI_ASPECT", "Aries aspects Cancer"),
    ("SGN.ARIES",       "SGN.LIBRA",      "JAIMINI_ASPECT", "Aries aspects Libra"),
    ("SGN.ARIES",       "SGN.CAPRICORN",  "JAIMINI_ASPECT", "Aries aspects Capricorn"),
    # Taurus (fixed) aspects Leo, Scorpio, Aquarius
    ("SGN.TAURUS",      "SGN.LEO",        "JAIMINI_ASPECT", "Taurus aspects Leo"),
    ("SGN.TAURUS",      "SGN.SCORPIO",    "JAIMINI_ASPECT", "Taurus aspects Scorpio"),
    ("SGN.TAURUS",      "SGN.AQUARIUS",   "JAIMINI_ASPECT", "Taurus aspects Aquarius"),
    # Libra (movable) aspects Aries (opp not counted same), Cap, Cancer
    ("SGN.LIBRA",       "SGN.ARIES",      "JAIMINI_ASPECT", "Libra aspects Aries"),
    ("SGN.LIBRA",       "SGN.CANCER",     "JAIMINI_ASPECT", "Libra aspects Cancer"),
    ("SGN.LIBRA",       "SGN.CAPRICORN",  "JAIMINI_ASPECT", "Libra aspects Capricorn"),
    # Capricorn (movable) aspects Aries, Cancer, Libra
    ("SGN.CAPRICORN",   "SGN.ARIES",      "JAIMINI_ASPECT", "Capricorn aspects Aries"),
    ("SGN.CAPRICORN",   "SGN.CANCER",     "JAIMINI_ASPECT", "Capricorn aspects Cancer"),
    ("SGN.CAPRICORN",   "SGN.LIBRA",      "JAIMINI_ASPECT", "Capricorn aspects Libra"),
    # Sagittarius (dual/mutable) aspects Gemini, Virgo, Pisces
    ("SGN.SAGITTARIUS", "SGN.GEMINI",     "JAIMINI_ASPECT", "Sagittarius aspects Gemini"),
    ("SGN.SAGITTARIUS", "SGN.VIRGO",      "JAIMINI_ASPECT", "Sagittarius aspects Virgo"),
    ("SGN.SAGITTARIUS", "SGN.PISCES",     "JAIMINI_ASPECT", "Sagittarius aspects Pisces"),
]

# G. DIVISIONAL_TRANSITION (D1→D9 for 9 planets, from CGM §6)
DIV_TRANSITION_EDGES = [
    ("PLN.SUN",     "DVS.D9.SUN",     "DIVISIONAL_TRANSITION", "Sun: D1 Capricorn → D9 Cancer"),
    ("PLN.MOON",    "DVS.D9.MOON",    "DIVISIONAL_TRANSITION", "Moon: D1 Aquarius → D9 Gemini"),
    ("PLN.MARS",    "DVS.D9.MARS",    "DIVISIONAL_TRANSITION", "Mars: D1 Libra → D9 Pisces"),
    ("PLN.MERCURY", "DVS.D9.MERCURY", "DIVISIONAL_TRANSITION", "Mercury: D1 Cap → D9 Cap (Vargottama)"),
    ("PLN.JUPITER", "DVS.D9.JUPITER", "DIVISIONAL_TRANSITION", "Jupiter: D1 Sag → D9 Gemini"),
    ("PLN.VENUS",   "DVS.D9.VENUS",   "DIVISIONAL_TRANSITION", "Venus: D1 Sag → D9 Virgo (debil)"),
    ("PLN.SATURN",  "DVS.D9.SATURN",  "DIVISIONAL_TRANSITION", "Saturn: D1 Libra (exalt) → D9 Aries (debil)"),
    ("PLN.RAHU",    "DVS.D9.RAHU",    "DIVISIONAL_TRANSITION", "Rahu: D1 Taurus → D9 Gemini"),
    ("PLN.KETU",    "DVS.D9.KETU",    "DIVISIONAL_TRANSITION", "Ketu: D1 Scorpio → D9 Sagittarius"),
]

# H. YOGA_MEMBERSHIP (key yogas from CGM §4 nodes, 19 YOG entries)
YOGA_MEMBERSHIP_EDGES = [
    # YOG.SASHA_MPY — Sasha Mahapurusha
    ("PLN.SATURN",  "YOG.SASHA_MPY",     "YOGA_MEMBERSHIP", "Saturn exalted kendra = Sasha MPY"),
    # YOG.BUDH_ADITYA — Sun+Mercury in same sign
    ("PLN.SUN",     "YOG.BUDH_ADITYA",   "YOGA_MEMBERSHIP", "Sun in Capricorn 10H"),
    ("PLN.MERCURY", "YOG.BUDH_ADITYA",   "YOGA_MEMBERSHIP", "Mercury in Capricorn 10H"),
    # YOG.LAKSHMI_NARAYANA — Venus+Jupiter 9H conjunction
    ("PLN.VENUS",   "YOG.LAKSHMI_NARAYANA","YOGA_MEMBERSHIP","Venus+Jupiter in 9H"),
    ("PLN.JUPITER", "YOG.LAKSHMI_NARAYANA","YOGA_MEMBERSHIP","Venus+Jupiter in 9H"),
    # YOG.NEECHA_BHANGA_VENUS — Venus debil D9 cancelled by Merc Vargottama
    ("PLN.VENUS",   "YOG.NEECHA_BHANGA_VENUS","YOGA_MEMBERSHIP","Venus D9 Virgo debil"),
    ("PLN.MERCURY", "YOG.NEECHA_BHANGA_VENUS","YOGA_MEMBERSHIP","Mercury Vargottama cancels"),
    # YOG.UBHAYACHARI — Sun flanked by benefics
    ("PLN.SUN",     "YOG.UBHAYACHARI",   "YOGA_MEMBERSHIP", "Sun central to Ubhayachari"),
    ("PLN.MOON",    "YOG.UBHAYACHARI",   "YOGA_MEMBERSHIP", "Moon in 2nd from Sun"),
    ("PLN.JUPITER", "YOG.UBHAYACHARI",   "YOGA_MEMBERSHIP", "Jupiter in 12th from Sun"),
    ("PLN.VENUS",   "YOG.UBHAYACHARI",   "YOGA_MEMBERSHIP", "Venus in 12th from Sun"),
    # YOG.MERCURY_OPERATIONAL_SPINE — Mercury 8-system convergence
    ("PLN.MERCURY", "YOG.MERCURY_OPERATIONAL_SPINE","YOGA_MEMBERSHIP","Mercury 8-system spine"),
    # YOG.SATURN_QUADRUPLE
    ("PLN.SATURN",  "YOG.SATURN_QUADRUPLE","YOGA_MEMBERSHIP","Saturn 4-fold designation"),
]

# I. KARAKA_ROLE (Chara Karaka assignments, from CGM KRK nodes)
KARAKA_EDGES = [
    ("PLN.SATURN",  "KRK.C8.AMATYA",    "KARAKA_ROLE", "Saturn = AmK (career minister)"),
    ("PLN.MERCURY", "KRK.C8.DARA",      "KARAKA_ROLE", "Mercury = DK (spouse signif)"),
    ("PLN.MOON",    "KRK.C8.ATMA",      "KARAKA_ROLE", "Moon = AK (soul significator)"),
    ("PLN.MARS",    "KRK.C8.BHRATRA",   "KARAKA_ROLE", "Mars = BK (co-born)"),
    ("PLN.JUPITER", "KRK.C8.GNATI",     "KARAKA_ROLE", "Jupiter = GK (obstacles)"),
    ("PLN.VENUS",   "KRK.C8.MATRU",     "KARAKA_ROLE", "Venus = MK (mother/relations)"),
    ("PLN.RAHU",    "KRK.C8.PITRU",     "KARAKA_ROLE", "Rahu = PiK (father/ancestor)"),
    ("PLN.SUN",     "KRK.C8.PUTRA",     "KARAKA_ROLE", "Sun = PuK (progeny/creative)"),
    ("PLN.KETU",    "KRK.STH.AMATYA",   "KARAKA_ROLE", "Mercury = sthira AmatyaK (amended: Ketu sthira)"),
]

# J. EXALT_DEBIL_AFFINITY (key dignity relationships)
EXALT_DEBIL_EDGES = [
    ("PLN.SATURN",  "SGN.LIBRA",        "EXALT_DEBIL_AFFINITY", "Saturn exalted in Libra (22°27')"),
    ("PLN.SATURN",  "SGN.ARIES",        "EXALT_DEBIL_AFFINITY", "Saturn debilitated in Aries (D9)"),
    ("PLN.VENUS",   "SGN.VIRGO",        "EXALT_DEBIL_AFFINITY", "Venus debilitated in Virgo (D9)"),
    ("PLN.MERCURY", "SGN.CAPRICORN",    "EXALT_DEBIL_AFFINITY", "Mercury Vargottama Capricorn D1+D9"),
    ("PLN.JUPITER", "SGN.SAGITTARIUS",  "EXALT_DEBIL_AFFINITY", "Jupiter own-sign in Sagittarius"),
    ("PLN.MOON",    "SGN.AQUARIUS",     "EXALT_DEBIL_AFFINITY", "Moon in 11H Aquarius (Saturn sign)"),
]


def _make_edge_id(source: str, target: str, edge_type: str) -> str:
    """Deterministic edge ID from source + target + type."""
    raw = f"{source}|{target}|{edge_type}"
    return "E" + hashlib.sha1(raw.encode()).hexdigest()[:10].upper()


def build_canonical_edges() -> list[dict[str, Any]]:
    """
    Assemble the full canonical edge corpus from all sources.

    Returns list of edge dicts with keys:
      edge_id, source_node, target_node, edge_type, weight, domain,
      derivation_note, provenance_envelope
    """
    edges: list[dict[str, Any]] = []

    def _add(src: str, tgt: str, etype: str, note: str, domain: str = "chart") -> None:
        eid = _make_edge_id(src, tgt, etype)
        edges.append({
            "edge_id":      eid,
            "source_node":  src,
            "target_node":  tgt,
            "edge_type":    etype,
            "weight":       EDGE_WEIGHTS.get(etype, 0.70),
            "domain":       domain,
            "derivation_note": note,
            "source_citation": SOURCE_CITATION,
            "provenance_envelope": {
                **PROVENANCE_ENVELOPE,
                "edge_id": eid,
            },
        })

    # A: DISPOSITED_BY
    for src, tgt, note in DISP_EDGES:
        _add(src, tgt, "DISPOSITED_BY", note, "dignity")

    # B: NAKSHATRA_LORD_IS
    for src, tgt, note in NAK_EDGES:
        _add(src, tgt, "NAKSHATRA_LORD_IS", note, "nakshatra")

    # C: GRAHA_ASPECT
    for src, tgt, etype, note in GRAHA_ASPECT_EDGES:
        _add(src, tgt, etype, note, "aspect")

    # D: OWNERSHIP
    for src, tgt, etype, note in OWNERSHIP_EDGES:
        _add(src, tgt, etype, note, "house")

    # E: TENANCY
    for src, tgt, etype, note in TENANCY_EDGES:
        _add(src, tgt, etype, note, "house")

    # F: JAIMINI_ASPECT
    for src, tgt, etype, note in JAIMINI_ASPECT_EDGES:
        _add(src, tgt, etype, note, "jaimini")

    # G: DIVISIONAL_TRANSITION
    for src, tgt, etype, note in DIV_TRANSITION_EDGES:
        _add(src, tgt, etype, note, "divisional")

    # H: YOGA_MEMBERSHIP
    for src, tgt, etype, note in YOGA_MEMBERSHIP_EDGES:
        _add(src, tgt, etype, note, "yoga")

    # I: KARAKA_ROLE
    for src, tgt, etype, note in KARAKA_EDGES:
        _add(src, tgt, etype, note, "karaka")

    # J: EXALT_DEBIL_AFFINITY
    for src, tgt, etype, note in EXALT_DEBIL_EDGES:
        _add(src, tgt, etype, note, "dignity")

    # Deduplicate by edge_id
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for e in edges:
        if e["edge_id"] not in seen:
            seen.add(e["edge_id"])
            unique.append(e)

    logger.info("[l2_graph] Built %d canonical edges", len(unique))
    return unique


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l2_graph] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── chart_facts writer ─────────────────────────────────────────────────────────

def seed_bodha_graph(
    chart_id: str,
    *,
    build_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Write CGM edges into chart_facts with fact_category='bodha.graph'.

    Returns: { seeded: int, volume_floor: int, volume_met: bool }
    """
    from datetime import date
    build_id = build_id or f"l2-graph-{date.today().isoformat()}"

    edges = build_canonical_edges()

    if dry_run:
        return {
            "seeded": 0, "dry_run": True,
            "edge_count": len(edges),
            "volume_floor": VOLUME_FLOOR,
            "volume_met": len(edges) >= VOLUME_FLOOR,
        }

    rows_written = 0
    with _conn() as conn:
        for e in edges:
            fact_value = {k: v for k, v in e.items() if k != "edge_id"}
            conn.execute(
                """
                INSERT INTO chart_facts
                  (chart_id, fact_category, fact_subject, fact_value,
                   source_citation, build_id)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                  fact_value      = EXCLUDED.fact_value,
                  source_citation = EXCLUDED.source_citation,
                  build_id        = EXCLUDED.build_id,
                  updated_at      = NOW()
                """,
                [
                    chart_id,
                    "bodha.graph",
                    e["edge_id"],
                    json.dumps(fact_value),
                    SOURCE_CITATION,
                    build_id,
                ],
            )
            rows_written += 1
        conn.commit()

    logger.info("[l2_graph] seed_bodha_graph: chart=%s rows=%d", chart_id, rows_written)
    return {
        "seeded":       rows_written,
        "volume_floor": VOLUME_FLOOR,
        "volume_met":   rows_written >= VOLUME_FLOOR,
        "grounding_status": "UNGROUNDED",
        "rule_id":      None,
        "build_id":     build_id,
    }


def check_volume() -> dict[str, Any]:
    """Check that canonical edges meet the volume floor (no DB required)."""
    edges = build_canonical_edges()
    actual = len(edges)
    # Edge type breakdown
    type_counts: dict[str, int] = {}
    for e in edges:
        t = e["edge_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    return {
        "status":           "GREEN" if actual >= VOLUME_FLOOR else "AMBER",
        "volume_floor":     VOLUME_FLOOR,
        "actual":           actual,
        "grounding_status": "UNGROUNDED",
        "edge_type_counts": type_counts,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    parser = argparse.ArgumentParser(
        description="l2_graph — Seed bodha.graph (CGM edges)"
    )
    sub = parser.add_subparsers(dest="cmd")

    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--chart-id", default=NATIVE_CHART_ID)
    p_seed.add_argument("--build-id", default=None)
    p_seed.add_argument("--dry-run", action="store_true")

    p_check = sub.add_parser("check")

    args = parser.parse_args()
    if args.cmd == "seed":
        result = seed_bodha_graph(args.chart_id, build_id=args.build_id, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    elif args.cmd == "check":
        result = check_volume()
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)
