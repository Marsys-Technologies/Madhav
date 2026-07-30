---
artifact: BRIEF_PB-3
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN) — WRITE WAVE
campaign: PB — Paripraśna Build
wave: PB-3 SAMĪKṢĀ — the prediction loop
version: 1.0
status: FROZEN — opens when PB-2 closes green (or ship-degraded per Pratinidhi MEMO)
authored_by: Claude (Cowork) 2026-07-28
governing: CAMPAIGN_PB_MASTER_BRIEF_v1_0.md (its §2 amends the house protocols; the Pratinidhi replaces every human gate)
design_authority: >
  PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §14 (§14.2 detection, §14.3
  candidate→ledger, §14.4 Samīkṣā, §14.5 jobs, §14.6 minimum-n/collect-only,
  §14.7 compliance decay, §14.10 NO-LEAKAGE) + D-16 (stamp copied, never
  referenced) + design plan v0.3 §6.9 (kāla-rekhā card), J8, §10.2, AC-16.
evidence_base: pg2_diagnostic/state/PG2_LANE_X-5.md (the three-ledger OT-11 costing)
gate: §G — 12 assertions on the DEPLOYED flagged route + final proof + anti-gaming pass
blocks: PB-4.
---

# PB-3 — SAMĪKṢĀ: the loop

## §0 — Objective, and the wave's FIRST ACT

L5 is sealed STRUCTURAL: calibration fills only from prediction→outcome
data, and the conversation surface is the only source (§14.1). Today a
detected `predictionCandidatePart` streams and dies. This wave carries it
the whole way: candidate → human confirmation → ledger row with utterance
provenance → window close → outcome → `mimamsa_calibration` — while
**serving remains byte-identical** (collect-only, §14.6 Phase C1).

**First act, before any lane dispatches: the Pratinidhi EXECUTES the OT-11
ruling it carries** (master §2.1.6; evidence = X-5), as `MEMO_PB-3_0.md`:

1. **A fresh conversational ledger table is created** (name fixed in the
   MEMO — §14.3's `brahma_mimamsa_prediction_ledger` names no live table,
   X-5 §3; neither existing table satisfies §14.3 without surgery).
2. **`mcp_predictions` is RETIRED** (0 rows, interim relay, migration 071) —
   destructive → Pratinidhi-level with written rollback path (master §4);
   its writer (`ppl_writer.ts`) repointed or deleted per the MEMO.
3. **`mimamsa_predictions` is UNTOUCHED** — schema + 384 rows hash-pinned at
   BIND; stays the build-time deterministic L5 ledger referenced by
   `mimamsa_calibration`. `brahma_prospective_ledger` likewise untouched.
4. **A ledger-map doc** (`briefs/pariprashna_build/LEDGER_MAP_PB-3.md`):
   each table's authority + the `record_outcome` disambiguation.

Lanes bind to the MEMO's table name (slot B-2). The campaign never waits on
OT-11 — the deputy rules, MEMO'd, audited post-hoc.

## §1 — Lifecycle, state, git

Per master brief §1/§4. Branch `pb/3/<lane>`, worktree `Madhav-pb-3-<lane>`,
state shards `briefs/pariprashna_build/state/PB3_LANE_<lane>.md`, index
`STATE_PB-3.md`, commits `chore(pb-3/<lane>): … [PB-BOT]`. Verification law
per master §2.2, verbatim. Migration guard (opus/high) standing;
additive-only except the MEMO'd `mcp_predictions` retirement.

## FROZEN §F1 — Lane map

### Lane L-1 — the ledger schema ⭐ MERGES FIRST
**Implementer opus/high (schema lane — §3 dial-up class) · Verifier opus/high · Migration guard opus/high**

