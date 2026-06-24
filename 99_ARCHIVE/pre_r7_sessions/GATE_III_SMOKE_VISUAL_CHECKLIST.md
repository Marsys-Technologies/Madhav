---
artifact: GATE_III_SMOKE_VISUAL_CHECKLIST
version: 1.0
authored_by: Claude Code Sonnet 4.6 (smoke verification)
date: 2026-05-13
---

# Gate III — Visual Walkthrough Checklist

**Dev server:** run `npm run dev` from `platform/` before starting.
**URL base:** `http://localhost:3000`
**Tick each item [ ] or mark with notes.**

---

## Setup

- [ ] `npm run dev` running (or still running from Phase 2.9)
- [ ] Logged in as `super_admin` user

---

## 1 — Login + Roster landing

**Step:** Open `http://localhost:3000/login`, log in as super_admin.
**Expected:** Redirected to `/dashboard` (Roster page) with one or more chart cards visible.
**Where:** `/login` → `/dashboard`
**Pass/Fail:** [ ]

---

## 2 — Open the consume chat (empty state)

**Step:** Click Abhisek's chart card.
**Expected:** Lands on `/clients/[chartId]/consume`. The chat area is empty — no messages yet. The compose area is visible at the bottom.
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]

---

## 3 — Empty state "By type" tab

**Step:** Observe the empty state in the message area.
**Expected:**
- Two tabs visible: **By type** (active by default) and **By moment**
- "By type" shows 5 query-class groups: Factual, Interpretive, Predictive, Discovery, Holistic
- Each group shows 4–6 suggestions in plain English
- No internal IDs visible anywhere (no "MSR", "CGM", "FORENSIC", etc.)
- Above tabs: a welcoming line (e.g. "Ask anything about your chart.")
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]
**Notes (optional):** ______

---

## 4 — Empty state "By moment" tab

**Step:** Click the "By moment" tab.
**Expected:**
- A brief loading skeleton appears, then 4–6 suggestions grounded in context (they may be somewhat generic if dasha/transit integration is not yet wired, per HANDOFF deferred items — acceptable)
- Suggestions are in plain English, readable
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]

---

## 5 — Click a suggestion fills the input (no auto-submit)

**Step:** Click any suggestion from either tab.
**Expected:** The text fills the composer input box. The query is NOT automatically submitted — you must press Enter or click Send yourself.
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]

---

## 6 — Conversation History Drawer

**Step:** Click the "History" / clock-icon button in the chat header (to the left of the header area or in a dedicated button near the header).
**Expected:**
- A drawer slides in from the left
- Lists any prior conversations with titles + relative timestamps ("2h ago", "Yesterday", etc.)
- On first use: may show empty state ("No prior conversations")
- Has a search input at the top
- Clicking a conversation in the list navigates to it
- Drawer can be closed via ESC or clicking outside
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]

---

## 7 — Submit a query: LiveReasoningCard

**Step:** Type a fresh question (e.g., "What does my current Mahadasha indicate for my life right now?") and submit.
**Expected:**
- A compact card appears ABOVE the answer area showing a pulsing dot + "Thinking…"
- As the pipeline runs, the card text updates to astrological narration: e.g., "Reading the question", "Searching classical sources", "Weighing the most relevant sources", "Reasoning through the question"
- The most-recent thought is visible as a single line; a chevron-down icon is on the right
- Click the card/chevron → full chronological list expands
- Click again → collapses back to most-recent
- **CRITICAL:** NONE of these reasoning texts contain "MSR", "CGM", "pgvector", "cosine", "FORENSIC" or any internal jargon. All in Jyotish vocabulary.
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]
**Notes:** ______

---

## 8 — Answer streams with inline citations

**Step:** Wait for the answer to complete streaming.
**Expected:**
- Answer prose flows naturally below the reasoning card
- Reasoning is woven INTO the prose (no separate "Reasoning:" section)
- Inline `[1]`, `[2]` citation markers appear in the text
- No raw `‹reasoning›`, `‹correction›`, `‹sanskrit›`, `‹out_of_domain›` marker text appears in the visible answer
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]

---

## 9 — Sanskrit term hover tooltips

**Step:** Look for Sanskrit/Jyotish terms in the answer (e.g., "Vimshottari", "Antardasha", "Atmakaraka", "Karaka", "Navamsa"). Hover over them.
**Expected:**
- Sanskrit/Jyotish terms have a dotted underline (or similar subtle visual indicator)
- Hovering shows a small tooltip with:
  - The term name
  - Transliteration (if present)
  - A one-sentence definition
- Keyboard focus (Tab to the term) also triggers the tooltip
**Where:** `/clients/[chartId]/consume` (within the answer text)
**Pass/Fail:** [ ]
**Notes:** If the first query didn't use Sanskrit terms, try "Explain my Vimshottari Mahadasha" explicitly.

---

## 10 — Context cue + Provenance pills after answer

**Step:** After the answer completes, look below the answer.
**Expected:**
- A small context cue chip: "Independent query" or "N prior turn(s) (comprehension only)" — reflecting the planner's decision
- Three provenance pills: `[N models]`, `[N sources]`, `[N signals]`
**Where:** `/clients/[chartId]/consume` (below completed answer)
**Pass/Fail:** [ ]

---

