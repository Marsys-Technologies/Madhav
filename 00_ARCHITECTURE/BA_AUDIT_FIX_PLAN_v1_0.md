---
artifact: BA_AUDIT_FIX_PLAN
type: audit_fix_plan
version: 1.0
status: CURRENT
authored_by: Claude (BA_FULL_ASSET_AUDIT)
date: 2026-07-05
---

# BA Audit Fix Plan (v1.0)

Prioritized remediation plan for the `BA_FULL_ASSET_AUDIT`. Consumes `BA_FULL_ASSET_AUDIT_REGISTER_v1_0.md` (91-asset findings register) and `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md` (DAG integrity + rebuild-readiness verdict).

**IMPORTANT — session-scope statement:** Nothing was rebuilt this session. No per-chart data was hand-patched. All work in scope was (a) source-code bug fixes to writers, (b) one registry/seed-script correction, and (c) one diagnostic instrumentation addition — all committed to git on branch `audit/ba-full-asset-audit`, none deployed or run against a live rebuild.

---

## BLOCKERS — confirmed, NOT YET fixed (must resolve before any full rebuild)

These are the 3 real HARD DAG edge-completeness violations from `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md §2.1` + §4. They are registry/migration changes, distinct in kind from the 4 findings that were in the Fix phase's scope this session, and remain fully open.

