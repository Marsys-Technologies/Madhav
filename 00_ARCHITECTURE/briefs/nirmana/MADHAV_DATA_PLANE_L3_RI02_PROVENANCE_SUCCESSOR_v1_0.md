# MADHAV Data Plane L3 RI02 Provenance Successor v1.0

**Decision:** DP-SD-018 / RI02-R-001
**Authority commit:** `7f21f27b14a7909424591a530096dc2f5d6e2b13`
**Input tree:** `5142109f7f219ea860f859e322646f79d875bee8`
**Immutable source-inventory predecessor:** `d2369b888e760e5b8d693328f00683877cbd5f28`
**Disposition:** IMPLEMENTED, PENDING INDEPENDENT EXACT-TIP REVIEW

## 1. Bounded result

The checked-in writer inventory was recomputed from the real writer/import
closure. Versioned successors were admitted for L0, L1, L2, metadata-only L3,
and metadata-only L4. L5 remains byte-for-byte unchanged. The admission does
not change writer behavior, physical data, deployment state, layer freeze, or
elevation acceptance.

The source inventory was committed first, so every successor names an existing
immutable predecessor rather than its own future commit. Each predecessor pin
and its complete layer writer snapshot is retained under `history`; historical
receipt bases are reconstructed only from that archive and never from mutable
current inventory.

## 2. Old and new layer identities

| Layer | Historical snapshot | Old aggregate | New aggregate / disposition |
|---|---|---|---|
| L0 | `c558e60d3267ded79d65fd25f50ee926ce27b75a` | `5125cccb68715ebc6054c3ce47bc4c047684445249503a4c4dabd85e0d036178` | `3dda261170ee0dc879071d43d8e266e5cbf5c715775f94d2a27edaeee1c9e146` |
| L1 | `c558e60d3267ded79d65fd25f50ee926ce27b75a` | `55984558527e9c1b95da608839b69a4dde255b3855ac6839980c26b24c2b17e0` | `3e8816fc708ac9b93d1551269be702651add7e7b246f74049303493e62f8db40` |
| L2 | `c558e60d3267ded79d65fd25f50ee926ce27b75a` | `863a3e6e6b67320fd5de7d00c6093307a9f2c816e39af09c4b4bc9341af8169b` | `ad143c22bd8d21e2d8d4c1ecef399b8ba3c46d3b5347757cfbeeece35af9dc16` |
| L3 | `5142109f7f219ea860f859e322646f79d875bee8` | `a32b7cc7b4fc82cce56ffa2d84331633bc75dd5c39fd829a303a269f3ebb9667` | `44e78dc0ccbce53661d79dcc43188382604e25d57667d8afff0a7339110e6e3b` (metadata only) |
| L4 | `c558e60d3267ded79d65fd25f50ee926ce27b75a` | `486959b1df74015873b326c2b5d58aa00865a47e6116b3b0c39f479f978d66f9` | `e73988c0dd03174681e8e98ba7c6e6bdc77ca27b9e6a6a90458c814eba51c7ac` (metadata only) |
| L5 | not superseded | `df295e3ac158980ee69a210ecfd6252ffa2a4cb2db1ae8e732af7814240883bc` | unchanged; no history entry |

All admitted active successors bind to source commit `d2369b888e760e5b8d693328f00683877cbd5f28`.

## 3. Exact delta classification and trace

- **L0 — approved intentional:** `bg_cohort`, `bg_gochara_arcs`, `bg_remedies`.
  **Derived/import closure:** `bg_ephemeris`, `bg_muhurta_lattice`, `bg_rules`,
  `bg_sky_calendar`. Acceptance artifact: L0 producer-ready acceptance at
  `f6fed12c794224329f6b3b436f8b1b814499d06d`, content SHA-256
  `abeb3ffa67d646bdbf4777145ba43e97318e04da9226c78a3fb2e0876b7e76f4`.
