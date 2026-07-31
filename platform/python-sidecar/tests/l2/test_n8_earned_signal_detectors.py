"""
tests/l2/test_n8_earned_signal_detectors.py — SAMĀPTI lane B-N8-FIX regression guard
====================================================================================

Locks in the §N.8 (CLAUDE.md "Earned-Signal Principle") repairs for the findings
`SAMAPTI_N8_EARNED_SIGNAL_REGISTER_v1_0.md` §2.1 recorded against two writers,
plus the four PŪRṆATĀ-campaign residuals named in `SAMAPTI_DVARAPALA_LEDGER.md`
Ruling 86 ("B-N8-FIX/SWEEPFIX residuals") that were explicitly left unfixed at
the time (out of declared scope) and are now closed here:

  F-07 `lel_zero_leak_pass`             — PROXY     (was `trap1_count == 0`; never read LEL data)
  F-08 `pillars_meet_reachability_pass` — TAUTOLOGY (was `msr_count > 0`, already raised above)
  F-09 `trap2_narration_leak_count`     — LITERAL 0 (no detector at all)
  F-10 `divergent_flagged_count`        — LITERAL 0 (no detector at all)
  F-12 `bo_chart_gestalt` stored a verdict its own docstring forbids
  F-13 `msr_no_threshold_drop_flag`     — TAUTOLOGY (was `msr_count > 0`, IDENTICAL shape to
                                          F-08 — PŪRṆATĀ residual, closed here)
  F-15 `fragility_class`                — LITERAL "multi_ayanamsha_tested" — PŪRṆATĀ residual
  F-16 `linking_mechanism`               — LITERAL "domain_tension" — PŪRṆATĀ residual
  F-17 `contested_areas` "genuinely balanced" — PROXY (both-nonzero, no threshold) — PŪRṆATĀ residual
  strongest_domain/weakest_domain        — INSERTION-ORDER bug (alphabetical, not by strength) —
                                          PŪRṆATĀ residual

TEST LAYERING, and the honest bounds of each layer:

  1. STRUCTURAL guards — the specific pre-fix expressions must not come back, and
     each scorecard field must be wired to a detector result rather than to a
     literal. Cheap, DB-free, catches a regression to the exact defect.
  2. ASSEMBLY guards — drive the real writer functions with a canned connection
     and assert on what they build. Tests the writer's own logic; deliberately
     does NOT claim to test the SQL.
  3. LIVE CAN-FAIL proof (`test_detectors_canfail_live`) — seeds a real Postgres,
     runs the module's own SQL constants verbatim, mutates the underlying
     condition each detector claims to measure, asserts the field goes red, and
     reverts. This is the only layer that proves the SQL itself is not
     true-by-construction. It SKIPS unless `N8_DETECTOR_TEST_DSN` points at a
     throwaway Postgres, so CI without a DB does not silently report a green it
     did not earn — the skip is visible, which is the point.

To run layer 3:
    initdb -D /tmp/n8pg -U postgres --auth=trust
    pg_ctl -D /tmp/n8pg -o "-p 55432 -k /tmp" start
    N8_DETECTOR_TEST_DSN="host=127.0.0.1 port=55432 dbname=postgres user=postgres" \
        pytest tests/l2/test_n8_earned_signal_detectors.py
"""
from __future__ import annotations

import inspect
import json
import os

import pytest

from pipeline.orchestrator.writers import bo_chart_gestalt, bo_pramana_mapa

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"


# ══════════════════════════════════════════════════════════════════════════════
# Layer 1 — structural guards: the pre-fix expressions must never come back
# ══════════════════════════════════════════════════════════════════════════════

def test_pramana_mapa_no_longer_carries_the_four_prefix_expressions():
    src = inspect.getsource(bo_pramana_mapa)

    assert "lel_zero_leak = trap1_count == 0" not in src, (
        "F-07 regression: lel_zero_leak_pass is back to the constituent-array "
        "proxy, which never reads LEL data at all"
    )
    assert "pillars_pass = msr_count > 0" not in src, (
        "F-08 regression: pillars_meet_reachability_pass is back to the "
        "tautology (msr_count == 0 already raises ~160 lines earlier, so this "
        "expression can only ever evaluate True)"
    )
    assert '"trap2_narration_leak_count": 0,' not in src, (
        "F-09 regression: trap2_narration_leak_count is back to a literal 0"
    )
    assert '"divergent_flagged_count": 0,' not in src, (
        "F-10 regression: divergent_flagged_count is back to a literal 0"
    )
    assert '"msr_no_threshold_drop_flag": msr_count > 0,' not in src, (
        "F-13 regression: msr_no_threshold_drop_flag is back to the IDENTICAL "
        "tautology as F-08 (msr_count == 0 already raises ~300 lines earlier, "
        "so this expression can only ever evaluate True)"
    )


