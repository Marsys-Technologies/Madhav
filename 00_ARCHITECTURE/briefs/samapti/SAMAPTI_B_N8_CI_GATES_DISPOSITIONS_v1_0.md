---
artifact: SAMAPTI_B_N8_CI_GATES_DISPOSITIONS
canonical_id: SAMAPTI_B_N8_CI_GATES_DISPOSITIONS
version: 1.0
status: CURRENT
created: 2026-07-30
lane: B-N8-CI-GATES
governed_by: 00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md (Ruling 12)
source_register: SAMAPTI_N8_EARNED_SIGNAL_REGISTER_v1_0.md (origin/samapti/n8-audit) §2.4 + F-21
---

# B-N8-CI-GATES — per-finding dispositions

Lane created mid-run by Dvārapāla Ruling 12. Owns F-21 (shipped first, as ruled) plus
the CI/gates/guards subset F-26 → F-35. Ruling 12 requires **every** item to carry a
disposition with evidence; not every item needs code.

Branch: `samapti/n8-ci-gates`.

---

## Summary table

| ID | Subject | Disposition | Code? |
|---|---|---|---|
| F-21 | `density_contract` governance false-green | **VERIFIED-FIXED** | yes |
| F-26 | `hard_gates_check.sh` cannot return non-zero | **VERIFIED-FIXED** | yes |
| F-27 | `icr_weekly_scan.yml` cannot go red | **VERIFIED-FIXED** | yes |
| F-28 | `secret_scan.sh` scope hole | **NOT-APPLICABLE (handled elsewhere)** | no |
| F-29 | `schema_validator.py` ci.yml misdescription | **VERIFIED-FIXED** | yes |
| F-30 | `chat-v2-ci.yml` swallowed failures | **VERIFIED-FIXED** | yes |
| F-31 | `chat-v2-ci.yml` four no-op "HARD" gates | **VERIFIED-FIXED** | yes |
| F-32 | `deploy.yml` web smoke → 100% promote | **VERIFIED-FIXED** | yes |
| F-33 | PB-2 byte-equality gate wording | **REJECTED-AS-WORDED / reclassification CONFIRMED** | no (routed) |
| F-34 | PB-3 §G item 9 no-auto-promotion | **PARKED-HONEST — no detector exists** | no (routed) |
| F-35 | MCP post-deploy smoke | **NOT-APPLICABLE (cross-ref A3)** | no |

---

## F-21 · `density_contract` machine-backfill — VERIFIED-FIXED

**Mechanism, re-derived at `origin/main` 5f5033a5 rather than accepted from the register.**
`descriptor_defaults.ts:deriveDensityContract()` (:396–415) derives `empty_reason` from
`cap.archetype !== 'orientation_digest' && cap.archetype !== 'calibration'` — an archetype
LABEL — and `paginated` from param-name presence. Neither reads the handler.
`applyDescriptorDefaults()` (:470) stamps that onto every capability lacking one, in place,
inside `getCatalog()`. `generate_tool_census.ts:scoreA4` then graded §N.6 from `typeof`/shape
checks on the resulting object, never inspecting source — unlike its own sibling `scoreA3`,
which greps the capability's source file.

**Two corrections to the register, both material:**

1. The register says the census "reads the descriptor POST-backfill". It does not.
   `generate_tool_census.ts` imports `getAllCapabilities()` (registry `index.ts`), and its
   `import '@/lib/retrieval/registry/catalog'` is a registration side-effect only — it never
   calls `getCatalog()`, which is where the backfill runs. Measured: 13 of 174 capabilities
   carried a `density_contract`, not 174. The **grading** defect is exactly as described; the
   **reading** claim was not. The post-backfill grading does happen, but in two other places:
   `projection_builders.ts:338` (`has_density_contract: cap.density_contract !== undefined`,
   feeding `machine_census.generated.json`, true for all rows) and
   `descriptor_defaults.test.ts:163`'s 100%-coverage assertion — both true by construction of
   the backfill. Recorded as a residual; not fixed in this lane.
