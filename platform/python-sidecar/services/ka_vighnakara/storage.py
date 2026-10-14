"""KYD-134 explicit fixture preparation in private candidate storage only.

Legacy required score columns are inert compatibility slots. Interpretation
and consumers use the typed axes exclusively; no numeric measure is derived.
"""
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT
from services.kala_core.stored_verification import has_stored_verification

from psycopg.rows import tuple_row
from psycopg.types.json import Jsonb

from services.kala_core.idempotency import replace_candidate_partition
from services.ka_vighnakara.model import Finding, VERSION, interpret


def write_fixture_candidate(ctx, inputs: list[Finding]) -> int:
    """Validate every input before replacing one build-bound fixture partition."""
    if ctx.dry_run:
        return 0
    chart = str(ctx.config['chart_id'])
    with ctx.db_conn.cursor(row_factory=tuple_row) as cursor:
        binding = cursor.execute(
            'SELECT chart_id,generation,state,conventions FROM kala_layer_candidate '
            'WHERE build_id=%s FOR UPDATE', (str(ctx.build_id),)).fetchone()
        if binding is None or str(binding[0]) != chart or binding[2] != 'building':
            raise ValueError('only a building candidate bound to this chart may be replaced')
        generation = binding[1]
        head = cursor.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s FOR SHARE',
                              (chart,)).fetchone()
        if head is not None and head[0] == generation:
            raise ValueError('a published head cannot be replaced')
        if binding[3].get('fixture') is not True:
            raise ValueError('fixture preparation requires an explicitly opened fixture candidate')
        if not generation.startswith('candidate:') or generation == 'candidate:':
            raise ValueError('a private candidate partition is required')
        if any(str(value.chart_id) != chart or value.generation != generation for value in inputs):
            raise ValueError('input lies outside the build candidate partition')
        if len({value.assertion_id for value in inputs}) != len(inputs):
            raise ValueError('duplicate assertion identity')
        # Labels, prose, protection facts and edge targets are evidence, not
        # physical identity. Refuse aliases before replacing the partition.
        physical = {}
        for value in inputs:
            key = (value.chart_id, value.generation, value.event_class_id, value.mechanism,
                   tuple(sorted(set(value.roots.record_ids))),
                   tuple(sorted(set(value.roots.contact_ids))))
            physical.setdefault(key, []).append((value.interval.t0, value.interval.t1))
        for intervals in physical.values():
            ordered = sorted(intervals)
            if any(start < previous_end for (_, previous_end), (start, _)
                   in zip(ordered, ordered[1:])):
                raise ValueError('duplicate physical conclusion under overlapping assertion aliases')
        # A label-only singleton rebuild has no peer to expose its alias. The
        # envelope cannot resolve a stale target to immutable roots, so refuse
        # overlapping evidence rather than silently dropping or retargeting it.
        if any(edge.target_assertion_id != value.assertion_id
               and edge.interval.t0 < value.interval.t1 and edge.interval.t1 > value.interval.t0
               for value in inputs for edge in value.protections):
            raise ValueError('overlapping protection target cannot be resolved to this physical conclusion')
        store_tier = has_stored_verification(cursor, 'kala_obstruction')
        rows = []
        for value in inputs:
            result = interpret(value)
            if result is None:
                continue
            assertion = result.model_dump(mode='json')
            # PG16 JSONPath .datetime() rejects Pydantic's UTC "Z" suffix.
            # Preserve each evidence instant with an explicit numeric offset
            # so migration 1374 can check its half-open interval overlap.
            for payload, edge in zip(assertion['protections'], result.protections):
                payload['interval'] = {key: getattr(edge.interval, key).isoformat()
                                       for key in ('t0', 't1')}
            row = {key: getattr(result, key) for key in ('generation','assertion_id','event_class_id',
                   'exposure','knowledge','rule_conclusion','defeat_state','effective_state','measurement',
                   'what','by_what','null_reason','release_reason')}
            row.update(chart_id=chart, negative_space_contract_version=VERSION,
                       assertion=Jsonb(assertion),
                       roots=Jsonb(result.roots.model_dump(mode='json')),
                       release=Jsonb(result.release.model_dump(mode='json')),
                       interval_start=result.interval.t0, interval_end=result.interval.t1,
                       obstruction_type='malefic_transit', severity='mild',
                       severity_score=0, override_score=0, obstruction_detail=Jsonb({}),
                       source_citation=result.source.locator)
            if store_tier:
                row["verification_pass_status"] = UNVERIFIED_DEFAULT
            rows.append(row)
        return replace_candidate_partition(cursor, 'kala_obstruction', chart, generation, None, rows)
