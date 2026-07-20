---
artifact: PG2_DIAGNOSTIC_REPORT
canonical_id: PG2_DIAGNOSTIC_REPORT
version: 1.0
status: CURRENT — PG-2 diagnostic-wave synthesis report
verified_against_tree: 2026-07-19 (pg2/wave, base origin/main @ 4b69df8c; 44 canonical findings, all 6 lanes ACCEPT by the verification floor)
authored_by: Lane Z-2 (SYNTHESIS), PG-2 Diagnostic Wave — Claude Code (Opus 4.8, 1M)
supersedes: none (new artifact; corrects and completes the open items PG-1 left)
purpose: >
  The consolidated verdict of the PG-2 diagnostic wave. PG-1 (the Paripraśna
  Grounding Audit) was read-only and, by design, left a set of high-consequence
  questions undiagnosed — most sharply the chart_facts row-count divergence and
  whether the chat engine actually works when invoked. PG-2 ran six lanes (five
  diagnostic X-lanes + one meta-audit M-lane) to close those questions with
  root-cause depth, plus a full integrity re-audit of PG-1's own sealed gate.
  This document reports, per open question: the resolution, the root cause, the
  residual unknown, and the recommended action — and reproduces, unsoftened, the
  two headline final-answers (chart_facts, chat engine), M-1's VALID verdict on
  PG-1's gate, OT-11's costed fork, the X-3 coverage numbers, and a
  severity-ranked table of all 44 findings.
governing_inputs:
  - 00_ARCHITECTURE/pg2_diagnostic/deliverables/pg2_findings.jsonl (44 findings)
  - 00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_{X-1,X-2,X-3,X-4,X-5,M-1}.md (6 lanes)
  - 00_ARCHITECTURE/pg2_diagnostic/state/VERIFICATION_RECEIPTS.md (6/6 ACCEPT)
  - 00_ARCHITECTURE/pg2_diagnostic/BIND_PG-2.md (BIND-time observations)
  - 00_ARCHITECTURE/pg1_audit/REPORT_PG-1.md, PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md (the PG-1 artifacts this wave corrects)
---

# PG-2 Diagnostic Wave — Report

The PG-1 grounding audit closed GATE GREEN but was strictly read-only. It surfaced
several high-consequence items it could not diagnose and one procedural item
(`CURRENT_STATE` update) it could not complete. PG-2 was chartered to close those
items with root-cause depth. Six lanes ran; **all 6 verified ACCEPT** (see
`VERIFICATION_RECEIPTS.md`); **44 canonical findings** were filed
(`pg2_findings.jsonl`). This report synthesizes them, one section per open question.

> **Reading contract.** Every claim here is sourced to a PG-2 finding id
> (`PG2-X1-0001` …) or a cited PG-1 artifact line. Nothing is asserted from memory.
> This document is descriptive; it authorizes no code change. Where PG-2 resolves a
> PG-1 claim it does so in place, with PG-1's original claim quoted, never erased.

---

## §0 — The two headline answers, stated once, plainly

Two questions dominated this wave. Both now have a definitive, code- or DB-confirmed
answer, quoted verbatim from the lane that established it (gate-critical, G.1/G.2/G.3):

**Q1 — `chart_facts` divergence (F-25u).** X-1's own final-proof statement:

> "**Scope-labeling mismatch, not a data bug.** 27,554 = legacy v1.0
> single-ayanamsha-equivalent / pre-enrichment figure; 138,519 = correct
> all-ayanamsha total for ONE fully-built chart (5 ayanamsha partitions of ~27,677
> rows each + 135 ayanamsha-invariant rows); 276,206 = correct total across the TWO
> built charts (138,519 Abhisek + 137,687 Abhinandan). Divergence is the
> ayanamsha-partition multiplication (H1) compounded with documented post-v1.0
> enrichment … Zero duplicate fact_ids; zero natural keys span >1 build_id."
> — `PG2-X1-0001`

**RESOLVED BENIGN.** There is no idempotency, conflation, or accretion bug. See §1.

**Q2 — Does the chat engine work when actually invoked?** X-2's own final-proof
statement:

> "The deployed `/api/chat/consult` engine authenticates and plans correctly but
> **FAILS DETERMINISTICALLY with HTTP 500 at bundle hydration on EVERY request,
> before any synthesis or streaming.** Cause: `platform/src/lib/bundle/bundle_hydrator.ts`
> line 25 hard-codes `FLOOR_ASSET_IDS = ['FORENSIC','CGM']` and line 96 throws
> `bundle_hydrator: floor asset '<id>' not found in manifest` when a mandatory floor
> asset is absent from `CAPABILITY_MANIFEST.json`. The FORENSIC asset was DELETED
> from the manifest in PR #187 Legacy Teardown … so `hydrateBundle` throws … and the
> outer catch … returns HTTP 500."
> — `PG2-X2-0001`

**NO — the chat engine does not work.** It is the first real serving-path datum this
project has ever had, and the answer is a specific, code-confirmed, one-line-to-fix
regression, not a mystery. See §2.

---

## §1 — `chart_facts` +402% divergence (F-25u) — RESOLVED BENIGN

**PG-1's open question** (`F-25u`, high, undiagnosed): "*A sealed closure figure and
the live table disagree by 5×*," with the number "*itself unstable across probes.*"
PG-1 offered two open alternatives — "*either legitimate post-closure enrichment or an
idempotency/duplication defect*" — and, being read-only, diagnosed neither.

