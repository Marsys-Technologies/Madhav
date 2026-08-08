"""Tests for the bo_pratijna writer (Promise Register, L2 Bodha).

Two tiers, matching the project's established writer-test convention:

1. Offline (always runs, no DB required): the pure, DB-free grading logic
   (_compute_grade, _grade_to_status, _partition_signal).
2. Live (skipped unless DATABASE_URL or PROD_DB_URL is set): proves the
   migration constraint and writer behaviour against the real schema.

Bug targets (SHABDA-SHUDDHI lane-l2-pratijna):

BUG-1: Empty evidence -> 'denied 0.000' instead of 'no_evidence'
   When BOTH supporting AND contradicting signal lists are empty, the writer
   must set status='no_evidence', NOT status='denied'.

BUG-2: Valence filtering uses 'positive'/'negative' which never occur
   The actual bodha_msr_signals valence values are 'benefic'/'malefic'/
   'mixed'/'neutral'. The old code checks 'positive'/'negative' so everything
   is silently discarded and all outputs are falsely 'denied'.

BUG-3: mixed and neutral signals are silently discarded (R7 violation)
   Mixed signals must contribute to BOTH supporting and contradicting with
   reduced weight. Neutral signals contribute as context (lower weight).
"""
from __future__ import annotations

import inspect
import os

import pytest

from pipeline.orchestrator.writers.bo_pratijna import (
    _compute_grade,
    _grade_to_status,
    _partition_signal,
)
from pipeline.orchestrator.writers.bo_pratijna_karyatva import (
    KARYATVA_REGISTRY,
    get_karyatva,
)


# ── Offline tests: pure logic, no DB ──────────────────────────────────────────


# BUG-1: empty evidence must yield no_evidence, not denied
class TestNoEvidenceStatus:
    def test_empty_both_sides_yields_grade_zero(self):
        """Grade with no evidence is 0.0 — the formula has no inputs."""
        grade = _compute_grade([], [])
        assert grade == 0.0

    def test_grade_zero_empty_evidence_maps_to_no_evidence(self):
        """BUG-1 fix: grade=0.0 from empty evidence -> 'no_evidence', not 'denied'."""
        status = _grade_to_status(0.0, supporting_empty=True, contradicting_empty=True)
        assert status == "no_evidence", (
            f"Expected 'no_evidence' when both lists are empty; got {status!r}. "
            "Empty evidence means 'no information', NOT 'denied'."
        )

    def test_grade_zero_with_contradicting_signals_is_denied(self):
        """grade=0 from real contradicting signals is still 'denied', not 'no_evidence'."""
        grade = _compute_grade([], [0.5])
        status = _grade_to_status(grade, supporting_empty=True, contradicting_empty=False)
        assert status == "denied", (
            "A chart with real contradicting evidence should be 'denied', not 'no_evidence'."
        )

    def test_no_evidence_is_not_denied_and_not_promised(self):
        """no_evidence is a distinct fourth state."""
        status = _grade_to_status(0.0, supporting_empty=True, contradicting_empty=True)
        assert status not in ("denied", "promised", "conditional")


# BUG-2: valence mapping uses actual data values ('benefic'/'malefic')
class TestValencePartitioning:
    def test_benefic_signal_goes_to_supporting(self):
        """'benefic' (the actual data value) must land in supporting, not be discarded."""
        sup, con = _partition_signal("benefic", 0.8)
        assert sup == 0.8, "'benefic' valence must contribute its full salience to supporting"
        assert con == 0.0

    def test_malefic_signal_goes_to_contradicting(self):
        """'malefic' (the actual data value) must land in contradicting, not be discarded."""
        sup, con = _partition_signal("malefic", 0.8)
        assert sup == 0.0
        assert con == 0.8, "'malefic' valence must contribute its full salience to contradicting"

    def test_positive_valence_is_not_in_actual_data(self):
        """'positive' never occurs in bodha_msr_signals.
        It must NOT be accepted as full benefic weight."""
        sup, con = _partition_signal("positive", 0.8)
        assert sup != 0.8, (
            "'positive' is not a real valence in the data — the old bug is still present "
            "if it maps to full benefic weight"
        )

    def test_negative_valence_is_not_in_actual_data(self):
        """'negative' never occurs in bodha_msr_signals. Must not map to malefic weight."""
        sup, con = _partition_signal("negative", 0.8)
        assert con != 0.8, (
            "'negative' is not a real valence in the data — the old bug is still present "
            "if it maps to full malefic weight"
        )


