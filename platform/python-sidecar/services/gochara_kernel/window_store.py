"""Persistence for the window sweep (A5.3 design v1.5) over migration 1156.

`ka_gochara_eval_window` + `ka_gochara_eval_window_record`, written under the chart family key the
caller already holds (nothing here commits, rolls back or locks). One grain = one
(chart × generation × class × path × rule_version): delete-then-insert, REPLACING never accreting
(§N.3); a sealed generation is refused. The window's coverage snapshot is read FROM THE STORED
PARTITION (`stored_coverage_facts_json`), never hand-shaped (N10/N14).

The post-write check recomputes the connected union FROM SQL (`range_agg` over the stored admitted
records' supports) and compares it with what was written — an independent derivation that shares no
code with `window_sweep.union_components`.
"""
from __future__ import annotations

import json as _json
from datetime import datetime, timezone
from typing import Callable

from . import targets
from .convention import drishti_angles
from .evaluator import record_uuid
from .record_store import RecordStore
from .window_sweep import SweepRecord, WindowDraft, graha_title

_SIGN_DEG = 30.0


def window_uuid(*, chart_id: str, generation: str, event_class: str, path_id: str,
                rule_version: str, interval: tuple) -> object:
    """Deterministic UUIDv8 over the window's natural key (one connected union per grain)."""
    return record_uuid({
        "kind": "eval_window", "chart_id": str(chart_id), "generation": generation,
        "event_class": event_class, "path_id": path_id, "rule_version": rule_version,
        "interval": [interval[0].astimezone(timezone.utc).isoformat(),
                     interval[1].astimezone(timezone.utc).isoformat()],
    })


