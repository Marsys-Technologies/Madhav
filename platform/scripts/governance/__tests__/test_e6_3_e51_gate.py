"""E6.3 reader vs E5.1's own validator: ONE definition. `elevated_report` runs E5.1's `nikasha_certify.parse_records` (loaded from the
SAME ref, in a subprocess) on the certificate ledger and reads the RECORDS it accepts: the chain, seq, generations, record_version,
citation_state / caveat and the declarations binding are defined only there; the reader holds no copy of those rules (tests: "the
copies are gone"). The reader's own rules remain (E5.5 events, registry, currency, dispositions). The validator's verdict is memoised
per process under (ref, sha256(ledger), sha256(nikasha_certify.py), sha256(asset_census.py), sha256(driver)); the cache tests are the
seeded defects for that key."""
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
from _e6_3_fixtures import (CERTS, NIKASHA, World, cert, chained, disp, load_tracker, mini_patch, nikasha_text, parse_via_validator)  # noqa: E402

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


def test_a_citation_defect_is_refused_by_e5_1s_validator_through_the_reader(w):
    """Seeded defect: a citation_state on a non-citation gate. Only E5.1's validator (from the ref) holds that rule."""
    w.find("ga_alpha", "Idem.pat")["citation_state"] = "sourced"
    raises(w, "E5.1's own reader refuses", "malformed")


def test_a_declarations_defect_and_a_chain_defect_are_refused_by_e5_1s_validator_too(w):
    w.find("ga_alpha", "Idem.pat")["declarations_sha256"] = "xyz"
    raises(w, "E5.1's own reader refuses")


def test_a_broken_chain_is_refused_by_e5_1s_validator(w):
    w.commit()
    lines = (w.repo / CERTS).read_text(encoding="utf-8").splitlines()
    lines[2], lines[3] = lines[3], lines[2]
    w.raw[CERTS] = "\n".join(lines) + "\n"
    raises(w, "E5.1's own reader refuses", "malformed")


@pytest.mark.parametrize("name", ["_e63_check_citation_fields", "_e63_check_declarations_fields", "E63_CITATION_STRICT",
                                  "E63_CITATION_STATES", "E63_RECORD_VERSIONS", "E63_CITATION_CRITERIA"])
def test_the_readers_copies_of_e5_1s_rules_are_gone(name):
    assert not hasattr(T, name), f"{name}: the reader must not hold its own copy of an E5.1 rule"


