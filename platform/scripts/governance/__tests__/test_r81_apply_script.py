"""test_r81_apply_script.py — proves apply_r80_r81_ledger_migration.py end to end, against a copy.

This is the last proof before R81's real, single authorized write to
`00_ARCHITECTURE/control/asset_gaps.jsonl`: the exact script that will run against the real file
is run here against a temp COPY only (`tmp_path`, never the real path), through its actual CLI
entry point (`main()`), covering: dry-run writes nothing; apply is atomic and produces the
documented line-count delta; a second apply is a true no-op (idempotency, live, not just the
underlying function in isolation); every line — including the untouched originals — still parses
as JSON afterward; and no line between the schema row and the appended rows is altered.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REAL_LEDGER = HERE.parents[3] / "00_ARCHITECTURE/control/asset_gaps.jsonl"
SCRIPT = HERE.parent / "apply_r80_r81_ledger_migration.py"

spec = importlib.util.spec_from_file_location("apply_r80_r81_ledger_migration", SCRIPT)
apply_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply_mod)


def _copy_real_ledger_to(tmp_path: pathlib.Path) -> pathlib.Path:
    dest = tmp_path / "asset_gaps.jsonl"
    dest.write_bytes(REAL_LEDGER.read_bytes())
    return dest


def test_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
    copy = _copy_real_ledger_to(tmp_path)
    before = copy.read_bytes()
    monkeypatch.setattr(sys, "argv", ["apply_r80_r81_ledger_migration.py", "--ledger", str(copy)])
    rc = apply_mod.main()
    assert rc == 0
    assert copy.read_bytes() == before, "a dry run (no --apply) must never write the ledger"
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "27 new row(s)" in out


def test_apply_then_reapply_is_idempotent(tmp_path, monkeypatch, capsys):
    copy = _copy_real_ledger_to(tmp_path)
    before_lines = copy.read_text(encoding="utf-8").splitlines()
    before_count = len(before_lines)

    monkeypatch.setattr(sys, "argv", ["apply_r80_r81_ledger_migration.py", "--ledger", str(copy), "--apply"])
    rc1 = apply_mod.main()
    assert rc1 == 0
    after_first = copy.read_text(encoding="utf-8").splitlines()
    assert len(after_first) == before_count + 27

    rc2 = apply_mod.main()
    assert rc2 == 0
    after_second = copy.read_text(encoding="utf-8").splitlines()
    assert after_second == after_first, "a second --apply must be a byte-for-byte no-op"
    out = capsys.readouterr().out
    assert "0 line(s) added" in out


def test_every_line_still_parses_and_originals_are_preserved_verbatim(tmp_path, monkeypatch):
    copy = _copy_real_ledger_to(tmp_path)
    before_lines = copy.read_text(encoding="utf-8").splitlines()

    monkeypatch.setattr(sys, "argv", ["apply_r80_r81_ledger_migration.py", "--ledger", str(copy), "--apply"])
    apply_mod.main()

    after_lines = copy.read_text(encoding="utf-8").splitlines()
    for ln in after_lines:
        json.loads(ln)  # every line, including every appended one, is valid JSON

    # Lines 2..830 (0-indexed 1..829) are untouched originals — byte-identical, in order.
    assert after_lines[1:len(before_lines)] == before_lines[1:]
    # Line 1 (the schema row) changed; every appended line is new.
    assert after_lines[0] != before_lines[0]
    assert "superseded_by" in after_lines[0]


def test_refuses_to_write_when_line_one_is_not_the_schema_row(tmp_path, monkeypatch, capsys):
    bad = tmp_path / "asset_gaps.jsonl"
    bad.write_text('{"asset": "bg_x", "gap_id": "bg_x-Foo"}\n', encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["apply_r80_r81_ledger_migration.py", "--ledger", str(bad), "--apply"])
    rc = apply_mod.main()
    assert rc == 2
    err = capsys.readouterr().err
    assert "REFUSED" in err
    assert bad.read_text(encoding="utf-8") == '{"asset": "bg_x", "gap_id": "bg_x-Foo"}\n'
