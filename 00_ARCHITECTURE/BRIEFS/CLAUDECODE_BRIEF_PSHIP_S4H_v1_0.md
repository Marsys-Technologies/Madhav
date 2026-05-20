---
artifact: CLAUDECODE_BRIEF_PSHIP_S4H_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-20
session_id: PSHIP-S4H
session_name: PSHIP-S4H — Planner prompt: extend R-PA + add R-PCI + renumber (HUMAN GATE)
executor: Claude Code sub-agent (Conductor) — requires_human_approval BEFORE this entry runs
worktree:
  branch: feature/panchang-ship
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
predecessor: PSHIP-S3H
human_approval_prompt: |
  PSHIP-S3H closed (query-tool reconciled, migration 061 + 5-col cache, SQL tool
  serves all 13 triggers). PSHIP-S4H edits PLANNER_PROMPT_v2_0.md — sensitive
  routing change. Approve to: extend main's R-PA with 13 trigger phrases, add
  R-PCI (context inheritance) verbatim, renumber few-shot 4.25→4.28, leave main's
  R-TC untouched. Reply APPROVE PSHIP-S4H, or request changes.
---

# CLAUDECODE_BRIEF — PSHIP-S4H
## Planner prompt integration — extend R-PA, add R-PCI, renumber (D3/D4/D5) — HUMAN GATE

The most sensitive session: it changes planner routing. Per the approved decisions, this EXTENDS main's R-PA (does not import our colliding R-TC), adds R-PCI, and renumbers the few-shot. Main's R-TC (Transit-Context Enrichment) is left untouched. **The Conductor halts before this entry for native approval.**

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
git log --oneline -6   # PSHIP-S3H commits present
# confirm the SQL tool now serves the new fields (S3H done)
grep -q "choghadiya\|special_yogas" platform/src/lib/retrieve/query_panchanga.ts && echo "SQL tool extended (S3H done)"
```
If the SQL tool wasn't extended in S3H, halt — the planner must not route triggers to a tool that can't serve them.

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md` §3 (routing diff — the 13 phrases + R-PCI text) + §9 D3/D4/D5
3. main's `PLANNER_PROMPT_v2_0.md` — the CURRENT R-PA rule (you extend it) + the CURRENT R-TC rule (you LEAVE UNTOUCHED) + the few-shot section (numbering)
4. our branch's `PLANNER_PROMPT_v2_0.md` R-PCI block (you copy it verbatim) — `git show origin/feature/phase-4c-panchang:00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`

## §3 — Scope (6 items)

### Item 1 — Extend main's R-PA trigger list (D3)
Add these 13 trigger phrases to main's R-PA (Panchanga Anchor) rule — they route to main's SQL query_panchanga (which post-S3H serves all of them):
`rahu kalam`, `yamagandam`, `gulika`, `choghadiya`, `hora`, `brahma muhurta`, `abhijit`, `amrit kalam`, named special yogas (`Sarvartha Siddhi`, `Amrit Siddhi`, `Guru Pushya`, `Ravi Pushya`, `Tripushkar`, `Bhadra`, `Panchaka`), `panchang for today` / `today's panchang` / `panchang for [date]`, and `chandra bala` / `tara bala`.
Integrate INTO main's existing R-PA block — do NOT create a new rule, do NOT import our R-TC label.

**AC.S4H.1:** R-PA trigger list extended with the 13 phrases; rule structure preserved.

### Item 2 — Leave main's R-TC untouched
Confirm main's R-TC (Transit-Context Enrichment) is unchanged. Our branch's R-TC (panchang routing) is DROPPED — its triggers are now in the extended R-PA (Item 1). Do not touch main's R-TC text.

**AC.S4H.2:** main's R-TC byte-identical to its pre-session state; our R-TC label not present.

### Item 3 — Add R-PCI verbatim (D4)
Copy the R-PCI (Panchang Context Inheritance) rule from our branch verbatim: when a `<panchang_context>` block is present in the user query (injected by /panchang AskMadhavLink), skip the query_panchanga tool call, use the injected context; R-PCI priority > R-PA for same date/location; exceptions for different date / explicit re-query / truncated context. This is pure-additive (no main equivalent).

**AC.S4H.3:** R-PCI rule present verbatim; placed logically near R-PA.

### Item 4 — Renumber the few-shot (D5)
Renumber our Panchang few-shot example from `4.25` to follow main's current sequence (count main's examples; the spec said `4.28` — verify the exact next number). Update the §4 example count + any cross-references.

**AC.S4H.4:** Few-shot renumbered to the correct next slot; §4 count + cross-refs consistent.

### Item 5 — Planner probe set (the gate)
Build/extend a probe set and test the routing:
- The 13 new trigger phrases → route to query_panchanga (main's SQL tool), priority 1
- main's R-TC behavior on transit-context queries → UNCHANGED
- A `<panchang_context>`-bearing query → R-PCI fires, NO query_panchanga call
- No false positives (a pure ephemeris query doesn't fire R-PA)
Run it: all probes pass.

**AC.S4H.5:** Planner probe set 100% pass; main's R-TC behavior unchanged; R-PCI verified.

### Item 6 — Session close
CURRENT_STATE; SESSION_LOG; brief flip; FINAL_SUMMARY noting the R-PA extension + R-PCI + renumber + probe results.

**AC.S4H.6:** Close protocol complete.

---

## §4 — Human gate
The Conductor halts before spawning this sub-agent (requires_human_approval). Native reviews the exact 13 trigger phrases + the R-PCI text + the renumbering, then approves. Only then does the sub-agent run. This is because planner-routing changes affect every chat query and are the highest-blast-radius edit in the ship round.

## §5 — Constraints
**may_touch:** `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` (R-PA extension + R-PCI addition + few-shot renumber ONLY); the planner probe set + test; governance state; this brief.
**must_not_touch:** main's R-TC rule text; the SQL query_panchanga.ts (S3H sealed it); migration/bootstrap (S3H); the UI/engine; the nav/deploy/CLAUDE.md (S2H); Conductor; corpus.

## §6 — Close checklist
- [ ] 6 ACs PASS
- [ ] R-PA extended with 13 phrases; main's R-TC untouched; our R-TC label gone
- [ ] R-PCI added verbatim
- [ ] Few-shot renumbered correctly
- [ ] Planner probe set 100% pass (incl. main R-TC unchanged + R-PCI fires)
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- D3: extend main's R-PA (NOT import our R-TC). main's R-TC = Transit-Context Enrichment, stays. Our R-TC label dropped.
- D4: R-PCI verbatim from our branch (context-inheritance skip). Pairs with S2H's context-injection edits.
- D5: 4.25 → 4.28 (verify exact number against main's current example count).
- The 13 triggers are only safe to route to the SQL tool BECAUSE S3H extended the cache to serve them (5 columns). Confirm S3H done in pre-flight.

## §9 — Canary
The planner probe set. The two highest-risk failure modes: (1) the R-PA extension over-fires (a pure ephemeris query wrongly pulls query_panchanga) — false positive; (2) main's R-TC behavior changed (regression on the existing transit-context routing). Both must be clean. If either fails, halt — a mis-routing planner degrades every chat answer.

*End — PSHIP-S4H. Human-gated planner change.*
