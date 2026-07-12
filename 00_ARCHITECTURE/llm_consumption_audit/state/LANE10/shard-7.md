# LANE 10 — Promise-vs-Delivery — Shard 7 (L5 Mīmāṃsā, 7 assets)

Charter §7.5 attribution tree. Charts: Abhisek `482012f1-710e-4a25-994a-93821f5871aa` (primary),
Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (secondary). DEPLOYED channel tested (read-only).

## Promise re-sourcing (all 7 arrived promise_quote=NOT FOUND)
4-source search: (1) build brief — no `CLAUDECODE_BRIEF_mi_*` exists, BUT per-asset specs exist under
`00_ARCHITECTURE/L5_SPECS/` (01_mi_jivanaghatana … 09_mi_darshana etc.); (2) `asset_registry.english_description`
present for all 7 (quoted below); (3) closure doc `L5_SEAL_AND_SHIP_REPORT_v1_0.md` — L5 sealed in STRUCTURAL
mode by design; (4) MCP tool descriptions for the 3 fronting tools. → promise_status = **re-sourced** for all 7.

## Deployed mimamsa-fronting read tools (from tools/list, 130 tools)
- `mimamsa_insight_get` → mi_darshana (insight_units)
- `mimamsa_calibration_get` / `query_calibration` → mi_pramana (calibration+reliability) AND surfaces mi_gunanaka multipliers
- `mimamsa_lel_query` / `lel_query` → mi_jivanaghatana (LEL)
- **NO fronting tool** for: mi_kula (signal_families), mi_pariksha (qa_eval/attribution/discoveries), mi_sambandha (manifestation_grammar)

## Data-plane counts (verbatim, both charts)
| table | Abhisek 482012f1 | Abhinandan 1c826d5a |
|---|---|---|
| mimamsa_insight_units | 74 | 30 |
| mimamsa_insight_embeddings | 0 | 0 |
| mimamsa_multipliers | 9 | 9 |
| mimamsa_event_provenance | 57 | 0 |
| mimamsa_signal_families (global) | 11 | 11 |
| mimamsa_negative_controls (global) | 4 | 4 |
| mimamsa_qa_eval | 141 | 6 |
| mimamsa_attribution | 0 | 0 |
| mimamsa_discoveries | 45 | 0 |
| mimamsa_calibration | 0 | 0 |
| mimamsa_reliability | 0 | 0 |
| mimamsa_manifestation_grammar | 20 | 20 |

## Deployed-payload evidence
- `mimamsa_insight_get(482012f1)` → real insight_units with statements ("Career Setback: promised (grade 7.2/10)…"),
  provenance_chain, confidence_band, evidence_grade=structural. Usable. Does NOT return embeddings.
- `mimamsa_calibration_get(482012f1)` → `verdict_distribution:[]`, `reliability_curve:[]` (EMPTY, matches DB 0/0),
  multipliers present (`promotion_status:"prior_only"`, `n_observations:0`, kill_switch active).
- `mimamsa_lel_query(482012f1)` → LEL signals populated (frame=lagna, two_pass_verified). Usable.

## Per-asset verdicts
- **mi_darshana (AP-050)** — PARTIAL / data-plane. Insight units + provenance DELIVER via mimamsa_insight_get; but
  promise "with embeddings" → mimamsa_insight_embeddings = **0/0 both charts**, embeddings never written, no vector
  path over insights. Class 4.
- **mi_gunanaka (AP-051)** — DELIVERS (modest). multipliers 9/9 present, reachable via mimamsa_calibration_get.multipliers.
  "Empirical/learned" facet is prior_only (n=0) by STRUCTURAL-seal design — noted, not a shortfall against declared intent.
- **mi_jivanaghatana (AP-052)** — DELIVERS. event_provenance 57 (primary) served via mimamsa_lel_query, usable.
  Abhinandan 0 is expected (LEL is native-specific life-event ground truth).
- **mi_kula (AP-053)** — SHORTFALL / retrieval-plane. 11 families + 4 negative_controls computed but NO MCP tool serves
  the family registry / negative-control battery. Class 1 UNREACHABLE.
- **mi_pariksha (AP-054)** — SHORTFALL / compound. qa_eval 141/discoveries 45 present but NO fronting tool
  (retrieval-plane, class 1); mimamsa_attribution = **0/0 both charts** (data-plane empty, class 4).
- **mi_pramana (AP-055)** — SHORTFALL / data-plane. calibration 0/0 + reliability 0/0 both charts; tool reachable but
  returns empty verdict_distribution/reliability_curve. HONESTLY declared STRUCTURAL/prior_only (not class 5). Class 4,
  by-design-empty per L5 seal — low severity.
- **mi_sambandha (AP-056)** — SHORTFALL / retrieval-plane. manifestation_grammar 20/20 computed but NO fronting tool
  serves it as a queryable per-native grammar surface. Class 1 UNREACHABLE.
