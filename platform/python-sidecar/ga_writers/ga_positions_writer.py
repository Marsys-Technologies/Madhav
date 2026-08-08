"""
ga_positions_writer.py — GA3 ga_positions writer
==================================================
Writes per-chart, per-ayanamsha graha positions to `chart_facts`.

Per A3_CHART_FACTS_SPEC §3 + GA3 brief §6.1:
  - 5 canonical ayanamshas × ≥10 bodies (9 grahas + Lagna)
  - Atomic rows: each key (longitude, sign, nakshatra, pada, house) = own row
  - Dual citations (citation_ref + citation_human) on every row
  - FORENSIC gate MUST pass before any INSERT

FORENSIC anchors (birth: 1984-02-05 10:43 IST, lat 20.27, lon 85.84):
  - Sun: Capricorn
  - Moon nakshatra: Purva Bhadrapada
  - Lagna: Aries (NOT Scorpio)

Storage strategy:
  - chart_facts rows: one row per atomic fact key (sign, nakshatra, longitude, etc.)
    fact_category IN ('graha_position', 'graha_sign_attributes')

chart_facts is the canonical positions store (ganita_positions dropped at migration 232).
"""
from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any

from pyjhora_adapter.compute import compute_chart
from pyjhora_adapter.version import ENGINE_VERSION

from brahmagyan.graha_vocabulary import norm_graha
from ga_writers._idempotency import replace_prior_chart_facts
from ga_writers._telemetry import update_asset_throughput

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# Canonical ayanamsha ids per A3 §4.
# Maps A3 canonical id → pyjhora_adapter ayanamsha_id
CANONICAL_AYANAMSHAS: dict[str, str] = {
    "lahiri_chitrapaksha": "lahiri",
    "true_chitra": "true_chitra",
    "krishnamurti": "kp",
    "raman": "raman",
    "surya_siddhanta_classical": "surya_siddhanta",
}

# Planet name → fact_subject (A3 §5 UPPER_SNAKE convention).
# Values sourced from the graha SSoT (brahmagyan/graha_vocabulary.norm_graha)
# rather than hardcoded literals — ADHIṢṬHĀNA Lane A2. `.get()`-with-None
# semantics on an unrecognized engine name are preserved exactly (this dict
# is a closed allowlist of the pyjhora_adapter engine's own output names,
# not a general normalizer).
PLANET_TO_SUBJECT: dict[str, str] = {
    name: norm_graha(name)
    for name in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
        "Rahu", "Ketu", "Lagna",
    )
}

# Forbidden narration patterns (A3 §17, brief §7)
FORBIDDEN_PATTERNS = [
    "indicates", "suggests", "implies", "means", "denotes",
    "yields", "results in", "leads to",
]


# ── DB connection ────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[ga_positions_writer] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── fact_id derivation (A3 §2) ───────────────────────────────────────────────

def _fact_id(category: str, subject: str, key: str, chart_id: str,
              ayanamsha_id: str, build_id: str) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Citation builders (A3 §6) ────────────────────────────────────────────────

def _citation_ref(category: str, subject: str, key: str,
                  chart_id: str, ayanamsha_id: str, eng_ver: str) -> str:
    return f"{category}.{subject}.{key}@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}"


def _citation_human_position(graha: str, key: str, value_text: str | None,
                              value_num: float | None, ayanamsha_id: str) -> str:
    """Render a human-readable citation sentence for a position fact."""
    if key == "longitude_sidereal":
        return (f"{graha} sidereal longitude: {value_num:.6f} deg "
                f"({ayanamsha_id.replace('_', ' ').title()}).")
    if key == "longitude_tropical":
        return f"{graha} tropical longitude: {value_num:.6f} deg."
    if key == "sign":
        return (f"{graha} is in {value_text} "
                f"({ayanamsha_id.replace('_', ' ').title()}).")
    if key == "sign_lord":
        return f"{graha} sign lord: {value_text} ({ayanamsha_id.replace('_', ' ').title()})."
    if key == "nakshatra":
        return (f"{graha} nakshatra: {value_text} "
                f"({ayanamsha_id.replace('_', ' ').title()}).")
    if key == "nakshatra_lord":
        return f"{graha} nakshatra lord: {value_text} ({ayanamsha_id.replace('_', ' ').title()})."
    if key == "pada":
        return (f"{graha} nakshatra pada: {int(value_num)} "
                f"({ayanamsha_id.replace('_', ' ').title()}).")
    if key == "house_d1":
        return (f"{graha} whole-sign house: {int(value_num)} "
                f"({ayanamsha_id.replace('_', ' ').title()}).")
    if key == "retrograde_flag":
        return f"{graha} is {value_text} at birth."
    if key == "combustion_state":
        return f"{graha} combustion: {value_text}."
    if key == "degree_in_sign":
        return (f"{graha} degree in sign: {value_num:.6f} deg "
                f"({ayanamsha_id.replace('_', ' ').title()}).")
    if key == "sign_num":
        return (f"{graha} sign number: {int(value_num)} "
                f"({ayanamsha_id.replace('_', ' ').title()}).")
    return f"{graha} {key}: {value_text or value_num} ({ayanamsha_id})."


