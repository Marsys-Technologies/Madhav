---
artifact: MODERNIZATION_AUDIT_PROMPT_GEMINI_v2_0.md
purpose: Deep-dive re-run of the Gemini audit — forces file-grounding, blocks confabulation, prevents section-collapse. Supersedes v1_0 after the v1 run came back shallow + partly confabulated.
status: prompt (read-only audit; no implementation)
date: 2026-05-27
run_environment: Gemini WITH repository file access + iteration (Antigravity / Gemini CLI / Code Assist) — NOT plain Gemini chat
expose_to_chat: false
---

# Prompt — Gemini DEEP-DIVE audit (v2, file-grounded, anti-confabulation)

RUN THIS IN AN ENVIRONMENT WHERE GEMINI CAN OPEN REPO FILES AND ITERATE (Antigravity IDE / Gemini CLI /
Code Assist). In plain chat it cannot ground and must say so. Paste everything below the line.

---

You are an independent senior architect doing a **read-only, exhaustively-grounded** audit of
`00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md` against the actual repository. A prior pass was
too shallow and invented details; this pass must be deep and provably grounded. No code changes, no plan edits.

## STEP 0 — Access + anti-confabulation gate (do this FIRST, before any audit)
1. Confirm you can read repository files. If you cannot open files, STOP and reply only: "NO FILE ACCESS —
   cannot ground this audit," and do nothing else.
2. Open `PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md` and **quote verbatim** (a) its §3 five-track list and
   (b) its §7 wave model (the wave names + the five hard gates G1–G5). Paste these quotes at the top of your
   report as proof you read the real structure. If you cannot quote them exactly, STOP and say so.
   (The prior pass invented a wave model — this gate exists to prevent that. Do not paraphrase from memory.)

## PROOF-OF-READ RULE (applies to the whole audit)
For **every** file or code claim you mark CONFIRMED or WRONG, paste a short verbatim quote (≤2 lines) with its
`path` and approximate location. **No quote = you must mark it UNVERIFIABLE.** Never invent file contents,
paths, or line numbers. An honest "UNVERIFIABLE" is correct; a fabricated citation is a failure.

## NO-COLLAPSE + DEPTH RULES
- Produce **every** numbered section AND every matrix **separately and in full** — do NOT merge §2–§9 into
  one block (the prior pass did this; it is wrong).
- Minimum depth: the Claim-Verification Matrix must have **≥ 30 rows** (walk the plan §0–§15 line by line —
  one row per discrete claim). If you find fewer, you have not read closely enough.
- This is a **multi-pass** task. If a single response would truncate, produce Part 1, then continue in the
  next message, until all 13 sections exist. Only write "✅ AUDIT COMPLETE — all sections present" when every
  section and matrix below is finished. Do not summarize to fit one message.

## READ (and verify against code)
Plan + constituents: `PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md` and `_v1_0.md`,
`PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md`, `PLATFORM_REBUILD_ARCHITECTURE_v1_0.md`,
`DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md`, `TARGET_ARCHITECTURE_REPORT_v1_0.md`,
`BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md`, `STRUCTURAL_FACT_LAYER_SPEC_v1_0.md`,
`BRIEFS/TOOL_PORTFOLIO_PLAN_v1_4.md`, `INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md`,
`MSR_UCN_CONTAMINATION_AUDIT_v1_0.md`, `CAPABILITY_MANIFEST.json`.
Code you must actually open to verify the high-stakes claims: `platform/src/lib/retrieve/msr_sql.ts`;
`platform/src/app/api/chat/consume/route.ts`; `platform/src/components/consume/TierPicker.tsx`;
`platform/src/app/api/clients/route.ts`; `platform/src/lib/mcp/primitives_registry.ts`;
`platform-mcp/src/` (server.ts, tools/, client.ts); the DB migrations under `platform/migrations/` +
`platform/supabase/migrations/`; `.github/workflows/deploy.yml`, `cloudbuild.yaml` files.

## HIGH-STAKES CLAIMS — verify each WITH a quote (prove or disprove)
1. Tenant-key fragmentation across migrations (chart_id uuid vs text vs native_id vs client_id) — list the
   tables + types you actually find.
2. De-judgment floors in `msr_sql.ts` (DEFAULT_CONFIDENCE_FLOOR, FINANCE_WEALTH_CONFIDENCE_FLOOR,
   PANCHA_MP_CLIQUE, LL1_PRODUCTION_WEIGHTS) — quote the lines.
3. Two pipelines branching on `R11V2_USE_ADAPTERS` in `consume/route.ts`; enumerate the shared stages.
4. B.11 `validateCitationsForStream` on legacy path only, not the adapter path — quote both sites (or its absence).
5. `TierPicker.tsx` maps Deep/Study/Brief → super_admin/acharya_reviewer/client — quote it.
6. Per-chart Firebase user creation in `clients/route.ts` POST — quote it.
7. `SURGICAL_TOOLS` duplicates + null `query_schema` in the manifest — quote evidence.
8. GCP: Cloud Run services + the build Job, Cloud SQL tier, dual deploy paths, public MCP — quote config.
9. Whether L2 is archived (`99_ARCHIVE/02_ANALYTICAL_LAYER/`) and no live L2 remains.
10. The 5 hard gates + 5 waves as actually written in §7 — validate the dependencies; find false parallelism.

## OUTPUT — write to `00_ARCHITECTURE/INVESTIGATION/MODERNIZATION_AUDIT_REPORT_GEMINI_v2_0.md`, all sections:
0. Access proof (the §3 + §7 verbatim quotes) + Executive summary + prioritized must-resolve list.
1. Claim-Verification Matrix (≥30 rows): | Plan ref | Claim | Quote/evidence (path) | Verdict | Note |
2. Conflict Matrix (separate): plan-vs-code / plan-vs-constituent / intra-plan.
3. Gap Matrix (separate).
4. Complexity & Roadblock Matrix (separate).
5. Sequencing & Dependency Matrix (separate) — validate G1–G5 + the waves AS WRITTEN.
6. Technical/Architectural Review — one subsection per track (Track 0 Governance + Tracks 1–5).
7. UI/UX Review — per flow (guest, super-admin, shared-access guest) + surface matrix.
8. Naming-Taxonomy Review.
9. Elimination-Safety Review (per deletion: consumers + safe?).
10. GCP Review (feasibility/cost/security).
11. ★ Independent Perspective — challenged assumptions, shared blind spots, ≥3 alternatives, biggest concern.
12. Open-questions — recommendation + reasoning for each.
End with "✅ AUDIT COMPLETE" only when all of 0–12 are present.

## DISCIPLINE
Evidence-or-UNVERIFIABLE on every verdict. Never fabricate. Where the plan is right, confirm it with a quote.
Do not implement anything.
