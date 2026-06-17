---
artifact: CLAUDECODE_BRIEF_WS3_AUTONOMOUS_ACTIVATION_v1_0.md
canonical_id: CLAUDECODE_BRIEF_WS3_AUTONOMOUS_ACTIVATION
version: 1.0
status: READY_FOR_EXECUTION (parallel to WS-1 and WS-2; WS-2's L2-grounded session waits on this wave's close-tag)
project_codename: Brahma — WS-3 Rule Base + Grounding (Fully Autonomous, External Acharya Eval Async)
authored_by: Claude (Cowork) 2026-06-04
authored_for: Claude Code in Antigravity — Conductor + Two-AI Adversarial Review
governs_under: BUILD_GUARANTOR_SWARM_CHARTER + AUTONOMOUS_MODE
predecessor: tag `legacy-cleanup-arc-complete` (ccc66c77)
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavWS3
branch: feature/ws3-rule-base
no_backup: true
human_gates: NONE for in-loop work; NATIVE COMMISSIONS external acharya eval at three gates (pilot close, canon close, post-grounding) — those are out-of-band, not synchronous merge gates
---

# WS-3 Autonomous Activation — Rule Base + Grounding

The Rule Base (BG-0-6) is the keystone for acharya-grade quality: until rules exist, every L2 signal is ungrounded scaffold. WS-3 builds it fully autonomously per native directive 2026-06-04 — *the AI has more breadth and judgment on Jyotish source texts than either you or me, and the methodology is craft, not domain authority.* Human judgment substitute = external acharya commissioned at three discrete gates (async, non-blocking), not synchronous review.

## §1 The mitigation for the "swarm self-judges" risk

The single risk autonomy doesn't auto-cover is: a rule extracted that LOOKS plausible but misrepresents the source. WS-3 mitigates with three layers:

1. **Mechanical verse-traceability check.** Pramāṇa reads the source verse + the extracted rule, asserts the rule's `condition` and `assertion` are derivable from the verse text (not the executor's prose summary). Failure → reject the rule, re-extract.
2. **Two-AI adversarial review.** The executor swarm produces rules; Cowork (this session, between waves) acts as the second AI reviewer on a sampled batch — independent re-extraction from the same verses; disagreements logged to Smṛti for native review at the next gate.
3. **External acharya commission gates.** Three discrete gates where the native sends a sample of extracted rules to a real Jyotish acharya for spot-evaluation:
   - **Gate A: Pilot close** — after BPHS pilot, ~50 rules sampled
   - **Gate B: Canon close** — after full canon extraction, ~200 rules stratified by source/topic/confidence
   - **Gate C: Post-grounding** — after L2 signals re-derived against rules; sample of signals' rule citations

The conductor pauses at each gate, emits the sample + a covering note to a designated path (`00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_{A,B,C}/`); native commissions the acharya eval; native posts the verdict back; conductor resumes (or revises the extraction method per the verdict).

## §2 Setup

```bash
cd /Users/Dev/Vibe-Coding/Apps
git -C Madhav worktree add ../MadhavWS3 -b feature/ws3-rule-base legacy-cleanup-arc-complete
cd MadhavWS3

mkdir -p 00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_A
mkdir -p 00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_B
mkdir -p 00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_C
```

## §3 Conductor queue

