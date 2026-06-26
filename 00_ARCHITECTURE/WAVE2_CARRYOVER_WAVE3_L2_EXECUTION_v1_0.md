---
artifact: WAVE2_CARRYOVER_WAVE3_L2_EXECUTION_v1_0.md
canonical_id: WAVE2_CARRYOVER_WAVE3_L2_EXECUTION
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
parent: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0.md
purpose: >
  Execute the Wave 2 carry-over fixes (gated — must land before L2 opens), then run Wave 3: the L2 Bodha
  audit of all 10 bo_ assets on Axis A (code/contamination — human-grade, not grep-only) + Axis C
  (astrology) + the L2-specific dimensions (no value-restating, derivation ledgers, referential
  integrity into L1). All on branch audit/pre-regen-wave0; main stays untouched.
audience: Claude Code (Antigravity)
---

# Wave 2 carry-overs → Wave 3 (L2 Bodha)

## §0 — State + non-negotiables
Branch `audit/pre-regen-wave0` (kept, not merged; main untouched). Waves 0/1/2 done: contamination
guard GREEN for the known shapes, but Wave 2 found two GREP-INVISIBLE contamination sites + one
blocker formula bug. The carry-overs (§1) MUST land before Wave 3 (§2), because L2 Bodha CONSUMES L1
outputs — auditing L2 on top of a known-wrong D9 navamsha or contaminated dasha would audit against
corrupt input.

DURABLE LESSON (apply throughout Wave 3): the grep guard is necessary but NOT sufficient. Wave 2's
contamination escapes were a local-alias constant (`BIRTH_IST` not `NATIVE_BIRTH`) and an unconditional
`{**NATIVE_BIRTH}` spread (no `or` pattern). So Axis A on EVERY remaining writer is a human-grade read
of the actual birth-param flow, not "the guard is green." Widen the grep as new evasion shapes appear,
but never trust green-guard alone.

## §1 — WAVE 2 CARRY-OVERS (gated — finish before any L2 work)
Fix, test, commit on the audit branch. Re-run the full sidecar suite + the contamination guard green
after each.

1.1 — **F-W2-001 (BLOCKER) ga_vargas D9 Navamsha wrong formula.** `ga_vargas_writer.py` uses
  `_compute_general_varga()` for D9 where the trikona-start rule (`_compute_divisional_sign()`) is
  required. Fix D9 to the correct navamsha derivation. VERIFY against a cited classical source (BPHS
  navamsha trikona-start rule) AND re-derive the native's D9 by hand for 1–2 grahas to confirm the
  placements are now correct. This gates L2 — L2 varga analysis reads these placements.

1.2 — **F-W2-002 ga_dashas local-alias contamination.** `ga_dashas_writer.py` does
  `birth or {}).get(...) or BIRTH_IST` — a native-birth fallback via a LOCAL ALIAS that evades the
  grep. Replace with the `resolve_birth_params(chart_id, birth_params)` 3-way guard (raise for
  non-native with no params). Confirm the adapter passes birth_params.

1.3 — **F-W2-003 ga_tajaka unconditional NATIVE_BIRTH.** `ga_tajaka_writer.py compute_varsha()` does an
  UNCONDITIONAL `{**NATIVE_BIRTH}` (not an or-fallback). Add a `birth_params` param threaded from the
  caller + `resolve_birth_params()`; inject `conn` if needed for the charts-row fetch. A non-native
  Varshaphala must use that chart's birth, never the native's.

1.4 — **WIDEN the structural grep guard** to catch the evasion shapes Wave 2 exposed: add patterns for
  local birth aliases (`BIRTH_IST`, `BIRTH_LAT`, `BIRTH_LON`, and any `= <alias> ` where the alias is a
  module-level native-birth constant) and the unconditional-spread form (`{**NATIVE_BIRTH}` /
  `{**<native_alias>}`). The guard should now FAIL on F-W2-002/003-style code, so after fixing them it
  goes (and stays) green. Document the added patterns in the test docstring.

1.5 — **F-W2-004 ga_vargas INVARIANT sentinel accretion + `_telemetry` import.** Remove the INVARIANT
  sentinel-row accretion (A2 idempotency — rebuild must replace, not accrete) and the `_telemetry`
  import from the source module (A3 — orchestrator is the sole throughput writer). (F-W2-005/006/007
  are minors — fix if cheap, else log them in the register as deferred-non-blocking.)

GATE: §1 complete (D9 re-derived correct, both contamination sites on resolve_birth_params, grep widened
+ green, INVARIANT removed) before §2. Update PRE_REGEN_AUDIT_FINDINGS_REGISTER + commit.

