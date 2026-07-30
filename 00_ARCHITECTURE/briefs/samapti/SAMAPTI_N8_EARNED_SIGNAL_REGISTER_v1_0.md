---
artifact: SAMAPTI_N8_EARNED_SIGNAL_REGISTER
canonical_id: SAMAPTI_N8_REGISTER
version: 1.1
status: FINDINGS-COMPLETE (audit lane — ships no fixes)
changelog: >
  v1.1 (2026-07-30, post-VER-verification corrections, DVA-applied): fixed F-04's Julian Day
  citation (:112 -> :111); fixed F-11's envelope.ts citation (:1620-1624 -> :1622-1625, both
  occurrences) which previously contradicted F-25/F-38's correct citation of the same check;
  corrected F-02's ci.yml quote splice (was presented as one continuous remark about
  dag_edge_guard's own test, is actually two remarks about two different test files;
  re-verified the underlying finding independently instead, confirmed to survive); narrowed
  F-27's "two independent reasons" to one demonstrated reason (--synthetic short-circuits
  before the second, undemonstrated reason is ever reached); disambiguated bare `envelope.ts`
  (two files exist, platform/src/lib/retrieval/ vs platform-mcp/src/generated/) and
  `ga_dashas_writer.py` citations to full paths. No finding's substance or severity changed;
  citation precision only, required before the 8 lanes depending on this register consume it.
created: 2026-07-30
lane: A7-N8-AUDIT (SAMĀPTI conductor swarm)
track: SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §7 (T4.3 + T4.4)
doctrine: CLAUDE.md §N.8 — Earned-Signal Principle
base_commit: cdb6fc3b3d37e3b586f188649c59e57c251ed935 (origin/main at audit time)
starting_set_source: SATYA_DIPA_REPORT_v1_0.md §5 (scoped-but-never-swept)
consumes:
  - CLAUDE.md §N.8 (Earned-Signal Principle) + §N.6 (Serving Density Principle)
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/satya_dipa/SATYA_DIPA_REPORT_v1_0.md §5
  - 00_ARCHITECTURE/briefs/samapti/SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §7
  - 00_ARCHITECTURE/CONDUCTOR/session_queue_SAMAPTI.yaml (lane A7-N8-AUDIT)
feeds: B-N8-FIX · B-N8-SWEEPFIX · B-N8-LINT
ships_code: false
---

# SAMĀPTI A7-N8-AUDIT — Earned-Signal Findings Register

**This lane ships no fixes.** Every entry below is a work item for a B-lane. Nothing here was
repaired; nothing here should be repaired by reading this document alone — each finding names the
file:line and the demonstration, and a B-lane builder must re-derive before changing code.

---

## §0 — Method, and the bar every finding had to clear

### §0.1 — The doctrine, restated as a test

`CLAUDE.md §N.8`: *"Every status, grade, or PASS must be computed by a detector that measures the
specific claim it asserts; a signal without such a detector is null, not green."*

Applied as one question per candidate:

> **What specifically does this signal claim, and what code path would have to run — AND FAIL — for
> the signal to correctly read false?**

Five verdicts are possible, and only the first four are findings:

| Class | Meaning |
|---|---|
| **LITERAL** | The value is a hardcoded constant. No input can change it. |
| **TAUTOLOGY** | Structurally always-true: the only falsifying state is unreachable, or is caught and raised before the signal is computed. |
| **PROXY** | A real, falsifiable check — of something adjacent to the claim, not the claim. |
| **CANNOT-FAIL GATE** | A CI/guard/probe whose green is not produced by any executed assertion (never invoked, skipped, error swallowed, exit code unpropagated). Includes the inverse: an **always-red** gate, whose red is equally uninformative. |
| **GENUINE** | A real detector measures the real claim. **Not a finding — rejected.** |

### §0.2 — The adversarial requirement

The lane's verify contract states the Verifier will *"spot-refute a sample of the register and reject
the lane if any finding survives only by assertion."* Accordingly:

1. Every candidate was traced to its computation — including helpers, SQL, and consumers. No finding
   rests on a field name.
2. Every candidate was attacked. Sub-auditors argued against their own findings inline (the `(e)`
   blocks in their reports, reproduced or summarised here).

   **Disclosure about the §1 refutation, because this register is about unearned claims and must not
   make one.** A **separate, independent refuter sub-agent** was dispatched against F-01…F-06 with the
   evidence and an explicit instruction to destroy each finding. **It never returned its verdicts.**
   The refutation attempts recorded in each §1 entry's `(d)` block are therefore the **lane owner's
   own adversarial passes**, not an independent agent's. They are genuine — each names a specific
   counter-argument and answers it on code evidence, and two of them (F-03, F-06) *succeeded* in
   narrowing the finding — but they are **self-refutation, not independent refutation.**
   **A Verifier should treat §1 as the least independently-attacked section of this register and
   weight its spot-refutation there.**
3. Findings that the refutation killed, or that could not be demonstrated, are in **§4 — Dropped**,
   with the reason. That section is deliberately non-empty. A register of only survivors is a
   register that did not test itself.
4. Where a finding was *narrowed* by refutation rather than killed, the narrowed version is what
   appears — with the overstatement named, so a B-lane does not inherit it.

### §0.3 — What "demonstrated" means here, by finding type

- For a **runtime signal**: the code path is quoted and the reachable input state named.
- For a **probe**: it was **executed** and its real output pasted. (F-07, F-08.)
- For an **absence** (no detector exists): the exhaustive search is written out — what was grepped,
  over which trees — because an absence claim is only as good as the search behind it.
- For a **numeric claim**: it was recomputed independently. (F-07's Julian Day and node longitude
  were recomputed with Swiss Ephemeris; the arithmetic is in the finding.)

### §0.4 — Coverage, honestly stated

- **Part A** (§1) — the five named files from `SATYA_DIPA_REPORT` §5. This is the sweep's *defined
  starting set and its completion test*. **All five files are swept. Every one carries at least one
  confirmed finding.**
- **Part B** (§2) — codebase-wide, by subsystem, via four bounded parallel read-only sub-auditors
  (known-member writers · TypeScript serving layer · CI/gates/guards · Python build-layer writers),
  all of which reported.
- **§3** — rejected candidates. These are load-bearing: they show the sweep discriminates, and
  several are the *correct pattern* a B-lane should copy rather than reinvent.
- **§4 / §5** — dropped candidates and residuals: named surfaces this audit did **not** reach, and
  the one class of evidence it could not obtain.

**Three methodology caveats a Verifier should hold against the whole document:** (i) live DB
corroboration in Part B is the sub-auditors', not mine — my own production query failed
(`ECONNREFUSED 127.0.0.1:5433`); (ii) F-33 (PB-2) is **static-only** — `vitest` was absent from that
sub-auditor's worktree, so its mutation-sensitivity claim is code-read, not executed; (iii) the
independent refuter dispatched against §1 never reported, so §1's refutations are self-authored —
see §0.2 item 2.

---

## §1 — PART A · The five named files (the defined starting set)

| File | Findings | Verdict |
|---|---|---|
| `pipeline/orchestrator/runner.py` | F-01, F-05 | SWEPT — findings confirmed |
| `pipeline/orchestrator/staleness.py` | F-05 | SWEPT — finding confirmed |
| `pipeline/orchestrator/dag_edge_guard.py` | F-02 | SWEPT — finding confirmed |
| `pipeline/orchestrator/kala_derivation_completeness_guard.py` | F-02, F-03 | SWEPT — findings confirmed |
| `pipeline/orchestrator/service_probes.py` | F-04, F-06 | SWEPT — findings confirmed |

All paths below are relative to `platform/python-sidecar/`.

**Disambiguation note.** Two files in the repo are named `runner.py`:
`platform/python-sidecar/pipeline/orchestrator/runner.py` (the build orchestrator) and
`platform/scripts/eval/runner.py` (the evaluator harness). `SATYA_DIPA_REPORT` §5 lists it among
orchestrator modules, and the SAMĀPTI v2.0 authorization grant explicitly excludes *"modifying the
sealed evaluator harness"* — so the orchestrator file is the one in scope. `platform/scripts/eval/runner.py`
was **not** audited; see §5.

---

### F-01 · `build_run_assets.state` is the literal `'complete'`, so a run containing an asset the build itself classified `incomplete` reports as clean

- **Class:** LITERAL (with a downstream cascade into the run-level verdict)
- **Severity:** HIGH
- **Files:** `pipeline/orchestrator/asset_runner.py:695-699` (origin) · `pipeline/orchestrator/runner.py:490-495`, `:350-356`, `:578-636`, `:795` (cascade)
- **Routes to:** B-N8-SWEEPFIX (runner.py is in its scope; the origin write is in `asset_runner.py` — see the scope note below)

**(a) The claim.** `build_run_assets.state = 'complete'` asserts *"this asset's work in this run
finished successfully."* It is the run-level per-asset truth record, and — per
`_reconcile_failed_assets_from_db`'s own docstring — it is treated as **the source of truth** over the
scheduler's in-memory bookkeeping.

**(b) What actually computes it.** Nothing. `asset_runner.py:695-699`:

```python
    cur.execute(
        """UPDATE build_run_assets SET state = 'complete', ended_at = NOW()
           WHERE run_id = %s AND asset_id = %s""",
        (run_id, asset_id),
    )
```

This statement is unconditional. It is reached for **every** value of `final_state` — `'lit'`,
`'dormant'`, and `'incomplete'` alike. Nine lines above, the same function writes the *truthful*
state to a different table (`:686-693`, `SET state = %s` with `final_state`). The two tables diverge
by construction.

**(c) Demonstration — the falsifying state exists, is produced by this very function, and is discarded.**

`asset_runner.py:661-678` is SATYA-DĪPA's own fix. When a writer's substep plan reports work
remaining, it takes this branch:

```python
            else:
                logger.warning(
                    "[orchestrator] NO-OP COMPLETION REJECTED: asset %s (chart %s, run %s) "
                    "reported 0 rows this run; %d data rows are present but the writer's own "
                    "substep plan reports %d substep(s) still remaining. Marking 'incomplete', "
                    "NOT 'lit' — downstream deps stay blocked until the plan actually finishes.",
                    ...
                )
                final_state = 'incomplete'
```

`final_state` is now `'incomplete'`. Eighteen lines later `build_run_assets` is set to `'complete'`.
The cascade, each step quoted from the code:

1. `runner.py:490-495` — `worker()` reads **`build_run_assets.state`** as the asset's outcome:
   `"SELECT state FROM build_run_assets WHERE run_id = %s AND asset_id = %s"` → returns `'complete'`.
2. `runner.py:350-356` — `execute_dag`'s success rule is a **denylist**:
   `if fut.result() == "error": failed.add(a) else: completed.add(a)`. `'complete'` ≠ `'error'`, so
   the incomplete asset enters `completed` and `on_complete(a)` fires.
3. `runner.py:578-636` — `_reconcile_failed_assets_from_db` classifies `'error'`/`'aborted'` and the
   non-terminal `'building'`/`'queued'`/`None` as failed. `'complete'` is not failed — and at
   `:621-627` it **actively removes** such an asset from the failed set (*"trusting DB, removing from
   failed set"*).
4. `runner.py:795` — `final_state = "failed" if failed_assets else "completed"` →
   **`build_runs.state = 'completed'`**.

The run is reported clean. The comment guarding that very line (`runner.py:790-792`) states the
purpose it fails to serve:

> *"BA-P3 FIX 3: a run whose plan included any failed/blocked asset must NOT be reported as
> 'completed' — that reads as a clean, trustworthy build to an operator when it is not (the 45/66-errored
> 'green over-report', NF-1)."*

**Reachable scenario, concretely:** rebuild a single heavy writer with a real substep plan
(`has_substeps=true` — `ka_sangam` or `ka_gochara_sweep`, the two writers `SATYA_DIPA_REPORT` §5
identifies as the only participants in `build_substep_progress`). The plan does not finish.
`asset_throughput.state = 'incomplete'`; `build_run_assets.state = 'complete'`;
`build_runs.state = 'completed'`. Note `ka_gochara_sweep` at 78/303 and 70/303 substeps is an
already-observed real state (`SATYA_DIPA_REPORT` §4).

**(d) Adversarial refutation attempted, and why it failed.**

*Refutation 1 — "`deps_unsatisfied` catches it, so the run goes red anyway."* `asset_runner.py:44-89`
does use the correct allowlist (`elif state != "lit": bad.append(...)`), and in `enforce` mode a
downstream asset dispatched onto an `incomplete` upstream is marked `error`, turning the run red.
**This does not refute the finding, on four independent grounds:**
  - It only fires if the incomplete asset **has a downstream asset inside this run's plan**. A
    single-asset rebuild — the ordinary way a heavy writer is retried — has none. The run reports
    `completed` with no red anywhere.
  - It is a *different detector at a different layer*. §N.8's test is whether *this* signal measures
    *its* claim. `build_run_assets.state` measures nothing; a second surface being correct does not
    earn the first one's green.
  - It is **env-disableable**: `_DEP_ASSERT_MODE = os.environ.get("ORCHESTRATOR_DEP_ASSERT", "enforce")`
    (`asset_runner.py:41`). In `warn` mode the backstop logs and runs the writer anyway.
  - Where it *does* fire, the resulting signal is still wrong in kind: the downstream asset is marked
    `error` by a dependency assertion instead of taking the honest `BLOCKED:` path
    `_mark_asset_blocked` (`runner.py:207-246`) exists to produce — because `execute_dag` never put the
    incomplete asset in `failed`, so transitive blocking never engages.

*Refutation 2 — "`dormant` has always been written `'complete'` too; this is long-standing intended
behaviour."* Correct as history, and it is why the finding is stated about `incomplete` specifically:
`dormant` is a *declared* outcome of a legitimate build ("ran, produced nothing"), whereas
`incomplete` was introduced by SATYA-DĪPA (migration 474) precisely to mean *"this build did not
finish."* The finding is that the state introduced to carry that meaning is not carried anywhere the
run-level verdict can see it.

*Refutation 3 — "the operator can see `asset_throughput` in the cockpit."* Two surfaces disagreeing
is the defect, not the mitigation. And per `SATYA_DIPA_REPORT` §7, five cockpit TypeScript
`AssetState` unions do not yet include `'incomplete'`, so that surface renders it through a default
branch.

**Scope note for the conductor.** The queue assigns `runner.py` to **B-N8-SWEEPFIX** and the origin
write is in `asset_runner.py`, which no B-lane names. `asset_runner.py` is also the file carrying
SATYA-DĪPA's **spent** freeze exception. The one-line fix (make the `build_run_assets` write carry
`final_state`'s verdict) is a writer-side data fix, not an orchestrator *contract* change — but the
call belongs to `DVA`, not to a builder. **Flagged, not decided.** See §6 QUESTIONS.

---

### F-02 · `dag_edge_guard` and `kala_derivation_completeness_guard` assert they are CI gates; neither runs in CI. One has zero automated invocation anywhere

- **Class:** CANNOT-FAIL GATE (absence of any executed assertion)
- **Severity:** HIGH
- **Files:** `pipeline/orchestrator/dag_edge_guard.py:13-15, :27-28, :213` · `pipeline/orchestrator/kala_derivation_completeness_guard.py:22-24, :119` · `.github/workflows/ci.yml:344-372` · `tests/test_dag_edge_guard.py:96-98` · `tests/test_kala_derivation_completeness_guard.py`
- **Routes to:** B-N8-SWEEPFIX (both files in scope) · B-N8-LINT (the same wiring gap applies to the new §N.8 lint — do not repeat it)

**(a) The claim.** `dag_edge_guard.py:13-15`, verbatim:

> *"This automates, **as a CI gate**, the manual reads-vs-declared audit that produced migration 365.
> It catches drift **the moment** a writer adds an undeclared cross-asset read."*

That is a claim about automatic, immediate detection. The governance corpus repeats it —
`BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md:82` calls it *"the project's own CI edge-completeness
gate"*; `ORCHESTRATOR_WAVE_PARALLEL_SCHEDULER_v1_0.md:64` lists it as *"CI edge-completeness guard."*
`kala_derivation_completeness_guard.py:22-24` makes the weaker but still-automated claim
`"Run as a script: ... (exit 1 on any hard completeness violation) / Used by: tests/..."`.

**(b) What actually executes it.**

`dag_edge_guard` — exactly one automated caller, `tests/test_dag_edge_guard.py:96-98`:

```python
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_live_registry_has_no_hard_violations():
    res = g.analyze()
```

`.github/workflows/ci.yml:344-372` is the only job that runs the sidecar suite. Its own comment
spans two separate remarks, about two different test files, spliced here for context — `:345-346`
states the general policy, `:347-348` is specifically about `test_a3_schema_smoke.py`, not about
`dag_edge_guard`'s own test:

> *"All tests here are self-contained (conn=None dry-run or `@pytest.mark.skipif(not DATABASE_URL)`
> for integration tests)."* (`:345-346`) *"...test_a3_schema_smoke.py uses pytestmark to skip when
> DATABASE_URL is absent — CI has no DB, so those 6 tests skip cleanly."* (`:347-348`)

The "6 tests" in the second remark are `test_a3_schema_smoke.py`'s, not `test_dag_edge_guard.py`'s —
correcting an earlier version of this citation that spliced the two into one continuous quote as if
both concerned the same test file. The finding itself does not depend on this comment: verified
directly instead, `test_dag_edge_guard.py:96-98` carries its own
`@pytest.mark.skipif(not os.environ.get("DATABASE_URL"))`, and CI's `ci.yml:344-372` job sets no
`DATABASE_URL` — so the guard's live check is independently confirmed skipped on every CI run,
regardless of what the neighboring comment says. The remaining four tests in that file exercise
the pure `evaluate()` against synthetic fixtures — they verify the *detector's logic*, never the
*live DAG*.

`kala_derivation_completeness_guard` — **zero** automated invocation. Its test file's own header
(`:4-5`) reads *"DB-free: exercises the pure evaluate() / evaluate_throughput_drift() functions
only"*, and it never calls `analyze()` or `main()`. Nothing anywhere runs the guard.

**(c) Demonstration of the absence — the exhaustive search.**

Ran over the whole worktree, excluding `.git`, `node_modules`, and `.pyc`:

```
grep -rn "dag_edge_guard\|kala_derivation_completeness" .
```

Every hit is one of: (i) the two modules themselves; (ii) their two test files; (iii) **prose** —
`00_ARCHITECTURE/*.md` reports, `SESSION_LOG.md`, and three SQL migration *comments*
(`419_...sql:21`, `413_...sql:6`, `asset_registry_seed.ts:1846`). A targeted second pass over
`--include=*.yml --include=*.yaml --include=*.json --include=*.sh --include=*.toml` returned **zero
hits**. All 14 files in `.github/workflows/` were enumerated; none references either module. No
Makefile, npm script, pre-commit hook, Dockerfile entrypoint, or scheduler config invokes them.

Therefore: *no mutation to any writer, and no drift in `asset_registry.depends_on`, can turn either
guard red automatically.* The gate's green is not produced; it is simply never asked for.

**(d) Adversarial refutation attempted, and why it failed.**

*Refutation 1 — "the docstring says 'Run as a script', so it is honestly a manual tool."* The same
docstring, two lines earlier, says *"as a CI gate"* and *"catches drift the moment"*. Both cannot be
true. And the ci.yml step whose scope contains the guard's live test is labelled **"Hard gate"** —
a reader of the CI config concludes the guard gates.

