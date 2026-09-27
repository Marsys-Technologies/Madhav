"""test_w2_3_deeper_detectors.py — Nikaṣa wave 2, packet W2-3: deeper detectors.

One section per register row (R242, R20 with R240, R241, R21, R23). Every test drives the REAL census
code path — a writer tree on disk read by the real `idem_scan`, the real `measure()` with only the
database answered by a stub (W2-1's `_stub_layer` harness, imported), the real `emit_gaps` on a ledger
copy — or, in the `live_` tests, the real read-only database and the real writer sources. No test here
greps source text.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_w2_3_deeper_detectors.py -v
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402

LIVE = w1.LIVE


# ─────────────────────────── R242: target_owners() read once per measure() ───────────────────────────

def _target_less_layer(monkeypatch, ctrl, owners_map):
    """Three writer-backed data assets with no target_table, each reaching Build.target's ownership
    branch (one table in its count_sql). Returns the census and the number of target_owners() reads."""
    reg = {"bg_a": w1._reg_row("bg_a", None, count_sql="SELECT count(*) FROM t_main"),
           "bg_b": w1._reg_row("bg_b", None, count_sql="SELECT count(*) FROM chart_facts"),
           "bg_c": w1._reg_row("bg_c", None, count_sql="SELECT count(*) FROM chart_facts")}
    w1._stub_layer(monkeypatch, ctrl, reg)
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_main": 7, "chart_facts": 3}))
    calls = []

    def owners():
        calls.append(1)
        return dict(owners_map)
    monkeypatch.setattr(ac, "target_owners", owners, raising=False)
    return ac.measure("L0"), calls


def test_r242_the_ownership_map_is_read_once_per_measure_and_the_verdicts_are_unchanged(monkeypatch, tmp_path):
    """Three assets need the registry-wide ownership map; it is read ONCE. The verdicts are exactly the
    per-asset grading of that map (bg_a's table has no declaring owner -> FAIL; bg_b / bg_c write a
    partition of chart_facts, declared by ga_positions -> PASS). Fails without the fix: 3 reads (the
    `setdefault` argument was evaluated on every call)."""
    c, calls = _target_less_layer(monkeypatch, tmp_path, {"chart_facts": ["ga_positions"]})
    assert len(calls) == 1, calls
    got = {a: (w1._m(c, a, "Build.target")["v"], w1._m(c, a, "Build.target")["measured"]) for a in ("bg_a", "bg_b", "bg_c")}
    expect = {a: (lambda g: (g["v"], g["measured"]))(ac._grade_target_less(
        dict(asset_id=a, count_sql=f"SELECT count(*) FROM {t}"), lambda: {"chart_facts": ["ga_positions"]}))
        for a, t in (("bg_a", "t_main"), ("bg_b", "chart_facts"), ("bg_c", "chart_facts"))}
    assert got == expect, (got, expect)
    assert got["bg_a"][0] == ac.FAIL and got["bg_b"][0] == got["bg_c"][0] == ac.PASS, got


def test_r242_an_unreadable_map_is_not_cached_as_empty(monkeypatch, tmp_path):
    """A read that raises is not cached as an empty map (which would turn the next asset's partition
    PASS into a false FAIL): each asset that needs it reads ERRORED."""
    reg = {"bg_b": w1._reg_row("bg_b", None, count_sql="SELECT count(*) FROM chart_facts"),
           "bg_c": w1._reg_row("bg_c", None, count_sql="SELECT count(*) FROM chart_facts")}
    w1._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"chart_facts": 3}))

    def boom():
        raise ac.Unknown("relation gone")
    monkeypatch.setattr(ac, "target_owners", boom, raising=False)
    c = ac.measure("L0")
    assert {w1._m(c, a, "Build.target")["v"] for a in ("bg_b", "bg_c")} == {ac.ERRORED}


# ─────────── R20 (+ R240): Idem.pattern follows the writer's delegation into the seeder ───────────

_FRAMEWORK = {
    "pipeline/__init__.py": "",
    "pipeline/orchestrator/__init__.py": "",
    "pipeline/orchestrator/writers/__init__.py": '"""framework"""\nclass WriterBase: pass\ndef register(x):\n    return lambda c: c\n',
}
_HDR = "from pipeline.orchestrator.writers import WriterBase, register\n"


def _sidecar(monkeypatch, tmp_path, files: dict[str, str]):
    """A python-sidecar tree on disk (framework + the given modules); the census reads it as the real one."""
    side = tmp_path / "python-sidecar"
    for rel, body in {**_FRAMEWORK, **files}.items():
        p = side / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    monkeypatch.setattr(ac, "SIDECAR", side, raising=False)
    monkeypatch.setattr(ac, "WRITERS", side / "pipeline" / "orchestrator" / "writers")
    return side


_HELPER = '''
def _delete(conn, sql, params):
    conn.execute(sql, params)
    return 1


def replace_prior_a(conn, chart_id, aya):
    return _delete(conn, "DELETE FROM public.t_a WHERE chart_id = %s AND ayanamsha_id = %s", [chart_id, aya])


def replace_prior_b(conn, chart_id, aya):
    return _delete(conn, "DELETE FROM public.t_b WHERE chart_id = %s AND ayanamsha_id = %s", [chart_id, aya])


def replace_prior_unrelated(conn):
    return _delete(conn, "DELETE FROM public.t_c", [])
'''


def _bo_upaya_shape(calls: str) -> dict[str, str]:
    return {"bodha_writers/__init__.py": "", "bodha_writers/_idempotency.py": _HELPER,
            "pipeline/orchestrator/writers/bo_x.py": _HDR + (
                "from bodha_writers._idempotency import replace_prior_a, replace_prior_b, replace_prior_unrelated\n"
                '@register("bo_x")\nclass BoX(WriterBase):\n    def run(self, ctx):\n        conn = ctx.db_conn\n'
                '        for aya in ("lahiri",):\n' + calls +
                '        conn.execute("DELETE FROM t_rollup WHERE chart_id = %s", (1,))\n'
                '        conn.execute("INSERT INTO t_a (chart_id) VALUES (%s)", (1,))\n')}


def test_r20_a_replacement_delegated_to_a_shared_helper_passes_naming_the_helper_and_chain(monkeypatch, tmp_path):
    """bo_upaya's shape: the writer's own DELETE hits only a sibling rollup; its counted tables are replaced
    by `replace_prior_*` in bodha_writers/_idempotency.py. Followed one hop, the replacement is measured:
    PASS naming each counted table, the helper's file:line and the call chain. Fails without the fix:
    PARTIAL "DELETE FROM present but none names the asset's own table(s)"."""
    _sidecar(monkeypatch, tmp_path, _bo_upaya_shape("            replace_prior_a(conn, 1, aya)\n"
                                                    "            replace_prior_b(conn, 1, aya)\n"))
    v, notes = ac.idem_scan("bo_x", ["bo_x.py"], "delete_then_insert", ["t_a", "t_b"])
    assert v == ac.PASS, notes
    assert "t_a (bodha_writers/_idempotency.py:" in notes[0] and "t_b (bodha_writers/_idempotency.py:" in notes[0], notes
    assert "via bo_x.py → bodha_writers/_idempotency.py:replace_prior_a" in notes[0], notes


def test_r20_a_helper_module_is_not_credited_for_functions_the_writer_never_calls(monkeypatch, tmp_path):
    """Control: the same helper module holds DELETEs of t_a/t_b, but this writer calls only the unrelated
    one. Only what the rebuild REACHES counts: the writer inserts into t_a and nothing it runs deletes
    it, so the rebuild accretes — FAIL, never a PASS borrowed from an uncalled function."""
    _sidecar(monkeypatch, tmp_path, _bo_upaya_shape("            replace_prior_unrelated(conn)\n"))
    v, notes = ac.idem_scan("bo_x", ["bo_x.py"], "delete_then_insert", ["t_a", "t_b"])
    assert v == ac.FAIL and "plain INSERT into the asset's own table(s)" in notes[0] and "t_a (bo_x.py:" in notes[0], notes


def _l0_writer(body: str) -> dict[str, str]:
    return {"brahmagyan/__init__.py": "",
            "brahmagyan/l0_x.py": ('def seed_x(conn, build_id=None):\n'
                                   '    conn.execute("""INSERT INTO t_own (k, v) VALUES (%s, %s)\n'
                                   '        ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v""", (1, 2))\n'),
            "pipeline/orchestrator/writers/bg_x.py": _HDR + "from brahmagyan.l0_x import seed_x\n"
                                                      '@register("bg_x")\nclass BgX(WriterBase):\n'
                                                      "    def run(self, ctx):\n" + body}


