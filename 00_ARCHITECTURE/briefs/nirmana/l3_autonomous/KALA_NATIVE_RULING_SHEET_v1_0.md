---
artifact: KALA_NATIVE_RULING_SHEET
version: "1.0"
status: AWAITING_NATIVE_RULING
date: 2026-09-22
author: strategic session (Claude Code), from the KĀLA readiness audit (cycles 1–14)
source: audit/KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md §"Readiness verdict" + independent re-measurement
does_not_authorize: any build, migration, grant, evidence event or code change. Each ruling below
  becomes authority only when the native answers it.
changelog:
  - "1.0 (2026-09-22): first issue. Six rulings that together unblock the campaign; two corrections to the audit."
---

# Kāla — the six rulings that unblock the campaign

The audit returned **strategy GO-WITH-CONDITIONS; environment GO for non-mutating work, NO-GO for
production builds**. Its decision list has 20 items. These six, taken in one sitting, unblock
nearly all of it. Each has the question, what I measured, my recommendation, and what the
recommendation costs you if I am wrong.

Answer format: `R1: agree` / `R1: agree, but …` / `R1: no — …`.

---

## Two corrections to the audit first (both change Ruling 1)

**Correction 1 — the inheritance question is about 41 upstream assets, not 12 Kāla ones.**
The audit quantified Kāla's *own* old freezes (12 / 7 / 3). But the readiness gate does not block
on those — it blocks on **ancestors**. Measured against production, 2026-09-22:

| Upstream layer | Ancestors Kāla depends on | Frozen under current definition (t3) | Frozen only under a superseded definition | Never frozen |
|---|---|---|---|---|
| L0 `bg_*` | 22 | 0 | 22 | 0 |
| L1 `ga_*` | 13 | 0 | 13 | 0 |
| L2 `bo_*` | 13 | 7 | 6 | 0 |
| **Total** | **48** | **7** | **41** | **0** |

Every one of the 48 was genuinely frozen once. None is frozen under t3 except seven L2 assets.
No session is currently re-freezing L0 or L1 — and the campaign ledger has recorded **zero events
of any kind since 2026-09-11** (11 days). Without a ruling, Kāla waits on a 35-asset L0+L1
re-freeze that nobody is running.

**Correction 2 — `server_reconstructed` is the strong evidence path, not the weak one.**
The audit argued that ~30% of old evidence is `source_kind=server_reconstructed`, "not a live build
receipt", so inheriting it would need a re-run. That misreads the vocabulary.
`platform/scripts/nirmana/README.md` §"The identity split" and the DB trigger in migration 632 define
`server_reconstructed` as the source kind reserved for the **verifier** service account — it is how
*every* `asset_frozen` and `integrity_verified` event is minted, by design. It is the certified path.
This removes the audit's main argument against inheritance. (To be corrected in the audit record.)

---

## R1 — Inheritance under t3  *(unblocks: 22 of 22)*

**Question.** May a freeze earned under a superseded definition count under t3?

**Recommendation — inherit if unchanged, by re-verification, not rebuild; pilot one asset first.**
1. *Principle:* a superseded freeze is admissible under t3 **only if the thing that was frozen has
   not changed since** — the freeze event's recorded `registry_fingerprint_sha256` still matches,
   and the asset's writer digest (which covers its whole local import closure) is unchanged since
   the freeze date. That is an evidence-shaped boundary, not a per-asset judgment call.
2. *Mechanism:* the verifier re-runs `integrity_verified` → `asset_frozen` **under t3** against the
   existing artifact. No rebuild. Anything that fails the unchanged test re-earns from scratch.
3. *Pilot before scale:* do this for **one** L0 asset end-to-end and record the unit cost and
   whether the verifier route accepts a t3 freeze without re-binding the whole t3 chain (L2's cycle
   81 suggests some re-binding is needed — unknown for L0). Then scale to the other 40.

**Why not the alternatives.** Blanket inheritance with no check (B) certifies code nobody looked at
since. Full re-freeze of everything (A) is weeks of L0/L1 work with no session assigned to it.

**If I'm wrong:** the unchanged test admits an asset whose *data* drifted while its code did not.
Mitigation is already in the mechanism — `integrity_verified` re-checks the data, not just the code.

---

## R2 — The headline metric cannot move as defined  *(caps the campaign's outcome)*

**Question.** The delivery target is `LAYER_DATA_ACCEPTED + CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED +
VALUE_EVALUATED`. The ledger's 17 event types can evidence only the first. Design the missing
receipts, or restate the target?

