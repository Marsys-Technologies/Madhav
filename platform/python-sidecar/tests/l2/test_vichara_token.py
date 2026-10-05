"""N-143 option B (SS 2026-10-05): L2 cites a DETERMINISTIC vichara token, never the bigserial chart_vichara.id.

Covers
  * the ONE Python definition (bodha_writers.vichara_token): golden vector, canonicalization rules (NULL vs empty, float
    refusal, trim_scale, unicode / control characters, key order), the token detector;
  * migration 1295 (the SQL resolver): its function body is GENERATED from the same template (byte-for-byte test),
    it runs on a disposable PostgreSQL with stub roles, is re-runnable, refuses to widen access, and the SQL token equals
    the Python token on every row of a production-shaped fixture plus a hostile-value fuzz set (float / NULL / jsonb
    canonicalization, the places the two definitions could drift);
  * the writers: bo_karanajala's three vichara lookups cite tokens (not ids) and choose among duplicate rows by token, not
    by row order; _batch_insert refuses a serial; bo_yantra_mechanism refuses an un-rebuilt serial; bo_upaya's leverage
    fetch returns `vichara_token`.
No production access.
"""
from __future__ import annotations

import json
import os
import pathlib
import random
import re
import sys
from decimal import Decimal
from typing import Any

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import bodha_writers.vichara_token as vt  # noqa: E402
import pipeline.orchestrator.writers.bo_karanajala as k  # noqa: E402
import pipeline.orchestrator.writers.bo_yantra_mechanism as ym  # noqa: E402
import pipeline.orchestrator.writers.bo_upaya as up  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[4]
MIG = REPO / "platform" / "migrations" / "1295_chart_vichara_token_resolver.sql"

GOLDEN_ARGS = ("lahiri_chitrapaksha", "valence_pass", "SUN", "SUN", "D1_HOUSE_1", None, "D1", "D1", "mixed", "0.50",
               '{"varga": "D1", "link_kind": "lord_placed"}', ["3f2a9c1d5b7e4a60", "9d8c7b6a5f4e3d2c"])
GOLDEN_TOKEN = "3bf71fa91397a24a"


def tok(**over):
    vals = dict(zip(vt.VICHARA_KEY_FIELDS, GOLDEN_ARGS[:10] + (GOLDEN_ARGS[10], GOLDEN_ARGS[11])))
    vals["value_jsonb_text"] = vals.pop("value_jsonb")
    for key, val in over.items():
        vals["value_jsonb_text" if key == "value_jsonb" else key] = val
    return vt.vichara_token(**vals)


# ── 1. The Python definition ─────────────────────────────────────────────────────────────────────

