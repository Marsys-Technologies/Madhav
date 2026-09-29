"""WP8 synthetic workload harness (L3 §4.6 M-1 battery, §4.7 M-2 ablation,
§4.11 factor delta report).

Everything here is INVENTED geometry in the shape of plan §3 F-02
walkthroughs: no real chart, no person, no real ephemeris season. Planet
tracks are piecewise-linear functions of Julian day with declared speeds;
contact sentences are generated analytically from those tracks.

Two evaluation surfaces are provided:

- ``activity_series`` — the engine's own activity surface
  (``engine._compute_activity_v3`` + ``engine._instantaneous_orbs_at``)
  driven over a daily grid with the legacy ±5 d gather box reproduced as an
  event-time filter. Used by the M-1 orb battery (tens of thousands of
  evaluations; the full engine per JD would be needlessly slow, and a
  cross-check test proves the surface matches the full engine's activity
  term on sampled JDs).

- ``evaluate_full`` — the full ``engine._evaluate_single_from_context``
  with all DB-touching primitives patched to the synthetic sentence set.
  Used by the §4.11 factor delta report (fewer, heavier evaluations).

Co-factor declaration: where a λ value is needed at the activity surface
(margin/range metrics), λ is computed as ``PROMISE × PERMISSION × activity``
with the declared synthetic co-factors PROMISE=0.8, PERMISSION=0.5, all
other factors 1.0 — identical across arms, so arm comparisons isolate the
activity shape, which is what the battery is about.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from unittest import mock

from services.gochara_grammar.models import ConfigurationSentence, ResonanceTarget
from services.gochara_v3 import engine
from services.gochara_v3.context import ClassContext, NatalFacts

# ── JD ↔ calendar helpers (UT; synthetic but real calendar dates) ────────────

_JD_EPOCH = 2440587.5  # JD of 1970-01-01T00:00:00 UT


def jd_of(y: int, m: int, d: int) -> float:
    dt = datetime(y, m, d, 12, 0, tzinfo=timezone.utc)
    return _JD_EPOCH + dt.timestamp() / 86400.0


def date_of(jd: float) -> str:
    dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=jd - _JD_EPOCH)
    return dt.strftime("%Y-%m-%d")


def daily_grid(jd0: float, jd1: float) -> list[float]:
    n = int(round(jd1 - jd0))
    return [jd0 + float(i) for i in range(n + 1)]


# ── Synthetic ephemeris ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class Track:
    """One body's piecewise-linear longitude track.

    segments: tuple of (jd_start, lon_at_start, speed_deg_per_day), ascending
    in jd_start; the last segment extends to +inf.
    """
    segments: tuple[tuple[float, float, float], ...]

    @staticmethod
    def constant(lon_at_ref: float, speed: float, jd_ref: float) -> "Track":
        return Track(((jd_ref - 1.0e6, lon_at_ref - speed * 1.0e6, speed),))

    @staticmethod
    def for_crossing(speed: float, target_deg: float, t_cross: float, jd_ref: float) -> "Track":
        """Constant-speed track that is exactly at target_deg at t_cross."""
        return Track.constant(target_deg - speed * (t_cross - jd_ref), speed, jd_ref)

    def pos(self, jd: float) -> tuple[float, float]:
        seg = self.segments[0]
        for s in self.segments:
            if jd >= s[0]:
                seg = s
            else:
                break
        jd0, lon0, speed = seg
        return (lon0 + speed * (jd - jd0)) % 360.0, speed


class SyntheticEphemeris:
    """swe-compatible facade over declared Tracks (Moon + Mean-node codes for
    the engine's tārā/w30 calls; everything else by name via pos())."""

    MOON = 1
    MEAN_NODE = 10
    FLG_SIDEREAL = 64

    _CODE_TO_NAME = {1: "Moon", 10: "Rahu"}

    def __init__(self, tracks: dict[str, Track]):
        self._tracks = tracks

    def pos(self, body: str, jd: float) -> tuple[float, float]:
        return self._tracks[body].pos(jd)

    def speed(self, body: str, jd: float) -> float:
        return self.pos(body, jd)[1]

    def calc_ut(self, jd, body_code, _flags):
        name = self._CODE_TO_NAME[body_code]
        lon, speed = self.pos(name, jd)
        return ((lon, 0.0, 0.0, speed), 2)

    def bodies(self) -> list[str]:
        return list(self._tracks)


# ── Workload ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Anchor:
    label: str
    jd_center: float
    half_days: float = 5.0


@dataclass
class Workload:
    name: str
    chart_id: str
    event_class: str
    eph: SyntheticEphemeris
    targets: list[ResonanceTarget]
    sentences: list[ConfigurationSentence]
    jd0: float
    jd1: float
    anchors: list[Anchor] = field(default_factory=list)

    @property
    def weights(self) -> dict[str, float]:
        return {t.target_ref: t.weight for t in self.targets}

    def gathered(self, jd: float, box_days: float = 5.0) -> list[ConfigurationSentence]:
        """The legacy ±box_days event-time gather (the time box itself)."""
        lo, hi = jd - box_days, jd + box_days
        return [s for s in self.sentences
                if s.event_jd is not None and lo <= s.event_jd <= hi]


def _sentence(primitive: str, chart_id: str, event_class: str, target: ResonanceTarget,
              body: str, event_jd: float, target_deg: float,
              temporal_shape: str = "point") -> ConfigurationSentence:
    return ConfigurationSentence(
        primitive=primitive,
        chart_id=chart_id,
        event_class=event_class,
        target_type=target.target_type,
        target_ref=target.target_ref,
        transit_planet=body,
        secondary_planet=None,
        event_jd=event_jd,
        event_datetime_ist=None,
        uncited_extension=True,
        temporal_shape=temporal_shape,
        detail={"target_longitude_deg": target_deg, "orb_strength": 1.0,
                "aspect_deg": 0.0},
    )


def _crossing_jds(track: Track, target_deg: float, jd0: float, jd1: float,
                  max_crossings: int = 512) -> list[float]:
    """Analytic exact-crossing JDs of a piecewise-linear track vs a longitude,
    within [jd0-30, jd1+30] (apron so horizon-edge box semantics is exercised)."""
    lo, hi = jd0 - 30.0, jd1 + 30.0
    out: list[float] = []
    for s_jd0, s_lon0, speed in track.segments:
        if abs(speed) < 1e-12:
            continue
        # crossing offsets: d ≡ (target - lon0) (mod 360) in the direction of
        # travel; t(m) = s_jd0 + (d0 + 360 m) / speed, m ∈ ℤ
        if speed > 0:
            d0 = (target_deg - s_lon0) % 360.0
        else:
            d0 = -((s_lon0 - target_deg) % 360.0)
        m_a = (speed * (lo - s_jd0) - d0) / 360.0
        m_b = (speed * (hi - s_jd0) - d0) / 360.0
        m_lo, m_hi = (m_a, m_b) if speed > 0 else (m_b, m_a)
        import math as _m
        for m in range(_m.ceil(m_lo - 1e-9), _m.floor(m_hi + 1e-9) + 1):
            if len(out) >= max_crossings:
                break
            t = s_jd0 + (d0 + 360.0 * m) / speed
            if lo - 1e-7 <= t <= hi + 1e-7:
                out.append(t)
    return sorted(set(round(t, 9) for t in out))


def make_contact_workload(
    *,
    name: str,
    chart_id: str,
    event_class: str,
    eph: SyntheticEphemeris,
    targets: list[ResonanceTarget],
    contacts: list[tuple[str, str]],  # (body, target_ref) pairs to generate
    jd0: float,
    jd1: float,
    anchors: list[Anchor] | None = None,
    extra_sentences: list[ConfigurationSentence] | None = None,
) -> Workload:
    """Generate degree_contact sentences for every analytic crossing of each
    (body, target) pair inside the horizon (±30 d apron so the box semantics
    at the horizon edges is exercised honestly)."""
    by_ref = {t.target_ref: t for t in targets}
    sentences: list[ConfigurationSentence] = []
    for body, ref in contacts:
        target = by_ref[ref]
        tdeg = float(target.target_longitude_deg)
        for t in _crossing_jds(eph._tracks[body], tdeg, jd0, jd1):
            sentences.append(_sentence("degree_contact", chart_id, event_class,
                                       target, body, t, tdeg))
    if extra_sentences:
        sentences.extend(extra_sentences)
    sentences.sort(key=lambda s: (s.event_jd, s.primitive, s.transit_planet or ""))
    return Workload(
        name=name, chart_id=chart_id, event_class=event_class, eph=eph,
        targets=targets, sentences=sentences, jd0=jd0, jd1=jd1,
        anchors=anchors or [],
    )


# ── Activity-surface series (M-1 battery) ────────────────────────────────────

DECLARED_PROMISE = 0.8
DECLARED_PERMISSION = 0.5


def activity_at(workload: Workload, jd: float, *,
                activity_shape: str = "legacy_box",
                orb_max_deg: float | None = None,
                moon_channel: str = "blended",
                retro_attenuation: float | None = None,
                malefics: tuple[str, ...] = ("Saturn", "Mars"),
                ) -> tuple[float, dict]:
    """Engine activity surface at one JD.

    retro_attenuation: the M-2 probe (test-code only, never engine code) —
    after the engine computes its per-sentence contributions, the p_i of
    sentences whose malefic body is retrograde at jd is multiplied by
    (1 - retro_attenuation) and the noisy-OR is re-formed. None = engine
    output untouched.
    """
    gathered = workload.gathered(jd)
    orbs = None
    if activity_shape == "linear_no_box":
        orbs = {}
        for idx, s in enumerate(gathered):
            tdeg = s.detail.get("target_longitude_deg")
            if not s.transit_planet or tdeg is None:
                continue
            lon, _ = workload.eph.pos(s.transit_planet, jd)
            orbs[idx] = abs(((lon - float(tdeg) + 180.0) % 360.0) - 180.0)
    activity, detail, _tb = engine._compute_activity_v3(
        gathered, workload.weights,
        activity_shape=activity_shape,
        orb_max_deg=orb_max_deg,
        instantaneous_orbs=orbs,
        moon_channel=moon_channel,
    )
    if retro_attenuation is not None:
        product = 1.0
        for c in detail["contributions"]:
            p_i = c["p_i"]
            body = c["transit_planet"]
            if body in malefics and workload.eph.speed(body, jd) < 0.0:
                p_i = p_i * (1.0 - retro_attenuation)
            product *= (1.0 - p_i)
        activity = max(0.0, min(1.0, 1.0 - product))
        detail = {**detail, "retro_attenuation": retro_attenuation,
                  "activity_attenuated": round(activity, 8)}
    return activity, detail


def lam_series(workload: Workload, jds: list[float], **kwargs) -> list[float]:
    """Declared-λ series: PROMISE × PERMISSION × activity (co-factors constant
    across arms by declaration)."""
    return [DECLARED_PROMISE * DECLARED_PERMISSION * activity_at(workload, jd, **kwargs)[0]
            for jd in jds]


# ── Battery metrics ──────────────────────────────────────────────────────────

def active_day_count(series: list[float]) -> int:
    return sum(1 for v in series if v > 0.0)


def windows(series: list[float], jds: list[float]) -> list[tuple[float, float, float]]:
    """Runs of consecutive active days → (start_jd, end_jd, peak_value)."""
    out: list[tuple[float, float, float]] = []
    start = None
    peak = 0.0
    for v, jd in zip(series, jds):
        if v > 0.0:
            if start is None:
                start, peak = jd, v
            else:
                peak = max(peak, v)
            end = jd
        elif start is not None:
            out.append((start, end, peak))
            start = None
    if start is not None:
        out.append((start, end, peak))
    return out


def recall_metrics(series: list[float], jds: list[float],
                   anchors: list[Anchor]) -> dict:
    wins = windows(series, jds)
    peaks_sorted = sorted((w[2] for w in wins), reverse=True)
    background = [v for v, jd in zip(series, jds)
                  if v > 0.0 and all(not (a.jd_center - a.half_days <= jd <= a.jd_center + a.half_days)
                                     for a in anchors)]
    med_background = (sorted(background)[len(background) // 2] if background else 0.0)
    per_anchor = []
    for a in anchors:
        hit = None
        for w in wins:
            if w[0] <= a.jd_center + a.half_days and w[1] >= a.jd_center - a.half_days:
                hit = w
                break
        rank = (peaks_sorted.index(hit[2]) + 1) if hit else None
        margin = (hit[2] - med_background) if hit else 0.0
        per_anchor.append({"label": a.label, "recalled": hit is not None,
                           "rank": rank, "lam_margin": margin})
    return {"anchors": per_anchor,
            "recalled": sum(1 for p in per_anchor if p["recalled"]),
            "of": len(anchors),
            "median_background_lam": med_background}


def dynamic_range(series: list[float], jds: list[float],
                  anchors: list[Anchor] | None = None) -> dict:
    active = [v for v in series if v > 0.0]
    if not active:
        return {"variance_active": 0.0, "peak": 0.0, "median_active": 0.0,
                "peak_over_median": 0.0}
    mean = sum(active) / len(active)
    var = sum((v - mean) ** 2 for v in active) / len(active)
    med = sorted(active)[len(active) // 2]
    peak = max(active)
    return {"variance_active": var, "peak": peak, "median_active": med,
            "peak_over_median": (peak / med) if med > 0 else 0.0}


# ── Full-engine evaluation (§4.11 factor deltas) ─────────────────────────────

def make_context(workload: Workload, *,
                 promise: float = DECLARED_PROMISE,
                 dasha_lord: str = "Jupiter") -> ClassContext:
    nf = NatalFacts(
        graha_longitudes={
            "Moon": 35.75, "Jupiter": 105.50, "Venus": 243.20,
            "Sun": 280.50, "Mars": 23.27, "Saturn": 237.90,
            "Mercury": 275.00,
        },
        graha_signs={},
        lagna_sign=None,
        lagna_longitude=None,
    )
    start = date_of(workload.jd0 - 4000.0)
    end = date_of(workload.jd1 + 4000.0)
    return ClassContext(
        chart_id=workload.chart_id,
        event_class=workload.event_class,
        resonance_targets=tuple(workload.targets),
        promise=promise,
        promise_detail={"calibration_state": "structural_prior"},
        dasha_periods=(
            {"system_id": "vimshottari", "level_n": 1, "lord_graha": dasha_lord,
             "start_iso": start, "end_iso": end},
        ),
        relevant_grahas=frozenset({dasha_lord}),
        relevant_signs=frozenset(),
        temporal_shape="point",
        valence="benefic",
        is_adverse=False,
        beta_e=0.0,
        weight_by_target_ref=workload.weights,
        natal_facts=nf,
    )


def evaluate_full(workload: Workload, jds: list[float],
                  context: ClassContext | None = None,
                  **flag_kwargs) -> list:
    """Full engine._evaluate_single_from_context over a grid, all DB-touching
    primitives patched to the synthetic sentence set."""
    ctx = context or make_context(workload)
    by_ref = {t.target_ref: t for t in workload.targets}

    def fake_primitive(name):
        def fn(_swe, _chart_id, target, start_jd, end_jd):
            return [s for s in workload.sentences
                    if s.primitive == name and s.target_ref == target.target_ref
                    and s.event_jd is not None and start_jd <= s.event_jd <= end_jd]
        return fn

    patches = [
        mock.patch.object(engine, "_get_planet_pos",
                          lambda _swe, body, jd: workload.eph.pos(body, jd)),
        mock.patch.object(engine, "_jd_to_ist_iso", lambda _swe, jd: date_of(jd)),
        mock.patch.object(engine, "_jd_to_date_iso", lambda _swe, jd: date_of(jd)),
        mock.patch.object(engine, "_kakshya_cell_crossing_from_context",
                          lambda *a, **k: []),
        mock.patch.object(engine.SBC, "find_sarvatobhadra_vedha_states",
                          lambda *a, **k: []),
    ]
    for prim in ("degree_contact", "drishti_contact", "sign_ingress",
                 "nakshatra_ingress_tara", "station_retro_loop", "eclipse_degree"):
        patches.append(mock.patch.object(engine.P, prim, fake_primitive(prim)))
    patches.append(mock.patch.object(engine.P, "gochara_vedha_pair", lambda *a, **k: []))

    results = []
    for p in patches:
        p.start()
    try:
        for jd in jds:
            targets = [by_ref[ref] for ref in by_ref]
            results.append(engine._evaluate_single_from_context(
                workload.eph, ctx, jd, targets, **flag_kwargs,
            ))
    finally:
        for p in patches:
            p.stop()
    return results


def factor_row(results: list) -> dict:
    """Mean of each λ factor over a full-engine result grid."""
    n = len(results)
    return {
        "n": n,
        "lambda": sum(r.raw_lambda for r in results) / n,
        "promise": sum(r.promise for r in results) / n,
        "permission": sum(r.permission for r in results) / n,
        "activity": sum(r.x_t for r in results) / n,
        "tara": sum(r.x_t_detail["tara_modifier"] for r in results) / n,
        "w30": sum(r.x_t_detail["w30_modifier"] for r in results) / n,
        "quality_gates": sum(r.x_t_detail["quality_gates"] for r in results) / n,
        "permission_denominator": sum(
            sum(s["weight"] for s in r.permission_detail["systems"])
            for r in results
        ) / n,
    }


def peak_count(series: list[float]) -> int:
    count = 0
    for i in range(1, len(series) - 1):
        if series[i] > 0.0 and series[i] > series[i - 1] and series[i] >= series[i + 1]:
            count += 1
    return count


def slice_contributions(workload: Workload, jds: list[float], **kwargs) -> dict:
    """Summed activity p_i per (primitive, body) slice over the grid."""
    out: dict[tuple[str, str], float] = {}
    for jd in jds:
        _a, detail = activity_at(workload, jd, **kwargs)
        for c in detail["contributions"]:
            key = (c["primitive"], c["transit_planet"] or "?")
            out[key] = out.get(key, 0.0) + c["p_i"]
    return out
