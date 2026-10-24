"""Run with -B and pytest's cache disabled; fixtures stay under --basetemp."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import server

NOW = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)


def fixture_state():
    items = [
        {"id": "A", "title": "First task", "status": "done"},
        {"id": "B", "title": "Second task", "status": "done"},
        {"id": "C", "title": "Not needed", "status": "not_applicable"},
        {"id": "D", "title": "Reopened task", "status": "review"},
        {"id": "V-A", "title": "Check first batch", "status": "ready"},
        {"id": "C-1", "title": "Close report", "status": "waiting"},
        {"id": "E", "title": "Blocked task", "status": "blocked"},
        {"id": "F", "title": "Deferred task", "status": "parked"},
    ]
    return {"generated_at": NOW.isoformat(), "tracks": [
        {"id": "one", "title": "First", "plain": "First workstream", "items": items[:4]},
        {"id": "two", "title": "Second", "plain": "Second workstream", "items": items[4:]},
    ], "native_queue": [{"id": "D-ASK", "title": "Choose", "status": "pending"}],
        "health": {"hold": False, "engine_tick_age_s": 1}}


def completions():
    return {"A": server.parse_time("2026-10-08T12:00:00Z"),
            "B": server.parse_time("2026-10-14T09:00:00Z"),
            "D": server.parse_time("2026-10-12T09:00:00Z")}


def test_counts_pace_projection_and_tracks():
    s = server.compute_summary(fixture_state(), completions(), NOW)
    m = s["metrics"]
    assert m["percent"] == 37.5
    assert (m["done"], m["not_applicable"], m["total"]) == (2, 1, 8)
    assert (m["in_progress"], m["ready"], m["waiting"], m["stuck"]) == (1, 1, 1, 2)
    assert (m["completed_24h"], m["completed_7d"]) == (1, 2)
    assert m["pace_per_day"] == pytest.approx(2 / 7)
    assert m["projected_finish"] == "2026-11-01"
    assert s["tracks"][0]["counts"]["done"] == 3
    assert s["tracks"][1]["counts"]["stuck"] == 2
    assert [i["id"] for i in s["milestones"]] == ["V-A", "C-1"]
    assert s["owner_decisions"][0]["id"] == "D-ASK"


def test_reopened_item_not_in_history():
    s = server.compute_summary(fixture_state(), completions(), NOW)
    assert [r["id"] for r in s["recently_completed"]] == ["B", "A"]
    series = s["history"]["series"]
    assert series[0]["done"] == 0
    assert {k: series[-1][k] for k in ("date", "done", "total")} == {"date": "2026-10-14", "done": 2, "total": 8}
    assert next(r for r in series if r["date"] == "2026-10-12")["done"] == 1


def test_zero_pace_and_missing_dates():
    s = server.compute_summary(fixture_state(), {}, NOW)
    assert s["metrics"]["pace_per_day"] == 0
    assert s["metrics"]["projected_finish"] is None
    assert s["history"]["undated_done"] == 2


def test_event_history_incremental_partial_line_and_rotation(tmp_path):
    p = tmp_path / "events.jsonl"
    first = {"kind": "item", "item": "A", "state": "done", "ts": "2026-10-08T12:00:00Z"}
    p.write_text(json.dumps(first) + "\n")
    reader = server.EventHistory(p)
    assert reader.read()["A"] == completions()["A"]
    offset = reader.offset
    assert reader.read()["A"] == completions()["A"]
    assert reader.offset == offset
    with p.open("a") as f:
        f.write(json.dumps({**first, "ts": "2026-10-09T12:00:00Z"}) + "\n")
        f.write('{"kind":"item"')
    assert reader.read()["A"] == completions()["A"]
    complete_offset = reader.offset
    assert complete_offset < p.stat().st_size
    with p.open("a") as f:
        f.write(',"item":"B","state":"done","ts":"2026-10-14T09:00:00Z"}\n')
    assert reader.read()["B"] == completions()["B"]
    p.unlink()
    p.write_text(json.dumps({**first, "item": "Z"}) + "\n")
    assert set(reader.read()) == {"Z"}


def test_malformed_event_is_unavailable(tmp_path):
    p = tmp_path / "events.jsonl"
    p.write_text('not json\n')
    with pytest.raises(ValueError):
        server.EventHistory(p).read()


def test_agents_use_process_evidence_and_terminal_result(tmp_path):
    direct, fleet = tmp_path / "direct", tmp_path / "fleet"
    direct.mkdir(); fleet.mkdir()
    job = direct / "X-20261014T100000Z-task"
    job.mkdir()
    (job / "prompt.md").write_text('# Common header\n## Your box\n## Item: Build the calendar\n')
    ended = direct / "X-20261014T090000Z-finished"
    ended.mkdir(); (ended / "DONE").touch()
    (ended / "result.json").write_text('{"status":"blocked"}')
    fj = fleet / "J-20261014T110000Z-b1"
    fj.mkdir()
    (fj / "state.json").write_text(json.dumps({"phase": "live", "item": "K4-3", "pid": 42,
                                               "model": "claude-opus-5-5", "started_at": "2026-10-14T11:00:00Z"}))
    processes = f'41 /opt/bin/codex exec --add-dir {job} -\n42 /bin/claude --print\n'
    result = server.detect_agents(direct, fleet, processes, NOW)
    assert result["count"] == 2
    assert result["by_engine"] == {"Codex": 1, "Claude": 1, "Unknown": 0}
    assert result["running"][0]["label"] == "Build the calendar"
    assert result["running"][0]["elapsed_seconds"] == 7200
    assert result["finished"][0]["status"] == "blocked"
    assert server.detect_agents(direct, fleet, '', NOW)["count"] == 0
    (job / "DONE").touch()
    assert server.detect_agents(direct, fleet, processes, NOW)["count"] == 1


def test_agent_folder_substring_is_not_a_match(tmp_path):
    d, f = tmp_path / "direct", tmp_path / "fleet"
    d.mkdir(); f.mkdir()
    j = d / "X-20261014T100000Z-task"; j.mkdir()
    (j / "prompt.md").write_text('## Build: Task\n')
    assert server.detect_agents(d, f, f'12 codex exec --add-dir {j}-other -', NOW)["count"] == 0


def test_tracker_unreachable_no_stale_counts(tmp_path):
    p = tmp_path / "events"; p.write_text('')
    d, f = tmp_path / "d", tmp_path / "f"; d.mkdir(); f.mkdir()
    responses = [fixture_state(), OSError('unreachable')]
    def fetch():
        r = responses.pop(0)
        if isinstance(r, Exception): raise r
        return r
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=fetch, process_list=lambda: '', cache_seconds=0)
    assert dashboard.summary(NOW)["metrics"]["done"] == 2
    bad = dashboard.summary(NOW)
    assert bad["metrics"] is None and bad["tracks"] is None
    assert bad["sources"]["tracker"]["available"] is False
    assert bad["sources"]["tracker"]["unavailable_since"] == NOW.isoformat()
    assert bad["agents"]["count"] == 0


def test_event_failure_preserves_only_current_tracker_counts(tmp_path):
    d, f = tmp_path / "d", tmp_path / "f"; d.mkdir(); f.mkdir()
    dashboard = server.Dashboard(event_path=tmp_path / "absent", direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=fixture_state, process_list=lambda: '', cache_seconds=0)
    s = dashboard.summary(NOW)
    assert s["metrics"]["done"] == 2
    assert s["metrics"]["pace_per_day"] is None
    assert s["metrics"]["completed_24h"] is None
    assert s["history"] is None and s["recently_completed"] is None
    assert not s["sources"]["events"]["available"]


def test_missing_agent_source_does_not_turn_into_zero(tmp_path):
    p = tmp_path / "events"; p.write_text('')
    d = tmp_path / "d"; d.mkdir()
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=tmp_path / "missing",
                                 fetch_tracker=fixture_state, process_list=lambda: '', cache_seconds=0)
    s = dashboard.summary(NOW)
    assert s["agents"]["count"] is None
    assert s["agents"]["by_engine"] is None
    assert not s["sources"]["fleet_jobs"]["available"]


def test_engine_status_needs_actual_evidence():
    assert server.engine_status({"hold": True}) == "paused"
    assert server.engine_status({"emergency_hold": True, "hold": True}) == "emergency hold"
    assert server.engine_status({"hold": False, "engine_tick_age_s": 1}) == "running"
    assert server.engine_status({"hold": False, "engine_tick_age_s": 1000}) is None
    assert server.engine_status({}) is None


def test_reject_invalid_tracker_shape():
    with pytest.raises(ValueError):
        server.compute_summary({"tracks": []}, {}, NOW)
    state = fixture_state(); state['tracks'][0]['items'][0]['status'] = 'invented'
    with pytest.raises(ValueError):
        server.compute_summary(state, {}, NOW)


def test_plain_text_hides_files_and_keeps_honest_unknown():
    text = server.plain_text('Waiting on platform/src/check.py and result.json. More detail.')
    assert '.py' not in text and '.json' not in text and '/' not in text
    assert server.plain_text('') == ''


def test_direct_job_process_can_reference_a_file_inside_job_folder(tmp_path):
    d, f = tmp_path / 'direct', tmp_path / 'fleet'
    d.mkdir(); f.mkdir()
    job = d / 'X-20261014T100000Z-task'; job.mkdir()
    (job / 'prompt.md').write_text('## Item: K4-3 — Attach canonical claims\n')
    result = server.detect_agents(d, f, f'41 /opt/bin/codex exec -o {job}/final_message.txt -', NOW)
    assert result['count'] == 1
    assert result['running'][0]['item'] == 'K4-3'


def test_cached_summary_and_failure_timestamp_recovery(tmp_path):
    p = tmp_path / 'events'; p.write_text('')
    d, f = tmp_path / 'd', tmp_path / 'f'; d.mkdir(); f.mkdir()
    calls = []
    def fetch():
        calls.append(True)
        return fixture_state()
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=fetch, process_list=lambda: '', cache_seconds=500)
    assert dashboard.cache_seconds == 5
    first = dashboard.summary(NOW)
    assert dashboard.summary(NOW) is first and len(calls) == 1
    dashboard.cache_seconds = 0
    def fail(): raise OSError('unavailable')
    dashboard.fetch_tracker = fail
    a = dashboard.summary(NOW)
    b = dashboard.summary(NOW + server.timedelta(minutes=2))
    assert a['sources']['tracker']['unavailable_since'] == b['sources']['tracker']['unavailable_since']
    dashboard.fetch_tracker = fixture_state
    assert dashboard.summary(NOW)['sources']['tracker']['unavailable_since'] is None


def test_dead_fleet_job_is_not_presented_as_working(tmp_path):
    d, f = tmp_path / 'd', tmp_path / 'f'; d.mkdir(); f.mkdir()
    j = f / 'J-20261014T100000Z-b1'; j.mkdir()
    (j / 'state.json').write_text('{"phase":"running","pid":99,"item":"K4-3","engine":"claude"}')
    assert server.detect_agents(d, f, '', NOW)['count'] == 0
    (j / 'state.json').write_text('{"phase":"mystery","pid":99}')
    with pytest.raises(ValueError):
        server.detect_agents(d, f, '', NOW)


def test_process_failure_invalidates_all_agent_counts(tmp_path):
    p = tmp_path / 'events'; p.write_text('')
    d, f = tmp_path / 'd', tmp_path / 'f'; d.mkdir(); f.mkdir()
    def fail(): raise OSError('processes unavailable')
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=fixture_state, process_list=fail, cache_seconds=0)
    result = dashboard.summary(NOW)
    assert result['agents']['count'] is None
    assert result['agents']['running'] == []
    assert result['sources']['processes']['available'] is False


def test_agents_show_explicit_items_from_review_prompt(tmp_path):
    d, f = tmp_path / 'd', tmp_path / 'f'; d.mkdir(); f.mkdir()
    j = d / 'X-20261014T100000Z-review'; j.mkdir()
    (j / 'prompt.md').write_text('## Independent item review\nItems under review: K6-5a (accepted), K6-123 and K6-5.\n')
    r = server.detect_agents(d, f, f'1 codex exec -o {j}/final_message.txt -', NOW)
    assert r['running'][0]['item'] == 'K6-5a, K6-123, K6-5'
    assert r['running'][0]['label'] == 'Independent item review'


@pytest.mark.parametrize('bad', [None, [], {'phase': []}])
def test_malformed_fleet_state_is_source_unavailable(tmp_path, bad):
    p = tmp_path / 'events'; p.write_text('')
    d, f = tmp_path / 'd', tmp_path / 'f'; d.mkdir(); f.mkdir()
    j = f / 'J-20261014T100000Z-b1'; j.mkdir()
    (j / 'state.json').write_text(json.dumps(bad))
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=fixture_state, process_list=lambda: '', cache_seconds=0)
    assert dashboard.summary(NOW)['sources']['fleet_jobs']['available'] is False


@pytest.mark.parametrize('bad', [None, [], 'invalid'])
def test_malformed_tracker_children_are_source_unavailable(tmp_path, bad):
    p = tmp_path / 'events'; p.write_text('')
    d, f = tmp_path / 'd', tmp_path / 'f'; d.mkdir(); f.mkdir()
    state = fixture_state(); state['tracks'] = [bad]
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=lambda: state, process_list=lambda: '', cache_seconds=0)
    result = dashboard.summary(NOW)
    assert result['metrics'] is None and result['sources']['tracker']['available'] is False


def test_fleet_pid_with_unrecognised_process_makes_count_unknown(tmp_path):
    p = tmp_path / 'events'; p.write_text('')
    d, f = tmp_path / 'd', tmp_path / 'f'; d.mkdir(); f.mkdir()
    j = f / 'J-20261014T100000Z-b1'; j.mkdir()
    (j / 'state.json').write_text('{"phase":"live","pid":99,"item":"K4-3","engine":"claude"}')
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=fixture_state, process_list=lambda: '99 unrelated-program', cache_seconds=0)
    result = dashboard.summary(NOW)
    assert result['agents']['count'] is None
    assert result['sources']['fleet_jobs']['available'] is False


def test_hash_is_not_presented_as_review_evidence():
    assert 'reviewed' not in server.plain_text('Code at 6898a3d8a04bdfe8996e1dd1542c8d88e2ba7bc4.')


def d21_state():
    state = fixture_state()
    state['tracks'] = [{'id': 'J', 'title': 'Transit', 'plain': 'Transit work', 'items': [
        {'id': 'J-1a', 'title': 'Build small-test tools', 'status': 'done'},
        {'id': 'J-W4-P01', 'title': 'Packet join', 'status': 'not_applicable'},
        {'id': 'J-0m', 'title': 'Extend plan model', 'status': 'done'},
        {'id': 'J-4b', 'title': 'Apply protected changes', 'status': 'waiting'},
        {'id': 'V-J6', 'title': 'Review publication', 'status': 'done'},
        {'id': 'VC-1', 'title': 'Freeze pre-registration', 'status': 'done'},
        {'id': 'K7-1a', 'title': 'Build registry views and registration', 'status': 'done'},
        {'id': 'K8-REG', 'title': 'Registry migration', 'status': 'done'},
    ]}]
    for item in state['tracks'][0]['items']:
        item['completion_kind'] = 'artifact' if item['id'] in ('J-0m', 'VC-1') else 'code'
    state['overall'] = {'pct': 99, 'total': 999}
    return state


def d21_dates():
    return {iid: server.parse_time(ts) for iid, ts in {
        'J-1a': '2026-10-14T09:00:00Z', 'J-0m': '2026-10-14T10:00:00Z',
        'V-J6': '2026-10-13T12:00:00Z', 'VC-1': '2026-10-08T12:00:00Z',
        'K7-1a': '2026-10-07T11:59:59Z', 'K8-REG': '2026-10-14T13:00:00Z',
    }.items()}


def test_d21_one_percentage_and_wave_partition():
    s = server.compute_summary(d21_state(), d21_dates(), NOW)
    assert s['metrics']['percent'] == 87.5  # seven complete, eight in scope; ignore weighted 99
    assert s['progress_lines'] == [
        {'id': 'wave4', 'label': 'Wave 4 · Gochara 5.0', 'complete': 3, 'total': 4},
        {'id': 'rest', 'label': 'Everything else', 'complete': 4, 'total': 4},
        {'id': 'total', 'label': 'Total', 'complete': 7, 'total': 8},
    ]


def test_d21_burnup_includes_not_needed_and_splits_wave():
    dates = d21_dates()
    complete_dates = {**dates, 'J-W4-P01': server.parse_time('2026-10-14T08:00:00Z')}
    s = server.compute_summary(d21_state(), dates, NOW, first_complete=complete_dates)
    last = s['history']['series'][-1]
    assert (last['wave4'], last['rest'], last['complete']) == (3, 3, 6)
    assert s['history']['undated_complete'] == 1  # future event is not historical evidence
    assert s['history']['dated_complete'] == 6
    assert s['history']['not_applicable'] == 1


def test_d21_scope_marker_has_exact_time_and_size():
    now = server.parse_time('2026-10-15T12:00:00Z')
    s = server.compute_summary(d21_state(), {}, now)
    assert s['history']['scope_changes'][0] == {
        'at': '2026-10-14T19:04:00+00:00', 'before': 152, 'after': 213,
        'label': 'Scope grew: 152 → 213 items · 14 Oct 19:04 UTC',
    }
    assert any(p['at'] == '2026-10-14T19:04:00+00:00' for p in s['history']['series'])
    assert server.compute_summary(d21_state(), {}, NOW)['history']['scope_changes'] == []


def test_d21_closure_classes_and_rolling_boundaries():
    m = server.compute_summary(d21_state(), d21_dates(), NOW)['metrics']
    assert m['closures_24h'] == {'capability': 1, 'verdict': 1, 'planning': 1}
    assert m['closures_7d'] == {'capability': 1, 'verdict': 1, 'planning': 2}
    assert (m['completed_24h'], m['completed_7d']) == (3, 4)
    assert server.compute_summary(d21_state(), None, NOW)['metrics']['closures_24h'] is None


def test_d21_event_reader_retains_not_applicable_dates(tmp_path):
    p = tmp_path / 'events'
    p.write_text('\n'.join(json.dumps(e) for e in [
        {'kind': 'item', 'item': 'J-W4-P01', 'state': 'not_applicable', 'ts': '2026-10-14T08:00:00Z'},
        {'kind': 'item', 'item': 'J-1a', 'state': 'done', 'ts': '2026-10-14T09:00:00Z'},
    ]) + '\n')
    reader = server.EventHistory(p)
    done = reader.read()
    assert set(done) == {'J-1a'}
    s = server.compute_summary(d21_state(), done, NOW, first_complete=reader.first_complete)
    assert s['history']['series'][-1]['wave4'] == 2
    assert s['metrics']['completed_24h'] == 1  # not-needed is not a code closure
    p.write_text('')
    reader.read()
    assert reader.first_complete == {}


def make_duration_job(root, name, end):
    import os
    job = root / name
    job.mkdir()
    (job / 'DONE').touch()
    stamp = server.parse_time(end).timestamp()
    os.utime(job / 'DONE', (stamp, stamp))
    return job


def test_d21_agent_hours_per_closure_uses_all_finished_work(tmp_path):
    # Include failed/review jobs, count each once; unfinished/future/out-of-window jobs contribute nothing.
    make_duration_job(tmp_path, 'X-20261014T080000Z-build', '2026-10-14T10:00:00Z')
    failed = make_duration_job(tmp_path, 'X-20261013T100000Z-review', '2026-10-13T12:00:00Z')
    (failed / 'result.json').write_text('{"status":"blocked"}')
    make_duration_job(tmp_path, 'X-20261008T100000Z-old', '2026-10-08T11:00:00Z')
    make_duration_job(tmp_path, 'X-20261014T130000Z-future', '2026-10-14T14:00:00Z')
    (tmp_path / 'X-20261014T070000Z-running').mkdir()
    hours = server.job_effort(tmp_path, NOW)
    assert hours['agent_hours_24h'] == 4
    assert hours['agent_hours_7d'] == 5
    s = server.compute_summary(d21_state(), d21_dates(), NOW, effort=hours)
    assert s['metrics']['agent_hours_per_closure_24h'] == pytest.approx(4 / 3)
    assert s['metrics']['agent_hours_per_closure_7d'] == 1.25
    zero = server.compute_summary(fixture_state(), {}, NOW, effort=hours)['metrics']
    assert zero['agent_hours_per_closure_24h'] is None
    unknown = server.compute_summary(fixture_state(), completions(), NOW)['metrics']
    assert unknown['agent_hours_per_closure_24h'] is None


def test_d21_bad_job_timing_is_unknown_not_zero(tmp_path):
    make_duration_job(tmp_path, 'X-20261014T100000Z-bad', '2026-10-14T09:00:00Z')
    with pytest.raises(ValueError):
        server.job_effort(tmp_path, NOW)


def test_d21_dashboard_observes_further_scope_changes(tmp_path):
    p = tmp_path / 'events'; p.write_text('')
    d, f = tmp_path / 'd', tmp_path / 'f'; d.mkdir(); f.mkdir()
    state = fixture_state()
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=lambda: state, process_list=lambda: '', cache_seconds=0)
    dashboard.summary(NOW)
    state['tracks'][0]['items'].append({'id': 'NEW', 'title': 'Extra scope', 'status': 'waiting'})
    later = NOW + server.timedelta(minutes=5)
    state['generated_at'] = later.isoformat()
    change = dashboard.summary(later)['history']['scope_changes'][-1]
    assert (change['before'], change['after'], change['at']) == (8, 9, later.isoformat())


def evaluate_page(expression, state):
    """Run the real inline render functions with macOS's system JS engine; no packages/scripts."""
    import ctypes
    import ctypes.util
    import sys
    if sys.platform != 'darwin':
        pytest.skip('Rendering smoke test uses the macOS system JavaScriptCore framework')
    lib = ctypes.CDLL(ctypes.util.find_library('JavaScriptCore'))
    ptr = ctypes.c_void_p
    signatures = {
        'JSGlobalContextCreate': (ptr, [ptr]), 'JSGlobalContextRelease': (None, [ptr]),
        'JSStringCreateWithUTF8CString': (ptr, [ctypes.c_char_p]), 'JSStringRelease': (None, [ptr]),
        'JSEvaluateScript': (ptr, [ptr, ptr, ptr, ptr, ctypes.c_int, ctypes.POINTER(ptr)]),
        'JSValueToStringCopy': (ptr, [ptr, ptr, ctypes.POINTER(ptr)]),
        'JSStringGetMaximumUTF8CStringSize': (ctypes.c_size_t, [ptr]),
        'JSStringGetUTF8CString': (ctypes.c_size_t, [ptr, ctypes.c_char_p, ctypes.c_size_t]),
    }
    for name, (result, args) in signatures.items():
        function = getattr(lib, name); function.restype = result; function.argtypes = args
    page = (Path(__file__).parent / 'index.html').read_text()
    script = page.split('<script>', 1)[1].split('function setTheme', 1)[0]
    script = "const document={documentElement:{clientWidth:390}};\n" + script
    script += '\nsummary=' + json.dumps(state) + ';\n' + expression
    context = lib.JSGlobalContextCreate(None)
    source = lib.JSStringCreateWithUTF8CString(script.encode())
    exception = ptr()
    result = lib.JSEvaluateScript(context, source, None, None, 1, ctypes.byref(exception))
    value = lib.JSValueToStringCopy(context, exception.value or result, None)
    size = lib.JSStringGetMaximumUTF8CStringSize(value)
    buffer = ctypes.create_string_buffer(size)
    lib.JSStringGetUTF8CString(value, buffer, size)
    text = buffer.value.decode()
    lib.JSStringRelease(value); lib.JSStringRelease(source); lib.JSGlobalContextRelease(context)
    assert not exception.value, text
    return text


