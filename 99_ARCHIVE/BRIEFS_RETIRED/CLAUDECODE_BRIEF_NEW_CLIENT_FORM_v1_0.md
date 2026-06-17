---
canonical_id: CLAUDECODE_BRIEF_NEW_CLIENT_FORM
version: 1.5
status: R5_VERIFIED_COMPLETE_LOCALHOST
authored: 2026-06-06
amended: 2026-06-07
author: Cowork (planning)
executor: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: New-Client Form — R2 centered-card redesign + Places root-cause + collapsed coords
branch: feature/new-client-form-reskin
supersedes: none
implementation_notes: |
  R1 (v1.1) implemented 2026-06-06 on feature/new-client-form-reskin (W1–W8 shipped).
  R1 Step 0 findings: 0.1 only NewClientForm calls /api/clients/create; 0.2 central
  formatter = @/lib/utils/date formatDate() → dd-MMM-yyyy (UTC); 0.3 charts PK = id
  (route fixed chart.chart_id → chart.id); 0.5 deploy-web job wires the Maps key from
  GitHub secret correctly.
  R2 (v1.2) — native reviewed R1 in Chrome at localhost:3000/clients/new (2026-06-07)
  and rejected the layout: strict no-scroll was followed too literally, squeezing the
  whole form into the top third with the bottom ~55% as dead black space, unequal
  column heights, manual-coords accordion open by default, and a clipped footer bar.
  Native chose Option A (centered card) over the full-bleed two-column. See §R2 below —
  it is the CURRENT ASK and supersedes §D.1's two-column layout instruction.
  PLACES CONFIRMED DEAD via Chrome diagnostic: window.google=false, no
  maps.googleapis.com script injected, scriptSrcs=[]. Root cause = NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
  ABSENT in the environment (component logic correct; isGoogleMapsKeyConfigured()→false
  so <Autocomplete> never mounts, manual fallback shows). Localhost fix: add the key to
  platform/.env + restart next dev. Prod fix: set GitHub secret + fresh build (build-time baked).
changelog:
  - v1.5 (2026-06-07) — §R5 added. Cowork re-verified R4 build (ddb5f2bd) on localhost:
    R4.3 landed (fields always visible) but fetchFields STILL not firing — Dublin select
    left lat/lng value="" and no Place-Details request. Plus: remove tz/offset UI fields
    (derive via Google Time Zone API + send silently; needs Time Zone API enabled on key —
    Cowork to check GCP), and fix Manual override toggling on any page click. §R5 CURRENT ASK.
  - v1.4 (2026-06-07) — §R4 added. Cowork Chrome-verified the R3 build: R3.1–R3.8 work
    (dropdown now visible, checkboxes one line, themed controls, calendar). But DOM+network
    inspection found R3.9 is broken — place-select fires no fetchFields/Place-Details call,
    so lat/lng state stays EMPTY (the visible 20.2961/85.8245 are placeholders). Handler is
    still on the legacy getPlace() pattern; new PlaceAutocompleteElement needs
    gmp-select → place.fetchFields(['location',…]). Amended same day with R4.3 (lat/lng
    ALWAYS visible, read-only by default, editable only on Manual override) and R4.4
    (birthplace bg = page --brand-ink). §R4 is the CURRENT ASK.
  - v1.3 (2026-06-07) — §R3 punch-list added after native reviewed the R2 build (commit
    33699024) live in Chrome. R2 confirmed shipped (centered card, palette, no-scroll,
    Places API 200s). R3 = refinements: icon-only back link beside title, remove subtitle
    + node-count microcopy, ayanamsha checkboxes on one line, birthplace dropdown
    visibility fix (closed-shadow-DOM popup clipped by card overflow), and theme the
    gender/date/time controls + add a date calendar picker. Amended same day with R3.9
    (lat/lng auto-fill on place-select + checkbox-gated manual override) and R3.10
    (elevation deliberately excluded — engine is geocentric, verified). §R3 is the CURRENT ASK.
  - v1.2 (2026-06-07) — §R2 added: Option A centered-card redesign (supersedes §D.1
    two-column), manual coords collapsed-by-default, R2.5 palette-deepening (near-black
    surfaces + gold, minimize grey), and W9 — migrate to PlaceAutocompleteElement after
    Chrome confirmed the legacy Places Autocomplete API is dead for new keys (key now in
    platform/.env; SDK loads + authenticates but returns 0 suggestions). Native rejected
    the R1 squeezed layout after Chrome review.
  - v1.1 (2026-06-06) — Added §D Design System (canonical tokens + reference
    components), the back-link, the ॥ Nava Jātaka ॥ rename, strict single-viewport
    no-scroll two-column layout, and work items W6–W8. Renamed buttons to
    Cancel / Save chart / Build chart. Title decision + layout decision recorded.
  - v1.0 (2026-06-06) — Initial: wiring fix, 3-button footer, dd-MMM dates, feedback, Places.
---

## §R5 — VERIFIED COMPLETE (2026-06-07, commit 2c99176a) — place-select coords + tz derivation + override fix

> COWORK CHROME-VERIFIED ON LOCALHOST 2026-06-07. All AC31–AC33 PASS:
> - Dublin select → GetPlace 200 + lat/lng = 53.3498053 / -6.2603097 (real, read-only).
> - Time Zone API (timezone/json) 200 — derived silently; tz/offset UI fields removed.
> - Second place (Tokyo) → lat/lng updated to 35.6764225 / 139.650027 (no stuck value);
>   a second timezone/json 200 fired for the new coords.
> - Manual override stays unchecked on stray page clicks; only its checkbox toggles it.
> - Time Zone API confirmed ENABLED on the key (both calls returned 200).
> Nothing further required on R5. Section retained for history.

## §R5 — (original ask) Place-select STILL not capturing coords; remove tz/offset fields

> Cowork re-verified the R4 build (commit ddb5f2bd) live on localhost. R4.3 landed (lat/lng
> + tz/offset now always visible), BUT the core bug PERSISTS: selecting "Dublin, Ireland"
> left `latitude.value=""` and `longitude.value=""` (DOM-confirmed; the 20.2961/85.8245 are
> still placeholders), and NO `places.googleapis.com` Place-Details request fired on select.
> So R4.1's fetchFields wiring is still not working. Plus two new asks. §R5 is the CURRENT
> ASK and wins over §R4/§R3/§R2/§D on conflict.

**R5.1 — fetchFields STILL not firing — the place-select handler is not wired to the element.**
- Confirmed again: no Place-Details/fetchFields network call on selection → coords never
  retrieved → lat/lng state empty. The R4.1 attempt did not take.
