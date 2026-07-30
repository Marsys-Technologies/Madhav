---
artifact: CAMPAIGN_PB_MASTER_BRIEF
canonical_id: PARIPRASHNA_BUILD_CAMPAIGN
type: CAMPAIGN MASTER BRIEF — MULTI-WAVE AUTONOMOUS BUILD
campaign: PB — Paripraśna Build ("the surface, made real")
version: 1.0
status: FROZEN — awaiting native kickoff
authored_by: Claude (Cowork) 2026-07-27, with the native
governing: >
  00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md (v1.4)
  + ESCALATION_POLICY_v1_0.md (v1.1) + ADJUDICATOR_CHARGE_v1_0.md (v1.1),
  AS AMENDED by §2 of this brief (the Pratinidhi replaces every human gate).
design_authority: >
  00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md (v0.3) — THE spec.
  Its §5.8.0 rulings 1–8c, §7.8 lexicon, §19.7 gate table are binding verbatim.
  Secondary: PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.10 — mind its ⚠ banner),
  RETRIEVAL_MCP_GROUND_TRUTH artifacts, pariprashna_mockups/ (the approved feel).
mode: >
  BUILD CAMPAIGN. Four write waves, PB-1 → PB-4, executed sequentially,
  lanes within each wave maximally parallel in isolated worktrees.
  Full 8-step lifecycle per wave incl. autonomous deploy + post-deploy gate.
autonomy: >
  TOTAL. One kickoff prompt; the campaign runs to its final REPORT with zero
  human input. Every fork a human would rule is ruled by the PRATINIDHI (§2).
base_model_policy: >
  Implementers default to SONNET 5. Conductor may dial any seat to OPUS and/or
  raise effort whenever value warrants (§3). Verifier floor is OPUS/high and is
  not a cost lever. Pratinidhi is OPUS/xhigh always.
---

# PB — Paripraśna Build Campaign (autonomous, four waves)

## §0 — What this campaign builds

The Paripraśna conversation surface as designed and approved: the typed
block-level stream protocol with the route reorder; the fixed-viewport
renderer with the one-line working band, pass seams, follow pill, right dock,
Model→Depth→Length composer; the closed phase lexicon with registry reader
labels; server-side citation sentinels; the canonical message store and
memory; the Samīkṣā prediction loop; and the finished surface at
`/clients/[id]/pariprashna`.

**The approved mockups are the felt spec.** When prose and mockup disagree on
feel, the mockup wins; when either disagrees with a numbered ruling, the
ruling wins.

### §0.1 Preconditions verified at campaign BIND (PB-0)

| # | Check | If it fails |
|---|---|---|
| P-1 | `/api/chat/consult` returns 200 for chart `482012f1-…` on the DEPLOYED app (the W4 bundle_hydrator carve-out landed) | Campaign HALTS at BIND with a one-page report — the engine is the substrate; do not build UI on a 500. This is the only halt in the campaign that precedes Pratinidhi authority. |
| P-2 | SAMĀPANA contracts live: `reading_depth: deep_dive` + verbosity tiers (commit `9c84ed51`) | Pratinidhi rules: bind pickers to whatever contract exists, or stub with a `TODO(PB-4)` — record which. |
| P-3 | `origin/main` fetched; base SHA pinned; rollback image pinned | Mechanical. |
| P-4 | Coexistence check: read root `CLAUDECODE_BRIEF.md` current campaign (do NOT touch the file). Record what is active. | Worktrees isolate us; `pb/*` namespace; never stash or clean the shared checkout — **the ŚUDDHAVĀCĀ sweep already ate this campaign's design files once.** |
| P-5 | Design authority fingerprints (sha256 of the plan + mockups) | Z-lanes edit only these exact versions. |

---

## §1 — Campaign lifecycle

```
 PB-0 BIND (campaign-level, once)
   │
 PB-1 DHĀRĀ — the stream & the surface        (the render bet, made real)
   │   gate green → deploy stays; REPORT_PB-1
 PB-2 SMṚTI — the canonical store & memory    (protocol and storage, one algebra)
   │
 PB-3 SAMĪKṢĀ — the prediction loop           (capture → ledger → review → outcome)
   │
 PB-4 PŪRṆATĀ — completion & cutover          (sidebar, arrival, seal, a11y/mobile
   │                                            hardening, /pariprashna default,
   │                                            consult retired, smoke in CI)
 CAMPAIGN CLOSE — REPORT_PB.md + SESSION_LOG + CURRENT_STATE pointer
```