**Resolution (X-1, six hypotheses all resolved):**

| Hypothesis | Verdict | Basis |
|---|---|---|
| H1 — per-ayanamsha multiplication (native, 2026-07-12) | **CONFIRMED** (principal cause) | `GROUP BY ayanamsha_id` returns exactly 5 real ayanamshas (raman 27,735 · true_chitra 27,691 · krishnamurti 27,670 · lahiri_chitrapaksha 27,670 · surya_siddhanta_classical 27,618) + a 135-row INVARIANT partition; 138,519 / 27,554 = 5.027 (`PG2-X1-0002`) |
| H2 — legitimate structural growth (REPORT_D-1.6:48) | **CONFIRMED** | `ga_structural` owns 98,554 of 138,519 rows (71%) via `fact_category_ownership`; count(*) = count(DISTINCT fact_id) = 138,519 → zero duplicates (`PG2-X1-0003`) |
| H3 — build_id accretion (accumulation bug) | **REFUTED** | 3 build_ids coexist for Abhisek but own **disjoint** natural-key sets; zero natural keys span >1 build_id — benign scope-limited-rebuild provenance under §N.3 (`PG2-X1-0004`) |
| H4 — chart conflation (276,206 vs 138,519) | **REFUTED** | Only 2 charts have rows; 138,519 (Abhisek) + 137,687 (Abhinandan) = 276,206 exactly (`PG2-X1-0005`) |
| H5 — active write / mid-rebuild read | **REFUTED** | `max(computed_at)` = 2026-07-17T18:58 — two days stale; no write during session (`PG2-X1-0006`) |
| H6 — non-determinism | **REFUTED** | Three spaced probes all returned 138,519, byte-identical (`PG2-X1-0006`) |

**Root cause.** `chart_facts` stores one full ~27,677-row fact set **per ayanamsha**
(5 partitions) plus a 135-row ayanamsha-invariant partition, so one fully-built chart
= **138,519 rows** — the correct all-ayanamsha total. The sealed **27,554 is a stale
v1.0 single-ayanamsha / pre-enrichment figure**; the live cockpit `count_sql` does not
filter by `ayanamsha_id`, so the canonical figure should be restated as the
all-ayanamsha 138,519.

**PG-1's "unstable across probes" claim was itself a category error.** X-1 confirmed
(and BIND_PG-2 §B-5 independently predicted) that PG-1 compared an **unfiltered
all-charts** count (276,206) against a **chart-scoped** count (138,519) — apples vs
oranges — and read the difference as intra-session instability. The three historical
numbers (135,645 / 138,279 / 138,519) are successive rebuild states across days, not
one query drifting.

**Residual unknown.** X-1 cannot measure the v1.0 build state directly, so cannot prove
whether 27,554 was literally a single-ayanamsha count or an early all-ayanamsha total
that later grew ~5× by enrichment. Either way the current all-ayanamsha total of
138,519 is correct and non-anomalous (`PG2-X1-0001`).

**Recommended action.** `L1_GANITA_CLOSURE_v2_0.md` (out of this session's write scope)
should express the canonical `chart_facts` figure as a per-chart **all-ayanamsha** total
of 138,519 (= 5 partitions ~27,677 each + 135 invariant), explicitly retiring the bare
27,554 as stale. The `§8.7 ±1%` health-tolerance check in the architecture doc must
baseline against the all-ayanamsha figure, not 27,554.

---

## §2 — Does the chat engine work? (T-9) — NO, code-confirmed

**PG-1's open state (`T-9`).** PG-1 could observe only `conversation_messages = 0` and
correctly refused to read "wired but 0 rows" as "works," leaving T-9 ambiguous between
"no traffic" and "silently broken."

**Resolution (X-2, live authenticated invocation).** X-2 performed the actual
authenticated invocation PG-1 could not, using the documented native login flow (gcloud
→ Firebase custom token → Identity Toolkit ID token → `/api/auth/session` cookie → POST
`/api/chat/consult`). Two live invocations against chart `482012f1` — real questions
("career outlook over the next year", "favourable periods for marriage") — both returned
**HTTP 500** with a byte-identical body:

```
{"error":{"code":"SYSTEM_INTERNAL","message":"An unexpected server error occurred.",
"retry":false,"detail":"bundle_hydrator: floor asset 'FORENSIC' not found in manifest"}}
```

3.5 minutes apart, with byte-identical Cloud Run server logs (`[consume:v2] pre-stream
error: bundle_hydrator: floor asset 'FORENSIC' not found in manifest`) — **steady-state,
not cold-start**. The content-type was `application/json`, never `text/event-stream`: no
SSE stream ever opened.

**Root cause.** `bundle_hydrator.ts:25` hard-codes `FLOOR_ASSET_IDS = ['FORENSIC','CGM']`
and throws at line 96 when a floor asset is absent from `CAPABILITY_MANIFEST.json`.
`FORENSIC` was deleted from the manifest in PR #187 Legacy Teardown (CLAUDE.md §B;
`grep -c FORENSIC CAPABILITY_MANIFEST.json` = 0) and was never removed from this
hardcoded list. `route.ts:689` calls `hydrateBundle`, the throw is caught at
`route.ts:1023-1027`, and `res.internal(msg)` returns the 500.

