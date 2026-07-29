---
artifact: BRIEF_PB-1
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN) — WRITE WAVE
campaign: PB — Paripraśna Build
wave: PB-1 DHĀRĀ — the stream & the surface
version: 1.0
status: FROZEN — opens when the campaign conductor reaches it (PB-0 green)
authored_by: Claude (Cowork) 2026-07-27
governing: CAMPAIGN_PB_MASTER_BRIEF_v1_0.md (which amends the house protocols per its §2)
design_authority: PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md (v0.3) + pariprashna_mockups/pariprashna_core_conversation.html (v3 — the felt spec)
gate: §G — 14 assertions on the DEPLOYED flagged route + final proof + anti-gaming pass
blocks: PB-2/3/4. The campaign's spine.
---

# PB-1 — DHĀRĀ: the stream & the surface

## §0 — Objective

A user opens `/clients/[id]/pariprashna` (behind flag `PARIPRASHNA_ENABLED`),
asks a real question about chart `482012f1-…`, and receives a real reading
rendered with the approved feel. The old consult route is UNTOUCHED; rollback
is the flag.

**Definition of the approved feel** (all binding, from plan §5.8.0 rulings
1–8c + mockup v3): fixed-height viewport that never grows, one-line working
band whose live label rewrites in place, expandable fixed-height ledger with
PASS grouping, tool rows named by data point, pass seams on adaptive turns
that settle into hairline dividers, ↓ follow pill, collapsible right dock
(grounding + prediction placeholder), ⟦n⟧ chips deep-linking into the dock,
composer with Model→Depth→Length pickers and a three-line field, zero
provenance anywhere ambient, zero internal identifiers in any streamed byte.

## §1 — Lifecycle, state, git

Per master brief §1/§4. Branch `pb/1/<lane>`, worktree
`Madhav-pb-1-<lane>`, state shards `briefs/pariprashna_build/state/PB1_LANE_<lane>.md`,
conductor-only index `STATE_PB-1.md`, receipts in protocol §3.2 format,
commits `chore(pb-1/<lane>): … [PB-BOT]` pushed at every transition.

## FROZEN §F1 — Lane map

### Lane C-2 — the harness (MERGES FIRST; it is the acceptance instrument)
**Implementer sonnet/med · Verifier opus/high**

- Replay server + fixtures: `adaptive-3-pass`, `single-pass`, `gemini-slabs`,
  `1-byte-trickle`, `3s-stall`, `disconnect-mid-block`, `unclosed-sentinel`,
  `malformed-sentinel-variants`, `citation-dense`, `giant-table`,
  `honest-gap`, `stop-mid-pass`.
- Playwright gate battery, each an executable assertion:
  G-CLS (settled-region layout-shift contribution = 0 above the volatile
  tail), G-CARET (caret rect ⊆ tail-block rect, every frame), G-TRANSMUTE
  (screenshot diffs at 25/50/75/100% per fixture — no prose→chip flips),
  G-RAF (React commit count ≤ frames elapsed), G-VIEWPORT (thread container
  height constant during stream; page height constant), G-PILL (pill appears
  on upward scroll during stream, re-pins on click), G-AXE (axe-core clean;
  committed blocks exit the aria-live region), G-MOBILE (full battery at
  390×844, chips tap-open).
- Golden protocol test scaffold: recorded event stream → reducer → final
  client state (used by PB-2 for byte-equality vs persisted parts; here
  asserts reducer determinism + idempotent duplicate-seq handling).

**Acceptance:** every battery item runs and can FAIL (each demonstrated red
against a seeded violation), then green against C-1.
```
may_touch: platform/tests/pariprashna/** · platform/scripts/replay/** ·
           .github/workflows/pariprashna-ci.yml · briefs/pariprashna_build/**
```

### Lane S-1 — protocol + route (opus/high)

- New route `platform/src/app/api/pariprashna/route.ts` (fork, not edit, of
  consult): **the stream opens before the planner** — `turn.open` +
  `phase{plan,start}` are the first bytes; planner faults become in-stream
  `error` events (no post-headers 422).
- Typed SSE events exactly per plan §8 vocabulary: `turn.open · phase ·
  activity.upsert (keyed; label_key; pass_id) · block.open|delta|commit ·
  seam.open|set (pass boundaries) · citation.define · flag · grade ·
  turn.commit · turn.close · error`. Zod schemas in a shared module imported
  by server AND client — **zero `as any` in the writer path** (gate G-9).
- Adaptive passes: when the loop re-enters retrieval after prose, emit
  `seam.open{pass_id,label_key}` then `seam.set{summary}` when prose resumes;
  activities carry `pass_id` for ledger grouping.
- **Retrieval dispatch is IN-PROCESS through the shared registry** — the same
  capability handlers the MCP edge proxies to over HTTP
  (`/api/retrieval/capability` → `lib/retrieval/registry/`). No parallel
  retrieval client, no HTTP hop to the MCP edge, no data access outside
  registry handlers. This is gate assertion 15 [integrity] and the §6.5
  engine-boundary test made executable.
