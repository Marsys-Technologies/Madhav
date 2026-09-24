---
artifact: KALA_SETTLEMENT_BRIEF
canonical_id: KALA_SETTLEMENT_BRIEF
version: "1.2"
status: RULED
date: 2026-09-24
audience: "the native — this is a decision document, not a plan to execute"
author: "L3 strategy session (madhav-e3), Opus 5"
purpose: >
  Settle the eight preconditions that must hold before the per-asset elevation loop starts.
  Each item states what is measured, what is assumed, the options, and one recommendation.
  Nothing here is executed; every item ends in a decision line for the native.
verdict_tier: "Establishes readiness to begin. Proves no explanatory value and no empirical performance."
---

# Kāla settlement brief — what must be true before asset 1

Eight items. Six need a ruling; two are corrections already applied and are recorded so the
record is not silently repaired.

---

## S-1 — Merge strategy for the two unmerged streams  ·  RULING NEEDED

**Measured (production, read-only, 2026-09-24).** 15 migrations are written and not applied. All 15
are on two unmerged branches: 9 on `l3/gochara-autonomous-wp0-7`, 6 on `sangam/stage3`. Migrations
applied in production reach 1079. Nothing on `main` is pending.

**Correction, recorded rather than quietly fixed.** An earlier count in this session said **159
unapplied**, and I presented it as the campaign's most consequential finding — "every schema change
all three streams have authored is sitting undeployed". That was false. The detector compared
migration *filenames* on `main` against `_migrations_applied`, and the early schema was applied
under a consolidated legacy naming (`0000_seed_legacy_applied.sql`, `0001_brahma_baseline.sql`,
`001_baseline.sql`) that does not match `main`'s `001_initial_schema.sql`. 147 long-applied
migrations were read as pending. The detector now counts only branch-only files and reports 15.
A detector that cannot distinguish "not applied" from "applied under another name" was not measuring
what it claimed (§N.8).

**So the real question is not deployment. It is merge.** `sangam/stage3` is 119 commits ahead of
`main` and unmerged; Gochara's WP0-7 session has closed with its work on its own branch. Both are
deliberately disposable-DB-only today.

**Options.** (a) Merge both streams before L3 briefs finalize, so briefs are written against landed
schema. (b) Leave them unmerged, write briefs against branch state, accept that the target moves.
(c) Merge Saṅgam only — it is the DAG chokepoint with 5 downstream assets.

**Recommendation: (c), then (a).** Saṅgam gates five downstream assets; Gochara gates three and has
two open native decisions of its own (E-012, E-015) that should be ruled before its branch lands.

> **Decision S-1 — RULED 2026-09-24 (native):** recommendation adopted. Saṅgam merges first (DAG
> chokepoint, 5 downstream assets); Gochara follows once its own E-012 and E-015 are ruled.

---

## S-2 — Adopt the synergy binding  ·  RULING NEEDED

**Measured.** `KALA_SYNERGY_BINDING` is at **v2.3**, reachable from `origin/l3/kala-elevation-readiness`,
status `PROPOSED_FOR_NATIVE_RULING_THEN_ADOPTION` — **unadopted**. It contradicts itself on its most
cited field: §B1 asserts `precision_regime` as the ruled name while §B8 item 9 still lists that very
direction as an open native decision. §B8 carries ten open decisions in total.

**Why it blocks.** All 19–22 final briefs cite it. Finalizing them against an unratified,
self-contradicting contract guarantees a second vocabulary pass across every brief — the exact cost
already paid once this session when sixteen briefs were written against the superseded v1.0.

**Options.** (a) Ratify v2.3 and close §B8 item 9. (b) Leave it unadopted; briefs cite the underlying
rulings only — Kṣetra ruling 8, Gochara G-9, Saṅgam M-3 for the name, D-S4 for the native ruling,
Saṅgam D-7 for the alias condition — none of which depends on adoption.

**Recommendation: (b) now, (a) when convenient.** The rulings are already sound and independent; the
briefs do not need the binding ratified to be correct, and (b) unblocks today. Production supports
this: `kala_field_windows` already carries `precision_regime` in prod, so the ruled name is the one
the system already speaks.

