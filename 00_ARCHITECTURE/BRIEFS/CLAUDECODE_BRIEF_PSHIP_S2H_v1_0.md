---
artifact: CLAUDECODE_BRIEF_PSHIP_S2H_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-20
session_id: PSHIP-S2H
session_name: PSHIP-S2H — Net-new + non-planner shared-file integration (hybrid Option H)
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/panchang-ship
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
predecessor: PRECON-S1 (reconciliation spec approved — Option H, 6 decisions, 5-col cache)
supersedes: PSHIP-S2 (the pre-reconciliation shared-file brief)
---

# CLAUDECODE_BRIEF — PSHIP-S2H
## Integrate net-new files + non-planner shared files onto main (Option H hybrid)

Per the approved reconciliation (Option H): main's SQL `query_panchanga` + `panchanga_daily` cache + R-TC stay. We add our net-new layer + integrate the shared files that DON'T involve the planner prompt (S4H) or the query-tool collision (S3H). PSHIP-S1 already transplanted the 132 additive files; this session integrates the non-planner shared files onto main's current versions.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
git branch --show-current   # feature/panchang-ship
test -f 00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md   # approved spec present
test -f 00_ARCHITECTURE/PSHIP_CONFLICT_MAP.md
test -d platform/src/app/panchang   # PSHIP-S1 additive transplant present
git show origin/main:platform/src/lib/retrieve/query_panchanga.ts >/dev/null 2>&1 && echo "main's SQL query_panchanga confirmed"
```
Halt if the approved spec or S1's transplant is missing.

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md` §6 (recommendation) + §7 (re-scoped plan) + §9 (the 6 approved decisions)
3. `00_ARCHITECTURE/PSHIP_CONFLICT_MAP.md` (the 22 shared files; this session does the NON-planner, NON-query-tool subset)
4. main's current versions of each shared file you integrate (read on this branch — it's cut from main)

## §3 — Scope (8 items)

### Item 1 — Confirm additive transplant intact
Verify PSHIP-S1's 132 additive files are present and unmodified. Re-run engine tests: `cd platform/python-sidecar/panchang_engine && python3 -m pytest -q` → expect 230/230.

**AC.S2H.1:** Additive transplant intact; engine tests green.

### Item 2 — Nav rail + mobile nav
Add the `/panchang` entry to `platform/src/components/shared/AppShellRail.tsx` (MoonCrescentIcon + NAV_ITEMS entry, roles all three) and `MobileNavSheet.tsx`. Integrate onto main's CURRENT NAV_ITEMS structure. **Halt if main restructured the nav array** (HIGH-risk per S1's map).

**AC.S2H.2:** Both nav files have the /panchang entry; tsc clean.

### Item 3 — Sidecar router registration (the UI's live-engine path)
In `platform/python-sidecar/main.py`, register our `routers/panchang.py` + `routers/muhurat.py` at `/api/compute` with `verify_api_key`. These serve the `/panchang` UI's live-engine path (NOT the planner — planner uses main's SQL tool per D6). Match main's current router-registration pattern.

**AC.S2H.3:** Both routers registered; sidecar boots clean (`uvicorn main:app` smoke or `python3 -c "import main"`).

### Item 4 — Ask-Madhav context injection (shared files)
Integrate the 4C-8 context-injection edits onto main's current `platform/src/app/clients/[id]/consume/page.tsx` + `platform/src/lib/synthesis/prompts.ts` (the `<panchang_context>` block handling). This pairs with R-PCI (added in S4H). If main restructured these files, halt.

**AC.S2H.4:** Context-injection edits integrated onto main's versions; tsc clean.

### Item 5 — deploy.yml
Ensure the `deploy-sidecar` job carries our new routers (they're in main.py now) and add any NEXT_PUBLIC build-args the /panchang UI needs (check; if none, no build-arg change). Integrate onto main's current deploy.yml.

**AC.S2H.5:** deploy.yml integrated; no unbaked NEXT_PUBLIC flag (or confirmed none).

### Item 6 — CLAUDE.md §E + .geminirules
Add the Phase 4C Panchang workstream entry to `CLAUDE.md §E` onto main's CURRENT version (which already lists the Conductor). Bump version. Propagate MP.1 to `.geminirules`. ADD Panchang; don't overwrite the Conductor entry.

**AC.S2H.6:** §E has Conductor + Panchang; version bumped; mirror_enforcer exits 0.

### Item 7 — Full test + tsc sweep (minus planner + query-tool)
```bash
cd platform && npx tsc --noEmit && npm test 2>&1 | tail -30
```
Note: query_panchanga.ts collision is NOT resolved yet (S3H) and planner is NOT touched (S4H), so some routing/tool tests may still be in their main-default state — that's expected. Document any test that's red specifically because of the not-yet-done S3H/S4H work as EXPECTED-until-S3H/S4H.

**AC.S2H.7:** tsc clean for the integrated shared files; tests green except documented expected-until-S3H/S4H.

### Item 8 — Session close
CURRENT_STATE; SESSION_LOG; brief flip; FINAL_SUMMARY listing each shared file integrated + risk level + any halt.

**AC.S2H.8:** Close protocol complete.

---

## §4 — Halt discipline
This session does NOT touch: the planner prompt (`PLANNER_PROMPT_v2_0.md` — S4H), the `query_panchanga.ts` collision or `RETRIEVAL_TOOLS` (S3H), or migration 061 (S3H). If a shared-file integration is HIGH-risk (main restructured it), halt with the specific file rather than guess.

## §5 — Constraints
**may_touch:** AppShellRail.tsx, MobileNavSheet.tsx, sidecar main.py (router registration), consume page + synthesis prompts (context-injection), deploy.yml, CLAUDE.md §E, .geminirules, governance state, this brief.
**must_not_touch:** `PLANNER_PROMPT_v2_0.md` (S4H); `query_panchanga.ts` + `retrieve/index.ts` (S3H); migrations (S3H); main's SQL query_panchanga; the additive transplant (already correct); Conductor files; corpus.

## §6 — Close checklist
- [ ] 8 ACs PASS
- [ ] Engine tests 230/230; integrated-file tsc clean
- [ ] Nav, sidecar routers, context-injection, deploy.yml, CLAUDE.md §E all integrated
- [ ] No HIGH-risk integration guessed (halted instead)
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Option H approved: main's SQL tool + cache + R-TC stay; we add net-new + non-planner shared files here, query-tool/schema in S3H, planner in S4H.
- Our sidecar routers (panchang + muhurat) serve the UI's live path — that's why they register in main.py even though the planner uses main's SQL tool.
- query_panchanga.ts collision is S3H's job — do NOT register our version here.

## §9 — Canary
Item 7's test sweep. Reds must be cleanly attributable to not-yet-done S3H/S4H work. Any OTHER red means a shared-file integration broke something — halt and diagnose.

*End — PSHIP-S2H.*