def test_the_readers_source_applies_no_citation_or_declarations_rule():
    """No code path of the reader inspects `record_version`, compares against the citation states, or checks a declarations
    field's shape (it only READS the validated fields): the strings that name E5.1's rules do not occur as code constants."""
    import ast
    src = (pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/control/asset_elevation_tracker.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    consts = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    for needle in ("record_version", "sourced_ocr_unverified", "applicability_facts"):
        assert needle not in consts, f"the reader mentions {needle!r} as a rule constant"
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not {"E63_CITATION_STRICT", "E63_CITATION_STATES", "E63_RECORD_VERSIONS", "E63_CITATION_CRITERIA"} & names


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


@pytest.mark.parametrize("const,value", [("E63_CITATION_BLOCKING", ("refuted",)), ("E63_CITATION_BLOCKING", ()),
                                         ("E63_DECLARATIONS_PATH", "x/y.json")])
def test_a_constant_the_reader_still_uses_and_the_two_sides_disagree_on_raises(w, monkeypatch, const, value):
    monkeypatch.setattr(T, const, value)
    e = raises(w, "disagree", "registry_unreadable")
    assert "CITATION_PASS_REFUSED" in str(e) or "DECLARATIONS_RELPATH" in str(e)


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


def test_differential_the_readers_pipeline_never_accepts_what_e5_1_refuses(tmp_path, monkeypatch):
    """Seeded fuzz over single-field mutations of a real-writer ledger (record fields set to odd values or deleted, re-chained):
    the reader's pipeline (E5.1's validator at the ref, then the reader's own checks) must never accept a ledger the checkout's
    E5.1 refuses; the reader's own extra rules (registry, layer, gate) refuse some ledgers E5.1 accepts (the run is not vacuous).
    Run with the REAL citation constants (the base ledger's citation fields are normalised to null/false)."""
    import nikasha_certify as nc
    from _e6_3_fixtures import MINI_FLOOR, MINI_PINNED, real_citation_patch
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", MINI_FLOOR)
    monkeypatch.setattr(T, "E63_REQUIRED_CRITERIA", MINI_PINNED)
    real_citation_patch(monkeypatch, T)
    rows = [json.loads(ln) for ln in GOLDEN.read_text().splitlines()]
    base = [rows[0]] + [dict(r, citation_state=None, citation_state_caveat=False) if r.get("kind") in ("gate", "addition") else r
                        for r in rows[1:]]
    wld = World(tmp_path)
    wld.commit()
    facts = T._e63_registry_facts(str(wld.repo), wld.last)

    def mine(data):
        try:
            parse_via_validator(T, wld.repo, wld.last, data, facts)
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
    for _ in range(150):
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
    assert bad == [], f"the reader's pipeline accepts what E5.1 refuses: {bad[:5]}"
    assert ours_stricter > 0


@pytest.mark.parametrize("val", [[], {}, [1], {"a": 1}])
def test_an_unhashable_layer_is_a_clean_refusal_not_a_crash(tmp_path, val):
    wld = World(tmp_path)
    wld.commit()
    facts = T._e63_registry_facts(str(wld.repo), wld.last)
    rows = [json.loads(ln) for ln in GOLDEN.read_text().splitlines()]
    rows[1]["layer"] = val
    with pytest.raises(T.ElevatedInputError):
        parse_via_validator(T, wld.repo, wld.last, _rechain(rows), facts)


# ---- the validator-result cache: its key and its seeded defects ------------------------------------------------------------

@pytest.fixture
def runs(monkeypatch):
    """Count the real validator runs (every cache miss runs it once)."""
    T._E63_E51_CACHE.clear()
    box = []
    real = T._e63_e51_run

    def spy(sha, data, nc_src, census_src):
        box.append(sha)
        return real(sha, data, nc_src, census_src)
    monkeypatch.setattr(T, "_e63_e51_run", spy)
    yield box
    T._E63_E51_CACHE.clear()


def _ledger(w):
    return T._e63_show(str(w.repo), w.last, CERTS)


def test_cache_the_same_ref_ledger_and_validator_run_the_validator_once(w, runs):
    w.commit()
    first = w.elevated(T)
    again = w.elevated(T)
    assert first == again == ALL and len(runs) == 1
    T.elevated_report(w.last, str(w.repo))
    T.citation_blocked_cells(w.last, str(w.repo))
    assert len(runs) == 1                                   # every public function shares the one run


def test_cache_one_changed_ledger_byte_runs_the_validator_again_and_is_refused(w, runs):
    sha = w.commit()
    good = _ledger(w)
    T._e63_e51_validate(str(w.repo), sha, good)
    assert len(runs) == 1
    flipped = good.replace(b'"Idem.pat"', b'"Idem.pax"', 1)            # one byte of one certificate line
    assert flipped != good and len(flipped) == len(good)
    with pytest.raises(T.ElevatedInputError) as e:
        T._e63_e51_validate(str(w.repo), sha, flipped)            # same ref, same validator, other bytes: a MISS, then refused
    assert len(runs) == 2 and "E5.1's own reader refuses" in str(e.value)
    T._e63_e51_validate(str(w.repo), sha, good)                  # the original is still accepted from the cache
    assert len(runs) == 2


def test_cache_a_refusal_is_cached_as_a_refusal_never_as_a_pass(w, runs):
    w.find("ga_alpha", "Idem.pat")["citation_state"] = "sourced"
    w.commit()
    for _ in range(3):
        with pytest.raises(T.ElevatedInputError) as e:
            w.elevated(T)
        assert e.value.code == "malformed" and "E5.1's own reader refuses" in str(e.value)
    assert len(runs) == 1                                    # replayed, but always as the refusal
    assert [v["ok"] for v in T._E63_E51_CACHE.values()] == [False]


def test_cache_a_different_ref_is_a_miss_even_with_identical_bytes(w, runs):
    w.commit()
    w.elevated(T)
    w.commit("same files, new commit")
    other = w.last
    T.elevated_assets(other, str(w.repo))
    assert len(runs) == 2
    assert len({k[0] for k in T._E63_E51_CACHE}) == 2


def test_cache_a_swapped_validator_text_is_a_miss_and_its_verdict_is_used(w, runs, monkeypatch):
    sha = w.commit()
    data = _ledger(w)
    assert T._e63_e51_validate(str(w.repo), sha, data)               # accepted under the real validator, now cached
    real_show = T._e63_show
    src = real_show(str(w.repo), sha, T.E63_E51_PATH).decode()
    marker = "def parse_records(data: bytes) -> list[dict]:\n"
    swapped = src.replace(marker, marker + '    _refuse("bad_ledger", "seeded: a swapped validator refuses")\n').encode()

    def show(repo, ref, path):
        return swapped if path == T.E63_E51_PATH else real_show(repo, ref, path)
    monkeypatch.setattr(T, "_e63_show", show)
    with pytest.raises(T.ElevatedInputError, match="seeded: a swapped validator refuses"):
        T._e63_e51_validate(str(w.repo), sha, data)
    assert len(runs) == 2


def test_cache_a_swapped_census_text_is_a_miss(w, runs, monkeypatch):
    sha = w.commit()
    data = _ledger(w)
    T._e63_e51_validate(str(w.repo), sha, data)
    real_show = T._e63_show

    def show(repo, ref, path):
        b = real_show(repo, ref, path)
        return b + b"\n# one more comment\n" if path == T.E63_CENSUS_PATH else b
    monkeypatch.setattr(T, "_e63_show", show)
    T._e63_e51_validate(str(w.repo), sha, data)
    assert len(runs) == 2


def test_cache_the_key_is_all_five_parts(w):
    k = T._e63_e51_key("r" * 40, b"ledger", b"nc", b"census")
    assert k != T._e63_e51_key("s" * 40, b"ledger", b"nc", b"census")
    assert k != T._e63_e51_key("r" * 40, b"ledgeR", b"nc", b"census")
    assert k != T._e63_e51_key("r" * 40, b"ledger", b"nC", b"census")
    assert k != T._e63_e51_key("r" * 40, b"ledger", b"nc", b"censuS")
    assert k == T._e63_e51_key("r" * 40, b"ledger", b"nc", b"census")
    assert len(set(k)) == 5 and k[-1] == hashlib.sha256(T._E63_E51_DRIVER.encode()).hexdigest()


def test_cache_returned_records_are_copies_a_caller_cannot_poison_the_cache(w, runs):
    sha = w.commit()
    data = _ledger(w)
    first = T._e63_e51_validate(str(w.repo), sha, data)
    first[0]["verdict"] = "FAIL"
    first.clear()
    again = T._e63_e51_validate(str(w.repo), sha, data)
    assert len(runs) == 1 and again and again[0]["verdict"] != "FAIL"


def test_cache_the_constants_check_still_runs_on_a_hit(w, runs, monkeypatch):
    sha = w.commit()
    data = _ledger(w)
    T._e63_e51_validate(str(w.repo), sha, data)
    monkeypatch.setattr(T, "E63_CITATION_BLOCKING", ("refuted",))
    with pytest.raises(T.ElevatedInputError, match="disagree"):
        T._e63_e51_validate(str(w.repo), sha, data)
    assert len(runs) == 1


def test_cache_a_validator_that_gives_no_answer_is_not_cached_and_still_raises(w, runs, monkeypatch):
    w.raw[NIKASHA] = "raise SystemExit('broken validator')\n"
    w.commit()
    for _ in range(2):
        with pytest.raises(T.ElevatedInputError) as e:
            w.elevated(T)
        assert e.value.code == "registry_unreadable"
    assert len(runs) == 2 and not T._E63_E51_CACHE


def test_cache_a_missing_validator_or_ledger_raises_before_any_lookup(w, runs):
    w.raw[NIKASHA] = None
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)
    (w.repo.parent / "second").mkdir()
    w2 = World(w.repo.parent / "second").default()
    w2.raw[CERTS] = None
    w2.commit()
    with pytest.raises(T.ElevatedInputError):
        w2.elevated(T)
    assert not runs and not T._E63_E51_CACHE