2. `get_positions.ts` is cited as "stamped `empty_reason: true` with zero occurrences of
   `empty_reason`". True of the live descriptor, but it scored A4=0 in the census even before
   this fix (it has no hand-set contract and the census reads pre-backfill). The worked example
   is sound as a description of the estate; it was not what the census was grading.

**Fix.** `scoreA4` now: (a) checks whether the contract is declared in the capability's own
source file, which takes precedence over everything else; (b) for contracts NOT in their own
source, re-runs `deriveDensityContract()` and scores 0 when byte-identical to the generated
default — robust to the census being switched `getAllCapabilities()` → `getCatalog()`, the
one-line edit that would otherwise flip the whole estate to "enforced"; (c) for hand-authored
contracts, greps the source the way `scoreA3` does, **with the `density_contract: { ... }`
literal excised first** so a declaration cannot corroborate itself; (d) grades 2 only when every
claim asserted `true` is corroborated in the handler; (e) reports unresolved or stale
`uri`→file mappings as UNVERIFIABLE (1), never 2. `deriveDensityContract` is exported read-only
for this purpose; `applyDescriptorDefaults()` remains the sole writer.

**Ordering bug caught during the work, recorded because it nearly shipped:** comparing against
the machine default BEFORE checking source declaration graded `get_vichara` a 0. Its hand-set
`max_verdict_bytes: 1024 / max_digest_bytes: 4096` is byte-identical to the `leaf` tier default
— because `TOOL_ROLE_DIGEST_BYTES`'s own doc comment says the tier table was built from
get_vichara's precedent. A detector for unearned greens must not invent a red.

**Effect:** A4=2 falls 13 → 6. New `a4_n6_accounting` block reports declaration and enforcement
separately (present 13 / enforced 6 / unearned 7), because collapsing them is how the axis went
green in the first place.

**Real finding surfaced by the fixed axis:** `query_spine_bundle`
(`register_spine_bundle.ts:92`) declares `empty_reason: true` and ships no empty-reason
discipline — the only token in the file is the declaration itself.

