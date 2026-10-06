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
  * acceptance of a stored generation is only claimed through `read_measuring_view` + `measuring_refusals` together;
  * MARKER INTEGRITY is NOT checked: `marker_digest_verified` is always None (reason `not_checked_by_verifier_steward_stamp_proof`): the verifier
    must not import the writer, so only the digest's SHAPE (64 lower-case hex) is checked; integrity is the steward's stamp proof at the sitting.

Independence: this module imports NOTHING from the builder, the sweep, the evaluator or the record store. Its tables
(the horizon rule, the fast/slow split, the eight excluded classes, the scored-class list, the selected rule versions) are
written here from the specification and decision text and WILL BE compared with the builder's as data by the FB-38
equality test once the builder side exists (no such test exists yet).

Day arithmetic (FB-50 "days in the horizon"): a day is ADMITTED when some admitted interval overlaps its `[00:00, 24:00)` span by a positive
length; an interval ending exactly at midnight does not admit the day it ends on; intervals touching inside one day count that day once.
TWO conventions, never mixed in one ratio: the BUILD horizon is UTC calendar dates, half-open `[start, end)` (`class_share_report`,
`convention` 'utc_half_open', 31,446 days for the pinned chart); the SCORED horizon is the SCORER's own (IST calendar dates, both endpoints
inclusive, 1998-01-01 .. 2026-04-17 = 10,334 days: gochara_eval/registry.py:8-21, extract.py:65-67, metrics.py:80-87; `scored_share_report`,
`convention` 'ist_inclusive'), for numerator AND denominator: a window covers the IST calendar dates from its start's date through its end's date,
endpoint dates inclusive, so a window ending exactly at IST midnight still counts the date it ends on. Every number that feeds the 40 percent guard
uses the scored grid (one day in either term can flip it: 4,134/10,334 is 40.004 percent, 4,133/10,333 is 39.998). Every date elsewhere is a UTC date
(the build date is the UTC date the manifest pins).

