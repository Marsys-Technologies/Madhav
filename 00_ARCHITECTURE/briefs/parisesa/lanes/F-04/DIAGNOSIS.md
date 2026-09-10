---
finding: F-04
lane: S5-MULA / F-04 (CL-02 dead-backend class)
stage: D (DIAGNOSE)
status: DIAGNOSIS-COMPLETE
board_label_was: DIAGNOSIS-INCOMPLETE (stale — the audit corpus already carried a full
  RESOLVED mechanism write-up; this artifact re-verifies it live and formalizes it)
verified_date: 2026-08-16
verified_against: live prod DB via mcp__marsys-jis-direct, worktree
  .claude/worktrees/par-s5-lead @ 5ff46c2a0
severity: TIER2-HONESTY
---

# F-04 Diagnosis — ref_nakshatra_get dead-backend / false-absence narration

## 1. Live reproduction — CONFIRMED STILL LIVE (not already-fixed)

`mcp__marsys-jis-direct__ref_nakshatra_get({nakshatra: 'purva_bhadrapada', limit: 5})`
called live today (2026-08-16). Raw envelope saved to `repro_raw.json` (sibling file, this
directory).

Result confirms the finding exactly as filed:
- `structured_filter_applied: false`
- `fallback_reason: "No structured bg_nakshatra catalog table exists — this is a
  classical-text hybrid search using the nakshatra/lord/keyword filter as the search query,
  not a WHERE-clause match."`
- The 5 rows served are classical-text hybrid-search hits from `muhurta_chintamani`,
  `brihat_samhita`, and `bphs` — none of which is a Purva Bhadrapada catalog record. Two of
  the five (`brihat_samhita:PG1005:C2`, `bphs:PG513:C2`) are OCR-garbled fragments
  ("One born in Punarvasu will be—", "lord of Dasa, ihe Bhal'at and Bhabhog...") that are not
  usable even as classical-text answers, let alone as the promised structured fields.
- None of the tool description's promised fields (lord, devata, gender, gana, varna, nadi,
  pada lords, body part, symbol) appear anywhere in the response.

**Verdict: NOT already-fixed. The defect described in the corpus is live in production today.**

## 2. Claim decomposition

a. **Tool description promises structured fields** — confirmed.
   `register_p1_reference.ts:415-419`: "Returns the 27 (or 28) nakshatra definitions: lord,
   devata, gender, gana (divine/human/demon), varna, nadi, pada lords, body part, symbol, and
   classical associations."

b. **Always routes through classical-text hybrid search instead** — confirmed. No
   conditional branch exists in the handler; every call (regardless of `nakshatra`/`lord`
   params) unconditionally calls `query_classical_texts`.

