"""E6.3 reader vs E5.1's own validator: ONE definition. `elevated_report` runs E5.1's `nikasha_certify.parse_records` (loaded from the
SAME ref, in a subprocess) on the certificate ledger before its own reading, so the reader never accepts a ledger E5.1 refuses,
whatever either side's copy of a rule says. The reader's own rules remain (E5.5 events, registry, currency, dispositions) and are
checked against E5.1 by the differential test below (a seeded single-field fuzz: reader accepts => E5.1 accepts)."""
from __future__ import annotations

import collections
import hashlib
import json
import os
import pathlib
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from _e6_3_fixtures import (CERTS, NIKASHA, World, cert, chained, disp, load_tracker, mini_patch, nikasha_text)  # noqa: E402

T = load_tracker()
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}
GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "e6_3_golden" / "ledger_v2.jsonl"


@pytest.fixture(autouse=True)
def _mini(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture
def w(tmp_path):
    return World(tmp_path).default()


def raises(w, needle=None, code=None):
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    if needle:
        assert needle in str(e.value), e.value
    if code:
        assert e.value.code == code, e.value
    return e.value


def test_a_clean_ledger_passes_the_gate(w):
    w.commit()
    assert w.elevated(T) == ALL


def test_a_record_e5_1_refuses_is_refused_by_the_reader_even_when_the_readers_own_copy_of_the_rule_is_gone(w, monkeypatch):
    """Seeded defect: a citation_state on a non-citation gate. The reader's own copy of the rule is disabled; the ledger is still
    refused because E5.1's validator (from the ref) refuses it."""
    monkeypatch.setattr(T, "_e63_check_citation_fields", lambda *a, **k: None)
    rec = w.find("ga_alpha", "Idem.pat")
    rec["citation_state"] = "sourced"
    raises(w, "E5.1's own reader refuses", "malformed")


def test_the_same_for_a_declarations_defect_and_a_chain_defect(w, monkeypatch):
    monkeypatch.setattr(T, "_e63_check_declarations_fields", lambda *a, **k: None)
    w.find("ga_alpha", "Idem.pat")["declarations_sha256"] = "xyz"
    raises(w, "E5.1's own reader refuses")


def test_the_reader_loads_the_validator_from_the_ref_not_from_the_checkout(w):
    # the committed validator refuses everything; the checkout's (working-tree) E5.1 would accept this ledger
    src = nikasha_text()
    marker = "def parse_records(data: bytes) -> list[dict]:\n"
    assert marker in src
    w.raw[NIKASHA] = src.replace(marker, marker + '    _refuse("bad_ledger", "seeded: the validator AT THE REF refuses")\n')
    raises(w, "seeded: the validator AT THE REF refuses")


def test_a_ref_without_the_validator_raises_fail_closed(w):
    w.raw[NIKASHA] = None
    assert raises(w).code == "unreadable"


def test_a_validator_at_the_ref_that_cannot_run_raises(w):
    w.raw[NIKASHA] = "raise SystemExit('broken validator')\n"
    assert raises(w).code == "registry_unreadable"


@pytest.mark.parametrize("const,value", [("E63_CITATION_STRICT", ()), ("E63_CITATION_STRICT", ("Carr.D1", "Idem.alt")),
                                         ("E63_CITATION_STATES", ("sourced",)), ("E63_CITATION_BLOCKING", ("refuted",)),
                                         ("E63_RECORD_VERSIONS", (1, 2, 3)), ("E63_DECLARATIONS_PATH", "x/y.json")])
def test_a_rule_the_two_sides_disagree_on_raises_instead_of_being_applied_by_one_of_them(w, monkeypatch, const, value):
    monkeypatch.setattr(T, const, value)
    e = raises(w, "disagree", "registry_unreadable")
    assert const.replace("E63_", "") in str(e) or "CITATION" in str(e) or "READABLE" in str(e) or "DECLARATIONS" in str(e)


def test_a_citation_criteria_disagreement_raises(w, monkeypatch):
    monkeypatch.setattr(T, "E63_CITATION_CRITERIA", ("Ldgr.src",))
    raises(w, "disagree")


def test_the_gate_runs_in_both_public_functions(w):
    w.find("ga_alpha", "Idem.pat")["citation_state"] = "sourced"
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        T.elevated_report(w.last, str(w.repo))
    with pytest.raises(T.ElevatedInputError):
        T.elevated_assets(w.last, str(w.repo))
    with pytest.raises(T.ElevatedInputError):
        T.citation_blocked_cells(w.last, str(w.repo))
    with pytest.raises(T.ElevatedInputError):
        T.stale_declaration_cells(w.last, str(w.repo))


# ---- differential: reader accepts => E5.1 accepts ---------------------------------------------------------------------

def _rechain(rows):
    out = [json.dumps(rows[0])]
    prev = hashlib.sha256(out[0].encode()).hexdigest()
    for i, r in enumerate(rows[1:], 1):
        line = json.dumps(dict(r, seq=i, prev_sha256=prev))
        out.append(line)
        prev = hashlib.sha256(line.encode()).hexdigest()
    return ("\n".join(out) + "\n").encode()


def test_differential_the_readers_parser_never_accepts_what_e5_1s_own_validator_refuses(tmp_path, monkeypatch):
    """Seeded fuzz over single-field mutations of a real-writer ledger (record fields set to odd values or deleted, re-chained):
    count the ledgers the reader's own parser accepts but E5.1 refuses. Run with the REAL citation constants (the base ledger's
    citation fields are normalised to null/false so it is valid under them)."""
    import nikasha_certify as nc
    from _e6_3_fixtures import MINI_FLOOR, MINI_PINNED
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", MINI_FLOOR)
    monkeypatch.setattr(T, "E63_REQUIRED_CRITERIA", MINI_PINNED)
    monkeypatch.setattr(T, "E63_CITATION_CRITERIA", nc.CITATION_CRITERIA)
    rows = [json.loads(ln) for ln in GOLDEN.read_text().splitlines()]
    base = [rows[0]] + [dict(r, citation_state=None, citation_state_caveat=False) if r.get("kind") in ("gate", "addition") else r
                        for r in rows[1:]]
    wld = World(tmp_path)
    wld.commit()
    facts = T._e63_registry_facts(str(wld.repo), wld.last)

    def mine(data):
        try:
            T._e63_parse_certs(data, facts)
            return True
        except T.ElevatedInputError:
            return False

    def theirs(data):
        try:
            nc.parse_ledger(data)
            return True
        except nc.CertificationRefused:
            return False

    assert mine(_rechain(base)) and theirs(_rechain(base))
    pool = [None, "", 0, 1, -1, True, False, "x", "sourced", "N-70", "1" * 64, "A" * 64, [], {}, [1], {"a": 1}, 2, 3, 1.5, "PASS",
            "gate", "addition", "L1", "L9", " ", "unsourced", "refuted", "applicability_facts"]
    rnd = random.Random(7)
    bad, ours_stricter = [], 0
    for _ in range(600):
        rs = [dict(r) for r in base]
        i = rnd.randrange(1, len(rs))
        keys = list(rs[i]) + ["citation_state", "citation_state_caveat", "declarations_sha256", "declarations_version", "record_version",
                              "na", "type", "kind"]
        k = rnd.choice(keys)
        if rnd.random() < 0.25:
            rs[i].pop(k, None)
        else:
            rs[i][k] = rnd.choice(pool)
        data = _rechain(rs)
        m, t = mine(data), theirs(data)
        if m and not t:
            bad.append((rs[i].get("kind") or rs[i].get("type"), k, rs[i].get(k, "<deleted>")))
        ours_stricter += (t and not m)
    assert bad == [], f"the reader's parser accepts what E5.1 refuses: {bad[:5]}"
    assert ours_stricter > 0          # the reader's own extra rules (registry, layer, gate) do refuse more: the run is not vacuous


@pytest.mark.parametrize("val", [[], {}, [1], {"a": 1}])
def test_an_unhashable_layer_is_a_clean_refusal_not_a_crash(tmp_path, val):
    wld = World(tmp_path)
    wld.commit()
    facts = T._e63_registry_facts(str(wld.repo), wld.last)
    rows = [json.loads(ln) for ln in GOLDEN.read_text().splitlines()]
    rows[1]["layer"] = val
    with pytest.raises(T.ElevatedInputError):
        T._e63_parse_certs(_rechain(rows), facts)
