"""Independent verifier side of the measuring build (FINAL_BUILD_SCOPE v1.1: FB-2, FB-3, FB-6, FB-50, FB-52, §13).

The measuring build is the FIRST unsealed full build: run shape `all_classes_full` of the existing
`gochara_v5_test_slice` marker (steward ruling MEASURING-BUILD), on the derived chart horizon, on TODAY's rules
(ND-H / ND-P2 not implemented). It exists to measure, so what the verifier owes it is (a) ACCEPTANCE: the build is
what it claims to be and cannot be mistaken for a sealable one, and (b) a REPORT recomputed from the stored rows
alone: admitted-day share per class and path (FB-50), window-length distribution, per-agent contribution, and the
near-miss COUNTS, shown separately and never added to a share (FB-29).

What this module does NOT do (stated plainly, review MV-FABLE-1 P2-5):
  * seam, wrap, graze and stretch counts are NOT recomputed here; an independent recount is on the not-done list;
  * `near_miss_counts` is a tally of the near-misses the caller passes (what the builder reports), not a recount;
  * the class census checks the marker's class list and the classes that hold rows; a class that is planned but holds
    no row (a partial class) is invisible to it, because a class may legitimately admit nothing;
  * acceptance of a stored generation is only claimed through `read_measuring_view` + `measuring_refusals` together.

Independence: this module imports NOTHING from the builder, the sweep, the evaluator or the record store. Its tables
(the horizon rule, the fast/slow split, the eight excluded classes, the scored-class list, the bound rule versions) are
written here from the specification and decision text and WILL BE compared with the builder's as data by the FB-38
equality test once the builder side exists (no such test exists yet).

Day arithmetic (FB-50 "days in the horizon"): the horizon is half-open `[start, end)` in UTC at midnight; a day is
ADMITTED when some admitted interval overlaps its `[00:00, 24:00)` UTC span by a positive length. An interval that
ends exactly at midnight does not admit the day it ends on; intervals touching inside one day count that day once.
Every date here is a UTC date: the build date is the UTC date the manifest pins.

P4-alone means the P4 path's OWN union of admitted days (ND-H's sign-bin P4 shares are of that kind), NOT P4 minus what
P1 and P3 already admit. The 40 percent comparison (FB-41) is made over the SCORED horizon of the evaluation protocol
(`SCORED_HORIZON`), never over the build horizon: call `class_share_report(..., SCORED_HORIZON)` for it.
"""
from __future__ import annotations

import dataclasses
import json
import math
from datetime import date, datetime, timedelta, timezone

# ── tables written from the specification text (FB-2/FB-3/FB-30/FB-35/FB-37/§13) ─────────────────────────────────
SUBSTRATE_DOMAIN_START = date(1998, 1, 1)                # FB-3: the convention substrate domain is 1998-01-01 ..
SUBSTRATE_DOMAIN_END = date(2085, 1, 1)                  # .. 2085-01-01
SCORED_HORIZON = (date(1998, 1, 1), date(2026, 4, 17))   # EVALUATION_PROTOCOL v2.3 §1 (FB-5): the scored window
MEASURING_SCOPE = "test_slice"                           # the marker's stored scope: never publishable, never sealable
MEASURING_RUN = "all_classes_full"                       # the third run shape (steward MEASURING-BUILD)
# The 27 registered event classes of the evaluation protocol's fixed table minus `birth_anchor` (an unscored annotation):
# the 26 SCORED classes an all-classes build must name. Written out here, never imported (review MV-FABLE-1 P2-2).
SCORED_CLASSES = frozenset({
    "achievement_recognition", "bereavement", "business_launch", "career_advancement", "career_change", "career_entry",
    "career_setback", "childbirth", "chronic_onset", "education_milestone", "exam_outcome", "financial_deception",
    "foreign_settlement", "illness_acute", "major_gain", "major_loss", "marriage", "parental_event",
    "property_acquisition", "psychological_arc", "relocation", "romantic_start", "separation", "spiritual_turn",
    "surgery", "travel_event"})
# The eight classes whose houses and significators ND-H decided are EXCLUDED from today's rules (`ST-H-UNKNOWN`, §13):
# a measuring build must hold no record and no window for them.
EXCLUDED_EIGHT = frozenset({
    "achievement_recognition", "business_launch", "financial_deception", "foreign_settlement",
    "parental_event", "property_acquisition", "psychological_arc", "spiritual_turn"})
