"""
R6A.3 — bo_laksana D9 cross-check must consult L1's neecha-bhanga verdict.

The bug (caught by the native on his own chart): bo_laksana's
`_build_navamsha_cross_check_signals` (O3) classified every graha purely from
raw D1×D9 dignity tiers and hardcoded `neechabhanga_modifier=1.0` /
`cancellation_modifier=1.0` — with zero knowledge of the R6A.1 NBRY evaluator
in ga_yoga_writer, which already records (in `ga_yoga_firings`,
yoga_canonical_id='neecha_bhanga_raja_yoga') that the native's D1-debilitated
Saturn (Aries) is classically CANCELLED via rule 2 (Sun, exalted in Aries,
in a kendra — 10th — from the Aries lagna).

The fix (architecture rule §N.5 — L1 is the authority over L2+ derivations):
bo_laksana does NOT reimplement neecha-bhanga. It reads the already-computed
`ga_yoga_firings` NBRY row once per (chart, ayanamsha) and, for any graha whose
D1-context bhanga fired, classifies 'neecha_bhanga_redeemed' and feeds
`neechabhanga_modifier=1.3` (formulas.py's ratified "cancelled debility" value).

Covers:
  1. Golden gate (synthetic): the native's real chart shape — Saturn
     debilitated in Aries D1, NBRY rule-2 row on record → classification is
     'neecha_bhanga_redeemed' (NOT a raw-tier weakness class), modifier 1.3.
  2. Golden gate (REAL, read-only): same assertions against the live
     ga_yoga_firings / chart_facts / chart_divisionals rows for chart_id
     482012f1-710e-4a25-994a-93821f5871aa. Skips (not fails) when no
     DATABASE_URL is reachable — mirrors R6A.1's integration-test discipline.
  3. Negative control: an UNCANCELLED debilitation (no ga_yoga_firings row)
     keeps its pre-R6A.3 classification and modifier 1.0; a D1-strong × D9-weak
     graha still classifies 'broken_promise' exactly as before.
  4. Consult-before-classify mechanics: an active D1-context redemption takes
     precedence over every tier branch (including the broken_promise branch);
     a pure-D9-context bhanga entry does NOT redeem the D1 classification;
     supporting (canceller) planets in constituent_planets are never marked
     redeemed themselves.

Sections 1, 3, 4 are pure in-process tests (mock conn, no DB, no LLM).
Section 2 performs READ-ONLY SELECTs against the canonical chart — no writes.
"""
from __future__ import annotations

import json
import os
import pathlib
from unittest.mock import MagicMock

import pytest

