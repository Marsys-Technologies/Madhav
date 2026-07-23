---
artifact: REPORT_D4B
type: WAVE CLOSE REPORT (protocol §7) — CAMPAIGN CLOSE (supersedes B-6 passes #1-#6, PR #695/
  #703/#708/#717, all merged and preserved in history)
wave: D-4b — Calibration Ignition + Grand Bakeoff
status: CLOSED. Headline: B-1 (the Grand Bakeoff) is DONE, genuinely, cleanly, merged (PR #712) —
  an honest, adversarially-verified NO_WINNER. B-2/B-3 (calibration ignition) close HONESTLY-
  DEFERRED by native ruling (CR-128, 2026-07-23) — not blocked-pending-fix, but the campaign's own
  designed honest terminus: there is nothing legitimate to backfill against a model the retrospective
  test itself found unvalidated. The standing live loop is declared the primary path forward. B-6's
  three-point baseline diff is produced and included below.
authored_by: Orchestrating session, directly (not agent-dispatched).
---

# REPORT_D4B — Campaign Close

## §0 — Headline and native ruling (verbatim disposition)

**B-1 is done.** After three prior attempts (blocked / VOID-narrowed / quarantined-for-sealed-
split-breach), a fourth attempt — chunked, checkpointed, on a harness structurally guarded against
the exact defect that quarantined attempt #3 — ran clean, was independently verified twice over,
and merged as **PR #712**. The result is an honest **NO_WINNER**: no contender clears its control
with statistical distinguishability.

**B-1's NO_WINNER, and the missing write-surface (CR-128), reached the same conclusion from two
directions — and the native ruled on that convergence.** The full ruling, recorded verbatim for
the record:

> Native ruling — CR-128: do NOT build/repair the calibration write-surface now. Close D-4b
> honestly with calibration DEFERRED to the prospective regime. This is the campaign close.
>
> The reasoning, on the record: B-1 returned NO_WINNER — no contender beat its control, and the
> one apparent signal was a verified outlier artifact. Per the pre-committed no-winner branch,
> B-2's backfill would write `model_confidence: none_validated` rows: calibrating against a model
> the data itself says isn't validated, from N≈40 design-time-exposed events. There is nothing
> legitimate to backfill. CR-128 (the missing write-surface) is therefore not a blocker to fix —
> it's a surface we correctly should not use yet. Building it now to write meaningless rows would
> be the exact fabrication this campaign exists to refuse. The gap and the no-winner agree:
> retrodiction cannot ignite calibration on this corpus.
>
> **Campaign verdict (verbatim):** "No validated timing model on the sealed retrospective corpus
> (NO_WINNER, adversarially verified). Calibration ignition is deferred to the prospective regime —
> the standing live loop is the path. The retrospective test ran clean and reported honestly that
> it lacks sufficient validated signal to calibrate." This IS the pre-committed no-winner outcome;
> the campaign reaches its designed honest terminus.

## §1 — B-1: the full history, condensed

| # | What | Result |
|---|---|---|
| 1 | Original 5-contender attempt (PR #687) | BLOCKED — 4/5 contenders had no real implementation. Honest, no fabrication. |
| 2 | Narrowed 14-contender / 31-event run, pre-fix (PR #694) | VOID — 433 negative CRPS values (proved F-2 was needed). |
| 3 | Full chunked re-run, post-F1/F2, pre-CR-127 | **QUARANTINED** — scored the sealed test split across all 14 contenders. Every number VOID. Caught by the final anti-gaming pass, three verification altitudes downstream of where it originated. |
| 4 | CR-127/DR-20 fix (PR #709) | The structural fix itself — `sealed_split_guard.ts` wired into the harness's one universal scoring entry point. Not a re-run. |
| 5 | Clean chunked re-run (PR #712) | **MERGED. FINAL.** Zero sealed-split touches (independently re-confirmed by a from-scratch cross-reference check). DR-12 NO_WINNER, honestly grounded — the campaign's own headline result. |

**Attempt #5's adjudication, in detail:** `pratyantar_lord` was the only contender with adequate
coverage (n=31 of 56 TRAIN-scope events). Its raw aggregate skill (+0.1058) looks like a win — but
the anti-gaming verifier's own adversarial statistical re-derivation found this is a **single-
outlier artifact**: one event (`EVT.2002.XX.XX.01`, real CRPS 268.9 vs control 603.9) contributes
+335.1 of the total +141.7 skill-relevant sum — 236% of it. Excluding that one event, the model
**loses** on 27 of the remaining 31 events (exact binomial sign test p=3.40e-05; Wilcoxon one-
sided p=6.85e-04). Every other contender (all 12 PERMISSION systems + the ensemble) scored only
n=2 events each — structurally too thin for any sign test to mean anything (max possible p-value
0.5–1.0). **No contender clears DR-15(b). NO_WINNER is the honest, adversarially-checked
adjudication, and it is now the campaign's final, standing result.**

## §2 — What made attempt #5 different: DR-20 and CR-126/127

Two consecutive unchunked full-scoring dispatches had crashed with zero committed progress before
this campaign adopted checkpointed batching (**CR-126**, closed, proven twice — once on the
breached run, once on the clean one, both completing all 3 batches + assembly cleanly; **promoted
this pass to the standing per-release regression suite** — see promise ledger). Separately, the
breach itself produced **DR-20** (`DISAGREEMENT_REGISTER_v1_0.md` DIS.031): *"a train/test seal is
enforced at the query/data layer... never by agent instruction alone."* Its fix, **CR-127**
(`sealed_split_guard.ts`, PR #709), is wired as the first statement in the harness's single
universal scoring funnel — no driver or contender type can bypass it by construction. Verified
independently twice: once by a fresh-context Opus reviewer (including an adversarial millisecond-
precision boundary test not in the original PR), once live by attempt #5's own anti-gaming pass,
which wrote its own independent date cross-reference (not reusing the guard's code path) and
confirmed the exact prior-breach signature — the 2025 marriage event, the 20 post-2020
`pratyantar_lord` scores — is provably absent this time.

## §3 — B-2/B-3: CLOSED, HONESTLY-DEFERRED (not fixed, not blocked)

The B-2 dispatch, before writing anything, traced `mimamsa_outcome_record` (B-2's stated write
target per `BRIEF_D4B.md` §1) end to end and found it does not exist — no table, no live write
path, confirmed by direct `pg_tables`/migration-grep queries. Three real, distinct candidate
surfaces were investigated and none is the described batch-backfill target: `mcp_prediction_outcomes`
(exists, empty, scoped to one prediction at a time); `mimamsa_multipliers`/`mi_gunanaka` (real
asset, 9 rows for this chart, all `n_observations=0`) whose posteriors depend on
`mimamsa_calibration` (0 rows), populated by `update_calibration()`, which references
`phala_anchors.prediction_state` — a column that does not exist on the live `phala_anchors` table
(37 real columns enumerated, none by that name) — dead code against the current schema; and the
B-1 harness itself, which produces JSON artifacts only, no DB write path anywhere in that tree.
Full detail: `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-128.

**The native ruling above resolves the fork this gap created.** Per §0: repairing or building the
write-surface now would let B-2 write real-looking rows carrying `model_confidence: none_validated`
against a model B-1 itself found has no validated skill, sourced from ~40 events all exposed to the
retrodiction contenders at design time. That is not calibration — it is exactly the fabrication
this campaign's own discipline (B.10, DR-16, DR-19, DR-20) exists to refuse. **B-2/B-3 therefore
close HONESTLY-DEFERRED, not blocked-pending-fix.** CR-128 stays **OPEN as a named future-work
item** — not a D-4b blocker — with disposition text: *"calibration write-surface unbuilt;
`update_calibration()` dead-code references dropped `phala_anchors.prediction_state`."* It is
built when there is real data to write it from — when the prospective ledger has accrued enough
forward-scored, genuinely-unseen outcomes to calibrate against. Its natural home is a small
pre-work lane before whichever future wave first has that data, or folded into D-6. Whether to
repair the old `phala_anchors` pipeline or build fresh is decided THEN, against real requirements,
not now against a dead one.

## §4 — Process incident: cross-campaign content loss + CR-numbering collisions (informational)

Two distinct content-loss causes, both understood and repaired in the B-6 pass #6 lane, carried
forward here for the permanent record:

1. This session's own DR-20/CR-127(orig. CR-123)/NP-D4B-007 doctrine entries were first committed
   only on the incident branch itself (`wave/D-4b/B1-full-rerun`), which — correctly, by design —
   never merges (it stays QUARANTINED permanently, as evidence). Those entries never reached
   `main` until pass #6 re-landed them under fresh numbers.
2. A separate, unrelated, concurrently-active campaign's own merge accidentally swept up this
   campaign's staged `STATE_D4B.md`/`REPORT_D4B.md` changes from a shared working directory; that
   campaign correctly identified the contamination and reverted it (commit `d1c375d2`), but the
   revert rolled back further than intended, incidentally erasing this campaign's own legitimate
   PR #708 content too. Repaired in pass #6.

**A separate, distinct finding — CR-number collisions, twice.** This campaign's original CR-122/
123 collided with a concurrent RC-04 campaign's own CR-122/123/124 (renumbered to CR-125/126/127).
Before that renumbering even reached `main`, a second concurrent campaign (RC-02/RC-17) independently
claimed CR-125 and merged it first, requiring a real git merge-conflict resolution (not just
renumbering) across the register and every cross-referencing doctrine file. Final numbers: CR-126
(batching), CR-127 (seal fix), CR-128 (B-2 gap).

**Native-directed process/hygiene finding, recorded here per the campaign-close ruling:** two
concurrent campaigns sharing one register namespace (`MARSYS_DEFECT_GAP_REGISTER_v2_0.md`) need a
coordination convention — reserved numeric ranges per active campaign, or a claim/lock file — for
whoever runs the next concurrent waves. No data was permanently lost either time; both incidents
were caught and repaired within the campaign that discovered them.

## §5 — DR ratification sweep (full, through DR-20)

DR-6 through DR-16: unaffected by this campaign, no change. DR-17 (grading weights)/DR-18: ratified
in substance via the DR-17 grading module (PR #704), no formal register row needed — exercised live
in the clean B-1 re-run, open but unchanged, not blocking. **DR-19** (an open is a repo state, not
a message — DIS.030): ratified, holding, exercised repeatedly across the campaign, most recently by
B-2's own DEFERRED (not silently-closed) disposition this pass. **DR-20** (train/test seal enforced
structurally — DIS.031): ratified 2026-07-22, **discharged** — built (CR-127/PR #709), verified
twice, proven live by the clean re-run. **DR-12** (D-4 peak-model adjudication hook — DIS.025):
ratified 2026-07-17, **discharged this campaign** — B-1's clean NO_WINNER (PR #712) is the
campaign's first, and final, legitimate scored comparison; it is now the standing headline result.

## §6 — Native-Proxy ledger (compiled for ratification)

NP-D4B-001 through 006: unchanged status from prior passes, no new developments this close.
**NP-D4B-007**: the sealed-split breach ruling — QUARANTINE in full, structural fix, one clean
re-run — **fully discharged**: the clean re-run materialized exactly as the ruling's pre-committed
outcome anticipated (NO_WINNER, honestly). **NP-D4B-008**: process findings (content loss,
informational; CR-128 architecture gap, native review requested) — **item 2 now resolved** by this
close's native ruling (§0 above); item 1 remains informational, folded into §4's hygiene finding.
**NP-D4B-009** (new, this close — see `NATIVE_PROXY_LEDGER_D4B.md` for full text): records the
CR-128 defer-don't-build ruling itself as the campaign's final Native-Proxy entry, closing the
ledger's open item.

Full ledger content: `NATIVE_PROXY_LEDGER_D4B.md`.

## §7 — Three-point baseline diff: pre-D-2 → post-D-2 → post-campaign wealth reading

**Protocol:** `BASELINE_WEALTH_READING_PRE_D2_v1_0.md` §4, seven comparison axes, against the
sealed question *"Full financial analysis of 482012f1: when does the wealth promise activate, and
what intervention secures or advances it?"* — served live this pass via `judgment_query`
(domain=wealth, v3), `get_dashas`, `kala_windows_get` (domain=wealth), and `bodha_remedies_get`
(domain=wealth) against chart `482012f1-710e-4a25-994a-93821f5871aa`.

**Honest disclosure, made once and governing the whole section:** no post-D-2 checkpoint reading
was ever produced by any prior wave — a repo-wide search this pass found none. This diff is
genuinely two points (pre-D-2 baseline → post-campaign), not three, with the missing middle
honestly reported rather than fabricated to satisfy the instruction's three-point framing.

| Axis | Pre-D-2 baseline (`BASELINE_WEALTH_READING_PRE_D2_v1_0.md`) | Post-D-2 | Post-campaign (this pass, live) |
|---|---|---|---|
| 1. Served vs. hand-assembled activation date | No forward dasha projection served; activation date hand-assembled from the dasha table | **not produced — gap, disclosed** | **Still hand-assembled, unchanged.** `kala_windows_get(domain=wealth)` returns `forward_window_count: 0` for the current query horizon — no dated Venus-MD-era forward window is served. The tool returns the CURRENT window (Mercury MD/Saturn AD, 2024-12-08 → 2027-08-18) correctly, but nothing forward. This is an honest, unchanged gap. |
| 2. Venus-MD forward window w/ NBRY-deferral sub-timing | Absent — baseline's own §4 names this as a gap | **not produced — gap, disclosed** | **Still absent, unchanged.** Same root cause as axis 1: no forward-window materialization beyond the current dasha period is served by `kala_windows_get` at this query scope. |
| 3. Mechanism-named evidence | Baseline's own §4: no mechanism object | **not produced — gap, disclosed** | **Improved.** `judgment_query` v3 now returns a live `affliction_mechanisms` array: `{"mechanism_name":"Rahu occupies dhana (2nd) bhāva (mixed)", "mechanism_class":"graha_bhava_affliction", "valence":"mixed", "citation_human":"Rahu (Taurus) tenants the dhana (2nd) bhāva — valence mixed (net -0.50); natural -1.0, dignity +0.50"}` — a named, cited mechanism object where baseline had none. |
| 4. Receipt completeness | Baseline's own §4: no completeness receipt | **not produced — gap, disclosed** | **Improved.** Full receipt served: `{bhava:true, bhavesha:true, karaka:true, from_moon:true, varga_confirmed:"D2✓", varga_weighted_into_verdict:true, yogas_checked:12, bhanga_checked:true, timing_anchored:true}`. |
| 5. Suppression-adjusted windows | Not modeled at baseline | **not produced — gap, disclosed** | **Unchanged — still not modeled.** No suppression-adjustment field found in the live `judgment_query`/`kala_windows_get` payloads this pass; not investigated further beyond confirming absence (out of scope for a close pass to build). |
| 6. Retrodictive confirmation section | Baseline: wealth phala anchors = 0, no retrodictive confirmation | **not produced — gap, disclosed** | **Not resolvable this pass — tool-name residual, disclosed.** No `mechanism_retrodiction_get` tool resolves live on the connected MCP surface (confirmed via direct tool search, zero matches) despite B-5 (PR #688) having merged retrodiction-adjacent work under this campaign. This is recorded as a naming/registration residual for B-5's surface, not chased further in a close pass — see STATE_D4B.md B-5 lane note. |
| 7. Remedy leverage_index join | Not modeled at baseline (no `bo_upaya` join existed yet) | **not produced — gap, disclosed** | **Confirmed still empty — for a documented reason, not a new gap.** `bodha_remedies_get(domain=wealth)` returns `resonance_count: 0, prescription_count: 0` with an explicit `data_gap_note`: `bo_upaya`'s `associated_doshas_array` and `estimated_cost_inr_range_jsonb` are 100% NULL for every chart built so far (writer-level gap, not a serving-layer drop). No `leverage_index` field is present in the response at all — the join axis 7 asks about does not yet exist as a served field, distinct from the wealth-domain resonance rows themselves being empty. |
| Composite score | `convergent_moderate`, 2.38 (d1_score 1.15 + yoga_term 1.23), 3 domain-bearing firings of 12 | — | **Unchanged.** `judgment_query` returns the identical `verdict_grade: convergent_moderate`, `composite_score: 2.38`, and the same 3 domain-bearing yoga firings (`dhana_yoga_2_5_9_11`, `dhana_yoga_house_lords`, `raja_yoga_kendra_trikona`, all strength 1.0218). |
| Epistemic grade | Not fielded at baseline (pre-dates the v3 envelope's epistemic block) | — | `epistemic: {grade: "structural_prior", verified_fraction: null}` — served honestly. This is the exact disclosure pattern the campaign-close ruling requires elsewhere (never blocked, never faked): the verdict renders in full, and its calibration state is labeled structural_prior rather than presented as empirically validated. **This live finding independently corroborates §0's calibration-deferred disposition** — the serving layer already reports honestly what B-1/CR-128 concluded architecturally. |

**Summary judgment:** the campaign's work on this domain landed in mechanism transparency and
receipt completeness (axes 3–4, genuinely improved) and in honestly surfacing rather than hiding
two further gaps (axis 6's tool-naming residual, axis 7's missing `leverage_index` field beyond the
already-known empty-resonance state) — not in the domain's headline composite score, which is
identical to baseline, nor in forward-window serving (axes 1–2, unchanged), nor in suppression
modeling (axis 5, unchanged). No component was blocked or faked to produce this diff; every gap
above is disclosed as a gap, per the native ruling's explicit instruction.

## §8 — Standing live loop: declared OPEN, PRIMARY path

The prospective-prediction ledger is no longer a footnote — it is now the campaign's stated primary
path to calibration. Every reading files falsifier-bearing predictions; forward outcomes accrue
toward the eventual honest calibration CR-128 will serve once there is real data to write from.

## §9 — Master battery → standing regression suite

The B-1 checkpointed-batching pattern (CR-126) and the full 14-contender scoring battery
(`B1_RUN_MANIFEST_v2_0.json`, `sealed_split_guard.ts`, `b1_batch_artifact_io.ts`) are promoted this
pass to the standing per-release regression suite — any future change to the scoring harness,
curve controls, or PERMISSION-bridge adapters re-runs this battery before merge. See promise
ledger for the binding commitment.

## §10 — Register final sweep

`DISAGREEMENT_REGISTER_v1_0.md`: DIS.031 (DR-20) present, discharged, no new entries this close.
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md`: CR-128 disposition text updated to HONESTLY-DEFERRED future-
work framing (this pass). `CAPABILITY_MANIFEST.json`: not touched, no drift.
`NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md`: no new open directive. `BRIEF_D4B.md`: status → CLOSED.
`CLAUDECODE_BRIEF.md`: `current_wave` → CAMPAIGN-CLOSED. D-6: staged ratification-ready —
`GOCHARA_SWEEP_2_0_DESIGN_v1_0.md` exists as an untracked draft in the doctrine_waves briefs
directory at this pass's start; native review recommended before D-6 formally opens (not a D-4b
blocker, not touched by this close).

## §11 — Campaign close

**D-4b is CAMPAIGN-CLOSED.** B-1: DONE, final, NO_WINNER. B-2/B-3: HONESTLY-DEFERRED per native
ruling. B-4/B-5/F-1/F-2/permission-bridge: merged, unchanged, standing. B-6: REAL close delivered —
three-point (honestly two-point) baseline diff produced. DR-6 through DR-20: swept. Native-Proxy
ledger: compiled, NP-D4B-009 added, submitted for ratification. Registers sealed through CR-128.
The master battery is now the standing regression suite. The standing live loop is OPEN and
primary. Cross-campaign collision process finding recorded as a named hygiene item.

---

*REPORT_D4B — CAMPAIGN CLOSE. Supersedes B-6 passes #1-#6 (PR #695/#703/#708/#717, all merged,
preserved in history).*
