"""WP3c resonance corrections R-1..R-6 (N-12 pre-approved honesty fixes).

Golden tests per correction, using the WP1 golden-case fixtures at
tests/l3/gochara/fixtures/wp1_target_resolution.json where the case shape
exists, plus writer-level fake-conn integration for the build-time
validation and the build record (WriterResult notes).

Corrections under test (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §WP3c,
WP1_CONTRACTS.md §2, GOCHARA_RULING_SHEET_v1_0 N-12):
  R-1 negative sensitive_degree facts -> ZERO rows; positives kept
  R-2 arudha rows typed sign-level (cusp placeholder never a degree)
  R-3 yoga ids validated against live firings; drift pinned in notes
  R-4 lord resolution per WP1 contract; 'unqualified' on rulership gap
  R-5 'afflicted' qualifier preserved; first root retained, discards counted
  R-6 target_resolution_state on every emitted row; migration file shape
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_gochara_resonance.writer import (  # noqa: E402
    _CLASSICAL_SIGN_LORDS,
    _NEGATIVE_SENSITIVE_VALUES,
    _POSITIVE_SENSITIVE_VALUES,
    _TARGET_RESOLUTION_STATES,
    _build_lord_rows,
    _build_wp3c_notes,
    _resolve_lord_ref,
    build_resonance_rows,
)
from services.ka_gochara_resonance.writer import (  # noqa: E402
    _fetch_chart_resolution_context,
    _stamp_target_resolution,
)

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures/wp1_target_resolution.json").read_text()
)
MIGRATION_1071 = (
    Path(__file__).parent.parent.parent.parent.parent
    / "migrations/1080_nirmana_l3_gochara_resonance_target_resolution_state.sql"
)

RESOLVED_STATES = set(_TARGET_RESOLUTION_STATES)
_USE_DEFAULT_LORDS = object()


def _case(name: str) -> dict:
    return FIXTURES["cases"][name]


def _facts_of(case_name: str, fact_category: str) -> list[dict]:
    return [f for f in _case(case_name)["inputs"]["chart_facts"]
            if f.get("fact_category") == fact_category]


def _resolution_ctx(lagna_sign_num, sign_lords=_USE_DEFAULT_LORDS,
                    present_subjects=frozenset()):
    return {
        "lagna_sign_num": lagna_sign_num,
        "sign_lords": _CLASSICAL_SIGN_LORDS if sign_lords is _USE_DEFAULT_LORDS
                      else sign_lords,
        "present_subjects": set(present_subjects),
    }


# ── R-1: sensitive_degree — positive results only ─────────────────────────────

class TestR1SensitivePositiveOnly:
    def test_fixture_negative_case_produces_zero_rows(self):
        """WP1 fixture neg_sensitive_check_zero_targets: a not_gandanta row
        produces ZERO targets, not a target marked negative (F-19)."""
        from services.ka_gochara_resonance.writer import _build_sensitive_degree_rows
        facts = _facts_of("neg_sensitive_check_zero_targets", "sensitive_degree_check")
        assert facts and facts[0]["fact_value_text"] == "not_gandanta"
        assert _build_sensitive_degree_rows("marriage", facts) == []

    def test_fixture_positive_case_kept_and_resolves_to_subject_graha(self):
        """WP1 fixture sensitive_degree_positive: papa_kartari on Saturn is
        kept, keyed by the check fact_id, and resolves to Saturn's own
        position row (subject recoverable; merge into graha:Saturn's
        independence_group is realized downstream)."""
        from services.ka_gochara_resonance.writer import _build_sensitive_degree_rows
        facts = _facts_of("sensitive_degree_positive", "sensitive_degree_check")
        # Shape note: the WP1 resolution fixture models the positive kartari
        # check as fact_key='papa_kartari'; the live L1 producer
        # (ga_sensitive_degree_writer.build_sensitive_degree_rows) stores
        # fact_key='kartari', fact_value_text='papa_kartari'. The writer's
        # whitelist follows the LIVE producer vocabulary — the fixture row
        # is translated here to the live shape, not the other way around.
        assert facts and facts[0]["fact_value_text"] == "papa_kartari"
        live_facts = [dict(facts[0], fact_key="kartari")]
        report = {"kept": 0, "dropped_negative": 0, "dropped_unknown_value": 0,
                  "kept_subjects": set()}
        rows = _build_sensitive_degree_rows("illness_acute", live_facts, report=report)
        assert len(rows) == 1
        assert rows[0]["target_ref"] == facts[0]["fact_id"]
        assert rows[0]["_fact_subject"] == "SAT"
        # Build-time verification: Saturn's graha_position row exists -> resolved.
        _stamp_target_resolution(rows, _resolution_ctx(1, present_subjects={"SAT"}))
        assert rows[0]["target_resolution_state"] == "resolved"
        assert "_fact_subject" not in rows[0], "internal helper key must be popped before INSERT"
        assert report["kept"] == 1 and report["dropped_negative"] == 0

    def test_all_four_negative_spellings_produce_zero_rows(self):
        from services.ka_gochara_resonance.writer import _build_sensitive_degree_rows
        facts = [
            {"fact_id": "a", "fact_subject": "MOON", "fact_key": "gandanta",
             "fact_value_text": "not_gandanta"},
            {"fact_id": "b", "fact_subject": "SAT", "fact_key": "mrityu_bhaga",
             "fact_value_text": "not_fired"},
            {"fact_id": "c", "fact_subject": "JUP", "fact_key": "pushkara",
             "fact_value_text": "not_pushkara"},
            {"fact_id": "d", "fact_subject": "MAR", "fact_key": "kartari",
             "fact_value_text": "none"},
        ]
        report = {"kept": 0, "dropped_negative": 0, "dropped_unknown_value": 0,
                  "kept_subjects": set()}
        assert _build_sensitive_degree_rows("marriage", facts, report=report) == []
        assert report["dropped_negative"] == 4  # the pinned negative vocabulary

    def test_unknown_value_dropped_and_counted_not_silent(self):
        from services.ka_gochara_resonance.writer import _build_sensitive_degree_rows
        report = {"kept": 0, "dropped_negative": 0, "dropped_unknown_value": 0,
                  "kept_subjects": set()}
        rows = _build_sensitive_degree_rows("marriage", [
            {"fact_id": "u1", "fact_subject": "VEN", "fact_key": "kartari",
             "fact_value_text": "pandita_says_maybe"},
        ], report=report)
        assert rows == []
        assert report["dropped_unknown_value"] == 1
        assert "pandita_says_maybe" not in _NEGATIVE_SENSITIVE_VALUES

    def test_positive_vocabulary_is_the_pinned_set(self):
        """The whitelist is exactly the plan-pinned positive set per key —
        no broader predicate can smuggle a negative through."""
        assert _POSITIVE_SENSITIVE_VALUES == {
            "mrityu_bhaga": frozenset({"fired"}),
            "gandanta": frozenset({"gandanta"}),
            "kartari": frozenset({"papa_kartari", "shubha_kartari"}),
            "pushkara": frozenset({"pushkara"}),
        }

    def test_subject_position_absent_honest_unavailable(self):
        """A kept positive check whose subject graha has no graha_position
        row cannot resolve to a degree -> 'unavailable', never fabricated."""
        from services.ka_gochara_resonance.writer import _build_sensitive_degree_rows
        rows = _build_sensitive_degree_rows("marriage", [
            {"fact_id": "p1", "fact_subject": "RAH_MEAN", "fact_key": "pushkara",
             "fact_value_text": "pushkara"},
        ])
        _stamp_target_resolution(rows, _resolution_ctx(1, present_subjects={"SUN"}))
        assert rows[0]["target_resolution_state"] == "unavailable"


# ── R-2: arudha typed sign-level ──────────────────────────────────────────────

class TestR2ArudhaSignLevel:
    def test_fixture_arudha_row_references_sign_fact_only(self):
        """WP1 fixture arudha_sign_interval / neg_arudha_cusp_placeholder:
        the emitted row references the SIGN fact_id; the sibling
        longitude_sidereal fact (the cusp placeholder, every live value
        exactly 30*(sign-1), F-20) is NEVER the target and never read as a
        degree."""
        from services.ka_gochara_resonance.writer import _build_arudha_rows
        for case in ("arudha_sign_interval", "neg_arudha_cusp_placeholder"):
            facts = _facts_of(case, "arudha_pada")
            sign_fact = next(f for f in facts if f["fact_key"] == "sign")
            lon_fact = next(f for f in facts if f["fact_key"] == "longitude_sidereal")
            rows = _build_arudha_rows("wealth_gain", [sign_fact])
            assert len(rows) == 1
            assert rows[0]["target_ref"] == sign_fact["fact_id"]
            assert rows[0]["target_ref"] != lon_fact["fact_id"], (
                "the cusp-placeholder longitude fact must never be the target"
            )
            assert rows[0]["target_resolution_state"] == "resolved"
            # No degree anywhere on the row: sign-level interval typing.
            assert "longitude" not in json.dumps(rows[0])

    def test_missing_sign_value_is_unavailable_not_cusp_resolved(self):
        from services.ka_gochara_resonance.writer import _build_arudha_rows
        report = {"rows": 0, "invalid_sign_value": 0}
        rows = _build_arudha_rows("wealth_gain", [
            {"fact_id": "a1", "fact_subject": "A7", "fact_value_text": None},
        ], report=report)
        assert rows[0]["target_resolution_state"] == "unavailable"
        assert report["invalid_sign_value"] == 1


# ── R-3: yoga_constituent re-validation + build record ────────────────────────

class TestR3YogaRevalidation:
    def test_firing_row_constituents_carried_in_report(self):
        """The yoga fetch now selects constituent_fact_ids /
        constituent_planets (plan §5.3 resolution inputs); the build record
        pins the validated id set with constituent counts."""
        from services.ka_gochara_resonance.writer import _build_yoga_rows
        firing = _case("yoga_constituent_live")["inputs"]["ga_yoga_firings"][0]
        report = {"validated_ids": set(), "constituents": {}}
        rows = _build_yoga_rows("wealth_gain", [firing], report=report)
        assert len(rows) == 1
        assert report["validated_ids"] == {"gajakesari_yoga"}
        assert report["constituents"]["gajakesari_yoga"] == 2

    def test_dangling_yoga_id_produces_no_row_and_surfaces_in_notes(self):
        """A yoga id with no live firing row produces NO target row; if it
        existed in the prior build, the drift is pinned in THIS build's
        notes (F-21) — never a silent skip."""
        report = {"sensitive_degree": {"kept": 0, "dropped_negative": 0,
                                       "dropped_unknown_value": 0, "kept_subjects": set()},
                  "arudha": {"rows": 0, "invalid_sign_value": 0},
                  "yoga_constituent": {"validated_ids": set(), "constituents": {}},
                  "roots": {"discarded": 0, "details": []},
                  "lord": {"resolved": 0, "unavailable": 0, "unqualified": 0,
                           "unavailable_refs": [], "unqualified_refs": [],
                           "resolved_map": {}, "rulership_available": True}}
        rows = build_resonance_rows("career_advancement", yoga_firing_rows=[],
                                    report=report)
        assert [r for r in rows if r["target_type"] == "yoga_constituent"] == []
        notes = json.loads(_build_wp3c_notes(report, rows, ["chatra_yoga"]))
        assert notes["yoga_constituent"]["validated_ids"] == []
        assert notes["yoga_constituent"]["dropped_since_prior_build"] == ["chatra_yoga"]

    def test_bhanga_active_carried_as_qualifier_not_weight(self):
        from services.ka_gochara_resonance.writer import _build_yoga_rows
        rows = _build_yoga_rows("wealth_gain", [{
            "yoga_canonical_id": "neecha_bhanga_raja_yoga",
            "constituent_fact_ids": ["f1"], "constituent_planets": ["Moon"],
            "bhanga_active": True,
        }])
        assert rows[0]["target_qualifier"] == "bhanga_active"
        assert rows[0]["weight"] == 0.7  # unchanged — qualifier, not a weight


# ── R-4: lord resolution per the WP1 contract ─────────────────────────────────

class TestR4LordResolution:
    def test_fixture_lord_whole_sign_resolved(self):
        """WP1 fixture lord_whole_sign: LAGNA Cancer (sign 4); house 7 ->
        Capricorn (sign 10); classical rulership Capricorn -> Saturn;
        Saturn's graha_position row present -> 'resolved', lord emitted."""
        ctx = _resolution_ctx(4, present_subjects={"SAT"})
        state, lord = _resolve_lord_ref("7L", ctx)
        assert state == "resolved"
        assert lord == "Saturn"

    def test_missing_rulership_row_is_unqualified(self):
        """The rulership-table gap synthesized in the test input: sign 10 has
        no rulership row -> 'unqualified' (WP1 contract), never guessed."""
        lords = {k: v for k, v in _CLASSICAL_SIGN_LORDS.items() if k != 10}
        state, lord = _resolve_lord_ref("7L", _resolution_ctx(4, sign_lords=lords,
                                                              present_subjects={"SAT"}))
        assert state == "unqualified"
        assert lord is None

    def test_empty_rulership_table_is_unqualified_not_silent_fallback(self):
        """reference_signs unreachable/incomplete -> every lord row is
        'unqualified'; the writer does NOT silently fall back to a hardcoded
        table (unlike the yogi-point reader) — the contract cites the L0 row."""
        state, _ = _resolve_lord_ref("7L", _resolution_ctx(4, sign_lords=None,
                                                           present_subjects={"SAT"}))
        assert state == "unqualified"

    def test_missing_lagna_fact_is_unavailable(self):
        state, _ = _resolve_lord_ref("7L", _resolution_ctx(None, present_subjects={"SAT"}))
        assert state == "unavailable"

    def test_lord_graha_position_absent_is_unavailable(self):
        """Chain completes through rulership but Saturn has no
        graha_position row -> 'unavailable' (cited input fact absent)."""
        state, lord = _resolve_lord_ref("7L", _resolution_ctx(4, present_subjects={"SUN"}))
        assert state == "unavailable"
        assert lord is None  # no resolved lord may be emitted

    def test_sign_lords_copy_matches_chart_reader_v4_drift_guard(self):
        """_CLASSICAL_SIGN_LORDS is a literal copy of the drift-guarded
        brahmagyan SIGN_LORD table (BPHS Ch.1 whole-sign rulership)."""
        from brahmagyan.chart_reader_v4 import SIGN_LORD
        assert _CLASSICAL_SIGN_LORDS == SIGN_LORD