@pytest.mark.parametrize("body, verdict, text", [
    ("        return seed_x(ctx.db_conn, ctx.build_id)\n", ac.PASS,
     "INSERT … ON CONFLICT into the asset's own table(s) (upsert): t_own (brahmagyan/l0_x.py:"),     # the seeder's upsert
    ('        ctx.db_conn.execute("INSERT INTO t_other (k) VALUES (1) ON CONFLICT DO NOTHING")\n'
     '        ctx.db_conn.execute("INSERT INTO t_own (k, v) VALUES (1, 2)")\n', ac.FAIL,
     "plain INSERT into the asset's own table(s)"),                        # ON CONFLICT on a SIBLING table only
])
def test_r20_an_upsert_layer_passes_only_on_an_on_conflict_into_its_own_table(monkeypatch, tmp_path, body, verdict, text):
    """L0 (upsert convention). Case 1: the writer delegates to a seeder whose INSERT … ON CONFLICT targets the
    asset's table — PASS, measured in the seeder (fails without the fix: PARTIAL "likely delegates to a
    seeder"). Case 2: the writer's only ON CONFLICT is on another table and its own table gets a plain
    INSERT — FAIL (fails without the fix: PASS "ON CONFLICT present in the writer" — text anywhere)."""
    _sidecar(monkeypatch, tmp_path, _l0_writer(body))
    v, notes = ac.idem_scan("bg_x", ["bg_x.py"], "upsert", ["t_own"])
    assert v == verdict and text in notes[0], (v, notes)


def _ga_chain(deep: bool) -> dict[str, str]:
    idem = ("from ga_writers.deep import really_delete\n"
            "def replace_prior_facts(conn, rows):\n    return really_delete(conn)\n") if deep else \
           ('def replace_prior_facts(conn, rows):\n'
            '    conn.execute("DELETE FROM chart_facts WHERE chart_id = %s AND fact_category = ANY(%s)", (1, []))\n')
    return {"ga_writers/__init__.py": "",
            "ga_writers/deep.py": 'def really_delete(conn):\n    conn.execute("DELETE FROM chart_facts WHERE chart_id = %s", (1,))\n',
            "ga_writers/_idempotency.py": idem,
            "ga_writers/ga_x_writer.py": ("from ga_writers._idempotency import replace_prior_facts\n"
                                          "def build_x(chart_id, conn):\n    rows = []\n"
                                          "    replace_prior_facts(conn, rows)\n"
                                          '    conn.execute("INSERT INTO chart_facts (chart_id) VALUES (%s)", (chart_id,))\n'),
            "pipeline/orchestrator/writers/ga_x.py": _HDR + '@register("ga_x")\nclass GaX(WriterBase):\n'
                                                     "    def run(self, ctx):\n"
                                                     "        from ga_writers.ga_x_writer import build_x\n"
                                                     "        return build_x(ctx.config['chart_id'], ctx.db_conn)\n"}


def test_r20_the_l1_adapter_chain_is_followed_two_hops(monkeypatch, tmp_path):
    """The L1 shape: writers/ga_x.py (adapter, function-level import) → ga_writers/ga_x_writer.build_x (hop 1)
    → ga_writers/_idempotency.replace_prior_facts (hop 2), which deletes chart_facts. PASS naming the
    two-hop chain. Fails without the fix: PARTIAL "no idempotency pattern … likely delegates"."""
    _sidecar(monkeypatch, tmp_path, _ga_chain(deep=False))
    v, notes = ac.idem_scan("ga_x", ["ga_x.py"], "delete_then_insert", ["chart_facts"])
    assert v == ac.PASS, notes
    assert "chart_facts (ga_writers/_idempotency.py:" in notes[0] and \
        "via ga_x.py → ga_writers/ga_x_writer.py:build_x → ga_writers/_idempotency.py:replace_prior_facts" in notes[0], notes


