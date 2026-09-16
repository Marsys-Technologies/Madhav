---
artifact: MADHAV_DATA_PLANE_L1_RESOURCE_CONFIG_SLICE
version: "1.0"
status: VERIFIED_SYNTHETIC_PRODUCER_SLICE
slice_id: L1-SLICE-RESOURCE-CONFIG-01
generation_id: l1-resource-config-g1
content_sha256: 25c46b559def7e1a9f8e1a05114be5a6c306a846a23b2665b1b5c917128d3279
fixture_id: synthetic.non_person.l1-resource-config-01.v1
implementation_commits:
  - 7cabc0cfd1eae83f0a1054132d3c850c6b760153
  - 3cb1a84ae
  - bcda11997
  - 0fc45813e
  - b2c4f1d7f
  - a9c44c298
---

# L1-SLICE-RESOURCE-CONFIG-01

The executable slice is
`platform/python-sidecar/ga_writers/data_plane_resource_config_slice.py`; its sole
input is the committed deterministic non-person fixture
`ga_writers/__tests__/fixtures/l1_resource_config_non_person_v1.json`.

| Pin | Exact value |
|---|---|
| L0 semantic release | `l0.semantic.2026-09-13.1` |
| L0 semantic digest | `665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1` |
| L0 resource generation | `l0-resource-config-g1` |
| L0 resource digest | `d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a` |
| L1 context | `l1ctx:cd0bb71550b6021c7f464fab` |
| L1 content digest | `25c46b559def7e1a9f8e1a05114be5a6c306a846a23b2665b1b5c917128d3279` |

The bundle contains a complete D1 natal calculation context plus an explicit D9
relationship-domain sensitivity target; stable
position, house, karaka and condition facts; explicit real zero; all six non-value states;
an exact one-day synthetic interval; changed and unchanged boundary perturbations; and a
decomposed resource configuration occurrence.

All fixture dependencies resolve to one of the 11 emitted fact IDs or an exact identity in
the accepted L0 dependency registry, with the accepted semantic release/digest recorded.
Unknown `l0:`/`external:` strings fail closed. The relevant perturbation calls the admitted
production D9 Navāṃśa evaluator, records its D1 comparison, crosses the computed D9
boundary and changes output; the irrelevant perturbation stays within the D9 segment and
does not. Unknown formula/domain identities fail closed. The full digest above is asserted
as a golden value by both the unit suite and standalone validator. Personal chart and
subject identities are rejected.

Bhāvat Bhāvam is present only as an unapplied L0 package reference:
`UNQUALIFIED_SOURCE`, L2 owner, primary-house facts preserved, positive doctrinal arm
`NOT_REACHABLE`. The engineering fixture exercises state machinery without claiming
doctrine. Personal/stored chart IDs are rejected.

Terminal slice truth: producer fixture `PASS`; integrated `NO`; deployed `NO`; consumer
value demonstrated `NO`; empirically evaluated `NO`.
