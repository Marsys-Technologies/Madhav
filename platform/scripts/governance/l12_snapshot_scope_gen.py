#!/usr/bin/env python3
"""l12_snapshot_scope_gen.py -- (re)generates l12_snapshot_scopes.json, the DATA the L1/L2 chart snapshot digests.  OFFLINE: no database.

Sources, in the order they decide what a component is
  1. asset_declarations.json `produced_tables` (table + optional filter {column, equals|in}): the declared produced set of the asset;
  2. the registry count_sql (asset_registry_seed.ts, transcribed below as CF_PREDICATES for the chart_facts slices): the rows the asset is credited
     with in a SHARED table; where the active output-digest spec names more categories than count_sql, the slice is the UNION of both;
  3. the active asset_output_digest_specs row (the migration that last inserted a spec for the asset; the nirmana spec carries key_columns,
     value_columns = the columns vetted as deterministic across rebuilds, and the filters): key + content columns of a component;
  4. a table with no spec column list is digested over every column except the volatile ones (decided at run time from information_schema).
Run:  python3 platform/scripts/governance/l12_snapshot_scope_gen.py [--check]     (--check: exit 1 when the committed file is stale)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLATFORM = HERE.parents[1]
OUT = HERE / "l12_snapshot_scopes.json"
DECLS = HERE / "asset_declarations.json"
CENSUS_NOTE = "census_interim/42e96d491 (census_L1.json, census_L2.json) lists the same 20 + 23 assets"

VOLATILE = {
    "names": ["computed_at", "created_at", "updated_at", "build_id", "build_run_id", "run_id", "receipt_id", "attempt_id", "last_built_at",
              "generated_at", "written_at", "built_at", "ingested_at", "loaded_at", "last_refreshed_at"],
    "regex": r"(_at$|_run_id$|_receipt_id$|_attempt_id$|^receipt|^attempt_)",
    "why": "wall-clock write times and run / receipt / attempt identifiers differ on every rebuild by construction",
}

# chart_facts predicates = the registry count_sql of the asset (asset_registry_seed.ts) -- SQL over the unqualified chart_facts columns
CF_PREDICATES = {
    "ga_positions": "fact_category IN ('graha_position', 'graha_sign_attributes', 'bhava_cusps', 'house_chalit', 'sandhi_flag')",
    "ga_strength": ("fact_category LIKE 'graha_shadbala_%' OR fact_category IN ('graha_ishta_phala', 'graha_kashta_phala') OR fact_category LIKE 'graha_vimsopaka_%' "
                    "OR (fact_category LIKE 'ashtakavarga_%' AND fact_category <> 'ashtakavarga_anubindu') OR fact_category LIKE 'house_bhava_bala_%' "
                    "OR fact_category LIKE 'graha_%_bala_per_varga'"),
    "ga_sensitive": ("fact_category IN ('upagraha_position', 'saturn_derived_point', 'saham_position', 'karaka_chara_position', 'karakamsa_position', "
                     "'swamsa_position', 'arudha_pada', 'midpoint', 'aprakasha_position', 'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point', "
                     "'sensitive_point_gulika_mandi', 'sun_derived_upagraha', 'special_lagna', 'nakshatra_pada_sensitive', 'kp_ruling_planets_natal', "
                     "'kp_cuspal_significators') OR fact_category LIKE 'esoteric_point_%' OR fact_category LIKE 'tajik_%'"),
    "ga_sensitive_degree": "fact_category = 'sensitive_degree_check'",
    "ga_ayurdaya": "fact_category = 'ayurdaya'",
    "ga_panchanga": "fact_category LIKE 'panchanga%'",
    "ga_sade_sati": ("fact_category IN ('sade_sati_cycle', 'sade_sati_phase', 'sade_sati_phase_quarter', 'dhaiya_period', 'kantaka_shani_period', "
                     "'ashtama_shani_period', 'ardha_ashtama_shani_period', 'janma_shani_period', 'vishakha_shani_period', 'anumukha_shani_period', "
                     "'sade_sati_saturn_retrograde_subset', 'sade_sati_cancellation_check', 'sade_sati_modifier_overlay', "
                     "'sade_sati_concurrent_dasha_overlay', 'sade_sati_downstream_cross_reference')"),
    "ga_nakshatra": ("fact_category IN ('graha_nakshatra_join', 'graha_pada_join', 'nakshatra_lord_placement', 'graha_kp_lords', 'cusp_kp_lords', "
                     "'graha_gandanta', 'graha_degree_flags', 'nakshatra_dispositor', 'nakshatra_exchange', 'nakshatra_conjunction', 'nakshatra_cogravity', "
                     "'graha_tara_bala', 'nakshatra_statistics', 'nakshatra_cross_ayanamsha', 'kp_house_significators', 'kp_planet_significations')"),
    "ga_structural": ("fact_category IN (SELECT fco.fact_category FROM fact_category_ownership fco WHERE fco.owning_asset_id = 'ga_structural')"),
}
# the ga_condition and ga_dashas slices of chart_facts (their count_sql / declared produced_tables)
CF_EXTRA_COMPONENT = {
    "ga_condition": ("chart_facts_avastha", "fact_category LIKE 'graha_avastha_%_per_varga' OR fact_category = 'graha_avastha_sayanadi' OR fact_category = 'graha_avastha_lajjitadi'",
                     "registry count_sql (migration 1219 text)"),
    "ga_dashas": ("chart_facts_dasha_scope_cap", "fact_category = 'dasha_scope_cap'", "asset_declarations produced_tables filter"),
}

DIMS = {
    "chart_facts": ["ayanamsha_id", "fact_category", "fact_key"],
    "chart_divisionals": ["ayanamsha_id", "varga", "fact_category"],
    "chart_dashas": ["ayanamsha_id", "system_id", "level_n"],
    "chart_vichara": ["ayanamsha_id", "vichara_family"],
    "bodha_msr_signals": ["ayanamsha_id", "signal_type_class"],
    "bodha_cgm_nodes": ["ayanamsha_id", "node_type"],
    "bodha_cgm_edges": ["ayanamsha_id", "edge_type"],
    "bodha_grounding_matches": ["ayanamsha_id", "target_kind"],
}
# surrogate ids (own) and id-bearing columns: they go to the IDS digest only. Anything not listed is content.
IDS = {
    "chart_divisionals": {"id": ["id"], "ref": []},
    "chart_dashas": {"id": ["dasha_row_id"], "ref": []},
    "bodha_msr_signals": {"id": ["signal_id"], "ref": ["constituent_signals_array", "contradicts_signals_array"]},
    "bodha_cgm_nodes": {"id": ["node_id"], "ref": ["msr_signal_id"]},
    "bodha_cgm_edges": {"id": ["edge_id"], "ref": ["from_node_id", "to_node_id", "underlying_msr_signal_ids_array"]},
    "bodha_signal_embeddings": {"id": ["signal_id", "embedding_id"], "ref": []},
    "bodha_discoveries": {"id": ["discovery_id"], "ref": []},
    "bodha_anomalies": {"id": ["anomaly_id"], "ref": []},
    "bodha_contradictions": {"id": ["contradiction_id"], "ref": ["signal_a_id", "signal_b_id"]},
    "bodha_cgm_motifs": {"id": ["motif_id"], "ref": ["involved_node_ids_array", "involved_edge_ids_array"]},
    "bodha_cgm_sub_graphs": {"id": ["subgraph_id"], "ref": ["node_ids_array"]},
    "bodha_rm_resonances": {"id": ["resonance_id"], "ref": []},
    "bodha_rm_remedy_prescriptions": {"id": ["prescription_id"], "ref": ["target_resonance_id"]},
    "bodha_rm_chart_summary": {"id": ["summary_id"], "ref": []},
    "bodha_rm_dosha_remedy_bundles": {"id": ["bundle_id"], "ref": ["prescription_ids_in_bundle_array"]},
    "bodha_rm_pattern_remedies": {"id": ["pattern_remedy_id"], "ref": ["prescription_ids_array"]},
    "bodha_rm_dasha_windowed_prescriptions": {"id": ["window_prescription_id"], "ref": ["base_prescription_id"]},
}
AUTO_ID_COLUMNS = ["id"]         # auto (no spec column list) components: a column literally named id is a surrogate
# row identity for the ROW-LEVEL detail: the natural key, never a surrogate. Only where it is known to be the declared natural key.
ROW_KEYS = {
    "chart_facts": ["ayanamsha_id", "fact_category", "fact_subject", "fact_key"],
}
NO_ROW_DETAIL = {"bodha_msr_signals", "bodha_cgm_nodes", "bodha_cgm_edges", "chart_vichara"}      # key is a surrogate / not a proven unique tuple
EMBEDDING_COLUMNS = {"bodha_signal_embeddings": ["embedding_vec"]}
GLOBAL_RELATIONS = {"fact_category_ownership"}
# components the spec does not list but the declared produced set / count_sql names, digested with every non-volatile column
AUTO_EXTRAS = {
    "ga_fact_identity": [("chart_fact_identity", None, "registry target table (migration 1262): no declared produced set, no spec")],
    "ga_structural": [("fact_category_ownership", None, "ownership map the count_sql joins (global, not chart scoped)")],
    "ga_prashna": [("ga_prashna_lagna", None, "declared produced_tables")],
    "bo_karanajala": [("bodha_contradictions", None, "declared produced_tables")],
    "bo_cdlm_summary": [("bodha_cdlm_domain_rollups", None, "declared produced_tables"), ("bodha_cdlm_pattern_clusters", None, "declared produced_tables")],
}
# bo_karanajala's node slices (declared produced_tables with a filter)
NODE_SLICES = {"bo_karanajala": [("bodha_cgm_nodes_arudha", "node_type = 'arudha'", "declared produced_tables filter node_type=arudha"),
                                 ("bodha_cgm_nodes_special_lagna", "node_type = 'special_lagna'", "declared produced_tables filter node_type=special_lagna")]}
# bo_bimba: the declared produced set is the WHOLE bodha_cgm_nodes (no filter); the spec's node_type filter is a narrower slice
WHOLE_TABLE = {"bo_bimba": "bodha_cgm_nodes", "bo_laksana": "bodha_msr_signals"}
# slices of bodha_msr_signals per satellite asset (registry count_sql)
MSR_SLICES = {
    "bo_sudarshana": "signal_type_class = 'sudarshana_agreement'",
    "bo_nakshatra_semantic": "signal_type_class = 'nakshatra_semantic'",
    "bo_arudha": "signal_type_class = 'arudha'",
    "bo_special_lagna": "signal_type_class = 'special_lagna'",
    "bo_vargottama_dhana": "signal_type_class = ANY(ARRAY['vargottama_amplification', 'dhana_axis'])",
    "bo_laksana_rerank": "graph_node_strength_contribution_jsonb IS NOT NULL",
}


def _mig_num(path: str) -> int:
    m = re.match(r"(\d+)_", os.path.basename(path))
    return int(m.group(1)) if m else 10 ** 9


def load_specs() -> dict:
    """asset_id -> (migration file, spec_sha256, spec) of the LAST spec a migration inserted for the asset (retire-then-insert is the pattern)."""
    pat = re.compile(r"\(\s*'([a-z_0-9]+)'\s*,\s*'([0-9a-f]{64})'\s*,\s*'(\{.*?\})'::jsonb", re.S)
    out: dict = {}
    for f in sorted(glob.glob(str(PLATFORM / "migrations" / "*.sql")), key=_mig_num):
        text = Path(f).read_text(encoding="utf-8", errors="replace")
        if "asset_output_digest_specs" not in text:
            continue
        for m in pat.finditer(text):
            out[m.group(1)] = (os.path.basename(f), m.group(2), json.loads(m.group(3).replace("''", "'")))
    return out


def sql_list(values) -> str:
    return "(" + ", ".join("'" + v.replace("'", "''") + "'" for v in values) + ")"


def spec_filter(c: dict) -> tuple[str | None, str | None]:
    parts, text = [], []
    for col, vals in sorted((c.get("where_in") or {}).items()):
        parts.append(col + " IN " + sql_list(vals))
        text.append(col + " in " + str(len(vals)) + " values")
    for col, v in sorted((c.get("where_equals") or {}).items()):
        if col == "chart_id":
            continue
        parts.append(col + " = '" + str(v).replace("'", "''") + "'")
        text.append(col + " = " + str(v))
    for col in c.get("where_is_null") or []:
        parts.append(col + " IS NULL")
        text.append(col + " is null")
    return (" AND ".join(parts) or None), ("; ".join(text) or None)


def component(name, relation, where_sql, where_text, key, content, source, extra_note=None) -> dict:
    ids = IDS.get(relation, {"id": [], "ref": []})
    auto = content is None
    comp = {"name": name, "relation": relation, "kind": "global" if relation in GLOBAL_RELATIONS else "chart",
            "where_sql": where_sql, "where_text": where_text, "key": key or [], "content_columns": content,
            "id_columns": list(ids["id"]) + (AUTO_ID_COLUMNS if auto and not ids["id"] else []), "id_ref_columns": list(ids["ref"]), "dims": DIMS.get(relation, []),
            "source": source}
    if relation in ROW_KEYS:
        comp["row_key"] = ROW_KEYS[relation]
        comp["key"] = ROW_KEYS[relation]
    elif relation in NO_ROW_DETAIL or not comp["key"]:
        comp["row_key"] = []
    if relation in EMBEDDING_COLUMNS:
        comp["embedding_columns"] = EMBEDDING_COLUMNS[relation]
    if extra_note:
        comp["note"] = extra_note
    return comp


def strip_ids(cols, relation):
    ids = IDS.get(relation, {"id": [], "ref": []})
    return [c for c in cols if c not in ids["id"] and c not in ids["ref"]]


def build() -> dict:
    decls = json.loads(DECLS.read_text(encoding="utf-8"))["assets"]
    specs = load_specs()
    assets: dict = {}
    names = sorted(a for a in decls if a[:3] in ("ga_", "bo_"))
    for a in names:
        layer = "L1" if a.startswith("ga_") else "L2"
        comps: list = []
        mig, sha, spec = specs.get(a, (None, None, None))
        spec_by_rel: dict = {}
        for c in (spec or {}).get("components", []):
            spec_by_rel.setdefault(c["relation"], []).append(c)
        src_spec = (" + spec " + mig.split("_")[0] + " " + sha[:8]) if mig else ""
        done_rel_where: set = set()
        for rel, cl in spec_by_rel.items():
            for c in cl:
                sf, st = spec_filter(c)
                key, content = c["key_columns"], strip_ids(c["value_columns"], rel)
                name = c["name"]
                where_sql, where_text, source = sf, st, "output-digest spec" + src_spec
                if rel == "chart_facts":
                    pred = CF_PREDICATES.get(a)
                    cats = (c.get("where_in") or {}).get("fact_category") or []
                    if pred:
                        where_sql = "(" + pred + ")" + ((" OR fact_category IN " + sql_list(cats)) if cats and a != "ga_structural" else "")
                        where_text = "registry count_sql predicate" + (" UNION spec fact_category set (" + str(len(cats)) + ")" if cats and a != "ga_structural" else "")
                        source = "registry count_sql + " + source
                    name = "chart_facts"
                if a in WHOLE_TABLE and rel == WHOLE_TABLE[a]:
                    where_sql, where_text, source = None, "whole table (declared produced_tables / count_sql have no filter)", "declared produced_tables + " + source
                if a in MSR_SLICES and rel == "bodha_msr_signals":
                    where_sql, where_text, source = MSR_SLICES[a], "registry count_sql: " + MSR_SLICES[a], "registry count_sql + " + source
                if rel == "chart_vichara":
                    name = c["name"]
                comps.append(component(name, rel, where_sql, where_text, key, content, source))
                done_rel_where.add((rel, name))
        if not spec_by_rel and a in WHOLE_TABLE:
            comps.append(component(WHOLE_TABLE[a], WHOLE_TABLE[a], None, "whole table", [], None, "declared produced_tables"))
        if a in CF_EXTRA_COMPONENT:
            name, pred, why = CF_EXTRA_COMPONENT[a]
            base = next(x for x in specs["ga_positions"][2]["components"] if x["relation"] == "chart_facts")
            comps.append(component(name, "chart_facts", pred, why + ": " + pred, ROW_KEYS["chart_facts"], strip_ids(base["value_columns"], "chart_facts"), why))
        if a in NODE_SLICES:
            for name, pred, why in NODE_SLICES[a]:
                base = next(x for x in specs["bo_bimba"][2]["components"] if x["relation"] == "bodha_cgm_nodes")
                comps.append(component(name, "bodha_cgm_nodes", pred, why, base["key_columns"], strip_ids(base["value_columns"], "bodha_cgm_nodes"), why))
        for rel, pred, why in AUTO_EXTRAS.get(a, []):
            comps.append(component(rel, rel, pred, why, [], None, why))
        if a == "ga_vichara":
            fams = sorted((c["where_text"] or "").split("= ")[-1] for c in comps)
            comps.append(component("chart_vichara_other_families", "chart_vichara", "vichara_family NOT IN " + sql_list(fams),
                                   "families outside the five the spec names (registry count_sql counts the whole table)", [], None,
                                   "registry count_sql (whole chart_vichara)"))
        names_seen = [c["name"] for c in comps]
        assert len(names_seen) == len(set(names_seen)), (a, names_seen)
        if not comps:
            raise SystemExit("no component for " + a)
        assets[a] = {"layer": layer, "spec_migration": mig, "spec_sha256": sha, "components": comps}
    # the residual: chart_facts rows of the chart that no asset slice claims
    preds = []
    for a, rec in assets.items():
        for c in rec["components"]:
            if c["relation"] == "chart_facts" and c.get("where_sql"):
                preds.append("(" + c["where_sql"] + ")")
    base = next(x for x in specs["ga_positions"][2]["components"] if x["relation"] == "chart_facts")
    residual = {"layer": "L1", "spec_migration": None, "spec_sha256": None,
                "components": [component("chart_facts_unclaimed", "chart_facts", "NOT coalesce(" + " OR ".join(preds) + ", false)",
                                         "chart_facts rows of the chart claimed by NO asset slice above (a change here is never predicted)",
                                         ROW_KEYS["chart_facts"], strip_ids(base["value_columns"], "chart_facts"), "complement of the union of every chart_facts slice")]}
    return {"schema": "suvarna.l12_snapshot_scopes/1", "volatile": VOLATILE, "census_note": CENSUS_NOTE, "assets": assets, "residual": residual}


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    a = p.parse_args(argv)
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if a.check:
        return 0 if OUT.exists() and OUT.read_text(encoding="utf-8") == text else 1
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
