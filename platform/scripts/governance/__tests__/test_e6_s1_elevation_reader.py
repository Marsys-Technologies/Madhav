"""test_e6_s1_elevation_reader.py: E6 S1 (REGISTRY_REVISION 13): the ELEVATED reader consumes the census's earned Null lift.

Without this the census would say Null PASS and `elevated_assets` would still say "capped": two definitions. The reader (E6.3,
asset_elevation_tracker.py) takes the census file a Null PASS certificate cites (committed at the ref, hash-checked), finds the layer
head and the asset's measurements, and asks the REF'S OWN asset_census.py (loaded into a subprocess exactly as E5.1's validator is:
`_e63_ref_run`) for the census rollup of the Null cell and for `null_lift_earned`; it also requires the head's registry revision and
fingerprint to be the ref census's. A Null PASS counts ONLY on an earned lift. Everything else stays capped: a forged flag, a one-sided
lift, a pattern-only PASS, a lift on another registry revision, a convention that does not verify, a missing block, a census that
cannot be found or does not hash, a ref whose census has no lift at all. No rule is copied: the reader holds only the criterion names.

The tracker under test is `E6_3_TRACKER_UNDER_TEST` when set (the mutation harness points it at a mutated copy)."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_s1_null_convention as s1  # noqa: E402
from _e6_3_fixtures import RUN_ID, World, cert, disp, load_tracker, real_citation_patch, sha  # noqa: E402

T = load_tracker()
SD, BR = s1.SD, s1.BR
REAL_FLOOR, REAL_PINS = dict(T.E63_REQUIRED_FLOOR), dict(T.E63_REQUIRED_CRITERIA)
CENSUS_TEXT = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
ASSET, LAYER = "ga_x", "L1"
CDIR = "00_ARCHITECTURE/control/census"
CFILE = f"{CDIR}/asset_census_x.json"


@pytest.fixture(autouse=True)
def real_registry(monkeypatch):
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", REAL_FLOOR)
    monkeypatch.setattr(T, "E63_REQUIRED_CRITERIA", REAL_PINS)
    real_citation_patch(monkeypatch, T)
    T._E63_NULL_CACHE.clear()


def census_obj(ms, *, revision=None, fingerprint=None, asset=ASSET, layer=LAYER, generated=RUN_ID, extra_assets=()):
    head = dict(generated=generated, layer=layer,
                registry_revision=ac.REGISTRY_REVISION if revision is None else revision,
                registry_fingerprint=ac.registry_fingerprint() if fingerprint is None else fingerprint,
                assets=[dict(asset_id=asset, layer=layer, measurements=ms)] + list(extra_assets))
    return head


def world(tmp_path, ms, *, head=None, text=None, path=CFILE, census_src=None, sha_of=None, certs=(SD, BR), verdict="PASS", file_present=True):
    """A repo whose ledger holds `certs` (Null PASS certificates citing the census file committed with measurements `ms`)."""
    pathlib.Path(tmp_path).mkdir(parents=True, exist_ok=True)
    w = World(tmp_path, census=census_src or CENSUS_TEXT)
    body = text if text is not None else json.dumps(head if head is not None else census_obj(ms))
    if file_present:
        w.raw[path] = body
    digest = sha_of or sha(body.encode("utf-8"))
    for c in certs:
        e = ac.CRITERION_REGISTRY[c]
        w.certs.append(cert(ASSET, c, verdict, detector=e["detector"], layer=LAYER, revision=e["revision"], gate=e["gate"],
                            evidence=dict(census_run_id=RUN_ID, census_file=path, census_sha256=digest)))
    w.disps.append(disp(ASSET, "keep"))
    w.commit()
    return w


def satisfied(w, crits=(SD, BR)):
    state, _d, _g, _p = T._e63_load(w.last, str(w.repo))
    return [T._e63_satisfies(state.by_key[f"{ASSET}|gate|{c}"][-1], state, False) for c in crits]


def lifted():
    return copy.deepcopy(s1._lifted())


# ───────────────────────── the earned lift counts ─────────────────────────

def test_an_earned_null_lift_satisfies_both_null_certificates(tmp_path):
    assert satisfied(world(tmp_path, lifted())) == [True, True]


def test_the_cap_the_reader_parses_is_still_there_so_a_plain_null_pass_is_capped(tmp_path):
    w = world(tmp_path, lifted())
    state, *_ = T._e63_load(w.last, str(w.repo))
    assert state.facts.capped(SD) and state.facts.capped(BR)
    plain = {SD: dict(v="PASS", measured="x"), BR: dict(v="PASS", measured="x")}
    assert satisfied(world(tmp_path / "p", plain)) == [False, False]


# ───────────────────────── seeded defects: each stays capped ─────────────────────────

def _forge_verified(ms):
    for c in (SD, BR):
        ms[c]["null_convention"]["verified"] = False


def _forge_flag_only(ms):                       # the record says PASS and carries a bare flag, nothing behind it
    for c in (SD, BR):
        ms[c]["null_convention"] = {"verified": True}


def _one_sided(ms):                              # only one of the two Null records is lifted
    ms[BR] = dict(v="PASS", measured="x")


def _sibling_absent(ms):
    del ms[BR]


def _pattern_only(ms):                           # a clean populated table: PASS with no block at all
    for c in (SD, BR):
        ms[c].pop("null_convention")


def _convention_fails(ms):                       # the detector said FAIL: the cells are FAIL, the certificate says PASS anyway
    ms[BR] = dict(v="FAIL", measured="undeclared NULL in count_from_graha", null_convention=dict(ms[BR]["null_convention"], verified=False, v="FAIL"))
    ms[SD] = dict(ms[SD], v="PARTIAL")


def _block_convention_not_pass(ms):
    for c in (SD, BR):
        ms[c]["null_convention"]["v"] = "PARTIAL"


def _block_not_clean(ms):
    ms[SD]["null_convention"]["blank_rows_clean"] = False
    ms[BR]["null_convention"]["blank_rows_clean"] = False


def _block_no_evidence(ms):
    for c in (SD, BR):
        ms[c]["null_convention"].pop("evidence")


def _siblings_disagree(ms):
    ms[BR]["null_convention"]["table"] = "another_t"


def _inconclusive(ms):
    ms[SD]["inconclusive"] = True


def _basis(ms):
    ms[BR]["basis"] = "declaration"


DEFECTS = [_forge_verified, _forge_flag_only, _one_sided, _sibling_absent, _pattern_only, _convention_fails, _block_convention_not_pass,
           _block_not_clean, _block_no_evidence, _siblings_disagree, _inconclusive, _basis]


@pytest.mark.parametrize("defect", DEFECTS, ids=lambda f: f.__name__.strip("_"))
def test_every_seeded_defect_stays_capped(tmp_path, defect):
    ms = lifted()
    defect(ms)
    assert satisfied(world(tmp_path, ms)) == [False, False]


def test_a_missing_block_on_one_record_caps_both_certificates(tmp_path):
    ms = lifted()
    ms[SD].pop("null_convention")
    assert satisfied(world(tmp_path, ms)) == [False, False]


@pytest.mark.parametrize("what", ["revision", "fingerprint"])
def test_a_lift_on_a_registry_revision_the_ref_does_not_have_stays_capped(tmp_path, what):
    kw = dict(revision=ac.REGISTRY_REVISION - 1) if what == "revision" else dict(fingerprint="0" * 64)
    assert satisfied(world(tmp_path, lifted(), head=census_obj(lifted(), **kw))) == [False, False]


def test_a_ref_whose_census_has_no_lift_at_all_keeps_the_cap(tmp_path):
    assert "def null_lift_earned(" in CENSUS_TEXT
    old = CENSUS_TEXT.replace("def null_lift_earned(", "def null_lift_earned_renamed(")
    assert satisfied(world(tmp_path, lifted(), census_src=old)) == [False, False]


def test_a_ref_census_that_covers_other_null_checks_than_the_reader_raises_never_guesses(tmp_path):
    line = 'NULL_CHECKS = ("Null.schema_default", "Null.blank_rows")'
    assert line in CENSUS_TEXT
    other = CENSUS_TEXT.replace(line, 'NULL_CHECKS = ("Null.schema_default", "Null.blank_rows", "Null.extra")')
    w = world(tmp_path, lifted(), census_src=other)
    with pytest.raises(T.ElevatedInputError, match="disagree on which Null checks"):
        satisfied(w)


def test_a_ref_census_that_cannot_run_the_rollup_raises_or_stays_capped_never_lifts(tmp_path):
    broken = CENSUS_TEXT.replace("def null_lift_earned(crit: str, meas, all_meas) -> bool:", "def null_lift_earned(crit: str, meas, all_meas) -> bool:\n    raise RuntimeError('x')")
    assert broken != CENSUS_TEXT
    assert satisfied(world(tmp_path, lifted(), census_src=broken)) == [False, False]


# ───────────────────────── the cited census must be the one the certificate says ─────────────────────────

def test_a_certificate_citing_no_census_file_stays_capped(tmp_path):
    pathlib.Path(tmp_path).mkdir(parents=True, exist_ok=True)
    w = World(tmp_path, census=CENSUS_TEXT)
    for c in (SD, BR):
        e = ac.CRITERION_REGISTRY[c]
        w.certs.append(cert(ASSET, c, "PASS", detector=e["detector"], layer=LAYER, revision=e["revision"], gate=e["gate"]))
    w.disps.append(disp(ASSET, "keep"))
    w.commit()
    assert satisfied(w) == [False, False]


def test_a_census_file_that_is_not_at_the_ref_or_does_not_hash_stays_capped(tmp_path):
    assert satisfied(world(tmp_path / "a", lifted(), file_present=False)) == [False, False]
    assert satisfied(world(tmp_path / "b", lifted(), sha_of="0" * 64)) == [False, False]


@pytest.mark.parametrize("path", [f"{CDIR}/sub/asset_census_x.json", "00_ARCHITECTURE/control/asset_census_x.json", f"{CDIR}/asset_census_x.txt",
                                  f"{CDIR}/../census/asset_census_x.json", f"{CDIR}/", "platform/scripts/governance/asset_census_x.json", f"{CDIR}/a\\b.json"])
def test_a_census_file_outside_the_trusted_root_stays_capped(tmp_path, path):
    w = world(tmp_path, lifted(), path=path)
    assert satisfied(w) == [False, False]


def test_a_census_whose_head_run_layer_or_asset_does_not_match_stays_capped(tmp_path):
    ms = lifted()
    for i, head in enumerate((census_obj(ms, generated="2020-01-01T00:00:00+05:30"), census_obj(ms, layer="L0"), census_obj(ms, asset="ga_other"))):
        assert satisfied(world(tmp_path / str(i), ms, head=head)) == [False, False], i
    dup = census_obj(ms, extra_assets=[dict(asset_id=ASSET, layer=LAYER, measurements=ms)])
    assert satisfied(world(tmp_path / "dup", ms, head=dup)) == [False, False]            # two records of one asset: ambiguous, never lifted


def test_two_layer_heads_with_the_same_run_and_layer_are_ambiguous_and_stay_capped(tmp_path):
    ms = lifted()
    body = json.dumps({"A": census_obj(ms), "B": census_obj(ms), "rollup": {"cells": []}})
    assert satisfied(world(tmp_path, ms, text=body)) == [False, False]


def test_a_census_that_is_not_strict_json_stays_capped(tmp_path):
    body = json.dumps(census_obj(lifted()))
    dup = "{" + body[1:-1] + ', "generated": ' + json.dumps(RUN_ID) + "}"                       # a duplicate key with the SAME value: only a strict reader refuses it
    assert json.loads(dup)["generated"] == RUN_ID
    assert satisfied(world(tmp_path / "a", lifted(), text=dup)) == [False, False]
    assert satisfied(world(tmp_path / "b", lifted(), text="not json")) == [False, False]
    assert satisfied(world(tmp_path / "c", lifted(), text="[]")) == [False, False]


def test_the_multi_layer_census_file_shape_is_read_too(tmp_path):
    ms = lifted()
    decoy = census_obj(ms, layer="L9", generated="2020-01-01T00:00:00+05:30")
    body = json.dumps({"L9": decoy, LAYER: census_obj(ms), "rollup": {"cells": []}})
    assert satisfied(world(tmp_path, ms, text=body)) == [True, True]


def test_a_certificate_that_is_not_pass_or_not_a_null_check_never_uses_the_lift(tmp_path):
    ms = lifted()
    w = world(tmp_path, ms)
    state, *_ = T._e63_load(w.last, str(w.repo))
    rec = dict(state.by_key[f"{ASSET}|gate|{SD}"][-1])
    assert T._e63_null_lift_earned(str(w.repo), w.last, dict(rec, verdict="PARTIAL"), CENSUS_TEXT.encode()) is False
    # a non-Null capped criterion (Narr.fidelity_test) is never lifted by a Null block
    ms2 = lifted()
    ms2["Narr.fidelity_test"] = dict(v="PASS", measured="x", null_convention=copy.deepcopy(ms2[SD]["null_convention"]))
    (tmp_path / "n").mkdir()
    w2 = World(tmp_path / "n", census=CENSUS_TEXT)
    body = json.dumps(census_obj(ms2))
    w2.raw[CFILE] = body
    e = ac.CRITERION_REGISTRY["Narr.fidelity_test"]
    w2.certs.append(cert(ASSET, "Narr.fidelity_test", "PASS", detector=e["detector"], layer=LAYER, revision=e["revision"], gate="Narr",
                         evidence=dict(census_run_id=RUN_ID, census_file=CFILE, census_sha256=sha(body.encode()))))
    w2.disps.append(disp(ASSET, "keep"))
    w2.commit()
    assert satisfied(w2, ("Narr.fidelity_test",)) == [False]


def test_every_conjunct_of_the_refs_answer_is_required_even_where_the_refs_own_rollup_makes_it_redundant(tmp_path, monkeypatch):
    """The ref's rollup cannot read a Null check PASS without the lift, so `earned`, `verified`, `check` and `cell` normally move together; the
    reader still requires each, so a ref whose census answers inconsistently never lifts (defence in depth, tested with a stubbed ref answer)."""
    w = world(tmp_path, lifted())
    state, *_ = T._e63_load(w.last, str(w.repo))
    rec = state.by_key[f"{ASSET}|gate|{SD}"][-1]
    head = census_obj(lifted())
    good = dict(has=True, constants={"NULL_CHECKS": list(T.E63_NULL_CHECKS)}, revision=head["registry_revision"], fingerprint=head["registry_fingerprint"],
                earned=True, verified=True, check="PASS", cell="PASS")

    def ask(answer):
        T._E63_NULL_CACHE.clear()
        monkeypatch.setattr(T, "_e63_ref_run", lambda *a, **k: dict(answer))
        return T._e63_null_lift_earned(str(w.repo), w.last, rec, CENSUS_TEXT.encode())
    assert ask(good) is True
    for key, bad in (("earned", False), ("verified", False), ("check", "PARTIAL"), ("cell", "PARTIAL"), ("revision", head["registry_revision"] + 1),
                     ("fingerprint", "0" * 64)):
        assert ask(dict(good, **{key: bad})) is False, key
    assert ask(dict(good, error="ValueError: x")) is False
    assert ask(dict(good, has=False)) is False
    with pytest.raises(T.ElevatedInputError):
        ask(dict(good, constants={"NULL_CHECKS": ["Null.schema_default"]}))


# ───────────────────────── the shared ref runner ─────────────────────────

def test_the_ref_runner_runs_the_drivers_code_against_the_refs_own_files_and_demands_an_answer():
    out = T._e63_ref_run("a" * 40, {"data.txt": b"hello"}, "import json, sys\nprint(json.dumps({'a': open('data.txt').read(), 'in': sys.stdin.read()}))", b"IN", "the thing", ("a",))
    assert out == {"a": "hello", "in": "IN"}                                         # cwd holds the ref's files; stdin is the request
    noisy = T._e63_ref_run("a" * 40, {}, "import json\nprint('noise from an import')\nprint(json.dumps({'a': 1}))", b"", "the thing", ("a",))
    assert noisy == {"a": 1}                                                          # the answer is the LAST stdout line
    for driver in ("print('not json')", "print('{}')", "print('[]')", "", "raise SystemExit(3)"):
        with pytest.raises(T.ElevatedInputError, match="the thing at aaaaaaaaaaaa did not answer"):
            T._e63_ref_run("a" * 40, {}, driver, b"", "the thing", ("a",))


def _driver_answer(ms, criterion=SD):
    req = json.dumps({"layer": LAYER, "criterion": criterion, "measurements": ms}, sort_keys=True).encode()
    return T._e63_ref_run("a" * 40, {"asset_census.py": CENSUS_TEXT.encode()}, T._E63_NULL_DRIVER, req, "the census rollup's Null lift", ("has",))


def test_the_null_driver_reports_the_refs_own_rollup_and_lift_and_nothing_else():
    ok = _driver_answer(lifted())
    assert ok["has"] is True and ok["constants"] == {"NULL_CHECKS": list(T.E63_NULL_CHECKS)} and ok["revision"] == ac.REGISTRY_REVISION
    assert ok["fingerprint"] == ac.registry_fingerprint() and ok["earned"] is True and ok["verified"] is True and ok["check"] == "PASS" and ok["cell"] == "PASS"
    one = lifted()
    _one_sided(one)
    bad = _driver_answer(one)
    assert bad["earned"] is False and bad["verified"] is False and bad["check"] == "PARTIAL" and bad["cell"] != "PASS" and "error" not in bad
    plain = {SD: dict(v="PASS", measured="x"), BR: dict(v="PASS", measured="x")}
    assert _driver_answer(plain)["cell"] == "PARTIAL"
    assert _driver_answer({SD: dict(v="NOT_A_VERDICT")})["error"]                    # a measurement the rollup refuses is reported, never a lift
    only_null = _driver_answer(dict(lifted(), **{"Idem.pattern": dict(v="NOT_A_VERDICT")}))
    assert only_null["cell"] == "PASS"                                                # only the Null checks are rolled up


def test_the_ref_runner_does_not_inherit_pythonpath(tmp_path, monkeypatch):
    (tmp_path / "evil.py").write_text("X = 'leaked'\n", encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    with pytest.raises(T.ElevatedInputError, match="did not answer"):
        T._e63_ref_run("a" * 40, {}, "import evil\nprint('{}')", b"", "the thing", ())


# ───────────────────────── the parity: the census rollup and the reader give ONE answer ─────────────────────────

def _oracle(ms, revision=None):
    """The census's own answer for these measurements: the Null cell reads PASS on a registry stamp that is the current one (what E5.1 enforces at
    certificate time and the reader re-checks)."""
    stamped_current = revision is None or revision == ac.REGISTRY_REVISION
    return ac.rollup_asset(LAYER, {c: m for c, m in ms.items() if c in (SD, BR)})["Null"]["v"] == "PASS" and stamped_current


def _variants():
    out = [("earned", lambda ms: None, None)]
    mutators = [
        ("forge_verified_sd", lambda ms: ms[SD]["null_convention"].update(verified=False)),
        ("forge_verified_br", lambda ms: ms[BR]["null_convention"].update(verified=False)),
        ("block_removed_sd", lambda ms: ms[SD].pop("null_convention")),
        ("block_removed_br", lambda ms: ms[BR].pop("null_convention")),
        ("sibling_removed", lambda ms: ms.pop(BR)),
        ("sd_partial", lambda ms: ms[SD].update(v=PARTIAL)),
        ("br_fail", lambda ms: ms[BR].update(v="FAIL")),
        ("sd_nodet", lambda ms: ms[SD].update(v="NO_DETECTOR")),
        ("conv_v_partial", lambda ms: ms[SD]["null_convention"].update(v=PARTIAL)),
        ("declared_false", lambda ms: ms[BR]["null_convention"].update(declared=False)),
        ("no_why", lambda ms: ms[SD]["null_convention"].pop("why")),
        ("no_evidence", lambda ms: ms[BR]["null_convention"].pop("evidence")),
        ("no_table", lambda ms: ms[SD]["null_convention"].pop("table")),
        ("empty_columns", lambda ms: ms[BR]["null_convention"].update(columns=[])),
        ("columns_differ", lambda ms: ms[BR]["null_convention"].update(columns=["other"])),
        ("table_differs", lambda ms: ms[SD]["null_convention"].update(table="other_t")),
        ("sd_not_clean", lambda ms: ms[SD]["null_convention"].update(schema_default_clean=False)),
        ("br_not_clean", lambda ms: ms[BR]["null_convention"].update(blank_rows_clean=False)),
        ("inconclusive_sd", lambda ms: ms[SD].update(inconclusive=True)),
        ("basis_br", lambda ms: ms[BR].update(basis="declaration")),
        ("flag_only", lambda ms: ms[SD].update(null_convention={"verified": True})),
        ("pattern_only", lambda ms: [ms[c].pop("null_convention") for c in (SD, BR)]),
        ("extra_keys_harmless", lambda ms: ms[SD].update(note="a harmless extra key")),
    ]
    for name, f in mutators:
        out.append((name, f, None))
    out.append(("stale_revision", lambda ms: None, ac.REGISTRY_REVISION - 1))
    return out


PARTIAL = ac.PARTIAL


@pytest.mark.parametrize("name, mutate, revision", _variants(), ids=[v[0] for v in _variants()])
def test_parity_the_census_rollup_and_the_reader_give_the_same_null_answer(tmp_path, name, mutate, revision):
    ms = lifted()
    mutate(ms)
    census_says = _oracle(ms, revision)
    head = census_obj(ms, revision=revision)
    reader_says = all(satisfied(world(tmp_path, ms, head=head, certs=tuple(c for c in (SD, BR)))))
    assert reader_says == census_says, (name, census_says, reader_says)
    if name == "earned":
        assert census_says is True


def test_parity_is_not_vacuous_some_variants_pass_and_most_do_not():
    verdicts = []
    for name, mutate, revision in _variants():
        ms = lifted()
        mutate(ms)
        verdicts.append(_oracle(ms, revision))
    assert verdicts.count(True) >= 2 and verdicts.count(False) >= 20, verdicts


# ───────────────────────── end to end: ELEVATED on the real registry ─────────────────────────

def _real_asset_world(tmp_path, null_ms):
    """ga_x certified on every criterion the REAL L1 registry requires: the Null checks as Null PASS certificates citing a census file holding `null_ms`,
    every other criterion the rollup would not honour as a declared N/A (as in test_e6_3_elevated_exact), the rest PASS."""
    layer = LAYER
    req = {c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] in ac.CELL_GATES and layer in e["layers"]}
    null_c = {SD, BR}
    blocked = {c for c in req if ac._check_contribution(c, layer, {"v": "PASS"}, None)["v"] != "PASS"} - null_c
    rules = {f"{c}#measured:x-cause": "N-test" for c in blocked}
    src = _na_rules_replaced(CENSUS_TEXT, dict(ac.NA_RULE_DECISIONS, **rules))
    src += ("\n\nfor _c in %r:      # the test's own N/A cause, registered so the ref's census accepts its rules\n"
            "    NA_CAUSES[_c] = tuple(NA_CAUSES.get(_c, ())) + ('x-cause',)\n") % (sorted(blocked),)
    pathlib.Path(tmp_path).mkdir(parents=True, exist_ok=True)
    w = World(tmp_path, census=src)
    rev, fp = _stamp_of(src, tmp_path)
    body = json.dumps(census_obj(null_ms, revision=rev, fingerprint=fp))
    w.raw[CFILE] = body
    ev = dict(census_run_id=RUN_ID, census_file=CFILE, census_sha256=sha(body.encode()))
    for c in sorted(req):
        e = ac.CRITERION_REGISTRY[c]
        if c in blocked:
            w.certs.append(cert(ASSET, c, "N/A", detector=e["detector"], layer=layer, revision=e["revision"], gate=e["gate"],
                                na=dict(rule_id=f"{c}#measured:x-cause", decision_id="N-test", basis="measured_cause", cause="x-cause", facts=None)))
        else:
            w.certs.append(cert(ASSET, c, "PASS", detector=e["detector"], layer=layer, revision=e["revision"], gate=e["gate"],
                                citation_state="sourced" if c in ("Carr.D1", "Ldgr.source_presence") else ..., **(dict(evidence=ev) if c in null_c else {})))
    w.disps.append(disp(ASSET, "keep"))
    w.commit()
    return w


def _stamp_of(src, tmp_path):
    """(REGISTRY_REVISION, registry_fingerprint) of the census source `src` (the ref's own stamp, which the head of a census run by it carries)."""
    import subprocess
    d = pathlib.Path(tmp_path) / "stamp"
    d.mkdir()
    (d / "asset_census.py").write_text(src, encoding="utf-8")
    r = subprocess.run([sys.executable, "-c", "import json, asset_census as a; print(json.dumps([a.REGISTRY_REVISION, a.registry_fingerprint()]))"],
                       cwd=str(d), capture_output=True, text=True, timeout=60)
    return tuple(json.loads(r.stdout.strip().splitlines()[-1]))


def _na_rules_replaced(src, merged):
    import ast
    tree = ast.parse(src)
    node = next(n for n in tree.body if (isinstance(n, ast.AnnAssign) and getattr(n.target, "id", None) == "NA_RULE_DECISIONS")
                or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) == "NA_RULE_DECISIONS"))
    lines = src.split("\n")
    lines[node.lineno - 1:node.end_lineno] = [f"NA_RULE_DECISIONS: dict[str, str] = {merged!r}"]
    return "\n".join(lines)


def test_end_to_end_an_asset_is_elevated_exactly_when_its_null_lift_is_earned(tmp_path):
    w = _real_asset_world(tmp_path / "ok", lifted())
    assert ASSET in w.elevated(T)
    for i, defect in enumerate((_forge_verified, _one_sided, _pattern_only, _convention_fails)):
        ms = lifted()
        defect(ms)
        w2 = _real_asset_world(tmp_path / f"d{i}", ms)
        assert ASSET not in w2.elevated(T), defect.__name__
