"""
test_mi_darshana_no_evidence.py — tests for honest 'no_evidence' verdict rows.

bo_pratijna v2.0 introduced status='no_evidence' for event classes that have zero
supporting or contradicting signals. mi_darshana must produce verdict_object rows
for these that carry:
  - statement containing "no evidence" (not "grade N/10")
  - rank_consequence == 0.0
  - confidence_band is None (not a fabricated band from a null grade)
  - activation_state == 'no_evidence' in the provenance_chain
  - grade is None in the provenance_chain (not the 5.0 fallback)

§N.7 item 6: "an honest null beats an invented judgment."
R6: serve no_evidence rows — don't gate them.
"""
from __future__ import annotations

import json
import sys
import os

# Ensure the pipeline package is importable without a full install.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.orchestrator.writers.mi_darshana import MiDarshanaWriter

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# Insert-tuple column offsets (mirror the INSERT column list in the writer).
# (chart_id, insight_id, insight_type, domain, horizon, question_lens,
#  statement, rank_consequence, confidence_band, n_support,
#  leakage_status, evidence_grade, freshness_lel_version,
#  last_calibrated_at, provenance_chain, is_negative_knowledge,
#  surface_formula_version)
STATEMENT = 6
RANK_CONSEQUENCE = 7
CONFIDENCE_BAND = 8
N_SUPPORT = 9
PROVENANCE_CHAIN = 14


# ── DB-path fakes (minimal, reuses the pattern from test_mi_darshana.py) ─────

class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "information_schema.tables" in s:
            table_name = params[0] if params else None
            self._result = [{"exists": 1}] if table_name in self._conn.existing_tables else []
        elif "FROM mimamsa_reliability" in s:
            self._result = []
        elif "FROM mimamsa_manifestation_grammar" in s:
            self._result = []
        elif "FROM mimamsa_discoveries" in s:
            self._result = []
        elif "FROM mimamsa_load_bearing" in s:
            self._result = []
        elif "JOIN brahma_event_ontology" in s:
            self._result = list(self._conn.pratijna_rows)
        elif "SELECT COUNT(DISTINCT ayanamsha_id) FROM bodha_pratijna" in s:
            self._result = [{"count": self._conn.aya_count}]
        elif "FROM bodha_msr_signals" in s:
            self._result = []
        elif "FROM bodha_contradictions" in s:
            self._result = []
        elif "FROM bodha_triangulation" in s:
            self._result = []
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None

    def executemany(self, sql, params_list):
        if "INSERT INTO mimamsa_insight_units" in " ".join(sql.split()):
            self._conn.inserted_rows.extend(params_list)


class _FakeConn:
    def __init__(self):
        self.existing_tables: set[str] = {"bodha_pratijna", "bodha_triangulation"}
        self.pratijna_rows: list[dict] = []
        self.aya_count = 1
        self.inserted_rows: list[tuple] = []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


def _run_verdict_with_no_evidence(pratijna_rows):
    """Drive the Section-5 verdict_object branch with no_evidence rows."""
    conn = _FakeConn()
    conn.pratijna_rows = pratijna_rows
    writer = MiDarshanaWriter()
    result = writer._substep_insight_units(conn, NATIVE_CHART_ID, t0=0.0)
    return conn, result


def _no_evidence_row(event_class_id="ec_marriage", domain="relationship"):
    """A bodha_pratijna row with status='no_evidence' and grade=None."""
    return {
        "event_class_id": event_class_id,
        "status": "no_evidence",
        "grade": None,
        "supporting_signal_ids": [],
        "contradicting_signal_ids": [],
        "name_en": event_class_id.replace("_", " ").title(),
        "domain": domain,
    }


# ── tests ─────────────────────────────────────────────────────────────────────

def test_no_evidence_statement_contains_no_evidence_not_grade():
    """
    A no_evidence row must produce a statement that says "no evidence",
    NOT "grade N/10" — which would be an invented judgment (§N.7 item 6).
    """
    conn, result = _run_verdict_with_no_evidence([
        _no_evidence_row("ec_marriage", domain="relationship"),
    ])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    statement = row[STATEMENT]

    assert "no evidence" in statement.lower(), (
        f"Expected 'no evidence' in statement, got: {statement!r}"
    )
    assert "grade" not in statement.lower(), (
        f"Statement must not contain 'grade' for no_evidence row, got: {statement!r}"
    )


