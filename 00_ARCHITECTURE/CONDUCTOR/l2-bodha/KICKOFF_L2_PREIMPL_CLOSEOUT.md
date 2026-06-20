# L2 Bodha — Pre-Implementation Closeout (run BEFORE the autonomous buildout)

**Paste this entire file as the prompt in Claude Code (Antigravity). Single autonomous prep pass. It SETS UP the
clean state + CLOSES the open issues so the L2 Bodha buildout conductor can kick off. It does NOT build any asset
— it prepares. Halt-and-report ONLY on a genuine blocker (a destructive op that isn't safe, or prod≠main). Output
a READINESS REPORT at the end. Verify everything against the LIVE repo + prod — do not assume.**

---

## ROLE + OBJECTIVE
You are running the **L2 Bodha pre-implementation closeout**. Get the repo + prod + the open issues into the exact
state the autonomous buildout needs, then report readiness. Governing plan:
`00_ARCHITECTURE/L2_BODHA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md` **Part A**. Do the steps below IN ORDER.

## STEP 1 — Branch + commit the planning corpus (the docs are currently UNCOMMITTED + on a stale branch)
Current state (verify): you are likely on `recovery/pre-l2-stash-salvage` (diverged from main); **23 untracked
L2/L3 planning artifacts** live in `00_ARCHITECTURE/` (the 10 asset/B6 briefs, ~12 governing docs, and the
`00_ARCHITECTURE/CONDUCTOR/l2-bodha/` Conductor inputs). These are the buildout's INPUT artifacts and must be
committed onto a clean branch off CURRENT `origin/main`.
1. `git fetch origin`.
2. **Preserve the untracked docs** (they are working-tree files, not commits): copy/stash them safely, or simply
   note that `git checkout -b` preserves untracked files.
3. **Create the clean working branch off current main:** `git checkout origin/main && git checkout -b feature/l2-bodha`
   (the untracked 00_ARCHITECTURE docs carry over to the new branch — they're working-tree files).
   **Do NOT merge/rebase the 16 stale `recovery/pre-l2-stash-salvage` commits** — the build starts from clean main.
4. **`test-results/`** → add to `.gitignore` (or delete). Do not commit it.
5. **Commit the planning corpus** as one docs-only commit: `git add 00_ARCHITECTURE/ && git commit -m
   "docs(l2-bodha): planning corpus — 10 asset/B6 briefs + governing docs + Conductor inputs + L3 Kāla handoff"`.
   Push the branch: `git push -u origin feature/l2-bodha`.
6. Confirm: `git status` clean (except intended ignores); the 23 docs are tracked on `feature/l2-bodha`.

## STEP 2 — Prod == main verification (the seed→prod-divergence guard)
1. Confirm `git log origin/main` HEAD == the deployed prod Cloud Run revision (the seed→prod path has diverged
   before). If they differ → **HALT + REPORT** (do not start a buildout on a prod that isn't main).
2. Confirm migrations through the current max (≤324 in `platform/migrations/`) are APPLIED on prod, not just on
   disk. Bring up the Cloud SQL proxy (`platform/scripts/start_db_proxy.sh`, port 5433) and check the migration
   ledger / `/api/cockpit/stats?chart_id=482012f1-710e-4a25-994a-93821f5871aa` for live L0+L1 asset state.
3. Confirm **`platform/migrations/` is the canonical tree (max 324)** — new L2 migrations will start at 325+.
   Record the exact current max in the readiness report (the conductor numbers from max+1).

## STEP 3 — Close F2: RM subsystem-remedy corpus coverage
The remedy corpus is DESIGNED for medical/vastu/nakshatra/ayurvedic remedials (asset bg_remedies scope) but the
consuming path was planet-only. VERIFY the L0 `brahma_remedy_corpus` CONTENT:
1. Query: does it contain rows keyed by / applicable to **nakshatra**, **direction (vastu)**, **body_part
   (medical)**, **dosha** — not just planet? Report counts per type.
2. Where rows EXIST → note "covered; bo_upaya §R5 will query by all affliction keys." Where a type has the
   design-slot but ZERO rows → record it as an **L0-corpus-expansion gap** in the readiness report (the buildout
   handles it as a tracked sub-task or a documented `remedy_corpus_gap` — NEVER invent remedies; grounding is absolute).

## STEP 4 — Confirm the cross-subsystem L0 mappings (for the §XS edges)
bo_karanajala §XS builds cross-subsystem edges from L0 classical cross-discipline mappings. VERIFY they exist:
1. `bg_nakshatra_medical` (nakshatra→body-part) — should exist (was verified at plan time). Confirm + row count.
2. The vastu mapping (graha→direction) + any other cross-discipline tables — confirm they exist or record the gap.
3. Where a mapping is MISSING → record as a tracked gap (the §XS edge family covers what's available + flags the rest).

## STEP 5 — Embedding regime confirmation + cleanup decision
1. Confirm the LIVE classical corpus (`classical_text_chunks`) is embedded with `text-multilingual-embedding-002`
   (768-dim) — the model bo_samskara must match.
2. Run a reverse-citation check on the STALE `classical_chunks` (mig 158, text-embedding-004 + ivfflat): does ANY
   live code read it? If NO → record "safe to retire" (the buildout retires it). If YES → record the reader
   (it's on the old corpus; the buildout repoints it). **Do not retire it in this prep pass — just diagnose + report.**

## STEP 6 — Confirm the Conductor inputs are in place
1. `00_ARCHITECTURE/CONDUCTOR/l2-bodha/session_queue.yaml` exists + is valid YAML (the wave queue + the hard spine gate).
2. `00_ARCHITECTURE/CONDUCTOR/l2-bodha/KICKOFF_L2_BODHA_AUTONOMOUS.md` exists (the buildout paste-prompt).
3. Create the Smṛti dir + halt log if absent: `00_ARCHITECTURE/CONDUCTOR/l2-bodha/smriti/` + `CONDUCTOR_HALT_LOG.md`.
4. Confirm all 10 asset/B6 briefs referenced in the queue's `asset_briefs` map exist on disk.

## STEP 7 — THE READINESS REPORT (the deliverable)
Write `00_ARCHITECTURE/CONDUCTOR/l2-bodha/PREIMPL_READINESS_REPORT.md` with:
- branch `feature/l2-bodha` created off main + the docs committed (commit SHA) + pushed.
- prod==main: PASS/FAIL (+ the prod revision + the current migration max → the buildout's start number).
- F2: per-remedy-type corpus coverage counts + any `remedy_corpus_gap` flagged.
- cross-subsystem L0 mappings: present/missing per mapping.
- embedding: live model confirmed + classical_chunks retire/repoint diagnosis.
- Conductor inputs: present + valid; Smṛti dir created; all 10 briefs present.
- **VERDICT: READY TO KICK OFF THE BUILDOUT (yes/no)** + any blocker.

## HARD STOPS (this prep pass)
- prod ≠ main (Step 2) → HALT + REPORT (do not build on a divergent prod).
- a destructive op that isn't provably safe → HALT + REPORT.
- Everything else → diagnose, record in the readiness report, continue. This pass does NOT build assets and does
  NOT apply L2 schema migrations (that is Wave-0 of the buildout) — it PREPARES + REPORTS.

**Begin: STEP 1. Verify state against the live repo + prod at each step. Produce the readiness report. Go.**