Each wave: full 8 steps (OPEN → SPAWN → IMPLEMENT∥VERIFY → INTEGRATE → DEPLOY
→ REBUILD(scope-limited, usually none) → GATE(post-deploy) → CLOSE). A wave's
Binder expands its charter (§6) into `BRIEF_PB-n.md` in this directory at
OPEN, resolves BIND slots, stamps BOUND. **A red wave gate does not advance
the campaign**: the conductor runs the fix-loop (≤2 remediation cycles), then
Pratinidhi rules ship-degraded / park-wave / halt-campaign — recorded in a
MEMO either way.

**Between-wave deploys are real deploys.** PB-1 ships behind route flag
`/pariprashna` (old consult untouched — rollback is a flag). PB-4 flips the
default and retires consult per D-02.

---

## §2 — Roles, and the rule that replaces the human

House roles per CONDUCTOR_PROTOCOL §1 (Conductor, Binder, Implementers,
**Verifiers**, Gate runner, Anti-gaming verifier, Migration guard, Scope
warden) — plus one:

### §2.1 THE PRATINIDHI (the native's deputy) — replaces every human gate

A dedicated, fresh-context OPUS/xhigh agent, spawned at campaign open and
re-briefed at each wave, loaded with: the design plan v0.3 (all rulings), the
target architecture's decision registers (D-1…D-19, OT table, T-tensions),
the mockups, REPORT_PG-1/PG-2, and this brief. **Wherever the governing
protocols say "native ruling / async native review / HALT-AND-REPORT," the
Pratinidhi rules instead.** ESCALATION §2's three halt classes are re-routed
to it, except P-1 above.

**Its charge:**
1. **Rule from the registers first.** Most "human questions" are already
   answered by a D-ruling, a PC-pattern, or the mockups. Cite the register
   line in the ruling.
2. **Where the registers are silent, rule as the native would** — the deputy
   knows the product: acharya-grade always, one register, calm honesty,
   restraint over options, the mockup's feel is law, ship-small over
   gold-plate.
3. **Prefer the reversible option** when genuinely uncertain, and say so.
4. **Never re-baseline an integrity assertion.** A red gate fact stays red
   (ADJUDICATOR_CHARGE §4 binds the Pratinidhi absolutely). The Pratinidhi
   rules *what to do about* a red gate, never *whether it is red*.
5. **Every ruling is a MEMO** (`MEMO_PB-n_k.md`): question, options, ruling,
   register citations, reversibility, and what the native should review
   post-hoc. The campaign close report indexes all memos — the native audits
   the deputy's judgment after the fact, never during.
6. Known open items it WILL meet, pre-authorized to rule: **OT-11** (it holds
   the costed X-5 memo + the fresh-conversational-ledger recommendation),
   dock default open/collapsed, seam voice clause, per-thread control
   stickiness, any §12 open design decision.

### §2.2 The verification law (the native's core requirement)

**Nothing is done because its implementer says so. A lane is done when its
dedicated fresh-context Verifier (OPUS/high) issues an ACCEPT receipt** —
diff reviewed, tests run by the verifier itself, scope-warden pass, and for
UI lanes the replay-harness assertions green. Phase 1 merges a lane; only the
post-deploy Phase 2 gate closes a wave. Receipts in protocol §3.2 format.
Three rejections → PARK, Pratinidhi rules disposition.

---

## §3 — Model & effort policy (native-set)

| Seat | Model | Effort | Note |
|---|---|---|---|
| Implementers (default) | **sonnet** (Sonnet 5) | medium | The native's base. |
| Implementer on protocol/route reorder (S-1), sentinel pipeline (S-3), store schema (PB-2 M-1) | **opus** | high | Conductor pre-authorized to dial up: irreversible-ish, correctness-critical. |
| Verifiers — every lane | **opus** | **high** | Floor. Never a cost lever. "The strong model at high effort is always the one that says done." |
| Gate runner + anti-gaming | **opus** | high | Fresh context each. |
| Pratinidhi | **opus** | **xhigh** | Always. |
| §J reading-grader (PB-1 Q-lane, PB-4) | **opus** | **xhigh** | Never dialed down. |
| Mechanical fan-out (lexicon backfill, fixtures) | sonnet or haiku | low | Economize on discovery/transforms; spend on verification. |

Conductor may raise any seat at its judgment; it may never lower a floor.

---

## §4 — Worktrees, git, deploy (autonomous)

```
branch:    pb/<wave>/<lane>     wave branch: pb/<wave>
worktree:  /Users/Dev/Vibe-Coding/Apps/Madhav-pb-<wave>-<lane>
base:      origin/main@<PB-0 pin>, then each wave rebases its open on
           origin/main fetched fresh (other campaigns are landing)
identity:  pb-build-bot@madhav-astrology.iam.gserviceaccount.com
           chore(pb-<wave>/<lane>): <what> [PB-BOT]
```

- Worktree isolation ENFORCED (`git worktree list` before dispatch; a lane
  committing in the shared checkout = automatic REJECT).
