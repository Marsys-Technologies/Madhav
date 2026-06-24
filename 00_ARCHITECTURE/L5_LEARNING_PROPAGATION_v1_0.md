---
artifact: L5_LEARNING_PROPAGATION_v1_0.md
canonical_id: L5_LEARNING_PROPAGATION
version: 1.0
status: DRAFT — backbone architecture for how L5 learning propagates through L1–L4 (overlay, dedup, bounds)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  Specifies HOW the calibration/learning L5 computes is applied to the layers below it — which assets
  it touches (L1→L4, never L0), how the deterministic base stays strictly segregated from the adapted
  value, how a single correction is prevented from being double-counted along a multi-consumer
  consumption path (the deduplication problem), how the modulation magnitude is bounded + evidence-
  scaled, and how the single master `learning_influence` toggle subtracts ALL of it cleanly. Grounded
  in the REAL asset lineage extracted from the code (see §2), not the architecture docs alone.
native_decisions_2026_06_22:
  - "Attach model = OVERLAY (L5 writes to its own tables keyed to upstream ids; base L1–L4 NEVER mutated)"
  - "Propagation scope = FULL L1→L4 (L0 excluded — global/classical, priors locked)"
  - "Segregation = deterministic value and adapted value strictly separated at every node; NO deduplication of shared assets"
  - "Toggle = single master learning_influence switch (clean subtraction across all layers)"
  - "Modulation = BOUNDED + EVIDENCE-SCALED (cap × evidence factor; thin n → near-zero shift)"
depends_on_artifacts:
  - L5_MIMAMSA_VISION_v1_0.md (Pillar 4 FEED-BACK)
  - L5_CONTRIBUTION_CONTROL_v1_0.md (the learning_influence channel this propagation realizes)
  - L5_MIMAMSA_CAMPAIGN_PLAN_v1_0.md (build phases)
  - asset_registry_seed.ts + the bo_*/ka_*/ph_* writers (the lineage ground truth)
---

# L5 Learning Propagation — How Calibration Reaches the Layers Below

> The question this answers: *L5 computes a correction. Where does it go, what does it touch, how does
> it avoid being applied twice, how far is it allowed to move a value, and how does the user's single
> switch turn all of it off cleanly?* Answered on the REAL dependency graph, with the deterministic
> base kept inviolate.

---

## §1 — Five rules that govern everything

1. **L0 is untouchable.** L0 (`bg_*`) is global, classical, shared across all charts. Learning is
   chart-specific. The reverse channel propagates **L1→L4 only**. Touching L0 would corrupt the shared
   classical base for every chart and violate learning-discipline rule #1 (priors locked). Hard line.
2. **Overlay, never mutation.** L5 writes adjustments to its OWN tables (`mimamsa_*_adjustment`), keyed
   to the upstream id they modify. The deterministic L1–L4 rows are **never written by L5**. This
   preserves L-is-authority (`CLAUDE.md §N.5`), determinism (re-run = identical base), and instant
   reversibility (the toggle is a non-application, not a rebuild).
3. **Deterministic value and adapted value are strictly segregated at every node.** Every consumable
   value exists as a pair: `base_value` (the cited, deterministic L1–L4 computation) and, only when
   learning is ON, an `effective_value = apply(base_value, overlay)`. The base is the source of truth;
   the effective value is a derived view. They are never collapsed into one column.
4. **Single-origin attribution prevents double-counting.** A correction is attached to ONE origin
   asset (the place the evidence is actually about). Along a consumption path it is applied **exactly
   once**; no downstream layer derives a *second* overlay from the *same* evidence. (This is the heart
   of §4 — the deduplication solution.)
