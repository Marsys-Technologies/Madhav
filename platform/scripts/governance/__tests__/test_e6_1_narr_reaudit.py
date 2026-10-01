"""test_e6_1_narr_reaudit.py — E6.1 re-audit of the 13 Narr declarations that cited DDL (SS ruling 2026-10-01).

The 13 older `prose_fields` declarations cited a column's DDL + the census ("TEXT column a capability SELECTs"), never the
writer code. The Narr definition (SS 2026-10-01): generated prose = text the writer composes from computed values (template or
LLM) that STATES OR GRADES a computed value, counts included; verbatim loads, provenance pointers, ordinals and structural
labels are not. This file re-audits each declared column against WRITER CODE:

  * COMPOSED-NARRATION  -> the declaration is kept and its `evidence_kind: "ddl"` marker is dropped, because the evidence now cites
    the composing code (path:line) and the served read (path:line); the AST checks below prove the INSERT binds the declared
    column to the builder's output and that the builder string-composes it (helpers: `_narr_reaudit_checks.py`).
  * NOT-COMPOSED / UNCLEAR -> `prose_fields` is null (undeclared; Narr reads NO_DETECTOR), never `[]` unless the AST shows no string
    building bound to any column of the asset.

Offline: no database. Evidence: /Users/Dev/suvarna-evidence/E6.1/narr_reaudit_evidence.md.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _narr_reaudit_checks as rc  # noqa: E402
import _narr_writer_checks as nw  # noqa: E402

REPO_ROOT = HERE.parents[3]
_SC = "platform/python-sidecar/"
_WR = _SC + "pipeline/orchestrator/writers/"
_BW = _SC + "bodha_writers/"
_SV = _SC + "services/"
_L = "platform/src/lib/retrieval/registry/layers/"
_MIG = "platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql"

MSR = "bodha_msr_signals"
MSR_COLS = ["signal_headline_text", "signal_summary_text"]
# the six writers that share bodha_msr_signals: (writer, emitter module, builders the writer calls, owned-class constant)
MSR_SIX = {
    "bo_arudha": ("bo_arudha.py", "arudha_emitter", ["build_signal_rows"], "BO_ARUDHA_OWNED_SIGNAL_TYPE_CLASSES"),
    "bo_nakshatra_semantic": ("bo_nakshatra_semantic.py", "nakshatra_semantic_emitter", ["build_signal_row"],
                              "BO_NAKSHATRA_SEMANTIC_OWNED_SIGNAL_TYPE_CLASSES"),
    "bo_special_lagna": ("bo_special_lagna.py", "special_lagna_emitter", ["build_signal_row"], "BO_SPECIAL_LAGNA_OWNED_SIGNAL_TYPE_CLASSES"),
    "bo_sudarshana": ("bo_sudarshana.py", "sudarshana_emitter", ["build_signal_row"], None),
    "bo_vargottama_dhana": ("bo_vargottama_dhana.py", "vargottama_dhana_emitter", ["build_vargottama_rows", "build_dhana_axis_rows"],
                            "BO_VARGOTTAMA_DHANA_OWNED_SIGNAL_TYPE_CLASSES"),
}
# the classes each writer's rows carry (its producer_asset_id filter, expressed in the served facet); sudarshana has no owned list
# constant (it deletes by the emitter's SIGNAL_TYPE_CLASS), bo_laksana's list is the 15-class constant in the writer
MSR_CLASSES = {
    "bo_arudha": ["arudha"], "bo_nakshatra_semantic": ["nakshatra_semantic"], "bo_special_lagna": ["special_lagna"],
    "bo_sudarshana": ["sudarshana_agreement"], "bo_vargottama_dhana": ["vargottama_amplification", "dhana_axis"],
    "bo_laksana": ["yoga", "dosha", "sade_sati", "panchanga", "karaka_alignment", "tradition_specific", "parivartana", "configuration",
                   "varga_pattern", "annual", "medical", "vastu", "composite_state", "varga_ratification_divergence",
                   "bhavat_bhavam_amplifier"],
}

# (file, line, substring the line must contain): every cite the evidence text carries as `<basename>:<line>`
_QS = _L + "L2_bodha/query_signals.ts"
MSR_SERVED = [(_QS, 140, "'signal_type_class'"), (_QS, 141, "'signal_summary_text', 'signal_headline_text'"),
              (_QS, 449, "m.signal_type_class = "), (_QS, 507, "FROM bodha_msr_signals m")]

KEPT = {
    "bo_arudha": dict(table=MSR, cols=MSR_COLS, writer=_WR + "bo_arudha.py", emitter=_BW + "arudha_emitter.py", cites=MSR_SERVED + [
        (_WR + "bo_arudha.py", 163, "rows = build_signal_rows("), (_WR + "bo_arudha.py", 182, "conn.execute(_INSERT_SQL, row)"),
        (_WR + "bo_arudha.py", 189, "INSERT INTO public.bodha_msr_signals"),
        (_WR + "bo_arudha.py", 222, "%(signal_summary_text)s, %(signal_headline_text)s"),
        (_BW + "arudha_emitter.py", 139, '"signal_summary_text": summary'), (_BW + "arudha_emitter.py", 140, '"signal_headline_text": headline'),
        (_BW + "arudha_emitter.py", 242, 'summary=f"category=arudha'), (_BW + "arudha_emitter.py", 243, 'headline=f"Arudha Lagna'),
        (_BW + "arudha_emitter.py", 265, 'summary=f"category=arudha'), (_BW + "arudha_emitter.py", 266, 'headline=f"{graha_display} conjunct'),
        (_BW + "arudha_emitter.py", 306, 'summary=(f"category=arudha'), (_BW + "arudha_emitter.py", 308, 'headline=(f"{pada_label}')]),
    "bo_nakshatra_semantic": dict(table=MSR, cols=MSR_COLS, writer=_WR + "bo_nakshatra_semantic.py",
                                  emitter=_BW + "nakshatra_semantic_emitter.py", cites=MSR_SERVED + [
        (_WR + "bo_nakshatra_semantic.py", 141, "row = build_signal_row("), (_WR + "bo_nakshatra_semantic.py", 168, "conn.execute(_INSERT_SQL, row)"),
        (_WR + "bo_nakshatra_semantic.py", 175, "INSERT INTO public.bodha_msr_signals"),
        (_WR + "bo_nakshatra_semantic.py", 208, "%(signal_summary_text)s, %(signal_headline_text)s"),
        (_BW + "nakshatra_semantic_emitter.py", 251, "headline_bits = [f"), (_BW + "nakshatra_semantic_emitter.py", 258, 'headline = " | ".join(headline_bits)'),
        (_BW + "nakshatra_semantic_emitter.py", 260, "summary = ("),
        (_BW + "nakshatra_semantic_emitter.py", 281, '"signal_summary_text": summary'), (_BW + "nakshatra_semantic_emitter.py", 282, '"signal_headline_text": headline')]),
    "bo_special_lagna": dict(table=MSR, cols=MSR_COLS, writer=_WR + "bo_special_lagna.py", emitter=_BW + "special_lagna_emitter.py", cites=MSR_SERVED + [
        (_WR + "bo_special_lagna.py", 134, "row = build_signal_row("), (_WR + "bo_special_lagna.py", 155, "conn.execute(_INSERT_SQL, row)"),
        (_WR + "bo_special_lagna.py", 162, "INSERT INTO public.bodha_msr_signals"),
        (_WR + "bo_special_lagna.py", 195, "%(signal_summary_text)s, %(signal_headline_text)s"),
        (_BW + "special_lagna_emitter.py", 135, "summary = ("), (_BW + "special_lagna_emitter.py", 139, 'headline = f"{display} in H{house_d1}'),
        (_BW + "special_lagna_emitter.py", 154, '"signal_summary_text": summary'), (_BW + "special_lagna_emitter.py", 155, '"signal_headline_text": headline')]),
    "bo_sudarshana": dict(table=MSR, cols=MSR_COLS, writer=_WR + "bo_sudarshana.py", emitter=_BW + "sudarshana_emitter.py", cites=MSR_SERVED + [
        (_WR + "bo_sudarshana.py", 220, "row = build_signal_row("), (_WR + "bo_sudarshana.py", 258, "conn.execute(_INSERT_SQL, row)"),
        (_WR + "bo_sudarshana.py", 265, "INSERT INTO public.bodha_msr_signals"),
        (_WR + "bo_sudarshana.py", 298, "%(signal_summary_text)s, %(signal_headline_text)s"),
        (_BW + "sudarshana_emitter.py", 261, "headline = ("), (_BW + "sudarshana_emitter.py", 267, "headline = ("),
        (_BW + "sudarshana_emitter.py", 274, "headline = ("), (_BW + "sudarshana_emitter.py", 281, "summary = ("),
        (_BW + "sudarshana_emitter.py", 307, '"signal_summary_text": summary'), (_BW + "sudarshana_emitter.py", 308, '"signal_headline_text": headline')]),
    "bo_vargottama_dhana": dict(table=MSR, cols=MSR_COLS, writer=_WR + "bo_vargottama_dhana.py", emitter=_BW + "vargottama_dhana_emitter.py",
                                cites=MSR_SERVED + [
        (_WR + "bo_vargottama_dhana.py", 144, "rows = build_vargottama_rows("), (_WR + "bo_vargottama_dhana.py", 147, "build_dhana_axis_rows("),
        (_WR + "bo_vargottama_dhana.py", 166, "conn.execute(_INSERT_SQL, row)"),
        (_WR + "bo_vargottama_dhana.py", 173, "INSERT INTO public.bodha_msr_signals"),
        (_WR + "bo_vargottama_dhana.py", 206, "%(signal_summary_text)s, %(signal_headline_text)s"),
        (_BW + "vargottama_dhana_emitter.py", 162, '"signal_summary_text": summary'), (_BW + "vargottama_dhana_emitter.py", 163, '"signal_headline_text": headline'),
        (_BW + "vargottama_dhana_emitter.py", 284, 'summary=f"category=vargottama_amplification'), (_BW + "vargottama_dhana_emitter.py", 286, 'headline=f"{graha_display} is VARGOTTAMA'),
        (_BW + "vargottama_dhana_emitter.py", 381, "summary = ("), (_BW + "vargottama_dhana_emitter.py", 386, "headline = (")]),
    "bo_laksana": dict(table=MSR, cols=MSR_COLS, writer=_WR + "bo_laksana.py", emitter=_WR + "bo_laksana.py", cites=MSR_SERVED + [
        (_WR + "bo_laksana.py", 743, 'return " | ".join(parts)'), (_WR + "bo_laksana.py", 771, 'return f"{str(fact_subject).upper()}{loc}: {body}'),
        (_WR + "bo_laksana.py", 772, 'return f"{body} [{source_l1_asset}]"'),
        (_WR + "bo_laksana.py", 1394, '"signal_summary_text": ('), (_WR + "bo_laksana.py", 1398, '"signal_headline_text": value_text or f"'),
        (_WR + "bo_laksana.py", 2414, "signal_summary_text = _build_summary_text("), (_WR + "bo_laksana.py", 2425, "signal_headline_text = _build_headline_text("),
        (_WR + "bo_laksana.py", 2478, '"signal_summary_text":'), (_WR + "bo_laksana.py", 2479, '"signal_headline_text":'),
        (_WR + "bo_laksana.py", 2920, "headline = ("), (_WR + "bo_laksana.py", 2924, "summary = ("),
        (_WR + "bo_laksana.py", 2951, '"signal_summary_text":'), (_WR + "bo_laksana.py", 2952, '"signal_headline_text":'),
        (_WR + "bo_laksana.py", 3067, "INSERT INTO public.bodha_msr_signals"),
        (_WR + "bo_laksana.py", 3107, "%(signal_summary_text)s, %(signal_headline_text)s"),
        (_WR + "bo_laksana.py", 3264, "cur.executemany(_INSERT_SQL, batch)"), (_WR + "bo_laksana.py", 3601, "_batch_insert(conn, signal_rows)")]),
    "bo_anveshana": dict(table="bodha_discoveries", cols=["surface_reading", "depth_reading", "hypothesis_text"],
                         writer=_WR + "bo_anveshana.py", emitter=_WR + "bo_anveshana.py", cites=[
        (_WR + "bo_anveshana.py", 54, "INSERT INTO public.bodha_discoveries"), (_WR + "bo_anveshana.py", 70, "%(surface_reading)s, %(depth_reading)s"),
        (_WR + "bo_anveshana.py", 71, "%(hypothesis_text)s"), (_WR + "bo_anveshana.py", 423, '"surface_reading": surface'),
        (_WR + "bo_anveshana.py", 424, '"depth_reading": depth'), (_WR + "bo_anveshana.py", 426, '"hypothesis_text": hypothesis'),
        (_WR + "bo_anveshana.py", 511, 'surface=f"Signal {cand'), (_WR + "bo_anveshana.py", 512, 'depth=f"Structurally consequential'),
        (_WR + "bo_anveshana.py", 514, 'hypothesis=f"Pattern {cand'), (_WR + "bo_anveshana.py", 587, 'surface=f"Signal {sig_info'),
        (_WR + "bo_anveshana.py", 588, 'depth=f"Embedding distance'), (_WR + "bo_anveshana.py", 590, 'hypothesis=f"Pattern {sig_info'),
        (_WR + "bo_anveshana.py", 650, 'surface=f"Appears as one of many'), (_WR + "bo_anveshana.py", 651, 'depth=f"Stands {anom'),
        (_WR + "bo_anveshana.py", 653, 'hypothesis=f"Pattern {anom'), (_WR + "bo_anveshana.py", 734, 'surface=f"{subject} as an individual'),
        (_WR + "bo_anveshana.py", 735, 'depth=f"{subject} as a structural BROKER'), (_WR + "bo_anveshana.py", 737, 'hypothesis=f"{subject} acts as a structural bridge'),
        (_WR + "bo_anveshana.py", 829, "_batch_insert(conn, discoveries, _DISCOVERY_INSERT)"),
        (_L + "L2_bodha/query_discoveries.ts", 122, "surface_reading, depth_reading"), (_L + "L2_bodha/query_discoveries.ts", 123, "hypothesis_text"),
        (_L + "L2_bodha/query_discoveries.ts", 126, "FROM bodha_discoveries")]),
    "mi_darshana": dict(table="mimamsa_insight_units", cols=["statement"], writer=_WR + "mi_darshana.py", emitter=None, cites=[
        (_WR + "mi_darshana.py", 230, "statement = ("), (_WR + "mi_darshana.py", 296, "statement = ("), (_WR + "mi_darshana.py", 303, "statement = ("),
        (_WR + "mi_darshana.py", 308, "statement = ("), (_WR + "mi_darshana.py", 370, 'r["statement"],'), (_WR + "mi_darshana.py", 400, "statement = ("),
        (_WR + "mi_darshana.py", 526, 'f"{name_en}: no evidence'), (_WR + "mi_darshana.py", 649, 'statement = f"{name_en}: {status}'),
        (_WR + "mi_darshana.py", 692, 'SQL = """'), (_WR + "mi_darshana.py", 708, "cur.executemany(SQL, rows[i:i+BATCH])"),
        (_L + "L5_mimamsa/query_insights.ts", 221, "statement, rank_consequence"), (_L + "L5_mimamsa/query_insights.ts", 225, "FROM mimamsa_insight_units")]),
    "ph_sankrama": dict(table="phala_sankrama", cols=["mechanism_text"], writer=_WR + "ph_sankrama.py", emitter=_SV + "ph_sankrama/engine.py", cites=[
        (_WR + "ph_sankrama.py", 146, "spillovers = derive_spillover(sctx)"), (_WR + "ph_sankrama.py", 148, "for s in spillovers:"),
        (_WR + "ph_sankrama.py", 155, "bridge_path_jsonb, mechanism_text,"), (_WR + "ph_sankrama.py", 178, "s.mechanism_text"),
        (_SV + "ph_sankrama/engine.py", 237, "mechanism_text = ("), (_SV + "ph_sankrama/engine.py", 280, "mechanism_text=mechanism_text"),
        (_L + "L4_phala/query_phala_calibration.ts", 176, "mechanism_text"), (_L + "L4_phala/query_phala_calibration.ts", 181, "FROM phala_sankrama")]),
    "ph_sodhana": dict(table="phala_sodhana", cols=["recommendation_text"], writer=_WR + "ph_sodhana.py", emitter=_SV + "ph_sodhana/engine.py", cites=[
        (_WR + "ph_sodhana.py", 61, "flags = derive_sodhana_flags(sctx)"), (_WR + "ph_sodhana.py", 67, "for rec in flags:"),
        (_WR + "ph_sodhana.py", 70, "INSERT INTO phala_sodhana"), (_WR + "ph_sodhana.py", 91, "rec.recommendation_text"),
        (_SV + "ph_sodhana/engine.py", 156, "recommendation_text=("), (_SV + "ph_sodhana/engine.py", 205, "recommendation_text=("),
        (_SV + "ph_sodhana/engine.py", 231, "recommendation_text=("), (_SV + "ph_sodhana/engine.py", 254, "recommendation_text=("),
        (_SV + "ph_sodhana/engine.py", 288, "recommendation_text=("), (_SV + "ph_sodhana/engine.py", 336, "recommendation_text=("),
        (_SV + "ph_sodhana/engine.py", 394, "recommendation_text=("),
        (_L + "L4_phala/query_phala_calibration.ts", 322, "recommendation_text"), (_L + "L4_phala/query_phala_calibration.ts", 323, "FROM phala_sodhana")]),
    "ph_muhurta": dict(table="phala_muhurta", cols=["verdict_reason"], writer=_WR + "ph_muhurta.py", emitter=_SV + "ph_muhurta/engine.py", cites=[
        (_WR + "ph_muhurta.py", 179, "rec = derive_muhurta_record(mctx)"), (_WR + "ph_muhurta.py", 183, "INSERT INTO phala_muhurta"),
        (_WR + "ph_muhurta.py", 217, "rec.verdict_reason"),
        (_SV + "ph_muhurta/engine.py", 122, "return None, ("), (_SV + "ph_muhurta/engine.py", 134, "reason = ("), (_SV + "ph_muhurta/engine.py", 138, "return 'mediocre', reason"),
        (_SV + "ph_muhurta/engine.py", 218, "verdict, reason = classify_verdict("), (_SV + "ph_muhurta/engine.py", 290, "verdict_reason=reason"),
        (_L + "L4_phala/query_phala_calibration.ts", 97, "verdict_reason"), (_L + "L4_phala/query_phala_calibration.ts", 99, "FROM phala_muhurta")]),
}
# the two whose declaration is REMOVED (null): mi_bhavisya (UNCLEAR), ph_pramana (NOT-COMPOSED: verbatim copy of another asset's text)
NULLED = ("mi_bhavisya", "ph_pramana")
THIRTEEN = set(KEPT) | set(NULLED)
COLS_OF = {a: v["cols"] for a, v in KEPT.items()}


