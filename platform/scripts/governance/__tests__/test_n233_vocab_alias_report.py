"""test_n233_vocab_alias_report.py: the non-canonical-spelling report (vocab_alias_report.py, SS ruling N-233 R2). Offline; runs on a census JSON."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import vocab_alias_report as vr  # noqa: E402


def _census(tmp_path, found, verdict="FAIL", unread=()):
    d = {"L0": {"assets": [{"asset_id": "bg_nakshatra", "measurements": {"Vocab.alias": {"v": verdict, "vocab_values": {"found": found, "unread": list(unread)}}}},
                           {"asset_id": "bg_other", "measurements": {"Vocab.alias": {"v": "PASS", "vocab_values": {"found": [dict(table="t", column="c", classes=["graha"], spellings=[])]}}}},
                           {"asset_id": "bg_none", "measurements": {}}]}}
    p = tmp_path / "census_L0.json"
    p.write_text(json.dumps(d))
    return p


FOUND = [dict(table="reference_nakshatra", column="alt_names", classes=["nakshatra"], spellings=["Mula", "Kritika", "MULA"])]


def test_extract_lists_only_assets_with_noncanonical_spellings(tmp_path):
    rows = vr.extract([_census(tmp_path, FOUND)])
    assert [(r["asset"], r["table"], r["column"], r["spellings"]) for r in rows] == [("bg_nakshatra", "reference_nakshatra", "alt_names", ["Mula", "Kritika", "MULA"])]


def test_classify_uses_the_exact_registered_string_only():
    reg, label = vr.offline_registered()
    assert "OFFLINE STAND-IN" in label
    assert vr.classify("Mula", reg)["status"] == "REGISTERED" and "canonical_name_sa" in vr.classify("Mula", reg)["sources"]
    assert vr.classify("Kritika", reg)["status"] == "UNREGISTERED"          # the ontology registers Krittika / kritika, not this spelling
    assert vr.classify("MULA", reg)["status"] == "UNREGISTERED"             # a case variant of a registered alias is not registered


def test_a_live_alias_file_replaces_the_stand_in(tmp_path):
    f = tmp_path / "live.json"
    f.write_text(json.dumps([dict(c="nakshatra", id="nak_03_krittika", sa="Krittika", syn=["Kritika"])]))
    reg, label = vr.live_registered(f)
    assert "LIVE" in label and vr.classify("Kritika", reg)["status"] == "REGISTERED" and vr.classify("Mula", reg)["status"] == "UNREGISTERED"


def test_report_counts_and_renders_each_spelling_with_its_status(tmp_path):
    reg, label = vr.offline_registered()
    rep = vr.report([_census(tmp_path, FOUND)], reg, label, with_locations=False)
    s = rep["summary"]
    assert (s["assets_with_noncanonical_spellings"], s["spellings"], s["registered"], s["unregistered"], s["still_fail_after_rule"]) == (1, 3, 1, 2, 1)
    txt = vr.render(rep)
    assert "`Mula`: REGISTERED via canonical_name_sa" in txt and "`Kritika`: UNREGISTERED" in txt and "reference_nakshatra.alt_names (nakshatra)" in txt


def test_an_asset_whose_every_spelling_is_registered_is_cleared_but_unread_parts_keep_it_partial(tmp_path):
    reg, label = vr.offline_registered()
    only = [dict(table="t", column="c", classes=["nakshatra"], spellings=["Mula"])]
    rep = vr.report([_census(tmp_path, only)], reg, label, with_locations=False)
    assert rep["assets"]["bg_nakshatra"]["unregistered"] == 0 and rep["assets"]["bg_nakshatra"]["after"].startswith("no longer FAIL")
    rep = vr.report([_census(tmp_path, only, unread=["t.x: not read"])], reg, label, with_locations=False)
    assert rep["assets"]["bg_nakshatra"]["after"].startswith("PARTIAL")


def test_the_locator_finds_the_seed_literal_in_the_writer_source_set():
    loc = vr.locate("bg_nakshatra", "reference_nakshatra", "Pooradam")
    assert any("l0_nakshatra.py" in x for x in loc["literal"]) and loc["table_write"], loc


def test_cli_prints_the_registered_sql_and_writes_the_report(tmp_path, capsys):
    assert vr.main(["--print-registered-sql"]) == 0
    assert "FROM brahma_ontology" in capsys.readouterr().out
    out = tmp_path / "r.md"
    assert vr.main(["--census", str(_census(tmp_path, FOUND)), "--out", str(out), "--no-locations"]) == 0
    assert out.read_text().startswith("# VOCAB_ALIAS_NONCANONICAL")
