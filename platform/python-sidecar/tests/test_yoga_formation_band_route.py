"""NMB-CAND-v1 yoga formation band -- serve-time route contract tests.

Spec: 00_ARCHITECTURE/briefs/nirmana/purna_acceptance/
NEAR_MISS_DOMAIN_PACKET_v1_0.md (OSR-009) as amended by
NEAR_MISS_DOMAIN_PACKET_v1_1.md (OSR-012, section 7) and narrowed by
NEAR_MISS_DOMAIN_PACKET_v1_2.md (OSR-015): `near_miss` is NOT a v1 state.

Fake-connection tests: chart fixtures are real-shaped `chart_facts` rows
evaluated through the REAL `ChartState` / `_check_house_lord_association` /
`_detect_dhana_yoga_house_lords`. Every scenario asserts its own shape (which
lord pairs associate) so a fixture can never silently mean something other
than what its name says. A DB-backed class runs only when
NEARMISS_TEST_DATABASE_URL points at a DISPOSABLE Postgres (never
DATABASE_URL: the test creates and drops its own schema).
"""
from __future__ import annotations

import itertools
import os
import random
import re
from pathlib import Path

import pytest

from ga_writers.ga_yoga_writer import (
    ChartState,
    _check_house_lord_association,
    _detect_dhana_yoga_house_lords,
    _lord_of_house,
)
from routers import yoga_formation_band as band

SIDECAR = Path(__file__).resolve().parents[1]
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"
B_POS = "00000000-0000-0000-0000-00000000b001"
B_YOGA = "00000000-0000-0000-0000-00000000b002"
BUILDS = [B_POS, B_YOGA]

# Aries lagna: h1 Mars, h2 Venus, h5 Sun, h9 Jupiter, h11 Saturn.
BASE = {
    "SUN": "leo", "MOON": "cancer", "MAR": "aries", "MER": "virgo",
    "JUP": "sagittarius", "VEN": "scorpio", "SAT": "scorpio",
}
SIGNS = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
         "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
SIGN_TO_NUM = {s: i + 1 for i, s in enumerate(SIGNS)}


def make_facts(lagna: str = "aries", place: dict | None = None, drop: set | None = None) -> list[dict]:
    place = dict(BASE if place is None else place)
    drop = drop or set()
    rows: list[dict] = []
    n = 0

    def add(subject: str, key: str, text=None, num=None):
        nonlocal n
        if (subject, key) in drop:
            return
        n += 1
        rows.append({
            "fact_id": f"fact-{n:03d}", "fact_category": "graha_position",
            "fact_subject": subject, "fact_key": key,
            "fact_value_text": text, "fact_value_num": num, "fact_value_jsonb": None,
        })

    add("LAGNA", "sign", text=lagna)
    for subj, sign in place.items():
        add(subj, "sign", text=sign)
        add(subj, "house_d1", num=((SIGN_TO_NUM[sign] - SIGN_TO_NUM[lagna]) % 12) + 1)
    return rows


CATALOG = {
    cid: {
        "canonical_id": cid, "name_en": f"name of {cid}",
        "formation_text": f"formation text of {cid}",
        "classical_citations": [{"text_id": "bphs", "chapter": 41}],
    }
    for cid in band.CANDIDATE_IDS
}


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeConn:
    """Routes the route module's three reads and records every (sql, params).
    Has no commit/close: the module must never need them."""

    def __init__(self, facts, firings=None, catalog=None):
        self.facts = facts
        self.firings = firings or {}
        self.catalog = CATALOG if catalog is None else catalog
        self.calls: list[tuple[str, list]] = []

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params or [])))
        if "FROM ga_yoga_firings" in sql:
            return FakeCursor([
                {"id": i, "yoga_canonical_id": cid, "fired": fr.get("fired", True),
                 "bhanga_active": fr.get("bhanga_active", False)}
                for i, (cid, fr) in enumerate(sorted(self.firings.items()), start=101)
            ])
        if "FROM brahma_yoga_catalog" in sql:
            return FakeCursor([dict(r) for r in self.catalog.values()])
        if "FROM chart_facts" in sql:
            return FakeCursor([dict(f) for f in self.facts])
        raise AssertionError(f"unexpected SQL: {sql}")


# ga_yoga writes one row per FIRED yoga, so "L1 ran for this build" is proven by ANY
# firing row of the served build. `l1_seen=True` adds one unrelated row; the
# zero-row tests pass `l1_seen=False`.
OTHER_ROW = {"kemadruma_yoga": {"fired": True}}


def run(facts, firings=None, l1_seen=True, **kw):
    merged = dict(firings or {})
    if l1_seen:
        merged.update(OTHER_ROW)
    conn = FakeConn(facts, merged, **kw)
    return band.build_yoga_band(conn, CHART, AYA, BUILDS)


def by_id(resp):
    return {c["candidate_id"]: c for c in resp["candidates"]}


def assoc_pairs(facts):
    st = ChartState(facts)
    return sorted(
        (h1, h2) for h1 in (2, 11) for h2 in (1, 2, 5, 9, 11)
        if h1 != h2 and _check_house_lord_association(st, h1, h2)
    )


