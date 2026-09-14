---
artifact: MADHAV_DATA_PLANE_L3_DHARA_NUMERICAL_CONTRACT
version: "1.0"
status: CURRENT
authority: DP-SD-017
strategy_content_commit: 793972c754b106688097dbc54536c1a9c270a793
approval_pin_commit: 04a9ab33effa23e5e9b4e89772330ae264498a9b
packet: L3-W0-FOUNDATION-SAFETY-01
scope: ka_kshetra DHARA stored-field endpoint semantics and numerical reference
supersedes: "DHARA_DESIGN_v1_0.md v1.1 F-12 right-limit rule only"
does_not_supersede: "Any other DHARA design rule, layer authority, build gate or release state"
---

# L3 DHARA numerical correction contract

## 1. Disposition

DP-SD-017 explicitly requires W0 to resolve DHARA's knot/discontinuity reference
question with an independent small mathematical fixture and to distinguish a
numerical optimization from an intentional semantic repair. This record makes
that disposition explicit without editing the older, out-of-manifest Sampūrti
design artifact.

The old `DHARA_DESIGN_v1_0.md` v1.1 F-12 rule used the new period's value
`lambda(t_{i+1}+)` as the right endpoint of the preceding segment. That linearly
smears a discontinuous clock change across the whole prior interval. It conflicts
with the governing stored-field definition already carried by
`KALA_W2_FIELD_DESIGN_v1_0.md` and declared by `integrator.py`:

```
alpha_i = ln lambda(t_i+)
gamma_i = [ln lambda(t_{i+1}-) - ln lambda(t_i+)] / (t_{i+1} - t_i)
```

For this L3 campaign, DP-SD-017 therefore supersedes F-12's right-limit rule
only. This is a semantic correction, not a claim that the old and new fields are
numerically equivalent.

## 2. Endpoint and horizon contract

At an internal clock knot `k`:

1. The segment ending at `k` uses the old clock stack's left limit `lambda(k-)`.
2. The segment starting at `k` uses the half-open clock contract's exact,
   right-continuous value `lambda(k+) = lambda(k)`.
3. `math.nextafter(k, t_i)` is the minimal representable probe toward the
   preceding knot. It selects the old half-open clock period without introducing
   a macroscopic epsilon or changing interval width.
4. Non-clock endpoints require one exact evaluation and reuse it as the next
   segment's left endpoint.

At the terminal horizon `H`, there is no following interval. The final stored
segment therefore ends at `lambda(H-)`; DHARA does not perform an unused exact
`lambda(H)` evaluation. `lambda_at(segments, H)` returns the final segment's
retained left limit, while values strictly beyond `H` remain zero.

For `N` stored knots and `C_internal` internal clock knots, endpoint construction
performs exactly `N + C_internal` `terms_at` evaluations. Suppression-active
midpoint checks are separate `ln_lambda` evaluations and occur only under the
existing suppression/refinement rule.

## 3. Content-bound identity

The machine-readable semantic identity is
`DHARA_SWEEP_SEMANTIC_VERSION = "1.2"`.

- Analytic field `config_pin` includes `segment_engine` and
  `dhara_sweep_semantic_version`; changing `1.1` to `1.2` must change
  `field_snapshot_id`.
- The Kshetra resume fingerprint includes the same semantic version.
- `_RESUME_VERSION = 9` invalidates v8 checkpoints so no pre-correction stage-4
  work can resume into the corrected field.
- Sampled-mode identity records the segment engine and a null DHARA semantic
  version; this contract does not redefine sampled-engine endpoint behavior.

## 4. Independent numerical reference

The W0 fixture contains no chart or person data. Decimal arithmetic at 60-digit
precision supplies the expected log-linear integral and a 4,096-subinterval
composite-Simpson reference. Its suppression hazard has closed forms
`integral = 11/40`, `q=1/4 crossing = 5/9`, and window expected count `5/24`.
The oracle does not call production integration, window or sweep helpers to
construct expected values.

The accepted tolerances are explicit: `5e-13` relative for the exact stored
log-linear count; `0.003` day for the true-field suppression crossing; `0.3%`
for its full-horizon integral; and `0.5%` for its window expected count. These
test the deliberate piecewise log-linear approximation within the existing
`0.02`-nat midpoint policy; they do not call it exact relative to the curved
true field.

## 5. Evidence and non-claims

Implementation inputs are the independent oracle at `9210b8489`, the clock-step
regression at `542a934bb`, and the left-limit production correction at
`aea1671e4`. The bounded correction adds version/pin/resume and terminal-call
detectors on top of that lineage. Final test counts and the correction commit are
recorded by the parent W0 acceptance packet after independent review.

This record authorizes no production database access, migration, build, rebuild,
deployment, consumer-value claim or empirical predictive-performance claim.