- The executor MUST debug the actual event, not re-submit the same pattern. Concretely:
  - Add a temporary `console.log` in the selection handler and confirm in the browser
    console that it FIRES on pick. If it doesn't fire, the event name/listener is wrong —
    `PlaceAutocompleteElement` dispatches **`gmp-select`** (current) with
    `event.placePrediction` → call `event.placePrediction.toPlace()` then
    `await place.fetchFields({fields:['location']})`. Older docs use a `gmp-placeselect`
    /`place_changed` event or an `event.place` — the exact shape depends on the installed
    `@googlemaps/extended-component-library` / Maps JS version. Inspect the actual event
    object (`console.dir(event)`) and read `location` off the resolved Place.
  - If the handler fires but coords are still empty, the bug is in reading the Place —
    log the resolved `place` and confirm `place.location.lat()/lng()` exist (note
    `location` may be a `LatLng` needing `.lat()`/`.lng()`, or a literal `{lat,lng}`).
  - Acceptance is a VISIBLE Place-Details/fetchFields network request on select AND
    non-empty lat/lng in the DOM. Cowork will check both in Chrome.
- Add a unit test that drives the REAL event the element emits (dispatch a `gmp-select`
  with a mock placePrediction whose `toPlace().fetchFields()` resolves a known location)
  and asserts lat/lng state is set — so a green test actually proves the wiring.

**R5.2 — Remove the Timezone and UTC offset FIELDS from the UI (but still derive + send them).**
- Native: timezone + UTC offset are always a function of the location and are never
  user-edited, so remove both form fields entirely.
- They are STILL REQUIRED by the API + engine — so derive them silently and include them
  in the submit payload (`timezone_id`, `tz_offset`):
  - On place-select, after getting lat/lng, call the **Google Time Zone API** with the
    lat/lng (and a reference timestamp) to get the exact IANA `timeZoneId` + offset
    (`rawOffset + dstOffset`). Store both in state; do not render them.
  - This needs the **Time Zone API** (`timezone-backend.googleapis.com`) enabled on the
    project AND in the key's API allowlist. VERIFIED 2026-06-07: it is currently NOT
    enabled (Console shows "Enable"). Native action: enable it + add to key allowlist
    (same flow as Places API New). Until then the call 403s — the R5.2 fallback must keep
    submit working.
  - Fallback if the Time Zone API call fails: keep the existing `timezoneFromOffset`
    derivation so submit still has a value; never block submit on tz lookup.

**R5.3 — "Manual override" appears on any click (misbehavior).**
- Native: clicking anywhere on the screen makes the Manual override state/section appear.
  This is a stray click/focus/blur handler toggling override (or the place element's
  blur). Fix so override ONLY toggles via its own checkbox; clicks elsewhere on the page
  must not change it. (Likely an onBlur on the place input or an outside-click handler
  flipping `manualOpen`/override — scope it to the checkbox only.)

**R5.4 — Lat/lng remain ALWAYS visible, read-only by default, editable only on override.**
- Unchanged from R4.3 and confirmed landed — keep it. With tz/offset fields removed (R5.2),
  the visible coordinate block is just Latitude + Longitude (read-only unless override).

**R5 acceptance (adds AC31–AC33; AC28/AC29 still apply to lat/lng):**
- **AC31** Selecting a place fires a Place-Details/fetchFields network request AND writes
  non-empty lat/lng to the DOM; two different places → two different real pairs; a saved
  chart persists correct lat/lng and a derived `timezone_id`/`tz_offset` (not NULL).
  `[verify-against: localhost] [via: browser + DOM read + network]`
- **AC32** Timezone + UTC offset fields are GONE from the UI; the submit payload still
  contains derived `timezone_id` + `tz_offset` (from the Time Zone API, or fallback).
- **AC33** Manual override changes ONLY via its own checkbox; clicking elsewhere on the
  page never toggles it.
---

## §R4 — place-select coordinate capture (superseded by §R5; kept for the fetchFields detail)

> Cowork verified the R3 build live in Chrome (localhost, real Maps key). R3.1–R3.8 all
> confirmed working — the Places dropdown now appears (overflow fix good), checkboxes on
> one line, themed controls, calendar picker, manual-override checkbox. BUT R3.9 has a
> real defect found by reading the DOM + network, NOT visible from screenshots:

**R4.1 — Selecting a place does NOT populate lat/lng/timezone (confirmed root cause).**
- Symptom: pick "Bhubaneswar" then "Mumbai" — the text field updates, but checking
  "Manual override" reveals lat/lng `value=""` (EMPTY). The `20.2961 / 85.8245` visible in
  the fields are just hardcoded **placeholders**, not captured values. So no place pick —
  first or subsequent — ever writes coordinates to form state. (This also means a chart
  Saved/Built right now would carry NULL lat/lng.)
- Network proof: typing fires `AutocompletePlaces` 200s, but selecting a suggestion fires
  **NO Place Details / fetchFields request**. The coordinates are never retrieved.
- Root cause: the place-resolved handler is still written for the LEGACY
  `Autocomplete.getPlace().geometry.location` pattern. The new
  `PlaceAutocompleteElement` does NOT work that way. Correct wiring:
  1. Listen for the element's selection event — **`gmp-select`** (newer builds) or
     `gmp-placeselect` (confirm against the installed `@googlemaps/*` version); the event
     detail carries a `Place` with only `id` populated.
  2. `await place.fetchFields({ fields: ['location', 'displayName', 'formattedAddress', 'addressComponents'] })`
     — THIS is the missing call; it issues the Place Details request.
  3. Read `place.location.lat()` / `place.location.lng()` → write to lat/lng state.
     Derive timezone as today (keep `timezoneFromOffset` fallback; or call the Time Zone
     API if you want exact tz — optional, not required).
  4. Set `places_resolved=true` so the resolved chip shows; the override checkbox stays
     unchecked (coords read-only) per R3.9.
- After the fix: picking two different places must yield two different, non-empty
  lat/lng pairs (Bhubaneswar ≈ 20.27/85.84; Mumbai ≈ 19.08/72.88).

**R4.2 — Resolved-coordinate chip must actually render the captured values.**
- With override unchecked, show the R2.2 chip with the REAL captured numbers
  ("✓ 19.08, 72.88 · Asia/Kolkata"), so the user gets visible confirmation the place
  resolved. Right now nothing renders, which is what made the empty-state invisible.

**R4.3 — Lat/lng fields ALWAYS visible; read-only by default; editable only on override.**
- Supersedes R2.2/R3.9's "hidden until override" model. New behaviour:
  - Latitude + Longitude fields are **always rendered/visible** (not hidden, no
    resolved-chip-instead-of-fields). Show the Timezone/UTC offset alongside as today.
  - By default they are **read-only / disabled** and auto-populate from the place
    selection (driven by the R4.1 fetchFields fix). Style them so "read-only" reads
    clearly (muted, not-editable cursor) but still on-theme.
  - When the **"Manual override"** checkbox is checked, lat/lng (and tz/offset) become
    **editable** with the existing validation (lat −90..90, lng −180..180, numeric,
    required). Unchecking returns them to read-only, repopulated from the last place.
  - A new place-select always overwrites the values (even while override is unchecked,
    since the fields are visible) and leaves override unchecked.