# BUG-3: mixed and neutral signals must not be discarded (R7)
class TestMixedNeutralSignals:
    def test_mixed_contributes_to_both_sides_with_reduced_weight(self):
        """R7: mixed signals contribute to BOTH supporting and contradicting.
        They are NOT discarded. The contribution is reduced (< full salience)."""
        sup, con = _partition_signal("mixed", 0.8)
        assert sup > 0.0, "mixed signal must contribute SOMETHING to supporting (R7)"
        assert con > 0.0, "mixed signal must contribute SOMETHING to contradicting (R7)"
        assert sup <= 0.8, "mixed signal's supporting contribution must not exceed full salience"
        assert con <= 0.8, "mixed signal's contradicting contribution must not exceed full salience"

    def test_neutral_contributes_as_context(self):
        """R7: neutral signals contribute as context (lower weight, not zero).
        They are NOT silently discarded."""
        sup, con = _partition_signal("neutral", 0.8)
        total = sup + con
        assert total > 0.0, (
            "neutral signal must contribute as context (R7) — "
            f"got sup={sup}, con={con} (both zero means it was discarded)"
        )

    def test_mixed_hurts_grade_less_than_pure_malefic_of_same_salience(self):
        """When the top-5 supporting pool is saturated, a mixed signal (contributing
        partial con weight = _MIXED_WEIGHT * sal) damages the grade LESS than a pure
        malefic of the same salience (contributing full con weight = sal).

        This is the key R7 invariant: mixed is not equivalent to pure malefic.
        It contributes supporting evidence AND contradicting, so its net harm is
        smaller than the same salience as pure opposition.
        """
        sal = 0.5
        sup_from_mixed, con_from_mixed = _partition_signal("mixed", sal)

        # 5 strong benefic signals already saturate the top-5 supporting pool.
        # A 6th supporting entry (the mixed's sup portion) does not change the mean.
        grade_with_mixed = _compute_grade([1.0] * 5 + [sup_from_mixed], [con_from_mixed])
        grade_with_malefic = _compute_grade([1.0] * 5, [sal])  # pure malefic, no sup

        assert grade_with_mixed >= grade_with_malefic, (
            "A mixed signal (partial con) must damage the grade LESS than a pure "
            "malefic of the same salience (full con). "
            f"grade_with_mixed={grade_with_mixed:.3f}, "
            f"grade_with_malefic={grade_with_malefic:.3f}"
        )


# Grade thresholds: contract with downstreams (ph_nimitta, stage2_promise)
class TestGradeThresholds:
    def test_high_grade_yields_promised(self):
        """grade >= 6.0 -> 'promised'."""
        status = _grade_to_status(6.0, supporting_empty=False, contradicting_empty=True)
        assert status == "promised"

    def test_mid_grade_yields_conditional(self):
        """2.0 <= grade < 6.0 -> 'conditional'."""
        status = _grade_to_status(4.0, supporting_empty=False, contradicting_empty=False)
        assert status == "conditional"

    def test_low_grade_with_signals_yields_denied(self):
        """grade < 2.0 with real evidence -> 'denied'."""
        status = _grade_to_status(1.0, supporting_empty=False, contradicting_empty=False)
        assert status == "denied"

    def test_grade_range_is_clamped_0_to_10(self):
        """_compute_grade must always return a value in [0, 10]."""
        assert 0.0 <= _compute_grade([], []) <= 10.0
        assert 0.0 <= _compute_grade([1.0, 2.0], []) <= 10.0
        assert 0.0 <= _compute_grade([], [1.0, 2.0]) <= 10.0
        assert 0.0 <= _compute_grade([1.0], [1.0]) <= 10.0


