"""Tests for the bo_pratijna writer (Promise Register, L2 Bodha), PRATIJÑĀ v4.1.0
(R22 adoption, F1 default-on, 2026-08-09).
G10 varga_confirmation (SAMPURTI L0e, 2026-08-10): cross-ayanamsha consensus
tests added in TestVargaConfirmationConsensus.

Two tiers, matching the project's established writer-test convention:

1. Offline (always runs, no DB required): the pure, DB-free status-mapping
   logic (`status_from_occurrence_label`), row-shaping logic
   (`_row_for_score`, `_varga_confirmation_consensus`, `_divisional_entry_from_ledger`),
   and structural checks against the writer's source.
2. Live (skipped unless DBURL/DATABASE_URL/PROD_DB_URL is set): Rung P6, the
   PRATIJÑĀ v4 writer-wiring acceptance gate -- a REAL orchestrated
   `run(ctx)` call against chart 482012f1, followed by reading the rows
   back out of `bodha_pratijna` and diffing them against Rung P5's offline
   engine output (`bo_pratijna_v4_engine.PratijnaV4Engine`, the exact same
   library the writer wraps) for byte/numeric agreement.

This file supersedes the v3-era test suite (BUG-1/2/3, DB6 fact_id->
fact_key resolution, `_partition_signal`/`_match_signal_to_class` unit
tests) -- those exercised the MSR-signal-partition matcher that v4 retires
entirely (see bo_pratijna.py's module docstring, "What replaced what").
The v3 property tests that remain load-bearing under v4 (marriage != separation
with genuinely distinct evidence; childbirth independent of the 7th house)
are re-expressed here directly against the v4 engine's own KARYATVA_REGISTRY
-- which is unchanged infrastructure this lane does not touch -- and against
live engine output, which is a STRONGER form of the same guarantee than the
v3 structural-only checks were.
"""
from __future__ import annotations

import inspect
import os

import pytest

from pipeline.orchestrator.writers.bo_pratijna import (
    CANONICAL_AYAS,
    DEFAULT_AMENDMENTS,
    ENGINE_VERSION,
    FORMULA_VERSION,
    _divisional_entry_from_ledger,
    _row_for_score,
    _varga_confirmation_consensus,
    status_from_occurrence_label,
)
from pipeline.orchestrator.writers.bo_pratijna_karyatva import (
    KARYATVA_REGISTRY,
    get_karyatva,
)
from pipeline.orchestrator.writers.bo_pratijna_v4_engine import ClassScore


# ── Offline tests: pure logic, no DB ──────────────────────────────────────────


class TestStatusMapping:
    """The central design decision of this lane: §6.1 occurrence band ->
    the pre-existing 4-value `status` column. See bo_pratijna.py's module
    docstring for the full R13/R16 reasoning; these tests pin the mapping
    table itself so a future edit cannot silently change it."""

    def test_denied_band_maps_to_denied(self):
        assert status_from_occurrence_label("DENIED") == "denied"

    def test_weak_band_maps_to_conditional(self):
        assert status_from_occurrence_label("WEAK") == "conditional"

    def test_moderate_band_maps_to_conditional(self):
        assert status_from_occurrence_label("MODERATE") == "conditional"

    def test_strong_band_maps_to_promised(self):
        assert status_from_occurrence_label("STRONG") == "promised"

    def test_very_strong_band_maps_to_promised(self):
        assert status_from_occurrence_label("VERY_STRONG") == "promised"

    def test_unknown_band_raises_rather_than_guessing(self):
        """An honest failure (§N.7 item 6) beats silently defaulting an
        unrecognized band to some plausible-looking status."""
        with pytest.raises(ValueError):
            status_from_occurrence_label("NOT_A_REAL_BAND")

    def test_mapping_is_monotonic_in_band_order(self):
        """No band maps to a 'worse' status than an earlier (lower-
        occurrence) band -- a mapping that let a higher occurrence score
        yield a nominally worse status would contradict §6.1's own
        ordering and is exactly the kind of defect this test exists to
        catch mechanically, not just by code review."""
        order = ["DENIED", "WEAK", "MODERATE", "STRONG", "VERY_STRONG"]
        rank = {"denied": 0, "conditional": 1, "promised": 2}
        statuses = [status_from_occurrence_label(b) for b in order]
        ranks = [rank[s] for s in statuses]
        assert ranks == sorted(ranks), (
            f"Status mapping is not monotonic in band order: {list(zip(order, statuses))}"
        )

    def test_mapping_covers_every_band_the_engine_can_emit(self):
        """Every label bo_pratijna_v4_engine.occurrence_band() can return
        must have a mapping entry -- a live KeyError mid-build would be a
        writer defect, not an engine defect."""
        from pipeline.orchestrator.writers.bo_pratijna_v4_engine import (
            OCCURRENCE_BANDS,
        )

        for _lo, _hi, label in OCCURRENCE_BANDS:
            # Must not raise.
            status_from_occurrence_label(label)


