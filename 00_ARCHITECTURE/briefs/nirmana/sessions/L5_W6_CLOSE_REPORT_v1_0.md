---
artifact: L5_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_L5_W6_CLOSE_REPORT
version: "0.7-DRAFT"
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

**NOT CLOSED.** W1 ✅ (15/15) · W2 ✅ (15/15 routed) · **W3 ✅ complete, all PRs merged** ·
**W4 🟢 IN FLIGHT — real dispatches executed, not just routed** · **W5 🟢 first real handoff to a
fresh-context verifier in progress** (`lel_events`) · W6 ⬜.

**The lane died at 00:37Z and was resumed once**; separately, a second stale-worktree episode was
found and recovered mid-session (a prior local branch sat on an already-merged commit with 117
stray uncommitted files, discarded after confirming nothing was lost — see `L5_STATE.md`
heartbeat). Nothing real was ever lost either time.

**W4 turned out to be the layer's real contribution, not a formality.** `mi_vistara` (canary 1)
was dispatched and completed — the campaign's first-ever real `mi_*` build execution. Getting its
evidence chain to `accepted_rebuild_observed` then surfaced, in order, **three genuine
campaign-wide structural defects** that no layer had hit before because L5 dispatched the first
real non-L0 builds this session: #1840 (`output_digest_spec` L0-only), #1848 (dispatch
duplicate-guard has no bypass), #1856 (a UUID-serialization crash in core orchestrator
provenance capture). All three independently found, evidenced, and filed rather than routed
around; two already have Conductor fixes in flight (#1861 for #1856, #1851 for #1848, neither
merged yet as of this draft). See §3.6.

L5's freeze is last in the C2 ordering (L0→L1→L2→L3→L4→L5), so this report closes the build arc.
It is being drafted against evidence as that evidence lands, not written at the end from memory.

## §1 — Asset table (15)

Routes are W2-final. Status is live.

| # | asset | route | W3 | W4 | W5 | notes |
|---|---|---|---|---|---|---|
| 1 | `mi_vistara` | `rebuild_only` | ✅ | ✅ built | 🔒 #1848 | **CANARY 1 — BUILT.** `run_id=e45e343b-…`, 18.29s, job logs + DB verified, first-ever `mi_*` provenance receipt. `output_digest_spec` authored (migration 692, first non-L0 entry, #1840). Capsule blocked: `mi_vistara`'s own already-completed run permanently occupies its `triggered_by` — no `accepted_rebuild_observed` possible until #1851 merges AND a fresh dispatch (bundled with another asset) succeeds. |
| 2 | `lel_events` | `static` | ✅ | ✅ `source_accepted` | 🔒 #1869 | **CANARY 2 — TERMINAL-ACCEPTANCE COMPLETE, W5 BLOCKED ON A FOURTH INFRA GAP.** First `source_accepted` event in the campaign. Reconciliation found + removed real production test-fixture contamination (2026-07-19 demo data in `life_events`/`mimamsa_event_provenance`/`brahma_prospective_ledger`). Fresh-context verifier subagent independently reran the real integrity check (`true`, non-vacuous) and correctly-routed digests, but the server's own re-verification 500'd: `nirmana_evidence_ingress_writer` has no `SELECT` grant on `life_events`/`charts`. Filed #1869; digests preserved for immediate resubmission once granted. |
| 3 | `mi_jivanaghatana` | `changed` | ✅ | ⚠️ crashed | ⬜ | **CANARY 3.** W2 complete (verdict `correct`, two real writer defects confirmed already-fixed: A-F-08 honest-null, A-F-09 volume formula). Dispatched solo (full `build_run_authorized` sequence executed correctly — landed 3.4s before start), but the run **crashed** in orchestrator provenance capture — the #1856 bug, found here. Retry pending #1861. |
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

## §1.5 — W3 outcome (6 PRs)

