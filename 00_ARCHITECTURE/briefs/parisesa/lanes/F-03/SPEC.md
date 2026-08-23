---
lane: F-03
stream: S5 MŪLA
campaign: PARIŚEṢA
stage: S (SPEC)
status: DRAFT — pending VERIFIER review (Stage R)
author: S5 MŪLA lead
severity: TIER2-HONESTY
---

# F-03 SPEC — `listRemediesByCategoryCapability` limit/offset no-op

## 1. Root-cause statement

`register_d7_channel.ts`'s `listRemediesByCategoryCapability` (and 2 of its 3 sibling
capabilities in the same `brahma_remedy_corpus` family) declares no `limit`/`offset` in its own
`input_schema` and applies no `LIMIT`/`OFFSET` in its SQL, even though the public alias layer
(`register_p1_aliases.ts`) forwards those params in good faith — so a populous category always
returns every matching row, and an oversized serialized result gets hard-truncated mid-JSON by
`response_budget.ts`'s generic string trimmer, which has no way to know the string it's slicing
is itself JSON.

## 2. Files to change

1. **`platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`**
   - `listRemediesByCategoryCapability` (~1528-1608): add `limit`/`offset` to `input_schema`
     (mirroring `GlobalBase`'s bounds: `limit` int 1-1000 optional, `offset` int ≥0 optional,
     sensible default e.g. `limit=50`); read `args['limit']`/`args['offset']` in the handler;
     apply `LIMIT $n OFFSET $m` to the SQL at lines 1584-1591.
   - `queryTantricRemediesCapability` (1712-1749): same three changes, SQL at 1725-1733.
     **In-lease, covered directly** — see §4.
   - `query_remedies_by_planet`'s capability (1791-1822): same three changes, SQL at
     1799-1806. **In-lease, covered directly** — see §4.
   - `queryMantrasCapability` (1863-1898): same three changes. **In-lease, covered directly**
     — see §4.
   - **All four capabilities in this file get the identical treatment** (add `limit`/`offset`
     to `input_schema`, read `args['limit']`/`args['offset']`, apply `LIMIT $n OFFSET $m` to
     each SQL block), landing in one PR.
2. No change needed to `register_p1_aliases.ts` — the alias layer for all four siblings already
   declares and forwards `limit`/`offset` faithfully (confirmed in Stage D). No change needed to
   `response_budget.ts` — confirmed not the fix target in Stage D.

## 3. Exit test

New file: `platform/src/lib/retrieval/registry/layers/__tests__/register_d7_channel.limit_offset.test.ts`

- `listRemediesByCategoryCapability({category:'mantra'})` vs
  `listRemediesByCategoryCapability({category:'mantra', limit:5})` — assert the two calls return
  **different** `result_hash` / different row counts (today: identical — this assertion FAILS on
  current code, per Stage R rule 3).
- Same paired assertion for `queryTantricRemediesCapability` (once F-05's dead-backend fix lands
  and tantric rows exist — see dependency note below, this half of the test may need a seeded
  fixture rather than live prod data since prod currently has 0 tantric rows).
- Same paired assertion for `query_remedies_by_planet` (`{planet:'Saturn'}` vs
  `{planet:'Saturn', limit:5}`) and `query_mantras` (`{}` vs `{limit:5}`) against live prod
  data — both have real non-empty rows today, no fixture needed.
- Assert `offset` behaves correctly (second page is disjoint from first page, same `limit`) for
  all four capabilities.
- Assert no response exceeds the response_budget string-truncation threshold when `limit` is
  honored at a reasonable default, closing the observed truncation symptom.

## 4. Sibling sites covered (from Stage D §4 sibling census) — coverage table

