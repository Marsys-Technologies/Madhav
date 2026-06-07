/**
 * usePlacesAutocomplete — functional hook for Google Places autocomplete
 *
 * D-S3 finding: Places API was NOT previously wired. This hook provides the
 * integration surface. When NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is absent the hook
 * returns `keyAbsent: true` and callers should auto-expand the manual coords
 * accordion as fallback.
 *
 * Stream C wires the JSX wrapper (<LoadScript> + <Autocomplete>) using this
 * hook's result. Stream D owns the functional state + callback logic here.
 *
 * [BUILD-ORCH-D-S3] Branch: NOT_WIRED — added integration surface + fallback.
 * Commit body note: GOOGLE_MAPS_API_KEY absent at discovery time; manual-override
 * fallback (auto-expand accordion) already implemented in NewClientForm.tsx
 * handleBirthplaceChange. This hook formalises that contract.
 */

export interface PlacesResult {
  description: string
  lat: number
  lng: number
  utcOffsetMinutes: number | null
  timezone_id?: string   // from Google Time Zone API (R5.2)
  tz_offset?: string     // from Google Time Zone API (R5.2)
}

export interface UsePlacesAutocompleteReturn {
  keyAbsent: boolean
  onPlaceSelected: (place: google.maps.places.PlaceResult) => void
  result: PlacesResult | null
  clearResult: () => void
}

// Determine whether the Google Maps key is configured at build time.
// When absent, callers fall back to the manual lat/lng accordion.
export function isGoogleMapsKeyConfigured(): boolean {
  return !!process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
}

/**
 * Returns a callback to wire to the Google Places <Autocomplete> onPlaceChanged
 * event. When the key is absent, returns a no-op and signals keyAbsent=true so
 * the caller can open the manual override accordion.
 */
export function buildPlacesHandler(
  onResult: (result: PlacesResult) => void,
): {
  keyAbsent: boolean
  onPlaceSelected: (place: google.maps.places.PlaceResult) => void
} {
  const keyAbsent = !isGoogleMapsKeyConfigured()

  function onPlaceSelected(place: google.maps.places.PlaceResult) {
    if (!place?.geometry?.location) return

    const lat = place.geometry.location.lat()
    const lng = place.geometry.location.lng()
    const description = place.formatted_address ?? place.name ?? ''
    const utcOffsetMinutes = place.utc_offset_minutes ?? null

    onResult({ description, lat, lng, utcOffsetMinutes })
  }

  return { keyAbsent, onPlaceSelected: keyAbsent ? () => {} : onPlaceSelected }
}
