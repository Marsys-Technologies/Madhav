"""
ga_ayurdaya_writer.py — GA ayurdaya / longevity writer (WP-2.5 / LCA-16)
========================================================================
Asset:  ga_ayurdaya
Table:  chart_facts   (fact_category = 'ayurdaya')
Grain:  per (chart × ayanamsha): 3 method-totals + per-graha contributions +
        applicability rule + maraka significators.

Root defect (REMEDIATION_PLAN_v2_0 §5 WP-2.5 / LCA-16): ayurdaya/longevity was never
computed by any L1 writer — no Pindayu/Nisargayu/Amsayu, no maraka linkage, no
alpa/madhya/purna classification.

BINDING RULING — §7.2 (immutable once ratified):
  Compute ALL THREE classical methods (Pindayu, Nisargayu, Amsayu), method-attributed,
  with the classical APPLICABILITY RULE served alongside (which method the canon prescribes
  for which chart class). NO autonomous adjudication of the doctrinal dispute over which
  method to trust — that is P-3's mandate, post-W4. This writer serves all three, attributed.

B.10 posture (no invented numbers): the base longevity contributions, the per-method full-
longevity constants, and the applicability rule are all DELEGATED to PyJHora's shipped,
cited ayurdaya implementation (jhora.horoscope.dhasa.graha.aayu + jhora.const —
pindayu_full_longevity_of_planets [19,25,15,12,15,21,20], nisargayu_full_longevity_of_planets
[20,1,2,9,18,20,50], amsayu = navamsa-arc method), the same trusted-delegation discipline as
migration 430. Base ayus are computed with apply_haranas=False (deterministic from the stored
longitudes alone — §N.5, no re-derivation of positions); the reductive haranas
(astangata/shatru-kshetra/chakrapata/krurodaya) are a documented W3 refinement flagged on
each method total, because they require benefic/malefic + combustion context that this writer
deliberately does not recompute.

  Amsayu uses PyJHora method=2 (Varahamihira navamsa-arc rule, (λ·0.3) mod 12); method=1
  (Santhanam (λ·108) mod 12) is degenerate in the shipped build and is NOT used — flagged.

Applicability rule (served, not adjudicated): the stronger of Lagna / Sun / Moon selects the
governing method — Lagna→Amsayu, Sun→Pindayu, Moon→Nisargayu (BPHS ayurdaya adhyaya).

Idempotency: L1 delete-then-insert scoped to (chart_id, ayanamsha_id, fact_category='ayurdaya').
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg.rows

from brahmagyan.graha_vocabulary import to_title

from jhora import const as _jconst
from jhora.horoscope.dhasa.graha import aayu as _aayu
from ga_writers._idempotency import replace_prior_chart_facts

logger = logging.getLogger(__name__)

GA_AYURDAYA_ASSET_ID = "ga_ayurdaya"
FACT_CATEGORY = "ayurdaya"
CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman",
    "surya_siddhanta_classical",
]

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]

# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2 (found via the full-tree census; not one of the originally-
# enumerated retirement targets). GRAHA_SUBJECT itself needs the REVERSE
# direction (title -> code), built by inverting SUBJECT_GRAHA.
SUBJECT_GRAHA = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN", "LAGNA")
}
GRAHA_SUBJECT = {v: k for k, v in SUBJECT_GRAHA.items()}
# jhora planet ids: 0=Sun..6=Saturn, 7=Rahu, 8=Ketu, 'L'=Lagna
_JHORA_ID = {"Sun": 0, "Moon": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4,
             "Venus": 5, "Saturn": 6, "Rahu": 7, "Ketu": 8}
SEVEN = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

AAYU_TYPE_NAME = {0: "pindayu", 1: "nisargayu", _jconst._ascendant_symbol: "amsayu"}

APPLICABILITY_CITATION = (
    "BPHS ayurdaya adhyaya: the stronger of Lagna / Sun / Moon selects the governing "
    "longevity method — Lagna→Amsayu, Sun→Pindayu, Moon→Nisargayu. Served, not adjudicated "
    "(method-trust dispute deferred to doctrine campaign P-3, post-W4)."
)
MARAKA_CITATION = (
    "BPHS maraka doctrine: the 2nd and 7th houses are maraka-sthanas; their lords and "
    "occupants, plus Saturn (natural maraka), are the death-inflicting significators whose "
    "dasha/antardasha activates the ayurdaya verdict."
)
CLASSIFICATION_CITATION = (
    "BPHS ayurdaya classification into alpayu / madhyayu / purnayu (deerghayu). Tri-partition "
    "thresholds 0-32 / 32-64 / >64 years, aligned to PyJHora const.longevity_years "
    "[[32,36,40],[64,72,80],[96,108,120]] life-class bands."
)


def classify_ayus(total_years: float) -> str:
    """Alpayu (<32) / madhyayu (32-64) / purnayu (>64) per BPHS ayurdaya."""
    if total_years < 32.0:
        return "alpayu"
    if total_years < 64.0:
        return "madhyayu"
    return "purnayu"


def build_planet_positions(positions: dict[str, dict]) -> Optional[list]:
    """Assemble jhora planet_positions [(id,(rasi,deg)),...] from stored L1 longitudes.
    Index 0 = Lagna, 1..7 = Sun..Saturn, 8 = Rahu, 9 = Ketu.

    `sign_num` MUST be 0-based (Aries=0) — jhora's rasi index is 0-based. The shared
    ga_sensitive_degree_writer.load_positions guarantees this (it converts the 1-based
    chart_facts.sign_num to 0-based, preferring longitude_sidereal)."""
    lag = positions.get("Lagna")
    if not lag or lag.get("sign_num") is None or lag.get("degree_in_sign") is None:
        return None
    pp: list = [(_jconst._ascendant_symbol, (int(lag["sign_num"]), float(lag["degree_in_sign"])))]
    for g in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        rec = positions.get(g)
        if not rec or rec.get("sign_num") is None or rec.get("degree_in_sign") is None:
            return None
        pp.append((_JHORA_ID[g], (int(rec["sign_num"]), float(rec["degree_in_sign"]))))
    return pp


def compute_method_totals(planet_positions: list) -> dict:
    """Return per-method {per-graha contributions, total} for all THREE methods, base
    (apply_haranas=False) — delegated to PyJHora's cited implementation."""
    pinda = _aayu._pindayu(planet_positions, apply_haranas=False, method=2)
    nisarga = _aayu._nisargayu(planet_positions, apply_haranas=False, method=2)
    amsa = _aayu._amsayu(planet_positions, apply_haranas=False, method=2)  # Varahamihira arc

    # Lagna contribution (rasi portion of the ascendant longitude — Santhanam lagna aayu).
    lag_sign, lag_deg = planet_positions[0][1]
    lagna_years = (lag_sign * 30 + lag_deg) / 30.0

    def _pack(contrib: dict, include_lagna: bool) -> dict:
        per = {p: round(float(v), 4) for p, v in contrib.items()}
        total = sum(contrib.values()) + (lagna_years if include_lagna else 0.0)
        return {"per_graha": per, "lagna_years": round(lagna_years, 4) if include_lagna else None,
                "total_years": round(total, 4)}

    return {
        "pindayu": _pack(pinda, include_lagna=True),
        "nisargayu": _pack(nisarga, include_lagna=True),
        "amsayu": _pack(amsa, include_lagna=True),
    }