def test_pramana_mapa_fields_are_wired_to_detector_results():
    src = inspect.getsource(bo_pramana_mapa)
    for field, expr in [
        ("lel_zero_leak_pass", 'lel_result["pass"]'),
        ("pillars_meet_reachability_pass", 'pillars_result["pass"]'),
        ("msr_no_threshold_drop_flag", 'no_drop_result["pass"]'),
        ("trap2_narration_leak_count", 'trap2_result["count"]'),
        ("divergent_flagged_count", 'divergent_result["count"]'),
    ]:
        assert f'"{field}": {expr}' in src, f"{field} is not wired to its detector"


def test_every_detector_reads_a_real_table():
    """A detector whose terms never touch the DB cannot observe anything."""
    for sql_const in [
        bo_pramana_mapa._LEL_TERM_A_SQL,
        bo_pramana_mapa._LEL_TERM_B_SQL,
        bo_pramana_mapa._LEL_TERM_C_SQL,
        bo_pramana_mapa._ORPHAN_EDGE_ENDPOINTS_SQL,
        bo_pramana_mapa._ORPHAN_EDGE_SIGNAL_REFS_SQL,
        bo_pramana_mapa._WEAK_TAIL_COUNT_SQL,
        bo_pramana_mapa._NARRATION_LEAK_SQL,
        bo_pramana_mapa._EXPLICIT_DIVERGENT_SQL,
        bo_pramana_mapa._TIER_INVERSION_SQL,
    ]:
        assert "FROM" in sql_const and "%s" in sql_const

    # The LEL detector must actually read LEL data — the whole of F-07.
    assert "life_events" in bo_pramana_mapa._LEL_TERM_B_SQL
    assert "lel_origin" in bo_pramana_mapa._LEL_TERM_A_SQL
    # The reachability gate must carry a second, independent term (the F-19
    # lesson: a gate whose operands cannot disagree is not a gate).
    assert "bodha_cgm_nodes" in bo_pramana_mapa._ORPHAN_EDGE_ENDPOINTS_SQL
    # F-13: the no-threshold-drop gate must actually read computed_salience —
    # the second, independent term the msr_count>0 tautology lacked.
    assert "computed_salience" in bo_pramana_mapa._WEAK_TAIL_COUNT_SQL


def test_no_threshold_drop_needs_both_presence_and_weak_tail():
    """F-13: msr_count alone must not be sufficient — a second independent
    term (a real weak-tail signal) is required, unlike the tautology it
    replaces."""
    class FakeCursor:
        def __init__(self, count):
            self._count = count
        def fetchone(self):
            return (self._count,)

    class ZeroWeakTail:
        """msr_count > 0 but no signal clears the weak-tail scan."""
        def execute(self, *_a, **_k):
            return FakeCursor(0)

    res = bo_pramana_mapa.detect_no_threshold_drop(ZeroWeakTail(), CHART_ID, msr_count=5)
    assert res["pass"] is False, (
        "msr_count > 0 alone flipped the gate true — this is the F-08-shaped "
        "tautology again; the weak-tail term must be independently required"
    )
    assert res["terms"]["weak_tail_signal_count"] == 0


def test_unevaluable_detector_returns_none_not_a_pass():
    """§N.8: an unevaluable check is an unknown, never a clean pass."""
    class Exploding:
        def execute(self, *_a, **_k):
            raise RuntimeError("relation does not exist")

    conn = Exploding()
    assert bo_pramana_mapa.detect_lel_leak(conn, CHART_ID)["pass"] is None
    assert bo_pramana_mapa.detect_pillar_reachability(
        conn, CHART_ID, 1, 1, 1, 1, 1)["pass"] is None
    assert bo_pramana_mapa.detect_no_threshold_drop(conn, CHART_ID, msr_count=1)["pass"] is None
    assert bo_pramana_mapa.count_narration_leaks(conn, CHART_ID)["count"] is None
    assert bo_pramana_mapa.count_divergent_signals(conn, CHART_ID)["count"] is None


def test_pillar_presence_term_is_falsifiable_without_a_db():
    """Term 1 of the reachability gate is pure-Python and must be able to fail
    even when term 2 cannot be evaluated — proving the gate is not the old
    `msr_count > 0` tautology."""
    class Exploding:
        def execute(self, *_a, **_k):
            raise RuntimeError("no db")

    res = bo_pramana_mapa.detect_pillar_reachability(Exploding(), CHART_ID, 5, 0, 5, 5, 5)
    assert res["terms"]["pillars_present"]["cdlm_cells"] is False
    assert res["pass"] is None  # unknown, because term 2 could not run — not True


