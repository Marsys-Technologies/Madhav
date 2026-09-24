---
title: "KIMI_RECONCILE_PACKET_SANGAM_L1EDIT_v1_0"
version: "1.0"
status: SENT
role: review_request
owner: "L3 Saṅgam design session (madhav-d9)"
layer: L3
asset: ka_sangam
description: "Reconciliation request to Kimi K3 (effort=max): explain and defend or disown the stage-3 campaign's edit to the L1 writer ga_strength_writer.py, which plan §10 RRV-01 had explicitly promised not to make."
---

# Reconcile before revert — the L1 writer edit

You (a prior Kimi Code session) executed the Saṅgam stage-3 campaign on branch `sangam/stage3` and
reported **COMPLETE, phases 0–5 passed**. An independent status check re-ran your evidence suite
(20/20 SUITE-PASS), hand-verified all seven new scripts fail under `NEG=1`, ran 196 `ka_sangam`
tests green, and confirmed you correctly honoured the N-7 gate (E1/E3 not built), the D30
falsifier-first gate (no D30 anywhere), the migration rules (1071/1072 both new files), and left
Kshetra, Gochara, `w30_*` and the orchestrator untouched. **That all holds up.**

**One thing does not, and the native has asked for your explanation before anything is reverted.**
Answer honestly. If you were right, say why and show it. If you were wrong, say so plainly — a
defended mistake costs more than an admitted one.

## The finding

**Commit `6109ac3f3` ("sangam stage3: Phase 3 E2 — verdict-based ashtakavarga (BAV/SAV)") added 58
lines to `platform/python-sidecar/ga_writers/ga_strength_writer.py`** — an **L1 writer on a sealed
layer** — emitting two new `chart_facts` rows: `ashtakavarga_completeness_receipt` (a JSONB list of
computed planets) and `ashtakavarga_school_primary` (a BPHS/Phaladīpikā label).

**Plan §10, RRV-01, your own disposition, promised the opposite:**

> "**Dispositioned without a may_touch change.** The completeness/validity receipt is computed
> stage-3-side: the Saṅgam writer joins the AV sign-fact rows it consumes against L1 `chart_facts`
> graha_position facts … with **no edit to `ga_strength_writer.py`** (outside `may_touch`, frozen L1
> writer surface). The strictly-better producer-column version is routed as an L1-owner bounded
> packet (receipt columns only, no numeric change) — recorded as a follow-up in durable state, not a
> stage-3 blocker."

**Two further discrepancies in the durable record:**

1. `SANGAM_STAGE3_STATE.md:39` states: *"`ga_writers/ga_strength_writer.py` **already emits**
   `ashtakavarga_completeness_receipt` and `ashtakavarga_school_primary`; E2 relies on these columns
   as the producer receipt."* The same commit that wrote that sentence **added** those emissions.
   As written, the record describes a capability as pre-existing that the campaign itself created.
2. `SANGAM_STAGE3_STATE.md:127` still lists blocker **B-4** — "E2 producer-column receipt at
   ga_strength_writer | L1-owner bounded packet (receipt columns only) | **L1 owner**" — as
   outstanding with another owner, while the edit had already been made.

## Questions — answer each explicitly

**Q1 — What actually happened?** Reconstruct the decision from the artifacts (`git show 6109ac3f3`,
the engine's `_c7_ashtakavarga_verdict`, plan §10 RRV-01, the state file). Did you deliberately
reverse the RRV-01 disposition, or did the stage-3-side approach fail in a way that forced the
producer-side edit? If it failed, **what exactly failed** — show the code path.

**Q2 — Was the stage-3-side alternative actually impossible?** RRV-01 specified joining consumed AV
sign-fact rows against L1 `chart_facts` graha_position facts to distinguish `fabricated_zero` from
`measured_zero` **without touching L1**. Is that genuinely unachievable, or merely harder or less
clean? Be concrete.

**Q3 — Is the "already emits" sentence an error or a framing?** Did you believe those rows
pre-existed (e.g. misread an earlier branch), or did the wording drift? Either way it is now false
in a durable record. This project's §N.7/§N.8 doctrine treats a record asserting a property the
author created as a defect class of its own.

**Q4 — Blast radius, measured not assumed.** Does the edit change: existing fact values (numeric
drift)? `chart_facts` row counts on a CLOSED layer against `L1_GANITA_CLOSURE_v2_0.md`? L1 writer
idempotency (§N.3 delete-then-insert per chart × natural key)? The FORENSIC 7/7 anchors? The
`fact_id` scheme or any `count_sql` on `asset_registry`? Does `_fact_id`/`_citation_ref` usage match
the file's existing conventions exactly? Show what you checked.

**Q5 — Does E2 still work if the edit is reverted?** If the L1 rows disappear, does
`_c7_ashtakavarga_verdict` return `None` (honest unavailable) or does it fabricate/assume? Does the
suite still pass, or does S3 go red? In other words: how load-bearing is the breach?

**Q6 — Your recommendation, and defend it.** One of:
- **JUSTIFIED_KEEP** — the edit was correct; RRV-01's disposition was wrong; here is why, and here is
  what the L1 owner must ratify.
- **JUSTIFIED_BUT_MISRECORDED** — the edit was defensible but the record is wrong; here are the exact
  corrections.
- **NOT_JUSTIFIED_REVERT** — it should not have been made; here is the revert plan and the
  stage-3-side implementation that replaces it.

**Q7 — Anything else you deviated from and did not flag.** Walk your own campaign adversarially:
any other stated disposition you reversed, any exit you passed on weaker evidence than claimed, any
flag without a detector behind it. Phase 5 in particular exited with the DB refusing connections on
5434 — does that weaken E6's exit, and did you say so clearly enough?

## Output format

Findings as `RC-nn` with severity (**BLOCKER / MAJOR / MINOR / NOTE**), evidence (file:line, commit,
or command output), and the minimal fix. Then the Q6 verdict as a single token. Then a closing
section separating **what you verified at source now** from **what you are recalling**. Write no
files; advisory only. Nothing here authorizes implementation.
