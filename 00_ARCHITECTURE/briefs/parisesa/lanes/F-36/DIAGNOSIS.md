# F-36 — DIAGNOSIS

Stream: S2 MĀTRĀ (as filed) · Class: CL-06, grouped with F-12/F-37/F-45 — **see
`F-12/DIAGNOSIS.md` for the shared defect-class taxonomy (§6 there), sibling census (§4), and the
BRANCH-EXISTS methodology; this doc covers what's specific to F-36 and states F-36's own,
DIFFERENT verdict.**
File: `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`
Stage: D (DIAGNOSE) · Chart: `482012f1-710e-4a25-994a-93821f5871aa`

## 1. Live reproduction — REPRODUCES (the offset-clamp claim; the `total` field is NOT broken —
see §5)

`ganita_chart_facts_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, offset=999999)`:
```json
{"content": {"shape": "pivoted", "facts": [], "returned_count": 0, "offset": 100000, "limit": 100,
  "total": 5750, "more_available": false}}
```

`ganita_chart_facts_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, offset=500000)`:
```json
{"content": {"shape": "pivoted", "facts": [], "returned_count": 0, "offset": 100000, "limit": 100,
  "total": 5750, "more_available": false}}
```

Both calls: caller passed `offset=999999` / `offset=500000`; both responses echo back
`"offset": 100000` — the clamped value — with no field anywhere disclosing that a clamp
happened, what the caller's original value was, or that `100000` is a ceiling rather than the
caller's own input. Confirmed exactly as claimed.

## 2. Claim decomposition

- **F-36a:** `offset` values above 100,000 are silently clamped to 100,000.
- **F-36b:** the clamped value is echoed back in the response under the same field name the
  caller used (`offset`), indistinguishable from an honest echo of the caller's own input.
- **F-36c (implicit):** no `offset_clamped` / `offset_requested` disclosure field exists anywhere
  in the response shape.

## 3. Mechanism → file:line — confirmed, ONE line number correction from the finding's citation

