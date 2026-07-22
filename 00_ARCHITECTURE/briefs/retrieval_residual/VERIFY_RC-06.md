---
artifact: VERIFY_RC-06.md
residual: RC-06 (golden set) — planner_golden_set.json recalibration
brief: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E Cluster 2
branch: res/rc06-golden-set
commit_verified: 9365a616 (fix-cycle-2); 853cf471 (fix-cycle-1, REJECTED — record below)
base: a81f4cd6 (res/integration head — includes RC-05 dead-tool sweep)
verifier: independent VERIFIER agent (did NOT implement) — fresh re-verify after fix
verdict: ACCEPT (fix-cycle-2); prior REJECT (fix-cycle-1) retained below for audit
date: 2026-07-22
---

# RC-06 Independent Verification — FIX-CYCLE-2 VERDICT: ACCEPT

Re-verified from scratch against `res/rc06-golden-set` @ `9365a616` (worktree
`.claude/worktrees/wf_3e85c10c-202-1`) after the prior REJECT (fix-cycle-1 @
`853cf471`, full record preserved below this section). Nothing was trusted
from the implementer report; every check was re-run. The residual is now
**complete**: all three DONE-bar legs are met and every one of the seven
required changes from the prior REJECT is independently confirmed.

## Independent re-derivation of the authoritative dead set (not trusted from report)

The WP-1.7 14-name dead set was re-derived from BOTH sources the task named:
- `tool_name_bridge.ts:410-422` (the WP-1.7 removal note listing the 14 names REMOVED for having no backing registry capability), and
- `compiled_floor_adapter.test.ts:242-247` (`DEAD_CAPABILITIES` array).

Both sources agree exactly on the 14 names: `pattern_register,
resonance_register, cluster_atlas, kp_query, query_kp_ruling_planets,
query_ucn_walk, query_cdlm_lookup, query_rm_walk, query_jaimini_drishti,
timeline_query, query_signal_state, multi_school_signal_lookup,
jaimini_chara_dasha, jaimini_chara_dasha_full`. The RETAINED/now-resolvable
set (`cgm_graph_walk, temporal, contradiction_register, query_tara_balam,
query_chandra_balam`) was NOT treated as dead.

## (a) Tests — rerun independently @ 9365a616

- `npx vitest run tests/eval/` → **4 files, 73 passed (73)**, 1.88s.
- `npx vitest run src/lib/pipeline/__tests__/compiled_floor_adapter.test.ts` (the RC-05 dead-cap floor guard) → **30 passed (30)**.
- Regression gate legs verified passing: "baseline covers every planner_golden_set entry by id"; "avg_tool_recall ≥ 0.80 and avg_tool_precision ≥ 0.90".

The prior REJECT correctly noted the mock gate is structurally blind to a
dead-cap sitting in `expected_tools`/`required_tools`; that is why leg 1 is
verified by the independent scan in (c), NOT by the gate alone.

## (b) DONE bar (brief §E RC-06, verbatim) — all three legs MET

> **DONE:** zero dead-capability references remain in the golden set; the
> planner regression gate passes against the recalibrated set; a diff report
> explains every changed case.

1. **"zero dead-capability references remain in the golden set" — MET.** See
   (c): 0 across `expected_tools`, `required_tools`, `available_tools`, and
   baseline `mock_tool_calls[].tool_name` for all 14 WP-1.7 names.
2. **"planner regression gate passes" — MET** (see (a)).
3. **"a diff report explains every changed case" — MET.** `RC-06_DIFF_REPORT.md`
   now marks the fix-cycle-1 leg-1 claim SUPERSEDED/FALSE (line 85) and adds a
   "Fix-cycle-2" section (line 312+) with the full 14-name re-derivation and a
   per-name Resolver-ruling table (lines 344-346) covering GT.050/051,
   GT.056-058, GT.059-061.

## (c) Independent dead-capability scan @ 9365a616 — the passing evidence