def test_cache_is_bounded_and_evicts_the_oldest_entry(w, monkeypatch):
    T._E63_E51_CACHE.clear()
    monkeypatch.setattr(T, "_E63_E51_CACHE_MAX", 3)
    calls = []

    def fake(sha, data, nc_src, census_src):
        calls.append(data)
        return {"ok": True, "constants": {"CITATION_PASS_REFUSED": list(T.E63_CITATION_BLOCKING),
                                          "DECLARATIONS_RELPATH": T.E63_DECLARATIONS_PATH}, "records": []}
    monkeypatch.setattr(T, "_e63_e51_run", fake)
    sha = w.commit()
    for i in range(5):
        T._e63_e51_validate(str(w.repo), sha, b"ledger %d" % i)
    assert len(T._E63_E51_CACHE) == 3 and len(calls) == 5
    T._e63_e51_validate(str(w.repo), sha, b"ledger 4")           # newest: a hit
    assert len(calls) == 5
    T._e63_e51_validate(str(w.repo), sha, b"ledger 0")           # evicted: runs again
    assert len(calls) == 6
    T._E63_E51_CACHE.clear()


# ---- the dispatch the reader keeps (E5.1 settled which lines are certificates and which are events) ----------------------------

def test_a_certificate_line_with_a_stray_type_is_refused_not_read_as_an_event(w):
    """E5.1 accepts a certificate that carries an extra `type` field (it reads it as a certificate); the reader will not guess."""
    w.find("ga_alpha", "Idem.pat")["type"] = "invalidation"
    w.commit()
    with pytest.raises(T.ElevatedInputError, match="both a `type` and a cert_key"):
        w.elevated(T)


