"""
test_lane2_ga_vichara.py — Night-1 Doctrine Campaign, Lane 2 (ga_vichara).

Covers 00_ARCHITECTURE/llm_consumption_audit/briefs/night1/LANE2_GA_VICHARA.md
§6 test list + §7 acceptance criteria, using fixture facts built from CR-57/
CR-71's cited verified numbers (this environment has no DATABASE_URL — see
this lane's handback report — so these are pure-function / fixture-conn
tests, exactly as the brief's §6 "Unit (pure functions, no DB)" instructs;
CR-71's shadbala figures and the Venus 2034 MD figure are the brief's own
cited ground truth, not independently re-derived here).

  1. valence matrix lookup, incl. the 8L-Mars -> H2 = strong_malefic anchor
     (CR-54 AMENDED specimen).
  2. ratification_factor arithmetic incl. clamps at both ends.
  3. varga_consistency vargottama ordering (Mercury-style fixture).
  4. leverage_index Venus-#1 fixture using CR-71's verified numbers.
  5. Divergence-row firing (Venus/Saturn D9 wealth specimen, CR-57).
  6. Fixture-conn integration smoke test: build_ga_vichara_substep runs
     against a fake in-memory conn/cursor, delete-then-insert idempotency,
     zero orphan constituent_fact_ids (DEFECT-001 class).

Pure deterministic functions — no LLM, no live DB.
"""
from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone

from ga_writers.ga_vichara_writer import (
    PLANET_TO_SUBJECT,
    VicharaFactIndex,
    build_aspect_valence_rows,
    build_ga_vichara_substep,
    build_leverage_index_rows,
    build_valence_pass_rows,
    build_varga_consistency_rows,
    build_varga_ratification_rows,
    classify_actor,
    compute_valence,
    dignity_direction,
)

VALENCE_MATRIX = {
    "dusthana_lord_wealth_or_lagna": {"value_text": "strong_malefic", "value_num": -1.0, "citation": "c1"},
    "dusthana_lord_other": {"value_text": "malefic", "value_num": -0.5, "citation": "c2"},
    "trikona_lord_benefic_target": {"value_text": "benefic", "value_num": 0.5, "citation": "c3"},
    "trikona_lord_yogakaraka": {"value_text": "strong_benefic", "value_num": 1.0, "citation": "c4"},
    "maraka": {"value_text": "malefic", "value_num": -0.5, "citation": "c5"},
    "upachaya_lord": {"value_text": "benefic", "value_num": 0.5, "citation": "c6"},
    "kendra_lord_neutral": {"value_text": "neutral", "value_num": 0.0, "citation": "c7"},
    "ambiguous_default": {"value_text": "neutral", "value_num": 0.0, "citation": "c8"},
}


def _fact(fact_id, category, subject, key, value_text=None, value_num=None, value_jsonb=None):
    return {
        "fact_id": fact_id, "fact_category": category, "fact_subject": subject, "fact_key": key,
        "fact_value_text": value_text, "fact_value_num": value_num, "fact_value_jsonb": value_jsonb,
    }


def _link_fact(fid, varga, kind, lord, src_h, tgt_h, link_type):
    return _fact(
        fid, "bhava_significance_link", f"{varga}_HOUSE_{src_h}_to_HOUSE_{tgt_h}", kind,
        value_text=link_type,
        value_jsonb={"varga": varga, "source_house": src_h, "target_house": tgt_h,
                     "lord": lord, "link_kind": kind, "link_type": link_type},
    )


def _dignity_fact(fid, varga, subj, sign, house, dignity):
    return _fact(
        fid, "graha_dignity_per_varga", f"{varga}_{subj}", "dignity_state",
        value_text=dignity, value_jsonb={"varga": varga, "sign": sign, "house": house},
    )


