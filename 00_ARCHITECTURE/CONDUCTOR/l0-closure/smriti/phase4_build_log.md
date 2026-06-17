---
title: Phase 4 Build Log
phase: L0 Closure Pass — Phase 4 (Synergy Hunt)
date: 2026-06-17
branch: fix/l0-closure-integrity
---

# Phase 4 Build Log

## Summary

Phase 4 investigated 12 candidate cross-asset synergies across the L0 Brahmagyan layer.
One new static table was built. No existing tables were modified.

---

## Tables Built

### bg_graha_dik

| Field | Value |
|---|---|
| Migration file | `platform/migrations/304_bg_graha_dik.sql` |
| Applied | 2026-06-17 15:18:58 UTC |
| Row count | 9 |
| Schema | `(id, graha, peak_house, peak_direction, debility_house, paired_graha, school_note, classical_citation, created_at)` |
| Unique constraint | `UNIQUE(graha)` |
| Idempotency | `ON CONFLICT (graha) DO NOTHING` |

**Row verification (SELECT * FROM bg_graha_dik ORDER BY id):**

```
 id | graha   | peak_house | peak_direction | debility_house | paired_graha | school_note | classical_citation
----+---------+------------+----------------+----------------+--------------+-------------+----
  1 | sun     |         10 | South          |              4 | mars         | parashari   | BPHS Ch.27...
  2 | moon    |          4 | North          |             10 | venus        | parashari   | BPHS Ch.27...
  3 | mars    |         10 | South          |              4 | sun          | parashari   | BPHS Ch.27...
  4 | mercury |          1 | East           |              7 | jupiter      | parashari   | BPHS Ch.27...
  5 | jupiter |          1 | East           |              7 | mercury      | parashari   | BPHS Ch.27...
  6 | venus   |          4 | North          |             10 | moon         | parashari   | BPHS Ch.27...
  7 | saturn  |          7 | West           |              1 | (null)       | parashari   | BPHS Ch.27...
  8 | rahu    |          7 | West           |              1 | (null)       | tajika      | Tajika Neelakanthi...
  9 | ketu    |          4 | North          |             10 | (null)       | debated     | Ketu Dig Bala not...
```

**Classical authority:** BPHS Ch.27 (Digbala), Saravali Ch.3 v.10, Brihat Jataka Ch.2
**Rahu:** Tajika school (debated but widely used)
**Ketu:** No universal consensus — flagged as provisional

---

## Tables NOT Built (and why)

| Candidate | Not built because |
|---|---|
| nakshatra-deity × medical bridge | reference_nakshatra.body_part + bg_nakshatra_medical already cover this |
| nakshatra → vimshottari lord mapping | Already in reference_nakshatra.vimshottari_lord (28 rows, fully populated) |
| transit_vedha × transit_rules combined | Tables are complementary and joinable; a VIEW is sufficient (REC-002) |
| prashna_rules × reference_planets | Trivial query-time join; no static table adds value |
| vastu_directions × nakshatra directional affinity | Trivially computed: nakshatra.disha + nakshatra.ruling_planet JOIN bg_vastu_directions |

---

## Candidates Deferred to L1/L2 (not built in L0)

| Candidate | Layer | Reason |
|---|---|---|
| dignity × transit rules | L1 | Requires chart+transit-time graha position |
| yoga × dosha conflict pairs | L2 | Interpretive synthesis |
| nakshatra × remedies | L2 | Chart-specific application |
| medical × nakshatra → dhatu chain | L2 | Chart-dependent interpretation |
| dosha × remedy cross-ref | L2 | Chart-specific + data content gap |

---

## Output Files

1. `00_ARCHITECTURE/CONDUCTOR/l0-closure/smriti/phase4_analysis.md` — full raw analysis
2. `00_ARCHITECTURE/CONDUCTOR/l0-closure/L0_SYNERGY_REGISTER_v1_0.md` — canonical register
3. `00_ARCHITECTURE/CONDUCTOR/l0-closure/smriti/phase4_build_log.md` — this file

---

## Structural Recommendations Raised

See L0_SYNERGY_REGISTER_v1_0.md §4 for four recommendations requiring native sign-off:
- REC-001: Unified directional authority (view or governance note)
- REC-002: Transit table consolidation VIEW (migration 305)
- REC-003: brahma_dosha_catalog.associated_remedies population (data task)
- REC-004: bg_nakshatra_medical vs reference_nakshatra.body_part inconsistency audit
