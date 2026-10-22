"""K9-WRITE-SCOPE F1 (migration 1405): kala_convergence is generation-scoped, so ka_sangam's delete can never cascade into served tables.

The defect. ka_sangam rewrote kala_convergence IN PLACE for the whole chart. The foreign keys onto kala_convergence(convergence_id) cascade:
kala_darshana, kala_obstruction and phala_anchors ON DELETE CASCADE, kala_bhavishya ON DELETE SET NULL. Source of those actions: the production
readback /Users/Dev/kalayantra/run/ops/receipts/k9-fk-cascade-readback-20261022T0710Z.output.txt (all NO ACTION on update, not deferrable) and migrations
245 / 247 / 363 / 249. The fixture below declares exactly those actions on minimal stand-in tables (only the columns the oracles read); everything else is
the real code: ka_sangam's own substeps, rebuild_control.teardown, the real 1330 candidate tables and the real migration 1405.

Claims, one oracle each, each with ONE planted reversion that fails (``BOTH``: the oracle passes on the real code and fails, by its own assertion, on a copy
with that claim's line reverted; root CLAUDE.md §N.8):

  M1  migration: every row that existed is stamped 'legacy' and served; the served view returns the head's generation (else legacy) and never a candidate
  M2  migration: refuses (changing nothing) when a chart holds rows AND a candidate/head, the one case the stamp rule cannot decide
  M3  migration: the widened natural key refuses a repeated window inside one generation and allows the same window in another
  M4  migration: a second application changes nothing
  M5  migration: the view is readable by exactly the roles that read the base table
  M6  migration: ka_sangam's integrity contract (670 conjunct (a), §N.3 accretion) no longer reads the same window in two generations as accretion
  M7  migration: ka_sangam's output-digest spec digests the served view (real canonical_digest / _validate_spec), 980 is retired, one current spec
  W1  a candidate-bound build writes its own generation and leaves served kala_convergence AND every cascaded child byte-identical
  W2  an ordinary rebuild writes and deletes the served generation (head, else legacy) only
  W3  a build bound to a candidate that is no longer a building, unpublished candidate cannot write
  T1  tearing down a candidate removes exactly its rows; served rows and the cascaded children of served rows are byte-identical afterwards
  T2  teardown also removes the candidate's rows (the unlinked-table list names kala_convergence)
  T3  teardown REFUSES, deleting nothing, when a row that is not the candidate's would be cascaded or nulled (a served child pointing at a candidate row)
  R1  no writer reads the base table (a reader of the base table would mix a candidate's rows into served data); the one allowed writer is ka_sangam
  R2  the derivation-completeness guard does not count a candidate-only chart as having served convergence
"""
import json
import os
import re
import uuid
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from pipeline.orchestrator.writers import SubStep
from services.kala_core import rebuild_control, writer_grain
from services.kala_core.writer_grain import bound_candidate, convergence_generation
from tests.l3.kala_db.manifest.test_k9_publication_hardening import BOTH, REAL, REVERTED, mutated  # noqa: F401
from tests.l3.kala_db.manifest.test_publication_ops import db  # noqa: F401  (a fixture)
from tests.l3.kala_db.manifest.test_rebuild_control import CHART, ctl, make_run  # noqa: F401  (ctl is a fixture)

ROOT = Path(__file__).resolve().parents[5]
SIDECAR = ROOT / 'python-sidecar'
OTHER = '00000000-0000-0000-0000-0000000000c7'
SIG = '11111111-1111-1111-1111-111111111111'
GEN = 'candidate:k9conv'
HEAD = 'published:g1'


def migration_path() -> Path:
    # K9_CONVERGENCE_MIGRATION points a job that has not been placed yet at its own copy of the file; CI reads the placed one.
    override = os.environ.get('K9_CONVERGENCE_MIGRATION')
    if override:
        return Path(override)
    found = sorted((ROOT / 'migrations').glob('1405_*.sql'))
    assert len(found) == 1, 'migration 1405 (kala_convergence generation) is allocated to this item and must be placed once'
    return found[0]


def migration() -> str:
    return migration_path().read_text()


# ---------------------------------------------------------------------------------------------------------------------
# the pre-1405 world


