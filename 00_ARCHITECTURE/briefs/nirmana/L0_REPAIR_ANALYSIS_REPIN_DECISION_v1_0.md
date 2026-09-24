---
artifact: L0_REPAIR_ANALYSIS_REPIN_DECISION
canonical_id: L0_REPAIR_ANALYSIS_REPIN_DECISION
version: "1.0"
status: L0_REPAIR_REPIN_APPROVED
decision_id: NATIVE-2026-09-24-L0-REPAIR-REPIN
date: 2026-09-24
approved_state: 101171f76517fa3c6b0b44fa9d1cc46358612eee
protected_baseline: 954d6c119a0d95725ea9c2ead1a9a4ff5cf8a7a0
scope: "Successor admission of the L0, L2 and L3 analysis-layer pins (nirmana-analysis-layer-pins.json) for PR #2727. No other layer, no data."
recorded_by: "Claude Code session (scribe). The approval below is the native's, transcribed from the session; it is NOT a signed commit."
---

# L0 repair — analysis-layer re-pin: recorded decision

This records one decision so the pins tool's authority chain
(`AUTHORITY_BINDINGS` → this document → its bytes → its decision binding →
the approved commit) has something real to point at. It does not create the
decision; it records that it was made, by whom, on what understanding, and
exactly what it covers.

**Approved state (authority identity):** `101171f76517fa3c6b0b44fa9d1cc46358612eee`
— the tip of `l0/vedha-and-frame-repair` at the moment of approval, i.e. every
commit of PR #2727 up to and including the registry-seed/census fix. The
successor pins record this same commit as their `source_commit`, so what was
approved and what is pinned cannot diverge.

## 1. The approval, verbatim, and its provenance

Provenance, stated plainly: these are the user's messages in an interactive
Claude Code session on 2026-09-24, transcribed by the session. The session
cannot cryptographically verify who typed them; it records that the operator
of the native's project session gave them. The tool patch instruction (2b)
arrived after the session context was re-read under a different account
identifier than the one that gave the approval (2a). Anyone who needs
stronger identity than "the session's operator" should countersign this file
in a later commit.

**2a. Approval of the re-pin** (after a plain-language explanation of what is
superseded — see §3):

> Yes, I approve it. go ahead and do it.

**2b. Choice of path when the pins tool proved unable to admit a successor
from a branch cut after the data-plane squash delivery** (options were: patch
the tool / wait for its owner / merge red and follow up):

> Yes, please wrap up all three.  → selected: "Patch the tool, finish it (Recommended)"
> Notification question → answered: "Igonore" (no notification to be sent)

Nobody was notified anywhere as part of this decision, by instruction.

## 2. What is being approved

Admission of one successor generation each for **L0, L2 and L3** in
`platform/src/generated/nirmana-analysis-layer-pins.json`, recording that the
writer-source digests of 38 assets legitimately changed because PR #2727
edited five source files:

| edited file | writer digests it moves |
|---|---|
| `brahmagyan/l0_transit.py` | 2 (`bg_transit_rules`, `bg_transit_engine`) |
| `brahmagyan/l0_phaladeepika_vedha.py` | 2 (`bg_vedha_malefic_scale`, `bg_phaladeepika_latta`) |
| `services/ka_vedha_gochara/logic.py` | 1 (`ka_vedha_gochara`) |
| `brahmagyan/l0_ephemeris.py` | 34 (23 `bo_`, 5 `bg_`, 6 `ka_`) — a shared upstream module |
| `pipeline/orchestrator/service_probes.py` | 23 (`bo_`) plus the generic probe digest |

A writer's digest hashes its transitive source closure, so editing a shared
module moves every writer that imports it. **No L2 writer's own logic changed.**
That is why 32 of the 38 moves are classified `derived_import_change`.

Classifications (the tool refuses any set that does not cover exactly the
changed assets):

- `approved_intentional_change` — writers whose own module was edited:
  `bg_transit_rules`, `bg_transit_engine`, `bg_vedha_malefic_scale`,
  `bg_phaladeepika_latta`, `bg_ephemeris`.
- `approved_intentional_and_derived_import_change` — `ka_vedha_gochara`
  (its `logic.py` was edited AND it imports the changed `l0_ephemeris`).
- `derived_import_change` — every other changed asset: the other four `bg_`
  writers and five other `ka_` writers that import `l0_ephemeris`, and all 23
  `bo_` writers (which import `l0_ephemeris` and `service_probes`).

## 3. What "superseding" means here, and what it does not touch

The pins are a code-inspection ledger, not chart data. Each writer's evidence
identity includes a fingerprint of its code; each layer carries a batch seal
over its writers' fingerprints. When code legitimately changes, the seal must
be re-issued as a **new generation**, with the previous one archived — not
overwritten. This decision approves exactly that.

- Predecessor generations are archived whole in the pin file's `history` and
  stay re-derivable; each successor names what it supersedes.
- No chart data, reading, prediction or calibration value is touched.
- The other layers (L1, L4, L5) and every writer whose digest did not move keep
  their existing evidence untouched; the tool does not hash a layer seal into
  per-asset identity precisely to avoid that "treadmill".
- Until the seals are re-issued the only thing blocked is *filing new
  code-acceptance evidence* for L0/L2/L3; the instrument keeps running.

## 4. The tool change this decision also authorises

`nirmana_analysis_layer_pins.py` could verify, but not admit, a successor whose
evidence commits were severed from ancestry by the data-plane squash delivery
(`fa9857f00`); every review-artifact commit and the definition snapshot
`5142109f7f219ea860f859e322646f79d875bee8` must otherwise be an ancestor of
HEAD, and for a branch cut from the squashed `main` none can be. Commit
`149d2add5` adds two narrow fallbacks, both requiring
`--protected-baseline-commit` and both leaving strict behaviour unchanged when
it is absent: (1) review artifacts not reachable from HEAD are validated as an
exact one-parent squash delivery already on the baseline; (2) existing
definition bindings are carried verbatim only when byte-identical to the
baseline's and covering L0–L5, with the candidate's membership still
re-derived and compared. It adds ten tests, including that a tampered artifact
set, an artifact the baseline does not carry, a mismatched snapshot label and a
wrong membership are all still refused.

## 5. Standing conditions this decision does not lift

1. **L3 must not be rebuilt yet.** `services/ka_vedha_gochara/writer.py` hardcodes
   `uncited_extension: False` for every `house_vedha` row and its selector now
   includes the six Rāhu/Ketu rows PR #2727 declared UNSOURCED; a rebuild would
   stamp unsourced node doctrine as machine-readably cited. The structured
   `source_qualification` / `corpus_verifiable` columns (Gochara WP9) are the fix.
2. Production `kala_vedha_gochara` (267 `house_vedha` rows, 2 charts) still
   carries the refuted `BPHS Ch.29` citation and pre-repair Venus pairs.
3. `bg_sarvatobhadra_grid` remains empty; see PR #2727 item 4.
4. The successor pins name protected baseline `954d6c119…` as their historical
   snapshot. If `main` advances before merge, the pins must be re-admitted
   against the new baseline; this decision then applies unchanged.

## 6. What this decision does not decide

It does not approve any change to L1, L4 or L5, any data rebuild, any
production write, or any widening of the tool's relaxation beyond §4.
