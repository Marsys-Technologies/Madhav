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
    assert series[-1] == {"date": "2026-10-14", "done": 2, "total": 8}
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