Scanned `planner_golden_set.json` (86 entries) and
`fixtures/regression_baseline.json` (86 entries) for all 14 names, via both a
JSON-parse partition AND a raw `grep` cross-check (belt-and-suspenders):

| Field | Dead refs (all 14 names) |
|---|---|
| `expected_tools` | **0** |
| `required_tools` | **0** |
| `available_tools` (catalog, now 13 names) | **0** |
| baseline `mock_tool_calls[].tool_name` | **0** |

Raw-grep reconciliation: the only remaining occurrences of any dead name in
the golden set are `pattern_register`×16, `resonance_register`×5,
`cluster_atlas`×5, `timeline_query`×6 = **32 total, ALL inside `forbidden_tools`**
(JSON-partition: forbidden_tools=32, expected=0, required=0, available=0 —
sum reconciles exactly, zero leakage into any authoritative field). Retention
in `forbidden_tools` is correct and desirable: it is the guard asserting the
planner must NEVER emit these. This matches the prior REJECT's own note that
`forbidden_tools` retention is defensible.

Per-entry confirmation of the seven required changes from the prior REJECT:
- GT.050/051 (`multi_school_signal_lookup` dropped): now `expected=required=[convergence_score_lookup]` — sole live survivor. ✓
- GT.056 (`query_signal_state` dropped): `expected=[msr_sql, vector_search]`, `required=[msr_sql]`. ✓
- GT.057/058 (`query_signal_state` dropped): `msr_sql` promoted to required alongside temporal/lel_query. ✓
- GT.059/060 (`query_kp_ruling_planets`/`kp_query` dropped): `expected=required=[msr_sql]`. ✓
- GT.061 (`query_kp_ruling_planets` dropped, `msr_sql` forbidden here): `expected=required=[]` — empty, precedented (GT.027/028/046 already empty; `scoreEntry` treats empty expected as recall=precision=1). No div-by-zero; regression gate passes with all 4 empty-expected entries present. ✓
- `available_tools` catalog: 16 → 13 (the 3 names removed). ✓
- baseline mocks: 0 dead refs across all 86 entries; every golden entry still covered by a baseline entry (86/86, no missing ids); every `required_tool` present in its entry's mock (required_hit holds). ✓

## (d) Scope / must_not_touch — CLEAN

`git diff --stat a81f4cd6..HEAD` (full branch history) touches exactly four
files, all inside `may_touch`:
- `platform/tests/eval/planner_golden_set.json` (`platform/tests/eval/**`)
- `platform/tests/eval/fixtures/regression_baseline.json` (same)
- `00_ARCHITECTURE/briefs/retrieval_residual/RC-06_DIFF_REPORT.md` (`retrieval_residual/**`)
- `00_ARCHITECTURE/briefs/retrieval_residual/VERIFY_RC-06.md` (this artifact)

`git diff --name-only a81f4cd6..HEAD | grep -iE 'orchestrat|writer|ga_|bo_|ka_|ph_|mi_|WriterBase|chart_facts|migrations|CLAUDECODE_BRIEF.md|wave/D-4b|kala_|gochara'` → **empty**. No FROZEN
orchestrator / WriterBase / layer writer, no `chart_facts` semantics, no
`kala_*`/gochara serving semantics, no D-4b branch, no root CLAUDECODE_BRIEF,
no migration touched. Working tree clean (only untracked `node_modules`).

## FIX-CYCLE-2 VERDICT

**ACCEPT.** All three DONE-bar legs are met; the independent 14-name scan
returns 0 across every authoritative field and the baseline; the full eval
suite (73/73) and the RC-05 floor guard (30/30) are green; scope is clean.
RC-06 is CLOSED.

---
---

# [SUPERSEDED] RC-06 fix-cycle-1 Independent Verification — VERDICT: REJECT (853cf471)

*Retained verbatim for audit. Every required change below was subsequently
applied in fix-cycle-2 (`9365a616`) and independently re-verified ACCEPT above.*