> **Decision S-2 — RULED 2026-09-24 (native):** recommendation adopted. Proceed WITHOUT waiting for
> binding adoption. Briefs cite the underlying rulings — Kṣetra ruling 8, Gochara G-9, Saṅgam M-3 for
> the name; D-S4 for the native ruling; Saṅgam D-7 for the alias condition — none of which depends on
> the binding being adopted. The binding version is recorded as context, flagged UNADOPTED.

---

## S-3 — Campaign scope: 19, 22, or 23 assets  ·  RULING NEEDED

**Measured.** The registry seed carries **23** `ka_*` assets. The brief-state table tracks 22.
`ka_gochara_sweep` is in `asset_registry.depends_on`, has a registered writer, and appears in no
brief and no tracker row. Of the 22, three (`ka_kshetra`, `ka_sangam`, `ka_gochara`) are mid-execution
under their own streams with native rulings already taken, and three more inherit the Gochara family
plan with no standalone brief.

**Recommendation: 19 assets in this loop.** The three streams stay with their streams and report into
the ledger; this session consumes their state rather than commanding it. Pulling them in duplicates
their governance and risks conflicting instruction — which already cost a full correction cycle this
morning over `precision_regime`. `ka_gochara_sweep` needs its own disposition: brief it as a 20th, or
exclude it with a stated reason. It should not remain untracked by default.

> **Decision S-3 — RULED 2026-09-24 (native):** scope is **19 assets**. The three streams stay with
> their streams and report into the ledger. `ka_gochara_sweep` is dispositioned to the **Gochara
> stream**, not to this loop: it is a Gochara-family asset (`depends_on: [ka_gochara_resonance]`) and
> the family is already excluded, so briefing it here would split one family across two pipelines.
> It is no longer untracked — it is assigned, and the tracker will say so rather than alerting.

---

## S-4 — The L0/L1/L2 elevation assumption  ·  RECORDED, CONFIRM STANDING

**Native ruling, 2026-09-24:** "Consider L0, L1 and L2 all assets to be elevated as per the current
revision." Recorded in the tracker as `ASSUME_UPSTREAM_LAYERS_ELEVATED` and stated on the page.

**Measured state it overrides.** Under the currently-frozen definition `t3-2026-09-11-8b884eac`:
`bg_` **0/40** frozen, `ga_` **0/19**, `bo_` **8/22**, `ka_` **0**. Earlier freezes exist under
t0/t1/t2 and do not carry — `egate.sql` scopes to the current revision precisely because a freeze
under a superseded manifest "was read as current clearance".

**What this costs.** Every L3 result produced under this assumption inherits it. If the t3 re-freeze
later finds a real defect in an L0/L1/L2 asset an L3 brief depended on, that brief is re-opened. The
assumption is cheap now and the exposure is bounded, but it is an exposure and should not become
invisible.

> **Decision S-4 — RULED 2026-09-24 (native):** the assumption **stands**. L0/L1/L2 are treated as
> elevated under the current revision. The measured state remains recorded beside it and every L3
> result inherits the exposure.

---

## S-5 — The four systemic brief gaps  ·  RULING NEEDED

**Measured across all 22 briefs:** `PD` (Product Definition) **7/22** · `Val` (value extraction)
**8/22** · `Ldgr` (derivation ledger) **9/22** · `Dens` (serving density) **9/22**. Every other
criterion is at 15/22 or better; all of Tier 1 and both ladders are at 22/22.

Twenty independent reviews across ten assets never flagged these, because each reviewer saw one
brief. A per-asset review cannot see a column.

**Recommendation: one sweep across all briefs before asset 1**, not 19 inline repairs. `Ldgr` is a
non-negotiable architectural principle (B.3) and `PD` is the top of the alignment stack.

> **Decision S-5 — RULED 2026-09-24 (native):** **sweep first.** One pass across all briefs closing
> `PD`, `Val`, `Ldgr`, `Dens` before asset 1.

---

## S-6 — Multi-table assets are under-measured  ·  CORRECTION PENDING

The production probe reads each asset's single registered `target_table`. Kṣetra is a 23-table
internal DAG: `precision_regime` lives on `kala_field_windows`, while its registered target is
`kala_field`. Kṣetra's contract coverage is therefore **understated** in every number this session
has produced.