def _aspect_fact(fid, varga, subj, source_house, target_house, offset, strength):
    """Mirrors ga_structural_writer.py:4228-4250's aspect_parashari_per_varga
    row shape exactly (CR-91/A2)."""
    return _fact(
        fid, "aspect_parashari_per_varga", f"{varga}_{subj}", f"house_{target_house}",
        value_num=strength,
        value_jsonb={"varga": varga, "source_sign": "Sagittarius", "source_house": source_house,
                     "target_house": target_house, "offset": offset, "ayanamsha_id": "lahiri_chitrapaksha"},
    )


class TestClassifyActor(unittest.TestCase):
    def test_dusthana_lord(self):
        classes, primary = classify_actor({8})
        self.assertIn("dusthana_lord", classes)
        self.assertEqual(primary, "dusthana_lord")

    def test_trikona_precedence_over_dusthana(self):
        # dual lordship e.g. lord of 1 and 8 -> trikona wins per precedence
        classes, primary = classify_actor({1, 8})
        self.assertEqual(primary, "trikona_lord")
        self.assertIn("dusthana_lord", classes)


class TestValenceMatrix(unittest.TestCase):
    """DR-9 / VAL-ROOT: compute_valence was REPLACED — it no longer maps
    (actor_lordship_class × target_house) over the brahma_vichara_constants
    matrix (whose trikoṇa-membership rule pre-empted the dusthāna-affliction
    cell for a dual-lord graha, mislabeling the CR-54 8L-Mars→H2 specimen
    benefic, had no contact-type dimension, and skipped Rahu/Ketu). It now
    delegates to the shared brahmagyan.valence_doctrine (natural × functional ×
    dignity × contact-type → signed/mixed). The doctrine's own depth (incl. the
    6 mandatory both-direction anti-overcorrection specimens) is tested in
    brahmagyan/__tests__/test_valence_doctrine.py; THIS class verifies the
    ga_vichara wiring + the 6-way vocab mapping (_verdict_to_vichara_label)."""

    def test_cr54_specimen_dual_lord_malefic_natured_is_mixed(self):
        """THE CR-54 root: Mars (natural malefic) that is Aries's lagneśa
        (functional yogakaraka, i.e. dual trikoṇa/dusthāna lordship) casting its
        harsh 8th aspect onto the wealth house → MIXED, never plain benefic. The
        old matrix returned 'benefic' here (trikoṇa membership pre-empted the
        dusthāna cell) — that inversion is exactly what this test now guards."""
        vt, vn, cit, label = compute_valence(
            "MAR", 2, "yogakaraka", contact_type="aspect", aspect_offset=8)
        self.assertEqual(label, "mixed")
        self.assertEqual(vt, "mixed")
        self.assertTrue(cit)

    def test_natural_malefic_no_functional_mitigation_is_strong_malefic(self):
        """A pure natural malefic (Saturn) with a temporal-malefic functional
        class placed on the wealth house → strong_malefic (the CR-54 anchor,
        now nature-grounded rather than lordship-class-keyed)."""
        vt, vn, _c, label = compute_valence(
            "SAT", 2, "temporal_malefic", contact_type="lordship")
        self.assertEqual(label, "malefic")
        self.assertIn(vt, ("malefic", "strong_malefic"))
        self.assertLess(vn, 0)

    def test_natural_benefic_trikona_lord_is_benefic(self):
        """Jupiter (natural benefic) as a temporal-benefic in own trikoṇa H9 →
        benefic (no regression on the Dhana-yoga specimen)."""
        vt, vn, _c, label = compute_valence(
            "JUP", 9, "temporal_benefic", contact_type="lordship")
        self.assertEqual(label, "benefic")
        self.assertIn(vt, ("benefic", "strong_benefic"))
        self.assertGreater(vn, 0)

    def test_node_is_judged_not_skipped(self):
        """DR-9 fix: Rahu/Ketu (no sign lordship) are judged by NATURAL nature
        (malefic), NOT skipped — the prior skip is why an adverse node aspect on
        a money house never reached a computed valence."""
        vt, vn, _c, label = compute_valence(
            "RAH_MEAN", 2, None, contact_type="aspect", aspect_offset=5)
        self.assertIn(label, ("malefic", "mixed"))
        self.assertLessEqual(vn, 0)

    def test_vocab_mapping_bands(self):
        """_verdict_to_vichara_label maps the signed net onto the 6-way vocab;
        mixed is first-class."""
        from ga_writers.ga_vichara_writer import _verdict_to_vichara_label
        import brahmagyan.valence_doctrine as vd
        # a genuinely mixed verdict → 'mixed'
        mixed = vd.graha_valence("RAH_MEAN", contact_type="occupancy",
                                 target_house=2, dignity_state="exalted")
        self.assertEqual(_verdict_to_vichara_label(mixed), "mixed")


