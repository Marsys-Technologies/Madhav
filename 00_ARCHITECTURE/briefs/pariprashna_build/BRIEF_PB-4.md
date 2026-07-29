---
artifact: BRIEF_PB-4
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN) — WRITE WAVE, CUTOVER
campaign: PB — Paripraśna Build
wave: PB-4 PŪRṆATĀ — completion & cutover
version: 1.0
status: FROZEN — opens when PB-3 closes green (or ship-degraded per Pratinidhi MEMO)
authored_by: Claude (Cowork) 2026-07-28
governing: CAMPAIGN_PB_MASTER_BRIEF_v1_0.md (its §2 amends the house protocols; the Pratinidhi replaces every human gate)
design_authority: >
  Design plan v0.3: §5.3 (empty state, the Seal), §5.7 (motion constitution, SND-1),
  §7.5 (error copy), §7.8 (edge-state table), §9 (responsive/a11y checklist), §10.1
  (sidebar), §11 (AC-1..AC-16), §3.2 (arrival line) — plus target architecture D-02
  (consult/consume retired) and PG-1 Lane C-3 dead-code census (deletion warrant + order).
gate: §G — 13 assertions on the DEPLOYED DEFAULT route + final proof + anti-gaming pass
blocks: CAMPAIGN CLOSE.
---

# PB-4 — PŪRṆATĀ: completion & cutover

## §0 — Objective

The surface completes and becomes the only door. History sidebar, empty-state
invocation + arrival line, the Seal, the full edge-state lexicon, mobile + a11y to the
§9 bar — then `/clients/[id]/pariprashna` becomes the DEFAULT, `consult`/`consume`
retire per D-02 with redirects, dead chat trees are deleted per the PG-1 census, the
flag is removed, and a post-deploy smoke test guards the route forever (the PF-1 F-3
fold — closing the detection gap that let the engine sit dead for weeks).

**Cutover discipline is the wave's spine:** flag-flip to default → seven consecutive
green smoke runs → retirement commit. Rollback is the flag until retirement; after
retirement, the rollback pin. **PC-3 expires THIS wave only** — the single wave
authorized to touch the consult tree, and only to retire it.

## §1 — Lifecycle, state, git

Per master brief §1/§4. Branch `pb/4/<lane>`, worktree `Madhav-pb-4-<lane>`, state
shards `briefs/pariprashna_build/state/PB4_LANE_<lane>.md`, index `STATE_PB-4.md`,
commits `chore(pb-4/<lane>): … [PB-BOT]`. Verification law per master §2.2, verbatim.
No schema work expected; Migration guard on call if a lane surprises.

## FROZEN §F1 — Lane map

### Lane F-1 — history sidebar (sonnet/med)