def _decl():
    return ac.load_asset_declarations()


def _read(path):
    return (REPO_ROOT / path).read_text(encoding="utf-8")


# ───────────────────────── (1) the committed file ─────────────────────────

def test_the_thirteen_are_exactly_the_audited_set_and_none_keeps_the_ddl_marker():
    from_test = {"bo_anveshana", "bo_arudha", "bo_laksana", "bo_nakshatra_semantic", "bo_special_lagna", "bo_sudarshana",
                 "bo_vargottama_dhana", "mi_bhavisya", "mi_darshana", "ph_muhurta", "ph_pramana", "ph_sankrama", "ph_sodhana"}
    assert THIRTEEN == from_test and len(KEPT) == 11 and len(NULLED) == 2
    decl = _decl()
    for a in THIRTEEN:       # writer evidence on the 11 kept, no marker on the 2 undeclared; none is `ddl`
        assert decl[a].get("evidence_kind") == ("writer" if a in KEPT else None), a


@pytest.mark.parametrize("asset", sorted(KEPT))
def test_kept_declaration_lists_exactly_the_audited_columns_and_cites_writer_code(asset):
    e = _decl()[asset]
    assert e["prose_fields"] == KEPT[asset]["cols"], asset
    ev = e["evidence"]["prose_fields"]
    assert ac.EVIDENCE_PATH_LINE_RE.search(ev)
    assert not re.search(r"TEXT in DDL", ev), "the DDL wording must not be the evidence any more"
    for path, line, needle in KEPT[asset]["cites"]:
        lines = _read(path).splitlines()
        assert line <= len(lines), (path, line)
        assert needle in lines[line - 1], (asset, path, line, lines[line - 1])
        assert f"{path.rsplit('/', 1)[1]}:{line}" in ev, (asset, path, line)


