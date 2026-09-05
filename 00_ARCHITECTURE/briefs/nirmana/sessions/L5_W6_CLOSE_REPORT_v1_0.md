---
artifact: L5_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_L5_W6_CLOSE_REPORT
version: "0.4-DRAFT"
status: DRAFT — sections filled as evidence lands; NOT a close claim
session: L5
layer: L5 — Mīmāṃsā
produced_on: 2026-09-05
charter_ref: C11 (definition of done)
warning: >
  This is a DRAFT started early per the L5 session prompt ("your close report feeds the Conductor's
  Phase Z directly — draft it early"). It is NOT a claim of closure. Sections marked OPEN are
  genuinely open. No capsule, freeze event, or completion is asserted anywhere in this file.
---

# L5 — Mīmāṃsā — W6 CLOSE REPORT (DRAFT)

## §0 — Status

**NOT CLOSED.** W1 ✅ (15/15) · W2 ✅ (15/15 routed) · W3 🟡 in flight · W4 ⛔ blocked · W5 ⬜ · W6 ⬜.

L5's freeze is last in the C2 ordering (L0→L1→L2→L3→L4→L5), so this report closes the build arc.
It is being drafted against evidence as that evidence lands, not written at the end from memory.

## §1 — Asset table (15)

Routes are W2-final. Status is live.

| # | asset | route | W3 | W4 | W5 | notes |
|---|---|---|---|---|---|---|
| 1 | `mi_vistara` | `rebuild_only` | — | ⛔ | ⬜ | **CANARY 1.** 0.287s measured, zero deps. Would capture the campaign's first `mi_*` provenance receipt. Must dispatch `scope='asset'` (D-F-D01). |
| 2 | `lel_events` | `static` | — | ⛔ | ⬜ | **CANARY 2.** `source_accepted` disposition; no build. Zero precedent events in campaign history. |
| 3 | `mi_jivanaghatana` | `changed` | 🟡 | ⛔ | ⬜ | **CANARY 3**, demoted from 1st on its own W1 evidence. |
| 4 | `mi_kula` | `changed` | ⬜ | ⛔ | ⬜ | global re-seed; dispatch `scope='global'`, `chart_id=NULL`. |
| 5 | `mi_sankalpa` | `rebuild_only` | 🟡 | ⛔ | ⬜ | floor fix must land before the build. |
| 6 | `mi_seva` | `rebuild_only` | 🟡 | ⛔ | ⬜ | **not** `probe` — that path is unreachable through four gates. |
| 7 | `mi_bhara` | `changed` | 🟡 | ⛔ | ⬜ | registry-only; L3-acked (#1743). |
| 8 | `mi_bhavisya` | `changed` | 🟡 | 🔒 | ⬜ | **HELD** on #1732. |
| 9 | `mi_pramana` | `changed` | 🟡 | 🔒 | ⬜ | **HELD** on #1732. |
| 10 | `mi_abhilekha` | `probe` | ⬜ | ⛔ | ⬜ | needs a real GREEN probe (B-F-03). |
| 11 | `mi_gunanaka` | `changed` | ⬜ | ⛔ | ⬜ | three literal flags live in stored rows. |
| 12 | `mi_pariksha` | `rebuild_only` | 🟡 | ⛔ | ⬜ | |
| 13 | `mi_adhilepa` | `changed` | ⬜ | ⛔ | ⬜ | measured max **843 s** vs an 11 s registry estimate. |
| 14 | `mi_sambandha` | `changed` | ⬜ | ⛔ | ⬜ | stored rows carry an unearned `empirical` grade. |
| 15 | `mi_darshana` | `rebuild_only` | 🟡 | ⛔ | ⬜ | code correct at HEAD; data predates three merged fixes. |

⛔ = blocked on #1715/PR #1736 (receipt spine) and #1723 (per-chart detector). 🔒 = additionally held on a named cross-layer item.

## §2 — Findings ledger outcome

~109 findings across four W1 batches. **34 MUST · ~60 NOW · 15 NEVER/LATER.** Batch-prefixed ids
(`A-F-15`, `B-F-14`, `C-F-05`, `D-F-D09`) are canonical.

*(Per-finding disposition table fills as W3 lands. OPEN.)*

## §3 — Pillar movement (per the five doctrines) — the section Phase Z consumes

**P7 (PARKED) — seam-keeping, L5's actual mandate.** All five items discharged or determined:
1. *STRUCTURAL re-documented as deliberate* — **determined**, writes in W3. The seal's justification
   had gone stale in two ways: its stated precondition ("L4 sealed") cleared two days after it was
   written, and its stated evidence ("all 9 multipliers `prior_only`") is factually false live (2 are
   `promoted`). The honest justification is that **no prediction in the instrument has a recorded
   outcome** — 195/195 `pending`, journal empty, no outcome column — and P7 is parked by ruling.
2. *Prediction provenance retention* — **VERIFIED HEALTHY.** 0 orphans across all four links. One
   live threat found and escalated (#1732), one more contributed to L4's (#1748).
3. *Journal / adjudication seams* — **CONFIRMED, with precision.** The journal is empty because it is
   **unwritable** (no `INSERT INTO mimamsa_journal` exists anywhere in the repo), not because parked.
   The adjudication log is written correctly behind a real permission gate but **never read back into
   L5**; its one bridge 404s silently on every adjudication.
4. *Insight-embedding serve path* — **NOTED in full.** Schema ✓, serve path ✓ **and honest** (it
   refuses to embed a query string it cannot honestly embed — B.10 conduct to preserve), producer
   **missing**, MCP reachability **missing**, and embeddings are always zero after any build by
   construction.
5. *No calibration values invented* — **HELD ABSOLUTE**, and it caught a live violation: a hardcoded
   `base_rate = 0.10` on all 57 calibration rows with `brier_vs_null` computed from it. Repaired to an
   honest NULL, **not** to a better-looking prior.

**D-SERVICE (P8).** Zero of 16 L5 capabilities declared a `density_contract`; 8 of 16 lacked
`empty_reason`, including all three headline P7 surfaces. In flight. Named built-but-unplugged
instances recorded: the journal append path, `query_insight_embeddings` (unreachable from any MCP
tool name), `mimamsa_outcome_record` (a dead alias that 400s while served prose still tells callers
to use it), `prediction_lifecycle_sweep` (registered, in zero tool projections).

**D-GROUNDING (P3).** L5's outputs are overwhelmingly and correctly `pratyaksa`. Two mislabels found
(`mi_kula`'s `fam_msr_signal` / `fam_anchor` badged `CLASSICAL_CITED` while citing MARSYS-internal
documents). One genuine tier gap named and **deferred, not bodged**: `verdict_object`'s grounding
tier is flattened into its derivation tier — a D-GROUNDING schema change spanning L2→L5.

**D-SALIENCE (P5) / D-SYNTHESIS (P4) / D-TIME (P6).** L5 is a consumer, not a producer, of these.
The one genuine contribution is negative and worth Phase Z's attention: `mimamsa_load_bearing`
reports **rank as measurement**, and its `>= 1.0` cut excludes the only empirically-grounded family
on the canonical chart while promoting an `n=0` family to `role='load_bearing'`.

## §4 — Cost actuals vs forecast

**The plan's L5 forecast was wrong in a way Phase Z should record.** Plan §5 forecast "mostly
`verified_reuse`/`static` against existing build evidence" — i.e. L5 as the cheap closing layer.
**No asset takes `verified_reuse`** (D-L5-04): the served data predates three merged narration fixes
and the intervening rebuild was BLOCKED, so the digest lineage that route requires does not hold.

**Registry estimates were also materially wrong**, re-measured from `build_run_assets`:

| asset | registry est. | measured avg | measured max | tail error |
|---|---|---|---|---|
| `mi_adhilepa` | 11 s | 31.2 s | **843.1 s** | **77×** |
| `mi_bhara` | 2 s | 17.3 s | **596.5 s** | **298×** |
| `mi_pariksha` | 2 s | 4.2 s | 32.9 s | 16× |

*(Session token/wall-clock actuals: OPEN, filled at close.)*

## §5 — Backlog handed forward

**To Phase Z:**
- L5's **32 DAG corrections** (19 undeclared-but-read, 13 declared-but-unread), posted to #1734.
  Two false edges have **already destroyed real builds**; under D-CND-09 those blocks are permanent
  for this campaign.
- The `expected_volume_formula` seed-revert hazard (#1757) if unruled.
- Three `main` test failures (#1764) if still red.
- A third chart (`cb73cd3d…`) sits in build state with no L5 data and no disposition.

**To the future P7 programme** (plan §7.3, each with its evidence):
- The journal **producer** — the append path does not exist in any language.
- The insight-**embedding** producer + MCP reachability (full spec in B-F-20).
- A **calibration-history table** — the highest-value single item. Its absence is what makes #1732
  unrecoverable rather than merely inconvenient.
- A real hold-out scorer, negative-control harness, and a leakage detector that can write `'leaked'`.
- The age-banded `base_rate_by_age` derivation, and a real `event_class_id` resolution rule
  (`matching_rules` exists and nothing consumes it).
- `mi_sankalpa` is the P7 **substrate**; §7.3's parked "remedy-efficacy ledger" is the *analysis over*
  it. Recorded because conflating them would wrongly park a live, tested write path.

**To the campaign's own doctrine record:**
- Three pieces of existing §N.8 conduct flagged for **verbatim preservation**: `mi_pariksha`'s
  `structural_proxy`/`not_implemented` statuses, `mi_sambandha`'s `_PROPENSITY_UNMEASURED` null, and
  `query_insight_embeddings.ts`'s refusal to embed a query it cannot honestly embed.
- **A predecessor seal is evidence, not authority** (D-L5-09): L5's seal gate G8 is a false PASS and
  G11 has regressed. Any layer inheriting a seal should re-verify its gates.

## §6 — OPEN

Per-finding disposition table · W4/W5 evidence · cost actuals · the Conductor's freeze-ordering ack ·
closure-safe sync proof.