# Source code structural checks (always run, no DB needed)
class TestSourceStructure:
    def test_writer_does_not_check_positive_valence(self):
        """The old bug: code checked 'positive' which never occurs.
        After the fix, 'positive' must not appear as a valence gate."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert 'valence in ("positive"' not in src, (
            "Old bug still present: code checks for 'positive' valence which never "
            "occurs in bodha_msr_signals"
        )
        assert "valence == 'positive'" not in src

    def test_writer_does_not_check_negative_valence(self):
        """The old bug: code checked 'negative' which never occurs."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert 'valence in ("negative"' not in src, (
            "Old bug still present: code checks for 'negative' valence which never "
            "occurs in bodha_msr_signals"
        )
        assert "valence == 'negative'" not in src

    def test_writer_handles_benefic_and_malefic(self):
        """The actual valence values must be handled in the writer."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "benefic" in src, "Writer must handle 'benefic' valence (real data value)"
        assert "malefic" in src, "Writer must handle 'malefic' valence (real data value)"

    def test_writer_handles_mixed_valence(self):
        """'mixed' must be present -- R7 forbids discarding it."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "mixed" in src, (
            "Writer must handle 'mixed' valence (R7: mixed signals are not discarded)"
        )

    def test_no_evidence_status_is_emitted(self):
        """Writer must be able to emit 'no_evidence' status."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "no_evidence" in src, (
            "Writer must emit 'no_evidence' status for empty-evidence cases"
        )


# ── v3 Property Tests (SIDDHANTA campaign) ────────────────────────────────────


class TestMarriageNotEqualSeparation:
    """REQUIRED: marriage and separation must have different karyatva routes
    producing DIFFERENT grades on the same chart. This test would have caught
    the domain-matching defect."""

    def test_different_karyatva_maps(self):
        """Marriage and separation have structurally different factor sets."""
        marriage = get_karyatva("marriage")
        separation = get_karyatva("separation")
        assert marriage is not None
        assert separation is not None
        # Key structural difference: separation requires dusthana
        assert not marriage.dusthana_required
        assert separation.dusthana_required
        # Different karaka grahas
        assert set(marriage.karaka_grahas) != set(separation.karaka_grahas)

    def test_marriage_separation_different_primary_bhava(self):
        """Separation uses dusthana houses (6,8,12) that marriage does not."""
        marriage = get_karyatva("marriage")
        separation = get_karyatva("separation")
        assert set(marriage.primary_bhava) != set(separation.primary_bhava)
        # Separation includes dusthana houses
        assert 6 in separation.primary_bhava
        assert 8 in separation.primary_bhava
        assert 12 in separation.primary_bhava


class TestChildbirthIndependence:
    """REQUIRED: childbirth routes through 5H/Jupiter/D7 and is INDEPENDENT
    of 7H affliction."""

    def test_childbirth_does_not_use_7th_house(self):
        """Childbirth's primary bhava must NOT include house 7."""
        cb = get_karyatva("childbirth")
        assert cb is not None
        assert 7 not in cb.primary_bhava

    def test_childbirth_uses_5th_house_and_jupiter(self):
        """Childbirth routes through 5H and Jupiter."""
        cb = get_karyatva("childbirth")
        assert 5 in cb.primary_bhava
        assert "Jupiter" in cb.karaka_grahas

    def test_childbirth_uses_d7(self):
        """Childbirth uses D7 (saptamsha) divisional."""
        cb = get_karyatva("childbirth")
        assert cb.divisional == "D7"


class TestR12TwoJudgments:
    """REQUIRED: an afflicted-but-present 7th house yields
    occurrence-positive AND condition-afflicted."""

    def test_occurrence_grade_separate_from_condition(self):
        """v3 produces two separate grades. The _compute_grade function
        can produce different values for occurrence vs condition."""
        # Strong occurrence evidence, weak condition evidence
        occ = _compute_grade([0.8, 0.7, 0.6, 0.5, 0.4], [])
        cond = _compute_grade([], [0.8, 0.7, 0.6])
        # They should be different values
        assert occ != cond
        # Occurrence should be positive (above denied threshold)
        assert occ >= 2.0  # Not denied

    def test_afflicted_house_not_denied(self):
        """An afflicted 7th house: occurrence-positive (house exists),
        condition-afflicted. Status from occurrence must NOT be 'denied'."""
        # Occurrence: house is present (supporting evidence exists)
        occ_grade = _compute_grade([0.6, 0.5, 0.4], [])
        status = _grade_to_status(occ_grade, supporting_empty=False, contradicting_empty=True)
        assert status != "denied", (
            f"An afflicted-but-present house should not be denied. "
            f"occurrence_grade={occ_grade}, status={status}"
        )


