#!/usr/bin/env python3.13
"""T1 planted-defect test for asset_census.py (the Nikaṣa inspector).

For each plantable check, plants ONE defect at a time into the sandbox DB
(nikasha_sandbox) or, for code-reading checks, into a temporarily mutated
writer/capability file, runs the inspector for that layer, restores, verifies
restoration, and asserts:
  (a) the target check's verdict on the target asset changed as expected;
  (b) NO OTHER asset's verdicts changed vs the clean baseline.

Verdict cells are the unit of comparison (asset_census JSON: per-asset
`measurements[check].v`). Measured-text changes are recorded but do not count
as verdict changes.

Usage:
  plant.py run [--only id,id,...]   run the plant suite (default: all)
  plant.py list                     list plant ids
Outputs: NT/census/plants/<id>.json (per-plant census), NT/harness/T1_RESULTS.json
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/Dev/madhav-nikasha")
NT = ROOT / "00_ARCHITECTURE" / "briefs" / "nirmana" / "nikasha_test"
SANDBOX_SOCK = NT / ".sandbox"
INSPECTOR = ROOT / "platform" / "scripts" / "governance" / "asset_census.py"
PY = "/opt/homebrew/opt/python@3.13/bin/python3.13"
PSQL = "/opt/homebrew/bin/psql"
BASELINE = NT / "census" / "L0_sandbox2_20260926.json"
BASELINES = {"L0": BASELINE,
             "L3": NT / "census" / "L3_sandbox_20260926.json",
             "L4": NT / "census" / "L4_sandbox_20260926.json"}
PLANTS_DIR = NT / "census" / "plants"
RESULTS = NT / "harness" / "T1_RESULTS.json"

RANK = {"PASS": 3, "PARTIAL": 2, "FAIL": 0, "N/A": 1, "NO_DETECTOR": 1, "NOT_GENERIC": 1}


def env() -> dict:
    e = dict(os.environ)
    e["PGHOST"] = str(SANDBOX_SOCK)
    e["PGPORT"] = "54329"
    e["PGUSER"] = "sandbox"
    e["PGDATABASE"] = "nikasha_sandbox"
    e["PGOPTIONS"] = ""
    e["PATH"] = "/opt/homebrew/bin:" + e.get("PATH", "")
    return e


def sql(q: str) -> list[list[str]]:
    p = subprocess.run([PSQL, "-tAX", "-F", "\x1f", "-v", "ON_ERROR_STOP=1", "-c", q],
                       capture_output=True, text=True, env=env(), timeout=300)
    if p.returncode != 0:
        raise RuntimeError("psql: " + p.stderr.strip())
    return [ln.split("\x1f") for ln in p.stdout.strip().split("\n") if ln.strip()]


def scalar(q: str) -> str:
    r = sql(q)
    return r[0][0] if r else ""


def run_census(name: str, layer: str = "L0", script: Path = INSPECTOR) -> dict:
    out = PLANTS_DIR / f"{name}.json"
    p = subprocess.run([PY, str(script), "--layer", layer, "--out", str(out)],
                       capture_output=True, text=True, env=env(), cwd=ROOT, timeout=1200)
    sys.stdout.write(p.stdout[-400:] + p.stderr[-400:])
    if not out.exists():
        raise RuntimeError(f"census did not write {out}; rc={p.returncode}")
    return json.loads(out.read_text())


def verdicts(doc: dict) -> dict[str, dict[str, str]]:
    for v in doc.values():
        if isinstance(v, dict) and "assets" in v:
            return {a["asset_id"]: {c: (m or {}).get("v") for c, m in a["measurements"].items()}
                    for a in v["assets"]}
    return {}


def measured(doc: dict, aid: str, check: str) -> str:
    for v in doc.values():
        if isinstance(v, dict) and "assets" in v:
            for a in v["assets"]:
                if a["asset_id"] == aid:
                    return (a["measurements"].get(check) or {}).get("measured", "<absent>")
    return "<absent>"


# ── backup helpers ─────────────────────────────────────────────────────

def bak_table(name: str, src: str) -> None:
    sql(f"CREATE SCHEMA IF NOT EXISTS nt_t1; DROP TABLE IF EXISTS nt_t1.{name}; "
        f"CREATE TABLE nt_t1.{name} AS {src}")


def restore_table_from_bak(name: str, table: str) -> None:
    try:
        sql(f"DELETE FROM {table}; INSERT INTO {table} SELECT * FROM nt_t1.{name}; "
            f"DROP TABLE nt_t1.{name}")
    except RuntimeError:
        sql(f"DELETE FROM {table}; INSERT INTO {table} OVERRIDING SYSTEM VALUE "
            f"SELECT * FROM nt_t1.{name}; DROP TABLE nt_t1.{name}")


class Ctx:
    """Holds per-plant restore state."""
    def __init__(self):
        self.vals: dict = {}


# ── plant definitions ──────────────────────────────────────────────────
# Each: id, check, asset, layer, desc, expect (verdict or ('UNCHANGED',) /
# ('MEASURED_WORSE',)), allow_same_asset (checks expected to co-change on the
# target asset), plant(ctx), restore(ctx), verify(ctx)->bool.

def _registry_save(ctx, aid, cols):
    ctx.vals = {c: scalar(f"SELECT coalesce({c}::text,'\\NULL') FROM asset_registry WHERE asset_id='{aid}'")
                for c in cols}
    ctx.vals["depends_on"] = scalar(
        f"SELECT coalesce(array_to_string(depends_on,','),'\\NULL') FROM asset_registry WHERE asset_id='{aid}'")


def _registry_restore(ctx, aid):
    for c, v in ctx.vals.items():
        if c == "depends_on":
            sql(f"UPDATE asset_registry SET depends_on="
                + ("NULL" if v == "\\NULL" else "string_to_array('" + v + "',',')")
                + f" WHERE asset_id='{aid}'")
        else:
            sql(f"UPDATE asset_registry SET {c}="
                + ("NULL" if v == "\\NULL" else "'" + v.replace("'", "''") + "'")
                + f" WHERE asset_id='{aid}'")


def _throughput_save(ctx, aid, cols):
    ctx.vals = {c: scalar(f"SELECT coalesce({c}::text,'\\NULL') FROM asset_throughput WHERE asset_id='{aid}'")
                for c in cols}


def _throughput_restore(ctx, aid):
    for c, v in ctx.vals.items():
        sql(f"UPDATE asset_throughput SET {c}="
            + ("NULL" if v == "\\NULL" else "'" + v.replace("'", "''") + "'")
            + f" WHERE asset_id='{aid}'")


PLANTS: list[dict] = []

def P(**kw):
    PLANTS.append(kw)


P(id="vocab_identity", check="Vocab.identity", asset="ph_sankrama", layer="L4", expect="FAIL",
  desc="INSERT 2 rows into phala_sankrama duplicating the declared composite natural key "
       "(chart_id,source_anchor_id,cdlm_cell_id,target_domain,relationship_type) with the two "
       "nullable members NULL (unique constraint admits NULL members; count(*)-count(DISTINCT key) "
       "becomes 1). L4 asset: no L0 target table has a nullable declared-key member "
       "(bg_sky_calendar's secondary_body_key is a GENERATED ALWAYS column that coalesces NULL to "
       "'', which physically blocks the duplicate — measured, not assumed).",
  plant=lambda c: (c.vals.__setitem__("n", scalar("SELECT count(*) FROM phala_sankrama")),
                   c.vals.__setitem__("ids", [r[0] for r in sql(
      "WITH src AS (SELECT * FROM phala_sankrama LIMIT 1), ins AS ("
      "INSERT INTO phala_sankrama (chart_id,source_anchor_id,cdlm_cell_id,source_domain,"
      "target_domain,relationship_type,linkage_strength,asymmetry_score,bridge_path_jsonb,"
      "mechanism_text,source_window_start,source_window_end,projected_window_start,"
      "projected_window_end,projected_peak_date,cascade_chain_jsonb,cascade_depth,trajectory,"
      "mitigation_ref,spillover_confidence,confidence_basis,falsifier,derivation_ledger_jsonb,"
      "source_citation,computed_at) "
      "SELECT chart_id,NULL::uuid,NULL::uuid,source_domain,target_domain,relationship_type,linkage_strength,"
      "asymmetry_score,bridge_path_jsonb,mechanism_text,source_window_start,source_window_end,"
      "projected_window_start,projected_window_end,projected_peak_date,cascade_chain_jsonb,"
      "cascade_depth,trajectory,mitigation_ref,spillover_confidence,confidence_basis,falsifier,"
      "derivation_ledger_jsonb,source_citation,computed_at FROM src UNION ALL "
      "SELECT chart_id,NULL::uuid,NULL::uuid,source_domain,target_domain,relationship_type,linkage_strength,"
      "asymmetry_score,bridge_path_jsonb,mechanism_text,source_window_start,source_window_end,"
      "projected_window_start,projected_window_end,projected_peak_date,cascade_chain_jsonb,"
      "cascade_depth,trajectory,mitigation_ref,spillover_confidence,confidence_basis,falsifier,"
      "derivation_ledger_jsonb,source_citation,computed_at FROM src RETURNING sankrama_id) "
      "SELECT sankrama_id::text FROM ins")])),
  restore=lambda c: sql("DELETE FROM phala_sankrama WHERE sankrama_id IN ("
                        + ",".join(f"'{t}'" for t in c.vals["ids"]) + ")")
                    if c.vals.get("ids") else None,
  verify=lambda c: scalar("SELECT count(*) FROM phala_sankrama") == c.vals["n"])

P(id="count_floor", check="Count.floor", asset="bg_vedha_malefic_scale", expect="FAIL",
  desc="DELETE 1 row from bg_vedha_malefic_scale (live 5 -> 4, target_floor=5)",
  plant=lambda c: (bak_table("vms", "SELECT * FROM bg_vedha_malefic_scale"),
                   sql("DELETE FROM bg_vedha_malefic_scale WHERE ctid IN "
                       "(SELECT ctid FROM bg_vedha_malefic_scale LIMIT 1)")),
  restore=lambda c: restore_table_from_bak("vms", "bg_vedha_malefic_scale"),
  verify=lambda c: scalar("SELECT count(*) FROM bg_vedha_malefic_scale") == "5")

P(id="build_completion_rw0", check="Build.completion", asset="bg_dignity_reference", expect="FAIL",
  desc="UPDATE asset_throughput SET rows_written=0 for bg_dignity_reference "
       "(live=151, populated table with a zero-rows build record)",
  plant=lambda c: (_throughput_save(c, "bg_dignity_reference", ["rows_written"]),
                   sql("UPDATE asset_throughput SET rows_written=0 WHERE asset_id='bg_dignity_reference'")),
  restore=lambda c: _throughput_restore(c, "bg_dignity_reference"),
  verify=lambda c: scalar("SELECT rows_written FROM asset_throughput WHERE asset_id='bg_dignity_reference'") == "151")

P(id="build_completion_truncate", check="Build.completion", asset="bg_muhurta_lattice",
  expect="FAIL->PASS (inverted)",
  desc="TRUNCATE-equivalent: DELETE all 8579 rows from bg_muhurta_lattice while its build record "
       "says rows_written=0. Inspector logic only fails on (rw=0 AND live>0); destroying data flips "
       "FAIL->PASS. Expected NOT-detected-as-worsening (known defect R42 probe).",
  plant=lambda c: (bak_table("ml", "SELECT * FROM bg_muhurta_lattice"),
                   sql("DELETE FROM bg_muhurta_lattice")),
  restore=lambda c: restore_table_from_bak("ml", "bg_muhurta_lattice"),
  verify=lambda c: scalar("SELECT count(*) FROM bg_muhurta_lattice") == "8579")

P(id="earn_cost_signal", check="Earn.build_record", asset="bg_yogas", expect="PASS",
  also_checks=["Cost.baseline"],
  desc="SENSITIVITY (reverse direction): sandbox has ZERO assets with rows_per_second set, so "
       "Earn.build_record/Cost.baseline are constant FAIL at baseline and no defect can worsen them. "
       "Plant sets rows_per_second=100 on bg_yogas: both checks must flip FAIL->PASS, proving the "
       "verdict actually reads the column.",
  plant=lambda c: (_throughput_save(c, "bg_yogas", ["rows_per_second"]),
                   sql("UPDATE asset_throughput SET rows_per_second=100 WHERE asset_id='bg_yogas'")),
  restore=lambda c: _throughput_restore(c, "bg_yogas"),
  verify=lambda c: scalar("SELECT coalesce(rows_per_second::text,'NULL') FROM asset_throughput "
                          "WHERE asset_id='bg_yogas'") == "NULL")

P(id="build_dag", check="Build.dag", asset="bg_yogas", expect="FAIL",
  allow_same_asset=["Build.dep_liveness"],
  desc="UPDATE asset_registry SET depends_on = depends_on || 'bg_t1_phantom' for bg_yogas "
       "(references a nonexistent bg_* asset). Build.dep_liveness co-fires on the same asset "
       "(phantom is also unlit) — same root cause, recorded as legitimate co-fire.",
  plant=lambda c: (_registry_save(c, "bg_yogas", []),
                   sql("UPDATE asset_registry SET depends_on = depends_on || 'bg_t1_phantom'::text "
                       "WHERE asset_id='bg_yogas'")),
  restore=lambda c: _registry_restore(c, "bg_yogas"),
  verify=lambda c: scalar("SELECT array_to_string(depends_on,',') FROM asset_registry "
                          "WHERE asset_id='bg_yogas'") == "bg_ontology,bg_texts")

P(id="build_target_null", check="Build.target", asset="bg_transit_rules", expect="N/A",
  allow_same_asset=["Complete.depth", "Vocab.identity", "Dens.served", "Ldgr.source_presence",
                    "Vocab.alias"],
  desc="UPDATE asset_registry SET target_table=NULL for bg_transit_rules (has_writer=true). "
       "asset_kind CANNOT be emptied (CHECK constraint: data|service|artifact — measured), so the "
       "inspector's FAIL branch ('has a writer and NO target_table') is unreachable through the "
       "registry: the defect surfaces as N/A, not FAIL. Recorded as detected-but-degraded. "
       "Table-bound checks on the same asset (Complete.depth, Vocab.identity) lose their substrate "
       "and disappear — recorded as same-asset effects.",
  plant=lambda c: (_registry_save(c, "bg_transit_rules", ["target_table"]),
                   sql("UPDATE asset_registry SET target_table=NULL "
                       "WHERE asset_id='bg_transit_rules'")),
  restore=lambda c: _registry_restore(c, "bg_transit_rules"),
  verify=lambda c: scalar("SELECT target_table FROM asset_registry WHERE asset_id='bg_transit_rules'")
                   == "bg_transit_rules")

P(id="count_integrity", check="Build.count_integrity", asset="bg_dignity_reference", expect="PARTIAL",
  desc="UPDATE asset_registry SET integrity_check_sql=NULL for bg_dignity_reference "
       "(count_sql retained, so live count, floor and completion are untouched)",
  plant=lambda c: (c.vals.__setitem__("md5", scalar(
                       "SELECT md5(integrity_check_sql) FROM asset_registry "
                       "WHERE asset_id='bg_dignity_reference'")),
                   bak_table("ci", "SELECT asset_id, integrity_check_sql FROM asset_registry "
                             "WHERE asset_id='bg_dignity_reference'"),
                   sql("UPDATE asset_registry SET integrity_check_sql=NULL "
                       "WHERE asset_id='bg_dignity_reference'")),
  restore=lambda c: (sql("UPDATE asset_registry t SET integrity_check_sql=b.integrity_check_sql "
                         "FROM nt_t1.ci b WHERE t.asset_id=b.asset_id"),
                     sql("DROP TABLE nt_t1.ci")),
  verify=lambda c: scalar("SELECT md5(integrity_check_sql) FROM asset_registry "
                          "WHERE asset_id='bg_dignity_reference'") == c.vals["md5"])

P(id="ldgr_source", check="Ldgr.source_presence", asset="bg_dasha_systems", expect="PARTIAL",
  desc="UPDATE brahma_dasha_systems SET classical_citations=NULL on one row (60/60 populated at "
       "baseline -> 59/60, verdict PASS->PARTIAL)",
  plant=lambda c: (bak_table("ds", "SELECT canonical_id, classical_citations FROM brahma_dasha_systems"),
                   sql("UPDATE brahma_dasha_systems SET classical_citations=NULL WHERE canonical_id = "
                       "(SELECT canonical_id FROM brahma_dasha_systems ORDER BY canonical_id LIMIT 1)")),
  restore=lambda c: (sql("UPDATE brahma_dasha_systems t SET classical_citations=b.classical_citations "
                         "FROM nt_t1.ds b WHERE t.canonical_id=b.canonical_id"),
                     sql("DROP TABLE nt_t1.ds")),
  verify=lambda c: scalar("SELECT count(*) FROM brahma_dasha_systems WHERE classical_citations IS NULL") == "0")

P(id="vocab_alias", check="Vocab.alias", asset="bg_ontology", expect="FAIL (severity-invisible)",
  desc="UPDATE brahma_ontology SET synonyms='{}' on the 662 rows that HAVE aliases (empty alias sets "
       "79/741 -> 741/741). Verdict is FAIL at baseline already (no synonyms-bearing asset is PASS "
       "anywhere in the sandbox), so this plant measures MEASURED-text sensitivity, not verdict flip.",
  plant=lambda c: (bak_table("ont", "SELECT id, synonyms FROM brahma_ontology"),
                   sql("UPDATE brahma_ontology SET synonyms='{}' WHERE cardinality(synonyms)>0")),
  restore=lambda c: (sql("UPDATE brahma_ontology t SET synonyms=b.synonyms FROM nt_t1.ont b "
                         "WHERE t.id=b.id"),
                     sql("DROP TABLE nt_t1.ont")),
  verify=lambda c: scalar("SELECT count(*) FROM brahma_ontology "
                          "WHERE synonyms IS NULL OR cardinality(synonyms)=0") == "79")

P(id="build_history", check="Build.history", asset="bg_class_priors", expect="FAIL",
  desc="INSERT a build_runs row (scope='layer', created now) plus a build_run_assets row with "
       "state='error' for bg_class_priors — the latest run of the asset is now an error",
  plant=lambda c: (c.vals.__setitem__("rid", scalar(
                       "INSERT INTO build_runs (id,chart_id,scope,scope_target,action,state,plan,"
                       "triggered_by,created_at) "
                       "VALUES (gen_random_uuid(),'00000000-0000-0000-0000-0000000000e1','layer','L0',"
                       "'build','completed','{}'::jsonb,'t1_plant',now()) RETURNING id")),
                   sql(f"INSERT INTO build_run_assets (run_id,asset_id,position,state,error) "
                       f"VALUES ('{c.vals['rid']}','bg_class_priors',0,'error','T1 planted error')")),
  restore=lambda c: (c.vals.get("rid") and sql(
      f"DELETE FROM build_run_assets WHERE run_id='{c.vals['rid']}'; "
      f"DELETE FROM build_runs WHERE id='{c.vals['rid']}'")),
  verify=lambda c: scalar("SELECT count(*) FROM build_run_assets WHERE asset_id='bg_class_priors'") == "4")

P(id="build_exercised", check="Build.exercised", asset="bg_dignity_reference", expect="FAIL",
  allow_same_asset=["Build.history"],
  desc="DELETE all 3 build_run_assets rows for bg_dignity_reference (has_writer=true, exercised at "
       "baseline -> 'registered with a writer and the orchestrator has NEVER run it'). "
       "Build.history co-changes to N/A on the same asset (no runs left to judge).",
  plant=lambda c: (bak_table("bra", "SELECT * FROM build_run_assets WHERE asset_id='bg_dignity_reference'"),
                   sql("DELETE FROM build_run_assets WHERE asset_id='bg_dignity_reference'")),
  restore=lambda c: (sql("INSERT INTO build_run_assets SELECT * FROM nt_t1.bra"),
                     sql("DROP TABLE nt_t1.bra")),
  verify=lambda c: scalar("SELECT count(*) FROM build_run_assets WHERE asset_id='bg_dignity_reference'") == "3")

P(id="dep_liveness", check="Build.dep_liveness", asset="bg_class_lifetime_counts", expect="FAIL",
  desc="UPDATE asset_throughput SET state='error' for bg_ghatana — the declared dependency of "
       "bg_class_lifetime_counts leaves the 'lit' set (no L0 asset other than the target depends on "
       "bg_ghatana; 'error' is within the state CHECK constraint)",
  plant=lambda c: (_throughput_save(c, "bg_ghatana", ["state"]),
                   sql("UPDATE asset_throughput SET state='error' WHERE asset_id='bg_ghatana'")),
  restore=lambda c: _throughput_restore(c, "bg_ghatana"),
  verify=lambda c: scalar("SELECT state FROM asset_throughput WHERE asset_id='bg_ghatana'") == "lit")

P(id="build_registered", check="Build.registered", asset="bg_reference", expect="FAIL",
  desc="UPDATE asset_registry SET has_writer=false for bg_reference while writer file still carries "
       "@register('bg_reference') — registry and code disagree",
  plant=lambda c: (_registry_save(c, "bg_reference", ["has_writer"]),
                   sql("UPDATE asset_registry SET has_writer=false WHERE asset_id='bg_reference'")),
  restore=lambda c: _registry_restore(c, "bg_reference"),
  verify=lambda c: scalar("SELECT has_writer::text FROM asset_registry WHERE asset_id='bg_reference'") == "true")

WRITER_DIR = ROOT / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers"
CAPS_L0 = ROOT / "platform" / "src" / "lib" / "retrieval" / "registry" / "layers" / "L0_brahmagyan"


def _plant_contract(c: Ctx):
    f = WRITER_DIR / "bg_dignity_reference.py"
    txt = f.read_text()
    anchor = "        conn = ctx.db_conn\n"
    assert anchor in txt, "anchor not found"
    c.vals["file"] = str(f)
    f.write_text(txt.replace(anchor, anchor + "        ctx.db_conn.commit()  # T1 PLANT\n", 1))


def _restore_code(c: Ctx):
    subprocess.run(["git", "checkout", "--", c.vals["file"]], cwd=ROOT, check=True)


P(id="build_contract", check="Build.contract", asset="bg_dignity_reference", expect="FAIL",
  desc="CODE plant: insert a real `ctx.db_conn.commit()` call into the run() of "
       "BgDignityReferenceWriter in writers/bg_dignity_reference.py (the orchestrator owns the "
       "transaction). Restored with git checkout.",
  plant=_plant_contract, restore=_restore_code,
  verify=lambda c: subprocess.run(["git", "diff", "--quiet", "--", c.vals["file"]],
                                  cwd=ROOT).returncode == 0)


def _plant_idem(c: Ctx):
    f = WRITER_DIR / "bg_cohort.py"
    txt = f.read_text()
    assert txt.count("ON CONFLICT") >= 2
    c.vals["file"] = str(f)
    f.write_text(txt.replace("ON CONFLICT", "ON  CONFLICT"))  # extra space: regex misses, SQL still valid


P(id="idem_pattern", check="Idem.pattern", asset="bg_cohort", expect="PARTIAL",
  desc="CODE plant: rewrite the two ON CONFLICT clauses in writers/bg_cohort.py as 'ON  CONFLICT' "
       "(valid SQL, invisible to the inspector's r'ON CONFLICT' regex) — the upsert pattern "
       "disappears from the writer's own SQL (PASS->PARTIAL). Restored with git checkout.",
  plant=_plant_idem, restore=_restore_code,
  verify=lambda c: subprocess.run(["git", "diff", "--quiet", "--", c.vals["file"]],
                                  cwd=ROOT).returncode == 0)

P(id="dens_served", check="Dens.served", asset="bg_gochara_arcs", expect="FAIL",
  desc="CODE plant: create L0 capability file zz_t1_plant.ts referencing table bg_gochara_arcs "
       "WITHOUT a density_contract (baseline N/A: no module references the table). Deleted after.",
  plant=lambda c: (c.vals.__setitem__("file", str(CAPS_L0 / "zz_t1_plant.ts")),
                   Path(c.vals["file"]).write_text(
                       "// T1 PLANT\n"
                       "export const T1_TABLE = 'bg_gochara_arcs';\n")),
  restore=lambda c: Path(c.vals["file"]).unlink(),
  verify=lambda c: not Path(c.vals["file"]).exists())


def run_plant(p: dict, base_v: dict, base_doc: dict) -> dict:
    ctx = Ctx()
    res = dict(id=p["id"], check=p["check"], asset=p["asset"], desc=p["desc"],
               expect=p["expect"], planted=False, detected=False, verdict_before=None,
               verdict_after=None, measured_after=None, same_asset_effects={}, collateral=[],
               restore_ok=False, error=None, seconds=0)
    t0 = time.time()
    try:
        ctx.vals["_pre"] = scalar("SELECT count(*) FROM asset_registry")  # sanity channel open
        p["plant"](ctx)
        res["planted"] = True
        doc = run_census(p["id"], p.get("layer", "L0"))
        pv = verdicts(doc)
        res["verdict_before"] = base_v.get(p["asset"], {}).get(p["check"], "<absent>")
        res["verdict_after"] = pv.get(p["asset"], {}).get(p["check"], "<absent>")
        res["measured_after"] = measured(doc, p["asset"], p["check"])
        # target assertion
        targets = [p["check"]] + p.get("also_checks", [])
        exp = p["expect"]
        oks = []
        for tc in targets:
            v0, v1 = base_v.get(p["asset"], {}).get(tc, "<absent>"), pv.get(p["asset"], {}).get(tc, "<absent>")
            if exp.startswith("FAIL->"):
                oks.append(v0 == "FAIL" and v1 == exp.split("->")[1])
            elif exp in ("PASS", "FAIL", "PARTIAL", "N/A"):
                oks.append(v1 == exp and v1 != v0)
            else:  # severity-invisible etc.: verdict unchanged, measured must differ
                oks.append(v1 == v0 and measured(doc, p["asset"], tc) != measured(base_doc, p["asset"], tc))
        res["detected"] = all(oks)
        # diffs
        allowed = set(targets) | set(p.get("allow_same_asset", []))
        for aid in sorted(set(base_v) | set(pv)):
            for ck in sorted(set(base_v.get(aid, {})) | set(pv.get(aid, {}))):
                v0, v1 = base_v.get(aid, {}).get(ck), pv.get(aid, {}).get(ck)
                if v0 == v1:
                    continue
                if aid == p["asset"] and ck in allowed:
                    continue
                entry = f"{aid}/{ck}: {v0}->{v1}"
                if aid == p["asset"]:
                    res["same_asset_effects"][ck] = f"{v0}->{v1}"
                else:
                    res["collateral"].append(entry)
    except Exception as exc:  # noqa: BLE001
        res["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            p["restore"](ctx)
            res["restore_ok"] = bool(p["verify"](ctx))
        except Exception as exc:  # noqa: BLE001
            res["error"] = (res["error"] or "") + f" | RESTORE {type(exc).__name__}: {exc}"
    res["seconds"] = round(time.time() - t0, 1)
    return res


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "list":
        for p in PLANTS:
            print(f"{p['id']:28s} {p['check']:22s} {p['asset']}")
        return 0
    only = None
    if "--only" in args:
        only = set(args[args.index("--only") + 1].split(","))
    PLANTS_DIR.mkdir(parents=True, exist_ok=True)
    base_cache: dict[str, tuple[dict, dict]] = {}

    def baseline(layer: str) -> tuple[dict, dict]:
        if layer not in base_cache:
            doc = json.loads(BASELINES[layer].read_text())
            base_cache[layer] = (doc, verdicts(doc))
        return base_cache[layer]

    results = []
    if RESULTS.exists():
        results = [r for r in json.loads(RESULTS.read_text()) if not only or r["id"] not in only]
    done = {r["id"] for r in results}
    for p in PLANTS:
        if only and p["id"] not in only:
            continue
        if p["id"] in done and not only:
            continue
        print(f"=== plant {p['id']} ({p['check']} on {p['asset']}) ===", flush=True)
        base_doc, base_v = baseline(p.get("layer", "L0"))
        r = run_plant(p, base_v, base_doc)
        results = [x for x in results if x["id"] != r["id"]] + [r]
        RESULTS.write_text(json.dumps(results, indent=1) + "\n")
        print(json.dumps({k: r[k] for k in ("id", "planted", "detected", "verdict_before",
                                            "verdict_after", "collateral", "restore_ok", "error",
                                            "seconds")}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