# ── R-5: qualifier preserved, first root retained, discards counted ───────────

class TestR5QualifierAndFirstRoot:
    def test_afflicted_qualifier_preserved_on_clean_ref(self):
        """F-12: '10L afflicted' -> target_ref stays '10L' (natural-key
        stability — consumers read '10L'), qualifier preserved in
        target_qualifier."""
        rows = _build_lord_rows("career_setback", ["10L afflicted"], None)
        assert len(rows) == 1
        assert rows[0]["target_ref"] == "10L"
        assert rows[0]["target_qualifier"] == "afflicted"

    def test_compound_qualifier_applies_to_each_token(self):
        rows = _build_lord_rows("major_loss", ["2L/11L afflicted", "12L"], None)
        by_ref = {r["target_ref"]: r for r in rows}
        assert by_ref["2L"]["target_qualifier"] == "afflicted"
        assert by_ref["11L"]["target_qualifier"] == "afflicted"
        assert by_ref["12L"]["target_qualifier"] is None

    def test_multiple_roots_first_retained_discard_counted(self):
        """Two bg_transit_rules rows yield the same mechanism_node ref: the
        table's UNIQUE key admits one row — the FIRST root wins and the
        discard is recorded with kept-vs-discarded provenance (F-12: the
        retention existed; the silence is what R-5 fixes)."""
        report = {"sensitive_degree": {"kept": 0, "dropped_negative": 0,
                                       "dropped_unknown_value": 0, "kept_subjects": set()},
                  "arudha": {"rows": 0, "invalid_sign_value": 0},
                  "yoga_constituent": {"validated_ids": set(), "constituents": {}},
                  "roots": {"discarded": 0, "details": []}}
        rows = build_resonance_rows(
            "marriage",
            transit_rule_rows=[
                {"id": 34, "rule_type": "favourable", "graha": "venus",
                 "primary_house": 2, "classical_citation": "BPHS Ch.29"},
                {"id": 91, "rule_type": "favourable", "graha": "venus",
                 "primary_house": 2, "classical_citation": "BPHS Ch.29 (dup)"},
            ],
            report=report,
        )
        mech = [r for r in rows if r["target_type"] == "mechanism_node"]
        assert len(mech) == 1
        assert mech[0]["source_rule_id"] == 34, "first source root retained"
        assert report["roots"]["discarded"] == 1
        (detail,) = report["roots"]["details"]
        assert detail["kept_source_rule_id"] == 34
        assert detail["discarded_source_rule_id"] == 91

    def test_no_report_no_behavior_change(self):
        """Without a report sink the assembly is byte-identical in shape to
        pre-R-5 behavior (first wins; discards simply unrecorded)."""
        rows = build_resonance_rows(
            "marriage",
            transit_rule_rows=[
                {"id": 34, "rule_type": "favourable", "graha": "venus", "primary_house": 2,
                 "classical_citation": "c"},
                {"id": 91, "rule_type": "favourable", "graha": "venus", "primary_house": 2,
                 "classical_citation": "c2"},
            ],
        )
        assert [r["source_rule_id"] for r in rows] == [34]


