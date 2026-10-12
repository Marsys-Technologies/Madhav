"""Offline comparison oracles for the K8 documentation snapshot; no DB/imports."""

import ast
import os
from pathlib import Path
import re
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[4]
DOC = Path(os.environ.get("K8_GATE_TABLE_DOC", Path(__file__).with_name("K8_GATE_TABLE_R26_v1_0.md")))
SOURCE = "platform/scripts/governance/asset_census.py"
GATES = ("Ldgr", "Idem", "Earn", "Null", "Vocab", "Carr", "Narr", "Dens", "Build")
SNAPSHOT = "3d39fe7ccad5b41c6c2f900d3134d5a5f6eb3ed4"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def registry():
    tree = ast.parse(git("show", f"{SNAPSHOT}:{SOURCE}"))
    entries = next(node.value for node in tree.body if isinstance(node, ast.AnnAssign)
                   and getattr(node.target, "id", None) == "CRITERION_REGISTRY")
    return {ast.literal_eval(key): {
        **{kw.arg: ast.literal_eval(kw.value) for kw in value.keywords
           if kw.arg in ("revision", "detector", "applicability")}, "line": value.lineno,
    } for key, value in zip(entries.keys, entries.values)
        if ast.literal_eval(key).split(".")[0] in GATES}


REGISTRY = registry()


def rows(text):
    return {line.split("|")[1].strip(): line for line in text.splitlines()
            if line.startswith("| ") and line.split("|")[1].strip() in GATES}


def prose():
    return " ".join(DOC.read_text().split())


def test_snapshot_commit_blob_and_revision():
    text = DOC.read_text()
    assert (re.search(r'ref: "origin/main@([0-9a-f]{40})"', text).group(1),
            re.search(r'blob: "([0-9a-f]{40})"', text).group(1),
            int(re.search(r"registry_revision: (\d+)", text).group(1))) == (
                SNAPSHOT, git("rev-parse", f"{SNAPSHOT}:{SOURCE}"), 29)


@pytest.mark.parametrize("criterion", REGISTRY)
def test_each_criterion_revision_and_exact_source_locator(criterion):
    entry = REGISTRY[criterion]
    row = rows(DOC.read_text())[criterion.split(".")[0]]
    assert re.search(rf"`{re.escape(criterion)}` rev {entry['revision']}"
                     rf" — `asset_census.py:{entry['line']}`", row)


def test_exactly_nine_gates_and_all_25_core_criteria():
    found = re.findall(r"`([A-Za-z]+\.[a-zA-Z0-9_]+)` rev \d+ — `asset_census.py:\d+`",
                       "\n".join(rows(DOC.read_text()).values()))
    assert (set(rows(DOC.read_text())), sorted(found)) == (set(GATES), sorted(REGISTRY))


def test_checked_no_table_carriage_rule_and_d2_ceiling():
    text = prose()
    carr = rows(DOC.read_text())["Carr"]
    assert all(token in text for token in (
        "N-283", "`no_table`", "target_table empty", "no count_sql table",
        "no @register", "no produced_tables", "no carriage nature", "all checked",
        "Carr.D1#measured:no-table-no-prose", "Carr.D2#measured:no-table-no-prose",
        "Carr.D3#measured:no-table-no-prose", "no-per-witness-values",
    )) and "Checked N/A" in carr and "D2 cannot earn PASS" in carr


def test_difference_table_covers_changed_plan_criteria_and_required_topics():
    text = DOC.read_text().split("## Differences from plan §7", 1)[1].split("## Carriage applicability", 1)[0]
    assert all(key in text for key in REGISTRY) and all(word in text for word in (
        "produced_tables", "rows_written", "history window", "NO_DETECTOR",
        "source resolution", "same capability entry", "N-283", "registry revision 28",
    ))


@pytest.mark.parametrize("criterion", REGISTRY)
def test_difference_table_names_current_criterion_revision(criterion):
    text = DOC.read_text().split("## Differences from plan §7", 1)[1].split("## Carriage applicability", 1)[0]
    assert re.search(rf"{re.escape(criterion)} rev {REGISTRY[criterion]['revision']}\b", text)


def test_corpus_derived_modes_preserve_placeholder_and_fidelity_readings():
    text = prose()
    assert all(token in text for token in (
        "Mode 1", "Mode 2", "sha256-pinned parser", "every cited chunk",
        "uncited chunks", "only Narr.agree and Narr.checkable", "Null.schema_default",
        "Null.blank_rows", "Narr.fidelity_test", "Narr.lint keep their own readings",
    ))


def test_build_completion_read_failures_never_leave_pass():
    text = prose()
    assert all(token in text for token in (
        "SQLSTATE 42501", "NO_DETECTOR", "unread latest-attempt",
        "cuts PASS to PARTIAL", "no age window", "passive_projection",
    ))


@pytest.mark.parametrize("criterion", ("Carr.D1", "Carr.D2", "Carr.D3"))
def test_stale_carriage_revision_mutations_are_rejected(criterion):
    entry = REGISTRY[criterion]
    text = DOC.read_text().replace(f"`{criterion}` rev {entry['revision']} —",
                                   f"`{criterion}` rev {entry['revision'] - 1} —", 1)
    assert not re.search(rf"`{re.escape(criterion)}` rev {entry['revision']} —",
                         rows(text)["Carr"])
