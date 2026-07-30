"""
`mi_bhara` (Kāla Bhāra — "the weight of time") — STAGE 9 of the ṢAḌ-DARŚANA W2 temporal-field
pipeline. L5 Mīmāṃsā-seated.

Spec: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/KALA_W2_FIELD_DESIGN_v1_0.md`
§7.2 (the fitting harness), §7.3 (skill score + time-rescaling GOF), §7.5 (weights versioning
and the acyclicity mechanism), §7.6 (the Living-LEL plane). Execution contract:
`SHAD_DARSHANA_BRIEF_v2_0.md` §3 W2, §2.5.

── WHAT STAGE 9 IS ────────────────────────────────────────────────────────────────────────
Stages 0–8 (`ka_kshetra`, L3) are pure functions of `(chart, corpus_pin, config_pin,
weights_version)`. Stage 9 is **the only state that grows**, and **the only stage that may see
the LEL** (design §2). It does four things:

  1. FITS the hazard field's parameters θ = (w_s, β_j, ρ_m) against this chart's recorded life
     events, by maximising the inhomogeneous-Poisson log-likelihood
     `ℓ_e(θ) = Σ_k ln λ_e(t_k; θ) − Λ_e(0,T; θ)` — with the integral computed by the SAME
     `field.integrate` the serving path uses. That sharing is load-bearing: a fitter with its
     own integral would publish a skill score for a model the product does not serve.
  2. SHRINKS the fit toward the classical structural priors, conservatively, so a thin LEL
     cannot move a weight far and an ABSENT LEL reproduces the priors EXACTLY (`n_eff = 0 ⇒
     φ̂ = φ⁰`, which is the LEL-absent scenario falling out of the formula rather than being
     special-cased).
  3. PUBLISHES a temporal skill score and a time-rescaling goodness-of-fit — both real,
     computable, and FALSIFIABLE, in the three honest states the design specifies.
  4. WRITES a new weights VERSION row. It never mutates an existing one: weights are versioned
     artifacts and silent mutation is a drift failure (brief §7 rail).

── THE CIRCULARITY GUARD (peer of LAW ZERO) ───────────────────────────────────────────────
The field never reads the LEL. This package is the ONE sanctioned exception, and even here the
LEL read is confined to a single module — `db.py` — so the static half of the guard can express
its whitelist as "exactly one file, by name" rather than as a judgement call. Every other module
in this package is a pure function of its arguments and touches no database at all.

Concretely: for any mutation of a chart's LEL that leaves `(corpus_pin, config_pin,
weights_version, cohort_version)` unchanged, the stage 0–8 field hash is bit-identical before
and after — while stage 9's output (this package's) MUST move. Both halves are asserted; see
`tests/l5/test_mi_bhara_circularity_guard_w2.py`.

── LAYOUT ─────────────────────────────────────────────────────────────────────────────────
    field.py       the stored segment representation + the exact analytic integrator (§5.2)
    basis.py       the θ-independent per-segment basis, and ln λ(t; θ) built from it (§5.1)
    likelihood.py  the inhomogeneous-Poisson log-likelihood (§7.2)
    fit.py         L-BFGS-B fit · blocked forward-chaining CV · shrinkage · trust region (§7.2)
    skill.py       the temporal skill score, its bootstrap interval, its three states (§7.3)
    gof.py         time rescaling · Kolmogorov–Smirnov · Ljung–Box · three states (§7.3)
    weights.py     weights versioning and the RESOLVE-ONCE acyclicity mechanism (§7.5)
    living_lel.py  the Living-LEL plane: maturity, receipt, prospective/backfill split (§7.6)
    db.py          the ONLY module in this package that touches a database
"""
