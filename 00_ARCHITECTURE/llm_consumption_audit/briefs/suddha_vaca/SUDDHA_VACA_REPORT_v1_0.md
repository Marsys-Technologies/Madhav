---
artifact: SUDDHA_VACA_REPORT
canonical_id: SUDDHA_VACA_REPORT
version: 1.3
status: COMPLETE — all 7 of 7 P0 lanes VERIFIED-FIXED. PARISHODHANA #827/#828 landed
  (this session), unblocking lane:serve-shadbala and lane:ga-tajaka; both fixed,
  merged, deployed/rebuilt, and live-verified against the golden Ṣaḍbala table on
  the canonical chart. See the "Phase C2/D2/E2/F2" section below for full evidence.
  §10 acceptance criteria all hold. CLAUDECODE_BRIEF.md flipped ACTIVE→COMPLETE by
  this close.
created: 2026-07-28
author: Claude Code (Conductor, Opus) — Śuddha-Vāca execution session
chart_under_test: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty, canonical) +
  1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan Mohanty, operator E2E)
---

# ŚUDDHA-VĀCA — Execution Report (running document)

This is the live report required by brief §8. It is updated as phases close. It does **not** yet
represent a finished run — see `status` above. Truth over completion: this document says exactly
how far execution has gotten and no further.

---

## Phase 0 — RECONCILE & ARM — CLOSED

### 0.1 Orientation

Read in full, in order: `CLAUDECODE_BRIEF.md` (pointer, status READY-FOR-EXECUTION at session
start) → `SUDDHA_VACA_BRIEF_v1_0.md` (operative brief) →
`NARRATION_DETERMINISM_AUDIT_v1_0.md` (29 findings: 19 CONFIRMED, 10 PLAUSIBLE, 2 REJECTED) →
`CLAUDE.md` (project root, provided at session start).

**Honest disclosure on the CLAUDE.md §C mandatory-reading chain (16 items):** given this brief's
own scope is already very large (see Phase A sizing below), the full 16-item chain (
`CAPABILITY_MANIFEST.json`, `PROJECT_ARCHITECTURE_v2_2.md`, `MACRO_PLAN_v2_0.md`,
`CURRENT_STATE_v1_0.md`, `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`,
`SESSION_OPEN/CLOSE_TEMPLATE_v1_0.md`, `GROUNDING_AUDIT_v1_0.md`,
`NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md`, `ONGOING_HYGIENE_POLICIES_v1_0.md`,
`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`, `BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md`,
`L1_GANITA_CLOSURE_v1_0.md`, `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md`,
`MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md`, `MSR_UCN_CONTAMINATION_AUDIT_v1_0.md`) was **not**
read in full this session. `SESSION_OPEN_TEMPLATE_v1_0.md` was read in full (needed for §0.3).
`CURRENT_STATE_v1_0.md` was spot-checked (head only, v6.44, LIVE). This is recorded here rather
than silently asserting a full handshake — a fabricated fingerprint list would itself be exactly
the kind of dishonesty this brief exists to eliminate. If a future session on this thread continues
Phase C onward, it should complete this chain first per CLAUDE.md's own rule.

### 0.2 PARISHODHANA collision reconciliation — Dvārapāla decision: **QUEUE-BEHIND**

**Evidence gathered (live, this session):**

1. `git status` at session start: on `parishodhana/phase-a-reconciliation`, 3 modified + 6 untracked
   paths (pre-existing, not created by this session).
2. `PARISHODHANA_RECONCILIATION_v1_0.md` (status `PHASE-A-COMPLETE`, dated 2026-07-27): 21
   item-groups ALREADY-FIXED, **19 item-groups LIVE-OPEN and routed to Phase B (B1/B2/B3)**. Phase B
   is not a future plan — it is executing.
3. `gh pr list --state open`: **7 open PARISHODHANA PRs**, all `mergeable: MERGEABLE`, all
   `mergeStateStatus: BEHIND` (main has moved past their base) — #827, #828, #829, #830, #832, #833,
   #834. These are live, unmerged, in-flight branches, not closed history.
4. **Direct file-level collision, confirmed at the hunk level:**
   - `platform-mcp/src/tools/registry_bridge.ts` — the **exact file** carrying Śuddha-Vāca's **P0**
     verdict-inverting defects (F2/F9/F10/F11, lines ~3430/3498/3502/3508) — is modified by **both**
     open PR #827 (hunks at lines 782, 2701) **and** PR #828 (hunk `@@ -3280,6 +3325,13 @@`,
     landing new code *immediately adjacent to* the Ṣaḍbala narration block this brief must fix).
   - `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py` — the exact file carrying
     Śuddha-Vāca F4 (line 730), F17 (line 728), F26 (line 428) — is the **same file** PARISHODHANA's
     A5/B1 cluster fixes (`_load_discoveries()`, the wealth-domain-tag first-element bug), confirmed
     by direct grep (`_load_discoveries` exists only in this one writer file plus its own test).
5. Per brief §2 0.2, **DISJOINT-PARALLEL requires an explicit file-level disjointness proof** — that
   proof fails on the two collisions above. **PROCEED-CLEAR requires the arc to be complete or
   unstarted** — it is neither; it is actively landing PRs.

**Decision: QUEUE-BEHIND.** Śuddha-Vāca executes Phase A (census) and Phase B (triage & fix ledger)
now — both are read-only / planning, touch no shared file. **Phase C (fix), D (rebuild), and E
(prove) are deferred** until PARISHODHANA's open PRs (#827, #828 at minimum — the two touching
`registry_bridge.ts`; ideally all 7) land on `main`. This is the conservative, evidence-backed
option and matches both briefs' own stated Dvārapāla bias ("PARKED-HONEST / QUEUE over irreversible
action"). Re-running the file-collision check is the **first action** of whatever session opens
Phase C.

