"""WP8 synthetic workload builders (L3 §4.6/§4.7/§4.11).

All geometry is INVENTED (shape of plan §3 F-02 walkthroughs; no real chart,
no person, no real season). Every constant is declared here and echoed into
the WP8 reports by the tests.

Toy universe (marriage-2013): nine analytic tracks with declared speeds
(°/d): Saturn 0.017 (WP4's pinned slow-body speed), Jupiter 0.095, Mars
0.520, Venus 0.980, Sun 0.990, Mercury 1.050, Moon 13.180, Rahu/Ketu
−0.053. Moon generates no contact sentences in the battery workloads (the
Moon channel is M-3's separate concern); it exists as the tārā/w30 ephemeris
input for full-engine runs.
"""
from __future__ import annotations

from services.gochara_grammar.models import ResonanceTarget

from .wp8synth import (
    Anchor, SyntheticEphemeris, Track, Workload, daily_grid, jd_of,
    make_contact_workload, _sentence,
)

CHART_MARRIAGE = "00000000-0000-4000-8000-000000000810"
CHART_QUARTER = "00000000-0000-4000-8000-000000000811"
CHART_CLASS = "00000000-0000-4000-8000-000000000812"
CHART_RETRO = "00000000-0000-4000-8000-000000000813"

ENVELOPE_ONLY_CLASSES = (
    "marriage", "career_advancement", "illness_acute", "surgery",
    "childbirth", "romantic_start", "relocation", "education_admission",
    "litigation", "property_purchase", "spiritual_initiation",
    "business_launch", "foreign_travel",
)
assert len(ENVELOPE_ONLY_CLASSES) == 13

SPEEDS = {
    "Saturn": 0.017, "Jupiter": 0.095, "Mars": 0.520, "Venus": 0.980,
    "Sun": 0.990, "Mercury": 1.050, "Moon": 13.180, "Rahu": -0.053,
    "Ketu": -0.053,
}


def _target(chart_id: str, event_class: str, ref: str, deg: float,
            weight: float = 1.0) -> ResonanceTarget:
    return ResonanceTarget(
        chart_id=chart_id, event_class=event_class,
        target_type="sensitive_degree", target_ref=ref, weight=weight,
        uncited_extension=True, target_longitude_deg=deg,
        target_sign=None, target_nakshatra_id=None,
    )


# ── marriage-2013 ────────────────────────────────────────────────────────────

