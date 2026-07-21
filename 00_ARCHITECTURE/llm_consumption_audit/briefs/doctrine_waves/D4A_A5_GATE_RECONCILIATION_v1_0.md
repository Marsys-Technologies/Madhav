---
artifact: D4A_A5_GATE_RECONCILIATION
type: INVESTIGATION REPORT (not itself a gate ruling — findings + a draft correction for a
  separate lane to land)
version: 1.0
status: FINDINGS COMPLETE — verdict (b), correction drafted AND APPLIED (2026-07-22, landed by
  wave/D-4b/B6-close campaign-close session; see REPORT_D-4A.md §10 and STATE_D-4A.md frontmatter)
authored_by: Claude Code (Sonnet 5), wave/D-4b/a5-reconciliation lane, 2026-07-22
branch: wave/D-4b/a5-reconciliation (worktree
  .claude/worktrees/wave-D-4b-a5-reconciliation), based on origin/main @ 8b8a5f1e
governing: BRIEF_D4B.md, CLAUDE.md B.10/DR-16/DR-19, CONDUCTOR_PROTOCOL.md
scope: Investigation only. No code, no doctrine-wave artifact (REPORT_D-4A.md, BIND_D-4A.md,
  STATE_D-4A.md, model_interface.ts, curve.ts) was modified by this session. The proposed
  correction text in §5 below is a DRAFT for a separate lane to review and land.
---

# D-4a Lane A-5 gate-record reconciliation — investigation findings

## §0 — DR-19 check (performed first)

`CLAUDECODE_BRIEF.md` frontmatter on `origin/main` @ fetch time: `status: ACTIVE`,
`current_wave: D-4b (OPEN)`. `wave_sequence` includes `D-4b`; `BRIEF_D4B.md` frontmatter reads
`status: OPENED — native kickoff via Cowork 2026-07-21`. No branch/campaign mismatch — this is a
live, in-scope D-4b lane.

Process note carried over for the record (same discrepancy an adjacent sibling investigation on
this same campaign, `bakeoff_results/B1_BAKEOFF_STATUS_v1_0.md` §1, already flagged): this
session's initial environment banner stated "Current branch: impl/wave-5" with unrelated W5-lane
commit history (`ka_gochara_sweep` throughput fixes, QoS lanes) — a different numbering scheme
than this doctrine-waves campaign's `D-n`/`A-n`/`B-n` lanes. Live `git branch --show-current` at
session start showed `main`, not `impl/wave-5`. The DR-19 check above was performed against the
actually-observed live branch/repo state, not the banner text. No refuse-and-report condition was
triggered: `main` legitimately carries the D-4b-open campaign state and is the correct base to
fork this lane's worktree from.

## §1 — Verdict

**(b) GATE-RECORD-INTEGRITY-FINDING — with a precise, evidence-narrowed scope.**

(a) PLUMBING-DRIFT is **ruled out** with hard evidence (§3 below): `model_interface.ts` has
exactly one commit in its entire history and was created already containing the
`NotImplementedModelError` stubs for `midpoint_triangle`/`transit_kernel`. No commit, on any
branch, at any point in this repository's history, ever added a working `curve()` for either
model. Nothing was orphaned by a later refactor — there is no "later" for this file to have
drifted from.

The correction needed is **narrower than "the claim was never true and nobody flagged it."** Every
substantive artifact that actually reports what A-5 did —
`artifacts/D-4a/A-5/RESULTS_v1_0.md` §1, the A-5 merge commit message (`86e9954d`),
`REPORT_D-4A.md` §2/§6, and `BIND_D-4A.md` §5e — states plainly, at the time of close, that only
`pratyantar_lord` was scored and the other two were honestly reported as gaps per B.10. **The gap
is that `REPORT_D-4A.md` §3's one-line gate-result table marks criterion 5 a bare `PASS`, with no
qualification, against `BRIEF_D4A.md` §G item 5's literal pre-registered text ("3 models scored
end-to-end") — which was not met.** A reader who consults only that summary table (exactly what
this task's own framing did, and exactly what the orchestrating session is positioned to do when
skimming a closed wave's gate result) is told something the surrounding narrative in the very same
document already contradicts.

## §2 — Evidence trail

### §2.1 — `model_interface.ts` has one commit, ever, already stubbed

```
$ git log --follow --oneline -- platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface.ts
055eb9d2 feat(D-4a/A-3): controls + proper-scoring harness — CRPS/log-score primary, structural control-mirroring enforcement (#614)
```

