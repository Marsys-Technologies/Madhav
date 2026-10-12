"""test_ss_idem_update_only.py -- SS 2026-10-05 (Idem update-only): `update_only: {why, evidence}` reads Idem.pattern N/A (cause update-only-by-intent) ONLY when the writer scope
the Idem scan reads holds UPDATE statements on the asset's own table(s) and nothing that contradicts it. Real writers (bg_text_index, bo_laksana_rerank, and the negative controls bg_texts,
bo_laksana, bo_samvada) plus synthetic writer trees; offline."""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_w2_3_deeper_detectors as w3  # noqa: E402

NA, ND, FAIL, PARTIAL = ac.NA, ac.NO_DET, ac.FAIL, ac.PARTIAL
_HDR = w3._HDR
EV = "platform/python-sidecar/pipeline/orchestrator/writers/bg_text_index.py:546"
UO = dict(why="the writer UPDATEs one column of existing rows in place and never inserts or deletes one", evidence=EV)
REAL = {"bg_text_index": ["classical_text_chunks"], "bo_laksana_rerank": ["bodha_msr_signals"]}


def _crit(aid):
    return ac.registered_ids("")[aid], REAL[aid]


# ───────────────────────── registry / causes / rule ─────────────────────────

def test_the_cause_the_rule_row_and_the_revision_are_registered():
    assert "update-only-by-intent" in ac.NA_CAUSES["Idem.pattern"]
    assert ac.NA_RULE_DECISIONS["Idem.pattern#measured:update-only-by-intent"].startswith("SS 2026-10-05 Idem update-only")
    assert ac.CRITERION_REGISTRY["Idem.pattern"]["revision"] == 5 and "update_only" in ac.CRITERION_REGISTRY["Idem.pattern"]["applicability"]      # 4: SS 2026-10-05 update-only; 5: registry revision 28 (ONE bump)


# ───────────────────────── the declaration shape ─────────────────────────

def test_a_sound_declaration_is_accepted_and_the_committed_file_declares_exactly_two():
    assert ac.update_only_problem(dict(update_only=UO)) is None and ac.update_only_problem({}) is None
    assert sorted(a for a, e in ac.load_asset_declarations().items() if e.get("update_only")) == ["bg_text_index", "bo_laksana_rerank"]


@pytest.mark.parametrize("bad", [
    "text", dict(why="x"), dict(UO, extra=1), dict(UO, why="short"), dict(UO, why="the writer rebuilds its own table without touching a single other thing"),
    dict(UO, why="the writer UPDATEs rows, tbd after review"), dict(UO, evidence="unverified:the writer code was read"), dict(UO, evidence="platform/python-sidecar/nope.py:1"),
    dict(UO, evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_text_index.py"), dict(UO, evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_text_index.py:99999"),
])
def test_a_malformed_declaration_is_refused(bad):
    assert ac.update_only_problem(dict(update_only=bad))


def test_update_only_beside_produced_tables_is_refused_review_low_5():
    bad = ac.update_only_problem(dict(update_only=UO, produced_tables=[dict(table="bodha_x")]))
    assert bad and "produced_tables" in bad and "cannot stand beside" in bad
    assert ac.update_only_problem(dict(update_only=UO, produced_tables=None)) is None
    with pytest.raises(ac.DeclarationsError, match="produced_tables"):
        ac.validate_update_only_declaration("assets['x']", dict(update_only=UO, produced_tables=[dict(table="t")]))
    assert not any("produced_tables" in e for a, e in ac.load_asset_declarations().items() if e.get("update_only"))      # neither committed update-only asset declares a produced set


# ───────────────────────── the scan agreement, on the real writers ─────────────────────────

@pytest.mark.parametrize("aid", sorted(REAL))
def test_the_two_real_update_only_writers_agree(aid):
    files, tabs = _crit(aid)
    f = ac.idem_update_only_facts(aid, files, tabs)
    assert f["updates"] and (f["insert"], f["upsert"], f["replace"], f["dynamic"], f["beyond"]) == (0, 0, 0, 0, 0) and f["accumulating"] == []
    assert ac.update_only_scan_problem(f) is None
    r = ac._measure_idem(aid, files, "upsert", True, tabs, False, UO)
    assert r["v"] == NA and r["cause"] == "update-only-by-intent" and r["update_only"]["declared"] is True, r
    assert ac.rollup_asset("L2", {"Idem.pattern": r})["Idem"]["checks"][0]["v"] == NA


@pytest.mark.parametrize("aid,tabs", [("bg_texts", ["classical_text_chunks"]), ("bo_laksana", ["bodha_msr_signals"]), ("bo_samvada", ["vw_chart_digest"])])
def test_a_writer_that_inserts_replaces_or_writes_nothing_contradicts_the_declaration(aid, tabs):
    files = ac.registered_ids("")[aid]
    r = ac._measure_idem(aid, files, "upsert", True, tabs, False, UO)
    assert r["v"] == ND and r["declaration_disagreements"] and "contradicted" in r["measured"], r
    assert ac.rollup_asset("L2", {"Idem.pattern": r})["Idem"]["checks"][0]["v"] == ND


