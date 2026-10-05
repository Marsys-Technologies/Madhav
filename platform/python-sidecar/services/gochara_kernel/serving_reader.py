"""The serving reader for a SEALED governed generation (serving path work item W1).

`read_v5` is the one read-side entry point for a generation whose windows live in `ka_gochara_eval_window`. It answers
with ONE envelope (a plain, JSON-serialisable dict) and never with a bare list:

  * It serves ONLY a generation whose manifest is `published`, that has a seal row naming that manifest, and whose
    bound input vector is not a test slice. Anything else is a NAMED refusal (`refusal.code`), never an empty answer.
  * The served horizon is the manifest's own `horizon` column. No date is written in this module: a request entirely
    outside the horizon is the refusal `outside_served_horizon`; a partial overlap is clipped and says so.
  * Every numeric window field is passed through exactly as stored (NULL stays null). The reader computes no score,
    valence, peak, rank or adversity flag. The order is chronological with a stated total tie-break.
  * Completeness is never decided here: for every requested class the existing mandatory constructor
    `scope_response.coverage_response` is CALLED and its result carried, for a positive and for a no-window answer.
  * `scoring_status` needs the scored edge pinned in the manifest's input vector. Until that pin exists the status is
    null with the reason `scored_until_not_pinned`.
  * The near-miss layer is a SEPARATE array, never merged into `windows` and never counted with them; when its tables
    do not exist the layer is reported `absent` and no array is returned.

Read-only: SELECT statements only; the caller owns the connection and its transaction; nothing here commits.

Rows are read by position, so the connection may use tuple rows or dict rows.
"""
from __future__ import annotations

import json as _json
import re as _re
from datetime import datetime, timezone
from typing import Any, Sequence

from . import scope_response as sr
from .result_policy import POLICY_ALL_NULL, POLICY_QUALIFICATION, RESULT_POLICIES

ENVELOPE_SCHEMA = "gochara_v5_windows/1"

# ── refusal codes (answers, not errors) ──────────────────────────────────────────────────────────────────────────────
REFUSE_UNKNOWN_GENERATION = "unknown_generation"
REFUSE_TEST_SLICE = "test_slice_candidate"
REFUSE_NOT_PUBLISHED = "not_published"
REFUSE_NOT_SEALED = "not_sealed"
REFUSE_OUTSIDE_HORIZON = "outside_served_horizon"
REFUSE_INVALID_RANGE = "invalid_range"
REFUSE_INVALID_REQUEST = "invalid_request"
REFUSE_HORIZON_NOT_STATED = "served_horizon_not_stated"
REFUSE_POLICY_UNBOUND = "result_policy_unbound"
REFUSAL_CODES = (REFUSE_UNKNOWN_GENERATION, REFUSE_TEST_SLICE, REFUSE_NOT_PUBLISHED, REFUSE_NOT_SEALED,
                 REFUSE_OUTSIDE_HORIZON, REFUSE_INVALID_RANGE, REFUSE_INVALID_REQUEST, REFUSE_HORIZON_NOT_STATED,
                 REFUSE_POLICY_UNBOUND)

# ── vocabulary this reader states ────────────────────────────────────────────────────────────────────────────────────
RANKING_CHRONOLOGICAL = "chronological_only"
ORDERING_STATEMENT = ("windows are ordered by interval start, then interval end, then event_class, path_id, "
                      "rule_version and window_id (ascending); members by contact entry instant (records without a "
                      "contact last), then agent, relation, object_role and record_id")
SCORED_HORIZON = "scored_horizon"
STRADDLES_SCORED_EDGE = "straddles_scored_edge"
SERVED_NOT_SCORED = "served_not_scored"
SCORING_STATUSES = (SCORED_HORIZON, STRADDLES_SCORED_EDGE, SERVED_NOT_SCORED)
REASON_SCORED_UNTIL_NOT_PINNED = "scored_until_not_pinned"
REASON_SCORED_UNTIL_NOT_AN_INSTANT = "scored_until_not_an_instant"
#: the input-vector key the scored edge is read from (work item W10 adds the pin; nothing is assumed until it exists)
SCORED_UNTIL_VECTOR_KEY = "scored_until"

