"""Independent verifier side of the measuring build (FINAL_BUILD_SCOPE v1.1: FB-2, FB-3, FB-6, FB-50, FB-52, §13).

The measuring build is the FIRST unsealed full build: run shape `all_classes_full` of the existing
`gochara_v5_test_slice` marker (steward ruling MEASURING-BUILD), on the derived chart horizon, on TODAY's rules
(ND-H / ND-P2 not implemented). It exists to measure, so what the verifier owes it is (a) ACCEPTANCE: the build is
what it claims to be and cannot be mistaken for a sealable one, and (b) a REPORT recomputed from the stored rows
alone: admitted-day share per class and path (FB-50), window-length distribution, per-agent contribution, and the
near-miss COUNTS, shown separately and never added to a share (FB-29).

Independence: this module imports NOTHING from the builder, the sweep, the evaluator or the record store. Its
tables (the horizon rule, the fast/slow split, the eight excluded classes) are written here from the specification
text and are compared with the builder's as data by the equality test, never by import.

Pure functions over plain tuples/dicts; the database reader is a separate, thin function so the arithmetic is
testable without a cluster.

Day arithmetic (FB-50 "days in the horizon"): the horizon is half-open `[start, end)` in UTC at midnight; a day is
ADMITTED when some admitted interval overlaps its `[00:00, 24:00)` UTC span by a positive length. An interval that
ends exactly at midnight does not admit the day it ends on; intervals touching inside one day count that day once.
"""
from __future__ import annotations

import dataclasses
import math
from datetime import date, datetime, timedelta, timezone

# ── tables written from the specification text (FB-2/FB-3/FB-35/FB-37/§13) ───────────────────────────────────────
SUBSTRATE_DOMAIN_END = date(2085, 1, 1)                  # FB-3: the convention substrate domain ends 2085-01-01
MEASURING_SCOPE = "test_slice"                           # the marker's stored scope: never publishable, never sealable
MEASURING_RUN = "all_classes_full"                       # the third run shape (steward MEASURING-BUILD)
# The eight classes whose houses and significators ND-H decided are EXCLUDED from today's rules (`ST-H-UNKNOWN`, §13):
# a measuring build must hold no record and no window for them.
EXCLUDED_EIGHT = frozenset({
    "achievement_recognition", "business_launch", "financial_deception", "foreign_settlement",
    "parental_event", "property_acquisition", "psychological_arc", "spiritual_turn"})
# ND-H K-B names the slow agents as Jupiter/Saturn (conjunction or aspect) and Rahu/Ketu (conjunction), "fast agents
# never": the complement among the nine is the fast set.
SLOW_AGENTS = frozenset({"jupiter", "saturn", "rahu", "ketu"})
FAST_AGENTS = frozenset({"sun", "moon", "mars", "mercury", "venus"})
P4_AGENTS = frozenset({"jupiter", "saturn"})             # P4 = influence of Jupiter AND Saturn (FB-37/FB-45)
# Rule versions: today's rows only. 1.2.0 is the ND-H generation and must not appear in a measuring build (§13).
FORBIDDEN_RULE_VERSIONS = frozenset({"1.2.0"})
PATHS = ("P1", "P2", "P3", "P4")
_DAY = timedelta(days=1)


class MeasuringReportError(ValueError):
    """A refusal by name; the message starts with the refusal code."""


# ── the horizon (FB-1, FB-2): the verifier's OWN derivation ───────────────────────────────────────────────────────
def derive_chart_horizon(birth_date: date, dated_events, build_date: date):
    """-> (start, end, basis). END = birth date + 100 years; START = 1 January of the year of the first FULLY dated
    life-event (`dated_events`: full `date` values only — the caller passes the events that carry a complete date,
    the birth entry excluded); with none, START = the build date and basis `build_date`. A 29 February birth has no
    anniversary in a non-leap year: refused by name rather than guessed."""
    try:
        end = birth_date.replace(year=birth_date.year + 100)
    except ValueError:
        raise MeasuringReportError("horizon_birth_anniversary_undefined: "
                                   f"{birth_date.isoformat()} + 100 years does not exist") from None
    events = sorted(d for d in dated_events if d is not None)
    if events:
        return date(events[0].year, 1, 1), end, "first_dated_event"
    return build_date, end, "build_date"


def horizon_problem(horizon) -> str | None:
    """FB-3: the horizon is non-empty and lies inside the substrate domain (end <= 2085-01-01); never clipped."""
    start, end = horizon
    if not start < end:
        return f"horizon_empty: {start}..{end}"
    if end > SUBSTRATE_DOMAIN_END:
        return f"horizon_outside_substrate_domain: end {end} > {SUBSTRATE_DOMAIN_END}"
    return None


