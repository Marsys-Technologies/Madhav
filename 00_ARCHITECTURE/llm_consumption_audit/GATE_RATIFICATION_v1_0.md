---
artifact: GATE_RATIFICATION_v1_0
type: REVIEW_GATE_RECORD (plan §12.5.iii / §12 item 4)
version: 1.5  # v1.5 (2026-07-12): E-8 per-channel retrievability schema ratified. v1.4 (2026-07-12): E-7c — E-7b premise falsified (bench IS prod; prod lacks reports); consult lanes re-routed to MCP wire; LCA-2 upgraded CRITICAL; zero writes exercised. v1.3 (2026-07-12): E-7b refined ruling — reports recreated locally from archived DDL (deployed-parity rationale); code-fix option rejected to protect measurement integrity. v1.2 (2026-07-12): E-7 environment-provisioning ruling (local reports table + schema-parity diff) — native-approved via Cowork gate. v1.1: E-5 verification swarm (all lanes) + E-6 depth gate added per native directive
status: RATIFIED — execution is UNBLOCKED subject to the conditions in §3
reviewed_by: Fable 5 (Cowork) + native (Abhisek Mohanty), 2026-07-12
inputs_reviewed: TRACEABILITY_MATRIX.md v2.0 (line-by-line, incl. all 11 exceptions),
  FOUNDRY_CLOSE_REPORT.md v2.0, CHARTER.md §7 rubrics (full text), lane brief spot-checks
---

# Cowork Review Gate — Ratification Record

## §1 — Rubric ratification (CHARTER §7; all five DRAFT rubrics)

| Rubric | Ruling |
|---|---|
| 7.1 Usable form | **RATIFIED as written.** |
| 7.2 Synthesizability-as-received | **RATIFIED as written.** First-contact discipline (no follow-up calls) affirmed. |
| 7.3 Evidence-sufficiency scale | **RATIFIED as written.** The INSUFFICIENT vs UNREACHABLE-BY-NONEXISTENCE distinction is affirmed as load-bearing. "§J" = CLAUDE.md §J (plan v1.4 clarification). |
| 7.4 Ranking-quality metrics | **RATIFIED with one amendment:** raw metric values (all five) are ALWAYS reported per surface per chart; any tolerance judgment ("above what a reasonable acharya read would tolerate") must state its rationale inline in the finding — no silent thresholds. |
| 7.5 Promise-shortfall attribution | **RATIFIED as written.** Facet-grained attribution (rule 5) and four-source promise sourcing with promise-record INCONSISTENT logging (rule 6) affirmed. |

CHARTER §7 header may be updated from DRAFT → RATIFIED (per this record) by the first
execution conductor; cite this file.

## §2 — Exception rulings (traceability matrix §3)

| Exc. | Ruling |
|---|---|
| 3.1 foundry-brief-as-implementing-surface | ACCEPTED (interpretation blessed). |
| 3.2 battery grading-keys informational | ACCEPTED. |
| 3.3 asset_promises 67 rows vs "~55" + 2 `promise_quote: NOT FOUND` (bo_cgm_motifs, bo_cgm_paths) | ACCEPTED; Lane 10 reconciles the count at compile. The two NOT-FOUND rows: re-run the four-source search; if still not found, log **"promise undeclared"** as a finding in its own right (a built asset with no declared promise is a governance gap, class 5-adjacent). |
| 3.4 P-1/P-3/P-9 thin mapping | CONFIRMED as faithful, not under-built — their plan audit hook is class-9 logs by design; the planning phase (not the audit) owns them. |
| 3.5 plan §11 staleness | RESOLVED — plan v1.4 marks §11 CLOSED. |
| 3.6 76-vs-82 question arithmetic | RESOLVED — plan v1.4 corrects to 82; ledger (328 rows) is authoritative. Foundry's refuse-to-fix behavior commended. |
| 3.7 dangling "§J" | RESOLVED — plan v1.4 clarifies CLAUDE.md §J; LANE2's CHARTER-§7.3 substitution stands. |
| 3.8 / 3.11 recovery episode | ACCEPTED — the guarantee principle worked as designed; retention of the record affirmed. |
| 3.9 AUDIT_STATE Lane5/Lane9 rows PROVISIONAL | **EXECUTION CONDITION E-1** (see §3). |
| 3.10 Lane 9a bhava sample widened to all 12 | **BLESSED** — all 12 bhavas is correct; "key bhavas" was plan compression, not intent. |

