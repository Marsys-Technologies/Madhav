"""
bo_pratijna -- Promise Register (L2 Bodha)
==========================================
PRATIJÑĀ v4.1.0 -- writer wiring (Lane B2 follow-on; F1 ADOPTION CYCLE, R22, 2026-08-09).

Production default flipped from v4.0 (amendments unset) to v4.1.0
(amendments={'F1'}) per ruling R22 on the evidence of `F1_SIDE_BY_SIDE_v1_0.md`
-- see `V4_RUBRIC_SPEC_v1_0.md` §2.1.1 and `F1_CYCLE_STATE.md` (adoption
phase). The `amendments` parameter on `PratijnaV4Engine` remains available,
unremoved, for future R20 cycles (F3/F7/F6a/F6b and beyond) -- this writer
simply now supplies a non-empty default instead of none.

Reads chart_divisionals / chart_facts / chart_fact_identity (exclusively
through `brahmagyan.chart_reader_v4.ChartReaderV4`, per §N.2's per-writer
read discipline and R19) via `bo_pratijna_v4_engine.PratijnaV4Engine` ->
writes bodha_pratijna.

This is the FROZEN-contract LIGHT writer (`run(ctx)`, no sub-steps) that
wires the standalone, independently PARĪKṢAKA-verified v4 scoring library
(`bo_pratijna_v4_engine.py`, Lane B2, Rung P5 GREEN -- exact reproduction
of RUNG_P3_HAND_WORKED_v1_0.md's hand-worked numbers on chart 482012f1)
into the actual orchestrator build. The engine itself is untouched by this
lane; this module only calls it and persists its output.

── What replaced what ──────────────────────────────────────────────────────
The v3 writer (ENGINE_VERSION="bo_pratijna_v3.0", git history) matched
`bodha_msr_signals` rows to event classes via a fuzzy karyatva/domain
partition. That approach is RETIRED here -- not reused, not imported --
because it is the exact defect class this whole PRATIJÑĀ v4 campaign
exists to fix (MSR-signal partitioning historically produced IDENTICAL
grades for marriage vs separation from identical evidence; see
`PRATIJNA_ENGINE_V3_SPEC_v1_0.md §1` and this campaign's own checkpoint
question). v4 instead derives each of the 27 event classes' occurrence
[0,1] and condition [0,10] grades from classical significator maps
(`bo_pratijna_karyatva.KARYATVA_REGISTRY`) applied to L1-sourced dignity/
placement/aspect facts read through the Chart Reader -- no MSR signal
matching anywhere in this path.

── The central design decision: mapping v4's 5-band occurrence reading
   onto the pre-existing 4-value `status` CHECK constraint ─────────────────
`bodha_pratijna.status` (migrations 391 + 545) only accepts
'promised' / 'denied' / 'conditional' / 'no_evidence'. `V4_RUBRIC_SPEC_v1_0.
md §6.1` defines FIVE equal-width occurrence bands (DENIED / WEAK /
MODERATE / STRONG / VERY_STRONG), written blind, before any chart was
scored. This writer does NOT introduce a new column or a reverse-engineered
cutoff; it reuses the rubric's own a-priori band semantics directly:

    DENIED                   -> status = 'denied'
    WEAK, MODERATE            -> status = 'conditional'
    STRONG, VERY_STRONG       -> status = 'promised'
    engine status='no_evidence' (no karyatva map for the class -- should
        not occur now that KARYATVA_REGISTRY covers all 27 classes, kept
        as an honest defensive path) -> status = 'no_evidence'

Why this mapping and not another, stated plainly (R13/R16):
  1. §6.1's own text for the DENIED band reads "Classical evidence for this
     event's occurrence is largely absent, OR has been actively negated by
     a named denial configuration (§4)" -- i.e. the spec ITSELF already
     defines DENIED as the union of "no evidence" and "actively negated",
     which is exactly what the pre-existing `status='denied'` column value
     means. No new judgment is added by this mapping; it is a direct
     restatement of the rubric's own written definition, chosen BEFORE
     looking at what this produces on any specific chart's rows.
  2. The two thresholds this collapses to (0.60 for promised, 0.20 for
     denied) are numerically IDENTICAL, after unit conversion, to the
     pre-existing v3 writer's own `_PROMISED_FLOOR = 6.0` / `_DENIED_CEIL
     = 2.0` on its [0,10] grade scale (6.0/10 = 0.60, 2.0/10 = 0.20) --
     this mapping does not invent a new promised/denied line, it reuses
     the one downstream consumers (`ka_avadhi`, `mi_darshana`,
     `ph_nimitta`) already read against, at the same relative position.
  3. WEAK and MODERATE both collapse to 'conditional' rather than splitting
     WEAK into 'denied' or MODERATE into 'promised' -- keeping the mapping
     monotonic and boundary-preserving (every band maps to exactly one
     status, no band straddles two statuses) was preferred over any
     alternative split, because a non-monotonic mapping would let two
     charts with a HIGHER occurrence score end up with a "worse" status,
     which no reading of §6.1 supports.
  4. This mapping was written by reading §6.1's own prose FIRST, before
     computing what it does to chart 482012f1's marriage/separation/
     childbirth numbers (Rung P5: 0.321->WEAK->conditional, 0.505->
     MODERATE->conditional, 0.593->MODERATE->conditional). Their exact
     margins to the nearest STATUS-CHANGING threshold ({0.20, 0.60} --
     0.40 is a band edge but not a status-changing one, since both WEAK
     and MODERATE map to 'conditional'): marriage is 0.121 from 0.20;
     separation is 0.095 from 0.60; childbirth is only **0.007** from the
     STRONG/MODERATE boundary at 0.60 -- close enough that a status of
     'promised' rather than 'conditional' would have resulted from an
     occurrence 0.007 higher. This proximity is disclosed plainly, not
     minimized: it is NOT evidence of R13 chart-fitting, because neither
     number that produces it was chosen with this chart in view --
     the 0.20/0.40/0.60/0.80 band edges come from V4_RUBRIC_SPEC_v1_0.md
     §6.1, written and committed before any chart was scored (R20 blind-
     definition discipline), and the 0.60/0.20 status-collapse thresholds
     this mapping reuses are inherited UNCHANGED from the pre-existing v3
     writer's own `_PROMISED_FLOOR`/`_DENIED_CEIL` constants (reason #2
     above) -- nothing in this writer's own logic could have nudged 0.60
     to move childbirth off it. The proximity is a property of the v4
     engine's classical-factor arithmetic on this chart (Lane B2, out of
     this lane's scope to touch), not of the status-mapping choice audited
     here; it is recorded so a future reader -- or a future rebuild after
     any Lane B2 fix -- knows this specific class sits right at a status
     edge and is worth a second look, not so it can be quietly smoothed
     over.

No new migration is required for this mapping (§N.4): `occurrence_grade`
and `condition_grade` (NUMERIC(5,3), migration 548) already exist and
carry the full-fidelity v4-native values (occurrence in [0,1], condition
in [0,10] -- the SAME scale range as before but an OPPOSITE polarity on
condition: v3's condition was a favorability scale, v4's is an affliction-
MAGNITUDE scale per V4_RUBRIC_SPEC_v1_0.md §5.2 -- documented in
`derivation` per row, not silently re-using the old meaning). The 5-band
occurrence/condition LABELS themselves (DENIED/WEAK/.../CLEAN/MILD/...)
are not discarded -- they are carried in full inside the `derivation` JSONB
column (`occurrence_label`, `condition_label`), so no information the v4
rubric was built to add is lost; only the narrower 4-state `status` summary
column loses resolution, exactly as it always has for any bounded-enum
column.

── grade (legacy compatibility) ────────────────────────────────────────────
`ph_nimitta`, `ka_taranga`, `ka_yojaka` all read `bodha_pratijna.grade` on
its pre-existing [0,10] "higher = more promised" scale (e.g. `ka_taranga.
py`'s own comment: "promise_contribution — bodha_pratijna grade/10"). This
writer keeps `grade` on that same scale/polarity for those NOT-YET-AUDITED
consumers (Lane B4, consumer audit, is explicitly out of scope for this
lane) via `grade = round(occurrence * 10, 3)` -- a straight unit rescale of
the v4-native occurrence axis, not a new formula. `occurrence_grade` /
`condition_grade` carry the true v4-native values for any reader that wants
them directly.

`supporting_signal_ids` / `contradicting_signal_ids` (UUID[], referencing
`bodha_msr_signals.signal_id`) are always NULL under v4: this engine never
reads `bodha_msr_signals` at all (see "what replaced what" above), so there
is nothing honest to put in those columns. This is a real, disclosed
capability difference from v3, not an oversight.

`varga_confirmation` (JSONB) is populated from the class's own divisional
(varga) factor-ledger entry when one was scored (the slot v4 dedicates to
divisional-chart confirmation, §2.4) -- a natural, non-invented fit for a
column that already existed for exactly this purpose and was always NULL
under v3.

LIGHT writer: one run() call. §N.3: per-chart delete-then-insert,
idempotent, ON CONFLICT (chart_id, ayanamsha_id, event_class_id) DO UPDATE
(unchanged from v3).

R19: this writer's own DB access is limited to (a) the idempotent
delete-then-insert against `bodha_pratijna` and (b) whatever
`ChartReaderV4`/`PratijnaV4Engine` read internally (`chart_divisionals`,
`chart_facts`, `chart_fact_identity`, `brahma_reference_planets` --
all READ-ONLY, never `chart_facts`/`chart_divisionals` writes).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from brahmagyan.chart_reader_v4 import ChartReaderV4

from . import WriterBase, ContextSpec, WriterResult, register
from .bo_pratijna_v4_engine import ClassScore, PratijnaV4Engine

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_pratijna_v4.1.0"
FORMULA_VERSION = "v4.1.0"

# R22 adoption (2026-08-09): production default amendment set. F1
# (dispositor-conjunction exception, V4_RUBRIC_SPEC_v1_0.md §2.1.1) is now
# applied by default. Future R20 cycles add their own amendment id here
# only after their own adoption ruling -- this constant is the single
# point that gates production behavior, never a per-call literal.
DEFAULT_AMENDMENTS: frozenset[str] = frozenset({"F1"})

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

_STATUS_NO_EVIDENCE = "no_evidence"
_STATUS_DENIED = "denied"
_STATUS_CONDITIONAL = "conditional"
_STATUS_PROMISED = "promised"

# §6.1 band -> status column mapping (see module docstring for the full
# R13/R16 reasoning -- this table is the single source of truth for it).
_OCCURRENCE_BAND_TO_STATUS: dict[str, str] = {
    "DENIED": _STATUS_DENIED,
    "WEAK": _STATUS_CONDITIONAL,
    "MODERATE": _STATUS_CONDITIONAL,
    "STRONG": _STATUS_PROMISED,
    "VERY_STRONG": _STATUS_PROMISED,
}


def status_from_occurrence_label(occurrence_label: str) -> str:
    """Map V4_RUBRIC_SPEC_v1_0.md §6.1's occurrence band label to the
    pre-existing `bodha_pratijna.status` CHECK-constrained vocabulary.
    See module docstring for the full reasoning; this function is the
    single point that implements it (unit-testable without a DB)."""
    try:
        return _OCCURRENCE_BAND_TO_STATUS[occurrence_label]
    except KeyError as exc:
        raise ValueError(
            f"Unknown occurrence_label {occurrence_label!r} -- not one of "
            f"V4_RUBRIC_SPEC_v1_0.md §6.1's five bands"
        ) from exc


_PRATIJNA_INSERT = """
INSERT INTO bodha_pratijna (
    pratijna_id, chart_id, ayanamsha_id, build_id,
    event_class_id, status, grade,
    occurrence_grade, condition_grade,
    supporting_signal_ids, contradicting_signal_ids,
    varga_confirmation, derivation, formula_version,
    computed_at, engine_version
) VALUES (
    %(pratijna_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
    %(event_class_id)s, %(status)s, %(grade)s,
    %(occurrence_grade)s, %(condition_grade)s,
    %(supporting_signal_ids)s, %(contradicting_signal_ids)s,
    %(varga_confirmation)s, %(derivation)s, %(formula_version)s,
    %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, event_class_id)
DO UPDATE SET
    status = EXCLUDED.status,
    grade = EXCLUDED.grade,
    occurrence_grade = EXCLUDED.occurrence_grade,
    condition_grade = EXCLUDED.condition_grade,
    supporting_signal_ids = EXCLUDED.supporting_signal_ids,
    contradicting_signal_ids = EXCLUDED.contradicting_signal_ids,
    varga_confirmation = EXCLUDED.varga_confirmation,
    derivation = EXCLUDED.derivation,
    formula_version = EXCLUDED.formula_version,
    computed_at = EXCLUDED.computed_at,
    engine_version = EXCLUDED.engine_version
"""


def _varga_confirmation_from_ledger(score: ClassScore) -> dict | None:
    """Pull the divisional-slot factor_ledger entry (§2.4), if this class
    scored one, into the pre-existing `varga_confirmation` JSONB column --
    a natural fit for a column that was always NULL under v3 and exists
    specifically for divisional-chart confirmation evidence."""
    for entry in score.factor_ledger:
        if entry.get("slot") == "divisional":
            return entry
    return None


def _row_for_score(
    *, chart_id: str, aya: str, build_id: str, event_class_id: str,
    score: ClassScore, now: str,
) -> dict:
    if score.status == "no_evidence":
        return {
            "pratijna_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "event_class_id": event_class_id,
            "status": _STATUS_NO_EVIDENCE,
            "grade": None,
            "occurrence_grade": None,
            "condition_grade": None,
            "supporting_signal_ids": None,
            "contradicting_signal_ids": None,
            "varga_confirmation": None,
            "derivation": json.dumps({
                "engine_version": ENGINE_VERSION,
                "rubric_version": score.rubric_version,
                "reason": "no KaryatvaMap registered for this event_class_id",
            }),
            "formula_version": FORMULA_VERSION,
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        }

    status = status_from_occurrence_label(score.occurrence_label)
    grade = round(score.occurrence * 10.0, 3) if score.occurrence is not None else None
    varga_confirmation = _varga_confirmation_from_ledger(score)
    derivation = {
        "engine_version": score.engine_version,
        "rubric_version": score.rubric_version,
        "occurrence_label": score.occurrence_label,
        "condition_label": score.condition_label,
        "occurrence_pre_denial": score.occurrence_pre_denial,
        "status_mapping_rule": (
            "V4_RUBRIC_SPEC_v1_0.md §6.1 occurrence band -> status: "
            "DENIED->denied, WEAK/MODERATE->conditional, "
            "STRONG/VERY_STRONG->promised"
        ),
        "weights": score.weights,
        "factor_ledger": score.factor_ledger,
        "denials": score.denials,
        "condition_ledger": score.condition_ledger,
        "provenance": score.provenance,
    }
    return {
        "pratijna_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "event_class_id": event_class_id,
        "status": status,
        "grade": grade,
        "occurrence_grade": score.occurrence,
        "condition_grade": score.condition,
        "supporting_signal_ids": None,
        "contradicting_signal_ids": None,
        "varga_confirmation": json.dumps(varga_confirmation) if varga_confirmation is not None else None,
        "derivation": json.dumps(derivation),
        "formula_version": FORMULA_VERSION,
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
    }


@register("bo_pratijna")
class BoPratijnaWriter(WriterBase):
    """bo_pratijna -- Promise Register (L2 Bodha), PRATIJÑĀ v4.1.0 (R22 adoption)."""

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config.get("chart_id")
        build_id = ctx.build_id
        conn = ctx.db_conn
        now = datetime.now(timezone.utc).isoformat()

        # Idempotency: delete prior rows for this chart (§N.3).
        # Disable per-statement timeout for the heavy DELETE on large charts.
        # SET LOCAL scopes to the orchestrator txn (writer never commits).
        conn.execute("SET LOCAL statement_timeout = 0")
        conn.execute("DELETE FROM bodha_pratijna WHERE chart_id=%s", [chart_id])

        rows_inserted = 0
        no_evidence_count = 0
        status_counts: dict[str, int] = {}

        for aya in CANONICAL_AYAS:
            reader = ChartReaderV4(conn, ayanamsha=aya)
            engine = PratijnaV4Engine(reader, amendments=DEFAULT_AMENDMENTS)
            scores = engine.score_all(chart_id)

            for event_class_id, score in scores.items():
                row = _row_for_score(
                    chart_id=chart_id, aya=aya, build_id=build_id,
                    event_class_id=event_class_id, score=score, now=now,
                )
                conn.execute(_PRATIJNA_INSERT, row)
                rows_inserted += 1
                status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
                if row["status"] == _STATUS_NO_EVIDENCE:
                    no_evidence_count += 1

        logger.info(
            "[bo_pratijna] chart=%s: %d rows inserted (%d no_evidence); status_counts=%s",
            chart_id, rows_inserted, no_evidence_count, status_counts,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_inserted,
            notes=(
                f"engine={ENGINE_VERSION};ayanamshas={len(CANONICAL_AYAS)};"
                f"no_evidence={no_evidence_count};status_counts={status_counts}"
            ),
        )
