"""C-09 - platform/scripts/readbacks/first_seal_input_readback.sql, the first-seal input-stability readback (runbook section 5.5, Codex R16-3).

Brought to main from origin/campaign/pravaha as ONE SELECT/WITH statement. Every test runs the file BYTES through the real executor script
(00_ARCHITECTURE/briefs/kalayantra/fleet/readback_sql.sh: SELECT/WITH-only, no backslash, one prepared statement, read-only session) against a local
disposable cluster, on fixture tables shaped like the real ones.

Claims (each one planted reversion in the job folder fails exactly the test named):
  F1 the file is accepted by the executor's own guard and returns rows (one statement, read-only, no psql variable);                  test_runs_through_the_real_executor
  F2 PART A has exactly the runbook's families (A1 L1 builds, A2 six registry md5s, A3 three corpus md5s), scoped to the canonical chart; test_part_a_has_the_runbook_families_scoped_to_the_canonical_chart
  F3 PART A is byte-identical across runs and CHANGES when any family's input changes (the R0/R1/R2 comparison can read false);     test_part_a_is_byte_identical_and_moves_when_an_input_moves
  F4 PART B reads true|true only when the stored digests equal the re-derived ones, and false (never an empty set) when a digest is wrong, NULL, or the
     snapshot is absent.                                                                                                              test_part_b_*
"""
from __future__ import annotations

import csv
import io
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SQL = REPO / "platform/scripts/readbacks/first_seal_input_readback.sql"
EXECUTOR = REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet/readback_sql.sh"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER_CHART = "1c826d5a-0000-4000-8000-000000000001"
GEN = "5.0"
BUILD = "11111111-1111-4111-8111-111111111111"
OTHER_BUILD = "99999999-9999-4999-8999-999999999999"

sys.path.insert(0, str(REPO / "platform/scripts/governance/__tests__"))
from _disposable_pg import point_psql_at  # noqa: E402,F401
from _gochara_readback_pg import disposable_pg  # noqa: E402,F401

REGISTRY = ["ka_gochara_predicate", "ka_gochara_factor", "ka_gochara_rule_path", "ka_gochara_rule_path_prerequisite",
            "ka_gochara_rule_path_soft_factor", "ka_gochara_rule_path_seal"]
CORPUS = ["classical_texts", "classical_chunks", "classical_attributions"]


@pytest.fixture(scope="session", autouse=True)
def _c_locale():
    old = os.environ.get("LC_ALL")
    os.environ["LC_ALL"] = "C"
    yield
    if old is None:
        os.environ.pop("LC_ALL", None)
    else:
        os.environ["LC_ALL"] = old