**CAN-FAIL (Ruling 12's mandated proof).** Planted a hand-authored, non-implementing
`density_contract {paginated:true, facets:['planet','house'], empty_reason:true}` on
`get_positions.ts` (a capability whose handler contains zero `empty_reason` occurrences):
new rubric scores **1** with basis "hand-declared in source but UNCORROBORATED"; the old
shape-only rubric scores **2**. Reverted. Second proof: renamed the 4 handler-side
`empty_reason` tokens in `get_yoga_dosha.ts`, leaving its declaration intact — A4 drops **2 → 1**
and `present_and_enforced` 6 → 5. Reverted.

---

## F-26 · `hard_gates_check.sh` — VERIFIED-FIXED

Header claimed "Returns: 0 if all GREEN, 1 if any RED". The file contained **zero** `exit`
statements, so it returned the status of its final `printf`: 0, always. Proven against
`origin/main`'s copy: planted `jh_oracle.json` (the artifact G2 bans) → **exit 0**.

Fixing only the exit would not have been enough. **Nine** of fifteen gates had no RED branch at
all — G1, G3, G5, G7, G8, G11, G12, G13, G15 (**the register said eight; the correct count is
nine**), several with notes reading "acceptable". G6 additionally carried a fake-green fallback
on top of its real RED branch. Ten branches were reclassified by what they actually mean:

- **G5, G7, G8, G11 → RED.** A real assertion was hiding behind the fake green.
- **G3, G6-fallback, G12, G13 → STALE.** The check cannot run; its target path is gone.
- **G1 → NOT_ASSERTED.** Both arms were legitimately fine; it never validated anything.

`STALE` is deliberately neither RED nor GREEN. A detector that lost its target has not found a
violation, and dressing one up as a violation is the same sin as the fake green, inverted — but
an unperformed check is never a pass either (conductor manual §8). Exit codes: `0` clean, `1`
violation, `2` no violations but coverage incomplete.

**State on main after the fix: exit 2** — 12 GREEN, 0 RED, 1 NOT_ASSERTED, 2 STALE. G3 globs for
a Python-era `test_chart_facts*.py` (chart_facts coverage now lives in TypeScript tests); G12
globs for `build_chart.py`, superseded by the orchestrator per `L1_GANITA_CLOSURE`. Both were
reported GREEN before. Repointing them is a build-layer judgment, logged as a residual rather
than guessed at here.

**DVA Ruling 59 — exit 2 on main is CLEARED TO SHIP.** `STALE` is the honest label per this
lane's own disposition; no workflow invokes the script, so it is CI-invisible either way; and
repointing the globs is a build-layer test-location judgment outside this lane's brief.

> **RESIDUAL FOR THE CLOSE REPORT (Ruling 59, not a new lane).** Repoint the two STALE detectors,
> routed to whoever next touches L1 test hygiene:
> - **G3** → the current `chart_facts` TypeScript test location (coverage now lives in
>   `platform/src/lib/retrieval/registry/layers/chart_facts_query_*.test.ts` and
>   `platform-mcp/src/__tests__/chart_facts_ayanamsha.test.ts`), replacing the Python-era
>   `test_chart_facts*.py` glob.
> - **G12** → the orchestrator-native equivalent of `build_chart.py`, which no longer exists
>   anywhere in the repo (superseded per `L1_GANITA_CLOSURE`).

**CAN-FAIL:** planted `jh_oracle.json` → G2 RED, **exit 1**; removed → **exit 2**. Same mutation
against `origin/main`'s copy → exit 0.

**Reported, not fixed:** no GitHub workflow invokes this script. Fixing the exit makes its header
claim true for the operator runbooks that call it by hand; it does not make it a live CI gate.
That is F-02's territory, not this lane's.

---

## F-27 · `icr_weekly_scan.yml` — VERIFIED-FIXED

The weekly "ICR Conflict Scan" scanned nothing and could not fail. **Five** independent causes,
three beyond what the register recorded:

1. `--dry-run` suppressed the only non-zero exit path.
2. `--synthetic` validated a hardcoded fixture; the corpus was never opened.
3. The default MSR path was `MSR_v3_0.md`, gone since the MSR reached v5.0.
4. **New, and the worst.** `runGate()` parsed `## MSR.NNN` + `sources:` blocks. `MSR_v5_0.md`
   has none — it has **569** `SIG.MSR.NNN:` blocks with `derivation_ledger.l1_sources`. The
   parser matched **0 of 569**, produced zero violations, and printed
   *"PASS — all signals have FORENSIC/LEL citations"* over an empty set. Green because it
   stopped looking. Fixing 1–3 alone would have left this vacuous pass in place, now wearing a
   real gate's clothes.
5. **Also new.** `/\bFORENSIC\b/` cannot match the corpus's own `FORENSIC_v8.0` citation style —
   `_` is a word character, so there is no trailing boundary. Invisible while the parser matched
   nothing; once Format A parsed 569 blocks it reported all 569 ungrounded.

**Fix.** Parser understands both layouts. A scan recognising **zero** signal blocks now exits 1
(an unperformed scan is not a pass). The MSR is discovered as the highest `MSR_v*.md` rather than
pinned to a version that rots. The workflow runs the real corpus scan as the gate, and its
synthetic step became a genuine **positive control** asserting `exit == 1` on the fixture's
planted violation — previously that step passed whether or not the detector detected anything.

Real scan now: **569 blocks scanned, 0 violations, exit 0.**

**CAN-FAIL:** stripped the `FORENSIC_v8.0` refs from `SIG.MSR.001` only → *"FAIL — 1 signal(s)
lack FORENSIC/LEL citation"*, **exit 1**. Restored → exit 0, MSR byte-clean per `git status`.
Positive control: `--synthetic` → exit 1 as required.

**REGRESSION TESTS ADDED ON CYCLE 1 (VER).** VER observed that reverting either half of the F-27
fix left all 13 then-existing tests passing — the suite was blind to both defects, so a
regression would have gone unnoticed until a weekly cron printed a vacuous PASS. A gate fixed
without a test that locks the fix is one careless commit from reverting to a false green. Five
tests added to `tests/icr/icr_pr_gate.test.ts`, all using the REAL corpus format. Fail-then-pass
proven per SATYA-DĪPA's standard:

| Revert applied | Result |
|---|---|
| restore `/\bFORENSIC\b/` | **1 test fails** (the `FORENSIC_v8.0` grounding test) |
| disable the Format A parser | **2 tests fail** (blocks parsed; ungrounded flagged) |
| both fixes restored | **18/18 pass** |

---

## F-28 · `secret_scan.sh` scope hole — NOT-APPLICABLE (handled elsewhere)

Already routed by Dvārapāla Rulings 1–3 to dedicated lanes: **B-SECRETSCAN-SCOPE** (invert the
allowlist-of-8 to repo-wide-minus-suppressions), **B-SECRET-REDACT** (env-var indirection across
the 9 files), **B-SECRET-ROTATE-PREP** (runbook only). Not duplicated here.

Incidentally confirmed while working: there are two `hard_gates_check.sh` files. The one carrying
the credential at line 46 is `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/hard_gates_check.sh`
(64 lines) — **B-SECRET-REDACT's file, untouched by this lane**. F-26's subject is the different,
180-line `platform/scripts/hard_gates_check.sh`, which contains no credential (verified by grep;
the credential itself is not reproduced anywhere in this lane's output, per Ruling 12 action 4).

---

## F-29 · `schema_validator.py` ci.yml claim — VERIFIED-FIXED

The step comment asserted *"schema_validator exits 0. Gate hardened."* A live run on the same
tree: `schema_validator: 43 violations; exit=3`. The 2026-05-31 governance pass did resolve the
four SESSION_LOG entries it named; that was mistaken for the whole picture.

The deeper defect is not the comment. **Both** governance steps accepted exit 3
*unconditionally*, so the entire MEDIUM/LOW band passed green permanently and without limit —
one pre-existing violation and four hundred new ones produced an identical green tick.
`drift_detector` at least names a `known_residuals[]` whitelist; `schema_validator` has no
whitelist mechanism at all, so exit 3 was blanket amnesty.

**Fix.** Both steps pin a count ceiling at the **DVA Ruling 4 T0 baseline** — 216 drift findings
/ 43 schema violations, reproduced on this tree. Exit 3 still passes, but only while the count
does not GROW. Unparseable output now fails rather than passing: a gate whose result cannot be
read has not passed.

**CAN-FAIL (parse + ceiling logic, three ways, against real captured output):** ceiling 43 →
PASS exit 0; ceiling 42 (simulating one new violation) → `::error::EXCEEDS` exit 1; unparseable
output → `::error::unparseable — refusing to pass` exit 1.

**DVA Ruling 59 — the feared cross-lane coupling does NOT materialise; no allowance granted.**
This lane raised a concern that B-DOCS-GOVERNANCE's two `artifact:` additions would push the
schema count to 45 and redden CI against the pinned 43. DVA checked out
`origin/samapti/governance-docs @ b3e0d510` (post-Ruling-58 tip) in an isolated worktree and ran
both tools live: **schema_validator 43, drift_detector 216** — both exactly at T0, unchanged.
The 45-count coupling does not occur against the actual branch tip. The ceiling stands as the
ratchet Ruling 4 / F-29 intend, with no temporary allowance and no expiry to track. This
independently reproduces the same 216/43 measured in this lane.

---

## F-30 / F-31 · `chat-v2-ci.yml` — VERIFIED-FIXED

**F-30, two swallows, both load-bearing and both printing a false message.**
Stage 1 ESLint ended `2>/dev/null || echo "STAGE-1-LINT no-op (paths not fully populated yet)"`.
All ten paths are populated (185 files) and ESLint reports **26 errors + 93 warnings** across
them. Those 26 belong to the chat-v2 arc and are not this lane's to fix, so the step becomes a
ratchet: debt pinned at 26 and disclosed, any NEW error fails.
Stage 5 ended `|| echo "STAGE-5-VISUAL no visual specs yet"` — also false; `a11y/axe.spec.ts`
carries a `@visual`-tagged test. Swallow removed; the *absence* of any `@visual` spec is now
itself a failure rather than the excuse the swallow used.

**F-31, four stages labelled "Gate: HARD pre-merge" that gate nothing.** Stages 10 (chaos), 11
(security), 13 (mutation), 14 (staging smoke) — all four targets verified absent, so every run
takes the no-op branch. Worse, 10/13/14 additionally carried `continue-on-error: true`, so even
once their tests land their failures could not have blocked a merge. Stage 14 installed three
Playwright browsers and then echoed a string.

`continue-on-error` removed from 10/13/14 so they gate the moment their target appears; Stage
14's unused browser install dropped; every not-active branch emits `::warning::` stating plainly
that the stage asserts nothing; each header records actual status rather than intended status.
Relabelled honestly rather than forced red — the work genuinely has not landed, and a
permanently red stage is how `ci-red-ignored-*` tags get minted (which is what G15 counts).

Stages 6 (a11y) and 7 (perf) keep `continue-on-error`: their headers already say SOFT, so they
are honest and were left alone.

**REFUTED BY VER ON CYCLE 1, AND WHY THAT MATTERS.** The first pass at the Stage 5 fix removed
the swallow correctly but left the stage FAILING on live CI, which would have reddened
`chat-v2-ci.yml` for every subsequent PR in the run — the exact masked-signal harm this lane
exists to eliminate. Cause: Stage 5's `env` carried only `MARSYS_FIXTURE_MODE`, while sibling
Stage 3 (same Playwright config, passing) also supplies six `NEXT_PUBLIC_FIREBASE_*` secrets.
`playwright.config.ts`'s `webServer.env` forwards exactly those six from `process.env`, with the
comment *"Forward Firebase vars from CI env so Next.js can start without auth/invalid-api-key"*.
Without them `npm run dev` died with `FirebaseError: auth/invalid-api-key` and the webServer timed
out after 120s. Fixed by mirroring Stage 3's env block exactly (verified equal key-for-key).

**The deeper correction, which belongs in the record.** The removed swallow's message —
*"no visual specs yet"* — was not merely false, it named the **wrong cause**. There is a `@visual`
spec (`axe.spec.ts:79`); what was missing was the **environment**. That false explanation is worse
than a silent failure: it sent every reader looking for absent tests instead of absent secrets,
and this lane's own first fix inherited the same wrong assumption. A misleading label on a
swallowed failure propagates the error into whoever eventually removes it.

**Verification limit, previously declared and now discharged:** the Stage 5 change could not be
executed locally (needs browsers + a dev server) and was published as *"reasoned edit, not
runtime-proven."* That declaration is exactly what VER's live-CI check tested, and it did not
hold. It is now verified against live CI rather than reasoning. The ESLint ratchet and its
26-error baseline were measured by running ESLint locally.

---

## F-32 · `deploy.yml` web smoke → 100% traffic promote — VERIFIED-FIXED

The whole gate between a broken build and all production traffic was two probes, neither
examining the candidate's application code:

1. `/api/health` is `export function GET() { return NextResponse.json({status:'ok'}) }` — a
   static literal. No imports, no auth, no DB. It cannot distinguish a healthy revision from one
   whose every real route 500s.
2. `SMOKE_SIDECAR_URL` is never passed by the `deploy-web` job, so the sidecar probe silently
   fell back to a hardcoded URL for the **already-live** sidecar — a different service — while
   counting toward the gate as though it said something about the artifact about to take traffic.

**Fix.** Added `probe_auth_enforced`: an unauthenticated GET of the auth-guarded
`/api/sidecar/health` on the **candidate** must return 401, exercising dynamic-route handling,
the `cookies()` runtime, the auth guard and response serialization. Deterministic and
credential-free — `getServerUser()` returns null on a missing `__session` cookie before touching
Firebase Admin — so it cannot false-red on secret availability. The sidecar probe is relabelled a
dependency check and announces when it is using the hardcoded fallback. Probes accumulate and
report together.

**CAN-FAIL,** against a local server returning 200 on `/api/health` in every mode:

| candidate behaviour | fixed script | `origin/main` script |
|---|---|---|
| auth guard enforced (401) | exit 0, Smoke PASS | exit 0 |
| auth guard missing (200) | **exit 1, Smoke FAIL** | **exit 0** |
| app erroring (500) | **exit 1, Smoke FAIL** | **exit 0** |

The pre-fix script would have promoted 100% of production traffic to a revision with no auth
guard.

**Not claimed:** no DB round-trip, no authenticated request, no chart render. Those need a web
canary credential that does not exist — the same class of gap `deploy.yml` already documents for
the MCP canary key. Residual.

---

## F-33 · PB-2 byte-equality gate — REJECTED-AS-WORDED; reclassification CONFIRMED

The register flagged this as needing reclassification and disclosed a methodology caveat:
`vitest` was absent in the audit worktree, so F-33 was **static-only, read not executed**. This
lane had vitest available and **settled it by execution**.

**The inherited wording is REFUTED.** `CLAUDE.md §N.8` instance 3 describes this as *"a
'byte-identical' claim with no byte comparison behind it."* False as worded:
`canonical_serialization_golden.test.ts:335` performs a real `expect(reducerSerialized).toBe(writerSerialized)`,
the suite carries explicit anti-vacuity sanity tests, and it **is** mutation-sensitive —
a behavioural change to the real writer path (`route_writer_adapter.ts`'s `textPartFromBlock`
body) reddens it with an `AssertionError` on the serialized bytes (1 failed / 3 passed).

**What is actually wrong is narrower, and confirmed by construction.** The comparison is against
a **test-owned reimplementation** of the client reducer, never the shipped
`s1LiveAdapter.ts`. The test does not import it: the sole occurrence of that name in the file is
a prose mention in the header (line 21, *"mirroring what `state/s1LiveAdapter.ts` does in
spirit"*). Demonstrated: breaking a real mapping in the shipped adapter (renaming
`case 'primary':` in `mapGrade`, so the primary citation tier stops mapping) leaves **all 4 tests
GREEN**. Scope is also one inline fixture, not the 12-file corpus.

**Disposition: no code change in this lane.** The remedy is the wording amendment to
`CLAUDE.md §N.8` instance 3, which **DVA Ruling 15** assigns to **B-DOCS-GOVERNANCE**, gated on a
VER precondition that instance 3 is actually wrong. This lane does not self-edit `CLAUDE.md`.
The execution evidence above is offered as the input to that precondition — it discharges the
register's static-only caveat.

---

## F-34 · PB-3 §G item 9 "no auto-promotion" — PARKED-HONEST, no detector exists

`00_ARCHITECTURE/briefs/pariprashna_build/REPORT_PB-3.md:34` grades item 9 **VERIFIED-FIXED**
while the same table cell discloses: *"this property has no dedicated detector/CI test — it is
currently true only by inspection, and would not by itself catch a future regression."* A grade
that contradicts its own evidence in the same sentence.

Independently confirmed: **zero** occurrences of `401` or `403` anywhere under
`platform/tests/pariprashna/`. No test asserts the auth rejection the claim rests on.

**Disposition: flagged, not fixed, and not self-edited.** DVA Ruling 15 assigns the re-grade to
**B-DOCS-GOVERNANCE**: item 9 moves `VERIFIED-FIXED` → `VERIFIED-BY-INSPECTION-ONLY` and stays
open until its detector exists. Writing that detector was explicitly out of this lane's scope.
Recorded here with the evidence B-DOCS-GOVERNANCE needs.

---

## F-35 · MCP post-deploy smoke — NOT-APPLICABLE (cross-ref A3)

Both static gaps re-confirmed on current `main`, then handed on rather than duplicated:

- `mcp_end_to_end_smoke.sh`'s probes all use `curl -s -o /dev/null -w '%{http_code}'` — **status
  only**. A `200` carrying a JSON-RPC `error` body passes every probe.
- `deploy.yml`'s `deploy-mcp` job runs "Promote traffic to latest revision" and then only "Show
  deployment URL". Nothing verifies traffic actually moved — which *is* the INF-2 failure mode
  (a green pipeline that skipped promotion).

The register itself routes this to lane **A3**, whose verdict governs and which owns the
can-fail proof. Counted once, there. No code in this lane.

---

*End of SAMAPTI_B_N8_CI_GATES_DISPOSITIONS v1.0.*
