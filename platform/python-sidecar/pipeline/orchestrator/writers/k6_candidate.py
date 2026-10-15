"""KYD-140 private read-model projections. No live source binding is admitted.

SQL below is the complete computation: no sky, doctrine, grade or probability.
Typed fixtures are validated before candidate replacement in the caller's tx.
"""
from datetime import datetime
from typing import Literal

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field, model_validator

from pipeline.orchestrator.writers import WriterResult
from services.kala_core.idempotency import replace_candidate_partition

VERSION = 'k6-123:read-models:v1'


class Typed(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Source(Typed):
    text: str = Field(min_length=1)
    locator: str = Field(min_length=1)


class Pin(Typed):
    build_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    ayanamsha_id: str = Field(min_length=1)
    qualification: Literal['fixture_only']
    source: Source


class Coverage(Typed):
    state: Literal['complete', 'incomplete', 'absent']
    reason: str | None = None

    @model_validator(mode='after')
    def unavailable(self):
        if self.state != 'complete' and not self.reason:
            raise ValueError('incomplete/absent coverage needs a reason')
        return self


class Evidence(Typed):
    chart_id: str
    generation: str
    scenario_id: str
    ayanamsha_id: str
    source: Source
    provenance: dict


class Span(Evidence):
    start: datetime
    end: datetime
    coverage: Coverage

    @model_validator(mode='after')
    def interval(self):
        if self.start.utcoffset() is None or self.end.utcoffset() is None:
            raise ValueError('aware half-open interval required')
        if self.end <= self.start:
            raise ValueError('nonempty half-open interval required')
        return self


class Mechanism(Evidence):
    mechanism_id: str = Field(min_length=1)
    assertion_id: str = Field(min_length=1)
    event_class: str = Field(min_length=1)
    participant_ids: list[str] = Field(min_length=1)
    constituent_lords: list[str]


class Anchor(Typed):
    system: str | None
    level: int | None = Field(ge=1, le=4)
    lord: str | None
    period_id: str | None
    no_prerequisite: bool = Field(strict=True)

    @model_validator(mode='after')
    def binding(self):
        fields = (self.system, self.level, self.lord, self.period_id)
        if self.no_prerequisite and any(v is not None for v in fields):
            raise ValueError('no-prerequisite anchor cannot carry a period')
        if not self.no_prerequisite and any(v is None or v == '' for v in fields):
            raise ValueError('judge period anchor must be complete')
        return self


class Window(Span):
    assertion_id: str = Field(min_length=1)
    event_class: str = Field(min_length=1)
    participant_ids: list[str] = Field(min_length=1)
    contact_ids: list[str]
    record_ids: list[str]
    operator_role: Literal['scored', 'testimony']
    period_anchor: Anchor
    valence: dict  # the judge's three independent estimands; never combined

    @model_validator(mode='after')
    def testimony(self):
        if self.period_anchor.level == 3 and self.operator_role != 'testimony':
            raise ValueError('PD anchor is testimony, never scored timing')
        if set(self.valence) != {'natal', 'transit', 'occurrence'}:
            raise ValueError('three separate judge valence fields required')
        return self


class Contact(Span):
    contact_id: str = Field(min_length=1)
    occurrence_ordinal: int = Field(ge=1)
    participant_ids: list[str] = Field(min_length=1)


class Condition(Typed):
    participant_conditions: dict
    commencement_condition: dict
    effective_state: str = Field(min_length=1)
    coverage: Coverage


class Period(Span):
    period_id: str = Field(min_length=1)
    assertion_id: str = Field(min_length=1)
    system: str = Field(min_length=1)
    level: int = Field(ge=1, le=4)
    lord: str = Field(min_length=1)
    parent_id: str | None
    sigma_boundary: dict
    dossier: dict
    mechanism_conditions: dict[str, Condition]


class Negative(Evidence):
    assertion_id: str = Field(min_length=1)
    target_assertion_id: str = Field(min_length=1)
    effective_state: str = Field(min_length=1)
    coverage: Coverage


class Jury(Span):
    assertion_id: str = Field(min_length=1)
    event_class: str = Field(min_length=1)
    dw: float | None = Field(allow_inf_nan=False)
    null_reason: str | None
    witness_signature: list[str]
    segment_support: list[dict]

    @model_validator(mode='after')
    def unavailable(self):
        if self.dw is None and not self.null_reason:
            raise ValueError('unavailable D(W) requires null_reason')
        return self


class Context(Span):
    assertion_id: str = Field(min_length=1)
    event_class: str = Field(min_length=1)
    kind: Literal['coverage_gap', 'clock_only', 'uncomputed_method']
    reason: str = Field(min_length=1)


class Forecaster(Span):
    assertion_id: str = Field(min_length=1)
    event_class: str = Field(min_length=1)
    alignment_surprise: float | None = Field(allow_inf_nan=False)
    null_reason: str | None

    @model_validator(mode='after')
    def unavailable(self):
        if self.alignment_surprise is None and not self.null_reason:
            raise ValueError('unavailable alignment surprise requires null_reason')
        return self


class Lel(Evidence):
    event_id: str = Field(min_length=1)
    period_id: str = Field(min_length=1)
    role: Literal['explains', 'selects', 'scores', 'outcome', 'diagnoses']
    used_for_selection: bool = Field(strict=True)


class Bundle(Typed):
    contract_version: Literal['k6-123:read-models:v1']
    as_of: datetime
    primary_ayanamsha: Literal['lahiri_chitrapaksha']
    upstream_refs: dict[str, Pin]
    mechanisms: list[Mechanism]
    windows: list[Window]
    contacts: list[Contact]
    periods: list[Period]
    negative_space: list[Negative]
    jury: list[Jury]
    contexts: list[Context]
    lel: list[Lel]
    forecaster: list[Forecaster] = Field(default_factory=list)


def validate_bundle(value, chart, generation):
    bundle = Bundle.model_validate(value)
    if bundle.as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    pin_names = ['judge', 'F1', 'F2', 'jury', 'negative_space', 'LEL']
    if bundle.forecaster:
        pin_names.append('forecaster')
    for name in pin_names:
        if name not in bundle.upstream_refs:
            raise ValueError(f'explicit {name} upstream pin required')
    if len({(pin.scenario_id, pin.ayanamsha_id) for pin in bundle.upstream_refs.values()}) != 1:
        raise ValueError('one explicit scenario/ayanamsha per fixture projection required')
    groups = [('mechanisms', 'F1', 'mechanism_id'), ('windows', 'judge', 'assertion_id'),
              ('contacts', 'judge', 'contact_id'), ('periods', 'F2', 'period_id'),
              ('negative_space', 'negative_space', 'target_assertion_id'),
              ('jury', 'jury', 'assertion_id'), ('contexts', 'judge', 'assertion_id'),
              ('lel', 'LEL', 'event_id')]
    if bundle.forecaster:
        groups.append(('forecaster', 'forecaster', 'assertion_id'))
    for name, pin_name, key in groups:
        pin = bundle.upstream_refs[pin_name]; seen = set()
        for record in getattr(bundle, name):
            identity = getattr(record, key)
            if identity in seen:
                raise ValueError(f'duplicate {name} {key}')
            seen.add(identity)
            if record.chart_id != chart or record.generation != generation:
                raise ValueError('record outside candidate partition')
            if (record.scenario_id, record.ayanamsha_id) != (pin.scenario_id, pin.ayanamsha_id):
                raise ValueError(f'{name} scenario/ayanamsha pin mismatch')
    contacts = {r.contact_id for r in bundle.contacts}
    mechanisms = {r.mechanism_id for r in bundle.mechanisms}
    windows = {r.assertion_id for r in bundle.windows}
    periods = {r.period_id: r for r in bundle.periods}
    for record in bundle.windows:
        if not set(record.contact_ids) <= contacts:
            raise ValueError('judge contact reference missing')
    for record in bundle.negative_space:
        if record.target_assertion_id not in windows:
            raise ValueError('negative-space target missing')
    for record in bundle.periods:
        if not set(record.mechanism_conditions) <= mechanisms:
            raise ValueError('chapter mechanism reference missing')
        if record.parent_id is not None:
            parent = periods.get(record.parent_id)
            if parent is None or (parent.system, parent.level + 1, parent.scenario_id, parent.ayanamsha_id) != (
                    record.system, record.level, record.scenario_id, record.ayanamsha_id) or not (
                    parent.start <= record.start < record.end <= parent.end):
                raise ValueError('F2 parent lineage mismatch')
        elif record.level > 1:
            raise ValueError('F2 child requires explicit parent')
    for record in bundle.lel:
        if record.period_id not in periods:
            raise ValueError('LEL period reference missing')
    return bundle


_INPUT = '''WITH input AS (SELECT %s::jsonb b),
m AS (SELECT value r FROM input,jsonb_array_elements(b->'mechanisms')),
w AS (SELECT value r FROM input,jsonb_array_elements(b->'windows')),
c AS (SELECT value r FROM input,jsonb_array_elements(b->'contacts')),
p AS (SELECT value r FROM input,jsonb_array_elements(b->'periods')),
n AS (SELECT value r FROM input,jsonb_array_elements(b->'negative_space')),
j AS (SELECT value r FROM input,jsonb_array_elements(b->'jury')),
x AS (SELECT value r FROM input,jsonb_array_elements(b->'contexts')),
l AS (SELECT value r FROM input,jsonb_array_elements(b->'lel')),
f AS (SELECT value r FROM input,jsonb_array_elements(b->'forecaster'))
'''

# Every join keeps the scenario and convention, never an implicit primary.
_SAME = "a.r->>'scenario_id'=b.r->>'scenario_id' AND a.r->>'ayanamsha_id'=b.r->>'ayanamsha_id'"
_OVERLAP = "(a.r->>'start')::timestamptz < (b.r->>'end')::timestamptz AND (b.r->>'start')::timestamptz < (a.r->>'end')::timestamptz"

KALASUTRA_SQL = _INPUT + '''
SELECT jsonb_build_array(a.r->>'mechanism_id','judge',b.r->>'assertion_id')::text model_key,
 'judge' row_kind,(b.r->>'start')::timestamptz interval_start,(b.r->>'end')::timestamptz interval_end,
 jsonb_build_object('mechanism',a.r,'judge',b.r,'period_anchor',b.r->'period_anchor',
   'scored',b.r->>'operator_role'='scored','contact_ids',b.r->'contact_ids',
   'lord_period_ids',COALESCE((SELECT jsonb_agg(p.r->>'period_id' ORDER BY p.r->>'start',p.r->>'period_id')
     FROM p WHERE p.r->>'scenario_id'=a.r->>'scenario_id' AND p.r->>'ayanamsha_id'=a.r->>'ayanamsha_id'
     AND a.r->'constituent_lords' ? (p.r->>'lord')
     AND (p.r->>'start')::timestamptz < (b.r->>'end')::timestamptz
     AND (b.r->>'start')::timestamptz < (p.r->>'end')::timestamptz),'[]'::jsonb)) payload
FROM m a JOIN w b ON ''' + _SAME + '''
 AND a.r->>'event_class'=b.r->>'event_class'
 AND a.r->'participant_ids' ?| ARRAY(SELECT jsonb_array_elements_text(b.r->'participant_ids'))
UNION ALL
SELECT jsonb_build_array(a.r->>'mechanism_id','contact',b.r->>'contact_id')::text,'contact',
 (b.r->>'start')::timestamptz,(b.r->>'end')::timestamptz,
 jsonb_build_object('mechanism',a.r,'contact',b.r,'contact_id',b.r->>'contact_id',
 'occurrence_ordinal',b.r->'occurrence_ordinal','scored',false,
 'search_state',CASE WHEN b.r->'coverage'->>'state'='complete' THEN 'searched' ELSE 'unsearched' END)
FROM m a JOIN c b ON ''' + _SAME + '''
 AND a.r->'participant_ids' ?| ARRAY(SELECT jsonb_array_elements_text(b.r->'participant_ids'))
UNION ALL
SELECT jsonb_build_array(a.r->>'mechanism_id','context',b.r->>'assertion_id')::text,'context',
 (b.r->>'start')::timestamptz,(b.r->>'end')::timestamptz,
 jsonb_build_object('mechanism',a.r,'context',b.r,'search_state','unsearched','scored',false)
FROM m a JOIN x b ON ''' + _SAME + ''' AND a.r->>'event_class'=b.r->>'event_class'
 AND b.r->>'kind'='coverage_gap'
ORDER BY interval_start,model_key
'''

DARSHANA_SQL = _INPUT + '''
SELECT jsonb_build_array('judge',a.r->>'assertion_id')::text model_key,'judge' row_kind,
 (a.r->>'start')::timestamptz interval_start,(a.r->>'end')::timestamptz interval_end,
 jsonb_build_object('judge',a.r,'valence',a.r->'valence','contact_ids',a.r->'contact_ids',
 'negative_space',n.r,'effective_state',COALESCE(n.r->>'effective_state','information_unavailable'),
 'null_reason',CASE WHEN n.r IS NULL THEN 'negative_space_mapping_missing' END,
 'jury',COALESCE((SELECT jsonb_agg(b.r ORDER BY b.r->>'assertion_id') FROM j b WHERE ''' + _SAME + ' AND ' + _OVERLAP + '''
 AND a.r->>'event_class'=b.r->>'event_class'),'[]'::jsonb),
 'forecaster',COALESCE((SELECT jsonb_agg(b.r ORDER BY b.r->>'assertion_id') FROM f b WHERE ''' + _SAME + ' AND ' + _OVERLAP + '''
 AND a.r->>'event_class'=b.r->>'event_class'),'[]'::jsonb)) payload
FROM w a LEFT JOIN n ON n.r->>'target_assertion_id'=a.r->>'assertion_id'
 AND n.r->>'scenario_id'=a.r->>'scenario_id' AND n.r->>'ayanamsha_id'=a.r->>'ayanamsha_id'
UNION ALL
SELECT jsonb_build_array('context',r->>'assertion_id')::text,'context',
 (r->>'start')::timestamptz,(r->>'end')::timestamptz,
 jsonb_build_object('context',r,'effective_state','information_unavailable','null_reason',r->>'reason')
FROM x ORDER BY interval_start,model_key
'''

JIVANA_SQL = _INPUT + ''', chapters AS (
 SELECT r, lag(r->'mechanism_conditions') OVER (
 PARTITION BY r->>'system',r->>'level',r->>'parent_id',r->>'scenario_id',r->>'ayanamsha_id'
 ORDER BY (r->>'start')::timestamptz,r->>'period_id') previous FROM p)
SELECT jsonb_build_array('chapter',a.r->>'period_id')::text model_key,'chapter' row_kind,
 (a.r->>'start')::timestamptz interval_start,(a.r->>'end')::timestamptz interval_end,
 jsonb_build_object('period',a.r,'lord',a.r->>'lord',
 'judge',COALESCE((SELECT jsonb_agg(b.r ORDER BY b.r->>'assertion_id') FROM w b WHERE ''' + _SAME + ' AND ' + _OVERLAP + '''),'[]'::jsonb),
 'jury',COALESCE((SELECT jsonb_agg(b.r ORDER BY b.r->>'assertion_id') FROM j b WHERE ''' + _SAME + ' AND ' + _OVERLAP + '''),'[]'::jsonb),
 'negative_space',COALESCE((SELECT jsonb_agg(n.r ORDER BY n.r->>'assertion_id') FROM n JOIN w b
 ON n.r->>'target_assertion_id'=b.r->>'assertion_id'
 AND n.r->>'scenario_id'=b.r->>'scenario_id' AND n.r->>'ayanamsha_id'=b.r->>'ayanamsha_id'
 WHERE ''' + _SAME + ' AND ' + _OVERLAP + '''),'[]'::jsonb),
 'themes',COALESCE((SELECT jsonb_agg(DISTINCT m.r->>'event_class' ORDER BY m.r->>'event_class') FROM m
 WHERE a.r->'mechanism_conditions' ? (m.r->>'mechanism_id')
 AND a.r->>'scenario_id'=m.r->>'scenario_id' AND a.r->>'ayanamsha_id'=m.r->>'ayanamsha_id'),'[]'::jsonb),
 'lel',COALESCE((SELECT jsonb_agg(l.r ORDER BY l.r->>'event_id') FROM l
 WHERE l.r->>'period_id'=a.r->>'period_id' AND l.r->>'role'='explains'
 AND l.r->>'used_for_selection'='false' AND l.r->>'scenario_id'=a.r->>'scenario_id'
 AND l.r->>'ayanamsha_id'=a.r->>'ayanamsha_id'),'[]'::jsonb),
 'diff',COALESCE((SELECT jsonb_agg(jsonb_build_object('mechanism_id',COALESCE(old.key,new.key),
 'kind',CASE WHEN old.key IS NULL THEN 'new' WHEN new.key IS NULL THEN 'gone' ELSE 'changed' END,
 'before',old.value,'after',new.value,
 'changed_fields',COALESCE((SELECT jsonb_agg(COALESCE(o.key,v.key) ORDER BY COALESCE(o.key,v.key))
 FROM jsonb_each(COALESCE(old.value,'{}'::jsonb)) o FULL JOIN jsonb_each(COALESCE(new.value,'{}'::jsonb)) v
 ON o.key=v.key WHERE o.value IS DISTINCT FROM v.value),'[]'::jsonb)) ORDER BY COALESCE(old.key,new.key))
 FROM jsonb_each(COALESCE(a.previous,'{}'::jsonb)) old
 FULL JOIN jsonb_each(a.r->'mechanism_conditions') new ON old.key=new.key
 WHERE old.value IS DISTINCT FROM new.value),'[]'::jsonb)) payload
FROM chapters a ORDER BY interval_start,model_key
'''

MODELS = {
    'ka_kalasutra': ('kala_activation_candidate', KALASUTRA_SQL),
    'ka_kala_darshana': ('kala_darshana_candidate', DARSHANA_SQL),
    'ka_jivana_parva': ('kala_jivana_parva_candidate', JIVANA_SQL),
}


def run_candidate(ctx, asset_id):
    if ctx.dry_run:
        return WriterResult(asset_id, 0, notes='fixture_only dry_run=True')
    chart = ctx.config['chart_id']; conn = ctx.db_conn
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute('''SELECT generation,state,conventions FROM kala_layer_candidate
            WHERE chart_id=%s AND build_id=%s FOR UPDATE''', (chart, ctx.build_id))
        candidate = cur.fetchone()
        if candidate is None or candidate['state'] != 'building' or not candidate['generation'].startswith('candidate:'):
            raise ValueError('build-bound building candidate required')
        if candidate['conventions'].get('fixture') is not True:
            raise ValueError('live mappings unadmitted; fixture candidate required')
        gen = candidate['generation']
        cur.execute('SELECT 1 FROM kala_layer_head WHERE chart_id=%s AND generation=%s FOR SHARE', (chart, gen))
        if cur.fetchone():
            raise ValueError('cannot replace a published head')
        bundle = validate_bundle(ctx.config['kala_read_model_fixture'], str(chart), gen)
        table, query = MODELS[asset_id]
        cur.execute(query, (Jsonb(bundle.model_dump(mode='json')),))
        projected = cur.fetchall()
    rows = []
    for row in projected:
        payload = row['payload']
        payload['acceptance_scope'] = 'fixture_only'
        if asset_id == 'ka_kalasutra' and row['row_kind'] == 'judge':
            payload['lord_period_concurrent'] = bool(payload['lord_period_ids'])
        judge = payload.get('judge')
        testimony = isinstance(judge, dict) and judge.get('operator_role') == 'testimony'
        rows.append(dict(chart_id=chart, generation=gen, **{k: row[k] for k in
            ('model_key', 'row_kind', 'interval_start', 'interval_end')}, as_of=bundle.as_of,
            payload=Jsonb(payload), upstream_refs=Jsonb(bundle.model_dump(mode='json')['upstream_refs']),
            tier='contextual' if row['row_kind'] == 'context' else 'testimony' if testimony else 'fixture_only'))
    count = replace_candidate_partition(conn, table, chart, gen, None, rows)
    return WriterResult(asset_id, count, notes=f'candidate={gen}; fixture_only; live mappings unadmitted')
