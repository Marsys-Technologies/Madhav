"""The admitted-day-share report read from a STORED generation (ND-H-20261005 cond. 4; FB-50).

READ-ONLY: two SELECTs over the v5 window tables of ONE chart and ONE generation
(`ka_gochara_eval_window`, `ka_gochara_eval_window_record` → `ka_gochara_relationship_record`) and one over
the coverage partitions for the horizon. No write, no lock, no commit, no rollback, no close: the connection
is the caller's. No outcome and no life event is read — admitted windows only.

What is read:
  * WINDOW spans — every stored window of the generation: its class, path, rule_version and interval.
  * MEMBER spans — per member record of a window: its agent, whether its object_role is `karaka` (a K-B
    luminary target), and each of its support intervals INTERSECTED with the window's interval. These give
    the P3 fast/slow split and the K-B contribution (a window is a union over agents).
  * the HORIZON — the generation's one `completed_horizon` across its event_class coverage partitions; two
    different horizons refuse (never a silent pick).

A stored interval is half-open [lo, hi). A calendar day is counted when ANY instant of it is admitted; days
are taken in `tz` (default IST, +05:30 — the day convention of the scorer's extract).

"P4 without DVI" is NOT derivable from stored windows (P4 is an AND across agents): it is a separate P4
rerun over the non-DVI members. The report says so per class (`series_notes`), never a bare null.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

from .density import AdmittedSpan, admitted_day_share_report

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

WINDOWS_SQL = (
    "SELECT w.event_class, w.path_id, w.rule_version, lower(w.interval), upper(w.interval)"
    " FROM public.ka_gochara_eval_window w"
    " WHERE w.chart_id = %s::uuid AND w.generation = %s"
    " ORDER BY w.event_class, w.path_id, lower(w.interval), w.window_id")
MEMBERS_SQL = (
    "SELECT w.event_class, w.path_id, r.agent, r.object_role,"
    "       lower(s.iv * w.interval), upper(s.iv * w.interval)"
    " FROM public.ka_gochara_eval_window w"
    " JOIN public.ka_gochara_eval_window_record m ON m.window_id = w.window_id"
    " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id"
    " CROSS JOIN LATERAL unnest(r.temporal_support_intervals) AS s(iv)"
    " WHERE w.chart_id = %s::uuid AND w.generation = %s AND NOT isempty(s.iv * w.interval)"
    " ORDER BY w.event_class, w.path_id, r.agent, lower(s.iv * w.interval), r.record_id")
HORIZON_SQL = (
    "SELECT DISTINCT lower(c.completed_horizon), upper(c.completed_horizon)"
    " FROM public.kala_gochara_coverage c"
    " WHERE c.chart_id = %s::uuid AND c.generation = %s AND c.partition_kind = 'event_class'"
    "   AND c.completed_horizon IS NOT NULL")
STATEMENTS = (WINDOWS_SQL, MEMBERS_SQL, HORIZON_SQL)


class ExtractRefused(RuntimeError):
    """The stored generation cannot be reported honestly (named, never defaulted)."""


def _tuples(rows) -> list[tuple]:
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in rows]


def _day_span(lo: dt.datetime, hi: dt.datetime, tz: dt.tzinfo) -> tuple[dt.date, dt.date] | None:
    """The inclusive calendar days (in `tz`) a half-open [lo, hi) touches; None for an empty interval."""
    if lo.tzinfo is None or hi.tzinfo is None:
        raise ExtractRefused("a stored interval bound is not timezone-aware")
    if not lo < hi:
        return None
    last = hi - dt.timedelta(microseconds=1)
    return lo.astimezone(tz).date(), last.astimezone(tz).date()


def read_horizon(conn, chart_id: str, generation: str, tz: dt.tzinfo = IST) -> tuple[dt.date, dt.date]:
    rows = _tuples(conn.execute(HORIZON_SQL, (chart_id, generation)).fetchall())
    if not rows:
        raise ExtractRefused(f"generation {generation!r}: no event_class coverage partition carries a completed_horizon")
    if len(rows) > 1:
        raise ExtractRefused(f"generation {generation!r}: {len(rows)} different completed horizons — never picked silently")
    span = _day_span(rows[0][0], rows[0][1], tz)
    if span is None:
        raise ExtractRefused(f"generation {generation!r}: the completed horizon is empty")
    return span


def read_spans(conn, chart_id: str, generation: str, tz: dt.tzinfo = IST) -> tuple[list[AdmittedSpan], dict[str, str]]:
    """(window + member spans, {class: the rule_version its P4 windows were built under})."""
    spans: list[AdmittedSpan] = []
    p4_version: dict[str, set[str]] = {}
    for cls, path, version, lo, hi in _tuples(conn.execute(WINDOWS_SQL, (chart_id, generation)).fetchall()):
        day = _day_span(lo, hi, tz)
        if day is None:
            raise ExtractRefused(f"{cls}/{path}: a stored window is empty")
        spans.append(AdmittedSpan(cls, path, day[0], day[1]))
        if path == "P4":
            p4_version.setdefault(cls, set()).add(version)
    for cls, path, agent, role, lo, hi in _tuples(conn.execute(MEMBERS_SQL, (chart_id, generation)).fetchall()):
        day = _day_span(lo, hi, tz)
        if day is not None:
            spans.append(AdmittedSpan(cls, path, day[0], day[1], agent=agent, via_kb=(role == "karaka"),
                                      level="member"))
    mixed = {c: sorted(v) for c, v in p4_version.items() if len(v) > 1}
    if mixed:
        raise ExtractRefused(f"P4 windows of one class under several rule versions: {mixed}")
    return spans, {c: next(iter(v)) for c, v in p4_version.items()}


def report_from_store(conn, *, chart_id: str, generation: str, tz: dt.tzinfo = IST,
                      horizon: tuple[dt.date, dt.date] | None = None) -> dict:
    """The admitted-day-share report of one stored generation. `horizon` overrides the coverage horizon (the
    report over the SCORED horizon, FB-50); the DVI members are those of the H table each class's P4 windows
    were built under."""
    from services.gochara_rules import registry as rules

    spans, p4_version = read_spans(conn, chart_id, generation, tz)
    h = horizon or read_horizon(conn, chart_id, generation, tz)
    dvi = {}
    for cls, version in sorted(p4_version.items()):
        members = rules.tier_table_lagna(version).get(cls, {}).get("dvi", ())
        if members:
            dvi[cls] = list(members)
    out = admitted_day_share_report(spans, h, dvi_members=dvi, generation=generation)
    out["source"] = {"kind": "stored_windows", "chart_id": chart_id, "day_timezone": str(tz),
                     "tables": ["ka_gochara_eval_window", "ka_gochara_eval_window_record",
                                "ka_gochara_relationship_record", "kala_gochara_coverage"],
                     "window_spans": sum(1 for s in spans if s.level == "window"),
                     "member_spans": sum(1 for s in spans if s.level == "member"),
                     "p4_rule_versions": dict(sorted(p4_version.items()))}
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI. The connection string is read from the ENVIRONMENT variable named by --dsn-env (never an argument:
    no DSN on a command line); the session is opened read-only."""
    import os

    ap = argparse.ArgumentParser(prog="gochara_eval.density_extract", description=__doc__.splitlines()[0])
    ap.add_argument("--chart-id", required=True)
    ap.add_argument("--generation", required=True)
    ap.add_argument("--dsn-env", required=True, help="NAME of the environment variable holding the connection string")
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)
    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        print(f"environment variable {args.dsn_env} is not set", file=sys.stderr)
        return 2
    import psycopg
    with psycopg.connect(dsn, autocommit=False) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        try:
            report = report_from_store(conn, chart_id=args.chart_id, generation=args.generation)
        except ExtractRefused as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 1
        finally:
            conn.rollback()
    with open(args.output, "w") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
    print(f"report written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