def applicable_method(planet_positions: list) -> str:
    """Classical applicability rule → 'pindayu' | 'nisargayu' | 'amsayu'."""
    sp = _aayu._get_aayur_type(planet_positions)  # 0=Sun/Pinda, 1=Moon/Nisarga, 'L'=Lagna/Amsa
    return AAYU_TYPE_NAME.get(sp, "amsayu")


def compute_marakas(positions: dict[str, dict]) -> dict:
    """2nd & 7th lords + occupants + Saturn (natural maraka)."""
    lag = positions.get("Lagna")
    if not lag or lag.get("sign_num") is None:
        return {"maraka_grahas": [], "reason": "lagna_unknown"}
    ls = int(lag["sign_num"])
    second_sign = (ls + 1) % 12
    seventh_sign = (ls + 6) % 12
    lords = {SIGN_LORDS[second_sign], SIGN_LORDS[seventh_sign]}
    occupants = {g for g, r in positions.items()
                 if r.get("house_d1") in (2, 7) and g in SEVEN}
    marakas = sorted(lords | occupants | {"Saturn"})
    return {
        "maraka_grahas": marakas,
        "second_house_sign": SIGNS[second_sign], "second_lord": SIGN_LORDS[second_sign],
        "seventh_house_sign": SIGNS[seventh_sign], "seventh_lord": SIGN_LORDS[seventh_sign],
        "occupants_2_7": sorted(occupants),
        "natural_maraka": "Saturn",
    }


def _fact_id(subject, key, chart_id, ayanamsha_id, build_id) -> str:
    raw = f"{FACT_CATEGORY}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _row(chart_id, ayanamsha_id, build_id, subject, key, num, text, jsonb, citation,
         computed_at, provenance="single", unit=None) -> dict:
    return {
        "fact_id": _fact_id(subject, key, chart_id, ayanamsha_id, build_id),
        "chart_id": chart_id, "ayanamsha_id": ayanamsha_id, "build_id": build_id,
        "fact_category": FACT_CATEGORY, "fact_subject": subject, "fact_key": key,
        "fact_value_text": text, "fact_value_num": num,
        "fact_value_jsonb": json.dumps(jsonb) if jsonb is not None else None,
        "unit": unit,
        "citation_ref": f"WP-2.5/LCA-16/{key}",
        "citation_human": citation,
        "source_calculation": f"ga_ayurdaya_writer/{key}/{provenance}",
        "verification_pass_status": provenance,
        "engine_version": "ga_ayurdaya_v1",
        "computed_at": computed_at,
    }