- **Never stash, never clean the shared checkout** (P-4).
- Full git cadence auto-proceed per ESCALATION §0: commit, push at every
  transition, PR per wave, **merge on full receipts**, deploy, rollback pin
  armed before every deploy; build-health failure → immediate rollback, no
  forward-fixing.
- Migrations: **additive-only** without a Migration-guard ACCEPT (OPUS/high);
  destructive migrations are Pratinidhi-level with a written rollback path.

---

## §5 — Campaign-level pre-committed rulings

| # | Fork | Ruling |
|---|---|---|
| PC-1 | Spec ambiguity between plan prose, mockup, rulings | Ruling > mockup > prose. Still unclear → Pratinidhi. |
| PC-2 | A lane wants to touch the engine beyond its charter | REJECT via scope warden; raise to conductor; engine work is scheduled, not opportunistic. |
| PC-3 | The route reorder (S-1) destabilizes consult | Old route is UNTOUCHED until PB-4; the new route is a parallel path behind the flag. If shared code must change, verifier runs the consult smoke before ACCEPT. |
| PC-4 | A dependency on an open OT | Pratinidhi rules it (§2.1.6), MEMO'd. The campaign never waits. |
| PC-5 | §J grade of the first real readings is poor | Report as-is (PG-lineage discipline). Build quality ≠ reading quality; both facts stand. The campaign still ships the surface; the reading-quality finding transfers to the next campaign. |
| PC-6 | CI/deploy infra flakes | 2 retries, then Pratinidhi: proceed-with-manual-verify-equivalent (gate runner probes deployed URL directly) or park. |
| PC-7 | Concurrent campaign lands conflicting changes mid-wave | Rebase the wave branch; if semantic conflict, Pratinidhi rules precedence; never force-push main. |
| PC-8 | Anything would tempt a leak of internal register to the surface | There is no fork. D-14 is absolute; the lint + lexicon fallback are the mechanism; a lane shipping a raw id fails verification, period. |

---

## §6 — Wave charters

### PB-1 — DHĀRĀ: the stream & the surface ⭐ the campaign's spine

**Objective:** a user opens `/clients/[id]/pariprashna` (flagged), asks a real
question, and receives a real reading rendered with the approved feel: fixed
viewport, one-line band, ledger with pass grouping, tool rows named by data
point, pass seams on adaptive turns, follow pill, right dock with grounding +
prediction card, ⟦n⟧ chips with audit expand, Model→Depth→Length composer
bound to real contracts, three-line field.

**Lanes (parallel unless noted):**
- **S-1 (opus/high): protocol + route.** New `/api/pariprashna` route (or
  flagged fork of consult): stream opens BEFORE the planner (`turn.open`,
  `phase` live); typed SSE events per design §8 (turn/phase/activity.upsert/
  block.open|delta|commit/citation.define/seam.open|set/flag/grade/
  turn.commit|close), Zod schemas shared; NO `as any` anywhere (gate
  assertion); persistence via EXISTING write path (canonical store is PB-2).
- **S-2 (sonnet/med): lexicon + labels.** §7.8 closed lexicon as data;
  `label_key` on every activity; registry `register.reader_label` backfill
  for the ~30 capabilities the floor actually calls (top-50 list from
  RETRIEVAL_SYSTEM_TRUTH), fallback `CONSULTING THE CHART`/`RETRIEVED — CHART
  DATA` + CI warn; seam lexicon.
- **S-3 (opus/high): citation pipeline.** Sentinel prompt change; server
  rewriter with 64B/400ms hold-back, tolerant grammar, per-model
  hallucination counters; `citation.define` carrying reader_label + grade +
  audit_detail; register lint (rewrite/redact/telemetry — never fail-turn).
- **C-1 (sonnet/med): the renderer.** React client per mockup v3: fixed-height
  thread, follow pill, band (one-line live label, expandable fixed-height
  ledger, pass groups), seams, frozen-block/volatile-tail with rAF
  coalescing, caret-in-tail, chips, dock (collapsible, deep-link), composer
  (3 pickers in order, 3-line field, footnote), Marsys tokens exactly.
- **C-2 (sonnet/med): the harness.** Replay fixtures (incl. adaptive-3-pass,
  gemini-slabs, trickle, disconnect-mid-block, unclosed-sentinel); Playwright
  gates: settled-region CLS = 0, caret-in-tail-rect, no transmutation
  screenshots, rAF-coalesce commit-count, axe-core pass, mobile viewport run.
  **C-2's harness is the acceptance instrument for S-1/S-3/C-1 — it merges
  first** (declared serialization).
- **Q-1 (opus/xhigh, post-deploy):** three real questions through the flagged
  route (domain/timing/interpretive); grade against §J; compare stream to
  §12.3 contract. Report-only (PC-5).

