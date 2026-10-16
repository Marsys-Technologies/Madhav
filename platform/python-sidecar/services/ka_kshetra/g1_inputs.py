"""G1 input conventions (ALGO §3.20 c–e; PLAN §8.1 ruling 4).

(I) INTERPRETATION: partial/contested obstructions have no scalar strength in
K3. Retain an unavailable-term disclosure instead of inventing a fraction.
KA-3b mūrti is testimony: its intervals are retained without a numeric bridge; this does not qualify the adapter or calibrate odds.
"""
from datetime import datetime, timedelta, timezone
import math

from .stage1_symbolization import PrimitiveRow, _box_envelope, build_moorti_primitive

CANONICAL_AYANAMSHA = 'lahiri_chitrapaksha'
SECONDS_PER_DAY = 86400.0  # SI day; same UT axis as ephemeris_daily
JD_UNIX_EPOCH = 2440587.5  # Julian date at 1970-01-01 00:00 UT


def instant(value):
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('instant requires an explicit UTC offset')
    return result.astimezone(timezone.utc)


def birth_instant(config):
    params = config.get('birth_params') or {}
    if not params.get('datetime_iso'):
        raise ValueError('explicit birth_params.datetime_iso required')
    birth = datetime.fromisoformat(params['datetime_iso'])
    if birth.tzinfo is None:
        if 'tz_offset_hours' not in params:
            raise ValueError('birth offset required')
        birth = birth.replace(tzinfo=timezone(timedelta(hours=float(params['tz_offset_hours']))))
    return instant(birth)


def pinned_as_of(config):
    if not config.get('as_of'):
        raise ValueError('explicit as_of required for G1 candidate')
    return instant(config['as_of'])


def field_days(value, birth):
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise ValueError('finite Julian date required')
        value = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=value-JD_UNIX_EPOCH)
    return (instant(value) - instant(birth)).total_seconds() / SECONDS_PER_DAY


def suppression_primitives(chart, birth, vedha, moorti, negative, *, allow_fixture=False):
    """Reference upstream intervals; never derive a transit or cancellation.

    Cancelled candidates contribute no obstruction. Missing strength is a gap,
    not a cancellation or an invented 0.5. All referenced interval edges survive.
    """
    out, gaps = [], []
    def mask(subject, source, ref, start, end, state):
        lo,hi=field_days(start,birth),field_days(end,birth)
        out.append(PrimitiveRow(chart,'input_mask',subject,lo,hi,[(lo,0.),(hi,0.)],
            'neutral',class_label=state,source_kind='l3_row',source_table=source,source_pk=ref))
    for row in vedha:
        if row['state'] != 'active':
            mask(row['graha'],'kala_vedha_gochara_interval',row.get('source_ref'),row['t_in'],row['t_out'],row['state'])
            if row['state'] == 'unqualified':
                gaps.append({'source_ref':row.get('source_ref'), 'reason':'vedha_unqualified'})
            continue
        lo,hi=field_days(row['t_in'],birth),field_days(row['t_out'],birth)
        out.append(PrimitiveRow(chart,'vedha',row['graha'],lo,hi,_box_envelope(lo,hi,1.),'obstructive',
            object_ref=row.get('source_ref'),class_label=row['vedha_kind'],source_kind='l3_row',
            source_table='kala_vedha_gochara_interval',source_pk=row.get('source_ref')))
    for row in moorti:
        if row.get('null_reason') or row.get('quality_tier') is None:
            gaps.append({'source_ref':row.get('source_ref'), 'reason':'moorti_information_unavailable'})
            continue
        lo,hi=field_days(row['t_in'],birth),field_days(row['t_out'],birth)
        p=build_moorti_primitive(chart,row['graha'],lo,hi,row['moorti_name'],int(row['quality_tier']))
        p.primitive_kind='moorti_testimony'; p.polarity='neutral'
        p.source_kind='l3_row'; p.source_table='kala_moorti_nirnaya_candidate'; p.source_pk=row.get('source_ref')
        out.append(p)
        gaps.append({'source_ref':row.get('source_ref'), 'reason':'moorti_uncited_legacy_testimony;numeric_bridge_not_admitted'})
    for row in negative:
        state=row['effective_state']
        scope=(row.get('assertion') or {}).get('acceptance_scope')
        if scope != 'fixture_only' or not allow_fixture or state != 'obstruction_in_force':
            mask(row['assertion_id'],'kala_obstruction',row['assertion_id'],row['interval_start'],row['interval_end'],state)
        if scope != 'fixture_only' or not allow_fixture:
            gaps.append({'source_ref':row['assertion_id'], 'reason':'negative_space_binding_not_admitted'})
            continue
        gaps.append({'source_ref':row['assertion_id'], 'reason':'fixture_only_prebuild'})
        if state != 'obstruction_in_force':
            if state in ('obstruction_partly_cancelled','obstruction_contested','information_unavailable'):
                gaps.append({'source_ref':row['assertion_id'],'reason':state})
            continue
        lo,hi=field_days(row['interval_start'],birth),field_days(row['interval_end'],birth)
        out.append(PrimitiveRow(chart,'negative_space',row['assertion_id'],lo,hi,_box_envelope(lo,hi,1.),
            'obstructive',class_label='event_class:'+row['event_class_id'],source_kind='l3_row',
            source_table='kala_obstruction',source_pk=row['assertion_id']))
    return out,gaps


def load_suppression(conn, chart, generation, birth):
    """Read only this candidate/convention; absence remains machine-readable."""
    from psycopg.rows import dict_row
    gaps=[]
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute('SELECT conventions FROM kala_layer_candidate WHERE chart_id=%s AND generation=%s', (chart,generation))
        binding=cur.fetchone()
        allow_fixture=bool(binding and binding['conventions'].get('fixture') is True)
        cur.execute('SELECT * FROM kala_vedha_gochara_interval WHERE chart_id=%s AND generation=%s '
                    'AND ayanamsha_id=%s ORDER BY vedha_kind,graha,t_in', (chart,generation,CANONICAL_AYANAMSHA))
        vedha=cur.fetchall()
        for row in vedha:
            row['source_ref']=':'.join((generation,row['vedha_kind'],row['graha'],instant(row['t_in']).isoformat()))
        from services.kala_core.overlays.contested_reader import load_candidate_payload
        payload=load_candidate_payload(conn,chart_id=chart,generation=generation,
                                       ayanamsha_id=CANONICAL_AYANAMSHA,family='moorti_nirnaya')
        moorti=[]
        if payload is not None:
            gaps.append({'source_ref':'moorti_nirnaya','reason':'testimony_only',
                         'coverage':payload.coverage,'upstream_fingerprint':payload.upstream_fingerprint,
                         'method_qualification':payload.method_qualification})
            for entry in payload.entries:
                row=dict(entry); row['source_ref']=f"{generation}:moorti:{row['graha']}:{row['t_in']}"
                moorti.append(row)
        cur.execute('SELECT assertion_id,effective_state,interval_start,interval_end,event_class_id,assertion '
                    'FROM kala_obstruction WHERE chart_id=%s AND generation=%s ORDER BY assertion_id', (chart,generation))
        negative=cur.fetchall()
    for name,rows in [('vedha',vedha),('moorti',moorti),('negative_space',negative)]:
        if not rows:
            gaps.append({'source_ref':name,'reason':'information_unavailable'})
    prims,detail=suppression_primitives(chart,birth,vedha,moorti,negative,allow_fixture=allow_fixture)
    return prims,gaps+detail