@pytest.mark.parametrize("asset", NULLED)
def test_removed_declaration_is_undeclared_with_no_orphan_pointer(asset):
    e = _decl()[asset]
    assert e["prose_fields"] is None and e["evidence"]["prose_fields"] is None and e.get("evidence_kind") is None


# ───────────────────────── (2) the six bodha_msr_signals writers share ONE table ─────────────────────────

def _owned_classes(src, const):
    tree = ast.parse(src)
    for s in tree.body:
        tgt = s.targets if isinstance(s, ast.Assign) else ([s.target] if isinstance(s, ast.AnnAssign) else [])
        if any(isinstance(t, ast.Name) and t.id == const for t in tgt):
            return [e.value for e in s.value.elts]
    return None


@pytest.mark.parametrize("asset", sorted(MSR_CLASSES))
def test_msr_group_evidence_names_the_producer_filter_and_the_classes_the_writer_owns(asset):
    ev = _decl()[asset]["evidence"]["prose_fields"]
    for needle in ("producer_asset_id", "signal_type_class", "dark"):
        assert needle in ev, (asset, needle)
    assert f"producer_asset_id='{asset}'" in ev
    for c in MSR_CLASSES[asset]:
        assert f"'{c}'" in ev, (asset, c)
    if asset == "bo_laksana":
        assert _owned_classes(_read(_WR + "bo_laksana.py"), "BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES") == MSR_CLASSES[asset]
    else:
        const = MSR_SIX[asset][3]
        if const:
            assert _owned_classes(_read(_WR + MSR_SIX[asset][0]), const) == MSR_CLASSES[asset]
        else:     # sudarshana: its one class is the emitter's SIGNAL_TYPE_CLASS literal, the delete scope of the writer
            assert re.search(r'^SIGNAL_TYPE_CLASS = "sudarshana_agreement"$', _read(_BW + "sudarshana_emitter.py"), re.M)