*Refutation 2 — "the pure `evaluate()` unit tests are sufficient coverage."* They cover the detector,
not the claim. `evaluate()` passing on fixtures says nothing about whether the live DAG is
edge-complete — which is the entire assertion.

*Refutation 3 — "this is theoretical; the drift never actually happens."* Refuted by the project's
own record. `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md:82` documents the guard *"currently exits 1 with
3 confirmed real HARD violations"* — found by a **manual** run during an audit, not by CI — and `:102`
records that the corrective migration 406 *"has NOT been applied to the live database"* at the time
of writing. That is precisely the drift the docstring claims is caught "the moment" it appears,
persisting undetected until a human went looking. §N.8's closing line applies verbatim: *"'It's
usually true' or 'nothing has broken yet' is not a substitute for a real detector."*

**Note for B-N8-LINT.** The §N.8 lint this arc is chartered to add would land in the same repo with
the same wiring options. If it is added without a CI job that fails on its violations, it reproduces
F-02 exactly — a lint asserting enforcement it does not perform. `SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md`
§7.5 already requires the lint to *"state its bounds in its own docstring"*; F-02 adds the harder
requirement: **wire it, and prove it red.**

---

### F-03 · `kala_derivation_completeness_guard` reports "no derivation-completeness gaps" while measuring chart *presence* over 3 hardcoded derivations

- **Class:** PROXY (scope overclaim in the emitted verdict)
- **Severity:** MEDIUM
- **File:** `pipeline/orchestrator/kala_derivation_completeness_guard.py:37-41`, `:44-59`, `:78-80`, `:119`
- **Routes to:** B-N8-SWEEPFIX

**(a) The claim.** The verdict a CI log or an operator reads, `:119`:

```python
    print("[kala_derivation_completeness_guard] OK — no derivation-completeness gaps")
```

Combined with the module's name, that asserts: the Kāla derivations are complete.

**(b) What actually computes it.** `evaluate()` (`:44-59`) subtracts two **sets of chart_ids**:

```python
        upstream_charts = charts_by_table.get(upstream_table, set())
        derived_charts = charts_by_table.get(derived_table, set())
        missing = upstream_charts - derived_charts
```

fed by `_charts_with_rows` (`:78-80`), which is `SELECT DISTINCT chart_id FROM {table}`. So the
measured property is: *does this chart appear at least once in the derived table?* Over exactly three
pairs, hardcoded at `:37-41` (`kala_obstruction`, `kala_darshana`, `kala_bhavishya`).

**(c) Demonstration.** A chart with **1** row in `kala_obstruction` where the derivation should have
produced 500 satisfies `chart_id ∈ derived_charts` and the guard prints its unqualified OK. The
falsifying state for the asserted claim ("the derivation is complete") is *reachable and never
consulted* — no row count, no expected-count, no substep-plan check appears anywhere in the module.
This is the same substitution SATYA-DĪPA's headline defect was: **row presence standing in for work
completed.** L3 Kāla has 12 `ka_*` assets (`CLAUDE.md §E`); three derivations are checked.

**(d) Adversarial refutation attempted — and the finding is NARROWED as a result.**

*Refutation — "the docstring is explicit that the finding it addresses is the 0-row derived table
(`:11-15`), so the module is honest about being a presence check."* **This refutation partially
succeeds, and the finding is narrowed accordingly.** The detector is not broken and it is not
unfalsifiable: `evaluate()` genuinely fires when a chart has upstream rows and an empty derived
table, which is the specific audit finding it was built for. What does **not** survive is the
**emitted verdict string** and the module name, which assert `completeness` over
`derivation-completeness` generally. A docstring is not what a CI log reader sees.

This is therefore a **wording-and-scope** finding, not a cannot-fail finding, and it is graded
MEDIUM rather than HIGH deliberately. `SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md` §7.5 makes the standard
explicit for exactly this class: *"a lint that overclaims its coverage is itself an §N.8 violation."*
The fix is correspondingly small — state the bound in the verdict (`"no empty-derived-table gaps for
the 3 checked derivations"`) — and a B-lane should not be sent to rebuild the detector.

*Secondary observation, not a separate finding:* `analyze()` (`:96-97`) computes `live_count` as
`SELECT count(*) FROM {derived_table}` — **fleet-wide, unscoped by chart** — and compares it to the
per-asset `asset_registry.asset_throughput`. The comparison is between incommensurable quantities.
It is explicitly informational and never gates (`:108-112`, per §N.4), so it asserts no PASS and is
not scored as a finding; it is noted so a B-lane touching this file does not mistake it for correct.

---

### F-04 · `_probe_ephemeris_engine` cannot return GREEN — the ephemeris service asset's health signal is unearned in either branch

- **Class:** CANNOT-FAIL GATE (inverse: always-red), on a wrong Julian Day and a wrong expected value
- **Severity:** HIGH
- **File:** `pipeline/orchestrator/service_probes.py:110-114`, `:130-157`, `:162-202`, `:204` · consumer `pipeline/orchestrator/asset_runner.py:332-366`
- **Routes to:** B-N8-SWEEPFIX

**(a) The claim.** The module docstring (`:4-5`): *"A service asset's 'build' = running its health
probe. … GREEN = all checks pass."* The consumer is strict — `asset_runner.py:332` promotes to
`state='lit'` and `asset_registry.service_health='healthy'` **only** on `status == "GREEN"`;
anything else calls `mark_asset_error` (`:366`). So GREEN is the sole gate on the ephemeris engine
being declared healthy.

**(b) What actually computes it.** Three checks, aggregated at `:204`:
`status = "GREEN" if not failures else ("degraded" if len(failures) < len(checks) else "down")`.

**(c) Demonstration — the probe was EXECUTED. It returns `degraded`.**

Run against the repo's own code and its installed Swiss Ephemeris:

```
EPHEMERIS status = degraded
message: "Rahu sign=3 (lon=74.4517°), expected sign 2 (Vrishabha) for 1984-02-05;
          Ketu sign=9 (lon=254.4517°), expected sign 8 (Vrischika) for 1984-02-05"
checks:  swisseph_importable      passed=true
         de441_position_query     passed=true   sun_lon=281.2217
         mean_node_rahu_invariant passed=false  rahu_sign=3 ketu_sign=9
```

`status != "GREEN"` ⇒ `asset_runner.py:366` ⇒ `mark_asset_error`. **There is no input under which
this probe promotes the asset.** Two independent defects produce that:

1. **The expected node sign is wrong.** `_FORENSIC_POSITION["expected_mean_node_rahu_sign"] = 2`
   (`:113`, "Vrishabha"). Independently recomputed: `swe.calc_ut(jd, swe.MEAN_NODE)` gives
   `74.4517°` → sign **3**, and Ketu at `254.4517°` → sign **9** (expected 8). Both sub-assertions
   fail, unconditionally, on every run. The comment at `:162-165` claims this is *"a real FORENSIC
   assertion, not the tautological '1 <= sign <= 12'"* — it is a real assertion, with a wrong
   expected value, i.e. an always-false one.
2. **The Julian Day is wrong by 33.77 days.** `_FORENSIC_POSITION["jd"] = 2445701.948264` is
   commented `# 1984-02-05 10:43 IST → UTC Julian Day` (`:111`). Recomputed: `swe.revjul` decodes it
   to **1984-01-02 10:45 UT**; the correct JD for 1984-02-05 05:13 UT is **2445735.717361**. This is
   load-bearing for check 2: on the code's JD the tropical Sun is `281.222°`, inside the probe's own
   `[255, 315]` window (`:136-137`) → passes; on the **correct** JD it is `315.588°`, **outside** the
   window → check 2 would fail too. So the one check that does pass, passes only because the date is
   wrong. Relatedly, `_FORENSIC_POSITION["expected_sun_sign"] = 10` (`:112`) is declared and
   **never referenced anywhere** in the repo — the fixture's own spec value is dead.

**Both branches of the consequence are §N.8 findings, and which one holds is a DB question this
audit could not answer** (see §5 — the Postgres MCP was unreachable, `ECONNREFUSED 127.0.0.1:5433`):

- **Branch A — the probe is dispatched.** Then the ephemeris service asset is permanently `error` /
  `service_health='degraded'`, and nothing in the corpus acts on that red (L0 is recorded ✓ SEALED,
  *"Infrastructure provisioned"*, `CLAUDE.md §E`). A gate that is always red and never consulted is
  as uninformative as one that is always green.
- **Branch B — the probe is not dispatched.** Then whatever marks the ephemeris asset healthy does so
  **without running the probe that is supposed to gate it** — the health signal has no detector
  behind it at all.

**(d) Adversarial refutation attempted, and why it failed.** *"The expected sign may be right under a
sidereal ayanamsha; the project's Rahu may be defined differently."* No: the probe calls
`swe.calc_ut(jd, swe.MEAN_NODE)` with **no** `FLG_SIDEREAL` and no ayanamsha set, so the value is
tropical, and the recomputation above uses the identical call. Sidereal would move the longitude
*further* from sign 2, not toward it. *"Maybe `degraded` is acceptable to some caller."* Refuted by
`asset_runner.py:332` — the branch is `if status == "GREEN"`, everything else is `mark_asset_error`.
*"Maybe the JD arithmetic is mine, not theirs."* Both directions were computed with `swe.julday` and
`swe.revjul` and are quoted above; the 33.77-day delta is reproducible in one command.

**Additional, weaker note (not scored separately):** `xx, _ = swe.calc_ut(jd, swe.SUN)` (`:144`)
discards the returned `retflag`, which is the only datum that distinguishes the DE441 ephemeris from
Swiss Ephemeris' built-in Moshier fallback. The check is named `de441_position_query`; a missing
`/app/ephe` would silently fall back to Moshier and still satisfy a 60°-wide window. The observed
`retflag=260` shows the flag is available and thrown away. Included here rather than as its own
finding because F-04's primary demonstration already condemns this check's arithmetic.