- The resolved-chip (R2.2/R4.2) is now optional — the always-visible read-only fields ARE
  the confirmation. Keep whichever is cleaner; the requirement is the visible read-only
  lat/lng, not a separate chip.

**R4.4 — Birthplace field background = PAGE background (not card).**
- Native: the birthplace input's background must match the **page** background
  (`--brand-ink`, the darkest canvas), so it reads as part of the page rather than a
  distinct fill. Set the `gmp-place-autocomplete` surface tokens (`--gmpx-color-surface`
  etc.) and the input wrapper background to `--brand-ink`. (Refines R3.5, which said
  "card/page"; the precise target is the page/ink background.)

**R4 acceptance (adds AC28–AC30):**
- **AC28** Selecting a Places suggestion issues a fetchFields/Place-Details request and
  writes non-empty lat/lng/timezone to state; picking two different places yields two
  different coordinate pairs; a Saved chart persists the correct lat/lng (not NULL).
  Cowork will re-verify in Chrome (localhost key is set).
  `[verify-against: localhost-then-prod] [via: browser + DOM read]`
- **AC29** Lat/lng fields are ALWAYS visible. Default = read-only, auto-filled from the
  selected place. "Manual override" checked → editable + validated; unchecked → read-only
  again. Verify the read-only fields show the real captured numbers (DOM `value`, not
  placeholder). `[verify-against: localhost] [via: browser + DOM read]`
- **AC30** Birthplace input background matches the page `--brand-ink` background.
---

## §R3 — Punch-list on the R2 build (R3.1–R3.8 SHIPPED & verified; R3.9 superseded by §R4)

> R3.1–R3.8 confirmed working in Chrome. R3.9 (lat/lng on place-select) shipped but is
> defective — see §R4 above for the actual fix. Native reviewed the R2 build (commit
> 33699024) live in Chrome. R2 is confirmed shipped and good (centered card, deep-black palette, no-scroll both viewports, Places
> API returning 200s). §R3 is the active refinement list and wins over §R2 where they
> conflict. Same branch (`feature/new-client-form-reskin`), additive commit. §D tokens +
> §R2.5 palette discipline still apply to everything below (no grey hex; --brand-* tokens).

**R3.1 — Header: icon-only back link, moved beside the title; remove subtitle.**
- Replace the "← Back to dashboard" text link with an **icon-only** back affordance (a
  left-arrow / chevron-left icon), styled in the theme (gold/muted, hover gold). Keep
  `href="/dashboard"` + `aria-label="Back to dashboard"` for accessibility.
- Move it OFF its own top row. Place it on the **same line as the `॥ Nava Jātaka ॥`
  title**, anchored to the **left edge of the viewport** (title stays centered; the icon
  floats left). This lets the title rise and reclaims vertical space.
- **Remove the "New Chart" subtitle entirely** (native: drop it). Title alone carries it.

**R3.2 — Ayanamsha: checkboxes on one line.**
- Convert the 5 ayanamsha chips (Lahiri / True Chitra / KP / Raman / Surya Siddhanta)
  into **checkboxes**, all on a **single horizontal line**. Themed: gold check/fill when
  selected, gold-hairline box when not; label + sub-label in theme text colors.
- If 5 don't fit the current ~540px card on one line, **widen the card/viewport** enough
  that they do (this is the one place native authorized going wider). Keep no-scroll.

**R3.3 — Remove the node-count microcopy.**
- Delete "N ayanamshas × 28 assets = M nodes" from the footer entirely (native: not
  needed). The footer becomes just the three buttons (Cancel / Save chart / Build chart),
  right-aligned; reclaim the freed space.

**R3.4 — Birthplace dropdown does NOT appear (visibility bug, NOT the API).**
- Confirmed via Chrome: typing fires `places.googleapis.com/.../v1.Places/AutocompletePlaces`
  POSTs returning **200** — data flows. But the suggestions dropdown never shows.
- Root cause is almost certainly CSS: `gmp-place-autocomplete` renders its prediction
  list in a **closed shadow-DOM popup** appended near the element; the centered card's
  `overflow:hidden` / rounded clipping / a stacking context / low z-index is hiding or
  clipping it. **Fix the popup's visibility** — ensure the card (or the field's wrapper)
  does not clip the dropdown (`overflow: visible` on the relevant ancestor, raise
  z-index, or detach the popup), and verify in Chrome that suggestions are VISIBLE and
  selectable. This is the acceptance bar — not "requests fire," but "dropdown shows and a
  pick fills the field + chip."
- Style the dropdown to the theme via the element's `--gmpx-*` / part selectors where
  available (charcoal background, gold-cream text, gold hover) — see R3.5.

**R3.5 — Theme the birthplace field + dropdown background.**
- The birthplace input background must **blend with the card/page** (near-black
  `--brand-charcoal` / `--brand-ink`), not the current lighter fill. The Google widget
  exposes CSS custom properties (`--gmpx-color-surface`, `--gmpx-color-on-surface`,
  `--gmpx-color-primary`, etc. — executor: confirm the exact tokens for the installed
  `gmp-place-autocomplete` version) — set them to the theme so the field and its
  dropdown read as charcoal + gold-cream, not white/grey.

**R3.6 — Gender select: theme font + dropdown colors.**
- The gender `<select>` font color and its option dropdown are off-theme. Style the
  control (charcoal fill, gold-cream text, gold focus ring, themed custom ▼) and, as far
  as the browser allows, the option list. If native option-list theming is too limited,
  use a styled custom dropdown component consistent with the brand inputs.

**R3.7 — Date: add a clickable calendar picker + theme it.**
- Currently the date field has no calendar control to click and select a date. Add a
  **calendar date picker** (themed to the design system) while preserving the
  `dd-MMM-yyyy` display and the `YYYY-MM-DD` value sent to the API (R1 W3 contract).
  Either restore a native date control styled to theme, or use a themed date-picker
  component — executor's choice — but clicking must open a selectable calendar.

**R3.8 — Time field: theme the picker.**
- The time picker currently shows a grey background / white text (off-theme). Restyle the
  time control + its dropdown to the design theme (charcoal fill, gold-cream text, gold
  accents), consistent with the other inputs.