def test_the_producer_column_exists_and_is_dark_in_the_served_projection_while_the_class_facet_is_served():
    mig = _read(_MIG)
    assert re.search(r"ADD COLUMN IF NOT EXISTS producer_asset_id text", mig)
    assert "'bo_laksana','bo_arudha','bo_special_lagna','bo_sudarshana'" in mig and "'bo_vargottama_dhana','bo_nakshatra_semantic'" in mig
    ts = _read(_QS)
    assert "producer_asset_id" not in ts                      # not projectable, not filterable: dark in every projection
    default = re.search(r"const DEFAULT_SERVE_COLUMNS[^=]*=\s*\[(.*?)\n\]", ts, re.S).group(1)
    assert "'signal_type_class'" in default and "'signal_summary_text'" in default and "'signal_headline_text'" in default
    assert "m.signal_type_class = $${p++}" in ts              # the served facet (the per-asset Narr filter)


# ───────────────────────── (3) AST: the INSERT binds the column, the builder composes it ─────────────────────────

NAMED = sorted((a, c) for a, v in KEPT.items() if a in MSR_SIX or a in ("bo_laksana", "bo_anveshana") for c in v["cols"])


@pytest.mark.parametrize("asset_col", NAMED)
def test_named_parameter_insert_binds_the_declared_column(asset_col):
    asset, col = asset_col
    spec = KEPT[asset]
    assert rc.named_insert_problems(_read(spec["writer"]), spec["table"], col) == []


