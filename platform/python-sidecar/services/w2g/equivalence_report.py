"""W2G — the equivalence-report tool (native ruling point 3, design §3).

THE RULING THIS MODULE EXISTS TO SATISFY (SHAD_DARSHANA_STATE.md, "RULING —
Lane G / W2G write-target", 2026-08-06), point 3, verbatim: "The protected
corpus is W2G's frozen validation benchmark: W2G acceptance REQUIRES an
equivalence report against it (per the design doc's criteria), verified by
PARĪKṢAKA."

THE DESIGN DOC'S CRITERIA THIS MODULE IMPLEMENTS
(`GOCHARA_SWEEP_2_0_DESIGN_v1_0.md` §3):

  §3.1 Equivalence corpus check. v1's fully-materialized century table is
       ground truth. 2.0 must reproduce v1's windows (same event-classes,
       overlapping bounds within 1 day -- v1's own resolution) WHEREVER v1
       was right. Implemented by `match_rows` (per-event-class, greedy
       nearest-date, one-to-one, `DEFAULT_MATCH_TOLERANCE_DAYS`-day window).
  §3.2 Documented-divergence protocol. Where 2.0 differs, each divergence is
       classified with evidence: (a) v1 grid artifact (chunk-edge bounds,
       midnight snapping) -- 2.0 correct; (b) v1 Moon-undersampling miss --
       2.0 found a real sub-day window v1 couldn't see (the expected headline
       finding); (c) genuine 2.0 bug -- fix. NO divergence ships unclassified.
       Implemented by `classify_v1_only`/`classify_v2_only` (heuristic,
       evidence-based, honestly falling to a "needs human review" bucket --
       itself one of the closed `ALL_CLASSIFICATIONS` values, never `None`
       -- when neither named pattern's evidence is present) plus a direct,
       non-heuristic classification for a MATCHED pair whose valence/
       is_adverse disagree (no ambiguity there: same instant, same class,
       different verdict IS a genuine-bug signal, not a candidate for (a)/(b)).
  §3.3-3.5 Specimen continuity / determinism / adversarial probes / post-
       cutover battery. Per the native ruling's own point 4 framing ("if
       equivalence-testing reveals..."), and per this lane's explicit
       instruction ("don't need the full machinery if that's a larger
       undertaking -- build what's reasonably scoped, honestly report what's
       deferred"), THIS MODULE DOES NOT IMPLEMENT THESE. `EquivalenceReport.
       deferred` names them explicitly on every report this module produces
       -- never silently absent, always disclosed alongside whatever WAS
       measured.

WHAT THIS MODULE IS NOT: it does not read a database. `build_equivalence_report`
takes already-fetched row dicts (from either `kala_gochara_windows` -- v1,
read-only -- or `kala_gochara_windows_v2` -- this writer's own table) and
returns a pure, deterministic report. The DB read itself lives in
`scripts/w2g_equivalence_report.py` (read-only against v1, per the ruling;
its own writes, if any -- there are none -- would go nowhere near v1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Mapping, Optional, Sequence

# ── Closed classification vocabulary (design §3.2) ────────────────────────────
# Every divergence gets EXACTLY one of these. Never None, never a free-text
# string outside this set -- `EquivalenceReport.unclassified()` checks
# membership in `ALL_CLASSIFICATIONS`, and the end-to-end builder asserts it
# is empty on every report it produces (see this module's own test suite).

CLASS_V1_GRID_ARTIFACT = "v1_grid_artifact"
CLASS_V1_MOON_UNDERSAMPLING_MISS = "v1_moon_undersampling_miss"
CLASS_GENUINE_2_0_BUG_VALENCE_MISMATCH = "genuine_2_0_bug_valence_mismatch"
CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW = "unclassified_v1_only_needs_review"
CLASS_UNCLASSIFIED_V2_ONLY_NEEDS_REVIEW = "unclassified_v2_only_needs_review"

ALL_CLASSIFICATIONS = frozenset({
    CLASS_V1_GRID_ARTIFACT,
    CLASS_V1_MOON_UNDERSAMPLING_MISS,
    CLASS_GENUINE_2_0_BUG_VALENCE_MISMATCH,
    CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW,
    CLASS_UNCLASSIFIED_V2_ONLY_NEEDS_REVIEW,
})

# design §3.1's own stated resolution bound.
DEFAULT_MATCH_TOLERANCE_DAYS = 1

# Heuristic net for "this might be the SAME real event, just grid-shifted
# beyond the 1-day match tolerance" -- wider than the match tolerance on
# purpose (a grid-snap artifact can drift more than a day; an unrelated
# event usually will not have ANY nearby row on the other side at all,
# which is exactly the signal that separates class (a) from the
# needs-review buckets). Disclosed as a heuristic, not a certainty -- see
# module docstring §3.2.
WIDE_DRIFT_DAYS = 4

# Best-effort signal for "a fast body (chiefly the Moon) drove this
# candidate" -- design §3.2(b)'s named expected finding. Read from
# `active_sentences[].transit_planet` (see `GenerationRow.from_db_row`).
# Deliberately NOT the only fast body in principle, but the Moon is the one
# named explicitly in both the design doc and the ruling's own framing, and
# it is the dominant undersampling case in the daily-grid v1 by a wide
# margin (13 deg/day vs. the next-fastest eager-tier body).
MOON_UNDERSAMPLING_BODIES = frozenset({"Moon"})

DEFERRED_ITEMS = (
    "§3.3 specimen continuity (D-5/D-4b named specimens reproducing, e.g. "
    "windfall plateau overlap, both 2013 marriage peaks incl. the "
    "double-transit at its exact timestamps) -- NOT implemented this lane; "
    "would need each named specimen's exact expected shape re-derived "
    "against 2.0's output, a larger undertaking than this lane's scope.",
    "§3.4 determinism + adversarial probes (byte-identical re-derivation, "
    "cache-poisoning class probes on the spline/event caches) -- NOT "
    "implemented this lane; this lane's substrate (bg_gochara_arcs) predates "
    "the spline/event-calendar architecture §3.4 describes and has no cache "
    "layer of that kind to probe yet.",
    "§3.5 post-cutover full regression battery + D-4b gate scoring-assertion "
    "re-run on 2.0 data -- not applicable: this lane does not cut over "
    "(native ruling point 3 defers corpus disposition to a W6 ruling); there "
    "is no 'post-cutover' state yet to battery-test.",
)


# ── Row model ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GenerationRow:
    """One served window, from either generation, shape-normalized for
    comparison. Deliberately carries only the fields the comparison actually
    needs -- not every `kala_gochara_windows`/`kala_gochara_windows_v2`
    column."""

    event_class: str
    temporal_shape: str
    peak_date: date
    window_start: date
    window_end: date
    is_adverse: bool
    valence: str
    signed_intensity: float
    generation: str
    transit_planets: frozenset[str] = field(default_factory=frozenset)

    @staticmethod
    def from_db_row(d: Mapping[str, Any]) -> "GenerationRow":
        """Best-effort `transit_planet` extraction from `active_sentences` --
        honestly empty (not a fabricated guess) when the field is absent or
        empty, which `classify_v2_only` treats as "no Moon-undersampling
        evidence available", not as "definitely not Moon-driven"."""
        sentences = d.get("active_sentences") or []
        planets = frozenset(
            s["transit_planet"] for s in sentences
            if isinstance(s, dict) and s.get("transit_planet")
        )
        return GenerationRow(
            event_class=d["event_class"],
            temporal_shape=d["temporal_shape"],
            peak_date=d["peak_date"],
            window_start=d["window_start"],
            window_end=d["window_end"],
            is_adverse=d["is_adverse"],
            valence=d["valence"],
            signed_intensity=float(d["signed_intensity"]),
            generation=d["generation"],
            transit_planets=planets,
        )