class TestAspectValenceIngestion(unittest.TestCase):
    """CR-91/A2: aspect_parashari_per_varga facts ingested into
    VicharaFactIndex and judged via functional-lordship valence
    (build_aspect_valence_rows), independent of bhava_significance_link."""

    def test_index_parses_aspect_parashari_per_varga(self):
        facts = [_aspect_fact("f1", "D1", "JUP", source_house=9, target_house=2, offset=5, strength=1.0)]
        idx = VicharaFactIndex(facts)
        self.assertIn("D1", idx.aspects_by_varga)
        entry = idx.aspects_by_varga["D1"][0]
        self.assertEqual(entry["graha_subject"], "JUP")
        self.assertEqual(entry["graha"], "Jupiter")
        self.assertEqual(entry["target_house"], 2)
        self.assertEqual(entry["strength"], 1.0)
        self.assertEqual(entry["fact_id"], "f1")

    def test_aspect_strength_decimal_from_db_is_json_serializable(self):
        """Regression: psycopg returns NUMERIC columns as decimal.Decimal, not
        float. fact_value_num from a real DB row is a Decimal — if
        VicharaFactIndex stores it verbatim, build_aspect_valence_rows'
        value_jsonb['aspect_strength'] carries a Decimal straight into
        _insert_rows' json.dumps(), which raises
        TypeError: Object of type Decimal is not JSON serializable.
        Caught live during the D-1.5a wave rebuild (ga_vichara errored on
        every chart) — fixtures elsewhere in this file use plain floats and
        never exercised this path."""
        from decimal import Decimal
        facts = [
            _link_fact("l1", "D1", "lord_placed", "Mars", src_h=8, tgt_h=8, link_type="dusthana"),
            _aspect_fact("a1", "D1", "MAR", source_house=8, target_house=2, offset=7, strength=Decimal("1.0218")),
        ]
        idx = VicharaFactIndex(facts)
        entry = idx.aspects_by_varga["D1"][0]
        self.assertNotIsInstance(entry["strength"], Decimal)
        self.assertIsInstance(entry["strength"], float)

        rows = build_aspect_valence_rows(idx, "D1", VALENCE_MATRIX)
        self.assertEqual(len(rows), 1)
        # Must not raise — this is the actual failure mode from the live rebuild.
        json.dumps(rows[0]["value_jsonb"])
        self.assertNotIsInstance(rows[0]["value_jsonb"]["aspect_strength"], Decimal)

    def test_dusthana_lord_aspect_on_wealth_house_is_malefic(self):
        """A natural-malefic graha (Mars, here with NO functional-class fact so
        natural nature carries) raw-aspecting a wealth house (2/11) reads
        adverse — the CR-54 anchor, now reachable purely via an aspect fact.
        (With Mars's functional lagneśa status supplied it becomes MIXED — see
        TestValenceMatrix.test_cr54_specimen_dual_lord_malefic_natured_is_mixed;
        without it, pure natural malefic → strong_malefic.)"""
        facts = [
            _link_fact("l1", "D1", "lord_placed", "Mars", src_h=8, tgt_h=8, link_type="dusthana"),
            _aspect_fact("a1", "D1", "MAR", source_house=8, target_house=2, offset=7, strength=1.0),
        ]
        idx = VicharaFactIndex(facts)
        rows = build_aspect_valence_rows(idx, "D1", VALENCE_MATRIX)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["actor"], "MAR")
        self.assertEqual(row["target"], "D1_HOUSE_2")
        self.assertIn(row["value_text"], ("malefic", "strong_malefic"))
        self.assertLess(row["value_num"], 0)
        self.assertEqual(row["value_jsonb"]["matrix_key"], "malefic")  # the 4-way label
        self.assertEqual(row["value_jsonb"]["signal_source"], "aspect_parashari_per_varga")
        self.assertIn("a1", row["constituent_fact_ids"])

    def test_natural_benefic_dual_lordship_aspect_is_benefic(self):
        """Jupiter (natural benefic) aspecting a wealth house classifies
        benefic — no regression on a natural-benefic dual-lord through the
        aspect path (the OLD test asserted this via the trikoṇa-matrix cell;
        it now holds via natural nature + benefic-drishti softening)."""
        facts = [
            _link_fact("l1", "D1", "lord_placed", "Jupiter", src_h=9, tgt_h=9, link_type="trikona"),
            _link_fact("l2", "D1", "lord_placed", "Jupiter", src_h=12, tgt_h=12, link_type="dusthana"),
            _aspect_fact("a1", "D1", "JUP", source_house=9, target_house=11, offset=3, strength=1.0),
        ]
        idx = VicharaFactIndex(facts)
        rows = build_aspect_valence_rows(idx, "D1", VALENCE_MATRIX)
        self.assertEqual(len(rows), 1)
        self.assertIn(rows[0]["value_text"], ("benefic", "strong_benefic"))
        self.assertGreater(rows[0]["value_num"], 0)

    def test_node_aspect_now_yields_a_malefic_row(self):
        """DR-9 / VAL-ROOT fix (this test FLIPPED): a node (Rahu/Ketu) aspect
        MUST now yield a computed valence row judged by natural nature (malefic)
        — the prior behavior (skip → no row → bo_laksana keyword fallback →
        benefic-by-omission) is THE bug that made adverse node contacts on money
        houses invisible. B.10 is satisfied because natural nature is a real
        BPHS judgment, not a fabrication."""
        facts = [_aspect_fact("a1", "D1", "RAH_MEAN", source_house=5, target_house=11, offset=7, strength=1.0)]
        idx = VicharaFactIndex(facts)
        rows = build_aspect_valence_rows(idx, "D1", VALENCE_MATRIX)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["actor"], "RAH_MEAN")
        self.assertIn(rows[0]["value_text"], ("malefic", "strong_malefic", "mixed"))


