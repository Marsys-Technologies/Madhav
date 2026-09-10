---
canonical_id: CG6_NATIVE_ACCEPTANCE_PACKET
version: 1.0
status: AWAITING_NATIVE_REVIEW
campaign: pariprashna-experience-assurance-v3
authored_by: closeout-session (Phase G)
authored_at: 2026-08-30
verified_against_live: true
verification_time: 2026-08-30T (session), tracker read at as_of 2026-08-29T20:50:23Z
---

# CG-6 Native Acceptance Packet — Pariprashna Experience Assurance Programme v3.0

**Read this when you wake up. It takes about ten minutes. Two things below need your decision — everything else is a status report for your information.**

## Executive summary

Tonight's session resumed a closeout that had stalled silently for ~16 hours overnight with a critical fix sitting unmerged. It merged that fix, closed all six assurance streams (S1–S6), closed gates CG-0 through CG-5, ran a mandatory red-team pass, and now stages this packet for your review. The headline finding — your private ~79KB chart corpus was being injected into other people's chart syntheses for over 16 hours — is fixed, deployed, and independently re-verified live; a forensic check tonight found no evidence any of the exposed content was ever actually captured or persisted anywhere retrievable. The campaign sits at **92% complete** with every gate closed except CG-6 (Native Accepted, reserved for you) and CG-7 (downstream of CG-6). This session did not and will not fire `native_acceptance` — that action is yours alone. One operational note before you fire it: the control plane's own prerequisite check currently blocks that command until a small, mechanical bookkeeping step is completed (detailed under "Before you run this" below) — it is not a judgment call, just a missing verification record.

---

## Two things that need YOUR decision (not the swarm's call)

### 1. Disclosure question — the 16-hour real third-party data exposure

V3-E-016/B1 (below) means your chart corpus was actually injected into 5 of 6 production charts' synthesis prompts — 4 of those charts belong to other real people — for roughly 16+ hours before this session started. The fix is in and verified. The open question is whether this warrants any disclosure to the affected parties beyond the silent code fix.

Relevant context for your decision: a full database forensic check run tonight found **zero evidence that any of the exposed content was actually captured or persisted anywhere retrievable** — see Residual #2 below for the detail. That doesn't erase the exposure window; it bears on how you weigh the disclosure question.

### 2. V3-E-054 — a safety-gate flag deliberately shipped OFF

Found via Phase E referral reconciliation: live code confirms a safety-gate flag is deliberately shipped in an OFF state ("P1 pre-authorization" posture). This is **not a fresh code defect** — it's a real, deliberate product/policy decision that is already reflected in the code. It sits outside the Surrogate's authority to rule on unilaterally; it needs your explicit confirmation that this is the posture you intend.

---

## Gate ledger (live, verified against `/api/projection` at time of writing)

| Gate | Name | Status | Notes |
|---|---|---|---|
| CG-0 | Control Plane Ready | CLOSED | |
| CG-1 | Takeover Reconciled | CLOSED | |
| CG-2 | Safe to Test | CLOSED | |
| CG-3 | Stream Complete | **CLOSED tonight** | verifier event `638f2c91-11c9-451a-b8b9-10417d984eb0` — confirmed live: `verification_accepted`, actor `verifier`, role `INDEPENDENT_VERIFIER`, stream `P3`, 2026-08-29T20:21:47Z |
| CG-4 | Integrated Assurance | **CLOSED tonight** | verifier event `d87d6bcb-08eb-4b4a-8a87-8b05e9f01448`, confirmed live: stream `P4`, 2026-08-29T20:39:14Z; campaign completion at close ≈85% (session record) |
| CG-5 | Operationally Proven | **CLOSED tonight** | verifier event `b504f419-c134-4ea8-b73f-3b55a90a7bd8`, confirmed live: stream `P5`, 2026-08-29T20:50:23Z; campaign completion at close ≈92% (session record) |
| CG-6 | Native Accepted | **OPEN — reserved for you** | Do not close except by your own `native_acceptance` event. See "Before you run this" — the control plane currently blocks this until one bookkeeping prerequisite clears. |
| CG-7 | Release Closed | OPEN | Downstream of CG-6; not startable until you accept. |

