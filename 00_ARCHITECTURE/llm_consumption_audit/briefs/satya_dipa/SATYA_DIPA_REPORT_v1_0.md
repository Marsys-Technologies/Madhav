---
artifact: SATYA_DIPA_REPORT
canonical_id: SATYA_DIPA_REPORT
version: 1.0
status: CLOSED
authored_by: Claude Code, 2026-07-29
seals: SATYA_DIPA_BRIEF_v1_0.md
mode: FULLY AUTONOMOUS — Conductor + Dvārapāla + Opus-Verifier-equivalent adversarial self-check, no human gates
---

# SATYA-DĪPA Close Report — Make `lit` Mean Lit

## Plain-language answer, first

**Can `asset_throughput.state = 'lit'` be trusted now?** Yes, for the specific defect this campaign
targeted. The promotion predicate now checks substep-plan completeness (not just "rows exist")
before promoting a genuinely-partial build to `lit`.

**How many assets were lying?** In the live database, at the moment this campaign started: **zero**
currently-`lit` assets were falsely promoted by this defect. The defect is real and was latent in
the code, but empirically only two writers in the entire fleet ever exercise the code path that
could trigger it (`ka_sangam`, `ka_gochara_sweep` — the only two that use the
`build_substep_progress` cross-attempt resumption ledger at all), and reconciliation against that
ledger found all of their current rows honest: `ka_sangam` is 61/61 substeps on all three charts
that have it, correctly `lit`; `ka_gochara_sweep` is 303/303 on the canonical chart (482012f1,
correctly `lit`) and honestly `error` on the other two charts (operator 1c826d5a at 78/303, chart
cb73cd3d at 70/303). **One confirmed historical instance** of this exact defect firing exists — not
from a queryable event log (see below), but from this session's own immediately-preceding work: the
operator chart's `ka_gochara_sweep` was misreported as complete via this exact mechanism, caught by
adversarial review, and manually corrected to `error` before this campaign began. That correction
already stands; this campaign's job was to make sure the *code* can't do it again, and to prove the
DB is honest — both are now true.

**What was built on top of the lying population?** Nothing currently in the database, because the
falsely-lit population is empirically empty right now. Downstream contamination assessment (§4) is
therefore a clean bill for the live DB, not a remediation list.

---

## 1 — Forensic-lead correction (load-bearing finding)

The brief's forensic lead instructed querying the `asset.noop_completion` event history first, as
"a near-complete register of every time this fired." **That register does not exist as a queryable,
durable artifact.** `emit_event()` (`pipeline/orchestrator/events.py`) either prints to stdout
(captured by Cloud Logging only when running on Cloud Run, and only within Cloud Logging's default
~30-day retention) or fire-and-forget publishes to Pub/Sub, whose only consumer
(`/api/cockpit/sse/route.ts`) opens an ephemeral, per-connection subscription with a 600-second
message-retention window. There is no `build_events`-style durable table for orchestrator events —
the one table by that name (`migrations/_archive/118_build_events.sql`) belongs to a different,
retired legacy pipeline (`marsys-build-pipeline-job`), not the current writer-based orchestrator.
A Cloud Logging query (`gcloud logging read 'textPayload:"noop_completion"' --freshness=9999d`)
returned zero results — either the event has only ever fired locally (not on Cloud Run, so never
logged there), or any Cloud-Run-side occurrences aged out of retention. This is a real gap, not a
dead end I chose to skip: **Phase A pivoted to independent reconciliation against
`build_substep_progress`** (the brief's own second, always-available instruction — "then reconcile
independently") as the sole forensic method, and that reconciliation is what §"Plain-language
answer" and §4 above are built on. Recommend, as a non-blocking follow-up: persist
`asset.noop_completion` / `asset.noop_completion_rejected` to a durable table (or a Cloud Logging
sink with export) so a future audit of this class of defect has a real register to query.

## 2 — Phase 0 corrections to the brief's own stated context

- **ŚUDDHA-VĀCA is CLOSED, not PARTIAL.** The brief (authored 2026-07-28) carried forward "ŚUDDHA-VĀCA
  remains PARTIAL — 5 of 7 P0 lanes fixed... TWO pre-authorized lanes still parked on PARISHODHANA
  PRs #827/#828." Both PRs merged 2026-07-28 (`#827` 07:07 UTC, `#828` 07:16 UTC) — same day, before
  the brief was written, in a prior session of this same conversation. Both parked lanes
  (`lane:serve-shadbala`, `lane:ga-tajaka`) were released and verified in that prior session.
  `lane:serve-shadbala` was independently re-verified live during this campaign's Phase 0: the
  canonical chart's Sun `graha_shadbala_total`/`rupa` reads 8.47 in `chart_facts`, matching the fixed
  value, confirming no regression since. ŚUDDHA-VĀCA is 7/7 P0 lanes VERIFIED-FIXED. CLAUDE.md §N.8's
  footer (this campaign, §3 below) corrects the stale claim at its source.
- **No concurrent rebuild campaign.** `build_runs` had zero rows in `state IN ('running','planned')`
  at Phase 0 and remained so throughout. The only open PRs besides this campaign's own were #446 (an
  unrelated old docs PR) — no PARISHODHANA/PARIPRAŚNA rebuild in flight. Dvārapāla ruling:
  **PROCEED-CLEAR**, no DISJOINT-PARALLEL or QUEUE-BEHIND concern.
