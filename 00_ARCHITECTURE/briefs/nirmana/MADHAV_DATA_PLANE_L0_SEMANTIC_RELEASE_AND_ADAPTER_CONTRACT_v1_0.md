---
artifact: MADHAV_DATA_PLANE_L0_SEMANTIC_RELEASE_AND_ADAPTER_CONTRACT
version: "1.0"
status: IMPLEMENTED
produced_on: 2026-09-13
semantic_release_id: l0.semantic.2026-09-13.1
semantic_release_digest: b5563e1eea87ca06b5e912b902869483b4bbb1b3b2c87ed6bed9bc8d892ad2a7
owner: bg_ontology
---

# L0 semantic release and adapter contract

## Authority

`platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json` is the immutable
lexical release for this packet. `bg_ontology` owns identity; specialized L0
assets own their narrower semantics; `bg_reference` binds those semantics to the
released identities; indexes and concordance navigate but do not define identity
or source truth. Python and TypeScript modules are deterministic adapters, not
rival registries.

The release records stable `identity_id`, canonical subject code and label,
Unicode/transliteration aliases, roles, physical variant, interface/generation,
compatibility and digest. NFC + trim + casefold is the comparison operation.

## Node correction and compatibility

`rahu:mean_node`, `rahu:true_node`, `ketu:mean_node` and `ketu:true_node` are four
distinct physical identities. Bare Rahu/Ketu and legacy RAH/KET retain their
historical mean-node defaults. Explicit RAH_TRUE/KET_TRUE no longer collapse to
mean nodes. Generic `node` and `lunar node` are ambiguous and the strict adapters
fail closed. Unknown values also fail closed.

The legacy Python `norm_graha` surface intentionally retains unknown-value
upper-case pass-through for existing consumers; new producer code uses the strict
resolver. Its minimal literal compatibility floor is detector-only and verified
against the release at import; it is never used to resolve an identity.

## Adapter and correction surface

| Surface | Contract | Failure detector |
|---|---|---|
| `l0_semantic_release.py` | Validates schema/digest/collisions/node variants and returns released identity copies | import and tampered-release tests |
| `graha_vocabulary.py` | Release-derived aliases/titles plus explicit legacy wrapper | census, compatibility and node tests |
| `graha_labels.ts` | Release-derived strict TS identity/code adapter | Vitest alias, ambiguity, unknown and physical-variant tests |
| `parity_check.ts` | Derives the current 36+4 L0 inventory from generated authorities | 40/40 cardinality and named non-writer tests |

Changing identity, physical variant or canonical code is a semantic correction:
publish a new immutable release/generation, invalidate identity-keyed adapters and
producer fixtures, and retain the previous release for replay. Alias-only additions
do not stale astronomical computations or historical readings. No stored identity
or downstream consumer was rewritten in this packet.

## Evidence boundary

Cross-language identity behavior is proved at producer-adapter level. Ingestion,
retrieval-query, Paripraśna, MCP and synthesis integration are deliberately
unmodified and therefore remain `NOT_REACHED`, not inferred from adapter tests.
