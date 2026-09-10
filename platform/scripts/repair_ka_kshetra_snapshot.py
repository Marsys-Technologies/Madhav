"""
repair_ka_kshetra_snapshot.py — one-shot repair for ka_kshetra snapshot substep failure.

CONTEXT (2026-08-15):
  The A8 full build (run 3c0cfc9d) completed all 302 substeps for 25 event classes
  but the final 'snapshot' substep always fails. Root cause: _compute_content_hash
  fetches 1,839,618 kala_field_provenance rows client-side, which takes >10 min,
  triggering Cloud Run's role-level idle_in_transaction_session_timeout=600s before
  the db.py session-level SET can protect it (the session SET from db.py only runs
  inside a fresh connect(); if the Cloud Run task is still in its initial state when
  the snapshot begins, the GUC may not have taken effect — TBD).

  Locally: no such constraint. We SET idle_in_transaction_session_timeout=0 and
  statement_timeout=0 for this repair session, compute the same hash the writer would
  compute, INSERT the kala_field_snapshots row, and UPDATE asset_throughput to 'lit'.

PRECONDITIONS:
  - cloud-sql-proxy running on 127.0.0.1:5433
  - DB_PASS (amjis-db-password secret) available
  - kala_field/windows/provenance/null/salience/insights/timeline_spec complete
  - kala_field_snapshots = 0 rows for this chart

RUN:
  export DB_PASS=$(gcloud secrets versions access latest --secret=amjis-db-password --project=madhav-astrology)
  cd platform/python-sidecar
  python3 ../scripts/repair_ka_kshetra_snapshot.py [--dry-run]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../python-sidecar')

import math

import psycopg
import psycopg.rows

CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
SNAPSHOT_ID = 'kfs_e23ba1abdf1c6fd3a1cc5c08c7538aeb'
ASSET_ID = 'ka_kshetra'

# ── constants from writer / hazard / integrator (verified against source) ─────
X_SCHEMA_VERSION = 'x12_v0'
WEIGHTS_VERSION = 'v0_classical'
HORIZON_DAYS = 36525.0
DHARA_REPLICATES = 1024   # analytic path: dhara_null.DEFAULT_REPLICATES
Q_QUANTILE = 0.95
DURATION_BUCKETS = [1, 3, 7, 15, 30, 60, 90, 180, 365, 730]
P_FLOOR = 0.05
RHO_MAX = 0.95
TAU_NATS = 0.02
MAX_REFINEMENT_DEPTH = 6

HASHED_TABLES = [
    'kala_field',
    'kala_field_windows',
    'kala_field_provenance',
    'kala_field_null',
    'kala_field_salience',
    'kala_insights',
    'kala_timeline_spec',
]

SKIPPED_CLASSES = [
    {'event_class': 'birth_anchor', 'reason': 'no_class_prior_row',
     'detail': 'no bg_class_priors lifetime-count row for this event class'},
    {'event_class': 'career_change', 'reason': 'no_class_prior_row',
     'detail': 'no bg_class_priors lifetime-count row for this event class'},
]


def _canonical(value):
    """Exact copy of stage4_field._canonical — floats → repr string (§7.4)."""
    if isinstance(value, float):
        if math.isnan(value):
            return 'nan'
        return repr(value)
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value) -> str:
    return json.dumps(_canonical(value), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, default=str)


def field_content_hash(pin_identity: str, rows) -> str:
    """Same as stage4_field.field_content_hash."""
    entries = sorted(
        (table, canonical_json(list(key)), canonical_json(dict(payload)))
        for table, key, payload in rows
    )
    digest = hashlib.sha256()
    digest.update(pin_identity.encode('utf-8'))
    for table, key_json, payload_json in entries:
        digest.update(b'\x1e')
        digest.update(table.encode('utf-8'))
        digest.update(b'\x1f')
        digest.update(key_json.encode('utf-8'))
        digest.update(b'\x1f')
        digest.update(payload_json.encode('utf-8'))
    return 'kfh_' + digest.hexdigest()[:32]


def rows_from_cur(cur) -> list[dict]:
    fetched = cur.fetchall()
    if not fetched:
        return []
    if isinstance(fetched[0], dict):
        return [dict(r) for r in fetched]
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in fetched]


def get_corpus_pin(conn) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(build_id::text) AS b FROM bg_synthetic_cohort")
        rows = rows_from_cur(cur)
    if rows and rows[0]['b']:
        return str(rows[0]['b'])
    return 'corpus_pin_unavailable'


def get_gochara_corpus_pin(conn, chart_id: str) -> dict:
    generation = 'v1'
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE("
                "  (SELECT authoritative_generation FROM kala_gochara_authority"
                "   WHERE chart_id = %s), 'v1') AS gen",
                (chart_id,),
            )
            rows = rows_from_cur(cur)
        if rows and rows[0]['gen']:
            generation = str(rows[0]['gen'])
    except Exception as e:
        print(f'  [warn] gochara_authority query failed: {e}')

    calibration_state = 'no_windows'
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT calibration_state, COUNT(*) AS n"
                " FROM kala_gochara_windows"
                " WHERE chart_id = %s AND generation = %s"
                " GROUP BY calibration_state ORDER BY n DESC LIMIT 1",
                (chart_id, generation),
            )
            rows = rows_from_cur(cur)
        if rows and rows[0]['calibration_state']:
            calibration_state = str(rows[0]['calibration_state'])
    except Exception as e:
        print(f'  [warn] kala_gochara_windows query failed: {e}')

    digest = 'digest_unavailable'
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT md5("
                "  COALESCE(COUNT(*)::text, '0') || '|'"
                "  || COALESCE(MAX(computed_at)::text, '') || '|'"
                "  || COALESCE(MAX(id)::text, '')) AS digest"
                " FROM gochara_resonance_map WHERE chart_id = %s",
                (chart_id,),
            )
            rows = rows_from_cur(cur)
        if rows and rows[0]['digest']:
            digest = str(rows[0]['digest'])
    except Exception as e:
        print(f'  [warn] gochara_resonance_map query failed: {e}')

    return {
        'gochara_generation': generation,
        'gochara_calibration_state': calibration_state,
        'gochara_corpus_digest': digest,
    }


def compute_field_snapshot_id(chart_id: str, corpus_pin: str, config_pin: dict) -> str:
    payload = canonical_json({
        'chart_id': chart_id,
        'corpus_pin': corpus_pin,
        'weights_version': WEIGHTS_VERSION,
        'x_schema_version': X_SCHEMA_VERSION,
        'cohort_version': None,
        'config_pin': config_pin,
    })
    return 'kfs_' + hashlib.sha256(payload.encode('utf-8')).hexdigest()[:32]


def compute_content_hash(conn, chart_id: str, snapshot_id: str) -> str:
    rows = []
    with conn.cursor() as cur:
        print('  Fetching kala_field ...')
        t0 = time.time()
        cur.execute(
            """SELECT event_class, segment_index, t_start, t_end, alpha, gamma,
                      integral_days, refinement_depth, refinement_exhausted
                 FROM kala_field WHERE chart_id = %s AND field_snapshot_id = %s""",
            (chart_id, snapshot_id),
        )
        for r in rows_from_cur(cur):
            key = (r['event_class'], r['segment_index'])
            rows.append(('kala_field', key, {k: v for k, v in r.items()}))
        print(f'    {len([x for x in rows if x[0]=="kala_field"])} rows, {time.time()-t0:.1f}s')

        print('  Fetching kala_field_windows ...')
        t0 = time.time()
        cur.execute(
            """SELECT window_id, event_class, t_start, t_end, t_peak, lambda_peak,
                      expected_count, null_p, confidence_tier, weakest_link,
                      adrishta_residual
                 FROM kala_field_windows
                WHERE chart_id = %s AND field_snapshot_id = %s""",
            (chart_id, snapshot_id),
        )
        for r in rows_from_cur(cur):
            rows.append(('kala_field_windows', (r['window_id'],), dict(r)))
        print(f'    {len([x for x in rows if x[0]=="kala_field_windows"])} rows, {time.time()-t0:.1f}s')

        print('  Fetching kala_field_provenance (1.8M rows — this takes a while) ...')
        t0 = time.time()
        cur.execute(
            """SELECT target_kind, target_id, term_key, term_value, log_contribution,
                      weight_id, weight_value, source_kind, source_table, source_pk,
                      source_fact_id, authority_basis
                 FROM kala_field_provenance
                WHERE chart_id = %s AND field_snapshot_id = %s""",
            (chart_id, snapshot_id),
        )
        for r in rows_from_cur(cur):
            rows.append(('kala_field_provenance',
                         (r['target_kind'], r['target_id'], r['term_key']), dict(r)))
        print(f'    {len([x for x in rows if x[0]=="kala_field_provenance"])} rows, {time.time()-t0:.1f}s')

        print('  Fetching kala_field_null ...')
        t0 = time.time()
        cur.execute(
            """SELECT event_class, bucket_days, q_threshold, replicates
                 FROM kala_field_null
                WHERE chart_id = %s AND field_snapshot_id = %s""",
            (chart_id, snapshot_id),
        )
        for r in rows_from_cur(cur):
            rows.append(('kala_field_null', (r['event_class'], r['bucket_days']), dict(r)))
        print(f'    {len([x for x in rows if x[0]=="kala_field_null"])} rows, {time.time()-t0:.1f}s')

        print('  Fetching kala_field_salience ...')
        t0 = time.time()
        cur.execute(
            """SELECT window_id, event_class, factor_informativeness,
                      factor_consequence, factor_relevance, factor_reliability,
                      factor_actionability, salience, salience_weights_version,
                      salience_basis, selected, selection_rank, marginal_gain,
                      coverage_fraction, largest_omission_window_id,
                      largest_omission_marginal_gain, cohort_version
                 FROM kala_field_salience
                WHERE chart_id = %s AND field_snapshot_id = %s""",
            (chart_id, snapshot_id),
        )
        for r in rows_from_cur(cur):
            rows.append(('kala_field_salience', (r['window_id'],), dict(r)))
        print(f'    {len([x for x in rows if x[0]=="kala_field_salience"])} rows, {time.time()-t0:.1f}s')

        print('  Fetching kala_insights ...')
        t0 = time.time()
        cur.execute(
            """SELECT insight_id, insight_type, event_class, window_id, t_start,
                      t_end, statement_key, statement_params, fact_ids,
                      cohort_surprise, cohort_version, surprise_basis,
                      insight_score
                 FROM kala_insights
                WHERE chart_id = %s AND field_snapshot_id = %s
                  AND lel_derived = FALSE""",
            (chart_id, snapshot_id),
        )
        for r in rows_from_cur(cur):
            rows.append(('kala_insights', (r['insight_id'],), dict(r)))
        print(f'    {len([x for x in rows if x[0]=="kala_insights"])} rows, {time.time()-t0:.1f}s')

        print('  Fetching kala_timeline_spec ...')
        t0 = time.time()
        cur.execute(
            """SELECT generated_for, spec_version, spec, n_tracks, n_intervals,
                      n_points, n_bands, empty_reason
                 FROM kala_timeline_spec
                WHERE chart_id = %s AND field_snapshot_id = %s""",
            (chart_id, snapshot_id),
        )
        for r in rows_from_cur(cur):
            rows.append(('kala_timeline_spec', (r['generated_for'],), dict(r)))
        print(f'    {len([x for x in rows if x[0]=="kala_timeline_spec"])} rows, {time.time()-t0:.1f}s')

    print(f'  Total rows collected: {len(rows)}')
    print('  Computing SHA256 hash ...')
    t0 = time.time()
    h = field_content_hash(snapshot_id, rows)
    print(f'  Hash computed in {time.time()-t0:.1f}s → {h}')
    return h


def get_event_classes(conn, chart_id: str, snapshot_id: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT event_class FROM kala_field_null "
            "WHERE chart_id=%s AND field_snapshot_id=%s ORDER BY event_class",
            (chart_id, snapshot_id),
        )
        return [r['event_class'] for r in rows_from_cur(cur)]


def main():
    parser = argparse.ArgumentParser(description='Repair ka_kshetra snapshot row')
    parser.add_argument('--dry-run', action='store_true', help='Read-only — no DB writes')
    args = parser.parse_args()

    db_pass = os.environ.get('DB_PASS', '')
    if not db_pass:
        print('ERROR: DB_PASS not set. Run: export DB_PASS=$(gcloud secrets versions access latest --secret=amjis-db-password --project=madhav-astrology)')
        sys.exit(1)

    local_url = f'postgresql://amjis_app:{db_pass}@127.0.0.1:5433/amjis'
    print(f'[repair] Connecting to local proxy ...')
    conn = psycopg.connect(local_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False

    with conn.cursor() as cur:
        # Disable all timeouts for this local repair session.
        cur.execute('SET idle_in_transaction_session_timeout = 0')
        cur.execute('SET statement_timeout = 0')
        cur.execute('SET lock_timeout = 0')
        print('[repair] Timeouts disabled for local session.')
    conn.commit()

    # ── 1. Compute pins ────────────────────────────────────────────────────
    print('\n[repair] Computing corpus_pin ...')
    corpus_pin = get_corpus_pin(conn)
    print(f'  corpus_pin = {corpus_pin!r}')

    print('[repair] Computing gochara A1 pin ...')
    gochara_pin = get_gochara_corpus_pin(conn, CHART_ID)
    print(f'  gochara_pin = {gochara_pin}')

    config_pin = {
        'horizon_days': HORIZON_DAYS,
        'p_floor': P_FLOOR,
        'rho_max': RHO_MAX,
        'tau_nats': TAU_NATS,
        'max_refinement_depth': MAX_REFINEMENT_DEPTH,
        'null_replicates': DHARA_REPLICATES,
        'null_quantile': Q_QUANTILE,
        'duration_buckets': DURATION_BUCKETS,
        'precision_regime': 'day_grade',
        **gochara_pin,
    }

    # ── 2. Verify field_snapshot_id ────────────────────────────────────────
    computed_snapshot_id = compute_field_snapshot_id(CHART_ID, corpus_pin, config_pin)
    print(f'\n[repair] Computed snapshot_id: {computed_snapshot_id}')
    print(f'[repair] Expected snapshot_id:  {SNAPSHOT_ID}')
    if computed_snapshot_id != SNAPSHOT_ID:
        print('ERROR: snapshot_id MISMATCH. Config pin or corpus pin is wrong.')
        print('  config_pin:', json.dumps(config_pin, indent=2))
        conn.close()
        sys.exit(2)
    print('[repair] snapshot_id VERIFIED ✓')

    # ── 3. Compute content hash ────────────────────────────────────────────
    print('\n[repair] Computing content hash ...')
    t_start = time.time()
    content_hash = compute_content_hash(conn, CHART_ID, SNAPSHOT_ID)
    print(f'[repair] Content hash: {content_hash} (total {time.time()-t_start:.1f}s)')

    # ── 4. Get event_classes ───────────────────────────────────────────────
    event_classes = get_event_classes(conn, CHART_ID, SNAPSHOT_ID)
    print(f'\n[repair] event_classes ({len(event_classes)}): {event_classes[:3]}...')

    # ── 5. Verify preconditions ────────────────────────────────────────────
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM kala_field_snapshots WHERE chart_id=%s",
            (CHART_ID,)
        )
        n_snap = rows_from_cur(cur)[0]['n']
    print(f'[repair] kala_field_snapshots existing rows: {n_snap}')
    if n_snap > 0:
        print('WARNING: kala_field_snapshots already has rows — will ON CONFLICT DO UPDATE.')

    print(f'\n[repair] dry_run={args.dry_run}')
    if args.dry_run:
        print('[repair] DRY RUN — no DB writes. Exiting.')
        conn.close()
        return

    # ── 6. INSERT kala_field_snapshots ─────────────────────────────────────
    print('[repair] Inserting kala_field_snapshots row ...')
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO kala_field_snapshots (
                   chart_id, field_snapshot_id, field_content_hash, weights_version,
                   x_schema_version, corpus_pin, config_pin, cohort_version,
                   substrate_build_ids, hashed_tables, event_classes, skipped_classes,
                   horizon_days)
               VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s,%s,%s::jsonb,%s)
               ON CONFLICT (chart_id, field_snapshot_id) DO UPDATE SET
                   field_content_hash = EXCLUDED.field_content_hash,
                   skipped_classes = EXCLUDED.skipped_classes,
                   event_classes = EXCLUDED.event_classes,
                   built_at = now()""",
            (CHART_ID, SNAPSHOT_ID, content_hash, WEIGHTS_VERSION,
             X_SCHEMA_VERSION, corpus_pin,
             json.dumps(config_pin), None,
             json.dumps({}), HASHED_TABLES,
             event_classes, json.dumps(SKIPPED_CLASSES), HORIZON_DAYS),
        )
    conn.commit()
    print('[repair] kala_field_snapshots row inserted ✓')

    # ── 7. UPDATE asset_throughput to 'lit' ────────────────────────────────
    print('[repair] Setting asset_throughput.state = "lit" ...')
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE asset_throughput SET state='lit', updated_at=now()
               WHERE chart_id=%s AND asset_id=%s""",
            (CHART_ID, ASSET_ID),
        )
        count = cur.rowcount
    conn.commit()
    print(f'[repair] asset_throughput updated ({count} row) ✓')

    # ── 8. Verify ──────────────────────────────────────────────────────────
    with conn.cursor() as cur:
        cur.execute(
            "SELECT state FROM asset_throughput WHERE chart_id=%s AND asset_id=%s",
            (CHART_ID, ASSET_ID),
        )
        row = rows_from_cur(cur)[0]
    print(f'\n[repair] Final asset_throughput.state = {row["state"]!r}')
    with conn.cursor() as cur:
        cur.execute(
            "SELECT field_content_hash FROM kala_field_snapshots WHERE chart_id=%s",
            (CHART_ID,),
        )
        snap = rows_from_cur(cur)[0]
    print(f'[repair] kala_field_snapshots.field_content_hash = {snap["field_content_hash"]!r}')

    conn.close()
    print('\n[repair] COMPLETE — ka_kshetra is now lit ✓')


if __name__ == '__main__':
    main()