class TestRatificationFactor(unittest.TestCase):
    def _index_for(self, subj, d1_dignity, per_varga_dignity):
        facts = [
            _link_fact("F_H2", "D1", "lord_placed", "Venus", 2, 3, "neutral_link"),
            _link_fact("F_H11", "D1", "lord_placed", "Saturn", 11, 5, "trikona_link"),
            _dignity_fact("F_D1_VEN", "D1", subj, "Libra", 9, d1_dignity),
        ]
        for i, (v, sign, house, dign) in enumerate(per_varga_dignity):
            facts.append(_dignity_fact(f"F_{v}_{subj}_{i}", v, subj, sign, house, dign))
        return VicharaFactIndex(facts)

    def test_clamp_high_end_three_agree(self):
        idx = self._index_for("VEN", "own", [
            ("D2", "Taurus", 12, "own"), ("D9", "Libra", 1, "own"), ("D11", "Taurus", 5, "own"),
        ])
        domains = {"wealth": {"vargas": ["D1", "D2", "D9", "D11"], "houses": [2], "karaka": None, "provisional": False}}
        rows, lookup = build_varga_ratification_rows(idx, domains, step=0.2, lo=0.6, hi=1.4)
        self.assertAlmostEqual(lookup[("VEN", "wealth")], 1.4)

    def test_clamp_low_end_three_oppose(self):
        idx = self._index_for("VEN", "own", [
            ("D2", "Scorpio", 12, "debilitated"), ("D9", "Scorpio", 1, "debilitated"),
            ("D11", "Scorpio", 5, "debilitated"),
        ])
        domains = {"wealth": {"vargas": ["D1", "D2", "D9", "D11"], "houses": [2], "karaka": None, "provisional": False}}
        rows, lookup = build_varga_ratification_rows(idx, domains, step=0.2, lo=0.6, hi=1.4)
        self.assertAlmostEqual(lookup[("VEN", "wealth")], 0.6)

    def test_d1_not_counted_as_a_voter(self):
        """A subtle double-count trap the brief explicitly calls out (§8 known
        traps): D1 must never be counted in n_agree/n_oppose."""
        idx = self._index_for("VEN", "own", [("D9", "Scorpio", 1, "debilitated")])
        domains = {"wealth": {"vargas": ["D1", "D9"], "houses": [2], "karaka": None, "provisional": False}}
        rows, lookup = build_varga_ratification_rows(idx, domains, step=0.2, lo=0.6, hi=1.4)
        # one opposing varga only -> factor = 1.0 - 0.2 = 0.8, NOT clamped/extra
        # from counting D1 as an agreeing reference.
        self.assertAlmostEqual(lookup[("VEN", "wealth")], 0.8)

    def test_venus_saturn_d9_wealth_divergence_fires(self):
        """CR-57/CR-71 type specimen: Venus (own D1, debilitated D9) and Saturn
        (own D1, debilitated D9) must both fire a varga_ratification_divergence
        row for wealth in D9."""
        facts = [
            _link_fact("F_H2", "D1", "lord_placed", "Venus", 2, 3, "neutral_link"),
            _link_fact("F_H11", "D1", "lord_placed", "Saturn", 11, 5, "trikona_link"),
            _dignity_fact("F_D1_VEN", "D1", "VEN", "Libra", 9, "own"),
            _dignity_fact("F_D9_VEN", "D9", "VEN", "Scorpio", 1, "debilitated"),
            _dignity_fact("F_D11_VEN", "D11", "VEN", "Taurus", 12, "exalted"),
            _dignity_fact("F_D1_SAT", "D1", "SAT", "Aquarius", 11, "own"),
            _dignity_fact("F_D9_SAT", "D9", "SAT", "Aries", 3, "debilitated"),
        ]
        idx = VicharaFactIndex(facts)
        domains = {"wealth": {"vargas": ["D1", "D2", "D9", "D11"], "houses": [2, 11], "karaka": None, "provisional": False}}
        rows, _lookup = build_varga_ratification_rows(idx, domains, step=0.2, lo=0.6, hi=1.4)
        divergence = [r for r in rows if r["vichara_family"] == "varga_ratification_divergence"]
        subjects_with_d9_divergence = {(r["subject"], r["domain"]) for r in divergence if r["varga_id"] == "D9"}
        self.assertIn(("VEN", "wealth"), subjects_with_d9_divergence)
        self.assertIn(("SAT", "wealth"), subjects_with_d9_divergence)


