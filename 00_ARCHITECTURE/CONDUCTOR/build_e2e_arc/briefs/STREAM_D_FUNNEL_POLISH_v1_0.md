---
brief_id: STREAM_D_FUNNEL_POLISH_v1_0
status: ACTIVE
arc_id: build_e2e_arc
stream: D
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavFunnelPolish
branch: feat/funnel-polish
base: feature/ux-workflow-overhaul
sessions: 6
estimated_loc: ~350 across 6 files
---

# Stream D — Front-of-funnel + functional polish

Ships the functional gaps in the New Client → Cockpit handoff: form schema
extensions (Preferred name, Time zone, DD-MM-YYYY date), Places API
verification, Cancel button reality check, and end-to-end browser smoke.

## Cross-cuts read first

- `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md`
- `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/VISUAL_CONTRACT_v2.md` (Page 1 functional spec)

## Hard gates

- NO Anthropic models.
- NO touching `NewClientForm.tsx`'s visual layout / styling / typography — Stream C's surface. D edits ONLY state, validation, submit handler, schema. If a session needs to touch styling, halt and tag for coordination.
- NO breaking the existing form contract — any new fields must be optional with sensible defaults so old form submissions still work.
- NO inventing Places API keys. If the key isn't present in env, document and use the manual override path; don't hardcode.
- DD-MM-YYYY format is UI-only. API and DB still use ISO 8601 (YYYY-MM-DD). The form's submit handler converts before POST.

## §D-S1 — Form schema extension

In `platform/src/components/clients/NewClientForm.tsx`, edit ONLY the
state shape and validation:

```typescript
interface FormState {
  full_name: string
  preferred_name: string       // NEW — defaults to first word of full_name on blur
  gender: string
  birth_date_ui: string        // NEW — DD MM YYYY in UI
  birth_time: string
  birth_place: string
  latitude: string
  longitude: string
  timezone_offset: string      // existing — but now sourced from explicit TZ select
  timezone_id: string          // NEW — IANA TZ like "Asia/Kolkata"
  ayanamshas: AyanamshaId[]
}
```

Update `validate()` to accept DD MM YYYY format and convert to YYYY-MM-DD
in `birth_date` field passed to API. Default `preferred_name` to the first
word of `full_name` if user leaves blank.

Tests in `__tests__/form_schema.test.ts`:
- validate accepts DD MM YYYY, rejects malformed
- preferred_name defaults on blank
- timezone_id required

Gate: `cd platform && npm test -- form_schema.test.ts` → green.

## §D-S2 — /api/clients/create accepts new fields

In `platform/src/app/api/clients/create/route.ts`, extend the request body
type and validation to accept:
- `preferred_name?: string`
- `timezone_id?: string`

These flow into the `charts` INSERT (need to confirm `charts` schema has
columns for them; if not, add an inline migration `158_charts_preferred_name_tz_id.sql`
that adds them ALTER TABLE — coordinate with Stream A's migration runner so
it gets picked up automatically).

Update `route.test.ts` tests to assert new fields are accepted and
persisted. Backwards-compat: missing fields → use full_name as
preferred_name, compute timezone_offset from lat/lng as fallback.

Gate: `cd platform && npm test -- route.test.ts` → green.

## §D-S3 — Places API verification

Locate Places API integration:
```bash
grep -rln "google.maps.places\|Autocomplete\|GOOGLE_MAPS_API_KEY" platform/src/ | grep -v test
grep "GOOGLE_MAPS\|PLACES" platform/.env.local platform/.env.example 2>/dev/null
```

Three possible findings:
1. **Wired + key present**: verify the autocomplete actually fires + populates lat/lng/tz. Smoke with a Places API test query in `__tests__/places_autocomplete.test.tsx`. Done.
2. **Wired + key missing**: document in commit body. Add a feature-flag fallback that auto-expands the manual override accordion when no key is present. Don't hardcode a key.
3. **Not wired at all**: add the @react-google-maps/api dep + `<Autocomplete>` component to the birth_place input. Use `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` env. Fallback to manual override when key absent.

Gate: `cd platform && npm test -- places_autocomplete.test.tsx` → green
(or documented gap + manual override path verified).

## §D-S4 — Cancel button on cockpit

Locate the cockpit Cancel button:
```bash
grep -rln "Cancel\|cancelBuild\|api/build/.*cancel" platform/src/components/cockpit/
```

Three possible findings:
1. **Exists and works**: verify with a test in `__tests__/cancel.test.ts`. Done.
2. **UI exists, backend doesn't**: create `platform/src/app/api/build/[id]/cancel/route.ts` (POST endpoint that marks the build cancelled + signals the Cloud Run Job execution via gcloud — or just sets DB state and trusts the reaper). Wire the existing button.
3. **Neither exists**: build both. Endpoint as above + button in the cockpit's button bar (NOT in Stream C's visual scope — D adds the functional button, C can style it post-hoc).

This is the L1-guard footgun protection — without a working Cancel, the
L1 guard locks the user out of starting new builds.

Gate: `cd platform && npm test -- cancel.test.ts` → green.

## §D-S5 — Form-to-cockpit end-to-end (Playwright)

Create `platform/tests/e2e/new-client-flow.spec.ts`:

```typescript
test('new client form → cockpit redirect → graph renders', async ({ page }) => {
  // 1. Auth (mint session cookie via mint_session_cookie.ts in test setup)
  // 2. Navigate to /clients/new
  // 3. Fill form: name, preferred name, gender, date (DD MM YYYY), time, place, tz, ayanamshas
  // 4. Click Compute chart
  // 5. Assert redirect to /clients/<id>/build
  // 6. Assert cockpit force-graph component is mounted
  // 7. Assert all 28 pending nodes visible
})
```

Requires the dev server + Cloud SQL proxy. Brief assumes the executor can
boot both locally; if not (CI), mark this test as @ci-skip.

Gate: `cd platform && npm run test:e2e -- new-client-flow.spec.ts` → green
(or skipped with explicit note).

## §D-S6 — Final commit + cherry-pick to main

Per STREAM_COORDINATION §5. Heads up on the NewClientForm.tsx conflict
with Stream C: D's edits land on state + handlers; C's edits land on
JSX layout + class names. Three-way merge usually clean; halt if not.

Gate: `git log origin/main..HEAD --oneline | head -1` returns 0.

---

End of Stream D brief.