def test_r20_a_replacement_deeper_than_the_hop_limit_is_partial_naming_the_chain_never_guessed(monkeypatch, tmp_path):
    """The same chain with the DELETE one module further (hop 3): not followed, so not measured — PARTIAL
    naming the cut chain; and the writer's INSERT is NOT graded 'accretes' either (the cut chain may hold
    the replacement). Fails without the fix: the text never named a chain ("likely delegates")."""
    _sidecar(monkeypatch, tmp_path, _ga_chain(deep=True))
    v, notes = ac.idem_scan("ga_x", ["ga_x.py"], "delete_then_insert", ["chart_facts"])
    assert v == ac.PARTIAL, notes
    assert f"delegation deeper than {ac.IDEM_DELEGATION_HOPS} hop(s), not followed: ga_x.py → " \
           "ga_writers/ga_x_writer.py:build_x → ga_writers/_idempotency.py:replace_prior_facts → " \
           "ga_writers/deep.py:really_delete" in notes[0], notes


_PAIR = _HDR + '''
@register("bo_p")
class BoP(WriterBase):
    def run(self, ctx):
        ctx.db_conn.execute("DELETE FROM t_s WHERE chart_id = %s", (1,))
        ctx.db_conn.execute("INSERT INTO t_s (chart_id) VALUES (%s)", (1,))


@register("bo_q")
class BoQ(WriterBase):
    def run(self, ctx):
        ctx.db_conn.execute("UPDATE t_s SET rank = 1 WHERE chart_id = %s", (1,))
'''


def test_r20_the_scan_starts_at_the_registered_class_not_its_whole_module(monkeypatch, tmp_path):
    """bo_laksana.py registers bo_laksana (delete-then-insert of bodha_msr_signals) AND bo_laksana_rerank
    (UPDATE-only on the same table). The rerank writer must not inherit its sibling's replacement: bo_q
    reads PARTIAL "only UPDATEd in place", bo_p PASS. Fails without the fix: bo_q PASSed on the module's
    DELETE FROM t_s, which it never runs."""
    _sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/bo_pair.py": _PAIR})
    vp, np_ = ac.idem_scan("bo_p", ["bo_pair.py"], "delete_then_insert", ["t_s"])
    vq, nq = ac.idem_scan("bo_q", ["bo_pair.py"], "delete_then_insert", ["t_s"])
    assert vp == ac.PASS, np_
    assert vq == ac.PARTIAL and "only UPDATEd in place: t_s (bo_pair.py:" in nq[0], nq


_GOCHARA = _HDR + '''
TABLE = "t_win_v2"


@register("ka_g")
class KaG(WriterBase):
    def run(self, ctx):
        ctx.db_conn.execute(f"DELETE FROM {TABLE} WHERE chart_id = %s", (1,))
        ctx.db_conn.execute(f"INSERT INTO {TABLE} (chart_id) VALUES (%s)", (1,))
'''


def test_r20_r240_a_registry_writer_table_mismatch_is_named_never_laundered_into_a_pass(monkeypatch, tmp_path):
    """ka_gochara's shape (R240 / W2-1 F8): the registry declares t_win; the writer replaces only t_win_v2
    (a module constant). Resolving the constant must not launder the mismatch: PARTIAL with the explicit
    registry/writer reason naming both tables. Control: were the registry re-pointed to t_win_v2, the same
    writer PASSes on true grounds. Fails without the fix: the reason was the generic "none names the
    asset's own table(s) … it may delegate"."""
    _sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/ka_g.py": _GOCHARA})
    v, notes = ac.idem_scan("ka_g", ["ka_g.py"], "delete_then_insert", ["t_win"])
    assert v == ac.PARTIAL, notes
    assert "registry/writer table mismatch (R240" in notes[0] and \
        "the registry declares t_win, the writer replaces t_win_v2" in notes[0], notes
    v2, notes2 = ac.idem_scan("ka_g", ["ka_g.py"], "delete_then_insert", ["t_win_v2"])
    assert v2 == ac.PASS and "t_win_v2 (ka_g.py:" in notes2[0], notes2


@pytest.mark.parametrize("extra, verdict, text", [
    ("", ac.FAIL, "upsert into the asset's own table(s) with no delete of them anywhere in the resolved scope"),
    ('        ctx.db_conn.execute(f"DELETE FROM {self.tbl} WHERE chart_id = %s", (1,))\n', ac.PARTIAL,
     "a DELETE/INSERT whose table the scan cannot name: ga_u.py:"),
])
def test_r20_an_own_table_upsert_where_delete_then_insert_is_required_fails_only_on_a_fully_read_scope(
        monkeypatch, tmp_path, extra, verdict, text):
    """§N.3 L1+: an upsert alone lets rows a rebuild no longer produces survive it. On a fully-read scope
    that is a measured FAIL; with a DELETE whose table the scan cannot name, it stays PARTIAL naming the
    unresolved statement (that DELETE may be the replacement). Fails without the fix: both read PARTIAL
    "ON CONFLICT where the layer convention is delete-then-insert"."""
    _sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/ga_u.py": _HDR + (
        '@register("ga_u")\nclass GaU(WriterBase):\n    def run(self, ctx):\n' + extra +
        '        ctx.db_conn.execute("INSERT INTO t_u (k) VALUES (1) ON CONFLICT (k) DO UPDATE SET k = 1")\n')})
    v, notes = ac.idem_scan("ga_u", ["ga_u.py"], "delete_then_insert", ["t_u"])
    assert v == verdict and text in notes[0], (v, notes)


def test_r20_an_insert_and_its_on_conflict_split_across_two_strings_is_an_upsert_not_an_accretion(monkeypatch, tmp_path):
    """Control against a manufactured FAIL: `sql = "INSERT INTO t_own …"; sql += " ON CONFLICT …"` in one
    function is an upsert — PASS on an upsert layer, never 'plain INSERT … accretes'."""
    _sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/bg_s.py": _HDR + (
        '@register("bg_s")\nclass BgS(WriterBase):\n    def run(self, ctx):\n'
        '        sql = "INSERT INTO t_own (k) VALUES (%s)"\n'
        '        sql += " ON CONFLICT (k) DO NOTHING"\n'
        '        ctx.db_conn.execute(sql, (1,))\n')})
    v, notes = ac.idem_scan("bg_s", ["bg_s.py"], "upsert", ["t_own"])
    assert v == ac.PASS and "t_own (bg_s.py:" in notes[0], notes


