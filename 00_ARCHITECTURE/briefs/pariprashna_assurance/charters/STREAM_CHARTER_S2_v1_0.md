---
artifact: PARIPRASHNA_STREAM_CHARTER_S2
version: "1.0"
status: FROZEN — registered as tracker plan revision 4
date: 2026-08-27
stream_id: S2
stream_name: Conversation & Reading Experience
frozen_by: Session A, Phase A5
---

# Stream charter — S2 (Conversation & Reading Experience)

- **Owner (actor to register):** `lead-s2`
- **Independent verifier:** `verifier` (Sonnet/high default; escalate per finding severity)
- **Baseline SHA:** `3686772b7000cf9e1d391b97eccc008ef167b8d0`
- **Deployed revision pin:** see S1 charter's identical note — `amjis-web` deployed at `cafa894ee7cfc2e86743bb92625e7faf293aec0a`, stale behind baseline due to an unrelated Nirmana-campaign deploy-pipeline failure (PR #1601). Re-check at your own open.
- **Worktree/branch:** fresh worktree off `origin/main` @ baseline SHA, branch `pariprashna/v3-s2-conversation-reading`
- **Approved ceiling:** 8h wall-clock; spend by judgment
- **Entry gate and dependencies:** CG-2 CLOSED (`031e03fc-7685-4c17-af34-bba115318246`); P2→P3 RESOLVED (`02d8c469-7ceb-440c-be10-a910cc6bcaa8`)

## Credential status (RESOLVED — A2)

Same as S1's charter: pre-existing guest-role test principal `hunQRYVJ5Ec2mQnJnutK7AoQnsO2`, scoped to chart `1c826d5a` only. See `../A2_CREDENTIAL_LANE_OUTCOME_v1_0.md` for the mint recipe and proof.

## Test subject

Synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` ONLY. Native's real chart `482012f1-710e-4a25-994a-93821f5871aa` out of bounds.

## Scope (test plan v2.1 §5.1 viewport/working/dock/composer rows + §8 for these regions; journeys J2, J3, J5, J6, J9)

**Primary file territory:** answer/streaming components, the reducer, working-region components, right dock, composer — under `platform/src/components/pariprashna/` (the non-shell/non-sidebar surface) plus `platform/src/lib/pariprashna/` reducer/replay logic.

**Region battery (test plan §5.1):**
- **Main viewport:** a focused, stable reading surface — settled blocks never jump/mutate; only one live tail changes; scroll follows only while the reader hasn't intentionally scrolled away; tables/verses/honest-gaps/errors/clarification-asks/prediction-cards read as their actual semantic type. Proof: complete a deep reading; inspect a table and a difficult finding; interrupt and resume without losing place.
- **Working region:** progress informative, calm, truthful — no internal ids, no fabricated certainty. **Testable against the §4.3.5 progress-cadence check** (test plan §4.3 item 5: 1s-cadence snapshots across a deep turn must show monotone, phase-accurate, elapsed-accurate advancement on both doors — the live seed defect this guards against, EDIR E-003, is a frozen progress message during synthesis). Proof: can the agent-as-user distinguish "working"/"waiting"/"needs clarification"/"finished" at every 5s sample of a deep turn?
- **Right dock:** citation chips open the exact evidence card (source, evidence grade, confidence, relevance, caveat); alternatives/falsifiers discoverable; empty states explain absence. Proof: answer "why should I trust this sentence?" and "what would change it?" from the dock alone.
- **Composer:** labelled input, predictable focus, keyboard/IME/paste/touch/mobile-keyboard usable; Send/Stop/retry/validation work; model/depth/length settings either genuinely affect the outcome or are absent (GAP-8's cosmetic-picker seeded failure is the specific case to re-check). Proof: toggle each setting, confirm the resulting turn is intelligibly different where promised.
- **Errors and recovery:** failure explains what happened, protects entered text, identifies incomplete content, safe next step, never silently promotes a partial answer. Proof: deliberately kill the network / press Stop mid-turn; recover without reconstructing context by hand.

**Mandatory journeys (test plan §5.2), your assignment:** J2 (standard interpretive reading: stream, inspect a citation, open a non-selected interpretation, understand a falsifier), J3 (timing/deep-dive: inspect a semantic table/verse, retain place through a long stream), J5 (clarification: answer the instrument's question; resulting turn retains context without accidental re-submission), J6 (interruption: Stop/disconnect mid-turn; return via replay or disclosed incomplete state), J9 (mobile: journeys 1/2/4/6 on a 390×844 viewport with software keyboard open — note J1/J4 are S1/S3 territory by topic but J9's mobile re-run of them is yours by region if the failure is viewport-specific; refer to the owning stream if the root cause is theirs).

**Additional named scenarios (elevation §11.2 S2 block):** settled-block stability, live-tail behavior, caret/scroll behavior, reduced-motion/zoom cases (test plan §8.1's hard interaction assertions apply directly here).

**Cross-cutting (§8, shared territory with S1 by component, not topic):** §8.1 visual/interaction regression and §8.2 accessibility for viewport/working/dock/composer specifically.

Freeze your own scenario denominator from the concrete list above before executing.

## Evidence rungs required

STATIC → REPLAY → INTEGRATION → LIVE, per finding. Progress-truthfulness (§4.3.5) and interruption/recovery scenarios specifically warrant REPLAY-or-LIVE proof (a synthetic pipeline-degradation fixture or a real deployed interruption), not STATIC code-reading alone.

## EDIR_V3 seeds

`../EDIR_V3_REGISTER_v1_0.md` — file S2 findings as `V3-E-0NN`, `stream: S2`. Cross-territory referral (elevation §8.3) for anything actually rooted in S1's shell or S3's synthesis-quality territory.

## Posture

Browser + replay-fixture heavy. Sonnet/medium finder/investigator; Sonnet/high verifier default. Native Surrogate (Opus/high) for scope/product decisions. Closure per elevation §8.1 lifecycle: result packet, independent verification, integrator acceptance (CG-3 contribution).
