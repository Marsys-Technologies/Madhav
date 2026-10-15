"""G1 candidate SQL boundary; no orchestrator or serving changes.

(I) INTERPRETATION: use additive sibling tables for *all* stages, rather than
re-keying populated legacy tables. The fixed stage SQL is adapted here so a
missed WHERE in a stage cannot cross generations. This is deliberately not a
general SQL engine: unsupported writes fail before execution. No connection,
transaction, publication, or credential is owned here.
"""
import re
from types import SimpleNamespace

from psycopg.rows import dict_row

TABLES = (
    'kala_field_provenance','kala_field_salience','kala_insights','kala_timeline_spec',
    'kala_field_windows','kala_field_null','kala_field','kala_field_snapshots',
    'kala_field_primitives','kala_field_boundaries','kala_field_clocks',
    'kala_field_routes','kala_field_promise_edges','kala_field_promise_nodes',
    'kala_field_kinematics','build_substep_progress',
)
_OWNED = '(?:' + '|'.join(sorted(TABLES,key=len,reverse=True)) + ')'


def candidate_sql(query, generation):
    """Scope literal stage statements; preserve bind values and quoted labels.

    SELECTs use generation-filtered relations, INSERTs carry generation and
    conflict keys, DELETEs prepend it to their WHERE. Quoted source_table names
    in stored provenance remain the authoritative logical names.
    """
    if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', generation) or generation in ('legacy','published','retained','current'):
        raise ValueError('explicit fresh candidate generation required')
    if not isinstance(query, str):
        query = query.as_string()
    mask=re.sub(r"'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/", lambda m:' '*len(m[0]),query)
    if re.search(r'\b(?:UPDATE|TRUNCATE|ALTER|DROP)\s+(?:TABLE\s+)?'+_OWNED+r'\b',mask,re.I):
        raise ValueError('unsupported candidate write')
    edits=[]
    literal="'"+generation+"'"  # generation's strict alphabet excludes SQL syntax
    insert=re.search(r'\bINSERT\s+INTO\s+('+_OWNED+r')\s*\(', mask,re.I)
    if insert:
        edits.extend([(insert.start(1),insert.end(1),insert[1]+'_candidate'),(insert.end(),insert.end(),'generation, ')])
        values=re.search(r'\bVALUES\s*\(',mask[insert.end():],re.I)
        if values is None:
            raise ValueError('candidate INSERT requires explicit VALUES')
        pos=insert.end()+values.end(); edits.append((pos,pos,literal+', '))
        conflict=re.search(r'\bON\s+CONFLICT\s*\(',mask,re.I)
        if conflict:
            edits.append((conflict.end(),conflict.end(),'generation, '))
    delete=re.search(r'\bDELETE\s+FROM\s+('+_OWNED+r')\b',mask,re.I)
    if delete:
        where=re.search(r'\bWHERE\b',mask[delete.end():],re.I)
        if where is None: raise ValueError('candidate DELETE requires chart scope')
        pos=delete.end()+where.end()
        edits.extend([(delete.start(1),delete.end(1),delete[1]+'_candidate'),
                      (pos,pos,' generation = '+literal+' AND')])
    for m in re.finditer(r'\b(?:FROM|JOIN)\s+('+_OWNED+r')\b',mask,re.I):
        if delete and m.start(1)==delete.start(1): continue
        table=m[1]
        edits.append((m.start(1),m.end(1),f'(SELECT * FROM {table}_candidate WHERE generation = {literal}) AS {table}'))
    for a,b,value in sorted(edits,reverse=True):
        query=query[:a]+value+query[b:]
    return query


class CandidateCursor:
    def __init__(self, cursor, generation):
        self._cursor=cursor; self.generation=generation
    def execute(self, query, params=None, **kwargs):
        self._cursor.execute(candidate_sql(query,self.generation),params,**kwargs)
        return self
    def executemany(self, query, params, **kwargs):
        self._cursor.executemany(candidate_sql(query,self.generation),params,**kwargs)
        return self
    def __getattr__(self, name): return getattr(self._cursor,name)
    def __enter__(self): self._cursor.__enter__(); return self
    def __exit__(self,*args): return self._cursor.__exit__(*args)
    def __iter__(self): return iter(self._cursor)


class CandidateConnection:
    def __init__(self, conn, generation):
        self.raw=conn; self.generation=generation
    def cursor(self,*args,**kwargs):
        # The retained cohort client requests psycopg2's dictionary cursor.
        # Keep it on the caller's psycopg3 connection; never open another DB.
        if 'cursor_factory' in kwargs:
            from psycopg2.extras import RealDictCursor
            factory = kwargs.pop('cursor_factory')
            if factory is not RealDictCursor:
                raise TypeError('unsupported legacy cursor factory')
            kwargs.setdefault('row_factory', dict_row)
        return CandidateCursor(self.raw.cursor(*args,**kwargs),self.generation)
    def execute(self,query,params=None,**kwargs):
        return self.cursor().execute(query,params,**kwargs)
    def __getattr__(self,name):
        if name in ('commit','rollback','close'):
            raise AttributeError('orchestrator owns transaction and connection')
        return getattr(self.raw,name)


def bind_candidate(ctx, *, lock=False):
    """Validate the explicit build binding; never open/publish a candidate here."""
    generation=ctx.config['kshetra_g1_candidate']
    # Validate alphabet even when the build has no stage rows.
    candidate_sql('SELECT 1',generation)
    from services.kala_core.manifest import Candidate, lock_candidate_inputs
    chart=str(ctx.config['chart_id']); build=str(ctx.build_id)
    if lock:
        with ctx.db_conn.cursor() as cur:
            lock_candidate_inputs(cur,Candidate(chart,generation,build,None))
    with ctx.db_conn.cursor(row_factory=dict_row) as cur:
        cur.execute('SELECT c.*, b.chart_id AS build_chart FROM kala_layer_candidate c '
                    'JOIN build_runs b ON b.id=c.build_id '
                    'WHERE c.chart_id=%s AND c.generation=%s AND c.build_id=%s'+(' FOR UPDATE OF c' if lock else ''),
                    (chart,generation,build))
        candidate=cur.fetchone()
        if candidate is None or candidate['state']!='building' or str(candidate['build_chart'])!=chart:
            raise ValueError('G1 requires a mutable candidate bound to this chart/build')
        convention=(candidate['conventions'] or {}).get('natal',{}).get('ayanamsha_id')
        if convention is not None and convention != 'lahiri_chitrapaksha':
            raise ValueError('G1 canonical ayanamsha differs from candidate convention')
        cur.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s', (chart,))
        if any(row['generation']==generation for row in cur.fetchall()):
            raise ValueError('G1 cannot modify the published generation')
    return CandidateConnection(ctx.db_conn,generation),candidate


def stage_context(ctx, conn):
    return SimpleNamespace(config=ctx.config, db_conn=conn, build_id=ctx.build_id,
                           dry_run=ctx.dry_run, asset_id='ka_kshetra')