PRE_1405 = """
CREATE TABLE kala_convergence (
  convergence_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, window_start date NOT NULL, window_end date NOT NULL,
  convergence_score double precision, constituent_factors jsonb, source_citation text NOT NULL DEFAULT 'fixture',
  computed_at timestamptz NOT NULL DEFAULT now(), signal_id uuid, mode text, peak_date date, orb_strength double precision,
  rarity_years double precision, confidence_score double precision, confidence_label text, independent_current_count smallint,
  is_off_dasha_discovery boolean DEFAULT false, horizon_tier text, domain text, confidence_label_relative text, tier_basis text,
  verification_pass_status text);
CREATE TABLE kala_darshana (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, generation text, narrative text,
  convergence_id bigint REFERENCES kala_convergence (convergence_id) ON DELETE CASCADE);
CREATE TABLE kala_obstruction (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, generation text, narrative text,
  convergence_id bigint REFERENCES kala_convergence (convergence_id) ON DELETE CASCADE);
CREATE TABLE phala_anchors (anchor_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, narrative text,
  convergence_id bigint REFERENCES kala_convergence (convergence_id) ON DELETE CASCADE);
CREATE TABLE kala_bhavishya (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, narrative text,
  convergence_id bigint REFERENCES kala_convergence (convergence_id) ON DELETE SET NULL);
CREATE TABLE build_substep_progress (chart_id uuid NOT NULL, asset_id text NOT NULL, substep_key text NOT NULL, build_fingerprint text,
  rows_written integer, completed_at timestamptz, PRIMARY KEY (chart_id, asset_id, substep_key));
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text, count_sql text);
CREATE TABLE asset_output_digest_specs (asset_id text NOT NULL, spec_sha256 text NOT NULL, spec json NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), retired_at timestamptz, PRIMARY KEY (asset_id, spec_sha256));
CREATE UNIQUE INDEX asset_output_digest_specs_one_current ON asset_output_digest_specs (asset_id) WHERE retired_at IS NULL;
"""
CHILDREN = ('kala_darshana', 'kala_obstruction', 'phala_anchors', 'kala_bhavishya')
COUNT_SQL_SEED = 'SELECT count(*) FROM kala_convergence WHERE chart_id = $1'


def contract_670() -> str:
    text = (ROOT / 'migrations/670_nirmana_l3_w3_integrity_contracts.sql').read_text()
    found = re.search(r"-- ka_sangam\nUPDATE asset_registry SET integrity_check_sql = \$ck\$(.*?)\$ck\$\n WHERE asset_id = 'ka_sangam';", text, re.S)
    assert found, '670 ka_sangam contract not found'
    return found.group(1)


def spec_980():
    text = (ROOT / 'migrations/980_nirmana_l3_ka_sangam_output_digest_spec.sql').read_text()
    found = re.search(r"VALUES \(\s*'ka_sangam',\s*'([0-9a-f]{64})',\s*'(\{.*?\})'::json", text, re.S)
    assert found, '980 spec not found'
    return found.group(1), found.group(2)


@pytest.fixture
def world(ctl):  # noqa: F811
    ctl.execute(PRE_1405)
    sha, spec = spec_980()
    ctl.execute('INSERT INTO asset_registry VALUES (%s, %s, %s)', ('ka_sangam', contract_670(), COUNT_SQL_SEED))
    ctl.execute('INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES (%s, %s, %s::json)', ('ka_sangam', sha, spec))
    ctl.commit()
    return ctl


def apply(conn, sql=None):
    """The migration with its public. qualifiers removed (the test schema is on the search_path); migrate.ts owns the transaction in production."""
    conn.execute((sql if sql is not None else migration()).replace('public.', ''))
    conn.commit()


def conv(conn, *, chart=CHART, generation=None, tier='near', mode='A', peak=date(2027, 3, 1), signal=SIG):
    cols = 'chart_id, window_start, window_end, convergence_score, constituent_factors, signal_id, mode, peak_date, horizon_tier, confidence_score, independent_current_count'
    vals = [chart, peak - timedelta(days=2), peak + timedelta(days=2), 0.4, json.dumps({'dasha_score': 0.9}), signal, mode, peak, tier, 0.0769, 1]
    if generation is not None:
        cols += ', generation'
        vals.append(generation)
    return conn.execute(f'INSERT INTO kala_convergence ({cols}) VALUES ({", ".join(["%s"] * len(vals))}) RETURNING convergence_id', vals).fetchone()[0]


def children_of(conn, convergence_id, *, chart=CHART, generation='SERVED'):
    """One child row in each cascaded table (generation only where the production table has the column)."""
    for table in ('kala_darshana', 'kala_obstruction'):
        conn.execute(f'INSERT INTO {table} (chart_id, generation, narrative, convergence_id) VALUES (%s, %s, %s, %s)',
                     (chart, None if generation == 'SERVED' else generation, f'{table}:{convergence_id}', convergence_id))
    for table in ('phala_anchors', 'kala_bhavishya'):
        conn.execute(f'INSERT INTO {table} (chart_id, narrative, convergence_id) VALUES (%s, %s, %s)', (chart, f'{table}:{convergence_id}', convergence_id))