def scenario_present():
    place = dict(BASE, VEN="gemini", SAT="gemini")  # 2L+11L conjoin in house 3
    facts = make_facts(place=place)
    assert (2, 11) in assoc_pairs(facts)
    firings = {
        "dhana_yoga_house_lords": {"fired": True, "bhanga_active": False},
        "dhana_yoga_2_11": {"fired": True},
        "dhana_yoga_2_5_9_11": {"fired": True},
    }
    return facts, firings


def scenario_dusthana_association():
    """(2,11) lords associate in house 8. The shipped detector does not fire; v1.2
    removed the dusthana gate as a formation condition, so this is plain `absent`."""
    facts = make_facts()  # BASE: only (2,11) associates, in house 8 (dusthana)
    assert assoc_pairs(facts) == [(2, 11), (11, 2)]
    assert _detect_dhana_yoga_house_lords(ChartState(facts), {}) is None
    firings = {"dhana_yoga_2_11": {"fired": True}, "dhana_yoga_2_5_9_11": {"fired": True}}
    return facts, firings


def scenario_absent():
    facts = make_facts(place=dict(BASE, VEN="taurus", SAT="virgo"))
    assert assoc_pairs(facts) == []
    return facts, {}


# ── States ───────────────────────────────────────────────────────────────────

def test_present_state_from_l1_firing_and_evaluator():
    facts, firings = scenario_present()
    rows = by_id(run(facts, firings))
    gated = rows["dhana_yoga_house_lords"]
    assert gated["state"] == band.STATE_PRESENT
    assert gated["l1_firing_ids"], "present must cite the L1 ga_yoga_firings id"
    assert rows["dhana_yoga_2_11"]["state"] == band.STATE_PRESENT


def test_dusthana_association_is_absent_never_near_miss():
    facts, firings = scenario_dusthana_association()
    rows = by_id(run(facts, firings))
    gated = rows["dhana_yoga_house_lords"]
    assert gated["state"] == band.STATE_ABSENT
    assert gated["reason"] == "no_formation"
    assert gated["l1_firing_ids"] == []
    assert all(l["leg"] == "lords_associate" for l in gated["legs"]), "no dusthana leg is exposed"
    assert rows["dhana_yoga_2_11"]["state"] == band.STATE_PRESENT
    # the present overlapping siblings are recorded on the non-present family row
    assert "dhana_yoga_2_11" in gated["contradicting_present_siblings"]
    assert "dhana_yoga_2_5_9_11" in gated["contradicting_present_siblings"]


def test_no_row_ever_has_state_near_miss_and_near_miss_is_not_a_state():
    assert not hasattr(band, "STATE_NEAR_MISS")
    assert "near_miss" not in band.BAND_STATES
    for scen in (scenario_present, scenario_dusthana_association, scenario_absent):
        facts, firings = scen()
        resp = run(facts, firings)
        assert resp["near_miss_capable_candidates"] == 0
        assert resp["band_coverage"]["near_miss"] == 0
        assert sum(resp["band_coverage"][k] for k in ("present", "absent", "indeterminate")) == 6
        for c in resp["candidates"]:
            assert c["state"] != "near_miss"
            assert "near_miss_capable" not in c
            assert all("gate_failed" not in p for p in c["pairs"])


def test_association_missing_is_absent():
    facts, firings = scenario_absent()
    gated = by_id(run(facts, firings))["dhana_yoga_house_lords"]
    assert gated["state"] == band.STATE_ABSENT and gated["reason"] == "no_pair_associated"


def test_route_source_has_no_dead_near_miss_branch():
    src = (SIDECAR / "routers" / "yoga_formation_band.py").read_text()
    body = src.split('"""', 2)[2]  # drop the module docstring
    for dead in ("STATE_NEAR_MISS", "gate_failed", "DUSTHANAS", "near_miss_capable=", "gate_only_failure"):
        assert dead not in body, dead


def test_absent_state_no_association():
    facts, firings = scenario_absent()
    for cid, c in by_id(run(facts, firings)).items():
        assert c["state"] == band.STATE_ABSENT, cid
        assert c["reason"] == "no_pair_associated"


def test_indeterminate_when_a_required_input_is_missing():
    facts = make_facts(drop={("VEN", "sign"), ("VEN", "house_d1")})
    rows = by_id(run(facts, {}))
    gated = rows["dhana_yoga_house_lords"]
    assert gated["state"] == band.STATE_INDETERMINATE
    assert gated["reason"].startswith("missing_input:")
    assert "sign_of:venus" in gated["reason"]
    assert rows["dhana_yoga_5_9"]["state"] == band.STATE_ABSENT  # unaffected pair stays decidable


def test_indeterminate_when_lagna_missing_and_when_no_facts_at_all():
    for facts in (make_facts(drop={("LAGNA", "sign")}), []):
        resp = run(facts, {})
        assert len(resp["candidates"]) == 6
        assert {c["state"] for c in resp["candidates"]} == {band.STATE_INDETERMINATE}


