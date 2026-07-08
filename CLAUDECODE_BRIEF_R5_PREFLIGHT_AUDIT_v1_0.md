---
canonical_id: CLAUDECODE_BRIEF_R5_PREFLIGHT_AUDIT
version: 1.0
status: READY-FOR-EXECUTION — run any time; ideally AFTER the BA runway closes (final HEAD) but Track B
  (information sourcing) is valid immediately
created: 2026-07-08
author: Cowork (Beyond-Acharya program) — native-directed pre-R5 verification + information sourcing
program: verification gate for CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN (v1.1) and
  RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN (v1.6). READ-ONLY: findings + measurements + sourced
  information, never fixes. Outputs feed: run brief v1.2 fine-tuning, R5_ANSWER_BATTERY authoring,
  R5_AUTHORITY_DOSSIER authoring (both are R5 kickoff preconditions).
objective: >
  (A) Re-verify at current HEAD + live prod every premise the R5 brief stands on — my §18/§20/§23
  evidence was Cowork-side repo-grep + one p50 table; upgrade it to prod-grade (measurements, EXPLAIN,
  live DB values, deployed revisions) and catch drift from the runway's own merges. (B) SOURCE the
  known-unknowns Cowork needs to finalize the battery, the dossier, and the brief.
output: 00_ARCHITECTURE/R5_PREFLIGHT_REPORT_v1_0.md — §1 premise verdicts (CONFIRMED/DRIFTED-with-new-
  evidence/WRONG) · §2 measurements pack · §3 sourced-information pack · §4 recommended brief deltas ·
  §5 GO/NO-GO for R5 kickoff. Commit it.
may_touch: ["00_ARCHITECTURE/R5_PREFLIGHT_REPORT_v1_0.md (create)", "read access everywhere", "read-only SQL", "read-only gcloud describe/logs", "MCP client probes (read tools only)"]
must_not_touch: ["any code fix (even one-liners — findings only)", "any migration", "any deploy or env change", "any chart build", "any write beyond the report file"]
---

# BRIEF R5-PREFLIGHT — VERIFY THE PREMISES, SOURCE THE UNKNOWNS

> Every item: VERDICT + EVIDENCE (file:line at CURRENT HEAD / SQL result / measurement / gcloud output).
> My prior evidence is in the design doc Parts IV–V — where HEAD has drifted, report the NEW truth.

## TRACK A — PREMISE RE-VERIFICATION (prod-grade upgrade of Parts IV–V)

A1. **HEAD drift scan.** The runway's W1/W2 merges touched serving surfaces (lel_query fns,
    retrieval_capability_spec, tool_metadata, asset_names). Diff the §18/§20 cited files between the
    audit-era SHA and HEAD; report every §20 fix site whose line numbers or surrounding logic moved.
A2. **Registry + seam:** confirm at HEAD the three-surface architecture (canonical registry map ·
    platform-mcp Zod shims · primitives whitelist), the alias mechanism, and the hand-maintained name
    maps. Count: primary tools, aliases, total MCP-visible names.
A3. **Envelope sites:** confirm the two envelope builders and the null/[]-hardcoding at HEAD; list
    which tools have NO envelope at all.
A4. **The four serving defects LIVE:** (a) `/api/mcp/db/query` still absent (route scan); (b) 401
    header gap still present in both proxy helpers; (c) as_of_date still dropped by get_dashas;
    (d) phala serving SQL still selecting id/theme vs the mig-330 schema — AND run the actual failing
    query read-only against prod to capture the exact error.
A5. **Valence vocabulary — settle it with DATA:** `SELECT DISTINCT valence, count(*) FROM
    bodha_cgm_edges GROUP BY 1` on both charts. Which vocabulary did the writers ACTUALLY write?
    (325's benefic/malefic vs 394's harmonious/antagonistic.) Same for edge_type distinct values —
    the traversal facet enums must match reality.
A6. **Percentile + stored-salience state:** prod NULL-rate of salience_pctl_in_class (mig 393 col);
    distinct-value profile of computed_salience (is 2.326672 still ~degenerate pre-R4?); confirm
    query-time percentile_within_class=1 behavior and root-cause it (single-member classes? bug?).