P4 is the INTERSECTION, at the instant level, of Jupiter's and Saturn's influence unions (window_store.py:199-220; migration 1240:280-299), not
their union and not a day-set intersection; "P4-alone" is the P4 path's own admitted set, which is that intersection (K-B edges count toward an
agent's influence; DVI members only in the `with_dvi` variant).
"""
from __future__ import annotations

import dataclasses
import json
import math
import re
from datetime import date, datetime, timedelta, timezone

# ── tables written from the specification text (FB-2/FB-3/FB-30/FB-35/FB-37/§13) ─────────────────────────────────
SUBSTRATE_DOMAIN_START = date(1998, 1, 1)                # FB-3: the convention substrate domain is 1998-01-01 ..
SUBSTRATE_DOMAIN_END = date(2085, 1, 1)                  # .. 2085-01-01
SCORED_HORIZON_DATES = (date(1998, 1, 1), date(2026, 4, 17))   # the scorer's H0 and H1, both INCLUSIVE, IST calendar dates
SCORED_DAYS = 10334                                            # (H1 - H0).days + 1: EVALUATION_PROTOCOL v2.3 §1 and gochara_eval.registry.H_DAYS
MEASURING_SCOPE = "test_slice"                           # the marker's stored scope: never publishable, never sealable
MEASURING_RUN = "all_classes_full"
MARKER_SCHEMA = "gochara_v5_test_slice/1"
MARKER_DIGEST_NOT_CHECKED = "not_checked_by_verifier_steward_stamp_proof"
_DIGEST = re.compile(r"[0-9a-f]{64}")                       # the third run shape (steward MEASURING-BUILD)
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
# Rule versions SELECTED today (FB-30: BOUND/SELECTED_PATH_REFS name 1.0.0 for P1-P5; 1.1.0 rows exist but are not selected; 1.2.0 is the
# ND-H generation and must not appear in a measuring build, §13). An ALLOWLIST: any other version is refused.
ALLOWED_RULE_VERSIONS = frozenset({"1.0.0"})
PATHS = ("P1", "P2", "P3", "P4")
VIAS = ("base", "karakatva", "dvi", "kb")
# which paths an extension tag can legally belong to (FB-34/FB-37/FB-46): DVI only in P4, K-B only in P3 and P4, karakatva only in P1
VIA_PATHS = {"base": frozenset(PATHS), "karakatva": frozenset({"P1"}), "dvi": frozenset({"P4"}), "kb": frozenset({"P3", "P4"})}
# The life-event log as STORED (`life_events`: 001_baseline + 423 (chart_id) + 457_lel_schema_v2_event_shapes + 691): `event_id`, `event_date`,
# `category`, `date_confidence` in {exact, month_known, year_only}, `shape` in {point, interval, chain}, `interval_start`, `interval_end`,
# `chain_parent_event_id`, `domain` and `provenance` (`lel_id`). There is NO birth flag: the birth row is identified by `domain = 'other/birth'`
# (`is_birth_row`, pinned by the R-LEL read of the real log).
DATE_CONFIDENCES = frozenset({"exact", "month_known", "year_only"})
SHAPES = frozenset({"point", "interval", "chain"})
_EVENT_ID = re.compile(r"^EVT\.(\d{4})\.(\d{2})\.(\d{2})\.(\d{2})$")        # a REAL-digit id: month and day are digits (year-only ids carry XX)
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
    """The build date is a UTC DATE (as the manifest pins it): a date, or a tz-aware datetime taken to its UTC date; anything else
    (None, a string) is refused by name."""
    if not isinstance(value, date):
        raise MeasuringReportError(f"build_date_unreadable: {value!r}")
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise MeasuringReportError("naive_datetime: build_date must be timezone-aware")
        return value.astimezone(timezone.utc).date()
    return value


# ── the horizon (FB-1, FB-2, FB-3): the verifier's OWN derivation ─────────────────────────────────────────────────
def is_birth_row(row: dict) -> bool:
    """The birth row: `domain = 'other/birth'`, the ONLY identifier (R-LEL, read-only production read of the real log, 5 Oct 2026: the birth row has category
    `other`, event_type `other`, domain `other/birth`, lel id EVT.1984.02.05.01, and `provenance->>'subcategory'` is EMPTY on every row; the existing reader
    identifies it the same way, lel.ts:132-138). No `subcategory`, `event_type` or `category` spelling identifies it."""
    return row.get("domain") == "other/birth"


def birth_date_of(birth_params) -> date:
    """The civil date of `birth_params['datetime_iso']` IN ITS OWN OFFSET (the real runner passes no `birth_date` key): 1984-02-05T10:43+05:30
    is 1984-02-05 even though it is 1984-02-05T05:13Z."""
    iso = (birth_params or {}).get("datetime_iso")
    if not isinstance(iso, str):
        raise MeasuringReportError(f"birth_params_unreadable: datetime_iso {iso!r}")
    try:
        return datetime.fromisoformat(iso).date()
    except ValueError:
        raise MeasuringReportError(f"birth_params_unreadable: datetime_iso {iso!r}") from None


def _row_dates(r: dict, by_id: dict, reading: str):
    """The date this row would open the horizon with under `reading` ('event_date' | 'interval_start' | 'chain_root')."""
    if reading == "interval_start" and r.get("shape") == "interval" and r.get("interval_start") is not None:
        return as_utc_date(r["interval_start"], what="interval_start")
    if reading == "chain_root" and r.get("shape") == "chain":
        seen, cur = set(), r
        while cur.get("chain_parent_event_id") is not None:
            pid = cur["chain_parent_event_id"]
            if pid in seen or pid not in by_id:
                raise MeasuringReportError(f"lel_chain_unresolvable: {r.get('event_id')!r} -> {pid!r}")
            seen.add(pid)
            cur = by_id[pid]
        return as_utc_date(cur["event_date"], what="chain root date")
    return as_utc_date(r["event_date"], what="event_date")


def _lel_id(r: dict):
    """The human `EVT.*` id of a row: `provenance->>'lel_id'` ONLY. The intake stores a uuid5 in `event_id` and the EVT id in provenance; a dated
    top-level `event_id` is NOT a substitute (a row without a provenance lel id has no id: rule I cannot hold for it)."""
    prov = r.get("provenance") if isinstance(r.get("provenance"), dict) else {}
    return str(prov["lel_id"]) if prov.get("lel_id") is not None else None


def _id_dated(r: dict) -> bool:
    """Rule I: the lel id has REAL digits `EVT.YYYY.MM.DD.NN` and its date equals the stored `event_date` (migration 457 defaulted legacy rows to
    `exact`, so the flag alone is not trustworthy)."""
    m = _EVENT_ID.match(_lel_id(r) or "")
    if not m or r.get("event_date") is None:
        return False
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) == as_utc_date(r["event_date"], what="event_date")
    except (ValueError, MeasuringReportError):
        return False


def fully_dated_events(rows, *, birth_date: date):
    """From STORED life-event rows -> {'dates', 'excluded', 'chosen', 'readings', 'birth_row', 'flag_exact_but_id_undated', 'rows_without_lel_id'}. EMPTY log: nothing to identify (the caller falls
    back to the rebuild date). A non-empty log must hold exactly one birth row (`is_birth_row` and `event_date == birth_date`), set aside and
    never counted, else `lel_birth_row_unidentifiable`. FULLY DATED is a CONJUNCTION (MB-CONTRACT-V1): `date_confidence == 'exact'` (rule F) AND the
    row's lel id (`provenance->>'lel_id'`, NOT the uuid `event_id`) has real digits `EVT.YYYY.MM.DD.NN` and that date equals `event_date` (rule I). An
    exact-flagged row whose id is undated or mismatched is EXCLUDED and REPORTED (`flag_exact_but_id_undated`), never a refusal; an exact-flagged row with NO
    provenance lel id at all is NOT fully dated either: EXCLUDED, and EVERY row without a provenance lel id (whatever its confidence) is REPORTED
    (`rows_without_lel_id`, with its event_id and date), never a refusal and never a fallback to the top-level event_id (R-LEL: the real log holds an exact lifelong interval dated on the birth date with no lel id). The date of
    a row is its own `event_date` for EVERY shape (the literal reading of "the first event"); START is also computed under the interval-start and
    chain-root readings and the derivation is refused (`lel_shape_reading_sensitive`) only when a reading would change START (the interval/chain
    reading is an OPEN owner point). Unknown `date_confidence` / `shape` words, an exact row without `event_date`, and an unresolvable chain are
    refused by name."""
    rows = list(rows)
    out = {"dates": [], "excluded": 0, "chosen": None, "readings": {}, "birth_row": None, "flag_exact_but_id_undated": [], "rows_without_lel_id": []}
    if not rows:
        return out
    births = [r for r in rows if r.get("event_date") is not None and is_birth_row(r)
              and as_utc_date(r["event_date"], what="birth row date") == birth_date]
    if len(births) != 1:
        raise MeasuringReportError(f"lel_birth_row_unidentifiable: {len(births)} birth rows on {birth_date} in a log of {len(rows)} rows")
    out["birth_row"] = births[0]
    by_id = {r.get("event_id"): r for r in rows}
    full = []
    for r in rows:
        if r is births[0]:
            continue
        conf, shape = r.get("date_confidence"), r.get("shape")
        if conf not in DATE_CONFIDENCES:
            raise MeasuringReportError(f"lel_date_confidence_unknown: {conf!r}")
        if shape not in SHAPES:
            raise MeasuringReportError(f"lel_shape_unknown: {shape!r}")
        if _lel_id(r) is None:                       # no provenance lel id: reported WHATEVER its confidence (R-LEL-ASTRA), never a refusal, no fallback to event_id
            out["rows_without_lel_id"].append({"event_id": r.get("event_id"), "event_date": None if r.get("event_date") is None else str(r["event_date"])})
        if conf != "exact":
            out["excluded"] += 1
            continue
        if r.get("event_date") is None:
            raise MeasuringReportError(f"lel_date_missing: an exact {shape} event has no event_date")
        if _lel_id(r) is None:                       # not fully dated: excluded (already reported above)
            out["excluded"] += 1
        elif _id_dated(r):
            full.append(r)
        else:
            out["excluded"] += 1
            out["flag_exact_but_id_undated"].append({"event_id": r.get("event_id"), "lel_id": _lel_id(r), "event_date": str(r["event_date"])})
    def start_of(selected, reading):
        ds = sorted(_row_dates(r, by_id, reading) for r in selected)
        return date(ds[0].year, 1, 1) if ds else None
    for key in ("flag_exact_but_id_undated", "rows_without_lel_id"):           # the reports do not depend on the order the rows were read in
        out[key].sort(key=lambda x: (str(x["event_date"]), str(x["event_id"])))
    readings = {k: start_of(full, k) for k in ("event_date", "interval_start", "chain_root")}
    if len(set(readings.values())) > 1:
        raise MeasuringReportError(f"lel_shape_reading_sensitive: {sorted((k, str(v)) for k, v in readings.items())}")
    out["readings"] = readings
    out["dates"] = sorted(_row_dates(r, by_id, "event_date") for r in full)
    out["chosen"] = min(full, key=lambda r: _row_dates(r, by_id, "event_date")) if full else None
    return out


def derive_chart_horizon_detail(birth, lel_rows, build_date) -> dict:
    """{'start', 'end', 'basis', 'excluded_undated', 'readings', 'chosen'}. `birth` is the birth DATE or the runner's `birth_params` dict
    (`datetime_iso`, read in its own offset). END = birth date + 100 years; START = 1 January of the year of the first FULLY dated life event
    (year truncation is Owner Ruling 13; the dating rules are those of `fully_dated_events`); an EMPTY log, or one with no fully dated event, falls
    back to the build date (a UTC date) with basis `build_date`. Refused by name: a 29 February birth whose +100 anniversary does not exist
    (`horizon_birth_anniversary_undefined`), a start before birth, before the substrate domain, or in the future (`horizon_start_in_future`), an end
    outside the substrate domain, and the log refusals of `fully_dated_events`."""
    birth_date = birth if isinstance(birth, date) and not isinstance(birth, datetime) else birth_date_of(birth)
    build = _build_date(build_date)
    try:
        end = birth_date.replace(year=birth_date.year + 100)
    except ValueError:
        raise MeasuringReportError("horizon_birth_anniversary_undefined: "
                                   f"{birth_date.isoformat()} + 100 years does not exist") from None
    lel_rows = list(lel_rows)
    info = fully_dated_events(lel_rows, birth_date=birth_date)
    if lel_rows and not info["dates"]:
        # the rebuild-date fallback is ONLY for a log with ZERO rows (the owner's "else"); a log that exists but opens no fully dated event is a case
        # the owner has not ruled on (it cannot occur for the pinned chart): refused, never read as an absent log
        raise MeasuringReportError(f"horizon_underivable_log_has_no_dated_event: {len(lel_rows)} rows, none fully dated")
    if info["dates"]:
        start, basis = date(info["dates"][0].year, 1, 1), "first_dated_event"
        if start > build:
            raise MeasuringReportError(f"horizon_start_in_future: {start} > build date {build}")
    else:
        start, basis = build, "build_date"
    prob = horizon_problem((start, end), birth_date=birth_date)
    if prob:
        raise MeasuringReportError(prob)
    return {"start": start, "end": end, "basis": basis, "excluded_undated": info["excluded"], "readings": info["readings"],
            "flag_exact_but_id_undated": info["flag_exact_but_id_undated"],
            "rows_without_lel_id": info["rows_without_lel_id"],
            "chosen": None if info["chosen"] is None else info["chosen"].get("event_id")}


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
    near_miss_rows_stored: int | None   # rows in the near_miss store; None = the store does not exist (unknown, never 0)
    class_paths_with_rows: frozenset    # {(event_class, path_id)} holding a stored record or window
    marker_classes: frozenset = frozenset()          # the classes the marker says the build was planned for
    marker_schema: str | None = None                 # the marker's schema string
    marker_digest: str | None = None                 # the marker's digest: only its SHAPE (64 lower-case hex) is checked here
    marker_digest_verified: None = None              # ALWAYS None: integrity (the digest equals the writer's own recomputation) is NOT checked by this
    marker_digest_reason: str = MARKER_DIGEST_NOT_CHECKED   # verifier (it must not import the writer): it is the steward's stamp proof at the sitting
    marker_horizon: tuple | None = None              # the marker's own horizon, in clear
    status: str | None = None                        # the publication row's status (candidate | published | superseded | rolled_back ...)


    @property
    def classes_with_records(self) -> frozenset:
        return frozenset(c for c, _ in self.class_paths_with_rows)




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
    if view.status not in (None, "candidate", "published"):
        out.append(f"measuring_status_not_candidate: {view.status!r}")
    if not view.class_paths_with_rows:
        out.append("measuring_build_holds_no_rows: no stored record or window in any class (an empty generation is not a measuring build)")
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
        out.append(f"rule_version_not_in_scope: {bad_versions} (selected today: {sorted(ALLOWED_RULE_VERSIONS)})")
    if view.near_miss_rows_stored:
        out.append(f"near_miss_rows_stored: {view.near_miss_rows_stored} (counts are reported, never stored, §13)")
    # ST-H-UNKNOWN excludes the PATHS P1/P3/P4 of the eight classes, not the classes: P2 rows for them are legitimate today
    excluded_present = sorted((c, p) for c, p in view.class_paths_with_rows if c in EXCLUDED_EIGHT and p in ("P1", "P3", "P4"))
    if excluded_present:
        out.append(f"excluded_path_has_rows: {excluded_present} (ST-H-UNKNOWN excludes P1/P3/P4 for these classes)")
    stray = sorted(set(view.classes_with_records) - SCORED_CLASSES)
    if stray:
        out.append(f"unknown_class_has_rows: {stray}")
    if view.marker_horizon is None or view.marker_schema != MARKER_SCHEMA or not view.marker_digest:
        out.append(f"marker_incomplete: horizon {view.marker_horizon!r}, schema {view.marker_schema!r}, digest {'present' if view.marker_digest else 'absent'}")
    elif not isinstance(view.marker_digest, str) or _DIGEST.fullmatch(view.marker_digest) is None:
        out.append(f"marker_digest_malformed: {str(view.marker_digest)[:20]!r} is not 64 lower-case hex characters")
    missing, extra = sorted(SCORED_CLASSES - set(view.marker_classes)), sorted(set(view.marker_classes) - SCORED_CLASSES)
    if missing or extra:
        out.append(f"class_census_mismatch: the marker names {len(set(view.marker_classes))} classes, missing {missing}, not scored {extra}")
    return out


_SQL_PUBLICATION = ("SELECT status, input_generation_vector, lower(horizon), upper(horizon) FROM public.kala_gochara_publication"
                    " WHERE chart_id = %s AND generation = %s")
_SQL_SEALED = "SELECT count(*) FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s"
_SQL_VERSIONS = ("SELECT rule_version FROM public.ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s"
                 " UNION SELECT rule_version FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s")
_SQL_CLASS_PATHS = ("SELECT event_class, path_id FROM public.ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s"
                    " UNION SELECT event_class, path_id FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s")


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
    class_paths = frozenset(tuple(r.values()) if isinstance(r, dict) else tuple(r)
                            for r in conn.execute(_SQL_CLASS_PATHS, (chart_id, generation, chart_id, generation)).fetchall())
    nm = None                                                       # unknown: the store is absent until the near-miss migration lands
    if _scalar(conn.execute("SELECT to_regclass('public.ka_gochara_near_miss')").fetchone()) is not None:
        nm = int(_scalar(conn.execute("SELECT count(*) FROM public.ka_gochara_near_miss WHERE chart_id = %s AND generation = %s",
                                      (chart_id, generation)).fetchone()))
    mh = marker.get("horizon")
    return MeasuringBuildView(
        stored_scope=(vector or {}).get("stored_scope"), run=marker.get("run"), sealed=sealed, published=status == "published",
        horizon=(h_lo, h_hi), rule_versions=versions, near_miss_rows_stored=nm, class_paths_with_rows=class_paths,
        marker_classes=frozenset(marker.get("classes") or ()), marker_horizon=tuple(mh) if mh else None, status=status,
        marker_schema=marker.get("schema"), marker_digest=marker.get("marker_digest"))


# ── day arithmetic: two conventions, never mixed in one ratio ────────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
_SCORER_H0, _SCORER_H1 = date(1998, 1, 1), date(2026, 4, 17)       # the scorer's own constants (gochara_eval.registry H0 / H1), pinned by a test


@dataclasses.dataclass(frozen=True)
class DayGrid:
    """A day-counting convention: the calendar (`tz`), the instants the grid covers `[lo, hi)` and the denominator in days."""
    label: str
    tz: timezone
    lo: datetime
    hi: datetime
    days: int
    date_inclusive: bool = False         # the SCORER's rule: a window covers the calendar dates from its start's date THROUGH its end's date


def build_grid(horizon) -> DayGrid:
    """The BUILD horizon: UTC calendar dates, half-open `[start, end)` (31,446 days for the pinned chart)."""
    if (prob := horizon_problem(horizon)):
        raise MeasuringReportError(prob)
    return DayGrid("utc_half_open", timezone.utc, datetime(horizon[0].year, horizon[0].month, horizon[0].day, tzinfo=timezone.utc),
                   datetime(horizon[1].year, horizon[1].month, horizon[1].day, tzinfo=timezone.utc), (horizon[1] - horizon[0]).days)


def scored_grid() -> DayGrid:
    """The SCORED horizon in the SCORER's convention (gochara_eval/registry.py:8-21, extract.py:65-67, metrics.py:80-87), for BOTH numerator and
    denominator: IST calendar dates, both endpoints inclusive, 1998-01-01 .. 2026-04-17 = 10,334 days. A stored window (a UTC instant interval)
    covers the IST calendar dates from the date of its START through the date of its END, endpoint dates inclusive (`MergedWindow.days_in_horizon`:
    `(hi - lo).days + 1` over the clipped date pair) — so a window ending exactly at IST midnight still counts the date it ends on. Every number that
    feeds the 40 percent guard uses this grid."""
    lo = datetime(_SCORER_H0.year, _SCORER_H0.month, _SCORER_H0.day, tzinfo=IST)
    hi = datetime(_SCORER_H1.year, _SCORER_H1.month, _SCORER_H1.day, tzinfo=IST) + timedelta(days=1)
    return DayGrid("ist_inclusive", IST, lo, hi, (_SCORER_H1 - _SCORER_H0).days + 1, date_inclusive=True)


def _utc(t: datetime) -> datetime:
    if not isinstance(t, datetime):
        raise MeasuringReportError(f"instant_unreadable: {t!r}")
    if t.tzinfo is None:
        raise MeasuringReportError("naive_datetime: every stored instant is timezone-aware")
    return t.astimezone(timezone.utc)


def _merge(intervals) -> list[tuple[datetime, datetime]]:
    """Merged, sorted INSTANT intervals (UTC); an inverted interval is refused, an empty one dropped."""
    xs = []
    for lo, hi in intervals:
        lo, hi = _utc(lo), _utc(hi)
        if hi < lo:
            raise MeasuringReportError(f"interval_inverted: {lo.isoformat()} > {hi.isoformat()}")
        if lo < hi:
            xs.append((lo, hi))
    xs.sort()
    out: list[list[datetime]] = []
    for lo, hi in xs:
        if out and lo <= out[-1][1]:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return [(a, b) for a, b in out]


def _intersect(a, b) -> list[tuple[datetime, datetime]]:
    """Intersection of two MERGED instant interval lists: instants first, calendar days never (disjoint morning/afternoon intervals share no instant)."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if lo < hi:
            out.append((lo, hi))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def _day_ranges(intervals, grid: DayGrid) -> list[tuple[int, int]]:
    """Merged half-open `[first_day, last_day_exclusive)` ordinal ranges (in the grid's calendar) of the days the intervals admit inside the grid."""
    ranges = []
    for lo, hi in _merge(intervals):
        if not grid.date_inclusive:
            lo, hi = max(lo, grid.lo), min(hi, grid.hi)
            if not lo < hi:
                continue
        l_lo, l_hi = lo.astimezone(grid.tz), hi.astimezone(grid.tz)
        first = l_lo.date().toordinal()
        midnight = datetime(l_hi.year, l_hi.month, l_hi.day, tzinfo=grid.tz)
        last_excl = l_hi.date().toordinal() + (1 if grid.date_inclusive or l_hi != midnight else 0)
        if grid.date_inclusive:                                         # clip the DATE pair to the scorer's inclusive [H0, H1]
            first, last_excl = max(first, _SCORER_H0.toordinal()), min(last_excl, _SCORER_H1.toordinal() + 1)
            if first >= last_excl:
                continue
        ranges.append((first, last_excl))
    ranges.sort()
    merged: list[list[int]] = []
    for a, b in ranges:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


