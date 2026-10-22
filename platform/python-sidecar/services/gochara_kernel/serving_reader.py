"""The serving reader for a SEALED governed generation (serving path work item W1).

`read_v5` is the one read-side entry point for a generation whose windows live in `ka_gochara_eval_window`. It answers
with ONE envelope (a plain, JSON-serialisable dict) and never with a bare list:

  * It serves ONLY a generation whose manifest is `published`, that has a seal row naming that manifest, and whose
    bound input vector is not a test slice. Anything else is a NAMED refusal (`refusal.code`), never an empty answer.
  * The served horizon is the manifest's own `horizon` column. No date is written in this module: a request entirely
    outside the horizon is the refusal `outside_served_horizon`; a partial overlap is clipped and says so.
  * Every numeric window field is passed through exactly as stored (NULL stays null). The reader computes no score,
    valence, peak, rank or adversity flag. The order is chronological with a stated total tie-break.
    ONE exception, and it is the seal's, not the reader's: a window the verifier DEMOTED (R-6: its solver check was inconclusive; the generation's PASSED
    numerical-window attestation lists it by `window_id` and reason) is served as the named blank it was sealed as — every numeric field null, the valence
    `unqualified`, `unqualified_reason` the attested reason, `demoted_at_seal` true — whatever number the stored row still carries. This is applied in ONE place, to the
    finished window list (`_serve_demoted_as_blank`), after both the window page and the constructor's per-window qualification (which carries `objective_value` and the
    builder's `solver_certificate`) have been merged in, so no path can serve the number round the other.
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
from .numerical_window_gate import ATTESTATION_KEY as GATE_ATTESTATION_KEY
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
                 REFUSE_POLICY_UNBOUND, 'stored_window_bounds_incompatible', 'class_evidence_unavailable',
                 'stored_scope_missing', 'coverage_refused', 'authority_not_published')

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
#: the input-vector key the scored edge is read from (the candidate manifest pins it: `input_vector.scored_until_instant`, re-derived by the verifier; a manifest without it reads null)
SCORED_UNTIL_VECTOR_KEY = "scored_until"

NUMBERS_DISCLOSURE = {
    POLICY_ALL_NULL: (
        "This generation was built under the result policy all_null_candidate/1: every window's score, evidence, "
        "objective value, severity and peak instant is null and its valence is 'unqualified'. The windows are "
        "stored contact intervals listed in chronological order; no ranking, strength, peak or favourable/adverse "
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

#: Compatibility contract retained from the pinned W1 oracle. The builder migration
#: is not on this base; incompatible storage is unavailable rather than guessed.
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

# Information-schema spellings of the pinned fixture contract. No coercion of incompatible data.
NEAR_MISS_COLUMN_TYPES = {
    NEAR_MISS_SCHEMA['occurrence_table']: dict(zip(NEAR_MISS_SCHEMA['occurrence_columns'].values(),
        ('uuid', 'text', 'uuid', 'uuid', 'integer', 'timestamp with time zone', 'timestamp with time zone',
         'timestamp with time zone', 'text', 'double precision', 'double precision', 'double precision',
         'text', 'real', 'jsonb', 'boolean'))),
    NEAR_MISS_SCHEMA['object_table']: dict(zip(NEAR_MISS_SCHEMA['object_columns'].values(),
        ('uuid', 'text', 'text', 'text', 'text'))),
}

#: tables this reader cannot answer without (an absent one is a schema error for the caller, never an empty answer)
REQUIRED_TABLES = ("kala_gochara_publication", "kala_gochara_coverage", "ka_gochara_generation_seal",
                   "ka_gochara_eval_window", "ka_gochara_eval_window_record", "ka_gochara_relationship_record",
                   "ka_gochara_contact", "ka_gochara_physical_object", "ka_gochara_search_inventory", "ka_gochara_eval_window_verification")
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
                   " lower_inc(w.interval), upper_inc(w.interval), w.peak_instant, w.score::float8,"
                   " w.evidence_for::float8, w.evidence_against::float8, w.outcome_valence_for_native, w.severity::float8,"
                   " w.null_states_used")
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

def _near_miss_contract_problem(conn, occ_t, obj_t, oc, ob, chart_id, generation):
    actual = {(t, c): dtype for t, c, dtype in _all(conn,
        "SELECT table_name, column_name, data_type FROM information_schema.columns"
        " WHERE table_schema = 'public' AND table_name = ANY(%s::text[])"
        " ORDER BY table_name, column_name", ([occ_t, obj_t],))}
    bad_types = [f'{t}.{c}' for t, cols in NEAR_MISS_COLUMN_TYPES.items()
                 for c, dtype in cols.items() if actual.get((t, c)) != dtype]
    if bad_types:
        return {'column_types': sorted(bad_types)}
    # Every object and occurrence identity must be unique; duplicate joins must never multiply rows.
    for table, column in ((occ_t, oc['near_miss_id']), (obj_t, ob['object_id'])):
        unique = _first(conn,
            "SELECT EXISTS (SELECT 1 FROM pg_index i JOIN pg_attribute a"
            " ON a.attrelid = i.indrelid AND a.attnum = i.indkey[0]"
            " WHERE i.indrelid = to_regclass(%s) AND i.indisunique AND i.indisvalid"
            " AND i.indpred IS NULL AND i.indexprs IS NULL AND i.indnkeyatts = 1 AND a.attname = %s)",
            (f'public.{table}', column))[0]
        if not unique:
            return {'keys': [f'{table}.{column}']}
    invalid = _first(conn,
        f"SELECT EXISTS (SELECT 1 FROM public.{occ_t} n LEFT JOIN public.{obj_t} o"
        f" ON o.{ob['object_id']} = n.{oc['object_id']}"
        f" WHERE n.{oc['chart_id']} = %s AND n.{oc['generation']} = %s"
        f" AND (o.{ob['object_id']} IS NULL OR n.{oc['standing']} IS DISTINCT FROM 'near_miss'"
        f" OR n.{oc['score']} IS NOT NULL OR n.{oc['t_in']} IS NULL"
        f" OR n.{oc['t_out']} <= n.{oc['t_in']}))", (chart_id, generation))[0]
    if invalid:
        return {'rows': 'orphan_object_or_incompatible_standing_score_interval'}
    return None


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
    problem = _near_miss_contract_problem(conn, occ_t, obj_t, oc, ob, chart_id, generation)
    if problem:
        out.update(near_miss_layer=NEAR_MISS_SCHEMA_MISMATCH, near_miss_layer_detail=problem)
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



def _stored_bounds_problem(conn, chart_id, generation):
    return bool(_first(conn,
        "SELECT EXISTS (SELECT 1 FROM public.ka_gochara_eval_window"
        " WHERE chart_id = %s AND generation = %s"
        " AND (NOT lower_inc(interval) OR upper_inc(interval)))", (chart_id, generation))[0])


def _admit(conn, env):
    """Bind publication, seal, policy and finite half-open horizon before reading data."""
    chart_id, generation = env['chart_id'], env['generation']
    _require_schema(conn)
    manifest = _load_manifest(conn, chart_id, generation)
    if manifest is None:
        _refuse(env, REFUSE_UNKNOWN_GENERATION, f'no manifest for generation {generation!r}')
        return None
    mid, status, lo, hi, lower_inc, upper_inc, raw_vector = manifest
    vector = _as_dict(raw_vector)
    vector = vector if isinstance(vector, dict) else {}
    env.update(manifest_id=mid, manifest_status=status)
    if vector.get('stored_scope') == 'test_slice' or 'test_slice' in vector:
        _refuse(env, REFUSE_TEST_SLICE, 'test slices are never served')
        return None
    if status != 'published':
        _refuse(env, REFUSE_NOT_PUBLISHED, f'manifest status is {status!r}', manifest_status=status)
        return None
    seal = _load_seal(conn, chart_id, generation)
    if seal is None or seal['manifest_id'] != mid:
        _refuse(env, REFUSE_NOT_SEALED, 'no seal bound to the published manifest',
                seal_manifest_id=None if seal is None else seal['manifest_id'])
        return None
    env.update(seal=seal, stored_scope=vector.get('stored_scope'))
    policy = vector.get('result_policy')
    if policy not in RESULT_POLICIES:
        _refuse(env, REFUSE_POLICY_UNBOUND, f'unknown result policy {policy!r}')
        return None
    env.update(result_policy=policy, numbers_disclosure=NUMBERS_DISCLOSURE[policy],
               ranking=RANKING_CHRONOLOGICAL, ordering=ORDERING_STATEMENT)
    if not _aware(lo) or not _aware(hi) or lo >= hi or not lower_inc or upper_inc:
        _refuse(env, REFUSE_HORIZON_NOT_STATED, 'manifest horizon must be finite, nonempty and half-open')
        return None
    env['served_horizon'] = _span(lo, hi)
    return vector, lo, hi


def _effective_horizon(env, start, end, instant, horizon_lo, horizon_hi):
    """Intersect the requested range with the manifest, with explicit clipping."""
    if instant is not None:
        outside = instant < horizon_lo or instant >= horizon_hi
        side = 'before' if instant < horizon_lo else 'after'
        requested = {'at_instant': _iso(instant)}
        lo = hi = instant
    else:
        outside = (end is not None and end <= horizon_lo) or (start is not None and start >= horizon_hi)
        side = 'before' if end is not None and end <= horizon_lo else 'after'
        requested = _span(start, end)
        lo = horizon_lo if start is None else max(start, horizon_lo)
        hi = horizon_hi if end is None else min(end, horizon_hi)
        cut_start = start is not None and start < horizon_lo
        cut_end = end is not None and end > horizon_hi
        if cut_start or cut_end:
            env['horizon_clipped'] = {
                'side': 'both' if cut_start and cut_end else ('start' if cut_start else 'end'),
                'requested': requested, 'served_horizon': env['served_horizon']}
    if outside:
        _refuse(env, REFUSE_OUTSIDE_HORIZON, 'request is outside the served horizon',
                side=side, requested=requested, served_horizon=env['served_horizon'])
        return None
    env['effective_range'] = {**_span(lo, hi), 'kind': 'instant' if instant is not None else 'half_open_range'}
    return lo, hi


def _window_page(conn, chart_id, generation, classes, instant, lo, hi, limit, edge, edge_reason):
    where, args = _window_filter(classes, instant, lo, hi)
    base = ' FROM public.ka_gochara_eval_window w WHERE w.chart_id = %s AND w.generation = %s' + where
    params = [chart_id, generation] + args
    counts = dict(_all(conn, 'SELECT w.event_class, count(*)' + base +
                       ' GROUP BY w.event_class ORDER BY w.event_class', params))
    query = 'SELECT ' + _WINDOW_COLUMNS + base + _WINDOW_ORDER
    rows = _all(conn, query + (' LIMIT %s' if limit is not None else ''),
                params + ([limit] if limit is not None else []))
    members = _members(conn, chart_id, generation, [r[0] for r in rows])
    windows = []
    for r in rows:
        scoring, reason = _scoring_status(r[4], r[5], edge, edge_reason)
        windows.append({
            'window_id': r[0], 'event_class': r[1], 'path_id': r[2], 'rule_version': r[3],
            'interval': {**_span(r[4], r[5]), 'bounds': '[)'},
            'peak_instant': _iso(r[8]), 'score': r[9], 'evidence_for': r[10], 'evidence_against': r[11],
            'outcome_valence_for_native': r[12], 'severity': r[13], 'null_states_used': list(r[14] or []),
            'objective': None, 'objective_value': None, 'qualification': None,
            'qualification_reason': 'not_provided_by_coverage_constructor', 'vedha_moon_obstruction_scope': None,
            'unqualified_reason': None, 'demoted_at_seal': False,
            'scoring_status': scoring, 'scoring_status_reason': reason,
            'members': members[r[0]], 'member_count': len(members[r[0]]),
        })
    return windows, counts


def _demoted_windows(conn, chart_id: str, generation: str, policy: str) -> dict[str, str]:
    """{window_id: reason} of the windows the generation's VERIFIED grains attest as DEMOTED to a named blank (R-6). Only the numerical policy has any; a malformed entry is
    ignored here (the numerical-window gate refuses to seal one), never guessed."""
    if policy != POLICY_QUALIFICATION:
        return {}
    out: dict[str, str] = {}
    for (identity,) in _all(conn, "SELECT runner_identity FROM public.ka_gochara_eval_window_verification WHERE chart_id = %s AND generation = %s"
                                  " AND status = 'VERIFIED' AND policy_version = %s ORDER BY event_class, path_id, rule_version",
                            (chart_id, generation, POLICY_QUALIFICATION)):
        identity = _as_dict(identity)
        attestation = identity.get(GATE_ATTESTATION_KEY) if isinstance(identity, dict) else None
        for entry in (attestation.get("demoted_windows") if isinstance(attestation, dict) else None) or ():
            if isinstance(entry, dict) and isinstance(entry.get("window_id"), str) and isinstance(entry.get("reason"), str) and entry["reason"]:
                out[entry["window_id"]] = entry["reason"]
    return out


def _serve_demoted_as_blank(windows: list, demoted: dict[str, str]) -> None:
    """Serve each listed window as its named blank, in place: no number survives — not the page's columns, not the constructor's `objective_value`, not the builder's
    `solver_certificate` (its value and instant are the unverified number)."""
    for w in windows:
        reason = demoted.get(w['window_id'])
        if reason is None:
            continue
        w.update(peak_instant=None, score=None, evidence_for=None, evidence_against=None, severity=None, objective_value=None,
                 outcome_valence_for_native='unqualified', unqualified_reason=reason, demoted_at_seal=True)
        q = w.get('qualification')
        if isinstance(q, dict):
            w['qualification'] = {**{k: v for k, v in q.items() if k != 'solver_certificate'}, 'unqualified_reason': reason}


def _class_coverage(conn, chart_id, generation, names, windows, counts, horizon):
    by_id = {w['window_id']: w for w in windows}
    classes = []
    for name in names:
        page = [w for w in windows if w['event_class'] == name]
        coverage = dict(sr.coverage_response(conn, chart_id=chart_id, generation=generation, event_class=name,
                         windows=[{'window_id': w['window_id']} for w in page], horizon=horizon, sealed_read=True))
        coverage.pop('windows', None)
        for entry in coverage.pop('window_qualification', None) or []:
            target = by_id.get((entry.get('window') or {}).get('window_id'))
            if target is not None and entry.get('qualification') is not None:
                target.update(objective=entry.get('objective'), objective_value=entry.get('objective_value'),
                              qualification=entry['qualification'], qualification_reason=None,
                              vedha_moon_obstruction_scope=entry.get('vedha_moon_obstruction_scope'),
                              unqualified_reason=entry['qualification'].get('unqualified_reason')
                              if isinstance(entry['qualification'], dict) else None)
        total = counts.get(name, 0)
        classes.append({'event_class': name, 'windows_matched': total, 'windows_returned': len(page),
                        'completeness': coverage.get('completeness'), 'coverage': coverage,
                        'zero_window_reading': _zero_window_reading(coverage.get('completeness')) if total == 0 else None})
    return classes


def read_v5(conn: Any, chart_id: str, generation: str, *, event_classes: Sequence[str] | None = None,
            date_from: datetime | None = None, date_to: datetime | None = None,
            at_instant: datetime | None = None, limit: int | None = None) -> dict:
    """Read a sealed generation on the caller's snapshot, preserving stored values."""
    chart_id, generation = str(chart_id), str(generation)
    names_in = None if event_classes is None else [str(c) for c in event_classes]
    env = _envelope(chart_id, generation, {'event_classes': names_in, 'limit': limit,
        'date_from': _iso(date_from) if _aware(date_from) else None,
        'date_to': _iso(date_to) if _aware(date_to) else None,
        'at_instant': _iso(at_instant) if _aware(at_instant) else None})
    if any(t is not None and not _aware(t) for t in (date_from, date_to, at_instant)):
        return _refuse(env, REFUSE_INVALID_REQUEST, 'all instants must carry a timezone offset')
    if at_instant is not None and (date_from is not None or date_to is not None):
        return _refuse(env, REFUSE_INVALID_REQUEST, 'instant and range are mutually exclusive')
    if names_in == [] or limit is not None and (type(limit) is not int or limit <= 0):
        return _refuse(env, REFUSE_INVALID_REQUEST, 'classes must be nonempty and limit must be a positive integer')
    if date_from is not None and date_to is not None and date_from >= date_to:
        return _refuse(env, REFUSE_INVALID_RANGE, 'date_from must precede date_to')
    admitted = _admit(conn, env)
    if admitted is None:
        return env
    vector, h_lo, h_hi = admitted
    effective = _effective_horizon(env, date_from, date_to, at_instant, h_lo, h_hi)
    if effective is None:
        return env
    lo, hi = effective
    if _stored_bounds_problem(conn, chart_id, generation):
        return _refuse(env, 'stored_window_bounds_incompatible', 'stored windows require start-inclusive, end-exclusive bounds')
    edge, reason = _scored_until(vector)
    env.update(scored_until=_iso(edge), scored_until_reason=reason)
    windows, counts = _window_page(conn, chart_id, generation, names_in, at_instant, lo, hi, limit, edge, reason)
    names, source = _requested_classes(conn, chart_id, generation, names_in, counts)
    if not names:
        return _refuse(env, 'class_evidence_unavailable', 'no search inventory or matching class evidence for this generation')
    classes = _class_coverage(conn, chart_id, generation, names, windows, counts, (lo, hi))
    _serve_demoted_as_blank(windows, _demoted_windows(conn, chart_id, generation, env['result_policy']))
    refusals = [c for c in classes if c['coverage'].get('refusal') or c['completeness'] == 'refused']
    if refusals:
        return _refuse(env, refusals[0]['coverage'].get('refusal') or 'coverage_refused',
                       'mandatory coverage constructor refused the requested scope', class_details=classes)
    env.update(windows=windows, classes=classes, classes_source=source)
    near = _near_miss(conn, chart_id, generation, vector, at_instant, lo, hi, limit)
    near_counts = near.pop('near_miss_counts', None)
    env.update(near)
    total = sum(counts.values())
    env['counts'] = {'windows_matched': total, 'windows_returned': len(windows), 'windows_truncated': len(windows) < total,
                     'near_miss_matched': None if near_counts is None else near_counts['matched'],
                     'near_miss_returned': None if near_counts is None else near_counts['returned'],
                     'near_miss_truncated': None if near_counts is None else near_counts['truncated']}
    return env