def test_r20_a_writer_that_writes_nothing_is_partial_with_the_reason_never_the_closable_na(monkeypatch, tmp_path):
    """mi_seva / bo_samvada's shape: the registered class writes no row anywhere (a module constant holding
    DDL it never runs is not in its scope). §N.8: a static scan cannot prove a write's absence, so this is
    PARTIAL with the reason, never N/A. Fails without the fix: the text was "likely delegates"."""
    _sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/mi_s.py": _HDR + (
        '_DDL = "CREATE OR REPLACE VIEW t_view AS SELECT 1"\n'
        '@register("mi_s")\nclass MiS(WriterBase):\n    def run(self, ctx):\n        return None\n')})
    v, notes = ac.idem_scan("mi_s", ["mi_s.py"], "delete_then_insert", ["t_view"])
    assert v == ac.PARTIAL and "no write to the asset's own table(s) ['t_view']" in notes[0] \
        and "not graded N/A" in notes[0], notes


def test_r20_end_to_end_an_open_gap_closes_on_the_followed_replacement_and_not_on_the_mismatch(monkeypatch, tmp_path):
    """measure() + emit_gaps() on a ledger copy (L2): bo_x (replacement delegated to the helper) and bo_g (the
    R240 mismatch shape) each have an OPEN Idem.pattern gap. Exactly one closes — bo_x's, quoting the
    helper; bo_g's stays OPEN. Fails without the fix: 0 closed (bo_x read PARTIAL)."""
    files = _bo_upaya_shape("            replace_prior_a(conn, 1, aya)\n            replace_prior_b(conn, 1, aya)\n")
    files["pipeline/orchestrator/writers/bo_g.py"] = _GOCHARA.replace('"ka_g"', '"bo_g"').replace("KaG", "BoG")
    _sidecar(monkeypatch, tmp_path, files)
    reg = {"bo_x": w1._reg_row("bo_x", "t_a", count_sql="SELECT (SELECT count(*) FROM t_a) + (SELECT count(*) FROM t_b)"),
           "bo_g": w1._reg_row("bo_g", "t_win")}
    w1._stub_layer(monkeypatch, tmp_path, reg, writers={"bo_x": ["bo_x.py"], "bo_g": ["bo_g.py"]})
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_a": 3, "t_b": 2, "t_win": 1}))
    for aid in reg:
        w1._open_gap(tmp_path, aid, "Idem.pattern")
    c = ac.measure("L2")
    assert w1._m(c, "bo_x", "Idem.pattern")["v"] == ac.PASS and w1._m(c, "bo_g", "Idem.pattern")["v"] == ac.PARTIAL
    assert ac.emit_gaps(c)[2] == 1
    rows = [json.loads(x) for x in (tmp_path / "asset_gaps.jsonl").read_text().splitlines() if x.strip()]
    closed = [r for r in rows if r["state"] == "CLOSED"]
    assert [r["gap_id"] for r in closed] == ["bo_x-Idem.pattern"] and "bodha_writers/_idempotency.py" in closed[0]["what"]


# Real writer sources (no database): the targets are the registry's, read live 2026-09-27.
_REAL_TARGETS = {
    "bo_upaya": ["bodha_rm_resonances", "bodha_rm_resonances", "bodha_rm_remedy_prescriptions"],
    "ka_gochara": ["kala_gochara_windows", "kala_gochara_windows"],
    "bo_laksana_rerank": ["bodha_msr_signals", "bodha_msr_signals"],
    "bo_samvada": ["vw_chart_digest"],
    "bo_bimba": ["bodha_cgm_nodes", "bodha_cgm_nodes"],
    "bo_pramana_mapa": ["synthesis_quality_scorecard", "synthesis_quality_scorecard"],
    "ga_positions": ["chart_facts", "chart_facts"],
    "bg_rules": ["sutravali_rules", "sutravali_rules"],
}


def test_r20_the_real_writers_resolve_as_hand_verified():
    """The three W2-2 C-KSHETRA acceptance items on the real sources, plus R127's three L2 delegating writers
    and one L1 adapter / one L0 seeder: bo_upaya PASS through bodha_writers/_idempotency.py (both counted
    tables); ka_gochara PARTIAL naming the v2 mismatch (R240); ka_kshetra still FAIL; bo_bimba and
    bo_pramana_mapa PASS through their replace_prior_* helpers; bo_samvada PARTIAL (its writer runs no DDL);
    bo_laksana_rerank PARTIAL (UPDATE-only); ga_positions PASS two hops down; bg_rules PASS in its seeder."""
    ids = {**ac.registered_ids("bo_"), **ac.registered_ids("ka_"), **ac.registered_ids("ga_"), **ac.registered_ids("bg_")}
    conv = {"bo": "delete_then_insert", "ka": "delete_then_insert", "ga": "delete_then_insert", "bg": "upsert"}

    def scan(aid, targets=None):
        return ac.idem_scan(aid, ids[aid], conv[aid[:2]], targets if targets is not None else _REAL_TARGETS[aid])
    v, n = scan("bo_upaya")
    assert v == ac.PASS and "bodha_rm_resonances (bodha_writers/_idempotency.py:" in n[0] \
        and "bodha_rm_remedy_prescriptions (bodha_writers/_idempotency.py:" in n[0], n
    v, n = scan("ka_gochara")
    assert v == ac.PARTIAL and "the registry declares kala_gochara_windows, the writer replaces kala_gochara_windows_v2" in n[0], n
    v, n = scan("ka_kshetra", ["kala_field"])
    assert v == ac.FAIL and "services/ka_kshetra/writer.py:" in n[0], n
    for aid in ("bo_bimba", "bo_pramana_mapa"):
        v, n = scan(aid)
        assert v == ac.PASS and "(bodha_writers/_idempotency.py:" in n[0], (aid, n)
    assert scan("bo_samvada")[0] == ac.PARTIAL and scan("bo_laksana_rerank")[0] == ac.PARTIAL
    v, n = scan("ga_positions")
    assert v == ac.PASS and "→ ga_writers/_idempotency.py:replace_prior_chart_facts" in n[0], n
    v, n = scan("bg_rules")
    assert v == ac.PASS and "sutravali_rules (brahmagyan/l0_rules.py:" in n[0], n


