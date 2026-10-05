"""test_e5_7_mirror_wiring.py -- E5.7: the mirror wiring of the L0 rebuild drill (`suvarna_mirror_drill.py`) and its hook in `suvarna_rehearsal.py`.

No production database, credential or network is touched, and the mirror recipe folders are never opened for writing: every test builds a
TINY SYNTHETIC recipe in a temp dir. PostgreSQL appears ONLY through the repo's disposable fixture (a throw-away loopback cluster).

Layout
  1. recipe             copy-never-edit, allow-list, symlink/oversize/in-recipe-scratch refusals, schema-only check, derived restore file
  2. baseline (real SQL) the builder on the disposable cluster with a synthetic recipe: PASS, idempotent re-run, and one broken variant per
                         verification / step failure; the document validator re-derives the verdict
  3. fingerprint output  the rehearsal side computed on the cluster; one refusal per rule for both sides
  4. drill compare       the EXISTING comparison over the DECLARED assets; undeclared / partial assets reported, never dropped
  5. status, reader spec, CLI hook
  6. source mutants      one textual mutation per verdict-deciding line; the invariants must catch each
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import types

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
REPO = GOV.parents[2]
sys.path.insert(0, str(GOV))
sys.path.insert(0, str(HERE))

import fingerprint_declarations as fd  # noqa: E402
import suvarna_mirror_drill as smd  # noqa: E402
import suvarna_rehearsal as sr  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401

SRC = (GOV / "suvarna_mirror_drill.py").read_text(encoding="utf-8")
REAL_DUMP = pathlib.Path("/Users/Dev/suvarna-evidence/S_L1/rehearsal_final/seed/prod_schema.sql")
H = "ab" * 32
SHA40 = "1" * 40
RUNTIME_OK = {"platform": "linux/amd64", "os": "Debian GNU/Linux 12 (bookworm)", "postgres_version": "15.18", "python_version": "3.11.9",
              "swisseph_version": "2.10.03", "collation": "en_US.UTF-8"}


@pytest.fixture
def needs_psycopg():
    return pytest.importorskip("psycopg")


# ═════════════════════════ synthetic declarations, recipe and documents ═════════════════════════

def _table(name, key, key_ev, exclude=(), naive=(), horizon=None):
    return {**({"horizon_date_column": horizon} if horizon else {}), "name": name, "scope": "global", "key": list(key), "key_evidence": key_ev, "naive_utc_columns": list(naive),
            "exclude": [{"column": c, "reason_code": rc, "reason": f"{c} is volatile by construction (synthetic)"} for c, rc in exclude],
            "write_evidence": ["x.py:1"]}


def _declared(tables, *, reproducibility=("deterministic",), notcov=(), groups=()):
    return {"status": "declared", "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "scope": "global",
            "coverage": "partial" if notcov else "full", "reproducibility": list(reproducibility), "groups": list(groups), "tables": tables,
            "not_covered_tables": [{"name": n, "reason": "r" * 70, "evidence": ["x.py:1"]} for n in notcov]}


def syn_doc(seeded_group=False):
    a = {f"a_{i}": _declared([_table(f"syn_t{i}", ["k"], f"primary_key:syn_t{i}_pk")]) for i in range(5)}
    a["a_multi"] = _declared([_table("syn_m1", ["k"], "primary_key:syn_m1_pk"), _table("syn_m2", ["k", "n"], "unique:syn_m2_u", [("id", "surrogate_identity")])])
    a["a_roll"] = _declared([_table("syn_roll", ["k"], "primary_key:syn_roll_pk", [("computed_at", "wall_clock_timestamp")], horizon="d")],
                            reproducibility=("rolling_horizon", "platform_bound"))
    a["a_part"] = _declared([_table("syn_p", ["k"], "primary_key:syn_p_pk")], notcov=("syn_shared",))
    a["a_gm1"] = _declared([], groups=("g_shared",))
    a["a_gm2"] = _declared([], groups=("g_shared",))
    a["a_und"] = {"status": "undeclared", "reason_code": "shared_table", "tables_written": ["syn_shared"], "evidence": ["x.py:1"],
                  "reason": "a shared table written by two assets: no row filter exists, so neither can be fingerprinted alone"}
    a["a_svc"] = {"status": "undeclared", "reason_code": "no_table", "tables_written": [], "evidence": [],
                  "reason": "a service asset: it owns no stored rows, so there is nothing to fingerprint at all here"}
    return {"schema": fd.SCHEMA_ID, "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "layer": "L0", "scope": "global",
            "source": {"registry_snapshot": "x", "registry_snapshot_sha256": "0" * 64, "schema_dump": "x", "schema_dump_sha256": "0" * 64,
                       "code_commit": SHA40},
            "groups": {"g_shared": {"tables": [_table("syn_g", ["k"], "primary_key:syn_g_pk", [("id", "surrogate_identity")])],
                                    "members": {"a_gm1": ["x.py:1"], "a_gm2": ["x.py:1"]}, "reproducibility": ["deterministic"],
                                    "seeded": seeded_group}},
            "assets": a}


def syn_decls(sha="7" * 64, seeded_group=False):
    doc = syn_doc(seeded_group)
    assert fd.validate(doc, registry=None, schema=None, repo_root=None) == []
    return fd.Declarations(doc=doc, sha256=sha)


SYN_DUMP = """--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
CREATE SCHEMA public;

