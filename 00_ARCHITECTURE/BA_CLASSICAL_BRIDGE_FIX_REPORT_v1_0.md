---
artifact: BA_CLASSICAL_BRIDGE_FIX_REPORT
type: FIX_REPORT
version: 1.0
status: COMPLETE
authored_by: Claude Code (autonomous session, CLAUDECODE_BRIEF_B_CLASSICAL_BRIDGE_v1_0.md)
date: 2026-07-05
chart_id_proof: 1c826d5a-41cb-4450-b4dc-59d440e5f75a  # Abhinandan Mohanty (limited-scope proof chart)
gate: PASS — ≥60% classical-source coverage on yoga/dosha signal classes
---

# BA Classical Bridge Fix Report — bo_laksana L0 Classical Bridge (Phase 2)

## §0 — Root cause (confirmed, refined from brief's hypothesis)

The brief's premise was correct in outcome (0% coverage) but slightly off on mechanism. `bo_laksana.py`
(pre-fix, L928–933) only read `fvj.get("classical_citation_id") or fvj.get("citation_id")` — keys that
**L1 chart_facts never populate**. Direct inspection of `chart_facts` on chart `482012f1` confirmed:

- 100% of `yoga_label` (409/409) and `dosha_label` (110/110) facts carry a **`fact_value_jsonb.classical_citations`**
  array (`{chapter, text_id, chunk_id, verse_ref}` objects) — already attached at L1 build time.
- 0% carry `classical_citation_id`/`citation_id`.
- `fact_subject` (e.g. `"akriti"`, `"ruchaka"`) **is** the `canonical_id` used by `brahma_yoga_catalog` /
  `brahma_dosha_catalog` — confirmed by direct join (all sampled fact_subjects resolved).

So the missing piece was not a catalog *table* join so much as reading the citation data L1 had already
attached, plus a confirmatory join to the catalog/rule corpus for `catalog_ids`/`rule_ids`.

## §1 — Join keys verified before coding

| Table | Join key | Status |
|---|---|---|
| `brahma_yoga_catalog` | `canonical_id` == `chart_facts.fact_subject` (yoga_label/yoga_fires/graha_yoga_karaka_flag) | CONFIRMED — sample resolved |
| `brahma_dosha_catalog` | `canonical_id` == `chart_facts.fact_subject` (dosha_label/dosha_fires) | CONFIRMED — sample resolved |
| `classical_text_chunks` | `id` (uuid) == `fvj.classical_citations[].chunk_id` | CONFIRMED — sample resolved |
| `sutravali_rules` | `yoga_canonical_id` == canonical_id | **CORPUS GAP**: 2,912 rules exist but 0 rows have `yoga_canonical_id` populated (unbackfilled). Rule-derived citations are floor-NULL until this backfill happens — tracked separately, does not block the gate below since `catalog_ids` + fact-level `citations`/`text_chunk_ids` already clear ≥60%. |

## §2 — Implementation

`platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py`:

- `_build_classical_catalog_lookup(conn)` — bulk-preloads `brahma_yoga_catalog`/`brahma_dosha_catalog`
  canonical_ids and `sutravali_rules.yoga_canonical_id → [rule_id]` **once per sub-step** (5 ayanamshas),
  not per-row.
- `_collect_referenced_chunk_ids` + `_validate_chunk_ids(conn, ids)` — one bulk query per sub-step
  confirming which `chunk_id`s referenced in facts actually exist in `classical_text_chunks` (no
  fabricated/broken chunk refs).
- `_build_classical_sources(...)` — deterministic, no LLM: reads `fvj.classical_citations` directly for
  `citations`/`text_chunk_ids`; joins `fact_subject` against the preloaded catalog sets for `catalog_ids`
  (+ `rule_ids` via `sutravali_rules`, currently empty pending the corpus backfill above). Returns `None`
  (floor-NULL) when a signal genuinely carries no classical source — never fabricates.
- Threaded through `_build_signal_row` (new optional `classical_catalog` param, backward compatible —
  existing unit tests pass unmodified) and wired into `run_substep`.
- Populates both `classical_sources_jsonb` (structured: `catalog_ids`/`rule_ids`/`text_chunk_ids`/`citations`)
  and `classical_sources_array` (flat, deduped).