# ND-H K-B names the slow agents as Jupiter/Saturn (conjunction or aspect) and Rahu/Ketu (conjunction), "fast agents
# never": the complement among the nine is the fast set.
SLOW_AGENTS = frozenset({"jupiter", "saturn", "rahu", "ketu"})
FAST_AGENTS = frozenset({"sun", "moon", "mars", "mercury", "venus"})
ALL_AGENTS = FAST_AGENTS | SLOW_AGENTS                   # lower-case, exactly as stored; anything else is refused by name
P4_AGENTS = frozenset({"jupiter", "saturn"})             # P4 = influence of Jupiter AND Saturn (FB-37/FB-45)
# Rule versions BOUND today (FB-30: BOUND_PATH_REFS name 1.0.0 for P1-P5; 1.1.0 rows exist but are not bound; 1.2.0 is the
# ND-H generation and must not appear in a measuring build, §13). An ALLOWLIST: any other version is refused.
ALLOWED_RULE_VERSIONS = frozenset({"1.0.0"})
PATHS = ("P1", "P2", "P3", "P4")
VIAS = ("base", "karakatva", "dvi", "kb")
# The life-event log's date precision, as the verifier reads it from a raw log row (`precision`): only a complete
# calendar day is "fully dated" (a year- or month-approximate event carries a proxy date and is NOT).
DATE_PRECISIONS = frozenset({"day", "month", "year", "approx", "unknown"})
_DAY = timedelta(days=1)


class MeasuringReportError(ValueError):
    """A refusal by name; the message starts with the refusal code."""


# ── dates ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def as_utc_date(value, *, what: str = "bound") -> date:
    """Normalise a stored bound to a UTC date: a `date` as is; a tz-aware datetime must sit exactly at UTC midnight
    (`horizon_bound_not_midnight` otherwise); a naive datetime is refused (`naive_datetime`); an ISO string is parsed
    the same way. The builder stores horizons as tz-aware instants / tstzrange bounds."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value) if "T" in value or " " in value else date.fromisoformat(value)
        except ValueError:
            raise MeasuringReportError(f"horizon_bound_unreadable: {what} {value!r}") from None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise MeasuringReportError(f"naive_datetime: {what} must be timezone-aware")
        u = value.astimezone(timezone.utc)
        if (u.hour, u.minute, u.second, u.microsecond) != (0, 0, 0, 0):
            raise MeasuringReportError(f"horizon_bound_not_midnight: {what} {u.isoformat()}")
        return u.date()
    if isinstance(value, date):
        return value
    raise MeasuringReportError(f"horizon_bound_unreadable: {what} {value!r}")


def _build_date(value) -> date:
    """The build date is a UTC DATE (as the manifest pins it): a date, or a tz-aware datetime taken to its UTC date."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise MeasuringReportError("naive_datetime: build_date must be timezone-aware")
        return value.astimezone(timezone.utc).date()
    return value


# ── the horizon (FB-1, FB-2, FB-3): the verifier's OWN derivation ─────────────────────────────────────────────────
def fully_dated_events(raw_rows):
    """From raw life-event-log rows ({'date', 'precision', 'is_birth'}) -> (dates of the FULLY dated events, count
    excluded as not fully dated). The birth entry is aside (not counted at all); only precision 'day' with a date is
    fully dated; an unknown precision word is refused by name, never guessed."""
    dates, excluded = [], 0
    for r in raw_rows:
        if r.get("is_birth"):
            continue
        prec = r.get("precision")
        if prec not in DATE_PRECISIONS:
            raise MeasuringReportError(f"lel_precision_unknown: {prec!r}")
        if prec == "day" and r.get("date") is not None:
            dates.append(as_utc_date(r["date"], what="event date"))
        else:
            excluded += 1
    return dates, excluded


def derive_chart_horizon_detail(birth_date: date, lel_rows, build_date) -> dict:
    """{'start', 'end', 'basis', 'excluded_undated'}. END = birth date + 100 years; START = 1 January of the year of the
    first FULLY dated life event (year truncation is Owner Ruling 13); with none, START = the build date (UTC date) and
    basis `build_date`. Refused by name: a 29 February birth whose +100 anniversary does not exist
    (`horizon_birth_anniversary_undefined`, flagged to the owner, not guessed), a start before birth, before the
    substrate domain, or in the future (`horizon_start_in_future`), an end outside the substrate domain."""
    build = _build_date(build_date)
    try:
        end = birth_date.replace(year=birth_date.year + 100)
    except ValueError:
        raise MeasuringReportError("horizon_birth_anniversary_undefined: "
                                   f"{birth_date.isoformat()} + 100 years does not exist") from None
    events, excluded = fully_dated_events(lel_rows)
    if events:
        start, basis = date(min(events).year, 1, 1), "first_dated_event"
        if start > build:
            raise MeasuringReportError(f"horizon_start_in_future: {start} > build date {build}")
    else:
        start, basis = build, "build_date"
    prob = horizon_problem((start, end), birth_date=birth_date)
    if prob:
        raise MeasuringReportError(prob)
    return {"start": start, "end": end, "basis": basis, "excluded_undated": excluded}


