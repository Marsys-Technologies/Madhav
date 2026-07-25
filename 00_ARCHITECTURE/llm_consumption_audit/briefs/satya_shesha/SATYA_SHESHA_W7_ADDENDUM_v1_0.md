---
artifact: SATYA_SHESHA_W7_ADDENDUM (Flagship Substance-Inline)
canonical_id: SATYA_SHESHA_W7_ADDENDUM
version: 1.0
status: READY-FOR-EXECUTION — extends SATYA_SHESHA_BRIEF_v1_0.md with work item W7 + builder B5
created: 2026-07-25
author: Fable (Cowork), responding to the Verifier's Phase-4 flagship re-check (sealed harness 2/13
  flat after α's #782 completeness-pointer fix, deployed and honestly measured)
parent: 00_ARCHITECTURE/llm_consumption_audit/briefs/satya_shesha/SATYA_SHESHA_BRIEF_v1_0.md
  (all of its §3 topology, §4 verification protocol, §5 rails and merge/deploy rules apply verbatim)
how_to_run: >
  If SATYA-ŚEṢA is currently RUNNING: hand this file to its Conductor as W7, assigned to a new
  parallel builder B5 (files are disjoint from B1–B4 except registry_bridge.ts — B5 owns it; B3
  must not touch it). If SATYA-ŚEṢA has CLOSED: run this standalone with the §4 mini-kickoff.
---

# W7 — Flagship substance-inline: serve the reading, not the receipt

## §1 — The finding this answers (the OFFER LAW, now proven twice)

The Verifier's re-check of #782 (live revision amjis-mcp-00475-d2t) established:

