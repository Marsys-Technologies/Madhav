"""_r81_pre_migration_fixture.py — a frozen, historical snapshot of the 11 rows T5_LEDGER_DRIFT.md
§A measured (2026-09-26) plus the pre-R80 `_schema` doc text, exactly as they read in the real
ledger BEFORE R80+R81's one authorized write (commit "Nikaṣa wave3 R80+R81: the one authorized
real write to asset_gaps.jsonl this wave makes"). Frozen here, verbatim, so every test that proves
the R81 fold algorithm against "the real overlap pairs" keeps working after the real ledger has
been migrated for good — these tests must not depend on the real file's current (post-migration)
state to prove what the migration DID.

Not itself an authority on the ledger's current content — 00_ARCHITECTURE/control/asset_gaps.jsonl
is. This is a test fixture only.
"""
from __future__ import annotations

PRE_MIGRATION_SCHEMA_DOC = (
    "Delta ledger (tier-4 §5), both kinds. Append-only, one JSON object per line. Fields: asset, "
    "gap_id, kind (gap|opportunity), criterion, what, change, detector, owner, gate, state "
    "(OPEN|IN_PROGRESS|CLOSED|WITHDRAWN), ts. kind=gap: the shortfall against a requirement — "
    "`what` is written `measured: <figure, instrument, population> / required: <the gate's "
    "claim>` so the delta is a re-run, not a claim; gate = what it blocks (default: this asset's "
    "certification); CLOSED = the detector passed. kind=opportunity (tier-4 §9): the beyond — "
    "`what` = the distinction added or cost removed + expected delta; `change` = the proposal "
    "with cost and risk; `detector` = the measurement that proves it afterward; gate = NONE (an "
    "opportunity never blocks certification) and the row names the layer packet it feeds; "
    "OPEN=proposed, IN_PROGRESS=accepted and being built, CLOSED=realised and proven by its "
    "measurement, WITHDRAWN=rejected. A row with no detector/measurement is not registered — it "
    "is raised as a question. Rows without `kind` are read as kind=gap (pre-2026-09-26 rows)."
)

PRE_MIGRATION_SCHEMA_ROW = dict(asset="_schema", _doc=PRE_MIGRATION_SCHEMA_DOC,
                                 kind_added_on="2026-09-26")

