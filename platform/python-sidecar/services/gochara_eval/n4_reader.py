"""N4 post-build reader: 5.x extractor with IST-inclusive clipping, digest-pinned scorer, five-endpoint comparison (post-build tooling).

Sources: FINAL_BUILD_SCOPE_v1_0 FB-5 (the extractor reads the eval-window tables and clips for scoring only; the stored window is untouched)
and FB-60 (the five endpoints on the final generation beside the 3.0 baseline); MEASURING_BUILD_CONTRACT_v1_0 MB-5.2 (the scored horizon is IST
calendar dates, both ends inclusive, 1998-01-01..2026-04-17 = 10,334 days; a stored UTC interval [lo, hi) admits IST day D iff it overlaps
[D 00:00 IST, D+1 00:00 IST) by positive length) and MB-5.4 (the scoring oracle moves to the first numerical build); SR-F5-41-DEFER (4.1 is
not a comparator for this campaign).

Three claims, each with its own detector:
  1. CLIP    `clip_to_scored_horizon` keeps every window that touches an IST day of [H0, H1] (the boundary day 2026-04-17 included) and clips
             `ws`/`we` to it; everything outside is COUNTED, never silently dropped.
  2. SCORER  the scoring core (`SCORER_FILES`) is FROZEN: `require_pinned_scorer` recomputes its digest and REFUSES, before any extract is
             opened, when it differs from `PINNED_SCORER_DIGEST`. Editing a scorer file is a deliberate act that re-pins this constant.
  3. COMPARE `compare_endpoints` lays the five endpoints of 5.0 beside 3.0 from the scorers' own verdict blocks (no recomputation, no null -> 0);
             the report header states the 4.1 deferral and carries no 4.1 column.

A trial read (no verified Stage-1/Stage-2 freeze on the 5.0 result) is labelled `trial_read_not_a_measurement`; only a result whose own
`mode == MEASUREMENT` and `freeze.status == VERIFIED` is graded `measurement` (the real measurement stays `candidate_score`, which verifies the freeze).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

from .candidate import load_candidate_extract_bytes, score_candidate
from .dump_extract import GOVERNED_COLUMNS, _require_read_only, render
from .extract import InputRejected
from .qualification import ENDPOINTS, endpoint_records
from .registry import H0, H1, RegistryError, load_registry

READER_SCHEMA = "ky.n4_reader/1"
DEFER_HEADER = "4.1 not built for this campaign (deferred by SR-F5-41-DEFER); no substitute baseline"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SIDECAR_ROOT = Path(__file__).resolve().parents[2]
#: the scoring core: adapter, unknown-si bounds, merge, endpoint metrics, registry and controls. The reader and the dump are NOT in it (they may evolve).
SCORER_FILES = tuple(f"services/gochara_eval/{n}.py" for n in ("candidate", "controls", "extract", "metrics", "registry", "unknowns"))
#: sha256 over the sorted "<path> <file sha256>" lines of SCORER_FILES, as at the commit that introduced this reader
PINNED_SCORER_DIGEST = "2a90097124731cc0a9dbb35212f7e98a4753e8974a788420ce6a9e766913f220"

#: raw eval-window row: (event_class, lower, upper, peak_instant, evidence_for, outcome_valence_for_native, path_id, null_reason); lower/upper/peak are tz-aware UTC
RAW_COLUMNS = ("event_class", "lower", "upper", "peak_instant", "evidence_for", "outcome_valence_for_native", "path_id", "null_reason")
SQL_RAW = """SELECT w.event_class, lower(w.interval), upper(w.interval), w.peak_instant, w.evidence_for,
       w.outcome_valence_for_native, w.path_id, w.qualification ->> 'unqualified_reason'
  FROM public.ka_gochara_eval_window w
 WHERE w.chart_id = %s AND w.generation = %s
 ORDER BY w.event_class, lower(w.interval), upper(w.interval), w.peak_instant, w.evidence_for, w.outcome_valence_for_native, w.path_id,
          w.qualification ->> 'unqualified_reason'"""


class ReaderRefused(RuntimeError):
    """The reader refuses to run or to report (frozen scorer drifted, malformed window, identity mismatch)."""


# ---- claim 2: the frozen scorer --------------------------------------------------------------------------------------------------
def scorer_digest(sidecar_root: Path = SIDECAR_ROOT) -> dict:
    """{files: {path: sha256}, digest}; a missing scoring file is a refusal, never a smaller digest."""
    files = {}
    for rel in SCORER_FILES:
        p = Path(sidecar_root) / rel
        if not p.is_file():
            raise ReaderRefused(f"SCORER REFUSED: scoring file {rel} is missing")
        files[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    lines = "\n".join(f"{rel} {files[rel]}" for rel in sorted(files))
    return {"files": files, "digest": hashlib.sha256(lines.encode()).hexdigest()}


def require_pinned_scorer(sidecar_root: Path = SIDECAR_ROOT, pinned: str = PINNED_SCORER_DIGEST) -> dict:
    live = scorer_digest(sidecar_root)
    if live["digest"] != pinned:
        raise ReaderRefused(f"SCORER REFUSED: the frozen scoring core changed (live {live['digest']}, pinned {pinned}); "
                            "re-pin deliberately before reading")
    return {"pinned": pinned, "live": live["digest"], "match": True, "files": live["files"]}


# ---- claim 1: IST-inclusive clipping ---------------------------------------------------------------------------------------------
def ist_days(lower: dt.datetime, upper: dt.datetime) -> tuple[dt.date, dt.date]:
    """First and last IST calendar day a stored UTC half-open [lower, upper) overlaps by positive length (MB-5.2). An upper bound at exactly
    00:00 IST belongs to the NEXT day, so the last instant is upper - 1 microsecond (the day convention of dump_extract.SQL_GOVERNED_DUMP)."""
    for v in (lower, upper):
        if not isinstance(v, dt.datetime) or v.tzinfo is None:
            raise ReaderRefused("window bounds must be timezone-aware datetimes")
    if upper <= lower:
        raise ReaderRefused("empty or inverted window interval")
    return lower.astimezone(IST).date(), (upper - dt.timedelta(microseconds=1)).astimezone(IST).date()


def clip_to_scored_horizon(raw_rows: list[tuple], h0: dt.date = H0, h1: dt.date = H1) -> tuple[list[dict], dict]:
    """Raw eval-window rows -> candidate-adapter rows (GOVERNED_COLUMNS, IST dates), clipped to the INCLUSIVE IST range [h0, h1] for scoring only.

    A window that touches any IST day of [h0, h1] is kept and its `ws`/`we` are clipped to the range; the peak and `si` are the stored values
    (a peak outside the range is counted, not moved). `si` NULL stays NULL with its stored reason. Output has a total order. Counts: every
    window is read, kept or excluded (before/after), so nothing leaves unrecorded."""
    out, c = [], {"windows_read": 0, "windows_kept": 0, "excluded_before_horizon": 0, "excluded_after_horizon": 0,
                  "clipped_at_start": 0, "clipped_at_end": 0, "peak_outside_horizon": 0}
    for raw in raw_rows:
        cls, lower, upper, peak, si, valence, path_id, reason = raw
        c["windows_read"] += 1
        first, last = ist_days(lower, upper)
        if last < h0:
            c["excluded_before_horizon"] += 1
            continue
        if first > h1:
            c["excluded_after_horizon"] += 1
            continue
        ws, we = max(first, h0), min(last, h1)
        c["clipped_at_start"] += ws != first
        c["clipped_at_end"] += we != last
        pk = None if peak is None else peak.astimezone(IST).date()
        if pk is not None and not (h0 <= pk <= h1):
            c["peak_outside_horizon"] += 1
        out.append({"event_class": cls, "ws": ws.isoformat(), "we": we.isoformat(), "pk": None if pk is None else pk.isoformat(),
                    "si": None if si is None else float(si), "outcome_valence_for_native": valence, "path_id": path_id,
                    "null_reason": reason})
        c["windows_kept"] += 1
    out.sort(key=lambda r: tuple((v is None, v if v is not None else 0) for v in (r[k] for k in GOVERNED_COLUMNS)))
    return out, c


def read_raw_windows(conn, generation: str, chart_id: str) -> list[tuple]:
    """Read-only SELECT of the stored governed windows of one chart and generation (a candidate may be unsealed; no publication is consulted)."""
    _require_read_only(conn)
    with conn.cursor() as cur:
        cur.execute(SQL_RAW, (chart_id, generation))
        return [tuple(r) for r in cur.fetchall()]


def build_extract(raw_rows: list[tuple], *, generation: str, chart_id: str, pinned_at: str) -> tuple[bytes, dict]:
    rows, counts = clip_to_scored_horizon(raw_rows)
    extra = {"scored_horizon": [H0.isoformat(), H1.isoformat()], "horizon_convention": "IST calendar dates, both ends inclusive (MB-5.2)",
             "clip": counts}
    return render(generation, pinned_at, rows, chart_id=chart_id, extra=extra), counts


# ---- scoring (the frozen core) ---------------------------------------------------------------------------------------------------
def score_extract(raw: bytes, registry_path: str | Path, *, declared_pin: str | None = None) -> dict:
    """The candidate scorer over extract bytes; the result carries the same endpoint blocks as `candidate_score`. NOT a verified-freeze measurement:
    `mode` is TRIAL_READ unless the caller replaces it with a result of `candidate_score`'s MEASUREMENT mode."""
    try:
        cext = load_candidate_extract_bytes(raw, declared_pin)
        registry = load_registry(registry_path)
    except (InputRejected, RegistryError) as exc:
        raise ReaderRefused(f"INPUT REFUSED: {exc}") from exc
    result = {"artifact": "n4_read_result", "mode": "TRIAL_READ", "extract_sha256": cext.sha256, "dedup_table": cext.dedup_table,
              "input_adapter": {"status": "PASS", "raw_row_count": cext.row_count, "unknown_si_rows": cext.unknown_rows,
                                "null_reasons": cext.null_reasons},
              "source_reconciliation": registry.reconciliation}
    result.update(score_candidate(registry, cext))
    return result


