"""
stage8_spec.py — STAGE 8: `kala_timeline_spec v1` (registry item 27).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.1. Lane E owns THIS FILE ONLY inside
`services/ka_kshetra/` (§0's lane table); stages 0–6.5 belong to Lanes A–D.

── WHAT STAGE 8 IS ────────────────────────────────────────────────────────────────────────
The last stage INSIDE the field-hash boundary. It turns the field's own rows — windows
(Lane C), daśā boundaries (Lane B), kinematic events (Lane A) — into a renderer-agnostic
document the portal serialises straight through. Opt-in: MCP token budgets do not pay for it
by default. Persisted: so it is deterministic and hash-replayable, and so no serving path ever
computes a second, possibly divergent, view of the same field.

── FOUR RULES THIS FILE ENFORCES, EACH TRACEABLE TO A RAIL ────────────────────────────────

1. **SINGLE TEMPORAL AUTHORITY (item 44 / brief §7).** Every `intervals[].id` IS a
   `kala_field_windows.window_id`. The spec CITES the field's windows; it never derives one.
   `build_timeline_spec` takes window rows as input and has no window-finding code — a
   serving path that computed its own window is a build error, not a divergence to classify.

2. **B.10 PROSE RULE (brief §7).** Labels here are SHORT, deterministic, template-shaped
   strings assembled from computed values. No sentence is composed, and no generative call
   exists on this path. The argument composer is template-over-computed-data at SERVING time.

3. **LAW ZERO / honest-empty.** A view with nothing to render emits an empty spec WITH a
   machine-readable `empty_reason` (and migration 482's CHECK constraint makes that structural:
   `empty_reason` is non-NULL exactly when the spec has no renderable content). An empty
   `bands` array beside populated `intervals` is a legitimate, silent state — the reason is
   about the WHOLE spec being empty, not about each array.

4. **PRECISION HONESTY (§4.2, §1).** A boundary whose `precision_state` is `'instant'` gets
   NO `*_interval`; one that is `'interval'` carries its 95% bounds; one that is
   `precision_unsupported` is NOT RENDERED AT ALL — serving it as a point would claim a
   precision the input uncertainty cannot support. Every row carries
   `precision_regime = 'day_grade'` at W2; W2G flips it and nothing here may branch on it.

── TIME ───────────────────────────────────────────────────────────────────────────────────
The field's internal axis is days since birth (float). The spec's is ISO calendar dates,
because the renderer is a calendar. `t_zero` (the birth instant) is the only conversion
anchor, it is an argument, and the conversion is a pure function — no clock is read anywhere
in this module, so two runs a day apart produce byte-identical output.

Pure functions. No DB, no clock, no RNG.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Mapping, Sequence

SPEC_VERSION = "kala_timeline_spec/1"

#: §7.1's `generated_for` vocabulary — the six views, and nothing else.
VIEWS = ("now", "ahead", "elect", "story", "priority", "explain")

#: §1 rail: every row W2 writes is day-grade. W2G upgrades the label AND the roots; nothing
#: downstream may branch on `'sub_day'` at W2 other than to pass it through.
PRECISION_DAY_GRADE = "day_grade"

#: §4.2's precision-support rule. A boundary in this state contributes no hazard factor and is
#: served with an honest-empty coverage entry — so it must not appear as a timeline point.
PRECISION_UNSUPPORTED = "precision_unsupported"

VALENCES = ("gain", "loss", "neutral", "mixed")
TIERS = ("structural_prior", "concurrent", "calibrated_provisional", "calibrated")
SHAPES = ("point", "interval", "chain")

EMPTY_NO_RENDERABLE_ROWS = "honest_empty:no_renderable_field_rows_for_this_view"


def days_to_iso(t_zero: datetime, t_days: float) -> str:
    """Days-since-birth → `YYYY-MM-DD`: the calendar day containing `t_zero + t_days`, in
    `t_zero`'s OWN timezone.

    Two things this is deliberately NOT. It is not a ROUND — 23:59 stays on its own day rather
    than being promoted to the next, which would widen every window edge by up to a day. And
    it is not `⌊t_days⌋` days after a notional midnight — the native was born at 10:43 IST, so
    `t = 0.99 d` is the following MORNING and belongs to the following date. Flooring `t`
    before adding would shift every edge in the chart by up to a day, in a direction that
    depends on the birth hour, which is exactly the sort of quiet systematic error a day-grade
    regime cannot afford.
    """
    return (t_zero + timedelta(days=float(t_days))).date().isoformat()


def _iso_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    return str(value)


@dataclass(frozen=True)
class TimelineTrack:
    track_id: str
    kind: str  # 'clock' | 'domain'
    label: str
    row: int

    def to_dict(self) -> dict:
        return {"track_id": self.track_id, "kind": self.kind, "label": self.label, "row": self.row}


def _validate_enum(value: str, allowed: Sequence[str], what: str) -> str:
    if value not in allowed:
        raise ValueError(f"{what} must be one of {tuple(allowed)}; got {value!r}")
    return value


def interval_from_window(
    window: Mapping[str, Any], *, t_zero: datetime, track_id: str
) -> dict:
    """One `intervals[]` entry, built from ONE `kala_field_windows` row.

    `id` is the row's own `window_id` — never regenerated here. Regenerating it (even by the
    same formula) would create a second authority for the same claim, which is exactly what
    item 44's SINGLE TEMPORAL AUTHORITY rail forbids.
    """
    window_id = window.get("window_id")
    if not window_id:
        raise ValueError(
            "a timeline interval must cite an existing kala_field_windows.window_id "
            "(item 44 authority_basis) — this module never derives one"
        )
    out: dict[str, Any] = {
        "id": str(window_id),
        "track_id": track_id,
        "start": days_to_iso(t_zero, window["t_start"]),
        "end": days_to_iso(t_zero, window["t_end"]),
        "peak": days_to_iso(t_zero, window["t_peak"]),
        "valence": _validate_enum(str(window.get("valence", "neutral")), VALENCES, "valence"),
        "tier": _validate_enum(str(window["confidence_tier"]), TIERS, "tier"),
        "shape": _validate_enum(str(window["temporal_shape"]), SHAPES, "shape"),
        "label": str(window.get("label") or window["event_class"]),
        "expected_count": float(window["expected_count"]),
        "null_p": None if window.get("null_p") is None else float(window["null_p"]),
        "precision_regime": str(window.get("precision_regime") or PRECISION_DAY_GRADE),
    }
    # §7.1: `start_interval` / `end_interval` are null when precision_state = 'instant'.
    # Emitting a degenerate [d, d] pair instead would look like a measured interval of width
    # zero rather than like "this edge is known to the day".
    for key, lo_col, hi_col in (
        ("start_interval", "start_interval_lo", "start_interval_hi"),
        ("end_interval", "end_interval_lo", "end_interval_hi"),
    ):
        lo, hi = window.get(lo_col), window.get(hi_col)
        out[key] = (
            None
            if lo is None or hi is None
            else [days_to_iso(t_zero, lo), days_to_iso(t_zero, hi)]
        )
    return out


def point_from_boundary(
    boundary: Mapping[str, Any], *, t_zero: datetime, track_id: str
) -> dict | None:
    """One `points[]` entry from a `kala_field_boundaries` row (Lane B's table).

    Returns `None` for a `precision_unsupported` boundary. That is the §4.2 rule made
    operational: rendering it as a dated point would be serving a claim at a precision the
    birth-time and ayanāṃśa uncertainty cannot support. The caller reports the omission in the
    spec's coverage, so it is a stated gap, not a silent drop.
    """
    if str(boundary.get("precision_state")) == PRECISION_UNSUPPORTED:
        return None
    out: dict[str, Any] = {
        "id": str(boundary["point_id"]),
        "track_id": track_id,
        "at": days_to_iso(t_zero, boundary["t_boundary"]),
        "kind": str(boundary["kind"]),
        "label": str(boundary["label"]),
    }
    lo, hi = boundary.get("interval_lo"), boundary.get("interval_hi")
    out["at_interval"] = (
        None
        if str(boundary.get("precision_state")) == "instant" or lo is None or hi is None
        else [days_to_iso(t_zero, lo), days_to_iso(t_zero, hi)]
    )
    return out


def band_from_row(band: Mapping[str, Any], *, t_zero: datetime, track_id: str) -> dict:
    """One `bands[]` entry — sandhi / eclipse / sade-sati / naisargika-stage spans."""
    return {
        "id": str(band["band_id"]),
        "track_id": track_id,
        "start": days_to_iso(t_zero, band["t_start"]),
        "end": days_to_iso(t_zero, band["t_end"]),
        "kind": str(band["kind"]),
        "label": str(band["label"]),
    }


def build_timeline_spec(
    *,
    chart_id: str,
    generated_for: str,
    t_zero: datetime,
    now_marker: str,
    field_snapshot_id: str,
    weights_version: str,
    tracks: Sequence[TimelineTrack],
    windows: Sequence[Mapping[str, Any]] = (),
    boundaries: Sequence[Mapping[str, Any]] = (),
    bands: Sequence[Mapping[str, Any]] = (),
) -> dict:
    """The whole §7.1 document for one view.

    Every input row names its own `track_id`; a row whose track is not declared in `tracks` is
    an error rather than an invented track — the renderer lays out by row index, and a track
    conjured at render time would land wherever the renderer felt like.

    Ordering is total and deterministic (start date, then id) so two builds of the same
    snapshot are byte-identical, which is what the golden-render test and the field hash both
    depend on.
    """
    _validate_enum(generated_for, VIEWS, "generated_for")
    if not tracks:
        raise ValueError("a timeline spec needs at least one track to lay rows out on")
    declared = {t.track_id for t in tracks}

    def _require_track(row: Mapping[str, Any], kind: str) -> str:
        tid = str(row.get("track_id") or "")
        if tid not in declared:
            raise ValueError(
                f"{kind} row references undeclared track_id {tid!r}; declared: "
                f"{sorted(declared)}"
            )
        return tid

    intervals = [
        interval_from_window(w, t_zero=t_zero, track_id=_require_track(w, "window"))
        for w in windows
    ]
    points = [
        p
        for p in (
            point_from_boundary(b, t_zero=t_zero, track_id=_require_track(b, "boundary"))
            for b in boundaries
        )
        if p is not None
    ]
    band_rows = [
        band_from_row(b, t_zero=t_zero, track_id=_require_track(b, "band")) for b in bands
    ]

    intervals.sort(key=lambda d: (d["start"], d["id"]))
    points.sort(key=lambda d: (d["at"], d["id"]))
    band_rows.sort(key=lambda d: (d["start"], d["id"]))

    n_unsupported = sum(
        1 for b in boundaries if str(b.get("precision_state")) == PRECISION_UNSUPPORTED
    )

    spec: dict[str, Any] = {
        "spec_version": SPEC_VERSION,
        "chart_id": chart_id,
        "field_snapshot_id": field_snapshot_id,
        "generated_for": generated_for,
        "t_zero": t_zero.isoformat(),
        "now_marker": now_marker,
        "tracks": [t.to_dict() for t in sorted(tracks, key=lambda t: (t.row, t.track_id))],
        "intervals": intervals,
        "points": points,
        "bands": band_rows,
        "legend": {"tiers": list(TIERS), "valences": list(VALENCES)},
        "drill": {"instrument": "kala_explain_get", "id_param": "id"},
        # Coverage is DATA on the spec, not prose about it: a consumer can see exactly what
        # was withheld and why, without reading a sentence someone wrote.
        "coverage": {
            "weights_version": weights_version,
            "precision_unsupported_boundaries_omitted": n_unsupported,
            "precision_regime": PRECISION_DAY_GRADE,
        },
    }
    return spec


def spec_counts(spec: Mapping[str, Any]) -> dict:
    """The denormalised counts migration 482 stores beside the blob, plus `empty_reason`.

    `empty_reason` is non-`None` exactly when nothing renderable exists — which is precisely
    the CHECK constraint on `kala_timeline_spec`, so the two cannot drift apart.
    """
    n_intervals = len(spec.get("intervals", []))
    n_points = len(spec.get("points", []))
    n_bands = len(spec.get("bands", []))
    total = n_intervals + n_points + n_bands
    return {
        "n_tracks": len(spec.get("tracks", [])),
        "n_intervals": n_intervals,
        "n_points": n_points,
        "n_bands": n_bands,
        "empty_reason": EMPTY_NO_RENDERABLE_ROWS if total == 0 else None,
    }
