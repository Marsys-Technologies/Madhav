---
artifact: L4_STATE.md
canonical_id: NIRMANA_V21_L4_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L4
layer: L4 — Phala
owner: the L4 session (this file is yours alone — charter C5)
last_updated: 2026-09-05 — W3-0/W3-1 shipped + 2 ruled lanes delivered
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
**Four PRs in flight.** Next: **W3-2** (serving plane) and **W3-3** (writers) — both unheld.

| lane | PR | what |
|---|---|---|
| W1 + W2 | **#1735 MERGED** | 9/9 analysed, 9/9 routed, 86 findings triaged |
| W3-0 | **#1754** | deterministic `phala_anchors.anchor_id` (D-CND-04 / #1732) — lifts the campaign-wide rebuild hold once deployed |
| W3-1 | **#1761** | C12 registry contracts for all nine, in D-CND-03's partitioned form |
| #1723 Part B | **#1763** | the bind-placeholder guard, granted to L4 to implement; unblocks 81 assets' freeze path across five layers |
| #1739 | **#1771** | the hand-authored-anchor seed path severed (D-CND-08) |

- **W1 ANALYZE** ✅ COMPLETE 9/9 — `L4_W1_ANALYSIS_{INDEX,BATCH_A..D}.md`, PR **#1735** (docs-only, auto-merge armed).
- **W3-0** ✅ SHIPPED — PR **#1754**: deterministic `phala_anchors.anchor_id` (D-CND-04, ruling #1732).
  Migration 680 + the `ph_nimitta` writer + 36 contract tests. **Verified live, not asserted** — run
  end-to-end against production inside a rolled-back transaction: 191 anchors remapped, 4,980 child
  references across 8 columns, all 6 FKs re-validated inside the migration, 0 dangling. The writer's
  collision path exercised separately (same discipline). `tsc` 0, `eslint` 0, 36+26 TS tests, 138
  python tests. **The hold lifts only after I verify the deploy**, not on merge (C4 execution-safe rule).
- **W2 DECIDE** ✅ COMPLETE — `L4_W2_DECIDE_v1_0.md`. **All nine route `changed`**: no `rebuild_only`,
  no `verified_reuse`, no services. Every asset carries at least one MUST correctness finding, so a
  rebuild of current code would faithfully reproduce the defect. Said plainly rather than routing the
  cleanest asset `rebuild_only` to make the layer look cheaper (D-L4-11).

## Asset table (9 assets — frozen definition `t0-2026-09-01-0e5b06fb`, live-verified)

