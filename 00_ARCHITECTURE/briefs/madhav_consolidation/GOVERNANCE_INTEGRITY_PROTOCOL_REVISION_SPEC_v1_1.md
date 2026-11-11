---
artifact: GOVERNANCE_INTEGRITY_PROTOCOL_REVISION_SPEC
version: "1.1"
status: DRAFT
date: 2026-11-11
---

# Additive session-open qualification

This revision adds truthful Codex Desktop provenance to the existing [Governance and Integrity Protocol](../../GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md) and [session-open template](../../SESSION_OPEN_TEMPLATE_v1_0.md). Keep the canonical paths and stable reference anchors. The protocol advances to 1.1 and the template to 1.3. Existing approved CLI identifiers and current controls stay in force.

A qualified observer obtains client and worktree metadata, effective instruction fingerprints and access scope, and current coordination readback. The existing validator compares separately supplied observations with the handshake, validator file digest, current session and worktree, and unexpired lease and scope. A caller supplies observations through the in-process interface after authorization and independent verification. YAML alone cannot establish that trust. This consistency check does not grant access or replace actual protected controls.

Independent verification covers preserved CLI and tool cases, wrong or unsupported profile, mismatched client/session/worktree/validator observations, expired, stale or superseded lease, and failed access or instruction checks. Keep the existing mandatory fields, exclusion checks, canonical fingerprints and decision-register acknowledgment. Preserve historical validation outcomes at their original pins. The revision adds no retired mirror authority or secondary governance system.

Source qualification checks the parser and its observable behavior. Installed qualification separately requires actual current client startup, effective access and scoped session evidence. Report those states independently. Revert the parser, its tests and the two documents as one source change if the admission path fails its obligations. Retain the previous valid records and their validator revisions.

The validator checks the backing file digest and may revalidate identical observations during their freshness window. A qualified observer must load the immutable reviewed candidate afresh and independently check live custody for each session qualification. Do not reuse historical evidence for another session, scope or validator revision. The parser does not record receipt consumption.