@pytest.fixture(scope="module")
def world(disposable_pg, tmp_path_factory):
    import psycopg
    env = disposable_pg.env()
    conn = psycopg.connect(host=env["PGHOST"], port=env["PGPORT"], dbname=env["PGDATABASE"], user=env["PGUSER"], autocommit=True)
    names = ["chart_facts", "chart_dashas", "ka_gochara_search_input_snapshot", *REGISTRY, *CORPUS]
    funcs = ["ka_gochara_search_l1_facts_digest(uuid,text[])", "ka_gochara_search_dasha_digest(uuid,uuid[])"]
    for n in names:                       # the suite-owned database is shared with other readback suites (as in provisioning_world)
        conn.execute(f"DROP TABLE IF EXISTS public.{n} CASCADE")
    for f in funcs:
        conn.execute(f"DROP FUNCTION IF EXISTS public.{f} CASCADE")
    conn.execute("CREATE TABLE public.chart_facts (chart_id uuid, ayanamsha_id text, build_id uuid, fact_id text)")
    conn.execute("CREATE TABLE public.chart_dashas (chart_id uuid, ayanamsha_id text, system_id text, build_id uuid, row_id uuid)")
    for n in [*REGISTRY, *CORPUS]:
        conn.execute(f"CREATE TABLE public.{n} (id int, body text)")
        conn.execute(f"INSERT INTO public.{n} VALUES (1,'a'),(2,'b')")
    conn.execute("CREATE TABLE public.ka_gochara_search_input_snapshot (chart_id uuid, generation text, l1_facts_digest text, dasha_digest text,"
                 " consumed_fact_ids text[], consumed_dasha_row_ids uuid[])")
    # stand-ins for the two derivation functions the verifier and the seal share (the real ones are 1206/1305 SQL): any deterministic digest will do
    conn.execute("CREATE FUNCTION public.ka_gochara_search_l1_facts_digest(p_chart uuid, p_ids text[]) RETURNS text LANGUAGE sql IMMUTABLE"
                 " AS $$ SELECT md5(p_chart::text || ':' || array_to_string(p_ids, ',')) $$")
    conn.execute("CREATE FUNCTION public.ka_gochara_search_dasha_digest(p_chart uuid, p_ids uuid[]) RETURNS text LANGUAGE sql IMMUTABLE"
                 " AS $$ SELECT md5(p_chart::text || ':' || array_to_string(p_ids, ',')) $$")
    reset(conn)
    root = tmp_path_factory.mktemp("ky_root")
    (root / "run/ops/sql").mkdir(parents=True)
    python = root / "venv/bin/python"
    python.parent.mkdir(parents=True)
    python.symlink_to(sys.executable)
    pgenv = root / "pgenv.sh"
    pgenv.write_text(f"export PGHOST={env['PGHOST']} PGPORT={env['PGPORT']} PGDATABASE={env['PGDATABASE']} PGUSER={env['PGUSER']}\n")
    try:
        yield {"conn": conn, "root": root, "pgenv": pgenv}
    finally:
        for n in names:
            conn.execute(f"DROP TABLE IF EXISTS public.{n} CASCADE")
        for f in funcs:
            conn.execute(f"DROP FUNCTION IF EXISTS public.{f} CASCADE")
        conn.close()


FACT_IDS = ["f1", "f2"]
DASHA_IDS = ["aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"]


def reset(conn):
    """The consistent baseline: a canonical-chart build, another chart's build (must stay out of PART A), and a snapshot whose digests are the re-derived ones."""
    conn.execute("TRUNCATE public.chart_facts, public.chart_dashas, public.ka_gochara_search_input_snapshot")
    conn.execute("INSERT INTO public.chart_facts VALUES (%s,'lahiri',%s,'f1'),(%s,'lahiri',%s,'f2'),(%s,'raman',%s,'f3'),(%s,'lahiri',%s,'x1')",
                 (CHART, BUILD, CHART, BUILD, CHART, BUILD, OTHER_CHART, OTHER_BUILD))
    conn.execute("INSERT INTO public.chart_dashas VALUES (%s,'lahiri','vimshottari',%s,%s),(%s,'lahiri','vimshottari',%s,%s),(%s,'lahiri','yogini',%s,%s)",
                 (CHART, BUILD, DASHA_IDS[0], CHART, BUILD, DASHA_IDS[1], CHART, BUILD, str(uuid.uuid4())))
    conn.execute("INSERT INTO public.ka_gochara_search_input_snapshot SELECT %s::uuid, %s,"
                 " public.ka_gochara_search_l1_facts_digest(%s::uuid, %s::text[]), public.ka_gochara_search_dasha_digest(%s::uuid, %s::uuid[]), %s::text[], %s::uuid[]",
                 (CHART, GEN, CHART, FACT_IDS, CHART, DASHA_IDS, FACT_IDS, DASHA_IDS))
    for n in REGISTRY + CORPUS:
        conn.execute(f"UPDATE public.{n} SET body = CASE id WHEN 1 THEN 'a' ELSE 'b' END")