def test_no_evidence_rank_consequence_is_zero():
    """
    no_evidence rows get rank_consequence=0.0 (lowest priority in serving
    order, not a fabricated mid-range from a null grade).
    """
    conn, result = _run_verdict_with_no_evidence([
        _no_evidence_row("ec_career", domain="career"),
    ])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    rank = row[RANK_CONSEQUENCE]
    assert rank == 0.0, f"Expected rank_consequence=0.0 for no_evidence, got {rank!r}"
    assert isinstance(rank, float), f"rank_consequence must be float, got {type(rank)}"


def test_no_evidence_confidence_band_is_null():
    """
    no_evidence rows must have confidence_band=None — you cannot compute a
    band from a null grade. Fabricating one (e.g. "[0.4,0.6)") would be an
    invented judgment.
    """
    conn, result = _run_verdict_with_no_evidence([
        _no_evidence_row("ec_health", domain="health"),
    ])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    band = row[CONFIDENCE_BAND]
    assert band is None, (
        f"Expected confidence_band=None for no_evidence row, got {band!r}"
    )


def test_no_evidence_activation_state_in_provenance():
    """
    The provenance_chain JSON must have activation_state='no_evidence'
    so callers can distinguish this from promised/denied/conditional.
    """
    conn, result = _run_verdict_with_no_evidence([
        _no_evidence_row("ec_wealth", domain="wealth"),
    ])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov.get("activation_state") == "no_evidence", (
        f"Expected activation_state='no_evidence' in provenance, got: {prov.get('activation_state')!r}"
    )


def test_no_evidence_grade_is_null_in_provenance():
    """
    The provenance_chain JSON must have grade=None, NOT 5.0 (the neutral
    default that is correct for unscored rows but dishonest for no_evidence
    rows where grade IS null by design).
    """
    conn, result = _run_verdict_with_no_evidence([
        _no_evidence_row("ec_dharma", domain="dharma"),
    ])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov.get("grade") is None, (
        f"Expected grade=None in provenance for no_evidence, got {prov.get('grade')!r}"
    )


def test_no_evidence_row_is_still_written_r6():
    """
    R6 says serve no_evidence rows — don't gate or drop them. A no_evidence
    row must still produce exactly one insight_unit row in the output.
    """
    conn, result = _run_verdict_with_no_evidence([
        _no_evidence_row("ec_moksha", domain="spirituality"),
    ])

    assert result.rows_inserted == 1, (
        f"R6: no_evidence row must still be written, rows_inserted={result.rows_inserted}"
    )
    assert len(conn.inserted_rows) == 1


def test_no_evidence_mixed_with_normal_rows():
    """
    When no_evidence rows exist alongside normal (conditional/promised/denied)
    rows, each is handled independently:
    - no_evidence: honest statement, null grade in provenance, 0.0 rank
    - normal: existing grade logic unchanged
    """
    pratijna_rows = [
        _no_evidence_row("ec_no_signal", domain="career"),
        {
            "event_class_id": "ec_with_grade",
            "status": "conditional",
            "grade": 4.5,
            "supporting_signal_ids": [],
            "contradicting_signal_ids": [],
            "name_en": "Ec With Grade",
            "domain": "career",
        },
    ]
    conn, result = _run_verdict_with_no_evidence(pratijna_rows)

    # The ORDER BY grade DESC NULLS LAST means no_evidence (grade=NULL) comes last
    # in the pratijna fetch, but both rows must be written.
    assert result.rows_inserted == 2

    # Find the no_evidence row by checking statement content
    no_evid_rows = [r for r in conn.inserted_rows if "no evidence" in r[STATEMENT].lower()]
    normal_rows = [r for r in conn.inserted_rows if "no evidence" not in r[STATEMENT].lower()]

    assert len(no_evid_rows) == 1, f"Expected 1 no_evidence row, got {len(no_evid_rows)}"
    assert len(normal_rows) == 1, f"Expected 1 normal row, got {len(normal_rows)}"

    # no_evidence row checks
    ne_row = no_evid_rows[0]
    ne_prov = json.loads(ne_row[PROVENANCE_CHAIN])
    assert ne_prov.get("grade") is None
    assert ne_row[RANK_CONSEQUENCE] == 0.0
    assert ne_row[CONFIDENCE_BAND] is None

    # normal row checks — grade must be 4.5, not 5.0 (no truthiness bug regression)
    norm_row = normal_rows[0]
    norm_prov = json.loads(norm_row[PROVENANCE_CHAIN])
    assert norm_prov.get("grade") == 4.5
