---
artifact: PARISESA_REBUILD_SCOPE
sole_writer: SUTRADHARA (aggregates from each lane's SPEC.md §6 dependency declaration)
status: LIVE — updated as streams report
governed_by: NATIVE_DIRECTIVE_NO_REBUILD_WITHOUT_PERMISSION.md (ND-PARISESA-1), PAR-R-10/SP-10
---

# Rebuild scope classes (per PAR-R-10)

Permission is sought **once per class**, with the landed-lane list attached, not per-lane.

## RS-A · L1/L2 writer-layer — chart data is stale until a native-authorized rebuild runs

| Finding | Stream | Writer file | Status |
|---|---|---|---|
| F-62 | S6 | ga_structural_writer.py, ga_vargas_writer.py | CODE-LANDED (merged, main+7459f8837) · DATA-PENDING-REBUILD |
| F-63 | S4 | ga_panchanga_writer.py | pending-rebuild-permission (D/S in progress) |
| F-116 | S4 | bo_upaya.py (L2) | pending-rebuild-permission (D/S in progress) |
| F-35 | S3 | mimamsa writer (mi_sambandha.py evidence_grade) | pending-rebuild-permission — spec originally instructed triggering a rebuild (written before directive existed), self-caught and corrected by S3 |
| F-117 Phase 1 | S3→S5 | bo_upaya.py writer-stored ranking fields | pending-rebuild-permission — Phase 1 only; disclosure-layer Phase 2 (if any) may not need it |

## RS-B · none needed (detector/disclosure-only, or refused-rebuild by ruling)

| Finding | Stream | Note |
|---|---|---|
| F-141 | S6 | PAR-R-9 refused both proposed fixes; rescoped to detector+disclosure, no rebuild in this class |

## RS-C · serving-layer only — code deploy alone closes the finding, no rebuild dependency

Confirmed zero-rebuild-dependency by stream self-audit against ND-PARISESA-1:
- **S1**: all 10 findings (F-09,F-11,F-17,F-18,F-25,F-38,F-43,F-67,F-73,F-123) — registration/dispatch/pointer fixes, no writer touched.
- **S2**: all 16 findings — MCP serving-layer (response_budget.ts/registry_bridge.ts/kala_views), reads already-persisted data.
- **S5**: 10 of 12 (F-03,F-06,F-08,F-10,F-26,F-27,F-133,F-04,F-22,F-70) — pure serving-layer or global-reference repoints, no per-chart rebuild.
- **S4**: 6 of 10 (F-50,F-93,F-120,F-121,F-129,F-130,F-135 — wait, that's 7, recount pending) confirmed serving/query-layer only.

## Ambiguous / pending clarification

| Finding | Stream | Question |
|---|---|---|
| F-05 | S5 | L0 global corpus upsert (brahma_remedy_corpus, ON CONFLICT-safe) — native clarified 2026-08-16: directive covers chart rebuilds only, this is NOT gated. Proceeds normally. |
| F-61 | S5 | Design fork not yet resolved (serving-layer aggregation vs. writer-layer persist) — S5 recommended the spec pick serving-layer to sidestep the gate entirely; pending Stage S. |

## F-62's evidence wording (PAR-R-10, mandatory)

> **F-62: CODE-LANDED · DATA-PENDING-REBUILD** — fixed in the writers and guarded by tests; the
> canonical chart's stored dignity values remain uncorrected until a native-authorized rebuild runs.

VERIFIER standing rule from PAR-R-10: an exit test passing in-worktree is NOT live evidence for any
RS-A (writer-touching) lane. No RS-A lane may be marked LIVE without an actual post-rebuild live
probe.

## Native permission ledger

**GRANTED — 2026-08-16, direct chat message to the conductor, native's own words, verbatim:**

> "All approved for rebuilds"

**Context this was said in:** immediately following the conductor's status update listing the
then-current RS-A class in full (F-62, F-63, F-116, F-35, F-117 Phase 1) and explaining the
"permission requested once per class, batched" mechanism PRATINIDHI had just set up. Conductor's
reading: this is blanket approval for the RS-A class as currently enumerated, standing going
forward as further RS-A findings land (satisfies the native's own original rationale — batch,
don't ask piecemeal, don't redo). Routed to PRATINIDHI for the required countersign before any
rebuild is actually dispatched — this grant record alone does not authorize INTEGRATOR to act;
PRATINIDHI's own sign-off is still required per PAR-R-10's stated asymmetry (a restrictive
relay is honoured on its face; a permissive one needs independent confirmation before an
irreversible write proceeds).

**Practical sequencing:** only F-62 is actually build-ready right now (code merged to main). F-63,
F-116, F-35, F-117 Phase 1 are still in Stage D/S/R — their rebuild happens when THEIR code lands,
under this same standing grant, without asking again, per the native's stated batching intent.


## PAR-R-11 (PRATINIDHI) — COUNTERSIGN WITHHELD

Not a refusal of the grant's validity — a refusal to act on it NOW, on the grounds that rebuilding
for F-62 alone today, then again later when F-63/F-116/F-35/F-117 land, IS the premature-rebuild-
gets-redone outcome the native's own directive was written to prevent. Since 4 of 5 RS-A lanes
aren't ready anyway, waiting costs nothing. PRATINIDHI also declined to read "all approved for
rebuilds" as a standing grant covering future RS-A entrants not yet built/seen — held that a
scoped, one-shot ask per completed class (naming the exact lane list) is the correct mechanism,
consistent with the batching design itself.

**INTEGRATOR instructed to hold.** Unblocks when: all 5 current RS-A lanes are landed/merged/
VERIFIED, then one scoped ask (chart 482012f1, class RS-A, exact lane list) goes to PRATINIDHI for
countersign — expected to be granted per PRATINIDHI's own statement ("I expect to countersign it").

**Also flagged by PRATINIDHI, unresolved:** the merged F-62 commit (7459f8837) cites "F-72" in its
own commit message, not "F-62" — id discrepancy needs reconciling before any close record asserts
either. Routed to INTEGRATOR to investigate.
