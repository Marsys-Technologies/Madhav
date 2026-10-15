"""Contract fixtures only: accepted L0-M migration/reseal remains a prerequisite."""
import json
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import pytest

from tests.l3.ka_muhurta_seva.conftest import request_data, sky  # noqa: F401
from services.ka_muhurta_seva import parihara_eval as ev
from routers import parihara_evaluate as route


@pytest.fixture(scope="module")
def db_dsn(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn) as conn:
        conn.execute("""CREATE TABLE bg_parihara_rules (
            id bigint PRIMARY KEY, cancellation_index integer DEFAULT 100, dosha_canonical_id text NOT NULL, scope text NOT NULL,
            source_citation text, source_chunk_id text, source_verse integer, cancellation_condition_text text,
            predicate jsonb, conjunction_reading text, tika_extension boolean,
            priority_rank text, net_standing text, extraction_context text)""")
        for row in json.loads((Path(__file__).parents[2] / "ka_muhurta_seva" / "parihara_predicates.json").read_text()):
            conn.execute("""INSERT INTO bg_parihara_rules (id,dosha_canonical_id,scope,source_citation,source_chunk_id,source_verse,
                cancellation_condition_text,predicate,conjunction_reading,tika_extension,priority_rank,
                net_standing,extraction_context) VALUES (
                %(id)s,%(dosha_canonical_id)s,%(scope)s,%(source_citation)s,%(source_chunk_id)s,%(source_verse)s,
                %(cancellation_condition_text)s,%(predicate)s,%(conjunction_reading)s,%(tika_extension)s,
                %(priority_rank)s,%(net_standing)s,%(extraction_context)s)""",dict(row,predicate=Jsonb(row["predicate"])))
    yield isolated_kala_db_dsn

def test_scoped_read_only_source_roundtrip_and_unknown_readings(db_dsn,request_data,sky):
    sky(longitudes={"Mars":220.})
    with psycopg.connect(db_dsn,row_factory=dict_row) as conn:
        conn.read_only=True
        rows=ev.load_rules(conn,"marriage",["venus_sixth","kartari"])
        request_data["dosas_present"]=["venus_sixth","kartari"]
        out=ev.evaluate_candidate(**request_data,rules=rows)
        assert [(d["state"],d["reason"]) for d in out["dosas"]]==[("cancelled",None),("cancellation_unassessed","predicate_not_encoded")]
        assert {r["rule_id"] for r in out["rules"]}=={202,203,204}
        assert [r["source_verse"] for r in rows]==[88,88,88]
        assert [r["source_verse"] for r in out["rules"]]==[88,88,88]
        assert ev.load_rules(conn,"business",["venus_sixth"])==[]
        assert ev.load_rules(conn,"marriage",["venus_sixth'); DROP TABLE bg_parihara_rules; --"])==[]
        assert conn.execute("SELECT count(*) AS n FROM bg_parihara_rules").fetchone()["n"]==6
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction): conn.execute("DELETE FROM bg_parihara_rules")


def test_mars_v88_disagreement_survives_read_only_source_roundtrip(db_dsn,request_data,sky):
    """NB-02: neither source reading may disappear between storage and evaluation."""
    sky(longitudes={"Mars":220.})
    request_data["dosas_present"]=["mars_eighth"]
    with psycopg.connect(db_dsn,row_factory=dict_row) as conn:
        conn.read_only=True
        rows=ev.load_rules(conn,"marriage",["mars_eighth"])
        out=ev.evaluate_candidate(**request_data,rules=rows)
    assert out["dosas"]==[{"dosha_canonical_id":"mars_eighth","by_rules":[201,206],
                           "state":"cancellation_unassessed","reason":"readings_disagree"}]
    assert [(r["rule_id"],r["result"],r["extraction_context"],r["source_chunk_id"])
            for r in out["rules"]]==[
        (201,"applies","tika_commentary","muhurta_chintamani_pg0116_c01"),
        (206,"does_not_apply","mula_reconstructed","muhurta_chintamani_pg0115_c02"),
    ]


def test_real_route_connection_is_read_only(monkeypatch,db_dsn):
    monkeypatch.setattr(route,"_db_url",lambda:db_dsn)
    with route._connect() as conn:
        assert conn.read_only
        assert conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"]=="on"
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction): conn.execute("DELETE FROM bg_parihara_rules")


@pytest.mark.parametrize("column", ["predicate", "source_verse"])
def test_missing_typed_schema_is_loud_not_no_rules(db_dsn,column):
    with psycopg.connect(db_dsn,row_factory=dict_row) as conn:
        conn.execute(f"ALTER TABLE bg_parihara_rules RENAME COLUMN {column} TO unavailable_column")
        with pytest.raises(psycopg.errors.UndefinedColumn): ev.load_rules(conn,"marriage",["venus_sixth"])
        conn.rollback()
