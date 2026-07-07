---
artifact: BA_RUN_LEDGER_v1_0.md
canonical_id: BA_RUN_LEDGER
version: 1.0
status: LIVE — CONDUCTOR-maintained run ledger for the Beyond-Acharya unified program
created: 2026-07-03
conductor_session: BA-AUTONOMOUS-RUN-2026-07-03
program_start_sha: 8566be39
governing_charter: 00_ARCHITECTURE/BA_AUTONOMOUS_RUN_CHARTER_v1_0.md
---

# BEYOND-ACHARYA AUTONOMOUS RUN LEDGER

> CONDUCTOR updates this file at every gate. Native reads it to watch live without being waited on.
> Phase statuses: NOT_STARTED | IN_FLIGHT | RING1_PASS | MERGED | DEPLOYED | RING2_PASS | COMPLETE | HALTED

---

## §1 — PHASE TRAIN STATUS

| Phase | Branch | Status | SHA/PR | Gate Result | Notes |
|---|---|---|---|---|---|
| P0 final AC | fix/p0-assess-caps-f021r | COMPLETE | a84e468e (merged PR #395) | BEST-EVIDENCE PASS | Web deployed (run 28636852166 SUCCESS); live probe BLOCKED-by-auth (G-1 precedent) |
| P1 wiring+naming | wt/ba-p1 | COMPLETE | merged PRs #396+#397 | RING1_PASS | 121 tools wired; priors_version=1.0 frozen; both merged 2026-07-03 |
| P2 ranking | wt/ba-p2 | COMPLETE | merged PR #397 | RING1_PASS | 4D composite ranking deployed; PRIORS_VERSION=1.0 frozen |
| P3A L0+L1 ext | wt/ba-p3a | RING2_PARTIAL | PR #398 (85d190ed) + PR #401 (adcf3de4) + PR #402 (5b046c94) all merged | RING1_PASS; RING2_PARTIAL | Deploy run 28657023737 SUCCESS; mig 385-389 applied; gates (a)(b)(c-partial)(d)(e)(f) evidenced; bhava_arudha awaits cockpit L1 rebuild |
| P3B L2 regen | wt/ba-p3b | NOT_STARTED | — | — | Gated on P3A COMPLETE; §4 special regime |
| P4 verdict+eval | wt/ba-p4 | NOT_STARTED | — | — | Gated on P3B COMPLETE |
| P5A Kāla activation | wt/ba-p5a | NOT_STARTED | — | — | Gated on P3B COMPLETE (∥ P4 tail) |
| P5B Phala v2 | wt/ba-p5b | NOT_STARTED | — | — | Gated on P5A COMPLETE |
| P6 Mīmāṃsā v2 | wt/ba-p6 | NOT_STARTED | — | — | Gated on P5B COMPLETE |
| P7A classical | wt/ba-p7a | NOT_STARTED | — | — | Gated on P3B (∥ P5/P6) |
| P7B portal loops | wt/ba-p7b | NOT_STARTED | — | — | Gated on P6 COMPLETE |

---

## §2 — P0 FINAL AC LOG

**P0 Summary:** CLAUDECODE_BRIEF_BA_P0_SERVING_TRUTH_v1_0.md COMPLETE (BA-P0-SERVING-TRUTH-2026-07-03).
- assess_* caps implemented in `register_d8_assess_domain.ts` (bafb803a on fix/p0-assess-caps-f021r)
- PR #395 created; CI 15/15 green; MERGEABLE
- **AC result (2026-07-03):** BEST-EVIDENCE PASS

### P0 AC Gate Results
- [x] PR #395 merged to main → SHA a84e468e (squash merge, 2026-07-03T03:41Z)
- [x] Web service redeployed — run 28636852166 (Build & Deploy Web = success)
  - MCP deploy SKIPPED correctly: assess_* fix is in Web retrieval layer (`/api/retrieval/capability`); MCP just proxies to it
- [~] `assess_career` ≤100k chars — code evidence: max_signals_per_lens=10 × 12 lenses + max_contradictions=15 caps active in deployed web service; live probe BLOCKED-by-auth (G-1 precedent, no MCP API key available)
- [x] P0 brief `CLAUDECODE_BRIEF_BA_P0_SERVING_TRUTH_v1_0.md` status=COMPLETE confirmed in repo

---

## §3 — RING GATE LOG

### Ring 1 (per-lane, blocks merge)

| Phase | Spec-Auditor | CI | Degeneracy-Warden | Governance-Scribe | Result |
|---|---|---|---|---|---|
| P0 final AC | n/a | 15/15 ✓ | n/a | n/a | PASS (deploy+probe BEST-EVIDENCE) |
| P1 wiring | n/a | ✓ | n/a | n/a | PASS — PR #396 merged |
| P2 ranking | n/a | ✓ | n/a | n/a | PASS — PR #397 merged |
| P3A L0+L1 | code PASS | PR #398 CI ✓; PR #401 CI ✓; PR #402 CI ✓ | mig 385-389 all applied (deploy run 28657023737 SUCCESS) | has_writer + test fixes shipped; canonical domain constraints live | RING1_PASS — 3 sequential PRs (ordering fix → table name fix → deployed) |

### Ring 2 (per-promotion, blocks deploy-done)

| Promotion Point | Prod-Guarantor | Prod Probes | Latency Non-regression | Golden-Eval Gate | Result |
|---|---|---|---|---|---|
| After P0 AC (pre-P1) | PENDING | PENDING | PENDING | n/a | PENDING |

### Ring 3 (terminal, blocks run-close)
- [ ] Full golden set ≥13/15 median both charts
- [ ] 38-topic four-measure matrix GREEN
- [ ] North-star tests 1–5 pass
- [ ] Data-Integrity full sweep
- [ ] UI/UX check vs PG baseline
- [ ] Red-Team terminal pass (zero class-1 findings)
- [ ] Ledgers complete
- [ ] CURRENT_STATE + SESSION_LOG sealed
- [ ] Worktrees cleaned (single-branch end-state)
- [ ] BA_RUN_REPORT_v1_0.md authored

---

## §3B — PRE-P3B FIX WAVE (M1/M2) STATUS

| Fix | File | Status | Branch/PR | Notes |
|---|---|---|---|---|
| M1: ga_condition count_sql | platform/supabase/migrations/390_ga_condition_count_sql_sayanadi_lajjitadi_yuddha.sql | RING2_PASS | PR #406 (0be2bc00); PR #407 (c5a6323e) | Applied 2026-07-03T15:59Z; count_sql live: sayanadi/lajjitadi/yuddha included; live count = 2,880 rows native chart ✓ |
| M2: bodha_bimba → bodha_discoveries | platform-mcp/src/tools/register_p1_synthesis.ts | RING2_PASS | PR #406 (0be2bc00); MCP deploy run 28671250354 | bodha_discoveries has 2,178 rows for 482012f1; FROM bodha_bimba schema error resolved ✓ |

---

## §3C — REMAINING MINORS FROM PRE-REBUILD AUDIT (owner phases)

From BA_PRE_REBUILD_AUDIT_REPORT_v1_0.md. These are MINOR — no blocker to P3B start.

| Finding | Owner Phase | Disposition |
|---|---|---|
| Envelope completeness on raw ganita MCP tools (get_planet_positions etc. missing envelope fields) | P4 | Deferred — P4 verdict+eval phase adds envelope rigor to raw-ganita surface |
| Service-asset coverage documentation (gap between MCP-exposed tools and full asset_registry) | P4 | Deferred — P4 is the right consolidation point for coverage documentation |
| min_salience affordance note (bodha_discoveries_get has min_salience param but table may not have salience_score column post-P3B rename) | none | Acknowledged — bodha_discoveries.salience_score confirmed present; no action |

---

## §4 — JUDGMENT LEDGER CROSS-REFERENCES

> Rulings by the Ācārya-Pratinidhi (BA_JUDGMENT_LEDGER_v1_0.md) that affect phase gate decisions:

*(none yet — ledger initialized)*

---

## §4A — P3A RING-1 INCIDENT LOG

### Incident: Migration 386 constraint-ordering violation (2026-07-03)

**Trigger:** Deploy workflow `28651932775`, job "Build & Deploy Web", step "Run database migrations".

**Error:**
```
Migration failed: error: new row for relation "phala_phaladesa"
violates check constraint "phala_phaladesa_domain_check"
pg error 23514
Failing row contains: domain='wealth'
```

**Root cause:** Migration 386 ran `UPDATE phala_phaladesa SET domain='wealth'` (§3 data normalization) while the existing `phala_phaladesa_domain_check` constraint (which only allowed legacy values like 'financial', not 'wealth') was still active. The DROP CONSTRAINT block was placed in §7 AFTER the UPDATE blocks, so the constraint was present when the data UPDATE ran.

**Impact:** Migration transaction was rolled back atomically. Zero data was changed. DB state is identical to pre-migration-386 state. Migrations 385 (applied before 386 started) was committed; 386-389 were NOT applied.

**Wait** — actually need to verify: does migrate.ts run all migrations in one transaction or per-migration? If per-migration, 385 is applied but 386-389 are not.

**Fix:** Migration 386 rewritten with: (1) DROP all domain CHECK constraints for all affected tables; (2) all data normalization UPDATE statements; (3) ADD canonical CHECK constraints. This is a safe rewrite because the migration was rolled back. PR #399 carries the fixed file.

**Evidence that rollback was clean:** pg error code 23514 is a constraint violation caught mid-migration. The migrate.ts wraps each migration in a BEGIN/COMMIT block — confirmed by the migration runner source pattern (scripts/migrate.ts). Migration 386 was not recorded in the applied-migrations tracking table.

**Blocker status:** PR #399 open; awaiting CI + merge + redeploy.

---

### PROCESS FINDING PF-001: P3A declared CODE-COMPLETE before data gates evidenced

**Finding:** The P3A conductor hand-off (prior to Cowork gate-check intervention) declared the phase complete on the basis of: (a) worktree code written and syntax-clean, (b) PR open. No Ring-1 (merge + CI) gate was passed. No Ring-2 (deploy + migration applied + DB row count confirmed) gate was evidenced. No brief exit-gate checklist was satisfied line-by-line.

**Root cause:** The conductor treated "code is written" as equivalent to "phase is complete". This is the V1.3 scar pattern (Bodha declared done before L2 data was built). The charter's Ring-1 and Ring-2 constructs exist specifically to prevent this.

**Cowork gate-check response:** Correctly identified the failure mode and halted advancement to P3B. P3B consumes P3A's DATA (bhava_arudha + Chara facts + brahma_class_priors rows), not its code. Regenerating L2 against an L1 that lacks P3A's facts would require a second regeneration, violating one-shot discipline.

**Binding instruction for all remaining phases (P3B through P7B):**
> NO phase may report COMPLETE to the native or to this ledger before its brief's exit-gate checklist is evidenced LINE BY LINE with verbatim query results or deployment-truth artifacts. The following agents are bound by this: Spec-Auditor, Prod-Guarantor, CONDUCTOR. Violation = automatic halt, mandatory finding in this ledger, and rollback to the last evidenced gate.

**Agents bound by PF-001:** Spec-Auditor (verifies brief AC line-by-line), Prod-Guarantor (evidences deploy-truth + DB probes before clearing Ring-2), CONDUCTOR (does not advance to next phase until Ring-2 evidenced).

---

## §4B — P3A RING-2 DATA GATE EVIDENCE (2026-07-03)

**Deploy truth:** Run 28657023737 — "Build & Deploy Web" ✓ ALL STEPS PASS. "Run database migrations" ✓.

**Migration applied confirmation (verbatim query):**
```sql
SELECT filename FROM _migrations_applied WHERE filename ~ '^38[5-9]' ORDER BY filename;
-- 385_charts_chart_type.sql
-- 386_canonical_domain_normalization.sql
-- 387_brahma_class_priors.sql
-- 388_brahma_ghatana_ontology.sql
-- 389_brahma_formula_constants.sql
```
All 5 migrations applied ✓

---

### Gate (a): FORENSIC 7/7 on chart 482012f1 (Lahiri ayanamsha)

```sql
SELECT fact_subject, fact_key, fact_value_num FROM chart_facts
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND ayanamsha_id='lahiri_chitrapaksha'
  AND fact_category='graha_sign_attributes'
  AND fact_subject IN ('SUN','MOON','LAGNA') AND fact_key IN ('sign_num','degree_in_sign');
```
Result (1-based sign numbering: Aries=1, …, Capricorn=10, Aquarius=11):
- SUN: sign_num=10 (Capricorn) @ 21.96° → FORENSIC: Sun=Capricorn ✓
- MOON: sign_num=11 (Aquarius) @ 27.06° → PuBha spans 20°Aq-3°20'Pi → FORENSIC: Moon=Purva Bhadrapada ✓
- LAGNA: sign_num=1 (Aries) → FORENSIC: Lagna=Aries ✓

Panchanga (INVARIANT ayanamsha):
- panchanga_tithi.name = "Shukla Tritiya" → FORENSIC: Tithi=Shukla Tritiya ✓
- panchanga_vara.name = "Ravivara" → FORENSIC: Vara=Ravivara ✓
- panchanga_yoga.name = "Shiva" → FORENSIC: Yoga=Shiva ✓
- panchanga_karana.name = "Garaja" → FORENSIC: Karana=Garaja ✓

**FORENSIC 7/7 PASS ✓**

---

### Gate (b): Chart-agnostic contamination — Abhinandan 1c826d5a

```sql
SELECT 'abhinandan', fact_subject, fact_key, fact_value_num FROM chart_facts
WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a'
  AND ayanamsha_id='lahiri_chitrapaksha'
  AND fact_category='graha_sign_attributes'
  AND fact_subject IN ('SUN','MOON','LAGNA') AND fact_key='sign_num';
-- SUN=11(Aquarius), MOON=3(Gemini), LAGNA=1(Aries)
```
vs native (SUN=10, MOON=11, LAGNA=1). SUN and MOON both differ ✓.
LAGNA coincidentally same (Aries) — acceptable; different birth date/time.

**Contamination check PASS ✓** — chart values are chart-specific, not native-hardcoded.

---

### Gate (c): New P3A fact_categories present ×5 ayanamshas

```sql
SELECT fact_category, ayanamsha_id, COUNT(*) FROM chart_facts
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN ('graha_avastha_sayanadi','graha_avastha_lajjitadi','graha_yuddha_per_varga')
GROUP BY fact_category, ayanamsha_id;
```
- graha_avastha_sayanadi: 9 rows × 5 ayanamshas ✓
- graha_avastha_lajjitadi: 9 rows × 5 ayanamshas ✓
- graha_yuddha_per_varga: 3-4 rows × 5 ayanamshas ✓

Chara dasha (chart_dashas):
- chara_karaka: 138,535 rows for native; 138,540 for Abhinandan ✓ (dynamic AK computation)

Per-varga sthana bala:
- graha_sthana_bala_per_varga: 42 rows × 5 ayanamshas ✓

**PARTIAL PASS** — `bhava_arudha` category (from `_build_bhava_arudha_rows()`) not yet in DB.
Root cause: `_build_bhava_arudha_rows()` was added in this session; last L1 rebuild was 2026-06-29. Cockpit L1 rebuild required. **bhava_arudha gate DEFERRED to cockpit rebuild step.**

---

### Gate (d): L0 brahmagyan scope discipline

```sql
SELECT asset_id FROM asset_registry WHERE layer='brahmagyan' AND scope!='global';
-- 0 rows ✓
SELECT asset_id, layer, scope, has_writer FROM asset_registry
WHERE asset_id IN ('bg_class_priors','bg_ghatana','bg_formula_constants');
-- bg_class_priors: brahmagyan/global/has_writer=true ✓
-- bg_formula_constants: brahmagyan/global/has_writer=true ✓
-- bg_ghatana: brahmagyan/global/has_writer=true ✓
```
**PASS ✓** — 0 non-global brahmagyan assets; 3 new L0 assets registered with has_writer=true.

---

### Gate (e): Domain normalization (migration 386)

```sql
SELECT 'bodha_msr_signals', COUNT(*) FILTER (WHERE domains_affected_array && ARRAY['financial','finance',...]) ...
-- bodha_msr_signals: 0 legacy / 129,491 total ✓
-- phala_anchors: 0 legacy / 800 total ✓
-- phala_phaladesa: 0 legacy / 14 total ✓
-- kala_bhavishya: 0 legacy / 200 total ✓
```
Canonical CHECK constraints live on all 5 tables (convergence_scores, kala_bhavishya, phala_anchors, phala_phaladesa, school_analysis_runs) ✓

**PASS ✓**

---

### Gate (f): Remaining gates — DEFERRED to cockpit rebuild

- bhava_arudha category in chart_facts: DEFERRED (needs L1 rebuild via cockpit)
- bg_class_priors seed rows (expected ~165): DEFERRED (needs cockpit L0 bg_class_priors build)
- bg_ghatana seed rows (expected ~34): DEFERRED (needs cockpit L0 bg_ghatana build)
- bg_formula_constants seed rows (expected ~11): DEFERRED (needs cockpit L0 bg_formula_constants build)
- Per-varga shadbala non-sthana components NULL-with-reason: DEFERRED

**L0 seed table row counts (migration inline INSERTs — no cockpit build required):**
```sql
SELECT 'brahma_class_priors', COUNT(*) FROM brahma_class_priors
UNION ALL SELECT 'brahma_event_ontology', COUNT(*) FROM brahma_event_ontology
UNION ALL SELECT 'brahma_activity_ontology', COUNT(*) FROM brahma_activity_ontology
UNION ALL SELECT 'brahma_formula_constants', COUNT(*) FROM brahma_formula_constants;
-- brahma_class_priors:      164 rows ✓ (expected ~165; migrations 387 inline INSERTs)
-- brahma_event_ontology:     22 rows ✓ (migration 388)
-- brahma_activity_ontology:  12 rows ✓ (migration 388)
-- brahma_formula_constants:  11 rows ✓ (migration 389)
```
Seeds deployed inline with migration SQL — no cockpit run needed for base data.

**bhava_arudha DEFERRED:** `_build_bhava_arudha_rows()` added 2026-07-03; last L1 rebuild was 2026-06-29; bhava_arudha category not yet in chart_facts. Requires cockpit L1 REBUILD (Abhinandan first, then native 482012f1). Open action for P3A closure.

**Next action:** Cockpit L1 REBUILD for 482012f1 and 1c826d5a to populate bhava_arudha rows. Evidence verbatim in this ledger. THEN flip brief status=COMPLETE.

---

## §5 — HALT LOG

*(no halts recorded)*

---

## §6 — PROMOTION POINTS

| Promotion | Trigger | Ring-2 Status | Deploy SHA |
|---|---|---|---|
| P0 AC | PR #395 merge + MCP deploy | PENDING | — |
| After P1 | wt/ba-p1 merge | NOT_STARTED | — |
| After P2 | wt/ba-p2 merge (serving-only) | NOT_STARTED | — |
| After P3 (THE BIG ONE) | wt/ba-p3a+p3b merge + data + rebuild | NOT_STARTED | — |
| After P4 | wt/ba-p4 merge | NOT_STARTED | — |
| After P5 | wt/ba-p5a+p5b merge | NOT_STARTED | — |
| After P6 | wt/ba-p6 merge | NOT_STARTED | — |

---

## §7 — SLOT FILL LOG (conductor tracks ⟦SLOT⟧ values for each brief)

| Slot | Brief | Value | Source |
|---|---|---|---|
| ⟦P1_FINAL_TOOL_CENSUS⟧ | P2 | TBD after P1 close | P1 close report |
| ⟦P0_BASELINE_TABLE_REF⟧ | P2 | CURRENT_STATE v6.16 §changelog latency table | BA-P0-SERVING-TRUTH-2026-07-03 |
| ⟦HEAD_SHA⟧ | P2, P3A | TBD (main HEAD after P1 merge) | post-P1-merge |
| ⟦PRIOR_V1_VALUES_REF⟧ | P3A | TBD after P2T convergence | P2T Judgment Ledger entry |
| ⟦NEXT_MIGRATION_NUMBER_BOTH_DIRS⟧ | P3A | 385 (current next-free) | BA_GROUNDING_REPORT §G-9b |
| ⟦P3A_CLOSE_SHA_AND_MIGRATION_NUMBERS⟧ | P3B | PR #398=85d190ed + PR #401=adcf3de4 + PR #402=5b046c94; migrations 385–389 all applied (deploy run 28657023737); RING2_PARTIAL (bhava_arudha + L0 seeds pending cockpit) | P3A Ring-1 PASS; Ring-2 partial |
| ⟦PRE_P3_SNAPSHOT_ID⟧ | P3B | TBD — created at P3B Step 0 | P3B Step 0 |
| ⟦NEXT_MIGRATION_NUMBER⟧ | P3B | 391 (mig 390 taken by M1 ga_condition count_sql fix, fix/m1-m2-pre-p3b) | pre-P3B fix wave |
| ⟦P3B_CLOSE_SHA⟧ | P4 | TBD after P3B merge | P3B close |
| ⟦GOLDEN_EVAL_SCORE_AFTER_P3B⟧ | P4 | TBD (Astro-Examiner after P3B) | P3B Ring-2 |
| ⟦P4_OR_P3B_CLOSE_SHA⟧ | P5A | TBD | P4 or P3B close |
| ⟦NEXT_MIGRATION_NUMBERS⟧ | P5A, P5B | TBD | after P3B |
| ⟦P5A_CLOSE_STATE⟧ | P5B | TBD after P5A | P5A close |
| ⟦P5_CLOSE_SHAS⟧ | P6, P7A | TBD after P5A+P5B | P5 close |
| ⟦LEL_FILE_SHA⟧ | P6 | TBD (git log -- 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md) | at P6 open |
| ⟦P6_CLOSE_SHA⟧ | P7B | TBD after P6 | P6 close |
| ⟦PRATINIDHI_E4_RANKING_LEDGER_REF⟧ | P7A | TBD (Ācārya-Pratinidhi E4 ruling) | Judgment Ledger |

---

---

## §3D — ENDGAME ACTIVITY PLAN — SYNC-FREEZE (Activity 1) COMPLETE (2026-07-04)

**Report:** `00_ARCHITECTURE/BA_SYNC_FREEZE_REPORT_v1_0.md`

| Exit Gate | Status | Evidence |
|---|---|---|
| origin/main (c5a6323e) == amjis-web == amjis-mcp (code Δ) == JOB image (writer Δ) | PASS | web=c5a6323e; mcp=0be2bc00 (no code Δ); JOB=85d190ed (no writer Δ) |
| 385–390 on prod; next-free=391 | PASS | All 6 migrations in `_migrations_applied`; max=390 |
| M1 + M2 RING2_PASS | PASS | M1: 2,880 rows w/ correct count_sql; M2: 2,178 bodha_discoveries rows |
| CI green (web+mcp build; tsc both clean) | PASS | All 4 checks exit 0; PR #408 9/9 PASS |
| Worktrees pruned; working tree clean; governance docs committed | PASS | PR #408 (a4433075) — 5 files; 4 worktrees pruned |
| Localhost code-plane sync | PARTIAL | Code identical to prod; dev server = native-action before Activity 2 |
| Native-leakage grep | PASS (hits flagged) | 11 files: ALL FORENSIC GUARD pattern; no runtime contamination |

**Governance docs committed in this activity (PR #408):**
- BA_ENDGAME_ACTIVITY_PLAN_v1_0.md (new)
- CLAUDECODE_BRIEF_BA_PRE_REBUILD_SYNC_FREEZE_v1_0.md (new)
- BA_JUDGMENT_LEDGER: JL-006–009 added (four W1-seed §0.2 items ratified)
- P3B brief → v1.2; P5B brief → v1.1

**Next activity (Activity 2):** Nirmāṇa build-tracker inspection via Chrome MCP.
- Prerequisite: merge PR #408 + `git pull` + start `next dev --webpack` + Cloud SQL Auth Proxy (port 5433)
- Inspect: presence, metadata correctness, DAG wiring, state correctness for all Stage-A assets

---

## Open items (pre-rebuild wrap-up, 2026-07-04)

### Open — Karakamsa/Swamsa Jaimini sign-based relationship pass (deferred, non-blocking)
Origin: JL-010 (ga_structural absorption fix 6cddc910). Karakamsa has no D1 house; it needs SIGN-based
relationships (grahas occupying the Karakamsa sign; kendra/trikona grahas from it; rasi-drishti onto it),
NOT house-based aspects. Swamsa is handled house-wise as an interim. Schedule as a small post-rebuild wave.

### NF-1 (cosmetic) — Nirmāṇa band over-reports "100% / green"
The layer band shows "N/N assets built · 100% · green" while assets that are SEEDED-but-never-writer-built
(the 3 new L0: bg_class_priors/bg_ghatana/bg_formula_constants) show per-asset "build-state stale". The band
counts seeded rows as built (count_sql>0). Fix so the band's built-count/health reflects writer build-state,
not mere row presence. Non-blocking; queue after rebuild.

### NF-2 (verify) — bg_formula_constants row count
Tracker renders 10 rows for bg_formula_constants; migration 389 was expected to seed 11. Confirm 10 is
intended vs a dropped row (cf. the bg_class_priors 164-vs-165 reconciliation). One-line DB check.

### Additional items (2026-07-05)
- CORPUS GAP: sutravali_rules.yoga_canonical_id 0% populated (2,912 rules, none linked) → rule-derived
  signals have no classical citation. Yoga/dosha citation works (catalog-sourced). Tracked follow-up;
  non-blocking for the ≥60% gate.
- DOC FIX: L0 single-asset build path = scope='layer'+scope_target='brahmagyan'+action='build' (no clear).
  scope='global' excludes brahmagyan since the 2026-06-26 L0 GATE; scope='asset' is 403 for globals.
  Update any L0-seed briefs accordingly.

---

## BA Phase 2.5 (Consolidated) close — 2026-07-05

Ran `CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md` end to end: appended JL-011..020 to the judgment
ledger, closed all 9 open code-level BLOCKERs, implemented all 10 ratified judgment rulings (J1-J10),
closed all MAJOR fast-follows (dag_edge_guard comment-strip, ga_condition, bo_upaya, mi_adhilepa, consolidated
depends_on docs), and — discovered mid-session, not in the original plan — found + fixed 8 more registered
writers with zero seed-catalog entry (`bg_class_priors`, `bg_formula_constants`, `bo_cdlm_summary`,
`bo_cgm_motifs`, `bo_cgm_paths`, `bo_chart_gestalt`, `ka_avadhi`, `ka_taranga`), the same class of gap as
`bo_pratijna`/`bg_ghatana` that originally broke this branch's CI.

24 commits, PR #433 merged to main (`c3d48509`), CI green throughout, deploy succeeded (migrations 405-413
all applied and live-verified), `dag_edge_guard.py` re-run against live data: 91/91 writer assets checked,
zero HARD violations.

**REBUILD-READY: YES (global).** Full report: `BA_PHASE_2_5_REPORT_v1_0.md`. `BA_AUDIT_FIX_PLAN_v1_0.md`
marked SUPERSEDED-AS-COMPLETE (v1.1). Handed back to the strategic track for the gate-check + 3-item
spot-check (J1 collisions→NULL, J3 no invented formula, J4 product-not-average) before scheduling the
deferred full Abhinandan rebuild.

---

## BA Pre-Rebuild Gate close — 2026-07-05

Ran the executor confirm-pass from `BA_PRE_REBUILD_GATE_REPORT_v1_0.md` (B2/B3/B4/B7/B8 + A1/A5/A2·J7/A2·J10
runtime checks), then `CLAUDECODE_BRIEF_BA_PRE_REBUILD_CLOSEOUT_v1_0.md` end to end.

**B2** migrations 405–413 confirmed live on prod (`_migrations_applied`, 2026-07-05 13:36 UTC). **A1/A5/A2·J7**
pytest 110/1-skip green; **A2·J10** assetClearSpec 16/16 green; **A5** `dag_edge_guard` live 91/91, zero HARD
violations. **B3/B4** found RED (not GREEN as the report's residual list left open): `amjis-mcp` was 88 commits
stale (path-gated deploy skip, no `platform-mcp/**` diff since the previous activity) — fixed via a full manual
`workflow_dispatch` redeploy; all four surfaces (web/sidecar/mcp/JOB) confirmed on merged HEAD (`76158638`).
**B7** on-demand prod snapshot of `amjis-postgres` taken. **B8** JL-013/JL-015 checked directly — no mismatch,
both correctly tag J4/`bo_cgm_paths`.

**A6** (LEL starvation) closed Path 1 (parser hardening only, zero LEL edit) across two follow-on PRs merged
in this pass:
- **#435** (merge `bd0d3756`) — raw-field fallback in `mi_jivanaghatana.py`: when a block's narrative fields
  (description/native_reflection/notes) break strict YAML with an unquoted colon, recover the event via only
  the fields this writer actually consumes (date/category/subcategory/magnitude), read as raw uninterpreted
  strings. Recovered 22 of 29 originally-failing blocks (the other 7 are legitimately non-event PATTERN.*/
  PERIOD.*/GAP.*/version-history blocks).
- **#436** (merge `6a0aea6f`) — found during the post-#435 A6 smoke test (not anticipated by the closeout
  brief): the #435 fallback only read the FIRST `EVT.*` key on a block, silently dropping the rest when a
  block groups more than one event under one ```yaml``` fence (7 blocks do this, one with 4 events) — 6 real
  events were being lost. Fixed by splitting on every top-level `EVT.*` boundary before extracting fields.
  Same PR also fixed a separate pre-existing bug (unrelated to A6): the illustrative `EVT.YYYY.MM.DD.XX`
  template/legend block was parsing successfully on its own (its bracket-placeholder values happen to be
  valid YAML) and leaking into `mimamsa_event_provenance` as a spurious event on every prior build.
- **Verified end state:** exactly 57/57 real distinct `EVT.*` events parse from the live LEL file, each with
  date + category present, zero missing, zero spurious.

Deploy-truth re-confirmed after each merge: web/sidecar/JOB all path-gate-triggered and rebuilt to the new
HEAD both times (`bd0d3756` then `6a0aea6f`); `amjis-mcp` correctly did NOT rebuild either time (no
`platform-mcp/**` diff) and was independently confirmed still on its already-current SHA, not merely
assumed unchanged.

**Secrets hygiene** (the one flagged non-blocker from the prior report): `amjis-sidecar`'s `DATABASE_URL` was
a plaintext Cloud Run env var while its sibling services referenced Secret Manager. Repointed to the same
`amjis-pipeline-db-url` secret the build-pipeline JOB already uses (`--update-secrets` + `--remove-env-vars`);
verified via an authenticated DB-touching endpoint (`phala/outlook/acceptance_gate/482012f1`) — identical
200 response before and after.

**Housekeeping:** `docs/ba-phase-2-5-report` and `fix/mi-jivanaghatana-multi-event-fallback` both confirmed
fully merged, then deleted (local + remote).

**REBUILD-READY: YES (unconditional).** Full report: `BA_PRE_REBUILD_CLOSEOUT_REPORT_v1_0.md`. Handed back to
the strategic track to issue the Phase-3 Abhinandan rebuild brief. No cockpit Build/Rebuild was run in this
pass.

---

## BA Phase-4 Runway — W1 (R2.2 Step 1: LEL schema) CLOSE — 2026-07-07

Executed `CLAUDECODE_BRIEF_BA_R4_WRAP_v1_0.md` W1 as conductor (this session HAS prod write + interactive native).

- **PR #457** (single R2.2 PR: migration 423 + LEL code surfaces + tests + JL-027 options doc) — branch
  brought current with main (#456 merged in), CI **10/10 pass** (Build, Governance incl. native-literal,
  TypeScript ×2, Unit, Planner, ICR, Naming, Coverage, Secret Scan), squash-**merged** → main `4d036ca9` @ 17:37Z.
- **Migration 423 deployed to prod** via surgical `psql -v ON_ERROR_STOP=1 -f` (NOT migrate.ts) — pre-deploy
  guard confirmed `life_events` empty (0 rows) so `SET NOT NULL` no-backfill/no-native-literal path held; COMMIT clean.
- **Post-deploy verify (independent — verifier subagent gates 3–6 + conductor gates 1–2,7–9), ALL PASS
  `[verify-against: prod db]`:** `life_events.chart_id` uuid NOT NULL; `recorded_at`/`pool_consent` NOT NULL +
  `contributed_to_pool_at` nullable; `(chart_id,event_id)` unique + old `event_id` unique dropped + index;
  `event_chart_state_index` scoped/re-keyed/indexed; `lel_query(uuid,text,date,date,int)` live and the
  chart-less signature GONE; `lel_query(482012f1)` & `lel_query(1c826d5a)` → total_count=0 + honest
  empty-with-reason (no error); `asset_registry.lel_events` = per_chart / has_writer=false / count_sql binds `$1`.
- Destructive-op clear-safety test present in suite and green in CI (Unit Tests gate).

**W1 EXIT: GREEN.** Next: W2 (first-intake 57 events @ 482012f1 with clear-safety proven vs prod schema FIRST;
LEL Steps 3–7; JL-027 ruling). Native checkpoint at this boundary; JL-027 ruling requested.

---

*RUN LEDGER v1.0 — initialized 2026-07-03 by CONDUCTOR (BA-AUTONOMOUS-RUN-2026-07-03)*
*Update at every gate. Do not edit substance of prior entries — append only.*
