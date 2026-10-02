"""The mandatory coverage-response constructor (AM-14; Codex rounds 7 [2] and 8 R8-5).

Every answer the serving layer gives about this generation's stored tier — a POSITIVE answer (windows found) AND a
NO-WINDOW answer — is built here. Two things are kept apart, always (R8-5):

  * SCOPE — what the stored tier holds. Read BACK from the BOUND manifest vector (`stored_scope`), never a literal and
    never inferred. A manifest without the scope REFUSES any completeness claim (`completeness = "refused"`).
  * COMPLETENESS — whether the REQUESTED class and horizon were searched, finalised and verified. A scope declaration
    alone NEVER proves completion. `complete_within_scope` is returned only when every one of these holds, each read
    from the database for the requested (chart, generation, class, horizon):

        the manifest is PUBLISHED and its bound input vector equals the search snapshot's (no stale binding);
        the class has a FINALISED inventory whose horizon COVERS the requested horizon and whose input identity is
        the snapshot's;
        the inventory ledger holds no `missing_inputs` interval;
        the inventory was independently VERIFIED (a verification row equal to the stored digest);
        the class's event-class coverage partition completed the requested horizon;
        every included P1–P4 window grain carries a VERIFIED, current, input-bound window verification (1240).

    Anything else returns its own named non-complete state with the reasons (`completeness_reasons`) — `not_published`,
    `class_not_searched`, `stale_binding`, `incomplete_horizon`, `incomplete_inventory`, `unverified`,
    `evidence_unavailable` — never "complete". Each returned window also carries its persisted qualification
    provenance (1240) and, for P2, the vedha Moon-obstruction scope; an on-demand (Moon) answer never changes the stored
    scope — it is listed beside it.

Serving code must call `coverage_response`; the stored tier's scope is `stored_non_moon`: the Moon is the on-demand
tier (AM-4), excluded from this generation's stored contacts, records and windows.
"""
from __future__ import annotations

import json as _json
from datetime import datetime
from typing import Any, Sequence

SCOPE_STATEMENT = {
    "stored_non_moon": "the stored tier holds no Moon-agent contact, record or window; the Moon is served "
                       "on demand (moon_on_demand coverage), and Moon-resolved period portions are "
                       "accounted as excluded from the stored tier",
}

COMPLETE = "complete_within_scope"
NON_COMPLETE_STATES = ("refused", "not_published", "class_not_searched", "stale_binding", "incomplete_horizon",
                       "incomplete_inventory", "unverified", "evidence_unavailable")
#: the cited vedha scope: a stored state can prove `active` but never fully `inactive` — the Moon is on demand
VEDHA_MOON_SCOPE = "excluding_on_demand_moon_obstruction"


class ScopeMissing(RuntimeError):
    """The bound manifest does not state a stored scope."""


def _one(row):
    return None if row is None else (tuple(row.values()) if isinstance(row, dict) else tuple(row))