- Persistence via the EXISTING write path (canonical store is PB-2's).
  Prediction detector left wired as-is.
- Depth/Length/Model params accepted and bound: `reading_depth` (Auto→derive;
  `deep_dive` forces dossier route), verbosity tier, `model_id`
  (P-2 contracts; stub per Pratinidhi if absent).

**Acceptance:** curl of the deployed flagged route shows `turn.open` < 300ms
from POST on the canonical chart; event stream Zod-validates end-to-end;
consult route diff = zero lines.
```
may_touch: platform/src/app/api/pariprashna/** ·
           platform/src/lib/pariprashna/protocol/** (new) ·
           briefs/pariprashna_build/**
```

### Lane S-2 — lexicon + reader labels (sonnet/med; fan-out haiku/low)

- §7.8 lexicon as data (`platform/src/lib/pariprashna/lexicon.ts`): the 10
  band phases, retrieval facets, `RETRIEVED — ⟨data point⟩` pattern, seam
  entries (`LOOKING FURTHER —`, `READING DEEPER —`, `CROSS-CHECKING BEFORE
  CONCLUDING`, `RECONSIDERING —`), all edge states verbatim from the plan.
- `register.reader_label` backfill on the capabilities the acharya floor
  actually calls (derive the list from RETRIEVAL_SYSTEM_TRUTH + a live
  PlanReceipt for career/timing/health questions; expect ~30). Unmapped →
  `RETRIEVED — CHART DATA` fallback + CI warning (test proves the fallback
  and the warning fire).
- Server resolves `label_key`→string; **the client renders strings verbatim
  and contains no mapping** (leak-proof by construction).

**Acceptance:** a synthetic tool with no label streams as the fallback, never
its id; CI warn emitted; the three PlanReceipt question-types produce 100%
mapped labels.
```
may_touch: platform/src/lib/pariprashna/lexicon.ts ·
           platform/src/lib/retrieval/registry/** (register blocks ONLY —
           additive fields; zero behavioural change; verifier greps the diff) ·
           briefs/pariprashna_build/**
```

### Lane S-3 — citation pipeline (opus/high)

- Synthesis prompt: emit `⟦cite: <ref>⟧` sentinels; footnote instruction
  REMOVED on this route.
- Server rewriter in the stream path: hold-back from `⟦` with
  MAX_HOLDBACK=64B / TIMEOUT=400ms → flush-as-text + `flag{malformed_sentinel}`;
  tolerant grammar (`[[cite:…]]`, spacing, case) normalized + logged;
  resolves ref → `citation.define{n, reader_label, grade, audit_detail}`;
  unresolvable → `unverified` grade + per-model hallucination counter.
- Register lint on every block pre-commit: patterns `SIG\.\w+\.\d+`,
  `\b(MSR|UCN|CGM|CDLM|LEL)\b`, `\b(bo|ga|ka|ph|mi|bg)_[a-z_]+\b`, table
  names. Verdicts: rewrite (id-shaped w/ registry label) / redact+flag /
  telemetry. **Never fail-the-turn** (plan ruling; the primary defense is the
  clean evidence context + this structured channel).

**Acceptance:** replay fixtures `unclosed-sentinel` (stream never stalls;
flushes at limits) and `malformed-sentinel-variants` (all normalized) green;
lint telemetry = 0 leaks across Q-1's three real readings (gate G-11).
```
may_touch: platform/src/lib/pariprashna/citations/** (new) ·
           platform/src/lib/synthesis/prompts/** (route-scoped prompt variant
           only — consult's prompt untouched) · briefs/pariprashna_build/**
```

### Lane C-1 — the renderer (sonnet/med)

React client at `platform/src/app/clients/[id]/pariprashna/` matching mockup
v3 exactly: Marsys tokens verbatim; fixed-height thread owning scroll
(`overflow-anchor:none`, pinned-follow, upward-intent break, ↓ pill); working
band (one-line live label ← latest `activity.upsert`; expandable 172px
ledger well, PASS group headers, ▸ tool rows with mono counts, ✓/◐/○ states);
seams (`seam.open` live line → `seam.set` hairline divider, self-mutating
only); frozen-block/volatile-tail with rAF-coalesced deltas and
`block.commit.final_md` re-render-once-then-memo (always-equal comparator —
re-render of a frozen block fails CI via C-2's profiler hook); caret as child
of tail text node; ⟦n⟧ chips fixed-geometry, click → dock opens to row; dock
(312px, collapsible », grounding rows accrue per pass with grade marks,
prediction-card slot for PB-3, NO provenance footer); composer (pickers
Model→Depth→Length wired to S-1 params, footnote Auto/override, 3-line field,
Stop during stream → `interrupted` settle keeping streamed text).

**Acceptance:** full C-2 battery green on all fixtures, desktop + mobile.
```
may_touch: platform/src/app/clients/[id]/pariprashna/** ·
           platform/src/components/pariprashna/** (new tree — the old chat
           component trees are NOT modified) · briefs/pariprashna_build/**
```

### Lane Q-1 — first real readings (opus/xhigh; post-deploy; report-only)

Three real questions through the deployed flagged route (career+timing /
health / open-interpretive), one forced `deep_dive`. Capture full streams +
persisted rows. Grade each against CLAUDE.md §J; assess register purity,
seam behaviour under real adaptive passes, stream-vs-contract conformance.
PC-5 (master): verdicts reported as-is; a poor reading does not block the
wave; it transfers forward.

### Lane Z-1 — synthesis & close (opus/high)
`REPORT_PB-1.md`; design plan → v0.4 annotated AS-BUILT deltas (if any —
each one Pratinidhi-memo'd); SESSION_LOG append; STATE finalized.

### §F1.9 — DAG
```
        C-2 (harness first)
          │
   ┌──────┼──────────┐
   S-1   S-2   S-3   C-1     (parallel; C-1 integrates against S-* stubs
   └──────┼──────────┘        via recorded fixtures until merge)
          ▼
      INTEGRATE → DEPLOY (flagged) → Q-1 → §G GATE → Z-1
```

## FROZEN §F2 — must_not_touch
```
platform/src/app/api/chat/** (consult UNTOUCHED — PC-3 master) ·
platform/src/components/consume/** · platform/src/components/chat*/** ·
platform/migrations/** & supabase/migrations/** (no schema work this wave) ·
platform-mcp/** · 00_ARCHITECTURE/llm_consumption_audit/** ·
CLAUDECODE_BRIEF.md · CLAUDE.md · the sealed pg1/pg2 trees
```

## §B — BIND-AT-OPEN
B-1 origin/main fetched+pinned; rollback image pinned. B-2 P-1/P-2 rechecked
(consult 200; depth/verbosity contracts — record binding or stub ruling).
B-3 worktree isolation verified. B-4 flag name + routing confirmed dead in
prod before work. B-5 design-authority fingerprints. B-6 live PlanReceipt
captured for S-2's label list.

## §5 — Wave rulings (beyond master PCs)
| # | Fork | Ruling |
|---|---|---|
| W-1 | Provider stream gives no clean pass boundary | Derive seams from the loop's own re-entry into retrieval (engine-side truth), never from prose heuristics. If a model yields no adaptive passes, seams simply don't render — single-pass is a valid shape. |
| W-2 | turn.open <300ms unreachable due to auth/middleware cost | Measure; if platform-imposed, Pratinidhi may re-baseline to measured-floor+50ms with MEMO. This is a latency budget, not an integrity assertion. |
| W-3 | A needed reader_label has no obvious plain name | Pratinidhi names it (it holds the lexicon voice rules). Never ship the id. |
| W-4 | Streamdown/markdown lib fights frozen-block memo | C-1 may swap the md renderer inside the new tree; the invariant (commit-once, memo-forever) outranks any library. |

## §G — Gate (post-deploy, flagged route; fresh opus gate-runner + anti-gaming)
1 G-CLS=0 [integrity] · 2 G-CARET [integrity] · 3 G-TRANSMUTE [integrity] ·
4 G-VIEWPORT fixed [integrity] · 5 G-PILL · 6 turn.open<300ms (or W-2
re-baseline) · 7 G-RAF · 8 seams render on a real adaptive turn & settle
in place · 9 zero `as any` in writer path + full Zod round-trip [integrity] ·
10 tool rows show reader names; synthetic-unmapped shows fallback+CI-warn ·
11 zero internal identifiers in every streamed byte of Q-1's three readings
(lint telemetry corroborates) [integrity] · 12 chips deep-link to dock rows;
dock collapse/expand stable · 13 G-AXE + G-MOBILE · 14 consult route byte-
identical to base pin [integrity] · 15 **ONE RETRIEVAL SYSTEM**: every
retrieval in Q-1's readings dispatched IN-PROCESS through the shared registry
(trace shows `marsys://` capability ids; zero HTTP calls to the MCP edge;
zero data access outside registry handlers; `git grep` proves no parallel
retrieval client was introduced) [integrity].
**Final proof:** a real persisted reading, streamed through the deployed
flagged route, indistinguishable in behaviour from mockup v3 across the
C-2 battery. **If the harness can tell them apart, the wave did not happen.**
Anti-gaming charge: find the assertion passed against a fixture but never
against the live deployed stream.

## §C — Close
REPORT_PB-1.md sealed; flag REMAINS OFF for default users (native flips or
PB-4 cutover); worktrees cleaned; memo index appended; campaign advances
to PB-2.

*End BRIEF_PB-1 v1.0.*