class TestRowShaping:
    """`_row_for_score` -- the pure function that turns one engine
    ClassScore into one bodha_pratijna row dict, independent of any DB."""

    def _scored(self, **overrides) -> ClassScore:
        base = dict(
            event_class_id="marriage",
            status="scored",
            occurrence=0.321,
            occurrence_label="WEAK",
            condition=5.83,
            condition_label="MODERATE",
            occurrence_pre_denial=0.4,
            factor_ledger=[
                {"slot": "house_lord", "house": 7, "band": 0.6},
                {"slot": "divisional", "varga": "D9", "graha": "Venus",
                 "band": 0.8, "dignity_state": "friend"},
            ],
            denials=[{"config_id": "CFG-1", "fired": False, "deduction": 0.0, "reason": "n/a"}],
            condition_ledger=[{"malefic": "Saturn", "contribution": 0.5}],
            weights=[{"slot": "house_lord", "item": "7", "weight": 0.5}],
            provenance=[{"source_table": "chart_divisionals", "id_kind": "chart_divisionals_id", "id": "x"}],
        )
        base.update(overrides)
        return ClassScore(**base)

    def test_no_evidence_row_has_no_evidence_status_and_null_grades(self):
        score = ClassScore(event_class_id="birth_anchor", status="no_evidence")
        row = _row_for_score(
            chart_id="c1", aya="lahiri_chitrapaksha", build_id="b1",
            event_class_id="birth_anchor", score=score, now="2026-08-09T00:00:00Z",
        )
        assert row["status"] == "no_evidence"
        assert row["grade"] is None
        assert row["occurrence_grade"] is None
        assert row["condition_grade"] is None

    def test_scored_row_carries_v4_native_occurrence_and_condition(self):
        score = self._scored()
        row = _row_for_score(
            chart_id="c1", aya="lahiri_chitrapaksha", build_id="b1",
            event_class_id="marriage", score=score, now="2026-08-09T00:00:00Z",
        )
        assert row["occurrence_grade"] == 0.321, "occurrence_grade must carry the v4-native [0,1] value"
        assert row["condition_grade"] == 5.83, "condition_grade must carry the v4-native [0,10] value"
        assert row["status"] == "conditional"  # WEAK -> conditional

    def test_grade_is_occurrence_rescaled_to_legacy_0_to_10_scale(self):
        """Legacy-compatibility rescale for NOT-YET-AUDITED downstream
        consumers (ph_nimitta/ka_taranga/ka_yojaka) that read `grade` on
        the old [0,10] 'higher = more promised' scale."""
        score = self._scored(occurrence=0.321)
        row = _row_for_score(
            chart_id="c1", aya="lahiri_chitrapaksha", build_id="b1",
            event_class_id="marriage", score=score, now="2026-08-09T00:00:00Z",
        )
        assert row["grade"] == pytest.approx(3.21)

    def test_supporting_and_contradicting_signal_ids_are_always_null(self):
        """v4 never reads bodha_msr_signals -- these columns have nothing
        honest to hold (see module docstring, disclosed capability gap)."""
        score = self._scored()
        row = _row_for_score(
            chart_id="c1", aya="lahiri_chitrapaksha", build_id="b1",
            event_class_id="marriage", score=score, now="2026-08-09T00:00:00Z",
        )
        assert row["supporting_signal_ids"] is None
        assert row["contradicting_signal_ids"] is None

    def test_varga_confirmation_populated_when_passed_in(self):
        """varga_confirmation is passed in from the pre-computed consensus;
        _row_for_score only serialises it to JSON — it does not compute it."""
        score = self._scored()
        consensus = {"varga": "D9", "graha": "Venus", "unanimous": True,
                     "per_system": {}, "consensus_dignity": "friend",
                     "dissent": [], "source": "test"}
        row = _row_for_score(
            chart_id="c1", aya="lahiri_chitrapaksha", build_id="b1",
            event_class_id="marriage", score=score, now="2026-08-09T00:00:00Z",
            varga_confirmation=consensus,
        )
        assert row["varga_confirmation"] is not None
        assert "D9" in row["varga_confirmation"]

    def test_varga_confirmation_null_when_none_passed(self):
        score = self._scored()
        row = _row_for_score(
            chart_id="c1", aya="lahiri_chitrapaksha", build_id="b1",
            event_class_id="marriage", score=score, now="2026-08-09T00:00:00Z",
            varga_confirmation=None,
        )
        assert row["varga_confirmation"] is None

    def test_derivation_carries_full_ledger_and_labels(self):
        """B.3 traceability: the full factor_ledger/denials/condition_ledger/
        provenance must land in the DB row's derivation JSONB, not be
        computed-and-discarded."""
        score = self._scored()
        row = _row_for_score(
            chart_id="c1", aya="lahiri_chitrapaksha", build_id="b1",
            event_class_id="marriage", score=score, now="2026-08-09T00:00:00Z",
        )
        import json
        derivation = json.loads(row["derivation"])
        assert derivation["occurrence_label"] == "WEAK"
        assert derivation["condition_label"] == "MODERATE"
        assert derivation["factor_ledger"] == score.factor_ledger
        assert derivation["denials"] == score.denials
        assert derivation["condition_ledger"] == score.condition_ledger
        assert derivation["provenance"] == score.provenance
        assert "status_mapping_rule" in derivation

    def test_divisional_entry_helper_returns_none_for_empty_ledger(self):
        """_divisional_entry_from_ledger references the engine's factor_ledger;
        an empty ledger (no divisional slot scored) correctly returns None."""
        assert _divisional_entry_from_ledger(ClassScore(event_class_id="x", status="scored", factor_ledger=[])) is None

    def test_divisional_entry_helper_returns_entry_when_slot_present(self):
        score = self._scored()  # includes a divisional slot in factor_ledger
        entry = _divisional_entry_from_ledger(score)
        assert entry is not None
        assert entry["slot"] == "divisional"
        assert entry["varga"] == "D9"


