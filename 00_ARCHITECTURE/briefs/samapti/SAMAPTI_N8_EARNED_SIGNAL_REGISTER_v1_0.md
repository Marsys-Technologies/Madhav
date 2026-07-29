---
artifact: SAMAPTI_N8_EARNED_SIGNAL_REGISTER
canonical_id: SAMAPTI_N8_REGISTER
version: 1.0
status: FINDINGS-COMPLETE (audit lane — ships no fixes)
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
2. Every candidate was attacked. Sub-auditors argued against their own findings inline (`(e)` blocks
   in their reports); the five-named-file findings — the ones the lane owner authored — were attacked
   by a **separate, independent refuter sub-agent** given the finding, the evidence, and an explicit
   instruction to destroy it.
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
- **Part B** (§2) — codebase-wide, by subsystem, via bounded parallel read-only sub-auditors.
- **§3** — rejected candidates. These are load-bearing: they show the sweep discriminates, and three
  of them are the *correct pattern* a B-lane should copy.
- **§5** — residuals: named surfaces this audit did **not** reach, and the one class of evidence it
  could not obtain.

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

`.github/workflows/ci.yml:344-372` is the only job that runs the sidecar suite. Its own comment, at
`:347-350`, states the outcome:

> *"All tests here are self-contained (conn=None dry-run or `@pytest.mark.skipif(not DATABASE_URL)`
> for integration tests). … **CI has no DB, so those 6 tests skip cleanly.**"*

So the guard's live check is skipped on every CI run. The remaining four tests in that file exercise
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
   commented `# 1984-02-05 10:43 IST → UTC Julian Day` (`:112`). Recomputed: `swe.revjul` decodes it
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
