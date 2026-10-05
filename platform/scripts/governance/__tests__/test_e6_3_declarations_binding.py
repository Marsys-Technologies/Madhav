"""E6.3 / N-74 add-on: a gate certificate is CURRENT only if its `declarations_sha256` equals the sha256 of the BYTES of
platform/scripts/governance/asset_declarations.json AT THE REF read (E5.1's definition). Fixtures: the golden ledgers in
fixtures/e6_3_golden were written by the real E5.1 writer, which stamps the field (README); the hand-written records here
carry it exactly as that writer does (gate: sha + version; addition: null/null)."""
from __future__ import annotations

import hashlib
import os
import sys

import pytest

pytestmark = pytest.mark.skip(reason="the E6.3 certificate reader was dropped by owner decision N-152; the module stays importable, its tests are not run in CI")

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import DECL_TEXT, DECLARATIONS, World, cert, git, load_tracker, mini_patch  # noqa: E402

T = load_tracker()
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}
OTHER = DECL_TEXT.replace("1.0.0", "1.0.1")
SHA = hashlib.sha256(DECL_TEXT.encode()).hexdigest()
OTHER_SHA = hashlib.sha256(OTHER.encode()).hexdigest()


@pytest.fixture(autouse=True)
def _mini(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture
def w(tmp_path):
    return World(tmp_path).default()


def got(w):
    w.commit()
    return w.elevated(T)


def raises(w):
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    return e.value


def test_matching_declarations_make_the_gates_current_and_the_report_says_so(w):
    w.commit()
    rep = T.elevated_report(w.last, str(w.repo))
    assert set(rep) == ALL
    for a in ("ga_alpha", "bg_beta", "ka_gamma"):
        assert rep[a]["declarations_current"] is True and rep[a]["stale_declaration_cells"] == []
    assert T.stale_declaration_cells(w.last, str(w.repo)) == []


def test_edited_declarations_at_the_ref_make_every_gate_stale_and_withhold_the_asset(w):
    w.declarations_text = OTHER
    w.commit()
    assert w.elevated(T) == {"ka_gamma"}                                   # only the terminal asset; no measurement counts
    cells = T.stale_declaration_cells(w.last, str(w.repo))
    assert cells and {c["reason"] for c in cells} == {"stale"} and {c["asset"] for c in cells} == {"ga_alpha", "bg_beta"}
    assert {c["recorded_sha256"] for c in cells} == {SHA} and {c["at_ref_sha256"] for c in cells} == {OTHER_SHA}
    assert {c["recorded_version"] for c in cells} == {"1.0.0"}
    assert {c["criterion"] for c in cells if c["asset"] == "bg_beta"} == {"Ldgr.src", "Idem.pat", "Idem.alt", "Null.x", "Build.any", "Build.target"}


def test_the_sha_is_of_the_bytes_not_of_the_parsed_json(w):
    w.declarations_text = DECL_TEXT + " "                                 # a trailing byte: the same JSON, different bytes
    assert got(w) == {"ka_gamma"}


def test_one_stale_gate_withholds_only_its_asset(w):
    w.find("ga_alpha", "Idem.pat").update(declarations_sha256=OTHER_SHA)
    assert got(w) == ALL - {"ga_alpha"}
    cells = T.stale_declaration_cells(w.last, str(w.repo))
    assert [(c["asset"], c["criterion"], c["recorded_sha256"], c["reason"]) for c in cells] == [("ga_alpha", "Idem.pat", OTHER_SHA, "stale")]


def test_a_stale_upstream_gate_makes_its_dependants_stale_too(w):
    w.find("ga_alpha", "Ldgr.src").update(declarations_sha256=OTHER_SHA)
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["ga_alpha|gate|Ldgr.src@1"]
    assert got(w) == ALL - {"ga_alpha"}


def test_a_gate_with_no_declarations_binding_is_not_current_and_is_reported_unbound(w):
    rec = w.find("ga_alpha", "Idem.pat")
    del rec["declarations_sha256"], rec["declarations_version"]            # an ABSENT key: a v2 record from before the binding
    assert got(w) == ALL - {"ga_alpha"}
    assert [(c["criterion"], c["reason"], c["recorded_sha256"]) for c in T.stale_declaration_cells(w.last, str(w.repo))] == [("Idem.pat", "unbound", None)]


def test_a_present_null_sha_on_a_v2_gate_is_a_forgery_and_raises(w):
    w.find("ga_alpha", "Idem.pat").update(declarations_sha256=None, declarations_version=None)
    raises(w)


def test_null_on_an_addition_is_fine_and_still_counts(w):
    add = w.find("bg_beta", "D-GROUNDING", "addition")
    assert add["declarations_sha256"] is None and add["declarations_version"] is None
    assert "bg_beta" in got(w)


def test_an_addition_may_not_carry_a_declarations_binding(w):
    w.find("bg_beta", "D-GROUNDING", "addition")["declarations_sha256"] = SHA
    raises(w)


@pytest.mark.parametrize("over", [dict(declarations_sha256="xyz"), dict(declarations_sha256=SHA.upper()), dict(declarations_sha256=5),
                                  dict(declarations_version="  "), dict(declarations_version=1),
                                  dict(declarations_sha256=None, declarations_version="1.0.0")])
def test_a_malformed_declarations_field_raises(w, over):
    w.find("ga_alpha", "Idem.pat").update(over)
    raises(w)


def test_a_version_with_an_absent_sha_key_raises(w):
    rec = w.find("ga_alpha", "Idem.pat")
    del rec["declarations_sha256"]                    # the key is absent (not a present null) but a version is still there
    raises(w)


def test_a_v1_record_carrying_a_declarations_field_raises(w):
    rec = w.find("ga_alpha", "Idem.pat")
    for k in ("citation_state", "citation_state_caveat"):
        del rec[k]
    rec["record_version"] = 1
    raises(w)


def test_a_version_without_a_matching_sha_text_is_informational_only(w):
    w.find("ga_alpha", "Idem.pat")["declarations_version"] = "9.9.9"        # the sha, not the version, decides currency
    assert got(w) == ALL


def test_a_missing_declarations_file_at_the_ref_raises_fail_closed(w):
    w.raw[DECLARATIONS] = None
    e = raises(w)
    assert e.code == "unreadable"


def test_a_missing_declarations_file_raises_even_when_no_certificate_exists(tmp_path):
    w = World(tmp_path)
    w.disps.append(__import__("_e6_3_fixtures").disp("ka_gamma", "retire", reason="gone"))
    w.raw[DECLARATIONS] = None
    raises(w)


def test_the_declarations_are_read_at_the_ref_not_the_working_tree_and_each_ref_answers_for_itself(w):
    first = w.commit()
    assert w.elevated(T, first) == ALL
    (w.repo / DECLARATIONS).write_text(OTHER, encoding="utf-8")            # dirty working tree: no effect
    assert w.elevated(T, first) == ALL
    w.declarations_text = OTHER
    second = w.commit("declarations edited")
    assert w.elevated(T, first) == ALL and w.elevated(T, second) == {"ka_gamma"}


def test_a_stale_non_required_gate_cell_is_listed_on_an_elevated_asset(w):
    w.certs.append(cert("ga_alpha", "Cost.base", declarations_sha256=OTHER_SHA))      # an informational criterion
    w.commit()
    rep = T.elevated_report(w.last, str(w.repo))
    assert "ga_alpha" in rep and rep["ga_alpha"]["declarations_current"] is False
    assert [(c["criterion"], c["reason"]) for c in rep["ga_alpha"]["stale_declaration_cells"]] == [("Cost.base", "stale")]
    assert rep["bg_beta"]["declarations_current"] is True


def test_a_newer_generation_bound_to_the_current_declarations_clears_the_stale_cell(w):
    w.find("ga_alpha", "Idem.pat").update(declarations_sha256=OTHER_SHA)
    w.certs.append(cert("ga_alpha", "Idem.pat", gen=2))
    w.commit()
    assert "ga_alpha" in w.elevated(T) and T.stale_declaration_cells(w.last, str(w.repo)) == []


def test_elevated_assets_is_still_the_key_set_of_the_report(w):
    w.find("bg_beta", "Idem.pat").update(declarations_sha256=OTHER_SHA)
    w.commit()
    assert w.elevated(T) == set(T.elevated_report(w.last, str(w.repo))) == {"ga_alpha", "ka_gamma"}


def test_the_declarations_path_is_the_one_e5_1_binds_to():
    assert T.E63_DECLARATIONS_PATH == "platform/scripts/governance/asset_declarations.json"


GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "e6_3_golden")


@pytest.mark.parametrize("name,assets", [("ledger_clean.jsonl", {"ga_alpha", "ga_beta"}),
                                         ("ledger_v2.jsonl", {"ga_alpha", "ga_beta", "ga_gamma"})])
def test_golden_ledgers_from_the_real_writer_are_bound_to_the_fixtures_declarations(tmp_path, name, assets):
    """The real E5.1 writer stamped sha256(DECL_TEXT) on every gate: with those bytes at the ref the assets are elevated; with any
    other bytes at the ref nothing the ledger certifies is."""
    from _e6_3_fixtures import CERTS, disp
    for text, want in ((DECL_TEXT, assets), (OTHER, set())):
        sub = tmp_path / ("ok" if text == DECL_TEXT else "edited")
        sub.mkdir()
        w = World(sub)
        for a in ("ga_alpha", "ga_beta", "ga_gamma", "ga_delta"):
            w.disps.append(disp(a, "keep"))
        w.raw[CERTS] = open(os.path.join(GOLDEN_DIR, name), "rb").read()
        w.declarations_text = text
        w.commit()
        assert w.elevated(T) == want, (name, text == DECL_TEXT)