```yaml
# 00_ARCHITECTURE/CONDUCTOR/ws3/session_queue.yaml
wave: ws3
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavWS3
branch: feature/ws3-rule-base
mode: AUTONOMOUS_MODE
max_run_budget_usd: 5000
max_spend_per_asset_usd: 1000  # rule extraction is the documented exception per AUTONOMOUS_MODE §C

sessions:
  - id: method-and-rubric
    role: Racayitā + adversarial Cowork review
    scope: |
      Author the extraction method:
      - Source-text selection (BPHS edition, Jaimini edition, KP reader, Tajaka Neelakanthi — match licensing)
      - Chunking + verse-ID convention
      - Rule schema: {rule_id, source_verse (canonical_id + verse_ref), condition, assertion,
                       scope (chart-element it applies to), school, confidence, caveats}
      - Confidence rubric (principled — textual-strength × cross-text corroboration; NOT a guess)
      - Quality bar (e.g., ≥X% of rules in pilot pass verse-traceability + 2 of 3 LLM reviewers agree)
    acceptance: |
      Methodology committed as 00_ARCHITECTURE/WS3_EXTRACTION_METHOD_v1_0.md.
      Cowork second-AI review attached. No native sign-off needed at this stage — the
      gate is at Pilot Close (Gate A) where the acharya assesses the OUTPUT of the method.

  - id: bphs-pilot
    depends_on: [method-and-rubric]
    role: Śilpī (lead) + Pramāṇa (verse-trace verifier) + Review Swarm ×5
    scope: |
      Extract rules from BPHS using the method. Target: ~500-1000 rules covering the
      canonical structural areas (yogas, dignities, aspects, dashas, sade sati, ashtakavarga,
      muhurta, remedies — the major chapters).
      Each rule emitted carries verse_ref + source_text excerpt; Pramāṇa rejects any
      rule whose assertion can't be derived from the cited verse text.
    acceptance: |
      ≥ pilot's quality bar passes Pramāṇa + Review Swarm + Cowork adversarial sample.

  - id: gate-a-acharya
    depends_on: [bphs-pilot]
    type: external-eval-gate
    scope: |
      Sample 50 rules stratified across topics (yoga, dignity, dasha, remedy, etc.) and
      confidence tiers. Write the sample + covering note to
      00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_A/sample.md.
      Conductor pauses; emits Smṛti entry "WAITING_FOR_NATIVE_ACHARYA_VERDICT".
      Native commissions external acharya; posts the verdict at
      00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_A/verdict.md.
      Conductor resumes when verdict.md is present.
    verdict_branches:
      pass: continue to canon extraction
      pass_with_revisions: route to method-and-rubric (revise rubric per acharya notes), then re-run pilot
      fail: HALT — native + Cowork redesign

  - id: canon-extraction
    depends_on: [gate-a-acharya:pass-or-pass-with-revisions]
    role: full swarm — Śilpī parallel across texts
    scope: |
      Apply the (possibly revised) method to the full canon — BPHS + Jaimini + KP + Tajaka.
      Parallel extraction per source; central convergence check after.
      Estimated ~5000-15000 rules total depending on rubric strictness.
    acceptance: |
      Per-source quality bar passes; convergence check: rules from different sources on the
      same topic surface their agreement / disagreement (feeds the concordance asset).

  - id: gate-b-acharya
    depends_on: [canon-extraction]
    type: external-eval-gate
    scope: |
      Sample ~200 rules stratified by source + topic + confidence tier.
      Same gate mechanics as Gate A.

  - id: concordance-build
    depends_on: [gate-b-acharya:pass]
    role: Śilpī + Pramāṇa
    scope: |
      Build brahmagyan.concordance — cross-school agreement / divergence index over
      the full Rule Base. For each topic: agree / qualify / conflict, with lineage trace.
      Per master arch §C "Concordance silent-handling fix" — distinguish silent (orthogonal)
      from contradicts; silence is not a "no" vote.
    acceptance: |
      Per-topic entries link rules across schools; conflicts surfaced (not flattened);
      provenance / lineage present.

  - id: ws2-handoff-tag
    depends_on: [concordance-build]
    role: Sūtradhāra
    scope: |
      Open WS-3 PR; CI green; swarm merges; tag `ws3-rule-base-complete`.
      WS-2's l2-bodha-grounded session, which has been polling for this tag, now releases.

  - id: gate-c-acharya-post-grounding
    depends_on: [ws3-handoff-tag, ws2-tag:ws2-l2-grounded-complete]
    type: external-eval-gate
    scope: |
      After WS-2 re-derives signals against the Rule Base, sample 100 signals.
      For each: present the signal + its cited rule_id + the rule's source verse.
      Acharya assesses: does the signal correctly invoke the rule, and does the rule
      correctly capture the verse?
    verdict_branches:
      pass: WS-3 fully closes
      pass_with_revisions: route specific rules back to extraction; WS-2 re-grounds the affected signals
      fail: HALT — significant rework

  - id: wave-close
    depends_on: [gate-c-acharya-post-grounding:pass]
    role: Sūtradhāra
    scope: tag `ws3-acharya-validated-complete` on main; WS-3 sealed.
```

