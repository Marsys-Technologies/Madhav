---
artifact: RETRIEVAL_TO_MCP_HANDOFF
canonical_id: RETRIEVAL_TO_MCP_HANDOFF
version: 1.0
status: CURRENT — paste into the MCP build conversation; the post-seal handoff FROM retrieval
created: 2026-06-30
author: Cowork (retrieval-engine conversation) — handoff to the MCP build conversation
classification: cross-conversation handoff (retrieval → MCP), live-grounded post-seal
supersedes_framing_of: MCP_ELEVATION_PLAN_AND_HANDOFF_v1_0 (its §A/§B were written PRE-build and are now stale —
  this handoff updates them to LIVE reality; the MCP vision/phases in §C/§D of that doc still stand)
authoritative_state: CURRENT_STATE v6.07; RETRIEVAL_ELEVATION_PLAN SEALED v1.1; seal record RETRIEVAL_ENGINE_SEAL_RECORD_v1_0
changelog:
  - v1.0 (2026-06-30): Post-seal retrieval→MCP handoff. What retrieval delivered (live seams, resolved P0s),
    the now-LIVE frozen contract, the technical specs + pointers the MCP must build against, and what's already
    done so the MCP fork doesn't redo it.
---

# RETRIEVAL → MCP HANDOFF (post-seal, live-grounded)

> **For the MCP build conversation.** The retrieval engine is SEALED and elevated (R-1→R6, commits d139a63d +
> a009ee1b, migration 380, CURRENT_STATE v6.07). This handoff carries what that build actually delivered + the
> hard-won technical guidance the MCP must build against. It UPDATES the stale parts of
> `MCP_ELEVATION_PLAN_AND_HANDOFF_v1_0` — read this for current reality; that doc's MCP *vision + phased plan*
> (its §C/§D) still stand, but its §A/§B "what's live" statements are superseded by §1–§3 here.

## §1 — WHAT THE RETRIEVAL ENGINE DELIVERED (now live; the MCP consumes this)

The retrieval layer is the **single source**; the MCP is a thin channel adapter over it. These are now LIVE:

1. **The registry-served path works.** The keystone landed: the 5 tools that bypassed the registry with their
   own `pg.Pool` (`audit.ts`, `remedy_tools.ts`, `read_classical_text.ts`, `kala_timeline.ts`,
   `holistic_bundle.ts`) are **repointed to `callPlatformPrimitive`** → the registry. There is ONE retrieval
   surface; both chat and MCP consume the same capabilities. **The MCP must NOT run its own chart SQL** (this
   was the old anti-pattern; it's been removed — don't reintroduce it).
2. **The 401 seam is FIXED.** `/api/mcp/primitives/[tool]` no longer requires the dead `x-mcp-audience-tier`
   header (removed from the guard). Registry-path tools return 200. **➜ The MCP fork's M0.1 (the 401 one-liner)
   is ALREADY DONE here — do not redo it.**
3. **`getMcpSurfaceSpec(family)` is published as a live seam.** New route `/api/mcp/surface-spec` +
   `callPlatformSurfaceSpec()` client bridge the per-model surface spec across processes. **The MCP consumes
   this to shape declared→profiled surfaces** (M6). MARO profiles are MEASURED v1.1.0 — exposure, not build.
4. **Bundle-elasticity is live.** `response_format: minimal | standard | detailed` branches for real in
   `bundle_adapters.ts`. **The MCP per-model surface uses this** to serve terse (Claude-looping) vs exhaustive
   (Gemini-big-context) shapes.
5. **Reasoning-unit tools exist** (`assess_marriage/career/health/wealth` + `yoga_activation_by_dasha`), each
   orienting via whole-chart-read first, contradiction-aware (graceful-empty until contradiction data verified
   — see §4). The MCP surfaces these as the high-value portal-equivalent tools.
6. **Resources + prompts are live.** `registerResources()` is wired (9 resources, previously dead); 3
   guided-reading prompts exist (`orient_chart`, `assess_domain`, `find_active_yogas`). The MCP can expose
   these as MCP resources/prompts for the portal-like experience.
7. **Contamination is gone + gated.** `kala_temporal` native FORENSIC fallback removed; `kala_timeline` purged
   of 100+ lines of native dasha schedule; the chart-agnostic CI gate (Rule 8) scans `platform-mcp/src/tools/`
   for native identifiers. **➜ The MCP fork's M0.3 (kala_temporal contamination) is ALREADY DONE here.**

## §2 — THE FROZEN SYNC CONTRACT (now LIVE, not aspirational)

Unchanged in intent, but now backed by working code (`RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4`):
1. **Retrieval is chart-agnostic + FROZEN** — `chart_id` required, no default, ZERO entitlement awareness.
   The MCP MUST NOT push entitlement into retrieval. (Verified: contamination sweep zero hits in operational code.)
2. **Entitlement lives at the CHANNEL (Option 1)** — every chart-scoped MCP call calls
   `authorizeChartAccess(principal, chart_id)` (`platform/src/lib/auth/authorizeChartAccess.ts`) and denies
   before any `retrieve()`. Follow the built `invokeTool` chokepoint pattern. **This is still the MCP's to
   build (M0.2/M1) — retrieval did NOT add it (correctly).**
