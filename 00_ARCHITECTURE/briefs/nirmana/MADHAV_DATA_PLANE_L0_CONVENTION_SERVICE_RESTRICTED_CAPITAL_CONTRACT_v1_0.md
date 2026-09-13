---
artifact: MADHAV_DATA_PLANE_L0_CONVENTION_SERVICE_RESTRICTED_CAPITAL_CONTRACT
version: "1.0"
status: IMPLEMENTED_WITH_DECLARED_LIMITS
produced_on: 2026-09-13
---

# L0 convention, service and restricted-capital contract

## Numerical and calendar services

| Producer | Grain/context now carried | Honest failure and limit |
|---|---|---|
| `bg_ephemeris_engine` | instant UTC, geocentric sidereal frame, ayanāṃśa, mean-node mode, observed backend, output precision and registry generation | timezone-free/invalid instant and unknown ayanāṃśa fail; local Moshier fallback is returned as `UNQUALIFIED_BACKEND`, never represented as the admitted Swiss-file corpus |
| `bg_panchanga` | civil date + latitude + longitude + fixed UTC offset, Lahiri frame, mean-node mode, sunrise/day-boundary convention, engine versions and precision | partial coordinates, coordinates without timezone, unknown named location and conflicting named timezone fail; fixed offset is not zone-rule history |
| `bg_gochara_arcs` | body + substrate version + bounded longitude arc | current generation rebuild no longer deletes prior substrate generations; exact instant refinement remains a later service operation |

The ephemeris Ketu correction preserves the antipodal longitude and uses Rahu's
same signed angular speed. Negating that speed incorrectly reported a direct Ketu
while mean Rahu was retrograde. The numerical kernel, ayanāṃśa calculation and
planet set otherwise remain intact.

No chart fact, personal relevance, temporal activation or forecast is emitted by
these L0 services. `bg_ephemeris` daily samples remain distinct from the
arbitrary-instant service. The local environment observed Moshier fallback, so no
Swiss-file health or supported-horizon claim is made here; the existing strict
registry service probe remains the detector for that separate admission.

## Unresolved convention variants

Formula/dignity friendship scores, combustion ordinary/deep orbs and
direct/retrograde meanings are not silently unified. Existing method-native
values remain preserved and `contradictory_unresolved` until an exact variant,
source and consumer meaning is admitted. Muhūrta lattice reference location and
sunrise-midpoint approximation, average-motion transit substrate, KP division,
Kota, vedha/latta and sky-calendar geometry remain explicitly method/version
bound; catalog presence is not arbitrary-instant or personal applicability.

Some existing writer tables remain current-generation projections rather than
simultaneous history stores. This packet changes only the proved destructive
cross-version delete in `bg_gochara_arcs`; it does not manufacture generation
history where schema/authority was not established. The residual is carried in
the rollback record.

## Restricted capital and discovery

| Capital | Permitted L0 role | Prohibited inference |
|---|---|---|
| medical mappings | attributed traditional reference/research | diagnosis, treatment or individual health forecast |
| vāstu directions | attributed restricted testimony | activated spatial/remedial service or efficacy |
| remedies/parihāra | voluntary, source-qualified and contraindication-aware reference | guaranteed result, burden coercion or automatic recommendation |
| class priors/counts | typed reference coordinate with population/unit/source | personal probability |
| synthetic cohort | engineering fixture with generation context | human validation or empirical evidence |

The existing Vidhi TS-only `vastu_read` reservation is retained because its
generated/frozen counterpart cannot be changed without a separately protected
repin. The known parity exception stays visible; no false exact-parity claim is
made. Capability discovery is producer description only: no retrieval ranking,
managed/raw channel or caller integration was authorized.
