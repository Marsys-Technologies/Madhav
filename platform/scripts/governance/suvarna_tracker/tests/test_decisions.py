"""Fix 1: the authoritative decisions log — validation, append-only + flock, latest-per-id reads,
the one-off seed from the old-format log, and the mirror-to-committed-copy helper."""
import json
import os
import threading

import pytest

from suvarna_tracker import decisions as DEC


def test_valid_decided_record_round_trips(tmp_path):
    p = str(tmp_path / "DECISIONS.jsonl")
    rec = DEC.append_decision(p, {"id": "N-1", "state": "decided", "writer": "strategic-suvarna",
                                  "source": "Native, session 'X', 2026-09-29: 'yes'",
                                  "detail": "approved"})
    assert rec["id"] == "N-1" and rec["ts"] and rec["decided_on"]
    log = DEC.load_decisions(p)
    assert log["latest"]["N-1"]["detail"] == "approved" and log["malformed"] == 0


def test_first_write_gets_a_schema_header(tmp_path):
    p = str(tmp_path / "DECISIONS.jsonl")
    DEC.append_decision(p, {"id": "N-1", "state": "decided", "writer": "steward",
                            "source": "Native, session 'X', 2026-09-29: 'yes'", "detail": "approved"})
    with open(p, encoding="utf-8") as f:
        first = json.loads(f.readline())
    assert first.get("_schema") == "suvarna.decisions.v1"


@pytest.mark.parametrize("rec,msg_part", [
    ({"state": "decided", "writer": "steward", "source": "x" * 20, "detail": "d"}, "id"),
    ({"id": "N-1", "state": "nope", "writer": "steward", "source": "x" * 20, "detail": "d"}, "state"),
    ({"id": "N-1", "state": "decided", "writer": "steward", "source": "short", "detail": "d"}, "source"),
    ({"id": "N-1", "state": "decided", "writer": "steward", "source": "x" * 20, "detail": ""}, "detail"),
    ({"id": "N-1", "state": "decided", "writer": "nobody", "source": "x" * 20, "detail": "d"}, "writer"),
])
def test_invalid_records_rejected(rec, msg_part):
    with pytest.raises(DEC.DecisionError, match=msg_part):
        DEC.validate(rec)


def test_latest_line_wins_per_id(tmp_path):
    p = str(tmp_path / "DECISIONS.jsonl")
    DEC.append_decision(p, {"id": "N-1", "state": "decided", "writer": "steward",
                            "source": "Native, session 'X', 2026-09-29: 'first'", "detail": "first ruling"})
    DEC.append_decision(p, {"id": "N-1", "state": "revoked", "writer": "strategic-suvarna",
                            "source": "Native, session 'X', 2026-09-29: 'revoke it'", "detail": "revoked, changed my mind"})
    log = DEC.load_decisions(p)
    assert log["latest"]["N-1"]["state"] == "revoked" and log["latest"]["N-1"]["detail"] == "revoked, changed my mind"


def test_reader_is_tolerant_of_malformed_lines(tmp_path):
    p = str(tmp_path / "DECISIONS.jsonl")
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(DEC.SCHEMA_LINE) + "\n")
        f.write("{not json}\n")
        f.write(json.dumps({"id": "N-1", "state": "not-a-state", "detail": "x"}) + "\n")  # bad state
        f.write(json.dumps({"id": "N-2", "state": "decided", "writer": "steward",
                            "source": "Native: yes", "detail": "ok", "ts": "2026-09-29T00:00:00+00:00"}) + "\n")
    log = DEC.load_decisions(p)
    assert log["malformed"] == 2 and set(log["latest"]) == {"N-2"}


def test_load_missing_file_is_empty_not_fatal(tmp_path):
    log = DEC.load_decisions(str(tmp_path / "nope.jsonl"))
    assert log == {"latest": {}, "malformed": 0}