@dataclass(frozen=True)
class MatchedPair:
    v1: GenerationRow
    v2: GenerationRow
    date_diff_days: int
    valence_agrees: bool


@dataclass(frozen=True)
class Divergence:
    kind: str             # "v1_only" | "v2_only" | "valence_mismatch"
    classification: str   # one of ALL_CLASSIFICATIONS -- never None
    event_class: str
    peak_date: date
    evidence: str


# ── Scoping (design §3.1's comparable-set definition) ─────────────────────────


def scope_v1_rows(
    v1_rows: Sequence[GenerationRow],
    *,
    classes_attempted_by_v2: Sequence[str],
    horizon_start: date,
    horizon_end: date,
) -> tuple[list[GenerationRow], dict[str, str]]:
    """Splits v1 rows into (comparable, out_of_scope_reason_by_class).

    A v1 row is IN SCOPE for comparison only if ALL of:
      * temporal_shape == 'point' (2.0 materializes point shapes only, this
        lane -- interval/chain are honestly deferred, per materialize.py's
        own docstring);
      * its event_class is one 2.0 actually attempted this run (a class 2.0
        never touched cannot honestly be scored either way);
      * its peak_date falls inside 2.0's progressive horizon (2.0 never
        claims coverage outside it -- a v1 row from outside the horizon is
        neither confirmed NOR contradicted by this run, so it is excluded
        from scope rather than silently counted as a miss).

    Out-of-scope reasons are recorded PER CLASS (first reason wins) --
    this is a coverage-scope disclosure, not a divergence; §3.2's
    classification vocabulary does not apply to it."""
    in_scope: list[GenerationRow] = []
    out_of_scope: dict[str, str] = {}
    attempted = set(classes_attempted_by_v2)
    for row in v1_rows:
        if row.temporal_shape != "point":
            out_of_scope.setdefault(
                row.event_class,
                f"temporal_shape={row.event_class!r}={row.temporal_shape!r} "
                f"is not 'point' -- interval/chain deferred, not materialized by 2.0 this lane",
            )
            continue
        if row.event_class not in attempted:
            out_of_scope.setdefault(
                row.event_class,
                "2.0 never attempted this event_class this run -- no comparable data on either side",
            )
            continue
        if not (horizon_start <= row.peak_date <= horizon_end):
            out_of_scope.setdefault(
                row.event_class,
                f"at least one v1 row (peak_date={row.peak_date}) falls outside 2.0's "
                f"progressive horizon {horizon_start}..{horizon_end} -- neither confirmed nor "
                f"contradicted by this run",
            )
            continue
        in_scope.append(row)
    return in_scope, out_of_scope