**This is the same failure CLASS as LCA-2, one stage downstream.** LCA-2 was the retired
`reports`-table regression in the consult path, fixed in `route.ts:306-316`; that fix
unblocked the request far enough to hit the **next** retired-legacy relic
(`FORENSIC`) at `bundle_hydrator`. It is a **NEW, distinct regression** — same class,
different file/asset — not a recurrence.

**Why the prediction detector never fires — resolved.** X-2 also confirmed the partial
DB write behaviour on failure: after the two failed calls, `conversations = +2` (orphaned
rows from the eager insert at `route.ts:375`, both **KEPT** per the wave's fence rules —
ids `14d96091-4038-461e-9a21-1e822bbe7555` and `3829624c-ff9f-4e19-96ba-4f10d87c03a0`),
`llm_call_log = +2` (planner ran and succeeded), but `conversation_messages = 0` and
`mcp_predictions = 0` — because `writeConversationMessages` and the `mcp_predictions`
detector both run in `onFinish`, which is **structurally unreachable** past the
`hydrateBundle` throw. So `PG1-D3-0002`'s "detector never fires" is resolved: the detector
is wired correctly but every request dies upstream of `onFinish` (`PG2-X2-0001`).

**§J is NOT graded this wave — honestly noted, not skipped.** The wave's G.4 charge
was to grade a real reading against CLAUDE.md §J. **No reading was ever produced** — the
engine 500s before synthesis — so there is no reading to grade. `conversation_messages`
remains 0 all-time. §J therefore stands exactly where PG-1's Q-1 left it:
**ASPIRATIONAL and UNPROVEN**, now with the added, concrete knowledge that the
serving path is hard-blocked at a named line.

**Residual unknown.** Whether removing `'FORENSIC'` from `FLOOR_ASSET_IDS` yields a clean
reading or exposes a **third** retired relic downstream cannot be known read-only.

**Recommended action.** One-line fix candidate: drop `'FORENSIC'` from `FLOOR_ASSET_IDS`
(leaving `CGM`, which resolves in the manifest) — the direct analogue of the LCA-2 fix
(remove the retired-relic reference, do not resurrect the asset). Add a
manifest-vs-`FLOOR_ASSET_IDS` CI assertion so a retired floor asset fails the build, not
production request #1. This is cheap and separable from the expensive C-2 shim work
(see §7).

---

## §3 — Prior-work citation (G.2 charge): three documents

PG-1's `F-25u` called the divergence "undiagnosed," and BRIEF_PG-2 §0.2 flagged an
uncited-prior-work pattern. G.2 charges this report to cite and dispose of **both**
prior-work documents named in the brief, **plus** the third document M-1 newly surfaced:

| Document | What it already contained | PG-2 disposition |
|---|---|---|
| `llm_consumption_audit/REMEDIATION_RUN_LEDGER_v1_0.md:115` | `[OBS-1]`: the native's own 2026-07-12 per-ayanamsha hypothesis — "135,645 ≈ 27,554 × ~5 ayanamshas … Verify FIRST at W3 with `SELECT ayanamsha_id, COUNT(*) … GROUP BY`; if ~5 roughly-equal groups → hypothesis confirmed, benign." | **VINDICATED.** X-1 ran exactly that query and got exactly that shape (5 groups ~27,600–27,735 + INVARIANT). The hypothesis was correct and pre-registered; X-1 is its verification (`PG2-X1-0002`). |
| `llm_consumption_audit/briefs/doctrine_waves/REPORT_D-1.6.md:48` | The chart_facts growth (27,554→138,279) was "*investigated and confirmed legitimate (zero duplicate rows, clean build_id separation — `ga_structural`'s correct combinatorial output, not an accumulation bug).*" | **CONFIRMED & STRENGTHENED.** X-1's independent probe reproduces zero duplicates and attributes 71% of volume to `ga_structural`; the 138,279 endpoint is one rebuild state in the same series (`PG2-X1-0003`). |
| `ABHINANDAN_POST_REGEN_DATA_AUDIT_v1_0.md` (2026-06-28) — **newly surfaced by M-1** | Already reported `chart_facts` at 130,212 rows vs native 27,554, diagnosed the mechanism as "stale multi-build residue / idempotency violation," and specifically flagged native chart `482012f1` as carrying "5 distinct build_ids … stale multi-build residue persists. Flagged for a dedicated native hygiene session." | **RECONCILED — not a contradiction.** Both statements are true and compatible: multiple build_ids **do** exist on the native chart (X-1 found 3), **and** an earlier session flagged that multi-build state as worth investigating. What the ABHINANDAN audit framed as a suspected "idempotency violation" X-1 decisively resolves with the test the earlier audit did not run: **0 natural keys span >1 build_id**. So the build_ids are benign scope-limited-rebuild provenance under §N.3, not an accumulation bug. X-1's finding is the more complete, definitive resolution; the ABHINANDAN audit is the correct earlier partial diagnosis that should have been cited by PG-1's F-25u (`PG2-X1-0004`, `PG2-M1-0009`). |

M-1's own scope note (`PG2-M1-0009`): the uncited-prior-work pattern is **real on this
one high-consequence topic** but is **not** a pervasive lane-wide failure — spot-checks
of the NO-LEAKAGE and PITR findings found no genuine uncited prior art (the apparent
"leakage" repo hits are a different concept; the PITR hits were incidental substrings).

