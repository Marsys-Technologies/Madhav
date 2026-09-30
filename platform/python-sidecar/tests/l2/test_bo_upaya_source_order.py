"""Source-order guard for bo_upaya's rebuild delete sequence (R244).

bodha_rm_dasha_windowed_prescriptions.base_prescription_id carries a live NO ACTION
foreign key onto bodha_rm_remedy_prescriptions.prescription_id, and
bodha_rm_remedy_prescriptions.target_resonance_id carries one onto
bodha_rm_resonances.resonance_id. A rebuild therefore only succeeds if the writer
deletes child before parent, in this order:

    replace_prior_rm_dasha_windowed  ->  replace_prior_rm_prescriptions
                                     ->  replace_prior_rm_resonances

Commit fa9857f00 (#2607) dropped the first call, making every rebuild raise a
foreign-key violation on charts holding legacy windowed rows. DP-SD-015 asks L2 to
stop PRODUCING windowed rows and to keep the legacy schema; it does not ask for
legacy rows to survive a rebuild (native ruling R244, option a).

Pure source/AST test: no DB, no imports of the writer module.
"""
from __future__ import annotations

import ast
from pathlib import Path

WRITER = (
    Path(__file__).parents[2] / "pipeline" / "orchestrator" / "writers" / "bo_upaya.py"
)

WINDOWED = "replace_prior_rm_dasha_windowed"
PRESCRIPTIONS = "replace_prior_rm_prescriptions"
RESONANCES = "replace_prior_rm_resonances"


def _run_method() -> ast.FunctionDef:
    tree = ast.parse(WRITER.read_text())
    writer = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "BoUpayaWriter"
    )
    return next(
        n for n in writer.body if isinstance(n, ast.FunctionDef) and n.name == "run"
    )


def _call_lines(run: ast.FunctionDef) -> dict[str, list[int]]:
    lines: dict[str, list[int]] = {}
    for node in ast.walk(run):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            lines.setdefault(node.func.id, []).append(node.lineno)
    return lines


def _loop_statement_index(run: ast.FunctionDef) -> dict[str, tuple[int, int]]:
    """Map each helper name to (id of enclosing For node, statement index in its body)."""
    out: dict[str, tuple[int, int]] = {}
    for loop in ast.walk(run):
        if not isinstance(loop, ast.For):
            continue
        for idx, stmt in enumerate(loop.body):
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in (WINDOWED, PRESCRIPTIONS, RESONANCES):
                        out.setdefault(node.func.id, (id(loop), idx))
    return out


def test_run_calls_all_three_rm_delete_helpers_exactly_once():
    lines = _call_lines(_run_method())
    for name in (WINDOWED, PRESCRIPTIONS, RESONANCES):
        assert len(lines.get(name, [])) == 1, (
            f"{name} must be called exactly once in BoUpayaWriter.run "
            f"(found {lines.get(name, [])})"
        )


def test_windowed_delete_precedes_prescriptions_delete_precedes_resonances_delete():
    lines = _call_lines(_run_method())
    assert WINDOWED in lines, (
        f"{WINDOWED} is not called in BoUpayaWriter.run: rebuild would violate the "
        "NO ACTION FK from bodha_rm_dasha_windowed_prescriptions onto "
        "bodha_rm_remedy_prescriptions (R244)"
    )
    windowed, presc, reson = lines[WINDOWED][0], lines[PRESCRIPTIONS][0], lines[RESONANCES][0]
    assert windowed < presc, (
        f"{WINDOWED} (line {windowed}) must precede {PRESCRIPTIONS} (line {presc})"
    )
    assert presc < reson, (
        f"{PRESCRIPTIONS} (line {presc}) must precede {RESONANCES} (line {reson})"
    )


def test_delete_helpers_share_one_per_ayanamsha_loop_body_in_fk_order():
    """Same For-loop body (so each ayanamsha's generation is cleared before it is
    re-inserted), with strictly ascending statement position in FK-safe order."""
    pos = _loop_statement_index(_run_method())
    assert set(pos) == {WINDOWED, PRESCRIPTIONS, RESONANCES}, sorted(pos)
    assert len({loop_id for loop_id, _ in pos.values()}) == 1
    assert pos[WINDOWED][1] < pos[PRESCRIPTIONS][1] < pos[RESONANCES][1]


def test_windowed_helper_is_imported_from_the_shared_idempotency_module():
    run = _run_method()
    imported = {
        alias.name
        for node in ast.walk(run)
        if isinstance(node, ast.ImportFrom) and node.module == "bodha_writers._idempotency"
        for alias in node.names
    }
    assert {WINDOWED, PRESCRIPTIONS, RESONANCES} <= imported


def test_l2_still_does_not_emit_windowed_rows():
    """DP-SD-015 stays satisfied: the fix restores a DELETE only; nothing inserts
    into the legacy windowed table and the L3-only builder is not called."""
    run = _run_method()
    calls = set(_call_lines(run))
    assert "_build_remedy_leverage_windows" not in calls
    src = WRITER.read_text()
    assert "INSERT INTO public.bodha_rm_dasha_windowed_prescriptions" not in src
    assert "_WINDOWED_INSERT" not in src