Verified against `res/rc06-golden-set` @ `853cf471` (worktree
`.claude/worktrees/wf_3e85c10c-202-1`). Every check below was run by the
verifier, not trusted from the implementer report. The register-family
sweep the implementer performed is genuinely good per-case work — but the
residual's DONE-bar leg 1 ("zero dead-capability references remain in the
golden set") is **NOT met**: four other WP-1.7 dead capabilities survive in
`expected_tools`, `required_tools`, `available_tools`, AND the baseline
mocks. The implementer silently narrowed "dead capability" to the three
register-family names and did not apply the full 14-name WP-1.7 dead set that
RC-05 established as authoritative and that the diff report itself cites.

---

## (a) Tests — rerun independently

- `npx vitest run tests/eval/planner_regression_gate.test.ts` → **2 passed (2)**, 606ms.
- `npx vitest run tests/eval/` → **4 files, 73 passed (73)**, 1.63s.

Both match the implementer's report. **However, the regression gate is
structurally blind to this residual's core defect.** The gate's mock planner
(`planner_regression_gate.test.ts:75-81`) replays `mock_tool_calls` that
*mirror each entry's `expected_tools`*; recall/precision are therefore ~1.0
by construction, and `forbidden_violation` only inspects `forbidden_tools`.
A dead tool sitting in `expected_tools`/`required_tools` produces **no test
failure**. So "the gate passes" (DONE-bar leg 2) is TRUE but provides **zero
evidence** for DONE-bar leg 1. Passing tests here cannot be read as "no dead
tools remain."

## (b) DONE bar (brief §E RC-06, verbatim) vs. what shipped

The brief §E RC-06 DONE bar has three legs:

> **DONE:** zero dead-capability references remain in the golden set; the
> planner regression gate passes against the recalibrated set; a diff report
> explains every changed case.

1. **"zero dead-capability references remain in the golden set" — FAILS.**
   See (c). Dead capabilities remain in the "SHOULD/MUST select" fields and
   the tool catalog, not merely in `forbidden_tools`.
2. **"planner regression gate passes" — MET but non-probative** (see (a); the
   gate cannot detect the leg-1 defect).
3. **"a diff report explains every changed case" — MET for the changes made,
   but the report's leg-1 self-assessment is false.** `RC-06_DIFF_REPORT.md`
   line 311-316 asserts leg 1 is "**MET** for `expected_tools`/`required_tools`/
   `available_tools` (the assertable, test-consumed surfaces)." That claim is
   contradicted by the report's own table (lines 149-150 show `query_signal_state`
   surviving in the after-column of changed entries GT.056/GT.057) and by the
   scans in (c).

The implementer's summary likewise claims: *"Zero dead-capability references
remain in `expected_tools`/`required_tools`/`available_tools` or the baseline
mocks (verified programmatically)."* **This claim is false** — reproduced
below.

## (c) Independent dead-capability scan — the failing evidence

Authoritative dead set = the WP-1.7 14-name list, taken verbatim from the
RC-05 regression test that governs RC-06's substitutions
(`compiled_floor_adapter.test.ts:242-247`, `DEAD_CAPABILITIES`) and from
`tool_name_bridge.ts:410-422`: `pattern_register, resonance_register,
cluster_atlas, kp_query, query_kp_ruling_planets, query_ucn_walk,
query_cdlm_lookup, query_rm_walk, query_jaimini_drishti, timeline_query,
query_signal_state, multi_school_signal_lookup, jaimini_chara_dasha,
jaimini_chara_dasha_full`. (RETAINED / now-resolvable, NOT dead:
`cgm_graph_walk, temporal, contradiction_register, query_tara_balam,
query_chandra_balam`.)

I re-derived that these four remaining names are genuinely unresolvable:
none appears as a resolvable KEY in `TOOL_NAME_TO_URI`
(`grep '^\s*(name):' tool_name_bridge.ts` → empty); the file's own docstring
(lines 58-63) lists `kp_query, query_kp_ruling_planets, timeline_query,
query_signal_state` as "return undefined from `getToolByName()`"; the WP-1.7
block (lines 417-420, 532-535) lists `multi_school_signal_lookup` and the KP
pair as "no registered cap / no backing." Same truth source as a live
`unresolved_tools` trace.

