---
artifact: SAMAPTI_IMPLEMENTATION_BRIEF (Samāpti — Close Every Open Item)
canonical_id: SAMAPTI_BRIEF
version: 2.0
status: READY-FOR-EXECUTION
created: 2026-07-30
supersedes: SAMAPTI_IMPLEMENTATION_BRIEF_v1_0.md (2026-07-29) — superseded in full; see §0.2
author: Claude Code (Opus) consolidation session — native-commissioned
consolidates:
  - SAMAPTI_IMPLEMENTATION_BRIEF_v1_0.md (Tracks 0–5, retained where still live)
  - The native's 2026-07-30 exhaustive open-item enumeration (PB-2/PB-3/PB-4, SATYA-DĪPA,
    PARKED-FINDINGS-3ITEM, cross-cutting, campaign-level, and working-tree items)
source_documents_VERIFIED_ON_MAIN:
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_REPORT_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_FIX_LEDGER_v1_0.md (v1.2)
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/PARKED_FINDINGS_CLOSE_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/satya_dipa/SATYA_DIPA_REPORT_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_build/REPORT_PB-3.md
  - 00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE.md
  - 00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-4.md
  - 00_ARCHITECTURE/briefs/pariprashna_build/FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md
  - 00_ARCHITECTURE/briefs/pariprashna_build/PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md
  - 00_ARCHITECTURE/narration_audit/NARRATION_DETERMINISM_AUDIT_v1_0.md (working tree only — see T0)
  - CLAUDE.md §N.7 (Narration Fidelity) + §N.8 (Earned-Signal Principle)
registry_correction: >
  v1.0 named `OPEN_ITEMS_REGISTER_v1_0.md` as "the item list this brief operationalizes" and made
  "every register item (Groups 1–5)" its first acceptance criterion. That document — on disk AND on
  origin/main — is a 2026-06-17 L1-closure register with Groups A0/A/B/C/D/E and contains ZERO
  SV-/FC-/INF-/EP- items. The Groups 1–5 taxonomy existed only inside v1.0 itself, so v1.0's own
  primary acceptance criterion was unverifiable. This version carries its register INTERNALLY
  (Appendix A) and treats the real OPEN_ITEMS_REGISTER as a separate, still-open inheritance (T9.6).
mode: >
  FULLY AUTONOMOUS · one Claude Code session at a time · Conductor (Opus) + parallel Sonnet builders
  in ISOLATED worktrees + ONE dedicated Opus Verifier that NEVER writes code + ONE Dvārapāla that
  resolves every would-be human gate with a documented conservative decision · NO HUMAN GATES except
  the two named in §2 · build in parallel, INTEGRATE + DEPLOY STRICTLY SERIALLY under the merge lock ·
  PRIME RULE: truth over completion — PARKED-HONEST with evidence is a legitimate close.
authorization_grant: >
  Authorizes, without further human confirmation: read-probes against production; code edits within
  each track's named files; creation of golden/live tests + CI wiring; snapshot-guarded destructive
  asset rebuilds where a fixed writer requires them; PR creation + auto-merge on green CI; and
  production deploys via merge (each verified-healthy-then-reported, hard-stop if unhealthy). Does
  NOT authorize: further orchestrator-contract changes (SATYA-DĪPA's freeze exception is spent and
  closed), modifying the sealed evaluator harness, any Anthropic model in a production path, schema
  migrations beyond what a fixed defect strictly requires, routing around a denied Write tool with a
  heredoc/other tool, or executing Track 8 (PB-4) — which carries its own explicit decision gate.
---

# SAMĀPTI v2.0 — Close Every Open Item

*Samāpti* = the completion. This brief finishes the ŚUDDHA-VĀCA · SATYA-DĪPA · PARIPRAŚNA ·
PARKED-FINDINGS arc. v1.0 was correct in doctrine and structure; it was written against a snapshot
that had already moved, it under-scoped three of its own tracks by roughly an order of magnitude, and
it omitted 22 items the native has since enumerated. This version corrects all three classes.

---

## §0 — Read first

### §0.1 — The doctrine (governs every track)

Four principles, earned across the arc, bind all work here. The first three are inherited from v1.0
unchanged. The fourth is new, and is the direct lesson of v1.0 itself.

1. **Verified fact ≠ verified prose (ŚUDDHA-VĀCA).** `two_pass_verified` guarantees a NUMBER; it
   never covered the SENTENCE that selects among numbers and grades them. Fix defects at the layer
   where the derivation happens.
2. **Earned-Signal Principle (SATYA-DĪPA, `CLAUDE.md §N.8`).** Every status/grade/PASS must be
   computed by a detector that measures the claim it asserts. A signal without such a detector is
   **null, not green.**
3. **Live proof, not fixtures (PARIPRAŚNA).** A green that cannot go red is not acceptance. Every
   acceptance criterion is verified against the REAL deployed route / prod DB on a real chart.
4. **Verify state before you fix it (SAMĀPTI, new).** v1.0's P0 track — the one carrying the
   native's originating complaint — specified building a fix that was already merged, deployed, and
   live-correct. A brief is a claim about the world and decays like any other claim. **Every track
   below opens with a VERIFY step whose possible outcome is "already closed — record evidence and
   skip."** Re-fixing closed work is not conservatism; it is a merge-conflict and a rebuild-blast-
   radius risk taken for nothing.

**Fix at origin, then rebuild.** A writer defect is fixed in the writer and the asset is rebuilt —
never masked by a downstream serve-time patch. Where the defect genuinely originates at serve time
(read-time selection, e.g. `registry_bridge.ts`), fix there and redeploy.

### §0.2 — What changed since v1.0 was written (evidence-backed corrections)

v1.0 was authored 2026-07-29. Between its authoring and this consolidation, five of its items closed.
**All five were verified against `origin/main` and live production during this consolidation session,
not assumed.** A session executing v1.0 verbatim would spend its P0 track diagnosing a working deploy
and re-fixing merged code.