# ── R-6: target_resolution_state on every row + migration ─────────────────────

class TestR6ResolutionStateColumn:
    def test_every_emitted_row_carries_a_valid_state(self):
        rows = build_resonance_rows(
            "marriage",
            houses=["7"], lords=["7L afflicted"], karakas=["Venus"],
            ontology_citation="BPHS ch.7",
            transit_rule_rows=[{"id": 1, "rule_type": "favourable", "graha": "venus",
                                "primary_house": 2, "classical_citation": "c"}],
            sensitive_fact_rows=[{"fact_id": "s", "fact_subject": "VEN",
                                  "fact_key": "pushkara", "fact_value_text": "pushkara"}],
            arudha_fact_rows=[{"fact_id": "a", "fact_subject": "A7",
                               "fact_value_text": "Gemini"}],
            yoga_firing_rows=[{"yoga_canonical_id": "y", "constituent_fact_ids": [],
                               "constituent_planets": [], "bhanga_active": False}],
            dasha_rows=[{"lord_graha": "Venus"}],
        )
        assert rows, "fixture must emit rows across all target types"
        for row in rows:
            assert row["target_resolution_state"] in RESOLVED_STATES, row
            assert "target_qualifier" in row, row

    def test_notes_state_counts_sum_to_rows(self):
        report = {"sensitive_degree": {"kept": 1, "dropped_negative": 0,
                                       "dropped_unknown_value": 0, "kept_subjects": {"VEN"}},
                  "arudha": {"rows": 1, "invalid_sign_value": 0},
                  "yoga_constituent": {"validated_ids": {"y"}, "constituents": {"y": 0}},
                  "roots": {"discarded": 0, "details": []},
                  "lord": {"resolved": 1, "unavailable": 0, "unqualified": 0,
                           "unavailable_refs": [], "unqualified_refs": [],
                           "resolved_map": {"7L": "Saturn"}, "rulership_available": True}}
        rows = build_resonance_rows(
            "marriage", houses=["7"], lords=["7L"], karakas=["Venus"],
            ontology_citation="c",
            sensitive_fact_rows=[{"fact_id": "s", "fact_subject": "VEN",
                                  "fact_key": "pushkara", "fact_value_text": "pushkara"}],
            arudha_fact_rows=[{"fact_id": "a", "fact_subject": "A7",
                               "fact_value_text": "Gemini"}],
            yoga_firing_rows=[{"yoga_canonical_id": "y"}], report=report,
        )
        _stamp_target_resolution(rows, _resolution_ctx(1, present_subjects={"VEN", "SAT"}),
                                 report["lord"])
        notes = json.loads(_build_wp3c_notes(report, rows, []))
        counts = notes["target_resolution_state_counts"]
        assert sum(counts.values()) == len(rows) == notes["rows"]
        assert set(counts) <= RESOLVED_STATES

    def test_migration_1071_exists_with_check_constraint(self):
        sql = MIGRATION_1071.read_text()
        assert "ALTER TABLE gochara_resonance_map" in sql
        assert "ADD COLUMN IF NOT EXISTS target_resolution_state" in sql
        assert "ADD COLUMN IF NOT EXISTS target_qualifier" in sql
        assert "CHECK (target_resolution_state IN ('resolved','unavailable','unqualified'))" in sql
        assert "gochara_resonance_map_target_resolution_state_check" in sql
        # Idempotent house style (mirrors 459): guarded constraint, one tx.
        assert "IF NOT EXISTS" in sql
        assert sql.strip().count("BEGIN;") >= 1 and "COMMIT;" in sql
        # No destructive op outside the commented rollback section.
        body = sql.split("-- ROLLBACK:")[0]
        active = "\n".join(l for l in body.splitlines() if not l.strip().startswith("--"))
        assert "DROP TABLE" not in active and "TRUNCATE" not in active


