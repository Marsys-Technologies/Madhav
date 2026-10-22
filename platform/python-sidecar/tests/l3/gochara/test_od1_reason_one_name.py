"""SR-REASON-ONE-NAME (DECISIONS_SURROGATE 2026-10-22, madhav-44): ONE name for "the stored dasha table ends before the support", on both paths.

Claims: (1) the P1 table-end blank (`dasha_read.PERIOD_TABLE_ENDS_REASON`, written by record_store, counted by ka_gochara_v5) is spelled
`dasha_horizon_exhausted`, the identical string the legacy permission path uses (main PR #3873, SR-MUDDA-HORIZON); (2) the first spelling never reappears
anywhere under platform/python-sidecar; (3) no second `dasha_*` reason string for the same condition exists in production code.

Planted reversion (the ONE for this ruling): restore the first spelling as the value of `PERIOD_TABLE_ENDS_REASON` -> claims (1) and (2) fail.
Detector: the real constant, a byte scan of the real tree, and an AST scan of the real production modules (nothing faked). The first spelling is built from
parts so this file itself never carries it.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from services.gochara_kernel import dasha_read

ONE_NAME = "dasha_horizon_exhausted"
OLD_NAME = "dasha_table_ends" + "_before_support"
SIDECAR = Path(__file__).resolve().parents[3]
TEXT_SUFFIXES = {".py", ".sql", ".json", ".yml", ".yaml", ".md", ".txt", ".ts", ".toml", ".cfg", ".ini"}
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "node_modules"}
#: a string constant that names the "dasha table / horizon ran out" condition, whatever its spelling
SAME_CONDITION = re.compile(r"^dasha_[a-z_]*(horizon|table_end|ends_before|exhaust)[a-z_]*$")


def _files(suffixes):
    return [p for p in SIDECAR.rglob("*") if p.is_file() and p.suffix in suffixes and not (set(p.relative_to(SIDECAR).parts) & SKIP_DIRS)]


def test_period_table_end_reason_is_the_one_name():
    assert dasha_read.PERIOD_TABLE_ENDS_REASON == ONE_NAME


def test_first_spelling_appears_nowhere_under_the_sidecar():
    files = _files(TEXT_SUFFIXES)
    assert files, "the scan found no files: the detector would read green on an empty tree"
    hits = [str(p.relative_to(SIDECAR)) for p in files if OLD_NAME in p.read_text(encoding="utf-8", errors="replace")]
    assert hits == [], f"the first spelling is back in {hits}"


def test_one_string_names_the_condition_in_production_code():
    prod = [p for p in _files({".py"}) if p.relative_to(SIDECAR).parts[0] != "tests"]
    assert any(p.name == "dasha_read.py" for p in prod), "the scan must cover the module that owns the constant"
    found: dict[str, list[str]] = {}
    for p in prod:
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"), filename=str(p))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and SAME_CONDITION.match(node.value):
                found.setdefault(node.value, []).append(f"{p.relative_to(SIDECAR)}:{node.lineno}")
    assert set(found) == {ONE_NAME}, f"two or more strings name the dasha-horizon condition: {found}"
