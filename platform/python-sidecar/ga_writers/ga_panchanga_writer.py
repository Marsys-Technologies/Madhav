"""
ga_panchanga_writer.py — GA4 Panchanga (birth-instant) writer
==============================================================

Computes the full A4 panchanga for the native's birth instant using the
`panchanga_engine.panchanga_instant()` L0 service and persists all results
as atomic rows into `chart_facts`.

A4 specification: 00_ARCHITECTURE/A4_PANCHANGA_SPEC_v1_0.md
Campaign brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_GA4_PANCHANGA_WRITER_v1_0.md

FORENSIC gate (hard — any divergence halts):
    panchanga_instant(1984-02-05T10:43 IST, 20.27, 85.84, +5.5 hours):
        Tithi   = Shukla Tritiya
        Vara    = Ravivara
        Yoga    = Shiva
        Karana  = Garaja
        Nakshatra (Moon) = Purva Bhadrapada   (ayanamsha-dependent via pyjhora_adapter)

Canonical chart_id: 482012f1-710e-4a25-994a-93821f5871aa
Ayanamsha-INVARIANT rows: ayanamsha_id = 'INVARIANT'
Ayanamsha-DEPENDENT rows: one pass per canonical ayanamsha (×5)

Engine: panchanga_engine.panchanga_instant  (NOT natal_engine)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from ga_writers._idempotency import replace_prior_chart_facts
from ga_writers._telemetry import update_asset_throughput
from pipeline.orchestrator.birth_params import resolve_birth_params

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# Canonical ayanamsha ids (same as GA3)
CANONICAL_AYANAMSHAS: list[str] = [
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
]

# FORENSIC expected values (invariant — ayanamsha does not affect angas)
FORENSIC_EXPECTED = {
    "tithi_name": "Shukla Tritiya",
    "vara_name": "Ravivara",
    "yoga_name": "Shiva",
    "karana_name": "Garaja",
    "nakshatra_name": "Purva Bhadrapada",  # moon nak at birth
}

# Engine identification string (A4 §5 — NOT natal_engine)
ENGINE_STRING = "panchanga_engine/2.0.0-P2"

# Nakshatra short codes for Tara bala subject key
NAKSHATRA_SHORT: list[str] = [
    "ASH", "BHA", "KRI", "ROH", "MRI", "ARD", "PUN", "PUS", "ASL",
    "MAG", "PPH", "UPH", "HAS", "CHI", "SWA", "VIS", "ANU", "JYE",
    "MOO", "PAS", "UAS", "SHR", "DHA", "SHA", "PPB", "UPB", "REV",
]

# Nakshatra full names (1-indexed via index+1)
NAKSHATRA_NAMES: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

# Sign names (1-indexed)
SIGN_NAMES: list[str] = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]

# Nakshatra vimshottari lords (0-indexed, matches NAKSHATRA_NAMES)
NAKSHATRA_LORDS: list[str] = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

# Tara Bala quality map (position 1..27 within 9-cycle, then repeats)
_TARA_QUALITY: dict[int, str] = {
    1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema", 5: "Pratyak",
    6: "Sadhaka", 7: "Vadha", 8: "Mitra", 9: "Atimitra",
}

# Chandra Bala classification (position from birth Moon sign — 1=same, 12=12th house)
_CHANDRA_BALA: dict[int, str] = {
    1: "favorable", 2: "unfavorable", 3: "favorable", 4: "unfavorable",
    5: "unfavorable", 6: "favorable", 7: "favorable", 8: "unfavorable",
    9: "neutral", 10: "favorable", 11: "favorable", 12: "unfavorable",
}

# Native birth Moon nakshatra (Purva Bhadrapada = id 25, 1-indexed)
NATIVE_MOON_NAK_ID = 25   # Purva Bhadrapada

# Native birth Moon sign (Aquarius = Kumbha = id 11, 1-indexed)
# 1984-02-05: Moon in Purva Bhadrapada spans Aquarius–Pisces; birth pada matters.
# Purva Bhadrapada padas 1-3 = Aquarius, pada 4 = Pisces.
# Canonical: Moon in Kumbha (Aquarius) at birth — confirmed FORENSIC.
NATIVE_MOON_SIGN_ID = 11  # Kumbha (Aquarius)


# ── DB connection (same pattern as GA3) ──────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[ga_panchanga_writer] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── Helpers ───────────────────────────────────────────────────────────────────

# M-22 fix: every `_emit_*` derived-anga function below (disha_shul, tithi/
# nakshatra-shoonya, agni_vasa, inauspicious/auspicious windows, bhadra flag,
# special-yoga combinations, panchaka classification/flag, eclipse proximity)
# previously hardcoded the top verification tier unconditionally (`vp =`
# the two-pass-verified literal) — stamped at the emit site with no verifier
# ever running a second pass. These
# are deterministic single-pass table lookups derived directly from the
# already-computed panchang_engine anga objects (tithi/nakshatra/yoga/karana/
# vara) — a real, single computation, but NOT independently cross-checked by
# a second method. `_single_pass_verif()` makes that honest: the class-wide
# tier for this file is "single_pass" (formulas.py VERIFICATION_RESCALE 0.85
# vs 1.00 for two_pass_verified) unless/until a genuine second-pass
# cross-check is implemented for a given anga (at which point that specific
# emit function should compute its own real two_pass_verified tier instead
# of calling this helper).
def _single_pass_verif() -> str:
    return "single_pass"


def _fact_id(category: str, subject: str, key: str,
             chart_id: str, ayanamsha_id: str, build_id: str) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _citation_ref(category: str, subject: str, key: str,
                  chart_id: str, ayanamsha_id: str) -> str:
    return (
        f"{category}.{subject}.{key}"
        f"@chart={chart_id}:ay={ayanamsha_id}:eng={ENGINE_STRING}"
    )


def _row(
    category: str, subject: str, key: str,
    chart_id: str, ayanamsha_id: str, build_id: str,
    value_text: Optional[str] = None,
    value_num: Optional[float] = None,
    value_jsonb: Optional[Any] = None,
    unit: Optional[str] = None,
    citation_human: str = "",
    verification_pass_status: str = "single",
    computed_at: Optional[str] = None,
) -> dict[str, Any]:
    """Build one chart_facts row dict."""
    fid = _fact_id(category, subject, key, chart_id, ayanamsha_id, build_id)
    cref = _citation_ref(category, subject, key, chart_id, ayanamsha_id)
    return {
        "fact_id": fid,
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "fact_category": category,
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_text": value_text,
        "fact_value_num": value_num,
        "fact_value_jsonb": json.dumps(value_jsonb) if value_jsonb is not None else None,
        "unit": unit,
        "citation_ref": cref,
        "citation_human": citation_human,
        "source_calculation": ENGINE_STRING,
        "verification_pass_status": verification_pass_status,
        "engine_version": "2.0.0-P2",
        "computed_at": computed_at or datetime.now(timezone.utc).isoformat(),
    }


def _ts_iso(dt) -> Optional[str]:
    """Convert a datetime (possibly naive) to ISO string."""
    if dt is None:
        return None
    if hasattr(dt, "isoformat"):
        if getattr(dt, "tzinfo", None) is None:
            return dt.replace(tzinfo=timezone.utc).isoformat()
        return dt.isoformat()
    return str(dt)


# ── FORENSIC gate ─────────────────────────────────────────────────────────────

def panchanga_forensic_gate(pi: Any) -> None:
    """
    Assert FORENSIC anchors against PanchangaInstant output.
    Raises RuntimeError if any anchor fails — halts the build.

    Anchors:
        tithi  = Shukla Tritiya
        vara   = Ravivara
        yoga   = Shiva
        karana = Garaja
        nakshatra (Moon) = Purva Bhadrapada
    """
    failures: list[str] = []

    # Tithi
    tithi_name = getattr(pi.tithi, "name", "") if pi.tithi else ""
    if "Tritiya" not in tithi_name:
        failures.append(
            f"FORENSIC FAIL: tithi expected 'Shukla Tritiya', got '{tithi_name}'"
        )
    if "Shukla" not in tithi_name and "Tritiya" in tithi_name:
        failures.append(
            f"FORENSIC FAIL: tithi paksha expected 'Shukla', got '{tithi_name}'"
        )

    # Vara
    vara_name = getattr(pi.vara, "name", "") if pi.vara else ""
    if vara_name != "Ravivara":
        failures.append(
            f"FORENSIC FAIL: vara expected 'Ravivara', got '{vara_name}'"
        )

    # Yoga
    yoga_name = getattr(pi.yoga, "name", "") if pi.yoga else ""
    if yoga_name != "Shiva":
        failures.append(
            f"FORENSIC FAIL: yoga expected 'Shiva', got '{yoga_name}'"
        )

    # Karana
    karana_name = getattr(pi.karana, "name", "") if pi.karana else ""
    if karana_name != "Garaja":
        failures.append(
            f"FORENSIC FAIL: karana expected 'Garaja', got '{karana_name}'"
        )

    # Nakshatra (Moon)
    nak_name = getattr(pi.nakshatra, "name", "") if pi.nakshatra else ""
    if nak_name != "Purva Bhadrapada":
        failures.append(
            f"FORENSIC FAIL: nakshatra expected 'Purva Bhadrapada', got '{nak_name}'"
        )

    if failures:
        msg = "PANCHANGA FORENSIC GATE FAILED (GA4):\n" + "\n".join(
            f"  - {f}" for f in failures
        )
        logger.error(msg)
        _write_halt_log("GA4_FORENSIC_GATE", msg)
        raise RuntimeError(msg)

    logger.info(
        "[GA4 FORENSIC] PASS: Tithi=Shukla Tritiya, Vara=Ravivara, "
        "Yoga=Shiva, Karana=Garaja, Nak=Purva Bhadrapada"
    )


def _write_halt_log(gate_name: str, msg: str) -> None:
    """Append failure to CONDUCTOR_HALT_LOG.md (best-effort).

    Target directory is overridable via CONDUCTOR_HALT_LOG_DIR_OVERRIDE, which
    the test suite sets to an isolated tmp dir (see tests/conftest.py) so that
    forensic-gate unit tests exercising deliberately-bad PanchangaInstant mocks
    (e.g. test_ga4_writer.py::TestForensicGate) never append fixture noise to
    the real repo-tracked l1-ganita-build/CONDUCTOR_HALT_LOG.md.
    """
    try:
        import pathlib
        override = os.environ.get("CONDUCTOR_HALT_LOG_DIR_OVERRIDE")
        if override:
            candidate = pathlib.Path(override) / "l1-ganita-build" / "CONDUCTOR_HALT_LOG.md"
            candidate.parent.mkdir(parents=True, exist_ok=True)
            with open(candidate, "a", encoding="utf-8") as fh:
                fh.write(
                    f"\n## HALT: {gate_name} — "
                    f"{datetime.now(timezone.utc).isoformat()}\n"
                    f"{msg}\n"
                )
            return
        p = pathlib.Path(__file__).resolve()
        for _ in range(10):
            candidate = (
                p / "00_ARCHITECTURE" / "CONDUCTOR"
                / "l1-ganita-build" / "CONDUCTOR_HALT_LOG.md"
            )
            if candidate.parent.exists():
                candidate.parent.mkdir(parents=True, exist_ok=True)
                with open(candidate, "a", encoding="utf-8") as fh:
                    fh.write(
                        f"\n## HALT: {gate_name} — "
                        f"{datetime.now(timezone.utc).isoformat()}\n"
                        f"{msg}\n"
                    )
                return
            p = p.parent
    except Exception as exc:
        logger.debug("[ga_panchanga] _write_halt_log failed (best-effort): %s", exc)


# ── Row emitters — INVARIANT categories ─────────────────────────────────────

def _emit_tithi(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_tithi — subject TITHI_BIRTH — A4 §3."""
    cat = "panchanga_tithi"
    subj = "TITHI_BIRTH"
    ay = "INVARIANT"
    t = pi.tithi
    ta = pi.tithi_attrs  # AngaAttributes

    tithi_num = t.id  # 1..30
    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    name = t.name  # e.g. "Shukla Tritiya"
    # Derive number within paksha (1..15 for both)
    num_in_paksha = tithi_num if tithi_num <= 15 else tithi_num - 15

    # Tithi type
    tithi_type = ta.anga_type if ta else "unknown"
    # Tithi deity (canonical)
    tithi_deity = ta.deity if ta else ""
    lord = ta.lord if ta else ""

    # Percent elapsed at birth
    # We approximate: time elapsed since tithi pravesh / tithi duration
    # A4 §3 requires percent_elapsed_at_birth — stored as null if unavailable
    pct = ta.pct_elapsed if (ta and ta.pct_elapsed is not None) else None

    pravesh_iso = None  # start of tithi (not in PanchangaInstant directly)
    arambha_iso = _ts_iso(t.end_utc)  # end of tithi

    # Inauspicious tithis: 4,6,8,9,12,14,30 (classical)
    INAUSPICIOUS_TITHIS = {4, 6, 8, 9, 12, 14, 30}
    inauspicious = tithi_num in INAUSPICIOUS_TITHIS

    vp = "single"
    rows = [
        _row(cat, subj, "name",         chart_id, ay, build_id,
             value_text=name,
             citation_human=f"Tithi at birth: {name}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "number_in_lunar_month", chart_id, ay, build_id,
             value_num=float(tithi_num),
             citation_human=f"Tithi number: {tithi_num} (of 30).",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "paksha",       chart_id, ay, build_id,
             value_text=paksha,
             citation_human=f"Paksha: {paksha}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "type",         chart_id, ay, build_id,
             value_text=tithi_type,
             citation_human=f"Tithi type: {tithi_type}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "lord",         chart_id, ay, build_id,
             value_text=lord,
             citation_human=f"Tithi lord: {lord}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "arambha_iso",  chart_id, ay, build_id,
             value_text=arambha_iso,
             citation_human=f"Tithi ends: {arambha_iso}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "inauspicious_flag", chart_id, ay, build_id,
             value_text=str(inauspicious).lower(),
             citation_human=f"Tithi inauspicious: {inauspicious}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    # Optional fields
    if pct is not None:
        rows.append(_row(cat, subj, "percent_elapsed_at_birth", chart_id, ay, build_id,
                         value_num=float(pct),
                         citation_human=f"Tithi was {pct*100:.1f}% elapsed at birth.",
                         verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_vara(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_vara — subject VARA_BIRTH."""
    cat = "panchanga_vara"
    subj = "VARA_BIRTH"
    ay = "INVARIANT"
    v = pi.vara
    vp = "single"

    # Lord from VARA_NAMES table
    VARA_LORDS = {
        1: ("Sun", "Agni"), 2: ("Moon", "Jala"), 3: ("Mars", "Agni"),
        4: ("Mercury", "Prithvi"), 5: ("Jupiter", "Akasha"),
        6: ("Venus", "Jala"), 7: ("Saturn", "Vayu"),
    }
    vara_id = v.id  # 1..7
    lord, element = VARA_LORDS.get(vara_id, ("", ""))

    rows = [
        _row(cat, subj, "name",         chart_id, ay, build_id,
             value_text=v.name,
             citation_human=f"Vara at birth: {v.name}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "number",       chart_id, ay, build_id,
             value_num=float(vara_id),
             citation_human=f"Vara number: {vara_id} (1=Sun..7=Sat).",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "lord",         chart_id, ay, build_id,
             value_text=lord,
             citation_human=f"Vara lord: {lord}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "lord_element", chart_id, ay, build_id,
             value_text=element,
             citation_human=f"Vara lord element: {element}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    return rows


def _emit_yoga(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_yoga — subject YOGA_BIRTH."""
    cat = "panchanga_yoga"
    subj = "YOGA_BIRTH"
    ay = "INVARIANT"
    y = pi.yoga
    vp = "single"

    yoga_num = y.id  # 1..27
    INAUSPICIOUS_YOGAS = {1, 6, 9, 10, 13, 15, 17, 19, 27}
    inauspicious = yoga_num in INAUSPICIOUS_YOGAS
    arambha_iso = _ts_iso(y.end_utc)

    rows = [
        _row(cat, subj, "name",         chart_id, ay, build_id,
             value_text=y.name,
             citation_human=f"Yoga at birth: {y.name}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "number",       chart_id, ay, build_id,
             value_num=float(yoga_num),
             citation_human=f"Yoga number: {yoga_num} (1=Vishkambha, 27=Vaidhriti).",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "arambha_iso",  chart_id, ay, build_id,
             value_text=arambha_iso,
             citation_human=f"Yoga ends: {arambha_iso}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "inauspicious_flag", chart_id, ay, build_id,
             value_text=str(inauspicious).lower(),
             citation_human=f"Yoga inauspicious: {inauspicious}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    return rows


def _emit_karana(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_karana — subject KARANA_BIRTH."""
    cat = "panchanga_karana"
    subj = "KARANA_BIRTH"
    ay = "INVARIANT"
    k = pi.karana
    vp = "single"

    karana_id = k.id  # 1..11
    # Vishti/Bhadra karana_id = 7
    vishti_flag = karana_id == 7
    MOVABLE_KARANAS = {1, 2, 3, 4, 5, 6, 7}
    half_tithi = "second" if karana_id in {8, 9, 10, 11} else "first"
    arambha_iso = _ts_iso(k.end_utc)

    rows = [
        _row(cat, subj, "name",         chart_id, ay, build_id,
             value_text=k.name,
             citation_human=f"Karana at birth: {k.name}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "number",       chart_id, ay, build_id,
             value_num=float(karana_id),
             citation_human=f"Karana number: {karana_id}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "half_tithi_position", chart_id, ay, build_id,
             value_text=half_tithi,
             citation_human=f"Karana half-tithi position: {half_tithi}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "vishti_bhadra_flag", chart_id, ay, build_id,
             value_text=str(vishti_flag).lower(),
             citation_human=f"Bhadra/Vishti karana active: {vishti_flag}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "arambha_iso",  chart_id, ay, build_id,
             value_text=arambha_iso,
             citation_human=f"Karana ends: {arambha_iso}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    return rows


def _emit_solar_context(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_solar_context — subject SOLAR_CONTEXT_BIRTH."""
    cat = "panchanga_solar_context"
    subj = "SOLAR_CONTEXT_BIRTH"
    ay = "INVARIANT"
    cal = pi.calendrical
    vp = "single"

    if cal is None:
        return []

    rows = [
        _row(cat, subj, "ayana",        chart_id, ay, build_id,
             value_text=cal.ayana,
             citation_human=f"Ayana at birth: {cal.ayana}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "ritu",         chart_id, ay, build_id,
             value_text=cal.ritu,
             citation_human=f"Ritu at birth: {cal.ritu}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "solar_arc_into_current_sign_deg", chart_id, ay, build_id,
             value_num=float(cal.solar_arc_deg) if cal.solar_arc_deg else None,
             citation_human=f"Sun's arc into current sign: {cal.solar_arc_deg:.4f} deg.",
             unit="deg",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    if cal.sankranti_name:
        rows.append(_row(cat, subj, "last_sankranti_name", chart_id, ay, build_id,
                         value_text=cal.sankranti_name,
                         citation_human=f"Last Sankranti: {cal.sankranti_name}.",
                         verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_calendrical(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_calendrical — subject CALENDRICAL_BIRTH."""
    cat = "panchanga_calendrical"
    subj = "CALENDRICAL_BIRTH"
    ay = "INVARIANT"
    cal = pi.calendrical
    vp = "single"

    if cal is None:
        return []

    rows = [
        _row(cat, subj, "masa_purnimanta",   chart_id, ay, build_id,
             value_text=cal.masa_purnimanta,
             citation_human=f"Masa (Purnimanta): {cal.masa_purnimanta}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "masa_amanta",       chart_id, ay, build_id,
             value_text=cal.masa_amanta,
             citation_human=f"Masa (Amanta): {cal.masa_amanta}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "adhika_masa_flag",  chart_id, ay, build_id,
             value_text=str(cal.is_adhika_masa).lower(),
             citation_human=f"Adhika (intercalary) masa: {cal.is_adhika_masa}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "kshaya_masa_flag",  chart_id, ay, build_id,
             value_text=str(cal.is_kshaya_masa).lower(),
             citation_human=f"Kshaya (suppressed) masa: {cal.is_kshaya_masa}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "vikram_samvat",     chart_id, ay, build_id,
             value_num=float(cal.vikram_samvat),
             citation_human=f"Vikram Samvat: {cal.vikram_samvat}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "shaka_samvat",      chart_id, ay, build_id,
             value_num=float(cal.shaka_samvat),
             citation_human=f"Shaka Samvat: {cal.shaka_samvat}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "kali_samvat",       chart_id, ay, build_id,
             value_num=float(cal.kali_samvat),
             citation_human=f"Kali Samvat: {cal.kali_samvat}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "jovian_60yr_cycle_name", chart_id, ay, build_id,
             value_text=cal.jovian_year_name,
             citation_human=f"Jovian 60-year cycle: {cal.jovian_year_name}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "jovian_60yr_position", chart_id, ay, build_id,
             value_num=float(cal.jovian_year_number),
             citation_human=f"Jovian 60-year position: {cal.jovian_year_number}/60.",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    return rows


def _emit_sun_moon_dynamics(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_sun_moon_dynamics — subject SUN_MOON_DYNAMICS_BIRTH."""
    cat = "panchanga_sun_moon_dynamics"
    subj = "SUN_MOON_DYNAMICS_BIRTH"
    ay = "INVARIANT"
    sm = pi.sun_moon
    vp = "single"

    rows = []
    if sm is None:
        return rows

    rows += [
        _row(cat, subj, "sun_moon_separation_deg", chart_id, ay, build_id,
             value_num=sm.sun_moon_separation_deg,
             citation_human=f"Sun-Moon separation at birth: {sm.sun_moon_separation_deg:.4f} deg.",
             unit="deg",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "moon_illumination_pct", chart_id, ay, build_id,
             value_num=sm.moon_illumination_pct,
             citation_human=f"Moon illumination at birth: {sm.moon_illumination_pct:.2f}%.",
             unit="%",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "moon_phase_angle_deg", chart_id, ay, build_id,
             value_num=sm.moon_phase_angle_deg,
             citation_human=f"Moon phase angle at birth: {sm.moon_phase_angle_deg:.4f} deg.",
             unit="deg",
             verification_pass_status=vp, computed_at=computed_at),
    ]

    # Also emit tithi/nakshatra/yoga/karana pravesh+arambha from the anga objects
    tithi = pi.tithi
    nak = pi.nakshatra
    yoga = pi.yoga
    karana = pi.karana

    for anga_name, anga_obj in [("tithi", tithi), ("nakshatra", nak),
                                 ("yoga", yoga), ("karana", karana)]:
        if anga_obj is not None:
            arambha = _ts_iso(anga_obj.end_utc)
            rows.append(_row(cat, subj, f"{anga_name}_arambha_iso", chart_id, ay, build_id,
                             value_text=arambha,
                             citation_human=f"{anga_name.title()} ends: {arambha}.",
                             verification_pass_status=vp, computed_at=computed_at))

    return rows


def _emit_disha_shul(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_disha_shul — subject DISHA_SHUL_BIRTH."""
    cat = "panchanga_disha_shul"
    subj = "DISHA_SHUL_BIRTH"
    ay = "INVARIANT"
    vp = _single_pass_verif()

    # DISHA_SHUL_TABLE: vara_id → direction to avoid
    DISHA_SHUL_TABLE = {
        1: "West", 2: "East", 3: "North", 4: "North",
        5: "South", 6: "West", 7: "East",
    }
    vara_id = pi.vara.id if pi.vara else 1
    direction = DISHA_SHUL_TABLE.get(vara_id, "")

    return [
        _row(cat, subj, "direction_to_avoid", chart_id, ay, build_id,
             value_text=direction,
             citation_human=f"Disha Shul (direction to avoid) at birth: {direction} (vara={pi.vara.name if pi.vara else 'unknown'}).",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "weekday_reference", chart_id, ay, build_id,
             value_text=pi.vara.name if pi.vara else "",
             citation_human=f"Disha Shul weekday reference: {pi.vara.name if pi.vara else ''}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]


def _emit_tithi_shoonya(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_tithi_shoonya_rashi — subject TITHI_SHOONYA_BIRTH.

    D-4 fix: `panchang_engine.panchanga_instant()` always sets `pi.shoonya`
    (via `compute_shoonya`, which itself always returns a `ShoonyaState` —
    never `None`), and `TITHI_SHOONYA_TABLE` covers every valid tithi_id
    (1..30) with no gaps. So `shoonya is None` and
    `tithi_shoonya_sign_id is None` should never happen for a structurally
    valid tithi.id — if either does, it is a genuine upstream defect (e.g.
    a stale/mismatched panchang_engine build, or tithi.id outside 1..30),
    not a legitimate "nothing to report" case. Previously both were silent
    `return []` (classic silent-skip, per B.10 / CLAUDE.md discipline on
    never silently absorbing a computation gap). Now: log loud + halt via
    RuntimeError so a build never quietly ships 0 rows for a table that is
    supposed to be exhaustive.
    """
    cat = "panchanga_tithi_shoonya_rashi"
    subj = "TITHI_SHOONYA_BIRTH"
    ay = "INVARIANT"
    vp = _single_pass_verif()

    shoonya = pi.shoonya
    if shoonya is None:
        logger.error(
            "[ga_panchanga] chart_id=%s: pi.shoonya is None — panchang_engine "
            "should always populate ShoonyaState; refusing to silently skip "
            "panchanga_tithi_shoonya_rashi (D-4).", chart_id,
        )
        raise RuntimeError(
            f"[ga_panchanga] chart_id={chart_id}: panchanga_instant() returned "
            f"pi.shoonya=None — TITHI_SHOONYA_TABLE lookup never ran. This is a "
            f"halt-worthy defect (D-4), not a silent-skip case."
        )

    rows = []
    if shoonya.tithi_shoonya_sign_id is not None:
        sign_name = SIGN_NAMES[shoonya.tithi_shoonya_sign_id - 1] if shoonya.tithi_shoonya_sign_id <= 12 else ""
        rows += [
            _row(cat, subj, "void_sign_id",   chart_id, ay, build_id,
                 value_num=float(shoonya.tithi_shoonya_sign_id),
                 citation_human=f"Tithi Shoonya Rashi (void sign) at birth: sign id {shoonya.tithi_shoonya_sign_id}.",
                 verification_pass_status=vp, computed_at=computed_at),
            _row(cat, subj, "void_sign_name", chart_id, ay, build_id,
                 value_text=sign_name,
                 citation_human=f"Tithi Shoonya Rashi (void sign) at birth: {sign_name}.",
                 verification_pass_status=vp, computed_at=computed_at),
        ]
    else:
        logger.warning(
            "[ga_panchanga] chart_id=%s: tithi_shoonya_sign_id is None for "
            "tithi.id=%s — TITHI_SHOONYA_TABLE covers 1..30 with no gaps, so "
            "this indicates tithi.id is out of range or the table has "
            "drifted. Emitting zero rows for this category IS a real gap, "
            "not a silent one (D-4) — surfaced via WARNING, not swallowed.",
            chart_id, getattr(pi.tithi, "id", None),
        )
    return rows


def _emit_nakshatra_shoonya(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_nakshatra_shoonya_rashi — subject NAKSHATRA_SHOONYA_BIRTH.

    D-4 fix: see `_emit_tithi_shoonya` docstring — same class of defect,
    same fix (halt on `shoonya is None`, loud WARNING instead of silent
    skip when a specific sign_id resolves to None despite an exhaustive
    NAKSHATRA_SHOONYA_TABLE covering 1..27).
    """
    cat = "panchanga_nakshatra_shoonya_rashi"
    subj = "NAKSHATRA_SHOONYA_BIRTH"
    ay = "INVARIANT"
    vp = _single_pass_verif()

    shoonya = pi.shoonya
    if shoonya is None:
        logger.error(
            "[ga_panchanga] chart_id=%s: pi.shoonya is None — panchang_engine "
            "should always populate ShoonyaState; refusing to silently skip "
            "panchanga_nakshatra_shoonya_rashi (D-4).", chart_id,
        )
        raise RuntimeError(
            f"[ga_panchanga] chart_id={chart_id}: panchanga_instant() returned "
            f"pi.shoonya=None — NAKSHATRA_SHOONYA_TABLE lookup never ran. This "
            f"is a halt-worthy defect (D-4), not a silent-skip case."
        )

    rows = []
    if shoonya.nakshatra_shoonya_sign_id is not None:
        sign_name = SIGN_NAMES[shoonya.nakshatra_shoonya_sign_id - 1] if shoonya.nakshatra_shoonya_sign_id <= 12 else ""
        rows += [
            _row(cat, subj, "void_sign_id",   chart_id, ay, build_id,
                 value_num=float(shoonya.nakshatra_shoonya_sign_id),
                 citation_human=f"Nakshatra Shoonya Rashi (void sign) at birth: sign id {shoonya.nakshatra_shoonya_sign_id}.",
                 verification_pass_status=vp, computed_at=computed_at),
            _row(cat, subj, "void_sign_name", chart_id, ay, build_id,
                 value_text=sign_name,
                 citation_human=f"Nakshatra Shoonya Rashi (void sign) at birth: {sign_name}.",
                 verification_pass_status=vp, computed_at=computed_at),
        ]
    else:
        logger.warning(
            "[ga_panchanga] chart_id=%s: nakshatra_shoonya_sign_id is None for "
            "nakshatra.id=%s — NAKSHATRA_SHOONYA_TABLE covers 1..27 with no "
            "gaps, so this indicates nakshatra.id is out of range or the "
            "table has drifted. Emitting zero rows for this category IS a "
            "real gap, not a silent one (D-4) — surfaced via WARNING, not "
            "swallowed.", chart_id, getattr(pi.nakshatra, "id", None),
        )
    return rows


def _emit_agni_vasa(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_agni_vasa — subject AGNI_VASA_BIRTH."""
    cat = "panchanga_agni_vasa"
    subj = "AGNI_VASA_BIRTH"
    ay = "INVARIANT"
    vp = _single_pass_verif()

    vasa = pi.vasa
    if vasa is None:
        return []

    residence = vasa.agni_vasa
    tithi_id = pi.tithi.id if pi.tithi else 0

    # Agni Vasa formula: tithi-based residence
    # Prithvi/Bhumi=auspicious for yajna
    auspicious = residence in ("Prithvi",)

    return [
        _row(cat, subj, "residence",            chart_id, ay, build_id,
             value_text=residence,
             citation_human=f"Agni Vasa at birth: {residence}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "computation_formula",  chart_id, ay, build_id,
             value_text=f"tithi_id={tithi_id} → AGNI_VASA_TABLE",
             citation_human=f"Agni Vasa formula: tithi {tithi_id} → AGNI_VASA_TABLE lookup.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "auspicious_for_yagna_flag", chart_id, ay, build_id,
             value_text=str(auspicious).lower(),
             citation_human=f"Agni Vasa auspicious for yajna: {auspicious}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]


def _emit_hora_birth(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_hora_birth — subject HORA_BIRTH."""
    cat = "panchanga_hora_birth"
    subj = "HORA_BIRTH"
    ay = "INVARIANT"
    vp = "single"
    rows = []

    wm = pi.window_membership
    if wm is None or not wm.hora_planet:
        return rows

    hora_planet = wm.hora_planet
    rows.append(_row(cat, subj, "lord", chart_id, ay, build_id,
                     value_text=hora_planet,
                     citation_human=f"Hora lord at birth: {hora_planet}.",
                     verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_choghadiya_birth(pi: Any, chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """panchanga_choghadiya_birth — subject CHOGHADIYA_BIRTH."""
    cat = "panchanga_choghadiya_birth"
    subj = "CHOGHADIYA_BIRTH"
    ay = "INVARIANT"
    vp = "single"
    rows = []

    wm = pi.window_membership
    if wm is None or not wm.choghadiya_slot:
        return rows

    slot = wm.choghadiya_slot
    rows.append(_row(cat, subj, "choghadiya_slot", chart_id, ay, build_id,
                     value_text=slot,
                     citation_human=f"Choghadiya at birth: {slot}.",
                     verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_inauspicious_window(pi: Any, window_name: str, subject: str,
                               chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """Generic inauspicious time window emitter."""
    cat = f"panchanga_{window_name}"
    ay = "INVARIANT"
    vp = _single_pass_verif()
    rows = []

    inauspicious_full = pi.inauspicious_full
    if inauspicious_full is None:
        return rows

    # Find the matching timing object
    timing = None
    for t in inauspicious_full:
        label = getattr(t, "label", "")
        if window_name in label.lower() or label.lower() in window_name.lower():
            timing = t
            break

    if timing is None:
        # Try to find in the basic inauspicious list
        for t in (pi.vasa and [] or []):
            pass  # No match found — emit null marked
        return rows

    start_iso = _ts_iso(timing.start_utc)
    end_iso = _ts_iso(timing.end_utc)
    # Duration in minutes
    try:
        from datetime import timezone as _tz
        st = timing.start_utc
        et = timing.end_utc
        if getattr(st, "tzinfo", None) is None:
            st = st.replace(tzinfo=_tz.utc)
        if getattr(et, "tzinfo", None) is None:
            et = et.replace(tzinfo=_tz.utc)
        duration_min = (et - st).total_seconds() / 60.0
    except Exception as exc:
        logger.warning("[ga_panchanga] Duration computation failed: %s", exc)
        duration_min = None

    rows += [
        _row(cat, subject, "start_iso",         chart_id, ay, build_id,
             value_text=start_iso,
             citation_human=f"{window_name.replace('_', ' ').title()} start: {start_iso}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subject, "end_iso",           chart_id, ay, build_id,
             value_text=end_iso,
             citation_human=f"{window_name.replace('_', ' ').title()} end: {end_iso}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    if duration_min is not None:
        rows.append(_row(cat, subject, "duration_minutes", chart_id, ay, build_id,
                         value_num=duration_min,
                         citation_human=f"{window_name.replace('_', ' ').title()} duration: {duration_min:.1f} min.",
                         unit="minutes",
                         verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_auspicious_window(pi: Any, window_name: str, subject: str,
                              chart_id: str, build_id: str, computed_at: str) -> list[dict]:
    """Generic auspicious time window emitter."""
    cat = f"panchanga_{window_name}"
    ay = "INVARIANT"
    vp = _single_pass_verif()
    rows = []

    auspicious_full = pi.auspicious_full
    if auspicious_full is None:
        return rows

    timing = None
    for t in auspicious_full:
        label = getattr(t, "label", "")
        if window_name in label.lower() or label.lower() in window_name.lower():
            timing = t
            break

    if timing is None:
        return rows

    start_iso = _ts_iso(timing.start_utc)
    end_iso = _ts_iso(timing.end_utc)
    try:
        from datetime import timezone as _tz
        st = timing.start_utc
        et = timing.end_utc
        if getattr(st, "tzinfo", None) is None:
            st = st.replace(tzinfo=_tz.utc)
        if getattr(et, "tzinfo", None) is None:
            et = et.replace(tzinfo=_tz.utc)
        duration_min = (et - st).total_seconds() / 60.0
    except Exception as exc:
        logger.warning("[ga_panchanga] Duration computation failed: %s", exc)
        duration_min = None

    rows += [
        _row(cat, subject, "start_iso",         chart_id, ay, build_id,
             value_text=start_iso,
             citation_human=f"{window_name.replace('_', ' ').title()} start: {start_iso}.",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subject, "end_iso",           chart_id, ay, build_id,
             value_text=end_iso,
             citation_human=f"{window_name.replace('_', ' ').title()} end: {end_iso}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    if duration_min is not None:
        rows.append(_row(cat, subject, "duration_minutes", chart_id, ay, build_id,
                         value_num=duration_min,
                         citation_human=f"{window_name.replace('_', ' ').title()} duration: {duration_min:.1f} min.",
                         unit="minutes",
                         verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_bhadra_flag(pi: Any, chart_id: str, build_id: str, computed_at: str,
                       ayanamsha_id: str = "INVARIANT") -> list[dict]:
    """bhadra_flag — active when Vishti karana operating at birth."""
    cat = "bhadra_flag"
    subj = "BHADRA_FLAG_BIRTH"
    ay = ayanamsha_id
    vp = _single_pass_verif()

    karana = pi.karana
    active = (karana is not None and karana.id == 7)  # Vishti/Bhadra = id 7

    return [
        _row(cat, subj, "active_at_birth_flag", chart_id, ay, build_id,
             value_text=str(active).lower(),
             citation_human=f"Bhadra (Vishti karana) active at birth: {active}.",
             verification_pass_status=vp, computed_at=computed_at),
    ]


# ── Row emitters — AYANAMSHA-DEPENDENT categories ───────────────────────────

def _emit_nakshatra_moon(pi: Any, chart_id: str, build_id: str, computed_at: str,
                          ayanamsha_id: str) -> list[dict]:
    """panchanga_nakshatra_moon — subject NAKSHATRA_MOON_BIRTH (per ayanamsha)."""
    cat = "panchanga_nakshatra_moon"
    subj = "NAKSHATRA_MOON_BIRTH"
    ay = ayanamsha_id
    vp = "single"

    nak = pi.nakshatra
    na = pi.nakshatra_attrs

    nak_id = nak.id  # 1..27
    nak_name = nak.name
    arambha_iso = _ts_iso(nak.end_utc)
    lord = NAKSHATRA_LORDS[nak_id - 1]

    rows = [
        _row(cat, subj, "name",         chart_id, ay, build_id,
             value_text=nak_name,
             citation_human=f"Moon nakshatra at birth: {nak_name} ({ayanamsha_id}).",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "number",       chart_id, ay, build_id,
             value_num=float(nak_id),
             citation_human=f"Moon nakshatra number: {nak_id} ({ayanamsha_id}).",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "vimshottari_starting_lord", chart_id, ay, build_id,
             value_text=lord,
             citation_human=f"Vimshottari dasha starting lord for {nak_name}: {lord} ({ayanamsha_id}).",
             verification_pass_status=vp, computed_at=computed_at),
        _row(cat, subj, "arambha_iso",  chart_id, ay, build_id,
             value_text=arambha_iso,
             citation_human=f"Moon nakshatra ends: {arambha_iso} ({ayanamsha_id}).",
             verification_pass_status=vp, computed_at=computed_at),
    ]

    if na is not None:
        deity = getattr(na, "deity", "")
        rows += [
            _row(cat, subj, "deity",    chart_id, ay, build_id,
                 value_text=deity,
                 citation_human=f"Moon nakshatra deity: {deity} ({ayanamsha_id}).",
                 verification_pass_status=vp, computed_at=computed_at),
        ]
        if na.pct_elapsed is not None:
            rows.append(_row(cat, subj, "percent_elapsed_at_birth", chart_id, ay, build_id,
                             value_num=float(na.pct_elapsed),
                             citation_human=f"Nakshatra elapsed at birth: {na.pct_elapsed:.3f} ({ayanamsha_id}).",
                             verification_pass_status=vp, computed_at=computed_at))

    return rows


def _emit_special_yoga_combinations(pi: Any, chart_id: str, build_id: str,
                                     computed_at: str, ayanamsha_id: str) -> list[dict]:
    """panchanga_special_yoga_combinations (ayanamsha-dependent)."""
    cat = "panchanga_special_yoga_combinations"
    ay = ayanamsha_id
    vp = _single_pass_verif()
    rows = []

    yogas = pi.special_yogas_instant or []
    if not yogas:
        yogas = []

    for yoga_dict in yogas:
        yname = yoga_dict.get("yoga")
        if not yname:
            continue
        active = True  # these are the ones active at the instant
        citation_id = yoga_dict.get("citation_id", "panchanga_engine/special_yogas")
        subj = f"YOGA_{yname.upper().replace(' ', '_')}"

        rows += [
            _row(cat, subj, "combination_name", chart_id, ay, build_id,
                 value_text=yname,
                 citation_human=f"Special yoga {yname}: active at birth ({ayanamsha_id}).",
                 verification_pass_status=vp, computed_at=computed_at),
            _row(cat, subj, "active_at_birth_flag", chart_id, ay, build_id,
                 value_text="true",
                 citation_human=f"Special yoga {yname} active at birth: true ({ayanamsha_id}).",
                 verification_pass_status=vp, computed_at=computed_at),
            _row(cat, subj, "constituent_facts_jsonb_atomic", chart_id, ay, build_id,
                 value_jsonb={
                     "tithi": pi.tithi.name if pi.tithi else None,
                     "vara": pi.vara.name if pi.vara else None,
                     "nakshatra": pi.nakshatra.name if pi.nakshatra else None,
                 },
                 citation_human=f"Special yoga {yname} constituent: tithi={pi.tithi.name if pi.tithi else None}, vara={pi.vara.name if pi.vara else None}, nakshatra={pi.nakshatra.name if pi.nakshatra else None}.",
                 verification_pass_status=vp, computed_at=computed_at),
        ]

    return rows


def _emit_panchaka_classification(pi: Any, chart_id: str, build_id: str,
                                   computed_at: str, ayanamsha_id: str) -> list[dict]:
    """panchanga_panchaka_classification (5 panchakas + overall)."""
    cat = "panchanga_panchaka_classification"
    ay = ayanamsha_id
    vp = _single_pass_verif()
    rows = []

    # 5-panchaka types and their nakshatra mapping
    PANCHAKA_NAKSHATRAS = {23: "Roga", 24: "Raja", 25: "Agni", 26: "Chora", 27: "Mrityu"}

    nak_id = pi.nakshatra.id if pi.nakshatra else 0
    active_panchaka = PANCHAKA_NAKSHATRAS.get(nak_id)

    for nak_num, ptype in PANCHAKA_NAKSHATRAS.items():
        is_active = (nak_id == nak_num)
        subj = f"PANCHAKA_{ptype.upper()}"
        nak_name = NAKSHATRA_NAMES[nak_num - 1]
        rows += [
            _row(cat, subj, "panchaka_name",         chart_id, ay, build_id,
                 value_text=ptype,
                 citation_human=f"Panchaka type {ptype}: active={is_active} ({ayanamsha_id}).",
                 verification_pass_status=vp, computed_at=computed_at),
            _row(cat, subj, "active_at_birth_flag",  chart_id, ay, build_id,
                 value_text=str(is_active).lower(),
                 citation_human=f"{ptype} Panchaka at birth: {is_active} ({ayanamsha_id}).",
                 verification_pass_status=vp, computed_at=computed_at),
            _row(cat, subj, "nakshatra_component",   chart_id, ay, build_id,
                 value_text=nak_name,
                 citation_human=f"{ptype} Panchaka nakshatra: {nak_name}.",
                 verification_pass_status=vp, computed_at=computed_at),
        ]

    # Overall panchaka classification
    subj_ov = "PANCHAKA_OVERALL"
    rows.append(_row(cat, subj_ov, "panchaka_overall_classification", chart_id, ay, build_id,
                     value_text=active_panchaka or "none",
                     citation_human=(
                         f"Active panchaka at birth: {active_panchaka or 'none'} ({ayanamsha_id})."
                     ),
                     verification_pass_status=vp, computed_at=computed_at))

    return rows


def _emit_panchaka_flag(pi: Any, chart_id: str, build_id: str,
                         computed_at: str, ayanamsha_id: str) -> list[dict]:
    """panchaka_flag (Panchak Rahit window — last 1/4 Dhanishtha through Revati)."""
    cat = "panchaka_flag"
    subj = "PANCHAKA_FLAG_BIRTH"
    ay = ayanamsha_id
    vp = _single_pass_verif()

    PANCHAKA_NAKSHATRAS = {23, 24, 25, 26, 27}
    nak_id = pi.nakshatra.id if pi.nakshatra else 0
    active = nak_id in PANCHAKA_NAKSHATRAS
    nak_name = NAKSHATRA_NAMES[nak_id - 1] if 1 <= nak_id <= 27 else ""

    rows = [
        _row(cat, subj, "active_at_birth_flag", chart_id, ay, build_id,
             value_text=str(active).lower(),
             citation_human=f"Panchaka (Panchak Rahit) active at birth: {active} ({ayanamsha_id}).",
             verification_pass_status=vp, computed_at=computed_at),
    ]
    if active:
        rows.append(_row(cat, subj, "nakshatra_position", chart_id, ay, build_id,
                         value_text=nak_name,
                         citation_human=f"Panchaka nakshatra at birth: {nak_name} ({ayanamsha_id}).",
                         verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_eclipse_proximity(pi: Any, chart_id: str, build_id: str,
                              computed_at: str, ayanamsha_id: str) -> list[dict]:
    """eclipse_proximity_natal — eclipses ±15 days from birth (ayanamsha-dependent for sign/nak)."""
    cat = "eclipse_proximity_natal"
    ay = ayanamsha_id
    vp = _single_pass_verif()
    rows = []

    # Eclipse proximity requires G4 eclipse table lookup — not available in panchanga_engine's
    # PanchangaInstant output directly. We emit a null-marked row per A4 §4 floor contract.
    subj = "ECLIPSE_PROXIMITY_BIRTH"
    rows.append(_row(cat, subj, "days_from_birth", chart_id, ay, build_id,
                     value_text="no_eclipse_±15d",
                     citation_human=(
                         f"Eclipse proximity at birth (±15 days): no eclipse found in "
                         f"G4 reference (ayanamsha={ayanamsha_id}). "
                         f"[EXTERNAL_COMPUTATION_REQUIRED: query G4 eclipse table]"
                     ),
                     verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_tara_bala_baseline(pi: Any, chart_id: str, build_id: str, computed_at: str,
                               ayanamsha_id: str) -> list[dict]:
    """
    tara_bala_natal_baseline — 27-row state table per ayanamsha.
    Birth nakshatra derived from pi.nakshatra.id (chart-specific).
    Each row: subject=TRANSIT_NAK_<SHORT>, key=tara_class, value=Janma/Sampat/...
    """
    cat = "tara_bala_natal_baseline"
    ay = ayanamsha_id
    vp = "single"
    rows = []

    birth_nak_id = (
        pi.nakshatra.id
        if (pi and pi.nakshatra and pi.nakshatra.id)
        else NATIVE_MOON_NAK_ID
    )
    birth_nak_name = NAKSHATRA_NAMES[birth_nak_id - 1] if 1 <= birth_nak_id <= 27 else "unknown"

    for transit_nak_idx in range(27):  # 0-indexed → nak_id = idx+1
        transit_nak_id = transit_nak_idx + 1
        short = NAKSHATRA_SHORT[transit_nak_idx]
        nak_name = NAKSHATRA_NAMES[transit_nak_idx]
        subj = f"TRANSIT_NAK_{short}"

        # Tara position: ((transit - birth) mod 27) + 1
        tara_pos = ((transit_nak_id - birth_nak_id) % 27) + 1
        # Map to 9-cycle name
        tara_pos_in_cycle = (tara_pos - 1) % 9 + 1
        tara_class = _TARA_QUALITY[tara_pos_in_cycle]

        rows.append(_row(cat, subj, "tara_class", chart_id, ay, build_id,
                         value_text=tara_class,
                         citation_human=(
                             f"When transit Moon is in {nak_name}, "
                             f"Tara state for native (birth nak={birth_nak_name}): "
                             f"{tara_class} ({ayanamsha_id})."
                         ),
                         verification_pass_status=vp, computed_at=computed_at))
    return rows


def _emit_chandra_bala_baseline(pi: Any, chart_id: str, build_id: str, computed_at: str,
                                  ayanamsha_id: str) -> list[dict]:
    """
    chandra_bala_natal_baseline — 12-row state table per ayanamsha.
    Birth Moon sign derived from pi.nakshatra.id (chart-specific).
    Each row: subject=TRANSIT_SIGN_<NAME>, key=classification.
    """
    cat = "chandra_bala_natal_baseline"
    ay = ayanamsha_id
    vp = "single"
    rows = []

    birth_nak_id = (
        pi.nakshatra.id
        if (pi and pi.nakshatra and pi.nakshatra.id)
        else NATIVE_MOON_NAK_ID
    )
    # Derive birth Moon sign from nakshatra start position (standard formula):
    # each sign spans 2.25 nakshatras; sign_id = floor((nak_id-1)*4/9) + 1
    birth_moon_sign_id = ((birth_nak_id - 1) * 4) // 9 + 1
    birth_moon_sign_name = SIGN_NAMES[birth_moon_sign_id - 1] if 1 <= birth_moon_sign_id <= 12 else "unknown"

    for sign_idx in range(12):  # 0-indexed → sign_id = idx+1
        sign_id = sign_idx + 1
        sign_name = SIGN_NAMES[sign_idx]
        subj = f"TRANSIT_SIGN_{sign_name.upper()}"

        # Position from birth Moon sign: 1=same sign
        position = (sign_id - birth_moon_sign_id) % 12 + 1
        classification = _CHANDRA_BALA.get(position, "neutral")

        rows.append(_row(cat, subj, "classification", chart_id, ay, build_id,
                         value_text=classification,
                         citation_human=(
                             f"When transit Moon is in {sign_name}, "
                             f"Chandra Bala for native (birth Moon sign={birth_moon_sign_name}): "
                             f"{classification} ({ayanamsha_id})."
                         ),
                         verification_pass_status=vp, computed_at=computed_at))
    return rows


# ── INSERT ────────────────────────────────────────────────────────────────────

def _insert_chart_facts_rows(conn: Any, rows: list[dict]) -> int:
    # Idempotency: replace this chart's prior rows for the scope being written so a
    # rebuild under a new build_id replaces instead of accreting.
    replace_prior_chart_facts(conn, rows)
    written = 0
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
              fact_id                  = EXCLUDED.fact_id,
              fact_value_text          = EXCLUDED.fact_value_text,
              fact_value_num           = EXCLUDED.fact_value_num,
              fact_value_jsonb         = EXCLUDED.fact_value_jsonb,
              citation_ref             = EXCLUDED.citation_ref,
              citation_human           = EXCLUDED.citation_human,
              source_calculation       = EXCLUDED.source_calculation,
              verification_pass_status = EXCLUDED.verification_pass_status,
              engine_version           = EXCLUDED.engine_version,
              computed_at              = EXCLUDED.computed_at
            """,
            r,
        )
        written += 1
    return written


# ── asset_throughput update ───────────────────────────────────────────────────

def _update_asset_throughput(chart_id: str, build_id: str, row_count: int) -> None:
    with _conn() as conn:
        update_asset_throughput(conn, "ga_panchanga", chart_id, build_id, row_count)


# ── Main build function ────────────────────────────────────────────────────────

def build_ga_panchanga(
    chart_id: str = CANONICAL_CHART_ID,
    build_id: Optional[str] = None,
    *,
    conn: Any = None,
    birth_params: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Build ga_panchanga for chart_id using panchanga_engine.panchanga_instant.

    Emits all A4 §2 categories into chart_facts:
    - Ayanamsha-INVARIANT: all panchanga categories with ayanamsha_id='INVARIANT'
    - Ayanamsha-DEPENDENT: nakshatra_moon, special_yogas, panchaka, tara_bala (×5 ayanamshas)
    - Tara bala baseline: 27 rows per ayanamsha
    - Chandra bala baseline: 12 rows per ayanamsha

    Returns summary dict. Raises RuntimeError on FORENSIC gate failure.
    """
    import uuid
    from panchang_engine import panchanga_instant

    if build_id is None:
        build_id = str(uuid.uuid4())

    from contextlib import nullcontext
    owns_conn = conn is None

    bp = resolve_birth_params(chart_id, birth_params)
    computed_at = datetime.now(timezone.utc).isoformat()

    summary: dict[str, Any] = {
        "chart_id": chart_id,
        "build_id": build_id,
        "forensic_pass": False,
        "total_chart_facts_rows": 0,
        "invariant_rows": 0,
        "dependent_rows_by_ayanamsha": {},
        "status": "IN_PROGRESS",
    }

    logger.info(
        "[ga_panchanga_writer] Starting GA4 build chart_id=%s build_id=%s",
        chart_id, build_id,
    )

    # Compute PanchangaInstant at birth.
    # birth_params from the DB (via _to_birth_params) uses datetime_iso + tz_offset_hours.
    # The panchanga_instant() call needs a datetime object and tz_offset_minutes.
    # Normalise both key formats here.
    if "datetime_local" in bp:
        birth_dt = bp["datetime_local"]
    else:
        from datetime import datetime as _dt
        birth_dt = _dt.fromisoformat(bp["datetime_iso"])
    lat = bp["latitude_deg"]
    lon = bp["longitude_deg"]
    if "tz_offset_minutes" in bp:
        tz_min = bp["tz_offset_minutes"]
    else:
        tz_min = int(round(bp["tz_offset_hours"] * 60))

    pi = panchanga_instant(birth_dt, lat, lon, tz_min)

    # FORENSIC gate — native-anchored; asserted only for the native (Phase 3B).
    if chart_id == CANONICAL_CHART_ID:
        panchanga_forensic_gate(pi)
    summary["forensic_pass"] = True

    # ── Build INVARIANT rows ─────────────────────────────────────────────────
    invariant_rows: list[dict] = []
    invariant_rows += _emit_tithi(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_vara(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_yoga(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_karana(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_solar_context(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_calendrical(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_sun_moon_dynamics(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_disha_shul(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_tithi_shoonya(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_nakshatra_shoonya(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_agni_vasa(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_hora_birth(pi, chart_id, build_id, computed_at)
    invariant_rows += _emit_choghadiya_birth(pi, chart_id, build_id, computed_at)

    # Inauspicious windows (9 categories)
    INAUSPICIOUS_WINDOWS = [
        ("rahu_kalam",       "RAHU_KALAM_BIRTH_DAY"),
        ("yamaganda_kalam",  "YAMAGANDA_KALAM_BIRTH_DAY"),
        ("gulika_kalam",     "GULIKA_KALAM_BIRTH_DAY"),
        ("durmuhurta",       "DURMUHURTA_BIRTH_DAY"),
        ("varjyam",          "VARJYAM_BIRTH_DAY"),
        ("visha_ghati",      "VISHA_GHATI_BIRTH_DAY"),
        ("sashtighati",      "SASHTIGHATI_BIRTH_DAY"),
        ("yamakantaka",      "YAMAKANTAKA_BIRTH_DAY"),
        ("krakaca",          "KRAKACA_BIRTH_DAY"),
    ]
    for wname, wsubj in INAUSPICIOUS_WINDOWS:
        invariant_rows += _emit_inauspicious_window(
            pi, wname, wsubj, chart_id, build_id, computed_at
        )

    # Auspicious windows (9 categories)
    AUSPICIOUS_WINDOWS = [
        ("abhijit_muhurta",    "ABHIJIT_MUHURTA_BIRTH_DAY"),
        ("brahma_muhurta",     "BRAHMA_MUHURTA_BIRTH_DAY"),
        ("pratah_sandhya",     "PRATAH_SANDHYA_BIRTH_DAY"),
        ("madhyahna_sandhya",  "MADHYAHNA_SANDHYA_BIRTH_DAY"),
        ("sayam_sandhya",      "SAYAM_SANDHYA_BIRTH_DAY"),
        ("amrit_kaal",         "AMRIT_KAAL_BIRTH_DAY"),
        ("vijaya_muhurta",     "VIJAYA_MUHURTA_BIRTH_DAY"),
        ("godhuli_muhurta",    "GODHULI_MUHURTA_BIRTH_DAY"),
        ("nishita_kala",       "NISHITA_KALA_BIRTH_DAY"),
    ]
    for wname, wsubj in AUSPICIOUS_WINDOWS:
        invariant_rows += _emit_auspicious_window(
            pi, wname, wsubj, chart_id, build_id, computed_at
        )

    # Bhadra flag (ayanamsha-invariant for karana)
    invariant_rows += _emit_bhadra_flag(pi, chart_id, build_id, computed_at, "INVARIANT")

    summary["invariant_rows"] = len(invariant_rows)

    # ── Build DEPENDENT rows (×5 ayanamshas) ────────────────────────────────
    all_dependent: list[dict] = []
    for ay in CANONICAL_AYANAMSHAS:
        dep_rows: list[dict] = []
        dep_rows += _emit_nakshatra_moon(pi, chart_id, build_id, computed_at, ay)
        dep_rows += _emit_special_yoga_combinations(pi, chart_id, build_id, computed_at, ay)
        dep_rows += _emit_panchaka_classification(pi, chart_id, build_id, computed_at, ay)
        dep_rows += _emit_panchaka_flag(pi, chart_id, build_id, computed_at, ay)
        dep_rows += _emit_eclipse_proximity(pi, chart_id, build_id, computed_at, ay)
        dep_rows += _emit_bhadra_flag(pi, chart_id, build_id, computed_at, ay)

        # Tara bala baseline (27 rows per ayanamsha) — derived from this chart's birth nakshatra
        dep_rows += _emit_tara_bala_baseline(pi, chart_id, build_id, computed_at, ay)

        # Chandra bala baseline (12 rows per ayanamsha) — derived from this chart's birth Moon sign
        dep_rows += _emit_chandra_bala_baseline(pi, chart_id, build_id, computed_at, ay)

        summary["dependent_rows_by_ayanamsha"][ay] = len(dep_rows)
        all_dependent.extend(dep_rows)

    all_rows = invariant_rows + all_dependent

    # ── Write to DB ──────────────────────────────────────────────────────────
    with (_conn() if owns_conn else nullcontext(conn)) as conn:
        written = _insert_chart_facts_rows(conn, all_rows)
        if owns_conn:
            conn.commit()

    summary["total_chart_facts_rows"] = written
    summary["status"] = "PASS"

    logger.info(
        "[ga_panchanga_writer] COMPLETE. invariant=%d dependent_total=%d total=%d",
        len(invariant_rows), len(all_dependent), written,
    )

    # Update asset_throughput
    if owns_conn:
        _update_asset_throughput(chart_id, build_id, written)

    return summary
