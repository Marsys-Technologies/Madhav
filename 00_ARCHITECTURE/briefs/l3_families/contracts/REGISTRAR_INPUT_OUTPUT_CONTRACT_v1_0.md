---
artifact: REGISTRAR_INPUT_OUTPUT_CONTRACT
version: "1.1"
status: PREPARATION — fixture-only; live admission and reference cutover pending
item: K6-5
authority: KYD-141; ALGO 3.8; PLAN sections 4.1, 7, 9, 10
produced_on: 2026-10-10
changelog:
  - "1.1 (2026-10-16, K6-N1): reconcile merged default dispatch, historical-only L4 safety and fixture/live admission limits; no runtime change."
  - "1.0: pin the complete registrar input/output boundary using K6-5a storage."
---

# Registrar boundary

The default append-only registrar is `KaBhavishyaLekhaWriter`. Both
`registrar_inputs` and `registrar_fixture_inputs` in `ctx.config` accept a sequence
of typed `RegistrarInput` values and call the same immutable registrar. The
fixture key takes precedence, even when empty; next, `jury_reader_generation`
selects the retained jury preparation entry; otherwise the default reads
`registrar_inputs`. Absent inputs or an empty sequence perform no SQL and return
zero rows with `no_delivery_inputs`. No stage row becomes an issue during an
ordinary rebuild, and no legacy rebuild runs on that path.

Both keys still require a complete/verified fixture manifest and explicit
delivery confirmation. This contract supplies consumer fixtures only; the
conductor must admit actual producer, delivery-confirmation and ontology bindings
before live issue creation. Both entries refuse every non-fixture manifest.
Source: `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py:768`
(shared helper), `:790` (registered default), `:803` (dispatch precedence).

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

`_LegacyKaBhavishyaLekhaWriter` is unregistered and retained for historical safety
oracles only, including the L4 `phala_anchors` protective read. The default
registrar never reads L4 and never updates, reclassifies or deletes legacy rows
or archived issues. Historical foreign keys and safety oracles remain intact;
this dispatch change does not establish downstream L4 reference acceptance.
Source: `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py:88`;
see `ISSUED_FORECAST_LIFECYCLE_CONTRACT_v1_0.md:18` and `:133` for lifecycle custody.
Live qualification, protected upstream application, independent acceptance,
parent completion, deployment and K9-4b publication are not established by these
fixtures. No new migration or asset is introduced.

Certification: the registrar's append-only helper remains **FAIL under the
current Idem detector**, routed to PLAN section 7/R-10 for reviewed immutable
insertion treatment. Deletion must never be added to earn a green detector.
The legacy detector result still describes the legacy branch. The other K6
read-model mappings remain their owning items' responsibility.
