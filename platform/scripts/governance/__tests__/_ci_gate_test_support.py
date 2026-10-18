"""Evaluate real CI expressions in governance tests; reject unsupported syntax."""
import json
import re

def evaluate(condition, *, event, selected=(), profiles=(), full=False, census=False, ref='refs/heads/main', docs='false', results=None, combination='true'):
    """Evaluate the actual job expression; unsupported syntax fails the oracle."""
    if condition is None:
        return True  # all dependencies succeed in event-selection tests
    expr = str(condition).removeprefix('${{').removesuffix('}}').strip()
    values = {
        'github.event_name': event, 'github.ref': ref, 'inputs.full_gate': full, 'inputs.census_battery': census,
        'needs.changes.outputs.docs_only': docs,
        'needs.changes.outputs.run_combination_suites': combination,
        'needs.changes.outputs.db_jobs': json.dumps(list(selected)),
        'needs.changes.outputs.db_profiles': json.dumps(list(profiles)),
    }
    for key, val in sorted(values.items(), key=lambda p: -len(p[0])):
        expr = expr.replace(key, repr(val))
    expr = re.sub(r'needs\.([\w-]+)\.result', lambda m: repr((results or {}).get(m[1], 'success')), expr)
    expr = expr.replace('!cancelled()', 'True').replace('always()', 'True').replace('success()', 'True')
    expr = expr.replace('&&', ' and ').replace('||', ' or ')
    return bool(eval(expr, {'__builtins__': {}}, {'contains': lambda seq, val: val in seq, 'fromJSON': json.loads, 'true': True, 'false': False}))


def runs_in_full_gate(job):
    # OWNER-CI-SCOPED-QUEUE-20261017: the merge queue is NOT a full event any more (it is scoped like a PR).
    return all(evaluate(job.get("if"), event=event, full=full, docs="true")
               for event, full in (("push", False), ("workflow_dispatch", True)))
