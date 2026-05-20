---
artifact: CLAUDECODE_BRIEF_PSHIP_S5H_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-20
session_id: PSHIP-S5H
session_name: PSHIP-S5H — Verification: key-enforced smoke + planner probe + GO/NO-GO + PR prep
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/panchang-ship
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
predecessor: PSHIP-S4H (planner integration, human-approved)
note: LAST autonomous session. PSHIP-S6H (merge + deploy) is HUMAN.
---

# CLAUDECODE_BRIEF — PSHIP-S5H
## Prove the hybrid works end-to-end (both paths), GO/NO-GO, prep the PR — stop at merge

Final autonomous session. Verifies BOTH panchanga paths work: the UI path (live sidecar engine, key-enforced) and the planner path (main's SQL tool over the now-5-column cache). Produces a GO/NO-GO and preps the PR. Does NOT merge or deploy — that's PSHIP-S6H (human).

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
git log --oneline -10   # PSHIP-S2H/S3H/S4H commits present
cd platform && npx tsc --noEmit | tail -3   # 0 errors
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md` §9 (the 6 decisions — verify each landed)
3. `00_ARCHITECTURE/PSHIP_S3H_PARITY.md` (SQL-tool-vs-engine parity from S3H)
4. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` §8 (original acceptance criteria)

## §3 — Scope (9 items)

### Item 1 — Full quality gate
```bash
cd platform && npx tsc --noEmit && npm run lint 2>&1 | tail -10 && npm test 2>&1 | tail -40
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip/platform/python-sidecar/panchang_engine && python3 -m pytest -q
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
python3 platform/scripts/governance/schema_validator.py
python3 platform/scripts/governance/drift_detector.py
python3 platform/scripts/governance/mirror_enforcer.py
```
All green/clean.

**AC.S5H.1:** tsc 0, lint clean, all tests green, validators clean.

### Item 2 — UI path smoke (key-ENFORCED)
Start the sidecar with the API key SET (`PYTHON_SIDECAR_API_KEY=ship-test`), start Next.js, confirm `/panchang` renders with LIVE data. This proves the BUG-1 auth fix (S3H Item 9) works under enforcement — the Wave 1 mistake was smoking keyless. Capture the result to `PSHIP_S5H_SMOKE.md`.

**AC.S5H.2:** /panchang renders with sidecar key ENFORCED — full data (5 angas, timings, special yogas, choghadiya, hora, Muhurat Finder). Auth fix proven.

### Item 3 — Planner path smoke (the hybrid's other half)
Verify the planner path: run the planner probe set from S4H + confirm a chat query like "what's the rahu kalam and is there a special yoga today?" routes to main's SQL query_panchanga (R-PA), and the SQL tool returns the new 5-column data (special yogas, rahu kalam). This proves the cache extension (migration 061) + R-PA extension work together.

**AC.S5H.3:** Planner routes the 13-trigger queries to the SQL tool; tool returns the new fields; documented in PSHIP_S5H_SMOKE.md.

### Item 4 — Decision-landing audit
Confirm each of the 6 approved decisions actually landed: D1 (Option H structure), D2 (migration 061, 5 cols), D3 (R-PA extended, main R-TC untouched), D4 (R-PCI present), D5 (few-shot renumbered), D6 (only main's query_panchanga in RETRIEVAL_TOOLS). Table it.

**AC.S5H.4:** All 6 decisions confirmed landed (or any gap flagged → NO-GO).

### Item 5 — AC audit vs master plan §8
Walk the original Phase 4C acceptance criteria; mark MET / DEFERRED. Note that AC.4C.2 (cache coverage) is now MET via main's panchanga_daily + migration 061; AC.4C.6 (acharya review) remains LLM-derived (real review pending).

**AC.S5H.5:** AC audit table complete.

### Item 6 — Bootstrap-population status
State whether migration 061's bootstrap actually populated the 73K rows (S3H Item 5) or was DEFERRED. If deferred, the GO recommendation must flag that the prod deploy (S6H) MUST run the bootstrap, else the SQL tool returns null for the new columns until then.

**AC.S5H.6:** Bootstrap status explicit in the report + carried into S6H deploy steps.

### Item 7 — Ship-readiness report + diff stat
Author `00_ARCHITECTURE/PSHIP_SHIP_READINESS_H_v1_0.md`: quality gate, both-path smoke proofs, decision-landing audit, AC audit, bootstrap status, `git diff main...feature/panchang-ship --stat` summary, and a clear GO / NO-GO.

**AC.S5H.7:** Ship-readiness report with GO/NO-GO.

### Item 8 — PR body + push
Write `00_ARCHITECTURE/PSHIP_PR_BODY_H.md` (the hybrid story: keeps main's SQL tool + cache, extends to 5 cols, adds UI/Muhurat/iCal/Ask-Madhav net-new, R-PA extended, R-PCI added). Then:
```bash
git add -A && git commit -m "PSHIP-S5H: ship-readiness verification + PR prep (hybrid)"
git push origin feature/panchang-ship
```

**AC.S5H.8:** PR body drafted; branch pushed.

### Item 9 — Session close + HUMAN HANDOFF
CURRENT_STATE; SESSION_LOG; flip brief; FINAL_SUMMARY stating: **autonomous round COMPLETE; PSHIP-S6H (merge + deploy + prod bootstrap) is HUMAN — see PSHIP_SHIP_READINESS_H GO/NO-GO + PSHIP_PR_BODY_H + the deploy steps including the migration-061 bootstrap.**

**AC.S5H.9:** Close protocol complete; human handoff explicit.

---

## §4 — Stop discipline
No merge, no deploy. Ends at "pushed + PR-ready + GO". If either path smoke fails (UI 401s under key enforcement → auth fix incomplete; or planner mis-routes / SQL tool returns null for new columns → cache/extension gap), the recommendation is NO-GO with the specific blocker, and the session halts.

## §5 — Constraints
**may_touch:** `PSHIP_S5H_SMOKE.md`, `PSHIP_SHIP_READINESS_H_v1_0.md`, `PSHIP_PR_BODY_H.md` (new); governance state; this brief. May start/stop local sidecar + Next.js for smokes (ephemeral).
**must_not_touch:** application code (S2H/S3H/S4H sealed it — this session only verifies); main; Conductor; corpus. NO merge/deploy/force-push.

## §6 — Close checklist
- [ ] 9 ACs PASS
- [ ] Quality gate green
- [ ] UI path smoke PASS with API key ENFORCED (auth fix proven)
- [ ] Planner path smoke PASS (R-PA routes 13 triggers; SQL tool returns 5-col data)
- [ ] All 6 decisions confirmed landed
- [ ] Bootstrap status explicit (populated or deferred-to-S6H)
- [ ] Ship-readiness GO/NO-GO + PR body; branch pushed
- [ ] FINAL_SUMMARY states S6H is human

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Two paths to verify: UI (live sidecar, key-enforced) + planner (main's SQL tool over 5-col cache). BOTH must work — that's the hybrid.
- The key-enforced UI smoke is mandatory (keyless would mask BUG 1, the Wave 1 mistake).
- If the bootstrap was deferred in S3H, the SQL tool returns null for the new columns until S6H runs it on prod — flag loudly in the GO/NO-GO.
- S6H (merge + deploy + prod migration 061 + bootstrap) is human.

## §9 — Canary
The two-path smoke (Items 2+3). The UI path proves the live engine + auth fix; the planner path proves the cache extension + R-PA routing. If either is red, the hybrid isn't actually working end-to-end → NO-GO, halt, report which path.

*End — PSHIP-S5H. Last autonomous session.*