# ── Linter (A3 §17) ──────────────────────────────────────────────────────────

def _check_narration(text_value: str | None, context: str) -> None:
    if text_value is None:
        return
    lower = text_value.lower()
    for pat in FORBIDDEN_PATTERNS:
        if pat in lower:
            raise ValueError(
                f"[NARRATION LINTER] Forbidden pattern '{pat}' found in "
                f"fact_value_text='{text_value}' at {context}"
            )


# ── FORENSIC gate (campaign §C) ───────────────────────────────────────────────

def forensic_gate(chart_output: dict[str, Any], ayanamsha_id: str) -> None:
    """
    Assert FORENSIC anchors against engine output.
    Halts (raises) if any anchor fails.
    Checks:
      - Sun in Capricorn
      - Moon nakshatra = Purva Bhadrapada
      - Lagna sign = Aries
    Panchanga anchors (Tithi/Vara/Yoga/Karana) checked by GA4 panchanga writer.
    """
    grahas = chart_output.get("grahas", [])
    ascendant = chart_output.get("ascendant", {})

    sun = next((g for g in grahas if g["name"] == "Sun"), None)
    moon = next((g for g in grahas if g["name"] == "Moon"), None)

    failures = []

    if sun is None:
        failures.append("Sun graha not found in engine output")
    elif sun.get("sign") != "Capricorn":
        failures.append(
            f"FORENSIC FAIL: Sun sign expected Capricorn, got '{sun.get('sign')}' "
            f"(ayanamsha={ayanamsha_id})"
        )

    if moon is None:
        failures.append("Moon graha not found in engine output")
    elif moon.get("nakshatra") != "Purva Bhadrapada":
        failures.append(
            f"FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada', "
            f"got '{moon.get('nakshatra')}' (ayanamsha={ayanamsha_id})"
        )

    lagna_sign = ascendant.get("sign")
    if lagna_sign != "Aries":
        failures.append(
            f"FORENSIC FAIL: Lagna sign expected 'Aries', got '{lagna_sign}' "
            f"(ayanamsha={ayanamsha_id}). Known trap: NOT Scorpio."
        )

    if failures:
        msg = "FORENSIC GATE FAILED:\n" + "\n".join(f"  - {f}" for f in failures)
        logger.error(msg)
        # Write to CONDUCTOR_HALT_LOG if accessible
        _write_halt_log("FORENSIC_GATE", msg)
        raise RuntimeError(msg)

    logger.info(
        "[FORENSIC] PASS: Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries (%s)",
        ayanamsha_id,
    )


def _write_halt_log(gate_name: str, msg: str) -> None:
    """Append failure to CONDUCTOR_HALT_LOG.md if path is resolvable.

    Target directory is overridable via CONDUCTOR_HALT_LOG_DIR_OVERRIDE, which
    the test suite sets to an isolated tmp dir (see tests/conftest.py) so that
    forensic-gate unit tests exercising deliberately-bad chart data (e.g.
    test_ga3_writers.py::TestForensicGate) never append fixture noise to the
    real repo-tracked CONDUCTOR_HALT_LOG.md.
    """
    try:
        import pathlib
        override = os.environ.get("CONDUCTOR_HALT_LOG_DIR_OVERRIDE")
        if override:
            candidate = pathlib.Path(override) / "CONDUCTOR_HALT_LOG.md"
            candidate.parent.mkdir(parents=True, exist_ok=True)
            with open(candidate, "a", encoding="utf-8") as fh:
                fh.write(
                    f"\n## HALT: {gate_name} — {datetime.now(timezone.utc).isoformat()}\n"
                    f"{msg}\n"
                )
            return
        # Walk up from current file to find project root
        p = pathlib.Path(__file__).resolve()
        for _ in range(8):
            candidate = p / "00_ARCHITECTURE" / "CONDUCTOR" / "CONDUCTOR_HALT_LOG.md"
            if candidate.parent.exists():
                with open(candidate, "a", encoding="utf-8") as fh:
                    fh.write(
                        f"\n## HALT: {gate_name} — {datetime.now(timezone.utc).isoformat()}\n"
                        f"{msg}\n"
                    )
                return
            p = p.parent
    except Exception:
        pass  # Best-effort — do not mask the original error


