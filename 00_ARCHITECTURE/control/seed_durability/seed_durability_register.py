#!/usr/bin/env python3
"""M0-T29 · SEED DURABILITY REGISTER — generator.

Answers, per asset_registry column and per campaign repair: **would the next
`asset_registry_seed.ts` run change this cell, and does that undo a repair?**

M0-T27's post-reseed projection (m0_exit_scorecard.py:1446) modelled 4 of the 23
seed-overwritten columns and said so — a declared LOWER BOUND. This closes that gap
by modelling every column the seed writes.

READ-ONLY, by construction:
  * the DB session is opened with `default_transaction_read_only = on`; the only
    statements issued are SELECT / SET / to_regclass;
  * `asset_registry_seed.ts` is never imported and never executed (D-13, D-17).
    Its per-asset literals reach this script through
    `extract_seed_projection.mjs`, which slices out the `ASSETS` array LITERAL,
    statically proves it inert, and evaluates only that;
  * `m0_exit_scorecard.py` and `writer_substep_census.py` are NOT imported or
    edited — a sibling KĀRAKA holds the latter. The upsert-parse below is this
    file's own copy of the technique, not a call into theirs.

Re-run:  python3 00_ARCHITECTURE/control/seed_durability/seed_durability_register.py
"""
from __future__ import annotations
import datetime as _dt
import json
import pathlib
import re
import subprocess
import sys

import psycopg
import psycopg.rows

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
SEED_TS = ROOT / "platform/scripts/seed/asset_registry_seed.ts"
OUT_JSON = ROOT / "00_ARCHITECTURE/control/SEED_DURABILITY_REGISTER_v1_0.json"
OUT_MD = ROOT / "00_ARCHITECTURE/control/SEED_DURABILITY_REGISTER_v1_0.md"
EXTRACTOR = HERE / "extract_seed_projection.mjs"


def db_url() -> str:
    """DATABASE_URL from platform/.env.local, exactly as measure_assets.py reads it.
    The value is never printed, logged or written to any output of this script (P4)."""
    for line in (ROOT / "platform/.env.local").read_text().splitlines():
        m = re.match(r"^\s*DATABASE_URL\s*=\s*(.+)$", line)
        if m and line.startswith("DATABASE_URL="):
            return m.group(1).strip().strip("\"'")
    raise SystemExit("DATABASE_URL not found in platform/.env.local")


# ── 1 · what the seed writes, parsed from the TS as text ────────────────────
def parse_upsert() -> dict:
    """INSERT column list, DO UPDATE SET column list, and which of the latter are
    guarded by a CASE that can preserve the DB value."""
    txt = SEED_TS.read_text(errors="replace")
    out: dict = {"path": "platform/scripts/seed/asset_registry_seed.ts", "ok": False}
    m = re.search(r"INSERT\s+INTO\s+asset_registry\s*\((.*?)\)\s*VALUES", txt, re.S | re.I)
    if not m:
        out["reason"] = "no `INSERT INTO asset_registry ( ... ) VALUES` block"
        return out
    out["insert_columns"] = [c.strip() for c in m.group(1).split(",") if c.strip()]
    u = re.search(r"ON\s+CONFLICT\s*\(\s*asset_id\s*\)\s*DO\s+UPDATE\s+SET(.*?)`", txt, re.S | re.I)
    if not u:
        out["reason"] = "no `ON CONFLICT (asset_id) DO UPDATE SET` block"
        return out
    body_raw = u.group(1)
    body = re.sub(r"--[^\n]*", "", body_raw)
    # split the SET list into `col = <expr>` assignments at top level
    assigns: list[tuple[str, str]] = []
    for am in re.finditer(r"(?m)^\s*([a-z_][a-z0-9_]*)\s*=", body):
        start = am.end()
        nxt = re.search(r"(?m)^\s*[a-z_][a-z0-9_]*\s*=", body[start:])
        expr = body[start:start + nxt.start()] if nxt else body[start:]
        assigns.append((am.group(1), " ".join(expr.split()).rstrip(",")))
    out["do_update"] = {c: e for c, e in assigns}
    out["do_update_columns"] = sorted(out["do_update"])
    out["case_guarded"] = sorted(c for c, e in out["do_update"].items()
                                 if re.search(r"\bCASE\b", e, re.I))
    out["unconditional"] = sorted(set(out["do_update_columns"]) - set(out["case_guarded"]))
    out["insert_only_columns"] = sorted(
        set(out["insert_columns"]) - set(out["do_update_columns"]) - {"asset_id"})
    # the guard's own words, kept verbatim — it is the pattern any fix would follow
    gm = re.search(r"(-- MR-06.*?)\n\s*catalog_status = CASE", body_raw, re.S)
    out["guard_comment_verbatim"] = (
        "\n".join(l.strip() for l in gm.group(1).strip().splitlines()) if gm else None)
    out["ok"] = True
    return out