@LIVE
def test_live_r20_no_idem_verdict_is_na_unless_the_registry_says_no_writer_and_every_pass_names_an_own_table():
    """Live, read-only, all six layers: idem_scan never emits N/A itself (N/A comes only from
    `_no_writer_scanned` with has_writer=false), and every PASS names one of the asset's own tables."""
    for layer, cfg in ac.LAYERS.items():
        reg, _ = ac.registry(layer)
        regd = ac.registered_ids(cfg["prefix"])
        for aid, r in reg.items():
            targets = [r["target_table"]] + ac._count_tables(r["count_sql"])
            res = ac._measure_idem(aid, regd.get(aid, []), cfg["idem"], r["has_writer"], targets)
            if res["v"] == ac.NA:
                assert not r["has_writer"], (aid, res)
            if res["v"] == ac.PASS:
                assert any(f"{t} (" in res["measured"] for t in targets if t), (aid, res)


# ─────────── R241: the refusal-guard blind spots W2-2 disclosed (RC-1 a–d), closed on the resolved scope ───────────

_HOLD_METHODS = '''
    @staticmethod
    def _populated(conn):
        return conn.execute("SELECT EXISTS (SELECT 1 FROM t_h WHERE chart_id = %s)", (1,)).fetchone()[0]

    @staticmethod
    def _count(conn):
        return conn.execute("SELECT count(*) FROM t_h WHERE chart_id = %s", (1,)).fetchone()[0]

    @staticmethod
    def _upstream(conn):
        return conn.execute("SELECT count(*) FROM t_input WHERE chart_id = %s", (1,)).fetchone()[0]

    @staticmethod
    def _already_this_build(conn, build_id):
        return conn.execute("SELECT count(*) FROM t_h WHERE chart_id = %s AND build_id_uuid = %s", (1, build_id)).fetchone()[0]

    @staticmethod
    def _unchanged(conn):
        return True

    @staticmethod
    def _delete_prior(conn):
        conn.execute("DELETE FROM t_h WHERE chart_id = %s", (1,))
'''
_THEN_REPLACE = "        self._delete_prior(conn)\n        conn.execute('INSERT INTO t_h (chart_id) VALUES (1)')\n"


def _hold_writer(run_body: str) -> dict[str, str]:
    return {"pipeline/orchestrator/writers/ka_h.py": _HDR + '@register("ka_h")\nclass KaH(WriterBase):\n'
            "    def run(self, ctx):\n        conn = ctx.db_conn\n" + run_body + _HOLD_METHODS}


_HOLDS = {
    # RC-1(a): a hold that RETURNS instead of raising
    "early_return": ("        if self._populated(conn):\n            return None\n" + _THEN_REPLACE, "return"),
    # RC-1(b): the count(*) probe form, `n > 0`
    "count_probe": ("        n = self._count(conn)\n        if n > 0:\n            raise RuntimeError('held')\n" + _THEN_REPLACE,
                    "raise RuntimeError"),
    # RC-1(d): walrus polarity
    "walrus": ("        if (n := self._count(conn)) > 0:\n            raise RuntimeError('held')\n" + _THEN_REPLACE,
               "raise RuntimeError"),
    # RC-1(d): a negated test — the replacement runs only in the `not populated` branch, the else raises
    "negated": ("        if not self._populated(conn):\n            self._delete_prior(conn)\n"
                "        else:\n            raise RuntimeError('held')\n", "raise RuntimeError"),
    # RC-1(a): a loop that skips populated tables with `continue`
    "continue": ("        for t in ('t_h',):\n            if self._populated(conn):\n                continue\n"
                 "            self._delete_prior(conn)\n", "continue"),
    # RC-1(a): a skip with no raise/return — the delete sits only in the empty branch
    "skip_no_raise": ("        if self._populated(conn):\n            print('kept')\n        else:\n"
                      "            self._delete_prior(conn)\n", "the delete runs only in the output-empty branch"),
}


@pytest.mark.parametrize("case", sorted(_HOLDS))
def test_r241_every_disclosed_hold_shape_reads_fail_naming_the_hold(monkeypatch, tmp_path, case):
    """Each shape W2-2_C_KSHETRA_REVIEW §7 RC-1 named as a blind spot of C-KSHETRA's guard (which recognised
    only `if <EXISTS probe result>: raise` in one file). Each holds the replacement on a populated chart,
    so each reads FAIL naming the hold. Fails without the fix: every one PASSed on its reachable DELETE."""
    body, what = _HOLDS[case]
    _sidecar(monkeypatch, tmp_path, _hold_writer(body))
    v, notes = ac.idem_scan("ka_h", ["ka_h.py"], "delete_then_insert", ["t_h"])
    assert v == ac.FAIL and "rebuild refused when target is populated: ka_h.py:" in notes[0] and what in notes[0], (case, notes)


def test_r241_a_guard_in_a_delegated_module_is_seen(monkeypatch, tmp_path):
    """RC-1(c): the probe and the raise live in a helper module the writer calls (hop 1), which then
    deletes. FAIL naming the helper and the chain. Fails without the fix: the guard was looked for only
    in the writer's own file, so the helper's reachable DELETE PASSed."""
    _sidecar(monkeypatch, tmp_path, {
        "services/__init__.py": "", "services/h/__init__.py": "",
        "services/h/prep.py": ('def _probe(conn):\n'
                               '    return conn.execute("SELECT EXISTS (SELECT 1 FROM t_h WHERE chart_id = %s)", (1,)).fetchone()[0]\n\n\n'
                               'def prepare_replace(conn):\n    if _probe(conn):\n        raise RuntimeError("held")\n'
                               '    conn.execute("DELETE FROM t_h WHERE chart_id = %s", (1,))\n'),
        "pipeline/orchestrator/writers/ka_h.py": _HDR + "from services.h.prep import prepare_replace\n"
                                                 '@register("ka_h")\nclass KaH(WriterBase):\n    def run(self, ctx):\n'
                                                 "        prepare_replace(ctx.db_conn)\n"
                                                 "        ctx.db_conn.execute('INSERT INTO t_h (chart_id) VALUES (1)')\n"})
    v, notes = ac.idem_scan("ka_h", ["ka_h.py"], "delete_then_insert", ["t_h"])
    assert v == ac.FAIL and "services/h/prep.py:" in notes[0] and "reached via ka_h.py → services/h/prep.py:prepare_replace" in notes[0], notes