def test_indeterminate_on_l1_evaluator_disagreement_l1_only(caplog):
    facts, _ = scenario_absent()
    with caplog.at_level("WARNING"):
        gated = by_id(run(facts, {"dhana_yoga_house_lords": {"fired": True}}))["dhana_yoga_house_lords"]
    assert gated["state"] == band.STATE_INDETERMINATE
    assert gated["reason"] == "l1_evaluator_disagreement"
    assert gated["disagreement"] == {"l1_fired": True, "evaluator_fired": False}
    assert "l1_evaluator_disagreement" in caplog.text  # logged, not fatal


def test_zero_l1_firing_rows_makes_candidates_indeterminate_not_absent():
    facts, _ = scenario_absent()
    resp = run(facts, {}, l1_seen=False)
    assert resp["ledger"]["l1_firing_rows_seen"] == 0
    for c in resp["candidates"]:
        assert c["state"] == band.STATE_INDETERMINATE, c["candidate_id"]
        assert c["reason"] == "no_l1_firing_rows_seen"
    assert resp["band_coverage"] == {"present": 0, "near_miss": 0, "absent": 0, "indeterminate": 6}


def test_zero_l1_rows_reason_wins_over_disagreement_but_not_over_missing_input():
    facts, _ = scenario_present()  # evaluator fires; no L1 rows at all
    for c in run(facts, {}, l1_seen=False)["candidates"]:
        if c["state"] == band.STATE_INDETERMINATE:
            assert c["reason"] == "no_l1_firing_rows_seen"
    gone = make_facts(drop={("VEN", "sign"), ("VEN", "house_d1")})
    gated = by_id(run(gone, {}, l1_seen=False))["dhana_yoga_house_lords"]
    assert gated["reason"].startswith("missing_input:")


def test_any_l1_row_of_the_served_build_proves_ga_yoga_ran():
    facts, _ = scenario_absent()
    resp = run(facts, {}, l1_seen=True)  # only an unrelated yoga row exists
    assert resp["ledger"]["l1_firing_rows_seen"] == 1
    assert {c["state"] for c in resp["candidates"]} == {band.STATE_ABSENT}


def test_indeterminate_on_l1_evaluator_disagreement_evaluator_only():
    facts, _ = scenario_present()
    gated = by_id(run(facts, {}))["dhana_yoga_house_lords"]  # evaluator fires; L1 has no row
    assert gated["state"] == band.STATE_INDETERMINATE
    assert gated["disagreement"] == {"l1_fired": False, "evaluator_fired": True}


def test_all_three_states_are_representable():
    states = set()
    for scen in (scenario_present, scenario_dusthana_association, scenario_absent):
        facts, firings = scen()
        states |= {c["state"] for c in run(facts, firings)["candidates"]}
    states |= {c["state"] for c in run([], {})["candidates"]}
    assert states == set(band.BAND_STATES) == {"present", "absent", "indeterminate"}


# ── Negative controls ────────────────────────────────────────────────────────

@pytest.mark.parametrize("scenario", [scenario_present, scenario_dusthana_association, scenario_absent])
def test_single_leg_candidates_have_only_the_association_leg(scenario):
    facts, firings = scenario()
    rows = by_id(run(facts, firings))
    for cid in band.CANDIDATE_IDS:
        assert rows[cid]["state"] != "near_miss", cid
        assert all(l["leg"] == "lords_associate" for l in rows[cid]["legs"])


def test_same_lord_pair_is_never_associated():
    # Leo lagna: h2 Virgo and h11 Gemini are both ruled by Mercury -> same-lord (2,11) pair.
    facts = make_facts(lagna="leo", place=dict(BASE, MER="scorpio"))
    assert _lord_of_house(ChartState(facts), 2) == _lord_of_house(ChartState(facts), 11) == "mercury"
    gated = by_id(run(facts, {}))["dhana_yoga_house_lords"]
    pair = next(p for p in gated["pairs"] if p["houses_ruled"] == [2, 11])
    assert pair["associated"] is False and pair["evaluable"] is True


def test_bhanga_active_firing_stays_present_and_is_carried():
    facts, firings = scenario_present()
    firings["dhana_yoga_house_lords"] = {"fired": True, "bhanga_active": True}
    gated = by_id(run(facts, firings))["dhana_yoga_house_lords"]
    assert gated["state"] == band.STATE_PRESENT
    assert gated["l1_bhanga_active"] is True


def test_exactly_six_ids_in_candidate_order_and_versions():
    facts, firings = scenario_dusthana_association()
    resp = run(facts, firings)
    assert [c["candidate_id"] for c in resp["candidates"]] == [
        "dhana_yoga_house_lords", "dhana_yoga_2_11", "dhana_yoga_5_9",
        "dhana_yoga_lagna_2", "dhana_yoga_9_11", "dhana_yoga_2_5_9_11",
    ]
    assert resp["candidate_set_version"] == "NMB-CAND-v1"
    assert resp["eligibility_rule_version"] == "NMB-ELIG-v1"
    assert resp["band_version"] == "NMB-BAND-v1"
    assert resp["tolerance"] == "none"