Programmatic scan of `planner_golden_set.json` @ 853cf471 (86 entries):

| Field | Dead refs found | Entries |
|---|---|---|
| `expected_tools` | **9** | GT.050, GT.051 (`multi_school_signal_lookup`); GT.056, GT.057, GT.058 (`query_signal_state`); GT.059, GT.060, GT.061 (`query_kp_ruling_planets`); GT.060 (`kp_query`) |
| `required_tools` | **7** | GT.050 (`multi_school_signal_lookup`); GT.056-058 (`query_signal_state`); GT.059-061 (`query_kp_ruling_planets`) |
| `available_tools` (catalog) | **3** | `multi_school_signal_lookup`, `query_kp_ruling_planets`, `query_signal_state` |

Scan of `fixtures/regression_baseline.json` @ 853cf471 (86 entries):

| Field | Dead refs found | Entries |
|---|---|---|
| `mock_tool_calls[].tool_name` | **9** | GT.050, GT.051, GT.056-061 (same names as above) |

These are not `forbidden_tools` (where retention is defensibly documented in
`field_notes`). They are in the fields that assert *correct planner behavior*:
e.g. GT.059 `required_tools: ["query_kp_ruling_planets"]` — the golden set
declares a correct planner **MUST** emit a tool that `getToolByName` resolves
to `undefined`. That is exactly the defect class RC-05/RC-06 exist to remove;
a planner obeying this golden expectation on a live query would surface
`unresolved_tools`.

**Why it was missed:** the implementer swept only `pattern_register /
resonance_register / cluster_atlas` (the RC-06 brief's illustrative "~99
pattern_register references" + the 3-name `available_tools` 19→16 trim), and
scanned only for those three when claiming "verified programmatically." The
KP tools, `query_signal_state`, and `multi_school_signal_lookup` were never
in the implementer's dead-set definition, so they passed through untouched.

## (c-supplement) Quality of the work that WAS done

The register-family recalibration (43 entries) is **sound, per-case judgment
work — not a blind bulk replace.** Spot-checked >10 changed cases against the
RC-05 substitution rules; each is correct and carries a specific rule cite:

- GT.014 (predictive, "transiting right now") — `pattern_register` → `vector_search`; correct per R7c's absolute ban allowing only msr_sql + vector_search.
- GT.031/032/037/038 (remedial) — `resonance_register` → `vector_search`; correct per R7b's unconditional live substitute.
- GT.045 (single-stone remedial) — `resonance_register` → `vector_search`, and `vector_search` correctly removed from `forbidden_tools` because R7b now unconditionally mandates it (supersedes the old "dilutes codex" ban). Good catch.
- GT.053 (long-horizon dasha) — `pattern_register` **dropped** (deduped against existing required `vector_search`); correct per R7a.
- GT.054 (Saturn live-transit) — `pattern_register` → `vector_search`; correct per R7c.
- GT.062/063 — `pattern_register` dropped, `vector_search` promoted to required; correct per R7a.
- GT.064/066 (multi-domain synthesis) — `cluster_atlas` → `vector_search` (R11 main branch), `pattern_register` dropped-no-substitute (R11 excised it in W6.3/v2.8); correct.
- GT.033/034 (yogas / whole-chart interpretive) — `pattern_register` → `vector_search` under R17 chart-level-multi-layer scope; correct, msr_sql yoga surface retained.

The substitution doctrine was applied correctly *within the scope the
implementer chose*. The defect is scope, not technique.

## (d) RC-09 — not on this branch (out of scope)

The task checklist asked to verify RC-09 (51/51 dark tables terminal). **No
RC-09 deliverable exists on `res/rc06-golden-set`** — `DARK_TABLE_DISPOSITIONS_v3_0.md`
and `VERIFY_RC-09.md` are absent here. RC-09 is a separate Wave R-B lane
(`res/rc09-dark-tables`, worktree `wf_3e85c10c-202-2`) with its own dedicated
verifier per brief §D.4. The RC-06 branch under verification does not touch it;
I make no claim on RC-09's count and defer it to the RC-09 lane verifier. (This
appears to be a generic-template checklist item that does not apply to the
RC-06 branch.)

