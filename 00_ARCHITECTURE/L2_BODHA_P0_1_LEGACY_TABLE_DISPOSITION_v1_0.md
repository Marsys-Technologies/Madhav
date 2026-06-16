---
artifact: L2_BODHA_P0_1_LEGACY_TABLE_DISPOSITION_v1_0.md
canonical_id: L2_BODHA_P0_1_LEGACY_TABLE_DISPOSITION
version: 1.0
status: CURRENT
authored_by: Claude Code (Cowork) 2026-06-12
authored_for: the native — the "report before you drop both" deliverable requested at the Phase-0 decision gate
supersedes_assumption_in:
  - 00_ARCHITECTURE/L2_BODHA_PHASE0_GAP_REPORT_v1_0.md §6 item 1 (the "DROP both" recommendation)
purpose: >
  The native, at the Phase-0 §6 decision gate, did NOT approve the gap report's "DROP both
  legacy bodha_* and l25_*" recommendation. The native's exact instruction: "The table naming
  nomenclature has been standardized across all phases … please check the memory or give me a
  report before you drop both." This is that report. It (a) distinguishes the TWO senses of
  "standardization" so the right thing is preserved, (b) corrects three material code-plane
  errors in the gap report, (c) gives a differentiated, per-table disposition, and (d) lists the
  exact residual prod checks that remain operator-only.
verdict: DO NOT BLIND-DROP. Differentiated disposition; one legacy table has a LIVE reader.
read_in_combination_with:
  - 00_ARCHITECTURE/L2_BODHA_PHASE0_GAP_REPORT_v1_0.md
  - 00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md
  - 00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md
---

# L2 Bodha — P0.1 Legacy-Table Disposition Report v1.0

## §0 — Verdict (read this first)

**The gap report's "DROP both sets" recommendation is REJECTED as written. A blind DROP would
have broken a live production route.** The disposition is **differentiated, not uniform**, and one
hard fact gates everything:

> `platform/src/app/api/chat/consult/route.ts:22` runs a **live runtime SQL query** against the
> legacy table: `SELECT signal_id, signal_name AS name, signal_text AS description FROM
> bodha_signals WHERE signal_id IN (...)`. This is inside the **chat consultation API**. Dropping
> `bodha_signals` now would throw at runtime in the consult path.

This is exactly the `[[feedback-destructive-brief-reverse-citation-gate]]` failure the native's
caution was protecting against. The audit's V3 grep was the right gate; the audit's *conclusion*
(that it would come back clean) was wrong.

---

## §1 — The native's point is correct: two DIFFERENT senses of "standardization"

The native said the table nomenclature is "standardized across all phases (L0 Brahmagyan, L1
Gaṇita, planned L2 Bodha)." That is true — but it refers to a different axis than the one the
gap report proposed to demolish. Separating them is the whole job of this report.

| Sense | What is standardized | Status | Does the Phase-0 plan preserve it? |
|---|---|---|---|
| **(A) Asset-id + writer-contract + fact-grammar** | `bg_*`/`ga_*`/`bo_*` underscore ids (migration 224); the FROZEN `WriterBase` contract; the canonical **fact-row grammar** of `chart_facts` (`fact_id · chart_id · ayanamsha_id · build_id · fact_category · fact_subject · fact_key · fact_value_* · citation_ref · citation_human · source_calculation · verification_pass_status · engine_version · computed_at`, UNIQUE on chart×ayanamsha×cat×subj×key×build) | **REAL, LOCKED, cross-layer** | **YES — fully preserved.** The plan keeps the `bo_*` ids, the WriterBase contract, and builds the LOCKED A10–A14 spec tables *to the same fact-grammar discipline*. This standardization is the thing we are *completing* for L2, not destroying. |
| **(B) Legacy table column-shapes** | The Wave-1 hand-authored `bodha_signals` shape (`signal_text`, `claim_text`, fused `confidence`/`salience`, `grounding_status`) | **NON-standard — predates the L1 grammar** | The legacy `bodha_signals` does **NOT** follow the `chart_facts` grammar. It is the contaminated shape the `MSR_UCN_CONTAMINATION_AUDIT` flagged. So sense-(B) was never the standard to protect. |

**Bottom line of §1:** What the native rightly wants protected (sense A) is preserved by the
plan. What the gap report wanted to drop (sense B) is the *pre-standard* shape. The two are not
the same thing — and conflating them is precisely why a "report before drop" was the right call.

---

## §2 — Three material errors in the gap report, corrected against the repo + memory

| Gap report claim | Reality (verified) | Evidence |
|---|---|---|
| **C3:** `l25_*` stubs are "from migration 206," "coarse 12-col placeholders, created-but-empty" | `l25_*` tables were created by **migration 137** (`platform/migrations/137_l25_tables.sql`, session A3-S4, 2026-05-29), and were **"verified present in amjis database (14 total l25_* tables now)"** — i.e. live in prod, and the audit's "6 empty stubs" undercounts a **14-table family**. Migration 206 in the repo is `ga3_supporting_tables` — unrelated. | repo `ls platform/supabase/migrations/`; memory obs #5647 |
| **P0.1:** the two table-sets can both be DROPped after a clean reverse-citation grep | `bodha_signals` has a **live runtime reader** in the consult API (above). The grep does **not** come back clean. | `consult/route.ts:22` |
| **Implicit:** legacy `bodha_*` and `l25_*` are the only two representations to reconcile | Correct that the spec-grade tables exist nowhere; but the `l25_*` family (14 tables) is the **larger** live representation, and the two live families (`bodha_*` baseline + `l25_*`) are in **two different migration trees** (`platform/supabase/migrations/` vs `platform/migrations/`). The reconciliation is genuinely three-way, but the shapes/locations differ from the audit's account. | both migration dirs |

