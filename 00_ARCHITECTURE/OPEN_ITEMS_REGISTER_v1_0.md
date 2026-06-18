---
artifact: OPEN_ITEMS_REGISTER_v1_0.md
canonical_id: OPEN_ITEMS_REGISTER
version: 1.0
status: CURRENT
created: 2026-06-17
purpose: >
  Consolidated inventory of open items as of L0-sealed + L1-enrichment-sealed, BEFORE the L1 Gaṇita closure
  pass. Authored so nothing is silently absorbed or lost when the next big pass opens. Grouped by urgency
  relative to L1 closure; each item tagged owner (Cowork-plan / Claude-Code-exec / operator) + status.
governing_decisions:
  - Gate-3 runs as its OWN pass BEFORE the L1 closure (native, 2026-06-17) — a layer can't close with assets unbuilt.
  - Connection-resilience guards = VERIFY before trusting (status unconfirmed; only the ga_sensitive heavy split is confirmed).
---

# Open Items Register v1.0 — what to close before / around the L1 Gaṇita closure

## Corrected sequence (native-ratified 2026-06-17)

1. **Six-subsystem Gate-3** (its own operator pass) — build the 4 per-chart subsystem L1 assets for the native.
2. **L1 Gaṇita closure pass** — on the now-fully-populated layer (kickoff already written).
3. **L2 Bodha design** — with closed L0 + closed L1 + accumulated opportunity register.
Cosmetic/CI items (group A) can run in parallel anytime; the L0/L1 residuals (group C) are tracked, non-blocking.

---

## GROUP A0 — Cockpit asset-state issues found via Chrome MCP 2026-06-17 (live localhost inspection)

Direct cockpit inspection of `/clients/482012f1/nirmana` surfaced 4 distinct classes. Most are metadata-hygiene
the L1 closure sweeps; TWO are genuinely-unbuilt Gate-3 data (confirming Gate-3 must run BEFORE L1 closure).

