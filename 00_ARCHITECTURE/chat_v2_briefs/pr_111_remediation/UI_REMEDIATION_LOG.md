# Chat V2 UI Gap Remediation Log

**Branch:** `chat-v2/ui-gap-remediation`  
**Base:** `main` (42178331)  
**Date:** 2026-05-20  
**Session:** Triage + remediation of 12 FAIL/INCONCLUSIVE items from `UI_VERIFICATION_localhost_2026-05-20.md`

---

## Phase 0 — Orient

- [x] `git checkout main && git pull --ff-only` — up to date
- [x] Branch `chat-v2/ui-gap-remediation` created
- [x] Chrome MCP connected (about:blank → prod nav redirected to /login)
- [ ] PHASE 1 prod triage — awaiting user login to prod

---

## Phase 1 — Prod Triage

**Purpose:** Separate localhost `.env.local` config issues from real code bugs.  
**Method:** Re-run all 12 failing checks on `https://madhav.marsys.in/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume`.

### Checks under test

| # | Feature | Files | Hypothesis |
|---|---------|-------|------------|
| 9/14 | Citation hover tooltip | NumberedCitation.tsx + CitationCtx | Likely FAIL both envs — missing mount |
| 10 | Slash command menu | SlashCommandMenu + Composer | Likely FAIL — not wired |
| 12 | Export menu | ExportDropdown + R8 flag | Likely PASS prod (flag baked) |
| 13 | Token estimate | useTokenCount + R8 flag | Likely PASS prod (flag baked) |
| 15 | Citation freshness dot | NumberedCitation badge + NEXT_PUBLIC | Likely PASS prod (build-arg baked) |
| 16 | Citation panel auto-open | CitationSidePanel.tsx mount | Likely FAIL both envs — missing mount |
| 18 | Tool-flow post-stream | InlineToolFlow persistence | Likely FAIL both envs — stream state lost |
| 19 | Interactive tables | InteractiveTable + NEXT_PUBLIC | Likely PASS prod (build-arg baked) |
| 20 | Mermaid | MermaidBlock + NEXT_PUBLIC | Likely PASS prod (build-arg baked) |
| 23 | Branch-on-regen | MessageActions + useBranches | Likely FAIL both envs — not wired |
| 24 | Edit-message branch | BranchPicker + edit flow | Likely FAIL both envs — not wired |
| 25 | Keyboard nav j/k/c | useHotkeys handlers | Likely FAIL both envs — handler absent |

### Results

*(to be filled after prod login)*

| # | Feature | Prod Result | Class | Notes |
|---|---------|-------------|-------|-------|
| 9/14 | Citation hover tooltip | TBD | | |
| 10 | Slash command menu | TBD | | |
| 12 | Export menu | TBD | | |
| 13 | Token estimate | TBD | | |
| 15 | Citation freshness dot | TBD | | |
| 16 | Citation panel auto-open | TBD | | |
| 18 | Tool-flow post-stream | TBD | | |
| 19 | Interactive tables | TBD | | |
| 20 | Mermaid | TBD | | |
| 23 | Branch-on-regen | TBD | | |
| 24 | Edit-message branch | TBD | | |
| 25 | Keyboard nav j/k/c | TBD | | |

**Class legend:**
- **A** — Config-only (PASS on prod, was just missing from .env.local — NO code fix needed)
- **B** — Real bug (FAIL on prod → goes on fix list)

---

## Phase 2 — Localhost Fix Environment

*(to be filled after Phase 1)*

---

## Phase 3 — Audit + Fix

*(to be filled after Phase 2)*

---

## Phase 4 — Full Local Re-Verify

*(to be filled after Phase 3)*

---

## Notes / Decisions

- Hard rule: browser observation is the ONLY acceptance signal
- Unit-green + code-present is NOT sufficient — this was the original failure mode
