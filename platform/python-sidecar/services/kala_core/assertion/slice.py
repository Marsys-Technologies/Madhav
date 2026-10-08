"""K0a fixture slice: validated judge references → negative space → SQL view.

This is the explicitly selected rehearsal path, not the K3 negative-space
engine. It accepts planted typed conclusions and computes no new rule or score.
The orchestrator owns the transaction; a build without a candidate is a no-op.
"""
from datetime import datetime, time, timezone
from types import SimpleNamespace

from psycopg.rows import tuple_row
from psycopg.types.json import Jsonb

from services.kala_core.assertion import Assertion, NegativeSpacePayload
from services.kala_core.idempotency import replace_candidate_partition
from services.kala_core.manifest import candidate_generation

DARSHANA_SQL = """
SELECT chart_id, generation, assertion_id, assertion, effective_state,
       interval_start, interval_end
FROM kala_obstruction
WHERE chart_id = %s AND generation = %s
ORDER BY assertion_id
"""


def run_fixture_slice(ctx) -> int:
    """Write one explicit fixture assertion into this build's private partition."""
    # The runtime uses dict_row; manifest's positional interface requires a
    # tuple cursor. Keep the caller's connection/row factory unchanged.
    with ctx.db_conn.cursor(row_factory=tuple_row) as cursor:
        return _run_fixture_slice(ctx, cursor)


def _run_fixture_slice(ctx, conn) -> int:
    try:
        generation = candidate_generation(SimpleNamespace(db_conn=conn, build_id=ctx.build_id))
    except LookupError:
        return 0
    row = Assertion.model_validate(ctx.config["kala_assertion_fixture"])
    chart = str(row.chart_id)
    if row.generation != generation or chart != str(ctx.config["chart_id"]):
        raise ValueError("assertion is outside the build's candidate chart and generation")
    binding = conn.execute(
        "SELECT chart_id, state, conventions FROM kala_layer_candidate WHERE build_id = %s FOR UPDATE", (str(ctx.build_id),)
    ).fetchone()
    if str(binding[0]) != chart or binding[1] != "building":
        raise ValueError("only a building candidate bound to this chart can be replaced")
    if binding[2].get("fixture") is not True:
        raise ValueError("the fixture path requires an explicitly opened rehearsal candidate")
    if row.roots.fact_ids or row.roots.contact_ids:
        raise ValueError("fixture path resolves judge window record ids only")
    ids = tuple(dict.fromkeys(row.roots.record_ids))
    expected_parents = {"judge:window:" + record for record in ids}
    if set(row.derivation_parents) != expected_parents:
        raise ValueError("derivation parents must resolve to the fixture judge windows")
    for source_id in ids:
        source = conn.execute(
            "SELECT event_class, window_start, window_end, suppression_state FROM kala_gochara_windows "
            "WHERE id::text = %s AND chart_id = %s AND generation = %s AND source = 'fixture'",
            (source_id, chart, generation),
        ).fetchone()
        if (source is None or source[0] != row.subject.event_class
                or datetime.combine(source[1], time.min, timezone.utc) != row.interval.t0
                or datetime.combine(source[2], time.min, timezone.utc) != row.interval.t1):
            raise ValueError("source id must resolve to the candidate's fixture judge interval")
        derived = NegativeSpacePayload.from_judge_fixture(source[3])
        if derived != row.payload:
            raise ValueError("assertion disagrees with the fixture judge's raw axes")
    if ctx.dry_run:
        return 0
    payload = derived
    encoded = Jsonb(row.model_dump(mode="json"))
    replace_candidate_partition(conn, "kala_obstruction", chart, generation, None, [{
        "chart_id": chart, "generation": generation, "assertion_id": row.assertion_id, "assertion": encoded,
        "exposure": payload.exposure, "knowledge": payload.knowledge, "rule_conclusion": payload.rule_conclusion,
        "defeat_state": payload.defeat_state, "effective_state": payload.effective_state,
        "measurement": payload.measurement, "what": payload.what, "by_what": payload.by_what,
        "release": Jsonb(payload.release.model_dump(mode="json")),
        "interval_start": row.interval.t0, "interval_end": row.interval.t1,
        # Required legacy columns are inert storage compatibility slots. The
        # candidate path and capability use typed state, never these numbers.
        "obstruction_type": "malefic_transit", "severity": "mild", "severity_score": 0.0,
        "override_score": 0.0, "obstruction_detail": Jsonb({}), "source_citation": row.source.locator,
    }])
    rows = []
    for chart_id, gen, assertion_id, assertion, state, t0, t1 in conn.execute(
        DARSHANA_SQL, (chart, generation)
    ).fetchall():
        rows.append({
            "chart_id": str(chart_id), "generation": gen, "assertion_id": assertion_id,
            "assertion": Jsonb(assertion), "candidate_effective_state": state,
            "source_assertion_ids": [assertion_id], "interval_start": t0, "interval_end": t1,
            "effective_score": 0.0, "net_label": "neutral", "source_citation": assertion["source"]["locator"],
        })
    return replace_candidate_partition(conn, "kala_darshana", chart, generation, None, rows)
