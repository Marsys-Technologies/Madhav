---
artifact: NIKASHA_WAVE2_W2-3_REVIEW
packet: W2-3 — deeper detectors (R242, R20, R240, R241, R21, R23); the last packet of wave 2
reviewer: independent gate reviewer (fresh context, read-only; never the implementer)
reviewed_on: 2026-09-27
base: a72cdf460
commits: [fa23abe69, 50c0d4535, ee2c7d7ee, f31a98e4f, 8702ee331, 3f9a11428, f032ecec5, 480d799af]
verdict: ACCEPT_WITH_CORRECTIONS
wave2_complete: yes
wave2_complete_condition: "at the executor's fold, with C1–C3 (§10) recorded; none needs a code change"
scratch: "<scratchpad>/rev-w2-3/ (worktree wt_head at 480d799af, removed at the end; ledger copies ctrl_head / ctrl_base / ctrl_empty / ctrl_dagfail)"
production_ledgers: "asset_gaps.jsonl 7f2257a8d4f0d6a7a21c0648b4101f85 (830 lines) and asset_certs.jsonl 514cbdfcf3fa71b3e382f84a978bf369, byte-identical to a72cdf460 at start and at close; never written"
---

# Nikaṣa wave 2 · W2-3 · independent gate review

## §1 — Verdict

**ACCEPT_WITH_CORRECTIONS.** Every packet proof reproduced exactly. The detectors do what the report says, the
mutations kill, and the next emit on the real ledger behaves as claimed: 58 closed, 11 opened, 0 re-opened, and a
byte-identical re-run.

I then hand-read **all 41** closures the builder left unverified. None is a Python-level false PASS: each one
replaces or upserts its own table on the rebuild path, with no hold on populated output in Python. **Six of them
(the L2 MSR family) sit behind a database-enforced conditional hold the report does not disclose as live.**
`bodha_writers/_idempotency.py:168` calls `public.assert_l2_msr_delete_safe`. That function RAISES "L2 MSR
replacement blocked by cross-layer dependent rows" whenever `kala_*` rows reference the producer's signals. On
two production charts today, a rebuild of these assets would be held, not replaced (§7.2). The canonical chart has
no such dependents today, so on the census chart the closures are earned.

**Is the 58/69 resolution safe to fold?**
- **52 of the 58 closures are trustworthy as stated.** 17 were hand-verified by the builder and 35 by me.
- **6 are trustworthy only with a caveat:** bo_arudha, bo_laksana, bo_nakshatra_semantic, bo_special_lagna,
  bo_sudarshana, bo_vargottama_dhana.
  - They are earned on the canonical chart's data. In general they are conditional on "no cross-layer dependents".
  - Fold them with that caveat recorded and a native ruling queued: is a DB-enforced cross-layer interlock a held
    rebuild (the ka_kshetra class, FAIL) or a permitted precondition (PASS with caveat)? See C1.
- **The 11 remaining PARTIALs are classified accurately** (§3.2).

**Wave 2 as a whole can be declared complete at the fold.** W2-1 and W2-2 are folded, and W2-3 delivers all six
rows. The corrections are disclosure and ruling items, none of which needs code before the fold. The ruling can be
carried to the native queue as an open item.

## §2 — R20: both commits, and the attacks

### §2.1 What the first commit did, what was wrong, and the follow-up

- **`50c0d4535`** replaced the single-file scan with `_delegation_scope`. The scope starts at the registered class,
  adds same-module referenced definitions, and follows first-party references up to 2 module hops.
  `_write_facts` classifies statements as replace / upsert / insert / update / dynamic.
  - PASS rule: any own-table replace (delete layers), or any own-table upsert or replace (L0).
  - **The defect it shipped with:** the PASS was **per asset**. A multi-table writer that DELETEs own table `t_a`
    and plain-INSERTs into own table `t_b` PASSed on `t_a` alone, while `t_b` accretes on every rebuild.
- **`ee2c7d7ee`** computes `covered = own replace ∪ own upsert`. Any own table INSERTed into but not covered gives
  FAIL on a fully-read scope, and PARTIAL when a cut chain or an unnamed table exists. I confirmed the fix is
  genuine: the three parametrised cases hold, and both follow-up mutations kill.
- **Residual gap in the fix** (it covers plain INSERT only):
  - An own table written by `COPY` and never deleted is invisible to the rule. My attack S4 returns PASS.
  - An own table that is only upserted, next to a replaced one on a delete-then-insert layer, is credited as
    covered (S5 → PASS). Yet the same table alone reads FAIL ("§N.3 requires delete-then-insert"). The per-table
    rule is therefore not applied consistently.
  - **One live instance** of that second shape: `mi_gunanaka` → `mimamsa_calibration_snapshot`
    (`ON CONFLICT (snapshot_id) DO NOTHING`, an append-only versioned snapshot by design, `mi_gunanaka.py:342–369`).
    It was PASS already at base, so it is not a W2-3 closure.

### §2.2 Mutations re-run (all 9 R20; scratch worktree, revert md5-verified after each)