def test_d21_page_renders_one_percentage_three_lines_and_scope_marker():
    from html.parser import HTMLParser
    class Markup(HTMLParser):
        def __init__(self):
            super().__init__(); self.text = []; self.tags = []
        def handle_data(self, data):
            self.text.append(data)
        def handle_starttag(self, tag, attrs):
            self.tags.append((tag, dict(attrs)))
    state = server.compute_summary(d21_state(), d21_dates(), server.parse_time('2026-10-15T08:00:00Z'),
                                   effort={'agent_hours_24h': 6, 'agent_hours_7d': 10})
    markup = Markup()
    markup.feed(evaluate_page('headline()+chart()', state))
    text = ''.join(markup.text)
    assert text.count('%') == 1 and '87.5%' in text
    assert sum(attrs.get('class') == 'progress-line' for _, attrs in markup.tags) == 3
    assert sum(tag == 'polyline' for tag, _ in markup.tags) == 3
    assert all(label in text for label in ('Wave 4', 'Everything else', 'Total complete'))
    assert '152 → 213' in text and '19:04' in text and 'UTC' in text
    assert 'Capabilities' in text and 'Verdicts' in text and 'Planning' in text
    assert 'Agent-hours per closed item' in text and '2.00' in text


def test_d21_closure_class_uses_code_metadata_not_registry_title():
    assert server.closure_class({'id': 'K7-1a', 'completion_kind': 'code'}) == 'capability'
    assert server.closure_class({'id': 'J-0m', 'completion_kind': 'code'}) == 'planning'
    assert server.closure_class({'id': 'V-J6', 'completion_kind': 'packet'}) == 'verdict'
    assert server.closure_class({'id': 'PLAN', 'completion_kind': 'artifact'}) == 'planning'
    assert server.closure_class({'id': 'JOIN-ALL'}) == 'planning'