def dump(conn, generation):
    """Byte-level state of one generation: its convergence rows and every row of the four cascaded tables that hangs from them."""
    owned = '(SELECT convergence_id FROM kala_convergence WHERE generation = %(g)s)'
    parts = ["'%s', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY %s), '[]'::jsonb) FROM %s t WHERE t.convergence_id IN %s)" % (t, k, t, owned)
             for t, k in (('kala_darshana', 'id'), ('kala_obstruction', 'id'), ('phala_anchors', 'anchor_id'), ('kala_bhavishya', 'id'))]
    parts.append("'conv', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY convergence_id), '[]'::jsonb) FROM kala_convergence t WHERE generation = %(g)s)")
    return conn.execute('SELECT jsonb_build_object(%s)::text' % ', '.join(parts), {'g': generation}).fetchone()[0]


def generations(conn):
    return sorted(r[0] for r in conn.execute('SELECT DISTINCT generation FROM kala_convergence').fetchall())


def has_generation_column(conn):
    return conn.execute("SELECT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'kala_convergence'::regclass AND attname = 'generation' AND NOT attisdropped)").fetchone()[0]


def head(conn, generation=HEAD, chart=CHART):
    conn.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s) ON CONFLICT (chart_id) DO UPDATE SET generation = EXCLUDED.generation', (chart, generation))


def variant_sql(old, new):
    sql = migration()
    assert sql.count(old) == 1, f'reversion anchor is not unique: {old!r}'
    return sql.replace(old, new)


# ---------------------------------------------------------------------------------------------------------------------
# M: the migration


def oracle_stamp_and_view(conn, sql=None):
    pre = conv_pre(conn, CHART) + conv_pre(conn, OTHER)
    apply(conn, sql)
    assert generations(conn) == ['legacy'], 'every row that existed before the column is the served legacy partition'
    assert sorted(r[0] for r in conn.execute('SELECT convergence_id FROM kala_convergence_served').fetchall()) == sorted(pre)
    # a published head: the view serves the head's generation for that chart, and a candidate's rows nowhere
    head(conn)
    served_head, served_candidate = conv(conn, generation=HEAD, peak=date(2027, 4, 1)), conv(conn, generation=GEN, peak=date(2027, 5, 1))
    conn.commit()
    got = {r[0] for r in conn.execute('SELECT convergence_id FROM kala_convergence_served WHERE chart_id = %s', (CHART,)).fetchall()}
    assert got == {served_head}, 'a chart with a head serves exactly the head generation'
    assert served_candidate not in {r[0] for r in conn.execute('SELECT convergence_id FROM kala_convergence_served').fetchall()}
    other = {r[0] for r in conn.execute('SELECT convergence_id FROM kala_convergence_served WHERE chart_id = %s', (OTHER,)).fetchall()}
    assert other == set(conv_ids(conn, OTHER, 'legacy')), 'a chart with no head serves legacy'


def conv_pre(conn, chart):
    """A row written before the column exists (no generation in the INSERT)."""
    return [conv(conn, chart=chart)] + [conv(conn, chart=chart, tier='lifetime', peak=date(2030, 1, 1))]


def conv_ids(conn, chart, generation):
    return [r[0] for r in conn.execute('SELECT convergence_id FROM kala_convergence WHERE chart_id = %s AND generation = %s ORDER BY convergence_id',
                                       (chart, generation)).fetchall()]


@BOTH
def test_m1_existing_rows_are_stamped_legacy_and_the_view_serves_head_or_legacy(world, reverted):
    if not reverted:
        return oracle_stamp_and_view(world)
    # reversion: the column default is dropped from the stamp ('legacy' -> a fixed, wrong partition for the existing rows)
    sql = variant_sql("ADD COLUMN generation text NOT NULL DEFAULT 'legacy'", "ADD COLUMN generation text NOT NULL DEFAULT 'candidate:unknown'")
    with pytest.raises(AssertionError, match='served legacy partition'):
        oracle_stamp_and_view(world, sql)


def oracle_refuses_ambiguity(conn, sql=None):
    conv_pre(conn, CHART)
    conn.execute('INSERT INTO kala_layer_candidate (chart_id, generation, build_id, model_digest, rule_registry_version, conventions) '
                 "VALUES (%s, %s, %s, 'd', 'r', '{}'::jsonb)", (CHART, GEN, str(uuid.uuid4())))
    conn.commit()
    try:
        apply(conn, sql)
    except psycopg.errors.RaiseException as exc:
        conn.rollback()
        assert 'refused' in str(exc)
        assert not has_generation_column(conn), 'a refusal changes nothing'
        return
    raise AssertionError('migration 1405 stamped rows it cannot attribute')


@BOTH
def test_m2_refuses_when_a_chart_has_rows_and_a_candidate(world, reverted):
    if not reverted:
        return oracle_refuses_ambiguity(world)
    with pytest.raises(AssertionError, match='cannot attribute'):
        oracle_refuses_ambiguity(world, variant_sql('IF ambiguous > 0 THEN', 'IF false THEN'))