def test_gestalt_writer_stores_no_verdict():
    """F-12: the writer's own docstring says it NEVER stores verdicts."""
    src = inspect.getsource(bo_chart_gestalt)
    assert 'verdict_class = "strong_positive"' not in src
    assert 'verdict_class = "strong_challenge"' not in src
    assert '"verdict_class": verdict_class' not in src
    assert '"confidence": round(min(salience / 10.0, 1.0), 3)' not in src
    assert "NEVER stores verdicts" in src  # the rule itself must stay


def test_gestalt_no_longer_carries_the_purnata_residual_literals():
    """PŪRṆATĀ residual sweep regression guard: F-15, F-16, F-17, and the
    strongest/weakest-domain insertion-order bug must not come back."""
    src = inspect.getsource(bo_chart_gestalt)

    assert '"fragility_class": "multi_ayanamsha_tested"' not in src, (
        "F-15 regression: fragility_class is back to a hardcoded literal a "
        "single ayanamsha's write cannot honestly assert"
    )
    assert '"linking_mechanism": "domain_tension",' not in src, (
        "F-16 regression: linking_mechanism is back to a hardcoded literal "
        "that never checks whether the two poles actually share a domain"
    )
    assert '"note": "domains where benefic and malefic evidence is genuinely balanced"' not in src, (
        "F-17 regression: contested_areas is back to asserting 'balanced' "
        "from a HAVING clause that only requires both counts to be non-zero"
    )
    assert (
        'strongest_domain = list(domain_verdict_map.keys())[0]' not in src
    ), (
        "strongest_domain regression: back to reading dict insertion order "
        "(== alphabetical, from the DISTINCT ON ORDER BY) instead of ranking "
        "by evidence.top_signal_salience"
    )
    assert (
        'weakest_domain_entry = list(domain_verdict_map.items())[-1]' not in src
    ), (
        "weakest_domain regression: back to reading dict insertion order "
        "(== alphabetical) instead of ranking by evidence.top_signal_salience"
    )
    # The real replacements must be present.
    assert "domain_strength_order" in src
    assert "_CONTESTED_BALANCE_RATIO_THRESHOLD" in src
    assert "_assess_fragility" in src and "_patch_fragility" in src


def test_strongest_and_weakest_domain_rank_by_salience_not_alphabet():
    """The register's own diagnosis: an INSERTION-ORDER bug, not a
    sorting-by-value bug. Domain names are chosen so that alphabetical order
    gives the WRONG answer, proving the fix ranks by real salience."""
    captured: dict = {}
    top_signal = {
        "signal_id": "sig-top", "signal_type_id": "t1",
        "signal_type_class": "position", "computed_salience": 5.0,
        "signature_tier": "major", "valence": "benefic",
        "source_l1_asset": "ga_structural", "domains_affected_array": ["aaa_domain"],
        "constituent_facts_array": ["fact0001"],
    }
    canned = [
        ("signature_tier IN ('chart_defining', 'major')", [top_signal]),
        # domain_signals: 'aaa_domain' (alphabetically first) is DELIBERATELY
        # the WEAKEST signal; 'zzz_domain' (alphabetically last) is the
        # STRONGEST. If the bug were still present, strongest_domain would
        # read 'aaa_domain' and weakest_domain would read 'zzz_domain' —
        # exactly backwards.
        ("DISTINCT ON (unnested_domain)", [
            {"unnested_domain": "aaa_domain", "signal_id": "sig-weak",
             "computed_salience": 0.9, "valence": "benefic",
             "signature_tier": "supporting"},
            {"unnested_domain": "zzz_domain", "signal_id": "sig-strong",
             "computed_salience": 9.5, "valence": "malefic",
             "signature_tier": "chart_defining"},
        ]),
        ("major_tier_count", [
            {"domain": "aaa_domain", "signal_count": 3, "benefic_count": 3,
             "malefic_count": 0, "mixed_count": 0, "neutral_count": 0,
             "major_tier_count": 0},
            {"domain": "zzz_domain", "signal_count": 50, "benefic_count": 5,
             "malefic_count": 45, "mixed_count": 0, "neutral_count": 0,
             "major_tier_count": 40},
        ]),
        # NOTE: "HAVING COUNT(*)" (unique to the `contested` query) MUST be
        # checked before the generic "valence = 'malefic'"/"valence =
        # 'benefic'" fragments below, because `contested`'s own SQL also
        # contains those substrings (its FILTER clauses) — first-match-wins.
        ("HAVING COUNT(*)", []),        # contested
        ("valence = 'malefic'", []),    # malefic_signals
        ("valence = 'benefic'", []),    # benefic_top
        ("bodha_discoveries", []),      # outlier_discoveries
    ]
    conn = _CannedConn(canned, captured)
    bo_chart_gestalt._write_aya(conn, CHART_ID, AYA, "build-1", "2026-07-31T00:00:00Z")

    headline = json.loads(captured["row"]["headline_jsonb"])
    watch_list = json.loads(captured["row"]["watch_list_jsonb"])

    assert headline["strongest_domain"] == "zzz_domain", (
        f"strongest_domain read '{headline['strongest_domain']}' — this is "
        "alphabetical/insertion order, not the real highest-salience domain"
    )
    assert watch_list["weakest_domain"] == "aaa_domain", (
        f"weakest_domain read '{watch_list['weakest_domain']}' — this is "
        "alphabetical/insertion order, not the real lowest-salience domain"
    )


