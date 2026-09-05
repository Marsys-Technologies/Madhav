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