**`register_d7_channel.ts:924`** (matches the finding's cited line exactly — no drift):
```ts
const offset = Math.max(0, Math.min(Number(args['offset'] ?? 0), 100_000))
```

Response fields that echo this post-clamp variable — the finding cited `:1130-1223`; on the
current `origin/main` tip the two actual echo sites are at **`:1140`** (shape="rows" branch) and
**`:1216`** (shape="pivoted" branch, the one exercised by the live repro above since `pivoted` is
the default shape) — both inside the originally-cited range, just narrower than the full span
cited (that range also includes unrelated fields like `total`/`more_available`, which are NOT
part of this defect — see §5):
```ts
// :1132-1145 (shape="rows")
const servedRows = rows.slice(offset, offset + limit)
...
content = { ..., offset, limit, total, more_available: offset + servedRows.length < total }

// :1160-1222 (shape="pivoted", the branch actually exercised above)
const servedSubjectEntries = Array.from(bySubject.entries()).slice(offset, offset + limit)
...
content = { ..., offset, limit, total, more_available: offset + pivoted.length < total }
```
`offset` in both branches is the SAME clamped local variable from `:924` — there is no
`offset_requested` anywhere to reconstruct what the caller actually asked for.

## 4. Sibling census

Not separately re-run — same file, same `offset` variable, both branches already enumerated in
§3. No other clamp-with-silent-echo site was found specific to this tool during this pass; a
broader "silently clamped param echoed as if it were the caller's own input" census (as distinct
from F-12/F-37's `total`-arithmetic census in `F-12/DIAGNOSIS.md` §4) was out of this lane's
Stage-D budget — flagged as a possible follow-up census, not claimed as exhaustive.

## 5. IMPORTANT CORRECTION to the finding's framing — F-36 is NOT the CL-06
"total-dies-under-composition" defect at all

The campaign groups F-36 with F-12/F-37/F-45 under one class: "`total` computed as returned row
count post-LIMIT/post-clamp/post-trim instead of a true independent count." **This is factually
wrong for F-36.** Read `register_d7_channel.ts:1091-1120` (the same file, just above the
clamp-echo site):
```ts
const countSql = (shape === 'rows'
  ? 'SELECT COUNT(*)::int AS total '
  : 'SELECT COUNT(DISTINCT fact_subject)::int AS total ') + whereOnly
const countParams = [...params]
...
const countRes = await query<{ total: number }>(countSql, countParams)
const total = Number(countRes.rows?.[0]?.total ?? 0)
```
`ganita_chart_facts_get`'s `total` field is a genuine, independent `COUNT(*)` (or
`COUNT(DISTINCT fact_subject)` for the pivoted shape) run in a SEPARATE query against the SAME
`WHERE` clause, snapshotted before the row-cap parameter is appended (`:1098`, explicit comment:
"Snapshot the WHERE clause + its bound params HERE... so the count query... reflects the whole
matching set, not just this page"). The live reproduction confirms this: `total: 5750` at BOTH
`offset=999999` and `offset=500000` — a stable, correct, independent count, unaffected by the
offset clamp. This is exactly the CORRECT pattern F-12/F-37 are missing (see
`F-12/DIAGNOSIS.md` §3's contrast with `get_condition_composite.ts` — this file already does the
same right thing).

**F-36's actual defect (silent offset-clamp, no disclosure) is a different bug in the SAME file
as the correct `total` pattern.** It belongs to a DIFFERENT defect class from F-12/F-37/F-45:
"a bounding/clamping transform silently substitutes a different value for the caller's own input
and echoes it back under the original field's name, with no `_requested`/`_clamped` disclosure
pair." This is closer in spirit to CL-13 (missing disclosure, S3's lease) than to CL-06's
count-arithmetic story. The campaign's CL-06 grouping for F-36 should be corrected at the board
level; this DIAGNOSE pass treats it honestly as its own thing rather than forcing it into the
CL-06 narrative.

## 6. BRANCH-EXISTS verdict — WRONG, and doubly so

Per `F-12/DIAGNOSIS.md` §5, `ekv/a-09-sara-kernel`'s entire diff is `response_budget.ts` +
`registry_bridge.ts`, scoped to `assess_*` composition (`SaraKernel`/`assembleSaraContent`/
`buildAssessResponse`, F-56/F-111). `ganita_chart_facts_get` is not an `assess_*` tool, and its
handler (`register_d7_channel.ts`) is untouched by the branch.

Beyond that: since F-36 is not even a "count field goes stale under a generic trim/budget
transform" bug in the first place (§5 above — its `total` is already correctly independent), the
sara-kernel branch is doubly inapplicable — there is no response-composition/budgeting mechanism
to extend here at all. The actual fix is local to `register_d7_channel.ts`: either raise or
remove the 100,000 ceiling, or (more likely the SPEC-preferred fix, consistent with the
codebase's own disclosed-pagination convention already used two lines away for `total`) keep the
ceiling but add `offset_requested`/`offset_clamped` fields alongside the existing `offset` field,
the same way `more_available` already discloses a page-boundary fact honestly.

## 7. Blast radius

- **File ownership vs S2's lease:** `register_d7_channel.ts` is under
  `platform/src/lib/retrieval/registry/layers/` (not `L1_ganita/`, `L0_brahmagyan/`, etc. — it's
  a top-level registry-layer file). Checked against
  `git show origin/par/coordination:00_ARCHITECTURE/briefs/parisesa/LEASES.json`: this exact path
  is **not listed in any stream's OWNS array** (not S1, S2, S3, S4, S5, or S6). This is a lease
  GAP, not a lease conflict — the same situation LEASES.json itself documents for
  `platform-mcp/src/lib/kala_envelope.ts` before its post-Phase-0 assignment to S5. **Flagged via
  `NEEDS_LEASE.md` in this lane** with a recommendation (S5, by analogy — S5 already owns
  "capability SQL under layers/L0_*" and all `L1_ganita/**`/`L2_bodha/**` query files; this
  top-level registry-layer file is the same kind of raw-retrieval-handler code, just one
  directory up).
- **§N controls touched:** this is a disclosure gap, closest to §N.6 item 4 (density signaling is
  data, not narration) and the disclosure spirit of CL-13 (S3's lease, "gated on total emptiness
  instead of did-we-serve-less-than-asked") even though the concrete mechanism (S3's CL-13
  predicate) doesn't apply verbatim here.
- **Other lanes sharing this file:** none of S2's OWNS files are `register_d7_channel.ts`; no
  collision with S2's other lanes. Worth flagging to whichever stream ends up owning this file
  that F-9/F-17/F-18/F-43 (S1's CL-11 dead-pointer findings) and other retrieval-layer findings
  may also touch large registry-layer files like this one — no confirmed overlap found in this
  pass, noted as a watch item only.
- **A-09 sāra-kernel:** confirmed not touching `register_d7_channel.ts`.

## Evidence

Live JSON captured this session for `ganita_chart_facts_get(offset=999999)` and
`ganita_chart_facts_get(offset=500000)` (both quoted verbatim above, full envelopes in this
session's tool-call transcript).