**Recommendation — both, in that order of time.** Restate the headline **now** as two honest
numbers: `Data-accepted N/22` (what the ledger can prove today) and `Delivered N/22` (the full
target, which stays 0 until receipts exist). Commission the three receipt designs in parallel as
their own small piece of work; do not hold asset work for them. This keeps §N.8 intact — no number
is reported that no detector can earn — without making the campaign look stalled for a
bookkeeping reason.

**If I'm wrong:** a two-number headline gets read as the easier number. Guard: every report prints
both, always, with `Delivered` first.

---

## R3 — Who is authorized to start  *(today: formally, nobody)*

**Question.** The only asset brief is Gochara v0.3, status `PROPOSAL_FOR_NATIVE_RULING`. Kshetra and
Sangam briefs do not exist. The layer brief's disposition table covers 1 of 22 identities.

**Recommendation — three-part.**
1. Rule on **Gochara v0.3** (with Astra's amendments) when you are satisfied with it; it becomes the
   first admitted brief and the template.
2. **Kshetra and Sangam briefs gate only their own assets** (and Sangam's seven dependents), not
   the campaign. They are yours and in progress; nothing else should wait for them.
3. The **11 foundation-tier assets with no hard design question** may be admitted on the elevation
   plan's per-asset dimension table plus the audit's traceability matrix as their brief — a
   one-page admission note each, not a full discussion.

**If I'm wrong:** a "simple" asset turns out to hide a design question. Guard: the admission note
must state its truncation/selection behaviour explicitly; any hard cap found sends it to R-list Q8.

---

## R4 — The cascade that erases Kāla's output  *(highest severity)*

**Measured.** Five `kala_*` tables reference `bodha_msr_signals(signal_id)` `ON DELETE CASCADE`
(migration 403, deliberate). L2 rebuilds are delete-then-insert with fresh signal ids. Result on
your chart: 335,403 + 14,868 rows written 2026-08-13, **0 present** after L2's 2026-09-08 rebuild.
Control chart `1c826d5a` (L2 built *before* L3): 336,093 / 336,093 intact. A Kāla freeze today
could be emptied by L2's next rebuild while its freeze event stood.

**Recommendation — two steps.**
1. *Now, no schema change:* a standing rule that Kāla's signal-bound assets are rebuilt **after**
   any L2 signal rebuild, and the readiness query reports `claimed rows ≠ actual rows` as a defect.
2. *Permanent, designed in the Sangam brief:* Kāla rows bind to a **stable signal key + upstream
   generation**, not to a surrogate id that is destroyed on every rebuild. One migration in the L3
   range (1071+), touching only L3-owned foreign keys.

**Rejected:** switching to `RESTRICT` — it would make every L2 rebuild fail and break the L2
campaign. `SET NULL` alone — rows survive but point at nothing.

---

## R5 — PR #2695 (the dispatcher records receipts for code that never ran)

**Measured.** `dispatch_frozen_rebuild.py:28` reads writer digests from a hardcoded path in a stale
developer worktree; every digest there differs from `main`. A dispatched build would mint a
provenance receipt asserting the wrong code identity. #2695 fixes it but is stuck on a
Pūrṇa-owned golden baseline.

**Recommendation — split it; I will do this under the standing authorization unless you object.**
The digest-path fix is independent of the ayanāṃśa-default fix that disturbs Pūrṇa's baselines.
Land the dispatcher fix as its own small PR; leave the ayanāṃśa fix in #2695 for Codex to
re-baseline. No production build before the dispatcher fix is on `main`.

---

## R6 — Builder read access  *(ten-minute decision, one nuance)*

**Measured.** `data_plane_builder` cannot read four tables that three Kāla writers read unguarded:
`bg_transit_moorti`, `bg_synthetic_cohort`, `bg_synthetic_cohort_md`, `phala_rectification`.

**Recommendation.** Grant SELECT on the **three `bg_*` tables** now (migration 1071, same
fail-closed pattern as 1070) — a lower layer read by a higher one is the normal direction.
**Hold `phala_rectification`.** That is Kāla (L3) reading Phala (L4): a dependency pointing
*upward*. Birth-time uncertainty is arguably an L1 fact that Kshetra should receive from below.
Decide that in the Kshetra brief rather than cement the inversion with a grant.

---

## Also needs your eye tonight, outside the six

**Safety gap on live surfaces.** The mortality-exclusion detector is wired into `kala_elect` and
`kala_ritual` only. `ahead`, `now`, `story`, `upaya`, `explain` and `priority` accept the same
free-text intent and never call it; no central layer applies it (verified: the only non-test callers
are `elect.ts`, `ritual.ts`, `lib/kala_sky_pattern.ts`). Product boundary P07/P24. These files sit on
the MCP door Codex is actively changing — recommend a priority request to Codex rather than a
parallel edit.