def load_positions(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, dict]:
    """Reuse the sensitive-degree position reader (single L1-authority reader)."""
    from ga_writers.ga_sensitive_degree_writer import load_positions as _lp
    return _lp(conn, chart_id, ayanamsha_id)


def build_ayurdaya_rows(chart_id, build_id, ayanamsha_id, positions) -> list[dict]:
    """Pure builder — all ayurdaya rows for one (chart × ayanamsha)."""
    now = datetime.now(timezone.utc)
    pp = build_planet_positions(positions)
    if pp is None:
        return []
    totals = compute_method_totals(pp)
    applicable = applicable_method(pp)
    marakas = compute_marakas(positions)
    rows: list[dict] = []

    HARANA_NOTE = ("base ayus (apply_haranas=False); reductive haranas are a W3 refinement "
                   "(require combustion/enemy/benefic context not recomputed here)")

    for method in ("pindayu", "nisargayu", "amsayu"):
        m = totals[method]
        classification = classify_ayus(m["total_years"])
        subject = method.upper()
        prov = "single" if method != "amsayu" else "single"
        cite = (
            f"{method.capitalize()} longevity — PyJHora jhora.horoscope.dhasa.graha.aayu "
            f"(cited BPHS/Varahamihira). {HARANA_NOTE}."
            + (" Amsayu uses method=2 (Varahamihira navamsa-arc); method=1 degenerate/unused."
               if method == "amsayu" else "")
        )
        rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "total_years",
                         m["total_years"], classification,
                         {"per_graha": m["per_graha"], "lagna_years": m["lagna_years"],
                          "classification": classification, "method": method,
                          "harana_status": "base_only_haranas_deferred_to_w3"},
                         cite, now, provenance=prov, unit="years"))
        # per-graha contributions (evidence)
        for pid, years in m["per_graha"].items():
            gname = {v: k for k, v in _JHORA_ID.items()}.get(pid)
            if gname is None:
                continue
            rows.append(_row(chart_id, ayanamsha_id, build_id, GRAHA_SUBJECT[gname],
                             f"{method}_contribution_years", years, method,
                             {"method": method, "graha": gname}, cite, now,
                             provenance=prov, unit="years"))

    # applicability rule (served, not adjudicated)
    rows.append(_row(chart_id, ayanamsha_id, build_id, "CHART", "applicable_method",
                     None, applicable,
                     {"applicable_method": applicable,
                      "rule": "stronger_of_lagna_sun_moon",
                      "all_three_served": True,
                      "totals": {k: totals[k]["total_years"] for k in totals}},
                     APPLICABILITY_CITATION, now))

    # maraka significators
    rows.append(_row(chart_id, ayanamsha_id, build_id, "CHART", "maraka_grahas",
                     None, ",".join(marakas["maraka_grahas"]), marakas,
                     MARAKA_CITATION, now))
    return rows


def build_ga_ayurdaya_substep(chart_id: str, build_id: str, ayanamsha_id: str, conn: Any) -> int:
    """Build + insert ayurdaya rows for one (chart × ayanamsha). Never commits/closes conn."""
    positions = load_positions(conn, chart_id, ayanamsha_id)
    if not positions:
        logger.warning("[ga_ayurdaya] no positions for chart=%s aya=%s", chart_id, ayanamsha_id)
        return 0
    rows = build_ayurdaya_rows(chart_id, build_id, ayanamsha_id, positions)
    if not rows:
        logger.warning("[ga_ayurdaya] incomplete positions for chart=%s aya=%s",
                       chart_id, ayanamsha_id)
        return 0
    replace_prior_chart_facts(conn, rows)
    inserted = 0
    for r in rows:
        conn.execute(
            """
            INSERT INTO chart_facts
              (fact_id, chart_id, ayanamsha_id, build_id,
               fact_category, fact_subject, fact_key,
               fact_value_text, fact_value_num, fact_value_jsonb,
               unit, citation_ref, citation_human,
               source_calculation, verification_pass_status,
               engine_version, computed_at)
            VALUES
              (%(fact_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
               %(fact_category)s, %(fact_subject)s, %(fact_key)s,
               %(fact_value_text)s, %(fact_value_num)s, %(fact_value_jsonb)s,
               %(unit)s, %(citation_ref)s, %(citation_human)s,
               %(source_calculation)s, %(verification_pass_status)s,
               %(engine_version)s, %(computed_at)s)
            ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
            WHERE formula_id IS NULL
            DO UPDATE SET
              fact_id         = EXCLUDED.fact_id,
              fact_value_text = EXCLUDED.fact_value_text,
              fact_value_num  = EXCLUDED.fact_value_num,
              fact_value_jsonb= EXCLUDED.fact_value_jsonb,
              citation_human  = EXCLUDED.citation_human,
              computed_at     = EXCLUDED.computed_at
            """,
            r,
        )
        inserted += 1
    logger.info("[ga_ayurdaya] chart=%s aya=%s inserted %d rows", chart_id, ayanamsha_id, inserted)
    return inserted