| # | Asset(s) | Symptom | Class | Fix path |
|---|---|---|---|---|
| A0-1 | L0 **bg_reference** (Reference Library, 1,485) + **bg_ontology** (Ontology, 623) | bare count, EMPTY bar, no `/target` | **NULL target_floor** → bar has no denominator to fill (display bug; data is LIVE/fine). These 2 had no floor at all so slipped the L0 floor-backfill | Set target_floor=achieved (1,485 / 623) + seed patch. Quick L0 touch-up (sealed L0 — log as L0 micro-fix, native already aware). |
| A0-2 | L1 **ga_str03 Graha-sthāna** (530/50) + **Saṃracanā/Structural** (87,169/74,644) | count > target (overfill) | **stale target_floor** | Bump floors to achieved count. → L1 closure Phase 2. |
| A0-3 | L1 **Sāḍesātī** (11,019), **Nakṣatra-Paṭala** (1,802, Last-Built "—"), **Vastu-graha-dik-mapa** (40), **Gochara Sthāna/transit-anchors** (45), **Saṃracanā** — ~5 assets | "build-state stale" badge; data present + counts match | **asset_throughput out of sync** — mostly SUBSYSTEM assets built/seeded outside the orchestrator throughput-write path (same class as L0's bg_transit_engine/bg_nakshatra_medical stale fix) | Re-sync throughput records. → L1 closure Phase 2 (and Gate-3 builds will refresh several). |
| A0-4 | L1 **ga_prashna** (Praśna-ādeśa, `0` NOT BUILT red) + **ga_yoga** (Yoga Firings, `5/50` partial red+stale) | red/partial in cockpit | **⚠️ CORRECTED 2026-06-17: NOT unbuilt — both are BUILT + CORRECT per `SIX_SUBSYSTEM_BUILD_CLOSE_v1_0.md` (Gate-3 already PASSED).** ga_prashna=0 is CORRECT (natal chart, no horary question → 0 rows, RT-7). ga_yoga=5 is CORRECT (only Yuga Nabhasa fires for this native — deterministic). The cockpit is MIS-RENDERING both. | (a) ga_prashna: cockpit DISPLAY BUG — treats 0-rows as NOT-BUILT when 0 is the valid built state for a natal prashna asset; cockpit needs a "0-rows-is-valid" signal (catalog_status/state vs rows). (b) ga_yoga: stale target_floor 50→5 + stale throughput. → L1 closure Phase 2 + a cockpit-render fix. **Supersedes the earlier "Gate-3 must precede L1 closure" claim — Gate-3 is DONE.** |

Note: L1 also confirmed the enrichment landed — Balatva/Strength 11,936 (4h ago), Sūkṣmabindu/Sensitive 8,610
(47m ago) both LIVE+fresh = PR #298 prod-validated in the cockpit.

## CLOSE-OUT STATUS 2026-06-18 (pre-L2 cleanup complete)

- L0 + L1 BOTH prod-sealed + verified (L0 PR #297 @ a6f564cc; L1 PR #299 @ 37ebd082; L1 prod-verify VERIFIED v2.1).
- Cockpit GENUINELY clean — endpoint-verified (camelCase-probe artifact resolved; bo_samskara count_sql fixed mig 314). [[feedback-verify-cockpit-endpoint-not-just-sql]]
- Migration ledger reconciled 311–314 (IDs 76–79).
- 11 stale open PRs audited → 10 CLOSED as superseded (#172/#180/#183/#185/#190/#194/#195/#196/#199/#206, each with documented reason); **#179 KEPT** (unmerged cascade-modal/route work — cherry-pick-or-close later).
- Brahma Conductor scheduled CI (red every 15min, obsolete autonomous-build path) → schedule removed, PR #300 OPEN (merge to stop the red; Cloud Scheduler watchdog already paused). Real gates (Gaṇita Quality Gate + Deploy to Cloud Run) GREEN.
- REMAINING (non-blocking): merge PR #300; decide #179 (cherry-pick cascade work or close); Group A4 (chore/repo-hygiene-isolated branch + /Madhav-nirmana-ui dir); Group C L0 residuals (DEFER-001..005, REC-003) tracked.
- **NEXT: L2 Bodha** — foundation clean. bo_samskara fix already cleared the first L2 schema issue.

## GROUP A — Cockpit / CI hygiene (parallel; do before or alongside L1 closure)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| A1 | **Cosmetic cockpit polish** — services-first ordering, service green-bar dimension match, centered headers, centered Last Built column | Claude-Code | Brief written, NOT run | `CLAUDECODE_BRIEF_COCKPIT_COSMETIC_v1_0.md`. Edits `AssetRow.tsx` — overlaps A2's red test. |
| A2 | **Main CI red** — `AssetRow_CockpitPolishR2.test.tsx` | Claude-Code | ✅ FIXED (commit 70c55e0c) | Stale `getByText('● GREEN')` → `getByTitle('CURRENT · healthy')` matching the StatusDot refactor (test was stale, not code). 4,526 tests 0 failures. Main CI trustworthy again. **A1 cosmetic brief must keep this green.** |
| A3 | **floor = count exact-match** — ga_strength/condition/sensitive have target_floor == achieved count; any future legit row change false-flags | Cowork-note | Logged, no action | Rail for L1 audit: "count BELOW floor" is the only alarm; "above" is fine; these 3 need a floor bump on future enrichment. |
| A4 | **`chore/repo-hygiene-isolated` branch SKIPPED** (unmerged commits) + **`/Madhav-nirmana-ui/` dir on disk** post-worktree-prune | Claude-Code | OPEN (loose ends from hygiene merge) | Resolve the skipped branch (review its unmerged commits); safe manual `rm -rf` the stale worktree dir. Neither urgent. |

## GROUP B — Connection resilience (from the 2026-06-17 orphaned-txn incident)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| B1 | **ga_sensitive light→heavy split** (5 per-ayanamsha substeps, independent commits) | Claude-Code | ✅ DONE (PR #298) | The durable crash-resilience fix; now a PATTERN for other multi-ayanamsha writers. |
| B2 | **idle_in_transaction_session_timeout guard** (DB backstop) | Claude-Code | ⚠️ VERIFY | Briefed in `CLAUDECODE_BRIEF_CONN_RESILIENCE_AND_RESUME_v1_0.md`; unconfirmed whether applied. Check pg settings on the build role. |
| B3 | **finally/rollback guard in orchestrator txn path** (root-cause fix) | Claude-Code | ⚠️ VERIFY | Same brief; unconfirmed. Check the orchestrator substep txn manager handles interrupt/SIGTERM. |
| B4 | **parallelism cap** (orchestrator worker concurrency vs 50-conn ceiling) | Claude-Code | ⚠️ VERIFY | Same brief; unconfirmed whether the cap was set vs only the heavy split mitigated it. |
| B5 | **PgBouncer pooler** (long-term connection fix) | operator/brahma-pipeline | LOGGED, deferred | Dedicated post-closure brahma-pipeline session. Not wedged into closure. |
| B6 | **light→heavy audit for OTHER multi-ayanamsha L1 writers** | fold into L1 closure | OPEN | Any L1 writer looping 5 ayanamshas in one txn has the same exposure ga_sensitive just fixed. L1 closure Phase-1 audit checks which are still "light." |

## GROUP C — L0 residuals (disclosed at L0 seal; tracked, NON-blocking for L1)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| C1 | **DEFER-001/002** — bg_transit_engine + bg_nakshatra_medical have NO WriterBase writer (data migration-seeded, not orchestrator-reproducible) | Claude-Code | ✅ RESOLVED (Foundation-Session-1 2026-06-18) | bg_transit_rules writer added (folds bg_transit_engine); bg_medical_mappings writer already registered bg_nakshatra_medical. Both confirmed regenerable. |
| C2 | **DEFER-003** — reference_nakshatras DROP needs bg_reference.py refactor first (still INSERTs into it) | Claude-Code | OPEN, disclosed | Refactor → governance-script update → DROP migration. |
| C3 | **DEFER-004** — classical_chunks + prashna_charts (empty) DROP needs code-ref removal first | Claude-Code | OPEN, disclosed | l0_text_index.py + ga_prashna_writer.py reference them. |
| C4 | **DEFER-005** — bg_nakshatra upstream-hash tracking broken (hashes empty string; latent silent-staleness) | Claude-Code | OPEN, should be tracked issue | Data correct; change-detection broken. File as issue. |
| C5 | **REC-003** — brahma_dosha_catalog.associated_remedies[] empty for all 50 doshas | data task | OPEN | Required pre-L2-Bodha (bo_upaya consumes it). Classical research + data entry. |

## GROUP D — Larger parallel workstreams (standing, from memory)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| D1 | **Six-subsystem Gate-3** — per-chart L1 subsystem data for 482012f1 | operator | ✅ DONE + SEALED 2026-06-17 (`SIX_SUBSYSTEM_BUILD_CLOSE_v1_0.md`) | All 8 assets lit (ga_yoga 5, ga_prashna 0-correct, ga_structural 75,168, ga_condition 45, ga_transit_anchors 45, ga_vastu 40, ga_medical 45, ga_sade_sati 11,019 = 86,367 rows). FORENSIC 7/7, Vimarśaka RT clean. **No longer gates L1 closure — it's complete.** Sealed on branch feature/bg-nakshatra-l0 (verify merged to main). |
| D2 | **227-file brief purge** | Claude-Code | ✅ DONE (PR #282 @ d9c668ca) | 229 non-CURRENT briefs → 99_ARCHIVE/BRIEFS_RETIRED/ (290 total archived); 5 CURRENT/ACTIVE/READY retained by STATUS not count (reverse-citation discipline held). G52 signal_type_registry also eliminated (PR #281, 0 live refs). 85 live briefs remain. |
| D3 | **Tier-3 merge queue + Tier-B branch audit** — accumulated worktrees/branches awaiting reviewed merges | Claude-Code | OPEN | ~per-branch sessions; never batch. |
| D4 | **feature/panchanga-service-registry branch** — pending its own PR (independent of layer closures) | Claude-Code | OPEN | Phantom branch from earlier. |

## GROUP E — Foundation-Session-1 residuals (2026-06-18, pre-L2)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| E1 | **bg_remedies depth / bo_upaya dependency** — bg_remedies has 266 rows (first deterministically-citable pass; classical tradition has thousands). L2 bo_upaya (remedy prescription layer) will read bg_remedies depth directly. | Cowork-plan | LOGGED, DEFERRED to L2 | Accept 266 as-built. A future bg_remedies expansion pass is needed BEFORE bo_upaya produces rich outputs. Flag at bo_upaya spec time. |
| E2 | **bg_rules yield = corpus ceiling** — full 10,651-chunk mine confirmed 2,912 rules (0 new insertions); remaining 9,625 chunks don't contain regex-extractable rule patterns. The current regex pattern library (19 patterns) is the yield ceiling for the existing corpus. | Cowork-note | LOGGED, no action | Expanding yield requires either (a) new pattern families or (b) corpus expansion (more classical_text_chunks). Floor = 2,912 (ACHIEVED). |
| E3 | **bg_yogas count 175 in DB vs 144 in l0_yogas.py** — endpoint shows bg_yogas=175 (in brahma_yoga_catalog); YOGAS_CORE=144. Discrepancy: the DB may contain the full 175-entry catalog including entries beyond YOGAS_CORE. Verify if intentional or a stale count. | Claude-Code | OPEN | Check whether brahma_yoga_catalog has 175 entries or 144; if 175, YOGAS_CORE list may be incomplete. Non-blocking for L2 open. |

---

## What gates what (the dependency the native cares about)

- **L2 Bodha is gated behind:** Gate-3 (D1) populating the subsystem data + the L1 closure sealing the layer +
  REC-003 (C5) data. Bodha reading empty subsystem inputs = building MSR signals on nothing.
- **L1 closure is gated behind:** Gate-3 (D1) — can't close a layer whose subsystem assets aren't built for the native.
- **Nothing critical gates the cosmetic/CI items (A)** — but A2 (CI green) should precede the multi-PR L1 closure so the merge signal is trustworthy.

*End. Recommended order: (1) verify B2–B4 + run A1/A2 to green CI; (2) Gate-3 (D1); (3) L1 closure pass
(folding B6 audit + C-residuals awareness); (4) L2 Bodha. C/D residuals tracked throughout, closed opportunistically.*