@pytest.mark.parametrize("asset_col", NAMED)
def test_every_dict_site_that_carries_the_column_resolves_to_composed_text(asset_col):
    asset, col = asset_col
    problems, sites, leaves = rc.emitter_column_problems(_read(KEPT[asset]["emitter"]), col)
    assert problems == [] and sites >= 1 and leaves, (asset, col, problems)


EXPECT_SITES = {"bo_laksana": 3, "bo_anveshana": 1}       # dict literals carrying the column; every other asset: 1
EXPECT_LEAVES = {      # composed expressions the dict values resolve to (one per emit site / call site)
    ("bo_arudha", "signal_summary_text"): 3, ("bo_arudha", "signal_headline_text"): 3,
    ("bo_nakshatra_semantic", "signal_summary_text"): 1, ("bo_nakshatra_semantic", "signal_headline_text"): 1,
    ("bo_special_lagna", "signal_summary_text"): 1, ("bo_special_lagna", "signal_headline_text"): 1,
    ("bo_sudarshana", "signal_summary_text"): 1, ("bo_sudarshana", "signal_headline_text"): 3,
    ("bo_vargottama_dhana", "signal_summary_text"): 2, ("bo_vargottama_dhana", "signal_headline_text"): 2,
    ("bo_anveshana", "surface_reading"): 4, ("bo_anveshana", "depth_reading"): 4, ("bo_anveshana", "hypothesis_text"): 4,
}


@pytest.mark.parametrize("asset_col", NAMED)
def test_the_number_of_emit_sites_is_pinned_so_a_new_site_must_be_decided(asset_col):
    asset, col = asset_col
    _, sites, leaves = rc.emitter_column_problems(_read(KEPT[asset]["emitter"]), col)
    assert sites == EXPECT_SITES.get(asset, 1), (asset, col, sites)
    if asset == "bo_laksana":      # 3 dict literals: the fact path (2 called builders, one return each + 1 f-string headline), D9 cross-check, divergence
        assert len(leaves) >= 3
    else:
        assert len(leaves) == EXPECT_LEAVES[asset_col], (asset, col, len(leaves))


@pytest.mark.parametrize("asset", sorted(MSR_SIX))
def test_writer_hands_the_emitter_row_to_the_insert_unchanged(asset):
    writer, module, builders, _ = MSR_SIX[asset]
    assert rc.writer_uses_emitter_problems(_read(_WR + writer), module, builders) == []


def test_laksana_batch_insert_executes_the_insert_with_the_rows_the_builders_made():
    src = _read(_WR + "bo_laksana.py")
    tree = ast.parse(src)
    assert any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr in ("execute", "executemany")
               and c.args and isinstance(c.args[0], ast.Name) and c.args[0].id == "_INSERT_SQL" for c in ast.walk(tree))
    assert rc.assigned_from_call_problems(src, "row", "_build_signal_row") == []
    assert any(rc._called_name(c) == "_batch_insert" for c in ast.walk(tree) if isinstance(c, ast.Call))


def test_laksana_divergence_headline_is_verbatim_first_with_a_composed_fallback():
    # documented doubt, pinned: `value_text or f"{subj}: divergent varga ratification in {dom}"` - the loaded vichara text wins when present
    tree = rc.parents(ast.parse(_read(_WR + "bo_laksana.py")))
    hits = [v for v in rc.dict_literal_values(tree, "signal_headline_text") if isinstance(v, ast.BoolOp)]
    assert len(hits) == 1 and isinstance(hits[0].op, ast.Or) and isinstance(hits[0].values[0], ast.Name) and hits[0].values[0].id == "value_text"


# ── mi_darshana: positional INSERT fed by rows.append tuples ──

def test_mi_darshana_statement_is_bound_at_its_insert_position_and_composed_at_five_of_six_append_sites():
    src = _read(_WR + "mi_darshana.py")
    sql = rc.sql_literal_assigned(src, "_substep_insight_units", "SQL")
    idx = rc.positional_insert_index(sql, "mimamsa_insight_units", "statement")
    assert idx == 6
    assert rc.executemany_feeds_problems(src, "_substep_insight_units", "SQL", "rows") == []
    problems, elems = rc.appended_tuple_elements(src, "_substep_insight_units", "rows", idx, width=17)
    assert problems == []
    tree = rc.parents(ast.parse(src))
    comp, non = [], []
    for e in elems:
        (non if rc.resolve_composed(tree, e)[0] else comp).append(ast.unparse(e)[:40])
    # 5 composed (calibrated outlook, manifestation grammar, load-bearing, verdict-object x2); 1 verbatim load (emergent-law
    # statements copied from mimamsa_discoveries, itself composed by mi_pariksha)
    assert len(comp) == 5 and non == ["r['statement']"], (comp, non)


# ── ph_*: record dataclass filled by the engine, iterated by the writer ──

def _engine(asset):
    return rc.parents(ast.parse(_read(KEPT[asset]["emitter"])))


def test_ph_sankrama_mechanism_text_is_bound_to_the_engines_record_and_composed_in_both_branches():
    w, tree = _read(_WR + "ph_sankrama.py"), _engine("ph_sankrama")
    problems, vals = nw.bound_values(w, "phala_sankrama", "mechanism_text")
    assert problems == [] and [ast.unparse(v) for v in vals] == ["s.mechanism_text"]
    assert rc.loop_var_from_builder_problems(w, "s", "derive_spillover") == []
    kws = rc.call_kwarg_values(tree, "SankramaRecord", "mechanism_text")
    assert len(kws) == 1
    problems, leaves = rc.resolve_composed(tree, kws[0])
    assert problems == [] and len(leaves) == 2           # an IfExp: the bridge-seed f-string and the CDLM-cell fallback f-string