def test_concurrent_appends_never_interleave(tmp_path):
    p = str(tmp_path / "DECISIONS.jsonl")

    def writer(n):
        for i in range(20):
            DEC.append_decision(p, {"id": f"N-{n}-{i}", "state": "decided", "writer": "steward",
                                    "source": "Native, session 'X', 2026-09-29: 'ok'" + "x" * 200,
                                    "detail": "d" * 200})

    ts = [threading.Thread(target=writer, args=(n,)) for n in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    log = DEC.load_decisions(p)
    assert log["malformed"] == 0
    assert len(log["latest"]) == 120


# ---- seed_from ---------------------------------------------------------------------------------

OLD_LOG = (
    json.dumps({"_schema": "suvarna.decisions.v1", "fields": ["id"]}) + "\n"
    + json.dumps({"id": "N-2", "state": "decided", "decided_on": "2026-09-28",
                  "source": "Native, session 'X': 'yes'", "detail": "approved"}) + "\n"
    + json.dumps({"id": "F-2", "state": "delegated", "decided_on": "2026-09-29",
                  "source": "Native, session 'X' (N-17)", "detail": "delegated to Y"}) + "\n"
)


def test_seed_from_copies_records_and_fills_missing_writer(tmp_path):
    src = tmp_path / "old.jsonl"
    src.write_text(OLD_LOG)
    dest = str(tmp_path / "DECISIONS.jsonl")
    result = DEC.seed_from(str(src), dest)
    assert result["copied"] == 2
    log = DEC.load_decisions(dest)
    assert set(log["latest"]) == {"N-2", "F-2"}
    assert log["latest"]["N-2"]["writer"] == "strategic-suvarna"
    assert log["latest"]["N-2"]["decided_on"] == "2026-09-28"  # kept from the source, not overwritten


def test_seed_from_refuses_when_target_already_has_records(tmp_path):
    src = tmp_path / "old.jsonl"
    src.write_text(OLD_LOG)
    dest = str(tmp_path / "DECISIONS.jsonl")
    DEC.append_decision(dest, {"id": "N-9", "state": "decided", "writer": "steward",
                               "source": "Native, session 'X', 2026-09-29: 'existing'", "detail": "existing"})
    with pytest.raises(DEC.DecisionError, match="already has"):
        DEC.seed_from(str(src), dest)
    # target untouched beyond the pre-existing record
    log = DEC.load_decisions(dest)
    assert set(log["latest"]) == {"N-9"}


# ---- mirror_to ----------------------------------------------------------------------------------

def test_mirror_to_writes_atomically_and_matches_source(tmp_path):
    src = str(tmp_path / "DECISIONS.jsonl")
    DEC.append_decision(src, {"id": "N-1", "state": "decided", "writer": "steward",
                              "source": "Native, session 'X', 2026-09-29: 'yes'", "detail": "approved"})
    dest = str(tmp_path / "mirror" / "DECISIONS.jsonl")
    result = DEC.mirror_to(src, dest)
    assert os.path.exists(dest)
    with open(src, "rb") as f:
        assert f.read() == open(dest, "rb").read()
    assert result["bytes"] > 0
    # no stray tmp file left behind
    assert not any(n.startswith("DECISIONS.jsonl.tmp.") for n in os.listdir(os.path.dirname(dest)))


def test_mirror_to_missing_source_writes_empty_file(tmp_path):
    dest = str(tmp_path / "mirror.jsonl")
    result = DEC.mirror_to(str(tmp_path / "nope.jsonl"), dest)
    assert result["bytes"] == 0 and os.path.exists(dest)


# ---- CLI ------------------------------------------------------------------------------------------

def test_cli_append_writes_and_prints(tmp_path, capsys):
    p = str(tmp_path / "DECISIONS.jsonl")
    rc = DEC.main(["--path", p, "--id", "N-5", "--state", "decided", "--writer", "steward",
                  "--source", "Native, session 'X', 2026-09-29: 'ok'", "--detail", "approved"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["id"] == "N-5"
    assert DEC.load_decisions(p)["latest"]["N-5"]["state"] == "decided"


def test_cli_rejects_missing_required_args(tmp_path, capsys):
    p = str(tmp_path / "DECISIONS.jsonl")
    rc = DEC.main(["--path", p, "--id", "N-5", "--state", "decided"])
    assert rc == 2
    assert "missing required arguments" in capsys.readouterr().err


def test_cli_seed_from(tmp_path, capsys):
    src = tmp_path / "old.jsonl"
    src.write_text(OLD_LOG)
    p = str(tmp_path / "DECISIONS.jsonl")
    rc = DEC.main(["--path", p, "--seed-from", str(src)])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["copied"] == 2


def test_cli_mirror_to(tmp_path, capsys):
    p = str(tmp_path / "DECISIONS.jsonl")
    DEC.append_decision(p, {"id": "N-1", "state": "decided", "writer": "steward",
                            "source": "Native, session 'X', 2026-09-29: 'ok'", "detail": "approved"})
    dest = str(tmp_path / "mirror.jsonl")
    rc = DEC.main(["--path", p, "--mirror-to", dest])
    assert rc == 0
    assert os.path.exists(dest)
