---
artifact: AUTONOMY_RESILIENCE_PATTERN_v1_0.md
canonical_id: AUTONOMY_RESILIENCE_PATTERN
version: 1.0
status: CURRENT (governs Brahma wave execution under AUTONOMOUS_MODE — zero synchronous native gates)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-04
authored_for: Build-Guarantor Swarm + Claude Code conductors
amends: BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md §B + §F + §I; extends BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md §E (12-role → 14-role)
context: >
  Native directive 2026-06-04: zero synchronous native gates across the four parallel Brahma waves
  (WS-1, WS-2, WS-3, WS-Misc). This pattern documents the three-tier escalation framework, the four
  provisioning patterns, the two new swarm roles (Vimarśaka + Tier-1 Severity Remediator), and the
  reframe of the WS-3 external-acharya gates to AI-assessed-with-optional-retrospective. After this
  doc, only ONE event can ever reach the native synchronously: the absolute catastrophic-runaway
  budget ceiling, and even that is an async notification.
---

# Autonomy Resilience Pattern — zero synchronous native gates

## §A — The three-tier escalation framework

Every event that interrupts an autonomous loop falls into exactly one of three tiers. The swarm classifies as it goes; only Tier-3 may pause the run, and Tier-3 has only one entry.

| Tier | Behavior | Examples |
|---|---|---|
| **Tier 1 — Auto-resolved** | Swarm internalizes; no log entry beyond standard provenance | Bounded retries that succeed; routine canary→promote; passing AC gates |
| **Tier 2 — Decision-with-Smṛti-log** | Swarm decides + writes the decision + reasoning to Smṛti; run continues; native reads asynchronously | Destructive-op disposition (REPOINT / DELETE / STUB); allowlist construction; budget cap raises within ceiling; engine ground-truth self-repair fallbacks; Tier-1 Severity Remediator invocations; AI-assessed acharya verdicts |
| **Tier 3 — Genuine pause (single entry)** | Swarm stops; emits async Smṛti notification; native may authorize continuation from any device | **Catastrophic-runaway cap** ($5k absolute ceiling per AUTONOMOUS_MODE §C.4). And only this. |

The Conductor never waits on a human for any other reason.

## §B — The four provisioning patterns (Tier-1 / Tier-2 enablers)

### B.1 — Deep-fix escalation tier

Replaces the "5 fix-attempts → park" rule with a graduated escalation:

```
Attempt 1–4: standard reasoner (Gemini / DeepSeek per model preference)
Attempt 5:   stronger reasoner (Gemini Pro / DeepSeek v4 Pro), full Smṛti context
Attempt 6:   multi-model parallel attempt — 3 reasoners independently, swarm picks
             the highest-confidence patch that passes the AC
Park only after 6 distinct attempts (not 5 identical retries)
```

A "park" under this regime is the rarest of Tier-2 events — it doesn't pause the wave; the parked asset is reported in the wave-close summary and a follow-on session re-attempts later. Adjacent assets continue.

### B.2 — Autonomous disposition classifier

For destructive ops on files / code / data, the disposition (DELETE_WHOLESALE / DELETE_WITH_CONSUMERS / REPOINT / STUB) is decided by an LLM classifier reading:
- The file's reverse-import graph (built by Nirīkṣaka)
- The disposition rule table (committed alongside the wave brief)
- The known Brahma-equivalent mapping for repointable surfaces
- Smṛti history of past similar decisions in this wave

Output: a disposition + a 2-line rationale, logged to Smṛti. If the classifier's confidence < 0.6 OR a multi-model consensus check fails (e.g., 2 of 3 reasoners disagree), the disposition defaults to **STUB with TODO marker + BRAHMA_DEFERRED_FEATURES.md entry** rather than halting. Stubbing is reversible; halting is not.

### B.3 — Auto-budget raise within ceiling

Per-asset cap escalation (default $300):
- 80% of cap reached, asset shows positive progress (commits landing, ACs partially passing) → raise to $600
- 80% of $600 reached, still positive progress → raise to $1000
- 80% of $1000 reached → escalate to multi-model consensus on a "is this asset salvageable" assessment; if yes, raise to $2000; if no, park
- Raise stops at $2000 per asset OR the wave's total run budget approaches the $5k absolute ceiling

The ceiling itself ($5k per wave) is the **only** native-input event in the system (§A Tier 3).

### B.4 — Engine ground-truth self-repair

When astronomical / engine correctness fails (e.g., PyJHora longitude diverges from JPL/Swiss):

```
1. Pin attempt: re-install PyJHora at the last known-good version; re-run; if pass, log + continue
2. Fallback engine attempt: switch the engine adapter to Swiss Ephemeris direct path
   (PyJHora wraps Swiss; the direct path bypasses the wrapper); re-run; if pass, log + continue
3. Upstream issue auto-file: open a GitHub issue at the PyJHora repo with the failing
   testcase + JPL comparison; continue with the fallback engine; track until upstream fixes
4. Only if all 3 fail: mark the asset PARKED in the wave-close summary; adjacent assets continue
```

Self-repair never blocks the wave; it shifts to a safe execution path and logs.

## §C — Two new SWARM roles (extends BUILD_GUARANTOR_SWARM_CHARTER §E from 12 to 14)

### C.1 — Vimarśaka (विमर्शक — investigator / critic) — 13th role

**Trigger:** runs asynchronously after every merge to main on a wave branch. Watches the Smṛti audit log + the merged diff.

**Method:**
- Adversarial re-read of the merged change against the swarm's own AC-scorecard claim
- Sampled re-execution of a subset of the ACs (e.g., re-run the curl smoke on 20% of routes; re-run the volume-floor check on 1 asset; re-run the verse-traceability check on 5 rules)
- "What could go wrong" review: imagine three failure modes for the merged change; check whether each is detectable in the current code