c. **The `fallback_reason`/inline comment actively assert the structured table doesn't
   exist — a §N.7-class narration-fidelity violation, not just a missing feature.** Confirmed,
   and this is the sharper part of the finding: it is not merely "unwired," the code
   *narrates a specific false claim* ("No structured bg_nakshatra catalog table exists") to
   every caller of this tool. §N.7 item 4 ("A verification flag must have a real detector
   behind it, or be null") and item 6 ("An honest null beats an invented judgment") both bear
   directly — this is a hardcoded false assertion, not an honest null. Flagging per Stage-D
   contract item 2c.

d. **The structured table genuinely exists, is populated, and is correct** — confirmed, and
   re-verified beyond the census's DB check. `platform/supabase/migrations/238_bg_nakshatra_tables.sql`
   creates `reference_nakshatra` (28 rows, canonical per migration 302's deprecation of the
   legacy plural `reference_nakshatras`) with exactly the columns the tool description
   promises: `vimshottari_lord`, `presiding_deity`, `nakshatra_gender`, `gana`, `varna`,
   `nadi`, `body_part`, `symbol` (plus `reference_nakshatra_pada` for pada lords — migration
   238 §2). It is actively read as the L1 authority by `ga_nakshatra.py`,
   `ga_sensitive_degree_writer.py`, `l0_kp_sublord_division.py`, and the independent
   Vimshottari verifier (`_vimshottari_independent_verifier.py`) — i.e. this is not a stale or
   abandoned table, it is the live authority other L0/L1 writers already depend on. Migration
   306 shows it is still being actively maintained/corrected (body_part alignment fix).

## 3. Mechanism — file:line (re-read against current worktree; lines have drifted slightly
   from the corpus's cited 410-447)

File: `platform-mcp/src/tools/register_p1_reference.ts`

Handler now spans **lines 412-449** (registration comment at 412, `server.tool(...)` block
413-449); the corpus's citation of 410-447 is off by ~2-3 lines but points at the same
mechanism — not a stale reference, just minor line drift from intervening edits.

```
440   return dualOutput(envelope({
441     structured_filter_applied: false,
442     fallback_reason: 'No structured bg_nakshatra catalog table exists — this is a classical-text hybrid search using the nakshatra/lord/keyword filter as the search query, not a WHERE-clause match.',
443     ...dataObj,
444   }, 'ref_nakshatra_get'))
```

and the call site:

```
435   const kw = [keyword, nakshatra, lord, 'nakshatra'].filter(Boolean).join(' ')
436   const data = await callRegistryCapability('marsys://tool/L0/query_classical_texts', {
437     query_text: kw, limit: limit ?? 30, offset: offset ?? 0,
438   }, principal)
```

Both the `fallback_reason` string (line 442) and the unconditional `query_classical_texts`
call (line 436) are confirmed present, unchanged in substance, in the current worktree.

## 4. Sibling census

**F-22 is directly adjacent in the same file, same exact shape** — `ref_dasha_systems_get`,
lines 379-409, immediately precedes `ref_nakshatra_get`. Its fallback_reason (line 403):
"No structured bg_dasha_systems catalog table exists — this is a classical-text hybrid
search..." — word-for-word the same false-absence pattern, against `brahma_dasha_systems`
(confirmed real/populated by CL02_CENSUS.md, 20 rows live). Confirmed same-shape, confirmed
adjacent (30 lines apart, both under the "P1 Group 2 — Reference-layer tools" file header).

Full sibling grep of `register_p1_reference.ts` for `fallback_reason`/`structured_filter_applied`
turns up **one more related-but-distinct case**: `ref_dignity_reference_get` (~line
340-365) — this one is a *partial* fallback: `structured_filter_applied: true` when a row is
found (line 343) and only degrades to classical-text search per-planet when no structured row
exists (line 359-361, message scoped to the specific `planet` param, not an absolute
"no table exists" claim). This is architecturally sound (it does query the structured table
first) and is not part of the F-04/F-22 defect class — no diagnosis action needed here.

Repo-wide grep for `query_classical_texts` call sites outside this file: `register_p1_aliases.ts:990`
and `registry_bridge.ts:2733/2747` (the latter is the actual proxy implementation, not a
caller-with-false-fallback). `register_p1_aliases.ts:990` was not inspected further — out of
this lane's F-04 scope but worth a one-line flag for whoever owns alias-tool census.

**Sibling count for the exact F-04 pattern (unconditional fallback + false absence claim
against a real, populated table): 2 — F-04 (`ref_nakshatra_get`) and F-22
(`ref_dasha_systems_get`), both in `register_p1_reference.ts`, 30 lines apart.**

## 5. Blast radius — corpus claim partially verified, one important correction

Corpus claim: "the fix is a one-URI-string change... not new development." **This is TRUE
for sibling F-22, but NOT fully true for F-04 as filed — important nuance for the S-stage
spec:**

- **F-22 (`ref_dasha_systems_get`) — genuinely a one-URI-string repoint.** A complete, tested,
  already-registered structured capability exists:
  `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dasha_systems.ts`
  (`marsys://tool/L0/query_dasha_systems`, backed by `brahma_dasha_systems`, with its own
  `__tests__/query_dasha_systems.test.ts`). The fix really is swapping the
  `callRegistryCapability('marsys://tool/L0/query_classical_texts', ...)` call at line 397 for
  a call to `query_dasha_systems` — no new backend code.

- **F-04 (`ref_nakshatra_get`) — no equivalent structured capability exists yet.** Grepped
  `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` directly (the source registry,
  not the generated surface profile): the only nakshatra-adjacent capability is
  `query_nakshatra_medical.ts`, which wraps a **different, narrower table**
  (`bg_nakshatra_medical`, 27 rows, body-part-only) — not `reference_nakshatra`. No
  `query_nakshatra_catalog` (or equivalent) capability targeting the full
  `reference_nakshatra` (+`reference_nakshatra_pada` for pada lords) table exists anywhere in
  the registry today (confirmed via grep of both the generated surface profile and the source
  `L0_brahmagyan/` directory).

  **Correction to carry into the S-stage spec:** F-04's fix is a *small, template-following
  new capability* (one new file mirroring `query_dasha_systems.ts`'s ~60-line structure,
  targeting `reference_nakshatra`/`reference_nakshatra_pada`, registered under
  `marsys://tool/L0/query_nakshatra_catalog` or similar) **plus** the repoint in
  `register_p1_reference.ts`. It is low-risk and pattern-matched (not exploratory
  development), but it is not literally "change one URI string" the way F-22 is — that exact
  phrase should not be reused verbatim for F-04 in the spec without this caveat.

## Summary for BOARD update

Board's `DIAGNOSIS-INCOMPLETE` label for F-04 was stale. This lane confirms the corpus's
prior RESOLVED mechanism write-up is accurate and still live in production, adds the §N.7
narration-fidelity framing explicitly, confirms F-22 as an adjacent same-shape sibling in the
same file, and corrects the blast-radius claim: F-22 is a pure repoint, F-04 needs one small
new capability file first. Recommend board status → `DIAGNOSIS-COMPLETE`, ready for S-stage.