def _wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def _aspect_offset_provider(target: str, agent: str, position_at: Callable[[str, datetime], float]):
    """Inclusive whole-sign house offset of the target from the aspecting graha's sign at t."""
    if target.startswith("span:"):
        tgt_sign = targets.span_sign_index(target) - 1
    elif target.startswith("point:"):
        tgt_sign = int(float(target[len("point:"):]) // _SIGN_DEG) % 12
    else:
        return None

    name = graha_title(agent)

    def offset(t: datetime) -> int:
        src_sign = int(position_at(name, t) // _SIGN_DEG) % 12
        return (tgt_sign - src_sign) % 12 + 1

    return offset


class WindowStore:
    def __init__(self, conn):
        self.conn = conn
        self._records = RecordStore(conn)

    # ── read ────────────────────────────────────────────────────────────────

    def read_grain(self, *, chart_id: str, generation: str, event_class: str, path_id: str,
                   rule_version: str,
                   position_at: Callable[[str, datetime], float] | None = None) -> list[SweepRecord]:
        rows = self.conn.execute(
            "SELECT r.record_id::text, COALESCE(r.contact_id, r.object_id)::text, r.path_id,"
            " r.rule_version, r.relation, r.object_kind, r.agent, r.operator_role,"
            " r.admission_state, o.canonical_target, r.house_from_frame,"
            " lower(s.x), upper(s.x), lower_inc(s.x), upper_inc(s.x), c.t_exact, c.convention_id"
            " FROM public.ka_gochara_relationship_record r"
            " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id"
            " LEFT JOIN public.ka_gochara_contact c ON (c.chart_id, c.generation, c.contact_id)"
            "                                      = (r.chart_id, r.generation, r.contact_id)"
            " LEFT JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x) ON true"
            " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s"
            " AND r.path_id = %s AND r.rule_version = %s"
            " ORDER BY r.record_id, lower(s.x)",
            (chart_id, generation, event_class, path_id, rule_version)).fetchall()
        grouped: dict[str, dict] = {}
        for (rid, root, pid, ver, rel, kind, agent, role, adm, target, house,
             lo, hi, lo_inc, hi_inc, t_exact, conv) in rows:
            g = grouped.setdefault(rid, {
                "root": root, "pid": pid, "ver": ver, "rel": rel, "kind": kind, "agent": agent,
                "role": role, "adm": adm, "target": target, "house": house,
                "t_exact": t_exact, "conv": conv, "supports": []})
            if lo is not None:
                if not (lo_inc and not hi_inc):
                    raise RuntimeError(
                        f"record {rid}: support interval bounds are not half-open [lo, hi) — "
                        "the sweep refuses to guess")
                g["supports"].append((lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)))
        out: list[SweepRecord] = []
        crossings: dict[tuple, list[datetime]] = {}
        for rid, g in grouped.items():
            lon = offset = rays = hints = bounds = None
            if position_at is not None and g["rel"] in ("residence", "aspect", "conjunction"):
                name = graha_title(g["agent"])
                lon = (lambda t, _n=name: position_at(_n, t))
                rays = drishti_angles(name) if g["rel"] == "aspect" else ()
            if position_at is not None and g["rel"] == "aspect":
                offset = _aspect_offset_provider(g["target"], g["agent"], position_at)
                # the dṛṣṭi offset (a house-offset STEP function) changes only where the body changes
                # sign: the exact ingress instants inside the support are the state boundaries
                key = (g["agent"], g["conv"])
                if key not in crossings:
                    crossings[key] = sorted(c.t for c in self._records.fetch_crossings(g["agent"], g["conv"])) \
                        if g["conv"] else []
                bounds = (lambda lo, hi, _c=crossings[key]: [c for c in _c if lo < c < hi])
            if g["t_exact"] is not None and g["rel"] in ("conjunction", "aspect") \
                    and g["target"].startswith("point:"):
                te = g["t_exact"].astimezone(timezone.utc)
                hints = (lambda lo, hi, _te=te: [_te] if lo <= _te < hi else [])
            out.append(SweepRecord(
                record_id=rid, root_id=g["root"], path_id=g["pid"], rule_version=g["ver"],
                relation=g["rel"], object_kind=g["kind"], agent=g["agent"],
                operator_role=g["role"], admission_state=g["adm"],
                supports=tuple(g["supports"]), longitude_at=lon, aspect_rays=rays or (),
                aspect_offset_at=offset, house_from_frame=g["house"], canonical_target=g["target"],
                state_boundaries=bounds, peak_hints=hints))
        return out

    # ── write ───────────────────────────────────────────────────────────────

    def provenance_columns_available(self) -> bool:
        """Does the APPLIED schema carry the window provenance columns (1240)? Read, never assumed."""
        row = self.conn.execute(
            "SELECT count(*) FROM pg_attribute WHERE attrelid = 'public.ka_gochara_eval_window'::regclass"
            " AND attname IN ('objective', 'objective_value', 'qualification') AND NOT attisdropped").fetchone()
        return (next(iter(row.values())) if isinstance(row, dict) else row[0]) == 3

    def replace_grain_windows(self, *, chart_id: str, generation: str, event_class: str,
                              path_id: str, rule_version: str,
                              drafts: list[WindowDraft]) -> dict[str, int]:
        self._records._refuse_if_sealed(chart_id, generation,
                                        f"window grain {event_class}/{path_id}")
        grain = (chart_id, generation, event_class, path_id, rule_version)
        deleted = self.conn.execute(
            "DELETE FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s"
            " AND event_class = %s AND path_id = %s AND rule_version = %s", grain).rowcount
        if not drafts:
            return {"windows": 0, "memberships": 0, "replaced": deleted}
        coverage_facts = self._records.stored_coverage_facts_json(
            chart_id=chart_id, generation=generation, event_class=event_class)
        provenance = self.provenance_columns_available()
        memberships = 0
        for d in drafts:
            wid = window_uuid(chart_id=chart_id, generation=generation, event_class=event_class,
                              path_id=path_id, rule_version=rule_version, interval=d.interval)
            rng = f"[{d.interval[0].isoformat()},{d.interval[1].isoformat()})"
            base = (str(wid), chart_id, event_class, generation, path_id, rule_version, rng,
                    d.peak_instant, d.score, d.evidence_for, d.evidence_against,
                    d.outcome_valence_for_native, d.severity, event_class, coverage_facts,
                    list(d.null_states_used))
            if provenance:       # R8-4 (1240): the objective, its value and the structured qualification provenance
                self.conn.execute(
                    "INSERT INTO public.ka_gochara_eval_window ("
                    " window_id, chart_id, event_class, generation, path_id, rule_version, interval,"
                    " peak_instant, score, evidence_for, evidence_against,"
                    " outcome_valence_for_native, severity, coverage_partition_kind,"
                    " coverage_partition_key, coverage_facts, null_states_used,"
                    " objective, objective_value, qualification)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s::tstzrange,%s,%s,%s,%s,%s,%s,'event_class',%s,"
                    " %s::jsonb,%s::text[],%s,%s,%s::jsonb)",
                    base + (d.objective, d.objective_value, _json.dumps(d.qualification(), sort_keys=True)))
            else:
                self.conn.execute(
                    "INSERT INTO public.ka_gochara_eval_window ("
                    " window_id, chart_id, event_class, generation, path_id, rule_version, interval,"
                    " peak_instant, score, evidence_for, evidence_against,"
                    " outcome_valence_for_native, severity, coverage_partition_kind,"
                    " coverage_partition_key, coverage_facts, null_states_used)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s::tstzrange,%s,%s,%s,%s,%s,%s,'event_class',%s,"
                    " %s::jsonb,%s::text[])", base)
            for rid in d.record_ids:
                self.conn.execute(
                    "INSERT INTO public.ka_gochara_eval_window_record ("
                    " window_id, record_id, chart_id, generation, event_class, path_id,"
                    " rule_version) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (str(wid), rid, chart_id, generation, event_class, path_id, rule_version))
                memberships += 1
        return {"windows": len(drafts), "memberships": memberships, "replaced": deleted}

    # ── independent post-write check ───────────────────────────────────────

    def verify_grain(self, *, chart_id: str, generation: str, event_class: str, path_id: str,
                     rule_version: str) -> dict[str, int]:
        """The stored windows must equal the connected components of the prerequisite-satisfied
        support — recomputed here by Postgres `range_agg` over the stored ADMITTED, SCORED records'
        supports (P4: the multirange INTERSECTION of Jupiter's and Saturn's influence unions), not by
        the sweep — and each window's membership must be exactly the admitted scored records whose
        support OVERLAPS it."""
        grain = (chart_id, generation, event_class, path_id, rule_version)
        rec_where = ("r.chart_id = %s AND r.generation = %s AND r.event_class = %s"
                     " AND r.path_id = %s AND r.rule_version = %s"
                     " AND r.admission_state = 'admitted' AND r.operator_role = 'scored'")
        if path_id == "P4":
            union = ("SELECT range_agg(s.x) FILTER (WHERE r.agent = 'jupiter')"
                     " * range_agg(s.x) FILTER (WHERE r.agent = 'saturn') AS m")
        else:
            union = "SELECT range_agg(s.x) AS m"
        expected = self.conn.execute(
            "SELECT lower(c), upper(c) FROM ("
            " SELECT unnest(m) AS c FROM (" + union +
            " FROM public.ka_gochara_relationship_record r,"
            "      LATERAL unnest(r.temporal_support_intervals) AS s(x)"
            " WHERE " + rec_where + ") q) z ORDER BY 1", grain).fetchall()
        stored = self.conn.execute(
            "SELECT lower(interval), upper(interval) FROM public.ka_gochara_eval_window WHERE"
            " chart_id = %s AND generation = %s AND event_class = %s AND path_id = %s"
            " AND rule_version = %s ORDER BY 1", grain).fetchall()
        if [tuple(r) for r in expected] != [tuple(r) for r in stored]:
            raise RuntimeError(
                f"window verification failed {event_class}/{path_id}: stored windows "
                f"{stored!r} != SQL connected components {expected!r}")
        pair_where = ("w.chart_id = %s AND w.generation = %s AND w.event_class = %s"
                      " AND w.path_id = %s AND w.rule_version = %s")
        want_pairs = ("SELECT w.window_id, r.record_id FROM public.ka_gochara_eval_window w"
                      " JOIN public.ka_gochara_relationship_record r"
                      "   ON r.chart_id = w.chart_id AND r.generation = w.generation"
                      "  AND r.event_class = w.event_class AND r.path_id = w.path_id"
                      "  AND r.rule_version = w.rule_version"
                      "  AND r.admission_state = 'admitted' AND r.operator_role = 'scored'"
                      " WHERE " + pair_where +
                      " AND EXISTS (SELECT 1 FROM unnest(r.temporal_support_intervals) x"
                      "             WHERE x && w.interval)")
        have_pairs = ("SELECT m.window_id, m.record_id FROM public.ka_gochara_eval_window_record m"
                      " JOIN public.ka_gochara_eval_window w ON w.window_id = m.window_id"
                      " WHERE " + pair_where)
        missing = self.conn.execute(
            "SELECT count(*) FROM (" + want_pairs + " EXCEPT " + have_pairs + ") z",
            grain + grain).fetchone()[0]
        extra = self.conn.execute(
            "SELECT count(*) FROM (" + have_pairs + " EXCEPT " + want_pairs + ") z",
            grain + grain).fetchone()[0]
        orphans = self.conn.execute(
            "SELECT count(*) FROM public.ka_gochara_relationship_record r WHERE " + rec_where +
            " AND cardinality(r.temporal_support_intervals) > 0"
            " AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_eval_window_record m"
            "                 WHERE m.record_id = r.record_id)", grain).fetchone()[0]
        if missing or extra or orphans:
            raise RuntimeError(
                f"window verification failed {event_class}/{path_id}: {missing} overlapping "
                f"admitted record(s) not members, {extra} non-overlapping/non-admitted member(s), "
                f"{orphans} admitted record(s) in no window")
        return {"windows": len(stored)}


__all__ = ["WindowStore", "window_uuid"]