**R3.9 — Lat/lng auto-fill on place-select + checkbox-gated manual override.**
- BUG: selecting a Places suggestion does not update lat/lng — they stay stuck on a prior
  value. On place-select, lat/lng (and timezone) MUST overwrite to the selected place's
  coordinates every time (read the resolved Place's `location.lat()/lng()`).
- Replace the always-editable manual coords with a **"Manual override" checkbox**,
  unchecked by default:
  - Unchecked (default): lat/lng are **read-only**, shown via the resolved chip (R2.2),
    driven entirely by the Places selection. User cannot edit them.
  - Checked: lat/lng fields become **editable**, with the existing validation (lat −90..90,
    lng −180..180, required, numeric). A manual edit then takes precedence until the user
    picks a new place (which re-fills and, per discretion, may re-disable — keep it simple:
    a new place-select overwrites and unchecks override).
- Keep the key-absent fallback: if Places can't load, default the override on so the user
  can still enter coordinates manually.

**R3.10 — Elevation: deliberately NOT added (decision recorded).**
- Native asked whether elevation is needed. VERIFIED against the engine: the natal
  computation calls `swe.houses(jd_ut, lat, lon, b'P')` — geocentric, lat/lon/time only,
  never `swe.set_topo(...)`. The `charts` schema has `birth_lat`/`birth_lng` and **no
  altitude column**. PyJHora (the replacement engine) is likewise geocentric by default.
  Places autocomplete does not return elevation anyway (it needs a separate Elevation API
  call). Conclusion: elevation has no effect on the Vedic chart as computed, so it is
  **deliberately excluded** — no field, no column, no Elevation API call. If a future
  topocentric need arises (e.g. lunar parallax), it would be a separate engine workstream
  (`set_topo` + DB column + API), not this form. Do NOT add an elevation field in R3.

**R3 acceptance (adds AC19–AC27):**
- **AC19** Back link is icon-only (no text), themed, on the same line as the title at the
  left viewport edge; title rises; "New Chart" subtitle removed.
- **AC20** Ayanamshas render as checkboxes on a single line; card widened only as needed;
  still no scroll at the chosen viewport. `[verify-against: prod] [via: browser screenshot]`
- **AC21** Node-count microcopy removed; footer is just the three buttons.
- **AC22** Birthplace suggestions dropdown is VISIBLE on type and a selection fills
  birth_place + lat/lng + timezone + resolved chip. `[verify-against: prod] [via: browser]`
- **AC23** Birthplace field + dropdown background blend with the charcoal/ink theme (no
  white/grey surface).
- **AC24** Gender select + its dropdown are theme-colored (no off-theme grey/white).
- **AC25** Date field opens a clickable, themed calendar picker; display stays
  dd-MMM-yyyy; API still gets YYYY-MM-DD.
- **AC26** Time picker is theme-colored (no grey bg / white text).
- **AC27** Selecting a Places suggestion overwrites lat/lng/timezone every time (no stuck
  value). "Manual override" checkbox unchecked by default → lat/lng read-only; checked →
  editable + validated. Verify in Chrome that picking two different places updates the
  coords both times. `[verify-against: prod] [via: browser]` Elevation is NOT present.
---

## §R2 — Centered-card redesign

> SHIPPED in commit 33699024 (the centered-card baseline). §R3 above refines it and wins
> on conflict; this section still governs anything R3 doesn't touch. Where §R2 conflicts
> with §D.1 (the R1 strict two-column no-scroll layout), **§R2 wins**. §D's tokens,
> typography, title, back-link,
> button styling, and reference components all still apply — only the *composition*
> changes. Same branch (`feature/new-client-form-reskin`), additive commit.

**Why:** native reviewed the R1 build in Chrome and the layout reads as broken —
everything crammed into the top third, the bottom half empty black canvas, columns of
unequal height, the intimidating lat/lng/timezone block open by default, and the footer
microcopy clipped at the left edge.

**R2.1 — Centered-card composition (Option A, native-chosen).**
- Drop the full-screen two-column grid. Place the form in a single **centered card**,
  horizontally and vertically centered in the viewport (a focused "create" dialog feel).
  Target max-width ~480–560px. No dead-space zone; no page scroll at ≥1280×800.
- Card: `bg-card` / charcoal surface, `border-border` gold-hairline, `rounded-lg`,
  comfortable internal padding. The card *is* the content — it should feel composed and
  intentional, not floated in a void.
- Vertical field order inside the card (single column, logical tab order):
  full name → preferred name + gender (one row) → birth place → date + time (one row)
  → [collapsed coords link] → ayanamsha chips → footer row (node-count + 3 buttons).
- Title `॥ Nava Jātaka ॥` (`.bt-display`, gold-cream, inline danda spans per §D) +
  "New Chart" subtitle, centered at the top of (or just above) the card.
- Back-link `← Back to dashboard` top-left of the page (outside the card), per §D / W6.
- Footer row inside the card: node-count microcopy left, **Cancel / Save chart /
  Build chart** right — ensure the microcopy is NOT clipped (R1 bug: it was cut to
  "…ayanamshas × 28 assets = 140 nodes"). Give the row full width and proper padding.

**R2.2 — Manual coordinates collapsed by default.**
- The lat/lng/timezone/UTC-offset block must be **collapsed by default**, behind a
  quiet link/disclosure labelled "Enter coordinates manually" (`.bt-body` muted).
- It auto-expands ONLY when Places fails or the Maps key is absent (the current
  key-absent fallback). When Places resolves a place, show a **compact green chip**
  ("✓ resolved · {lat}, {lng} · {tz}") instead of the full field block — do not leave
  the four raw numeric fields dominating the Birth section.

**R2.3 — Google Places — TWO causes; the key alone does NOT fix it (Chrome-confirmed 2026-06-07).**
- Cause 1 (key absent): RESOLVED. Key written to `platform/.env`; dev server picked it
  up; SDK loads; `AuthenticationService.Authenticate` returns 200 (key valid, not
  referrer-blocked).
- Cause 2 (DEAD LEGACY API): the form uses `@react-google-maps/api`'s `<Autocomplete>`,
  which wraps `google.maps.places.Autocomplete`. **Google closed that legacy API to new
  customers on 2025-03-01.** Console emits: "google.maps.places.Autocomplete is not
  available to new customers. Please use google.maps.places.PlaceAutocompleteElement
  instead." Live result: SDK loads, `.pac-container` is created but stays EMPTY (0
  suggestions), no autocomplete request fires. So a newly-created key authenticates but
  returns no predictions. **Adding the key is necessary but NOT sufficient.** → see W9.
- **Prod (native action):** set the `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` GitHub secret AND
  trigger a fresh build — `NEXT_PUBLIC_*` is build-time baked; a runtime env update does
  nothing (memory `feedback_next_public_build_arg_baking`). (Still required, but W9 must
  also ship for autocomplete to actually work on a new key.)
- **Native (parallel check):** in Google Cloud Console, confirm whether the project
  predates 2025-03-01 (legacy Autocomplete may still work) or whether "Places API
  (legacy)" can be enabled. If legacy works, the current component is a stopgap; W9 still
  ships as the supported long-term path.

**GCP state verified in Console 2026-06-07 (project madhav-astrology, MARSYS-JIS):**
- Project keys both created 2026 → "new customer" → legacy Autocomplete dead (confirms W9).
- **Places API (New)** (`places.googleapis.com`) — ENABLED (was not; native enabled it
  via Chrome session). Legacy Places API also enabled.
