---
artifact_id: VERIFICATION_E2E_11C_PLAYBOOK
status: ACTIVE
authored_by: Claude (Cowork) 2026-04-29
authored_for: native execution (no Claude Code session needed)
related_briefs:
  - CLAUDECODE_BRIEF_RETRIEVAL_11C_PROBES (COMPLETE)
  - CLAUDECODE_BRIEF_RETRIEVAL_11C_a (COMPLETE — graph topology)
  - CLAUDECODE_BRIEF_RETRIEVAL_11C_b (COMPLETE — classifier seeds)
  - CLAUDECODE_BRIEF_RETRIEVAL_11C_c (COMPLETE — L2.5/L3 chunks)
estimated_time: 60–90 minutes
---

# End-to-End Verification Playbook — Post-11C_c

## §1 — Purpose

Three retrieval briefs landed in 48 hours. Before launching a fourth, look at the actual LLM output on representative queries to confirm the cumulative effect. This playbook is a 10-query check that exercises every retrieval path that recent work touched. The output is a per-query rubric score + a small set of verbatim response excerpts. Bring those back to chat and the next brief decision becomes data-driven.

This is **not** a Claude Code session. You run it manually through the deployed Consume tab.

## §2 — The 10 queries

Run each of these against the deployed amjis-web (post-11C_c, revision amjis-web-00026-t9s or later) using the Consume tab logged in as you (super_admin). Open the trace panel after each query so you can capture which tools fired with what result counts.

| # | Query | What it should exercise | Pass signal |
|---|---|---|---|
| 1 | "What sign is my Mercury placed in?" | factual class → msr_sql + vector_search (L1 forensic chunks) | Returns Capricorn 00°50′11″ with citation; trace shows msr_sql+vector_search firing |
| 2 | "What's in my 7th house and what does it mean?" | factual+interpretive → cgm_graph_walk(HSE.7) + vector_search (L1+UCN) | Names Saturn (exalted) + Mars; trace shows cgm_graph_walk seed=["HSE.7"] |
| 3 | "What does my chart say about my career?" | interpretive → msr_sql + cgm_graph_walk(HSE.10, PLN.MERCURY) + vector_search L2.5 | Mentions Mercury 10H, Saturn AmK, Mahapurusha yoga; vector_search returns ucn_section + cdlm_cell + rm_element doc_types |
| 4 | "Tell me about my Saraswati yoga and what it means in practice." | interpretive (yoga) → cgm_graph_walk(YOG.SARASWATI) + vector_search RM.28 + msr_signal | Names the planets in the yoga; vector_search returns rm_element=RM.28 in top-K |
| 5 | "Are there contradictions in my karaka system?" | discovery → contradiction_register + cgm_graph_walk(KARAKA.DUAL_SYSTEM_DIVERGENCE) | Mentions 7-karaka vs 8-karaka divergence, Rahu-as-PK; trace shows seeds includes KARAKA.DUAL_SYSTEM_DIVERGENCE |
| 6 | "How does my career relate to my marriage in this chart?" | cross_domain → cdlm_cell + cgm_graph_walk(HSE.7, HSE.10, PLN.MARS, PLN.SATURN) + resonance_register | Names Saturn+Mars 7H, the AmK-7H structural identity; vector_search returns cdlm_cell career→relationships |
| 7 | "What does my Saturn dasha bring over the next two years?" | predictive → temporal + cgm_graph_walk(DSH.MD.SATURN, PLN.SATURN) + msr_sql forward_looking=true | Time-windowed claim with explicit years; trace shows temporal step (within reasonable latency, NOT 300s) |
| 8 | "What does my chart suggest about my health risks?" | interpretive (health) → pattern_register + msr_sql(domain=health) + vector_search | Specific risks named (not generic "watch your health"); pattern_register returns ≥2 patterns |
| 9 | "What is my chart's spiritual path and when does it activate?" | interpretive+predictive (spiritual) → vector_search UCN moksha sections + RM Ketu + temporal | Mentions Ketu MD timing (2031–2038), references Foundation Signature 4 or similar UCN content |
| 10 | "Explain section IV.1 of my unified chart narrative." | interpretive (UCN-targeted) → cgm_graph_walk(UCN.SEC.IV.1) + vector_search ucn_section | Quotes / paraphrases UCN Part IV section 1 content; vector_search returns ucn_section in top-K |

## §3 — Rubric per response

For each of the 10 responses, score on five dimensions, 0–2 each. Total: 0–10 per query.