NUMBERS_DISCLOSURE = {
    POLICY_ALL_NULL: (
        "This generation was built under the result policy all_null_candidate/1: every window's score, evidence, "
        "objective value, severity and peak instant is null and its valence is 'unqualified'. The windows are "
        "verified contact intervals listed in chronological order; no ranking, strength, peak or favourable/adverse "
        "reading is computed or implied, and a null is not a zero."),
    POLICY_QUALIFICATION: (
        "This generation was built under the result policy window_qualification/1: numeric window fields are served "
        "exactly as stored; a null field means the window is unqualified for the reason its qualification states, "
        "never zero. This reader orders chronologically and computes no number of its own."),
}

NEAR_MISS_ABSENT = "absent"
NEAR_MISS_PRESENT = "present"
NEAR_MISS_SCHEMA_MISMATCH = "schema_mismatch"
NEAR_MISS_NOT_BUILT = "not_built_for_generation"
NEAR_MISS_SCORE_REASON = "near_miss_unscored"

#: The ONE place the near-miss storage names live (planned migration 1308; not on main). Logical name → stored name.
#: Align this mapping when the migration lands; nothing else in the reader names a near-miss table or column.
NEAR_MISS_SCHEMA = {
    "occurrence_table": "ka_gochara_near_miss",
    "object_table": "ka_gochara_near_miss_object",
    "layer_version_vector_key": "near_miss_layer_version",
    "occurrence_columns": {
        "chart_id": "chart_id", "generation": "generation", "near_miss_id": "near_miss_id", "object_id": "object_id",
        "ordinal": "ordinal", "t_in": "t_in", "t_out": "t_out", "t_closest": "t_closest",
        "closest_state": "closest_state", "clearance_deg": "clearance_deg", "orb_deg": "orb_deg",
        "proximity": "proximity", "standing": "standing", "score": "score", "junction": "junction",
        "junction_complete": "junction_complete",
    },
    "object_columns": {
        "object_id": "object_id", "body": "body", "relation": "relation", "target": "target",
        "orb_policy_id": "orb_policy_id",
    },
}

#: tables this reader cannot answer without (an absent one is a schema error for the caller, never an empty answer)
REQUIRED_TABLES = ("kala_gochara_publication", "kala_gochara_coverage", "ka_gochara_generation_seal",
                   "ka_gochara_eval_window", "ka_gochara_eval_window_record", "ka_gochara_relationship_record",
                   "ka_gochara_contact", "ka_gochara_physical_object", "ka_gochara_search_inventory")
SEAL_APPROVAL_TABLE = "ka_gochara_seal_approval"

_IDENT = _re.compile(r"^[a-z][a-z0-9_]*\Z")
for _name in ([NEAR_MISS_SCHEMA["occurrence_table"], NEAR_MISS_SCHEMA["object_table"]]
              + list(NEAR_MISS_SCHEMA["occurrence_columns"].values()) + list(NEAR_MISS_SCHEMA["object_columns"].values())
              + list(REQUIRED_TABLES) + [SEAL_APPROVAL_TABLE]):
    if not _IDENT.match(_name):                                   # the names are composed into SQL: identifiers only
        raise RuntimeError(f"serving_reader: {_name!r} is not a plain SQL identifier")


class ServingSchemaMissing(RuntimeError):
    """A table this reader needs does not exist on the connected database — a deployment fault, not an answer."""


# ── small helpers ────────────────────────────────────────────────────────────────────────────────────────────────────

def _tup(row):
    return None if row is None else (tuple(row.values()) if isinstance(row, dict) else tuple(row))


def _all(conn: Any, sql: str, params: Sequence[Any] = ()) -> list[tuple]:
    return [_tup(r) for r in conn.execute(sql, params).fetchall()]


def _first(conn: Any, sql: str, params: Sequence[Any] = ()):
    return _tup(conn.execute(sql, params).fetchone())


def _as_dict(value):
    """A json/jsonb value as Python: the driver may hand it over decoded (any JSON type) or as text."""
    return _json.loads(value) if isinstance(value, (str, bytes, bytearray)) else value


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat()