class TestPythonDefinition:
    def test_golden_vector(self):
        assert vt.vichara_token(*GOLDEN_ARGS) == GOLDEN_TOKEN
        assert tok() == GOLDEN_TOKEN

    def test_canonical_json_shape(self):
        assert vt.canonical_vichara_key_json(*GOLDEN_ARGS) == (
            '["lahiri_chitrapaksha","valence_pass","SUN","SUN","D1_HOUSE_1",null,"D1","D1","mixed",0.5,'
            '{"varga": "D1", "link_kind": "lord_placed"},["3f2a9c1d5b7e4a60","9d8c7b6a5f4e3d2c"]]')

    def test_token_is_16_lowercase_hex(self):
        assert vt.is_vichara_token(GOLDEN_TOKEN) and len(GOLDEN_TOKEN) == 16

    @pytest.mark.parametrize("field", ["ayanamsha_id", "vichara_family", "subject", "actor", "target", "domain",
                                        "varga_id", "varga", "value_text"])
    def test_every_text_field_is_part_of_the_key(self, field):
        assert tok(**{field: "changed"}) != GOLDEN_TOKEN

    def test_value_num_jsonb_and_facts_are_part_of_the_key(self):
        assert tok(value_num="0.51") != GOLDEN_TOKEN
        assert tok(value_jsonb='{"varga": "D2"}') != GOLDEN_TOKEN
        assert tok(constituent_facts_array=["3f2a9c1d5b7e4a60"]) != GOLDEN_TOKEN, "a changed fact set gives a NEW token"
        assert tok(constituent_facts_array=["9d8c7b6a5f4e3d2c", "3f2a9c1d5b7e4a60"]) != GOLDEN_TOKEN, "array order is part of the key"

    def test_null_and_empty_are_distinct(self):
        assert tok(constituent_facts_array=None) != tok(constituent_facts_array=[])
        assert tok(actor=None) != tok(actor="")
        assert tok(value_num=None) != tok(value_num="0")
        assert tok(value_jsonb=None) != tok(value_jsonb="{}")

    def test_value_num_scale_does_not_change_the_token(self):
        assert tok(value_num="0.50") == tok(value_num="0.5") == tok(value_num=Decimal("0.5000"))
        assert tok(value_num="100") != tok(value_num="1")
        assert tok(value_num="0.00") == tok(value_num="0") == tok(value_num=0)

    def test_float_is_refused(self):
        with pytest.raises(TypeError, match="never a float"):
            tok(value_num=0.5)
        with pytest.raises(TypeError):
            tok(value_num=True)

    def test_nan_is_a_string_not_a_number(self):
        assert vt.canonical_vichara_key_json(*GOLDEN_ARGS[:9], "NaN", GOLDEN_ARGS[10], GOLDEN_ARGS[11]).count('"NaN"') == 1

    def test_unicode_is_raw_and_control_chars_use_lowercase_u_escapes(self):
        c = vt.canonical_vichara_key_json("é", "日本", 'q"b\\', "a\nb\tc", "\x01\x1f\x7f", None, None, None, None, None, None, None)
        assert c.startswith('["é","日本","q\\"b\\\\","a\\nb\\tc","\\u0001\\u001f\x7f",')

    def test_jsonb_text_is_taken_verbatim(self):
        weird = '{"b": 1.50, "aa": [1, 2], "a": null}'
        assert weird in vt.canonical_vichara_key_json(*GOLDEN_ARGS[:10], weird, GOLDEN_ARGS[11])

    def test_inputs_are_type_checked(self):
        with pytest.raises(TypeError):
            tok(value_jsonb={"a": 1})
        with pytest.raises(TypeError):
            tok(constituent_facts_array="abc")
        with pytest.raises(TypeError):
            tok(constituent_facts_array=[1, 2])
        with pytest.raises(TypeError):
            tok(subject=7)

    def test_from_row_dict_and_tuple(self):
        d = dict(zip(("ayanamsha_id", "vichara_family", "subject", "actor", "target", "domain", "varga_id", "varga",
                      "value_text", "value_num_text", "value_jsonb_text", "constituent_facts_array"), GOLDEN_ARGS))
        assert vt.vichara_token_from_row(d) == GOLDEN_TOKEN
        assert vt.vichara_token_from_row(tuple(GOLDEN_ARGS)) == GOLDEN_TOKEN
        assert vt.vichara_token_from_row(tuple(GOLDEN_ARGS) + ("extra",)) == GOLDEN_TOKEN
        with pytest.raises(KeyError):
            vt.vichara_token_from_row({"subject": "x"})
        with pytest.raises(ValueError):
            vt.vichara_token_from_row(GOLDEN_ARGS[:5])

    @pytest.mark.parametrize("bad", ["167204", 167204, "3F2A9C1D5B7E4A60", "3f2a9c1d5b7e4a6", "3f2a9c1d5b7e4a600", "", None])
    def test_detector_rejects_serials_and_malformed(self, bad):
        assert not vt.is_vichara_token(bad)
        with pytest.raises(ValueError, match="not a vichara token"):
            vt.assert_vichara_tokens([GOLDEN_TOKEN, bad], where="t")

    def test_detector_accepts_tokens_and_empty(self):
        vt.assert_vichara_tokens([GOLDEN_TOKEN, "0000000000000000"])
        vt.assert_vichara_tokens([])
        vt.assert_vichara_tokens(None)


# ── 2. Migration 1295 text is generated from the same template ───────────────────────────────────

class TestMigrationIsGeneratedFromTheTemplate:
    SQL = MIG.read_text()

    def test_function_body_equals_template_rendering(self):
        body = vt.TOKEN_SQL_TEMPLATE.format(**{f: f"p_{f}" for f in vt.VICHARA_KEY_FIELDS})
        assert body in self.SQL, "migration 1295's function body must be TOKEN_SQL_TEMPLATE with the p_* parameters"

    def test_golden_token_in_migration_is_the_python_golden(self):
        assert self.SQL.count(GOLDEN_TOKEN) >= 2
        assert vt.vichara_token(*GOLDEN_ARGS) == GOLDEN_TOKEN

    def test_template_binds_the_columns_for_the_inline_measurement(self):
        expr = vt.token_sql_for_alias("v")
        assert "v.value_jsonb::text" in expr and "trim_scale(v.value_num)" in expr
        with pytest.raises(ValueError):
            vt.token_sql(ayanamsha_id="a")


