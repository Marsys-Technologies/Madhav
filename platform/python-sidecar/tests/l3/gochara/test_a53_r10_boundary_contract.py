"""A5.3 — Codex round 10, R10-6: ONE boundary contract in the complete job.

The job used to run `inventory_verifier.verify_aspect_span_contacts` (fixed 3-second tolerance, 6-hour sampling step) BEFORE
the new certifier, so a stored boundary 10 s off on a smooth one-degree-per-day crossing — valid under the declared contract
(tolerance = the contact's own stated accuracy / |speed| at that instant + 1 s) — was rejected by the old comparison. That
precheck is removed (job and writer); every contact, aspect-to-span included, is certified by `contact_certify` under the
DERIVED tolerance and the union-of-contacts contract. These tests run the COMPLETE job (`verification_job.run` as the verifier
login) on a smooth sky: a valid small offset is accepted, a valid LARGE offset at a SLOW crossing is accepted (the tolerance
scales with 1/|speed|), and an offset beyond the derived bound is refused."""
from __future__ import annotations

import inspect
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import inventory_verifier as inv_v
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _t
from .test_a53_r10_complete_records import (CLS, LIBRA, _job_position, _kwargs, _stage, _verification_rows, built, login,  # noqa: F401
                                            rworld)
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401

UTC = timezone.utc
JAN10 = datetime(2025, 1, 10, tzinfo=UTC)
FEB20 = datetime(2025, 2, 20, tzinfo=UTC)
DAYS = (FEB20 - JAN10).total_seconds() / 86400.0            # 41
_K = (30.0 - 0.05 * DAYS) / DAYS ** 3                         # slow-entry cubic: 180 at Jan 10, 210 at Feb 20


def _smooth(w, *, slow_entry=False, entry_offset_s=0.0):
    """Saturn crosses into Libra at (Jan 10 + entry_offset) and out at Feb 20 on a SMOOTH path (0.73°/day, or a slow 0.05°/day
    entry for `slow_entry`) within HALF A DAY of each crossing; in between it sits inside Libra, and elsewhere in the world's
    quiet longitude — so the world's other (point/aspect) obligations stay out of play and only the two boundaries are under
    test. The STORED contacts are the world's (exact Jan 10 / Feb 20 crossings); `entry_offset_s` is the stored boundary's
    error."""
    base = _job_position(w, [])
    half = 0.5

    def lon(d):
        return 180.0 + (0.05 * d + _K * d ** 3 if slow_entry else (30.0 / DAYS) * d)

    def at(body, t):
        if body.lower() != "saturn":
            return base(body, t)
        d = (t - JAN10).total_seconds() / 86400.0
        # the entry crossing is displaced by `entry_offset_s`: shift the path near the entry only (fading to nothing by the exit)
        if -half <= d <= half:
            return lon(d - entry_offset_s / 86400.0)
        if DAYS - half <= d <= DAYS + half:
            return lon(d)
        if half < d < DAYS - half:
            return 195.0
        return base(body, t)
    return at


def _job(w, position_at):
    with login(w, "gochara_verifier") as conn:
        return vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, position_at))


def test_the_fixed_tolerance_precheck_is_gone_from_the_job_and_the_writer():
    assert not hasattr(inv_v, "verify_aspect_span_contacts")
    for mod in (vj, writer_mod):
        assert "verify_aspect_span_contacts" not in inspect.getsource(mod)
        assert "tol_seconds" not in inspect.getsource(mod)


def test_a_smooth_crossing_with_the_exact_stored_boundary_is_verified(built):
    report = _job(built, _smooth(built))
    assert report["status"] == "VERIFIED", _stage(report)


def test_a_ten_second_boundary_error_on_a_smooth_degree_per_day_crossing_is_accepted_by_the_complete_job(built):
    """Old contract: |10 s| > 3 s ⇒ rejected. Derived contract: the stored contact states delta_lambda = 2″; at 0.73°/day that
    is 2/3600 / 0.73 × 86400 ≈ 66 s (+ 1 s) — a 10 s error is inside the bound."""
    w = built
    report = _job(w, _smooth(w, entry_offset_s=10.0))
    assert report["status"] == "VERIFIED", _stage(report)
    assert _verification_rows(w)["ka_gochara_eval_window_verification"] == 4


def test_a_large_boundary_error_at_a_slow_crossing_is_accepted_because_the_tolerance_scales_with_inverse_speed(built):
    """Entry at 0.05°/day: the bound is 2″/0.05°/day ≈ 1,000 s, so a 600 s error is valid there (and would be refused 9× over
    at the 0.73°/day crossing)."""
    w = built
    report = _job(w, _smooth(w, slow_entry=True, entry_offset_s=600.0))
    assert report["status"] == "VERIFIED", _stage(report)


@pytest.mark.parametrize("kw", [{"entry_offset_s": 300.0}, {"slow_entry": True, "entry_offset_s": 3000.0}])
def test_an_offset_beyond_the_derived_bound_is_refused_and_persists_nothing(built, kw):
    w = built
    report = _job(w, _smooth(w, **kw))
    c = report["classes"][CLS]
    assert c["status"] == "DISAGREE" and c["stage"] in ("contact_geometry", "p1_anchors") \
        or str(c.get("stage", "")).startswith("member_geometry"), c
    assert report["status"] == "DISAGREE" and _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}