@pytest.mark.parametrize("case, body", [
    # mi_jivanaghatana: raises when its UPSTREAM input exists but it built nothing — not a refusal
    ("upstream_probe", "        if self._upstream(conn) > 0:\n            raise RuntimeError('input present, nothing built')\n" + _THEN_REPLACE),
    # ga_vargas: skips what THIS build already wrote (a resume check, a new build has a new id)
    ("this_build_resume", "        for v in ('D1',):\n            if self._already_this_build(conn, ctx.build_id):\n"
                          "                continue\n            self._delete_prior(conn)\n"),
    # an EMPTY-polarity raise (C-KSHETRA's own control)
    ("empty_polarity", "        if self._count(conn) == 0:\n            raise RuntimeError('nothing to replace yet')\n" + _THEN_REPLACE),
    # the legitimate incremental skip: populated AND inputs unchanged (deliberately not a hold; see report)
    ("incremental_skip", "        if self._populated(conn) and self._unchanged(conn):\n            return None\n" + _THEN_REPLACE),
])
def test_r241_controls_that_are_not_holds_still_pass(monkeypatch, tmp_path, case, body):
    """The guard must not manufacture a FAIL: an upstream probe, a same-build resume probe, an empty-polarity
    raise and a populated-AND-unchanged incremental skip each replace on a rebuild — PASS."""
    _sidecar(monkeypatch, tmp_path, _hold_writer(body))
    v, notes = ac.idem_scan("ka_h", ["ka_h.py"], "delete_then_insert", ["t_h"])
    assert v == ac.PASS, (case, notes)


def test_r241_an_open_gap_does_not_close_on_an_early_return_hold(monkeypatch, tmp_path):
    """measure() + emit_gaps() on a ledger copy: the early-return hold's OPEN Idem.pattern gap stays OPEN.
    Fails without the fix: it CLOSED on the reachable DELETE."""
    _sidecar(monkeypatch, tmp_path, _hold_writer(_HOLDS["early_return"][0]))
    reg = {"ka_h": w1._reg_row("ka_h", "t_h")}
    w1._stub_layer(monkeypatch, tmp_path, reg, writers={"ka_h": ["ka_h.py"]})
    w1._open_gap(tmp_path, "ka_h", "Idem.pattern")
    c = ac.measure("L3")
    assert w1._m(c, "ka_h", "Idem.pattern")["v"] == ac.FAIL
    assert ac.emit_gaps(c)[2] == 0


def test_r241_the_real_writers_near_the_new_shapes_resolve_as_hand_verified():
    """Real sources (targets read live 2026-09-27): ka_kshetra still FAILs on its KshetraReplacementHeld raise;
    mi_jivanaghatana's `count_chart_lel_events` probe counts life_events (its input), and ga_vargas's
    `_check_already_written` is pinned to the current build — neither is a hold, both PASS."""
    ids = {**ac.registered_ids("ka_"), **ac.registered_ids("mi_"), **ac.registered_ids("ga_")}
    v, n = ac.idem_scan("ka_kshetra", ids["ka_kshetra"], "delete_then_insert", ["kala_field"])
    assert v == ac.FAIL and "services/ka_kshetra/writer.py:545 (raise KshetraReplacementHeld" in n[0], n
    v, n = ac.idem_scan("mi_jivanaghatana", ids["mi_jivanaghatana"], "delete_then_insert", ["mimamsa_event_provenance"] * 2)
    assert v == ac.PASS, n
    v, n = ac.idem_scan("ga_vargas", ids["ga_vargas"], "delete_then_insert", ["chart_divisionals"] * 2)
    assert v == ac.PASS and "chart_divisionals" in n[0], n


# ─────────── R21: blocking radius per asset from the DAG, attached to every Build gap as its severity ───────────

_DAG = {"bg_root": [], "bg_mid": ["bg_root"], "bg_leaf": ["bg_mid"], "ga_x": ["bg_root", "bg_gone"],
        "bo_c1": ["bo_c2"], "bo_c2": ["bo_c1", "bg_leaf"]}


def test_r21_the_radius_is_the_count_of_active_assets_that_transitively_depend_on_it():
    """bg_root is depended on by bg_mid (direct), bg_leaf (through bg_mid), ga_x (another layer, direct),
    and the bo_c1<->bo_c2 cycle (through bg_leaf): 5 transitive, 2 direct. A cycle counts each member once
    and never the asset itself; `bg_gone` (not active) is no edge. severity_weight = 1 + transitive."""
    r = ac.blocking_radius(_DAG)
    assert r["bg_root"] == dict(transitive=5, direct=2, severity_weight=6), r["bg_root"]
    assert r["bg_leaf"] == dict(transitive=2, direct=1, severity_weight=3), r["bg_leaf"]
    assert r["bo_c1"] == dict(transitive=1, direct=1, severity_weight=2) and r["bo_c2"]["transitive"] == 1, r
    assert r["ga_x"] == dict(transitive=0, direct=0, severity_weight=1), r["ga_x"]
    assert "bg_gone" not in r


# bg_root <- bg_mid <- bg_leaf, and ga_x (another layer) <- bg_root: root 3 transitive, leaf 0.
_DAG_E2E = {"bg_root": [], "bg_mid": ["bg_root"], "bg_leaf": ["bg_mid"], "ga_x": ["bg_root"]}


def _radius_layer(monkeypatch, ctrl, graph):
    reg = {a: w1._reg_row(a, "t_main", count_sql="SELECT count(*) FROM t_main") for a in ("bg_root", "bg_mid", "bg_leaf")}
    w1._stub_layer(monkeypatch, ctrl, reg)
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_main": 0}))      # live=0: Build.completion FAILs for all three
    monkeypatch.setattr(ac, "dependency_graph", graph, raising=False)
    return ac.measure("L0")


def test_r21_a_root_and_a_leaf_with_the_same_verdict_open_differently_weighted_build_gaps(monkeypatch, tmp_path):
    """measure() + emit_gaps() on a ledger copy: bg_root and bg_leaf both FAIL Build.completion (same verdict,
    same measured shape). Their OPEN rows carry blocking_radius 3 / severity_weight 4 and 0 / 1. A non-Build
    gap carries no radius. Fails without the fix: no row carried a blocking radius."""
    c = _radius_layer(monkeypatch, tmp_path, lambda: dict(_DAG_E2E))
    assert {w1._m(c, a, "Build.completion")["v"] for a in ("bg_root", "bg_leaf")} == {ac.FAIL}
    ac.emit_gaps(c)
    rows = {r["gap_id"]: r for r in (json.loads(x) for x in (tmp_path / "asset_gaps.jsonl").read_text().splitlines() if x.strip())}
    root, leaf = rows["bg_root-Build.completion"], rows["bg_leaf-Build.completion"]
    assert (root["blocking_radius"], root["severity_weight"]) == (3, 4), root
    assert (leaf["blocking_radius"], leaf["severity_weight"]) == (0, 1), leaf
    assert "blocking_radius" not in rows["bg_root-Carr.detector"]


