---
artifact: SUVARNA_ALIGNMENT
version: "1.0"
status: LOCAL_DRAFT — K0-SV template_checklist slice; Suvarṇa acknowledgement pending
item: K0-SV
produced_on: 2026-10-07
---

# Suvarṇa alignment for Kāla writers

This is the local K0-SV checklist extracted from the governed sources below. It is a preparation aid for Kāla implementation, not a Suvarṇa certification, a settled L3 layer instance, or an acknowledgement of the proposed `chart_dashas` contract. The tier-4 template itself says `DRAFT_PENDING_REVIEW`; the L3 instance says `PROVISIONAL — until J1; may register gaps, may not certify`. Keep those limits visible until the source owners settle them.

## Pinned sources

| source (path relative to campaign checkout) | section used | SHA-256 of file read |
|---|---|---|
| `00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` | §0–§9, Filling order, Adapting per layer | `ff91138491b75ca0eb2134e6f5e8a05d7f874a59b72d3f8f50bfeb9bcd82f574` |
| `00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` | §4.4, §5.2–§5.3 | `5319de8738409fee0f3d30e4f34f1b432eee1a0247aab963126485b6ea5bc675` |
| `00_ARCHITECTURE/briefs/suvarna/layers/L3/L3_LAYER_INSTANCE_v1_0.md` | §4.4, §5.2–§5.4 | `fc5f3265f8147f31f8704644a2e7111033b8ba635977bd60075b9c65f7fbcbf1` |
| `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md` | §2.2 F2 clocks | `85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef` |
| `platform/python-sidecar/ga_writers/ga_dashas_writer.py` | `compute_ashtottari_system` and `_build_row` (current-code observation) | `edf3e1419f19d59ab978ebd9e8adeddcf5b5f1c851e905c6c17cffabab0d6eab` |

The paths above are under `/Users/Dev/kalayantra/wt/campaign/`. The hashes identify the exact local documents read; they do not imply that their provisional status changed.

## Checklist for each Kāla asset or service

| # | item to carry into its elevation brief and implementation | governing source |
|---|---|---|
| 1 | Name the asset id, kind, L3 instance revision and status, contribution scoring, temporal or manifestation role, measurement date and exact evidence population. Inherit the thirteen §0.1 rows from the L3 instance; leave an unavailable row marked as a layer-instance gap rather than inventing it. | Asset template §0 and §0.1; layer template §4.4; L3 instance §4.4 |
| 2 | Measure the current writer, table or service, build history, consumers, concept width and depth, retrieval reachability, and the three-way baseline. Record instrument, population and revision for each figure. | Asset template §1–§1.2; L3 instance §1.1–§1.4 |
| 3 | State the asset-specific temporal obligation: a witnessed event cannot choose its trigger; nearest versus better-supported windows use a named criterion; absent and unavailable remain distinct. Declare the preserved kernel and the expected semantic difference before changing code. | Asset template §3, §6, Adapting per layer; L3 instance §3.1–§3.3 |
| 4 | Name contracts produced and consumed, their fields, grain, identity, generation and declared use. In particular, pin L1 `chart_dashas` by build id, ayanāṃśa and each row's system-and-level tier before the F2 clock reads it; check ancestor tiers separately, and do not recompute or restate an L1 value. The current producer gives classical Vimśottarī levels 1–4 individual verdicts while KP and other deeper rows can remain `single`. Its Aṣṭottarī builder sets applicability true using a canonical-chart comment, rather than a per-chart condition, so a Kāla clock must await an evidenced producer applicability rule before treating that flag as a positive verdict. The proposed read policy awaits Suvarṇa's acknowledgement. | Asset template §0.1 row 5, §4 Ldgr, §6; L3 instance §2.3 and §5.2 Ldgr; Kāla architecture plan v1.1 §2.2 F2 clocks; `ga_dashas_writer.py` `compute_ashtottari_system`, `_build_row`, `_apply_vimshottari_independent_verification` and `build_system` verification loop (current-code observations) |
| 5 | For each of the nine gates — Ldgr, Idem, Earn, Null, Vocab, Carr, Narr, Dens, Build — state applicability, a detector that can fail, verdict and evidence. Use exactly `PASS`, `FAIL`, `PARTIAL`, `NO_DETECTOR` or reasoned `N/A`. Narr applies to prose; Dens applies to served output. | Asset template §4; layer template §5.2; L3 instance §5.2 |
| 6 | For Build, check registration, frozen `WriterBase` contract, dispatchable target, resolvable DAG, count and integrity checks, honest completion, executed history, outcome history and dependency liveness. Record `never_rebuilt`, `dry_run_ok`, `rebuilt_ok` or `rebuild_failed` from a real run. | Asset template §4.2; L3 instance §5.2 Build |
| 7 | For Carr, select and run the applicable source correspondence, witness-carriage or independent re-derivation test. For Null, leave underivable values null. Keep authority disagreements as disagreements and prevent shared roots from becoming independent confirmations. | Asset template §4, §4.1 and Adapting per layer; L3 instance §2.4, §2.7 |
| 8 | Enter measured gaps and optional measured opportunities in the governed delta ledger, each with a detector and owner. Close a gap only after its detector passes. The change packet states exact files, frozen writer conformance, idempotency, migration, rollback, consumer effects and open decisions. | Asset template §5–§6 |
| 9 | Run the brief-shape check, review, then write per-criterion certification records only after execution and a passing detector. A pilot brief derived from the provisional L3 instance may register gaps but may not certify. A later changed criterion invalidates only its affected records. | Asset template §2, §7–§8 and pilot clause; layer template §5.3; L3 instance §5.3–§5.4 |

## Open alignment

- The L3 instance explicitly leaves per-asset contract fields, presentation fields and coverage states unfilled (its §3.3 and §5.2). Those are inputs to a later asset brief, not facts this checklist can supply.
- The daśā-table agreement, including Suvarṇa's acknowledgement in the coordination log, is a separate K0-SV step. This document records no acknowledgement and makes no promise on Suvarṇa's behalf.
- Aṣṭottarī applicability needs a producer-side chart-specific detector and a named failed-condition result. The current all-true stored flag is insufficient evidence beyond the canonical-chart example; the proposed daśā contract leaves such a clock unavailable until Suvarṇa confirms the producer guarantee.