## 11 — Provenance Drawer — Astrological tab

**Step:** Click any of the three provenance pills.
**Expected:**
- A drawer slides in from the right
- Default tab is "Astrological"
- Lists models in the chain with human-readable role labels (e.g., "Planner", "Synthesizer")
- Sources listed with translated labels: e.g., "Astrological Signals" (not "MSR"), "Birth Chart" (not "FORENSIC"), "Concept Graph" (not "CGM")
- **CRITICAL:** No raw internal asset IDs ("MSR", "CGM", "FORENSIC", "UCN", "CDLM", "RM", "LEL") visible in this tab
**Where:** Provenance Drawer → Astrological tab
**Pass/Fail:** [ ]

---

## 12 — Provenance Drawer — Technical tab

**Step:** While the provenance drawer is open, click the "Technical" tab.
**Expected:**
- A compact list of technical metrics: vector scores, latencies (ms), token counts, cache hit indicators
- These CAN show internal technical data — this is where it belongs
- Values are formatted compactly (e.g., "≈0.87 cosine", "12.3s", "2048 tokens")
**Where:** Provenance Drawer → Technical tab
**Pass/Fail:** [ ]

---

## 13 — Close the Provenance Drawer

**Step:** Press ESC or click outside the provenance drawer.
**Expected:** Drawer closes smoothly. Main chat view is restored.
**Pass/Fail:** [ ]

---

## 14 — Factual correction notice

**Step:** Submit a query with a known-wrong chart fact. Since your Sun is in **Capricorn** (10th house), submit:
> "Since my Sun is in Aries, what does that mean for my career?"
**Expected:**
- Response leads with an amber-tinted correction notice: "Your Sun is in Capricorn, not Aries. Proceeding from the corrected placement."
- The correction notice appears ABOVE the main answer body
- The answer then proceeds using the corrected (Capricorn) facts
- No "ask permission" dialog
- Correction is polite but firm
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]

---

## 15 — Out-of-domain banner

**Step:** Submit a clearly non-Jyotish question, e.g.:
> "What's the weather in Bangalore tomorrow?"
**Expected:**
- A calm "outside scope" notice appears above the answer (non-blocking banner)
- The notice text is something like: "This question is outside the Jyotish scope of this instrument — answering briefly."
- The answer is brief (3–5 sentences), in good faith, without refusing or lecturing
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]

---

## 16 — Smart context cue on follow-up

**Step:** After 2–3 turns on the SAME conversation, ask a follow-up that references a prior turn, e.g.:
> "Tell me more about that."
**Expected:**
- Context cue pill shows "1 prior turn (comprehension only)" or similar (mode: 'narrative_context' or 'continuation')
- The planner correctly detected this is a continuation query
**Where:** `/clients/[chartId]/consume`
**Pass/Fail:** [ ]

---

## 17 — Trace drawer still works (Gate II surface — regression check)

**Step:** As super_admin, find the Trace button in the top-right header of the chat shell. Click it.
**Expected:**
- The trace drawer/panel opens exactly as it did before Gate III
- Shows pipeline trace steps for the last query
- No visual regression — Gate III did NOT touch this surface
**Where:** `/clients/[chartId]/consume` → Trace drawer (super_admin only)
**Pass/Fail:** [ ]
**Notes:** If trace drawer looks different or broken, this is a regression — report immediately.

---

## 18 — Conversation persistence across sessions

**Step:** Close the browser tab. Open a new tab and navigate back. Log in again if needed.
**Expected:**
- The history drawer lists the conversations from your previous session
- Clicking a conversation navigates to `/clients/[chartId]/consume/[conversationId]`
- The prior turns load and display correctly
**Where:** `/clients/[chartId]/consume/[conversationId]`
**Pass/Fail:** [ ]

---

## 19 — Conversation auto-titling

**Step:** Start a fresh conversation (no conversationId in URL). Submit your first query.
**Expected:**
- Within ~2 seconds of the first response appearing, the conversation title updates
- Title is 4–7 words, title case, sensible summary of the question
- No trailing punctuation (no "?" or "." at the end of the title)
- The new title appears in the history drawer and (if visible) in the page title or sidebar
**Where:** `/clients/[chartId]/consume` (new conversation)
**Pass/Fail:** [ ]

---

## 20 — Visual baseline: evolution, not redesign

**Step:** Compare the overall app chrome with your memory of the pre-Gate III state (or with a screenshot if you have one).
**Expected:**
- The Roster (dashboard), app header, left sidebar, and overall color palette/typography feel like a Gate III evolution of the existing design
- No jarring visual changes — Gate III enhanced, not redesigned
- The left sidebar is collapsed by default (hover to expand) — per LOCKED decision #1
- The Trace button (super_admin) is in the top-right header — per LOCKED decision #2
- The composer is a fixed-size textarea — per LOCKED decision #3
**Where:** Overall app
**Pass/Fail:** [ ]
**Notes:** ______

---

## After completing the checklist

Return to the Gate III planning conversation with your results. The smoke verification automated phase is complete. The findings report is at `GATE_III_SMOKE_FINDINGS.md`.

**Do NOT merge `feature/gate3-intelligent-chat` to main yet.** Wait for Gate I and Gate II to also complete, then follow the coordinated merge sequence in the macro plan conversation.
