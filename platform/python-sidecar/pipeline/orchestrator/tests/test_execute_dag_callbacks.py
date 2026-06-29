from ..runner import execute_dag

def test_on_complete_called_for_each_successful_asset():
    calls = []
    def run_fn(a): return 'lit'
    def on_complete(a): calls.append(a)

    plan = ['a', 'b', 'c']
    deps = {'a': [], 'b': ['a'], 'c': ['b']}
    failed, _ = execute_dag(
        plan=plan, deps_of=deps, run_fn=run_fn,
        worker_limit=2, on_complete=on_complete,
    )
    assert failed == set()
    assert set(calls) == {'a', 'b', 'c'}

def test_on_complete_not_called_for_failed_asset():
    calls = []
    def run_fn(a): return 'error' if a == 'b' else 'lit'

    execute_dag(
        plan=['a', 'b', 'c'], deps_of={'a': [], 'b': ['a'], 'c': ['b']},
        run_fn=run_fn, worker_limit=2,
        on_complete=lambda a: calls.append(a),
    )
    assert 'a' in calls       # succeeded before b
    assert 'b' not in calls   # failed
    assert 'c' not in calls   # blocked by b

def test_on_complete_exception_does_not_crash_scheduler():
    """A buggy on_complete must not kill the build."""
    def run_fn(a): return 'lit'
    def bad_on_complete(a): raise RuntimeError("oops")

    failed, terminal = execute_dag(
        plan=['a', 'b'], deps_of={'a': [], 'b': ['a']},
        run_fn=run_fn, worker_limit=2,
        on_complete=bad_on_complete,
    )
    # Both assets complete despite the callback error
    assert failed == set()
    assert terminal is None
