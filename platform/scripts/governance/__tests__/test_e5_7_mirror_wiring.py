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


@pytest.fixture
def needs_psycopg():
    return pytest.importorskip("psycopg")


# ═════════════════════════ synthetic declarations, recipe and documents ═════════════════════════

def _table(name, key, key_ev, exclude=(), naive=()):
    return {"name": name, "scope": "global", "key": list(key), "key_evidence": key_ev, "naive_utc_columns": list(naive),
            "exclude": [{"column": c, "reason_code": rc, "reason": f"{c} is volatile by construction (synthetic)"} for c, rc in exclude],
            "write_evidence": ["x.py:1"]}


def _declared(tables, *, reproducibility=("deterministic",), notcov=(), groups=()):
    return {"status": "declared", "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "scope": "global",
            "coverage": "partial" if notcov else "full", "reproducibility": list(reproducibility), "groups": list(groups), "tables": tables,
            "not_covered_tables": [{"name": n, "reason": "r" * 70, "evidence": ["x.py:1"]} for n in notcov]}


def syn_doc(seeded_group=False):
    a = {f"a_{i}": _declared([_table(f"syn_t{i}", ["k"], f"primary_key:syn_t{i}_pk")]) for i in range(5)}
    a["a_multi"] = _declared([_table("syn_m1", ["k"], "primary_key:syn_m1_pk"), _table("syn_m2", ["k", "n"], "unique:syn_m2_u", [("id", "surrogate_identity")])])
    a["a_roll"] = _declared([_table("syn_roll", ["k"], "primary_key:syn_roll_pk", [("computed_at", "wall_clock_timestamp")])],
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


def out_doc(decls, side="production", *, assets=None, seed=0, stage=None, as_of="2026-10-03", commit=SHA40, rebuild="auto"):
    tabs = _tables_for(decls, assets, seed=seed)
    stage = stage or ("production_read" if side == "production" else "after_rebuild")
    if rebuild == "auto":
        rebuild = {"run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "orchestrator_commit": commit} if (side == "rehearsal" and stage == "after_rebuild") else None
    return {"schema": smd.OUTPUT_SCHEMA, "side": side, "stage": stage, "definition": fd.FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256,
            "commit": commit, "as_of": as_of, "rebuild": rebuild, "tables": tabs,
            "fingerprints": {a: fd.composite_fingerprint({n: m["sha256"] for n, m in t.items()}) for a, t in tabs.items()}}


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
            "decision": f"N-{100 + n}"}


def _pair(**kw):
    return out_doc(D5, "production", **kw), out_doc(D5, "rehearsal", **kw)


def _set_unit(doc, unit, sha, rows=None):
    """Give every table of `unit` the value `sha` (rows optional) and recompute the unit fingerprint."""
    for t, m in doc["tables"][unit].items():
        m["sha256"] = sha if len(doc["tables"][unit]) == 1 else hashlib.sha256(f"{sha}{t}".encode()).hexdigest()
        if rows is not None:
            m["rows"] = rows
    doc["fingerprints"][unit] = fd.composite_fingerprint({t: m["sha256"] for t, m in doc["tables"][unit].items()})


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
    drill2, _ = smd.build_drill(prod, reh, D5, {"a_roll": _ex()}, commit=SHA40)
    assert drill2["result"] == "PASS_DECLARED_ONLY" and drill2["differences"][0]["explained"]["decision"] == "N-101"
    no_dec = dict(_ex())
    del no_dec["decision"]
    assert smd.build_drill(prod, reh, D5, {"a_roll": no_dec}, commit=SHA40)[0]["result"] == "FAIL"


def test_rolling_horizon_and_platform_bound_codes_are_refused_for_a_deterministic_unit():
    prod, reh = _pair()
    _set_unit(reh, "a_0", H)
    for code in ("rolling_horizon",):
        r, _ = smd.build_drill(prod, reh, D5, {"a_0": _ex(code=code)}, commit=SHA40)
        assert r["result"] == "FAIL" and r["unexplained"] == ["a_0"] and any("flagged rolling_horizon" in x for x in r["problems"])
    miss = out_doc(D5, "rehearsal", assets=[u for u in D5.expected_assets() if u != "a_0"])
    r, _ = smd.build_drill(prod, miss, D5, {"a_0": _ex(code="source_unavailable_offline")}, commit=SHA40)
    assert r["result"] == "FAIL" and any("flagged platform_bound" in x for x in r["problems"])
    # the flagged unit may carry them
    _set_unit(reh, "a_roll", H)
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
    receipt = {"run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "orchestrator_commit": SHA40}
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
    assert reasons["text_seed"] == "NEEDS_TEXT_SEED" and reasons["ss_decisions"] == "NEEDS_SS_DECISIONS" and reasons["as_of_pin"] == "NEEDS_AS_OF_PIN"
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
    assert st["text_seed"] == st["linux_amd64_runtime"] == st["ss_decisions"] == "UNMEASURED"          # never inferable from files
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
    assert len(real["selects"]) == 63 and real["expected_differences"][0]["unit"] == "bg_ephemeris"
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
    base = ["compare-fingerprints", "--pre", str(p), "--post", str(p), "--expected", "declarations", "--rows", str(rows), "--commit", SHA40, "--out", str(out)]
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
    assert sr.main(["compare-fingerprints", "--pre", str(p), "--post", str(p2), "--expected", "declarations", "--rows", str(rows2), "--commit", SHA40]) == 4
    assert sr.main(["compare-fingerprints", "--pre", str(p), "--post", str(p), "--expected", str(tmp_path / "x.json"), "--rows", str(rows), "--commit", SHA40]) == 2   # no --coverage


def test_validate_drill_cli_rejects_a_drill_made_under_other_declarations(tmp_path, capsys):
    decls = fd.load_declarations()
    units = decls.expected_assets()
    fps = {a: hashlib.sha256(a.encode()).hexdigest() for a in units}
    drill = sr.compare_fingerprint_sets(sr.fingerprint_set(fps), sr.fingerprint_set(fps), expected_assets=units, commit=SHA40,
                                        coverage={**decls.drill_coverage(), "undeclared": {"bg_x": "no_table"}}, rows=_rows_file(units, decls))
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
    assert printed["expected_differences"][0]["unit"] == "bg_ephemeris" and printed["expected_differences"][0]["status"] == "not_observed"
    (tmp_path / "reh2.json").write_text(json.dumps({**reh, "as_of": "2026-01-01"}))
    assert smd.main(["compare", "--production", str(tmp_path / "prod.json"), "--rehearsal", str(tmp_path / "reh2.json"), "--commit", SHA40, "--out", str(out)]) == 2


def test_the_ephemeris_expected_difference_is_printed_and_never_hides_the_difference(tmp_path, capsys):
    decls = fd.load_declarations()
    prod, reh = out_doc(decls, "production"), out_doc(decls, "rehearsal")
    _set = lambda d, u: [d["tables"][u][t].update(sha256=hashlib.sha256(f"{u}{t}x".encode()).hexdigest()) for t in d["tables"][u]]  # noqa: E731
    _set(reh, "bg_ephemeris")
    reh["fingerprints"]["bg_ephemeris"] = reh["tables"]["bg_ephemeris"]["ephemeris_daily"]["sha256"]
    drill, cov = smd.build_drill(prod, reh, decls, None, commit=SHA40)
    assert drill["result"] == "FAIL" and drill["unexplained"] == ["bg_ephemeris"]                 # not an exclusion: the difference still needs an explanation
    st = cov["expected_differences_status"][0]
    assert st["status"] == "observed" and st["columns"] == ["node_mode", "epoch_convention"] and "#3015" in st["reference"] and "production_ahead_of_commit" in st["hint"]
    ok, _ = smd.build_drill(prod, reh, decls, {"bg_ephemeris": {"reason_code": "production_ahead_of_commit", "decision": "N-300",
                                                                "detail": "production carries node_mode and epoch_convention that the writer at this commit does not write (PR #3015 held)"}}, commit=SHA40)
    assert ok["result"] == "PASS_DECLARED_ONLY"


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
                                                     "0 SEEDED (shown, not counted toward the verdict); 2 comparison units, 2 in the rebuilt-equals-source claim.")


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
    assert "CLAIMED_UNVERIFIED" in exp["purpose"]
    assert any("build_record_expected" in x["detail"].get("expects", "") for x in s["steps"] if x["step"] == "rehearsal_l0_rebuild")
    # a record written exactly from the spec verifies (the spec and the verifier agree)
    ex = exp["shape_example"]
    assert set(ex) == set(exp["required_fields"]) and ex["schema"] == smd.BUILD_RECORD_SCHEMA
    rec = {**ex, "run_id": "5e57e57e-5e57-4e57-8e57-5e57e57e57e5", "orchestrator_commit": SHA40,
           "assets": [{"asset_id": a, "state": "complete"} for a in exp["declared_assets_that_must_be_complete"]]}
    assert smd.verify_rebuild_receipt({"run_id": rec["run_id"], "orchestrator_commit": SHA40}, rec, D5) == []
    assert smd.verify_rebuild_receipt({"run_id": rec["run_id"], "orchestrator_commit": SHA40}, {**rec, "extra": 1}, D5)
    # the claimed step says what to supply
    prod, reh = _pair()
    claimed = {x["step"]: x for x in smd.drill_status(D5, rehearsal=reh)["steps"]}["rehearsal_l0_rebuild"]
    assert claimed["state"] == "CLAIMED_UNVERIFIED" and "--build-record PATH" in claimed["detail"]["expects"]
    assert smd.main(["build-record-spec"]) == 0
    real = json.loads(capsys.readouterr().out)
    assert real["schema"] == "suvarna-build-record/v1" and len(real["declared_assets_that_must_be_complete"]) == 34 and "bg_ontology" in real["declared_assets_that_must_be_complete"]
    assert smd.main(["status"]) == 0 and json.loads(capsys.readouterr().out)["build_record_expected"]["schema"] == "suvarna-build-record/v1"


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


def invariants(m, tmp: pathlib.Path) -> list[str]:
    bad: list[str] = []

    def check(name, fn):
        try:
            ok = bool(fn())
        except Exception:                                         # noqa: BLE001 - a crash is a failed invariant
            ok = False
        if not ok:
            bad.append(name)

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
    diff["tables"]["a_roll"]["syn_roll"]["sha256"] = H
    diff["fingerprints"]["a_roll"] = H
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
    ('    cov["headline"] = coverage_headline(drill["result"], drill["coverage"], len(decls.assets), drill["seeded"])', '    cov["headline"] = ""'),
    ('    return "; ".join(bits) + "."', '    return bits[0] + "."'),
    ('    cov["limits"] = list(LIMITS_TEXT)', '    cov["limits"] = []'),
    ('    for u, st in drill["seeded"].items():\n        unit_status[u] = {"status": f"seeded:{st}", "members": decls.members(u)}', '    pass'),
    ('    return {**copy.deepcopy(BUILD_RECORD_SPEC), "declared_assets_that_must_be_complete": decls.declared_assets()}', '    return copy.deepcopy(BUILD_RECORD_SPEC)'),
    ('"steps": steps, "build_record_expected": build_record_spec(decls)}', '"steps": steps}'),
    ('    return (isinstance(rebuild, Mapping) and set(rebuild) == {"run_id", "orchestrator_commit"} and real_uuid(rebuild["run_id"])', '    return (isinstance(rebuild, Mapping) and set(rebuild) == {"run_id", "orchestrator_commit"}'),
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
    ('expected_assets=decls.expected_assets(), commit=commit, coverage=decls.drill_coverage(), rows=rows)', 'expected_assets=decls.expected_assets()[:-1], commit=commit, coverage=decls.drill_coverage(), rows=rows)'),
    ('    cov["note"] = "undeclared assets are NOT in expected_assets: they are reported here and in the drill\'s coverage block, not compared"', '    cov.pop("undeclared")'),
    ('    if baseline is not None and not bprob and baseline["result"] == "PASS":', '    if baseline is not None:'),
    ('    if rehearsal is not None and not reh_p and rehearsal["stage"] == "after_rebuild":', '    if rehearsal is not None:'),
    ('    if t.port in sr.FORBIDDEN_PORTS:', '    if False:'),
    ('    if (file is None) == (sql is None):', '    if False:'),
    ('    if (stage == "after_rebuild") != (rebuild is not None):', '    if False:'),
    ('    if not _iso_date(as_of) or not (isinstance(commit, str) and HEX40.fullmatch(commit)):', '    if False:'),
]


@pytest.mark.parametrize("old,new", MUTANTS, ids=[f"m{i:02d}" for i in range(len(MUTANTS))])
def test_every_source_mutant_is_caught(tmp_path, old, new):
    assert SRC.count(old) == 1, f"the mutant target is absent or not unique: {old!r}"
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    try:
        mod = load_module(mutated, "smd_mut_" + str(abs(hash(old + new)) % 10**8))
    except Exception:
        return                                                    # a mutant that does not even load is trivially dead
    failed = invariants(mod, tmp_path)
    assert failed, f"SURVIVING MUTANT: replacing {old!r} with {new!r} changed no invariant"