def test_excluded_yogas_are_not_candidates():
    for excluded in ("lakshmi_yoga", "chandra_mangala", "guru_mangala", "raja_yoga_kendra_trikona"):
        assert excluded not in band.CANDIDATE_IDS
    assert not any(c.startswith("pancha_mahapurusha") for c in band.CANDIDATE_IDS)


def test_response_ledger_shape():
    facts, firings = scenario_dusthana_association()
    resp = run(facts, firings)
    all_ids = {f["fact_id"] for f in facts}
    assert resp["scope"]["frame"] == "D1_rashi" and resp["scope"]["ayanamsha_id"] == AYA
    assert resp["scope"]["chandra_frame"] is False and resp["scope"]["surya_frame"] is False
    assert resp["served_build_ids"] == sorted(BUILDS)
    ledger = resp["ledger"]
    assert set(ledger["consumed_fact_ids"]) <= all_ids and ledger["consumed_fact_ids"]
    assert ledger["fact_source"]["producing_assets"] == ["ga_positions"]
    assert ledger["firing_source"]["producing_assets"] == ["ga_yoga"]
    for c in resp["candidates"]:
        assert c["constituent_fact_ids"] and set(c["constituent_fact_ids"]) <= all_ids
        assert c["scope"]["ayanamsha_id"] == AYA
        assert c["classical_citations"] == ["bphs:41"]
        assert c["formation_text"] == f"formation text of {c['candidate_id']}"


def test_missing_catalog_degrades_honestly():
    facts, firings = scenario_dusthana_association()
    c = by_id(run(facts, firings, catalog={}))["dhana_yoga_house_lords"]
    assert c["yoga_name"] is None and c["formation_text"] is None and c["classical_citations"] == []
    assert c["state"] == band.STATE_ABSENT


def test_ambiguous_fact_values_are_dropped_and_reported_not_guessed():
    facts = make_facts()
    facts.append({**next(f for f in facts if f["fact_subject"] == "VEN" and f["fact_key"] == "sign"),
                  "fact_id": "fact-dup", "fact_value_text": "gemini"})
    resp = run(facts, {})
    assert resp["ledger"]["ambiguous_facts"] == [
        {"fact_subject": "venus", "fact_key": "sign", "fact_ids": ["fact-005", "fact-dup"]}
    ] or [a["fact_subject"] for a in resp["ledger"]["ambiguous_facts"]] == ["venus"]
    gated = by_id(resp)["dhana_yoga_house_lords"]
    assert gated["state"] == band.STATE_INDETERMINATE and "sign_of:venus" in gated["reason"]


def test_identical_duplicate_rows_collapse_without_ambiguity():
    facts = make_facts()
    facts.append({**facts[1], "fact_id": "fact-dup-same"})
    resp = run(facts, {})
    assert resp["ledger"]["ambiguous_facts"] == []


# ── Parity with the L1 detector ──────────────────────────────────────────────

def _l1_firings_from_real_evaluators(facts):
    """What ga_yoga would have written: the REAL L1 evaluators' verdicts."""
    st = ChartState(facts)
    firings = {}
    if _detect_dhana_yoga_house_lords(st, {}) is not None:
        firings["dhana_yoga_house_lords"] = {"fired": True}
    for cid in band.SIBLING_IDS:
        if any(_check_house_lord_association(st, h1, h2) for h1, h2 in band.candidate_pairs(cid)):
            firings[cid] = {"fired": True}
    return firings


def test_present_equals_detector_on_every_fixture_and_never_disagrees():
    rng = random.Random(20260929)
    grahas = ["SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"]
    seen_states: set[str] = set()
    for lagna in SIGNS:
        for _ in range(40):
            place = {g: rng.choice(SIGNS) for g in grahas}
            facts = make_facts(lagna=lagna, place=place)
            firings = _l1_firings_from_real_evaluators(facts)
            gated = by_id(run(facts, firings))["dhana_yoga_house_lords"]
            detector_fires = _detect_dhana_yoga_house_lords(ChartState(facts), {}) is not None
            assert (gated["state"] == band.STATE_PRESENT) == detector_fires, (lagna, place)
            assert gated["state"] != band.STATE_INDETERMINATE, (lagna, place)
            for c in run(facts, firings)["candidates"]:
                seen_states.add(c["state"])
    assert seen_states == {band.STATE_PRESENT, band.STATE_ABSENT}


def test_sibling_present_equals_l1_relation_evaluator_on_every_fixture():
    rng = random.Random(7)
    grahas = ["SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"]
    for lagna in SIGNS:
        for _ in range(20):
            facts = make_facts(lagna=lagna, place={g: rng.choice(SIGNS) for g in grahas})
            st = ChartState(facts)
            rows = by_id(run(facts, _l1_firings_from_real_evaluators(facts)))
            for cid in band.SIBLING_IDS:
                l1 = any(_check_house_lord_association(st, h1, h2) for h1, h2 in band.candidate_pairs(cid))
                assert (rows[cid]["state"] == band.STATE_PRESENT) == l1