# ── Matching (design §3.1) ────────────────────────────────────────────────────


def match_rows(
    v1_rows: Sequence[GenerationRow],
    v2_rows: Sequence[GenerationRow],
    *,
    tolerance_days: int = DEFAULT_MATCH_TOLERANCE_DAYS,
) -> tuple[list[MatchedPair], list[GenerationRow], list[GenerationRow]]:
    """Per-event_class, greedy nearest-date, one-to-one matching within
    `tolerance_days` (design §3.1's own stated 1-day resolution bound).

    Greedy-by-smallest-diff: every candidate (v1_row, v2_row) pair sharing an
    event_class and within tolerance is a candidate; candidates are consumed
    smallest-diff-first, each row usable in at most one match -- this keeps
    the matching deterministic and prefers the closest available pairing
    over an arbitrary first-found one when multiple candidates compete for
    the same row (see `test_match_rows_greedy_prefers_closest_date_one_to_one`)."""
    candidates: list[tuple[int, int, int]] = []  # (diff_days, v1_idx, v2_idx)
    for i, v1r in enumerate(v1_rows):
        for j, v2r in enumerate(v2_rows):
            if v1r.event_class != v2r.event_class:
                continue
            diff = abs((v1r.peak_date - v2r.peak_date).days)
            if diff <= tolerance_days:
                candidates.append((diff, i, j))
    candidates.sort(key=lambda t: t[0])

    matched_v1: set[int] = set()
    matched_v2: set[int] = set()
    pairs: list[MatchedPair] = []
    for diff, i, j in candidates:
        if i in matched_v1 or j in matched_v2:
            continue
        matched_v1.add(i)
        matched_v2.add(j)
        v1r, v2r = v1_rows[i], v2_rows[j]
        pairs.append(MatchedPair(
            v1=v1r, v2=v2r, date_diff_days=diff,
            valence_agrees=(v1r.valence == v2r.valence and v1r.is_adverse == v2r.is_adverse),
        ))

    v1_only = [r for idx, r in enumerate(v1_rows) if idx not in matched_v1]
    v2_only = [r for idx, r in enumerate(v2_rows) if idx not in matched_v2]
    return pairs, v1_only, v2_only


