---
artifact: REPORT_D4B
type: WAVE CLOSE REPORT (protocol §7) — B-6 REAL CLOSE PASS #6, mode=GATED (explicitly NOT a full
  campaign close)
wave: D-4b — Calibration Ignition + Grand Bakeoff (campaign close lane B-6)
status: OPEN — GATED. Headline: B-1 is DONE, genuinely, cleanly, and merged (PR #712) — the first
  legitimate scored result this campaign has ever produced, an honest NO_WINNER. B-2 is now
  blocked on a real architecture gap (CR-128), not a bug in this campaign's own work. This report
  supersedes PR #695/#703/#708 (all merged, preserved in history) and restores content an
  unrelated concurrent campaign's own cleanup revert accidentally rolled back.
authored_by: Orchestrating session, directly (not agent-dispatched), given the precision required
  after (a) a background workflow task died silently with no completion notification mid-B-2, and
  (b) a cross-campaign content-loss incident this pass had to first diagnose and repair.
---

# REPORT_D4B — B-6 Campaign Close Pass #6 (GATED)

## §0 — Headline

**B-1 is done.** After three prior attempts (blocked / VOID-narrowed / quarantined-for-sealed-
split-breach), a fourth attempt — chunked, checkpointed, on a harness now structurally guarded
against the exact defect that quarantined attempt #3 — ran clean, was independently verified twice
over (per-batch receipts + a full adversarial anti-gaming pass), and merged as **PR #712**. The
result is an honest **NO_WINNER**: no contender clears its control with statistical
distinguishability. This is not a failure — it is the campaign's own pre-committed outcome,
reached honestly.

**The wave still does not close.** B-2 hit a genuine architecture gap (CR-128): `BRIEF_D4B.md`'s
described write target for the one-shot backfill does not exist in the live schema. This requires
a native/Binder decision, not a mechanical fix.

## §1 — B-1: the full history, condensed

| # | What | Result |
|---|---|---|
| 1 | Original 5-contender attempt (PR #687) | BLOCKED — 4/5 contenders had no real implementation. Honest, no fabrication. |
| 2 | Narrowed 14-contender / 31-event run, pre-fix (PR #694) | VOID — 433 negative CRPS values (proved F-2 was needed). |
| 3 | Full chunked re-run, post-F1/F2, pre-CR-123 | **QUARANTINED** — scored the sealed test split across all 14 contenders. Every number VOID. Caught by the final anti-gaming pass, three verification altitudes downstream of where it originated. |
| 4 | CR-123/DR-20 fix (PR #709) | The structural fix itself — `sealed_split_guard.ts` wired into the harness's one universal scoring entry point. Not a re-run. |
| 5 | Clean chunked re-run (PR #712) | **MERGED.** Zero sealed-split touches (independently re-confirmed by a from-scratch cross-reference check). DR-12 NO_WINNER, honestly grounded. |

**Attempt #5's adjudication, in detail:** `pratyantar_lord` was the only contender with adequate
coverage (n=31 of 56 TRAIN-scope events). Its raw aggregate skill (+0.1058) looks like a win — but
the anti-gaming verifier's own adversarial statistical re-derivation found this is a **single-
outlier artifact**: one event (`EVT.2002.XX.XX.01`, real CRPS 268.9 vs control 603.9) contributes
+335.1 of the total +141.7 skill-relevant sum — 236% of it. Excluding that one event, the model
**loses** on 27 of the remaining 31 events (exact binomial sign test p=3.40e-05; Wilcoxon one-
sided p=6.85e-04). Every other contender (all 12 PERMISSION systems + the ensemble) scored only
n=2 events each — structurally too thin for any sign test to mean anything (max possible p-value
0.5–1.0). **No contender clears DR-15(b). NO_WINNER is the honest, adversarially-checked
adjudication, not an evasion.**

## §2 — What made attempt #5 different: DR-20 and CR-126/127

Two consecutive unchunked full-scoring dispatches had crashed with zero committed progress before
this campaign adopted checkpointed batching (**CR-126**, closed, proven twice — once on the
breached run, once on the clean one, both completing all 3 batches + assembly cleanly). Separately,
the breach itself produced **DR-20** (`DISAGREEMENT_REGISTER_v1_0.md` DIS.031): *"a train/test seal
is enforced at the query/data layer... never by agent instruction alone."* Its fix, **CR-127**
(`sealed_split_guard.ts`, PR #709), is wired as the first statement in the harness's single
universal scoring funnel — no driver or contender type can bypass it by construction. Verified
independently twice: once by a fresh-context Opus reviewer (including an adversarial millisecond-
precision boundary test not in the original PR), once live by attempt #5's own anti-gaming pass,
which wrote its own independent date cross-reference (not reusing the guard's code path) and
confirmed the exact prior-breach signature — the 2025 marriage event, the 20 post-2020
`pratyantar_lord` scores — is provably absent this time.

## §3 — B-2: CR-128, a real architecture gap

The B-2 dispatch, before writing anything, traced `mimamsa_outcome_record` (B-2's stated write
target per `BRIEF_D4B.md` §1) end to end and found it does not exist — no table, no live write
path, confirmed by direct `pg_tables`/migration-grep queries. **Independently re-confirmed by this
pass**, live: zero `pg_tables` hits for the name; `phala_anchors` has 37 real columns and none is
named `prediction_state`, the column `update_calibration()` requires to populate
`mimamsa_calibration` — dead code against the live schema; `mimamsa_multipliers` (the real
`mi_gunanaka` asset) has 9 rows for this chart, all `n_observations=0`, matching every prior
pass's live check exactly; a third candidate, `mcp_prediction_outcomes`, exists but is empty,
narrowly scoped to resolving one filed prediction at a time, and is wired into nothing. **B-2
correctly halted rather than fabricate a row count against a write mechanism that doesn't exist.**
Full detail: `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-128.

**This requires a real decision, not a fix.** Either (a) repair `update_calibration()`/
`phala_anchors`'s schema mismatch and wire a genuine event→calibration pipeline, or (b) build
whatever `mimamsa_outcome_record` was actually meant to name, since nothing currently exists at
that name. B-2/B-3 stay correctly blocked pending that ruling.

## §4 — Process incident: cross-campaign content loss (repaired this pass, informational)

Two distinct causes, both now understood and repaired:

1. This session's own DR-20/CR-127(orig. CR-123)/NP-D4B-007 doctrine entries were first committed
   only on the incident branch itself (`wave/D-4b/B1-full-rerun`), which — correctly, by design —
   never merges (it stays QUARANTINED, permanently, as evidence). That meant those entries never
   actually reached `main`. This pass re-lands them under fresh numbers (`CR-122`/`CR-123` having
   since been independently claimed by a concurrent, unrelated campaign's own work before this
   campaign's entries arrived) — no content lost, fully cross-referenced.
2. A separate, unrelated, concurrently-active campaign's own merge accidentally swept up this
   campaign's staged `STATE_D4B.md`/`REPORT_D4B.md` changes from a shared working directory; that
   campaign correctly identified the contamination and reverted it (commit `d1c375d2`), but the
   revert rolled back further than intended, incidentally erasing this campaign's own legitimate
   PR #708 content too. This pass restores it.

**No data was permanently lost** — reconstructed in full from this session's own record. Recorded
as `NP-D4B-008` for native awareness; flagged as a process pattern worth a coordination convention
if it recurs (doctrine-wave prose artifacts + a shared working directory + two active writers).

## §5 — DR ratification sweep

DR-6 through DR-16: unaffected. DR-17/18: ratified in substance, no formal register row yet (open,
unchanged, not blocking). **DR-19: ratified, holding, exercised again this pass.** **DR-20:
ratified AND discharged this pass** — built, verified twice, proven live. **DR-12 (DIS.025):
ratified 2026-07-17, discharged this pass** — B-1's clean NO_WINNER is the campaign's first
legitimate scored comparison.

NP-D4B ledger: 001–006 unchanged status from prior passes. **007: outcome recorded** (the
quarantine's pre-committed next step — a clean re-run — materialized exactly as the ruling
anticipated). **008: new, process findings, native review requested** (informational on the
content-loss incident; a real decision needed on CR-128).

## §6 — Register final sweep

`DISAGREEMENT_REGISTER_v1_0.md`: DIS.031 (DR-20) added. `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`
v3.13: CR-126/127 (closed, proven) and CR-128 (open, native decision required) added, with an
explicit re-landing/renumbering note for the CR-122/123 collision. `CAPABILITY_MANIFEST.json`: not
touched, no drift. `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md`: no new open directive.

## §7 — Three-point baseline diff

**Still not run.** Its precondition (a completed calibration loop — B-1 through B-3 genuinely
merged) is now half-met for the first time (B-1 merged) but B-2/B-3 remain blocked on CR-128. Not
a new gap — the same one every prior GATED pass has honestly reported, now one lane closer.

## §8 — Standing live loop

Unaffected. The prospective-prediction ledger remains the campaign's real forward test and stays
open independent of B-1/B-2's internal state.

## §9 — Next action (binding)

1. **Native/Binder decision on CR-128**: repair the `phala_anchors`/`update_calibration()` schema
   mismatch to wire a genuine pipeline, or build the write surface `mimamsa_outcome_record`
   actually described, since neither currently exists.
2. Once that surface exists, B-2 can honestly simulate then execute its backfill (against
   `pratyantar_lord`, `model_confidence: none_validated`, per B-1's honest no-winner branch).
3. Then B-3 → a real, FULL-mode B-6 close: full DR sweep, the three-point baseline diff, `current_wave` → `CAMPAIGN-CLOSED` if everything genuinely merges.
4. **B-1 itself needs no further action.** Its result is final, clean, and merged.

---

*REPORT_D4B, B-6 pass #6 (GATED). Supersedes PR #695/#703/#708 (merged, preserved in history).*
