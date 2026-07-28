---
artifact: SUDDHA_VACA_BRIEF (Śuddha-Vāca — Purification of the Narration Layer)
canonical_id: SUDDHA_VACA_BRIEF
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-07-27
author: Cowork (Opus) planning session — native-commissioned
native_directive: >
  "I had taken up the narration part hesitatingly because I did not want anything subjective or
  LLM-based. Only when we agreed to do the narrations using a deterministic engine did I accept it.
  Now we found one place where it broke. I want to completely review ALL the assets, ALL the writers
  which involve narration, identify the gaps, fix those gaps, and rebuild those assets. The most
  important part: ensure that in the entire portal — the chart, the writers, the code — there are no
  defects, no bugs, and it is not contaminated."
source_documents:
  - NARRATION_DETERMINISM_AUDIT_v1_0.md (THE seed register — 19 CONFIRMED · 10 PLAUSIBLE ·
    2 REJECTED across 12 surfaces. READ IT FIRST AND IN FULL. Its findings are seeds, NOT the
    scope ceiling — Phase A must exceed it.)
  - 03_DOMAIN_REPORTS/REPORT_WHOLE_CHART_SYNTHESIS_AND_MCP_DIAGNOSTIC_v1_0.md §Tier 0/1
    (the originating Ṣaḍbala root-cause narrative)
  - 00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (§E roles, §J standing constraints)
  - 00_ARCHITECTURE/BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md (§C safety rails — inherited verbatim)
  - 00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (the FROZEN WriterBase contract)
  - 00_ARCHITECTURE/L1_GANITA_CLOSURE_v1_0.md (canonical row-count invariants)
  - 00_ARCHITECTURE/MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md (§N.5 authority-inversion trap —
    the doctrinal ancestor of this entire defect class)
mode: >
  FULLY AUTONOMOUS · ONE Claude Code session · Conductor (Opus) + Phase-A census/prober swarm
  (parallel Sonnet) + Phase-C fix builders (Sonnet base; Opus after 2 failed verify cycles) +
  ONE dedicated Opus Verifier that NEVER writes code + ONE Dvārapāla escalation agent that resolves
  every would-be human gate with a documented conservative decision · NO HUMAN GATES · in-repo git
  worktrees (.worktrees/suddhavaca-*) · PR + auto-merge only · wall-clock cap 10h ·
  PRIME RULE: truth over completion — PARKED-HONEST with evidence is a legitimate close.
authorization_grant: >
  Launching this brief authorizes, without further human confirmation: read-probes against live
  production for every narration surface; code edits to writers, emitters, services and serve-side
  assembly files; creation of golden/semantic tests and CI lint; PR creation and auto-merge to main
  on green CI; DESTRUCTIVE per-chart asset REBUILDS (delete-then-insert per §N.3) of every asset
  whose writer is fixed, PRECEDED IN EVERY CASE by a verified table snapshot and a tested rollback;
  and explicit redeploy of amjis-mcp. It does NOT authorize: orchestrator contract changes,
  modification of the sealed evaluator harness, schema migrations outside a fixed defect, or any
  Anthropic model in a production path.
---

# ŚUDDHA-VĀCA — Purification of the Narration Layer

**Śuddha-vāca** = *pure speech*. Every sentence this instrument utters must be a correct, reproducible
function of a verified fact — nothing added, nothing mis-selected, nothing invented.

---

## §0 — The mission in one paragraph

A deterministic, individually-verified asset shipped an **inverted verdict**: the Ṣaḍbala narration
graded the chart's single strongest planet "weak," on every graha, on every chart. The failure was
not in any *fact* — all three underlying rows were `two_pass_verified` and correct. It was in an
**untested derivation across facts**: a selector that picked a row by `fact_category` without pinning
`fact_key`, relabelled a unitless ratio as "rūpas," and subtracted a wrapper-local hardcoded constant
from it. A prior audit proved this is a **class, not an incident** — the same mis-selection is
reproduced inside the L2 root writer `bo_laksana`, where it is worse (no `ORDER BY` → the grade is
not even reproducible between two builds of the identical chart). This brief exists to sweep the
**entire** narration landscape for that class and its six siblings, fix each defect **at the layer
where it originates**, rebuild every affected asset so the corrected derivation propagates into
stored data, and prove the correction with live evidence — autonomously, end to end.

