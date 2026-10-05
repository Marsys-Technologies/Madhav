"""Chart context for the '5.0' evaluator (Pravāha A5.3, window_evaluator).

Reads the pinned candidate chart's L1 operands from `chart_facts` (L1 is the
authority, §N.5 — never recomputed here) into the exact dict shape
`services/gochara_rules` consumes: {"lagna_deg": float, "natal": {Title: λ}}.

Honesty contract: a missing or conflicting operand is NAMED in
`operands_missing` — never defaulted, never row-order picked (the
step06a_class_context.py precedent). `source_fact_ids` carries the fact_ids
read, so every downstream record can cite its L1 provenance
(kgrr_source_fact_ids_ck: non-empty unless fixture).

Read-only: this module never writes.
"""
from __future__ import annotations

from . import targets

#: L1 subjects of the nine grahas (mean nodes — the pinned chart's node
#: convention, substrate pin 3) + LAGNA, as stored under
#: graha_position/longitude_sidereal.
NATAL_SUBJECTS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT",
                  "RAH_MEAN", "KET_MEAN")

#: The canonical chart's sidereal ayānāṃśa predicate (step06a precedent).
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

_SUBJECT_TITLE = {
    "SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury",
    "JUP": "Jupiter", "VEN": "Venus", "SAT": "Saturn",
    "RAH_MEAN": "Rahu", "KET_MEAN": "Ketu",
}


def fetch_chart_context(conn, chart_id: str,
                        ayanamsha_id: str = CANONICAL_AYANAMSHA) -> dict:
    """{lagna_deg, natal{Title: λ}, operands_missing, source_fact_ids}.

    A subject with several DISTINCT stored values is a conflict: excluded and
    named `graha_position:<SUBJ>:conflict` — never picked by row order. A
    read failure names `chart_facts:unreadable` and records the error.
    """
    out = {"chart_id": chart_id, "ayanamsha_id": ayanamsha_id,
           "lagna_deg": None, "natal": {}, "operands_missing": [],
           "source_fact_ids": [], "source": "L1 chart_facts"}
    try:
        rows = conn.execute(
            "SELECT fact_id, fact_subject, fact_value_num FROM chart_facts"
            " WHERE chart_id = %s AND ayanamsha_id = %s"
            "   AND fact_category = 'graha_position'"
            "   AND fact_key = 'longitude_sidereal'",
            (chart_id, ayanamsha_id)).fetchall()
    except Exception as exc:  # noqa: BLE001
        out["operands_missing"] = ["chart_facts:unreadable"]
        out["error"] = str(exc)
        return out
    return _fill_from_rows(out, rows)


def _fill_from_rows(out: dict, rows) -> dict:
    """The row -> context logic, ONE implementation for the live read and the snapshot-copy read (rows = (fact_id, fact_subject, fact_value_num))."""
    seen: dict[str, set] = {}
    fact_ids: dict[str, str] = {}
    for row in rows:
        fid, subj, num = (
            (row["fact_id"], row["fact_subject"], row["fact_value_num"])
            if isinstance(row, dict) else row)
        if num is None:
            continue
        subj = str(subj)
        if subj != "LAGNA" and subj not in NATAL_SUBJECTS:
            continue
        try:
            value = targets.assert_float64_exact(num)
        except ValueError:
            # an L1 numeric a float64 cannot carry exactly: named, never quantised (F-3 §3)
            out["operands_missing"].append(f"graha_position:{subj}:not_float64_exact")
            continue
        seen.setdefault(subj, set()).add(value)
        fact_ids.setdefault(subj, str(fid))
    for subj, vals in seen.items():
        if len(vals) != 1:
            out["operands_missing"].append(f"graha_position:{subj}:conflict")
            continue
        (lon,) = tuple(vals)
        if subj == "LAGNA":
            out["lagna_deg"] = lon
        else:
            out["natal"][_SUBJECT_TITLE[subj]] = lon
        out["source_fact_ids"].append(fact_ids[subj])
    if out["lagna_deg"] is None:
        out["operands_missing"].append("graha_position:LAGNA")
    for subj in NATAL_SUBJECTS:
        if _SUBJECT_TITLE[subj] not in out["natal"]:
            out["operands_missing"].append(f"graha_position:{subj}")
    return out


def fetch_chart_context_from_snapshot(conn, chart_id: str, generation: str) -> dict:
    """The same context, read from the search-input SNAPSHOT's own COPY of the consumed fact rows (G12, Codex round 1 ruling 3): after the snapshot
    substep every computation of the build reads THIS, never live L1, so the output is computed from exactly the inputs the snapshot binds even when an
    L1 rebuild lands between substeps. A snapshot without a copy (migration 1305 not applied) falls back to the live read, as before."""
    import json
    from decimal import Decimal
    out = {"chart_id": chart_id, "ayanamsha_id": CANONICAL_AYANAMSHA, "lagna_deg": None, "natal": {}, "operands_missing": [],
           "source_fact_ids": [], "source": "snapshot copy of L1 chart_facts"}
    has = conn.execute(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'"
        " AND column_name = 'consumed_fact_rows'").fetchone()
    if int(next(iter(has.values())) if isinstance(has, dict) else has[0]) != 1:
        return fetch_chart_context(conn, chart_id)
    row = conn.execute("SELECT consumed_fact_rows::text FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
                       (chart_id, generation)).fetchone()
    text = None if row is None else (next(iter(row.values())) if isinstance(row, dict) else row[0])
    if text is None:
        return fetch_chart_context(conn, chart_id)         # a legacy snapshot (no copy), or none yet: the live read
    copy = json.loads(text, parse_float=Decimal)
    rows = [(e["key"]["fact_id"], e["content"]["fact_subject"], e["content"]["fact_value_num"]) for e in copy
            if e["content"].get("fact_category") == "graha_position" and e["content"].get("fact_key") == "longitude_sidereal"
            and e["content"].get("ayanamsha_id") == CANONICAL_AYANAMSHA]
    return _fill_from_rows(out, rows)


def require_complete(context: dict) -> None:
    """Loud refusal on any missing operand — the evaluator never runs on a
    partial chart (unknown is a state, never a silent default)."""
    if context["operands_missing"]:
        raise ValueError(
            f"chart context incomplete for {context['chart_id']}: "
            f"{context['operands_missing']} — refusing to evaluate on a "
            "partial chart (unknown is named, never defaulted)"
        )


__all__ = [
    "CANONICAL_AYANAMSHA",
    "NATAL_SUBJECTS",
    "fetch_chart_context",
    "fetch_chart_context_from_snapshot",
    "require_complete",
]