def test_m2b_refuses_duplicate_natural_keys_and_a_head_without_candidate(world):
    conv(world), conv(world)       # the same window twice: the widened key cannot be built over it
    world.commit()
    with pytest.raises(psycopg.errors.RaiseException, match='duplicate'):
        apply(world)
    world.rollback()
    assert not has_generation_column(world)
    world.execute('DELETE FROM kala_convergence')
    conv(world)
    head(world, 'published:old')
    world.commit()
    with pytest.raises(psycopg.errors.RaiseException, match='refused'):
        apply(world)
    world.rollback()
    assert not has_generation_column(world)


def oracle_widened_key(conn, sql=None):
    apply(conn, sql)
    conv(conn, generation='legacy')
    conv(conn, generation=GEN)               # the same window in another generation is legitimate
    conn.commit()
    try:
        conv(conn, generation=GEN)           # ...but not twice in one generation
    except psycopg.errors.UniqueViolation:
        conn.rollback()
        return
    raise AssertionError('the same window was stored twice in one generation')


@BOTH
def test_m3_widened_natural_key(world, reverted):
    if not reverted:
        return oracle_widened_key(world)
    with pytest.raises(AssertionError, match='stored twice in one generation'):
        oracle_widened_key(world, variant_sql('CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_convergence_generation_natural_key',
                                              'CREATE INDEX IF NOT EXISTS uq_kala_convergence_generation_natural_key'))


def structure(conn):
    return conn.execute("""SELECT jsonb_build_object(
        'columns', (SELECT jsonb_agg(to_jsonb(c) ORDER BY ordinal_position) FROM information_schema.columns c
                     WHERE table_schema = current_schema() AND table_name = 'kala_convergence'),
        'indexes', (SELECT jsonb_agg(indexdef ORDER BY indexname) FROM pg_indexes WHERE schemaname = current_schema() AND tablename = 'kala_convergence'),
        'constraints', (SELECT jsonb_agg(pg_get_constraintdef(oid) ORDER BY conname) FROM pg_constraint WHERE conrelid = 'kala_convergence'::regclass),
        'view', pg_get_viewdef('kala_convergence_served'::regclass),
        'registry', (SELECT jsonb_agg(to_jsonb(r) ORDER BY asset_id) FROM asset_registry r),
        'specs', (SELECT jsonb_agg(spec_sha256 || ':' || (retired_at IS NULL)::text ORDER BY spec_sha256) FROM asset_output_digest_specs),
        'comment', col_description('kala_convergence'::regclass, (SELECT attnum FROM pg_attribute WHERE attrelid = 'kala_convergence'::regclass AND attname = 'generation')))::text""").fetchone()[0]


def oracle_idempotent(conn, sql=None):
    conv_pre(conn, CHART)
    conn.commit()
    apply(conn, sql)
    first, rows = structure(conn), dump(conn, 'legacy')
    apply(conn, sql)
    assert structure(conn) == first, 'a second application changed the schema or the registry'
    assert dump(conn, 'legacy') == rows


@BOTH
def test_m4_second_application_changes_nothing(world, reverted):
    if not reverted:
        return oracle_idempotent(world)
    # reversion: the stamp block runs on every application (its column guard is removed), so the second application fails
    sql = variant_sql("IF NOT EXISTS (SELECT 1 FROM pg_attribute\n                  WHERE attrelid = 'public.kala_convergence'::regclass AND attname = 'generation' AND NOT attisdropped) THEN", 'IF true THEN')
    with pytest.raises(psycopg.errors.DuplicateColumn):
        oracle_idempotent(world, sql)


def view_acl_public(conn):
    return conn.execute("SELECT EXISTS (SELECT 1 FROM pg_class c CROSS JOIN LATERAL aclexplode(c.relacl) a "
                        "WHERE c.oid = 'kala_convergence_served'::regclass AND a.grantee = 0 AND a.privilege_type = 'SELECT')").fetchone()[0]


def oracle_grants(conn, sql=None):
    conn.execute('GRANT SELECT ON kala_convergence TO PUBLIC')
    conn.commit()
    apply(conn, sql)
    assert view_acl_public(conn), 'the view must be readable by the roles that read the base table'


@BOTH
def test_m5_view_grants_follow_the_base_table(world, reverted):
    if not reverted:
        return oracle_grants(world)
    with pytest.raises(AssertionError, match='readable by the roles'):
        oracle_grants(world, variant_sql("EXECUTE format('GRANT SELECT ON public.kala_convergence_served TO %s', grantee_name);", 'NULL;'))


def test_m5b_a_view_is_not_granted_to_a_role_the_table_withholds(world):
    apply(world)
    assert not view_acl_public(world), 'no PUBLIC grant on the base table means none on the view'


def integrity(conn):
    return conn.execute('SELECT integrity_check_sql FROM asset_registry WHERE asset_id = %s', ('ka_sangam',)).fetchone()[0]