def test_ph_sodhana_recommendation_text_is_bound_to_the_engines_record_composed_at_three_of_seven_detectors():
    w, tree = _read(_WR + "ph_sodhana.py"), _engine("ph_sodhana")
    problems, vals = nw.bound_values(w, "phala_sodhana", "recommendation_text")
    assert problems == [] and [ast.unparse(v) for v in vals] == ["rec.recommendation_text"]
    assert rc.loop_var_from_builder_problems(w, "rec", "derive_sodhana_flags") == []
    comp, non = rc.classify_sites(tree, rc.call_kwarg_values(tree, "SodhanaRecord", "recommendation_text"))
    # composed: confidence_inflation (ceiling), magnitude_drift (threshold), ledger_gap (missing keys). Constant text: falsifier_absent,
    # layer_leakage, confidence_degenerate, ceiling_inputs_degenerate
    assert len(comp) == 3 and len(non) == 4, (comp, non)


def test_ph_muhurta_verdict_reason_is_bound_to_the_engines_record_and_composed_in_one_reachable_branch():
    w, tree = _read(_WR + "ph_muhurta.py"), _engine("ph_muhurta")
    problems, vals = nw.bound_values(w, "phala_muhurta", "verdict_reason")
    assert problems == [] and [ast.unparse(v) for v in vals] == ["rec.verdict_reason"]
    assert rc.assigned_from_call_problems(w, "rec", "derive_muhurta_record") == []
    kws = rc.call_kwarg_values(tree, "MuhurtaRecord", "verdict_reason")
    assert [ast.unparse(k) for k in kws] == ["reason"]
    assert rc.assigned_from_call_problems(_read(KEPT["ph_muhurta"]["emitter"]), "verdict", "classify_verdict") == []
    rets = rc.tuple_return_elements(tree, "classify_verdict", 1)
    comp = [ast.unparse(e) for _, e in rets if not rc.resolve_composed(tree, e)[0]]
    non = [ast.unparse(e)[:24] for _, e in rets if rc.resolve_composed(tree, e)[0]]
    # one composed reason (the 'mediocre' f-string, reachable only when tarabala/chandrabala are a live lookup); two constant strings
    # ('not graded' placeholder state, 'none_genuine'); two None ('strong', 'adequate')
    assert comp == ["reason"] and len(non) == 4 and non.count("None") == 2, (comp, non)


# ───────────────────────── (4) the two removals rest on code facts ─────────────────────────

def test_ph_pramana_falsifier_text_is_the_anchors_falsifier_stripped_not_composed():
    w, tree = _read(_WR + "ph_pramana.py"), _engine_path(_SV + "ph_pramana/engine.py")
    problems, vals = nw.bound_values(w, "phala_pramana", "falsifier_text")
    assert problems == [] and [ast.unparse(v) for v in vals] == ["rec.falsifier_text"]
    assert rc.loop_var_from_builder_problems(w, "rec", "derive_pramana_records") == []
    kws = rc.call_kwarg_values(tree, "PramanaRecord", "falsifier_text")
    assert [ast.unparse(k) for k in kws] == ["falsifier"]
    fn = rc.functions_named(tree, "derive_pramana_records")[0]
    assert [ast.unparse(v) for v in rc._assignments(fn, "falsifier")] == ["(anchor.falsifier or '').strip()"]
    assert rc.resolve_composed(tree, kws[0])[0] != []     # not composed
    # why `null` and not `[]`: the writer/engine still string-build a bound column (the provenance pointer `source_citation`)
    cit = rc.call_kwarg_values(tree, "PramanaRecord", "source_citation")
    assert len(cit) == 1 and rc.resolve_composed(tree, cit[0])[0] == []
    # the same text IS declared composed where it is composed: ph_nimitta.falsifier
    assert _decl()["ph_nimitta"]["prose_fields"] == ["falsifier"]


def _engine_path(path):
    return rc.parents(ast.parse(_read(path)))


def test_mi_bhavisya_outcome_claim_is_a_verbatim_copy_or_a_label_join_so_undeclared():
    src = _read(_WR + "mi_bhavisya.py")
    tree = rc.parents(ast.parse(src))
    run = next(f for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) and any(
        isinstance(a, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "outcome_claim" for t in a.targets) for a in ast.walk(f)))
    vals = [ast.unparse(v) for v in rc._assignments(run, "outcome_claim")]
    assert vals == ["str(_karmic_note)", "' '.join(parts) if parts else 'unspecified'"], vals
    assert [ast.unparse(v) for v in rc._assignments(run, "_karmic_note")] == ["anchor.get('karmic_note')"]       # copied from phala_anchors
    assert [ast.unparse(v) for v in rc._assignments(run, "parts")] == ["[p for p in [_direction, _domain_raw, _event_type] if p]"]
    sql = rc.sql_literal_assigned(src, run.name, "PRED_SQL")
    idx = rc.positional_insert_index(sql, "mimamsa_predictions", "outcome_claim")
    problems, elems = rc.appended_tuple_elements(src, run.name, "pred_rows", idx)
    assert problems == [] and [ast.unparse(e) for e in elems] == ["outcome_claim"]
    # why `null` and not `[]`: the observation_window is string-built (a range literal) and outcome_claim itself joins labels
    win = rc.appended_tuple_elements(src, run.name, "pred_rows", rc.positional_insert_index(sql, "mimamsa_predictions", "observation_window"))[1]
    assert len(win) == 1 and isinstance(win[0], ast.JoinedStr)


# ───────────────────────── (5) mutation checks: each check fails on the defect it claims to catch ─────────────────────────

def _replace_node(tree, target, new):
    for n in ast.walk(tree):
        for f, v in ast.iter_fields(n):
            if v is target:
                setattr(n, f, new)
                return True
            if isinstance(v, list):
                for i, x in enumerate(v):
                    if x is target:
                        v[i] = new
                        return True
    return False