def execute(world, tmp_name="first_seal.sql", text=None):
    """Run SQL bytes through the real executor readback_sql.sh; returns (CompletedProcess, rows as dicts)."""
    f = world["root"] / "run/ops/sql" / tmp_name
    f.write_text(SQL.read_text() if text is None else text)
    env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
    env.update(KY_ROOT=str(world["root"]), KY_READBACK_PGENV=str(world["pgenv"]))
    proc = subprocess.run(["bash", str(EXECUTOR), "--sql-file", str(f)], env=env, capture_output=True, text=True, timeout=60)
    rows = []
    if proc.returncode == 0:
        table = list(csv.reader(io.StringIO(proc.stdout), delimiter="\t"))
        rows = [dict(zip(table[0], r)) for r in table[1:]]
    return proc, rows


def part_b(rows):
    return [r for r in rows if r["kind"] == "B_snapshot_vs_rederived"]


def code_of(path: Path) -> str:
    return "\n".join(re.sub(r"--.*$", "", line) for line in path.read_text(encoding="utf-8").splitlines())


def test_file_is_one_read_only_select_under_the_readback_sql_rules():  # F1 (the same static rules test_gochara_readback_sql_files.py applies to its two files)
    raw = SQL.read_text(encoding="utf-8")
    assert "\\" not in raw and re.match(r"\s*(SELECT|WITH)\b", raw, re.I)
    code = code_of(SQL).strip()
    assert code.endswith(";") and ";" not in code[:-1]                     # exactly one statement
    assert not re.search(r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|call|do|set|lock)\b", code, re.I)
    assert re.search(r"\bORDER\s+BY\b[^()]*;$", code, re.I)               # a total ORDER BY closes the outer query (N.7.2)


def test_what_it_reads_exists_in_the_creating_migrations():  # F2/F4 (a column the file reads that no migration creates would fail only in production)
    mig = REPO / "platform/migrations"
    snapshot = (mig / "1206_gochara_search_inventory_completeness.sql").read_text(encoding="utf-8")
    body = re.search(r"CREATE TABLE public\.ka_gochara_search_input_snapshot \((.*?)\n\);", snapshot, re.S).group(1)
    cols = {m.group(1) for m in re.finditer(r"^\s{2}([a-z_0-9]+)\s+[A-Za-z]", body, re.M)}
    assert {"chart_id", "generation", "l1_facts_digest", "dasha_digest", "consumed_fact_ids", "consumed_dasha_row_ids"} <= cols
    assert "ka_gochara_search_l1_facts_digest(p_chart uuid, ids text[])" in snapshot and "ka_gochara_search_dasha_digest(p_chart uuid, ids uuid[])" in snapshot
    registry = (mig / "1154_gochara_rule_path_registry.sql").read_text(encoding="utf-8")
    for name in REGISTRY:
        assert re.search(r"CREATE TABLE( IF NOT EXISTS)? public\." + name + r"\b", registry), name
    # chart_facts, chart_dashas, classical_chunks and classical_attributions are created outside platform/migrations (bootstrap DDL); the original read their
    # live catalog on 2026-10-03, so the file only names them - it cannot be checked against a migration here.


def test_runs_through_the_real_executor(world):  # F1
    text = SQL.read_text()
    assert re.match(r"\s*WITH\b", text) and "\\" not in text and not re.search(r":'\w+'", text), "WITH-first, no backslash, no psql variable"
    proc, rows = execute(world)
    assert proc.returncode == 0, proc.stderr
    assert rows and list(rows[0]) == ["kind", "rel", "grain", "value", "n"]
    # the executor's own guard refuses the pravaha original's shape (a leading comment, a SET, psql variables, two statements): this file is not that
    proc, _ = execute(world, "pravaha_shape.sql", "-- comment first\nSET default_transaction_read_only = on;\nSELECT 1;\n")
    assert proc.returncode != 0 and "one SELECT/WITH statement required" in proc.stderr


