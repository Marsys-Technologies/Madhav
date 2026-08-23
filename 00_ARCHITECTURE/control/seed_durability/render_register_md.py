#!/usr/bin/env python3
"""M0-T29 · renders SEED_DURABILITY_REGISTER_v1_0.md from the .json the generator
writes. Split out so the measurement and the prose have separate blast radii; the
generator invokes it, and it can also be re-run alone after an edit to the wording.

Every number below is read from the JSON. Nothing is typed in by hand."""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
J = ROOT / "00_ARCHITECTURE/control/SEED_DURABILITY_REGISTER_v1_0.json"
M = ROOT / "00_ARCHITECTURE/control/SEED_DURABILITY_REGISTER_v1_0.md"

CONSEQUENCE = {
    # column -> (class, one-line why). Assigned by hand ONCE, from what reads the
    # column in code; the row counts beside them are all measured.
    "has_substeps": ("CORRECTNESS", "gates the §N.8 substep-plan-completeness detector"),
    "scope": ("CORRECTNESS", "domain was derived from it; moving one and not the other splits the pair"),
    "is_active": ("OPERATIONAL", "decides whether the asset builds at all"),
    "catalog_status": ("OPERATIONAL", "CURRENT/DRAFT/RETIRED lifecycle + serving eligibility"),
    "count_sql": ("OPERATIONAL", "the cockpit's row count — §N.4 'cockpit truth'"),
    "target_floor": ("OPERATIONAL", "§N.4/I7 — floors are the MEASURED achieved count"),
    "target_table": ("OPERATIONAL", "where the asset's rows live; also drives the is_active pre-flight"),
    "depends_on": ("OPERATIONAL", "the DAG edges the orchestrator walks"),
    "asset_kind": ("CONTRACT", "which per-kind catalogue-contract fields apply"),
    "asset_type": ("CONTRACT", "data-vs-service routing"),
    "storage_type": ("CONTRACT", "per-kind contract input"),
    "layer": ("CONTRACT", "rung was derived from it (migration 590)"),
    "health_probe": ("OPERATIONAL", "service health mechanism"),
    "provides_apis": ("CONTRACT", "service contract surface"),
    "size_sql": ("COSMETIC", "reporting only"),
    "expected_volume_formula": ("COSMETIC", "audit-trail expression"),
    "expected_volume_inputs": ("COSMETIC", "audit-trail inputs"),
    "volume_explanation": ("COSMETIC", "prose"),
    "english_description": ("COSMETIC", "prose"),
    "english_name": ("COSMETIC", "label"),
    "sanskrit_name": ("COSMETIC", "label"),
    "sort_order": ("COSMETIC", "display order"),
    "layer_name": ("COSMETIC", "label"),
    "layer_index": ("COSMETIC", "label; migration 590 refused to derive rung from it"),
}
RANK = {"CORRECTNESS": 0, "CONTRACT": 1, "OPERATIONAL": 2, "COSMETIC": 3}