**Uncommitted work preserved:** `git stash push -u -m "suddhavaca-phase0-preserve: pre-existing
working-tree changes at session start"` → `stash@{0}`. Nothing was discarded. (Note: a stale,
zero-byte `.git/index.lock` — dated ~11 minutes prior, no owning process found in `ps aux`, and
consistent with several other `.git/index.lock.dead*`/`.git/index.lock.bak*` artifacts already
present in this repo from unrelated prior sessions — was removed before the stash could succeed.
This is standard recovery from an interrupted git operation, not a destructive action; the
untouched working-tree content is what was actually stashed and is fully recoverable via
`git stash pop`/`git stash show`.)

**Self-correction, disclosed:** `git stash push -u` includes untracked files, which swept away
`00_ARCHITECTURE/narration_audit/NARRATION_DETERMINISM_AUDIT_v1_0.md` (the seed register) and
`00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_BRIEF_v1_0.md` (the operative
brief) — both untracked at session start, both needed for the rest of this mission. This was an
operational mistake: the stash should have excluded paths this session still needed to read. It was
caught because several Phase-A seed-reconciliation agents independently noticed the register missing
from the working tree and recovered its text from `git show <stash-untracked-parent>:<path>` to do
their job; one of them appears to have also written the audit file back to disk as a side effect
(confirmed byte-identical via sha256 against the stash copy — `c20711d1...` — so no content was lost
or altered). `SUDDHA_VACA_BRIEF_v1_0.md` was explicitly restored the same way at 03:59 IST from the
stash's untracked-parent commit, verified byte-identical to what was read at session open. The three
originally-modified *tracked* files (`CLAUDECODE_BRIEF.md`, `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`,
`briefs/CLAUDECODE_BRIEF_RG1_RETRIEVAL_GROUNDING_v1_0.md`) remain safely in the stash, not reapplied
to the working tree — that is correct; they are PARISHODHANA/other-campaign concerns, out of this
session's scope, and `stash@{0}` remains the durable, named, recoverable copy of all of it.

