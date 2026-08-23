---
lane: F-10
stream: S5 MŪLA
stage: D (DIAGNOSE)
role: CL-03 EXEMPLAR (sibling replication targets: F-03, F-06, F-08, F-26, F-27, F-133)
status: CONFIRMED-LIVE (not fixed)
severity: TIER1-CORRECTNESS
date: 2026-08-16
---

# F-10 Diagnosis — `prashna_undertaking_get` election-window domain filter no-op

## 1. Live reproduction

**Command actually run** (via `mcp__marsys-jis-direct__prashna_undertaking_get`, the direct MCP
tool made available to this session):

```
prashna_undertaking_get({chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a', domain: 'health'})
prashna_undertaking_get({chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a', domain: 'career'})
```

Raw responses saved to `lanes/F-10/repro_raw.json` (both calls, full envelope).

**Result: reproduces live, and more starkly than the corpus's illustrative example.**

`domain: 'health'` →
- `content.action_class` = `"medical_procedure"` (correctly domain-mapped — computed via
  `_DOMAIN_TO_ACTION`)
- `content.election_windows[].action_class` = `["marriage", "marriage", "medical"]`, ranked in
  that order by `composite_quality` (0.25, 0.25, 0.187)
- Top-ranked window is `marriage`, not the health-relevant `medical` window (which is ranked
  **last**, third of three)
- `judgment_flags: []` — no mismatch disclosure of any kind

`domain: 'career'` →
- `content.action_class` = `"business_start"` (correctly domain-mapped)
- `content.election_windows[]` = **byte-for-byte identical** to the health call:
  `["marriage", "marriage", "medical"]`, same `composite_quality` values, same
  `window_start`/`window_end` timestamps
- `judgment_flags: []`

The `career` result is stronger evidence than the corpus's own illustrative claim ("all returned
windows were `action_class='new_venture'`") — that specific action_class was not observed in this
live run for either domain. What **is** proven live: `election_windows` is completely
domain-invariant. Two different `domain` values that correctly produce two different
`content.action_class` values produce the *exact same* `election_windows` array — conclusive proof
the underlying SQL never consults `domain` (or the derived `action_class`) at all; it returns the
chart's global top-N `phala_muhurta` rows by `composite_quality` regardless of what the caller
asked for.

This is a WIN in the narrow sense that the corpus's specific example doesn't match current
behavior — but it is not an ALREADY-FIXED case. The defect is live and, if anything, more clearly
demonstrable now than as originally described.

## 2. Claim decomposition

The audit claim decomposes into (at least) these distinct, separately-checkable assertions:

| # | Assertion | Verified? |
|---|---|---|
| (a) | The `election_windows` sub-query applies no domain/action_class filter, despite an inline comment claiming a domain→action-class mapping is applied there. | **TRUE.** Confirmed by reading `muhurtaResult` (current lines 921–931) — no `action_class` predicate, no reference to `domain` or `actionClass` in the query or its bind params (`[chart_id, top_windows]` only). The comment block at lines 878–881 ("Reads … phala_muhurta (election windows for domain) …") does assert domain-scoping that the query does not perform. |
| (b) | A wrong-domain window ranks ABOVE the correct one, with no indication to the caller. | **TRUE for the `health` case** — `marriage` (0.25) ranks above `medical` (0.187) in `election_windows[0]` and `[1]`, and `judgment_flags` is empty. **Superseded/strengthened for the general case** — live testing shows this isn't just a ranking problem, it's total domain-invariance: the same three windows return for every domain tested, so "ranks above" undersells it; the domain-correct window set is never computed as a distinct set in the first place. |
| (c) | No mismatch disclosure is served to the caller. | **TRUE.** `judgment_flags: []` in both calls. There is no field anywhere in the `recipe` object (lines 995–1011) that compares `election_windows[].action_class` against `actionClass` (the domain-derived value at line 968) or flags a mismatch. The only place `actionClass` is used at all is `content.action_class` (line 998, informational) and gating the separate `ontologyResult` query (line 969). |
| (d) *(new, found during this diagnosis — not in the original corpus text)* | The domain-to-action-class mapping is not merely unwired from `muhurtaResult` — it is **computed after** `muhurtaResult` has already executed. | **TRUE.** See §3 below. This means the fix cannot be "add a WHERE clause using the existing `actionClass` variable" without also reordering the function — `actionClass` doesn't exist yet at the point `muhurtaResult` runs. |

