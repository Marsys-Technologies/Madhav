"""test_n317_evaluation_copy.py: SS N-310/N-313/N-317 a census of a RESTORED copy states exactly which data it measured, and is refused when it is actually production.

From N-310 the censuses run against a restored copy of production's backup. The reading says so: `SUVARNA_EVAL_COPY` ({backup_id, backup_time, instance, source_instance}) is validated and stamped into every
layer head as `evaluation_copy`; census_postprocess carries it into the lists ("full census of an evaluation copy of production, backup <id> taken <time>"). A port number is a weak proof of which database you
are on, so a declared evaluation copy is REFUSED when the connected server's identity is unreadable or EQUALS a recorded production identity (production_db_identities.json).

Offline: the identity is faked; the postprocess side runs on the synthetic stamped census files of test_e5_7_census_postprocess.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import test_e5_7_census_postprocess as base  # noqa: E402  (world / run / rewrite / refused)

cp, world, run, rewrite, refused = base.cp, base.world, base.run, base.rewrite, base.refused

PROD = "dc44e6454be49742e4317b414a460f2f760c8470e6c05a7586e2eea8d23c1731"       # the identity the six full production censuses stamped
COPY = "a" * 64
EC = {"backup_id": "1791559465537", "backup_time": "2026-10-09T15:24:00Z", "instance": "amjis-ri02-validation-c720f1832", "source_instance": "amjis-postgres"}
RAW = json.dumps(EC)


def ident(sid=COPY, db="amjis"):
    return dict(schema=ac.DB_IDENTITY_SCHEMA, database=db, system_id_sha256=sid)


# ───────────────────────── the declaration ─────────────────────────

def test_no_declaration_means_no_stamp_and_no_check(monkeypatch):
    monkeypatch.delenv(ac.EVAL_COPY_ENV, raising=False)
    assert ac.evaluation_copy_declared() is None and ac.evaluation_copy_stamp(ident(PROD)) is None          # even production's own identity passes untouched when nothing is declared
    monkeypatch.setenv(ac.EVAL_COPY_ENV, "")
    assert ac.evaluation_copy_declared() is None


def test_a_wellformed_declaration_is_returned_in_field_order(monkeypatch):
    monkeypatch.setenv(ac.EVAL_COPY_ENV, json.dumps(dict(reversed(list(EC.items())))))
    assert list(ac.evaluation_copy_declared()) == list(ac.EVAL_COPY_FIELDS) and ac.evaluation_copy_declared() == EC
    assert ac.evaluation_copy_stamp(ident(), raw=RAW) == dict(evaluation_copy=EC)


@pytest.mark.parametrize("bad", [
    "not json", "[]", "null", '"x"', "{}",
    json.dumps({**EC, "extra": "x"}),                                       # an extra key
    json.dumps({k: v for k, v in EC.items() if k != "backup_id"}),          # a missing key
    json.dumps({**EC, "backup_id": ""}), json.dumps({**EC, "backup_id": "id with space"}), json.dumps({**EC, "backup_id": "x;rm"}),
    json.dumps({**EC, "backup_id": 1791559465537}),                         # not a string
    json.dumps({**EC, "backup_id": "a" * 81}),
    json.dumps({**EC, "backup_time": "2026-10-09"}), json.dumps({**EC, "backup_time": "2026-10-09 15:24:00"}),
    json.dumps({**EC, "backup_time": "2026-10-09T15:24:00+05:30"}),         # not UTC
    json.dumps({**EC, "backup_time": "yesterday"}),
    json.dumps({**EC, "instance": "amjis-postgres"}),                       # the copy is the source
    json.dumps({**EC, "source_instance": ""}),
])
def test_forgery_a_malformed_declaration_is_refused(bad):
    with pytest.raises(ac.EvalCopyRefused):
        ac.evaluation_copy_declared(bad)


# ───────────────────────── the identity check: the copy is NOT production ─────────────────────────

def test_the_recorded_production_identity_is_the_one_the_full_censuses_stamped():
    assert PROD in ac.known_production_identities()
    d = json.loads(ac.PRODUCTION_IDENTITIES_PATH.read_text(encoding="utf-8"))
    assert d["schema"] == "nikasha_known_production_identities/1" and [i["database"] for i in d["identities"]] == ["amjis"]


def test_a_server_whose_identity_equals_production_is_refused_whatever_the_port():
    with pytest.raises(ac.EvalCopyRefused) as ei:
        ac.evaluation_copy_stamp(ident(PROD), raw=RAW)
    assert "EQUALS the recorded production identity" in str(ei.value)


@pytest.mark.parametrize("unreadable", [
    None, {}, dict(schema="x", database="amjis", system_id_sha256=None, unavailable="the system identifier could not be read by this role (pg_control_system())"),
    dict(system_id_sha256="not-a-hash"), dict(system_id_sha256=PROD.upper()), dict(system_id_sha256=PROD[:-1]),
])
def test_an_identity_that_cannot_be_read_is_refused_never_assumed_to_be_a_copy(unreadable):
    with pytest.raises(ac.EvalCopyRefused) as ei:
        ac.evaluation_copy_stamp(unreadable, raw=RAW)
    assert "could not be read" in str(ei.value)


def test_a_missing_or_malformed_production_record_refuses_rather_than_skipping_the_check(tmp_path):
    with pytest.raises(ac.EvalCopyRefused) as ei:
        ac.evaluation_copy_stamp(ident(), raw=RAW, identities_path=tmp_path / "nope.json")
    assert "cannot be made" in str(ei.value)
    for body in ("not json", "{}", json.dumps({"identities": []}), json.dumps({"identities": [{"system_id_sha256": "short"}]}), json.dumps({"identities": [{}]})):
        p = tmp_path / "ids.json"
        p.write_text(body, encoding="utf-8")
        with pytest.raises(ac.EvalCopyRefused):
            ac.evaluation_copy_stamp(ident(), raw=RAW, identities_path=p)


def test_the_stamp_is_in_the_census_head_only_when_declared(monkeypatch):
    monkeypatch.setattr(ac, "_db_identity", lambda: dict(db_identity=ident()))
    monkeypatch.delenv(ac.EVAL_COPY_ENV, raising=False)
    assert "evaluation_copy" not in ac.census_stamp()
    monkeypatch.setenv(ac.EVAL_COPY_ENV, RAW)
    st = ac.census_stamp()
    assert st["evaluation_copy"] == EC and st["db_identity"]["system_id_sha256"] == COPY
    monkeypatch.setattr(ac, "_db_identity", lambda: dict(db_identity=ident(PROD)))
    with pytest.raises(ac.EvalCopyRefused):
        ac.census_stamp()


def test_main_refuses_with_its_own_exit_code_and_writes_nothing(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ac, "_db_identity", lambda: dict(db_identity=ident(PROD)))
    monkeypatch.setenv(ac.EVAL_COPY_ENV, RAW)
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--out", str(tmp_path / "x.json")])
    rc = ac.main()
    assert rc == ac.EXIT_EVAL_COPY_REFUSED == 13 and not (tmp_path / "x.json").exists()
    assert "evaluation copy refused" in capsys.readouterr().err


# ───────────────────────── census_postprocess carries it into the lists ─────────────────────────

def stamp_all(paths, ec=EC):
    for p in paths:
        rewrite(p, lambda d: _head(d).__setitem__("evaluation_copy", ec))


def _head(d):
    return d[next(k for k in d if k.startswith("L"))] if any(k.startswith("L") for k in d) else d


def test_a_production_census_reads_exactly_as_before(tmp_path):
    rc, out = run(world(tmp_path), tmp_path)
    assert rc == 0
    for name in ("CERTIFIED_LIST.md", "FIX_LIST.md", "BLOCKERS_BY_CLASS.md"):
        assert "evaluation copy" not in (out / name).read_text(encoding="utf-8")
    assert "evaluation_copy" not in json.loads((out / "CERTIFIED_LIST.json").read_text()) and "evaluation_copy" not in json.loads((out / "BLOCKERS_BY_CLASS.json").read_text())


def test_an_evaluation_copy_census_says_so_in_every_list(tmp_path):
    paths = world(tmp_path)
    stamp_all(paths)
    rc, out = run(paths, tmp_path)
    assert rc == 0
    sentence = "full census of an evaluation copy of production, backup 1791559465537 taken 2026-10-09T15:24:00Z"
    for name in ("CERTIFIED_LIST.md", "FIX_LIST.md", "BLOCKERS_BY_CLASS.md"):
        text = (out / name).read_text(encoding="utf-8")
        assert sentence in text and "Not a census of the live production database" in text, name
    for name in ("CERTIFIED_LIST.json", "FIX_LIST.json", "BLOCKERS_BY_CLASS.json"):
        assert json.loads((out / name).read_text())["evaluation_copy"] == EC, name


def test_forgery_one_layer_without_the_stamp_is_refused(tmp_path, capsys):
    paths = world(tmp_path)
    stamp_all(paths[:2])                                                       # L2 declares nothing: a mixed reading must not be certified as one
    refused(capsys, paths, tmp_path, "different evaluation_copy stamps")


def test_forgery_layers_naming_different_backups_are_refused(tmp_path, capsys):
    paths = world(tmp_path)
    stamp_all(paths[:2])
    stamp_all(paths[2:], dict(EC, backup_id="1791559465538"))
    refused(capsys, paths, tmp_path, "different evaluation_copy stamps")


@pytest.mark.parametrize("bad", [{"backup_id": "x"}, dict(EC, extra="y"), dict(EC, backup_id=""), dict(EC, backup_time=5), "backup 1", ["a"]])
def test_forgery_a_malformed_stamp_in_a_census_file_is_refused(tmp_path, capsys, bad):
    paths = world(tmp_path)
    stamp_all(paths, bad)
    refused(capsys, paths, tmp_path, "evaluation_copy is not exactly")


def test_the_scoped_refusal_no_longer_says_production():
    src = pathlib.Path(cp.__file__).read_text(encoding="utf-8")
    assert "full production censuses" not in src and "full censuses of one database" in src