def test_d21_timing_failure_keeps_closure_counts(tmp_path):
    p = tmp_path / 'events'
    p.write_text('{"kind":"item","item":"B","state":"done","ts":"2026-10-14T09:00:00Z"}\n')
    d, f = tmp_path / 'missing', tmp_path / 'f'; f.mkdir()
    dashboard = server.Dashboard(event_path=p, direct_jobs=d, fleet_jobs=f,
                                 fetch_tracker=fixture_state, process_list=lambda: '', cache_seconds=0)
    s = dashboard.summary(NOW)
    assert s['metrics']['completed_24h'] == 1
    assert s['metrics']['agent_hours_per_closure_24h'] is None
    assert not s['sources']['job_timing']['available']


def test_d21_page_has_no_competing_done_over_total_metric():
    from html.parser import HTMLParser
    class Text(HTMLParser):
        def __init__(self):
            super().__init__(); self.data = []
        def handle_data(self, value):
            self.data.append(value)
    state = server.compute_summary(d21_state(), d21_dates(), NOW)
    text = Text(); text.feed(evaluate_page('headline()', state))
    visible = ''.join(text.data)
    assert '6 / 8' not in visible  # six done omits the not-needed completion
    assert '7 / 8' in visible
    assert visible.count('%') == 1


def test_tracker_unknown_status_is_accepted_and_shown_as_not_yet_measured():
    """The live tracker reports 'unknown' for items whose detector has not been measured yet; the whole
    feed must not be rejected (that blanked the dashboard on 2026-10-15) and the item counts as waiting."""
    import server
    assert 'unknown' in server.STATUSES
    assert server.GROUPS['unknown'] == 'waiting'
    assert server.LABELS['unknown'] == 'Not yet measured'


