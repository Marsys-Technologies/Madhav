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
from .window_sweep import SweepRecord, WindowDraft

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


def _point_delta_provider(rec_relation: str, agent: str, target: str,
                          position_at: Callable[[str, datetime], float]):
    """|Δλ| from the exact contact for a point object: the body's longitude vs the target point,
    through the aspect angle that applies (0 for a conjunction; the agent's own dṛṣṭi angles for an
    aspect — the nearest one is the one the contact is on, the angles being ≥ 30° apart)."""
    lam = float(target[len("point:"):])
    angles = (0.0,) if rec_relation == "conjunction" else drishti_angles(agent.title())
    if not angles:
        return None

    def delta(t: datetime) -> float:
        lon = position_at(agent.title(), t)
        return min(abs(_wrap180(lon + a - lam)) for a in angles)

    return delta


def _aspect_offset_provider(target: str, agent: str, position_at: Callable[[str, datetime], float]):
    """Inclusive whole-sign house offset of the target from the aspecting graha's sign at t."""
    if target.startswith("span:"):
        tgt_sign = targets.span_sign_index(target) - 1
    elif target.startswith("point:"):
        tgt_sign = int(float(target[len("point:"):]) // _SIGN_DEG) % 12
    else:
        return None

    def offset(t: datetime) -> int:
        src_sign = int(position_at(agent.title(), t) // _SIGN_DEG) % 12
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
            " r.admission_state, o.canonical_target,"
            " lower(s.x), upper(s.x), lower_inc(s.x), upper_inc(s.x)"
            " FROM public.ka_gochara_relationship_record r"
            " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id"
            " LEFT JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x) ON true"
            " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s"
            " AND r.path_id = %s AND r.rule_version = %s"
            " ORDER BY r.record_id, lower(s.x)",
            (chart_id, generation, event_class, path_id, rule_version)).fetchall()
        grouped: dict[str, dict] = {}
        for (rid, root, pid, ver, rel, kind, agent, role, adm, target,
             lo, hi, lo_inc, hi_inc) in rows:
            g = grouped.setdefault(rid, {
                "root": root, "pid": pid, "ver": ver, "rel": rel, "kind": kind, "agent": agent,
                "role": role, "adm": adm, "target": target, "supports": []})
            if lo is not None:
                if not (lo_inc and not hi_inc):
                    raise RuntimeError(
                        f"record {rid}: support interval bounds are not half-open [lo, hi) — "
                        "the sweep refuses to guess")
                g["supports"].append((lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)))
        out: list[SweepRecord] = []
        for rid, g in grouped.items():
            delta = offset = None
            if position_at is not None and g["rel"] in ("conjunction", "aspect") \
                    and g["target"].startswith("point:"):
                delta = _point_delta_provider(g["rel"], g["agent"], g["target"], position_at)
            if position_at is not None and g["rel"] == "aspect":
                offset = _aspect_offset_provider(g["target"], g["agent"], position_at)
            out.append(SweepRecord(
                record_id=rid, root_id=g["root"], path_id=g["pid"], rule_version=g["ver"],
                relation=g["rel"], object_kind=g["kind"], agent=g["agent"],
                operator_role=g["role"], admission_state=g["adm"],
                supports=tuple(g["supports"]), delta_lambda_at=delta, aspect_offset_at=offset))
        return out

    # ── write ───────────────────────────────────────────────────────────────

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
        memberships = 0
        for d in drafts:
            wid = window_uuid(chart_id=chart_id, generation=generation, event_class=event_class,
                              path_id=path_id, rule_version=rule_version, interval=d.interval)
            rng = f"[{d.interval[0].isoformat()},{d.interval[1].isoformat()})"
            self.conn.execute(
                "INSERT INTO public.ka_gochara_eval_window ("
                " window_id, chart_id, event_class, generation, path_id, rule_version, interval,"
                " peak_instant, score, evidence_for, evidence_against,"
                " outcome_valence_for_native, severity, coverage_partition_kind,"
                " coverage_partition_key, coverage_facts, null_states_used)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s::tstzrange,%s,%s,%s,%s,%s,%s,'event_class',%s,"
                " %s::jsonb,%s::text[])",
                (str(wid), chart_id, event_class, generation, path_id, rule_version, rng,
                 d.peak_instant, d.score, d.evidence_for, d.evidence_against,
                 d.outcome_valence_for_native, d.severity, event_class, coverage_facts,
                 list(d.null_states_used)))
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
        """The stored windows must equal the connected union of the stored ADMITTED, SCORED
        records' supports — recomputed here by Postgres `range_agg`, not by the sweep — and each
        window's membership must be exactly the admitted records whose support lies inside it."""
        grain = (chart_id, generation, event_class, path_id, rule_version)
        where = (" chart_id = %s AND generation = %s AND event_class = %s"
                 " AND path_id = %s AND rule_version = %s")
        expected = self.conn.execute(
            "SELECT lower(m), upper(m) FROM ("
            " SELECT unnest(range_agg(s.x)) AS m"
            " FROM public.ka_gochara_relationship_record r,"
            "      LATERAL unnest(r.temporal_support_intervals) AS s(x)"
            " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s"
            " AND r.path_id = %s AND r.rule_version = %s"
            " AND r.admission_state = 'admitted' AND r.operator_role = 'scored') q"
            " ORDER BY 1", grain).fetchall()
        stored = self.conn.execute(
            "SELECT lower(interval), upper(interval) FROM public.ka_gochara_eval_window WHERE"
            + where + " ORDER BY 1", grain).fetchall()
        if [tuple(r) for r in expected] != [tuple(r) for r in stored]:
            raise RuntimeError(
                f"window verification failed {event_class}/{path_id}: stored windows "
                f"{stored!r} != SQL connected union {expected!r}")
        bad = self.conn.execute(
            "SELECT count(*) FROM ("
            " SELECT r.record_id FROM public.ka_gochara_relationship_record r"
            " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s"
            " AND r.path_id = %s AND r.rule_version = %s"
            " AND r.admission_state = 'admitted' AND r.operator_role = 'scored'"
            " AND cardinality(r.temporal_support_intervals) > 0"
            " EXCEPT SELECT m.record_id FROM public.ka_gochara_eval_window_record m"
            " WHERE m.chart_id = %s AND m.generation = %s AND m.event_class = %s"
            " AND m.path_id = %s AND m.rule_version = %s) z", grain + grain).fetchone()[0]
        extra = self.conn.execute(
            "SELECT count(*) FROM public.ka_gochara_eval_window_record m"
            " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id"
            " WHERE m.chart_id = %s AND m.generation = %s AND m.event_class = %s"
            " AND m.path_id = %s AND m.rule_version = %s"
            " AND NOT (r.admission_state = 'admitted' AND r.operator_role = 'scored')",
            grain).fetchone()[0]
        if bad or extra:
            raise RuntimeError(
                f"window verification failed {event_class}/{path_id}: {bad} admitted record(s) "
                f"in no window, {extra} non-admitted member(s)")
        return {"windows": len(stored)}


__all__ = ["WindowStore", "window_uuid"]
