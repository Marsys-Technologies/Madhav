"""test_n317_evaluation_copy.py: SS N-310/N-313/N-317/N-327 a census of a RESTORED copy states exactly which data it measured, and the copy is proven POSITIVELY by a marker the restore writes.

A physical restore of production KEEPS its system identifier (REGISTERED_DB_IDENTITIES.json says so), so the database identity cannot tell a copy from production; the first design ("refuse when the identity
equals production") would have refused every legitimate copy and let an unstamped copy census read as production (Kāla's review of #3372). The proof is now a one-row table `evalcopy.marker` the restore
writes into the copy (production never has it):
  * every census head carries `eval_copy_probe` (the census LOOKED for the marker; absent schema = "absent", an unreadable lookup = `checked: false`);
  * SUVARNA_EVAL_COPY declares the run: the marker must be present and EQUAL the declaration (the stated backup is VERIFIED), else the census does not run; a marker WITHOUT a declaration refuses;
  * census_postprocess refuses a census with no probe unless --allow-legacy-census ('legacy census: production-ness assumed'), requires one stamp across layers and overlays, validates the stamp values
    (they are printed into the certificate) and writes "full census of an evaluation copy of production, backup <id> taken <time>".
The identity stays INFORMATION only (`identity_in_production_registry`).

Offline for the logic (the database is faked); one real-SQL test on a disposable PostgreSQL for the marker lookup.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import test_e5_7_census_postprocess as base  # noqa: E402  (world / run / rewrite / refused)
import test_n268_bar as n268  # noqa: E402  (scoped overlay fixtures)
from _disposable_pg import disposable_pg  # noqa: E402,F401

cp, world, run, rewrite, refused = base.cp, base.world, base.run, base.rewrite, base.refused

PROD = "dc44e6454be49742e4317b414a460f2f760c8470e6c05a7586e2eea8d23c1731"       # the identity the registry records for production (and the six full production censuses stamped)
COPY = "a" * 64
EC = {"backup_id": "1791559465537", "backup_time": "2026-10-09T15:24:00Z", "instance": "amjis-ri02-validation-c720f1832", "source_instance": "amjis-postgres"}
RAW = json.dumps(EC)
PROBE_ABSENT = dict(checked=True, marker_present=False)
PROBE_OK = dict(checked=True, marker_present=True, marker=EC)


@pytest.fixture(autouse=True)
def _declared_env_is_explicit(monkeypatch):
    monkeypatch.delenv(ac.EVAL_COPY_ENV, raising=False)


def ident(sid=COPY, db="amjis"):
    return dict(schema=ac.DB_IDENTITY_SCHEMA, database=db, system_id_sha256=sid)


# ───────────────────────── the declaration ─────────────────────────

def test_no_declaration_means_none(monkeypatch):
    assert ac.evaluation_copy_declared() is None
    monkeypatch.setenv(ac.EVAL_COPY_ENV, "")
    assert ac.evaluation_copy_declared() is None


def test_a_wellformed_declaration_is_returned_in_field_order(monkeypatch):
    monkeypatch.setenv(ac.EVAL_COPY_ENV, json.dumps(dict(reversed(list(EC.items())))))
    assert list(ac.evaluation_copy_declared()) == list(ac.EVAL_COPY_FIELDS) and ac.evaluation_copy_declared() == EC


@pytest.mark.parametrize("bad", [
    "not json", "[]", "null", '"x"', "{}",
    json.dumps({**EC, "extra": "x"}), json.dumps({k: v for k, v in EC.items() if k != "backup_id"}),
    json.dumps({**EC, "backup_id": ""}), json.dumps({**EC, "backup_id": "id with space"}), json.dumps({**EC, "backup_id": "x;rm"}), json.dumps({**EC, "backup_id": "a\nb"}),
    json.dumps({**EC, "backup_id": 1791559465537}), json.dumps({**EC, "backup_id": "a" * 81}),
    json.dumps({**EC, "backup_time": "2026-10-09"}), json.dumps({**EC, "backup_time": "2026-10-09 15:24:00"}), json.dumps({**EC, "backup_time": "2026-10-09T15:24:00+05:30"}), json.dumps({**EC, "backup_time": "yesterday"}),
    json.dumps({**EC, "instance": "amjis-postgres"}), json.dumps({**EC, "source_instance": ""}),
    '{"backup_id": "1", "backup_id": "2", "backup_time": "2026-10-09T15:24:00Z", "instance": "a", "source_instance": "b"}',          # a repeated key (json.loads would keep the last)
])
def test_forgery_a_malformed_declaration_is_refused(bad):
    with pytest.raises(ac.EvalCopyRefused):
        ac.evaluation_copy_declared(bad)


# ───────────────────────── the identity registry: ONE source, information only ─────────────────────────

def test_production_identity_is_read_from_the_existing_registry_and_there_is_no_second_file():
    assert PROD in ac.known_production_identities()
    assert ac.REGISTERED_IDENTITIES_PATH == ac.CTRL / "REGISTERED_DB_IDENTITIES.json" and ac.REGISTERED_IDENTITIES_PATH.exists()
    assert not (pathlib.Path(ac.__file__).resolve().parent / "production_db_identities.json").exists()          # no duplicate registry (a GA.1-class disagreement)


def _registry(tmp_path, body):
    p = tmp_path / "REGISTERED_DB_IDENTITIES.json"
    p.write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
    return p


@pytest.mark.parametrize("body", [
    "not json", "{}", json.dumps({"schema": "x", "entries": []}),
    json.dumps({"schema": "nikasha_registered_db_identities/1", "entries": []}),
    json.dumps({"schema": "nikasha_registered_db_identities/1", "entries": [{"role": "production", "system_id_sha256": "short"}]}),
    json.dumps({"schema": "nikasha_registered_db_identities/1", "entries": [{"role": "replica", "system_id_sha256": PROD}]}),           # only role production counts
    '{"schema": "nikasha_registered_db_identities/1", "entries": [{"role": "production", "system_id_sha256": "' + PROD + '"}], "entries": []}',      # a repeated key would drop production
])
def test_a_missing_malformed_or_key_repeating_registry_refuses_rather_than_skipping(tmp_path, body):
    with pytest.raises(ac.EvalCopyRefused):
        ac.known_production_identities(_registry(tmp_path, body))
    with pytest.raises(ac.EvalCopyRefused):
        ac.known_production_identities(tmp_path / "missing.json")


def test_the_identity_equal_to_production_is_NOT_a_refusal_it_is_information_only():
    """SS N-327 withdrew 'refuse if the identity equals production': a physical restore keeps it, so that rule would refuse every legitimate copy."""
    out = ac.evaluation_copy_stamp(ident(PROD), PROBE_OK, raw=RAW)
    assert out["evaluation_copy"] == EC and out["eval_copy_probe"]["identity_in_production_registry"] is True
    out = ac.evaluation_copy_stamp(ident(COPY), PROBE_OK, raw=RAW)
    assert out["eval_copy_probe"]["identity_in_production_registry"] is False
    assert ac.evaluation_copy_stamp(None, PROBE_OK, raw=RAW)["eval_copy_probe"]["identity_in_production_registry"] is None


# ───────────────────────── the marker proof ─────────────────────────

def test_declared_and_the_marker_equals_the_declaration_stamps_both():
    out = ac.evaluation_copy_stamp(ident(), PROBE_OK, raw=RAW)
    assert out["evaluation_copy"] == EC and out["eval_copy_probe"]["marker"] == EC and out["eval_copy_probe"]["marker_present"] is True


@pytest.mark.parametrize("probe, needle", [
    (PROBE_ABSENT, "not proven to be an evaluation copy"),
    (dict(checked=False, reason="the marker could not be looked up"), "could not be checked"),
    (dict(checked=True, marker_present=True, marker=None, problem="must hold exactly one row (it holds 2)"), "malformed"),
    (dict(checked=True, marker_present=True, marker=dict(EC, backup_id="1791559465538")), "does not equal the declaration"),
    (dict(checked=True, marker_present=True, marker=dict(EC, backup_time="2026-10-09T15:25:00Z")), "does not equal the declaration"),
    (dict(checked=True, marker_present=True, marker=dict(EC, instance="amjis-other")), "does not equal the declaration"),
    (dict(checked=True, marker_present=True, marker=dict(EC, source_instance="amjis-other")), "does not equal the declaration"),
    (None, "could not be checked"),
])
def test_forgery_a_declared_run_without_a_matching_marker_is_refused(probe, needle):
    with pytest.raises(ac.EvalCopyRefused) as ei:
        ac.evaluation_copy_stamp(ident(), probe, raw=RAW)
    assert needle in str(ei.value)


def test_a_marker_without_a_declaration_is_refused_a_copy_that_forgot_to_say_so():
    with pytest.raises(ac.EvalCopyRefused) as ei:
        ac.evaluation_copy_stamp(ident(), PROBE_OK, raw="")
    assert "run declares none" in str(ei.value)


def test_undeclared_without_a_marker_is_just_the_probe_and_an_unchecked_probe_does_not_refuse_an_undeclared_run():
    assert ac.evaluation_copy_stamp(ident(), PROBE_ABSENT, raw="")["eval_copy_probe"]["marker_present"] is False
    out = ac.evaluation_copy_stamp(ident(), dict(checked=False, reason="x"), raw="")
    assert "evaluation_copy" not in out and out["eval_copy_probe"]["checked"] is False


class FakeDb:
    def __init__(self, reg="evalcopy.marker", rows=None, reg_error=None, read_error=None):
        self.reg, self.rows, self.reg_error, self.read_error, self.asked = reg, rows, reg_error, read_error, []

    def scalar(self, sql, *a, **k):
        self.asked.append(sql)
        if self.reg_error:
            raise self.reg_error
        return self.reg

    def psql(self, sql, *a, **k):
        self.asked.append(sql)
        if self.read_error:
            raise self.read_error
        return self.rows


def _lookup(monkeypatch, **kw):
    db = FakeDb(**kw)
    monkeypatch.setattr(ac, "scalar", db.scalar)
    monkeypatch.setattr(ac, "psql", db.psql)
    return ac.read_eval_copy_marker(), db


def test_lookup_an_absent_marker_is_checked_and_absent(monkeypatch):
    for reg in ("", None):
        got, db = _lookup(monkeypatch, reg=reg)
        assert got == PROBE_ABSENT and len(db.asked) == 1 and "to_regclass('evalcopy.marker')" in db.asked[0]                  # an absent schema is NULL, not an error


def test_lookup_a_wellformed_single_row_is_the_marker(monkeypatch):
    got, db = _lookup(monkeypatch, rows=[list(EC.values())])
    assert got == PROBE_OK and all(q.lstrip().upper().startswith("SELECT") for q in db.asked)                              # read-only


@pytest.mark.parametrize("rows", [[], [list(EC.values())] * 2, [["only", "three", "cols"]], [["a\nb", EC["backup_time"], EC["instance"], EC["source_instance"]]],
                                  [[EC["backup_id"], "2026-10-09", EC["instance"], EC["source_instance"]]]])
def test_lookup_a_malformed_marker_is_present_but_has_no_marker_value(monkeypatch, rows):
    got, _ = _lookup(monkeypatch, rows=rows)
    assert got["checked"] is True and got["marker_present"] is True and got["marker"] is None and got["problem"]


def test_lookup_a_failed_read_is_never_guessed(monkeypatch):
    got, _ = _lookup(monkeypatch, reg_error=ac.Unknown("connection refused"))
    assert got["checked"] is False and "could not be looked up" in got["reason"]
    got, _ = _lookup(monkeypatch, read_error=ac.Unknown("permission denied for schema evalcopy"))
    assert got["checked"] is False and "could not be read" in got["reason"]


@pytest.fixture
def clean_evalcopy(disposable_pg):
    """The disposable cluster is shared by the session: every real-SQL test here starts, and ends, without an evalcopy schema."""
    disposable_pg.psql("DROP SCHEMA IF EXISTS evalcopy CASCADE")
    yield disposable_pg
    disposable_pg.psql("DROP SCHEMA IF EXISTS evalcopy CASCADE")


def test_REAL_SQL_the_marker_lookup_on_a_disposable_postgres(monkeypatch, clean_evalcopy):
    from _disposable_pg import point_psql_at
    disposable_pg = clean_evalcopy
    point_psql_at(disposable_pg, monkeypatch)
    assert ac.read_eval_copy_marker() == PROBE_ABSENT                                                                          # no evalcopy schema at all: absent, no error
    disposable_pg.psql("CREATE SCHEMA evalcopy")
    assert ac.read_eval_copy_marker() == PROBE_ABSENT                                                                          # the schema alone is not a marker
    disposable_pg.psql("CREATE TABLE evalcopy.marker (backup_id text, backup_time text, instance text, source_instance text)")
    got = ac.read_eval_copy_marker()
    assert got["marker_present"] is True and got["marker"] is None and "exactly one row" in got["problem"]                    # an empty table is malformed
    disposable_pg.psql("INSERT INTO evalcopy.marker VALUES ('1791559465537', '2026-10-09T15:24:00Z', 'amjis-ri02-validation-c720f1832', 'amjis-postgres')")
    assert ac.read_eval_copy_marker() == PROBE_OK
    disposable_pg.psql("INSERT INTO evalcopy.marker VALUES ('1791559465538', '2026-10-09T15:24:00Z', 'amjis-ri02-validation-c720f1832', 'amjis-postgres')")
    assert ac.read_eval_copy_marker()["marker"] is None                                                                        # two rows: ambiguous, never picked


# ───────────────────────── census_stamp and main ─────────────────────────

def test_the_head_always_carries_the_probe_and_the_copy_stamp_only_when_declared(monkeypatch):
    monkeypatch.setattr(ac, "_db_identity", lambda: dict(db_identity=ident()))
    monkeypatch.setattr(ac, "read_eval_copy_marker", lambda: dict(PROBE_ABSENT))
    st = ac.census_stamp()
    assert st["eval_copy_probe"]["checked"] is True and "evaluation_copy" not in st
    monkeypatch.setattr(ac, "read_eval_copy_marker", lambda: dict(PROBE_OK))
    monkeypatch.setenv(ac.EVAL_COPY_ENV, RAW)
    st = ac.census_stamp()
    assert st["evaluation_copy"] == EC and st["eval_copy_probe"]["marker"] == EC and st["db_identity"]["system_id_sha256"] == COPY
    monkeypatch.setenv(ac.EVAL_COPY_ENV, "")
    with pytest.raises(ac.EvalCopyRefused):
        ac.census_stamp()                                                                                                       # the marker exists, the run says nothing


def test_main_refuses_with_its_own_exit_code_and_writes_nothing(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ac, "_db_identity", lambda: dict(db_identity=ident()))
    monkeypatch.setattr(ac, "read_eval_copy_marker", lambda: dict(PROBE_ABSENT))
    monkeypatch.setenv(ac.EVAL_COPY_ENV, RAW)                                                                                   # declared, but the database has no marker
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--out", str(tmp_path / "x.json")])
    rc = ac.main()
    assert rc == ac.EXIT_EVAL_COPY_REFUSED == 13 and not (tmp_path / "x.json").exists()
    assert "evaluation copy refused" in capsys.readouterr().err


# ───────────────────────── census_postprocess ─────────────────────────

def _head(d):
    return d[next(k for k in d if k.startswith("L") and isinstance(d[k], dict) and "assets" in d[k])]


def stamp_all(paths, ec=EC, probe=None):
    for p in paths:
        def fn(d, ec=ec, probe=probe):
            h = _head(d)
            h["evaluation_copy"] = ec
            h["eval_copy_probe"] = probe if probe is not None else dict(checked=True, marker_present=True, marker=ec)
        rewrite(p, fn)


def legacy_all(paths):
    for p in paths:
        rewrite(p, lambda d: _head(d).pop("eval_copy_probe", None))


def test_a_production_looking_census_reads_exactly_as_before(tmp_path):
    rc, out = run(world(tmp_path), tmp_path)
    assert rc == 0
    for name in ("CERTIFIED_LIST.md", "FIX_LIST.md", "BLOCKERS_BY_CLASS.md"):
        text = (out / name).read_text(encoding="utf-8")
        assert "evaluation copy" not in text and "Legacy census" not in text
    for name in ("CERTIFIED_LIST.json", "BLOCKERS_BY_CLASS.json"):
        d = json.loads((out / name).read_text())
        assert "evaluation_copy" not in d and "legacy_census" not in d


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


def test_forgery_a_census_with_no_probe_is_refused_unless_the_legacy_flag_is_given(tmp_path, capsys):
    paths = world(tmp_path)
    legacy_all(paths)
    refused(capsys, paths, tmp_path, "no eval_copy_probe")
    rc, out = run(paths, tmp_path / "ok", "--allow-legacy-census")
    assert rc == 0
    for name in ("CERTIFIED_LIST.md", "FIX_LIST.md", "BLOCKERS_BY_CLASS.md"):
        assert "Legacy census: production-ness assumed" in (out / name).read_text(encoding="utf-8"), name
    assert json.loads((out / "CERTIFIED_LIST.json").read_text())["legacy_census"] is True


def test_forgery_the_stripped_stamp_of_a_copy_census_is_refused(tmp_path, capsys):
    """A copy census whose evaluation_copy stamp was removed after the run, but whose probe still shows the marker, would read as production."""
    paths = world(tmp_path)
    stamp_all(paths)
    for p in paths:
        rewrite(p, lambda d: _head(d).pop("evaluation_copy"))
    refused(capsys, paths, tmp_path, "carries no evaluation_copy stamp")


def test_forgery_a_stamp_the_probe_does_not_back_is_refused(tmp_path, capsys):
    paths = world(tmp_path)
    stamp_all(paths, probe=PROBE_ABSENT)                                                                                       # a stamp with no marker behind it
    refused(capsys, paths, tmp_path, "not backed by the marker")
    (tmp_path / "b").mkdir()
    paths2 = world(tmp_path / "b")
    stamp_all(paths2, probe=dict(checked=True, marker_present=True, marker=dict(EC, backup_id="1791559465538")))                # a marker for another backup
    refused(capsys, paths2, tmp_path / "b", "not backed by the marker")


@pytest.mark.parametrize("probe", [dict(checked=False, reason="x"), dict(checked=True), dict(checked=True, marker_present="yes"), dict(marker_present=False), "no", []])
def test_forgery_an_unchecked_or_malformed_probe_is_refused(tmp_path, capsys, probe):
    paths = world(tmp_path)
    for p in paths:
        rewrite(p, lambda d, probe=probe: _head(d).__setitem__("eval_copy_probe", probe))
    refused(capsys, paths, tmp_path, "eval_copy_probe is not a checked lookup")


def test_forgery_one_layer_without_the_stamp_is_refused(tmp_path, capsys):
    paths = world(tmp_path)
    stamp_all(paths[:2])
    refused(capsys, paths, tmp_path, "different evaluation_copy stamps")


def test_forgery_layers_naming_different_backups_are_refused(tmp_path, capsys):
    paths = world(tmp_path)
    stamp_all(paths[:2])
    stamp_all(paths[2:], dict(EC, backup_id="1791559465538"))
    refused(capsys, paths, tmp_path, "different evaluation_copy stamps")


def test_forgery_some_layers_proven_and_some_legacy_is_refused(tmp_path, capsys):
    paths = world(tmp_path)
    legacy_all(paths[:1])
    refused(capsys, paths, tmp_path, "some files carry the evaluation-copy proof", "--allow-legacy-census")


@pytest.mark.parametrize("bad", [
    {"backup_id": "x"}, dict(EC, extra="y"), dict(EC, backup_id=""), dict(EC, backup_time=5), "backup 1", ["a"],
    dict(EC, backup_id="1791559465537\n# CERTIFIED: full production census"),                                                   # a newline would inject a line into the certificate
    dict(EC, instance="x y"), dict(EC, source_instance="a|b"), dict(EC, backup_time="2026-10-09T15:24:00Z\n"),
])
def test_forgery_a_stamp_value_that_could_inject_text_is_refused_before_it_is_printed(tmp_path, capsys, bad):
    paths = world(tmp_path)
    stamp_all(paths, bad, probe=dict(checked=True, marker_present=True, marker=bad))
    refused(capsys, paths, tmp_path, "evaluation_copy is not exactly")


def test_forgery_an_overlay_that_does_not_carry_the_same_stamp_is_refused(tmp_path):
    paths = n268._write(tmp_path, {})
    stamp_all(paths)                                                                                                            # the full census is a stamped copy ...
    delta = n268._delta(tmp_path, {"a1": n268._cells()})                                                                         # ... the scoped delta is not
    with pytest.raises(cp.Refused) as ei:
        cp.build(paths, ["L0", "L1", "L2"], None, None, "2026-10-09", {}, "n268", [str(delta)])
    assert "evaluation copy does not match" in str(ei.value)
    stamp_all([delta])                                                                                                          # the same stamp: accepted
    r = cp.build(paths, ["L0", "L1", "L2"], None, None, "2026-10-09", {}, "n268", [str(delta)])
    assert r["evaluation_copy"] == EC


def test_the_stamp_patterns_in_the_two_modules_are_identical():
    assert cp.EVAL_COPY_FIELDS == ac.EVAL_COPY_FIELDS
    assert cp.EVAL_COPY_ID.pattern == ac.EVAL_COPY_ID.pattern and cp.EVAL_COPY_TIME.pattern == ac.EVAL_COPY_TIME.pattern


def test_the_scoped_refusal_no_longer_says_production():
    src = pathlib.Path(cp.__file__).read_text(encoding="utf-8")
    assert "full production censuses" not in src and "full censuses of one database" in src


# ───────────────────────── the marker writer's SQL (the contract Exec's restore step runs) ─────────────────────────

MARKER_SQL = pathlib.Path(ac.__file__).resolve().parent / "evalcopy_marker.sql"


def _apply_marker(cl, **v):
    import os
    import subprocess
    env = {k: x for k, x in os.environ.items() if not (k.startswith("PG") or k in ("DATABASE_URL", "POSTGRES_URL"))}
    env.update(cl.env())
    args = [str(cl.bin_dir / "psql"), "-X", "-q", "-v", "ON_ERROR_STOP=1"] + [a for k, x in v.items() for a in ("-v", f"{k}={x}")] + ["-f", str(MARKER_SQL)]
    return subprocess.run(args, capture_output=True, text=True, env=env, timeout=60)


def test_REAL_SQL_the_marker_writers_sql_produces_exactly_what_the_census_reads(monkeypatch, clean_evalcopy):
    from _disposable_pg import point_psql_at
    disposable_pg = clean_evalcopy
    point_psql_at(disposable_pg, monkeypatch)
    disposable_pg.psql("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'suvarna_reader') THEN CREATE ROLE suvarna_reader NOLOGIN; END IF; END $$")
    p = _apply_marker(disposable_pg, **EC)
    assert p.returncode == 0, p.stderr[-400:]
    assert ac.read_eval_copy_marker() == PROBE_OK                                                                              # the census reads back what the writer wrote
    assert disposable_pg.psql("SELECT has_table_privilege('suvarna_reader', 'evalcopy.marker', 'SELECT')") == "t"
    assert disposable_pg.psql("SELECT has_table_privilege('suvarna_reader', 'evalcopy.marker', 'INSERT')") == "f"             # the reader can only read
    again = _apply_marker(disposable_pg, **dict(EC, backup_id="1791559465538"))                                                # idempotent: a later restore replaces the marker
    assert again.returncode == 0 and ac.read_eval_copy_marker()["marker"]["backup_id"] == "1791559465538"
    assert disposable_pg.psql("SELECT count(*) FROM evalcopy.marker") == "1"


@pytest.mark.parametrize("bad", [dict(EC, backup_id="a b"), dict(EC, backup_time="2026-10-09"), dict(EC, instance="amjis-postgres"), dict(EC, source_instance=EC["instance"]), dict(EC, backup_id="")])
def test_REAL_SQL_the_marker_writer_refuses_malformed_values(monkeypatch, clean_evalcopy, bad):
    from _disposable_pg import point_psql_at
    disposable_pg = clean_evalcopy
    point_psql_at(disposable_pg, monkeypatch)
    disposable_pg.psql("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'suvarna_reader') THEN CREATE ROLE suvarna_reader NOLOGIN; END IF; END $$")
    p = _apply_marker(disposable_pg, **bad)
    assert p.returncode != 0, bad                                                                                               # a CHECK constraint refuses it: nothing is written for a bad value
    assert ac.read_eval_copy_marker() == PROBE_ABSENT                                                                           # and the failed transaction left no marker behind