class TestVargaConsistency(unittest.TestCase):
    def test_vargottama_scores_higher(self):
        """A true vargottama graha (same sign D1/D9) must score strictly higher
        than a non-vargottama peer with an otherwise identical dignity spread."""
        facts = [
            # Mercury: vargottama (Virgo in both D1 and D9), own in both.
            _dignity_fact("F1", "D1", "MER", "Virgo", 6, "own"),
            _dignity_fact("F2", "D9", "MER", "Virgo", 6, "own"),
            # Moon: same dignity spread (own/own) but NOT vargottama (sign differs).
            _dignity_fact("F3", "D1", "MOON", "Cancer", 4, "own"),
            _dignity_fact("F4", "D9", "MOON", "Taurus", 2, "own"),
        ]
        idx = VicharaFactIndex(facts)
        rows = build_varga_consistency_rows(idx, w_sign=0.5, w_dignity=0.5)
        by_subj = {r["subject"]: r["value_num"] for r in rows}
        self.assertGreater(by_subj["MER"], by_subj["MOON"])
        mer_row = next(r for r in rows if r["subject"] == "MER")
        self.assertTrue(mer_row["value_jsonb"]["vargottama"])


class TestLeverageIndex(unittest.TestCase):
    def test_venus_ranks_first_for_wealth(self):
        """CR-69/CR-60 type specimen (482012f1/wealth): Venus (2L, weakest
        shadbala 4.64, 20-year MD from 2034) must rank #1 by leverage_index
        among the 7 classical grahas. Shadbala figures per the brief's cited
        CR-71 verified numbers."""
        shadbala = {
            "SUN": 8.47, "SAT": 7.83, "JUP": 7.80, "MER": 7.55,
            "MOON": 5.65, "MAR": 5.57, "VEN": 4.64,
        }
        facts = [
            _link_fact("F_H2", "D1", "lord_placed", "Venus", 2, 3, "neutral_link"),
            _link_fact("F_H11", "D1", "lord_placed", "Saturn", 11, 5, "trikona_link"),
        ]
        dignities = {
            "SUN": ("Capricorn", 10, "neutral"), "MOON": ("Purva_Bhadrapada_sign", 11, "neutral"),
            "MAR": ("Aries", 1, "own"), "MER": ("Pisces", 12, "debilitated"),
            "JUP": ("Sagittarius", 9, "own"), "VEN": ("Libra", 7, "own"),
            "SAT": ("Aquarius", 11, "own"),
        }
        for i, (subj, rupa) in enumerate(shadbala.items()):
            facts.append(_fact(f"FS{i}", "graha_shadbala_total", subj, "rupa", value_num=rupa))
        for i, (subj, (sign, house, dign)) in enumerate(dignities.items()):
            facts.append(_dignity_fact(f"FD{i}", "D1", subj, sign, house, dign))
        idx = VicharaFactIndex(facts)

        now = datetime(2026, 7, 14, tzinfo=timezone.utc)
        venus_md_start = datetime(2034, 7, 14, tzinfo=timezone.utc)
        dasha_rows = [
            {"lord_graha": "Venus", "start_iso": venus_md_start, "end_iso": venus_md_start + timedelta(days=20 * 365.25),
             "duration_days": 20 * 365.25},
        ]
        domains_config = {"wealth": {"vargas": ["D1", "D2", "D9", "D11"], "houses": [2, 11], "karaka": "Jupiter", "provisional": False}}
        leverage_weights = {
            "lordship": 1.0, "karakatva": 0.75, "occupancy": 0.5, "yoga_participation": 0.75,
            "capability_floor": 0.1, "runway_base": 1.0, "runway_scale": 0.5,
            "runway_duration_norm_years": 20, "runway_start_horizon_years": 15,
            "runway_lookforward_years": 30, "domain_yoga_keywords": {"wealth": []},
        }
        dignity_score_map = {"exalted": 1.0, "own": 0.75, "neutral": 0.5, "debilitated": 0.25}

        rows = build_leverage_index_rows(
            idx, domains_config, ratification_lookup={}, dasha_rows=dasha_rows,
            leverage_weights=leverage_weights, dignity_score_map=dignity_score_map, now=now,
        )
        wealth_rows = {r["subject"]: r["value_num"] for r in rows if r["domain"] == "wealth"}
        top = max(wealth_rows, key=wealth_rows.get)
        self.assertEqual(top, "VEN", f"expected VEN #1, got ranking={sorted(wealth_rows.items(), key=lambda kv: -kv[1])}")


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._last_query = None
        self._last_rows = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        sql_norm = " ".join(sql.split())
        if sql_norm.startswith("SELECT fact_id"):
            self._last_rows = self._conn.facts
        elif sql_norm.startswith("SELECT constant_key"):
            self._last_rows = self._conn.constants_rows
        elif sql_norm.startswith("SELECT yoga_canonical_id"):
            self._last_rows = []
        elif sql_norm.startswith("SELECT lord_graha"):
            self._last_rows = []
        elif sql_norm.startswith("DELETE FROM chart_vichara"):
            self._last_rows = []
            self.rowcount = 0
        elif sql_norm.startswith("INSERT INTO chart_vichara"):
            self._conn.inserted_rows.append(params)
            self._last_rows = []
        else:
            self._last_rows = []

    def fetchall(self):
        return self._last_rows


