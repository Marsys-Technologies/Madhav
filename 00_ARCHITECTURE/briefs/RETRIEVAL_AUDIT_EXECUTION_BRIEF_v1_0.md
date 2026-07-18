---
artifact: RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md
canonical_id: RETRIEVAL_AUDIT_EXECUTION_BRIEF
version: 1.0
status: ACTIVE
type: CLAUDECODE_BRIEF (governing scope for one autonomous execution session)
authored_by: Claude (Cowork, Fable 5) 2026-07-19, native-directed
authority: >
  Native directive 2026-07-19 (Cowork retrieval-strategy session). This brief
  is the operative scope for the Claude Code session launched against it; per
  CLAUDE.md §C item 0 semantics its may_touch/must_not_touch override all
  other scope guidance for the session's duration. NOTE: the root
  CLAUDECODE_BRIEF.md (D-4 campaign pointer) does NOT govern this session —
  this session is the retrieval-strategy infrastructure track, explicitly
  authorized to run outside the doctrine-wave arc. Do not modify the root
  brief; do not open D-4.
run_mode: FULLY AUTONOMOUS — no human intervention; native runs with bypass
  permissions. Everything recorded; commits are the checkpoints.
may_touch:
  - "NEW worktree + branch (Phase 0) and everything inside it"
  - "00_ARCHITECTURE/RETRIEVAL_*.md (strategy, plan, consult — amendments)"
  - "00_ARCHITECTURE/briefs/retrieval_audit/** (NEW — all lane artifacts)"
  - "00_ARCHITECTURE/SESSION_LOG.md (append-only, close step)"
  - "git: commits on the new branch only (plus the single Phase-0 main commit)"
must_not_touch:
  - "platform/** and platform-mcp/** SOURCE (READ-ONLY for the entire session)"
  - "orchestrator, WriterBase, ga_*/bo_*/ka_*/ph_*/mi_* writers (FROZEN)"
  - "CLAUDECODE_BRIEF.md (root, D-4 pointer)"
  - "database contents (read-only queries permitted if a local/dev DSN exists; no writes)"
  - "deploy configs, CI workflows, migrations"
status_field_semantics: >
  Set status: COMPLETE in this frontmatter only when all §G acceptance
  criteria pass and the close commit is made.
---

# Retrieval Audit — Autonomous Execution Brief

## §A — Mission (two objectives, in order)

**Objective 1 — Workstream worktree.** Create the dedicated retrieval-strategy
worktree and put the doctrine set under version control.

**Objective 2 — Ground the Elevation Plan in code reality.** Audit
`RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` (v1.2) claim by claim against the
actual codebase; verify, correct, and complete it; produce the gap register
and an amended plan (v1.3) that is implementation-solid. This is an AUDIT —
no production code is changed. The deliverable is trustworthy paper, not
patches.

## §B — Mandatory context load (before any work)

Read, in order:
1. `CLAUDE.md` (v6.4 — note §I B.11 now carries the RS-4 carve-out; §N.6).
2. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 (campaign position: D-4
   INCOMING — you are NOT it; you are the parallel infrastructure track).
3. `00_ARCHITECTURE/RETRIEVAL_STRATEGY_v1_0.md` (v1.1) — the doctrine this
   audit serves; §3.5 distillation boundary, §3.6 proportionality, §5.2/§5.3
   coverage doctrine incl. service assets, §6 eight-axis rubric.
4. `00_ARCHITECTURE/RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` (v1.2) — the
   AUDIT SUBJECT. Every factual claim in §1, every phase item in §3/§7/§8.
5. `00_ARCHITECTURE/RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md` — the vendor
   constraints the plan must satisfy.
6. `00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` — **the
   Paripraśna rebuild master doc.** Read §1 (settled decisions D-03/04/05/
   08/09/12/14, A-01…A-19), §2 (open forks), §4 (engine boundary), §6, §8,
   §16 (forensic appendix), §18 (tensions). The rebuilt internal chat engine
   is the retrieval plane's largest consumer; §E Lane F below exists to keep
   the plan aligned with it.
7. `00_ARCHITECTURE/briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md` — §3
   (verified current state), §7 (findings not to relitigate).
8. `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` — live defect
   register; the audit cross-references, never duplicates, its rows.

## §C — Phase 0 (sequential, first): worktree + version control

1. From the main checkout (`git status` first; expect the doc set untracked):
   commit to **main** in ONE docs-only commit — message
   `docs(retrieval): strategy+plan+consult v1 set, PARIPRASHNA target arch, MCP handoff, RS-4 governance amendments (CLAUDE.md v6.4, PROJECT_ARCHITECTURE B.11/H.4)` —
   including: the three `RETRIEVAL_*` docs, `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`,
   `briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md`, this brief, `CLAUDE.md`,
   `PROJECT_ARCHITECTURE_v2_2.md`, `CLAUDE_MD_CHANGELOG.md`. Nothing else —
   if other unrelated dirty files exist (e.g. `BRIEF_D4.md` modifications,
   dispatch scripts), LEAVE THEM UNSTAGED.