## 3. Mechanism — file:line (current, re-verified against source, not corpus text)

File: `platform-mcp/src/tools/register_p1_synthesis.ts` (current `main`-based worktree,
`.claude/worktrees/par-s5-lead`). **Line numbers below are current and differ slightly from the
corpus's `902-913` / `934-946` citation** (drifted by a handful of lines from unrelated edits
above; the mechanism itself is unchanged).

Comment claiming domain-scoping (lines 878–881):
```
878:  // ── prashna_undertaking_get ───────────────────────────────────────────────
879:  // BA-P5B Step 3: Q4 undertaking recipe = prashna verdict × election scoring × fructification.
880:  // Reads ga_prashna_judgment (prashna chart), phala_muhurta (election windows for domain),
881:  // phala_anchors (fructification timing anchor), brahma_activity_ontology (rules).
```

The `muhurtaResult` query itself (**current lines 920–931**, corpus said 902–913):
```
920:        // 2. Election windows (phala_muhurta for domain → action class mapping)
921:        const muhurtaResult = await platformQuery(`
922:          SELECT pm.action_class, pm.window_start, pm.window_end,
923:                 pm.composite_quality, pm.window_quality_verdict,
924:                 pm.fructification_anchor, pm.tarabala_chandrabala_jsonb,
925:                 pm.significators_met_jsonb, pm.follow_up_hook_jsonb
926:          FROM phala_muhurta pm
927:          WHERE pm.chart_id = $1
928:            AND pm.composite_quality IS NOT NULL
929:          ORDER BY pm.composite_quality DESC NULLS LAST
930:          LIMIT $2
931:        `, [chart_id, top_windows], principal)
```
No predicate on `action_class`; bind params are `[chart_id, top_windows]` only. `domain` never
enters this query.

Contrast with `anchorResult` (**current lines 934–946**), which DOES correctly apply the domain
filter — proving the pattern was known and used elsewhere in the same function, just not wired
into `muhurtaResult`:
```
934:        const anchorResult = await platformQuery(`
935:          SELECT pa.anchor_id, pa.domain, pa.event_type, pa.posterior,
...
941:          WHERE pa.chart_id = $1
942:            AND pa.domain = $2
943:            AND pa.posterior IS NOT NULL
944:          ORDER BY pa.posterior DESC NULLS LAST
945:          LIMIT 3
946:        `, [chart_id, domain], principal)
```

The `_DOMAIN_TO_ACTION` mapping and `actionClass` derivation (**current lines 949–968**, corpus
said 934–946 — this block moved down ~15 lines relative to the corpus's citation, most likely
because of the SHABDA-SHUDDHI Lane L5 comment block that was added above it):
```
957:        const _DOMAIN_TO_ACTION: Record<string, string> = {
958:          career:       'business_start',
959:          wealth:       'contract_signing',
960:          health:       'medical_procedure',
961:          relationship: 'marriage',
962:          spirituality: 'spiritual_initiation',
963:          transition:   'travel_journey',
964:          residence:    'griha_pravesh',
965:          travel:       'travel_journey',
966:          education:    'education_start',
967:        }
968:        const actionClass: string | null = _DOMAIN_TO_ACTION[domain] ?? null
```

`actionClass` is used exactly twice after this: `content.action_class` (line 998) and to gate
`ontologyResult` (line 969, `actionClass ? await platformQuery(...) : { rows: [] }`). It is never
referenced by `muhurtaResult`.

**Corpus claim confirmed, with one refinement:** the corpus said "correctly used to filter the
separate ontologyResult query" and implied the fix is simply "wire actionClass into the
muhurtaResult query." That undersells the defect: `actionClass` is computed at line 968, which is
**textually and temporally after** `muhurtaResult` already ran (line 921–931). Any fix has to
either hoist the `_DOMAIN_TO_ACTION` lookup above the `muhurtaResult` query, or restructure the
function so `muhurtaResult` runs after `actionClass` is known. This is exactly the kind of
sequencing detail a naive sibling-replication ("just add `AND pm.action_class = $N`") would miss
without noticing the variable doesn't exist yet at that point in the file.