| PR | content | state |
|---|---|---|
| #1745 | W1 analyses (15/15), W2 decisions, notes audit, state | **merged** |
| #1768 | migration 690 — registry accuracy (floors, `target_table`, 5 volume formulas, 5 measured durations) | **merged** |
| #1769 | writer honesty fixes — 9 raises + 2 fabricated-value repairs + a float off-by-one | **merged** |
| #1786 | serving plane — density contracts **0/16 → 15/15**, `qa_fail_count` under-report, an always-empty spine section | **merged** |
| #1785 | migration 691 — 15 integrity contracts + the free-registry-window sweep | **merged** |
| #1790 | `mi_pariksha` §N.3 idempotency scar | **merged** |
| #1809 | C13 blast-radius statements, all 15 routes | **merged** |
| #1811 | recovered W5 checks + W4 canary runbook | **merged** |
| #1844 | migration 692 — `mi_vistara` `output_digest_spec` (first non-L0 entry, #1840) | queued |

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

## §3.5 — Findings that outgrew L5 (the layer's real contribution)

Four L5 findings became campaign-wide rulings or corrected another layer's work. Recording them
here because Phase Z's value from this layer is mostly *not* L5's own assets:

1. **#1732 — a `ph_nimitta` rebuild destroys the L5 prediction-provenance chain.** Became
   **D-CND-04**; L4 built the deterministic `anchor_id` fix (#1754). **And on re-verification after
   it landed, its identity tuple COLLIDES**: 191 of 195 anchors match their own identity, and the 4
   that do not are two *pairs* collapsing to one id each — so the next `ph_nimitta` rebuild silently
   drops 2 of 195 via `ON CONFLICT DO NOTHING`, and all 4 are referenced by live L5 predictions.
   Reported; L5's hold stays for that reason rather than the original one.
2. **#1738 — `WriterResult.notes` is write-only across 87 writers.** Became a campaign-wide ruling;
   every layer audits its own. L5's audit: 10 A-sites, 9 converted, **the tenth decided as a
   considered B under §R5 rather than left waiting** — it is an instance of the *parked* class (the
   orchestrator cannot hear structured degradation), not the closed one.
3. **#1807 — `catalog_status` is still seed-governed**, so a `runSeed()` reverts the DRAFT→CURRENT
   sweeps of **L0/L2/L3/L4 — 45 assets**, including L2's migration-660 nine. Found while checking
   whether my *own* sweep would survive. Same defect class as #1757, which had already been ruled;
   `catalog_status` was simply not in that fix's scope.
4. **#1748 — the `signal_id` type split.** L5 is the only layer storing it as `text`; the other nine
   such columns are `uuid`. Supplied the JSONB surface a column-name sweep cannot see
   (`mimamsa_predictions.driving_signals`, 975 refs) and live evidence that identity is already
   unstable across builds (predictions referencing two `bo_laksana` generations).

## §3.6 — W4 findings that outgrew L5 (the layer's SECOND real contribution)

§3.5 recorded W1's contributions. W4 — actually dispatching real builds, the first non-L0
dispatches this campaign has run — produced three more, structurally deeper because they sit in
shared plumbing every other layer's Conform work must also pass through:

1. **#1840 — `output_digest_spec` is L0-only.** `asset_output_digest_specs` had 37 rows, every
   one `bg_*`; zero for any other layer. `compute_output_digest()` deliberately returns
   `(None, None)` when no spec exists, and `NirmanaRebuildEvidenceSchema.output_digest` is
   non-nullable — so `accepted_rebuild_observed`/`asset_frozen` were structurally unreachable for
   every non-L0 asset campaign-wide, confirmed by a live query: 0 such events anywhere outside
   L0. Ruled by the Conductor (D-CND-27): per-layer authoring, same division of labor as the
   #1715 receipt-spine generalization. L5 authored its own first entry (migration 692,
   `mi_vistara`) as the precedent for other layers to follow.