def _aware(value: Any) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _span(lo: datetime | None, hi: datetime | None) -> dict:
    return {"start": _iso(lo), "end": _iso(hi)}


def _envelope(chart_id: str, generation: str, requested: dict) -> dict:
    """Every key of the envelope, present in every answer. A value not established is null — never a default."""
    return {
        "schema": ENVELOPE_SCHEMA, "chart_id": chart_id, "generation": generation, "refusal": None,
        "manifest_id": None, "manifest_status": None, "seal": None, "served_horizon": None, "stored_scope": None,
        "requested": requested, "effective_range": None, "horizon_clipped": None,
        "result_policy": None, "numbers_disclosure": None, "ranking": None, "ordering": None,
        "scored_until": None, "scored_until_reason": None,
        "classes": None, "classes_source": None, "windows": None, "counts": None,
        "near_miss_layer": None, "near_miss_layer_version": None,
    }


def _refuse(env: dict, code: str, detail: str, **extra: Any) -> dict:
    env["refusal"] = {"code": code, "detail": detail, **extra}
    return env


# ── the manifest, the seal, the horizon ──────────────────────────────────────────────────────────────────────────────

def _require_schema(conn: Any) -> None:
    rows = _all(conn, "SELECT t.name, to_regclass('public.' || t.name) IS NOT NULL AS present FROM unnest(%s::text[]) AS t(name)"
                      " ORDER BY t.name", (list(REQUIRED_TABLES),))
    missing = [name for name, present in rows if not present]
    if missing:
        raise ServingSchemaMissing(f"serving tables absent on this database: {missing}")


def _load_manifest(conn: Any, chart_id: str, generation: str):
    # (chart_id, generation) is UNIQUE on the manifest table; the ORDER BY keeps the selection total regardless.
    return _first(conn,
                  "SELECT manifest_id::text, status, lower(horizon), upper(horizon), lower_inc(horizon),"
                  " upper_inc(horizon), input_generation_vector"
                  " FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s"
                  " ORDER BY manifest_id LIMIT 1", (chart_id, generation))


def _load_seal(conn: Any, chart_id: str, generation: str) -> dict | None:
    row = _first(conn,                                            # (chart_id, generation) is the seal's primary key
                 "SELECT manifest_id::text, sealed_at FROM public.ka_gochara_generation_seal"
                 " WHERE chart_id = %s AND generation = %s ORDER BY chart_id, generation LIMIT 1",
                 (chart_id, generation))
    if row is None:
        return None
    seal = {"chart_id": chart_id, "generation": generation, "manifest_id": row[0], "sealed_at": _iso(row[1]),
            "brief_digest": None, "brief_id": None, "brief_digest_reason": None}
    present = _first(conn, "SELECT to_regclass(%s) IS NOT NULL AS present", (f"public.{SEAL_APPROVAL_TABLE}",))[0]
    if not present:
        seal["brief_digest_reason"] = "seal_approval_table_absent"
        return seal
    receipt = _first(conn,                                        # (chart_id, generation) is the receipt's primary key
                     f"SELECT brief_digest, brief_id FROM public.{SEAL_APPROVAL_TABLE}"
                     " WHERE chart_id = %s AND generation = %s ORDER BY chart_id, generation LIMIT 1",
                     (chart_id, generation))
    if receipt is None:
        seal["brief_digest_reason"] = "no_approval_receipt"
    else:
        seal["brief_digest"], seal["brief_id"] = receipt[0], receipt[1]
    return seal


def _scored_until(vector: dict) -> tuple[datetime | None, str | None]:
    """(instant, reason): the exclusive end of the scored horizon as the manifest pins it, or null with why."""
    raw = vector.get(SCORED_UNTIL_VECTOR_KEY)
    if raw is None:
        return None, REASON_SCORED_UNTIL_NOT_PINNED
    try:
        parsed = datetime.fromisoformat(raw) if isinstance(raw, str) else None
    except ValueError:
        parsed = None
    if parsed is None or not _aware(parsed):                      # a bare date has no stated instant: do not guess one
        return None, REASON_SCORED_UNTIL_NOT_AN_INSTANT
    return parsed, None