def test_an_event_of_a_type_nobody_reads_is_refused_when_handed_to_the_parser(tmp_path):
    wld = World(tmp_path)
    wld.commit()
    facts = T._e63_registry_facts(str(wld.repo), wld.last)
    with pytest.raises(T.ElevatedInputError, match="unknown event type"):
        T._e63_parse_certs([{"seq": 1, "type": "bogus"}], facts)


def test_the_readers_event_classification_copy_is_gone():
    for name in ("_e63_is_cert_line", "_e63_is_event_line", "E63_EVENT_FORBIDDEN", "E63_EVENT_TYPES"):
        assert not hasattr(T, name), name


# ---- the validator subprocess itself: cannot run / answers without records -------------------------------------------------------

def _stub_validator(monkeypatch, behaviour):
    """Replace ONLY the validator subprocess (python -c <driver>); every git call still runs for real."""
    import subprocess
    real = subprocess.run

    def run(args, *a, **k):
        if isinstance(args, list) and len(args) == 3 and args[0] == sys.executable and args[1] == "-c":
            return behaviour()
        return real(args, *a, **k)
    monkeypatch.setattr(subprocess, "run", run)


@pytest.mark.parametrize("exc", [OSError("no exec"), __import__("subprocess").TimeoutExpired("python", 1)])
def test_a_validator_that_cannot_be_started_or_times_out_raises_and_is_not_cached(w, runs, monkeypatch, exc):
    w.commit()

    def boom():
        raise exc
    _stub_validator(monkeypatch, boom)
    for _ in range(2):
        with pytest.raises(T.ElevatedInputError) as e:
            w.elevated(T)
        assert e.value.code == "registry_unreadable" and "could not be run" in str(e.value)
    assert len(runs) == 2 and not T._E63_E51_CACHE


def test_an_acceptance_that_carries_no_records_is_not_believed(w, runs, monkeypatch):
    w.commit()
    ok = {"ok": True, "constants": {"CITATION_PASS_REFUSED": list(T.E63_CITATION_BLOCKING),
                                    "DECLARATIONS_RELPATH": T.E63_DECLARATIONS_PATH}}

    class R:
        stdout = json.dumps(ok).encode()
        stderr = b""
    _stub_validator(monkeypatch, lambda: R())
    with pytest.raises(T.ElevatedInputError, match="returned no records") as e:
        w.elevated(T)
    assert e.value.code == "registry_unreadable" and not T._E63_E51_CACHE
