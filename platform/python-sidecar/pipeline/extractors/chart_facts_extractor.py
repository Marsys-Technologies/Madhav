# DEPRECATED 2026-05-10 — VARGA-ETL-FULL-S1-CPA
# This extractor produced a parallel chart_facts population that races with the
# YAML pipeline's staging-swap. The dual-pipeline race condition (Pipeline A
# DELETE-then-INSERT vs Pipeline B ON CONFLICT upserts) caused divisional rows
# to disappear depending on run order. All of its categories have been migrated
# into CHART_FACTS_EXTRACTION_v1_0.yaml v1.1 (the new YAML is the canonical
# single source of truth for chart_facts). This file is frozen — do not extend
# it; do not invoke chart_facts_loader against it for new ingests.
#
# The canonical pipeline is: ingest_chart_facts.py -> chart_facts_writer.py
# (reads CHART_FACTS_EXTRACTION_v1_0.yaml from GCS, validates against schema,
#  writes to chart_facts_staging, swaps to chart_facts via DELETE-then-INSERT).
#
# See 00_ARCHITECTURE/CHART_FACTS_PIPELINE_AUDIT_v1_0.md for the full rationale.
"""
pipeline.extractors.chart_facts_extractor — FROZEN/DEPRECATED 2026-05-10
KARN-W2-R2-CHART-FACTS-ETL — Parse FORENSIC_ASTROLOGICAL_DATA_v8_0.md for
sections §6–§24 and produce chart_facts rows for new categories.

Produces ~190–215 new rows across 19 categories:
  shadbala, bhava_bala, ishta_kashta, strength_extra,
  ashtakavarga_bav, ashtakavarga_sav, ashtakavarga_pinda,
  kakshya_zone, avastha, upagraha, sensitive_point, mrityu_bhaga,
  arudha_occupancy, aspect, chalit_shift, chandra_placement,
  deity_assignment, varshphal, longevity_indicator

Each returned dict has keys:
  fact_id, category, divisional_chart, value_text, value_json, source_section
value_number is omitted (loader sets None when absent).
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Table-parsing utilities
# ──────────────────────────────────────────────────────────

def _parse_md_table(text: str) -> list[dict[str, str]]:
    """Parse a single markdown table block into list-of-dicts.

    Expects rows like:  | col1 | col2 | col3 |
    Returns empty list if no table found.
    """
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break  # table ended
            continue
        # skip separator rows (| --- | --- |)
        if re.match(r"^\|[\s\-|]+\|$", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)

    if len(rows) < 2:
        return []

    headers = rows[0]
    result = []
    for row in rows[1:]:
        # pad/trim to header length
        padded = (row + [""] * len(headers))[: len(headers)]
        result.append(dict(zip(headers, padded)))
    return result


def _find_tables(section_text: str) -> list[str]:
    """Return list of raw markdown table blocks found in section_text."""
    tables: list[str] = []
    current_lines: list[str] = []
    in_table = False

    for line in section_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            in_table = True
            current_lines.append(line)
        else:
            if in_table and current_lines:
                tables.append("\n".join(current_lines))
                current_lines = []
            in_table = False

    if in_table and current_lines:
        tables.append("\n".join(current_lines))

    return tables


def _extract_section(md: str, h2_anchor: str) -> str:
    """Extract text of H2 section whose heading contains h2_anchor.

    Returns text from the matching ## line to the next ## line (exclusive).
    """
    lines = md.splitlines()
    start_idx: int | None = None

    # Use boundary-aware match: §9 must not be followed by another digit
    _anchor_re = re.compile(re.escape(h2_anchor) + r"(?:\s|—|–|-|\.|$)")
    for i, line in enumerate(lines):
        if line.startswith("## ") and _anchor_re.search(line):
            start_idx = i
            break

    if start_idx is None:
        return ""

    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if lines[i].startswith("## "):
            end_idx = i
            break

    return "\n".join(lines[start_idx:end_idx])


def _extract_subsection(section_text: str, h3_anchor: str) -> str:
    """Extract text of an H3 subsection within a section block."""
    lines = section_text.splitlines()
    start_idx: int | None = None

    _sub_anchor_re = re.compile(re.escape(h3_anchor) + r"(?:\s|—|–|-|\.|$)")
    for i, line in enumerate(lines):
        if line.startswith("### ") and _sub_anchor_re.search(line):
            start_idx = i
            break

    if start_idx is None:
        return ""

    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if lines[i].startswith("## ") or lines[i].startswith("### "):
            end_idx = i
            break

    return "\n".join(lines[start_idx:end_idx])


def _clean_id(raw: str) -> str:
    """Strip backtick wrappers from ID cell values."""
    return raw.strip().strip("`").strip()


def _row(
    fact_id: str,
    category: str,
    value_text: str,
    value_json: dict[str, Any],
    source_section: str,
    divisional_chart: str = "D1",
) -> dict[str, Any]:
    return {
        "fact_id": fact_id,
        "category": category,
        "divisional_chart": divisional_chart,
        "value_text": value_text,
        "value_json": value_json,
        "source_section": source_section,
    }


# ──────────────────────────────────────────────────────────
# §6 — STRENGTH METRICS
# ──────────────────────────────────────────────────────────

_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
_PLANET_SHORT = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MARS",
    "Mercury": "MER", "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
}

_SBL_COMPONENT_MAP = {
    "SBL.UCHA": ("ucha_bala", "Ucha Bala (Exaltation)"),
    "SBL.SAPT": ("sapta_bala", "Saptavargaja Bala"),
    "SBL.OJAY": ("ojay_bala", "Ojayugmarasyamsa Bala"),
    "SBL.KEND": ("kendra_bala", "Kendra Bala"),
    "SBL.DREK": ("drekkana_bala", "Drekkana Bala"),
    "SBL.STHANA.TOTAL": ("sthana_bala", "Total Sthana Bala"),
    "SBL.DIG.TOTAL": ("dig_bala", "Total Dig Bala"),
    "SBL.NATH": ("nath_bala", "Nathonnatha Bala"),
    "SBL.PAKSHA": ("paksha_bala", "Paksha Bala"),
    "SBL.TRIBH": ("tribhaga_bala", "Tribhaga Bala"),
    "SBL.ABDA": ("abda_bala", "Abda Bala"),
    "SBL.MASA": ("masa_bala", "Masa Bala"),
    "SBL.VARA": ("vara_bala", "Vara Bala"),
    "SBL.HORA": ("hora_bala", "Hora Bala"),
    "SBL.AYANA": ("ayana_bala", "Ayana Bala"),
    "SBL.YUDDHA": ("yuddha_bala", "Yuddha Bala"),
    "SBL.KALA.TOTAL": ("kala_bala", "Total Kala Bala"),
    "SBL.CHESTA.TOTAL": ("chesta_bala", "Total Chesta Bala"),
    "SBL.NAISARG.TOTAL": ("naisargika_bala", "Total Naisargika Bala"),
    "SBL.DRIK.TOTAL": ("drik_bala", "Total Drik Bala"),
}

_SBL_COMPONENT_TO_SLOT = {k: v[0] for k, v in _SBL_COMPONENT_MAP.items()}


def parse_section_6(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §6 Strength Metrics into chart_facts rows."""
    sec = _extract_section(md, "§6")
    rows: list[dict[str, Any]] = []

    # §6.1 Shadbala component breakdown — transpose planet columns → per-planet rows
    sub61 = _extract_subsection(sec, "§6.1")
    tables = _find_tables(sub61)
    if tables:
        planet_components: dict[str, dict[str, Any]] = {p: {} for p in _PLANETS}
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            slot = _SBL_COMPONENT_TO_SLOT.get(row_id)
            if slot is None:
                continue
            for planet in _PLANETS:
                raw_val = trow.get(planet, "").strip()
                try:
                    planet_components[planet][slot] = float(raw_val)
                except ValueError:
                    planet_components[planet][slot] = raw_val

        for planet in _PLANETS:
            pshort = _PLANET_SHORT[planet]
            components = planet_components[planet]
            rows.append(_row(
                fact_id=f"SHB.{pshort}",
                category="shadbala",
                value_text=f"{planet} Shadbala components",
                value_json={"planet": planet, **components},
                source_section="§6.1",
            ))

    # §6.2 Shadbala totals + ranking (FORENSIC + JH)
    sub62 = _extract_subsection(sec, "§6.2")
    tables = _find_tables(sub62)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            try:
                forensic_viru = float(trow.get("FORENSIC Virupas", "0") or "0")
            except ValueError:
                forensic_viru = None
            try:
                forensic_rupas = float(trow.get("FORENSIC Rupas", "0") or "0")
            except ValueError:
                forensic_rupas = None
            try:
                jh_rupas = float(trow.get("JH Rupas", "0") or "0")
            except ValueError:
                jh_rupas = None
            rows.append(_row(
                fact_id=row_id,
                category="shadbala",
                value_text=f"{planet} Shadbala total: FORENSIC {forensic_rupas} rupas / JH {jh_rupas} rupas",
                value_json={
                    "planet": planet,
                    "forensic_virupas": forensic_viru,
                    "forensic_rupas": forensic_rupas,
                    "forensic_rank": trow.get("FORENSIC Rank", "").strip() or None,
                    "jh_rupas": jh_rupas,
                    "jh_rank": trow.get("JH Rank", "").strip() or None,
                    "min_required_rupas": trow.get("Min Required (Rupas)", "").strip() or None,
                },
                source_section="§6.2",
            ))

    # §6.3 Uccha Bala Ranking → strength_extra
    sub63 = _extract_subsection(sec, "§6.3")
    tables = _find_tables(sub63)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            try:
                score = float(trow.get("Uccha Score (max 60)", "") or "0")
            except ValueError:
                score = None
            rows.append(_row(
                fact_id=row_id,
                category="strength_extra",
                value_text=f"{planet} Uccha Bala {score}",
                value_json={
                    "planet": planet,
                    "metric": "uccha_bala",
                    "score": score,
                    "band": trow.get("Band", "").strip(),
                },
                source_section="§6.3",
            ))

    # §6.5 Vimsopaka Bala → strength_extra
    sub65 = _extract_subsection(sec, "§6.5")
    tables = _find_tables(sub65)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            try:
                score = float(trow.get("Score", "") or "0")
            except ValueError:
                score = None
            rows.append(_row(
                fact_id=row_id,
                category="strength_extra",
                value_text=f"{planet} Vimsopaka {score}",
                value_json={
                    "planet": planet,
                    "metric": "vimsopaka_bala",
                    "score": score,
                    "band": trow.get("Band", "").strip(),
                },
                source_section="§6.5",
            ))

    # §6.6 Bhava Bala JH engine → bhava_bala
    sub66 = _extract_subsection(sec, "§6.6")
    tables = _find_tables(sub66)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            if not row_id:
                continue
            try:
                house = int(trow.get("House", "0") or "0")
            except ValueError:
                house = None
            try:
                jh_rupas = float(trow.get("JH Rupas", "0") or "0")
            except ValueError:
                jh_rupas = None
            rows.append(_row(
                fact_id=row_id,
                category="bhava_bala",
                value_text=f"House {house} JH Bhavabala {jh_rupas} rupas",
                value_json={
                    "house": house,
                    "life_area": trow.get("Life Area", "").strip(),
                    "jh_rupas": jh_rupas,
                    "jh_rank": trow.get("JH Rank", "").strip() or None,
                    "engine": "JH",
                },
                source_section="§6.6",
            ))

    # §6.7 Ishta / Kashta Phala → ishta_kashta
    sub67 = _extract_subsection(sec, "§6.7")
    tables = _find_tables(sub67)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            try:
                ishta = float(trow.get("Ishta Phala", "0") or "0")
            except ValueError:
                ishta = None
            try:
                kashta = float(trow.get("Kashta Phala", "0") or "0")
            except ValueError:
                kashta = None
            rows.append(_row(
                fact_id=row_id,
                category="ishta_kashta",
                value_text=f"{planet} Ishta {ishta} / Kashta {kashta}",
                value_json={
                    "planet": planet,
                    "ishta": ishta,
                    "kashta": kashta,
                    "net_assessment": trow.get("Net Assessment", "").strip(),
                },
                source_section="§6.7",
            ))

    # §6.8 Pancha-Vargeeya → strength_extra
    sub68 = _extract_subsection(sec, "§6.8")
    tables = _find_tables(sub68)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            try:
                score = float(trow.get("Score", "") or "0")
            except ValueError:
                score = None
            rows.append(_row(
                fact_id=row_id,
                category="strength_extra",
                value_text=f"{planet} Pancha-Vargeeya {score} — {trow.get('Classification','').strip()}",
                value_json={
                    "planet": planet,
                    "metric": "pancha_vargeeya",
                    "score": score,
                    "classification": trow.get("Classification", "").strip(),
                },
                source_section="§6.8",
            ))

    logger.info("parse_section_6: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §7 — ASHTAKAVARGA
# ──────────────────────────────────────────────────────────

_SIGNS = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def parse_section_7(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §7 Ashtakavarga into chart_facts rows."""
    sec = _extract_section(md, "§7")
    rows: list[dict[str, Any]] = []

    # §7.1 BAV — Per-Planet Bindus by Sign
    sub71 = _extract_subsection(sec, "§7.1")
    tables = _find_tables(sub71)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            by_sign: dict[str, int] = {}
            for short, name in zip(_SIGNS, _SIGN_NAMES):
                try:
                    by_sign[name] = int(trow.get(short, "0") or "0")
                except ValueError:
                    by_sign[name] = 0
            try:
                total = int(trow.get("Total", "0") or "0")
            except ValueError:
                total = None
            rows.append(_row(
                fact_id=row_id,
                category="ashtakavarga_bav",
                value_text=f"{planet} BAV total bindus: {total}",
                value_json={
                    "planet": planet,
                    "total_bindus": total,
                    "by_sign": by_sign,
                },
                source_section="§7.1",
            ))

    # §7.2 SAV — Sarvashtakavarga by Sign
    sub72 = _extract_subsection(sec, "§7.2")
    tables = _find_tables(sub72)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            sign = trow.get("Sign", "").strip()
            if not row_id:
                continue
            try:
                forensic_total = int(trow.get("SAV Total (FORENSIC)", "0") or "0")
            except ValueError:
                forensic_total = None
            try:
                jh_total = int(trow.get("JH Total", "0") or "0")
            except ValueError:
                jh_total = None
            rows.append(_row(
                fact_id=row_id,
                category="ashtakavarga_sav",
                value_text=f"{sign} SAV {forensic_total} (FORENSIC) / {jh_total} (JH)",
                value_json={
                    "sign": sign,
                    "house": trow.get("House", "").strip() or None,
                    "sav_forensic": forensic_total,
                    "sav_jh": jh_total,
                },
                source_section="§7.2",
            ))

    # §7.3 Shuddha Pinda
    sub73 = _extract_subsection(sec, "§7.3")
    tables = _find_tables(sub73)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            try:
                rasi = int(trow.get("Rasi Pinda", "0") or "0")
            except ValueError:
                rasi = None
            try:
                graha = int(trow.get("Graha Pinda", "0") or "0")
            except ValueError:
                graha = None
            try:
                shuddha = int(trow.get("Shuddha Pinda", "0") or "0")
            except ValueError:
                shuddha = None
            rows.append(_row(
                fact_id=row_id,
                category="ashtakavarga_pinda",
                value_text=f"{planet} Shuddha Pinda {shuddha}",
                value_json={
                    "planet": planet,
                    "rasi_pinda": rasi,
                    "graha_pinda": graha,
                    "shuddha_pinda": shuddha,
                    "rank": trow.get("Rank", "").strip() or None,
                },
                source_section="§7.3",
            ))

    logger.info("parse_section_7: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §8 — SATURN KAKSHYA ZONES
# ──────────────────────────────────────────────────────────

def parse_section_8(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §8 Saturn Kakshya Zones."""
    sec = _extract_section(md, "§8")
    rows: list[dict[str, Any]] = []
    tables = _find_tables(sec)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            if not row_id:
                continue
            try:
                zone_num = int(trow.get("Zone", "0") or "0")
            except ValueError:
                zone_num = None
            status = trow.get("Status", "").strip()
            rows.append(_row(
                fact_id=row_id,
                category="kakshya_zone",
                value_text=f"Zone {zone_num} {trow.get('Degree Range','').strip()} ruler={trow.get('Ruler','').strip()} {status}",
                value_json={
                    "zone": zone_num,
                    "degree_range": trow.get("Degree Range", "").strip(),
                    "ruling_planet": trow.get("Ruler", "").strip(),
                    "transit_active": status.upper() == "ACTIVE",
                    "sign": "Pisces",
                },
                source_section="§8",
            ))
    logger.info("parse_section_8: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §9 — AVASTHA DIAGNOSTICS
# ──────────────────────────────────────────────────────────

def parse_section_9(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §9 Avastha Diagnostics."""
    sec = _extract_section(md, "§9")
    rows: list[dict[str, Any]] = []
    sub91 = _extract_subsection(sec, "§9.1")
    tables = _find_tables(sub91)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            jagratadi = trow.get("Jagratadi", "").strip()
            baladi = trow.get("Baladi", "").strip()
            deeptadi = trow.get("Deeptadi", "").strip()
            rows.append(_row(
                fact_id=row_id,
                category="avastha",
                value_text=f"{planet} Avastha: {jagratadi}/{baladi}/{deeptadi}",
                value_json={
                    "planet": planet,
                    "role": trow.get("Role", "").strip(),
                    "jagratadi": jagratadi,
                    "baladi": baladi,
                    "deeptadi": deeptadi,
                    "explanation": f"{jagratadi} wakefulness; {baladi} age; {deeptadi} state",
                },
                source_section="§9.1",
            ))
    logger.info("parse_section_9: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §11 — SENSITIVE POINTS
# ──────────────────────────────────────────────────────────

def parse_section_11(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §11 Sensitive Points subsections."""
    sec = _extract_section(md, "§11")
    rows: list[dict[str, Any]] = []

    # §11.1 Upagrahas → upagraha
    sub111 = _extract_subsection(sec, "§11.1")
    tables = _find_tables(sub111)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            upagraha = trow.get("Upagraha", "").strip()
            if not row_id or not upagraha:
                continue
            sign = trow.get("Sign", "").strip()
            degree = trow.get("Degree", "").strip()
            rows.append(_row(
                fact_id=row_id,
                category="upagraha",
                value_text=f"{upagraha} in {sign} {degree}",
                value_json={
                    "upagraha": upagraha,
                    "type": trow.get("Type", "").strip(),
                    "sign": sign,
                    "degree": degree,
                    "nakshatra": trow.get("Nakshatra", "").strip(),
                },
                source_section="§11.1",
            ))

    # §11.2 Bhrigu Bindu → sensitive_point (one row per field)
    sub112 = _extract_subsection(sec, "§11.2")
    tables = _find_tables(sub112)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            field = trow.get("Field", "").strip()
            value = trow.get("Value", "").strip()
            if not row_id:
                continue
            rows.append(_row(
                fact_id=row_id,
                category="sensitive_point",
                value_text=f"Bhrigu Bindu {field}: {value}",
                value_json={
                    "point": "Bhrigu Bindu",
                    "field": field,
                    "value": value,
                },
                source_section="§11.2",
            ))

    # §11.3 Yogi / Avayogi → sensitive_point
    sub113 = _extract_subsection(sec, "§11.3")
    tables = _find_tables(sub113)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            field = trow.get("Field", "").strip()
            value = trow.get("Value", "").strip()
            if not row_id:
                continue
            rows.append(_row(
                fact_id=row_id,
                category="sensitive_point",
                value_text=f"Yogi/Avayogi {field}: {value}",
                value_json={
                    "point": "Yogi_Avayogi",
                    "field": field,
                    "value": value,
                },
                source_section="§11.3",
            ))

    # §11.4 Combustion and Planetary War → sensitive_point
    sub114 = _extract_subsection(sec, "§11.4")
    tables = _find_tables(sub114)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            check = trow.get("Check", "").strip()
            result = trow.get("Result", "").strip()
            if not row_id:
                continue
            rows.append(_row(
                fact_id=row_id,
                category="sensitive_point",
                value_text=f"{check}: {result}",
                value_json={
                    "point": "Combustion" if "CMB" in row_id else "Planetary War",
                    "check": check,
                    "result": result,
                    "is_combust": False,
                    "in_war": False,
                },
                source_section="§11.4",
            ))

    # §11.5 Mrityu Bhaga → mrityu_bhaga
    sub115 = _extract_subsection(sec, "§11.5")
    tables = _find_tables(sub115)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            sign = trow.get("Sign", "").strip()
            degree = trow.get("Degree", "").strip()
            mb_degree = trow.get("Mrityu Bhaga Degree", "").strip()
            status = trow.get("Status", "").strip()
            rows.append(_row(
                fact_id=row_id,
                category="mrityu_bhaga",
                value_text=f"{planet} {sign} {degree} — MB at {mb_degree} — {status}",
                value_json={
                    "planet": planet,
                    "sign": sign,
                    "degree": degree,
                    "mrityu_bhaga_degree": mb_degree,
                    "differential": trow.get("Differential", "").strip(),
                    "active": status.upper() != "SAFE",
                },
                source_section="§11.5",
            ))

    logger.info("parse_section_11: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §13 — ARUDHAS (only §13.2 Arudha Sign Occupancy)
# ──────────────────────────────────────────────────────────

def parse_section_13(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §13.2 Arudha Sign Occupancy."""
    sec = _extract_section(md, "§13")
    rows: list[dict[str, Any]] = []
    sub132 = _extract_subsection(sec, "§13.2")
    tables = _find_tables(sub132)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            sign = trow.get("Sign", "").strip()
            if not row_id or not sign:
                continue
            try:
                house = int(trow.get("House (from D1 Lagna)", "0") or "0")
            except ValueError:
                house = None
            markers = trow.get("Markers / Planets Present", "").strip()
            rows.append(_row(
                fact_id=row_id,
                category="arudha_occupancy",
                value_text=f"{sign} house {house}: {markers}",
                value_json={
                    "sign": sign,
                    "house": house,
                    "markers": [m.strip() for m in markers.split(",") if m.strip()],
                },
                source_section="§13.2",
            ))
    logger.info("parse_section_13: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §16 — ASPECTS (only §16.1 Parashari Graha Drishti)
# ──────────────────────────────────────────────────────────

def parse_section_16(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §16.1 Classical Vedic Aspects (Graha Drishti)."""
    sec = _extract_section(md, "§16")
    rows: list[dict[str, Any]] = []
    sub161 = _extract_subsection(sec, "§16.1")
    tables = _find_tables(sub161)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            from_sign = trow.get("From Sign", "").strip()
            aspect_rays_raw = trow.get("Aspect Rays", "").strip()
            # Parse individual aspect rays into list
            aspects: list[dict[str, Any]] = []
            for part in aspect_rays_raw.split(";"):
                part = part.strip()
                m = re.match(r"(\d+)(?:st|nd|rd|th)\s+on\s+(.+)", part)
                if m:
                    aspects.append({
                        "degree_aspect": int(m.group(1)),
                        "target_sign": m.group(2).strip(),
                    })
            rows.append(_row(
                fact_id=row_id,
                category="aspect",
                value_text=f"{planet} from {from_sign} aspects: {aspect_rays_raw}",
                value_json={
                    "from_planet": planet,
                    "from_sign": from_sign,
                    "type": "parashari",
                    "aspect_rays": aspects,
                    "raw": aspect_rays_raw,
                },
                source_section="§16.1",
            ))
    logger.info("parse_section_16: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §17 — CHALIT KINETIC SHIFTS
# ──────────────────────────────────────────────────────────

def parse_section_17(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §17 Chalit Kinetic Shifts."""
    sec = _extract_section(md, "§17")
    rows: list[dict[str, Any]] = []
    tables = _find_tables(sec)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            planet = trow.get("Planet", "").strip()
            if not row_id or not planet:
                continue
            rashi_raw = trow.get("Rashi House", "").strip()
            # Rashi House may have extra notes (e.g., "10 (2.14° from House 10 cusp...)")
            rashi_num_m = re.match(r"(\d+)", rashi_raw)
            try:
                rashi_house = int(rashi_num_m.group(1)) if rashi_num_m else None
            except (ValueError, AttributeError):
                rashi_house = None
            try:
                chalit_house = int(re.match(r"(\d+)", trow.get("Chalit House", "0")).group(1))
            except (ValueError, AttributeError):
                chalit_house = None
            shift_raw = trow.get("Shift", "0").strip()
            m = re.match(r"([+-]?\d+)", shift_raw)
            try:
                shift = int(m.group(1)) if m else 0
            except ValueError:
                shift = 0
            rows.append(_row(
                fact_id=row_id,
                category="chalit_shift",
                value_text=f"{planet} Rashi H{rashi_house} → Chalit H{chalit_house} (shift {shift:+d})",
                value_json={
                    "planet": planet,
                    "rashi_house": rashi_house,
                    "chalit_house": chalit_house,
                    "shift": shift,
                    "shift_description": shift_raw,
                },
                source_section="§17",
            ))
    logger.info("parse_section_17: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §18 — CHANDRA CHART
# ──────────────────────────────────────────────────────────

def parse_section_18(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §18 Chandra Chart (From-Moon View)."""
    sec = _extract_section(md, "§18")
    rows: list[dict[str, Any]] = []
    tables = _find_tables(sec)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            if not row_id:
                continue
            # "House from Moon" column — may have format "1 (Self)"
            house_raw = trow.get("House from Moon", "").strip()
            hm = re.match(r"(\d+)", house_raw)
            try:
                moon_house = int(hm.group(1)) if hm else None
            except ValueError:
                moon_house = None
            sign = trow.get("Sign", "").strip()
            planets_raw = trow.get("Planets", "").strip()
            planets = [p.strip() for p in planets_raw.split(",") if p.strip() and p.strip() != "(none)"]
            rows.append(_row(
                fact_id=row_id,
                category="chandra_placement",
                value_text=f"Chandra H{moon_house} ({sign}): {planets_raw if planets_raw else 'empty'}",
                value_json={
                    "moon_house": moon_house,
                    "moon_sign": sign,
                    "life_area": house_raw.split("(")[1].rstrip(")").strip() if "(" in house_raw else None,
                    "planets": planets,
                    "occupied": len(planets) > 0,
                },
                source_section="§18",
            ))
    logger.info("parse_section_18: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §20 — DEITY ASSIGNMENTS
# ──────────────────────────────────────────────────────────

def parse_section_20(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §20 Deity Assignments subsections."""
    sec = _extract_section(md, "§20")
    rows: list[dict[str, Any]] = []

    # §20.1 Deity Triad (Jaimini Derivation)
    sub201 = _extract_subsection(sec, "§20.1")
    tables = _find_tables(sub201)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            role = trow.get("Role", "").strip()
            if not row_id or not role:
                continue
            rows.append(_row(
                fact_id=row_id,
                category="deity_assignment",
                value_text=f"{role}: {trow.get('Deity','').strip()}",
                value_json={
                    "role": role,
                    "d9_sign": trow.get("D9 Sign", "").strip(),
                    "ruling_planet": trow.get("Ruling Planet", "").strip(),
                    "deity": trow.get("Deity", "").strip(),
                },
                source_section="§20.1",
                divisional_chart="D9",
            ))

    # §20.2 Digpala and Divisional Deity Mapping
    sub202 = _extract_subsection(sec, "§20.2")
    tables = _find_tables(sub202)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            scope = trow.get("Scope", "").strip()
            if not row_id or not scope:
                continue
            rows.append(_row(
                fact_id=row_id,
                category="deity_assignment",
                value_text=f"{scope}: {trow.get('Assignments','').strip()}",
                value_json={
                    "scope": scope,
                    "assignments": trow.get("Assignments", "").strip(),
                },
                source_section="§20.2",
            ))

    # §20.3 Planet → Deity Ledger
    sub203 = _extract_subsection(sec, "§20.3")
    tables = _find_tables(sub203)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            body = trow.get("Body", "").strip()
            if not row_id or not body:
                continue
            rows.append(_row(
                fact_id=row_id,
                category="deity_assignment",
                value_text=f"{body}: D10={trow.get('D10 Digpala','').strip()} D20={trow.get('D20 Deity','').strip()} D24={trow.get('D24 Deity','').strip()}",
                value_json={
                    "planet": body,
                    "d10_digpala": trow.get("D10 Digpala", "").strip(),
                    "d20_deity": trow.get("D20 Deity", "").strip(),
                    "d24_deity": trow.get("D24 Deity", "").strip(),
                    "d60_label": trow.get("D60 Label", "").strip(),
                },
                source_section="§20.3",
            ))

    logger.info("parse_section_20: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §22 — VARSHPHAL 2026–2027
# ──────────────────────────────────────────────────────────

def parse_section_22(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §22 Varshphal 2026–2027."""
    sec = _extract_section(md, "§22")
    rows: list[dict[str, Any]] = []
    tables = _find_tables(sec)
    if tables:
        kv: dict[str, str] = {}
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            component = trow.get("Component", "").strip()
            value = trow.get("Value", "").strip()
            if row_id:
                kv[row_id] = value
                rows.append(_row(
                    fact_id=row_id,
                    category="varshphal",
                    value_text=f"{component}: {value}",
                    value_json={
                        "component": component,
                        "value": value,
                        "year": "2026-2027",
                        "intentionally_excluded": "INTENTIONALLY EXCLUDED" in value.upper(),
                    },
                    source_section="§22",
                ))
    logger.info("parse_section_22: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# §24 — LONGEVITY INDICATORS
# ──────────────────────────────────────────────────────────

def parse_section_24(md: str) -> list[dict[str, Any]]:
    """Parse FORENSIC §24 Longevity Indicators."""
    sec = _extract_section(md, "§24")
    rows: list[dict[str, Any]] = []

    # §24.1 Kalachakra Paramayush
    sub241 = _extract_subsection(sec, "§24.1")
    tables = _find_tables(sub241)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            field = trow.get("Field", "").strip()
            value = trow.get("Value", "").strip()
            if not row_id:
                continue
            rows.append(_row(
                fact_id=row_id,
                category="longevity_indicator",
                value_text=f"Kalachakra {field}: {value}",
                value_json={
                    "system": "kalachakra",
                    "field": field,
                    "value": value,
                    "estimated_years": 85 if "85" in value else None,
                    "basis": "JH export JHORA_TRANSCRIPTION §10.7",
                },
                source_section="§24.1",
            ))

    # §24.2 Ayurdasaya status
    sub242 = _extract_subsection(sec, "§24.2")
    tables = _find_tables(sub242)
    if tables:
        for trow in _parse_md_table(tables[0]):
            row_id = _clean_id(trow.get("ID", ""))
            field = trow.get("Field", "").strip()
            status = trow.get("Status", "").strip()
            if not row_id:
                continue
            rows.append(_row(
                fact_id=row_id,
                category="longevity_indicator",
                value_text=f"{field}: {status[:80]}",
                value_json={
                    "system": "ayurdasaya",
                    "field": field,
                    "status": status,
                    "intentionally_excluded": "INTENTIONALLY EXCLUDED" in status.upper(),
                },
                source_section="§24.2",
            ))

    logger.info("parse_section_24: %d rows", len(rows))
    return rows


# ──────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────

def extract_all(forensic_md: str) -> list[dict[str, Any]]:
    """Run all section parsers and return deduplicated list of fact dicts."""
    parsers = [
        parse_section_6,
        parse_section_7,
        parse_section_8,
        parse_section_9,
        parse_section_11,
        parse_section_13,
        parse_section_16,
        parse_section_17,
        parse_section_18,
        parse_section_20,
        parse_section_22,
        parse_section_24,
    ]

    all_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for parser in parsers:
        try:
            section_rows = parser(forensic_md)
            for r in section_rows:
                fid = r["fact_id"]
                if fid in seen_ids:
                    logger.warning("Duplicate fact_id skipped: %s", fid)
                    continue
                if not fid:
                    logger.warning("Empty fact_id in row from %s; skipping", parser.__name__)
                    continue
                seen_ids.add(fid)
                all_rows.append(r)
        except Exception as exc:  # noqa: BLE001
            logger.error("Parser %s failed: %s", parser.__name__, exc, exc_info=True)

    logger.info("extract_all: %d total rows from %d parsers", len(all_rows), len(parsers))
    return all_rows


def load_and_extract(forensic_path: str | Path) -> list[dict[str, Any]]:
    """Read FORENSIC markdown from disk and run extract_all."""
    path = Path(forensic_path)
    if not path.exists():
        raise FileNotFoundError(f"FORENSIC file not found: {path}")
    md = path.read_text(encoding="utf-8")
    return extract_all(md)