**D1 — Specificity (0–2).** Does the response reference specific chart entities by name and detail (degrees, signs, houses, yoga names) or stay generic?
- 0: generic ("your chart suggests strength here")
- 1: names entities but no specifics
- 2: specific with classical detail (e.g., "Saturn at 0°50′ Libra, exalted, in the 7th from Aries Lagna")

**D2 — Source diversity (0–2).** Open the trace panel. Count distinct retrieval tools that returned `item_count > 0` for this query.
- 0: only vector_search returned content
- 1: 2 tools returned content
- 2: 3+ tools returned content

**D3 — L2.5 visibility (0–2).** In the vector_search trace step's items, what doc_types appear?
- 0: only `l1_fact`
- 1: `l1_fact` + one of (msr_signal, cgm_node)
- 2: `l1_fact` + two or more of (ucn_section, cdlm_cell, rm_element, msr_signal, domain_report)

**D4 — Classical grounding (0–2).** Does the response cite classical sources or use classical jargon correctly?
- 0: pure vernacular, no classical terms
- 1: uses classical terms (Mahapurusha, Vargottama, etc.) without sources
- 2: cites BPHS / Saravali / Jaimini / Phaladeepika OR provides shadbala / dignity numerics

**D5 — Predictive grounding (0–2).** Only applies to queries 7 and 9. For others, score N/A and don't include in the mean.
- 0: vague timing ("eventually", "in the future")
- 1: named period (Saturn dasha, age range) without window
- 2: explicit dates or year-windows with falsifier (e.g., "2027–2030 Saturn AD; falsified if no career escalation by Q3 2028")

**Score:** sum D1–D4 (and D5 if applicable). Mean across 10 queries.

**Pass threshold:** mean ≥ 6.5 across the 10 queries → the briefs materially moved the needle. Mean 5.0–6.4 → some uplift but identifiable gaps. Mean < 5.0 → something is still broken; deeper diagnosis before the next brief.

## §4 — Capture template

For each query, copy this block into a new file (e.g., `outputs/E2E_VERIFICATION_RESULTS.md` or just a chat paste):

```
### Query #N: <verbatim query>

**Trace summary:**
- Tools fired (with item_count > 0): <list>
- vector_search doc_types in top results: <list>
- temporal latency: <ms or "not fired">
- cgm_graph_walk seeds: <array from QueryPlan>

**Response excerpt (first 3–5 sentences, verbatim):**
> ...

**Rubric:**
- D1 specificity: 0/1/2
- D2 source diversity: 0/1/2
- D3 L2.5 visibility: 0/1/2
- D4 classical grounding: 0/1/2
- D5 predictive grounding: 0/1/2/N/A
- TOTAL: N/10
```

## §5 — What to bring back

When you finish, paste in chat:

1. **The 10 query/score blocks** (or just the totals if the responses are too long — but at minimum 2–3 verbatim excerpts that struck you as either acharya-grade or noticeably weak).
2. **Mean rubric score across the 10 queries.**
3. **Anomalies:** any query where a tool didn't fire when you expected it to, or where the response looked nothing like the trace data.
4. **Latency observations:** anything that took > 30s, especially the temporal tool (per PROBE 8 it was hitting 300s timeouts; verify whether that's still the case).
5. **One free-form sentence:** "compared to where this was three days ago, the responses feel ___."

## §6 — What I'll do with it

The rubric scores plus your free-form impression decide the next brief:

- **Mean ≥ 7.5 + most queries D2 ≥ 1 + temporal latency normal** → the pipeline is in solid shape; next brief is F2.2 (vector_search filter precision) to push from "good" toward "excellent".
- **Mean 6.5–7.4 with D3 = 0 on multiple queries** → 11C_c chunkers under-coverage is the visible gap; next brief is the chunker coverage close (ucn_section H3 + cgm_node UCN merge).
- **Mean 5.0–6.4 with mixed signals** → observability cluster (audit_events + query_plans + temporal timeout) so we can measure precisely what's still missing.
- **Mean < 5.0** → something deeper is wrong; pause new briefs and do a fresh pipeline trace deep-dive.
- **Temporal latency still 300s** → sidecar timeout fix becomes urgent regardless of other scores.

## §7 — Hard constraints

- This is **manual** — do not ask Claude Code to run this. It needs your judgment on the rubric.
- **Do not** modify any source files. This is read-only verification.
- **Do not** rerun the pipeline or redeploy.
- The trace panel is your friend — use it on every query to capture D2 and D3 scores.

---

*End of VERIFICATION_E2E_11C_PLAYBOOK. Run it, paste results, decide next brief from §6.*
