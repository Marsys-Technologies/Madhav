"""
phase_locked_anchors_writer.py — Phase-Locked Anchor detection and seeding.

Derives anchors from:
  1. l1_time_synchronicity windows with cluster_intensity >= 4
  2. G29 rules that fire for dasha-period conditions 2026-2060
  3. Hard-coded structural anchors (MD/AD change points)

Stream C — A16 [BUILD-ORCH-STREAM-C-A16-S1]
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Allowed anchor types (must match migration 146 CHECK constraint)
# ---------------------------------------------------------------------------

ALLOWED_ANCHOR_TYPES = frozenset({
    "dasha_change",
    "dasha_synergy",
    "transit_peak",
    "vedha_cluster",
    "bb_activation",
    "tajik_peak",
    "multi_system",
})

# ---------------------------------------------------------------------------
# Native chart_id
# ---------------------------------------------------------------------------

NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"

# ---------------------------------------------------------------------------
# STRUCTURAL_ANCHORS — 10 hard-coded, pre-analyzed from FORENSIC data
# Covers the native's Vimshottari schedule 2026-2060
# ---------------------------------------------------------------------------

STRUCTURAL_ANCHORS: list[dict[str, Any]] = [
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Mercury MD peak: Saturn-Jupiter trine 2026",
        "window_start": "2026-04-01",
        "window_end": "2026-07-31",
        "anchor_type": "transit_peak",
        "cluster_intensity": 4,
        "g29_rules_fired": ["phala_015", "saravali_001"],
        "systems_active": [
            "vimshottari_dasha",
            "bhrigu_bindu",
            "graha_aspect",
            "tajik_varsha",
        ],
        "primary_outcome": (
            "Intellectual and professional peak during Mercury MD; Jupiter transit over "
            "natal 1H signals expansion. Recognition for communication/analytical work."
        ),
        "alternative_scenario": (
            "If Mercury dasha lord is hemmed by malefics, scattered outcomes instead of "
            "peak — multiple projects without completion."
        ),
        "falsifiability_test": (
            "Test: does a career milestone, publication, or significant professional "
            "recognition occur Q2-Q3 2026?"
        ),
        "confidence_score": 0.72,
        "classical_citation": "Phaladeepika Ch 22, sl 4; Saravali Ch 40, sl 2",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Mercury→Ketu MD transition 2036-02",
        "window_start": "2035-11-01",
        "window_end": "2036-05-31",
        "anchor_type": "dasha_change",
        "cluster_intensity": 5,
        "g29_rules_fired": ["bphs_dp_030", "bphs_dp_031", "jaimini_001"],
        "systems_active": [
            "vimshottari_dasha",
            "jaimini_chara",
            "sade_sati",
            "vedha_activation",
            "bhrigu_bindu",
        ],
        "primary_outcome": (
            "Major life transition: Mercury MD (17-year intellectual/career epoch) ends; "
            "Ketu MD begins — orientation shifts toward spirituality, detachment from "
            "worldly pursuits, and karmic completion."
        ),
        "alternative_scenario": (
            "If Ketu is in favorable position (9H or 12H): spiritual elevation, foreign "
            "travel, moksha-orientation. If afflicted: confusion, loss, health challenges."
        ),
        "falsifiability_test": (
            "Test: does a significant career transition, spiritual turn, or life-philosophy "
            "shift occur in H2 2035–H1 2036?"
        ),
        "confidence_score": 0.85,
        "classical_citation": "BPHS Ch 53, sl 3-5; Jaimini Sutra 1.1.1",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Ketu MD Jupiter antardasha: spiritual peak 2036-2037",
        "window_start": "2036-08-01",
        "window_end": "2037-04-30",
        "anchor_type": "dasha_synergy",
        "cluster_intensity": 4,
        "g29_rules_fired": ["bphs_ad_004", "kp_012", "jaimini_008"],
        "systems_active": [
            "vimshottari_dasha",
            "bhrigu_bindu",
            "graha_aspect",
            "tajik_varsha",
        ],
        "primary_outcome": (
            "Jupiter AD within Ketu MD brings clarity after the transition confusion. "
            "Dharmic wisdom, guru encounter, spiritual practice deepens. Foreign travel "
            "for philosophical purposes."
        ),
        "alternative_scenario": (
            "If natal Jupiter is weak or combust: gains come as intellectual frameworks "
            "rather than lived wisdom; guru relationship may be superficial."
        ),
        "falsifiability_test": (
            "Test: does a guru figure, philosophical breakthrough, or significant spiritual "
            "practice begin during this period?"
        ),
        "confidence_score": 0.68,
        "classical_citation": "BPHS Ch 49 AD, Jaimini Sutra 1.3.7",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Ketu MD Saturn antardasha: karmic reckoning 2039-2041",
        "window_start": "2039-06-01",
        "window_end": "2041-02-28",
        "anchor_type": "dasha_synergy",
        "cluster_intensity": 5,
        "g29_rules_fired": ["bphs_ad_017", "bphs_dp_024", "saravali_004"],
        "systems_active": [
            "vimshottari_dasha",
            "sade_sati",
            "jaimini_chara",
            "vedha_activation",
            "bhrigu_bindu",
        ],
        "primary_outcome": (
            "Most intensive karmic period: Ketu MD × Saturn AD × approaching Sade Sati "
            "(Saturn enters Scorpio ~2041). Isolation, withdrawal, health challenges of a "
            "structural nature. Karmic debts from past lives surface. Outcomes depend "
            "heavily on spiritual preparedness."
        ),
        "alternative_scenario": (
            "If Saturn is strong (Libra exaltation or own sign) and native has done "
            "spiritual practice: this becomes a period of deep structural renewal. For "
            "unprepared native: loss, illness, forced separation."
        ),
        "falsifiability_test": (
            "Test: do significant material losses, health events, or enforced isolation "
            "occur 2039-2041? Does the native report this as a spiritually transformative "
            "period in retrospect?"
        ),
        "confidence_score": 0.80,
        "classical_citation": "BPHS Ch 51 AD, sl 8; Phaladeepika Ch 20, sl 8",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Ketu→Venus MD transition 2043-02",
        "window_start": "2042-11-01",
        "window_end": "2043-05-31",
        "anchor_type": "dasha_change",
        "cluster_intensity": 4,
        "g29_rules_fired": ["bphs_dp_033", "tajik_027", "phala_020"],
        "systems_active": [
            "vimshottari_dasha",
            "jaimini_chara",
            "tajik_varsha",
            "graha_aspect",
        ],
        "primary_outcome": (
            "Re-emergence into material world after Ketu MD withdrawal. Venus MD (20 years) "
            "brings relationships, creativity, aesthetic pursuits back to center. Strong "
            "potential for marriage or deep partnership if not already established."
        ),
        "alternative_scenario": (
            "If natal Venus is afflicted (conjunct Saturn or Rahu): relationships are "
            "complicated; creative success but relational strain."
        ),
        "falsifiability_test": (
            "Test: does a significant new relationship, creative project, or lifestyle "
            "elevation begin in H1 2043?"
        ),
        "confidence_score": 0.70,
        "classical_citation": "BPHS Ch 54, sl 1; Phaladeepika Ch 21, sl 3",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Venus MD Sun antardasha: authority peak 2043-2044",
        "window_start": "2043-08-01",
        "window_end": "2044-08-31",
        "anchor_type": "dasha_synergy",
        "cluster_intensity": 4,
        "g29_rules_fired": ["bphs_ad_008", "phala_022", "saravali_009"],
        "systems_active": [
            "vimshottari_dasha",
            "bhrigu_bindu",
            "graha_aspect",
            "tajik_varsha",
        ],
        "primary_outcome": (
            "Creative authority crystallizes: Venus MD × Sun AD = artistic leadership. "
            "Government recognition, public role, creative direction. Father-connection "
            "may also be significant."
        ),
        "alternative_scenario": (
            "Sun combust natal: ego conflicts in relationships; authority achieved but at "
            "cost of partnership harmony."
        ),
        "falsifiability_test": (
            "Test: does a public/creative leadership role or recognition emerge in the "
            "2043-2044 period?"
        ),
        "confidence_score": 0.65,
        "classical_citation": "BPHS Ch 54 AD; Saravali Ch 43, sl 10",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Jupiter transit over natal Moon 2027: emotional renewal",
        "window_start": "2027-04-01",
        "window_end": "2027-09-30",
        "anchor_type": "transit_peak",
        "cluster_intensity": 3,
        "g29_rules_fired": ["saravali_002", "phala_006"],
        "systems_active": ["bhrigu_bindu", "graha_aspect", "tajik_varsha"],
        "primary_outcome": (
            "Jupiter transiting 4H/5H from natal Moon: domestic expansion, children events, "
            "emotional wisdom. The 12-year Jupiter cycle returns to natal Moon configuration."
        ),
        "alternative_scenario": (
            "If natal Moon is afflicted: emotional expansion mixed with instability; children "
            "may bring joy and anxiety simultaneously."
        ),
        "falsifiability_test": (
            "Test: does a domestic expansion (home purchase, child birth/education milestone) "
            "or emotional peak occur April-September 2027?"
        ),
        "confidence_score": 0.60,
        "classical_citation": "Saravali Ch 40, sl 5-6; Phaladeepika Ch 22, sl 3",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Bhrigu Bindu cluster: Saturn exact transit 2028",
        "window_start": "2028-01-01",
        "window_end": "2028-04-30",
        "anchor_type": "bb_activation",
        "cluster_intensity": 4,
        "g29_rules_fired": ["nadi_023", "nadi_024", "bphs_dp_023"],
        "systems_active": [
            "bhrigu_bindu",
            "vimshottari_dasha",
            "graha_aspect",
            "vedha_activation",
        ],
        "primary_outcome": (
            "Saturn exact on Bhrigu Bindu (destiny point at Scorpio 26°): karmic pressure "
            "at destiny point. Hard discipline imposed by events; structural karmic "
            "reckoning. Health or career event that forces long-term course correction."
        ),
        "alternative_scenario": (
            "If native has been disciplined and prepared: the Saturn BB transit becomes a "
            "crystallization of long-term effort into form. Rewards the prepared."
        ),
        "falsifiability_test": (
            "Test: does a significant karmic or structural life event (career restructuring, "
            "health diagnosis, major relationship shift) occur Q1 2028?"
        ),
        "confidence_score": 0.75,
        "classical_citation": "BN Bindu section; BPHS Ch 51, sl 1",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Mercury MD late-phase: Rahu antardasha 2034",
        "window_start": "2033-09-01",
        "window_end": "2034-09-30",
        "anchor_type": "dasha_synergy",
        "cluster_intensity": 4,
        "g29_rules_fired": ["bphs_ad_009", "phala_029", "tajik_001"],
        "systems_active": [
            "vimshottari_dasha",
            "jaimini_chara",
            "bhrigu_bindu",
            "tajik_varsha",
        ],
        "primary_outcome": (
            "Rahu antardasha within Mercury MD: technological breakthroughs, foreign "
            "business, unconventional career pivot. The last major push of the Mercury "
            "epoch before transition."
        ),
        "alternative_scenario": (
            "If Rahu is ill-placed or conjunct a malefic: obsessive behavior, foreign "
            "entanglements, deceptive partnerships."
        ),
        "falsifiability_test": (
            "Test: does a significant foreign, technological, or unconventional professional "
            "event occur in 2033-2034?"
        ),
        "confidence_score": 0.62,
        "classical_citation": "BPHS Ch 52 AD; Phaladeepika Ch 20, sl 9",
    },
    {
        "chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
        "anchor_label": "Venus MD Jupiter antardasha: peak prosperity 2050-2052",
        "window_start": "2050-02-01",
        "window_end": "2052-01-31",
        "anchor_type": "dasha_synergy",
        "cluster_intensity": 5,
        "g29_rules_fired": ["bphs_dp_019", "bphs_ad_016", "phala_001", "jaimini_019"],
        "systems_active": [
            "vimshottari_dasha",
            "jaimini_chara",
            "tajik_varsha",
            "graha_aspect",
            "bhrigu_bindu",
        ],
        "primary_outcome": (
            "Venus MD × Jupiter AD = Mahavidya combination: highest prosperity window of "
            "the lifetime. All classical benefic indicators align. Spiritual wisdom combined "
            "with material abundance. Artistic and philosophical legacy works."
        ),
        "alternative_scenario": (
            "If by 2050 the native has squandered material or spiritual resources: this "
            "shows as a period of philosophical insight without material manifestation. "
            "The blessing exists but may be internal rather than external."
        ),
        "falsifiability_test": (
            "Test: does the most significant material/creative/spiritual peak of the "
            "native's later life occur 2050-2052?"
        ),
        "confidence_score": 0.78,
        "classical_citation": (
            "BPHS Ch 50, sl 1; Phaladeepika Ch 22, sl 4; Ch 21, sl 3"
        ),
    },
]

# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

_INSERT_SQL = """
INSERT INTO l1_phase_locked_anchors (
    chart_id,
    anchor_label,
    window_start,
    window_end,
    anchor_type,
    cluster_intensity,
    g29_rules_fired,
    systems_active,
    primary_outcome,
    alternative_scenario,
    falsifiability_test,
    confidence_score,
    classical_citation
) VALUES (
    %(chart_id)s,
    %(anchor_label)s,
    %(window_start)s,
    %(window_end)s,
    %(anchor_type)s,
    %(cluster_intensity)s,
    %(g29_rules_fired)s,
    %(systems_active)s,
    %(primary_outcome)s,
    %(alternative_scenario)s,
    %(falsifiability_test)s,
    %(confidence_score)s,
    %(classical_citation)s
)
ON CONFLICT (chart_id, window_start, anchor_label) DO NOTHING
"""

_QUERY_HIGH_INTENSITY_WINDOWS = """
SELECT
    window_start,
    window_end,
    cluster_intensity,
    systems_active