Per §10.1 + layout ruling 3 + the workspace mockup SVG: left rail, collapsible to
icons (remembered per user); threads grouped by chart then recency; rows = Inter 13
auto-generated title (editable), chart glyph, relative time, active tick; streaming
thread shows a quiet gold dot. Selection swaps the route in the shell — never a reload.
Delete is archival; hard delete native-only, confirmed in the instrument's register.
Search deferred if no server index exists — record, don't stub-fake.
**Acceptance:** C-2 battery unaffected (zero added layout shift); collapse state
persists; deep links `/pariprashna/t/{id}#turn-{n}` resolve from rows.
```
may_touch: platform/src/components/pariprashna/** ·
           platform/src/app/clients/[id]/pariprashna/** ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane F-2 — empty state, arrival line, the Seal (sonnet/med)

- **Empty state — the invocation** (§5.3): the ecliptic hairline (`--rule`, scaleX 0→1
  from center, 400ms; instant under reduced motion) at ~38% height; "Ask the chart."
  Cormorant 28 ivory; chart pin; focused composer; three chart-aware example pills
  (OD-7: engine-generated, curated fallback if quality embarrasses — Pratinidhi rules,
  MEMO'd). No star fields, no wheels.
- **Arrival line** (§3.2, J2, AC-16): one Inter 12.5 `--ink-dim` line on thread open —
  daśā year + open windows (PB-3 ledger feeds the count). Chrome, not transcript; once
  per session; **derived from L1/Kāla truth — NEVER model-composed** (gate 7 wire-taps).
- **The Seal** (§5.3 settling): six steps strictly ordered — tail commits · caret fades
  120ms · band flips in place · dock grounding settles · closing rule draws 400ms
  scaleX-from-center · composer restores. Reduced motion: instant, same order.
- **Motion constitution as tokens** (§5.7) + CI audit — every animation cites its
  constitution slot or is cut. SND-1 settle tone: one soft note, off by default,
  per-user; deleted without ceremony if it reads as notification.
**Acceptance:** AC-16 arrival-line + Seal-order assertions green; motion audit lists
every animation with its slot.
```
may_touch: platform/src/components/pariprashna/** ·
           platform/src/app/clients/[id]/pariprashna/** ·
           platform/src/lib/pariprashna/** ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane F-3 — failure & reconnect UX (sonnet/med)

Complete the §7.8 edge-state table — every row a lexicon entry with a fixture: `A
QUESTION FIRST` · `BEFORE I ANSWER —` · `THE CHART HAS BEEN REBUILT` ·
`RECONNECTING…`/`RESUMED — NOTHING LOST` · `THE MODEL IS BUSY — RETRYING` · `TAKING
LONGER THAN USUAL…` · `SERVED WITHIN LIMITS — n OF m STEPS` (+ ribbon) · `STOPPED —
KEPT WHAT ARRIVED` · `WILL SWITCH TO ⟨model⟩ NEXT TURN` · `IN LINE — STARTS IN A
MOMENT`. Failure bands + copy verbatim from §7.5 (its voice rules bind). **Adopt the
dead `classify-error.ts` taxonomy** (PG1-C3-0001: built, never wired) into the route's
error events — adopt, don't rewrite; if unsalvageable, reimplement to the same taxonomy
and let F-5's sweep delete the corpse. Auto-retry per §5.9.
**Acceptance:** one fixture per edge state rendering its exact lexicon copy; taxonomy
unit-mapped to §7.5; J6 10s/45s drop scripts green (AC-10).
```
may_touch: platform/src/lib/pariprashna/** ·
           platform/src/app/api/pariprashna/** ·
           platform/src/components/pariprashna/** ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane F-4 — mobile + a11y hardening (sonnet/med; fan-out haiku/low)

To the plan §9 checklist, item by item — normative, not advisory: tap-first citations
everywhere (chip tap → bottom sheet; ≥40×40 hit areas; zero hover-only affordances);
every displacing disclosure a sheet on mobile; composer pinned via `visualViewport`
(never 100vh guesses); transcript resizes, focus never stolen; overscroll containment;
Stop ≥44px; aria-live discipline (ONE polite region = the volatile tail; committed
blocks LEAVE it at commit; band announcements throttled ≥5s; ticks aria-hidden; settle
announces one summary; gap ribbon `role="note"`, never `alert`); §9.3 structure list;
contrast + reduced-motion + `prefers-contrast: more` + 200% zoom + `lang="sa-Latn"`.
**Acceptance:** G-MOBILE at 390×844 green incl. keyboard-open streaming; axe 0
critical/serious on every §5.3 state fixture (AC-6); VoiceOver + NVDA smoke for J1 + J6
executed and documented (§9.3 harness).
```
may_touch: platform/src/components/pariprashna/** ·
           platform/src/app/clients/[id]/pariprashna/** ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane F-5 — CUTOVER ⭐ (opus/high — the irreversible lane; SEQUENCED LAST)

Strict order, each step its own pushed commit:

1. **Default flip:** `/clients/[id]/pariprashna` becomes the default — dashboard
   actions, global nav, every entry point. Flag ON for all (= rollback lever).
2. **Hold:** SEVEN consecutive green post-deploy smoke runs (F-6's test) on the
   default; counter resets on any red (W-1); seven runs are seven runs.
3. **Retirement commit** (D-02): `consult` + `consume` retired — `/api/chat/consult`
   and old UI routes redirect (308 route→route; API callers 410 + pointer per B-4);
   **old chat trees deleted per the B-3-refreshed PG-1 C-3 census in dependency order**
   (leaf-first: `AdaptiveMessageList` → `VirtualizedMessageList` → `useChatSession` →
   `retrieval/adapters/agentic_loop/` → rest). Legacy `parts_json` path removed.
4. **Flag removal:** `PARIPRASHNA_ENABLED` deleted; from here rollback = git revert +
   rollback pin (W-3).
**Acceptance:** verifier reviews the retirement diff line-by-line against the refreshed
census (W-2); redirect assertions green; build green each step.
```
may_touch: platform/src/app/api/chat/** (retirement only — PC-3 expires here)
           · platform/src/components/consume/** · platform/src/components/chat*/**
           · platform/src/lib/** (dead-cluster deletion per census only) ·
           platform/src/app/clients/[id]/** (default routing) · next.config/
           middleware (redirects) · platform/tests/pariprashna/** ·
           briefs/pariprashna_build/**
```

### Lane F-6 — chat smoke in CI (sonnet/med) — the PF-1 F-3 fold; MERGES FIRST

Post-deploy CI step against the DEPLOYED app, targeting the pariprashna route:
authenticate → POST one fixed question for chart `482012f1-…` → assert **HTTP 200** +
non-empty streamed body + **a persisted canonical `message_parts` row** +
**zero-internal-id grep on every streamed byte** (the AC-4 regex suite). Fails the
deploy loudly. Deterministic per PF-1 PC-5: fixed question, bounded timeout, rows KEPT.
**Demonstrated-can-fail** against a seeded violation — a smoke that cannot fail is
decoration. REPORT_PB-4 records "PF-1 §F1.F-3 superseded-in-part by PB-4 F-6"; PF-1's
file is never edited.
**Acceptance:** red-then-green demonstrated in CI history; the F-5 7-run counter
consumes this test's verdicts.
```
may_touch: .github/workflows/** · platform/scripts/smoke/** ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane Q-2 — final readings graded (opus/xhigh — §3 floor; post-cutover; report-only)

Three real questions through the DEFAULT route post-cutover (domain / timing /
interpretive; one `deep_dive`; one logged to Samīkṣā). Grade against CLAUDE.md §J;
assess register purity, seams, arrival-line truthiness, prediction capture. PC-5:
verdicts as-is; quality findings transfer forward, never soften the gate.

### Lane F-7 — docs seal & campaign close (opus/high)

Design plan → **v1.0 RATIFIED-AS-BUILT** (every AS-BUILT delta carries its Pratinidhi
MEMO ref; unbuilt Phase-2 items marked honestly); architecture: D-02 executed, §11/§14
pointers to as-built, T-9 closed with the served-reading record; `CURRENT_STATE_v1_0.md`
§2 + `SESSION_LOG.md` closes; **`REPORT_PB.md`** — the FULL memo index (PB-0→PB-4),
gate ledgers per wave, residuals (arm-1, PF-1 supersessions, AC-15 handoff).
```
may_touch: 00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md ·
           00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md ·
           00_ARCHITECTURE/CURRENT_STATE_v1_0.md · 00_ARCHITECTURE/SESSION_LOG.md
           · briefs/pariprashna_build/**
```

### §F1.9 — DAG
```
        F-6 (smoke first — it is the cutover instrument)
   ┌──────┬──────┬──────┐
   F-1   F-2    F-3    F-4        (parallel)
   └──────┴──────┴──────┘
   → INTEGRATE → DEPLOY → smoke×7 green → F-5 CUTOVER (flip → hold → retire →
     deflag, each step deployed) → Q-2 → §G GATE → F-7 → CAMPAIGN CLOSE
```

## FROZEN §F2 — must_not_touch
```
platform-mcp/** (the root dispatcher NEVER; MCP surface out of scope) ·
platform/migrations/** & supabase/migrations/** (no schema work this wave) ·
mimamsa_predictions · the PB-3 ledger schema ·
briefs/CLAUDECODE_BRIEF_PF1_ENGINE_RESURRECTION_v1_0.md (supersession in
REPORT only) · 00_ARCHITECTURE/llm_consumption_audit/** ·
CLAUDECODE_BRIEF.md · CLAUDE.md · the sealed pg1/pg2 trees ·
any file outside the census/inventory in the F-5 deletion sweep
```

## §B — BIND-AT-OPEN
B-1 origin/main fetched+pinned; rollback image pinned. B-2 PB-1/2/3 gate receipts
confirmed green on the deployed flagged route. B-3 **dead-code census refreshed**:
PG1-C3 findings re-verified zero-importer at HEAD (census dated 2026-07-19) — the
refreshed list is F-5's deletion warrant. B-4 **inbound-consumer inventory** for
consult/consume: routes, links, scripts, CI, MCP docs — each mapped to redirect/410/fix
(W-5). B-5 worktree isolation verified. B-6 AC-15 handoff note drafted: the native's
week-of-use gate CANNOT run autonomously — handed over open, never claimed (W-4).

## §5 — Wave rulings (beyond master PCs)
| # | Fork | Ruling |
|---|---|---|
| W-1 | When may the retirement commit land? | Only after SEVEN consecutive green post-deploy smoke runs on the new default. Counter resets on any red. No exceptions, no Pratinidhi override — the campaign's own pre-commitment. |
| W-2 | Retirement diff review | Verifier reviews the deletion diff against the B-3 refreshed census: every deleted path in-census or proven zero-importer at HEAD; order leaf-first per the census dependency analysis. Any path outside the warrant = REJECT. |
| W-3 | Regression after cutover | Before flag removal → flag-flip rollback, immediately. After retirement/deflag → git revert of the retirement commit + rollback-pin redeploy. NEVER forward-fix a red default route. |
| W-4 | AC-15 (native's week-of-use gate) can't run autonomously | Recorded HANDED-TO-NATIVE with harness + symptom checklist in place. Never claimed, simulated, or proxied. M10 has no substitute. |
| W-5 | A consult consumer surfaces post-retirement that B-4 missed | Never a silent 404: Pratinidhi rules shim vs fix vs redirect, MEMO'd, same day. |
| W-6 | An AC item fails only on the default route (passed flagged) | The gate doing its job — the default route is the product. Fix-loop per master §1; the flagged-route pass is void for that assertion. |

## §G — Gate (post-deploy, DEFAULT route, no flags; fresh opus gate-runner + anti-gaming)
1 fresh session lands on `/clients/[id]/pariprashna` as default from dashboard +
global nav, no flag anywhere · 2 consult + consume retired and redirecting per the B-4
inventory (routes 308; API callers 410 + pointer); old trees deleted per refreshed
census; zero orphaned importers (build + grep proof) [integrity] · 3 seven consecutive
green smoke runs recorded BEFORE the retirement commit (CI history is evidence)
[integrity] · 4 smoke in CI post-deploy: 200 + persisted `message_parts` row +
zero-internal-id grep; demonstrated-can-fail [integrity] · 5 full §11 sweep on the
DEFAULT route: AC-1..AC-8 + AC-16 automated green; AC-9..AC-13 executed with evidence;
AC-14 on devices; AC-15 handed to native per W-4 (recorded, NOT claimed) · 6 sidebar:
collapse persists, streaming dot, zero added CLS · 7 arrival line derived from L1/Kāla
capability data — wire-tap proves retrieved values, never model prose [integrity] ·
8 the Seal fires in §5.3 order; motion audit: every animation cites its slot; the
closing-rule draw is the only >240ms motion · 9 every §7.8 edge state has a green
fixture with its exact lexicon copy; taxonomy maps 1:1 to §7.5 · 10 G-MOBILE + axe
green on the default route (AC-6/AC-14); SR smoke documented · 11 zero internal
identifiers in every streamed byte of Q-2's readings [integrity] · 12
`PARIPRASHNA_ENABLED` absent (grep = 0) · 13 Q-2 §J verdicts present and unsoftened;
the Samīkṣā-logged prediction reached the ledger.
**Final proof:** a fresh browser session, default routes only, no flags: ask → read
(approved feel) → log a prediction → revisit the thread (arrival line + sidebar +
byte-identical settled turns) — **while every [integrity] assertion from PB-1/2/3's
gates, re-run against this deployed default artifact, is still green.** **If any prior
wave's integrity assertion fails on the default route, the campaign is not closed.**
Anti-gaming charge: find the AC sweep run on the flagged route instead of the default, a
"deleted" tree surviving as an orphaned import or re-added file, or a smoke counter
padded with runs predating the default flip.

## §C — Close
REPORT_PB.md + REPORT_PB-4.md sealed; design plan v1.0 RATIFIED-AS-BUILT; CURRENT_STATE
+ SESSION_LOG updated; memo index complete; AC-15 with the native. **CAMPAIGN CLOSE.**

*End BRIEF_PB-4 v1.0.*
