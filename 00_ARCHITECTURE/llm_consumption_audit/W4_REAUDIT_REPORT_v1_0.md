---
artifact: W4_REAUDIT_REPORT_v1_0
type: W4 FINAL RE-AUDIT (plan §2 ten-gate measurement against DEPLOYED + REBUILT prod)
version: 1.0 (DRAFT — in flight)
status: IN_PROGRESS
governing_plan: 00_ARCHITECTURE/llm_consumption_audit/REMEDIATION_PLAN_v3_0.md §2
measured_by: W4 wave-conductor (fresh context), 2026-07-13
system_under_test: main HEAD e1d601f2 (W2 code, deployed web amjis-web + mcp amjis-mcp);
  both charts rebuilt on deployed code (native 482012f1 §W3.2, Abhinandan 1c826d5a §W3.1)
channel: deployed prod MCP connector mcp__marsys-jis-direct__* (api_key) + prod DB read (:5433)
---

# W4 Re-Audit — 10-Gate Measurement Report

Measured against the DEPLOYED + REBUILT production system (not local). Honest measurement
discipline (plan §8.4): honest NOT-MET beats a gamed PASS. Read-only against prod.

## Headline verdict
(pending agent completion — filled at close)

## Gate-by-gate results

_(table assembled below as each gate resolves)_

---

## Gate 2 — Class-9 improvisation (MEASURED + categorized) — MET-as-disposition
- W4 gate: "measured + categorized (doctrine campaign gates it)" — not a pass/fail threshold.
- **Measured: 135 findings → DOCTRINE-DEFERRED** in `wp_coverage.jsonl` (exact match to plan §3
  distribution). These transfer to the post-W4 doctrine campaign as its requirements corpus — a
  tracked disposition, not a remediation gap. **DISPOSITION HONORED.**

## Gate 10 — Tool hard-failures (500/dead/blank-dishonest) — **FAIL** (gate: 0)
Independently re-probed live on the deployed channel (native chart). **≥9 tools hard-fail**, plus a
cluster of dishonest-blank/filter-lie serves. Root cause is isolated to the ref_*/legacy-alias +
registry + param-plumbing layer — the underlying engines are healthy (working twins pass).

### 9 confirmed hard-failures (each returns an error / is_error:true on the deployed channel)
| Tool | Live result | Class | Working twin |
|---|---|---|---|
| `asset_registry_all` | `{error:true, [l0_brahmagyan] platform GET /api/cockpit/registry → 401}` | cockpit auth 401 | catalog_assets_all (PASS) |
| `asset_registry_l0` | cockpit GET ?layer=brahmagyan → 401 | cockpit auth 401 | catalog_assets_l0 (PASS) |
| `ref_aspects_at_time_get` | `ok:false, sidecar 401 Invalid API key` | sidecar auth (LCA-13 family) | query_aspects_at_time (PASS) |
| `ref_planet_transit_get` | `ok:false, sidecar 401 Invalid API key` | sidecar auth | query_planet_transit (PASS) |
| `ref_retrograde_periods_get` | `ok:false, sidecar 401 Invalid API key` | sidecar auth | query_retrograde_periods (PASS, 2 Venus stations 2026) |
| `ref_planet_position_get` | `ok:false, sidecar 500: invalid input syntax for type date: "undefined"` | param-mapping → 500 | query_planet_position (PASS) |
| `ref_transit_rules_get` | `ok:false, [p1_reference] platform DB query failed: 400` | query/param bug | (bg_transit_rules engine) |
| `ref_ephemeris_year_get` | `ok:false, 404 Unknown capability URI marsys://resource/ephemeris-cache/year/2026` | unregistered URI (LCA-12 family) | ephemeris_cache_year (PASS) |
| `traverse_graph` | `is_error:true, "Could not parse address expression: \"l\""` (about DSL truncated to 1st char) | param-handling bug on a FLAGSHIP graph tool | bodha_graph_traverse_get (PASS) |

### Dishonest-blank / filter-lie serves (E5 "never serve blank/dishonest" violations — additional)
- `query_remedies(planet=Venus)` → returns 20 **JUPITER** rows (`total:266`); the `planet` filter is
  **silently ignored** — serves the wrong planet's data with no disclosure. (Worst of the set.)
- `list_remedies_by_category(gemstones)` → `returned_count:0`, no `empty_reason` (dishonest-blank).
- `ganita_positions_get(planet=Venus)` → `rows:[], total:0, is_error:false` while unfiltered returns
  rows — filter-vocab bug, silent empty.
- Census-corroborated siblings (same family, not re-probed here): `query_mantras`/`ref_mantras_get`
  ("Venus" 0 vs "venus" 25 = case-sensitivity), `get_positions` (filter vocab), `query_tantric_remedies`,
  `ref_remedies_by_category_list`, `ref_yogas_get` (0, no empty_reason), `yoga_activation_by_dasha`
  (0 activated over 3yr — suspected broken yoga→dasha join; discloses provenance but no empty_reason).

**Verdict: FAIL (measured ≥9 hard-failures + ~6-9 dishonest-blank/filter serves; gate requires 0).**
**Conductor-fixable** (serving-layer only, no frozen-contract change): (a) wire the sidecar API key for
the ref_* alias family; (b) fix cockpit-registry auth for asset_registry_*; (c) fix the ref_* alias
param-mapping (undefined date, DSL truncation in traverse_graph, transit_rules query, ephemeris URI
registration); (d) honor `planet`/`category` filters + emit honest `empty_reason` on the remedy/position
family. NONE require rebuild or writer changes. Data is reachable via working twins — but the gate is
tool-level and these tools hard-fail.

## §3 coverage-enforcement (part 1 — finding→WP mapping) — CLEAN
- **1,009/1,009 finding_ids mapped to exactly one WP; 0 unmapped; 0 duplicates.** Distribution matches
  plan §3 exactly: WP-1.3=295, WP-1.7=172, DOCTRINE-DEFERRED=135, WP-1.2=79, WP-1.5=78, WP-2.3=66,
  WP-1.4=48, WP-2.4=40, WP-2.5=29, WP-2.1=27, WP-2.2=19, WP-1.8=10, WP-1.1=7, WP-0.1=4.
- Part 2 (per-class LCA/R/KP disposition cross-check): pending agent C.

---

_(gates 1, 3, 4, 5, 6, 7, 8 + §3 part-2 filled from the four measurement agents)_
