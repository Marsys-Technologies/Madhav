"""Two read-only readback_sql files: sky_event_bodies.sql (J-3c-a52) and class_inventory_digest.sql (F-SHARED-GEOMETRY).

Claims, each with one oracle:
  1. Each file is ONE read-only SELECT/WITH the executor's readback_sql guard accepts
     (fleet/readback_sql.sh: first token SELECT/WITH, no backslash, one prepared statement).
  2. Every column the files read exists in the migration that creates the table (1153, 1155, 1206).
  3. sky_event_bodies: one row per (body, event_kind) with its count; a Moon row is counted, not assumed absent.
  4. class_inventory_digest: classes with the same record content (different event_class, different record_id)
     share record_content_digest and a group size; a different set does not; a class with no records is NULL, not a group.
  5. class_inventory_digest: only the chart's latest COMPLETED generation is read (an unfinished newer one and another
     chart's rows are ignored).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
READBACKS = REPO / "platform/scripts/readbacks"
SKY = READBACKS / "sky_event_bodies.sql"
DIGEST = READBACKS / "class_inventory_digest.sql"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER_CHART = "11111111-1111-4111-8111-111111111111"

sys.path.insert(0, str(REPO / "platform/scripts/governance/__tests__"))
from _gochara_readback_pg import disposable_pg  # noqa: F401,E402


@pytest.fixture(scope="module", autouse=True)
def _c_locale():
    old = os.environ.get("LC_ALL")
    os.environ["LC_ALL"] = "C"
    yield
    if old is None:
        os.environ.pop("LC_ALL", None)
    else:
        os.environ["LC_ALL"] = old


def code_of(path: Path) -> str:
    return "\n".join(re.sub(r"--.*$", "", line) for line in path.read_text(encoding="utf-8").splitlines())


# ── 1. the executor's own acceptance rules ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", [SKY, DIGEST], ids=lambda p: p.name)
def test_file_is_one_read_only_select_the_executor_accepts(path):
    raw = path.read_text(encoding="utf-8")
    assert "\\" not in raw                                           # readback_sql.sh refuses any backslash
    assert re.match(r"\s*(SELECT|WITH)\b", raw, re.I)               # and requires SELECT/WITH as the first token
    code = code_of(path)
    assert ";" not in code                                           # one statement
    assert not re.search(r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|call|do|set|lock)\b", code, re.I)
    assert re.search(r"\bORDER\s+BY\b[^()]*$", code.strip(), re.I)   # a total ORDER BY closes the outer query (N.7.2)


# ── 2. columns exist in the creating migrations ─────────────────────────────────────────────────────
def table_columns(migration: str, table: str) -> set[str]:
    text = (REPO / "platform/migrations" / migration).read_text(encoding="utf-8")
    m = re.search(r"CREATE TABLE (?:IF NOT EXISTS )?public\." + table + r"\s*\((.*?)\n\);", text, re.S)
    assert m, table
    cols = set()
    for line in m.group(1).splitlines():
        mm = re.match(r"\s{2}([a-z_]+)\s+[A-Za-z]", line)
        if mm and mm.group(1) not in ("constraint", "primary", "unique", "foreign", "check"):
            cols.add(mm.group(1))
    return cols


READS = {
    "ka_gochara_sky_event": ("1153_gochara_sky_event_substrate.sql", {"body", "event_kind", "created_at"}),
    "ka_gochara_relationship_record": ("1155_gochara_relationship_record.sql", {
        "record_id", "chart_id", "generation", "event_class", "affected_person", "frame_kind", "frame_arg", "agent",
        "relation", "object_id", "object_role", "path_id", "rule_version", "contact_id"}),
    "ka_gochara_search_inventory": ("1206_gochara_search_inventory_completeness.sql", {
        "chart_id", "generation", "event_class", "input_digest", "inventory_digest", "ledger_digest", "finalized_at"}),
    "ka_gochara_search_obligation": ("1206_gochara_search_inventory_completeness.sql", {
        "chart_id", "generation", "event_class", "path_id", "rule_version", "agent", "relation", "object_role",
        "target", "frame", "person"}),
    "ka_gochara_search_path_pin": ("1206_gochara_search_inventory_completeness.sql", {
        "chart_id", "generation", "event_class", "path_id", "rule_version", "disposition"}),
}


@pytest.mark.parametrize("table", sorted(READS))
def test_columns_read_exist_in_the_creating_migration(table):
    migration, wanted = READS[table]
    assert wanted <= table_columns(migration, table), wanted - table_columns(migration, table)
    sources = code_of(SKY) + code_of(DIGEST)
    assert re.search(r"\b" + table + r"\b", sources)                 # the table is really read by one of the files


# ── 3-5. behaviour against a disposable database with the real column names ──────────────────────────
DDL = """
CREATE TABLE ka_gochara_sky_event (event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), body text NOT NULL,
  event_kind text NOT NULL, created_at timestamptz NOT NULL);
