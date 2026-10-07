#!/usr/bin/env python3
"""B-3b executor safety cases, isolated from the live executor and production."""
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import fcntl

SOURCE = pathlib.Path(__file__).resolve().parents[1] / 'executor.py'
BASE = pathlib.Path(tempfile.gettempdir())


def load(root):
    old = os.environ.get('KY_ROOT')
    os.environ['KY_ROOT'] = str(root)
    try:
        spec = importlib.util.spec_from_file_location('ky_executor_b3b', SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if old is None:
            os.environ.pop('KY_ROOT', None)
        else:
            os.environ['KY_ROOT'] = old


def setup(root, mod):
    for path in (mod.REQ, mod.REC, mod.DONE, mod.ACC, mod.INFLIGHT, mod.TMP,
                 mod.EXEC, root / 'logs'):
        path.mkdir(parents=True, exist_ok=True)


def check_lock():
    with tempfile.TemporaryDirectory(prefix='B-3b-executor-lock-', dir=BASE) as tmp:
        root = pathlib.Path(tmp)
        mod = load(root)
        setup(root, mod)
        (mod.RUN / 'STOP_executor').touch()
        lock_file = (mod.OPS / 'executor.lock').open('a+')
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            # A second invocation must leave before it logs "executor up" or opens a worker.
            result = subprocess.run(['python3', str(SOURCE)], env=dict(os.environ, KY_ROOT=str(root)),
                                    capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, result.stderr
            assert not (root / 'logs/executor.log').exists()
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
        mod.capabilities = lambda table_on_main: {'none': True}
        assert mod.main() == 0
        assert 'executor up' in (root / 'logs/executor.log').read_text()
    return 'exclusive instance lock: second exits; single controller starts'


def check_process_group():
    with tempfile.TemporaryDirectory(prefix='B-3b-executor-group-', dir=BASE) as tmp:
        root = pathlib.Path(tmp)
        marker = root / 'child.pid'
        command = ['bash', '-c', f'sleep 30 & echo $! > {marker}; exit 0']
        result = load(root).run_group(command, root, dict(os.environ), 5)
        assert result.returncode == 0
        child = int(marker.read_text().strip())
        state = subprocess.run(['ps', '-o', 'stat=', '-p', str(child)], capture_output=True, text=True).stdout.strip()
        assert not state or state.startswith('Z'), f'child survived process group cleanup: {child} {state}'
    return 'child process group killed after parent exits'


def check_fence_and_restart():
    with tempfile.TemporaryDirectory(prefix='B-3b-executor-fence-', dir=BASE) as tmp:
        root = pathlib.Path(tmp)
        mod = load(root)
        setup(root, mod)
        req = {'operation_id': 'fixture-prod', 'kind': 'fixture_production', 'item_id': 'B-3b',
               'idempotency_key': 'fixture-key', 'requested_by': 'adhikarin', 'kyd': 'fixture'}
        table = {'fixture_production': {'production': True}}
        (mod.REQ / 'fixture-prod.json').write_text(json.dumps(req))
        mod.sync = lambda: None
        mod.load_table = lambda: table
        mod.capabilities = lambda table_on_main: {'none': True}
        mod.validate = lambda request, current_table, caps, reserved=False: None
        mod.execute = lambda request, op: (0, 'dispatch returned while remote job may continue')
        def next_tick(_seconds):
            # Let the submitted task finish; stop the loop only after the receipt exists.
            future = mod._test_future[0]
            future.result(timeout=5)
            (mod.RUN / 'STOP_executor').touch()
        original_submit = None
        # Capture the production future without changing the executor's execution path.
        original_builder = mod.cf.ThreadPoolExecutor
        class CapturingExecutor(original_builder):
            def submit(self, fn, *args, **kwargs):
                result = super().submit(fn, *args, **kwargs)
                if getattr(self, '_thread_name_prefix', '') == 'prod':
                    mod._test_future.append(result)
                return result
        mod._test_future = []
        mod.cf.ThreadPoolExecutor = CapturingExecutor
        mod.time.sleep = next_tick
        assert mod.main() == 0
        receipt = json.loads((mod.REC / 'fixture-prod.json').read_text())
        assert receipt['status'] == 'COMPLETED'
        assert mod.FENCE.exists(), 'dispatch completion released the production fence'
        assert (mod.DONE / 'fixture-prod.json').exists()
        # A restart with a pending production request marks it interrupted and keeps the fence.
        interrupted = dict(req, operation_id='fixture-interrupted', idempotency_key='fixture-key-2')
        (mod.INFLIGHT / 'fixture-interrupted.json').write_text(json.dumps(interrupted))
        assert mod.main() == 0
        restart = json.loads((mod.REC / 'fixture-interrupted.json').read_text())
        assert restart['status'] == 'INTERRUPTED'
        assert (mod.DONE / 'fixture-interrupted.json').exists()
        assert mod.FENCE.exists(), 'restart released the production fence'
    return 'production fence retained after completed dispatch and interrupted restart'


def check_refresh_preflight_refusals():
    with tempfile.TemporaryDirectory(prefix='B-6r-refresh-', dir=BASE) as tmp:
        root = pathlib.Path(tmp)
        mod = load(root)
        setup(root, mod)
        assert mod.refresh_refusal_reason() is None
        (mod.REQ / 'queued.json').write_text('{}')
        assert 'pending operation request' in mod.refresh_refusal_reason()
        (mod.REQ / 'queued.json').unlink()
        (mod.INFLIGHT / 'remote.json').write_text('{}')
        assert 'in-flight operation' in mod.refresh_refusal_reason()
        (mod.INFLIGHT / 'remote.json').unlink()
        mod.FENCE.write_text('{"operation_id":"remote"}')
        assert 'quiescence evidence' in mod.refresh_refusal_reason()
        mod.FENCE.unlink()
        (mod.KY_ROOT / 'HOLD').touch()
        assert 'HOLD set' in mod.refresh_refusal_reason()
        (mod.KY_ROOT / 'HOLD').unlink()
        (mod.RUN / 'STOP_executor').touch()
        assert 'STOP_executor set' in mod.refresh_refusal_reason()
    return 'refresh preflight refuses queued, in-flight, fenced, HOLD and STOP states'


if __name__ == '__main__':
    results = [check_lock(), check_process_group(), check_fence_and_restart(), check_refresh_preflight_refusals()]
    out = {'result': 'PASS', 'cases': results, 'source': str(SOURCE)}
    (BASE / 'B-3b-executor-cases.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))
