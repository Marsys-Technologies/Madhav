---
canonical_id: MCP_SYSTEM_AUDIT_FIX_PLAN
version: 1.0
status: DRAFT-FOR-REVIEW — prioritized fix-wave plan from the 360° audit (~31 findings)
created: 2026-07-01
author: Cowork (from the live MCP audit) — for native Abhisek Mohanty
parent: MCP_SYSTEM_AUDIT_FINDINGS_v1_0 (the evidence) + MCP_SYSTEM_AUDIT_PLAN_v1_0 (the plan)
execution: Cowork authors per-wave CLAUDECODE briefs; Claude Code implements (per the split)
changelog:
  - v1.0 (2026-07-01): First fix-wave plan. 5 waves by leverage×owner. Wave 1 = the ayanamsha one-liner that
    unblocks the whole insight surface.
---

# MCP SYSTEM AUDIT — FIX-WAVE PLAN (v1.0)

> ~31 findings across A–H. The through-line: **the system is richly built, astrologically correct at the fact
> level, and honestly engineered — but a small number of SERVING bugs hide the data, and a deeper ASTROLOGICAL-
> MODEL gap (salience + synthesis) sits between "serving" and "acharya-grade."** Waves are ordered by
> leverage-per-effort. Wave 1 is a one-liner with system-wide impact.

## The finding→cause map (why 31 findings are really ~7 fixes)
| Root cause | Findings | Owner |
|---|---|---|
| Ayanamsha default/vocabulary mismatch | F-006, F-011, F-031 | MCP/RET (fast) |
| Runtime capability/resource registration | F-001, F-002, F-018, F-027 | MCP |
| Surgical-whitelist + method + void + auth-route | F-004, F-015, F-016, F-003 | MCP/PLAT |
| Output token-bounding (verbosity inert, giant payloads) | F-008, F-021, F-023, F-026, F-029 | MCP/L2 |
| L2 domain-filter schema gap | F-009, F-022 | L2/RET |
| **Salience model + synthesis (the astrological core)** | **F-007, F-020, F-024, F-025** | **L2 Bodha (deep)** |
| L4 phala schema drift + sidecar reliability | F-005, F-014, F-013, F-012, F-030 | L4/infra |
| Machine-grounding orphan (constituent_facts) | DEFECT-001 | RET/L2 (MSR rebuild) |

## WAVE 1 — THE AYANAMSHA UNBLOCK (do FIRST; highest leverage in the whole audit)
**Owner: MCP/RET. Effort: tiny. Impact: lights up the entire L2 insight surface.**
- Fix the default ayanamsha so tools query the id the data is stored under (`lahiri_chitrapaksha`), OR alias
  `LAHIRI`→`lahiri_chitrapaksha` at the query layer (F-006/F-011). Standardize the canonical ayanamsha vocabulary
  + aliases across ALL tools (F-031).
- **Acceptance:** get_signals / get_chart_orientation / get_domain_reading / get_temporal_windows return data on
  the DEFAULT call (no explicit ayanamsha needed). Re-run the live connector probe — orientation non-empty by default.
- This single change flips the product from "sealed but empty" to "serving." Verify on prod, ≥2 charts.

