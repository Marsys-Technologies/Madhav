"""
test_kala_timeline_spec — ṢAḌ-DARŚANA W2 Lane E · stage 8, `kala_timeline_spec v1` (item 27).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.1, including its mandatory GOLDEN-RENDER TEST:

    "a fixture covering EVERY key above — including `chain` shape, an interval with
     `start_interval` present, a `no_lever`-adjacent empty `bands` array, and both canonical
     charts — rendered and byte-compared. 'Full spec surface' means every key, not every value."

§1 is that golden test. The fixture deliberately exercises all three of the named awkward
cases, and the byte comparison is against a committed JSON file
(`tests/fixtures/kala_timeline_spec_golden.json`) rather than against a re-computation, so a
change to the spec's SHAPE cannot slip through by changing the test and the code together in
one edit without the diff being visible.

§2–§4 cover the three rails the module exists to hold: single temporal authority (a spec
never mints a window id), precision honesty (an unsupported boundary is omitted, not
rendered), and honest-empty (an empty spec says why).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_kshetra.stage8_spec import (  # noqa: E402
    EMPTY_NO_RENDERABLE_ROWS,
    PRECISION_DAY_GRADE,
    SPEC_VERSION,
    TimelineTrack,
    build_timeline_spec,
    days_to_iso,
    interval_from_window,
    point_from_boundary,
    spec_counts,
)

GOLDEN = Path(__file__).parent.parent / "fixtures" / "kala_timeline_spec_golden.json"

IST = timezone(timedelta(hours=5, minutes=30))
#: The native's birth instant (CLAUDE.md §B) — the spec's `t_zero`.
ABHISEK_T_ZERO = datetime(1984, 2, 5, 10, 43, 0, tzinfo=IST)
ABHISEK = "482012f1-710e-4a25-994a-93821f5871aa"
ABHINANDAN = "1c826d5a-0000-0000-0000-000000000000"

TRACKS = [
    TimelineTrack("clock:vimshottari", "clock", "Vimśottarī", 0),
    TimelineTrack("domain:career", "domain", "Career", 1),
]


def _windows():
    """Three windows, chosen to cover the shapes §7.1's golden test names.

    `t` values are days since birth; the ISO dates in the golden file are their conversions.
    """
    return [
        {  # interval shape, WITH start_interval/end_interval present
            "window_id": "kfw_a1b2c3d4e5f60718293a4b5c",
            "track_id": "domain:career",
            "event_class": "career_change",
            "t_start": 15_730.0,
            "t_end": 15_810.0,
            "t_peak": 15_769.0,
            "start_interval_lo": 15_725.0,
            "start_interval_hi": 15_735.0,
            "end_interval_lo": 15_804.0,
            "end_interval_hi": 15_816.0,
            "valence": "gain",
            "confidence_tier": "concurrent",
            "temporal_shape": "interval",
            "label": "Career — Jupiter/Saturn double transit",
            "expected_count": 0.83,
            "null_p": 0.0117,
            "precision_regime": PRECISION_DAY_GRADE,
        },
        {  # CHAIN shape — the case §7.1 calls out by name
            "window_id": "kfw_0f1e2d3c4b5a69788796a5b4",
            "track_id": "domain:career",
            "event_class": "relocation",
            "t_start": 16_100.0,
            "t_end": 16_900.0,
            "t_peak": 16_400.0,
            "start_interval_lo": None,
            "start_interval_hi": None,
            "end_interval_lo": None,
            "end_interval_hi": None,
            "valence": "mixed",
            "confidence_tier": "structural_prior",
            "temporal_shape": "chain",
            "label": "Relocation — milestone chain",
            "expected_count": 1.4,
            "null_p": 0.0428,
            "precision_regime": PRECISION_DAY_GRADE,
        },
        {  # point shape, honest null_p absent (stage 5 not run for this class)
            "window_id": "kfw_9988776655443322110aabbc",
            "track_id": "domain:career",
            "event_class": "recognition",
            "t_start": 15_400.0,
            "t_end": 15_401.0,
            "t_peak": 15_400.0,
            "start_interval_lo": None,
            "start_interval_hi": None,
            "end_interval_lo": None,
            "end_interval_hi": None,
            "valence": "neutral",
            "confidence_tier": "structural_prior",
            "temporal_shape": "point",
            "label": "Recognition",
            "expected_count": 0.06,
            "null_p": None,
            "precision_regime": PRECISION_DAY_GRADE,
        },
    ]


def _boundaries():
    return [
        {  # instant → no at_interval
            "point_id": "kfb_md_ke",
            "track_id": "clock:vimshottari",
            "t_boundary": 15_500.0,
            "interval_lo": 15_498.0,
            "interval_hi": 15_502.0,
            "precision_state": "instant",
            "kind": "dasha_boundary",
            "label": "MD Ketu begins",
        },
        {  # interval → at_interval present
            "point_id": "kfb_ad_ve",
            "track_id": "clock:vimshottari",
            "t_boundary": 15_950.0,
            "interval_lo": 15_930.0,
            "interval_hi": 15_970.0,
            "precision_state": "interval",
            "kind": "dasha_boundary",
            "label": "AD Venus begins",
        },
        {  # precision_unsupported → OMITTED, and counted in coverage
            "point_id": "kfb_prd_su",
            "track_id": "clock:vimshottari",
            "t_boundary": 15_960.0,
            "interval_lo": 15_900.0,
            "interval_hi": 16_020.0,
            "precision_state": "precision_unsupported",
            "kind": "dasha_boundary",
            "label": "PrD Sun begins",
        },
    ]


def _build(chart_id: str, view: str = "ahead", bands=()) -> dict:
    return build_timeline_spec(
        chart_id=chart_id,
        generated_for=view,
        t_zero=ABHISEK_T_ZERO,
        now_marker="2026-07-30",
        field_snapshot_id="kfs_1122334455667788990011223344556677",
        weights_version="v0_classical",
        tracks=TRACKS,
        windows=_windows(),
        boundaries=_boundaries(),
        bands=bands,
    )


# ── §1 — THE GOLDEN-RENDER TEST (full spec surface, byte-compared) ─────────────────────

def test_golden_render_is_byte_identical_for_both_canonical_charts():
    """§7.1's mandatory golden test. Covers `chain` shape, an interval WITH `start_interval`,
    and a deliberately EMPTY `bands` array (the `no_lever`-adjacent case) — and both charts.

    The empty `bands` array beside populated `intervals` is a legitimate SILENT state: the
    honest-empty reason is about the whole spec having nothing renderable, not about each
    individual array, which is why `empty_reason` is null here (see §4).
    """
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for chart_id, key in ((ABHISEK, "abhisek"), (ABHINANDAN, "abhinandan")):
        produced = _build(chart_id, bands=())
        assert json.dumps(produced, sort_keys=True, indent=2) == json.dumps(
            expected[key], sort_keys=True, indent=2
        ), f"timeline spec drifted for {key}"
        assert produced["bands"] == [], "the no_lever-adjacent empty bands case"


def test_the_golden_fixture_really_covers_every_key_of_the_spec_surface():
    """"Full spec surface means every key, not every value" (§7.1). A golden file that had
    quietly lost a key would still byte-match a code change that dropped the same key, so the
    key set is asserted independently."""
    spec = _build(ABHISEK)
    assert set(spec) == {
        "spec_version",
        "chart_id",
        "field_snapshot_id",
        "generated_for",
        "t_zero",
        "now_marker",
        "tracks",
        "intervals",
        "points",
        "bands",
        "legend",
        "drill",
        "coverage",
    }
    assert spec["spec_version"] == SPEC_VERSION
    assert set(spec["tracks"][0]) == {"track_id", "kind", "label", "row"}
    assert set(spec["intervals"][0]) == {
        "id", "track_id", "start", "end", "peak", "start_interval", "end_interval",
        "valence", "tier", "shape", "label", "expected_count", "null_p", "precision_regime",
    }
    assert set(spec["points"][0]) == {"id", "track_id", "at", "kind", "label", "at_interval"}
    assert set(spec["drill"]) == {"instrument", "id_param"}
    assert spec["drill"]["instrument"] == "kala_explain_get"
    # every one of the three shapes appears in the fixture
    assert {i["shape"] for i in spec["intervals"]} == {"interval", "chain", "point"}


def test_output_is_deterministic_and_totally_ordered():
    """Two builds of one snapshot must be byte-identical — the property both the golden test
    and the field hash rest on. Shuffling the inputs must not change the output."""
    a = _build(ABHISEK)
    shuffled = build_timeline_spec(
        chart_id=ABHISEK,
        generated_for="ahead",
        t_zero=ABHISEK_T_ZERO,
        now_marker="2026-07-30",
        field_snapshot_id="kfs_1122334455667788990011223344556677",
        weights_version="v0_classical",
        tracks=list(reversed(TRACKS)),
        windows=list(reversed(_windows())),
        boundaries=list(reversed(_boundaries())),
    )
    assert json.dumps(a, sort_keys=True) == json.dumps(shuffled, sort_keys=True)


# ── §2 — SINGLE TEMPORAL AUTHORITY (item 44) ───────────────────────────────────────────

def test_every_interval_id_is_the_field_windows_window_id_verbatim():
    spec = _build(ABHISEK)
    assert [i["id"] for i in spec["intervals"]] == [
        "kfw_9988776655443322110aabbc",
        "kfw_a1b2c3d4e5f60718293a4b5c",
        "kfw_0f1e2d3c4b5a69788796a5b4",
    ]
    assert all(i["id"].startswith("kfw_") for i in spec["intervals"])


def test_a_window_row_with_no_window_id_is_rejected_rather_than_having_one_minted():
    """The rail: "a serving path that computes its own window is a build error, not a
    divergence to classify" (brief §7 SINGLE TEMPORAL AUTHORITY)."""
    bad = dict(_windows()[0])
    bad["window_id"] = None
    with pytest.raises(ValueError, match="authority_basis"):
        interval_from_window(bad, t_zero=ABHISEK_T_ZERO, track_id="domain:career")


