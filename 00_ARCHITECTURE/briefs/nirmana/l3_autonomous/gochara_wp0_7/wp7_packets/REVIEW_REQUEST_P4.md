---
artifact: WP7_REVIEW_REQUEST_P4
packet_id: P-4
status: IMPLEMENTED_AWAITING_REVIEW
date: 2026-09-24
branch: l3/gochara-autonomous-wp0-7
---

# REVIEW REQUEST — P-4 (contact-ledger + coverage read capability)

## What landed

- **New capability `platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts`**
  (new file, per packet's "new capability, not an edit to a sibling-owned
  file"): exported `queryContactLedger(input, principal)` core + MCP tool
  `gochara_contact_ledger_get`. Registered in `platform-mcp/src/server.ts`
  (one import + one registration line, the established sibling pattern).
- Request shape per packet §2 (`generation` default = explicit authority read;
  partition filters body/target_type/target_ref/relation/event_class/interval;
  horizon; `moon='on_demand'`; `include_context` default false; keyset
  `page {limit, cursor}` with cursor `(t_exact, contact_id)`).
- Response shape per packet §3: `status`, `generation`, `manifest` (null for
  legacy generations), `hard_floor {confirmed, count}` + `context_layer` only
  when asked, `coverage {partitions, searched_horizon, unavailable_inputs}`,
  `page {returned, next_cursor, confirmed_returned}`.
- **Layering rules implemented as normative:**
  1. Layers disjoint *in SQL* — the confirmed predicate
     (`completeness_state IN (...) AND target_resolution_state='resolved'`)
     vs its negation; the caller never re-separates.
  2. Floor trim-proof: `COUNT(*)` first; `confirmedCount > page.limit` ⇒
     `status='not_computed'` + `floor_overflow:true` + true count, zero
     episodes served — never a truncated confirmed list. Absolute ceiling
     `CONFIRMED_FLOOR_BUDGET=200`.
  3. `moon_on_demand` partitions quoted exactly (H-3): `searched_horizon` =
     the moon partition's own `completed_horizon`, `unsearched_reason`
     present; a MISSING moon partition is stated in `coverage.note`, never
     served as a 0-contact answer (F06).
  4. Absent authority row ⇒ `status='unpublished'` full coverage object,
     no contact/coverage SQL issued (N-10).
- **Whitelist:** `kala_gochara_contacts` added to `ALLOWED_TABLES` in
  `platform/src/app/api/mcp/db/query/route.ts` with a dated read-only comment
  (replaces P-1's "deliberately NOT added" note).
- **Index reliance:** queries lead with `(chart_id, generation)` (PK prefix)
  and use `body`/`t_exact` ordering per `idx_kgc_serve_p4`; keyset pagination
  ordered `(t_exact, contact_id)`.

## Test evidence

- New `register_gochara_contact_ledger.test.ts` — 5 tests (packet §5
  acceptance): layers disjoint (predicate in SQL, disjoint ids);
  floor-overflow under small page (not_computed, no page query issued);
  moon searched_horizon + unsearched_reason + unavailable_inputs; unpublished
  with no authority row (only the authority SELECT runs); keyset pagination
  cursor produced and consumed.
- 5/5 green. `npx tsc --noEmit` platform-mcp: 0 errors.

## Items flagged for independent review

1. **Live Moon derivation is NOT in this tool** — R7 on-demand Moon episodes
   require the kernel/sidecar (S-1's `find_episodes`, separate packet). This
   capability serves the moon COVERAGE record and says so in `coverage.note`
   rather than fabricating episodes. If the reviewer expected live Moon here,
   that belongs to S-1.
2. **Confirmed-set vocabulary** matches P-2's resolution
   (`{'confirmed','qualified'}`) — same flag: the F06 six-state enumeration
   isn't pinned anywhere in the packets.
3. **Floor budget = page.limit** (capped 200): the packet's acceptance ("page
   size smaller than the confirmed set ⇒ not_computed") pins this reading; a
   separate fixed transport budget could be argued — flagged, one-line change.
4. `context_layer` has no cursor (capped 200, noted) — the packet paginates
   the confirmed floor; context pagination unspecified.
5. Live-DB acceptance (disposable DB fixture) not runnable in this
   environment; tests mock the fetch proxy per sibling convention.