def passes(conn, check):
    return bool(conn.execute(check).fetchone()[0])


def oracle_accretion(conn, sql=None):
    apply(conn, sql)
    conv(conn, generation='legacy')
    conv(conn, generation=GEN)            # the SAME window, built again as a candidate: not accretion
    conn.commit()
    assert passes(conn, integrity(conn)), 'the same window in two generations was read as rebuild accretion'
    conv(conn, generation=GEN, tier='near', mode='B', signal=SIG)  # a different window: still fine
    conn.execute('DROP INDEX uq_kala_convergence_generation_natural_key')   # accretion INSIDE one generation must still read false
    conv(conn, generation=GEN)
    conn.commit()
    assert not passes(conn, integrity(conn)), 'the §N.3 detector must still catch a window stored twice in one generation'


@BOTH
def test_m6_integrity_contract_groups_accretion_by_generation(world, reverted):
    if not reverted:
        return oracle_accretion(world)
    old = 'GROUP BY chart_id, horizon_tier, mode, peak_date, signal_id'
    with pytest.raises(AssertionError, match='rebuild accretion'):
        oracle_accretion(world, variant_sql("new_group constant text := 'GROUP BY chart_id, generation, horizon_tier, mode, peak_date, signal_id';",
                                            f"new_group constant text := '{old}';"))


def test_m6b_the_unspliced_670_contract_is_red_on_that_data(world):
    """Control for M6: the same data against the unchanged 670 text (its GROUP BY has no generation) is red, so the splice is what turns it green."""
    apply(world)
    conv(world, generation='legacy')
    conv(world, generation=GEN)
    world.commit()
    assert not passes(world, contract_670()), 'without the splice the first candidate build would fail ka_sangam integrity'


def oracle_digest(conn, sql=None):
    from pipeline.orchestrator.output_digest import _validate_spec
    from pipeline.orchestrator.provenance import canonical_digest
    apply(conn, sql)
    old_sha, _ = spec_980()
    rows = conn.execute('SELECT spec_sha256, spec::text, retired_at IS NULL FROM asset_output_digest_specs WHERE asset_id = %s', ('ka_sangam',)).fetchall()
    current = [r for r in rows if r[2]]
    assert len(current) == 1, 'the registry allows ONE current spec per asset'
    sha, text = current[0][0], json.loads(current[0][1])
    assert sha != old_sha and old_sha in {r[0] for r in rows if not r[2]}, 'spec 980 is retired, not edited or deleted'
    assert canonical_digest(text) == sha, 'spec_sha256 must be the canonical digest of the stored spec'
    assert _validate_spec('ka_sangam', text, sha).asset_id == 'ka_sangam'
    assert [c['relation'] for c in text['components']] == ['kala_convergence_served']


@BOTH
def test_m7_digest_spec_digests_the_served_view(world, reverted):
    if not reverted:
        return oracle_digest(world)
    with pytest.raises(AssertionError, match='canonical digest'):
        oracle_digest(world, variant_sql('"relation":"kala_convergence_served"', '"relation":"kala_convergence"'))


def test_m7b_count_sql_is_left_as_the_census_reads_it(world):
    """count_sql stays the plain single-table count: the asset census refuses a nested subselect (asset_census._count_scope_tail), so a served-generation
    count would blind it to ka_sangam's own rows; the cockpit Clear route also derives its DELETE from this text."""
    apply(world)
    assert world.execute("SELECT count_sql FROM asset_registry WHERE asset_id = 'ka_sangam'").fetchone()[0] == COUNT_SQL_SEED


# ---------------------------------------------------------------------------------------------------------------------
# W: the writer


def window(peak, mode='A'):
    return dict(window_start=peak - timedelta(days=2), window_end=peak + timedelta(days=2), peak_date=peak, convergence_score=0.4,
                constituent_factors={'dasha_score': 0.9}, source_citation='fixture:k9-convergence-scope', signal_id=SIG, mode=mode,
                orb_strength=0.8, rarity_years=3.0, is_off_dasha_discovery=False, primary_domain='career')


NEAR = [window(date(2027, 7, 1)), window(date(2027, 8, 1), 'B')]
LIFETIME = [window(date(2001, 7, 1))]


