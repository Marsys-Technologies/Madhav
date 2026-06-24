---
artifact: MIGRATION_PRE_ALLOCATION.md
conductor: Sūtradhāra
layer: L3 Kāla
created: 2026-06-21
updated: 2026-06-21 (K0 complete — updated actual numbers)
purpose: Pre-allocated migration numbers (CS2 — prevents "two-174" collision during parallel fan-out).
basis: >
  platform/supabase/migrations/ last on-disk = 242 (242_l3_service_asset_type.sql, K0 DONE).
  New L3 migrations go in platform/supabase/migrations/ (K0 agent confirmed this is the correct dir;
  platform/migrations/ is for app-level governance, supabase/migrations/ for schema).
---

# L3 Kāla — Migration Number Pre-Allocation (CS2)

## K0 COMPLETED
| Migration # | Asset | File name | Dir | Status |
|---|---|---|---|---|
| 242 | K0 / k0_service_asset_type | `242_l3_service_asset_type.sql` | platform/supabase/migrations/ | ✅ APPLIED TO PROD + registered in _migrations_applied |

Note: K0 brief pre-allocated 328 in platform/migrations/, but the K0 agent correctly used 242 in
platform/supabase/migrations/ (schema-change convention). Logged as Tier-2 deviation resolved autonomously.

## K3–K6 PENDING ALLOCATION (contiguous from 243)
Agents use their assigned number directly — NEVER resolve `<next>` themselves (the "two-174" trap).

| Migration # | Asset | File name (to create) | Dir | Kind |
|---|---|---|---|---|
| 243 | ka_yojaka | `243_l3_ka_yojaka.sql` | platform/supabase/migrations/ | artifact table |
| 244 | ka_sangam | `244_l3_ka_sangam.sql` | platform/supabase/migrations/ | artifact table + indexes |
| 245 | ka_vighnakara | `245_l3_ka_vighnakara.sql` | platform/supabase/migrations/ | artifact table |
| 246 | ka_kalasutra | `246_l3_ka_kalasutra.sql` | platform/supabase/migrations/ | artifact table |
| 247 | ka_kala_darshana | `247_l3_ka_kala_darshana.sql` | platform/supabase/migrations/ | artifact catalog table |
| 248 | ka_jivana_parva | `248_l3_ka_jivana_parva.sql` | platform/supabase/migrations/ | artifact narrative table |
| 249 | ka_bhavishya_lekha | `249_l3_ka_bhavishya_lekha.sql` | platform/supabase/migrations/ | artifact prediction table |

## Notes
- K1 services (ka_graha_sancara, ka_dasha_kala, ka_muhurta_seva) have NO new tables — they are service assets
- K2 (ka_gochara / transit_search) builds code only, no new table schema migration needed
- Numbers 250+ reserved for post-L3 use (L4 Phala)

## Gate: no agent may use a migration number outside this pre-assigned list.
Any impulse to use a different number → STOP, log to HALT_LOG.md as Tier-2, use the assigned number.
</content>