A7. **Performance measurements (the §24 baseline the P0 brief never got):** p50 AND p95 (n≥20 warm +
    note colds separately) for: list_my_charts, chart digest, signals(top_k=10), domain_reading,
    dashas, yogas, traverse_graph, one apex, vector_search (post-fix it will 401 — record the fail
    time), phala_outlook. EXPLAIN ANALYZE the dual-pool salience ORDER BY — confirm/deny the missing
    `(chart_id, ayanamsha_id, computed_salience DESC)` index and report the plan. Current pg pool
    config, Cloud Run min-instances/concurrency/CPU per service (gcloud describe), and observed
    cold-start frequency from recent request logs.
A8. **dualOutput duplication measured:** for one mid-size response, bytes of structuredContent vs the
    pretty-printed text duplicate — quantify the §23-S3 tax precisely.
A9. **Security flag verified:** confirm the capability route performs no per-call chart entitlement
    (code at HEAD) — do NOT probe with unentitled access attempts beyond code reading; this is
    evidence for the MCP-elevation workstream.
A10. **MCP SDK currency:** platform-mcp package.json — SDK version; does it support outputSchema?
    elicitation? Tasks? What protocol version does the DEPLOYED server negotiate? (This decides
    whether §32 adoptions are W-wave items or SDK-upgrade-first items.)

## TRACK B — INFORMATION SOURCING (the unknowns Cowork needs)

B1. **Consumer inventory (decides format-negotiation scope):** enumerate every live MCP/API consumer —
    Claude desktop/web connector, portal chat (bulk_context path), GPT/OpenAI channel, any scripts.
    For each: which tool families it calls, does it parse `content` text or `structuredContent`?
    Evidence from code + recent access logs if available.
B2. **Request corpus feasibility (parity gates need replay traffic):** does any request/response
    logging exist on the MCP or capability paths (trace_emitter? Cloud Run request logs with bodies?)?
    If NO: report what a minimal capture shim would need (the run brief will front-load it in W0a).
B3. **tools/list footprint TODAY:** measure the full tools/list response (KB + est. tokens) — the
    §31.1 baseline number.
4. **Battery inputs package:** locate + digest for Cowork: the 38-topic reachability matrix results
    (pre-rebuild audit C1), the G10-QT rubric text, golden-eval assets + current scores, the Q1–Q9
    query-class taxonomy file. Report paths + one-paragraph state of each.
B5. **Shastra-map source completeness:** do the L0 ontology tables carry the full domain→bhava/karaka/
    varga/dasha-rule correspondences the §28.5 card needs (all 12 domains × the 38 topics), or only
    the 22 event classes? Quantify gaps (the dossier must know what the card can cite vs what
    Pratinidhi-R must rule).
B6. **Time-confidence source (§31.4):** what does ph_rectification expose per chart TODAY
    (confidence/train_score/offset fields, both charts' live values)? Is there per-varga lagna
    sensitivity data anywhere (varga lagna positions per candidate time), or must the ladder be
    computed at serve time from birth_params?
B7. **Telemetry substrate (§31.6):** what does trace_emitter/existing logging already capture per
    tool call (fields, retention, where it lands)? Gap to the call-sequence telemetry the loop needs.
B8. **min-instances cost:** compute the actual monthly cost of min-instances=1 for amjis-web +
    amjis-mcp at their current CPU/memory in asia-south1 (public pricing) — the native's spend
    decision gets a number, not a shrug.
B9. **Anything else a fresh eye flags:** one section of free-form findings — premises Cowork never
    thought to question. Explicitly invited.

## OUTPUT + ACCEPTANCE
`R5_PREFLIGHT_REPORT_v1_0.md` committed; zero UNKNOWNs left blank (every item answered or marked
BLOCKED-with-reason); §4 lists concrete run-brief deltas (numbered, one line each); §5 GO/NO-GO.
No code changed anywhere — `git status` clean except the report. Cowork gate-checks the report, folds
deltas into run brief v1.2, then authors the battery + dossier from the §3 information pack.
