"""
test_mi_darshana.py — hermetic tests for the L5 Mīmāṃsā insight-retrieval writer.

Focus: the confidence-interval computation in `_substep_insight_units` must not
choke on DB numeric values. `observed_rate` and `brier_score` arrive as
`decimal.Decimal` for a calibrated chart (the native); Abhinandan's were NULL,
so they fell through to a float default and masked a `Decimal - float` TypeError
at build time. These tests feed a `Decimal` observed value through a fake conn
(no real DB) and assert: no TypeError, correct float conf_lo/conf_hi bounds, and
JSON-serializable provenance. The NULL/None path is kept for regression cover.
"""
from __future__ import annotations

from decimal import Decimal

from pipeline.orchestrator.writers.mi_darshana import MiDarshanaWriter

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


# ── DB-path fakes (model only the queries _substep_insight_units issues) ──────

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
            # Section-5 bodha tables present iff the test opted in via
            # conn.existing_tables (default empty → verdict_object branch skipped).
            table_name = params[0] if params else None
            self._result = [{"exists": 1}] if table_name in self._conn.existing_tables else []
        elif "FROM mimamsa_reliability" in s:
            self._result = list(self._conn.reliability_rows)
        elif "FROM mimamsa_manifestation_grammar" in s:
            self._result = list(self._conn.grammar_rows)
        elif "FROM mimamsa_discoveries" in s:
            self._result = []
        elif "FROM mimamsa_load_bearing" in s:
            self._result = []
        elif "JOIN brahma_event_ontology" in s:
            self._result = list(self._conn.pratijna_rows)
        elif "SELECT COUNT(DISTINCT ayanamsha_id) FROM bodha_pratijna" in s:
            self._result = [{"count": self._conn.aya_count}]
        elif "FROM bodha_msr_signals" in s:
            self._result = list(self._conn.msr_signal_rows)
        elif "FROM bodha_contradictions" in s:
            self._result = list(self._conn.contradiction_rows)
        elif "FROM bodha_triangulation" in s:
            self._result = list(self._conn.triangulation_rows)
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
    def __init__(self, reliability_rows):
        self.reliability_rows = list(reliability_rows)
        self.grammar_rows: list[dict] = []
        self.inserted_rows: list[tuple] = []
        # Section-5 (bodha_pratijna verdict_object) fakes — opt-in per test.
        self.existing_tables: set[str] = set()
        self.pratijna_rows: list[dict] = []
        self.msr_signal_rows: list[dict] = []
        self.contradiction_rows: list[dict] = []
        self.triangulation_rows: list[dict] = []
        self.aya_count = 1

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


def _run(reliability_rows):
    conn = _FakeConn(reliability_rows)
    writer = MiDarshanaWriter()
    result = writer._substep_insight_units(conn, NATIVE_CHART_ID, t0=0.0)
    return conn, result


def _pratijna_row(event_class_id, grade, status="conditional", domain="career", name_en=None):
    return {
        "event_class_id": event_class_id,
        "status": status,
        "grade": grade,
        "supporting_signal_ids": [],
        "contradicting_signal_ids": [],
        "name_en": name_en or event_class_id,
        "domain": domain,
    }


def _grammar_row(channel_propensity, prior_propensity, channel_id="ch1", domain="career", n=10):
    return {
        "channel_id": channel_id,
        "domain": domain,
        "channel_propensity": channel_propensity,
        "prior_propensity": prior_propensity,
        "n_support": n,
        "evidence_grade": "empirical",
    }


def _run_grammar(grammar_rows):
    conn = _FakeConn([])
    conn.grammar_rows = grammar_rows
    writer = MiDarshanaWriter()
    result = writer._substep_insight_units(conn, NATIVE_CHART_ID, t0=0.0)
    return conn, result


def _run_verdict(pratijna_rows, triangulation_rows=None):
    """Drive the Section-5 verdict_object branch: bodha_pratijna +
    bodha_triangulation both 'exist', with the given pratijna rows and no
    corroborating signals/contradictions (kept empty so the test isolates the
    grade-fallback / verdict_note logic under scrutiny). `triangulation_rows`
    defaults to empty (no cross-tradition data) unless a test opts in."""
    conn = _FakeConn([])
    conn.existing_tables = {"bodha_pratijna", "bodha_triangulation"}
    conn.pratijna_rows = pratijna_rows
    conn.triangulation_rows = triangulation_rows or []
    writer = MiDarshanaWriter()
    result = writer._substep_insight_units(conn, NATIVE_CHART_ID, t0=0.0)
    return conn, result