# ── Classification (design §3.2) ──────────────────────────────────────────────


def classify_v1_only(row: GenerationRow, v2_same_class: Sequence[GenerationRow],
                      *, wide_days: int = WIDE_DRIFT_DAYS) -> Divergence:
    """v1 has a row 2.0 did not reproduce within tolerance. Evidence-based
    classification, honestly falling to "needs review" absent evidence:

      * a 2.0 row for the SAME class exists within `wide_days` (wider than
        the match tolerance) -> candidate (a) v1 grid artifact: v1's daily-
        grid snap likely landed the window a few days off from 2.0's
        arc-solved exact instant. This is a CANDIDATE, disclosed as such in
        `evidence` -- not a certainty a heuristic can establish alone.
      * otherwise -> (c)-adjacent: no positive evidence either way, so this
        is reported as `CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW`, not
        silently folded into (a) or (c). Per design §3.2, this still counts
        as "classified" (it is one of `ALL_CLASSIFICATIONS`) -- it is the
        honest "needs a human/PARĪKṢAKA look" bucket, not an unclassified gap."""
    nearby = [r for r in v2_same_class if abs((r.peak_date - row.peak_date).days) <= wide_days]
    if nearby:
        closest = min(nearby, key=lambda r: abs((r.peak_date - row.peak_date).days))
        drift = abs((closest.peak_date - row.peak_date).days)
        return Divergence(
            kind="v1_only", classification=CLASS_V1_GRID_ARTIFACT,
            event_class=row.event_class, peak_date=row.peak_date,
            evidence=f"v1 daily-grid row with no 2.0 match inside {DEFAULT_MATCH_TOLERANCE_DAYS}d, "
                     f"but a 2.0 row for the same class exists {drift}d away "
                     f"(peak_date={closest.peak_date}) -- candidate v1 grid-snap artifact, "
                     f"2.0's arc-solved date likely the more accurate one",
        )
    return Divergence(
        kind="v1_only", classification=CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW,
        event_class=row.event_class, peak_date=row.peak_date,
        evidence=f"v1 row (peak_date={row.peak_date}) has no 2.0 match within "
                 f"{DEFAULT_MATCH_TOLERANCE_DAYS}d OR {wide_days}d -- no automatic evidence for "
                 f"grid-artifact; candidate genuine 2.0 miss, needs PARĪKṢAKA/human review",
    )