---

### F-05 · Fabricated `from_state` in emitted state-change events — including for rows no `UPDATE` touched

- **Class:** LITERAL
- **Severity:** MEDIUM
- **Files:** `pipeline/orchestrator/staleness.py:86-95` · `pipeline/orchestrator/asset_runner.py:707-719` · consumer `platform/src/lib/components/cockpit/v2/WorkflowView.tsx:137`
- **Routes to:** B-N8-SWEEPFIX (`staleness.py` in scope; the `asset_runner.py` site is the same defect — see F-01's scope note)

**(a) The claim.** An `asset.state_change` event asserts a specific transition: *this asset moved from
state X to state Y.* It is not internal telemetry — `WorkflowView.tsx:137` renders it verbatim into
the operator's activity log: `label = \`${e.asset_id}: ${e.from_state} → ${e.to_state}\``.

**(b) What actually computes `from_state`.** Nothing — it is typed in. Two sites, of differing
severity:

*Site 1 — `staleness.py:86-95`.* The `UPDATE` matches `state IN ('lit', 'service_ok')` (`:77`) and
`RETURNING`s only `asset_id` (`:78`), so the prior state is never read. The event then asserts:

```python
                emit_fn({
                    "type": "asset.state_change",
                    ...
                    "from_state": "lit",
```

An asset that was `service_ok` produces an event claiming it was `lit`.

*Site 2 — `asset_runner.py:707-719`, materially worse.* Same literal, plus the event is emitted for
**every** member of the downstream closure rather than for the rows the `UPDATE` actually changed:

```python
        downstream = compute_downstream_closure(cur, asset_id)
        if downstream:
            cur.execute(
                """UPDATE asset_throughput SET state = 'stale'
                   ... AND state IN ('lit', 'mature')""", ...)
        for d in downstream:
            emit_event({... "from_state": "lit", "to_state": "stale"})
```

**(c) Demonstration.** At site 2 the `UPDATE` is filtered to `state IN ('lit','mature')` while the
emit loop iterates the unfiltered `downstream` list. For any downstream asset in `dormant`, `error`,
`stale`, or `absent` — the normal condition of most of a chart's DAG mid-build — the row is **not
updated** and an event is nonetheless emitted claiming it transitioned `lit → stale`. The operator's
log shows a transition that did not occur, for an asset that was not in the claimed prior state.
Both halves of the claim are fabricated, and there is no code path on which either could read
correctly-false.

**(d) Adversarial refutation attempted, and why it failed.** *"`from_state` is cosmetic telemetry, not
a status/grade/PASS, so §N.8 does not reach it."* The consumer is a rendered operator-facing claim
about build state, and §N.8's subject is *"every status"* — a state-transition assertion is the
narrowest possible status claim. *"It is almost always actually `lit`."* At site 1, `service_ok` is a
live state written by the service-probe path (`asset_runner.py:335`), so the wrong case is reachable;
at site 2 the wrong case is the **common** case. And §N.8 names this exact excuse as inadmissible.

**The correct pattern already exists in the same pair of files** — and this is what makes the finding
cheap to close and hard to argue with. `staleness.py:61` documents it: *"Uses RETURNING to emit
events only for rows that actually changed"*, and `:78-83` implements it. Site 2 is the older sibling
that does not. Only `from_state` remains unmeasured at site 1.

---

### F-06 · `panchanga_day_runs` is a decorative `passed` field, and the probe's verdict does not aggregate the checks it reports

- **Class:** TAUTOLOGY (the field) + PROXY (the aggregation)
- **Severity:** LOW-MEDIUM
- **File:** `pipeline/orchestrator/service_probes.py:92-105`, `:11-13`
- **Routes to:** B-N8-SWEEPFIX

**(a) The claim.** A per-check `passed` boolean, reported inside the probe result that gates the
panchanga service asset, and aggregated into `status`.

**(b) What actually computes it.** `:98`:

```python
        checks.append({"check": "panchanga_day_runs", "passed": result is not None})
```

`panchanga_day` is annotated `-> "Panchang"` (`panchang_engine/__init__.py:380`) and has no
`return None` path, so `result is not None` cannot evaluate False. The real detector for "does it
run" is the surrounding `try/except` (`:99-101`), which appends to `failures`; the `passed`
expression adds nothing.

**(c) Demonstration, in two independent parts.**

1. *The field cannot read False.* Executed the probe: `panchanga_day_runs passed=true`, `status=GREEN`,
   `message="All checks passed"`. The only value that would falsify it is a `None` return the callee's
   contract does not produce.
2. *Even if it could, nothing would consume it.* `status` is computed from the `failures` list
   (`:103`), never from `checks`. Check 3 is the **only** check in the file that sets `passed: False`
   without also appending to `failures` (checks 1 and 2 do both, `:66-67` and `:84-85`). So a
   `passed: False` there yields `status = "GREEN"` and `message = "All checks passed"` —
   the aggregate verdict contradicting the checks it ships. Per `asset_runner.py:332`, GREEN promotes
   the asset to `lit`. The verdict measures a proxy (the failures list) for its claim (all checks
   passed), and the two are wired apart at exactly one point.

**(d) Adversarial refutation attempted, and the finding NARROWED.** *"The check does measure something
real — that `panchanga_day` doesn't raise."* Accepted, and the finding is narrowed to what survives:
the **`passed` field** is unearned (a tautology whose value no code consumes), while the `try/except`
around it is a genuine detector. This is why the severity is LOW-MEDIUM and not HIGH: the *probe* is
not blind, the *field* is decorative. Note the file already states the correct standard against
itself at `:133` — *"This is a real assertion, not just 'no exception raised'"* — describing check 2
while check 3 is exactly the pattern that comment rejects.

**Third element, reported and deliberately NOT scored — the 5-condition docstring.** `:11-13` states
GREEN requires five conditions per `UNIFIED_ASSET_REGISTRY_ARCHITECTURE_v1_0.md §D`, including
*"(4) endpoints reachable; (5) supported domain declared"*, and only three are measured. I attempted
to keep this as a finding and **refuted it myself**: `bg_panchanga` and `bg_ephemeris_engine` are
in-process Python libraries with no endpoint, so (4) is genuinely N/A, and the docstring's own
*"where applicable"* qualifier covers it. Condition (5) is a registry-declaration check that would be
trivial to add, but asserting a violation would require establishing that a `supported_domain` field
exists and is meaningful for these two assets, which I did not establish. **Dropped — see §4.**

---

## §2 — PART B · Codebase-wide (T4.4)

**Provenance, stated up front.** §§2.1, 2.3, 2.4 and 2.5 are the deliverables of four parallel
read-only sub-auditors, each of which traced candidates to source and self-refuted them inline.
**I did not personally re-derive these**, and one caveat applies throughout: my own attempt to query
production failed (`mcp__postgres__query` → `ECONNREFUSED 127.0.0.1:5433`), so every live row count
below is a sub-auditor's, not independently confirmed by me. Each is a specific, falsifiable number —
which is exactly what a spot-refutation should target first. §2.2 is mine. Bounded gaps *within*
this swept ground are listed in §5.1.

### §2.1 — Known-member writers: `bo_pramana_mapa`, `ga_nakshatra`, `bo_chart_gestalt`

**Provenance and its limits.** This subsection is the deliverable of a dedicated read-only
sub-auditor, which traced each candidate to source, self-refuted each, and corroborated against live
DB rows. **I did not personally re-derive these**, and one provenance caveat must be recorded: my own
attempt to query production failed (`mcp__postgres__query` → `ECONNREFUSED 127.0.0.1:5433`), so the
live row counts below are the sub-auditor's, not independently confirmed by me. Every one is a
specific, falsifiable number — which is exactly what a spot-refutation should target first.

All six candidates the brief named (§7.1, §7.2) are **CONFIRMED**. Five siblings were found in the
same three files. Findings are ordered as the sub-auditor graded them; F-17 is explicitly the weakest.

| ID | Signal | file:line | Class |
|---|---|---|---|
| F-07 | `lel_zero_leak_pass` | `bo_pramana_mapa.py:219-224` | PROXY |
| F-08 | `pillars_meet_reachability_pass` | `bo_pramana_mapa.py:226-228` | TAUTOLOGY |
| F-09 | `trap2_narration_leak_count` | `bo_pramana_mapa.py:273-278` | LITERAL |
| F-10 | `divergent_flagged_count` | `bo_pramana_mapa.py:259-262` | LITERAL |
| F-11 | `verification_pass_status='PASS'` | `ga_nakshatra.py:87` | LITERAL |
| F-12 | `verdict_class` + `confidence` stored in writer | `bo_chart_gestalt.py:209-223` | DOCTRINE + PROXY |
| F-13 | `msr_no_threshold_drop_flag` | `bo_pramana_mapa.py:265` | TAUTOLOGY |
| F-14 | `trap1_authority_inversion_count` | `bo_pramana_mapa.py:162-169` | PROXY |
| F-15 | `fragility_class="multi_ayanamsha_tested"` | `bo_chart_gestalt.py:333-338` | LITERAL |
| F-16 | `linking_mechanism="domain_tension"` | `bo_chart_gestalt.py:269-274` | LITERAL |
| F-17 | `contested_areas` note "genuinely balanced" | `bo_chart_gestalt.py:294-320` | PROXY (weakest) |

**F-07 · `lel_zero_leak_pass` — PROXY.** Asserts no Life-Event-Log leakage into the deterministic
base. Actually counts `constituent_facts_array` gaps and **never reads `life_events`/LEL at all**.
Live disproof: `bo_upaya.py` does read `life_events` and writes `milestone_event_ids`; chart
`482012f1`'s `bodha_rm_dasha_windowed_prescriptions` carries 5 real LEL `event_id`s on a build whose
scorecard still reads `lel_zero_leak_pass=true`. The claim and the measurement have no overlap.

**F-08 · `pillars_meet_reachability_pass` — TAUTOLOGY.** Expression is `msr_count > 0`, but
`msr_count == 0` already **raises ~160 lines earlier**, so no DB state reaches this line with a
falsifying value. Live: `true` on all three sampled charts. The repair pattern is three lines below
in the same dict — `no_pre_answer_pass` is `None`.

**F-09 · `trap2_narration_leak_count` — LITERAL `0`.** The code's own comment concedes it *"can never
report a real leak."* Aggravating factor: the zero is quoted as cleanliness evidence in
`PLAIN_LANGUAGE_INSTRUMENT_MAP.md:344` — the unearned signal has already been consumed as proof.

**F-10 · `divergent_flagged_count` — LITERAL `0`.** `divergent_flagged` is a real enum elsewhere in
the schema; the count query was simply never written. Unreachable-false.

**F-11 · `ga_nakshatra` `verification_pass_status='PASS'` — LITERAL. The strongest finding in this
subsection, and the purest §N.8 violation in the corpus.** An unconditional string constant on every
row (6 emitters × 5 ayanamshas, plus the cross-ayanamsha substep), placed **after `**r`** so it
overrides any status a caller computed. The only real check, `_forensic_gate`, covers **one body
(Moon)** and runs **only for chart `482012f1`** — every other chart receives zero verification and the
identical `'PASS'`. Live: **3,955 `chart_facts` rows** carry it.

> **Second-order defect, and it cuts the other way — surface this to `DVA`.** `'PASS'` is outside the
> documented vocabulary (`test_verification_pass_status_vocab.py`, `ganita/types.ts:45`), and
> `envelope.ts:1622-1625`'s grounding-score check matches only lowercase `'pass'` /
> `'two_pass_verified'`. So these 3,955 rows score as **UNGROUNDED in production**. The literal is
> simultaneously an unearned green at the writer and an unearned *red* at the serving layer. A naive
> fix that merely lowercases the constant would convert 3,955 unverified rows into
> production-"grounded" ones — **strictly worse than the current state.** The §N.8-correct fix is
> `NULL` plus a real detector, and the two changes must land together.

**F-12 · `bo_chart_gestalt` stores a verdict — DOCTRINE VIOLATION + PROXY.** The writer's own
docstring (`:19-21`) states it *"NEVER stores verdicts, computed values, or interpretive text."* It
stores `verdict_class` and `confidence`, derived from a single `DISTINCT ON` row per domain. Live:
the career domain reads `"strong_positive"` while holding **136 benefic vs 632 malefic** signals — the
verdict is not a summary of the evidence, it is the first row of it.

**F-13 · `msr_no_threshold_drop_flag` — TAUTOLOGY.** Same already-guaranteed `msr_count > 0`
expression as F-08.

**F-14 · `trap1_authority_inversion_count` — PROXY.** Measures citation-array *presence*, not value
*agreement* — and value agreement is the actual §N.5 trap (an L2 signal restating an L1 computed
value as its own). The count cannot detect the thing it is named for.

**F-15 · `fragility_class="multi_ayanamsha_tested"` — LITERAL.** A per-ayanamsha writer is
structurally incapable of comparing across ayanamshas. Live disproof: the health verdict **flips**
between `strong_challenge` and `neutral` across lahiri/raman — and both rows are stamped `"tested"`.

**F-16 · `linking_mechanism="domain_tension"` — LITERAL.** The two poles are selected by two
independent chart-wide queries that never test for domain overlap, so the asserted linking mechanism
is never established.

**F-17 · `contested_areas` note "genuinely balanced" — PROXY (weakest in this register).** The
`HAVING` clause requires only that both valence counts exceed zero. Live: **136 vs 632** is served as
"balanced". Included because the demonstration is concrete, but graded lowest — the fix is a threshold,
not a new detector.

### §2.2 — `mi_darshana._substep_views_verify` — a declared verification substep that cannot fail

- **ID:** F-18 · **Class:** CANNOT-FAIL GATE · **Severity:** MEDIUM
- **File:** `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py:72`, `:84-85`, `:477-499`
- **Routes to:** B-N8-FIX (writer-layer fix) · **Independently verified by this lane (mine).**

**(a) The claim.** `SubStep(key="views_verify", label="verify views")` (`:72`) is 1 of `mi_darshana`'s
3 declared substeps; the module header (`:9`) describes it as *"count-check against views and log
gaps."* Its completion asserts the views were verified.

**(b) What actually computes it.** `:477-499` iterates four `vw_mimamsa_*` views, and on any failure:

```python
            except Exception as exc:
                counts[view] = f"ERROR: {exc}"
```

then returns a successful `WriterResult` with `notes=f"view counts: {counts}"`. There is no
assertion, no raise, no non-zero-rows requirement, and no comparison against an expected count.

**(c) Demonstration.** Drop or break any of the four views: the exception is caught, the string
`"ERROR: ..."` is placed in a log line and a notes field, and the substep **succeeds**. No input
state makes this substep fail. `counts` is never read by any assertion — grep for `views_verify`
returns only the declaration, the dispatch, the implementation, and the log call.

**(d) Why this compounds F-01 and is not merely cosmetic.** SATYA-DĪPA's promotion predicate now
asks the writer's own `plan_substeps(ctx)` whether the plan finished
(`asset_runner.py:626-643`). `views_verify` counts toward that plan. So "the substep plan is
complete" — the claim SATYA-DĪPA made load-bearing for `lit` — is partly satisfied by a step that
verifies nothing. The unearned signal is now inside the detector that was built to replace an
unearned signal.

**(e) Adversarial refutation attempted, and why it failed.** *"It is a logging step, not a gate — the
docstring says 'log gaps'."* Its declared label is `"verify views"` and its key is `views_verify`;
both assert verification, and its completion feeds the plan-completeness predicate. *"An
ERROR string in the notes is visible to an operator."* A value buried in a free-text notes field, on
a substep reporting success, is precisely the "clean-looking default" the brief's §7.1 forbids.
*"Maybe the views cannot fail."* They are materialized/derived objects dependent on migrations; a
missing view is the ordinary post-migration failure mode, and the code's own `try/except` exists
because its author expected it.

---

### §2.3 — TypeScript serving layer (`platform-mcp/src/**`, `platform/src/**`)

Sub-auditor deliverable; each candidate self-refuted inline. Not personally re-derived by me.

| ID | Signal | file:line | Class | Sev |
|---|---|---|---|---|
| F-19 | `synthesis_gate` / `fully_accounted` | `dossier.ts:437-499`, `registry_bridge.ts:706-800` | TAUTOLOGY + LITERAL + RELABEL | **CRITICAL** |
| F-20 | `freshness.stale` | `kala_envelope.ts:248-272` | LITERAL | HIGH |
| F-21 | `density_contract` machine-backfill | `descriptor_defaults.ts:396-415` | PROXY | **HIGH (§N.6)** |
| F-22 | `orientation_ok` | `registry_bridge.ts:1859-1867` | PROXY | MED |
| F-23 | `planning_confidence` / `fallback_used` / `parsing_success` | consult `route.ts:711-737` | LITERAL | MED |
| F-24 | `verified` read-after-write | `conversation_writer.ts:16-87` | TAUTOLOGY | MED |
| F-25 | `verification_pass_status` → `epistemic.grade` | `envelope.ts:1622-1626`, `:73`, `:819-825` | RELABEL (inherited) | MED |

**F-19 · `synthesis_gate` / `fully_accounted` — BLOCKED is unreachable by construction.**
`gateOpen = accounted === slice_size`, where **both operands are read from the same precompiled JSON
bundle** — so the comparison cannot fail. All four shipped bundles were confirmed exact-match. Two
sinks additionally hardcode the literal `"100%"` regardless of the computed pct. The decisive
evidence is internal: the **paged sibling** at `dossier.ts:721` computes the correct conjunct
(`page.done && accounted === slice_size`), proving the codebase knows a real gate needs a second,
independent term. The receipt path dropped it.

**F-20 · `freshness.stale` — LITERAL `false` estate-wide.** `stale` can only become true if
`params.staleAfter` is supplied; grep confirms **zero** production call sites pass it across all
eight `kala_views/*.ts`, while all three provenance fields are `null`. Per §N.8 the correct value is
`null`. `KalaCoverageEntry`, in the same file, already models absence correctly (`'not_in_corpus'`).

**F-21 · `density_contract` machine-backfill — a §N.6 governance false-green, and the most
structurally serious of the serving findings.** `empty_reason` / `paginated` are derived from an
archetype label and the mere presence of a parameter name — **never from the handler**. About
**70 of 83** capability URIs are machine-stamped. Worked example: `get_positions.ts` is stamped
`empty_reason: true` and contains **zero occurrences of `empty_reason`** anywhere in the file. The
compliance harness compounds it: `generate_tool_census.ts`'s `scoreA4` grades all of these
"§N.6 enforced" purely from `typeof`/shape checks **on the backfilled object**, never inspecting
source — unlike its own sibling `scoreA3`, which at least greps source text. **The §N.6 CI gate is
therefore satisfied by the derivation rather than by the implementation** — precisely the violation
`CLAUDE.md §N.6` names: *"a capability that claims `density_contract` but ships no `empty_reason`
discipline behind it."*

**F-22 · `orientation_ok` — PROXY on the B.11 enforcement signal.** Named as *the* Whole-Chart-Read
enforcement signal; actually means only "the L2 `query_ucd` call did not throw." No assertion on
contents. An unbuilt chart returns 200 with empty context and still reads `orientation_ok: true`.

**F-23 · Hardcoded planner metrics in the consult route.** `pipeline_planner.ts` computes real
values; the consult route **discards them** and writes constants. Consequence: consult-route traffic
can never register as low-confidence in `AnalyticsTab`'s metric, by construction.

**F-24 · `conversation_writer` `verified` — TAUTOLOGY.** `verified = dbCount >= messageIds.length`
where `dbCount` is **not filtered by id**, so it holds by construction. The inline comment concedes
the `>=` was loosened.

**F-25 · `verification_pass_status` → `verified_fraction` → `epistemic.grade` — RELABEL, and the
cross-reference that matters most in this register.** The serving layer turns a per-row DB column
into response-level *"X% confirmed"* prose — a genuine relabel. The sub-auditor could not trace the
writer-side origin of `'two_pass_verified'`. **It is very likely the same root cause as F-11 seen from
the other side:** F-11 establishes that `ga_nakshatra.py:87` stamps a literal `'PASS'` on 3,955 rows
with no verification, and that `envelope.ts:1622-1625` matches only lowercase `'pass'` /
`'two_pass_verified'`. F-11 and F-25 must be dispositioned **together**; fixing either alone can move
rows across the grounded/ungrounded boundary in the wrong direction. **Flagged as one joint work item.**

### §2.4 — CI / gates / guards

Sub-auditor deliverable. **Methodology caveat, disclosed:** `platform/node_modules/.bin/vitest` was
absent in that worktree, so **F-33 (PB-2) is static-only** — read, not executed.

| ID | Gate | file | Class | Sev |
|---|---|---|---|---|
| F-26 | `hard_gates_check.sh` | `platform/scripts/**` | CANNOT-FAIL | **HIGH** |
| F-27 | `icr_weekly_scan.yml` | `.github/workflows/` | CANNOT-FAIL | **HIGH** |
| F-28 | `secret_scan.sh` exclusion zone | `platform/scripts/governance/` | PROXY (scope hole) | **HIGH** |
| F-29 | `schema_validator.py` CI claim | `.github/workflows/ci.yml` | PROXY | MED |
| F-30 | `chat-v2-ci.yml` swallowed failures | `.github/workflows/` | CANNOT-FAIL | MED |
| F-31 | `chat-v2-ci.yml` 4 × "Gate: HARD pre-merge" | `.github/workflows/` | CANNOT-FAIL (no-op) | MED |
| F-32 | `deploy.yml` web smoke → 100% traffic promote | `.github/workflows/` | PROXY | MED |
| F-33 | **PB-2 byte-equality gate** | `canonical_serialization_golden.test.ts` | PROXY (**reclassified**) | MED |
| F-34 | **PB-3 §G item 9 — no-auto-promotion** | *(absence)* | NO-DETECTOR-EXISTS | MED |
| F-35 | **MCP post-deploy smoke** | `.github/workflows/deploy.yml` | PROXY-bounded | MED · **CROSS-REF A3** |

**F-26 · `hard_gates_check.sh` — claims "returns 1 if any RED"; contains zero `exit` statements.**
Confirmed by live run: **exit=0 always**. 8 of 15 gates have no RED branch at all. A gate script that
cannot return non-zero cannot gate.

**F-27 · `icr_weekly_scan.yml` — CANNOT-FAIL.** `--dry-run` suppresses the only non-zero exit path.
The step also points at a hardcoded, nonexistent MSR file path — but `--synthetic` short-circuits
path resolution before that second defect is ever reached, so only the `--dry-run` suppression is
demonstrated to be load-bearing; the nonexistent-path defect is real but not independently proven to
also cause the cannot-fail behavior on its own. One demonstrated reason it can never go red, not two.

**F-28 · `secret_scan.sh` excludes `00_ARCHITECTURE/` — and a live plaintext production DB password
sits in the excluded zone.** The scanner's own detector logic is sound (rejected as a finding, §3);
the defect is the **exclusion scope**, which creates a blind region the corpus actively writes into.
**Note on handling:** the sub-auditor routed this **specific credential** to `DVA` directly as an
urgent item, separate from this register. It is recorded here as a finding for completeness only —
**this register is not the remediation channel for a live secret**, and the credential itself is
deliberately not reproduced in this document.

**F-29 · `schema_validator.py` — ci.yml's claim vs. live behaviour.** ci.yml states the validator
*"exits 0, Gate hardened"*; a live run shows **43 violations / exit=3**, with **no whitelist
mechanism**. An entire MED/LOW severity band therefore passes green permanently. (The
`drift_detector.py` *mechanism* is GENUINE — see §3 — only ci.yml's comment misdescribes its exit-3
semantics.)

**F-30 / F-31 · `chat-v2-ci.yml`.** Several steps swallow failures via `|| echo` and `2>/dev/null`
**despite their target paths existing** (so the swallowing is load-bearing, not defensive). Separately,
its four stages labelled *"Gate: HARD pre-merge"* are **pure no-ops** against verified-absent targets.

**F-32 · `deploy.yml` web smoke.** Probes a trivial static health route and then promotes **100% of
traffic**; the second probe hits an unrelated hardcoded URL. The promotion is gated on a signal that
does not exercise the deployed application.

**F-33 · PB-2 byte-equality gate — the register's inherited wording is REFUTED; the row survives
reclassified.** The brief and prior artefacts describe this as *"a 'byte-identical' claim with no byte
comparison behind it"* (`CLAUDE.md §N.8` instance 3). **That is false as worded:**
`canonical_serialization_golden.test.ts:327-335` performs a real `toBe()` comparison and is
mutation-sensitive — proven by changing `route_writer_adapter.ts:50`'s body shape, which reddens the
test. **What is actually wrong** is narrower and still a genuine §N.8 violation: the comparison is
against a **test-owned reimplementation** (the "reducer path", explicit in the test's own header),
**never against the actually-shipped `s1LiveAdapter.ts`**; and its scope is **one inline fixture**, not
the 12-file corpus. Already disclosed in
`FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md`. **Recommendation: amend the wording in `CLAUDE.md
§N.8` instance 3 rather than delete the row** — deleting it would lose a real finding, but leaving the
current wording standing means the doctrine cites an example that does not hold as stated.

**F-34 · PB-3 §G item 9 "no auto-promotion" — CONFIRMED absence of any detector.** Exhaustive grep
found **zero** real detector. The single test touching the surface carries **no 401/403 assertion** and
is `describe.skip` in CI. **Recommendation: downgrade PB-3 item 9 from VERIFIED-FIXED to
VERIFIED-BY-INSPECTION-ONLY** in its source artefact — the brief's own §7.4 already predicted exactly
this ("true by inspection only, with no dedicated detector or CI test … By this brief's own doctrine
that is an unearned green").

**F-35 · MCP post-deploy smoke — PROXY-bounded. CROSS-REFERENCE: lane A3 owns the can-fail proof.**
Static review only, deliberately not duplicating A3's live-mutation work. Two bounded gaps: it
**never confirms traffic actually moved** after promotion — which *is* the INF-2 failure mode (a green
pipeline that skipped promotion) — and it asserts **HTTP status only**, so a `200` carrying a JSON-RPC
**error body** passes. Counted once here; A3's verdict governs.

---

### §2.5 — Python build-layer writers (`ga_*` / `bo_*` / `ka_*` / `ph_*` / `mi_*`)

Sub-auditor deliverable; each candidate self-refuted inline. Not personally re-derived by me.

| ID | Signal | file:line | Class | Sev |
|---|---|---|---|---|
| F-36 | `_verify_vimshottari` → `two_pass_verified` | `ga_writers/ga_dashas_writer.py:661-675` | TAUTOLOGY | **HIGH** |
| F-37 | `_verify_yogini` / `_verify_ashtottari` / `_verify_naisargika` | `ga_writers/ga_dashas_writer.py:678-738` | TAUTOLOGY | **HIGH** |
| F-38 | 11 × hardcoded `verification_pass_status: "pass"` | 5 `bo_*` writers | LITERAL | **HIGH** |
| F-39 | `points_only_assertion: True` | `bo_drishti.py:244` | TAUTOLOGY | MED |
| F-40 | `source_corroboration_count_by_text` | `bo_laksana.py:2204` | PROXY (B.10) | MED |

**F-36 · `_verify_vimshottari` stamps `two_pass_verified` after a verification that does nothing for
every chart but one.** Pass 2 — the FORENSIC birth-lord check — runs **only if
`chart_id == CANONICAL_CHART_ID`**. Pass 1 computes its comparison and its mismatch branch is a bare
`pass` statement: the discrepancy is calculated and then discarded. So any non-native chart with
arbitrarily wrong `duration_days` still receives the `two_pass_verified` stamp. **Reachable today** —
other-native builds are live (Abhinandan `1c826d5a`).

**F-37 · Three dasha verifiers are closed loops.** Each checks only lord-name membership against a
set built from **the same constant the builder drew the lord from** — a comparison that cannot fail
on any builder-producible output. The invariants their names imply (sum-of-years, sequence) are never
computed. **The decisive counter-evidence is in the same file:** `_verify_kalachakra` (`:817-821`)
states outright that its check is *"shallow structural … does not warrant `two_pass_verified` …
never stamp a tier the check didn't earn"* and correctly demotes itself to `"single"`. The estate's
own correct standard is written down, one screen away, and these three do not follow it.
(`_verify_chara` is the weaker PROXY sibling — a separate literal reference set, same unimplemented
invariants.)

**F-38 · Eleven hardcoded `"verification_pass_status": "pass"` sites — and the token means opposite
things in the two systems that read it.** Across `bo_yantra_mechanism.py`, `bo_cgm_paths.py`,
`bo_cgm_motifs.py`, `bo_upaya.py`, `bo_cdlm_summary.py`. `"pass"` is **absent** from `formulas.py`'s
`VERIFICATION_RESCALE` map (which knows only `two_pass_verified` / `single_pass` /
`documented_approximation`), so server-side it silently falls through `.get()` to the **lowest tier
(0.60)** — while `envelope.ts:1622-1626` counts `s === 'pass'` as **VERIFIED**, promoting it to
`epistemic.grade = 'ganita_fact'`. **The same literal simultaneously scores worst-case in one
consumer and best-case in the other. That divergence is itself the proof that nothing measures it.**

> **Three-way cross-reference — F-11 · F-25 · F-38 are one defect seen from three sides.** F-11:
> `ga_nakshatra.py:87` stamps literal `'PASS'` (uppercase) on 3,955 rows with no verification. F-38:
> eleven `bo_*` sites stamp literal `'pass'` (lowercase). F-25: `platform/src/lib/retrieval/envelope.ts`
(disambiguated — a second, unrelated `envelope.ts` exists at `platform-mcp/src/generated/`) relabels the column into
> user-facing *"X% confirmed"* prose, matching lowercase only. Net effect: the **uppercase** literals
> read as *ungrounded* and the **lowercase** literals read as *grounded* — and **neither was verified
> by anything.** The grounded/ungrounded boundary in production is currently drawn by string casing.
> **These three must be dispositioned as a single work item.** See §6.2 Q2.

**F-39 · `points_only_assertion: True` — a flag whose own auditor query can never return a row.** The
sole writer hardcodes `True` (`bo_drishti.py:244`). The named auditor query
(`test_b6_eval_harness.py:411`, `WHERE points_only_assertion = FALSE`) is therefore structurally
guaranteed to return zero rows forever. The migration comment names `bo_pramana_mapa` as this flag's
auditor — **join this with §2.1's `bo_pramana_mapa` findings when fixing.**

**F-40 · `source_corroboration_count_by_text` is a fabricated count (B.10).** A two-valued map —
`5 if two_pass_verified else 2` — derived from L1's *verification tier*, **not** from the
`classical_sources_array` populated two lines above, which is never `len()`'d. An empty array still
reports `2`; a nine-source array reports the same `2` or `5`. The sibling field
`source_corroboration_count_by_verse: None` proves `None` was available and was deliberately not used
here.

**Medium / judgment calls, reported not scored:** `bo_laksana.py:1243` `verification_certainty: 0.778`
(a literal, but documented and conservative — the counter-argument substantially survives);
`bg_concordance.py:207-209` `match_confidence` saturates falsely at n=5 but is **NOT-REACHED** (no TS
consumer found); `mi_sambandha.py:97-98` fixed ±0.10 CI width (the n-gate itself is genuine).

---

## §3 — Rejected candidates (the sweep discriminates)

These were examined and are **NOT findings**. Three are the *correct pattern* a B-lane should copy —
listing them is how this register avoids sending builders to "fix" working detectors.

| Candidate | Verdict | Why |
|---|---|---|
| `deps_unsatisfied` (`asset_runner.py:44-89`) | **GENUINE** | Correct **allowlist** (`state != 'lit'` → unsatisfied). This is the pattern F-01's denylist should have used. |
| Service-probe consumer (`asset_runner.py:332`) | **GENUINE** | Strictly `if status == "GREEN"`; every other status → `mark_asset_error`. No partial-credit promotion. |
| `_guard_state_write` (`asset_runner.py:241-272`) | **GENUINE** | Real detector for a real failure (an `UPDATE` matching 0 rows), with loud logging and recovery. |
| `_check_writer_registry_gaps` (`runner.py:120-146`) | **GENUINE** | Genuinely compares the Python `@register` set against `asset_registry.has_writer`; can and does fail the run. |
| `dag_edge_guard.evaluate()` (`dag_edge_guard.py:137-186`) | **GENUINE** *logic* | The detector is sound and unit-tested. F-02 is about it never being **run**, not about it being wrong. |
| `kala_derivation_completeness_guard.evaluate()` (`:44-59`) | **GENUINE** *logic* | Genuinely fires on upstream-rows-but-empty-derived. F-03 is scoped to the verdict **string**. |
| `nak_5ay_consistency` (`ga_nakshatra.py:286-296`) | **GENUINE** | Lossy, but never falsely green. |
| `two_pass_verified_pct`, `documented_approximation_pct`, `msr_citation_ref_coverage_pct`, `unresolved_constituent_facts_count`, `l1_assets_projected_*` (`bo_pramana_mapa`) | **GENUINE** | Real SQL aggregates over real data. |
| `no_pre_answer_pass`, `ledger_independence_pass`, `discovery_not_fabricated_pass` = `NULL` (`bo_pramana_mapa`) | **ALREADY COMPLIANT** | §N.8-correct today: no detector ⇒ `NULL`, not green. **Cite these as the repair pattern for F-07/F-08/F-13.** |

**Serving layer — rejected as GENUINE.** `deriveEpistemicGrade`; `get_yoga_dosha.ts`'s catalog-only
handling (**reference implementation** for §N.6 — copy this); `graha_portrait.ts` completeness;
`c2ProtocolAdapter.verificationToGrade`; `cockpit/stats/route.ts` `service_health`;
`router/classifier.ts` confidence; `mcp_catalog_version.ts` (when a version is supplied);
`noLelCalibrationMaturity()`; and **`dossier.ts:721`'s paged `synthesis_gate`** — which is not merely
rejected but is the **contrast evidence** that condemns F-19.

**CI / guards — rejected as GENUINE.** `sc_pointer_validation.ts`; `secret_scan.sh`'s **detector
logic** (only its exclusion scope is at fault — F-28); `drift_detector.py`'s **mechanism** (only
ci.yml's comment about its exit-3 semantics is wrong — F-29); `msr_referential_integrity.py
--self-test`; `check_fact_category_pinning.py` (the #840 lint **B-N8-LINT should mirror**);
`whitelist_resolution_invariant.test.ts` / `parity_check.test.ts`; the `density-census` job;
`naming_lint.py`; `coverage_gate.py`; `assert_no_native_literal.sh`; `edge_security_smoke.sh`;
`reconciliation-cadence.yml` (**honestly discloses that it cannot fail** — disclosure is the §N.8-
compliant move); ci.yml's `icr-pr-gate` job (honestly scoped); `no_hardcoded_concept_lists.ts`
(self-disclaims as report-only).

**Python writers — rejected as GENUINE.** `bo_upaya.py:1120` `inputs_complete`;
`bo_pratijna.py._grade_to_status`; `ka_jivana_parva.py._assign_quality`; `bo_cgm_paths.py:179`
`is_final_dispositor`; `ga_dashas_writer._verify_mudda`; **`ga_dashas_writer._verify_kalachakra`** —
which is not merely genuine but is **the estate's own correct-standard exemplar** and the contrast
evidence condemning F-37; `mi_sambandha` / `mi_pramana` grade gate; `bo_karanajala.py`
`is_cross_subsystem`.

---

## §4 — Dropped candidates (examined, not demonstrable — deliberately not padded)

The lane's instruction was to never pad the register. These were real suspicions that failed the
evidentiary bar, and are recorded so no one re-spends the effort.

1. **`dag_edge_guard` dynamic-SQL blind spot.** `_reads()` (`:124-134`) regex-matches only literal
   `FROM`/`JOIN <name>`, so f-string table names are invisible. I traced the two real instances —
   `bo_pramana_mapa.py:84` (`bodha_msr_signals`, `bodha_cdlm_cells`, `bodha_rm_resonances`,
   `bodha_convergence`) and `mi_darshana.py:487` (four `vw_mimamsa_*` views). **All four
   `bo_pramana_mapa` tables also appear in literal SQL in the same file** (grep counts 7/1/1/1), so
   the guard does see them; and views have no `target_table` producer, so they could not yield a HARD
   violation anyway. The blind spot is real; **I could not demonstrate a single missed edge, so it is
   not a finding.**
2. **`service_probes.py` 5-condition docstring** (`:11-13`). Self-refuted — see F-06's closing note.
3. **`ph_nimitta` neutral-default fallbacks** (`ph_nimitta.py:745-746`): `pratijna_grade` defaults to
   `5.0` and `pratijna_status` to `'conditional'` when absent, feeding `_promise_lift`. The
   BA-Phase-2.5 defect is **closed** (`:475-476` now reads a real join). Whether coercing absence to a
   mid-scale value violates §N.8's "never a clean-looking default" needs the downstream provenance
   traced, which I did not do. **WEAK — not scored.**
4. **`_WRITER_GAP_MODE` fails open on a typo** (`runner.py:110`, `:673`): only the exact string
   `"enforce"` aborts; `"enforcee"` silently degrades a hard gate to a log line. Contrast
   `_DEP_ASSERT_MODE` (`asset_runner.py:41`), which fails **safe** on a typo. A configuration-robustness
   asymmetry, not a detector-less signal. **Not scored.**
5. **`staleness.py` swallowed propagation failure** (`:107-114`): logs and returns normally, so a
   failed staleness pass is invisible to the run verdict. Folded into F-05's site analysis rather than
   scored separately — the fabricated `from_state` is the demonstrable half.
6. **`/api/health` `status: "ok"`** (`health/route.ts`): a literal, but that is **correct
   liveness-probe semantics**. Not a finding.
7. **`tap-ci.yml`'s exit-0 self-skip convention** and **`brahma-conductor.yml`'s "SMOKE TEST: PASS"
   echo literals**: both graded LOW by the sub-auditor. The first is **disclosed** in its own config —
   disclosure is the §N.8-compliant response to an unenforceable check — so it is not scored. The
   second is a pure `echo` with no assertion behind a PASS string; it is recorded here rather than as
   a finding only because nothing consumes it. **B-N8-LINT should still catch this shape.**
8. **Serving-layer weak candidates, named not asserted:** `register_server_info.ts:58`
   stale-on-omitted-version; `AssetNode.tsx`'s `service_ok → 'complete'` UI relabel; and the §N.6
   density sentence at `platform/src/lib/retrieval/envelope.ts:860-862` (same file as F-11/F-25/F-38's
   check, not the unrelated `platform-mcp/src/generated/envelope.ts`), which is wired but has **zero production call sites
   passing `hasDensityContract`** — it would inherit F-21's false-green the moment it is wired, so it
   is a **pre-emptive** note for whoever wires it.
9. **CI weak candidates, named not asserted:** `chat-v2-smoke.yml` secret-provisioning status
   (unobtainable from a worktree); the `deploy-sidecar` job (not read to completion);
   `pipeline_smoke_audit.py` (no CI caller found); ci.yml's typecheck `|| true` (compensated
   elsewhere — theoretical only).
10. **`migration-guard` — NOT REACHED.** Only an agent-definition file was located, not a script.
    **No verdict should be inferred, and it must not be counted as checked.**
11. **Five `bo_*` emitters not opened** — `bo_sudarshana`, `bo_nakshatra_semantic`,
    `bo_special_lagna`, `bo_arudha`, `bo_vargottama_dhana` insert verification fields from emitters the
    sub-auditor did not read. **Missing evidence: whether each computes or hardcodes.** Given F-38
    found 11 hardcoded sites across five sibling files, these five are the **highest-yield next
    check** in the register — flagged as a named gap, not asserted as a finding.

---

## §5 — Residuals

### §5.1 — Coverage actually achieved

All four planned parallel sub-audits returned, plus the lane owner's own sweep of the named starting
set:

| Sweep | Ground | Status |
|---|---|---|
| **Lane owner (personally derived)** | the five named files, `SATYA_DIPA_REPORT` §5 | ✅ §1 — F-01…F-06 |
| Known-member §N.8 writers | `bo_pramana_mapa`, `ga_nakshatra`, `bo_chart_gestalt` | ✅ §2.1 — F-07…F-17 |
| Lane owner (incidental) | `mi_darshana` | ✅ §2.2 — F-18 |
| TypeScript serving layer | `platform-mcp/src/**`, `platform/src/**` | ✅ §2.3 — F-19…F-25 |
| CI / gates / guards | `.github/workflows/**`, `platform/scripts/**` | ✅ §2.4 — F-26…F-35 |
| Python build-layer writers | `ga_*`/`bo_*`/`ka_*`/`ph_*`/`mi_*` | ✅ §2.5 — F-36…F-40 |

**All three brief-mandated members of T4.4 are covered:** PB-2's byte-equality gate (F-33,
reclassified rather than deleted), PB-3 §G item 9 (F-34, confirmed absence), and the MCP post-deploy
smoke test (F-35, cross-referenced to lane A3 rather than duplicated).

**Bounded gaps within otherwise-swept ground** — these are *named holes inside* a completed sweep,
not unswept subsystems. They are the honest limit of T4.4's acceptance:

1. **Five `bo_*` emitters not opened** (§4 item 11) — the highest-yield next check, given F-38.
2. **`migration-guard` not reached** (§4 item 10) — must not be counted as checked.
3. **`bg_concordance.py` `match_confidence`** — NOT-REACHED (no TS consumer found).
4. **Serving layer NOT-REACHED items:** `capability_version.ts`'s `notifyIfCapabilityStale`; a full
   `ppl_writer.ts` `logPrediction` call-site audit; the writer-side origin of the
   `verification_pass_status` assignment (**now substantially answered by F-11 + F-38 — the two
   sub-audits met in the middle**).
5. **`platform/scripts/eval/runner.py`** — deliberately out of scope (sealed evaluator harness,
   excluded by the v2.0 authorization grant). Flagged so the `runner.py` name-collision is not
   mistaken for coverage.

### §5.2 — Evidence this audit could not obtain

- **Live DB state.** `mcp__postgres__query` returned `ECONNREFUSED 127.0.0.1:5433` on every attempt
  (no Cloud SQL proxy). This blocks one specific determination: **which branch of F-04 holds** —
  whether the always-red ephemeris probe is dispatched-and-ignored (Branch A) or never dispatched
  (Branch B). The finding stands under both, but a Verifier with DB access should resolve it, via:
  `SELECT asset_id, service_health, last_selftest_at, health_probe->>'probe_type' FROM asset_registry
  WHERE health_probe IS NOT NULL;` joined to `asset_throughput.state`.
- **§2.1's live row counts** are the sub-auditor's, not mine (see §2.1 provenance note).
- **Count discrepancy in §2.1, recorded not resolved.** The sub-auditor's summary line says "5
  additional siblings (4 confirmed / 1 rejected)" while its itemised list presents all five (F-13..F-17)
  as confirmed. F-17 is the likely intended rejection and is graded weakest here. **A spot-refutation
  should start with F-17.**
- **`platform/scripts/eval/runner.py`** was not audited — the sealed evaluator harness is outside the
  v2.0 authorization grant. Flagged so the name-collision is not mistaken for coverage.

---

## §6 — Routing to B-lanes, and questions for `DVA`

### §6.1 — Disposition

| Lane | Findings | Note |
|---|---|---|
| **B-N8-FIX** | F-07 … F-17 (its named scope) · **F-18** · **F-36 … F-40** (new, writer layer) | F-11 must land **with** F-25 + F-38 as one item — Q2 below. |
| **B-N8-SWEEPFIX** | F-01 … F-06 | All five named files. F-01/F-05 have an origin site in `asset_runner.py`, which no lane names — Q1. |
| **B-N8-LINT** | F-02 as a **precondition**; F-21 as its hardest test case | Mirror `check_fact_category_pinning.py` (#840). |
| **Unassigned — needs a lane** | **F-19 … F-25** (serving) · **F-26 … F-35** (CI/gates) | 17 confirmed findings fall outside all three B-lanes' declared scopes — Q5. |

### §6.2 — Questions for `DVA`

1. **F-01 / F-05 site ownership.** The origin write for both is in `asset_runner.py`, which is in no
   B-lane's declared scope and carries SATYA-DĪPA's **spent** freeze exception. Making
   `build_run_assets.state` carry the writer's real verdict is a data-correctness fix, not an
   orchestrator *contract* change — but per §N.2 the builder must stop rather than decide. **Rule on
   whether B-N8-SWEEPFIX may touch `asset_runner.py`.**
2. **F-11 + F-25 + F-38 must ship as ONE item — this is the register's highest-risk fix.** Today the
   grounded/ungrounded boundary in production is drawn by **string casing**: uppercase `'PASS'`
   (3,955 `ga_nakshatra` rows) reads as ungrounded; lowercase `'pass'` (11 `bo_*` sites) reads as
   grounded via `envelope.ts:1622-1626` — **and neither was verified by anything.** Any partial fix
   moves unverified rows across that boundary. Lowercasing F-11 alone would promote 3,955 unverified
   rows to production-"grounded" — **strictly worse than today.** The §N.8-correct fix is `NULL` +
   real detectors + vocabulary alignment, landing together. **Rule that no partial fix ships.**
3. **F-04 severity, pending §5.2.** If the ephemeris probe is dispatched, an L0 asset sealed as
   "provisioned" is permanently unhealthy and unnoticed. **Should F-04 escalate beyond B-N8-SWEEPFIX?**
4. **F-33 / F-34 amend upstream artefacts, not just code.** F-33 shows `CLAUDE.md §N.8`'s own
   instance 3 ("a 'byte-identical' claim with no byte comparison behind it") is **false as worded** —
   there *is* a real `toBe()`; the defect is that it compares a test-owned reimplementation, not the
   shipped adapter. F-34 shows PB-3 §G item 9 should be downgraded **VERIFIED-FIXED →
   VERIFIED-BY-INSPECTION-ONLY**. **Rule on who amends the doctrine text and the PB-3 report** — a
   builder should not silently edit `CLAUDE.md §N.8`.
5. **17 findings have no owning lane.** The serving layer (F-19…F-25) and CI/gates (F-26…F-35) fall
   outside B-N8-FIX / B-N8-SWEEPFIX / B-N8-LINT as declared in the queue. **Open new lanes, extend an
   existing one, or park with evidence?** F-19 (CRITICAL) and F-21 (§N.6 governance false-green)
   should not wait on that decision.
6. **F-28 is already with you, out-of-band.** A live plaintext production DB password sits in
   `secret_scan.sh`'s excluded `00_ARCHITECTURE/` zone. The sub-auditor routed the credential to `DVA`
   directly as urgent; this register deliberately does **not** reproduce it and is **not** the
   remediation channel. Noted here only so the finding is not double-handled or lost.

---

*End of SAMAPTI_N8_EARNED_SIGNAL_REGISTER v1.0.*

**40 confirmed findings**, each surviving an explicit refutation attempt: 6 in the five named files
(§1, personally derived and refuted by the lane owner), 11 in the known-member writers (§2.1), 1
additional writer finding (§2.2, lane owner), 7 in the TypeScript serving layer (§2.3), 10 in
CI/gates/guards (§2.4), 5 in the Python build-layer writers (§2.5).
**~40 candidates rejected as GENUINE** — several of which (`_verify_kalachakra`, `dossier.ts:721`,
`no_pre_answer_pass = NULL`, `get_yoga_dosha.ts`) are the repair patterns the fixes should copy.
**11 candidates dropped** as un-demonstrable, over-stated, or honestly disclosed.
**Three findings were narrowed rather than kept whole** (F-03, F-06, F-33) because the refutation
partially succeeded; the overstatement is named in each so no B-lane inherits it.

*This lane shipped no code.*