def admitted_days(intervals, horizon_or_grid) -> int:
    grid = horizon_or_grid if isinstance(horizon_or_grid, DayGrid) else build_grid(horizon_or_grid)
    return sum(b - a for a, b in _day_ranges(intervals, grid))


def horizon_days(horizon) -> int:
    return (horizon[1] - horizon[0]).days


def _day_set(intervals, grid: DayGrid) -> set[int]:
    out: set[int] = set()
    for a, b in _day_ranges(intervals, grid):
        out.update(range(a, b))
    return out


def length_distribution(lengths_days) -> dict:
    """count, median, p90 (nearest rank: the ceil(0.9 n)-th smallest), max — all None when there is no window
    (an honest null, never a zero). Every length must be finite."""
    xs = sorted(lengths_days)
    if any(not math.isfinite(x) for x in xs):
        raise MeasuringReportError("length_not_finite")
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
    'karakatva' (FB-46, P1), 'dvi' (FB-41, P4), 'kb' (FB-37, luminary target). `role` must be `scored`: an admitted TESTIMONY record never
    counts toward a scored share (it changes no admission), so the report refuses one by name. Any other tag is refused."""
    event_class: str
    path: str
    agent: str
    supports: tuple
    via: str = "base"
    role: str = "scored"


def _union(records, pred):
    return _merge([iv for r in records if pred(r) for iv in r.supports])


def _p4_instants(rs, vias) -> list[tuple[datetime, datetime]]:
    """P4 is the INTERSECTION, at the instant level, of Jupiter's and Saturn's influence unions (window_store.py:199-220; migration 1240:280-299):
    each agent's records (of the allowed `vias`) are unioned first, then the two unions are intersected."""
    jup = _union(rs, lambda r: r.path == "P4" and r.agent == "jupiter" and r.via in vias)
    sat = _union(rs, lambda r: r.path == "P4" and r.agent == "saturn" and r.via in vias)
    return _intersect(jup, sat)


