---
canonical_id: CLAUDECODE_BRIEF_AUDIT_E2E_REMEDIATION
version: 1.0
status: READY-FOR-EXECUTION — deterministic remediation of the E2E-test gaps (the fixable ones)
created: 2026-07-02
author: Cowork (from the live E2E LLM-client test) — for execution by Claude Code
parent: MCP_E2E_TEST_REPORT_v1_0 (the gap list G-A…G-I)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4
verification_basis: live MCP connector probes 2026-07-02
scope_boundary: DETERMINISTIC fixes only (known-correct answer + objective pass/fail). EXCLUDES G-B salience
  weighting + G-C synthesis contract (native-judgment / Wave 5 / beyond-acharya track) and G-D MSR rebuild
  (retrieval fork, already filed). If a fix here starts requiring a JUDGMENT on what-should-rank or how-to-
  reconcile, STOP — that's Wave 5, not this brief.
hard_constraints:
  - build gate (platform-mcp + platform tsc exit 0); BOTH-services SHA match; prod-prove each fix; VITEST
  - retrieval FROZEN + chart-agnostic; reverse-citation before any delete; stored counts unchanged unless a fix
    is explicitly a data-correctness fix (G-G shadbala link, G-H de-degeneracy) — even then, additive/corrective, not destructive
acceptance_criteria: see §7
---

# CLAUDE CODE BRIEF — E2E REMEDIATION (deterministic gaps G-A/E/F/G/H)

> The live LLM-client E2E test found the data stack largely works but named 9 gaps. This brief fixes the FIVE
> deterministic ones. Two (G-B salience, G-C synthesis) are native-judgment Wave-5 work — DO NOT attempt them
> here. One (G-D MSR rebuild) is the retrieval fork's. Each fix below has an objective prod-prove.

## G-A [CRIT] — new tools not advertised to connected clients
**Symptom:** assess_marriage/career/health/wealth, yoga_activation_by_dasha, query_chart_facts, vector_search,
get_cgm_subgraph are registered server-side (W2.5) but do NOT appear in a connected client's tool list, even
after a client-side refresh. A Cowork/Claude connector caches tools/list at connection.
**Server-side fix (this brief):** ensure the MCP server (platform-mcp) (1) includes ALL registered tools in its
`tools/list` response (verify the newly-registered d7/d8 + registry-bridge tools are actually enumerated there —
not just registered in the capability registry), and (2) emits a `notifications/tools/list_changed` per MCP spec
when the tool set changes, so compliant clients re-pull. Confirm the served tools/list count == the true
registered count (should now include the ~5 apex tools → ~50 total, reconcile the exact number).
**Client-side (native action, documented in §8, NOT code):** remove + re-add the MCP connector in Cowork to
force a fresh tools/list. The server fix makes future refreshes work; the re-add unblocks the current session.
**Prod-prove:** a fresh MCP client (or a raw tools/list JSON-RPC call) lists assess_marriage etc.; count matches.

## G-E [HIGH] — domain filter inert (bodha_question_lenses has no domain column)
**Symptom:** get_domain_reading(domain=career) returns lenses for ALL 12 question types; the tool self-reports
"bodha_question_lenses has no domain column; lenses returned chart-wide."
**Fix:** add a `domain` (or question_type→domain mapping) dimension so the lens set filters to the requested
domain. NOTE: the question_type→domain mapping (e.g. does "progeny" belong under "relationship" or its own
domain?) is a light classification — use the existing CDLM domain taxonomy (career/relationship/character/
spirituality/wealth/health); if a question_type doesn't map cleanly, list it for native confirmation rather than
guessing. The FILTER mechanism is deterministic; only the mapping edge-cases may need a native nod.
**Prod-prove:** get_domain_reading(domain=career) returns ONLY career-relevant lenses (not all 12).

## G-F [MED] — query_remedies_for_chart uncallable (over-gated)
**Symptom:** returns CHART_REQUIRED, but its schema has NO chart_id param (only affliction + top_k) — it's a
chart-AGNOSTIC corpus lookup that the M0 entitlement gate wrongly requires chart_id for. Contract contradiction.
**Fix:** exempt this chart-agnostic tool from the chart_id entitlement gate (it reads brahma_remedy_corpus by
affliction keyword, no chart data). AUDIT the gate's tool list for OTHER chart-agnostic tools wrongly gated
(the remedy-corpus family, list_entities, resolve_entity, get_classical_citation, ephemeris tools — none of
these take chart_id; confirm none is CHART_REQUIRED-blocked). The gate must apply ONLY to per-chart tools.
**Prod-prove:** query_remedies_for_chart(affliction=Saturn) returns remedies (no CHART_REQUIRED); no
chart-agnostic tool is entitlement-blocked; per-chart tools STILL gated (re-prove one deny).

