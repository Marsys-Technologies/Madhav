"""day-fx8 (SS N-272 / N-273): a literal fallback standing in for a missing fact is replaced by the real
value (a cited L1 fact) or an honest NULL / omission. Per fix: the fact MISSING -> no invented literal;
the fact PRESENT -> the real value is kept.

Assets: bo_bimba, bo_karanajala, bo_arudha, bo_vargottama_dhana, bo_anveshana.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

from bodha_writers.arudha_emitter import GRAHAS as AR_GRAHAS, build_signal_rows
from bodha_writers.vargottama_dhana_emitter import build_dhana_axis_rows
from pipeline.orchestrator.writers import bo_anveshana as ANV
from pipeline.orchestrator.writers import bo_bimba as BIM
from pipeline.orchestrator.writers import bo_karanajala as KAR

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
NOW = "2026-10-09T00:00:00+00:00"


# ── bo_arudha: "untenanted" only when every graha's house fact was read ───────────────────────────

def _arudha_facts():
    return {
        "ARUDHA_A1": {"house_d1": {"num": 9, "fact_id": "fal"}, "sign": {"text": "Sagittarius"}},
        "ARUDHA_A2": {"house_d1": {"num": 3, "fact_id": "fa2"}, "sign": {"text": "Cancer"}},
    }


def _all_graha_houses(**override):
    gh = {gc: {"house_d1": 10, "fact_id": f"f{gc}"} for gc in AR_GRAHAS}
    gh.update(override)
    return gh


def _a2_headline(graha_houses):
    rows = build_signal_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                             arudha_facts=_arudha_facts(), graha_houses=graha_houses, now=NOW)
    return next(r for r in rows if r["signal_type_id"] == "arudha:ARUDHA_A2_tenancy")["signal_headline_text"]


def test_arudha_untenanted_is_stated_when_all_graha_houses_are_read():
    assert _a2_headline(_all_graha_houses()).endswith("A2 (dhana arudha) in H3 (Cancer) — untenanted")


def test_arudha_missing_graha_house_fact_makes_occupancy_unknown_everywhere():
    gh = _all_graha_houses()
    del gh[AR_GRAHAS[0]]
    rows = build_signal_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                             arudha_facts=_arudha_facts(), graha_houses=gh, now=NOW)
    r = next(x for x in rows if x["signal_type_id"] == "arudha:ARUDHA_A2_tenancy")
    assert r["signal_headline_text"] == "A2 (dhana arudha) in H3 (Cancer)"
    assert r["signal_summary_text"] == ("category=arudha | pada=A2 (dhana arudha) | house=3 | sign=Cancer")
    cfg = json.loads(r["configuration_jsonb"])
    assert cfg["occupants"] is None and cfg["valence_net"] is None and cfg["valence_source"] is None
    assert r["valence"] is None and r["valence_source"] is None


def test_arudha_all_nine_read_empty_house_is_a_known_empty_house():
    r = next(x for x in build_signal_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                                          arudha_facts=_arudha_facts(), graha_houses=_all_graha_houses(), now=NOW)
             if x["signal_type_id"] == "arudha:ARUDHA_A2_tenancy")
    assert json.loads(r["configuration_jsonb"])["occupants"] == []
    assert "occupants=[]" in r["signal_summary_text"] and r["valence"] == "neutral"


def test_arudha_tenanted_clause_survives_a_missing_other_graha():
    gh = _all_graha_houses(**{AR_GRAHAS[1]: {"house_d1": 3, "fact_id": "fx"}})
    del gh[AR_GRAHAS[0]]
    assert "tenanted by" in _a2_headline(gh)


# ── bo_vargottama_dhana: same discipline ──────────────────────────────────────────────────────────

def _pos(house, sign, fid):
    return {"house_d1": {"num": house, "fact_id": fid + "_h"}, "sign": {"text": sign, "fact_id": fid + "_s"}}


def _dhana_h2(positions):
    rows = build_dhana_axis_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                                 positions=positions, now=NOW)
    return next(r for r in rows if r["signal_type_id"] == "dhana_axis:H2")["signal_headline_text"]


def test_dhana_untenanted_stated_only_with_all_nine_graha_houses():
    pos = {"LAGNA": _pos(1, "Aries", "lagna")}
    for gc in AR_GRAHAS:                       # every graha read, none in H2
        pos[gc] = _pos(7, "Libra", gc)
    assert " — untenanted" in _dhana_h2(pos)


def test_dhana_missing_graha_house_facts_make_occupancy_unknown_everywhere():
    rows = build_dhana_axis_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                                 positions={"LAGNA": _pos(1, "Aries", "lagna")}, now=NOW)
    h2 = next(r for r in rows if r["signal_type_id"] == "dhana_axis:H2")
    assert h2["signal_headline_text"] == "2nd house (dhana): Taurus, lord Venus"
    assert h2["signal_summary_text"] == ("category=dhana_axis | house=2 | sign=Taurus | lord=Venus")
    cfg = json.loads(h2["configuration_jsonb"])
    assert cfg["occupants"] is None and cfg["valence_net"] is None and cfg["valence_source"] is None
    assert h2["valence"] is None and h2["valence_source"] is None


def test_dhana_all_nine_read_and_empty_house_is_a_known_empty_house():
    pos = {"LAGNA": _pos(1, "Aries", "lagna")}
    for gc in AR_GRAHAS:
        pos[gc] = _pos(7, "Libra", gc)
    rows = build_dhana_axis_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                                 positions=pos, now=NOW)
    h2 = next(r for r in rows if r["signal_type_id"] == "dhana_axis:H2")
    cfg = json.loads(h2["configuration_jsonb"])
    assert cfg["occupants"] == [] and " — untenanted" in h2["signal_headline_text"]
    assert "occupants=[]" in h2["signal_summary_text"] and h2["valence"] == "neutral"


def test_dhana_tenanted_clause_kept():
    pos = {"LAGNA": _pos(1, "Aries", "lagna"), AR_GRAHAS[0]: _pos(2, "Taurus", "x")}
    assert "tenanted by" in _dhana_h2(pos)


# ── bo_bimba: a yoga/dosha signal with no name and no type id yields no node, not a blank label ───

def _yoga_sig(type_id, cfg=None):
    return {"signal_id": "s1", "signal_type_class": "yoga", "signal_type_id": type_id,
            "configuration_jsonb": json.dumps(cfg or {}), "computed_salience": 0.5,
            "domains_affected_array": ["career"], "signal_tradition": "parashari"}


def _yoga_nodes(sig):
    nodes = BIM._build_nodes_for_aya(CHART, "lahiri_chitrapaksha", "b", [sig], NOW)
    return [n for n in nodes if n["node_type"] == "yoga"]


def test_bimba_yoga_without_name_or_type_id_emits_no_blank_node():
    assert _yoga_nodes(_yoga_sig(None)) == []
    assert _yoga_nodes(_yoga_sig("   ")) == []


def test_bimba_yoga_named_by_type_id_keeps_real_label():
    (n,) = _yoga_nodes(_yoga_sig("yoga:gaja_kesari"))
    assert n["node_label_human"] == "yoga:gaja_kesari"
    assert n["citation_human"] == "Yoga node: yoga:gaja_kesari"


def test_bimba_yoga_named_by_config_without_type_id_still_emits():
    (n,) = _yoga_nodes(_yoga_sig(None, {"yoga_name": "Gaja Kesari"}))
    assert n["node_label_human"] == "Gaja Kesari"
    assert n["citation_human"] == "Yoga node: Gaja Kesari"


# ── bo_karanajala ─────────────────────────────────────────────────────────────────────────────────

def test_karanajala_present_text_is_an_honest_null():
    assert KAR._present_text(None) is None
    assert KAR._present_text("  ") is None
    assert KAR._present_text(" x ") == "x"


def test_karanajala_graha_from_cfg_unchanged_for_present_and_absent():
    assert KAR._graha_from_cfg({"graha": "SUN"}) == "Sun"
    assert KAR._graha_from_cfg({"fact_key": "SUN:MOON"}) == "Sun"
    assert KAR._graha_from_cfg({}) is None
    assert KAR._graha_from_cfg({"graha": None}) is None


def test_karanajala_signal_fact_ids_come_from_the_signal_ledger():
    assert KAR._signal_fact_ids({"constituent_facts_array": ["f1", " f2 ", "", None]}) == ["f1", "f2"]
    assert KAR._signal_fact_ids({"constituent_facts_array": None}) == []
    assert KAR._signal_fact_ids({}) == []


def _composite_sig(type_id, facts):
    return {"signal_id": "11111111-1111-1111-1111-111111111111", "signal_type_class": "composite_state",
            "signal_tradition": "parashari", "signal_type_id": type_id,
            "configuration_jsonb": json.dumps({"from_graha": "Sun", "graha": "Sun", "to_graha": "Venus",
                                               "fact_key": "shortest_path_length"}),
            "domains_affected_array": ["career"], "computed_salience": 0.4,
            "verification_pass_status": "single_pass", "constituent_facts_array": facts}


def _aspect_edges(sig):
    node_map = {("graha", "Sun"): "n-sun", ("graha", "Venus"): "n-ven"}
    edges, _ = KAR._build_edges_and_contradictions(CHART, "lahiri_chitrapaksha", "b", [sig], node_map, NOW, None)
    return edges


def test_karanajala_aspect_edge_carries_the_signals_l1_fact_ids():
    (e,) = _aspect_edges(_composite_sig("significator_path:shortest_path_length", ["f555dca35f633005"]))
    assert e["constituent_fact_ids_array"] == ["f555dca35f633005"]
    assert e["citation_human"] == "aspect: Sun→Venus"


def test_karanajala_signal_without_type_id_emits_no_edge_instead_of_a_blank_citation():
    assert _aspect_edges(_composite_sig(None, ["f1"])) == []
    assert _aspect_edges(_composite_sig("  ", ["f1"])) == []


def _sign_conn(rows):
    conn = MagicMock()
    conn.execute.return_value.fetchall.return_value = rows
    return conn


def test_karanajala_sign_value_and_cited_fact_come_from_one_row_with_total_order():
    c = _sign_conn([("fid-a", "SUN", 10.0), ("fid-b", "SUN", 4.0), ("fid-m", "MOON", 2.0), ("x", "NOPE", 1.0)])
    got = KAR._fetch_graha_sign_facts(c, CHART, "lahiri_chitrapaksha")
    assert got == {"Sun": (10, "fid-a"), "Moon": (2, "fid-m")}      # first row per graha (ORDER BY ..., fact_id)
    assert KAR._fetch_graha_sign_numbers(c, CHART, "lahiri_chitrapaksha") == {"Sun": 10, "Moon": 2}
    sql = " ".join(c.execute.call_args[0][0].split())
    assert "fact_category = 'graha_sign_attributes'" in sql and "fact_key = 'sign_num'" in sql
    assert "ORDER BY fact_subject, fact_id" in sql


def _dispositor(sign_fact_ids):
    node_map = {("graha", "Sun"): "n-sun", ("graha", "Saturn"): "n-sat"}
    return KAR._build_dispositor_edges(CHART, "lahiri_chitrapaksha", "b", {"Sun": 10}, node_map, NOW, None,
                                       sign_fact_ids=sign_fact_ids)


def test_karanajala_dispositor_edge_cites_the_sign_fact_when_present():
    (e,) = _dispositor({"Sun": "fid-sun"})
    assert e["constituent_fact_ids_array"] == ["fid-sun"]


def test_karanajala_dispositor_edge_ledger_is_empty_not_invented_when_fact_missing():
    (e,) = _dispositor({})
    assert e["constituent_fact_ids_array"] == []
    (e2,) = _dispositor(None)
    assert e2["constituent_fact_ids_array"] == []


# ── bo_anveshana ──────────────────────────────────────────────────────────────────────────────────

def _msr_rows(n_named, n_blank):
    rows = [{"signal_id": f"s{i}", "signal_type_id": "t", "signal_type_class": "c",
             "source_l1_asset": "ga_x", "computed_salience": 0.1, "domains_affected_array": []}
            for i in range(n_named)]
    rows[0]["computed_salience"] = 9.0                         # a clear outlier inside ga_x
    rows += [{"signal_id": f"b{i}", "signal_type_id": "t", "signal_type_class": "c",
              "source_l1_asset": None if i % 2 else "  ", "computed_salience": 5.0,
              "domains_affected_array": []} for i in range(n_blank)]
    return rows


def test_anveshana_signals_without_a_source_asset_are_not_pooled_under_unknown(monkeypatch):
    monkeypatch.setattr(ANV, "_fetch_dict", lambda *a, **k: _msr_rows(12, 6))
    out = ANV._compute_distributional_anomalies(MagicMock(), CHART, "lahiri_chitrapaksha")
    assert out and all(a["source_l1_asset"] == "ga_x" for a in out)
    assert not any(a["signal_id"].startswith("b") for a in out)


def test_anveshana_named_subsystem_still_flags_its_outlier(monkeypatch):
    monkeypatch.setattr(ANV, "_fetch_dict", lambda *a, **k: _msr_rows(12, 0))
    out = ANV._compute_distributional_anomalies(MagicMock(), CHART, "lahiri_chitrapaksha")
    assert [a["signal_id"] for a in out] == ["s0"]


def _mine_with_brokers(monkeypatch, brokers):
    monkeypatch.setattr(ANV, "_compute_non_obviousness", lambda *a, **k: [])
    monkeypatch.setattr(ANV, "_fetch_embeddings_np", lambda *a, **k: ([], None))
    monkeypatch.setattr(ANV, "_compute_distributional_anomalies", lambda *a, **k: [])
    monkeypatch.setattr(ANV, "_compute_brokers", lambda *a, **k: brokers)
    return ANV._mine_ayanamsha(MagicMock(), CHART, "lahiri_chitrapaksha", "b", NOW)[0]


def _broker(subject):
    return {"msr_signal_id": "sig-1", "node_subject": subject, "node_id": "n1", "node_type": "graha",
            "subsystem_diversity": 3, "edge_count": 4, "betweenness_centrality": 0.1, "pagerank_score": 0.1,
            "primary_domain": "career", "source_subsystem": "ga_x"}


def test_anveshana_broker_with_no_subject_yields_no_blank_subject_prose(monkeypatch):
    for blank in (None, "", "  "):
        assert _mine_with_brokers(monkeypatch, [_broker(blank)]) == []


def test_anveshana_broker_with_subject_keeps_real_prose(monkeypatch):
    (d,) = _mine_with_brokers(monkeypatch, [_broker("Saturn")])
    assert "Saturn as an individual astrological factor" == d["surface_reading"]
    assert d["why_an_acharya_misses_it"].startswith("Node Saturn bridges")


# ── None is never printed into text (SS follow-up, N.7 item 6) ───────────────────────────────────

def test_dhana_unknown_lord_house_is_omitted_not_the_text_none():
    # lord (Venus/Saturn) house not read -> lord_house_d1 is None
    rows = build_dhana_axis_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                                 positions={"LAGNA": _pos(1, "Aries", "lagna")}, now=NOW)
    for r in rows:
        assert "None" not in r["signal_summary_text"] and "None" not in r["signal_headline_text"]
        assert "lord_placed_in_house" not in r["signal_summary_text"]


def test_dhana_known_lord_house_is_still_stated():
    pos = {"LAGNA": _pos(1, "Aries", "lagna"), "VEN": _pos(9, "Sagittarius", "ven")}
    h2 = next(r for r in build_dhana_axis_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                                               positions=pos, now=NOW) if r["signal_type_id"] == "dhana_axis:H2")
    assert "lord_placed_in_house=9" in h2["signal_summary_text"]


def test_arudha_unknown_sign_is_omitted_not_the_text_none():
    facts = {"ARUDHA_A1": {"house_d1": {"num": 9, "fact_id": "fal"}},
             "ARUDHA_A2": {"house_d1": {"num": 3, "fact_id": "fa2"}}}
    rows = build_signal_rows(chart_id=CHART, ayanamsha_id="lahiri_chitrapaksha", build_id="b",
                             arudha_facts=facts, graha_houses=_all_graha_houses(), now=NOW)
    for r in rows:
        assert "None" not in r["signal_summary_text"] and "None" not in r["signal_headline_text"], r["signal_type_id"]
    al = next(r for r in rows if r["signal_type_id"] == "arudha:AL_bhava_relation")
    assert al["signal_headline_text"] == "Arudha Lagna (AL) in H9 — classical category: trikona"
    assert al["signal_summary_text"] == "category=arudha | AL_house=9 | AL_category=trikona"


def test_arudha_known_sign_text_unchanged():
    assert _a2_headline(_all_graha_houses()) == "A2 (dhana arudha) in H3 (Cancer) — untenanted"
