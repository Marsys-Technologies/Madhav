"""Private fixture readers and a lossless legacy shim (KYD-139).

These are preparation views, not issued claims. No stage identity is translated
into a legacy FK or peak date; the conductor must admit that bridge separately.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

from psycopg.rows import dict_row
from pydantic import Field, computed_field, model_validator

from services.kala_core.assertion import Ref, Typed

VERSION = 'k4-2b:reader:v1'
MISSING_MAPPING = 'stage_to_reader_mapping_unadmitted'
IDENTITIES = ('convergence_id', 'signal_id', 'peak_date', 'issuance_identity')
CANDIDATE_SQL = '''SELECT chart_id,generation,event_class,assertion_id,window_start,window_end,
    conditional_effect,witness_signature,conditional_null,pipeline_null,pipeline_null_reason,
    null_reason,coverage,provenance FROM kala_jury_candidate
    WHERE chart_id=%s AND generation=%s ORDER BY event_class,assertion_id'''


class JuryView(Typed):
    contract_version: Literal['k4-2b:reader:v1'] = VERSION
    acceptance_scope: Literal['fixture_only'] = 'fixture_only'
    chart_id: Ref
    generation: Ref
    event_class: Ref
    assertion_id: Ref
    window_start: datetime
    window_end: datetime
    dw: Annotated[float, Field(strict=True, allow_inf_nan=False)] | None
    witness_signature: tuple[Literal['G-P', 'G-J', 'G-T', 'G-K'], ...]
    conditional_null: dict
    pipeline_null: dict | None
    pipeline_null_reason: Ref | None
    null_reason: Ref | None
    coverage: dict
    provenance: dict

    @computed_field
    @property
    def identities(self) -> dict[str, None]:
        return {name: None for name in IDENTITIES}

    @computed_field
    @property
    def unavailable(self) -> dict[str, str]:
        return {name: MISSING_MAPPING for name in IDENTITIES}

    @model_validator(mode='after')
    def private_evidence(self):
        if not self.generation.startswith('candidate:') or self.generation == 'candidate:':
            raise ValueError('explicit private candidate generation required')
        if self.window_start.utcoffset() is None or self.window_end.utcoffset() is None:
            raise ValueError('aware stage interval required')
        if self.window_start >= self.window_end:
            raise ValueError('nonempty half-open stage interval required')
        if len(set(self.witness_signature)) != len(self.witness_signature):
            raise ValueError('duplicate witness cannot gain reader credit')
        if self.provenance.get('acceptance_scope') != 'fixture_only':
            raise ValueError('live jury reader mappings are unadmitted')
        if self.dw is None and not self.null_reason:
            raise ValueError('unavailable D(W) requires a named reason')
        self._validate_null(self.conditional_null, 'jury_incremental_agreement')
        if self.pipeline_null is None:
            if not self.pipeline_null_reason:
                raise ValueError('missing pipeline null requires a named reason')
        else:
            self._validate_null(self.pipeline_null, 'whole_pipeline_selection')
            if self.pipeline_null_reason is not None:
                raise ValueError('available pipeline null cannot carry an unavailable reason')
        return self

    @staticmethod
    def _validate_null(value, estimand):
        if value.get('estimand') != estimand or value.get('verdict') not in {
            'pass', 'fail', 'insufficient_evidence', 'not_evaluable'
        }:
            raise ValueError('stored null qualification required')
        denominator = value.get('denominator')
        if type(denominator) is not int or denominator < 2:
            raise ValueError('stored null denominator required')

    @classmethod
    def from_row(cls, row):
        values = dict(row)
        values['chart_id'] = str(values['chart_id'])
        values['dw'] = values.pop('conditional_effect')
        return cls.model_validate(values)


@dataclass(frozen=True)
class JuryRead:
    source: Literal['legacy', 'candidate']
    rows: tuple[dict, ...] | tuple[JuryView, ...]


def read_jury(ctx, *, generation=None) -> JuryRead:
    """Read stored legacy values or one explicitly bound private fixture.

    The legacy table has no generation column; private rows reside exclusively
    in kala_jury_candidate. Never coalesce, union or fall back between them.
    All queries are SELECTs; the caller owns the connection and transaction.
    """
    chart = str(ctx.config['chart_id'])
    with ctx.db_conn.cursor(row_factory=dict_row) as cur:
        if generation is None:
            cur.execute('SELECT * FROM kala_convergence WHERE chart_id=%s', (chart,))
            return JuryRead('legacy', tuple(cur.fetchall()))
        if not isinstance(generation, str) or not generation.startswith('candidate:') or generation == 'candidate:':
            raise ValueError('explicit private candidate generation required')
        cur.execute('''SELECT chart_id,generation,state,conventions FROM kala_layer_candidate
                       WHERE build_id=%s''', (str(ctx.build_id),))
        binding = cur.fetchone()
        if not binding or str(binding['chart_id']) != chart or binding['generation'] != generation:
            raise ValueError('candidate read outside build/chart/generation binding')
        if binding['state'] not in {'building', 'complete', 'verified'}:
            raise ValueError('candidate state unavailable for preparation read')
        if binding['conventions'].get('fixture') is not True:
            raise ValueError('fixture reader requires conventions.fixture=true')
        cur.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s', (chart,))
        head = cur.fetchone()
        if head and head['generation'] == generation:
            raise ValueError('published candidate cannot use fixture reader')
        cur.execute(CANDIDATE_SQL, (chart, generation))
        return JuryRead('candidate', tuple(JuryView.from_row(row) for row in cur.fetchall()))


def preparation_result(ctx, asset_id):
    """Explicit opt-in consumes candidates without writing unadmitted identities."""
    from pipeline.orchestrator.writers import WriterResult
    result = read_jury(ctx, generation=ctx.config['jury_reader_generation'])
    if result.source != 'candidate':
        raise ValueError('candidate preparation requires an explicit generation')
    return WriterResult(asset_id, 0, notes=(
        f'fixture reader preparation: {len(result.rows)} jury rows; '
        f'{MISSING_MAPPING}; no issuance or legacy output replacement'))
