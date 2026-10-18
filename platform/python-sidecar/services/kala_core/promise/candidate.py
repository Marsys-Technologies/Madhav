"""Ownership check before a candidate F1 partition can be replaced."""
import hashlib
import json


def building_candidate(cur, chart_id, generation, build_id):
    cur.execute('''SELECT generation, state, build_id, conventions FROM kala_layer_candidate
        WHERE chart_id = %s AND generation = %s FOR UPDATE''', (chart_id, generation))
    rows = cur.fetchall()
    if len(rows) != 1 or rows[0]['state'] != 'building':
        raise ValueError('F1 requires one registered building candidate')
    candidate = rows[0]
    if not build_id or str(candidate['build_id']) != str(build_id):
        raise ValueError('F1 candidate is bound to a different build')
    cur.execute('SELECT generation FROM kala_layer_head WHERE chart_id = %s FOR SHARE', (chart_id,))
    if any(r['generation'] == generation for r in cur.fetchall()):
        raise ValueError('F1 must not replace a published generation')
    return candidate


def natal_pin(candidate):
    """Only the manifest supplies source identity; caller config is not a pin."""
    conventions = candidate.get('conventions') or {}
    pin = conventions.get('natal') or {}
    if not pin.get('build_id') or not pin.get('ayanamsha_id'):
        raise ValueError('F1 requires candidate conventions.natal build_id and ayanamsha_id')
    return pin


def pin_input_vector(cur, chart_id, generation, grain_key, pin, **sources):
    """Attest selected row contents once; refuse drift before replacing output.

    (I) INTERPRETATION: the existing candidate-grain input_vector is the
    candidate input ledger. One source grain per writer also binds different
    class substeps to the same read set. Empty sets are hashed, not certified
    as upstream evaluated-empty. Row order carries no semantic information.
    """
    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str)
    vector = hashlib.sha256(canonical({
        'natal': pin,
        'sources': {name: sorted(canonical(row) for row in rows)
                    for name, rows in sources.items()},
    }).encode()).hexdigest()
    cur.execute('''SELECT input_vector FROM kala_layer_candidate_grain
        WHERE chart_id=%s AND generation=%s AND grain_key=%s''', (chart_id, generation, grain_key))
    prior = cur.fetchone()
    if prior and prior['input_vector'] != vector:
        raise ValueError(f'candidate input vector changed for {grain_key}; new candidate required')
    if not prior:
        cur.execute('''INSERT INTO kala_layer_candidate_grain
            (chart_id,generation,grain_key,result_state,input_vector)
            VALUES (%s,%s,%s,%s,%s)''',
            (chart_id, generation, grain_key, 'rows' if any(sources.values()) else 'zero_rows', vector))
    return vector