# ── 3. Migration 1295 on a disposable PostgreSQL; SQL token == Python token ───────────────────────

from tests.pg_disposable import pg, psql, q, new_db, requires_pg  # noqa: E402,F401

CHART_VICHARA_DDL = """
CREATE TABLE public.chart_vichara (
  id bigserial PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid,
  vichara_family text NOT NULL, subject text NOT NULL, actor text, target text, domain text, varga_id text, varga text,
  value_num numeric, value_text text, value_jsonb jsonb, ratification_factor numeric, constituent_fact_ids text[],
  constituent_facts_array text[], formula_version text, source_citation text, computed_at timestamptz NOT NULL DEFAULT now()
)"""
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


def _roles(port):
    for role in ("suvarna_reader", "data_plane_builder", "retrieval_census_ro", "stranger"):
        q(port, "postgres", f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{role}') THEN CREATE ROLE {role}; END IF; END $$")


def _fresh_db(port, grant_select_to=("suvarna_reader", "data_plane_builder")):
    _roles(port)
    db = new_db(port)
    q(port, db, CHART_VICHARA_DDL)
    for r in grant_select_to:
        q(port, db, f"GRANT SELECT ON public.chart_vichara TO {r}")
    return db


def _apply(port, db):
    return psql(port, db, file=MIG, single_transaction=True)


def _conn(port, db):
    import psycopg
    return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=db, autocommit=True)


def _fuzz_rows(n: int = 400) -> list[dict[str, Any]]:
    rnd = random.Random(1295)
    texts = [None, "", "SUN", "D1_HOUSE_9", "é", "日本語", "😀", 'q"uote', "back\\slash", "a\nb", "tab\tc", "\x01\x1f", "\x7f",
             " ", "%", "{\"a\":1}", " lead", "trail ", "null", "NULL"]
    nums = [None, "0", "0.00", "1", "1.50", "-0.5", "100", "0.000000001", "123456789012345678901234567890.123456789000",
            "NaN", "-12.340", "1E+3", "5e-3"]
    jsons = [None, "{}", "[]", "null", "1.50", "0", '"x"', '{"b": 1, "aa": 2, "a": 3}', '{"varga": "D1", "n": 1.50, "z": [1, 2.0, null]}',
             '{"é": "日本", "k": "q\\"b"}', '{"nested": {"bb": 1, "a": {"cc": [3, 2, 1]}}}', '[{"b": 1}, {"a": 2}]',
             '{"big": 12345678901234567890.123456789, "neg": -0.000, "e": 1e3}']
    facts = [None, [], ["a"], ["b", "a"], ["é", "日本"], ['q"b', "x\\y"], ["3f2a9c1d5b7e4a60", "9d8c7b6a5f4e3d2c"], [""], ["a", None]]
    rows = []
    for i in range(n):
        rows.append({
            "chart_id": CHART_A if i % 3 else CHART_B,
            "ayanamsha_id": rnd.choice(["lahiri_chitrapaksha", "raman", "é"]),
            "vichara_family": rnd.choice(["valence_pass", "varga_consistency", "varga_ratification", "leverage_index"]),
            "subject": rnd.choice([t for t in texts if t is not None]),
            "actor": rnd.choice(texts), "target": rnd.choice(texts), "domain": rnd.choice(texts),
            "varga_id": rnd.choice(texts), "varga": rnd.choice(texts), "value_text": rnd.choice(texts),
            "value_num": rnd.choice(nums), "value_jsonb": rnd.choice(jsons), "facts": rnd.choice(facts),
        })
    return rows


def _insert(conn, rows):
    for r in rows:
        conn.execute(
            """INSERT INTO public.chart_vichara (chart_id, ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id,
                 varga, value_text, value_num, value_jsonb, constituent_facts_array)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::numeric,%s::jsonb,%s)""",
            (r["chart_id"], r["ayanamsha_id"], r["vichara_family"], r["subject"], r["actor"], r["target"], r["domain"],
             r["varga_id"], r["varga"], r["value_text"], r["value_num"], r["value_jsonb"], r["facts"]))


