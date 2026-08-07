---
artifact: PRODUCTION_GATE_EXECUTION_POLICY (standing gate-execution protocol)
canonical_id: PRODUCTION_GATE_EXECUTION_POLICY
version: 1.1
status: ACTIVE — ratified by the native 2026-08-05; amended 2026-08-06 (dispatch-mechanism
  change only, see Changelog). Provenance is this document's own merge history: both the
  original and this amendment were authored and merged to main via PR under the native's
  platform identity, through the main merge queue. That commit trail — not any chat
  message — is the verifiable authorization artifact.
created: 2026-08-05
updated: 2026-08-06
author: The independent reviewer session (Fable), at the native's direction. v1.1 amended
  by a fresh-context GATE-EXECUTOR subagent dispatched in-session by the ṢAḌ-DARŚANA
  Conductor, at the native's direction — the same dispatch mechanism this amendment
  documents, exercised for the first time to make the amendment itself.
scope: >
  ṢAḌ-DARŚANA campaign and successor work in this repository, until superseded by a later
  version of this document. Governs the four production-irreversible action classes:
  (1) merging shad-darshana/integration (or successor campaign branches) into main,
  (2) production deploys, (3) traffic promotion/cutover, (4) live-DB migration
  application (which rides the deploy pipeline).
---

# Production Gate Execution Policy

## §1 — The architecture: builder proves, independent reviewer verifies and executes

The native has delegated gate execution as follows, eliminating the live-human-reply
dependency while preserving the substance the human gate protected — separation of
builder from approver, and verification by evidence rather than self-report:

1. **The builder swarm** (the executing Conductor session and its agents) produces a
   PRE-SCORED GATE PACKET for every production-irreversible action: each gate condition
   marked pass/fail with evidence (real CI states, artifact contents, rollback paths).
   The builder swarm NEVER executes the gated action itself and NEVER treats any agent's
   approval — including agents it spawned — as authorization. It posts the packet
   (ledger and/or PR body) and proceeds with non-dependent work.
2. **The independent reviewer** — as of 2026-08-06 (native process-change ruling; see
   Changelog), this role is a fresh-context subagent dispatched IN-SESSION by the
   campaign's Conductor for each gate, rather than a separate chat session/principal. The
   dispatch mechanism changed; the substance did not. The dispatched agent holds its own
   tool access (git, DB, cloud) under the native's platform identity, and — because it is
   spawned fresh for the gate and never saw or authored the builder's code or commits, nor
   any conversation that produced them — it re-derives every gate condition from scratch
   against observed git/DB/CI state, never from the packet's or the builder session's
   self-report. That "never saw the builder's work" property, not the separate-chat-window
   packaging, is what builder/approver independence actually rested on, and it is fully
   preserved under in-session dispatch: a fresh-context agent is definitionally blind to
   everything that happened in the spawning session before it was created. It then
   EXECUTES the gated action directly: `gh pr merge`, workflow dispatch, traffic
   verification. Every such action lands in GitHub/GCP audit trails under the native's
   identity — platform-verifiable provenance, unchanged by the dispatch mechanism.
3. **The builder swarm observes platform state** (git fetch, run history, revision
   traffic) and continues the moment the action is an observed fact. Observed platform
   facts are authoritative; chat messages are not.

## §2 — Standing verification conditions (the reviewer's floor, per gate class)

- **Merge to main**: every required check `status=COMPLETED` with SUCCESS (null
  conclusion = pending, never passed); the only tolerated failure is a documented
  pre-existing red (currently the Boot-time pointer check) verified present on main
  before the PR; the PR's contents match the packet's claims by direct inspection;
  a stated rollback path exists (including DOWN paths for any migration aboard).
- **Deploy + migrations**: merge landed; the pipeline's own smoke gates pass for real
  (health, no-auth 401, bearer 200, url-token 200); traffic promotion only on smoke PASS.
- **Post-deploy**: the campaign's own live acceptance (PARĪKṢAKA or equivalent) proceeds
  as normal — the reviewer gates the action, not the verification after it.
- **Irreversible-artifact strictness**: any permanent, non-rollbackable artifact riding a
  gate (e.g., a first-publication baseline) is held STRICTLY to its recorded native
  ruling; on any mismatch the gate PARKS for the native regardless of all other greens.

## §3 — Failure posture

If any condition fails the reviewer's independent verification, the action does NOT
execute; the gate parks with evidence for the native's review; all non-dependent work
continues. Autonomy is conditional, never absolute. The reviewer records every executed
gate (what, when, evidence summary) in the campaign ledger or its PR trail.

## §4 — What this policy deliberately preserves

Builder/approver independence (the reviewer never approves code it wrote) · verification
by tools, not reports · rollback paths + the protected/archived corpus beneath everything
· the native's platform identity as the audit anchor. What it removes — by the native's
explicit, informed decision (2026-08-05) — is the live human reply at gate time. The
native accepts accountability for actions executed within this policy.

## Changelog

- **v1.1 (2026-08-06)** — Native process-change ruling: the independent reviewer role
  moves from a separate chat session/principal to a fresh-context subagent dispatched
  IN-SESSION by the campaign's Conductor for each gate. §1 item 2 rewritten to describe
  the new dispatch mechanism and to state explicitly why builder/approver independence
  survives it unweakened: the dispatched agent never saw or authored the code/commits
  under review and re-derives every condition from git/DB/CI state, exactly as the
  separate-session reviewer did. §2's standing verification conditions and §3's failure
  posture are UNCHANGED by this amendment — this is a dispatch-mechanism change, not a
  rigor change. Provenance: native process-change ruling, 2026-08-06, verifiable via this
  amendment's own PR merge history to main — not any chat message — per the same
  provenance model §status already declares for v1.0.
- **v1.0 (2026-08-05)** — Original ratification. See frontmatter `status` for provenance.