def classify_v2_only(row: GenerationRow, v1_same_class: Sequence[GenerationRow],
                      *, wide_days: int = WIDE_DRIFT_DAYS) -> Divergence:
    """2.0 has a row v1 did not have within tolerance. Evidence-based
    classification, checked in this order:

      1. the candidate is Moon-driven (`row.transit_planets` intersects
         `MOON_UNDERSAMPLING_BODIES`) -> (b) v1 Moon-undersampling miss --
         design §3.2's named EXPECTED headline finding: v1's daily grid
         cannot resolve a fast body's sub-day contact, 2.0's arc-solver can.
      2. a v1 row for the same class exists within `wide_days` -> candidate
         (a) v1 grid artifact (the mirror of `classify_v1_only`'s check).
      3. otherwise -> `CLASS_UNCLASSIFIED_V2_ONLY_NEEDS_REVIEW` -- a
         genuinely new 2.0 finding with no automatic corroborating evidence
         either that it is expected (Moon) or that v1 was simply grid-off.
         Could be a real, non-Moon sub-day finding OR a genuine 2.0 bug --
         a heuristic cannot tell those apart, so this is exactly the honest
         "needs review" case, not silently defaulted to either bucket."""
    if row.transit_planets & MOON_UNDERSAMPLING_BODIES:
        return Divergence(
            kind="v2_only", classification=CLASS_V1_MOON_UNDERSAMPLING_MISS,
            event_class=row.event_class, peak_date=row.peak_date,
            evidence=f"2.0-only row (peak_date={row.peak_date}) driven by "
                     f"{sorted(row.transit_planets & MOON_UNDERSAMPLING_BODIES)} -- v1's daily grid "
                     f"cannot resolve a fast body's sub-day contact; expected headline finding per design §3.2(b)",
        )
    nearby = [r for r in v1_same_class if abs((r.peak_date - row.peak_date).days) <= wide_days]
    if nearby:
        closest = min(nearby, key=lambda r: abs((r.peak_date - row.peak_date).days))
        drift = abs((closest.peak_date - row.peak_date).days)
        return Divergence(
            kind="v2_only", classification=CLASS_V1_GRID_ARTIFACT,
            event_class=row.event_class, peak_date=row.peak_date,
            evidence=f"2.0-only row with a v1 row for the same class {drift}d away "
                     f"(peak_date={closest.peak_date}) -- candidate v1 grid-snap artifact",
        )
    return Divergence(
        kind="v2_only", classification=CLASS_UNCLASSIFIED_V2_ONLY_NEEDS_REVIEW,
        event_class=row.event_class, peak_date=row.peak_date,
        evidence=f"2.0-only row (peak_date={row.peak_date}), not Moon-driven, no nearby v1 row "
                 f"within {wide_days}d -- could be a real new non-Moon sub-day finding or a genuine "
                 f"2.0 bug; needs PARĪKṢAKA/human review",
    )


# ── The end-to-end report ─────────────────────────────────────────────────────


@dataclass
class EquivalenceReport:
    chart_id: str
    horizon_start: date
    horizon_end: date
    classes_compared: list[str]
    classes_out_of_scope: dict[str, str]
    v1_in_scope_count: int
    v2_count: int
    matched: list[MatchedPair]
    divergences: list[Divergence]
    deferred: tuple[str, ...] = DEFERRED_ITEMS

    @property
    def equivalent_count(self) -> int:
        return sum(1 for m in self.matched if m.valence_agrees)

    @property
    def equivalence_rate(self) -> Optional[float]:
        """`equivalent matches / v1-in-scope rows`. Honest `None` (not a
        fabricated 0.0 or 1.0) when there is nothing in scope to score --
        §N.7 item 6, an honest null beats an invented judgment."""
        if self.v1_in_scope_count == 0:
            return None
        return self.equivalent_count / self.v1_in_scope_count

    def unclassified(self) -> list[Divergence]:
        return [d for d in self.divergences if d.classification not in ALL_CLASSIFICATIONS]

    def summary(self) -> dict[str, Any]:
        by_classification: dict[str, int] = {}
        for d in self.divergences:
            by_classification[d.classification] = by_classification.get(d.classification, 0) + 1
        return {
            "chart_id": self.chart_id,
            "horizon_start": self.horizon_start.isoformat(),
            "horizon_end": self.horizon_end.isoformat(),
            "classes_compared": self.classes_compared,
            "classes_out_of_scope": self.classes_out_of_scope,
            "v1_in_scope_count": self.v1_in_scope_count,
            "v2_count": self.v2_count,
            "matched_count": len(self.matched),
            "equivalent_count": self.equivalent_count,
            "equivalence_rate": self.equivalence_rate,
            "divergence_count": len(self.divergences),
            "divergences_by_classification": by_classification,
            "unclassified_count": len(self.unclassified()),
            "divergences": [
                {
                    "kind": d.kind, "classification": d.classification,
                    "event_class": d.event_class, "peak_date": d.peak_date.isoformat(),
                    "evidence": d.evidence,
                }
                for d in self.divergences
            ],
            "deferred": list(self.deferred),
        }