This is a known limitation, not a finding. It needs a per-asset table *set* before these numbers are
used as an elevation baseline.

> **Decision S-6 — RULED 2026-09-24 (native):** **fix now**, before these numbers become the
> elevation baseline.

---

## S-7 — Where the loop starts  ·  RULING NEEDED

**Correction.** I earlier called `ka_avadhi` "DAG #1". Within depth 0 the twelve roots have **no
ordering constraint** — the numbering is an alphabetical tiebreak, not a dependency. The first asset
should be chosen for learning value.

**Recommendation: `ka_sudarshana_varsha`.** Depth 0, 120 rows, 21 columns, no stream entanglement,
and the highest-scoring brief at 29/31. The cheapest place to run the full SOP end to end and find
where the process leaks. Then `ka_tithi_pravesha` (240 rows), then `ka_kota_chakra` (1,170) — before
anything with six-figure row counts (`ka_yojaka` 150,724; `ka_taranga` 277,236; `ka_kalasutra`
337,148; `ka_kshetra` 10,982,957).

> **Decision S-7 — RULED 2026-09-24 (native):** first asset is **`ka_sudarshana_varsha`**, then
> `ka_tithi_pravesha`, then `ka_kota_chakra`. The native confirms the depth-0 tiebreak is understood
> and the ordering stands.

---

## S-8 — Final brief naming  ·  RULED

Native ruling, 2026-09-24: final briefs carry **`status: FINAL`**; each artifact keeps its own
version lineage. No forced common version number — Kṣetra is at 4.9, Gochara's plan at 2.2, the
layer briefs at 1.0–1.2, and a synthetic shared "v5.0" would assert a lineage that does not exist.

---

## What is already settled and needs no ruling

- **SOP and model split.** Opus 5 authors, elevates and decides; Fable 5.1 reviews only, in fresh
  read-only context; verdict is binary **ACCEPT / REJECT**; REJECT returns to Opus.
- **Baseline is a triangulation**, stated per asset: deployed (production schema + rows) · current
  code (newest on the system, including unmerged and uncommitted) · target (brief). The delta is
  target − current code; the *risk* is current code − deployed, and they are different numbers.
- **Ledger discipline.** One append-only vocabulary covers both halves. A verdict cannot be recorded
  without a review having been requested; a brief cannot go final without an independent ACCEPT;
  `completed` is never elevation until the strategy session appends `verified`.
- **Order.** DAG order from `asset_registry.depends_on`. Acyclic, five depths, 12 roots.

## The one measurement that should shape expectations

**Corrected after S-6 was executed.** An earlier version of this section said the shared contract
vocabulary "appears **three times**" across the layer. That figure was produced by the very defect
S-6 names, and it understated the truth by 4×. With per-asset table *sets* in place the measurement is:

| asset | tables | rows | contract fields live in production |
|---|---|---|---|
| `ka_gochara` | 9 | 42,708 | **8** — `time_basis`, `precision_regime`, `comparable_with`, `corpus_verifiable`, `independence_group`, `completeness_state`, `epistemic_class`, `operator_role` |
| `ka_kshetra` | 17 | 13,433,597 | **3** — `t_start`, `t_end`, `precision_regime` |
| `ka_sangam` | 1 | 20,497 | **1** — `tier_basis` |
| the other 15 | 1–2 each | ~795k total | **0** |

**12 contract-field instances live, not 3.** The correction lands almost entirely on `ka_gochara`,
which I had reported as carrying none: its `kala_gochara_contacts` / `_convention` / `_coverage` /
`_publication` tables are in production and already stamp the ruled vocabulary. Gochara is materially
further along in production than this session previously stated — twice.

**What still holds, and is the real shape of the work.** The vocabulary is concentrated in the two
stream assets that have been elevated under their own campaigns. **All fifteen non-stream assets
carry zero contract fields** across ~795k rows. The three streams are excluded from this loop (S-3),
so every asset this campaign touches starts at zero.

The layer is built and populated. The nineteen assets in scope do not yet speak the language the
elevation exists to establish. That — not missing data, and not a deployment backlog — is the delta
the briefs close.