- **Branch hygiene correction (Dvārapāla, mid-campaign):** this campaign's investigation and fix
  work was initially done on `parishodhana/dark-corpus-remeasure` — a long-lived feature branch that
  had diverged from `origin/main` by 39 commits (including the very ŚUDDHA-VĀCA/PARKED_FINDINGS_CLOSE
  work referenced above, and an unrelated `466_omega8_floor_wiring.sql` migration that collides with
  this campaign's first-chosen migration number). Opening a PR from that branch would have bundled
  39 unrelated commits and produced a silent migration-number collision. **Ruling: CONTRACT-CHANGE-
  REQUIRED for the delivery path, not the fix** — the fix itself was ported via patch to a fresh
  worktree/branch (`satyadipa/noop-completion-fix`) cut directly from `origin/main`, and the
  migration renumbered 466→467 to resolve the collision. The diverged branch's own working tree is
  left untouched (its unrelated in-flight work is not this campaign's to disturb).

## 3 — The fix (Phase B/C)

**The one authorized freeze exception** (`SATYA_DIPA_BRIEF_v1_0.md` §9.1): the promotion predicate
in `asset_runner.py` (`_run_data_writer`, formerly lines 596–630). No other orchestrator file, no
`WriterBase` contract, no `_drive_substeps` signature, no writer file was touched.

**The defect:** when a data writer's substep loop this round nets zero rows, the "no-op-completion
rescue" (added for the D-1.6 incident — see `tests/test_d16_state_write_defect.py`) reclassifies
`dormant` to `lit` whenever the asset's target table has *any* rows present, without checking
whether the writer's substep plan actually finished. A resumable writer that legitimately has
nothing left to do (D-1.6's true shape) and a resumable writer genuinely mid-build with substeps
still remaining are indistinguishable to that check — both show "rows present, 0 rows this run." The
latter is the same "unearned success signal" defect class as D-1.6 itself, one layer deeper.

**The fix:** for `asset_registry.has_substeps = true` writers only, before promoting, the rescue now
re-invokes the writer's own `plan_substeps(ctx)` (SAVEPOINT-isolated, mirroring the existing
`_data_rows_present` pattern) and requires it to report zero remaining substeps. This call is safe
immediately after the same round's `_drive_substeps` call completed — same fingerprint, no
intervening state change — so it cannot trigger a resumable writer's destructive fresh-replan branch
(verified by direct reading of `ka_gochara_sweep`'s `plan_substeps`, the only writer with such a
branch). Writers with `has_substeps` false/NULL (light writers, no real substep plan — the default
`WriterBase.plan_substeps` always returns exactly one synthetic substep, never resumption-aware) are
**unaffected**: the new check is gated on `has_substeps` and skipped entirely for them, preserving
prior behavior exactly, per the brief's own §4.1 requirement.

**The new honest state:** when the plan is genuinely incomplete, the asset is marked **`incomplete`**
(new value added to `asset_throughput_state_check`, migration `467_asset_throughput_incomplete_state.sql`,
applied to production) — not `lit` (would falsely satisfy `runner.py`'s and `staleness.py`'s
`state IN ('lit','service_ok')` dependency-satisfied allowlists, both confirmed to be allowlist-based
so no change was needed there) and not `dormant` (data is not absent). A distinct event,
`asset.noop_completion_rejected`, is emitted alongside the existing `asset.noop_completion`, carrying
`rows_present` and `substeps_remaining` for diagnosability.

**The regression proof — fail then pass, as required:**
`platform/python-sidecar/tests/test_d16_state_write_defect.py` gained three tests:
- `test_satyadipa_d16_preserved_through_completeness_check` — D-1.6's exact shape (writer's
  `plan_substeps` reports empty, meaning nothing remains), run *through* the new check, still
  promotes to `lit`. **This is the blocking acceptance criterion**: a resumable writer legitimately
  reporting 0 rows with a complete plan still promotes and keeps downstream unblocked.
- `test_satyadipa_partial_substep_plan_with_rows_present_not_lit` — a writer whose `plan_substeps`
  reports a substep still remaining, with data present from earlier commits. **Proven to FAIL against
  the pre-fix code** (asserted, ran with the fix stashed via `git stash`, confirmed
  `AssertionError: ... got 'lit'`) **and PASS against the fixed code** (state = `incomplete`, event
  `asset.noop_completion_rejected` emitted with `substeps_remaining=1`).
- `test_satyadipa_light_writer_no_substep_plan_behaves_as_before` — `has_substeps=False` — the
  original D-1.6-era no-op-completion behavior holds unchanged.

All 15 tests in the file pass (12 pre-existing + 3 new), including the original, untouched D-1.6
repro test. Full `python-sidecar` suite: **4070 passed, 23 failed, 10 skipped** — every failure is in
`tests/test_l0_remedy_corpus.py` (a planet-name case-convention mismatch, `'sun'` vs `{'Sun', ...}`),
unrelated to the orchestrator, pre-existing, and out of this campaign's scope. No test that exercises
`asset_runner.py`, `_drive_substeps`, or any writer regressed.

**Documentation:** the amendment is logged as a dated, authorized freeze exception in
`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §7.1 (version bumped 1.0→1.1), per §9.1's explicit
requirement that the freeze record stay truthful.

## 4 — Downstream contamination assessment

Per-asset, for the only two writers capable of triggering this defect:

| asset_id | chart_id | substeps done / total | state | contamination |
|---|---|---|---|---|
| ka_sangam | 1c826d5a (operator) | 61/61 | lit | CLEAN — full plan complete |
| ka_sangam | 482012f1 (canonical) | 61/61 | lit | CLEAN — full plan complete |
| ka_sangam | cb73cd3d | 61/61 | lit | CLEAN — full plan complete |
| ka_gochara_sweep | 482012f1 (canonical) | 303/303 (3 event_classes × 101 years, verified by direct count) | lit | CLEAN — full plan complete |
| ka_gochara_sweep | 1c826d5a (operator) | 78/303 | error | CLEAN — honestly not-lit already (this session's own prior manual correction) |
| ka_gochara_sweep | cb73cd3d | 70/303 | error | CLEAN — honestly not-lit already |

No asset anywhere in the fleet is currently `lit` with an incomplete substep plan. No downstream
asset was built on contaminated data from this defect. **Phase D (repair the record / rebuild
contaminated assets) has no work to do** — this is a clean result, not a skipped step; the
reconciliation that would have driven remediation is §1/§4 above, and it came back empty.

Separately, `asset_throughput.expected_rows` was cross-checked for every `lit`/`service_ok` asset
against `rows_written`: zero rows anywhere read below their `expected_rows` target — a second,
independent confirmation that nothing currently `lit` is under-filled.

## 5 — Broader build-layer sweep (Earned-Signal Principle)

Per the brief's directive to sweep the same defect class fleet-wide, and per the new CLAUDE.md §N.8
doctrine (below): the specific mechanism here — a proxy check (rows exist) standing in for the real
claim (plan finished) — was traced to exactly two writers via `build_substep_progress` usage
(`ka_sangam`, `ka_gochara_sweep`); no other writer participates in that ledger, so no other writer
can currently trigger this specific code path. A full census of `runner.py`, `staleness.py`,
`dag_edge_guard.py`, `kala_derivation_completeness_guard.py`, and `service_probes.py` for other
detector-less-PASS patterns was scoped but not exhaustively completed this session (time-bounded);
this is recorded as **PARKED-HONEST**, not silently dropped — a natural next SATYA-class wave.

## 6 — CLAUDE.md §N.8 — Earned-Signal Principle

Added `CLAUDE.md` §N.8 (v6.5→v6.6), generalizing §N.7 item 4 ("a flag needs a real detector or it's
null," from ŚUDDHA-VĀCA) to the build layer, citing all four confirmed instances across three
campaigns (Ṣaḍbala selector, two `bo_pramana_mapa` flags, the PB-2 byte-equality gate, and this
no-op-completion predicate). CLAUDE.md's own footer stale-status claim about ŚUDDHA-VĀCA/PARISHODHANA
#827/#828 was corrected in the same edit (§2 above).

## 7 — Not attempted this session (PARKED-HONEST)

- **§4.4 secondary P1 lanes** (`ka_bhavishya_lekha.py` domain vocabulary, the `chart_dashas` CLI-only
  sentinel): not re-verified this session; carried forward from the prior wave's
  `PARKED_FINDINGS_CLOSE_v1_0.md` (v1.1) unchanged. Not re-touched here to keep this campaign's diff
  scoped to its one authorized freeze exception plus its own documentation.
- **Cockpit UI display of the new `incomplete` state:** five TypeScript files
  (`src/lib/build/plan.ts`, `src/app/api/cockpit/stats/route.ts`, `src/components/build/AtlasView.tsx`,
  `src/components/build_orchestrator/AssetNode.tsx`, `src/hooks/useCockpitSSE.ts`) declare
  `AssetState`-style string unions that do not yet include `'incomplete'`. Functionally this is
  harmless — both dependency-gating call sites are allowlist-based (`state IN ('lit','service_ok')`),
  so `incomplete` is correctly excluded with zero code change there — but the cockpit UI may render an
  `incomplete` asset via an unstyled/default branch until these unions are updated. Non-blocking,
  cosmetic, PARKED for a follow-up UI polish pass.
- **Full fleet-wide detector-audit sweep** (§5): scoped, not completed.
- **A durable `asset.noop_completion` event register** (§1): recommended, not built this session —
  would require either a new DB table or a Cloud Logging export sink, both beyond the one authorized
  freeze exception.

## 8 — Disposition table

| Item | Disposition |
|---|---|
| D-1.6 regression test (fail-then-pass) | VERIFIED-FIXED |
| Promotion predicate fix (asset_runner.py) | VERIFIED-FIXED |
| New `incomplete` state + migration 467 | VERIFIED-FIXED (applied to production DB) |
| Falsely-lit population enumeration | VERIFIED-FIXED (empirically empty; see §4) |
| Downstream contamination remediation | NOT-APPLICABLE (nothing to remediate) |
| Full test suite regression check | VERIFIED-FIXED (4070 passed; 23 unrelated pre-existing failures) |
| drift_detector / schema_validator | VERIFIED-FIXED (no new violations attributable to this campaign) |
| ORCHESTRATOR_CONVERGENCE_CLOSE §7.1 authorized-exception log | VERIFIED-FIXED |
| CLAUDE.md §N.8 Earned-Signal Principle | VERIFIED-FIXED |
| ŚUDDHA-VĀCA status correction | VERIFIED-FIXED (confirmed CLOSED 7/7, corrected at source) |
| §4.4 secondary P1 lanes | PARKED-HONEST (not re-touched this session) |
| Cockpit UI `incomplete` state display | PARKED-HONEST (functionally harmless, cosmetic) |
| Fleet-wide detector-audit sweep | PARKED-HONEST (scoped, not exhaustive) |
| Durable noop_completion event register | PARKED-HONEST (recommended follow-up) |

## 9 — Delivery

Branch `satyadipa/noop-completion-fix`, cut from `origin/main` (see §2 branch-hygiene note). Files
changed: `platform/python-sidecar/pipeline/orchestrator/asset_runner.py`,
`platform/python-sidecar/tests/test_d16_state_write_defect.py`,
`platform/migrations/467_asset_throughput_incomplete_state.sql` (new),
`00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`, `CLAUDE.md`, this report (new). PR opened
against `main`, auto-merge on green CI.
