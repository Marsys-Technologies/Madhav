---
artifact: MCP_CHANNEL_CONVERSATION_HANDOFF_v1_0.md
canonical_id: MCP_CHANNEL_CONVERSATION_HANDOFF
version: 1.0
status: CURRENT — paste into a fresh Cowork conversation to start the MCP-channel workstream
created: 2026-06-28
author: Cowork (planning) — handoff primer for the MCP-channel conversation, for native Abhisek Mohanty
classification: conversation handoff / context primer (zero-context-loss)
purpose: give a brand-new Cowork conversation the full inheritance needed to plan + drive the MCP-channel
  workstream, so it does not re-derive the retrieval campaign and does not redo sealed work.
---

# MCP CHANNEL — CONVERSATION HANDOFF (paste this to start the new conversation)

> **How to use this.** Paste this whole document as the first message of a new Cowork conversation for the
> MCP-channel workstream. It carries everything that conversation needs: the project frame, what the retrieval
> campaign delivered, the EXACT current state of the MCP channel, the binding rules it inherits, the open items,
> the artifacts to read, and a proposed agenda. The new conversation plans + briefs; Claude Code in Antigravity
> implements (the project's Cowork-vs-Antigravity split).

---

## §1 — Project frame (one paragraph)

MARSYS-JIS is an LLM-operated Jyotish (Vedic astrology) instrument for native Abhisek Mohanty (canonical
chart_id `482012f1-710e-4a25-994a-93821f5871aa`). Six layers (L0 Brahmagyan / L1 Gaṇita / L2 Bodha / L3 Kāla /
L4 Phala / L5 Mīmāṃsā), ~81 buildable assets in Postgres, fronted by a retrieval system that serves TWO
consumption channels — an **MCP server** (external/BYO-LLM) and a **chat engine** (internal) — across four LLM
families (Anthropic, Gemini, OpenAI, DeepSeek). Governance is heavy and deliberate (CLAUDE.md §C reads,
CURRENT_STATE pointer, versioned artifacts, reverse-citation gates, prod-only data plane). Cowork plans + briefs;
Claude Code executes against real code.

## §2 — What the retrieval campaign just delivered (the inheritance)

A full retrieval-system design + build was completed and SEALED on both channels (CURRENT_STATE v6.04). The arc:
meta-plan → external+internal research → a 4-part ground-truth study → code-plane validation → a chart-agnostic
anti-contamination mandate → an autonomous overnight swarm build → chat migration → cleanup. Outcome:
- **D1 RetrievalSurface contract** (extends `CapabilityDescriptor` in
  `platform/src/lib/retrieval/registry/types.ts`) + a **chart-agnostic CI gate** (beside `parity_check.ts`).
- **D2 router** (5-class), **D3 grounding spine** (§N.5 reference-don't-restate), **D4 graph**
  (`traverse_chart_graph`), **D5 fan-out** (capabilities across L0–L5), **D-PROFILES/MARO** (all 4 families,
  measured v1.1.0), **D8 eval/seal** (14/14 principles, `retrieval-d8-sealed` tag).
- **Single source of query logic:** chat + MCP both consume the `lib/retrieval` registry; the old `lib/retrieve`
  + `mcp/primitives_registry` were retired. 20/20 drift parity proves the two channels behave identically.

## §3 — EXACT current state of the MCP channel (read carefully — don't redo sealed work)

The MCP channel is **already sealed at the retrieval layer**, but is NOT yet production-hardened for real
external consumers. Precisely:

**SEALED / done:**
- The MCP server (`platform-mcp/`) exposes **12 consolidated workflow-shaped tools** over the registry
  (Streamable HTTP, **no SSE**, Bearer + OAuth 2.0). Tools are chart-agnostic and grounded.
- Native contamination in the **wired** MCP tools was remediated (D6/D7).
- Both channels share one query source (no MCP↔chat drift).

**Recently closed (do NOT redo):**
- **ISSUE-7 (MCP-tool hygiene) ✅ CLOSED** (commit d9a22a5d, PR #360, CURRENT_STATE v6.05). The 19 unwired
  contaminated tool files are resolved (10 retired, 9 scrubbed), and the **chart-agnostic CI gate now scans
  `platform-mcp/src/tools/`** — so native UUIDs in any MCP tool file (wired or not) fail CI. `platform-mcp/
  src/tools/` is verified clean; re-contamination is structurally impossible. This workstream INHERITS a clean,
  gate-protected tool directory.

**NOT done / open (this workstream's territory):**
- **Per-model declared-profile behavior on MCP:** the design (MARO + D-PROFILES) says MCP should serve
  **declared→profiled / undeclared→universal-best** surfaces per connecting model family — the DECLARATION
  MECHANISM (config / OAuth scope / per-key / client hint) was left to this workstream to resolve + wire.
- **Production hardening for external/BYO-LLM use:** OAuth/connector compliance for real clients (ChatGPT
  connector, Claude MCP client, Gemini Remote-MCP — note Gemini needs Streamable HTTP + no `-` in tool names,
  and was historically not reachable on Gemini-3; DeepSeek has NO MCP and consumes tools as a plain backend),
  deployment/revision verification, rate limiting, end-to-end testing with real external model clients.
- **Product-surface questions:** discovery, onboarding, docs, multi-chart/multi-tenant access UX, the
  declared-profile UX. (The larger arc.)

## §4 — Binding rules this workstream INHERITS (non-negotiable)

- **Chart-agnostic, zero native contamination (principle #14):** every per-chart tool takes `chart_id` from
  request context, required, errors-if-missing, NO native default, no native in descriptions. The native chart
  is for BUILD/AUDIT only — never in shipped code as a default/fixture. Enforced by the CI gate (extend it to
  cover MCP tools).
- **No audience tier** anywhere.
- **Reference-don't-restate (§N.5 / F3):** numbers come from L1 `fact_id`, cited not regenerated.
- **F1 dedup:** one fact emitted once with perspectives attached; reference-keyed drill.
- **Reverse-citation gate before ANY deletion** (the project once wiped live tables from a trusted kill-list).
- **Prod-only data plane:** localhost writes ARE prod writes; verify against prod after merge, not worktree.
- **Provider best-practices** are captured in `RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md` — the MCP
  obligations checklist (outputSchema + structuredContent + text fallback, cursor pagination, response_format
  enum, UUIDs→names, names avoiding `-`, etc.) is the spec the MCP surface must satisfy.
- **The 14 design principles** (in `RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md §6`) bind.

## §5 — Artifacts to read at conversation open (in order)

1. This handoff (orientation).
2. `00_ARCHITECTURE/RETRIEVAL_AUTONOMOUS_RUN_OUTCOME_v1_0.md` — the most current state; what's sealed + open (ISSUE-4/7).
3. `00_ARCHITECTURE/RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md` — §A MARO, §A.3 channel asymmetry, §A.4
   declared/undeclared MCP, §D chart-agnostic, §6 the 14 principles.
4. `00_ARCHITECTURE/RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md` — Part 3 MCP-channel obligations + the
   per-provider MCP constraints (Anthropic/Gemini/OpenAI/DeepSeek).
5. `00_ARCHITECTURE/RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md` — §B MCP server findings + §H contamination.
6. `CLAUDECODE_BRIEF_RETRIEVAL_MCP_TOOL_HYGIENE_v1_0.md` — the ready ISSUE-7 brief (folds into this workstream).
7. `CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO_v1_0.md` — the MARO/profiles + the declared-profile mechanism it left open.
8. Live code: `platform-mcp/src/server.ts` (the wired surface), `platform-mcp/src/tools/` (incl. the 19 unwired
   files), `platform/src/lib/retrieval/registry/` (the source the MCP tools consume).
9. `CLAUDE.md` (project governance) + `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (verify "you are here" from here + git, not stale docs).

## §6 — Proposed agenda for the new conversation (audit → harden → product)

The native wants all three goals; they sequence:
1. **AUDIT-FIRST:** thorough assessment of the sealed MCP channel — what the 12 wired tools actually expose,
   gaps vs the provider obligations spec, the 19-file hygiene reality, deployment/revision state, and what real
   external clients (Claude MCP, ChatGPT connector, Gemini Remote-MCP, DeepSeek-as-backend) need. Produce a
   current-state map + a decision on rebuild-vs-update-vs-fix per area (mirror the retrieval D0 pattern).
2. **PRODUCTION-HARDEN (near-term build):** ISSUE-7 hygiene + gate extension; the declared-profile mechanism +
   per-model MCP surfaces (MARO); OAuth/connector compliance for each real client; deployment + prod-verify;
   rate limiting; end-to-end tests with real external LLM clients on ≥2 charts (never native-only).
3. **PRODUCT-SURFACE (larger arc):** MCP as a first-class product — discovery, onboarding, docs, multi-chart
   access UX, the declared-profile UX. Design up, then brief.

Run it the proven way: Cowork audits + plans + authors `CLAUDECODE_BRIEF`s; Claude Code implements (worktree
isolation, reverse-citation on deletes, prod-verify after merge); parameterized briefs get a detail-pass when
inputs land. Consider the autonomous-swarm charter pattern (`CLAUDECODE_BRIEF_RETRIEVAL_AUTONOMOUS_SWARM_
CHARTER_v1_0.md`) if the native wants an overnight build again.

## §7 — Relationship to the retrieval system (the integration point)

The MCP channel does NOT reimplement retrieval — it is a **thin channel adapter over the sealed registry +
MARO**. Its job is to PRESENT the registry's capabilities to external LLMs per MCP spec + per the connecting
model's profile, with auth/deployment/compliance around it. Any retrieval logic gap found here routes BACK to
the retrieval layer (a registry capability), not solved in the MCP tool. Keep the single-source-of-query-logic
invariant — that's what the whole campaign bought.

## §8 — Open items from the retrieval campaign that touch this workstream

- **ISSUE-7 (MCP-tool hygiene)** — ✅ CLOSED before this workstream opened (commit d9a22a5d, v6.05). The tool
  directory is clean + gate-protected. Nothing to do; noted so the new conversation knows the directory is safe.
- **ISSUE-4 (L2 Bodha MSR rebuild)** — NOT an MCP item (data-layer; the §N.5 detector correctly surfaced
  pre-existing drift). Mentioned only so the new conversation doesn't mistake low fact-resolution for an MCP bug.
- Governance hygiene (SESSION_LOG append + frontmatter pass) — booked for the next governance session.

**Net for this workstream:** the retrieval campaign is fully closed (only the non-MCP ISSUE-4 remains, owned by
L2 Bodha). The MCP channel inherits a clean, sealed, gate-protected foundation — this workstream is pure
forward build (production-hardening + product-surface), not cleanup.

---

*End of MCP_CHANNEL_CONVERSATION_HANDOFF v1.0. Paste into a fresh Cowork conversation to begin the MCP-channel
workstream with full inheritance and zero context loss.*