def _manifest(conn: Any, chart_id: str, generation: str):
    return _one(conn.execute(
        "SELECT input_generation_vector, status, horizon FROM public.kala_gochara_publication"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone())


def bound_stored_scope(conn: Any, chart_id: str, generation: str) -> str:
    """The `stored_scope` of the generation's BOUND manifest vector; ScopeMissing if there is no manifest,
    no scope, or a scope this build does not know how to state."""
    row = _manifest(conn, chart_id, generation)
    if row is None:
        raise ScopeMissing(f"generation {generation} has no bound manifest")
    vector = row[0] if isinstance(row[0], dict) else _json.loads(row[0])
    scope = vector.get("stored_scope")
    if not scope:
        raise ScopeMissing(f"the manifest vector of generation {generation} states no stored_scope")
    if scope not in SCOPE_STATEMENT:
        raise ScopeMissing(f"stored_scope {scope!r} is not a scope this build can state")
    return scope


def on_demand_partitions(conn: Any, chart_id: str, generation: str) -> list[str]:
    return [(r["partition_key"] if isinstance(r, dict) else r[0]) for r in conn.execute(
        "SELECT partition_key FROM public.kala_gochara_coverage WHERE chart_id = %s AND generation = %s"
        " AND partition_kind = 'moon_on_demand' ORDER BY partition_key", (chart_id, generation)).fetchall()]


def _as_dict(value):
    return value if isinstance(value, dict) or value is None else _json.loads(value)


def _covers(outer, lo: datetime, hi: datetime) -> bool:
    """A half-open `[a, b)` range covers `[lo, hi)`."""
    return outer is not None and outer.lower <= lo and hi <= outer.upper


def _completeness(conn: Any, chart_id: str, generation: str, event_class: str,
                  horizon: tuple[datetime, datetime] | None, manifest) -> tuple[str, list[dict], dict]:
    """(state, reasons, basis): derived from the requested class/horizon's own coverage, inventory and verification."""
    reasons: list[dict] = []
    basis: dict[str, Any] = {}

    def fail(state, code, detail):
        reasons.append({"code": code, "detail": detail})
        return state, reasons, basis

    if manifest[1] != "published":
        return fail("not_published", "manifest_not_published",
                    f"the manifest of generation {generation} is {manifest[1]!r}, not published")
    try:
        snap = _one(conn.execute(
            "SELECT input_generation_vector, input_digest FROM public.ka_gochara_search_input_snapshot"
            " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone())
    except Exception as exc:  # noqa: BLE001 — the search-inventory tables are not applied: say so, never "complete"
        if type(exc).__name__ != "UndefinedTable":
            raise
        return fail("evidence_unavailable", "search_inventory_not_applied", "no search inventory exists on this schema")
    if snap is None:
        return fail("stale_binding", "no_search_snapshot", f"generation {generation} has no search-input snapshot")
    if _as_dict(snap[0]) != _as_dict(manifest[0]):
        return fail("stale_binding", "manifest_vector_differs_from_snapshot",
                    "the manifest's bound input vector is not the one the search snapshot was taken under")
    inv = _one(conn.execute(
        "SELECT horizon, input_digest, inventory_digest FROM public.ka_gochara_search_inventory"
        " WHERE chart_id = %s AND generation = %s AND event_class = %s",
        (chart_id, generation, event_class)).fetchone())
    if inv is None:
        return fail("class_not_searched", "no_inventory_for_class",
                    f"event class {event_class!r} has no search inventory in generation {generation}")
    if inv[2] is None:
        return fail("incomplete_inventory", "inventory_not_finalised", "the class inventory is not finalised")
    if inv[1] != snap[1]:
        return fail("stale_binding", "inventory_bound_to_another_snapshot",
                    "the class inventory was computed under a different search-input identity")
    basis["inventory_digest"] = inv[2]
    lo, hi = horizon if horizon is not None else (inv[0].lower, inv[0].upper)
    if not _covers(inv[0], lo, hi):
        return fail("incomplete_horizon", "requested_horizon_not_covered",
                    f"the inventory horizon {inv[0]} does not cover the requested [{lo.isoformat()}, {hi.isoformat()})")
    cov = _one(conn.execute(
        "SELECT completed_horizon FROM public.kala_gochara_coverage WHERE chart_id = %s AND generation = %s"
        " AND partition_kind = 'event_class' AND partition_key = %s", (chart_id, generation, event_class)).fetchone())
    if cov is None or not _covers(cov[0], lo, hi):
        return fail("incomplete_horizon", "coverage_partition_does_not_cover_the_horizon",
                    "the class's event-class coverage partition is absent or did not complete the requested horizon")
    missing = _one(conn.execute(
        "SELECT count(*) FROM public.ka_gochara_search_interval WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND state = 'missing_inputs'", (chart_id, generation, event_class)).fetchone())[0]
    if missing:
        return fail("incomplete_inventory", "missing_inputs_present",
                    f"{missing} search interval(s) of the class are missing inputs — the search was not run there")
    verified = _one(conn.execute(
        "SELECT count(*) FROM public.ka_gochara_search_inventory_verification WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND rederived_inventory_digest = %s", (chart_id, generation, event_class, inv[2])
    ).fetchone())[0]
    if not verified:
        return fail("unverified", "inventory_not_independently_verified",
                    "no independent verification equals the stored inventory digest")
    wv = _one(conn.execute(
        "SELECT to_regprocedure('public.ka_gochara_window_verification_violations(uuid,text)') IS NOT NULL").fetchone())[0]
    if not wv:
        return fail("evidence_unavailable", "window_verification_not_applied",
                    "migration 1240 is not applied: window verification cannot be established")
    violations = conn.execute(
        "SELECT path_id, violation FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)"
        " WHERE event_class = %s", (chart_id, generation, event_class)).fetchall()
    if violations:
        for v in violations:
            v = tuple(v.values()) if isinstance(v, dict) else tuple(v)
            reasons.append({"code": v[1], "detail": f"window grain {v[0]}"})
        return "unverified", reasons, basis
    basis["window_verification"] = "VERIFIED"
    return COMPLETE, reasons, basis


def _window_qualification(conn: Any, chart_id: str, generation: str, windows: Sequence[Any]) -> list[dict]:
    """Each returned window with its PERSISTED qualification provenance (1240) and, for P2, the vedha Moon-obstruction
    scope. A window without an id is passed through with `qualification: None` (never invented)."""
    out = []
    for w in windows:
        wid = w.get("window_id") if isinstance(w, dict) else getattr(w, "window_id", None)
        entry = {"window": w, "qualification": None, "objective": None, "vedha_moon_obstruction_scope": None}
        if wid is not None:
            try:
                row = _one(conn.execute(
                    "SELECT objective, objective_value, qualification, path_id FROM public.ka_gochara_eval_window"
                    " WHERE chart_id = %s AND generation = %s AND window_id = %s", (chart_id, generation, str(wid))
                ).fetchone())
            except Exception as exc:  # noqa: BLE001 — pre-1240 schema: no provenance columns
                if type(exc).__name__ not in ("UndefinedColumn", "UndefinedTable"):
                    raise
                row = None
            if row is not None:
                entry.update(objective=row[0], objective_value=row[1], qualification=_as_dict(row[2]))
                if row[3] == "P2" and row[1] is not None:       # a numeric P2 window carries the cited vedha scope
                    entry["vedha_moon_obstruction_scope"] = VEDHA_MOON_SCOPE
        out.append(entry)
    return out


def named_limits() -> list[dict]:
    """The limits every completeness claim carries — NAMED, never silence (Codex round 9, R9-3/R9-9): what the contact
    certification guarantees and its assumption, and how a reconstructed boundary is compared with a stored one."""
    from . import contact_certify, contact_reconstruct
    return [
        {"name": "contact_geometry_guarantee", "assumption": contact_reconstruct.GUARANTEE_ASSUMPTION,
         "statement": contact_reconstruct.NAMED_LIMIT},
        {"name": "boundary_tolerance", "assumption": "solver_angular_accuracy_derived_tolerance",
         "statement": contact_certify.BOUNDARY_TOLERANCE_STATEMENT},
    ]


def coverage_response(conn: Any, *, chart_id: str, generation: str, event_class: str,
                      windows: Sequence[Any], horizon: tuple[datetime, datetime] | None = None) -> dict:
    """The response for one (chart, generation, class[, requested horizon]): windows (possibly none) with their
    qualification, the scope, and the COMPLETENESS state — derived from the class/horizon's own coverage, inventory
    and verification, separately from the scope (a scope declaration alone never proves completion)."""
    out: dict[str, Any] = {
        "chart_id": chart_id, "generation": generation, "event_class": event_class,
        "windows": list(windows), "window_count": len(windows),
        "on_demand_answered": on_demand_partitions(conn, chart_id, generation),
    }
    manifest = _manifest(conn, chart_id, generation)
    try:
        scope = bound_stored_scope(conn, chart_id, generation)
    except ScopeMissing as exc:
        out.update(stored_scope=None, completeness="refused", refusal="stored_scope_missing",
                   refusal_detail=str(exc), completeness_reasons=[{"code": "stored_scope_missing",
                                                                   "detail": str(exc)}])
        return out
    state, reasons, basis = _completeness(conn, chart_id, generation, event_class, horizon, manifest)
    out.update(stored_scope=scope, scope_statement=SCOPE_STATEMENT[scope], completeness=state,
               completeness_reasons=reasons, completeness_basis=basis,
               named_limits=named_limits(),
               window_qualification=_window_qualification(conn, chart_id, generation, windows))
    return out


__all__ = ["COMPLETE", "NON_COMPLETE_STATES", "SCOPE_STATEMENT", "ScopeMissing", "VEDHA_MOON_SCOPE",
           "bound_stored_scope", "coverage_response", "named_limits", "on_demand_partitions"]