## 4. Sibling census

### 4a. Within `register_p1_synthesis.ts` (same file, near this defect — explicitly requested)

All `platformQuery` blocks in the file, checked for the same shape (a computed filter variable
available but not applied to one of several parallel queries):

| Query var | Lines | Domain-scoped? | Verdict |
|---|---|---|---|
| `insightResult` | 793 | n/a (no domain param in this tool) | not applicable |
| `discResult` | 815 | n/a | not applicable |
| `prashnaResult` | 907–918 | No domain predicate — but correctly so; this queries `ga_prashna_judgment` filtered only by `chart_id`, which is domain-independent by design (the horary verdict itself isn't per-domain). | clean |
| **`muhurtaResult`** | **921–931** | **`domain`/`actionClass` never applied** | **F-10 — confirmed defective** |
| `anchorResult` | 934–946 | `AND pa.domain = $2` correctly applied | clean |
| `ontologyResult` | 969–973 | Gated on `actionClass ? ... : {rows: []}` — correctly applied | clean |

Also checked the file's other three `domain`-parameterized tools (`mimamsa_insight_get` line 561,
`bodha_discoveries_get` line 602, `synth_tail_divergence_get` line 714) — all three correctly
thread `domain` into the downstream registry-capability call or SQL `domainClause`. **F-10 is the
only defective query in this file**; it is not a file-wide pattern, it's isolated to this one
sub-query — which also means the fix is narrowly scoped once the sequencing issue (§3) is
accounted for.

### 4b. F-27 sibling — confirmed same defect shape, different file/tool

Per the assignment brief, F-27 (`mimamsa_calibration_get` domain no-op) was checked directly since
it is named as sharing this defect shape:

**`platform-mcp/src/tools/register_p1_aliases.ts:1844-1858`** — the tool's public schema:
```
1844:  server.tool(
1845:    'mimamsa_calibration_get',
1846:    '[Phase-1 alias] Query calibration stats for a chart (same as query_calibration).',
1847:    {
1848:      chart_id: z.string().uuid().describe('Chart UUID'),
1849:      domain:   z.string().optional(),
1850:      ...GlobalBase,
1851:    },
1852:    async ({ chart_id, domain, limit, offset }) => {
1853:      try {
1854:        const data = await callPlatformPrim('query_calibration', { chart_id, domain, limit, offset }, principal)
```
`domain` is declared, accepted, and forwarded to the `query_calibration` primitive call.

**`platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`** — the handler
actually invoked:
- `input_schema` (lines 27–43) declares only `chart_id`, `include_held_out`, `promoted_only` —
  **`domain` is not even a recognized parameter of the handler it's forwarded to.**
- The handler destructures `args.chart_id`, `args.include_held_out`, `args.promoted_only` (lines
  65–67) — `args.domain` is never read.
- All four parallel queries (`verdictSql` 72–84, `reliabilitySql` 86–92, `multiplierSql` 94–101,
  `qaSql` 103–108) filter only by `chart_id` (+ `leakageFilter`/`multFilter` built from the two
  boolean params). None filters by domain.
- `multiplierSql` (line 95) even `SELECT`s a `domain` column from `mimamsa_multipliers` — the
  table demonstrably has domain-scoped rows — but nothing in the WHERE clause narrows to the
  caller's requested domain.
- The response's own `filters` echo field (line 129) reports `{ include_heldout, promoted_only }`
  — `domain` isn't even echoed back, let alone applied. A caller passing `domain: 'health'` gets
  no error, no flag, and the exact same payload as a caller passing no domain at all.

This is the identical defect shape to F-10: a filter parameter is declared at the public-tool
schema layer, threaded through a proxy call, and silently dropped before it ever reaches a WHERE
clause — with zero disclosure that the filter had no effect. **Confirmed, not just plausible.**

### 4c. Additional un-verified candidates surfaced by this census (in scope for the harness, not this diagnosis)

A grep for tools/aliases declaring a `domain: z.string().optional()` (or required) parameter
turned up ~19 call sites across `register_p1_synthesis.ts`, `register_p1_aliases.ts`,
`register_p1_reference.ts`, `registry_bridge.ts`, and `scan_fetch_signals.ts`. Beyond the 4a/4b
set above (verified clean or verified defective), one additional candidate stood out but was
**not verified** within this lane's scope (Stage D is F-10 only; flagging for the sibling lanes /
the harness):