# ── Writer-level integration (fake conn, DB-free): R-1/R-3/R-4 end-to-end ─────

class _FakeCursor:
    def __init__(self, script, sink, row_factory=None):
        self._script = script
        self._sink = sink
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        normalized = " ".join(sql.split())
        if normalized.startswith("DELETE FROM gochara_resonance_map"):
            self._sink.setdefault("deletes", []).append(params)
            self._result = []
            return
        for matcher, rows in self._script:
            if matcher in normalized:
                self._result = list(rows)
                return
        self._result = []

    def executemany(self, sql, rows):
        if " ".join(sql.split()).startswith("INSERT INTO gochara_resonance_map"):
            self._sink.setdefault("inserted", []).extend(rows)

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None


class _FakeConn:
    def __init__(self, script, sink):
        self._script = script
        self._sink = sink

    def cursor(self, *a, **k):
        return _FakeCursor(self._script, self._sink)


class _Ctx:
    def __init__(self, conn, chart_id, dry_run=False):
        self.db_conn = conn
        self.config = {"chart_id": chart_id}
        self.dry_run = dry_run


_SIGN_LORD_ROWS = [{"sign_id": s, "lord": l} for s, l in sorted(_CLASSICAL_SIGN_LORDS.items())]

_ONTOLOGY = {
    "event_class_id": "marriage",
    "signature_model": {"houses": ["7"], "lords": ["7L"], "karakas": ["Saturn"]},
    "citations": ["BPHS ch.7 (vivaha)"],
}