def _class_instants(rs) -> list[tuple[datetime, datetime]]:
    """The COMPLETE class admission (every via) of the records `rs`: P1 (all), P2, P3 (base + K-B) and the P4 intersection (with DVI and K-B)."""
    return _merge([*_union(rs, lambda r: r.path == "P1"), *_union(rs, lambda r: r.path == "P2"), *_union(rs, lambda r: r.path == "P3"),
                   *_p4_instants(rs, ("base", "kb", "dvi"))])


def _report(records, windows, grid: DayGrid) -> dict:
    for r in records:
        if r.path not in PATHS:
            raise MeasuringReportError(f"unknown_path: {r.path!r}")
        if r.agent not in ALL_AGENTS:
            raise MeasuringReportError(f"unknown_agent: {r.agent!r} (the nine, lower-case)")
        if r.via not in VIAS:
            raise MeasuringReportError(f"unknown_via: {r.via!r}")
        if r.path not in VIA_PATHS[r.via]:
            raise MeasuringReportError(f"via_not_valid_for_path: {r.via!r} in {r.path}")
        if r.role != "scored":
            raise MeasuringReportError(f"testimony_record_in_scored_share: role {r.role!r} ({r.event_class} {r.path} {r.agent})")
        if r.path == "P4" and r.agent not in P4_AGENTS:
            raise MeasuringReportError(f"p4_agent_not_jupiter_or_saturn: {r.agent!r}")
    for w in windows:
        if w[1] not in PATHS:
            raise MeasuringReportError(f"unknown_path: {w[1]!r} (window)")
    classes = sorted({r.event_class for r in records} | {w[0] for w in windows})
    out = {}
    for cls in classes:
        rs = [r for r in records if r.event_class == cls]

        def days(instants) -> int:
            return sum(b - a for a, b in _day_ranges(instants, grid))

        p1_base = _union(rs, lambda r: r.path == "P1" and r.via == "base")
        p1_all = _union(rs, lambda r: r.path == "P1")
        p2 = _union(rs, lambda r: r.path == "P2")
        p3_base = _union(rs, lambda r: r.path == "P3" and r.via == "base")
        p3_all = _union(rs, lambda r: r.path == "P3")                                  # base + kb
        p4_wo = _p4_instants(rs, ("base", "kb"))
        p4_with = _p4_instants(rs, ("base", "kb", "dvi"))
        p4_nokb = _p4_instants(rs, ("base", "dvi"))
        union_all = _merge([*p1_all, *p2, *p3_all, *p4_with])
        union_nokb = _merge([*p1_all, *p2, *p3_base, *p4_nokb])
        shares = {
            "P1_base": days(p1_base),
            "P1_with_karakatva": days(p1_all),
            "P2": days(p2),
            "P3_fast": days(_union(rs, lambda r: r.path == "P3" and r.via in ("base", "kb") and r.agent in FAST_AGENTS)),
            "P3_slow": days(_union(rs, lambda r: r.path == "P3" and r.via in ("base", "kb") and r.agent in SLOW_AGENTS)),
            "P3_union": days(p3_all),
            "P4_without_dvi": days(p4_wo),
            "P4_with_dvi": days(p4_with),
            "kb_only": len(_day_set(union_all, grid) - _day_set(union_nokb, grid)),
            "class_union": days(union_all),
        }
        per_agent = {}
        all_days = _day_set(union_all, grid)
        for agent in sorted({r.agent for r in rs}):
            mine = _day_set(_union(rs, lambda r, a=agent: r.path != "P4" and r.agent == a), grid)
            others = _day_set(_union(rs, lambda r, a=agent: r.path != "P4" and r.agent != a), grid)
            # `exclusive_days`: P1-P3 records only, against the other agents' P1-P3 records (diagnostic). `exclusive_days_vs_class`: the days of COMPLETE
            # class admission that disappear when this agent's records are REMOVED — its P1-P3 records AND its P4 influence (removing Jupiter breaks
            # the P4 intersection too), recomputed from scratch
            rest = [r for r in rs if r.agent != agent]
            without = _day_set(_class_instants(rest), grid)
            per_agent[agent] = {"days": len(mine), "exclusive_days": len(mine - others), "exclusive_days_vs_class": len(all_days - without)}
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
            "admitted_share": {k: v / grid.days for k, v in shares.items()},
            "window_lengths_days": lengths,
            "per_agent": per_agent,
            "P4_joint": {"without_dvi_days": shares["P4_without_dvi"], "with_dvi_days": shares["P4_with_dvi"]},
        }
    return {"convention": grid.label, "horizon": [grid.lo.astimezone(grid.tz).date().isoformat(),
                                                   (grid.hi.astimezone(grid.tz) - (timedelta(days=1) if grid.label == "ist_inclusive" else timedelta(0))).date().isoformat()],
            "horizon_days": grid.days, "classes": out}