def _production_shaped_rows() -> list[dict[str, Any]]:
    """valence_pass / varga_consistency / varga_ratification / leverage_index rows with the shapes production holds."""
    rows = []
    for aya in ("lahiri_chitrapaksha", "raman"):
        for actor in ("SUN", "MOON", "MAR", "RAH_MEAN"):
            for h in range(1, 13):
                rows.append({"chart_id": CHART_A, "ayanamsha_id": aya, "vichara_family": "valence_pass", "subject": actor,
                             "actor": actor, "target": f"D1_HOUSE_{h}", "domain": None, "varga_id": "D1", "varga": "D1",
                             "value_text": ["mixed", "benefic", "malefic", "neutral"][h % 4], "value_num": str(round(0.1 * h - 0.3, 1)),
                             "value_jsonb": json.dumps({"varga": "D1", "link_kind": "lord_aspects", "matrix_key": "mixed", "t": h}),
                             "facts": [f"{h:016x}", f"{h + 1:016x}"]})
            rows.append({"chart_id": CHART_A, "ayanamsha_id": aya, "vichara_family": "varga_consistency", "subject": actor,
                         "actor": None, "target": None, "domain": None, "varga_id": None, "varga": None, "value_text": None,
                         "value_num": "0.8571428571", "value_jsonb": "{}", "facts": []})
            rows.append({"chart_id": CHART_A, "ayanamsha_id": aya, "vichara_family": "varga_ratification", "subject": actor,
                         "actor": None, "target": None, "domain": "wealth", "varga_id": None, "varga": None, "value_text": None,
                         "value_num": "1.2", "value_jsonb": '{"d": 1}', "facts": ["aaaaaaaaaaaaaaaa"]})
    return rows