---

## §4 — M-1 meta-audit: PG-1's gate is VALID

M-1 re-audited PG-1's sealed gate adversarially, from a fresh context. Its topline
(`PG2-M1-0012`), reproduced faithfully and unsoftened:

> "**PG-1's gate result is VALID.** The single most consequential check (item 2, the
> G.1 addendum) came back fully clean: all 11 reconciliation rows are genuine
> back-fills of pre-existing narrative verdicts, causality provably ran forward
> (report sealed 06:56 in one immutable commit; addendum 07:04 touched only jsonl),
> and no report retro-edit occurred. Every integrity assertion (G.2/G.4/G.5/G.8/G.9)
> holds under independent re-derivation … 10/10 spot-verified findings hold …
> The defects I DID find … are correction-worthy hygiene/versioning defects, NONE of
> which voids the gate."

The wave's own verifier independently re-confirmed this VALID verdict (6/6 ACCEPT,
`VERIFICATION_RECEIPTS.md`). Six correction-worthy defects were found; **none voids the
gate** (PC-6/PC-7 — do not defend PG-1, do not overstate the defects):

1. **Finding-count / severity discrepancy** (`PG2-M1-0001`). The sealed
   `PARIPRASHNA_GROUNDING_AUDIT_REPORT` asserts "87 findings" in ≥4 places while the
   cited `pg1_findings.jsonl` has **98 lines** (87 primary lanes + 11 G.1
   reconciliation addendum). Separately, §3 states "critical | 5" but **6** critical
   findings exist (`D3-0004, Q1-0001, Q1-0007, Q1-0012, C2-0001, C2-0008` — two JSON
   serializations masked the count), and §3's own critical-row examples already
   enumerate all six. A B.8 versioning/hygiene defect, not an integrity failure.
   → corrected in the sealed artifacts, §6 below.
2. **G.1 addendum authenticity** (`PG2-M1-0002`). Independently proven genuine by
   commit-timestamp forward-causality: report commit `6336c218` (06:56, 435 insertions,
   one file, never modified after) precedes addendum commit `75b42b5a` (07:04, jsonl-only,
   +11 each). Backward-causality hypothesis definitively REFUTED. The 8 evidence-bearing
   rows quote the report's assumption table verbatim; the 3 empty rows are honestly
   `NOT AUDITED`. Not gate-voiding.
3. **Protocol deviations** (`PG2-M1-0003`). Shared checkout (one commit race), D-3's
   commit riding inside R-1's, branch cut from local `main`, mid-wave G.9 base change —
   all assessed as **hygiene / commit-boundary issues that do not compromise finding
   reliability**; all disclosed. The one real PR-contamination (unrelated commit
   `9c358819` in `pg1/wave` ancestry) is disclosed and predates PG-1's fork point;
   reconcile at #613 merge.
4. **10/10 spot-verified findings hold** (`PG2-M1-0004..0007`). The critical NO-LEAKAGE
   finding (`D3-0004`) is confirmed and, if anything, **understated** — only `amjis_app`
   exists, holding full CRUD+TRUNCATE on both `mimamsa_predictions` and
   `mimamsa_calibration`. Two enumerated `=0` claims (`conversations`, `llm_usage_events`)
   are now `=1` (immaterial post-audit temporal drift). `F-25u`'s "unstable" framing is
   confirmed imprecise (same root cause X-1 found).
5. **G.4 qualified-GREEN was sound** (`PG2-M1-0008`), not a laundered pass. The literal
   "observed behaviour for EVERY capability" text is unmet (~25% coverage), but the
   integrity property it protects — non-laundering of partial coverage as exhaustive —
   is satisfied: the 35/139 bound is disclosed repeatedly and routed to native
   disposition. (X-3 closes the coverage gap this wave — see §5.)
6. **Uncited prior work extends beyond chart_facts** (`PG2-M1-0009`) — see §3. Real on
   one topic, not pervasive.

No MEMO was needed and none was filed (`PG2-M1-0011`): no §2 halt-class event (RED
integrity gate / contested doctrine / circuit-breaker) occurred. Governance exit codes
reproduce exactly (`PG2-M1-0010`): `drift_detector.py` exit 3 / 219 findings,
`schema_validator.py` exit 3 / 35 violations, zero of which touch any PG-1 path.

**Verdict: GATE GREEN UPHELD.** The corrections are Z-2's corrective scope, applied in
§6, not gate-voiding.

---

## §5 — Capability coverage (X-3): ~96%, remaining gaps

X-3 executed **98 additional distinct tool names** beyond R-2's 35, bringing combined
coverage to **133 / 139 (~96%)** of the live MCP tool-name surface mechanically
exercised at least once (`PG2-X3-0010`). This closes the G.4 coverage gap PG-1 disclosed.

**Bearer-key 401 (F-25v) — RESOLVED, not broken auth** (`PG2-X3-0001`). A raw
`curl -X POST /mcp` with `Authorization: Bearer <correct key>` returned **HTTP 200 with
the full 139-tool `tools/list`** (both header casings, both hosts). A garbage key
reproduced PG-1's exact 401 byte-for-byte. Root cause: a **stale/wrong key value** at
PG-1's audit time (not a request-shape, host, or server-side auth regression). The exact
stale value is unrecoverable (`scripts/setup_mcp_env.sh` is gitignored and absent from
the isolated worktree).