| v1.0 item | v1.0 said | Verified reality (2026-07-30) | Evidence |
|---|---|---|---|
| **SV-1** serve-shadbala | "Fix the Ṣaḍbala narration in `registry_bridge.ts`… Deploy `amjis-mcp`." | **CLOSED and LIVE-VISIBLE.** | Merged `6030073a` (#852). Live `graha_portrait` call, canonical chart, this session, returns verbatim: *"Shadbala: 8.47 rupas vs 5.00 required — grade: strong (surplus) (+3.47 rupas)"* — correct `fact_key='rupa'` selection, L1-sourced required-minimum, correct surplus arithmetic, correct unit. |
| **SV-2** ga-tajaka | "read the aspect orb from the graha's own L1-computed fact… Rebuild the affected L1→L5 assets." | **CLOSED.** Per-graha deeptamsa orb landed; L1→L5 rebuilt on both charts (46 assets each). | Merged `cf330fca` (#853); `SUDDHA_VACA_REPORT` disposition row P0-9 = VERIFIED-FIXED. |
| **INF-2** MCP deploy broken | "The 'Build & Deploy MCP' job fails its post-deploy smoke test on unmodified `main`… Diagnose and fix." | **CLOSED.** Root causes were a bash single-quote error in a `${VAR:?}` expansion and a missing `mcp-canary-key` Secret Manager IAM binding. Both fixed. | Last three `Deploy to Cloud Run` runs on `main` = **success** (`30481012731`, `30484976742`, `30485451839`, all 2026-07-29 18:40–19:44Z), after two failures at 18:24/18:35. **Correction (SAMĀPTI/B-DOCS-GOVERNANCE, 2026-07-30, DVA Rulings 17/25/28):** this row originally cited "152 tools serving incl. 8 new `kala_*`" — that figure came from `mcp_server_info.tool_count`, which Ruling 25 found is sourced from a *different, decoupled* population (`mcp_catalog_version.ts`'s generated registry-size metric) than what the server actually serves, not a live catalog measurement. A direct `tools/list` call against the deployed MCP server, independently re-derived by VER from two directions (source-registered-minus-gated arithmetic AND a live call), measures **124** — confirmed authoritative (Ruling 28's "CONFIRMED (not a new ruling)" note). Do not cite 152 going forward; cite the live `tools/list` count at time of use, with `mcp_server_info.tool_count` only once lane `B-MCP-CATALOG-GAP` (Ruling 25) has re-sourced it to equal the live count. |
| **SV-3** second L1 `fact_key` mis-selection | listed as open work | **CLOSED.** `ga_structural_writer.py:3369/:3378` pinned, plus a fleet-wide audit of all 50 enum-shaped CHECK constraints and a new scheduled `fresh_chart_smoke.yml`. | Merged `fdd6912c` (#864). |
| **SV-4** migration-339 OpenAI allowlist | listed as open work | **CLOSED** via surgical migration. | Merged `81509e07` (#862). |

**Consequence:** v1.0's Track 1 — its stated P0, "highest user value" — is **fully closed**. §9
criterion 2 ("`graha_portrait` shows Sun STRONG on the deployed portal") is **already met**. The
originating complaint is user-visible today. What remains of that track is *evidence capture and a
7-graha sweep*, not a build. It is demoted accordingly (T2).

### §0.3 — Where v1.0 under-scoped

Three tracks compressed large enumerated finding-sets into single line items. Corrected in T3/T4/T5.

| v1.0 item | v1.0 scope | Actual scope in the source ledger |
|---|---|---|
| **SV-8** "reconcile the P1/P2/P3 bands" | one line item | `SUDDHA_VACA_FIX_LEDGER` v1.2: **6 P1** findings, **~39 P2** (8 seed + 24 new CONFIRMED + 7 new PLAUSIBLE), **~5 P3**. ≈**50 discrete findings**, several architecturally significant (see T3.3). |
| **SV-6 / SV-7** | *undefined* — v1.0 says "pull exact specifics from `SUDDHA_VACA_REPORT`'s disposition table" | A brief cannot disposition items it cannot name. Resolved by enumeration in T3.4. |
| **FC-4** detector-less sweep | "codebase-wide" | `SATYA_DIPA_REPORT` §5 names the five files scoped-but-not-swept: `runner.py`, `staleness.py`, `dag_edge_guard.py`, `kala_derivation_completeness_guard.py`, `service_probes.py`. Without them the sweep has no starting set and no completion test. |
| **Track 3 / PB** | "Execute `BRIEF_PB-3.1` **verbatim** — it is the spec for this track", then lists PB-1..PB-8 | Internally contradictory. PB-3.1 contains **only G1–G5**. `REPORT_PB-3` explicitly records PB-6 (dock card) and the governance items as **"not carried into PB-3.1's scope."** Separated honestly in T5. |
| **EP-1** falsely-`lit` re-audit | "Start from the enumerated falsely-`lit` population in `SATYA_DIPA_REPORT`" | That population is **empirically ZERO** (report §"Plain-language answer" and §4: *"Phase D … has no work to do"*). Track 4 as written is a no-op. The real residue is different and is now T6. |
| **Track 0** worktree hygiene | "prune the ~20 stale/`prunable` worktrees" | `git worktree list` = **35** entries; `prunable` count = **0**. Nothing would be pruned. The real job is retiring **11 named PB worktrees** + their remote branches (T1.2). |
| **§9 criterion 6** | "`drift_detector` + `schema_validator` green" | **Unachievable as stated.** 216 findings / 43–45 violations are long-standing, explicitly tolerated exit-code-3 residuals per `ONGOING_HYGIENE_POLICIES` §F. Restated in §10. |

### §0.4 — One structural finding v1.0 (and the native's list) both missed

v1.0's migration rail reads: *"read `main`'s ACTUAL highest migration number and take the next."*
That rail **still collides**, because there are **two migration directories on `main`**, each carrying
an overlapping 4xx sequence:

- `platform/migrations/` — 283 files, highest **474** (`474_asset_throughput_incomplete_state.sql`)
- `platform/supabase/migrations/` — 235 files, highest **473** (`473_bg_sky_calendar.sql`)

This is the structural root cause of "467 was claimed three times." A session reading only one
directory computes a free number that is already taken in the other. Corrected rail in §1; permanent
fix in T1.5.

---

## §1 — Standing rails (binding on all tracks)

- **T0 (preserve) precedes T1 (isolate), which precedes everything else.** Retiring the shared
  checkout as a build surface *before* committing the uncommitted work inside it would destroy that
  work. This ordering is not negotiable.
- **Every track opens with a VERIFY step** whose legitimate outcome is "already closed — record
  evidence, skip the build." Per §0.1 principle 4.
- **Integrate + deploy STRICTLY SERIALLY under the merge lock.** Only one track integrates to `main`
  at a time. Before any merge: confirm the other tracks AND other live campaigns (PARISHODHANA,
  ṢAḌ-DARŚANA) are quiesced — *no open/auto-merging PR* **AND** *no live session editing the tree*;
  "no open PR" alone is insufficient — and rebase onto the latest `origin/main` immediately before
  merging.
- **Every merge to `main` AUTO-DEPLOYS to Cloud Run.** Treat each merge as a production deploy:
  merge in a deliberate order, verify the new revision serves healthy (route responds, no error
  spike, migration applied), report it, and HARD-STOP the track if unhealthy — do not stack the next
  merge on top.
- **Migration numbering (CORRECTED):** take `max(highest in platform/migrations/, highest in
  platform/supabase/migrations/) + 1`, read from `origin/main` at the moment of authoring, and
  **re-check immediately before merge**. Write the chosen number into the file's internal header
  comment *and* keep them in sync through any renumber (the 474/467 defect, T9.5).
- **Snapshot before every destructive write**, with a rollback TESTED once before use (the mechanism
  ŚUDDHA-VĀCA built). Any failed rebuild restores from snapshot and PARKS the item — never leaves the
  DB half-written.
- **The orchestrator contract is FROZEN.** SATYA-DĪPA's one authorized freeze exception is spent. Any
  new need to change it → STOP that lane, Dvārapāla records `CONTRACT-CHANGE-REQUIRED` +
  PARKED-HONEST, other tracks continue.
- **No Anthropic model in any production path. No heredoc/other-tool bypass of a denied Write** — if
  Write is denied, hand the content over or use the sanctioned commit path.
- **PR + auto-merge only, CI green.** The narration `fact_key` CI guard, `fresh_chart_smoke.yml`, and
  (once built) the detector-less-gate lint must stay green. **Known-red harness:** boot-time pointer
  validation SC-17/18/19 currently fails on unmodified `main` — see T7; do not mistake it for a
  regression this campaign introduced, and do not let it mask one either.
- **`drift_detector` / `schema_validator`:** the standard is **no NEW violation attributable to this
  campaign**, measured against a baseline captured at T0. Not "green" (§0.3).
- **Local Postgres proxy:** `127.0.0.1:5433` is a recurring failure surface — reproduced ECONNREFUSED
  during this consolidation. Any lane needing live DB reads restarts the Cloud SQL Auth Proxy first
  or falls back to `psql` directly; do not report a probe as "no data" when it was a dead proxy (T1.6).

---

## §2 — Human gates: NONE (superseded 2026-07-30 by native directive)

> **AMENDMENT (native directive, 2026-07-30).** This section originally reserved two decisions for
> the native. The native has since directed that SAMĀPTI execute as a **fully autonomous tick swarm
> with zero human gates**, with a dedicated **Dvārapāla** agent standing in for the native and
> deciding on best judgment. Both items below are therefore **Dvārapāla rulings**, not human gates.
> See `00_ARCHITECTURE/CONDUCTOR/SAMAPTI_CONDUCTOR_PROMPT_v1_0.md` §4.

1. **Track 8 (PB-4 PŪRṆATĀ)** — an entire authored-but-unstarted feature wave, not a gap-closure.
   Now **Dvārapāla ruling R-0/PB-4**, decided at the gate on evidence: PB-4 executes if (a) the
   prediction loop is proven live end-to-end (T5 acceptance A1–A6 all CONFIRMED) and (b) no
   higher-priority lane is starved of swarm capacity; otherwise it is DEFERRED with the reason
   recorded and its brief left READY-FOR-EXECUTION. Not a coin flip and not a default-skip.
2. **INF-3 — the `Write`-block root cause** (T12.4). Now a **Dvārapāla ruling**: determine from the
   evidence available whether the denial was deliberate policy or a glitch, document the boundary or
   the fix, and record the disposition with its reasoning and reversibility.

---

## §3 — TRACK 0 — PRESERVE the work at risk (P0 · URGENT · absolutely first)

**Why first, and why it is new in v2.0:** v1.0's Track 0 proposed retiring
`/Users/Dev/Vibe-Coding/Apps/Madhav` as a build surface. That checkout currently holds **real,
uncommitted, un-backed-up work that exists in exactly one place on earth.** Executing v1.0's Track 0
first would have destroyed it. This track is the correction.

**3.1 — Inventory and commit the untracked work-at-risk.** Present on the working tree, absent from
`origin/main`:

| Path | Note |
|---|---|
| `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/` | **Highest risk** — content is AHEAD of what is committed on `main`. Real in-flight campaign work. |
| `00_ARCHITECTURE/narration_audit/NARRATION_DETERMINISM_AUDIT_v1_0.md` | The 29-finding seed audit this entire arc is built on. A cited source document existing only locally. |
| `00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-3.md` | The PB-3 brief itself — never committed (confirmed absent from `origin/main`). Mode 0600. This is `REPORT_PB-3` §"Governance" item 6. |
| `00_ARCHITECTURE/briefs/pariprashna_build/.fuse_hidden0000000500000001` | Inspect: recover if it is a live file, delete if it is a filesystem artifact. Do not commit blindly. |
| `00_ARCHITECTURE/pariprashna_mockups/` | |
| `00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md` | |
| `00_ARCHITECTURE/llm_consumption_audit/PARISHODHANA_REPORT_v1_0.md` | |
| `03_DOMAIN_REPORTS/REPORT_WHOLE_CHART_SYNTHESIS_AND_MCP_DIAGNOSTIC_v1_0.md` | |
| PB-3 `STATE_*` / lane-state shards (locate; `BRIEF_PB-3.md` §1/§C require them) | |

Commit each to `main` via the sanctioned PR path, grouped by campaign, with honest provenance
messages ("recovered from working tree, authored by <campaign>, never committed"). **Nothing in this
track is edited for content** — this is preservation, not revision.

**3.2 — Reconcile the two unexplained modified files.** `.mcp.json` and both
`CONDUCTOR_HALT_LOG.md` files show modified on `parishodhana/dark-corpus-remeasure`, predating every
recent session, provenance unknown. Diff each against `origin/main`, determine whether the change is
intentional, and either commit it with a stated reason or revert it. **Do not blanket-revert** — one
of them may be live campaign state.

**3.3 — Reconcile `parishodhana/dark-corpus-remeasure`.** 2 commits ahead / 39 behind `origin/main`.
It is the branch this working tree sits on, and it only gets harder to reconcile. Determine what the
2 commits are, land or abandon them explicitly, then bring the checkout to `origin/main`.

**3.4 — Capture the governance baseline.** Run `drift_detector` + `schema_validator` and record the
exact finding/violation counts as this campaign's baseline (§1). Everything downstream measures
against this number, not against zero.

**Acceptance:** `git status` on the shared checkout is clean; every path in 3.1 is on `origin/main`
or explicitly dispositioned as discardable with a reason; the two modified files are explained; the
branch is reconciled; the governance baseline is recorded.
**Register items closed:** WT-1..4, PB-GOV-1.

---

## §4 — TRACK 1 — Isolation, hygiene, and the structural fixes (P0)

*(v1.0's Track 0, corrected and extended. Runs only after T0.)*

**Why:** on 2026-07-29 a session's shell drifted into the shared main checkout and was one
`git rebase` from acting there, caught only by git's own uncommitted-changes guard. Multiple
autonomous campaigns sharing one working tree is the top structural risk.

**4.1 — Per-campaign isolation.** Establish a shared bare repo (or equivalent); give each
active/future campaign its OWN dedicated worktree/clone. No campaign works in the common
`/Users/Dev/Vibe-Coding/Apps/Madhav` checkout again.

**4.2 — Worktree + branch retirement (CORRECTED SCOPE).** `git worktree list` = **35** entries;
`prunable` = **0**, so v1.0's "prune the prunable" would remove nothing. The real work is retiring
the **11 PB worktrees** and their remote branches, after confirming each is fully merged:
`Madhav-pb-1-c1` · `-pb-1-integrate` · `-pb-1-s1` · `-pb-2-integrate` · `-pb-3-l1` · `-l2` · `-l3` ·
`-l3-clean` · `-l4` · `-l5` · `-l6`. Then audit the remaining 24 by the same standard. Delete the
redundant local branch `satyadipa/orchestrator-lit-predicate` (superseded by merged #870).

**4.3 — Codify the merge-lock + deploy-window protocol** (§1) as a short standing doc under
`00_ARCHITECTURE/` so future sessions inherit it rather than rediscovering it.

**4.4 — Kill the migration-collision class at the root.** Two migration directories carry
overlapping 4xx sequences (§0.4). Do all three: (a) document the corrected `max()`-across-both rule
in the protocol doc from 4.3; (b) add a **CI guard** that fails on a duplicate migration number
across BOTH directories; (c) record whether the two-directory split is intentional — if it is not,
file a costed consolidation spec rather than performing it here (out of this brief's authorization).

**4.5 — Standing note: the local Postgres proxy.** Record the `ECONNREFUSED 127.0.0.1:5433` /
stale-Cloud-SQL-Auth-Proxy pattern in the protocol doc with the restart command, so future lanes stop
mistaking a dead proxy for absent data.

**Acceptance:** each campaign has an isolated working directory; the shared checkout is no longer a
build surface; the protocol doc exists and covers merge lock, deploy window, the corrected migration
rule, and the proxy; the duplicate-migration CI guard is merged and passing; `git worktree list` is
clean of dead entries and all 11 PB worktrees/branches are retired or explicitly retained with a reason.
**Register items closed:** INF-1, INF-4, INF-5, WT-5, MIG-1.

---

## §5 — TRACK 2 — Ṣaḍbala: verify, evidence, and finish the sweep (P1 — demoted from P0)

**Why demoted:** §0.2 — the fix is merged, deployed, and live-correct. This track no longer builds
anything; it *proves* and *extends*.

**5.1 — Capture the live evidence (do this once, first).** Record verbatim, with timestamp and
revision id, the deployed `graha_portrait` Ṣaḍbala sentence for the canonical chart. The
consolidation session's capture, for the close report's before/after:

> **AFTER (live, 2026-07-29T19:54:20Z, canonical chart `482012f1`):**
> *"Sun = 5th lord for Aries lagna. Shadbala: 8.47 rupas vs 5.00 required — grade: strong (surplus)
> (+3.47 rupas)."*

The BEFORE string ("weak") must be quoted from `SUDDHA_VACA_REPORT`/the native's original complaint,
**cited as historical** — it is no longer reproducible live, and must not be presented as if it were.

**5.2 — Finish the 7-graha golden-table sweep.** v1.0's own acceptance demanded all 7 grahas match
the golden table in `SUDDHA_VACA_BRIEF §5 C.8`. Only Sun is confirmed. Probe the remaining six live
and diff against the golden table. Any mismatch is a new finding with its own lane.

**5.3 — Confirm the ga-tajaka rebuild's invariants** (SV-2 closure evidence, not re-fix): FORENSIC
7/7 and row-count invariants on both rebuilt charts.

**5.4 — Confirm INF-2 stays closed.** The MCP deploy path was red for a real reason and went green
recently. Re-confirm a promotion succeeds, and verify the smoke test is a *real* detector (per §N.8)
rather than one that passes because it stopped checking.

**Acceptance:** verbatim live before/after captured and cited honestly; all 7 grahas match the golden
table or each divergence is a filed finding; FORENSIC 7/7 holds; MCP deploy demonstrably promotes and
its smoke test demonstrably can fail.
**Register items closed:** SV-1 (evidence), SV-2 (evidence), INF-2 (evidence), SV-GOLD-7.

---

## §6 — TRACK 3 — Narration residuals, FULLY enumerated (P1/P2)

*(v1.0's SV-3..SV-8, corrected: SV-3/SV-4 are closed; SV-5..SV-8 expand to ≈50 findings.)*

**6.1 — VERIFY first.** SV-3 (`ga_structural_writer`, #864) and SV-4 (migration 339, #862) are
**CLOSED** (§0.2). Record as VERIFIED-FIXED with the merge commits. Do not re-open.

**6.2 — SV-5 · `mi_darshana` narration gap.** The P0-10 truthiness defect is fixed (#839). What
remains is the PARKED-HONEST `verdict_note` tradition-blindness: *"Strong evidence across traditions"*
is phrased purely from `grade >= 6.0`, ignoring whether `tradition_concordance` holds any data. The
source report correctly judged this **not a clean one-line fix** (needs restructuring across two
axes). Either restructure it properly or re-park it with a costed spec — do not one-line it.

**6.3 — The P1 band (6 findings, `SUDDHA_VACA_FIX_LEDGER` §P1).** Fix at origin, rebuild affected
assets, live-verify each:

| # | File:line | Defect | Note |
|---|---|---|---|
| P1-a | `bo_pramana_mapa.py:224/228/262/278` | 4 detector-less "verification" fields | **Routed to T4** — this is the FC-1..3 cluster, an §N.8 defect, not a narration one. One PR. |
| P1-b | `ph_phaladesa.py:121` | contradiction-caution sentence is dead code; `contradiction_jsonb` fetched, never consumed | |
| P1-c | `ka_bhavishya_lekha.py:232` + `:226` | `obstruction_summary`/`net_label` fetched but never narrated — obstructed windows read identically to clear ones | Same root cause, two symptoms. **See also T6.4** — the same file has a *separate* stale-vocabulary defect. |
| P1-d | `kala_temporal.ts:377` / `:380` | "active today" fields are date-range-scoped not today-scoped; empty-array truthiness bug | |
| P1-e | `services/ph_phaladesa/engine.py:39` | OpenAI allowlist hole | **ALREADY FIXED** — merged #837 with P0-11. Verify and record. |
| P1-f | `ga_writers/gates.py:144` | `run_g7_only_facts_gate_db` Check 3 hardcodes a `valid_statuses` allowlist now stale against the vocabulary this audit's own writers use — a verified row can fail the gate, or a real gap pass it | Architecturally significant: a gate that mis-grades. |

**6.4 — The P2 band (≈39 findings).** Enumerated in `SUDDHA_VACA_FIX_LEDGER` §P2. Batch by subsystem
(`bo_*`, `ga_*`, `mi_*`, `ph_*`, `ka_*`, serve) into several PRs. **Two must NOT be deprioritized as
"cosmetic," per the ledger's own warning — both are §N.8 violations wearing a P2 label and are
routed to T4:**
- `ga_nakshatra.py:87` — hardcodes `verification_pass_status='PASS'` on every row **with zero actual
  verification logic**. This is the purest Earned-Signal violation in the corpus.
- `bo_chart_gestalt.py:210` — stores a verdict in a writer whose own docstring bans storing verdicts.

Remaining P2 CONFIRMED: `capabilities.ts:72`, `envelope.ts:1416`, `vidhi_registry_resource.ts:71`,
`server.ts:687`, `register_p1_synthesis.ts:893`, `l3_snapshot.py:519`, `l3_timeline.py:270`,
`answer_quality.py:180`, `muhurta.py:355`, `l4_anchors.py:211`, `ga_sade_sati_writer.py:974`,
`bo_bimba.py:253`, `bo_karanajala.py:1387`, `bo_upaya.py:1251`, `ga_nakshatra.py:289`,
`bo_pratijna.py:102`, `mi_sambandha.py:81`, `mi_darshana.py:159`, `mi_pramana.py:382`,
`gochara_grammar/primitives.py:788`, `ph_sodhana/engine.py:38` + `:136`, plus seed F4/F8/F11/F17/
F19/F20/F21/F24. PLAUSIBLE (verify before fixing, may REJECT): `register_p1_ganita.ts:374`,
`ga_sensitive_writer.py:2677`, `bo_cdlm_summary.py:348`, `ka_kala_darshana.py:180`,
`mi_darshana.py:360`, `mi_bhavisya.py:103`, `mi_bhavisya.py:161`.

**6.5 — The P3 band (≈5).** `ph_rectification/engine.py:253` (verify the "sourced from chart_facts,
embedded as constant" justification holds); seed F18 (**CANNOT-REPRODUCE** — disposition it as such,
do not manufacture a fix); `mi_gunanaka.py:337` non-fatal `'UUID' object is not subscriptable` in the
optional snapshot-publish step; `bo_laksana_rerank` `writer_timeout_seconds=600` (config-tuning
recommendation, **NOT-APPLICABLE** to narration scope — self-healed by existing `RR-fix`
reconciliation; record, do not chase).

**6.6 — Resolving v1.0's undefined SV-6 / SV-7.** v1.0 could not name these. Against
`SUDDHA_VACA_REPORT`'s disposition table, the only un-closed "operational/pre-existing" rows are
`mi_gunanaka.py:337` and the `bo_laksana_rerank` timeout — both now carried explicitly in 6.5.
**SV-6/SV-7 are hereby retired as identifiers**, replaced by the named findings. If the native
intended something else by them, that is a one-line correction to this brief, not an open item.

**Acceptance:** every P1/P2/P3 finding carries VERIFIED-FIXED / PARKED-HONEST / REJECTED /
NOT-APPLICABLE with evidence; PLAUSIBLE items are adversarially verified before being fixed (a
refuter tries to reject each); affected assets rebuilt and FORENSIC-clean; no finding is closed by
assumption.
**Register items closed:** SV-3..SV-8 (superseded by the enumeration above), NAR-P1-a..f, NAR-P2-*, NAR-P3-*.

---

## §7 — TRACK 4 — The Earned-Signal (§N.8) sweep (P1)

**7.1 — FC-1..3 · `bo_pramana_mapa` detector-less flags.** `lel_zero_leak_pass` (a proxy — no LEL
scan), `pillars_meet_reachability_pass` (a tautology that can only ever be True),
`trap2_narration_leak_count` / `divergent_flagged_count` (literal `0`, no detector). Per §N.8: give
each a **real detector, or set it null** — never a clean-looking default. Rebuild the asset.

**7.2 — The two P2-labelled §N.8 violations** routed from T6.4: `ga_nakshatra.py:87` and
`bo_chart_gestalt.py:210`.

**7.3 — The five named build-layer files** (`SATYA_DIPA_REPORT` §5 — scoped, never swept):
`runner.py` · `staleness.py` · `dag_edge_guard.py` · `kala_derivation_completeness_guard.py` ·
`service_probes.py`. This is the sweep's **defined starting set** and its completion test.

**7.4 — FC-4 · codebase-wide sweep.** Beyond 7.3, audit every boolean/grade/status/PASS in the build
and serving layers against one question: *does a detector measure the claim it asserts?* Produce a
findings register; **adversarially verify each** (a refuter tries to reject it); fix or null each.
Known members already identified across the arc, to be included and closed here:
- PB-3 §G item 9 — "no auto-promotion" is true by inspection only, with **no dedicated detector or
  CI test**. By this brief's own doctrine that is an unearned green. Build the detector (T5.7).
- The MCP post-deploy smoke test — verify it can fail (T2.4).
- PB-2's byte-equality gate — the original false-confidence gate (T5.8).

**7.5 — The permanent enforcement.** Add a **CI lint** that flags a status/grade/PASS field with no
detector behind it — the standing §N.8 guard, sibling to the `fact_key` lint from #840. Scope it
honestly and state its bounds in its own docstring (as #840 did); a lint that overclaims its coverage
is itself an §N.8 violation.

**Acceptance:** FC-1..3 carry a detector or null; the five named files are swept with a written
register; the codebase-wide register is adversarially verified; the §N.8 lint is merged and passing;
affected assets rebuilt and FORENSIC-clean.
**Register items closed:** FC-1, FC-2, FC-3, FC-4, N8-SWEEP-5, PB-9-DETECTOR.

---

## §8 — TRACK 5 — Make the prediction loop live (P0 for G1; P1/P2 for the rest)

**8.1 — Execute `BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE.md` verbatim.** It is the authoritative spec for
gaps **G1–G5 only**. Do not paraphrase it here; read it.

| Gap | Pri | Summary |
|---|---|---|
| **G1** | **P0** | Mount `LogToSamiksha` → `POST /api/pariprashna/samiksha/confirm` on the live reading route. The loop's only missing entry point; every other FAIL traces to it. |
| **G2** | P1 | `samiksha-daily.yml:63` reads `secrets.DATABASE_URL`; the repo's secret is `PROD_DATABASE_URL`. Also change the no-secret branch from `exit 0` to a visible failure so a misconfigured run can never report green again. |
| **G3** | P1 | `SAMIKSHA_TEST_DATABASE_URL` / `SAMIKSHA_E2E_DATABASE_URL` set nowhere in CI → 6 DB-integration test files permanently skipped. Wire them in. This is the net that should have caught G2. |
| **G4** | P2 | Reconcile the resolve route's local outcome map against the uncalled L-5 `recordConversationalOutcome`. One map, with a live caller — or a documented reason for two. |
| **G5** | P2 | Complete + wire the calibration leak guard: add the 4 omitted files to `serving_path_manifest.ts`, add the spine-bundle URI to `CALIBRATION_CONTEXT_ONLY_URIS`, widen `CALIBRATION_LEAK_KEYS` to match a bare `calibration` key, give `assertNoCalibrationLeak` a real call site. |

**Acceptance (LIVE, per PB-3.1 A1–A6, quoted not paraphrased):** a real deployed reading writes a
`detected` ledger row (psql-verified) → renders on the live review tab → resolves to an outcome,
can't-tell → NULL (the demonstrated-can-fail DB-constraint proof preserved as the template) → the
daily job transitions a real window with the corrected secret AND the CI integration tests RUN and
pass in the real pipeline → exactly one outcome map with a live caller → the leak guard runs in prod,
covers both paths, and a mutation proves it can fail. **No fixture may substitute for a live proof.**

### The items PB-3.1 does NOT cover (carried here explicitly, per §0.3)

`REPORT_PB-3` records these as deliberately out of PB-3.1's scope. v1.0 folded them in under
"execute verbatim," which is contradictory. They are separate, and each may park on its own merits.

**8.2 — PB-6 · UI geometry (P1).** Mount the spec-conformant `samiksha/KalaRekha.tsx` /
`PredictionCard.tsx` pair (currently dead code, imported by nothing) in place of the fixture-fed dock
card — **or** wire `todayFractionOfSpan` from a real date on the live SSE adapter path. Its sole
producer today is the hardcoded fixture literal `0.3`, so the dock card never renders on the real SSE
path at all. Fix the dot to 3px (currently 7px) on whichever component ships. Fix the review-tab
`KalaRekhaTimeline.tsx` geometry domain (window-padded → "reading-date to window-end" per §6.9) and
its start/end date-caption placement (currently under the padded-span extremes, not under the dates
they label).

**8.3 — PB-7 · badge-equals-SQL (P1, gated on G1).** Currently **evidentially vacuous** — only ever
checked at `0 == 0`. Re-verify against a NON-ZERO ledger once G1 lands. Not startable before then;
sequence it, do not park it.

**8.4 — PB-8 · byte-equality gate (P2).** `FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md`. v1.0
cited the doc; the doc's actual content is that **two independent things are needed and neither
exists**: (a) a fixture-corpus bridge — the 12-fixture corpus is the old C-2 harness shape and cannot
be quickly repointed, and `c2ProtocolAdapter.ts` converts to a *third*, UI-only shape, so it does not
solve it either; and (b) real-reading stream capture. Build both, or **PARK with a costed spec for
each**. Do not report this closed on the strength of the adapter.

**8.5 — PB-3 §G item 1 · the schema hash pin (P2).** The brief's demanded schema *hash* pin never
existed — only a prose row-count. `REPORT_PB-3` recorded a fingerprint (`b730b9f3…`) with nothing
prior to compare it against. Establish the pin properly now so the next wave has a real baseline.

**8.6 — PB-3 §G item 9 · the missing detector.** Routed to T7.4 — build the CI test that would catch
a future auto-promotion regression.

**8.7 — Integration-hygiene verify.** Confirm the L-3 vendored-DAL de-dup and `git add` hygiene
actually landed at PB-3 integration, and that L-4's two test files were placed via the sanctioned path.

**Register items closed:** PB-1..PB-8, PB-SCHEMA-PIN, PB-INTEG-VERIFY.

---

## §9 — TRACK 6 — Build-state truth: finish what `lit` now honestly reports (P1)

*(Replaces v1.0's Track 4, whose premise — an enumerated falsely-`lit` population — is empirically
empty. §0.3.)*

**9.1 — Record EP-1 correctly.** `SATYA_DIPA_REPORT` §"Plain-language answer" + §4: **zero**
currently-`lit` assets were falsely promoted; Phase D had no work to do. The `lit` predicate is now
honest. Disposition EP-1 **NOT-APPLICABLE (empirically empty)** with the evidence — not as a
completed re-audit, and not as an open item. Then do the reconciliation §9.2, which is the real work.

**9.2 — Reconcile the inventory anyway, cheaply.** For every `lit`/`service_ok` asset, check
`build_substep_progress` (**READ-ONLY — never mutate it**) against the full plan, and `rows_written`
against `expected_rows`. SATYA-DĪPA did this once and found it clean; re-run it as a standing check
now that other tracks have rebuilt assets. Anything genuinely incomplete → snapshot-guarded rebuild
in dependency order, live-verified. Assets independently corroborated by row-counts + FORENSIC 7/7 +
double-build determinism (the ŚUDDHA-VĀCA rebuilds) already stand — record as confirmed, no redo.

**9.3 — `ka_gochara_sweep` operator-chart parity (the item v1.0 omitted entirely).** This is the one
concrete case that motivated SATYA-DĪPA, and it is still unresolved on the data side:

| chart | substeps | state |
|---|---|---|
| `482012f1` (canonical) | 303/303 | `lit` — correct |
| `1c826d5a` (operator) | **78/303** | `error` — honest, unfinished |
| `cb73cd3d` | **70/303** | `error` — honest, unfinished |

The code can no longer lie about it; **nobody has finished the build.** Prior attempt was a
native-directed stop (PARKED-HONEST), so this track **re-opens it deliberately**: diagnose why the
sweep stalls at ~1/4 of its 303 substeps (3 event_classes × 101 years), fix or park with a real
root-cause statement, and run it snapshot-guarded to completion. **If it stalls again for the same
unresolved reason, PARK-HONEST with the diagnosis — do not force it.** That is the standing native
instruction and it survives into this brief.

**9.4 — `ka_bhavishya_lekha.py` stale domain vocabulary.** Uses `finance`/`spiritual` against the
canonical `wealth`/`spirituality`. Flagged as able to fail a live build. **PARKED-HONEST twice now**
— once in `PARKED_FINDINGS_CLOSE`, carried unchanged through SATYA-DĪPA. Real, not cosmetic. Fix it
here. (Distinct from the same file's narration defect in T6.3 P1-c — same file, two defects; fix
together, verify separately.)

**9.5 — `chart_dashas` CLI-only scope-cap sentinel** silently swallowed. Low urgency, CLI path only —
but carried unchanged across two campaigns. Fix or reject with a reason; do not carry it a third time.

**9.6 — Durable `asset.noop_completion` event register.** `SATYA_DIPA_REPORT` §1 is unambiguous: the
events go only to stdout (Cloud Logging, ~30-day retention, and a `--freshness=9999d` query returned
**zero** results) or to a fire-and-forget Pub/Sub topic whose only consumer holds a 600-second
per-connection window. **There is no queryable history at all** — which is why SATYA-DĪPA's own Phase
A had to abandon its primary forensic method. Build a durable table or a Cloud Logging export sink,
so the next audit of this defect class has a real register. Persist both `asset.noop_completion` and
`asset.noop_completion_rejected` with `rows_present` + `substeps_remaining`.

**9.7 — Cockpit UI: teach it the `incomplete` state.** Five TypeScript files declare `AssetState`-style
unions that omit the new value: `src/lib/build/plan.ts`, `src/app/api/cockpit/stats/route.ts`,
`src/components/build/AtlasView.tsx`, `src/components/build_orchestrator/AssetNode.tsx`,
`src/hooks/useCockpitSSE.ts`. Functionally harmless (dependency gating is allowlist-based) but an
`incomplete` asset renders via an unstyled/default branch until fixed. Cosmetic, non-blocking, real.

**Acceptance:** EP-1 dispositioned NOT-APPLICABLE with evidence; the inventory reconciliation is
re-run clean or every exception rebuilt; `ka_gochara_sweep` is complete on all three charts **or**
parked with a root-cause diagnosis (not a shrug); 9.4/9.5 fixed or rejected with reasons; the event
register exists and is queryable; the cockpit renders `incomplete` correctly.
**Register items closed:** EP-1, GOCH-1, SD-VOCAB-1, SD-DASHA-1, SD-EVENTREG-1, SD-COCKPIT-1.

---

## §10 — TRACK 7 — CI and harness health (P1)

*(Absent from v1.0 entirely. It belongs, because it red-flags every PR this campaign will raise.)*

**10.1 — Boot-time pointer validation SC-17/18/19.** Fails on every recent PR, **confirmed
pre-existing on unmodified `main` and reproduced independently**. Harness lives at
`platform/scripts/audit/tap/sc_pointer_validation.ts` (surfaced via `tap5_seam_conservation.ts`).
Three distinct sub-items, do not conflate:
- `SC-pointer:x` in `response_budget_verdict_immune_and_trim_order.test.ts` is an **unregistered new
  regression** per the harness's own baseline. Register it or fix it — it must not stay unlisted.
- Two pointers sit **QUARANTINED** (`query_signals`, `get_divisionals`). Resolve or document the
  quarantine with an expiry.
- One (`query_classical_texts`) is flagged **"NEW-P2 — verify intended target before filing"** and was
  **never filed**. File it.

Until this is green (or its residuals are formally whitelisted like drift/schema), every PR in this
campaign carries a red signal that masks real regressions. Fix it early.

**10.2 — Re-declare the tolerated-residual baseline.** `drift_detector`'s ~216 findings and
`schema_validator`'s 43–45 violations are long-standing, explicitly tolerated exit-code-3 residuals
(`ONGOING_HYGIENE_POLICIES` §F known_residuals whitelist) — and the backlog **keeps growing**, which
is the actual problem. Do not attempt to clear them here (out of scope, and v1.0's "green" criterion
was unachievable). Instead: re-baseline against T0's capture, confirm **zero new violations
attributable to this campaign**, and file a costed spec for the quarterly governance pass to
actually drain the backlog rather than re-tolerating it forever.

**Acceptance:** SC-17/18/19 green or formally whitelisted with each of the three sub-items
dispositioned; the drift/schema delta versus the T0 baseline is zero; a costed backlog-drain spec exists.
**Register items closed:** CI-SC-1, CI-SC-2, CI-SC-3, CI-BASELINE-1.

---

## §11 — TRACK 8 — PB-4 PŪRṆATĀ (HUMAN GATE — see §2)

**Status: NOT STARTED. Entire wave.** Scope per `BRIEF_PB-4.md`: history sidebar, empty state, "the
Seal," mobile/a11y hardening, default flip, consult/consume retirement, dead-code deletion. It was
blocked in sequence on the PB-3.1 disposition — which T5 resolves.

**This is a decision, not an omission.** PB-4 is a feature wave, not a gap closure. Folding it in
silently would change this brief's character and roughly triple its size; leaving it out silently
would make "close every open item" false. So it is named, sized, and gated:

- **Option A — Execute after T5.** The dependency is genuinely cleared once the loop is live. The
  arc closes completely, at materially greater cost and wall-clock.
- **Option B (default) — DEFERRED-BY-DEFAULT.** Close SAMĀPTI with PB-4 recorded as the single
  intentionally-open wave, its brief READY-FOR-EXECUTION and its blocker documented as cleared. The
  close report says so in its opening summary rather than burying it.

**If unanswered, Option B applies** and is stated plainly in the close report. Either way, `REPORT_PB.md`
(T9.2) must reflect the real state — the PB campaign cannot claim close while PB-4 is unrun.
**Register items closed:** PB-4-WAVE (by execution or by explicit deferral).

---

## §12 — TRACK 9 — Governance close-out (P2, but blocking for COMPLETE)

**12.1 — The PB-3 memo index.** Never produced as its own artifact. Cross-reference `MEMO_PB-3_0`,
`LEDGER_MAP_PB-3`, `PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE`,
`FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE`, `REPORT_PB-3`, `BRIEF_PB-3`, `BRIEF_PB-3.1`.

**12.2 — `REPORT_PB.md`** — the PB campaign close report with a memo index across PB-0→PB-4. Cannot
claim COMPLETE while PB-4 is unrun (T8); write it to reflect whichever T8 option was taken.

**12.3 — The `PARK_PB-3_L-5` Pratinidhi MEMO.** Still an open ask on the conversational-calibration
write target; never issued. Issue it, or record why it is no longer needed if T5's G4 supersedes it.

**12.4 — INF-3 · `Write`-block root cause (HUMAN GATE, §2).** Determine whether `Write` was denied
deliberately or by a glitch. If deliberate, document the boundary. If a glitch, fix it so the
heredoc-bypass temptation stops recurring. Record the disposition either way.

**12.5 — Migration 474's internal comment.** Its header still reads `-- Migration 467: …` after two
renumbers (466→467→474). The applied SQL is correct and live in production; the file lies about its
own number. One-line fix. **Verified present during this consolidation.**

**12.6 — The inherited `OPEN_ITEMS_REGISTER_v1_0.md`.** The real one (§frontmatter `registry_correction`)
carries its own genuinely-open items nobody has closed: A4 (`chore/repo-hygiene-isolated` branch +
stale `/Madhav-nirmana-ui/` dir), B2/B3/B4 (connection-resilience guards marked ⚠️ VERIFY, never
confirmed), B5, B6, C2/C3/C4/C5, D3/D4, E3. **Disposition each** — most will be ALREADY-FIXED or
OBSOLETE given a year of intervening work, but that must be *checked*, not assumed. This is exactly
the reconciliation pass the register was written to make possible.

**12.7 — The coordination-check accounting.** The original standing instruction for this whole task
asked for a final report on which ŚUDDHA-VĀCA / PARISHODHANA / SATYA-DĪPA coordination checks were
exercised and their outcomes. The individual checks were performed throughout (holds, PR-state
checks, branch/worktree avoidance) but **were never compiled into the single itemized accounting
originally requested.** Compile it.

**12.8 — Standing docs.** Confirm CLAUDE.md, `CURRENT_STATE`, `SESSION_LOG`, and the registries
reflect the closed state with no version/section collisions. Note CLAUDE.md's history of
frontmatter/footer version drift — check both.

**Register items closed:** INF-3, PB-MEMO-INDEX, PB-REPORT, PB-PARK-MEMO, MIG-474-COMMENT,
OIR-INHERIT, COORD-ACCT, GOV-DOCS.

---

## §13 — Sequencing

Build may be parallel in isolated worktrees; INTEGRATE/DEPLOY one at a time under the merge lock.

1. **T0 — PRESERVE.** Absolutely first. Nothing may touch the shared checkout's layout before the
   at-risk work is committed.
2. **T1 — Isolation + hygiene + migration guard.** De-risks everything after it.
3. **T7 — CI/harness health.** Early, so every subsequent PR has a trustworthy signal.
4. **T2 — Ṣaḍbala verify + 7-graha sweep.** Cheap; produces the headline evidence the native wants.
5. **T5 — Prediction loop live.** G1 is the highest-leverage single fix in the brief. PB-7 sequences
   behind G1; PB-6/PB-8 are independent.
6. **T3 — Narration residuals** and **T4 — §N.8 sweep.** Run adjacent; T4 receives three findings
   routed from T3 (the `bo_pramana_mapa` cluster, `ga_nakshatra.py:87`, `bo_chart_gestalt.py:210`).
7. **T6 — Build-state truth.** Independent of T2–T5; can start any time after T1.
8. **T8 — PB-4.** Only on the §2 gate; after T5 if executed.
9. **T9 — Governance.** Closes the arc; 12.6 can run early in parallel since it is read-mostly.

**Cross-campaign:** ṢAḌ-DARŚANA and PARISHODHANA may move `main`/migrations underneath — always
rebase immediately before merge, and re-check the migration `max()` across **both** directories at
that moment. PARISHODHANA #827/#828 (v1.0's stated blocker for Track 1) **merged 2026-07-28** and no
longer gate anything.

---

## §14 — Acceptance criteria for the whole brief (COMPLETE only when all hold)

1. **Every item in Appendix A** is dispositioned with evidence: VERIFIED-FIXED / PARKED-HONEST /
   REJECTED / NOT-APPLICABLE. No "passed with caveats." A disposition citing a merge commit, a live
   probe, or a psql result is evidence; a disposition citing a prior brief's claim is not.
2. `graha_portrait` shows Sun STRONG on the deployed portal — **already true (§0.2)**; the close
   report carries the verbatim live capture plus the historically-cited "weak" original, and all 7
   grahas match the golden table.
3. The prediction loop is live end-to-end (a real reading → ledger → review → resolved outcome),
   proven live, not by fixture.
4. Each campaign runs in its own isolated worktree; the shared checkout is retired as a build
   surface — **and every at-risk artifact it held is on `origin/main` first**.
5. The §N.8 detector-less-gate CI lint is merged and passing, alongside the narration `fact_key`
   lint, `fresh_chart_smoke.yml`, and the new duplicate-migration guard.
6. Zero regressions: all existing suites green; FORENSIC 7/7; row-count invariants hold or every
   delta explained; **`drift_detector` + `schema_validator` show zero NEW violations against the T0
   baseline** (not "green" — §0.3); SC-17/18/19 green or formally whitelisted with all three
   sub-items dispositioned.
7. Every production deploy verified healthy; the MCP deploy path demonstrably promotes revisions and
   its smoke test demonstrably can fail.
8. Governance closed atomically: `SESSION_LOG`, `CURRENT_STATE`, `CLAUDE.md`, registries — no
   collisions; memo index, `REPORT_PB.md`, and the coordination accounting all exist.
9. **PB-4 is either executed or explicitly recorded as DEFERRED-BY-DEFAULT** in the close report's
   opening summary — never silently absent.

---

## §15 — What the native wakes to

A close-out report opening with the four sentences that matter:

1. **Can `graha_portrait` be opened right now and show Sun as strong — yes or no?** (Today: **yes**,
   8.47 rūpas vs 5.00 required, +3.47 surplus, live-verified 2026-07-29T19:54Z.)
2. **Can a real reading now be logged, reviewed, and resolved end-to-end — yes or no?**
3. **Is any campaign still sharing a working tree, and did anything uncommitted get lost — no and no?**
4. **What is still open, and why is that honest?**

Then the four-disposition table over every item in Appendix A, the live before/after proofs for
Ṣaḍbala and the prediction loop, the `ka_gochara_sweep` outcome, the PB-4 decision, and the
coordination accounting. Nothing that requires reconstructing the reasoning by hand.

---

## Appendix A — Consolidated register and traceability

**Legend — Source:** `v1` = SAMAPTI v1.0 · `N` = native's 2026-07-30 enumeration · `C` = surfaced by
this consolidation. **Status at authoring:** verified during this session where marked ✅/⚠️.

### Group 1 — Infrastructure, isolation, and work-at-risk

| ID | Item | Track | Source | Status at authoring |
|---|---|---|---|---|
| WT-1 | Untracked work-at-risk (`kala_elevation` ahead of main, `narration_audit`, mockups, plans, reports) | T0.1 | N | OPEN — single-copy loss risk |
| WT-2 | `BRIEF_PB-3.md` + PB-3 lane-state shards never committed | T0.1 | N | ✅ confirmed absent from `origin/main` |
| WT-3 | `.mcp.json` + 2× `CONDUCTOR_HALT_LOG.md` modified, provenance unknown | T0.2 | N | OPEN |
| WT-4 | `parishodhana/dark-corpus-remeasure` diverged 2 ahead / 39 behind | T0.3 | N | ✅ confirmed |
| INF-1 | Campaigns share one working tree | T4.1 | v1 | OPEN |
| WT-5 | 11 PB worktrees + remote branches un-retired | T4.2 | N | ✅ confirmed (35 total, 0 prunable) |
| INF-4/5 | Worktree hygiene + `satyadipa/orchestrator-lit-predicate` branch | T4.2 | v1 | OPEN |
| MIG-1 | **Two migration dirs with overlapping 4xx sequences** — root cause of the 467 collisions | T4.4 | **C** | ✅ confirmed (474 vs 473) |
| PROXY-1 | Local Postgres proxy ECONNREFUSED 5433 | T4.5 | N | ✅ reproduced this session |

### Group 2 — Ṣaḍbala visibility (v1.0's Track 1 — now closed)

| ID | Item | Track | Source | Status at authoring |
|---|---|---|---|---|
| SV-1 | serve-shadbala `registry_bridge.ts` | T2.1 | v1 | ✅ **CLOSED** — #852, live-verified |
| SV-2 | `ga_tajaka_writer.py` hardcoded orb | T2.3 | v1 | ✅ **CLOSED** — #853 |
| INF-2 | MCP deploy broken | T2.4 | v1 | ✅ **CLOSED** — 3 consecutive successful deploys |
| SV-GOLD-7 | 7-graha golden-table sweep | T2.2 | v1 | OPEN — only Sun confirmed |

### Group 3 — Narration residuals

| ID | Item | Track | Source | Status at authoring |
|---|---|---|---|---|
| SV-3 | `ga_structural_writer.py` unpinned `fact_key` | T6.1 | v1 | ✅ **CLOSED** — #864 |
| SV-4 | Migration 339 OpenAI allowlist | T6.1 | v1 | ✅ **CLOSED** — #862 |
| SV-5 | `mi_darshana` `verdict_note` tradition-blindness | T6.2 | v1 | OPEN — not a one-liner |
| SV-6/SV-7 | *undefined in v1.0* | T6.6 | v1 | **RETIRED as identifiers** → replaced by named findings |
| NAR-P1-a..f | The 6 P1-band findings (a → routed to T7.1) | T6.3 | v1 (as SV-8) | OPEN (P1-e ✅ closed #837) |
| NAR-P2-* | ≈39 P2-band findings | T6.4 | v1 (as SV-8) | OPEN |
| NAR-P3-* | ≈5 P3-band findings | T6.5 | v1 (as SV-8) | OPEN |

### Group 4 — Earned-Signal (§N.8)

| ID | Item | Track | Source | Status at authoring |
|---|---|---|---|---|
| FC-1..3 | `bo_pramana_mapa` detector-less flags (4 fields) | T7.1 | v1 | OPEN |
| FC-4 | Codebase-wide detector-less-gate sweep + CI lint | T7.4/7.5 | v1 | OPEN |
| N8-SWEEP-5 | The five named build-layer files | T7.3 | N | OPEN — scoped, never swept |
| N8-P2-2 | `ga_nakshatra.py:87` + `bo_chart_gestalt.py:210` | T7.2 | C | OPEN — §N.8 violations mislabelled P2 |

### Group 5 — Prediction loop (PARIPRAŚNA)

| ID | Item | Track | Source | Status at authoring |
|---|---|---|---|---|
| PB-1..5 | PB-3.1 gaps G1–G5 | T8.1 | v1 + N | OPEN — spec ready |
| PB-6 | Dock card / kāla-rekhā geometry | T8.2 | v1 + N | OPEN — **not** in PB-3.1 |
| PB-7 | Badge-equals-SQL re-verify | T8.3 | v1 + N | OPEN — gated on G1 |
| PB-8 | Byte-equality: fixture bridge + stream capture | T8.4 | v1 + N | OPEN — two missing components |
| PB-SCHEMA-PIN | §G item 1 schema hash pin never existed | T8.5 | N | OPEN |
| PB-9-DETECTOR | §G item 9 no-auto-promotion has no detector | T7.4/8.6 | N | OPEN |
| PB-INTEG-VERIFY | L-3 DAL de-dup + L-4 test placement | T8.7 | v1 | OPEN |

### Group 6 — Build-state truth (SATYA-DĪPA residue)

| ID | Item | Track | Source | Status at authoring |
|---|---|---|---|---|
| EP-1 | Falsely-`lit` re-audit | T9.1 | v1 | **NOT-APPLICABLE** — population empirically zero |
| GOCH-1 | `ka_gochara_sweep` operator parity (78/303, 70/303) | T9.3 | N | OPEN — **absent from v1.0**, native-flagged urgent |
| SD-VOCAB-1 | `ka_bhavishya_lekha.py` stale domain vocabulary | T9.4 | N | OPEN — parked twice |
| SD-DASHA-1 | `chart_dashas` CLI-only sentinel | T9.5 | N | OPEN — carried twice |
| SD-EVENTREG-1 | Durable `noop_completion` event register | T9.6 | N | OPEN — no queryable history exists |
| SD-COCKPIT-1 | Cockpit UI missing `incomplete` state (5 files) | T9.7 | N | OPEN — cosmetic |

### Group 7 — CI and harness health

| ID | Item | Track | Source | Status at authoring |
|---|---|---|---|---|
| CI-SC-1 | `SC-pointer:x` unregistered new regression | T10.1 | N | OPEN — **absent from v1.0** |
| CI-SC-2 | Two QUARANTINED pointers (`query_signals`, `get_divisionals`) | T10.1 | N | OPEN |
| CI-SC-3 | `query_classical_texts` NEW-P2 never filed | T10.1 | N | OPEN |
| CI-BASELINE-1 | drift_detector 216 / schema_validator 43–45 tolerated residuals | T10.2 | N | OPEN — v1.0's "green" was unachievable |

### Group 8 — PB-4 and governance

| ID | Item | Track | Source | Status at authoring |
|---|---|---|---|---|
| PB-4-WAVE | Entire PŪRṆATĀ wave unstarted | T8 | N | **HUMAN GATE** — absent from v1.0 |
| PB-MEMO-INDEX | PB-3 memo index never produced | T12.1 | N | OPEN |
| PB-REPORT | `REPORT_PB.md` campaign close never written | T12.2 | N | OPEN |
| PB-PARK-MEMO | `PARK_PB-3_L-5` Pratinidhi MEMO never issued | T12.3 | N | OPEN |
| INF-3 | `Write`-block root cause | T12.4 | v1 | **HUMAN GATE** |
| MIG-474-COMMENT | Migration 474 header says "Migration 467" | T12.5 | N | ✅ confirmed present |
| OIR-INHERIT | The real `OPEN_ITEMS_REGISTER`'s own ~13 open items | T12.6 | **C** | OPEN — never reconciled |
| COORD-ACCT | Coordination-check accounting never compiled | T12.7 | N | OPEN |
| GOV-DOCS | Standing docs reflect closed state | T12.8 | v1 | OPEN |

---

## Appendix B — v1.0 → v2.0 disposition of every v1.0 item

| v1.0 item | v2.0 disposition |
|---|---|
| INF-1, INF-4, INF-5 | Carried → T1, scope corrected (11 PB worktrees, not "20 prunable") |
| INF-2 | **Closed before execution** — recorded as evidence in T2.4 |
| INF-3 | Carried → T12.4, marked HUMAN GATE |
| SV-1, SV-2 | **Closed before execution** — recorded as evidence in T2 |
| SV-3, SV-4 | **Closed before execution** — recorded as evidence in T6.1 |
| SV-5 | Carried → T6.2, re-scoped (not a one-line fix) |
| SV-6, SV-7 | **Retired as identifiers** (undefined in v1.0) → named findings in T6.5 |
| SV-8 | **Expanded** from 1 line to ≈50 enumerated findings → T6.3/6.4/6.5 |
| FC-1, FC-2, FC-3 | Carried unchanged → T7.1 |
| FC-4 | Carried, **given a defined starting set** (the 5 named files) → T7.3/7.4/7.5 |
| PB-1..PB-8 | Carried, **split** into PB-3.1's G1–G5 (T8.1) vs. the three items PB-3.1 excludes (T8.2–8.4) |
| EP-1 | **Re-premised** — population empirically zero; replaced by the real residue in T9 |
| §9 criterion 1 (register) | **Corrected** — v1.0 cited a register with none of its items; replaced by Appendix A |
| §9 criterion 6 (drift/schema green) | **Corrected** to "zero NEW violations vs. the T0 baseline" |
| §1 migration rail | **Corrected** — `max()` across BOTH migration directories + a CI guard |
| §2 Track 0 ordering | **Corrected** — preservation (T0) must precede isolation (T1) |

*End of SAMAPTI_IMPLEMENTATION_BRIEF v2.0.*
