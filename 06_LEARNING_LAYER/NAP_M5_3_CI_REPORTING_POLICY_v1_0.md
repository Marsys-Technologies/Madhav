---
artifact: NAP_M5_3_CI_REPORTING_POLICY_v1_0.md
canonical_id: CI_REPORTING_POLICY
version: "1.0"
status: APPROVED
layer: L6
authored_session: M5-D-S3
authored_date: 2026-05-13
nap_id: NAP.M5.3
nap_gate: AC.M5D.4 (prospective prediction log format)
prior_spec_ref: PRIOR_SPEC_v1_0.md v1.1
dbn_params_ref: 06_LEARNING_LAYER/dbn/dbn_params_v1_0.json
---

# NAP.M5.3 — Confidence Interval Reporting Policy for DBN Predictions

## §1 — Scope and Purpose

This policy governs how posterior credible intervals (CIs) are displayed whenever a DBN prediction
is emitted — whether in retroactive PPL entries, in prospective predictions, or in any M5+ session
response that quotes a domain-activation or event-occurrence probability. It closes the gap in
PRIOR_SPEC_v1_0.md §9 (no CI display rule) and gates AC.M5D.4 (prospective prediction log format).

All rules in this policy are binding from M5-D-S3 forward unless superseded by a later NAP.

---

## §2 — Credible Interval Level

**Rule CI.1 — Default interval: 90% HDI (Highest Density Interval).**

- 90% HDI is used for all operational predictions. It balances communicative clarity (narrower
  than 95%) with adequate coverage for calibration feedback. 95% HDI is available in
  technical-tier output on explicit request.
- HDI is computed from the Beta posterior via the `scipy.stats.beta.ppf` method at
  (0.05, 0.95) for the 90% interval; (0.025, 0.975) for the 95% interval.
- HDI is preferred over equal-tailed intervals because Beta posteriors near the boundaries
  (e.g., SUPPRESSED with prior Beta(0.5, 9.5) post_mean=0.05) are asymmetric; equal-tailed
  intervals would show negative lower bounds.

---

## §3 — Asymmetric Display Format

**Rule CI.2 — Display format: [lower, point_estimate, upper] — never ±.**

Predictions are displayed as:

```
P(event | ELEVATED, CAREER) = 0.857  [90% HDI: 0.695 – 0.954]
```

NOT:

```
P = 0.857 ± 0.13   ← FORBIDDEN
```

Rationale: Beta posteriors are inherently asymmetric, especially at ELEVATED (skewed left)
and NORMAL/SUPPRESSED (skewed right). The ± notation implies a symmetric Gaussian interval
and is epistemically wrong for this model.

**Rule CI.3 — Point estimate = posterior mean.**

The posterior mean (post_mean) is the point estimate in all output. Posterior mode is
available as an alternative label (e.g., for SUPPRESSED where the mode = 0) but never
substitutes the mean as the headline figure.

---

## §4 — Small-n Caveat

**Rule CI.4 — n=1 caveat trigger conditions:**

A ⚠ caveat is appended whenever any of the following hold for the quoted probability:

| Condition | Trigger |
|---|---|
| Domain-state n_obs = 1 | SPIRITUAL ELEVATED (n=1), PSYCHOLOGICAL ELEVATED (n=1) |
| posterior concentration < 12 | post_alpha + post_beta < 12 |
| SUPPRESSED state (no training data) | any SUPPRESSED probability |

**Rule CI.5 — Caveat text (standardized):**

When triggered, the caveat reads:

> ⚠ *Low-n estimate: this posterior is anchored primarily to the prior (n_successes=1 or 0).
> The credible interval is wide and the point estimate should be treated as a prior-informed
> guess, not a fitted parameter. Calibration at M5-E with additional observations is required.*

For SUPPRESSED state specifically:

> ⚠ *SUPPRESSED state: no training periods in this state; posterior = prior Beta(0.5, 9.5).
> P(event) = 0.05 is the prior anchor, not a data-fitted value.*

---

## §5 — Disclosure Tier Rules

DBN probability output is tiered per the Ethical Framework (MACRO_PLAN §Ethical Framework).

| Tier | Audience | CI Display | Beta params | Caveat |
|---|---|---|---|---|
| **T1 — Summary** | Native (conversational) | Point estimate + 90% HDI | No | If triggered |
| **T2 — Research** | Cross-native research | Point estimate + 90% HDI + 95% HDI | Yes (post_alpha, post_beta) | Always shown |
| **T3 — Technical** | Governance / audit | Full posterior dump | Yes | Always shown |

**Default tier for M5 sessions: T1 (Summary).** Use T2/T3 only when explicitly requested
or when producing artifacts for audit trail (session_close, held_out_validation, PPL).

---

## §6 — Application to Held-Out Validation Scores

Held-out validation (AC.M5D.3) produces point estimates P(event|MD,domain) as marginal
predictions integrated over domain state. CI display for these scores follows a different
rule: the model uncertainty is already marginalized, so no Beta-posterior CI is directly
applicable. Instead, report:

```
P(event | Mercury, CAREER) = 0.537  [marginal; CI on component posteriors available on request]
```

---

## §7 — Application to Prospective Prediction Log (PPL)

Every PPL entry produced at M5-D or later must include, in its `prediction_metadata` block:

```json
{
  "p_point": 0.857,
  "ci_level": 0.90,
  "ci_lower": 0.695,
  "ci_upper": 0.954,
  "post_alpha": 18.0,
  "post_beta": 3.0,
  "small_n_caveat": false,
  "disclosure_tier": "T1"
}
```

PPL entries from before NAP.M5.3 (M5-B, M5-C) are grandfathered and need not be
back-populated unless a calibration session revisits them.

---

## §8 — Implementation Reference

Computing 90% HDI from Beta(alpha, beta):

```python
from scipy.stats import beta as beta_dist
lo, hi = beta_dist.ppf([0.05, 0.95], a=post_alpha, b=post_beta)
```

Example outputs for fitted posteriors:

| Domain-State | post_alpha | post_beta | post_mean | 90% HDI |
|---|---|---|---|---|
| CAREER ELEVATED | 18.0 | 3.0 | 0.857 | [0.709 – 0.958] |
| CAREER NORMAL | 2.0 | 20.0 | 0.091 | [0.022 – 0.200] |
| HEALTH ELEVATED | 11.0 | 3.0 | 0.786 | [0.598 – 0.929] |
| RELATIONSHIP ELEVATED | 13.0 | 3.0 | 0.813 | [0.637 – 0.943] |
| SPIRITUAL ELEVATED ⚠ | 8.0 | 3.0 | 0.727 | [0.486 – 0.913] |
| PSYCHOLOGICAL ELEVATED ⚠ | 8.0 | 3.0 | 0.727 | [0.486 – 0.913] |
| Any SUPPRESSED ⚠ | 0.5 | 9.5 | 0.050 | [0.001 – 0.149] |

⚠ = small-n caveat triggered.

---

## §9 — Changelog

| Version | Date | Session | Change |
|---|---|---|---|
| 1.0 | 2026-05-13 | M5-D-S3 | Initial — NAP.M5.3 PENDING |

---

*NAP.M5.3 APPROVED (M5-D-S3, 2026-05-13). Gates AC.M5D.4.*