- `phala_mitigation_get` (`register_p1_aliases.ts:1733-1744`) — declares `domain: z.string().optional()`
  and forwards `{ chart_id, domain }` to `callPlatformPrim('mitigation_map', ...)`. Whether the
  `mitigation_map` primitive actually applies `domain` was not checked here — same shape as F-10/F-27
  (schema-declared param forwarded to a primitive), unconfirmed whether the primitive drops it.

The remaining ~15 `domain`-param sites were not individually re-verified; this census establishes
the *pattern* (declared filter param, forwarded across a tool→primitive boundary, silently
unused at the SQL layer) and gives the harness (§5) a machine-checkable way to close out the rest
without a human re-reading each file.

## 5. Blast radius

**Direct correctness harm:** a caller of `prashna_undertaking_get` — the Q4 "should I do this
undertaking now" recipe — receives a "best election window" that is provably wrong-domain for any
domain other than whichever one happens to top the chart's global `composite_quality` ranking
(here: `marriage`/relationship windows dominate regardless of what the caller asked). No flag,
no lower confidence, no note — the response reads as if the ranking were domain-aware. This is a
direct hit on:

- **CLAUDE.md §N.7 (Narration Fidelity) item 6** — "An honest null beats an invented judgment."
  Here it's worse than a null: a domain-labeled `content.action_class` sits directly next to
  `election_windows` that silently disagree with it, with nothing marking the disagreement.
- **CLAUDE.md §N.6 (Serving Density Principle)** — the density-layering discipline requires
  distinguishing confirmed/relevant findings from off-target ones; `election_windows` presents
  three undifferentiated rows with no domain-match flag, so a caller cannot tell the top-ranked
  row is off-domain without independently comparing `action_class` strings themselves.
- **CLAUDE.md §I B.11 / RS-4 escalation valve** — a factual/retrieval-shaped query is supposed to
  carry "a one-line flag with drill pointer whenever the fact touches an active contradiction" —
  a top-ranked recommendation contradicting the requested domain is exactly this case, and
  `judgment_flags` is empty in both live calls.
- **CLAUDE.md §N.8 (Earned-Signal Principle)** — `mimamsa_calibration_get`'s `filters` echo
  (query_calibration.ts:129) reports `{include_heldout, promoted_only}` as if that's the complete
  filter set applied — a caller has no signal that `domain` was silently dropped. A field that
  claims to report "filters applied" but omits a filter the caller explicitly passed is the same
  defect class as an unearned PASS/verified flag.
- **ONGOING_HYGIENE_POLICIES §C (scope-boundary enforcement) / §G (red-team cadence)** — this
  defect class (declared-but-unapplied parameter, silently dropped across a tool→primitive
  boundary) is exactly what a red-team pass or a param-parity CI gate is supposed to catch before
  ship; neither F-10 nor F-27 was caught until this manual audit corpus surfaced them.

**Reusable mechanism for the CL-03 exemplar-then-replicate harness** (the actual ask of this
lane, since F-10/F-27/F-03/F-06/F-08/F-26/F-133 are declared as the same defect shape): a
**param-parity contract test**, generated off each MCP tool's own JSONSchema/Zod input schema,
that for every declared optional/required parameter either (a) asserts the parameter changes the
tool's `result_hash` (or a stable normalized digest of the response) between two otherwise-identical
calls that differ only in that parameter's value, or (b) requires the parameter to be explicitly
declared `advisory` (informational-only, does not affect results) in the tool's own metadata. A
tool with a `domain` param that produces byte-identical `election_windows` for two different
`domain` values — as directly demonstrated in §1 above — is precisely the case this harness is
built to catch mechanically, without needing a human to manually diff two live calls the way this
diagnosis did.

**Leasing note (informational only, not this lane's problem to resolve):** `register_p1_synthesis.ts`
is currently held by stream S5 (this stream) per the plan §2.1 lease-conflict table, with an
ordered handoff to S4 once S5's lanes here are VERIFIER-passed. No edits were made to this file or
any other source file in this session — Stage D is diagnosis-only per contract.