# The 11 pairs' hand + census rows, transcribed verbatim from T5_LEDGER_DRIFT.md §A (measured
# 2026-09-26). Pair 8 has no single census counterpart — its two "partial" census siblings
# (Earn.build_record, Cost.baseline) are included too, since R81 must prove it leaves them
# untouched.
ROWS = [
    dict(asset="bg_ontology", gap_id="bg_ontology-G02", kind="gap", criterion="Earn.build_record",
         what="measured: asset_throughput.rows_written = 0 against 741 live rows, rows_per_second NULL, "
              "last_built_at 2026-09-04 / required: a build record carrying a real figure",
         change="instrument the seeder's run (rows, duration) into asset_throughput",
         detector="asset_throughput.rows_written non-zero after one build", owner="bg_ontology brief",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T05:56:21+05:30"),
    dict(asset="bg_ontology", gap_id="bg_ontology-Earn.build_record", kind="gap", criterion="Earn.build_record",
         what="measured: rows_per_second=NULL, last_built=2026-09-04 / required: the Earn gate's claim",
         change="", detector="asset_census.py --layer L0 (Earn.build_record)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_ontology", gap_id="bg_ontology-G07", kind="gap", criterion="Vocab.rule1.alias",
         what="measured: 79 of 79 dosha rows carry an empty synonyms array; the other 15 classes are "
              "complete / required: a non-empty closed alias set per entity",
         change="seed dosha alias sets through the writer",
         detector="per-class alias census: no_alias = 0 for all 16 classes", owner="bg_ontology brief",
         gate="W-L0-5", state="OPEN", ts="2026-09-26T05:56:21+05:30"),
    dict(asset="bg_ontology", gap_id="bg_ontology-Vocab.alias", kind="gap", criterion="Vocab.alias",
         what="measured: 16 class(es); empty alias sets: dosha 79/79 / required: the Vocab gate's claim",
         change="", detector="asset_census.py --layer L0 (Vocab.alias)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_ontology", gap_id="bg_ontology-G10", kind="gap", criterion="Dens.density_contract",
         what="measured: 0 of 2 capability modules serving this asset declare a density_contract (0 of "
              "46 layer-wide) / required: declared where the capability paginates or facets",
         change="declare density_contract on resolve_entity and list_entities",
         detector="grep census over the L0 capability directory", owner="layer packet",
         gate="W-L0-8", state="OPEN", ts="2026-09-26T05:56:21+05:30"),
    dict(asset="bg_ontology", gap_id="bg_ontology-Dens.served", kind="gap", criterion="Dens.served",
         what="measured: 2 module(s): list_entities.ts, resolve_entity.ts; declaring density_contract: 0 "
              "/ required: the Dens gate's claim",
         change="", detector="asset_census.py --layer L0 (Dens.served)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_ontology", gap_id="bg_ontology-G05", kind="gap", criterion="Carr.D1",
         what="measured: no detector compares a row to its source_citation; 741/741 rows carry one / "
              "required: a source-correspondence detector that can fail",
         change="build the D1 detector (layer packet W-L0-3) and run it over this asset",
         detector="the detector reports a non-zero mismatch count it could also report as zero",
         owner="layer packet", gate="W-L0-3", state="OPEN", ts="2026-09-26T05:56:21+05:30"),
    dict(asset="bg_ontology", gap_id="bg_ontology-Carr.detector", kind="gap", criterion="Carr.detector",
         what="measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset "
              "semantics / required: the Carr gate's claim",
         change="", detector="asset_census.py --layer L0 (Carr.detector)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_ephemeris", gap_id="bg_ephemeris-G03", kind="gap", criterion="Earn.build_record",
         what="measured: asset_throughput.rows_written = 0 for the layer's largest table (825,084 rows), "
              "rows_per_second NULL / required: a build record carrying a real figure",
         change="instrument the COPY path", detector="rows_written non-zero and a rate after one build",
         owner="bg_ephemeris brief", gate="this asset's certification", state="OPEN",
         ts="2026-09-26T06:20:58+05:30"),
    dict(asset="bg_ephemeris", gap_id="bg_ephemeris-Earn.build_record", kind="gap", criterion="Earn.build_record",
         what="measured: rows_per_second=NULL, last_built=2026-09-04 / required: the Earn gate's claim",
         change="", detector="asset_census.py --layer L0 (Earn.build_record)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_ephemeris", gap_id="bg_ephemeris-G05", kind="gap", criterion="Dens.density_contract",
         what="measured: 4 capability modules expose it, 0 declare a density_contract / required: "
              "declared where the capability paginates or facets",
         change="declare it on the 4 modules", detector="grep census over the L0 capability directory",
         owner="layer packet", gate="W-L0-8", state="OPEN", ts="2026-09-26T06:20:58+05:30"),
    dict(asset="bg_ephemeris", gap_id="bg_ephemeris-Dens.served", kind="gap", criterion="Dens.served",
         what="measured: 4 module(s): query_aspects_at_time.ts, query_planet_position.ts, "
              "query_planet_transit.ts, query_retrograde_periods.ts; declaring density_contract: 0 / "
              "required: the Dens gate's claim",
         change="", detector="asset_census.py --layer L0 (Dens.served)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_ephemeris", gap_id="bg_ephemeris-G02", kind="gap", criterion="Carr.D3",
         what="measured: integrity_check_sql asserts shape (exact row count, span, 9-body set, "
              "ayanamsha_id='tropical') and never recomputes a position; 825,084 computed values, none "
              "independently re-derived / required: D3 re-derivation within a declared tolerance",
         change="build D3: recompute a sample a second way and compare; seed one error to prove it fails",
         detector="non-zero mismatch on the seeded case, zero on the corpus", owner="layer packet",
         gate="W-L0-4", state="OPEN", ts="2026-09-26T06:20:58+05:30"),
    dict(asset="bg_ephemeris", gap_id="bg_ephemeris-Carr.detector", kind="gap", criterion="Carr.detector",
         what="measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset "
              "semantics / required: the Carr gate's claim",
         change="", detector="asset_census.py --layer L0 (Carr.detector)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_panchanga", gap_id="bg_panchanga-G01", kind="gap", criterion="Earn.service_state",
         what="measured: the asset's only status is asset_throughput state='lit' with rows_written=0 — "
              "identical to what a writer that produced nothing would write; no liveness or correctness "
              "signal exists / required: a status that can return false for a broken service",
         change="give service assets their own probe: answer a pinned instant, compare to a stored "
                "expected limb set",
         detector="the probe fails when the service is down or wrong", owner="layer packet",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T06:20:58+05:30"),
    dict(asset="bg_panchanga", gap_id="bg_panchanga-Earn.build_record", kind="gap", criterion="Earn.build_record",
         what="measured: rows_per_second=NULL, last_built=2026-08-27 / required: the Earn gate's claim",
         change="", detector="asset_census.py --layer L0 (Earn.build_record)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),
    dict(asset="bg_panchanga", gap_id="bg_panchanga-Cost.baseline", kind="gap", criterion="Cost.baseline",
         what="measured: state=lit, rows_written=0, rps=- / required: the Cost gate's claim",
         change="", detector="asset_census.py --layer L0 (Cost.baseline)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_panchanga", gap_id="bg_panchanga-G02", kind="gap", criterion="Carr.D3",
         what="measured: no detector recomputes a pañcāṅga limb a second way / required: D3 "
              "re-derivation on at least one limb",
         change="recompute tithi/vāra a second way for a pinned instant and compare",
         detector="mismatch reported on a seeded wrong convention", owner="layer packet",
         gate="W-L0-4", state="OPEN", ts="2026-09-26T06:20:58+05:30"),
    dict(asset="bg_panchanga", gap_id="bg_panchanga-Carr.detector", kind="gap", criterion="Carr.detector",
         what="measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset "
              "semantics / required: the Carr gate's claim",
         change="", detector="asset_census.py --layer L0 (Carr.detector)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_rules", gap_id="bg_rules-G03", kind="gap", criterion="Carr.D1",
         what="measured: 3,002 encoded rules, each citing text_id + verse_ref, and no detector compares "
              "a rule to its verse / required: D1 source correspondence that can fail",
         change="build D1 (layer packet W-L0-3) and run it over this asset first — it is the largest "
                "encoded-claim set in L0",
         detector="non-zero mismatch count it could also report as zero; a seeded wrong rule is caught",
         owner="layer packet", gate="W-L0-3", state="OPEN", ts="2026-09-26T06:20:58+05:30"),
    dict(asset="bg_rules", gap_id="bg_rules-Carr.detector", kind="gap", criterion="Carr.detector",
         what="measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset "
              "semantics / required: the Carr gate's claim",
         change="", detector="asset_census.py --layer L0 (Carr.detector)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),

    dict(asset="bg_rules", gap_id="bg_rules-G06", kind="gap", criterion="Completeness.depth.dasha_link",
         what="measured: dasha_system_id populated on 0 of 3,002 rows — a column never used / required: "
              "populated where the rule is daśā-conditioned, or the column removed",
         change="populate or drop; an always-null column is a claim nobody makes",
         detector="count > 0, or the column gone", owner="bg_rules brief",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T06:20:58+05:30"),
    dict(asset="bg_rules", gap_id="bg_rules-Complete.depth", kind="gap", criterion="Complete.depth",
         what="measured: 3002 rows, 14 cols; fully populated 12; NEVER populated ['dasha_system_id'] / "
              "required: the Complete gate's claim",
         change="", detector="asset_census.py --layer L0 (Complete.depth)", owner="asset_census",
         gate="this asset's certification", state="OPEN", ts="2026-09-26T13:19:10+05:30"),
]