2. **#1848 — the dispatch script's duplicate-execution guard has no bypass.** Blocks on ANY
   prior `build_runs` row sharing a `(definition_revision, layer, wave, asset_ids)` key,
   regardless of terminal state — so an asset dispatched once without first submitting
   `build_run_authorized` (which every layer's naive first CLI use does, since the CLI's
   single-shot `--commit` path doesn't leave a window to submit it) permanently loses its only
   chance at `accepted_rebuild_observed`. `mi_vistara` hit this itself. Conductor fix (#1851,
   Option B — narrow to genuinely in-flight states) in flight, not yet merged.
3. **#1856 — a real crash in core orchestrator provenance capture.** `chart_id` reaches
   `compute_upstream_hash`/`canonical_upstream_hash` as a raw `uuid.UUID` and both functions
   `json.dumps()` it directly with no `uuid.UUID` case in the canonicalizer — crashing any
   per-chart asset with declared dependencies before its writer even runs. Found live on
   `mi_jivanaghatana`'s first (correctly-authorized) dispatch attempt. Flagged, not
   self-patched — it is inside the FROZEN core orchestrator (§N.2), and genuinely uncertain
   whether production's regular "click Build" flow is equally exposed (worth Phase Z or the
   native's own confirmation). Conductor fix (#1861) in flight, not yet merged.

4. **#1869 — `nirmana_evidence_ingress_writer` lacks `SELECT` on tables outside the registry
   surface.** Found by a fresh-context verifier subagent's own independent W5 attempt on
   `lel_events` (implementer≠certifier working as designed): the real integrity check passed
   (`true`, non-vacuous, live-reran) and the digests routed correctly under the verifier identity,
   but the server's own re-verification 500'd — `permission denied for table life_events`. This
   role backs every layer's `integrity_verified`/`asset_frozen`/`probe_accepted`, so any OTHER
   asset whose integrity check reads a table outside its own registered surface will hit the same
   wall the first time any layer's W5 reaches it. Not self-fixed (a production GRANT is
   Conductor/security territory); digests preserved for instant resubmission once granted.

Between them, these four findings are why **zero non-L0 assets, anywhere in the campaign, had
ever reached `accepted_rebuild_observed`, `integrity_verified`, or `asset_frozen` before this
session** — not for lack of trying elsewhere, but because nobody had yet pushed a real non-L0
asset far enough through W4→W5 to hit all four walls in sequence.

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
- **The `catalog_status` seed-revert (#1807)** if unruled — it silently undoes four layers' merged
  registry work.
- **The `mimamsa_attribution` `text`→`uuid` conversion + `ON DELETE RESTRICT` FK**, sequenced behind
  L2's deterministic `signal_id`. Together the two make the orphan class *structurally impossible*
  rather than merely absent-today; either alone leaves it possible.
- **`mi_adhilepa`'s `target_table` / `count_sql`** — decided (#1757) but **not executable by
  migration**, because both fields remain seed-governed. The decision is on the record; the
  mechanism is not.
- **The one L5 sequencing rule:** `mi_gunanaka` must be followed by `mi_adhilepa`, always — 224,742
  overlay rows carry *copies* of multiplier values, so a multiplier change leaves them stale at an
  unchanged row count.
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

## §5.5 — C13 blast radius (charter requirement, discharged)

**Measured empty, in both directions.** Zero CASCADE children from all 27 L5 write-target tables;
no campaign-layer table cascades into L5 either (the only inbound CASCADE is from `profiles`, i.e.
user-account deletion). L5 is the terminal layer, so the hazard that made C13 necessary has no L5
analogue. Full statements per route: `L5_C13_BLAST_RADIUS_v1_0.md` (#1809).

The substance is in the no-FK half, and it includes one finding worth carrying forward: a
**name collision that is not a reference** — `kala_field_provenance` (663,000 rows) shares the
`weight_id` column name with `mimamsa_multipliers` but is **100% unresolvable against it in both
directions**. A naive column-name sweep reports "663,000 L3 rows depend on an L5 table", which is
alarming and false. Recorded so nobody adds an FK that would be actively wrong.

## §6 — OPEN

Per-finding disposition table · **W4 execution and W5 capsules — no L5 asset is terminal and no
capsule exists** · cost actuals · the Conductor's freeze-ordering ack · closure-safe sync proof.

**W4's current gate is L5's own choice, and it is worth stating as such:** the three E-gate-open
assets (`lel_events`, `mi_vistara`, `mi_jivanaghatana`) are dispatchable, and the receipt spine
(#1736) and per-chart detector (#1723) have both merged. Acceptance is deliberately sequenced behind
migration **691**, because **D-CND-09** closes the registry window on the *first* W2 acceptance and
691 carries the last of it. Accepting first would strand the `catalog_status` sweep and the final ten
volume formulas and force re-acceptance. That is a sequencing decision, not a stall.

**W5's honest state:** the mechanical checks are written *and run* — **7 of 12 pass, 5 fail, and
every failure is on a defect already found and recorded**. Those five failing is the C12
rewrite-floor test passing: the checks can fail on real corruption and they do. W3 fixed the code;
only a W4 rebuild fixes the data.