CREATE TABLE public.syn_one (
    id bigint NOT NULL,
    k text NOT NULL,
    v numeric(9,4) NOT NULL,
    at_utc timestamp without time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.syn_one
    ADD CONSTRAINT syn_one_k PRIMARY KEY (k);

CREATE TABLE public.syn_two_a (
    k text NOT NULL,
    j jsonb NOT NULL
);

ALTER TABLE ONLY public.syn_two_a
    ADD CONSTRAINT syn_two_a_pk PRIMARY KEY (k);

CREATE TABLE public.syn_two_b (
    id bigint NOT NULL,
    k text NOT NULL,
    n integer NOT NULL,
    w text
);

ALTER TABLE ONLY public.syn_two_b
    ADD CONSTRAINT syn_two_b_u UNIQUE (k, n);

CREATE FUNCTION public.syn_f() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  INSERT INTO syn_two_a (k, j) VALUES ('x', '{}');
END;
$$;
"""
SYN_ROLES = "CREATE ROLE e57_role_a LOGIN NOINHERIT;\nCREATE ROLE e57_role_b NOLOGIN;\nGRANT e57_role_b TO e57_role_a;\n"
SYN_SEQ = "DO $$ BEGIN NULL; END $$;\n"
SYN_FIX = "SELECT 1;\n"
SYN_TABLES = ["syn_one", "syn_two_a", "syn_two_b"]


def syn_baseline_decls():
    """Declarations over the three real synthetic tables (so the baseline verification has something to find)."""
    doc = syn_doc()
    keep = {
        "a_one": _declared([_table("syn_one", ["k"], "primary_key:syn_one_k", [("id", "surrogate_identity"), ("created_at", "wall_clock_timestamp")], ["at_utc"])]),
        "a_two": _declared([_table("syn_two_a", ["k"], "primary_key:syn_two_a_pk"),
                            _table("syn_two_b", ["k", "n"], "unique:syn_two_b_u", [("id", "surrogate_identity")])]),
    }
    doc["assets"] = {**keep, "a_svc": doc["assets"]["a_svc"]}
    doc["groups"] = {}
    assert fd.validate(doc, registry=None, schema=None, repo_root=None) == []
    return fd.Declarations(doc=doc, sha256="9" * 64)


def make_recipe(tmp_path, *, dump=SYN_DUMP, roles=SYN_ROLES, seq=SYN_SEQ, fix=SYN_FIX, w1_roles=True):
    r = tmp_path / "recipe"
    (r / "seed").mkdir(parents=True)
    (r / "sql").mkdir()
    (r / "seed" / "prod_schema.sql").write_text(dump)
    (r / "sql" / "00_roles.sql").write_text(roles)
    (r / "sql" / "20_sequences.sql").write_text(seq)
    (r / "sql" / "30_seed_fixes.sql").write_text(fix)
    if w1_roles:
        (tmp_path / "w1_privilege_audit").mkdir(exist_ok=True)
        (tmp_path / "w1_privilege_audit" / "roles.sql").write_text(roles)
    return r


def tree_digest(root: pathlib.Path) -> dict:
    return {str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in sorted(root.rglob("*")) if p.is_file()}


# ═════════════════════════ 1. recipe: copy, never edit; schema only; derived restore ═════════════════════════

def test_copy_recipe_copies_allow_listed_files_records_hashes_and_never_touches_the_source(tmp_path):
    r = make_recipe(tmp_path)
    before = tree_digest(tmp_path)
    out = smd.copy_recipe(r, tmp_path / "scratch")
    assert tree_digest(tmp_path) == {**before, **{k: v for k, v in tree_digest(tmp_path).items() if k.startswith("scratch")}}      # nothing outside scratch moved
    assert sorted(out) == ["roles", "roles_acl_mirror", "schema", "seed_fixes", "sequences"]
    for name, m in out.items():
        assert hashlib.sha256(pathlib.Path(m["path"]).read_bytes()).hexdigest() == m["sha256"]
        assert pathlib.Path(m["path"]).parent == tmp_path / "scratch" and (os.stat(m["path"]).st_mode & 0o077) == 0
    assert out["schema"]["source"] == "seed/prod_schema.sql" and out["roles_acl_mirror"]["source"] == "../w1_privilege_audit/roles.sql"


def test_copy_recipe_works_without_the_optional_w1_roles_mirror(tmp_path):
    r = make_recipe(tmp_path, w1_roles=False)
    assert "roles_acl_mirror" not in smd.copy_recipe(r, tmp_path / "scratch")


@pytest.mark.parametrize("missing", ["seed/prod_schema.sql", "sql/00_roles.sql", "sql/20_sequences.sql", "sql/30_seed_fixes.sql"])
def test_copy_recipe_refuses_a_missing_recipe_file(tmp_path, missing):
    r = make_recipe(tmp_path)
    (r / missing).unlink()
    with pytest.raises(smd.MirrorError, match="missing"):
        smd.copy_recipe(r, tmp_path / "scratch")


def test_copy_recipe_refuses_a_symlinked_file_a_symlinked_directory_and_a_non_regular_file(tmp_path):
    r = make_recipe(tmp_path)
    real = tmp_path / "elsewhere.sql"
    real.write_text("SELECT 1;")
    (r / "sql" / "20_sequences.sql").unlink()
    (r / "sql" / "20_sequences.sql").symlink_to(real)
    with pytest.raises(smd.MirrorError, match="symlink"):
        smd.copy_recipe(r, tmp_path / "s1")
    (r / "sql" / "20_sequences.sql").unlink()
    (r / "sql" / "20_sequences.sql").write_text(SYN_SEQ)
    sql_dir = r / "sql"
    moved = tmp_path / "sqlreal"
    sql_dir.rename(moved)
    sql_dir.symlink_to(moved)
    with pytest.raises(smd.MirrorError, match="symlink"):
        smd.copy_recipe(r, tmp_path / "s2")
    sql_dir.unlink()
    moved.rename(sql_dir)
    (sql_dir / "30_seed_fixes.sql").unlink()
    (sql_dir / "30_seed_fixes.sql").mkdir()
    with pytest.raises(smd.MirrorError, match="regular"):
        smd.copy_recipe(r, tmp_path / "s3")


def test_copy_recipe_refuses_an_oversize_file(tmp_path, monkeypatch):
    r = make_recipe(tmp_path)
    monkeypatch.setattr(smd, "MAX_RECIPE_BYTES", 10)
    with pytest.raises(smd.MirrorError, match="larger"):
        smd.copy_recipe(r, tmp_path / "scratch")


def test_copy_recipe_refuses_a_scratch_inside_equal_to_or_containing_the_recipe_and_a_non_empty_scratch(tmp_path):
    r = make_recipe(tmp_path)
    for bad in (r, r / "seed" / "x", tmp_path):
        with pytest.raises(smd.MirrorError, match="recipe"):
            smd.copy_recipe(r, bad)
    s = tmp_path / "scratch"
    s.mkdir()
    (s / "stale").write_text("x")
    with pytest.raises(smd.MirrorError, match="new or empty"):
        smd.copy_recipe(r, s)
    link = tmp_path / "link_to_recipe"
    link.symlink_to(r)
    with pytest.raises(smd.MirrorError, match="recipe"):
        smd.copy_recipe(r, link / "inner")


def test_copy_recipe_refuses_a_copy_that_does_not_match_its_source(tmp_path, monkeypatch):
    r = make_recipe(tmp_path)
    real = smd.shutil.copyfile
    monkeypatch.setattr(smd.shutil, "copyfile", lambda a, b: (real(a, b), open(b, "ab").write(b"x"))[0])
    with pytest.raises(smd.MirrorError, match="does not match"):
        smd.copy_recipe(r, tmp_path / "scratch")


def test_assert_schema_only_refuses_data_statements_and_accepts_function_body_inserts():
    smd.assert_schema_only(SYN_DUMP)                                     # an indented INSERT inside a function body is not data
    for bad in ("COPY public.t (a) FROM stdin;\n1\n\\.\n", "INSERT INTO public.t VALUES (1);\n", "x\n\\.\n"):
        with pytest.raises(smd.MirrorError, match="data statements"):
            smd.assert_schema_only(SYN_DUMP + bad)


@pytest.mark.skipif(not REAL_DUMP.is_file(), reason="the mirror recipe dump is not on this machine")
def test_the_real_mirror_dump_is_schema_only():
    smd.assert_schema_only(REAL_DUMP.read_text(encoding="utf-8"))


def test_derive_schema_restore_removes_exactly_the_create_schema_line():
    out, info = smd.derive_schema_restore(SYN_DUMP)
    assert "CREATE SCHEMA public;" not in out and out.count("\n") == SYN_DUMP.count("\n") - 1
    assert info == {"schema_line_removed": True, "vector_shim": False, "vector_columns_replaced": 0}
    for bad in (SYN_DUMP.replace("CREATE SCHEMA public;\n", ""), SYN_DUMP + "CREATE SCHEMA public;\n"):
        with pytest.raises(smd.MirrorError, match="exactly one"):
            smd.derive_schema_restore(bad)


def test_derive_schema_restore_shims_vector_only_when_the_extension_is_unavailable():
    dump = SYN_DUMP.replace("w text\n", "w text,\n    emb public.vector(768),\n    emb2 public.vector(768) NOT NULL\n")
    out, info = smd.derive_schema_restore(dump, vector_available=True)
    assert "public.vector(768)" in out and not info["vector_shim"]
    out, info = smd.derive_schema_restore(dump, vector_available=False)
    assert "vector" not in out.split("CREATE FUNCTION")[0] and info == {"schema_line_removed": True, "vector_shim": True, "vector_columns_replaced": 2}
    assert "emb text," in out and "emb2 text NOT NULL" in out


def test_error_classes_counts_psql_errors_by_class():
    err = ("psql:x:1: ERROR:  relation \"t\" already exists\npsql:x:2: ERROR:  role \"r\" does not exist\n"
           "psql:x:3: ERROR:  multiple primary keys for table \"t\" are not allowed\npsql:x:4: ERROR:  permission denied for schema public\n"
           "psql:x:5: ERROR:  syntax error at or near \"x\"\nNOTICE: fine\n")
    assert smd.error_classes(err) == {"already_exists": 1, "does_not_exist": 1, "multiple_primary_keys": 1, "other": 1, "privilege": 1}
    assert smd.error_classes("") == {} and smd.error_classes(None) == {}


# ═════════════════════════ 2. the baseline builder on the disposable cluster ═════════════════════════

def _target(cl, db):
    cl.psql(f"DROP DATABASE IF EXISTS {db}", db="postgres")
    cl.psql(f"CREATE DATABASE {db}", db="postgres")
    return smd.Target(pg_bin=str(cl.bin_dir), host="127.0.0.1", port=cl.port, user=cl.user, db=db, policy="disposable",
                      expect={"data_directory": str(cl.data_dir), "port": cl.port})


def _syn_extract(tables=SYN_TABLES, dump=SYN_DUMP):
    return fd.extract_schema(dump, tables)


def _build(cl, tmp_path, name, *, recipe=None, decls=None, extract=None, **kw):
    t = _target(cl, f"suvarna_disposable_{name}")
    recipe = recipe or make_recipe(tmp_path / name)
    try:
        return smd.build_mirror_baseline(recipe, tmp_path / name / "scratch", t, decls=decls or syn_baseline_decls(), extract=extract or _syn_extract(), **kw)
    finally:
        cl.psql(f"DROP DATABASE IF EXISTS {t.db}", db="postgres")


def test_baseline_builds_and_verifies_a_synthetic_recipe(needs_psycopg, disposable_pg, tmp_path):
    doc = _build(disposable_pg, tmp_path, "ok1")
    assert doc["result"] == "PASS" and smd.validate_baseline(doc) == []
    assert [s["name"] for s in doc["steps"]] == list(smd.STEP_ORDER)
    st = {s["name"]: s["status"] for s in doc["steps"]}
    assert st["copy_recipe"] == st["schema_only_check"] == st["roles"] == st["sequences"] == st["verify"] == "OK" and st["seed_fixes"] == "SKIPPED"
    assert doc["verification"] == {"tables_checked": 3, "problems": [], "ok": True}
    assert doc["derived"]["roles_statements_equal_w1_mirror"] is True and doc["derived"]["schema_line_removed"] is True
    assert doc["cluster"]["host"] == "127.0.0.1" and doc["cluster"]["port"] == disposable_pg.port and doc["cluster"]["policy"] == "disposable"
    assert doc["recipe"]["schema"]["sha256"] == hashlib.sha256(SYN_DUMP.encode()).hexdigest()
    json.dumps(doc)


def test_baseline_is_idempotent_on_a_cluster_that_already_has_the_roles(needs_psycopg, disposable_pg, tmp_path):
    t = _target(disposable_pg, "suvarna_disposable_idem")
    try:
        r = make_recipe(tmp_path / "idem")
        a = smd.build_mirror_baseline(r, tmp_path / "idem" / "s1", t, decls=syn_baseline_decls(), extract=_syn_extract())
        b = smd.build_mirror_baseline(r, tmp_path / "idem" / "s2", t, decls=syn_baseline_decls(), extract=_syn_extract())
    finally:
        disposable_pg.psql("DROP DATABASE IF EXISTS suvarna_disposable_idem", db="postgres")
    assert a["result"] == "PASS" and b["result"] == "PASS"
    assert {s["name"]: s["status"] for s in b["steps"]}["roles"] == "TOLERATED_ERRORS" and {s["name"]: s["status"] for s in b["steps"]}["schema"] == "TOLERATED_ERRORS"
    assert smd.validate_baseline(b) == []


def test_baseline_runs_the_l1_seed_fixes_only_when_asked(needs_psycopg, disposable_pg, tmp_path):
    doc = _build(disposable_pg, tmp_path, "fix1", with_l1_fixes=True)
    assert {s["name"]: s["status"] for s in doc["steps"]}["seed_fixes"] == "OK" and doc["with_l1_fixes"] is True and doc["result"] == "PASS"
    bad = _build(disposable_pg, tmp_path, "fix2", recipe=make_recipe(tmp_path / "fix2", fix="SELECT * FROM no_such_table;\n"), with_l1_fixes=True)
    assert {s["name"]: s["status"] for s in bad["steps"]}["seed_fixes"] == "TOLERATED_ERRORS" and bad["result"] == "PASS"     # fixes are optional: reported, not fatal


def test_baseline_fails_when_a_declared_table_is_missing_from_the_restored_schema(needs_psycopg, disposable_pg, tmp_path):
    dump = SYN_DUMP.replace("CREATE TABLE public.syn_two_b", "CREATE TABLE public.syn_zzz")
    doc = _build(disposable_pg, tmp_path, "miss", recipe=make_recipe(tmp_path / "miss", dump=dump))
    assert doc["result"] == "FAIL" and any("syn_two_b" in p and "missing" in p for p in doc["verification"]["problems"])
    assert smd.validate_baseline(doc) == []


def test_baseline_fails_on_a_column_type_or_key_constraint_that_differs_from_the_dump_extract(needs_psycopg, disposable_pg, tmp_path):
    ext = _syn_extract()
    ext["tables"]["syn_one"]["columns"]["v"]["type"] = "numeric(10,4)"
    doc = _build(disposable_pg, tmp_path, "typ", extract=ext)
    assert doc["result"] == "FAIL" and any("syn_one.v" in p and "type" in p for p in doc["verification"]["problems"])
    ext2 = _syn_extract()
    ext2["tables"]["syn_two_b"]["unique"][0]["name"] = "syn_two_b_other"
    doc2 = _build(disposable_pg, tmp_path, "idx", extract=ext2)
    assert doc2["result"] == "FAIL" and any("index syn_two_b_other is missing" in p for p in doc2["verification"]["problems"])
    ext3 = _syn_extract()
    ext3["tables"]["syn_one"]["columns"]["extra_col"] = {"type": "text", "not_null": False, "default": None, "generated": False, "identity": False}
    doc3 = _build(disposable_pg, tmp_path, "col", extract=ext3)
    assert doc3["result"] == "FAIL" and any("extra_col" in p and "missing" in p for p in doc3["verification"]["problems"])


def test_baseline_fails_when_the_roles_file_has_a_real_error(needs_psycopg, disposable_pg, tmp_path):
    doc = _build(disposable_pg, tmp_path, "role", recipe=make_recipe(tmp_path / "role", roles="CREATE ROLE e57_role_c LOGIN;\nCREATE BOGUS;\n"))
    assert {s["name"]: s["status"] for s in doc["steps"]}["roles"] == "FAILED" and doc["result"] == "FAIL" and smd.validate_baseline(doc) == []


def test_baseline_fails_when_the_sequences_file_errors(needs_psycopg, disposable_pg, tmp_path):
    doc = _build(disposable_pg, tmp_path, "seq", recipe=make_recipe(tmp_path / "seq", seq="SELECT * FROM no_such;\n"))
    assert {s["name"]: s["status"] for s in doc["steps"]}["sequences"] == "FAILED" and doc["result"] == "FAIL"


def test_baseline_refuses_a_dump_with_data_before_touching_the_database(disposable_pg, tmp_path):
    t = _target(disposable_pg, "suvarna_disposable_data")
    try:
        r = make_recipe(tmp_path / "data", dump=SYN_DUMP + "COPY public.syn_one (id) FROM stdin;\n1\n\\.\n")
        with pytest.raises(smd.MirrorError, match="data statements"):
            smd.build_mirror_baseline(r, tmp_path / "data" / "scratch", t, decls=syn_baseline_decls(), extract=_syn_extract())
        assert disposable_pg.psql("SELECT count(*) FROM pg_tables WHERE tablename = 'syn_one'", db=t.db) == "0"
    finally:
        disposable_pg.psql("DROP DATABASE IF EXISTS suvarna_disposable_data", db="postgres")


def test_baseline_never_targets_a_forbidden_port(tmp_path):
    for port in sorted(sr.FORBIDDEN_PORTS):
        t = smd.Target(pg_bin="/nonexistent", host="127.0.0.1", port=port, user="x", db="suvarna_disposable_x")
        with pytest.raises(smd.MirrorError, match="never targeted"):
            smd.run_psql(t, sql="SELECT 1", on_error_stop=True)


def test_baseline_without_psycopg_is_unmeasured_not_pass(disposable_pg, tmp_path, monkeypatch):
    monkeypatch.setattr(sr, "_psycopg_available", lambda: False)
    doc = _build(disposable_pg, tmp_path, "nopg")
    assert doc["result"] == "UNMEASURED" and {s["name"]: s["status"] for s in doc["steps"]}["verify"] == "UNMEASURED" and smd.validate_baseline(doc) == []


def test_baseline_verification_connection_is_policy_checked_and_logged(needs_psycopg, disposable_pg, tmp_path, monkeypatch):
    seen = []
    real = sr.connect_checked
    monkeypatch.setattr(smd.sr, "connect_checked", lambda url, policy, log, **kw: (seen.append((url, policy, dict(kw.get("expect") or {}))), real(url, policy, log, **kw))[1])
    doc = _build(disposable_pg, tmp_path, "pol")
    assert doc["result"] == "PASS" and len(seen) == 1 and seen[0][1] == "disposable" and seen[0][0].startswith("postgresql://") and "@127.0.0.1:" in seen[0][0]
    assert seen[0][2]["port"] == disposable_pg.port


def test_baseline_with_a_wrong_expected_server_is_refused(needs_psycopg, disposable_pg, tmp_path):
    t = _target(disposable_pg, "suvarna_disposable_wrong")
    t = smd.Target(**{**t.__dict__, "expect": {"data_directory": "/somewhere/else", "port": disposable_pg.port}})
    try:
        doc = smd.build_mirror_baseline(make_recipe(tmp_path / "wrong"), tmp_path / "wrong" / "scratch", t, decls=syn_baseline_decls(), extract=_syn_extract())
    finally:
        disposable_pg.psql("DROP DATABASE IF EXISTS suvarna_disposable_wrong", db="postgres")
    assert doc["result"] == "FAIL" and {s["name"]: s["status"] for s in doc["steps"]}["verify"] == "FAILED"


# ── the baseline document validator re-derives the verdict ──

def _good_baseline():
    steps = [smd._step(n, "OK") for n in smd.STEP_ORDER]
    steps[smd.STEP_ORDER.index("seed_fixes")] = smd._step("seed_fixes", "SKIPPED", reason="x")
    doc = {"schema": smd.BASELINE_SCHEMA, "tool_sha256": smd.tool_sha256(), "result": "PASS", "with_l1_fixes": False,
           "recipe": {n: {"source": n, "sha256": H, "bytes": 1} for n in ("schema", "roles", "sequences", "seed_fixes")},
           "derived": {"schema_restore_sha256": H, "schema_line_removed": True, "vector_shim": False, "vector_columns_replaced": 0, "roles_statements_equal_w1_mirror": True},
           "cluster": {"host": "127.0.0.1", "port": 40001, "database": "suvarna_disposable_x", "policy": "disposable", "data_directory": "/tmp/x", "pg_version": "15"},
           "steps": steps, "verification": {"tables_checked": 3, "problems": [], "ok": True}}
    return doc


def test_good_baseline_document_validates_and_derives_pass():
    d = _good_baseline()
    assert smd.validate_baseline(d) == [] and smd.derive_baseline_result(d) == "PASS"


@pytest.mark.parametrize("name,mutate", [
    ("forged_pass_with_failed_step", lambda d: d["steps"][4].update({"status": "FAILED"})),
    ("forged_pass_with_problem", lambda d: d["verification"].update({"problems": ["x"]})),
    ("verification_ok_not_derived", lambda d: d["verification"].update({"ok": True, "tables_checked": 0})),
    ("skipped_schema", lambda d: d["steps"][4].update({"status": "SKIPPED"})),
    ("unknown_status", lambda d: d["steps"][2].update({"status": "MAYBE"})),
    ("steps_out_of_order", lambda d: d["steps"].reverse()),
    ("missing_step", lambda d: d["steps"].pop()),
    ("wrong_tool_sha", lambda d: d.update({"tool_sha256": H})),
    ("extra_key", lambda d: d.update({"x": 1})),
    ("wrong_schema_id", lambda d: d.update({"schema": "x/v1"})),
    ("non_loopback_cluster", lambda d: d["cluster"].update({"host": "10.0.0.1"})),
    ("forbidden_port", lambda d: d["cluster"].update({"port": 5432})),
    ("bad_recipe_hash", lambda d: d["recipe"]["schema"].update({"sha256": "zz"})),
    ("missing_recipe_file", lambda d: d["recipe"].pop("roles")),
    ("derived_extra_key", lambda d: d["derived"].update({"x": 1})),
    ("verify_unmeasured_but_result_pass", lambda d: d["steps"][-1].update({"status": "UNMEASURED"})),
])
def test_baseline_validator_refuses(name, mutate):
    d = _good_baseline()
    mutate(d)
    assert smd.validate_baseline(d) != [], name


def test_baseline_validator_never_raises_on_garbage():
    for bad in (None, [], "x", {}, {"schema": 1}, {**_good_baseline(), "steps": "x"}, {**_good_baseline(), "verification": None}):
        assert isinstance(smd.validate_baseline(bad), list) and smd.validate_baseline(bad)


# ═════════════════════════ 3. fingerprint output (both sides) ═════════════════════════

def _tables_for(decls, assets=None, *, seed=0):
    out = {}
    for a in (assets or decls.expected_assets()):
        out[a] = {t: {"sha256": hashlib.sha256(f"{a}|{t}|{seed}".encode()).hexdigest(), "rows": 5} for t in decls.tables(a)}
    return out


def _projections_for(decls, tabs, seed=0):
    """The projection block: one sha256 per unit with a recorded expected difference, the same on both sides unless the test changes it."""
    return {u: {t: {"sha256": hashlib.sha256(f"proj|{u}|{t}|{seed}".encode()).hexdigest() if tabs[u][t]["rows"] else fd.empty_projection_fingerprint(decls, u, t),
                    "rows": tabs[u][t]["rows"]}} for u, t in decls.projection_tables().items() if u in tabs}


HZ_MIN, HZ_MAX = "2026-01-01", "2026-01-05"


def _horizons_for(decls, tabs):
    """The N-135 horizon blocks of a fingerprint file: one block per rolling_horizon unit that is present, covering the whole table (a production block; a rehearsal
    block with the same horizon as production by default)."""
    out = {}
    for u, h in decls.horizon_tables().items():
        if u in tabs:
            m = tabs[u][h["table"]]
            out[u] = {h["table"]: {"date_column": h["date_column"], "min_date": HZ_MIN if m["rows"] else None, "max_date": HZ_MAX if m["rows"] else None, "rows": m["rows"],
                                   "overlap_cutoff": HZ_MAX if m["rows"] else None, "overlap_rows": m["rows"], "overlap_sha256": m["sha256"]}}
    return out


def out_doc(decls, side="production", *, assets=None, seed=0, stage=None, as_of="2026-10-03", commit=SHA40, rebuild="auto"):
    tabs = _tables_for(decls, assets, seed=seed)
    stage = stage or ("production_read" if side == "production" else "after_rebuild")
    if rebuild == "auto":
        rebuild = {"run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "orchestrator_commit": commit, "runtime": dict(RUNTIME_OK)} if (side == "rehearsal" and stage == "after_rebuild") else None
    return {"schema": smd.OUTPUT_SCHEMA, "side": side, "stage": stage, "definition": fd.FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256,
            "commit": commit, "as_of": as_of, "rebuild": rebuild, "tables": tabs,
            "fingerprints": {a: fd.composite_fingerprint({n: m["sha256"] for n, m in t.items()}) for a, t in tabs.items()},
            "projections": _projections_for(decls, tabs, seed), "horizons": _horizons_for(decls, tabs)}


def test_rehearsal_fingerprints_on_the_cluster_match_the_declarations_loader_and_use_a_read_only_transaction(needs_psycopg, disposable_pg, tmp_path):
    decls = syn_baseline_decls()
    t = _target(disposable_pg, "suvarna_disposable_fp")
    try:
        disposable_pg.psql("CREATE TABLE syn_one (id bigserial, k text PRIMARY KEY, v numeric(9,4) NOT NULL, at_utc timestamp NOT NULL, created_at timestamptz NOT NULL DEFAULT now());"
                           "CREATE TABLE syn_two_a (k text PRIMARY KEY, j jsonb NOT NULL);"
                           "CREATE TABLE syn_two_b (id bigserial, k text NOT NULL, n int NOT NULL, w text, UNIQUE (k, n));"
                           "INSERT INTO syn_one (k, v, at_utc) VALUES ('a', 1.5, '2020-01-01 00:00:00'), ('b', 2.5, '2020-01-02 00:00:00');"
                           "INSERT INTO syn_two_a VALUES ('a', '{}');INSERT INTO syn_two_b (k, n, w) VALUES ('a', 1, 'x');", db=t.db)
        log = sr.ConnectionLog()
        conn = sr.connect_checked(t.url, "disposable", log, expect=t.expect)
        try:
            doc = smd.rehearsal_fingerprints(conn, decls, stage="baseline", as_of="2026-10-03", commit=SHA40)
            assert conn.read_only is True
            with pytest.raises(Exception):                                         # the connection is read-only: a write is refused
                conn.execute("INSERT INTO syn_two_a VALUES ('zz', '{}')")
            conn.rollback()
            direct = fd.unit_fingerprints(conn, decls)
        finally:
            conn.close()
        assert doc["fingerprints"] == direct["fingerprints"] and doc["tables"] == direct["tables"] and doc["stage"] == "baseline"
        assert smd.validate_fingerprint_output(doc, decls, side="rehearsal") == []
        assert log.opened[0]["policy"] == "disposable" and log.opened[0]["host"] == "127.0.0.1"
        # the rows in the database are untouched by the read
        assert disposable_pg.psql("SELECT count(*) FROM syn_two_a", db=t.db) == "1"
    finally:
        disposable_pg.psql("DROP DATABASE IF EXISTS suvarna_disposable_fp", db="postgres")


def test_rehearsal_fingerprints_refuses_bad_arguments_before_reading(monkeypatch):
    class Boom:
        def __getattr__(self, n):
            raise AssertionError("must not touch the connection")
    d = syn_baseline_decls()
    good = dict(stage="baseline", as_of="2026-10-03", commit=SHA40)
    for kw in ({**good, "stage": "production_read"}, {**good, "as_of": "03/10/2026"}, {**good, "commit": "abc"},
               {**good, "stage": "after_rebuild"}, {**good, "rebuild": {"run_id": "x", "orchestrator_commit": SHA40}},
               {**good, "stage": "after_rebuild", "rebuild": {"run_id": "bad", "orchestrator_commit": SHA40}},
               {**good, "stage": "after_rebuild", "rebuild": {"run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5"}}):
        with pytest.raises(smd.MirrorError):
            smd.rehearsal_fingerprints(Boom(), d, **kw)


D5 = syn_decls()


def test_good_output_documents_validate_for_both_sides():
    assert smd.validate_fingerprint_output(out_doc(D5, "production"), D5, side="production") == []
    assert smd.validate_fingerprint_output(out_doc(D5, "rehearsal"), D5, side="rehearsal") == []
    assert smd.validate_fingerprint_output(out_doc(D5, "rehearsal", stage="baseline", rebuild=None), D5, side="rehearsal") == []
    assert smd.validate_fingerprint_output(out_doc(D5, "production", assets=["a_0", "a_multi"]), D5, side="production") == []     # a subset is allowed (a failed table)


def _o(mutate, side="production", **kw):
    d = out_doc(D5, side, **kw)
    mutate(d)
    return smd.validate_fingerprint_output(d, D5, side=side)


@pytest.mark.parametrize("name,mutate,side", [
    ("wrong_schema", lambda d: d.update({"schema": "x"}), "production"),
    ("wrong_side", lambda d: d.update({"side": "rehearsal"}), "production"),
    ("wrong_definition", lambda d: d.update({"definition": "other/1"}), "production"),
    ("wrong_declarations_sha", lambda d: d.update({"declarations_sha256": H}), "production"),
    ("bad_commit", lambda d: d.update({"commit": "abc"}), "production"),
    ("bad_as_of", lambda d: d.update({"as_of": "yesterday"}), "production"),
    ("production_stage_baseline", lambda d: d.update({"stage": "baseline"}), "production"),
    ("rehearsal_stage_production_read", lambda d: d.update({"stage": "production_read"}), "rehearsal"),
    ("production_with_rebuild", lambda d: d.update({"rebuild": {"run_id": "x", "orchestrator_commit": SHA40}}), "production"),
    ("after_rebuild_without_receipt", lambda d: d.update({"rebuild": None}), "rehearsal"),
    ("baseline_with_receipt", lambda d: d.update({"stage": "baseline"}), "rehearsal"),
    ("undeclared_asset", lambda d: (d["tables"].update({"a_und": {}}), d["fingerprints"].update({"a_und": H})), "production"),
    ("unknown_asset", lambda d: (d["tables"].update({"nope": {}}), d["fingerprints"].update({"nope": H})), "production"),
    ("tables_without_fingerprint", lambda d: d["fingerprints"].pop("a_0"), "production"),
    ("fingerprint_without_tables", lambda d: d["tables"].pop("a_1"), "production"),
    ("fingerprint_without_tables_rehearsal", lambda d: d["tables"].pop("a_1"), "rehearsal"),
    ("group_member_as_unit", lambda d: (d["tables"].update({"a_gm1": {}}), d["fingerprints"].update({"a_gm1": H})), "production"),
    ("empty_hash_with_rows", lambda d: (d["tables"]["a_0"]["syn_t0"].update(sha256=fd.empty_table_fingerprint(D5, "a_0", "syn_t0")),
                                        d["fingerprints"].update(a_0=fd.empty_table_fingerprint(D5, "a_0", "syn_t0"))), "production"),
    ("zero_rows_with_data_hash", lambda d: d["tables"]["a_0"]["syn_t0"].update(rows=0), "production"),
    ("nil_run_id", lambda d: d["rebuild"].update(run_id="00000000-0000-0000-0000-000000000000"), "rehearsal"),
    ("dash_run_id", lambda d: d["rebuild"].update(run_id="-" * 36), "rehearsal"),
    ("missing_table", lambda d: d["tables"]["a_multi"].pop("syn_m2"), "production"),
    ("extra_table", lambda d: d["tables"]["a_0"].update({"extra": {"sha256": H, "rows": 1}}), "production"),
    ("bad_table_sha", lambda d: d["tables"]["a_0"]["syn_t0"].update({"sha256": "zz"}), "production"),
    ("negative_rows", lambda d: d["tables"]["a_0"]["syn_t0"].update({"rows": -1}), "production"),
    ("bool_rows", lambda d: d["tables"]["a_0"]["syn_t0"].update({"rows": True}), "production"),
    ("extra_table_key", lambda d: d["tables"]["a_0"]["syn_t0"].update({"x": 1}), "production"),
    ("composite_not_recomputed", lambda d: d["fingerprints"].update({"a_multi": H}), "production"),
    ("single_table_asset_fp_differs", lambda d: d["fingerprints"].update({"a_0": H}), "production"),
    ("extra_top_key", lambda d: d.update({"x": 1}), "production"),
])
def test_fingerprint_output_validator_refuses(name, mutate, side):
    assert _o(mutate, side) != [], name


def test_fingerprint_output_validator_rejects_a_bad_side_and_garbage():
    with pytest.raises(smd.MirrorError):
        smd.validate_fingerprint_output(out_doc(D5), D5, side="both")
    for bad in (None, [], "x", {}):
        assert smd.validate_fingerprint_output(bad, D5, side="production")


# ═════════════════════════ 4. drill compare: the existing comparison over the DECLARED assets ═════════════════════════

def _ex(n=1, ch="", code="rolling_horizon"):
    return {"reason_code": code, "detail": ("rolling forward horizon computed from today at run time; pinned window recorded " + ch).ljust(60, "."),
            "decision": "N-135" if code == "rolling_horizon" else f"N-{100 + n}"}


def _pair(**kw):
    return out_doc(D5, "production", **kw), out_doc(D5, "rehearsal", **kw)


def _set_unit(doc, unit, sha, rows=None):
    """Give every table of `unit` the value `sha` (rows optional) and recompute the unit fingerprint."""
    for t, m in doc["tables"][unit].items():
        m["sha256"] = sha if len(doc["tables"][unit]) == 1 else hashlib.sha256(f"{sha}{t}".encode()).hexdigest()
        if rows is not None:
            m["rows"] = rows
    doc["fingerprints"][unit] = fd.composite_fingerprint({t: m["sha256"] for t, m in doc["tables"][unit].items()})
    for t, b in doc.get("horizons", {}).get(unit, {}).items():            # the horizon block follows the table (the whole table is its overlap)
        if rows is not None:
            b["rows"] = b["overlap_rows"] = rows
        if b["overlap_rows"] == b["rows"]:
            b["overlap_sha256"] = doc["tables"][unit][t]["sha256"]


def _later(reh, prod, unit="a_roll", extra=3, mx="2026-01-09", decls=None):
    """Make `unit`'s rehearsal differ from production ONLY by `extra` rows after the production horizon (built later): the shared range stays row-for-row equal."""
    decls = decls or D5
    t = decls.horizon_tables()[unit]["table"]
    pb = prod["horizons"][unit][t]
    n = pb["rows"] + extra
    reh["tables"][unit][t].update(sha256=hashlib.sha256(f"later|{unit}".encode()).hexdigest(), rows=n)
    reh["fingerprints"][unit] = fd.composite_fingerprint({x: m["sha256"] for x, m in reh["tables"][unit].items()})
    reh["horizons"][unit][t] = {"date_column": pb["date_column"], "min_date": pb["min_date"], "max_date": mx, "rows": n, "overlap_cutoff": pb["max_date"],
                                "overlap_rows": pb["overlap_rows"], "overlap_sha256": pb["overlap_sha256"]}


def _empty_unit(doc, unit):
    for t, m in doc["tables"][unit].items():
        m["sha256"], m["rows"] = fd.empty_table_fingerprint(D5, unit, t), 0
    doc["fingerprints"][unit] = fd.composite_fingerprint({t: m["sha256"] for t, m in doc["tables"][unit].items()})


def test_compare_of_equal_sides_is_scoped_over_the_comparison_units():
    prod, reh = _pair()
    drill, cov = smd.build_drill(prod, reh, D5, None, commit=SHA40)
    units = D5.expected_assets()
    assert len(units) == 9 and "grp_g_shared" in units and drill["expected_assets"] == units == sorted(units)
    assert drill["result"] == "PASS_DECLARED_ONLY" and cov["result"] == "PASS_DECLARED_ONLY"      # partial, undeclared and non-deterministic assets exist
    assert drill["equal"] == units and drill["empty_both_sides"] == []
    assert not {"a_und", "a_svc", "a_gm1", "a_gm2"} & set(units)                                  # undeclared assets and group-only members are no units
    assert sr.validate_drill(drill) == [] and sr.validate_drill(drill, declarations_coverage=D5.drill_coverage()) == []
    assert drill["coverage"] == D5.drill_coverage() and drill["coverage"]["groups"] == {"grp_g_shared": ["a_gm1", "a_gm2"]}
    assert set(drill["coverage"]["undeclared"]) == {"a_und", "a_svc"} and drill["coverage"]["partial"] == {"a_part": ["syn_shared"]}
    assert drill["coverage"]["non_deterministic"] == {"a_roll": ["rolling_horizon", "platform_bound"]} and drill["coverage"]["scope"] == "declared_only"
    assert drill["rows"]["a_multi"] == {"production": {"syn_m1": 5, "syn_m2": 5}, "rehearsal": {"syn_m1": 5, "syn_m2": 5}}
    assert set(cov["undeclared"]) == {"a_und", "a_svc"} and sorted(cov["partial"]) == ["a_part"] and cov["declarations_sha256"] == D5.sha256
    assert cov["unit_status"]["grp_g_shared"] == {"status": "equal", "members": ["a_gm1", "a_gm2"]} and cov["differences_with_hints"] == []
    assert cov["reproducibility"] == {"a_roll": ["rolling_horizon", "platform_bound"]}


def test_a_bare_pass_needs_a_declarations_file_with_nothing_partial_undeclared_or_non_deterministic():
    doc = syn_doc()
    for a in ("a_und", "a_svc"):
        doc["assets"].pop(a)
    doc["assets"].pop("a_part")
    doc["assets"]["a_roll"]["reproducibility"] = ["deterministic"]
    doc["assets"]["a_roll"]["tables"][0].pop("horizon_date_column")                              # a deterministic unit carries no horizon column
    assert fd.validate(doc, registry=None, schema=None, repo_root=None) == []
    full = fd.Declarations(doc=doc, sha256="8" * 64)
    assert full.drill_coverage()["scope"] == "all_declared_full"
    drill, _ = smd.build_drill(out_doc(full, "production"), out_doc(full, "rehearsal"), full, None, commit=SHA40)
    assert drill["result"] == "PASS" and sr.validate_drill(drill) == []


def test_a_group_is_one_unit_and_its_members_are_reported_together():
    prod, reh = _pair()
    _set_unit(reh, "grp_g_shared", H)
    drill, cov = smd.build_drill(prod, reh, D5, None, commit=SHA40)
    assert drill["result"] == "FAIL" and drill["unexplained"] == ["grp_g_shared"] and [d["asset"] for d in drill["differences"]] == ["grp_g_shared"]
    assert cov["unit_status"]["grp_g_shared"] == {"status": "fingerprint_differs", "members": ["a_gm1", "a_gm2"]}
    assert cov["differences_with_hints"][0]["members"] == ["a_gm1", "a_gm2"]
    ok, cov2 = smd.build_drill(prod, reh, D5, {"grp_g_shared": _ex(1, code="seeded_not_rebuilt")}, commit=SHA40)
    assert ok["result"] == "PASS_DECLARED_ONLY" and cov2["unit_status"]["grp_g_shared"]["members"] == ["a_gm1", "a_gm2"]


def test_an_unexplained_difference_fails_and_an_explained_one_with_a_decision_passes_scoped():
    prod, reh = _pair()
    _set_unit(reh, "a_roll", H)
    drill, cov = smd.build_drill(prod, reh, D5, None, commit=SHA40)
    assert drill["result"] == "FAIL" and drill["unexplained"] == ["a_roll"]
    assert cov["differences_with_hints"] == [{"asset": "a_roll", "kind": "fingerprint_differs", "members": ["a_roll"],
                                              "reproducibility": ["rolling_horizon", "platform_bound"], "table_notes": {}}]
    drill1, _ = smd.build_drill(prod, reh, D5, {"a_roll": _ex()}, commit=SHA40)                  # a rolling_horizon explanation needs the N-135 evidence
    assert drill1["result"] == "FAIL" and drill1["unexplained"] == ["a_roll"] and any("N-135" in x and "overlap fingerprints differ" in x for x in drill1["problems"])
    prod, reh = _pair()
    _later(reh, prod)
    drill2, _ = smd.build_drill(prod, reh, D5, {"a_roll": _ex()}, commit=SHA40)
    assert drill2["result"] == "PASS_DECLARED_ONLY" and drill2["differences"][0]["explained"]["decision"] == "N-135"
    no_dec = dict(_ex())
    del no_dec["decision"]
    assert smd.build_drill(prod, reh, D5, {"a_roll": no_dec}, commit=SHA40)[0]["result"] == "PASS_DECLARED_ONLY"      # decided by N-135 itself, on evidence


def test_rolling_horizon_and_platform_bound_codes_are_refused_for_a_deterministic_unit():
    prod, reh = _pair()
    _set_unit(reh, "a_0", H)
    for code in ("rolling_horizon",):
        r, _ = smd.build_drill(prod, reh, D5, {"a_0": _ex(code=code)}, commit=SHA40)
        assert r["result"] == "FAIL" and r["unexplained"] == ["a_0"] and any("flagged rolling_horizon" in x for x in r["problems"])
    miss = out_doc(D5, "rehearsal", assets=[u for u in D5.expected_assets() if u != "a_0"])
    r, _ = smd.build_drill(prod, miss, D5, {"a_0": _ex(code="source_unavailable_offline")}, commit=SHA40)
    assert r["result"] == "FAIL" and any("flagged platform_bound" in x for x in r["problems"])
    # the flagged unit may carry them (rolling_horizon with the N-135 evidence)
    _later(reh, prod)
    assert smd.build_drill(prod, {**reh, **{}}, D5, {"a_0": _ex(1, "zero", code="seeded_not_rebuilt"), "a_roll": _ex(2, "roll")}, commit=SHA40)[0]["result"] == "PASS_DECLARED_ONLY"


def test_too_many_differences_fail_even_when_each_is_explained():
    prod, reh = _pair()
    for i, a in enumerate(("a_0", "a_1", "a_2")):
        _set_unit(reh, a, hashlib.sha256(f"x{i}".encode()).hexdigest())
    ex = {a: _ex(i, a, code="seeded_not_rebuilt") for i, a in enumerate(("a_0", "a_1", "a_2"))}
    assert smd.build_drill(prod, reh, D5, ex, commit=SHA40)[0]["result"] == "FAIL"


def test_a_missing_unit_on_one_side_is_a_difference_not_a_silent_drop():
    prod, _ = _pair()
    reh = out_doc(D5, "rehearsal", assets=[a for a in D5.expected_assets() if a != "a_roll"])
    drill, _ = smd.build_drill(prod, reh, D5, None, commit=SHA40)
    assert drill["result"] == "FAIL" and drill["differences"][0]["kind"] == "missing_in_rehearsal" and drill["unexplained"] == ["a_roll"]
    assert drill["rows"]["a_roll"]["rehearsal"] is None


def test_a_unit_that_is_empty_on_both_sides_is_never_equal_and_the_verdict_is_unmeasured():
    prod, reh = _pair()
    for d in (prod, reh):
        _empty_unit(d, "a_multi")
    assert smd.validate_fingerprint_output(prod, D5, side="production") == [] and smd.validate_fingerprint_output(reh, D5, side="rehearsal") == []
    drill, cov = smd.build_drill(prod, reh, D5, None, commit=SHA40)
    assert drill["result"] == "UNMEASURED" and drill["empty_both_sides"] == ["a_multi"] and "a_multi" not in drill["equal"]
    assert cov["unit_status"]["a_multi"]["status"] == "empty_both_sides" and cov["empty_both_sides"] == ["a_multi"]
    assert sr.validate_drill(drill) == []


def test_equal_fingerprints_with_different_row_counts_are_a_refusal_in_the_compare():
    prod, reh = _pair()
    _set_unit(reh, "a_0", prod["tables"]["a_0"]["syn_t0"]["sha256"], rows=6)          # the same hash, one more row on the rehearsal side
    drill, _ = smd.build_drill(prod, reh, D5, None, commit=SHA40)
    assert drill["result"] == "FAIL" and "a_0" not in drill["equal"] and any("a_0: equal fingerprints but different row counts" in x for x in drill["problems"])


def test_a_hash_and_a_row_count_that_disagree_are_refused_per_side():
    for side in ("production", "rehearsal"):
        d = out_doc(D5, side)
        t = d["tables"]["a_0"]["syn_t0"]
        t["sha256"] = fd.empty_table_fingerprint(D5, "a_0", "syn_t0")                  # rows=5 but the empty-table hash
        d["fingerprints"]["a_0"] = t["sha256"]
        assert any("empty-table fingerprint" in x for x in smd.validate_fingerprint_output(d, D5, side=side))
        d = out_doc(D5, side)
        d["tables"]["a_0"]["syn_t0"]["rows"] = 0                                          # rows=0 but a non-empty hash
        assert any("rows=0" in x for x in smd.validate_fingerprint_output(d, D5, side=side))


@pytest.mark.parametrize("name,mutate", [
    ("as_of_differs", lambda p, r: r.update({"as_of": "2026-10-04"})),
    ("rehearsal_baseline_stage", lambda p, r: r.update({"stage": "baseline", "rebuild": None})),
    ("rebuild_commit_not_evidence_commit", lambda p, r: r["rebuild"].update({"orchestrator_commit": "2" * 40})),
    ("production_declarations_sha", lambda p, r: p.update({"declarations_sha256": H})),
    ("rehearsal_undeclared_asset", lambda p, r: (r["tables"].update({"a_und": {}}), r["fingerprints"].update({"a_und": H}))),
    ("rehearsal_group_member_is_no_unit", lambda p, r: (r["tables"].update({"a_gm1": {}}), r["fingerprints"].update({"a_gm1": H}))),
    ("production_definition", lambda p, r: p.update({"definition": "other/1"})),
    ("rebuild_run_id_is_nil", lambda p, r: r["rebuild"].update({"run_id": "00000000-0000-0000-0000-000000000000"})),
])
def test_build_drill_refuses_inconsistent_inputs(name, mutate):
    prod, reh = _pair()
    mutate(prod, reh)
    with pytest.raises(smd.MirrorError):
        smd.build_drill(prod, reh, D5, None, commit=SHA40)


def test_drill_uses_the_existing_comparison_and_defines_no_second_fingerprint():
    assert "sr.compare_fingerprint_sets" in SRC and "def fingerprint_rows" not in SRC and "def table_fingerprint" not in SRC
    assert "sr.fingerprint_set(" in SRC and "hashlib.sha256(canonical" not in SRC


# ═════════════════════════ 5. status, reader spec, the CLI hook ═════════════════════════

def test_real_uuid_accepts_only_canonical_rfc4122_ids():
    assert smd.real_uuid("5e57e57e-5e57-4e57-8e57-5e57e57e57e5") and smd.real_uuid(str(__import__("uuid").uuid4())) and smd.real_uuid(str(__import__("uuid").uuid1()))
    for bad in ("00000000-0000-0000-0000-000000000000", "-" * 36, "-" * 4, "", "x", None, 5, "5E57E57E-5E57-4E57-8E57-5E57E57E57E5",
                "5e57e57e5e574e578e575e57e57e57e5", "{5e57e57e-5e57-4e57-8e57-5e57e57e57e5}", "ffffffff-ffff-ffff-ffff-ffffffffffff",
                "5e57e57e-5e57-4e57-0e57-5e57e57e57e5"):
        assert not smd.real_uuid(bad), bad


def _record(decls=D5, run_id="5e57e57e-5e57-4e57-8e57-5e57e57e57e5", commit=SHA40, state="completed", **over):
    rec = {"schema": smd.BUILD_RECORD_SCHEMA, "run_id": run_id, "state": state, "orchestrator_commit": commit,
           "assets": [{"asset_id": a, "state": "complete"} for a in decls.declared_assets()]}
    rec.update(over)
    return rec


def test_a_rebuild_receipt_is_verified_only_against_a_matching_completed_build_record():
    receipt = {"run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "orchestrator_commit": SHA40, "runtime": dict(RUNTIME_OK)}
    assert smd.verify_rebuild_receipt(receipt, _record(), D5) == []
    cases = {
        "run id differs": _record(run_id="6e57e57e-5e57-4e57-8e57-5e57e57e57e5"), "not completed": _record(state="running"),
        "other commit": _record(commit="2" * 40), "other schema": _record(schema="x/v1"),
        "asset not complete": _record(assets=[{"asset_id": a, "state": "failed" if a == "a_0" else "complete"} for a in D5.declared_assets()]),
        "asset missing": _record(assets=[{"asset_id": a, "state": "complete"} for a in D5.declared_assets() if a != "a_roll"]),
        "extra key": {**_record(), "x": 1}, "assets not a list": _record(assets="x"), "asset shape": _record(assets=[{"asset_id": "a_0"}]),
    }
    for label, rec in cases.items():
        assert smd.verify_rebuild_receipt(receipt, rec, D5), label
    for bad in (None, {}, {"run_id": "x", "orchestrator_commit": SHA40}, {"run_id": "00000000-0000-0000-0000-000000000000", "orchestrator_commit": SHA40},
                {"run_id": receipt["run_id"]}):
        assert smd.verify_rebuild_receipt(bad, _record(), D5)
    assert smd.verify_rebuild_receipt(receipt, None, D5) and smd.verify_rebuild_receipt(receipt, [], D5)


def test_status_is_unmeasured_without_inputs_and_names_the_reasons():
    s = smd.drill_status(D5)
    assert s["result"] == "UNMEASURED" and "PASS" not in json.dumps(s)
    reasons = {x["step"]: x.get("reason") for x in s["steps"]}
    assert reasons["mirror_baseline"] == "NEEDS_MIRROR_BASELINE" and reasons["rehearsal_l0_rebuild"] == "NEEDS_REHEARSAL_ORCHESTRATOR_L0_RUN"
    assert reasons["production_fingerprints"] == "NEEDS_PRODUCTION_READER_DUMP" and reasons["linux_amd64_runtime"] == "NEEDS_LINUX_AMD64_RUNTIME"
    assert reasons["text_seed"] == "NEEDS_TEXT_SEED_CHECK" and reasons["ss_decisions"] == "NEEDS_DRILL_DOCUMENT" and reasons["as_of_pin"] == "NEEDS_AS_OF_PIN"
    assert {x["step"]: x["state"] for x in s["steps"]}["declarations"] == "MEASURED"
    assert "COMPLETE_INPUTS" not in SRC                                                            # the unreachable verdict is gone


def test_a_file_that_only_has_the_right_shape_is_never_measured():
    prod, reh = _pair()
    s = smd.drill_status(D5, baseline=_good_baseline(), production=prod, rehearsal=reh)
    st = {x["step"]: x["state"] for x in s["steps"]}
    assert st["mirror_baseline"] == st["production_fingerprints"] == st["as_of_pin"] == "SHAPE_CHECKED"
    assert st["rehearsal_l0_rebuild"] == "CLAIMED_UNVERIFIED"                      # a self-asserted receipt is a claim
    detail = {x["step"]: x.get("detail", {}) for x in s["steps"]}
    assert detail["rehearsal_l0_rebuild"]["unverified_because"] == ["no build record supplied"] and s["result"] == "UNMEASURED"
    assert st["text_seed"] == st["ss_decisions"] == "UNMEASURED"                                      # never inferable from files
    assert st["linux_amd64_runtime"] == "SHAPE_CHECKED" and detail["linux_amd64_runtime"]["runtime"] == RUNTIME_OK       # the receipt's runtime block is a claim, shape-checked
    assert {x["step"]: x["state"] for x in smd.drill_status(D5)["steps"]}["linux_amd64_runtime"] == "UNMEASURED"          # no rehearsal file: nothing to say
    dw = copy.deepcopy(reh)
    dw["rebuild"]["runtime"]["platform"] = "darwin/arm64"
    sd = {x["step"]: x for x in smd.drill_status(D5, rehearsal=dw)["steps"]}["linux_amd64_runtime"]
    assert sd["state"] == "CLAIMED_UNVERIFIED" and sd["reason"] == "NEEDS_LINUX_AMD64_RUNTIME" and "darwin/arm64" in sd["detail"]["note"]
    assert "MEASURED" not in [v for k, v in st.items() if k != "declarations"]
    # a record that does not match leaves it a claim; one that matches measures only the rebuild step
    s2 = smd.drill_status(D5, rehearsal=reh, build_record=_record(state="running"))
    assert {x["step"]: x["state"] for x in s2["steps"]}["rehearsal_l0_rebuild"] == "CLAIMED_UNVERIFIED"
    s3 = smd.drill_status(D5, baseline=_good_baseline(), production=prod, rehearsal=reh, build_record=_record())
    st3 = {x["step"]: x["state"] for x in s3["steps"]}
    assert st3["rehearsal_l0_rebuild"] == "MEASURED" and st3["production_fingerprints"] == "SHAPE_CHECKED" and st3["as_of_pin"] == "SHAPE_CHECKED"
    bad_reh = copy.deepcopy(reh)
    bad_reh["declarations_sha256"] = H
    s4 = smd.drill_status(D5, baseline=_good_baseline(), production=prod, rehearsal=bad_reh, build_record=_record())
    assert {x["step"]: x["state"] for x in s4["steps"]}["rehearsal_l0_rebuild"] == "UNMEASURED"
    bl = _good_baseline()
    bl["result"] = "FAIL"
    assert {x["step"]: x["state"] for x in smd.drill_status(D5, baseline=bl)["steps"]}["mirror_baseline"] == "UNMEASURED"
    base_stage = out_doc(D5, "rehearsal", stage="baseline", rebuild=None)
    assert {x["step"]: x["state"] for x in smd.drill_status(D5, rehearsal=base_stage)["steps"]}["rehearsal_l0_rebuild"] == "UNMEASURED"


def test_the_reader_and_rehearsal_files_are_read_strictly(tmp_path, capsys):
    prod, reh = _pair()
    good = json.dumps(prod)
    for name, text in (("dup.json", good.replace('"side": "production"', '"side": "production", "side": "rehearsal"', 1)),
                       ("nan.json", good.replace('"rows": 5', '"rows": NaN', 1)), ("inf.json", good.replace('"rows": 5', '"rows": Infinity', 1)),
                       ("junk.json", "{not json")):
        (tmp_path / name).write_text(text)
        with pytest.raises(Exception):
            smd._rd(tmp_path / name)
    (tmp_path / "reh.json").write_text(json.dumps(reh))
    (tmp_path / "dup.json").write_text(good.replace('"side": "production"', '"side": "production", "side": "rehearsal"', 1))
    assert smd.main(["status", "--production", str(tmp_path / "dup.json")]) == 2
    out = tmp_path / "drill.json"
    rc = smd.main(["compare", "--production", str(tmp_path / "dup.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--out", str(out)])
    assert rc == 2 and not out.exists()


def test_reader_spec_lists_exactly_the_unit_tables_and_aggregate_only_probes():
    spec = smd.reader_spec(D5)
    assert spec["selects"] == fd.reader_selects(D5) and len(spec["selects"]) == 10 and spec["role"] == "suvarna_reader"
    assert all(re.fullmatch(r'SELECT \* FROM "syn_[a-z0-9_]+"', s["sql"]) for s in spec["selects"])
    assert [s["table"] for s in spec["selects"] if s["asset"] == "grp_g_shared"] == ["syn_g"]
    assert not any(s["asset"] in ("a_und", "a_svc", "a_gm1", "a_gm2") for s in spec["selects"]) and set(spec["undeclared"]) == {"a_und", "a_svc"}
    assert spec["groups"] == {"grp_g_shared": ["a_gm1", "a_gm2"]}
    assert spec["declarations_sha256"] == D5.sha256 and spec["output"]["side"] == "production" and "aggregates only" in spec["output"]["contains"]
    for pr in smd.OWNERSHIP_PROBES:
        sql = pr["sql"]
        assert re.fullmatch(r"SELECT (?:[a-z_]+, )*count\(\*\) FROM [a-z_]+(?: GROUP BY [0-9, ]+)?", sql), sql          # aggregate-only, one statement
        assert ";" not in sql and "WHERE" not in sql and "*)" in sql and pr["outcome"]
    real = smd.reader_spec(fd.load_declarations())
    assert len(real["selects"]) == 63 and real["expected_differences"] == [] and real["projections"] == []
    assert {p["asset"] for p in smd.OWNERSHIP_PROBES} == {"bg_rules", "bg_transit_rules", "bg_gochara_citation_resolution", "bg_sarvatobhadra_grid"}
    assert "bg_rules" not in real["undeclared"] and {"bg_transit_rules", "bg_gochara_citation_resolution", "bg_sarvatobhadra_grid"} <= set(real["undeclared"])


def test_expected_status_and_reader_spec_never_open_a_connection(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("no connection may be opened")
    monkeypatch.setattr(sr, "_psycopg_connect", boom)
    monkeypatch.setattr(sr, "connect_checked", boom)
    monkeypatch.setattr(smd.subprocess, "run", boom)
    assert smd.main(["expected"]) == 0 and smd.main(["reader-spec"]) == 0 and smd.main(["status"]) == 0


def test_the_harness_expected_assets_are_the_comparison_units():
    assert sr.drill_expected_assets() == fd.load_declarations().expected_assets()
    assert len(sr.drill_expected_assets()) == 32 and "grp_brahma_ontology" in sr.drill_expected_assets() and "bg_ontology" not in sr.drill_expected_assets()


def test_the_harness_refuses_when_the_declarations_name_a_different_definition(monkeypatch):
    monkeypatch.setattr(fd, "FINGERPRINT_DEFINITION", "other/1")
    with pytest.raises(sr.RehearsalError):
        sr.drill_expected_assets()


def test_the_harness_refuses_invalid_declarations_with_exit_2_not_a_crash(tmp_path, capsys):
    bad = tmp_path / "d.json"
    bad.write_text(json.dumps({"schema": "x"}))
    with pytest.raises(sr.RehearsalError, match="refused"):
        sr.drill_expected_assets(bad)
    with pytest.raises(sr.RehearsalError):
        sr.drill_expected_assets(tmp_path / "absent.json")


def test_harness_drill_subcommand_delegates(capsys):
    assert sr.main(["drill", "status"]) == 0
    assert json.loads(capsys.readouterr().out)["result"] == "UNMEASURED"
    assert sr.main(["drill", "expected"]) == 0
    assert json.loads(capsys.readouterr().out)["expected_assets"] == sr.drill_expected_assets()


def _rows_file(units, decls, n=5):
    return {u: {"production": {t: n for t in decls.tables(u)}, "rehearsal": {t: n for t in decls.tables(u)}} for u in units}


def test_compare_fingerprints_cli_accepts_expected_declarations(tmp_path, capsys):
    decls = fd.load_declarations()
    units = decls.expected_assets()
    fps = {a: hashlib.sha256(a.encode()).hexdigest() for a in units}
    p = tmp_path / "p.json"
    p.write_text(json.dumps(sr.fingerprint_set(fps)))
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps(_rows_file(units, decls)))
    out = tmp_path / "drill.json"
    rt = tmp_path / "rt.json"
    rt.write_text(json.dumps(RUNTIME_OK))
    base = ["compare-fingerprints", "--pre", str(p), "--post", str(p), "--expected", "declarations", "--rows", str(rows), "--runtime", str(rt), "--commit", SHA40, "--out", str(out)]
    assert sr.main(base) == 0
    doc = json.loads(out.read_text())
    assert doc["result"] == "PASS_DECLARED_ONLY" and doc["expected_assets"] == units and sr.validate_drill(doc) == []
    assert doc["coverage"] == decls.drill_coverage()
    assert sr.main(["validate-drill", str(out), "--declarations"]) == 0                     # bound to the committed declarations
    capsys.readouterr()
    p2 = tmp_path / "p2.json"
    p2.write_text(json.dumps(sr.fingerprint_set({**fps, "bg_panchanga": H})))               # an undeclared asset is `unexpected`: FAIL
    rows2 = tmp_path / "rows2.json"
    rows2.write_text(json.dumps({**_rows_file(units, decls), "bg_panchanga": {"production": {"t": 1}, "rehearsal": {"t": 1}}}))
    assert sr.main(["compare-fingerprints", "--pre", str(p), "--post", str(p2), "--expected", "declarations", "--rows", str(rows2), "--runtime", str(rt), "--commit", SHA40]) == 4
    assert sr.main(["compare-fingerprints", "--pre", str(p), "--post", str(p), "--expected", str(tmp_path / "x.json"), "--rows", str(rows), "--runtime", str(rt), "--commit", SHA40]) == 2   # no --coverage


def test_validate_drill_cli_rejects_a_drill_made_under_other_declarations(tmp_path, capsys):
    decls = fd.load_declarations()
    units = decls.expected_assets()
    fps = {a: hashlib.sha256(a.encode()).hexdigest() for a in units}
    drill = sr.compare_fingerprint_sets(sr.fingerprint_set(fps), sr.fingerprint_set(fps), expected_assets=units, commit=SHA40,
                                        coverage={**decls.drill_coverage(), "undeclared": {"bg_x": "no_table"}}, rows=_rows_file(units, decls), runtime=dict(RUNTIME_OK))
    p = tmp_path / "d.json"
    p.write_text(json.dumps(drill))
    assert sr.main(["validate-drill", str(p)]) == 0                                          # internally consistent
    assert sr.main(["validate-drill", str(p), "--declarations"]) == 2                          # but not the committed declarations'
    capsys.readouterr()


def test_drill_cli_compare_writes_the_drill_and_the_coverage_report(tmp_path, capsys, monkeypatch):
    decls = fd.load_declarations()
    prod, reh = out_doc(decls, "production"), out_doc(decls, "rehearsal")
    for n, d in (("prod", prod), ("reh", reh)):
        (tmp_path / f"{n}.json").write_text(json.dumps(d))
    out = tmp_path / "L0_REBUILD_DRILL.json"
    rc = smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--out", str(out)])
    assert rc == 0
    drill = json.loads(out.read_text())
    cov = json.loads((tmp_path / "L0_REBUILD_DRILL.json.coverage.json").read_text())
    assert drill["result"] == "PASS_DECLARED_ONLY" and sr.validate_drill(drill) == [] and drill["coverage"] == decls.drill_coverage()
    assert sorted(cov["undeclared"]) == sorted(decls.undeclared_assets()) and sorted(cov["partial"]) == sorted(decls.partial_assets())
    printed = json.loads(capsys.readouterr().out)
    assert printed["undeclared"] == sorted(decls.undeclared_assets()) and printed["partial"] == sorted(decls.partial_assets())
    assert printed["scope"] == "declared_only" and set(printed["groups"]) == {"grp_brahma_class_priors", "grp_brahma_ontology", "grp_classical_text_chunks"}
    assert printed["expected_differences"] == [] and printed["resolved_findings"][0].startswith("9. (resolved) bg_ephemeris writer did not write node_mode/epoch_convention")
    (tmp_path / "reh2.json").write_text(json.dumps({**reh, "as_of": "2026-01-01"}))
    assert smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh2.json"), "--commit", SHA40, "--out", str(out)]) == 2


def test_a_rebuild_that_nulls_the_ephemeris_node_columns_is_a_real_mismatch_now_that_3015_is_on_main(tmp_path, capsys):
    decls = fd.load_declarations()
    assert decls.expected_differences() == [] and decls.projection_tables() == {} and decls.drill_coverage()["expected_differences"] == []
    assert out_doc(decls, "production")["projections"] == {}
    prod, reh = out_doc(decls, "production"), out_doc(decls, "rehearsal")
    _set = lambda d, u: [d["tables"][u][t].update(sha256=hashlib.sha256(f"{u}{t}x".encode()).hexdigest()) for t in d["tables"][u]]  # noqa: E731
    _set(reh, "bg_ephemeris")
    reh["fingerprints"]["bg_ephemeris"] = reh["tables"]["bg_ephemeris"]["ephemeris_daily"]["sha256"]
    drill, cov = smd.build_drill(prod, reh, decls, None, commit=SHA40)
    assert drill["result"] == "FAIL" and drill["unexplained"] == ["bg_ephemeris"] and "bg_ephemeris" not in drill["equal"]       # nothing expected: a real mismatch
    assert drill["known_differences"] == [] and drill["projections"] == {} and cov["expected_differences_status"] == [] and cov["known_differences"] == []
    assert cov["differences_with_hints"][0]["asset"] == "bg_ephemeris" and sr.validate_drill(drill) == []
    # the equal drill is the expected one: the unit is equal, nothing is known, nothing is open about it
    de, ce = smd.build_drill(prod, out_doc(decls, "rehearsal"), decls, None, commit=SHA40)
    assert "bg_ephemeris" in de["equal"] and de["known_differences"] == [] and "ephemeris_daily" not in json.dumps(ce["expected_differences_status"])
    assert not any("bg_ephemeris" in f and "9." in f[:3] for f in ce["open_findings"]) and ce["resolved_findings"] == list(smd.RESOLVED_FINDINGS)


def test_the_real_declarations_cover_the_real_drill_end_to_end_offline():
    """All 32 comparison units through the whole pure pipeline (no database): equal sides pass scoped; the text group is SEEDED and not counted."""
    decls = fd.load_declarations()
    prod, reh = out_doc(decls, "production"), out_doc(decls, "rehearsal")
    drill, cov = smd.build_drill(prod, reh, decls, None, commit=SHA40)
    assert drill["result"] == "PASS_DECLARED_ONLY" and len(drill["expected_assets"]) == 32 and len(cov["undeclared"]) == 6
    assert len(drill["equal"]) == 31 and "grp_classical_text_chunks" not in drill["equal"] and sorted(cov["partial"]) == ["bg_remedies", "bg_texts"]
    assert drill["seeded"] == {"grp_classical_text_chunks": "equal"} and drill["coverage"]["seeded"] == ["grp_classical_text_chunks"]
    assert cov["unit_status"]["grp_classical_text_chunks"] == {"status": "seeded:equal", "members": ["bg_text_index", "bg_texts"]}


def test_the_headline_next_to_the_result_prints_the_numbers_and_the_names():
    decls = fd.load_declarations()
    drill, cov = smd.build_drill(out_doc(decls, "production"), out_doc(decls, "rehearsal"), decls, None, commit=SHA40)
    h = cov["headline"]
    assert h.startswith("PASS_DECLARED_ONLY: 34 of 40 L0 assets declared (32 full, 2 partial: bg_remedies (not covered: remedy_review_queue); bg_texts (not covered: classical_texts))")
    assert "6 undeclared: bg_compendium_index, bg_ephemeris_engine, bg_gochara_citation_resolution, bg_panchanga, bg_sarvatobhadra_grid, bg_transit_rules" in h
    assert "3 non-deterministic: bg_cohort ['platform_bound'], bg_muhurta_lattice ['rolling_horizon'], bg_sky_calendar ['rolling_horizon', 'platform_bound']" in h
    assert "1 SEEDED (shown, not counted toward the verdict): grp_classical_text_chunks [equal]" in h and "32 comparison units, 31 in the rebuilt-equals-source claim" in h
    assert cov["seeded_status"] == {"grp_classical_text_chunks": "equal"}
    assert len(cov["limits"]) == 3 and any("STATEMENT level" in x and "cannot tell WHICH column a clock call feeds" in x and "post-J1" in x for x in cov["limits"])
    assert any("SEEDED units" in x and "never counted" in x and "does not by itself fail" in x for x in cov["limits"])
    assert any("bare PASS is reserved for full coverage" in x for x in cov["limits"])


def test_the_headline_for_a_fully_covered_declarations_file_says_zero_everywhere():
    cov = {"declared": ["a", "b"], "partial": {}, "undeclared": {}, "non_deterministic": {}, "seeded": [], "units": ["a", "b"]}
    assert smd.coverage_headline("PASS", cov, 2) == ("PASS: 2 of 2 L0 assets declared (2 full, 0 partial); 0 undeclared; 0 non-deterministic; "
                                                     "0 SEEDED (shown, not counted toward the verdict); 0 partial-ownership units (partial: writer-only rows compared; the whole table is fingerprinted, "
                                                     "a difference is the expected migration_owned_rows); 0 not-run units, UNMEASURED (never equal, never counted toward the verdict; not_run_declared, N-121); "
                                                     "2 comparison units, 2 in the rebuilt-equals-source claim.")


def test_the_compare_cli_prints_coverage_names_limits_and_seeded_next_to_the_result(tmp_path, capsys):
    decls = fd.load_declarations()
    for n, d in (("prod", out_doc(decls, "production")), ("reh", out_doc(decls, "rehearsal"))):
        (tmp_path / f"{n}.json").write_text(json.dumps(d))
    out = tmp_path / "drill.json"
    assert smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--out", str(out)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["result"] == "PASS_DECLARED_ONLY" and printed["headline"].startswith("PASS_DECLARED_ONLY: 34 of 40")
    assert len(printed["declared"]) == 34 and printed["seeded"] == {"grp_classical_text_chunks": "equal"} and sorted(printed["non_deterministic"]) == ["bg_cohort", "bg_muhurta_lattice", "bg_sky_calendar"]
    assert any("STATEMENT level" in x for x in printed["limits"])
    rep = json.loads((tmp_path / "drill.json.coverage.json").read_text())
    assert rep["headline"] == printed["headline"] and rep["limits"] == printed["limits"]


def _seeded_decls(seeded=True):
    doc = syn_doc(seeded)
    for a in list(doc["assets"]):
        if a not in ("a_gm1", "a_gm2", "a_svc", "a_und"):
            doc["assets"].pop(a)
    assert fd.validate(doc, registry=None, schema=None, repo_root=None) == []
    return fd.Declarations(doc=doc, sha256="6" * 64)


def test_a_seeded_group_is_shown_but_never_counted_in_the_drill():
    ds = syn_decls(seeded_group=True)
    assert ds.seeded_units() == ["grp_g_shared"] and ds.drill_coverage()["seeded"] == ["grp_g_shared"] and ds.units()["grp_g_shared"]["seeded"] is True
    prod, reh = out_doc(ds, "production"), out_doc(ds, "rehearsal")
    drill, cov = smd.build_drill(prod, reh, ds, None, commit=SHA40)
    assert drill["result"] == "PASS_DECLARED_ONLY" and "grp_g_shared" not in drill["equal"] and len(drill["equal"]) == 8 and drill["seeded"] == {"grp_g_shared": "equal"}
    assert cov["unit_status"]["grp_g_shared"] == {"status": "seeded:equal", "members": ["a_gm1", "a_gm2"]} and sr.validate_drill(drill) == []
    # the seeded unit differs: reported, not unexplained, the rebuild claim stands
    _set_unit(reh, "grp_g_shared", H)
    d2, c2 = smd.build_drill(prod, reh, ds, None, commit=SHA40)
    assert d2["result"] == "PASS_DECLARED_ONLY" and [x["asset"] for x in d2["differences"]] == ["grp_g_shared"] and d2["unexplained"] == []
    assert c2["unit_status"]["grp_g_shared"]["status"] == "seeded:fingerprint_differs" and c2["differences_with_hints"][0]["members"] == ["a_gm1", "a_gm2"]
    assert "[fingerprint_differs]" in c2["headline"]
    # the same drill with the group NOT seeded fails on that difference
    plain = syn_decls(seeded_group=False)
    prod_p, reh_p = out_doc(plain, "production"), out_doc(plain, "rehearsal")
    _set_unit(reh_p, "grp_g_shared", H)
    assert smd.build_drill(prod_p, reh_p, plain, None, commit=SHA40)[0]["result"] == "FAIL"


def test_a_drill_whose_only_equal_unit_is_the_seeded_group_reads_unmeasured():
    only = _seeded_decls(True)
    assert only.expected_assets() == ["grp_g_shared"]
    drill, cov = smd.build_drill(out_doc(only, "production"), out_doc(only, "rehearsal"), only, None, commit=SHA40)
    assert drill["result"] == "UNMEASURED" and drill["equal"] == [] and drill["seeded"] == {"grp_g_shared": "equal"} and sr.validate_drill(drill) == []
    assert cov["headline"].startswith("UNMEASURED:")
    unseeded = _seeded_decls(False)
    assert smd.build_drill(out_doc(unseeded, "production"), out_doc(unseeded, "rehearsal"), unseeded, None, commit=SHA40)[0]["result"] == "PASS_DECLARED_ONLY"


def test_the_real_text_group_is_seeded_and_no_other_group_is():
    d = fd.load_declarations()
    assert {g: v["seeded"] for g, v in d.groups.items()} == {"brahma_ontology": False, "brahma_class_priors": False, "classical_text_chunks": True}
    assert d.seeded_units() == ["grp_classical_text_chunks"] and d.drill_coverage()["scope"] == "declared_only"
    assert all(not v["seeded"] for u, v in d.units().items() if v["kind"] == "asset")


def test_status_states_the_exact_build_record_it_expects(capsys):
    s = smd.drill_status(D5)
    exp = s["build_record_expected"]
    assert exp["schema"] == "suvarna-build-record/v1" and "--build-record PATH" in exp["flag"] and set(exp["required_fields"]) == {"schema", "run_id", "state", "orchestrator_commit", "assets"}
    assert exp["declared_assets_that_must_be_complete"] == D5.declared_assets() and "no other top-level key" in exp["closed"]
    assert exp["declared_assets_that_may_be_not_run"] == {}
    assert "CLAIMED_UNVERIFIED" in exp["purpose"]
    assert any("build_record_expected" in x["detail"].get("expects", "") for x in s["steps"] if x["step"] == "rehearsal_l0_rebuild")
    # a record written exactly from the spec verifies (the spec and the verifier agree)
    ex = exp["shape_example"]
    assert set(ex) == set(exp["required_fields"]) and ex["schema"] == smd.BUILD_RECORD_SCHEMA and ex["assets"][1]["state"] == "not_run"
    rec = {**ex, "run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "orchestrator_commit": SHA40,
           "assets": [{"asset_id": a, "state": "complete"} for a in exp["declared_assets_that_must_be_complete"]]}
    assert smd.verify_rebuild_receipt({"run_id": rec["run_id"], "orchestrator_commit": SHA40, "runtime": dict(RUNTIME_OK)}, rec, D5) == []
    assert smd.verify_rebuild_receipt({"run_id": rec["run_id"], "orchestrator_commit": SHA40, "runtime": dict(RUNTIME_OK)}, {**rec, "extra": 1}, D5)
    # the claimed step says what to supply
    prod, reh = _pair()
    claimed = {x["step"]: x for x in smd.drill_status(D5, rehearsal=reh)["steps"]}["rehearsal_l0_rebuild"]
    assert claimed["state"] == "CLAIMED_UNVERIFIED" and "--build-record PATH" in claimed["detail"]["expects"]
    assert smd.main(["build-record-spec"]) == 0
    real = json.loads(capsys.readouterr().out)
    assert real["schema"] == "suvarna-build-record/v1" and len(real["declared_assets_that_must_be_complete"]) == 31 and "bg_ontology" in real["declared_assets_that_must_be_complete"]
    assert real["declared_assets_that_may_be_not_run"] == {a: v for a, v in smd.NOT_RUN_ALLOWED.items()} and not set(real["declared_assets_that_may_be_not_run"]) & set(real["declared_assets_that_must_be_complete"])
    assert smd.main(["status"]) == 0 and json.loads(capsys.readouterr().out)["build_record_expected"]["schema"] == "suvarna-build-record/v1"


# ═════════════════ round 4: not_run, partial ownership, open findings, the config seed ═════════════════

RD = fd.load_declarations()

# The committed declarations carry no expected-difference record any more (#3015 is on main: the rebuild writes node_mode/epoch_convention), but the MECHANISM
# stays in the code: these tests exercise it on a SYNTHETIC record installed on bg_ephemeris/ephemeris_daily (the same record the declarations tests use).
SYN_ED = {"columns": ["node_mode", "epoch_convention"], "reference": "synthetic tracked change (test fixture)",
          "detail": "a synthetic known difference limited to the two columns, used to exercise the expected-difference mechanism in tests",
          "until": "the synthetic tracked change is merged: remove this record"}


def _ed_doc():
    doc = json.loads(fd.DEFAULT_DECLARATIONS.read_text(encoding="utf-8"))
    next(t for t in doc["assets"]["bg_ephemeris"]["tables"] if t["name"] == "ephemeris_daily")["expected_difference"] = copy.deepcopy(SYN_ED)
    return doc


def _decls_with_ed():
    doc = _ed_doc()
    return fd.Declarations(doc=doc, sha256=hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest())


RD_ED = _decls_with_ed()


def _rrec(over=None, *, drop=(), extra=(), **top):
    """A build record over the REAL declarations: every declared asset complete, the three allowed ones not_run with their reasons."""
    assets = []
    for a in RD.declared_assets():
        if a in drop:
            continue
        assets.append({"asset_id": a, "state": "not_run", "reason": smd.NOT_RUN_ALLOWED[a]["reason"]} if a in smd.NOT_RUN_ALLOWED else {"asset_id": a, "state": "complete"})
    for a, e in (over or {}).items():
        assets = [e if x["asset_id"] == a else x for x in assets]
    assets += list(extra)
    rec = {"schema": smd.BUILD_RECORD_SCHEMA, "run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "state": "completed", "orchestrator_commit": SHA40, "assets": assets}
    rec.update(top)
    return rec


RECEIPT = {"run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "orchestrator_commit": SHA40, "runtime": dict(RUNTIME_OK)}


def test_the_not_run_list_is_closed_and_every_entry_has_a_needs_reason_and_a_decision():
    assert set(smd.NOT_RUN_ALLOWED) == {"bg_sky_calendar", "bg_cohort", "bg_muhurta_lattice"}                  # bg_gochara_arcs runs now: it is not on the list
    assert {a: v["reason"] for a, v in smd.NOT_RUN_ALLOWED.items()} == {"bg_sky_calendar": "NEEDS_LINUX_AMD64_RUNTIME", "bg_cohort": "NEEDS_LINUX_AMD64_RUNTIME",
                                                                         "bg_muhurta_lattice": "NEEDS_AS_OF_PIN"}
    assert all(set(v) == {"reason", "decision"} and v["reason"].startswith("NEEDS_") and v["decision"] == "N-121" for v in smd.NOT_RUN_ALLOWED.values())
    assert smd.NOT_RUN_ALLOWED is fd.NOT_RUN_ALLOWED and RD.not_run_allowed() == {a: v["reason"] for a, v in smd.NOT_RUN_ALLOWED.items()}
    assert RD.drill_coverage()["not_run_allowed"] == RD.not_run_allowed() and RD.coverage_report()["not_run_allowed"] == RD.not_run_allowed()
    assert set(smd.NOT_RUN_ALLOWED) <= set(RD.declared_assets()) and set(smd.RECORD_STATES) == {"complete", "not_run", "failed", "error", "incomplete", "blocked", "skipped"}


def test_bg_gochara_arcs_runs_now_so_it_must_be_complete_and_no_not_run_reason_is_accepted_for_it():
    assert "bg_gochara_arcs" not in smd.NOT_RUN_ALLOWED and "bg_gochara_arcs" not in RD.not_run_allowed() and "bg_gochara_arcs" in smd.build_record_spec(RD)["declared_assets_that_must_be_complete"]
    ok = _rrec()
    assert [x for x in ok["assets"] if x["asset_id"] == "bg_gochara_arcs"] == [{"asset_id": "bg_gochara_arcs", "state": "complete"}]
    assert smd.verify_rebuild_receipt(RECEIPT, ok, RD) == []
    for reason in ("NEEDS_PR_3015", "NEEDS_AS_OF_PIN", "NEEDS_LINUX_AMD64_RUNTIME", "waiting for 3015", ""):
        probs = smd.verify_rebuild_receipt(RECEIPT, _rrec({"bg_gochara_arcs": {"asset_id": "bg_gochara_arcs", "state": "not_run", "reason": reason}}), RD)
        assert any("bg_gochara_arcs is not_run but is not in the closed not_run list" in x for x in probs), reason
    assert smd.verify_rebuild_receipt(RECEIPT, _rrec({"bg_gochara_arcs": {"asset_id": "bg_gochara_arcs", "state": "not_run"}}), RD)               # no reason
    assert smd.verify_rebuild_receipt(RECEIPT, _rrec({"bg_gochara_arcs": {"asset_id": "bg_gochara_arcs", "state": "failed"}}), RD)               # a failure is never accepted
    # the retired reason code is accepted for no asset
    for other in ("bg_ephemeris", "bg_ghatana", "bg_nakshatra", "bg_ontology", "bg_sky_calendar", "bg_cohort", "bg_muhurta_lattice"):
        assert smd.verify_rebuild_receipt(RECEIPT, _rrec({other: {"asset_id": other, "state": "not_run", "reason": "NEEDS_PR_3015"}}), RD), other


def test_a_record_with_the_allowed_not_run_assets_and_everything_else_complete_verifies():
    assert smd.verify_rebuild_receipt(RECEIPT, _rrec(), RD) == []
    ok_complete = _rrec({"bg_cohort": {"asset_id": "bg_cohort", "state": "complete"}})                    # an allowed asset that DID run is fine
    assert smd.verify_rebuild_receipt(RECEIPT, ok_complete, RD) == []
    undeclared_too = _rrec(extra=[{"asset_id": "bg_panchanga", "state": "skipped"}])                       # an undeclared L0 asset may carry any known state
    assert smd.verify_rebuild_receipt(RECEIPT, undeclared_too, RD) == []


@pytest.mark.parametrize("label,rec", [
    ("not_run_outside_the_list", _rrec({"bg_ephemeris": {"asset_id": "bg_ephemeris", "state": "not_run", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}})),
    ("not_run_without_reason", _rrec({"bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "not_run"}})),
    ("not_run_wrong_reason", _rrec({"bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "not_run", "reason": "NEEDS_AS_OF_PIN"}})),
    ("not_run_free_text_reason", _rrec({"bg_muhurta_lattice": {"asset_id": "bg_muhurta_lattice", "state": "not_run", "reason": "too slow"}})),
    ("reason_on_a_complete_entry", _rrec({"bg_ephemeris": {"asset_id": "bg_ephemeris", "state": "complete", "reason": "NEEDS_X"}})),
    ("failed_asset_not_the_listed_one", _rrec({"bg_ghatana": {"asset_id": "bg_ghatana", "state": "failed"}})),
    ("errored_asset", _rrec({"bg_formula_constants": {"asset_id": "bg_formula_constants", "state": "error"}})),
    ("failed_asset_with_a_not_run_reason", _rrec({"bg_ghatana": {"asset_id": "bg_ghatana", "state": "failed", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}})),
    ("failed_listed_asset", _rrec({"bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "failed", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}})),
    ("errored_listed_asset", _rrec({"bg_cohort": {"asset_id": "bg_cohort", "state": "error"}})),
    ("incomplete_asset", _rrec({"bg_nakshatra": {"asset_id": "bg_nakshatra", "state": "incomplete"}})),
    ("blocked_asset", _rrec({"bg_reference": {"asset_id": "bg_reference", "state": "blocked"}})),
    ("skipped_asset", _rrec({"bg_doshas": {"asset_id": "bg_doshas", "state": "skipped"}})),
    ("declared_asset_missing", _rrec(drop=("bg_ephemeris",))),
    ("listed_asset_missing", _rrec(drop=("bg_sky_calendar",))),
    ("duplicate_asset", _rrec(extra=[{"asset_id": "bg_ephemeris", "state": "complete"}])),
    ("unknown_asset", _rrec(extra=[{"asset_id": "bg_not_an_asset", "state": "complete"}])),
    ("unknown_state", _rrec({"bg_nakshatra": {"asset_id": "bg_nakshatra", "state": "lit"}})),
    ("extra_key_in_an_entry", _rrec({"bg_nakshatra": {"asset_id": "bg_nakshatra", "state": "complete", "x": 1}})),
    ("entry_without_state", _rrec({"bg_nakshatra": {"asset_id": "bg_nakshatra"}})),
    ("run_not_completed", _rrec(state="running")),
])
def test_the_build_record_refuses(label, rec):
    assert smd.verify_rebuild_receipt(RECEIPT, rec, RD), label


def test_a_failed_asset_is_never_accepted_as_complete_or_as_not_run_and_the_message_says_so():
    probs = smd.verify_rebuild_receipt(RECEIPT, _rrec({"bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "failed", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}}), RD)
    assert any("bg_sky_calendar is failed" in x and "never accepted as complete or as not_run" in x for x in probs)
    probs = smd.verify_rebuild_receipt(RECEIPT, _rrec({"bg_ephemeris": {"asset_id": "bg_ephemeris", "state": "not_run", "reason": "NEEDS_AS_OF_PIN"}}), RD)
    assert any("bg_ephemeris is not_run but is not in the closed not_run list" in x and "cannot become not_run" in x for x in probs)


# ═════════════════ round 5: the explanation code not_run_declared (decision N-121) ═════════════════

NOT_RUN_UNITS = ("bg_cohort", "bg_muhurta_lattice", "bg_sky_calendar")


def _rrec_nr(units=(), **kw):
    """A build record in which only `units` of the closed list are not_run; every other listed asset is complete (it ran)."""
    return _rrec({u: {"asset_id": u, "state": "complete"} for u in smd.NOT_RUN_ALLOWED if u not in units}, **kw)
NR_DETAIL = "the rebuild did not run this asset: the build record lists it not_run with its closed-list NEEDS_ reason (N-121) [%s]"


def _nr_expl(units=("bg_muhurta_lattice",), code="not_run_declared"):
    return {u: {"reason_code": code, "detail": NR_DETAIL % u} for u in units}


def _nr_pair(missing=NOT_RUN_UNITS):
    prod = out_doc(RD, "production")
    reh = out_doc(RD, "rehearsal", assets=[u for u in RD.expected_assets() if u not in missing])
    return prod, reh


def test_not_run_declared_covers_the_muhurta_lattice_gap_and_the_unit_stays_unmeasured():
    prod, reh = _nr_pair()
    expl = {**_nr_expl(), **{u: {"reason_code": "source_unavailable_offline", "detail": NR_DETAIL % u, "decision": "N-121"} for u in ("bg_cohort", "bg_sky_calendar")}}
    drill, cov = smd.build_drill(prod, reh, RD, expl, commit=SHA40, build_record=_rrec())
    assert drill["result"] == "PASS_DECLARED_ONLY" and drill["problems"] == [] and drill["unexplained"] == []
    assert drill["unmeasured"] == ["bg_muhurta_lattice"] and "bg_muhurta_lattice" not in drill["equal"] and len(drill["equal"]) == 28
    assert drill["not_run"] == {u: smd.NOT_RUN_ALLOWED[u]["reason"] for u in NOT_RUN_UNITS} and sr.validate_drill(drill) == []
    assert cov["unit_status"]["bg_muhurta_lattice"]["status"] == "UNMEASURED:not_run_declared" and cov["unit_status"]["bg_muhurta_lattice"]["reason"] == "NEEDS_AS_OF_PIN"
    assert cov["unmeasured"] == ["bg_muhurta_lattice"] and cov["not_run"] == drill["not_run"]
    assert "1 not-run units, UNMEASURED (never equal, never counted toward the verdict; not_run_declared, N-121): bg_muhurta_lattice [NEEDS_AS_OF_PIN]" in cov["headline"]
    assert "bg_gochara_arcs" in drill["equal"]                                                                 # it runs now and is compared like any other unit
    # a platform-bound unit may use either code; the three together are three UNMEASURED units, still never a bare PASS
    drill3, cov3 = smd.build_drill(prod, reh, RD, _nr_expl(NOT_RUN_UNITS), commit=SHA40, build_record=_rrec())
    assert drill3["result"] == "PASS_DECLARED_ONLY" and drill3["unmeasured"] == list(NOT_RUN_UNITS) and len(drill3["equal"]) == 28
    assert "3 not-run units, UNMEASURED" in cov3["headline"]


def test_not_run_declared_is_refused_without_a_record_for_a_complete_asset_or_an_unlisted_unit():
    prod, reh = _nr_pair(("bg_muhurta_lattice",))
    d, _ = smd.build_drill(prod, reh, RD, _nr_expl(), commit=SHA40)                                      # no build record at all
    assert d["result"] == "FAIL" and d["unmeasured"] == [] and any("no `not_run` entry" in x for x in d["problems"])
    done = _rrec_nr(())                                                                                  # the record says the asset ran
    d, _ = smd.build_drill(prod, reh, RD, _nr_expl(), commit=SHA40, build_record=done)
    assert d["result"] == "FAIL" and d["unmeasured"] == [] and d["unexplained"] == ["bg_muhurta_lattice"] and any("no `not_run` entry" in x for x in d["problems"])
    prod2, reh2 = _nr_pair(("bg_ephemeris",))                                                                  # a unit outside the closed list
    d, _ = smd.build_drill(prod2, reh2, RD, _nr_expl(("bg_ephemeris",)), commit=SHA40, build_record=_rrec_nr(()))
    assert d["result"] == "FAIL" and d["unmeasured"] == [] and any("not in the closed not_run list" in x for x in d["problems"])
    prod3, reh3 = _nr_pair(("bg_ghatana",))                                                                    # missing for another reason, record says complete
    d, _ = smd.build_drill(prod3, reh3, RD, _nr_expl(("bg_ghatana",)), commit=SHA40, build_record=_rrec_nr(()))
    assert d["result"] == "FAIL" and d["unmeasured"] == []
    rec_diff = out_doc(RD, "rehearsal")                                                                        # the unit was built (fingerprint present) yet the record says not_run
    d, _ = smd.build_drill(out_doc(RD, "production"), rec_diff, RD, None, commit=SHA40, build_record=_rrec())
    assert d["result"] == "FAIL" and any("the build record says not_run but the rehearsal has a fingerprint" in x for x in d["problems"])


def test_a_build_record_that_does_not_verify_refuses_the_comparison_and_accepts_nothing():
    prod, reh = _nr_pair(("bg_muhurta_lattice",))
    for label, rec in (("failed_asset", _rrec({"bg_ghatana": {"asset_id": "bg_ghatana", "state": "failed"}})),
                       ("outside_list", _rrec({"bg_ephemeris": {"asset_id": "bg_ephemeris", "state": "not_run", "reason": "NEEDS_AS_OF_PIN"}})),
                       ("wrong_reason", _rrec({"bg_muhurta_lattice": {"asset_id": "bg_muhurta_lattice", "state": "not_run", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}})),
                       ("other_run", _rrec(run_id="6e57e57e-5e57-4e57-8e57-5e57e57e57e5")),
                       ("incomplete_run", _rrec(state="running"))):
        with pytest.raises(smd.MirrorError, match="build record"):
            smd.build_drill(prod, reh, RD, _nr_expl(), commit=SHA40, build_record=rec)


def test_not_run_declared_through_the_compare_cli_and_its_report_file(tmp_path, capsys):
    prod, reh = _nr_pair(("bg_muhurta_lattice",))
    rec = _rrec_nr(("bg_muhurta_lattice",))
    files = {"prod": prod, "reh": reh, "expl": _nr_expl(), "rec": rec}
    for n, d in files.items():
        (tmp_path / f"{n}.json").write_text(json.dumps(d))
    out = tmp_path / "drill.json"
    base = ["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--out", str(out)]
    assert smd.main(base + ["--explained", str(tmp_path / "expl.json"), "--build-record", str(tmp_path / "rec.json")]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["result"] == "PASS_DECLARED_ONLY" and printed["unmeasured"] == ["bg_muhurta_lattice"] and printed["not_run"] == {"bg_muhurta_lattice": "NEEDS_AS_OF_PIN"}
    assert "not-run units, UNMEASURED" in printed["headline"]
    report = json.loads((tmp_path / "drill.json.coverage.json").read_text())
    assert report["unmeasured"] == ["bg_muhurta_lattice"] and report["unit_status"]["bg_muhurta_lattice"]["status"] == "UNMEASURED:not_run_declared"
    assert smd.main(base + ["--explained", str(tmp_path / "expl.json")]) == 4                                 # without the record the code is refused
    assert json.loads(capsys.readouterr().out)["result"] == "FAIL"


# ═════════════════ round 7: the runtime block of the receipt, the container expectation, platform-bound units ═════════════════

RT_BAD = [None, {}, "linux/amd64", {**RUNTIME_OK, "extra": 1}, {k: v for k, v in RUNTIME_OK.items() if k != "collation"}, {**RUNTIME_OK, "platform": "linux"},
          {**RUNTIME_OK, "os": ""}, {**RUNTIME_OK, "postgres_version": "x"}, {**RUNTIME_OK, "python_version": "3"}, {**RUNTIME_OK, "swisseph_version": ""},
          {**RUNTIME_OK, "collation": "a b"}]


def test_the_receipt_carries_a_required_validated_closed_runtime_block():
    assert smd.RECEIPT_KEYS == ("run_id", "orchestrator_commit", "runtime") and "runtime" in smd.RECEIPT_SPEC["keys"]
    assert set(smd.RECEIPT_SPEC["runtime"]) == set(sr.RUNTIME_KEYS) and "--runtime-file" in smd.RECEIPT_SPEC["flag"] and "CLAIMED_UNVERIFIED" in smd.RECEIPT_SPEC["rule"]
    assert smd.build_record_spec(RD)["receipt_expected"] == smd.RECEIPT_SPEC
    ok = out_doc(D5, "rehearsal")
    assert ok["rebuild"]["runtime"] == RUNTIME_OK and smd.validate_fingerprint_output(ok, D5, side="rehearsal") == []
    ok2 = out_doc(D5, "rehearsal")
    ok2["rebuild"]["runtime"]["swisseph_version"] = None                                           # swisseph is optional
    assert smd.validate_fingerprint_output(ok2, D5, side="rehearsal") == []
    for bad in RT_BAD:
        d = out_doc(D5, "rehearsal")
        d["rebuild"]["runtime"] = bad
        probs = smd.validate_fingerprint_output(d, D5, side="rehearsal")
        assert probs and any("runtime" in x for x in probs), bad
        assert smd.verify_rebuild_receipt({**RECEIPT, "runtime": bad}, _rrec(), RD), bad
        with pytest.raises(smd.MirrorError):
            smd.rehearsal_fingerprints(object(), syn_baseline_decls(), stage="after_rebuild", as_of="2026-10-03", commit=SHA40, rebuild={**RECEIPT, "runtime": bad})
    d = out_doc(D5, "rehearsal")
    d["rebuild"].pop("runtime")                                                                      # no runtime at all: the receipt is not a receipt
    assert smd.validate_fingerprint_output(d, D5, side="rehearsal")
    assert smd.verify_rebuild_receipt({k: v for k, v in RECEIPT.items() if k != "runtime"}, _rrec(), RD)
    with pytest.raises(smd.MirrorError):
        smd.rehearsal_fingerprints(object(), syn_baseline_decls(), stage="after_rebuild", as_of="2026-10-03", commit=SHA40,
                                   rebuild={k: v for k, v in RECEIPT.items() if k != "runtime"})


def _off_linux(platform="darwin/arm64"):
    reh = out_doc(RD, "rehearsal")
    reh["rebuild"]["runtime"] = {**RUNTIME_OK, "platform": platform, "os": "macOS 15.1", "collation": "C"}
    return out_doc(RD, "production"), reh


def test_a_rehearsal_run_off_linux_amd64_reads_claimed_unverified_for_platform_bound_units():
    prod, reh = _off_linux()
    drill, cov = smd.build_drill(prod, reh, RD, None, commit=SHA40)
    pb = sorted(u for u, v in RD.units().items() if "platform_bound" in v["reproducibility"])
    assert pb == ["bg_cohort", "bg_sky_calendar"] and drill["claimed_unverified"] == pb and not set(pb) & set(drill["equal"]) and len(drill["equal"]) == 29
    assert drill["result"] == "PASS_DECLARED_ONLY" and drill["runtime"]["platform"] == "darwin/arm64" and sr.validate_drill(drill) == []
    assert cov["claimed_unverified"] == pb and cov["runtime"] == drill["runtime"]
    assert all(cov["unit_status"][u]["status"] == "CLAIMED_UNVERIFIED:platform_not_linux_amd64" for u in pb)
    assert "2 platform-bound units CLAIMED_UNVERIFIED (rebuilt off linux/amd64: never equal, never counted): bg_cohort, bg_sky_calendar" in cov["headline"]
    assert "rebuild runtime: darwin/arm64, macOS 15.1, PostgreSQL 15.18, Python 3.11.9, swisseph 2.10.03, collation C" in cov["headline"]
    # the same files from a linux/amd64 run: the units are equal and counted
    d2, c2 = smd.build_drill(out_doc(RD, "production"), out_doc(RD, "rehearsal"), RD, None, commit=SHA40)
    assert d2["claimed_unverified"] == [] and set(pb) <= set(d2["equal"]) and len(d2["equal"]) == 31
    assert "0 platform-bound units CLAIMED_UNVERIFIED" in c2["headline"] and "rebuild runtime: linux/amd64, Debian GNU/Linux 12 (bookworm), PostgreSQL 15.18" in c2["headline"]
    for u in pb:
        assert c2["unit_status"][u]["status"] == "equal"


def test_the_runtime_is_printed_by_the_compare_cli_and_a_status_for_an_off_linux_run_is_claimed_unverified(tmp_path, capsys):
    prod, reh = _off_linux()
    for n, d in (("prod", prod), ("reh", reh)):
        (tmp_path / f"{n}.json").write_text(json.dumps(d))
    out = tmp_path / "drill.json"
    assert smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--out", str(out)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["result"] == "PASS_DECLARED_ONLY" and "CLAIMED_UNVERIFIED" in printed["headline"]
    assert json.loads(out.read_text())["runtime"]["platform"] == "darwin/arm64"
    assert json.loads((tmp_path / "drill.json.coverage.json").read_text())["claimed_unverified"] == ["bg_cohort", "bg_sky_calendar"]
    st = {x["step"]: x for x in smd.drill_status(RD, rehearsal=reh)["steps"]}["linux_amd64_runtime"]
    assert st["state"] == "CLAIMED_UNVERIFIED" and st["detail"]["units"] == ["bg_cohort", "bg_sky_calendar"]
    assert {x["step"]: x for x in smd.drill_status(RD, rehearsal=out_doc(RD, "rehearsal"))["steps"]}["linux_amd64_runtime"]["state"] == "SHAPE_CHECKED"


def test_the_container_run_expects_33_of_34_complete_and_only_the_muhurta_lattice_not_run():
    ce = smd.build_record_spec(RD)["container_run_expectation"]
    assert ce["expected_complete_count"] == "33 of 34" and len(ce["expected_complete"]) == 33 and ce["expected_not_run"] == {"bg_muhurta_lattice": "NEEDS_AS_OF_PIN"}
    assert {"bg_sky_calendar", "bg_cohort", "bg_gochara_arcs"} <= set(ce["expected_complete"]) and "bg_muhurta_lattice" not in ce["expected_complete"]
    assert smd.CONTAINER_EXPECTED_NOT_RUN == ("bg_muhurta_lattice",) and set(smd.CONTAINER_EXPECTED_NOT_RUN) <= set(smd.NOT_RUN_ALLOWED)
    assert "SS B1" in ce["decision"] and "linux/amd64 Debian container" in ce["decision"] and "EXPECTED `complete`" in ce["note"]
    rules = " ".join(smd.build_record_spec(RD)["rules"])
    assert ("33 of the 34 declared assets `complete`, including bg_sky_calendar, bg_cohort and bg_gochara_arcs, and 1 `not_run`: bg_muhurta_lattice with NEEDS_AS_OF_PIN") in rules
    assert "3015" not in rules and "bg_gochara_arcs with" not in rules                                    # no stale #3015 wording anywhere in the spec
    # the validator is unchanged: a record with the two platform-bound assets complete verifies; not_run for them is still accepted as listed
    assert smd.verify_rebuild_receipt(RECEIPT, _rrec({"bg_cohort": {"asset_id": "bg_cohort", "state": "complete"}, "bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "complete"}}), RD) == []
    assert smd.verify_rebuild_receipt(RECEIPT, _rrec(), RD) == []
    assert smd.verify_rebuild_receipt(RECEIPT, _rrec({"bg_ephemeris": {"asset_id": "bg_ephemeris", "state": "not_run", "reason": "NEEDS_AS_OF_PIN"}}), RD)
    st = {x["step"]: x for x in smd.drill_status(RD, rehearsal=out_doc(RD, "rehearsal"))["steps"]}["rehearsal_l0_rebuild"]
    assert "33 of 34 declared assets are expected complete (bg_sky_calendar and bg_cohort among them)" in st["detail"]["expects"]
    assert "bg_muhurta_lattice not_run (NEEDS_AS_OF_PIN)" in st["detail"]["expects"] and "bg_gochara_arcs not_run" not in st["detail"]["expects"]
    s0 = {x["step"]: x for x in smd.drill_status(RD)["steps"]}["rehearsal_l0_rebuild"]
    assert "33 of 34 declared assets are expected complete" in s0["detail"]["expects"]


# ═════════════════ round 8: a recorded expected difference is limited to its columns (projection fingerprints) ═════════════════

def _eph_pair(*, change_columns_only=True, drop=False, decls=None):
    """production vs rehearsal for the REAL declarations, where bg_ephemeris/ephemeris_daily differs. `change_columns_only` keeps the projection (the fingerprint
    WITHOUT node_mode / epoch_convention) equal on both sides, as a rebuild that nulled the two columns would; otherwise the projection differs too (something else changed)."""
    decls = decls or RD_ED
    prod, reh = out_doc(decls, "production"), out_doc(decls, "rehearsal")
    reh["tables"]["bg_ephemeris"]["ephemeris_daily"]["sha256"] = hashlib.sha256(b"eph-differs").hexdigest()
    reh["fingerprints"]["bg_ephemeris"] = reh["tables"]["bg_ephemeris"]["ephemeris_daily"]["sha256"]
    if not change_columns_only:
        reh["projections"]["bg_ephemeris"]["ephemeris_daily"]["sha256"] = hashlib.sha256(b"proj-differs").hexdigest()
    if drop:
        reh["projections"] = {}
    return prod, reh


EPH_EXPL = {"bg_ephemeris": {"reason_code": "production_ahead_of_commit", "decision": "N-300",
                             "detail": "production carries node_mode and epoch_convention that the writer at this commit does not write (synthetic tracked change)"}}


def test_a_recorded_difference_is_a_known_difference_limited_to_its_two_columns():
    prod, reh = _eph_pair()
    drill, cov = smd.build_drill(prod, reh, RD_ED, EPH_EXPL, commit=SHA40)
    assert drill["result"] == "PASS_DECLARED_ONLY" and drill["problems"] == [] and drill["unexplained"] == [] and "bg_ephemeris" not in drill["equal"]
    k = drill["known_differences"]
    assert len(k) == 1 and k[0]["unit"] == "bg_ephemeris" and k[0]["table"] == "ephemeris_daily" and k[0]["columns"] == ["node_mode", "epoch_convention"]
    assert k[0]["observed"] is True and k[0]["limited_to_columns"] is True and k[0]["explained"] is True and k[0]["reference"] == "synthetic tracked change (test fixture)"
    st = cov["expected_differences_status"][0]
    assert st["status"] == "observed" and st["limited_to_columns"] is True and st["explained"] is True
    assert ("limited to ['node_mode', 'epoch_convention']: explained. KNOWN DIFFERENCE (tracked: synthetic tracked change (test fixture)): expected, visible, never equal."
            == st["hint"])
    assert cov["known_differences"] == k and cov["projections"]["bg_ephemeris"]["production"] == cov["projections"]["bg_ephemeris"]["rehearsal"]
    assert sr.validate_drill(drill) == [] and not any("#3015" in f for f in cov["open_findings"])
    # unexplained: still expected and visible, but it needs its explanation
    d0, c0 = smd.build_drill(prod, reh, RD_ED, None, commit=SHA40)
    assert d0["result"] == "FAIL" and d0["unexplained"] == ["bg_ephemeris"] and "explain it (reason code production_ahead_of_commit" in c0["expected_differences_status"][0]["hint"]
    # the fully equal drill: the record is not observed (the tracked change has landed: remove the record)
    de, ce = smd.build_drill(out_doc(RD_ED, "production"), out_doc(RD_ED, "rehearsal"), RD_ED, None, commit=SHA40)
    assert de["known_differences"][0]["observed"] is False and ce["expected_differences_status"][0]["status"] == "not_observed"


def test_something_else_changing_in_the_ephemeris_unit_cannot_hide_behind_the_recorded_difference():
    prod, reh = _eph_pair(change_columns_only=False)
    drill, cov = smd.build_drill(prod, reh, RD_ED, EPH_EXPL, commit=SHA40)
    assert drill["result"] == "FAIL" and drill["unexplained"] == ["bg_ephemeris"] and drill["known_differences"][0]["limited_to_columns"] is False
    assert any("bg_ephemeris: the difference is not limited to the expected columns ['node_mode', 'epoch_convention'] of ephemeris_daily" in x and "still differs" in x for x in drill["problems"])
    st = cov["expected_differences_status"][0]
    assert st["limited_to_columns"] is False and st["hint"].startswith("NOT limited to ['node_mode', 'epoch_convention']") and "something else in the unit changed" in st["hint"]
    # a rehearsal file that carries no projections cannot be validated at all (the file validator refuses it before any comparison)
    prod2, reh2 = _eph_pair(drop=True)
    assert any("projections must cover exactly the units" in x for x in smd.validate_fingerprint_output(reh2, RD_ED, side="rehearsal"))
    with pytest.raises(smd.MirrorError, match="projections"):
        smd.build_drill(prod2, reh2, RD_ED, EPH_EXPL, commit=SHA40)


@pytest.mark.parametrize("label,edit", [
    ("missing_block", lambda d: d.pop("projections")), ("not_an_object", lambda d: d.update(projections=[])), ("empty", lambda d: d.update(projections={})),
    ("extra_unit", lambda d: d["projections"].update(bg_nakshatra={"nakshatra": {"sha256": H, "rows": 5}})),
    ("wrong_table", lambda d: d["projections"].update(bg_ephemeris={"other": {"sha256": H, "rows": 5}})),
    ("two_tables", lambda d: d["projections"]["bg_ephemeris"].update(other={"sha256": H, "rows": 5})),
    ("bad_sha", lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(sha256="short")),
    ("bad_rows", lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(rows=-1)),
    ("bool_rows", lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(rows=True)),
    ("rows_differ_from_table", lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(rows=6)),
    ("extra_key", lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(x=1)),
    ("zero_rows_nonempty_hash", lambda d: (d["tables"]["bg_ephemeris"]["ephemeris_daily"].update(rows=0, sha256=fd.empty_table_fingerprint(RD_ED, "bg_ephemeris", "ephemeris_daily")),
                                            d["fingerprints"].update(bg_ephemeris=fd.empty_table_fingerprint(RD_ED, "bg_ephemeris", "ephemeris_daily")),
                                            d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(rows=0))),
    ("rows_with_empty_hash", lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(sha256=fd.empty_projection_fingerprint(RD_ED, "bg_ephemeris", "ephemeris_daily"))),
])
def test_the_projections_block_of_a_fingerprint_file_is_validated_on_both_sides(label, edit):
    for side in ("production", "rehearsal"):
        d = out_doc(RD_ED, side)
        assert smd.validate_fingerprint_output(d, RD_ED, side=side) == []
        edit(d)
        probs = smd.validate_fingerprint_output(d, RD_ED, side=side)
        assert probs, (label, side)


def test_the_projection_block_is_exactly_the_units_with_a_recorded_difference_and_the_reader_spec_says_how():
    d = out_doc(RD_ED, "production")
    assert list(d["projections"]) == ["bg_ephemeris"] and list(d["projections"]["bg_ephemeris"]) == ["ephemeris_daily"] and RD_ED.projection_tables() == {"bg_ephemeris": "ephemeris_daily"}
    assert "projections" in smd.OUTPUT_KEYS
    spec = smd.reader_spec(RD_ED)
    assert spec["projections"][0]["unit"] == "bg_ephemeris" and spec["projections"][0]["excluded_columns"] == ["node_mode", "epoch_convention"]
    assert "added to volatile_columns" in spec["projections"][0]["how"] and "no second read is needed" in spec["projections"][0]["how"]
    # a unit set without bg_ephemeris has no projections
    sub = out_doc(RD_ED, "production", assets=[u for u in RD_ED.expected_assets() if u != "bg_ephemeris"])
    assert sub["projections"] == {} and smd.validate_fingerprint_output(sub, RD_ED, side="production") == []


def test_the_compare_cli_prints_the_known_difference(tmp_path, capsys):
    decl_file = tmp_path / "decl_with_ed.json"
    decl_file.write_text(json.dumps(_ed_doc()), encoding="utf-8")
    loaded = fd.load_declarations(decl_file)                                                                 # the synthetic record is valid under the real validator
    assert loaded.projection_tables() == {"bg_ephemeris": "ephemeris_daily"}
    prod, reh = _eph_pair(decls=loaded)
    for n, d in (("prod", prod), ("reh", reh), ("expl", EPH_EXPL)):
        (tmp_path / f"{n}.json").write_text(json.dumps(d))
    out = tmp_path / "drill.json"
    assert smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--explained", str(tmp_path / "expl.json"),
                     "--declarations", str(decl_file), "--out", str(out)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["known_differences"][0]["limited_to_columns"] is True and printed["expected_differences"][0]["status"] == "observed"
    assert "KNOWN DIFFERENCE (tracked: synthetic tracked change (test fixture))" in printed["expected_differences"][0]["hint"] and printed["resolved_findings"][0].startswith("9. (resolved)")
    assert not any("#3015" in f for f in printed["open_findings"])


# ═════════════════ round 9: N-135, the rolling-horizon evidence in the fingerprint files and the drill ═════════════════

def _hz_pair(**kw):
    """production vs rehearsal for the synthetic declarations where a_roll differs ONLY by rows after the production horizon (built later)."""
    prod, reh = _pair()
    _later(reh, prod, **kw)
    return prod, reh


A_ROLL_EXPL = {"a_roll": {"reason_code": "rolling_horizon", "decision": "N-135", "detail": "rebuilt later than production: the extra rows are all after the production horizon (N-135)"}}


def test_a_later_build_is_explained_with_both_counts_both_dates_and_the_equal_overlap_in_the_report():
    prod, reh = _hz_pair()
    drill, cov = smd.build_drill(prod, reh, D5, A_ROLL_EXPL, commit=SHA40)
    assert drill["result"] == "PASS_DECLARED_ONLY" and drill["problems"] == [] and drill["unexplained"] == [] and "a_roll" not in drill["equal"]
    ev = drill["differences"][0]["explained"]["evidence"]
    assert ev["summary"] == ("N-135: rows 8 vs 5 (rehearsal vs production), built-through dates 2026-01-09 vs 2026-01-05 (rehearsal vs production), "
                             "overlap equal over 5 rows (count and fingerprint, through 2026-01-05)")
    assert cov["horizon_evidence"] == [{"unit": "a_roll", **ev}] and cov["unit_status"]["a_roll"]["horizon_evidence"] == ev["summary"]
    assert cov["horizons"]["a_roll"]["table"] == "syn_roll" and cov["horizons"]["a_roll"]["rehearsal"]["rows"] == 8
    assert "1 rolling-horizon differences explained by N-135 (evidence checked: the shared date range is row-for-row equal, count and fingerprint): a_roll: N-135: rows 8 vs 5" in cov["headline"]
    assert sr.validate_drill(drill) == []
    d0, c0 = smd.build_drill(*_pair(), D5, None, commit=SHA40)                                             # no rolling difference: nothing explained, the clause says 0
    assert "0 rolling-horizon differences explained by N-135" in c0["headline"] and c0["horizon_evidence"] == []


@pytest.mark.parametrize("label,edit,message", [
    ("overlap_hash_differs", lambda p, r: r["horizons"]["a_roll"]["syn_roll"].update(overlap_sha256=hashlib.sha256(b"other").hexdigest()), "the overlap fingerprints differ"),
    ("overlap_rows_differ", lambda p, r: r["horizons"]["a_roll"]["syn_roll"].update(overlap_rows=4), "overlap row counts differ"),
    ("rehearsal_max_before_production_max", lambda p, r: (_set_unit(r, "a_roll", hashlib.sha256(b"earlier").hexdigest(), rows=5),
                                                          r["horizons"]["a_roll"]["syn_roll"].update(max_date="2026-01-04", overlap_cutoff="2026-01-05"))[1], "was not built later"),
    ("rehearsal_cutoff_not_production_max", lambda p, r: r["horizons"]["a_roll"]["syn_roll"].update(overlap_cutoff="2026-01-07"), "is not the production max_date"),
])
def test_the_rolling_horizon_explanation_is_refused_in_the_drill_without_the_evidence(label, edit, message):
    prod, reh = _hz_pair()
    edit(prod, reh)
    assert smd.validate_fingerprint_output(reh, D5, side="rehearsal") == [], label                       # the FILE is valid; the evidence is what fails
    drill, _ = smd.build_drill(prod, reh, D5, A_ROLL_EXPL, commit=SHA40)
    assert drill["result"] == "FAIL" and drill["unexplained"] == ["a_roll"] and any("(N-135)" in x and message in x for x in drill["problems"]), (label, drill["problems"])


def test_a_missing_horizon_block_is_a_refused_file_and_a_block_on_a_non_rolling_unit_is_refused():
    prod, reh = _hz_pair()
    for side, doc in (("production", prod), ("rehearsal", reh)):
        d = copy.deepcopy(doc)
        d["horizons"] = {}
        assert any("horizons must cover exactly the units flagged rolling_horizon" in x for x in smd.validate_fingerprint_output(d, D5, side=side))
        d = copy.deepcopy(doc)
        d.pop("horizons")
        assert smd.validate_fingerprint_output(d, D5, side=side)
        d = copy.deepcopy(doc)                                                                           # a block on a unit that is not flagged rolling_horizon
        d["horizons"]["a_0"] = {"syn_t0": dict(d["horizons"]["a_roll"]["syn_roll"])}
        assert any("horizons must cover exactly" in x for x in smd.validate_fingerprint_output(d, D5, side=side))
    with pytest.raises(smd.MirrorError, match="horizons"):
        d = copy.deepcopy(reh)
        d["horizons"] = {}
        smd.build_drill(prod, d, D5, A_ROLL_EXPL, commit=SHA40)
    # the comparison itself refuses a horizons input for a unit that is not flagged (the unit set comes from the declarations, so the input is closed)
    with pytest.raises(sr.RehearsalError, match="horizons must map a unit flagged rolling_horizon"):
        sr.compare_fingerprint_sets(sr.fingerprint_set(prod["fingerprints"]), sr.fingerprint_set(reh["fingerprints"]), None, expected_assets=D5.expected_assets(), commit=SHA40,
                                    coverage=D5.drill_coverage(), rows={u: {"production": smd._rows_of(prod, u), "rehearsal": smd._rows_of(reh, u)} for u in D5.expected_assets()},
                                    runtime=RUNTIME_OK, horizons={"a_0": {"table": "syn_t0", "production": None, "rehearsal": None}})


@pytest.mark.parametrize("label,edit", [
    ("not_an_object", lambda d: d.update(horizons=[])), ("extra_unit", lambda d: d["horizons"].update(a_0={"syn_t0": {}})),
    ("wrong_table", lambda d: d["horizons"].update(a_roll={"other": dict(d["horizons"]["a_roll"]["syn_roll"])})),
    ("two_tables", lambda d: d["horizons"]["a_roll"].update(other={})),
    ("not_a_block", lambda d: d["horizons"]["a_roll"].update(syn_roll="x")),
    ("missing_key", lambda d: d["horizons"]["a_roll"]["syn_roll"].pop("overlap_rows")),
    ("extra_key", lambda d: d["horizons"]["a_roll"]["syn_roll"].update(x=1)),
    ("wrong_date_column", lambda d: d["horizons"]["a_roll"]["syn_roll"].update(date_column="other_date")),
    ("rows_differ_from_table", lambda d: d["horizons"]["a_roll"]["syn_roll"].update(rows=6, overlap_rows=6)),
    ("whole_overlap_hash_not_the_table_hash", lambda d: d["horizons"]["a_roll"]["syn_roll"].update(overlap_sha256=hashlib.sha256(b"x").hexdigest())),
    ("empty_overlap_non_empty_hash", lambda d: d["horizons"]["a_roll"]["syn_roll"].update(overlap_rows=0, overlap_cutoff=None)),
    ("bad_date", lambda d: d["horizons"]["a_roll"]["syn_roll"].update(max_date="2026-13-45", overlap_cutoff="2026-13-45")),
])
def test_the_horizons_block_of_a_fingerprint_file_is_validated_on_both_sides(label, edit):
    prod, reh = _pair()
    for side, doc in (("production", prod), ("rehearsal", reh)):
        d = copy.deepcopy(doc)
        assert smd.validate_fingerprint_output(d, D5, side=side) == []
        edit(d)
        assert smd.validate_fingerprint_output(d, D5, side=side), (label, side)


def test_a_production_block_is_cut_at_its_own_max_date_and_covers_the_whole_table():
    prod, _ = _pair()
    for edit in (lambda b: b.update(overlap_cutoff="2026-01-04", overlap_rows=4), lambda b: b.update(overlap_cutoff="2026-01-09")):
        d = copy.deepcopy(prod)
        edit(d["horizons"]["a_roll"]["syn_roll"])
        probs = smd.validate_fingerprint_output(d, D5, side="production")
        assert probs and any("on the production side the overlap_cutoff is the block's own max_date" in x or "overlap" in x for x in probs)
    # the same block is a valid REHEARSAL block: its cutoff is the production's max_date, not its own
    _, reh = _hz_pair()
    assert reh["horizons"]["a_roll"]["syn_roll"]["overlap_cutoff"] != reh["horizons"]["a_roll"]["syn_roll"]["max_date"]
    assert smd.validate_fingerprint_output(reh, D5, side="rehearsal") == [] and smd.validate_fingerprint_output(reh, D5, side="production") != []


def test_the_cutoffs_for_the_rehearsal_come_from_the_production_file_and_the_reader_spec_says_what_to_emit():
    prod, _ = _hz_pair()
    assert smd.horizon_cutoffs_from(prod, D5) == {"a_roll": HZ_MAX}
    real = out_doc(RD, "production")
    assert smd.horizon_cutoffs_from(real, RD) == {"bg_muhurta_lattice": HZ_MAX, "bg_sky_calendar": HZ_MAX}
    sub = out_doc(RD, "production", assets=[u for u in RD.expected_assets() if u != "bg_sky_calendar"])
    assert smd.horizon_cutoffs_from(sub, RD) == {"bg_muhurta_lattice": HZ_MAX}
    bad = copy.deepcopy(prod)
    bad["horizons"] = {}
    with pytest.raises(smd.MirrorError, match="--horizon-cutoffs is not valid"):
        smd.horizon_cutoffs_from(bad, D5)
    with pytest.raises(smd.MirrorError):
        smd.horizon_cutoffs_from(out_doc(D5, "rehearsal"), D5)                                         # a rehearsal file is not a production file
    spec = smd.reader_spec(RD)["horizons"]
    assert spec["rule"].startswith("N-135") and spec["units"] == [{"unit": "bg_muhurta_lattice", "table": "bg_muhurta_lattice", "date_column": "start_utc"},
                                                                {"unit": "bg_sky_calendar", "table": "bg_sky_calendar", "date_column": "event_datetime_utc"}]
    text = " ".join(str(v) for v in spec.values())
    for needle in ("SAME streaming pass", "date_column, min_date, max_date, rows, overlap_cutoff, overlap_rows, overlap_sha256", "YYYY-MM-DDTHH:MM:SS.ffffff", "overlap_cutoff = the block's own max_date",
                   "nikasha_stale_certs.fingerprint_rows", "SAME function and the SAME declaration", "--horizon-cutoffs production_file", "PRODUCTION file's max_date"):
        assert needle in text, needle
    assert "horizons" in smd.OUTPUT_KEYS


SKY_EXPL = {"bg_sky_calendar": {"reason_code": "rolling_horizon", "detail": "rebuilt later than production: the extra rows are all after the production horizon (N-135)"},
            "bg_cohort": {"reason_code": "source_unavailable_offline", "decision": "N-121", "detail": "the container run is not the production runtime for this unit (platform bound)"}}


def test_the_compare_cli_prints_the_horizon_evidence_for_the_real_declarations(tmp_path, capsys):
    prod, reh = out_doc(RD, "production"), out_doc(RD, "rehearsal")
    _later(reh, prod, unit="bg_sky_calendar", extra=20, mx="2026-01-31", decls=RD)
    assert smd.validate_fingerprint_output(reh, RD, side="rehearsal") == []
    for n, d in (("prod", prod), ("reh", reh), ("expl", {"bg_sky_calendar": SKY_EXPL["bg_sky_calendar"]})):
        (tmp_path / f"{n}.json").write_text(json.dumps(d))
    out = tmp_path / "drill.json"
    assert smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--explained", str(tmp_path / "expl.json"),
                     "--out", str(out)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["result"] == "PASS_DECLARED_ONLY" and "1 rolling-horizon differences explained by N-135" in printed["headline"]
    assert "rows 25 vs 5 (rehearsal vs production), built-through dates 2026-01-31 vs 2026-01-05" in printed["headline"]
    rep = json.loads((tmp_path / "drill.json.coverage.json").read_text())
    assert rep["horizon_evidence"][0]["unit"] == "bg_sky_calendar" and rep["horizon_evidence"][0]["rule"] == "N-135" and rep["unit_status"]["bg_sky_calendar"]["horizon_evidence"]
    assert json.loads(out.read_text())["horizons"]["bg_sky_calendar"]["rehearsal"]["overlap_cutoff"] == "2026-01-05"
    # without the explanation file the unit is unexplained (the evidence alone explains nothing)
    assert smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--out", str(out)]) == 4
    capsys.readouterr()


def test_rehearsal_fingerprints_passes_the_horizon_cutoffs_to_the_reader_and_records_the_blocks(monkeypatch):
    seen = {}

    class Conn:
        read_only = False

        def rollback(self):
            pass

    def fake(conn, decls, units=None, **kw):
        seen.update(kw)
        return {"definition": fd.FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256, "fingerprints": {}, "tables": {}, "projections": {}, "horizons": {"u": "block"}}
    monkeypatch.setattr(smd.fd, "unit_fingerprints", fake)
    doc = smd.rehearsal_fingerprints(Conn(), D5, stage="baseline", as_of="2026-10-03", commit=SHA40, horizon_cutoffs={"a_roll": HZ_MAX})
    assert seen["horizon_cutoffs"] == {"a_roll": HZ_MAX} and doc["horizons"] == {"u": "block"} and seen["cursor_prefix"] == "e57"
    smd.rehearsal_fingerprints(Conn(), D5, stage="baseline", as_of="2026-10-03", commit=SHA40)
    assert seen["horizon_cutoffs"] is None


# ═════════════════ round 10: real detectors for the status steps ss_decisions and text_seed ═════════════════

def _git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=x", "-c", "user.email=x@x", "-c", "commit.gpgsign=false", *args], check=check, capture_output=True, env=sr._git_env())


def _scratch(tmp_path, files, name="repo"):
    """A scratch git repository under tmp_path with one commit holding `files` ({path: text|bytes}); returns (repo, commit sha)."""
    repo = pathlib.Path(tmp_path) / name
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    for rel, body in files.items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "x", "--allow-empty")
    return repo, _git(repo, "rev-parse", "HEAD").stdout.decode().strip()


_SCRATCH_MEMO: dict = {}
_MEMO_ROOT: list = []


def _scratch_memo(parent, files, name="repo"):
    """`_scratch`, built ONCE per (name, content) in a persistent temporary directory and then reused. For the mutant battery only (every mutant
    reads the same repositories and never writes to them; each build is about six git spawns, 13 per battery, 235 batteries on a CI runner)."""
    import atexit
    import shutil
    import tempfile
    key = (name, json.dumps({k: (v.hex() if isinstance(v, bytes) else v) for k, v in files.items()}, sort_keys=True))
    hit = _SCRATCH_MEMO.get(key)
    if hit is not None and hit[0].exists():
        return hit
    if not _MEMO_ROOT:
        root = tempfile.mkdtemp(prefix="smd_memo_")
        _MEMO_ROOT.append(root)
        atexit.register(shutil.rmtree, root, True)
    sub = pathlib.Path(_MEMO_ROOT[0]) / f"{len(_SCRATCH_MEMO):04d}"
    sub.mkdir()
    _SCRATCH_MEMO[key] = _scratch(sub, files, name=name)
    return _SCRATCH_MEMO[key]


REG_PATH = smd.DECISION_REGISTER_PATH


def _register(*ids, extra=""):
    """A register body: each item is an id (state `decided`) or an (id, state) pair; a repeated id is a later record of it (the register is append-only)."""
    out = []
    for it in ids:
        i, st = (it, "decided") if isinstance(it, str) else it
        out.append(json.dumps({"id": i, "title": f"decision {i}", "state": st}) + "\n")
    return "".join(out) + extra


def _status_drill(commit, *, horizon=False):
    """A valid drill document for the real declarations whose commit is `commit` (cites N-121; with `horizon` also N-135 through a rolling-horizon explanation)."""
    prod, reh = out_doc(RD, "production", commit=commit), out_doc(RD, "rehearsal", commit=commit)
    expl = None
    if horizon:
        _later(reh, prod, unit="bg_sky_calendar", extra=20, mx="2026-01-31", decls=RD)
        expl = {"bg_sky_calendar": {"reason_code": "rolling_horizon", "detail": "rebuilt later than production: the extra rows are all after the production horizon (N-135)"}}
    return smd.build_drill(prod, reh, RD, expl, commit=commit)[0]


def _dstep(repo, drill, **kw):
    return smd.decisions_step(RD, drill, repo, **kw)


def test_the_register_absent_at_the_commit_reads_unmeasured_with_the_exact_text(tmp_path):
    repo, sha = _scratch(tmp_path, {"README": "x\n"})
    st = _dstep(repo, _status_drill(sha))
    assert st["step"] == "ss_decisions" and st["state"] == "UNMEASURED" and st["reason"] == "NEEDS_DECISION_REGISTER_ON_MAIN"
    assert st["detail"]["text"] == "decision register not on main" and st["detail"]["commit"] == sha and st["detail"]["register"] == REG_PATH
    assert st["detail"]["cited"]["N-121"] and smd.NEEDS["decisions"] == "NEEDS_DECISION_REGISTER_ON_MAIN"
    # the cross-cutting register of another campaign is never read in its place
    repo2, sha2 = _scratch(tmp_path, {"00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md": '{"id": "N-121"}\n'}, name="repo2")
    assert _dstep(repo2, _status_drill(sha2))["reason"] == "NEEDS_DECISION_REGISTER_ON_MAIN"
    # a register in the working tree (untracked) or only in a LATER commit is not the register AT the commit under test
    (repo / REG_PATH).parent.mkdir(parents=True)
    (repo / REG_PATH).write_text(_register("N-121"))
    assert _dstep(repo, _status_drill(sha))["reason"] == "NEEDS_DECISION_REGISTER_ON_MAIN"
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "register")
    assert _dstep(repo, _status_drill(sha))["reason"] == "NEEDS_DECISION_REGISTER_ON_MAIN"          # the drill's commit is the earlier one


def test_every_cited_id_in_the_register_at_the_commit_measures_the_step_and_binds_its_sha(tmp_path):
    body = _register("N-77", "N-121", "N-135", "N-200")
    repo, sha = _scratch(tmp_path, {REG_PATH: body})
    st = _dstep(repo, _status_drill(sha))
    assert st["state"] == "MEASURED" and "reason" not in st and st["detail"]["register_sha256"] == hashlib.sha256(body.encode()).hexdigest()
    assert st["detail"]["records"] == 4 and st["detail"]["latest_states"] == {"N-121": "decided"} and st["detail"]["cited"] == {"N-121": ["the runtime block", "the closed not_run list", "partial-ownership units", "SEEDED units"]}
    assert st["detail"]["commit"] == sha and "every decision id the drill cites" in st["detail"]["note"]
    st2 = _dstep(repo, _status_drill(sha, horizon=True), config_seed=True)                          # N-135 through the rolling-horizon explanation, N-121 for the seed too
    assert st2["state"] == "MEASURED" and sorted(st2["detail"]["cited"]) == ["N-121", "N-135"] and "the production config seed" in st2["detail"]["cited"]["N-121"]
    assert any("bg_sky_calendar" in w and "rolling_horizon" in w for w in st2["detail"]["cited"]["N-135"])
    # the status as a whole carries it
    s = smd.drill_status(RD, drill=_status_drill(sha), repo=repo)
    assert {x["step"]: x["state"] for x in s["steps"]}["ss_decisions"] == "MEASURED" and s["result"] == "UNMEASURED"


def test_a_cited_id_missing_from_the_register_is_listed_and_a_prefix_is_not_a_match(tmp_path):
    repo, sha = _scratch(tmp_path, {REG_PATH: _register("N-121")})
    st = _dstep(repo, _status_drill(sha, horizon=True))
    assert st["state"] == "UNMEASURED" and st["reason"] == "NEEDS_DECISIONS_IN_REGISTER" and st["detail"]["missing"] == ["N-135"]
    assert st["detail"]["text"] == "decision id N-135 not in the register" and st["detail"]["register_sha256"] and st["detail"]["records"] == 1
    # the id prefix trap: N-13 and N-1350 are not N-135, and ids are exact (no case folding, no trimming)
    repo2, sha2 = _scratch(tmp_path, {REG_PATH: _register("N-121", "N-13", "N-1350", "n-135", " N-135", "N-135 ")}, name="repo2")
    st2 = _dstep(repo2, _status_drill(sha2, horizon=True))
    assert st2["reason"] == "NEEDS_DECISIONS_IN_REGISTER" and st2["detail"]["missing"] == ["N-135"]
    repo3, sha3 = _scratch(tmp_path, {REG_PATH: _register("N-1", "N-12", "N-1211")}, name="repo3")
    assert _dstep(repo3, _status_drill(sha3))["detail"]["missing"] == ["N-121"]
    repo4, sha4 = _scratch(tmp_path, {REG_PATH: _register()}, name="repo4")                         # an empty register
    assert _dstep(repo4, _status_drill(sha4))["reason"] == "NEEDS_VALID_DECISION_REGISTER"
    both = _dstep(repo, _status_drill(sha, horizon=True) | {"explained_input": {}})
    assert both["state"] == "UNMEASURED"


def test_the_register_is_append_only_so_repeated_ids_are_legal_and_the_latest_record_must_be_decided(tmp_path):
    drill_h = lambda sha: _status_drill(sha, horizon=True)  # noqa: E731
    cases = {
        "superseded_later": ([("N-121", "decided"), ("N-135", "decided"), ("N-135", "superseded")], "NEEDS_DECISIONS_IN_REGISTER", {"N-135": "superseded"}),
        "decided_after_superseded": ([("N-121", "decided"), ("N-135", "superseded"), ("N-135", "decided")], None, {}),
        "only_proposed": ([("N-121", "decided"), ("N-135", "proposed")], "NEEDS_DECISIONS_IN_REGISTER", {"N-135": "proposed"}),
        "state_case_matters": ([("N-121", "decided"), ("N-135", "Decided")], "NEEDS_DECISIONS_IN_REGISTER", {"N-135": "Decided"}),
        "no_state_field": ([("N-121", "decided"), ("N-135", None)], "NEEDS_DECISIONS_IN_REGISTER", {"N-135": None}),
        "uncited_id_superseded_is_irrelevant": ([("N-17", "decided"), ("N-17", "superseded"), ("N-121", "decided"), ("N-135", "decided")], None, {}),
        "cited_id_decided_twice": ([("N-121", "decided"), ("N-121", "decided"), ("N-135", "decided"), ("N-135", "decided")], None, {}),
        "first_decided_last_superseded_for_the_runtime_decision": ([("N-121", "decided"), ("N-121", "superseded"), ("N-135", "decided")], "NEEDS_DECISIONS_IN_REGISTER", {"N-121": "superseded"}),
    }
    for label, (recs, reason, undecided) in cases.items():
        body = "".join(json.dumps({"id": i, "state": st} if st is not None else {"id": i}) + "\n" for i, st in recs)
        repo, sha = _scratch(tmp_path, {REG_PATH: body}, name=label)
        st = _dstep(repo, drill_h(sha))
        assert st["detail"]["register_sha256"] == hashlib.sha256(body.encode()).hexdigest(), label
        if reason is None:
            assert st["state"] == "MEASURED" and st["detail"]["latest_states"] == {"N-121": "decided", "N-135": "decided"} and st["detail"]["records"] == len(recs), label
        else:
            assert st["state"] == "UNMEASURED" and st["reason"] == reason and st["detail"]["not_decided"] == undecided and st["detail"]["missing"] == [], label
            for i, v in undecided.items():
                assert f"decision id {i} not decided (its latest record is {v!r})" in st["detail"]["text"], label
    recs, probs = smd.parse_decision_register(_register("N-1", ("N-1", "superseded"), "N-2").encode())
    assert probs == [] and recs == [("N-1", "decided"), ("N-1", "superseded"), ("N-2", "decided")]
    assert smd.register_latest(recs) == {"N-1": "superseded", "N-2": "decided"} and smd.register_latest([]) == {} and smd.DECIDED_STATE == "decided"


@pytest.mark.parametrize("label,body,needle", [
    ("malformed_json", _register("N-121") + "{not json\n", "not strict JSON"),
    ("duplicate_key_in_a_record", _register("N-121") + '{"id": "N-135", "id": "N-1"}\n', "not strict JSON"),
    ("nan_constant", _register("N-121") + '{"id": "N-135", "x": NaN}\n', "not strict JSON"),
    ("blank_line", _register("N-121") + "\n" + _register("N-135"), "is empty"),
    ("not_an_object", _register("N-121") + '["N-135"]\n', "non-empty string `id`"),
    ("id_not_a_string", _register("N-121") + '{"id": 135}\n', "non-empty string `id`"),
    ("empty_id", _register("N-121") + '{"id": " "}\n', "non-empty string `id`"),
    ("no_id_field", _register("N-121") + '{"name": "N-135"}\n', "non-empty string `id`"),
])
def test_a_register_that_is_not_strict_jsonl_with_unique_ids_is_not_trusted(tmp_path, label, body, needle):
    repo, sha = _scratch(tmp_path, {REG_PATH: body})
    st = _dstep(repo, _status_drill(sha))
    assert st["state"] == "UNMEASURED" and st["reason"] == "NEEDS_VALID_DECISION_REGISTER", label
    assert any(needle in x for x in st["detail"]["problems"]) and st["detail"]["register_sha256"] == hashlib.sha256(body.encode()).hexdigest()
    assert smd.parse_decision_register(body.encode())[1]


def test_the_register_reader_and_the_drill_input_refuse_what_they_cannot_trust(tmp_path):
    repo, sha = _scratch(tmp_path, {REG_PATH: _register("N-121")})
    no_drill = _dstep(repo, None)
    assert no_drill["state"] == "UNMEASURED" and no_drill["reason"] == "NEEDS_DRILL_DOCUMENT" and no_drill["detail"]["register"] == REG_PATH
    forged = _status_drill(sha)
    forged["result"] = "FAIL" if forged["result"] != "FAIL" else "PASS"
    bad = _dstep(repo, forged)
    assert bad["reason"] == "NEEDS_VALID_DRILL" and bad["detail"]["problems"]
    assert _dstep(repo, "x")["reason"] == "NEEDS_VALID_DRILL" and _dstep(repo, {})["reason"] == "NEEDS_VALID_DRILL"
    other = _status_drill("2" * 40)                                                                  # a commit this repository does not have
    st = _dstep(repo, other)
    assert st["reason"] == "NEEDS_COMMIT_IN_REPO" and "is not in the repository" in st["detail"]["text"]
    with pytest.raises(smd.CommitNotInRepo):
        smd.git_read_at(repo, "3" * 40, REG_PATH)
    for bad_commit in ("HEAD", "abc", "../x", "1" * 39, None):
        with pytest.raises(smd.MirrorError):
            smd.git_read_at(repo, bad_commit, REG_PATH)
    assert smd.git_read_at(repo, sha, REG_PATH) == _register("N-121").encode() and smd.git_read_at(repo, sha, "no/such/file") is None
    # a drill made under other declarations is not accepted either
    drill = _status_drill(sha)
    drill["coverage"]["undeclared"] = {"bg_x": "no_table"}
    assert _dstep(repo, drill)["reason"] == "NEEDS_VALID_DRILL"


def test_cited_decisions_collects_the_closed_set_from_the_drill_document():
    sha = "1" * 40
    drill = _status_drill(sha)
    assert smd.cited_decisions(drill) == {"N-121": ["the runtime block", "the closed not_run list", "partial-ownership units", "SEEDED units"]}
    assert smd.cited_decisions(drill, config_seed=True)["N-121"][-1] == "the production config seed"
    h = _status_drill(sha, horizon=True)
    assert sorted(smd.cited_decisions(h)) == ["N-121", "N-135"]
    ex = {"bg_ephemeris": {"reason_code": "production_ahead_of_commit", "decision": "N-300", "detail": "production carries node_mode and epoch_convention that the writer does not write (held)"}}
    prod, reh = out_doc(RD, "production", commit=sha), out_doc(RD, "rehearsal", commit=sha)
    reh["tables"]["bg_ephemeris"]["ephemeris_daily"]["sha256"] = hashlib.sha256(b"eph").hexdigest()
    reh["fingerprints"]["bg_ephemeris"] = reh["tables"]["bg_ephemeris"]["ephemeris_daily"]["sha256"]
    d3 = smd.build_drill(prod, reh, RD, ex, commit=sha)[0]
    assert smd.cited_decisions(d3)["N-300"] == ["the explanation of bg_ephemeris (production_ahead_of_commit)", "the explanation given for bg_ephemeris"]


# ----- text_seed -----

M610 = (REPO / smd.MIGRATION_610_PATH).read_bytes()
AUD = smd.migration_610_constants(M610)
RUN = "5e57e57e-5e57-4e57-8e57-5e57e57e57e5"


def _migration(identity=None, content=None, count=10651, dup=False):
    ident = identity or "a" * 64
    cont = content or "b" * 64
    body = (f"CREATE TABLE IF NOT EXISTS nirmana_bg_texts_integrity_baselines (\n  contract_revision text PRIMARY KEY,\n  row_count bigint NOT NULL CHECK (row_count = {count})\n);\n"
            f"audited_identity_sha256 constant text :=\n    '{ident}';\n  audited_content_sha256 constant text :=\n    '{cont}';\n")
    return body + (f"audited_identity_sha256 constant text :=\n    '{ident}';\n" if dup else "")


def _check(commit, aud=None, **over):
    a = aud or AUD
    doc = {"schema": smd.TEXT_SEED_SCHEMA, "spec_sha256": smd.text_seed_spec()["spec_sha256"], "commit": commit, "run_id": RUN,
           "baseline": {"contract_revision": smd.TEXT_BASELINE_REVISION, **a}, "computed": dict(a), "orphan_chunks": 0}
    doc.update(over)
    return doc


def _tstep(repo, sha, check, *, rehearsal="auto", record="auto", commit=None):
    reh = out_doc(RD, "rehearsal", commit=sha) if rehearsal == "auto" else rehearsal
    rec = _rrec(orchestrator_commit=sha) if record == "auto" else record
    return smd.text_seed_step(check, repo, commit=commit or sha, rehearsal=reh, build_record=rec, decls=RD)


def test_the_real_migration_610_constants_are_what_the_status_detector_reads():
    assert AUD == {"identity_sha256": "44b067b48544af32df4b2f4d8b13cc7c269aa029e236a0af3d2e8d7347d7d30e",
                   "content_sha256": "b81fb9c098847ecafc2072fd49d706f1a6bb811ab3fcc169d8753010ea6e17e2", "row_count": 10651}
    assert smd.migration_610_constants(_migration("c" * 64, "d" * 64, 7).encode()) == {"identity_sha256": "c" * 64, "content_sha256": "d" * 64, "row_count": 7}
    for bad in (_migration(dup=True).encode(), b"x", b"\xff\xfe", _migration().replace("audited_content_sha256", "audited_content_sha").encode(),
                _migration().replace("row_count = 10651", "row_count > 5").encode()):
        assert smd.migration_610_constants(bad) is None


def test_the_text_seed_spec_prints_the_selects_and_the_digest_sql_is_migration_610s_own():
    spec = smd.text_seed_spec()
    assert spec["schema"] == "suvarna-text-seed-check/v1" and spec["file"] == "text_seed_check.json" and [x["name"] for x in spec["selects"]] == ["baseline", "computed", "orphans"]
    assert spec["spec_sha256"] == smd.sha256_text(fd.canonical_json({"schema": smd.TEXT_SEED_SCHEMA, "selects": [{"name": x["name"], "select": x["select"]} for x in spec["selects"]]}))
    flat = lambda t: re.sub(r"\s+", "", t)  # noqa: E731
    m610 = flat(M610.decode())
    digest = {x["name"]: x["select"] for x in spec["selects"]}["computed"]
    for expr in re.findall(r"encode\(sha256\(.*?'hex'\) AS (?:identity|content)_sha256", digest):                   # each digest expression, whitespace-insensitive
        assert flat(expr.rsplit(" AS ", 1)[0]) in m610, expr[:60]
    assert "count(*) AS row_count" in digest and digest.endswith("FROM classical_text_chunks")
    sel = {x["name"]: x["select"] for x in spec["selects"]}
    assert "contract_revision = 'bg-texts-integrity-v1'" in sel["baseline"] and "NOT EXISTS" in sel["orphans"] and "classical_texts" in sel["orphans"]
    assert all(";" not in x["select"] and not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|TRUNCATE|COPY)\b", x["select"], re.I) for x in spec["selects"])
    text = " ".join(spec["status_detector"])
    for needle in ("audited constants READ FROM migration 610", "recomputed by `drill status`", "orphan_chunks is 0", "bg_texts is `complete` in the VERIFIED build record"):
        assert needle in text
    assert "NEEDS_TEXT_SEED_CHECK" in spec["without_the_file"] and "FAIL" in spec["without_the_file"]


@pytest.mark.parametrize("label,edit", [
    ("extra_key_asserting_equal", lambda d: d.update(equal=True)), ("missing_key", lambda d: d.pop("orphan_chunks")), ("schema", lambda d: d.update(schema="x/v1")),
    ("spec_sha", lambda d: d.update(spec_sha256="0" * 64)), ("commit", lambda d: d.update(commit="abc")), ("run_id_nil", lambda d: d.update(run_id="00000000-0000-0000-0000-000000000000")),
    ("baseline_revision", lambda d: d["baseline"].update(contract_revision="bg-texts-integrity-v2")), ("baseline_extra", lambda d: d["baseline"].update(x=1)),
    ("baseline_hash", lambda d: d["baseline"].update(identity_sha256="short")), ("baseline_rows", lambda d: d["baseline"].update(row_count=True)),
    ("computed_hash", lambda d: d["computed"].update(content_sha256="Z" * 64)), ("computed_rows", lambda d: d["computed"].update(row_count=-1)),
    ("computed_extra", lambda d: d["computed"].update(contract_revision="x")), ("orphans_negative", lambda d: d.update(orphan_chunks=-1)),
    ("orphans_bool", lambda d: d.update(orphan_chunks=False)), ("not_an_object", lambda d: d.clear()),
])
def test_the_text_seed_check_is_a_closed_validated_file(label, edit):
    good = _check("1" * 40)
    assert smd.validate_text_seed_check(good) == []
    bad = copy.deepcopy(good)
    edit(bad)
    assert smd.validate_text_seed_check(bad), label
    assert smd.validate_text_seed_check(None) and smd.validate_text_seed_check([])


def test_text_seed_without_the_file_or_with_a_bad_one_is_unmeasured_with_the_named_reason(tmp_path):
    repo, sha = _scratch(tmp_path, {smd.MIGRATION_610_PATH: M610})
    none = smd.text_seed_step(None, repo)
    assert none["state"] == "UNMEASURED" and none["reason"] == "NEEDS_TEXT_SEED_CHECK" and "text-seed-spec" in none["detail"]["spec"] and smd.NEEDS["text_seed"] == "NEEDS_TEXT_SEED_CHECK"
    bad = _tstep(repo, sha, _check(sha, spec_sha256="0" * 64))
    assert bad["state"] == "UNMEASURED" and bad["reason"] == "NEEDS_TEXT_SEED_CHECK" and any("spec_sha256" in x for x in bad["detail"]["problems"])
    other = _tstep(repo, sha, _check("2" * 40))
    assert other["reason"] == "NEEDS_TEXT_SEED_CHECK" and "not at the commit under test" in other["detail"]["problems"][0]
    assert smd.drill_status(RD)["steps"][[x["step"] for x in smd.drill_status(RD)["steps"]].index("text_seed")]["reason"] == "NEEDS_TEXT_SEED_CHECK"


def test_text_seed_is_measured_only_on_the_audited_equal_digests_with_bg_texts_complete(tmp_path):
    repo, sha = _scratch(tmp_path, {smd.MIGRATION_610_PATH: M610})
    ok = _tstep(repo, sha, _check(sha))
    assert ok["state"] == "MEASURED" and ok["detail"]["audited"] == AUD and ok["detail"]["computed"] == AUD and ok["detail"]["orphan_chunks"] == 0
    assert ok["detail"]["migration_610_sha256"] == hashlib.sha256(M610).hexdigest() and ok["detail"]["run_id"] == RUN and ok["detail"]["commit"] == sha
    # equality is recomputed from the values: every unequal value is a measured FAIL, never MEASURED, never UNMEASURED
    for field, val in (("identity_sha256", "e" * 64), ("content_sha256", "f" * 64), ("row_count", 10650)):
        st = _tstep(repo, sha, _check(sha, computed={**AUD, field: val}))
        assert st["state"] == "FAIL" and any("differ from the baseline row" in x for x in st["detail"]["problems"]), field
    for field, val in (("identity_sha256", "e" * 64), ("content_sha256", "f" * 64), ("row_count", 10650)):       # a baseline that is not the audited constants (computed agrees with it)
        mine = {**AUD, field: val}
        st = _tstep(repo, sha, _check(sha, aud=mine))
        assert st["state"] == "FAIL" and any("not the audited constants of migration 610" in x for x in st["detail"]["problems"]), field
    orph = _tstep(repo, sha, _check(sha, orphan_chunks=3))
    assert orph["state"] == "FAIL" and any("3 orphan chunk(s)" in x for x in orph["detail"]["problems"])
    # the file's run is not the receipt's run / no rehearsal file at all
    run = _tstep(repo, sha, _check(sha, run_id="6e57e57e-5e57-4e57-8e57-5e57e57e57e5"))
    assert run["state"] == "UNMEASURED" and run["reason"] == "NEEDS_TEXT_SEED_CHECK_OF_THIS_RUN"
    norh = _tstep(repo, sha, _check(sha), rehearsal=None)
    assert norh["state"] == "UNMEASURED" and norh["reason"] == "NEEDS_REHEARSAL_RECEIPT"
    # bg_texts must be complete in a build record that verifies against the receipt
    not_done = _tstep(repo, sha, _check(sha), record=_rrec_nr((), orchestrator_commit=sha, ) | {"assets": [x if x["asset_id"] != "bg_texts" else {"asset_id": "bg_texts", "state": "failed"} for x in _rrec(orchestrator_commit=sha)["assets"]]})
    assert not_done["reason"] == "NEEDS_BUILD_RECORD_BG_TEXTS"
    other_run = _tstep(repo, sha, _check(sha), record=_rrec(orchestrator_commit=sha, run_id="6e57e57e-5e57-4e57-8e57-5e57e57e57e5"))
    assert other_run["reason"] == "NEEDS_BUILD_RECORD_BG_TEXTS" and any("run_id" in x for x in other_run["detail"]["unverified_because"])
    assert _tstep(repo, sha, _check(sha), record=None)["reason"] == "NEEDS_BUILD_RECORD_BG_TEXTS"
    missing = _rrec(orchestrator_commit=sha, drop=("bg_texts",))
    assert _tstep(repo, sha, _check(sha), record=missing)["reason"] == "NEEDS_BUILD_RECORD_BG_TEXTS"


def test_text_seed_needs_migration_610_at_the_commit_under_test(tmp_path):
    repo, sha = _scratch(tmp_path, {"README": "x\n"})
    st = _tstep(repo, sha, _check(sha))
    assert st["state"] == "UNMEASURED" and st["reason"] == "NEEDS_MIGRATION_610_AT_COMMIT"
    dup, sha2 = _scratch(tmp_path, {smd.MIGRATION_610_PATH: _migration(dup=True)}, name="dup")
    assert _tstep(dup, sha2, _check(sha2))["reason"] == "NEEDS_MIGRATION_610_AT_COMMIT"
    syn, sha3 = _scratch(tmp_path, {smd.MIGRATION_610_PATH: _migration("a" * 64, "b" * 64, 12)}, name="syn")      # the audited constants come from the migration at THAT commit
    mine = {"identity_sha256": "a" * 64, "content_sha256": "b" * 64, "row_count": 12}
    assert _tstep(syn, sha3, _check(sha3, aud=mine))["state"] == "MEASURED"
    assert _tstep(syn, sha3, _check(sha3))["state"] == "FAIL"                                                      # the real constants are not this commit's constants
    assert _tstep(repo, sha, _check("2" * 40), commit="2" * 40)["reason"] == "NEEDS_COMMIT_IN_REPO"


def test_the_status_cli_reads_the_drill_and_the_text_seed_check_and_the_spec_commands_print(tmp_path, capsys):
    repo, sha = _scratch(tmp_path, {REG_PATH: _register("N-121"), smd.MIGRATION_610_PATH: M610})
    files = {"drill": _status_drill(sha), "check": _check(sha), "reh": out_doc(RD, "rehearsal", commit=sha), "rec": _rrec(orchestrator_commit=sha)}
    for n, d in files.items():
        (tmp_path / f"{n}.json").write_text(json.dumps(d))
    assert smd.main(["status", "--drill", str(tmp_path / "drill.json"), "--text-seed-check", str(tmp_path / "check.json"), "--rehearsal", str(tmp_path / "reh.json"),
                     "--build-record", str(tmp_path / "rec.json"), "--repo", str(repo)]) == 0
    out = json.loads(capsys.readouterr().out)
    st = {x["step"]: x["state"] for x in out["steps"]}
    assert st["ss_decisions"] == "MEASURED" and st["text_seed"] == "MEASURED" and out["result"] == "UNMEASURED"
    assert smd.main(["text-seed-spec"]) == 0 and json.loads(capsys.readouterr().out)["spec_sha256"] == smd.text_seed_spec()["spec_sha256"]
    assert smd.main(["validate-text-seed-check", str(tmp_path / "check.json")]) == 0 and json.loads(capsys.readouterr().out)["valid"] is True
    (tmp_path / "bad.json").write_text(json.dumps({**files["check"], "equal": True}))
    assert smd.main(["validate-text-seed-check", str(tmp_path / "bad.json")]) == 2 and json.loads(capsys.readouterr().out)["valid"] is False
    (tmp_path / "junk.json").write_text('{"a": 1, "a": 2}')
    assert smd.main(["validate-text-seed-check", str(tmp_path / "junk.json")]) == 2
    capsys.readouterr()


def test_the_spec_and_the_status_text_state_the_not_run_rule(capsys):
    spec = smd.build_record_spec(RD)
    assert spec["declared_assets_that_may_be_not_run"] == {a: smd.NOT_RUN_ALLOWED[a] for a in sorted(smd.NOT_RUN_ALLOWED)}
    assert len(spec["declared_assets_that_must_be_complete"]) == 31 and not {"bg_sky_calendar", "bg_cohort", "bg_muhurta_lattice"} & set(spec["declared_assets_that_must_be_complete"])
    assert "bg_gochara_arcs" in spec["declared_assets_that_must_be_complete"]
    rules = " ".join(spec["rules"])
    assert "not_run" in rules and "closed not_run_allowed list" in rules and "never accepted as `complete` or as `not_run`" in rules and "decision id" in rules
    assert "reason: NEEDS_" in spec["required_fields"]["assets"] and any(x["state"] == "not_run" and x["reason"].startswith("NEEDS_") for x in spec["shape_example"]["assets"])
    st = {x["step"]: x for x in smd.drill_status(RD, rehearsal=out_doc(RD, "rehearsal"))["steps"]}["rehearsal_l0_rebuild"]
    assert st["state"] == "CLAIMED_UNVERIFIED" and "not_run" in st["detail"]["expects"] and "bg_sky_calendar" in st["detail"]["expects"] and "a failed asset is never accepted" in st["detail"]["expects"]
    s0 = {x["step"]: x for x in smd.drill_status(RD)["steps"]}["rehearsal_l0_rebuild"]
    assert "not_run" in s0["detail"]["expects"] and "bg_muhurta_lattice" in s0["detail"]["expects"]
    reh = out_doc(RD, "rehearsal")
    s1 = smd.drill_status(RD, rehearsal=reh, build_record=_rrec())
    assert {x["step"]: x["state"] for x in s1["steps"]}["rehearsal_l0_rebuild"] == "MEASURED"
    s2 = smd.drill_status(RD, rehearsal=reh, build_record=_rrec({"bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "failed", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}}))
    d2 = {x["step"]: x for x in s2["steps"]}["rehearsal_l0_rebuild"]
    assert d2["state"] == "CLAIMED_UNVERIFIED" and any("bg_sky_calendar is failed" in x for x in d2["detail"]["unverified_because"])
    assert smd.main(["build-record-spec"]) == 0
    assert "NEEDS_AS_OF_PIN" in capsys.readouterr().out


def test_a_partial_ownership_unit_in_the_real_drill_is_reported_and_never_a_bare_pass():
    prod, reh = out_doc(RD, "production"), out_doc(RD, "rehearsal")
    for t, m in reh["tables"]["bg_formula_constants"].items():
        m["sha256"] = hashlib.sha256(f"mig{t}".encode()).hexdigest()
    reh["fingerprints"]["bg_formula_constants"] = reh["tables"]["bg_formula_constants"]["brahma_formula_constants"]["sha256"]
    drill, cov = smd.build_drill(prod, reh, RD, None, commit=SHA40)
    assert drill["result"] == "PASS_DECLARED_ONLY" and drill["unexplained"] == [] and [d["asset"] for d in drill["differences"]] == ["bg_formula_constants"]
    assert drill["differences"][0]["explained"]["reason_code"] == "migration_owned_rows" and drill["coverage"]["partial_ownership"] == RD.partial_ownership_units()
    assert cov["unit_status"]["bg_formula_constants"]["partial_ownership"].startswith("partial: writer-only rows compared") and cov["partial_ownership"] == RD.partial_ownership_units()
    assert "2 partial-ownership units" in cov["headline"] and "bg_formula_constants (brahma_formula_constants)" in cov["headline"] and "bg_ghatana (brahma_event_ontology)" in cov["headline"]
    assert sr.validate_drill(drill) == [] and sr.validate_drill(drill, declarations_coverage=RD.drill_coverage()) == []
    # a difference on a unit WITHOUT the declaration is still a failure
    reh2 = out_doc(RD, "rehearsal")
    for t, m in reh2["tables"]["bg_nakshatra"].items():
        m["sha256"] = hashlib.sha256(f"x{t}".encode()).hexdigest()
    reh2["fingerprints"]["bg_nakshatra"] = fd.composite_fingerprint({t: m["sha256"] for t, m in reh2["tables"]["bg_nakshatra"].items()})
    assert smd.build_drill(prod, reh2, RD, None, commit=SHA40)[0]["result"] == "FAIL"


def test_the_open_findings_are_printed_with_every_report_in_factual_words(tmp_path, capsys):
    f = smd.OPEN_FINDINGS
    assert len(f) == 8 and [x[:2] for x in f] == ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."]
    assert "bg_ghatana" in f[0] and "event-ontology" in f[0] and "matches no migration" in f[0] and "activity-ontology" in f[0] and "does match" in f[0]
    assert "bg_transit_engine" in f[1] and "69 rows" in f[1] and "bg_transit_rules" in f[1] and "undeclared" in f[1]
    assert "bg_medical_mappings" in f[2] and "21 rows" in f[2] and "9 graha rows" in f[2]
    assert "build_run_assets.state is 'complete'" in f[3] and "asset_throughput.state is 'error'" in f[3]
    assert "706" in f[4] and "1077" in f[4] and "asset_output_digest_specs" in f[4] and "brahma_formula_constants" in f[4] and "seed-spec" in f[4]
    assert "bg_ontology's stored integrity check requires COUNT(*) >= 737 in brahma_ontology" in f[5] and "414 rows (13 classes + 5 bootstrap dasha_system rows)" in f[5]
    assert "bg_dasha_systems, bg_doshas, bg_yogas add the rest after it" in f[5] and "can never pass in DAG order" in f[5] and "N-99/N-105" in f[5] and "only its own output" in f[5]
    assert "bg_reference's md5-over-string_agg pins" in f[6] and "reference_strength_systems" in f[6] and "reference_glossary" in f[6] and "Debian glibc en_US.UTF8, x86_64, PostgreSQL 15.18" in f[6]
    assert "returns TRUE on production" in f[6] and 'COLLATE "C"' in f[6]
    assert "ephemeris_daily speed_dps (all 9 bodies)" in f[7] and "aarch64/Darwin" in f[7] and "x86_64/Linux" in f[7] and "node_mode, epoch_convention, source_citation and row counts equal" in f[7]
    assert "linux/amd64 Debian container (SS decision B1)" in f[7]
    assert not any("#3015" in x or "NEEDS_PR_3015" in x or "KNOWN" in x for x in f)                       # nothing open names the retired known difference
    rf = smd.RESOLVED_FINDINGS
    assert len(rf) == 1 and rf[0] == ("9. (resolved) bg_ephemeris writer did not write node_mode/epoch_convention; fixed by #3015, on main 2026-10-05; the drill must now show "
                                       "equality for ephemeris_daily. bg_gochara_arcs, which needs the Rahu/Ketu node_mode rows, runs and is expected complete.")
    drill, cov = smd.build_drill(out_doc(RD, "production"), out_doc(RD, "rehearsal"), RD, None, commit=SHA40)
    assert cov["open_findings"] == list(f)
    for n, d in (("prod", out_doc(RD, "production")), ("reh", out_doc(RD, "rehearsal"))):
        (tmp_path / f"{n}.json").write_text(json.dumps(d))
    assert smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh.json"), "--commit", SHA40, "--out", str(tmp_path / "d.json")]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["open_findings"] == list(f) and json.loads((tmp_path / "d.json.coverage.json").read_text())["open_findings"] == list(f)
    assert cov["resolved_findings"] == list(rf) and printed["resolved_findings"] == list(rf) and json.loads((tmp_path / "d.json.coverage.json").read_text())["resolved_findings"] == list(rf)
    assert not hasattr(smd, "DEPENDENCIES") and "dependencies" not in cov and "dependencies" not in printed
    assert printed["partial_ownership"] == RD.partial_ownership_units()


# ── the production config seed: specified, validated, never run ──

def test_the_seed_spec_names_exactly_the_seven_tables_with_read_only_selects():
    spec = smd.seed_spec(RD)
    assert spec["schema"] == "suvarna-l0-config-seed/v1" and spec["role"] == "suvarna_reader" and "READ ONLY" in spec["transaction"] and "Pravaha" in spec["when"]
    assert [t["table"] for t in spec["tables"]] == ["asset_registry", "asset_output_digest_specs", "brahma_formula_constants", "brahma_event_ontology", "bg_transit_rules", "brahma_ontology", "nirmana_bg_texts_integrity_baselines"]
    for t in spec["tables"]:
        sel = t["select"]
        assert re.fullmatch(r"SELECT row_to_json\((\w)\)::text FROM [a-z_]+ \1( WHERE .+)? ORDER BY .+", sel), sel
        assert ";" not in sel and not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|TRUNCATE|COPY)\b", sel, re.I) and t["what"]
    sel = {t["table"]: t["select"] for t in spec["tables"]}
    assert "layer = 'brahmagyan'" in sel["asset_registry"] and "layer = 'brahmagyan'" in sel["asset_output_digest_specs"]
    assert sel["bg_transit_rules"].count("'double_transit'") == 1
    assert sel["brahma_formula_constants"].count("'") == 20 and sel["brahma_event_ontology"].count("'") == 54
    assert len(smd.writer_owned_ids("brahma_formula_constants")) == 10 and len(smd.writer_owned_ids("brahma_event_ontology")) == 27
    for i in smd.writer_owned_ids("brahma_formula_constants"):
        assert f"'{i}'" in sel["brahma_formula_constants"]
    for i in smd.writer_owned_ids("brahma_event_ontology"):
        assert f"'{i}'" in sel["brahma_event_ontology"]
    assert all(f"'{i}'" not in sel["bg_transit_rules"] for i in ("favourable", "unfavourable"))
    assert len(spec["evidence"]["rules"]) == 4 and "never connects" in spec["load"]
    assert spec["spec_sha256"] == smd.sha256_text(fd.canonical_json({"schema": smd.SEED_SCHEMA, "tables": [{"table": t["table"], "select": t["select"]} for t in spec["tables"]]}))


# ── collation-independent seed order (found by the first rerun: production and the C-locale rehearsal cluster sorted text keys differently) ──

# the type of every ORDER BY key of the seed SELECTs (verified against the schema extract / the mirror dump by `test_the_seed_order_key_types_are_the_real_column_types`)
SEED_ORDER_TYPES = {("asset_registry", "asset_id"): "text", ("asset_output_digest_specs", "asset_id"): "text", ("asset_output_digest_specs", "spec_sha256"): "text",
                    ("brahma_formula_constants", "constant_id"): "text", ("brahma_event_ontology", "event_class_id"): "text",
                    ("bg_transit_rules", "graha"): "text", ("bg_transit_rules", "rule_type"): "text", ("bg_transit_rules", "primary_house"): "integer",
                    ("bg_transit_rules", "id"): "integer", ("brahma_ontology", "entity_class"): "text", ("brahma_ontology", "canonical_id"): "text",
                    ("nirmana_bg_texts_integrity_baselines", "contract_revision"): "text"}
TEXT_TYPES = ("text", "character varying", "varchar", "character", "citext", "name")


def seed_order_problems(tables):
    """Problems with the ORDER BY of the seed SELECTs: a text-typed key without `COLLATE "C"`, an unknown key, or no ORDER BY. [] = collation independent."""
    out = []
    for t in tables:
        m = re.search(r" ORDER BY (.+)$", t["select"])
        if not m:
            out.append(f"{t['table']}: no ORDER BY")
            continue
        for item in m.group(1).split(", "):
            km = re.fullmatch(r'\w\.(\w+)( COLLATE "C")?', item.strip())
            if not km:
                out.append(f"{t['table']}: ORDER BY item {item!r} is not <alias>.<column> [COLLATE \"C\"]")
                continue
            ty = SEED_ORDER_TYPES.get((t["table"], km.group(1)))
            if ty is None:
                out.append(f"{t['table']}.{km.group(1)}: key type unknown to the test")
            elif ty in TEXT_TYPES and not km.group(2):
                out.append(f"{t['table']}.{km.group(1)}: text key sorted with the database collation (needs COLLATE \"C\")")
    return out


def test_every_text_key_in_a_seed_order_by_carries_collate_c():
    tables = smd.seed_tables()
    assert seed_order_problems(tables) == []
    got = {t["table"]: re.search(r" ORDER BY (.+)$", t["select"]).group(1) for t in tables}
    assert got == {"asset_registry": 'r.asset_id COLLATE "C"', "asset_output_digest_specs": 's.asset_id COLLATE "C", s.spec_sha256 COLLATE "C"',
                   "brahma_formula_constants": 'c.constant_id COLLATE "C"', "brahma_event_ontology": 'e.event_class_id COLLATE "C"',
                   "bg_transit_rules": 't.graha COLLATE "C", t.rule_type COLLATE "C", t.primary_house, t.id',
                   "brahma_ontology": 'c.entity_class COLLATE "C", c.canonical_id COLLATE "C"', "nirmana_bg_texts_integrity_baselines": 'b.contract_revision COLLATE "C"'}
    for t in tables:                                                       # the integer keys carry no collation (it would be a type error)
        assert not re.search(r"(primary_house|\.id) COLLATE", t["select"])
    # the checker itself catches a missing COLLATE on any text key, one at a time
    for i, t in enumerate(tables):
        for m in re.finditer(r' COLLATE "C"', t["select"]):
            broken = [dict(x) for x in tables]
            broken[i]["select"] = t["select"][:m.start()] + t["select"][m.end():]
            assert seed_order_problems(broken), (t["table"], m.start())


def test_the_seed_order_key_types_are_the_real_column_types():
    ext = json.loads((REPO / "00_ARCHITECTURE/control/FINGERPRINT_SCHEMA_EXTRACT_L0.json").read_text())["tables"]
    dump = REAL_DUMP.read_text(encoding="utf-8") if REAL_DUMP.is_file() else None
    checked = 0
    for (tab, col), want in SEED_ORDER_TYPES.items():
        if tab in ext:
            have = ext[tab]["columns"][col]["type"]
        elif dump is not None:
            mm = re.search(rf"CREATE TABLE (?:public\.)?{tab} \((.*?)\n\);", dump, re.S)
            line = next(x.strip() for x in mm.group(1).split("\n") if x.strip().startswith(col + " "))
            have = line.split()[1] if line.split()[1] != "character" else "character varying"
        else:
            continue
        assert (have in TEXT_TYPES) == (want in TEXT_TYPES) and (have == want or want == "text"), (tab, col, have, want)
        checked += 1
    assert checked >= 4                                                    # the three declared tables are in the committed extract, even without the dump


def test_the_seed_spec_hash_and_selects_changed_with_the_collation_fix():
    spec = smd.seed_spec(RD)
    assert all('COLLATE "C"' in t["select"] for t in spec["tables"])
    assert spec["spec_sha256"] == smd.sha256_text(fd.canonical_json({"schema": smd.SEED_SCHEMA, "tables": [{"table": t["table"], "select": t["select"]} for t in spec["tables"]]}))
    old = {"asset_registry": "SELECT row_to_json(r)::text FROM asset_registry r WHERE r.layer = 'brahmagyan' ORDER BY r.asset_id"}
    assert spec["tables"][0]["select"] != old["asset_registry"]            # select_sha256 moves: an evidence file made before the fix is refused by the validators


def test_the_seed_spec_hash_moves_with_any_select(monkeypatch):
    base = smd.seed_spec(RD)["spec_sha256"]
    real = smd.seed_tables
    def changed(repo_root=None):
        t = real(repo_root)
        t[4] = {**t[4], "select": t[4]["select"] + " "}
        return t
    monkeypatch.setattr(smd, "seed_tables", changed)
    assert smd.seed_spec(RD)["spec_sha256"] != base


def test_writer_owned_ids_refuse_a_source_that_does_not_yield_the_expected_count(tmp_path):
    for rel in ("platform/python-sidecar/brahmagyan/l0_formula_constants.py", "platform/python-sidecar/brahmagyan/l0_ghatana.py"):
        (tmp_path / pathlib.Path(rel).parent).mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text('"constant_id": "only_one"\n"event_class_id": "only_one"\n')
    with pytest.raises(smd.MirrorError, match="expected"):
        smd.writer_owned_ids("brahma_formula_constants", tmp_path)
    with pytest.raises(smd.MirrorError):
        smd.writer_owned_ids("no_such_table")


def _seed_evidence():
    spec = smd.seed_spec(RD)
    ids = sorted(RD.assets)
    tabs = {}
    for t in spec["tables"]:
        n = len(ids) if t["table"] == "asset_registry" else 3
        tabs[t["table"]] = {"select_sha256": smd.sha256_text(t["select"]), "rows": n, "sha256": hashlib.sha256(f"{t['table']}".encode()).hexdigest()}
    return {"schema": smd.SEED_SCHEMA, "spec_sha256": spec["spec_sha256"], "commit": SHA40, "as_of": "2026-10-04", "reader": {"role": "suvarna_reader", "read_only": True},
            "tables": tabs, "asset_registry_ids": ids}


def test_the_seed_spec_has_the_two_round_7_tables_with_their_reasons_and_the_not_seeded_statement():
    spec = smd.seed_spec(RD)
    sel = {t["table"]: t for t in spec["tables"]}
    bo, bl = sel["brahma_ontology"], sel["nirmana_bg_texts_integrity_baselines"]
    assert bo["select"] == ("SELECT row_to_json(c)::text FROM brahma_ontology c WHERE c.entity_class IN ('dasha_system', 'dosha', 'yoga') "
                            'ORDER BY c.entity_class COLLATE "C", c.canonical_id COLLATE "C"')
    assert bl["select"] == 'SELECT row_to_json(b)::text FROM nirmana_bg_texts_integrity_baselines b ORDER BY b.contract_revision COLLATE "C"'      # all rows, no WHERE
    assert "332 rows" in bo["what"] and "20 + 79 + 233" in bo["what"] and "contract_revision bg-texts-integrity-v1" in bl["what"]
    assert ("DELETE their own class and re-insert it" in bo["why"] and "REPLACED by the rebuild" in bo["why"] and "COUNT(*) >= 737" in bo["why"]
            and "bg_ontology itself writes 414 rows" in bo["why"] and "open finding 6" in bo["why"])
    assert "schema-only mirror has no baseline row" in bl["why"] and "audited constants of migration 610" in bl["why"]
    assert all("why" not in sel[t] for t in ("asset_registry", "asset_output_digest_specs", "brahma_formula_constants", "brahma_event_ontology", "bg_transit_rules"))
    notes = " ".join(spec["notes"])
    assert ("NOT seeded: the Rahu/Ketu rows of ephemeris_daily. The orchestrated bg_ephemeris writer writes node_mode/epoch_convention (PR #3015, on main 2026-10-05), "
            "so the rebuild produces them and the drill compares them.") in notes and "DEPENDENT" not in notes and "wait for" not in notes
    assert "only the dasha_system, dosha and yoga classes are seeded (332 rows)" in notes
    assert "exactly the seven tables of this spec" in " ".join(spec["evidence"]["rules"])
    assert spec["schema"] == "suvarna-l0-config-seed/v1" and spec["spec_sha256"] != "7ce73b761d47d58982510dba01d364594a7e24577161a9087470456a40ac2c82"   # the round 6 hash
    # the SELECTs read real, declared-by-the-dump columns: brahma_ontology's natural key and the baseline table's primary key from the committed extract
    ext = json.loads((REPO / "00_ARCHITECTURE/control/FINGERPRINT_SCHEMA_EXTRACT_L0.json").read_text())["tables"]
    assert {"entity_class", "canonical_id", "id"} <= set(ext["brahma_ontology"]["columns"]) and ext["brahma_ontology"]["unique"] == [{"columns": ["entity_class", "canonical_id"], "name": "brahma_ontology_canonical_unique"}]
    nb = ext["nirmana_bg_texts_integrity_baselines"]
    assert sorted(nb["columns"]) == ["content_sha256", "contract_revision", "identity_sha256", "recorded_at", "row_count"] and nb["primary_key"] == ["contract_revision"]
    assert nb["columns"]["contract_revision"]["type"] == "text" and nb["columns"]["row_count"]["type"] == "bigint"


def test_seed_evidence_must_cover_all_seven_tables_and_evidence_from_before_round_7_is_refused():
    ok = _seed_evidence()
    assert sorted(ok["tables"]) == sorted(t["table"] for t in smd.seed_tables()) and len(ok["tables"]) == 7 and smd.validate_seed_evidence(ok, RD) == []
    for dropped in ("brahma_ontology", "nirmana_bg_texts_integrity_baselines"):
        e = _seed_evidence()
        e["tables"].pop(dropped)
        assert any("tables must be exactly" in x for x in smd.validate_seed_evidence(e, RD)), dropped
    old = _seed_evidence()                                                                      # a five-table file bound to the round 6 spec hash
    for t in ("brahma_ontology", "nirmana_bg_texts_integrity_baselines"):
        old["tables"].pop(t)
    old["spec_sha256"] = "7ce73b761d47d58982510dba01d364594a7e24577161a9087470456a40ac2c82"
    probs = smd.validate_seed_evidence(old, RD)
    assert any("spec_sha256" in x for x in probs) and any("tables must be exactly" in x for x in probs)
    extra = _seed_evidence()
    extra["tables"]["ephemeris_daily"] = {"select_sha256": H, "rows": 1, "sha256": H}                # the Rahu/Ketu rows are NOT seeded: no such table is accepted
    assert smd.validate_seed_evidence(extra, RD)
    bad_sel = _seed_evidence()
    bad_sel["tables"]["brahma_ontology"]["select_sha256"] = smd.sha256_text(smd.seed_tables()[5]["select"].replace(", 'yoga'", ""))
    assert any("brahma_ontology: select_sha256" in x for x in smd.validate_seed_evidence(bad_sel, RD))


def test_a_seed_evidence_made_before_the_collation_fix_is_refused():
    """Evidence hashed with the old (database-collation) SELECTs binds to the old SELECT text and spec hash: both validators refuse it."""
    ev = _seed_evidence()
    old_select = smd.seed_tables()[0]["select"].replace(' COLLATE "C"', "")
    assert old_select != smd.seed_tables()[0]["select"]
    ev["tables"]["asset_registry"]["select_sha256"] = smd.sha256_text(old_select)
    probs = smd.validate_seed_evidence(ev, RD)
    assert probs and any("asset_registry" in x and "select" in x.lower() for x in probs)
    old_tables = [{"table": t["table"], "select": t["select"].replace(' COLLATE "C"', "")} for t in smd.seed_tables()]
    ev2 = _seed_evidence()
    ev2["spec_sha256"] = smd.sha256_text(fd.canonical_json({"schema": smd.SEED_SCHEMA, "tables": old_tables}))
    assert smd.validate_seed_evidence(ev2, RD)


def test_a_good_seed_evidence_validates():
    assert smd.validate_seed_evidence(_seed_evidence(), RD) == []
    ev = _seed_evidence()
    ev["tables"]["bg_transit_rules"].update(rows=0, sha256=smd.EMPTY_SHA256)                # an empty migration-owned slice is an honest result
    assert smd.validate_seed_evidence(ev, RD) == []


@pytest.mark.parametrize("label,mutate", [
    ("schema", lambda e: e.update(schema="x/v1")), ("spec_sha", lambda e: e.update(spec_sha256=H)), ("commit", lambda e: e.update(commit="abc")),
    ("as_of", lambda e: e.update(as_of="yesterday")), ("reader_role", lambda e: e["reader"].update(role="amjis_app")), ("reader_writable", lambda e: e["reader"].update(read_only=False)),
    ("reader_extra", lambda e: e["reader"].update(x=1)), ("extra_key", lambda e: e.update(x=1)), ("missing_key", lambda e: e.pop("as_of")),
    ("missing_table", lambda e: e["tables"].pop("bg_transit_rules")), ("extra_table", lambda e: e["tables"].update(charts={"select_sha256": H, "rows": 1, "sha256": H})),
    ("select_sha", lambda e: e["tables"]["asset_registry"].update(select_sha256=H)), ("rows_negative", lambda e: e["tables"]["brahma_formula_constants"].update(rows=-1)),
    ("rows_bool", lambda e: e["tables"]["brahma_formula_constants"].update(rows=True)), ("rows_float", lambda e: e["tables"]["brahma_formula_constants"].update(rows=1.5)),
    ("sha_bad", lambda e: e["tables"]["brahma_formula_constants"].update(sha256="zz")),
    ("zero_rows_non_empty_hash", lambda e: e["tables"]["brahma_formula_constants"].update(rows=0)),
    ("rows_with_empty_hash", lambda e: e["tables"]["brahma_formula_constants"].update(sha256=smd.EMPTY_SHA256)),
    ("table_extra_key", lambda e: e["tables"]["brahma_formula_constants"].update(x=1)),
    ("ids_missing_an_l0_asset", lambda e: (e["asset_registry_ids"].remove("bg_ephemeris"), e["tables"]["asset_registry"].update(rows=39))),
    ("ids_unsorted", lambda e: e["asset_registry_ids"].reverse()), ("ids_duplicate", lambda e: e["asset_registry_ids"].append("bg_texts")),
    ("registry_rows_differ_from_ids", lambda e: e["tables"]["asset_registry"].update(rows=41)),
    ("registry_rows_fewer_than_l0", lambda e: (e["asset_registry_ids"].pop(), e["tables"]["asset_registry"].update(rows=39))),
    ("ids_not_a_list", lambda e: e.update(asset_registry_ids="x")),
])
def test_the_seed_evidence_validator_refuses(label, mutate):
    e = _seed_evidence()
    mutate(e)
    assert smd.validate_seed_evidence(e, RD), label
    for junk in (None, [], "x", {}):
        assert smd.validate_seed_evidence(junk, RD)


def test_the_seed_cli_commands_and_the_status_step(tmp_path, capsys):
    assert smd.main(["seed-spec"]) == 0
    assert json.loads(capsys.readouterr().out)["spec_sha256"] == smd.seed_spec(RD)["spec_sha256"]
    good = tmp_path / "seed.json"
    good.write_text(json.dumps(_seed_evidence()))
    assert smd.main(["validate-seed-evidence", str(good)]) == 0 and json.loads(capsys.readouterr().out)["valid"] is True
    bad = _seed_evidence()
    bad["tables"]["asset_registry"]["rows"] = 1
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    assert smd.main(["validate-seed-evidence", str(tmp_path / "bad.json")]) == 2
    (tmp_path / "dup.json").write_text(good.read_text().replace('"as_of"', '"as_of": "2026-10-04", "as_of"', 1))
    assert smd.main(["validate-seed-evidence", str(tmp_path / "dup.json")]) == 2
    assert smd.main(["validate-seed-evidence", str(tmp_path / "absent.json")]) == 2
    capsys.readouterr()
    st = {x["step"]: x for x in smd.drill_status(RD)["steps"]}["config_seed"]
    assert st["state"] == "UNMEASURED" and st["reason"] == "NEEDS_CONFIG_SEED" and "seed-spec" in st["detail"]["expects"]
    ok = {x["step"]: x["state"] for x in smd.drill_status(RD, seed_evidence=_seed_evidence())["steps"]}["config_seed"]
    assert ok == "SHAPE_CHECKED"
    assert {x["step"]: x["state"] for x in smd.drill_status(RD, seed_evidence=bad)["steps"]}["config_seed"] == "UNMEASURED"
    assert smd.main(["status", "--seed-evidence", str(good)]) == 0 and "SHAPE_CHECKED" in capsys.readouterr().out


def test_the_seed_commands_never_open_a_connection(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("no connection may be opened")
    monkeypatch.setattr(sr, "_psycopg_connect", boom)
    monkeypatch.setattr(sr, "connect_checked", boom)
    monkeypatch.setattr(smd.subprocess, "run", boom)
    assert smd.main(["seed-spec"]) == 0 and smd.main(["status"]) == 0 and "psycopg" not in SRC.split("def seed_spec")[1].split("def validate_seed_evidence")[0]



# ── baseline target: database names, the rehearsal policy pins ──

@pytest.mark.parametrize("db", ["postgres", "template1", "suvarna_disposable; DROP DATABASE x", "Suvarna_disposable", "suvarna_disposable-x", "", None,
                                'suvarna_disposable"x', "suvarna_disposable x", "suvarna_disposable\n", "rehearsal", "suvarna", "suvarna_disposableX"])
def test_a_disposable_baseline_database_must_match_the_policy_pattern(db):
    with pytest.raises(smd.MirrorError, match="not allowed"):
        smd.validate_db_name(db, "disposable")


@pytest.mark.parametrize("db", ["postgres", "rehearsal-x", "rehearsal_", "rehearsalx", "suvarna_disposable_m", "", None, "rehearsal x", "rehearsal; DROP", 'rehearsal"'])
def test_a_rehearsal_baseline_database_must_match_the_policy_pattern(db):
    with pytest.raises(smd.MirrorError, match="not allowed"):
        smd.validate_db_name(db, "rehearsal")


def test_valid_database_names_are_accepted_and_quoted_safely():
    assert smd.validate_db_name("suvarna_disposable", "disposable") == "suvarna_disposable" and smd.validate_db_name("suvarna_disposable_m1", "disposable")
    assert smd.validate_db_name("rehearsal", "rehearsal") == "rehearsal" and smd.validate_db_name("rehearsal_mirror", "rehearsal")
    with pytest.raises(smd.MirrorError, match="unknown policy"):
        smd.validate_db_name("rehearsal", "production")
    assert smd._quote_ident('a"b') == '"a""b"' and smd._quote_lit("a'b") == "'a''b'"


def test_the_database_is_validated_before_any_cluster_is_touched(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise AssertionError("no cluster may be touched")
    monkeypatch.setattr(smd.sr, "init_cluster", boom)
    monkeypatch.setattr(smd.sr, "start_cluster", boom)
    monkeypatch.setattr(smd, "run_psql", boom)
    with pytest.raises(smd.MirrorError, match="not allowed"):
        smd.harness_target(tmp_path / "root", db="postgres", port=40123)
    with pytest.raises(smd.MirrorError, match="not allowed"):
        smd.harness_target(tmp_path / "root", db="suvarna_disposable_x", port=55432 + 1, policy="rehearsal")


def test_build_mirror_baseline_validates_the_database_before_copying_or_restoring(tmp_path, monkeypatch):
    monkeypatch.setattr(smd, "run_psql", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no psql")))
    t = smd.Target(pg_bin="/x", host="127.0.0.1", port=40001, user="u", db="postgres", policy="disposable")
    scratch = tmp_path / "scratch"
    with pytest.raises(smd.MirrorError, match="not allowed"):
        smd.build_mirror_baseline(make_recipe(tmp_path / "r"), scratch, t, decls=syn_baseline_decls(), extract=_syn_extract())
    assert not scratch.exists()                                                                  # nothing was copied either


def test_baseline_cli_refuses_a_bad_database_before_anything_else(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(smd, "harness_target", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not start a cluster")))
    rc = smd.main(["baseline", "--recipe", str(tmp_path), "--scratch", str(tmp_path / "s"), "--root", str(tmp_path / "root"), "--port", "40001",
                   "--db", "postgres", "--out", str(tmp_path / "o.json")])
    assert rc == 2 and "not allowed" in capsys.readouterr().err


def test_there_is_no_machine_specific_recipe_default_and_the_env_var_names_it(monkeypatch, tmp_path, capsys):
    assert not hasattr(smd, "DEFAULT_RECIPE") and "rehearsal_final" not in SRC and "S_L1" not in SRC
    monkeypatch.delenv(smd.RECIPE_ENV, raising=False)
    monkeypatch.setattr(smd, "harness_target", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not start a cluster")))
    assert smd.main(["baseline", "--scratch", str(tmp_path / "s"), "--root", str(tmp_path / "root"), "--port", "40001", "--out", str(tmp_path / "o.json")]) == 2
    assert smd.RECIPE_ENV in capsys.readouterr().err
    seen = {}
    monkeypatch.setenv(smd.RECIPE_ENV, str(tmp_path / "from_env"))
    monkeypatch.setattr(smd, "harness_target", lambda root, **kw: smd.Target(pg_bin="/x", host="h", port=40001, user="u", db="suvarna_disposable_mirror"))
    monkeypatch.setattr(smd, "build_mirror_baseline", lambda recipe, *a, **k: seen.update(recipe=str(recipe)) or _good_baseline())
    assert smd.main(["baseline", "--scratch", str(tmp_path / "s"), "--root", str(tmp_path / "root"), "--port", "40001", "--out", str(tmp_path / "o.json")]) == 0
    assert seen["recipe"] == str(tmp_path / "from_env")


def _rehearsal_root(monkeypatch, tmp_path, *, port=55432, with_marker=True, with_data=True):
    root = pathlib.Path(os.path.realpath(tmp_path)) / "rehearsal"
    root.mkdir(mode=0o700)
    os.chmod(root, 0o700)
    monkeypatch.setattr(sr, "DEFAULT_ROOT", str(root))
    lay = sr._Layout(root)
    if with_marker:
        sr._write_marker(lay, port)
    if with_data:
        lay.data.mkdir()
        (lay.data / "PG_VERSION").write_text("15\n")
    return root


def _stub_cluster(monkeypatch, *, started="already_running"):
    calls = []
    monkeypatch.setattr(smd.sr, "init_cluster", lambda *a, **k: calls.append("init") or {})
    monkeypatch.setattr(smd.sr, "start_cluster", lambda root, pg_bin: calls.append("start") or {"state": "running", "result": started})
    monkeypatch.setattr(smd, "run_psql", lambda t, *, sql=None, file=None, on_error_stop, db=None, timeout=900:
                        types.SimpleNamespace(returncode=0, stdout="0" if "count(*)" in (sql or "") else ("" if "pg_database" in (sql or "") else "1"), stderr=""))
    return calls


def test_the_rehearsal_policy_pins_root_port_database_owner_and_never_initialises(monkeypatch, tmp_path):
    root = _rehearsal_root(monkeypatch, tmp_path)
    calls = _stub_cluster(monkeypatch)
    t = smd.harness_target(root, db="rehearsal_mirror", port=55432, policy="rehearsal", owner=sr._user())
    assert calls == ["start"] and t.policy == "rehearsal" and t.port == 55432 and t.started is False and t.host == str(root / "sock")
    assert t.expect == {"data_directory": f"{root}/pg", "port": 55432} and t.url == f"postgresql://{sr._user()}@127.0.0.1:55432/rehearsal_mirror"
    assert sr.rehearsal_policy(t.url) == t.url                                                          # the rehearsal URL guard accepts the verification URL
    started = smd.harness_target(root, db="rehearsal_mirror", port=55432, policy="rehearsal")             # owner defaults to the running user
    assert started.started is False
    calls2 = _stub_cluster(monkeypatch, started="started")
    assert smd.harness_target(root, db="rehearsal_mirror", port=55432, policy="rehearsal").started is True and calls2 == ["start"]


@pytest.mark.parametrize("what", ["other_root", "other_port", "bad_db", "no_marker", "no_data", "wrong_owner", "forbidden_db"])
def test_the_rehearsal_policy_refuses_every_pin_violation(monkeypatch, tmp_path, what):
    root = _rehearsal_root(monkeypatch, tmp_path, with_marker=what != "no_marker", with_data=what != "no_data")
    calls = _stub_cluster(monkeypatch)
    kw = dict(db="rehearsal_mirror", port=55432, policy="rehearsal")
    if what == "other_root":
        other = pathlib.Path(os.path.realpath(tmp_path)) / "elsewhere"
        other.mkdir(mode=0o700)
        root = other
    if what == "other_port":
        kw["port"] = 5499
    if what == "bad_db":
        kw["db"] = "postgres"
    if what == "forbidden_db":
        kw["db"] = "suvarna_disposable_x"
    if what == "wrong_owner":
        kw["owner"] = "somebody_else"
    with pytest.raises(smd.MirrorError):
        smd.harness_target(root, **kw)
    assert calls == []                                                                                     # nothing was started or initialised


def test_a_disposable_baseline_never_uses_the_rehearsal_port_and_an_existing_database_must_be_empty(monkeypatch, tmp_path):
    calls = _stub_cluster(monkeypatch)
    with pytest.raises(smd.MirrorError, match="never used"):
        smd.harness_target(tmp_path / "root", db="suvarna_disposable_m", port=55432)
    assert calls == []
    seen = []

    def fake(t, *, sql=None, file=None, on_error_stop, db=None, timeout=900):
        seen.append(sql)
        out = "1" if "pg_database" in sql else "3"                     # the database exists and holds 3 tables
        return types.SimpleNamespace(returncode=0, stdout=out, stderr="")
    monkeypatch.setattr(smd, "run_psql", fake)
    with pytest.raises(smd.MirrorError, match="not empty"):
        smd.harness_target(tmp_path / "root", db="suvarna_disposable_m", port=40123)
    assert smd.harness_target(tmp_path / "root", db="suvarna_disposable_m", port=40123, allow_existing_db=True).db == "suvarna_disposable_m"


def test_baseline_cli_rehearsal_policy_needs_the_explicit_pins(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(smd, "harness_target", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not start a cluster")))
    base = ["baseline", "--recipe", str(tmp_path), "--scratch", str(tmp_path / "s"), "--root", str(tmp_path / "root"), "--port", "55432",
            "--policy", "rehearsal", "--out", str(tmp_path / "o.json")]
    assert smd.main(base) == 2 and "explicit pins" in capsys.readouterr().err
    assert smd.main(base + ["--owner", "Dev"]) == 2
    assert smd.main(base + ["--owner", "Dev", "--data-directory", str(tmp_path / "other" / "pg")]) == 2 and "<root>/pg" in capsys.readouterr().err
    assert smd.main(base + ["--db", "postgres", "--owner", "Dev", "--data-directory", str(tmp_path / "root" / "pg")]) == 2


def test_baseline_cli_passes_the_rehearsal_pins_through_and_stops_only_what_it_started(monkeypatch, tmp_path, capsys):
    got, stopped = {}, []
    root = tmp_path / "root"
    monkeypatch.setattr(smd, "harness_target", lambda r, **kw: got.update(kw) or smd.Target(pg_bin="/x", host="h", port=55432, user="u", db=kw["db"], policy=kw["policy"],
                                                                                           started=kw.get("started", False)))
    monkeypatch.setattr(smd.sr, "stop_cluster", lambda r, pg_bin: stopped.append(str(r)))
    monkeypatch.setattr(smd, "build_mirror_baseline", lambda *a, **k: _good_baseline())
    args = ["baseline", "--recipe", str(tmp_path), "--scratch", str(tmp_path / "s"), "--root", str(root), "--port", "55432", "--policy", "rehearsal",
            "--owner", "Dev", "--data-directory", str(root / "pg"), "--out", str(tmp_path / "o.json")]
    assert smd.main(args) == 0
    assert got["policy"] == "rehearsal" and got["owner"] == "Dev" and got["db"] == "rehearsal_mirror" and got["port"] == 55432 and stopped == []      # it did not start it


def test_harness_target_starts_the_owned_cluster_and_creates_the_database_once(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(smd.sr, "init_cluster", lambda root, port, pg_bin: calls.append(("init", str(root), port)) or {})
    monkeypatch.setattr(smd.sr, "start_cluster", lambda root, pg_bin: calls.append(("start", str(root))) or {"state": "running", "result": "started"})
    seen_sql = []
    exists = {"db": False}

    def fake_psql(t, *, sql=None, file=None, on_error_stop, db=None, timeout=900):
        seen_sql.append((t.db, sql))
        if sql.startswith("CREATE DATABASE"):
            exists["db"] = True
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        if "count(*)" in sql:
            return types.SimpleNamespace(returncode=0, stdout="0", stderr="")
        return types.SimpleNamespace(returncode=0, stdout="1" if exists["db"] else "", stderr="")
    monkeypatch.setattr(smd, "run_psql", fake_psql)
    t = smd.harness_target(tmp_path / "root", db="suvarna_disposable_m", port=40123)
    assert calls == [("init", str(tmp_path / "root"), 40123), ("start", str(tmp_path / "root"))] and t.started is True
    assert [q for _d, q in seen_sql if q.startswith("CREATE DATABASE")] == ['CREATE DATABASE "suvarna_disposable_m"']
    assert t.host == str(tmp_path / "root" / "sock") and t.port == 40123 and t.db == "suvarna_disposable_m" and t.expect == {"data_directory": str(tmp_path / "root" / "pg"), "port": 40123}
    seen_sql.clear()
    smd.harness_target(tmp_path / "root", db="suvarna_disposable_m", port=40123)           # second call: the database exists and is empty, no CREATE
    assert not [q for _d, q in seen_sql if q.startswith("CREATE DATABASE")]


def test_harness_target_refuses_a_cluster_that_is_not_running(monkeypatch, tmp_path):
    monkeypatch.setattr(smd.sr, "init_cluster", lambda *a, **k: {})
    monkeypatch.setattr(smd.sr, "start_cluster", lambda *a, **k: {"state": "foreign"})
    with pytest.raises(smd.MirrorError, match="not running"):
        smd.harness_target(tmp_path / "root", db="suvarna_disposable_m", port=40123)


def test_harness_target_never_uses_a_forbidden_port(tmp_path):
    for port in sorted(sr.FORBIDDEN_PORTS):
        with pytest.raises(sr.RehearsalError):
            smd.harness_target(tmp_path / "root", db="suvarna_disposable_m", port=port)


def test_baseline_cli_writes_a_valid_document_and_stops_only_a_cluster_it_started(monkeypatch, tmp_path, capsys):
    stopped = []
    state = {"started": True}
    monkeypatch.setattr(smd, "harness_target", lambda root, **kw: smd.Target(pg_bin="/x", host="h", port=40001, user="u", db="suvarna_disposable_mirror",
                                                                            started=state["started"]))
    monkeypatch.setattr(smd.sr, "stop_cluster", lambda root, pg_bin: stopped.append(str(root)))
    monkeypatch.setattr(smd, "build_mirror_baseline", lambda *a, **k: _good_baseline())
    out = tmp_path / "MIRROR_BASELINE.json"
    args = ["baseline", "--recipe", str(tmp_path), "--scratch", str(tmp_path / "s"), "--root", str(tmp_path / "root"), "--port", "40001", "--out", str(out)]
    real_root = os.path.realpath(str(tmp_path / "root"))
    assert smd.main(args) == 0 and stopped == [real_root]
    assert smd.validate_baseline(json.loads(out.read_text())) == [] and smd.main(["validate-baseline", str(out)]) == 0
    capsys.readouterr()
    bad = _good_baseline()
    bad["result"] = "FAIL"
    bad["steps"][4]["status"] = "FAILED"
    monkeypatch.setattr(smd, "build_mirror_baseline", lambda *a, **k: bad)
    assert smd.main(args) == 4 and len(stopped) == 2                      # a failed baseline exits 4 and the cluster is still stopped

    def boom(*a, **k):
        raise smd.MirrorError("recipe refused")
    monkeypatch.setattr(smd, "build_mirror_baseline", boom)
    assert smd.main(args) == 2 and len(stopped) == 3                      # a refusal exits 2 and the cluster is still stopped
    assert smd.main(args + ["--keep-running"]) == 2 and len(stopped) == 3
    state["started"] = False
    assert smd.main(args) == 2 and len(stopped) == 3                      # a cluster that was already running is left running
    (tmp_path / "junk.json").write_text("{not json")
    assert smd.main(["validate-baseline", str(tmp_path / "junk.json")]) == 2
    assert smd.main(["validate-baseline", str(tmp_path / "absent.json")]) == 2


# ═════════════════════════ 6. source mutants (pure behaviour, no database) ═════════════════════════

def load_module(src: str, name: str):
    mod = types.ModuleType(name)
    mod.__file__ = str(GOV / "suvarna_mirror_drill.py")
    sys.modules[name] = mod
    exec(compile(src, f"<{name}>", "exec"), mod.__dict__)         # noqa: S102 - the repo's own source, one mutation applied
    return mod


def _dup_file(tmp):
    f = tmp / "dup_inv.json"
    f.write_text('{"a": 1, "a": 2}')
    return f


_GIT_HEAVY_CHECKS = ("dec_", "ts_")                     # name prefixes of the checks that spawn git processes (decision register, text seed)


class _FirstFailure(Exception):
    """Raised by `check` when `first_only` is set: a mutant is dead as soon as ONE invariant fails, so the rest of the battery need not run."""

    def __init__(self, bad):
        super().__init__(bad)
        self.bad = bad


def invariants(m, tmp: pathlib.Path, first_only: bool = False, round10: bool = True) -> list[str]:
    """The failed invariants of module `m`. `first_only` stops at the first failure (enough to kill a mutant; the unmutated module is always
    run in full by test_the_invariants_hold_on_the_real_module). `round10=False` leaves out the git-heavy decision-register and text-seed
    block (about 60 percent of the cost): a mutant that the rest of the battery already kills needs nothing more."""
    try:
        return _invariants_body(m, tmp, first_only, round10)
    except _FirstFailure as e:
        return e.bad


def _invariants_body(m, tmp: pathlib.Path, first_only: bool, round10: bool = True) -> list[str]:
    bad: list[str] = []

    def check(name, fn):
        if not round10 and name.startswith(_GIT_HEAVY_CHECKS):
            return                                                # the git-heavy decision-register / text-seed checks: only for mutants the rest did not kill
        try:
            ok = bool(fn())
        except Exception:                                         # noqa: BLE001 - a crash is a failed invariant
            ok = False
        if not ok:
            bad.append(name)
            if first_only:
                raise _FirstFailure(list(bad))

    def raises(exc, fn):
        try:
            fn()
        except exc:
            return True
        return False

    # recipe
    r = make_recipe(tmp / "inv")
    check("copy_ok", lambda: sorted(m.copy_recipe(r, tmp / "inv_s1")) == ["roles", "roles_acl_mirror", "schema", "seed_fixes", "sequences"])
    check("copy_refuses_scratch_in_recipe", lambda: raises(m.MirrorError, lambda: m.copy_recipe(r, r / "x")))
    s2 = tmp / "inv_s2"
    s2.mkdir()
    (s2 / "stale").write_text("x")
    check("copy_refuses_nonempty_scratch", lambda: raises(m.MirrorError, lambda: m.copy_recipe(r, s2)))
    (r / "sql" / "20_sequences.sql").unlink()
    check("copy_refuses_missing", lambda: raises(m.MirrorError, lambda: m.copy_recipe(r, tmp / "inv_s3")))
    (r / "sql" / "20_sequences.sql").symlink_to(r / "sql" / "00_roles.sql")
    check("copy_refuses_symlink", lambda: raises(m.MirrorError, lambda: m.copy_recipe(r, tmp / "inv_s4")))
    (r / "sql" / "20_sequences.sql").unlink()
    (r / "sql" / "20_sequences.sql").write_text(SYN_SEQ)
    (r / "sql" / "30_seed_fixes.sql").unlink()
    (r / "sql" / "30_seed_fixes.sql").mkdir()
    check("copy_refuses_non_regular", lambda: raises(m.MirrorError, lambda: m.copy_recipe(r, tmp / "inv_s5")))
    (r / "sql" / "30_seed_fixes.sql").rmdir()
    (r / "sql" / "30_seed_fixes.sql").write_text(SYN_FIX)
    old_max = m.MAX_RECIPE_BYTES
    m.MAX_RECIPE_BYTES = 10
    check("copy_refuses_oversize", lambda: raises(m.MirrorError, lambda: m.copy_recipe(r, tmp / "inv_s6")))
    m.MAX_RECIPE_BYTES = old_max
    real_copy = m.shutil.copyfile
    m.shutil.copyfile = lambda a, b: (real_copy(a, b), open(b, "ab").write(b"x"))[0]
    try:
        check("copy_refuses_mismatch", lambda: raises(m.MirrorError, lambda: m.copy_recipe(r, tmp / "inv_s7")))
    finally:
        m.shutil.copyfile = real_copy
    check("copy_ok_after_repairs", lambda: len(m.copy_recipe(r, tmp / "inv_s8")) == 5)
    check("schema_only_ok", lambda: m.assert_schema_only(SYN_DUMP) is None)
    check("schema_only_copy", lambda: raises(m.MirrorError, lambda: m.assert_schema_only(SYN_DUMP + "COPY t FROM stdin;\n")))
    check("schema_only_insert", lambda: raises(m.MirrorError, lambda: m.assert_schema_only(SYN_DUMP + "INSERT INTO t VALUES (1);\n")))
    check("restore_removes_line", lambda: "CREATE SCHEMA public;" not in m.derive_schema_restore(SYN_DUMP)[0])
    check("restore_needs_exactly_one", lambda: raises(m.MirrorError, lambda: m.derive_schema_restore(SYN_DUMP + "CREATE SCHEMA public;\n")))
    check("restore_needs_one_not_zero", lambda: raises(m.MirrorError, lambda: m.derive_schema_restore("SELECT 1;\n")))
    dump_v = SYN_DUMP.replace("w text\n", "w text,\n    emb public.vector(768)\n")
    check("vector_shim", lambda: "public.vector" not in m.derive_schema_restore(dump_v, vector_available=False)[0] and "public.vector" in m.derive_schema_restore(dump_v)[0])
    check("error_classes", lambda: m.error_classes("ERROR:  x already exists\nERROR:  y does not exist\n") == {"already_exists": 1, "does_not_exist": 1})
    # baseline document
    good = _good_baseline()
    good["tool_sha256"] = m.tool_sha256()
    check("baseline_valid", lambda: m.validate_baseline(good) == [] and m.derive_baseline_result(good) == "PASS")
    for label, mut in (("failed_step", lambda d: d["steps"][4].update({"status": "FAILED"})), ("problem", lambda d: d["verification"].update({"problems": ["x"]})),
                       ("skipped_schema", lambda d: d["steps"][4].update({"status": "SKIPPED"})), ("order", lambda d: d["steps"].reverse()),
                       ("ok_flag", lambda d: d["verification"].update({"ok": True, "tables_checked": 0})),
                       ("forbidden_port", lambda d: d["cluster"].update({"port": 5432})), ("non_loopback", lambda d: d["cluster"].update({"host": "10.1.1.1"}))):
        d = copy.deepcopy(good)
        mut(d)
        check(f"baseline_refuses_{label}", lambda d=d: m.validate_baseline(d) != [])
    d = copy.deepcopy(good)
    d["steps"][-1]["status"] = "UNMEASURED"
    check("baseline_unmeasured", lambda: m.derive_baseline_result(d) == "UNMEASURED")
    d = copy.deepcopy(good)
    d["steps"][2]["status"] = "FAILED"
    check("baseline_fail", lambda: m.derive_baseline_result(d) == "FAIL")
    d = copy.deepcopy(good)
    d["steps"][2]["status"] = "FAILED"
    d["steps"][-1]["status"] = "UNMEASURED"
    check("baseline_fail_beats_unmeasured", lambda: m.derive_baseline_result(d) == "FAIL")
    d = copy.deepcopy(good)
    d["steps"][4]["status"] = "SKIPPED"
    check("baseline_schema_skipped_is_fail", lambda: m.derive_baseline_result(d) == "FAIL")
    d = copy.deepcopy(good)
    d["verification"] = {"tables_checked": 3, "problems": ["x"], "ok": False}
    check("baseline_unverified_is_fail", lambda: m.derive_baseline_result(d) == "FAIL")
    d = copy.deepcopy(good)
    d["steps"][3], d["steps"][5] = d["steps"][5], d["steps"][3]
    d["result"] = "FAIL"
    check("baseline_order_refused_even_if_result_fail", lambda: m.validate_baseline(d) != [])
    d = copy.deepcopy(good)
    d["steps"][4]["status"] = "SKIPPED"
    d["result"] = "FAIL"
    check("baseline_only_seed_fixes_may_skip", lambda: m.validate_baseline(d) != [])
    d = copy.deepcopy(good)
    d["tool_sha256"] = H
    check("baseline_tool_sha_bound", lambda: m.validate_baseline(d) != [])
    # fingerprint output + drill
    prod, reh = _pair()

    def v(doc, side):
        return m.validate_fingerprint_output(doc, D5, side=side)
    check("output_valid", lambda: v(prod, "production") == [] and v(reh, "rehearsal") == [])
    for label, mut, side in (("definition", lambda d: d.update({"definition": "other/1"}), "production"),
                             ("declsha", lambda d: d.update({"declarations_sha256": H}), "production"),
                             ("undeclared", lambda d: (d["tables"].update({"a_und": {}}), d["fingerprints"].update({"a_und": H})), "production"),
                             ("composite", lambda d: d["fingerprints"].update({"a_multi": H}), "production"),
                             ("missing_table", lambda d: d["tables"]["a_multi"].pop("syn_m2"), "production"),
                             ("rows", lambda d: d["tables"]["a_0"]["syn_t0"].update({"rows": -1}), "production"),
                             ("side", lambda d: d.update({"side": "rehearsal"}), "production"),
                             ("stage", lambda d: d.update({"stage": "baseline"}), "production"),
                             ("receipt", lambda d: d.update({"rebuild": None}), "rehearsal")):
        dd = copy.deepcopy(prod if side == "production" else reh)
        mut(dd)
        check(f"output_refuses_{label}", lambda dd=dd, side=side: v(dd, side) != [])
    ex_tab = copy.deepcopy(prod)
    ex_tab["tables"]["a_0"]["extra"] = {"sha256": H, "rows": 1}
    ex_tab["fingerprints"]["a_0"] = m.fd.composite_fingerprint({n: x["sha256"] for n, x in ex_tab["tables"]["a_0"].items()})
    check("output_refuses_extra_table_even_if_composed", lambda: v(ex_tab, "production") != [])
    prod_rb = copy.deepcopy(prod)
    prod_rb["rebuild"] = {"run_id": "x", "orchestrator_commit": SHA40}
    check("output_refuses_production_rebuild", lambda: v(prod_rb, "production") != [])
    check("drill_pass_scoped", lambda: m.build_drill(prod, reh, D5, None, commit=SHA40)[0]["result"] == "PASS_DECLARED_ONLY")
    check("drill_expected_units", lambda: m.build_drill(prod, reh, D5, None, commit=SHA40)[0]["expected_assets"] == D5.expected_assets())
    check("drill_carries_coverage_and_rows", lambda: m.build_drill(prod, reh, D5, None, commit=SHA40)[0]["coverage"] == D5.drill_coverage()
          and m.build_drill(prod, reh, D5, None, commit=SHA40)[0]["rows"]["a_0"]["production"] == {"syn_t0": 5})
    check("drill_coverage_undeclared", lambda: set(m.build_drill(prod, reh, D5, None, commit=SHA40)[1]["undeclared"]) == {"a_und", "a_svc"})
    diff = copy.deepcopy(reh)
    _later(diff, prod)                                                  # a_roll differs only by rows after the production horizon
    flagless = copy.deepcopy(reh)
    flagless["tables"]["a_0"]["syn_t0"]["sha256"] = H
    flagless["fingerprints"]["a_0"] = H
    check("drill_rolling_code_refused_on_deterministic_unit", lambda: m.build_drill(prod, flagless, D5, {"a_0": _ex()}, commit=SHA40)[0]["result"] == "FAIL")
    check("drill_rolling_code_ok_on_flagged_unit", lambda: m.build_drill(prod, diff, D5, {"a_roll": _ex()}, commit=SHA40)[0]["result"] == "PASS_DECLARED_ONLY")
    check("drill_group_members_reported", lambda: m.build_drill(prod, reh, D5, None, commit=SHA40)[1]["unit_status"]["grp_g_shared"]["members"] == ["a_gm1", "a_gm2"])
    ep, er = copy.deepcopy(prod), copy.deepcopy(reh)
    for dd_ in (ep, er):
        _empty_unit(dd_, "a_multi")
    check("drill_empty_both_unmeasured", lambda: m.build_drill(ep, er, D5, None, commit=SHA40)[0]["result"] == "UNMEASURED")
    bad_rows = copy.deepcopy(reh)
    bad_rows["tables"]["a_0"]["syn_t0"]["sha256"] = prod["tables"]["a_0"]["syn_t0"]["sha256"]
    bad_rows["fingerprints"]["a_0"] = prod["fingerprints"]["a_0"]
    bad_rows["tables"]["a_0"]["syn_t0"]["rows"] = 6
    check("drill_row_cross_check", lambda: m.build_drill(prod, bad_rows, D5, None, commit=SHA40)[0]["result"] == "FAIL")
    emp_h = copy.deepcopy(prod)
    emp_h["tables"]["a_0"]["syn_t0"]["sha256"] = m.fd.empty_table_fingerprint(D5, "a_0", "syn_t0")
    emp_h["fingerprints"]["a_0"] = emp_h["tables"]["a_0"]["syn_t0"]["sha256"]
    check("output_refuses_empty_hash_with_rows", lambda: v(emp_h, "production") != [])
    zero_rows = copy.deepcopy(prod)
    zero_rows["tables"]["a_0"]["syn_t0"]["rows"] = 0
    check("output_refuses_zero_rows_with_data_hash", lambda: v(zero_rows, "production") != [])
    only_fp = copy.deepcopy(prod)
    only_fp["tables"].pop("a_1")
    check("output_refuses_unit_in_fingerprints_only", lambda: v(only_fp, "production") != [])
    only_tab = copy.deepcopy(prod)
    only_tab["fingerprints"].pop("a_1")
    check("output_refuses_unit_in_tables_only", lambda: v(only_tab, "production") != [])
    nil_run = copy.deepcopy(reh)
    nil_run["rebuild"]["run_id"] = "00000000-0000-0000-0000-000000000000"
    check("output_refuses_nil_run_id", lambda: v(nil_run, "rehearsal") != [])
    check("real_uuid", lambda: m.real_uuid("5e57e57e-5e57-4e57-8e57-5e57e57e57e5") and not m.real_uuid("-" * 36) and not m.real_uuid("00000000-0000-0000-0000-000000000000")
          and not m.real_uuid("5E57E57E-5E57-4E57-8E57-5E57E57E57E5") and not m.real_uuid("5e57e57e5e574e578e575e57e57e57e5") and not m.real_uuid("{5e57e57e-5e57-4e57-8e57-5e57e57e57e5}"))
    check("drill_difference_fails", lambda: m.build_drill(prod, diff, D5, None, commit=SHA40)[0]["result"] == "FAIL")
    check("drill_hint", lambda: m.build_drill(prod, diff, D5, None, commit=SHA40)[1]["differences_with_hints"][0]["reproducibility"] == ["rolling_horizon", "platform_bound"])
    check("drill_as_of", lambda: raises(m.MirrorError, lambda: m.build_drill(prod, {**reh, "as_of": "2026-10-04"}, D5, None, commit=SHA40)))
    base = out_doc(D5, "rehearsal", stage="baseline", rebuild=None)
    check("drill_needs_after_rebuild", lambda: raises(m.MirrorError, lambda: m.build_drill(prod, base, D5, None, commit=SHA40)))
    wrong = copy.deepcopy(reh)
    wrong["rebuild"]["orchestrator_commit"] = "2" * 40
    check("drill_commit_binding", lambda: raises(m.MirrorError, lambda: m.build_drill(prod, wrong, D5, None, commit=SHA40)))
    # status / reader spec
    blf = copy.deepcopy(good)
    blf["result"] = "FAIL"
    check("status_baseline_fail_unmeasured", lambda: {x["step"]: x["state"] for x in m.drill_status(D5, baseline=blf)["steps"]}["mirror_baseline"] == "UNMEASURED")
    check("status_unmeasured", lambda: m.drill_status(D5)["result"] == "UNMEASURED")
    sts = lambda **kw: {x["step"]: x["state"] for x in m.drill_status(D5, **kw)["steps"]}  # noqa: E731
    check("status_shape_checked_only", lambda: sts(baseline=good, production=prod, rehearsal=reh)["production_fingerprints"] == "SHAPE_CHECKED"
          and sts(baseline=good, production=prod, rehearsal=reh)["as_of_pin"] == "SHAPE_CHECKED" and sts(baseline=good, production=prod, rehearsal=reh)["mirror_baseline"] == "SHAPE_CHECKED")
    check("status_receipt_is_a_claim", lambda: sts(rehearsal=reh)["rehearsal_l0_rebuild"] == "CLAIMED_UNVERIFIED")
    check("status_receipt_verified_by_record", lambda: sts(rehearsal=reh, build_record=_record())["rehearsal_l0_rebuild"] == "MEASURED")
    check("status_receipt_bad_record", lambda: sts(rehearsal=reh, build_record=_record(state="running"))["rehearsal_l0_rebuild"] == "CLAIMED_UNVERIFIED")
    check("verify_receipt", lambda: m.verify_rebuild_receipt(reh["rebuild"], _record(), D5) == [] and m.verify_rebuild_receipt(reh["rebuild"], _record(commit="2" * 40), D5)
          and m.verify_rebuild_receipt(reh["rebuild"], _record(run_id="6e57e57e-5e57-4e57-8e57-5e57e57e57e5"), D5))
    check("verify_receipt_all_assets", lambda: m.verify_rebuild_receipt(reh["rebuild"], _record(assets=[]), D5) != [])
    check("status_no_complete_inputs_verdict", lambda: "COMPLETE_INPUTS" not in json.dumps(m.drill_status(D5, baseline=good, production=prod, rehearsal=reh, build_record=_record())))
    check("status_rejects_baseline_stage", lambda: {x["step"]: x["state"] for x in m.drill_status(D5, rehearsal=base)["steps"]}["rehearsal_l0_rebuild"] == "UNMEASURED")
    check("reader_spec", lambda: len(m.reader_spec(D5)["selects"]) == 10)
    check("probe_aggregate_only", lambda: all("count(*)" in p["sql"] and "WHERE" not in p["sql"] for p in m.OWNERSHIP_PROBES))
    check("psql_needs_exactly_one", lambda: raises(m.MirrorError, lambda: m.run_psql(m.Target(pg_bin="/x", host="127.0.0.1", port=40001, user="u", db="d"), on_error_stop=True)))

    class Boom:
        def __getattr__(self, n):
            raise AssertionError("must not touch the connection")
    dd5 = syn_baseline_decls()
    good_kw = dict(stage="baseline", as_of="2026-10-03", commit=SHA40)
    check("fp_needs_receipt_for_after_rebuild", lambda: raises(m.MirrorError, lambda: m.rehearsal_fingerprints(Boom(), dd5, **{**good_kw, "stage": "after_rebuild"})))
    check("fp_refuses_receipt_on_baseline", lambda: raises(m.MirrorError, lambda: m.rehearsal_fingerprints(Boom(), dd5, **good_kw, rebuild={"run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "orchestrator_commit": SHA40})))
    check("fp_refuses_bad_as_of", lambda: raises(m.MirrorError, lambda: m.rehearsal_fingerprints(Boom(), dd5, **{**good_kw, "as_of": "bad"})))
    check("forbidden_port", lambda: raises(m.MirrorError, lambda: m.run_psql(m.Target(pg_bin="/x", host="127.0.0.1", port=5432, user="u", db="d"), sql="SELECT 1", on_error_stop=True)))
    # database names and the baseline guards
    check("db_disposable_ok", lambda: m.validate_db_name("suvarna_disposable_m", "disposable") == "suvarna_disposable_m")
    check("db_disposable_refuses", lambda: all(raises(m.MirrorError, lambda d=d: m.validate_db_name(d, "disposable")) for d in ("postgres", "rehearsal", "suvarna_disposable; x", "", None)))
    check("db_rehearsal_ok_and_refuses", lambda: m.validate_db_name("rehearsal_m", "rehearsal") and raises(m.MirrorError, lambda: m.validate_db_name("suvarna_disposable_m", "rehearsal")))
    check("db_unknown_policy", lambda: raises(m.MirrorError, lambda: m.validate_db_name("rehearsal", "production")))
    good_recipe = make_recipe(tmp / "inv_br")
    check("baseline_db_first", lambda: raises(m.MirrorError, lambda: m.build_mirror_baseline(good_recipe, tmp / "inv_bs", m.Target(pg_bin="/x", host="h", port=40001, user="u", db="postgres"))))
    check("baseline_no_scratch_before_db_check", lambda: not (tmp / "inv_bs").exists())
    check("harness_db_first", lambda: raises(m.MirrorError, lambda: m.harness_target(tmp / "no_root", db="postgres", port=40001)))
    check("harness_disposable_not_rehearsal_port", lambda: raises(m.MirrorError, lambda: m.harness_target(tmp / "no_root", db="suvarna_disposable_m", port=55432)))
    check("quote", lambda: m._quote_ident('a"b') == '"a""b"' and m._quote_lit("a'b") == "'a''b'")
    check("strict_rd", lambda: raises(Exception, lambda: m._rd(_dup_file(tmp))))
    # round 3
    dseed = syn_decls(seeded_group=True)
    pS, rS = out_doc(dseed, "production"), out_doc(dseed, "rehearsal")
    check("drill_seeded_not_counted", lambda: m.build_drill(pS, rS, dseed, None, commit=SHA40)[0]["seeded"] == {"grp_g_shared": "equal"}
          and "grp_g_shared" not in m.build_drill(pS, rS, dseed, None, commit=SHA40)[0]["equal"])
    check("report_headline_and_limits", lambda: m.build_drill(pS, rS, dseed, None, commit=SHA40)[1]["headline"].startswith("PASS_DECLARED_ONLY:")
          and "SEEDED" in m.build_drill(pS, rS, dseed, None, commit=SHA40)[1]["headline"] and len(m.build_drill(pS, rS, dseed, None, commit=SHA40)[1]["limits"]) == 3)
    check("report_seeded_unit_status", lambda: m.build_drill(pS, rS, dseed, None, commit=SHA40)[1]["unit_status"]["grp_g_shared"] == {"status": "seeded:equal", "members": ["a_gm1", "a_gm2"]})
    only_seeded = _seeded_decls(True)
    check("drill_only_seeded_unmeasured", lambda: m.build_drill(out_doc(only_seeded, "production"), out_doc(only_seeded, "rehearsal"), only_seeded, None, commit=SHA40)[0]["result"] == "UNMEASURED")
    check("headline_names", lambda: "bg_remedies" in m.coverage_headline("X", {"declared": ["a"], "partial": {"bg_remedies": ["t"]}, "undeclared": {"u1": "c"}, "non_deterministic": {}, "seeded": ["grp_x"], "units": ["a", "grp_x"]}, 3, {"grp_x": "equal"})
          and "u1" in m.coverage_headline("X", {"declared": ["a"], "partial": {}, "undeclared": {"u1": "c"}, "non_deterministic": {}, "seeded": [], "units": ["a"]}, 3)
          and "grp_x [equal]" in m.coverage_headline("X", {"declared": ["a"], "partial": {}, "undeclared": {}, "non_deterministic": {}, "seeded": ["grp_x"], "units": ["a", "grp_x"]}, 3, {"grp_x": "equal"}))
    check("limits_text", lambda: any("STATEMENT level" in x for x in m.LIMITS_TEXT) and len(m.LIMITS_TEXT) == 3)
    check("build_record_spec", lambda: m.build_record_spec(D5)["declared_assets_that_must_be_complete"] == D5.declared_assets() and m.drill_status(D5)["build_record_expected"]["schema"] == m.BUILD_RECORD_SCHEMA)
    # round 4: not_run, partial ownership, open findings, seed
    vr = lambda rec: m.verify_rebuild_receipt(RECEIPT, rec, RD)  # noqa: E731
    check("rec_ok", lambda: vr(_rrec()) == [])
    check("rec_not_run_outside_list", lambda: vr(_rrec({"bg_ephemeris": {"asset_id": "bg_ephemeris", "state": "not_run", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}})) != [])
    check("rec_not_run_wrong_reason", lambda: vr(_rrec({"bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "not_run", "reason": "NEEDS_AS_OF_PIN"}})) != [])
    check("rec_not_run_no_reason", lambda: vr(_rrec({"bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "not_run"}})) != [])
    check("rec_failed_listed_asset_refused", lambda: vr(_rrec({"bg_sky_calendar": {"asset_id": "bg_sky_calendar", "state": "failed", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}})) != [])
    check("rec_errored_asset_refused", lambda: vr(_rrec({"bg_ghatana": {"asset_id": "bg_ghatana", "state": "error"}})) != [])
    check("rec_failed_with_reason_refused", lambda: vr(_rrec({"bg_ghatana": {"asset_id": "bg_ghatana", "state": "failed", "reason": "NEEDS_AS_OF_PIN"}})) != [])
    check("rec_missing_declared_asset", lambda: vr(_rrec(drop=("bg_ephemeris",))) != [])
    check("rec_missing_listed_asset", lambda: vr(_rrec(drop=("bg_cohort",))) != [])
    check("rec_duplicate_asset", lambda: vr(_rrec(extra=[{"asset_id": "bg_ephemeris", "state": "complete"}])) != [])
    check("rec_unknown_asset", lambda: vr(_rrec(extra=[{"asset_id": "bg_nope", "state": "complete"}])) != [])
    check("rec_unknown_state", lambda: vr(_rrec({"bg_nakshatra": {"asset_id": "bg_nakshatra", "state": "lit"}})) != [])
    check("rec_reason_on_complete", lambda: vr(_rrec({"bg_nakshatra": {"asset_id": "bg_nakshatra", "state": "complete", "reason": "NEEDS_X"}})) != [])
    check("rec_blocked_refused", lambda: vr(_rrec({"bg_nakshatra": {"asset_id": "bg_nakshatra", "state": "blocked"}})) != [])
    check("rec_complete_listed_asset_ok", lambda: vr(_rrec({"bg_cohort": {"asset_id": "bg_cohort", "state": "complete"}})) == [])
    check("rec_spec_lists", lambda: set(m.build_record_spec(RD)["declared_assets_that_may_be_not_run"]) == {"bg_sky_calendar", "bg_cohort", "bg_muhurta_lattice"}
          and "bg_sky_calendar" not in m.build_record_spec(RD)["declared_assets_that_must_be_complete"])
    check("status_expects_not_run", lambda: "not_run" in {x["step"]: x for x in m.drill_status(RD)["steps"]}["rehearsal_l0_rebuild"]["detail"]["expects"])
    pdr, prr = out_doc(RD, "production"), out_doc(RD, "rehearsal")
    for t_, mm in prr["tables"]["bg_formula_constants"].items():
        mm["sha256"] = hashlib.sha256(f"mig{t_}".encode()).hexdigest()
    prr["fingerprints"]["bg_formula_constants"] = prr["tables"]["bg_formula_constants"]["brahma_formula_constants"]["sha256"]
    check("drill_partial_ownership_reported", lambda: m.build_drill(pdr, prr, RD, None, commit=SHA40)[0]["result"] == "PASS_DECLARED_ONLY"
          and m.build_drill(pdr, prr, RD, None, commit=SHA40)[1]["unit_status"]["bg_formula_constants"]["partial_ownership"].startswith("partial: writer-only rows compared")
          and "2 partial-ownership units" in m.build_drill(pdr, prr, RD, None, commit=SHA40)[1]["headline"]
          and "partial: writer-only rows compared" in m.build_drill(pdr, prr, RD, None, commit=SHA40)[1]["headline"]
          and "expected migration_owned_rows" in m.build_drill(pdr, prr, RD, None, commit=SHA40)[1]["headline"]
          and "bg_formula_constants (brahma_formula_constants)" in m.build_drill(pdr, prr, RD, None, commit=SHA40)[1]["headline"])
    # round 7: runtime, container expectation
    rtd = lambda rt: {**out_doc(D5, "rehearsal"), "rebuild": {**RECEIPT, "runtime": rt}}  # noqa: E731
    check("rt_receipt_valid", lambda: m.validate_fingerprint_output(out_doc(D5, "rehearsal"), D5, side="rehearsal") == [] and m.verify_rebuild_receipt(RECEIPT, _rrec(), RD) == [])
    check("rt_receipt_requires_runtime", lambda: m.validate_fingerprint_output({**out_doc(D5, "rehearsal"), "rebuild": {k: v for k, v in RECEIPT.items() if k != "runtime"}}, D5, side="rehearsal")
          and m.verify_rebuild_receipt({k: v for k, v in RECEIPT.items() if k != "runtime"}, _rrec(), RD))
    check("rt_receipt_validates_runtime", lambda: all(m.validate_fingerprint_output(rtd(b), D5, side="rehearsal") and m.verify_rebuild_receipt({**RECEIPT, "runtime": b}, _rrec(), RD) for b in RT_BAD))
    check("rt_fp_refuses_bad_runtime", lambda: all(raises(m.MirrorError, lambda b=b: m.rehearsal_fingerprints(Boom(), dd5, stage="after_rebuild", as_of="2026-10-03", commit=SHA40,
                                                                                                                   rebuild={**RECEIPT, "runtime": b})) for b in RT_BAD))
    offp, offr = _off_linux()
    check("rt_drill_claims_platform_bound", lambda: m.build_drill(offp, offr, RD, None, commit=SHA40)[0]["claimed_unverified"] == ["bg_cohort", "bg_sky_calendar"]
          and not {"bg_cohort", "bg_sky_calendar"} & set(m.build_drill(offp, offr, RD, None, commit=SHA40)[0]["equal"]))
    check("rt_drill_linux_counts", lambda: m.build_drill(out_doc(RD, "production"), out_doc(RD, "rehearsal"), RD, None, commit=SHA40)[0]["claimed_unverified"] == []
          and "bg_cohort" in m.build_drill(out_doc(RD, "production"), out_doc(RD, "rehearsal"), RD, None, commit=SHA40)[0]["equal"])
    check("rt_report", lambda: m.build_drill(offp, offr, RD, None, commit=SHA40)[1]["unit_status"]["bg_cohort"]["status"].startswith("CLAIMED_UNVERIFIED")
          and "2 platform-bound units CLAIMED_UNVERIFIED (rebuilt off linux/amd64: never equal, never counted): bg_cohort, bg_sky_calendar" in m.build_drill(offp, offr, RD, None, commit=SHA40)[1]["headline"]
          and "rebuild runtime: darwin/arm64" in m.build_drill(offp, offr, RD, None, commit=SHA40)[1]["headline"]
          and m.build_drill(offp, offr, RD, None, commit=SHA40)[1]["claimed_unverified"] == ["bg_cohort", "bg_sky_calendar"] and m.build_drill(offp, offr, RD, None, commit=SHA40)[1]["runtime"]["platform"] == "darwin/arm64")
    check("rt_status_linux_step", lambda: {x["step"]: x["state"] for x in m.drill_status(RD, rehearsal=offr)["steps"]}["linux_amd64_runtime"] == "CLAIMED_UNVERIFIED"
          and {x["step"]: x["state"] for x in m.drill_status(RD, rehearsal=out_doc(RD, "rehearsal"))["steps"]}["linux_amd64_runtime"] == "SHAPE_CHECKED"
          and {x["step"]: x["state"] for x in m.drill_status(RD)["steps"]}["linux_amd64_runtime"] == "UNMEASURED")
    check("container_expectation", lambda: m.build_record_spec(RD)["container_run_expectation"]["expected_complete_count"] == "33 of 34"
          and m.build_record_spec(RD)["container_run_expectation"]["expected_not_run"] == {"bg_muhurta_lattice": "NEEDS_AS_OF_PIN"}
          and "bg_cohort" in m.build_record_spec(RD)["container_run_expectation"]["expected_complete"] and "bg_gochara_arcs" in m.build_record_spec(RD)["container_run_expectation"]["expected_complete"])
    check("container_status_text", lambda: "33 of 34 declared assets are expected complete" in {x["step"]: x for x in m.drill_status(RD)["steps"]}["rehearsal_l0_rebuild"]["detail"]["expects"])
    check("receipt_spec_in_record_spec", lambda: m.build_record_spec(RD)["receipt_expected"]["keys"]["runtime"].startswith("REQUIRED"))
    # round 8: projections
    ep, er = _eph_pair()
    ep2, er2 = _eph_pair(change_columns_only=False)
    check("eph_limited_passes", lambda: m.build_drill(ep, er, RD_ED, EPH_EXPL, commit=SHA40)[0]["result"] == "PASS_DECLARED_ONLY"
          and m.build_drill(ep, er, RD_ED, EPH_EXPL, commit=SHA40)[0]["known_differences"][0]["limited_to_columns"] is True)
    check("eph_not_limited_fails", lambda: m.build_drill(ep2, er2, RD_ED, EPH_EXPL, commit=SHA40)[0]["result"] == "FAIL"
          and m.build_drill(ep2, er2, RD_ED, EPH_EXPL, commit=SHA40)[0]["unexplained"] == ["bg_ephemeris"])
    check("eph_hints", lambda: m.build_drill(ep, er, RD_ED, EPH_EXPL, commit=SHA40)[1]["expected_differences_status"][0]["hint"].endswith("KNOWN DIFFERENCE (tracked: synthetic tracked change (test fixture)): expected, visible, never equal.")
          and m.build_drill(ep2, er2, RD_ED, EPH_EXPL, commit=SHA40)[1]["expected_differences_status"][0]["hint"].startswith("NOT limited to"))
    check("eph_report_fields", lambda: m.build_drill(ep, er, RD_ED, EPH_EXPL, commit=SHA40)[1]["known_differences"] == m.build_drill(ep, er, RD_ED, EPH_EXPL, commit=SHA40)[0]["known_differences"] != []
          and m.build_drill(ep, er, RD_ED, EPH_EXPL, commit=SHA40)[1]["projections"]["bg_ephemeris"]["table"] == "ephemeris_daily")
    check("eph_projections_required_in_file", lambda: m.validate_fingerprint_output(_eph_pair(drop=True)[1], RD_ED, side="rehearsal") != [] and raises(m.MirrorError, lambda: m.build_drill(*_eph_pair(drop=True), RD_ED, EPH_EXPL, commit=SHA40)))
    pbad = lambda edit: (lambda d: (edit(d), m.validate_fingerprint_output(d, RD_ED, side="production"))[1])(out_doc(RD_ED, "production"))  # noqa: E731
    check("proj_valid", lambda: m.validate_fingerprint_output(out_doc(RD_ED, "production"), RD_ED, side="production") == [] and m.validate_fingerprint_output(out_doc(RD_ED, "rehearsal"), RD_ED, side="rehearsal") == [])
    check("proj_units_exact", lambda: pbad(lambda d: d["projections"].update(bg_nakshatra={"nakshatra": {"sha256": H, "rows": 5}})) and pbad(lambda d: d.update(projections={})))
    check("proj_table_exact", lambda: pbad(lambda d: d["projections"].update(bg_ephemeris={"other": {"sha256": H, "rows": 5}})) and pbad(lambda d: d["projections"]["bg_ephemeris"].update(other={"sha256": H, "rows": 5})))
    check("proj_shape", lambda: pbad(lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(sha256="short")) and pbad(lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(rows=True))
          and pbad(lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(x=1)) and pbad(lambda d: d.update(projections=[])))
    check("proj_not_object_message", lambda: any("projections must be an object" in x for x in pbad(lambda d: d.update(projections=[]))))
    check("eph_status_explained_flag", lambda: m.build_drill(ep, er, RD_ED, None, commit=SHA40)[1]["expected_differences_status"][0]["explained"] is False
          and m.build_drill(ep, er, RD_ED, EPH_EXPL, commit=SHA40)[1]["expected_differences_status"][0]["explained"] is True)
    check("no_stale_open_finding", lambda: len(m.OPEN_FINDINGS) == 8 and not any("#3015" in x or "NEEDS_PR_3015" in x for x in m.OPEN_FINDINGS))
    check("real_declarations_have_no_known_difference", lambda: RD.expected_differences() == [] and RD.projection_tables() == {} and out_doc(RD, "production")["projections"] == {}
          and m.build_drill(out_doc(RD, "production"), out_doc(RD, "rehearsal"), RD, None, commit=SHA40)[0]["known_differences"] == [])
    check("proj_rows_equal_table_rows", lambda: pbad(lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(rows=6)))
    check("proj_empty_hash_rule", lambda: pbad(lambda d: d["projections"]["bg_ephemeris"]["ephemeris_daily"].update(sha256=fd.empty_projection_fingerprint(RD_ED, "bg_ephemeris", "ephemeris_daily"))))
    check("reader_spec_projections", lambda: m.reader_spec(RD_ED)["projections"][0]["excluded_columns"] == ["node_mode", "epoch_convention"])
    # round 9: N-135
    hp, hr = _hz_pair()
    hd = lambda p_=None, r_=None, e=A_ROLL_EXPL: m.build_drill(p_ or hp, r_ or hr, D5, e, commit=SHA40)  # noqa: E731
    check("n135_later_build_explained", lambda: hd()[0]["result"] == "PASS_DECLARED_ONLY" and hd()[0]["differences"][0]["explained"]["evidence"]["summary"] == (
        "N-135: rows 8 vs 5 (rehearsal vs production), built-through dates 2026-01-09 vs 2026-01-05 (rehearsal vs production), overlap equal over 5 rows (count and fingerprint, through 2026-01-05)"))
    check("n135_report", lambda: hd()[1]["horizon_evidence"][0]["unit"] == "a_roll" and hd()[1]["unit_status"]["a_roll"]["horizon_evidence"].startswith("N-135: rows 8 vs 5")
          and hd()[1]["horizons"]["a_roll"]["table"] == "syn_roll" and "1 rolling-horizon differences explained by N-135" in hd()[1]["headline"]
          and "a_roll: N-135: rows 8 vs 5" in hd()[1]["headline"])
    check("n135_report_zero", lambda: "0 rolling-horizon differences explained by N-135" in m.build_drill(*_pair(), D5, None, commit=SHA40)[1]["headline"])

    def refused(edit, text):
        p2, r2 = _hz_pair()
        edit(r2)
        d = m.build_drill(p2, r2, D5, A_ROLL_EXPL, commit=SHA40)[0]
        return d["result"] == "FAIL" and d["unexplained"] == ["a_roll"] and any("(N-135)" in x and text in x for x in d["problems"])
    check("n135_overlap_hash_refused", lambda: refused(lambda r: r["horizons"]["a_roll"]["syn_roll"].update(overlap_sha256=hashlib.sha256(b"o").hexdigest()), "overlap fingerprints differ"))
    check("n135_overlap_rows_refused", lambda: refused(lambda r: r["horizons"]["a_roll"]["syn_roll"].update(overlap_rows=4), "overlap row counts differ"))
    check("n135_rehearsal_cutoff_refused", lambda: refused(lambda r: r["horizons"]["a_roll"]["syn_roll"].update(overlap_cutoff="2026-01-07"), "is not the production max_date"))
    check("n135_earlier_refused", lambda: refused(lambda r: (_set_unit(r, "a_roll", hashlib.sha256(b"e").hexdigest(), rows=5),
                                                            r["horizons"]["a_roll"]["syn_roll"].update(max_date="2026-01-04", overlap_cutoff="2026-01-05")), "was not built later"))
    check("n135_no_explanation_no_pass", lambda: hd(e=None)[0]["result"] == "FAIL")

    def file_bad(edit, side="rehearsal"):
        d = copy.deepcopy(hr if side == "rehearsal" else hp)
        edit(d)
        return m.validate_fingerprint_output(d, D5, side=side) != []
    check("n135_file_valid", lambda: m.validate_fingerprint_output(hr, D5, side="rehearsal") == [] and m.validate_fingerprint_output(hp, D5, side="production") == [])
    check("n135_file_units_exact", lambda: file_bad(lambda d: d.update(horizons={})) and file_bad(lambda d: d["horizons"].update(a_0={"syn_t0": dict(d["horizons"]["a_roll"]["syn_roll"])})) and file_bad(lambda d: d.update(horizons=[])))
    check("n135_file_table_exact", lambda: file_bad(lambda d: d["horizons"].update(a_roll={"other": dict(d["horizons"]["a_roll"]["syn_roll"])})) and file_bad(lambda d: d["horizons"]["a_roll"].update(other={})))
    check("n135_file_block_valid", lambda: file_bad(lambda d: d["horizons"]["a_roll"]["syn_roll"].update(x=1)) and file_bad(lambda d: d["horizons"]["a_roll"]["syn_roll"].update(max_date="2026-13-45", overlap_cutoff="2026-13-45")))
    check("n135_file_date_column", lambda: file_bad(lambda d: d["horizons"]["a_roll"]["syn_roll"].update(date_column="other_date")))
    check("n135_file_rows_equal_table", lambda: file_bad(lambda d: d["horizons"]["a_roll"]["syn_roll"].update(rows=9, overlap_rows=5)))
    check("n135_file_whole_overlap_hash", lambda: file_bad(lambda d: d["horizons"]["a_roll"]["syn_roll"].update(overlap_sha256=hashlib.sha256(b"x").hexdigest()), "production"))
    check("n135_file_empty_overlap_hash", lambda: file_bad(lambda d: d["horizons"]["a_roll"]["syn_roll"].update(overlap_rows=0, overlap_cutoff=None)))
    check("n135_file_production_cutoff", lambda: file_bad(lambda d: d["horizons"]["a_roll"]["syn_roll"].update(overlap_cutoff="2026-01-04", overlap_rows=4), "production")
          and not file_bad(lambda d: None, "rehearsal"))
    check("n135_cutoffs_from", lambda: m.horizon_cutoffs_from(hp, D5) == {"a_roll": HZ_MAX} and raises(m.MirrorError, lambda: m.horizon_cutoffs_from(hr, D5)))
    check("n135_reader_spec", lambda: m.reader_spec(RD)["horizons"]["units"][1] == {"unit": "bg_sky_calendar", "table": "bg_sky_calendar", "date_column": "event_datetime_utc"}
          and "SAME streaming pass" in m.reader_spec(RD)["horizons"]["emit"])

    class _Conn:
        read_only = False

        def rollback(self):
            pass
    _seen: dict = {}
    _orig = m.fd.unit_fingerprints

    def _fake(conn, decls, units=None, **kw):
        _seen.update(kw)
        return {"fingerprints": {}, "tables": {}, "projections": {}, "horizons": {"u": "block"}}

    def _cut():
        m.fd.unit_fingerprints = _fake
        try:
            doc_ = m.rehearsal_fingerprints(_Conn(), D5, stage="baseline", as_of="2026-10-03", commit=SHA40, horizon_cutoffs={"a_roll": HZ_MAX})
        finally:
            m.fd.unit_fingerprints = _orig
        return _seen.get("horizon_cutoffs") == {"a_roll": HZ_MAX} and doc_["horizons"] == {"u": "block"}
    check("n135_cutoffs_passed_to_reader", _cut)
    # round 10: the decision register and text seed detectors
    r10 = tmp / "r10"
    r10.mkdir()
    repoA, shA = _scratch_memo(r10, {REG_PATH: _register("N-121", "N-135")}, name="a")
    repoB, shB = _scratch_memo(r10, {"README": "x\n"}, name="b")
    repoC, shC = _scratch_memo(r10, {REG_PATH: _register("N-121")}, name="c")
    repoE, shE = _scratch_memo(r10, {REG_PATH: _register("N-13", "N-1350", "n-135")}, name="e")
    dA, dB, dC, dE = _status_drill(shA), _status_drill(shB), _status_drill(shC, horizon=True), _status_drill(shE, horizon=True)
    _dec_cache: dict = {}

    def dec(repo, drill, **kw):
        k = (str(repo), json.dumps(drill, sort_keys=True, default=str), json.dumps(kw, sort_keys=True, default=str))
        if k not in _dec_cache:
            _dec_cache[k] = m.decisions_step(RD, drill, repo, **kw)
        return _dec_cache[k]
    check("dec_absent", lambda: dec(repoB, dB)["state"] == "UNMEASURED" and dec(repoB, dB)["reason"] == "NEEDS_DECISION_REGISTER_ON_MAIN"
          and dec(repoB, dB)["detail"]["text"] == "decision register not on main")
    check("dec_measured_and_bound", lambda: dec(repoA, dA)["state"] == "MEASURED" and dec(repoA, dA)["detail"]["register_sha256"] == hashlib.sha256(_register("N-121", "N-135").encode()).hexdigest()
          and dec(repoA, dA)["detail"]["records"] == 2)
    check("dec_missing_listed", lambda: dec(repoC, dC)["reason"] == "NEEDS_DECISIONS_IN_REGISTER" and dec(repoC, dC)["detail"]["missing"] == ["N-135"]
          and dec(repoC, dC)["detail"]["text"] == "decision id N-135 not in the register")
    check("dec_prefix_trap", lambda: dec(repoE, dE)["reason"] == "NEEDS_DECISIONS_IN_REGISTER" and dec(repoE, dE)["detail"]["missing"] == ["N-121", "N-135"])
    badreg = {}
    for lbl, body in (("json", _register("N-121") + "{x\n"), ("dupkey", _register("N-121") + '{"id": "N-135", "id": "N-1"}\n'),
                      ("blank", _register("N-121") + "\n" + _register("N-135")), ("array", _register("N-121") + '["N-135"]\n'), ("noid", _register("N-121") + '{"a": 1}\n'),
                      ("empty", "")):
        badreg[lbl] = _scratch_memo(r10, {REG_PATH: body}, name="bad_" + lbl)
    for lbl, (rp, sh_) in badreg.items():
        check(f"dec_bad_register:{lbl}", lambda rp=rp, sh_=sh_: dec(rp, _status_drill(sh_))["reason"] == "NEEDS_VALID_DECISION_REGISTER" and bool(dec(rp, _status_drill(sh_))["detail"]["problems"])
              and "register_sha256" in dec(rp, _status_drill(sh_))["detail"])
    check("dec_blank_line_message", lambda: any("is empty" in x for x in dec(badreg["blank"][0], _status_drill(badreg["blank"][1]))["detail"]["problems"]))
    emptyid = _scratch_memo(r10, {REG_PATH: _register("N-121") + '{"id": " "}\n'}, name="bad_emptyid")
    check("dec_blank_id_refused", lambda: dec(emptyid[0], _status_drill(emptyid[1]))["reason"] == "NEEDS_VALID_DECISION_REGISTER")
    check("dec_register_parser", lambda: m.parse_decision_register(_register("N-1", ("N-1", "superseded"), "N-2").encode()) == ([("N-1", "decided"), ("N-1", "superseded"), ("N-2", "decided")], []) and m.parse_decision_register(b"")[1]
          and m.parse_decision_register(b"\xff")[1] and m.parse_decision_register((_register("N-1") + "\n").encode())[1])
    repoL, shL = _scratch_memo(r10, {REG_PATH: _register("N-121", ("N-135", "superseded"))}, name="l")
    repoM, shM = _scratch_memo(r10, {REG_PATH: _register("N-121", ("N-135", "superseded"), ("N-135", "decided"), "N-17", ("N-17", "superseded"))}, name="mm")
    repoP, shP = _scratch_memo(r10, {REG_PATH: _register("N-121", ("N-135", "decided"), ("N-135", "superseded"))}, name="p")
    repoS, shS = _scratch_memo(r10, {REG_PATH: _register("N-121", ("N-135", None))}, name="s")
    check("dec_latest_wins_superseded", lambda: dec(repoP, _status_drill(shP, horizon=True))["reason"] == "NEEDS_DECISIONS_IN_REGISTER"
          and dec(repoP, _status_drill(shP, horizon=True))["detail"]["not_decided"] == {"N-135": "superseded"})
    check("dec_latest_wins_decided", lambda: dec(repoM, _status_drill(shM, horizon=True))["state"] == "MEASURED"
          and dec(repoM, _status_drill(shM, horizon=True))["detail"]["latest_states"] == {"N-121": "decided", "N-135": "decided"})
    check("dec_never_decided", lambda: dec(repoL, _status_drill(shL, horizon=True))["reason"] == "NEEDS_DECISIONS_IN_REGISTER"
          and dec(repoL, _status_drill(shL, horizon=True))["detail"]["not_decided"] == {"N-135": "superseded"} and dec(repoL, _status_drill(shL, horizon=True))["detail"]["missing"] == [])
    check("dec_no_state_is_not_decided", lambda: dec(repoS, _status_drill(shS, horizon=True))["detail"]["not_decided"] == {"N-135": None}
          and "not decided (its latest record is None)" in dec(repoS, _status_drill(shS, horizon=True))["detail"]["text"])
    check("dec_register_latest", lambda: m.register_latest([("a", 1), ("b", 2), ("a", 3)]) == {"a": 3, "b": 2} and m.DECIDED_STATE == "decided")
    check("dec_no_drill", lambda: dec(repoA, None)["reason"] == "NEEDS_DRILL_DOCUMENT")
    forged = copy.deepcopy(dA)
    forged["result"] = "FAIL"
    check("dec_forged_drill", lambda: dec(repoA, forged)["reason"] == "NEEDS_VALID_DRILL" and dec(repoA, "x")["reason"] == "NEEDS_VALID_DRILL")
    check("dec_commit_not_in_repo", lambda: dec(repoA, _status_drill("2" * 40))["reason"] == "NEEDS_COMMIT_IN_REPO")
    check("git_read", lambda: m.git_read_at(repoA, shA, REG_PATH) == _register("N-121", "N-135").encode() and m.git_read_at(repoA, shA, "no/file") is None
          and raises(m.CommitNotInRepo, lambda: m.git_read_at(repoA, "3" * 40, REG_PATH)) and raises(m.MirrorError, lambda: m.git_read_at(repoA, "HEAD", REG_PATH))
          and raises(m.MirrorError, lambda: m.git_read_at(repoA, None, REG_PATH)))
    check("dec_cited", lambda: m.cited_decisions(dA) == {"N-121": ["the runtime block", "the closed not_run list", "partial-ownership units", "SEEDED units"]}
          and m.cited_decisions(dA, config_seed=True)["N-121"][-1] == "the production config seed" and sorted(m.cited_decisions(dC)) == ["N-121", "N-135"])
    check("dec_status_wired", lambda: {x["step"]: x["state"] for x in m.drill_status(RD, drill=dA, repo=repoA)["steps"]}["ss_decisions"] == "MEASURED"
          and {x["step"]: x.get("reason") for x in m.drill_status(RD)["steps"]}["ss_decisions"] == "NEEDS_DRILL_DOCUMENT")
    repoT, shT = _scratch_memo(r10, {m.MIGRATION_610_PATH: M610}, name="t")
    repoN, shN = _scratch_memo(r10, {"README": "x\n"}, name="tn")
    repoD, shD = _scratch_memo(r10, {m.MIGRATION_610_PATH: _migration(dup=True)}, name="td")
    ts = lambda sh_, chk, repo=None, **kw: m.text_seed_step(chk, repo or repoT, commit=kw.pop("commit", sh_), rehearsal=kw.pop("rehearsal", out_doc(RD, "rehearsal", commit=sh_)),
                                                            build_record=kw.pop("record", _rrec(orchestrator_commit=sh_)), decls=RD)  # noqa: E731
    check("ts_measured", lambda: ts(shT, _check(shT))["state"] == "MEASURED" and ts(shT, _check(shT))["detail"]["audited"] == AUD)
    check("ts_no_file", lambda: m.text_seed_step(None, repoT)["reason"] == "NEEDS_TEXT_SEED_CHECK" and m.text_seed_step(None, repoT)["state"] == "UNMEASURED"
          and "expects" in m.text_seed_step(None, repoT)["detail"] and "problems" not in m.text_seed_step(None, repoT)["detail"])
    check("ts_invalid_file", lambda: ts(shT, _check(shT, spec_sha256="0" * 64))["reason"] == "NEEDS_TEXT_SEED_CHECK" and ts(shT, {**_check(shT), "equal": True})["reason"] == "NEEDS_TEXT_SEED_CHECK")
    check("ts_commit_mismatch", lambda: ts(shT, _check("2" * 40))["reason"] == "NEEDS_TEXT_SEED_CHECK")
    check("ts_commit_not_in_repo", lambda: ts("2" * 40, _check("2" * 40))["reason"] == "NEEDS_COMMIT_IN_REPO")
    check("ts_migration_absent", lambda: ts(shN, _check(shN), repo=repoN)["reason"] == "NEEDS_MIGRATION_610_AT_COMMIT" and ts(shD, _check(shD), repo=repoD)["reason"] == "NEEDS_MIGRATION_610_AT_COMMIT")
    for field, val in (("identity_sha256", "e" * 64), ("content_sha256", "f" * 64), ("row_count", 10650)):
        check(f"ts_computed_differs:{field}", lambda field=field, val=val: ts(shT, _check(shT, computed={**AUD, field: val}))["state"] == "FAIL"
              and any("differ from the baseline row" in x for x in ts(shT, _check(shT, computed={**AUD, field: val}))["detail"]["problems"]))
        check(f"ts_baseline_not_audited:{field}", lambda field=field, val=val: ts(shT, _check(shT, aud={**AUD, field: val}))["state"] == "FAIL"
              and any("not the audited constants" in x for x in ts(shT, _check(shT, aud={**AUD, field: val}))["detail"]["problems"]))
    check("ts_orphans", lambda: ts(shT, _check(shT, orphan_chunks=2))["state"] == "FAIL" and any("2 orphan chunk(s)" in x for x in ts(shT, _check(shT, orphan_chunks=2))["detail"]["problems"]))
    check("ts_fail_not_unmeasured", lambda: ts(shT, _check(shT, orphan_chunks=1))["state"] == "FAIL" and "reason" not in ts(shT, _check(shT, orphan_chunks=1)))
    check("ts_no_rehearsal", lambda: ts(shT, _check(shT), rehearsal=None)["reason"] == "NEEDS_REHEARSAL_RECEIPT")
    check("ts_other_run", lambda: ts(shT, _check(shT, run_id="6e57e57e-5e57-4e57-8e57-5e57e57e57e5"))["reason"] == "NEEDS_TEXT_SEED_CHECK_OF_THIS_RUN")
    failed_rec = _rrec(orchestrator_commit=shT)
    failed_rec["assets"] = [x if x["asset_id"] != "bg_texts" else {"asset_id": "bg_texts", "state": "failed"} for x in failed_rec["assets"]]
    check("ts_bg_texts_not_complete", lambda: ts(shT, _check(shT), record=failed_rec)["reason"] == "NEEDS_BUILD_RECORD_BG_TEXTS"
          and ts(shT, _check(shT), record=None)["reason"] == "NEEDS_BUILD_RECORD_BG_TEXTS" and ts(shT, _check(shT), record=_rrec(orchestrator_commit=shT, drop=("bg_texts",)))["reason"] == "NEEDS_BUILD_RECORD_BG_TEXTS"
          and ts(shT, _check(shT), record=_rrec(orchestrator_commit=shT, run_id="6e57e57e-5e57-4e57-8e57-5e57e57e57e5"))["reason"] == "NEEDS_BUILD_RECORD_BG_TEXTS")
    check("ts_spec", lambda: [x["name"] for x in m.text_seed_spec()["selects"]] == ["baseline", "computed", "orphans"] and len(m.text_seed_spec()["spec_sha256"]) == 64)
    for lbl, edit in (("extra", lambda d: d.update(equal=True)), ("missing", lambda d: d.pop("orphan_chunks")), ("schema", lambda d: d.update(schema="x/v1")), ("spec", lambda d: d.update(spec_sha256="0" * 64)),
                      ("commit", lambda d: d.update(commit="abc")), ("run_id", lambda d: d.update(run_id="00000000-0000-0000-0000-000000000000")),
                      ("revision", lambda d: d["baseline"].update(contract_revision="bg-texts-integrity-v2")), ("bkeys", lambda d: d["baseline"].update(x=1)), ("ckeys", lambda d: d["computed"].update(x=1)),
                      ("bhash", lambda d: d["baseline"].update(identity_sha256="short")), ("chash", lambda d: d["computed"].update(content_sha256="Z" * 64)), ("bhash2", lambda d: d["baseline"].update(content_sha256="x")),
                      ("brows", lambda d: d["baseline"].update(row_count=True)), ("crows", lambda d: d["computed"].update(row_count=-1)), ("orph", lambda d: d.update(orphan_chunks=-1)),
                      ("orphb", lambda d: d.update(orphan_chunks=False)), ("chash2", lambda d: d["computed"].update(identity_sha256=5))):
        def _bad(edit=edit):
            d = _check(shT)
            edit(d)
            return m.validate_text_seed_check(d) != []
        check(f"ts_validator:{lbl}", _bad)
    check("ts_validator_good", lambda: m.validate_text_seed_check(_check(shT)) == [] and m.validate_text_seed_check(None) != [])
    check("ts_migration_constants", lambda: m.migration_610_constants(M610) == AUD and m.migration_610_constants(_migration(dup=True).encode()) is None and m.migration_610_constants(b"x") is None
          and m.migration_610_constants(_migration().replace("row_count = 10651", "row_count > 5").encode()) is None and m.migration_610_constants(b"\xff") is None)
    check("ts_status_wired", lambda: {x["step"]: x["state"] for x in m.drill_status(RD, text_seed_check=_check(shT), rehearsal=out_doc(RD, "rehearsal", commit=shT), build_record=_rrec(orchestrator_commit=shT),
                                                                                 repo=repoT)["steps"]}["text_seed"] == "MEASURED")
    check("report_open_findings", lambda: m.build_drill(pdr, prr, RD, None, commit=SHA40)[1]["open_findings"] == list(m.OPEN_FINDINGS) and len(m.OPEN_FINDINGS) == 8)
    # round 5: not_run_declared
    nrp, nrr = out_doc(RD, "production"), out_doc(RD, "rehearsal", assets=[u for u in RD.expected_assets() if u not in NOT_RUN_UNITS])
    nrx = {u: {"reason_code": "not_run_declared", "detail": NR_DETAIL % u} for u in NOT_RUN_UNITS}
    nrd = lambda **kw: m.build_drill(nrp, nrr, RD, kw.pop("expl", nrx), commit=SHA40, **kw)  # noqa: E731
    check("nr_ok", lambda: nrd(build_record=_rrec())[0]["result"] == "PASS_DECLARED_ONLY" and nrd(build_record=_rrec())[0]["unmeasured"] == list(NOT_RUN_UNITS))
    check("nr_never_equal", lambda: not set(nrd(build_record=_rrec())[0]["equal"]) & set(NOT_RUN_UNITS) and len(nrd(build_record=_rrec())[0]["equal"]) == 28)
    check("nr_needs_record", lambda: nrd()[0]["result"] == "FAIL" and nrd()[0]["unmeasured"] == [])
    check("nr_complete_refused", lambda: nrd(build_record=_rrec({"bg_muhurta_lattice": {"asset_id": "bg_muhurta_lattice", "state": "complete"}}))[0]["result"] == "FAIL")
    check("nr_unlisted_refused", lambda: m.build_drill(out_doc(RD, "production"), out_doc(RD, "rehearsal", assets=[u for u in RD.expected_assets() if u != "bg_ephemeris"]), RD,
                                                       {"bg_ephemeris": nrx["bg_muhurta_lattice"]}, commit=SHA40, build_record=_rrec())[0]["result"] == "FAIL")
    check("nr_unverified_record_refused", lambda: raises(m.MirrorError, lambda: nrd(build_record=_rrec({"bg_ghatana": {"asset_id": "bg_ghatana", "state": "failed"}}))))
    check("nr_report_status", lambda: nrd(build_record=_rrec())[1]["unit_status"]["bg_muhurta_lattice"]["status"] == "UNMEASURED:not_run_declared"
          and nrd(build_record=_rrec())[1]["unmeasured"] == list(NOT_RUN_UNITS)
          and nrd(build_record=_rrec())[1]["not_run"] == nrd(build_record=_rrec())[0]["not_run"] != {})
    check("nr_headline", lambda: "3 not-run units, UNMEASURED" in nrd(build_record=_rrec())[1]["headline"] and "bg_muhurta_lattice [NEEDS_AS_OF_PIN]" in nrd(build_record=_rrec())[1]["headline"])
    sp = m.seed_spec(RD)
    check("seed_round7_tables", lambda: [t["table"] for t in sp["tables"]][5:] == ["brahma_ontology", "nirmana_bg_texts_integrity_baselines"]
          and sp["tables"][5]["select"].count("'") == 6 and all(f"'{c}'" in sp["tables"][5]["select"] for c in ("dasha_system", "dosha", "yoga"))
          and " WHERE " not in sp["tables"][6]["select"] and "REPLACED by the rebuild" in sp["tables"][5]["why"] and "COUNT(*) >= 737" in sp["tables"][5]["why"]
          and "audited constants of migration 610" in sp["tables"][6]["why"])
    check("seed_not_seeded_statement", lambda: "NOT seeded: the Rahu/Ketu rows of ephemeris_daily. The orchestrated bg_ephemeris writer writes node_mode/epoch_convention" in " ".join(sp["notes"])
          and "DEPENDENT" not in " ".join(sp["notes"]))
    check("seed_evidence_seven_tables", lambda: m.validate_seed_evidence(_seed_evidence(), RD) == []
          and all(m.validate_seed_evidence({**_seed_evidence(), "tables": {k: v for k, v in _seed_evidence()["tables"].items() if k != d}}, RD) for d in ("brahma_ontology", "nirmana_bg_texts_integrity_baselines")))
    check("resolved_findings_text", lambda: len(m.RESOLVED_FINDINGS) == 1 and m.RESOLVED_FINDINGS[0].startswith("9. (resolved) bg_ephemeris writer did not write node_mode/epoch_convention; fixed by #3015, on main 2026-10-05")
          and m.build_drill(out_doc(RD, "production"), out_doc(RD, "rehearsal"), RD, None, commit=SHA40)[1]["resolved_findings"] == list(m.RESOLVED_FINDINGS)
          and not hasattr(m, "DEPENDENCIES"))
    check("seed_collate_c_on_every_text_key", lambda: seed_order_problems(m.seed_tables()) == [])
    check("seed_spec_tables", lambda: [t["table"] for t in sp["tables"]] == ["asset_registry", "asset_output_digest_specs", "brahma_formula_constants", "brahma_event_ontology", "bg_transit_rules", "brahma_ontology", "nirmana_bg_texts_integrity_baselines"])
    check("seed_writer_ids", lambda: len(m.writer_owned_ids("brahma_formula_constants")) == 10 and len(m.writer_owned_ids("brahma_event_ontology")) == 27)
    check("seed_select_double_transit", lambda: "'double_transit'" in sp["tables"][4]["select"] and "layer = 'brahmagyan'" in sp["tables"][0]["select"])
    se = _seed_evidence()
    se["spec_sha256"] = sp["spec_sha256"]
    for t_ in sp["tables"]:
        se["tables"][t_["table"]]["select_sha256"] = m.sha256_text(t_["select"])
    check("seed_evidence_ok", lambda: m.validate_seed_evidence(se, RD) == [])
    for label, mut in (("spec_sha", lambda e: e.update(spec_sha256=H)), ("select_sha", lambda e: e["tables"]["asset_registry"].update(select_sha256=H)),
                       ("zero_hash", lambda e: e["tables"]["bg_transit_rules"].update(rows=0)), ("empty_hash_rows", lambda e: e["tables"]["bg_transit_rules"].update(sha256=m.EMPTY_SHA256)),
                       ("ids_lack", lambda e: e["asset_registry_ids"].remove("bg_ephemeris")), ("registry_rows", lambda e: e["tables"]["asset_registry"].update(rows=41)),
                       ("reader", lambda e: e["reader"].update(read_only=False)), ("missing_table", lambda e: e["tables"].pop("bg_transit_rules")),
                       ("few_rows", lambda e: (e["asset_registry_ids"].pop(), e["tables"]["asset_registry"].update(rows=39))), ("ids_order", lambda e: e["asset_registry_ids"].reverse()),
                       ("bad_rows", lambda e: e["tables"]["asset_registry"].update(rows=-1))):
        e2 = copy.deepcopy(se)
        mut(e2)
        check(f"seed_evidence_refuses_{label}", lambda e2=e2: m.validate_seed_evidence(e2, RD) != [])
    swapped = copy.deepcopy(se)
    swapped["asset_registry_ids"] = sorted([i for i in swapped["asset_registry_ids"] if i != "bg_ephemeris"] + ["zz_unknown_asset"])
    check("seed_evidence_refuses_bogus_id_for_l0_asset", lambda: m.validate_seed_evidence(swapped, RD) != [])
    badse = copy.deepcopy(se)
    badse["tables"]["asset_registry"]["rows"] = 1
    check("seed_status_bad_evidence_unmeasured", lambda: {x["step"]: x["state"] for x in m.drill_status(RD, seed_evidence=badse)["steps"]}["config_seed"] == "UNMEASURED")
    check("seed_status_step", lambda: {x["step"]: x["state"] for x in m.drill_status(RD, seed_evidence=se)["steps"]}["config_seed"] == "SHAPE_CHECKED"
          and {x["step"]: x["state"] for x in m.drill_status(RD)["steps"]}["config_seed"] == "UNMEASURED")
    # the rehearsal policy pins (stubs: nothing real is started or touched; each pin is isolated: every OTHER pin is satisfied)
    def mkroot(name, *, marker=True, data=True):
        r = tmp / name
        r.mkdir(mode=0o700)
        os.chmod(r, 0o700)
        r = pathlib.Path(os.path.realpath(str(r)))
        if marker:
            m.sr._write_marker(m.sr._Layout(r), 55432)
        if data:
            m.sr._Layout(r).data.mkdir()
            (m.sr._Layout(r).data / "PG_VERSION").write_text("15\n")
        return r
    saved = (m.sr.DEFAULT_ROOT, m.sr.init_cluster, m.sr.start_cluster, m.run_psql)
    started_calls = []
    nonempty = {"v": False}
    m.sr.init_cluster = lambda *a, **k: started_calls.append("init") or {}
    m.sr.start_cluster = lambda *a, **k: started_calls.append("start") or {"state": "running", "result": "started"}
    m.run_psql = lambda t, *, sql=None, file=None, on_error_stop, db=None, timeout=900: types.SimpleNamespace(
        returncode=0, stdout=(("3" if nonempty["v"] else "0") if "count(*)" in (sql or "") else ("1" if "pg_database" in (sql or "") else "")), stderr="")
    try:
        good_root = mkroot("inv_reh_good")
        m.sr.DEFAULT_ROOT = str(good_root)
        rkw = dict(db="rehearsal_m", port=55432, policy="rehearsal")
        check("reh_ok", lambda: m.harness_target(good_root, **rkw).policy == "rehearsal")
        check("reh_port_pin", lambda: raises(m.MirrorError, lambda: m.harness_target(good_root, db="rehearsal_m", port=5999, policy="rehearsal")))
        check("reh_owner_pin", lambda: raises(m.MirrorError, lambda: m.harness_target(good_root, owner="nobody_else", **rkw)))
        other = mkroot("inv_reh_other")
        check("reh_root_pin", lambda: raises(m.MirrorError, lambda: m.harness_target(other, **rkw)))
        nomarker = mkroot("inv_reh_nomarker", marker=False)
        m.sr.DEFAULT_ROOT = str(nomarker)
        check("reh_needs_marker", lambda: raises(m.MirrorError, lambda: m.harness_target(nomarker, **rkw)))
        m.sr.DEFAULT_ROOT = str(good_root)
        nonempty["v"] = True
        check("reh_existing_db_must_be_empty", lambda: raises(m.MirrorError, lambda: m.harness_target(good_root, **rkw)))
        check("reh_allow_existing", lambda: m.harness_target(good_root, allow_existing_db=True, **rkw).policy == "rehearsal")
        check("reh_never_initialises", lambda: "init" not in started_calls)
        check("disposable_existing_db_must_be_empty", lambda: raises(m.MirrorError, lambda: m.harness_target(tmp / "inv_d2", db="suvarna_disposable_m", port=40123)))
        nonempty["v"] = False
        check("disposable_not_rehearsal_port", lambda: raises(m.MirrorError, lambda: m.harness_target(tmp / "inv_d", db="suvarna_disposable_m", port=55432)))
    finally:
        m.sr.DEFAULT_ROOT, m.sr.init_cluster, m.sr.start_cluster, m.run_psql = saved
    return bad


def test_invariants_hold_on_the_unmutated_module(tmp_path):
    assert invariants(smd, tmp_path) == []


MUTANTS = [
    ('            if allowed is None:', '            if False:'),
    ('            elif x.get("reason") != allowed["reason"]:', '            elif False:'),
    ('        elif x["state"] in RECORD_STATES:\n            p.append(f"declared asset {aid} is {x[\'state\']}: a failed / errored / incomplete asset is never accepted as complete or as not_run")', '        elif False:\n            pass'),
    ('        if x is None:\n            p.append(f"declared asset {aid} is missing from the build record")', '        if x is None:\n            pass'),
    ('        if aid in by_id:\n            p.append(f"asset {aid} appears twice")', '        if False:\n            p.append(f"asset {aid} appears twice")'),
    ('        if not isinstance(aid, str) or aid not in known:', '        if False:'),
    ('        if st not in RECORD_STATES:', '        if False:'),
    ('        if "reason" in x and st != "not_run":', '        if False:'),
    ('"%d partial-ownership units (partial: writer-only rows compared; the whole table is fingerprinted, a difference is the expected migration_owned_rows)%s"', '"%d partial-ownership units%s"'),
    ('            % (len(po), (": " + po_txt) if po else ""),', '            % (len(po), ""),'),
    ('ORDER BY r.asset_id COLLATE \\"C\\"\"}', 'ORDER BY r.asset_id\"}'),
    ('ORDER BY s.asset_id COLLATE \\"C\\", s.spec_sha256', 'ORDER BY s.asset_id, s.spec_sha256'),
    ('s.spec_sha256 COLLATE \\"C\\"\"}', 's.spec_sha256\"}'),
    ('ORDER BY c.constant_id COLLATE \\"C\\"\"}', 'ORDER BY c.constant_id\"}'),
    ('ORDER BY e.event_class_id COLLATE \\"C\\"\"}', 'ORDER BY e.event_class_id\"}'),
    ('ORDER BY t.graha COLLATE \\"C\\", t.rule_type', 'ORDER BY t.graha, t.rule_type'),
    ('t.rule_type COLLATE \\"C\\", t.primary_house, t.id', 't.rule_type, t.primary_house, t.id'),
    ('c.entity_class IN (\'dasha_system\', \'dosha\', \'yoga\') "', 'c.entity_class IN (\'dasha_system\', \'dosha\') "'),
    ('c.entity_class IN (\'dasha_system\', \'dosha\', \'yoga\') "', 'c.entity_class IN (\'dasha_system\', \'dosha\', \'yoga\', \'planet\') "'),
    ('"ORDER BY c.entity_class COLLATE \\"C\\", c.canonical_id COLLATE \\"C\\""}', '"ORDER BY c.entity_class, c.canonical_id COLLATE \\"C\\""}'),
    ('"ORDER BY c.entity_class COLLATE \\"C\\", c.canonical_id COLLATE \\"C\\""}', '"ORDER BY c.entity_class COLLATE \\"C\\", c.canonical_id"}'),
    ('ORDER BY b.contract_revision COLLATE \\"C\\""}', 'ORDER BY b.contract_revision"}'),
    ('FROM nirmana_bg_texts_integrity_baselines b ORDER BY', 'FROM nirmana_bg_texts_integrity_baselines b WHERE b.contract_revision = \'x\' ORDER BY'),
    ('"why": "a schema-only mirror has no baseline row', '"why": "x", "why2": "a schema-only mirror has no baseline row'),
    ('"NOT seeded: the Rahu/Ketu rows of ephemeris_daily. The orchestrated bg_ephemeris writer writes node_mode/epoch_convention (PR #3015, on main 2026-10-05), "', '"x: the orchestrated bg_ephemeris writer writes node_mode/epoch_convention (PR #3015, on main 2026-10-05), "'),
    ('    cov["resolved_findings"] = list(RESOLVED_FINDINGS)', '    cov["resolved_findings"] = []'),
    ('    p += _horizon_problems(doc["horizons"], tabs, decls, side)', '    pass'),
    ('    if set(hz) != present:', '    if False:'),
    ('        if not (isinstance(hu, Mapping) and set(hu) == {t}):', '        if not isinstance(hu, Mapping) or t not in hu:'),
    ('        why = sr.horizon_block_problem(b)\n        if why:', '        why = None\n        if why:'),
    ('        if b["date_column"] != col:', '        if False:'),
    ('            if b["rows"] != full["rows"]:\n                p.append(f"{u}.{t}: the horizon block has', '            if False:\n                p.append(f"{u}.{t}: the horizon block has'),
    ('            elif b["overlap_rows"] == b["rows"] and isinstance(full.get("sha256"), str) and b["overlap_sha256"] != full["sha256"]:', '            elif False:'),
    ('        if b["overlap_rows"] == 0 and b["overlap_sha256"] != fd.empty_table_fingerprint(decls, u, t):', '        if False:'),
    ('        if side == "production" and not (b["overlap_cutoff"] == b["max_date"] and b["overlap_rows"] == b["rows"]):', '        if False:'),
    ('            hzs[u] = {"table": ht["table"], "production": production["horizons"][u][ht["table"]] if u in production["horizons"] else None,\n                      "rehearsal": rehearsal["horizons"][u][ht["table"]] if u in rehearsal["horizons"] else None}', '            hzs[u] = {"table": ht["table"], "production": rehearsal["horizons"][u][ht["table"]] if u in rehearsal["horizons"] else None,\n                      "rehearsal": production["horizons"][u][ht["table"]] if u in production["horizons"] else None}'),
    ('projections=pjs, horizons=hzs, not_run=', 'projections=pjs, horizons=None, not_run='),
    ('    cov["horizon_evidence"] = [{"unit": d["asset"], **d["explained"]["evidence"]}', '    cov["horizon_evidence"] = [] and [{"unit": d["asset"], **d["explained"]["evidence"]}'),
    ('        unit_status[h["unit"]] = {**unit_status[h["unit"]], "horizon_evidence": h["summary"]}', '        pass'),
    ('    cov["horizons"] = copy.deepcopy(drill["horizons"])', '    cov["horizons"] = {}'),
    ('[f"{h[\'unit\']}: {h[\'summary\']}" for h in cov["horizon_evidence"]])', '[])'),
    ('    if horizon_notes is not None:', '    if False:'),
    ('    return {u: production["horizons"][u][t["table"]]["max_date"] for u, t in decls.horizon_tables().items() if u in production["horizons"]}', '    return {u: production["horizons"][u][t["table"]]["min_date"] for u, t in decls.horizon_tables().items() if u in production["horizons"]}'),
    ('    bad = validate_fingerprint_output(production, decls, side="production")\n    if bad:', '    bad = []\n    if bad:'),
    ('        r = fd.unit_fingerprints(conn, decls, units, cursor_prefix="e57", horizon_cutoffs=horizon_cutoffs)', '        r = fd.unit_fingerprints(conn, decls, units, cursor_prefix="e57")'),
    ('"projections": r["projections"], "horizons": r["horizons"]}', '"projections": r["projections"], "horizons": {}}'),
    ('"horizons": {"rule": "N-135: a rolling-horizon difference is expected ONLY when the shared date range is shown row-for-row equal",', '"horizons_x": {"rule": "N-135: a rolling-horizon difference is expected ONLY when the shared date range is shown row-for-row equal",'),
    ('                         "emit": "for every unit flagged rolling_horizon (the list below), in the SAME streaming pass over the table\'s rows (no second read), the output "', '                         "emit": "for every unit flagged rolling_horizon (the list below), the output "'),
    ('    if set(projs) != present:', '    if False:'),
    ('        if not (isinstance(pu, Mapping) and set(pu) == {t}):', '        if not isinstance(pu, Mapping) or t not in pu:'),
    ('        if not (isinstance(m, Mapping) and set(m) == {"sha256", "rows"} and isinstance(m["sha256"], str) and SHA256.fullmatch(m["sha256"])\n                and isinstance(m["rows"], int)', '        if not (isinstance(m, Mapping) and set(m) == {"sha256", "rows"} and isinstance(m["sha256"], str)\n                and isinstance(m["rows"], int)'),
    ('        if isinstance(full, Mapping) and isinstance(full.get("rows"), int) and m["rows"] != full["rows"]:', '        if False:'),
    ('        if (m["rows"] == 0) != (m["sha256"] == empty):', '        if False:'),
    ('    if not isinstance(projs, Mapping):\n        return ["projections must be an object', '    if False:\n        return ["projections must be an object'),
    ('            pjs[u] = {"table": t, "production": production["projections"][u][t]["sha256"] if u in production["projections"] else None,', '            pjs[u] = {"table": t, "production": rehearsal["projections"][u][t]["sha256"] if u in rehearsal["projections"] else None,'),
    ('            pjs[u] = {"table": t, "production": production["projections"][u][t]["sha256"] if u in production["projections"] else None,\n                      "rehearsal": rehearsal["projections"][u][t]["sha256"] if u in rehearsal["projections"] else None}', '            pjs[u] = {"table": t, "production": production["projections"][u][t]["sha256"] if u in production["projections"] else None,\n                      "rehearsal": production["projections"][u][t]["sha256"] if u in production["projections"] else None}'),
    ('runtime=rehearsal["rebuild"]["runtime"], projections=pjs, horizons=hzs, not_run=', 'runtime=rehearsal["rebuild"]["runtime"], projections=None, horizons=hzs, not_run='),
    ('    cov["known_differences"] = [dict(k) for k in drill["known_differences"]]', '    cov["known_differences"] = []'),
    ('    cov["projections"] = {u: dict(v) for u, v in drill["projections"].items()}', '    cov["projections"] = {}'),
    ('        if k["limited_to_columns"] is False:\n            return (f"NOT limited', '        if False:\n            return (f"NOT limited'),
    ('        tail = f" KNOWN DIFFERENCE (tracked: {e[\'reference\']}): expected, visible, never equal."', '        tail = ""'),
    ('"explained": kd[e["unit"]]["explained"], "hint": _hint(e)}', '"explained": True, "hint": _hint(e)}'),
    ('            "projections": [{"unit": u, "table": t,', '            "projections_x": [{"unit": u, "table": t,'),
    ('    "9. (resolved) bg_ephemeris writer did not write node_mode/epoch_convention; fixed by #3015, on main 2026-10-05; the drill must now show equality for "', '    "9. x. "'),
    ('CONTAINER_EXPECTED_NOT_RUN = ("bg_muhurta_lattice",)', 'CONTAINER_EXPECTED_NOT_RUN = ()'),
    ('CONTAINER_EXPECTED_NOT_RUN = ("bg_muhurta_lattice",)', 'CONTAINER_EXPECTED_NOT_RUN = ("bg_muhurta_lattice", "bg_cohort")'),
    # round 10: decision register and text seed
    ('    if not (isinstance(commit, str) and HEX40.fullmatch(commit)):\n        raise MirrorError("the commit under test must be 40-hex")', '    if False:\n        raise MirrorError("x")'),
    ('        if run("cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:', '        if False:'),
    ('        if run("cat-file", "-e", f"{commit}:{path}").returncode != 0:\n            return None', '        if False:\n            return None'),
    ('    if lines and lines[-1] == "":', '    if False:'),
    ('    if not lines:\n        return [], ["the register holds no record"]', '    if False:\n        return [], ["x"]'),
    ('        if not ln.strip():\n            probs.append', '        if False:\n            probs.append'),
    ('            rec = fd.strict_loads(ln)', '            rec = json.loads(ln)'),
    ('        if not (isinstance(rec, Mapping) and isinstance(rec.get("id"), str) and rec["id"].strip()):', '        if not isinstance(rec, Mapping):'),
    ('        if not (isinstance(rec, Mapping) and isinstance(rec.get("id"), str) and rec["id"].strip()):', '        if not (isinstance(rec, Mapping) and isinstance(rec.get("id"), str)):'),
    ('    for i, st in records:\n        latest[i] = st', '    for i, st in records:\n        latest.setdefault(i, st)'),
    ('    undecided = {i: latest[i] for i in sorted(cited) if i in latest and latest[i] != DECIDED_STATE}', '    undecided = {}'),
    ('    undecided = {i: latest[i] for i in sorted(cited) if i in latest and latest[i] != DECIDED_STATE}', '    undecided = {i: latest[i] for i in sorted(cited) if i in latest and latest[i] is None}'),
    ('    if missing or undecided:', '    if missing:'),
    ('DECIDED_STATE = "decided"', 'DECIDED_STATE = "Decided"'),
    ('        recs.append((rec["id"], rec.get("state")))', '        recs.append((rec["id"], "decided"))'),
    ('    add("N-121", "the runtime block")', '    pass'),
    ('    if cov["not_run_allowed"]:\n        add("N-121", "the closed not_run list")', '    if False:\n        add("N-121", "the closed not_run list")'),
    ('    if cov["partial_ownership"]:\n        add("N-121", "partial-ownership units")', '    if False:\n        add("N-121", "partial-ownership units")'),
    ('    if cov["seeded"]:\n        add("N-121", "SEEDED units")', '    if False:\n        add("N-121", "SEEDED units")'),
    ('    if config_seed:\n        add("N-121", "the production config seed")', '    if False:\n        add("N-121", "the production config seed")'),
    ('        if isinstance(e, Mapping) and e.get("decision"):\n            add(e["decision"], f"the explanation of {d[\'asset\']}', '        if False:\n            add("N-121", f"the explanation of {d[\'asset\']}'),
    ('    if drill is None:\n        return {"step": "ss_decisions"', '    if False:\n        return {"step": "ss_decisions"'),
    ('    if probs:\n        return {"step": "ss_decisions", "state": "UNMEASURED", "reason": "NEEDS_VALID_DRILL"', '    if False:\n        return {"step": "ss_decisions", "state": "UNMEASURED", "reason": "NEEDS_VALID_DRILL"'),
    ('    except CommitNotInRepo as exc:\n        return {"step": "ss_decisions"', '    except ZeroDivisionError as exc:\n        return {"step": "ss_decisions"'),
    ('    if raw is None:\n        return {"step": "ss_decisions"', '    if False:\n        return {"step": "ss_decisions"'),
    ('    if rprobs:\n        return {"step": "ss_decisions"', '    if False:\n        return {"step": "ss_decisions"'),
    ('    missing = sorted(i for i in cited if i not in latest)', '    missing = sorted(i for i in cited if not any(x.startswith(i) for x in latest))'),
    ('    missing = sorted(i for i in cited if i not in latest)', '    missing = sorted(i for i in cited if i.lower() not in {x.lower() for x in latest})'),
    ('    missing = sorted(i for i in cited if i not in latest)', '    missing = []'),
    ('"detail": {**base, "register_sha256": sha, "records": len(recs), "latest_states"', '"detail": {**base, "records": len(recs), "latest_states"'),
    ('    sha = hashlib.sha256(raw).hexdigest()\n    recs, rprobs = parse_decision_register(raw)', '    sha = ""\n    recs, rprobs = parse_decision_register(raw)'),
    ('DECISION_REGISTER_PATH = "00_ARCHITECTURE/control/suvarna/state/DECISIONS.jsonl"', 'DECISION_REGISTER_PATH = "00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md"'),
    ('DECISION_REGISTER_ABSENT_TEXT = "decision register not on main"', 'DECISION_REGISTER_ABSENT_TEXT = "register missing"'),
    ('    steps.append(decisions_step(decls, drill, repo, config_seed=seed_evidence is not None and not seed_p))', '    steps.append({"step": "ss_decisions", "state": "UNMEASURED", "reason": NEEDS["decisions"]})'),
    ('    "decisions": "NEEDS_DECISION_REGISTER_ON_MAIN",', '    "decisions": "NEEDS_SS_DECISIONS",'),
    ('    if check is None:\n        return {"step": "text_seed"', '    if False:\n        return {"step": "text_seed"'),
    ('    probs = validate_text_seed_check(check)\n    if probs:', '    probs = []\n    if probs:'),
    ('    if check["commit"] != at:', '    if False:'),
    ('    except CommitNotInRepo as exc:\n        return {"step": "text_seed"', '    except ZeroDivisionError as exc:\n        return {"step": "text_seed"'),
    ('    if audited is None:\n        return {"step": "text_seed"', '    if False:\n        return {"step": "text_seed"'),
    ('    if {k: check["baseline"][k] for k in _TS_COMPUTED_KEYS} != audited:', '    if False:'),
    ('    if check["computed"] != {k: check["baseline"][k] for k in _TS_COMPUTED_KEYS}:', '    if False:'),
    ('    if check["orphan_chunks"] != 0:', '    if False:'),
    ('    if why:\n        return {"step": "text_seed", "state": "FAIL"', '    if False:\n        return {"step": "text_seed", "state": "FAIL"'),
    ('"state": "FAIL", "detail": {**detail, "problems": why}}', '"state": "UNMEASURED", "reason": NEEDS["text_seed"], "detail": {**detail, "problems": why}}'),
    ('    if not (isinstance(rehearsal, Mapping) and isinstance(rehearsal.get("rebuild"), Mapping) and decls is not None):', '    if False:'),
    ('    if check["run_id"] != rehearsal["rebuild"].get("run_id"):', '    if False:'),
    ('    if vprobs or not (entry and entry.get("state") == "complete"):', '    if False:'),
    ('    vprobs = verify_rebuild_receipt(rehearsal["rebuild"], build_record, decls) if build_record is not None else ["no build record supplied"]', '    vprobs = []'),
    ('    if doc["spec_sha256"] != text_seed_spec()["spec_sha256"]:', '    if False:'),
    ('    if not (isinstance(doc["commit"], str) and HEX40.fullmatch(doc["commit"])):\n        p.append("commit must be 40-hex")\n    if not real_uuid(doc["run_id"]):', '    if False:\n        p.append("x")\n    if not real_uuid(doc["run_id"]):'),
    ('    if not real_uuid(doc["run_id"]):\n        p.append("run_id must be a real UUID")', '    if False:\n        p.append("x")'),
    ('        if key == "baseline" and b.get("contract_revision") != TEXT_BASELINE_REVISION:', '        if False:'),
    ('            if not (isinstance(b[h], str) and SHA256.fullmatch(b[h])):', '            if False:'),
    ('        if not (isinstance(b["row_count"], int) and not isinstance(b["row_count"], bool) and b["row_count"] >= 0):', '        if False:'),
    ('    if not (isinstance(doc["orphan_chunks"], int) and not isinstance(doc["orphan_chunks"], bool) and doc["orphan_chunks"] >= 0):', '    if False:'),
    ('    if not isinstance(doc, Mapping) or set(doc) != set(TEXT_SEED_KEYS):', '    if not isinstance(doc, Mapping):'),
    ('        if not (isinstance(b, Mapping) and set(b) == set(keys)):', '        if not isinstance(b, Mapping):'),
    ('    if len(ident) != 1 or len(cont) != 1 or len(cnt) != 1:', '    if len(ident) < 1 or len(cont) < 1 or len(cnt) < 1:'),
    ('    ident = re.findall(r"audited_identity_sha256 constant text :=\\s*\'([0-9a-f]{64})\'", text)', '    ident = re.findall(r"audited_identity_sha256 constant text :=\\s*\'([0-9a-f]{64})\'", text)[:1] or [""]'),
    ('    steps.append(text_seed_step(text_seed_check, repo, commit=ts_commit, rehearsal=rehearsal if (rehearsal is not None and not reh_p) else None, build_record=build_record, decls=decls))', '    steps.append({"step": "text_seed", "state": "UNMEASURED", "reason": NEEDS["text_seed"]})'),
    ('    "text_seed": "NEEDS_TEXT_SEED_CHECK",', '    "text_seed": "NEEDS_TEXT_SEED",'),

    ('                                        runtime=rehearsal["rebuild"]["runtime"], projections=pjs, horizons=hzs, not_run=', '                                        runtime={**rehearsal["rebuild"]["runtime"], "platform": "linux/amd64"}, projections=pjs, not_run='),
    ('    cov["claimed_unverified"] = list(drill["claimed_unverified"])', '    cov["claimed_unverified"] = []'),
    ('    cov["runtime"] = dict(drill["runtime"])', '    cov["runtime"] = {}'),
    ('        unit_status[u] = {"status": "CLAIMED_UNVERIFIED:platform_not_linux_amd64", "members": decls.members(u), "platform": drill["runtime"]["platform"]}', '        pass'),
    ('    if runtime is not None:\n        bits.append("rebuild runtime:', '    if False:\n        bits.append("rebuild runtime:'),
    ('        bits.append("%d platform-bound units CLAIMED_UNVERIFIED (rebuilt off %s: never equal, never counted)%s" % (\n            len(claimed), sr.RUNTIME_PLATFORM, (": " + ", ".join(claimed)) if claimed else ""))', '        bits.append("%d platform-bound units CLAIMED_UNVERIFIED%s" % (len(claimed), ""))'),
    ('            "container_run_expectation": container_expectation(decls), "receipt_expected": copy.deepcopy(RECEIPT_SPEC)}', '            "container_run_expectation": container_expectation(decls)}'),
    ('    complete = [a for a in declared if a not in not_run]', '    complete = list(declared)'),
    ('"expected_complete_count": f"{len(complete)} of {len(declared)}"', '"expected_complete_count": f"{len(declared)} of {len(declared)}"'),
    ('    return (f"in the linux/amd64 container run {ce[\'expected_complete_count\']} declared assets are expected complete (bg_sky_calendar and bg_cohort among them) and "', '    return (f"every declared asset is expected complete and "'),
    ('            steps.append({"step": "linux_amd64_runtime", "state": "CLAIMED_UNVERIFIED", "reason": NEEDS["linux"],', '            steps.append({"step": "linux_amd64_runtime", "state": "SHAPE_CHECKED", "reason": NEEDS["linux"],'),
    ('    else:\n        steps.append({"step": "linux_amd64_runtime", "state": "UNMEASURED", "reason": NEEDS["linux"], "detail": {"units": pb_units}})', '    else:\n        steps.append({"step": "linux_amd64_runtime", "state": "SHAPE_CHECKED", "reason": NEEDS["linux"], "detail": {"units": pb_units}})'),
    ('NOT_RUN_ALLOWED = fd.NOT_RUN_ALLOWED\n', 'NOT_RUN_ALLOWED = {**fd.NOT_RUN_ALLOWED, "bg_ephemeris": {"reason": "NEEDS_X", "decision": "x"}}\n'),
    ('            "declared_assets_that_may_be_not_run": {a: dict(v) for a, v in sorted(NOT_RUN_ALLOWED.items()) if a in declared},', '            "declared_assets_that_may_be_not_run": {},'),
    ('    cov["open_findings"] = list(OPEN_FINDINGS)', '    cov["open_findings"] = []'),
    ('                                        runtime=rehearsal["rebuild"]["runtime"], projections=pjs, horizons=hzs, not_run=record_not_run(build_record, decls) if build_record is not None else None)', '                                        runtime=rehearsal["rebuild"]["runtime"], projections=pjs, horizons=hzs, not_run=None)'),
    ('            problems += [f"build record: {x}" for x in verify_rebuild_receipt(rehearsal["rebuild"], build_record, decls)]', '            pass'),
    ('        unit_status[u] = {"status": "UNMEASURED:not_run_declared", "members": decls.members(u), "reason": drill["not_run"][u]}', '        pass'),
    ('    cov["unmeasured"] = list(drill["unmeasured"])', '    cov["unmeasured"] = []'),
    ('            % (len(unmeasured), (": " + ", ".join("%s [%s]" % (u, (not_run or {}).get(u, "?")) for u in unmeasured)) if unmeasured else ""),', '            % (len(unmeasured), ""),'),
    ('    cov["not_run"] = dict(drill["not_run"])', '    cov["not_run"] = {}'),
    ('            unit_status[u] = {**unit_status[u], "partial_ownership": f"partial: writer-only rows compared (whole table fingerprinted; tables {tabs})"}', '            pass'),
    ('    if doc["spec_sha256"] != spec["spec_sha256"]:', '    if False:'),
    ('        if m["select_sha256"] != sha256_text(want[name]["select"]):', '        if False:'),
    ('        if (m["rows"] == 0) != (m["sha256"] == EMPTY_SHA256):', '        if False:'),
    ('        missing = sorted(l0 - set(ids))\n        if missing:', '        missing = []\n        if missing:'),
    ('        if isinstance(ar, Mapping) and isinstance(ar.get("rows"), int) and ar["rows"] != len(ids):', '        if False:'),
    ('    if doc["reader"] != {"role": "suvarna_reader", "read_only": True}:', '    if False:'),
    ('    if not (isinstance(tabs, Mapping) and set(tabs) == set(want)):', '    if not isinstance(tabs, Mapping):'),
    ('"select": "SELECT row_to_json(t)::text FROM bg_transit_rules t WHERE t.rule_type = \'double_transit\' ORDER BY t.graha COLLATE \\"C\\", t.rule_type COLLATE \\"C\\", t.primary_house, t.id"}', '"select": "SELECT row_to_json(t)::text FROM bg_transit_rules t ORDER BY t.graha COLLATE \\"C\\", t.rule_type COLLATE \\"C\\", t.primary_house, t.id"}'),
    ('    if seed_evidence is not None and not seed_p:', '    if seed_evidence is not None:'),
    ('    cov["headline"] = coverage_headline(drill["result"]', '    cov["headline"] = (lambda *a: "")(drill["result"]'),
    ('    return "; ".join(bits) + "."', '    return bits[0] + "."'),
    ('    cov["limits"] = list(LIMITS_TEXT)', '    cov["limits"] = []'),
    ('    for u, st in drill["seeded"].items():\n        unit_status[u] = {"status": f"seeded:{st}", "members": decls.members(u)}', '    pass'),
    ('"steps": steps, "build_record_expected": build_record_spec(decls)}', '"steps": steps}'),
    ('    return (isinstance(rebuild, Mapping) and set(rebuild) == set(RECEIPT_KEYS) and real_uuid(rebuild["run_id"])', '    return (isinstance(rebuild, Mapping) and set(rebuild) == set(RECEIPT_KEYS)'),
    ('            and sr.runtime_problem(rebuild["runtime"]) is None)', '            and True)'),
    ('    return (isinstance(rebuild, Mapping) and set(rebuild) == set(RECEIPT_KEYS)', '    return (isinstance(rebuild, Mapping) and set(rebuild) == {"run_id", "orchestrator_commit"}'),
    ('    return str(u) == v and u.variant == uuid.RFC_4122 and u.version in range(1, 9)', '    return True'),
    ('    return str(u) == v and u.variant == uuid.RFC_4122 and u.version in range(1, 9)', '    return u.variant == uuid.RFC_4122 and u.version in range(1, 9)'),
    ('            if m["rows"] > 0 and m["sha256"] == empty:', '            if False:'),
    ('            elif m["rows"] == 0 and m["sha256"] != empty:', '            elif False:'),
    ('    for a in sorted(set(tabs) ^ set(fps)):', '    for a in []:'),
    ('    if record["state"] != "completed":', '    if False:'),
    ('    if record["orchestrator_commit"] != receipt["orchestrator_commit"]:', '    if False:'),
    ('    if missing:', '    if False:'),
    ('    if not real_uuid(record["run_id"]) or record["run_id"] != receipt["run_id"]:', '    if False:'),
    ('        if not rprob:', '        if True:'),
    ('        steps.append({"step": "production_fingerprints", "state": "SHAPE_CHECKED",', '        steps.append({"step": "production_fingerprints", "state": "MEASURED",'),
    ('        steps.append({"step": "as_of_pin", "state": "SHAPE_CHECKED",', '        steps.append({"step": "as_of_pin", "state": "MEASURED",'),
    ('        steps.append({"step": "mirror_baseline", "state": "SHAPE_CHECKED",', '        steps.append({"step": "mirror_baseline", "state": "MEASURED",'),
    ('    validate_db_name(target.db, target.policy)                  # before ANY file is copied, restore run or database touched', '    pass'),
    ('    validate_db_name(db, policy)\n    if policy not in ("disposable", "rehearsal"):', '    if policy not in ("disposable", "rehearsal"):'),
    ('        if port in sr.FORBIDDEN_PORTS or port == sr.DEFAULT_PORT:', '        if False:'),
    ('        if port != sr.DEFAULT_PORT:', '        if False:'),
    ('        if os.path.realpath(root) != os.path.realpath(sr.DEFAULT_ROOT) or str(lay.root) != os.path.realpath(sr.DEFAULT_ROOT):', '        if False:'),
    ('        if sr.read_marker(root) is None or not (lay.data / "PG_VERSION").is_file():', '        if False:'),
    ('        if data_owner != want_owner or lay.data.stat().st_uid != os.getuid():', '        if False:'),
    ('    elif not allow_existing_db:', '    elif False:'),
    ('    return fd.strict_loads(Path(path).read_text(encoding="utf-8"))', '    return json.loads(Path(path).read_text(encoding="utf-8"))'),
    ('    if not (isinstance(db, str) and DB_NAME_RES[policy].fullmatch(db)):', '    if False:'),
    ('    if dst_real == src_root or src_root in dst_real.parents or dst_real in src_root.parents:', '    if False:'),
    ('    if dst_root.exists() and (not dst_root.is_dir() or any(dst_root.iterdir())):', '    if False:'),
    ('            if p.is_symlink():\n                raise MirrorError(f"recipe file {rel}: {p} is a symlink")', '            if False:\n                raise MirrorError(f"recipe file {rel}: {p} is a symlink")'),
    ('        if not os.path.lexists(src):\n            if optional:\n                continue\n            raise MirrorError', '        if not os.path.lexists(src):\n            continue\n            raise MirrorError'),
    ('        if sr.sha256_file(dst) != want:', '        if False:'),
    ('        if not src.is_file():', '        if False:'),
    ('        if size > MAX_RECIPE_BYTES:', '        if False:'),
    ('    bad = [i for i, ln in enumerate(text.split("\\n"), 1) if ln.startswith("COPY ") or ln.startswith("INSERT INTO ") or ln.startswith("\\\\.")]', '    bad = [i for i, ln in enumerate(text.split("\\n"), 1) if ln.startswith("COPY ")]'),
    ('    if len(idx) != 1:', '    if len(idx) == 0:'),
    ('        out, n = re.subn(r"\\bpublic\\.vector\\(\\d+\\)", "text", out)', '        out, n = out, 0'),
    ('        if "already exists" in msg:\n            cls = "already_exists"', '        if "already exists" in msg:\n            cls = "other"'),
    ('    if any(steps.get(n) == "FAILED" for n in STEP_ORDER):\n        return "FAIL"', '    if False:\n        return "FAIL"'),
    ('    if steps.get("verify") == "UNMEASURED":\n        return "UNMEASURED"', '    if False:\n        return "UNMEASURED"'),
    ('all(steps[n] in ("OK", "TOLERATED_ERRORS") for n in STEP_ORDER if n != "seed_fixes")', 'all(steps[n] in ("OK", "TOLERATED_ERRORS", "SKIPPED", "FAILED") for n in STEP_ORDER if n != "seed_fixes")'),
    ('    verified = bool(doc["verification"].get("ok")) and steps.get("verify") == "OK"', '    verified = True'),
    ('        if v["ok"] is not (not v["problems"] and v["tables_checked"] > 0):', '        if False:'),
    ('        if doc["result"] != derive_baseline_result(doc):', '        if False:'),
    ('        if tuple(s["name"] for s in st) != STEP_ORDER:', '        if False:'),
    ('        elif any(s["status"] == "SKIPPED" and s["name"] not in ("seed_fixes",) for s in st):', '        elif False:'),
    ('        if doc["tool_sha256"] != tool_sha256():', '        if False:'),
    ('                and c["port"] not in sr.FORBIDDEN_PORTS):', '                and True):'),
    ('    if doc["definition"] != fd.FINGERPRINT_DEFINITION:', '    if False:'),
    ('    if doc["declarations_sha256"] != decls.sha256:', '    if False:'),
    ('        if a not in units:', '        if False:'),
    ('        if not (isinstance(t, Mapping) and set(t) == set(decls.tables(a))):', '        if not isinstance(t, Mapping):'),
    ('        if ok and fps.get(a) != fd.composite_fingerprint({n: m["sha256"] for n, m in t.items()}):', '        if False:'),
    ('    if doc["side"] != side:', '    if False:'),
    ('    if doc["stage"] not in allowed:', '    if False:'),
    ('        if (doc["stage"] == "after_rebuild") != (doc["rebuild"] is not None):', '        if False:'),
    ('    elif doc["rebuild"] is not None:\n        p.append("a production file has no rebuild receipt")', '    elif False:\n        p.append("a production file has no rebuild receipt")'),
    ('        if rehearsal["stage"] != "after_rebuild":', '        if False:'),
    ('        if production["as_of"] != rehearsal["as_of"]:', '        if False:'),
    ('        if rehearsal["rebuild"] and rehearsal["rebuild"]["orchestrator_commit"] != commit:', '        if False:'),
    ('expected_assets=decls.expected_assets(), commit=commit, coverage=decls.drill_coverage(), rows=rows,', 'expected_assets=decls.expected_assets()[:-1], commit=commit, coverage=decls.drill_coverage(), rows=rows,'),
    ('    cov["note"] = "undeclared assets are NOT in expected_assets: they are reported here and in the drill\'s coverage block, not compared"', '    cov.pop("undeclared")'),
    ('    if baseline is not None and not bprob and baseline["result"] == "PASS":', '    if baseline is not None:'),
    ('    if rehearsal is not None and not reh_p and rehearsal["stage"] == "after_rebuild":\n        rprob', '    if rehearsal is not None:\n        rprob'),
    ('    if rehearsal is not None and not reh_p and rehearsal["stage"] == "after_rebuild":\n        rt = rehearsal', '    if rehearsal is not None:\n        rt = rehearsal'),
    ('        if rt["platform"] == sr.RUNTIME_PLATFORM:\n            steps.append({"step": "linux_amd64_runtime", "state": "SHAPE_CHECKED"', '        if True:\n            steps.append({"step": "linux_amd64_runtime", "state": "SHAPE_CHECKED"'),
    ('    if t.port in sr.FORBIDDEN_PORTS:', '    if False:'),
    ('    if (file is None) == (sql is None):', '    if False:'),
    ('    if (stage == "after_rebuild") != (rebuild is not None):', '    if False:'),
    ('    if not _iso_date(as_of) or not (isinstance(commit, str) and HEX40.fullmatch(commit)):', '    if False:'),
]


def _judge_mutant(args):
    """One source mutant in its own temporary directory -> (index, verdict). Module-level so a process pool can run it."""
    import tempfile
    i, old, new = args
    if SRC.count(old) != 1:
        return i, "TARGET_ABSENT_OR_NOT_UNIQUE"
    mutated = SRC.replace(old, new, 1)
    if mutated == SRC:
        return i, "NO_CHANGE"
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="smd_mut_"))
    try:
        try:
            mod = load_module(mutated, "smd_mut_" + str(abs(hash(old + new)) % 10**8))
        except Exception:                                         # noqa: BLE001 - a mutant that does not even load is trivially dead
            return i, "dead"
        # cheap battery first; the full one (with the git-heavy round-10 block) only for a mutant the cheap one did not kill: the verdict is the
        # same as running the full battery (a mutant is dead if ANY invariant fails), just reached with fewer git processes for most mutants
        (tmp / "cheap").mkdir()
        (tmp / "full").mkdir()
        dead = invariants(mod, tmp / "cheap", first_only=True, round10=False) or invariants(mod, tmp / "full", first_only=True, round10=True)
        return i, ("dead" if dead else "SURVIVED")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def _mutant_verdicts(items):
    """Every mutant judged, in parallel where `fork` exists (each judgement is independent and CPU-bound: 235 of them serially made this file the
    longest governance test and pushed its CI shard past the 10-minute ceiling), serially elsewhere. Results are returned in input order."""
    import multiprocessing
    import concurrent.futures
    jobs = [(i, o, n) for i, (o, n) in enumerate(items)]
    workers = max(1, min(8, os.cpu_count() or 1))
    if workers > 1 and "fork" in multiprocessing.get_all_start_methods():
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("fork")) as pool:
            return sorted(pool.map(_judge_mutant, jobs, chunksize=4))
    return sorted(_judge_mutant(j) for j in jobs)


def test_every_source_mutant_is_caught():
    verdicts = _mutant_verdicts(MUTANTS)
    assert len(verdicts) == len(MUTANTS) and len(MUTANTS) >= 200
    bad = [(i, v, MUTANTS[i][0][:90]) for i, v in verdicts if v != "dead"]
    assert not bad, f"{len(bad)} mutant(s) not caught: {bad[:5]}"
