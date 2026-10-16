---
artifact: KSHETRA_G2_BRIEF_v1_0.md
version: '1.0'
status: PREBUILD_ONLY — SR-A4-01; D-VC/D-G2 and activation are not asserted
authored_on: 2026-10-16
changelog:
  - '1.0: explicit replacement model and isolated candidate implementation; test-first.'
---

# K5-3: specified replacement forecaster

Authority: `KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md` §3.20 G2 (lines
433–435), `KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md` §9 row 8 (line 458),
CLAUDE.md §N.2–N.8. This is the replacement functional form and parameter
contract, not fitted parameters, value evidence, decision approval or activation.
D-VC nonapproval parks G2 and preserves the G1 baseline. The registered G1 writer
and every live reader retain their existing path.

## Event process and risk set per class

Every `EventModel` explicitly names class, version, process, risk-set identity,
eligibility reference and censoring reference. `RiskSet` provides sourced,
half-open eligible intervals on **absolute Julian days**, with evaluated,
information_unavailable or outside_risk_set state. Unknown eligibility is not
zero exposure. Outside risk is evaluated zero exposure. No age, sex, relationship
status, calendar or lifetime horizon is inferred. No class model is auto-selected.

(I) INTERPRETATION: these are admissible class-specific definitions, modelling
choices rather than classical assertions or facts about the native. An executing
parameter bundle must bind the actual eligibility detector/source and episode
definition. Alternative: one homogeneous recurrent process for every class;
refused because a span and an event are different estimands.

| Class | Process and eligible risk definition |
|---|---|
| achievement_recognition | Recurrent distinct recognition episodes; declared eligible observation time. |
| bereavement | Recurrent losses; explicit affected-person relation and coverage. |
| birth_anchor | Not prospective here; no eligible intervals or synthetic hazard. |
| business_launch | Recurrent distinct launches; declared launch/exposure definition. |
| career_advancement | Recurrent advances; career participation and detector coverage. |
| career_change | Recurrent changes; career participation and transition definition. |
| career_entry | First entry; not yet entered at cutoff; conditional hazard until entry/censoring. |
| career_setback | Recurrent setbacks; career participation and setback definition. |
| childbirth | Recurrent births; source-declared person/parental-role eligibility, no inferred biology. |
| chronic_onset | First onset per named condition; condition-free at cutoff. Another condition needs another model/risk identity. |
| education_milestone | Recurrent milestones; declared education participation/coverage. |
| exam_outcome | Recurrent outcomes; explicit examination exposure intervals. |
| financial_deception | Recurrent episodes; declared financial exposure/coverage. |
| foreign_settlement | Recurrent settlement transitions; declared residence-transition eligibility. |
| illness_acute | Recurrent episodes; sourced recovery/re-entry and episode separation. |
| major_gain | Recurrent gains; financial exposure and magnitude definition. |
| major_loss | Recurrent losses; financial exposure and magnitude definition. |
| marriage | First union under an explicit first-marriage model, or distinct recurrent unions under a separately named model; status/entry/re-entry sourced. |
| parental_event | Recurrent episodes; explicit parent/relation and observation coverage. |
| property_acquisition | Recurrent acquisitions; declared transaction definition/exposure. |
| psychological_arc | Span/duration: not_evaluable with span_requires_duration_model here; no count/odds. |
| relocation | Recurrent residence transitions under a declared episode definition. |
| romantic_start | Recurrent relationship starts; declared eligibility/re-entry. |
| separation | Recurrent separations; eligible relationship spells, not already-separated time. |
| spiritual_turn | Recurrent distinct transitions only under an event definition; ongoing spans use the separate span path. |
| surgery | Recurrent procedures; procedure/episode definition and coverage. |
| travel_event | Recurrent trips; episode separation and eligible observation intervals. |

Left truncation begins at supplied eligibility; right censoring ends at supplied
horizon/coverage. First-event hazard is conditional on no event before cutoff;
a terminal endpoint is usable only if known at cutoff. Recurrent re-entry needs
an explicit spell definition. Risk intervals cannot overlap. This service neither
fetches future adjudications nor infers eligibility from their absence.

## Baseline, graph features and coefficients

Each independent admitted route r declares a positive baseline b_r in
**events/eligible_day**, its source, mechanism identities, and every coefficient
`(key, beta, provenance, origin, preregistration)`. No numeric parameter bundle is
shipped. There is no lifetime-count substitution or 1.0 rate. Missing baseline
means absent route plus flag; partial integrated intensity is disclosed and
expected count remains null. Learned coefficients require frozen preregistration;
fitting/calibration remain separate evaluation operations. Declared coefficients
also require provenance. Labelled synthetic test parameters are not adopted
chart or population values.

(I) INTERPRETATION: specify a source-bound parameterized family and require its
complete numeric parameter bundle at execution, rather than adopting unprovided
seeded replacement coefficients. That alternative would invent evidence.

Every route explicitly maps its F1 features, including an explicitly empty map:

- `admitted_count(role)` counts distinct admitted mechanisms with resolved F1
  relationships of that role and grounded fact IDs. Testimony never contributes.
- `effective_cancellation` indicates a grounded defeated conclusion; every
  requested mechanism must have an evaluated conclusion. Unresolved means
  unavailable, not false. Fact, defeat and conclusion references are retained.
- `rule_local_dominance(rule_id)` consumes only an explicit grounded upstream
  rule-local operand. F1 supplies no universal dominance number today, so that
  feature is absent with a flag until supplied.

