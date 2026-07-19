---
artifact: BIND_D-4A
type: BINDER (opens D-4a under CONDUCTOR_PROTOCOL.md §2)
version: 1.0
status: OPEN
authored_by: Claude Code (Sonnet 5), conductor session, 2026-07-19
governs: BRIEF_D4A.md "Measurement Foundry"
---

# BIND_D-4A — Wave Open

## §0 — Ratification note
`TEMPORAL_ENGINE_ARC_PLAN_v1_0.md` frontmatter self-declared DRAFT at session start while every
downstream artifact (BRIEF_D4A.md, CLAUDECODE_BRIEF.md, CURRENT_STATE) asserted native ratification
2026-07-19. Native confirmed ratified-in-fact at this session's open (stale stamp only). Frontmatter
corrected in-place. Recorded per CLAUDE.md B.8.

## §1 — Rollback pin (re-probed live, this session, supersedes REPORT_D-3's cached pin)
- `amjis-web` @ `91c5cfcbcda1addf2801d6e946fcbe979b72fdc3`
- `amjis-sidecar` @ `91c5cfcbcda1addf2801d6e946fcbe979b72fdc3`
- `brahma-build-pipeline-job` (`brahma-pipeline` image) @ `91c5cfcbcda1addf2801d6e946fcbe979b72fdc3`
- `amjis-mcp` @ `11377530892799afd8015d3ee9b6ec68efeb0c0d` (unchanged since D-2 — no platform-mcp/ path
  touched by PR #607)
- All three non-mcp services moved together via PR #607 (C-6 tiebreak fix), confirmed against
  `git log` — matches `origin/main` HEAD `91c5cfcb`. This is the correct rollback target if D-4a
  needs emergency revert.

## §1a — Rollback pin update, post-Lane-A-0 (Opus verifier finding, corrected)
Lane A-0's PR #608 (CR-111 fix) touched `platform-mcp/src/tools/retrieval/kala_temporal.ts`, moving
`amjis-mcp` off the §1 pin. Current live state post-A-0 (all four services):
- `amjis-web` / `amjis-sidecar` / `brahma-build-pipeline-job` @ `c1187a8d` (PR #609)
- `amjis-mcp` @ `8f3ace37` (PR #608 — the CR-111 fix; did not move further at PR #609, which only
  touched migrations/writer, not platform-mcp)
**An emergency rollback of Lane A-0 must revert `amjis-mcp` to `8f3ace37`'s predecessor together
with the other three services to `91c5cfcb`** — reverting only web/sidecar/job while leaving mcp at
`8f3ace37` would strand mcp with an unfixed CR-111 while the rest of the stack changes underneath
it. This supersedes §1's original pin for any rollback decision made after Lane A-0.

## §2 — Gate item 7 ("all prior batteries green") — Binder ruling
D-3's §G retrodiction gate is sealed CLOSED_BLOCKED_RED by native disposition (MEMO_D-3_1.md
Option-C: "if §G then fails, that's a true red about the kernel, and it stands"). That RED is a
pre-accepted standing condition, not re-litigated by D-4a (REPORT_D-3.md is explicit: "this gate is
not re-litigated").

**Ruling:** D-4a's gate item 7 reads as **"no NEW battery regression since D-3's sealed state."**
D-3's own RED is excluded from the "all green" requirement as a carried, disclosed, native-accepted
finding. Any battery that was green at D-3 close and turns red during D-4a is a genuine gate-7
failure; D-3's retrodiction RED itself is not re-scored here (that's D-4b's DR-12 adjudication).
This ruling is recorded per ESCALATION_POLICY §1 (route-to-adjudicator class: routine gate-reading
ambiguity, non-integrity, non-doctrine) — no native halt required.

## §3 — Minimal-cascade rebuild scope — Binder ruling
protocol §8.2's stale table entry ("D-4 = L5 calibration assets ONLY") predates the arc split and is
superseded here. D-4a's actual touched surfaces:
- A-0 touches `kala_temporal_bundle`, `ka_sangam`/`date_resolver.py` (python-sidecar service code,
  not itself a build-layer writer output requiring rebuild beyond re-deploy) and the `kala_convergence`
  join path — L3 (Kāla) serving-layer only.
- A-1/A-2/A-3/A-4 touch the `life_events` (LEL) table and new application tables (prospective ledger,
  event ontology) — these are NOT L0-L5 asset-DAG members; they require migration + deploy, not an
  orchestrator chart rebuild.
- **Ruling: scope-limited rebuild = L3 `ka_*` assets only, chart 482012f1 (Abhisek), triggered only
  if CR-109's writer-cardinality fix requires re-materializing `kala_dashas`/`kala_convergence` rows
  (it does — the fix changes what gets written, not just how it's read). No L1/L2/L4/L5 cascade.**
  A-1 through A-4's LEL/ledger/ontology work needs a migration + deploy only, no chart rebuild.

## §4 — Carried D-2 findings #2/#4 — lane ownership
- #2 (C1 nodal-exaltation offset surface asymmetry, Rahu-H2): no D-4a lane touches this surface.
  **PARK-with-owner**: owner = D-4b (calibration wave touches the same signal-scoring surfaces).
  Recorded here so it is not silently dropped a second time (per D4_BRIEF_REVISION_INPUTS §6 finding).
- #4 (`judgment_query` v3 oversize baseline, response >12kb after full trim): re-scopable now that
  D-3's T-6 vedha-frame fix landed, but no D-4a lane owns response-budget work.
  **PARK-with-owner**: owner = D-4b's Grand Bakeoff prep (response surfaces get re-audited there).

## §5 — Promise ledger
Full checklist per the pre-open research pass, 28 rows spanning A-0 through A-6 + carried items +
anti-gaming pass + gate-7. Tracked in this session's TodoWrite; will be re-published as
REPORT_D-4A.md's ledger table at close.

## §5a — Lane A-1 verification note (Opus verifier, ACCEPT-WITH-FINDINGS)
Two non-blocking findings, no code action required: (F1) `_migrations_applied` ledger carries a
stale duplicate-name row for the LEL v2 migration (pre-rebase filename 456, re-landed as 457) —
harmless, migration is idempotent. (F2) `BRIEF_D4A.md §F1` text listed item #3 (dialogues-2001)
among corrections to ingest, while `NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md`'s own ingestion notes
explicitly QUARANTINE it pending native confirmation. A-1 correctly followed the more authoritative,
more specific quarantine instruction and did NOT ingest #3 — verified live (row unchanged, no
correction entry exists). The brief's summary text is stale relative to its own source doc; noted
here for the record, not corrected in the frozen brief.

## §5b — Lane A-2 verification note (Opus verifier, ACCEPT-WITH-FINDINGS)
Extended the pre-existing `brahma_event_ontology` registry (migration 388) rather than duplicating
it; all 27 target classes live with populated DR-13 shape data; schema-violation test 15/15 passing
live. Two non-blocking findings: (1) A-2's "57 LEL rows" enumeration figure is a point-in-time
snapshot — A-1's later append-only ingestion grew the table to 61; the load-bearing 13-category
enumeration itself is unaffected and exact. (2) The migration-456 cross-lane forward-fix (A-1
repairing A-2's broken CHECK constraint, see §5a) is a minor lane-isolation deviation per
CONDUCTOR_PROTOCOL §3's may_touch discipline — judged correct and pragmatic given it was blocking
the whole wave's deploy step and the fix was minimal/semantics-preserving, but recorded here rather
than passed silently, per the protocol's own transparency requirement.

## §5c — Lane A-3 verification note (Opus verifier, ACCEPT — clean)
Highest-stakes check in the wave: sealed LEL test-split (events ≥2020-01-01) contact. Structurally
verified clean — harness has no DB/network/fs access path at all in the diff; every fixture is
synthetic, dated pre-2020. CRPS/log-score, real shuffled-birth + antiphase controls, structural
control-mirroring enforcement (live-demonstrated refusal), and model-agnostic curve() interface all
independently confirmed. 52/52 tests re-run and passing. No findings.

## §5d — Lane A-4 verification note (Opus verifier, ACCEPT-WITH-FINDINGS)
Live adversarial INSERT tests (rolled back) independently reproduced: shape-mismatch rejection,
missing-falsifier rejection, whitespace-falsifier rejection, and filing_method-bypass rejection (DB
CHECK pins filing_method to 'explicit_filing_tool' — chat-mining structurally impossible). 5 live
rows confirmed incl. the 3 named baseline-arc predictions, each with a genuinely checkable falsifier.
LEL-append→outcome-matching hook fired for real against a clearly-marked test fixture row (not
commingled with real native data). Two non-blocking findings: (1) commit message references a
`demo_append_hook.mts` script not present in the merged tree — the demonstration's result is real
and independently re-verified via SQL trace, but the paper trail for how it was produced is
incomplete. (2) §11 governance text confirmed present in the deployed source and DB-corroborated as
wired to production, but the verifier lacked live authenticated HTTP credentials to observe the raw
wire response — a verification-method limitation, not a contradiction.

## §5e — Lane A-5 verification note (Opus verifier, ACCEPT — clean)
Doctrinal guardrail (the headline check for this lane): swept every commit message, artifact header,
and diagnostic summary for ruling-language crossing into a DR-12 adjudication — clean. All "win/
loser/verdict" hits are negations or verbatim quotes of DR-12's own text, explicitly scoped to
"that happens at D-4b." Pre-registration (`PREREGISTRATION_v1_0.md`, commit `03b226f7`, zero score
data) provably precedes the scoring run (`00d1a9d5`, +3.5min) — DR-15(d) anti-gaming satisfied
structurally. Only 1 of 3 models (pratyantar_lord) was scoreable; midpoint_triangle and
transit_kernel are honestly reported as gaps (both throw `NotImplementedModelError`, no fabricated
curve) per B.10 — noted as an open gap for D-4b, not a defect of this lane. Harness untouched
(0 modified files), scoring pass read-only against LEL. Diagnostic numbers (informational, NOT
adjudicatory per the lane's own framing): pratyantar_lord underperforms shuffled-birth control on
primary CRPS/skill in all 5 domains (skill -1.93 to -2.40) but beats antiphase control in 4/5;
legacy hit-rate metric points the opposite direction (real beats/matches shuffled in 4/5 domains).
This primary-vs-secondary metric disagreement is exactly the kind of diagnostic signal D-4b exists
to adjudicate — explicitly not resolved here.

## §7 — Wave-level verification summary
All 6 implementer lanes (A-0 through A-5) independently adversarially verified by a fresh-context
Opus verifier per CONDUCTOR_PROTOCOL's "unverified = not done" standard. Verdicts: A-0
ACCEPT-WITH-FINDINGS (2 findings, both fixed via follow-up PR #610 + BIND update). A-1
ACCEPT-WITH-FINDINGS (2 findings, both governance/cosmetic, no action required). A-2
ACCEPT-WITH-FINDINGS (2 findings, both governance/cosmetic, no action required). A-3 ACCEPT, clean
— zero findings, including the wave's single highest-stakes check (sealed LEL test-split contact).
A-4 ACCEPT-WITH-FINDINGS (2 findings, both auditability/verification-method gaps, no functional
defect). A-5 ACCEPT, clean — zero findings requiring remediation, doctrinal guardrail confirmed
clean. Zero REJECT verdicts. Zero circuit-breaker trips. One cross-lane deploy-blocking bug found
and fixed forward (A-1 repairing A-2's migration-456 CHECK-constraint subquery bug) — logged as a
minor, defensible lane-isolation deviation per CONDUCTOR_PROTOCOL §3, not treated as a defect.

## §6 — Lane dispatch order (confirmed)
A-0 (solo, root dependency) → A-1 ∥ A-2 (A-2 may start once A-0's serving contract is stable; A-1
starts strictly after A-0 merges) → A-3 (after A-2) → A-4 (after A-3) → A-5 (after A-4, pre-registers
before scoring). A-6 (docs-only) runs now, in parallel with everything, conductor-owned.