def test_r21_an_unreadable_dag_is_unmeasured_never_zero(monkeypatch, tmp_path):
    """The dependency read fails: the census still completes, every Build gap carries blocking_radius null
    with the reason — never 0 (which would read as 'an isolated leaf, lowest priority')."""
    def boom():
        raise ac.Unknown("relation asset_registry gone")
    c = _radius_layer(monkeypatch, tmp_path, boom)
    ac.emit_gaps(c)
    row = next(json.loads(x) for x in (tmp_path / "asset_gaps.jsonl").read_text().splitlines()
               if '"bg_root-Build.completion"' in x)
    assert row["blocking_radius"] is None and row["severity_weight"] is None, row
    assert "unmeasured: the dependency read failed" in row["blocking_radius_note"], row


def test_r21_a_closing_or_reopening_build_row_carries_the_radius_measured_now(monkeypatch, tmp_path):
    """Transition rows carry the radius THIS run measured (the DAG moves; a prior row's figure is not carried):
    a CLOSED Build.count_integrity row and a RE-OPENED Build.completion row both read bg_root's 3."""
    c = _radius_layer(monkeypatch, tmp_path, lambda: dict(_DAG_E2E))
    w1._open_gap(tmp_path, "bg_root", "Build.count_integrity")
    (tmp_path / "asset_gaps.jsonl").open("a").write(json.dumps(dict(
        asset="bg_root", gap_id="bg_root-Build.completion", kind="gap", criterion="Build.completion", what="w",
        change="", detector="d", owner="o", gate="g", state="CLOSED", ts="t0", blocking_radius=99)) + "\n")
    assert w1._m(c, "bg_root", "Build.count_integrity")["v"] == ac.PASS
    added, _, closed, reopened = ac.emit_gaps(c)
    assert closed >= 1 and reopened == 1
    rows = [json.loads(x) for x in (tmp_path / "asset_gaps.jsonl").read_text().splitlines() if x.strip()]
    last = {r["gap_id"]: r for r in rows}
    assert last["bg_root-Build.count_integrity"]["state"] == "CLOSED" and last["bg_root-Build.count_integrity"]["blocking_radius"] == 3
    assert last["bg_root-Build.completion"]["state"] == "OPEN" and last["bg_root-Build.completion"]["blocking_radius"] == 3


@LIVE
def test_live_r21_the_radius_agrees_with_an_independent_recursive_query():
    """Live, read-only: the census's radius for every active asset equals a recursive CTE over
    asset_registry.depends_on computed in SQL (a second, independent derivation of the same metric)."""
    r = ac.blocking_radius(ac.dependency_graph())
    rows = ac.psql(
        "WITH RECURSIVE act AS (SELECT asset_id, coalesce(depends_on, '{}') d FROM asset_registry "
        " WHERE is_active AND NOT coalesce(dead_flag,false)), "
        "e AS (SELECT DISTINCT unnest(d) AS dep, asset_id AS child FROM act), "
        "edge AS (SELECT e.dep, e.child FROM e JOIN act a ON a.asset_id = e.dep WHERE e.dep <> e.child), "
        "reach(root, x) AS (SELECT dep, child FROM edge UNION SELECT r.root, edge.child FROM reach r "
        " JOIN edge ON edge.dep = r.x) "
        "SELECT a.asset_id, (SELECT count(DISTINCT x) FROM reach WHERE root = a.asset_id AND x <> a.asset_id)::text "
        "FROM act a")
    sql = {a: int(n) for a, n in rows}
    assert len(sql) == len(r) and all(r[a]["transitive"] == sql[a] for a in sql), \
        [(a, r[a]["transitive"], sql[a]) for a in sql if r[a]["transitive"] != sql[a]][:5]
    assert max(v["transitive"] for v in r.values()) > 0


# ─────────── R23: field-level reachability over capability modules (width / depth), reported not graded ───────────

_REAL_CAPABILITY_SQL = getattr(ac, "capability_sql", None)


def _caps_tree(tmp_path, files: dict[str, str]) -> str:
    d = tmp_path / "caps"
    for rel, body in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return str(d)


_READS_T_R = {
    "L1_x/get_r.ts": ("import { query } from '@/lib/db/client'\n"
                      "// SELECT d FROM t_r  <- a comment, not a query\n"
                      "export const cap = { description: 'Retrieve rows from t_r for a chart.',\n"
                      "  handler: () => query(`SELECT a, b, coalesce(c, 0) AS c2 FROM t_r WHERE chart_id = $1 AND kind = $2`) }\n"),
    "L1_x/__tests__/get_r.test.ts": "query(`SELECT * FROM t_r`)\n",                       # a test is not a capability
    "L4_y/get_other.ts": "query(`SELECT o.d FROM t_other o JOIN t_r r ON r.a = o.a WHERE o.k = 'x'`)\n",
}


def _reach_measure(monkeypatch, tmp_path, caps: dict[str, str] | None, never=("e",), psql_fake=None):
    cols = ["chart_id", "a", "b", "c", "d", "e"]
    reg = {"ga_r": w1._reg_row("ga_r", "t_r", count_sql="SELECT count(*) FROM t_r WHERE chart_id = $1")}
    w1._stub_layer(monkeypatch, tmp_path, reg, tables={"t_r": (cols, [])})
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=3, full=[], never=list(never), note=""))
    if caps is None:
        monkeypatch.setattr(ac, "capability_sql", lambda: _REAL_CAPABILITY_SQL(str(tmp_path / "no_such_dir")), raising=False)
    else:
        root = _caps_tree(tmp_path, caps)
        monkeypatch.setattr(ac, "capability_sql", lambda: _REAL_CAPABILITY_SQL(root), raising=False)
    monkeypatch.setattr(ac, "psql", psql_fake or w1._pg_like_psql({"t_r": 3}))
    c = ac.measure("L1")
    return w1._m(c, "ga_r", "Reach.fields"), next(a for a in c["assets"] if a["asset_id"] == "ga_r").get("reach"), c