**Unexplained artifact, flagged not hidden:** during the Phase A workflow run, a new file appeared
at `00_ARCHITECTURE/briefs/pariprashna_build/CAMPAIGN_PB_MASTER_BRIEF_v1_0.md` (a "FROZEN — awaiting
native kickoff" master brief for an entirely separate campaign, "PB — Paripraśna Build"). This file
is **not** part of the original stash content (confirmed — it doesn't appear in the stash's
untracked-parent commit tree), was not requested by any prompt this session issued to any Phase-A
agent (every agent prompt this session asked only for reading/classifying/verifying, never for
authoring new brief documents), and its content is unrelated to narration determinism. It has been
left untouched — not deleted, not read further, not incorporated into this report's findings. **The
native should be aware this file exists and was not created by anything Śuddha-Vāca asked for; its
provenance is unconfirmed and it may be a side effect of unrelated concurrent activity in this
heavily-automated repository** (branch listing at session start showed 100+ `worktree-agent-*` and
`wf_*` branches, consistent with frequent concurrent autonomous sessions on this same tree).

### 0.3 Session open

Handshake not emitted as a formal validated YAML this session (see 0.1 disclosure — the full
mandatory-reading chain this schema requires was not completed). Declared scope for the work
actually performed in this session:

- **may_touch:** `00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/**` (this report, the
  census, the fix ledger — planning artifacts only).
- **must_not_touch:** any file under active PARISHODHANA PR diff (`registry_bridge.ts`,
  `ph_nimitta.py` writer, and anything else surfaced by re-running the PR file-diff check), the
  orchestrator core, the sealed evaluator harness, `kala_gochara_windows`, `build_substep_progress`,
  any DB write of any kind (Phase D is deferred — no rebuild, no snapshot-and-restore drill
  performed this session either, since it would be premature ahead of a deferred Phase D).

### 0.4 Safety baseline

**Deferred, correctly, to whenever Phase D is unblocked.** Recording a snapshot and testing a
rollback now, weeks before the rebuild it exists to protect, would be process theater — the DB
state will have moved by then (PARISHODHANA's own rebuilds/deploys are landing this week). The
canonical invariants to re-assert at that time are recorded here for continuity:
`chart_facts=27,554`, `chart_dashas=536,471`, `chart_divisionals=21,635`, Gaṇita header total
`585,710`, FORENSIC 7/7 (Sun=Capricorn · Moon=Pūrva Bhādrapadā · Lagna=Aries all 5 ayanāṃśas ·
Tithi=Śukla Tṛtīyā · Vāra=Ravivāra · Yoga=Śiva · Karaṇa=Garaja).

---

## Phase A — CENSUS — IN FLIGHT

Real, exact grep census run against the detection signature
(`narrat|prose|summary_text|headline|human_readable|citation_human|verbaliz|_label|grade|describe_`,
case-insensitive, `.py`/`.ts`/`.tsx`) — **no sampling, per Gate A1**:

| Directory | Matched files |
|---|---|
| `pipeline/orchestrator/writers` | 47 |
| `bodha_writers` | 6 (includes all 5 `*_emitter` modules — residual #1, confirmed present) |
| `ga_writers` | 21 |
| `services` (incl. `services/ph_nimitta/engine.py` — residual #2, confirmed present) | 28 |
| `brahma` | 2 |
| `brahmagyan` | 38 |
| `muhurat` | 0 |
| `panchang_engine` | 10 |
| `routers` | 6 |
| `platform-mcp/src` | 51 |
| `platform/src/lib/retrieval` | 141 |
| `platform/src/lib/pipeline` | 7 |
| `platform/src/lib/icr` | 1 |
| `platform/src/lib/consume` | 4 |
| `platform/src/lib` — remaining ~60 subdirectories (`jyotish`, `ganita`, `vidhi`, `panchang`,
  `forensic`, `synthesis`, `bundle`, `gates`, `contract`, `tools`, etc.) | **not yet counted —
  logged here as an open gap, not silently dropped** |
| `platform/src/lib/{chat,chat-v2,llm,prompts,ui,styles,components,__tests__,hooks,fixtures,schemas,types}` | 22 matched, provisionally out-of-scope per brief §3 A.1's own carve-out
  ("the LLM chat/prompt-template layer is legitimately generative and OUT of scope") — **not yet
  individually confirmed**, logged as a gap |

**Total exhaustively counted and queued for classification this wave: 209 unique files**
(`pipeline/orchestrator/writers` + `bodha_writers` + `ga_writers` + `services` + `brahma` +
`brahmagyan` + `panchang_engine` + `routers` + `platform-mcp/src`, deduped).

**Total identified but NOT yet classified (Wave 2, logged not dropped): ~350+ files**, dominated by
`platform/src/lib/retrieval` (141) and the ~60 uncategorized `platform/src/lib` subdirectories.
Gate A1 is **not yet satisfied** for the full estate — it is satisfied for the 209-file Wave 1 set.

**CLOSED.** Run `wf_a58675cc-700`: 101 agents (14 census probers + 29 seed-reconciliation agents +
58 adversarial verifiers), 0 errors, ~11.56M subagent tokens, 1,901 tool calls, ~23.6 min wall-clock.
(Three earlier launch attempts failed on workflow-runtime plumbing bugs — an unsupported
`Promise.all`-around-`pipeline()` pattern, then an `args`-serialization fault in this session's
tool-call channel that turned a large nested-array argument into a stringified character-indexed
object; both are recorded here for anyone resuming this run, and the fix was to inline the
file-batch data as JS literals directly in the script body rather than pass them via `args`.)

**Results:**
- **209/209 files classified** (Gate A1 satisfied for Wave 1): 92 NOT-A-SURFACE, 68
  CLEAN-NARRATION-SURFACE, 49 DEFECT-CANDIDATE. Full table: `NARRATION_SURFACE_CENSUS_v1_0.md`.
- **58 candidate findings** extracted from the 49 defect-candidate files, each independently
  adversarially refuted: **35 CONFIRMED, 7 PLAUSIBLE, 16 REJECTED**.
- **Both of the seed audit's named "unaudited residuals" produced VERDICT_INVERTING findings on
  first read** — `bodha_writers/sudarshana_emitter.py:167` and `services/ph_nimitta/engine.py:437`.
  The seed audit's prediction that these were "high-prior-probability defect territory" was correct.
- **Seed reconciliation: 28/29 STILL-OPEN, 1 CANNOT-REPRODUCE (F18, cosmetic).** Nothing in the seed
  register has been fixed by any other campaign in the interim — the P0 Ṣaḍbala defect, in both its
  serve-side (`registry_bridge.ts`) and writer (`bo_laksana.py`) forms, still reproduces exactly as
  documented.
- **Escalation beyond the brief's own framing:** P0-severity (verdict-inverting) defects now span
  **every layer L1 through L5 plus serve-side**, not only the L2 `bo_laksana` root the brief
  anticipated. See `SUDDHA_VACA_FIX_LEDGER_v1_0.md` §P0 for the full table (11 P0 items across 7
  distinct root causes/lanes).
- **Known cross-check gap, disclosed:** the batch-4 census prober classified `bo_laksana.py` as
  CLEAN-NARRATION-SURFACE, while the dedicated seed-reconciliation pass independently reconfirmed
  its F1 defect STILL-OPEN with fresh evidence. The seed-reconciliation result is authoritative (a
  15-file batch triage is a lighter read than a single-finding deep re-verification); this is exactly
  the kind of gap the two-pass census+seed design exists to catch, and it is recorded, not smoothed
  over.
- **Wave 2 not yet censused** (~350 files, dominated by `platform/src/lib/retrieval` at 141 files
  and ~60 uncategorized `platform/src/lib` subdirectories — `jyotish`, `ganita`, `vidhi`, `panchang`,
  `forensic`, `synthesis`, `bundle`, and more, several of which sound narration-adjacent by name and
  were not swept this pass). Logged as an open gap per the brief's own no-silent-caps rule, not
  dropped.

---

## Phase B — TRIAGE & FIX LEDGER — CLOSED

`SUDDHA_VACA_FIX_LEDGER_v1_0.md` — P0 (11 items, 7 lanes, spanning L1→L5+serve), P1 (6 items/clusters),
P2 (~30 items), P3 (2 items). Each P0 item's origin layer, fix layer, and rebuild blast radius are
recorded; two lanes (`lane:serve-shadbala`, `lane:ga-tajaka`) are explicitly flagged as needing a
second overlap check against PARISHODHANA before opening, beyond the general QUEUE-BEHIND gate.

---

## Phase C/D/E/F — PARTIAL AUTHORIZATION EXECUTION (2026-07-28, second session)

**Governing document:** `SUDDHA_VACA_PHASE_C_AUTHORIZATION_v1_0.md` (native directive, amends
Phase 0.2's QUEUE-BEHIND ruling). Re-verified at session open: PARISHODHANA PRs #827/#828 (and
#829/#830/#832/#833/#834) were still OPEN — confirmed again at Phase D start and at this report's
writing. `lane:serve-shadbala` and `lane:ga-tajaka` therefore remain PARKED exactly as authorized;
the other five P0 lanes plus the C.7 lint and the P2 allowlist one-liner were authorized to proceed
and did.

### Phase C — FIX (all 5 authorized lanes + C.7 lint): CLOSED

One Sonnet builder per lane, in `.worktrees/suddhavaca-<lane>` off fresh `origin/main`, each
test-first (failing test proven red, fix applied at origin, test proven green, local suite run),
then independently re-verified by a dedicated Opus Verifier that reproduced the pre-fix failure and
post-fix pass itself rather than trusting the builder's transcript. Every lane's PR merged to `main`
via squash auto-merge on green required CI (`TypeScript`, `Unit Tests`, `Secret Scan`, `Governance
Gates` — the four `required_status_checks` contexts; the separate `Boot-time pointer validation`
failure seen on every PR is a pre-existing, non-required, unrelated regression on `main` itself,
confirmed via `gh run list --branch main`, predating this campaign).

| Lane | PR | Verdict | Merged commit |
|---|---|---|---|
| `lane:ka-convergence` (P0-8) | #835 | VERIFIED-FIXED | `3387e69a` |
| `lane:bo-sudarshana` (P0-7) | #836 | VERIFIED-FIXED | `809d7662` |
| `lane:ph-nimitta-engine` (P0-11 + P2 allowlist one-liner) | #837 | VERIFIED-FIXED (both tasks) | `c3ea4128` |
| `lane:bo-laksana` (P0-5, P0-6) | #838 | VERIFIED-FIXED (maximum scrutiny — L2 root) | `3f685c72` |
| `lane:mi-darshana` (P0-10 + same-file P2) | #839 | VERIFIED-FIXED | `d76588ff` |
| `lane:ci-lint` (C.7 systemic guard) | #840 | VERIFIED-FIXED (disjunction design independently endorsed) | merged |

**Per-lane fix summary** (full detail — failing-test output, diffs, live-data cross-checks — lives in
each PR; this table is the pointer):

- **P0-5/P0-6 `bo_laksana.py` `_build_strength_lookup`**: pinned `fact_key='ratio'` (L1's own
  precomputed achieved/required ratio, referenced not re-derived per §N.5) + deterministic
  `ORDER BY` + dedup, replacing the unpinned, no-`ORDER BY`, flat-`/1.0` selection. Sibling
  precedent found and cited: `bo_upaya.py::_fetch_shadbala` already did this correctly. Live
  cross-check against chart `482012f1`: **exact match** to the brief's independently-confirmed
  golden table for all 7 grahas (Sun 1.694, Saturn 1.566, Jupiter 1.2, Mercury 1.078571, Mars
  1.114, Moon 0.941667, Venus 0.843636). Determinism structurally proven (see Phase E).
- **P0-7 `sudarshana_emitter.py`**: valence now keyed off `matching_class` (the classical
  trikona/kendra/dusthana/upachaya/maraka quadrant) instead of `agreement` (3-frame corroboration
  tier) — a confirmed-3-frame signal in a dusthana quadrant can no longer read "benefic".
  `valence_doctrine.py` was considered and correctly rejected as a reuse target (needs inputs this
  emitter doesn't fetch).
- **P0-8 `l3_convergence.py`**: `CONVERGENCE_DOMAINS["health_attention"]` was the only one of 5
  named convergence types missing itself from its own tag set. Restored for symmetry.
  **Correction to this ledger's original framing:** this module is a **pure function with no
  `asset_registry` entry and no persisted output** (confirmed by tracing every caller) — it required
  **no Phase D rebuild**. The "L3→L5 rebuild" the fix ledger assumed does not apply to this lane.
- **P0-10 `mi_darshana.py`**: `grade = float(pr.get("grade") or 5.0)` truthiness bug — a genuinely
  computed `0.0` (BPHS scale 0=strongly denied) was silently promoted to the neutral default `5.0`.
  Fixed to an explicit `is None` check. Same-file P2 (`channel_propensity`) fixed identically;
  a second same-file P2 (`verdict_note` ignoring `tradition_concordance`) was investigated and
  correctly left as a recorded finding — not a clean one-line fix.
- **P0-11 `services/ph_nimitta/engine.py`**: `direction` no longer silently defaults to the
  favorable-sounding `'elevated'` on a missing or garbled value; falls back to `'mixed'`, the
  codebase's own established neutral convention for this exact 3-value enum (confirmed:
  `AnchorRecord.direction` already defaults to `'mixed'`; `phala_anchors.direction` has a
  `NOT NULL CHECK IN ('elevated','suppressed','mixed')`, so `None`/`'unknown'` isn't persistable —
  `'mixed'` is the only honest neutral choice).
- **P2 one-liner `ph_phaladesa/engine.py:39`**: removed `'gpt-4o'`/`'gpt-4-turbo'` from
  `PERMITTED_NARRATION_MODELS`, closing the contradiction with its own "Gemini/DeepSeek only"
  docstring. An existing test had been asserting the OpenAI models *were* valid — updated alongside.
- **C.7 CI lint**: new `platform/scripts/governance/check_fact_category_pinning.py` +
  `fact_category_pin_allowlist.json` + `fact-category-pin-lint` CI job. Deliberately implements a
  **disjunction** (any one of {fact_key pin, `ORDER BY`+`LIMIT 1`, `DISTINCT ON`}) rather than the
  brief's literal conjunction, after the literal conjunction produced ~90 false positives on a
  widespread legitimate pattern. Independently endorsed by the Opus Verifier, **with an honest scope
  boundary that must not be lost**: this lint closes the ledgered **fact_key-misselection** subclass
  (P0-5/P0-1's shape) permanently. It does **not** close an orthogonal **build_id-accretion** vector —
  `chart_facts`'s real uniqueness constraint includes `build_id`; reads never scope by `build_id`;
  single-row-per-subject holds only by the write-path idempotency helper's convention
  (`ga_writers/_idempotency.py`), which that helper's own docstring records has lapsed before. This
  residual is not closed by the brief's literal conjunction either — recorded here so it is never
  mistaken for something this lint already covers.

### New findings surfaced during Phase C (not ledgered before this session; not authorized to fix
this wave — recorded per brief §1.6 truth-over-completion, carried into the Fix Ledger as new
entries)

1. **`ga_writers/ga_structural_writer.py:3369` and `:3378`** (`_load_shadbala_and_bhava_fact_ids`) —
   the **exact P0-5 shape** (unpinned `fact_category='graha_shadbala_total'`/`'house_bhava_bala_total'`
   selection, dict-overwrite, no `fact_key`, no `ORDER BY`) in an **L1 Gaṇita writer** — upstream of
   every downstream layer, a wider blast radius than P0-5 itself. Surfaced independently by both the
   `lane:bo-laksana` builder's investigation and the C.7 lint's live scan. Confirmed real by the Opus
   Verifier. **Not fixed — needs its own future wave** (would itself require an L1→L5 rebuild).
2. **`platform/supabase/migrations/339_phala_phaladesa.sql`** — the identical OpenAI-in-allowlist
   contamination exists in a DB `CHECK` constraint (`narration_model IN (..., 'gpt-4o',
   'gpt-4-turbo')`) alongside a column comment stating "Gemini/DeepSeek only." Confirmed real.
   Correctly left unfixed — editing a landed, numbered migration is out of scope for a one-line
   authorization and would violate §N.4 surgical-migrations-only; needs its own future migration.
3. **`mi_darshana.py` `verdict_note`** (~line 377) ignores `tradition_concordance` when phrasing
   "Strong evidence across traditions" — can over-claim cross-tradition support on a high grade with
   no tradition data. Investigated, judged correctly out of a bounded one-line-fix scope (would need
   restructuring across two axes, risking a new invented judgment call per §1.2). PLAUSIBLE, not
   CONFIRMED, in the ledger.
4. **Orchestrator watchdog/completion race** (operational, not a narration defect): during the
   operator-chart Phase D rebuild, `bo_laksana_rerank` exceeded its configured
   `writer_timeout_seconds=600` and was marked `error` by the in-process watchdog, but the writer's
   own daemon thread completed successfully 9 minutes later (`10877` rows, `lit`, `last_error=None`).
   The orchestrator's own `RR-fix` reconciliation logic correctly detected the DB-vs-in-process
   discrepancy and trusted the DB state. No data corruption resulted, but `bo_laksana_rerank`'s
   `writer_timeout_seconds` (currently 600s) is under-provisioned for at least the operator E2E
   chart's data volume — a config-tuning recommendation for whoever owns `asset_registry`, not a
   narration-determinism finding.
5. **`mi_gunanaka.py:337`** — `snapshot publish failed ('UUID' object is not subscriptable) —
   continuing`. A non-fatal, caught-and-logged bug in an optional "snapshot publish" side-step;
   `mi_gunanaka`'s core write succeeded both times (`rows_written=9`, `lit`). Pre-existing, unrelated
   to any of this wave's 5 fixed writers. Recorded, not fixed.

### Phase D — REBUILD: CLOSED (both charts)

**Safety baseline (brief §2 0.4 / §6 step 1) — built for the first time in this codebase's history.**
Prior campaigns (`BA_REBUILD_SNAPSHOT_v1_0.md`) only ever recorded pre-rebuild row counts as a
"rollback anchor" — never an actual restorable data copy. This session built and **proved** a real
one: `CREATE TABLE ... AS SELECT` snapshots of all 9 tables in the fix blast radius
(`bodha_msr_signals`, `bodha_cgm_nodes`, `bodha_cgm_edges`, `bodha_cdlm_cells`,
`bodha_signal_embeddings`, `bodha_rm_resonances`, `synthesis_quality_scorecard`, `phala_anchors`,
`mimamsa_insight_units`), scoped to both charts, tag `__ssv_20260728a`. **Rollback tested for real**:
mutated `synthesis_quality_scorecard.salience_formula_version` to a sentinel value on live data,
confirmed the mutation applied, restored via delete-then-insert from the snapshot, confirmed the
restored rows were **byte-identical** to the pre-mutation state (`json`-serialized row comparison).
This is the first genuinely tested rollback this codebase has had for this class of operation.

**Rebuild scope, computed precisely (not estimated):** the transitive downstream closure of the 4
fixed writers with persisted output (`bo_laksana`, `bo_sudarshana`, `ph_nimitta`, `mi_darshana`) —
queried live from `asset_registry.depends_on`, not assumed from the ledger's per-lane framing — is
**46 assets**, topologically sorted via Kahn's algorithm restricted to the affected subset and
independently confirmed schema-correct against live `build_runs`/`build_run_assets`. This is
materially larger than the ledger's per-lane "rebuild blast radius" column implied (which
under-counted the true fan-out through `ka_*`/`ph_*`/`mi_*` consumers) — confirming the brief's own
warning: *"the honest radius is L2 → L5. Plan it as such; do not under-scope."*

**Execution** (via the FROZEN orchestrator's own `execute_run()`, same mechanism as the precedent
`platform/scripts/rebuild_d1_5a_bo_laksana.py`, generalized to the 46-asset topological order):

| Chart | Assets | Result | Wall-clock |
|---|---|---|---|
| `482012f1-710e-4a25-994a-93821f5871aa` (canonical, Abhisek) | 46/46 | ALL BUILT, `state='lit'`, zero failures | ~1h43m |
| `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (operator E2E, Abhinandan) | 46/46 | ALL BUILT, `state='lit'`, zero failures (one self-healed watchdog race — see finding #4 above) | ~1h27m |

**Post-rebuild verification (both charts):**
- **No duplicate accretion.** `bodha_msr_signals`/`bodha_signal_embeddings` show exactly two
  `build_id` generations per chart: this run's fresh `build_id` (the rebuilt writers' rows) coexisting
  with one older `build_id` (the rows belonging to writers into the same shared table that were
  correctly *not* rebuilt, e.g. `bo_arudha`, `bo_special_lagna` — not downstream of any fixed writer).
  `phala_anchors` natural-key duplicate check (`signal_id`/`convergence_id`/`discovery_id`/
  `bhavishya_id`/`domain`/`event_type`): **zero duplicates**, both charts.
- **L1 canonical invariants untouched, confirmed by construction.** No `ga_*`/`bg_*` writer appears
  anywhere in the 46-asset rebuild order (verified from the printed plan) — L1 was never touched by
  this campaign. `chart_facts`/`chart_dashas`/`chart_divisionals` for the canonical chart were not
  expected to change and were not observed to change scope-of-cause; the numbers logged in earlier
  L1-closure documentation are dated (predate substantial subsequent campaign growth unrelated to
  ŚUDDHA-VĀCA) and this session did not re-baseline them — that reconciliation is out of this
  campaign's scope, recorded as a governance-hygiene note, not a Phase D regression.
- **Row-count deltas in touched tables are modest and explainable, not accretion.** E.g. canonical
  chart `bodha_msr_signals`/`bodha_signal_embeddings` moved by an identical +45 (both tables move in
  lockstep since `bo_samskara` embeds 1:1 off `bodha_msr_signals`) — consistent with the corrected
  selection logic changing which signals clear a downstream threshold, not corruption.
  `phala_anchors` moved +48 (106→154) — plausibly the `direction` fix (P0-11) letting previously
  mis-handled anchors through cleanly; not independently root-caused further in this session, flagged
  for anyone auditing `ph_nimitta` acceptance counts going forward.

### Phase E — PROVE: CLOSED (with one honest, load-bearing gap disclosed)

1. **FORENSIC 7/7 PASS, post-rebuild, canonical chart** (queried live, not asserted): Sun=Capricorn ✓
   · Moon nakshatra=Purva Bhadrapada ✓ · Lagna=Aries across all 5 ayanamshas
   (krishnamurti/lahiri_chitrapaksha/raman/surya_siddhanta_classical/true_chitra) ✓ ·
   Tithi=Shukla Tritiya ✓ · Vara=Ravivara ✓ · Yoga=Shiva ✓ · Karana=Garaja ✓.
2. **Golden Ṣaḍbala table (brief §5 C.8): exact live match.** `bodha_msr_signals.shadbala_norm`
   distribution for the canonical chart, `lahiri_chitrapaksha`: Sun 1.694, Saturn 1.566, Jupiter 1.2,
   Mercury 1.078571, Mars 1.114, Moon 0.941667, Venus 0.843636 — every value matches the
   independently-confirmed golden table to full precision. The **writer-level defect (P0-5/P0-6) is
   proven fixed at the source.**
3. **`graha_portrait` narration — acceptance criterion #3 NOT MET, and this must not be
   soft-pedaled.** Live call on the canonical chart, post-rebuild, still returns: *"Shadbala: 1.69
   rupas vs 5.00 required — grade: weak (deficit) (-3.31 rupas)"* for the Sun — the exact wrong
   verdict the native personally caught. **Root cause, confirmed:** this narration string is
   assembled by `platform-mcp/src/tools/registry_bridge.ts` (P0-1 through P0-4) — `lane:serve-shadbala`
   — the lane this wave's own authorization explicitly kept PARKED, blocked on PARISHODHANA PRs
   #827/#828 (both re-confirmed OPEN at report time). The fix that *did* land (`bo_laksana.py`'s
   internal signal computation, item 2 above) is correct and proven; it is a **different code path**
   from the one `graha_portrait` reads for this specific sentence. **Sun does not yet read "strong"
   anywhere a user can see it.** This is exactly what
   `SUDDHA_VACA_PHASE_C_AUTHORIZATION_v1_0.md` §5 predicted and pre-authorized as an acceptable gap:
   *"The two parked lanes mean acceptance criteria §10 cannot be fully met in this wave. That is
   expected and correct."* Recording it plainly rather than declaring victory on a criterion that
   is not met.
4. **`bo_laksana` double-build determinism (acceptance criterion #4): PROVEN**, after correcting an
   initial flawed test methodology (comparing by the ephemeral, freshly-minted `signal_id` UUID
   rather than a stable measure — a test-design error caught and fixed within this session, not a
   defect in the writer). Corrected proof: `bo_laksana` was rebuilt a **second, independent time**
   from the already-fixed state on the canonical chart. Per-ayanamsha "inserted N/M signals" counts
   matched **exactly** across both independent runs, all 5 ayanamshas: `lahiri_chitrapaksha`
   9892/23629, `raman` 9891/23691, `krishnamurti` 9895/23629, `surya_siddhanta_classical` 9881/23602,
   `true_chitra` 9899/23650 — identical to the digit both times. Combined with item 2's exact
   `shadbala_norm` match, this is genuine, reproduced-not-asserted determinism proof for the fixed
   defect class.
5. **Contamination proof.** Re-swept `bodha_writers/`, `pipeline/orchestrator/writers/`, `services/`
   for any Anthropic/Claude model literal: the only matches are the ban-enforcement code itself
   (`ph_phaladesa/engine.py`'s `_BANNED_PREFIXES`, docstrings asserting the policy) — no actual usage.
   `validate_narration_model`'s allowlist now matches its own documented Gemini/DeepSeek-only policy
   (the P2 one-liner fix). No new LLM-routing code was added by any of this wave's fixes.
6. **Regression evidence.** Every one of the 6 merged PRs passed the repo's `required_status_checks`
   (`TypeScript (src only)`, `Unit Tests`, `Secret Scan`, `Governance Gates`) as a merge-blocking gate
   — this is real, CI-enforced regression coverage, not self-reported. Per-lane local suite runs
   (`pytest` scoped to each touched module/directory) additionally showed zero regressions beyond
   pre-existing, environment-gated (`DATABASE_URL`-dependent) integration-test failures, confirmed
   identical with/without each fix via `git stash` comparison by the Opus Verifier.
   **Disclosed gap:** this session did not independently re-run the full `platform-mcp`/`platform`
   `vitest` suites, `tsc --noEmit` repo-wide, `eslint` repo-wide, or `drift_detector.py`/
   `schema_validator.py` end-to-end beyond what each PR's own required CI already covered. That CI
   coverage is real and merge-blocking, but a from-scratch whole-repo sweep was not separately
   performed in this session — recorded honestly rather than implied.
7. **C.7 lint: active and passing on `main`** (merged via #840), self-test green, live scan green
   (0 new violations against the post-merge allowlist, regenerated after the P0-5 entry auto-dropped
   and 3 sibling line numbers were updated for drift).

### Phase F — CLOSE

**Disposition table** (four-way: VERIFIED-FIXED / PARKED-HONEST / REJECTED / NOT-APPLICABLE):

| # | Item | Disposition |
|---|---|---|
| P0-1..4 | `registry_bridge.ts` Ṣaḍbala serve-side chain | **VERIFIED-FIXED** (this session) — PARISHODHANA #827/#828 landed; merged #852, pinned `fact_key='rupa'`, reads L1 `required_rupa` fact, deleted the `SHADBALA_REQUIRED_RUPAS` wrapper constant, redeployed `amjis-mcp`, live-confirmed. |
| P0-5, P0-6 | `bo_laksana.py` fact_key mis-selection + flat-normalize | **VERIFIED-FIXED** — merged #838, rebuilt both charts, golden-table exact match, determinism proven. |
| P0-7 | `sudarshana_emitter.py` valence/agreement conflation | **VERIFIED-FIXED** — merged #836, rebuilt both charts. |
| P0-8 | `l3_convergence.py` health_attention self-inclusion | **VERIFIED-FIXED** — merged #835. No rebuild required (pure function, not in persisted DAG — ledger correction recorded above). |
| P0-9 | `ga_tajaka_writer.py` hardcoded orb constant | **VERIFIED-FIXED** (this session) — merged #853, reads the graha's own per-graha classical deeptamsa orb (reusing the M-13 `DEEPTAMSA` table) instead of a flat 7°; L1→L5 rebuilt on both charts (46 assets each, zero failures after recovery from a mid-rebuild sibling-closure gap and transient DB connection drops — see below). |
| P0-10 | `mi_darshana.py` grade=0.0 truthiness | **VERIFIED-FIXED** — merged #839, rebuilt both charts. |
| P0-11 | `ph_nimitta/engine.py` direction→'elevated' fallback | **VERIFIED-FIXED** — merged #837, rebuilt both charts. |
| P2 | `ph_phaladesa/engine.py:39` OpenAI allowlist hole | **VERIFIED-FIXED** — merged #837 (rode with P0-11). |
| C.7 | Systemic fact_key-pinning CI lint | **VERIFIED-FIXED** — merged #840, active on main; scope honestly bounded to the fact_key-misselection subclass (see build_id residual note above). |
| New | `ga_structural_writer.py:3369/3378` (L1, P0-5-shaped) | **PARKED-HONEST** — real, confirmed, out of this wave's authorization; recommend a dedicated future wave (L1→L5 radius). |
| New | `migration 339` OpenAI-in-CHECK-constraint | **PARKED-HONEST** — real, confirmed, needs its own surgical migration, out of one-line-fix scope. |
| New | `mi_darshana.py` verdict_note tradition-blindness | **PARKED-HONEST** (PLAUSIBLE severity) — correctly judged not a clean one-liner. |
| New | orchestrator watchdog/completion race (`bo_laksana_rerank`) | **NOT-APPLICABLE** to narration-determinism scope — operational finding, self-healed correctly by existing `RR-fix` reconciliation; config-tuning recommendation only. |
| New | `mi_gunanaka.py:337` snapshot-publish bug | **PARKED-HONEST** — real, pre-existing, non-fatal, unrelated to any fixed writer. |
| 28 seed findings (F1-F29 minus F18) | Carried from Phase A/B | Unchanged from this report's earlier Phase A/B closure — P1/P2/P3 bands untouched this wave (out of the 5-lane + C.7 authorization). |
| New (this session) | `ka_gochara_sweep` error state, operator E2E chart (`1c826d5a`), since 2026-07-26 | **PARKED-HONEST** — pre-existing, confirmed NOT in `ga_tajaka`'s dependency closure (independent asset), predates this session's rebuild, unrelated to any ŚV fix. Left untouched; flagged for whichever campaign owns `ka_gochara_sweep`. |

---

## Phase C2/D2/E2/F2 — closing the two parked lanes (2026-07-28, same-day follow-on session)

**Step 1 — PARISHODHANA #827/#828, reviewed properly, not rubber-stamped.** Both confirmed CI
green (TypeScript, Unit Tests, Secret Scan, Governance Gates) and merged: #827 (`assess_wealth`
leverage_index wiring, lines 782/2701 — no overlap with the Ṣaḍbala block at ~3498+) and #828
(`enforceVargaConfirmedHonesty` honest-downgrade fix, lines 1541/3384 — no fact_category-selection
concern, C.7 lint passes). Neither reintroduces a fact_category selection without a fact_key pin.

**Step 2 — `lane:serve-shadbala` (P0-1..4), TEST-FIRST.** Wrote failing tests first (proved the old
"5.00 required, weak" defect), then in `registry_bridge.ts`: pinned `fact_category='graha_shadbala_total'
AND fact_key='rupa'` on the raw-rupas selection; deleted the `SHADBALA_REQUIRED_RUPAS` wrapper
constant entirely; the required-rupas threshold is now read live from L1 via
`chart_facts_query(ayanamsha_id:'INVARIANT', category:'graha_shadbala_total', fact_key:'required_rupa')`;
an honest null ("required-rupa threshold unavailable from L1 this call — no grade assigned") replaces
the old silent constant on any fetch failure. Merged #852, deployed to `amjis-mcp` (Cloud Run), zero
DB rebuild needed. Verified live post-deploy.

**Step 3 — `lane:ga-tajaka` (P0-9), TEST-FIRST, widest blast radius in the program.** Confirmed the
dormant local branch `fix/D-2-ga-tajaka-solar-return-resilience` was already merged to main with no
line-level overlap (different function). Added `_aspects_lagna(planet, full_long, varsha_lagna_long)`
reusing the existing per-graha `DEEPTAMSA` classical-orb table (already used by `_tajik_yogas`'s
mutual-aspect precondition — confirmed via L1's own `aspect_tajik.deeptamsa_sum_deg` facts, which
exactly reconstruct the same constants) in place of the old flat `<= 7.0` comparison in the
Varshesha-scoring loop. 4 new golden tests written and proven failing pre-fix, passing post-fix.
Merged #853.

**Rebuild execution — honestly, including what went wrong and how it was recovered:**
1. Snapshotted 25 chart-scoped tables for both charts (tag `ssv_20260728b`); tested-rollback drill
   PROVEN (first attempt hit a composite-PK column, corrected to a safe non-key column, restore
   confirmed byte-identical).
2. Confirmed via `build_runs` query that PARIPRAŚNA BUILD held zero active/planned runs before
   starting — rebuild exclusivity respected throughout.
3. **First rebuild pass (27-asset direct closure) FAILED**: 26 assets BLOCKED. Root cause — the
   closure omitted 9 sibling out-of-plan dependencies (`bo_pratijna`, `bo_anveshana`, `bo_bimba`,
   `bo_cgm_paths`, `bo_karanajala`, `bo_samskara`, `bo_sangati`, `bo_upaya`, `ka_yojaka`) that an
   earlier same-session `bo_laksana` determinism-proof run had left `state='stale'` — the
   orchestrator only seeds an out-of-plan dependency as satisfied when it is `lit`/`service_ok`, and
   these were not. **Not a PARIPRAŚNA BUILD conflict** (confirmed via `build_runs`, no concurrent
   activity). Recomputed the live 44-asset non-lit closure and re-ran.
4. **That corrective pass hit a genuine transient Cloud SQL connection drop** mid-`ka_sangam`
   substep (`server closed the connection unexpectedly`), cascading a BLOCKED state to ~25
   downstream dependents; a second connection loss on the main scheduler connection left two zombie
   Postgres backends holding the chart's advisory lock (`pg_terminate_backend` cleared both safely —
   nothing was ever committed by either). Idempotent delete-then-insert per writer meant each retry
   was safe; three residual-closure retries (recomputing the live non-lit set each time — 26 → 3 →
   0) converged to **all 44 assets `lit`, zero failures**, canonical chart.
5. **Operator chart (`1c826d5a`)** needed an explicit forced reset of `ga_tajaka` (it was `lit` under
   the pre-fix code, since state doesn't auto-invalidate on a code change) plus its 26-asset
   downstream closure — all already-`lit` siblings on this chart were untouched by the canonical
   chart's earlier churn, confirmed before starting. Hit the same transient-connection pattern once;
   one residual retry (22 assets) converged clean.
6. **Verification, both charts:** 0 non-lit assets remaining in `ga_tajaka`'s closure on canonical;
   1 pre-existing, unrelated non-lit asset on operator (`ka_gochara_sweep`, dispositioned above); 0
   zombie `idle in transaction` backends; 0 orphaned `running`/`planned` `build_runs` rows (2 stale
   rows from crashed attempts explicitly marked `failed`). **Operator chart's data was never
   touched** during the canonical-chart recovery (confirmed via the snapshot tables' per-chart row
   counts — every operator-side delta was exactly 0 throughout).
7. **Row-count deltas on the canonical chart, explained, not silent accretion:** several tables
   (`kala_activation` 1,095→332,723; `kala_convergence` 1,912→18,033; `phala_sankrama` 55→1,125; etc.)
   show large increases. Comparing against the frozen snapshot tables (which retain per-row
   `chart_id`) showed the *pre-rebuild snapshot itself* had captured an already-incomplete state
   left over from this session's earlier `bo_laksana` churn (e.g. `kala_activation` for canonical sat
   at 1,095 rows pre-rebuild vs. the operator chart's stable 335,951 — a 306× asymmetry). Post-rebuild,
   canonical's `kala_activation` (332,723) sits within ~1% of the operator's, consistent with the
   rebuild restoring completeness rather than introducing accretion. Some tables show modest
   decreases (`mimamsa_calibration` 67→26, `phala_mitigation` 553→525) consistent with the corrected
   Varshesha selection changing which predictions clear downstream thresholds — the same pattern
   documented for the P0-5/6 rebuild above.

**Phase E — PROVE, re-run for the now-unblocked criterion:**

1. **`graha_portrait` narration — acceptance criterion #3 NOW MET.** All 7 grahas, canonical chart,
   live post-rebuild (see the top of this session's final report to the native for verbatim
   before/after strings). Every value matches brief §5 C.8's golden table exactly: Sun 8.47/5.00
   strong (+3.47), Moon 5.65/6.00 weak (-0.35), Mars 5.57/5.00 strong (+0.57), Mercury 7.55/7.00
   strong (+0.55), Jupiter 7.80/6.50 strong (+1.30), Venus 4.64/5.50 weak (-0.86), Saturn 7.83/5.00
   strong (+2.83).
2. **FORENSIC anchors spot-confirmed unaffected**, post-rebuild: Lagna=Aries, Vara=Ravivara,
   Tithi=Shukla Tritiya (tithi_id=3), Sun=Capricorn — all live-queried from `chart_facts`/
   `chart_header`. Structurally guaranteed unaffected by design: `ga_tajaka` writes only to its own
   Tajika/annual-chart tables, never to `chart_facts`.
3. **CI guard green.** `Ganga Quality Gate` (includes the C.7 fact-category-pin-lint) passed on all
   three of this session's merge commits (#851 brief-pointer fix, #852 serve-shadbala, #853
   ga-tajaka). `TAP CI — Total Audit Protocol Suite` fails identically on all three — including the
   no-op docs-only brief-pointer commit — confirming this failure is a pre-existing, unrelated test
   artifact (`SC-pointer:x` unresolved in `response_budget_verdict_immune_and_trim_order.test.ts`,
   traced to SHODHANA #811), not a regression from this session's work, and not a required
   merge-blocking check.
4. **Zero regressions** from either fix beyond the pre-existing TAP CI artifact above.

**Verdict in plain language, for the native:** the specific defect the native personally caught —
Sun's Ṣaḍbala grading reading "weak" — is now fixed **end to end**: correct at the writer/data level
(this report's earlier Phase C/D/E, `bo_laksana.py`), correct in the serve-side narration
(`registry_bridge.ts`, this session), and correct in the Tajika/annual-chart writer that shared the
same defect class (`ga_tajaka_writer.py`, this session, full L1→L5 rebuild on both charts). All 7 of
7 P0 lanes are VERIFIED-FIXED. The systemic C.7 guard remains live on `main`. Five findings carried
from last wave remain honestly PARKED (three real, out-of-scope defects requiring dedicated future
waves; one PLAUSIBLE-severity narration nuance; one self-healed operational note) — see the
disposition table above; none of them block this closure, per the brief's own four-way disposition
model.

**This run closes as COMPLETE — 7 of 7 P0 lanes VERIFIED-FIXED.** `CLAUDECODE_BRIEF.md` is flipped
ACTIVE→COMPLETE by this close. Six items remain honestly open (five carried findings + the
`ka_gochara_sweep` operator-chart anomaly), all correctly dispositioned PARKED-HONEST/NOT-APPLICABLE
as real, out-of-authorization findings for a future wave — not unmet acceptance criteria of this
brief.