## §3 — Limited-scope proof (Abhinandan, `1c826d5a-…`, `scope=asset`)

Rebuilt `bo_laksana` only (run `23960990-b698-4414-bf6f-9a1351689485`, `state=completed`, no error) via
`POST /api/cockpit/runs {chart_id, scope:"asset", scope_target:"bo_laksana", action:"rebuild"}` against the
deployed prod backend, then verified directly on prod Postgres:

| `signal_type_class` | total | has classical source | coverage |
|---|---|---|---|
| `dosha` | 110 | 88 | **80.0%** |
| `yoga` | 441 | 333 | **75.5%** |

**Both clear the ≥60% gate.** (Note: the brief's verification query filtered `signal_type_class='configuration'`
— that class does not correspond to yoga/dosha signals in `bo_laksana`'s `_signal_type_class` mapping;
`kala_sarpa`-family facts land there instead. The correct filter, confirmed against the writer's own
category→class mapping, is `signal_type_class IN ('yoga','dosha')`, used above.)

**Spot-check (5 random signals with a classical source):**

| signal_type_id | catalog_id | resolves? | text_chunk_id | resolves? | citation |
|---|---|---|---|---|---|
| `dosha_label:dosha_name` | `balarishta_sandhi` | ✅ brahma_dosha_catalog | — | — | `bphs:9` |
| `yoga_label:yoga_name` | `kedara` | ✅ brahma_yoga_catalog | — | — | `bphs:35` |
| `yoga_label:yoga_name` | `raja` | ✅ brahma_yoga_catalog | `ab0a24c9-…` | ✅ classical_text_chunks | `bphs:369` |
| `yoga_label:yoga_name` | `papa_kartari` | ✅ brahma_yoga_catalog | `65337162-…` | ✅ classical_text_chunks | `bphs:955` |
| `yoga_label:yoga_name` | `dhana` | ✅ brahma_yoga_catalog | `d67b253f-…` | ✅ classical_text_chunks | `bphs:7` |

**Regression / degeneracy check:** signal counts and `computed_salience` distributions across all 11
`signal_type_class` values are unchanged in shape (composite_state=54,142, karaka_alignment=6,019,
yoga=441, dosha=110, …, all with sane non-degenerate salience averages and multiple signature tiers) —
this fix touches citation columns only, confirming no ranking/salience regression.

## §4 — Commit + ship

- Branch: `fix/ba-classical-bridge`, created from `fix/ba-rebuild-live-abhinandan` HEAD.
- Commit: `824f0c65` — "fix(bo-laksana): implement L0 classical bridge for yoga/dosha citations"
- PR: [#431](https://github.com/amonty84/Madhav/pull/431) — CI green (Unit Tests, Governance Gates,
  Coverage Gate, Planner Regression Gate, TypeScript, ICR PR Gate, Build Check all passed); pre-existing
  unrelated failures (`test_b6_eval_harness` magnitude gates on `bo_anveshana`/`bo_cgm_paths`/`bo_sangati`,
  a stale `test_dict_row_fixes` fixture) confirmed present on branch HEAD **before** this change too (not
  caused by this diff).
- Merged to `main`: squash commit `698b68df7bf79a495c3d1038beaff661c6a301da`.
- Deploy: GH Actions run `28721393123` ("Deploy to Cloud Run") — succeeded.
- **JOB image**: `asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:698b68df7bf79a495c3d1038beaff661c6a301da`
  (+ `:latest`) built, pushed, verified (`ga_writers` importable), and `brahma-build-pipeline-job`
  (Cloud Run Job, `asia-south1`) re-pointed to it.

## §5 — Exit / gate verdict

**GATE: PASS.** ≥60% classical-source coverage proven on the limited-scope Abhinandan build
(yoga 75.5%, dosha 80.0%), citations spot-verified against real `brahma_yoga_catalog` /
`brahma_dosha_catalog` / `classical_text_chunks` rows, zero salience/ranking regression. **Phase 2 is
COMPLETE — feeds Phase 3 (full run).**

**Tracked follow-on (not blocking):** `sutravali_rules.yoga_canonical_id` is unpopulated corpus-wide
(2,912 rules, 0 linked) — rule-derived citations (`rule_ids`) will stay empty until that backfill lands.
This is a separate corpus workstream, flagged for discussion before any rule-citation-specific gate is
set.