# ---- claim 3: the five-endpoint comparison ---------------------------------------------------------------------------------------
def evidence_grade(result: dict) -> str:
    """`measurement` only when the result itself says a verified freeze bound the run; never inferred from presence of numbers."""
    if result.get("mode") == "MEASUREMENT" and (result.get("freeze") or {}).get("status") == "VERIFIED":
        return "measurement"
    return "trial_read_not_a_measurement"


def compare_endpoints(result_5: dict, result_3: dict) -> dict:
    """The five endpoints of 5.0 beside 3.0, from each scorer's own verdict block (qualification.endpoint_records: nothing recomputed,
    a null stays a null). `relation` is `same` / `differs` only when both statuses are pass|fail, else `incomparable`."""
    e5, e3 = endpoint_records(result_5), endpoint_records(result_3)
    table = {}
    for name in ENDPOINTS:
        s5, s3 = e5[name]["status"], e3[name]["status"]
        decided = {"pass", "fail"}
        table[name] = {"5.0": e5[name], "3.0": e3[name],
                       "relation": ("incomparable" if not (s5 in decided and s3 in decided) else "same" if s5 == s3 else "differs")}
    return {"header": DEFER_HEADER, "evidence_grade_5_0": evidence_grade(result_5), "endpoints": table}


def run_reader(raw_rows: list[tuple], *, generation: str, chart_id: str, pinned_at: str, registry_path: str | Path,
               baseline_extract: Path | str, baseline_pin: str, sidecar_root: Path = SIDECAR_ROOT,
               pinned_scorer: str = PINNED_SCORER_DIGEST) -> dict:
    """Frozen-scorer check FIRST (before any extract is opened), then clip -> extract -> score 5.0 and the 3.0 baseline -> compare."""
    pin = require_pinned_scorer(sidecar_root, pinned_scorer)
    extract, clip = build_extract(raw_rows, generation=generation, chart_id=chart_id, pinned_at=pinned_at)
    r5 = score_extract(extract, registry_path)
    r3 = score_extract(Path(baseline_extract).read_bytes(), registry_path, declared_pin=baseline_pin)
    return {"schema": READER_SCHEMA, "header": DEFER_HEADER, "chart_id": chart_id, "generation": generation,
            "scorer": {k: pin[k] for k in ("pinned", "live", "match")}, "clip": clip,
            "extract_sha256": hashlib.sha256(extract).hexdigest(), "comparison": compare_endpoints(r5, r3),
            "results": {"5.0": r5, "3.0": r3}}


