---
artifact: CLAUDECODE_BRIEF_PSHIP_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-20
session_id: PSHIP-S1
session_name: PSHIP-S1 — Additive Panchang transplant onto current main + conflict map
executor: Claude Code sub-agent (Conductor)
execution_mode: autonomous, --dangerously-skip-permissions
worktree:
  name: PanchangShip
  branch: feature/panchang-ship
  base: main (current, with Conductor merged)
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
source_branch: feature/phase-4c-panchang (the Wave 1 build — 125 ahead / 88 behind main)
predecessor: Wave 1 complete (built, unmerged); Conductor merged to main
---

# CLAUDECODE_BRIEF — PSHIP-S1
## Transplant the additive Panchang files onto current main + produce the shared-file conflict map

The Wave 1 Panchang module lives on `feature/phase-4c-panchang`, which is 88 commits behind main. Rather than rebase that hell, this session transplants the **additive** Panchang files (new files that don't exist on main — they copy cleanly) onto a fresh branch cut from current main, and produces a precise map of the **shared** files (that DO exist on main and need careful integration in PSHIP-S2).

---

## §0 — Pre-flight (Conductor sub-agent)

```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
git branch --show-current   # expect: feature/panchang-ship
git log -1 --oneline        # expect: current main HEAD (with Conductor)
test -d 00_ARCHITECTURE/CONDUCTOR   # Conductor present (merged to main)
git rev-parse --verify origin/feature/phase-4c-panchang   # source branch reachable
```
Halt with HALT_NEEDS_HUMAN if the worktree isn't on `feature/panchang-ship` cut from current main, or if `feature/phase-4c-panchang` isn't reachable.

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. This brief
3. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` §7 (Critical Files Map — the authoritative list of files Panchang creates vs modifies) — read from the source branch: `git show origin/feature/phase-4c-panchang:00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md`

## §3 — Scope (7 items)

### Item 1 — Inventory all Panchang files on the source branch
List every file `feature/phase-4c-panchang` adds or modifies relative to its merge-base with main:
```bash
git diff --name-status $(git merge-base origin/main origin/feature/phase-4c-panchang) origin/feature/phase-4c-panchang
```
Classify each path as **A (added — not on current main)** or **M (modified — exists on current main)**. Cross-check existence against current main with `git cat-file -e origin/main:<path>`.

**AC.PSHIP1.1:** Full classified inventory written to `00_ARCHITECTURE/PSHIP_FILE_INVENTORY.md` — every path tagged A or M, with the count of each.

### Item 2 — Transplant the ADDITIVE files
For every A-classified path, bring it from the source branch:
```bash
git checkout origin/feature/phase-4c-panchang -- <path>
```
Expected additive set (verify against Item 1, don't assume): `platform/python-sidecar/panchang_engine/**`, `platform/python-sidecar/routers/panchang.py`, `platform/python-sidecar/routers/muhurat.py`, `platform/src/app/panchang/**`, `platform/src/lib/retrieve/query_panchanga.ts`, `platform/src/lib/panchang/**`, `platform/src/lib/security/sign_url.ts`, `platform/src/app/api/panchang/**`, `platform/src/components/ui/star-rating.tsx`, `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md`, the Panchang briefs + close artifacts under `00_ARCHITECTURE/`, the Panchang master plan.

Do NOT touch any M-classified (shared) file in this session — those are PSHIP-S2.

**AC.PSHIP1.2:** All additive files present on `feature/panchang-ship`; `git status` shows them staged; no shared file modified yet.

### Item 3 — Produce the shared-file conflict map
For every M-classified path, write a precise integration spec to `00_ARCHITECTURE/PSHIP_CONFLICT_MAP.md`. For each shared file, capture:
- The path
- What Panchang's version added (diff the source branch's version against the merge-base for that file)
- What main's current version looks like (has it structurally changed since the merge-base?)
- A proposed integration: exact lines/blocks to add to main's current version
- A risk flag: LOW (clean insert, main unchanged in that region) / MED (main changed nearby) / HIGH (main restructured the file — needs human judgment)

Expected shared files: `platform/src/components/shared/AppShellRail.tsx`, `platform/src/components/shared/MobileNavSheet.tsx`, `platform/python-sidecar/main.py`, `platform/src/lib/retrieve/index.ts`, `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`, `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`, `.github/workflows/deploy.yml`, `CLAUDE.md`, `.geminirules`, possibly `platform/src/app/clients/[id]/consume/page.tsx` + `platform/src/lib/synthesis/prompts.ts` (Ask-Madhav context injection).

**AC.PSHIP1.3:** `PSHIP_CONFLICT_MAP.md` covers every M-classified file with a proposed integration + risk flag.

### Item 4 — Compile the transplanted additive code
Run TypeScript + Python checks on the additive files (they may reference shared-file symbols not yet integrated — note expected failures):
```bash
cd platform && npx tsc --noEmit 2>&1 | tail -30
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip/platform/python-sidecar/panchang_engine && python3 -m pytest -q 2>&1 | tail -15
```
The panchang_engine tests should pass standalone (no shared-file deps). TS may show errors for the not-yet-wired shared files (query_panchanga not in RETRIEVAL_TOOLS yet, etc.) — document these as EXPECTED-until-S2.

**AC.PSHIP1.4:** panchang_engine pytest green; TS errors catalogued as expected-until-S2 (no surprises).

### Item 5 — Commit the additive transplant
```bash
git add -A
git commit -m "PSHIP-S1: transplant additive Panchang files onto current main"
```

**AC.PSHIP1.5:** Single commit with all additive files; shared files untouched.

### Item 6 — HIGH-risk halt check
Review `PSHIP_CONFLICT_MAP.md`. If ANY shared file is flagged HIGH risk (main restructured it — e.g., AppShellRail's NAV_ITEMS array shape changed, or main.py's router registration pattern changed), emit `HALT_NEEDS_HUMAN` with the list of HIGH-risk files. PSHIP-S2 needs human guidance on those before integrating. If all are LOW/MED, proceed to close.

**AC.PSHIP1.6:** HIGH-risk files surfaced for human review, OR confirmed none.

### Item 7 — Session close
Update CURRENT_STATE concurrent block; append SESSION_LOG; flip brief; FINAL_SUMMARY noting additive-count, shared-count, and any HIGH-risk files.

**AC.PSHIP1.7:** Close protocol complete.

---

## §5 — Constraints
**may_touch:** all ADDITIVE Panchang paths (new files); `00_ARCHITECTURE/PSHIP_FILE_INVENTORY.md` + `PSHIP_CONFLICT_MAP.md` (new); governance state files; this brief.
**must_not_touch:** any M-classified shared file (that's PSHIP-S2); the Conductor files (00_ARCHITECTURE/CONDUCTOR/ — sealed); the source branch `feature/phase-4c-panchang` (read-only); main directly; corpus.

## §6 — Close checklist
- [ ] 7 ACs PASS
- [ ] Additive files transplanted + committed; shared files untouched
- [ ] PSHIP_FILE_INVENTORY.md + PSHIP_CONFLICT_MAP.md written
- [ ] panchang_engine pytest green
- [ ] HIGH-risk shared files surfaced (or none)
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Wave 1 Panchang module is on feature/phase-4c-panchang; main has NO panchang code (verified 2026-05-20)
- Most Panchang work is additive (new files) — copies clean; ~10 shared files need integration (PSHIP-S2)
- Conductor already merged to main (available in this worktree)
- The 88-commit drift is mostly irrelevant for additive files; only shared files carry conflict risk

## §9 — Canary
The conflict map's risk flags. If a shared file is HIGH risk (main restructured it), do NOT guess the integration — halt for human guidance. Wrong integration of AppShellRail or main.py silently breaks the nav or the sidecar routing.

*End — PSHIP-S1.*
