#!/usr/bin/env python3
"""flip_detector.py: S-L1 class-flip detector and attribution-hook validator (SS N-64 acceptance tool). READ-ONLY. Tooling only: it never writes to the database.

This is a VERDICT-DECIDING tool (it produces the W7 flip report and validates the lane hooks). Its tests live in
platform/scripts/governance/__tests__/test_flip_detector.py (with mutation proof in test_flip_detector_mutations.py).

  --snapshot <native|abhinandan|kiran|CHART_UUID> [--out FILE.json.gz] [--no-dashas] [--no-daily]
        Capture the current production class-level state of one chart (chart_facts incl. verification tier, chart_divisionals,
        chart_dashas) plus the global panchanga_daily table into one gzip JSON: the pre-rebuild baseline. Prints path + sha256.
  --compare <SNAPSHOT.json.gz> [--against OTHER_SNAPSHOT.json.gz] [--out REPORT.json] [--hooks-dir DIR] [--require-lanes a,b,c]
                               [--no-dashas] [--no-daily] [--allow-not-checked] [--i-know-dashas-are-not-compared]
        Compare the snapshot with production (read-only), or with OTHER_SNAPSHOT (offline, no database), and attribute every
        difference to a lane hook file (all top-level *.json in --hooks-dir).
        Verdict classes (the JSON field "verdict"; never PASS while anything below FAIL / ALERT / NOT_CHECKED exists):
            ALERT        a FORENSIC anchor changed (native chart only); wins over everything
            FAIL         at least one failure class (below) is non-empty
            NOT_CHECKED  nothing failed, but the detector cannot machine-check some declared-or-standing scopes (always the case in
                         production: chart_dashas tier and l1_tajik_varsha_year_lords tier are never compared). Never counted as a pass.
            PASS         nothing failed and nothing is NOT CHECKED (only reachable when the standing NOT CHECKED registry is empty)
        Failure classes: UNDECLARED_CHANGE (no hook declares the changed row/category/column), KIND_MISMATCH (a hook declares the
            category but not this KIND of change), DECLARED_BUT_ABSENT (a non-optional hook entry saw no change at all),
            EXPECTATION_MISMATCH (expected_count violated), DASHA_SHIFT_UNDECLARED (a dasha start shift outside every declared
            range), HOOK_ERROR (invalid hook file or a --require-lanes lane with no hook), EMPTY_READ (a compared table has zero rows in
            either state). Warning class (never fails):
            OPTIONAL_ABSENT (an entry marked "optional": true saw no change).
        Exit codes:
            0  verdict PASS, or verdict NOT_CHECKED with --allow-not-checked (the summary still prints every NOT CHECKED item)
            2  verdict FAIL: STOP THE WAVE, GO TO SS
            3  verdict ALERT: a FORENSIC anchor changed (wins over 2 and 4)
            4  verdict NOT_CHECKED and --allow-not-checked was not passed
            5  READ_ERROR: the read failed or cannot be trusted (psql failure after retries, timeout, incomplete or mis-split result,
               session not read-only). A report with verdict READ_ERROR is still written. Also for --snapshot, including a snapshot whose
               read returned zero rows in a table that must have rows (nothing is written: no snapshot, no .sha256, no temporary file).
            6  REFUSED: --no-dashas / --no-daily together with --require-lanes without --i-know-dashas-are-not-compared; or --snapshot
               onto an existing file (a baseline is never overwritten)
  --validate-hooks [--hooks-dir DIR] [--require-lanes a,b,c] [--out REPORT.json]     lint the hook files only (no database access); exit 0 or 2

Database access (read-only): set FLIP_READER to an executable that takes one SQL SCRIPT as argv[1], runs it in one psql session (every result
set printed) and prints tab-separated rows, no header (a psql wrapper that sources your reader credentials is the usual choice). If unset,
`psql` from PATH is used with the libpq PG* environment. The tables are read in ONE `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY`
transaction (a concurrent build cannot tear the read); only SELECT statements are ever placed in it; PGOPTIONS gets
`-c default_transaction_read_only=on` (the operator's own options are kept) and nothing is read unless the session reports
transaction_read_only = on. Timeout per attempt: $FLIP_TIMEOUT_SEC (default 120 s). Error text is cut to 200 characters with DSNs and
passwords removed. Credentials are never read or printed by this script.
Snapshot store: --out, else $FLIP_SNAPSHOT_DIR, else /Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots.

Hook schema, matching rules, NOT CHECKED semantics and the W7 hand read-back SQL: see FLIP_DETECTOR_README.md next to this file.

L2 (Bodha) extension, opt-in (L2_EXTENSION_VERSION below): add --l2 to --snapshot and --compare (and optionally --l2-tables a,b,c) to also snapshot / compare the 29 L2 tables
of the L2_TABLES registry in the same read-only transaction; hooks may then name those tables. Without --l2 every output is byte-identical to the pre-L2 tool.
See FLIP_DETECTOR_L2_README.md next to this file.
"""
import sys, os, re, json, gzip, glob, hashlib, argparse, collections, subprocess, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_HOOKS_DIR = os.path.join(REPO_ROOT, "00_ARCHITECTURE", "briefs", "suvarna", "exec", "s_l1_attribution_hooks")
TOOL_VERSION = "2.3"
DEFAULT_SNAPSHOT_DIR = "/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots"
CHARTS = {"native": "482012f1-710e-4a25-994a-93821f5871aa", "abhinandan": "1c826d5a-41cb-4450-b4dc-59d440e5f75a", "kiran": "cb73cd3d-9eba-4220-9902-0de91566e980"}
NATIVE = CHARTS["native"]
# A FULL ISO timestamp (date, time, optional seconds / fraction / zone). A text fact that merely starts like one is not a timestamp.
ISO = re.compile(r"^\d{4}-\d\d-\d\d[T ]\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d(:?\d\d)?)?$")
PHANTOM_PREFIX = "362f9f17"  # the dead phantom chart id (CLAUDE.md section B): refused whatever UUID shape it arrives in
CLASS_NUM_KEYS = {"pada", "house_d1", "sign_num", "sign_id", "number", "number_in_lunar_month", "nakshatra_id", "nakshatra_num", "amsa_number",
                  "chalit_house_sripati", "whole_sign_house", "nakshatra_pada", "tithi_id", "vara_id", "yoga_id", "karana_id", "house_num"}
NOT_CLASS_INT = {"longitude_sidereal", "degree_in_sign", "longitude", "longitude_deg"}
AYANS = ("lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical")
ANCHORS = [("SUN sign = Capricorn", ("graha_position", "SUN", "sign"), "Capricorn", AYANS),
           ("MOON nakshatra = Purva Bhadrapada", ("graha_position", "MOON", "nakshatra"), "Purva Bhadrapada", AYANS),
           ("LAGNA sign = Aries", ("graha_position", "LAGNA", "sign"), "Aries", AYANS),
           ("Tithi = Shukla Tritiya", ("panchanga_tithi", "TITHI_BIRTH", "name"), "Shukla Tritiya", ("INVARIANT",)),
           ("Vara = Ravivara", ("panchanga_vara", "VARA_BIRTH", "name"), "Ravivara", ("INVARIANT",)),
           ("Yoga = Shiva", ("panchanga_yoga", "YOGA_BIRTH", "name"), "Shiva", ("INVARIANT",)),
           ("Karana = Garaja", ("panchanga_karana", "KARANA_BIRTH", "name"), "Garaja", ("INVARIANT",))]
DAILY_COLS = ["date", "tithi_id", "paksha", "vara_id", "nakshatra_id", "moon_nakshatra", "yoga_id", "karana_id", "karana_second_id", "tithi_name", "vara", "yoga", "karana"]

TABLES = ("chart_facts", "chart_divisionals", "chart_dashas", "panchanga_daily")
# Tables a hook may name but the detector never reads. An entry on one of these is always NOT CHECKED (never silently passed).
UNCOMPARED_TABLES = ("l1_tajik_varsha_year_lords",)
LEGACY_HOOK_TABLES = TABLES + UNCOMPARED_TABLES  # the tables a hook could name before the L2 extension (kept so the validation message stays byte-identical)
CHANGE_TYPES = ("value", "appeared", "disappeared", "occurrence_count", "tier")
# chart_dashas is compared as a row set only (appeared / disappeared) plus start shifts; its tier is NOT compared.
DASHA_CHANGE_TYPES = ("appeared", "disappeared", "tier")
HOOK_FIELDS = {"lane", "ruling", "pr", "description", "charts", "may_change"}
ENTRY_FIELDS = {"table", "kind", "categories", "fact_keys", "ayanamsha_ids", "systems", "change_types", "expected_direction", "expected_count", "shift_range_sec", "note", "optional"}

# ------------------------------------------------------------------ L2 (Bodha) extension: opt-in behind --l2 (add-only)
# Nothing below changes any output unless --l2 is given. The detector's row model is chart_facts-shaped:
#   [ayanamsha, category, subject, key, text, num, tier]
# For an L2 table the registry entry below builds those 7 columns from the live table:
#   ayanamsha  the row's ayanamsha_id ('INVARIANT' for a table with none)
#   category   the coarse class a hook names in "categories" (signal_type_class, node_type, edge_type, ...)
#   subject, key   together with category the SEMANTIC natural key: NO generated id (signal_id, node_id, edge_id, ... are never in the key)
#   text       'id=<generated identity>|label=value|label=digest|...': the generated identity FIRST, then the content columns that matter.
#              Arrays / jsonb / vectors are compared by a 12-hex md5 digest (the content is never copied into the snapshot).
#              A moved identity (the content it is derived from changed) therefore reads as a 'value' change, not as appeared + disappeared.
#   num        up to a few continuous scores joined by ',' (empty part = NULL). They are NOT compared as class values: see diff_l2_table.
#   tier       verification_pass_status (or the table's own tier-like column)
# Rows that share a semantic key are an occurrence list (the existing occurrence_count mechanism). Adding a table is ONE _l2_reg() call.
L2_EXTENSION_VERSION = "1.0"
L2_COLS = ("ayanamsha", "category", "subject", "key", "text", "num", "tier")
L2_TABLES = {}


def _dg(col):
    """12-hex md5 digest of a column's text form (arrays, jsonb, vectors): content compared by digest, never copied."""
    return f"left(md5(coalesce(({col})::text,'')),12)"


def _clean(expr):
    """Text form with tab / CR / LF replaced (a tab or newline in a value would mis-split the reader's rows and fail the read)."""
    return "regexp_replace(coalesce((" + expr + ")::text,''), E'[\\t\\r\\n]', ' ', 'g')"


def _l2_reg(table, frm, cat, subj, key, ident, content=(), score=(), tier="''", aya="t.ayanamsha_id", must_have_rows=True, unread="", doc=""):
    """Register one L2 table. `frm` uses alias t for the table itself (joins use their own aliases). `content` = [(label, sql expr)]; `score` = [sql expr].
    must_have_rows is True only where the producing writer raises on zero rows or registry target_floor >= 1 guarantees rows for any chart."""
    L2_TABLES[table] = {"from": frm, "category": cat, "subject": subj, "key": key, "ident": ident, "content": list(content), "score": list(score),
                        "tier": tier, "aya": aya, "must_have_rows": bool(must_have_rows), "unread": unread, "doc": doc}


def l2_select_sql(table, chart_id):
    """The single SELECT that reads one L2 table for one chart as 7 chart_facts-shaped columns (the chart id is a validated UUID)."""
    s = L2_TABLES[table]
    cid = normalize_chart_id(chart_id)
    text = _clean("'id=' || coalesce((" + s["ident"] + ")::text,'')" + "".join(f" || '|{lab}=' || coalesce(({expr})::text,'')" for lab, expr in s["content"]))
    num = " || ',' || ".join(f"coalesce(({c})::text,'')" for c in s["score"]) or "''"
    return (f"select {_clean(s['aya'])}, {_clean(s['category'])}, {_clean(s['subject'])}, {_clean(s['key'])}, {text}, {num}, {_clean(s['tier'])} "
            f"from {s['from']} where t.chart_id='{cid}' order by 1,2,3,4,5")


_V = "t.verification_pass_status"
_NL = lambda a: f"coalesce({a}.node_type||':'||{a}.node_subject,'__missing_node__')"  # a node's semantic label (never its node_id)

_l2_reg("bodha_msr_signals", "bodha_msr_signals t",
        cat="t.signal_type_class",
        subj="coalesce(t.varga_id,'') || '|' || coalesce(t.configuration_jsonb->>'fact_subject','') || '|' || coalesce(t.configuration_jsonb->>'fact_key','')",
        key="t.signal_type_id", ident="t.signal_id",
        content=[("valence", "t.valence"), ("producer", "t.producer_asset_id"), ("cites", _dg("t.constituent_facts_array")),
                 ("sysconv", "t.system_convergence_count"), ("consensus", "t.cross_system_consensus_count"),
                 ("contra", _dg("t.contradicts_signals_array")), ("nodecontrib", _dg("t.graph_node_strength_contribution_jsonb"))],
        score=["t.computed_salience", "t.shadbala_norm", "t.dignity_score", "t.deterministic_strength"], tier=_V,
        unread="signal_summary_text, signal_headline_text, classical_sources_*, epistemic_*, the salience sub-factors and modifiers, domain_salience_jsonb, "
               "predicted/active dasha jsonb, remedy_hooks_array, ranks and the other columns outside the spec",
        doc="Key = ayanamsha_id, signal_type_class, signal_type_id (+ varga_id and configuration_jsonb fact_subject/fact_key). Identity = signal_id "
            "(uuid_v5 over the configuration): a config change re-keys the signal id and reads as a value change on the same semantic key. Cites = digest of "
            "constituent_facts_array (moves when L1 fact ids move). Rerank enrichment (sysconv, consensus, contra, nodecontrib) is in the text.")