# ── acceptance of the measuring build (§13) ───────────────────────────────────────────────────────────────────────
@dataclasses.dataclass(frozen=True)
class MeasuringBuildView:
    """What the verification job reads from the stored generation (no builder import; the reader below fills it)."""
    stored_scope: str | None
    run: str | None
    sealed: bool
    published: bool
    horizon: tuple                      # (start, end) dates as stored in the manifest
    rule_versions: frozenset            # every rule_version with a stored window or record
    near_miss_rows_stored: int          # rows in any near_miss store (0 when the tables do not exist yet)
    classes_with_records: frozenset     # event classes holding a stored record or window


def measuring_refusals(view: MeasuringBuildView, *, expected_horizon) -> list[str]:
    """Every reason, by name, that this stored generation is NOT an acceptable measuring build. Empty = accepted."""
    out: list[str] = []
    if view.stored_scope != MEASURING_SCOPE:
        out.append(f"measuring_scope_not_test_slice: {view.stored_scope!r}")
    if view.run != MEASURING_RUN:
        out.append(f"measuring_run_not_all_classes_full: {view.run!r}")
    if view.sealed:
        out.append("measuring_build_sealed")
    if view.published:
        out.append("measuring_build_published")
    if tuple(view.horizon) != tuple(expected_horizon):
        out.append(f"horizon_mismatch: stored {tuple(map(str, view.horizon))} != derived {tuple(map(str, expected_horizon))}")
    prob = horizon_problem(tuple(view.horizon))
    if prob:
        out.append(prob)
    bad_versions = sorted(set(view.rule_versions) & FORBIDDEN_RULE_VERSIONS)
    if bad_versions:
        out.append(f"rule_version_not_in_scope: {bad_versions}")
    if view.near_miss_rows_stored:
        out.append(f"near_miss_rows_stored: {view.near_miss_rows_stored} (counts are reported, never stored, §13)")
    excluded_present = sorted(set(view.classes_with_records) & EXCLUDED_EIGHT)
    if excluded_present:
        out.append(f"excluded_class_has_rows: {excluded_present} (ST-H-UNKNOWN)")
    return out


# ── day arithmetic ────────────────────────────────────────────────────────────────────────────────────────────────
def _utc(t: datetime) -> datetime:
    if t.tzinfo is None:
        raise MeasuringReportError("naive_datetime: every stored instant is timezone-aware")
    return t.astimezone(timezone.utc)


def _midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _day_ranges(intervals, horizon) -> list[tuple[int, int]]:
    """Merged, half-open `[first_day, last_day_exclusive)` ordinal ranges of the days the intervals admit inside the
    horizon (an interval touching a day for zero length admits nothing)."""
    h0, h1 = _midnight(horizon[0]), _midnight(horizon[1])
    ranges = []
    for lo, hi in intervals:
        lo, hi = max(_utc(lo), h0), min(_utc(hi), h1)
        if not lo < hi:
            continue
        first = lo.date().toordinal()
        last_excl = hi.date().toordinal() + (0 if hi == _midnight(hi.date()) else 1)
        ranges.append((first, last_excl))
    ranges.sort()
    merged: list[list[int]] = []
    for a, b in ranges:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


def admitted_days(intervals, horizon) -> int:
    return sum(b - a for a, b in _day_ranges(intervals, horizon))


def horizon_days(horizon) -> int:
    return (horizon[1] - horizon[0]).days


def _share(days: int, horizon) -> float:
    return days / horizon_days(horizon)


def _day_set(intervals, horizon) -> set[int]:
    out: set[int] = set()
    for a, b in _day_ranges(intervals, horizon):
        out.update(range(a, b))
    return out


def length_distribution(lengths_days) -> dict:
    """count, median, p90 (nearest rank: the ceil(0.9 n)-th smallest), max — all None when there is no window
    (an honest null, never a zero)."""
    xs = sorted(lengths_days)
    n = len(xs)
    if not n:
        return {"count": 0, "median": None, "p90": None, "max": None}
    median = xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2
    return {"count": n, "median": median, "p90": xs[math.ceil(0.9 * n) - 1], "max": xs[-1]}


# ── the report (FB-50) ────────────────────────────────────────────────────────────────────────────────────────────
@dataclasses.dataclass(frozen=True)
class SupportRecord:
    """One stored admitted relationship record: its class, path (P1..P4), agent and stored support intervals.
    `via` is 'base' for today's rules; the extension tags exist so the report can split them when they land:
    'karakatva' (FB-46, P1), 'dvi' (FB-41, P4), 'kb' (FB-37, luminary target)."""
    event_class: str
    path: str
    agent: str
    supports: tuple
    via: str = "base"


def _group(records, pred):
    return [iv for r in records if pred(r) for iv in r.supports]


