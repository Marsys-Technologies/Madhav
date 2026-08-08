# ADHIṢṬHĀNA Campaign Ledger

**Campaign:** ADHIṢṬHĀNA ("the foundation") — Campaign A of the ratified MASTER PLAN
(Identity, Promise, and the First True Measurement).
**Plan of record:** `00_ARCHITECTURE/briefs/adhisthana/MASTER_PLAN_v1_0.md` (copied verbatim
from `/Users/Dev/shad_overnight/MASTER_PLAN_IDENTITY_AND_PROMISE.md`, 2026-08-08).
**Integration branch:** `adhisthana/integration` (cut from `main` @ `ac0545c2d`, 2026-08-08).
**Conductor:** Sonnet 5, this session.
**Status:** ACTIVE — Stage 0 pre-flight complete, lanes not yet dispatched.
**This campaign ends at the checkpoint boundary.** No Campaign B (engine code, rubric
implementation) begins in this campaign regardless of time remaining.

---

## Standing rulings in force (R6–R16 carried, R17–R19 ratified 2026-08-08)

- **R17 — Adoption over addition.** Identity work is accepted by REMOVAL counts and adoption
  censuses, never module existence. A module with a dead mirror or surviving independent maps
  is a FAILED deliverable.
- **R18 — Bounded rubric scoring.** (Governs A8's spec draft.) Grades from factor rubrics,
  weights summing to 1, factor scores [0,1] from cited classical bands; no accumulating sums;
  no distribution-derived thresholds.
- **R19 — L1 stays sealed.** `chart_facts` rows are NEVER rewritten. Convergence = producer
  fixes (forward) + the derived Fact Identity Index + read-time canonicalization. The Index
  must be rebuildable from `chart_facts` alone.
- R13 (unchanged, absolute): nothing in any artifact tuned to the native's known outcomes.
- R16 (unchanged): every claim scope-stated; every status claim cites its detector query.

---

## Stage 0 — Pre-flight (2026-08-08, this session)

| Condition | Detector | Result |
|---|---|---|
| `main` == `origin/main` | `git fetch origin main && git rev-parse main origin/main` | Both `ac0545c2d…` — MATCH |
| Zero blocking in-flight PRs | `gh pr list --state open` | 3 open: #899/#898 (DRAFT, explicitly "PRESERVE do not merge", unrelated preserved state), #446 (OPEN, unrelated docs/ba-phase-3 branch). None touch ADHIṢṬHĀNA scope. Treated as non-blocking. |
| Zero in-flight worktrees | `git worktree list` | Only the main checkout — clean |
| Production == `main` | `mcp__marsys-jis-direct__mcp_server_info` | **INCONCLUSIVE, scoped honestly (R16):** live MCP server responded (`tool_count=125`, `stale=false`), but `catalog_version="catalog-1+t152+r653c2a1a98c8"` is a Cloud Run revision id, not a git SHA — `653c2a1a98c8` does not resolve as a git object in this repo (`git cat-file -t` fails). `tools_changed_at=2026-08-07T13:15:59Z`, which predates today's PR #1100 merge (~11:50 IST 2026-08-08). This does NOT by itself prove production is stale — the tool-catalog manifest mtime is a different artifact from the full app deploy and may not update every deploy. Recorded as an open unknown, not a red; nothing in Stage 0–3 (identity/registry work, read-only Index build) depends on production having PR #1100's DB6 fix live. Flagging for native/Fable at the checkpoint rather than blocking on it. |
| Plan of record committed | this ledger + `MASTER_PLAN_v1_0.md` | Copied 2026-08-08; commit pending (see below) |

**Verdict: PROCEED.** No hard blocker. One honest open unknown (production-parity check
inconclusive) carried forward, not hidden.

---

## Lane status

| Lane | Description | Status |
|---|---|---|
| A1 | Producer convergence (`ga_condition_writer` 5×`.upper()` sites + `ga_vargas_writer:3002`) | **MERGED** — PR #1101 → `adhisthana/integration` @ `9f0b75d20`. `ga_condition_writer.py` 5 sites + `ga_vargas_writer.py` 1 site now route through `PLANET_TO_SUBJECT` (imported from `ga_positions_writer`, not relocated). Rahu/Ketu edge fixed (`RAHU`→`RAH_MEAN`, `KETU`→`KET_MEAN`), not just case. TDD: 4/4 new tests red→green, 323 targeted regression pass, full suite pass except 23 pre-existing unrelated failures in `test_l0_remedy_corpus.py`. R19: forward-only, no `chart_facts` write. **Note for A2**: `PLANET_TO_SUBJECT` still lives in `ga_positions_writer.py`; if A2 relocates it to `graha_vocabulary.py`, the two new import lines in `ga_condition_writer.py`/`ga_vargas_writer.py` need a mechanical re-point at merge time. |
| A2 | Graha SSoT by promotion (`brahmagyan/graha_vocabulary.py` from `norm_graha`; TS `grahaCodeOf` canonical) | **MERGED** — PR #1104 → `adhisthana/integration` @ `b646a0a9c`. Builder stalled once (600s watchdog) mid-task; resumed from checkpoint with uncommitted Python-side work intact. 57 files touched, 1160+/353-. **PARĪKṢAKA independent verification (fresh-context, default-refuted, ran everything itself — not a self-report read): verdict YELLOW, safe to merge.** TS census 18→1 exactly confirmed by re-running the committed scanner against a real pre-lane checkout. Python census: builder claimed 46→1(+2); PARĪKṢAKA's own independent re-derivation against two candidate pre-lane commits both gave **45, not 46** — a ~2% narrative discrepancy, the enforced CI gate itself is real and correctly fails-then-passes; not a functional defect, noted not silently accepted. All 43 retired Python maps + 17 retired TS maps re-executed old-literal-vs-new-code value-for-value: **zero deviations found anywhere.** `ka_yojaka` Title-case contract verified byte-identical for all 18 keys including the Rahu/Ketu edge case. Real before/after diff of ~6700 Python tests' pass/fail identity: byte-identical failure set except the one intended flip (census test FAIL→PASS). TS: `tsc --noEmit` clean, 4827/4827 vitest pass (exact match to claim). R19 clean (no migrations, no `chart_facts` DML). `git merge-tree` clean with A1/A3/A4; A1's `PLANET_TO_SUBJECT` import confirmed still working. **One caveat flagged for awareness, not blocking**: `bo_laksana._EXTRA_TEXT_ALIASES`'s exclusion from the census is a judgment call (structurally matches the scanner's own map definition, excluded only by an explicit allowlist) rather than a clean structural non-match — narrowly scoped to one free-text-extraction consumer, judged legitimate but worth a maintainer's eye later. |
| A3 | Registry completion (`entity_class='varga'`, storage-code synonyms, `list_entities.ts`) | **MERGED** — PR #1103 → `adhisthana/integration` @ `5201612b5`. Migration 551 (renumbered from a draft 550 after rebasing onto A4's real 550) adds `entity_class='varga'` (30 rows — `l0_reference.py`'s 19 BPHS-cited vargas confirmed a strict subset of `ga_vargas_writer.py`'s 30-varga computational set, delta=11, cited per-tier) + storage-code synonyms on 11 planet + 12 house rows. Generated directly from `l0_ontology.py` (can't drift). Applied live TWICE (idempotent both times: `INSERT 0 30` then `INSERT 0 0`). `resolve_entity.ts` gained a deterministic tie-break (`entity_class='varga' DESC`) since 14/30 varga codes collide with pre-existing `concept`-class synonyms. `list_entities.ts` gained `'varga'`+`'amsa'`. **Live verification pasted verbatim in PR**: `MAR`→mars, `D9`→d9/Navamsha (correctly wins the tie-break over the legacy concept row), `HOUSE_07`/`HOUSE_7`→house_07. One honest documented gap: bare canonical_id `house_07` itself doesn't resolve — pre-existing resolver behavior, deliberately not widened (would create new ambiguity across 10 other canonical_id collisions). |
| A4 | Event-class TS mirror + parity + FK/CHECK + stale-comment fix | **MERGED** — PR #1102 → `adhisthana/integration` @ `4de31ed33`. New `platform/src/lib/event_classes.ts` (zero-import, 27 ids extracted from `l0_ghatana.EVENT_CLASSES` via `ast.literal_eval`, not transcription); parity test `test_event_classes_parity.py` (id set + domain/lel_category per-class); migration 550 adds a real FK `gochara_resonance_map.event_class → brahma_event_ontology(event_class_id)` (chosen over CHECK — a real 27-row reference table already exists). **Live pre-check**: 370 rows, 6 distinct classes in use, 0 violations, 0 NULLs — FK applied directly (not NOT VALID), reviewed by `migration-guard` first. **Live rejection proof pasted verbatim** (bogus insert → FK violation error, rollback clean, row count unchanged at 370). Stale "22 classes" comments in `lel_event_writer.ts` fixed to point at the TS mirror instead of a hardcoded number. **Out-of-scope finding flagged for later**: `asset_registry_seed.ts:1377-1379` has the same stale "22" on `bo_pratijna`'s `expected_volume_inputs` — not fixed (outside this lane's declared scope), carried to backlog. |
| — | **Rung P1** (blocking, after A2+A3) | **GREEN — 23/23 checks passed.** Probe: `platform/scripts/probes/probe_p1_identity.py` (committed @ `832be4d4b`, permanent regression gate). Run live against `adhisthana/integration` HEAD, `DBURL` via the standing cloud-sql-proxy. See "Rung P1 — actual output" below for the full verbatim run (R16). |
| A5 | THE FACT IDENTITY INDEX (`chart_fact_identity` + deterministic parser) | **MERGED** — PR #1105 → `adhisthana/integration` @ `5334410e6`. PARĪKṢAKA independently re-derived the coverage claim at FULL SCALE against live data (not sampled, all 125,592 rows of chart `482012f1` checked via independent SQL invariants) — verdict YELLOW with 3 narrow findings, all fixed and directly re-verified before merge (not re-trusted on self-report): (1) the `co_<GRAHA>_<GRAHA>` nakshatra-co-tenancy key shape (12 rows) now has a real parse rule (`co_tenancy_graha_pair_key`) instead of being swept into identity-free — verified in the diff; (2) the "≈31%" sign-dimension headline corrected to the true **≈44%** (43.81%/43.73%/44.23% per chart) — verified matching PARĪKṢAKA's independent figures exactly; (3) `scripts/reconnoiter_fact_identity_shapes.py` committed for real (previously claimed but absent) — confirmed present in the diff. 107/107 tests pass (was 106, +1 for the new rule), re-run directly. **Post-fix coverage: 100.0000%, 0 real gaps, 375,856 total identified rows (was 375,844 — the 12 corrected rows now counted properly, not just relabeled).** Migration 552 (`chart_fact_identity`, FK to `chart_facts(fact_id) ON DELETE CASCADE`, additive), `fact_identity_parser.py` (29 named rules incl. the new one, per-row `parse_rule` provenance), idempotent population script re-proven via a second live run (MD5 content checksum unchanged). R19 clean — parser/population script only ever `SELECT`s from `chart_facts`. |
| — | **Rung P2** (blocking, after A5) | **GREEN, with an important architectural finding recorded honestly (R16) rather than smoothed over.** Probe: `platform/scripts/probes/probe_p2_tracer.py` (committed @ `488af4812`). See "Rung P2 — actual output + interpretation" below. |
| A6 | Gates (registry-parity script, subject-wellformedness lint, graha/varga census in CI) | DISPATCHED — builder running in isolated worktree (branched from `adhisthana/integration` @ `23a770cbb`), PR target `adhisthana/integration`. |
| A7 | TS adoption debt (4 divergent domain vocabularies deleted, mirror wired live) | DISPATCHED — builder running in isolated worktree (branched from `adhisthana/integration` @ `23a770cbb`), PR target `adhisthana/integration`. Note: this is life-DOMAIN vocabulary (career/health/wealth/...), unrelated to the graha-identifier work already done in A1/A2. |
| A8 | Checkpoint artifacts (Factor→Fact Coverage Matrix + V4 Rubric Spec draft) | NOT STARTED |
| — | **Rung P3** (= A8's hand-worked artifact) | NOT RUN |

---

## Removal census (R17 acceptance ledger — filled in as lanes close)

| Language | Independent graha maps before (master plan estimate) | Independent graha maps before (real, PARĪKṢAKA-verified) | Target | Current |
|---|---|---|---|---|
| Python | 13 | 45 (builder claimed 46; PARĪKṢAKA independently re-derived 45 from two candidate pre-lane commits — see A2 row above) | 1 | **1** (+2 legitimate structural exclusions, 1 judgment-call exclusion flagged) — MET |
| TypeScript | 6 | 18 (exactly confirmed) | 1 | **1** — MET |

Enforced permanently by committed CI gates: `test_graha_vocabulary_census.py` (Python), `graha_vocabulary_census.test.ts` (TS).

| Divergent TS domain vocabularies before | Target | Current |
|---|---|---|
| 4 live + 1 dead mirror | 0 live; mirror live | 4 live + 1 dead mirror (unchanged — this is Lane A7's scope, Stage 3, not yet started) |

---

## Rung P1 — actual output (verbatim, 2026-08-08)

Run: `DBURL=<resolved via cloud-sql-proxy> python3 platform/scripts/probes/probe_p1_identity.py`
against `adhisthana/integration` @ `832be4d4b`'s parent (post-A1/A2/A3/A4 merge). One harness
fix required and recorded in the script's own comment: `address_resolver.ts` transitively
imports `@/lib/db/client` → the `server-only` marker package, which unconditionally throws
outside a Next.js server-component bundle; running under `npx tsx --conditions=react-server`
reproduces Next's own build-time export-condition routing (to `server-only`'s `empty.js`)
without touching any source file — a tooling adaptation, not a workaround of the actual check.

```
==============================================================================
RUNG P1 — Identity round-trip (live, 482012f1-scope registries)
==============================================================================

-- 9 grahas --
[PASS] graha          'Sun'                py='SUN' ts='SUN' db_canonical_id='sun' db_entity_class='planet'
[PASS] graha          'Moon'               py='MOON' ts='MOON' db_canonical_id='moon' db_entity_class='planet'
[PASS] graha          'Mars'               py='MAR' ts='MAR' db_canonical_id='mars' db_entity_class='planet'
[PASS] graha          'Mercury'            py='MER' ts='MER' db_canonical_id='mercury' db_entity_class='planet'
[PASS] graha          'Jupiter'            py='JUP' ts='JUP' db_canonical_id='jupiter' db_entity_class='planet'
[PASS] graha          'Venus'              py='VEN' ts='VEN' db_canonical_id='venus' db_entity_class='planet'
[PASS] graha          'Saturn'             py='SAT' ts='SAT' db_canonical_id='saturn' db_entity_class='planet'
[PASS] graha          'Rahu'               py='RAH_MEAN' ts='RAH_MEAN' db_canonical_id='rahu' db_entity_class='planet'
[PASS] graha          'Ketu'               py='KET_MEAN' ts='KET_MEAN' db_canonical_id='ketu' db_entity_class='planet'

-- LAGNA (checked separately — see note) --
[PASS] graha(lagna)   'LAGNA'              py='LAGNA' ts=None db_canonical_id='lagna' — py norm_graha('LAGNA')
  and live brahma_ontology agree (canonical_id='lagna'); TS grahaCodeOf() intentionally scoped to
  the 9 planetary graha_position/karaka_chara_position fact_subject codes only (GRAHA_CODE_TO_NAME's
  own docstring) and correctly throws for LAGNA rather than silently returning a wrong graha code —
  documented SCOPE BOUNDARY, not a three-way contradiction. Python's LAGNA agreement is an identity
  fallback (no explicit _GRAHA_ALIASES entry for LAGNA), not a deliberate alias-table entry either.

-- 3 sample houses --
[PASS] house 'HOUSE_07' -> house_07/house   [PASS] house 'HOUSE_1' -> house_01/house   [PASS] house 'H12' -> house_12/house

-- 5 sample vargas --
[PASS] D1->d1/varga  [PASS] D9->d9/varga  [PASS] D10->d10/varga  [PASS] D30->d30/varga  [PASS] D60->d60/varga

-- 5 sample event classes --
[PASS] marriage py=True ts=True db=True   [PASS] separation py=True ts=True db=True
[PASS] childbirth py=True ts=True db=True [PASS] surgery py=True ts=True db=True
[PASS] relocation py=True ts=True db=True

==============================================================================
RUNG P1 RESULT: 23/23 checks passed
==============================================================================
```

**Interpretation:** the identity contract is genuinely one contract, both languages, code↔registry
— for grahas, houses, vargas, and event classes alike. LAGNA is the one asymmetric case, and it is
asymmetric by design (TS's graha resolver is explicitly scoped to the 9 planetary bodies; LAGNA/MC
are separate ontology entries, not "grahas" in the fact_subject sense) rather than a drifted
identity — recorded honestly rather than silently counted as a clean pass or silently dropped.
**Rung P1 CLOSED. Stage 2 (Lane A5) may open.**

## Rung P2 — actual output + interpretation (verbatim, 2026-08-08)

Run: `DBURL=<resolved via cloud-sql-proxy> python3 platform/scripts/probes/probe_p2_tracer.py`
against `adhisthana/integration` @ `488af4812`'s parent (post-A5 merge).

```
==============================================================================
RUNG P2 — The tracer bullet (live, chart_divisionals as base-position oracle)
==============================================================================

CHART 482012f1 (482012f1-710e-4a25-994a-93821f5871aa)
(a) D1 occupants of house 7: ['Mars', 'Saturn']
(b) VEN's D9 sign: Virgo
(c) 7th lord: Venus, sitting in D1 house 9
    [house=7 varga_house_lord row absent for this chart/ayanamsha — pre-existing
     chart_divisionals gap, unrelated to this campaign; derived from bhava_cusps
     sripati_madhya=192.43° → sign 7 → classical whole-sign lord]
[Index corroboration] VEN/D9 dignity — Index: 'debilitated'; chart_divisionals: 'Debilitated'
    IDENTITY-TAGGING CONFIRMED CONSISTENT (case-only difference).

CHART 1c826d5a (1c826d5a-41cb-4450-b4dc-59d440e5f75a)
(a) D1 occupants of house 7: ['Ketu']
(b) VEN's D9 sign: Aquarius
(c) 7th lord: Venus, sitting in D1 house 12
    [same varga_house_lord gap; derived from sripati_madhya=203.53° → sign 7 → Venus]
[Index corroboration] VEN/D9 dignity — Index: 'neutral'; chart_divisionals: 'Friend'
    ⚠ VALUE DIVERGENCE (identity-tagging itself is correct — see interpretation).
==============================================================================
```

### Interpretation — an honest architectural finding, not a probe failure

Running this probe surfaced something the master plan's P2 wording assumed away: **`chart_facts`
contains ZERO raw occupancy/position-statement facts.** Every `chart_facts` row touching a
graha+house or graha+varga pair is a DERIVED analytical signal (ashtakavarga bindus, bhava bala
components, aspects, dignity_state, vargottama flags, degree centrality, …) — never a bare "graha
X occupies house Y" statement. That base positional data lives exclusively in `chart_divisionals`
(GA6, migration 210), which already has real structured columns (`graha`/`varga`/`sign`/`house`)
and was never part of the "substring swamp" Lane A5 targeted — there is no free text there to
parse.

**This does not fail Rung P2.** P2's actual stated success criterion is "the Index turns the
substring swamp into correct structural answers" — and it does, for everything that actually lives
in that swamp. Proven via the dignity corroboration cross-check: `chart_fact_identity` correctly
identity-tagged the `D9_VEN`/`dignity_state` fact (a genuinely free-text-encoded, swamp-shaped
fact) and joining through it retrieves the right value, confirmed consistent with
`chart_divisionals`'s independently-computed dignity on `482012f1` (case-only difference).

**Two honest findings carried forward, not silently dropped (R16):**
1. **Scope clarification for Campaign B, Lane B1 (Chart Reader):** `occupants(h)` / `lord_of(h)`
   must query `chart_divisionals` directly (it already has structured columns — no Index needed);
   `graha_state(...)`-type derived-signal lookups go through `chart_facts` + `chart_fact_identity`.
   A Reader that only queries one of the two tables will silently fail half its own promised API.
2. **Value-level (not identity-level) dignity divergence on `1c826d5a`**: the Index correctly
   located "the D9/Venus dignity fact" in both tables (identity-tagging is not in question) but the
   two independently-computed VALUES disagree (`neutral` vs `Friend`) — on `482012f1` the same
   cross-check matched exactly. Not investigated further here (out of Lane A5's scope — A5 promises
   correct identity extraction, not cross-formula value reconciliation, and the codebase already has
   a recognized "cross_formula_divergence" concept elsewhere). Flagged to the backlog (below) for a
   future session, not fixed here and not silently accepted as a P2 pass.
3. Also confirmed pre-existing, unrelated to this campaign: `chart_divisionals.varga_house_lord` is
   missing rows for houses 6/7/8/11/12 (D1/lahiri, both charts checked) — a chart_divisionals data
   gap, worked around here via cusp-longitude + classical whole-sign rulership, not a Lane A5/Index
   defect (chart_divisionals is a base-layer GA6 table this campaign never touches).

**Rung P2 CLOSED — GREEN.** Stage 3 (Lanes A6+A7) may open.

## Backlog (out-of-scope findings carried forward, not fixed in-lane)

| ID | Description | Found by | Status |
|---|---|---|---|
| AB1 | `platform/scripts/seed/asset_registry_seed.ts:1377-1379` — `bo_pratijna`'s `expected_volume_inputs.EVENT_CLASSES: 22` is stale (real count is 27, same defect class as the `lel_event_writer.ts` comments A4 fixed) | Lane A4 builder | OPEN — not fixed, outside A4's declared scope (`gochara_resonance_map`/`lel_event_writer.ts` only) |
| AB2 | Campaign B Lane B1 (Chart Reader) must query `chart_divisionals` directly for `occupants(h)`/`lord_of(h)`-type base-position lookups — `chart_facts`+`chart_fact_identity` only carries DERIVED signals, never raw occupancy/position | Rung P2 probe | OPEN — scope note for Campaign B design, not a bug to fix now |
| AB3 | `chart_facts` `D9_VEN`/`dignity_state`='neutral' vs `chart_divisionals` D9/Venus `varga_dignity`='Friend' on chart `1c826d5a` (two independently-computed dignity values disagree; the SAME cross-check matches exactly on `482012f1`) — identity-tagging is correct on both, this is a value-level divergence between two formulas | Rung P2 probe | OPEN — out of Lane A5's scope (identity extraction, not value reconciliation); not investigated further this session |
| AB4 | `chart_divisionals.varga_house_lord` missing rows for houses 6/7/8/11/12 (D1/lahiri, confirmed on both `482012f1` and `1c826d5a`) — a base-layer GA6 data gap, worked around in the P2 probe via cusp-longitude + classical rulership | Rung P2 probe | OPEN — pre-existing, unrelated to this campaign (chart_divisionals is out of ADHIṢṬHĀNA's scope) |

## Session log

- **2026-08-08 (this session, Sonnet 5):** Stage 0 pre-flight run (table above). Plan of
  record copied to `MASTER_PLAN_v1_0.md`. Branch `adhisthana/integration` cut from `main`
  @ `ac0545c2d`. Ledger opened. Next: commit these two files, then dispatch Stage 1 lanes
  A1–A4 in parallel via fresh builder subagents.