## WAVE 2 — SERVING WIRING (unblock the dark tool families)
**Owner: MCP/PLAT. Effort: small (mostly one-liners). Impact: ~15 tools go from ❌ to working.**
- Runtime-register L0/L1 capabilities + the asset-registry resource (F-001 [PR#372 partial], F-002, F-018).
- Point asset_registry_all at an MCP-reachable surface or allow the internal token on /api/cockpit/ (F-003).
- Whitelist/reroute the 7-tool remedy-corpus family (F-004); fix resolve_entity GET→POST 405 (F-015); make
  mitigation_map return a structured envelope not void (F-016).
- **Acceptance:** all 45 tools return a structured response (data or clean empty); the retrievability matrix is
  ✅/clean-⬛ with zero ❌. Discovery (list_assets) works.

## WAVE 3 — OUTPUT BOUNDING (make it usable by a real client)
**Owner: MCP/L2. Effort: medium. Impact: the system becomes consumable.**
- Make `response_format` actually branch (digest=counts / summary=top-k / full) — currently inert (F-026).
- Cap + paginate the big synthesis tools: get_domain_reading must NOT return 17 MB (F-021); dedup signal_id_refs
  (F-023); bound get_projections (F-008). Default to a token-safe size; paginate the rest.
- Standardize the error envelope across all tools (F-028).
- **Acceptance:** no tool returns >~25k-token default; verbosity levers demonstrably change payload size;
  uniform error shape.

## WAVE 4 — L4 PHALA + SIDECAR REPAIR (restore the prediction layer)
**Owner: L4 data-layer + infra. Effort: medium. Impact: prediction/timing tools work.**
- Fix the L4 schema drift: missing columns (`id`, `anchor_id`), the `phala_get_rectification` PL/pgSQL
  `candidate_time` field, the missing `panchanga_daily` relation (F-005, F-014).
- Re-provision the corrupted Swiss Ephemeris file `sepl_18.se1` + a sidecar image integrity pass (F-012, F-030).
- Root-cause the L5 mimamsa 500s (F-013).
- **Acceptance:** phala_outlook / event_anchors / query_special_lagnas / query_calibration return data on prod.

## WAVE 5 — THE ASTROLOGICAL CORE (salience + synthesis; the real "acharya-grade" work)
**Owner: L2 Bodha + retrieval fork. Effort: LARGE (design + data-model). Impact: the actual goal — superlative insight.**
This is the true long pole. The data is rich + correct; the JUDGMENT layer is not.
- **Salience re-model (F-020, F-025):** the ranking must know a raja-yoga / 10th-lord / dignity outranks a D2700
  ashtakavarga bindu. Fix the degenerate salience (identical values), stop ashtakavarga varga-counts saturating
  the top band, and ACTIVATE signature_tier (currently 100% background) so chart-defining signals rank first.
  This is an astrological-relevance model, native's judgment required on weighting.
- **Synthesis step (F-024):** get_domain_reading / the assess_* reasoning-units must produce a RECONCILED reading
  (weigh, resolve contradictions, prioritize) — a verdict, not a 90k-row dump. Decide the facts/LLM-synthesis
  boundary (some rawness is by design, but there must be a narrowed, ranked core).
- **Domain-filter schema (F-009, F-022):** bodha_question_lenses needs a domain dimension so a career query
  returns career, not all 12 life areas.
- **Machine-grounding (DEFECT-001):** the MSR rebuild against current L1 so constituent_facts resolve (the D-A
  request already filed — REQUEST_RETRIEVAL_MSR_REBUILD_FOR_MCP_G10). Re-score the scorecard after.
- **Remedy scoring (F-007):** fix the degenerate 0.28-for-every-planet weakness score so remedy prioritization
  is chart-specific.
- **Acceptance:** for a career query, the top signals are career-diagnostic (10th house/lord, karakas, raja
  yogas), ranked meaningfully, reconciled into a verdict an acharya would call "my level or above" (the G10 test).

## Sequencing + ownership summary
1. **Wave 1** (ayanamsha) — now, tiny, unblocks everything. → one CLAUDECODE brief.
2. **Waves 2–3** (wiring + bounding) — MCP-side, fast, make it usable. → CLAUDECODE briefs (fold in the pending
   M8.1/PR#372 which already covers part of Wave 2).
3. **Wave 4** (phala/sidecar) — data-layer/infra, parallelizable with 2–3.
4. **Wave 5** (salience + synthesis) — the deep astrological work; the real distance to "superlative." Owned by
   the L2 Bodha + retrieval forks; needs the native's astrological judgment on weighting. This is its own
   campaign, not a quick fix.

**The honest bottom line for the goal:** Waves 1–4 get you to "an LLM connects, accesses, and retrieves the
data cleanly and efficiently" — achievable fast. Wave 5 is what makes the output *superlative* — and it's real
astrological-model work, the true long pole, now precisely scoped by this audit.

*End of MCP_SYSTEM_AUDIT_FIX_PLAN v1.0 (draft). Next: author Wave 1 CLAUDECODE brief on your go; refine Wave 5
scope with your astrological input.*