CREATE TABLE ka_gochara_search_inventory (chart_id uuid NOT NULL, generation text NOT NULL, event_class text NOT NULL,
  input_digest text NOT NULL, inventory_digest text, ledger_digest text, finalized_at timestamptz,
  PRIMARY KEY (chart_id, generation, event_class));
CREATE TABLE ka_gochara_relationship_record (record_id uuid PRIMARY KEY, chart_id uuid NOT NULL, generation text NOT NULL,
  contact_id uuid, event_class text NOT NULL, affected_person text NOT NULL, frame_kind text NOT NULL, frame_arg text,
  agent text NOT NULL, relation text NOT NULL, object_id uuid NOT NULL, object_role text NOT NULL, path_id text NOT NULL,
  rule_version text NOT NULL);
CREATE TABLE ka_gochara_search_obligation (chart_id uuid NOT NULL, generation text NOT NULL, event_class text NOT NULL,
  ob_id uuid NOT NULL, path_id text NOT NULL, rule_version text NOT NULL, agent text NOT NULL, relation text NOT NULL,
  object_role text NOT NULL, target text NOT NULL, frame text NOT NULL, person text NOT NULL);
CREATE TABLE ka_gochara_search_path_pin (chart_id uuid NOT NULL, generation text NOT NULL, event_class text NOT NULL,
  path_id text NOT NULL, rule_version text NOT NULL, disposition text NOT NULL);
