---
artifact: WP7_PACKET_P2
packet_id: P-2
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of platform/src/lib/retrieval/registry/layers/reading_checklist.ts (D8 assess-domain and D9 judgment inherit this via fetchGocharaSweep)"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 P-2, §6.1 (reading_checklist row); GOCHARA_RULING_SHEET_v1_0.md N-7/N-10
authority_note: "Owed to its owner. Anchors read at this checkout (l3/gochara-autonomous-wp0-7 @ fd13ec0a6; pin c58e86662 ancestor, source identical)."
---

# P-2 — Reading checklist: carry `contact_id`, `completeness_state`, `peak_basis` through the capped page

## 1. Where the change lands (verified anchors)

`fetchGocharaSweep` at `platform/src/lib/retrieval/registry/layers/reading_checklist.ts:1011-1098`.

The page-capping happens in two places. The SQL caps at 200 rows
(`:1072-1073` — `ORDER BY ABS(w.signed_intensity) DESC NULLS LAST LIMIT 200`), then
the in-memory projection keeps only five (`:1084` — `out.windows = res.rows.slice(0, 5)`).
The SELECT at `:1063-1064` projects exactly:

```sql
SELECT w.event_class, w.temporal_shape, w.window_start, w.window_end, w.peak_date,
        w.valence, w.is_adverse
```

and the returned per-window shape is `GocharaSweepWindow` (`:975-984`):

```ts
export interface GocharaSweepWindow {
  event_class: string
  temporal_shape: string | null
  window_start: string | null
  window_end: string | null
  peak_date: string | null
  valence: string | null
  is_adverse: boolean | null
  is_past_peak: boolean | null
}
```

The window rows written under generation `'4.0'` carry `active_sentences` (the plan §4.6
restores it: "Every window row lists the `contact_id`s it rests on in `active_sentences`"),
`peak_basis`, `completeness_state` (via the projection's typed-qualification columns), and
`generation` — but **none of those columns are selected**, so the reading layer cannot
distinguish a confirmed timing window from a context-only row, and cannot trace any row
back to the contact ledger.

## 2. What must survive the cap, and why dropping it breaks Q01/Q02

Three fields, two of them in the SQL projection and one derived:

1. **`contact_id` list** (from `active_sentences` / the window↔contact join). Q01
   (identity: "is this the same claim it was last read?") is answered by id, not by
   (event_class, window_start) coincidence — windows shift under rebuilds, ids don't
   (contact_id is stable under horizon re-partitioning, WP1_CONTRACTS §3.2). Without
   it, the reading layer's windows are anonymous envelopes — exactly the F-01
   condition the elevation exists to end, reintroduced one layer up.
2. **`completeness_state`** (the F06 six-state typed qualification; N-14's nodal-dṛṣṭi
   absence is declared here, never silently dropped). Q02 (honesty: "what could not be
   qualified?") is unanswerable if a `unqualified`/`unavailable` row is flattened into
   the same list as confirmed rows — the flattening §N.6 forbids. A capped page that
   mixes them and counts 5 "windows" is a false density claim.
3. **`peak_basis`** (stored column; `GENUINE_PEAK_BASES` mirror at
   `register_gochara_windows.ts:372`). It is the reading layer's only signal for
   "genuine located extremum vs context envelope" — `deriveResolutionDisclosure`
   (`register_gochara_windows.ts:419`) treats non-argmax bases as
   `peak_basis_not_argmax` context. Dropping it makes every swept row read as a
   timing claim.

Why the cap itself is fine: §N.6 density layering wants a **trimmed display** with
**honest counts**, not a full dump. The defect is that the cap discards the
qualification data needed to layer, then counts the remainder as homogeneous.

## 3. Proposed shape change

Add to the SQL at `:1063-1064` (generation-safe: all three columns exist since
migrations 527/564 and the WP6 projection writes them; v1 rows arrive NULL, which the
interface already treats as honest-null per the file's own conventions):

```sql
SELECT w.event_class, w.temporal_shape, w.window_start, w.window_end, w.peak_date,
        w.valence, w.is_adverse,
        w.peak_basis,
        w.generation,
        w.active_sentences,                 -- jsonb: list of contact_id strings ('4.x'),
                                            -- [] / NULL for v1 rows — pass through
        w.completeness_state
```

(If `active_sentences` proves too sparse at window grain — the projection may instead
offer a window→contact join view — the fallback is a second query keyed by the 5 served
window ids; the packet does not prescribe the mechanism, only that the served rows
carry ids.)

New/extended interfaces (extending, not replacing — D8/D9 read the existing fields):

```ts
export interface GocharaSweepWindow {
  // ... existing fields unchanged ...
  peak_basis: string | null
  generation: string | null
  completeness_state: string | null        // F06 six states; null = pre-'4.x' row
  contact_ids: string[]                    // parsed from active_sentences; [] when none
  is_confirmed: boolean                    // derived: completeness_state in the confirmed
                                          // set AND peak_basis passes the argmax check
}

export interface GocharaSweepResult {
  // ... existing fields unchanged ...
  confirmed_rows_in_page: number           // §N.6: never let the raw page count read as
  context_only_rows_in_page: number        //   N confirmed timing windows
  catalog_only_note: string | null         // same pattern as summarizeResolutionDisclosure
                                          //   in register_gochara_windows.ts:530-543
  provenance: { generation: string | null; manifest_id: string | null }
}
```

Confirmed-vs-context counting (§N.6 discipline): a row counts **confirmed** iff
`is_confirmed` (above); everything else — era-resolution envelopes, `unqualified`,
`unavailable`, non-argmax peaks — counts **context_only**, and both counts are served
alongside the existing `upcoming_window_count` (which stays a raw match count per its
own disclosure comment at `:988-992`). The `note` field gains one sentence when
`context_only_rows_in_page > 0`, mirroring the existing wording style.

## 4. Acceptance test

On a disposable DB fixture: one chart, `'4.0'` windows including (a) a confirmed row
with `active_sentences=['sha256:…']`, `peak_basis='gochara_lambda_v3_argmax'`,
`completeness_state='confirmed'`; (b) an `unqualified` row; (c) a v1-generation chart
with NULL new columns. Assert: `fetchGocharaSweep` returns `contact_ids` on (a);
`confirmed_rows_in_page=1`, `context_only_rows_in_page=1`; (c) returns nulls and empty
arrays without error (the interface's existing honest-null convention). Assert D8/D9
compile and their sweep legs show the new counts without any change on their side.

## 5. What this packet does NOT do

- It does not raise the 200-row cap or the 5-window display trim — trimming at serve
  time is §N.6 policy, kept.
- It does not change the authority COALESCE predicate at `:1048-1050`/`:1069-1071`
  itself — that removal is P-1d (owned by the register_gochara_windows.ts owner); this
  packet only notes the predicate appears here too and must change in the same release.
- It does not read `kala_gochara_contacts` directly (that is P-4's capability); ids
  arrive via the windows projection's `active_sentences`.
- It does not add a confidence scalar; `is_confirmed` is a typed two-state
  qualification, not a 0–1 number.