1. **`ka_taranga` missing `ka_sangam` in `depends_on`.**
   - Evidence: `ka_taranga.py:133` reads `kala_convergence` (ka_sangam's target table) without ka_sangam in its dependency closure.
   - Fix: `asset_registry` migration adding `ka_sangam` to `ka_taranga.depends_on`.
   - Blocks: L3 Kāla layer REBUILD-READY.

2. **`ka_yojaka` missing `bo_pratijna` in `depends_on`.**
   - Evidence: `ka_yojaka.py:67,81` reads `bodha_pratijna` inside a SAVEPOINT-guarded soft-dependency block, without bo_pratijna declared.
   - Fix: `asset_registry` migration adding `bo_pratijna` to `ka_yojaka.depends_on`.
   - Blocks: L3 Kāla layer REBUILD-READY.

3. **`mi_darshana` missing `bo_pratijna` in `depends_on`.**
   - Evidence: `mi_darshana.py:240,248,296` reads `bodha_pratijna` (cross-layer L2→L5) without bo_pratijna declared.
   - Fix: `asset_registry` migration adding `bo_pratijna` to `mi_darshana.depends_on`.
   - Blocks: L5 Mīmāṃsā layer REBUILD-READY.

**After all 3:** re-run `python -m pipeline.orchestrator.dag_edge_guard` to confirm exit 0. Only then is global REBUILD-READY = YES.

---

## Fixed this session (4 commits, branch `audit/ba-full-asset-audit`)

| # | asset | finding | commit SHA | what changed |
|---|---|---|---|---|
| 1 | `bg_text_index` | L3-Code BLOCKER — positional `fetchone()[0]`/tuple-unpack against a `dict_row` cursor, causing `KeyError` on every real run | `41225988` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_text_index.py` — replaced every `fetchone()[0]`/positional access (5 named sites + 1 additional vocabulary-load site of the same class) with dict-key lookups matching `ctx.db_conn`'s `dict_row` factory; fixed the silent-dict-key-iteration bug in the `chunk_id, content_en` unpack loop. |
| 2 | `bg_concordance` | L3-Code BLOCKER — identical `dict_row` bug pattern | `b9a495bf` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_concordance.py` — same class of fix for `topic_meta` construction and named `fetchone()[0]` reads, plus three more same-class positional-unpack loops further down (`group_rows`, `chunk_agg_rows`, `rule_rows`) and the final-count verification block that would have hit the identical bug immediately after the first fix. |
| 3 | `bg_rules` / `dasha_system_id` coverage gap | L6-Coverage MAJOR — P7 ('dasha_rule') pattern never fires against the live corpus, cause (never-matches vs. matched-but-filtered) unknown | `88d98a33` | `platform/python-sidecar/brahmagyan/l0_rules.py` — instrumented `extract_rules_from_chunk()` with `pattern_match_counts`/`pattern_yield_counts` (raw regex matches vs. post-dedup/threshold yields, per pattern name), wired through `seed_rules()`, added per-pattern log report + stats-dict exposure. Diagnostic only — does not change firing behavior; next rebuild will reveal root cause without guessing at regex changes. |
| 4 | `bg_remedies` `target_floor` drift | L1-Registry MAJOR — registry floor (800) far exceeds writer's true fixed-bucket design ceiling (266), and a stale seed script would silently re-drift any future reseed | `29ce08d0` | `platform/scripts/seed/asset_registry_seed.ts` + new migration `platform/supabase/migrations/405_bg_remedies_floor_recorrection.sql` — corrected the seed script's hardcoded `target_floor` (800→266) and stale "cross-text universe" comment; added migration 405 to re-correct the currently-drifted live value. Confirmed live count = 266 via `SELECT count(*) FROM brahma_remedy_corpus`. |

---

## MAJOR fast-follow (confirmed, not yet fixed, not session-blocking)

1. **`bg_reference` under target_floor (MINOR-leaning MAJOR by scope).** count_sql total = 1,242 vs target_floor = 1,485 (84%). Identify thin sub-table(s) — glossary (364) and topic_tags (481) are the largest, most likely under-seeded categories — and either backfill or correct the floor to the honestly-achieved count. `fix_type: seed`.

2. **11 non-blocking `depends_on` documentation-accuracy gaps** (`BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md §2.3`): `mi_kula`→`bg_class_priors` (the one reproducing prior-flagged example), `bo_pratijna`→`bg_ghatana`, `ka_yojaka`→`bg_ghatana`, `ka_avadhi`→`bg_ghatana`, `mi_pramana`→`bg_ghatana`+`bg_formula_constants`, `mi_jivanaghatana`→`bg_ghatana`, `ph_muhurta`→`bg_ghatana`, `mi_pariksha`→`bg_formula_constants`, `mi_gunanaka`→`bg_formula_constants`, `bo_upaya`→`bg_remedies`. All are L0-bedrock guard-exempted (not scheduling bugs) but violate the derivation-ledger spirit of CLAUDE.md §I B.3. Recommend one consolidated follow-up migration declaring all 11 edges. `fix_type: registry`.

3. **`dag_edge_guard.py` comment-stripping tooling defect.** `_reads()` should strip `#`-prefixed lines before regex-matching `FROM|JOIN` to eliminate the `ph_nimitta` class of false positive (confirmed not a real violation this pass, but will recur and mislead future audits until fixed). `fix_type: code`.

---

## MINOR / ENHANCEMENT backlog

1. **`bg_transit_engine` / `bg_nakshatra_medical` registry visibility (ENHANCEMENT).** Both are verified-clean, correctly-behaving sub-table/dual-@register exceptions — no functional issue — but the exception is only documented in writer docstrings + `runner.py`, not in `asset_registry` itself. Consider adding a `catalog_status`/comment column so the exception is visible from the registry without reading three separate files.

2. **No live-dict-row regression test added.** The `bg_text_index` finding suggested a regression test exercising writers against a real/live `psycopg` `dict_row` connection so this bug class can't silently land again. No existing test harness in the repo does this (`tests/test_ga3_writers.py`, `tests/l2/test_bo_a7_writers.py` checked — both use mocked/tuple cursors). Building one needs new DB test fixtures — flagged as a good follow-up but out of scope for a surgical fix-forward pass; not done this session.

---

## NATIVE_JUDGMENT_QUEUE

One finding this session requires native judgment before any code fix — a design decision, not a deterministic bug.

### `bg_rules` — `yoga_canonical_id` 0% populated (BLOCKER, L2-Data)

**Finding:** `sutravali_rules.yoga_canonical_id` is 0% populated across all 2,912 rows. The column is declared, FK-validated, and inserted by `l0_rules.py`, but no extraction pattern in the P1–P21+ dispatch table ever sets a real value — there is no yoga-detection pattern at all — and nothing downstream references the column (`grep yoga_canonical_id` hits only the writer itself).

**Options:**
- **(a) Implement a real yoga-detection extraction pattern.** Regex/name-match chunk text against `brahma_yoga_catalog.canonical_id`/name aliases so rules can genuinely cite the yoga they derive from. Requires domain decisions: which yoga aliases/catalog entries to match against, how to bound false-positive risk, and how the current corpus's English-translation phrasing should be matched. This is a substantive Jyotish-domain design choice, not a deterministic bug fix — guessing at a yoga-detection regex without acharya-grade review risks fabricating low-quality classical citations (forbidden by CLAUDE.md §L Do-Not list and §N.4/B.10 no-fabrication standard).
- **(b) Drop the column and its FK-validation dead code.** If yoga-linkage was descoped or never intended to be live, remove `yoga_canonical_id` from the dataclass, FK validation, and INSERT statement rather than leave a phantom citation field that silently starves any future consumer expecting it to be populated.

**Recommendation:** Lean toward (a) if yoga-citation is part of the acharya-grade quality bar this project targets (§J) — sutravali_rules is meant to ground classical rule citations, and yoga-based rules are a core Jyotish technique, so a permanently-null column here is a real coverage gap, not cosmetic. But this should not be built without native sign-off on which yoga catalog entries/aliases are safe to match deterministically and what the acceptable false-positive tolerance is. If native judgment instead concludes yoga-linkage is not a near-term priority, (b) is the lower-risk immediate action — it removes dead code and an actively misleading always-null column, and can be revisited later without loss (the FK-validation and INSERT plumbing can be re-added when a genuine pattern is designed).

**Status:** OPEN — awaiting native decision. Not fixed this session per the Fix agent's explicit judgment call to flag rather than guess.

---

## Summary

- **BLOCKERS still open:** 3 DAG `depends_on` gaps (ka_taranga/ka_sangam, ka_yojaka/bo_pratijna, mi_darshana/bo_pratijna) + 1 native-judgment item (bg_rules/yoga_canonical_id). Global REBUILD-READY = **NO** until the 3 DAG gaps are fixed; L3 and L5 layers specifically blocked.
- **BLOCKERS fixed this session:** 2 of the original 4 code-level BLOCKERS (bg_text_index, bg_concordance) — both dict_row `KeyError` bugs that would have halted their writers on every real rebuild attempt.
- **MAJOR fixed this session:** 1 of 2 (bg_remedies floor correction). bg_rules/dasha_system_id got diagnostic instrumentation (not a behavior fix) — root cause still to be determined from next rebuild's logs.
- **Nothing was rebuilt. No per-chart data was hand-patched.** All 4 fixes are source/config changes committed to git; none have been exercised against a live orchestrator run yet. The 3 DAG-edge BLOCKERs and the yoga_canonical_id native-judgment item remain fully open and must be resolved (the former) or decided (the latter) before the native authorizes a full six-layer rebuild.