**The doctrine this establishes:** *deterministic* and *correct* are two different guarantees.
`two_pass_verified` covers the number; it has never covered the sentence that selects among numbers
and grades them. Śuddha-Vāca closes that gap permanently, in code and in CI.

---

## §1 — Prime directives (violating any one invalidates the run)

1. **Fix at origin, not at the surface.** If a defect originates in a writer, the writer is fixed
   and the asset is REBUILT — never patched downstream at serve time. A serve-side patch that masks
   a writer defect is itself a defect. Where the defect genuinely originates at serve time
   (read-time selection, e.g. `registry_bridge.ts`), fix there and redeploy.
2. **Narration may only RESTATE computed facts.** Per charter §J prime directive ("only computed
   facts — no narrative, opinion, or judgement in built data"), no fix may ADD interpretation to
   close a gap. If a sentence cannot be derived from a cited fact, the correct fix is to remove the
   claim or emit an honest null — never to invent a plausible one.
3. **§N.5 L1 authority is absolute.** Narration REFERENCES `fact_id` and INHERITS L1's value. A
   wrapper-local constant table that shadows an L1 fact (`SHADBALA_REQUIRED_RUPAS`, the hardcoded
   `1.0` normaliser, the literal `3` robustness) is a defect by construction, even when its current
   values happen to be right — because it can drift.
4. **No fabricated rows, ever (B.10 / §N.4).** Floors are aspirational; `target_floor` = achieved
   count after build. A rebuild that manufactures rows to hit a number is a failed rebuild.
5. **Reproducibility is part of correctness.** Any selection feeding narration must be
   deterministic: pinned key AND a total `ORDER BY`. "Whichever row the DB returned last" is a
   defect even when the value is right.
6. **Truth over completion.** Every thread ends DISPOSITIONED WITH EVIDENCE. `PARKED-HONEST` is a
   legitimate close. There is no "passed with caveats."

---

## §2 — Phase 0 — RECONCILE & ARM (Conductor, serial, before any other work)

**0.1 — Orientation.** Read CLAUDE.md §C chain in order, `CURRENT_STATE_v1_0.md §2`, this brief,
and `NARRATION_DETERMINISM_AUDIT_v1_0.md` in full.

**0.2 — PARISHODHANA collision reconciliation (BLOCKING).** A campaign `PARISHODHANA_BRIEF_v1_0.md`
is at `READY-FOR-EXECUTION`; the working tree sits on `parishodhana/phase-a-reconciliation` with
uncommitted changes and many `parishodhana/*` branches exist. Before touching anything the Conductor
must determine, from branches / open PRs / `PROGRAM_LEDGER_AND_ELEVATION_ROADMAP_v1_0.md` /
`PARISHODHANA_RECONCILIATION_v1_0.md`, whether that arc is mid-flight, complete, or unstarted, and
the **Dvārapāla** issues a written decision from exactly these options:
  - **DISJOINT-PARALLEL** — Śuddha-Vāca touches only narration surfaces PARISHODHANA does not; run
    concurrently on separate branches off a common base. (Requires an explicit file-level
    disjointness proof, published in the report.)
  - **QUEUE-BEHIND** — PARISHODHANA is mid-flight on overlapping files; Śuddha-Vāca completes
    Phases A–B (read-only census + ledger) now and defers Phases C–E until its branches land.
  - **PROCEED-CLEAR** — the arc is complete/unstarted and no overlap exists.
  Uncommitted working-tree changes are **preserved** (stash with a named ref, recorded in the
  report) — never discarded. Record the decision + evidence in the report before proceeding.

**0.3 — Session open.** Emit the SESSION_OPEN handshake per `SESSION_OPEN_TEMPLATE_v1_0.md`.
`must_not_touch` MUST be non-empty (an empty one fails the handshake). Validate with
`schema_validator.py` before the first substantive tool call. Propose the Cowork thread name per
`CONVERSATION_NAMING_CONVENTION_v1_0.md §4`.

**0.4 — Safety baseline (BLOCKING before any Phase D work).**
  - Record per-table row counts for every table any candidate rebuild would touch.
  - Capture a restorable snapshot of each such table, scoped to the charts under rebuild.
  - **Test the rollback once** on a single non-critical table and prove restore works. An untested
    rollback does not count as a rollback.
  - Record the canonical invariants to re-assert post-rebuild: `chart_facts=27,554`,
    `chart_dashas=536,471`, `chart_divisionals=21,635`, Gaṇita header total `585,710`, and
    FORENSIC 7/7 (Sun=Capricorn · Moon=Pūrva Bhādrapadā · Lagna=Aries all 5 ayanāṃśas ·
    Tithi=Śukla Tṛtīyā · Vāra=Ravivāra · Yoga=Śiva · Karaṇa=Garaja).

---

## §3 — Phase A — CENSUS (exhaustive landscape audit; read-only; parallel swarm)

The prior audit covered 12 surfaces / 21 files. **That is the floor, not the ceiling.** The native's
requirement is that the ENTIRE landscape be audited.

**A.1 — Build the census.** Enumerate EVERY narration-bearing surface in the repo. Sweep at minimum:
  - `platform/python-sidecar/pipeline/orchestrator/writers/*.py` — **all** layers (`bg_ ga_ bo_ ka_
    ph_ mi_`), not only the 14 previously flagged.
  - `platform/python-sidecar/bodha_writers/**` — **including the `*_emitter` modules**
    (`arudha_emitter`, `special_lagna_emitter`, `vargottama_dhana_emitter`, and every sibling).
    *These are UNAUDITED residual #1 and are the actual builders of `signal_summary_text` /
    `signal_headline_text` — treat as high-prior-probability defect territory.*
  - `platform/python-sidecar/ga_writers/**`, `services/**/engine.py` — **including
    `services/ph_nimitta/engine.py`** (UNAUDITED residual #2: falsifier text, `karmic_note`,
    `source_citation` composition), `brahma/**`, `brahmagyan/**`, `muhurat/**`, `panchang_engine/**`,
    `routers/**`.
  - `platform-mcp/src/**` — tools, resources, retrieval, lib (response_budget, envelope).
  - `platform/src/lib/**` — retrieval (envelope, ranking, grounding), pipeline, icr, consume.
    *Distinguish rigorously: the LLM chat/prompt-template layer is legitimately generative and is
    OUT of scope; any surface that emits a grade/verdict/summary presented as derived-from-fact
    is IN scope.*

  Detection signature (union, case-insensitive): `narrat|prose|summary_text|headline|human_readable|
  citation_human|verbaliz|_label|grade|describe_`, plus every f-string / template literal that
  interpolates a computed value into a sentence, plus every threshold table that maps a number to a
  word (`weak|strong|afflicted|benefic|malefic|promised|denied|obstructed|clear|auspicious`).

  Output: **`NARRATION_SURFACE_CENSUS_v1_0.md`** — one row per surface: path · layer · emits-prose?
  · deterministic? (with evidence) · audited-before? · assigned prober · disposition.
  **Gate A1: the census must be exhaustive by construction** — publish the total count of files
  matching the signature and prove that count equals the number classified. No sampling.

**A.2 — Audit every surface against the 7 defect classes.** One prober per surface (parallel),
each hunting:
  - **D1 MIS-SELECTION** — selects a fact by category/label without pinning key/unit/ayanāṃśa, or
    without a total `ORDER BY`. *(The Ṣaḍbala class. Highest prior.)*
  - **D2 MISLABEL** — value printed with the wrong unit, level, or meaning.
  - **D3 HARDCODED-DRIFT** — grades against a wrapper-local constant instead of the L1 fact.
  - **D4 GRADE-INVERSION** — threshold/sign/operand logic that can flip a verdict.
  - **D5 CONTAMINATION** — routes (or can route) to an LLM; bypasses/mis-implements
    `validate_narration_model`; or asserts a verification that was never performed.
  - **D6 COVERAGE-GAP** — branch silently emits empty/default/placeholder text; fetched data
    dropped before narration; a flag hardcoded to a clean-looking literal with no detector behind it.
  - **D7 PARAPHRASE-DIVERGENCE** — prose restates a value in a way that can drift from it.

  Every finding is then **adversarially verified by a second agent instructed to REFUTE it**,
  re-opening the source and, where a live tool can settle it, calling MARSYS-JIS against
  `482012f1-710e-4a25-994a-93821f5871aa`. Default to REJECTED when not concretely reproducible.
  Only `CONFIRMED` / `PLAUSIBLE` enter the ledger. (This two-pass discipline caught a hallucinated
  finding in the seed audit — it is not optional.)

**A.3 — Seed reconciliation.** Carry the 29 seed findings forward: each must be re-verified as
still-open (some may already be fixed by in-flight work). Do not re-litigate settled ones; do
record their current state.

---

## §4 — Phase B — TRIAGE & FIX LEDGER

Dedupe and rank all findings. For each, determine and record:
  - **Origin layer** — writer / emitter / service-engine / serve-side / multiple.
  - **Fix layer** — per §1.1 (origin, never surface).
  - **Rebuild blast radius** — which assets must be rebuilt for the fix to reach stored data, in
    dependency order. `bo_laksana` is the **L2 root**: fixing it cascades through
    `bo_bimba / bo_karanajala / bo_sangati / bo_samvada / bo_samskara → bo_upaya → bo_pramana_mapa`
    and the gestalt/CGM/CDLM writers, and because L3 Kāla / L4 Phala / L5 Mīmāṃsā consume Bodha,
    the honest radius is **L2 → L5**. Plan it as such; do not under-scope.
  - **Lane assignment** — cluster by file/subsystem so worktrees do not collide.

Output: **`SUDDHA_VACA_FIX_LEDGER_v1_0.md`**. Priority bands:
  - **P0 — verdict-inverting.** `registry_bridge.ts:3498/3502/3508` and `bo_laksana.py:831/848`.
  - **P1 — false assurances & dropped warnings.** `bo_pramana_mapa.py:224/228/262/278` (flags that
    read "0 leaks / verified clean" with no detector), `ph_phaladesa.py:121` (contradiction warning
    is dead code), `ka_bhavishya_lekha.py:232`, `kala_temporal.ts:377/380`.
  - **P2 — mislabel / drift / paraphrase.** Includes `services/ph_phaladesa/engine.py:39` — narrow
    `PERMITTED_NARRATION_MODELS` to match its own docstring (it currently permits `gpt-4o` /
    `gpt-4-turbo` while charter §J bans Anthropic and the docstring says Gemini/DeepSeek only).
    **Do this in the P0 wave** — it is one line and it closes a standing contamination hole.
  - **P3 — newly discovered** from the A.1 expansion (emitters, ph_nimitta engine, and beyond),
    banded by the same severity rule.

---

## §5 — Phase C — FIX (parallel, worktree-isolated, TEST-FIRST)

One lane per cluster, in `.worktrees/suddhavaca-<lane>`. Per lane, in this exact order:

1. **Write the failing test FIRST.** Encode the CORRECT semantics as a golden/semantic assertion.
   **Prove it fails against current code** and record that failure output. A fix without a
   previously-failing test does not count as fixed.
2. **Fix at the origin layer.**
3. **Prove the test passes**; run the surrounding suite (`vitest run` in `platform-mcp` /
   `platform`; `pytest` for the sidecar), `tsc --noEmit`, `eslint`.
4. **Opus Verifier** adversarially reviews the diff — it NEVER writes code. It checks: fix is at
   origin; no interpretation added (§1.2); no L1 value re-derived instead of referenced (§N.5); the
   test genuinely fails before and passes after; no FROZEN-contract drift (§N.2 — writers stay
   `@register` `WriterBase` subclasses, run on `ctx.db_conn`, never commit/close it, never write
   `asset_throughput`).
5. **PR + auto-merge on green CI.** Never push directly to main.
6. **Bounded retries: MAX_FIX_ATTEMPTS = 5**, then `PARKED-HONEST` with a written spec of what a
   correct fix requires and why it was not reached.

**C.7 — The systemic guard (mandatory, ships with P0).** Add a CI lint that FAILS the build on any
selection over a `fact_category` (`.find(`, `[0]`, `filter(...)` in TS; `SELECT ... WHERE
fact_category = ...` in Python) that does not also pin `fact_key` **and** carry a total `ORDER BY`
where a set is reduced to one row. This is the permanent fix for the entire D1 class. Include an
allowlist file with written justification for any legitimate exception.

**C.8 — The golden Ṣaḍbala fixture.** Derive the expected table **from L1 `rupa` and `required_rupa`
facts directly** (never hardcode it — that would repeat D3). It must cross-check against this
independently-confirmed table for the canonical chart:

| Graha | ratio | required (rūpa) | actual (rūpa) | surplus | correct grade |
|---|---|---|---|---|---|
| Sun | 1.694 | 5.0 | **8.47** | +3.47 | **strong** |
| Saturn | 1.566 | 5.0 | **7.83** | +2.83 | **strong** |
| Jupiter | 1.200 | 6.5 | **7.80** | +1.30 | **strong** |
| Mercury | 1.079 | 7.0 | **7.55** | +0.55 | **strong** |
| Mars | 1.114 | 5.0 | **5.57** | +0.57 | **strong** *(confirm required from L1)* |
| Moon | 0.942 | 6.0 | **5.65** | −0.35 | weak |
| Venus | 0.844 | 5.5 | **4.64** | −0.86 | weak |

If any L1-derived value contradicts this table, **L1 wins** (§N.5) and the divergence is reported as
a finding — do not force agreement.

---

## §6 — Phase D — REBUILD (dependency-ordered, snapshot-guarded)

For every asset whose writer was fixed:

1. **Snapshot** the target tables (Phase 0.4 rollback proven).
2. **Rebuild in dependency order** via the FROZEN orchestrator — never by hand-editing rows, never
   by a bulk `migrate.ts`, never by deploy.yml-auto (§N.4 surgical-migrations-only).
   Order: any `ga_*` fix first → `bo_laksana` → L2 cascade → L3 `ka_*` → L4 `ph_*` → L5 `mi_*`.
3. **Charts:** canonical native `482012f1-710e-4a25-994a-93821f5871aa` **and** the operator E2E
   chart Abhinandan Mohanty `1c826d5a` (proves the fix is not native-specific).
4. **§N.3 idempotency:** per-chart delete-then-insert scoped to `(chart_id × natural key)`.
   Rebuild REPLACES; it never accretes. Verify no duplicate accretion post-run.
5. **Post-rebuild assertions (all BLOCKING):** FORENSIC 7/7 PASS · canonical row-count invariants
   hold or every delta is explained in writing · `count_sql` on `asset_registry` still correct per
   asset (the L1 cockpit trap) · `target_floor` reset to achieved counts, nothing fabricated.
6. **Any failure → restore from snapshot, mark the lane PARKED-HONEST, continue other lanes.**
   A failed rebuild must never leave the DB in a half-written state.

---

## §7 — Phase E — PROVE (regression battery; evidence, not assertion)

1. **Re-run the full Phase-A census swarm** against the rebuilt data. Expect **zero CONFIRMED
   findings of any fixed class**. Anything surviving is reported, not explained away.
2. **Live grade proof.** Call `graha_portrait` (and `ganita_strength_get` / `judgment_query`) for
   all 7 grahas on the canonical chart. The narration must now match §5 C.8 — specifically **Sun
   must read strong (~8.47 rūpas), not "weak (deficit)"**. Capture verbatim before/after strings.
3. **Determinism proof (this is the one that proves the `bo_laksana` fix).** Build `bo_laksana`
   **twice** from clean state on the same chart and byte-compare `shadbala_norm`, salience, and
   `signature_tier` across both runs. **They must be identical.** A passing value with a
   non-reproducible derivation is still a failure.
4. **Contamination proof.** Re-assert no LLM in any narration path; `validate_narration_model`
   allowlist matches its documented policy; no Anthropic model in any production path (§J).
5. **Zero regressions.** Full existing suites green — `platform-mcp` and `platform` vitest, sidecar
   pytest, `tsc --noEmit`, eslint, plus `drift_detector.py` and `schema_validator.py` (manifest mode).
6. **The new CI lint (C.7) is active and passing** on main.

---

## §8 — Phase F — CLOSE (governance; atomic)

1. **`SUDDHA_VACA_REPORT_v1_0.md`** — consolidated, with a **disposition table covering every
   finding** (seed + newly discovered). Four dispositions only:
   `VERIFIED-FIXED` (with evidence) · `PARKED-HONEST` (with spec + reason) · `REJECTED`
   (false positive, with refutation) · `NOT-APPLICABLE` (with justification).
   No "passed with caveats". Include the Phase-E before/after narration strings verbatim.
2. **Doctrine.** Add **CLAUDE.md §N.7 — Narration Fidelity Principle**, drawn from what the code
   now enforces (not a fresh idea), stating: narration is a deterministic restatement of L1-
   referenced facts; every fact selection pins `fact_key` and carries a total order; no wrapper-
   local constant may shadow an L1 fact; a verification flag must have a detector behind it or be
   null; and *verified fact ≠ verified prose* — semantic grade tests are required at every narration
   layer. Bump CLAUDE.md version + changelog; keep frontmatter and footer versions in sync.
3. **Registry hygiene.** Update `CAPABILITY_MANIFEST.json` / `CANONICAL_ARTIFACTS_v1_0.md` for new
   artifacts; registries must not disagree (B.8 / GA.1).
4. **Session close.** Emit the SESSION_CLOSE checklist per template; validate with
   `schema_validator.py`; only then append the atomic `SESSION_LOG.md` entry (open + body + close).
   Update `CURRENT_STATE_v1_0.md §2`. Discharge the red-team obligation if `red_team_due`.
5. **Flip the root `CLAUDECODE_BRIEF.md` frontmatter `status` to `COMPLETE`** with the disposition
   summary, per CLAUDE.md §C item 0.
6. **Cleanup.** Remove `.worktrees/suddhavaca-*`; restore any Phase-0.2 stash; leave the tree clean.

---

## §9 — Hard boundaries (breach = halt that lane, Dvārapāla dispositions, run continues)

- **The orchestrator is FROZEN** (§N.2). Writers conform; the orchestrator is never extended. If a
  fix appears to require a contract change → **STOP that lane**, Dvārapāla records
  `CONTRACT-CHANGE-REQUIRED` + `PARKED-HONEST` with a written spec for the native. Other lanes continue.
- **The sealed evaluator harness is never modified.**
- **No Anthropic model in any production path** (§J). Dev-loop agents are unconstrained.
- **No schema migration** beyond what a confirmed defect strictly requires; surgical only.
- **`kala_gochara_windows` and `build_substep_progress` remain untouchable** unless a CONFIRMED
  finding traces *into* them — in which case snapshot first and record the exception explicitly.
- **No JH-parity oracle** anywhere — verification is internal consistency + classical re-derivation
  + FORENSIC grounding.
- **main via PR + auto-merge only**, CI green. `amjis-mcp` deploys explicitly.
- **Budgets:** inherit `BUILD_GUARANTOR_AUTONOMOUS_MODE` §C ceilings; wall-clock cap 10h;
  MAX_FIX_ATTEMPTS=5 → park.

---

## §10 — Acceptance criteria (the run is COMPLETE only when all hold)

1. Census is exhaustive: signature-matching file count published and fully classified — including
   `bodha_writers/*_emitter` and `services/ph_nimitta/engine.py` (the two named residuals).
2. All 29 seed findings dispositioned with evidence; all newly discovered findings dispositioned.
3. `graha_portrait` narration matches the §5 C.8 golden table for all 7 grahas on the canonical
   chart — **Sun reads strong, not weak** — with verbatim before/after captured.
4. Double-build of `bo_laksana` produces byte-identical strength/salience/tier outputs.
5. FORENSIC 7/7 PASS post-rebuild; canonical row-count invariants hold or every delta is explained.
6. Zero regressions across all existing suites; `drift_detector` + `schema_validator` green.
7. The C.7 `fact_key`-pinning lint is merged, active, and passing on main.
8. `validate_narration_model` allowlist matches its documented policy; no LLM in any narration path.
9. `SUDDHA_VACA_REPORT_v1_0.md` exists with a complete four-disposition table.
10. Governance closed: SESSION_LOG appended atomically, CURRENT_STATE updated, CLAUDE.md §N.7 added,
    root `CLAUDECODE_BRIEF.md` flipped to COMPLETE.

---

## §11 — What the native wakes to

`SUDDHA_VACA_REPORT_v1_0.md`, opening with a one-paragraph verdict in plain language answering the
question he actually asked: **is the narration layer clean, deterministic, and uncontaminated — yes
or no, and where is it not.** Then the disposition table. Then the before/after narration strings
that prove the grades flipped. Nothing that requires him to reconstruct the reasoning himself.

*End of SUDDHA_VACA_BRIEF v1.0.*
