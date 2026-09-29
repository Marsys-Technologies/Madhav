---
artifact: NEAR_MISS_DOMAIN_PACKET
version: 1.1
status: RATIFIED_BY_OWNER_SURROGATE_PENDING_INDEPENDENT_DOMAIN_REVIEW
date: 2026-09-29
ruling: OSR-012 (amends OSR-009)
supersedes_sections_of: NEAR_MISS_DOMAIN_PACKET_v1_0.md (sections 5, 6, 7, 8, 9, 10 as below; all others unchanged)
changelog:
  - 1.1 (2026-09-29): producer changed from bo_laksana stored rows to a serve-time derivation, because stored absence rows force reader-isolation edits in L2, L3 and L5 and three unavailable pin re-admissions. Candidate set NMB-CAND-v1, eligibility NMB-ELIG-v1, tolerance, scope, states, precedence, wording rules and the section 7 producer/consumer cases are unchanged.
---

# Near-miss packet v1.1 (delta over v1.0)

- **5 Producer.** A new sidecar route (`routers/yoga_formation_band.py`, not imported by any registered writer) imports and calls the shipped L1 evaluators (`ChartState`, `_lord_of_house`, `_house_of_planet`, `_check_house_lord_association`, `_detect_dhana_yoga_house_lords`) without editing them. Inputs: `chart_id`, `ayanamsha_id`, validated UUID `served_build_ids`. It reads `chart_facts` and `ga_yoga_firings` only with `build_id = ANY(...)` and fact_key-pinned selections with total ORDER BY. It always returns exactly six candidate rows carrying the v1.0 section 5 configuration fields as its response ledger. Nothing is persisted; no migration; no writer, digest or pin change.
- **6 Consumer.** `register_d9_judgment.ts` calls the route with `served_build_ids`. `source_unproven` = no fresh `ga_yoga` receipt, wrong generation, a missing fence asset, a sidecar failure, or not exactly six ids. The fence is `ga_yoga` plus the producing assets of the `chart_facts` categories `ChartState` reads (expected to include `ga_positions`); `bo_laksana` is not in the fence. Wording and forbidden words unchanged.
- **7 Tests.** Reader-isolation and allowlist tests are replaced by: writer digests and layer pins byte-identical to main (`--check` green, zero re-admissions), and the route imports the L1 evaluators and does not fork them. Parity test: the `present` state equals the detector result on every fixture.
- **8 Review.** `security-reviewer` is now REQUIRED (new data-access route) plus a second semantic review; the independent Parashari domain review remains a merge precondition.
- **9/10 Files and rebuild.** Route, consumer, checklist fence, tests. No `bo_laksana` rebuild is implied; the single OSR-004 rebuild refreshing `ga_yoga`/`ga_positions` suffices. Until then the wealth path returns `source_unproven`.
- **Descriptor text.** If correcting the judgment tool's description moves the capability content hash pinned by goldens this session cannot edit, keep the descriptor text and record the stale sentence as a follow-up; never change the hash without regenerating every pinned golden.
