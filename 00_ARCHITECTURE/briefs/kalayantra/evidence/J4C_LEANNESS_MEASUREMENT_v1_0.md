---
artifact: J4C_LEANNESS_MEASUREMENT
version: "1.0"
status: WRITTEN — J-4c F-LEANNESS builder evidence; independent review pending
produced_on: 2026-10-20
changelog: v1.0 — first commit. Measured before/after of the record/window write groups (SR-J3D-LEANNESS-ROW, F-LEANNESS accepted as J-4c's call).
owner_step: J-4c leanness (builder PR)
---

# J-4c F-LEANNESS — where the tiny classes' cost comes from, what was removed, what was measured

## 1. Finding (SR-J3D-LEANNESS-ROW)

J-3d flagged six classes (`achievement_recognition`, `business_launch`, `financial_deception`, `foreign_settlement`, `parental_event`,
`property_acquisition`; <= 38 intervals) because their seconds per interval is above 2 x the median. Their *cost* is not their interval
count: every class mints one `ka_gochara_relationship_record` per CONTACT it touches, and the tiny classes touch ~2,000 contacts (J-3d
`leanness.rows[].contact_count`: 464 / 2,063). Measured on a lane database with the full 1998-2031 horizon, one such class writes 792 records
and costs, per record, **14 statements, each its own network round trip**:

| per record | statements |
|---|---|
| physical object insert-if-absent + read-back check | 2 |
| contact identity insert-if-absent + read-back check | 2 |
| contact insert + stored-row check | 2 |
| relationship record insert + read-back | 2 |
| prerequisite insert + membership read-back | 2 |
| prerequisite result update + read-back | 2 |
| admission-state update | 1 |
| anchor-column catalogue probe (`pg_attribute`) | 1 |

`business_launch` (a 38-interval class) sends 12,467 statements in its 11 substeps: 11,231 in the record substeps and 1,016 in the window substeps (792 of them membership inserts).
Against a remote database the round trips are the class's wall time (production tiny classes: 30-320 s; the same class on a loopback database:
1.4-4.4 s). The avoidable part is the transport, not the work.

## 2. What changed (no output change; no FROZEN path; no writer-contract change)

* `services/gochara_kernel/record_store.py` — `pipelined(conn)`: the statements of ONE write group are sent in one round trip (libpq pipeline
  mode; the SQL, parameters, order and every read-back check are unchanged; the checks run after the group). Groups: object | identity |
  contact row | record + prerequisites | prerequisite result + admission state. The object and the identity stay separate groups ON PURPOSE: each
  is checked before the statement that depends on it, so a collision still raises its own `IdentityCollisionError` instead of a foreign-key error.
  `p1_anchor_columns_available()` reads the catalogue once per store (one substep) instead of once per record.
* `services/gochara_kernel/window_store.py` — a grain's window and membership inserts (no read-backs) go out as one group.
* A connection without `pipeline()`, a libpq without pipeline support, or `record_store.PIPELINE_ENABLED = False` runs the old one-statement-at-a-time path.

## 3. Measured (same machine, same load window: before/after interleaved; 3 runs each; median; load average 8-14 from other jobs)

Lane database: `a53t_lean_*` on the local cluster (127.0.0.1:55433), real Swiss corpus, sky substrate for all 8 bodies, canonical chart fixture.

**A. Six tiny classes, 1998-2031, loopback database (seconds per class)**

| class | before median (runs) | after median (runs) | change |
|---|---|---|---|
| achievement_recognition (first: carries the one-off verify warm-up) | 56.06 (67.75 / 56.06 / 49.68) | 52.27 (52.27 / 55.62 / 48.18) | -7% |
| business_launch | 4.28 (4.28 / 4.14 / 4.29) | 3.87 (3.90 / 3.87 / 3.03) | -10% |
| financial_deception | 1.51 (1.64 / 1.51 / 1.41) | 1.53 (1.66 / 1.53 / 1.12) | +2% (noise) |
| foreign_settlement | 4.52 (4.41 / 4.52 / 5.13) | 3.55 (3.55 / 3.55 / 3.50) | -22% |
| parental_event | 1.65 (1.65 / 1.62 / 1.86) | 1.27 (1.33 / 1.09 / 1.27) | -23% |
| property_acquisition | 4.42 (4.42 / 4.38 / 4.53) | 3.64 (3.57 / 3.64 / 3.75) | -18% |
| sum without the first class | 16.41 | 13.68 | **-17%** |

