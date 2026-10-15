"""G1 snapshot → existing candidate manifest; never publish or self-verify.

The input vector includes complete snapshot pins, the candidate's model/rules/
conventions and every other attested grain. The independently dispatched verifier
still owns acceptance. Baseline freezing happens only AFTER merge in the cockpit.
"""
import hashlib
import json
from pathlib import Path
import re


def snapshot_vector(snapshot_id, content_digest, dependencies):
    if not snapshot_id or not content_digest or not dependencies:
        raise ValueError('complete snapshot identity and dependencies required')
    material = json.loads(json.dumps(dict(snapshot_id=snapshot_id,
        content_digest=content_digest, dependencies=dependencies), allow_nan=False))
    digest = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return material | {'digest': digest, 'schema': 'ky.g1_snapshot/1'}


def attest_snapshot(conn, *, chart_id, generation, build_id, snapshot_id, content_digest, pins):
    from services.kala_core.manifest import Candidate, attest_grain, _lock_building_candidate
    raw = getattr(conn, 'raw', conn)
    candidate = Candidate(str(chart_id), generation, str(build_id), None)
    _lock_building_candidate(raw, candidate)
    # Explicit cursor row factory avoids inheriting a connection's dict factory.
    from psycopg.rows import tuple_row
    with raw.cursor(row_factory=tuple_row) as cur:
        cur.execute('SELECT model_digest, rule_registry_version, conventions FROM kala_layer_candidate '
                    'WHERE chart_id=%s AND generation=%s AND build_id=%s',
                    (str(chart_id),generation,str(build_id)))
        model, rules, conventions = cur.fetchone()
        cur.execute('SELECT grain_key, result_state, input_vector FROM kala_layer_candidate_grain '
                    "WHERE chart_id=%s AND generation=%s AND grain_key <> 'ka_kshetra:snapshot' ORDER BY grain_key",
                    (str(chart_id),generation))
        grains = cur.fetchall()
    if any(state == 'failed' for _,state,_ in grains):
        raise ValueError('cannot attest snapshot over failed upstream grain')
    vector = snapshot_vector(snapshot_id, content_digest, dict(model_digest=model,
        rule_registry_version=rules, conventions=conventions, upstream_grains=grains, pins=pins))
    attest_grain(raw,candidate,grain_key='ka_kshetra:snapshot',result_state='rows',
                 input_vector=json.dumps(vector,sort_keys=True,separators=(',', ':')))
    return vector


def freeze_baseline(path, *, merged_head, code_digest):
    """Write-once receipt; caller must supply the real accepted MERGED head.

    This library never guesses a future merge SHA from the pre-build branch.
    (I) INTERPRETATION: capture after merge is an activation gate, not a claim
    that a branch's uncommitted source is already the frozen G1 baseline.
    """
    if not re.fullmatch('[0-9a-f]{40}', merged_head) or not re.fullmatch('[0-9a-f]{64}', code_digest):
        raise ValueError('exact merged-head SHA and SHA256 code digest required')
    value = dict(schema='ky.g1_baseline/1', merged_head=merged_head, code_digest=code_digest)
    target = Path(path)
    try:
        with target.open('x') as handle:
            handle.write(json.dumps(value,sort_keys=True) + '\n')
    except FileExistsError:
        if json.loads(target.read_text()) != value:
            raise ValueError('G1 baseline is frozen')
    return value

