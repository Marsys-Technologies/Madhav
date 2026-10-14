"""Ownership check before a candidate F1 partition can be replaced."""


def building_candidate(cur, chart_id, generation, build_id):
    cur.execute('''SELECT generation, state, build_id FROM kala_layer_candidate
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