_l2_reg("bodha_signal_embeddings", "bodha_signal_embeddings t left join bodha_msr_signals s on s.signal_id=t.signal_id",
        cat="coalesce(s.signal_type_class,'__orphan__')", subj="coalesce(t.embedding_model,'') || '|' || coalesce(t.embedding_model_version,'')",
        key="coalesce(s.signal_type_id,'__orphan__:'||t.signal_id::text)", ident="t.embedding_id",
        content=[("signal", "t.signal_id"), ("vec", _dg("t.embedding_vec")), ("input", _dg("t.embedding_input_summary"))],
        unread="the embedding vector itself (compared by a 12-hex md5 of its text form only), the input summary text (digest only)",
        doc="Semantic key = the embedded signal's own key (joined from bodha_msr_signals; an embedding whose signal is gone is category __orphan__ keyed by the "
            "dangling signal id) + the model. Identity = embedding_id; vec = digest of the vector.")
_l2_reg("bodha_cgm_nodes", "bodha_cgm_nodes t",
        cat="t.node_type", subj="t.node_subject", key="t.snapshot_type", ident="t.node_id",
        content=[("dignity", "t.dignity_state"), ("domain", "t.primary_domain"), ("hub", "t.hub_flag"), ("msr", _dg("t.msr_signal_id")),
                 ("pos", _dg("t.position_in_chart_jsonb")), ("constituents", _dg("t.configuration_constituents_array")), ("degin", "t.degree_in"), ("degout", "t.degree_out")],
        score=["t.strength_score", "t.pagerank_score", "t.betweenness_centrality", "t.eigenvector_centrality", "t.harmonic_centrality"], tier=_V,
        unread="node_embedding_vec, node_label_human, clustering/closeness/core metrics, domain_affiliations, cluster membership, ephemeris_audit_jsonb",
        doc="Key = ayanamsha_id, node_type, node_subject, snapshot_type (the table's own unique key minus build_id). Identity = node_id (deterministic from the key).")
_l2_reg("bodha_cgm_edges",
        "bodha_cgm_edges t left join bodha_cgm_nodes nf on nf.node_id=t.from_node_id left join bodha_cgm_nodes nt on nt.node_id=t.to_node_id",
        cat="t.edge_type", subj="t.snapshot_type || '|' || " + _NL("nf"), key=_NL("nt"), ident="t.edge_id",
        content=[("valence", "t.valence"), ("direction", "t.direction"), ("cancelled", "t.cancelled_flag"), ("msr", _dg("t.underlying_msr_signal_ids_array")),
                 ("facts", _dg("t.constituent_fact_ids_array")), ("vichara", _dg("t.constituent_ga_vichara_ids_array")), ("consensus", "t.cross_system_consensus_count")],
        score=["t.computed_strength", "t.intrinsic_strength", "t.edge_betweenness"], tier=_V,
        unread="edge_properties_jsonb, affected_domains, active_dasha_periods_jsonb, cancelled_by_jsonb, citation text, graph library versions",
        doc="Key = ayanamsha_id, edge_type, snapshot_type, from-node label, to-node label (node_type:node_subject, joined; never node ids). Identity = edge_id. "
            "msr/facts/vichara = digests of the cited L1/L2 id arrays (they move when the cited ids move).")
_l2_reg("bodha_cgm_paths",
        "bodha_cgm_paths t left join bodha_cgm_nodes nf on nf.node_id=t.from_node_id left join bodha_cgm_nodes nt on nt.node_id=t.to_node_id",
        cat="t.path_type", subj="t.snapshot_type || '|' || " + _NL("nf"), key=_NL("nt"), ident="t.path_id",
        content=[("len", "t.path_length"), ("final", "t.is_final_dispositor"), ("conv", "t.convergence_count"), ("nodes", _dg("t.path_node_ids_array")),
                 ("edges", _dg("t.path_edge_ids_array"))],
        score=["t.path_strength"], tier=_V, unread="path_label_human, citation text",
        doc="Key = ayanamsha_id, path_type, snapshot_type, from/to node labels. Identity = path_id; the node/edge chains are digests.")
_l2_reg("bodha_cgm_motifs", "bodha_cgm_motifs t",
        cat="t.motif_class", subj="t.snapshot_type || '|' || t.motif_name", key="t.fingerprint_hash", ident="t.motif_id",
        content=[("nodes", _dg("t.involved_node_ids_array")), ("edges", _dg("t.involved_edge_ids_array")), ("cite", "t.classical_citation_id")],
        score=["t.motif_strength"], tier=_V, must_have_rows=False, unread="citation text",
        doc="Key = ayanamsha_id, motif_class, snapshot_type, motif_name, fingerprint_hash. Legitimately empty for some charts (target_floor 0).")
_l2_reg("bodha_cdlm_cells", "bodha_cdlm_cells t",
        cat="t.snapshot_type",
        subj="coalesce(t.tradition_view_id,'')||'|'||coalesce(t.dynamic_system_id,'')||'|'||coalesce(t.dynamic_maha_lord,'')||'|'||coalesce(t.dynamic_antar_lord,'')",
        key="coalesce(t.domain_row,'')||'|'||coalesce(t.domain_col,'')||'|'||coalesce(t.subdomain_row,'')||'|'||coalesce(t.subdomain_col,'')", ident="t.cell_id",
        content=[("sharedsig", "t.shared_signal_count"), ("sharedfac", "t.shared_factor_count"), ("contradict", "t.contradicting_signal_pairs_count"),
                 ("sigids", _dg("t.shared_signal_ids_array")), ("asym", "t.asymmetric_linkage_flag"), ("domaincontra", "t.cross_domain_contradiction_flag")],
        score=["t.net_linkage_strength", "t.computed_linkage_strength", "t.shared_signal_salience_sum", "t.positive_contribution", "t.negative_contribution"], tier=_V,
        unread="the other jsonb/array columns (remedy, narrative, bridge seeds, predicted windows), ranks, evolution gradient",
        doc="Key = ayanamsha_id, snapshot_type, tradition view + dynamic system/lords, domain/subdomain row and column (the table's unique key minus build_id).")
_l2_reg("bodha_triangulation", "bodha_triangulation t",
        cat="t.question_class", subj="''", key="t.tradition", ident="t.triangulation_id",
        content=[("formula", "t.formula_version"), ("sigids", _dg("t.signal_ids")), ("inputs", _dg("t.verdict_inputs"))],
        score=["t.concordance_score"], must_have_rows=False, doc="Key = ayanamsha_id, question_class, tradition. Identity = triangulation_id; signal_ids by digest.")
_l2_reg("bodha_contradictions",
        "bodha_contradictions t left join bodha_msr_signals sa on sa.signal_id=t.signal_a_id left join bodha_msr_signals sb on sb.signal_id=t.signal_b_id",
        cat="t.tension_class", subj="coalesce(sa.signal_type_id,'__missing_signal__')", key="coalesce(sb.signal_type_id,'__missing_signal__')", ident="t.contradiction_id",
        content=[("a", "t.signal_a_id"), ("b", "t.signal_b_id"), ("domains", _dg("t.domains_affected_array")), ("basis", _dg("t.tension_basis_jsonb"))],
        score=["t.combined_salience"], tier=_V, must_have_rows=False,
        unread="resolution_hint_jsonb, citation text",
        doc="Key = ayanamsha_id, tension_class, signal_type_id of signal A and of signal B (joined). Identity = contradiction_id plus both signal ids (so a moved "
            "signal id is visible). Legitimately empty for some charts.")
_l2_reg("bodha_convergence", "bodha_convergence t",
        cat="t.snapshot_type", subj="coalesce(t.dynamic_system_id,'')||'|'||coalesce(t.dynamic_maha_lord,'')||'|'||coalesce(t.dynamic_antar_lord,'')", key="t.domain",
        ident="t.convergence_id",
        content=[("count", "t.convergence_count"), ("crosstrad", "t.cross_tradition_count"), ("contra", "t.contradiction_count"), ("top", _dg("t.top_signal_ids_array"))],
        score=["t.convergence_score", "t.salience_weighted_sum", "t.salience_max"], tier=_V, must_have_rows=False,
        unread="tradition_breakdown_jsonb, classical_sources_jsonb", doc="Key = ayanamsha_id, snapshot_type, dynamic system/lords, domain.")
_l2_reg("bodha_rm_resonances", "bodha_rm_resonances t",
        cat="t.snapshot_type", subj="''", key="t.graha", ident="t.resonance_id",
        content=[("class", "t.remedy_priority_class"), ("yk", "t.is_yoga_karaka_flag"), ("ck", "t.is_chara_karaka_role"), ("rank", "t.weakest_rank_in_chart"),
                 ("doshas", _dg("t.associated_doshas_array")), ("motifs", _dg("t.associated_motifs_array")), ("cells", _dg("t.associated_cdlm_cells_array"))],
        score=["t.resonance_score", "t.weakness_score", "t.contradiction_factor", "t.domain_burden", "t.motif_burden"], tier=_V, unread="ephemeris_audit_jsonb, citation text",
        doc="Key = ayanamsha_id, snapshot_type, graha.")
_l2_reg("bodha_mechanisms", "bodha_mechanisms t",
        cat="t.mechanism_class", subj="t.snapshot_type || '|' || t.mechanism_name", key="t.fingerprint_hash", ident="t.mechanism_id",
        content=[("valence", "t.valence"), ("nodes", _dg("t.member_node_ids_array")), ("edges", _dg("t.member_edge_ids_array")), ("vichara", _dg("t.constituent_ga_vichara_ids_array")),
                 ("motif", "t.source_motif_id"), ("domains", _dg("t.domains_affected_array"))],
        score=["t.edge_strength_avg", "t.edge_strength_min", "t.edge_strength_max"], tier=_V, unread="centrality_summary_jsonb, citation text",
        doc="Key = ayanamsha_id, mechanism_class, snapshot_type, mechanism_name, fingerprint_hash. Identity = mechanism_id; vichara = digest of cited chart_vichara ids.")
_l2_reg("bodha_discoveries", "bodha_discoveries t",
        cat="t.discovery_class", subj="coalesce(t.discovery_subsystem,'')", key="coalesce(t.novelty_class_id,'')||'|'||coalesce(array_to_string(t.affected_domains_array,','),'')",
        ident="t.discovery_id",
        content=[("refs", _dg("t.constituent_refs_jsonb")), ("corroboration", "t.corroboration_count"), ("crosssub", "t.cross_subsystem_root"), ("novelty", "t.novelty_class")],
        score=["t.non_obviousness_score", "t.consequence_score", "t.composite_discovery_rank"], must_have_rows=False,
        unread="reasoning_chain_jsonb, the reading texts (surface/depth/hypothesis), falsifier and calibration jsonb, provenance",
        doc="No natural unique key exists (discovery_id embeds the cited signal ids): semantic key = class, subsystem, novelty class + affected domains; many rows "
            "share a key (an occurrence list); identity = discovery_id, so a re-cited discovery reads as a value change.")
_l2_reg("bodha_anomalies", "bodha_anomalies t",
        cat="t.anomaly_type", subj="coalesce(t.discovery_subsystem,'')", key="coalesce(t.anomaly_metric,'')", ident="t.anomaly_id",
        content=[("subject", _dg("t.subject_ref_jsonb")), ("gate", "t.meaningfulness_gate_result")],
        score=["t.anomaly_value", "t.chart_baseline_value", "t.sigma_from_baseline"], must_have_rows=False,
        doc="Semantic key = anomaly_type, subsystem, metric (many rows share it); identity = anomaly_id (embeds the subject reference).")
_l2_reg("bodha_pratijna", "bodha_pratijna t",
        cat="'pratijna'", subj="''", key="t.event_class_id", ident="t.pratijna_id",
        content=[("status", "t.status"), ("support", _dg("t.supporting_signal_ids")), ("contradict", _dg("t.contradicting_signal_ids")), ("derivation", _dg("t.derivation")),
                 ("vargaconf", _dg("t.varga_confirmation"))],
        score=["t.grade", "t.occurrence_grade", "t.condition_grade"], must_have_rows=False,
        doc="Key = ayanamsha_id, event_class_id; the status is content, so a status flip reads as a value change. target_floor 0.")