def test_no_window_finding_code_exists_on_this_path():
    """A structural assertion, not a stylistic one: this module has no threshold, no root
    find and no peak search. If one appears, stage 8 has become a second window authority."""
    src = (
        Path(__file__).parent.parent.parent
        / "services" / "ka_kshetra" / "stage8_spec.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("brentq", "q_threshold", "argmax", "def find_window"):
        assert forbidden not in src, f"stage 8 must not contain {forbidden!r}"


# ── §3 — PRECISION HONESTY (§4.2) ──────────────────────────────────────────────────────

def test_a_precision_unsupported_boundary_is_omitted_and_the_omission_is_counted():
    spec = _build(ABHISEK)
    assert [p["id"] for p in spec["points"]] == ["kfb_md_ke", "kfb_ad_ve"]
    assert spec["coverage"]["precision_unsupported_boundaries_omitted"] == 1, (
        "the omission must be visible as data — a silent drop is indistinguishable from "
        "the boundary not existing"
    )


def test_an_instant_boundary_carries_no_at_interval_and_an_interval_one_does():
    instant, interval, _ = _boundaries()
    p_i = point_from_boundary(instant, t_zero=ABHISEK_T_ZERO, track_id="clock:vimshottari")
    p_v = point_from_boundary(interval, t_zero=ABHISEK_T_ZERO, track_id="clock:vimshottari")
    assert p_i["at_interval"] is None, "a degenerate [d,d] would look like a measured zero width"
    # t_zero = 1984-02-05 (IST); 15 930 d → 2027-09-17, 15 970 d → 2027-10-27.
    assert p_v["at_interval"] == ["2027-09-17", "2027-10-27"]
    assert p_v["at"] == "2027-10-07"  # 15 950 d


def test_every_row_is_day_grade_at_w2():
    spec = _build(ABHISEK)
    assert spec["coverage"]["precision_regime"] == PRECISION_DAY_GRADE
    assert {i["precision_regime"] for i in spec["intervals"]} == {PRECISION_DAY_GRADE}


def test_date_conversion_names_the_calendar_day_the_instant_falls_in():
    """A day-grade claim names the calendar day containing `t_zero + t`, in `t_zero`'s OWN
    timezone — not the day `⌊t⌋` days after a notional midnight.

    The distinction is real and this test pins it: the native was born at 10:43 IST, so
    `t = 0.99 d` is 10:29 the FOLLOWING morning and belongs to 1984-02-06, while `t = 0.5 d`
    is 22:43 that same evening and belongs to 1984-02-05. A conversion that floored `t`
    before adding would put both on 02-05 and would silently shift every window edge in the
    chart by up to a day, in a direction that depends on the birth hour.
    """
    assert days_to_iso(ABHISEK_T_ZERO, 0.0) == "1984-02-05"
    assert days_to_iso(ABHISEK_T_ZERO, 0.5) == "1984-02-05"   # 22:43 IST, same day
    assert days_to_iso(ABHISEK_T_ZERO, 0.99) == "1984-02-06"  # 10:29 IST, next morning
    assert days_to_iso(ABHISEK_T_ZERO, 1.0) == "1984-02-06"
    # and it is a floor of the resulting instant, never a round: 23:59 stays on its own day
    assert days_to_iso(ABHISEK_T_ZERO, 0.55) == "1984-02-05"


# ── §4 — LAW ZERO / honest-empty ───────────────────────────────────────────────────────

def test_an_empty_spec_carries_a_machine_readable_reason():
    spec = build_timeline_spec(
        chart_id=ABHISEK,
        generated_for="story",
        t_zero=ABHISEK_T_ZERO,
        now_marker="2026-07-30",
        field_snapshot_id="kfs_deadbeef",
        weights_version="v0_classical",
        tracks=TRACKS,
    )
    counts = spec_counts(spec)
    assert counts["n_intervals"] == counts["n_points"] == counts["n_bands"] == 0
    assert counts["empty_reason"] == EMPTY_NO_RENDERABLE_ROWS


def test_a_populated_spec_carries_no_empty_reason():
    """Mirrors migration 496's CHECK constraint exactly, so the two cannot drift apart."""
    counts = spec_counts(_build(ABHISEK))
    assert counts["n_intervals"] == 3
    assert counts["empty_reason"] is None


def test_an_undeclared_track_is_an_error_rather_than_an_invented_row():
    bad = dict(_windows()[0])
    bad["track_id"] = "domain:invented"
    with pytest.raises(ValueError, match="undeclared track_id"):
        build_timeline_spec(
            chart_id=ABHISEK,
            generated_for="ahead",
            t_zero=ABHISEK_T_ZERO,
            now_marker="2026-07-30",
            field_snapshot_id="kfs_x",
            weights_version="v0_classical",
            tracks=TRACKS,
            windows=[bad],
        )


def test_an_unknown_view_or_enum_value_is_rejected():
    with pytest.raises(ValueError, match="generated_for"):
        build_timeline_spec(
            chart_id=ABHISEK,
            generated_for="dashboard",
            t_zero=ABHISEK_T_ZERO,
            now_marker="2026-07-30",
            field_snapshot_id="kfs_x",
            weights_version="v0_classical",
            tracks=TRACKS,
        )
    bad = dict(_windows()[0])
    bad["confidence_tier"] = "very_confident"
    with pytest.raises(ValueError, match="tier"):
        interval_from_window(bad, t_zero=ABHISEK_T_ZERO, track_id="domain:career")


def test_zero_surviving_tracks_is_an_honest_empty_spec_not_a_crash():
    """Real reachable regression (Gate-Chain MORNING REPORT defect #6, chart 482012f1):
    ka_kshetra's field build can discover event classes that ALL get skipped with
    `no_class_prior_row` (stage4's `ClassSkipped`) because none overlap the N_e
    lifetime-count corpus in `brahma_class_priors`. When that happens, stage 8 receives
    zero windows and zero boundaries, so `_timeline_tracks_and_windows` /
    `_timeline_points` hand it zero tracks. That must be an honest-empty
    `kala_timeline_spec` — LAW ZERO — never an unhandled `ValueError` that takes down the
    whole build.
    """
    spec = build_timeline_spec(
        chart_id=ABHISEK,
        generated_for="ahead",
        t_zero=ABHISEK_T_ZERO,
        now_marker="2026-07-30",
        field_snapshot_id="kfs_zero_surviving_tracks",
        weights_version="v0_classical",
        tracks=(),
    )
    assert spec["tracks"] == []
    assert spec["intervals"] == []
    assert spec["points"] == []
    assert spec["bands"] == []
    counts = spec_counts(spec)
    assert counts["n_tracks"] == 0
    assert counts["empty_reason"] == EMPTY_NO_RENDERABLE_ROWS, (
        "an empty spec must carry LAW ZERO's machine-readable empty_reason, matching "
        "migration 496's CHECK constraint (empty iff empty_reason is set)"
    )


def test_the_module_contains_no_composed_prose_or_generative_call():
    """brief §7's B.10 prose rule: the argument composer is template-over-computed-data and
    no generative call exists on any serving path."""
    src = (
        Path(__file__).parent.parent.parent
        / "services" / "ka_kshetra" / "stage8_spec.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("anthropic", "openai", "generate_text", "vertexai", "completion("):
        assert forbidden not in src, f"stage 8 must not reference {forbidden!r}"
