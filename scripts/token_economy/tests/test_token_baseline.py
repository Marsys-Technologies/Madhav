"""Characterisation tests for scripts/token_economy/token_baseline.py (KV3-B-BASELINE).

The script is a fixed candidate: its bytes are the reviewed scratch source and
are never edited here.  These tests pin what those bytes do.

  * Arithmetic and de-duplication are asserted against figures summed by hand
    in each test.
  * A label (workspace, role) or an empty-input result is asserted as observed.
    Where the observed behaviour does not meet plan v2.7 section 13 the test
    pins it and says so in a "GAP" comment; KV3-B-KYREPORT turns each gap into
    `unknown`.

Every test points the three roots at directories it writes under the pytest
base.  The autouse root guard fails a test in which one of them still has its
default value, before that test's body runs.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import textwrap

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.dirname(TESTS_DIR)
SCRIPT = os.path.join(SCRIPT_DIR, "token_baseline.py")

# The script's directory goes on sys.path so that the script's own worker
# processes can import it by the same module name.
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import token_baseline as tb  # noqa: E402

# Ruling P14: the reviewed candidate.
EXPECTED_SHA256 = "28c1bb5b9df644a0a60a44a80b0a9a01c949db2838e03bf766631411b45c4176"
EXPECTED_BYTES = 26018

ROOT_NAMES = ("CLAUDE_ROOT", "CODEX_ROOT", "FLEET_LOGS")
# Written out here, not read back from the script, so the guard does not depend
# on the thing it guards.
DEFAULT_ROOTS = {
    "CLAUDE_ROOT": os.path.join(os.path.expanduser("~"), ".claude", "projects"),
    "CODEX_ROOT": os.path.join(os.path.expanduser("~"), ".codex", "sessions"),
    "FLEET_LOGS": "/Users/Dev/kalayantra/logs",
}
IMPORT_TIME_ROOTS = {name: getattr(tb, name) for name in ROOT_NAMES}

OPUS = "claude-opus-5-5"
HAIKU = "claude-haiku-5-5"
TS = "2026-10-11T09:00:00.000Z"

# A Claude Code project folder name that is_madhav() accepts on its own, so the
# fixtures are counted whatever the pytest base path is.
PROJECT = "-Users-Dev-Vibe-Coding-Apps-Madhav"
SHARED_CWD = "/Users/Dev/Vibe-Coding/Apps/Madhav"
PLANNER_CWD = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan"
CAMPAIGN_CWD = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
BOOTSTRAP_CWD = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-baseline"
LEGACY_CAMPAIGN_CWD = "/Users/Dev/kalayantra/wt/campaign"


# ------------------------------------------------------------ root guard ----
class RootGuardError(AssertionError):
    pass


def check_roots(base):
    """Raise unless all three roots are redirected to somewhere under `base`."""
    base = os.path.realpath(str(base))
    for name in ROOT_NAMES:
        value = getattr(tb, name)
        if value in (DEFAULT_ROOTS[name], IMPORT_TIME_ROOTS[name]):
            raise RootGuardError(f"{name} still has its default value {value!r}")
        if not os.path.realpath(value).startswith(base + os.sep):
            raise RootGuardError(f"{name}={value!r} is not under the pytest base {base!r}")


@pytest.fixture
def roots(monkeypatch, tmp_path):
    """Three empty fixture roots under the pytest base, with the script pointed at them."""
    made = {}
    for name, sub in zip(ROOT_NAMES, ("claude_projects", "codex_sessions", "fleet_logs")):
        d = tmp_path / sub
        d.mkdir()
        monkeypatch.setattr(tb, name, str(d))
        made[name] = d
    return made


@pytest.fixture(autouse=True)
def root_guard(request, monkeypatch, tmp_path):
    if "roots" in request.fixturenames:
        request.getfixturevalue("roots")
    check_roots(tmp_path)          # a test that left a default never starts
    real_main = tb.main

    def guarded_main(argv=None):
        check_roots(tmp_path)      # nor may a test put one back and then run
        return real_main(argv)

    monkeypatch.setattr(tb, "main", guarded_main)


# --------------------------------------------------------------- helpers ----
def assistant(mid, rid, usage, *, session, cwd=SHARED_CWD, ts=TS, model=OPUS, branch="main", **extra):
    i, o, cc, cr = usage
    line = {"type": "assistant", "sessionId": session, "cwd": cwd, "gitBranch": branch,
            "timestamp": ts, "requestId": rid,
            "message": {"id": mid, "role": "assistant", "model": model,
                        "content": [{"type": "text", "text": "ok"}],
                        "usage": {"input_tokens": i, "output_tokens": o,
                                  "cache_creation_input_tokens": cc,
                                  "cache_read_input_tokens": cr}}}
    line.update(extra)
    return line


def prompt(session, cwd=SHARED_CWD):
    return {"type": "user", "sessionId": session, "cwd": cwd, "timestamp": TS,
            "message": {"role": "user", "content": "go"}}


def tool_result(session, cwd=SHARED_CWD):
    return {"type": "user", "sessionId": session, "cwd": cwd, "timestamp": TS,
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "toolu_1", "content": "done"}]}}


def write_jsonl(path, lines, tail=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(line) + "\n" for line in lines) + tail)
    return path


def run(tmp_path, *args):
    out = tmp_path / "baseline.json"
    assert not out.exists()
    assert tb.main(["--json", str(out), "--jobs", "1", *args]) == 0
    report = json.loads(out.read_text())
    out.unlink()
    return report


def four(d):
    """(input, output, cache_creation, cache_read, total) of a totals row."""
    return tuple(d[k] for k in (*tb.CLASSES, "total"))


def row(table, key):
    hits = [r for r in table if r["key"] == key]
    assert len(hits) == 1, f"{key!r} appears {len(hits)} times in {[r['key'] for r in table]}"
    return hits[0]


def keys(table):
    return sorted(r["key"] for r in table)


ZERO_SOURCES = {"claude_files": 0, "claude_files_with_usage": 0, "codex_files_scanned": 0,
                "codex_madhav_sessions": 0, "fleet_logs": 0, "claude_api_calls_deduped": 0,
                "claude_cross_file_duplicate_keys_dropped": 0}


# ------------------------------------------------------- the fixed bytes ----
def assert_is_reviewed_candidate(path):
    with open(path, "rb") as fh:
        data = fh.read()
    assert hashlib.sha256(data).hexdigest() == EXPECTED_SHA256
    assert len(data) == EXPECTED_BYTES


def test_committed_script_is_the_reviewed_bytes(roots):
    assert os.path.realpath(tb.__file__) == os.path.realpath(SCRIPT)
    assert_is_reviewed_candidate(SCRIPT)
    # git mode 100644: no execute bit.
    assert stat.S_IMODE(os.stat(SCRIPT).st_mode) & 0o111 == 0


@pytest.mark.parametrize("offset", [0, 13009, EXPECTED_BYTES - 1])
def test_hash_check_fails_on_one_changed_byte(roots, tmp_path, offset):
    with open(SCRIPT, "rb") as fh:
        data = bytearray(fh.read())
    data[offset] ^= 0x01
    copy = tmp_path / "token_baseline_one_byte_changed.py"
    copy.write_bytes(bytes(data))
    assert len(data) == EXPECTED_BYTES
    with pytest.raises(AssertionError):
        assert_is_reviewed_candidate(copy)


def test_module_surface(roots):
    assert tb.CLASSES == ("input", "output", "cache_creation", "cache_read")
    assert IMPORT_TIME_ROOTS == DEFAULT_ROOTS
    assert IMPORT_TIME_ROOTS["FLEET_LOGS"] == "/Users/Dev/kalayantra/logs"


# ------------------------------------------------------------ root guard ----
@pytest.mark.parametrize("name", ROOT_NAMES)
def test_root_guard_refuses_a_default_root(roots, tmp_path, monkeypatch, name):
    out = tmp_path / "never_written.json"
    globbed = []
    with monkeypatch.context() as m:
        m.setattr(tb.glob, "glob", lambda *a, **k: globbed.append(a) or [])
        m.setattr(tb, name, DEFAULT_ROOTS[name])
        with pytest.raises(RootGuardError, match=name):
            check_roots(tmp_path)
        with pytest.raises(RootGuardError, match=name):
            tb.main(["--json", str(out), "--jobs", "1"])
    assert globbed == []            # refused before anything was listed
    assert not out.exists()
    check_roots(tmp_path)


def test_root_guard_refuses_a_root_outside_the_pytest_base(roots, tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(tb, "CODEX_ROOT", os.path.dirname(str(tmp_path)))
        with pytest.raises(RootGuardError, match="CODEX_ROOT"):
            check_roots(tmp_path)


def test_root_guard_fails_a_test_that_would_read_the_real_roots(roots, tmp_path):
    """Two probe tests run in their own pytest; neither may pass, neither may read."""
    sentinel = tmp_path / "glob_was_called"
    probe = tmp_path / "test_root_guard_probe.py"
    probe.write_text(textwrap.dedent(f"""\
        import sys
        sys.path.insert(0, {TESTS_DIR!r})
        from test_token_baseline import DEFAULT_ROOTS, root_guard, roots, tb  # noqa: F401

        def _record(*a, **k):
            with open({str(sentinel)!r}, "a") as fh:
                fh.write("glob\\n")
            return []

        def test_never_points_the_roots(monkeypatch, tmp_path):
            monkeypatch.setattr(tb.glob, "glob", _record)
            tb.main(["--json", str(tmp_path / "o.json"), "--jobs", "1"])

        def test_puts_a_default_back(roots, monkeypatch, tmp_path):
            monkeypatch.setattr(tb.glob, "glob", _record)
            monkeypatch.setattr(tb, "CLAUDE_ROOT", DEFAULT_ROOTS["CLAUDE_ROOT"])
            tb.main(["--json", str(tmp_path / "o.json"), "--jobs", "1"])
        """))
    done = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", str(probe), "-q", "-p", "no:cacheprovider",
         "--rootdir", str(tmp_path), "--basetemp", str(tmp_path / "probe_base")],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=300)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "1 failed, 1 error" in done.stdout, done.stdout
    assert "passed" not in done.stdout, done.stdout
    assert "RootGuardError: CLAUDE_ROOT still has its default value" in done.stdout, done.stdout
    assert not sentinel.exists()


# --------------------------------------------------------------- is_madhav --
def test_is_madhav_filter(roots, tmp_path):
    # Asserted on the function: the pytest base path may itself hold a token.
    assert tb.is_madhav("/Users/Dev/.claude/projects/" + PROJECT + "/s.jsonl")
    assert tb.is_madhav("/Users/Dev/kalayantra/wt/k1")
    assert tb.is_madhav("/Users/Dev/.codex/worktrees/purna-x")
    assert tb.is_madhav("-Users-Dev-worktrees-noindex-MADHAV-claude-x")
    assert not tb.is_madhav("")
    assert not tb.is_madhav(None)
    assert not tb.is_madhav("/Users/Dev/.claude/projects/-Users-Dev-other-project/s.jsonl")
    assert not tb.is_madhav("/Users/Dev/.codex/worktrees/zzz")

    # main() applies it to the whole file path; the expectation follows the
    # function, so it holds whether or not the base path carries a token.
    other = write_jsonl(roots["CLAUDE_ROOT"] / "-Users-Dev-other-project" / "o.jsonl",
                        [assistant("msg_o", "req_o", (1, 2, 3, 4), session="other")])
    counted = tb.is_madhav(str(other))
    report = run(tmp_path)
    assert report["sources"]["claude_files"] == (1 if counted else 0)
    assert four(report["grand_total"]) == ((1, 2, 3, 4, 10) if counted else (0, 0, 0, 0, 0))


# ------------------------------------------------------ normal completion ---
def test_normal_completion(roots, tmp_path):
    s = "sess-normal"
    write_jsonl(roots["CLAUDE_ROOT"] / PROJECT / f"{s}.jsonl", [
        {"type": "system", "sessionId": s, "cwd": SHARED_CWD, "subtype": "init"},
        prompt(s),
        assistant("msg_a", "req_a", (100, 20, 3000, 0), session=s),
        tool_result(s),
        assistant("msg_b", "req_b", (7, 150, 400, 3000), session=s),
        assistant("msg_c", "req_c", (5, 60, 0, 3400), session=s, model=HAIKU),
    ])
    report = run(tmp_path)

    # input 100+7+5, output 20+150+60, cache_creation 3000+400+0, cache_read 0+3000+3400
    assert four(report["grand_total"]) == (112, 230, 3400, 6400, 10142)
    assert report["sources"] == {**ZERO_SOURCES, "claude_files": 1, "claude_files_with_usage": 1,
                                 "claude_api_calls_deduped": 3}
    assert keys(report["by_provider"]) == ["claude"]
    assert four(row(report["by_provider"], "claude")) == (112, 230, 3400, 6400, 10142)
    assert keys(report["by_model"]) == [HAIKU, OPUS]
    assert four(row(report["by_model"], OPUS)) == (107, 170, 3400, 3000, 6677)
    assert four(row(report["by_model"], HAIKU)) == (5, 60, 0, 3400, 3465)
    assert four(row(report["by_workspace"], "shared-checkout")) == (112, 230, 3400, 6400, 10142)
    assert four(row(report["by_role"], "interactive")) == (112, 230, 3400, 6400, 10142)
    assert report["shares"]["cache_read_share"] == 6400 / 10142
    assert report["shares"]["output_share"] == 230 / 10142

    assert len(report["top_sessions"]) == 1
    top = report["top_sessions"][0]
    assert top["key"] == "claude:sess-normal"
    assert four(top) == (112, 230, 3400, 6400, 10142)
    assert (top["workspace"], top["role"], top["branch"]) == ("shared-checkout", "interactive", "main")
    # one prompt; the tool-result line is not a turn
    assert (top["calls"], top["turns"], top["subagent_files"], top["first"]) == (3, 1, 0, "2026-10-11")


def test_since_and_until_select_calls_by_utc_day(roots, tmp_path):
    s = "sess-window"
    write_jsonl(roots["CLAUDE_ROOT"] / PROJECT / f"{s}.jsonl", [
        assistant("msg_1", "req_1", (1, 0, 0, 0), session=s, ts="2026-10-09T23:59:59.999Z"),
        assistant("msg_2", "req_2", (0, 10, 0, 0), session=s, ts="2026-10-10T00:00:00.000Z"),
        assistant("msg_3", "req_3", (0, 0, 100, 0), session=s, ts="2026-10-11T12:00:00.000Z"),
        assistant("msg_4", "req_4", (0, 0, 0, 1000), session=s, ts="2026-10-12T00:00:00.000Z"),
    ])
    whole = run(tmp_path)
    assert four(whole["grand_total"]) == (1, 10, 100, 1000, 1111)
    assert whole["window"] == {"since": None, "until": None}
    assert [(r["key"], r["total"]) for r in whole["by_day"]] == [
        ("2026-10-09", 1), ("2026-10-10", 10), ("2026-10-11", 100), ("2026-10-12", 1000)]
    # 2026-10-05 and 2026-10-12 are Mondays.
    assert [(r["key"], r["total"]) for r in whole["by_week"]] == [("2026-W41", 111), ("2026-W42", 1000)]

    one_day = run(tmp_path, "--since", "2026-10-10", "--until", "2026-10-10")
    assert four(one_day["grand_total"]) == (0, 10, 0, 0, 10)
    assert one_day["sources"]["claude_api_calls_deduped"] == 1
    assert one_day["window"] == {"since": "2026-10-10", "until": "2026-10-10"}

    since = run(tmp_path, "--since", "2026-10-10")
    assert four(since["grand_total"]) == (0, 10, 100, 1000, 1110)
    assert since["sources"]["claude_api_calls_deduped"] == 3

    until = run(tmp_path, "--until", "2026-10-09")
    assert four(until["grand_total"]) == (1, 0, 0, 0, 1)
    assert until["sources"]["claude_api_calls_deduped"] == 1
    # The file counts are not windowed: the transcript still counts as having usage.
    assert until["sources"]["claude_files_with_usage"] == 1


# ------------------------------------------------------ duplicate results ---
def test_duplicate_results_counted_once_at_the_per_class_maximum(roots, tmp_path):
    proj = roots["CLAUDE_ROOT"] / PROJECT
    # One call written on three lines with growing usage; the last line is not
    # the largest in every class.
    write_jsonl(proj / "dup-a.jsonl", [
        assistant("msg_d", "req_d", (10, 1, 300, 0), session="dup-a"),
        assistant("msg_d", "req_d", (10, 40, 300, 0), session="dup-a"),
        assistant("msg_d", "req_d", (10, 90, 0, 2000), session="dup-a"),
        assistant("msg_e", "req_e", (3, 8, 0, 50), session="dup-a"),
    ])
    # A second transcript (a resumed session) repeats that key, and carries the
    # same message id under another request id.
    write_jsonl(proj / "dup-b.jsonl", [
        assistant("msg_d", "req_d", (12, 5, 0, 2500), session="dup-b"),
        assistant("msg_d", "req_other", (1, 2, 0, 0), session="dup-b"),
    ])
    report = run(tmp_path)

    # (msg_d, req_d): max(10,10,10,12)=12, max(1,40,90,5)=90, max(300,300,0,0)=300,
    # max(0,0,2000,2500)=2500 -- a usage no single line reported.
    # + (msg_e, req_e) 3/8/0/50 + (msg_d, req_other) 1/2/0/0
    assert four(report["grand_total"]) == (16, 100, 300, 2550, 2966)
    naive = (10 + 10 + 10 + 3 + 12 + 1, 1 + 40 + 90 + 8 + 5 + 2, 300 + 300, 2000 + 50 + 2500)
    assert naive == (46, 146, 600, 4550)
    assert four(report["grand_total"])[:4] != naive
    last_seen_wins = (10 + 3 + 1, 90 + 8 + 2, 0, 2000 + 50)
    assert four(report["grand_total"])[:4] != last_seen_wins

    assert report["sources"]["claude_files"] == 2
    assert report["sources"]["claude_files_with_usage"] == 2
    # Three distinct keys; the same message id with another request id is a call of its own.
    assert report["sources"]["claude_api_calls_deduped"] == 3
    # Only the key repeated across files is "dropped"; repeats inside one file are not counted here.
    assert report["sources"]["claude_cross_file_duplicate_keys_dropped"] == 1
    # The repeated call belongs to whichever transcript is listed first, so only
    # the sum over the two sessions is fixed.
    assert keys(report["top_sessions"]) == ["claude:dup-a", "claude:dup-b"]
    assert sum(r["total"] for r in report["top_sessions"]) == 2966
    assert sum(r["calls"] for r in report["top_sessions"]) == 3


def test_fleet_result_events_and_provider_sources(roots, tmp_path):
    s = "fleet-sess"
    usage = {"input_tokens": 5, "output_tokens": 6, "cache_creation_input_tokens": 7,
             "cache_read_input_tokens": 8}
    write_jsonl(roots["CLAUDE_ROOT"] / PROJECT / f"{s}.jsonl", [
        assistant("msg_f", "req_f", (5, 6, 7, 8), session=s, cwd="/Users/Dev/kalayantra/wt/k1")])
    result = {"type": "result", "subtype": "success", "session_id": s, "usage": usage}
    # A `claude -p` stream-json cycle log of the same session, its result event written twice.
    write_jsonl(roots["FLEET_LOGS"] / "k1.7.log", [
        {"type": "system", "subtype": "init", "session_id": s, "model": OPUS}, result, result])
    # A Codex exec cycle log: header and "tokens used" footer.
    (roots["FLEET_LOGS"] / "v2.3.log").write_text(
        "model: gpt-5.5\nreasoning effort: high\nsession id: cx-1\n--------\nwork\n"
        "tokens used\n12,345\n")
    (roots["FLEET_LOGS"] / "notes.log").write_text("not a cycle log\n")

    day = roots["CODEX_ROOT"] / "2026" / "10" / "11"
    count = lambda i, c, o, r: {"type": "event_msg", "payload": {"type": "token_count", "info": {  # noqa: E731
        "total_token_usage": {"input_tokens": i, "cached_input_tokens": c, "output_tokens": o,
                              "reasoning_output_tokens": r}}}}
    write_jsonl(day / "rollout-2026-10-11T09-00-00-cx-1.jsonl", [
        {"type": "session_meta", "payload": {"id": "cx-1", "cwd": "/Users/Dev/kalayantra/wt/v2",
                                             "timestamp": TS}},
        {"type": "turn_context", "payload": {"model": "gpt-5.5", "effort": "low"}},
        count(1000, 600, 50, 10),
        count(5000, 4200, 300, 120),          # cumulative: the last one is the session
    ])
    write_jsonl(day / "rollout-2026-10-11T09-30-00-cx-2.jsonl", [
        {"type": "session_meta", "payload": {"id": "cx-2", "cwd": "/Users/Dev/other-project",
                                             "timestamp": TS}},
        {"type": "turn_context", "payload": {"model": "gpt-5.5", "effort": "low"}},
        count(900000, 0, 900000, 0),
    ])
    report = run(tmp_path)

    assert report["sources"] == {
        "claude_files": 1, "claude_files_with_usage": 1, "codex_files_scanned": 2,
        "codex_madhav_sessions": 1, "fleet_logs": 2, "claude_api_calls_deduped": 1,
        "claude_cross_file_duplicate_keys_dropped": 0}
    assert keys(report["by_provider"]) == ["claude", "claude(fleet-stream-json)", "codex"]
    assert four(row(report["by_provider"], "claude")) == (5, 6, 7, 8, 26)
    # GAP (duplicate results): a result event repeated in a fleet stream-json log
    # is added once per line: 2 x (5, 6, 7, 8).
    assert four(row(report["by_provider"], "claude(fleet-stream-json)")) == (10, 12, 14, 16, 52)
    # codex: input 5000 - 4200 cached = 800 uncached, output 300, cache_read 4200
    assert four(row(report["by_provider"], "codex")) == (800, 300, 0, 4200, 5300)
    assert report["codex_reasoning_tokens_subset_of_output"] == 120
    # GAP (accounting ownership): the session's transcript and its fleet log are
    # both added: 26 + 52 + 5300.  Nothing checks that the log is uncovered.
    assert four(report["grand_total"]) == (815, 318, 21, 4224, 5378)

    assert keys(report["by_role"]) == ["KARAKA", "PARIKSAKA"]
    assert four(row(report["by_role"], "KARAKA")) == (15, 18, 21, 24, 78)
    assert four(row(report["by_role"], "PARIKSAKA")) == (800, 300, 0, 4200, 5300)
    assert keys(report["by_workspace"]) == ["kalayantra/k1", "kalayantra/v2"]
    assert row(report["by_model"], "gpt-5.5 (low)")["total"] == 5300

    fleet = report["fleet_cycle_logs"]["by_role"]
    assert sorted(fleet) == ["KARAKA", "PARIKSAKA"]
    assert (fleet["KARAKA"]["cycles"], fleet["KARAKA"]["claude_cycles"]) == (1, 1)
    assert fleet["KARAKA"]["claude_usage"] == {"input": 10, "output": 12, "cache_creation": 14,
                                               "cache_read": 16}
    # The Codex footer figure is reported beside the totals, never inside them.
    assert (fleet["PARIKSAKA"]["cycles"], fleet["PARIKSAKA"]["tokens_used"],
            fleet["PARIKSAKA"]["no_footer"]) == (1, 12345, 0)
    assert fleet["PARIKSAKA"]["models"] == {"gpt-5.5 (high)": 1}


# -------------------------------------------------------------- killed job --
def test_killed_job_transcript_cut_mid_line(roots, tmp_path):
    proj = roots["CLAUDE_ROOT"] / PROJECT
    cut = json.dumps(assistant("msg_cut", "req_cut", (1000, 1000, 1000, 1000), session="killed"))
    cut = cut[:len(cut) // 2]
    with pytest.raises(ValueError):
        json.loads(cut)
    write_jsonl(proj / "killed.jsonl", [
        assistant("msg_a", "req_a", (9, 11, 13, 17), session="killed"),
        assistant("msg_b", "req_b", (1, 2, 3, 4), session="killed"),
    ], tail=cut)
    # A job killed before its first whole line, and one killed before any byte.
    write_jsonl(proj / "killed-early.jsonl", [], tail=cut)
    write_jsonl(proj / "killed-empty.jsonl", [])
    report = run(tmp_path)

    assert four(report["grand_total"]) == (10, 13, 16, 21, 60)
    assert report["sources"] == {**ZERO_SOURCES, "claude_files": 3, "claude_files_with_usage": 1,
                                 "claude_api_calls_deduped": 2}
    assert keys(report["top_sessions"]) == ["claude:killed"]
    assert report["top_sessions"][0]["calls"] == 2
    # GAP (killed job): the cut call is dropped without a trace; the report
    # holds no marker that a transcript ended mid-line.
    assert "msg_cut" not in json.dumps(report)
    assert "killed-early" not in json.dumps(report)


# ---------------------------------------------------- parent/child sessions -
def test_parent_and_child_sessions(roots, tmp_path):
    proj = roots["CLAUDE_ROOT"] / PROJECT
    s = "sess-pc"
    write_jsonl(proj / f"{s}.jsonl", [
        prompt(s),
        assistant("msg_p1", "req_p1", (10, 20, 30, 40), session=s),
        prompt(s),
        assistant("msg_p2", "req_p2", (1, 2, 3, 4), session=s),
    ])
    # The child carries no isSidechain flag: the /subagents/ path alone marks it.
    write_jsonl(proj / s / "subagents" / "agent-a1.jsonl", [
        prompt(s),
        assistant("msg_c1", "req_c1", (100, 200, 300, 400), session=s),
        assistant("msg_c2", "req_c2", (5, 6, 7, 8), session=s),
    ])
    # A child whose parent transcript is missing.
    write_jsonl(proj / "sess-orphan" / "subagents" / "agent-b1.jsonl", [
        assistant("msg_o1", "req_o1", (2, 3, 5, 7), session="sess-orphan", isSidechain=True)])
    report = run(tmp_path)

    parent = (11, 22, 33, 44, 110)
    child = (105, 206, 307, 408, 1026)
    orphan = (2, 3, 5, 7, 17)
    # GAP (parent/child): child usage is added to parent usage unconditionally;
    # nothing proves the parent's usage does not already include it.
    assert four(report["grand_total"]) == (118, 231, 345, 459, 1153)
    assert 1153 == parent[4] + child[4] + orphan[4]
    assert report["sources"]["claude_api_calls_deduped"] == 5
    assert report["sources"]["claude_files"] == 3

    # The child's tokens go to the role "subagent" ...
    assert keys(report["by_role"]) == ["interactive", "subagent"]
    assert four(row(report["by_role"], "interactive")) == parent
    assert four(row(report["by_role"], "subagent")) == (107, 209, 312, 415, 1043)
    assert 1043 == child[4] + orphan[4]
    assert keys(report["by_model_role"]) == [f"{OPUS} | interactive", f"{OPUS} | subagent"]

    # ... but it has no session row of its own: parent and child are one session,
    # labelled by the transcript listed first (the parent's directory is listed
    # before the directories under it).
    assert keys(report["top_sessions"]) == ["claude:sess-orphan", "claude:sess-pc"]
    merged = row(report["top_sessions"], "claude:sess-pc")
    assert four(merged) == (116, 228, 340, 452, 1136)
    assert (merged["role"], merged["subagent_files"], merged["calls"], merged["turns"]) == (
        "interactive", 1, 4, 2)
    alone = row(report["top_sessions"], "claude:sess-orphan")
    assert four(alone) == orphan
    assert (alone["role"], alone["subagent_files"], alone["calls"], alone["turns"]) == (
        "subagent", 1, 1, 0)


# ------------------------- interactive planner/conductor; bootstrap jobs ----
def test_planner_conductor_and_bootstrap_labels(roots, tmp_path):
    croot = roots["CLAUDE_ROOT"]
    enc = lambda cwd: cwd.replace("/", "-").replace(".", "-")  # noqa: E731
    write_jsonl(croot / enc(PLANNER_CWD) / "planner.jsonl", [
        assistant("msg_pl", "req_pl", (1, 10, 100, 1000), session="planner", cwd=PLANNER_CWD,
                  branch="kalayantra/relaunch-plan")])
    write_jsonl(croot / enc(CAMPAIGN_CWD) / "conductor.jsonl", [
        assistant("msg_co", "req_co", (2, 20, 200, 2000), session="conductor", cwd=CAMPAIGN_CWD,
                  branch="kalayantra/campaign")])
    write_jsonl(croot / enc(BOOTSTRAP_CWD) / "bootstrap.jsonl", [
        assistant("msg_bs", "req_bs", (4, 40, 400, 4000), session="bootstrap", cwd=BOOTSTRAP_CWD,
                  branch="kalayantra/kv3-b-baseline")])
    write_jsonl(croot / enc(BOOTSTRAP_CWD) / "bootstrap" / "subagents" / "agent-x.jsonl", [
        assistant("msg_bx", "req_bx", (16, 160, 1600, 16000), session="bootstrap", cwd=BOOTSTRAP_CWD,
                  branch="kalayantra/kv3-b-baseline", isSidechain=True)])
    write_jsonl(croot / enc(LEGACY_CAMPAIGN_CWD) / "legacy.jsonl", [
        assistant("msg_lg", "req_lg", (8, 80, 800, 8000), session="legacy", cwd=LEGACY_CAMPAIGN_CWD,
                  branch="HEAD")])
    report = run(tmp_path)

    assert four(report["grand_total"]) == (31, 310, 3100, 31000, 34441)
    assert report["sources"]["claude_api_calls_deduped"] == 5

    # GAP (interactive planner/conductor sessions; bootstrap jobs): every checkout
    # whose path holds "/kalayantra" -- the relaunch-plan checkout, the campaign
    # checkout and a bootstrap worktree alike -- is one workspace and one role.
    assert tb.workspace_of(PLANNER_CWD) == "kalayantra/root"
    assert tb.workspace_of(CAMPAIGN_CWD) == "kalayantra/root"
    assert tb.workspace_of(BOOTSTRAP_CWD) == "kalayantra/root"
    assert tb.workspace_of(LEGACY_CAMPAIGN_CWD) == "kalayantra/campaign"
    assert keys(report["by_workspace"]) == ["kalayantra/campaign", "kalayantra/root"]
    # planner 1111 + conductor 2222 + bootstrap 4444 + the bootstrap job's subagent 17776
    assert four(row(report["by_workspace"], "kalayantra/root")) == (23, 230, 2300, 23000, 25553)
    assert four(row(report["by_workspace"], "kalayantra/campaign")) == (8, 80, 800, 8000, 8888)
    # GAP: in a kalayantra workspace a subagent transcript takes the workspace's
    # role; there is no "subagent" row.
    assert keys(report["by_role"]) == ["interactive(kalayantra-campaign)", "interactive(kalayantra-root)"]
    assert four(row(report["by_role"], "interactive(kalayantra-root)")) == (23, 230, 2300, 23000, 25553)
    assert four(row(report["by_role"], "interactive(kalayantra-campaign)")) == (8, 80, 800, 8000, 8888)

    # Only the branch of a top-session row tells the three apart.
    seen = {r["key"]: (r["workspace"], r["role"], r["branch"], r["subagent_files"], r["total"])
            for r in report["top_sessions"]}
    assert seen == {
        "claude:planner": ("kalayantra/root", "interactive(kalayantra-root)",
                           "kalayantra/relaunch-plan", 0, 1111),
        "claude:conductor": ("kalayantra/root", "interactive(kalayantra-root)",
                             "kalayantra/campaign", 0, 2222),
        "claude:bootstrap": ("kalayantra/root", "interactive(kalayantra-root)",
                             "kalayantra/kv3-b-baseline", 1, 22220),
        "claude:legacy": ("kalayantra/campaign", "interactive(kalayantra-campaign)", "HEAD", 0, 8888),
    }


def test_workspace_and_role_labels_of_other_checkouts(roots):
    labels = {cwd: (tb.workspace_of(cwd), tb.role_of(tb.workspace_of(cwd), False),
                    tb.role_of(tb.workspace_of(cwd), True)) for cwd in (
        "/Users/Dev/kalayantra/wt/k3", "/Users/Dev/kalayantra/wt/v1",
        "/Users/Dev/kalayantra/wt/adhikarin", "/Users/Dev/kalayantra/wt/sutradhara",
        "/Users/Dev/kalayantra", "/Users/Dev/worktrees.noindex/madhav/claude/pravaha-x",
        SHARED_CWD, SHARED_CWD + "/platform/src", "")}
    assert labels == {
        "/Users/Dev/kalayantra/wt/k3": ("kalayantra/k3", "KARAKA", "KARAKA"),
        "/Users/Dev/kalayantra/wt/v1": ("kalayantra/v1", "PARIKSAKA", "PARIKSAKA"),
        "/Users/Dev/kalayantra/wt/adhikarin": ("kalayantra/adhikarin", "ADHIKARIN", "ADHIKARIN"),
        "/Users/Dev/kalayantra/wt/sutradhara": ("kalayantra/sutradhara", "SUTRADHARA", "SUTRADHARA"),
        "/Users/Dev/kalayantra": ("kalayantra/root", "interactive(kalayantra-root)",
                                  "interactive(kalayantra-root)"),
        "/Users/Dev/worktrees.noindex/madhav/claude/pravaha-x": ("wt.noindex/pravaha-x", "interactive",
                                                                "subagent"),
        SHARED_CWD: ("shared-checkout", "interactive", "subagent"),
        SHARED_CWD + "/platform/src": ("shared-checkout/platform", "interactive", "subagent"),
        "": ("?", "interactive", "subagent"),
    }


# ---------------------------------------------------------- missing records -
def assert_reports_nothing(report):
    assert report["sources"] == ZERO_SOURCES
    # GAP (missing records): no source and no coverage is reported as zero, not unknown.
    assert four(report["grand_total"]) == (0, 0, 0, 0, 0)
    assert report["shares"] == {"cache_read_share": 0.0, "output_share": 0.0}
    for table in ("by_provider", "by_role", "by_model", "by_workspace", "by_day", "by_week",
                  "top_sessions"):
        assert report[table] == [], table
    assert report["claude_first_day"] is None
    assert report["fleet_cycle_logs"]["by_role"] == {}


def test_missing_records_empty_roots(roots, tmp_path):
    for d in roots.values():
        assert list(d.iterdir()) == []
    assert_reports_nothing(run(tmp_path))


def test_missing_records_roots_that_do_not_exist(roots, tmp_path, monkeypatch):
    for name in ROOT_NAMES:
        gone = tmp_path / "absent" / name.lower()
        assert not gone.exists()
        monkeypatch.setattr(tb, name, str(gone))
    # An absent root and an empty root give the same report, exit status 0.
    assert_reports_nothing(run(tmp_path))


def test_missing_records_inside_a_transcript(roots, tmp_path):
    s = "sess-partial"
    no_id = assistant(None, "req_n", (1000, 1000, 1000, 1000), session=s)
    no_ts = assistant("msg_t", "req_t", (7, 7, 7, 7), session=s)
    del no_ts["timestamp"]
    nulls = assistant("msg_u", "req_u", (0, 5, 0, 0), session=s)
    nulls["message"]["usage"] = {"input_tokens": None, "output_tokens": 5}
    empty = assistant("msg_v", "req_v", (0, 0, 0, 0), session=s)
    empty["message"]["usage"] = {}
    write_jsonl(roots["CLAUDE_ROOT"] / PROJECT / f"{s}.jsonl", [no_id, no_ts, nulls, empty])
    report = run(tmp_path)

    # GAP (missing records): a usage record without a message id, and a call
    # without a timestamp, are left out of every total without a trace.
    assert four(report["grand_total"]) == (0, 5, 0, 0, 5)
    assert report["sources"]["claude_api_calls_deduped"] == 1
    assert report["sources"]["claude_files_with_usage"] == 1


def test_a_session_outside_the_top_twenty_has_no_row(roots, tmp_path):
    proj = roots["CLAUDE_ROOT"] / PROJECT
    for n in range(1, 22):
        write_jsonl(proj / f"cap-{n:02d}.jsonl", [
            assistant(f"msg_{n}", f"req_{n}", (0, n, 0, 0), session=f"cap-{n:02d}")])
    report = run(tmp_path)

    # output 1 + 2 + ... + 21
    assert four(report["grand_total"]) == (0, 231, 0, 0, 231)
    assert report["sources"]["claude_api_calls_deduped"] == 21
    assert [r["key"] for r in report["top_sessions"]] == [f"claude:cap-{n:02d}" for n in range(21, 1, -1)]
    assert sum(r["total"] for r in report["top_sessions"]) == 230
    # GAP (coverage): the twenty-first session is in the totals but named nowhere
    # in the report, so the report cannot show that a given session was covered.
    assert "cap-01" not in json.dumps(report)
