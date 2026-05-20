---
artifact: CLAUDECODE_BRIEF_PSHIP_S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-20
session_id: PSHIP-S2
session_name: PSHIP-S2 — Integrate the ~10 shared files onto current main
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/panchang-ship
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
predecessor: PSHIP-S1 (additive transplant + conflict map)
---

# CLAUDECODE_BRIEF — PSHIP-S2
## Carefully integrate the shared-file Panchang edits onto main's current versions

PSHIP-S1 transplanted additive files and produced `PSHIP_CONFLICT_MAP.md`. This session applies the Panchang edits to the ~10 shared files — using main's CURRENT version as the base and inserting Panchang's additions per the conflict map. This is the conflict-prone heart of the ship work.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
test -f 00_ARCHITECTURE/PSHIP_CONFLICT_MAP.md
test -f 00_ARCHITECTURE/PSHIP_FILE_INVENTORY.md
test -d platform/src/app/panchang   # additive transplant from S1 present
git log -1 --oneline                 # PSHIP-S1 commit present
```
Halt if S1's outputs aren't present.

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `00_ARCHITECTURE/PSHIP_CONFLICT_MAP.md` (the integration spec from S1 — your work list)
3. For each shared file: read main's CURRENT version (the file on this branch, since it's cut from main) AND the source-branch version (`git show origin/feature/phase-4c-panchang:<path>`)

## §3 — Scope (per-file integration; one commit per file)

Work through `PSHIP_CONFLICT_MAP.md` file by file. For each shared file, integrate Panchang's additions into main's current version. Commit after each so a bad integration is isolated and revertible.

### Item 1 — Nav rail + mobile nav
Integrate the Panchang nav entry into `platform/src/components/shared/AppShellRail.tsx` (the `MoonCrescentIcon` + the `/panchang` NAV_ITEMS entry, roles all three) and `platform/src/components/shared/MobileNavSheet.tsx` (the mobile entry). Use main's CURRENT NAV_ITEMS array structure — if it changed since the merge-base, adapt the insert. **If S1 flagged this HIGH risk, halt for human guidance instead of guessing.**

**AC.PSHIP2.1:** Both nav files integrated; `/panchang` appears in NAV_ITEMS; tsc clean for these files.

### Item 2 — Sidecar router registration
In `platform/python-sidecar/main.py`, add the panchang + muhurat router imports + `app.include_router(..., prefix="/api/compute", dependencies=[Depends(verify_api_key)])` registrations. Match main's current router-registration pattern.

**AC.PSHIP2.2:** Both routers registered at `/api/compute`; sidecar imports clean (`python3 -c "import main"` from python-sidecar dir, or uvicorn boot smoke).

### Item 3 — RetrievalTool registration
In `platform/src/lib/retrieve/index.ts`, add `import { queryPanchanga }` + add it to `RETRIEVAL_TOOLS`. Match main's current array.

**AC.PSHIP2.3:** queryPanchanga registered; introspection lists it; tsc clean.

### Item 4 — Planner prompt
In `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`, add the Panchang few-shot (§4) + the R-TC routing extension (§5). Apply onto main's current prompt version (it may have evolved — preserve main's content, append Panchang's clauses).

**AC.PSHIP2.4:** Panchang few-shot + R-TC clause present; main's existing prompt content intact.

### Item 5 — Capability manifest
In `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`, add the `PANCHANG_DAILY_v1_0` entry (status: CURRENT_ENGINE_DIRECT, runtime_path: engine_direct) per the source branch. Match main's current manifest schema.

**AC.PSHIP2.5:** Manifest entry added; `python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py` and the manifest schema validator both clean (modulo the 2 known pre-existing failures — those are fixed in PSHIP-S3).

### Item 6 — Deploy workflow
In `.github/workflows/deploy.yml`, ensure the sidecar deploy job carries the panchang routers (it should, since they're in main.py now) and add any NEXT_PUBLIC build-args the Panchang UI needs (per the build-arg-baking lesson — check if /panchang uses any NEXT_PUBLIC flags; if not, no build-arg change needed). Apply onto main's current deploy.yml.

**AC.PSHIP2.6:** deploy.yml integrated; no NEXT_PUBLIC flag left unbaked (or confirmed none needed).

### Item 7 — Ask-Madhav context injection (if applicable)
If `platform/src/app/clients/[id]/consume/page.tsx` + `platform/src/lib/synthesis/prompts.ts` were flagged shared in S1's map (the 4C-8 context-injection edits), integrate them onto main's current versions.

**AC.PSHIP2.7:** Context-injection edits integrated, or confirmed not needed.

### Item 8 — CLAUDE.md §E + .geminirules
Add the Phase 4C Panchang workstream entry to `CLAUDE.md §E` onto main's CURRENT CLAUDE.md (which already lists the Conductor as a workstream from the Conductor merge). Bump version. Propagate MP.1 to `.geminirules`. **Critical:** main's §E already has the Conductor entry — ADD Panchang, don't overwrite.

**AC.PSHIP2.8:** §E has both Conductor (from Conductor merge) AND Panchang entries; version bumped; mirror_enforcer exits 0.

### Item 9 — Full test suite + tsc
```bash
cd platform && npx tsc --noEmit && npm test 2>&1 | tail -40
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip/platform/python-sidecar/panchang_engine && python3 -m pytest -q
```
All green. The TS errors that were "expected-until-S2" in PSHIP-S1 should now resolve (query_panchanga wired, etc.).

**AC.PSHIP2.9:** tsc 0 errors; full test suite green; panchang_engine pytest green.

### Item 10 — Session close
CURRENT_STATE; SESSION_LOG; brief flip; FINAL_SUMMARY listing each shared file integrated + its risk level.

**AC.PSHIP2.10:** Close protocol complete.

---

## §4 — Halt discipline (critical)
For ANY shared-file integration where main's current version diverges from what the conflict map assumed (main restructured the file, renamed symbols, changed the array shape), do NOT guess. Emit `HALT_NEEDS_HUMAN` with the specific file + what diverged. A wrong integration here silently breaks production (nav missing, sidecar 404, planner mis-routing). Better to halt and get human guidance than ship a broken integration.

## §5 — Constraints
**may_touch:** only the M-classified shared files from PSHIP_CONFLICT_MAP.md + CLAUDE.md + .geminirules + governance state + this brief.
**must_not_touch:** additive files from S1 (already correct); Conductor files; source branch; corpus; the 2 validator-failure root causes (PSHIP-S3 fixes those — don't touch them here, just tolerate the known EXIT 4s).

## §6 — Close checklist
- [ ] All 10 ACs PASS
- [ ] Every shared file integrated + committed separately
- [ ] tsc 0 errors; full test suite green
- [ ] CLAUDE.md §E has both Conductor + Panchang; mirror clean
- [ ] No HIGH-risk integration guessed (halted instead)
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Base is current main (88 commits newer than the Wave 1 fork). Shared files may have evolved — always integrate onto main's CURRENT version, not the source branch's stale version.
- main's §E already lists the Conductor (from the pre-round Conductor merge) — Panchang ADDS to it.
- The auth bug + 2 validator failures are PSHIP-S3, not here.

## §9 — Canary
Item 9's full test suite. If tests that passed on the source branch now fail on main's base, a shared-file integration is wrong OR main changed an API the Panchang code depends on. Diagnose; halt if it needs human judgment.

*End — PSHIP-S2.*