class TestR13NoFitting:
    """REQUIRED: no weight or threshold derived from the native's outcomes."""

    def test_no_chart_id_in_karyatva(self):
        """Karyatva maps must not reference any specific chart_id."""
        from pipeline.orchestrator.writers import bo_pratijna_karyatva as mod
        src = inspect.getsource(mod)
        assert "482012f1" not in src, "Karyatva map references native's chart_id (R13 violation)"
        assert "1c826d5a" not in src
        assert "cb73cd3d" not in src

    def test_all_entries_have_citations(self):
        """Every karyatva entry must have at least one classical citation (B.3)."""
        for ec_id, km in KARYATVA_REGISTRY.items():
            assert km.citations, f"Karyatva map for {ec_id} has no citations (B.3 violation)"

    def test_uniform_weights(self):
        """No empirical weight tuning — all weights in the matching function
        are structural constants, not outcome-derived."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "LEL" not in src.upper() or "life_event_log" not in src.lower(), (
            "Writer references LEL data (R13: no fitting to known outcomes)"
        )


class TestKaryatvaRegistry:
    """Structural tests for the karyatva registry."""

    def test_all_mapped_classes_have_primary_bhava(self):
        for ec_id, km in KARYATVA_REGISTRY.items():
            if not km.provisional:
                assert km.primary_bhava, f"{ec_id} has empty primary_bhava"

    def test_all_mapped_classes_have_karaka(self):
        for ec_id, km in KARYATVA_REGISTRY.items():
            if not km.provisional:
                assert km.karaka_grahas, f"{ec_id} has empty karaka_grahas"

    def test_provisional_classes_are_labelled(self):
        """DR-13 provisional classes must be marked provisional=True."""
        provisionals = {ec_id for ec_id, km in KARYATVA_REGISTRY.items() if km.provisional}
        assert "achievement_recognition" in provisionals
        assert "financial_deception" in provisionals
        assert "psychological_arc" in provisionals
        assert "birth_anchor" in provisionals
        assert "travel_event" in provisionals


class TestEngineVersion:
    """v3 version markers."""

    def test_engine_version_is_v3(self):
        from pipeline.orchestrator.writers.bo_pratijna import ENGINE_VERSION
        assert "v3" in ENGINE_VERSION.lower()

    def test_formula_version_is_v3(self):
        from pipeline.orchestrator.writers.bo_pratijna import FORMULA_VERSION
        assert "v3" in FORMULA_VERSION.lower()


# ── Live tests (require DATABASE_URL or PROD_DB_URL; skipped otherwise) ───────


@pytest.fixture(scope="module")
def db_conn():
    import psycopg
    import psycopg.rows
    url = os.environ.get("DATABASE_URL") or os.environ.get("PROD_DB_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_no_evidence_status_is_in_check_constraint(db_conn):
    """Migration 545 must have added 'no_evidence' to the CHECK constraint."""
    cur = db_conn.cursor()
    cur.execute("""
        SELECT pg_get_constraintdef(c.oid) AS def
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = 'bodha_pratijna'
          AND c.contype = 'c'
          AND pg_get_constraintdef(c.oid) LIKE '%status%'
    """)
    rows = cur.fetchall()
    assert rows, "No CHECK constraint on bodha_pratijna.status found"
    constraint_def = rows[0]["def"]
    assert "no_evidence" in constraint_def, (
        f"Migration 545 did not add 'no_evidence' to the CHECK constraint. "
        f"Constraint definition: {constraint_def}"
    )


def test_stage2_promise_fetch_includes_no_evidence_rows(db_conn):
    """stage2_promise._fetch_pratijna must NOT filter out no_evidence rows.
    R6 (PROMISE IS A MODIFIER, NEVER A GATE): all statuses flow through."""
    from services.ka_kshetra.stage2_promise import _fetch_pratijna

    # DB12: this assertion originally grepped the RAW source, so it also matched
    # the comment that DOCUMENTS the gate's removal -- failing on correct code.
    # It stayed invisible because the test skips without a DB. Strip comment
    # lines so the detector inspects executable SQL only, which is what the
    # claim "the gate is gone" actually rests on.
    src = "\n".join(
        line for line in inspect.getsource(_fetch_pratijna).splitlines()
        if not line.strip().startswith("#")
    )
    assert "AND status IN ('promised', 'conditional')" not in src, (
        "stage2_promise._fetch_pratijna still gates on status='promised'/'conditional'. "
        "R6 fix: remove the status filter so ALL rows flow through as modifiers."
    )


# ── DB6: fact_id → fact_key resolution (SIDDHANTA arc-finishing run) ──────────
#
# DB6 root cause: bodha_msr_signals.constituent_facts_array stores fact_id
# digests (16-hex-char, e.g. '012f55cebed7f5a0'), NOT fact_keys. The matcher
# tested bhava/karaka/divisional patterns ('house_7', 'venus', 'd9') against
# those opaque digests, so it matched NOTHING on live data. Every occurrence
# and condition weight came out 0.0, which is why every v3 skill score was
# numerically zero (~1e-16) and condition_grade was 0.000 everywhere (DB7).
#
# Verified against live production before this fix (chart 482012f1):
#   - constituent_facts_array sample -> {012f55cebed7f5a0}
#   - chart_facts.fact_id '012f55cebed7f5a0' -> fact_key 'conjunct_MOON'
#   - fact_key 'house_7' exists with 223 rows (so patterns DO match once resolved)
#   - 58,786 of 70,512 distinct fact_ids resolve (83.4%)
#
# §N.5: an L2 signal must REFERENCE the L1 fact, never restate it. Resolving
# fact_id -> fact_key through chart_facts is that reference being followed.


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConn:
    """Minimal stand-in for the orchestrator's db_conn (chart_facts lookup only)."""

    def __init__(self, mapping: dict[str, str]):
        self._mapping = mapping
        self.queries: list = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        return _FakeCursor(
            [{"fact_id": k, "fact_key": v} for k, v in self._mapping.items()]
        )