**Both known-broken tools reconfirmed unchanged:** `phala_anchors_get` still 422s when
`date_range` is omitted (`PG2-X3-0002`); `ref_dignity_reference_get` still 400s on
`planet=Saturn`, on **both** charts — chart-independent code-path defect (`PG2-X3-0003`).

**New defects surfaced by the wider sweep:**

| Defect | Detail | Finding |
|---|---|---|
| `unknown_tool` drill degradation extends to the catalog family | `catalog_assets_all`/`catalog_assets_list` emit `recover_via.instrument: "unknown_tool"` — extends `PG1-R2-0001`'s class to the asset-registry alias family (systemic to a broader Phase-1 alias class) | `PG2-X3-0004` |
| `record_outcome` 500s on a bad id | A syntactically valid but non-existent `prediction_id` returns an unguarded sidecar HTTP 500 instead of a graceful 404 | `PG2-X3-0005` |
| `holistic_bundle_chart_facts` falsely reports "completed" | Returns `type: bundle.completed` while only 3/8 sub-tools fire (UCN/RM/CDLM); 5 silently error (MSR/CGM/LEL/PANCHANG/DASHA). A caller trusting it for B.11 whole-chart-read is silently missing 5/8 subsystems | `PG2-X3-0006` |
| Whole-chart tools exceed client token ceiling | `assess_career/health/marriage/wealth`, `get_temporal_windows` (289KB), `kala_temporal_bundle`, `get_domain_reading`, `ref_nakshatra_get` produce 92–289KB payloads too large for the client even after server-side trim — trimmer exemption or miscalibrated ceiling | `PG2-X3-0009` |
| v3-vs-legacy `judgment_flags` gating reconfirmed on 2nd chart | `PG1-R2-0007` confirmed systemic (Abhinandan), not an Abhisek data artifact | `PG2-X3-0007` |

**No cross-chart leakage** was found on the second-chart sweep (12 tools against
Abhinandan `1c826d5a` immediately after ~90 calls against Abhisek — every response
correctly scoped, `PG2-X3-0008`), corroborating the A2 chart-agnostic gate on a
broader, non-sentinel sample.

