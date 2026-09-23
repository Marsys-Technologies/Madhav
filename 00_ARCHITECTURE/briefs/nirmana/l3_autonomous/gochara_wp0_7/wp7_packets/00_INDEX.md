---
artifact: WP7_PACKETS_INDEX
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "WP7 run (l3/gochara-autonomous-wp0-7) — for the parent run and the packet owners"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 (interface packets) + §4 WP7 exit gate; KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA_v1_0.md §4 WP7
---

# WP7 — Receiving contracts: packet index

All eight packets live in this directory, one file each. Every packet is
`DESIGN_ONLY_NOT_IMPLEMENTED`: none of the targeted files (all in other teams'
ownership / `must_not_touch`) was modified; each owner needs no further discovery
conversation to implement. Anchors in every packet were read and verified at this
checkout (`l3/gochara-autonomous-wp0-7` @ `fd13ec0a6`; pin `c58e86662` is an ancestor —
source files identical to the pinned revision).

## The eight packets

| Packet | File | One-line summary |
|---|---|---|
| **P-1** | `PACKET_P1_serving_provenance_coverage.md` | Manifest-driven provenance/coverage in `register_gochara_windows.ts`: any generation with a `kala_gochara_publication` row resolves provenance from `writer_asset_id + convention_id + manifest_id` and coverage from `kala_gochara_coverage`; `'v1'`/`'3.0'`/`g3_*` string branches survive only as legacy fallbacks; removes the `'v1'` COALESCE default (absent authority = `unpublished` coverage object); plus the `/api/mcp/db/query` whitelist additions (`kala_gochara_coverage`, `kala_gochara_publication`) its owner must land for the new queries to transit (WP0 E-004 item 1). |
| **P-2** | `PACKET_P2_reading_checklist.md` | `fetchGocharaSweep` must carry `contact_id`s (via `active_sentences`), `completeness_state`, and `peak_basis` through its 200-row cap / 5-window trim, with confirmed-vs-context counts served separately per §N.6 — else Q01/Q02 are unanswerable from the reading layer. |
| **P-3** | `PACKET_P3_l5_ledger.md` | L5 claim/prediction ledger gains a nullable `contact_id` (the WP1 §3.2 `sha256:` id) so frozen claims keep identity across rebuilds/republishes/rollbacks via the chain `contact_id → window_id → manifest_id`. |
| **P-4** | `PACKET_P4_contact_ledger_read_capability.md` | New density-layered read capability over `kala_gochara_contacts` + `kala_gochara_coverage`: confirmed episodes on a trim-proof `hard_floor`, catalog-only rows in a separate context layer, `searched_horizon` exposed for `moon_on_demand` partitions. |
| **S-1/S-2** | `PACKET_S1_S2_gochara_transit_service.md` | S-1: `find_aspects` keeps its exact shape for the duck-typed callers (`kala_trigger` :96/:150/:199, `currents.py:59`, `ka_sangam/engine.py:464`); the enriched interface arrives as a new `find_episodes(chartId, targets, horizon) → {episodes, coverage}` with grain + `contact_id`. S-2: this stream produces Saṅgam's directed contact events per M-3 — full Parāśari per-graha dṛṣṭi (Mars 90/180/210, Jupiter 120/180/240, Saturn 60/180/270, others 180; **no node dṛṣṭi, N-14**), both directions, `planets` as a list, absent-when-nothing-fires, no ephemeris scan inside Saṅgam (`_resolve_transit_planet` replaced by event consumption). |
| **T-1** | `PACKET_T1_kala_trigger.md` | One-paragraph note to the kala_trigger owner on whether `find_episodes` reduces per-window fan-out — **with the WP4 measurement placeholder left explicit** (`[WP4 NUMBERS PENDING — parent run fills this after WP4 with the measured fan-out comparison]`) and the measurement structure drafted so the numbers slot in. |
| **C-1** | `PACKET_C1_cockpit_clear.md` | The exact `EXPLICIT_CLEAR_OPS['ka_gochara']` entry: three generation-scoped DELETEs in dependency order (coverage → contacts → windows, each `WHERE chart_id=$1 AND generation='4.0'`), the authoritative-generation refusal (non-release principal refused; release authority cascades authority reset + manifest `cleared`), the no-JOIN rule, the `ClearOp` guard-extension design, and the `clear_tables` display value with the F-24 "display-only" caveat. |
| **V-1** | `PACKET_V1_sangam_dependency.md` | Saṅgam declares `→ka_vedha_gochara` (the undeclared read at `ka_sangam.py:1057-1065`, F-17) with role `counterevidence`, and re-types `→ka_gochara` as `service` per S-1/S-2. |
| **K-1** | `PACKET_K1_kshetra_dependency.md` | Kṣetra declares `→ka_gochara` (+ `→ka_vedha_gochara` after one cross-check generation), pins provenance edges by `(generation, id)` instead of bare row id (`writer.py:952,1063`), and removes its own `'v1'` COALESCE fall-throughs (`stage4_field.py:1386-1389`, `writer.py:2328-2330`) so absent authority = `unpublished`. |