def build(conn, writer_cls, run_id, *, bind=True, lifetime=True, reset=True):
    """ka_sangam's own substeps (`near`, `lifetime:0`) over fixed windows: the sky engine is not under test, the DELETE and INSERT statements are."""
    w = writer_cls()
    w._chart_id = CHART
    w._candidate = bound_candidate(conn, run_id, CHART) if bind else None
    w._pred_dicts = [{'signal_id': SIG}]
    w._lt_preds = [{'signal_id': SIG}] if lifetime else []
    w._birth_year = 1984
    w._enrichment_ctx = None
    w._dks = w._gs = w._muhurta = None
    w._native_ctx = SimpleNamespace()
    w._reset_pending = reset
    w._record_substep = lambda *a, **k: None
    w._generate_windows = lambda **kw: list(NEAR if kw['pred_dicts'] is w._pred_dicts else LIFETIME)
    ctx = SimpleNamespace(db_conn=conn, build_id=run_id, dry_run=False, config={'chart_id': CHART, 'birth_params': {
        'datetime_iso': '1984-02-05T10:43:00+05:30', 'latitude_deg': 20.2961, 'longitude_deg': 85.8245, 'tz_offset_hours': 5.5}})
    for key in (['near', 'lifetime:0'] if lifetime else ['near']):
        w.run_substep(ctx, SubStep(key=key))
    return w


def real_writer():
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter
    return KaSangamWriter