**Outputs:**
- **GREEN** — no concerns; entry logged to Smṛti at "info" level; native sees only on summary scans
- **AMBER** — concerns worth surfacing but not blocking; Smṛti entry at "warn" level; the next wave session reads them and may pre-emptively fix
- **RED** — concrete regression evidence; Vimarśaka triggers an automatic revert PR (always under AUTONOMOUS_MODE rails — canary checks before promote), emits a Smṛti escalation, run continues with the revert applied

Vimarśaka is the only adversarial signal in the fully-autonomous loop. Without it, the swarm self-judges; with it, every merge gets an external read.

### C.2 — Tier-1 Severity Remediator — 14th role

**Trigger:** activates only when the red-team agent (Pramāṇa adversarial mode) surfaces a class-1 finding (security, correctness, data-loss path).

**Method (elevated rigor vs standard Śilpī patches):**
- Full reproducer authored as a failing test before any fix attempt
- Multi-model consensus on the fix: 3 independent reasoners must agree on the patch design
- 2× canary cycles before promote, with the reproducer test as a mandatory gate
- 30-minute observation window post-promote (vs standard 5 min) before declaring fix-complete
- Vimarśaka audits the remediation specifically, with elevated scrutiny — flags trigger auto-revert immediately, not the standard "amber → next session" cadence
- The original red-team finding becomes a permanent regression test that runs in every subsequent wave's CI

**Output:** GREEN (fix landed + monitored clean) or RED (fix failed; auto-revert; class-1 finding remains open; logged to Smṛti as PARKED for native to triage at next convenient time). PARKED class-1 does not halt the wave; the wave-close summary surfaces it prominently.

## §D — WS-3 acharya gates reframed (AI-assessed default; optional retrospective)

The original WS-3 brief had three external-acharya commission gates (Pilot Close, Canon Close, Post-grounding). Per native directive 2026-06-04, these reframe as follows:

**Default operation (no acharya commissioned):**
- **AI-assessed verdict at each gate.** Cowork (this session, as second-AI reviewer) + multi-model consensus on the sampled rule set. Verdict is one of {pass, pass_with_revisions, fail}.
- Verdict + reasoning + sample logged to `00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_{A,B,C}/ai_verdict.md`
- Wave continues per the verdict branches in the original brief

**Optional retrospective acharya calibration:**
- Native may commission an external acharya periodically (weekly, monthly, or at native discretion) to spot-check the AI's recent verdicts against ground truth
- Acharya verdicts arrive at `00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_{A,B,C}/acharya_verdict.md` and are compared against the AI verdicts
- Disagreements become Vimarśaka audit findings → may trigger re-grounding of affected rules / signals
- The retrospective is informational; it does not synchronously gate any wave

This converts WS-3 from "3 synchronous external pause-points" to "zero pause-points + optional async calibration."

## §E — The single residual native-input event

The catastrophic-runaway cap ($5k absolute ceiling per AUTONOMOUS_MODE §C.4). Mechanics:

- Wave-level total spend approaches $4.5k (90% of ceiling) → swarm emits async Smṛti notification "approaching-ceiling"
- Wave-level total spend hits $5k → swarm **stops the wave at the next safe checkpoint** (idempotent; resumable); emits async Smṛti notification "ceiling-hit-stopped"
- Native sees the notification at convenience (via Smṛti review, email integration, or however the notification surface is wired)
- Native authorizes continuation by writing to a designated file (`00_ARCHITECTURE/CONDUCTOR/ws-N/ceiling_authorization.md`) with a new ceiling value
- Swarm resumes from the safe checkpoint

This is the only event in the system that ever requires a native input, and it's:
- Asynchronous (no waiting; native acts when convenient)
- Budget-driven (not reasoning; the swarm could continue reasoning, just lacks the spend authorization)
- Resumable (no state lost; checkpoint-based resume)

## §F — Activation across the four wave briefs

Each wave brief replaces its "Hard stops" section with:

> **Hard stops:** none synchronous. The wave runs to completion without native intervention.
> All exceptional events route through `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md`:
> Tier-1 auto-resolved by the swarm, Tier-2 decided + Smṛti-logged, Tier-3 (catastrophic-runaway
> cap only) emits async notification per §E. Vimarśaka post-merge audits run asynchronously
> after every merge; class-1 findings route through the Tier-1 Severity Remediator (§C.2).

The four wave-activation briefs are amended in-place to point here. No further per-wave halt specifications needed.

## §G — Smṛti audit surface

Every Tier-2 decision + every Vimarśaka audit + every Tier-1 Severity Remediator activation writes to per-wave Smṛti directories:

```
00_ARCHITECTURE/CONDUCTOR/ws1/smriti/
00_ARCHITECTURE/CONDUCTOR/ws2/smriti/
00_ARCHITECTURE/CONDUCTOR/ws3/smriti/
00_ARCHITECTURE/CONDUCTOR/wsmisc/smriti/
```

Entries are append-only, timestamped, structured (yaml frontmatter + markdown body). Daily summaries are auto-generated at `00_ARCHITECTURE/CONDUCTOR/ws-N/smriti/DAILY_DIGEST_YYYY-MM-DD.md` so the native can read one summary instead of every entry.

The WS-1 cockpit's Asset Inspector surfaces the relevant Smṛti entries inline (per-asset disposition + Vimarśaka audit status), so observability for live builds is in the same place as observability for swarm decisions.

---

*End of AUTONOMY_RESILIENCE_PATTERN v1.0. Three tiers, four provisioning patterns, two new roles, one residual native-input event. Activates the fully-unattended Brahma wave execution per native directive 2026-06-04.*