_l2_reg("synthesis_quality_scorecard", "synthesis_quality_scorecard t",
        cat="'scorecard'", subj="''", key="'row'", ident="t.scorecard_id", aya="'INVARIANT'",
        content=[("msr", "t.msr_signal_count"), ("cells", "t.cdlm_cell_count"), ("nodes", "t.cgm_node_count"), ("edges", "t.cgm_edge_count"), ("resonances", "t.rm_resonance_count"),
                 ("prescriptions", "t.rm_prescription_count"), ("embeddings", "t.embedding_count"), ("convergence", "t.convergence_count"),
                 ("contradictions", "t.contradiction_count"), ("divergent", "t.divergent_flagged_count"), ("orphans", "t.unresolved_constituent_facts_count"),
                 ("trap1", "t.trap1_authority_inversion_count"), ("trap2", "t.trap2_narration_leak_count"), ("l1proj", "t.l1_assets_projected_count"),
                 ("nothreshold", "t.msr_no_threshold_drop_flag"), ("lel", "t.lel_zero_leak_pass"), ("nopre", "t.no_pre_answer_pass"), ("pillars", "t.pillars_meet_reachability_pass"),
                 ("ledger", "t.ledger_independence_pass"), ("discovery", "t.discovery_not_fabricated_pass")],
        score=["t.two_pass_verified_pct", "t.documented_approximation_pct", "t.msr_citation_ref_coverage_pct"], must_have_rows=True,
        unread="formula-version strings, l1_assets_projected_array, notes", doc="One row per chart; there is no ayanamsha, so ayanamsha = INVARIANT.")
_l2_reg("bodha_cgm_sub_graphs", "bodha_cgm_sub_graphs t",
        cat="t.subgraph_type", subj="coalesce(t.subgraph_label,'')", key="coalesce(t.classical_archetype_match,'')", ident="t.subgraph_id",
        content=[("nodes", _dg("t.node_ids_array")), ("edges", _dg("t.edge_ids_array")), ("centroid", "t.subgraph_centroid_node_id")],
        score=["t.subgraph_density"], tier=_V, must_have_rows=False, unread="graphml/gexf exports, representative_path_jsonb")
_l2_reg("bodha_cgm_chart_topology_summary", "bodha_cgm_chart_topology_summary t",
        cat="'topology'", subj="t.snapshot_type", key="'row'", ident="t.summary_id",
        content=[("nodes", "t.total_nodes"), ("edges", "t.total_edges"), ("triangles", "t.triangle_count"), ("scc", "t.strongly_connected_components_count"),
                 ("diameter", "t.graph_diameter"), ("fingerprint", "t.graph_fingerprint_hash"), ("isolated", _dg("t.isolated_node_ids_array")),
                 ("hubs", _dg("t.top_5_hub_nodes_jsonb"))],
        score=["t.graph_density", "t.hub_dominance_score", "t.fragmentation_score"], tier=_V, must_have_rows=False,
        unread="the embedding vector, graphml/gexf exports, story arcs, central-node jsonb")
_l2_reg("bodha_cdlm_chart_summary", "bodha_cdlm_chart_summary t",
        cat="'summary'", subj="coalesce(t.tradition_view_id,'')||'|'||coalesce(t.dynamic_system_id,'')||'|'||coalesce(t.dynamic_maha_lord,'')||'|'||coalesce(t.dynamic_antar_lord,'')",
        key="t.snapshot_type", ident="t.summary_id",
        content=[("typology", "t.chart_typology_class"), ("bridges", "t.bridge_link_count"), ("asym", "t.asymmetric_link_count"), ("dom3", _dg("t.dominant_3_domains_array")),
                 ("weak3", _dg("t.weakest_3_domains_array")), ("markers", _dg("t.pattern_cluster_markers_jsonb"))],
        score=["t.total_chart_linkage", "t.contradiction_density"], tier=_V, must_have_rows=False, unread="house/karaka strength jsonb")
_l2_reg("bodha_cdlm_domain_rollups", "bodha_cdlm_domain_rollups t",
        cat="'rollup'", subj="t.snapshot_type||'|'||coalesce(t.tradition_view_id,'')||'|'||coalesce(t.dynamic_system_id,'')||'|'||coalesce(t.dynamic_maha_lord,'')||'|'||coalesce(t.dynamic_antar_lord,'')",
        key="t.domain", ident="t.rollup_id",
        content=[("signals", "t.signal_count_for_domain"), ("markers", _dg("t.pattern_markers_for_domain_array")), ("top3", _dg("t.top_3_linked_domains_jsonb"))],
        score=["t.total_inbound_linkage", "t.total_outbound_linkage", "t.diagonal_density", "t.contradiction_density"], tier=_V, must_have_rows=False)
_l2_reg("bodha_cdlm_pattern_clusters", "bodha_cdlm_pattern_clusters t",
        cat="t.pattern_marker_type", subj="t.snapshot_type||'|'||coalesce(t.tradition_view_id,'')", key="coalesce(array_to_string(t.involved_domains_array,','),'')", ident="t.pattern_id",
        content=[("cells", _dg("t.involved_cells_array")), ("signals", _dg("t.involved_signals_array")), ("archetype", "t.classical_archetype_match"),
                 ("outcome", "t.predicted_outcome_class"), ("contradicts", _dg("t.contradicts_other_patterns_array"))],
        score=["t.cluster_strength_total"], tier=_V, must_have_rows=False, unread="remedy theme, subgraph seed, active dasha windows jsonb")
_l2_reg("bodha_chart_gestalt", "bodha_chart_gestalt t",
        cat="'gestalt'", subj="''", key="'row'", ident="t.gestalt_id",
        content=[("formula", "t.gestalt_formula_version"), ("threads", _dg("t.defining_threads_jsonb")), ("dynamics", _dg("t.central_dynamics_ids")), ("pivots", _dg("t.pivot_ids")),
                 ("gravity", _dg("t.center_of_gravity_node_ids")), ("verdicts", _dg("t.domain_verdict_map_jsonb")), ("headline", _dg("t.headline_jsonb")),
                 ("watch", _dg("t.watch_list_jsonb")), ("outliers", _dg("t.outliers_jsonb")), ("contested", _dg("t.contested_areas_jsonb"))],
        score=["t.headline_confidence"], must_have_rows=False, unread="central_question_jsonb, headline_epistemic_jsonb, zoom_spine_jsonb")
_l2_reg("bodha_question_lenses", "bodha_question_lenses t",
        cat="'lens'", subj="''", key="t.question_type", ident="t.lens_id",
        content=[("template", "t.lens_template_version"), ("formula", "t.lens_formula_version"), ("points", "t.points_only_assertion"),
                 ("elements", _dg("t.template_element_ids_jsonb")), ("wildcards", _dg("t.wildcard_element_ids_jsonb")), ("ranked", _dg("t.all_relevant_ranked_jsonb"))],
        tier=_V, must_have_rows=False)
_l2_reg("bodha_grounding_matches",
        "bodha_grounding_matches t left join bodha_msr_signals s on s.signal_id::text=t.target_id "
        "left join ga_yoga_firings y on t.target_kind<>'msr_signal' and y.id::text=t.target_id",
        cat="t.target_kind", subj="coalesce(t.matched_rule_id,'')", key="coalesce(s.signal_type_id,y.yoga_canonical_id,'__unresolved__:'||t.target_id)", ident="t.match_id",
        content=[("target", "t.target_id"), ("granularity", "t.citation_granularity"), ("chain", _dg("t.derivation_chain")), ("evidence", _dg("t.grounding_evidence_jsonb"))],
        tier="t.grounding_tier", must_have_rows=False,
        doc="tier = grounding_tier (pratyaksa / yukti / sruti). Key = target_kind, matched rule, the grounded signal's type id (or the yoga canonical id).")
_l2_reg("bodha_rm_chart_summary", "bodha_rm_chart_summary t",
        cat="'summary'", subj="''", key="t.snapshot_type", ident="t.summary_id",
        content=[("intensity", "t.recommended_intensity_class"), ("doshas", "t.total_active_dosha_count"), ("primary", "t.primary_dosha_class"), ("typology", "t.remedy_chart_typology"),
                 ("review", "t.acharya_review_required_count"), ("top3", _dg("t.top_3_resonance_targets_jsonb")), ("top10", _dg("t.top_10_priority_prescriptions_jsonb")),
                 ("phases", _dg("t.recommended_remedy_phase_sequence_jsonb"))], tier=_V, must_have_rows=False,
        unread="chart_remedy_embedding_vec, feasibility and cross-tradition jsonb")
_l2_reg("bodha_rm_dasha_windowed_prescriptions", "bodha_rm_dasha_windowed_prescriptions t",
        cat="coalesce(t.dasha_system,'')", subj="coalesce(t.dasha_level,'')||'|'||coalesce(t.dasha_lord,'')", key="t.window_start_iso::text", ident="t.window_prescription_id",
        content=[("end", "t.window_end_iso"), ("base", "t.base_prescription_id"), ("phase", "t.phase_within_window"), ("schedule", _dg("t.schedule_jsonb"))],
        score=["t.window_intensity_multiplier"], tier=_V, must_have_rows=False, doc="A tombstone table: bo_upaya only deletes from it.")
_l2_reg("bodha_rm_dosha_remedy_bundles", "bodha_rm_dosha_remedy_bundles t",
        cat="'bundle'", subj="''", key="t.dosha_class", ident="t.bundle_id",
        content=[("active", "t.active_flag"), ("cancellations", "t.cancellation_count"), ("prescriptions", _dg("t.prescription_ids_in_bundle_array")),
                 ("summary", _dg("t.bundle_summary_jsonb")), ("sources", _dg("t.classical_sources_jsonb"))],
        score=["t.intensity_score"], tier=_V, must_have_rows=False)
_l2_reg("bodha_rm_pattern_remedies", "bodha_rm_pattern_remedies t",
        cat="t.source_kind", subj="''", key="coalesce(t.remedy_theme,'')", ident="t.pattern_remedy_id",
        content=[("source", "t.source_id"), ("prescriptions", _dg("t.prescription_ids_array"))],
        score=["t.theme_strength", "t.cross_tradition_unanimity_score"], tier=_V, must_have_rows=False)
_l2_reg("bodha_rm_remedy_prescriptions", "bodha_rm_remedy_prescriptions t",
        cat="coalesce(t.remedy_category,'')", subj="t.snapshot_type||'|'||coalesce(t.target_graha,'')||'|'||coalesce(t.tradition,'')||'|'||coalesce(t.sub_tradition,'')",
        key="coalesce(t.remedy_id_g27,'')", ident="t.prescription_id",
        content=[("strength", "t.classical_strength_rating"), ("review", "t.requires_acharya_review_flag"), ("resonance", "t.target_resonance_id"), ("motif", "t.targets_motif_id"),
                 ("cell", "t.targets_cell_id"), ("dosha", "t.targets_dosha_class"), ("corroboration", "t.cross_tradition_corroboration_count"), ("phase", "t.phase_sequence_class"),
                 ("detail", _dg("t.prescription_detail_jsonb")), ("counter", _dg("t.counter_indications_array")), ("prereq", _dg("t.prerequisite_prescription_ids_array"))],
        score=["t.resonance_match_score", "t.feasibility_score", "t.estimated_time_minutes_daily"], tier=_V, must_have_rows=True,
        unread="prescription_embedding_vec, geometry/pilgrimage/cost jsonb, recommended hora/choghadiya arrays, substitute options, labels")
# must_have_rows is True only for: bodha_msr_signals, bodha_signal_embeddings, bodha_cgm_nodes, bodha_cgm_edges, bodha_cgm_paths, bodha_cdlm_cells,
# bodha_rm_resonances, bodha_mechanisms, synthesis_quality_scorecard, bodha_rm_remedy_prescriptions (writer raises on zero rows, or registry target_floor >= 1).
for _t in ("bodha_cdlm_cells", "bodha_cgm_edges", "bodha_cgm_nodes", "bodha_cgm_paths", "bodha_mechanisms", "bodha_rm_resonances", "bodha_signal_embeddings", "bodha_msr_signals"):
    L2_TABLES[_t]["must_have_rows"] = True

HOOK_TABLES = LEGACY_HOOK_TABLES + tuple(L2_TABLES)  # additive: a hook may also name an L2 table (judged only when that table was compared)

# Verdict classes, failure classes, warning class (see the module docstring).
V_ALERT, V_FAIL, V_NOT_CHECKED, V_PASS = "ALERT", "FAIL", "NOT_CHECKED", "PASS"
F_UNDECLARED, F_KIND, F_ABSENT, F_EXPECT, F_DASHA, F_HOOK = ("UNDECLARED_CHANGE", "KIND_MISMATCH", "DECLARED_BUT_ABSENT", "EXPECTATION_MISMATCH",
                                                             "DASHA_SHIFT_UNDECLARED", "HOOK_ERROR")
F_EMPTY = "EMPTY_READ"
FAILURE_CLASSES = (F_UNDECLARED, F_KIND, F_ABSENT, F_EXPECT, F_DASHA, F_HOOK, F_EMPTY)
REPORT_REQUIRED_KEYS = ("failures", "failure_counts", "not_checked", "chart_id")
W_OPTIONAL_ABSENT = "OPTIONAL_ABSENT"
EXIT_PASS, EXIT_FAIL, EXIT_ALERT, EXIT_NOT_CHECKED = 0, 2, 3, 4
EXIT_READ_ERROR = 5  # the read itself failed or cannot be trusted (psql failure, timeout, incomplete or malformed read, session not read-only)
EXIT_REFUSED = 6     # the invocation was refused (a dasha/daily skip together with --require-lanes without --i-know-dashas-are-not-compared; a baseline overwrite)
RO_PGOPTIONS = "-c default_transaction_read_only=on"

