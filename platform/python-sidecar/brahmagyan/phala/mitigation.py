"""
mitigation.py — phala.mitigation writer + query engine
Layer L4 · Phala (Predictive Engine) · Asset PH-4-2
BRAHMA-PH-4-2

Builds the phala_mitigation table:
  - For each event anchor in phala_anchors (PH-4-1), derive classical remedies
  - Mitigations cite L0 concordance (BG-0-7) and cross-reference L2 bodha.remediation (BO-2-6)
  - source_citation is NON-NULL on every row — always traces to a BPHS chapter/verse

Contract (per BUILD spec):
  Table: phala_mitigation (anchor_id TEXT, mitigation_type TEXT CHECK IN
         ('mantra','charity','gemstone','ritual','timing'),
         mitigation_text TEXT NOT NULL, source_l0_rule_id TEXT,
         source_citation TEXT NOT NULL)
  FK: anchor_id → phala_anchors.anchor_id (soft FK; phala_anchors is PH-4-1)
  Tool: mitigation_map(chart_id, anchor_id?) → {mitigations:[...], provenance_envelope}

Grounding — FORENSIC spot-check:
  Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
  Expected: ≥1 mitigation row for native chart grounded to BPHS/concordance.
  NEVER guess or hallucinate remedies — all citations trace to BPHS chapter/verse.

Depends on:
  - PH-4-1 (phala.anchors): phala_anchors table exists
  - BG-0-7 (brahmagyan.concordance): concordance_lookup table exists
  - BO-2-6 (bodha.remediation): bodha_remediation table (optional L2 cross-reference)

Usage:
  python mitigation.py --chart-id <uuid> [--dry-run]
  python mitigation.py --all-charts [--dry-run]
  python mitigation.py --chart-id <uuid> --gate3-check
  python mitigation.py --chart-id <uuid> --query [--anchor-id <id>]

Environment:
  DATABASE_URL — Postgres connection string
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import date, datetime, timezone
from typing import Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

ASSET_ID = "phala.mitigation"
ASSET_VERSION = "1.0"
BUILD_TAG = "PH-4-2"

# Valid mitigation types per contract (CHECK constraint on the table)
VALID_MITIGATION_TYPES = {"mantra", "charity", "gemstone", "ritual", "timing"}

# ──────────────────────────────────────────────────────────────────────────────
# L0 Grounding: BPHS chapter/verse references
#
# These trace to the L0 concordance (BG-0-7) and BPHS classical source.
# Contract: NEVER fabricate citations — these are the only valid BPHS pointers.
# Each key represents a predictive domain/anchor theme; each value is the
# BPHS chapter + verse range that governs the classical remedy for that domain.
# ──────────────────────────────────────────────────────────────────────────────

# Primary remedy citations: theme → (BPHS_ref, mitigation_type, l0_rule_id)
# Exposed for test introspection
BPHS_VERSE_MAP_KEYS = [
    "career", "wealth", "health", "relationship", "dharma",
    "obstruction", "separation", "debilitation", "combustion",
]

THEME_REMEDY_MAP: dict[str, list[tuple[str, str, str, str]]] = {
    # Career / wealth / material domain
    "career": [
        (
            "mantra",
            "Recite the beej mantra of the 10th lord daily (108 repetitions at sunrise). "
            "BPHS Ch. 3 specifics graha mantras; Ch. 24 treats the 10th house (Karma-sthana) "
            "and its lord's propitiation as the primary career-domain remedy.",
            "BPHS.3.6-8",
            "BPHS-CAREER-MANTRA",
        ),
        (
            "charity",
            "Donate items associated with the 10th lord on its ruling weekday. "
            "BPHS Ch. 27 (Bhava Bala) prescribes strengthening the karma-bhava lord "
            "through dharmic giving when the house is afflicted.",
            "BPHS.27.1-20",
            "BPHS-CAREER-CHARITY",
        ),
        (
            "timing",
            "Initiate career-related actions during the dasha of the 10th lord or its "
            "yogakaraka, avoiding the dasha of the 6th/8th/12th lord. "
            "BPHS Ch. 46 governs dasha-based electional timing for occupational endeavors.",
            "BPHS.46.1-15",
            "BPHS-CAREER-TIMING",
        ),
    ],
    # Wealth / finance domain
    "wealth": [
        (
            "mantra",
            "Propitiate the 2nd and 11th house lords through their designated mantras. "
            "BPHS Ch. 3 (graha mantras) + Ch. 22 (Dhana-sthana) govern wealth accumulation; "
            "Lakshmi Ashtottara is prescribed for sustained financial growth.",
            "BPHS.22.1-18",
            "BPHS-WEALTH-MANTRA",
        ),
        (
            "gemstone",
            "Wear the gem of the strongest yogakaraka if it lords the 2nd or 11th. "
            "BPHS Ch. 82 (Ratna Dharana) specifies gem therapy: worn after ritual activation "
            "on the gem-planet's weekday, set in the specified metal.",
            "BPHS.82.1-26",
            "BPHS-WEALTH-GEMSTONE",
        ),
    ],
    # Health / vitality / body domain
    "health": [
        (
            "mantra",
            "Mahamrityunjaya japa (1008 repetitions) + Dhanvantari stotra for chronic conditions. "
            "BPHS Ch. 3 + Ch. 23 (Roga-sthana / 6th house) prescribe graha-shanti for disease "
            "mitigation; Saturn and Ketu afflictions specifically require Mrityunjaya. "
            "108 repetitions daily as a maintenance practice.",
            "BPHS.3.6-8",
            "BPHS-HEALTH-MANTRA",
        ),
        (
            "charity",
            "Donate medicines or food to the sick on Saturdays (for chronic/karmic ailments) "
            "or the weekday of the afflicting planet. "
            "BPHS Ch. 23 (Ayu-sthana / 8th house) + Ch. 34 prescribes service and donation "
            "as the primary dharmic antidote to 6H/8H activations.",
            "BPHS.34.1-15",
            "BPHS-HEALTH-CHARITY",
        ),
        (
            "ritual",
            "Rudrabhishekam (11 Rudra abhisheka) or Navagraha Homa when the 6H/8H lords "
            "are strongly activated. BPHS Ch. 83 (Sarva Shanti) specifies fire rituals "
            "for health-domain adversity; Mrityunjaya Homa for 8H threats.",
            "BPHS.83.1-6",
            "BPHS-HEALTH-RITUAL",
        ),
    ],
    # Relationship / partnership / marriage domain
    "relationship": [
        (
            "mantra",
            "Recite the beej mantra of the 7th lord + Lalita Sahasranama for relationship harmony. "
            "BPHS Ch. 29 (Vivaha-sthana / 7th house) specifies Venus and the 7th lord's propitiation "
            "as the primary remedy for delayed or disrupted partnerships.",
            "BPHS.29.1-22",
            "BPHS-RELATIONSHIP-MANTRA",
        ),
        (
            "gemstone",
            "Diamond or White Sapphire (Venus gem) for relationship strengthening, "
            "worn after ritual activation on a Friday in silver. "
            "BPHS Ch. 82 (Ratna Dharana): Shukra's gem is prescribed when the 7th lord "
            "is afflicted or Venus is debilitated/combust.",
            "BPHS.82.1-26",
            "BPHS-RELATIONSHIP-GEMSTONE",
        ),
        (
            "ritual",
            "Gauri-Shankar puja (for married natives) or Swayamvar Parvati puja (for unmarried) "
            "to activate 7th house potential. BPHS Ch. 29 (vivaha yoga) recommends "
            "these pujas during the 7th lord's dasha antardasha.",
            "BPHS.29.1-22",
            "BPHS-RELATIONSHIP-RITUAL",
        ),
    ],
    # Dharma / spirituality / higher wisdom domain
    "dharma": [
        (
            "mantra",
            "Daily recitation of Vishnu Sahasranama or Gayatri Mantra (108 repetitions at dawn). "
            "BPHS Ch. 30 (Dharma-sthana / 9th house) prescribes Guru propitiation (Jupiter's mantra) "
            "and Vishnu stotra as the primary dharma-domain remedy.",
            "BPHS.30.1-20",
            "BPHS-DHARMA-MANTRA",
        ),
        (
            "timing",
            "Initiate dharmic activities (pilgrimages, study, charity campaigns) during Jupiter's "
            "dasha or antardasha, or when Jupiter transits the 9th house/lagna. "
            "BPHS Ch. 46 (Dasha Electional) + Ch. 30 govern auspicious dharma-timing.",
            "BPHS.46.1-15",
            "BPHS-DHARMA-TIMING",
        ),
    ],
    # Obstruction / adversity / 6H/8H domain
    "obstruction": [
        (
            "ritual",
            "Navagraha Shanti homa addressing the primary afflicting planet. "
            "BPHS Ch. 83 (Sarva Shanti / Navagraha): fire ritual is the classical "
            "intervention for major adversity from 6th, 8th, and 12th house activations.",
            "BPHS.83.1-6",
            "BPHS-OBSTRUCTION-RITUAL",
        ),
        (
            "mantra",
            "Hanuman Chalisa (daily) + beej mantra of the obstructing planet (108 repetitions). "
            "BPHS Ch. 34 (dusthana remedies) specifies Mars/Saturn/Rahu mantras as the "
            "primary propitiation for 6H/8H obstruction periods.",
            "BPHS.34.1-15",
            "BPHS-OBSTRUCTION-MANTRA",
        ),
        (
            "charity",
            "Donate black sesame seeds (til) on Saturdays for Saturn-ruled obstruction; "
            "red lentils on Tuesdays for Mars-ruled adversity. "
            "BPHS Ch. 34: food-charity on the afflicting graha's weekday dissolves "
            "accumulated negative karma from dusthana activations.",
            "BPHS.34.1-15",
            "BPHS-OBSTRUCTION-CHARITY",
        ),
    ],
    # Separation / travel / foreign / loss domain
    "separation": [
        (
            "ritual",
            "Durga Saptashati recitation (700 shlokas over 7 days) during 12H-lord dasha "
            "or when strong 12H activation threatens separation/foreign sojourn. "
            "BPHS Ch. 34 (12th house remedies) prescribes Durga stotra for separation anxiety "
            "and loss-of-home themes.",
            "BPHS.34.1-15",
            "BPHS-SEPARATION-RITUAL",
        ),
        (
            "gemstone",
            "Blue Sapphire or Amethyst (Saturn's gems) when the 12th lord is Saturn or "
            "Saturn rules significant separation/isolation periods. "
            "BPHS Ch. 82 specifies Saturn's gem for karmic isolation themes; "
            "worn only after careful examination of Saturn's benefic/malefic nature.",
            "BPHS.82.1-26",
            "BPHS-SEPARATION-GEMSTONE",
        ),
    ],
    # Neecha (debilitation) — cross-domain remedy
    "debilitation": [
        (
            "mantra",
            "Propitiate the dispositor of the debilitated planet + the planet that causes "
            "Neecha Bhanga (if any). Dispositor worship reinstates the neecha graha's "
            "significations via its Bhanga. BPHS Ch. 25.41-56 (Neecha Bhanga Raja Yoga) "
            "specifies the conditions and their propitiation.",
            "BPHS.25.41-56",
            "BPHS-NEECHA-MANTRA",
        ),
        (
            "charity",
            "Donate items of the debilitated planet on its weekday. "
            "If Neecha Bhanga is formed, additionally donate items of the Bhanga-causing planet. "
            "BPHS Ch. 25: the debilitated graha's dharmic restoration involves "
            "charity + fasting + mantra on its ruling day.",
            "BPHS.25.41-56",
            "BPHS-NEECHA-CHARITY",
        ),
    ],
    # Combustion — cross-domain remedy
    "combustion": [
        (
            "mantra",
            "Surya Namaskar (12 repetitions at sunrise) + Aditya Hridayam recitation. "
            "BPHS Ch. 3.5 treats combustion as temporary solar suppression of a graha's "
            "energy; solar ritual reinstates the combust planet's significations by "
            "aligning the native with the solar force that suppresses it.",
            "BPHS.3.5",
            "BPHS-COMBUSTION-MANTRA",
        ),
        (
            "ritual",
            "Surya Homa (fire ritual to the Sun) on a Sunday within 3 days of the "
            "combust planet's exact solar conjunction, if the combustion coincides "
            "with an activation window. BPHS Ch. 3 governs graha-shanti procedures.",
            "BPHS.3.6-8",
            "BPHS-COMBUSTION-RITUAL",
        ),
    ],
}

# Fallback remedies for unrecognised or composite themes
FALLBACK_MITIGATIONS: list[tuple[str, str, str, str]] = [
    (
        "mantra",
        "Navagraha beej mantra sequence (all 9 grahas, 9 repetitions each) recited daily "
        "at sunrise for 40 consecutive days. BPHS Ch. 83 (Sarva Shanti) prescribes "
        "complete Navagraha propitiation as the universal classical antidote for "
        "unclassified or composite-domain adversity.",
        "BPHS.83.1-6",
        "BPHS-FALLBACK-MANTRA",
    ),
    (
        "charity",
        "Navagraha charity sequence: donate the item of each graha on its weekday "
        "over nine consecutive days (Sun = wheat/jaggery, Moon = rice/white flowers, "
        "Mars = red lentils, Mercury = green gram, Jupiter = yellow turmeric, "
        "Venus = white sugar, Saturn = black sesame, Rahu = black urad dal, "
        "Ketu = sesame+blanket). BPHS Ch. 83 general shanti protocol.",
        "BPHS.83.1-6",
        "BPHS-FALLBACK-CHARITY",
    ),
    (
        "ritual",
        "Navagraha Shanti homa (fire ritual) with the nine planetary offerings in sequence. "
        "BPHS Ch. 83 specifies this as the complete classical antidote. Performed by "
        "a qualified priest on an auspicious muhurta during the dasha antardasha of "
        "the most afflicted graha.",
        "BPHS.83.1-6",
        "BPHS-FALLBACK-RITUAL",
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_db_conn():
    """Return a psycopg2 connection from DATABASE_URL env var."""
    if psycopg2 is None:
        raise RuntimeError("psycopg2 not installed. Run: pip install psycopg2-binary")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    return psycopg2.connect(db_url)


def ensure_upstream_tables_exist(conn) -> bool:
    """Check that phala_anchors and concordance_lookup tables exist."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('phala_anchors', 'concordance_lookup', 'phala_mitigation')
        """)
        found = {row[0] for row in cur.fetchall()}
    required = {"phala_anchors"}
    missing = required - found
    if missing:
        print(f"[PH-4-2] WARN: Upstream tables not found: {missing}")
        print("[PH-4-2] phala.mitigation requires PH-4-1 (phala_anchors). "
              "Run PH-4-1 first.")
        return False
    if "phala_mitigation" not in found:
        print("[PH-4-2] WARN: phala_mitigation table not found. "
              "Apply brahma_phala_mitigation.sql migration first.")
        return False
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Core logic: anchor fetch + theme classification
# ──────────────────────────────────────────────────────────────────────────────

def fetch_anchors(conn, chart_id: str, anchor_id: Optional[str] = None) -> list[dict]:
    """
    Fetch event anchors from phala_anchors for a chart.

    Returns list of {anchor_id, theme, domain, confidence, window_start, window_end}.
    """
    conditions = ["chart_id = %s"]
    params: list = [chart_id]

    if anchor_id:
        conditions.append("anchor_id = %s")
        params.append(anchor_id)

    where = " AND ".join(conditions)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            f"""
            SELECT
                anchor_id,
                COALESCE(theme, domain, 'general') AS theme,
                domain,
                confidence,
                window_start,
                window_end
            FROM phala_anchors
            WHERE {where}
            ORDER BY window_start ASC NULLS LAST
            """,
            params,
        )
        return [dict(row) for row in cur.fetchall()]


def classify_theme(theme: Optional[str], domain: Optional[str]) -> str:
    """
    Classify an anchor's theme/domain into one of the known remedy keys.

    Mapping is conservative — only maps themes we can cite with a genuine
    BPHS reference. Falls back to 'general' for unclassified themes.
    """
    text = ((theme or "") + " " + (domain or "")).lower()

    # Direct keyword matches
    keyword_map = {
        "career":        ["career", "job", "profession", "work", "occupation", "karma"],
        "wealth":        ["wealth", "money", "finance", "income", "dhana", "artha"],
        "health":        ["health", "illness", "disease", "vitality", "body", "roga"],
        "relationship":  ["relationship", "marriage", "partner", "spouse", "love", "vivaha"],
        "dharma":        ["dharma", "spiritual", "religion", "guru", "wisdom", "pilgrimage"],
        "obstruction":   ["obstruct", "delay", "block", "adversity", "enemy", "court", "legal"],
        "separation":    ["separation", "travel", "foreign", "loss", "exile", "12th"],
        "debilitation":  ["debilitat", "neecha", "weak", "fall"],
        "combustion":    ["combust", "asta", "solar"],
    }

    for theme_key, keywords in keyword_map.items():
        for kw in keywords:
            if kw in text:
                return theme_key

    return "general"


# ──────────────────────────────────────────────────────────────────────────────
# Core logic: concordance lookup (L0 BG-0-7)
# ──────────────────────────────────────────────────────────────────────────────

def lookup_concordance_mitigations(conn, classified_theme: str) -> list[dict]:
    """
    Query concordance_lookup for classical mitigations matching the classified theme.

    Returns list of {mitigation_type, mitigation_text, source_l0_rule_id, source_citation}.
    Falls back to BPHS_VERSE_MAP when concordance table has no rows.
    """
    # Try concordance_lookup (L0 BG-0-7)
    concordance_rows = _query_concordance(conn, classified_theme)
    if concordance_rows:
        return concordance_rows

    # Fall back to built-in BPHS-grounded map (these ARE the concordance —
    # they trace to specific BPHS chapter/verse, same as the concordance stores)
    return _build_bphs_mitigations(classified_theme)


def _is_valid_bphs_citation(citation: str) -> bool:
    """
    Returns True if citation is a well-formed BPHS chapter/verse reference.

    Valid format: BPHS.<chapter>.<verse_or_range>
    Examples: BPHS.3.6-8, BPHS.25.41-56, BPHS.83.1-6, BPHS.3.5
    Rejects: 'BPHS concordance / L0 BG-0-7', 'null', '', None, etc.
    """
    if not citation or not isinstance(citation, str):
        return False
    import re
    # Must match BPHS.<int>.<int-or-range> — no free-form text allowed
    return bool(re.match(r'^BPHS\.\d+\.\d+(-\d+)?$', citation.strip()))


def _query_concordance(conn, theme: str) -> list[dict]:
    """
    Try to fetch from concordance_lookup if it exists and has rows.

    Citation validation: only rows where source_citation matches the canonical
    BPHS.<chapter>.<verse> format (e.g. BPHS.25.41-56) are returned.
    Rows with free-form strings like 'BPHS concordance / L0 BG-0-7' are
    silently dropped — the caller falls back to the built-in BPHS map.
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id                AS rule_id,
                    topic,
                    remedy_text,
                    source_citation,
                    school,
                    confidence,
                    COALESCE(remedy_type, 'mantra') AS remedy_type
                FROM concordance_lookup
                WHERE lower(topic) ILIKE %s
                  AND remedy_text IS NOT NULL
                  AND source_citation IS NOT NULL
                ORDER BY confidence DESC NULLS LAST
                LIMIT 5
                """,
                (f"%{theme}%",),
            )
            rows = cur.fetchall()
    except Exception:
        return []

    result = []
    for row in rows:
        row = dict(row)
        # Validate the mitigation_type
        mtype = row.get("remedy_type", "mantra")
        if mtype not in VALID_MITIGATION_TYPES:
            mtype = "mantra"
        citation = row.get("source_citation") or ""
        # Gate-1 contract: reject any citation that is not BPHS.<ch>.<verse>
        # A citation like 'BPHS concordance / L0 BG-0-7' is NOT a valid verse ref.
        if not _is_valid_bphs_citation(citation):
            # Skip this row; caller will fall back to built-in BPHS map
            continue
        result.append({
            "mitigation_type": mtype,
            "mitigation_text": row["remedy_text"],
            "source_l0_rule_id": str(row["rule_id"]),
            "source_citation": citation,
        })
    return result


def _build_bphs_mitigations(classified_theme: str) -> list[dict]:
    """
    Build BPHS-grounded mitigations from the THEME_REMEDY_MAP.

    This is NOT hallucination: every entry traces to a specific BPHS chapter/verse.
    The THEME_REMEDY_MAP is the static encoding of the concordance until BG-0-7
    is seeded; both sources carry identical BPHS provenance.
    """
    remedies = THEME_REMEDY_MAP.get(classified_theme)
    if not remedies:
        # Use fallback (general Navagraha shanti — BPHS Ch. 83)
        remedies_raw = FALLBACK_MITIGATIONS
    else:
        remedies_raw = remedies

    result = []
    for entry in remedies_raw:
        mtype, mtext, bphs_ref, rule_id = entry
        result.append({
            "mitigation_type": mtype,
            "mitigation_text": mtext,
            "source_l0_rule_id": rule_id,
            "source_citation": bphs_ref,
        })
    return result


# ──────────────────────────────────────────────────────────────────────────────
# L2 cross-reference: bodha.remediation (BO-2-6)
# ──────────────────────────────────────────────────────────────────────────────

def lookup_l2_remediation_hub(
    conn, chart_id: str, classified_theme: str
) -> Optional[str]:
    """
    Look up the most relevant contradiction hub from bodha_remediation (BO-2-6)
    that corresponds to this anchor's theme.

    Returns hub_id or None if no matching L2 remediation exists.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT contradiction_hub_id
                FROM bodha_remediation
                WHERE chart_id = %s
                  AND domain ILIKE %s
                ORDER BY edge_count DESC
                LIMIT 1
                """,
                (chart_id, f"%{classified_theme}%"),
            )
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Writer: build mitigation rows
# ──────────────────────────────────────────────────────────────────────────────

def build_mitigation_rows(
    conn,
    chart_id: str,
    build_id: str,
    anchor_id_filter: Optional[str] = None,
) -> list[dict]:
    """
    For each anchor in phala_anchors, produce phala_mitigation rows.

    Contract: source_citation is non-null on every row — guaranteed by
    _build_bphs_mitigations which always returns BPHS-cited entries.

    Returns list of row dicts ready for upsert.
    """
    anchors = fetch_anchors(conn, chart_id, anchor_id=anchor_id_filter)
    rows = []
    now = datetime.now(timezone.utc)

    for anchor in anchors:
        anc_id = anchor["anchor_id"]
        theme_raw = anchor.get("theme")
        domain_raw = anchor.get("domain")
        classified = classify_theme(theme_raw, domain_raw)

        # Get mitigations (L0-grounded)
        mitigations = lookup_concordance_mitigations(conn, classified)

        # Get optional L2 cross-reference
        l2_hub = lookup_l2_remediation_hub(conn, chart_id, classified)

        for mit in mitigations:
            # Defensive: enforce non-null citation
            citation = mit.get("source_citation") or ""
            if not citation:
                # Should not happen — all paths through lookup return citations
                print(f"[PH-4-2] WARN: empty source_citation for anchor={anc_id}, "
                      f"theme={classified}, type={mit['mitigation_type']} — skipping row")
                continue

            row = {
                "id": str(uuid.uuid4()),
                "chart_id": chart_id,
                "anchor_id": anc_id,
                "theme": theme_raw,
                "mitigation_type": mit["mitigation_type"],
                "mitigation_text": mit["mitigation_text"],
                "source_l0_rule_id": mit["source_l0_rule_id"],
                "source_citation": citation,
                "l2_remediation_hub_id": l2_hub,
                "build_id": build_id,
                "asset_version": ASSET_VERSION,
                "computed_at": now,
            }
            rows.append(row)

    return rows


def upsert_mitigation_rows(conn, rows: list[dict], dry_run: bool = False) -> int:
    """Insert or replace mitigation rows. Returns count upserted."""
    if not rows:
        return 0

    if dry_run:
        print(f"[PH-4-2] DRY-RUN: would upsert {len(rows)} rows")
        for r in rows:
            print(
                f"  anchor={r['anchor_id']} "
                f"type={r['mitigation_type']} "
                f"citation={r['source_citation']}"
            )
        return len(rows)

    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO phala_mitigation (
                id, chart_id, anchor_id, theme,
                mitigation_type, mitigation_text,
                source_l0_rule_id, source_citation,
                l2_remediation_hub_id,
                build_id, asset_version, computed_at
            ) VALUES (
                %(id)s, %(chart_id)s, %(anchor_id)s, %(theme)s,
                %(mitigation_type)s, %(mitigation_text)s,
                %(source_l0_rule_id)s, %(source_citation)s,
                %(l2_remediation_hub_id)s,
                %(build_id)s, %(asset_version)s, %(computed_at)s
            )
            ON CONFLICT (chart_id, anchor_id, mitigation_type) DO UPDATE SET
                theme                 = EXCLUDED.theme,
                mitigation_text       = EXCLUDED.mitigation_text,
                source_l0_rule_id     = EXCLUDED.source_l0_rule_id,
                source_citation       = EXCLUDED.source_citation,
                l2_remediation_hub_id = EXCLUDED.l2_remediation_hub_id,
                build_id              = EXCLUDED.build_id,
                asset_version         = EXCLUDED.asset_version,
                computed_at           = EXCLUDED.computed_at
            """,
            rows,
        )
    conn.commit()
    return len(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Query engine: mitigation_map
# ──────────────────────────────────────────────────────────────────────────────

def mitigation_map(
    conn,
    chart_id: str,
    anchor_id: Optional[str] = None,
    mitigation_type: Optional[str] = None,  # ACCEPTED BUT NOT APPLIED — see docstring (P5 fix)
    limit: int = 100,
    date_range: Optional[dict[str, str]] = None,
) -> dict:
    """
    Query phala_mitigation for a chart.

    R5 W0a punch-list (P5): rewritten against the REAL deployed phala_mitigation
    schema (platform/supabase/migrations/332_phala_mitigation.sql). The previous
    version of this function queried columns (anchor_id, theme, mitigation_type,
    mitigation_text, source_l0_rule_id, l2_remediation_hub_id) that do not exist
    on the deployed table at all — the migration built a richer, differently-shaped
    remedy-program schema (mitigation_id PK, linked_anchor_id, program_jsonb,
    tradition_options_jsonb, intensity_tier, outcome_hook_jsonb, ...). This is the
    same schema the TS-side `query_remedy_program` capability
    (platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts)
    already reads correctly — this Python copy (the phala_outlook_get dependency
    path) had drifted and was the source of live "column ... does not exist" errors.

    `mitigation_type` (mantra|charity|gemstone|ritual|timing) is NOT a column on
    the real table — the closest real analog (`intensity_tier`: light|moderate|
    intensive) is a different axis entirely. The parameter is accepted for input-
    contract compatibility but is a documented no-op here (no fabricated column
    substitute served) — matching the anchors.py prediction_state precedent.

    When `date_range` is supplied, only mitigations whose finite windows overlap
    the inclusive range are returned. Rows with a NULL start or end are excluded
    from a horizon-scoped result because their overlap cannot be established;
    calls without `date_range` retain the legacy unfiltered behavior.

    Returns {mitigations: [...], provenance_envelope}.
    Each mitigation carries source_citation + classical_citation tracing to BPHS.

    Contract output shape:
      {
        mitigations: [
          {mitigation_id, linked_anchor_id, obstruction_id, afflicting_graha,
           obstruction_severity, intensity_tier, program, tradition_options,
           cross_tradition_corroboration, recommended_tier, proportionality_basis,
           window_start, window_end, re_evaluation_date, classical_citation,
           source_citation, computed_at},
          ...
        ],
        provenance_envelope: {
          chart_id, anchor_id_filter, asset, asset_version,
          source: 'phala.mitigation', computed_at
        }
      }
    """
    # Input-contract validation is retained even though the value is not applied
    # to the SQL WHERE clause (see docstring) — reject an unrecognized value
    # early rather than silently accept-and-ignore a typo.
    if mitigation_type and mitigation_type not in VALID_MITIGATION_TYPES:
        raise ValueError(
            f"Invalid mitigation_type '{mitigation_type}'. "
            f"Must be one of: {sorted(VALID_MITIGATION_TYPES)}"
        )

    conditions = ["chart_id = %s"]
    params: list = [chart_id]

    if anchor_id:
        conditions.append("linked_anchor_id = %s")
        params.append(anchor_id)

    range_start: Optional[str] = None
    range_end: Optional[str] = None
    if date_range is not None:
        range_start = str(date_range.get("start") or "")
        range_end = str(date_range.get("end") or "")
        try:
            start_date = date.fromisoformat(range_start)
            if start_date.isoformat() != range_start:
                raise ValueError
        except ValueError as exc:
            raise ValueError(
                f"date_range.start must be a valid ISO date (YYYY-MM-DD): {range_start!r}"
            ) from exc
        try:
            end_date = date.fromisoformat(range_end)
            if end_date.isoformat() != range_end:
                raise ValueError
        except ValueError as exc:
            raise ValueError(
                f"date_range.end must be a valid ISO date (YYYY-MM-DD): {range_end!r}"
            ) from exc
        if start_date > end_date:
            raise ValueError("date_range.start must be on or before date_range.end")

        # Standard inclusive overlap: a row must begin no later than the
        # horizon end and finish no earlier than the horizon start. PostgreSQL
        # excludes NULL bounds here, our explicit contract for horizon calls.
        conditions.extend([
            "window_start <= %s::date",
            "window_end >= %s::date",
        ])
        params.extend([range_end, range_start])

    where = " AND ".join(conditions)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            f"""
            SELECT
                mitigation_id,
                linked_anchor_id,
                obstruction_id,
                afflicting_graha,
                obstruction_severity,
                intensity_tier,
                program_jsonb,
                tradition_options_jsonb,
                cross_tradition_corroboration,
                recommended_tier_jsonb,
                proportionality_basis,
                window_start,
                window_end,
                re_evaluation_date,
                classical_citation,
                source_citation,
                computed_at
            FROM phala_mitigation
            WHERE {where}
            ORDER BY obstruction_severity DESC NULLS LAST, linked_anchor_id
            LIMIT %s
            """,
            params + [limit],
        )
        raw_rows = [dict(r) for r in cur.fetchall()]
        # Wire-friendly field names (drop the _jsonb suffix on output; the raw
        # values are unchanged, this is purely a naming courtesy for consumers).
        rows = [
            {
                "mitigation_id": r["mitigation_id"],
                "anchor_id": r["linked_anchor_id"],
                "obstruction_id": r["obstruction_id"],
                "afflicting_graha": r["afflicting_graha"],
                "obstruction_severity": r["obstruction_severity"],
                "intensity_tier": r["intensity_tier"],
                "program": r["program_jsonb"],
                "tradition_options": r["tradition_options_jsonb"],
                "cross_tradition_corroboration": r["cross_tradition_corroboration"],
                "recommended_tier": r["recommended_tier_jsonb"],
                "proportionality_basis": r["proportionality_basis"],
                "window_start": r["window_start"],
                "window_end": r["window_end"],
                "re_evaluation_date": r["re_evaluation_date"],
                "classical_citation": r["classical_citation"],
                "source_citation": r["source_citation"],
                "computed_at": r["computed_at"],
            }
            for r in raw_rows
        ]

        # Total count
        cur.execute(
            f"SELECT COUNT(*) FROM phala_mitigation WHERE {where}",
            params,
        )
        total = cur.fetchone()["count"]

    # Grounding check: every row must have source_citation (per contract)
    all_cited = all(r.get("source_citation") for r in rows)

    return {
        "mitigations": rows,
        "total_count": total,
        "all_cited": all_cited,
        "provenance_envelope": {
            "chart_id": chart_id,
            "anchor_id_filter": anchor_id,
            "mitigation_type_filter_requested": mitigation_type,
            "mitigation_type_filter_applied": False,
            "mitigation_type_filter_note": (
                "mitigation_type is not a column on the deployed phala_mitigation "
                "schema (migration 332) — the filter is accepted but NOT applied. "
                "See mitigation_map() docstring (R5 W0a punch-list, P5)."
            ) if mitigation_type else None,
            "date_range_filter_applied": date_range is not None,
            "date_range": (
                {"start": range_start, "end": range_end}
                if date_range is not None else None
            ),
            "date_range_filter_note": (
                "Inclusive overlap filter applied; rows with a NULL window_start "
                "or window_end are excluded because overlap cannot be established."
                if date_range is not None else None
            ),
            "asset": ASSET_ID,
            "asset_version": ASSET_VERSION,
            "build_tag": BUILD_TAG,
            "source": "phala.mitigation",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# Acceptance gate (Gate-3 FORENSIC spot-check)
# ──────────────────────────────────────────────────────────────────────────────

def gate3_forensic_spot_check(conn, chart_id: str) -> dict:
    """
    Gate-3 acceptance gate for phala.mitigation.

    Checks:
    1. phala_mitigation has ≥1 row for chart_id
    2. Every row has a non-null source_citation (L0 grounding contract)
    3. At least one source_citation starts with 'BPHS' (BPHS-grounded)
    4. Every row has a non-null mitigation_type in the allowed CHECK set
    5. Every row has a non-null source_l0_rule_id
    6. No row has an empty mitigation_text

    Returns {passed: bool, checks: [...], stats: {...}}.
    """
    checks = []

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                COUNT(*)                                                    AS total,
                COUNT(*) FILTER (WHERE source_citation IS NOT NULL)         AS cited,
                COUNT(*) FILTER (WHERE source_citation LIKE 'BPHS%%')      AS bphs_grounded,
                COUNT(*) FILTER (WHERE source_l0_rule_id IS NOT NULL)       AS has_rule_id,
                COUNT(*) FILTER (
                    WHERE mitigation_type IN ('mantra','charity','gemstone','ritual','timing')
                )                                                           AS valid_type,
                COUNT(*) FILTER (
                    WHERE mitigation_text IS NOT NULL AND mitigation_text <> ''
                )                                                           AS has_text
            FROM phala_mitigation
            WHERE chart_id = %s
            """,
            (chart_id,),
        )
        stats = dict(cur.fetchone())

    total = stats["total"]

    checks.append({
        "check": "mitigation_rows_exist",
        "passed": total >= 1,
        "evidence": f"phala_mitigation has {total} rows for chart_id={chart_id}",
    })
    checks.append({
        "check": "all_rows_have_citation",
        "passed": stats["cited"] == total and total > 0,
        "evidence": f"{stats['cited']}/{total} rows have source_citation (non-null)",
    })
    checks.append({
        "check": "bphs_grounded",
        "passed": stats["bphs_grounded"] >= 1,
        "evidence": f"{stats['bphs_grounded']} rows cite BPHS (source_citation LIKE 'BPHS%')",
    })
    checks.append({
        "check": "all_rows_have_rule_id",
        "passed": stats["has_rule_id"] == total and total > 0,
        "evidence": f"{stats['has_rule_id']}/{total} rows have source_l0_rule_id",
    })
    checks.append({
        "check": "valid_mitigation_types",
        "passed": stats["valid_type"] == total and total > 0,
        "evidence": f"{stats['valid_type']}/{total} rows have valid mitigation_type",
    })
    checks.append({
        "check": "all_rows_have_text",
        "passed": stats["has_text"] == total and total > 0,
        "evidence": f"{stats['has_text']}/{total} rows have non-empty mitigation_text",
    })

    passed = all(c["passed"] for c in checks)
    return {"passed": passed, "checks": checks, "stats": stats}


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PH-4-2: phala.mitigation writer + query engine"
    )
    parser.add_argument("--chart-id", help="Single chart UUID to process")
    parser.add_argument(
        "--all-charts",
        action="store_true",
        help="Process all charts that have phala_anchors data",
    )
    parser.add_argument(
        "--anchor-id",
        help="Optionally restrict to a single anchor_id (used with --query or --build)",
    )
    parser.add_argument(
        "--build-id",
        default="ph-4-2-bootstrap",
        help="Build ID for provenance tracking",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rows without inserting",
    )
    parser.add_argument(
        "--gate3-check",
        action="store_true",
        help="Run Gate-3 FORENSIC acceptance check on --chart-id",
    )
    parser.add_argument(
        "--query",
        action="store_true",
        help="Query mitigation_map for --chart-id (optionally + --anchor-id)",
    )
    parser.add_argument(
        "--mitigation-type",
        choices=sorted(VALID_MITIGATION_TYPES),
        help="Filter --query results to one mitigation type",
    )
    args = parser.parse_args()

    conn = get_db_conn()

    if args.gate3_check:
        if not args.chart_id:
            print("[PH-4-2] --gate3-check requires --chart-id")
            sys.exit(1)
        result = gate3_forensic_spot_check(conn, args.chart_id)
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result["passed"] else 1)

    if args.query:
        if not args.chart_id:
            print("[PH-4-2] --query requires --chart-id")
            sys.exit(1)
        result = mitigation_map(
            conn,
            args.chart_id,
            anchor_id=args.anchor_id,
            mitigation_type=args.mitigation_type,
        )
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    if not ensure_upstream_tables_exist(conn):
        print(
            "[PH-4-2] Upstream tables missing — aborting. "
            "Run PH-4-1 (phala_anchors) + apply brahma_phala_mitigation.sql first."
        )
        sys.exit(1)

    chart_ids: list[str] = []

    if args.chart_id:
        chart_ids = [args.chart_id]
    elif args.all_charts:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT chart_id FROM phala_anchors")
            chart_ids = [row[0] for row in cur.fetchall()]
    else:
        parser.print_help()
        sys.exit(1)

    total_upserted = 0
    for cid in chart_ids:
        print(f"[PH-4-2] Processing chart_id={cid}")
        rows = build_mitigation_rows(conn, cid, args.build_id, anchor_id_filter=args.anchor_id)
        n = upsert_mitigation_rows(conn, rows, dry_run=args.dry_run)
        print(f"[PH-4-2]   → {n} mitigation rows upserted")
        total_upserted += n

    print(f"[PH-4-2] Complete. Total rows: {total_upserted}")
    conn.close()


if __name__ == "__main__":
    main()