**Two tools remain genuinely unexercised** across PG-1+PG-2: `prashna_undertaking_get`
(needs a horary/prashna-cast chart; none of the 4 charts qualify) and
`mimamsa_outcome_record` (the alias twin of `record_outcome`, not re-probed once the
underlying handler's 500 was confirmed).

---

## §6 — Corrections applied to PG-1's sealed artifacts

Per the brief (D-18 discipline: append a marked correction block, do not rewrite
history), the following `[CORRECTED 2026-07-19 / PG-2]` blocks are added near each stale
count in the PG-1 sealed artifacts (the original numbers remain visible):

- `PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md` §3 (findings-by-severity) and body:
  finding count is **98** (87 primary + 11 reconciliation), critical count is **6** not 5
  (the §3 examples already list all six). Driver: `PG2-M1-0001`.
- `REPORT_PG-1.md` summary: the "87 evidenced findings" figure carries a correction note
  pointing to the 98-line jsonl it already discloses at L21.

These are B.8 versioning-hygiene corrections; they do not disturb the GATE GREEN verdict
(§4).

---

## §7 — OT-11: the prediction-ledger fork, fully costed (no choice made — PC-8)

X-5 established the landscape is **three** prediction-tracking tables, not the two OT-11
named (`PG2-X5-0006`): `mimamsa_predictions` (384 rows, build-time L5, referenced by
`mimamsa_calibration`), `mcp_predictions` (0 rows, chat-detector interim relay, migration
071, explicitly TODO-migrate), and `brahma_prospective_ledger` (5 rows, D-4a §11
explicit-filing). `record_outcome` writes to **neither** prediction ledger — and there
are **two same-sounding tools** targeting different tables: `record_outcome` →
`phala_anchors` + `mimamsa_calibration` (sidecar); `mimamsa_outcome_record` →
`mcp_predictions` (`PG2-X5-0005`). `mimamsa_predictions`' own lifecycle is transitioned
only by build-time `mi_abhilekha.py`.

**Neither table satisfies §14.3 without a schema change** (`PG2-X5-0004`): §14.3 mandates
a `message_part_id` FK to the exact utterance, a `created_from_channel` column, and an
8-state lifecycle enum — the three fields **no live table carries**. §14.3's own named
target (`brahma_mimamsa_prediction_ledger`) matches no live table.

**The two costed options (`PG2-X5-0007`), presented, not chosen:**

**Option A — merge into one canonical ledger.**
- Schema work: unify incompatible types (`chart_id` text→uuid backfill; `horizon`
  text→daterange parse; `confidence` text-enum→numeric so chat rows are Brier-scoreable);
  add the §14.3 columns neither has (`message_part_id` FK, `created_from_channel`, 8-state
  lifecycle enum); reconcile two disjoint id namespaces (`PH-4-1.*` vs `PPL.*`); fold in
  `brahma_prospective_ledger` and reconcile `phala_anchors` as `record_outcome`'s real target.
- Code rewrites: `mi_bhavisya`/`mi_abhilekha`/`mi_pramana`, `mimamsa_calibration` linkage,
  `query_predictions.ts`, `ppl_writer.ts`, `calibration_producer.ts`, **both**
  `record_outcome` surfaces, `assetClearSpec` count_sql.
- Migration risk is concentrated on `mimamsa_predictions` — the only populated (384) +
  referenced ledger and the sole thing L5 STRUCTURAL-mode calibration depends on;
  `mcp_predictions` data migration is trivial (0 rows) but its writer must be repointed.
  What breaks if done wrong: the `mimamsa_calibration` FK, the `mi_pramana` build step,
  the cockpit count, the §7.4 NO-LEAKAGE role that must name one table.

**Option B — keep all three + document the split.**
- No schema/migration risk. Ongoing cost is permanent reader confusion — `record_outcome`
  hits `phala_anchors`+`mimamsa_calibration` while `mimamsa_outcome_record` hits
  `mcp_predictions` and neither hits `mimamsa_predictions`; §7.4 `role_ledger_write`
  still cannot name one physical table.
- Documentation needed: a ledger-map declaring authority per table + `record_outcome`
  tool disambiguation.

**Is the split semantically justified? PARTIALLY-YES, as a fact.** Build-time analytical
predictions vs conversationally-surfaced live predictions is a principled provenance
distinction the architecture's own §14.1 endorses. But the as-built three-table state
tangles that one clean axis with two–three historical interim scaffolds (`mcp_predictions`
predates §14; `brahma_prospective_ledger` is a later third attempt), and §14.3's named
target matches none of them.

**The native-level canonical-ledger ruling is reserved (PC-8).** OT-11 stays an OPEN
fork in the architecture doc, now updated with this cost analysis.

**Separately surfaced runtime defect (not OT-11 core):** the sidecar `outcome.py`
SELECTs/UPDATEs `phala_anchors` columns absent from the live schema (`id`, `confidence`,
`prediction_state`, `outcome_note`, `outcome_recorded_at`, `updated_at` vs live
`anchor_id`, `confidence_low/high`, `posterior`, `computed_at`) — a runtime-breaking
schema drift the `record_outcome` sidecar would hit (`PG2-X5-0005`). Flagged for a
dedicated lane.

---

## §8 — Architecture-assumption closures (X-4)

All 8 X-4 items closed:

- **A-10 (provenance stamp)** `PG2-X4-0001`: a provenance-shaped stamp exists and is
  written per-turn, but lives in the **mutable** `conversation_messages.metadata_json`
  column via `ON CONFLICT DO UPDATE` — **not** the immutable append-only ledger D-16
  wants. No dedicated provenance table exists.
- **A-2 (chart_agnostic_gate)** `PG2-X4-0002`: confirmed **fail-closed** by source read —
  a `per_chart` capability with no `chart_id` returns `400 CHART_REQUIRED` before any
  handler, with no default-UUID substitution, backed by a second handler-level check and
  a FROZEN CI gate. No leak. (Residual: a true raw-HTTP-from-outside probe still needs a
  running server; code-read verdict, not yet live-observed.)
- **A-30/A-32 (calibration gating / disagreement capture)** `PG2-X4-0004`: F-25c
  confirmed a **genuine live stub** — the feedback endpoint's own header comment
  ("message_feedback table dropped in WS-0 … returns empty/ok stubs. TODO(ws-2)")
  self-documents the regression; POST discards, GET returns `[]`. Three superficially
  matching tables (`mcp_disagreements`, `school_disagreements`,
  `mimamsa_resonance_feedback`) are **not** the conversational A-32 surface. A-30 remains
  correctly out-of-scope, unverified.
- **A-08 (conversation store)** `PG2-X4-0005`: already fully closed within PG-1's D-1 lane
  — 7-column `conversation_messages`, no `message_parts` child table across 251 tables;
  re-confirmed live. A-13 was PG-1's mislabel for **A-08** (conversation migration).
- **A-14 (memoization / no-virtualization) — INVERTED from PG-1's assumption**
  `PG2-X4-0006`: PG-1's `PG1-Z1-A0001` left A-14 "unaudited" and **mislabelled it A-13**
  (A-13 is the unrelated three-region layout row). X-4 audited it: today's code is the
  **opposite** of A-14's target. The virtualizer A-14 says to remove
  (`VirtualizedMessageList.tsx`) IS live; **both** replacement techniques A-14 mandates are
  absent (`content-visibility` = 0 hits; frozen-block memoization = 0 hits). A real
  target-vs-actual gap, not merely an unaudited assumption.
- **Citation shape (S1-0003 / A-15)** `PG2-X4-0003`: citations live as a `CitationPart`
  data-part (`{type:'citation', signal_id:/^SIG\.MSR\.\d{3}$/}`) **inside `parts_json`**,
  not as `message_parts` child rows. PG-1's "no citations found" was a **DB-emptiness
  artifact** (`conversation_messages` = 0), **not** evidence of absence — the shape is
  confirmed by source; there is simply no traffic to sample.
- **A-31 (compliance decay)** `PG2-X4-0007`: confirmed **absent** — no batch-resolution /
  decay / lapse mechanism; `lifecycle_status` has no `lapsed`/`expired` state; no
  prediction cron. Was NOT AUDITED by PG-1; now confirmed not-built.
- **A-03/A-04/A-06/A-09 (`PG1-R1-0005/6/8/9`)** `PG2-X4-0008`: reclassified from
  "unverifiable" to **confirmed not-built** — `marsys_drill`, `mutation` field,
  `PlanReceipt`, `model_plane`/OpenRouter all return zero hits; target-state, zero
  scaffolding.

---

## §9 — Revised P0' estimate (Deliverable 5): C-2's 6–9 week analysis stands

X-2 never got a successful stream to observe — the engine 500s before streaming even
begins — so **C-2's analysis of the STREAMING PROTOCOL layer is unaffected**. C-2's core
finding (a translation shim cannot emit `turn.open` before the planner without a
`consult/route.ts` reorder; the full §19.7 gate is ~6–9 weeks, not 3–4 with an untouched
route) rests on the route/dispatch control-flow, which X-2 did not exercise and does not
change.

**What X-2 adds** is that there is now a **hard blocker BEFORE the streaming work even
matters**: `bundle_hydrator` 500s on every request. This is **good news, not bad**: the
blocker is a **one-line fix** (drop `'FORENSIC'` from a hardcoded array), it is
**separate from** the expensive C-2 shim work, and it is trivially cheap to unblock. The
correct reading is therefore a **sequencing note, not a revision** of C-2's estimate:

> P0' now has a ~1-line pre-requisite (fix `bundle_hydrator`'s stale `FORENSIC` floor
> asset) that must land before any streaming/shim work can even be observed end-to-end.
> Once unblocked, C-2's ~6–9 week estimate for the full §19.7 gate (with a bounded route
> reorder) stands unchanged. The render half remains cheap (Streamdown); the risk still
> lives in the SSE/route half.