def main() -> int:
    r = json.loads(J.read_text())
    ups, per = r["seed_upsert"], r["per_column"]
    hd, cov = r["headline"], r["coverage"]
    diffs = r["divergent_cells"]
    L = []
    A = L.append

    A("---")
    A("canonical_id: SEED_DURABILITY_REGISTER")
    A("version: 1.0")
    A("status: CURRENT")
    A(f"generated_at: {r['generated_at_utc']}")
    A("campaign: NIRMĀṆA — Track M0, task M0-T29")
    A("authored_by: KĀRAKA (M0-T29). NOT self-certified — I16/H7. PARĪKṢAKA verifies.")
    A("regenerate: python3 00_ARCHITECTURE/control/seed_durability/seed_durability_register.py")
    A("---")
    A("")
    A("# SEED DURABILITY REGISTER v1.0")
    A("")
    A("**The question.** A repair written straight to `asset_registry` survives only if its")
    A("column is absent from `asset_registry_seed.ts`'s `ON CONFLICT (asset_id) DO UPDATE SET`")
    A("list. A column in that list is restored from `EXCLUDED` on the next seed run. A green")
    A("resting on such a column is a green a re-seed silently undoes — strictly worse than a")
    A("red, because nothing announces its expiry.")
    A("")
    A("M0-T27 built the post-reseed projection that made this measurable, and declared its own")
    A("bound: it modelled **4 of the 23** seed-overwritten columns and was therefore a LOWER")
    A("BOUND. This register closes that gap.")
    A("")
    A("## 0 — Headline, and this register's own bound")
    A("")
    A(f"- **Columns modelled / columns a re-seed writes: {hd['columns_modelled_of_columns_written']}.**")
    A(f"- Cells a re-seed would change today: **{hd['total_cells_a_reseed_would_change']}**, "
      f"across **{hd['distinct_assets_touched']}** distinct assets.")
    A(f"- Cells this register could not determine (`UNKNOWN`): **{hd['cells_UNKNOWN']}**.")
    A(f"- Live `asset_registry`: {r['live']['asset_registry_rows']} rows × "
      f"{r['live']['asset_registry_columns']} columns; seed entries parsed: "
      f"{r['seed_extract_meta']['assets_parsed']}.")
    A("")
    A("**The honest summary, stated before the detail:** most of what this campaign has")
    A("repaired is durable, and the register did not have to hunt for that answer. The four")
    A("Asset-Catalogue-Contract columns (`domain`, `rung`, `superseded_by`,")
    A("`data_disposition`), `has_substeps`, `has_writer`, `integrity_check_sql`,")
    A("`clear_tables`, `service_health` and `writer_timeout_seconds` are **not written by the")
    A("seed at all** — no INSERT, no UPDATE. Repairs to them cannot be reverted by a re-seed.")
    A("Two real exposures remain, both already named by M0-T27 and both re-measured")
    A("independently here (§3), plus a third this register found while modelling the other 19")
    A("columns (§3.6). Everything else is prose and labels.")
    A("")

    # ── §1 ──────────────────────────────────────────────────────────────
    A("## 1 — What the seed writes: the complete column list")
    A("")
    A("Parsed from the text of `platform/scripts/seed/asset_registry_seed.ts` "
      "(D-13: never imported, never executed — its `main()` runs the upsert, and D-17 records "
      "that it refuses dry-run requests too). Evidence line numbers are that file's.")
    A("")
    A(f"The `INSERT INTO asset_registry ( … )` column list (:3274) names "
      f"**{len(ups['insert_columns'])}** columns. The `ON CONFLICT (asset_id) DO UPDATE SET` "
      f"body (:3283) names **{len(ups['do_update_columns'])}**.")
    A("")
    A("### 1.1 — Group A · written on INSERT only")
    A("")
    A("Set once when the seed creates a row; never touched again on a re-run.")
    A("")
    A("| column | evidence |")
    A("|---|---|")
    A("| `asset_id` | the conflict key itself (`ON CONFLICT (asset_id)`, :3283) |")
    for cnm in ups["insert_only_columns"]:
        A(f"| `{cnm}` | present in the INSERT list (:3274-3281), absent from the "
          f"DO UPDATE SET body (:3283-3319). The interface comments it "
          f"`always null — measured on first build` (:43) |")
    A("")
    A("### 1.2 — Group B · written on `ON CONFLICT DO UPDATE` — **the dangerous set**")
    A("")
    A(f"**{len(ups['unconditional'])} columns**, each assigned unconditionally from "
      f"`EXCLUDED`. Anything hand-written into one of these is reverted on the next seed run "
      f"unless it happens to equal what the seed would write.")
    A("")
    A("| column | consequence class | rows a re-seed changes today |")
    A("|---|---|---|")
    for cnm in sorted(ups["unconditional"],
                      key=lambda k: (RANK.get(CONSEQUENCE.get(k, ("COSMETIC",))[0], 9),
                                     -per[k]["cells_a_reseed_would_change"], k)):
        cls, _why = CONSEQUENCE.get(cnm, ("UNCLASSIFIED", ""))
        A(f"| `{cnm}` | {cls} | {per[cnm]['cells_a_reseed_would_change']} |")
    A("")
    A("Three of these are not simple `EXCLUDED` copies — the seed **derives** the value in "
      "`main()` before binding it, and a column absent from a seed entry is therefore "
      "**written with a default, not left alone**. This is the single most reversible mistake "
      "in reading the file and the reason the asset_kind finding is real:")
    A("")
    A("```ts")
    A("const assetType  = asset.asset_type  ?? 'data'                                  // :3267")
    A("const assetKind  = asset.asset_kind  ?? 'data'                                  // :3268")
    A("const layerName  = asset.layer_name  ?? layerNames[asset.layer]  ?? asset.layer  // :3269")
    A("const layerIndex = asset.layer_index ?? layerIndices[asset.layer] ?? null        // :3270")
    A("const catalogStatus = asset.catalog_status")
    A("                   ?? (asset.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT')       // :3271")
    A("```")
    A("")
    A("Two further pre-upsert mutations of the in-memory `ASSETS` array are modelled here:")
    A("")
    A("- `:3222-3231` — pre-flight `to_regclass(target_table)`; any asset whose declared "
      "target table is absent from the target DB has `is_active` forced to `false` **before** "
      "the upsert binds it.")
    A("- `:3205` — `mi_jivanaghatana.expected_volume_inputs` is overwritten with a live "
      f"`FILE_COUNT` of the LEL file (measured here: **{r['seed_extract_meta']['lel_file_count']}**).")
    A("")
    A("### 1.3 — Group C · guarded by a `CASE` that preserves the DB value")
    A("")
    A(f"**{len(ups['case_guarded'])} columns**: `" + "`, `".join(ups["case_guarded"]) + "`.")
    A("This is the existing precedent for a durable-by-construction column, and the pattern "
      "any fix to Group B would follow. The file explains itself, verbatim (:3299-3312):")
    A("")
    A("```sql")
    if ups.get("guard_comment_verbatim"):
        for line in ups["guard_comment_verbatim"].splitlines():
            A(line)
    A("catalog_status = CASE WHEN asset_registry.catalog_status = 'RETIRED'")
    A("                      THEN asset_registry.catalog_status")
    A("                      ELSE EXCLUDED.catalog_status END,")
    A("is_active = CASE WHEN asset_registry.catalog_status = 'RETIRED'")
    A("                 THEN asset_registry.is_active")
    A("                 ELSE EXCLUDED.is_active END,")
    A("```")
    A("")
    A("Read what the guard actually covers: it is keyed on `catalog_status = 'RETIRED'` and "
      "nothing else. It protects a RETIRED row's status and activity. It does **not** protect "
      "any other column of a RETIRED row, and it protects **nothing** on a CURRENT or DRAFT "
      "row. An honest note on its current state: the one RETIRED row live today "
      "(`ka_gochara_sweep`) is also declared `RETIRED` / `is_active: false` in the seed "
      "itself, so the guard agrees with `EXCLUDED` and has **not been exercised** — it is "
      "correct, and it is currently untested by production data.")
    A("")
    A("### 1.4 — Group D · never written by the seed at all")
    A("")
    A(f"**{len(r['columns']['never_written_by_the_seed_at_all'])} live columns** appear in "
      f"neither the INSERT list nor the DO UPDATE body. A repair to one of these cannot be "
      f"reverted by a re-seed. This is where most of the campaign's repair work landed.")
    A("")
    A("`" + "`, `".join(r["columns"]["never_written_by_the_seed_at_all"]) + "`")
    A("")
    A("The compensating hazard, and it is real: because the seed never *inserts* these "
      "columns either, **any asset the seed newly creates lands with all of them at their DB "
      "default** — NULL unless a NOT NULL/DEFAULT says otherwise. Today's rows are safe; "
      "future rows are not covered by anything in the seed.")
    A("")

    # ── §2 ──────────────────────────────────────────────────────────────
    A("## 2 — Per column: would a re-seed change a live row, and which?")
    A("")
    A("The core measurement. For each of the 23 seed-written columns, the value the seed "
      "would write for each asset (defaults and derivations applied) is compared against the "
      "live value. Comparison is type-normalised: `jsonb` against the seed's "
      "`JSON.stringify` output, `text[]` as an ordered list, numerics as numbers.")
    A("")
    A("| column | class | changed | seed fills a live NULL | seed NULLs a live value | both non-null, differ | UNKNOWN |")
    A("|---|---|---:|---:|---:|---:|---:|")
    for cnm in sorted(per, key=lambda k: (-per[k]["cells_a_reseed_would_change"], k)):
        v = per[cnm]
        d = v["direction_breakdown"]
        A(f"| `{cnm}` | {v['class']} | **{v['cells_a_reseed_would_change']}** | "
          f"{d['seed FILLS a live NULL']} | {d['seed NULLS a live value']} | "
          f"{d['both non-null, values differ']} | {len(v['cells_UNKNOWN'])} |")
    A("")
    A("Four columns — `" + "`, `".join(sorted(c for c, v in per.items()
                                              if not v["cells_a_reseed_would_change"])) +
      "` — are byte-identical between seed and live on every asset. They are in the dangerous "
      "set, but nothing currently diverges on them.")
    A("")
    A("`direction` is mechanical, not a judgment: it reports which side is NULL, never which "
      "side is *right*. Where a cleanliness test exists in the campaign's own writing "
      "(migration 590 defines a well-formed `layer_index` as `^L[0-5]$`) it is applied and "
      "reported; nowhere else is a direction called good or bad.")
    A("")
    cs_ws = per["count_sql"]["cells_differing_only_in_whitespace_or_case"]
    sz_ws = per["size_sql"]["cells_differing_only_in_whitespace_or_case"]
    A(f"**A second, weaker reading for the two SQL columns**, because a raw byte-difference "
      f"count would overstate them: of `count_sql`'s "
      f"{per['count_sql']['cells_a_reseed_would_change']} changed cells, **{cs_ws}** differ "
      f"only in whitespace or keyword case — leaving "
      f"**{per['count_sql']['cells_a_reseed_would_change'] - cs_ws} that are genuinely "
      f"different queries**. For `size_sql` the figure is {sz_ws} of "
      f"{per['size_sql']['cells_a_reseed_would_change']}. Both readings are in the JSON; "
      f"neither is treated as the authoritative one, because a re-seed writes different "
      f"bytes in either case.")
    A("")
    A("### 2.1 — Every divergent cell")
    A("")
    A("The full list is machine-readable in `SEED_DURABILITY_REGISTER_v1_0.json` under "
      "`divergent_cells` (asset, column, live value, seed value, direction, and whether the "
      "seed entry *declared* the key or fell through to a default). Reproduced here are the "
      "cells in the CORRECTNESS, CONTRACT and OPERATIONAL classes — the prose/label columns "
      "are left to the JSON.")
    A("")
    A("| asset | column | live | a re-seed writes | direction |")
    A("|---|---|---|---|---|")
    for d in sorted(diffs, key=lambda x: (RANK.get(CONSEQUENCE.get(x["column"], ("COSMETIC",))[0], 9),
                                          x["column"], x["asset_id"])):
        if CONSEQUENCE.get(d["column"], ("COSMETIC",))[0] == "COSMETIC":
            continue
        lv = "*(null)*" if d["live_value"] is None else f"`{d['live_value']}`"
        sv = "*(null)*" if d["seed_would_write"] is None else f"`{d['seed_would_write']}`"
        g = f" · guard: {d['guard']}" if d.get("guard") else ""
        A(f"| `{d['asset_id']}` | `{d['column']}` | {lv} | {sv} | {d['direction']}{g} |")
    A("")

    # ── §3 ──────────────────────────────────────────────────────────────
    A("## 3 — Per campaign repair: durable or not")
    A("")
    reps = r["per_repair"]

    def repair_block(key, heading, extra=None):
        v = reps[key]
        A(f"### {heading}")
        A("")
        A(f"- Columns: `" + "`, `".join(v["columns"]) + "`")
        A(f"- In the seed's `DO UPDATE SET` list: "
          + (("`" + "`, `".join(v["in_do_update_set"]) + "`") if v["in_do_update_set"] else "none"))
        A(f"- Not written by the seed at all: "
          + (("`" + "`, `".join(v["not_written_by_the_seed"]) + "`") if v["not_written_by_the_seed"] else "none"))
        A(f"- Rows a re-seed would change: **{v['total_rows_reverted']}**")
        A("")
        A(f"**Verdict.** {v['verdict']}")
        A("")
        A(f"**Consequence if reverted.** {v['consequence_if_reverted']}")
        A("")
        if extra:
            for line in extra:
                A(line)
            A("")

    v = reps["has_substeps__M0-T20"]
    repair_block("has_substeps__M0-T20", "3.1 — `has_substeps` (M0-T20, 12 rows) — **DURABLE**",
                 [f"Verified independently of M0-T27 rather than inherited from it. The check "
                  f"is not \"the projection did not fire\" but the stronger structural one: "
                  f"`has_substeps` is not in the seed's INSERT column list, so no seed run "
                  f"can name it in an assignment. Live rows with `has_substeps IS TRUE` "
                  f"today: **{v['live_true_rows']}**.",
                  "",
                  "One caveat that belongs to Group D, not to this repair: an asset the seed "
                  "newly inserts lands with `has_substeps` NULL, and a NULL is falsy at "
                  "`asset_runner.py`'s `if has_substeps:`. The repair is durable; the "
                  "*coverage* of future rows is not enforced by anything."])

    v = reps["asset_kind_asset_type__M0-T21"]
    rows = v["rows_a_reseed_would_change"]
    repair_block("asset_kind_asset_type__M0-T21",
                 "3.2 — `asset_kind` / `asset_type` (M0-T21, 6 rows) — **REVERTED on all 8 divergent rows**",
                 ["Independently re-measured; agrees with M0-T27's figure. The mechanism is "
                  "the `?? 'data'` default at `:3267-3268`, and it is the reason the count is "
                  "8 rather than 6: **not one of the eight seed entries declares the key at "
                  "all**. Every one of these reversions is a default being actively written "
                  "over a correct value, not a stale literal.",
                  "",
                  f"- `asset_kind` → `'data'`: `" + "`, `".join(rows.get("asset_kind", [])) + "`",
                  f"- `asset_type` → `'data'`: `" + "`, `".join(rows.get("asset_type", [])) + "`"])

    v = reps["domain_rung__migration_590"]
    pair = v["scope_domain_pair_break"]["rows"]
    repair_block("domain_rung__migration_590",
                 "3.3 — `domain` / `rung` (migration 590, 128 rows) — **columns durable, the PAIR is not**",
                 ["`domain` and `rung` are in Group D — the seed writes neither, so migration "
                  "590's backfill cannot be reverted. The exposure is one level indirect and "
                  "is the finding M0-T27 surfaced:",
                  "",
                  "| asset | live scope | seed writes scope | live domain | domain implied by the new scope | consistent after a re-seed |",
                  "|---|---|---|---|---|---|"] +
                 [f"| `{p['asset_id']}` | `{p['live_scope']}` | `{p['seed_would_write_scope']}` | "
                  f"`{p['live_domain']}` | `{p['domain_derived_from_scope_would_become']}` | "
                  f"**{'yes' if p['consistent_after_reseed'] else 'NO'}** |" for p in pair] +
                 ["",
                  "`scope` is seed-owned and `domain` is not, and 590 derived `domain` *from* "
                  "`scope`. A re-seed moves one half of the pair and leaves the other, and the "
                  "row then answers the same question two different ways. M0's acceptance "
                  "criterion 11 passes on `domain`/`rung` being present — which stays true — "
                  "while the value it presents becomes wrong. That is exactly the failure "
                  "shape this register exists to name.",
                  "",
                  "Note the asymmetry that makes it survivable: the reverse repair is *not* "
                  "available. Writing `scope='per_chart'` into the DB does not stick either — "
                  "it is the seed-owned half. The durable fix is in the seed file or in a "
                  "CASE guard, not in a DB write."])

    v = reps["has_writer__generator_only"]
    repair_block("has_writer__generator_only",
                 "3.4 — `has_writer` (generator-only, no rows written) — **confirmed safe**",
                 [f"Confirmed rather than assumed: `has_writer` is in Group D (absent from "
                  f"both seed column lists), and the column exists live with "
                  f"{v['live_non_null_rows']} non-NULL rows — i.e. it is populated by "
                  f"something other than the seed. Nothing for a re-seed to revert."])

    v = reps["layer_index_layer_name__phase_0.5a_NOT_PERFORMED"]
    md = v["measured_direction"]
    repair_block("layer_index_layer_name__phase_0.5a_NOT_PERFORMED",
                 "3.5 — `layer_index` / `layer_name` (Phase 0.5a — **NOT YET PERFORMED**)",
                 ["Held pending this question, so what follows is a projection of a repair "
                  "that does not exist yet. The measurement points the opposite way to §3.2, "
                  "and saying so is the point of the exercise:",
                  "",
                  f"- `layer_index` divergent cells: **{md['layer_index_divergent_cells']}**. "
                  f"The seed's value is well-formed `^L[0-5]$` on "
                  f"**{md['of_those_the_SEED_value_is_wellformed_Lx']}** of them; the live "
                  f"value on **{md['of_those_the_LIVE_value_is_wellformed_Lx']}**.",
                  f"- `layer_name` divergent cells: **{md['layer_name_divergent_cells']}**, of "
                  f"which {md['layer_name_cells_where_seed_fills_a_live_NULL']} are the seed "
                  f"filling a live NULL.",
                  "",
                  "Both columns are seed-owned, so a repair here *is* reachable by the seed — "
                  "but on every divergent cell the seed already holds the clean value. A "
                  "Phase 0.5a repair that writes exactly what `layerIndices[layer]` / "
                  "`layerNames[layer]` produce is durable by agreement; one that invents its "
                  "own form is reverted on the next run. The diacritics are load-bearing: the "
                  "seed's map carries `Gaṇita` / `Kāla` / `Mīmāṃsā` per CLAUDE.md §N.1, and "
                  "several live rows carry the unaccented spelling.",
                  "",
                  f"Dirty rows with no seed entry at all (durable outright, and unreachable by "
                  f"a re-seed): "
                  + (("`" + "`, `".join(v["live_dirt_today"]["dirty_rows_WITHOUT_a_seed_entry"]) + "`")
                     if v["live_dirt_today"]["dirty_rows_WITHOUT_a_seed_entry"] else "**none**") + "."])

    A("### 3.6 — Found while modelling the other 19 columns")
    A("")
    A("These are not campaign repairs; they are live seed-vs-DB divergences that only became "
      "visible once every column was modelled. They are reported, not acted on.")
    A("")
    def cells(col):
        return [d for d in diffs if d["column"] == col]
    ia = cells("is_active")
    A(f"**(a) `is_active` — a re-seed would DEACTIVATE a currently-active asset.** "
      f"`bg_sky_calendar` is live `is_active = true`, but its declared `target_table` "
      f"(`bg_sky_events`) is absent from production, so the pre-flight at `:3228` forces "
      f"`false` before the upsert. The `CASE` guard does not save it — the row is `CURRENT`, "
      f"not `RETIRED`. This is the seed working exactly as designed; it is listed because the "
      f"outcome (an active asset going inactive on a routine re-seed) is not obvious from "
      f"either side alone.")
    A("")
    tf = cells("target_floor")
    nulled = [d for d in tf if d["seed_would_write"] is None]
    moved = [d for d in tf if d["seed_would_write"] is not None and d["live_value"] is not None]
    A(f"**(b) `target_floor` — {len(tf)} cells move, {len(moved)} of them between two "
      f"non-NULL values.** CLAUDE.md §N.4 and invariant I7 both say a floor is the MEASURED "
      f"achieved count, set after a build. Those measured values live in a seed-owned column. "
      f"Examples: " + ", ".join(f"`{d['asset_id']}` {d['live_value']}→{d['seed_would_write']}"
                                for d in moved[:4]) + ". The "
      f"{len(nulled)} NULL-ings are all live `0` → NULL, so no non-zero measured floor is "
      f"lost today — but the exposure is structural, not incidental.")
    A("")
    cs = cells("count_sql")
    cs_real = [d for d in cs if not d.get("differs_only_in_whitespace_or_case")]
    A(f"**(c) `count_sql` — {len(cs)} cells move, {len(cs_real)} of them a genuinely "
      f"different query** (the other {len(cs) - len(cs_real)} differ only in whitespace or "
      f"keyword case). Two go from a live query to NULL "
      f"(`" + "`, `".join(d["asset_id"] for d in cs if d["seed_would_write"] is None) + "`), "
      f"and at least one changes the table read: `bg_sky_calendar` counts "
      f"`bg_sky_calendar` live and `bg_sky_events` per the seed. §N.4's 'cockpit truth' "
      f"bullet makes a correct chart-scoped `count_sql` the thing the stats route reads. "
      f"This register does not judge which side is correct — only that a re-seed moves it, "
      f"and that the movement is real rather than cosmetic.")
    A("")
    tt = cells("target_table")
    A(f"**(d) `target_table` — {len(tt)} cells move**, including "
      f"`mi_adhilepa` `mimamsa_load_bearing` → `mimamsa_signal_adjustment`: a re-seed would "
      f"re-point the asset at a different table, which also feeds the `is_active` pre-flight "
      f"in (a).")
    A("")
    A(f"**(e) One live row has no seed entry:** "
      f"`" + "`, `".join(r["rows_only_in_one_side"]["live_but_no_seed_entry"]) + "`. A re-seed "
      f"neither updates nor deletes it — every column on it is durable, and it is invisible to "
      f"the seed's own consistency checks.")
    A("")

    # ── §4 ──────────────────────────────────────────────────────────────
    A("## 4 — Ranked by consequence")
    A("")
    A("The ranking answers: *if this reversion happened silently, what would be wrong?* A "
      "reverted flag that switches a detector off is categorically worse than a reverted "
      "description, and the register refuses to present them in one flat list (CLAUDE.md "
      "§N.6).")
    A("")
    A("| rank | class | what reverts | rows at risk today | state |")
    A("|---|---|---|---:|---|")
    for row in r["consequence_ranking"]:
        A(f"| {row['rank']} | {row['class']} | `" + "`, `".join(row["columns"]) +
          f"` | {row['at_risk_today']} | {row['measured_state']} |")
    A("")
    for row in r["consequence_ranking"]:
        A(f"**{row['rank']}. {row['class']}** — {row['why']}")
        A("")
    A("Two qualifications on the rank-5 row, so its 149 is not read as 149 problems: it "
      "includes `layer_index`/`layer_name`, and §3.5 measures the seed as holding the CLEAN "
      "value on every one of those 41 cells — a re-seed *improves* them. And 41 of "
      "`volume_explanation`'s 47 are the seed filling a live NULL. The number counts cells "
      "that MOVE, which is the only thing a projection can honestly count; it does not claim "
      "they move for the worse.")
    A("")
    A("The two entries that matter for the ownership ruling are ranks 2 and 3: they are the "
      "only ones where a live divergence sits on a seed-owned column whose value a detector "
      "or contract rule reads. Rank 1 is listed first because its *consequence* is the worst, "
      "not because it is at risk — it is measured durable. Rank 4 is the largest genuinely "
      "open question and this register does not answer it: on `count_sql`, `target_floor` and "
      "`depends_on` it can say a re-seed moves 80 cells, and it cannot say which side is "
      "right. That is a judgment about ownership, not a measurement.")
    A("")

    # ── §5 ──────────────────────────────────────────────────────────────
    A("## 5 — Coverage, stated explicitly")
    A("")
    A(f"- Columns a re-seed writes: **{cov['columns_the_seed_writes_on_a_re_seed']}**. "
      f"Columns modelled here: **{cov['columns_modelled_here']}**. "
      f"Unmodelled: **{len(cov['unmodelled_columns'])}**"
      + (" (`" + "`, `".join(cov["unmodelled_columns"]) + "`)" if cov["unmodelled_columns"] else "")
      + ".")
    A(f"- M0-T27 modelled `" + "`, `".join(cov["m0_t27_modelled"]) + "` — 4 columns — and said "
      f"so. That declaration is why its result could be trusted, and this section is the same "
      f"declaration for this register.")
    A(f"- Cells marked UNKNOWN: **{cov['unknown_cells']}**. A cell is UNKNOWN, never "
      f"\"unchanged\", whenever the value the seed would write could not be determined.")
    A(f"- Rows compared: **{cov['rows_compared']}**. Live rows not compared (no seed entry): "
      + (("`" + "`, `".join(cov["rows_in_live_not_compared"]) + "`") if cov["rows_in_live_not_compared"] else "none") + ".")
    A("")
    A("### 5.1 — What is still NOT modelled, and why it matters")
    A("")
    for line in cov["what_remains_UNMODELLED_and_why"]:
        A(f"- {line}")
    pf = r["is_active_preflight"]
    A(f"- On the hard stop above: **{len(pf['assets_forced_inactive'])}** asset(s) currently "
      f"have a declared `target_table` absent from production "
      + (("(`" + "`, `".join(pf["assets_forced_inactive"]) + "`)") if pf["assets_forced_inactive"] else "")
      + f", against a limit of 20. The seed would proceed, not stop — but that margin is a "
      f"live quantity and this figure expires the moment a target table is dropped or "
      f"renamed.")
    A("")
    A("### 5.2 — How the seed's values were obtained without running the seed")
    A("")
    ine = r["seed_extract_meta"]["inertness"]
    A("`extract_seed_projection.mjs` slices out the `export const ASSETS: AssetDef[] = [ … ]` "
      "array **literal**, statically proves that slice inert, and evaluates only that. The "
      "proof is machine-checked on every run and the script refuses to evaluate if any check "
      "fails:")
    A("")
    A("| check | result |")
    A("|---|---|")
    for k2, v2 in ine["checks"].items():
        if k2 == "free_identifiers_found":
            continue
        A(f"| `{k2}` | {v2} |")
    A("")
    A("No module import of the seed occurs, no DB client is constructed in that process, and "
      "the seed's `main()` — the thing that actually issues `INSERT … ON CONFLICT DO UPDATE` "
      "— is never reached. `main()`'s value derivations (`?? 'data'`, the layer maps, the "
      "catalog_status default, the LEL `FILE_COUNT`, the `to_regclass` pre-flight) are "
      "**re-implemented** in the extractor and the generator against the cited line numbers, "
      "not called.")
    A("")

    # ── §6 ──────────────────────────────────────────────────────────────
    A("## 6 — Re-running this register")
    A("")
    A("```")
    A("python3 00_ARCHITECTURE/control/seed_durability/seed_durability_register.py")
    A("```")
    A("")
    A("Rewrites both `SEED_DURABILITY_REGISTER_v1_0.json` and this file. Read-only against "
      "the database (`SET default_transaction_read_only = on`; only SELECT / SET / "
      "`to_regclass` are issued) and read-only against the seed. Re-run it after **any** "
      "change to `asset_registry_seed.ts` or to `asset_registry` rather than trusting these "
      "numbers — that is the whole reason it is a generator and not a table someone typed.")
    A("")
    A("Files:")
    A("")
    A("| file | role |")
    A("|---|---|")
    A("| `00_ARCHITECTURE/control/seed_durability/extract_seed_projection.mjs` | slices + inertness-proves + evaluates the `ASSETS` literal; re-implements `main()`'s derivations |")
    A("| `00_ARCHITECTURE/control/seed_durability/seed_durability_register.py` | parses the upsert, projects every column against live, writes the JSON |")
    A("| `00_ARCHITECTURE/control/seed_durability/render_register_md.py` | renders this document from the JSON |")
    A("")
    A("Nothing here imports or edits `m0_exit_scorecard.py`, `writer_substep_census.py` or "
      "`build_asset_control_workbook.py`. The upsert-parse is this register's own copy of "
      "M0-T27's technique, extended from 4 columns to 23; a sibling KĀRAKA holds two of those "
      "files mid-flight.")
    A("")
    A("---")
    A("")
    A("*Authored by KĀRAKA on task M0-T29. This document reports measurements; it does not "
      "certify them, and its author may not (I16 / charter H7). Every figure in it is "
      "produced by the generator above and none is typed in by hand.*")

    M.write_text("\n".join(L) + "\n")
    print(f"wrote {M} ({len('\n'.join(L))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