- **API key 2** (id `f4b8bd0f-…`, the Maps key; the AIzaSyBQ… value in `platform/.env`)
  — API restriction list INCLUDES "Places API (New)" ✓ (and "Places API").
- **Website (HTTP-referrer) allowlist** — application restriction = Websites. VERIFIED
  saved 2026-06-07, three entries: `http://localhost:3000/*`,
  `https://amjis-web-938361928218.asia-south1.run.app/*`, `https://madhav.marsys.in/*`
  (prod domain = madhav.marsys.in). Places API (New) enforces referrers strictly; all
  three present, so localhost dev + prod are both covered.
- Net: ALL GCP blockers cleared (API enabled + key allows it + referrers set). ONLY the
  W9 code migration + prod GitHub-secret + fresh build remain for Places to work.

### W9 — Migrate birthplace autocomplete to PlaceAutocompleteElement
- Replace the deprecated `google.maps.places.Autocomplete` (via `@react-google-maps/api`
  `<Autocomplete>`) with Google's current **`google.maps.places.PlaceAutocompleteElement`**
  (the API Google directs new customers to). This is the only path that yields
  predictions on a post-2025-03-01 key.
- Preserve the existing contract: on place selection, populate `birth_place`, `lat`,
  `lng`, and derive `timezone_id` / `tz_offset` (the new API returns Place objects —
  use the place's location + a timezone lookup; keep the current `timezoneFromOffset`
  fallback). Set `places_resolved` → show the R2.2 resolved chip; collapse manual coords.