- **L1 — approved intentional:** `ga_ayurdaya`, `ga_condition`, `ga_dashas`,
  `ga_medical`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_prashna`,
  `ga_sade_sati`, `ga_sensitive`, `ga_sensitive_degree`, `ga_strength`,
  `ga_structural`, `ga_tajaka`, `ga_transit_anchors`, `ga_vargas`, `ga_vichara`,
  `ga_yoga`. Acceptance artifact: L1 producer-ready acceptance at
  `18503e9c2dbb140f5d17b4bc34a5f6d087f97c38`, content SHA-256
  `265ed113e94915ee3dcaa55c842bf3fd61f6a71320ffe33f3dbd22e87a82c267`.
- **L2 — approved intentional plus derived/import closure:** `bo_anveshana`,
  `bo_arudha`, `bo_bimba`,
  `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_chart_gestalt`,
  `bo_drishti`, `bo_grounding`, `bo_karanajala`, `bo_laksana`,
  `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_pramana_mapa`, `bo_pratijna`,
  `bo_samskara`, `bo_samvada`, `bo_sangati`, `bo_special_lagna`, `bo_sudarshana`,
  `bo_upaya`, `bo_vargottama_dhana`, `bo_yantra_mechanism`. `bo_grounding`
  remains supporting infrastructure and stays outside the 22-asset receipt
  denominator while remaining inside the inventory hash. Every listed digest
  combines the accepted L2 producer source with later imports from
  `services/ka_dasha_kala/service.py` and `services/ka_tulana/ranker.py`; the
  latter shared-source changes were accepted by L3 W2. Required acceptance
  artifacts are the L2 producer-ready acceptance and L3 W2 first-frontier source,
  both preserved at `5142109f7f219ea860f859e322646f79d875bee8`, with
  content SHA-256 respectively
  `adc2b3c9eceee0e51018c068f5a9e1a6554fa3d1421d5c4e16c5d1b744768b9e` and
  `27ba58e10997ae9c35053d75d11d044c66220053c7a0dc4bdc8727bc09bcf781`.
- **L3 — derived/import closure only:** `ka_sangam`. This is the narrowly ruled
  RI02-R-001 consequence of the accepted shared W2 source at
  `47131772b355ae2c67b1f6fb2b90e9fa007e2202`; no other L3 identity is admitted.
  Acceptance artifact: W2 first-frontier source at
  `5142109f7f219ea860f859e322646f79d875bee8`, content SHA-256
  `27ba58e10997ae9c35053d75d11d044c66220053c7a0dc4bdc8727bc09bcf781`.
- **L4 — derived/import closure only:** `ph_muhurta`, `ph_rectification`.
  Both changes are consequences of the accepted shared Swiss-state source, not
  new L4 implementation. Acceptance artifact: Swiss-state independent validation
  at `f6fed12c794224329f6b3b436f8b1b814499d06d`, content SHA-256
  `0f87dc072590179cc9a5e8b928bf30a0436de5d13b3d1e9ed4c20ce31aceee79`.
  This is provenance metadata only.

No delta was classified as generator defect, stale receipt, or
unapproved/foreign source. An `unapproved_foreign_source` classification is an
explicit hard rejection and cannot be admitted.

## 4. Successor and rejection properties

`nirmana-analysis-layer-pins/v2` appends
`nirmana-analysis-layer-successor/v2` records. Admission requires an exact
immutable source, authority, historical pin snapshot and definition snapshot;
a content-addressed layer-specific acceptance artifact with its expected
decision marker; a non-empty reason; and a classification for every and only
the changed asset identities. The authority commit is likewise bound to the
exact DP-SD-018 strategic-ledger blob, SHA-256
`e530098ba7199d30099fdef9fb40fde60b75a54b594fe79cb6dbc22b3ae224fc`.
The command requires the working
inventory to equal the inventory stored at the named source commit.

The immutable definition snapshot at
`5142109f7f219ea860f859e322646f79d875bee8` binds each layer's complete receipt
membership and exact non-writer set. Verification enforces sorted unique
identities, layer prefixes, no writer/non-writer overlap, and the single
governed L5 exception `lel_events`. The protected retired
`ka_gochara_sweep` identity remains required in L3.

| Layer | Immutable membership SHA-256 |
|---|---|
| L0 | `e136c56d9720f7383234f9c524fd1756071fa0e4dabfee8b6367a8a562139bbd` |
| L1 | `967e107735c2c0ff2174fad8886aefb6b86e60a680f4c35c9b9c3ab8c759cc24` |
| L2 | `ed79468208d665dc9eb7f47bf70392e058f6a1b7d1f51ad492afdbaad7f058bb` |
| L3 | `b0df0e0a5767c530ca8161c11e768d6e2797830a53b8445e0751736f6d8bc4ab` |
| L4 | `367159d666a511051e6364788a6638009b832fb4529409c01aa4869fa25388a4` |
| L5 | `70221ef549ea99db55541d0f09a78650b22ec634575314f2b6f89711a356db53` |

Offline verification re-derives active and historical aggregates and receipt
counts, checks source/convergence identity, acceptance-artifact bytes,
definition membership, exact archived pins at their snapshot commits, every
predecessor-to-successor delta, a complete single linear chain, layer isolation,
and the retained frozen L0 baseline. Tests reject nonexistent authority/review
commits, a wrong acceptance artifact or digest, wrong-source metadata, a
wrong-layer delta, a wrong current or historical hash, a rewritten historical
pin, stale generation identifiers, non-writer overlap, removal of protected
`ka_gochara_sweep`, missing/excess classification, and unapproved/foreign deltas.
A valid two-successor chain is also reconstructed and checked recursively.

The archived L0 generation
`l0:49bb5c98b864:5125cccb6871` reconstructs all 40 prior receipt bases. Their
canonical serialized base-map SHA-256 is
`bac97201ca2b3ecc070459b54e83d970c904bef3149f37823f231624a0858d2a`.

## 5. Verification run

- `python3 -m pytest -q platform/scripts/__tests__/test_nirmana_analysis_layer_pins.py`
  — 12 passed.
- `python3 platform/scripts/generate/nirmana_analysis_layer_pins.py --check`
  — current.
- `(cd platform/python-sidecar && python3 -m pipeline.orchestrator.provenance_inventory --check)`
  — current.
- Focused Vitest for generic and deprecated L0 receipt modules — 13 passed.

## 6. Residual holds

This packet is not an independent review of itself. Exact-tip independent
review remains required before acceptance. It provides no runtime parity,
database, deployment, protected-branch, freeze, or elevation evidence. L3 W2
acceptance remains intact; L5 and all unaffected receipt evidence remain
unchanged.