# The tier changes this detector cannot machine-check. They are printed on EVERY compare as NOT CHECKED: the detector never reads
# chart_dashas.verification_pass_status nor l1_tajik_varsha_year_lords, so it can neither confirm nor refute a hook about them.
_OTHER = "W7 hand read-back: 'Other tables the detector never reads' in FLIP_DETECTOR_README.md"
STANDING_NOT_CHECKED = (
    {"id": "chart_dashas.tier", "table": "chart_dashas", "what": "chart_dashas verification_pass_status (mudda, narayana, yogini, ashtottari, chara_karaka, naisargika, vimshottari tier)",
     "reason": "the detector never compares the dasha tier column (when chart_dashas is compared at all, only row sets and start shifts)", "readback": "W7 hand read-back: chart_dashas tier SQL in FLIP_DETECTOR_README.md"},
    {"id": "l1_tajik_varsha_year_lords.tier", "table": "l1_tajik_varsha_year_lords", "what": "l1_tajik_varsha_year_lords verification_pass_status",
     "reason": "the table is not one of the four tables the detector reads", "readback": "W7 hand read-back: l1_tajik_varsha_year_lords tier SQL in FLIP_DETECTOR_README.md"},
    {"id": "chart_vichara", "table": "chart_vichara", "what": "chart_vichara (ga_vichara rows: counts, dedupe, sorted constituent_fact_ids, leverage as-of)",
     "reason": "the table is not one of the four tables the detector reads: an empty flip report says nothing about ga_vichara",
     "readback": "W7: run evidence/ga_vichara_writer_ACCEPTANCE.sql (it exists only on PR 2970's branch until the S-L1 integration brings it into s_l1_attribution_hooks/evidence/); every row must read ok = t"},
    {"id": "ga_yoga_firings.strength", "table": "ga_yoga_firings", "what": "ga_yoga_firings strength (constituent_bala_v1)", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "bodha_msr_signals", "table": "bodha_msr_signals", "what": "bodha_msr_signals (shadbala_norm)", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "bodha_rm_resonances", "table": "bodha_rm_resonances", "what": "bodha_rm_resonances", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "ga_condition_composite", "table": "ga_condition_composite", "what": "ga_condition_composite", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "ga_medical", "table": "ga_medical", "what": "ga_medical", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "ga_vastu_*", "table": "ga_vastu_*", "what": "ga_vastu_* tables", "reason": "tables not read by the detector", "readback": _OTHER},
    {"id": "ga_prashna_*", "table": "ga_prashna_*", "what": "ga_prashna_* tables", "reason": "tables not read by the detector", "readback": _OTHER},
    {"id": "prashna_charts", "table": "prashna_charts", "what": "prashna_charts", "reason": "table not read by the detector", "readback": _OTHER},
)


# ------------------------------------------------------------------ read-only reader
class ReadError(Exception):
    """The read failed or cannot be trusted. The CLI maps it to exit 5 (READ_ERROR) with a report; the message is already scrubbed."""


def _scrub(text):
    """At most 200 characters of a process error, with anything that looks like a DSN or a password removed first."""
    t = str(text or "").strip()
    t = re.sub(r"(?i)(postgres(?:ql)?://)\S+", r"\1***", t)
    t = re.sub(r"(?i)\b(password|passwd|pwd|pgpassword|secret|token)\b(\s*[=:]\s*)\S+", r"\1\2***", t)
    return t[:200]


def _read_env():
    env = dict(os.environ)
    env["PGOPTIONS"] = (env.get("PGOPTIONS", "") + " " + RO_PGOPTIONS).strip()  # the operator's own options are kept
    return env


def _timeout_sec():
    try:
        return float(os.environ.get("FLIP_TIMEOUT_SEC", "120"))
    except ValueError:
        return 120.0


def _select_only(sql):
    if not re.match(r"^\s*select\b", sql, re.I) or ";" in sql.strip().rstrip(";"):
        raise RuntimeError("flip_detector is read-only: only a single SELECT statement is allowed")


def _exec(text, script):
    """Run one SQL string (script=False: -c) or one SQL script (script=True: psql reads it on stdin, so every result set is printed)."""
    reader = os.environ.get("FLIP_READER")
    if reader:
        cmd, inp = [reader, text], None
    elif script:
        cmd, inp = ["psql", "-X", "-q", "-A", "-t", "-F", "\t", "-v", "ON_ERROR_STOP=1", "-f", "-"], text
    else:
        cmd, inp = ["psql", "-X", "-A", "-F", "\t", "-t", "-c", text], None
    return subprocess.run(cmd, input=inp, capture_output=True, text=True, env=_read_env(), timeout=_timeout_sec())


def _run(text, script, retries):
    last = ""
    for i in range(retries):
        try:
            r = _exec(text, script)
            if r.returncode == 0:
                return r.stdout
            last = _scrub(r.stderr) or f"exit status {r.returncode}"
        except subprocess.TimeoutExpired:
            last = f"timed out after {_timeout_sec():g} s"
        except OSError as ex:
            last = _scrub(f"cannot start the reader: {ex}")
        if i < retries - 1:
            time.sleep(5 * (i + 1))  # transient connection loss / statement timeout on the shared reader
    raise ReadError(f"read failed after {retries} attempts: {last}")


def q(sql, retries=4):
    """One SELECT, tab-separated rows. Read-only is requested through PGOPTIONS on every call."""
    _select_only(sql)
    return [ln.split("\t") for ln in _run(sql, False, retries).splitlines() if ln != ""]


SENTINEL = re.compile(r"^@@END:([a-z_]+)@@$")


def q_txn(named, retries=4):
    """ONE repeatable-read, read-only transaction in ONE psql session: BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY; every SELECT; COMMIT.
    All tables are therefore read from one snapshot (a concurrent build cannot tear it). `named` is [(name, select)]; each result set is
    followed by an @@END:name@@ marker row, and a missing marker (a wrapper that returned only the last result) is a ReadError.
    Returns {name: [row, ...]} with rows split on tabs."""
    script = ["BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY"]
    for name, sql in named:
        _select_only(sql)
        script += [sql.strip().rstrip(";"), f"select '@@END:{name}@@'"]
    script.append("COMMIT")
    out = _run(";\n".join(script) + ";\n", True, retries)
    got, buf, order = {}, [], []
    lines = out.splitlines()
    if lines and lines[0] == "BEGIN":      # psql command tags (printed unless -q; a wrapper may print them): never data
        lines = lines[1:]
    if lines and lines[-1] == "COMMIT":
        lines = lines[:-1]
    for ln in lines:
        m = SENTINEL.match(ln)
        if m:
            got[m.group(1)] = buf
            order.append(m.group(1))
            buf = []
        else:
            buf.append(ln.split("\t"))
    want = [n for n, _ in named]
    if order != want:
        raise ReadError(f"incomplete read: expected result sets {want}, got {order} (the reader must print every result set of a script)")
    return got


def _rows(got, name, ncols):
    rows = got[name]
    for r in rows:
        if len(r) != ncols:
            raise ReadError(f"{name}: a row has {len(r)} columns, expected {ncols} (a tab or newline inside a text value mis-splits rows); the read cannot be trusted")
    return rows


UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def normalize_chart_id(c):
    """The ONE place a chart id is normalised (trim, braces, lower case) and validated as a UUID; anything else raises ValueError.
    Everything that interpolates a chart id into SQL, compares it with NATIVE or matches a hook 'charts' prefix goes through here."""
    t = str(c).strip().strip("{}").strip().lower()
    if t.replace("-", "").startswith(PHANTOM_PREFIX):
        raise ValueError("refused: the dead phantom chart id 362f9f17 is never read or compared")
    if not UUID_RE.match(t):
        raise ValueError(f"not a chart UUID: {str(c)[:60]!r}")
    return t


def resolve(c):
    key = str(c).strip().lower()
    return normalize_chart_id(CHARTS.get(key, c))


def ts_parse(s):
    s = s.replace(" ", "T")
    if s.endswith("+00"):
        s += ":00"
    return datetime.fromisoformat(s)


# ------------------------------------------------------------------ hooks
class HookError(Exception):
    pass


def validate_hook(h, fname):
    errs = []
    if not isinstance(h, dict):
        return [f"{fname}: top level must be an object"]
    unknown = set(h) - HOOK_FIELDS
    if unknown:
        errs.append(f"{fname}: unknown top-level fields {sorted(unknown)}")
    stem = os.path.splitext(os.path.basename(fname))[0]
    if h.get("lane") != stem:
        errs.append(f"{fname}: 'lane' must equal the file stem '{stem}'")
    if not isinstance(h.get("ruling"), str) or not h.get("ruling"):
        errs.append(f"{fname}: 'ruling' (the name shown in attribution) is required")
    if not isinstance(h.get("description"), str) or not h.get("description").strip():
        errs.append(f"{fname}: 'description' is required")
    pr = h.get("pr")
    if not ((isinstance(pr, str) and pr.strip()) or (isinstance(pr, int) and not isinstance(pr, bool) and pr > 0)):
        errs.append(f"{fname}: 'pr' (PR number or branch of the fix) is required")
    mc = h.get("may_change")
    if not isinstance(mc, list) or not mc:
        errs.append(f"{fname}: 'may_change' must be a non-empty list (an empty placeholder hook is not allowed; leave the file absent instead)")
        return errs
    for i, e in enumerate(mc):
        w = f"{fname} may_change[{i}]"
        if not isinstance(e, dict):
            errs.append(f"{w}: must be an object")
            continue
        unknown = set(e) - ENTRY_FIELDS
        if unknown:
            errs.append(f"{w}: unknown fields {sorted(unknown)}")
        if e.get("table") not in HOOK_TABLES:
            errs.append(f"{w}: 'table' must be one of {LEGACY_HOOK_TABLES}")
        if "optional" in e and not isinstance(e["optional"], bool):
            errs.append(f"{w}: 'optional' must be true or false")
        if e.get("kind") == "dasha_shift":
            if e.get("table") != "chart_dashas":
                errs.append(f"{w}: kind dasha_shift requires table chart_dashas")
            sr = e.get("shift_range_sec")
            if not (isinstance(sr, list) and len(sr) == 2 and all(isinstance(x, (int, float)) for x in sr) and sr[0] <= sr[1]):
                errs.append(f"{w}: dasha_shift needs shift_range_sec [lo, hi] (seconds, current minus snapshot)")
            if not (isinstance(e.get("systems"), list) and e.get("systems")):
                errs.append(f"{w}: dasha_shift needs a non-empty 'systems' list (exact system_id)")
            if "expected_count" in e:
                errs.append(f"{w}: 'expected_count' is not supported on a dasha_shift entry (it would be ignored); use 'optional' or leave the entry without a count")
        else:
            if e.get("kind") not in (None, "change"):
                errs.append(f"{w}: 'kind' must be 'change' (default) or 'dasha_shift'")
            cats = e.get("categories")
            if not (isinstance(cats, list) and cats and all(isinstance(c, str) and c for c in cats)):
                errs.append(f"{w}: 'categories' must be a non-empty list of EXACT names (no patterns): fact_category / panchanga_daily column / chart_dashas system_id")
            elif any(re.search(r"[*?\[\]()|^$\\]", c) for c in cats):
                errs.append(f"{w}: 'categories' must be exact names, not patterns")
        for f in ("fact_keys", "ayanamsha_ids"):
            if f in e and not (isinstance(e[f], list) and e[f] and all(isinstance(x, str) and x for x in e[f])):
                errs.append(f"{w}: '{f}' must be a NON-EMPTY list of exact strings (omit the field to match all; an empty list would broaden, not narrow)")
        ct = e.get("change_types")
        if ct is not None and not (isinstance(ct, list) and ct and set(ct) <= set(CHANGE_TYPES)):
            errs.append(f"{w}: 'change_types' must be a non-empty subset of {CHANGE_TYPES}")
        elif ct and e.get("table") == "chart_dashas" and e.get("kind") != "dasha_shift" and not set(ct) <= set(DASHA_CHANGE_TYPES):
            errs.append(f"{w}: chart_dashas row-set entries may only declare change_types within {DASHA_CHANGE_TYPES} (the detector never produces other kinds there)")
        ec = e.get("expected_count")
        if ec is not None:
            ok = (isinstance(ec, dict) and set(ec) <= {"exact", "min", "max"} and ec and all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in ec.values())
                  and not ("exact" in ec and len(ec) > 1) and not ("min" in ec and "max" in ec and ec["min"] > ec["max"]))
            if not ok:
                errs.append(f"{w}: 'expected_count' must be {{\"exact\": n}} or {{\"min\": a, \"max\": b}} (non-negative integers, not booleans; min must not exceed max)")
    if "charts" in h and not (isinstance(h["charts"], list) and h["charts"] and all(isinstance(c, str) and re.match(r"^[0-9a-fA-F-]{8,}$", c) for c in h["charts"])):
        errs.append(f"{fname}: 'charts' must be a NON-EMPTY list of hex chart-id prefixes (>= 8 chars); omit the field to apply to every chart")
    elif any(isinstance(c, str) and c.replace("-", "").lower().startswith(PHANTOM_PREFIX) for c in h.get("charts", [])):
        errs.append(f"{fname}: 'charts' names the dead phantom chart id {PHANTOM_PREFIX} (refused)")
    return errs


