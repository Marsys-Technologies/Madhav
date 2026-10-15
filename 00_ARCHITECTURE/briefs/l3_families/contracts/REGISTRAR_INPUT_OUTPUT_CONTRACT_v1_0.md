---
artifact: REGISTRAR_INPUT_OUTPUT_CONTRACT
version: "1.0"
status: PREPARATION — fixture-only; live admission and reference cutover pending
item: K6-5
authority: KYD-141; ALGO 3.8; PLAN sections 4.1, 7, 9, 10
produced_on: 2026-10-10
changelog:
  - "1.0: pin the complete registrar input/output boundary using K6-5a storage."
---

# Registrar boundary

The explicit entry is `ctx.config.registrar_fixture_inputs`, a sequence of typed
`RegistrarInput` values. The default writer continues legacy computation, and
its jury preparation entry remains intact. No stage row becomes an issue during
an ordinary rebuild. This contract supplies consumer fixtures only; the conductor
must admit actual producer, delivery-confirmation and ontology bindings before
live issue creation. The entry refuses every non-fixture manifest.

| Input | Exact mapping and admission |
|---|---|
| Issue/version | Explicit UUID `issue_id`, positive integer `version`; never rank, timestamp or assertion-id synthesis. |
| Episode | Explicit `event_class`, `phase`, `affected_person`, `episode`; outcome clustering includes chart identity. |
| Manifest | Chart from context, `generation` from input, `build_id` from context; actual `kala_layer_candidate` columns `state`, `model_digest`, `conventions`; fixture manifest must be complete/verified, never building/rejected/published or current serving head. |
| Producer/coverage | Nonblank `producer_ref`, `coverage_ref`, matching `conventions.registrar` fixture pins. These are fixture locators, not admitted live source bindings. |
| Qualification | `qualification_ref` matches fixture pins; event-class-specific `result_policy` and `calibration_status` must exactly match `conventions.registrar.classes[event_class]`; model digest must match the manifest. This JSON is test preparation, not an invented production qualification column. |
| Delivery | Typed `DeliveryConfirmation`: confirmed boolean true, exact issue/version and statement, named channel, aware `delivered_at <= issued_at`. No transport is invoked and no external delivery is claimed. Missing confirmation means no issue. |
| Statement/time | Nonblank delivered statement copied verbatim; aware `issued_at`, `information_cutoff <= issued_at`; no current-time defaults. |
| Windows | Explicit finite, nonempty half-open `tstzmultirange`; disconnected windows preserved; declared nonblank `disclosed_grain` and `point_functional`, including explicit `none`. |
| Probability | Nullable numeric target; nonnull only with calibrated class and a policy other than `all_null`; nonfinite and out-of-range numbers refused. No score conversion or probability tier. |
| Ontology | Typed `ObservationPredicate`: exact event class, canonical domain, nonblank locator and predicate matching that class's manifest fixture pins. Domain/predicate never inferred from statement keywords. |

The output is the existing `issued_forecast` schema, with **all** columns supplied
to `insert_immutable_checked`. Its immutable `(issue_id, version)` key stays
separate from the episode key. The `falsifier` JSON stores the supplied ontology
predicate/domain plus pinned producer, coverage, qualification and model
references. Delivery text and times are copied without narration. No legacy,
published, manifest, outcome or L4 row is written. Dry runs only validate.

Results report new insertion, equal retry, not-delivered candidate, or
`information_unavailable` with a named missing/invalid binding reason. A changed
retry raises `ImmutableIssueConflict`; no issue is rewritten. The orchestrator
retains transaction ownership. L5 outcomes still reference exact versions and
cluster evaluation credit by `(chart_id,event_class,phase,affected_person,episode)`.

The unchanged L4 `phala_anchors` protective read remains required until accepted
L5 integration and downstream reference acceptance. Existing archived issues
are never updated, reclassified or deleted. Reference-protection cutover, live
qualification, protected upstream application, deployment and publication are
not established by these fixtures. No new migration or asset is introduced.

Certification: the registrar's append-only helper remains **FAIL under the
current Idem detector**, routed to PLAN section 7/R-10 for reviewed immutable
insertion treatment. Deletion must never be added to earn a green detector.
The legacy detector result still describes the legacy branch. The other K6
read-model mappings remain their owning items' responsibility.
