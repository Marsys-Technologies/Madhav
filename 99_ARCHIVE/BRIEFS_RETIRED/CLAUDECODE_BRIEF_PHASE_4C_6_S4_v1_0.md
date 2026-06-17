---
artifact: CLAUDECODE_BRIEF_PHASE_4C_6_S4_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-6-S4
session_name: 4C-6-S4 — Muhurat Finder close — E2E tests + Phase 4C.6 close
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
predecessor: 4C-6-S3
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §6 (4C.6 acceptance: 5 events × 30-day range with acharya-grade results)
---

# CLAUDECODE_BRIEF — Phase 4C-6-S4
## Muhurat Finder E2E + 5-event × 30-day acharya review + Phase 4C.6 close

Closing session for Muhurat Finder. E2E integration tests, 5-event acharya-grade review (the master-plan-mandated gate), and Phase 4C.6 close protocol.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f platform/src/app/panchang/components/MuhuratFinderModal.tsx
test -f platform/src/app/panchang/components/MuhuratResultsList.tsx
test -f platform/python-sidecar/panchang_engine/config/muhurat_weights.yaml
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §6 Phase 4C.6 acceptance + §8 AC.4C.6
3. All Muhurat Finder code from S1/S2/S3
4. Brand/visual conventions from /panchang prior sessions

## §3 — Scope (8 items)

### Item 1 — E2E test for Muhurat Finder
Create `platform/tests/integration/test_muhurat_finder_e2e.ts`. Test flow:
1. Spin up sidecar locally
2. Navigate to `/panchang`
3. Click "Find Muhurat" → modal opens
4. Select event = "Vivah", date range = next 60 days
5. Submit → wait for results
6. Assert: 10 windows returned, sorted by star_rating descending, top result has rating ≥ 4★
7. Click first window's "Ask Madhav" → asserts chat opens with pre-loaded prompt

**AC.4C6S4.1:** E2E test PASSES.

### Item 2 — 5-event acharya-grade review (the master plan gate)
Master plan §8 AC.4C.6: "Muhurat Finder returns acharya-grade rankings for 5 event types — Native + senior acharya review."

Document a full review in `platform/tests/visual/4C6_acharya_review.md`. For each of 5 events (Vivah, Griha Pravesh, Vyapara, Yatra, Property Purchase — skipping Mantra Initiation for time):
- 30-day range (a varied stretch of upcoming dates)
- Top 5 results with full breakdown
- Acharya assessment per result: "acharya-grade", "acceptable", or "needs tuning" with brief rationale
- Identify any systematic bias (e.g., "consistently weights Pushya too heavily") and propose a weight adjustment in muhurat_weights.yaml

This is a SEMI-AUTONOMOUS step: the executor produces the review document with provisional acharya verdicts (using LLM reasoning over classical references); the document is then for native + acharya panel review (Phase 4C.6 close human-gates on this).

**AC.4C6S4.2:** Acharya review document complete; 5 events × 5 top results each = 25 windows reviewed with rationale.

### Item 3 — Weight tuning pass (if review surfaces issues)
If the acharya review in Item 2 surfaces a systematic bias (e.g., one event consistently overranks Thursdays), adjust `muhurat_weights.yaml` accordingly. Re-run the affected event's review to verify the adjustment helps without breaking other events.

**AC.4C6S4.3:** If tuning was needed, weight changes documented + before/after rankings shown. If not needed, document "no tuning required."

### Item 4 — Performance regression check
Re-run the latency baseline from 4C-6-S1: `find_muhurat` for 90-day range on a single event. Verify performance hasn't regressed from S1 baseline (~30s cold, expect similar). Document in `platform/tests/perf/4C6_S4_perf.md`.

**AC.4C6S4.4:** Perf within 110% of S1 baseline.

### Item 5 — Documentation pass
Update `platform/python-sidecar/panchang_engine/README.md` to add a Muhurat Finder section. Document:
- The 6 MVP events
- How the YAML weights work
- How to interpret breakdown badges
- Latency expectations
- Acharya review process

**AC.4C6S5.5:** README section added; total Muhurat Finder docs cohesive.

### Item 6 — Phase 4C.6 close protocol
- Update CURRENT_STATE: `4C.6 CLOSED 2026-05-19`; next: 4C-7
- Append SESSION_LOG with 4C-6-S4 atomic entry
- Update Phase 4 master plan §B: 4C.6 row to CLOSED with commit hash
- Author `00_ARCHITECTURE/PHASE_4C_6_CLOSE_v1_0.md` — one-page summary of Muhurat Finder delivery
- Update queue: 4C-6-S4 → passed; 4C-7 next eligible

**AC.4C6S4.6:** Close protocol steps complete.

### Item 7 — Brief flip + FINAL_SUMMARY
Flip this brief to COMPLETE; emit FINAL_SUMMARY.

**AC.4C6S4.7:** Done.

### Item 8 — Acharya review handoff (sub-agent note)
Note in the FINAL_SUMMARY's `notes_for_orchestrator` that the acharya review document (`platform/tests/visual/4C6_acharya_review.md`) is provisional; final acharya validation is a Wave 1 close concern (4C-9). For now, "acharya-grade" verdicts in Item 2 are LLM-derived and should not be treated as final acharya sign-off.

**AC.4C6S4.8:** FINAL_SUMMARY notes this caveat.

---

## §5 — Constraints
**may_touch:** `platform/tests/{integration,visual,perf}/4C6_*`; `platform/python-sidecar/panchang_engine/config/muhurat_weights.yaml` (Item 3 tuning if needed); README; governance state files; `00_ARCHITECTURE/PHASE_4C_6_CLOSE_v1_0.md` (new); this brief.
**must_not_touch:** UI components from S3; muhurat.py logic (Item 3 only edits YAML, never the Python); engine modules; corpus; master plan.

## §6 — Close checklist
- [ ] 8 ACs PASS
- [ ] E2E test PASS
- [ ] Acharya review documented for 5 events
- [ ] Perf baseline maintained
- [ ] Phase 4C.6 close protocol complete
- [ ] FINAL_SUMMARY emitted with acharya-review-pending caveat

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Acharya review verdict in Item 2 is LLM-derived, not final
- Real acharya sign-off is in 4C-9 Wave 1 close (human-gated)
- Weight tuning never touches knockout_penalty (master plan invariant)

## §9 — Canary
The acharya review document. If it surfaces consistent "needs tuning" verdicts across multiple events, the scoring rubric is wrong — halt and report rather than ship.

*End — 4C-6-S4 closes Phase 4C.6.*