def build_marriage_2013() -> Workload:
    jd0, jd1 = jd_of(2013, 1, 1), jd_of(2013, 12, 31)
    t_a, t_b, t_c = jd_of(2013, 3, 17), jd_of(2013, 7, 19), jd_of(2013, 11, 9)

    # Weights < 1.0 by declaration so a single exact contact does not
    # saturate the noisy-OR (keeps the dynamic-range metric discriminating).
    targets = [
        _target(CHART_MARRIAGE, "marriage", "syn:7th_lord", 105.50, weight=0.75),
        _target(CHART_MARRIAGE, "marriage", "syn:natal_venus", 243.20, weight=0.70),
        _target(CHART_MARRIAGE, "marriage", "syn:7th_cusp", 98.00, weight=0.80),
        _target(CHART_MARRIAGE, "marriage", "syn:natal_moon", 35.75, weight=0.55),
        _target(CHART_MARRIAGE, "marriage", "syn:upapada", 285.00, weight=0.60),
    ]
    by_ref = {t.target_ref: t for t in targets}

    tracks = {
        # placed anchor crossings:
        "Jupiter": Track.for_crossing(0.095, 98.00, t_a, jd0),
        "Venus": Track.for_crossing(0.980, 105.50, t_b, jd0),
        "Saturn": Track.for_crossing(0.017, 243.20, t_c, jd0),
        # placed background crossing:
        "Mars": Track.for_crossing(0.520, 35.75, jd_of(2013, 1, 25), jd0),
        # declared base longitudes:
        "Sun": Track.constant(280.50, 0.990, jd0),
        "Mercury": Track.constant(275.00, 1.050, jd0),
        "Moon": Track.constant(10.00, 13.180, jd0),
        "Rahu": Track.constant(260.00, -0.053, jd0),
        "Ketu": Track.constant(80.00, -0.053, jd0),
    }
    eph = SyntheticEphemeris(tracks)

    wl = make_contact_workload(
        name="marriage-2013", chart_id=CHART_MARRIAGE, event_class="marriage",
        eph=eph, targets=targets, jd0=jd0, jd1=jd1,
        contacts=[
            (body, ref)
            for body in ("Jupiter", "Saturn", "Venus", "Mars", "Sun", "Mercury")
            for ref in by_ref
        ],
        anchors=[
            Anchor("A", t_a), Anchor("B", t_b), Anchor("C", t_c),
        ],
    )

    # Drishti sentences (special aspects; aspect-exact longitude recorded as
    # the sentence's target longitude, per the harness convention).
    drishti_specs = [
        ("Jupiter", "syn:natal_venus", 150.0),   # 5th
        ("Jupiter", "syn:natal_moon", 270.0),    # 9th
        ("Mars", "syn:natal_venus", 120.0),      # 4th
        ("Mars", "syn:natal_moon", 240.0),       # 8th
        # N-14 nodal dṛṣṭi rows (removed under nodal_drishti='removed'):
        ("Rahu", "syn:natal_moon", 150.0),       # 5th
        ("Ketu", "syn:upapada", 210.0),          # 7th
    ]
    from .wp8synth import _crossing_jds
    for body, ref, aspect in drishti_specs:
        target = by_ref[ref]
        virtual = (float(target.target_longitude_deg) - aspect) % 360.0
        for t in _crossing_jds(tracks[body], virtual, jd0, jd1):
            s = _sentence("drishti_contact", CHART_MARRIAGE, "marriage",
                          target, body, t, virtual)
            s.detail["aspect_deg"] = aspect
            wl.sentences.append(s)
    wl.sentences.sort(key=lambda s: (s.event_jd, s.primitive, s.transit_planet or ""))
    return wl


# ── 13 envelope-only classes, 2013 (metric iii) ─────────────────────────────

def build_envelope_class(index: int) -> Workload:
    """Private toy ephemeris per class: a two-body cluster spaced Δ days
    (Δ cycles 3/8/15) plus one isolated background crossing."""
    name = ENVELOPE_ONLY_CLASSES[index]
    jd0, jd1 = jd_of(2013, 1, 1), jd_of(2013, 12, 31)
    target_deg = (137.0 + 7.0 * index) % 360.0
    delta = (3.0, 8.0, 15.0)[index % 3]
    t_center = jd0 + 20.0 + 26.0 * index
    t_bg = jd0 + 200.0 + 7.0 * index

    chart_id = f"{CHART_CLASS[:-2]}{index:02d}"
    targets = [_target(chart_id, name, f"syn:{name}", target_deg, weight=0.75)]
    tracks = {
        "Jupiter": Track.for_crossing(0.095, target_deg, t_center - delta / 2.0, jd0),
        "Venus": Track.for_crossing(0.980, target_deg, t_center + delta / 2.0, jd0),
        "Mars": Track.for_crossing(0.520, target_deg, t_bg, jd0),
        "Moon": Track.constant(10.00, 13.180, jd0),
        "Rahu": Track.constant(260.00, -0.053, jd0),
    }
    eph = SyntheticEphemeris(tracks)
    wl = make_contact_workload(
        name=f"{name}-2013", chart_id=chart_id, event_class=name,
        eph=eph, targets=targets, jd0=jd0, jd1=jd1,
        contacts=[("Jupiter", f"syn:{name}"), ("Venus", f"syn:{name}"),
                  ("Mars", f"syn:{name}")],
    )
    wl.cluster_delta_days = delta  # declared, printed by the battery
    return wl


# ── ordinary quarter 2027-03→05 (control) ───────────────────────────────────