def load_hooks(hooks_dir, required=()):
    """-> (hooks, errors). Every *.json in the folder is a lane hook. Errors make the run exit 2."""
    hooks, errors = [], []
    if not os.path.isdir(hooks_dir):
        return hooks, [f"HOOKS DIR NOT FOUND: {hooks_dir}"]
    files = sorted(glob.glob(os.path.join(hooks_dir, "*.json")))  # top level only: sub-folders (evidence/) are never hooks
    if not files:
        errors.append(f"NO HOOK FILES: {hooks_dir} contains no top-level *.json")
    for p in files:
        try:
            h = json.load(open(p))
        except Exception as ex:
            errors.append(f"{os.path.basename(p)}: not valid JSON ({ex})")
            continue
        errs = validate_hook(h, p)
        if errs:
            errors += errs
        else:
            hooks.append(h)
    present = {h["lane"] for h in hooks}
    for lane in required:
        if lane and lane not in present:
            errors.append(f"MISSING HOOK: lane '{lane}' has no valid {lane}.json in {hooks_dir} (blocker: its fix may change facts nothing attributes)")
    return hooks, errors


def scope_matches(e, c):
    """The entry declares this row/category/column (table, category, fact_key, ayanamsha), whatever KIND of change it is."""
    if e.get("kind") == "dasha_shift":
        return False
    if c["table"] != e["table"] or c["category"] not in e["categories"]:
        return False
    if e.get("fact_keys") and c.get("fact_key") not in e["fact_keys"]:
        return False
    if e.get("ayanamsha_ids") and c.get("ayanamsha") not in e["ayanamsha_ids"]:
        return False
    return True


def entry_matches(e, c):
    """Scope matches AND the change kind is one the entry declares (omitted change_types = all five kinds)."""
    return scope_matches(e, c) and c["change"] in (e.get("change_types") or CHANGE_TYPES)


def applies_to_chart(h, chart_id):
    if "charts" not in h:
        return True
    return any(chart_id.lower().startswith(p.lower()) for p in h["charts"])


def attribute_all(changes, hooks, chart_id):
    """Fills c['lanes'] (lane names, may be several; empty = UNATTRIBUTED) and c['kind_mismatch'] (for an unattributed change, the
    {lane: declared change_types} of every entry that declares its category but not its KIND). Returns per-entry observed counts."""
    counts = collections.Counter()
    for c in changes:
        c["lanes"] = []
        for h in hooks:
            if not applies_to_chart(h, chart_id):
                continue
            for i, e in enumerate(h["may_change"]):
                if entry_matches(e, c):
                    counts[(h["lane"], i)] += 1
                    if h["lane"] not in c["lanes"]:
                        c["lanes"].append(h["lane"])
        km = {}
        if not c["lanes"]:
            for h in hooks:
                if not applies_to_chart(h, chart_id):
                    continue
                for e in h["may_change"]:
                    if scope_matches(e, c):  # the hook declares this category, but not this KIND of change
                        km.setdefault(h["lane"], set()).update(e.get("change_types") or CHANGE_TYPES)
        c["kind_mismatch"] = {lane: sorted(v) for lane, v in sorted(km.items())}
    return counts


def entry_observability(e, have_dash, have_daily, l2_tables=()):
    """-> None if the detector can observe this entry, else the reason it cannot (the entry is then NOT CHECKED, not 'absent').
    l2_tables = the L2 (Bodha) tables compared in this run (empty unless --l2): a hook entry on an L2 table that was not compared is NOT CHECKED."""
    if e.get("table") in UNCOMPARED_TABLES:
        return f"table {e['table']} is never read by the detector"
    if e.get("table") in L2_TABLES and e["table"] not in l2_tables:
        return f"L2 table {e['table']} not compared in this run (run with --l2 on a snapshot taken with --l2)"
    if e.get("table") == "chart_dashas":
        if not have_dash:
            return "chart_dashas not compared in this run (--no-dashas or absent from the snapshot)"
        if e.get("kind") != "dasha_shift" and set(e.get("change_types") or ()) == {"tier"}:
            return "the detector never compares the chart_dashas tier column"
    if e.get("table") == "panchanga_daily" and not have_daily:
        return "panchanga_daily not compared in this run (--no-daily or absent from the snapshot)"
    return None


def expectation_report(hooks, counts, chart_id, have_dash=True, have_daily=True, shift_counts=None, l2_tables=()):
    """-> (expectation rows, EXPECTATION_MISMATCH messages, DECLARED_BUT_ABSENT messages, OPTIONAL_ABSENT warnings, entry-level NOT CHECKED).
    An entry that declares expected_count is judged by that bound (a bound with min 0 explicitly allows no change). An entry with no
    expected_count that observed nothing is DECLARED_BUT_ABSENT unless it is marked optional (then a warning). An entry the detector
    cannot observe is NOT CHECKED, never absent and never passing."""
    shift_counts = shift_counts or {}
    bad, rows, absent, warn, unchecked = [], [], [], [], []
    for h in hooks:
        if not applies_to_chart(h, chart_id):
            continue
        for i, e in enumerate(h["may_change"]):
            why = entry_observability(e, have_dash, have_daily, l2_tables)
            label = f"{h['lane']}[{i}] ({e['table']}:{','.join(e.get('categories') or e.get('systems') or [])})"
            if why:
                unchecked.append({"lane": h["lane"], "entry": i, "table": e["table"], "reason": why})
                continue
            n = shift_counts.get((h["lane"], i), 0) if e.get("kind") == "dasha_shift" else counts.get((h["lane"], i), 0)
            ec = e.get("expected_count")
            if ec is not None and e.get("kind") != "dasha_shift":
                ok = (n == ec["exact"]) if "exact" in ec else (ec.get("min", 0) <= n <= ec.get("max", 10 ** 12))
                rows.append({"lane": h["lane"], "entry": i, "expected": ec, "observed": n, "ok": ok})
                if not ok:
                    bad.append(f"EXPECTATION MISMATCH {label}: expected {ec}, observed {n}")
            elif n == 0:
                if e.get("optional"):
                    warn.append(f"{W_OPTIONAL_ABSENT} {label}: optional entry observed no change")
                else:
                    absent.append(f"DECLARED BUT ABSENT {label}: the hook declares this change and nothing changed (mark the entry \"optional\": true if absence is acceptable)")
    return rows, bad, absent, warn, unchecked


# ------------------------------------------------------------------ read production
def read_state(chart_id, dashas=True, daily=True, info=None, l2=None):
    """Read one chart (and the global panchanga_daily) in ONE repeatable-read read-only transaction. The session must report
    transaction_read_only = on (requested through PGOPTIONS, proven by the first statement) or nothing is read."""
    chart_id = normalize_chart_id(chart_id)  # the only interpolated operator-controlled value: a UUID or nothing
    named = [("ro", "select current_setting('transaction_read_only')"), ("usr", "select current_user"),
             ("facts", f"""select ayanamsha_id, fact_category, fact_subject, fact_key, coalesce(fact_value_text,''), coalesce(fact_value_num::text,''),
                 coalesce(verification_pass_status,'') from chart_facts where chart_id='{chart_id}' order by ayanamsha_id, fact_category, fact_subject, fact_key"""),
             ("divs", f"""select ayanamsha_id, varga, graha, fact_category, fact_key, coalesce(fact_value_text,''), coalesce(fact_value_num::text,''), coalesce(sign,'')
                 from chart_divisionals where chart_id='{chart_id}'""")]
    if dashas:
        named.append(("dashas", f"""select ayanamsha_id, system_id, level_n, lord_graha, coalesce(kp_sublevel,''), coalesce(kp_sub_lord,''), coalesce(kp_sub_sub_lord,''),
                 start_iso::text, end_iso::text, dasha_row_id::text, coalesce(parent_row_id::text,'') from chart_dashas
                 where chart_id='{chart_id}'"""))
    if daily:
        named.append(("daily", "select " + ",".join(f"{c}::text" for c in DAILY_COLS) + " from panchanga_daily order by date"))
    l2 = list(l2 or [])
    for t in l2:  # --l2: the L2 tables are read in the SAME repeatable-read read-only transaction (result-set names are letters + underscore only)
        if t not in L2_TABLES:
            raise ValueError(f"not an L2 table of the registry: {t!r}")
        named.append(("xl_" + t, l2_select_sql(t, chart_id)))
    got = q_txn(named)
    if got["ro"] != [["on"]]:
        raise ReadError(f"database session is not read-only (transaction_read_only={got['ro']!r}); refusing to read")
    if info is not None:
        info["db_user"] = got["usr"][0][0] if got["usr"] and got["usr"][0] else ""
    st = {"chart_facts": _rows(got, "facts", 7), "divisionals": _rows(got, "divs", 8)}
    if dashas:
        st["dashas"] = dasha_label_rows(_rows(got, "dashas", 11))
    if daily:
        st["daily"] = _rows(got, "daily", len(DAILY_COLS))
    if l2:
        st["l2"] = {t: _rows(got, "xl_" + t, len(L2_COLS)) for t in l2}
    return st


def dasha_label_rows(rows):
    byid = {r[9]: r for r in rows}

    def lab(r):
        s = r[3]
        if r[4]:
            s += ":" + r[4] + ":" + r[5] + ":" + r[6]
        return s
    paths = {}
    for r in sorted(rows, key=lambda r: int(r[2])):
        base = paths.get(r[10], "") if r[10] in byid else ""
        paths[r[9]] = base + "/" + lab(r)
    return [[r[0], r[1], int(r[2]), paths[r[9]], r[7], r[8]] for r in rows if r[1] != "scope_cap"]


def l2_requested_tables(a):
    """() unless --l2 was given; else the tables named by --l2-tables (comma list, registry names only) or every registry table."""
    if not getattr(a, "l2", False):
        return ()
    named = _csv(getattr(a, "l2_tables", None))
    return tuple(t for t in L2_TABLES if not named or t in named)


def cmd_snapshot(a):
    """Never overwrites: a baseline is evidence. An existing file (or .sha256) at the target is refused (exit 6); pick another --out."""
    chart_id = resolve(a.snapshot)
    info = {}
    try:
        st = read_state(chart_id, not a.no_dashas, not a.no_daily, info, l2=l2_requested_tables(a) or None)
    except ReadError as ex:
        print(f"READ ERROR: {ex}", file=sys.stderr)
        return EXIT_READ_ERROR
    empties = empty_tables(st, not a.no_dashas, not a.no_daily) + empty_l2_tables(st)
    if empties:
        # the baseline is the evidence the whole flip report rests on: a snapshot of an empty read would be saved with a .sha256 and could not be overwritten
        print(f"READ ERROR: EMPTY READ: {', '.join(empties)} returned zero rows for chart {chart_id}; no snapshot was written "
              "(check the reader's grants / row-level security and the chart id)", file=sys.stderr)
        return EXIT_READ_ERROR
    now = datetime.now(timezone.utc).isoformat()
    st["meta"] = {"tool": "flip_detector.py", "tool_version": TOOL_VERSION, "chart_id": chart_id, "taken_at_utc": now, "db_user": info.get("db_user", ""), "read_only": True,
                  "single_transaction": "REPEATABLE READ READ ONLY", "no_dashas": bool(a.no_dashas), "no_daily": bool(a.no_daily),
                  "counts": {k: len(v) for k, v in st.items() if isinstance(v, list)}}
    if "l2" in st:  # --l2 only: the default snapshot meta is byte-identical to the pre-L2 tool
        st["meta"].update({"l2": True, "l2_extension_version": L2_EXTENSION_VERSION, "l2_tables": list(st["l2"]), "l2_counts": {t: len(v) for t, v in st["l2"].items()}})
    d = os.environ.get("FLIP_SNAPSHOT_DIR", DEFAULT_SNAPSHOT_DIR)
    out = a.out or os.path.join(d, f"pre_rebuild_{chart_id[:8]}_{now[:10]}_{now[11:19].replace(':', '')}.json.gz")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if os.path.exists(out) or os.path.exists(out + ".sha256"):
        print(f"REFUSED: {out} (or its .sha256) already exists; a baseline is never overwritten. Choose another --out or move the old file.", file=sys.stderr)
        return EXIT_REFUSED
    # atomic: both files are written under temporary names and linked into place only after everything succeeded (link fails if the target exists: never overwrites)
    tmp, tmp_sha = f"{out}.tmp{os.getpid()}", f"{out}.sha256.tmp{os.getpid()}"
    try:
        with gzip.open(tmp, "wt") as f:
            json.dump(st, f)
        h = hashlib.sha256(open(tmp, "rb").read()).hexdigest()
        with open(tmp_sha, "w") as f:
            f.write(f"{h}  {os.path.basename(out)}\n")
        os.link(tmp, out)
        try:
            os.link(tmp_sha, out + ".sha256")
        except OSError:
            os.unlink(out)
            raise
    except FileExistsError:
        print(f"REFUSED: {out} (or its .sha256) appeared meanwhile; a baseline is never overwritten.", file=sys.stderr)
        return EXIT_REFUSED
    finally:
        for t in (tmp, tmp_sha):
            if os.path.exists(t):
                os.unlink(t)
    print(f"snapshot: {out}\nsha256:   {h}\ncounts:   {st['meta']['counts']}\ntaken:    {now} as {st['meta']['db_user']}")
    if "l2" in st:
        print(f"l2:       {st['meta']['l2_counts']}")
    return 0