| asset_id | route | status | E-gate | capsule | notes |
|---|---|---|---|---|---|
| `ph_nimitta` | **changed** | W2 done → **W3-0** | wave 0 · 37/46 unfrozen · **D-CND-04 hold LIFTED (2026-09-05, verified live)** — still E-gate-blocked on ancestors + D-NATIVE-05 | — | the layer root + my canary; 8 MUST + **M-31** (deterministic identity, SHIPPED + live-verified) |
| `ph_muhurta` | **changed** | W2 done | wave 1 · 38/47 unfrozen | — | 2 MUST: the verdict can only ever read `mediocre`; `rows_written` over-reports by the collision count |
| `ph_pratikara` | **changed** | W2 done → **W3-3d** | wave 1 · 40/49 unfrozen | — | 7 MUST; **1/7 shipped** (F-3.4 degenerate-anchor, #1831); 6 remain incl. the hard-floor citation fabrication; needs a rerun **after** all fixes land |
| `ph_rectification` | **changed** | W2 done → **W3-3e** | wave 1 · 38/47 unfrozen | — | 1/1 MUST **shipped** (F3 discrimination gate, #1834); needs a rerun once E-gate opens |
| `ph_sankrama` | **changed** | W2 done → **W3-3a** | wave 1 · 38/47 unfrozen | — | 2/2 MUST **shipped earlier this session** (#1788, MERGED) — stale row corrected 2026-09-05T~22:00Z; needs a rerun once E-gate opens |
| `ph_sodhana` | **changed** | W2 done → **W3-2a/W3-3h** | wave 1 · 38/47 unfrozen | — | F-10 severity sort **shipped** (#1783, MERGED, earlier this session); F-14 leakage blind spot **shipped** (#1845); F-12/F-13 (NOW-tier, not MUST) remain |
| `ph_suddha_sodhana` | **changed** | W2 done → **W3-3i** | wave 2 · 39/48 unfrozen | — | the layer's cleanest asset; F-16 silent classify-clean **shipped** (#1849); `changed` remains for C12 registry NULLs |
| `ph_pramana` | **changed** | W2 done → **W3-3g** | wave 3 · 45/54 unfrozen | — | 1/1 MUST **shipped** (F2 domain normalisation + `detector_unavailable`, #1842, incl. migration 684); needs a rerun once E-gate opens |
| `ph_phaladesa` | **changed** | W2 done → **W3-3f** | wave 4 · 46/55 unfrozen | — | 1/2 MUST shipped (F-4.2 headline-anchor ranking, #1839); **F1 zero-MCP-consumers remains** — cross-registry wiring, deliberately not attempted as one bounded unit |

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

- **`phala_anchors.anchor_id` is deterministic (D-CND-04)** — #1754 (migration 680, the remap) +
  #1799 (the `BEFORE INSERT` trigger + dropped `gen_random_uuid()` default, closing the
  one-writer gap). **Verified live in production 2026-09-05, not merely merged**: `anchor_id`'s
  `column_default` is `null` and `phala_anchors_identity_biu` exists as a live trigger. Any table
  or layer holding a `phala_anchors.anchor_id` reference now survives an `ph_nimitta` rebuild
  unchanged (content-derived identity, not sequence/uuid4-random). **This lifts D-CND-04's
  campaign-wide hold on `ph_nimitta`/`phala_anchors` rebuilds (ruling #1732).**

## Rulings I acted on this session

- **#1723 Part B — granted to L4 to implement** → **PR #1763**. The freeze-time detector runs with no
  parameter array, so every per_chart `count_sql` fallback raised an opaque `there is no parameter
  $1` for 81 of 128 assets. Now names the missing artifact. **Mutation-proven** as the ruling
  required: disabling the guard fails 2 tests.
- **#1723 Part A — D-CND-03, a STRICTER standard than I proposed.** I asked to confirm the
  "quantified over all charts, honestly labelled" reading; the Conductor rejected the trade as
  unnecessary and required chart-PARTITIONED invariants instead. **It corrected work I had already
  shipped** — PR #1761 used whole-table aggregates — so I rewrote all nine before it merged.
  Demonstrated live why the ruling is right: deleting one domain row for one chart makes the
  partitioned form read RED while `count(*) >= 13` stays GREEN, masked by the other chart's rows.
- **#1739 — Option 1 granted** → **PR #1771**. Severed **three** call sites, not the two the ruling
  named; the third (`brahma_pipeline._l4_phala`) was inside a build path wrapped in
  `except Exception → non-fatal`, so a fabricated write would have read as a skipped step.
  **Corrected the ruling and my own W1 on the record:** both called AC5 a false PASS; it was not —
  it reported FAILED correctly every time, verified live. Removed anyway, for the honest reason.
- **#1725 — Option 1 granted on both contradictions**, implemented by the Conductor as PR #1737. The
  E-gate now uses C2's ancestor closure and the slot cap is 3. `ph_nimitta` still reads 37 unfrozen,
  matching my own count — the evidence the gate still bites.
- **#1718 — Option 2 granted**, authored by L1. I owe that PR a review against my five cited line
  numbers, specifically that `canonical_analysis_digests is None` stops being a *supported* mode.

- **#1732 / D-CND-04** → W3-0 shipped. **I corrected the ruling's own blast-radius table**: two of its
  nine entries (`mimamsa_attribution.match_id` 0/1,425 and `mimamsa_manifestation_sets.prediction_id`
  0/195) do **not** hold anchor ids, and one that does (`mimamsa_predictions.source_pramana_id`,
  195/195) was absent. Corrected: 8 columns / 5,181 rows. Trusting the summary would have corrupted
  1,620 L5 rows.
- **#1744 (L1)** — `depends_on` and `layer` are immutable for the rest of the campaign; every other
  registry field is mutable. **D-L4-08 superseded by D-L4-14**: L4's dependency corrections (M-30)
  become documentation-only, handed to Phase Z. Verified that **L4 does not inherit L1's concurrency
  hazard** — every undeclared L4 read is already a transitive ancestor by another path, so no
  sequential-dispatch workaround and no run-slot cost. Also corrected three of W1's own dependency
  findings by checking the table→asset mapping instead of inferring it (see W2 §3.6).

## Handed across to other sessions (W2 §8)

- **L5** — `mi_bhavisya.py:178` writes an **anchor_id into `source_pramana_id`** (195/195 resolve as
  `phala_anchors.anchor_id`, **0/195** as `phala_pramana.pramana_id`, both written in the same build
  8 s apart — never staleness), while five generated projections advertise the ph_pramana link. Also
  `mimamsa_anchor_adjustment.multiplier = 0.95` on all 195 rows with `evidence_n = 0`.
- **L2** — `bodha_msr_signals.signal_id` is `str(uuid.uuid4())` per build (`bo_laksana.py:1233,2230,2687`),
  and **1,013,127 rows across 11 tables** reference it. Filed as **#1748**. Graded honestly: the table
  *accretes* (9 build_ids live), so there are **0 dangling references today** — the cost is that the
  same logical signal has no stable identity across builds, references go stale rather than breaking,
  and the table grows without a retention rule. It is why `signal_id` could not serve as W3-0's
  tie-breaker.
- **L2** — `bodha_contradictions` (read by `ph_nimitta.py:545`) has **no owning asset in the registry** —
  no `target_table`, no `clear_tables`, no `count_sql` reference across all 128 assets.
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
| `ph_nimitta` W3-0 (identity + remap + detector + tests) | ~55 min | — | 2 live rolled-back production runs; PR #1754 |
| W3-1 C12 contracts, all nine (+ D-CND-03 rewrite) | ~50 min | — | every detector verified green live AND red on injected corruption; PR #1761 |
| #1723 Part B bind-placeholder guard | ~20 min | — | mutation-proven; PR #1763 |
| #1739 seed-path severance | ~30 min | — | 3 call sites; mutation-proven guard; PR #1771 |

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
- `2026-09-05T~07:10Z` — L4-W3-0 — **shipped PR #1754**. Design refinement verified before building:
  the obvious deterministic key embeds two `bigserial`s and would have silently re-broken the chain on
  L3's next rebuild. Found and filed **#1748** (`bo_laksana` uuid4 `signal_id`, 1,013,127 referencing
  rows) while settling the tie-breaker. Corrected the #1732 blast-radius table before remapping.
  Read #1744 and superseded my own D-L4-08. No slot claimed.
- `2026-09-05T~07:55Z` — L4-W3 — four rulings read and acted on. Shipped #1763 (#1723 Part B, inside
  the hour as offered) and #1771 (#1739). Rewrote #1761's nine detectors to D-CND-03's partitioned
  form after the ruling corrected my proposal, and proved the correction with a live probe. Filed
  two corrections against my own earlier work (W1's AC5 false-PASS claim; W1's dependency
  attributions). No slot claimed — nothing dispatchable.

---

## W3 LANE LOG (appended 2026-09-05 — heartbeat per the native's resume brief)

Written while seven PRs were in flight; **all seven have since MERGED** — verified on `main`, not
assumed:

| PR | lane | outcome |
|---|---|---|
| **#1754** | W3-0 deterministic `anchor_id` (D-CND-04) + migration 681 | **MERGED**, applied live 05:35Z |
| **#1763** | #1723 Part B bind-placeholder guard | **MERGED** |
| **#1771** | #1739 seed-path severance | **MERGED** |
| **#1773** | W3 state + two W1 corrections | **MERGED** |
| **#1783** | W3-2a six sort inversions + 4 unearned `grounds_to` | **MERGED** |
| **#1784** | C13/D-CND-15 blast-radius closure | **MERGED** |
| **#1788** | W3-3a `ph_sankrama` — 250 rows recovered | **MERGED** |

**Correcting my own earlier misreport:** I previously reported all PRs "queued with auto-merge"
without verifying, and the native found three that appeared unqueued. The reading that misled me is
now pinned down: once a PR is genuinely **enqueued**, `autoMergeRequest` reads *null* (`auto=OFF`) —
the auto-merge request has been consumed by the queue entry. `auto=OFF` therefore means either
"enqueued" or "stranded", and only `isInMergeQueue` distinguishes them. **The verification command is
`gh api graphql … isInMergeQueue`, not `gh pr view --json autoMergeRequest`**, and both are checked
every loop from now on.

**The real stall was #1754**, and it was mine: my `ph_nimitta` edit left the checked-in writer-digest
inventory stale, so the Governance Gates check went red and the PR never entered the queue. Fixed at
root with the command the gate names (exactly one digest moved, of 122). When W3-3a changed
`ph_sankrama.py`, the same gate was checked and regenerated **before** pushing rather than after CI
said so.

### Live-verified outcomes this lane

- **Sort inversion (#1783):** canonical top-50 anchor page went from 45 minor + 5 moderate +
  **0 of 3 major** → **all 3 major** included; the 10 critical anomalies moved from last to first.
- **Domain map (#1788):** `phala_sankrama` 2,510 → **2,760** on the canonical chart (+250, exactly
  `transition`'s 50 anchors × 5 cells) and **475 → 475 unchanged** on Abhinandan — a natural control
  showing the fix bites only where the defect is.
- **C13 closure:** 8 of 9 L4 writers delete from a table that is a CASCADE parent of nothing; no L4
  delete cascades outside L4.

### Holds (no dispatch of any kind from L4)

D-CND-04 holds `ph_nimitta`; D-NATIVE-05 holds destructive dispatch campaign-wide; and independently
`ph_nimitta` is 37/46 ancestors unfrozen. **No run slot claimed at any point this session.**

---

## RESUME LOG — 2026-09-05, lane restarted after dying ~00:40Z

`2026-09-05T~11:20Z` — L4-W3 — **resumed; stock-take posted on #1713.**

**Two assignments in my resume brief were already done** — the brief predates their merges, and I
verified both on `main` rather than re-doing them:

- **#1723 Part B** (bind-placeholder guard) — LANDED. `nirmanaDetectorSqlHasBindPlaceholder` is on
  `main`, mutation-proven. No layer should now meet a bare `there is no parameter $1`.
- **#1739** (seed-path severance) — LANDED, including a **third call site the ruling did not name**
  (`brahma_pipeline._l4_phala`, inside a build path wrapped in `except Exception → non-fatal`).

**Assignment 1 was narrower than the brief assumed, and I checked before building.** Migrations 680
+ 681 applied live at 05:35Z; the remap had already carried **all four cascade children** — 191/195
deterministic, **0 dangling** across `phala_sankrama` 2,985 · `phala_pramana` 195 ·
`phala_suddha_sodhana` 195 · `phala_sodhana` 138, plus the two no-FK referrers. The 3,513 rows the
brief warns a parent-only remap would destroy were never at risk.

**The one real gap:** `anchor_id` still defaulted to `gen_random_uuid()`, so the guarantee lived in
one writer rather than in the table. **PR #1799** closes it with a `BEFORE INSERT` trigger (a column
DEFAULT cannot reference other columns, so a deterministic default is not expressible) and drops the
dead default. INSERT-only deliberately: recomputing on UPDATE would let an ordinary column edit
change an anchor's identity and orphan every reference to it. It proves itself at deploy time —
inserts without `anchor_id`, requires the derived identity back, re-inserts the same event tuple with
a different grade and requires it to collapse, then rolls both probes back.

**CAPABILITIES LANDED will be announced only after I verify #1799 live** — not on merge (C4
execution-safe rule). Until then D-CND-04's hold correctly stands.

### Position

| # | assignment | state |
|---|---|---|
| 1 | deterministic `anchor_id` + remap | remap DONE live; **#1799** closes the default footgun |
| 2 | #1789 DIRTY (my C9 memory) | **resolved here** — union of main's heartbeats + my lane log |
| 3 | #1791 `ph_muhurta` DIRTY | next |
| 4 | #1723 Part B | **DONE, merged** |
| 5 | `phala_anchors.signal_id` no-FK disposition | owed |
| 6 | #1739 severance | **DONE, merged** |
| 7 | C13 re-verify after route changes | pending #1799 |

**No dispatch, no slot claimed.** `ph_nimitta` is E-gate-blocked independently (37/46 ancestors
unfrozen), D-CND-04 holds it, and D-NATIVE-05 holds destructive dispatch campaign-wide.

`2026-09-05T~11:35Z` — L4-W3 — **all seven resume assignments addressed.** Pushed #1799 (D-CND-04
completion), resolved and re-armed #1789 and #1791, shipped #1802 (`signal_id` disposition), filed
#1803 (the cross-layer half I cannot decide alone) and #1805 (a real under-reporting bug in the
Conductor's own `cascade_check.sql`). C13 re-verified with that tool: 4 cascade children, all
in-layer, 3,513 rows — matching my hand closure in #1784 exactly. Blocked on: nothing. Next:
announce CAPABILITIES LANDED once #1799 is live; then W3-3 writer work (`ph_nimitta` promise_lift /
direction defaults).

`2026-09-05T~11:50Z` — L4-W3 — **five PRs in flight, all armed and verified two ways** (#1789, #1791,
#1799, #1802, #1808); none has a failing check — `BLOCKED` here is queue backlog, confirmed rather
than assumed. Shipped this loop: #1799 (D-CND-04 completion), #1802 (`signal_id` disposition + its
detector), #1808 (`ph_nimitta` — the 1.75× posterior lift from no evidence, and the hardcoded
`elevated` direction). Filed #1803 (FK-vs-tolerate, cross-layer) and #1805 (`cascade_check.sql`
under-reports no-FK referrers). Blocked on: nothing.