def derive_chart_horizon(birth_date: date, lel_rows, build_date):
    d = derive_chart_horizon_detail(birth_date, lel_rows, build_date)
    return d["start"], d["end"], d["basis"]


def horizon_problem(horizon, *, birth_date: date | None = None) -> str | None:
    """FB-3: the horizon is non-empty and lies inside the substrate domain `[1998-01-01, 2085-01-01]` (never clipped);
    with `birth_date`, it does not start before birth."""
    start, end = horizon
    if not start < end:
        return f"horizon_empty: {start}..{end}"
    if birth_date is not None and start < birth_date:                    # the more specific refusal comes first
        return f"horizon_start_before_birth: start {start} < birth {birth_date}"
    if start < SUBSTRATE_DOMAIN_START:
        return f"horizon_start_before_substrate_domain: start {start} < {SUBSTRATE_DOMAIN_START}"
    if end > SUBSTRATE_DOMAIN_END:
        return f"horizon_outside_substrate_domain: end {end} > {SUBSTRATE_DOMAIN_END}"
    return None


# ── acceptance of the measuring build (§13) ───────────────────────────────────────────────────────────────────────
@dataclasses.dataclass(frozen=True)
class MeasuringBuildView:
    """What the verification job reads from the stored generation; `read_measuring_view` fills it from the database.
    Bounds may be dates or the stored tz-aware instants (normalised by `measuring_refusals`)."""
    stored_scope: str | None
    run: str | None
    sealed: bool
    published: bool
    horizon: tuple                      # (start, end) as stored in the manifest
    rule_versions: frozenset            # every rule_version with a stored window or record
    near_miss_rows_stored: int          # rows in any near_miss store (0 when the tables do not exist yet)
    classes_with_records: frozenset     # event classes holding a stored record or window
    marker_classes: frozenset = frozenset()          # the classes the marker says the build was planned for
    marker_horizon: tuple | None = None              # the marker's own horizon, in clear


def measuring_refusals(view: MeasuringBuildView, *, expected_horizon, birth_date: date | None = None) -> list[str]:
    """Every reason, by name, that this stored generation is NOT an acceptable measuring build. Empty = accepted.
    Stored bounds are normalised to UTC-midnight dates first; a non-midnight or unreadable bound is its own refusal."""
    out: list[str] = []
    if view.stored_scope != MEASURING_SCOPE:
        out.append(f"measuring_scope_not_test_slice: {view.stored_scope!r}")
    if view.run != MEASURING_RUN:
        out.append(f"measuring_run_not_all_classes_full: {view.run!r}")
    if view.sealed:
        out.append("measuring_build_sealed")
    if view.published:
        out.append("measuring_build_published")
    try:
        stored = tuple(as_utc_date(x, what="stored horizon") for x in view.horizon)
        expected = tuple(as_utc_date(x, what="expected horizon") for x in expected_horizon)
    except MeasuringReportError as exc:
        out.append(str(exc))
        stored = expected = None
    if stored is not None:
        if stored != expected:
            out.append(f"horizon_mismatch: stored {tuple(map(str, stored))} != derived {tuple(map(str, expected))}")
        prob = horizon_problem(stored, birth_date=birth_date)
        if prob:
            out.append(prob)
        if view.marker_horizon is not None:
            try:
                marker = tuple(as_utc_date(x, what="marker horizon") for x in view.marker_horizon)
                if marker != stored:
                    out.append(f"marker_horizon_mismatch: marker {tuple(map(str, marker))} != stored {tuple(map(str, stored))}")
            except MeasuringReportError as exc:
                out.append(str(exc))
    bad_versions = sorted(set(view.rule_versions) - ALLOWED_RULE_VERSIONS)
    if bad_versions:
        out.append(f"rule_version_not_in_scope: {bad_versions} (bound today: {sorted(ALLOWED_RULE_VERSIONS)})")
    if view.near_miss_rows_stored:
        out.append(f"near_miss_rows_stored: {view.near_miss_rows_stored} (counts are reported, never stored, §13)")
    excluded_present = sorted(set(view.classes_with_records) & EXCLUDED_EIGHT)
    if excluded_present:
        out.append(f"excluded_class_has_rows: {excluded_present} (ST-H-UNKNOWN)")
    stray = sorted(set(view.classes_with_records) - SCORED_CLASSES)
    if stray:
        out.append(f"unknown_class_has_rows: {stray}")
    missing, extra = sorted(SCORED_CLASSES - set(view.marker_classes)), sorted(set(view.marker_classes) - SCORED_CLASSES)
    if missing or extra:
        out.append(f"class_census_mismatch: the marker names {len(set(view.marker_classes))} classes, missing {missing}, not scored {extra}")
    return out