# ------------------------------------------------------------------ classification and diff
def kind_of(t, n, key):
    if t:
        return "time" if ISO.match(t) else "class_text"
    if n not in ("", None):
        if key in CLASS_NUM_KEYS:
            return "class_num"
        try:
            f = float(n)
            if abs(f - round(f)) < 1e-9 and key not in NOT_CLASS_INT:
                return "class_num"
        except ValueError:
            pass
        return "continuous"
    return "class_text"


def occ_map(rows, keyfn, valfn):
    m = collections.defaultdict(list)
    for r in rows:
        m[keyfn(r)].append(valfn(r))
    for k in m:
        # the tier is part of the sort key: two rows equal in value but different in tier must pair in a fixed order, whatever order the database returned
        m[k].sort(key=lambda v: (v[0] or "", float(v[1]) if v[1] not in ("", None) else float("-inf"), (v[2] if len(v) > 2 else "") or ""))
    return m


def same_num(a, b):
    if a in ("", None) or b in ("", None):
        return (a in ("", None)) and (b in ("", None))
    return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a))) + 1e-9


def diff_table(table, A, B, nkey):
    """A,B: key -> sorted occurrence lists [(t, n, tier)]. nkey = (index of fact_category, index of fact_key) inside the key tuple.
    Returns (class_and_tier_changes, continuous_stats)."""
    out = []
    cont = {"compared": 0, "changed": 0, "max_abs_delta": 0.0, "to_non_numeric": 0, "keys_appeared": 0, "keys_disappeared": 0,
            "time_keys_appeared": 0, "time_keys_disappeared": 0, "time_to_non_time": 0}
    for k in sorted(set(A) | set(B)):
        a, b = A.get(k), B.get(k)
        cat, key = k[nkey[0]], k[nkey[1]]
        base = {"table": table, "key": list(k), "category": cat, "fact_key": key, "ayanamsha": k[0]}
        if a is None or b is None:
            vals = b if a is None else a
            kinds = {kind_of(v[0], v[1], key) for v in vals}
            if kinds == {"time"}:
                cont["time_keys_appeared" if a is None else "time_keys_disappeared"] += 1
                continue  # an appearing/disappearing timestamp-valued fact is not a class change
            if "continuous" in kinds:  # a continuous key that appears or disappears IS a change (it can trigger declared/undeclared logic)
                cont["keys_appeared" if a is None else "keys_disappeared"] += 1
            out.append({**base, "change": "appeared" if a is None else "disappeared", "value": [list(v[:2]) for v in vals][:2]})
            continue
        if len(a) != len(b):
            out.append({**base, "change": "occurrence_count", "before": len(a), "after": len(b)})
        for x, y in zip(a, b):
            kd = kind_of(x[0], x[1], key)
            if kd == "continuous":
                cont["compared"] += 1
                if (y[0] or "") != "" or y[1] in ("", None):
                    # the continuous number became NULL or text (1.694 -> 'no_data'): a number was lost, which is a value change
                    cont["changed"] += 1
                    cont["to_non_numeric"] += 1
                    out.append({**base, "change": "value", "before": [x[0], x[1]], "after": [y[0], y[1]]})
                elif not same_num(x[1], y[1]):
                    cont["changed"] += 1
                    try:
                        cont["max_abs_delta"] = max(cont["max_abs_delta"], abs(float(y[1]) - float(x[1])))
                    except (TypeError, ValueError):
                        pass
            elif kd == "time":
                if kind_of(y[0], y[1], key) != "time":
                    # a timestamp-valued fact that became NULL or non-timestamp text lost its timestamp: a value change (a changed timestamp is not)
                    cont["time_to_non_time"] += 1
                    out.append({**base, "change": "value", "before": [x[0], x[1]], "after": [y[0], y[1]]})
            elif (x[0] or "") != (y[0] or "") or not same_num(x[1], y[1]):
                out.append({**base, "change": "value", "before": [x[0], x[1]], "after": [y[0], y[1]]})
            if len(x) > 2 and x[2] != y[2]:
                out.append({**base, "change": "tier", "before": x[2], "after": y[2]})
    return out, cont


# ------------------------------------------------------------------ L2 diff (only reached with --l2)
L2_STANDING_NOT_CHECKED = (
    {"id": "l2.unread_columns", "table": "l2", "what": "L2 columns outside each table's registry entry (the entry's `unread` text is in the report under l2_unread)",
     "reason": "the L2 extension compares identity, the listed content columns (arrays / jsonb / embedding vectors by a 12-hex md5 digest only) and a few continuous scores; "
               "every other column of the 29 L2 tables is never read", "readback": "hand read-back: 'L2 extension' in FLIP_DETECTOR_L2_README.md"},
    {"id": "l2.generation_ledger", "table": "l2", "what": "the L2 data-plane generation ledger (producer generations, heads, partitions, run intents, row snapshots)",
     "reason": "the reader role is denied SELECT on those tables; the detector sees the active L2 tables only, never the generation or head that produced them",
     "readback": "hand read-back with a privileged login: 'L2 extension' in FLIP_DETECTOR_L2_README.md"},
)


def _l2_standing(standing, l2_tables):
    """The standing NOT CHECKED registry for this run. Without L2 it is returned unchanged. With L2, the rows that say 'table not read by the detector'
    for a table that IS now compared are dropped (they would be false) and the two L2 standing rows are added."""
    if not l2_tables:
        return standing
    return tuple(n for n in standing if n.get("table") not in l2_tables) + L2_STANDING_NOT_CHECKED


def empty_l2_tables(st, tables=None):
    """L2 tables that must hold rows (registry flag must_have_rows) but hold none in this state. Only tables named in `tables` (default: those present in the state)."""
    l2 = st.get("l2") or {}
    return [t for t in (tables if tables is not None else l2) if t in L2_TABLES and L2_TABLES[t]["must_have_rows"] and not l2.get(t)]


def _l2_cancel_common(a, b):
    """Rows of a key that are identical on both sides (same identity text and tier) cancel (multiset): a duplicate-key group is then paired on what is left, so
    one moved identity does not shift the pairing of the unchanged rows."""
    pool = collections.Counter((x[0], x[2]) for x in b)
    ra, gone = [], collections.Counter()
    for x in a:
        k = (x[0], x[2])
        if pool[k] > 0:
            pool[k] -= 1
            gone[k] += 1
        else:
            ra.append(x)
    rb = []
    for y in b:
        k = (y[0], y[2])
        if gone[k] > 0:
            gone[k] -= 1
        else:
            rb.append(y)
    return ra, rb


def _l2_score_pairs(base, a, b, stats):
    """Continuous scores of rows whose identity text is identical on both sides. A score that moves is counted, never a class change; a score that becomes
    NULL (a number lost) is a value change, as for the L1 continuous values."""
    pool = collections.defaultdict(list)
    for y in b:
        pool[y[0]].append(y)
    out = []
    for x in a:
        lst = pool.get(x[0])
        if not lst:
            continue
        y = lst.pop(0)
        px, py = x[3].split(","), y[3].split(",")
        lost = False
        for i in range(max(len(px), len(py))):
            u, v = (px[i] if i < len(px) else ""), (py[i] if i < len(py) else "")
            if u == "" and v == "":
                continue
            stats["compared"] += 1
            if u != "" and v == "":
                stats["changed"] += 1
                stats["to_null"] += 1
                lost = True
                continue
            try:
                same = same_num(u, v)
            except ValueError:
                same = u == v
            if not same:
                stats["changed"] += 1
                try:
                    stats["max_abs_delta"] = max(stats["max_abs_delta"], abs(float(v) - float(u)))
                except ValueError:
                    pass
        if lost:
            out.append({**base, "change": "value", "before": [x[0], x[3]], "after": [y[0], y[3]], "note": "score_lost"})
    return out


def diff_l2_table(table, rows_a, rows_b):
    """Class / identity / tier changes of one L2 table (7-column rows, see the L2 block above) -> (changes, score_stats).
    The identity-bearing text and the tier go through the existing occ_map / diff_table unchanged (appeared, disappeared, value, occurrence_count, tier).
    diff_table compares `num` whenever the text is non-empty, which would make every moved score a class change, so the scores are NOT passed as num:
    they ride as a 4th element of the occurrence tuple (diff_table ignores it) and are compared here, continuously."""
    kf = lambda r: (r[0], r[1], r[2], r[3])
    vf = lambda r: (r[4], "", r[6], r[5])
    A, B = occ_map(rows_a, kf, vf), occ_map(rows_b, kf, vf)
    stats = {"compared": 0, "changed": 0, "to_null": 0, "max_abs_delta": 0.0, "keys_appeared": 0, "keys_disappeared": 0, "keys_both": 0}
    A2, B2, orig, extra = {}, {}, {}, []
    for k in sorted(set(A) | set(B)):
        a, b = A.get(k), B.get(k)
        if a is None or b is None:
            stats["keys_appeared" if a is None else "keys_disappeared"] += 1
            if a is not None:
                A2[k] = a
            else:
                B2[k] = b
            continue
        stats["keys_both"] += 1
        base = {"table": table, "key": list(k), "category": k[1], "fact_key": k[3], "ayanamsha": k[0]}
        extra += _l2_score_pairs(base, a, b, stats)
        ra, rb = _l2_cancel_common(a, b)
        orig[k] = (len(a), len(b))
        if ra or rb:
            A2[k], B2[k] = ra, rb
    changes, _ = diff_table(table, A2, B2, (1, 3))
    for c in changes:
        if c["change"] == "occurrence_count":
            c["before"], c["after"] = orig[tuple(c["key"])]  # the totals, not what was left after the identical rows cancelled
    return changes + extra, stats


def dasha_diff(snap, cur, hooks, chart_id):
    """Pair rows by (ayanamsha, system, level, lord path) then nearest start within 10 days. Returns (changes, info).
    Row-set changes (a row exists in only one side) are class changes of table chart_dashas, category = system_id.
    A start shift is attributed only by a 'dasha_shift' hook entry whose system and shift_range_sec contain it; 0 s = no change."""
    def groups(rows):
        g = collections.defaultdict(list)
        for ay, sy, lv, p, s, e in rows:
            g[(ay, sy, lv, p)].append(ts_parse(s))
        for k in g:
            g[k].sort()
        return g
    gs, gc = groups(snap), groups(cur)
    tol = 10 * 86400.0
    changes, shifts = [], collections.defaultdict(list)
    shift_counts = collections.Counter()  # (lane, entry index) -> shifted rows that fall inside that dasha_shift entry's declared range
    for k in sorted(set(gs) | set(gc)):
        a, b = gs.get(k, []), gc.get(k, [])
        i = j = 0
        while i < len(a) and j < len(b):
            d = (b[j] - a[i]).total_seconds()
            if abs(d) <= tol:
                shifts[(k[0], k[1])].append(d)
                i += 1
                j += 1
            elif d > 0:
                changes.append({"table": "chart_dashas", "key": list(k), "category": k[1], "fact_key": "row", "ayanamsha": k[0], "change": "disappeared", "start": a[i].isoformat()})
                i += 1
            else:
                changes.append({"table": "chart_dashas", "key": list(k), "category": k[1], "fact_key": "row", "ayanamsha": k[0], "change": "appeared", "start": b[j].isoformat()})
                j += 1
        for x in a[i:]:
            changes.append({"table": "chart_dashas", "key": list(k), "category": k[1], "fact_key": "row", "ayanamsha": k[0], "change": "disappeared", "start": x.isoformat()})
        for x in b[j:]:
            changes.append({"table": "chart_dashas", "key": list(k), "category": k[1], "fact_key": "row", "ayanamsha": k[0], "change": "appeared", "start": x.isoformat()})
    info = {}
    shift_unattrib = []
    for (ay, sy), v in sorted(shifts.items()):
        moved = [x for x in v if abs(x) > 2.0]
        rec = {"rows": len(v), "rows_shifted": len(moved), "min": min(v), "max": max(v)}
        if moved:
            c = collections.Counter(round(x) for x in moved)
            rec["mode_shift_sec"], cnt = c.most_common(1)[0]
            rec["share_of_shifted_at_mode"] = round(cnt / len(moved), 4)
            lanes = []
            outside = list(moved)
            for h in hooks:
                if not applies_to_chart(h, chart_id):
                    continue
                for ei, e in enumerate(h["may_change"]):
                    if e.get("kind") == "dasha_shift" and sy in e["systems"] and (not e.get("ayanamsha_ids") or ay in e["ayanamsha_ids"]):
                        lo, hi = e["shift_range_sec"]
                        shift_counts[(h["lane"], ei)] += len([x for x in moved if lo <= x <= hi])
                        inside = [x for x in outside if lo <= x <= hi]
                        if inside and h["lane"] not in lanes:
                            lanes.append(h["lane"])
                        outside = [x for x in outside if not (lo <= x <= hi)]
            rec["lanes"] = lanes
            rec["rows_outside_every_declared_range"] = len(outside)
            if outside:
                shift_unattrib.append(f"{ay}|{sy}: {len(outside)} of {len(moved)} shifted rows lie outside every declared dasha_shift range (mode {rec['mode_shift_sec']} s)")
        info[f"{ay}|{sy}"] = rec
    return changes, info, shift_unattrib, shift_counts


