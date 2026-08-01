"""
arms.py — pure, DB-free study-arm classification + the LEL-matcher reuse wrapper for
mi_sankalpa (the Unified Intervention Ledger, registry item 42).

Spec: KALA_W4_UPAYA_DESIGN_v1_0.md §4.3 (the study-arm assignment table) + the binding
instruction: "Reuse services/mi_bhara/living_lel.py's score_predictions_against_event()
rather than writing a second matcher."

No DB, no clock (every timestamp is an argument). The writer (mi_sankalpa.py) is the only
I/O boundary; everything here is a pure function over already-fetched rows, so it is
testable with zero DB fixture setup.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Sequence

from services.mi_bhara.living_lel import (
    LelEventRef,
    OpenPrediction,
    ScoredPrediction,
    score_predictions_against_event,
)

# ── §4.3's study-arm vocabulary (mirrors the migration's CHECK constraint exactly) ─────────

STUDY_ARM_ELECTED_PENDING = "elected_pending"
STUDY_ARM_ACTED_WITH_ELECTION = "acted_with_election"
STUDY_ARM_ELECTED_NOT_ACTED = "elected_not_acted"
STUDY_ARM_ACTED_WITHOUT_ELECTION = "acted_without_election"

STUDY_ARMS = (
    STUDY_ARM_ELECTED_PENDING,
    STUDY_ARM_ACTED_WITH_ELECTION,
    STUDY_ARM_ELECTED_NOT_ACTED,
    STUDY_ARM_ACTED_WITHOUT_ELECTION,
)


def classify_study_arm(
    *,
    performed: bool | None,
    performed_at: datetime | None,
    window_start: datetime,
    window_end: datetime,
) -> str | None:
    """§4.3's study-arm table, arms 1-3. Arm 4 (`acted_without_election`) is never returned
    here — it is ORIGINATED as a new row (see `derive_acted_without_election_rows`-style
    logic in the writer), never reached by reclassifying an existing one.

    Returns:
      - 'elected_pending'       iff performed IS NULL (not yet attested).
      - 'elected_not_acted'     iff performed IS FALSE (attested, real evidence).
      - 'acted_with_election'   iff performed IS TRUE AND performed_at falls inside
                                 [window_start, window_end] (inclusive, matching the
                                 TSTZRANGE's own default '[)' semantics is the caller's
                                 concern via the window bounds it passes in).
      - None                    for the one combination §4.3's table leaves UNSPECIFIED:
                                 performed IS TRUE but performed_at is missing, or falls
                                 OUTSIDE the elected window. A None return means "leave this
                                 row's study_arm UNCHANGED" — LAW ZERO forbids inventing a
                                 disposition the design never named, and a native attestation
                                 (performed) is itself irreplaceable data this function must
                                 never appear to discard by mis-filing it under the wrong arm.
    """
    if performed is None:
        return STUDY_ARM_ELECTED_PENDING
    if performed is False:
        return STUDY_ARM_ELECTED_NOT_ACTED
    # performed is True.
    if performed_at is not None and window_start <= performed_at <= window_end:
        return STUDY_ARM_ACTED_WITH_ELECTION
    return None


def days_since_birth(d: date, birth_date: date) -> float:
    """Converts a calendar date onto the same days-since-birth axis
    `services/mi_bhara/db.py`'s LEL/prediction reads use, so this package's LEL matching
    agrees with the field's own units. `birth_date` is read from `ctx.config['birth_params']`
    by the writer, never recomputed from an ephemeris here (§N.5)."""
    return float((d - birth_date).days)


def score_ledger_rows_against_lel_event(
    event: LelEventRef, open_rows: Sequence[OpenPrediction]
) -> list[ScoredPrediction]:
    """Named pass-through to `living_lel.score_predictions_against_event` — kept as its own
    function purely so a reader of `mi_sankalpa.py` sees the §4.3 "reuse, don't write a
    second matcher" decision named at the call site, not buried in an import list."""
    return score_predictions_against_event(event, open_rows)


@dataclass(frozen=True)
class UnelectedLelEvent:
    """One LEL event whose class already appears among this chart's OWN filed
    interventions, with no existing `elected_window` (of ANY study_arm — an event covered
    by an existing election, resolved or not, is not "without election") covering its date.
    The writer turns this into a new `acted_without_election` row."""

    event_id: str
    event_class: str
    event_date: date


def find_unelected_lel_events(
    *,
    lel_events: Sequence[LelEventRef],
    known_event_classes: Sequence[str],
    birth_date: date,
    covered_windows_by_class: dict[str, Sequence[tuple[datetime, datetime]]],
) -> list[UnelectedLelEvent]:
    """§4.3 arm 4: "a LEL event of the same class with no matching ledger row inside its
    window."

    `known_event_classes` scopes the search to classes this chart has ALREADY filed at
    least one intervention for — the only principled way to know a class is
    "intervention-relevant" without inventing a mapping this design never specified (an
    event class never elected here is not a class this writer has any basis to originate
    an `acted_without_election` row for). `covered_windows_by_class` carries every existing
    ledger row's `elected_window` (any study_arm) for that class, so an event already
    covered by ANY prior election — resolved, pending, or attested — is correctly excluded.
    """
    out: list[UnelectedLelEvent] = []
    known = set(known_event_classes)
    for ev in lel_events:
        if ev.event_class not in known:
            continue
        event_date = birth_date + timedelta(days=ev.t)
        windows = covered_windows_by_class.get(ev.event_class, ())
        covered = any(w_start.date() <= event_date <= w_end.date() for (w_start, w_end) in windows)
        if not covered:
            out.append(UnelectedLelEvent(event_id=ev.event_id, event_class=ev.event_class, event_date=event_date))
    return out
