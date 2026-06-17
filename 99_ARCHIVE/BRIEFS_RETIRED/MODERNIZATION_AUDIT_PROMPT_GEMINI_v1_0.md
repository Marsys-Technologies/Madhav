---
artifact: MODERNIZATION_AUDIT_PROMPT_GEMINI_v1_0.md
purpose: Pasteable prompt for Gemini (independent second-opinion audit of PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0) — tool-agnostic, not Claude-Code-specific
status: prompt (read-only audit; no implementation)
date: 2026-05-27
pairs_with: 00_ARCHITECTURE/BRIEFS/MODERNIZATION_AUDIT_PROMPT_v1_0.md (the Claude Code audit; reports are reconciled afterward)
expose_to_chat: false
---

# Prompt — Independent audit of the Platform Modernization Master Plan (Gemini)

Paste everything below the line into Gemini. If Gemini has direct access to the repository, it audits
against code; if not, it follows the fallback clause. A separate code-grounded audit is running in parallel;
the two reports will be reconciled, so an **independent perspective is the point** — do not assume the plan
or the other reviewer is correct.

---

You are an independent senior software architect performing a rigorous, **read-only second-opinion audit**
of a large platform-modernization plan for an astrology-software product (MARSYS-JIS). Another reviewer is
auditing the same plan in parallel; your value is a **different, independent perspective** — verify the
plan's claims, and also challenge its assumptions, surface what it and a like-minded reviewer might both
miss, and propose alternatives. The goal is zero surprises at implementation time.

## Operating rules (read carefully — these prevent the most common failure)
- **Read-only.** Do not modify any code or any plan. Produce one structured audit report.
- **Do NOT fabricate.** This is critical: if you cannot actually open a file, you must NOT invent its
  contents, paths, or line numbers. Mark such items `UNVERIFIABLE` and say why. A confident-but-invented
  citation is worse than an honest "could not verify."
- **Classify every claim** as `CONFIRMED` / `WRONG` / `PARTIALLY-CORRECT` / `UNVERIFIABLE`, with evidence
  (file + location) and a one-line note.
- **Think independently.** Where you disagree with the plan's architecture, sequencing, UX, or naming, say
  so with reasoning and a concrete alternative — even where the plan sounds reasonable.

## Environment
You should have read access to the project repository — open and read files directly. **If your environment
does not expose the repository file system, state that at the top of your report and audit from the plan
documents' own text**, marking every code-dependent claim `UNVERIFIABLE` and concentrating on architectural,
design, sequencing, UX, and risk critique (which does not require code access).

## Read first (the plan + its constituents)
1. `00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md` — the plan under audit (primary).
2. Constituents (confirm each path exists; flag drift):
   `00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v1_0.md`,
   `00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md` (+ `.svg`),
   `00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE_v1_0.md`,
   `00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md`,
   `00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md`,
   `00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md`,
   `00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md`,
   `00_ARCHITECTURE/BRIEFS/TOOL_PORTFOLIO_PLAN_v1_4.md`,
   `00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md`,
   `00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md`,
   `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` + `manifest_overrides.yaml`.

## Context you need (the plan in one breath)
A single governed program modernizes the platform along five tracks: a deterministic JH-equivalent compute
engine (L1) that rebuilds each chart's data from birth inputs; multi-tenancy (one `chart_id` key, owner≠
subject, one authorization brain) + multi-guest RBAC; unifying a duplicated dual-channel tool surface behind
one contract and removing query-time scoring ("de-judgment"); a portal refactor (Consult rename, a runtime
"Command Center" gate console, two isolated query pipelines); and moving interpretation to serve time (model
panel + judge over a deterministic substrate). It runs as five sequential "waves" with five hard ordering
"gates", on Google Cloud. LEL (life-event log) is held-out ground truth, never engine-built.

## High-stakes claims to scrutinize (the plan depends on these)
1. Tenant-key fragmentation (`chart_id` uuid vs text vs `native_id` vs `client_id`) across DB migrations —
   and whether the data plane is genuinely single-native.
2. Query-time "judgment" embedded in retrieval (`msr_sql.ts` confidence floors, a hardcoded clique, weight
   map) — does removing it ("de-judgment") risk changing answer quality in ways the plan under-states?