def anchors_check(cur_facts):
    m = collections.defaultdict(list)
    for r in cur_facts:
        m[(r[0], r[1], r[2], r[3])].append(r[4])
    res, alert = [], False
    for name, (cat, subj, key), want, ayans in ANCHORS:
        for ay in ayans:
            vals = m.get((ay, cat, subj, key), [])
            ok = bool(vals) and all(v == want for v in vals)
            res.append({"anchor": name, "ayanamsha": ay, "values": vals, "expected": want, "ok": ok})
            alert |= not ok
    return res, alert


def _declared_by(hooks, chart_id, table, tier_only_scope):
    out = []
    for h in hooks:
        if not applies_to_chart(h, chart_id):
            continue
        for e in h["may_change"]:
            if e.get("table") != table or e.get("kind") == "dasha_shift":
                continue
            if tier_only_scope and "tier" not in (e.get("change_types") or CHANGE_TYPES):
                continue
            if h["lane"] not in out:
                out.append(h["lane"])
    return sorted(out)


def report_is_malformed(rep):
    """A report missing the keys the verdict is decided from (or with the wrong shapes) is never PASS and never a crash."""
    if not isinstance(rep, dict) or any(k not in rep for k in REPORT_REQUIRED_KEYS):
        return True
    return not isinstance(rep["failures"], dict) or not isinstance(rep["failure_counts"], dict) or not isinstance(rep["not_checked"], list)


def decide_verdict(rep):
    """The ONE place a verdict is decided. ALERT > FAIL > NOT_CHECKED > PASS. PASS only when no failure class is non-empty AND nothing is
    NOT CHECKED. It reads the report's own failure lists, so a failure can never be hidden by a stale 'verdict' field. A malformed report
    (missing failures / failure_counts / not_checked) is FAIL: a saved report JSON must never be trusted for its 'verdict' field."""
    if report_is_malformed(rep):
        return V_FAIL
    if rep.get("ALERT_anchor_changed"):
        return V_ALERT
    if any(rep["failures"].get(k) for k in FAILURE_CLASSES):
        return V_FAIL
    if rep.get("not_checked"):
        return V_NOT_CHECKED
    return V_PASS


def empty_tables(st, have_dash, have_daily):
    """Tables that must hold rows but hold none in this state: chart_facts and chart_divisionals always; chart_dashas / panchanga_daily when they are
    read. Used by compare_states (EMPTY_READ failure) and by --snapshot (a baseline of an empty read is refused)."""
    return [label for label, key, on in (("chart_facts", "chart_facts", True), ("chart_divisionals", "divisionals", True), ("chart_dashas", "dashas", have_dash),
                                         ("panchanga_daily", "daily", have_daily)) if on and not st.get(key)]


def compare_states(snap, cur, hooks, chart_id, have_dash=True, have_daily=True, hook_errors=(), standing_not_checked=STANDING_NOT_CHECKED,
                   not_compared=None, extra_not_checked=(), l2_tables=(), l2_requested=False):
    """Pure function (no I/O): the whole comparison. Returns the report dict (JSON-serializable, deterministic ordering).
    `standing_not_checked` is the registry of scopes the detector never compares; production always uses STANDING_NOT_CHECKED.
    EMPTY_READ rule: every table compared (chart_facts, chart_divisionals always; chart_dashas / panchanga_daily when compared) must hold
    at least one row in BOTH states. A real chart always has rows in each; zero rows means the read returned nothing (for example a
    row-level-security block for the reader), and empty-versus-empty would otherwise read as 'nothing changed'.
    A table that was NOT compared in this run (have_dash / have_daily False: a flag, or a section missing from a snapshot) is never silent:
    it adds a conditional NOT CHECKED row ('<table>.not_compared') carrying the reason in `not_compared` ({table: reason}), and the summary
    prints n/a (never a green ok) for the classes it would have evaluated. `extra_not_checked` is a list of ready NOT CHECKED rows.
    L2 (opt-in, default off: every output is then byte-identical to the pre-L2 tool): `l2_tables` = the L2 (Bodha) tables compared in this run (read from
    snap["l2"] / cur["l2"]); `l2_requested` = the operator asked for L2 (--l2), so a missing section adds the conditional NOT CHECKED row 'l2.not_compared'
    (reason in not_compared["l2"]). EMPTY_READ applies to L2 tables flagged must_have_rows only."""
    chart_id = normalize_chart_id(chart_id)
    l2set = tuple(t for t in l2_tables if t in L2_TABLES)
    not_compared = dict(not_compared or {})
    empty = []
    for side, st in (("snapshot", snap), ("current", cur)):
        for label in empty_tables(st, have_dash, have_daily):
            empty.append(f"EMPTY READ: {label} has zero rows in the {side} state (a real chart has rows: the read returned nothing; check reader grants / row-level security)")
    for side, st in (("snapshot", snap), ("current", cur)):
        for t in empty_l2_tables(st, l2set):
            empty.append(f"EMPTY READ: {t} has zero rows in the {side} state (a built chart has rows: the read returned nothing; check reader grants / row-level security)")
    fk = lambda r: (r[0], r[1], r[2], r[3])
    fv = lambda r: (r[4], r[5], r[6])
    changes, cont1 = diff_table("chart_facts", occ_map(snap["chart_facts"], fk, fv), occ_map(cur["chart_facts"], fk, fv), (1, 3))
    dk = lambda r: (r[0], r[1], r[2], r[3], r[4])
    dv = lambda r: (r[5] or r[7], r[6], "")
    ch2, cont2 = diff_table("chart_divisionals", occ_map(snap["divisionals"], dk, dv), occ_map(cur["divisionals"], dk, dv), (3, 4))
    changes += ch2
    if have_daily:
        sd, cd = {r[0]: r for r in snap["daily"]}, {r[0]: r for r in cur["daily"]}
        for d in sorted(set(sd) | set(cd)):
            if d not in sd or d not in cd:
                changes.append({"table": "panchanga_daily", "key": [d], "category": "row", "fact_key": d, "ayanamsha": "", "change": "appeared" if d not in sd else "disappeared"})
                continue
            for c, x, y in zip(DAILY_COLS[1:], sd[d][1:], cd[d][1:]):
                if x != y:
                    changes.append({"table": "panchanga_daily", "key": [d, c], "category": c, "fact_key": d, "ayanamsha": "", "change": "value", "before": x, "after": y})
    dinfo, shift_unattrib, shift_counts = None, [], {}
    if have_dash:
        dch, dinfo, shift_unattrib, shift_counts = dasha_diff(snap["dashas"], cur["dashas"], hooks, chart_id)
        changes += dch
    l2_cont = {}
    for t in l2set:
        ch3, l2_cont[t] = diff_l2_table(t, (snap.get("l2") or {}).get(t, []), (cur.get("l2") or {}).get(t, []))
        changes += ch3
    counts = attribute_all(changes, hooks, chart_id)
    exp_rows, exp_bad, absent, warn, entry_unchecked = expectation_report(hooks, counts, chart_id, have_dash, have_daily, shift_counts, l2set)
    unattrib = [c for c in changes if not c["lanes"]]
    kind_mm = [c for c in unattrib if c["kind_mismatch"]]
    undeclared = [c for c in unattrib if not c["kind_mismatch"]]
    by = collections.Counter((c["table"], c["category"], c["change"], ",".join(c["lanes"]) or "UNATTRIBUTED") for c in changes)
    not_checked = [{"id": n["id"], "table": n["table"], "what": n["what"], "reason": n["reason"], "readback": n["readback"],
                    "declared_by_lanes": _declared_by(hooks, chart_id, n["table"], n["table"] == "chart_dashas"), "status": "NOT CHECKED"}
                   for n in _l2_standing(standing_not_checked, l2set)]
    not_checked += [{"id": f"{u['lane']}[{u['entry']}]", "table": u["table"], "what": "hook entry the detector cannot observe in this run", "reason": u["reason"],
                     "readback": "hand read-back", "declared_by_lanes": [u["lane"]], "status": "NOT CHECKED"} for u in entry_unchecked]
    for tname, on, what in (("chart_dashas", have_dash, "chart_dashas row sets and start shifts (a real dasha change would read as no change)"),
                            ("panchanga_daily", have_daily, "panchanga_daily rows and columns (a real panchanga change would read as no change)")):
        if not on:
            not_checked.append({"id": f"{tname}.not_compared", "table": tname, "what": what, "reason": not_compared.get(tname, f"{tname} not compared in this run"),
                                "readback": "re-run the compare WITHOUT --no-dashas / --no-daily on snapshots that carry the section",
                                "declared_by_lanes": _declared_by(hooks, chart_id, tname, False), "status": "NOT CHECKED"})
    if l2_requested and not_compared.get("l2"):
        miss = sorted(t for t in L2_TABLES if t not in l2set)
        not_checked.append({"id": "l2.not_compared", "table": "l2", "what": "L2 (Bodha) tables requested with --l2 but not compared (a real L2 change would read as no change)",
                            "reason": not_compared["l2"], "readback": "re-run the snapshot and the compare WITH --l2 (both sides must carry the l2 section)",
                            "declared_by_lanes": sorted({h["lane"] for h in hooks if applies_to_chart(h, chart_id) for e in h["may_change"] if e.get("table") in miss}),
                            "status": "NOT CHECKED"})
    for row in not_checked:
        if row.get("table") == "l2" and row["id"] != "l2.not_compared":
            row["declared_by_lanes"] = sorted({h["lane"] for h in hooks if applies_to_chart(h, chart_id) for e in h["may_change"] if e.get("table") in l2set})
    not_checked += [dict(x, status="NOT CHECKED") for x in extra_not_checked]
    rep = {"tool_version": TOOL_VERSION, "chart_id": chart_id, "changes_total": len(changes), "unattributed": len(unattrib),
           "compared": {"chart_facts": True, "chart_divisionals": True, "chart_dashas": bool(have_dash), "panchanga_daily": bool(have_daily)},
           "unattributed_examples": unattrib[:50],
           "by_table_category_change_lane": [[list(k), v] for k, v in sorted(by.items(), key=lambda kv: (-kv[1], kv[0]))],
           "continuous": {"chart_facts": cont1, "chart_divisionals": cont2}, "dashas": dinfo,
           "dasha_shift_unattributed": shift_unattrib, "expectations": exp_rows, "expectation_mismatches": exp_bad,
           "failure_counts": {F_UNDECLARED: len(undeclared), F_KIND: len(kind_mm), F_ABSENT: len(absent), F_EXPECT: len(exp_bad),
                              F_DASHA: len(shift_unattrib), F_HOOK: len(hook_errors), F_EMPTY: len(empty)},
           "failures": {F_UNDECLARED: [_brief(c) for c in undeclared[:50]], F_KIND: [_brief(c) for c in kind_mm[:50]], F_ABSENT: absent,
                        F_EXPECT: exp_bad, F_DASHA: shift_unattrib, F_HOOK: list(hook_errors), F_EMPTY: empty},
           "warnings": warn, "not_checked": not_checked, "changes": changes}
    if chart_id == NATIVE and cur["chart_facts"]:
        rep["anchors"], rep["ALERT_anchor_changed"] = anchors_check(cur["chart_facts"])
    elif chart_id == NATIVE:
        # an empty current chart_facts is an EMPTY_READ failure (exit 2), not an anchor ALERT: nothing was read to compare with the anchors
        rep["anchors"], rep["ALERT_anchor_changed"] = [], False
    else:
        rep["ALERT_anchor_changed"] = False
    if l2set or l2_requested:
        rep["compared"]["l2"] = list(l2set)
        rep["l2_extension_version"] = L2_EXTENSION_VERSION
        rep["continuous_l2"] = l2_cont
        rep["l2_unread"] = {t: L2_TABLES[t]["unread"] for t in l2set}
    rep["verdict"] = decide_verdict(rep)
    return rep


def _brief(c):
    b = {k: c[k] for k in ("table", "category", "fact_key", "ayanamsha", "change") if k in c}
    if c.get("kind_mismatch"):
        b["declared_kinds_by_lane"] = c["kind_mismatch"]
    for k in ("before", "after", "value"):
        if k in c:
            b[k] = c[k]
    return b


def exit_code(rep, allow_not_checked=False):
    """0 PASS (or NOT_CHECKED with allow_not_checked), 2 FAIL, 3 ALERT, 4 NOT_CHECKED without allow_not_checked."""
    v = decide_verdict(rep)
    if v == V_ALERT:
        return EXIT_ALERT
    if v == V_FAIL:
        return EXIT_FAIL
    if v == V_NOT_CHECKED:
        return EXIT_PASS if allow_not_checked else EXIT_NOT_CHECKED
    return EXIT_PASS