No silent revision of C-2's numbers is made.

---

## §10 — Severity-ranked findings table (all 44)

Severity assigned by PG-2 synthesis from each finding's root-cause consequence (the
jsonl does not carry a per-row severity field for most). "Resolution" mirrors the
finding's own field.

| # | Finding | Lane | Resolves | Severity | Resolution |
|---|---|---|---|---|---|
| 1 | `PG2-X2-0001` — chat engine 500s at `bundle_hydrator` on every request (retired `FORENSIC` floor asset) | X-2 | T-9 | **critical** | refuted (engine does NOT work) |
| 2 | `PG2-M1-0004` — NO-LEAKAGE `D3-0004` holds, understated (only `amjis_app`, full CRUD+TRUNCATE) | M-1 | integrity item 4 | **critical** | resolved |
| 3 | `PG2-M1-0012` — PG-1 gate is VALID | M-1 | topline | **high** | resolved |
| 4 | `PG2-M1-0002` — G.1 addendum genuine (forward-causality proven) | M-1 | item 2 | **high** | resolved |
| 5 | `PG2-X1-0001` — chart_facts divergence resolved benign (scope-labeling) | X-1 | F-25u | **high** | resolved |
| 6 | `PG2-X3-0006` — `holistic_bundle_chart_facts` reports "completed" while 5/8 sub-tools error | X-3 | new defect | **high** | resolved |
| 7 | `PG2-X3-0003` — `ref_dignity_reference_get` 400 on Saturn, chart-independent | X-3 | PG1-R2-0003 | **high** | resolved |
| 8 | `PG2-X4-0006` — A-14 inverted: virtualizer live, both replacements absent | X-4 | PG1-Z1-A0001 | **high** | refuted (target gap) |
| 9 | `PG2-X5-0007` — OT-11 both options costed; neither table satisfies §14.3 | X-5 | OT-11 | **high** | resolved (no choice — PC-8) |
| 10 | `PG2-X5-0005` — `record_outcome` writes neither ledger; sidecar `outcome.py` schema drift | X-5 | OT-11 | **high** | resolved |
| 11 | `PG2-M1-0001` — 87-vs-98 finding count + 5-vs-6 critical severity in sealed report | M-1 | item 1 | medium | resolved |
| 12 | `PG2-M1-0009` — uncited prior work (ABHINANDAN audit) real on chart_facts, not pervasive | M-1 | item 6 | medium | partially_resolved |
| 13 | `PG2-X1-0002` — H1 per-ayanamsha CONFIRMED (5 partitions + invariant) | X-1 | F-25u | medium | resolved |
| 14 | `PG2-X1-0003` — H2 legitimate `ga_structural` growth (71%), zero dups | X-1 | F-25u | medium | resolved |
| 15 | `PG2-X1-0004` — H3 accretion REFUTED (0 natural keys span >1 build_id) | X-1 | F-25u | medium | refuted |
| 16 | `PG2-X1-0005` — H4 conflation REFUTED; "unstable across probes" a category error | X-1 | F-25u | medium | refuted |
| 17 | `PG2-X1-0006` — H5/H6 REFUTED; count deterministic, 2-day stale | X-1 | F-25u | low | refuted |
| 18 | `PG2-X2` (within `-0001`) — 2 orphaned `conversations` rows on pre-stream failure; detector structurally unreachable | X-2 | PG1-D3-0002 | medium | resolved |
| 19 | `PG2-X3-0001` — Bearer 401 (F-25v) = stale key, not broken auth | X-3 | F-25v | medium | refuted |
| 20 | `PG2-X3-0004` — `unknown_tool` drill degradation extends to catalog family | X-3 | PG1-R2-0001 | medium | resolved |
| 21 | `PG2-X3-0005` — `record_outcome` 500 on bad id (unguarded lookup) | X-3 | new defect | medium | resolved |
| 22 | `PG2-X3-0009` — whole-chart tools exceed client token ceiling (92–289KB) | X-3 | PG1-R2-0009 | medium | resolved |
| 23 | `PG2-X3-0002` — `phala_anchors_get` 422 reconfirmed unchanged | X-3 | PG1-R2-0002 | medium | resolved |
| 24 | `PG2-X4-0001` — A-10 provenance stamp exists but mutable, not immutable ledger | X-4 | PG1-R1-0010 | medium | partially_resolved |
| 25 | `PG2-X4-0004` — A-32 dispute capture confirmed genuinely stubbed (WS-0 TODO) | X-4 | PG1-S1-0004/5 | medium | resolved |
| 26 | `PG2-X5-0006` — three ledgers not two (`brahma_prospective_ledger` third) | X-5 | OT-11 | medium | resolved |
| 27 | `PG2-X5-0001` — full schema of both ledgers; thin conceptual overlap | X-5 | OT-11 | medium | resolved |
| 28 | `PG2-X5-0004` — neither table satisfies §14.3 (no message_part_id FK/channel/8-state) | X-5 | OT-11 | medium | resolved |
| 29 | `PG2-M1-0003` — protocol deviations are hygiene, compromise no finding | M-1 | item 3 | medium | resolved |
| 30 | `PG2-M1-0005` — DB-cluster spot-verify holds; 2 `=0`→`=1` temporal drift | M-1 | item 4 | medium | partially_resolved |
| 31 | `PG2-M1-0006` — F-25u "unstable" framing imprecise (same root cause as X-1) | M-1 | item 4 | medium | partially_resolved |
| 32 | `PG2-M1-0008` — G.4 qualified-GREEN was sound, not a gloss | M-1 | item 5 | medium | resolved |
| 33 | `PG2-X4-0003` — citation shape confirmed (data-part in parts_json); PG-1 "none" = DB-empty artifact | X-4 | PG1-S1-0003 | medium | resolved |
| 34 | `PG2-X4-0007` — A-31 compliance decay confirmed absent | X-4 | PG1-Z1-A0010 | medium | refuted |
| 35 | `PG2-X4-0008` — A-03/04/06/09 confirmed not-built (reclassified from unverifiable) | X-4 | PG1-R1-0005/6/8/9 | medium | resolved |
| 36 | `PG2-X4-0002` — chart_agnostic_gate fail-closed (400 CHART_REQUIRED, no leak) | X-4 | PG1-R2-0005 | medium | resolved |
| 37 | `PG2-X3-0010` — coverage 133/139 (~96%); 2 tools genuinely unexercised | X-3 | coverage | low | resolved |
| 38 | `PG2-X3-0007` — v3-vs-legacy `judgment_flags` gating reconfirmed on 2nd chart | X-3 | PG1-R2-0007 | low | resolved |
| 39 | `PG2-X3-0008` — no cross-chart leakage on 2nd-chart sweep | X-3 | PG1-R2-0004 | low | resolved |
| 40 | `PG2-X4-0005` — A-08 store confirmed (7-col, no message_parts); A-13 mislabel | X-4 | PG1-D1-0001 | low | resolved |
| 41 | `PG2-X5-0002` — writers disjoint (build-time vs serve-time), no table touched by both | X-5 | OT-11 | low | resolved |
| 42 | `PG2-X5-0003` — `phala_anchors` does NOT reference `mimamsa_predictions` (PG-1 inexact) | X-5 | PG1-D3-0003 | low | partially_resolved |
| 43 | `PG2-M1-0010` — governance exit codes reproduce (drift 219/exit3, schema 35/exit3) | M-1 | item 7 | low | resolved |
| 44 | `PG2-M1-0011` — no MEMO needed; no §2 halt-class event occurred | M-1 | item 8 | low | resolved |