# ── Position rows builder ────────────────────────────────────────────────────

def _build_position_rows(
    chart_output: dict[str, Any],
    chart_id: str,
    build_id: str,
    ayanamsha_id_canonical: str,
    ayanamsha_id_adapter: str,
    computed_at: str,
) -> list[dict[str, Any]]:
    """
    Build chart_facts rows for graha_position category.
    One row per atomic fact (longitude, sign, nakshatra, pada, house, etc.).
    Returns list of row dicts ready for INSERT.
    """
    grahas = chart_output.get("grahas", [])
    ascendant = chart_output.get("ascendant", {})
    eng_ver = ENGINE_VERSION

    rows: list[dict[str, Any]] = []

    # ── Grahas ──
    for g in grahas:
        subject = PLANET_TO_SUBJECT.get(g["name"])
        if subject is None:
            logger.warning("[ga_positions_writer] Unknown planet name: %s", g["name"])
            continue

        lon_sid = float(g.get("longitude_deg", g.get("lon", 0)))
        sign = g.get("sign", "")
        sign_lord = g.get("sign_lord", "")
        nakshatra = g.get("nakshatra", "")
        nakshatra_lord = g.get("nakshatra_lord", "")
        pada = int(g.get("pada", g.get("nakshatra_pada", 0)))
        house_d1 = int(g.get("house", 0))
        retrograde = g.get("retrograde", False)
        retro_flag = "retrograde" if retrograde else "direct"
        combust = g.get("combust", False)
        combustion_state = "combust" if combust else "none"
        degree_in_sign = float(g.get("degree_in_sign", lon_sid % 30.0))
        sign_num = int(g.get("sign_id", 0))  # 1-based

        # Atomic row definitions for this graha
        fact_atoms: list[tuple[str, str, float | None, str | None, str | None]] = [
            # (category, key, value_num, value_text, unit)
            ("graha_position", "longitude_sidereal", lon_sid, None, "deg"),
            ("graha_position", "sign", None, sign, None),
            ("graha_position", "sign_lord", None, sign_lord, None),
            ("graha_position", "nakshatra", None, nakshatra, None),
            ("graha_position", "nakshatra_lord", None, nakshatra_lord, None),
            ("graha_position", "pada", float(pada), None, None),
            ("graha_position", "house_d1", float(house_d1), None, None),
            ("graha_position", "retrograde_flag", None, retro_flag, None),
            ("graha_position", "combustion_state", None, combustion_state, None),
            ("graha_sign_attributes", "sign_num", float(sign_num), None, None),
            ("graha_sign_attributes", "degree_in_sign", degree_in_sign, None, "deg"),
        ]

        for cat, key, vnum, vtxt, unit in fact_atoms:
            _check_narration(vtxt, f"{subject}.{key}")
            fid = _fact_id(cat, subject, key, chart_id, ayanamsha_id_canonical, build_id)
            cref = _citation_ref(cat, subject, key, chart_id, ayanamsha_id_canonical, eng_ver)
            chum = _citation_human_position(
                g["name"], key, vtxt, vnum, ayanamsha_id_canonical
            )

            # ayanamsha_dependent = False for speed/retro/combustion (INVARIANT)
            eff_ayan = (
                "INVARIANT"
                if cat in ("graha_retrogression_state", "graha_combustion_state", "graha_speed_state")
                   and key in ("retrograde_flag", "combustion_state", "speed_dps")
                else ayanamsha_id_canonical
            )

            rows.append({
                "fact_id": fid,
                "chart_id": chart_id,
                "ayanamsha_id": eff_ayan,
                "build_id": build_id,
                "fact_category": cat,
                "fact_subject": subject,
                "fact_key": key,
                "fact_value_text": vtxt,
                "fact_value_num": vnum,
                "fact_value_jsonb": None,
                "unit": unit,
                "citation_ref": cref,
                "citation_human": chum,
                "source_calculation": f"pyjhora_adapter.positions/{eng_ver}",
                "verification_pass_status": "single",
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

    # ── Lagna (ascendant) ──
    asc = ascendant
    if asc:
        subject = "LAGNA"
        lon_sid = float(asc.get("longitude_deg", 0))
        sign = asc.get("sign", "")
        sign_lord = asc.get("sign_lord", "")
        nakshatra = asc.get("nakshatra") or ""
        nakshatra_lord = ""  # Lagna nakshatra lord not critical for positions
        pada = int(asc.get("pada", 0) or 0)
        sign_num = int(asc.get("sign_id", 0))
        degree_in_sign = float(asc.get("degree_in_sign", lon_sid % 30.0))

        fact_atoms_asc: list[tuple[str, str, float | None, str | None, str | None]] = [
            ("graha_position", "longitude_sidereal", lon_sid, None, "deg"),
            ("graha_position", "sign", None, sign, None),
            ("graha_position", "sign_lord", None, sign_lord, None),
            ("graha_position", "pada", float(pada), None, None),
            ("graha_position", "house_d1", 1.0, None, None),  # Lagna is always H1
            ("graha_sign_attributes", "sign_num", float(sign_num), None, None),
            ("graha_sign_attributes", "degree_in_sign", degree_in_sign, None, "deg"),
        ]

        for cat, key, vnum, vtxt, unit in fact_atoms_asc:
            _check_narration(vtxt, f"{subject}.{key}")
            fid = _fact_id(cat, subject, key, chart_id, ayanamsha_id_canonical, build_id)
            cref = _citation_ref(cat, subject, key, chart_id, ayanamsha_id_canonical, eng_ver)
            chum = _citation_human_position(
                "Lagna", key, vtxt, vnum, ayanamsha_id_canonical
            )
            rows.append({
                "fact_id": fid,
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id_canonical,
                "build_id": build_id,
                "fact_category": cat,
                "fact_subject": subject,
                "fact_key": key,
                "fact_value_text": vtxt,
                "fact_value_num": vnum,
                "fact_value_jsonb": None,
                "unit": unit,
                "citation_ref": cref,
                "citation_human": chum,
                "source_calculation": f"pyjhora_adapter.houses/{eng_ver}",
                "verification_pass_status": "single",
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

    return rows


# ── Bhāva-chalit rows builder (real cusps; ADDITIVE — DR-2) ──────────────────

def _chalit_row(
    chart_id: str, ayanamsha_id: str, build_id: str, computed_at: str,
    category: str, subject: str, key: str,
    value_num: float | None, value_text: str | None,
    unit: str | None, citation_human: str,
) -> dict[str, Any]:
    eng_ver = ENGINE_VERSION
    _check_narration(value_text, f"{subject}.{key}")
    return {
        "fact_id": _fact_id(category, subject, key, chart_id, ayanamsha_id, build_id),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "fact_category": category,
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_text": value_text,
        "fact_value_num": value_num,
        "fact_value_jsonb": None,
        "unit": unit,
        "citation_ref": _citation_ref(category, subject, key, chart_id, ayanamsha_id, eng_ver),
        "citation_human": citation_human,
        "source_calculation": f"pyjhora_adapter.houses.compute_bhava_chalit/{eng_ver}",
        "verification_pass_status": "single",
        "engine_version": eng_ver,
        "computed_at": computed_at,
    }


def _build_chalit_rows(
    chart_output: dict[str, Any],
    chart_id: str,
    build_id: str,
    ayanamsha_id_canonical: str,
    computed_at: str,
) -> list[dict[str, Any]]:
    """
    Emit the new L1 chalit fact categories (ADDITIVE second data layer; DR-2 —
    whole-sign house_d1 is NOT changed):

      * ``bhava_cusps``  — subject BHAVA_01..12; keys {sripati,placidus}_{start,madhya,end}.
      * ``house_chalit`` — subject per graha; Sripati chalit house + cusp distances.
      * ``sandhi_flag``  — subject per graha; junction flag (within-orb OR whole-sign≠chalit).

    Source: chart_output["bhava_chalit"] (pyjhora_adapter.houses.compute_bhava_chalit).
    """
    chalit = chart_output.get("bhava_chalit") or {}
    if not chalit:
        return []
    rows: list[dict[str, Any]] = []
    ay = ayanamsha_id_canonical
    ay_title = ay.replace("_", " ").title()

    # ── bhava_cusps: 12 houses × {sripati,placidus} × {start,madhya,end} ──
    sri_cusps = (chalit.get("sripati") or {}).get("cusps") or []
    plac_cusps = (chalit.get("placidus") or {}).get("cusps") or []
    for system, cusp_list in (("sripati", sri_cusps), ("placidus", plac_cusps)):
        for c in cusp_list:
            hnum = int(c["house"])
            subj = f"BHAVA_{hnum:02d}"
            for edge in ("start", "madhya", "end"):
                key = f"{system}_{edge}"
                val = float(c[edge])
                rows.append(_chalit_row(
                    chart_id, ay, build_id, computed_at,
                    "bhava_cusps", subj, key, val, None, "deg",
                    f"Bhāva {hnum} {system.title()} {edge} cusp: {val:.6f} deg ({ay_title}).",
                ))

    # ── house_chalit + sandhi_flag: per graha ──
    graha_chalit = chalit.get("graha_chalit") or {}
    for gname, gc in graha_chalit.items():
        subj = PLANET_TO_SUBJECT.get(gname)
        if subj is None:
            continue
        chalit_house = int(gc["chalit_house"])
        ws_house = gc.get("whole_sign_house")
        dist_madhya = float(gc["dist_to_madhya_deg"])
        dist_bound = float(gc["dist_to_nearest_boundary_deg"])
        nearest = str(gc.get("nearest_boundary", ""))

        rows.append(_chalit_row(
            chart_id, ay, build_id, computed_at,
            "house_chalit", subj, "chalit_house_sripati", float(chalit_house), None, None,
            f"{gname} Sripati bhāva-chalit house: {chalit_house} ({ay_title}).",
        ))
        if ws_house is not None:
            rows.append(_chalit_row(
                chart_id, ay, build_id, computed_at,
                "house_chalit", subj, "whole_sign_house", float(int(ws_house)), None, None,
                f"{gname} whole-sign house: {int(ws_house)} (primary frame; {ay_title}).",
            ))
        rows.append(_chalit_row(
            chart_id, ay, build_id, computed_at,
            "house_chalit", subj, "dist_to_madhya_deg", dist_madhya, None, "deg",
            f"{gname} arc to Sripati bhāva-madhya: {dist_madhya:.6f} deg ({ay_title}).",
        ))
        rows.append(_chalit_row(
            chart_id, ay, build_id, computed_at,
            "house_chalit", subj, "dist_to_nearest_boundary_deg", dist_bound, None, "deg",
            f"{gname} arc to nearest Sripati bhāva boundary: {dist_bound:.6f} deg ({ay_title}).",
        ))
        rows.append(_chalit_row(
            chart_id, ay, build_id, computed_at,
            "house_chalit", subj, "nearest_boundary", None, nearest, None,
            f"{gname} nearest Sripati bhāva boundary: {nearest} ({ay_title}).",
        ))

        # sandhi_flag category
        flag = bool(gc.get("sandhi_flag"))
        reasons = gc.get("sandhi_reasons") or []
        rows.append(_chalit_row(
            chart_id, ay, build_id, computed_at,
            "sandhi_flag", subj, "sandhi_flag", None, str(flag).lower(), None,
            f"{gname} bhāva-sandhi flag: {str(flag).lower()} ({ay_title}).",
        ))
        rows.append(_chalit_row(
            chart_id, ay, build_id, computed_at,
            "sandhi_flag", subj, "sandhi_reasons", None, ",".join(reasons) or "none", None,
            f"{gname} bhāva-sandhi reasons: {','.join(reasons) or 'none'} ({ay_title}).",
        ))

    return rows


# ── chart_facts INSERT (atomic rows) ─────────────────────────────────────────

def _insert_chart_facts_rows(conn: Any, rows: list[dict[str, Any]]) -> int:
    # Idempotency: replace this chart's prior chart_facts rows for the scope being
    # written so a rebuild under a new build_id replaces instead of accreting.
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
              fact_id          = EXCLUDED.fact_id,
              fact_value_text  = EXCLUDED.fact_value_text,
              fact_value_num   = EXCLUDED.fact_value_num,
              citation_ref     = EXCLUDED.citation_ref,
              citation_human   = EXCLUDED.citation_human,
              engine_version   = EXCLUDED.engine_version,
              computed_at      = EXCLUDED.computed_at
            """,
            r,
        )
        written += 1
    return written


# ── Main build function ───────────────────────────────────────────────────────

def build_ga_positions(
    chart_id: str,
    build_id: str | None = None,
    *,
    conn: Any = None,
    birth_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build ga_positions for the given chart_id across all 5 canonical ayanamshas.

    Returns summary dict with row counts.

    Raises RuntimeError on FORENSIC gate failure (no rows committed).

    Connection ownership (Orchestrator Convergence Phase 3):
    - conn injected (orchestrator path): writes on the caller-owned connection,
      does NOT commit or close, does NOT write asset_throughput (the orchestrator
      is the sole build-state writer). The caller's SAVEPOINT owns atomicity.
    - conn None (legacy CLI path via build_runner): opens its own connection,
      commits, closes, and writes asset_throughput via _telemetry.
    """
    import uuid
    from contextlib import nullcontext
    if build_id is None:
        build_id = str(uuid.uuid4())

    owns_conn = conn is None
    # Birth-param resolution: every chart (native included) must arrive with real
    # birth_params from public.charts via the orchestrator's fetch_birth_params().
    # No hardcoded fallback — a missing birth_params is always a bug, never a
    # legitimate path.
    if not birth_params:
        raise ValueError(
            f"[ga_positions_writer] no birth_params for chart_id={chart_id}; "
            f"orchestrator must populate ctx.config['birth_params'] from "
            f"fetch_birth_params() before calling this writer. "
            f"Ensure public.charts has a row for this chart."
        )
    bp = birth_params
    computed_at = datetime.now(timezone.utc).isoformat()

    summary: dict[str, Any] = {
        "chart_id": chart_id,
        "build_id": build_id,
        "ayanamshas": {},
        "total_chart_facts_rows": 0,
        "forensic_pass": False,
    }

    logger.info(
        "[ga_positions_writer] Starting build chart_id=%s build_id=%s",
        chart_id, build_id,
    )

    with (_conn() if owns_conn else nullcontext(conn)) as conn:
        for canonical_id, adapter_id in CANONICAL_AYANAMSHAS.items():
            logger.info("[ga_positions_writer] Computing ayanamsha=%s", canonical_id)

            # Compute chart
            chart_output = compute_chart(inputs=bp, ayanamsha_id=adapter_id)

            # FORENSIC gate — native-anchored; asserted only for the native chart
            # (a non-native chart has no pre-verified anchor). Phase 3B.
            if chart_id == CANONICAL_CHART_ID:
                forensic_gate(chart_output, canonical_id)

            summary["forensic_pass"] = True

            # Build chart_facts atomic rows
            cf_rows = _build_position_rows(
                chart_output, chart_id, build_id,
                canonical_id, adapter_id, computed_at,
            )
            # Bhāva-chalit fact categories (additive second data layer; DR-2)
            cf_rows.extend(_build_chalit_rows(
                chart_output, chart_id, build_id, canonical_id, computed_at,
            ))

            # Write chart_facts atomic rows
            cf_count = _insert_chart_facts_rows(conn, cf_rows)

            summary["ayanamshas"][canonical_id] = {
                "chart_facts_rows": cf_count,
            }
            summary["total_chart_facts_rows"] += cf_count

            logger.info(
                "[ga_positions_writer] ayanamsha=%s cf_rows=%d",
                canonical_id, cf_count,
            )

        if owns_conn:
            conn.commit()

    # asset_throughput is written by the orchestrator on the conformed path; only
    # the legacy standalone CLI (owns_conn) writes it here via _telemetry.
    if owns_conn:
        _update_asset_throughput(
            chart_id=chart_id,
            build_id=build_id,
            asset_id="ga_positions",
            row_count=summary["total_chart_facts_rows"],
        )

    logger.info(
        "[ga_positions_writer] COMPLETE. Total cf=%d",
        summary["total_chart_facts_rows"],
    )
    return summary


# ── asset_throughput update (brief §11) ─────────────────────────────────────

def _update_asset_throughput(
    chart_id: str,
    build_id: str,
    asset_id: str,
    row_count: int,
) -> None:
    """Update asset_throughput for this asset/chart to reflect built state
    (delegates to the shared _telemetry helper writing the real schema)."""
    with _conn() as conn:
        update_asset_throughput(conn, asset_id, chart_id, build_id, row_count)