def test_linking_mechanism_reflects_real_domain_overlap():
    """F-16: linking_mechanism must be computed from the actual overlap
    between the two poles' domains, not hardcoded to 'domain_tension'."""
    captured: dict = {}
    top_signal = {
        "signal_id": "sig-top", "signal_type_id": "t1",
        "signal_type_class": "position", "computed_salience": 5.0,
        "signature_tier": "major", "valence": "benefic",
        "source_l1_asset": "ga_structural", "domains_affected_array": ["career"],
        "constituent_facts_array": ["fact0001"],
    }
    canned = [
        ("signature_tier IN ('chart_defining', 'major')", [top_signal]),
        ("DISTINCT ON (unnested_domain)", [
            {"unnested_domain": "career", "signal_id": "sig-top",
             "computed_salience": 5.0, "valence": "benefic",
             "signature_tier": "major"},
        ]),
        ("major_tier_count", [
            {"domain": "career", "signal_count": 1, "benefic_count": 1,
             "malefic_count": 0, "mixed_count": 0, "neutral_count": 0,
             "major_tier_count": 1},
        ]),
        ("HAVING COUNT(*)", []),  # contested — must be checked before valence fragments below
        # malefic_signals: top malefic signal touches "health", NOT "career"
        ("valence = 'malefic'", [
            {"signal_id": "sig-malefic", "signal_type_id": "t2",
             "computed_salience": 4.0, "domains_affected_array": ["health"]},
        ]),
        # benefic_top: shares no domain with the malefic pole above
        ("valence = 'benefic'", [
            {"signal_id": "sig-benefic", "signal_type_id": "t3",
             "domains_affected_array": ["career"]},
        ]),
        ("bodha_discoveries", []),
    ]
    conn = _CannedConn(canned, captured)
    bo_chart_gestalt._write_aya(conn, CHART_ID, AYA, "build-1", "2026-07-31T00:00:00Z")

    cq = json.loads(captured["row"]["central_question_jsonb"])
    assert cq["linking_mechanism"] == "cross_domain_contrast", (
        "career (positive pole) and health (negative pole) share no domain — "
        "linking_mechanism must not claim 'domain_tension' unconditionally"
    )
    assert cq["linking_mechanism_terms"]["positive_pole_domains"] == ["career"]
    assert cq["linking_mechanism_terms"]["negative_pole_domains"] == ["health"]


def test_contested_areas_lopsided_is_not_genuinely_balanced():
    """F-17: the register's own live disproof — 136 benefic vs 632 malefic
    must be reported as contested but NOT genuinely balanced."""
    captured: dict = {}
    top_signal = {
        "signal_id": "sig-top", "signal_type_id": "t1",
        "signal_type_class": "position", "computed_salience": 5.0,
        "signature_tier": "major", "valence": "benefic",
        "source_l1_asset": "ga_structural", "domains_affected_array": ["career"],
        "constituent_facts_array": ["fact0001"],
    }
    canned = [
        ("signature_tier IN ('chart_defining', 'major')", [top_signal]),
        ("DISTINCT ON (unnested_domain)", [
            {"unnested_domain": "career", "signal_id": "sig-top",
             "computed_salience": 5.0, "valence": "benefic",
             "signature_tier": "major"},
        ]),
        ("major_tier_count", [
            {"domain": "career", "signal_count": 768, "benefic_count": 136,
             "malefic_count": 632, "mixed_count": 0, "neutral_count": 0,
             "major_tier_count": 12},
        ]),
        # contested: the live 136/632 case. Must be checked BEFORE the
        # generic valence fragments below — this query's own FILTER clauses
        # also contain "valence = 'benefic'"/"valence = 'malefic'" text.
        ("HAVING COUNT(*)", [
            {"domain": "career", "benefic_count": 136, "malefic_count": 632},
        ]),
        ("valence = 'malefic'", []),
        ("valence = 'benefic'", []),
        ("bodha_discoveries", []),
    ]
    conn = _CannedConn(canned, captured)
    bo_chart_gestalt._write_aya(conn, CHART_ID, AYA, "build-1", "2026-07-31T00:00:00Z")

    contested = json.loads(captured["row"]["contested_areas_jsonb"])
    career = contested["contested_domains"][0]
    assert career["domain"] == "career"
    assert career["genuinely_balanced"] is False, (
        "136 vs 632 (ratio 0.215) was served as 'genuinely balanced' — the "
        "register's own live disproof; the HAVING clause only checked both "
        "counts were non-zero, never an actual balance threshold"
    )
    assert abs(career["balance_ratio"] - round(136 / 632, 4)) < 1e-9


