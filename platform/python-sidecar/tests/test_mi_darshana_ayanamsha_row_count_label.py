"""
test_mi_darshana_ayanamsha_row_count_label.py -- SS N-341 (PR-H2), audit item B7.

CLAUDE.md §N.8 (Earned-Signal): mi_darshana's verdict_object provenance_chain carried

    "ayanamsha_robustness": <COUNT(DISTINCT ayanamsha_id) FROM bodha_pratijna>

That is a count of ayanamsha ROWS present in bodha_pratijna, not a robustness measurement:
the verdict itself is pinned to one canonical ayanamsha (CANONICAL_AYA), and nothing
compares the verdict across ayanamshas. (On a single-ayanamsha chart it read as a
"robustness" of 1; on a five-ayanamsha build it read as a "robustness" of 5 -- equally not
a measurement.) The count is real and kept, under a name that says what it is:
`distinct_ayanamsha_row_count`. The JSON key `ayanamsha_robustness` must not come back.

provenance_chain is a JSONB column (migration 353), so this is a JSON-key relabel, not a
column rename.

Behavioural tests drive the real `_substep_insight_units` (both verdict branches) through
the same hermetic fake connection test_mi_darshana.py uses; the ast guard pins the key.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from pipeline.orchestrator.writers.mi_darshana import MiDarshanaWriter
from tests.test_mi_darshana import (
    NATIVE_CHART_ID,
    PROVENANCE_CHAIN,
    _FakeConn,
    _pratijna_row,
)

_WRITER = (pathlib.Path(__file__).resolve().parent.parent
           / 'pipeline' / 'orchestrator' / 'writers' / 'mi_darshana.py')


def _verdict_provenances(pratijna_rows, aya_count):
    conn = _FakeConn([])
    conn.existing_tables = {'bodha_pratijna', 'bodha_triangulation'}
    conn.pratijna_rows = pratijna_rows
    conn.aya_count = aya_count
    MiDarshanaWriter()._substep_insight_units(conn, NATIVE_CHART_ID, t0=0.0)
    return [json.loads(r[PROVENANCE_CHAIN]) for r in conn.inserted_rows]


def _no_evidence_row():
    r = _pratijna_row('ec_none', grade=None, status='no_evidence', domain='career')
    return r


@pytest.mark.parametrize('aya_count', [1, 5])
class TestVerdictProvenanceLabelsTheRowCountHonestly:
    def test_graded_verdict_has_row_count_and_no_robustness_key(self, aya_count):
        (prov,) = _verdict_provenances(
            [_pratijna_row('ec_career', grade=7.0, status='promised', domain='career')], aya_count)
        assert 'ayanamsha_robustness' not in prov
        assert prov['distinct_ayanamsha_row_count'] == aya_count
        assert prov['canonical_ayanamsha_id'] == 'lahiri_chitrapaksha'

    def test_no_evidence_verdict_has_row_count_and_no_robustness_key(self, aya_count):
        (prov,) = _verdict_provenances([_no_evidence_row()], aya_count)
        assert 'ayanamsha_robustness' not in prov
        assert prov['distinct_ayanamsha_row_count'] == aya_count
        assert prov['activation_state'] == 'no_evidence'


def test_row_count_is_the_queried_count_not_a_constant():
    a = _verdict_provenances([_pratijna_row('ec_career', grade=7.0, status='promised')], 1)[0]
    b = _verdict_provenances([_pratijna_row('ec_career', grade=7.0, status='promised')], 5)[0]
    assert (a['distinct_ayanamsha_row_count'], b['distinct_ayanamsha_row_count']) == (1, 5)


class TestAstGuard:
    def test_no_dict_key_named_ayanamsha_robustness_in_writer(self):
        tree = ast.parse(_WRITER.read_text(), feature_version=(3, 11))
        keys = [n.value for node in ast.walk(tree) if isinstance(node, ast.Dict)
                for n in node.keys if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert 'ayanamsha_robustness' not in keys, (
            'mi_darshana labels a distinct-ayanamsha ROW COUNT as ayanamsha_robustness (SS N-341 / B7)'
        )
        assert keys.count('distinct_ayanamsha_row_count') == 2   # graded + no_evidence verdict dicts

    def test_no_row_count_variable_named_robustness(self):
        tree = ast.parse(_WRITER.read_text(), feature_version=(3, 11))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        assert not {n for n in names if 'robust' in n.lower()}