**B. The same six classes behind an EMULATED remote database** (in-process delay proxy, 2 ms each way = 4 ms round trip; labelled lab figure,
NOT a production measurement)

| class | before median | after median | change |
|---|---|---|---|
| achievement_recognition (first) | 114.40 | 85.19 | -26% |
| business_launch | 72.88 | 28.24 | **-61%** |
| financial_deception | 19.75 | 9.69 | -51% |
| foreign_settlement | 70.17 | 30.24 | -57% |
| parental_event | 19.44 | 10.13 | -48% |
| property_acquisition | 69.62 | 31.00 | -55% |
| sum without the first class | 251.85 | 109.12 | **-57%** |
| network round trips, whole run (3 runs, exact) | 57,549 | 21,996 / 21,997 / 21,998 | **-62%** |

The first class (alphabetically `achievement_recognition`) also pays a one-off ~50-70 s verify warm-up (the cross-class geometry cache of
`contact_reconstruct`); that cost is untouched here.

**C. A large class** (`marriage`, one-year horizon, plus two tiny classes; loopback): marriage 49.91 -> 49.55 s (-1%): its time is point solves
(P3/P4), not round trips. No regression; no claim of a gain.

Where the time still is (not changed here, listed for the owner): per substep ~45 round trips of `_verify_live_inputs` (11 substeps per class);
`swisseph.set_ephe_path` re-run on every position probe (~110 us of ~115 us per call; the per-call re-assertion is documented doctrine in
`panchang_engine/swiss_thread_scope.py`, so it was NOT removed); the first-class verify warm-up.

## 4. Byte identity (proof the output did not change)

`dump.py` fingerprints every row of all 30 `ka_gochara_*` / `kala_gochara_*` tables (to_jsonb minus the DB clocks), sorted, sha256, per table and
per event class. Before and after trees were run on the same lane database with the IMPLEMENTATION identity held constant (the source digests of
the governed modules are bound into every input digest, so without pinning them the digest columns differ by construction):

* six tiny classes, 1998-2031: 15,400 rows over 30 tables — **byte-identical** (`cmp` of the two fingerprint files exits 0);
* `marriage` + `achievement_recognition` + `financial_deception`, 2025: 4,258 rows over 30 tables — **byte-identical**.

Without the pin the only differing columns are `input_digest`, `inventory_digest`, `ledger_digest`, `input_generation_vector` (their implementation
component) and the DB-clock `finalized_at`; the same difference appears between two RUNS of the unchanged tree for `finalized_at` alone.
Not run: a full-horizon `marriage` (hours of point solves); the large-class identity claim is for the one-year horizon.

## 5. Digests (generated outputs are CI-owned and were NOT edited)

| digest | HEAD (528be80fe) | this tree |
|---|---|---|
| writer source hash of `ka_gochara_v5` (`provenance_inventory`, `get_writer_source_hash`) | `eb99cf563832ddf436d1d01e4fd2a38011481db655c64c2db1f0ba8c76717779` | `58cc66c43de57ad4d94c122ca746fb7666f9c3320a78f8d29ceaa33612497f1a` |
| governed implementation digest (`implementation_registry.compute()`) | `f32330c9ed0c378302954b194bd14d6b9ec4d37c58a6086278b8108f8c30b036` | `942ef17375a3679f8c8c57720da93109a50a03a0e0e628e02b55073007eb1aff` |
| stage `geometry` (`record_store`) | `e7634d7faf7df43521f5236d79a94c8a31192e62d78dc8eaa939160eaca0a6f7` | `4479243d6b7a9b8579cf7f9eb6b8d363bdd12722d24d9ff813c3b14a1e0680eb` |
| stage `window` (`window_store`) | `78b4d0a1cc63047045710a873f76b87f90de4493c4960bb08fd97ef1ad13aea3` | `3aab549f11cd9e52e9c368bd7f596460fb5bb7bb5ae9b829a0f3235cc2ebc5a4` |
| stage `evaluation` | `9f6c462e41ee255517dc9619e469ef8a77eab1acfccf40cabef03c6a18835bcf` | unchanged |

`platform/src/generated/nirmana-writer-digests.json` and `services/gochara_kernel/implementation_digest.lock.json` are `ci_generated.py` OUTPUTS:
this branch does not edit or regenerate them; CI regenerates both from the merged tree (the checked-in writer-digest inventory,
`fc6a22f0...`, already differs from HEAD's computed hash, so it is stale before this change too). Because the governed implementation digest moves,
any build made before the merge is bound to the old digest and a build after it to the new one — the change takes effect only for a build started
from the merged image, exactly as every governed-code change does.