**Gate (post-deploy, on the flagged route):** design plan §19.7 table
verbatim (CLS 0 / caret / no-transmutation / turn.open <300ms / no `as any` /
bad-network suite / mobile / axe) + tool rows visible with reader names +
seams render on a forced multi-pass + chips deep-link to dock + zero internal
ids in any streamed byte (lint telemetry = 0 leaks across Q-1's runs)
[integrity] + final proof: **a real persisted reading rendered with the
approved feel — the native could not distinguish its behaviour from the
mockup's.** Anti-gaming pass hunts the assertion passed on a local build.

### PB-2 — SMṚTI: store & memory
Canonical `conversation_messages`+`message_parts` (green-field, schema_version
from row one — no legacy corpus exists), protocol↔storage same-algebra golden
test (replay→reducer ≡ persisted parts), durable summaries worker +
prefix-stable splice, pgvector recall, Last-Event-ID replay-from-seq resume,
per-turn provenance stamp (D-16) written and surfaced ONLY in audit drawer.
Migration guard active; additive only.

### PB-3 — SAMĪKṢĀ: the loop
Conversational prediction ledger (Pratinidhi executes the OT-11 ruling it
carries), detector → candidate part → in-stream "Log to Samīkṣā" + dock card
with kāla-rekhā, review tab + dashboard badge, window-close daily job +
closing_soon, `record_outcome` end-to-end (folding PF-1's F-2 outcome.py fix
under a Migration-guard/Pratinidhi decision), NO-LEAKAGE arm-2 filter
confirmed on the new route, collect-only discipline (no serving loop-back —
§14.6 C1). PF-1's brief is marked superseded-in-part by a PB-3 addendum.

### PB-4 — PŪRṆATĀ: completion & cutover
History sidebar (collapsible, per mockup), empty state + arrival line, the
Seal settle choreography + motion constitution, error/reconnect UX per
lexicon edge states, mobile + a11y hardening to the §9 checklist, chat smoke
test in CI (PF-1 F-3 folded — asserts 200 + persisted row post-deploy),
`/pariprashna` becomes the default, `consult`/`consume` retired (D-02),
docs: design plan → v1.0 RATIFIED-AS-BUILT, architecture doc pointer,
CURRENT_STATE + SESSION_LOG closes, all memos indexed in REPORT_PB.md.

---

## §7 — Kickoff prompt (paste into Claude Code; the only human act)

```
Open campaign PB per 00_ARCHITECTURE/briefs/pariprashna_build/CAMPAIGN_PB_MASTER_BRIEF_v1_0.md.

You are the PB campaign conductor. Read, in order:
  1. CLAUDE.md
  2. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md
  3. .../ESCALATION_POLICY_v1_0.md and .../ADJUDICATOR_CHARGE_v1_0.md
  4. this master brief (its §2 amends the escalation policy: the PRATINIDHI
     replaces every human gate except precondition P-1)
  5. 00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md (v0.3 — THE spec)
  6. 00_ARCHITECTURE/pariprashna_mockups/ (the approved feel; the HTML v3 is law)

Then run PB-0 BIND and execute waves PB-1 → PB-4 end to end, autonomously,
with no human input at any point.

Binding constraints:
  - Spawn the PRATINIDHI (opus/xhigh) at open; route every would-be-human
    question to it; every ruling becomes a MEMO. It never re-baselines an
    integrity assertion.
  - Nothing is done until its dedicated fresh-context Verifier (opus/high)
    issues an ACCEPT receipt. Implementer "done" is a claim.
  - Implementers default to Sonnet 5; dial up to opus/higher effort where
    §3 pre-authorizes or value warrants; never lower a floor.
  - Maximal lane parallelism in isolated worktrees (pb/<wave>/<lane>);
    NEVER stash or clean the shared checkout; base on origin/main fetched.
  - Commit/push at every transition; PR + merge on full receipts; deploy
    autonomously with the rollback pin armed; red build → rollback, never
    forward-fix.
  - Old consult route untouched until PB-4 cutover; PB-1 ships behind the
    /pariprashna flag.
  - D-14 is absolute: zero internal identifiers in any user-facing byte.
  - Wave gates run post-deploy on the DEPLOYED artifact; a red gate is
    reported red; Pratinidhi rules disposition, never the color.

At PB-0, if /api/chat/consult does not return 200 on the deployed app for
chart 482012f1, HALT with a one-page report — that is the campaign's only
pre-Pratinidhi stop.

End with REPORT_PB.md, all wave reports, the memo index, SESSION_LOG and
CURRENT_STATE updated, worktrees cleaned. Do not ask for confirmation at any
point.
```

---

*End of CAMPAIGN_PB_MASTER_BRIEF v1.0 (2026-07-27) — FROZEN, awaiting the one kickoff.*