def class_share_report(records, windows, horizon) -> dict:
    """FB-50 items 1-3, per class: admitted-day shares by path and variant, the class union, K-B exclusive days,
    window-length distribution per path, per-agent contribution (days the agent admits; days only it admits).
    `records`: SupportRecord (admitted ones only); `windows`: (event_class, path, lo, hi) stored windows."""
    if (prob := horizon_problem(horizon)):
        raise MeasuringReportError(prob)
    classes = sorted({r.event_class for r in records} | {w[0] for w in windows})
    out = {}
    for cls in classes:
        rs = [r for r in records if r.event_class == cls]
        for r in rs:
            if r.path not in PATHS:
                raise MeasuringReportError(f"unknown_path: {r.path!r}")

        def days(pred) -> int:
            return admitted_days(_group(rs, pred), horizon)

        p3 = lambda r: r.path == "P3" and r.via in ("base", "kb")          # noqa: E731
        base_days = _day_set(_group(rs, lambda r: r.via != "kb"), horizon)
        kb_days = _day_set(_group(rs, lambda r: r.via == "kb"), horizon)
        shares = {
            "P1_base": days(lambda r: r.path == "P1" and r.via == "base"),
            "P1_with_karakatva": days(lambda r: r.path == "P1" and r.via in ("base", "karakatva")),
            "P2": days(lambda r: r.path == "P2"),
            "P3_fast": days(lambda r: p3(r) and r.agent in FAST_AGENTS),
            "P3_slow": days(lambda r: p3(r) and r.agent in SLOW_AGENTS),
            "P3_union": days(p3),
            "P4_without_dvi": days(lambda r: r.path == "P4" and r.via == "base"),
            "P4_with_dvi": days(lambda r: r.path == "P4" and r.via in ("base", "dvi")),
            "kb_only": len(kb_days - base_days),
            "class_union": days(lambda r: True),
        }
        per_agent = {}
        for agent in sorted({r.agent for r in rs}):
            mine = _day_set(_group(rs, lambda r, a=agent: r.agent == a), horizon)
            others = _day_set(_group(rs, lambda r, a=agent: r.agent != a), horizon)
            per_agent[agent] = {"days": len(mine), "exclusive_days": len(mine - others)}
        lengths = {}
        for path in PATHS:
            lens = [(_utc(hi) - _utc(lo)).total_seconds() / 86400.0
                    for c, p, lo, hi in windows if c == cls and p == path]
            lengths[path] = length_distribution(lens)
        out[cls] = {
            "admitted_days": shares,
            "admitted_share": {k: _share(v, horizon) for k, v in shares.items()},
            "window_lengths_days": lengths,
            "per_agent": per_agent,
        }
    return {"horizon": [str(horizon[0]), str(horizon[1])], "horizon_days": horizon_days(horizon), "classes": out}


def clip_windows_for_scoring(windows, scored_end: datetime):
    """FB-5: windows are served after the scored end and scored only up to it. The stored window is untouched; this
    returns the clipped view the scoring harness reads: windows starting at/after `scored_end` are dropped, a straddling
    window is cut at it."""
    end = _utc(scored_end)
    out = []
    for c, p, lo, hi in windows:
        lo, hi = _utc(lo), _utc(hi)
        if lo >= end:
            continue
        out.append((c, p, lo, min(hi, end)))
    return out


def near_miss_counts(near_misses) -> dict:
    """FB-50 item 6 / FB-29: near-miss windows counted per (class, relation, body), SEPARATELY. This function is the
    only consumer of near-misses in the report; `class_share_report` does not accept them, so no share can include one.
    `near_misses`: (event_class, relation, body) tuples (reported at measuring time, not stored)."""
    counts: dict = {}
    for cls, relation, body in near_misses:
        key = f"{cls}|{relation}|{body}"
        counts[key] = counts.get(key, 0) + 1
    return {"total": sum(counts.values()), "by_class_relation_body": dict(sorted(counts.items()))}


# ── database reader (thin; the arithmetic above is what the tests pin) ────────────────────────────────────────────
_SQL_RECORDS = (
    "SELECT r.event_class, r.path_id, r.agent, lower(s.x), upper(s.x)"
    " FROM public.ka_gochara_relationship_record r"
    " LEFT JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x) ON true"
    " WHERE r.chart_id = %s AND r.generation = %s AND r.admission_state = 'admitted'"
    " ORDER BY r.record_id, lower(s.x)")


def read_records(conn, chart_id: str, generation: str) -> list[SupportRecord]:
    """Admitted stored records of a generation as SupportRecord (base tier: today's rules carry no extension tags).
    A path id outside P1..P4 (P5 is held) is refused by name, never folded into a share."""
    grouped: dict = {}
    for cls, path, agent, lo, hi in conn.execute(_SQL_RECORDS, (chart_id, generation)).fetchall():
        if path not in PATHS:
            raise MeasuringReportError(f"unknown_path_id: {path!r}")
        grouped.setdefault((cls, path, agent), []).append((lo, hi))
    return [SupportRecord(c, p, a, tuple((lo, hi) for lo, hi in ivs if lo is not None))
            for (c, p, a), ivs in sorted(grouped.items())]