def _scoring_status(lo: datetime, hi: datetime, edge: datetime | None, reason: str | None):
    if edge is None:
        return None, reason
    if hi <= edge:
        return SCORED_HORIZON, None
    if lo >= edge:
        return SERVED_NOT_SCORED, None
    return STRADDLES_SCORED_EDGE, None


# ── windows and members ──────────────────────────────────────────────────────────────────────────────────────────────

_WINDOW_COLUMNS = ("w.window_id::text, w.event_class, w.path_id, w.rule_version, lower(w.interval), upper(w.interval),"
                   " lower_inc(w.interval), upper_inc(w.interval), w.peak_instant, w.score, w.evidence_for,"
                   " w.evidence_against, w.outcome_valence_for_native, w.severity, w.null_states_used")
_WINDOW_ORDER = (" ORDER BY lower(w.interval), upper(w.interval), w.event_class, w.path_id, w.rule_version,"
                 " w.window_id")

_MEMBER_SQL = (
    "SELECT m.window_id::text, r.record_id::text, r.agent, r.relation, r.object_role, r.object_kind,"
    " o.canonical_target, r.affected_person, r.frame_kind, r.frame_arg, r.operator_role,"
    " r.admission_state, r.period_anchor_lord, r.period_anchor_level, r.contact_id::text,"
    " c.contact_id IS NOT NULL AS contact_row, c.occurrence_ordinal, c.t_in, c.t_exact, c.t_out,"
    " c.coverage -> 'truncated' AS contact_truncated,"
    " c.solver_method"
    " FROM public.ka_gochara_eval_window_record m"
    " JOIN public.ka_gochara_relationship_record r"
    "   ON r.record_id = m.record_id AND r.chart_id = m.chart_id AND r.generation = m.generation"
    " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id"
    " LEFT JOIN public.ka_gochara_contact c"
    "   ON c.chart_id = r.chart_id AND c.generation = r.generation AND c.contact_id = r.contact_id"
    " WHERE m.chart_id = %s AND m.generation = %s AND m.window_id = ANY(%s::uuid[])"
    " ORDER BY m.window_id, c.t_in NULLS LAST, r.agent, r.relation, r.object_role, m.record_id")


def _window_filter(event_classes, at_instant, lo, hi) -> tuple[str, list]:
    where, params = "", []
    if event_classes is not None:
        where += " AND w.event_class = ANY(%s::text[])"
        params.append(list(event_classes))
    if at_instant is not None:
        where += " AND w.interval @> %s::timestamptz"
        params.append(at_instant)
    else:
        where += " AND w.interval && tstzrange(%s::timestamptz, %s::timestamptz, '[)')"
        params += [lo, hi]
    return where, params