def _leaf_mutants(src, col):
    """For every composed leaf the column's dict values resolve to, `src` with that one leaf replaced by a constant string."""
    n = len(rc.emitter_column_problems(src, col)[2])
    out = []
    for k in range(n):
        tree = rc.parents(ast.parse(src))
        leaves = []
        for v in rc.dict_literal_values(tree, col):
            leaves += rc.resolve_composed(tree, v)[1]
        assert _replace_node(tree, leaves[k], ast.Constant("constant text"))
        out.append(ast.unparse(tree))
    return out


@pytest.mark.parametrize("asset_col", NAMED)
def test_mutation_turning_any_one_composed_leaf_into_a_constant_is_caught(asset_col):
    asset, col = asset_col
    src = _read(KEPT[asset]["emitter"])
    mutants = _leaf_mutants(src, col)
    assert mutants
    for m in mutants:
        assert rc.emitter_column_problems(m, col)[0], (asset, col)


@pytest.mark.parametrize("asset_col", NAMED)
def test_mutation_renaming_the_insert_column_or_dropping_its_binding_is_caught(asset_col):
    asset, col = asset_col
    spec = KEPT[asset]
    src = _read(spec["writer"])
    m = re.search(rf"INSERT\s+INTO\s+(?:public\.)?{spec['table']}\s*\(", src)
    end = src.index("VALUES", m.end())
    mutant_a = src[:m.end()] + re.sub(rf"\b{col}\b", col[:-1], src[m.end():end], count=1) + src[end:]
    assert mutant_a != src
    assert rc.named_insert_problems(mutant_a, spec["table"], col), "renamed INSERT column must be caught"
    mutant_b = src.replace(f"%({col})s", "NULL", 1)
    assert mutant_b != src and rc.named_insert_problems(mutant_b, spec["table"], col), "dropped %(col)s binding must be caught"


@pytest.mark.parametrize("asset", sorted(MSR_SIX))
def test_mutation_breaking_the_writer_to_emitter_hand_off_is_caught(asset):
    writer, module, builders, _ = MSR_SIX[asset]
    src = _read(_WR + writer)
    assert rc.writer_uses_emitter_problems(src.replace("_INSERT_SQL, row)", "_INSERT_SQL, {})"), module, builders)
    assert rc.writer_uses_emitter_problems(src.replace(builders[0] + "(", "unrelated_builder("), module, builders)


def test_mutation_mi_darshana_a_constant_statement_or_a_shifted_column_is_caught():
    src = _read(_WR + "mi_darshana.py")
    tree = rc.parents(ast.parse(src))
    fn = rc.functions_named(tree, "_substep_insight_units")[0]
    elems = [c.args[0].elts[6] for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
             and c.func.attr == "append" and isinstance(c.func.value, ast.Name) and c.func.value.id == "rows"]

    def count_composed(s):
        t = rc.parents(ast.parse(s))
        e = rc.appended_tuple_elements(s, "_substep_insight_units", "rows", 6)[1]
        return sum(not rc.resolve_composed(t, x)[0] for x in e)

    assert count_composed(src) == 5
    # one composed append site turned into a constant
    f_site = next(e for e in elems if isinstance(e, ast.JoinedStr))
    assert _replace_node(tree, f_site, ast.Constant("constant"))
    assert count_composed(ast.unparse(tree)) == 4
    # the INSERT column order shifted: `statement` is no longer at index 6
    sql = rc.sql_literal_assigned(src, "_substep_insight_units", "SQL")
    shifted = sql.replace("statement, rank_consequence", "rank_consequence, statement")
    assert rc.positional_insert_index(shifted, "mimamsa_insight_units", "statement") == 7
    # a tuple of the wrong width is reported
    assert rc.appended_tuple_elements(src, "_substep_insight_units", "rows", 6, width=16)[0]


def test_mutation_ph_engines_a_constant_reason_or_text_changes_the_composed_split():
    sod = _read(KEPT["ph_sodhana"]["emitter"])
    old = "f'Recalculate confidence_high using G-LADDER: n_independent={anchor.dasha_consensus_count}, '"
    assert sod.count(old) == 1
    t = rc.parents(ast.parse(sod.replace(old, "'Recalculate confidence_high using G-LADDER: n_independent=unknown, '")))
    comp, non = rc.classify_sites(t, rc.call_kwarg_values(t, "SodhanaRecord", "recommendation_text"))
    assert len(comp) == 3 and len(non) == 4
    # the f-string part turned into a literal, but the tuple still holds the ceiling f-string on the next line: still composed;
    # both f-strings gone -> constant
    old2 = "f'ayanamsha_robustness={anchor.ayanamsha_robustness} → ceiling={ceiling:.3f}. '"
    assert sod.count(old2) == 1
    both = sod.replace(old, "'a '").replace(old2, "'b '")
    t2 = rc.parents(ast.parse(both))
    comp2, non2 = rc.classify_sites(t2, rc.call_kwarg_values(t2, "SodhanaRecord", "recommendation_text"))
    assert len(comp2) == 2 and len(non2) == 5
    mu = _read(KEPT["ph_muhurta"]["emitter"])
    old3 = 'f"Best available window scores {composite_quality:.2f} — below genuine threshold "'
    assert mu.count(old3) == 1
    t3 = rc.parents(ast.parse(mu.replace(old3, '"Best available window scores low — below genuine threshold "').replace(
        'f"({_GENUINE_THRESHOLD}). Moon may', '"(x). Moon may')))
    rets = rc.tuple_return_elements(t3, "classify_verdict", 1)
    assert [ast.unparse(e) for _, e in rets if not rc.resolve_composed(t3, e)[0]] == []
    sk = _read(KEPT["ph_sankrama"]["emitter"])
    t4 = rc.parents(ast.parse(sk.replace("f\"{ctx.source_domain} linkage to {target_domain} (mechanism from CDLM cell {cell.cell_id})\"",
                                        "\"linkage\"")))
    assert rc.resolve_composed(t4, rc.call_kwarg_values(t4, "SankramaRecord", "mechanism_text")[0])[0]