_SQL_PUBLICATION = ("SELECT status, input_generation_vector, lower(horizon), upper(horizon) FROM public.kala_gochara_publication"
                    " WHERE chart_id = %s AND generation = %s")
_SQL_SEALED = "SELECT count(*) FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s"
_SQL_VERSIONS = ("SELECT rule_version FROM public.ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s"
                 " UNION SELECT rule_version FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s")
_SQL_CLASSES = ("SELECT event_class FROM public.ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s"
                " UNION SELECT event_class FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s")


def _scalar(row):
    return row[0] if not isinstance(row, dict) else next(iter(row.values()))


def read_measuring_view(conn, chart_id: str, generation: str) -> MeasuringBuildView:
    """Read-only: fill the acceptance view from the stored generation. Refused by name when the generation has no
    manifest (`measuring_manifest_missing`) or more than one (`measuring_manifest_ambiguous`): a view must not pick one."""
    rows = conn.execute(_SQL_PUBLICATION, (chart_id, generation)).fetchall()
    if not rows:
        raise MeasuringReportError("measuring_manifest_missing: no publication row for the generation")
    if len(rows) > 1:
        raise MeasuringReportError(f"measuring_manifest_ambiguous: {len(rows)} publication rows")
    status, vector, h_lo, h_hi = tuple(rows[0].values()) if isinstance(rows[0], dict) else tuple(rows[0])
    if isinstance(vector, str):
        vector = json.loads(vector)
    marker = (vector or {}).get("test_slice") or {}
    sealed = int(_scalar(conn.execute(_SQL_SEALED, (chart_id, generation)).fetchone())) > 0
    versions = frozenset(_scalar(r) for r in conn.execute(_SQL_VERSIONS, (chart_id, generation, chart_id, generation)).fetchall())
    classes = frozenset(_scalar(r) for r in conn.execute(_SQL_CLASSES, (chart_id, generation, chart_id, generation)).fetchall())
    nm = 0
    if _scalar(conn.execute("SELECT to_regclass('public.ka_gochara_near_miss')").fetchone()) is not None:
        nm = int(_scalar(conn.execute("SELECT count(*) FROM public.ka_gochara_near_miss WHERE chart_id = %s AND generation = %s",
                                      (chart_id, generation)).fetchone()))
    mh = marker.get("horizon")
    return MeasuringBuildView(
        stored_scope=(vector or {}).get("stored_scope"), run=marker.get("run"), sealed=sealed, published=status == "published",
        horizon=(h_lo, h_hi), rule_versions=versions, near_miss_rows_stored=nm, classes_with_records=classes,
        marker_classes=frozenset(marker.get("classes") or ()), marker_horizon=tuple(mh) if mh else None)


# ── day arithmetic ────────────────────────────────────────────────────────────────────────────────────────────────
def _utc(t: datetime) -> datetime:
    if t.tzinfo is None:
        raise MeasuringReportError("naive_datetime: every stored instant is timezone-aware")
    return t.astimezone(timezone.utc)


