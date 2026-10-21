"""A10.1 item 6: the executor rewrites run/ops/CAPABILITIES.json every 30 s (was 300 s); the 45 s freshness bound is unchanged.

Oracle source: executor.py module constants CAPS_REFRESH_S (30) and CAPS_FRESH_S (45), and the main loop (`main()`), driven here on a fake clock.
A snapshot can be at most one refresh interval plus one idle tick (LOOP_TICK_S) old, so it never reaches the 45 s bound a reader applies."""
import importlib.util
import time
from pathlib import Path

FLEET = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location('executor_caps_refresh', FLEET / 'executor.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_main_loop_rewrites_capabilities_every_30_seconds_inside_the_45_second_bound(tmp_path, monkeypatch):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    ex = load()
    assert (ex.CAPS_REFRESH_S, ex.CAPS_FRESH_S) == (30, 45)
    clock = [1_000_000.0]
    stamps = []

    def fake_capabilities(table_on_main):
        stamps.append(clock[0])
        return {'none': True}

    def fake_sleep(seconds):
        clock[0] += seconds
        if clock[0] >= 1_000_000.0 + 200: (ex.RUN / 'STOP_executor').touch()

    monkeypatch.setattr(time, 'time', lambda: clock[0])
    monkeypatch.setattr(time, 'sleep', fake_sleep)
    monkeypatch.setattr(ex, 'sync', lambda: None)
    monkeypatch.setattr(ex, 'refresh_from_main_or_fail_closed', lambda: True)
    monkeypatch.setattr(ex, 'load_table', lambda: {})
    monkeypatch.setattr(ex, 'capabilities', fake_capabilities)
    monkeypatch.setattr(ex, 'log', lambda *a: None)
    assert ex.main() == 0
    loop_stamps = stamps[1:]          # stamps[0] is the start-up snapshot
    gaps = [b - a for a, b in zip(loop_stamps, loop_stamps[1:])]
    assert len(gaps) >= 5, gaps
    assert all(g <= ex.CAPS_REFRESH_S for g in gaps), gaps       # a refresh happens within 30 s of the previous one
    assert all(g < ex.CAPS_FRESH_S for g in gaps), gaps          # no snapshot ever reaches the 45 s freshness bound


def test_due_threshold_is_exactly_thirty_seconds():
    ex = load()
    assert ex.capabilities_due(100.0, 129.9) is False
    assert ex.capabilities_due(100.0, 130.0) is True
    assert ex.CAPS_REFRESH_S + ex.LOOP_TICK_S < ex.CAPS_FRESH_S