**Roll-up:** 2 critical, 8 high, ~24 medium, ~10 low. Of 44: 34 `resolved`, 6 `refuted`
(as claims — i.e. the hypothesis/assumption was disproven), 4 `partially_resolved`. Zero
findings void PG-1's gate; the two most consequential are the chat-engine 500 (a cheap
unblock) and the NO-LEAKAGE confirmation (a native remediation call, unchanged from PG-1).

---

## §11 — What PG-2 leaves for the native

1. **Fix `bundle_hydrator`'s `FORENSIC` floor asset** (one line) — the cheapest,
   highest-leverage unblock the project has; nothing serving-path can be observed
   end-to-end until it lands (§2, §9).
2. **Rule on OT-11** (merge vs document; PC-8) — both options are now fully costed (§7).
3. **Rule on OT-12 / D-17 P0' scope** — unchanged from PG-1 (render-bet-descope vs full
   §19.7 gate at ~6–9wk); the `bundle_hydrator` fix is a prerequisite either way (§9).
4. **Restate the canonical `chart_facts` figure** as all-ayanamsha 138,519 in
   `L1_GANITA_CLOSURE_v2_0.md` (§1).
5. **NO-LEAKAGE posture** (F-25q, critical) — unchanged native call from PG-1; PG-2
   confirms it is if anything worse than stated (§4).
6. **Runtime schema-drift in the `record_outcome` sidecar** (`outcome.py` vs live
   `phala_anchors`) — a separate lane (§7).

*End of PG2_DIAGNOSTIC_REPORT v1.0 — PG-2 Lane Z-2, 2026-07-19.*