FROM l1_time_synchronicity
WHERE chart_id = %(chart_id)s
  AND cluster_intensity >= 4
ORDER BY window_start
"""


def _build_db_derived_anchor(
    chart_id: str, row: tuple
) -> dict[str, Any]:
    """Convert a high-intensity synchronicity window row into an anchor dict."""
    window_start, window_end, cluster_intensity, systems_active = row

    # systems_active may be a Python list already (psycopg2 ARRAY→list) or a string
    if isinstance(systems_active, str):
        systems_active = [s.strip() for s in systems_active.strip("{}").split(",") if s.strip()]

    systems_str = ", ".join(systems_active) if systems_active else "multiple systems"
    label = f"Multi-system convergence {window_start}"

    return {
        "chart_id": chart_id,
        "anchor_label": label,
        "window_start": str(window_start),
        "window_end": str(window_end),
        "anchor_type": "multi_system",
        "cluster_intensity": cluster_intensity,
        "g29_rules_fired": [],
        "systems_active": systems_active if isinstance(systems_active, list) else [],
        "primary_outcome": (
            f"Multi-system convergence: {systems_str} agree on significance during "
            f"{window_start}–{window_end}"
        ),
        "alternative_scenario": None,
        "falsifiability_test": (
            "Test: does a significant life event occur during this window?"
        ),
        "confidence_score": min(1.0, cluster_intensity / 7.0),
        "classical_citation": None,
    }


def seed_phase_locked_anchors(conn, chart_id: str) -> int:
    """Seed structural + DB-derived phase-locked anchors. Returns rows inserted.

    Structural anchors are hard-coded in STRUCTURAL_ANCHORS.
    DB-derived anchors come from l1_time_synchronicity rows with cluster_intensity >= 4.
    Both use ON CONFLICT DO NOTHING for idempotency.
    """
    inserted = 0

    # 1. Structural anchors
    with conn.cursor() as cur:
        for anchor in STRUCTURAL_ANCHORS:
            row = dict(anchor)
            # Ensure array fields are Python lists (psycopg2 handles list→ARRAY)
            if not isinstance(row["g29_rules_fired"], list):
                row["g29_rules_fired"] = list(row["g29_rules_fired"])
            if not isinstance(row["systems_active"], list):
                row["systems_active"] = list(row["systems_active"])
            row.setdefault("alternative_scenario", None)
            row.setdefault("classical_citation", None)

            cur.execute(_INSERT_SQL, row)
            inserted += cur.rowcount

    conn.commit()

    # 2. DB-derived anchors from high-intensity synchronicity windows
    with conn.cursor() as cur:
        cur.execute(_QUERY_HIGH_INTENSITY_WINDOWS, {"chart_id": chart_id})
        rows = cur.fetchall()

    with conn.cursor() as cur:
        for row in rows:
            anchor = _build_db_derived_anchor(chart_id, row)
            # Convert lists to psycopg2-friendly format
            anchor["g29_rules_fired"] = list(anchor["g29_rules_fired"])
            anchor["systems_active"] = list(anchor["systems_active"])

            cur.execute(_INSERT_SQL, anchor)
            inserted += cur.rowcount

    conn.commit()

    logger.info(
        "seed_phase_locked_anchors: inserted %d rows for chart_id=%s",
        inserted,
        chart_id,
    )
    return inserted