## (e) RC-10 — not on this branch (out of scope)

Same as (d). No `NAMESPACE_COVERAGE_v2_0.md` or RC-10 artifact on this branch;
no `res/rc10-*` branch exists in the worktree set. The MCP↔web coverage
fraction is not measurable from the `res/rc06-golden-set` diff (which touches
only two eval fixtures + one report). Deferred to the RC-10 owner. Flagged as
a template-mismatch checklist item.

## (f) Scope / must_not_touch — CLEAN

`git diff --stat main...HEAD` touches exactly three files, all inside the
brief's `may_touch` globs:
- `platform/tests/eval/planner_golden_set.json` (may_touch: `platform/tests/eval/**`)
- `platform/tests/eval/fixtures/regression_baseline.json` (same)
- `00_ARCHITECTURE/briefs/retrieval_residual/RC-06_DIFF_REPORT.md` (may_touch: `retrieval_residual/**`)

`git diff --name-only main...HEAD | grep -iE 'orchestrat|writer|ga_|bo_|ka_|ph_|mi_|chart_facts|kala_|gochara'` → **empty**. No FROZEN
orchestrator / WriterBase / layer writer, no `chart_facts` semantics, no
`kala_*`/gochara serving semantics, no D-4b branch touched. Scope is clean.

## Verdict

**REJECT.** DONE-bar leg 1 ("zero dead-capability references remain in the
golden set") is not met, and the residual's own diff report + summary assert
it IS met on exactly the surfaces where the defect remains.

### What must change before RC-06 can close

Sweep the **remaining four WP-1.7 dead capabilities** out of the
"correct-behavior" fields and the catalog, applying the same RC-05
substitution doctrine already used for the register family (per-case; Resolver
rules any ambiguous case). Affected entries:

1. **`query_kp_ruling_planets`** — GT.059, GT.060, GT.061 (expected + required) — KP factual queries. No KP engine is registered (`tool_name_bridge.ts:417`). Substitute or drop per the governing factual rule; the KP concept has no live twin, so this likely drops to `msr_sql` (already present in GT.059/060) with the KP-specific expectation removed, or is Resolver-dispositioned.
2. **`kp_query`** — GT.060 (expected) — same class.
3. **`query_signal_state`** — GT.056, GT.057, GT.058 (expected + required) — dead; **`query_signals` is served by `msr_sql`** (`tool_name_bridge.ts:420`), which is the direct live twin and already sits in each of these entries' `expected_tools`. Straightforward substitution (drop `query_signal_state`, keep/require `msr_sql`).
4. **`multi_school_signal_lookup`** — GT.050, GT.051 (expected + required) — multi_school_triangulation class; "legacy lib/tools impl, never bridged" (`tool_name_bridge.ts:415, 507`). Resolver must rule the substitute (`convergence_score_lookup` is already the co-expected live tool; the triangulation concept may have no direct live twin → Resolver disposition).

5. **`available_tools` catalog** — remove `multi_school_signal_lookup`,
   `query_kp_ruling_planets`, `query_signal_state` (the current 16-name list
   still contains all three), so the catalog stops advertising dead names as
   primary tools.

6. **`fixtures/regression_baseline.json`** — mirror every one of the above
   edits in the 9 affected `mock_tool_calls` entries (GT.050, GT.051,
   GT.056-061), so the gate keeps mirroring `expected_tools`.

7. **Correct the diff report + summary**: leg-1 status is not MET; re-derive
   it against the full 14-name WP-1.7 dead set, not the 3-name register family.

After the fix: re-run `vitest run tests/eval/` (must stay green) AND re-run the
independent dead-capability scan (this document's (c)) — it must return **0**
across `expected_tools`, `required_tools`, `available_tools`, and the baseline
mocks against all 14 WP-1.7 names before RC-06 is re-submitted for verification.
