"""N4 post-build reader: IST-inclusive clipping, the digest-pinned scorer, the five-endpoint comparison (TRIAL FIXTURES only).

Every window, event and result below is a synthetic FIXTURE built in this file: none is a window or a life event of the native, and no figure here
is a measurement of a generation. Oracle sources:
  * CLIP    — MEASURING_BUILD_CONTRACT_v1_0 MB-5.2: the scored horizon is IST calendar dates, both ends inclusive (1998-01-01..2026-04-17 = 10,334
              days); a stored UTC interval [lo, hi) admits IST day D iff it overlaps [D 00:00 IST, D+1 00:00 IST) by positive length. FB-5: clip for
              scoring only. Protocol v2.3 §3: event dates are IST calendar dates, inclusive.
  * SCORER  — SI addendum §5 / freeze.py FROZEN_CODE_FILES: the scoring code is frozen and its identity is checked, not asserted (§N.8).
  * COMPARE — FB-60 (the five endpoints beside the 3.0 baseline); SR-F5-41-DEFER (no 4.1 comparator, no substitute baseline); §N.7.6 (an honest
              null stays null).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from services.gochara_eval import n4_reader as n4
from services.gochara_eval.qualification import ENDPOINTS

from .conftest import synth_registry, write_json

UTC = dt.timezone.utc
D = dt.date
CHART = "00000000-0000-4000-8000-000000000001"     # FIXTURE chart id, not the native's
REASON = "dynamic_objective_solver_guarantee_not_available"
MIDNIGHT_IST_0417 = dt.datetime(2026, 4, 16, 18, 30, tzinfo=UTC)    # 2026-04-17 00:00 IST
MIDNIGHT_IST_0101 = dt.datetime(1997, 12, 31, 18, 30, tzinfo=UTC)   # 1998-01-01 00:00 IST
US = dt.timedelta(microseconds=1)


def raw(cls, lower, upper, peak=None, si=0.9, valence="favourable", path="P3", reason=None):
    return (cls, lower, upper, peak, si, valence, path, reason)


def clip(rows):
    return n4.clip_to_scored_horizon(rows)


# ---- claim 1: IST-inclusive clipping (MB-5.2) -------------------------------------------------------------------------------------
def test_boundary_day_2026_04_17_ist_is_inside_the_scored_horizon():
    # the window opens at 00:00 IST on 2026-04-17: a one-day IST window ON the last scored day. A half-open `< 2026-04-17` clip (FB-5's wording,
    # ruled wrong by MB-5.2) would drop it.
    rows, c = clip([raw("career_advancement", MIDNIGHT_IST_0417, MIDNIGHT_IST_0417 + dt.timedelta(days=1), MIDNIGHT_IST_0417 + dt.timedelta(hours=5))])
    assert [(r["ws"], r["we"]) for r in rows] == [("2026-04-17", "2026-04-17")]
    assert c["windows_kept"] == 1 and c["excluded_after_horizon"] == 0


def test_first_day_after_the_horizon_is_excluded_and_counted():
    nxt = MIDNIGHT_IST_0417 + dt.timedelta(days=1)       # 2026-04-18 00:00 IST
    rows, c = clip([raw("career_advancement", nxt, nxt + dt.timedelta(days=3), nxt)])
    assert rows == [] and c["excluded_after_horizon"] == 1 and c["windows_read"] == 1


def test_upper_bound_at_ist_midnight_belongs_to_the_next_day_not_this_one():
    # [lo, 2026-04-17 00:00 IST) overlaps IST 04-16 only: the last instant is hi - 1 µs. Counting 04-17 would widen the window by a day.
    lo = MIDNIGHT_IST_0417 - dt.timedelta(days=2)
    rows, _ = clip([raw("career_advancement", lo, MIDNIGHT_IST_0417, lo)])
    assert rows[0]["we"] == "2026-04-16"
    rows, _ = clip([raw("career_advancement", lo, MIDNIGHT_IST_0417 + US, lo)])
    assert rows[0]["we"] == "2026-04-17"                # one microsecond past IST midnight touches the boundary day


def test_start_boundary_1998_01_01_ist_inclusive_and_the_day_before_excluded():
    before, c = clip([raw("career_advancement", MIDNIGHT_IST_0101 - dt.timedelta(days=5), MIDNIGHT_IST_0101, None, si=None, valence="unqualified")])
    assert before == [] and c["excluded_before_horizon"] == 1       # last instant is 1997-12-31 IST
    rows, c = clip([raw("career_advancement", MIDNIGHT_IST_0101 - dt.timedelta(days=5), MIDNIGHT_IST_0101 + US, None, si=None)])
    assert rows[0]["ws"] == "1998-01-01" and rows[0]["we"] == "1998-01-01" and c["clipped_at_start"] == 1


def test_straddling_window_is_clipped_for_scoring_and_the_peak_is_kept_and_counted():
    lo, hi = MIDNIGHT_IST_0417 - dt.timedelta(days=10), MIDNIGHT_IST_0417 + dt.timedelta(days=40)
    peak = MIDNIGHT_IST_0417 + dt.timedelta(days=5)
    rows, c = clip([raw("relocation", lo, hi, peak, si=0.4)])
    assert (rows[0]["ws"], rows[0]["we"], rows[0]["pk"]) == ("2026-04-07", "2026-04-17", "2026-04-22")
    assert c["clipped_at_end"] == 1 and c["peak_outside_horizon"] == 1 and rows[0]["si"] == 0.4


def test_null_si_stays_null_with_its_stored_reason_and_decimal_si_becomes_float():
    lo = dt.datetime(2015, 3, 1, tzinfo=UTC)
    rows, _ = clip([raw("relocation", lo, lo + dt.timedelta(days=3), None, si=None, valence="unqualified", reason=REASON),
                    raw("relocation", lo + dt.timedelta(days=9), lo + dt.timedelta(days=11), lo + dt.timedelta(days=10), si=Decimal("0.25"))])
    nul = next(r for r in rows if r["si"] is None)
    assert nul["pk"] is None and nul["null_reason"] == REASON
    assert next(r for r in rows if r["si"] is not None)["si"] == 0.25


def test_naive_or_empty_intervals_are_refused():
    with pytest.raises(n4.ReaderRefused):
        n4.ist_days(dt.datetime(2010, 1, 1), dt.datetime(2010, 1, 2))
    with pytest.raises(n4.ReaderRefused):
        n4.ist_days(MIDNIGHT_IST_0417, MIDNIGHT_IST_0417)


def test_output_order_is_total_and_independent_of_input_order():
    lo = dt.datetime(2010, 4, 1, tzinfo=UTC)
    rows = [raw("relocation", lo, lo + dt.timedelta(days=2), lo, si=0.5, path="P2"),
            raw("relocation", lo, lo + dt.timedelta(days=2), lo, si=0.5, path="P1"),
            raw("career_advancement", lo, lo + dt.timedelta(days=2), None, si=None, valence="unqualified", path="P4", reason=REASON)]
    assert clip(rows)[0] == clip(list(reversed(rows)))[0]


# ---- end to end on fixtures ---------------------------------------------------------------------------------------------------------
def registry_with_boundary_event(tmp_path: Path) -> Path:
    events = [
        {"eid": "EVT.2013.12.11.01", "tier": "dev", "obs_type": "point", "grain": "exact", "date": "2013-12-11", "class": "marriage"},
        {"eid": "EVT.2018.11.28.01", "tier": "dev", "obs_type": "point", "grain": "exact", "date": "2018-11-28", "class": "bereavement"},
        {"eid": "EVT.2022.01.03.01", "tier": "dev", "obs_type": "point", "grain": "exact", "date": "2022-01-03", "class": "career_entry"},
        # FIXTURE held-out event ON the last scored IST day
        {"eid": "EVT.2026.04.17.01", "tier": "held_out_timing", "obs_type": "point", "grain": "exact", "date": "2026-04-17",
         "class": "career_advancement"},
        {"eid": "EVT.2015.XX.XX.01", "tier": "held_out_year", "obs_type": "point", "grain": "year", "date": "2015", "class": "relocation"},
        {"eid": "EVT.CURRENT.01", "tier": "excluded", "obs_type": "status", "grain": "exact", "date": "2024-01-01", "class": "chronic_onset"},
    ]
    return write_json(tmp_path / "registry.json", synth_registry(events))


def baseline_3_0(tmp_path: Path) -> tuple[Path, str]:
    doc = {"artifact": "baseline_3_0_extract", "version": "1.0", "predicate": "kala_gochara_windows where generation='3.0'", "rows": [
        {"event_class": "relocation", "ws": "2015-03-01", "we": "2015-04-01", "pk": "2015-03-10", "si": 0.5, "valence": "gain"}]}
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps(doc, indent=1))
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def boundary_rows():
    return [raw("career_advancement", MIDNIGHT_IST_0417, MIDNIGHT_IST_0417 + dt.timedelta(days=1), MIDNIGHT_IST_0417 + dt.timedelta(hours=3), si=0.8),
            raw("relocation", dt.datetime(2015, 3, 1, tzinfo=UTC), dt.datetime(2015, 4, 1, tzinfo=UTC), dt.datetime(2015, 3, 10, tzinfo=UTC), si=0.6)]


def test_boundary_day_window_reaches_the_scorer_and_covers_the_boundary_event(tmp_path):
    reg = registry_with_boundary_event(tmp_path)
    base, pin = baseline_3_0(tmp_path)
    report = n4.run_reader(boundary_rows(), generation="5.0", chart_id=CHART, pinned_at="2026-10-22", registry_path=reg,
                           baseline_extract=base, baseline_pin=pin)
    assert report["clip"]["windows_kept"] == 2 and report["clip"]["excluded_after_horizon"] == 0
    assert report["results"]["5.0"]["t_cover"]["hits"] == 2          # the boundary event AND the 2015 year event are both inside a kept window
    # the same read WITHOUT the boundary-day window covers one event fewer: the endpoint genuinely moves with the clip convention
    report2 = n4.run_reader(boundary_rows()[1:], generation="5.0", chart_id=CHART, pinned_at="2026-10-22", registry_path=reg,
                            baseline_extract=base, baseline_pin=pin)
    assert report2["results"]["5.0"]["t_cover"]["hits"] == 1


# ---- claim 2: the frozen scorer --------------------------------------------------------------------------------------------------
def scorer_copy(tmp_path: Path) -> Path:
    root = tmp_path / "sidecar_copy"
    for rel in n4.SCORER_FILES:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(n4.SIDECAR_ROOT / rel, root / rel)
    return root


def test_the_live_scoring_core_equals_the_pinned_digest():
    got = n4.require_pinned_scorer()
    assert got["match"] is True and got["live"] == n4.PINNED_SCORER_DIGEST


def test_a_drifted_scoring_file_refuses_before_any_extract_is_opened(tmp_path):
    root = scorer_copy(tmp_path)
    assert n4.require_pinned_scorer(root)["match"] is True           # an unmodified copy passes: the refusal below is the edit's doing
    metrics = root / "services/gochara_eval/metrics.py"
    metrics.write_text(metrics.read_text() + "\n# drift\n")
    with pytest.raises(n4.ReaderRefused, match="SCORER REFUSED"):
        n4.require_pinned_scorer(root)
    # run_reader must stop at the pin: a missing registry/baseline would otherwise raise a different error first
    with pytest.raises(n4.ReaderRefused, match="SCORER REFUSED"):
        n4.run_reader([], generation="5.0", chart_id=CHART, pinned_at="x", registry_path=tmp_path / "none.json",
                      baseline_extract=tmp_path / "none.json", baseline_pin="0" * 64, sidecar_root=root)


def test_a_missing_scoring_file_refuses_rather_than_shrinking_the_digest(tmp_path):
    root = scorer_copy(tmp_path)
    (root / "services/gochara_eval/unknowns.py").unlink()
    with pytest.raises(n4.ReaderRefused, match="missing"):
        n4.require_pinned_scorer(root)


# ---- claim 3: the five-endpoint comparison ---------------------------------------------------------------------------------------
def result(**blocks):
    base = {"t_cover": {"pass": True, "hits": 9}, "t_time": {"pass": True, "capped_median_range": [10, 10]},
            "t_rank": {"status": "UNQUALIFIED", "pass": None}, "t_fp_overall": {"pass": False}, "t_honesty": {"status": "PASS", "pass": True}}
    return {**base, **blocks}


def test_comparison_names_exactly_the_five_endpoints_and_the_4_1_deferral():
    cmp_ = n4.compare_endpoints(result(), result(t_cover={"pass": False, "hits": 3}))
    assert tuple(cmp_["endpoints"]) == ENDPOINTS == ("t_cover", "t_time", "t_rank", "t_fp", "t_honesty")
    assert cmp_["header"] == "4.1 not built for this campaign (deferred by SR-F5-41-DEFER); no substitute baseline"
    for row in cmp_["endpoints"].values():
        assert set(row) == {"5.0", "3.0", "relation"}                 # no 4.1 column anywhere
    assert "4.1" not in json.dumps(cmp_["endpoints"])


def test_relation_same_differs_incomparable_and_originals_are_retained_unrecomputed():
    cmp_ = n4.compare_endpoints(result(), result(t_cover={"pass": False, "hits": 3}))
    ep = cmp_["endpoints"]
    assert ep["t_cover"]["relation"] == "differs" and ep["t_cover"]["3.0"]["measured"] == {"pass": False, "hits": 3}
    assert ep["t_time"]["relation"] == "same"
    assert ep["t_rank"]["relation"] == "incomparable" and ep["t_rank"]["5.0"]["status"] == "insufficient_evidence"
    assert ep["t_rank"]["5.0"]["measured"] == {"status": "UNQUALIFIED", "pass": None}


def test_a_missing_endpoint_block_is_an_honest_null_never_a_pass():
    r = result()
    del r["t_time"]
    row = n4.compare_endpoints(r, result())["endpoints"]["t_time"]
    assert row["5.0"]["status"] == "insufficient_evidence" and row["5.0"]["measured"] is None and row["relation"] == "incomparable"


def test_evidence_grade_comes_from_the_results_own_verified_freeze_not_from_having_numbers():
    assert n4.evidence_grade({"mode": "TRIAL_READ"}) == "trial_read_not_a_measurement"
    assert n4.evidence_grade({"mode": "MEASUREMENT", "freeze": {"status": "NOT_BOUND"}}) == "trial_read_not_a_measurement"
    assert n4.evidence_grade({"mode": "MEASUREMENT"}) == "trial_read_not_a_measurement"
    assert n4.evidence_grade({"mode": "MEASUREMENT", "freeze": {"status": "VERIFIED"}}) == "measurement"


def test_report_header_and_markdown_carry_the_deferral_and_the_five_endpoints(tmp_path):
    reg = registry_with_boundary_event(tmp_path)
    base, pin = baseline_3_0(tmp_path)
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps([[r[0], r[1].isoformat(), r[2].isoformat(), r[3].isoformat(), r[4], r[5], r[6], r[7]] for r in boundary_rows()]))
    out, md = tmp_path / "report.json", tmp_path / "report.md"
    rc = n4.main(["--registry", str(reg), "--baseline-extract", str(base), "--baseline-pin", pin, "--chart-id", CHART, "--pinned-at", "2026-10-22",
                  "--output", str(out), "--markdown", str(md), "--rows-json", str(rows)])
    assert rc == 0
    report = json.loads(out.read_text())
    assert report["header"] == n4.DEFER_HEADER and report["comparison"]["evidence_grade_5_0"] == "trial_read_not_a_measurement"
    assert report["scorer"]["match"] is True and tuple(report["comparison"]["endpoints"]) == ENDPOINTS
    text = md.read_text()
    assert n4.DEFER_HEADER in text.splitlines()[2] and all(f"| {n} |" in text for n in ENDPOINTS)


def test_a_baseline_pin_mismatch_is_refused_not_scored(tmp_path):
    reg = registry_with_boundary_event(tmp_path)
    base, _ = baseline_3_0(tmp_path)
    with pytest.raises(n4.ReaderRefused, match="INPUT REFUSED"):
        n4.run_reader(boundary_rows(), generation="5.0", chart_id=CHART, pinned_at="x", registry_path=reg, baseline_extract=base,
                      baseline_pin="0" * 64)


# ---- the read-only reader of the stored windows -----------------------------------------------------------------------------------
class _Cur:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        self.conn.executed.append((sql, params))

    def fetchall(self):
        return self.conn.rows


class _Conn:
    def __init__(self, rows, read_only=True):
        self.rows, self.read_only, self.executed = rows, read_only, []

    def cursor(self):
        return _Cur(self)


def test_reader_selects_one_chart_and_generation_read_only_with_a_total_order():
    conn = _Conn([list(r) for r in boundary_rows()])
    got = n4.read_raw_windows(conn, "5.0", CHART)
    sql, params = conn.executed[0]
    assert params == (CHART, "5.0") and "ka_gochara_eval_window" in sql and sql.lstrip().upper().startswith("SELECT")
    assert "ORDER BY" in sql and all(w not in sql.upper() for w in ("INSERT", "UPDATE", "DELETE")) and len(got) == 2


def test_reader_refuses_a_connection_that_is_not_read_only():
    with pytest.raises(RuntimeError, match="not configured read-only"):
        n4.read_raw_windows(_Conn([], read_only=False), "5.0", CHART)