def test_r23_width_counts_the_built_columns_some_capability_selects_and_names_the_dark_ones(monkeypatch, tmp_path):
    """t_r has 6 columns, `e` never populated, so 5 are built. get_r.ts selects a, b and c (inside
    coalesce); get_other.ts joins t_r but selects only its OWN alias's column (o.d); a comment and a
    description that say "from t_r" and a __tests__ module are not capabilities reading it. Width 3/5,
    dark [chart_id, d]; a parameter-bound predicate pins no row, so depth 1.0 (upper bound). Reported, not
    graded: the verdict stays NOT_GENERIC and no gap row is emitted for it. Fails without the fix: the
    criterion read "not generic" with no measurement and no `reach`."""
    rf, reach, c = _reach_measure(monkeypatch, tmp_path, _READS_T_R)
    assert rf["v"] == ac.NOT_GENERIC and reach is not None, rf
    assert reach["exposed"] == ["a", "b", "c"] and reach["dark"] == ["chart_id", "d"], reach
    assert reach["width"] == 0.6 and reach["depth"] == 1.0 and reach["columns_built"] == 5, reach
    assert sorted(reach["modules"]) == ["L1_x/get_r.ts", "L4_y/get_other.ts"], reach
    assert "width 3/5 built column(s) (60.0%)" in rf["measured"] and "dark: ['chart_id', 'd']" in rf["measured"], rf
    ac.emit_gaps(c)
    assert "Reach.fields" not in (tmp_path / "asset_gaps.jsonl").read_text()


def test_r23_depth_is_the_share_of_rows_the_literal_pins_reach_counted_read_only(monkeypatch, tmp_path):
    """Every query that reads t_r pins rows by literal values (d = 'x'; d IN ('y','z')): depth is the
    chart's rows matching the union of the pins, counted read-only (3 of 10 -> 30%), the count scoped to
    the bound chart. Fails without the fix: no depth was measured."""
    seen = []

    def fake(sql, sep="\x1f", timeout=None):
        if "FILTER (WHERE" in sql:
            seen.append(sql)
            return [["3", "10"]]
        return w1._pg_like_psql({"t_r": 3})(sql, sep, timeout)
    caps = {"L1_x/get_r.ts": ("const description = 'Pinned rows from t_r, by d.'\n"          # prose: not a query
                              "query(`SELECT a FROM t_r WHERE d = 'x' AND chart_id = $1`)\n"
                              "query(`SELECT b FROM t_r WHERE d IN ('y', 'z') AND chart_id = $1`)\n")}
    rf, reach, _ = _reach_measure(monkeypatch, tmp_path, caps, psql_fake=fake)
    assert reach["depth"] == 0.3 and reach["exposed"] == ["a", "b"], reach
    assert len(seen) == 1 and "d::text IN ('x')" in seen[0] and "d::text IN ('y', 'z')" in seen[0] \
        and f"WHERE chart_id = '{w1.CANONICAL}'" in seen[0], seen


@pytest.mark.parametrize("q", [
    "query(`SELECT a FROM t_r WHERE d = 'x' OR d = 'y'`)\n",                             # an OR: not analysable
    "query(`SELECT a FROM t_r WHERE d = 'x'`)\nquery(`SELECT b FROM t_r WHERE chart_id = $1`)\n",       # one unpinned
])
def test_r23_depth_is_never_narrowed_by_a_predicate_it_cannot_read(monkeypatch, tmp_path, q):
    """An OR predicate, or any one unpinned query, leaves depth at its upper bound 1.0 — no count is run and
    no narrowing is invented."""
    def fake(sql, sep="\x1f", timeout=None):
        assert "FILTER (WHERE" not in sql, sql
        return w1._pg_like_psql({"t_r": 3})(sql, sep, timeout)
    _, reach, _ = _reach_measure(monkeypatch, tmp_path, {"L1_x/get_r.ts": q}, psql_fake=fake)
    assert reach["depth"] == 1.0 and "upper bound" in reach["depth_basis"], reach


def test_r23_a_run_time_column_list_makes_width_a_lower_bound(monkeypatch, tmp_path):
    """ga_yoga_firings' shape: `SELECT ${cols} FROM t_r f …` — the columns are chosen at run time. Width is
    reported as a lower bound naming the module, never as 'every column dark'."""
    rf, reach, _ = _reach_measure(monkeypatch, tmp_path, {"L1_x/get_r.ts": "query(`SELECT ${cols} FROM t_r f WHERE ${where}`)\n"})
    assert reach["width_is_lower_bound"] is True and reach["dynamic_select"] == ["L1_x/get_r.ts"], reach
    assert "≥ 0/5 built column(s)" in rf["measured"] and "a lower bound" in rf["measured"], rf


def test_r23_no_capability_reading_the_table_is_width_and_depth_zero_and_a_missing_directory_is_unmeasured(
        monkeypatch, tmp_path):
    """A scanned directory where nothing reads t_r: every built column dark, depth 0. A directory that does not
    exist: unmeasured, said so — never 'all dark' inferred from a scan that did not run."""
    _, reach, _ = _reach_measure(monkeypatch, tmp_path, {"L1_x/other.ts": "query(`SELECT a FROM t_other`)\n"})
    assert reach["width"] == 0.0 and reach["depth"] == 0.0 and reach["modules"] == [], reach
    rf, reach2, _ = _reach_measure(monkeypatch, tmp_path, None)
    assert reach2 is None and "unmeasured: no capability directory" in rf["measured"], rf


@LIVE
def test_live_r23_real_capabilities_read_as_hand_verified():
    """Live catalog + real capability modules: chart_divisionals is served whole (get_divisionals.ts
    `SELECT *`) -> width 1.0; ga_yoga_firings is selected through a run-time list (get_yoga_firings.ts
    `SELECT ${cols}`) -> lower bound flagged; mimamsa_export_log is read by no capability -> depth 0."""
    caps = ac.capability_sql()
    cat = ac.catalog(["chart_divisionals", "ga_yoga_firings", "mimamsa_export_log"])
    div = ac.field_reach("chart_divisionals", cat["cols"]["chart_divisionals"], caps)
    assert "L1_ganita/get_divisionals.ts" in div["modules"] and div["exposed"] == {c.lower() for c in cat["cols"]["chart_divisionals"]}
    yf = ac.field_reach("ga_yoga_firings", cat["cols"]["ga_yoga_firings"], caps)
    assert "L1_ganita/get_yoga_firings.ts" in yf["dynamic_select"], yf
    assert ac.field_reach("mimamsa_export_log", cat["cols"]["mimamsa_export_log"], caps)["modules"] == []