def render_markdown(report: dict) -> str:
    cmp_ = report["comparison"]
    lines = [f"# N4 post-build reader — generation {report['generation']}", "", f"**{report['header']}**", "",
             f"Evidence grade of the 5.0 read: `{cmp_['evidence_grade_5_0']}`. Scorer digest {report['scorer']['live']} (pinned, match).", "",
             "| Endpoint | 5.0 | 3.0 | Relation |", "|---|---|---|---|"]
    lines += [f"| {n} | {v['5.0']['status']} | {v['3.0']['status']} | {v['relation']} |" for n, v in cmp_["endpoints"].items()]
    c = report["clip"]
    lines += ["", f"Clip to IST 1998-01-01..2026-04-17 inclusive: {c['windows_read']} read, {c['windows_kept']} kept, "
                  f"{c['excluded_before_horizon']} before, {c['excluded_after_horizon']} after, "
                  f"{c['clipped_at_start']} clipped at start, {c['clipped_at_end']} clipped at end.", ""]
    return "\n".join(lines)


def _decode_rows(path: str) -> list[tuple]:
    """Trial-fixture rows from JSON: each row is the RAW_COLUMNS in order, bounds as ISO-8601 with an offset."""
    def ts(v):
        return None if v is None else dt.datetime.fromisoformat(v)
    return [(r[0], ts(r[1]), ts(r[2]), ts(r[3]), r[4], r[5], r[6], r[7]) for r in json.loads(Path(path).read_text())]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="n4_reader", description=__doc__)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--baseline-extract", required=True)
    ap.add_argument("--baseline-pin", required=True)
    ap.add_argument("--generation", default="5.0")
    ap.add_argument("--chart-id", required=True)
    ap.add_argument("--pinned-at", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--markdown")
    ap.add_argument("--rows-json", help="TRIAL fixture rows (no database)")
    ap.add_argument("--libpq-env", action="store_true", help="read the stored windows with the libpq PG* variables (read-only snapshot)")
    args = ap.parse_args(argv)
    try:
        if args.rows_json:
            raw_rows = _decode_rows(args.rows_json)
        else:
            from .dump_extract import _connect
            conn = _connect(args, None)
            if conn is None:
                return 2
            try:
                raw_rows = read_raw_windows(conn, args.generation, args.chart_id)
            finally:
                conn.rollback()
                conn.close()
        report = run_reader(raw_rows, generation=args.generation, chart_id=args.chart_id, pinned_at=args.pinned_at,
                            registry_path=args.registry, baseline_extract=args.baseline_extract, baseline_pin=args.baseline_pin)
    except (ReaderRefused, OSError, ValueError) as exc:
        print(f"N4 reader refused: {exc}", file=sys.stderr)
        return 2
    Path(args.output).write_text(json.dumps(report, indent=1, allow_nan=False) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
