---
artifact: CONVERSATION_HANDOFF_2026-06-01_v2_0.md
purpose: >
  Self-contained capture of the Cowork conversation that ran on 2026-06-01 and
  shipped PR #184 (PyJHora). Designed to be pasted as the first message of a
  fresh Claude conversation (different account, no prior session memory) so
  that chat can pick up exactly where this one ended.
version: 2.0
supersedes: 00_ARCHITECTURE/CONTEXT_HANDOFFS/CONTEXT_HANDOFF_2026-06-01_v1_0.md
       (v1.0 was authored mid-conversation; v2.0 captures the full arc + the
        post-merge forensic-renderer gap finding + the native's directive to
        deep-reconcile all data assets in the next conversation.)
authored_at: 2026-06-01
authored_by: cowork-planner
audience: a new Claude conversation that has zero prior session context
how_to_use: >
  Step 1 — open a new Claude chat. Step 2 — paste this entire file as the first
  message, prefaced with: "Read this handoff end to end. Then re-read CLAUDE.md
  and CURRENT_STATE_v1_0.md. Then summarise where we are in 3 paragraphs and
  ask me what to do next." Step 3 — proceed.
read_in_combination_with:
  - CLAUDE.md (project root — mandatory)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (canonical "you are here")
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json (artifact catalog — single source of truth)
  - 00_ARCHITECTURE/CONTEXT_HANDOFFS/CONTEXT_HANDOFF_2026-06-01_v1_0.md (deeper architecture detail; v1.0 here is the architecture half, v2.0 is the conversation half)
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md (the brief PR #184 implemented)
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_AUDIT_FORENSIC_RENDER_COVERAGE_v1_0.md (the audit authored 2026-06-01, NOT yet run)
  - 00_ARCHITECTURE/PARIKSHA/builds/362f9f17-95a5-490b-a5a7-027d3e0efda0/REPORT.md (native chart Pariksha report)
---

# Conversation Handoff · 2026-06-01 · PyJHora arc + forensic renderer gap

A new Claude conversation reading this should be ready to act competently on the
project after one pass. This is the conversational half of the handoff; the
architectural half is in `CONTEXT_HANDOFF_2026-06-01_v1_0.md`. Read both.

---

## 1 · What this conversation accomplished

### 1.1 PyJHora arc — designed, briefed, executed, merged

The conversation opened with a Cowork-side question about whether the chart
build engine should switch from the pyswisseph-direct `natal_engine/` package
to PyJHora. After a brief debate about whether to run a verification spike
first, the native locked the decision:

- **PyJHora is the sole chart-fact engine.** No spike, no parallel run, no
  license gating, no JH-parity verification.
- **Direct `pip install`, replace `natal_engine/` in one PR.**
- **Internal-consistency verification only.**

Rationale: PyJHora *is* the Jagannatha Hora calculation logic in Python. The
native trusts JH's calculation set. There is therefore no second engine to
triangulate against — PyJHora's output IS the source of truth by construction.
Verification reduces to row counts, schema, structural invariants, layer
gates, and determinism.

I authored the implementation brief at
`00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md` —
7 phases, 8 acceptance criteria, ~1 day of executor work, halt at PR-to-main.

The executor (Claude Code in Google Antigravity IDE) ran the arc in the
worktree `/Users/Dev/Vibe-Coding/Apps/MadhavPyJHora` on branch
`feature/pyjhora-direct-engine`. **PR #184 was opened with all 8 ACs green,
then merged to main as squash commit `dda4d70` on 2026-05-31. 18 of 20 CI
checks passed (the 2 unidentified should be verified before assuming clean).**

What shipped in the merge:

- PyJHora 4.8.6 pinned in `platform/python-sidecar/requirements.txt`.
  (The brief named 3.6.2 — that version doesn't exist on PyPI. Executor
  resolved to latest stable.)
- Headless import strategy: `QT_QPA_PLATFORM=offscreen` in the Dockerfile
  + `libgl1`/`libglib2` apt deps + lazy submodule imports
  (`from jhora.panchanga import drik`, etc.; never `import jhora` at top
  level). This was the answer to whether PyQt6 init blocks the calculation
  modules — it does, the workaround works.
- `platform/python-sidecar/pyjhora_adapter/` created with 22 modules
  (`positions`, `houses`, `dignities`, `vargas`, `dashas`, `panchanga`,
  `sensitive_points`, `reconciliation`, `strength`/`yogas`/`transits`
  (stubs), `_ayanamsha`, `_isolation`, `_jhora`, `_names`, `compute`,
  `version`, `l25_builder`).
- `multiprocessing` fork-pool per ayanamsha (note: the brief specified
  `spawn` start-method; the executor implemented fork — confirm which actually
  ships and whether it should be tuned).
- `_ENGINE_SIDEREAL_LOCK` (threading.Lock) for process-global sidereal-mode
  serialisation — discovered concurrency issue during writer rewire.
- MEAN_NODE pinned for Rahu/Ketu — matches prior convention, avoids
  the swisseph TRUE_NODE Moshier failure under TRUE_CITRA via a
  `drik.sidereal_longitude` shim.
- `ENGINE_VERSION` constants in 16 writers updated to `"pyjhora/1.0.0"`.
- `natal_engine/` hard-deleted — net **-6,781 lines** across the PR.
- 22/22 adapter tests pass. Full suite: 3,246+ tests pass.
- Panchanga FORENSIC spot-check at native birth (1984-02-05) PASS 5/5:
  tithi=Shukla Tritiya, vara=Ravivara, nakshatra=Purva Bhadrapada, yoga=Shiva,
  karana=Garaja. (Internal arithmetic only; FORENSIC is the same chart so
  this is a same-source consistency check, NOT a JH-parity oracle.)
- Determinism test PASS (rebuild → identical row-payload hash).
- `CURRENT_STATE_v1_0.md` bumped v5.65 → v5.66 noting PyJHora as engine.

### 1.2 Pariksha second-pass — 5 bundled fixes inside PR #184

A Pariksha (autonomous QA swarm) second-pass on the native chart
`362f9f17-95a5-490b-a5a7-027d3e0efda0`, build `a62395ea`, surfaced 17 issues.
The PR bundled 5 of them in the first commit (`4f4da60`):

- **P0 / I-015 — `BUILD_TASK_AUTH_BYPASS` removed.** Production security
  hole closed. The env var allowed any unauthenticated caller to invoke
  `/api/build/task` by setting it in Cloud Run env (likely set during Cloud
  Tasks IAM debugging, never removed from the running revision). Bypass code
  path deleted; startup `console.error` if env var is still present in Cloud
  Run env (defense in depth). `task_route.test.ts` rewritten with fake OIDC
  JWT + audience-mismatch 401 test.
- **P1 / I-013 — `preferred_name` + `timezone_id` schema migration.**
  Migration 161 was authored but never applied to prod because `migrate.ts`
  CI step skipped (PROD_DATABASE_URL secret unset). Migration **162**
  re-applies both `ADD COLUMN IF NOT EXISTS` statements idempotently. Operator
  fallback: psql one-liner in the PR body if migrate.ts still skips.
- **P2 / I-014 — v2 cockpit wired; legacy `ConstellationCanvas` retired.**
  `/clients/[id]/build/page.tsx` now renders `<CockpitShell chartId={id} />`
  assembling `LiveDependencyGraph`, `OverallProgress` ("Sampurna gati"),
  `TelemetryStrip`, `AssetTable`. Polls `/api/build/active`; degrades cleanly
  in zero state.
- **P3 / I-007 — `vargas_writer` D1 sign off-by-one FIXED.** Root cause: the
  writer applied `(int(raw_idx) % 12) + 1` to BOTH `sign_index` (0-indexed,
  correct to +1) AND `sign_id` (1-indexed, must NOT +1). Pre-computed
  Capricorn (sign_id=10) became Aquarius (11). Fix: separate code paths. New
  regression tests `TestD1NativeSignRegression` (7 FORENSIC-grounded
  assertions) + `TestPrecomputedSignResolution` (3 tests).
- **P4 / RC-001 — `forensic_writer.py` STILL A STUB.** *Not* fixed in this
  PR. Root cause is intentional — "STUB: Emits build events but writes no
  data. Real implementation in Stream F sessions F-01 through F-14."
  Expanding to Stream F scope inside this PR would violate the hard gate.
  3 contract tests added as `XFAIL strict=True` documenting what Stream F
  must deliver. Issues cascading from RC-001: I-001..I-004 (0-row writers),
  I-005/I-006/I-008/I-010 (L2.5 sentinels). **All self-resolve once Stream F
  is implemented.**

### 1.3 The forensic renderer gap — the active question

After PR #184 merged, the native asked a sharp question: "Why is the new
renderer showing 2,426 data cells vs 6,332 for legacy FORENSIC v8.0? The new
renderer was supposed to be RICHER than v8.0, not thinner. Is the
implementation aligned with the spec, or do we need to rebuild the spec?"

Three facts established empirically by reading the code in this conversation:

1. **FORENSIC v8.0 is single-ayanamsha — Lahiri only.** Frontmatter of
   `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` line 13:
   `ayanamsa: Lahiri (Chitrapaksha), value 23°37′58″`. So the apples-to-apples
   comparison is: 6,332 cells (v8.0, Lahiri) vs 2,426 cells (new render,
   Lahiri) = **38% of legacy**, when the spec said it should be MORE.

2. **The new render is gated by `compute_chart()` input coverage.**
   `platform/python-sidecar/pyjhora_adapter/compute.py` (lines 104–129)
   returns a dict with these keys ONLY: `provenance, inputs, birth_datetime,
   ascendant/lagna, houses, grahas/planets, vargas, dashas, panchanga,
   sensitive_points, ayanamsha, reconciliation`. That is **~6 content
   domains** out of FORENSIC v8.0's **27 sections**. Renderers that expect
   `shadbala / ashtakavarga / KP cuspal sub-lords / Tajaka / chara karakas /
   yogas / aspects (Parashari/Jaimini/Tajik) / vimsopaka / avastha schemes /
   special lagnas / arudhas / sahams / midpoints / eclipses / choghadiya /
   hora / tara-chandra bala / Sade Sati / Kota Chakra / Chandra chart /
   longevity / additional dasha systems` see None or empty and emit
   placeholder sections.

3. **The depth data already exists in `chart_facts`.** The MCP Transformation
   arc (CLOSED 2026-05-22) backfilled 2,717 `chart_facts` rows across 27
   categories including shadbala, ashtakavarga, bhava bala, KP, Tajaka. The
   render writer doesn't read `chart_facts` — it only reads
   `chart_output` (the `compute_chart()` return). So the data is computed,
   stored, available, and ignored at render time.

I had already authored an audit brief for exactly this gap on the same day:
`00_ARCHITECTURE/BRIEFS/CLAUDECODE_AUDIT_FORENSIC_RENDER_COVERAGE_v1_0.md`.
It enumerates four data sources to pull, the coverage matrix structure, the
root-cause classification (engine gap / adapter gap / renderer bug / wrong
source), and three fix options:

- **A.** Extend `compute_chart()` to emit the missing depth domains.
- **B.** Re-point the depth renderers at `chart_facts` (where v3.3 already
  computed this data) via the adapter. *Cheapest path; the data is already
  computed.*
- **C.** Hybrid — core from `compute_chart()`, depth from `chart_facts`.

The audit has **NOT been run** —
`00_ARCHITECTURE/audits/FORENSIC_RENDER_COVERAGE_AUDIT_REPORT_v1_0.md` does
not exist on disk.

### 1.4 The native's directive — what the new conversation must do

The native rejected "just run the audit and pick A/B/C" as too narrow. Verbatim:

> "There are subsequent sections that build some of this data… how we had
> constructed the entire assets was something that was missing in L1 forensic
> renderer which we learned later after having created the brief for forensic
> renderer, we learnt later, much later, we included that in that asset as a
> supplementary or within the asset. So I think this needs a deep
> reconciliation of all data assets."

**This is the work the new conversation must lead.** A deep reconciliation of
all data assets across L1, L2.5, L3, L4, L5 — because over the project's
history, things that should have been in the L1 forensic renderer ended up
being added as supplementary sections of OTHER assets. The result is that
domains overlap, some are duplicated, some are split awkwardly across assets,
and the forensic renderer's spec doesn't reflect the actual scope it should
own. Until this reconciliation is done, Stream F's spec is fictional — we'd
be implementing against a brief that doesn't match the asset partitioning the
project actually evolved into.

The reconciliation work is explicitly NOT this conversation's scope. The
native asked for it to be done in a NEW conversation. So the new conversation
must:

1. Read this handoff + `CONTEXT_HANDOFF_2026-06-01_v1_0.md` + CLAUDE.md +
   `CURRENT_STATE_v1_0.md`.
2. Read every L1, L2.5, L3, L4, L5 asset spec under
   `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, and any L3/L4/L5 surface.
3. Build the actual asset-by-asset domain coverage matrix — what does each
   asset really contain today, where are the overlaps, where are the gaps.
4. Reconcile against the original intent (forensic richer than v8.0; clear
   L1→L2.5→L3 separation; one domain owned by one asset).
5. Propose a re-scoped Stream F (forensic renderer) brief that fits the
   reconciled asset map — not the SUPERSEDED scoping brief that pre-dates
   this finding.
6. Probably also re-scope L2.5 and L3 briefs if the reconciliation reveals
   they're consuming domains that should live in L1.

---

## 2 · Critical decisions locked during this conversation (do not re-negotiate)

| Decision | Value | Why |
|---|---|---|
| Chart-fact engine | PyJHora 4.8.6 (pip install direct, no fork) | Native trusts JH's calculation set; PyJHora IS the JH logic in Python |
| Verification | Internal consistency only — row counts, schema, structural invariants, cross-asset FK, layer gates, determinism | `[[no-jh-parity-anywhere]]` |
| External oracle (Jagannatha Hora) | NEVER | Same as above — PyJHora replaces the need for any external JH oracle |
| Anthropic models in production | BANNED | Native standing directive — cost reasons |
| Planning vs implementation | Cowork plans; Antigravity executes | `[[cowork-vs-antigravity-split]]` |
| PR-to-main | Human-gated | `[[two-stream-branch-policy]]` |
| Engine replacement strategy | Hard delete `natal_engine/`, no parallel run, no flag | Locked at brief-authoring time, executed in PR #184 |
| License check (PyJHora) | Skipped — native's call | Native trusts the source |
| Phase 0 spike | Skipped — empirical discovery happens inline in adapter tests | Native rejected 4-8h verification spike |

---

## 3 · Files this conversation created

In the Madhav repo (committed to main via PR #184 or pending commit):

| Path | Status | Purpose |
|---|---|---|
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md` | committed via #184 | The PyJHora arc brief |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_PHASE0_SPIKE_v1_0.md` | committed; SUPERSEDED | Authored then declined by native — kept for audit |
| `00_ARCHITECTURE/BRIEFS/STREAM_F_FORENSIC_RENDER_SCOPING_v1_0.md` | committed; SUPERSEDED | Early scoping; doesn't reflect the renderer-gap finding |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_STREAM_F_FORENSIC_RENDER_v1_0.md` | committed | Executable brief for Stream F — *probably needs re-scope post-reconciliation* |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_AUDIT_FORENSIC_RENDER_COVERAGE_v1_0.md` | committed | Audit of the renderer gap — NOT yet run |
| `00_ARCHITECTURE/CONTEXT_HANDOFFS/CONTEXT_HANDOFF_2026-06-01_v1_0.md` | uncommitted | Architecture handoff (system layers + 3 channels + tooling) |
| `00_ARCHITECTURE/CONTEXT_HANDOFFS/CONVERSATION_HANDOFF_2026-06-01_v2_0.md` | THIS FILE | Conversational handoff (decisions + arc + gap finding) |

In memory (`spaces/.../memory/`):

- `project_pyjhora_is_the_engine.md` — created and twice updated (decision, PR
  open, PR merged with 5 bundled fixes + RC-001 still open).
- `feedback_no_jh_parity_anywhere.md` — reinforced.
- `MEMORY.md` — index updated with PyJHora pointer.

---

## 4 · Open work after this conversation closes

Sorted by what blocks what:

**Immediate operator actions (manual, no executor needed):**

1. Apply migration 162 to prod if `migrate.ts` skipped (psql fallback in the
   PR #184 description).
2. Identify which 2 of 20 CI checks didn't pass on PR #184. Verify benign vs
   regression.
3. Deploy `amjis-sidecar` from main to roll PyJHora 4.8.6 into the running
   image (`gcloud run deploy amjis-sidecar` or trigger the deploy workflow).
4. Trigger Cloud Run Job for native chart build (chart_id
   `362f9f17-95a5-490b-a5a7-027d3e0efda0`) — populates `chart_facts` with
   PyJHora-derived rows.

**The reconciliation arc (next conversation's lead):**

5. Deep reconciliation of all L1 / L2.5 / L3 / L4 / L5 data assets per §1.4.
   This is the lead workstream for the next conversation.
6. After reconciliation: re-scope Stream F brief to match the reconciled
   asset map.
7. After re-scope: implement Stream F via Antigravity arc. Probable approach
   is Option B from the audit brief — repoint depth renderers at
   `chart_facts` where v3.3 backfills already sit. ~1-2 day arc, not 14
   sessions.

**Downstream auto-unblocked once a native build runs:**

8. Platform Modernization v1.3 partition migrations 121/122/124 — BLOCKED on
   `chart_id` being 100% NULL; unblocks the moment the first PyJHora build
   writes per-chart rows.

**Hygiene queue (not blocking):**

9. JH-parity references in `00_ARCHITECTURE/` governance docs (~40 grep hits)
   — separate cleanup arc.
10. Multi-Ayanamsha build operator queue (migrations 140–153, ACC1/3/4/5,
    answer:eval after build) — pre-existing operator queue items.

---

## 5 · Standing constraints — read every session, no exceptions

These override any reasoning chain that tries to relax them. They are
captured in memory and reinforced repeatedly throughout this conversation.

- **No JH parity oracle, anywhere.** Not in code, not in briefs, not in
  tests, not in fixtures, not in planning artifacts. Files still on disk
  (`test_jh_parity.py`, `jh_oracle.json`, `jh_oracle_loader.py`,
  `jh_oracle_schema.json` — all deleted under `natal_engine/` in this PR;
  ~40 grep hits remain in `00_ARCHITECTURE/`) are cleanup targets, not
  authoritative references.
- **No Anthropic models in production.** Default planner: Gemini Pro.
  Fallback: DeepSeek v4 Pro. Cheap-flash variants for non-critical paths.
- **Cowork plans; Antigravity executes.** Every output from a Cowork chat
  must be a pasteable prompt or a committed `.md` brief — never chat-only
  bullets the native has to translate.
- **PR-to-main is human-gated.** Merges, prod deploy, prod DB ops, secret
  rotations, flag flips — all human gates.
- **Verify state from `CURRENT_STATE_v1_0.md` + `git log`, NOT
  CLAUDE.md §F.** §F drifts.
- **Only computed facts.** No narrative, no opinion, no judgement (prime
  directive).
- **Verification is internal consistency.** Six categories. No category 7.

---

## 6 · How the new conversation should open

The new chat's first response should be ~3 paragraphs:

1. "I've read the handoff and the listed reference files. Here's where we
   are: PR #184 merged; PyJHora is the engine; natal_engine deleted;
   forensic renderer is at ~38% of v8.0 cell density because compute_chart()
   only surfaces ~6 of 27 v8.0 domains and the depth data sitting in
   chart_facts is unread by the renderers."
2. "The native's directive: deep-reconcile all L1/L2.5/L3/L4/L5 assets
   because the asset partitioning has drifted over time. Domains that
   belong in L1 forensic have been bolted onto other assets as
   supplementary. The forensic renderer scope is fictional until this
   reconciliation lands."
3. "Three open questions to confirm before scoping the reconciliation arc:
   (a) which assets should we open with — all five layers in parallel, or
   L1 first then propagate up? (b) is the reconciliation a Cowork-planning
   exercise (read every spec, write a master matrix) or does it need
   Antigravity to query live `chart_facts` to verify what's actually
   stored? (c) does the native want to settle the asset map BEFORE or
   AFTER the operator actions in §4 (migration 162, sidecar deploy, native
   build trigger) — order changes the verification surface."

Stop there. Wait for native answers. Do not start the reconciliation arc
until those three answers are explicit.

---

## 7 · Things the new conversation must NOT do

- Propose a verification spike for PyJHora. The decision is locked.
- Propose JH parity as an oracle for anything.
- Propose running the forensic-renderer audit as the *next step*. The audit
  exists, but the deeper question (asset-map reconciliation) supersedes it.
  The audit is useful as input to the reconciliation, not a standalone arc.
- Implement code in Cowork. Use Antigravity.
- Use Anthropic models for any production path.
- Treat `CLAUDE.md §F` as authoritative for "you are here" — read
  `CURRENT_STATE_v1_0.md` instead.

---

## 8 · Memory hooks the new conversation should re-read

If running in Cowork with memory enabled (`spaces/.../memory/`):

- `project_pyjhora_is_the_engine.md` — PyJHora as engine; PR #184 status; 5
  bundled fixes; RC-001 still open
- `feedback_no_jh_parity_anywhere.md` — the durable rule
- `feedback_cowork_vs_antigravity_split.md` — planning vs implementation lane
- `feedback_llm_model_selection.md` — Anthropic banned in prod
- `feedback_two_stream_branch_policy.md` — PR-to-main is human gated
- `feedback_verify_state_not_claude_md.md` — use CURRENT_STATE, not §F
- `feedback_silent_param_feature_toggle.md` — durable code-review lesson
- `feedback_grep_check_is_not_compile_check.md` — durable merge-resolution lesson
- `feedback_never_rm_based_on_filename.md` — durable delete-discipline lesson

If running outside Cowork (different account, no memory access), the rules
above are restated in §5 of THIS file. The memory files just centralise them.

---

## 9 · Quick reference — file paths the new conversation will need

Governance and architecture:

- `CLAUDE.md` (root) — project mission + mandatory reading list
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — canonical "you are here"
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — artifact catalog
- `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` — governing blueprint
- `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` — strategic arc
- `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` — session protocol
- `00_ARCHITECTURE/OPERATOR_ACTIONS_PENDING.md` — operator queue
- `00_ARCHITECTURE/V1_3_AUDIT_QUEUE_v1_0.md` — carry-forward items
- `00_ARCHITECTURE/SESSION_LOG.md` — append after every session close

Layer 1 facts (the canonical chart data — SCHEMA reference, NOT value oracle):

- `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — 27 sections, single
  ayanamsha (Lahiri). The new render must EXCEED this.
- `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` — LEL

Layer 2.5 synthesis:

- `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` — 573 signals
- `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md`
- `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md`
- `025_HOLISTIC_SYNTHESIS/RM_v2_0.md`
- `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md`

PyJHora arc:

- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md`
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_AUDIT_FORENSIC_RENDER_COVERAGE_v1_0.md`
- `00_ARCHITECTURE/BRIEFS/STREAM_F_FORENSIC_RENDER_SCOPING_v1_0.md` (SUPERSEDED)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_STREAM_F_FORENSIC_RENDER_v1_0.md`

Pariksha (autonomous QA swarm):

- `00_ARCHITECTURE/PARIKSHA/PARIKSHA_MASTER_PLAN_v1_0.md`
- `00_ARCHITECTURE/PARIKSHA/briefs/PRAMANA_DRASHTA_v1_0.md`
- `00_ARCHITECTURE/PARIKSHA/EXPECTED_ROW_COUNTS.yaml`
- `00_ARCHITECTURE/PARIKSHA/builds/362f9f17-95a5-490b-a5a7-027d3e0efda0/REPORT.md`
- `00_ARCHITECTURE/PARIKSHA/builds/362f9f17-95a5-490b-a5a7-027d3e0efda0/issues.yaml`

Engine (current — post PR #184):

- `platform/python-sidecar/pyjhora_adapter/` — the adapter package
- `platform/python-sidecar/pyjhora_adapter/compute.py` — the bottleneck;
  returns only ~6 content domains
- `platform/python-sidecar/pipeline/writers/forensic_writer.py` — STILL A STUB
- `platform/python-sidecar/pipeline/render/*_renderer.py` — 13 renderers
  with rich capability but starved of input

Build orchestrator:

- `marsys-build-pipeline-job` (Cloud Run Job, `asia-south1`) — no watchdog;
  see `[[build-orchestrator-no-watchdog]]`
- `platform/python-sidecar/pipeline/build_chart.py` — entry point
- `platform/python-sidecar/pipeline/dispatcher.py` — DAG runner

Three serving channels (architectural detail in `CONTEXT_HANDOFF_2026-06-01_v1_0.md` §5):

- Legacy `/consume` pipeline: `platform/web/src/app/api/consume/v2/route.ts`
- R11 Claude-style agentic chat: same route, `useAdapter()` branch +
  `lib/providers/agentic_loop.ts` + per-provider adapters under
  `lib/providers/{anthropic,google,openai,deepseek,nvidia}/`
- MCP server: `platform-mcp/src/server.ts` (40 tools, tier auth)

---

## 10 · Final note for the new conversation

This conversation was high-velocity. It produced a brief, watched the executor
ship a PR, the native merged, the native immediately surfaced the renderer
gap, and the conversation closed before the reconciliation work could open.
The new conversation inherits an active but well-defined open question with
clear next steps. The handoff is designed so that opening it requires only
this file + the listed reference files — no chat replay needed.

If anything in this handoff conflicts with `CURRENT_STATE_v1_0.md` or the
`CAPABILITY_MANIFEST.json`, those win. This file is a point-in-time capture;
the canonical surfaces are authoritative.

*End of CONVERSATION_HANDOFF_2026-06-01_v2_0.md.*