@requires_pg
class TestResolverOnPostgres:
    def test_apply_is_rerunnable_and_grants_exactly_two_roles(self, pg):
        db = _fresh_db(pg)
        assert _apply(pg, db).returncode == 0
        r2 = _apply(pg, db)
        assert r2.returncode == 0, r2.stderr
        got = q(pg, db, "SELECT has_table_privilege('suvarna_reader','public.vw_chart_vichara_token','SELECT'), "
                        "has_table_privilege('data_plane_builder','public.vw_chart_vichara_token','SELECT'), "
                        "has_table_privilege('retrieval_census_ro','public.vw_chart_vichara_token','SELECT'), "
                        "has_table_privilege('stranger','public.vw_chart_vichara_token','SELECT'), "
                        "has_function_privilege('suvarna_reader','public.chart_vichara_token(text,text,text,text,text,text,text,text,text,numeric,jsonb,text[])','EXECUTE'), "
                        "has_function_privilege('stranger','public.chart_vichara_token(text,text,text,text,text,text,text,text,text,numeric,jsonb,text[])','EXECUTE')")
        assert got == "t|t|f|f|t|f"
        assert q(pg, db, "SELECT count(*) FROM pg_proc WHERE proname='chart_vichara_token'") == "1"

    def test_changes_no_table_and_stores_no_column(self, pg):
        db = _fresh_db(pg)
        before = q(pg, db, "SELECT string_agg(column_name, ',' ORDER BY ordinal_position) FROM information_schema.columns WHERE table_name='chart_vichara'")
        assert _apply(pg, db).returncode == 0
        assert q(pg, db, "SELECT string_agg(column_name, ',' ORDER BY ordinal_position) FROM information_schema.columns WHERE table_name='chart_vichara'") == before
        assert q(pg, db, "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname NOT LIKE 'chart_vichara%' AND c.relname <> 'vw_chart_vichara_token' AND c.relkind IN ('r','m')") == "0"

    def test_refuses_when_a_role_would_gain_access_it_did_not_have(self, pg):
        db = _fresh_db(pg, grant_select_to=("suvarna_reader",))   # data_plane_builder cannot read chart_vichara here
        r = _apply(pg, db)
        assert r.returncode != 0 and "does not already read public.chart_vichara" in r.stderr
        assert q(pg, db, "SELECT count(*) FROM pg_proc WHERE proname='chart_vichara_token'") == "0", "a refused apply must leave nothing behind"

    def test_refuses_when_the_table_is_missing(self, pg):
        _roles(pg)
        db = new_db(pg)
        r = _apply(pg, db)
        assert r.returncode != 0 and "chart_vichara does not exist" in r.stderr

    def test_sql_token_equals_python_token_on_production_shaped_and_hostile_rows(self, pg):
        db = _fresh_db(pg)
        assert _apply(pg, db).returncode == 0
        rows = _production_shaped_rows() + _fuzz_rows()
        with _conn(pg, db) as c:
            _insert(c, rows)
            # the Python side reads exactly what a writer reads: the shared SELECT list
            got = c.execute(
                f"SELECT {vt.VICHARA_KEY_SELECT_SQL}, id, chart_id FROM chart_vichara ORDER BY id").fetchall()
            sql = {r[0]: r[1] for r in c.execute("SELECT id, vichara_token FROM vw_chart_vichara_token").fetchall()}
        assert len(got) == len(rows) == len(sql)
        mismatches = []
        for r in got:
            py = vt.vichara_token_from_row(r)
            if py != sql[r[12]]:
                mismatches.append((r[12], py, sql[r[12]], r[:12]))
        assert not mismatches, f"{len(mismatches)} SQL/Python token mismatches, first: {mismatches[:2]}"

    def test_token_is_unique_per_chart_on_production_shaped_rows_and_distinct_keys_never_collide(self, pg):
        db = _fresh_db(pg)
        assert _apply(pg, db).returncode == 0
        rows = _production_shaped_rows()
        with _conn(pg, db) as c:
            _insert(c, rows)
            n, d = c.execute("SELECT count(*), count(DISTINCT (chart_id, vichara_token)) FROM vw_chart_vichara_token").fetchone()
        assert n == d == len(rows)

    def test_a_citation_resolves_to_exactly_one_row_and_a_changed_fact_set_gets_a_new_token(self, pg):
        db = _fresh_db(pg)
        assert _apply(pg, db).returncode == 0
        with _conn(pg, db) as c:
            _insert(c, _production_shaped_rows())
            t = c.execute("SELECT vichara_token FROM vw_chart_vichara_token WHERE vichara_family='valence_pass' AND subject='SUN' AND target='D1_HOUSE_3' AND ayanamsha_id='raman'").fetchone()[0]
            assert c.execute("SELECT count(*) FROM vw_chart_vichara_token WHERE chart_id=%s AND vichara_token=%s", (CHART_A, t)).fetchone()[0] == 1
            # a rebuild renumbers the serial (DELETE + INSERT) but the token survives
            old_id = c.execute("SELECT id FROM vw_chart_vichara_token WHERE vichara_token=%s", (t,)).fetchone()[0]
            row = c.execute("SELECT chart_id, ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id, varga, value_text, value_num, value_jsonb, constituent_facts_array FROM chart_vichara WHERE id=%s", (old_id,)).fetchone()
            c.execute("DELETE FROM chart_vichara WHERE chart_id=%s", (CHART_A,))
            c.execute("INSERT INTO chart_vichara (chart_id, ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id, varga, value_text, value_num, value_jsonb, constituent_facts_array) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                      (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], json.dumps(row[11]), row[12]))
            new = c.execute("SELECT id, vichara_token FROM vw_chart_vichara_token WHERE chart_id=%s", (CHART_A,)).fetchone()
            assert new[0] != old_id and new[1] == t, "serial changed, token did not"
            c.execute("UPDATE chart_vichara SET constituent_facts_array = ARRAY['zzzzzzzzzzzzzzzz'] WHERE chart_id=%s", (CHART_A,))
            assert c.execute("SELECT vichara_token FROM vw_chart_vichara_token WHERE chart_id=%s", (CHART_A,)).fetchone()[0] != t

    def test_exact_duplicate_rows_share_one_token_and_are_reported_not_hidden(self, pg):
        db = _fresh_db(pg)
        assert _apply(pg, db).returncode == 0
        with _conn(pg, db) as c:
            r = _production_shaped_rows()[0]
            _insert(c, [r, r])
            n, d = c.execute("SELECT count(*), count(DISTINCT vichara_token) FROM vw_chart_vichara_token").fetchone()
        assert (n, d) == (2, 1)

    def test_null_and_json_null_scalar_coincide_documented(self, pg):
        # A SQL NULL and the jsonb scalar null render the same ('null'); production holds no jsonb null scalar (measured).
        db = _fresh_db(pg)
        assert _apply(pg, db).returncode == 0
        with _conn(pg, db) as c:
            sql_null = c.execute("SELECT chart_vichara_token('a','b','c',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL)").fetchone()[0]
            json_null = c.execute("SELECT chart_vichara_token('a','b','c',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'null'::jsonb,NULL)").fetchone()[0]
        assert sql_null == json_null == vt.vichara_token("a", "b", "c", None, None, None, None, None, None, None, None, None)


# ── 4. The writers cite tokens, not serials ──────────────────────────────────────────────────────

def _vrow(**kw):
    base = dict(ayanamsha_id="lahiri_chitrapaksha", vichara_family="valence_pass", subject="MAR", actor="MAR",
                target="D1_HOUSE_7", domain=None, varga_id="D1", varga="D1", value_text="benefic", value_num_text="0.5",
                value_jsonb_text='{"varga": "D1"}', constituent_facts_array=["f1"])
    base.update(kw)
    return base


class _Res:
    def __init__(self, rows): self._r = rows
    def fetchall(self): return self._r


class _Conn:
    def __init__(self, rows): self.rows, self.sql = rows, []
    def execute(self, sql, params=None):
        self.sql.append(sql)
        return _Res(self.rows)


class TestSelectListIsOneDefinition:
    def test_writer_local_literals_equal_the_shared_select_list(self):
        # The footprint scan refuses an imported SQL constant, so each writer carries its own literal; they must not drift.
        assert k._VICHARA_KEY_SELECT_SQL == vt.VICHARA_KEY_SELECT_SQL
        assert up._VICHARA_KEY_SELECT_SQL == vt.VICHARA_KEY_SELECT_SQL

    def test_writers_do_not_import_the_sql_constant(self):
        for mod in (k, up):
            assert "VICHARA_KEY_SELECT_SQL" not in {n for n in vars(mod) if n == "VICHARA_KEY_SELECT_SQL"}


class TestBoKaranajalaCitesTokens:
    def test_valence_lookup_value_is_token_not_serial(self):
        r = _vrow()
        out = k._fetch_vichara_valence_by_actor_house(_Conn([r]), "c", "a")
        label, cited = out[("MAR", 7)]
        assert label == "benefic" and cited == vt.vichara_token_from_row(r) and vt.is_vichara_token(cited)

    def test_select_list_is_the_shared_natural_key_and_no_serial_id(self):
        c = _Conn([])
        k._fetch_vichara_valence_by_actor_house(c, "c", "a")
        k._fetch_vichara_consistency_by_subject(c, "c", "a")
        k._fetch_vichara_ratification_by_subject_domain(c, "c", "a")
        assert len(c.sql) == 3
        for s in c.sql:
            flat = " ".join(s.split())
            assert vt.VICHARA_KEY_SELECT_SQL in flat
            assert not re.search(r"\bSELECT\s+id\b|\bid\s*,", flat), "the bigserial id must not be selected"

    def test_duplicate_rows_resolve_by_smallest_token_regardless_of_row_order(self):
        a = _vrow(value_jsonb_text='{"varga": "D1", "link_kind": "lord_aspects"}', constituent_facts_array=["f1"])
        b = _vrow(value_jsonb_text='{"varga": "D1", "link_kind": "graha_aspect_parashari"}', constituent_facts_array=["f2"])
        c3 = _vrow(value_jsonb_text='{"varga": "D1", "link_kind": "lord_placed"}', constituent_facts_array=["f3"])
        want = min(vt.vichara_token_from_row(x) for x in (a, b, c3))
        for order in ([a, b, c3], [c3, b, a], [b, c3, a]):
            assert k._fetch_vichara_valence_by_actor_house(_Conn(order), "c", "a")[("MAR", 7)][1] == want

    def test_consistency_and_ratification_carry_tokens_and_float_values(self):
        cons = _vrow(vichara_family="varga_consistency", subject="SAT", actor=None, target=None, varga_id=None, varga=None,
                     value_text=None, value_num_text="0.8571428571")
        rat = _vrow(vichara_family="varga_ratification", subject="SAT", actor=None, target=None, domain="wealth", varga_id=None,
                    varga=None, value_text=None, value_num_text=None)
        rat["ratification_factor_text"] = "1.4"
        co = k._fetch_vichara_consistency_by_subject(_Conn([cons]), "c", "a")
        ra = k._fetch_vichara_ratification_by_subject_domain(_Conn([rat]), "c", "a")
        assert co["SAT"] == (0.8571428571, vt.vichara_token_from_row(cons))
        assert ra[("SAT", "wealth")] == (1.4, vt.vichara_token_from_row(rat))

    def test_tuple_rows_work(self):
        r = _vrow()
        tup = tuple(r[f] for f in ("ayanamsha_id", "vichara_family", "subject", "actor", "target", "domain", "varga_id", "varga",
                                   "value_text", "value_num_text", "value_jsonb_text", "constituent_facts_array"))
        out = k._fetch_vichara_valence_by_actor_house(_Conn([tup]), "c", "a")
        assert out[("MAR", 7)][1] == vt.vichara_token_from_row(r)

    def test_edge_strength_still_returns_the_cited_tokens(self):
        r = _vrow()
        lk = object.__new__(k.ViharaLookups)
        lk.valence_by_actor_house = k._fetch_vichara_valence_by_actor_house(_Conn([r]), "c", "a")
        lk.consistency_by_subject, lk.ratification_by_subject_domain = {}, {}
        lk.occupied_house_by_graha = {"Mars": 7}
        _, cited = k._edge_strength_v1(0.5, "Mars", None, lk)
        assert cited == [vt.vichara_token_from_row(r)]

    def test_batch_insert_refuses_a_serial_and_accepts_tokens(self):
        class C:
            n = 0
            def execute(self, sql, row): C.n += 1
        ok = {"edge_type": "argala", "constituent_ga_vichara_ids_array": [GOLDEN_TOKEN]}
        assert k._batch_insert(C(), [ok], "SQL") == 1
        with pytest.raises(ValueError, match="not a vichara token"):
            k._batch_insert(C(), [{"edge_type": "aspect", "constituent_ga_vichara_ids_array": ["167204"]}], "SQL")
        assert k._batch_insert(C(), [{"edge_type": "x"}], "SQL") == 1, "rows without the column still default to []"


class TestYantraAndUpaya:
    def _edges(self, ids):
        return [{"edge_id": "e1", "computed_strength": 0.5, "weight_formula_version": "edge_strength_v1", "valence": "neutral",
                 "constituent_ga_vichara_ids_array": ids}]

    def test_mechanism_carries_member_edge_tokens_deduplicated(self):
        row = ym._make_mechanism("c", "a", "b", "now", mechanism_name="m", mechanism_class="dispositor_cycle",
                                 member_node_ids=["n1"], member_edges=self._edges([GOLDEN_TOKEN, GOLDEN_TOKEN, "0" * 16]),
                                 domains=None, nodes_by_id={},
                                 source_motif_id=None, citation_ref="r", citation_human="h")
        assert row["constituent_ga_vichara_ids_array"] == [GOLDEN_TOKEN, "0" * 16]

    def test_mechanism_refuses_a_serial_left_in_an_unrebuilt_edge(self):
        with pytest.raises(ValueError, match="not a vichara token"):
            ym._make_mechanism("c", "a", "b", "now", mechanism_name="m", mechanism_class="dispositor_cycle",
                               member_node_ids=["n1"], member_edges=self._edges(["167204"]), domains=None, nodes_by_id={},
                                 source_motif_id=None, citation_ref="r", citation_human="h")

    def test_upaya_leverage_fetch_returns_token_not_vichara_row_id(self):
        r1 = _vrow(vichara_family="leverage_index", subject="VEN", actor=None, target=None, domain="wealth", varga_id=None,
                   varga=None, value_text=None, value_num_text="3.9375", constituent_facts_array=["f1"])
        r2 = _vrow(vichara_family="leverage_index", subject="JUP", actor=None, target=None, domain="wealth", varga_id=None,
                   varga=None, value_text=None, value_num_text="1.336301", constituent_facts_array=["f3"])
        r1["constituent_fact_ids"], r2["constituent_fact_ids"] = ["fid1", "fid2"], ["fid3"]
        c = _Conn([r2, r1])
        out = up._fetch_wealth_leverage_index(c, "c", "a")
        assert [o["subject"] for o in out] == ["VEN", "JUP"], "ranked by leverage DESC"
        assert out[0] == {"vichara_token": vt.vichara_token_from_row(r1), "subject": "VEN", "value_num": Decimal("3.9375"),
                          "constituent_fact_ids": ["fid1", "fid2"]}
        assert "vichara_row_id" not in out[0]
        flat = " ".join(c.sql[0].split())
        assert not re.search(r"\bid AS\b", flat) and vt.VICHARA_KEY_SELECT_SQL in flat