def load_variant(tmp_path, old, new):
    """A copy of ka_sangam.py with ONE line reverted (the planted reversion). The writer registry is process-wide, so the copy is not registered."""
    import importlib.util
    source = (SIDECAR / 'pipeline/orchestrator/writers/ka_sangam.py').read_text()
    assert source.count(old) == 1, f'reversion anchor is not unique: {old!r}'
    path = tmp_path / 'variant_ka_sangam.py'
    path.write_text(re.sub(r"^@register\('ka_sangam'\)\n", '', source.replace(old, new), flags=re.M))
    spec = importlib.util.spec_from_file_location('variant_ka_sangam_' + uuid.uuid4().hex, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.KaSangamWriter


def served_world(conn, generation='legacy'):
    """Two served windows, each with one child in every cascaded table."""
    ids = [conv(conn, generation=generation), conv(conn, generation=generation, tier='lifetime', peak=date(2002, 1, 1))]
    for convergence_id in ids:
        children_of(conn, convergence_id)
    conn.commit()
    return ids


def oracle_candidate_build(conn, writer_cls):
    served_ids = served_world(conn)
    run = make_run(conn, 'completed', generation=GEN)
    before = dump(conn, 'legacy')
    build(conn, writer_cls, run.build_id)
    conn.commit()
    assert dump(conn, 'legacy') == before, 'a candidate build changed a served convergence row or a cascaded child of one'
    assert conv_ids(conn, CHART, 'legacy') == served_ids
    assert len(conv_ids(conn, CHART, GEN)) == len(NEAR) + len(LIFETIME), 'the candidate build writes its own generation'
    assert generations(conn) == sorted(['legacy', GEN])
    # a second candidate build of the same run replaces its own rows only
    build(conn, writer_cls, run.build_id)
    conn.commit()
    assert dump(conn, 'legacy') == before
    assert len(conv_ids(conn, CHART, GEN)) == len(NEAR) + len(LIFETIME), 'a rebuild REPLACES the candidate rows, never accretes them'


@BOTH
def test_w1_candidate_build_leaves_served_rows_and_their_children_byte_identical(world, tmp_path, reverted):
    apply(world)
    if not reverted:
        return oracle_candidate_build(world, real_writer())
    # reversion: the first executing substep deletes the whole chart again (the audit's F1 line)
    cls = load_variant(tmp_path, 'cur.execute("DELETE FROM kala_convergence WHERE chart_id = %s AND generation = %s",\n                            (chart_id, self._write_generation()))',
                       'cur.execute("DELETE FROM kala_convergence WHERE chart_id = %s", (chart_id,))')
    with pytest.raises(AssertionError, match='changed a served convergence row'):
        oracle_candidate_build(world, cls)


def test_w1b_every_delete_statement_is_scoped_when_the_near_tier_also_clears_lifetime_rows(world):
    """The near substep's bulk delete of lifetime rows (no lifetime substeps planned) and the per-signal delete are scoped the same way."""
    apply(world)
    served_world(world)
    run = make_run(world, 'completed', generation=GEN)
    before = dump(world, 'legacy')
    build(world, real_writer(), run.build_id, lifetime=False)
    build(world, real_writer(), run.build_id, lifetime=True, reset=False)
    world.commit()
    assert dump(world, 'legacy') == before


def oracle_ordinary_rebuild(conn, writer_cls):
    legacy_ids = served_world(conn)
    head(conn)
    head_ids = served_world(conn, HEAD)
    legacy_before = dump(conn, 'legacy')
    build(conn, writer_cls, None, bind=False)
    conn.commit()
    assert conv_ids(conn, CHART, 'legacy') == legacy_ids and dump(conn, 'legacy') == legacy_before, 'an ordinary rebuild with a head leaves the retained legacy partition alone'
    new = conv_ids(conn, CHART, HEAD)
    assert len(new) == len(NEAR) + len(LIFETIME) and not set(new) & set(head_ids), 'it replaces the served (head) generation'
    # the cascade from the replaced head rows reached THEIR children only
    assert conn.execute('SELECT count(*) FROM kala_darshana WHERE convergence_id = ANY(%s)', (head_ids,)).fetchone()[0] == 0


@BOTH
def test_w2_ordinary_rebuild_writes_and_deletes_the_served_generation_only(world, tmp_path, reverted):
    apply(world)
    if not reverted:
        return oracle_ordinary_rebuild(world, real_writer())
    cls = load_variant(tmp_path, "self._conv_generation = convergence_generation(conn, chart_id, getattr(self, '_candidate', None))",
                       "self._conv_generation = 'legacy'")
    with pytest.raises(AssertionError, match='retained legacy partition alone'):
        oracle_ordinary_rebuild(world, cls)


def test_w2b_an_ordinary_rebuild_with_no_head_writes_legacy(world):
    apply(world)
    build(world, real_writer(), None, bind=False)
    world.commit()
    assert generations(world) == ['legacy']


def oracle_unbuildable_candidate(conn, resolver):
    run = make_run(conn, 'completed', generation=GEN)
    candidate = bound_candidate(conn, run.build_id, CHART)
    assert resolver(conn, CHART, candidate) == GEN, 'a building candidate of this build resolves to its own generation'
    conn.execute("UPDATE kala_layer_candidate SET state = 'published' WHERE chart_id = %s AND generation = %s", (CHART, GEN))
    head(conn, GEN)
    conn.commit()
    try:
        resolver(conn, CHART, candidate)
    except ValueError:
        conn.rollback()
        return
    raise AssertionError('a published candidate was offered for writing')


@BOTH
def test_w3_a_published_candidate_cannot_be_written(world, tmp_path, reverted):
    apply(world)
    if not reverted:
        return oracle_unbuildable_candidate(world, convergence_generation)
    variant = mutated(writer_grain, tmp_path,
                      "return building_candidate(cur, candidate.chart_id, candidate.generation, candidate.build_id)['generation']",
                      'return candidate.generation')
    with pytest.raises(AssertionError, match='published candidate was offered'):
        oracle_unbuildable_candidate(world, variant.convergence_generation)


# ---------------------------------------------------------------------------------------------------------------------
# T: teardown


def candidate_with_children(conn, writer_cls=None):
    served_world(conn)
    run = make_run(conn, 'completed', generation=GEN)
    build(conn, writer_cls or real_writer(), run.build_id)
    own = conv_ids(conn, CHART, GEN)
    served_before = dump(conn, 'legacy')     # the served state, taken before the candidate's own children exist
    for table in ('kala_darshana', 'kala_obstruction'):      # the candidate's OWN children: only these two tables carry the generation
        conn.execute(f'INSERT INTO {table} (chart_id, generation, narrative, convergence_id) VALUES (%s, %s, %s, %s)', (CHART, GEN, 'candidate child', own[0]))
    conn.commit()
    return run, own, served_before


def oracle_teardown(conn, module):
    run, own, before = candidate_with_children(conn)
    done = module.teardown(conn, run_id=run.build_id, chart_id=CHART)
    conn.commit()
    assert done['status'] == 'TORN_DOWN'
    assert done['deleted'].get('kala_convergence') == len(own), "teardown must delete exactly the candidate's convergence rows"
    assert dump(conn, 'legacy') == before, 'teardown changed a served convergence row or a cascaded child of one'
    assert conv_ids(conn, CHART, GEN) == [], 'teardown removes exactly the candidate rows'
    assert conn.execute("SELECT count(*) FROM kala_darshana WHERE generation = %s", (GEN,)).fetchone()[0] == 0, 'the candidate\'s own cascaded children go with it'


def test_t1_teardown_removes_the_candidate_and_leaves_served_rows_and_children_identical(world, tmp_path):
    apply(world)
    oracle_teardown(world, rebuild_control)


def test_t1_planted_reversion_unscoped_delete_destroys_served_rows(world, tmp_path):
    apply(world)
    module = mutated(rebuild_control, tmp_path,
                     "sql.SQL('DELETE FROM {} WHERE chart_id = %s AND generation = %s').format(sql.Identifier(table)),\n                                      (chart_id, generation)).rowcount",
                     "sql.SQL('DELETE FROM {} WHERE chart_id = %s').format(sql.Identifier(table)),\n                                      (chart_id,)).rowcount")
    with pytest.raises(AssertionError, match='exactly the candidate'):
        oracle_teardown(world, module)


def test_t2_planted_reversion_teardown_forgets_kala_convergence(world, tmp_path):
    apply(world)
    module = mutated(rebuild_control, tmp_path, "'kala_f1_target_object', 'kala_convergence')", "'kala_f1_target_object')")
    with pytest.raises(AssertionError, match='exactly the candidate'):
        oracle_teardown(world, module)


def oracle_cascade_refusal(conn, module, child):
    run, own, _ = candidate_with_children(conn)
    if child == 'kala_darshana':      # a SERVED row (generation NULL) hanging from a candidate row
        conn.execute("INSERT INTO kala_darshana (chart_id, generation, narrative, convergence_id) VALUES (%s, NULL, 'served', %s)", (CHART, own[0]))
    else:                              # a row of a table that cannot say whose it is
        conn.execute(f"INSERT INTO {child} (chart_id, narrative, convergence_id) VALUES (%s, 'unattributable', %s)", (CHART, own[0]))
    conn.commit()
    before = (dump(conn, 'legacy'), dump(conn, GEN))
    try:
        module.teardown(conn, run_id=run.build_id, chart_id=CHART)
    except ValueError as exc:
        conn.rollback()
        assert child in str(exc), 'the refusal names the table it would have damaged'
        assert (dump(conn, 'legacy'), dump(conn, GEN)) == before, 'a refusal deletes nothing'
        return
    raise AssertionError(f'teardown cascaded into {child} rows that are not the candidate\'s')


@pytest.mark.parametrize('child', ['kala_darshana', 'phala_anchors', 'kala_bhavishya'])
def test_t3_teardown_refuses_when_a_cascade_would_reach_rows_that_are_not_the_candidates(world, child):
    apply(world)
    oracle_cascade_refusal(world, rebuild_control, child)


def test_t3_planted_reversion_no_cascade_check(world, tmp_path):
    apply(world)
    module = mutated(rebuild_control, tmp_path, 'if reached:', 'if False:')
    with pytest.raises(AssertionError, match='cascaded into'):
        oracle_cascade_refusal(world, module, 'kala_darshana')


# ---------------------------------------------------------------------------------------------------------------------
# R: readers


READERS = [
    'pipeline/orchestrator/writers/ka_kala_darshana.py', 'pipeline/orchestrator/writers/ka_bhavishya_lekha.py',
    'pipeline/orchestrator/writers/ka_jivana_parva.py', 'pipeline/orchestrator/writers/ka_kalasutra.py',
    'pipeline/orchestrator/writers/ka_vighnakara.py', 'pipeline/orchestrator/writers/ph_nimitta.py',
    'pipeline/orchestrator/writers/ph_pratikara.py', 'pipeline/orchestrator/writers/ph_muhurta.py',
    'pipeline/orchestrator/writers/mi_adhilepa.py', 'services/ka_sangam/jury/reader.py',
]


def base_table_reads(source: str) -> list[str]:
    """SQL reads of the base table (FROM / JOIN kala_convergence, not the served view or a longer name)."""
    return re.findall(r'\b(?:FROM|JOIN)\s+kala_convergence\b(?!_)', source)


def every_reader_reads_the_served_view(sources):
    for name, source in sources.items():
        assert source.count('kala_convergence_served') >= 1, f'{name} does not read the served view'
        assert base_table_reads(source) == [], f'{name} reads the base table, which also holds a K9 candidate\'s rows'


def test_r1_no_reader_reads_the_base_table():
    every_reader_reads_the_served_view({name: (SIDECAR / name).read_text() for name in READERS})
    # and nothing else under the writers or services does either, ka_sangam (the writer) excepted
    owners = {'pipeline/orchestrator/writers/ka_sangam.py',           # the writer of the partitions
              'services/kala_core/rebuild_control.py',                 # teardown: reads the candidate's rows to prove what a cascade would reach
              'services/kala_core/idempotency/__init__.py'}            # the generation-scoped delete map (never called by the plan)
    offenders = [str(p.relative_to(SIDECAR)) for base in ('pipeline/orchestrator/writers', 'services') for p in (SIDECAR / base).rglob('*.py')
                 if str(p.relative_to(SIDECAR)) not in owners and base_table_reads(p.read_text())]
    assert offenders == []


def test_r1_planted_reversion_a_reader_returns_to_the_base_table():
    sources = {name: (SIDECAR / name).read_text() for name in READERS}
    key = 'pipeline/orchestrator/writers/ka_kalasutra.py'
    sources[key] = sources[key].replace('FROM kala_convergence_served', 'FROM kala_convergence')
    with pytest.raises(AssertionError, match='does not read the served view|reads the base table'):
        every_reader_reads_the_served_view(sources)


def test_r2_completeness_guard_ignores_candidate_only_convergence(world):
    from pipeline.orchestrator.kala_derivation_completeness_guard import _charts_with_rows
    apply(world)
    conv(world, generation=GEN)                      # a candidate's rows only: the chart has no SERVED convergence
    conv(world, chart=OTHER, generation='legacy')
    world.commit()
    world.row_factory = psycopg.rows.dict_row
    assert _charts_with_rows(world, 'kala_convergence') == {OTHER}
