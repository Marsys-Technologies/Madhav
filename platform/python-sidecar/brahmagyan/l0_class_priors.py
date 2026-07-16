"""
brahmagyan.l0_class_priors — bg_class_priors L0 global seed.

Populates brahma_class_priors with 165 rows across 5 prior axes:
  · 17 signal_type_class rows
  · 12 source_subsystem rows
  · 6 signal_tradition rows
  · 30 varga base weight rows (with domain overlay JSONB)
  · 99 graha×domain affinity rows (9 grahas × 11 domains)

Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §2–§4.
Idempotency: L0 = ON CONFLICT DO UPDATE (global, not per-chart).

Row encoding convention (5-column PK):
  (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)

Sentinel '*' = "all" on non-active axes.
Varga rows:  signal_type_class='varga',        fact_kind=D<n>
Graha×domain: signal_type_class='graha_domain', fact_kind=<graha>, source_subsystem=<domain>
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

PRIOR_VERSION = "1.0"

# ── §2.1 signal_type_class weights ───────────────────────────────────────────
# (signal_type_class, class_prior, citation)
CLASS_ROWS: list[tuple] = [
    ("configuration",   1.40, "BPHS yoga/phala chapters — yogas are the headline structures"),
    ("yoga",            1.40, "Alias for configuration; same classical authority"),
    ("relationship",    1.20, "Parivartana/argala/aspects: chart wiring; BPHS bhava chapters"),
    ("position",        1.10, "Atomic backbone — graha in sign/house/dignity; BPHS"),
    ("dasha_period",    1.15, "Timing is half of Jyotish; period lord condition is first-class"),
    ("time_window",     0.95, "Derived timing; slightly below period itself"),
    ("birth_moment",    1.05, "Foundational panchanga; BPHS tithi/vara/nakshatra chapters"),
    ("annual",          0.85, "Varshaphala/tajika — powerful but tradition-scoped"),
    ("medical",         0.90, "Domain-specific; high within health, humble elsewhere"),
    ("vastu",           0.70, "Environmental/remedial; genuinely peripheral to natal judgment"),
    ("prashna",         1.00, "Only fires on prashna charts; gated by chart_type"),
    ("absence",         0.80, "Absent yoga is real evidence; weaker than a present one"),
    ("composite_state", 1.20, "Multi-system structural composite; equivalent to relationship"),
    ("karaka_alignment",1.05, "Karaka congruence; between position and structural level"),
    ("parivartana",     1.20, "Exchange of signs — equivalent to relationship class"),
    ("varga_pattern",   0.95, "Vargottama/varga structure; above birth_moment, below position"),
    ("magnitude",       1.00, "Bala/strength scores; modulates delivery; baseline"),
    # ── D-1.5b Lane B-3 (CR-100, Sudarśana Chakra) — appended-only per
    # DIS.016/DR-3 ratified constant (00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md).
    # Do NOT reorder/edit the rows above this line — B-4 (Bhavat Bhavam)
    # appends its own bhavat_bhavam_amplifier row separately, same convention.
    ("sudarshana_agreement", 1.15, "DIS.016/DR-3 ratified 2026-07-15: tri-frame "
     "(Lagna/Chandra/Surya) corroboration is relationship-grade wiring but "
     "derivative of existing positions — between position (1.10) and "
     "composite_state (1.20)"),
    # D-1.5b Lane B-4 (CR-97) — DIS.016/DR-3 ratified 2026-07-15 (Fable 5
    # adjudicator-doctrine proposal, formalized by the D-1.5b conductor).
    # GATED AMPLIFIER: fires only atop an already-salient primary (tier>=major
    # or fired yoga); below every existing anchor except "absence" (0.80) so it
    # can never outrank the primary it corroborates (primary anchors are all
    # >=0.85 wherever B-4 can fire — see DR-3 resolution). Never a generator;
    # code-enforced never-outranks-primary + no-chaining guards live in
    # bodha_writers/bhavat_bhavam_amplifier.py, not in this prior alone.
    ("bhavat_bhavam_amplifier", 0.85, "DIS.016/DR-3: Bhavat-Bhavam gated amplifier — corroborating-only, never a generator"),
    # D-2 Lane V-5 (CR-26/64, CR-61, CR-76, CR-36) — DIS.019/DR-6 ratified
    # 2026-07-16 (Fable 5 D-2 Binder proposal, BIND_D-2.md §B.2, recorded by
    # the D-2 conductor per protocol §8.8(ii)). APPEND-ONLY per this file's
    # shared-file discipline (V-5 + V-6 both append; do not reorder/edit the
    # rows above this line).
    ("nakshatra_semantic", 1.00, "DIS.019/DR-6: high-volume corroborative fabric "
     "(own-star, dispositor chains, tara bala) — neutral class-wide prior so it "
     "enriches without flooding; gandanta/end-degree flags earn a per-signal "
     "specificity boost, never a class-wide one"),
    ("arudha", 1.10, "DIS.019/DR-6: Jaimini perception layer (AL conjunctions, "
     "A2/A11, AL-bhava relations) — reading-bearing per CR-61, modest boost "
     "above fabric"),
    ("special_lagna", 0.90, "DIS.019/DR-6: Indu/Sree/Ghati/Hora Lagna are "
     "domain-scoped corroborators — below-neutral chart-wide; domain_salience "
     "on each signal carries in-domain rank, mirroring DR-3's sudarshana "
     "supporting-tier treatment"),
    ("vargottama_amplification", 1.15, "DIS.019/DR-6: cross-frame (D1/D9) "
     "confirmation class — same epistemics as sudarshana_agreement's DR-3 1.15"),
    ("dhana_axis", 1.05, "DIS.019/DR-6: domain-load-bearing 2nd/11th-house "
     "tenancy class, overlapping existing dhana-yoga rows — slight boost, "
     "dedup discipline against the yoga class enforced at emission"),
]

# ── §2.2 source_subsystem weights ────────────────────────────────────────────
# (source_subsystem, class_prior, citation)
SUBSYSTEM_ROWS: list[tuple] = [
    ("structural",           1.00, "Baseline structural provenance"),
    ("dasha",                1.10, "Dasha-sourced: timing premium"),
    ("yoga",                 1.15, "Yoga-sourced: formation premium"),
    ("strength_ashtakavarga",0.95, "AV bindus; useful but supplementary"),
    ("nakshatra",            1.05, "Nakshatra-sourced: lunar layer"),
    ("sensitive",            1.00, "Sensitive points: parity with structural"),
    ("varga",                1.00, "Varga-sourced: varga-grain weight does real work"),
    ("tajaka",               0.85, "Tajaka/varshaphala: tradition-scoped"),
    ("sade_sati",            1.05, "Sade Sati: significant transit pattern"),
    ("panchanga",            0.90, "Panchanga-sourced: birth-moment quality"),
    ("medical",              0.90, "Medical subsystem: domain-gated relevance"),
    ("vastu",                0.70, "Vastu: environmental; peripheral to natal"),
]

# ── §2.3 signal_tradition weights ────────────────────────────────────────────
# (signal_tradition, class_prior, citation)
TRADITION_ROWS: list[tuple] = [
    ("parashari", 1.00, "BPHS spine — canonical Parashara tradition"),
    ("jaimini",   0.95, "Jaimini Sutram — strong but method-specific"),
    ("kp",        0.90, "KP Reader system"),
    ("tajika",    0.85, "Tajika/Persian-Arabic system"),
    ("nadi",      0.80, "Bhrigu-Nandi/Nadi-Navamsa — powerful but method-sensitive"),
    ("lal_kitab", 0.70, "Lal Kitab — folk tradition; lowest classical authority"),
]

# ── §3.1 + §3.2 Varga base weights + domain overlays ─────────────────────────
# (varga_key, base_weight, domain_overlays_dict_or_None, citation)
VARGA_ROWS: list[tuple] = [
    ("D1",   1.00, {"career": 1.5, "health": 1.5, "relationship": 1.5, "character": 1.5},
     "BPHS Vimshopaka: D1=3.5/max; D1-overlay career/health/relat./char."),
    ("D2",   0.45, {"wealth": 1.5},
     "BPHS Vimshopaka: D2=1.0; Hora=wealth"),
    ("D3",   0.45, None,
     "BPHS Vimshopaka: D3=1.0; Drekkana; no specific domain overlay"),
    ("D4",   0.30, {"residence": 1.5, "family": 1.5},
     "BPHS Vimshopaka: D4=0.5; Chaturthamsha=property/fortune; family/residence overlay"),
    ("D5",   0.18, None, "Supplementary varga (not in Shodasavarga); floor weight"),
    ("D6",   0.18, None, "Supplementary varga; floor weight"),
    ("D7",   0.30, {"progeny": 1.5},
     "BPHS Vimshopaka: D7=0.5; Saptamsha=children"),
    ("D8",   0.18, None, "Supplementary varga; floor weight"),
    ("D9",   0.90, {"relationship": 1.5, "progeny": 1.5, "education": 1.5, "character": 1.5},
     "BPHS Vimshopaka: D9=3.0; Navamsha=spouse/dharma — highest after D1"),
    ("D10",  0.55, {"career": 1.5},
     "D10 lifted: 0.5→0.55 (BPHS base) + career overlay; modern practice weights Dashamsha for profession"),
    ("D11",  0.18, None, "Supplementary varga; floor weight"),
    ("D12",  0.32, {"family": 1.5},
     "BPHS Vimshopaka: D12=0.5; Dvadashamsha=parents/lineage"),
    ("D14",  0.18, None, "Supplementary varga; floor weight"),
    ("D15",  0.18, None, "Supplementary varga; floor weight"),
    ("D16",  0.60, {"character": 1.5},
     "BPHS Vimshopaka: D16=2.0; Shodashamsha=comforts/temperament"),
    ("D20",  0.35, {"spirituality": 1.5},
     "BPHS Vimshopaka: D20=0.5; Vimshamsha=worship/upasana"),
    ("D21",  0.18, None, "Supplementary varga; floor weight"),
    ("D24",  0.30, {"education": 1.5},
     "BPHS Vimshopaka: D24=0.5; Siddhamsha=learning/education"),
    ("D27",  0.30, None, "BPHS Vimshopaka: D27=0.5; Bhamsha"),
    ("D30",  0.45, {"health": 1.5},
     "BPHS Vimshopaka: D30=1.0; Trimshamsha=evils/afflictions/health"),
    ("D32",  0.18, None, "Supplementary varga; floor weight"),
    ("D33",  0.18, None, "Supplementary varga; floor weight"),
    ("D40",  0.28, None, "BPHS Vimshopaka: D40=0.5; Khavedamsha"),
    ("D45",  0.28, None, "BPHS Vimshopaka: D45=0.5; Akshavedamsha"),
    ("D50",  0.18, None, "Supplementary varga; floor weight"),
    ("D54",  0.18, None, "Supplementary varga; floor weight"),
    ("D60",  0.95, {"spirituality": 1.5},
     "BPHS Vimshopaka: D60=4.0 (Parashara: foremost); spirituality overlay; time-sensitive"),
    ("D108", 0.12, None, "Nadi varga; present-queryable; floor weight only"),
    ("D150", 0.12, None, "Nadi varga; floor weight"),
    ("D2700",0.12, None, "Nadi varga; floor weight"),
]

# ── §4 Graha × Domain affinity matrix ────────────────────────────────────────
# 9 grahas × 11 life-domains (excl. general which has no karaka = neutral 1.0)
# Format: (graha_code, domain, affinity, citation)
GRAHA_DOMAIN_ROWS: list[tuple] = [
    # Sun
    ("SU", "career",       1.40, "BPHS: Sun=10th-house natural significator, king/authority karaka"),
    ("SU", "wealth",       1.00, "BPHS: Sun=dhana only indirectly"),
    ("SU", "relationship", 0.80, "Sun is separative for 7th-house matters"),
    ("SU", "progeny",      0.90, "Sun=3rd/5th only weakly"),
    ("SU", "health",       1.10, "Sun=vitality/longevity (with 1st lord)"),
    ("SU", "education",    1.00, "Sun=education moderately"),
    ("SU", "family",       1.10, "Sun=father karaka (BPHS)"),
    ("SU", "residence",    0.90, "Sun=residence weakly"),
    ("SU", "travel",       0.90, "Sun=travel weakly"),
    ("SU", "spirituality", 1.00, "Sun=dharma moderately"),
    ("SU", "character",    1.10, "Sun=self/soul/atma"),
    # Moon
    ("MO", "career",       1.00, "Moon=career neutrally"),
    ("MO", "wealth",       1.00, "Moon=wealth neutrally"),
    ("MO", "relationship", 1.10, "Moon=emotional bond, 7th affinity"),
    ("MO", "progeny",      1.00, "Moon=progeny moderately"),
    ("MO", "health",       1.10, "Moon=mind-body, fluids"),
    ("MO", "education",    1.00, "Moon=education moderately"),
    ("MO", "family",       1.30, "Moon=mother karaka (BPHS, strongest)"),
    ("MO", "residence",    1.00, "Moon=residence moderately"),
    ("MO", "travel",       1.00, "Moon=travel moderately"),
    ("MO", "spirituality", 1.00, "Moon=spirituality moderately"),
    ("MO", "character",    1.40, "Moon=mind/temperament karaka — strongest character significator"),
    # Mars
    ("MA", "career",       1.20, "Mars=military/technical career, 10th signification"),
    ("MA", "wealth",       1.00, "Mars=wealth neutrally"),
    ("MA", "relationship", 1.00, "Mars=energy in relationship; Manglik watch"),
    ("MA", "progeny",      0.90, "Mars=progeny weakly"),
    ("MA", "health",       1.20, "Mars=surgery/accident/blood (BPHS 6/8 lords)"),
    ("MA", "education",    0.90, "Mars=technical skill not broad education"),
    ("MA", "family",       1.00, "Mars=siblings (3rd house)"),
    ("MA", "residence",    1.40, "Mars=bhumi-karaka (land/property) strongest"),
    ("MA", "travel",       1.00, "Mars=travel moderately"),
    ("MA", "spirituality", 0.90, "Mars=spiritual weakly"),
    ("MA", "character",    1.10, "Mars=courage/aggression aspect of character"),
    # Mercury
    ("ME", "career",       1.20, "Mercury=commerce/communication career"),
    ("ME", "wealth",       1.20, "Mercury=commerce/trade wealth (BPHS)"),
    ("ME", "relationship", 1.00, "Mercury=relationship neutrally (contracts)"),
    ("ME", "progeny",      1.00, "Mercury=intellect/progeny moderately"),
    ("ME", "health",       1.00, "Mercury=nervous system moderately"),
    ("ME", "education",    1.40, "Mercury=vidya-karaka — education karaka (Jaimini)"),
    ("ME", "family",       1.00, "Mercury=family neutrally"),
    ("ME", "residence",    0.90, "Mercury=residence weakly"),
    ("ME", "travel",       1.10, "Mercury=short journeys/3rd house"),
    ("ME", "spirituality", 1.00, "Mercury=spirituality moderately"),
    ("ME", "character",    1.20, "Mercury=intellect/discrimination aspect of character"),
    # Jupiter
    ("JU", "career",       1.10, "Jupiter=authority/guru/law career"),
    ("JU", "wealth",       1.30, "Jupiter=dhana-karaka (BPHS wealth significator)"),
    ("JU", "relationship", 1.10, "Jupiter=vivaha significator (Jaimini DK)"),
    ("JU", "progeny",      1.50, "Jupiter=putra-karaka — STRONGEST progeny significator"),
    ("JU", "health",       1.00, "Jupiter=health moderately (liver/fat)"),
    ("JU", "education",    1.30, "Jupiter=higher learning/guru/jnana-karaka"),
    ("JU", "family",       1.10, "Jupiter=pitri/family broadly"),
    ("JU", "residence",    1.00, "Jupiter=residence moderately"),
    ("JU", "travel",       1.00, "Jupiter=long-distance pilgrimage travel"),
    ("JU", "spirituality", 1.40, "Jupiter=dharma-karaka; jnana/moksha significator"),
    ("JU", "character",    1.10, "Jupiter=wisdom/expansion aspect of character"),
    # Venus
    ("VE", "career",       1.00, "Venus=arts/beauty career moderately"),
    ("VE", "wealth",       1.20, "Venus=luxury/material wealth (BPHS)"),
    ("VE", "relationship", 1.50, "Venus=kalatra-karaka — STRONGEST spouse/partner significator"),
    ("VE", "progeny",      1.20, "Venus=arts/creative progeny"),
    ("VE", "health",       1.00, "Venus=health moderately (reproductive)"),
    ("VE", "education",    1.00, "Venus=arts education moderately"),
    ("VE", "family",       1.00, "Venus=family moderately"),
    ("VE", "residence",    1.20, "Venus=vehicles/comforts/home luxury (4th signification)"),
    ("VE", "travel",       1.00, "Venus=travel moderately"),
    ("VE", "spirituality", 0.90, "Venus=spirituality weakly (worldly attachment)"),
    ("VE", "character",    1.10, "Venus=refinement/aesthetics aspect of character"),
    # Saturn
    ("SA", "career",       1.40, "Saturn=karma-karaka — STRONGEST career significator (10th house)"),
    ("SA", "wealth",       1.00, "Saturn=wealth neutrally (delays gains)"),
    ("SA", "relationship", 0.90, "Saturn=relationship with difficulty/delay"),
    ("SA", "progeny",      0.80, "Saturn=progeny weakly (reduces/delays)"),
    ("SA", "health",       1.20, "Saturn=chronic illness/ayushkaraka (longevity)"),
    ("SA", "education",    0.90, "Saturn=technical mastery but slow learning"),
    ("SA", "family",       0.90, "Saturn=family with difficulty/loss"),
    ("SA", "residence",    1.20, "Saturn=labor/land/property maintenance"),
    ("SA", "travel",       1.00, "Saturn=travel moderately"),
    ("SA", "spirituality", 1.10, "Saturn=vairagya/renunciation aspect"),
    ("SA", "character",    1.00, "Saturn=discipline/endurance aspect of character"),
    # Rahu
    ("RA", "career",       1.10, "Rahu=unconventional/technical career"),
    ("RA", "wealth",       1.10, "Rahu=speculation/sudden wealth"),
    ("RA", "relationship", 0.90, "Rahu=unconventional/cross-cultural relationship"),
    ("RA", "progeny",      0.80, "Rahu=progeny weakly"),
    ("RA", "health",       1.00, "Rahu=mysterious ailments moderately"),
    ("RA", "education",    1.00, "Rahu=education moderately"),
    ("RA", "family",       0.80, "Rahu=family disruption"),
    ("RA", "residence",    1.00, "Rahu=residence moderately"),
    ("RA", "travel",       1.40, "Rahu=foreign lands/distant travel (BPHS 12th/9th)"),
    ("RA", "spirituality", 1.10, "Rahu=maya; unconventional spiritual path"),
    ("RA", "character",    1.00, "Rahu=character moderately"),
    # Ketu
    ("KE", "career",       0.90, "Ketu=career disruption/technical but scattered"),
    ("KE", "wealth",       0.90, "Ketu=wealth with loss/renunciation"),
    ("KE", "relationship", 0.80, "Ketu=relationship weakly (isolation tendency)"),
    ("KE", "progeny",      0.80, "Ketu=progeny weakly (reduces)"),
    ("KE", "health",       1.10, "Ketu=occult ailments/mysterious health factors"),
    ("KE", "education",    1.00, "Ketu=education moderately (esoteric)"),
    ("KE", "family",       0.90, "Ketu=family weakly"),
    ("KE", "residence",    0.90, "Ketu=residence weakly"),
    ("KE", "travel",       1.10, "Ketu=pilgrimage/spiritual travel"),
    ("KE", "spirituality", 1.50, "Ketu=moksha-karaka — STRONGEST spiritual significator"),
    ("KE", "character",    1.10, "Ketu=detachment/past-karma aspect of character"),
]


def seed_class_priors(
    conn: Any,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, int]:
    """
    Upsert all 165 rows into brahma_class_priors across 5 prior axes.

    Returns {"brahma_class_priors": <total_upserted>}.

    autocommit: if False, caller owns the transaction (pass False from asset_runner).
    """
    total_expected = (
        len(CLASS_ROWS) + len(SUBSYSTEM_ROWS) + len(TRADITION_ROWS)
        + len(VARGA_ROWS) + len(GRAHA_DOMAIN_ROWS)
    )

    if dry_run:
        logger.info("[L0/class_priors] dry_run — would upsert %d rows", total_expected)
        return {"brahma_class_priors": total_expected}

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='brahma_class_priors'"
        )
        if cur.fetchone()["count"] == 0:
            raise RuntimeError(
                "brahma_class_priors table does not exist — apply migration 387 first."
            )

        upserted = 0

        # ── §2.1 signal_type_class rows ───────────────────────────────────────
        for (stc, prior, cit) in CLASS_ROWS:
            cur.execute(
                """
                INSERT INTO brahma_class_priors
                  (prior_version, signal_type_class, fact_kind, source_subsystem,
                   signal_tradition, class_prior, citation, ratified_by)
                VALUES (%s, %s, '*', '*', '*', %s, %s, 'W1_SEED_PACKAGE_v1_0')
                ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
                DO UPDATE SET class_prior = EXCLUDED.class_prior,
                              citation    = EXCLUDED.citation,
                              ratified_by = EXCLUDED.ratified_by
                """,
                (PRIOR_VERSION, stc, prior, cit),
            )
            upserted += 1

        # ── §2.2 source_subsystem rows ────────────────────────────────────────
        for (ss, prior, cit) in SUBSYSTEM_ROWS:
            cur.execute(
                """
                INSERT INTO brahma_class_priors
                  (prior_version, signal_type_class, fact_kind, source_subsystem,
                   signal_tradition, class_prior, citation, ratified_by)
                VALUES (%s, '*', '*', %s, '*', %s, %s, 'W1_SEED_PACKAGE_v1_0')
                ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
                DO UPDATE SET class_prior = EXCLUDED.class_prior,
                              citation    = EXCLUDED.citation,
                              ratified_by = EXCLUDED.ratified_by
                """,
                (PRIOR_VERSION, ss, prior, cit),
            )
            upserted += 1

        # ── §2.3 signal_tradition rows ────────────────────────────────────────
        for (trad, prior, cit) in TRADITION_ROWS:
            cur.execute(
                """
                INSERT INTO brahma_class_priors
                  (prior_version, signal_type_class, fact_kind, source_subsystem,
                   signal_tradition, class_prior, citation, ratified_by)
                VALUES (%s, '*', '*', '*', %s, %s, %s, 'W1_SEED_PACKAGE_v1_0')
                ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
                DO UPDATE SET class_prior = EXCLUDED.class_prior,
                              citation    = EXCLUDED.citation,
                              ratified_by = EXCLUDED.ratified_by
                """,
                (PRIOR_VERSION, trad, prior, cit),
            )
            upserted += 1

        # ── §3 varga rows ─────────────────────────────────────────────────────
        for (varga, base, overlays, cit) in VARGA_ROWS:
            cur.execute(
                """
                INSERT INTO brahma_class_priors
                  (prior_version, signal_type_class, fact_kind, source_subsystem,
                   signal_tradition, class_prior, varga_weights, citation, ratified_by)
                VALUES (%s, 'varga', %s, '*', '*', %s, %s::jsonb, %s, 'W1_SEED_PACKAGE_v1_0')
                ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
                DO UPDATE SET class_prior   = EXCLUDED.class_prior,
                              varga_weights = EXCLUDED.varga_weights,
                              citation      = EXCLUDED.citation,
                              ratified_by   = EXCLUDED.ratified_by
                """,
                (
                    PRIOR_VERSION, varga, base,
                    json.dumps(overlays) if overlays else None,
                    cit,
                ),
            )
            upserted += 1

        # ── §4 graha×domain rows ──────────────────────────────────────────────
        for (graha, domain, affinity, cit) in GRAHA_DOMAIN_ROWS:
            cur.execute(
                """
                INSERT INTO brahma_class_priors
                  (prior_version, signal_type_class, fact_kind, source_subsystem,
                   signal_tradition, class_prior, citation, ratified_by)
                VALUES (%s, 'graha_domain', %s, %s, '*', %s, %s, 'W1_SEED_PACKAGE_v1_0')
                ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
                DO UPDATE SET class_prior = EXCLUDED.class_prior,
                              citation    = EXCLUDED.citation,
                              ratified_by = EXCLUDED.ratified_by
                """,
                (PRIOR_VERSION, graha, domain, affinity, cit),
            )
            upserted += 1

    if autocommit:
        conn.commit()

    logger.info("[L0/class_priors] upserted %d rows across 5 axes", upserted)
    return {"brahma_class_priors": upserted}
