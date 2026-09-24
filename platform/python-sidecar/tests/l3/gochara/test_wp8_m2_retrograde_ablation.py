"""WP8 M-2 retrograde ablation (L3 §4.7).

Runs the pre-declared synthetic retrograde seasons of
`WP8_M2_RETROGRADE_WINDOWS_v1_0.md` (SAT-RETRO-2013-SYN, MAR-RETRO-2013-SYN)
with and without the declared probe weight w=0.25 (test-code only; the engine
is not modified). Every reported number is a `WP8RETRO|` print from this file.

Honesty rule (per the pre-declaration §5): NOT_RUN is a result. The §5.2
vedha-row qualifier `intensity_qualifier='retrograde_malefic'` is checked for
existence here and reported NOT_RUN because §5 of the remainder brief is not
executed on this branch.

Dwell check: kernel episodes on the synthetic Saturn retrograde loop must
satisfy dwell_k = t_out,k − max(t_in,k, t_out,k−1) (geometry-only,
`services/gochara_kernel/episodes.py` ~lines 41-45, 282-319). The weight may
not change the geometry: crossing counts are asserted identical across arms.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from services.gochara_kernel import arcs, contacts, episodes

from .wp8synth import (
    _crossing_jds, activity_at, daily_grid, date_of, jd_of, lam_series,
)
from .wp8workloads import build_retro_ablation_2013

W = 0.25  # pre-declared probe weight (WP8_M2_RETROGRADE_WINDOWS_v1_0 §2)

SEASONS = {
    "SAT-RETRO-2013-SYN": ("Saturn", 207.00, jd_of(2013, 2, 18), jd_of(2013, 7, 8)),
    "MAR-RETRO-2013-SYN": ("Mars", 262.00, jd_of(2013, 4, 16), jd_of(2013, 6, 30)),
}

SIDECAR = Path(__file__).resolve().parents[2]


def _arms():
    wl = build_retro_ablation_2013()
    jds = daily_grid(wl.jd0, wl.jd1)
    without = lam_series(wl, jds)
    with_w = lam_series(wl, jds, retro_attenuation=W)
    return wl, jds, without, with_w


def _in_mask(jds, lo, hi):
    return [lo <= jd <= hi for jd in jds]


def _mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def _peak_jd(series, jds, mask):
    best, best_jd = -1.0, None
    for v, jd, m in zip(series, jds, mask):
        if m and v > best:
            best, best_jd = v, jd
    return best_jd


def _season_crossings(wl, body, target_deg, lo, hi):
    return [t for t in _crossing_jds(wl.eph._tracks[body], target_deg, wl.jd0, wl.jd1)
            if lo <= t <= hi]


# ── detectors ────────────────────────────────────────────────────────────────

def test_attenuation_zero_equals_engine_output():
    """Drift guard: the probe path with w=0 must reproduce engine
    `_compute_activity_v3` output exactly (the probe re-forms the noisy-OR)."""
    wl = build_retro_ablation_2013()
    for jd in daily_grid(wl.jd0, wl.jd1)[::17]:
        plain, _ = activity_at(wl, jd)
        probed0, detail0 = activity_at(wl, jd, retro_attenuation=0.0)
        assert probed0 == plain
        assert detail0["activity_attenuated"] == round(plain, 8)


def test_crossings_identical_across_arms():
    """Declared metric 4: the weight may not change geometry. Crossings are
    computed from the analytic tracks — independent of either arm — and the
    gathered sentence set is the same object for both arms, so counts are
    trivially equal; asserted and printed anyway."""
    wl, jds, without, with_w = _arms()
    for name, (body, tdeg, lo, hi) in SEASONS.items():
        xs = _season_crossings(wl, body, tdeg, lo, hi)
        print(f"WP8RETRO|{name}|crossings_per_season|{len(xs)}|"
              f"jds|{','.join(date_of(t) for t in xs)}|identical_across_arms|True")
    # Retrograde crossings really are retrograde (speed < 0 at crossing):
    sat = _season_crossings(wl, "Saturn", 207.00, *SEASONS["SAT-RETRO-2013-SYN"][2:])
    assert len(sat) == 1 and wl.eph.speed("Saturn", sat[0]) < 0.0
    mar = _season_crossings(wl, "Mars", 262.00, *SEASONS["MAR-RETRO-2013-SYN"][2:])
    assert len(mar) == 1 and wl.eph.speed("Mars", mar[0]) < 0.0


def test_s5_2_vedha_qualifier_not_run():
    """§5.2 dependency check: `intensity_qualifier` must exist in services/
    for the vedha-row qualifier to be verifiable. §5 is not executed on this
    branch; report NOT_RUN honestly."""
    out = subprocess.run(
        ["grep", "-rn", "intensity_qualifier", "services/"],
        cwd=SIDECAR, capture_output=True, text=True,
    )
    present = out.returncode == 0 and out.stdout.strip() != ""
    print(f"WP8RETRO|s5.2_vedha_intensity_qualifier|present|{present}|status|NOT_RUN")
    assert not present, (
        "intensity_qualifier appeared in services/ — §5.2 may have landed; "
        "re-verify instead of reporting NOT_RUN"
    )


def test_dwell_is_geometry_only():
    """Declared metric 5: kernel dwell on the synthetic Saturn loop equals
    t_out,k − max(t_in,k, t_out,k−1) — no weight anywhere in the path."""
    wl = build_retro_ablation_2013()
    track = wl.eph._tracks["Saturn"]
    jds = [jd + 0.5 for jd in daily_grid(wl.jd0, wl.jd1)]  # noon-UT knots
    lons = [track.pos(jd)[0] % 360.0 for jd in jds]
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=1e-7)
    roots = contacts.find_roots(idx, "Saturn", "conjunction", 207.00, refine=False)
    eps = episodes.build_episodes(idx, "Saturn", "conjunction", 207.00, roots,
                                  (jds[0], jds[-1]), "orb_conj_slow")
    assert len(eps) == 2, f"expected 2 episodes (retro + direct crossings), got {len(eps)}"
    prev_out = None
    for k, ep in enumerate(eps):
        expected = ep.t_out - max(ep.t_in, prev_out) if prev_out is not None else ep.t_out - ep.t_in
        assert abs(ep.dwell_days - expected) < 1e-9, (
            f"episode {k}: dwell {ep.dwell_days} != geometric {expected}"
        )
        print(f"WP8RETRO|dwell|episode|{k}|branch|{ep.branch}|"
              f"t_in|{date_of(ep.t_in)}|t_out|{date_of(ep.t_out)}|"
              f"dwell_days|{round(ep.dwell_days, 4)}|geometry_only|True")
        prev_out = ep.t_out
    branches = [ep.branch for ep in eps]
    assert "retrograde" in branches, "the in-season crossing must be on a retrograde arc"


# ── declared metrics (printing tests) ────────────────────────────────────────

def test_metric_active_days_and_mean_lam():
    """Declared metrics 1+2: active-day count in-season; mean λ in vs out."""
    wl, jds, without, with_w = _arms()
    for name, (_b, _t, lo, hi) in SEASONS.items():
        mask = _in_mask(jds, lo, hi)
        for arm, series in (("without", without), ("with", with_w)):
            act_in = sum(1 for v, m in zip(series, mask) if m and v > 0.0)
            in_vals = [v for v, m in zip(series, mask) if m]
            out_vals = [v for v, m in zip(series, mask) if not m]
            print(f"WP8RETRO|{name}|arm|{arm}|active_days_in_season|{act_in}|"
                  f"mean_lam_in|{round(_mean(in_vals), 6)}|"
                  f"mean_lam_out|{round(_mean(out_vals), 6)}")
        # sanity: attenuation never raises λ
        assert all(b <= a + 1e-12 for a, b in zip(without, with_w))


def test_metric_peak_lam_shift():
    """Declared metric 3: JD of the λ maximum inside each season, per arm."""
    wl, jds, without, with_w = _arms()
    for name, (_b, _t, lo, hi) in SEASONS.items():
        mask = _in_mask(jds, lo, hi)
        p0, p1 = _peak_jd(without, jds, mask), _peak_jd(with_w, jds, mask)
        shift = (p1 - p0) if (p0 is not None and p1 is not None) else None
        print(f"WP8RETRO|{name}|peak_lam_jd_without|{date_of(p0) if p0 else 'none'}|"
              f"peak_lam_jd_with|{date_of(p1) if p1 else 'none'}|"
              f"shift_days|{shift}")