# ---------------------------------------------------------------------------------------- deferred bucket (owner direction 2026-10-22)

def deferred_state():
    """The tracker flags a row `deferred: true` (state.is_deferred): triage class b, outside the closure, unfinished."""
    state = fixture_state()
    state['tracks'][1]['items'] = state['tracks'][1]['items'] + [
        {"id": "G", "title": "Deferred by ruling", "status": "parked", "deferred": True},
        {"id": "H", "title": "Deferred, unmeasured", "status": "unknown", "deferred": True},
        {"id": "J", "title": "Not deferred, parked", "status": "parked", "deferred": False},
    ]
    return state


def test_deferred_items_are_their_own_bucket_not_stuck_waiting_or_attention():
    # Reversion: present_item ignores the `deferred` flag -> G, H land in stuck/waiting and in attention.
    base = server.compute_summary(fixture_state(), completions(), NOW)["metrics"]
    s = server.compute_summary(deferred_state(), completions(), NOW)
    m = s["metrics"]
    assert m["deferred"] == 2                                              # G (parked) and H (unmeasured)
    assert (m["stuck"], m["waiting"]) == (base["stuck"] + 1, base["waiting"])   # only J (parked, not deferred) adds to stuck; H is not waiting
    assert [i["id"] for i in s["deferred"]] == ["G", "H"]
    assert all(i["group"] == "deferred" and i["status_label"] == "Deferred" for i in s["deferred"])
    assert "G" not in [i["id"] for i in s["attention"]] and "H" not in [i["id"] for i in s["attention"]]
    assert "J" in [i["id"] for i in s["attention"]]                        # a parked item that is not deferred is still set aside


def test_a_deferred_item_never_counts_as_done_and_moves_no_other_figure():
    # Reversion: group 'deferred' folded into 'done' (e.g. GROUPS gains the deferred mapping) -> complete/percent move.
    with_flag, without = deferred_state(), deferred_state()
    for item in without["tracks"][1]["items"]:
        item.pop("deferred", None)
    a = server.compute_summary(with_flag, completions(), NOW)["metrics"]
    b = server.compute_summary(without, completions(), NOW)["metrics"]
    for key in ("total", "done", "not_applicable", "complete", "percent", "in_progress", "ready", "completed_24h", "completed_7d",
                "pace_per_day", "projected_finish"):
        assert a[key] == b[key], key
    assert a["deferred"] == 2 and b["deferred"] == 0


def test_the_page_names_the_deferred_bucket_and_its_track_count_without_error():
    state = server.compute_summary(deferred_state(), completions(), NOW)
    text = evaluate_page('headline()+workstreams()+attention()', state)
    assert 'Deferred' in text and 'not counted as done' in text
    assert state['tracks'][1]['counts']['deferred'] == 2