def test_assess_fragility_needs_at_least_two_ayanamsha_rows():
    """F-15: fragility_class cannot be established from a single ayanamsha's
    row — must be None (not a default), not a guess."""
    class OneRowConn:
        def cursor(self, *_a, **_k):
            class Cur:
                def __enter__(self_inner):
                    return self_inner
                def __exit__(self_inner, *_exc):
                    return False
                def execute(self_inner, *_a, **_k):
                    pass
                def fetchall(self_inner):
                    return [{"ayanamsha_id": AYA, "domain_verdict_map_jsonb": "{}"}]
                @property
                def description(self_inner):
                    return None
            return Cur()

    res = bo_chart_gestalt._assess_fragility(OneRowConn(), CHART_ID, "build-1")
    assert res["fragility_class"] is None
    assert res["terms"]["ayanamsha_rows_compared"] == 1


def test_assess_fragility_detects_a_real_disagreement():
    """F-15 can-fail proof (in-process): two ayanamsha rows whose stored
    domain evidence disagrees on which valence dominates a shared domain must
    flip fragility_class from stable to ayanamsha_sensitive."""
    def _rows(agree: bool):
        career_lahiri = {"career": {"evidence": {"benefic_count": 10, "malefic_count": 1}}}
        career_raman = (
            {"career": {"evidence": {"benefic_count": 9, "malefic_count": 1}}}
            if agree else
            {"career": {"evidence": {"benefic_count": 1, "malefic_count": 10}}}
        )
        return [
            {"ayanamsha_id": "lahiri_chitrapaksha", "domain_verdict_map_jsonb": json.dumps(career_lahiri)},
            {"ayanamsha_id": "raman", "domain_verdict_map_jsonb": json.dumps(career_raman)},
        ]

    class RowsConn:
        def __init__(self, rows):
            self._rows = rows
        def cursor(self, *_a, **_k):
            rows = self._rows
            class Cur:
                def __enter__(self_inner):
                    return self_inner
                def __exit__(self_inner, *_exc):
                    return False
                def execute(self_inner, *_a, **_k):
                    pass
                def fetchall(self_inner):
                    return rows
                @property
                def description(self_inner):
                    return None
            return Cur()

    stable = bo_chart_gestalt._assess_fragility(RowsConn(_rows(True)), CHART_ID, "build-1")
    assert stable["fragility_class"] == "stable_across_ayanamsha"

    fragile = bo_chart_gestalt._assess_fragility(RowsConn(_rows(False)), CHART_ID, "build-1")
    assert fragile["fragility_class"] == "ayanamsha_sensitive", (
        "career flips from benefic-leaning (lahiri) to malefic-leaning "
        "(raman) — this MUST be reported as ayanamsha-sensitive"
    )
    assert "career" in fragile["terms"]["domains_disagreeing"]


# ══════════════════════════════════════════════════════════════════════════════
# Layer 2 — assembly guard for the gestalt domain map
# ══════════════════════════════════════════════════════════════════════════════

class _CannedCursor:
    """Returns canned dict rows chosen by matching a fragment of the SQL."""

    def __init__(self, canned: list[tuple[str, list[dict]]], captured: dict):
        self._canned = canned
        self._captured = captured
        self._rows: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, sql, params=None):
        if isinstance(params, dict):          # the INSERT
            self._captured["row"] = params
            self._rows = []
            return
        for fragment, rows in self._canned:
            if fragment in sql:
                self._rows = rows
                return
        self._rows = []

    def fetchall(self):
        return self._rows

    @property
    def description(self):
        return None


class _CannedConn:
    def __init__(self, canned, captured):
        self._canned = canned
        self._captured = captured

    def cursor(self, *_a, **_k):
        return _CannedCursor(self._canned, self._captured)