5. **Bounded + evidence-scaled.** No overlay may move a base value beyond a per-surface cap, and the
   actual shift scales with evidence strength (n, leakage-status). Thin/contaminated evidence →
   near-zero shift. "Evidence earns the right to modulate" (LL discipline #6), made literal.

---

## §2 — The real lineage (ground truth, from the code)

Extracted from `asset_registry_seed.ts` + the actual SELECTs in the bo_*/ka_*/ph_* writers. This is the
substrate the design rests on — not assumed, read.

**The keystone asset:** `bodha_msr_signals` (L2) has **10 direct downstream readers** and sits at the
head of a 3-hop fan-out:

```
bodha_msr_signals ──read by──► bo_samskara, bo_sangati, bo_drishti, bo_upaya, bo_pramana_mapa,
   (L2 keystone)               ka_yojaka, ka_sangam, ka_bhavishya_lekha, ph_nimitta, ph_phaladesa
        │
        ├─► bo_sangati ──► bodha_convergence / bodha_cdlm_cells
        │         └─► bo_anveshana, ka_sangam, ph_nimitta, ph_phaladesa
        │
        ├─► ka_yojaka ──► kala_activation_predicates ──► ka_sangam ──► kala_convergence
        │                                                      └─► ka_vighnakara, ka_kala_darshana,
        │                                                          ka_bhavishya_lekha, ph_nimitta
        │
        └─► ph_nimitta ──► phala_anchors ──► ph_phaladesa, ph_pramana, ph_suddha_sodhana,
                                             ph_muhurta, ph_pratikara, ph_sankrama
```

> A single salience/dignity adjustment on one signal can ripple to **15+ consumers** across L2/L3/L4.
> That is precisely why naive write-back would double-count, and why single-origin overlay is required.

**The modulation surfaces already exist** (no new base columns needed — L5 adjusts existing ones):
- **L1 `chart_facts`** — fact salience (read by bo_laksana, bo_upaya).
- **L2 `bodha_msr_signals`** — `computed_salience`, `dignity_score`, `house_weight_multiplier`,
  `ashtakavarga_support_multiplier`, and the **reserved** `salience_confidence_interval_jsonb`.
  `bodha_convergence.convergence_score` / `salience_weighted_sum`. `bodha_cdlm_cells` linkage strengths.
- **L3 `kala_convergence`** — `convergence_score`, `confidence_score`, `confidence_label`.
- **L4 `phala_anchors`** — `magnitude`, `confidence_low/high`, `malleability`.

**The reverse channel is L5-only by construction.** `ph_pramana.py` enforces a D5 forbidden-column
gate (`calibration_score`, `posterior_probability`, `accuracy_rate`, `hit_rate`, `brier_score`, …) and
writes NO damping back into L4. So L4 cannot self-modulate; the only place adjustments can live is L5
overlay tables. The code already forces the overlay architecture.

---

## §3 — The overlay model (segregation made concrete)

L5 owns a small family of **adjustment tables**, one per layer surface it modulates. Each row is a
correction keyed to the exact upstream id it adjusts.

| overlay table | adjusts (origin) | key | adjustment payload |
|---|---|---|---|
| `mimamsa_fact_adjustment` | `chart_facts.fact_id` (L1) | (chart_id, fact_id) | salience multiplier + bound + evidence meta |
| `mimamsa_signal_adjustment` | `bodha_msr_signals.signal_id` (L2) | (chart_id, signal_id) | salience/dignity multipliers + bound + evidence meta |
| `mimamsa_convergence_adjustment` | `kala_convergence.convergence_id` (L3) | (chart_id, convergence_id) | window-confidence multiplier + bound |
| `mimamsa_anchor_adjustment` | `phala_anchors.anchor_id` (L4) | (chart_id, anchor_id) | confidence multiplier + bound |

**Each adjustment row carries its provenance** (this is what makes dedup + bounds + audit possible):

```
{
  origin_layer, origin_asset_id, origin_id,        -- WHAT it adjusts (single origin)
  calibration_session_id,                          -- WHICH calibration run produced it
  multiplier, applied_bound, raw_multiplier,       -- the bounded value + the pre-bound value
  evidence_n, leakage_status, evidence_strength,   -- WHY it's allowed (drives the bound)
  derived_from_pramana_ids[],                       -- the mi_pramana verdicts behind it (audit)
  version, created_at
}
```

**Segregation guarantee:** the consumer reads `base_value` from the L1–L4 row (untouched) and the
`multiplier` from the overlay; `effective_value = bound(base_value × multiplier)`. The base and the
effective value never occupy the same column; the overlay is a separate table. Turn learning off →
read `base_value` only → the overlay table is simply not joined.

---

## §4 — The deduplication solution (single-origin, apply-once)

This is the problem you flagged: a shared asset (one signal) is consumed by many downstream assets; a
correction must NOT be applied multiple times along a path, and "no deduplication of the shared asset
itself" — i.e. the signal stays ONE row, consumed everywhere, not copied per consumer.

**The rule: a calibration adjustment is attached to its ORIGIN, and applied exactly ONCE per
consumption path — at the point of consumption of the origin, by read-side join.**

Three sub-rules make this airtight:

**4.1 — One origin per adjustment.** L5 attributes each correction to the single asset the evidence is
actually about. If calibration learns "signal X over-fires in the career domain," the adjustment is on
`bodha_msr_signals.signal_id = X` — full stop. There is no *separate* L4 adjustment derived from the
same finding. The L4 prediction that consumed signal X inherits the correction *because it reads the
corrected signal*, not because L5 also corrected the prediction.

**4.2 — Apply at the consumption join, idempotently.** When learning is ON, a consumer that reads the
origin applies the overlay multiplier where it reads the origin's value — once. Because the multiplier
lives in one overlay row keyed to the origin id, every consumer of that origin applies the *same*
multiplier to the *same* base value. The shared asset is never duplicated (it's one row + one overlay
row); it's just read with its overlay everywhere it's read. Re-reading is idempotent.

**4.3 — No stacking down a path.** The danger is a *second* overlay at a downstream layer derived from
the same evidence (signal X corrected at L2, AND the anchor that used X corrected at L4 from the same
LEL match → X's correction counted twice). Prevented by an **attribution ledger**: every anchor/window
adjustment records `derived_from_pramana_ids[]`. Before L5 writes a downstream overlay, it checks
whether the evidence already adjusted an upstream origin that this downstream node consumes; if so, the
downstream node **inherits via read-side propagation** and L5 does **not** write a second overlay for
the same evidence. A downstream overlay is written ONLY for evidence that is genuinely about that
downstream node and not already expressed upstream (e.g. a prediction-composition error that isn't a
signal error).

> **Net effect:** corrections live at their true origin; everything downstream inherits them by reading
> the corrected origin; the attribution ledger guarantees the same evidence never produces two overlays
> on one path. One signal, one row, one overlay, applied once everywhere it's consumed. No duplication
> of the asset; no double-counting of the correction.

**4.4 — Propagation is read-side, not a rebuild.** Applying an overlay does NOT re-run the writers or
delete-then-insert anything. The base tables are stable; the effective value is computed at serve
time (or in a cached `effective` view) by joining the overlay. A new calibration session writes new
overlay rows; the next read reflects them. No L2–L4 rebuild is triggered by learning.

---

## §5 — Bounded + evidence-scaled modulation

Every overlay multiplier is clamped, and the clamp tightens when evidence is thin — the n=1 firewall
made numeric.

```
raw_multiplier      = f(mi_pramana calibration: predicted vs observed for this origin's stratum)
evidence_factor     = g(evidence_n, leakage_status, evidence_strength)   ∈ [0, 1]
                      -- n below min-n gate → evidence_factor = 0  (no shift at all)
                      -- contaminated/leaked evidence → heavily discounted
applied_multiplier  = 1 + (raw_multiplier - 1) × evidence_factor
effective_value     = clamp(base_value × applied_multiplier,
                            base_value × (1 - CAP_layer),
                            base_value × (1 + CAP_layer))
```

- **Per-layer caps (`CAP_layer`)** are native-ratified constants (a thin-data layer gets a tight cap).
  Recommendation: tightest at L1 facts (rarely move a hard fact), loosest at L4 confidences (the
  user-facing claim is the right place to express calibration). Exact values = native sign-off.
- **`evidence_factor = 0` below the min-n gate** means a 9-event domain effectively cannot move a value
  until it earns the right — exactly the "evidence earns modulation" discipline. No fabricated
  confidence from thin n.
- **Determinism:** the whole transform is deterministic Python; given the same calibration + base, the
  effective value is reproducible. No generative LLM is anywhere in this path.

---

## §6 — The single master toggle = clean subtraction at every layer

`learning_influence` (from `L5_CONTRIBUTION_CONTROL_v1_0.md`) is ONE switch. Its semantics here:

- **ON (default):** every consumer reads `effective_value` (base joined with overlay). Modulation
  propagates L1→L4 per §4.
- **OFF:** every consumer reads `base_value` only; the overlay tables are not joined anywhere. The
  response is **byte-for-byte the pure classical L1–L4 reading** — because the base was never mutated,
  "off" is literally "don't join the overlay," not "undo a change."

Because the base is inviolate (§3) and propagation is read-side (§4.4), the toggle is a single boolean
that selects which value the composition reads — at *every* layer simultaneously. There is no per-layer
unwinding to do. (The framework still *records* adjustments per-layer, so per-layer toggles can light
up later without re-architecting — but v1 is the single master switch you specified.)

**Verification (a seal criterion):** with `learning_influence` OFF, the composed response MUST equal the
pre-L5 baseline byte-for-byte. This is a testable invariant (the OFF==baseline test in the campaign
plan §6).

---

## §7 — Where application happens (the serve-time gate points)

The Whole-Chart-Read (B.11) composition is where base+overlay become the effective answer. Per origin:

| origin layer | base column(s) | overlay | applied at |
|---|---|---|---|
| L1 | `chart_facts` salience | `mimamsa_fact_adjustment` | fact-ranking in composition |
| L2 | `bodha_msr_signals.computed_salience/dignity_score` | `mimamsa_signal_adjustment` | wherever signals are ranked/weighted for the answer (the 10-reader fan-out reads effective salience) |
| L3 | `kala_convergence.confidence_score` | `mimamsa_convergence_adjustment` | timing-window confidence in the reading |
| L4 | `phala_anchors.confidence_low/high` | `mimamsa_anchor_adjustment` | prediction confidence presented to the user |

All four gate points obey the single `learning_influence` switch. With it ON, the composer reads
effective values; the signal-level overlay (the keystone) does the bulk of the work because everything
reads signals — the higher-layer overlays exist only for corrections genuinely *about* a higher layer
(§4.3).

> **Design consequence of the keystone:** because `bodha_msr_signals` is read by ~10 consumers,
> correcting it ONCE at L2 is how a single calibration finding correctly reaches L3 timing AND L4
> predictions AND the synthesis — *without* writing three overlays. The fan-out is the propagation;
> single-origin attribution is what keeps it from becoming triple-counting.

---

## §8 — Build implications (folds into the L5 campaign, Phase P5.5+)

1. **Overlay tables** — the 4 `mimamsa_*_adjustment` tables (migrations; numbering confirmed at open).
2. **Attribution ledger** — `derived_from_pramana_ids[]` + the upstream-already-adjusted check (§4.3),
   so L5 never writes a second overlay for evidence already expressed upstream.
3. **The bounded/evidence-scaled transform** (§5) as a deterministic shared function, native-ratified caps.
4. **Effective-value read path** — a composition-time join (or cached `vw_*_effective` views) that the
   Whole-Chart-Read uses; gated by `learning_influence`.
5. **OFF==baseline invariant test** — the load-bearing correctness test.
6. **Double-count test** — a path test: inject a calibration finding about one signal; assert the L4
   prediction that consumes it is adjusted exactly once (no second overlay on the path).
7. **No-L0-touch test** — assert no overlay/edge ever targets a `bg_*` asset.
8. **Per-origin audit** — `mi_pramana` → overlay traceability so any effective value can be explained
   back to the calibration verdicts that moved it (feeds the `contribution_state` provenance endpoint).

---

## §9 — Open sub-decisions for native

| # | Decision | Cowork lean |
|---|---|---|
| **P1** | **Per-layer caps `CAP_layer`** — the exact maximum shift per layer | Tight at L1 (≤±5–10%), widest at L4 confidence (≤±25–30%); native ratifies exact numbers |
| **P2** | **min-n gate value** — below how many clean observations is `evidence_factor`=0? | Reuse the calibration min-n gate (vision §4); one gate, not two |
| **P3** | **Effective values: computed live at serve time, or materialized in cached `effective` views refreshed per calibration session?** | Cached views for read performance (15+ consumers); invalidated when a calibration session writes overlays |
| **P4** | **Does the L1 fact overlay ever move a *hard FORENSIC anchor*?** | NO — the 7 FORENSIC anchors + canonical computed facts are never modulated; only soft salience of derived facts. Native ratify the exclusion list |
| **P5** | **Granularity recorded now for future per-layer toggles** — confirm v1 stays single-master but stores per-layer attribution | Yes — single master switch, per-layer attribution stored (cheap future-proofing) |

---

*End of L5_LEARNING_PROPAGATION v1.0. Learning propagates L1→L4 (never L0) as an OVERLAY keyed to upstream
ids; the deterministic base is never mutated; corrections attach to a single origin and propagate
read-side, applied exactly once per path (single-origin attribution + the dedup ledger solve double-
counting on the bodha_msr_signals keystone fan-out); magnitude is bounded + evidence-scaled (thin n →
zero shift); and the single master learning_influence toggle is a clean read-side subtraction at every
layer, with OFF==pre-L5-baseline as a testable invariant. Grounded in the real code lineage, not assumed.*