- α's fix attaches a truthful 100%-accounting block (`slice_size: 13820, accounted: 13820,
  synthesis_gate: OPEN`) + a dossier pointer to `assess_wealth` — **an accounting layer, not
  substance**. Its own commit message predicted the measurement would decide; it did: sealed
  harness **2/13, flat against baseline**.
- The naive consumer **saw the pointer and declined it** — it even wrote "a full dossier…is
  available if you want the exhaustive drill-down," then treated the headline as the answer.

**The Offer Law:** this product has now demonstrated twice that ANY architecture relying on the
consuming LLM to take an optional extra step will see that step skipped. First: compiled floors
nobody executed (EL-02). Now: a 100%-accounted dossier pointer nobody follows. The mandate's word
was **pushed** — "every remotely relevant piece of information pushed to the LLM before it
synthesizes" — and an offer is not a push. **Offer-shaped remedies are henceforth prohibited as
closures for consumption items.** (W5's owner: record this as a register amendment on EL-02/EL-14.)

Three precise defects inside the current state, each independently fixable:

**D1 — Served-but-not-reflected (the surprising one).** Six of the 13 graded families ALREADY have
substance in assess_wealth's content (indu_lagna Scorpio/Mars/8th, D2+D11 dignities, D2 AV pinda,
arudha, dispositor relations) — and the consumer reflected NONE of them. Substance buried in 40KB
of JSON blocks does not reach the answer; LLMs reflect what is narratively foregrounded. This is
EL-29 (composition) measured live: the gap is not only serving, it is FOREGROUNDING.

**D2 — Gate-semantics inversion (subtle, actively harmful).** The headline response reports
`accounted: 100%, synthesis_gate: OPEN` on the FIRST call. "Accounted" means the server reconciled
its books — but the consumer read it as "you have everything," so the block designed as a lure
functioned as an **absolution**. A gate on a headline response must reflect DELIVERED-TO-THIS-
CONSUMER, not reconciled-on-server; OPEN on call 1 tells the naive consumer the skip is principled.

**D3 — The trimmer ate the fix's own payload (EL-36/EL-46 class, recurring).** The budget trimmer
stripped `coverage_map` to `[]` and truncated `completeness_directive` mid-sentence — the actionable
parts of the new block did not survive to the wire, while boilerplate did. The new
completeness/directive fields were never added to the hardFloor-immune set.

## §2 — The fix: assess_wealth serves the acharya's opening reading, inline

Don't fight consumer tool choice (the naive consumer will always pick `assess_wealth` for "how is
my wealth?" — name affinity beat the enriched dossier description). **Make the tool they pick
satisfy the mandate.**

**W7.1 — Composed family digest, substance-inline.** `assess_wealth` (and `assess_career`) gain a
`reading` section: for EVERY concept family in the domain's TCI slice (top tier by Ω2 relevance —
for wealth: indu lagna · D2 · D11 · per-varga AV · argala on 2/11 · dispositor closure ·
mechanisms/chains inventory · special lagnas/arudha · cross-ayanamsha agreement · timing windows ·
contradictions · remedies · yogas/dhana), **one to three dense grounded sentences of SUBSTANCE** —
the value, the verdict, the fact_ids — composed by deterministic template over already-served data
(B.10: no generative call in the serving path). ~13 families × ~300 bytes ≈ 4KB: trivially
affordable. This is what an acharya says first; the dossier remains the full-hydration drill.
**Integrity constraint: the family list is derived MECHANICALLY from the TCI slice's relevance
tiers, NOT from the sealed harness's grading list.** They coincide by construction (the harness list
was frozen FROM the TCI) — but deriving from the harness would be teaching to the test and would
not generalize to ungraded domains. The derivation must work unchanged for any domain.

**W7.2 — Fill the two not-served families.** `argala` on H2/H11 (the facet serves house-resolved
post-elevation — wire it into the wealth digest) and `cross_ayanamsha_agreement` (γ's EL-27
machinery — serve the agreement score for the digest's headline findings). `remedies` currently
null: populate from the remedy engine or serve an explicit honest-empty with reason — never bare
null fields.

**W7.3 — Fix the gate semantics on headline responses.** The first-call block reports per-family
hydration honestly: `reading_digest: 13/13 families summarized inline · full_hydration: available
via dossier (N rows)`. `synthesis_gate: OPEN` may appear ONLY on responses (or dossier page
sequences) where the consumer has actually received the slice. Never serve OPEN as a first-call
absolution.

**W7.4 — hardFloor the new fields.** `reading` (the digest), `domain_completeness`,
`completeness_directive`, `coverage_map` (or its per-family successor) join the trim-immune honesty
set. The digest is the densest, most-actionable layer — under §N.6.2 it is the LAST thing
trimmable, not the first. Regression test: worst-case response with trimming active still carries
the full digest untruncated.

## §3 — Acceptance (Verifier-owned; the §4 protocol of the parent brief applies)

1. **Sealed harness, n=3 runs** (consumers are stochastic; the parent's n=1 caveat is answered with
   replication, never with prompt-tuning): naive "How is my wealth?" through the UNMODIFIED frozen
   harness. **Pass = median ≥12/13 on the strict both-prongs grade** (substance served AND reflected).
   The harness, its system prompt, and its grading list may not be touched — rule 3 of the γ
   kickoff stands: you do not grade yourself, and you do not tune the grader.
2. Same digest mechanism produces a well-formed reading for `assess_career` (proves the derivation
   is TCI-generic, not wealth-tuned) on both canonical charts.
3. Trim-survival: a deliberately small `budget_kb` call still carries the full digest; trimming
   sheds raw blocks instead.
4. First-call response contains no `synthesis_gate: OPEN` absent actual slice delivery.
5. Regression: the parent brief's §1 verified-FIXED list still passes; #782's accounting block
   still present and truthful.
Dispositions per the parent §4: four states, no "passed with caveats."

## §4 — Mini-kickoff (only if SATYA-ŚEṢA has already closed; otherwise hand to its Conductor)

```
You are the CONDUCTOR of SATYA-ŚEṢA W7 (Flagship Substance-Inline), FULLY AUTONOMOUS, no human
available. Read, in order: 00_ARCHITECTURE/llm_consumption_audit/briefs/satya_shesha/
SATYA_SHESHA_W7_ADDENDUM_v1_0.md (this brief — §1 is the diagnosis, §2 the fix, §3 acceptance),
then the parent SATYA_SHESHA_BRIEF_v1_0.md §3–§5 (topology, verification, rails — they bind you),
then the Verifier's flagship re-check evidence in the elevation ledgers.
Spawn ONE builder (Sonnet; Opus after 2 failed verify cycles) for W7.1–W7.4 — primary files:
platform-mcp/src/tools/registry_bridge.ts (the #782 helpers), platform-mcp/src/lib/
response_budget.ts (hardFloor set), the assess handler wiring — and ONE Opus Verifier that never
writes code. Merge via PR + auto-merge (main is protected; never push main directly); deploy
amjis-mcp EXPLICITLY; then the Verifier runs §3 acceptance including the n=3 sealed-harness runs
against LIVE production, both canonical charts. The harness may not be modified — a fix that
requires touching the grader is not a fix. Serving-side only; no writers, no rebuilds, no
kala_gochara_windows data. Wall-clock cap 3h. DONE = Verifier approval; four dispositions, no
"passed with caveats". Close with a report + ledger entry + register amendment (the OFFER LAW on
EL-02/EL-14) merged to main. Begin.
```

---

*The one-line version of this entire addendum: the consumer asked "how is my wealth?" and was
handed a receipt proving the library is complete. Serve the reading. The library card is for
footnotes.*