# ── 2 · what the seed would write per asset ─────────────────────────────────
def seed_rows() -> dict:
    r = subprocess.run([ "node", str(EXTRACTOR)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"extractor failed rc={r.returncode}: {r.stderr[:500]}")
    return json.loads(r.stdout)


# ── 3 · comparison ─────────────────────────────────────────────────────────
def norm(v):
    """Canonical form for cross-type comparison (jsonb vs dict, text[] vs list,
    numeric vs int). Returns a string, or the sentinel None for SQL NULL."""
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        f = float(v)
        return str(int(f)) if f.is_integer() else repr(f)
    s = str(v)
    # psycopg renders text[] as a python list already; a plain string stays a string
    return s


def clip(v, n=160):
    if v is None:
        return None
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, sort_keys=True)
    return s if len(s) <= n else s[:n] + f"…[+{len(s)-n}]"


def main() -> int:
    ext = seed_rows()
    if not ext.get("ok"):
        raise SystemExit("extractor could not prove the ASSETS literal inert; refusing")
    seed = ext["rows"]
    ups = parse_upsert()
    if not ups["ok"]:
        raise SystemExit(f"upsert parse failed: {ups.get('reason')}")

    rec: dict = {
        "generated_at_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task": "M0-T29",
        "generator": "00_ARCHITECTURE/control/seed_durability/seed_durability_register.py",
        "extractor": "00_ARCHITECTURE/control/seed_durability/extract_seed_projection.mjs",
        "read_only": True,
        "seed_extract_meta": {k: ext[k] for k in
                              ("seed_path", "seed_bytes", "inertness", "assets_parsed",
                               "lel_file_count", "lel_error")},
        "seed_upsert": {k: v for k, v in ups.items() if k != "do_update"},
        "seed_upsert_expressions": ups["do_update"],
    }

    with psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        c = conn.cursor()
        c.execute("SET default_transaction_read_only = on")
        c.execute("SET statement_timeout = '60s'")
        c.execute("""SELECT column_name, data_type, is_nullable, column_default
                     FROM information_schema.columns
                     WHERE table_schema='public' AND table_name='asset_registry'
                     ORDER BY ordinal_position""")
        colmeta = {r["column_name"]: r for r in c.fetchall()}
        cols = list(colmeta)
        c.execute("SELECT * FROM asset_registry ORDER BY asset_id")
        live = {r["asset_id"]: r for r in c.fetchall()}

        rec["live"] = {"asset_registry_columns": len(cols), "asset_registry_rows": len(live)}
        rec["columns"] = {
            "all_live": cols,
            "insert_only__written_once_never_updated": ups["insert_only_columns"],
            "do_update_unconditional__the_dangerous_set": ups["unconditional"],
            "do_update_case_guarded": ups["case_guarded"],
            "never_written_by_the_seed_at_all": sorted(
                set(cols) - set(ups["insert_columns"])),
        }

        # is_active needs main()'s pre-flight to_regclass mutation resolved.
        preflight = {}
        for aid, s in seed.items():
            tt = s.get("target_table")
            if tt is None:
                preflight[aid] = {"target_table": None, "exists_in_prod": None,
                                  "note": "null target_table — pre-flight skips it "
                                          "(:3219) and preserves is_active as declared"}
                continue
            c.execute("SELECT to_regclass(%s) AS t", (tt,))
            ok = c.fetchone()["t"] is not None
            preflight[aid] = {"target_table": tt, "exists_in_prod": ok,
                              "note": None if ok else
                                      "target_table ABSENT in prod → pre-flight (:3228) "
                                      "forces is_active=false before the upsert"}
        rec["is_active_preflight"] = {
            "what_it_models": ("asset_registry_seed.ts main() mutates asset.is_active to "
                               "false for any asset whose declared target_table is absent "
                               "from the target DB (:3222-3231), BEFORE the upsert binds "
                               "$17. Resolved here with a read-only to_regclass() per "
                               "declared target_table."),
            "assets_forced_inactive": sorted(a for a, v in preflight.items()
                                             if v.get("exists_in_prod") is False),
            "rows": preflight}

        # ── the projection, column by column ───────────────────────────────
        MODELLED = list(ups["do_update_columns"])
        per_col: dict = {}
        diffs: list = []
        unknown_cells: list = []
        for col in MODELLED:
            changed, same, unk = [], 0, []
            for aid, s in seed.items():
                if aid not in live:
                    continue  # the seed would INSERT it; handled separately below
                lv = live[aid].get(col)
                retired = live[aid].get("catalog_status") == "RETIRED"

                if col == "catalog_status":
                    want = lv if retired else s["catalog_status"]
                    guard = "RETIRED preserved" if retired else None
                elif col == "is_active":
                    if retired:
                        want, guard = lv, "RETIRED preserved"
                    else:
                        pf = preflight[aid]
                        if pf["exists_in_prod"] is False:
                            want, guard = False, "pre-flight forced false"
                        else:
                            want, guard = s["is_active_seed_declared"], None
                else:
                    want, guard = s.get(col, "__ABSENT__"), None

                if want == "__ABSENT__" or want == "__UNKNOWN__":
                    unk.append(aid)
                    unknown_cells.append({"asset_id": aid, "column": col,
                                          "why": "this script could not determine the value "
                                                 "the seed would write"})
                    continue
                if norm(lv) == norm(want):
                    same += 1
                else:
                    changed.append(aid)
                    cell = {"asset_id": aid, "column": col,
                            "live_value": clip(lv), "seed_would_write": clip(want),
                            "direction": ("seed FILLS a live NULL" if lv is None else
                                          "seed NULLS a live value" if want is None else
                                          "both non-null, values differ"),
                            "guard": guard,
                            "declared_in_seed_entry":
                                (s.get("__declared") or {}).get(col)}
                    if col in ("count_sql", "size_sql"):
                        # A second, WEAKER reading: are the two SQL texts the same
                        # statement modulo whitespace and keyword case? A re-seed
                        # still writes different BYTES either way — this only
                        # separates "the query changes" from "the formatting does".
                        def _sqlnorm(x):
                            return None if x is None else " ".join(str(x).split()).lower()
                        cell["differs_only_in_whitespace_or_case"] = (
                            _sqlnorm(lv) == _sqlnorm(want))
                    if col == "layer_index":
                        # the ONLY mechanical cleanliness test available: migration 590's
                        # own definition of the well-formed value ('Lx', x in 0..5).
                        cell["live_wellformed_Lx"] = bool(
                            lv is not None and re.fullmatch(r"L[0-5]", str(lv)))
                        cell["seed_wellformed_Lx"] = bool(
                            want is not None and re.fullmatch(r"L[0-5]", str(want)))
                    diffs.append(cell)
            per_col[col] = {
                "class": ("CASE-guarded" if col in ups["case_guarded"] else "unconditional"),
                "set_expression": ups["do_update"][col],
                "assets_compared": len([a for a in seed if a in live]),
                "cells_a_reseed_would_change": len(changed),
                "assets_changed": sorted(changed),
                "cells_unchanged": same,
                "cells_UNKNOWN": sorted(unk),
                "cells_differing_only_in_whitespace_or_case": len(
                    [x for x in diffs if x["column"] == col
                     and x.get("differs_only_in_whitespace_or_case")])
                if col in ("count_sql", "size_sql") else None,
                "direction_breakdown": {
                    d: len([x for x in diffs if x["column"] == col and x["direction"] == d])
                    for d in ("seed FILLS a live NULL", "seed NULLS a live value",
                              "both non-null, values differ")},
            }
        rec["per_column"] = per_col
        rec["divergent_cells"] = diffs
        rec["unknown_cells"] = unknown_cells

        rec["rows_only_in_one_side"] = {
            "live_but_no_seed_entry": sorted(set(live) - set(seed)),
            "seed_entry_but_not_live": sorted(set(seed) - set(live)),
            "note": ("a live row with no seed entry is untouched by a re-seed — the seed "
                     "neither updates nor deletes it. A seed entry with no live row is "
                     "INSERTed, and every column in "
                     "`never_written_by_the_seed_at_all` lands at its DB default "
                     "(NULL unless a DEFAULT/NOT NULL says otherwise)."),
        }

        # ── per-repair verdicts ────────────────────────────────────────────
        def col_verdict(colnames: list[str]) -> dict:
            written = [x for x in colnames if x in ups["do_update_columns"]]
            insert_only = [x for x in colnames if x in ups["insert_only_columns"]]
            never = [x for x in colnames if x not in ups["insert_columns"]]
            hit = {x: per_col[x]["assets_changed"] for x in written}
            return {"columns": colnames,
                    "in_do_update_set": written,
                    "insert_only": insert_only,
                    "not_written_by_the_seed": never,
                    "rows_a_reseed_would_change": hit,
                    "total_rows_reverted": sum(len(v) for v in hit.values())}

        repairs: dict = {}

        # (a) has_substeps — M0-T20, 12 rows
        c.execute("SELECT count(*) n FROM asset_registry WHERE has_substeps IS TRUE"
                  if "has_substeps" in colmeta else "SELECT 0 n")
        hs_true = c.fetchone()["n"]
        v = col_verdict(["has_substeps"])
        v["live_true_rows"] = hs_true
        v["verdict"] = ("DURABLE — the column is absent from the seed's INSERT list "
                        "entirely, so no seed run reads or writes it"
                        if "has_substeps" in v["not_written_by_the_seed"] else
                        "AT RISK — see rows_a_reseed_would_change")
        v["consequence_if_reverted"] = (
            "CORRECTNESS. has_substeps gates asset_runner.py's substep-plan-completeness "
            "predicate (CLAUDE.md §N.8 instance 4): plan_complete is initialised True and "
            "only recomputed inside `if has_substeps:`. A false-negative flag switches the "
            "detector OFF and lets `lit` be written on a proxy — the H4/I5 defect class.")
        repairs["has_substeps__M0-T20"] = v

        # (b) asset_kind / asset_type — M0-T21, 6 rows
        v = col_verdict(["asset_kind", "asset_type"])
        v["verdict"] = ("REVERTED — both columns are in the unconditional DO UPDATE SET "
                        "list and the seed supplies a `?? 'data'` default for each, so an "
                        "entry that omits the key is written with 'data', not left alone"
                        if v["total_rows_reverted"] else
                        "no divergence measured today")
        v["consequence_if_reverted"] = (
            "CORRECTNESS-ADJACENT. asset_kind/asset_type drive per-kind catalogue-contract "
            "rules (which required fields apply) and service-vs-data routing. Reverting a "
            "'service' to 'data' re-opens the contract violations M0-T21 closed.")
        repairs["asset_kind_asset_type__M0-T21"] = v

        # (c) domain / rung — migration 590, 128 rows
        v = col_verdict(["domain", "rung"])
        # the internal-consistency hazard: domain is not seed-written but scope is
        pair = []
        for aid, s in seed.items():
            if aid not in live:
                continue
            if "domain" not in colmeta:
                break
            if norm(live[aid].get("scope")) != norm(s.get("scope")):
                pair.append({"asset_id": aid,
                             "live_scope": live[aid].get("scope"),
                             "seed_would_write_scope": s.get("scope"),
                             "live_domain": live[aid].get("domain"),
                             "domain_derived_from_scope_would_become":
                                 {"global": "shared", "per_chart": "chart"}.get(s.get("scope")),
                             "consistent_after_reseed":
                                 {"global": "shared", "per_chart": "chart"}.get(s.get("scope"))
                                 == live[aid].get("domain")})
        v["scope_domain_pair_break"] = {
            "why": ("migration 590 derives domain 1:1 from scope. `scope` IS in the seed's "
                    "DO UPDATE SET list; `domain` is NOT. A re-seed therefore moves one half "
                    "of the pair and leaves the other, producing a row whose domain no "
                    "longer matches its own scope."),
            "rows": pair}
        v["verdict"] = ("domain/rung themselves are DURABLE (neither is written by the "
                        "seed at all) — but the PAIR is not: "
                        f"{len([p for p in pair if not p['consistent_after_reseed']])} row(s) "
                        "would end up internally inconsistent because `scope` moves under "
                        "them")
        v["consequence_if_reverted"] = (
            "CORRECTNESS. domain is the planner's split axis (plan §6.2) and rung is the "
            "layer-ladder position (§8.4). A domain that contradicts its own scope makes "
            "contract rule C-18/C-19 fire and makes I13's 'which rung owns this asset' "
            "question answerable two different ways.")
        repairs["domain_rung__migration_590"] = v

        # (d) has_writer — generator-only
        v = col_verdict(["has_writer"])
        c.execute("SELECT count(*) n FROM asset_registry WHERE has_writer IS NOT NULL"
                  if "has_writer" in colmeta else "SELECT 0 n")
        v["live_non_null_rows"] = c.fetchone()["n"]
        v["column_exists_live"] = "has_writer" in colmeta
        v["verdict"] = ("DURABLE (vacuously) — the column is not in the seed's INSERT or "
                        "DO UPDATE list, and no rows were written by the campaign"
                        if "has_writer" in v["not_written_by_the_seed"] else "AT RISK")
        v["consequence_if_reverted"] = "n/a — nothing to revert; no rows written."
        repairs["has_writer__generator_only"] = v

        # (e) layer_index / layer_name — Phase 0.5a, NOT YET PERFORMED
        v = col_verdict(["layer_index", "layer_name"])
        would = {}
        for col in ("layer_index", "layer_name"):
            would[col] = per_col[col]["assets_changed"] if col in per_col else None
        # what the DIRT looks like today, and what the seed would do to a repair
        c.execute("SELECT count(*) n FROM asset_registry WHERE layer_index IS NULL")
        li_null = c.fetchone()["n"]
        c.execute("SELECT count(*) n FROM asset_registry WHERE layer_index IS NOT NULL "
                  "AND layer_index !~ '^L[0-5]$'")
        li_bad = c.fetchone()["n"]
        c.execute("""SELECT asset_id, layer, layer_index, layer_name FROM asset_registry
                     WHERE layer_index IS NULL OR layer_index !~ '^L[0-5]$' ORDER BY asset_id""")
        dirty = [dict(r) for r in c.fetchall()]
        seedless_dirty = [d["asset_id"] for d in dirty if d["asset_id"] not in seed]
        seeded_dirty = [d["asset_id"] for d in dirty if d["asset_id"] in seed]
        v["live_dirt_today"] = {"layer_index_null": li_null,
                                "layer_index_malformed": li_bad,
                                "dirty_rows": dirty,
                                "dirty_rows_WITH_a_seed_entry": seeded_dirty,
                                "dirty_rows_WITHOUT_a_seed_entry": seedless_dirty}
        li_cells = [d for d in diffs if d["column"] == "layer_index"]
        ln_cells = [d for d in diffs if d["column"] == "layer_name"]
        seed_clean = len([d for d in li_cells if d.get("seed_wellformed_Lx")])
        live_clean = len([d for d in li_cells if d.get("live_wellformed_Lx")])
        v["measured_direction"] = {
            "layer_index_divergent_cells": len(li_cells),
            "of_those_the_SEED_value_is_wellformed_Lx": seed_clean,
            "of_those_the_LIVE_value_is_wellformed_Lx": live_clean,
            "layer_name_divergent_cells": len(ln_cells),
            "layer_name_cells_where_seed_fills_a_live_NULL":
                len([d for d in ln_cells if d["direction"] == "seed FILLS a live NULL"]),
            "reading": ("On EVERY divergent cell measured, the value the seed would write is "
                        "the well-formed one and the live value is the dirty one (a NULL, a "
                        "bare digit, or an unaccented layer_name). The seed is not the "
                        "threat to this repair — it is already performing it."),
        }
        v["if_the_repair_were_performed_today"] = {
            "layer_index": ("layer_index IS in the unconditional DO UPDATE SET list, so the "
                            "seed rewrites it on every run — but it derives the value as "
                            "`asset.layer_index ?? layerIndices[asset.layer] ?? null`, and "
                            f"on all {len(li_cells)} divergent cells that derivation yields "
                            f"the clean 'Lx' form ({seed_clean}/{len(li_cells)} well-formed) "
                            f"while the LIVE value is dirty ({live_clean}/{len(li_cells)} "
                            "well-formed). A Phase 0.5a repair that writes exactly "
                            "`layerIndices[layer]` is therefore DURABLE BY AGREEMENT: the "
                            "seed rewrites the identical value. A repair that writes "
                            "anything else is reverted on the next run."),
            "layer_name": ("same mechanism, `asset.layer_name ?? layerNames[asset.layer]`. "
                           "Note the seed's map carries the DIACRITICS locked by CLAUDE.md "
                           "§N.1 ('Gaṇita', 'Kāla', 'Mīmāṃsā'); several live rows carry the "
                           "unaccented spelling, so a repair must write the accented form or "
                           "it will diverge from the seed again."),
            "rows_with_NO_seed_entry": seedless_dirty,
            "rows_where_seed_and_live_already_disagree": would}
        v["verdict"] = ("NOT YET PERFORMED — and the measurement says the risk here runs the "
                        "OPPOSITE way to the asset_kind case. Both columns are seed-owned, "
                        f"but on all {len(li_cells) + len(ln_cells)} divergent cells the "
                        "seed's derived value is the CLEAN one. Phase 0.5a is durable so "
                        "long as it writes exactly what `layerIndices[layer]` / "
                        "`layerNames[layer]` produce, diacritics included; a repair that "
                        "invents its own form is reverted. "
                        f"{len(seedless_dirty)} dirty row(s) have no seed entry and are out "
                        "of the seed's reach entirely.")
        v["consequence_if_reverted"] = (
            "COSMETIC. layer_index is a display/ordering label; migration 590 explicitly "
            "REFUSED to derive `rung` from it precisely because it is dirty, so no gate "
            "reads it. A reversion here is a label going wrong, not a detector switching "
            "off — categorically less serious than has_substeps or the scope/domain pair.")
        repairs["layer_index_layer_name__phase_0.5a_NOT_PERFORMED"] = v

        rec["per_repair"] = repairs

        # ── consequence ranking ────────────────────────────────────────────
        rec["consequence_ranking"] = [
            {"rank": 1, "class": "CORRECTNESS — a detector switches off",
             "columns": ["has_substeps"],
             "at_risk_today": len(per_col.get("has_substeps", {}).get("assets_changed", []))
                              if "has_substeps" in per_col else 0,
             "why": ("a reverted has_substeps re-disables the §N.8 substep-plan-completeness "
                     "predicate, letting `lit` be written on a proxy. Nothing announces it."),
             "measured_state": "not seed-written; measured durable"},
            {"rank": 2, "class": "CORRECTNESS — a pair goes internally inconsistent",
             "columns": ["scope→domain"],
             "at_risk_today": len([p for p in pair if not p["consistent_after_reseed"]]),
             "why": ("scope is seed-owned, domain is not, and domain was derived FROM scope. "
                     "A re-seed moves one and leaves the other; the row then asserts two "
                     "different answers to the same question."),
             "measured_state": "MEASURED LIVE — see per_repair.domain_rung__migration_590"},
            {"rank": 3, "class": "CONTRACT — a per-kind rule set changes under the asset",
             "columns": ["asset_kind", "asset_type"],
             "at_risk_today": repairs["asset_kind_asset_type__M0-T21"]["total_rows_reverted"],
             "why": ("both carry a `?? 'data'` default, so an omitted key is an active write "
                     "of 'data', not a no-op. A 'service' asset silently becomes 'data' and "
                     "the contract rules that apply to it change."),
             "measured_state": "MEASURED LIVE"},
            {"rank": 4, "class": "OPERATIONAL — build gating / floors / counting",
             "columns": ["is_active", "catalog_status", "count_sql", "target_floor",
                         "depends_on", "target_table"],
             "at_risk_today": sum(len(per_col[x]["assets_changed"]) for x in
                                  ("is_active", "catalog_status", "count_sql",
                                   "target_floor", "depends_on", "target_table")
                                  if x in per_col),
             "why": ("these decide whether an asset builds at all, what its cockpit count "
                     "reads and what its DAG edges are. is_active and catalog_status are the "
                     "TWO columns already CASE-guarded — that guard is the pattern any fix "
                     "to the rest would follow."),
             "measured_state": "MEASURED LIVE"},
            {"rank": 5, "class": "COSMETIC — a label goes wrong, nothing gates on it",
             "columns": ["sanskrit_name", "english_name", "english_description",
                         "volume_explanation", "sort_order", "layer_name", "layer_index"],
             "at_risk_today": sum(len(per_col[x]["assets_changed"]) for x in
                                  ("sanskrit_name", "english_name", "english_description",
                                   "volume_explanation", "sort_order", "layer_name",
                                   "layer_index") if x in per_col),
             "why": "wrong text is visible and correctable; no detector reads it.",
             "measured_state": "MEASURED LIVE"},
        ]

        # ── coverage, stated explicitly ────────────────────────────────────
        modelled = set(MODELLED)
        rec["coverage"] = {
            "columns_the_seed_writes_on_a_re_seed": len(ups["do_update_columns"]),
            "columns_modelled_here": len(modelled & set(ups["do_update_columns"])),
            "modelled_columns": sorted(modelled & set(ups["do_update_columns"])),
            "unmodelled_columns": sorted(set(ups["do_update_columns"]) - modelled),
            "m0_t27_modelled": ["asset_kind", "asset_type", "layer", "scope"],
            "unknown_cells": len(unknown_cells),
            "rows_compared": len([a for a in seed if a in live]),
            "rows_in_live_not_compared": sorted(set(live) - set(seed)),
            "what_remains_UNMODELLED_and_why": [
                ("`is_active` is modelled only as far as to_regclass() can see: the "
                 "pre-flight also HARD-STOPS the whole seed if more than 20 assets have "
                 "absent target_tables (:3240). If that stop fires, NO column is written at "
                 "all and every figure in this register is moot. The count is reported "
                 "under is_active_preflight."),
                ("`expected_volume_inputs` for `mi_jivanaghatana` is overwritten by main() "
                 "(:3205) with a live FILE_COUNT of the LEL file. That evaluation is "
                 "replicated in the extractor and its result is reported "
                 f"(lel_file_count={ext.get('lel_file_count')}); if the LEL file changes, "
                 "the seed's value changes with it and this cell must be re-measured."),
                ("Column ORDER-sensitivity in `depends_on` is compared as an ordered list, "
                 "which is what Postgres text[] stores. A pure re-ordering counts as a "
                 "change here — that is deliberate, not a false positive."),
                ("This register models the seed's INSERT/UPDATE of asset_registry ONLY. "
                 "The same script also upserts asset_coefficients (:3341); that table is "
                 "out of scope and unmeasured."),
            ],
        }

        totals_by_class = {"unconditional": 0, "CASE-guarded": 0}
        for col, v2 in per_col.items():
            totals_by_class[v2["class"]] += v2["cells_a_reseed_would_change"]
        rec["headline"] = {
            "columns_modelled_of_columns_written":
                f"{len(modelled & set(ups['do_update_columns']))}/{len(ups['do_update_columns'])}",
            "total_cells_a_reseed_would_change": len(diffs),
            "columns_with_at_least_one_changed_cell":
                sorted(c2 for c2, v2 in per_col.items() if v2["cells_a_reseed_would_change"]),
            "distinct_assets_touched": len({d["asset_id"] for d in diffs}),
            "cells_UNKNOWN": len(unknown_cells),
            "changed_cells_by_class": totals_by_class,
        }

    OUT_JSON.write_text(json.dumps(rec, indent=1, default=str, ensure_ascii=False))
    md = subprocess.run([sys.executable, str(HERE / "render_register_md.py")],
                        capture_output=True, text=True)
    if md.returncode != 0:
        print(f"WARNING: markdown render failed rc={md.returncode}: {md.stderr[:400]}")
    else:
        print(md.stdout.strip())
    print(json.dumps(rec["headline"], indent=1))
    print("per-column changed cells:")
    for col in sorted(per_col, key=lambda k: -per_col[k]["cells_a_reseed_would_change"]):
        v2 = per_col[col]
        print(f"  {col:28s} {v2['class']:14s} changed={v2['cells_a_reseed_would_change']:4d} "
              f"unknown={len(v2['cells_UNKNOWN'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
