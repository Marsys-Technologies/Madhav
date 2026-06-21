# L1 Enrichment v2.0 — Pre-PR Review (paste into Claude Code / Antigravity)

**Context:** L1 Enrichment Amendments v2.0 are committed on `feature/l1-phase3-enrichment` @ `7ce339d4`
(per `L1_ENRICHMENT_AMENDMENTS_v2_0.md`): Amendment 1 ga_strength (per-varga Ashtakavarga + positional
components), Amendment 2 ga_condition (per-varga Baladi/Deeptadi avastha), Amendment 3 ga_sensitive (5 builders).
80 new tests, 378 passing. Before any prod run or PR, answer the 4 review questions below ON THE BRANCH
(read/analyze — no new feature work). These gate closeability. Standards: computed-and-cited / canonical-or-floor;
L1-is-authority; no silent failures (logger.warning not debug). Report a findings block per question.

---

## Q1 — The "15 Shodasavarga vargas" count: confirm it's not an off-by-one silent omission

Amendment 1 says per-varga Ashtakavarga across "15 Shodasavarga vargas." The classical Shodasavarga set is
**16 charts** (D1, D2, D3, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60 = 15 vargas, **+ D1 = 16**).

**Answer with evidence from the code:**
1. List the EXACT 15 vargas the Ashtakavarga builder iterates (paste the varga list/constant from the writer).
2. Confirm whether **D1 was deliberately excluded** because D1 Ashtakavarga already exists in `chart_facts`
   (the data investigation Q3 found D1 BAV present) — if so, "15 = 16 − D1" is CORRECT and intentional. State
   it explicitly.
3. If the 15 are NOT "Shodasavarga minus D1" — i.e. a different varga was dropped — that is a silent omission;
   identify the missing one and flag it. (This is the silent-omission class that has bitten this project; do
   not let "15" pass without naming the set.)

---

## Q2 — The `dignity_status` → `dignity` bug: was prior data silently corrupted, and is logging fixed?

Amendment 2 "also fixed a pre-existing `dignity_status` → `dignity` bug in `_load_varga_dignity_spread`." This
is the SAME CLASS as the ga_condition phantom-column transaction-poison we logged
([[feedback-swallowed-exception-txn-poison]]): a wrong column name that can throw `UndefinedColumn`, poison the
psycopg3 txn, and be swallowed by `logger.debug` — producing silently-empty/partial output that looks like a
clean run.

**Answer with evidence:**
1. **Was the bug LIVE and SILENT before this fix?** Show the before/after: did `_load_varga_dignity_spread`
   actually return data prior, or was it throwing/empty? Was the exception swallowed at `logger.debug`?
2. **CRITICAL — did it corrupt `graha_dignity_per_varga`?** Amendment 2's Deeptadi avastha READS those 1,350
   rows (the data investigation found them complete). If `_load_varga_dignity_spread` was the writer/loader for
   that data and it was buggy, those rows may be wrong/incomplete. Verify: query `graha_dignity_per_varga` for
   482012f1 — is it genuinely 1,350 rows (30 vargas × 9 grahas × 5 ay), and do sample values look correct
   (e.g. a known exaltation/debilitation for the native)? If the bug affected them, those rows need a REBUILD,
   and Amendment 2's Deeptadi (built on top) must rebuild after.
3. **Is the swallowing log fixed?** Confirm the helper's swallowed-DB-error `logger.debug` is now
   `logger.warning` (or re-raises) per the rail. If still debug, flip it.

---

## Q3 — Prod-validation plan (the L0 trap, repeated)

These are committed with passing UNIT tests on a branch — but unit-green ≠ prod rows for the native
([[feedback-ac-must-verify-target-environment]]). State the plan to validate against PROD (not the branch DB):
1. The 3 reopened writers (ga_strength, ga_condition, ga_sensitive) run for `482012f1` against prod via the
   orchestrator (they are @register WriterBase under the FROZEN contract — confirm no contract change was made;
   if any writer needed a contract change, that's a HALT-and-raise, report it).
2. The new rows actually land on prod: per-varga Ashtakavarga rows, per-varga Baladi/Deeptadi rows, the 5
   sensitive-point builders' rows — with counts.
3. Floors set to achieved counts; every new datum carries its classical_citation OR a floored NULL+reason
   (canonical-or-floor); the floored items (Kala/Cheshta, Jagradadi/Sayanadi/Lajjitadi, Vighati) show their
   stored reason, not a fabricated value.
(Don't run it yet if the native wants Q1/Q2 answered first — just state the plan + readiness.)

---

## Q4 — The 2 "pre-existing, unrelated" registry test failures

Confirm in one line each: (a) both failures exist on `main` BEFORE this branch (show they're the known main-CI-red
state — TypeScript ClassicalTextSearchResult.title + 035_DISCOVERY build-context, [[project-main-ci-red]] — or
name them if different), and (b) neither is masking a failure introduced by this branch (i.e. they fail
identically on main and here, same error signature). If either is actually new, it's not pre-existing — fix it.

---

## OUTPUT

A short findings block per question (Q1 the 15-varga set + D1-exclusion confirmation; Q2 the bug's live-impact +
the graha_dignity_per_varga integrity check result + logging status; Q3 the prod-validation readiness; Q4 the
2-failure provenance). If Q2 finds the 1,350 dignity rows were affected, STOP and report — that's a rebuild
dependency, not a PR. Otherwise report ready-for-prod-gate. Do NOT open the PR until the native reviews these
answers.