- Keep the key-absent / load-failure fallback graceful (manual accordion auto-opens).
- Verify live (Chrome) that typing a place yields suggestions and selecting one fills the
  fields + chip. Re-confirm `@react-google-maps/api` exposes the new element or swap to
  the `@googlemaps/extended-component-library` / direct `importLibrary('places')` path as
  needed (executor's call after checking the installed version).
- **Executor for R1-scope verification:** once a key is present AND W9 ships, confirm the
  end-to-end resolve→chip→collapse flow.

**R2.4 — Polish carried from the Chrome review.**
- Ayanamsha chips need a clearer "toggle" affordance (selected vs unselected must read
  at a glance — selected = gold border + faint gold fill + check or filled dot;
  unselected = muted hairline). Mirror via `--brand-*` tokens, no hex.
- Gender: the raw OS `<select>` is acceptable but style it to match the brand inputs
  (charcoal fill, gold focus ring) rather than leaving it default-chrome.
- Danda glyphs `॥` in the title render thin/small in R1 — match the dashboard's weight
  and size (`dashboard/page.tsx` treatment), opacity ~0.55, gold, serif.

**R2.5 — Deepen the palette: shades of black + gold, minimize grey (native, 2026-06-07).**
- The R1 form leans on mid-greys — `#1f1c17` borders, `#5d5b54` / `#888373` / `#8a8070`
  text, panel fills lighter than the canvas. Native's theme is **black ↔ gold contrast**;
  grey is not a third color. Pull surfaces toward near-black and let gold carry emphasis.
- Surface ladder (darkest → lifted), all via tokens, no hex:
  - Page canvas: `--brand-ink` (≈#020201) — the darkest shade.
  - Card / panel fill: `--brand-charcoal` (≈#0d0a05) or a hair above — must read as a
    distinct-but-still-near-black plane against the ink canvas, separated by a gold
    hairline, NOT by being a lighter grey.
  - Input fill: at or below the card (near-ink), so fields read as wells, not grey boxes.
- Borders: gold hairlines only — `color-mix(in oklch, var(--brand-gold) N%, transparent)`
  (≈14–22%). Remove the `#1f1c17` / `--obsidian-border` grey borders entirely.
- Text: only TWO greys survive, both warm and as TEXT only — secondary
  (`--color-muted-foreground`) and the faintest tertiary for hints/microcopy. Primary
  text is gold-cream (`--brand-gold-cream`) or near-white; accents/labels are gold.
  No grey fills, no grey borders.
- Net effect: the form should read as deep black with gold linework and gold/cream type —
  the same register as the dashboard's `॥ Jātakas ॥` header on its dark canvas. When in
  doubt, go darker. Verify: `grep -nE "#(1f1c17|5d5b54|888373|8a8070|0a0908)" NewClientForm.tsx`
  returns nothing after R2.

**R2 acceptance (supersedes AC12; adds AC15–AC18):**
- **AC12′** No page scroll at 1280×800 AND 1440×900 with the centered card; the card is
  vertically + horizontally centered with NO large empty dead zone. Screenshot both.
  `[verify-against: prod] [via: browser screenshot]`
- **AC15** Manual coords collapsed by default; expands on Places-fail/key-absent; a
  resolved place shows the compact green chip, not the four raw fields.
- **AC16** Footer microcopy fully visible (not clipped) alongside the three buttons.
- **AC17** Ayanamsha chips show an unambiguous selected/unselected state; gender select
  matches brand inputs; danda glyphs match the dashboard treatment.
- **AC18** Palette deepened: page canvas = near-black (`--brand-ink`), cards near-black
  (`--brand-charcoal`), gold-hairline borders, grey only as muted/tertiary TEXT. The grep
  gate in R2.5 returns no legacy grey hex. Side-by-side with the dashboard, the form reads
  as the same black↔gold register. `[verify-against: prod] [via: browser screenshot]`
- Places (AC7) remains a native operator action (set key + rebuild); executor verifies
  behavior once a key is present.
---

# CLAUDECODE_BRIEF — New-Client Form

> **Execution surface:** Claude Code in Antigravity IDE. Cowork authored this brief;
> it does not execute. Every command below is pasteable. Localhost-first means
> **code-plane only** — the data plane (DB + GCS) is always prod via the Cloud SQL
> Auth Proxy. Do not spin up a local Postgres.

## §0 — Why this brief exists (the problem)

The new-client form (`/clients/new` → `NewClientForm.tsx`, reached from the dashboard
"Nava Jātaka" link) collects birth details and POSTs to `/api/clients/create`. As of
2026-06-06 it has three confirmed defects and three requested changes:

**Confirmed defects (read from live code):**

1. **`chart_id` is `undefined` on fresh create.** `POST /api/clients/create`
   (`platform/src/app/api/clients/create/route.ts`) inserts with `RETURNING *` from
   the `charts` table (PK column = `id`), then responds
   `chart_id: chart.chart_id` — which is `undefined` because the row has no
   `chart_id` column. The form then navigates to `/dashboard?chart_created=undefined`.
   The **dedupe/idempotent** path returns a correct `chart_id` (it SELECTs an explicit
   alias), so re-submitting an existing chart "works" while creating a *new* one does
   not — an intermittent-looking failure.

2. **Fresh chart never reaches the build workflow.** The API returns a correct
   `redirect_url` (`/clients/{id}/build`) but `NewClientForm.handleSubmit` ignores it
   and always `router.push('/dashboard?chart_created=…')`. There is no path from the
   form into the build cockpit.

3. **Google Places autocomplete is dead in production.** `deploy.yml` has two build
   jobs; one bakes `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=` **empty** (line ~65), the other
   from a secret (line ~164). `NEXT_PUBLIC_*` is **build-time baked** (see memory
   `feedback_next_public_build_arg_baking`), so if the live `amjis-web` deploy is the
   empty-key job, `isGoogleMapsKeyConfigured()` returns false and the form silently
   falls back to manual coordinates every time. Root cause is suspected to be
   env/deploy wiring, not component code — **confirm in Step 0 before touching the
   component.**

**Requested changes (native, 2026-06-06):**

4. **Three-button footer: Cancel / Save / Build.**
   - **Cancel** — discard, no write, back to `/dashboard`.
   - **Save** — create the client, return to `/dashboard` (roster card + existing
     `chart_created` toast).
   - **Build** — create the client, then go to the **build cockpit**
     (`/clients/{id}/build` → `CockpitShell`).
   Today there is a single "Create chart" button.

5. **`dd-MMM-yyyy` date format** via the central formatter (native house style; see
   memory `feedback_cockpit_build_action_model` — "dd-MMM-yyyy everywhere via central
   formatter"). The OS-native `<input type="date">` is not house format, and
   `parseBirthDateUi` exists in `form_schema.ts` but is unused.

6. **Submit / build feedback** — clear per-button loading + error states and a clean
   hand-off as the chart is created and (for Build) the cockpit loads.

## §D — Design system (canonical; the form is currently the outlier)

The dashboard and cockpit are built on the brand spine in
`platform/src/app/globals.css`. The new-client form does NOT use it — it hardcodes
`#d4a648`, `#08070a`, `#0a0908`, inline `style={{…}}` everywhere, and a bespoke
"MARSYS · Jyotish Instrument" header. **This reskin's north star: the form must look
like it was built by the same hand as the dashboard.** Use the canonical system below;
do not introduce new color values or a parallel token set.

**Canonical tokens (from `globals.css`, oklch):** `--brand-gold` (≈#d4af37),
`--brand-gold-light`, `--brand-gold-deep`, `--brand-gold-cream` (≈#fce29a),
`--brand-charcoal` (≈#0d0a05), `--brand-ink` (≈#020201). Status: `--status-success`,
`--status-halt`, `--status-warn`, `--status-info` (+ `*-bg`). Borders via
`color-mix(in oklch, var(--brand-gold) N%, transparent)`. **Do not** reach for the
`--obsidian-*` / `--gold-primary` fallbacks some older cockpit components still use —
those are legacy; the dashboard's `--brand-*` tokens are the target.

**Canonical typography (use these classes, not arbitrary `text-*`):**
- `.bt-display` — page title (serif, 1.875rem, weight 500). The dashboard's `॥ Jātakas ॥`
  uses exactly this. The form title MUST use `.bt-display`.
- `.bt-heading` — section heads (serif, 1.125rem).
- `.bt-body` — body / inputs / links (sans, 0.875rem).
- `.bt-label` (+ `.bt-label-upper`) — micro labels / metadata (sans, 0.6875rem, tracked).
- `.bt-mono` — monospace metadata.

**Devanagari double-danda:** the dashboard renders `॥ Jātakas ॥` with the danda glyph
inline (see `dashboard/page.tsx`: `<span className="opacity-55 text-[#d4af37] font-serif">॥</span>`),
and `globals.css` also ships `.bt-devanagari-rule` (::before/::after `॥`). Match the
dashboard's inline-span treatment for visual identity; opacity ~0.55, gold, serif.

**Primary CTA:** `.brand-cta` (layered gold gradient on ink, uppercase, tracked,
warm shadow) — this is the dashboard's "Nava Jātaka" button and the consume "New chart"
button. **Build chart** uses `.brand-cta`. **Save chart** is a secondary (gold hairline
outline, not filled). **Cancel** is a ghost/text button (`.bt-body text-muted-foreground`).

**Reference components to mirror (read before coding):**
- `platform/src/app/dashboard/page.tsx` — the `॥ Jātakas ॥` title (`.bt-display`,
  `text-[#fce29a]` / `--brand-gold-cream`) and the `.brand-cta` CTA. **This is the
  primary visual reference for the form title + primary button.**
- `platform/src/app/cockpit/sessions/[session_id]/page.tsx` — the canonical back-link:
  `<Link href="…" className="bt-body text-muted-foreground hover:underline">← Back to …</Link>`.
  **Use this exact pattern + the `←` glyph for the top-left go-back link** (W6).
- `platform/src/lib/components/cockpit/v2/CockpitShell.tsx` (+ `platform/src/components/cockpit/*`)
  — layout density, panel framing, gold hairlines, button bar feel for the cockpit the
  Build button lands on. Mirror its visual weight so the form → cockpit transition is seamless.

**Skills (native explicitly invited their use):** before writing JSX, the executor
SHOULD run the front-end design / brainstorming / superpowers design skills to produce
a quick layout exploration for the strict no-scroll two-column composition (see §D.1),
then implement. The form should be *easy and pleasant to fill* — logical top-to-bottom,
left-to-right tab order; the most-common path (type a place → autocomplete fills
coords/timezone → pick date/time → Build) should need the fewest interactions.

### §D.1 — Layout: strict single-viewport, no scroll (native decision)

Hard constraint: **the entire form fits one desktop viewport (≥1280×800) with no
vertical OR horizontal scroll.** Use both axes. Recommended composition:

```
┌───────────────────────────────────────────────────────────────┐
│  ← Back to dashboard                              Charts · New  │  ← top bar (W6)
│                                                                 │
│                    ॥ Nava Jātaka ॥                              │  ← .bt-display, centered
│                       New Chart                                 │  ← .bt-body muted sub
│                                                                 │
│  ┌─ Vyakti · Identity ─────────┐  ┌─ Janma Sthāna · Birth ───┐ │
│  │ Full name                   │  │ Birth place (autocomplete)│ │  ← 2-col grid
│  │ Preferred name   Gender     │  │ Date         Time         │ │     left = identity
│  │                             │  │ [coords/tz: resolved chip │ │     right = birth
│  └─────────────────────────────┘  │  or compact manual row]   │ │
│  ┌─ Ganana · Compute ──────────┐  └───────────────────────────┘ │
│  │ [ Lahiri ][ Chitra ][ KP ]… │                                │  ← ayanamsha chips, wrap
│  └─────────────────────────────┘                                │
│                                                                 │
│  N ayanamshas × 28 = M nodes      [Cancel] [Save chart] [Build] │  ← button bar (W2)
└───────────────────────────────────────────────────────────────┘
```

- Collapse the always-open manual-coords accordion into a **compact inline row** that
  only expands when Places fails / key absent — it currently eats vertical space.
- Tighten section padding (the current 20px panels + 16px gaps are generous; reduce to
  fit). Keep panels' gold-hairline framing.
- On widths < 1024px, graceful vertical stack + scroll is acceptable (the no-scroll gate
  is desktop ≥1280px). Verify with a screenshot at 1280×800 AND 1440×900.

## §1 — Scope

`may_touch`:
- `platform/src/components/clients/NewClientForm.tsx`
- `platform/src/components/clients/form_schema.ts`
- `platform/src/components/clients/usePlacesAutocomplete.ts`
- `platform/src/app/api/clients/create/route.ts`
- `platform/src/components/clients/__tests__/**`
- `platform/src/app/api/clients/create/__tests__/**`
- `platform/tests/e2e/new-client-flow.spec.ts`
- `.github/workflows/deploy.yml` (Maps-key line only, IF Step 0 proves it is the cause)
- A central date formatter module (locate in Step 0; do NOT create a second one)

`read-only references` (mirror these, do not edit):
- `platform/src/app/globals.css` — canonical `--brand-*` tokens + `.bt-*` / `.brand-cta`.
- `platform/src/app/dashboard/page.tsx` — `॥ Jātakas ॥` title + `.brand-cta` CTA.
- `platform/src/app/cockpit/sessions/[session_id]/page.tsx` — back-link pattern.
- `platform/src/lib/components/cockpit/v2/CockpitShell.tsx` — cockpit visual weight.

`must_not_touch`:
- `platform/src/app/api/clients/route.ts` (the OTHER create endpoint — see §2 Step 0;
  decision deferred to native after investigation)
- `platform/src/lib/components/cockpit/**` (the cockpit itself; Build only navigates to it)
- Any `00_ARCHITECTURE/` governance file other than this brief
- Any migration; this brief is schema-neutral
- The dashboard roster / ClientCard (a separate active workstream)

## §2 — Step 0: Verify-first (NO code changes in this step)

Per memory `feedback_verify_state_not_claude_md` and the autonomous-wave prod-gate
discipline (`feedback_ac_must_verify_target_environment`), confirm the following
against **live code + prod/deploy** and write findings into the PR description before
writing any feature code. Each item is a gate: if reality differs from this brief,
stop and report rather than coding around it.

- **0.1 — Endpoint divergence.** Grep all callers of both create endpoints:
  ```
  grep -rn "api/clients/create" platform/src
  grep -rn "fetch('/api/clients'" platform/src
  grep -rn '"/api/clients"' platform/src
  ```
  Confirm `NewClientForm` is the only caller of `/api/clients/create`, and identify
  every caller of the bare `/api/clients` POST. **Decision gate:** report who uses the
  old route. Do NOT delete or merge endpoints in this brief — propose consolidation
  as a follow-up for native sign-off. Note the integration test
  `platform/src/app/api/clients/__tests__/create.integration.test.ts` mirrors the
  **old** `/api/clients` contract (`birth_lat`/`birth_lng`), not the form's endpoint;
  flag this divergence but leave it.

- **0.2 — Central date formatter.** Locate the existing house formatter (grep for
  `dd-MMM`, `format(`, `Intl.DateTimeFormat`, `date-fns`, a `lib/format`/`lib/date`
  module). Confirm its API. The form MUST reuse it, not introduce a new one.

- **0.3 — `charts` PK column.** Confirm against prod schema that the primary key is
  `id` and there is no `chart_id` column on `charts`:
  ```
  # via prod proxy (see memory reference_madhav_infra_paths; port 5433)
  psql "$DATABASE_URL" -c "\d charts" | grep -E "id|chart_id"
  ```
  `[verify-against: prod] [via: psql_prod]`

- **0.4 — Build cockpit route.** Confirm `/clients/{id}/build` renders `CockpitShell`
  with only `chartId={id}` (no extra params needed). (Already read: `page.tsx` awaits
  `params.id`, guards `access.canBuild`, renders `<CockpitShell chartId={id} />`.)
  Confirm a freshly created chart with seeded `pyramid_layers` but no build run lands
  cleanly on the cockpit (empty/"not started" state, not a crash).

- **0.5 — Google Maps key.** Determine which `deploy.yml` job deploys the live
  `amjis-web` service, and whether `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is non-empty in
  that job AND the GitHub secret is set:
  ```
  gcloud run services describe amjis-web --region asia-south1 \
    --format='value(spec.template.spec.containers[0].image)'
  # inspect both build jobs in .github/workflows/deploy.yml
  ```
  `[verify-against: prod] [via: gcloud]`. **Decision gate:** if the empty-key job is
  the live one, the fix is the deploy line + a rebuild (NEXT_PUBLIC is build-time
  baked — a gcloud env-var update has ZERO effect). If the secret itself is unset,
  that is a native operator action (set the secret), not a code change — surface it,
  don't fake a key.

## §3 — Work items

### W1 — Fix the create response + redirect contract
- In `route.ts`, fix the fresh-create response to return the real id. Use the same
  alias the dedupe path uses, e.g. `RETURNING id AS chart_id, client_id` (or read
  `chart.id`). Keep `redirect_url: /clients/${id}/build` correct and non-undefined.
- Add/adjust unit tests in `create/__tests__/route.test.ts` asserting `chart_id` is a
  defined UUID on the **fresh-create** path (not just the idempotent path).

### W2 — Three-button bar (Cancel / Save chart / Build chart)
- Replace the single submit button with **Cancel**, **Save chart**, **Build chart**.
  Styling per §D: Build chart = `.brand-cta` (primary, filled gold); Save chart =
  secondary (gold hairline outline); Cancel = ghost text (`.bt-body text-muted-foreground`).
- Both Save and Build POST the same validated body to `/api/clients/create`. They
  differ only in post-success navigation:
  - **Save chart** → `router.push('/dashboard?chart_created=' + chart_id)`.
  - **Build chart** → `router.push(data.redirect_url)` (i.e. `/clients/{id}/build`);
    fall back to `/clients/${chart_id}/build` if `redirect_url` is absent.
  - **Cancel** → `router.push('/dashboard')`, no fetch, no write.
- Per-button pending state: only the clicked button shows "Saving…/Building…"; the
  other two disable while a request is in flight. Preserve the idempotent/dedupe
  handling (a Save of an existing chart still resolves to its id; a Build of an
  existing chart still routes to its cockpit).
- Keep the node-count microcopy ("N ayanamshas × 28 assets = M nodes") in the bar,
  left-aligned, with the three buttons right-aligned (see §D.1 sketch).

### W3 — dd-MMM-yyyy birth date
- Replace the native `<input type="date">` with house `dd-MMM-yyyy` entry using the
  central formatter found in Step 0.2. Wire up `parseBirthDateUi` (currently unused)
  or the central parser as the bridge to the API's required `YYYY-MM-DD`.
- Preserve all existing validation: required, ≥ 1900-01-01, ≤ today, real calendar
  date. The API contract stays `YYYY-MM-DD` — only the UI representation changes.
- Update `form_schema.test.ts` / `NewClientForm.test.tsx` accordingly.

### W4 — Submit / build feedback
- Clear error surfacing for 422 (field map already exists), 429 (rate limit), 409,
  network. Keep the `aria-live`/`role="alert"` patterns already present.
- On Build, show an unambiguous "Building… opening cockpit" transition so the user
  understands navigation is intentional, not a hang.

### W5 — Fix Google Places (driven by Step 0.5 finding)
- If the cause is the empty-key deploy job: fix the `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`
  line in the live job and trigger a fresh build (NEXT_PUBLIC is build-time baked).
- If the secret is unset: surface as a native operator action; do not hardcode a key.
- Component robustness regardless of cause: ensure that when the key IS present,
  selecting a Places suggestion populates lat/lng/timezone and sets
  `places_resolved`; when absent, the manual-coords accordion auto-opens (already
  implemented — verify it still holds after W2/W3 refactor).
- Note the privacy-extension fetch-hang trap (memory
  `feedback_browser_extension_hangs_fetch`): test Places in an Incognito window during
  smoke.

### W6 — Top-left go-back link
- Add a back link in the top-left corner using the canonical pattern from
  `cockpit/sessions/[session_id]/page.tsx`: a `next/link` with
  `className="bt-body text-muted-foreground hover:underline"` and the `←` glyph,
  label "Back to dashboard", `href="/dashboard"`, `aria-label="Back to dashboard"`.
- This is navigation only (no write), distinct from Cancel (which is in the button
  bar). Both go to `/dashboard`; having both is intentional (corner affordance + bar action).

### W7 — Title rename + brand header
- Remove the current "MARSYS · Jyotish Instrument" header block.
- Render the title as **॥ Nava Jātaka ॥** using `.bt-display`, gold-cream
  (`text-[#fce29a]` / `--brand-gold-cream`), with the danda glyphs as inline spans
  matching `dashboard/page.tsx` (opacity ~0.55, gold, serif). English subtitle
  "New Chart" in `.bt-body` muted, directly beneath. Centered per §D.1.
- The small top-right "Charts · New" eyebrow may stay (use `.bt-label` / `.bt-mono`,
  not inline styles).

### W8 — Full design-system reskin (no hardcoded values)
- Replace ALL inline `style={{…}}` color/spacing/typography in `NewClientForm.tsx`
  with the canonical tokens + `.bt-*` classes per §D. No literal hex colors remain in
  the component (verify: `grep -nE "#[0-9a-fA-F]{6}" NewClientForm.tsx` returns nothing
  after the reskin, except where a token genuinely has no class equivalent — justify any).
- Panels keep gold-hairline framing via `color-mix` borders; inputs use the brand
  focus ring (gold). Ayanamsha chips: selected = gold border + faint gold fill
  (`--brand-gold-faint`), unselected = muted hairline — mirror the current behavior but
  via tokens.
- Implement the strict single-viewport two-column layout from §D.1; collapse the
  always-open manual-coords accordion into the compact resolved-chip / expand-on-fail row.
- The executor is invited (native) to use the front-end design / brainstorming /
  superpowers skills for a layout exploration before implementing.

## §4 — Acceptance criteria

All ACs gated; prod-verified ones tagged explicitly.

- **AC1** Fresh create returns a defined UUID `chart_id` (unit test).
- **AC2** Save creates a chart and lands on `/dashboard?chart_created={uuid}` with the
  toast + roster card showing. `[verify-against: prod] [via: curl_prod | browser]`
- **AC3** Build creates a chart and lands on `/clients/{uuid}/build` rendering the
  cockpit without crash on a never-built chart.
  `[verify-against: prod] [via: browser]`
- **AC4** Cancel performs no write and returns to `/dashboard` (assert no new `charts`
  row). `[verify-against: prod] [via: psql_prod]`
- **AC5** Birth date is entered and displayed as `dd-MMM-yyyy`; the API still receives
  `YYYY-MM-DD`; all date-boundary validations pass.
- **AC6** Per-button loading states are mutually exclusive; double-submit is prevented.
- **AC7** Google Places autocomplete resolves a place to lat/lng/timezone in the live
  service (Incognito). `[verify-against: prod] [via: browser]`. If blocked on an unset
  secret, AC7 is recorded as a native operator action with the exact secret name.
- **AC8** `tsc --noEmit` clean + all touched vitest files green
  (`feedback_grep_check_is_not_compile_check`).
- **AC9** Step 0 findings (endpoint divergence, formatter location, PK column, Maps
  cause) written into the PR description.
- **AC10** Top-left back link present, uses the canonical `← Back to dashboard` pattern,
  navigates to `/dashboard`. `[verify-against: prod] [via: browser]`
- **AC11** Title reads **॥ Nava Jātaka ॥** in `.bt-display` gold-cream with inline danda
  spans matching the dashboard; "MARSYS · Jyotish Instrument" header is gone; English
  subtitle "New Chart" present.
- **AC12** Strict no-scroll: the full form fits one viewport at 1280×800 and 1440×900
  with neither vertical nor horizontal scroll. **Screenshot both as evidence in the PR.**
  `[verify-against: prod] [via: browser screenshot]`
- **AC13** Design-system conformance: no literal hex colors remain in
  `NewClientForm.tsx` (grep gate per W8); title/sections/buttons/labels use `.bt-*`
  classes and `--brand-*` tokens; the form is visually consistent with the dashboard
  and cockpit (side-by-side screenshot in PR).
- **AC14** Tab order is logical (name → preferred → gender → place → date → time →
  ayanamshas → buttons); keyboard-only fill reaches Build chart.

## §5 — Out of scope (explicit)
- Consolidating / deleting the second `/api/clients` create endpoint (propose only).
- Birth-time precision / time-unknown / rectification (native deferred this round).
- Any change to the build cockpit, the roster, or the asset DAG.
- Schema migrations.

## §6 — Git
```
git checkout -b feature/new-client-form-reskin
# ... implement W1–W8 ...
git add -A && git commit -m "new-client form: design-system reskin (॥ Nava Jātaka ॥, single-viewport, brand tokens), back-link, 3-button bar, create wiring fix, dd-MMM dates, feedback, Places"
```
Branch isolation per stream (memory `feedback_two_stream_branch_policy`). Run
`npm run -w platform test -- <touched files>` and `tsc --noEmit` before commit.
Post-deploy smoke runs the AC2/AC3/AC4/AC7 prod checks before this is called done.
