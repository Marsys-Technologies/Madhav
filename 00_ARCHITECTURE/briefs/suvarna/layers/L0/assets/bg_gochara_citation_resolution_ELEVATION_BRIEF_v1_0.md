---
asset_id: bg_gochara_citation_resolution
layer: L0 Brahmagyan (bg_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L0 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_LAYER_INSTANCE_v3_1.md (3.1-rev1, PROVISIONAL)"
base_commit: "main 0250cbade"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-20]
ledger_gap_ids: [bg_gochara_citation_resolution-Build.completion, bg_gochara_citation_resolution-Earn.build_record, bg_gochara_citation_resolution-Cost.baseline, bg_gochara_citation_resolution-Carr.detector]
---
# bg_gochara_citation_resolution — Gochara citation → verse-ref resolution table (R9 input; 14 rows; static)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

MR-25 (PARIṢKĀRA): maps gochara citation strings to `classical_text_chunks` verse refs; resolved rows carry a confirmed `chunk_id` + `verse_ref`, unresolved rows record honest corpus gaps (seed description). Created and seeded by migration `platform/supabase/migrations/565_bg_gochara_citation_resolution.sql`, repaired by 630 and 631. **No writer, no `@register`, no `build_run_assets` row, no `asset_throughput` row, no provenance receipt** (layer instance §1.1.4); declarations kind `static`. `data_disposition = RETAINED_AS_CAPITAL`. Depends on `bg_texts`; 0 declared dependents, but `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` reads 5 of its 9 columns. **Charter R9 asset.** `source_citation` populated 14/14.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | static | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1023` | seed (live may differ by migration) |
| writer / `@register` | none registered in code; registry `has_writer` = False | writers dir, census `Build.registered` |
| target table(s) | `bg_gochara_citation_resolution`; count_sql tables: `bg_gochara_citation_resolution` | census CEN-R |
| live rows / floor | 14 / 14 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_texts` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_gochara_citation_resolution`: 5 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `route.ts`, `definitions.ts`, `producer_editorial_review.ts`, `register_gochara_windows.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `register_gochara_windows.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at chart 482012f1 |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.completion | FAIL | live=14 and no build record at all (chart 482012f1 (global count_sql; no global build row)) |
| Build | Build.contract | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Build | Build.exercised | N/A | never run, and it has no writer — consistent |
| Build | Build.history | N/A | never run; check 7 owns this |
| Build | Build.registered | N/A | no writer, and the registry agrees (service or static) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at chart 482012f1 |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 14/14 rows); Vocab.identity (declared key (citation_string, chunk_id): 0 duplicate(s)); Build.count_integrity; Build.dag †; Build.dep_liveness; Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem NO_DETECTOR · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_gochara_citation_resolution-Build.completion | Build | real as a status gap; cause = static kind with no writer (decided SS Q7: dispatchable writer) | live = 14 and no build record at all \| ledger: measured: live=14 and no build record at all / required: the Build gate's claim |
| bg_gochara_citation_resolution-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_gochara_citation_resolution-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_gochara_citation_resolution-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — the table is correct as seeded and read by a live module; its only gaps are build-system status artefacts of being migration-seeded (no writer to dispatch, so no build record). Retire is not in question (reference asset).

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Dispatchable writer that re-seeds from the git source (delete-then-insert)

- **Answers:** census `Build.completion` FAIL ("live=14 and no build record at all"); ledger `bg_gochara_citation_resolution-Build.completion`
- **Change:** decided (SS 2026-10-01, Q7): register a writer that re-seeds the 14 rows from the git source of migrations 565/630/631 by delete-then-insert, so the orchestrator can dispatch it and Build is measurable. Option (a) N/A-by-rule is not taken. R9 asset: the writer and any rebuild wait for SS after notifying Pravāha.
- **Files / declaration / migration:** `pipeline/orchestrator/writers/bg_gochara_citation_resolution.py` (new `@register`, `WriterBase`), registry `has_writer = true`, a test
- **Failing-first test and mutation:** failing-first: a rerun leaves the 14 rows’ fingerprint unchanged and a `build_run_assets` row exists; mutation: remove a row → the rerun restores it
- **Output change:** none
- **Blast radius:** rewrites or adds data in this asset’s tables (idempotent); declared dependents direct 0 / transitive 0; the readers listed in the §0 row read the same ids and see the changed fields.
- **Rebuild:** needs production rebuild/dispatch (14 rows, idempotent); R9: waits for SS after notifying Pravāha
- **Gate it moves:** Build (completion, exercised, registered)
- **Fix class:** writer code; **buildable before J1:** tier-independent (decided)
- **Decision:** ANSWERED by SS 2026-10-01 (Q7): static migration-seeded assets get a DISPATCHABLE writer that re-seeds from the git source (delete-then-insert), which makes Build measurable and ELEVATED reachable (Track I item; R9 assets wait for SS after notifying Pravāha).

### FD-2 · Carr detector — D1 on the resolved rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for each resolved row, test that `chunk_id` exists in `classical_text_chunks` and the chunk’s `verse_ref` equals the row’s; unresolved rows must carry a stated corpus-gap reason and are reported separately, never as passes.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `platform/supabase/migrations/565_bg_gochara_citation_resolution.sql` for any composed text column; declare `[]` expected (`note` is a literal) after reading migration 565/630/631
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 0 L0 modules; 1 platform-mcp module (`register_gochara_windows.ts`) reads it, so attribution is by `carriage` declaration; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference.
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* served by a platform-mcp module rather than an L0 registry module; attribution by declaration

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(citation_string, chunk_id)` (census, 0 duplicates). Static rows: fingerprint = the 14 `(citation_string, chunk_id, verse_ref, status)` tuples; volatile: `created_at`, `note`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 14 resolutions, including the honest unresolved rows with their corpus-gap reasons.
- **Carriage check chosen (T4 §4.1; one only):** D1 (correspondence of each resolved citation to its chunk).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q7): static migration-seeded assets get a DISPATCHABLE writer that re-seeds from the git source (delete-then-insert), which makes Build measurable and ELEVATED reachable (Track I item; R9 assets wait for SS after notifying Pravāha).
2. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
3. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-20.


## 8 · WAVE addendum (2026-10-03, Track I I.FL0; docs only, additive, PROVISIONAL like the rest of this brief)

**Disposition note, N-102 (owner ruling): deferred by owner (N-102): source not held.** The owner ruled to leave classical texts the platform does not hold: this asset is NOT being provenance-confirmed now. It stays NO_DETECTOR on Carr and is not elevated in this campaign. This is an OWNER DECISION relayed by Exec Suvarna (the N-102 text itself was not available to this lane); it is not a finding about the corpus. No other disposition in this brief changes; the fix designs above stay valid but are not to be scheduled for Carr in this campaign.

**Reconciliation with this brief:** this asset is itself a citation-to-chunk crosswalk of 14 mappings: 1 resolved to a served `classical_text_chunks` row and 13 recorded as honest corpus gaps (section 0). So it is not 'a source we do not hold' in one piece: the deferral is the owner's decision not to confirm its provenance now, and its existing resolved/unresolved split stays as recorded.
