"""test_r81_apply_script.py — proves apply_r80_r81_ledger_migration.py end to end, against a copy.

This ran once as the last proof before R81's real, single authorized write to
`00_ARCHITECTURE/control/asset_gaps.jsonl` (that write has since landed — see the confirmation
test at the bottom of this file). The exact script that ran against the real file is exercised
here against a synthetic, FROZEN pre-migration ledger (`_r81_pre_migration_fixture`, built fresh
in `tmp_path` — never the real path, and never depending on the real file's current, post-
migration state), through its actual CLI entry point (`main()`), covering: dry-run writes nothing;
apply is atomic and produces the documented line-count delta; a second apply is a true no-op
(idempotency, live, not just the underlying function in isolation); every line — including the
untouched originals — still parses as JSON afterward; and no line between the schema row and the
appended rows is altered.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REAL_LEDGER = HERE.parents[3] / "00_ARCHITECTURE/control/asset_gaps.jsonl"
SCRIPT = HERE.parent / "apply_r80_r81_ledger_migration.py"

sys.path.insert(0, str(HERE))
import _r81_pre_migration_fixture as fx  # noqa: E402

spec = importlib.util.spec_from_file_location("apply_r80_r81_ledger_migration", SCRIPT)
apply_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply_mod)


def _write_pre_migration_ledger(tmp_path: pathlib.Path) -> pathlib.Path:
    """A synthetic ledger containing the frozen pre-migration schema row + the 11 pairs' real
    (pre-migration) hand/census rows — enough for the apply script to run its real logic against,
    without depending on the real file's mutable, now-migrated current state."""
    dest = tmp_path / "asset_gaps.jsonl"
    lines = [json.dumps(fx.PRE_MIGRATION_SCHEMA_ROW, ensure_ascii=False)]
    lines += [json.dumps(r, ensure_ascii=False) for r in fx.ROWS]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def test_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
    copy = _write_pre_migration_ledger(tmp_path)
    before = copy.read_bytes()
    monkeypatch.setattr(sys, "argv", ["apply_r80_r81_ledger_migration.py", "--ledger", str(copy)])
    rc = apply_mod.main()
    assert rc == 0
    assert copy.read_bytes() == before, "a dry run (no --apply) must never write the ledger"
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "27 new row(s)" in out


def test_apply_then_reapply_is_idempotent(tmp_path, monkeypatch, capsys):
    copy = _write_pre_migration_ledger(tmp_path)
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
    copy = _write_pre_migration_ledger(tmp_path)
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


def test_real_ledger_is_confirmed_already_migrated_dry_run_only(monkeypatch, capsys):
    """Post-migration confirmation, dry-run only (--apply is never passed here — this test must
    never be able to write the real file): running the script against the REAL, now-migrated
    ledger reports 0 new rows and no schema change, live."""
    monkeypatch.setattr(sys, "argv", ["apply_r80_r81_ledger_migration.py", "--ledger", str(REAL_LEDGER)])
    before = REAL_LEDGER.read_bytes()
    rc = apply_mod.main()
    assert rc == 0
    assert REAL_LEDGER.read_bytes() == before, "a dry run must never write the real ledger"
    out = capsys.readouterr().out
    assert "R81 fold: 0 new row(s) to append" in out
    assert "already migrated" in out