def _script(yoga_rows=(), prior_yoga_refs=(), sensitive_rows=()):
    """Matchers key on SQL substrings; first match wins, so the specific
    chart_facts filters precede any broader key."""
    return [
        ("FROM brahma_event_ontology", [_ONTOLOGY]),
        ("FROM bg_transit_rules", []),
        ("fact_category = 'sensitive_degree_check'", list(sensitive_rows)),
        ("fact_category = 'arudha_pada'", []),
        ("fact_subject = 'LAGNA'", [{"fact_value_num": 4}]),  # Cancer
        ("fact_key = 'longitude_sidereal'", [{"fact_subject": "SAT"}]),
        ("FROM ga_yoga_firings", list(yoga_rows)),
        ("FROM chart_dashas", []),
        ("FROM reference_signs", list(_SIGN_LORD_ROWS)),
        ("FROM gochara_resonance_map", [{"target_ref": r} for r in prior_yoga_refs]),
    ]


def _run_writer(script, sink, chart_id="wp1-synth-00000000-0000-4000-8000-0000000000ff"):
    from pipeline.orchestrator.writers.ka_gochara_resonance import KaGocharaResonanceWriter
    return KaGocharaResonanceWriter().run(_Ctx(_FakeConn(script, sink), chart_id))


_GAJAKESARI = {
    "yoga_canonical_id": "gajakesari_yoga", "fired": True,
    "constituent_fact_ids": ["wp1synth.moon.lon", "wp1synth.jup.lon"],
    "constituent_planets": ["Moon", "Jupiter"], "bhanga_active": False,
}


