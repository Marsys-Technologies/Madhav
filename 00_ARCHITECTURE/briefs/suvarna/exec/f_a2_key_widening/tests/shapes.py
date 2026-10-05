"""The 18-shape capture probe (ported from the rehearsal's probe_shapes.py): ONE chart_facts row per value shape / verification tier /
ownership case, inserted as role data_plane_builder inside a really-opened generation (real open_l1_data_plane_generation, real guard
trigger, real l1_data_plane_capture_row) under a SAVEPOINT each; then the typed fact projection is read back."""
from __future__ import annotations

import hashlib
import uuid

import psycopg
import psycopg.rows
import psycopg.types.json as pj

import conftest as cf

CAT_OK = "aspect_tajik"          # owned by ga_structural in fact_category_ownership
ASSET = "ga_structural"
FIRST_18 = 18


def cases():
    c = []

    def case(name, cat, num=None, text=None, js=None, tier="single", key="k"):
        c.append(dict(name=name, cat=cat, num=num, text=text, js=js, tier=tier, key=key))

    case("A num only", CAT_OK, num=1.5)
    case("B text only", CAT_OK, text="x")
    case("C jsonb only", CAT_OK, js={"a": 1})
    case("D num+jsonb (aspect_tajik shape)", CAT_OK, num=93.4861, js={"orb_deg": 93.4861})
    case("E num+text+jsonb (lord_in_house shape)", CAT_OK, num=3, text="kendra", js={"h": 3})
    case("F text+jsonb (contradiction_pair shape)", CAT_OK, text="pair", js={"a": "x"})
    case("G num=0 + jsonb (zero)", CAT_OK, num=0, js={"a": 1})
    case("H all-null floored (sensitive-lane shape)", CAT_OK, tier="floored")
    case("I floored text-only (graha_*_per_varga shape)", CAT_OK, text="floored", tier="floored")
    case("J jsonb {state:floored}+num", CAT_OK, num=2, js={"state": "floored", "reason": "r"})
    case("K jsonb {floored:true} only (composite floor)", CAT_OK, js={"floored": True, "reason": "x"}, tier="floored")
    for t in ("classical_match", "computed_extension", "documented_approximation", "two_pass_verified", "divergent_flagged",
              "single_pass", "pending_w3_verification"):
        case(f"tier {t} num only", CAT_OK, num=1, tier=t)
    assert len(c) == FIRST_18
    case("L UNOWNED category karaka_web_per_varga (text+jsonb)", "karaka_web_per_varga", text="t", js={"a": 1})
    case("M UNOWNED category graha_position (num only)", "graha_position", num=1)
    case("N all-null, not floored (single)", CAT_OK, tier="single")
    return c


def run_shapes(cluster, db, chart=cf.CHART):
    """Returns (results, rows): results[name] = (ok, message); rows[fact_key] = fact snapshot + row snapshot columns."""
    run = str(uuid.uuid4())
    cluster.su(db, "INSERT INTO build_runs(id,chart_id,state) VALUES (%s,%s,'running')", (run, chart))
    cluster.su(db, "INSERT INTO build_run_assets(run_id,asset_id,state) VALUES (%s,%s,'building')", (run, ASSET))
    results, rows = {}, {}
    conn = cluster.conn(db, user="data_plane_builder")
    conn.row_factory = psycopg.rows.dict_row
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('madhav.l1_asset_id',%s,true), set_config('madhav.l1_chart_id',%s,true), "
                    "set_config('madhav.l1_generation_id',%s,true), set_config('madhav.l1_partition_key',%s,true), "
                    "set_config('madhav.l1_contract_version','l1.data-plane.contract.1.0',true)", (ASSET, chart, run, "probe_partition"))
        cur.execute("SELECT public.open_l1_data_plane_generation(%s::uuid,%s,%s,%s,1,NULL,'l1.data-plane.contract.1.0','l0.semantic.2026-09-13.1',"
                    "'665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1','l0-resource-config-g1',"
                    "'d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a')", (chart, ASSET, run, "probe_partition"))
        for i, k in enumerate(cases()):
            cur.execute("SAVEPOINT p")
            fid = hashlib.sha256(f"{k['name']}|{i}".encode()).hexdigest()[:16]
            try:
                cur.execute("""INSERT INTO chart_facts(fact_id,chart_id,ayanamsha_id,build_id,fact_category,fact_subject,fact_key,fact_value_text,
                  fact_value_num,fact_value_jsonb,unit,citation_ref,citation_human,source_calculation,verification_pass_status,engine_version,computed_at)
                  VALUES (%s,%s,'lahiri_chitrapaksha',%s,%s,'SUBJ',%s,%s,%s,%s,NULL,'ref','human','calc',%s,'v1',now())""",
                            (fid, chart, run, k["cat"], f"k{i}", k["text"], k["num"], pj.Jsonb(k["js"]) if k["js"] is not None else None, k["tier"]))
                cur.execute("RELEASE SAVEPOINT p")
                results[k["name"]] = (True, "")
            except Exception as exc:
                cur.execute("ROLLBACK TO SAVEPOINT p")
                results[k["name"]] = (False, f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}")
        cur.execute("""SELECT fs.fact_key, fs.missingness_state, fs.missingness_reason, fs.value_num, fs.value_text, fs.value_jsonb,
                       fs.grain_jsonb, rs.missingness_state AS row_state, rs.source_row_jsonb
                       FROM l1_data_plane_fact_snapshots fs JOIN l1_data_plane_row_snapshots rs ON rs.snapshot_id = fs.row_snapshot_id
                       WHERE fs.generation_id = %s""", (run,))
        for r in cur.fetchall():
            rows[r["fact_key"]] = r
    conn.rollback()
    conn.close()
    cluster.su(db, "DELETE FROM build_run_assets WHERE run_id=%s", (run,))
    cluster.su(db, "DELETE FROM build_runs WHERE id=%s", (run,))
    return results, rows