def class_share_report(records, windows, horizon) -> dict:
    """FB-50 items 1-3 over the BUILD horizon (UTC calendar dates, half-open; `convention` = 'utc_half_open'), per class: admitted-day shares by
    path and variant, the class union, K-B exclusive days, window-length distribution per path, per-agent contribution (P1-P3 records; P4's
    admission is joint). P4 is the intersection of Jupiter's and Saturn's influence unions at the instant level. `records`: SupportRecord
    (scored, admitted); `windows`: (event_class, path, lo, hi) stored windows. Refused by name: an unknown path / agent / via, a (via, path)
    pair that cannot exist, a testimony record, a P4 agent other than Jupiter/Saturn, an inverted interval — a silent zero in the fast/slow
    shares would feed the per-class fast-planet decision."""
    return _report(records, windows, build_grid(horizon))


def scored_share_report(records, windows) -> dict:
    """The same report over the SCORED horizon in the scorer's convention (IST calendar dates, inclusive, 10,334 days; `convention` =
    'ist_inclusive'). THIS is the report every 40 percent comparison uses. Its shares and `class_share_report`'s are on different grids and are
    never to be mixed in one ratio."""
    return _report(records, windows, scored_grid())


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
    " WHERE r.chart_id = %s AND r.generation = %s AND r.admission_state = 'admitted' AND r.operator_role = 'scored'"
    " ORDER BY r.record_id, lower(s.x)")


def read_records(conn, chart_id: str, generation: str) -> list[SupportRecord]:
    """Admitted stored records of a generation as SupportRecord. The `via` tag is NOT defaulted: a stored row is `base`
    only because its rule_version is one SELECTED today (a selected row carries no extension), and any other version is refused
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