## §2 — WAVE 3: L2 Bodha audit (10 bo_ assets, Axis A + C + L2-specific)
The 10 assets (DAG order — audit each AFTER its upstreams so referential checks have a verified base):
**bo_laksana** (root) → bo_bimba, bo_karanajala, bo_sangati, bo_samvada, bo_samskara, bo_drishti,
bo_anveshana → bo_upaya → bo_pramana_mapa.
(Verify this DAG against asset_registry.depends_on at run time; note bo_upaya is the one L2 asset that
reads L0 per prior context — check its birth-param/L0 access too.)

Per asset, score and record:

### Axis A — CODE (human-grade, not grep-only)
- A1 contamination: trace the actual birth-param / chart_id flow. L2 mostly reads L1 facts (not raw
  birth), so most should be CHART-INDEPENDENT-of-birth — but CONFIRM each reads per-chart L1 rows by
  chart_id and never a native default. bo_upaya (reads L0) gets extra scrutiny. Classify
  CHART-INDEPENDENT / NATIVE-ONLY / CORRECTLY-GUARDED / VULNERABLE.
- A2 idempotency (per-chart delete-then-insert, no accretion); A3 FROZEN-contract conformance (no
  direct commit/rollback/close, no _telemetry, @register/run(ctx)); A6 determinism (embeddings ok,
  generative-LLM curation NOT); A7 errors halt/record, never silent garbage.
- **A4 (L2-critical) — no value-restating / L1-authority.** Does the bo_ asset RESTATE an L1 computed
  value as its own, or correctly REFERENCE the L1 fact_id and inherit its value? A restated value that
  can drift from its source is a bug (the MSR drift trap). Check constituent_facts_array /
  source-fact references RESOLVE to real L1 chart_facts rows.
- **A5 (L2-critical) — derivation ledger / citation.** Every interpretive/synthesis claim carries a
  DERIVATION_LEDGER entry naming the specific L1 fact_ids (and any L0 classical source) it consumes —
  no "as is known classically" without a source.

### Axis B — DATA: POST-REGEN ONLY (do NOT run pre-regen — stale data is being discarded). Note the
B-priorities for L2 (referential integrity B6, no-degenerate-distribution B3) as POST-REGEN acceptance
items in the register; do not audit current bo_ data now.

### Axis C — ASTROLOGY / CLASSICAL
- C1 rule fidelity — the synthesis logic matches the classical method it claims (e.g. drishti/aspect
  rules in bo_drishti, sangati convergence logic). Hand-check a representative case.
- C2 canonical-or-floor; C4 cross-system coherence (multi-school/ayanāṁśa divergences are real
  doctrine, not artifacts — the AK-divergence lesson); C5 spot re-derivation, acharya-grade.
- SPECIAL: bo_ varga-consuming assets must be re-checked AFTER the §1.1 D9 fix (they were reading the
  wrong navamsha) — confirm they now consume the corrected placements.

Per-asset VERDICT: PASS / FIX-REQUIRED + severity (blocker/major/minor) + evidence + fix summary.

## §3 — Deliverables + gate
DELIVER: §1 carry-over fixes (diffs, tests, D9 hand-re-derivation, widened-guard green, commit SHAs);
then the Wave 3 L2 findings register (10 assets × Axis A + C + A4/A5 × pass/fail + evidence + severity)
appended to PRE_REGEN_AUDIT_FINDINGS_REGISTER, with the L2 fix-list extract. Commit on the audit branch.
STOP for native review before Wave 4 (L3 Kāla).
GUARDRAILS: branch audit/pre-regen-wave0 only — main untouched; never merge the branch while any guard
test is red; read-only audit before fixes within Wave 3 (audit all 10 → then fix, or fix-as-you-go but
keep the register authoritative); no fabricated values/citations/rules; acharya-grade Axis C; the
contamination read is HUMAN-grade per writer, not grep-trust. Native 482012f1 read-only; destructive
checks (none expected in an audit) only on 1c826d5a.

## §4 — Forward note
After L2: Wave 4 = L3 Kāla (ka_ — temporal; these take birth-TIME inputs so A1 is high-risk, like the
ga_dashas/ga_tajaka escapes — expect grep-invisible contamination, read each by hand). Wave 5 = L4
Phala (ph_ — l4_anchors native-hardcoded confirmed; LEL-citation discipline). Then consolidate the full
register → FIX PLAN → land all blocker/major CODE fixes → rebuild job image → main==prod re-proof →
regenerate all layers all charts → post-regen B7 isolation spot-check.