3. **Single source** — both channels via `/api/mcp/primitives/[tool]` → `getToolByName` → `tool.retrieve`. (Live.)
4. **MCP consumes:** registry capabilities + `getMcpSurfaceSpec` + `response_format` + the contract fields
   (archetype/traversal_level/tool_role/drill_children). (All live now.)
5. **Retrieval wins on conflict; MCP adapts.** Seam changes are requested from retrieval, not made unilaterally.

## §3 — WHAT'S ALREADY DONE (so the MCP doesn't redo it) — revised M0

The MCP plan's PHASE M0 (P0 fixes) is **partially complete already**:
- **M0.1 (401 fix)** — ✅ DONE (retrieval R2.0).
- **M0.3 (kala_temporal native contamination)** — ✅ DONE (retrieval R1).
- **M0.2 (authorizeChartAccess entitlement gate)** — ⬜ STILL THE MCP'S TO BUILD. This is the remaining P0 and
  the security keystone of the MCP build. Highest priority.
- **M0.4 (latent role/header bugs + stale /health + tool_list.json)** — ⬜ partially: the stale
  `x-mcp-audience-tier` read is gone (M0.1); the **MCP principal carrying no role for `authorizeChartAccess`**
  remains the MCP's to resolve (needed before M0.2 can map principal→role); regenerate stale /health + tool_list.

So the MCP build effectively STARTS at: M0.2 + the principal→role mapping, then M1→M8.

## §4 — RETRIEVAL-INTERNAL RESIDUALS (do NOT block the MCP; informational only)

Two items are closing in the retrieval conversation; neither changes the MCP's interface:
- **Contradiction data verification** — the contradiction WRITER + wiring are sealed; the Abhinandan chart
  rebuild (in progress) populates `bodha_contradictions` to verify contradictions surface end-to-end. Until
  then, reasoning-unit tools return contradictions graceful-empty. **MCP impact: none structural** — the tool
  contract is stable; only the richness of one field improves once data lands.
- **platform-mcp test triage (33 Vitest failures)** — test-hygiene debris (9 stale teardown test files, 20
  fetch-mock wiring in `mimamsa_lel_intake.test.ts`, 1 stale FORENSIC assertion). **NOT product defects;
  platform is all-green.** Being triaged retrieval-side. The MCP fork should be AWARE these exist so it doesn't
  mistake them for MCP-build regressions, but they don't gate MCP work.

## §5 — TECHNICAL POINTERS + RECOMMENDATIONS (hard-won this build; for the MCP)

Distilled guidance the MCP build should carry:
- **Verify live, don't trust reports.** This build repeatedly found "done" claims contradicted by live data
  (the MSR seal claimed 3×; the "jest/Babel breakage" that didn't exist — the project is **Vitest**). Run the
  read-only check yourself before acting. The project is Vitest (platform v4.1.8, platform-mcp v2.1.9) — there
  is NO jest/Babel.
- **The `_ctx.db` trap.** Handlers that destructure `{db} = _ctx` get `undefined` (CapabilityContext only
  carries `{chart_id?, request_id?}`); the correct pattern is `import { query } from '@/lib/db/client'`. If the
  MCP touches any handler, use the correct pattern.
- **Native-contamination is a recurring class.** It re-appears in fallback paths, LLM-visible descriptions, and
  *tests that assert presence of the native name*. The CI gate (Rule 8) catches tool-file identifiers; but
  watch descriptions + test assertions. Never "make a test green" if green means re-embedding the native name.
- **Destructive ops need the reverse-citation gate.** A prior unscoped `DELETE FROM mimamsa_preferences` wiped
  all users' prefs. Any DELETE must be chart/user-scoped; grep for live citations before removing anything.
- **Per-model serving is real + measured.** MARO profiles (anthropic/gemini/openai/deepseek) are MEASURED;
  consume `getMcpSurfaceSpec(family)` rather than re-deriving. DeepSeek has no MCP (plain-backend); Gemini
  Remote-MCP needs Streamable-HTTP + no `-` in tool names; OpenAI/ChatGPT connector needs the approval flow.
- **The MCP OAuth is scaffold** (in-memory Maps, anonymous tokens, dies on restart) — productionizing it
  (DB-backed token/client store, real identity binding) is core M5 work, untouched by retrieval.
- **Resources were dead-but-defined; now registered.** The 9 resources + 3 prompts retrieval wired are the
  natural multi-user "active chart context" + guided-reading surfaces — the MCP should expose them, not rebuild.

## §6 — HANDOFF VERDICT
The retrieval engine is sealed, green, contamination-clean, and serving the single registry surface with the
seam outputs the MCP needs (`/api/mcp/primitives` 200, `/api/mcp/surface-spec`, `response_format`). The MCP
build can proceed NOW, starting at **M0.2 (entitlement gate) + principal→role mapping**, then M1→M8 per
`MCP_ELEVATION_PLAN_AND_HANDOFF §D`. The two retrieval residuals (contradiction data, test triage) close in
the retrieval conversation and do not block or alter the MCP interface.

**To start the MCP conversation:** paste `MCP_ELEVATION_PLAN_AND_HANDOFF_v1_0` (the vision + phases) AND this
handoff (the live reality + what's-already-done). This handoff is authoritative where the two disagree on
"current state."

*End of RETRIEVAL_TO_MCP_HANDOFF v1.0 — retrieval is sealed; the MCP fork is cleared to build on a live,
working, contamination-clean retrieval surface.*