**Live tracker numbers, confirmed at read time:**
- `completion_pct`: **92.0** (`earned_campaign_points`: 92.0 / `planned_campaign_points`: 100.0, `readiness`: `GATES_ONLY`)
- Integrity check (`/api/integrity`): **`ok: true`** — `expected_hash`, `actual_hash`, and `materialized_hash` all equal (`b222ae754e57d230651f072b6049cf3f63863359cb4cf6b81e77b27cc7e8ce84...`); event-log hash-chain intact.

---

## The headline finding, fully closed

**V3-E-016 / B1 — real-chart context leak.** Your ~79KB private chart corpus was being injected into every chart's synthesis prompt — 5 of 6 production charts, 4 belonging to other real people — live for approximately 16+ hours before this session began.

- **Fix:** PR #1655 ("Pariprashna V3 B1: fix V3-E-016 real-chart context leak (CRITICAL, S3)") — merged 2026-08-29T17:06:53Z, deployed, live-re-proofed on production.
- **Independently ratified twice:**
  - Native Surrogate ruling, event `fb54d19b-...`: RATIFY V3-E-016 as fixed and verified for the full 6-chart blast radius.
  - Independent Verifier, event `209addec-...`: confirmed live — `verification_accepted`, `finding_id: V3-E-016`, `status: ACCEPTED`.

**Related fix — V3-E-061.** A red-team pass this session found that a citation-redaction fail-open path could *also* have leaked genuine content (not just a cosmetic empty token). Proven via a synthetic PII-shaped test token. Fixed by PR #1659 (merged 19:15:32Z) — now fails **closed**, architecturally, not pattern-list-dependent. Surrogate ruling `d9fd0274-...`: disposition COMMISSION_FIX_THIS_CAMPAIGN (a real defect, but not a confirmed data exposure — not an emergency fast-path).

---

## Six streams closed — honest accounting, not padded