def render_summary(rep, allow_not_checked=False):
    """Human summary lines (deterministic)."""
    L = []
    v = decide_verdict(rep)
    if report_is_malformed(rep):
        return [f"VERDICT: {v}   exit {exit_code(rep, allow_not_checked)}   MALFORMED REPORT: needs {list(REPORT_REQUIRED_KEYS)} (a saved report is never trusted for its verdict)"]
    L.append(f"VERDICT: {v}   exit {exit_code(rep, allow_not_checked)}   chart {rep['chart_id']}")
    if rep.get("ALERT_anchor_changed"):
        L.append("ALERT: A FORENSIC ANCHOR CHANGED. STOP AND GO TO SS.")
        for r in rep.get("anchors", []):
            if not r["ok"]:
                L.append(f"    {r}")
    L.append(f"changes (class + tier + dasha row-set): {rep['changes_total']}   not attributed to any lane: {rep['unattributed']}")
    for k, n in rep["failure_counts"].items():
        if n:
            L.append(f"FAIL {k}: {n}")
            for x in rep["failures"][k][:20]:
                L.append(f"    {x if isinstance(x, str) else json.dumps(x, sort_keys=True)}")
    comp = rep.get("compared") or {}
    na = {F_DASHA: ("chart_dashas", comp.get("chart_dashas", True))}
    for k, n in rep["failure_counts"].items():
        if not n:
            if not na.get(k, ("", True))[1]:
                L.append(f"n/a  {k}: NOT EVALUATED ({na[k][0]} was not compared in this run)")
            else:
                L.append(f"ok   {k}: 0")
    for tname in ("chart_dashas", "panchanga_daily"):
        if comp and not comp.get(tname, True):
            L.append(f"n/a  {tname}: NOT COMPARED in this run (see the NOT CHECKED line)")
    for w in rep["warnings"]:
        L.append(f"WARNING {w}")
    for n in rep["not_checked"]:
        by = ",".join(n["declared_by_lanes"]) or "-"
        L.append(f"NOT CHECKED {n['id']}: {n['what']} | {n['reason']} | declared by: {by} | {n['readback']}")
    if rep["not_checked"]:
        L.append("NOT CHECKED items are never counted as passing" + ("; exit 0 only because --allow-not-checked was passed" if allow_not_checked and v == V_NOT_CHECKED else ""))
    for k, n in rep["by_table_category_change_lane"][:30]:
        L.append(f"   {n:7d}  {k[0]:18s} {k[1]:42s} {k[2]:16s} {k[3]}")
    for tname in ("chart_facts", "chart_divisionals"):
        c = rep["continuous"][tname]
        L.append(f"continuous ({tname}): compared {c['compared']} changed {c['changed']} (to NULL/text {c['to_non_numeric']}) keys appeared {c['keys_appeared']} "
                 f"disappeared {c['keys_disappeared']} timestamp->non-timestamp {c['time_to_non_time']} max |delta| {c['max_abs_delta']:.6g}")
    if rep.get("dashas"):
        L.append("dasha shifts: " + json.dumps({k: (x.get("rows_shifted"), x.get("mode_shift_sec"), x.get("lanes")) for k, x in sorted(rep["dashas"].items()) if x.get("rows_shifted")}, sort_keys=True))
    if rep["chart_id"] == NATIVE and not rep["ALERT_anchor_changed"]:
        L.append("anchors: 7 of 7 OK")
    if rep.get("l2_extension_version"):  # --l2 runs only
        l2c = comp.get("l2") or []
        L.append(f"l2 (Bodha) tables compared: {len(l2c)} of {len(L2_TABLES)}" + ("" if l2c else "   NOT COMPARED in this run (see the NOT CHECKED line)"))
        for t, c in sorted((rep.get("continuous_l2") or {}).items()):
            if c["changed"] or c["to_null"] or c["keys_appeared"] or c["keys_disappeared"]:
                L.append(f"continuous (l2 {t}): compared {c['compared']} changed {c['changed']} (to NULL {c['to_null']}) keys appeared {c['keys_appeared']} "
                         f"disappeared {c['keys_disappeared']} max |delta| {c['max_abs_delta']:.6g}")
    return L


def _csv(x):
    return [y for y in (x or "").split(",") if y]


def verify_sidecar(path):
    """-> ('ok' | 'absent' | 'mismatch', detail). The .sha256 written by --snapshot must match the file bytes (the baseline is evidence)."""
    sc = path + ".sha256"
    if not os.path.exists(sc):
        return "absent", f"{os.path.basename(path)}.sha256 not found: the snapshot's integrity is unverified"
    want = open(sc).read().split()[:1]
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if not want or want[0].lower() != got:
        return "mismatch", f"{os.path.basename(path)}: sha256 {got[:16]}... does not match its .sha256 sidecar ({(want[0][:16] + '...') if want else 'empty'}): the snapshot was altered or corrupted"
    return "ok", ""


def _write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def cmd_compare(a):
    snap = json.load(gzip.open(a.compare, "rt"))
    try:
        chart_id = normalize_chart_id(snap["meta"]["chart_id"])
    except (ValueError, KeyError) as ex:
        print(f"ERROR: snapshot chart id is not a valid UUID: {ex}", file=sys.stderr)
        return EXIT_FAIL
    hooks, herrs = load_hooks(a.hooks_dir if a.hooks_dir is not None else DEFAULT_HOOKS_DIR, _csv(a.require_lanes))
    extra, sha_state = [], {}
    for label, path in (("snapshot", a.compare), ("against", a.against)):
        if not path:
            continue
        st_, detail = verify_sidecar(path)
        sha_state[label] = st_
        if st_ == "mismatch":
            herrs = list(herrs) + [f"SNAPSHOT INTEGRITY: {detail}"]
        elif st_ == "absent":
            extra.append({"id": f"{label}.sha256", "table": "snapshot", "what": f"integrity of the {label} file", "reason": detail,
                          "readback": "verify the file against the sha256 recorded when it was taken", "declared_by_lanes": []})
    not_compared = {}
    if a.against:
        cur = json.load(gzip.open(a.against, "rt"))
        try:
            other = normalize_chart_id(cur["meta"]["chart_id"])
        except (ValueError, KeyError):
            other = None
        if other != chart_id:
            print(f"ERROR: --against snapshot is for chart {cur['meta'].get('chart_id')}, not {chart_id}", file=sys.stderr)
            return EXIT_FAIL
        sections = {"chart_dashas": ("dashas", a.no_dashas, "--no-dashas"), "panchanga_daily": ("daily", a.no_daily, "--no-daily")}
        have = {}
        for tname, (key, flag, flagname) in sections.items():
            why = flagname if flag else ("the snapshot lacks the section" if key not in snap else ("the --against snapshot lacks the section" if key not in cur else ""))
            have[tname] = not why
            if why:
                not_compared[tname] = f"{tname} not compared in this run: {why}"
        have_dash, have_daily = have["chart_dashas"], have["panchanga_daily"]
    else:
        cur = None
        have_dash = "dashas" in snap and not a.no_dashas
        have_daily = "daily" in snap and not a.no_daily
        for tname, key, flag, flagname, on in (("chart_dashas", "dashas", a.no_dashas, "--no-dashas", have_dash), ("panchanga_daily", "daily", a.no_daily, "--no-daily", have_daily)):
            if not on:
                not_compared[tname] = f"{tname} not compared in this run: " + (flagname if flag else "the snapshot lacks the section")
    want_l2 = l2_requested_tables(a)  # () unless --l2 (then nothing below differs from the pre-L2 tool)
    l2_tables = ()
    if want_l2:
        in_snap = snap.get("l2") or {}
        in_cur = (cur.get("l2") or {}) if cur is not None else None
        l2_tables = tuple(t for t in want_l2 if t in in_snap and (in_cur is None or t in in_cur))
        parts = [f"{x} missing from the snapshot's l2 section" for x in want_l2 if x not in in_snap]
        if in_cur is not None:
            parts += [f"{x} missing from the --against snapshot's l2 section" for x in want_l2 if x in in_snap and x not in in_cur]
        if parts:
            not_compared["l2"] = "L2 tables not compared in this run: " + "; ".join(parts)
    out = a.out or a.compare.replace(".json.gz", "") + f"_COMPARE_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    if cur is None:
        try:
            cur = read_state(chart_id, have_dash, have_daily, l2=list(l2_tables) or None)
        except ReadError as ex:
            rep = {"verdict": "READ_ERROR", "exit_code": EXIT_READ_ERROR, "chart_id": chart_id, "error": str(ex), "meta": {"snapshot": a.compare, "compared_at_utc": datetime.now(timezone.utc).isoformat()}}
            _write_json(out, rep)
            print(f"VERDICT: READ_ERROR   exit {EXIT_READ_ERROR}   {ex}\nreport: {out} | exit {EXIT_READ_ERROR}")
            return EXIT_READ_ERROR
    rep = compare_states(snap, cur, hooks, chart_id, have_dash, have_daily, hook_errors=herrs, not_compared=not_compared, extra_not_checked=extra,
                         l2_tables=l2_tables, l2_requested=bool(want_l2))
    skipped = sorted(not_compared)
    rep["meta"] = {"snapshot": a.compare, "against": a.against, "snapshot_meta": snap["meta"], "compared_at_utc": datetime.now(timezone.utc).isoformat(),
                   "hook_lanes_loaded": [h["lane"] for h in hooks], "allow_not_checked": bool(a.allow_not_checked),
                   "flags": {"no_dashas": bool(a.no_dashas), "no_daily": bool(a.no_daily), "allow_not_checked": bool(a.allow_not_checked),
                             "i_know_dashas_are_not_compared": bool(a.i_know_dashas_are_not_compared), "require_lanes": _csv(a.require_lanes)},
                   "skipped_sections": skipped, "snapshot_sha256": sha_state}
    if want_l2:
        rep["meta"]["flags"].update({"l2": True, "l2_tables": list(want_l2)})
    code = exit_code(rep, a.allow_not_checked)
    rep["exit_code"] = code
    for ln in render_summary(rep, a.allow_not_checked):
        print(ln)
    _write_json(out, rep)
    print("report:", out, "| exit", code)
    return code


def validate_report(hooks_dir, required=()):
    hooks, errs = load_hooks(hooks_dir, required)
    return {"mode": "validate-hooks", "tool_version": TOOL_VERSION, "hooks_dir": hooks_dir, "required_lanes": list(required),
            "valid_lanes": sorted(h["lane"] for h in hooks), "errors": errs, "verdict": V_FAIL if errs else V_PASS}


def cmd_validate(a):
    rep = validate_report(a.hooks_dir if a.hooks_dir is not None else DEFAULT_HOOKS_DIR, _csv(a.require_lanes))
    print("valid hook lanes:", rep["valid_lanes"])
    for e in rep["errors"]:
        print("HOOK ERROR:", e)
    print(f"VERDICT: {rep['verdict']}   exit {EXIT_FAIL if rep['errors'] else EXIT_PASS}")
    if a.out:
        with open(a.out, "w") as f:
            json.dump(rep, f, indent=1, sort_keys=True)
    return EXIT_FAIL if rep["errors"] else EXIT_PASS


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot")
    ap.add_argument("--compare")
    ap.add_argument("--against", help="with --compare: a second snapshot to compare against instead of reading production (offline)")
    ap.add_argument("--validate-hooks", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--hooks-dir")
    ap.add_argument("--require-lanes")
    ap.add_argument("--no-dashas", action="store_true")
    ap.add_argument("--no-daily", action="store_true")
    ap.add_argument("--l2", action="store_true", help="opt-in: also snapshot / compare the L2 (Bodha) tables of the registry (see FLIP_DETECTOR_L2_README.md); without it every output is unchanged")
    ap.add_argument("--l2-tables", help="with --l2: comma list of registry tables to cover (default: all)")
    ap.add_argument("--allow-not-checked", action="store_true", help="exit 0 on verdict NOT_CHECKED (the NOT CHECKED items are still printed and recorded)")
    ap.add_argument("--i-know-dashas-are-not-compared", action="store_true",
                    help="required to combine --no-dashas / --no-daily with --require-lanes (the S-L1 window must compare dashas and daily)")
    a = ap.parse_args(argv)
    if sum(map(bool, (a.snapshot, a.compare, a.validate_hooks))) != 1:
        ap.error("exactly one of --snapshot / --compare / --validate-hooks")
    if a.against and not a.compare:
        ap.error("--against needs --compare")
    if a.l2 and not (a.snapshot or a.compare):
        ap.error("--l2 needs --snapshot or --compare")
    if a.l2_tables is not None:
        if not a.l2:
            ap.error("--l2-tables needs --l2")
        bad = [t for t in _csv(a.l2_tables) if t not in L2_TABLES]
        if bad or not _csv(a.l2_tables):
            ap.error(f"--l2-tables must name registry L2 tables; unknown: {bad}")
    if a.hooks_dir is not None and not a.hooks_dir.strip():
        ap.error("--hooks-dir must not be empty (omit it to use the default S-L1 hooks folder)")
    if a.require_lanes is not None and not _csv(a.require_lanes):
        ap.error("--require-lanes must name at least one lane (omit it to require none)")
    if a.compare and (a.no_dashas or a.no_daily) and a.require_lanes and not a.i_know_dashas_are_not_compared:
        print("REFUSED: --no-dashas / --no-daily together with --require-lanes skips a check the S-L1 lanes need. Compare WITHOUT those flags, or add "
              "--i-know-dashas-are-not-compared (the report then carries NOT CHECKED rows for the skipped tables).", file=sys.stderr)
        return EXIT_REFUSED
    if a.snapshot:
        try:
            resolve(a.snapshot)
        except ValueError as ex:
            ap.error(f"--snapshot: {ex} (use native, abhinandan, kiran or a chart UUID)")
        return cmd_snapshot(a)
    return cmd_compare(a) if a.compare else cmd_validate(a)


if __name__ == "__main__":
    sys.exit(main())