# ── Structural / source checks ─────────────────────────────────────────────


def _executable_source(mod) -> str:
    """`inspect.getsource(mod)` minus the leading module docstring.

    The module docstring legitimately DISCUSSES what v3 used to do and
    cites the native's chart_id in its R13 reasoning (the same disclosure
    pattern `bo_pratijna_v4_engine.py`'s own docstring uses, independently
    PARĪKṢAKA-verified PASS) -- a structural check for "is this string used
    in executable code" must not flag prose that explains why it is
    ABSENT from executable code. Mirrors the DB12 comment-stripping fix
    already established in this same test file's history for exactly this
    false-positive class."""
    src = inspect.getsource(mod)
    # The module docstring is the first triple-quoted block starting at
    # the top of the file.
    first = src.find('"""')
    second = src.find('"""', first + 3)
    if first == 0 and second != -1:
        return src[second + 3:]
    return src


class TestSourceStructure:
    def test_writer_does_not_import_msr_signals(self):
        """v4 must not read bodha_msr_signals -- reusing that path would
        reintroduce the exact retired defect class. Scoped to executable
        code (see `_executable_source`) -- the module docstring's own
        "what replaced what" section legitimately names the retired table
        as part of explaining why it is gone."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = _executable_source(mod)
        assert "bodha_msr_signals" not in src, (
            "Writer still references bodha_msr_signals -- the v3 MSR-signal-"
            "partition path this campaign exists to retire"
        )

    def test_writer_uses_chart_reader_v4(self):
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "ChartReaderV4" in src
        assert "PratijnaV4Engine" in src

    def test_engine_version_is_v4(self):
        assert "v4" in ENGINE_VERSION.lower()

    def test_formula_version_is_v4(self):
        assert "v4" in FORMULA_VERSION.lower()

    def test_writer_never_commits_or_closes_connection(self):
        """§N.2 FROZEN contract: writers never call commit/rollback/close
        on ctx.db_conn."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "db_conn.commit" not in src
        assert "db_conn.close" not in src
        assert "conn.commit()" not in src
        assert "conn.close()" not in src

    def test_writer_does_not_write_asset_throughput(self):
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "asset_throughput" not in src

    def test_delete_then_insert_idempotency_preserved(self):
        """§N.3: per-chart delete-then-insert, unchanged from v3."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "DELETE FROM bodha_pratijna WHERE chart_id=%s" in src
        assert "ON CONFLICT (chart_id, ayanamsha_id, event_class_id)" in src


# ── R13 checks (carried from v3; unchanged infrastructure) ────────────────


class TestR13NoFitting:
    def test_no_chart_id_in_writer(self):
        """Scoped to executable code (see `_executable_source`): the module
        docstring's design-decision reasoning DISCLOSES the Rung P5
        reference numbers computed on chart 482012f1 (the same disclosure
        pattern `bo_pratijna_v4_engine.py`'s own docstring already uses,
        independently PARĪKṢAKA-verified PASS) -- that is R13 transparency,
        not a violation. The violation this test actually guards against is
        the chart_id appearing in EXECUTABLE code (a conditional branch, a
        hardcoded constant used in control flow)."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = _executable_source(mod)
        assert "482012f1" not in src, "Writer references native's chart_id (R13 violation)"
        assert "1c826d5a" not in src

    def test_status_mapping_thresholds_documented_not_hardcoded_secretly(self):
        """The mapping table itself is a plain dict (no chart-conditional
        branches) -- the strongest structural evidence against R13
        fitting available to a source-inspection test."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod.status_from_occurrence_label)
        assert "chart_id" not in src
        assert "if event_class_id" not in src


class TestMarriageNotEqualSeparation:
    """REQUIRED (carried from v3, re-expressed against v4 infrastructure):
    marriage and separation must have structurally different karyatva
    routes. This is unchanged KARYATVA_REGISTRY infrastructure this lane
    does not touch; the live version of this guarantee is re-verified in
    the Rung P6 live test below, using genuinely distinct occurrence/
    condition values, not just structural KaryatvaMap distinctness."""

    def test_different_karyatva_maps(self):
        marriage = get_karyatva("marriage")
        separation = get_karyatva("separation")
        assert marriage is not None
        assert separation is not None
        assert not marriage.dusthana_required
        assert separation.dusthana_required
        assert set(marriage.karaka_grahas) != set(separation.karaka_grahas)


class TestChildbirthIndependence:
    def test_childbirth_does_not_use_7th_house(self):
        cb = get_karyatva("childbirth")
        assert cb is not None
        assert 7 not in cb.primary_bhava

    def test_childbirth_uses_5th_house_and_jupiter(self):
        cb = get_karyatva("childbirth")
        assert 5 in cb.primary_bhava
        assert "Jupiter" in cb.karaka_grahas


class TestKaryatvaRegistryCoverage:
    def test_all_27_event_classes_covered(self):
        """B0's registry-harmonization lane added `parental_event`, closing
        the 26/27 gap V4_RUBRIC_SPEC_v1_0.md §7 flagged. The writer's
        per-ayanamsha loop iterates `engine.score_all()`, which is keyed by
        KARYATVA_REGISTRY -- so this count IS the per-ayanamsha row count."""
        assert len(KARYATVA_REGISTRY) == 27


class TestCanonicalAyanamshas:
    def test_five_canonical_ayanamshas(self):
        assert len(CANONICAL_AYAS) == 5
        assert "lahiri_chitrapaksha" in CANONICAL_AYAS


class TestVargaConfirmationConsensus:
    """G10 (SAMPURTI L0e): _varga_confirmation_consensus builds the
    cross-ayanamsha consensus JSON. §N.5 discipline: it only REFERENCES
    the engine's already-computed factor_ledger entries; it never re-derives
    sign positions or dignity states from raw chart data."""

    def _div_entry(self, aya: str, varga_sign: str, dignity_state: str, band: float) -> dict:
        return {
            "slot": "divisional", "varga": "D10", "graha": "Mercury",
            "varga_sign": varga_sign, "dignity_state": dignity_state, "band": band,
        }

    def test_all_none_returns_none(self):
        """Classes with no divisional in their KaryatvaMap (e.g. birth_anchor
        for which the kill_switch makes scoring moot) produce None."""
        per_aya = {aya: None for aya in CANONICAL_AYAS}
        assert _varga_confirmation_consensus(per_aya) is None

    def test_unanimous_consensus_all_five_agree(self):
        per_aya = {
            aya: self._div_entry(aya, "Capricorn", "great_enemy", 0.2)
            for aya in CANONICAL_AYAS
        }
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert result["unanimous"] is True
        assert result["consensus_dignity"] == "great_enemy"
        assert result["dissent"] == []
        assert len(result["per_system"]) == 5
        assert result["varga"] == "D10"
        assert result["graha"] == "Mercury"

    def test_dissent_when_one_system_differs(self):
        per_aya = {aya: self._div_entry(aya, "Capricorn", "great_enemy", 0.2)
                   for aya in CANONICAL_AYAS}
        # Override one ayanamsha to a different sign/dignity
        raman_entry = self._div_entry("raman", "Aquarius", "own", 0.8)
        per_aya["raman"] = raman_entry
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert result["unanimous"] is False
        assert result["consensus_dignity"] == "great_enemy"  # 4 vs 1 -> majority
        assert len(result["dissent"]) == 1
        assert result["dissent"][0]["ayanamsha_id"] == "raman"
        assert result["dissent"][0]["dignity_state"] == "own"

    def test_no_majority_consensus_dignity_is_none(self):
        """3-way split (or balanced split) -> consensus_dignity=None, not a guess."""
        ayas = list(CANONICAL_AYAS)
        # 2 agree on A, 2 agree on B, 1 agrees on C -> tie between A and B
        dignities = ["great_enemy", "great_enemy", "own", "own", "neutral"]
        per_aya = {
            aya: self._div_entry(aya, "Capricorn", dig, 0.5)
            for aya, dig in zip(ayas, dignities)
        }
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert result["unanimous"] is False
        assert result["consensus_dignity"] is None  # tie, honest null not a guess

    def test_partial_none_entries_scored_by_available_systems(self):
        """If only 3 of 5 ayanamshas have a divisional entry (None for 2),
        consensus is built from the 3 that are present."""
        per_aya = {aya: None for aya in CANONICAL_AYAS}
        present_ayas = list(CANONICAL_AYAS)[:3]
        for aya in present_ayas:
            per_aya[aya] = self._div_entry(aya, "Capricorn", "great_enemy", 0.2)
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert len(result["per_system"]) == 3
        assert result["unanimous"] is True  # all 3 present ones agree
        assert result["consensus_dignity"] == "great_enemy"

    def test_source_field_documents_g10_provenance(self):
        """§N.7 item 1: the source field must state the G10 reference path,
        not a generic or invented string."""
        per_aya = {
            aya: self._div_entry(aya, "Capricorn", "great_enemy", 0.2)
            for aya in CANONICAL_AYAS
        }
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert "G10" in result["source"]
        assert "§N.5" in result["source"]


# ── Live tests (require DBURL/DATABASE_URL/PROD_DB_URL; skipped otherwise) ────


CHART_482012F1 = "482012f1-710e-4a25-994a-93821f5871aa"
_LIVE_AYA = "lahiri_chitrapaksha"

# v4.1.0 numbers (R22 adoption, F1 default-on 2026-08-09) -- source of the
# new expected values is F1_SIDE_BY_SIDE_v1_0.md §1: marriage moves
# 0.321->0.450 (WEAK->MODERATE, the sole band-crossing cell in the whole
# 54-cell sweep) and separation moves 0.505->0.575 (stays MODERATE);
# childbirth is one of the 17 unmoved classes on this chart (byte-identical
# v4.0/v4.1), so its expected value is unchanged. Condition (5.83/8.75/7.50)
# is unchanged for all three -- Δcondition = 0.000 structurally, per
# F1_SIDE_BY_SIDE_v1_0.md's own §5.2 analysis (the dignity-band amendment
# cannot touch the condition axis's disjoint inputs).
RUNG_P3_EXPECTED = {
    "marriage": (0.450, 5.83),
    "separation": (0.575, 8.75),
    "childbirth": (0.593, 7.50),
}


def _get_dburl() -> str | None:
    return os.environ.get("DBURL") or os.environ.get("DATABASE_URL") or os.environ.get("PROD_DB_URL")


@pytest.fixture(scope="module")
def db_conn():
    import psycopg
    import psycopg.rows

    url = _get_dburl()
    if not url:
        pytest.skip("DBURL/DATABASE_URL/PROD_DB_URL not set")
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.close()


class TestRungP6LiveWriteThenRead:
    """Rung P6 -- the PRATIJÑĀ v4 writer-wiring acceptance gate (BLOCKING).

    Runs the REAL writer (`BoPratijnaWriter.run(ctx)`) against chart
    482012f1 -- one full orchestrated run, all 27 event classes x 5
    canonical ayanamshas, 135 rows -- then COMMITS (see "why a real commit"
    below), reads the rows straight back with a plain SELECT, and diffs
    them against a freshly-recomputed offline engine call (`PratijnaV4Engine.
    score_class`, the exact same library the writer wraps, called directly
    -- not read back from the writer's own output) for exact numeric
    agreement, transitively also confirming agreement with RUNG_P3's own
    hand-worked reference numbers (Lane B2 / Rung P5).

    Why a REAL commit, not a rollback-scoped write: this writer's own
    delete-then-insert idempotency (§N.3) makes a committed re-run safe to
    repeat with no accretion -- any later real orchestrator build of this
    chart deletes and replaces these exact rows. The task brief for this
    lane explicitly authorizes this ("If you can safely test-write into
    bodha_pratijna for chart 482012f1 ... do the real live round-trip").
    Committing (vs. holding a multi-minute transaction open for a manual
    rollback) also avoids a real failure mode this test suite hit during
    development: 5 ayanamshas x 27 classes x several DB round-trips each
    through cloud-sql-proxy runs several minutes, and holding that whole
    span in ONE open transaction risked (and, once, hit) the connection
    being dropped before an explicit rollback could complete -- a
    connection-liveness problem, not a correctness one (the transaction
    aborts safely server-side on disconnect either way), but avoided
    entirely by committing promptly instead. This DOES mean the test
    leaves real v4-scored `bodha_pratijna` rows for chart 482012f1 in the
    database after it runs -- that is the intended, disclosed effect of
    wiring this writer, not an accidental side effect.
    """

    def test_writer_run_matches_offline_engine_on_reference_classes(self, db_conn):
        from brahmagyan.chart_reader_v4 import ChartReaderV4
        from pipeline.orchestrator.writers import ContextSpec
        from pipeline.orchestrator.writers.bo_pratijna import BoPratijnaWriter
        from pipeline.orchestrator.writers.bo_pratijna_v4_engine import PratijnaV4Engine

        conn = db_conn
        build_id = "00000000-0000-4000-8000-000000000006"  # fixed test build_id

        # ── 1. Run the REAL writer, through the REAL ContextSpec/WriterBase
        #      path -- one full orchestrated run, all 27 classes x 5
        #      ayanamshas -- then commit (see class docstring). ──
        ctx = ContextSpec(
            asset_id="bo_pratijna",
            build_id=build_id,
            db_conn=conn,
            config={"chart_id": CHART_482012F1},
        )
        writer = BoPratijnaWriter()
        writer.asset_id = "bo_pratijna"
        result = writer.run(ctx)
        conn.commit()

        assert result.rows_inserted == 27 * 5, (
            f"Expected 27 event classes x 5 ayanamshas = 135 rows; got {result.rows_inserted}"
        )

        # ── 2. Read the COMMITTED rows straight back out ──
        cur = conn.execute(
            """
            SELECT event_class_id, status, occurrence_grade, condition_grade,
                   engine_version, formula_version, derivation
            FROM bodha_pratijna
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND event_class_id = ANY(%s)
            ORDER BY event_class_id
            """,
            (CHART_482012F1, _LIVE_AYA, list(RUNG_P3_EXPECTED.keys())),
        )
        db_rows = {r["event_class_id"]: r for r in cur.fetchall()}
        conn.commit()

        assert set(db_rows.keys()) == set(RUNG_P3_EXPECTED.keys()), (
            f"Expected rows for {sorted(RUNG_P3_EXPECTED.keys())}, got {sorted(db_rows.keys())}"
        )

        # ── 3. A FRESH offline engine call, scoped to just the 3 reference
        #      classes (not a redundant full score_all() -- the writer's
        #      own run() above already exercised all 27 x 5; re-scoring to
        #      just marriage/separation/childbirth is the byte-agreement
        #      check this rung requires without doubling the DB round-trip
        #      cost of the whole 135-row run). ──
        reader = ChartReaderV4(conn, ayanamsha=_LIVE_AYA)
        # DEFAULT_AMENDMENTS ({'F1'}, R22 adoption) -- must match the
        # writer's own production default exactly, or this "offline vs DB
        # row" agreement check would compare a v4.1-written row against a
        # v4.0-scored offline recomputation and fail spuriously.
        engine = PratijnaV4Engine(reader, amendments=DEFAULT_AMENDMENTS)
        offline_scores = {
            event_class_id: engine.score_class(CHART_482012F1, event_class_id)
            for event_class_id in RUNG_P3_EXPECTED
        }
        conn.commit()

        # ── 4. Byte/numeric-agreement diff: DB row vs offline engine vs
        #      RUNG_P3's own hand-worked numbers (transitively) ──
        mismatches = []
        for event_class_id, (exp_occ, exp_cond) in RUNG_P3_EXPECTED.items():
            db_row = db_rows[event_class_id]
            offline = offline_scores[event_class_id]

            db_occ = float(db_row["occurrence_grade"])
            db_cond = float(db_row["condition_grade"])

            if db_occ != offline.occurrence:
                mismatches.append(
                    f"{event_class_id}: DB occurrence_grade={db_occ} != "
                    f"offline engine occurrence={offline.occurrence}"
                )
            if db_cond != offline.condition:
                mismatches.append(
                    f"{event_class_id}: DB condition_grade={db_cond} != "
                    f"offline engine condition={offline.condition}"
                )
            if db_occ != exp_occ:
                mismatches.append(
                    f"{event_class_id}: DB occurrence_grade={db_occ} != "
                    f"RUNG_P3 expected={exp_occ}"
                )
            if db_cond != exp_cond:
                mismatches.append(
                    f"{event_class_id}: DB condition_grade={db_cond} != "
                    f"RUNG_P3 expected={exp_cond}"
                )

        assert not mismatches, "Rung P6 FAILED:\n" + "\n".join(mismatches)

        # ── 5. Engine/formula version + status-mapping sanity on the
        #      written rows ──
        for event_class_id in RUNG_P3_EXPECTED:
            db_row = db_rows[event_class_id]
            assert db_row["engine_version"] == ENGINE_VERSION
            assert db_row["formula_version"] == FORMULA_VERSION
            assert db_row["status"] in ("promised", "denied", "conditional", "no_evidence")
            assert db_row["derivation"] is not None

        # ── 6. marriage != separation on the LIVE written rows (the exact
        #      checkpoint question this campaign exists to answer) ──
        m, s = db_rows["marriage"], db_rows["separation"]
        assert m["occurrence_grade"] != s["occurrence_grade"]
        assert m["condition_grade"] != s["condition_grade"]