(I) INTERPRETATION: formation counts and cancellation are separate regressors.
Alternative: count only effective formations, which conflates formation/effect.
`assemble_cells` uses the existing `PromiseGraph`/`Relationship` types, refuses
caller shadow values or mechanisms outside a route, and preserves every knot.
Missing upstream coverage never means evaluated zero.

```
log lambda_r(t) = log b_r + sum_k beta_rk * x_rki(t)
lambda_class(t) = sum_r lambda_r(t), within eligible risk intervals
```

Each x is affine inside its supplied elementary cell, with value at the left
boundary and slope/day. Role/cancellation features are constant; sourced clock
or other timing operands may be affine. An unavailable x contributes **no
term or slope**, emitting `route:key:information_unavailable`. A missing key is
malformed input; an evaluated sourced zero is valid. There are no seeded beta,
rho or P-tilde fallbacks. A partial field cannot earn odds.

(I) INTERPRETATION: independent cause-specific route intensities add. Alternative:
a competing-route mixture with learned weights, for which no evidence exists.
Additivity is a model declaration, not an empirical independence claim about a
native; activating parameter bundles must qualify their route/event semantics.

## Suppression operator (ruling 9)

Every suppression names exactly one route and its sourced operand. Unavailable
operands are absent with a flag; unrelated routes are invariant.

- `reduced_intensity`: explicit factor [0,1] on that route; factors multiply.
- `delayed`: nonnegative days translate its full field before risk/horizon
  clipping; multiple explicitly declared delays add.
- `less_favourable`: typed valence annotation, with occurrence rate unchanged.

(I) INTERPRETATION: delay is deterministic translation rather than an unspecified
kernel; valence remains an annotation rather than a negative occurrence hazard.
Nonconstant suppression operands are refused; split upstream into explicit
partitions/route-model versions before use. No chart-wide multiplier is inferred.

## Numerical, probability, null and uncertainty contract

No compact evaluator or knot subset is selected. Callers supply the **full**
contiguous route partition: kinematics/envelope knots, maximum switching roots,
clock/scenario boundaries, mask edges, seams and any qualified adaptive cells.
Every supplied boundary is retained; translated/risk-clip boundaries are added.
Gaps/overlaps and missing eligible horizon coverage before delay are errors.
This API cannot certify that an upstream omitted root never existed; upstream
breakpoint qualification remains an activation gate. Each route stays log-linear;
the class sum is not falsely stored as one log-linear segment. Evaluation is
half-open/right-continuous. Integration uses the analytic expm1 form per route,
then sums. No upstream approximation or floating-roundoff bound is invented.

Only an explicit first-event model with an externally supplied calibration
receipt can yield `p=1-exp(-H)` and odds `exp(H)-1`. The receipt must have status
calibrated, matching model digest/risk identity/process/exposure interval, source,
evaluation ID and n>0. This validates receipt binding, not calibration quality;
independent acceptance remains a gate. Recurrent output is expected count only;
no Poisson count distribution is assumed. Span models return neither count nor
odds. Parameter/numerical/predictive uncertainty are separate nullable fields.
Unrepresentable odds are null.

G2 null statistics are null with `G2_null_estimands_not_evaluated`, never copied
from G1. Activation requires shared preparation/shift schedule with the jury,
three separate estimands (incremental agreement, pipeline selection, class field
maxima), denominator shifts+observation and circular-shift surrogate disclosure.
No G2 significance is served. Existing G1 null/engine paths remain unchanged.

## Candidate storage, compatibility and activation gates

`write_graph_candidate` performs F1 projection → field → candidate. The caller
owns its existing context/connection/transaction/savepoints. `write_candidate`
also accepts assembled sourced operands for isolated kernel use. The manifest
must explicitly pin class model digests, upstream source pin, as_of JD and
prebuild_only:true. Input bytes cannot change on retry; open a new generation.
Rows live in additive `kala_kshetra_g2_candidate`, keyed by chart × NEW candidate
generation × class, plus an input-vector grain. Manifest lifecycle locks are
shared. Python and SQL refuse published/nonbuilding/wrong-build writes; SQL
refuses UPDATE/TRUNCATE. No registry dispatch, serving pointer, legacy row or
asset throughput changes. Ordinary registered builds retain G1 behavior.

Migration 1387 is after the observed maximum 1386 on remote main and 189 remote
campaign branches, is listed in the protected Kāla window, and is tested by
applying twice to the guarded isolated database. It is not deployed here.

Activation gates: D-VC approval, D-G2 approval, accepted full G1b prerequisites,
admitted real class parameter/eligibility/source bindings, independent model/
null/numerical qualification, protected migration window, calibrated evidence
for odds, and K9-4b publication/rollback qualification. No gate outcome, live
mapping or operation receipt is manufactured by this brief.

(I) INTERPRETATION: K5-G1b's measurement/snapshot integration is an upstream
contract not merged at the base head 9f7be28a0. This code uses the typed F1 and
manifest contracts already on that head and accepts the full upstream partition;
it leaves unearned G2 nulls null. Alternative: guess an unmerged measurement API
or dispatch G2 through the legacy writer. Neither is selected. Existing legacy
replacement holds are upstream G1 work, not removed by this isolated pre-build.

Pure tests: tests/l3/ka_kshetra/test_g2_{model,features,ci}.py. DB tests:
tests/l3/kala_db/ka_kshetra/test_g2_candidate.py. Both run in the existing required
Kāla DB Tests job, where skips fail; every previous CI selection is retained.
Fail-on-revert evidence lives in the job result.