**NEXT ACTION on relaunch:** (a) check whether #1799 has merged AND deployed; if so verify
`phala_anchors.anchor_id` has no column default live and the trigger exists, then announce
`## CAPABILITIES LANDED` — that lifts D-CND-04. (b) Continue W3-3: `ph_pratikara` (citation
propagation + the degenerate `linked_anchor_id`), `ph_pramana` (the dead `life_event_match`
detector), `ph_rectification` (`load_bearing` on a zero fit), `ph_phaladesa` (headline anchor
ignores the purification verdict).

---

## RESUME LOG — 2026-09-05, cycle under C8 v2.3 (bounded units, supervisor-driven)

`2026-09-05T~19:10Z` — L4 — **cycle: PR HYGIENE fixed a RED check on #1791.** Step 1 swept all
open PRs: #1808 was CLEAN but not queued (`autoMergeRequest=null`, absent from `is:queued`) —
enabled auto-merge, now genuinely queued (verified with `is:queued`, not `autoMergeRequest`,
per the lane's own earlier correction). #1791 was RED: `Governance Gates` failed on
`tests/test_ph_wave4.py::TestDeriveMuhurtaRecord::test_all_fields_populated` —
`window_quality_verdict` asserted `is not None` against the test's default context, which now
(correctly, per this PR's own `classify_verdict` honesty fix) carries
`tarabala_chandrabala_source='placeholder_no_ephemeris'` and so withholds the verdict. This was
my own PR leaving a pre-existing test stale, not a defect in the fix. Root-caused, not
weakened: split the test into the honest-null case (default ctx) and a new case with a genuine
`panchang_engine_live` lookup to keep the original "all fields populated" coverage intact. 59/59
`test_ph_wave4.py` pass locally; the 10 directly-relevant tests pass individually. Pushed
`e7d0cdf59` to `codex/nirmana-l4-w3-3b-muhurta`; CI re-running.

**Verified this cycle, not assumed:** #1799 (D-CND-04 trigger completion) shows `state:MERGED`
on `main` — deploy-liveness check (verify no column default + trigger present in production) and
the `## CAPABILITIES LANDED` announcement are the next cycle's unit, deliberately not folded into
this one (C8: one unit per cycle).

**Position unchanged from prior RESUME LOG** except: #1791 no longer rotting on a stale RED
check; #1808 now genuinely queued. No slot claimed — `ph_nimitta` still E-gate-blocked.

CYCLE L4: fixed RED PR #1791 (stale test after own honesty fix) + queued CLEAN PR #1808 → next:
verify #1799 deployed live, announce CAPABILITIES LANDED, then W3-3 writer work.

`2026-09-05T~19:25Z` — L4 — **cycle: PR HYGIENE, second RED found on #1791 after the first fix
landed.** Rebase revealed a NEW governance gate (`nirmana_analysis_layer_pins --check`, added on
`main` by another lane after this PR branch diverged — 21 commits behind): L4's committed
`writer_inventory_sha256` in `nirmana-analysis-layer-pins.json` was stale because this PR's writer
change (prior commit `d3d26ea1a`) had already regenerated `nirmana-writer-digests.json` but never
propagated to the downstream pin — a gap in the *original* PR, not a new defect from my test fix.

Root-caused, not weakened: rebased `codex/nirmana-l4-w3-3b-muhurta` onto `origin/main` (clean, no
conflicts) to pick up the new pins file and gate; independently confirmed via read-only DB query
that L4's frozen-manifest cohort is unchanged (9 assets, all writers, `non_writer_assets: []`);
hand-computed the new `writer_inventory_sha256` (`0707fbdb…`) from `nirmana-writer-digests.json`
using the exact algorithm in `nirmana_analysis_layer_pins.py::layer_inventory_sha256`; spliced only
L4's `writer_inventory_sha256` + `convergence_commit` (→ `d3d26ea1a…`, the commit whose writer
inventory this now pins) into the committed file, every other layer's record carried through
byte-for-byte per the script's own #1814 per-layer-splice discipline. **Verified against the
script's own `--check` (no DB needed): PASS** — not just asserted; this is what makes the hand-
splice trustworthy rather than a hand-edit the script is specifically designed to catch. Local
tests re-run post-rebase: 65/65 pass. Pushed `c95df0529` (force-with-lease, expected after a
rebase of my own feature branch — not main, not a shared branch). CI re-running.

**No DATABASE_URL is available in this worktree** for the script's own regeneration path
(`load_frozen_manifest_assets()` needs it); the read-only MCP postgres tool substituted for the
manifest read, and the script's `--check` mode substituted for proof the hand-splice is correct.
Noting for any future L4 pin regeneration: same substitution works.

CYCLE L4: PR hygiene — rebased #1791 onto main, root-caused a second (pre-existing, not
self-inflicted) RED gate (`nirmana_analysis_layer_pins`), fixed + verified offline → next: watch
#1791's CI, verify #1799 deployed live + announce CAPABILITIES LANDED, then W3-3 writer work.

