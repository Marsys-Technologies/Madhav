---
lane: F-03
stream: S5 MŪLA
campaign: PARIŚEṢA
stage: D (DIAGNOSE)
finding_id: F-03
status: CONFIRMED-LIVE (not fixed) — with a corrected mechanism location
severity: TIER2-HONESTY
date: 2026-08-16
---

# F-03 — ref_remedies_by_category_list limit/offset no-op — Stage D diagnosis

## 1. Live reproduction

Called both arg sets live against `mcp__marsys-jis-direct__ref_remedies_by_category_list`:

- **A:** `{category: 'mantra'}` → `result_hash: sha256:ad8a27bbdc37a7b8f37586af5bfcaee7463895dd36599891073203a45008006c`
- **B:** `{category: 'mantra', limit: 5}` → `result_hash: sha256:ad8a27bbdc37a7b8f37586af5bfcaee7463895dd36599891073203a45008006c`

**Hashes are identical**, and match the corpus's own predicted "if unfixed" hash exactly. `limit: 5`
had zero effect on the returned data. Both responses' `results[0].content` is a JSON string that was
hard-truncated at 120 chars with `…[truncated for budget]` (see §2c) — the same truncation marker on
both calls, confirming the same oversized payload hit `response_budget.ts` both times. Full raw
JSON for both calls saved to `lanes/F-03/repro_raw.json`.

**Verdict: CONFIRMED-LIVE, not fixed.**

## 2. Claim decomposition

**(a) limit/offset are no-ops in the underlying handler — CONFIRMED**, but not in `remedy_tools.ts`
as the corpus states — see §3 for the corrected location. The live handler's `input_schema` doesn't
even declare `limit`/`offset` as accepted fields, and its SQL has no `LIMIT`/`OFFSET` clause at all.

**(b) the entire category is always fetched — CONFIRMED.** The SQL (`SELECT ... FROM
brahma_remedy_corpus WHERE LOWER(remedy_type) = $1 OR LOWER(category) = $2 OR LOWER(category) = $1
ORDER BY planet, remedy_id`) has no row cap of any kind. `mantra` matched enough rows that the
serialized JSON exceeded the 40KB response budget (`budget_kb_applied: 40` in both responses).

**(c) response_budget truncation produces invalid embedded JSON — CONFIRMED.** Both live responses
show `results[0].content` — itself a JSON string (`"{\"category\":\"mantra\",\"remedies\":[...`) —
truncated mid-character with the literal marker `…[truncated for budget]`. A caller that tries to
`JSON.parse()` that string gets a syntax error with no recovery path other than falling back to
`response_format:legacy` per `recover_via` (which the caller has to know to ask for).

## 3. Mechanism to file:line — CORRECTED from the corpus citation

The corpus's cited mechanism file (`platform/src/lib/retrieve/remedy_tools.ts:171-188`) is **stale
dead code for this call path**, not the live implementation. That file's own docstring (lines 1-22)
says it is `RETIRED / DEPRECATED — lib/retrieve layer (legacy chat-route pipeline)`. The actual live
call path for `ref_remedies_by_category_list` is:

1. `platform-mcp/src/tools/register_p1_aliases.ts:1570-1580` — `ref_remedies_by_category_list`
   registers `{ category: z.string()..., ...GlobalBase }` (line 1573; `GlobalBase` = `{ limit:
   z.number().int().min(1).max(1000).optional(), offset: z.number().int().min(0).optional() }`,
   defined at lines 323-326), destructures `{ category, limit, offset }` (line 1574), and forwards
   all three to `callPlatformPrim('list_remedies_by_category', { category, limit, offset },
   principal)` (line 1576). **This alias layer is correctly wired** — it declares and forwards
   `limit`/`offset` in good faith.
2. `callPlatformPrim` (same file, lines 98-120) POSTs to
   `platform/src/app/api/mcp/primitives/[tool]/route.ts`.
3. That route (lines 155-159) resolves `'list_remedies_by_category'` via
   `MCP_TO_RETRIEVAL_TOOL` / `getToolByName` (`platform/src/lib/retrieval/registry/
   tool_name_bridge.ts:124, 330-`) to URI `marsys://tool/L0/list_remedies_by_category`, and calls
   `tool.retrieve(plan, params)` (route.ts line 257).
4. That URI is registered in
   `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1528-1608`
   (`listRemediesByCategoryCapability`). **This is the actual live bug site:**
   - `input_schema` (lines 1546-1553) declares only `category` — `limit`/`offset` are not in the
     schema at all.
   - `handler(args)` (lines 1571-1607) reads only `args['category']` (line 1572); it never reads
     `args['limit']` or `args['offset']`.
   - The SQL (lines 1584-1591):
     ```sql
     SELECT remedy_id, planet, domain, category, remedy_type, deity,
            prescription_text, mantra_text, mantra_sanskrit,
            cost_tier, source_canonical_id, classical_attestation_text
     FROM brahma_remedy_corpus
     WHERE LOWER(remedy_type) = $1 OR LOWER(category) = $2 OR LOWER(category) = $1
     ORDER BY planet, remedy_id
     ```
     has no `LIMIT`/`OFFSET` at all — every matching row is always fetched.