| Stream | Fixes | Scenarios | Notes |
|---|---|---|---|
| **S1** Navigation/Shell | 2 real fixes (PR #1610, #1614) | 10/10 | 2 minor residuals: breadcrumb color-contrast deferred with named ownership ask; CI-retargeting process gap noted |
| **S2** Conversation/Reading | 5 pre-session fixes + 2 this session (PR #1661) | 30/30 | V3-E-062 fully fixed, V3-E-060 partially fixed (honest residual disclosed); 1 duplicate voided; 2 referred to S4; 1 deferred pending native/design decision; 1 external (V3-E-061, see above) |
| **S3** Answer Quality | Headline finding (own numbering, same bug as B1) closed; V3-E-032 (CRITICAL) confirmed fixed via S4's PR #1646; V3-E-033 (MEDIUM) Surrogate-ruled to defer re-scoring | 47/60 executed | 13 honestly excluded — 5 gated by an unrelated feature flag, 8 blocked by the chat door's own clarification-classifier intercepting seed attempts. Both real, reproducible, live-system behaviors, recorded as `scenario_executed` / `outcome: STRUCTURALLY_EXCLUDED` with per-item reasons — not silently dropped |
| **S4** Pipeline/Door Parity | 10 real fixes (PRs #1620–1624 pre-session, #1643–1645 this session) | 54/54 | V3-E-056 (CRITICAL) absorbed via REJECT→fix→ACCEPT adversarial catch; 6 referred onward; 1 already tracked elsewhere; 1 no-action-needed; 30 honestly deferred. One recording defect (a referral's justification copy-pasted from a different finding) caught by independent verification, corrected, re-verified |
| **S5** Security/Privacy | 9 findings, all fixed and merged (incl. #1615, extended beyond original scope per Surrogate ruling) | 45/45 | A scenario-count discrepancy traced to a since-fixed tracker dedup bug — resolved, not padded. One low-severity residual: dead API endpoint, fail-closed, zero data risk |
| **S6** Performance/Resilience | 1 HIGH fix (PR #1662, MCP planning-latency disclosure) + 1 measurement-correction fix | 14/31 measured live | 17 honestly excluded — 16 because the load/chaos/CWV harness described in the stream's own spec doesn't exist yet (explicitly deferred per the *original* closeout plan's own instruction, not a shortcut invented tonight), plus 1 bundled adjacent infra gap |

---

## Surrogate rulings this session

(Native Surrogate authority — **not** native acceptance. Each recorded as `decision_recorded`, actor role `NATIVE_SURROGATE`, confirmed present in the live tracker.)

- **V3-E-016 ratification** (`fb54d19b-...`) — see headline finding above.
- **Control-plane-upgrade blocker** deferred as non-blocking residual (`e526c889-...`).
- **PR #1615 scope extension** (`5e1a5a17-...`) — ruled EXTEND beyond its original empty-table scope, to cover two live data-bearing tables (364 + 195 real rows).
- **B-002 (RLS gap)** (`9f5e1658-...`) — recorded accepted-risk, not commissioned for a full remediation build.
- **V3-E-061 disposition** (`d9fd0274-...`) — COMMISSION_FIX_THIS_CAMPAIGN, not an emergency fast-path (real defect, not a confirmed data exposure).
- **Three Phase E referral dispositions** — deferred-with-named-owner for 6 items (see Residual #1).

---

## Residuals and dispositions — full honest list

1. **Six deferred cross-stream referrals**, not yet fixed, now honestly re-opened with named target-stream ownership: V3-E-042 (→S1), V3-E-044 (→S5), V3-E-031 (→S6), V3-E-053 (→S6), V3-E-014 (→S4), V3-E-021 (→S4). A Phase E audit found these had been marked "referral filed = VERIFIED" by the referring stream without the target stream actually picking them up — now correctly tracked as open, owned, deferred work.
2. **Historical-replay architectural gap** (found by red-team): `/consult/continue`, `/regenerate`, `/resume` replay persisted conversation content verbatim without re-hydration or re-linting — meaning any pre-fix leaked content, had it been captured, would still be served today. A full DB forensic check tonight found **zero actual leaked content was ever captured** on any of the 4 affected real charts (3 had no conversations at all; the 1 that did was an empty shell with zero messages). No remediation needed for actual harm; the architectural gap itself is real and should be hardened in a future session (add re-hydration/re-lint on replay paths). This bears directly on native decision question #1 above.
3. **S5-V3-E-024** — dead API endpoint, fail-closed, zero data risk, still broken, low priority.
4. **B-002 (RLS gap)** — accepted-risk per Surrogate ruling above; not a fresh residual, but this packet is the standing record so it stops being re-discovered as new in future waves.
5. **Two unrelated open PRs (#1608, #1513)** have real merge conflicts from tonight's rapid merge cadence — need a rebase, not urgent, unrelated to Pariprashna's own scope.
6. **Ceremony audit-trail quality** (found by red-team): 6 of S5's `verification_accepted` events carry no verdict/note text. The underlying work is independently corroborated as real (PRs merged, matching diffs) — this is a documentation-discipline note for future sessions, not a re-verification requirement.
7. **Terminology note:** the tracker's `remediations[].status: VERIFIED` label applies identically to real code fixes and to honestly-verified "no fix, deferred" dispositions (~half of the 73 total findings across all streams are the latter). The underlying event text is honest in every case, but a dashboard read of "N VERIFIED" could be misread as "N fixed." Worth a future tracker UI/label clarity improvement.
8. **S6 §10.3 load/chaos/CWV harness** (16 scenarios) — explicitly deferred to a dedicated future session per the original plan's own instruction; spec already written; not a CG-3/campaign blocker.

---

## Red-team pass (run this session, mandatory before seal)

Three angles, all completed:

- **Leak-completeness** — found the historical-replay gap (Residual #2), otherwise clean.
- **Ceremony-integrity** — found the audit-trail-thinness, integrity≠veracity, and VERIFIED-terminology notes (Residuals #6, #7); spot-checked PRs all genuine; one full stream (S1) manually walked end-to-end with no illegitimate transition found.
- **Production-safety** — fully clean: migrations correctly scoped across all ~350 grantable tables (not just the 3 targeted), deploy state 3-way confirmed aligned, control-plane healthy, no interference with the concurrent Nirmana campaign.

---

## Merged PRs tonight — verified live via `gh pr view`

All confirmed **MERGED** as claimed:

| PR | Title | Merged at (UTC) |
|---|---|---|
| #1655 | B1: fix V3-E-016 real-chart context leak (CRITICAL, S3) | 17:06:53 |
| #1651 | A2: governed FINDING_FREEZE plan-revision path | 17:18:53 |
| #1654 | A5: split/restructure EDIR_V3_REGISTER for concurrent writes | 17:31:19 |
| #1658 | docs: land closeout plan v2.0, supersedes v1.0 | 17:44:10 |
| #1615 | test(audit): narrow amjis_app audit_log grant (E-001) | 18:33:12 |
| #1659 | fix: V3-E-061 citation register-leak fails closed | 19:15:32 |
| #1640 | docs(S2): convergence-readiness, 30/30 truth-checked | 19:29:22 |
| #1660 | docs(S1): result packet v1.3 — CG-3 closure | 19:36:44 |
| #1661 | fix(S2): V3-E-062 + V3-E-060 partial disclosure | 19:48:43 |
| #1662 | fix: disclose MCP-door planning latency (S6-V3-E-003) | 20:00:43 |
| #1663 | docs(S2): closure ceremony record, v3.0 → v4.0 CLOSED | 20:12:31 |

**One correction to the session's own record:** PR **#1664** ("docs(pariprashna): Phase E integration record (CG-4 closure)") was listed as merged tonight but is verified **still OPEN** as of this packet's writing — `mergeable: MERGEABLE`, CI green (all checks `SUCCESS`, one `SKIPPED` by design), not yet merged into `main`. The file it lands (`PHASE_E_INTEGRATION_RECORD_v1_0.md`) does not yet exist on `origin/main`; the CG-4 gate-closure evidence in the tracker cites it by `repo://` path, which currently resolves only on the PR branch (`docs/pariprashna-phase-e-integration-record`), not `main`. This does not affect the tracker's own CG-4 status (closed via an independent verifier event, `d87d6bcb-...`, confirmed live and re-checked above) — it only means the doc that narrates that closure is one merge away from being visible on `main`. **Recommended next action:** merge #1664 (docs-only, CI green) so the CG-4 evidence path resolves correctly on `main`.

---

## Before you run this: one mechanical prerequisite

The control plane's own validator (`control.py`) requires the P6 phase to be at 100% completion **before** it will accept a `native_acceptance` event — checked directly against the live database tonight:

- P6 ("Native Acceptance") has exactly one work item, `P6:completion` (5 campaign points), currently **not accepted** — P6 sits at **0% completion** as of this writing.
- Per `control.py`, firing `native_acceptance` right now would be **rejected** with `GATE_PREREQUISITE: "native acceptance requires complete P6 evidence and closed CG-5"` — even though CG-5 itself is closed.
- Getting P6 to 100% is a mechanical bookkeeping step, not a judgment call: it needs (a) an `INDEPENDENT_VERIFIER` to submit a `verification_accepted` event on stream `P6` with payload `{"work_item_id": "P6:completion", "finder_actor_id": ..., "fixer_actor_id": ...}`, evidence citing this packet; then (b) the `PROGRAMME_INTEGRATOR` to submit `work_item_accepted` on stream `P6` referencing that verification event.
- **This session deliberately did not perform steps (a)/(b)** — no tracker-mutating events were fired beyond read-only verification, since only the packet itself was requested. Whoever runs the morning session should complete this pair of events first (it requires no native judgment — it's the Verifier/Integrator confirming this packet itself is accurate, exactly like every other stream closure in this campaign), and only then will the one-command native acceptance below actually succeed.

---

## One-command native acceptance

Once the P6 prerequisite above is cleared, this is the exact command — do **not** run this on the swarm's initiative; it fires only when you decide to accept.

```bash
curl -X POST http://127.0.0.1:8787/api/events \
  -H "Authorization: Bearer $(jq -r .tokens.native /Users/Dev/.pariprashna-assurance-control/p2-credentials.json)" \
  -H "Content-Type: application/json" \
  -d '{
    "actor_id": "native",
    "idempotency_key": "native-acceptance-2026-08-30",
    "event_type": "native_acceptance",
    "stream_id": "P6",
    "expected_stream_seq": 0,
    "payload": {
      "decision": "accepted",
      "summary": "Native review of CG6_NATIVE_ACCEPTANCE_PACKET_v1_0.md complete; campaign accepted."
    },
    "evidence": [
      {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/CG6_NATIVE_ACCEPTANCE_PACKET_v1_0.md"}
    ]
  }'
```

Notes on this command, verified live against `control.py` and the control-plane database tonight:

- `actor_id: "native"` maps to role `NATIVE` with `P6` in its authorized stream scope — confirmed in the live actor table.
- `stream_id` must be exactly `"P6"` — the validator rejects any other value for `native_acceptance`.
- `expected_stream_seq: 0` is correct **as of tonight** — the `P6` stream has no prior events. If the P6 prerequisite steps above (or anything else) write to stream `P6` first, re-check the current sequence via `GET /api/projection` before firing, or the request will be rejected with `SEQUENCE_CONFLICT`.
- `evidence` is required (non-empty) — `native_acceptance` is a completion event; the array above is the minimum, pointing at this packet.
- `idempotency_key` should be changed if this exact command needs to be re-run under a different logical decision — reusing the same key with the same payload is safely idempotent; reusing it with a different payload will be rejected as an idempotency conflict.
- This event, once accepted, updates `gates["CG-6"]` to `CLOSED` directly (confirmed in `control.py`'s fold logic) — it does not go through a separate gate-closure step.

---

## Turnkey post-acceptance runbook (for the morning session — no re-planning needed)

Once you fire `native_acceptance` and CG-6 closes:

1. **Integrator closes CG-6 → CG-7.** CG-7 ("Release Closed") becomes eligible once CG-6 is closed; the Integrator submits the `gate_closed` event for `CG-7` (targeting phase `P7`), linked to the appropriate independent verification per the same pattern used for CG-3/CG-4/CG-5 above.
2. **Seal the campaign with a final report.** Write `PARIPRASHNA_V3_CLOSE_REPORT_v1_0.md` in `00_ARCHITECTURE/briefs/pariprashna_assurance/` — model it on the close-report structure used by prior campaigns cited in `CLAUDE.md` §N.8 footer (e.g. `PURNATA_CLOSE_REPORT_v1_0.md`), summarizing: final gate ledger, all residuals and their disposition, and pointers to this packet + the CG-4/CG-5/CG-6/CG-7 evidence chain.
3. **Reconnect to the roadmap.** Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — mark Pariprashna v3 complete, record what it unblocks (the campaign's own charter/plan documents in this same directory name the downstream work this clears — pull from `AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md` or the closeout plan v2.0 landed by PR #1658 for the specific unblock list).
4. **Append a `SESSION_LOG.md` close-checklist entry** per `CLAUDE.md` §H and `SESSION_CLOSE_TEMPLATE_v1_0.md` — this closes the session formally; do not skip it even though the campaign itself is sealed by step 2.

None of these four steps require re-deriving anything from scratch — this packet, the tracker's live gate ledger, and the PR list above are the complete input.

---

*End of packet. Written by the closeout session (Phase G), verified against the live tracker (`/api/projection`, `/api/integrity`) and `gh pr view` at authoring time. `native_acceptance` was not fired by this session.*