def read_authoritative(conn: Any, chart_id: str, *, legacy_reader, **request):
    """Dispatch only from the stored authority; return the legacy reader's bytes unchanged.

    The caller supplies its existing legacy reader and owns the read-only snapshot.
    Explicit generation reads use read_v5; an absent authority never invents a head.
    """
    row = _first(conn, 'SELECT authoritative_generation FROM public.kala_gochara_authority'
                      ' WHERE chart_id = %s ORDER BY chart_id LIMIT 1', (str(chart_id),))
    if row is None:
        requested = {key: (_iso(value) if _aware(value) else None) if isinstance(value, datetime) else value
                     for key, value in request.items()}
        return _refuse(_envelope(str(chart_id), None, requested), 'authority_not_published',
                       'no authority is recorded for this chart')
    generation = row[0]
    if _re.fullmatch(r'([5-9]|[1-9][0-9]+)\.[0-9]+', generation):
        return read_v5(conn, str(chart_id), generation, **request)
    return legacy_reader(conn, str(chart_id), generation, **request)


__all__ = ['ENVELOPE_SCHEMA', 'NEAR_MISS_SCHEMA', 'NUMBERS_DISCLOSURE', 'REFUSAL_CODES',
           'REQUIRED_TABLES', 'SCORED_UNTIL_VECTOR_KEY', 'SCORING_STATUSES',
           'ServingSchemaMissing', 'read_v5', 'read_authoritative']