def test_gestalt_domain_map_carries_evidence_not_a_verdict():
    """The register's live disproof: the career domain served 'strong_positive'
    while holding 136 benefic vs 632 malefic signals. The map must now carry the
    whole-domain counts and no verdict at all."""
    captured: dict = {}
    top_signal = {
        "signal_id": "sig-career", "signal_type_id": "t1",
        "signal_type_class": "position", "computed_salience": 8.4,
        "signature_tier": "chart_defining", "valence": "benefic",
        "source_l1_asset": "ga_structural", "domains_affected_array": ["career"],
        "constituent_facts_array": ["fact0001"],
    }
    canned = [
        # most-specific fragment first — several queries read bodha_msr_signals
        ("signature_tier IN ('chart_defining', 'major')", [top_signal]),
        # domain verdict map source (DISTINCT ON top-salience signal per domain)
        ("DISTINCT ON (unnested_domain)", [
            {"unnested_domain": "career", "signal_id": "sig-career",
             "computed_salience": 8.4, "valence": "benefic",
             "signature_tier": "chart_defining"},
        ]),
        # NEW: whole-domain evidence aggregate
        ("major_tier_count", [
            {"domain": "career", "signal_count": 768, "benefic_count": 136,
             "malefic_count": 632, "mixed_count": 0, "neutral_count": 0,
             "major_tier_count": 12},
        ]),
    ]
    conn = _CannedConn(canned, captured)
    bo_chart_gestalt._write_aya(conn, CHART_ID, AYA, "build-1", "2026-07-31T00:00:00Z")

    vm = json.loads(captured["row"]["domain_verdict_map_jsonb"])
    career = vm["career"]

    assert "verdict_class" not in career, "F-12 regression: a verdict is stored again"
    assert "confidence" not in career, "F-12 regression: a confidence is stored again"
    assert career["signal_id"] == "sig-career", "the pointer must survive"
    assert career["evidence"]["benefic_count"] == 136
    assert career["evidence"]["malefic_count"] == 632
    assert career["evidence"]["signal_count"] == 768
    assert "no verdict stored" in career["verdict_note"]


# ══════════════════════════════════════════════════════════════════════════════
# Layer 3 — LIVE can-fail proof against a real Postgres
# ══════════════════════════════════════════════════════════════════════════════

_DSN = os.environ.get("N8_DETECTOR_TEST_DSN")

_SCHEMA = """
DROP TABLE IF EXISTS chart_facts, life_events, bodha_msr_signals,
  bodha_cdlm_cells, bodha_cgm_nodes, bodha_cgm_edges, bodha_rm_resonances;
CREATE TABLE chart_facts (
  fact_id TEXT PRIMARY KEY, chart_id UUID NOT NULL, verification_pass_status TEXT);
CREATE TABLE life_events (
  event_id UUID PRIMARY KEY, chart_id UUID, event_date DATE, event_type TEXT);
CREATE TABLE bodha_msr_signals (
  signal_id UUID PRIMARY KEY, chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL,
  lel_origin BOOLEAN NOT NULL DEFAULT false, configuration_jsonb JSONB NOT NULL,
  constituent_facts_array TEXT[] NOT NULL, signal_summary_text TEXT,
  signal_headline_text TEXT, verification_pass_status TEXT,
  computed_salience NUMERIC NOT NULL DEFAULT 1.0);
CREATE TABLE bodha_cdlm_cells (cell_id UUID PRIMARY KEY, chart_id UUID NOT NULL);
CREATE TABLE bodha_cgm_nodes (node_id UUID PRIMARY KEY, chart_id UUID NOT NULL);
CREATE TABLE bodha_cgm_edges (
  edge_id UUID PRIMARY KEY, chart_id UUID NOT NULL, from_node_id UUID NOT NULL,
  to_node_id UUID NOT NULL, underlying_msr_signal_ids_array UUID[]);
CREATE TABLE bodha_rm_resonances (resonance_id UUID PRIMARY KEY, chart_id UUID NOT NULL);
"""

_SIG_A = "11111111-1111-4111-8111-111111111111"
_SIG_B = "22222222-2222-4222-8222-222222222222"  # low-salience "weak tail" signal (F-13)
_NODE_A = "33333333-3333-4333-8333-333333333333"
_NODE_B = "44444444-4444-4444-8444-444444444444"
_EDGE_A = "55555555-5555-4555-8555-555555555555"
_CELL_A = "66666666-6666-4666-8666-666666666666"
_RES_A = "77777777-7777-4777-8777-777777777777"
_EVENT_A = "88888888-8888-4888-8888-888888888888"