def test_candidate_pairs_come_from_the_shipped_tables():
    assert band.candidate_pairs("dhana_yoga_2_11") == [(2, 11)]
    assert band.candidate_pairs("dhana_yoga_5_9") == [(5, 9)]
    assert band.candidate_pairs("dhana_yoga_lagna_2") == [(1, 2)]
    assert band.candidate_pairs("dhana_yoga_9_11") == [(9, 11)]
    assert band.candidate_pairs("dhana_yoga_2_5_9_11") == list(itertools.combinations((2, 5, 9, 11), 2))
    assert (2, 11) in band.candidate_pairs("dhana_yoga_house_lords")
    assert all(h1 in (2, 11) and h1 != h2 for h1, h2 in band.candidate_pairs("dhana_yoga_house_lords"))


# ── Data access: fenced, pinned, ordered, read-only ──────────────────────────

def test_every_read_is_build_fenced_and_facts_are_pinned_with_total_order():
    facts, firings = scenario_dusthana_association()
    conn = FakeConn(facts, firings)
    band.build_yoga_band(conn, CHART, AYA, BUILDS)
    fenced = [(s, p) for s, p in conn.calls if "FROM chart_facts" in s or "FROM ga_yoga_firings" in s]
    assert len(fenced) == 2
    for sql, params in fenced:
        assert "build_id = ANY(%s::uuid[])" in sql
        assert sorted(BUILDS) in [sorted(p) for p in params if isinstance(p, list)]
    fact_sql = band._FACTS_SQL
    assert "fact_category = 'graha_position'" in fact_sql and "fact_key IN ('house_d1', 'sign')" in fact_sql
    assert re.search(r"ORDER BY .*fact_id::text\s*$", fact_sql.strip(), re.S)
    assert re.search(r"ORDER BY .*\bid\s*$", band._FIRINGS_SQL.strip(), re.S)


def test_module_never_commits_or_writes_state():
    import ast
    src = (SIDECAR / "routers" / "yoga_formation_band.py").read_text()
    doc = ast.get_docstring(ast.parse(src), clean=False) or ""
    body = "\n".join(l for l in src.replace(doc, "", 1).splitlines() if not l.lstrip().startswith("#"))
    for forbidden in (".commit(", "asset_throughput", "INSERT INTO", "DELETE FROM", "UPDATE ", "TRUNCATE"):
        assert forbidden not in body, forbidden


def test_route_imports_the_l1_evaluators_and_does_not_fork_them():
    src = (SIDECAR / "routers" / "yoga_formation_band.py").read_text()
    assert "from ga_writers.ga_yoga_writer import (" in src
    for name in ("ChartState", "_lord_of_house", "_house_of_planet",
                 "_check_house_lord_association", "_detect_dhana_yoga_house_lords"):
        assert re.search(rf"^\s+{name},$", src, re.M), f"{name} must be imported from ga_yoga_writer"
        assert f"def {name}" not in src and f"class {name}" not in src
    assert band.ChartState is ChartState
    assert band._check_house_lord_association is _check_house_lord_association
    assert band._detect_dhana_yoga_house_lords is _detect_dhana_yoga_house_lords


def test_no_registered_writer_closure_includes_the_route():
    """OSR-012: the route is not in any writer's source closure, so no writer
    digest (nirmana-writer-digests.json) or layer pin can move because of it."""
    from pipeline.orchestrator import asset_runner
    from pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all

    discover_all()
    assert WRITER_REGISTRY
    for asset_id in sorted(WRITER_REGISTRY):
        paths = [p for p, _ in asset_runner._writer_source_files(asset_runner._writer_source_paths(asset_id))]
        assert not any("yoga_formation_band" in p for p in paths), asset_id
    for py in list(SIDECAR.glob("ga_writers/*.py")) + list(SIDECAR.glob("pipeline/**/*.py")) \
            + list(SIDECAR.glob("bodha_writers/*.py")) + list(SIDECAR.glob("services/**/*.py")):
        if "/tests/" in str(py):
            continue
        assert "yoga_formation_band" not in py.read_text(encoding="utf-8"), py


# ── v1.2 amendments: overlaps, source honesty, timeout ──────────────────────

def test_rows_are_overlapping_statuses_not_a_yoga_count():
    facts, firings = scenario_present()
    resp = run(facts, firings)
    assert resp["overlap_note"].startswith("Candidate rows are overlapping statuses")
    assert "yoga count" in resp["overlap_note"]
    ov = resp["overlaps"]
    assert set(ov) == set(band.CANDIDATE_IDS)
    # subsumption per packet v1.2 section 2
    assert {"dhana_yoga_2_11", "dhana_yoga_5_9", "dhana_yoga_9_11"} <= set(ov["dhana_yoga_2_5_9_11"])
    assert set(ov["dhana_yoga_house_lords"]) == set(band.SIBLING_IDS)  # overlaps all of them
    assert "dhana_yoga_2_5_9_11" in ov["dhana_yoga_2_11"]
    assert "dhana_yoga_lagna_2" not in ov["dhana_yoga_2_5_9_11"]  # (1,2) is not among 2/5/9/11
    for c in resp["candidates"]:
        assert c["overlaps"] == ov[c["candidate_id"]]
        assert c["candidate_id"] not in c["overlaps"]
        assert set(c["contradicting_present_siblings"]) <= set(c["overlaps"])
        if c["state"] == band.STATE_PRESENT:
            assert c["contradicting_present_siblings"] == []