One commit. `git show 055eb9d2` (commit message, verbatim) states the file was authored to
"wrap[] the one servable model today (`pratyantar_lord`...) and stub[] `midpoint_triangle`/
`transit_kernel` with `NotImplementedModelError`... so Lane A-5 can register real implementations
without touching the harness contract." The stub design was the plan from the file's creation, not
a later regression.

### §2.2 — No working implementation of either stub ever existed, on any branch

```
$ git log --all --oneline -S"midpointTriangle" -- .
bb001c3d docs(d4b/b1): land NP-D4B-004 ruling; B-1 bakeoff status = BLOCKED, no fabrication
86e9954d D-4a Lane A-5: harness dry-run (diagnostic, NOT DR-12 adjudication) (#616)
055eb9d2 feat(D-4a/A-3): controls + proper-scoring harness — CRPS/log-score primary, structural control-mirroring enforcement (#614)
```

`git log --all -p -S"midpoint" --pickaxe-regex -- '*.ts'` across the whole history (checked for
every commit that ever added or removed a "midpoint" occurrence in any TypeScript file) shows only
comment/doc-string/type-literal references (`'midpoint_triangle'` as a `ModelId` union member,
"deprecated default" prose) — never a function body computing a midpoint-triangle curve.
`curve.ts` (the one real curve builder, `buildCurve()` backing `pratyantar_lord`) was created in
the D-3 T-0 harness commit `11377530` and its only "midpoint" references are the same "deprecated
default" comment. No predecessor file (`curve.ts`'s own single-commit `--follow` history) ever
implemented it either.

### §2.3 — A-5's own results artifact reports the truth plainly (`artifacts/D-4a/A-5/RESULTS_v1_0.md` §1)

| model | status | note |
|---|---|---|
| `pratyantar_lord` | **SCORED** | the one real, wired model |
| `midpoint_triangle` | **GAP — not scoreable** | `NotImplementedModelError`; no substrate exists in the codebase |
| `transit_kernel` | **GAP — not scoreable** | `NotImplementedModelError`; no ephemeris/transit curve-building code exists anywhere in the repo |

> "Per B.10 (no fabricated computation): the two gaps are reported as gaps, not fabricated
> scores. This is a genuine finding for D-4b, not a defect of this lane's run."

The A-5 merge commit message (`86e9954d`) says the same thing in its own words: "pratyantar_lord
scored, midpoint_triangle/transit_kernel gaps reported."

### §2.4 — `REPORT_D-4A.md` itself is honest in its body, but its gate table is not qualified

§2 (promise ledger), line 56, already reads correctly:

> `[x] A-5: 3 models attempted; pratyantar_lord scored end-to-end, midpoint_triangle/transit_kernel honestly reported as gaps (B.10 — no fabricated computation)`

§6 (findings requiring future disposition) repeats it:

> `midpoint_triangle and transit_kernel models remain unimplemented (NotImplementedModelError) — open engineering gap for whoever builds D-5's engine construction or D-4b's full bakeoff.`

But §3, the gate-result summary table, reads:

```
| # | Criterion            | Result |
|---|-----------------------|--------|
| 5 | Dry-run complete      | PASS   |
```

— no caveat, unlike row 6 ("Ledger live"), which *does* carry an inline parenthetical
qualification for its own partial-verification-method gap. Row 5 got no equivalent treatment.

### §2.5 — `BIND_D-4A.md` §5e is fully honest, and more precise than the gate table

> "Only 1 of 3 models (pratyantar_lord) was scoreable; midpoint_triangle and transit_kernel are
> honestly reported as gaps (both throw `NotImplementedModelError`, no fabricated curve) per
> B.10 — noted as an open gap for D-4b, not a defect of this lane."