def _seed(conn):
    conn.execute("TRUNCATE chart_facts, life_events, bodha_msr_signals, "
                 "bodha_cdlm_cells, bodha_cgm_nodes, bodha_cgm_edges, bodha_rm_resonances")
    conn.execute("INSERT INTO chart_facts VALUES ('fact0001', %s, 'two_pass_verified')", [CHART_ID])
    conn.execute("INSERT INTO chart_facts VALUES ('fact0002', %s, 'documented_approximation')", [CHART_ID])
    conn.execute("INSERT INTO life_events VALUES (%s, %s, '1999-01-01', 'spiritual')", [_EVENT_A, CHART_ID])
    conn.execute(
        """INSERT INTO bodha_msr_signals VALUES
             (%s, %s, 'lahiri_chitrapaksha', false, '{"house":10}'::jsonb,
              ARRAY['fact0001'], 'Sun occupies house 10.', 'Sun in 10th.', 'single_pass', 1.5)""",
        [_SIG_A, CHART_ID])
    # F-13: a genuine weak-tail signal (computed_salience below the 0.3
    # boundary) — its presence is the independent term the msr_count>0
    # tautology lacked.
    conn.execute(
        """INSERT INTO bodha_msr_signals VALUES
             (%s, %s, 'lahiri_chitrapaksha', false, '{"house":3}'::jsonb,
              ARRAY['fact0001'], 'Minor background signal.', 'Minor.', 'single_pass', 0.05)""",
        [_SIG_B, CHART_ID])
    conn.execute("INSERT INTO bodha_cdlm_cells VALUES (%s, %s)", [_CELL_A, CHART_ID])
    conn.execute("INSERT INTO bodha_cgm_nodes VALUES (%s, %s)", [_NODE_A, CHART_ID])
    conn.execute("INSERT INTO bodha_cgm_nodes VALUES (%s, %s)", [_NODE_B, CHART_ID])
    conn.execute("INSERT INTO bodha_cgm_edges VALUES (%s, %s, %s, %s, ARRAY[%s]::uuid[])",
                 [_EDGE_A, CHART_ID, _NODE_A, _NODE_B, _SIG_A])
    conn.execute("INSERT INTO bodha_rm_resonances VALUES (%s, %s)", [_RES_A, CHART_ID])
    conn.commit()


def _snapshot(conn):
    def n(table):
        return conn.execute(
            f"SELECT count(*) FROM {table} WHERE chart_id=%s", [CHART_ID]
        ).fetchone()[0]

    # Counts are read live, exactly as the writer reads them, so a deleted pillar
    # actually reaches the presence term.
    msr_count = n("bodha_msr_signals")
    return {
        "lel": bo_pramana_mapa.detect_lel_leak(conn, CHART_ID)["pass"],
        "pillars": bo_pramana_mapa.detect_pillar_reachability(
            conn, CHART_ID,
            msr_count, n("bodha_cdlm_cells"), n("bodha_cgm_nodes"),
            n("bodha_cgm_edges"), n("bodha_rm_resonances"))["pass"],
        "no_drop": bo_pramana_mapa.detect_no_threshold_drop(conn, CHART_ID, msr_count)["pass"],
        "trap2": bo_pramana_mapa.count_narration_leaks(conn, CHART_ID)["count"],
        "divergent": bo_pramana_mapa.count_divergent_signals(conn, CHART_ID)["count"],
    }


_CLEAN = {"lel": True, "pillars": True, "no_drop": True, "trap2": 0, "divergent": 0}