# Insert-tuple column offsets (mirror the INSERT column list in the writer).
STATEMENT, RANK_CONSEQUENCE, CONFIDENCE_BAND = 6, 7, 8
PROVENANCE_CHAIN = 14


def _calibrated_row(observed, brier, n=5):
    return {
        "stratum_key": "career|near|high",
        "predicted_prob_bin": "0.7-0.8",
        "observed_rate": observed,
        "n": n,
        "brier_score": brier,
        "evidence_grade": "empirical",
        "held_out_validity": True,
    }


# ── tests ─────────────────────────────────────────────────────────────────────

def test_decimal_observed_no_typeerror_and_correct_bounds():
    """The native path: observed_rate + brier_score are Decimal. Must not raise
    and must produce correct float confidence bounds."""
    import json

    conn, result = _run([_calibrated_row(Decimal("0.73"), Decimal("0.12"))])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    # conf_lo = 0.73 - 0.1 = 0.63 ; conf_hi = 0.73 + 0.1 = 0.83
    assert row[CONFIDENCE_BAND] == "[0.63,0.83)"
    assert row[RANK_CONSEQUENCE] == 0.73
    assert isinstance(row[RANK_CONSEQUENCE], float)
    # provenance JSON must be serializable and carry a float (not Decimal) brier
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov["brier"] == 0.12
    assert isinstance(prov["brier"], float)
    assert "73.0%" in row[STATEMENT]


def test_decimal_clamps_at_upper_bound():
    """High observed rate clamps conf_hi at 1.0 without Decimal arithmetic."""
    conn, _ = _run([_calibrated_row(Decimal("0.95"), Decimal("0.05"))])
    row = conn.inserted_rows[0]
    # conf_lo = 0.85 ; conf_hi = min(1.0, 1.05) = 1.0
    assert row[CONFIDENCE_BAND] == "[0.85,1.0)"


def test_none_observed_falls_back_to_default():
    """Regression cover for the pre-existing (Abhinandan) NULL path."""
    import json

    conn, result = _run([_calibrated_row(None, None)])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    # obs defaults to 0.5 → conf_lo 0.4, conf_hi 0.6
    assert row[CONFIDENCE_BAND] == "[0.4,0.6)"
    assert row[RANK_CONSEQUENCE] == 0.5
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov["brier"] is None
    assert "insufficient events" in row[STATEMENT]


def test_low_n_stratum_skipped():
    """n < 2 strata produce no insight unit (no rows, clean return)."""
    conn, result = _run([_calibrated_row(Decimal("0.73"), Decimal("0.12"), n=1)])
    assert result.rows_inserted == 0
    assert conn.inserted_rows == []


# ── P0-10 / D4_GRADE_INVERSION — verdict_object grade fallback ────────────────
#
# bodha_pratijna (migration 391_bodha_pratijna.sql) defines grade [0-10]:
# "0=strongly denied, 10=strongly promised" — 0.0 is a genuine, meaningful,
# computed value (the most-refuted possible score), not an absence marker.
# Only a NULL/missing grade means "not yet scored" and should fall back to
# the neutral default 5.0. `grade = float(pr.get("grade") or 5.0)` uses
# Python truthiness, which conflates a real 0.0 with "missing" and silently
# reports the neutral default instead — inverting the verdict.

def test_grade_zero_preserved_not_defaulted():
    """A genuinely computed grade of 0.0 (strongly denied) must survive into
    the verdict_object insight unit's provenance and narration verbatim —
    not be silently replaced by the neutral default 5.0."""
    import json

    conn, result = _run_verdict([
        _pratijna_row("ec_denied", grade=0.0, status="denied"),
    ])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov["grade"] == 0.0
    assert "grade 0.0/10" in row[STATEMENT]
    assert "Mixed or insufficient evidence." in row[STATEMENT]


def test_grade_missing_falls_back_to_neutral_default():
    """Regression cover for the legitimate fallback: an absent/None grade
    (bodha_pratijna has not yet scored this event_class) must still default
    to the neutral 5.0 — this path must not break when the truthiness bug
    is fixed."""
    import json

    conn, result = _run_verdict([
        _pratijna_row("ec_unscored", grade=None, status="conditional"),
    ])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov["grade"] == 5.0
    assert "grade 5.0/10" in row[STATEMENT]


# ── P2 (same file, mi_darshana.py:159, CONFIRMED mislabel/drift) ─────────────
#
# mimamsa_manifestation_grammar (migration 352) declares channel_propensity
# NULLABLE and prior_propensity NOT NULL — channel_propensity is only computed
# once there's enough fire/opportunity data, and a genuinely-computed 0.0
# means "this channel never fires" (a real, meaningful extreme, not a missing
# value). The same `or` truthiness pattern as P0-10 masks that 0.0 behind
# prior_propensity (or the 0.5 default).

