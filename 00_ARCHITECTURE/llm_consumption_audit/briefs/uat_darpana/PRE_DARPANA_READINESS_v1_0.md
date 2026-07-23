---
artifact: PRE_DARPANA_READINESS
type: READINESS CHECKLIST (residual fixes + verifications before UAT-DARPANA opens)
version: 1.0
status: SUPERSEDED by PRE_DARPANA_READINESS_v1_1.md (2026-07-24 swarm close) — retained in
  place for audit trail per repo archival convention. Read v1.1 for current per-item status;
  UAT-DARPANA remains HELD, exit condition not yet met.
context: VIDHI-PŪRṆATĀ merged to main (PR #728, squash 350d8455). Governance-close PR #729
  BLOCKED on a failing Governance Gates check post-branch-update. This list makes the Darpana
  test a test of the REAL, fully-served instrument — not of deployment gaps or known holes
  wearing a defect costume.
---

# PRE-DARPANA READINESS — full-coverage checklist

## Tier A — MUST FIX before Darpana (would corrupt or hollow the test)

**A-1. PR #729 governance close — diagnose + merge.** Required check "Governance Gates
(drift/schema/edge/native-literal/py-sidecar)" fails with exit 2 after the branch was updated
onto post-#728 main (head 074fd0dc). Likely: the SESSION_LOG/CURRENT_STATE close content was
authored against pre-#728 state and now trips a drift or schema cross-check. Run the gate
locally, fix the content (never the gate), merge. SESSION_LOG completeness policy (ONGOING_
HYGIENE §D) requires the close to land before a new initiative opens.

**A-2. Deploy the merged planner to the LIVE serving surface.** #728 changed platform +
platform-mcp code and shipped migrations 462/463 — but merged ≠ deployed. CI itself notes the
MCP smoke battery ran in "plan mode; LIVE mode needs a deployed server." If the deployed MCP
still serves pre-#728 code, Darpana tests the OLD planner and every wave gain is invisible.
Deploy; then live-verify through the real connector: (a) `plan_retrieval` for a spirituality
question returns the new `spirituality_deepdive` floor; (b) a keyword-free "tell me about my
money" compiles the FULL deepdive incl. elevation bands; (c) an unclassifiable question
returns the Pūrṇa-Ādhāra foundational floor; (d) migrations 462/463 applied on the live DB.

**A-3. CR-131 — Gochara temporal serving, root-caused and made real.** E-1 wired
activation/forecast/election primitives into every deepdive, but data-reachability is
UNCONFIRMED — and we already hold the likely cause from D-4b's close: `ka_gochara_sweep` for
482012f1 sat at 165/300 substeps, `state='error'` (6h Cloud Run timeout), with the forward
span 2026–2055 only background-materializing. If `kala_gochara_windows` is part-empty, every
Darpana timing question hits a half-dark crown jewel. Fix: re-dispatch the sweep to completion
for 482012f1 (resumable, §N.3-safe, post-memoization it is ~600x faster than the run that
timed out), then live-verify all three views return real, shape-correct rows through the
connector. Close or honestly re-scope CR-131.

**A-4. D7 `spouse_karya` → `progeny_karya` L1 writer mislabel.** Confirmed genuine writer
bug. The new `progeny_deepdive` floor consumes D7; a mislabeled karya marker risks polluting
progeny answers with spouse semantics. Fix the `ga_*` writer label (FROZEN WriterBase contract
respected), rebuild the affected rows chart-scoped (delete-then-insert idempotency), verify
482012f1 (+ Abhinandan 1c826d5a) reads `progeny_karya`.

**A-5. Remedy-engine cluster decision (CR-67 + CR-69).** `remedy_scan` "contributes nothing
to interventions today" and `intervention_synthesis` has no leverage_index axis — yet the
depth-doctrine now puts the intervention layer in EVERY deepdive by default, and Darpana's S5
stream ("help me act") tests it head-on. Decide: (a) minimal repair so remedy_scan returns
real domain-joined rows (preferred if a bounded fix exists — investigate first), or (b)
explicit accept-as-dark with the completeness receipt disclosing it, so S5 grades the honest
gap rather than mistaking it for silent breakage. NO fabricated remedy ranking to look alive.

**A-6. Timing-anchor cluster decision (CR-66 + CR-37).** `taranga_curve` rides every
deepdive's machine band but Phala domain anchors are zero (timing spine hand-assembled), and
yoga-activation dates are missing (CR-37). Same decision shape as A-5: bounded repair vs
explicit accept-as-dark. Note A-3 may substantially supersede this cluster — with Gochara
windows live, the temporal machine band has a real spine regardless; assess AFTER A-3 lands.

## Tier B — VERIFY before Darpana (no code expected; confirmation required)

**B-1. End-to-end plan→execute smoke on ONE question per new/changed floor** (spirituality,
education, progeny, marriage-with-timing, health-with-ayurdaya, foundational-fallback,
multi-domain union, pointed single-fact): the compiled plan's every floor item either serves
rows or surfaces its truthful known_gap in the completeness receipt. This is a reachability
smoke, not the UAT — no grading, just "no silent empties."
**B-2. Standing-predictions surface (E-2)** returns the real open ledger claims (Sat–Jupiter
Apr–Aug 2027; Ketu-MD shape; Venus-MD 2034) for a wealth/timing plan.
**B-3. CR-130 dark-flag serves correctly**: a spirituality plan's completeness receipt cites
CR-130 for the Jaimini spiritual yoga family — visible, not silent (the fix itself is Tier C).
**B-4. Connector environment for Darpana answerers**: the naive-session recipe reaches the
DEPLOYED server (post-A-2), all new tools visible, entitlement clean for 482012f1.
**B-5. Sealed split + §11 governance untouched** by all Tier-A work (standing assertion).

## Tier C — ACCEPT-AS-DARK for Darpana (explicit, disclosed; fix later informed by UAT data)

- **CR-130** Jaimini spiritual yoga family (pravrajyā/sannyāsa detectors) — new L1 detector
  work; floor flags it honestly. Darpana will measure how much it actually hurts S1-spirit.
- **CR-61** arudha/UL ranking (raw positions serve; ranking absent).
- **CR-16** chart-keyed special-lagna access residual; **CR-24** mechanism motif first-class
  serving; **CR-64** nakshatra ranking; **CR-68** mechanism_retrodiction surface; **CR-73**
  bespoke dosha cancellation residual; **CR-30** KP sublord dedicated face.
- Rationale: each is honestly disclosed in-plan via known_gap; fixing all pre-UAT would delay
  the test for months and rob it of its purpose — measuring which darks USERS actually feel.
  The UAT's probable_layer diagnosis converts this list into an evidence-ranked backlog.

## Exit condition

Tier A all CLOSED + Tier B all VERIFIED → publish this file v1.1 with per-item closure
evidence → UAT-DARPANA opens (single consolidated kickoff prompt from Fable, battery drafted
against post-fix reality incl. targeted probes for every Tier-C accepted dark).