def test_source_citation_honesty_only_5th_9th_is_directly_in_ch41():
    facts, firings = scenario_present()
    resp = run(facts, firings)
    src = resp["classical_sources"]
    assert src["catalog_citation_carries_verse"] is False
    assert src["directly_in_bphs_ch41_sloka_16"] == ["dhana_yoga_5_9"]
    assert "general Parashari sambandha" in src["note"]
    assert "Ch.41 sloka 16" in src["note"]
    for c in resp["candidates"]:
        basis = c["source_basis"]
        assert basis["directly_in_bphs_ch41"] is (c["candidate_id"] == "dhana_yoga_5_9")
        assert basis["verse"] == ("BPHS Ch.41 sloka 16 (5th and 9th lords)" if c["candidate_id"] == "dhana_yoga_5_9" else None)
        if c["candidate_id"] != "dhana_yoga_5_9":
            assert "general Parashari sambandha" in basis["basis"]
        assert c["citation_carries_verse"] is False


def test_route_connection_sets_statement_timeout_and_read_only(monkeypatch):
    seen = {}

    class C:
        read_only = False

    def fake_connect(url, **kw):
        seen["url"], seen["kw"] = url, kw
        return C()

    monkeypatch.setenv("DATABASE_URL", "postgresql://x/y")
    monkeypatch.setattr(band.psycopg, "connect", fake_connect)
    conn = band._connect()
    assert conn.read_only is True
    assert "statement_timeout=" in seen["kw"].get("options", "")
    ms = int(seen["kw"]["options"].split("statement_timeout=")[1].split()[0])
    assert 0 < ms <= 15000
    assert seen["kw"].get("connect_timeout")


# ── D: domain pins (BPHS lordship + Parashari aspects as the L1 detector codes them) ──

def test_lordship_uses_only_the_seven_parashari_planets():
    from ga_writers.ga_yoga_writer import NB_SIGN_LORDS
    assert set(NB_SIGN_LORDS) == set(SIGNS)
    assert set(NB_SIGN_LORDS.values()) == {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}
    assert not {"rahu", "ketu"} & set(NB_SIGN_LORDS.values())
    for sign, lord in {"aries": "mars", "scorpio": "mars", "aquarius": "saturn", "capricorn": "saturn",
                       "pisces": "jupiter", "sagittarius": "jupiter", "cancer": "moon", "leo": "sun"}.items():
        assert NB_SIGN_LORDS[sign] == lord  # no co-lordship for Scorpio/Aquarius
    for lagna in SIGNS:
        st = ChartState(make_facts(lagna=lagna))
        for h in range(1, 13):
            assert _lord_of_house(st, h) in NB_SIGN_LORDS.values()


def test_special_aspects_are_the_classical_parashari_set():
    from ga_writers.ga_yoga_writer import _nb_aspects_house
    expect = {"mars": {4, 7, 8}, "jupiter": {5, 7, 9}, "saturn": {3, 7, 10},
              "sun": {7}, "moon": {7}, "mercury": {7}, "venus": {7}}
    for planet, offsets in expect.items():
        got = {t for t in range(1, 13) if _nb_aspects_house(planet, 1, t)}
        assert got == {((o - 1) % 12) + 1 for o in offsets}, planet
    assert _nb_aspects_house("mars", 5, 8) and _nb_aspects_house("mars", 5, 12)  # 4th and 8th from house 5
    assert _nb_aspects_house("jupiter", 11, 3) and _nb_aspects_house("jupiter", 11, 7)  # 5th and 9th from house 11
    assert _nb_aspects_house("saturn", 10, 12) and _nb_aspects_house("saturn", 10, 7)  # 3rd and 10th from house 10


def test_mutual_aspect_honours_special_aspects_and_requires_both_directions():
    from ga_writers.ga_yoga_writer import _planets_associated
    # Mars 4th aspect <-> Saturn 10th aspect: Mars h1, Saturn h4 -> mutual (both special).
    st = ChartState(make_facts(place=dict(BASE, MAR="aries", SAT="cancer")))
    assert _planets_associated(st, "mars", "saturn") == "mutual_aspect"
    # Universal 7th <-> 7th is mutual.
    st = ChartState(make_facts(place=dict(BASE, MER="aries", VEN="libra")))
    assert _planets_associated(st, "mercury", "venus") == "mutual_aspect"
    # Jupiter's 5th aspect is one-sided (Venus casts only the 7th): NOT an association.
    st = ChartState(make_facts(place=dict(BASE, JUP="aries", VEN="leo")))
    assert _planets_associated(st, "jupiter", "venus") is None
    # Mars's 4th aspect one-sided onto Mercury: NOT an association.
    st = ChartState(make_facts(place=dict(BASE, MAR="aries", MER="cancer")))
    assert _planets_associated(st, "mars", "mercury") is None