---

## §3 — Differentiated per-table disposition (the actual recommendation)

### §3.1 — Legacy `bodha_*` (9 tables, `platform/supabase/migrations/0001_brahma_baseline.sql`)

| Table | Live reader? | Recommended disposition | Why |
|---|---|---|---|
| `bodha_signals` | **YES** — `consult/route.ts:22` (runtime SQL); plus 3 TODO/spec citations (`multi_school_signal_lookup.ts`, `classical_attribution_lookup.ts`, `retrieval_capability_spec.ts:569`) and a test fixture (`scope_filter.test.ts`) | **KEEP-UNTIL-REPOINTED.** Do not DROP. The `bo_laksana` spec writer produces `bodha_msr_signals`; the consult route must be repointed to read the new spec table (or a compat view `bodha_signals` over it) *before* the legacy table is retired. Retirement is a **later** step, gated on the repoint. | breaking the consult API is a production regression |
| `bodha_graph`, `bodha_graph_edges`, `bodha_graph_staging`, `bodha_domain_links`, `bodha_remediation`, `bodha_remediation_staging`, `bodha_resonance`, `bodha_signal_embeddings` (8) | **NO live reader** found in `platform/src` / `platform/platform-mcp` | **DROP-ELIGIBLE, prod-gated.** Eligible to drop *after* V1/V2 confirm they hold no native data worth keeping. Rebuild spec-grade under the campaign §3.2 names. | no live citation; Wave-1 shape superseded by spec |

### §3.2 — `l25_*` (14 tables, `platform/migrations/137_l25_tables.sql` + predecessors)

- **No live reader found** for any `l25_*` name in `platform/src` / `platform/platform-mcp`.
- **DROP-ELIGIBLE, prod-gated** on V1 (row counts) + a `l25_`-name reverse grep widened to
  `.py` writers. These are the older synthesis representation that the LOCKED A10–A14 spec
  supersedes wholesale. If V1 shows them empty (or only stale non-native rows), drop the family.
- **Caveat:** they were "verified present" in May; emptiness was never asserted. **V1 is mandatory
  before any l25 DROP.**

### §3.3 — Net

**Nobody drops anything in this session.** Disposition = (1) **repoint** the one live reader off
`bodha_signals`; (2) **prod-verify** (V1/V2) the 8 unreferenced legacy `bodha_*` + the 14 `l25_*`;
(3) DROP only the verified-safe, unreferenced tables, table-by-table, in the P0.1 migration brief —
*after* the spec tables exist and the repoint has shipped. This is the brownfield order the gap
report’s §4 implied but its §6 recommendation skipped.

---

## §4 — Residual operator-only checks (code-plane is exhausted; these need the Cloud SQL proxy)

The code-plane reverse-citation gate is now **fully discharged** (this report did V3, and refined
it). What remains is data-plane truth, which Cowork cannot reach:

| ID | Verifies | Query | Gates |
|---|---|---|---|
| V1′ | Row counts for all live `bodha_*` + `l25_*` (corrected: include the 14 l25_*) | `SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE relname LIKE 'bodha\_%' OR relname LIKE 'l25\_%' ORDER BY relname;` | every DROP |
| V2′ | Do any hold **native** (`482012f1-…`) data that DROP would lose? | per-table `SELECT count(*) … WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'` | every DROP |
| V3-py | Widen reverse-citation to python writers/SQL strings (`FROM l25_`, `INTO l25_`, `bodha_resonance` etc. in `platform/python-sidecar`) | code-plane grep — **run before l25 DROP** | l25 DROP |

V3-py is code-plane and *can* be run now; I did the `platform/src` pass. The python-sidecar pass
should be re-run cleanly inside the P0.1 brief (my one-shot grep hit a zsh glob error and is not
authoritative).

---

## §5 — What this unblocks

- **P0.1 reconciliation brief** can now be authored with a *correct* disposition: build spec-grade
  `bodha_*` tables fresh; **repoint** `consult/route.ts` off legacy `bodha_signals`; DROP only the
  verified-unreferenced legacy + `l25_*` tables, prod-gated, table-by-table.
- The native’s sense-(A) standardization is explicitly preserved and documented, so no future
  session re-opens this.

---

*End of L2_BODHA_P0_1_LEGACY_TABLE_DISPOSITION_v1_0. Bottom line for the native: you were right to
stop the drop. One legacy table (`bodha_signals`) is read live by the consult API and must be
repointed, not dropped; the `l25_*` family is bigger and older than the audit said (migration 137,
14 tables, live in prod) and needs a real row-count check first. Recommended path: repoint → prod-
verify → table-by-table DROP of only the verified-safe tables, inside the P0.1 brief. Nothing is
dropped blind.*