2. `git worktree add ../madhav-retrieval ret/strategy-s1` (branch from the
   commit just made). ALL subsequent work happens in that worktree on that
   branch.
3. Verification commit-gate: `git log --oneline -2` in both trees recorded in
   the conductor ledger.

## §D — Execution model: conductor + subagent swarm

You (the session) are the **conductor**. You do not perform lane audits
yourself; you spawn subagents, integrate, and commit. Rules:

- **Parallelize lanes A–F** (§E): spawn them as parallel subagents in one
  message. Reconciliation (§F) is sequential after all lanes return.
- **Model & effort selection is yours, per task, balancing cost and need:**
  - mechanical verification (grep counts, file existence, line-cite checks):
    cheap fast models, low effort;
  - judgment work (claim adjudication, plan amendment, Paripraśna interface
    analysis): `opus` or the strongest available (`fable` if the harness
    exposes it), high effort;
  - default for lane leads: opus-class; default for their scouts: cheap.
  Record every model/effort choice in the lane ledger (it is audit data).
- **Every lane writes its own artifact** under
  `00_ARCHITECTURE/briefs/retrieval_audit/LANE_<X>_REPORT.md` with: claims
  checked, verdict per claim (CONFIRMED / STALE / WRONG / UNVERIFIABLE with
  file:line evidence), gaps found, and a model/effort/cost ledger.
- **Commit after every lane lands** (`docs(ret-audit): lane X report`), and
  after each §F step. The conductor maintains
  `00_ARCHITECTURE/briefs/retrieval_audit/STATE.md` (living ledger: lane
  status, commits, decisions, anomalies) — updated and committed at every
  transition. Start-to-end traceability is a deliverable, not overhead.
- **Failure discipline:** a lane that cannot verify a claim marks it
  UNVERIFIABLE with the reason — never guesses, never silently drops it. If
  a subagent stalls, respawn once with narrowed scope; then record the hole.

## §E — Audit lanes (parallel)

Each lane audits the plan's claims about its territory, then answers its
lane questions. Territory = read-only source inspection; DB row counts only
if a dev DSN is trivially available.