"""
TABLES = ("ka_gochara_sky_event", "ka_gochara_search_inventory", "ka_gochara_relationship_record",
          "ka_gochara_search_obligation", "ka_gochara_search_path_pin")


@pytest.fixture()
def conn(disposable_pg):
    import psycopg
    env = disposable_pg.env()
    c = psycopg.connect(host=env["PGHOST"], port=env["PGPORT"], dbname=env["PGDATABASE"], user=env["PGUSER"], autocommit=True)
    try:
        for t in TABLES:
            c.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
        c.execute(DDL)
        yield c
    finally:
        for t in TABLES:
            c.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
        c.close()


def run_readback(conn, path: Path) -> list[dict]:
    """The same one-statement, read-only, prepared protocol as fleet/readback_sql.sh."""
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        cur = conn.execute(path.read_text(encoding="utf-8"), prepare=True)
        names = [c.name for c in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]


def test_sky_event_bodies_counts_each_body_kind_and_counts_a_moon_row(conn):
    stamp = "2026-10-17T16:00:00Z"
    for body, kind, n in (("sun", "sign_ingress", 3), ("saturn", "station", 2), ("saturn", "sign_ingress", 1)):
        conn.execute("INSERT INTO ka_gochara_sky_event (body, event_kind, created_at) SELECT %s, %s, %s FROM generate_series(1, %s)",
                     (body, kind, stamp, n))
    rows = run_readback(conn, SKY)
    per = {(r["body"], r["event_kind"]): r["n"] for r in rows if r["section"] == 1}
    assert per == {("sun", "sign_ingress"): 3, ("saturn", "station"): 2, ("saturn", "sign_ingress"): 1}
    assert [r["n"] for r in rows if r["section"] == 2] == [0]                  # a Moon row is reported, as zero
    assert [r["n"] for r in rows if r["section"] == 3] == [6]
    conn.execute("INSERT INTO ka_gochara_sky_event (body, event_kind, created_at) VALUES ('Moon', 'sign_ingress', %s)", (stamp,))
    after = run_readback(conn, SKY)
    assert [r["n"] for r in after if r["section"] == 2] == [1]
    assert [(r["section"], r["body"], r["event_kind"]) for r in after] == sorted(
        (r["section"], r["body"], r["event_kind"]) for r in after)


def add_class(conn, chart, generation, event_class, finalized, records=(), obligations=(), pins=()):
    conn.execute("INSERT INTO ka_gochara_search_inventory VALUES (%s, %s, %s, 'i', %s, %s, %s)",
                 (chart, generation, event_class, "a" * 64 if finalized else None, "b" * 64 if finalized else None,
                  "2026-10-18T00:00:00Z" if finalized else None))
    for i, (path_id, relation) in enumerate(records):
        conn.execute("INSERT INTO ka_gochara_relationship_record VALUES (gen_random_uuid(), %s, %s, NULL, %s, 'native', 'natal', NULL,"
                     " 'saturn', %s, '00000000-0000-4000-8000-000000000001', 'target', %s, '1')",
                     (chart, generation, event_class, relation, path_id))
    for path_id in obligations:
        conn.execute("INSERT INTO ka_gochara_search_obligation VALUES (%s, %s, %s, gen_random_uuid(), %s, '1', 'saturn',"
                     " 'conjunction', 'target', 'moon', 'natal', 'native')", (chart, generation, event_class, path_id))
    for path_id in pins:
        conn.execute("INSERT INTO ka_gochara_search_path_pin VALUES (%s, %s, %s, %s, '1', 'included')", (chart, generation, event_class, path_id))


def test_class_inventory_digest_groups_classes_that_share_a_record_set(conn):
    shared = [("p1", "conjunction"), ("p2", "aspect")]
    add_class(conn, CHART, "5.0", "marriage", True, shared, ["p1"], ["p1"])
    add_class(conn, CHART, "5.0", "relocation", True, shared, ["p1"], ["p1"])        # same content, other class and record ids
    add_class(conn, CHART, "5.0", "surgery", True, shared + [("p3", "aspect")], ["p1"], ["p1"])
    add_class(conn, CHART, "5.0", "spiritual_turn", True)                              # no records at all
    rows = {r["event_class"]: r for r in run_readback(conn, DIGEST)}
    assert list(rows) == ["marriage", "relocation", "spiritual_turn", "surgery"]       # total order
    m, r, s, e = rows["marriage"], rows["relocation"], rows["surgery"], rows["spiritual_turn"]
    assert m["record_content_digest"] == r["record_content_digest"] != s["record_content_digest"]
    assert m["record_set_digest"] != r["record_set_digest"]                            # record_id hashes the class
    assert (m["record_group_size"], r["record_group_size"], s["record_group_size"]) == (2, 2, 1)
    assert m["record_group_first_class"] == r["record_group_first_class"] == "marriage"
    assert m["obligation_content_digest"] == r["obligation_content_digest"]
    assert (m["record_count"], s["record_count"], e["record_count"]) == (2, 3, 0)
    assert e["record_content_digest"] is None and e["record_group_size"] is None       # an empty set is not a share
    assert m["stored_inventory_digest"] == "a" * 64 and m["stored_ledger_digest"] == "b" * 64


def test_class_inventory_digest_reads_only_the_latest_completed_generation_of_the_chart(conn):
    rec = [("p1", "conjunction")]
    add_class(conn, CHART, "5.0", "marriage", True, rec)                               # older, complete
    add_class(conn, CHART, "5.1", "marriage", True, rec)                               # latest complete
    add_class(conn, CHART, "5.1", "surgery", True, rec)
    add_class(conn, CHART, "5.2", "marriage", True, rec)                               # newer but one class unfinished
    add_class(conn, CHART, "5.2", "surgery", False, rec)
    add_class(conn, OTHER_CHART, "9.9", "marriage", True, rec)                         # another chart, newer still
    rows = run_readback(conn, DIGEST)
    assert {(r["generation"], r["event_class"]) for r in rows} == {("5.1", "marriage"), ("5.1", "surgery")}
    assert all(r["record_count"] == 1 for r in rows)