class TestWriterLevelWP3c:
    def test_r1_r4_end_to_end_states_and_notes(self):
        sink: dict = {}
        sensitive = [
            {"fact_id": "pos1", "fact_subject": "SAT", "fact_key": "kartari",
             "fact_value_text": "papa_kartari"},
            {"fact_id": "neg1", "fact_subject": "SAT", "fact_key": "gandanta",
             "fact_value_text": "not_gandanta"},
        ]
        result = _run_writer(_script(sensitive_rows=sensitive), sink)

        rows = sink["inserted"]
        sensitive_rows_out = [r for r in rows if r["target_type"] == "sensitive_degree"]
        # The fake serves the same two facts to every one of the 27 event
        # classes: exactly one positive row per class survives (27), the
        # negative row never appears anywhere.
        assert len(sensitive_rows_out) == TARGET_EVENT_CLASSES_N()
        assert {r["target_ref"] for r in sensitive_rows_out} == {"pos1"}
        assert all(r["target_resolution_state"] == "resolved" for r in sensitive_rows_out)
        assert all("_fact_subject" not in r for r in sensitive_rows_out)

        lord_rows = [r for r in rows if r["target_type"] == "lord"]
        assert lord_rows[0]["target_resolution_state"] == "resolved"  # 7L: Cancer->Capricorn->Saturn
        bhava_rows = [r for r in rows if r["target_type"] == "bhava"]
        assert bhava_rows[0]["target_resolution_state"] == "resolved"
        karaka_rows = [r for r in rows if r["target_type"] == "karaka"]
        assert karaka_rows[0]["target_resolution_state"] == "resolved"

        notes = json.loads(result.notes)
        assert notes["wp3c"] == "N-12 R-1..R-6"
        assert notes["sensitive_degree"]["positive_kept"] == TARGET_EVENT_CLASSES_N()
        assert notes["sensitive_degree"]["negative_dropped_zero_rows"] == TARGET_EVENT_CLASSES_N()
        assert notes["sensitive_degree"]["kept_subjects"] == ["SAT"]
        assert notes["lord"]["resolved_lords"] == {"7L": "Saturn"}
        assert notes["lord"]["rulership_source"] == "reference_signs"
        assert sum(notes["target_resolution_state_counts"].values()) == result.rows_inserted

    def test_r3_dropped_yoga_id_surfaces_in_next_build_notes(self):
        # Build 1: gajakesari fires.
        sink1: dict = {}
        result1 = _run_writer(_script(yoga_rows=[_GAJAKESARI]), sink1)
        notes1 = json.loads(result1.notes)
        assert notes1["yoga_constituent"]["validated_ids"] == ["gajakesari_yoga"]
        assert notes1["yoga_constituent"]["dropped_since_prior_build"] == []
        assert notes1["yoga_constituent"]["constituent_fact_counts"] == {"gajakesari_yoga": 2}

        # Build 2: the firing is gone (F-21 drift); the prior build carried it.
        sink2: dict = {}
        result2 = _run_writer(
            _script(yoga_rows=[], prior_yoga_refs=["gajakesari_yoga"]), sink2)
        notes2 = json.loads(result2.notes)
        assert notes2["yoga_constituent"]["validated_ids"] == []
        assert notes2["yoga_constituent"]["dropped_since_prior_build"] == ["gajakesari_yoga"]
        inserted_yoga = [r for r in sink2["inserted"]
                         if r["target_type"] == "yoga_constituent"]
        assert inserted_yoga == [], "delete-then-insert: no stale yoga row survives"

    def test_r4_unqualified_when_rulership_table_unreachable(self):
        sink: dict = {}
        script = _script()
        script = [(m, [] if m == "FROM reference_signs" else rows) for m, rows in script]
        result = _run_writer(script, sink)
        lord_rows = [r for r in sink["inserted"] if r["target_type"] == "lord"]
        assert all(r["target_resolution_state"] == "unqualified" for r in lord_rows)
        notes = json.loads(result.notes)
        assert notes["lord"]["unqualified"] == TARGET_EVENT_CLASSES_N()
        assert notes["lord"]["rulership_source"] == "unavailable_unqualified"


def TARGET_EVENT_CLASSES_N() -> int:
    from services.ka_gochara_resonance.writer import TARGET_EVENT_CLASSES
    return len(TARGET_EVENT_CLASSES)