5. The oversized result hits `platform-mcp/src/lib/response_budget.ts`'s
   `truncateLongStringsInPlace` (lines 457-492; corpus said 462-488 — close, drift of a few lines),
   which walks the response tree and hard-slices any string over `MAX_STRING_CHARS = 120` (line 454)
   to `current.slice(0, 120) + '…[truncated for budget]'` (line 488), with no awareness that the
   string it's slicing is itself serialized JSON.

**Net correction to the corpus's mechanism claim:** the underlying defect (limit/offset silently
discarded → unbounded fetch → mid-JSON truncation) is real and confirmed live, but it lives in
`register_d7_channel.ts`'s `listRemediesByCategoryCapability` handler, not in the retired
`lib/retrieve/remedy_tools.ts`. The `register_p1_aliases.ts:1576-1583` half of the corpus's citation
is correct (module/line numbers drifted slightly: actual alias block is 1570-1580, forwarding call
is line 1576, not 1576-1583 as a range — it's one line).

## 4. Sibling census

Searched `platform/src/lib/retrieve/*.ts` (all dead code for this call path — `remedy_tools.ts`,
`sutravali_tools.ts`, `pyhora_*.ts`, `index.ts` — none read `params?.limit`/`params?.offset` at all,
but none of them are reachable via the MCP surgical-primitive route, so they're out of scope for a
live sibling) and the live registry file `platform/src/lib/retrieval/registry/layers/
register_d7_channel.ts`, cross-referenced against `register_p1_aliases.ts`'s alias declarations.

**3 confirmed live siblings**, all in the same `brahma_remedy_corpus` capability family in
`register_d7_channel.ts`, all reached by an alias that spreads `...GlobalBase` (declares
`limit`/`offset`) but whose registry `input_schema` doesn't declare either field and whose SQL has
no `LIMIT`/`OFFSET`:

| Capability (register_d7_channel.ts) | Alias (register_p1_aliases.ts) | Handler lines | SQL lines |
|---|---|---|---|
| `query_tantric_remedies` | `ref_tantric_remedies_get` (~1596-1600, spreads `params` incl. GlobalBase limit/offset) | 1712-1749 | 1725-1733 (no LIMIT) |
| `query_remedies_by_planet` | `ref_remedies_by_planet_get` (1606-1612, explicit `{ planet, limit, offset }`) | 1791-1822 | 1799-1806 (no LIMIT) |
| `query_mantras` | `ref_mantras_get` (~1618-1624, spreads `params` incl. GlobalBase limit/offset) | 1863-1898 | 1874-1882 (no LIMIT) |

**Checked and NOT siblings** (correctly honor their row-cap parameter, or never claim one):
- `query_remedies_for_chart` (register_d7_channel.ts:1438-1526) — real `LIMIT $2` bound to `top_k`;
  its alias forwards `top_k`, not `limit`.
- `query_sutravali_rules` (313-395), `query_sutravali_rules_for_planet` (400-473),
  `list_sutravali_rules_by_text` (545-620) — all read `args['limit']`/`args['offset']` and forward
  them to the Python sidecar as real query params.
- `list_classical_texts` (1977-2024) — no `limit`/`offset` in its `input_schema` or description; it
  explicitly returns "the full text roster" by design — no false promise being broken.
- `find_verses_about` (2028-) — uses `top_k`, a different parameter name not implicated by this
  finding class.

So the CL-03 no-op-params defect class has **4 confirmed live instances** total in this file:
F-03 itself (`list_remedies_by_category`) plus the 3 siblings above — all four in the
`brahma_remedy_corpus` capability group of `register_d7_channel.ts`.

## 5. Blast radius

- **`register_p1_aliases.ts` lease (S1, CL-11 dualOutput sweep):** noted, not touched, no diagnosis
  edit proposed against it. But worth flagging for the eventual fix-lane: the alias layer for all 4
  siblings is **already correctly wired** — `GlobalBase`'s `limit`/`offset` zod fields are declared
  and forwarded faithfully in every case checked. The real fix target is entirely inside
  `register_d7_channel.ts` (add `input_schema.limit`/`.offset` + read `args['limit']`/`args['offset']`
  + apply `LIMIT`/`OFFSET` in each of the 4 SQL statements) — a fix may not need to touch
  `register_p1_aliases.ts` at all, which would sidestep the S1 lease dependency. This should be
  confirmed with S1/S5 lead before the shared param-parity harness lane starts, since it changes the
  lease's relevance to this finding.
- **`response_budget.ts` (S2's HOT file):** **not the fix target**, confirmed. Its
  `truncateLongStringsInPlace` is a generic last-resort trimmer operating correctly on whatever tree
  it's handed; the defect is entirely upstream (unbounded fetch). The truncation behavior is the
  *symptom* (turns a large-but-valid payload into invalid embedded JSON) — fixing the SQL/handler to
  honor `limit` removes the oversized-payload condition that triggers the trim path for this tool,
  without any change needed in `response_budget.ts` itself.

## Raw evidence

Full repro JSON (both calls) saved to `lanes/F-03/repro_raw.json`.