## §4 The two-AI adversarial slot (Cowork's role)

Between WS-3 sessions, Cowork (this conversation) is automatically routed batches of extracted rules for adversarial re-extraction. The pattern:

1. The Conductor writes a sample batch to `00_ARCHITECTURE/CONDUCTOR/ws3/cowork_review_batch_{N}.md`
2. Cowork (in a normal conversation turn) re-extracts the same verses, compares output, logs disagreements to Smṛti
3. If disagreement rate > 15%, Smṛti escalates — conductor pauses for native to assess whether the method or the rubric needs revision

This makes Cowork a genuine Review Swarm ×6 (the 5 in-CC reviewers + Cowork as the 6th, with separate model context).

## §5 Acceptance criteria

- AC-1: Method + rubric committed and reviewed (no acharya gate; methodology is craft)
- AC-2: Pilot rule set passes ≥ quality bar; Gate A acharya verdict ∈ {pass, pass_with_revisions}
- AC-3: Full canon extracted; Gate B acharya verdict ∈ {pass, pass_with_revisions}
- AC-4: Concordance built; cross-school agreement / divergence surfaced
- AC-5: `ws3-rule-base-complete` tagged; WS-2's L2-grounded session releases
- AC-6: Post-grounding Gate C verdict ∈ {pass, pass_with_revisions}
- AC-7: `ws3-acharya-validated-complete` tagged; instrument can pass external acharya review

## §6 Hard stops — none synchronous

The wave runs to completion without native intervention. All exceptional events route through `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md`. Notable per-WS-3 routings:

- **Method+rubric disagreement (executor vs Cowork)** → Tier-2: multi-model consensus (3 reasoners) on the disputed rubric clauses; majority wins; Smṛti logs both positions.
- **Gate A/B/C acharya verdict** → **REFRAMED per pattern §D**: AI-assessed by default (Cowork + multi-model consensus); the wave continues per the verdict branches (pass / pass_with_revisions / fail) without external commission. Optional retrospective acharya calibration is async and informational.
- **Cowork-adversarial disagreement >30%** → Tier-2: route to deep-fix escalation (§B.1) with the disagreement evidence; only escalates to method-revision if disagreement persists across the escalated attempts.
- **Spend approaches cap** → Tier-2 auto-budget raise (§B.3); rule-extraction assets have a $1000 per-asset cap per AUTONOMOUS_MODE §C exception, can raise to $2000 via the same pattern.
- **Verse-trace failure (Pramāṇa false-positive)** → Tier-2 disposition classifier defaults to STUB the affected rule with TODO marker; wave continues; verse-trace mechanism investigation routes to a Smṛti-logged follow-on session.
- **Wave hits absolute $5k ceiling** → Tier-3 (only event): async notification per pattern §E.

## §7 Out of WS-3 scope

| # | Item | Owner |
|---|------|-------|
| 1 | L2 signal re-derivation (consumes WS-3's rules) | WS-2 l2-bodha-grounded session |
| 2 | Bodha.remediation re-derivation (consumes WS-3's rules + L0 remedy_corpus) | WS-2 l2-bodha-grounded session |
| 3 | The actual acharya commissioning + payment | native (out-of-band) |
| 4 | Translation quality of source editions | scope of L0 brahmagyan.texts in WS-2 (not here) |

---

*End of WS-3 Autonomous Activation. Method → BPHS pilot → Gate A acharya → full canon → Gate B acharya → concordance → tag → WS-2 grounds → Gate C acharya → seal. Cowork sits as the 6th Review Swarm slot.*
