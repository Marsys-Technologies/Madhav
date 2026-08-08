# ADHIṢṬHĀNA Campaign Ledger

**Campaign:** ADHIṢṬHĀNA ("the foundation") — Campaign A of the ratified MASTER PLAN
(Identity, Promise, and the First True Measurement).
**Plan of record:** `00_ARCHITECTURE/briefs/adhisthana/MASTER_PLAN_v1_0.md` (copied verbatim
from `/Users/Dev/shad_overnight/MASTER_PLAN_IDENTITY_AND_PROMISE.md`, 2026-08-08).
**Integration branch:** `adhisthana/integration` (cut from `main` @ `ac0545c2d`, 2026-08-08).
**Conductor:** Sonnet 5, this session.
**Status:** ACTIVE — Stage 0 pre-flight complete, lanes not yet dispatched.
**This campaign ends at the checkpoint boundary.** No Campaign B (engine code, rubric
implementation) begins in this campaign regardless of time remaining.

---

## Standing rulings in force (R6–R16 carried, R17–R19 ratified 2026-08-08)

- **R17 — Adoption over addition.** Identity work is accepted by REMOVAL counts and adoption
  censuses, never module existence. A module with a dead mirror or surviving independent maps
  is a FAILED deliverable.
- **R18 — Bounded rubric scoring.** (Governs A8's spec draft.) Grades from factor rubrics,
  weights summing to 1, factor scores [0,1] from cited classical bands; no accumulating sums;
  no distribution-derived thresholds.
- **R19 — L1 stays sealed.** `chart_facts` rows are NEVER rewritten. Convergence = producer
  fixes (forward) + the derived Fact Identity Index + read-time canonicalization. The Index
  must be rebuildable from `chart_facts` alone.
- R13 (unchanged, absolute): nothing in any artifact tuned to the native's known outcomes.
- R16 (unchanged): every claim scope-stated; every status claim cites its detector query.

---

## Stage 0 — Pre-flight (2026-08-08, this session)

| Condition | Detector | Result |
|---|---|---|
| `main` == `origin/main` | `git fetch origin main && git rev-parse main origin/main` | Both `ac0545c2d…` — MATCH |
| Zero blocking in-flight PRs | `gh pr list --state open` | 3 open: #899/#898 (DRAFT, explicitly "PRESERVE do not merge", unrelated preserved state), #446 (OPEN, unrelated docs/ba-phase-3 branch). None touch ADHIṢṬHĀNA scope. Treated as non-blocking. |
| Zero in-flight worktrees | `git worktree list` | Only the main checkout — clean |
| Production == `main` | `mcp__marsys-jis-direct__mcp_server_info` | **INCONCLUSIVE, scoped honestly (R16):** live MCP server responded (`tool_count=125`, `stale=false`), but `catalog_version="catalog-1+t152+r653c2a1a98c8"` is a Cloud Run revision id, not a git SHA — `653c2a1a98c8` does not resolve as a git object in this repo (`git cat-file -t` fails). `tools_changed_at=2026-08-07T13:15:59Z`, which predates today's PR #1100 merge (~11:50 IST 2026-08-08). This does NOT by itself prove production is stale — the tool-catalog manifest mtime is a different artifact from the full app deploy and may not update every deploy. Recorded as an open unknown, not a red; nothing in Stage 0–3 (identity/registry work, read-only Index build) depends on production having PR #1100's DB6 fix live. Flagging for native/Fable at the checkpoint rather than blocking on it. |
| Plan of record committed | this ledger + `MASTER_PLAN_v1_0.md` | Copied 2026-08-08; commit pending (see below) |

**Verdict: PROCEED.** No hard blocker. One honest open unknown (production-parity check
inconclusive) carried forward, not hidden.

---

## Lane status

| Lane | Description | Status |
|---|---|---|
| A1 | Producer convergence (`ga_condition_writer` 5×`.upper()` sites + `ga_vargas_writer:3002`) | DISPATCHED — builder running in isolated worktree, PR target `adhisthana/integration` |
| A2 | Graha SSoT by promotion (`brahmagyan/graha_vocabulary.py` from `norm_graha`; TS `grahaCodeOf` canonical) | DISPATCHED — builder running in isolated worktree, PR target `adhisthana/integration` |
| A3 | Registry completion (`entity_class='varga'`, storage-code synonyms, `list_entities.ts`) | DISPATCHED — builder running in isolated worktree, PR target `adhisthana/integration` |
| A4 | Event-class TS mirror + parity + FK/CHECK + stale-comment fix | DISPATCHED — builder running in isolated worktree, PR target `adhisthana/integration` |
| — | **Rung P1** (blocking, after A2+A3) | NOT RUN |
| A5 | THE FACT IDENTITY INDEX (`chart_fact_identity` + deterministic parser) | NOT STARTED (blocked on P1) |
| — | **Rung P2** (blocking, after A5) | NOT RUN |
| A6 | Gates (registry-parity script, subject-wellformedness lint, graha/varga census in CI) | NOT STARTED (blocked on P2) |
| A7 | TS adoption debt (4 divergent domain vocabularies deleted, mirror wired live) | NOT STARTED (blocked on P2) |
| A8 | Checkpoint artifacts (Factor→Fact Coverage Matrix + V4 Rubric Spec draft) | NOT STARTED |
| — | **Rung P3** (= A8's hand-worked artifact) | NOT RUN |

---

## Removal census (R17 acceptance ledger — filled in as lanes close)

| Language | Independent graha maps before | Target | Current |
|---|---|---|---|
| Python | 13 | 1 | 13 (unchanged) |
| TypeScript | 6 | 1 | 6 (unchanged) |

| Divergent TS domain vocabularies before | Target | Current |
|---|---|---|
| 4 live + 1 dead mirror | 0 live; mirror live | 4 live + 1 dead mirror (unchanged) |

---

## Session log

- **2026-08-08 (this session, Sonnet 5):** Stage 0 pre-flight run (table above). Plan of
  record copied to `MASTER_PLAN_v1_0.md`. Branch `adhisthana/integration` cut from `main`
  @ `ac0545c2d`. Ledger opened. Next: commit these two files, then dispatch Stage 1 lanes
  A1–A4 in parallel via fresh builder subagents.
