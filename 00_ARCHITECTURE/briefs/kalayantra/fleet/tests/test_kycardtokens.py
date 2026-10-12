"""B-0c: a card's size is a measured token count bound to its bytes — never a byte proxy."""
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent

FAKE = r'''#!/usr/bin/env python3
import json, os, sys
cfg = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "fake.json")))
if sys.argv[1:] == ["--version"]:
    print(cfg["version"] + " (Claude Code)"); sys.exit(0)
prompt = sys.stdin.read()
if "BROKEN" in prompt and cfg["break_marked"]:
    print(json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True})); sys.exit(1)
print(json.dumps({"type": "system", "subtype": "init", "session_id": "s", "model": "claude-opus-5-5"}))
print(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "OK"}]}}))
print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 1,
                  "usage": {"input_tokens": 1000 + len(prompt.split()) * cfg["tokens_per_word"],
                            "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 1}}))
'''


@pytest.fixture()
def rig(tmp_path):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "SMALL.md").write_text("word " * 100)
    (cards / "BIG.md").write_text("word " * 400)
    (cards / "COVERAGE_X.md").write_text("word " * 5000)          # a table, never sent to a job
    fake = tmp_path / "claude"
    fake.write_text(FAKE)
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    mcp = tmp_path / "mcp.none.json"
    mcp.write_text('{"mcpServers":{}}\n')
    record = cards / "TOKEN_MEASUREMENT.json"

    def configure(**over):
        (tmp_path / "fake.json").write_text(json.dumps(dict({"version": "2.1.296", "tokens_per_word": 4, "break_marked": False}, **over)))

    def cli(*args):
        return subprocess.run([sys.executable, "-B", str(FLEET / "kycardtokens.py")] + [str(a) for a in args],
                              capture_output=True, text=True, timeout=120,
                              env={"HOME": str(tmp_path), "USER": "t", "PATH": "/opt/homebrew/bin:/usr/bin:/bin"})

    def measure(n=1):
        return cli("measure", "--cards-dir", cards, "--out", record, "--scratch", tmp_path / ("scratch%d" % n),
                   "--claude-bin", fake, "--mcp-config", mcp, "--add-dir", tmp_path)

    configure()
    return type("Rig", (), dict(cards=cards, record=record, configure=staticmethod(configure), cli=staticmethod(cli),
                                measure=staticmethod(measure), tmp=tmp_path))


def test_measures_by_difference_and_refuses_the_card_over_the_cap(rig):
    r = rig.measure()
    doc = json.loads(rig.record.read_text())
    assert doc["cards"]["SMALL.md"]["tokens"] == 400 and doc["cards"]["BIG.md"]["tokens"] == 1600
    assert "COVERAGE_X.md" not in doc["cards"]
    assert r.returncode == 1 and "BIG.md: 1600 tokens exceeds the cap of 1500" in r.stderr


def test_check_passes_only_for_measured_unchanged_cards_under_the_cap(rig):
    rig.configure(tokens_per_word=3)
    assert rig.measure().returncode == 0
    assert rig.cli("check", "--cards-dir", rig.cards, "--record", rig.record).returncode == 0
    (rig.cards / "SMALL.md").write_text("word " * 101)
    r = rig.cli("check", "--cards-dir", rig.cards, "--record", rig.record)
    assert r.returncode == 1 and "SMALL.md: changed since it was measured" in r.stderr
    (rig.cards / "NEW.md").write_text("x")
    assert "NEW.md: never measured" in rig.cli("check", "--cards-dir", rig.cards, "--record", rig.record).stderr
    rig.record.unlink()
    assert "missing or unreadable" in rig.cli("check", "--cards-dir", rig.cards, "--record", rig.record).stderr


def test_a_count_below_one_is_not_a_measurement(rig):
    rig.configure(tokens_per_word=3)
    assert rig.measure().returncode == 0
    doc = json.loads(rig.record.read_text())
    for bad in (0, -5, True):
        doc["cards"]["SMALL.md"]["tokens"] = bad
        rig.record.write_text(json.dumps(doc))
        r = rig.cli("check", "--cards-dir", rig.cards, "--record", rig.record)
        assert r.returncode == 1 and "SMALL.md: tokens unknown" in r.stderr, bad


def test_a_failed_run_is_unknown_never_a_number(rig):
    rig.configure(tokens_per_word=3, break_marked=True)
    (rig.cards / "SMALL.md").write_text("BROKEN " * 10)
    r = rig.measure()
    assert json.loads(rig.record.read_text())["cards"]["SMALL.md"]["tokens"] == "unknown"
    assert r.returncode == 1 and "SMALL.md: tokens unknown" in r.stderr


def test_refuses_an_old_program_and_a_reused_scratch(rig):
    rig.configure(version="2.1.239")
    assert rig.measure().returncode == 70
    rig.configure(tokens_per_word=3)
    assert rig.measure(2).returncode == 0
    assert rig.measure(2).returncode == 73