- The MEMO'd table, full §14.3/§14.2 field set from row one: `chart_id uuid
  NOT NULL` · `message_part_id` **FK → PB-2 `message_parts.id`** ·
  `claim_text` · `domain` · **`window daterange`** · **`confidence numrange`**
  (Brier-ready; never a text enum — the X-5 lesson) · `direction` ·
  `technique_refs[]` · `grounding_fact_ids[]` · `created_from_channel` ·
  **8-state lifecycle**: `detected → confirmed → open → window_closed →
  outcome_recorded`, exits `dismissed/lapsed/unverifiable`, + `lapsed_unconfirmed`.
- **Stamp COPIED in, never referenced** (D-16(d)): `build_id, priors_version,
  formula_versions, ranking_config, now_context_date` snapshotted at
  confirmation from M-6's read API. A ledger row is an immutable historical
  claim: DB-level guard + test forbid UPDATE of stamp and settled claim fields.
- Outcome columns co-located (`outcome`, `outcome_note`, `outcome_recorded_at`,
  Brier inputs); `unverifiable` = Brier-excluded marker.
- DAL enforcing one legal-transition matrix; `count_sql` registered (§N.4).

**Acceptance:** migration applies/rolls back on a copy; illegal transitions
rejected; stamp-immutability test green; `mimamsa_predictions` hash unchanged.
```
may_touch: platform/migrations/** · supabase/migrations/** ·
           platform/src/lib/pariprashna/samiksha/** (new) ·
           platform/src/app/api/mcp/writes/** (ppl_writer retirement per MEMO
           only) · briefs/pariprashna_build/**
```

### Lane L-2 — capture: detector → candidate → confirm (sonnet/med)

- Detector (two-stage, §14.2) emits the structured candidate `{claim_text,
  domain, window_start, window_end, direction, confidence_stated?,
  technique_refs[], grounding_fact_ids[]}` (grounding refs free from S-3's
  citation parts); persists as a PB-2 `prediction_candidate` part, state
  `detected`; interrupted turns excluded (PB-2 M-5 contract).
- **In-stream one-tap "Log to Samīkṣā"** on the settled turn (§14.4.2 —
  confirmation propensity decays fast).
- **Dock prediction card** per mockup + §6.9: lifecycle eyebrow, Cormorant
  claim, **kāla-rekhā** (1px `--rule` span, 2px gold window segment, 3px
  today-dot from the real date) — AC-16 geometry is the acceptance instrument.
- **Confirm elicits a probability** if none stated (§14.3): slider → numrange;
  confirmation writes the L-1 row, stamp copied,
  `created_from_channel='pariprashna'`; confirm/edit/dismiss-with-reason,
  dismissal reasons persisted (detector precision data).

**Acceptance:** fixture turn with a time-indexed claim → candidate → confirm
→ ledger row with resolving `message_part_id`; AC-16 card assertions green.
```
may_touch: platform/src/lib/pariprashna/samiksha/** ·
           platform/src/app/api/pariprashna/** (detector seam) ·
           platform/src/components/pariprashna/** ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane L-3 — the review surface (sonnet/med)

- `/clients/[id]/samiksha`, three sections per §14.4: **Awaiting confirmation**
  (candidate in message context; one-tap confirm/edit/dismiss; probability
  slider) · **Open** (live timeline) · **Resolve** (happened / didn't /
  partially / **can't-tell** → `unverifiable`, Brier-excluded, counted
  separately as an honesty metric); batch resolution keyboard-fast (§14.7).
- Dashboard badge: `--gold-dim` numeral, never red (§10.2), counting
  `detected` + `window_closed`. Lapsed non-shameful (W-2): coverage is a
  statistic, no guilt UI. Marsys tokens throughout.
- Deep links → `/pariprashna/t/{thread}#turn-{n}` (§3.3); settled turns stay
  byte-identical (P1).

**Acceptance:** badge equals SQL truth; can't-tell provably excluded from the
Brier query; axe clean on the tab.
```
may_touch: platform/src/app/clients/[id]/samiksha/** (new) ·
           platform/src/components/pariprashna/** ·
           platform/src/lib/pariprashna/samiksha/** ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane L-4 — ONE consolidated daily job (sonnet/med)

Per §14.5 but **one scheduled job, not three** — T-3 binds (every always-on
subsystem is future 2 a.m. debugging). The single daily run: (a) `open AND
window_end < now()` → `window_closed` + resolution enqueue; (b) `closing_soon`
at `window_end − 14d`; (c) **one consolidated email digest**, sent only when
non-empty. Idempotent per day; `--as-of <date>` simulated-clock flag for the
gate; transport per B-5 (log-only stub if absent — W-5).

**Acceptance:** simulated-clock run transitions correctly, idempotent on
re-run, exactly one digest.
```
may_touch: platform/src/lib/pariprashna/samiksha/** ·
           platform/scripts/samiksha/** (new) · .github/workflows/** (schedule)
           · platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane L-5 — record_outcome + outcome.py disposition (opus/high — PF-1 F-2's own bar)

- Outcome recording (L-3 Resolve or the card) → Brier `(confidence−outcome)²`
  → `mimamsa_calibration` upsert; `source_citation` = the ledger row id
  (**the ledger is the citation**, §14.5). All against the L-1 table.
- **The PF-1 F-2 fold — `outcome.py`/`phala_anchors` drift** (X-5 §4: the
  sidecar references columns absent from the live table; `record_outcome`
  has never been callable). **Diagnose rename-vs-missing BEFORE writing**
  (PF-1's case table governs). The fresh ledger changes the disposition
  space vs PF-1 PC-4: outcome state now lives in L-1's table, so the likely
  shape is `outcome.py` retargeted (or retired), `phala_anchors` read-only
  as anchor reference — Migration guard reviews; **`phala_anchors` schema
  work needs a Pratinidhi MEMO**; park-with-costed-spec stays valid.
  Inspect `update_calibration()` (X-5 flagged it uninspected).
- **Do NOT edit PF-1's brief file.** REPORT_PB-3 records "PF-1 §F1.F-2
  superseded-in-part by PB-3 L-5"; PF-1 stays sealed as authored.

**Acceptance:** `record_outcome` round-trips against a real ledger row on the
deployed app, OR parks with costed spec + MEMO. Both valid; silence is not.
```
may_touch: platform/python-sidecar/brahmagyan/mimamsa/** ·
           platform/src/lib/pariprashna/samiksha/** ·
           platform-mcp/src/tools/**/mimamsa_outcome* (retarget only; the
           root dispatcher NEVER) · platform/tests/pariprashna/** ·
           briefs/pariprashna_build/**
```

### Lane L-6 — NO-LEAKAGE + COLLECT-ONLY (sonnet/med · Verifier opus/high) [integrity lane]

- **Arm-2 verified on the new route** (§14.10): outcome/LEL-read tools carry
  `calibration_context_only`; test asserts exclusion from every planner
  projection the route can reach; CI canary (arm-4): no serving-path plan
  reaches a leakage-flagged tool. Exclusion test demonstrated-can-fail.
- **COLLECT-ONLY hard-coded** (§14.6 C1): no code path from a calibration
  write to a `priors_version` bump or any serving annotation in phala/kala
  envelopes — absent code with a grep test + runtime assertion, not config.
- Arm-1 (DB roles, 0% built per PG-1) OUT of scope: recorded as a standing
  residual in REPORT_PB-3, never silently fixed.

**Acceptance:** canary green; exclusion test red-then-green; the serving
byte-identity harness (used by the final proof) built and demonstrated.
```
may_touch: platform/src/lib/retrieval/registry/** (calibration_context_only
           flags — additive fields only; verifier greps the diff) ·
           platform/src/lib/pariprashna/** · platform/tests/pariprashna/** ·
           .github/workflows/pariprashna-ci.yml · briefs/pariprashna_build/**
```

### Lane Z-3 — synthesis & close (opus/high)
`REPORT_PB-3.md` (memo index, PF-1 supersession, arm-1 residual); LEDGER_MAP
finalized; arch §14 annotated AS-BUILT; SESSION_LOG; STATE.

### §F1.9 — DAG
```
  MEMO_PB-3_0 (Pratinidhi executes OT-11) → L-1 (ledger first)
          │
   ┌──────┼──────┬──────┬──────┐
   L-2   L-3    L-4    L-5    L-6    (parallel; conductor sequences the
   └──────┼──────┴──────┴──────┘      integrate if card components collide)
          ▼
      INTEGRATE → DEPLOY (flagged) → §G GATE → Z-3
```

## FROZEN §F2 — must_not_touch
```
platform/src/app/api/chat/** (consult UNTOUCHED — PC-3) ·
platform/src/components/consume/** · platform/src/components/chat*/** ·
mimamsa_predictions (no schema/row change — hash-pinned) ·
brahma_prospective_ledger (disposition recorded only) · mi_*.py L5 build
writers · the MCP root dispatcher ·
briefs/CLAUDECODE_BRIEF_PF1_ENGINE_RESURRECTION_v1_0.md (supersession lives
in REPORT, never in the file) · 00_ARCHITECTURE/llm_consumption_audit/** ·
CLAUDECODE_BRIEF.md · CLAUDE.md · the sealed pg1/pg2 trees
```

## §B — BIND-AT-OPEN
B-1 origin/main fetched+pinned; rollback pinned. B-2 **MEMO_PB-3_0 issued;
ledger name bound into every lane charge.** B-3 PB-2 `message_parts` live on
the deployed app (FK target) + M-6 stamp API confirmed. B-4
`mimamsa_predictions` schema+rowcount hash recorded; `phala_anchors`
live-schema snapshot for L-5. B-5 scheduler + email transport identified
(stub ruling if absent). B-6 worktree isolation verified; `mcp_predictions`
rollback path written BEFORE the retirement migration runs.

## §5 — Wave rulings (beyond master PCs)
| # | Fork | Ruling |
|---|---|---|
| W-1 | Detector confidence high; auto-promotion tempts | **FORBIDDEN — §14.3 verbatim.** A polluted ledger is worse than a sparse one. Candidates age out visibly as `lapsed_unconfirmed`; recall stays auditable. |
| W-2 | Lapsed/unresolved windows accumulate | Non-shameful by design (§14.7): no red counters, no guilt copy; coverage is a reported statistic; batch resolution is the answer. |
| W-3 | Calibration rows land; something wants to serve them | **NO — collect-only stands for the entire campaign** (§14.6 C1). No priors bump, no envelope annotation, no minimum-n exception. Loop-back is a future campaign's per-cell threshold decision. |
| W-4 | L-5 finds `phala_anchors` genuinely lacks outcome columns | The fresh ledger likely moots them (outcome lives in L-1). Migration guard + Pratinidhi rule the disposition; park-with-costed-spec valid. Never migrate `phala_anchors` without the MEMO. |
| W-5 | Email transport absent | Job + digest still built and tested; transport stubbed log-only; Pratinidhi MEMO records the residual. Never fake a send. |
| W-6 | No detectable prediction arises for the gate | Force one: a timing `deep_dive` on the canonical chart reliably yields time-indexed claims. If genuinely none, Pratinidhi rules a scripted-claim fallback — recorded as such, never passed off as organic. |

## §G — Gate (post-deploy, flagged route; fresh opus gate-runner + anti-gaming)
1 MEMO_PB-3_0 exists and is EXECUTED: ledger live · `mcp_predictions` retired
with written rollback · `mimamsa_predictions` hash-identical to B-4 pin ·
LEDGER_MAP committed [integrity] · 2 ledger carries the full §14.3/§14.2
field set incl. `message_part_id` FK, `created_from_channel`, 8-state
lifecycle, numrange confidence · 3 a prediction logged from a REAL deployed
reading reaches the ledger with the stamp COPIED (fields equal M-6's turn
stamp; no reference/join) and `message_part_id` resolving [integrity] ·
4 confirm elicits a probability when none stated · 5 dock card + kāla-rekhā
pass AC-16 geometry · 6 review tab: three sections live; badge equals SQL
truth; can't-tell → `unverifiable`, provably Brier-excluded · 7 consolidated
job under simulated clock: open→window_closed, closing_soon at −14d, exactly
one digest; idempotent re-run · 8 `record_outcome` round-trips on the
deployed app OR parked-with-costed-spec + MEMO; PF-1 file untouched,
supersession recorded · 9 no auto-promotion path (code audit: nothing writes
`confirmed`/`open` without a human act); `lapsed_unconfirmed` aging shown ·
10 zero leakage-flagged tools reachable from the route's planner context
(canary + exclusion test, demonstrated-can-fail) [integrity] · 11
collect-only: no code path from calibration write to priors bump or serving
annotation; serving byte-identical before/after a full loop [integrity] ·
12 consult route byte-identical to base pin [integrity].
**Final proof:** on the deployed flagged route — log a prediction from a
real reading → close its window (simulated clock) → resolve → a
`mimamsa_calibration` row lands — **while a fixed serving question's
response is byte-identical before and after the whole cycle.** **If serving
moved, or no calibration row landed, the wave did not happen.**
Anti-gaming charge: find the loop proven with hand-INSERTed rows instead of a
streamed reading, a byte-identity check against a cached response, or a stamp
"copied" by JOIN at read time.

## §C — Close
REPORT_PB-3.md sealed (memo index, PF-1 supersession, arm-1 residual);
worktrees cleaned; campaign advances to PB-4.

*End BRIEF_PB-3 v1.0.*