## G-G [MED] — get_dashas: wrong default + pre-birth rows + null shadbala
**Symptom (live, chart 482012f1 born 1984):** limit=6 returned ashtottari rows starting 1950 (pre-birth);
defaulted to ashtottari not vimshottari; lord_natal_shadbala_total = null.
**Fix:** (1) default system_id = vimshottari (the primary system a client expects; keep others available via a
param). (2) Order/anchor to the chart: return the birth-anchored active sequence (order by date, filter to
periods overlapping the native's lifetime; do not surface pre-birth periods by default). (3) Populate
lord_natal_shadbala_total from the L1 strength asset (the join is currently null — wire it).
**Prod-prove:** get_dashas(482012f1) defaults to vimshottari, first rows are birth-era (1984+) not 1950,
shadbala populated.

## G-H [HIGH] — degenerate constant scoring (root-cause the collapse; NOT the re-weighting)
**Symptom:** get_remedies gives EVERY planet resonance=weakness=0.28; salience collapses to ~3 constants
(0.581668 / 1.163336 / 2.326672). Values that should vary per graha/signal are identical constants.
**Fix (deterministic — this is a BUG hunt, not a weighting judgment):** find WHY the scores collapse to
constants — likely a normalization dividing everything to the same value, a hardcoded default fallback
(cf. the degenerate-distribution-guard scar: dict.get(k, <const>) writing plausible constants), or a missing
per-entity input so every entity gets the same computed value. Fix so the scores VARY per graha/signal as the
formula intends. **DO NOT re-design the weighting philosophy (that's G-B/Wave-5) — just make the EXISTING
formula produce non-degenerate per-entity values.** Add a distribution guard: halt/flag if a score column
collapses to one value where diversity is expected.
**Prod-prove:** get_remedies shows DISTINCT resonance/weakness per planet (not all 0.28); salience has a real
distribution (not 3 constants). Report the distributions.

## §6 — What this brief does NOT touch (route elsewhere)
- **G-B (salience weighting) + G-C (synthesis contract):** native-judgment Wave 5 → the beyond-acharya strategic
  plan (project_beyond_acharya_plan). G-H fixes the COLLAPSE bug; G-B decides the WEIGHTS — different problems.
- **G-D (MSR machine-grounding rebuild):** retrieval fork (REQUEST_RETRIEVAL_MSR_REBUILD_FOR_MCP_G10 filed).
- **G-I (verbosity/error-envelope polish):** low; sweep opportunistically, not gating.

## §7 — Acceptance criteria (all prod-verified, both services on merged SHA)
- G-A: tools/list advertises the apex tools (assess_*, get_cgm_subgraph, query_chart_facts, vector_search);
  tools/list_changed emitted on change; count reconciled.
- G-E: domain filter works (career query → career lenses only).
- G-F: query_remedies_for_chart callable; no chart-agnostic tool entitlement-blocked; per-chart gate intact.
- G-G: get_dashas defaults vimshottari, birth-anchored, shadbala populated.
- G-H: scores non-degenerate (distinct per entity); distribution guard added.
- Build gate green (both packages); BOTH amjis-mcp + amjis-web on the merged SHA; migrations green; retrieval
  FROZEN; chart-agnostic gate green; reverse-citation on any delete; Vitest; no Wave-5 (G-B/G-C) work done.

## §8 — Native action for G-A client-side (not code)
After the server fix deploys: in Cowork, REMOVE the MARSYS MCP connector and RE-ADD it (fresh tools/list). A
tool-list refresh alone did not surface the new tools; a full re-add does. Then the apex tools are reachable
from the LLM client and the G10 synthesis witness can run.

*End of CLAUDECODE_BRIEF_AUDIT_E2E_REMEDIATION v1.0 — the deterministic half of "fix everything." The judgment
half (salience + synthesis) is the beyond-acharya track, gated on native input.*