def build_quarter_class(index: int) -> Workload:
    """Sparse control: marriage (index 0) gets one Δ=8 cluster; even indices
    get one isolated crossing; odd indices get none (honest zero windows)."""
    name = ENVELOPE_ONLY_CLASSES[index]
    jd0, jd1 = jd_of(2027, 3, 1), jd_of(2027, 5, 31)
    target_deg = (137.0 + 7.0 * index) % 360.0
    chart_id = f"{CHART_QUARTER[:-2]}{index:02d}"
    targets = [_target(chart_id, name, f"syn:{name}", target_deg, weight=0.75)]

    tracks = {"Moon": Track.constant(10.00, 13.180, jd0),
              "Rahu": Track.constant(260.00, -0.053, jd0)}
    contacts: list[tuple[str, str]] = []
    if index == 0:
        tracks["Jupiter"] = Track.for_crossing(0.095, target_deg, jd0 + 26.0, jd0)
        tracks["Venus"] = Track.for_crossing(0.980, target_deg, jd0 + 34.0, jd0)
        contacts = [("Jupiter", f"syn:{name}"), ("Venus", f"syn:{name}")]
    elif index % 2 == 0:
        body = ("Venus", "Mars", "Jupiter", "Saturn")[(index // 2) % 4]
        speed = {"Venus": 0.980, "Mars": 0.520, "Jupiter": 0.095,
                 "Saturn": 0.017}[body]
        tracks[body] = Track.for_crossing(speed, target_deg, jd0 + 6.0 + 6.5 * index, jd0)
        contacts = [(body, f"syn:{name}")]

    eph = SyntheticEphemeris(tracks)
    return make_contact_workload(
        name=f"{name}-2027Q", chart_id=chart_id, event_class=name,
        eph=eph, targets=targets, jd0=jd0, jd1=jd1, contacts=contacts,
    )


# ── M-2 retrograde ablation (windows pre-declared in
#    WP8_M2_RETROGRADE_WINDOWS_v1_0.md — geometry here must match §1) ────────

def build_retro_ablation_2013() -> Workload:
    jd0, jd1 = jd_of(2013, 1, 1), jd_of(2013, 12, 31)
    sat_retro, sat_direct = jd_of(2013, 2, 18), jd_of(2013, 7, 8)
    mar_retro, mar_direct = jd_of(2013, 4, 16), jd_of(2013, 6, 30)

    targets = [
        _target(CHART_RETRO, "synthetic_m2", "syn:sat", 207.00),
        _target(CHART_RETRO, "synthetic_m2", "syn:mar", 262.00),
    ]
    sat_lon_at_retro = 208.2 + 0.017 * (sat_retro - jd0)
    sat_lon_at_direct = sat_lon_at_retro - 0.030 * (sat_direct - sat_retro)
    mar_lon_at_retro = 222.48 + 0.520 * (mar_retro - jd0)
    mar_lon_at_direct = mar_lon_at_retro - 0.350 * (mar_direct - mar_retro)
    tracks = {
        "Saturn": Track((
            (jd0 - 1.0e6, 208.2 - 0.017 * 1.0e6, 0.017),
            (sat_retro, sat_lon_at_retro, -0.030),
            (sat_direct, sat_lon_at_direct, 0.017),
        )),
        "Mars": Track((
            (jd0 - 1.0e6, 222.48 - 0.520 * 1.0e6, 0.520),
            (mar_retro, mar_lon_at_retro, -0.350),
            (mar_direct, mar_lon_at_direct, 0.520),
        )),
        "Moon": Track.constant(10.00, 13.180, jd0),
        "Rahu": Track.constant(260.00, -0.053, jd0),
    }
    eph = SyntheticEphemeris(tracks)
    return make_contact_workload(
        name="retro-ablation-2013", chart_id=CHART_RETRO,
        event_class="synthetic_m2", eph=eph, targets=targets,
        jd0=jd0, jd1=jd1,
        contacts=[("Saturn", "syn:sat"), ("Mars", "syn:mar")],
    )