**Lane A — Catalog & registration reality (plan §1.1, R-1, R-1.5 scope).**
Verify: 123-descriptor count; the three-catalog claim (registry vs
`lib/contract/tool_metadata.ts` vs MCP hand registrations — exact counts
each); bootstrap duplication (`api/retrieval/capability/route.ts` vs
`catalog.ts`); alias inventory (45 registered / 4 retired / 6 DEFERRED —
recount live); vidhi triple-copy claim; envelope codegen state (generated
mirror + parity test — confirm the handoff's "hand-mirror" claim is stale);
`capability_version` hash scope; census comment vs `REGISTERED_TOOL_COUNT`.
Output additionally: the authoritative name↔URI↔handler table the R-1
compiler will need.

**Lane B — Envelope & budget reality (plan §1.2, R-2).**
Verify: 6-of-123 envelope adoption; the exact v3-default set (3 tools?);
judgment_flags full emitter census + the d8 object-shape violation;
`envelope_version` stuck at v1; cursor contents; density_contract exact
declarations (6?) and empty_reason honesty; `still_over_budget` unread
callers; unclamped tool list; result_clipper orphan status; chart_header
best-effort paths. Output additionally: the closed flag-enum candidate list
(every distinct flag string in the codebase, classified token/prose).

**Lane C — Planner & taxonomy reality (plan §1.3, R-3).**
Verify: consult route's non-use of vidhi; the hardcoded B.11 injection +
dead tool names; the DR-8↔compiler vocabulary disjunction and silent
`coerce` collapse; the 3+1 intent taxonomies; floor thinness numbers
(wealth 26 / career 12 / health 10 / marriage 9); dark-primitive CR list
(12/37); cr_status snapshot staleness incl. CR-55 conflict. Output
additionally: the unified-taxonomy mapping table draft (vocab A ↔ B ↔ C)
that R-3.1 will implement.

**Lane D — MCP edge & adaptivity reality (plan §1.4/§1.5, R-4).**
Verify: surface-spec fetched-and-discarded (`server.ts:287-304`);
max_tools non-enforcement; zero MCP annotations; `behavioral_overrides`
single use; description length distribution + native row-count leakage
instances (list them all); `listCapabilities` filter gap; fail-open dev
token; plan-surface entitlement bypass; `parity_check` auto-pass. Output
additionally: per-family projection feasibility notes (what the current
`getMcpSurfaceSpec` families actually contain).

**Lane E — Data-plane & service coverage reality (strategy §5.2/§5.3,
plan §8 R-1.5).**
Re-verify the 2026-07-19 census from primary sources: per-layer physical
table inventory; the dark set ((a)–(e) in strategy §5.2); the recently-
remediated set (LCA-19/LCA-4 — confirm serving works, not just wiring);
the single cross-layer join claim; **plus the service-asset inventory the
census missed**: enumerate every real-time compute surface
(ga_chart_service endpoints, panchanga service, ephemeris/python sidecars,
muhurta/tajaka/prashna computation paths), whether a retrieval capability
reaches it, and its provenance markers (`computed_at`, versions). Output:
the SERVED / INTERNAL-BY-DESIGN / RETIRED disposition draft for every
table AND service.

**Lane F — Paripraśna rebuild interface (the consumer's contract).**
From `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`: extract every requirement
the rebuilt chat engine imposes on the retrieval plane (engine boundary
§4 — headless callability; A-05 density mandatory; A-07 one loop two
doors; A-10 session pin everywhere; A-18 register block; A-19 NO-LEAKAGE;
D-14 register lint inputs; planner pipeline → PlanReceipt; disclosure-tier
as parameter; prediction-detection hooks). Cross-check each against the
plan v1.2: covered where? Under-specified where? Contradicted where?
Verify the plan's R-3 assumption that `consult/route.ts` can adopt the
Vidhi floor without violating any settled decision. Flag every point where
the rebuild and the plan pull in different directions — raised, not
resolved (handoff §8 rule 8). This lane is judgment-heavy: strongest
model, high effort.

## §F — Reconciliation (sequential, conductor + strongest model)

1. **Adjudicate** all lane verdicts into
   `retrieval_audit/GROUND_TRUTH_REGISTER.md`: every plan claim → CONFIRMED
   / CORRECTED (with the true fact) / NEW-GAP (real, not in plan) /
   PLAN-ITEM-ALREADY-DONE (reality ahead of plan). Commit.
2. **Amend the plan → v1.3** in place (`RETRIEVAL_PLANE_ELEVATION_PLAN`):
   correct stale facts, absorb new gaps into the right phases, mark
   already-done items, re-sequence if dependencies changed, update §6
   success criteria if the audit moved baselines. Changelog entry cites the
   ground-truth register. Commit.
3. **Write `retrieval_audit/AUDIT_FINAL_REPORT.md`:** executive summary,
   per-lane verdict counts, top-10 corrections, top-10 new gaps, the
   Paripraśna alignment table (Lane F), open questions for the native,
   full commit ledger, total model/effort/cost accounting. Commit.
4. **Close:** append a session entry to `00_ARCHITECTURE/SESSION_LOG.md`
   (open block, lane summary, close block per the session templates — this
   is an audit session; scope declared per this brief). Set this brief's
   `status: COMPLETE`. Final commit
   `docs(ret-audit): CLOSE — ground truth register, plan v1.3, final report`.
   Do NOT merge to main; leave the branch for native review.

## §G — Acceptance criteria (all must hold before COMPLETE)

1. Phase-0 main commit exists and contains exactly the listed doc set;
   worktree + branch exist; all audit work is on the branch.
2. Six lane reports exist, each with per-claim verdicts + evidence cites +
   model/effort ledger; zero claims silently skipped.
3. GROUND_TRUTH_REGISTER covers 100% of plan §1 factual claims and every
   §3/§7/§8 item's feasibility note.
4. Plan v1.3 committed; every CORRECTED/NEW-GAP register row traceable into
   it (or explicitly deferred with reason).
5. Lane F Paripraśna alignment table present; every conflict RAISED with a
   pointer into `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §18 style, none
   silently resolved.
6. STATE.md shows an unbroken transition log; AUDIT_FINAL_REPORT complete;
   SESSION_LOG appended; no production source file modified
   (`git diff --stat main...HEAD -- platform platform-mcp` is empty).

## §H — Hard constraints (repeat, because they bind subagents too)

- READ-ONLY on all production source. Audit ≠ fix. Defects found are
  recorded, never patched here.
- No re-derivation of the foundational chart; no DB writes; no deploys.
- Do not relitigate handoff §7 findings — verify their citations still
  hold, extend, or flag with NEW evidence only.
- Subagents inherit may_touch/must_not_touch verbatim.
- If anything forces a choice between completing the audit and staying in
  scope: stay in scope, record the blockage, continue with remaining lanes.

*End of RETRIEVAL_AUDIT_EXECUTION_BRIEF v1.0. Launch prompt lives with the
native; the session that reads this file executes it start to finish.*
