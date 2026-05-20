---
artifact: CLAUDECODE_BRIEF_PSHIP_S4_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-20
session_id: PSHIP-S4
session_name: PSHIP-S4 — Pre-merge verification + PR prep + ship-readiness report
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/panchang-ship
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
predecessor: PSHIP-S3 (auth + validator fixes)
note: This is the LAST autonomous session. The merge + deploy after it are HUMAN steps.
---

# CLAUDECODE_BRIEF — PSHIP-S4
## Verify ship-readiness, run a live local /panchang smoke, prep the PR — stop at merge

The final autonomous session of the ship round. Proves the integrated module works end-to-end (including a live local /panchang render with the auth fix), produces a ship-readiness report, and preps the PR. Does NOT merge or deploy — those are human checkpoints.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
git log --oneline -8   # PSHIP-S1/S2/S3 commits present
cd platform && npx tsc --noEmit | tail -3   # 0 errors
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `00_ARCHITECTURE/PSHIP_FILE_INVENTORY.md` + `PSHIP_CONFLICT_MAP.md` (what was transplanted + integrated)
3. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` §8 (the original acceptance criteria — verify the shipped module still meets them)

## §3 — Scope (9 items)

### Item 1 — Full quality gate
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
cd platform && npx tsc --noEmit && npm run lint 2>&1 | tail -10 && npm test 2>&1 | tail -40
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip/platform/python-sidecar/panchang_engine && python3 -m pytest -q
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
python3 platform/scripts/governance/schema_validator.py
python3 platform/scripts/governance/drift_detector.py
python3 platform/scripts/governance/mirror_enforcer.py
```
Everything green/clean.

**AC.PSHIP4.1:** tsc 0, lint clean, all tests green, all 3 validators clean.

### Item 2 — Live local /panchang smoke (the verification that failed before)
Start the sidecar from this worktree keyless, start Next.js, and confirm `/panchang` renders with LIVE data (not the HTTP 500 we hit on the Wave 1 branch). Specifically verify the auth fix from PSHIP-S3 works:
```bash
# Terminal A: sidecar
cd platform/python-sidecar && pip install -r requirements.txt --break-system-packages 2>&1 | tail -2
PYTHON_SIDECAR_API_KEY=ship-test uvicorn main:app --port 8000 &
# Note: key SET this time (ship-test) to prove the x-api-key fix actually works under enforcement
```
Then call the panchang endpoint THROUGH the app's path with the key enforced. If the auth fix is correct, data returns; if the header is still missing, it 401s — which would mean PSHIP-S3 didn't fully fix it (halt + report).

Capture a confirmation (the JSON response or a screenshot-equivalent log) into `00_ARCHITECTURE/PSHIP_SMOKE_REPORT.md`.

**AC.PSHIP4.2:** /panchang data fetch succeeds with the sidecar API key ENFORCED (proves the auth fix). Documented in PSHIP_SMOKE_REPORT.md.

### Item 3 — Acceptance-criteria audit against master plan §8
Walk the original Phase 4C acceptance criteria (AC.4C.1–AC.4C.9 from the master plan §8) and confirm each is still met in the integrated build. Note any that are DEFERRED (e.g., AC.4C.2 cache coverage — deferred to a later round; AC.4C.6 acharya review — LLM-derived, real review pending).

**AC.PSHIP4.3:** AC audit table in PSHIP_SMOKE_REPORT.md — each original AC marked MET / DEFERRED with note.

### Item 4 — Diff stat + change summary
Produce the merge diff stat: `git diff main...feature/panchang-ship --stat | tail -30` and a human-readable summary of what the PR adds (files, LOC, the additive vs integrated split).

**AC.PSHIP4.4:** Change summary written.

### Item 5 — Known-deferred inventory
List what is explicitly NOT in this PR (so the reviewer knows): 4C-2 SQL cache (engine-direct only), v2 muhurat (finer windows + full event set), real acharya validation. Reference the followups doc.

**AC.PSHIP4.5:** Deferred-inventory section in the report.

### Item 6 — Author the ship-readiness report
Consolidate Items 1–5 into `00_ARCHITECTURE/PSHIP_SHIP_READINESS_v1_0.md`: quality gate results, live smoke proof, AC audit, diff stat, deferred inventory, and a clear GO / NO-GO recommendation for the human merge.

**AC.PSHIP4.6:** Ship-readiness report complete with GO/NO-GO.

### Item 7 — PR body draft
Write the PR description to `00_ARCHITECTURE/PSHIP_PR_BODY.md` (ready for the human to paste when opening the PR): what it ships, the additive/integrated split, the auth fix, the deferred items, the test/validator state, reviewer = native.

**AC.PSHIP4.7:** PR body drafted.

### Item 8 — Final commit + push
```bash
git add -A && git commit -m "PSHIP-S4: ship-readiness verification + PR prep"
git push -u origin feature/panchang-ship
```

**AC.PSHIP4.8:** Branch pushed; ready for human PR creation.

### Item 9 — Session close + HUMAN HANDOFF
CURRENT_STATE; SESSION_LOG; flip brief; FINAL_SUMMARY. The FINAL_SUMMARY must clearly state: **autonomous round COMPLETE; the merge and deploy are HUMAN steps — see PSHIP_SHIP_READINESS_v1_0.md GO/NO-GO and PSHIP_PR_BODY.md.**

**AC.PSHIP4.9:** Close protocol complete; human handoff explicit.

---

## §4 — Stop discipline
This session does NOT merge to main and does NOT deploy. It ends at "pushed + PR-ready + GO recommendation." If the live smoke (Item 2) fails or any AC audit reveals a real gap, the GO/NO-GO recommendation is NO-GO with the specific blocker, and the session halts rather than papering over it.

## §5 — Constraints
**may_touch:** `00_ARCHITECTURE/PSHIP_SMOKE_REPORT.md`, `PSHIP_SHIP_READINESS_v1_0.md`, `PSHIP_PR_BODY.md` (all new); governance state; this brief. May start/stop local sidecar + dev server for the smoke (ephemeral).
**must_not_touch:** application code (S1–S3 sealed it — this session only verifies); main; the Conductor files; corpus. NO merge, NO deploy, NO force-push.

## §6 — Close checklist
- [ ] 9 ACs PASS
- [ ] Quality gate fully green
- [ ] Live /panchang smoke PASS with API key ENFORCED (auth fix proven)
- [ ] AC audit vs master plan §8 complete
- [ ] Ship-readiness report with GO/NO-GO
- [ ] PR body drafted; branch pushed
- [ ] FINAL_SUMMARY states merge+deploy are human steps

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- This is the round's final autonomous session. After it: human merges the PR + deploys (web + sidecar) + verifies prod.
- The live smoke MUST run with the sidecar API key ENFORCED (not keyless) — that's the only way to prove PSHIP-S3's auth fix actually works. A keyless smoke would pass even with the bug present (the Wave 1 mistake).
- Deferred (NOT this round): 4C-2 cache, v2 muhurat, acharya validation.

## §9 — Canary
Item 2's key-enforced smoke. If /panchang data fetches succeed with PYTHON_SIDECAR_API_KEY set, the auth fix is real and prod will work. If it 401s, PSHIP-S3's fix was incomplete — NO-GO, halt, report which path still drops the key.

*End — PSHIP-S4. Last autonomous session of the ship round.*