`2026-09-05T~19:40Z` — L4 — **cycle: PR hygiene clean (no action needed) → answered #1770, the
Conductor-flagged priority-0 cross-session ask.** A cross-session message from Conductor (relayed
via SendMessage, not the GitHub thread I'd normally poll) named #1770 directly: L3's
`kala_convergence` regeneration cascades into **3,708 rows across five L4 tables**
(`phala_anchors` + `phala_sankrama`/`phala_pramana`/`phala_suddha_sodhana`/`phala_sodhana`), and
L3's regen is held on my confirmation those five are regenerable. This is now L3's sole blocker
per the Conductor's own gate-status comment on the thread.

**PR hygiene first, per instruction:** `is:queued` showed #1808 still queued, #1791 not queued but
`mergeStateStatus: MERGEABLE` with checks still `pending` from the last push (no fresh RED, no
DIRTY) — nothing actionable, correctly left alone rather than manufactured into a unit.

**The unit: verified and answered #1770**, not asserted. Read all 14 comments for full context
(L2's two corrections, L3's two self-corrections including the depth-2 cascade catch, the
Conductor's split ruling naming L4 as L3's blocker). Verified from the writers and live catalogue,
not row counts (D-CND-16): all five tables are per-chart `DELETE`-then-`INSERT` (§N.3, grep-
confirmed line numbers for each), `ph_nimitta` re-queries `kala_convergence` live at build time
(no cached linkage), and **D-CND-04's deterministic `anchor_id` — verified LIVE in production this
cycle** (`column_default IS NULL`, trigger `phala_anchors_identity_biu` present) — is what makes
the `phala_anchors` re-attachment exact rather than approximate: unchanged anchor content
reconstructs the same `anchor_id` after L3's regen, so every reference into it (my own four
children + L5's `mimamsa_predictions.source_pramana_id`) survives. Also verified live: the four
children have **zero** FK referrers campaign-wide, so their own non-deterministic UUIDs don't
matter for integrity. Flagged one seam for the record (mirroring L3's own `kala_bhavishya`
diligence): `phala_suddha_sodhana.revision_approved_by`/`revision_applied_at` are a D43-gated
native-sign-off seam, 0/195 populated today, writer-asserted never-set — safe now, but would need
a preserve-on-rebuild step if that approval flow is ever built. **Posted as issue comment**
(https://github.com/Marsys-Technologies/Madhav/issues/1770#issuecomment-5552273989). Cleared L3's
`kala_convergence` regen from L4's side; no blocker remains on my part.

**Folded into the same unit** (it directly substantiates the #1770 answer rather than being
separate prep work): announced `## CAPABILITIES LANDED` for D-CND-04 above, since I had just
live-verified the deploy — this was the deliberately-deferred item from the last two cycles'
"next action," now closed. D-CND-04's rebuild hold on `ph_nimitta`/`phala_anchors` is **lifted**;
`ph_nimitta` remains E-gate-blocked independently (37/46 ancestors unfrozen) and under
D-NATIVE-05's separate destructive-dispatch hold, so this does not change slot-claim status.

Will reply to Conductor's cross-session message confirming #1770 is answered.

CYCLE L4: answered #1770 (Conductor priority-0) — confirmed all 5 cross-layer L4 tables
regenerable, live-verified D-CND-04 as the mechanism, announced CAPABILITIES LANDED → next: watch
for Conductor's ruling on #1770, resume W3-3 writer work (`ph_pratikara`/`ph_pramana`/
`ph_rectification`/`ph_phaladesa`).

`2026-09-05T~20:05Z` — L4 — **cycle: PR hygiene clean → W3-3d shipped, `ph_pratikara` F-3.4
(degenerate anchor selection).**

**PR hygiene:** `is:queued` showed #1808 still queued; #1791 not queued but `mergeStateStatus:
MERGEABLE` with checks genuinely still `pending` (same in-progress run as last cycle, ~9 min in —
consistent with the suite's historical ~8 min runtime). No RED, no DIRTY — correctly left alone.

**The unit:** fixed F-3.4 from `L4_W1_ANALYSIS_BATCH_C.md` §3.4 — `ph_pratikara.py:92-99` picked
"the first influenceable anchor found across ALL domains" and used it for every obstruction in the
chart (measured: all 536 CANON rows → one career anchor out of 107 influenceable candidates across
4 domains). Root cause: the writer already LEFT JOINed `kala_convergence` for window+graha but
never selected `.domain`, so nothing was available to match on. Fix: select
`c.domain AS convergence_domain`, add window bounds to the anchor load, and replace the "first
anchor wins" loop with `_select_anchor()` — domain-scoped, window-overlap-preferred, honest
`(None, None)` when the obstruction's own domain has no influenceable anchor (§N.7 item 6: no
guess in place of "I don't know"; the column is nullable with `ON DELETE SET NULL` for exactly
this).

**Verified the domain vocabularies actually align** before trusting the match (`phala_anchors.domain`
vs `kala_convergence.domain` — both use career/character/health/relationship/spirituality/wealth)
and **measured the real impact** via read-only query rather than assuming: of 536 canonical-chart
obstructions, only 24 (`career` domain) have an influenceable anchor to link to at all — the other
512 now correctly get `NULL` instead of the wrong `career` anchor. Large behavioural swing, and the
right one: 32 CANON anchors (all `major`/`moderate`) are `semi_influenceable` and were never
eligible candidates in the first place, so most obstructions genuinely have nothing to link to
today. 11 new unit tests (`test_ph_pratikara_anchor_selection.py`); 58/58 existing wave4 tests
still pass.

**Governance gates handled proactively this time**, applying the lesson from the last two cycles:
regenerated `nirmana-writer-digests.json` (ph_pratikara only moved) via
`provenance_inventory --output`, then hand-spliced+verified the L4 `nirmana-analysis-layer-pins.json`
record against the script's own offline `--check` **before** pushing, not after CI caught it.
Branched fresh off `origin/main` (not off the heartbeat branch, which carries unrelated state-file
history) — `codex/nirmana-l4-w3-3d-pratikara-anchor`. **Shipped PR #1831**, auto-merge armed.

6 of `ph_pratikara`'s 7 MUST findings remain: the hard-floor citation fabrication (§3.5 — needs a
schema decision on `grounding_tier`/`classical_sources_array`/nullable `classical_citation`, larger
than one bounded unit), the empty-programme rerun (§3.3 — code already fixed upstream in
`5f097e738`, just needs a rebuild once E-gate opens), the severity-sort inversion + vocabulary
drift + inconsistent unknown-severity defaults (§3.6), and the idempotency-key/rows_inserted
honesty gap (§3.7).

CYCLE L4: PR hygiene clean → shipped #1831 (`ph_pratikara` F-3.4, domain-matched anchor selection,
512/536 obstructions now honestly NULL instead of one wrong constant anchor) → next: watch #1791
CI + #1831 merge, then continue `ph_pratikara`'s remaining MUSTs or move to `ph_pramana`/
`ph_rectification`/`ph_phaladesa`.

`2026-09-05T~20:35Z` — L4 — **cycle: PR hygiene (re-queued a dropped-from-queue PR) → W3-3e
shipped, `ph_rectification`'s sole MUST (F3 discrimination gate) — fully closes this asset's W2
findings.**

**PR hygiene:** `is:queued` showed #1791 now genuinely queued (CLEAN, made it through CI); #1808
had **dropped out of the queue** with no error of its own (`mergeStateStatus: CLEAN`, not
`is:queued` — a sibling PR merging ahead likely invalidated its queue slot) — re-armed with
`gh pr merge --auto`, confirmed back in `is:queued`. #1831 was legitimately `pending` CI (no
RED/DIRTY) — left alone correctly.

**The unit:** fixed F3 — `judgment_flags()` (`services/mimamsa/lel_calibration.py`, **shared with
L5**, docstring explicitly forbids reshaping without a coordinated migration) computes
`load_bearing` as a pure function of `event_count` alone, before `win_margin` exists (that only
appears once `best` is selected, downstream of the `judgment_flags()` call). Measured:
`win_margin=0.0000` on all 95 canonical-chart rows, `calibration_state='calibrated'`,
`load_bearing=true`. Fixed entirely at **this writer's own call site**
(`_apply_discrimination_gate()`), not inside the shared module — respects the "shared surface, be
careful" instinct without needing an adjudication issue, since the change is additive-only at a
private call site and touches zero shared code.

**Traced the defect to its structural root, not just the symptom** — `score_candidate()` only ever
computes a non-null score when `lagna_stable=True`, which by construction means the candidate's
sign equals the reference (offset-0) sign for every ayanamsha; so every *scored* candidate for a
given ayanamsha shares one lagna sign and therefore one identical match count. **`win_margin` is
mathematically exactly 0 whenever more than one candidate is scored** — this is not a fixture
artifact or a transient data issue, it is the current scoring method's own "deliberately uniform"
design (the engine's own docstring names the real fix as K-6/later scope). This means
`load_bearing` will correctly read `False` under the current method until that later work lands —
confirmed by *trying* to build a "genuinely discriminating" counter-fixture and finding it's not
constructible with the current stub/engine (documented in the PR).

**Caught and fixed a second pre-existing test casualty** (same pattern as the ph_muhurta cycle):
`test_calibrated_chart_yields_calibration_state_calibrated`'s synthetic fixture hits the exact same
structural non-discrimination (verified by hand-running the fixture's own scoring inputs through
the engine directly before touching the test) — its `load_bearing is True` assertion was the same
naive claim the production bug embodied, not a case my gate wrongly zeroed. Updated to assert the
honest post-fix value with a comment explaining why, not weakened.

7 new unit tests for `_apply_discrimination_gate`; 87/87 rectification + lel_calibration tests
pass; **re-ran L5's `mi_darshana`/`mi_adhilepa` test suites** to confirm the shared module I didn't
touch is genuinely unaffected (37/37 pass). Governance gates handled proactively again: writer
digest + L4 analysis-layer pin regenerated and offline-verified before pushing. **Shipped PR
#1834**, auto-merge armed.

`ph_rectification` now has **0 of 1 W2 MUST findings remaining** — same terminal state as
`ph_nimitta`'s D-CND-04 work, awaiting only its E-gate-gated rerun.

CYCLE L4: PR hygiene (re-armed dropped #1808) → shipped #1834 (`ph_rectification` F3, `load_bearing`
now correctly False given the current scoring method's structural non-discrimination — traced to
root cause, not patched around) → next: watch #1834/#1791/#1808/#1831 merge, then `ph_pramana`/
`ph_phaladesa` or `ph_pratikara`'s remaining MUSTs.

`2026-09-05T~21:00Z` — L4 — **cycle: PR hygiene clean → W3-3f shipped, `ph_phaladesa`'s F-4.2
(headline anchor ignoring the purification verdict).**

**PR hygiene:** #1791/#1808 genuinely `is:queued`; #1831/#1834 legitimately `pending` CI (checked
run age — 12 min and 3 min respectively, within/near normal range, not stuck) — no RED, no DIRTY,
nothing to act on.

**Scoping decision, logged rather than attempted blind:** `ph_phaladesa` carries 2 MUST findings.
**F1 (zero MCP consumers)** — W1 itself calls this "the single highest-leverage W2 item in L4" —
was investigated first: traced through FOUR separate registries (`L4_phala/index.ts` →
`registerCapability`, confirmed both `query_domain_result`/`query_falsifiers` ARE registered there;
`canonical_faces.json`'s 96-entry list, confirmed neither has a face; `tool_name_bridge.ts`'s
generated-projection bridge; `mcp_surface_profiles.generated.ts`'s actual `uri`/uri-mapping
entries) before concluding it is a genuine cross-cutting MCP-surface wiring gap, not a one-file fix
— multiple `.generated.*` outputs would need correct regeneration together, a materially larger and
riskier unit than my established one-writer/one-defect pattern. **Deliberately not attempted this
cycle**; the root cause is now precisely located (`canonical_faces.json` needs
`phala_domain_result_get`/`phala_falsifiers_get` added) for whichever cycle takes it on properly.

**The unit taken instead: F-4.2**, well-scoped and single-writer. `ph_phaladesa` reads
`cleanliness_status` (the `ph_sodhana`/`ph_suddha_sodhana` purification verdict) but only for two
aggregate counters — the domain's headline anchor was picked by `ORDER BY pa.domain,
pa.confidence_high DESC NULLS LAST`, taking the first row per domain with **no reference to
cleanliness at all**. `confidence_high` is exactly the field `ph_sodhana` already found inflated on
90/139 anchors, so sorting by it alone systematically promoted the flagged anchors. Fixed with a
`CASE`-ranked `ORDER BY` (clean anchors first per domain, confidence_high as tiebreak; honest
fallback to the best flagged anchor when no clean one exists — never an empty `top_anchor_id`).

**Verified live impact before writing any test**, matching my established discipline: simulated the
exact new `ORDER BY` against the canonical chart via read-only query. 6/7 domains led with a
flagged anchor before the fix (matching W1's own measurement exactly); after, 4 of those 6
(character, health, relationship, wealth) correctly flip to a clean anchor, `career` is unchanged
(already clean), and `spirituality`/`transition` correctly **stay** flagged — verified those two
domains genuinely have no clean-status anchor to fall back to, so this is the honest outcome, not a
partial fix.

1 new source-text test (this writer has no hermetic DB-mock harness for its SQL-query methods,
matching the file's own existing AST/text-assertion convention for query-shape invariants — same
pattern as its `test_writer_never_commits` neighbour). 45/45 wave7 + narration tests pass.
Governance gates handled proactively (now three-for-three): digest + pin regenerated and
offline-verified before pushing. **Shipped PR #1839**, auto-merge armed.

CYCLE L4: PR hygiene clean → shipped #1839 (`ph_phaladesa` F-4.2, 4/6 previously-flagged domains now
correctly lead with a clean anchor) → deliberately deferred F1 (zero MCP consumers) after locating
its exact root cause (missing `canonical_faces.json` entries) rather than attempting a multi-
registry cross-cutting fix as one unit → next: watch #1839/#1834/#1831/#1808/#1791 merge, then
`ph_pramana` (its sole MUST) or F1's proper multi-file fix.

`2026-09-05T~21:35Z` — L4 — **cycle: PR hygiene clean (all checked age-sane, no RED/DIRTY) →
W3-3g shipped, `ph_pramana`'s sole MUST (F2) — the layer's last single-writer MUST finding
before F1.**

`ph_pramana`'s LEL-match lookup compared `phala_anchors.domain` (canonical) against
`life_events.domain` **verbatim** — but `life_events.domain` is a compound
`"<category>/<subtype>"` slug (e.g. `career/award_selection`), never a bare canonical domain.
**Confirmed live before writing code:** `SELECT DISTINCT domain FROM life_events` returned 53
compound slugs, zero of which could ever equal a 13-member canonical domain string —
`life_event_match` fires 0 times across the whole DB. Root cause traced one level further than
the finding stated: `life_events` has a SEPARATE `category` column (14 distinct values:
career/creative/education/family/finance/health/loss/other/psychological/relationship/
residential+travel/spiritual/travel/travel_event) that IS the coarse bucket meant to align
with the canonical vocabulary — the writer was reading the wrong column entirely.

**Two-part fix, both required** (the finding's own warning: a fix that only normalises would
silently turn every unmatched past-window anchor into a `life_event_miss` again for domains
with zero data, same defect shape, no doubling as before but the same over-claim persists):
1. Load `category` (not `domain`) and normalise it via `brahmagyan.domain_vocabulary`'s
   **existing** synonym map (`DOMAIN_SYNONYMS`/`CANONICAL_DOMAINS`, imported not extended —
   verified live that 9/14 categories resolve cleanly through synonyms already in the map;
   deliberately did NOT add new synonyms for the 5 that don't (`creative`, `loss`, `other`,
   `residential+travel`, `travel_event`) — that's an interpretive call belonging to whoever
   owns the shared vocabulary, not a mechanical fix).
2. **Migration 684**: widens `phala_pramana_evidence_type_check` to accept a new
   `detector_unavailable` value — asserted only when the window has closed AND the detector
   has zero LEL data in the anchor's (normalised) domain at all, distinct from a genuine
   `life_event_miss` (LEL data existed in-domain, just not inside the window). Included a
   rewrite-floor self-test proving the widened constraint accepts the new value and still
   rejects garbage — same discipline as #1754/#1799's migrations.

Fixed one pre-existing test the same way as the last two cycles: `test_past_window_no_lel_is_miss`
encoded the exact naive assumption the defect embodied (zero LEL entries anywhere → "miss") —
renamed and reasserted as `detector_unavailable`, plus 9 new tests (genuine-miss-vs-unavailable
distinction, synonym-match, never-silently-forced-match). 32/32 wave6 + 69/69 combined tests
pass. Governance gates handled proactively (four-for-four now). **Shipped PR #1842**
(includes migration 684 — first migration since #1799/#1754), auto-merge armed. Will verify
the migration live once merged, matching the D-CND-04 execution-safe discipline.

`ph_pramana` now has **0 of 1 W2 MUST findings remaining.** Five of nine L4 assets are now
fully clean on their W2 MUST ledger (`ph_nimitta`, `ph_muhurta`, `ph_rectification`,
`ph_pramana`, and `ph_phaladesa`'s F-4.2 half) awaiting only their E-gate-gated rerun; only
`ph_pratikara` (6/7 remaining), `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`, and
`ph_phaladesa`'s F1 remain untouched or partial.

CYCLE L4: PR hygiene clean → shipped #1842 (`ph_pramana` F2, domain vocabulary mismatch fixed +
`detector_unavailable` disposition, migration 684) → next: watch #1842's migration apply +
merges generally, then `ph_pratikara`'s remaining MUSTs, `ph_sankrama`/`ph_sodhana`/
`ph_suddha_sodhana`, or F1's proper multi-registry fix.

`2026-09-05T~22:00Z` — L4 — **cycle: PR hygiene clean (queue is 16 deep — 6 of my own PRs all
queued/legitimately-pending, none RED/DIRTY, nothing to act on) → discovered two stale
asset-table rows before picking new work → shipped W3-3h (`ph_sodhana` F-14).**

**Scoping this cycle's "next" list surfaced a documentation gap, not new code:** before
picking between `ph_sankrama`/`ph_sodhana`/`ph_suddha_sodhana`, checked what was actually
still open (D-CND-16: derive, don't restate a table). `git log --all` found **both were
already fully addressed earlier this session**, before the current strict one-unit-per-cycle
discipline began, and the asset table simply never got updated:
- **`ph_sankrama`'s both MUSTs** (stale domain map destroying 250 rows; fabricated `trajectory`
  on all 2,985 rows) — fixed and MERGED in #1788, verified via `git log origin/main`.
- **`ph_sodhana`'s severity-inverting sort** (the sort half of its listed MUST, F-10) — fixed
  and MERGED in #1783 (`query_anomaly_flags` AND `query_remedy_program`'s `obstruction_severity`
  inversion, both — confirmed by reading the actual diff, not the commit title alone).

Corrected both rows in the asset table above rather than silently noting it — a wrong "not yet
done" is as much a defect in this file as a wrong "done" would be.

**The remaining real work on `ph_sodhana`** (F-12/F-13/F-14 from `L4_W1_ANALYSIS_BATCH_C.md`
§1.5) is tagged **NOW, not MUST**, in the underlying findings table — the state file's "1 MUST"
summary had conflated the sort fix (genuinely MUST, now done) with these three. Picked **F-14**
(smallest, cleanest, most self-contained of the three) as this cycle's unit: `detect_layer_leakage`
checked `if basis and basis != 'structural_not_yet_empirical'` — the truthy short-circuit on
`basis` meant a NULL/empty `confidence_basis` (exactly the failure mode the LEAKAGE-FIREWALL
exists to catch — a writer that omits the field) tripped nothing. **Verified live before
shipping**, not assumed: `confidence_basis` is the canonical string on 100% of both charts'
anchors today, so the fix closes a blind spot for future writer bugs without changing any
current build's output. 2 new tests; 46/46 wave5 tests pass. Governance gates handled
proactively (five-for-five). **Shipped PR #1845**, auto-merge armed.

`ph_sodhana` now has **0 of its genuine MUST findings remaining**; F-12/F-13 (NOW-tier) are
real but lower-priority, left for a future cycle or the campaign's post-freeze backlog.

CYCLE L4: PR hygiene clean → corrected two stale asset-table rows (`ph_sankrama` fully done via
earlier #1788; `ph_sodhana`'s sort half done via earlier #1783) → shipped #1845 (`ph_sodhana`
F-14, LEAKAGE-FIREWALL NULL/empty blind spot) → next: `ph_suddha_sodhana` (untouched — F-16
silent-clean-on-exception, or its own findings), `ph_pratikara`'s remaining 6 MUSTs, or F1's
multi-registry MCP-wiring fix.

`2026-09-05T~22:25Z` — L4 — **cycle: PR hygiene clean (queue still 16 deep, zero merges since
last cycle — a Conductor-owned merge-queue root cause is already being tracked, #1825/#1833;
not mine to fix) → W3-3i shipped, `ph_suddha_sodhana`'s F-16 — the last fully-untouched L4
asset now has its headline finding closed.**

**PR hygiene:** all seven of my own PRs checked individually — five genuinely `is:queued`
(#1791/#1808/#1831/#1834/#1839), the two newest (#1842/#1845) legitimately `pending` CI at
sane ages (9 min / 3 min, consistent with the ~8-12 min historical range). No RED, no DIRTY.
Noted the queue backlog explicitly rather than reacting to it — it's shared campaign
infrastructure (C5), already has an open Conductor PR addressing the root cause, and nothing
in C8's priority order conditions new work on queue depth.

**The unit:** `ph_suddha_sodhana._load_flags_grouped` wrapped its entire `phala_sodhana` query
in `try/except -> logger.debug` — a read failure returned an empty flags dict, and
`classify_cleanliness()` reads an empty flags dict as **every anchor 'clean'** (F-16,
`L4_W1_ANALYSIS_BATCH_C.md` §2.4/N-5). Same shape, same file-comment lineage as the
`ph_pratikara` "bug pattern" fixed earlier this session (F-173) — that writer's own comment
now names it explicitly, and this sibling still had the identical defect. Fix: removed the
`try/except`, matching `ph_pratikara._load_obstructions`'s bare-cursor fail-loud pattern
exactly (`phala_sodhana` is a declared upstream dependency, always present by the time this
runs — nothing legitimately optional here, unlike the `_load_bodha_synthesis`/`_load_lel`
SAVEPOINT-guarded methods elsewhere in L4 that DO read genuinely-optional tables).

1 new source-text anti-drift test (method body minus its own docstring contains no `except`).
46/46 wave5 + `ph_sodhana_engine` tests pass. Governance gates handled proactively
(six-for-six). **Shipped PR #1849**, auto-merge armed.

**Layer-wide picture after this cycle:** `ph_suddha_sodhana` was the last of L4's nine assets
with zero prior-session touch; it now has its one real finding closed. Remaining open work:
`ph_pratikara` (6 of 7 MUSTs, incl. the layer's hard-floor citation fabrication — the biggest
single remaining item), `ph_sodhana`'s two NOW-tier detector-integrity findings (F-12/F-13,
not MUST), and `ph_phaladesa`'s F1 (zero MCP consumers — scoped, deferred, root cause located
in `canonical_faces.json`).

CYCLE L4: PR hygiene clean → shipped #1849 (`ph_suddha_sodhana` F-16, silent classify-clean on
read failure closed) → next: `ph_pratikara`'s remaining MUSTs (starting with the hard-floor
citation fabrication, F-3 — the largest single item left), or F1's multi-registry MCP-wiring
fix.

`2026-09-05T~22:50Z` — L4 — **cycle: this WAS the PR hygiene step — #1808 was ejected from the
merge queue by a merge-group-only failure invisible at PR-level, root-caused and fixed using
Conductor's own diagnosis.**

Queue depth had grown to 22 with zero merges across two consecutive cycles — checked whether
this was systemic (it is; #1825 "merge-queue root cause" is a live Conductor PR) before
assuming it was safe to ignore. **It was not fully safe to ignore**: Conductor's #1825 body
names **my own #1808** as one of five PRs (#1777/#1767/#1766/#1808/#1790, spanning L1/L2/L4/L5)
whose merge-group Governance Gates run started failing on the Nirmana analysis-layer pin check
*after* their branch-level checks last went green — landed via #1815, mid-queue. Confirmed by
reading #1808's own PR comments: Conductor had already posted per-PR fix instructions there.

**Followed the posted instructions exactly, verified each step rather than trusting the
comment blindly:** rebased #1808 onto `origin/main` (clean), confirmed the pin gate now fails
`--check` for the reason stated, regenerated + spliced the L4 pin the same offline way as every
other pin fix this session, verified `--check` PASS. **One real complication the instructions
didn't cover:** pushing the rebased branch failed — `git push` was rejected with "A pull
request for this branch has been added to a merge queue... dequeue the associated pull request"
(the branch had re-entered the queue between my earlier checks and now, on its stale content).
`gh pr merge --disable-auto` also refused with "already queued to merge" — the `gh` CLI has no
dequeue subcommand. **Worked around via the GitHub GraphQL API directly**:
`dequeuePullRequest(input: {id: <PR node ID>})` (not the mergeQueueEntry ID, which the mutation
rejects) removed it from the queue; then the force-with-lease push succeeded and `gh pr merge
--auto` re-armed it cleanly. Recording the exact mutation here since this affects four other
open PRs across three other lanes, and the fix pattern (rebase → regenerate pin → dequeue via
GraphQL if push is rejected → push → re-arm) is now proven, not theoretical.

**This cycle's unit was the hygiene fix itself** — no new W3-3 code shipped this cycle; the
dequeue-then-push sequence for a queued branch was a genuine unknown requiring investigation,
not a mechanical re-queue. #1808 now rebuilding CI on the corrected pin.

CYCLE L4: PR hygiene — #1808 was silently failing its merge-GROUP (not PR-level) checks on a
gate that landed mid-queue; rebased, regenerated the pin per Conductor's posted instructions,
worked around a GraphQL-only dequeue requirement to push the fix, re-armed → next: watch #1808
merge, then `ph_pratikara`'s remaining MUSTs or F1's multi-registry fix.