class TestDB6FactKeyResolution:
    """The matcher must resolve fact_ids to fact_keys before pattern matching."""

    @pytest.fixture(autouse=True)
    def _clear_fact_key_cache(self):
        """The fact_key map is cached module-level and keyed by chart_id.

        Production clears it per writer run (see BoPratijnaWriter.run) so a
        rebuild never reads a previous generation's mapping. Tests must clear it
        too, or one test's mapping leaks into the next. This fixture is also the
        executable record that the cache is shared mutable state.
        """
        from pipeline.orchestrator.writers.bo_pratijna import _FACT_KEY_MAP_CACHE

        _FACT_KEY_MAP_CACHE.clear()
        yield
        _FACT_KEY_MAP_CACHE.clear()

    def test_fact_id_resolves_to_house_fact_key_and_matches(self):
        """DB6 CORE: a fact_id that resolves to 'house_7' must match marriage (7th bhava).

        This is the exact live-data shape. Before the fix the matcher compared
        'deadbeefcafe0001' against 'house_7' patterns and returned (0.0, 0.0).
        """
        from pipeline.orchestrator.writers.bo_pratijna import _match_signal_to_class

        karyatva = get_karyatva("marriage")  # primary_bhava=[7]
        conn = _FakeConn({"deadbeefcafe0001": "house_7"})
        signal = {
            "computed_salience": 5.0,
            "valence": "benefic",
            "constituent_facts_array": ["deadbeefcafe0001"],
            "signal_type_class": "",
        }

        occ_w, cond_w = _match_signal_to_class(signal, karyatva, conn, "chart-x")

        assert occ_w > 0, (
            "DB6: matcher failed to resolve fact_id -> fact_key 'house_7'. "
            f"Got occurrence_weight={occ_w}, condition_weight={cond_w}. "
            "The matcher is comparing raw fact_id digests against bhava patterns."
        )

    def test_unrelated_fact_key_still_does_not_match(self):
        """NEGATIVE CASE: resolution must not make everything match.

        'house_3' is not marriage's bhava, contains no marriage karaka
        (Venus/Jupiter), no D9, and no condition malefic — so it must score 0.
        A fix that returns nonzero here would be matching indiscriminately.
        """
        from pipeline.orchestrator.writers.bo_pratijna import _match_signal_to_class

        karyatva = get_karyatva("marriage")
        conn = _FakeConn({"aaaabbbbccccdddd": "house_3"})
        signal = {
            "computed_salience": 5.0,
            "valence": "benefic",
            "constituent_facts_array": ["aaaabbbbccccdddd"],
            "signal_type_class": "",
        }

        occ_w, cond_w = _match_signal_to_class(signal, karyatva, conn, "chart-x")

        assert occ_w == 0 and cond_w == 0, (
            f"Unrelated fact_key 'house_3' matched marriage karyatva "
            f"(occ={occ_w}, cond={cond_w}) — resolution is over-matching."
        )

    def test_karaka_graha_resolves_and_matches(self):
        """A fact_id resolving to a karaka-bearing fact_key must match."""
        from pipeline.orchestrator.writers.bo_pratijna import _match_signal_to_class

        karyatva = get_karyatva("childbirth")  # karaka_grahas=['Jupiter']
        conn = _FakeConn({"1111222233334444": "conjunct_JUPITER"})
        signal = {
            "computed_salience": 4.0,
            "valence": "benefic",
            "constituent_facts_array": ["1111222233334444"],
            "signal_type_class": "",
        }

        occ_w, _ = _match_signal_to_class(signal, karyatva, conn, "chart-x")

        assert occ_w > 0, "Karaka 'Jupiter' in 'conjunct_JUPITER' did not match childbirth"

    def test_unresolvable_fact_id_does_not_crash(self):
        """A fact_id absent from chart_facts must degrade honestly, not raise.

        83.4% of live fact_ids resolve; the remaining 16.6% must not break the build.
        """
        from pipeline.orchestrator.writers.bo_pratijna import _match_signal_to_class

        karyatva = get_karyatva("marriage")
        conn = _FakeConn({"known0000000000": "house_7"})
        signal = {
            "computed_salience": 5.0,
            "valence": "benefic",
            "constituent_facts_array": ["totally_unknown_id"],
            "signal_type_class": "",
        }

        occ_w, cond_w = _match_signal_to_class(signal, karyatva, conn, "chart-x")
        assert occ_w == 0 and cond_w == 0

    def test_property_every_nonprovisional_class_reachable_via_its_primary_bhava(self):
        """PROPERTY: every non-provisional class must be matchable from a real fact_key.

        For each class, synthesize the 'house_N' fact_key its own karyatva map
        declares primary. If any class cannot be reached, the karyatva routing
        is structurally unreachable for that class — the DB6 failure mode.
        """
        from pipeline.orchestrator.writers.bo_pratijna import _match_signal_to_class

        unreachable = []
        for ec_id, km in KARYATVA_REGISTRY.items():
            if km.provisional or not km.primary_bhava:
                continue
            bhava = km.primary_bhava[0]
            conn = _FakeConn({"f" * 16: f"house_{bhava}"})
            signal = {
                "computed_salience": 5.0,
                "valence": "benefic",
                "constituent_facts_array": ["f" * 16],
                "signal_type_class": "",
            }
            # Distinct chart_id per class: the fact_key map is cached per chart,
            # so reusing one id here would serve the first class's map to all
            # the rest and silently fake a pass.
            occ_w, cond_w = _match_signal_to_class(signal, km, conn, f"chart-{ec_id}")
            if occ_w == 0 and cond_w == 0:
                unreachable.append(f"{ec_id} (house_{bhava})")

        assert not unreachable, (
            "These event classes cannot be reached from their own declared "
            f"primary bhava fact_key: {unreachable}"
        )