def test_without_the_declaration_the_real_writers_read_exactly_as_before():
    for aid, tabs in REAL.items():
        r = ac._measure_idem(aid, ac.registered_ids("")[aid], "upsert", True, tabs, False, None)
        assert r["v"] == PARTIAL and "only UPDATEd in place" in r["measured"], r


# ───────────────────────── synthetic writers: every contradiction ─────────────────────────

CLS = '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'


def _side(monkeypatch, tmp_path, body):
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/ka_up.py": _HDR + body})


def _measure(monkeypatch, tmp_path, body, uo=UO):
    _side(monkeypatch, tmp_path, body)
    return ac._measure_idem("ka_up", ["ka_up.py"], "upsert", True, ["kala_up"], False, uo)


def test_update_only_synthetic_agrees(monkeypatch, tmp_path):
    r = _measure(monkeypatch, tmp_path, CLS + '        ctx.db_conn.execute("UPDATE kala_up SET label = %s WHERE chart_id = %s", (1, 2))\n')
    assert r["v"] == NA and r["update_only"]["updates"], r


@pytest.mark.parametrize("extra", [
    '        ctx.db_conn.execute("INSERT INTO kala_up (a) VALUES (1)")\n',
    '        ctx.db_conn.execute("INSERT INTO kala_up (a) VALUES (1) ON CONFLICT (a) DO NOTHING")\n',
    '        ctx.db_conn.execute("DELETE FROM kala_up WHERE chart_id = %s", (1,))\n',
    '        ctx.db_conn.execute("TRUNCATE kala_up")\n',
])
def test_any_insert_upsert_or_delete_of_the_own_table_contradicts(monkeypatch, tmp_path, extra):
    r = _measure(monkeypatch, tmp_path, CLS + '        ctx.db_conn.execute("UPDATE kala_up SET label = %s WHERE chart_id = %s", (1, 2))\n' + extra)
    if "INSERT INTO kala_up (a) VALUES (1)\")" in extra:
        assert r["v"] == FAIL and "accretes" in r["measured"], r                    # a plain own-table INSERT is a measured FAIL of its own: the declaration never excuses it
    else:
        assert r["v"] == ND and "contradicted" in r["measured"], r


def test_a_write_to_another_table_does_not_contradict(monkeypatch, tmp_path):
    r = _measure(monkeypatch, tmp_path, CLS + '        ctx.db_conn.execute("UPDATE kala_up SET label = %s WHERE chart_id = %s", (1, 2))\n'
                 '        ctx.db_conn.execute("INSERT INTO kala_other (a) VALUES (1)")\n')
    assert r["v"] == NA, r


def test_an_accumulating_assignment_is_a_measured_fail_the_declaration_never_excuses(monkeypatch, tmp_path):
    r = _measure(monkeypatch, tmp_path, CLS + '        ctx.db_conn.execute("UPDATE kala_up SET n = n + 1 WHERE chart_id = %s", (1,))\n')
    assert r["v"] == FAIL and "accumulating" in r["measured"], r


def test_a_dynamic_statement_or_no_update_at_all_is_not_a_release(monkeypatch, tmp_path):
    r = _measure(monkeypatch, tmp_path, CLS + '        t = ctx.table\n        ctx.db_conn.execute(f"DELETE FROM {t}")\n        ctx.db_conn.execute("UPDATE kala_up SET label = 1 WHERE chart_id = %s", (1,))\n')
    assert r["v"] == ND, r
    r = _measure(monkeypatch, tmp_path, CLS + '        ctx.db_conn.execute("SELECT 1 FROM kala_up")\n')
    assert r["v"] == ND and "no UPDATE statement" in r["measured"], r


# ───────────────────────── the rollup refuses a forged release ─────────────────────────

def test_the_rollup_honours_only_a_record_that_carries_the_clean_block():
    good = dict(v=NA, cause="update-only-by-intent", measured="m", update_only=dict(declared=True, updates=["t (w.py:1)"], insert=0, upsert=0, replace=0, dynamic=0, beyond=0, accumulating=[]))
    assert ac.rollup_asset("L2", {"Idem.pattern": good})["Idem"]["checks"][0]["v"] == NA
    for mut in (dict(declared=False), dict(insert=1), dict(upsert=1), dict(replace=1), dict(dynamic=1), dict(beyond=1), dict(accumulating=["x"]), dict(updates=[])):
        forged = dict(good, update_only=dict(good["update_only"], **mut))
        assert ac.rollup_asset("L2", {"Idem.pattern": forged})["Idem"]["checks"][0]["v"] == ND, mut
    assert ac.rollup_asset("L2", {"Idem.pattern": dict(good, update_only=None)})["Idem"]["checks"][0]["v"] == ND
    assert ac.update_only_na_problem("Idem.pattern", dict(good, update_only=None)) and ac.update_only_na_problem("Build.target", good) is None
