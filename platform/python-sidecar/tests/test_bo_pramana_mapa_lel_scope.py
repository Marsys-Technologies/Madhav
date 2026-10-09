"""
test_bo_pramana_mapa_lel_scope.py — F9 (LIFE_EVENTS_SCOPE_AUDIT, SS N-110).

The audit saw `_LEL_TERM_B_SQL` joining `life_events le ON le.event_id::text = r.ref`
with no chart predicate (an event id existing only in ANOTHER chart could raise a
false leak flag). On current main that join is already gone: Term B inspects only
declared L2 provenance (`bodha_msr_signals.source_l1_asset`) and never consults
life_events at all (L2 must not read private later-layer state to decide whether
deterministic producer output is clean). This guard pins both safe shapes so the
join cannot return unscoped:

  * the writer's SQL (any string constant that is a statement) either does not
    reference `life_events` at all (current, preferred), or
  * if it ever does, every such statement scopes the join with
    `le.chart_id = s.chart_id`.

Pure source inspection; no database.
"""
from __future__ import annotations

import ast
import inspect
import re

from pipeline.orchestrator.writers import bo_pramana_mapa as mod


def _sql_strings() -> list[str]:
    tree = ast.parse(inspect.getsource(mod))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if re.search(r"\b(SELECT|JOIN|FROM)\b", node.value):
                out.append(node.value)
    return out


def test_term_b_does_not_join_life_events():
    sql = mod._LEL_TERM_B_SQL
    assert "life_events" not in sql
    assert "source_l1_asset" in sql and "chart_id = %s" in sql


def test_any_life_events_reference_is_chart_scoped():
    offenders = []
    for sql in _sql_strings():
        if re.search(r"\blife_events\b", sql):
            flat = " ".join(sql.split())
            if not re.search(r"\ble\.chart_id\s*=\s*s\.chart_id\b", flat):
                offenders.append(flat[:120])
    assert not offenders, f"life_events referenced without chart scope: {offenders}"