def test_part_a_has_the_runbook_families_scoped_to_the_canonical_chart(world):  # F2 (runbook section 5.5; the pravaha original's three families)
    reset(world["conn"])
    _, rows = execute(world)
    a = [r for r in rows if r["kind"] != "B_snapshot_vs_rederived"]
    assert {(r["kind"], r["rel"]) for r in a} == (
        {("A1_l1_build", "chart_facts"), ("A1_l1_build", "chart_dashas")}
        | {("A2_registry_md5", n) for n in REGISTRY} | {("A3_corpus_md5", n) for n in CORPUS})
    facts = {(r["grain"], r["value"], r["n"]) for r in a if r["rel"] == "chart_facts"}
    assert facts == {("lahiri", BUILD, "2"), ("raman", BUILD, "1")}              # the other chart's build (OTHER_BUILD) is not read
    dashas = {(r["grain"], r["value"], r["n"]) for r in a if r["rel"] == "chart_dashas"}
    assert dashas == {("lahiri/vimshottari", BUILD, "2"), ("lahiri/yogini", BUILD, "1")}
    assert OTHER_BUILD not in "".join(r["value"] for r in rows)
    assert all(r["n"] == "2" for r in a if r["kind"] in ("A2_registry_md5", "A3_corpus_md5"))


@pytest.mark.parametrize("move", [
    "UPDATE public.chart_facts SET build_id = '%s' WHERE fact_id = 'f1'" % OTHER_BUILD,           # A1: an L1 rebuild between two runs
    "UPDATE public.ka_gochara_factor SET body = 'changed' WHERE id = 1",                          # A2: a registry row edited
    "UPDATE public.classical_chunks SET body = 'changed' WHERE id = 2",                           # A3: a corpus row edited
])
def test_part_a_is_byte_identical_and_moves_when_an_input_moves(world, move):  # F3
    conn = world["conn"]
    reset(conn)
    first, _ = execute(world)
    second, _ = execute(world)
    assert first.returncode == 0 and first.stdout == second.stdout, "R0 and R1 over an unchanged database must be byte-identical"
    conn.execute(move)
    try:
        moved, _ = execute(world)
        assert moved.returncode == 0 and moved.stdout != first.stdout, move
    finally:
        reset(conn)


def test_part_b_reads_true_true_when_the_stored_digests_equal_the_rederived_ones(world):  # F4
    reset(world["conn"])
    _, rows = execute(world)
    assert part_b(rows) == [{"kind": "B_snapshot_vs_rederived", "rel": GEN, "grain": "true", "value": "true", "n": "1"}]


@pytest.mark.parametrize("break_it, grain, value", [
    ("UPDATE public.ka_gochara_search_input_snapshot SET l1_facts_digest = 'tampered'", "false", "true"),
    ("UPDATE public.ka_gochara_search_input_snapshot SET dasha_digest = 'tampered'", "true", "false"),
    ("UPDATE public.ka_gochara_search_input_snapshot SET l1_facts_digest = NULL, dasha_digest = NULL", "false", "false"),
    ("UPDATE public.ka_gochara_search_input_snapshot SET consumed_fact_ids = ARRAY['f1']", "false", "true"),    # the consumed rows moved under a stored digest
])
def test_part_b_reads_false_when_a_digest_is_wrong_or_null(world, break_it, grain, value):  # F4
    conn = world["conn"]
    reset(conn)
    conn.execute(break_it)
    try:
        _, rows = execute(world)
        assert part_b(rows) == [{"kind": "B_snapshot_vs_rederived", "rel": GEN, "grain": grain, "value": value, "n": "1"}]
    finally:
        reset(conn)


def test_part_b_reads_false_not_an_empty_set_when_the_snapshot_is_absent(world):  # F4 (N.8: an empty PART B must not look like a pass)
    conn = world["conn"]
    reset(conn)
    conn.execute("DELETE FROM public.ka_gochara_search_input_snapshot")
    try:
        _, rows = execute(world)
        assert part_b(rows) == [{"kind": "B_snapshot_vs_rederived", "rel": GEN, "grain": "false", "value": "false", "n": "0"}]
    finally:
        reset(conn)
