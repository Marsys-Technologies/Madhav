"""Every scorer test runs with the ledgers redirected into a temporary directory (SUR-RB-45/46, review VERIFY3):
the canonical run ledger, its quarantine, the decisions ledger and the real-input-hash file. No test can write to,
or read from, the real ledger locations."""

from __future__ import annotations

import json

import pytest

from services.rulebook.scorer import config as C

from ._toy import ledger_lines


@pytest.fixture(autouse=True)
def _ledgers_in_tmp(tmp_path_factory, monkeypatch):
    base = tmp_path_factory.mktemp("ledgers")
    eng = base / "10_engine"
    eng.mkdir()
    (eng / "run-ledger-quarantine").mkdir()
    dec = base / "DECISIONS_SURROGATE.jsonl"
    dec.write_text("\n".join(json.dumps(r) for r in ledger_lines()) + "\n")
    monkeypatch.setattr(C, "LEDGER_DIR", str(eng / "run-ledger"))
    monkeypatch.setattr(C, "LEDGER_QUARANTINE_DIR", str(eng / "run-ledger-quarantine"))
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(dec))
    monkeypatch.setattr(C, "REAL_INPUT_HASHES_PATH", str(eng / "run-ledger-real-input-hashes.json"))
    yield