def test_channel_propensity_zero_preserved_not_masked_by_prior():
    """A genuinely computed channel_propensity of 0.0 must survive — not be
    silently replaced by a nonzero prior_propensity."""
    import json

    conn, result = _run_grammar([_grammar_row(channel_propensity=0.0, prior_propensity=0.8)])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    assert row[RANK_CONSEQUENCE] == 0.0
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov["propensity"] == 0.0
    assert "0% propensity" in row[STATEMENT]


def test_channel_propensity_missing_falls_back_to_prior():
    """Regression cover for the legitimate fallback: a genuinely-absent
    channel_propensity (None — not yet computed) must still fall back to
    prior_propensity."""
    conn, result = _run_grammar([_grammar_row(channel_propensity=None, prior_propensity=0.35)])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    assert row[RANK_CONSEQUENCE] == 0.35


# ── SV-5 — `verdict_note` tradition-blindness (ŚUDDHA-VĀCA parked finding,
# fixed by NIḤŚEṢA Track B) ───────────────────────────────────────────────────
#
# Pre-fix, `verdict_note` said "Strong evidence across traditions." purely from
# `grade >= 6.0`, regardless of whether `tradition_concordance` (sourced from
# `bodha_triangulation` via `trad_by_class`) held any actual cross-tradition
# data for the row's domain — an invented judgment, not a restatement of a
# cited fact (§N.7 item 6). The fix restructures the note across both axes:
# grade tier, and whether real concordance data exists. It also removes a dead
# `trad_by_class.get(event_class_id)` lookup: bo_sangati.py always writes
# `bodha_triangulation.question_class = domain`, never `event_class_id`, so
# that lookup could never hit — a fact confirmed by the third test below.

def test_verdict_note_high_grade_no_tradition_data_is_honest():
    """No bodha_triangulation rows at all for this domain: the note must say
    so honestly, not claim a cross-tradition check that never ran."""
    import json

    conn, result = _run_verdict(
        [_pratijna_row("ec_strong", grade=8.0, status="active", domain="career")],
    )
    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert (
        "Strong evidence (single-tradition basis; no cross-tradition concordance data)."
        in row[STATEMENT]
    )
    assert prov["grade"] == 8.0


def test_verdict_note_high_grade_with_tradition_data_is_corroborated():
    """A real bodha_triangulation row keyed to this row's domain must flip the
    note to the corroborated phrasing — the positive-data axis."""
    conn, result = _run_verdict(
        [_pratijna_row("ec_strong", grade=8.0, status="active", domain="career")],
        triangulation_rows=[
            {
                "question_class": "career",
                "tradition": "parashari",
                "concordance_score": 0.8,
                "signal_ids": ["s1"],
            }
        ],
    )
    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    assert "Strong evidence, corroborated across traditions." in row[STATEMENT]


def test_verdict_note_event_class_id_keyed_row_does_not_match_domain_lookup():
    """Regression for the removed dead lookup: bo_sangati.py never writes
    `question_class = event_class_id`, only `question_class = domain`. A
    triangulation row keyed to the event_class_id string (not the domain) must
    NOT be picked up by the domain-only lookup — proving the old
    `trad_by_class.get(event_class_id)` branch was genuinely unreachable, not
    just redundant."""
    conn, result = _run_verdict(
        [_pratijna_row("ec_strong", grade=8.0, status="active", domain="career")],
        triangulation_rows=[
            {
                "question_class": "ec_strong",  # matches event_class_id, NOT domain
                "tradition": "parashari",
                "concordance_score": 0.9,
                "signal_ids": [],
            }
        ],
    )
    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    assert (
        "Strong evidence (single-tradition basis; no cross-tradition concordance data)."
        in row[STATEMENT]
    )


def test_verdict_note_mid_grade_with_tradition_data():
    """Middle grade band, data present — the conditional-band phrasing must
    also honor the data-presence axis, not just the high/low bands."""
    conn, result = _run_verdict(
        [_pratijna_row("ec_mid", grade=4.5, status="conditional", domain="health")],
        triangulation_rows=[
            {
                "question_class": "health",
                "tradition": "jaimini",
                "concordance_score": 0.5,
                "signal_ids": ["s2"],
            }
        ],
    )
    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    assert "Conditional — context-dependent, per cross-tradition concordance." in row[STATEMENT]