| mutation | builder | reviewer | revert |
|---|---|---|---|
| R20-M1 no delegation followed | 7 | **7 failed** | byte-identical |
| R20-M2 whole module, not class | 3 | **3** | ✓ |
| R20-M3 ON CONFLICT anywhere | 1 | **1** | ✓ |
| R20-M4 stem match launders mismatch | 3 | **3** | ✓ |
| R20-M5 FAIL on an unread scope | 2 | **3** † | ✓ |
| R20-M6 "no write" reads N/A | 4 | **4** | ✓ |
| R20-M7 uncalled helpers credited | 1 | **1** | ✓ |
| R20b-M1 per-asset PASS | 2 | **2** | ✓ |
| R20b-M2 FAIL on unread scope | 1 | **1** | ✓ |

† The builder ran `-k r20` before the follow-up test existed. That test's name also matches `r20`, so HEAD kills
M5 with one more test. The difference is explained, not a discrepancy. The R20 selection at HEAD is green:
17 passed, 1 live-skipped.

### §2.3 Delegation-depth attack (writer → A → B → C, the DELETE in C)

Reviewer-built fixture: `bo_d.py` → `bodha_writers/a.py:prepare` (hop 1) → `b.py:clear` (hop 2) → `c.py:wipe`
(hop 3, the DELETE). The writer plain-INSERTs `t_own`.

- **D1 (the asked attack):** PARTIAL, correctly. The text reads "delegation deeper than 2 hop(s), not followed:
  bo_d.py → bodha_writers/a.py:prepare → bodha_writers/b.py:clear → bodha_writers/c.py:wipe", and the resolved
  scope is named. It neither passes nor fails silently.
- **D2 (variant):** `c.py` holds no write-SQL text itself because it imports its DELETE constant from a 4th module.
  - Result: **FAIL "accretes"**. The cut is reported only when the cut module's own text matches `_WRITE_TEXT`,
    so a scope that was not fully read is graded as if it were.
- **D3 (variant):** the writer imports its DELETE statement constant from a sibling module
  (`from bodha_writers.sql import DEL`).
  - Result: **FAIL "accretes"**. `_resolve_def` deliberately refuses `Assign` targets, so an imported SQL constant
    is never read.
- **D4:** a hold inside the hop-3 module, with the replacement at hop 0 → PASS. This is disclosed blind spot #5.
- **Assessment:** D2 and D3 break the stated invariant "FAIL needs a fully-read scope". Both err in the
  conservative direction: they open a gap and can never close one. 0 live instances (the only live Idem FAIL is
  ka_kshetra). This is residual C4 and blocks nothing.

### §2.4 Stray-row attacks (the ka_kshetra class, one level deeper)

All of these are reviewer fixtures run through the real `idem_scan`:

| # | shape | verdict | disclosed? |
|---|---|---|---|
| S1 | DELETE of own table only inside a class method nothing calls; `run()` plain-INSERTs | **PASS** (false) | no — M7 covers module-level helpers only; every method of the registered class is credited |
| S2 | `DELETE FROM own WHERE chart_id=%s AND build_id=%s` (current build only) | **PASS** (false) | no — the report even treats build-scoped *probes* as resume checks, but credits a build-scoped *DELETE* as replacement |
| S3 | DELETE gated on `if ctx.config.get("full_rebuild")` | **PASS** (false) | partially (#2 covers probe-based compound tests, not a probe-less flag) |
| S4 | own `t_a` replaced + own `t_b` written by COPY, never deleted | **PASS** (false) | no |
| S5 | own `t_a` replaced + own `t_b` upsert-only (delete layer) | **PASS**; `t_b` alone → FAIL | no (inconsistency) |
| S6 | delete per (chart, ayanamsha) + a separate method inserting a `'combined'` row outside the predicate | **PASS** (false) | partially (§7.3 "natural-key scope") |

- **Live check.** I ran each shape as a screen over the resolved scope of all 110 live PASSes (credited-DELETE
  reachability, enclosing `if` tests, build_id predicates on credited DELETEs, COPY into own tables, upsert-only
  own tables).
  - **Found 0 live false PASS from S1–S4/S6.** The only COPY is `ga_dashas` into `chart_dashas`, which is replaced.
  - S5 has one live instance (mi_gunanaka, by-design append-only, pre-existing PASS).
- **The deeper stray-row class does exist live, across assets.** `bo_karanajala` inserts arudha and special_lagna
  nodes into **bo_bimba's** table `bodha_cgm_nodes` with `ON CONFLICT (node_id) DO NOTHING`
  (`bo_karanajala.py:1539–1563`, called at :1827).
  - `bo_bimba`'s `replace_prior_cgm_nodes` deletes only `["bhava","domain","dosha","graha","yoga"]`
    (`_idempotency.py:337–350`).
  - Those 130 nodes (95 arudha + 35 special_lagna on 482012f1) are therefore **never refreshed** by any rebuild.
    Changed attributes stay stale, and a vanished fact leaves an orphan node.
  - Neither asset's `Idem.pattern` can see this: bo_bimba's own rows are replaced, and karanajala's own table is
    the edge table.
  - Today there is one build (all 7 node types carry a single build_id, 2026-09-11), so no stale row is observed
    yet. This is out of W2-3 scope and recorded as F-6 (§10).

**Conclusion for R20.**
- The delegation fix is real, and the self-correction (`ee2c7d7ee`) is genuine.
- The depth limit grades a third-module chain PARTIAL with a stated reason.
- The detector remains a static proxy with more undisclosed PASS-direction shapes than §2.4 lists. None of them is
  live among today's 110 PASSes (C2).

## §3 — The 69-asset resolution: independent hand-verification

### §3.1 PASS flips the builder did not read (8 read in depth here; all 41 are in §7)

| asset | what I read | verdict |
|---|---|---|
| ga_medical | `ga_medical_writer.py:285–291` `DELETE FROM ga_medical WHERE chart_id AND ayanamsha_id` as Step 1 of `build_ga_medical_substep`, before any input load; no early exit before it | genuine |
| ga_vastu | `ga_vastu_writer.py:92–95` DELETE (chart, ayanamsha) slice first, inside the substep cursor; no exit before it | genuine |
| ga_vichara | `_delete_prior_vichara_rows` (:161–168, chart × ayanamsha) called at :1016 just before `_insert_rows`; the earlier returns (:959/:964/:970) are dry-run / empty facts / empty constants | genuine (empty-upstream caveat #7) |
| ga_nakshatra | `_run_ayanamsha_pass` → `replace_prior_chart_facts(all_rows)` (:353) after the dry-run return; `cross_ayanamsha` step → replace (:494); the only raise (:408) is "reference_nakshatra <27 rows" (upstream) | genuine |
| bg_concordance | `DELETE FROM classical_attributions` (:207, full global projection) after the desired state is computed; the returns at :86/:108 are empty upstream (reference_topic_tags / tagged chunks) | genuine (caveat #7) |
| bg_doshas | `seed_doshas` `DELETE FROM reference_doshas` / `brahma_dosha_catalog` / `brahma_ontology WHERE entity_class='dosha'` (`l0_doshas.py:1942–1944`) after an information_schema preflight; the count at :2023 is a post-write summary | genuine |
| bo_grounding | `replace_prior_grounding_matches` (`_idempotency.py:227–234`, chart × ayanamsha, sole writer) at :162 before the inserts; `if not rows: continue` (:159) | genuine (caveat #7) |
| bo_karanajala | `replace_prior_cgm_edges(chart, aya, 'static_natal')` (`_idempotency.py:353–365`) + `replace_prior_contradictions` before `_batch_insert`; the raise at :1770 is empty upstream (`node_map`) | genuine for its own table; see §2.4 for the non-own node upsert |

**No guard the scan missed** in any of the 8. The pattern that recurs is the disclosed empty-upstream early exit
(#7). It is more widespread than the report's two examples.

### §3.2 The 11 remaining PARTIALs

| class | asset(s) | reviewer check | accurate? | right disposition |
|---|---|---|---|---|
| registry/writer mismatch (1) | ka_gochara | registry target/count `kala_gochara_windows`; the scope writes `kala_gochara_windows_v2` + `kala_gochara_v2_build_state` | yes | stays PARTIAL until the registry owner re-points it (R240 data action), **not** an N/A ruling |
| own table UPDATE-only (2) | bg_text_index | `UPDATE classical_text_chunks SET topic_tag … WHERE chunk_id … IS DISTINCT FROM` (:546); rows with no match keep their prior tag | yes | needs an idempotency ruling (does a convergent re-derivation count, and are stale no-match tags a gap?), **not** N/A; plausibly a real gap |
| | bo_laksana_rerank | UPDATEs of `bodha_msr_signals` rank columns (bo_laksana.py:3756/3886/3948); separate registered class, correctly scoped away from bo_laksana's DELETE | yes | same: convergence ruling, not N/A |
| writes nothing to own table (8) | bo_samvada | `run()` returns `rows_skipped=1`; the module's `_CREATE_VIEW_CLEAN` constant is never referenced by the class (class scoping correctly excludes it); target is a view | yes | native N/A ruling |
| | mi_abhilekha | UPDATEs `mimamsa_predictions` (not its own `mimamsa_journal`); no own-table write | yes | N/A ruling |
| | mi_seva | information_schema checks only | yes | N/A ruling |
| | mi_vistara | `SELECT COUNT(*)` only ("Service asset: no build-time rows") | yes | N/A ruling (+ OS-6 kind disagreement) |
| | ka_dasha_kala / ka_tulana | only `UPDATE asset_registry` (service health), no target table | yes | N/A ruling |
| | ka_graha_sancara / ka_muhurta_seva | not individually read beyond the scope listing; no target_table declared, and no write SQL on any own table (none declared) | consistent | N/A ruling |

**Correction to the framing.** "PARTIAL, permanent, needs a native N/A ruling" is right for the **8 writes-nothing**
assets only. The 2 UPDATE-only assets need a convergence ruling, and bg_text_index may be a genuine gap.
ka_gochara needs the registry fix. None of the 11 should be PASS or FAIL on present evidence.

## §4 — R21 blocking radius

- **Definition vs code.** `blocking_radius()` (asset_census.py) builds the reverse edges of `depends_on` among
  active, non-dead assets. It excludes self-edges and dependencies on inactive or unknown ids. It counts the
  distinct transitively reachable dependents, excluding A even inside a cycle. `severity_weight = 1 + transitive`.
  This matches the docstring and the report.
- **Independent recursive CTE**, written by me over `asset_registry` with its own edge and reach relations:
  **127/127 assets identical** on (transitive, direct). This covers 10 named assets across all layers:

  | asset | transitive | direct | weight |
  |---|---|---|---|
  | ga_positions | 79 | 31 | 80 |
  | bg_ontology | 69 | 4 | 70 |
  | ga_dashas | 61 | 14 | 62 |
  | bg_texts | 58 | 8 | 59 |
  | bo_laksana | 48 | 22 | 49 |
  | ka_gochara | 26 | 2 | 27 |
  | ph_nimitta | 17 | 10 | 18 |
  | mi_bhara / mi_sankalpa / bo_cdlm_summary | 0 | 0 | 1 |

- **Distribution and top radii reproduced:** 40 / 15 / 18 / 54; ga_positions 79, bg_ontology 69, bg_reference 62,
  ga_vargas 61, ga_dashas 61.
- **Attached to Build rows in a real emit.** I ran a live L1 `--emit-gaps` onto a schema-only ledger copy: 96 rows,
  **23 Build rows, 23 with `blocking_radius`/`severity_weight`, 0 non-Build rows with one**. Examples:
  ga_positions-Build.history 79/80, ga_condition-Build.completion 51/52, ga_vastu-Build.history 0/1.
  - On the real 830-line ledger the next emit writes no Build transition, so no radius appears there. This matches
    the report's stated limit.
- **Null, never 0, on a constructed failure.** I ran a live L5 `measure()` with only the dependency read replaced by
  one raising `Unknown`.
  - Every asset's radius read `transitive=None`, basis "unmeasured: the dependency read failed (…)".
  - The emit wrote **34 Build rows: 34 null, 0 zero**, each with `blocking_radius_note`.
  - Caveat: a *non*-`Unknown` failure (malformed JSON from the read) raises out of `measure()` (`JSONDecodeError`).
    That is fail-closed, never a silent 0, so it is acceptable (noted in F-5).
- **Mutations re-run:** R21-M1 3 failed, R21-M2 1, R21-M5 3. Each matches the builder, and each revert was
  md5-verified.

## §5 — R23 field reachability

- **Reports only.** `Reach.fields` is `NOT_GENERIC` in base and HEAD for all 127 assets, and the census diff shows
  **0 verdict changes and 127 text-only changes**.
  - `NOT_GENERIC` is in neither `FAILING (FAIL, PARTIAL, NO_DETECTOR)` nor `CLOSABLE (PASS, N/A)`
    (asset_census.py:2586–2587). R23 therefore cannot open or close a gap.
  - The next-emit transitions contain no `Reach.fields` row. No census verdict differs because of R23.
- **Figures reproduced:** 117 measured and 10 with no target; 26 with no capability module; 17 lower-bound widths;
  median width 0.75 with 6 at 1.0; ephemeris_daily depth 1.0 = 825,084/825,084 (`ayanamsha_id IN ('tropical')`).
- **Dark-table spot-check.** I searched the actual serving code, not just the registry layers.

  | table | R23 | reviewer finding |
  |---|---|---|
  | kala_field | dark | **genuinely dark**: `platform-mcp/src/lib/kala_ritual_resonance.ts:494–507` and `kala_views/ritual.ts:783–786` state "no serving capability exists over any kala_field* table" |
  | bodha_signal_embeddings | dark | **genuinely dark**: `L2_bodha/query_signals.ts` advertises a semantic path but only ever reads `bodha_msr_signals` (salience fallback, :478/:725) |
  | mimamsa_preferences | dark | dark to serving (only `platform/src/lib/cockpit/assetClearSpec.ts`, a cockpit spec) |
  | **ga_prashna_judgment** | dark | **not dark**: `platform-mcp/src/tools/register_p1_synthesis.ts:1011` `FROM ga_prashna_judgment gj` (an MCP tool) |

  - **A wider sweep** of SQL `FROM`/`JOIN` outside the registry layers finds MCP tool reads for at least **7 of the
    26**: bg_dignity_reference (`kala_views/ahead.ts`, `now.ts`, `register_p1_reference.ts`),
    bg_gochara_citation_resolution and gochara_resonance_map (`retrieval/register_gochara_windows.ts`),
    reference_nakshatra and bg_transit_rules (`register_p1_reference.ts`), ga_prashna_judgment, and kala_field_skill
    (`lib/kala_envelope.ts`).
  - **Why they are missed:** R23's surface (`CAPS_ROOT = platform/src/lib/retrieval/registry/layers`) excludes the
    `platform-mcp/src/tools/**` serving plane.
  - The report hedged OS-3 ("a question for its serving owner, not a verified gap"), and R23 is ungraded, so this
    blocks no gate. It does make the OS-3 list roughly a quarter wrong (C3).

## §6 — R240: is it fully discharged by R20?

**Yes, for the misclassification risk.** I checked every asset with a writer for own tables the resolved scope
never writes (insert / upsert / replace / update / COPY). The only assets were:
- **ka_gochara** (the known mismatch);
- **the 4 writes-nothing assets whose registry declares a table** (bo_samvada, mi_abhilekha, mi_seva, mi_vistara);
- **ga_structural**, whose `fact_category_ownership` is a count_sql join table, not an output.

No other asset has a registry/writer table-name mismatch. The stem heuristic is narrow: it matches only names
sharing a prefix. A mismatch without a shared stem would fall into "it replaces only other tables" and still read
PARTIAL, never PASS. So it cannot be silently laundered, only less precisely named. **R240 needs no commit**, as the
report says. The registry re-point stays the data-plane owner's action.

## §7 — The decisive test: the simulated next emit and the 41 unverified closures

### §7.1 Emit reproduction
- **Real ledger copy** (md5 `7f2257a8…`, 830 lines), six layers, `--emit-gaps`:

  | run | closed | opened | re-opened | detail |
  |---|---|---|---|---|
  | HEAD `480d799af` (code = `8702ee331`) | **58** | **11** | **0** | closed per layer L0 26 · L1 18 · L2 12 · L5 2; all 58 are `Idem.pattern`; opened = 11 L2 `Complete.depth` |
  | base code on the same tree (writer sources are identical between a72cdf460 and HEAD) | **0** | 11 | 0 | the same 11 `Complete.depth`, so live data moved and W2-3 did not cause them |

- **Idempotent:** a HEAD re-emit on the same copy appended 0 and closed 0. The ledger md5 was
  `a8bbf875…` before and after, **byte-identical**.
- **The 58 closed gap_ids equal the builder's `next_emit_transitions_final.txt` list exactly.**

### §7.2 Hand-verification of all 41 closures the builder did not read

Method: read the credited statement in context, the path from the writer entry to it, every conditional exit
before it, and every own-table read in the resolved scope (`ownreads`, `exits` screens, then source reading).
Result: **41 checked. 35 hold unconditionally, 6 hold on the census chart but sit behind a live DB conditional
hold. 0 false.**

| # | asset | credited replacement (read) | exits before it | verdict |
|---|---|---|---|---|
| 1 | bg_class_lifetime_counts | `l0_class_lifetime_counts.py:721` INSERT … ON CONFLICT … DO UPDATE into brahma_class_priors (its registry target) | dry-run; information_schema preflight raise (:710) | genuine (L0 upsert) — note that 2 assets share one target table |
| 2 | bg_class_priors | `l0_class_priors.py:319–407` five ON CONFLICT DO UPDATE | dry-run; table-exists preflight (:309) | genuine |
| 3 | bg_concordance | §3.1 | | genuine (#7) |
| 4 | bg_doshas | §3.1 | | genuine |
| 5 | bg_formula_constants | `l0_formula_constants.py:237–242` ON CONFLICT (constant_id) | dry-run; preflight | genuine |
| 6 | bg_ghatana | `l0_ghatana.py:878/887`, `:923/928` ON CONFLICT (event_class_id / activity_class_id) | dry-run; preflight; shape asserts | genuine |
| 7 | bg_kota_chakra_rings | `l0_kota_chakra_rings.py:154` ON CONFLICT (table_version, ring_position) DO UPDATE | dry-run | genuine |
| 8 | bg_kp_sublord_division | `l0_kp_sublord_division.py:423–427` stale-version DELETE, then the :316 upsert | verification raise (:405, not TWO_PASS); dry-run | genuine |
| 9 | bg_medical_mappings | `l0_medical.py:421–427` ON CONFLICT (graha) DO UPDATE | dry-run | genuine |
| 10 | bg_nakshatra | `l0_nakshatra.py:1395–1397` DELETE ×3 then insert | shape-validation raises (:1374–1384); dry-run | genuine |
| 11 | bg_nakshatra_medical | `l0_medical.py:453–458` ON CONFLICT (nakshatra_name); a stacked `@register` on the same class (`bg_medical_mappings.py:25–27`) | dry-run | genuine |
| 12 | bg_ontology | `l0_ontology.py:1119/1123` ON CONFLICT DO NOTHING / DO UPDATE | dry-run | genuine |
| 13 | bg_phaladeepika_latta | `l0_phaladeepika_vedha.py:160–165` ON CONFLICT (table_version, graha) | dry-run | genuine |
| 14 | bg_prashna_rules | `l0_prashna.py:807–918` five ON CONFLICT DO UPDATE | dry-run | genuine |
| 15 | bg_remedies | `l0_remedy_corpus.py:3462/3484` upsert + `:3551` DELETE of identities no longer produced; `l0_remedy_loader.py:206` upsert (tantric) | dry-run; preflight; postflight count raise | genuine (converges) |
| 16 | bg_sign_medical | `l0_medical.py:479–485` ON CONFLICT (sign_number) | dry-run | genuine |
| 17 | bg_transit_engine | `l0_transit.py:913` ON CONFLICT (graha) DO UPDATE; stacked `@register` (`bg_transit_rules.py:11–12`) | dry-run | genuine |
| 18 | bg_transit_rules | `l0_transit.py:938` upsert + `:973–985` retire of stale owned rows | dry-run | genuine |
| 19 | bg_vastu_directions | `l0_vastu_directions.py:298–325` two ON CONFLICT DO UPDATE | dry-run | genuine |
| 20 | bg_vedha_malefic_scale | `l0_phaladeepika_vedha.py:129–133` ON CONFLICT | dry-run | genuine |
| 21 | bg_yogas | `l0_yogas.py:2244–2249` DELETE ×4 (ontology scoped to entity_class) | dry-run | genuine |
| 22 | ga_ayurdaya | `ga_ayurdaya_writer.py:281` `replace_prior_chart_facts` → `_idempotency.py:54–72` | empty positions/rows returns (:273/:277) | genuine (#7) |
| 23 | ga_panchanga | `_insert_chart_facts_rows` (:1269–1272) → replace; called at :1467 | none | genuine |
| 24 | ga_sade_sati | `_insert_rows` (:1828) → replace | upstream-absent raise (:1958–1966); the COUNT(*) FROM chart_facts probes (:1449–1483) read upstream categories, empty polarity | genuine |
| 25 | ga_sensitive | `_insert_rows` (:2906) → replace, from `build_ga_sensitive_for_ayanamsha` (:3070) | divergence raise (:3059) | genuine |
| 26 | ga_sensitive_degree | `build_ga_sensitive_degree_substep` replace (:815) | empty returns (:802/:813) | genuine (#7) |
| 27 | ga_strength | `_insert_chart_facts_rows` (:1657–1660) → replace; called at :1829 | none | genuine |
| 28 | ga_structural | `_insert_chart_facts_rows` → replace; own-table reads at :2144 etc. are fact_id lookups (`_real_fact_id_ref`) | FORENSIC gate on the canonical chart; catalog loads | genuine |
| 29 | ga_tajaka | `replace_prior_tajik_varsha` (`_idempotency.py:113–136`, chart × varsha_year × ayanamsha) at :831 | FORENSIC muntha raise (:806); divergence (:821) | genuine |
| 30 | ga_nakshatra | §3.1 | | genuine |
| 31 | ga_medical | §3.1 | | genuine |
| 32 | ga_vastu | §3.1 | | genuine |
| 33 | ga_vichara | §3.1 | | genuine (#7) |
| 34 | bo_grounding | §3.1 | | genuine (#7) |
| 35 | bo_karanajala | §3.1 | | genuine (own table) |
| 36 | **bo_arudha** | `replace_prior_msr_for_chart` (:175) → `_idempotency.py:136–216`, which calls `_assert_msr_delete_safe` (:168) → `public.assert_l2_msr_delete_safe` | `continue` on empty facts/rows (:158/:170) | **conditional**: DB hold live on chart 1c826d5a (552 kala_convergence dependents) |
| 37 | **bo_laksana** | `run_substep` → `replace_prior_msr_for_chart` (:3595) → same assert | G3 empty-upstream raises; partial-generation refusals (:3445–3531), all before any write | **conditional**: live on 1c826d5a (16,853 kala_convergence + 750 kala_darshana) |
| 38 | **bo_nakshatra_semantic** | replace (:161) → same assert | `continue` (:135/:151/:156) | **conditional**: live on cb73cd3d (1,270) |
| 39 | **bo_special_lagna** | replace (:148) → same assert | `continue` | **conditional**: no dependents on any chart today |
| 40 | **bo_sudarshana** | replace (:248) → same assert | upstream raises (:192/:201) | **conditional**: live on 1c826d5a (552) and cb73cd3d (635) |
| 41 | **bo_vargottama_dhana** | replace (:159) → same assert | `continue` (:139/:154) | **conditional**: live on cb73cd3d (635) |

**The DB hold, read from the live catalog.**
- `assert_l2_msr_delete_safe` (`pg_get_functiondef`, read-only) loops over every FK onto `bodha_msr_signals`
  except embeddings and contradictions: kala_activation / kala_convergence / kala_darshana / kala_obstruction /
  kala_bhavishya, all `ON DELETE CASCADE`. It runs
  `RAISE EXCEPTION 'L2 MSR replacement blocked by cross-layer dependent rows in %.%'` whenever a dependent row
  references this producer's signals for the chart.
- **Canonical chart 482012f1: 0 dependents per producer**, so the closures are earned on the census chart.
- **Chart 1c826d5a (Abhinandan) and cb73cd3d: dependents exist**, so a rebuild of those assets raises there
  instead of replacing.
- **How this relates to known work.** It is §2.4's blind spot #6 ("a hold enforced by the database"), live. The
  report presents #6 only hypothetically ("a unique constraint … or a trigger"). The C-KSHETRA review's hold sweep
  looked for Python shapes only.
- **Why it is a ruling, not a verdict flip:**
  - ka_kshetra is held whenever its *own* output exists.
  - The MSR family is held whenever *downstream-layer* output references it. That is a deliberate D-CND-15-style
    interlock (see the comments at `_idempotency.py:78–111`).
  - Whether that is a "held rebuild" under §N.3 is a native ruling. It is not a detector bug to fix silently (C1).

**Also confirmed for the builder's own 17:**
- bo_pramana_mapa's `replace_prior_scorecard` deletes `WHERE chart_id` only (`_idempotency.py:517–526`). The
  build_id parameter is explicitly unused, so the S2 shape was fixed there historically.
- bo_bimba / bo_upaya / bo_samskara helpers carry no DB assert.

## §8 — R241's disclosed blind spots

| # | disclosed shape | accurate? | fixable in-packet? | live in a current writer? |
|---|---|---|---|---|
| 1 | `SELECT NOT EXISTS` probe | yes | yes (polarity inversion, small) | no |
| 2 | compound `BoolOp` test (force flag) | yes; the trade-off (incremental skip has the same shape) is real | not without false FAILs | no |
| 3 | flag built from a comparison | yes | yes (track `Compare` bindings) | no |
| 4 | probe with no literal SQL (ORM, assembled SQL) | yes | no (static limit) | no |
| 5 | beyond the resolved scope | yes | no (by design, hop limit) | not detectable by construction |
| 6 | hold enforced by the database | accurate as a *mechanism* | partially: the Python call site `_assert_msr_delete_safe` is in scope and name-recognisable | **YES, live**: 6 L2 closures (§7.2). The report does not say so |
| 7 | empty-upstream early return before replacement | yes | no (grading it FAIL would be wrong) | **YES, live**, and wider than the two examples: bo_arudha, bo_grounding, bo_nakshatra_semantic, bo_special_lagna, bo_vargottama_dhana, ga_ayurdaya, ga_sensitive_degree, ga_vichara, bg_concordance and more |

**Shapes missing from the list** (reviewer fixtures, real `idem_scan`; all produce PASS with a held rebuild):
- the inline probe test `if cur.fetchone()[0]:` (only a *name bound* to `fetchone` is tracked);
- `SELECT count(1) FROM own WHERE chart_id`;
- an aliased probe `FROM own o WHERE o.chart_id`;
- a probe whose WHERE puts another predicate before `chart_id`;
- `EXISTS (SELECT * FROM own …)`.

The inline `fetchone()` form is the most natural Python spelling. **Live check:** every own-table read in the
resolved scopes of all 110 PASSes is either a post-write verification count (L0 seeders, bg_remedies, bg_texts…),
an upstream read of a shared table (ga_sade_sati, ga_structural), or the build-scoped resume probe (ga_vargas).
**None of these shapes produces a live false PASS today.** Add them to the disclosed list (C2).

## §9 — Scope, regression, ledger safety

- **Scope:** `git diff --name-only a72cdf460 HEAD` outside `nikasha_test/wave2/**` is exactly
  `asset_census.py`, `test_w2_3_deeper_detectors.py`, and the one-line stubs in `test_w2_1_earned_verdicts.py` and
  `test_a4_gate_corrections.py`. No writer, orchestrator, migration, ledger, register or STATE file changed.
- **Ledgers:** `asset_gaps.jsonl` md5 `7f2257a8d4f0d6a7a21c0648b4101f85` (830 lines) and `asset_certs.jsonl` md5
  `514cbdfcf3fa71b3e382f84a978bf369` match the blobs at `a72cdf460` (`git show a72cdf460:… | md5`). They were
  identical at review start and at close. All emits ran on copies via `NIKASHA_CONTROL_DIR`.
- **Offline suite (HEAD):** **348 = 323 passed · 23 skipped · 2 failed**. The 2 are
  `test_drift_detector_h35_h38.py::test_f163_current_row_flagged_predecessor_row_is_not` and
  `::test_h35_critical_when_canonical_artifacts_missing`, both pre-existing.
- **Live suite (HEAD, one invocation, pgenv, `timeout 900`):** **346 passed · 2 failed** (348) in 517.6 s. These
  are the same 2 pre-existing failures.
- **Manifest:** `manifest_fingerprint.py --check` gives declared 1847709eec2bad52 = observed 1847709eec2bad52,
  **MATCH**.
- **Drift:** `drift_detector.py` gives **exit 3**, 1 finding: 0 CRITICAL / 0 HIGH / 0 MEDIUM / 1 LOW
  `a3_category_not_yet_populated` (pre-existing). Its report was written inside the scratch worktree, which was
  removed.
- **Census diff reproduced:** 2,446 = 2,446 verdicts, same keys. There are 58 verdict changes, all `Idem.pattern`
  PARTIAL→PASS, none toward FAIL or N/A. There are 151 text-only changes (127 Reach.fields, 24 Idem.pattern).
- **Idem live counts:** PARTIAL 69→11, PASS 52→110, FAIL 1, N/A 5.

## §10 — Remaining findings and the gate each blocks

| id | finding | severity | blocks |
|---|---|---|---|
| **C1** | The 6 L2 MSR-family closures sit behind the live DB interlock `assert_l2_msr_delete_safe` (raises on cross-layer dependents). They are earned on 482012f1 today and held on 1c826d5a / cb73cd3d. | **medium** | **The register fold of R20** and **the next production emit**. Fold "58/69" as "52 unconditional + 6 conditional (DB interlock; native ruling queued)". Either record the caveat in those 6 gaps' disposition, or withhold them from the next production emit until the native rules. If the ruling is "hold", open a detector row to read `_assert_msr_delete_safe` (or any `assert_*_delete_safe` call in scope) as a hold. |
| **C2** | R241's disclosed list is incomplete. It misses the inline-`fetchone()` / `count(1)` / aliased / predicate-first / `EXISTS(SELECT *)` probe forms, and the R20 PASS-direction shapes: uncalled class method credited, build-scoped DELETE credited, flag-gated DELETE, COPY-only own table, upsert-only secondary own table (inconsistent with single-table FAIL), stray row outside the DELETE predicate. #6 and #7 are live, not hypothetical. 0 live false PASS from the new shapes. | low (documentary) | **The R241 and R20 register rows' closure text.** Record the list. No code is required for the fold. |
| **C3** | R23's surface excludes `platform-mcp/src/tools/**`. At least 7 of the 26 "dark" tables are read by MCP tool SQL (ga_prashna_judgment, bg_dignity_reference, reference_nakshatra, bg_transit_rules, bg_gochara_citation_resolution, gochara_resonance_map, kala_field_skill). kala_field and bodha_signal_embeddings are genuinely dark. | low (reported, not graded) | **Dispatching OS-3** to owners, and **any future R23 grading threshold**. Widen the surface or re-scope the list first. |
| C4 | "FAIL needs a fully-read scope" is violated by an imported SQL constant (`_resolve_def` refuses `Assign`) and by a hop-3 module without its own write text (a cut not reported). Both give a false **FAIL**, which is conservative. 0 live. | low | nothing (carry as a residual) |
| F-5 | A non-`Unknown` DAG read failure (malformed JSON) crashes `measure()`. It is fail-closed, not null-with-reason. | low | nothing |
| F-6 | Cross-asset stray rows: bo_karanajala upserts 130 arudha/special_lagna nodes into bo_bimba's `bodha_cgm_nodes` with `DO NOTHING`, and nobody deletes them, so they are never refreshed by a rebuild. This is invisible to per-asset Idem.pattern. Latent today (single build). | low–medium (data quality, out of W2-3 scope) | nothing in W2-3. Route to the L2 owner. |
| F-7 | Report consistency: §4 lists ga_vargas among the "two hops down" L1 flips, but it PASSes at one hop on its own `DELETE … ayanamsha_id='INVARIANT'` (`ga_vargas_writer.py:2896`). With the hop limit at 1, exactly the 10 §0 names read PARTIAL, as reproduced. R20-M5 now kills with 3 tests under `-k r20` (the follow-up test matches). | cosmetic | nothing |
| F-8 | The `_schema` line of `asset_gaps.jsonl` does not list `blocking_radius` / `severity_weight` / `blocking_radius_note` (the report's OS-2). | cosmetic | the executor's ledger `_doc` amendment |

**No finding blocks acceptance of the code.** C1 gates how the six closures are *worded and emitted*, not whether
R20 is correct.

## §11 — Fact spot-check (claims in W2-3_REPORT.md, each re-measured)

| # | claim | reviewer measurement | holds |
|---|---|---|---|
| 1 | next emit: 58 closed · 11 opened · 0 re-opened (per layer 26/18/12/0/0/2) | identical | ✓ |
| 2 | base code on the same data closes 0, opens the same 11 | identical | ✓ |
| 3 | re-emit byte-identical | md5 a8bbf875… before and after | ✓ |
| 4 | census 2,446 = 2,446; 58 verdict changes; 151 text-only (127 + 24) | identical | ✓ |
| 5 | Idem PARTIAL 69→11, PASS 52→110, FAIL 1, N/A 5 | identical | ✓ |
| 6 | 10 of the 58 PASSes need the second hop | exactly 10 read PARTIAL at `IDEM_DELEGATION_HOPS=1` (the §0 list) | ✓ (the §4 listing has 11; F-7) |
| 7 | radius equals an independent recursive CTE on all 127 | my own CTE: 127/127 | ✓ |
| 8 | ga_positions-Build weighs 80, bo_cdlm_summary 1; distribution 40/15/18/54; top radii | identical | ✓ |
| 9 | Build rows carry the radius, non-Build rows none | 23/23 Build, 0 non-Build (live L1 emit on a fresh ledger) | ✓ |
| 10 | R23: 117 measured, 26 dark, 17 lower-bound, median width 0.75, 6 at 1.0, ephemeris_daily 825,084/825,084 | identical | ✓ (the "dark" set is surface-scoped; C3) |
| 11 | offline 348 = 323 / 23 / 2, the 2 pre-existing | identical | ✓ |
| 12 | manifest MATCH 1847709eec2bad52; drift exit 3, 1 LOW | identical | ✓ |
| 13 | production ledgers md5 7f2257a8… / 514cbdfc… untouched | identical to the a72cdf460 blobs | ✓ |
| 14 | the mutations kill with the stated counts | 18 re-run (9 R20; R241-M1/M3/M5/b-M1; R21-M1/M2/M5; R23-M1/M5): all kill. Counts match except R20-M5 (3 vs 2, explained) | ✓ |
| 15 | "None of these shapes is live today" (R241, and #6 framed hypothetically) | #6 is live via `assert_l2_msr_delete_safe`; #7 live across ≥9 assets | ✗ (C1/C2) |
| 16 | "the 11 remaining PARTIALs … each with a named reason"; 8 write nothing | all 11 texts re-read and sources checked; accurate | ✓ |
| 17 | bo_pramana_mapa `replace_prior_scorecard` deletes WHERE chart_id | `_idempotency.py:517–526` | ✓ |

**Not reproduced by me:**
- 14 of the 32 mutation runs: R242 ×2, R241-M2/M4/M6/M7/b-M2, R21-M3/M4, R23-M2/M3/M4/M6/M7. I re-ran the other 18.
- Individual reads of ka_graha_sancara / ka_muhurta_seva writer bodies. Their PARTIAL rests on a declared-empty
  own-table set.
