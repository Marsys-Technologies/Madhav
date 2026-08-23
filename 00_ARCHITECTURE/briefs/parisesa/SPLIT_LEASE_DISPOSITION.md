---
artifact: PARISESA_SPLIT_LEASE_DISPOSITION
ruling: PAR-R-13 (PRATINIDHI) — deliverable requested by that ruling
owner: SUTRADHARA
---

# Per-lane disposition for the 16 split-lane findings

Per PAR-R-13: default posture is SPEC-TRAVELS (the plan's own default). GRANT only where the
target file is (a) not one of the two hot files (`response_budget.ts`, `registry_bridge.ts` —
forbidden, no exceptions per LEASES.json's own words), and (b) not already resolved by one of
§2.1's four rows. Every GRANT is per-file, at B-stage entry only (after Stage R clears), with
explicit expiry, and the owning lead reviews the diff on handback.

| Finding | Spec author | Build target file(s) | Disposition | Reason |
|---|---|---|---|---|
| F-08 | S5 | L4_phala/** (S3) | SPEC-TRAVELS | Not hot, not in §2.1's four rows, but no strong reason to break S3's existing build ownership of L4_phala — low-value to re-lease |
| F-09 | S1 | response_budget.ts (S2) | SPEC-TRAVELS | **Carve-out 1**: hot file, no exceptions |
| F-12 | S2 | L1_ganita/* (S5) | **GRANT** | Plain domain file, not hot, not in §2.1's four rows — S2 gets a time-boxed per-file lease at B-stage entry |
| F-28 | S2 | tool_name_bridge.ts (S1) | SPEC-TRAVELS | Not hot, not in §2.1's rows, but this file is S1's core shared lease touched by many lanes (F-67, F-73, others) — granting risks the incoherence hazard PRATINIDHI named; S1 builds |
| F-31 | S3 | registry_bridge.ts (S2) | SPEC-TRAVELS | **Carve-out 1**: hot file, no exceptions |
| F-36 | S2 | register_d7_channel.ts (S5) | **GRANT** | Plain domain file (already S5's own F-05 lives here too, but this specific fix is narrow) — S2 gets a time-boxed per-file lease |
| F-37 | S2 | L1_ganita/* (S5) | **GRANT** | Same file as F-12 — bundle into the same grant/commit as F-12 |
| F-38 | S1 | now.ts / registry_bridge.ts (S2/S4) | **ALREADY-RESOLVED-BY-§2.1** | §2.1 row 3 + S1's own lease note: built as route-level middleware, never in now.ts or registry_bridge.ts — no lease crossing needed at all |
| F-45 | S2 | register_p1_aliases.ts, register_p1_synthesis.ts, L3_kala, L2_bodha (S5) | **ALREADY-RESOLVED-BY-§2.1** (mostly) | Touches two of §2.1's four named files directly (the S1→S5 and S5→S4 ordered handoffs) — those pieces travel by the existing mechanism; L3_kala/L2_bodha pieces travel too for consistency, not granted separately |
| F-46 | S2 | register_p1_ganita.ts (S1) + register_p1_synthesis.ts (S5→S4 handoff) | **SPLIT**: register_p1_ganita.ts piece = **GRANT** to S2 (plain file, not hot, not in the four rows); register_p1_synthesis.ts piece = **ALREADY-RESOLVED-BY-§2.1** | Two different files, two different dispositions |
| F-63 | S4 | ga_panchanga_writer.py (S6) | SPEC-TRAVELS | RS-A (rebuild-gated) — this lane can't reach Stage V until the batched rebuild regardless of who builds it; no urgency to grant |
| F-70 | S5 | kala_envelope.ts (S5, shared helper) + call sites in S2's/S4's own files | SPEC-TRAVELS | Not actually a lease conflict — S5 owns the shared helper it authored; S2/S4 apply call-site pieces inside files they already own themselves. Natural pattern, nothing to grant |
| F-78 | S3 | services/ka_kshetra/** (S6) | SPEC-TRAVELS | S6 already holds this domain lease (granted post-Phase-0 specifically for F-78 routing) — this is the plan working as designed, not a conflict |
| F-117 | S3 | bo_upaya.py / formulas.py (S5) | **GRANT** | Plain domain file, not hot, not in §2.1's four rows |
| F-123 | S1 | kala_views/now.ts, explain.ts (S4) | **ALREADY-RESOLVED-BY-§2.1** | The kala_views file split itself is a §2.1 row — S4 owns now.ts/explain.ts by that split, not a new conflict |
| F-125 | S2 | kala_views/upaya.ts (S4) + register_p1_aliases.ts (S5) | **ALREADY-RESOLVED-BY-§2.1** | Both target files are already covered by §2.1's rows (kala_views split; S1→S5 ordered handoff) |

## Summary

- **GRANT** (per-file, time-boxed, B-stage entry only): F-12, F-36, F-37, F-46 (partial), F-117 — 5 grants across 4 distinct files (F-12/F-37 share one file).
- **ALREADY-RESOLVED-BY-§2.1**: F-38, F-45, F-46 (partial), F-123, F-125 — 5 lanes, no new lease action needed, the plan already routes these.
- **SPEC-TRAVELS** (directive yields per PAR-R-13's correction): F-08, F-09, F-28, F-31, F-63, F-70, F-78 — 7 lanes, including both hot-file carve-outs (F-09, F-31).

Grants will be added to LEASES.json individually as each lane actually clears Stage R and enters Stage B — not pre-granted now, per PAR-R-13's sequencing condition.
