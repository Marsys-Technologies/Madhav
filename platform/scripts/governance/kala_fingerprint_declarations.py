"""K8 additive, opt-in chart fingerprint adapter; no census verdict changes.

(I) INTERPRETATION: this first tranche accepts PARTIAL declarations only. All
retained rows of each declared table are measured, never a selected generation.
No exclusions are admitted yet: build/row/generation identities and every new
column remain semantic. L0/global fingerprint definitions and certificate records
are untouched; the changed shared declarations hash needs custodian reconciliation.
The separate engine/custodian review required by PACKET_K8-REG §3–4 remains an
admission gate; the returned measurement is never a full/current/PASS signal.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
DEFINITION = 'nikasha_stale_certs.table_fingerprint/1'
_IDENT = re.compile(r'[a-z_][a-z0-9_]{0,62}')
_KEYS = {'status','fingerprint_definition','scope','coverage','groups','tables','not_covered_tables'}
_TABLE_KEYS = {'name','scope','key','key_evidence','exclude','naive_utc_columns','write_evidence'}


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()


def _evidence(ref, suffixes=('.py','.sql')):
    if not isinstance(ref,str) or not (match:=re.fullmatch(r'([^:]+):([1-9][0-9]*)',ref)):
        raise ValueError('fingerprint evidence needs a repository file:line')
    rel,line=match[1],int(match[2])
    path=ROOT/rel
    if (Path(rel).is_absolute() or '..' in Path(rel).parts or path.suffix not in suffixes
        or '__tests__' in path.parts or 'tests' in path.parts or not path.is_file()
        or not path.resolve().is_relative_to(ROOT.resolve())):
        raise ValueError('fingerprint evidence must name real non-test repository code')
    text=path.read_text(); lines=text.splitlines()
    if line>len(lines):raise ValueError('fingerprint evidence line does not exist')
    return path,text,'\n'.join(lines[line-1:line+29])


def validate(asset_id, declaration):
    """Validate optional partial L3 metadata without granting a detector verdict."""
    if declaration is None:return None
    if not isinstance(asset_id,str) or not re.fullmatch(r'ka_[a-z0-9_]+',asset_id):
        raise ValueError('fingerprint extension accepts ka_* assets only')
    d=declaration
    if not isinstance(d,Mapping) or set(d)!=_KEYS:
        raise ValueError('fingerprint has missing or unknown fields')
    if (d['status']!='declared' or d['fingerprint_definition']!=DEFINITION or d['scope']!='chart'
        or d['coverage']!='partial' or d['groups']!=[]):
        raise ValueError('first chart fingerprints require declared/partial/chart and no groups; no PASS/full claim')
    if not isinstance(d['tables'],list) or not 1<=len(d['tables'])<=8:
        raise ValueError('fingerprint needs one to eight evidenced tables')
    names=set()
    for table in d['tables']:
        if not isinstance(table,dict) or set(table)!=_TABLE_KEYS:
            raise ValueError('fingerprint table has missing or unknown fields')
        name=table['name']; key=table['key']
        if not isinstance(name,str) or not _IDENT.fullmatch(name) or name in names:
            raise ValueError('fingerprint table name is invalid or duplicated')
        names.add(name)
        if table['scope']!='chart' or table['exclude']!=[] or table['naive_utc_columns']!=[]:
            raise ValueError('first chart fingerprints permit no exclusions or timestamp reinterpretation')
        if (not isinstance(key,list) or not key or any(not isinstance(k,str) or not _IDENT.fullmatch(k) for k in key)
            or len(set(key))!=len(key) or not {'chart_id','generation'}<=set(key)):
            raise ValueError('fingerprint key must retain chart and generation identity')
        _,ddl,at=_evidence(table['key_evidence'],('.sql',))
        if not re.search(r'CREATE TABLE(?: IF NOT EXISTS)? (?:public\.)?'+name+r'\s*\(',at,re.I):
            raise ValueError('key evidence does not point to this table creation')
        block=re.search(r'CREATE TABLE(?: IF NOT EXISTS)? (?:public\.)?'+name+r'\s*\((.*?)\n\);',ddl,re.S|re.I)
        pk=re.search(r'PRIMARY KEY\s*\(([^)]+)\)',block[1],re.I) if block else None
        if not pk or [s.strip() for s in pk[1].split(',')]!=key:
            raise ValueError('fingerprint key disagrees with the evidenced plain primary key')
        path,_,at=_evidence(table['write_evidence'],('.py',))
        if (asset_id not in str(path.relative_to(ROOT)) or
            not re.search(r'INSERT\s+INTO\s+'+name+r'\b',at,re.I)):
            raise ValueError('write evidence does not bind this asset to this table')
    if not isinstance(d['not_covered_tables'],list) or not d['not_covered_tables']:
        raise ValueError('partial fingerprint must name the uncovered table(s)')
    uncovered=set()
    for item in d['not_covered_tables']:
        if (not isinstance(item,dict) or set(item)!={'name','reason','evidence'}
            or not isinstance(item['name'],str) or not _IDENT.fullmatch(item['name'])
            or item['name'] in names|uncovered or not isinstance(item['reason'],str) or len(item['reason'])<30):
            raise ValueError('partial fingerprint requires distinct uncovered tables with real reasons')
        _evidence(item['evidence']); uncovered.add(item['name'])
    return d


def fingerprint_asset(conn,asset_id,declaration,chart_id):
    """Read-only measurement using E5.5's ONE definition, with provenance pins.

    The caller owns the connection and READ ONLY transaction. Live column/key
    validation precedes SELECT *. Full/current/certified status is never emitted.
    """
    d=validate(asset_id,declaration)
    if d is None:raise ValueError('fingerprint is undeclared')
    if conn.execute('SHOW transaction_read_only').fetchone()[0]!='on':
        raise ValueError('fingerprint requires a read-only transaction')
    if conn.execute('SHOW transaction_isolation').fetchone()[0] not in ('repeatable read','serializable'):
        raise ValueError('fingerprint requires a stable repeatable-read snapshot')
    import nikasha_stale_certs as nsc
    from fingerprint_declarations import composite_fingerprint
    registry=conn.execute('SELECT to_jsonb(a) FROM public.asset_registry a WHERE asset_id=%s',(asset_id,)).fetchone()
    if registry is None:raise ValueError('fingerprint asset is absent from registry')
    schema={}; measured={}; code={}
    for table in d['tables']:
        name=table['name']; key=table['key']
        # Bind the same relation that E5.5's unqualified, parameterised SELECT resolves.
        relation=conn.execute('''SELECT n.nspname,c.relkind FROM pg_class c
          JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.oid=to_regclass(%s)''',(name,)).fetchone()
        if relation is None or relation[0]!='public' or relation[1] not in ('r','p'):
            raise ValueError('fingerprint needs a public base table')
        columns=conn.execute('''SELECT attname,format_type(atttypid,atttypmod),attnotnull
          FROM pg_attribute WHERE attrelid=to_regclass(%s) AND attnum>0 AND NOT attisdropped ORDER BY attnum''',(name,)).fetchall()
        pk=conn.execute('''SELECT a.attname FROM pg_index i
          CROSS JOIN LATERAL unnest(i.indkey) WITH ORDINALITY k(num,ord)
          JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.num
          WHERE i.indrelid=to_regclass(%s) AND i.indisprimary ORDER BY k.ord''',(name,)).fetchall()
        if [r[0] for r in pk]!=key or any(not r[2] for r in columns if r[0] in key):
            raise ValueError('fingerprint live primary key disagrees with declaration')
        constraints=conn.execute('''SELECT conname,contype,pg_get_constraintdef(oid)
          FROM pg_constraint WHERE conrelid=to_regclass(%s) ORDER BY conname''',(name,)).fetchall()
        schema[name]={'columns':columns,'key':key,'constraints':constraints}
        normalized={'table':name,'scope':'chart','natural_key':key,'volatile_columns':[]}
        # table_fingerprint and row count share one immutable read-only snapshot.
        sha=nsc.table_fingerprint(conn,normalized,chart_id=str(chart_id))
        count=conn.execute(f'SELECT count(*) FROM "{name}" WHERE chart_id=%s',(chart_id,)).fetchone()[0]
        measured[name]={'sha256':sha,'rows':count}
        for ref in (table['key_evidence'],table['write_evidence']):
            path,_,_=_evidence(ref); code[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    import asset_census as ac
    import fingerprint_declarations as fd
    inventory_path=ROOT/'platform/src/generated/nirmana-writer-digests.json'
    inventory_bytes=inventory_path.read_bytes()
    inventory=json.loads(inventory_bytes)
    writer_digest=inventory.get('writers',{}).get(asset_id)
    if not isinstance(writer_digest,str) or not re.fullmatch(r'[a-f0-9]{64}',writer_digest):
        raise ValueError('fingerprint needs the generated writer digest inventory')
    for path in (Path(__file__),Path(nsc.__file__),Path(ac.__file__),Path(fd.__file__)):
        code[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'definition':DEFINITION,'asset_id':asset_id,'chart_id':str(chart_id),'coverage':'partial',
      'tables':measured,'sha256':composite_fingerprint({t:v['sha256'] for t,v in measured.items()}),
      'schema_sha256':_hash(schema),'registry_sha256':_hash(registry[0]),'code_sha256':_hash(code),
      'declaration_sha256':_hash(d),
      'declarations_file_sha256':hashlib.sha256((ROOT/'platform/scripts/governance/asset_declarations.json').read_bytes()).hexdigest(),
      'writer_digest':writer_digest,'inventory_sha256':hashlib.sha256(inventory_bytes).hexdigest(),
      'criterion_sha256':ac.registry_fingerprint(),'registry_revision':ac.REGISTRY_REVISION,
      'production_certification':None}