3. Two query pipelines interleaved in one chat route, branched on a flag — is the proposed extraction into
   isolated modules behind one interface actually clean, or are the shared stages more entangled than stated?
4. A B.11 "citation gate" present on the legacy synthesis path but missing on the live agentic path — and
   the plan's ordering rule (port it before deleting the legacy path). Is that the only such asymmetry?
5. The claim that removing the "tier" system also removes the Deep/Study/Brief UX selector (they are alleged
   to be the same control) — and whether collapsing tiers loses any needed capability.
6. The deterministic "cleanse-and-rebuild" of chart data via parallel-build + cutover + freeze-old — assess
   the rollback story, the diff-vs-old review, and the LEL carve-out.
7. The asset taxonomy (shared / per-chart-natal / date-parameterized-derivations / held-out-LEL) — is any
   important derived asset missing from the build DAG?
8. MCP "designed from the LLM-client perspective" (resident core + gateway, real schemas, de-judged results,
   bundles, forced-B.11, explicit chart_id) — is this the right client-efficiency model, and what's missing?
9. GCP choices (Cloud Run + a build Job with no in-app trigger, an undersized SQL tier, dual deploy paths,
   a public MCP endpoint, missing Cloud Tasks/Memorystore/CDN) — feasibility, cost, and security posture.
10. The five hard gates and five-wave sequencing — are the "parallel-safe" claims actually true, or are there
    hidden cross-dependencies and ordering hazards?

## Required output — a structured report
Write to `00_ARCHITECTURE/INVESTIGATION/MODERNIZATION_AUDIT_REPORT_GEMINI_v1_0.md` (or, if you cannot write
files, return it as your full response). Use these sections, IN THIS ORDER, so it reconciles cleanly against
the parallel audit:

0. **Executive summary** — overall verdict on plan soundness + a prioritized "must-resolve-before-implementation" list.
1. **Claim-Verification Matrix** — one row per discrete claim (walk the plan §1–§15): `| Plan ref | Claim | Evidence | Verdict (CONFIRMED/WRONG/PARTIAL/UNVERIFIABLE) | Note |`.
2. **Conflict Matrix** — plan-vs-code, plan-vs-constituent-plan, intra-plan contradictions: `| Conflict | A | B | Evidence | Severity | Resolution |`.
3. **Gap Matrix** — missing / unowned / under-specified: `| Gap | Where it bites | Track | Severity | Needed |`.
4. **Complexity & Roadblock Matrix** — `| Item | Blast radius | Complexity | Roadblock | Mitigation |`.
5. **Sequencing & Dependency Matrix** — validate the 5 gates + 5 waves; find hidden dependencies / ordering hazards / false parallelism.
6. **Technical / Architectural Review** — per track, with soundness, missing design, integration seams, data-model risks.
7. **UI/UX Review** — dashboard role-gating, Profile/Build/Consult/Panchang, chart switcher, sharing, Command Center, multi-tenant cockpit/panchang; review each user flow (guest, super-admin, shared-access guest): `| Surface | Current | Target | Gap | UX risk |`.
8. **Naming-Taxonomy Review** — assess the proposed canonical taxonomy + migration risk.
9. **Elimination-Safety Review** — for each proposed deletion, is it safe + what are the consumers.
10. **GCP Review** — feasibility, cost direction, security posture of each choice/opportunity.
11. **★ INDEPENDENT PERSPECTIVE (your distinct value)** — this section is the reason you were asked. Cover:
    (a) assumptions the plan makes that you would challenge; (b) blind spots a second like-minded reviewer
    might also miss; (c) at least 3 concrete architectural/UX/sequencing ALTERNATIVES the plan didn't
    consider; (d) anything you'd do fundamentally differently and why; (e) your single biggest concern.
12. **Open-questions** — for each of the plan's open decisions, your recommendation + reasoning.

## Discipline
- Be exhaustive and evidence-led; mark confidence on every verdict. Where the plan is right, say so plainly.
- Never fabricate file contents or line numbers (re-read the rules above). Honesty about what you could not
  verify is itself a valuable finding.
- Do not start implementation. This is an independent review pass; its report will be reconciled with a
  parallel code-grounded audit.