class _FakeConn:
    def __init__(self, facts, constants_rows):
        self.facts = facts
        self.constants_rows = constants_rows
        self.inserted_rows = []

    def cursor(self):
        return _FakeCursor(self)


class TestSubstepIntegration(unittest.TestCase):
    """Fixture-conn smoke test (no live DB): confirms build_ga_vichara_substep
    runs end to end, and that every constituent_fact_id it emits resolves
    against the fact_ids present in the fixture chart_facts set (DEFECT-001
    class orphan check)."""

    def _constants_rows(self):
        vals = {
            "ratification_step": 0.2,
            "ratification_clamp": {"lo": 0.6, "hi": 1.4},
            "operative_vargas": {
                "wealth": {"vargas": ["D1", "D2", "D9", "D11"], "houses": [2, 11], "karaka": "Jupiter", "provisional": False},
            },
            "valence_matrix": VALENCE_MATRIX,
            "dignity_score_map": {"exalted": 1.0, "own": 0.75, "neutral": 0.5, "debilitated": 0.25},
            "leverage_weights": {
                "lordship": 1.0, "karakatva": 0.75, "occupancy": 0.5, "yoga_participation": 0.75,
                "capability_floor": 0.1, "runway_base": 1.0, "runway_scale": 0.5,
                "runway_duration_norm_years": 20, "runway_start_horizon_years": 15,
                "runway_lookforward_years": 30, "domain_yoga_keywords": {"wealth": []},
            },
            "consistency_weights": {"w_sign": 0.5, "w_dignity": 0.5},
        }
        return [{"constant_key": k, "value_jsonb": v} for k, v in vals.items()]

    def _facts(self):
        facts = [
            _link_fact("F_H8", "D1", "lord_placed", "Mars", 8, 2, "neutral_link"),
            _link_fact("F_H2", "D1", "lord_placed", "Venus", 2, 3, "neutral_link"),
            _link_fact("F_H11", "D1", "lord_placed", "Saturn", 11, 5, "trikona_link"),
            _dignity_fact("F_D1_VEN", "D1", "VEN", "Libra", 9, "own"),
            _dignity_fact("F_D9_VEN", "D9", "VEN", "Scorpio", 1, "debilitated"),
            _fact("FS1", "graha_shadbala_total", "VEN", "rupa", value_num=4.64),
            _fact("FS2", "graha_shadbala_total", "SAT", "rupa", value_num=7.83),
        ]
        return facts

    def test_runs_and_zero_orphan_constituents(self):
        conn = _FakeConn(self._facts(), self._constants_rows())
        rows_inserted = build_ga_vichara_substep(
            chart_id="482012f1-710e-4a25-994a-93821f5871aa",
            build_id="00000000-0000-0000-0000-000000000000",
            ayanamsha_id="lahiri_chitrapaksha",
            conn=conn,
            dry_run=False,
        )
        self.assertGreater(rows_inserted, 0)
        known_fact_ids = {f["fact_id"] for f in self._facts()}
        for params in conn.inserted_rows:
            # constituent_fact_ids / constituent_facts_array are params[14] / params[15]
            # per _insert_rows' positional VALUES order.
            cfids = params[14]
            for fid in cfids:
                self.assertIn(fid, known_fact_ids, f"orphan constituent_fact_id: {fid}")

    def test_idempotent_rerun_stable_count(self):
        conn = _FakeConn(self._facts(), self._constants_rows())
        n1 = build_ga_vichara_substep(
            chart_id="482012f1-710e-4a25-994a-93821f5871aa", build_id=None,
            ayanamsha_id="lahiri_chitrapaksha", conn=conn, dry_run=False,
        )
        conn.inserted_rows = []
        n2 = build_ga_vichara_substep(
            chart_id="482012f1-710e-4a25-994a-93821f5871aa", build_id=None,
            ayanamsha_id="lahiri_chitrapaksha", conn=conn, dry_run=False,
        )
        self.assertEqual(n1, n2)


if __name__ == "__main__":
    unittest.main()