def _midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _day_ranges(intervals, horizon) -> list[tuple[int, int]]:
    """Merged, half-open `[first_day, last_day_exclusive)` ordinal ranges of the days the intervals admit inside the
    horizon (an interval touching a day for zero length admits nothing). An inverted interval is refused."""
    h0, h1 = _midnight(horizon[0]), _midnight(horizon[1])
    ranges = []
    for lo, hi in intervals:
        lo, hi = _utc(lo), _utc(hi)
        if hi < lo:
            raise MeasuringReportError(f"interval_inverted: {lo.isoformat()} > {hi.isoformat()}")
        lo, hi = max(lo, h0), min(hi, h1)
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
    'karakatva' (FB-46, P1), 'dvi' (FB-41, P4), 'kb' (FB-37, luminary target). Any other tag is refused."""
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
    `records`: SupportRecord (admitted ones only); `windows`: (event_class, path, lo, hi) stored windows.
    Refused by name: an unknown path (record or window), an unknown agent (not one of the nine, lower-case), an unknown
    via tag, an inverted interval — a silent zero in the fast/slow shares would feed the per-class fast-planet decision."""
    if (prob := horizon_problem(horizon)):
        raise MeasuringReportError(prob)
    for r in records:
        if r.path not in PATHS:
            raise MeasuringReportError(f"unknown_path: {r.path!r}")
        if r.agent not in ALL_AGENTS:
            raise MeasuringReportError(f"unknown_agent: {r.agent!r} (the nine, lower-case)")
        if r.via not in VIAS:
            raise MeasuringReportError(f"unknown_via: {r.via!r}")
    for w in windows:
        if w[1] not in PATHS:
            raise MeasuringReportError(f"unknown_path: {w[1]!r} (window)")
    classes = sorted({r.event_class for r in records} | {w[0] for w in windows})
    out = {}
    for cls in classes:
        rs = [r for r in records if r.event_class == cls]

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
            lens = []
            for c, p, lo, hi in windows:
                if c == cls and p == path:
                    lo, hi = _utc(lo), _utc(hi)
                    if hi < lo:
                        raise MeasuringReportError(f"interval_inverted: window {lo.isoformat()} > {hi.isoformat()}")
                    lens.append((hi - lo).total_seconds() / 86400.0)
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
    """FB-50 item 6 / FB-29: near-miss windows counted per (class, relation, body), SEPARATELY. A TALLY of what the caller
    passes (what the builder reports), not an independent recount. `class_share_report` does not accept near-misses, so no
    share can include one. `near_misses`: (event_class, relation, body) tuples (reported at measuring time, not stored)."""
    counts: dict = {}
    for cls, relation, body in near_misses:
        key = f"{cls}|{relation}|{body}"
        counts[key] = counts.get(key, 0) + 1
    return {"total": sum(counts.values()), "by_class_relation_body": dict(sorted(counts.items()))}


# ── database reader (thin; the arithmetic above is what the tests pin) ────────────────────────────────────────────
_SQL_RECORDS = (
    "SELECT r.event_class, r.path_id, r.rule_version, r.agent, lower(s.x), upper(s.x), lower_inf(s.x), upper_inf(s.x)"
    " FROM public.ka_gochara_relationship_record r"
    " LEFT JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x) ON true"
    " WHERE r.chart_id = %s AND r.generation = %s AND r.admission_state = 'admitted'"
    " ORDER BY r.record_id, lower(s.x)")


def read_records(conn, chart_id: str, generation: str) -> list[SupportRecord]:
    """Admitted stored records of a generation as SupportRecord. The `via` tag is NOT defaulted: a stored row is `base`
    only because its rule_version is one BOUND today (a bound row carries no extension), and any other version is refused
    (`rule_version_not_in_scope`). A path id outside P1..P4 (P5 is held), an agent that is not one of the nine
    (lower-case) and an unbounded support interval are each refused by name, never folded into a share."""
    grouped: dict = {}
    for cls, path, version, agent, lo, hi, lo_inf, hi_inf in conn.execute(_SQL_RECORDS, (chart_id, generation)).fetchall():
        if path not in PATHS:
            raise MeasuringReportError(f"unknown_path_id: {path!r}")
        if version not in ALLOWED_RULE_VERSIONS:
            raise MeasuringReportError(f"rule_version_not_in_scope: {version!r}")
        if agent not in ALL_AGENTS:
            raise MeasuringReportError(f"unknown_agent: {agent!r}")
        bucket = grouped.setdefault((cls, path, agent), [])
        if lo is None and hi is None and not (lo_inf or hi_inf):
            continue                                            # a record with no support interval at all
        if lo_inf or hi_inf or lo is None or hi is None:
            raise MeasuringReportError(f"support_interval_unbounded: {cls} {path} {agent}")
        bucket.append((lo, hi))
    return [SupportRecord(c, p, a, tuple(ivs), "base") for (c, p, a), ivs in sorted(grouped.items())]