def test_exchange_and_conjunction_modes_are_sign_based():
    from ga_writers.ga_yoga_writer import _planets_associated
    st = ChartState(make_facts(place=dict(BASE, MAR="taurus", VEN="aries")))
    assert _planets_associated(st, "mars", "venus") == "exchange"
    st = ChartState(make_facts(place=dict(BASE, MAR="gemini", VEN="gemini")))
    assert _planets_associated(st, "mars", "venus") == "conjunction"  # same whole-sign house, no orb


# ── HTTP surface ─────────────────────────────────────────────────────────────

class _CtxConn(FakeConn):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture()
def client(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.include_router(band.router, prefix="/api/compute")
    monkeypatch.setenv("PYTHON_SIDECAR_API_KEY", "test-key")
    facts, firings = scenario_dusthana_association()
    monkeypatch.setattr(band, "_connect", lambda: _CtxConn(facts, firings))
    return TestClient(app)


GOOD = {"chart_id": CHART, "ayanamsha_id": AYA, "served_build_ids": BUILDS}
URL = "/api/compute/yoga_formation_band"


def test_http_success_returns_six_rows(client):
    r = client.post(URL, json=GOOD, headers={"x-api-key": "test-key"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["candidates"]) == 6
    assert {c["candidate_id"]: c["state"] for c in body["candidates"]}["dhana_yoga_house_lords"] == "absent"
    assert body["near_miss_capable_candidates"] == 0 and body["band_coverage"]["near_miss"] == 0


def test_http_auth_is_fail_closed(client, monkeypatch):
    assert client.post(URL, json=GOOD).status_code == 401
    assert client.post(URL, json=GOOD, headers={"x-api-key": "wrong"}).status_code == 401
    monkeypatch.delenv("PYTHON_SIDECAR_API_KEY")
    assert client.post(URL, json=GOOD, headers={"x-api-key": ""}).status_code == 503


@pytest.mark.parametrize("patch", [
    {"chart_id": "not-a-uuid"},
    {"served_build_ids": []},
    {"served_build_ids": ["x'; DROP TABLE chart_facts;--"]},
    {"served_build_ids": [B_POS] * 65},
    {"ayanamsha_id": "lahiri'; --"},
    {"ayanamsha_id": ""},
])
def test_http_rejects_invalid_input(client, patch):
    r = client.post(URL, json={**GOOD, **patch}, headers={"x-api-key": "test-key"})
    assert r.status_code == 422


def test_http_db_failure_is_a_generic_503(client, monkeypatch):
    def boom():
        raise RuntimeError("password=hunter2 host=secret")
    monkeypatch.setattr(band, "_connect", boom)
    r = client.post(URL, json=GOOD, headers={"x-api-key": "test-key"})
    assert r.status_code == 503
    assert "hunter2" not in r.text and "secret" not in r.text


def test_main_registers_the_router_under_the_shared_api_key_dependency():
    src = (SIDECAR / "main.py").read_text()
    assert re.search(
        r"app\.include_router\(yoga_formation_band_router\.router, prefix=\"/api/compute\", "
        r"dependencies=\[Depends\(verify_api_key\)\]\)", src)


def test_main_app_mounts_the_route():
    pytest.importorskip("asyncpg")  # main.py imports the bo_2-8 bundle, which needs asyncpg
    import main
    paths = {getattr(r, "path", None) for r in main.app.routes}
    assert URL in paths


# ── DB-backed (disposable Postgres only) ─────────────────────────────────────

_DB_URL = os.environ.get("NEARMISS_TEST_DATABASE_URL")


@pytest.mark.skipif(not _DB_URL, reason="NEARMISS_TEST_DATABASE_URL (disposable Postgres) not set")
class TestAgainstPostgres:
    SCHEMA = "nmb_route_test"

    @pytest.fixture()
    def conn(self):
        import psycopg
        import psycopg.rows
        c = psycopg.connect(_DB_URL, row_factory=psycopg.rows.dict_row, autocommit=True)
        c.execute(f"DROP SCHEMA IF EXISTS {self.SCHEMA} CASCADE")
        c.execute(f"CREATE SCHEMA {self.SCHEMA}")
        c.execute(f"SET search_path TO {self.SCHEMA}")
        c.execute("""CREATE TABLE chart_facts (
            fact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL,
            build_id uuid, ayanamsha_id text NOT NULL, fact_category text NOT NULL,
            fact_subject text NOT NULL, fact_key text NOT NULL, fact_value_text text,
            fact_value_num numeric, fact_value_jsonb jsonb)""")
        c.execute("""CREATE TABLE ga_yoga_firings (
            id serial PRIMARY KEY, chart_id uuid NOT NULL, build_id uuid, ayanamsha_id text NOT NULL,
            yoga_canonical_id text NOT NULL, fired boolean NOT NULL DEFAULT true,
            bhanga_active boolean DEFAULT false, UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id))""")
        c.execute("""CREATE TABLE brahma_yoga_catalog (
            canonical_id text PRIMARY KEY, name_en text, formation_text text, classical_citations jsonb)""")
        for cat in CATALOG.values():
            c.execute("INSERT INTO brahma_yoga_catalog VALUES (%s,%s,%s,%s::jsonb)",
                      (cat["canonical_id"], cat["name_en"], cat["formation_text"],
                       '[{"text_id": "bphs", "chapter": 41}]'))
        yield c
        c.execute("SET search_path TO public")
        c.execute(f"DROP SCHEMA IF EXISTS {self.SCHEMA} CASCADE")
        c.close()

    def _load(self, conn, facts, build_id, aya=AYA):
        for f in facts:
            conn.execute(
                "INSERT INTO chart_facts (chart_id, build_id, ayanamsha_id, fact_category, fact_subject,"
                " fact_key, fact_value_text, fact_value_num) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (CHART, build_id, aya, f["fact_category"], f["fact_subject"], f["fact_key"],
                 f["fact_value_text"], f["fact_value_num"]))

    def test_dusthana_association_is_absent_over_real_sql_and_build_fence(self, conn):
        facts, firings = scenario_dusthana_association()
        self._load(conn, facts, B_POS)
        # A stale, UNSERVED generation with a conflicting Venus sign must be invisible.
        stale = "00000000-0000-0000-0000-00000000dead"
        self._load(conn, [f for f in make_facts(place=dict(BASE, VEN="gemini", SAT="gemini"))
                          if f["fact_subject"] in ("VEN", "SAT")], stale)
        for cid in firings:
            conn.execute("INSERT INTO ga_yoga_firings (chart_id, build_id, ayanamsha_id, yoga_canonical_id)"
                         " VALUES (%s,%s,%s,%s)", (CHART, B_YOGA, AYA, cid))
        conn.execute("INSERT INTO ga_yoga_firings (chart_id, build_id, ayanamsha_id, yoga_canonical_id)"
                     " VALUES (%s,%s,%s,%s)", (CHART, stale, "other_aya", "dhana_yoga_house_lords"))
        resp = band.build_yoga_band(conn, CHART, AYA, BUILDS)
        rows = by_id(resp)
        assert len(resp["candidates"]) == 6
        assert rows["dhana_yoga_house_lords"]["state"] == band.STATE_ABSENT
        assert resp["near_miss_capable_candidates"] == 0
        assert rows["dhana_yoga_2_11"]["state"] == band.STATE_PRESENT
        assert resp["ledger"]["ambiguous_facts"] == []
        db_fact_ids = {r["fact_id"] for r in conn.execute(
            "SELECT fact_id::text AS fact_id FROM chart_facts WHERE build_id = %s", (B_POS,)).fetchall()}
        assert db_fact_ids and set(resp["ledger"]["consumed_fact_ids"]) <= db_fact_ids

    def test_unserved_builds_yield_indeterminate_not_absent(self, conn):
        facts, _ = scenario_absent()
        self._load(conn, facts, "00000000-0000-0000-0000-00000000dead")
        resp = band.build_yoga_band(conn, CHART, AYA, BUILDS)
        assert {c["state"] for c in resp["candidates"]} == {band.STATE_INDETERMINATE}

    def test_connection_is_left_uncommitted_and_unmodified(self, conn):
        facts, firings = scenario_dusthana_association()
        self._load(conn, facts, B_POS)
        before = conn.execute("SELECT count(*) AS n FROM chart_facts").fetchone()["n"]
        band.build_yoga_band(conn, CHART, AYA, BUILDS)
        assert conn.execute("SELECT count(*) AS n FROM chart_facts").fetchone()["n"] == before

    def test_zero_l1_rows_indeterminate_and_any_row_proves_l1_ran(self, conn):
        facts, _ = scenario_absent()
        self._load(conn, facts, B_POS)
        resp = band.build_yoga_band(conn, CHART, AYA, BUILDS)
        assert {c["reason"] for c in resp["candidates"]} == {"no_l1_firing_rows_seen"}
        conn.execute("INSERT INTO ga_yoga_firings (chart_id, build_id, ayanamsha_id, yoga_canonical_id)"
                     " VALUES (%s,%s,%s,%s)", (CHART, B_YOGA, AYA, "kemadruma_yoga"))
        resp = band.build_yoga_band(conn, CHART, AYA, BUILDS)
        assert {c["state"] for c in resp["candidates"]} == {band.STATE_ABSENT}
        assert resp["ledger"]["l1_firing_rows_seen"] == 1

    def test_statement_timeout_option_is_accepted_by_postgres(self, conn):
        import psycopg
        c2 = psycopg.connect(_DB_URL, options="-c statement_timeout=5000")
        try:
            assert c2.execute("SHOW statement_timeout").fetchone()[0] == "5s"
        finally:
            c2.close()