| Sibling | Same mechanism? | Disposition | Reason |
|---|---|---|---|
| `query_tantric_remedies` (`ref_tantric_remedies_get`) | YES — identical shape (schema omits limit/offset, SQL has no LIMIT) | **COVERED — built in this spec** | `register_d7_channel.ts` (the file this capability is actually in, per §4b's correction) was added to S5's lease post-Phase-0 specifically to cover F-36 + these three F-03 siblings + F-05 (conductor confirmation, 2026-08-16). PAR-R-4's file citation was wrong but its practical conclusion (in-lease) stands regardless of which of the two files was meant — both are S5's. |
| `query_remedies_by_planet` (`ref_remedies_by_planet_get`) | YES — identical shape | **COVERED — built in this spec** | Confirmed live in `register_d7_channel.ts` (§4a); that file is explicitly named in the conductor's post-Phase-0 lease addition for this exact finding. No longer reserved — conductor resolved it directly rather than leaving it to a re-ruling. |
| `query_mantras` (`ref_mantras_get`) | YES — identical shape | **COVERED — built in this spec** | Same file, same conductor lease addition, explicitly named alongside `query_remedies_by_planet`. Earlier `PAR-F-03-NEEDS-LEASE` flag WITHDRAWN — superseded by the lease addition, not by this lane resolving it unilaterally. |

### 4b. CORRECTION to PAR-R-4's lease note (found while doing §4a's check, FM-09 applied to a ruling)

PAR-R-4's "Lease note" states: *"Two of the three addresses resolve to
`platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts` — inside S5's lease
(`L2_bodha/**`)... But the third address, `register_d7_channel.ts`, sits at the `layers/` root
and matches none of S5's globs."*

**Directly verified against source — this premise does not hold:**
- `L2_bodha/query_remedies.ts` registers exactly ONE capability: `query_remedies`
  (`uri: 'marsys://tool/L2/query_remedies'`, line 233/236). It does not register
  `query_tantric_remedies`, `query_remedies_by_planet`, or `query_mantras` anywhere — the only
  occurrence of any of those three names in that file is a passing comment at line 342, not a
  registration.
- All three are, in fact, registered in `register_d7_channel.ts`:
  `name: 'query_tantric_remedies'` (line 1674), `name: 'query_remedies_by_planet'` (line 1757),
  `name: 'query_mantras'` (line 1830) — matching exactly what F-03's own Stage D diagnosis
  already established independently, with function bodies and SQL quoted.

This is a factual location error in PAR-R-4's lease note, not a difference of judgment about
lease policy — verified three independent ways (F-03's original Stage D diagnosis, this SPEC's
own §4a grep for the conductor, and a direct re-grep for `name: '...'` just now). **Not acting
on either conclusion this could imply** (building all three as in-lease, or treating them all as
needing `NEEDS-LEASE`) — per PAR-R-7, a factual dispute underneath a ruling is exactly the kind
of thing to post and wait on, not resolve by picking the alternative reading myself. Flagging
`PAR-R-4-FILE-CORRECTION` to the conductor/PRATINIDHI.

**Resolution (conductor, 2026-08-16):** practically moot — `register_d7_channel.ts` was already
added to S5's lease post-Phase-0 specifically for these findings (LEASES.json note: "resolves
F-36's lease gap + F-03's `query_mantras`/`query_remedies_by_planet` siblings + S5's own F-05,
all confirmed live in this file"). Whether PAR-R-4 meant `L2_bodha/query_remedies.ts` or
`register_d7_channel.ts`, both are S5's — no re-ruling needed on the routing question itself.
Conductor is separately annotating LEASES.json crediting the correction for the record. §4
above updated: all three siblings now COVERED.

### 4a. Definitive file resolution for `query_remedies_by_planet` (conductor's 30-second-check ask, 2026-08-16)

Grepped all 4 candidate files the conductor named for `query_remedies_by_planet\|remedies_by_planet`:

| File | Result |
|---|---|
| `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts` | **LIVE registration.** `uri: 'marsys://tool/L0/query_remedies_by_planet'` (~1754), `name: 'query_remedies_by_planet'` (~1757), handler + SQL at 1791-1822/1799-1806 (per Stage D). Same file, same `brahma_remedy_corpus` capability family, same pattern as the already-cleared `query_tantric_remedies`. |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts` | Only a comment mentioning the name (line 342) — not a registration. Not the home. |
| `platform-mcp/src/tools/register_p1_aliases.ts` | The public alias `ref_remedies_by_planet_get` (1607-1614) forwards to the `query_remedies_by_planet` primitive — this is the already-cleared, correctly-wired alias layer, not a second bug site. |
| `platform-mcp/src/tools/retrieval/remedy_tools.ts` | A SECOND, legacy registration of the raw name `query_remedies_by_planet` exists here (`registerRemedyTools`, wired into `server.ts:444`) — **but this exact name is listed in `DEPRECATED_MCP_TOOL_NAMES`** (`platform-mcp/src/lib/deprecated_tool_gate.ts:44-67`) and is unconditionally gated off the live MCP `tools/list` surface (`deprecated_tool_gate.ts`'s own header: "the go-forward MCP surface exposes ONLY the canonical `layer_noun_verb` faces... removing the legacy MCP registration drops zero capability"). Confirmed dead/unreachable via the live server — not a live bug site. |

**Definitive answer: `register_d7_channel.ts` is the one live home**, identical file and pattern
to `query_tantric_remedies`. Reported back to the conductor for routing per PAR-R-7; conductor
resolved it directly (§4b) — now COVERED, built alongside the other three capabilities in §2.

**Note on the glob-vs-ruling discrepancy:** `register_d7_channel.ts` physically lives at
`platform/src/lib/retrieval/registry/layers/register_d7_channel.ts` — a flat file directly under
`layers/`, not nested inside `L0_*/`, `L1_ganita/`, or `L2_bodha/`. Taken purely as a path glob,
none of the four capabilities in this file would match S5's literal OWNS text. PRATINIDHI's
ruling that `query_tantric_remedies` (and, by prior Stage-D precedent, F-05/F-06's mechanisms in
this same file) IS in-lease implies leasing here is being decided by **capability domain**
(remedy-family capabilities → S5, since S5 already owns the CL-02/CL-03 remedy findings F-03/
F-05/F-06), not literal path-glob matching. This spec does not attempt to resolve that
discrepancy itself — flagging it explicitly is the Stage-S-honest move; the conductor/PRATINIDHI
own reconciling §2's OWNS text if the domain-based reading is meant to stand.

## 5. Recurrence guard

The exit test itself (§3) is the immediate guard for all four capabilities now that all four are
covered. The stream-level recurrence guard is the CL-03 shared harness (spec'd separately off
the F-10 exemplar lane): a generated param-parity contract test that walks every registered
capability's JSONSchema and asserts every declared parameter provably changes `result_hash` or
is explicitly marked advisory — this becomes the permanent regression guard once both this
lane's point fix and the harness land, so a fifth sibling introduced later fails CI instead of
waiting for the next manual audit.

## 6. Dependencies and rollback note

- **F-05 dependency (soft, not blocking):** `queryTantricRemediesCapability`'s limit/offset fix
  is currently untestable against live data because `brahma_remedy_corpus` has zero `tantric`
  rows (F-05, separate S5 lane, dead-backend). The exit test uses a seeded fixture for this half
  until F-05 lands; re-run against live prod data once F-05 is built to confirm end-to-end.
- **`query_remedies_by_planet` / `query_mantras`:** no longer blocked — both confirmed in-lease
  by the conductor's post-Phase-0 `register_d7_channel.ts` addition (§4b). Both have real
  non-empty prod data today; their exit-test assertions need no fixture.
- **Rollback:** single-file change (`register_d7_channel.ts`), additive (new optional schema
  fields + a `LIMIT`/`OFFSET` clause with safe defaults, applied identically across all four
  capabilities) — no data migration, no orchestrator contract touch. `git revert` is sufficient;
  no special rollback sequencing needed.

## 7. Sub-claim coverage (from Stage D §2 claim decomposition)

| Sub-claim (Stage D §2) | Addressed by |
|---|---|
| (a) limit/offset no-ops in the handler | §2 file change: add schema fields + read args + apply SQL clause |
| (b) entire category always fetched | Same — `LIMIT`/`OFFSET` bounds the fetch |
| (c) response_budget truncation produces invalid JSON | Indirect fix: honoring `limit` at a sane default keeps responses under the truncation threshold for the common case; `response_budget.ts` itself is unchanged (confirmed not the fix target) — a caller requesting an unbounded `limit` can still hit truncation, which is correct behavior (their choice), not a residual defect of this finding |

## Provenance

Supersedes the earlier `lanes/F-03/SIBLING_DEFECTS_OUT_OF_SCOPE.md` note (deleted). That note
incorrectly treated all 3 Stage-D-discovered siblings as pure scope-creep per an initial
conductor instruction; PRATINIDHI's actual ruling (PAR-R-4) distinguishes "new mechanism" (true
scope-creep, correctly refused) from "new call site of the same already-diagnosed mechanism"
(must be covered or excluded-with-reason in this SPEC, not deferred to a handoff note). This
SPEC.md is the corrected artifact.