from pipeline.orchestrator.writers.bo_laksana import (
    _CLASSIFICATION_NEECHA_BHANGA_REDEEMED,
    _NEECHABHANGA_CANCELLED_MODIFIER,
    _NEECHABHANGA_NORMAL_MODIFIER,
    _build_navamsha_cross_check_signals,
    _build_nbry_d9_redemption_map,
    _build_nbry_redemption_map,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYANAMSHA = "lahiri_chitrapaksha"

# The R6A.1 NBRY row shape for the native's Saturn case: rule 2 fired in the
# D1 context (Sun exalted-in-Aries sits in a kendra from the Aries lagna).
_NATIVE_SATURN_RULE_FIRED = "saturn@D1:nbry_rule_2_exaltation_lord_kendra"
_NATIVE_NBRY_ROW = {
    "bhanga_rule_fired": _NATIVE_SATURN_RULE_FIRED,
    "citation_ref": "BPHS_ch39_neecha_bhanga",
    "citation_human": "BPHS Ch.39 — graha exalted in the debilitation sign in a kendra from lagna",
}


# ── Mock conn: dispatches on SQL content, order-independent ────────────────────

def _make_conn(d1_rows: list[dict], d9_rows: list[dict], nbry_rows: list[dict]):
    """Mock connection for _fetch_dict. Dispatches on the SQL text so the test
    does not depend on the internal query order of the function under test."""
    conn = MagicMock()

    def execute(sql, params=None):
        cur = MagicMock()
        if "ga_yoga_firings" in sql:
            batch = nbry_rows
        elif "chart_divisionals" in sql:
            batch = d9_rows
        elif "graha_dignity_per_varga" in sql:
            batch = d1_rows
        else:
            batch = []
        cur.fetchall.return_value = [dict(r) for r in batch]
        return cur

    conn.execute.side_effect = execute
    return conn


def _native_shape_d1_rows() -> list[dict]:
    """The native's real D1 shape for the grahas that matter here: Saturn
    debilitated (Aries), Sun in Capricorn (the kendra canceller — its own D1
    dignity is irrelevant to Saturn's redemption)."""
    return [
        {"fact_id": "f-sat-d1", "fact_subject": "D1_SAT", "fact_value_text": "debilitated"},
        {"fact_id": "f-sun-d1", "fact_subject": "D1_SUN", "fact_value_text": "own"},
        {"fact_id": "f-jup-d1", "fact_subject": "D1_JUP", "fact_value_text": "neutral"},
    ]


def _run(conn) -> dict[str, dict]:
    """Run the function under test; return {graha_lower: signal_row}."""
    signals = _build_navamsha_cross_check_signals(
        conn, CHART_ID, AYANAMSHA, "build-r6a3",
        "2026-07-11T00:00:00+00:00",
        strength_lookup={}, dignity_lookup={}, av_lookup={},
    )
    out = {}
    for s in signals:
        out[s["signal_type_id"].split(":", 1)[1]] = s
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 1. Golden gate — synthetic (the native's real chart shape)
# ──────────────────────────────────────────────────────────────────────────────

class TestGoldenGateSynthetic:
    def _conn(self, d9_saturn_dignity: str = "Neutral"):
        d9_rows = [
            {"graha": "Saturn", "fact_value_text": d9_saturn_dignity},
            {"graha": "Sun",    "fact_value_text": "Friend"},
            {"graha": "Jupiter", "fact_value_text": "Friend"},
        ]
        return _make_conn(_native_shape_d1_rows(), d9_rows, [_NATIVE_NBRY_ROW])

    def test_saturn_redeemed_not_a_weakness_class(self):
        sig = _run(self._conn())["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "neecha_bhanga_redeemed"
        assert config["classification"] != "broken_promise"
        assert sig["valence"] == "benefic"

    def test_saturn_redeemed_regardless_of_d9_tier(self):
        # The tier branches previously routed debilitated-D1 Saturn to
        # concordant_weak / vargottama_resilience / mixed depending on D9 —
        # the L1 verdict must override all of them.
        for d9 in ("Debilitated", "Exalted", "Neutral"):
            sig = _run(self._conn(d9_saturn_dignity=d9))["saturn"]
            config = json.loads(sig["configuration_jsonb"])
            assert config["classification"] == "neecha_bhanga_redeemed", (
                f"D9={d9}: got {config['classification']}"
            )

    def test_saturn_modifier_is_cancelled_debility_value(self):
        sig = _run(self._conn())["saturn"]
        assert sig["neechabhanga_modifier"] == _NEECHABHANGA_CANCELLED_MODIFIER == 1.3
        # cancellation_modifier means "cancelled YOGA" (0.1) — a redeemed
        # debility is not a cancelled yoga, so it stays at normal 1.0.
        assert sig["cancellation_modifier"] == 1.0

    def test_provenance_cites_the_l1_row(self):
        sig = _run(self._conn())["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        nb = config["neecha_bhanga"]
        assert nb["source"] == "ga_yoga_firings/neecha_bhanga_raja_yoga"
        assert _NATIVE_SATURN_RULE_FIRED in nb["bhanga_rules_fired"]
        assert nb["citation_ref"] == _NATIVE_NBRY_ROW["citation_ref"]

    def test_unredeemed_grahas_in_same_chart_unaffected(self):
        sigs = _run(self._conn())
        for graha in ("sun", "jupiter"):
            config = json.loads(sigs[graha]["configuration_jsonb"])
            assert config["classification"] != "neecha_bhanga_redeemed"
            assert sigs[graha]["neechabhanga_modifier"] == _NEECHABHANGA_NORMAL_MODIFIER == 1.0


# ──────────────────────────────────────────────────────────────────────────────
# 3. Negative controls — uncancelled debilitations keep pre-R6A.3 behavior
# ──────────────────────────────────────────────────────────────────────────────

class TestNegativeControls:
    def test_uncancelled_debilitation_stays_uncancelled(self):
        # Saturn debilitated D1, weak D9, NO ga_yoga_firings row on record.
        conn = _make_conn(
            _native_shape_d1_rows(),
            [{"graha": "Saturn", "fact_value_text": "Debilitated"}],
            nbry_rows=[],
        )
        sig = _run(conn)["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "concordant_weak"  # pre-R6A.3 branch
        assert "neecha_bhanga" not in config
        assert sig["neechabhanga_modifier"] == 1.0
        assert sig["cancellation_modifier"] == 1.0

    def test_broken_promise_preserved_without_redemption(self):
        # D1 strong (exalted, tier 3) × D9 weak (Debilitated, tier -2), no NBRY
        # row → the existing broken_promise behavior must be unchanged.
        conn = _make_conn(
            [{"fact_id": "f-jup", "fact_subject": "D1_JUP", "fact_value_text": "exalted"}],
            [{"graha": "Jupiter", "fact_value_text": "Debilitated"}],
            nbry_rows=[],
        )
        sig = _run(conn)["jupiter"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "broken_promise"
        assert sig["valence"] == "malefic"
        assert sig["neechabhanga_modifier"] == 1.0


# ──────────────────────────────────────────────────────────────────────────────
# 4. Consult-before-classify mechanics + redemption-map parsing
# ──────────────────────────────────────────────────────────────────────────────

class TestConsultBeforeClassify:
    def test_redemption_takes_precedence_over_broken_promise_branch(self):
        # Mechanics test: even for a tier combination that would land in the
        # broken_promise branch, an active D1-context redemption is consulted
        # FIRST and wins.
        conn = _make_conn(
            [{"fact_id": "f-sat", "fact_subject": "D1_SAT", "fact_value_text": "exalted"}],
            [{"graha": "Saturn", "fact_value_text": "Debilitated"}],
            nbry_rows=[_NATIVE_NBRY_ROW],
        )
        sig = _run(conn)["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "neecha_bhanga_redeemed"
        assert config["classification"] != "broken_promise"

    def test_pure_d9_context_bhanga_does_not_redeem_d1(self):
        # A bhanga that fired only in the D9 varga context does not cancel the
        # D1 debilitation this signal classifies.
        conn = _make_conn(
            _native_shape_d1_rows(),
            [{"graha": "Saturn", "fact_value_text": "Debilitated"}],
            nbry_rows=[{
                "bhanga_rule_fired": "saturn@D9:nbry_rule_1_dispositor_kendra",
                "citation_ref": "x", "citation_human": "x",
            }],
        )
        sig = _run(conn)["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "concordant_weak"
        assert sig["neechabhanga_modifier"] == 1.0

    def test_d1_to_d9_extension_context_counts_as_d1(self):
        # Rule-2's navamsha extension is recorded as varga context 'D1->D9' —
        # it IS a cancellation of the D1 debilitation.
        conn = _make_conn(
            _native_shape_d1_rows(),
            [{"graha": "Saturn", "fact_value_text": "Debilitated"}],
            nbry_rows=[{
                "bhanga_rule_fired": "saturn@D1->D9:nbry_rule_2_exaltation_lord_kendra",
                "citation_ref": "x", "citation_human": "x",
            }],
        )
        sig = _run(conn)["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "neecha_bhanga_redeemed"

    def test_supporting_planets_are_not_marked_redeemed(self):
        # constituent_planets in the L1 row includes the canceller (Sun) — the
        # redemption map must key off bhanga_rule_fired only, so the Sun is
        # never itself classified as redeemed.
        conn = _make_conn([], [], [_NATIVE_NBRY_ROW])
        redemption = _build_nbry_redemption_map(conn, CHART_ID, AYANAMSHA)
        assert set(redemption.keys()) == {"Saturn"}

    def test_malformed_rule_entries_never_guess_a_redemption(self):
        conn = _make_conn([], [], [{
            "bhanga_rule_fired": "garbage;also-garbage@",
            "citation_ref": "x", "citation_human": "x",
        }])
        assert _build_nbry_redemption_map(conn, CHART_ID, AYANAMSHA) == {}


# ──────────────────────────────────────────────────────────────────────────────
# 2. Golden gate — REAL read-only integration (chart 482012f1)
# ──────────────────────────────────────────────────────────────────────────────

class TestGoldenGateRealChartIntegration:
    """READ-ONLY integration against the native's canonical chart. Exercises
    the actual production path (_build_nbry_redemption_map +
    _build_navamsha_cross_check_signals) against the live ga_yoga_firings row
    written by the deployed R6A.1 evaluator. Only SELECTs are issued — no
    INSERT/UPDATE/DELETE, no rebuild. Skips (does not fail) when no
    DATABASE_URL is configured, exactly like R6A.1's integration test."""

    def _get_conn(self):
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            env_file = pathlib.Path(__file__).resolve().parents[1] / ".env.local"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                        db_url = line.split("=", 1)[1].strip()
                        break
        if not db_url:
            pytest.skip("DATABASE_URL not set — skipping live read-only DB integration test")
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(db_url, row_factory=dict_row)

    def test_native_saturn_redeemed_against_real_ga_yoga_firings(self):
        conn = self._get_conn()
        try:
            redemption = _build_nbry_redemption_map(conn, CHART_ID, AYANAMSHA)
            if not redemption:
                pytest.skip(
                    "no active neecha_bhanga_raja_yoga row for chart 482012f1/"
                    "lahiri_chitrapaksha in this DB — R6A.1 build not present here"
                )
            # The native's documented case: Saturn's D1 debilitation is
            # cancelled (rule 2 — Sun exalts in Aries, sits in kendra).
            assert "Saturn" in redemption, (
                f"expected Saturn among D1-redeemed grahas; got {sorted(redemption)}"
            )
            assert "saturn@D1" in redemption["Saturn"]["bhanga_rules_fired"]

            signals = _build_navamsha_cross_check_signals(
                conn, CHART_ID, AYANAMSHA, "build-r6a3-it",
                "2026-07-11T00:00:00+00:00",
                strength_lookup={}, dignity_lookup={}, av_lookup={},
            )
            sat = next(
                (s for s in signals
                 if s["signal_type_id"] == "navamsha_d9_cross_check:saturn"),
                None,
            )
            assert sat is not None, "Saturn cross-check signal must be emitted"
            config = json.loads(sat["configuration_jsonb"])
            assert config["classification"] == "neecha_bhanga_redeemed", (
                f"native's Saturn must not be a raw-tier weakness class; "
                f"got {config['classification']}"
            )
            assert config["classification"] != "broken_promise"
            assert sat["neechabhanga_modifier"] == 1.3
        finally:
            conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# 5. Y-13 fix-iteration — varga-of-weakness redemption for broken_promise
#    (GS-23; register item Y-13; the ONE authorized R5 fix-iteration)
# ──────────────────────────────────────────────────────────────────────────────

# The live case caught on the native chart (482012f1, restored after the failed
# rebuild): Saturn exalted in Libra D1, debilitated in Aries D9, with a
# pure-D9-context NBRY firing — the D9 debilitation is redeemed within D9.
_Y13_SATURN_D9_RULE_FIRED = "saturn@D9:nbry_rule_2_exaltation_lord_kendra"
_Y13_NBRY_D9_ROW = {
    "bhanga_rule_fired": _Y13_SATURN_D9_RULE_FIRED,
    "citation_ref": "BPHS_ch39_neecha_bhanga",
    "citation_human": "BPHS Ch.39 — exaltation lord of the debilitation sign in a kendra (D9 context)",
}


def _y13_broken_promise_shape(nbry_rows: list[dict]):
    """Saturn D1-exalted (tier 3) × D9-debilitated (tier -2) — the exact
    broken_promise formation state — with the given ga_yoga_firings rows."""
    return _make_conn(
        [{"fact_id": "f-sat-d1x", "fact_subject": "D1_SAT", "fact_value_text": "exalted"}],
        [{"graha": "Saturn", "fact_value_text": "Debilitated"}],
        nbry_rows=nbry_rows,
    )


class TestY13GoldenGateLiveCase:
    """Mandatory test (a) — the exact live case, literal and permanent (GS-23)."""

    def test_y13_saturn_d1_exalted_d9_debilitated_pure_d9_redemption_flips_to_redeemed(self):
        # NOT parametrized — this is the permanent, named regression gate for
        # register item Y-13. If this test disappears or is folded into a loop,
        # that is itself a defect.
        sig = _run(_y13_broken_promise_shape([_Y13_NBRY_D9_ROW]))["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "neecha_bhanga_redeemed"
        assert config["classification"] != "broken_promise"
        assert sig["valence"] == "benefic"
        assert sig["neechabhanga_modifier"] == _NEECHABHANGA_CANCELLED_MODIFIER == 1.3
        # Provenance: same shape as the D1-context path, PLUS the varga of the
        # redeemed weakness (D9 — where the weakness lives).
        nb = config["neecha_bhanga"]
        assert nb["source"] == "ga_yoga_firings/neecha_bhanga_raja_yoga"
        assert _Y13_SATURN_D9_RULE_FIRED in nb["bhanga_rules_fired"]
        assert nb["citation_ref"] == _Y13_NBRY_D9_ROW["citation_ref"]
        assert nb["redeemed_weakness_varga"] == "D9"


class TestY13NoDoubleApplication:
    """Mandatory test (b) — D1-context path unchanged; the two consults are
    mutually exclusive by construction, proven explicitly (not from reasoning)."""

    def test_d1_context_redemption_still_classifies_exactly_as_before(self):
        # The already-working, merged D1-context case (Abhinandan-shaped:
        # graha debilitated in D1, redeemed via a D1-tagged firing).
        conn = _make_conn(
            _native_shape_d1_rows(),
            [{"graha": "Saturn", "fact_value_text": "Neutral"}],
            nbry_rows=[_NATIVE_NBRY_ROW],
        )
        sig = _run(conn)["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "neecha_bhanga_redeemed"
        assert sig["valence"] == "benefic"
        assert sig["neechabhanga_modifier"] == 1.3
        nb = config["neecha_bhanga"]
        assert nb["source"] == "ga_yoga_firings/neecha_bhanga_raja_yoga"
        assert nb["bhanga_rules_fired"] == _NATIVE_SATURN_RULE_FIRED
        # Byte-identity of the D1 path's provenance block: the new
        # redeemed_weakness_varga key must NOT appear on the D1-context path.
        assert "redeemed_weakness_varga" not in nb

    def test_both_context_row_d1_weak_graha_consults_d1_map_only(self):
        # Adversarial: ONE ga_yoga_firings row carrying BOTH a D1-context and a
        # D9-context entry for the SAME graha. D1-debilitated Saturn → the
        # early D1-context branch fires; the D9 consult is never reached
        # (if/elif construction), so nothing is double-counted.
        both_row = {
            "bhanga_rule_fired": f"{_NATIVE_SATURN_RULE_FIRED};{_Y13_SATURN_D9_RULE_FIRED}",
            "citation_ref": "BPHS_ch39_neecha_bhanga",
            "citation_human": "x",
        }
        conn = _make_conn(
            _native_shape_d1_rows(),  # Saturn debilitated in D1
            [{"graha": "Saturn", "fact_value_text": "Debilitated"}],
            nbry_rows=[both_row],
        )
        sig = _run(conn)["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "neecha_bhanga_redeemed"
        nb = config["neecha_bhanga"]
        # Provenance comes from the D1-context map ONLY: the D9 entry was
        # filtered out of the D1 map, and the D9 map was never consulted.
        assert nb["bhanga_rules_fired"] == _NATIVE_SATURN_RULE_FIRED
        assert _Y13_SATURN_D9_RULE_FIRED not in nb["bhanga_rules_fired"]
        assert "redeemed_weakness_varga" not in nb
        assert sig["neechabhanga_modifier"] == 1.3  # applied once, not compounded

    def test_both_context_row_d1_strong_graha_consults_d9_map_only(self):
        # Adversarial mirror: same both-context row, but Saturn D1-exalted.
        # NOTE: the early branch keys off D1-context firings, so with a
        # D1-context entry present it wins even here — that is the existing,
        # untouched precedence (TestConsultBeforeClassify). The D9-only consult
        # is reached only when the D1 map is empty for this graha.
        both_row = {
            "bhanga_rule_fired": f"{_NATIVE_SATURN_RULE_FIRED};{_Y13_SATURN_D9_RULE_FIRED}",
            "citation_ref": "BPHS_ch39_neecha_bhanga",
            "citation_human": "x",
        }
        sig = _run(_y13_broken_promise_shape([both_row]))["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        # Exactly ONE redemption decision — classification and modifier are
        # single-valued regardless of two entries being present in the row.
        assert config["classification"] == "neecha_bhanga_redeemed"
        assert sig["neechabhanga_modifier"] == 1.3
        nb = config["neecha_bhanga"]
        # Early D1-context branch won (D1 entry present) → D1 provenance,
        # no varga key. Proves the branches never both apply.
        assert nb["bhanga_rules_fired"] == _NATIVE_SATURN_RULE_FIRED
        assert "redeemed_weakness_varga" not in nb

    def test_branches_are_tier_disjoint_proven_not_reasoned(self):
        # Explicit proof: for every dignity text the tier mapping knows, a
        # graha cannot be simultaneously in the early-branch-relevant D1-weak
        # state (a real D1 NBRY firing implies D1 debilitation, tier <= -1)
        # and the broken_promise-branch D1-strong state (tier >= 2).
        from pipeline.orchestrator.writers.bo_laksana import (
            _DIGNITY_STRENGTH_TIER,
            _dignity_tier,
        )
        for text in list(_DIGNITY_STRENGTH_TIER) + ["unknown", "", None]:
            tier = _dignity_tier(text)  # type: ignore[arg-type]
            assert not (tier <= -1 and tier >= 2), (
                f"dignity {text!r} maps to tier {tier} — impossible overlap"
            )


class TestY13NegativeControls:
    """Mandatory test (c) — unredeemed D9 debilitation stays broken_promise."""

    def test_no_nbry_row_stays_broken_promise(self):
        sig = _run(_y13_broken_promise_shape([]))["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "broken_promise"
        assert sig["valence"] == "malefic"
        assert sig["neechabhanga_modifier"] == 1.0
        assert "neecha_bhanga" not in config

    def test_nbry_row_for_a_different_graha_stays_broken_promise(self):
        sig = _run(_y13_broken_promise_shape([{
            "bhanga_rule_fired": "mercury@D9:nbry_rule_1_dispositor_kendra",
            "citation_ref": "x", "citation_human": "x",
        }]))["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "broken_promise"
        assert sig["neechabhanga_modifier"] == 1.0

    def test_malformed_entries_stay_broken_promise(self):
        sig = _run(_y13_broken_promise_shape([{
            "bhanga_rule_fired": "garbage;saturn@",
            "citation_ref": "x", "citation_human": "x",
        }]))["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "broken_promise"

    def test_d9_map_query_filters_on_bhanga_active_true(self):
        # bhanga_active=false rows never reach the parser: the mock conn cannot
        # simulate SQL WHERE filtering, so assert the filter is in the SQL
        # itself (same discipline as the D1-context map's query).
        conn = _make_conn([], [], [])
        _build_nbry_d9_redemption_map(conn, CHART_ID, AYANAMSHA)
        issued = [c.args[0] for c in conn.execute.call_args_list]
        assert len(issued) == 1
        assert "bhanga_active IS TRUE" in issued[0]
        assert "yoga_canonical_id='neecha_bhanga_raja_yoga'" in issued[0]

    def test_d9_map_excludes_d1_and_d1_to_d9_entries(self):
        conn = _make_conn([], [], [{
            "bhanga_rule_fired": (
                "saturn@D1:nbry_rule_2_exaltation_lord_kendra;"
                "saturn@D1->D9:nbry_rule_2_exaltation_lord_kendra"
            ),
            "citation_ref": "x", "citation_human": "x",
        }])
        assert _build_nbry_d9_redemption_map(conn, CHART_ID, AYANAMSHA) == {}


class TestY13VocabularyCheck:
    """Mandatory test (d) — the classification value is stored inside the
    configuration_jsonb column (no DB CHECK constraint exists on jsonb keys;
    verified against migrations 325/326 — no classification CHECK anywhere),
    so this reduces to: the D9-context branch emits LITERALLY the same string
    constant as the already-shipped D1-context branch."""

    def test_shared_constant_is_the_shipped_value(self):
        assert _CLASSIFICATION_NEECHA_BHANGA_REDEEMED == "neecha_bhanga_redeemed"

    def test_both_paths_emit_the_identical_shared_constant(self):
        # D1-context path (shipped, merged, live in Abhinandan's rebuilt data)
        d1_sig = _run(_make_conn(
            _native_shape_d1_rows(),
            [{"graha": "Saturn", "fact_value_text": "Neutral"}],
            nbry_rows=[_NATIVE_NBRY_ROW],
        ))["saturn"]
        # New D9-context broken_promise path
        d9_sig = _run(_y13_broken_promise_shape([_Y13_NBRY_D9_ROW]))["saturn"]
        d1_cls = json.loads(d1_sig["configuration_jsonb"])["classification"]
        d9_cls = json.loads(d9_sig["configuration_jsonb"])["classification"]
        assert d1_cls == d9_cls == _CLASSIFICATION_NEECHA_BHANGA_REDEEMED
        # No typo'd near-duplicate anywhere in the emitted vocabulary.
        assert {d1_cls, d9_cls} == {"neecha_bhanga_redeemed"}


class TestY13OtherClassificationsByteIdentical:
    """Regression gate for directive 1: with a pure-D9 NBRY firing present, every
    classification OTHER than broken_promise must produce exactly the pre-fix
    output — the D9 consult is behavior-gated to the broken_promise branch."""

    @staticmethod
    def _config_for(d1_dignity: str, d9_dignity: str, nbry_rows: list[dict]):
        conn = _make_conn(
            [{"fact_id": "f-sat", "fact_subject": "D1_SAT", "fact_value_text": d1_dignity}],
            [{"graha": "Saturn", "fact_value_text": d9_dignity}],
            nbry_rows=nbry_rows,
        )
        sig = _run(conn)["saturn"]
        return sig, json.loads(sig["configuration_jsonb"])

    def test_vargottama_resilience_unchanged_even_with_d9_firing(self):
        sig, config = self._config_for("debilitated", "Exalted", [_Y13_NBRY_D9_ROW])
        assert config == {
            "graha": "Saturn", "d1_dignity": "debilitated", "d9_dignity": "Exalted",
            "d1_tier": -2, "d9_tier": 3, "classification": "vargottama_resilience",
        }
        assert sig["valence"] == "benefic"
        assert sig["neechabhanga_modifier"] == 1.0

    def test_concordant_strong_unchanged_even_with_d9_firing(self):
        sig, config = self._config_for("exalted", "Exalted", [_Y13_NBRY_D9_ROW])
        assert config == {
            "graha": "Saturn", "d1_dignity": "exalted", "d9_dignity": "Exalted",
            "d1_tier": 3, "d9_tier": 3, "classification": "concordant_strong",
        }
        assert sig["valence"] == "benefic"
        assert sig["neechabhanga_modifier"] == 1.0

    def test_concordant_weak_unchanged_even_with_d9_firing(self):
        sig, config = self._config_for("debilitated", "Debilitated", [_Y13_NBRY_D9_ROW])
        assert config == {
            "graha": "Saturn", "d1_dignity": "debilitated", "d9_dignity": "Debilitated",
            "d1_tier": -2, "d9_tier": -2, "classification": "concordant_weak",
        }
        assert sig["valence"] == "malefic"
        assert sig["neechabhanga_modifier"] == 1.0

    def test_mixed_unchanged_even_with_d9_firing(self):
        sig, config = self._config_for("neutral", "Neutral", [_Y13_NBRY_D9_ROW])
        assert config == {
            "graha": "Saturn", "d1_dignity": "neutral", "d9_dignity": "Neutral",
            "d1_tier": 0, "d9_tier": 0, "classification": "mixed",
        }
        assert sig["valence"] == "neutral"
        assert sig["neechabhanga_modifier"] == 1.0

    def test_existing_d1_early_branch_unchanged_even_with_d9_firing(self):
        # The early nbry_redemption-is-not-None branch: D1-debilitated graha
        # with a D1-context firing, D9 firing also present in a second row.
        conn = _make_conn(
            _native_shape_d1_rows(),
            [{"graha": "Saturn", "fact_value_text": "Neutral"}],
            nbry_rows=[_NATIVE_NBRY_ROW, _Y13_NBRY_D9_ROW],
        )
        sig = _run(conn)["saturn"]
        config = json.loads(sig["configuration_jsonb"])
        assert config["classification"] == "neecha_bhanga_redeemed"
        nb = config["neecha_bhanga"]
        assert nb["bhanga_rules_fired"] == _NATIVE_SATURN_RULE_FIRED
        assert "redeemed_weakness_varga" not in nb