# (label, field that must go red, mutation SQL, revert SQL)
_MUTATIONS = [
    ("lel term A · lel_origin flipped true", "lel",
     f"UPDATE bodha_msr_signals SET lel_origin=true WHERE signal_id='{_SIG_A}'",
     f"UPDATE bodha_msr_signals SET lel_origin=false WHERE signal_id='{_SIG_A}'"),
    ("lel term B · life_events.event_id in the constituent chain", "lel",
     f"UPDATE bodha_msr_signals SET constituent_facts_array="
     f"ARRAY['fact0001','{_EVENT_A}'] WHERE signal_id='{_SIG_A}'",
     f"UPDATE bodha_msr_signals SET constituent_facts_array="
     f"ARRAY['fact0001'] WHERE signal_id='{_SIG_A}'"),
    ("lel term C · LEL payload key in configuration_jsonb", "lel",
     f"""UPDATE bodha_msr_signals SET configuration_jsonb=
         '{{"house":10,"milestone_event_ids":["x"]}}'::jsonb WHERE signal_id='{_SIG_A}'""",
     f"""UPDATE bodha_msr_signals SET configuration_jsonb=
         '{{"house":10}}'::jsonb WHERE signal_id='{_SIG_A}'"""),
    ("pillars term 1 · CDLM pillar deleted", "pillars",
     f"DELETE FROM bodha_cdlm_cells WHERE cell_id='{_CELL_A}'",
     f"INSERT INTO bodha_cdlm_cells VALUES ('{_CELL_A}','{CHART_ID}')"),
    ("pillars term 2 · edge repointed at a non-existent node", "pillars",
     f"UPDATE bodha_cgm_edges SET to_node_id="
     f"'99999999-9999-4999-8999-999999999999' WHERE edge_id='{_EDGE_A}'",
     f"UPDATE bodha_cgm_edges SET to_node_id='{_NODE_B}' WHERE edge_id='{_EDGE_A}'"),
    ("pillars term 2 · dangling underlying_msr_signal_ids_array ref", "pillars",
     f"UPDATE bodha_cgm_edges SET underlying_msr_signal_ids_array="
     f"ARRAY['aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa']::uuid[] WHERE edge_id='{_EDGE_A}'",
     f"UPDATE bodha_cgm_edges SET underlying_msr_signal_ids_array="
     f"ARRAY['{_SIG_A}']::uuid[] WHERE edge_id='{_EDGE_A}'"),
    ("no_drop · weak-tail signal's salience raised above the threshold", "no_drop",
     f"UPDATE bodha_msr_signals SET computed_salience=1.2 WHERE signal_id='{_SIG_B}'",
     f"UPDATE bodha_msr_signals SET computed_salience=0.05 WHERE signal_id='{_SIG_B}'"),
    ("no_drop · weak-tail signal deleted entirely", "no_drop",
     f"DELETE FROM bodha_msr_signals WHERE signal_id='{_SIG_B}'",
     f"""INSERT INTO bodha_msr_signals VALUES
             ('{_SIG_B}', '{CHART_ID}', 'lahiri_chitrapaksha', false, '{{"house":3}}'::jsonb,
              ARRAY['fact0001'], 'Minor background signal.', 'Minor.', 'single_pass', 0.05)"""),
    ("trap2 · deliberation committed into a deterministic text field", "trap2",
     f"UPDATE bodha_msr_signals SET signal_summary_text="
     f"'Wait: re-reading. Corrected: Ketu aspects 1H.' WHERE signal_id='{_SIG_A}'",
     f"UPDATE bodha_msr_signals SET signal_summary_text="
     f"'Sun occupies house 10.' WHERE signal_id='{_SIG_A}'"),
    ("divergent term a · explicit divergent_flagged stamp", "divergent",
     f"UPDATE bodha_msr_signals SET verification_pass_status='divergent_flagged' "
     f"WHERE signal_id='{_SIG_A}'",
     f"UPDATE bodha_msr_signals SET verification_pass_status='single_pass' "
     f"WHERE signal_id='{_SIG_A}'"),
    ("divergent term b · signal claims a stronger tier than its cited L1 fact", "divergent",
     f"UPDATE bodha_msr_signals SET verification_pass_status='two_pass_verified', "
     f"constituent_facts_array=ARRAY['fact0002'] WHERE signal_id='{_SIG_A}'",
     f"UPDATE bodha_msr_signals SET verification_pass_status='single_pass', "
     f"constituent_facts_array=ARRAY['fact0001'] WHERE signal_id='{_SIG_A}'"),
]


@pytest.mark.skipif(not _DSN, reason="set N8_DETECTOR_TEST_DSN to run the live can-fail proof")
@pytest.mark.parametrize("label,field,mutate_sql,revert_sql", _MUTATIONS,
                         ids=[m[0] for m in _MUTATIONS])
def test_detectors_canfail_live(label, field, mutate_sql, revert_sql):
    """green → mutate the underlying condition → RED → revert → green.

    Runs the writer module's own SQL constants against a real Postgres. This is
    the layer that proves none of the four fields is true-by-construction.
    """
    psycopg = pytest.importorskip("psycopg")
    with psycopg.connect(_DSN, autocommit=False) as conn:
        conn.execute(_SCHEMA)
        conn.commit()
        _seed(conn)

        assert _snapshot(conn) == _CLEAN, "baseline is not clean — fixture is wrong"

        conn.execute(mutate_sql)
        conn.commit()
        mutated = _snapshot(conn)
        assert mutated[field] != _CLEAN[field], (
            f"{label}: mutating the underlying condition did NOT move "
            f"{field} off its clean value — the field is true-by-construction"
        )
        # a mutation must not smear across unrelated fields
        for other in _CLEAN:
            if other != field:
                assert mutated[other] == _CLEAN[other], (
                    f"{label}: unrelated field {other} also moved")

        conn.execute(revert_sql)
        conn.commit()
        assert _snapshot(conn) == _CLEAN, f"{label}: revert did not restore the baseline"
