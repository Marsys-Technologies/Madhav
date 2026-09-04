---
artifact: L4_STATE.md
canonical_id: NIRMANA_V21_L4_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L4
layer: L4 — Phala
owner: the L4 session (this file is yours alone — charter C5)
last_updated: 2026-09-05 — L4-W2 complete; W3-0 next
---

# L4 — Phala — SESSION STATE

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → this file → `git fetch origin main` →
your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 (run-slot claims, freeze-ordering acks, monster scheduling)
- **Adjudication:** open a new issue labeled `nirmana-adjudication`, then keep working (C3)
- **Migration range:** 680–689 (mine alone, collision-free by construction)
- **Branch namespace:** `codex/nirmana-l4-*` · **PR title prefix:** `L4:`
- **Worktree:** `~/nirmana-s/l4` (created off `origin/main` `20323fae4`; `npm ci` complete, exit 0)
- **Freeze predecessor:** L3 Kāla must be frozen before my W6 ceremony (C2; asset work is never held)

## Position

`L4-W2` — **DECIDE COMPLETE (9/9 routed; 85 findings triaged, plus M-31 from ruling #1732).**
Next: **W3-0**, the deterministic anchor identity — the layer's highest-priority unheld item, and the
one that lifts the campaign-wide hold on `phala_anchors`.

- **W1 ANALYZE** ✅ COMPLETE 9/9 — `L4_W1_ANALYSIS_{INDEX,BATCH_A..D}.md`, PR **#1735** (docs-only, auto-merge armed).
- **W2 DECIDE** ✅ COMPLETE — `L4_W2_DECIDE_v1_0.md`. **All nine route `changed`**: no `rebuild_only`,
  no `verified_reuse`, no services. Every asset carries at least one MUST correctness finding, so a
  rebuild of current code would faithfully reproduce the defect. Said plainly rather than routing the
  cleanest asset `rebuild_only` to make the layer look cheaper (D-L4-11).

## Asset table (9 assets — frozen definition `t0-2026-09-01-0e5b06fb`, live-verified)

| asset_id | route | status | E-gate | capsule | notes |
|---|---|---|---|---|---|
| `ph_nimitta` | **changed** | W2 done → **W3-0** | wave 0 · 37/46 unfrozen · **REBUILD HELD campaign-wide (ruling #1732)** | — | the layer root + my canary; 8 MUST + **M-31** (deterministic identity) |
| `ph_muhurta` | **changed** | W2 done | wave 1 · 38/47 unfrozen | — | 2 MUST: the verdict can only ever read `mediocre`; `rows_written` over-reports by the collision count |
| `ph_pratikara` | **changed** | W2 done | wave 1 · 40/49 unfrozen | — | **7 MUST**, incl. the layer's hard-floor item (fabricated citation on 100% of 1,277 rows); needs a rerun **after** its writer fix |
| `ph_rectification` | **changed** | W2 done | wave 1 · 38/47 unfrozen | — | 1 MUST: `load_bearing: true` on a fit that is 0.0000 across all 95 scored candidates |
| `ph_sankrama` | **changed** | W2 done | wave 1 · 38/47 unfrozen | — | 2 MUST: 250 rows (10%) destroyed by a stale domain map; `trajectory` constant from an `or 0.0` |
| `ph_sodhana` | **changed** | W2 done | wave 1 · 38/47 unfrozen | — | detector-integrity defects + a severity-inverting sort that returns **critical last** |
| `ph_suddha_sodhana` | **changed** | W2 done | wave 2 · 39/48 unfrozen | — | the layer's cleanest asset; `changed` for C12 + a silent classify-clean path |
| `ph_pramana` | **changed** | W2 done | wave 3 · 45/54 unfrozen | — | 1 MUST: `life_event_miss` is a refutation from a detector that cannot return a match. D5 gate verified CLEAN — do not add a score |
| `ph_phaladesa` | **changed** | W2 done | wave 4 · 46/55 unfrozen | — | 2 MUST: **zero MCP consumers**; headline anchor ignores the purification verdict |

All 9: `asset_kind=artifact` · `asset_type=data` · `scope=per_chart` · `has_writer=true` ·
`has_substeps=false` · `domain=chart` · `rung=R4` · `is_active=true` · `catalog_status=DRAFT` ·
`execution_obligation=build`. **No services in L4** (so C12's service freeze-exception §3.5 addendum
does not apply to any of my assets).

**In-layer DAG tiers** (derived from `depends_on`, then independently corroborated by the frozen
manifest's own `wave_index`): 0:{nimitta} · 1:{muhurta, pratikara, rectification, sankrama, sodhana}
· 2:{suddha_sodhana} · 3:{pramana} · 4:{phaladesa}. Ancestor spread per asset: 13 L0 · 13 L1 ·
9–11 L2 · 11 L3 — L4's W4 opens only well into the campaign, as the prompt anticipated.

## Decisions log

- **D-L4-01** (2026-09-05) — **Canary = `ph_nimitta`**, derived not assumed. The C10 ancestor query
  shows it is the unique L4 asset with zero in-layer ancestors and the minimum transitive closure
  (46). Every other L4 asset descends from it, so it is provably the first `ph_*` whose ancestors
  can freeze.
- **D-L4-02** (2026-09-05) — W1 executed as a 4-way read-only subagent fan-out (root / timing pair /
  purification+remedial chain / verdict spine + rectification) per C8 item 4, rather than serially.
- **D-L4-03** (2026-09-05) — Canary independently corroborated: the frozen manifest's own L4
  `wave_index` split is identical to the DAG tiers derived in D-L4-01. W4 will follow the manifest
  waves; no re-derivation needed.
- **D-L4-04** (2026-09-05) — Three cross-layer/shared-surface findings routed to adjudication rather
  than worked around or silently patched (C5: shared campaign tooling is Conductor-owned). I did not
  touch `dispatch_nirmana_campaign_wave.py` or `definitions.ts`. Continuing W1/W2, which are never
  gated.

## Findings ledger (pre-W1, from the live registry read)

- **F-L4-A (all 9 assets):** `target_floor` NULL · `expected_volume_formula` NULL ·
  `expected_volume_inputs` NULL · `integrity_check_sql` NULL. Under **C12** this is the named defect
  condition verbatim ("NULL is the defect"); under **§N.4** the floors are simply unset. Whole-layer
  W2 item — nine derivations owed, and per C12 "derive, never pick".
- **F-L4-B (all 9 assets):** `catalog_status='DRAFT'` across the entire layer, while all nine have
  real build history on two charts and live serving consumers. Labelling drift to triage in W2.

## Conductor rulings binding on L4

- **#1732 — D-CND-04 (BINDING, effective immediately, campaign-wide).** `ph_nimitta` /
  `phala_anchors` rebuilds are **HELD** until L4 announces the deterministic-key capability under
  `## CAPABILITIES LANDED` on `main`. L4 owns the key's shape, the one-time remap of the existing 195,
  and a D-CND-03-partitioned referential-integrity detector. Blast radius verified by the Conductor:
  **6,606 rows across 9 tables — seven of them L4's own.** L4's tables self-heal on a whole-layer
  rebuild; **L5's never do** (`mi_bhavisya` deliberately preserves adjudicated rows, so the safeguard
  becomes an orphan generator). ACK + verified design refinement posted; **W3-0 in flight.**
  My W1 had graded this *verify-only, handed to L5* — **withdrawn, ownership accepted** (D-L4-13).

## Adjudication issues filed (C3/C7)

- **#1718 — ADJ-L4-01** *(not blocking L4; L1 meets it first)* — charter C2.3's writer-digest
  generation-pin is enforced for L0 only. `dispatch_nirmana_campaign_wave.py:731` gates the receipt
  path on `layer == "L0"`; for L1–L5 `canonical_analysis_digests` stays `None` and the whole
  writer-digest comparison (`:332–:340`) is skipped. The live *registry fingerprint* IS still
  enforced — but `REGISTRY_CONTRACT_FIELDS` carries no writer digest, so a W3 **writer** edit leaves
  stale analysis evidence reading "current". An unearned green in the §N.8 sense. Recommendation:
  carry `writer_digest_sha256` in the analysis payload and compare it layer-agnostically —
  `nirmana-writer-digests.json` already covers all 128 assets (ph 9/9), so no new per-layer
  generated file is needed. *(Corroborated independently: the Conductor's own new `egate.sql`
  deliberately returns `OPEN-PENDING-PIN`, never `OPEN`, because C2.3 cannot be established.)*
- **#1723 — ADJ-L4-02 (CAMPAIGN-BLOCKING, 81 of 128 assets)** — **no `per_chart` asset can produce
  `integrity_verified`.** `definitions.ts:1619` falls back to `count_sql` when `integrity_check_sql`
  is NULL; `:1622` runs `client.query(detectorSql)` with **no parameter array**; every per_chart
  `count_sql` is `… WHERE chart_id = $1`. Verified live against production: `there is no parameter
  $1`. Never exercised because L0 is 100% `global` scope — C12's own doctrine one layer up, a
  detector path that has never run. The FROZEN orchestrator is **not** implicated
  (`asset_runner.py:773` has no `count_sql` fallback), so no freeze exception is needed.
  Recommendation: per-layer chart-agnostic `integrity_check_sql` (C12 requires it anyway) + harden
  the fallback to reject a parameterized detector with an actionable message instead of an opaque
  Postgres error.
- **#1739 — ADJ-L4-04** — `seed_native_phala_anchors()`: a deployed function inserting hand-authored
  predictions with hand-assigned confidences into `phala_anchors`, citing the deleted FORENSIC v8.0,
  **live-routed** at `POST /api/compute/phala/seed_anchors` and held back only by a schema mismatch —
  while its acceptance gate asserts an idempotency PASS over a function that cannot run. Raised rather
  than fixed: it sits inside the native-ruled P7 parking and would require dropping a deployed DB
  object. Recommendation: sever the route, keep the function, fix the false PASS regardless.
  **Not blocking.**
- **#1725 — ADJ-L4-03** — two contradictions between the ratified charter and the shared dispatcher.
  (1) `campaign_prerequisite_asset_ids` (`:435–:464`) requires **every asset in every lower-ranked
  layer**, never consulting dependency edges, and `:786–:794` makes a miss fatal with no override —
  so `ph_nimitta` would need **104** frozen assets where C2's E-gate asks for **46**. Asset-frontier
  pipelining is defeated by the tool. (2) `:797–:804` refuses dispatch when **any** build run is
  active campaign-wide — so C5's ≤3-slot budget and #1713's slot ledger are unreachable; the tool
  enforces ≤1. Recommendation: adopt C2's ancestor closure (the Conductor's own `egate.sql` already
  implements it) and turn the blanket refusal into the ≤3 cap the charter published — while naming
  honestly that I have **not** measured live connection headroom for 3 concurrent runs.

## Held items

Charter C6 capability-deltas, declared at session open. All four are W3 items; **W1 and W2 proceed
in full regardless** (C2: W1/W2 are never gated).

| # | held item | waits on | source |
|---|---|---|---|
| **H-1** | one agreement line per verdict | **L2** consensus capability — `bo_samvada` populating `system_convergence_count` / `cross_system_consensus_count` | plan §5 L2 + D-SYNTHESIS |
| **H-2** | strongest śruti quote per verdict | **L2** grounding capability — `grounding_tier` + `classical_sources_array` on the interpretive signal classes | plan §5 L2 + D-GROUNDING |
| **H-3** | `tail_watch` in outlooks | **L2** tail capability — `low_salience_high_consequence` promoted to a first-class serving input | plan §5 L2 + D-SALIENCE |
| **H-4** | varshaphala / tithi-praveśa consumption **proof** into anchors (Discovery D-7) | **L3** tithi-praveśa verification landing | plan §5 L3 + my §5 mandate |

**Unheld and proceeding now:** prediction-provenance hygiene (parked-P7 seam) verification ·
honest-probability-surface preservation · all of W1 · all of W2 · the F-L4-A floor/volume/integrity
derivations.

Polling for **`## CAPABILITIES LANDED`** on `origin/main` in `L2_STATE.md` and `L3_STATE.md` each
loop.

## CAPABILITIES LANDED

Charter C6 — each NEW capability downstream layers may consume, one line, with its PR number.

_(none yet — L5 Mīmāṃsā is my only downstream consumer)_

## Handed across to other sessions (W2 §8)

- **L5** — `mi_bhavisya.py:178` writes an **anchor_id into `source_pramana_id`** (195/195 resolve as
  `phala_anchors.anchor_id`, **0/195** as `phala_pramana.pramana_id`, both written in the same build
  8 s apart — never staleness), while five generated projections advertise the ph_pramana link. Also
  `mimamsa_anchor_adjustment.multiplier = 0.95` on all 195 rows with `evidence_n = 0`.
- **L2** — is `bodha_discoveries.discovery_id` stable across a `bo_anveshana` rebuild? It has no column
  default, so a writer assigns it; if it is fresh-per-build, D-CND-04 applies to `bo_anveshana` and my
  discovery-sourced anchors inherit the problem. Also: `bodha_cdlm_cells.cell_evolution_gradient_score`
  is 100% NULL across 280 and 75 cells (disposition needed — my fix is correct either way); `bo_upaya`'s
  real chapter-level citations sit unpropagated on 135/135 rows.
- **L3** — `kala_convergence.convergence_id` and `kala_bhavishya.id` are **`bigserial`** and neither
  table declares a natural-key index; **anything storing a `convergence_id` across a rebuild has the
  D-CND-04 problem.** Separately, **the election seam**: four live surfaces answer election-adjacent
  questions and **no arbiter exists anywhere** (`grep partially_aligned|adjudicated_by|temporal_concordance`
  → 0 matches across all three trees); the one wire between `ph_muhurta` and `kala_elect_get` queries
  three columns that do not exist and has been dead since the schema changed. Write-set overlap to
  agree before either of us touches it: `kala_upaya_diagnosis.ts`, `kala_views/upaya.ts`,
  `kala_views/elect.ts`, `muhurta_finder.ts` — Kāla names over L4 assets.

## Cost ledger

| asset | wall-clock | tokens | notes |
|---|---|---|---|
| _(layer-wide)_ bootstrap + live registry/E-gate/manifest read | ~10 min | — | 8 read-only DB queries, 0 writes |
| _(layer-wide)_ `npm ci` in worktree (C4 local-verification prereq) | ~6 min | — | background, exit 0 |
| _(layer-wide)_ shared-tooling audit → 3 adjudication issues | ~35 min | — | read-only; #1718, #1723, #1725 |
| _(layer-wide)_ W1 fan-out | ~11 min wall | ~702k subagent | 4 concurrent read-only subagents, 232 tool uses |
| _(layer-wide)_ W1 deliverables + PR #1735 | ~25 min | — | 5 documents, ~2,400 lines |
| _(layer-wide)_ W2 DECIDE + #1739 + the #1732 design | ~40 min | — | 9 routes, 85 findings triaged, 13 decisions |

## Slot claims (C5)

_(none — no L4 asset is E-gate-open; `ph_nimitta` has 37/46 ancestors unfrozen)_

## Heartbeat

- `2026-09-05T~04:15Z` — L4-W1 — session open: charter read, `NIRMANA_HOLD` absent, worktree +
  `npm ci` done, 9-asset cohort and E-gate position live-verified, canary derived, W1 fan-out
  dispatched, #1718 filed.
- `2026-09-05T~04:40Z` — L4-W1 — shared-tooling audit complete; #1723 (campaign-blocking) and #1725
  filed; state file rebased onto the Conductor's stub shape. No slot claimed (nothing dispatchable).
- `2026-09-05T~05:20Z` — L4-W1 — all four subagents returned; five W1 deliverables written; PR #1735
  opened with auto-merge armed.
- `2026-09-05T~06:00Z` — L4-W2 — DECIDE complete (9/9 `changed`); #1739 filed; ruling #1732 read,
  accepted, and answered with a **verified** design refinement — the obvious deterministic key would
  not in fact have been deterministic, because it embeds two `bigserial`s. W3-0 next. No slot claimed
  (nothing dispatchable; `ph_nimitta` is additionally held by #1732 until I lift it).