def build_equivalence_report(
    chart_id: str,
    v1_rows_raw: Sequence[Mapping[str, Any]],
    v2_rows_raw: Sequence[Mapping[str, Any]],
    *,
    horizon_start: date,
    horizon_end: date,
    classes_attempted_by_v2: Sequence[str],
    tolerance_days: int = DEFAULT_MATCH_TOLERANCE_DAYS,
    wide_days: int = WIDE_DRIFT_DAYS,
) -> EquivalenceReport:
    """The full design-§3 comparison, from raw DB-row dicts (either
    generation's shape) to a disclosed, fully-classified report.

    Pure function: takes already-fetched rows, does no I/O. The caller
    (`scripts/w2g_equivalence_report.py`) is responsible for fetching v1
    READ-ONLY and this writer's own 2.0 rows, and passing them in."""
    v1_rows = [GenerationRow.from_db_row(d) for d in v1_rows_raw]
    v2_rows = [GenerationRow.from_db_row(d) for d in v2_rows_raw]

    v1_in_scope, out_of_scope = scope_v1_rows(
        v1_rows, classes_attempted_by_v2=classes_attempted_by_v2,
        horizon_start=horizon_start, horizon_end=horizon_end,
    )

    matched, v1_only, v2_only = match_rows(v1_in_scope, v2_rows, tolerance_days=tolerance_days)

    divergences: list[Divergence] = []
    for pair in matched:
        if not pair.valence_agrees:
            divergences.append(Divergence(
                kind="valence_mismatch", classification=CLASS_GENUINE_2_0_BUG_VALENCE_MISMATCH,
                event_class=pair.v1.event_class, peak_date=pair.v1.peak_date,
                evidence=f"matched at the SAME instant (diff={pair.date_diff_days}d) but v1 says "
                         f"valence={pair.v1.valence!r}/is_adverse={pair.v1.is_adverse} while 2.0 says "
                         f"valence={pair.v2.valence!r}/is_adverse={pair.v2.is_adverse} -- same event, "
                         f"disagreeing verdict, no heuristic ambiguity here",
            ))

    for row in v1_only:
        same_class_v2 = [r for r in v2_rows if r.event_class == row.event_class]
        divergences.append(classify_v1_only(row, same_class_v2, wide_days=wide_days))

    for row in v2_only:
        same_class_v1 = [r for r in v1_in_scope if r.event_class == row.event_class]
        divergences.append(classify_v2_only(row, same_class_v1, wide_days=wide_days))

    classes_compared = sorted({r.event_class for r in v1_in_scope} | {r.event_class for r in v2_rows})

    return EquivalenceReport(
        chart_id=chart_id, horizon_start=horizon_start, horizon_end=horizon_end,
        classes_compared=classes_compared, classes_out_of_scope=out_of_scope,
        v1_in_scope_count=len(v1_in_scope), v2_count=len(v2_rows),
        matched=matched, divergences=divergences,
    )


__all__ = [
    "ALL_CLASSIFICATIONS",
    "CLASS_GENUINE_2_0_BUG_VALENCE_MISMATCH",
    "CLASS_UNCLASSIFIED_V1_ONLY_NEEDS_REVIEW",
    "CLASS_UNCLASSIFIED_V2_ONLY_NEEDS_REVIEW",
    "CLASS_V1_GRID_ARTIFACT",
    "CLASS_V1_MOON_UNDERSAMPLING_MISS",
    "DEFAULT_MATCH_TOLERANCE_DAYS",
    "DEFERRED_ITEMS",
    "MOON_UNDERSAMPLING_BODIES",
    "WIDE_DRIFT_DAYS",
    "Divergence",
    "EquivalenceReport",
    "GenerationRow",
    "MatchedPair",
    "build_equivalence_report",
    "classify_v1_only",
    "classify_v2_only",
    "match_rows",
    "scope_v1_rows",
]