But `BIND_D-4A.md` never issues a formal **Binder ruling reconciling gate item 5's literal text**
against what actually ran — contrast this with gate item 7 ("all prior batteries green"), which
*does* get an explicit Binder ruling in `BIND_D-4A.md` §2 re-scoping its literal wording ("no new
regression since D-3's sealed state") before the wave-close report marks it PASS. Item 5 has the
narrative honesty but not the equivalent formal reconciliation — that is the actual missing piece.

### §2.6 — The source of the literal "3 models scored" text: `BRIEF_D4A.md` §G item 5

> "5. Dry-run complete: **3 models scored end-to-end**, per-event tables committed, header
> carries the DR-12-deferral disclaimer."

This is the pre-registered acceptance bar the wave was gated against. It was not met literally
(only 1/3 scored); what happened instead (1 scored, 2 honestly gapped, doctrinal guardrail swept
clean) is a legitimate and defensible outcome under B.10 — but it is a *different* outcome than
the criterion's literal text, and the difference was never formally reconciled the way item 7's
was.

### §2.7 — Independent corroboration from a sibling D-4b investigation, same campaign

A prior session on this same campaign (branch `wave/D-4b/B1-bakeoff`, commit `bb001c3d`,
`bakeoff_results/B1_BAKEOFF_STATUS_v1_0.md`) independently audited the same harness for D-4b's own
B-1 Grand Bakeoff (which needs all 5 requested contenders — midpoint-triangle, pratyantar-lord,
transit-kernel, 12 D-5 PERMISSION generators, and the hierarchical ensemble) and reached the
identical code-level finding: **"1 of 5 requested contenders (`pratyantar_lord`) has a real,
callable `curve()` in the harness today."** That report ruled B-1 **BLOCKED**, refused to score
anything, and refused a fabricated cost projection requested of it — the same B.10-honest pattern
this investigation independently confirms for A-5's narrower 3-model dry-run.

That same file (§4 recommendation) names the correct forward path: writing the missing
`TemporalCurveModel` adapters is "its own named pre-step," not something to fold into a scoring
dispatch under time pressure — directly relevant to D-4b's own B-1 lane, separate from this
lane's narrower gate-record question.

### §2.8 — A second, independent instance of the same overstatement pattern, this campaign

`NATIVE_PROXY_LEDGER_D4B.md` NP-D4B-005 (2026-07-22, native-ruled) records a **second, separate**
occurrence of the identical failure mode this investigation found in D-4a's gate table: "the
orchestrating session's own B-1 merge-agent dispatch prompt asserted 'the B-1 Grand Bakeoff lane
passed independent verification' when the actual verifier had accepted a BLOCKED report as
*honestly reported*, not as a *passing bakeoff* — a re-framing error." The native's own
process-finding fix for that instance: "orchestration scripts must pass a verifier's verdict
through to downstream steps verbatim... never re-narrated into a broader claim than the verifier
made." The same discipline applies to this investigation's finding: a gate table's terse `PASS`
must not silently drop the qualification the underlying report already carries.

## §3 — Why (a) PLUMBING-DRIFT is definitively ruled out

PLUMBING-DRIFT would require: a commit, at some point, that added a real `curve()` implementation
for `midpoint_triangle` or `transit_kernel`, followed by a later commit that deleted or simplified
it. Neither half of that exists:

- `model_interface.ts`: **one commit in its entire `--follow` history** (`055eb9d2`), already
  containing the stubs at creation.
- `curve.ts`: **one commit in its entire `--follow` history** (`11377530`), containing only the
  `pratyantar_lord`/`dasha_lord_confluence_v1` logic; its only "midpoint" references are comments
  naming it a "deprecated default," never code.
- Whole-repo `git log --all -S"midpointTriangle"` / `-S"transitKernel"` (pickaxe search across
  every commit on every branch — not just `main`'s linear history) surfaces exactly 3 commits,
  all of which are the creation commit, the A-5 dry-run commit consuming the stub, and the sibling
  B-1 investigation's write-up quoting the stub — no fourth commit exists that could have deleted
  a working implementation, because none was ever added.

There is no predecessor plumbing to have drifted from. The "gap" was a documented, deliberate
design decision (per `055eb9d2`'s own commit message) from the moment the interface was created,
carried forward honestly through A-5's dry-run, and left as an explicit open engineering item for
D-4b/D-5.

## §4 — What is and is not being claimed

- **Not claimed:** that D-4a's overall `GATE GREEN 7/7` close is fraudulent or should be reversed.
  The substance behind item 5's PASS — a real scoring pass for the one servable model, honest gap
  reporting for the other two, a clean doctrinal-guardrail sweep (no DR-12-adjudication language
  leaked into the diagnostic), a provably-prior pre-registration — is real, was accurately
  narrated in `REPORT_D-4A.md` §2/§6 and `BIND_D-4A.md` §5e, and is a defensible basis for a PASS
  under a corrected (not literal) reading of the criterion.
- **Claimed:** the top-line gate-result table in `REPORT_D-4A.md` §3 (and the bare `GATE GREEN
  7/7` frontmatter status line it and `STATE_D-4A.md` both carry) does not itself carry that
  qualification, creating exactly the kind of "read only the summary, miss the caveat buried in
  the body" gap that produced this task's own framing of the claim, and that NP-D4B-005 (§2.8
  above) shows has already caused a real downstream mischaracterization once elsewhere in this
  same campaign.

## §5 — Draft correction annotation (NOT APPLIED — for a separate lane to review and land)

**Target file 1 (primary): `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/REPORT_D-4A.md`**

Edit 1 — §3 gate-result table, row 5. Change:

```
| 5 | Dry-run complete | PASS |
```

to:

```
| 5 | Dry-run complete | PASS — scope-corrected 2026-07-22, see §10 |
```

Edit 2 — append a new section after the existing §9 ("Next"):

```markdown
## §10 — Correction (2026-07-22, wave/D-4b/a5-reconciliation lane)

**What this corrects.** §3's gate-result table originally marked criterion 5 ("Dry-run complete")
as a bare `PASS` with no qualification. `BRIEF_D4A.md` §G item 5's literal acceptance text reads:
"Dry-run complete: 3 models scored end-to-end, per-event tables committed, header carries the
DR-12-deferral disclaimer." Only 1 of the 3 pre-registered model contenders — `pratyantar_lord` —
was actually scored; `midpoint_triangle` and `transit_kernel` both throw
`NotImplementedModelError` and have never had a working `curve()` implementation anywhere in this
repository's history (verified via `git log --follow` / `git log -S` on `model_interface.ts` and
`curve.ts`: both single-commit creation, already stubbed/complete at that commit; zero prior or
later commit adds a real implementation for either). This was never hidden — this report's own §2
(A-5 promise-ledger line) and §6, `artifacts/D-4a/A-5/RESULTS_v1_0.md` §1, and `BIND_D-4A.md` §5e
all stated the 1-of-3 fact plainly at the time of close. The gap this correction closes is
narrower: unlike gate item 7, which received an explicit Binder ruling in `BIND_D-4A.md` §2
reconciling its literal text against what actually ran, item 5 got no equivalent ruling — so its
one-line `PASS` in the summary table, read in isolation from the surrounding narrative, overstated
what the dry-run delivered.

**Disposition.** The wave's overall GATE GREEN 7/7 status is not reversed by this correction — the
underlying substance (doctrinal guardrail clean, B.10-compliant honest-gap reporting, DR-12
adjudication correctly deferred to D-4b) was real and was accurately narrated elsewhere in this
same report and in `BIND_D-4A.md`. The correction is a precision fix to the top-line gate table
(§3, row 5) so a reader consulting only that table is not misled, plus this explanatory record.
`midpoint_triangle`/`transit_kernel` remain open engineering gaps, tracked in §6 above and in
D-4b's own B-1 lane (`bakeoff_results/B1_BAKEOFF_STATUS_v1_0.md`, which independently confirmed
the identical 1-real-model finding while auditing B-1's larger 5-contender requirement).

**Investigated by:** `wave/D-4b/a5-reconciliation` lane. Full evidence trail:
`D4A_A5_GATE_RECONCILIATION_v1_0.md` (this campaign's doctrine_waves directory).
```

**Target file 2 (optional companion, lower priority): `STATE_D-4A.md` frontmatter**

The `status: CLOSED — GATE GREEN 7/7` line could carry a one-line pointer
(`# item 5 scope-corrected 2026-07-22 — see REPORT_D-4A.md §10`) for discoverability, but this is
optional; `STATE_D-4A.md` is a rolling state pointer, not the primary gate record, and does not by
itself need the full explanation.

**Not recommended:** editing `BIND_D-4A.md` §5e — it is already accurate and needs no correction;
adding a formal "Binder ruling" subsection there mirroring §2's item-7 treatment would be a nice
symmetry improvement but is not required to fix the actual misstatement (which lives in
`REPORT_D-4A.md` §3's table, not in BIND's narrative).

## §6 — Ground-rule compliance

No numerical chart value, score, count, or DB row was fabricated, restated, or altered by this
investigation. Every number cited above (per-domain CRPS/skill/hit-rate figures, the 55-event
scorable corpus, commit hashes) is quoted verbatim from committed artifacts already in the repo,
never recomputed or invented. No file under `artifacts/D-4a/A-5/`, `REPORT_D-4A.md`,
`BIND_D-4A.md`, `STATE_D-4A.md`, `model_interface.ts`, or `curve.ts` was modified — this session
is investigation-only per its own charge. `asset_runner.py`, `runner.py`'s
`execute_dag`/`_schedule_parallel`, the leakage firewall, raw LEL event data, prior gate/regression
surfaces, and `gochara_grammar`/`gochara_intensity` internals were not touched (not read either —
out of scope for this investigation). No LEL event row of any date, sealed-split or otherwise, was
queried; no DB or MCP call was made (`mcp__marsys-jis-direct__*` also requires authorization this
session does not have, per the environment's own notice, and was not needed for this read-only
git/doctrine investigation).