## WP0 reader-inventory additions the packets must account for

From `WP0_FINDINGS.md` consumer re-enumeration (plan §6.1 + items 1–10). Packets cover
the load-bearing ones; the remainder are recorded here so no owner is surprised:

1. **`/api/mcp/db/query` whitelist** (`route.ts:64,71,84`) — folded into P-1 §4 and
   P-4 §4 (new-relation whitelist entries; `kala_gochara_contacts` deferred to P-4).
2. `scripts/kala_admission/*` calibration SQL writers/readers on `_v2` — untouched by
   any packet; they operate on `'2.0'`, which P-1 never routes and C-1 never reaches.
   Recorded; no action.
3. Same as 2 (w41/w44/w43 config refs) — recorded, no action.
4. `mr20/mr23/mr47` gates reading v1/`'3.0'`/`_v2` corpora — recorded; they read
   protected/historical generations the packets deliberately do not alter.
5. `w2g_validations` read-only suite — recorded, no action.
6. `gochara_grammar/resonance_map.py` + `gochara_intensity/*` internal mesh readers of
   `gochara_resonance_map` — recorded; P-1 keeps the `gochara_resonance_map` whitelist
   entry (:84) intact for them.
7. `ka_gochara_sweep/writer.py` (the F-03 Clear hazard's source) — C-1 composes with
   the Phase-1.1 `is_active` filter that makes it unreachable; recorded.
8. **`lel/prospective_ledger.ts`** (`:164,170,208,252,498`) — folded into P-3 (the
   windows/authority mechanism is its row-shape template; `contact_id` plugs into the
   same filing path).
9. `pariprashna/confidence/engine_tier.ts` comment-level coupling to the
   authority-flip mechanism — recorded; P-1d changes absent-authority semantics from
   silent-`'v1'` to `unpublished`, which is the honest state a comment-coupled reader
   should see; no code action.
10. Registry-seed prose surfaces (`vidhi/registry_data.ts`, `bg_vidhi_primitives.py`)
    claiming "rows ACTIVE on the current date" — recorded; the seed file is HELD
    (N-9(ii) co-ownership concern, WP10-era fix); P-1's manifest-driven provenance is
    the serving-side truth those prose claims will need to follow.

## Outstanding items owned elsewhere (not blockers for this packet set)

- **Sentinel exit-gate test** (plan §4 WP7 exit gate: a sentinel
  `independence_group` value surviving WP6 storage + simulated retrieval/budget/
  delivery + simulated replay) runs **after WP6 and is owned by the parent run** — it
  is not a WP7 packet deliverable and is not claimed here.
- **T-1's numbers** — the WP4 measured fan-out comparison fills the explicit
  placeholder in `PACKET_T1_kala_trigger.md` after WP4; until then T-1's recommendation
  is deliberately unmade (evidence-gated by design).
- **WP1_CONTRACTS §11 (E-001)** — `KALA_COST_PROFILE_v1_0.md` / `KALA_BASELINE_v1_0.md`
  unreachable from this branch; WP4 proceeds with fresh numbers. Recorded in
  `ESCALATIONS.md` by the WP1 run; no WP7 action.