## §3 — Conditions on execution

- **E-1 (first act, before any lane work):** the first execution conductor regenerates
  `AUDIT_STATE.md` rows 6 and 10 against LANE5/LANE9 as those files' own text instructs,
  clearing the PROVISIONAL markers.
- **E-2:** Lane 6 executes rubric 7.4 with the §1 amendment (raw metrics always; no silent
  tolerance judgments).
- **E-3:** Lane 10 handles the two NOT-FOUND promise rows per the §2 (3.3) ruling.
- **E-4:** Item-0 proceeds on the UPDATED fork state: `kala_activation` is populated
  (66,836 / 66,747 rows) — the writer is exonerated; the triage now targets the
  `get_temporal_windows` serving query (register R-45, updated 2026-07-12).
- **E-5 (VERIFICATION SWARM — added at gate v1.1, native directive):** EVERY lane (not
  only Lane 2) runs independent verifier workers alongside its audit workers, under its
  conductor: (a) ≥15% random sample of each worker's completed shard rows is independently
  RE-EXECUTED (same call, fresh agent, no sight of the first worker's grade) and
  re-graded; (b) 100% of CRITICAL and HIGH findings are re-verified before they enter the
  lane's merged output; (c) the sample MUST include rows the worker graded PASS/no-finding
  — false negatives (superficial "all clear") are the primary verification target, not
  only false positives; (d) any worker-vs-verifier disagreement escalates to a
  conductor-level live retest (the R5.1 conflicting-verifier discipline: trust neither
  self-report, test directly); (e) verifier results are recorded per shard in the lane's
  state file (verified-agree / verified-disagree-resolved counts).
- **E-6 (DEPTH GATE — added at gate v1.1):** a finding or a PASS is REJECTED by its
  conductor as superficial unless it carries: the exact reproducible call, verbatim
  payload evidence (not paraphrase), the §4 class with the specific rubric clause it
  fails/passes, and — for PASS rows — affirmative evidence of what WAS received (a PASS
  without quoted payload is an unverified claim, not a result). At consolidation, the
  verifier-coverage table (per lane: % sampled, % agreed, escalations) is a mandatory
  section of the audit report; a lane below 15% verification coverage is INCOMPLETE per
  satisfaction criterion 1.
- **E-7 (ENVIRONMENT PROVISIONING — added at gate v1.2, native-approved 2026-07-12):**
  the Wave-1 blocker (`relation "reports" does not exist`, local DB, blocking pipeline
  lanes 2/6/7/9a-leverage) is ruled TEST-BENCH PROVISIONING, not a product fix, and is
  AUTHORIZED under these exact conditions: (a) BEFORE applying anything, run a full
  schema-parity diff — migration files vs local DB — so ALL missing objects surface in
  one pass (one missing baseline relation implies possible others); (b) apply ONLY the
  missing schema objects (DDL as defined by the canonical migrations; no data backfill
  beyond what the migrations themselves define; LOCAL DB only — never deployed/prod);
  (c) log the entire episode as an environment OBSERVATION in the audit report (the
  local-vs-migrations divergence is itself information); (d) findings-only discipline
  remains absolute for everything else — this is the single authorized write, scoped by
  this ruling. Option "point pipeline lanes at prod" is REJECTED (prod data
  contamination + prod LLM spend).
- **E-7b (REFINED RULING — gate v1.3, 2026-07-12; supersedes E-7's application to
  `reports`):** the schema-parity pass found `reports` is RETIRED (DDL only in
  `platform/migrations/_archive/`), yet live consult code queries it unconditionally —
  a genuine serving-layer defect (LCA-2, stands as filed), almost certainly MASKED in
  deployed environments by retain-in-place archival (the physical table still exists
  there). Ruling: **option (b) — recreate `reports` locally from the archived DDL, as an
  explicit, logged exception to canonical-only.** Rationale: this restores the local
  bench to PARITY WITH THE DEPLOYED SYSTEM'S PHYSICAL STATE, which is the system under
  audit; option (a) (code fix) is rejected — it would modify the system mid-audit so the
  pipeline lanes would audit a patched consult path, corrupting the measurement; option
  (c) surrenders the audit's most valuable lanes. Conditions: (i) before creating,
  verify the deployed DB does physically retain `reports` (read-only check, or documented
  inference from prod consult functioning) — record the answer either way; (ii) create
  EMPTY, from the archived DDL verbatim, LOCAL only; (iii) LCA-2 remains OPEN and
  UNCHANGED — the defect is real regardless of the mask; (iv) the episode extends the
  §7.3 environment observation. Second authorized write; scope closes with it.
- **E-7c (SUPERSEDES E-7b — gate v1.4, 2026-07-12; E-7b's premise FALSIFIED):** the bench
  is production Cloud SQL and the deployed DB does NOT retain `reports` — there is no
  "deployed parity" to restore; consult is genuinely broken in production against the
  real schema, for every chart. Ruling: **NONE of the three offered options. (1) NO prod
  schema write — creating a retired table in the live production instance to make an
  audit pass is rejected outright. (2) NO mid-audit code fix — unchanged from E-7b's
  rationale. (3) NO deferral either — instead, RE-ROUTE lanes 2/6/7/9a-leverage to the
  MCP wire channel** (the surgical MCP surface already live with the super_admin
  principal, both charts). This is not a workaround but a return to doctrine: the plan's
  consumption lens (§2) and Lane-2 protocol ("end-to-end exactly as the consuming LLM
  would") were defined on the public MCP channel — the same channel the 2026-07-11
  Cowork session consumed — not on the portal consult HTTP pipeline. The consult
  pipeline becomes an AUDITED-AND-FAILED surface, not the audit's vehicle. Conditions:
  (i) **LCA-2 is UPGRADED to CRITICAL** — live prod code unconditionally queries a
  nonexistent relation; the product's own chat/consult surface cannot serve ANY chart;
  file with full evidence (route line, verbatim error, both-chart reproduction);
  (ii) each re-routed lane records a scope note: consult-pipeline behaviors (its
  orchestration, its report-composition) are NOT covered by that lane and are deferred
  to post-remediation re-audit — coverage honesty per §8 criterion 4; (iii) Lane
  9a-leverage treats consult's breakage as direct evidence on its "is the graph
  leveraged by any serving instrument" question (one fewer instrument than believed);
  (iv) the E-7 family closes with ZERO writes exercised — findings-only discipline
  survived the entire episode intact.
- **E-8 (MATRIX SCHEMA REFINEMENT — gate v1.5, 2026-07-12, ratified without being
  asked, on conductor's design note):** the Concept×Retrievability matrix upgrades
  retrievability from a binary to a PER-CHANNEL VERDICT — at minimum
  {reachable-surgical | served-only-by-down-pipeline | truly-UNREACHABLE}, extensible
  if further channels emerge. Rationale: with 19/42 surgical tools dead (LCA-1) and the
  consult pipeline down (LCA-2), a binary would mislabel thousands of families and
  corrupt the P-12 capability map this matrix seeds. This STRENGTHENS green-light
  condition (1): per-family rows remain mandatory, now carrying per-channel grades +
  derivation notes. Post-remediation re-audit re-grades the
  served-only-by-down-pipeline class once consult is repaired.

## §4 — Invented-section rulings

- CHARTER §7 rubrics: expected invention, now RATIFIED (§1).
- LANE1 §9 Item-0 broadcast extended to Lane 1 (beyond plan-named Lanes 2/7): **BLESSED** —
  harmless and useful.

## §5 — Gate verdict

**PASS.** The chain native-directives → plan (Appendix A) → briefs (traceability matrix,
0 unmapped) is verified end-to-end. Execution of Item-0 and all lanes (parallel, per plan
§12.7 DAG) is authorized under conditions E-1..E-4.

*End of GATE_RATIFICATION_v1_0.*