def _members(conn: Any, chart_id: str, generation: str, window_ids: list[str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {wid: [] for wid in window_ids}
    if not window_ids:
        return out
    for r in _all(conn, _MEMBER_SQL, (chart_id, generation, window_ids)):
        (window_id, record_id, agent, relation, object_role, object_kind, target, affected_person, frame_kind,
         frame_arg, operator_role, admission_state, anchor_lord, anchor_level, contact_id, contact_row,
         occurrence_ordinal, t_in, t_exact, t_out, truncated, solver_method) = r
        timing_reason = None
        if contact_id is None:
            timing_reason = "record_has_no_contact"               # a natal-relation record: no transit contact exists
        elif not contact_row:
            timing_reason = "contact_row_not_found"
        out[window_id].append({
            "record_id": record_id, "agent": agent, "relation": relation, "object_role": object_role,
            "object_kind": object_kind, "target": target, "affected_person": affected_person,
            "frame": {"kind": frame_kind, "arg": frame_arg},
            "operator_role": operator_role, "admission_state": admission_state,
            "period_anchor": None if anchor_lord is None else {"lord": anchor_lord, "level": anchor_level},
            "contact_id": contact_id, "occurrence_ordinal": occurrence_ordinal if contact_row else None,
            "t_in": _iso(t_in), "t_exact": _iso(t_exact), "t_out": _iso(t_out),
            "contact_truncated": _as_dict(truncated) if contact_row else None,
            "solver_method": solver_method if contact_row else None,
            "timing_reason": timing_reason,
        })
    return out


def _requested_classes(conn: Any, chart_id: str, generation: str, event_classes, matched: dict[str, int]):
    """(classes, source): the classes this answer speaks for — the caller's list, or every class the generation holds a
    search inventory for (plus any class a matched window names)."""
    if event_classes is not None:
        return sorted(set(event_classes)), "request"
    inv = [r[0] for r in _all(conn,
                              "SELECT event_class FROM public.ka_gochara_search_inventory"
                              " WHERE chart_id = %s AND generation = %s ORDER BY event_class", (chart_id, generation))]
    return sorted(set(inv) | set(matched)), "generation_search_inventory"


def _zero_window_reading(completeness: str) -> str:
    """How a class with NO window in this answer reads — named from the constructor's state, never assumed."""
    if completeness == sr.COMPLETE:
        return "searched_complete_none"
    if completeness == "class_not_searched":
        return "not_searched"
    return f"not_established:{completeness}"


# ── the near-miss layer ──────────────────────────────────────────────────────────────────────────────────────────────

def _near_miss(conn: Any, chart_id: str, generation: str, vector: dict, at_instant, lo, hi, limit) -> dict:
    """The near-miss layer as its own block. `near_miss_intervals` is present ONLY when the layer is readable."""
    occ_t, obj_t = NEAR_MISS_SCHEMA["occurrence_table"], NEAR_MISS_SCHEMA["object_table"]
    oc, ob = NEAR_MISS_SCHEMA["occurrence_columns"], NEAR_MISS_SCHEMA["object_columns"]
    version = vector.get(NEAR_MISS_SCHEMA["layer_version_vector_key"])
    out: dict[str, Any] = {"near_miss_layer": NEAR_MISS_ABSENT, "near_miss_layer_version": version}
    present = _first(conn, "SELECT to_regclass(%s) IS NOT NULL AS occurrences, to_regclass(%s) IS NOT NULL AS objects",
                     (f"public.{occ_t}", f"public.{obj_t}"))
    if not (present[0] and present[1]):
        return out
    have: dict[str, set] = {occ_t: set(), obj_t: set()}
    for table, column in _all(conn,
                              "SELECT table_name, column_name FROM information_schema.columns"
                              " WHERE table_schema = 'public' AND table_name = ANY(%s::text[])"
                              " ORDER BY table_name, column_name", ([occ_t, obj_t],)):
        have[table].add(column)
    missing = sorted([f"{occ_t}.{c}" for c in oc.values() if c not in have[occ_t]]
                     + [f"{obj_t}.{c}" for c in ob.values() if c not in have[obj_t]])
    if missing:
        out.update(near_miss_layer=NEAR_MISS_SCHEMA_MISMATCH, near_miss_layer_detail={"missing_columns": missing})
        return out
    scope = f" FROM public.{occ_t} n WHERE n.{oc['chart_id']} = %s AND n.{oc['generation']} = %s"
    if version is None:
        stored = _first(conn, "SELECT count(*)" + scope, (chart_id, generation))[0]
        if not stored:                                            # tables exist, but this generation never built the layer
            out["near_miss_layer"] = NEAR_MISS_NOT_BUILT
            return out
    where, params = "", [chart_id, generation]
    if at_instant is not None:
        where = (f" AND n.{oc['t_in']} <= %s::timestamptz"
                 f" AND (n.{oc['t_out']} IS NULL OR n.{oc['t_out']} > %s::timestamptz)")
        params += [at_instant, at_instant]
    else:
        where = (f" AND n.{oc['t_in']} < %s::timestamptz"
                 f" AND (n.{oc['t_out']} IS NULL OR n.{oc['t_out']} > %s::timestamptz)")
        params += [hi, lo]
    matched = _first(conn, "SELECT count(*)" + scope + where, params)[0]
    # every selected column gets its own alias: rows are read by position, and a dict-row connection would otherwise
    # collapse two columns that happen to share a stored name
    picked = ([f"n.{oc[k]}" + ("::text" if k in ("near_miss_id", "object_id") else "")
               for k in ("near_miss_id", "object_id", "ordinal", "t_in", "t_out", "t_closest", "closest_state",
                         "clearance_deg", "orb_deg", "proximity", "standing", "score", "junction",
                         "junction_complete")]
              + [f"o.{ob[k]}" for k in ("body", "relation", "target", "orb_policy_id")])
    select = ("SELECT " + ", ".join(f"{expr} AS c{i}" for i, expr in enumerate(picked))
              + f" FROM public.{occ_t} n JOIN public.{obj_t} o ON o.{ob['object_id']} = n.{oc['object_id']}"
              + f" WHERE n.{oc['chart_id']} = %s AND n.{oc['generation']} = %s" + where
              + f" ORDER BY n.{oc['t_in']}, n.{oc['t_out']} NULLS LAST, n.{oc['near_miss_id']}")
    if limit is not None:
        select += " LIMIT %s"
        params = params + [limit]
    rows = []
    for r in _all(conn, select, params):
        rows.append({
            "near_miss_id": r[0], "object_id": r[1], "ordinal": r[2],
            "interval": _span(r[3], r[4]), "t_closest": _iso(r[5]), "closest_state": r[6],
            "clearance_deg": r[7], "orb_deg": r[8], "proximity": r[9],
            "standing": r[10], "score": r[11], "score_reason": NEAR_MISS_SCORE_REASON if r[11] is None else None,
            "junction": _as_dict(r[12]), "junction_complete": r[13],
            "body": r[14], "relation": r[15], "target": r[16], "orb_policy_id": r[17],
        })
    out.update(near_miss_layer=NEAR_MISS_PRESENT, near_miss_intervals=rows,
               near_miss_counts={"matched": matched, "returned": len(rows), "truncated": len(rows) < matched},
               # whether the near-miss SEARCH was complete for the range is not read here (its coverage table is part
               # of the same planned migration): an empty array is "none stored", not yet "verified none"
               near_miss_completeness=None, near_miss_completeness_reason="near_miss_search_coverage_not_read")
    return out


# ── the entry point ──────────────────────────────────────────────────────────────────────────────────────────────────

def read_v5(conn: Any, chart_id: str, generation: str, *, event_classes: Sequence[str] | None = None,
            date_from: datetime | None = None, date_to: datetime | None = None, at_instant: datetime | None = None,
            limit: int | None = None) -> dict:
    """One envelope for (chart, generation) and the requested classes / range (or the instant). See the module
    docstring; the field-by-field contract is `_envelope` plus the keys added on a served answer."""
    chart_id, generation = str(chart_id), str(generation)
    classes_in = None if event_classes is None else [str(c) for c in event_classes]
    env = _envelope(chart_id, generation, {
        "event_classes": classes_in,
        "date_from": _iso(date_from) if _aware(date_from) else None,
        "date_to": _iso(date_to) if _aware(date_to) else None,
        "at_instant": _iso(at_instant) if _aware(at_instant) else None, "limit": limit})

    # (0) the request itself
    for name, value in (("date_from", date_from), ("date_to", date_to), ("at_instant", at_instant)):
        if value is not None and not _aware(value):
            return _refuse(env, REFUSE_INVALID_REQUEST, f"{name} must be a timezone-aware instant")
    if at_instant is not None and (date_from is not None or date_to is not None):
        return _refuse(env, REFUSE_INVALID_REQUEST, "at_instant and a date range are mutually exclusive")
    if classes_in is not None and not classes_in:
        return _refuse(env, REFUSE_INVALID_REQUEST, "event_classes is an empty list (omit it to ask for every class)")
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 1):
        return _refuse(env, REFUSE_INVALID_REQUEST, "limit must be a positive integer")
    if date_from is not None and date_to is not None and date_from >= date_to:
        return _refuse(env, REFUSE_INVALID_RANGE,
                       "date_from must be earlier than date_to (the range is half-open: start included, end excluded); "
                       "use at_instant for a single instant")

    # (1) the manifest, the scope word, the publication state, the seal
    _require_schema(conn)
    manifest = _load_manifest(conn, chart_id, generation)
    if manifest is None:
        return _refuse(env, REFUSE_UNKNOWN_GENERATION, f"no manifest exists for generation {generation!r} of this chart")
    manifest_id, status, h_lo, h_hi, h_lo_inc, h_hi_inc, vector = manifest
    vector = _as_dict(vector)
    vector = vector if isinstance(vector, dict) else {}
    env.update(manifest_id=manifest_id, manifest_status=status)
    scope_word = vector.get("stored_scope")
    if scope_word == "test_slice" or "test_slice" in vector:
        return _refuse(env, REFUSE_TEST_SLICE,
                       f"generation {generation!r} is a test slice (stored_scope {scope_word!r}, test_slice component "
                       f"{'present' if 'test_slice' in vector else 'absent'}): never served")
    if status != "published":
        return _refuse(env, REFUSE_NOT_PUBLISHED,
                       f"the manifest of generation {generation!r} is {status!r}, not published", manifest_status=status)
    seal = _load_seal(conn, chart_id, generation)
    if seal is None:
        return _refuse(env, REFUSE_NOT_SEALED, f"generation {generation!r} is published but has no seal row")
    if seal["manifest_id"] != manifest_id:
        return _refuse(env, REFUSE_NOT_SEALED,
                       f"the seal of generation {generation!r} names manifest {seal['manifest_id']}, not the published "
                       f"manifest {manifest_id}", seal_manifest_id=seal["manifest_id"])
    env.update(seal=seal, stored_scope=scope_word)

    # (2) the result policy — the manifest's, never a constant of this module
    policy = vector.get("result_policy")
    if policy not in RESULT_POLICIES:
        return _refuse(env, REFUSE_POLICY_UNBOUND,
                       f"the manifest vector selects result_policy {policy!r}, not one of {list(RESULT_POLICIES)}")
    env.update(result_policy=policy, numbers_disclosure=NUMBERS_DISCLOSURE[policy], ranking=RANKING_CHRONOLOGICAL,
               ordering=ORDERING_STATEMENT)

    # (3) the horizon — the manifest's
    if h_lo is None or h_hi is None or not h_lo_inc or h_hi_inc:
        return _refuse(env, REFUSE_HORIZON_NOT_STATED,
                       "the manifest's horizon is not a bounded half-open range (start included, end excluded)")
    served = _span(h_lo, h_hi)
    env["served_horizon"] = served
    if at_instant is not None:
        if at_instant < h_lo or at_instant >= h_hi:
            return _refuse(env, REFUSE_OUTSIDE_HORIZON,
                           "the requested instant lies outside the horizon this generation serves",
                           served_horizon=served, requested={"at_instant": _iso(at_instant)},
                           side="before" if at_instant < h_lo else "after")
        lo = hi = at_instant
    else:
        req_lo, req_hi = date_from, date_to
        if req_hi is not None and req_hi <= h_lo or req_lo is not None and req_lo >= h_hi:
            return _refuse(env, REFUSE_OUTSIDE_HORIZON,
                           "the requested range lies entirely outside the horizon this generation serves",
                           served_horizon=served, requested=_span(req_lo, req_hi),
                           side="before" if (req_hi is not None and req_hi <= h_lo) else "after")
        lo = h_lo if req_lo is None else max(req_lo, h_lo)
        hi = h_hi if req_hi is None else min(req_hi, h_hi)
        cut_start = req_lo is not None and req_lo < h_lo
        cut_end = req_hi is not None and req_hi > h_hi
        if cut_start or cut_end:
            env["horizon_clipped"] = {"side": "both" if cut_start and cut_end else ("start" if cut_start else "end"),
                                      "requested": _span(req_lo, req_hi), "served_horizon": served}
    env["effective_range"] = {"start": _iso(lo), "end": _iso(hi),
                              "kind": "instant" if at_instant is not None else "half_open_range"}

    # (4) the scored edge — pinned in the manifest, or null with the reason
    edge, edge_reason = _scored_until(vector)
    env.update(scored_until=_iso(edge), scored_until_reason=edge_reason)

    # (5) windows: per-class totals, then the ordered page
    where, params = _window_filter(classes_in, at_instant, lo, hi)
    base = " FROM public.ka_gochara_eval_window w WHERE w.chart_id = %s AND w.generation = %s" + where
    matched = {r[0]: r[1] for r in _all(conn, "SELECT w.event_class, count(*)" + base
                                              + " GROUP BY w.event_class ORDER BY w.event_class",
                                        [chart_id, generation] + params)}
    page_sql, page_params = "SELECT " + _WINDOW_COLUMNS + base + _WINDOW_ORDER, [chart_id, generation] + params
    if limit is not None:
        page_sql += " LIMIT %s"
        page_params = page_params + [limit]
    rows = _all(conn, page_sql, page_params)
    members = _members(conn, chart_id, generation, [r[0] for r in rows])
    windows: list[dict] = []
    for r in rows:
        status_, status_reason = _scoring_status(r[4], r[5], edge, edge_reason)
        windows.append({
            "window_id": r[0], "event_class": r[1], "path_id": r[2], "rule_version": r[3],
            "interval": {"start": _iso(r[4]), "end": _iso(r[5]),
                         "bounds": ("[" if r[6] else "(") + ("]" if r[7] else ")")},
            "peak_instant": _iso(r[8]), "score": r[9], "evidence_for": r[10], "evidence_against": r[11],
            "outcome_valence_for_native": r[12], "severity": r[13], "null_states_used": list(r[14] or []),
            "objective": None, "objective_value": None, "qualification": None,
            "qualification_reason": "not_provided_by_coverage_constructor",
            "vedha_moon_obstruction_scope": None,
            "scoring_status": status_, "scoring_status_reason": status_reason,
            "members": members[r[0]], "member_count": len(members[r[0]]),
        })

    # (6) per class: the mandatory constructor, for a positive and for a no-window answer alike
    by_id = {w["window_id"]: w for w in windows}
    class_names, class_source = _requested_classes(conn, chart_id, generation, classes_in, matched)
    classes: list[dict] = []
    for cls in class_names:
        page = [w for w in windows if w["event_class"] == cls]
        coverage = sr.coverage_response(conn, chart_id=chart_id, generation=generation, event_class=cls,
                                        windows=[{"window_id": w["window_id"]} for w in page], horizon=(lo, hi))
        coverage.pop("windows", None)                             # the windows live once, in the envelope's `windows`
        for entry in coverage.pop("window_qualification", None) or []:
            target = by_id.get((entry.get("window") or {}).get("window_id"))
            if target is not None and entry.get("qualification") is not None:
                target.update(objective=entry.get("objective"), objective_value=entry.get("objective_value"),
                              qualification=entry.get("qualification"), qualification_reason=None,
                              vedha_moon_obstruction_scope=entry.get("vedha_moon_obstruction_scope"))
        n = matched.get(cls, 0)
        classes.append({
            "event_class": cls, "windows_matched": n, "windows_returned": len(page),
            "completeness": coverage.get("completeness"),
            "zero_window_reading": _zero_window_reading(coverage.get("completeness")) if n == 0 else None,
            "coverage": coverage,
        })
    total = sum(matched.values())
    env.update(classes=classes, classes_source=class_source, windows=windows)

    # (7) the near-miss layer — its own block, its own counts
    near = _near_miss(conn, chart_id, generation, vector, at_instant, lo, hi, limit)
    near_counts = near.pop("near_miss_counts", None)
    env.update(near)
    env["counts"] = {
        "windows_matched": total, "windows_returned": len(windows), "windows_truncated": len(windows) < total,
        "near_miss_matched": None if near_counts is None else near_counts["matched"],
        "near_miss_returned": None if near_counts is None else near_counts["returned"],
        "near_miss_truncated": None if near_counts is None else near_counts["truncated"],
    }
    return env


__all__ = ["ENVELOPE_SCHEMA", "NEAR_MISS_SCHEMA", "NUMBERS_DISCLOSURE", "REFUSAL_CODES", "REQUIRED_TABLES",
           "SCORED_UNTIL_VECTOR_KEY", "SCORING_STATUSES", "ServingSchemaMissing", "read_v5"]
