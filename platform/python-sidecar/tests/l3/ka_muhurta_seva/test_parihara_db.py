"""Contract fixtures only: accepted L0-M migration/reseal remains a prerequisite."""
import json
import os
from pathlib import Path
import uuid

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import pytest

from tests.l3._disposable_db_guard import validate_disposable_dsn, assert_disposable_connection
from services.ka_muhurta_seva import parihara_eval as ev
from routers import parihara_evaluate as route


@pytest.fixture(scope="module")
def db_dsn():
    dsn=os.environ.get("KALA_ADMIN_DSN")
    required=os.environ.get("KALA_REQUIRE_DB")=="1"
    if not dsn:
        if required: pytest.fail("KALA_REQUIRE_DB=1 requires KALA_ADMIN_DSN")
        pytest.skip("deferred to CI: no disposable database DSN")
    validate_disposable_dsn(dsn,"postgres")
    try: admin=psycopg.connect(dsn,autocommit=True,connect_timeout=3)
    except psycopg.Error:
        if required: pytest.fail("disposable database unreachable")
        pytest.skip("deferred to CI: disposable database unreachable")
    name="kala_parihara_"+uuid.uuid4().hex
    created=False
    try:
        assert_disposable_connection(admin,"postgres")
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        created=True
        child=psycopg.conninfo.make_conninfo(dsn,dbname=name)
        validate_disposable_dsn(child,name)
        with psycopg.connect(child) as conn:
            assert_disposable_connection(conn,name)
            conn.execute("""CREATE TABLE bg_parihara_rules (
                id bigint PRIMARY KEY, cancellation_index integer DEFAULT 100, dosha_canonical_id text NOT NULL, scope text NOT NULL,
                source_citation text, source_chunk_id text, cancellation_condition_text text,
                predicate jsonb, conjunction_reading text, tika_extension boolean,
                priority_rank text, net_standing text, extraction_context text)""")
            for row in json.loads(Path(__file__).with_name("parihara_predicates.json").read_text()):
                conn.execute("""INSERT INTO bg_parihara_rules (id,dosha_canonical_id,scope,source_citation,source_chunk_id,
                    cancellation_condition_text,predicate,conjunction_reading,tika_extension,priority_rank,
                    net_standing,extraction_context) VALUES (
                    %(id)s,%(dosha_canonical_id)s,%(scope)s,%(source_citation)s,%(source_chunk_id)s,
                    %(cancellation_condition_text)s,%(predicate)s,%(conjunction_reading)s,%(tika_extension)s,
                    %(priority_rank)s,%(net_standing)s,%(extraction_context)s)""",dict(row,predicate=Jsonb(row["predicate"])))
        yield child
    finally:
        if created:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
        admin.close()


def test_scoped_read_only_source_roundtrip_and_unknown_readings(db_dsn,request_data,sky):
    sky(longitudes={"Mars":220.})
    with psycopg.connect(db_dsn,row_factory=dict_row) as conn:
        conn.read_only=True
        rows=ev.load_rules(conn,"marriage",["venus_sixth","kartari"])
        request_data["dosas_present"]=["venus_sixth","kartari"]
        out=ev.evaluate_candidate(**request_data,rules=rows)
        assert [(d["state"],d["reason"]) for d in out["dosas"]]==[("cancelled",None),("cancellation_unassessed","predicate_not_encoded")]
        assert {r["rule_id"] for r in out["rules"]}=={202,203,204}
        assert ev.load_rules(conn,"business",["venus_sixth"])==[]
        assert ev.load_rules(conn,"marriage",["venus_sixth'); DROP TABLE bg_parihara_rules; --"])==[]
        assert conn.execute("SELECT count(*) AS n FROM bg_parihara_rules").fetchone()["n"]==5
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction): conn.execute("DELETE FROM bg_parihara_rules")


def test_real_route_connection_is_read_only(monkeypatch,db_dsn):
    monkeypatch.setattr(route,"_db_url",lambda:db_dsn)
    with route._connect() as conn:
        assert conn.read_only
        assert conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"]=="on"
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction): conn.execute("DELETE FROM bg_parihara_rules")


def test_missing_typed_schema_is_loud_not_no_rules(db_dsn):
    with psycopg.connect(db_dsn,row_factory=dict_row) as conn:
        conn.execute("ALTER TABLE bg_parihara_rules RENAME COLUMN predicate TO unavailable_predicate")
        with pytest.raises(psycopg.errors.UndefinedColumn): ev.load_rules(conn,"marriage",["venus_sixth"])
        conn.rollback()
