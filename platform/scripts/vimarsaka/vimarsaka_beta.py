"""
Vimarsaka-β: 6 programmatic acceptance checks for Phase β.
Returns: APPROVE (exit 0) | REJECT_WITH_FEEDBACK (exit 1)

Run: PROD_DB_URL=... python platform/scripts/vimarsaka/vimarsaka_beta.py
"""
from __future__ import annotations
import os
import sys
import uuid

# Add python-sidecar to path
SIDECAR = os.path.join(os.path.dirname(__file__), '..', '..', 'python-sidecar')
sys.path.insert(0, os.path.abspath(SIDECAR))


def check_writer_registration(conn) -> tuple[bool, str]:
    """Both bg_reference and bg_ontology writers must be registered."""
    from pipeline.orchestrator.writers import discover_all, get_writer
    discover_all()
    ref = get_writer('bg_reference')
    ont = get_writer('bg_ontology')
    ok = bool(ref) and bool(ont)
    return ok, f'bg_reference={bool(ref)} bg_ontology={bool(ont)}'


def check_row_counts(conn) -> tuple[bool, str]:
    """bg_reference >= 88 rows total across 5 tables; bg_ontology >= 100 rows."""
    cur = conn.cursor()
    cur.execute("""
        SELECT
          (SELECT count(*) FROM reference_planets) +
          (SELECT count(*) FROM reference_nakshatras) +
          (SELECT count(*) FROM reference_signs) +
          (SELECT count(*) FROM reference_aspects) +
          (SELECT count(*) FROM reference_vargas) AS ref_total
    """)
    ref = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM brahma_ontology")
    ont = cur.fetchone()[0]
    ok = ref >= 88 and ont >= 100
    return ok, f'reference={ref}/88 ontology={ont}/100'


def check_source_citation_not_null(conn) -> tuple[bool, str]:
    """Every row in all reference + ontology tables has non-NULL source_citation."""
    cur = conn.cursor()
    failed = []
    for tbl in ['reference_planets', 'reference_nakshatras', 'reference_signs',
                'reference_aspects', 'reference_vargas', 'brahma_ontology']:
        cur.execute(f"SELECT count(*) FROM {tbl} WHERE source_citation IS NULL")
        n = cur.fetchone()[0]
        if n > 0:
            failed.append(f'{tbl}={n}')
    return len(failed) == 0, f'null source_citation rows: {failed or "none"}'


def check_idempotent_rerun(conn) -> tuple[bool, str]:
    """Re-running bg_ontology writer leaves brahma_ontology count unchanged."""
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM brahma_ontology")
    before = cur.fetchone()[0]

    from pipeline.orchestrator.writers import discover_all, get_writer, ContextSpec
    discover_all()
    ctx = ContextSpec(asset_id='bg_ontology', build_id=str(uuid.uuid4()), db_conn=conn)
    result = get_writer('bg_ontology')().run(ctx)
    conn.commit()

    cur.execute("SELECT count(*) FROM brahma_ontology")
    after = cur.fetchone()[0]
    ok = before == after and result.rows_inserted == 0
    return ok, f'before={before} after={after} rows_inserted={result.rows_inserted}'


def check_asset_throughput_updated(conn) -> tuple[bool, str]:
    """asset_throughput shows last_built_at populated for both assets after build."""
    cur = conn.cursor()
    cur.execute("""
        SELECT count(*) FROM asset_throughput
        WHERE asset_id IN ('bg_reference', 'bg_ontology')
        AND last_built_at IS NOT NULL
        AND chart_id IS NULL
    """)
    n = cur.fetchone()[0]
    ok = n >= 2
    return ok, f'last_built_at populated for {n}/2 assets'


def check_cockpit_displays_lit(conn) -> tuple[bool, str]:
    """asset_throughput state = 'lit' for both assets."""
    cur = conn.cursor()
    cur.execute("""
        SELECT asset_id, state FROM asset_throughput
        WHERE asset_id IN ('bg_reference', 'bg_ontology')
        AND chart_id IS NULL
    """)
    rows = cur.fetchall()
    states = {r[0]: r[1] for r in rows}
    ok = all(states.get(a) == 'lit' for a in ['bg_reference', 'bg_ontology'])
    return ok, f'states={states}'


CHECKS = [
    ('writer_registration', check_writer_registration),
    ('row_counts', check_row_counts),
    ('source_citation_not_null', check_source_citation_not_null),
    ('idempotent_rerun', check_idempotent_rerun),
    ('asset_throughput_updated', check_asset_throughput_updated),
    ('cockpit_displays_lit', check_cockpit_displays_lit),
]


def main():
    import psycopg
    db_url = os.environ.get('PROD_DB_URL') or os.environ.get('DATABASE_URL')
    if not db_url:
        print('ERROR: PROD_DB_URL not set')
        sys.exit(2)

    conn = psycopg.connect(db_url)
    passed = []
    failed = []
    for name, fn in CHECKS:
        try:
            ok, msg = fn(conn)
        except Exception as e:
            ok, msg = False, f'EXCEPTION: {e}'
        status = '✓ PASS' if ok else '✗ FAIL'
        print(f'{status}  {name}: {msg}')
        (passed if ok else failed).append(name)

    print(f'\nResult: {len(passed)}/{len(CHECKS)} PASS')
    if failed:
        print(f'FAIL: {failed}')
        sys.exit(1)
    print('SEAL: Phase β APPROVED')


if __name__ == '__main__':
    main()
