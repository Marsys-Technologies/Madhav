---
artifact: FOUNDATION_INTEGRITY_CAMPAIGN_v1_0.md
canonical_id: FOUNDATION_INTEGRITY_CAMPAIGN
version: 1.0
status: CURRENT — the governing plan for the ground-up data-integrity rebuild of L0–L4 before L5
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The multi-phase campaign to take the instrument's L0–L4 substrate to a PROVABLY SOUND foundation —
  data-grounded, no assumptions, no reliance on docs/code claims. Triggered by the convergence-cluster
  discovery (one symptom hid 3 critical root causes) + the 16 map-fill anomalies. Native rulings:
  (1) COMPLETE the deep audit L0→L4 BEFORE fixing anything; (2) FULL LATITUDE to fix right + rebuild from
  scratch (empty-system window — only the native's chart + unbuilt demos exist; no migration debt);
  (3) Cowork plans + authors prompts, native runs in Antigravity, data evidence reviewed together at gates.
---

# Foundation Integrity Campaign — L0→L4 Ground-Up

## §1 — Why this campaign exists (the realization)
This session found, one at a time: the all-Jupiter convergence (a hardcoded fallback), then — when we
VERIFIED rather than accepted "looks fixed" — THREE deeper critical bugs underneath it (eligibility-score
all-NULL → fake prioritization; fact_value_num semantically overloaded → 95% silent skip; YOGA class
crowded out → 0 rows). Separately, the map-fill surfaced 16 anomalies including ≥3 more degenerate-uniform
bugs (CGM all-0.506, resonance all-0.28, muhurta all-identical). **The pattern is now undeniable: this is
not a set of isolated bugs — it is a CLUSTER of root causes, and they live UPSTREAM of where they surface.**
A bug at L2 silently corrupted L2→L3→L4. We have been fixing symptoms; this campaign fixes the foundation.

**The window:** there is essentially NO production data to protect — the native's chart + 2-3 unbuilt demo
profiles. This is the one-time chance to fix the foundation correctly, with full latitude (schema changes,
rebuilds, re-architecture) and ZERO migration debt. It will not stay open once customers onboard.

## §1.5 — REFRAME (native 2026-06-23): the deliverable is CORRECT CODE, not corrected data
**Data is DISPOSABLE — regenerable on demand via the Nirmāṇa Build tracker.** The goal of Phase B is that
every WRITER'S LOGIC is correct, so that ANY build (the native's now, a customer's later) produces sound
data. This SIMPLIFIES Phase B significantly:
- **Drop the careful data-rebuild/migration/cascade machinery** — there is no production data to preserve.
- Phase B = **CODE-FIX waves, bottom-up (L0→L4)**, each followed by a **scoped PROOF-BUILD of that layer's
  writers** — NOT to preserve data, but as an INTEGRATION TEST: confirm the layer's code produces correct
  output WHEN FED CORRECT UPSTREAM INPUT (a writer's logic can't be validated on bad upstream — ph_pratikara
  is meaningless on all-Jupiter input). The proof-build's data is throwaway.
- Bottom-up still holds: fix + prove-build each layer on the now-correct input from the layer below.
- **The campaign ENDS in ONE full end-to-end Build** of the native's chart via the tracker — that single
  clean build IS the seal-grade integration proof (every fixed writer runs in dependency order, fed correct
  upstream, in one pass). The per-wave gate verifies CODE CORRECTNESS (does this writer produce right
  output?), not data preservation.
- The DAG/dependency ORDER still matters (for fix sequence + the final build's run order); the elaborate
  "downstream waits for upstream REBUILD" scheduling does not (one final build handles it).

## §2 — The governing doctrine (non-negotiable, native-ratified)
1. **DATA-FIRST, NOT DOCS/CODE.** Every soundness claim is proven against the ACTUAL DATA (distribution
   census + re-derivation), never "the code looks right" or "the doc says." Every bug this session was
   found in the data and MISSED by code-reading + tests. "Looks fixed" is not fixed — the Moon "8-graha"
   result LOOKED fixed and hid 3 critical bugs. Trust the method, not the appearance.
2. **DIAGNOSE COMPLETELY BEFORE FIXING.** The full deep audit L0→L4 (all 69 assets, the DEEP method — not
   2-row glances) completes and produces the COMPLETE root-cause map BEFORE any fix is applied. No fixing
   one cluster while others hide. (Phase A below.)
3. **FIX RIGHT, GROUND-UP, FULL LATITUDE.** Fix each root cause the CORRECT way — schema changes,
   re-architecture, full rebuilds allowed — bottom-up (L0→L4), because a lower-layer fix invalidates
   upper-layer data. No minimal-diff compromises, no backward-compat burden. (Phase B+.)
4. **ASSESS ≠ FIX, gated.** Diagnosis classifies (SOUND / SUSPECT / WRONG / DEFERRED); the native decides
   each fix at a gate. Cowork plans + authors; Antigravity runs; data evidence reviewed together.
5. **VERIFY EVERY FIX AGAINST DATA + the live cockpit** (the §7.9 seal-guard discipline). A fix is not done
   until the rebuilt data PROVES the logic sound — re-derived, distribution-checked, on the live revision.

## §3 — The two campaign phases

### PHASE A — COMPLETE DEEP DIAGNOSIS + IMPACT/SEQUENCING (fix nothing)
Finish the formal L0→L4 soundness audit (spec: `L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md`) with the DEEP method
on all 69 assets, bottom-up, one layer per session, gated. **Each layer's audit ALSO produces, for every
asset it finds WRONG, the DOWNSTREAM-IMPACT CHAIN (§3.5).** Outputs five `L<n>_SOUNDNESS_REPORT.md` + a
consolidated `FOUNDATION_ROOT_CAUSE_MAP.md` that:
- lists every confirmed root cause (data-proven), classified WRONG / DEFERRED / SOUND;
- maps how they INTERCONNECT (which upstream bug causes which downstream symptom — the dependency chains);
- folds in the 16 map-fill anomalies + the 3 convergence-cluster bugs as seeds to confirm/deepen;
- groups the WRONG findings into ROOT-CAUSE FAMILIES (see §4) so Phase B fixes patterns, not symptoms;
- **contains the MASTER REBUILD SCHEDULE (§3.5) — the dependency-ordered wave plan Phase B executes.**
**Gate A:** native + Cowork review the complete map + the rebuild schedule. Only when the FULL picture +
the sequence are certain does Phase B begin.

### §3.5 — DOWNSTREAM-IMPACT + REBUILD-SEQUENCING (the executable-plan layer — native-mandated)
A list of broken assets is not a fix plan. The next session must execute a SEQUENCE, because most assets
feed downstream systems that inherit their data — and a downstream asset must NOT be rebuilt until ALL of
its broken upstreams are fixed (else the corrected fix re-bakes stale/wrong data). The audit produces:

**(a) Per-WRONG-asset downstream-impact chain** (recorded in the layer report, while context is fresh):
the COMPLETE TRANSITIVE set of every asset that depends on it (directly + indirectly, all layers up) and
therefore must be REBUILT once it's fixed. Use the registry `depends_on` transitive closure (the code
exists: `src/lib/build/plan.ts` transitiveDownstream / `asset_runner.py` compute_downstream_closure).
**BUT VERIFY EACH EDGE against what the writer ACTUALLY READS** — depends_on has been WRONG before
(bo_laksana declared deps on bg_rules/ga_structural but code reads only chart_facts). A wrong edge = a
wrong rebuild plan (rebuild the unnecessary, or MISS the necessary → silent stale data). Data-first applies
to the GRAPH too: confirm each declared edge by grepping the writer's actual FROM/reads; flag any
declared-but-unread edge (over-declared) and any read-but-undeclared edge (under-declared — the dangerous
one, a hidden dependency the cascade would miss).

**(b) Master rebuild schedule (at Gate A consolidation — needs the full cross-layer picture):** a
dependency-ordered WAVE PLAN over ALL confirmed-WRONG assets + their transitive downstreams:
- Each asset gets a "READY-TO-REBUILD WHEN: [all these upstream fixes done]" condition (the multi-upstream
  wait — a downstream depending on 2+ broken assets waits for the LAST of them).
- Topologically sort so every wave only rebuilds assets whose every broken-upstream is already fixed+rebuilt
  in a prior wave. (topoSort exists in plan.ts — reuse it.)
- Note where a single fix triggers a LARGE downstream rebuild (cost/time flag) and where independent broken
  assets can be fixed+rebuilt in PARALLEL (no shared dependency).
- Output: an ordered "Wave 1 fixes [X], rebuilds [closure of X]; Wave 2 fixes [Y] (was waiting on X) …"
  that the Phase B session runs top-to-bottom with no guesswork. This IS Phase B's execution spine.

### PHASE B — GROUND-UP REMEDIATION (fix, bottom-up, data-verified)
Fix the confirmed root causes L0→L4. Each layer: fix → rebuild from scratch (native's chart) → VERIFY the
rebuilt DATA proves soundness (re-derivation + distribution + live cockpit) → gate → next layer up. A layer
is not "done" until its data is provably sound AND every layer below it already is. Sequenced so no fix
rests on unsound lower data. (Detailed phase breakdown authored AFTER Gate A, when the map is known — we do
not pre-plan fixes for bugs not yet fully diagnosed.)

## §4 — The root-cause FAMILIES (working hypothesis — Phase A confirms/revises)
Grouping the known leads by SHARED root cause, so Phase B fixes the pattern once wherever it appears:
- **F1 — Degenerate-uniform values** (a column that should vary collapsed to one constant): all-Jupiter
  convergence, CGM all-0.506 (#3), resonance all-0.28 (#4), muhurta all-identical (#13). Likely:
  scoring/differentiation formulas not implemented or stubbed. *Per asset: WRONG (compute-broken) vs
  DEFERRED (not-yet-built) — re-derivation decides.*
- **F2 — Field-semantics overload** (one column storing different meanings per row-type, so consumers
  mis-read it): fact_value_num = house_num OR aspect-degree OR frequency → 95% DISPOSITOR silent-skip.
  Likely siblings elsewhere — Phase A greps for other overloaded JSONB fields read positionally.
- **F3 — Missing/NULL ranking & eligibility** (a prioritization input never populated → selection becomes
  storage-order accident): eligibility_score all-NULL → LIMIT-60 picks by insertion order; YOGA crowd-out.
- **F4 — Silent fallbacks / empty-catch** (code substitutes a plausible constant or swallows a failure when
  input is missing): the `.get(k,'Jupiter')` family, ph_pratikara's empty-except, the Capricorn JD path.
  Phase A's silent-default code scan inventories all of these.
- **F5 — Epoch / anchoring errors** (a derivation anchored to the wrong reference point): jivana_parva
  life-chapters start 1950 not the 1984 birth (#11).
- **F6 — Inert / mis-calibrated gates** (a threshold that filters nothing): orb_strength binary 0.7/1.0 →
  the 0.45 gate is a no-op.
- **F7 — Vocabulary / taxonomy drift** (same concept, different labels → joins silently miss): CDLM
  spirituality/character/wealth vs canonical (in fix).
- **F8 — Data-quality at source** (corrupt inputs): OCR garble in scanned BPHS texts (#1), chart_divisionals
  graha='ALL' null rows (#2).

## §5 — Sequence (the critical path)
```
PHASE A — diagnose (fix nothing)
  A0  Convergence cluster: already deep-diagnosed (3 root causes confirmed) — FOLD into the map, do not re-audit.
  A1  L0 audit (foundation — bg_ephemeris first; everything inherits it)        → L0_SOUNDNESS_REPORT → GATE
  A2  L1 audit (the computed chart — ga_positions vs FORENSIC; ga_structural)   → L1_REPORT → GATE
  A3  L2 audit (bodha — CGM #3, resonance #4, eligibility-source, CDLM, laksana) → L2_REPORT → GATE
  A4  L3 audit (kala — ka_yojaka predicate pipeline, jivana_parva epoch, sangam) → L3_REPORT → GATE
  A5  L4 audit (phala — muhurta #13, the composers; re-audit after fixes)        → L4_REPORT → GATE
  A6  CONSOLIDATE → FOUNDATION_ROOT_CAUSE_MAP (families, interconnections)       → GATE A (full certainty)
PHASE B — fix ground-up (only after Gate A)
  B1  Fix L0 root causes → rebuild → verify data sound → GATE
  B2  Fix L1 → rebuild → verify → GATE
  B3  Fix L2 (incl. eligibility population, CGM/resonance, field-overload) → rebuild → verify → GATE
  B4  Fix L3 (ka_yojaka pipeline, convergence, jivana epoch) → rebuild → verify → GATE
  B5  Fix L4 (per-signature confirmed-correct on FIXED inputs; muhurta; ph_pratikara) → rebuild → verify → GATE
  B6  Whole-stack rebuild of the native's chart end-to-end → live-cockpit seal-grade verification
THEN  L4 seal (now on a provably-sound foundation) → L5 Mīmāṃsā opens on confirmed ground.
```

## §6 — What this protects
- **L5 makes sense only if L0–L4 is real.** L5 calibrates predictions against lived events; if the
  substrate has flat spots (uniform CGM, fake eligibility, missing YOGA), L5 learns from noise. This
  campaign is the precondition for the L5 investment being worthwhile — the native's stated goal.
- **The empty-system window.** Doing this now = no migration, no broken customers, full freedom to fix
  right. Deferring it = doing the same surgery later with real data and real users on top. Now is correct.

## §7 — Open (decided at Gate A, not now)
The detailed Phase B fix specs are authored AFTER the diagnosis is complete — we do not design fixes for
bugs not yet fully characterized (that's what produced the MD-lord and ph_pratikara mis-fixes). Phase A's
job is to make Phase B's design obvious + complete.

---
*End. Two phases: COMPLETE deep data-grounded diagnosis L0→L4 (fix nothing) → GATE A → ground-up fix +
rebuild + data-verify, bottom-up. Doctrine: data-first, diagnose-fully-first, fix-right-full-latitude,
verify-against-data. The empty-system window makes this the one-time chance for a provably-sound foundation
before L5.*