def test_resolver_unit_behaviour_on_synthetic_code():
    src = ("def mk(*, summary, headline):\n    return {'s': summary, 'h': headline}\n"
           "def go(a):\n    mk(summary=f'x {a}', headline='const')\n")
    tree = rc.parents(ast.parse(src))
    vals = rc.dict_literal_values(tree, "h")
    assert rc.resolve_composed(tree, vals[0])[0]                      # the call passes a constant
    vals = rc.dict_literal_values(tree, "s")
    assert rc.resolve_composed(tree, vals[0])[0] == []
    # an f-string with no placeholder, a numeric `+`, and `str(x)` are not composition
    for bad in ("f'plain'", "1 + 2", "str(a)", "a", "a[:5]", "a.get('k')"):
        t = rc.parents(ast.parse(f"def g(a):\n    x = {bad}\n    return {{'k': x}}\n"))
        assert rc.resolve_composed(t, rc.dict_literal_values(t, "k")[0])[0], bad
    for good in ("f'v {a}'", "'v ' + a", "'v %s' % a", "'{}'.format(a)", "' '.join(a)", "f'{a}' if a else f'{a}!'"):
        t = rc.parents(ast.parse(f"def g(a):\n    x = {good}\n    return {{'k': x}}\n"))
        assert rc.resolve_composed(t, rc.dict_literal_values(t, "k")[0])[0] == [], good
    # an IfExp with one constant branch is not composed; a name assigned on two branches needs both composed
    t = rc.parents(ast.parse("def g(a):\n    x = f'{a}' if a else 'none'\n    return {'k': x}\n"))
    assert rc.resolve_composed(t, rc.dict_literal_values(t, "k")[0])[0]
    t = rc.parents(ast.parse("def g(a):\n    if a:\n        x = f'{a}'\n    else:\n        x = 'c'\n    return {'k': x}\n"))
    assert rc.resolve_composed(t, rc.dict_literal_values(t, "k")[0])[0]


# ───────────────────────── (6) evidence_kind "writer": the cite shape is enforced, not trusted ─────────────────────────

import subprocess  # noqa: E402

_CITE_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\[\]@-]*\.(?:py|ts|tsx|sql):([1-9][0-9]*)")
_CITE_TOKEN = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./\[\]@-]*\.(?:py|ts|tsx|sql)):([1-9][0-9]*)")


def _vdoc(ev, kind="writer", pf=("x",)):
    return dict(version="1.0.0", kind_enum=list(ac.DECLARED_KINDS),
                assets={"a": dict(prose_fields=list(pf), evidence_kind=kind, evidence=dict(prose_fields=ev))})


@pytest.mark.parametrize("ev", ["platform/python-sidecar/x/w.py:3", "layers/q.ts:9 and w.py:2", "a/b.tsx:44"])
def test_writer_kind_accepts_py_ts_tsx_cites(ev):
    ac.validate_declarations(_vdoc(ev))
    ac.validate_declarations(_vdoc(ev, kind=None))       # unmarked legacy declarations get the same cite check


@pytest.mark.parametrize("ev", [
    "migrations/001_baseline.sql:12", "w.py:3 and migrations/001_baseline.sql:12", "tests/foo_test.py:3", "platform/tests/test_x.py:3",
    "platform/src/lib/__tests__/w.ts:3", "platform/src/lib/x.test.ts:3", "platform/src/lib/x.spec.tsx:3", "w.py:3 and tests/unit/a.py:9",
    "w.py", "the writer composes it", "w.py:0", "fixtures/census/w.py:3"])
def test_writer_kind_rejects_sql_test_path_and_shapeless_cites(ev):
    for kind in ("writer", None):
        with pytest.raises(ac.DeclarationsError):
            ac.validate_declarations(_vdoc(ev, kind=kind))


def test_ddl_kind_is_unchanged_and_writer_is_an_accepted_kind():
    assert "writer" in ac.EVIDENCE_KINDS and "ddl" in ac.EVIDENCE_KINDS
    ac.validate_declarations(_vdoc("TEXT in DDL (325_l2_bodha_enriched_schema.sql)", kind="ddl"))
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(_vdoc("w.py:3", kind="ddl"))          # ddl needs the migration file token


def _tracked():
    out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    return [f for f in out if f]


def _resolve(path, files):
    if (REPO_ROOT / path).is_file():
        return path
    hits = [f for f in files if f == path or f.endswith("/" + path)]
    return hits[0] if len(hits) == 1 else None


def test_every_non_null_declaration_is_writer_kind_with_cites_that_resolve_to_non_test_non_ddl_lines():
    files = _tracked()
    bad = []
    for aid, e in _decl().items():
        if e["prose_fields"] is None:
            continue
        ev = e["evidence"]["prose_fields"]
        if e.get("evidence_kind") != "writer":
            bad.append((aid, "evidence_kind", e.get("evidence_kind")))
            continue
        cites = _CITE_TOKEN.findall(ev)
        if not cites:
            bad.append((aid, "no cite"))
        for path, line in cites:
            if path.endswith(".sql"):
                bad.append((aid, "sql cite", path))
                continue
            real = _resolve(path, files)
            if real is None:
                bad.append((aid, "does not resolve (missing or ambiguous)", path))
            elif int(line) > len((REPO_ROOT / real).read_text(encoding="utf-8").splitlines()):
                bad.append((aid, "line past end of file", path, line))
            elif re.search(r"(^|/)(__tests__|tests?|fixtures)/|(^|/)test_[^/]*$|_test\.py$|\.(test|spec)\.tsx?$", real):
                bad.append((aid, "test path", real))
    assert bad == [], bad


def test_the_file_level_description_no_longer_says_the_thirteen_carry_ddl():
    d = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["description"]
    assert "13 earlier declarations" not in d and "evidence_kind 'writer'" in d
    assert not any(e.get("evidence_kind") == "ddl" for e in _decl().values())
