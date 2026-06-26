---
artifact: WAVE4_L3_KALA_EXECUTION_v1_0.md
canonical_id: WAVE4_L3_KALA_EXECUTION
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
parent: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0.md
purpose: >
  Confirm the F-W2-001 D9 dismissal with a DATA check (not just the math comment), then run Wave 4:
  the L3 Kāla audit of all 9 ka_ assets. L3 is the HIGHEST contamination-risk wave so far — ka_ writers
  do temporal computation from birth-TIME inputs, the exact class where L1's two grep-invisible escapes
  lived. Axis A here is a human-grade per-writer birth-param read, never grep-trust.
audience: Claude Code (Antigravity)
---

# Wave 4 — L3 Kāla (+ D9 data-confirm)

## §0 — State + the L3 risk
Branch `audit/pre-regen-wave0` (kept; main untouched). L0/L1/L2 audited — all contamination-clean after
fixes. L3 Kāla is temporal: dashas, transits (gochara), muhurta, life-periods — these consume birth
DATE/TIME directly, so A1 contamination is HIGH-RISK. L1 taught us the escapes are grep-INVISIBLE
(local alias `BIRTH_IST`; unconditional `{**NATIVE_BIRTH}`). So for EVERY ka_ writer, trace the actual
birth-param flow by hand; the green guard proves nothing here.

## §1 — D9 DATA-CONFIRM (fast carry-over — close the F-W2-001 dismissal)
F-W2-001 (ga_vargas D9) was dismissed as a false positive: `(sign_idx×9 + pada) % 12` claimed
equivalent to the trikona-start navamsha rule, with a math-proof comment. A math assertion is not a
ground-truth check, and a wrongly-dismissed blocker is the most expensive error in this campaign.
DO (read-only, ~10 min): for the NATIVE chart, pick 3 grahas whose D1 sign spans the three modalities —
one in a MOVABLE/chara sign, one in a FIXED/sthira, one in a DUAL/dvisvabhava. For each, compute the D9
navamsha sign TWO ways: (a) the code's `(sign_idx×9 + pada) % 12`, (b) the classical trikona-start
lookup (movable → starts same sign; fixed → starts 9th; dual → starts 5th — cite BPHS). Show the
resulting navamsha sign matches for all three modalities.
- ALL match → dismissal CONFIRMED; record the data check in the findings register; D9 closed.
- ANY mismatch → F-W2-001 is a REAL blocker after all; reopen, fix the routing, and re-flag every L2
  varga-consuming asset (it read wrong navamsha). HALT and report.

## §2 — WAVE 4: L3 Kāla audit (9 ka_ assets)
Assets (verify DAG order vs asset_registry.depends_on at run; audit upstream-first):
ka_kala_darshana, ka_kalasutra, ka_graha_sancara (transits), ka_sangam, ka_yojaka, ka_jivana_parva
(life-periods), ka_bhavishya_lekha (predictions), ka_vighnakara, ka_muhurta_seva (electional).

### Axis A — CODE (HUMAN-GRADE birth-param read — the high-risk axis this wave)
For EACH ka_ writer, explicitly trace: where does it get birth date/time/lat/lon/tz? Does any path
fall back to a native constant (NATIVE_BIRTH, BIRTH_IST/LAT/LON, a hardcoded 1984-02-05, a
`{**NATIVE_BIRTH}` spread, or a default `chart_id=CANONICAL_CHART_ID`) when building a NON-native chart?
- A1 classify CHART-INDEPENDENT / NATIVE-ONLY / CORRECTLY-GUARDED / VULNERABLE. Any writer that can
  compute a non-native chart's temporal data from native birth = VULNERABLE = blocker fix
  (resolve_birth_params guard). EXPECT to find some (this is the ga_dashas/ga_tajaka risk class).
- Specifically scrutinize: ka_graha_sancara (transit base = birth positions?), ka_muhurta_seva
  (electional from birth?), ka_bhavishya_lekha + ka_jivana_parva (dasha/period timelines from birth),
  ka_kala_darshana, ka_kalasutra. Note: ka_muhurta_seva.py is a service writer — confirm asset_kind.
- If a new evasion SHAPE appears, widen the grep guard (as in Wave 2) and record it.
- A2 idempotency (delete-then-insert, no accretion); A3 FROZEN contract (no direct commit/rollback/
  close, no _telemetry); A6 determinism; A7 errors halt/record not silent.
- A4 no value-restating (reference upstream L1/L2 fact_ids, don't restate computed values); A5
  derivation ledger / classical citation for any interpretive claim.

### Axis B — DATA: POST-REGEN ONLY. Note L3's B-priorities (B3 no degenerate distribution — the
all-Jupiter kala_convergence bug LIVED in L3; B6 referential integrity) as post-regen acceptance items.
Do NOT audit current ka_ data now.

### Axis C — ASTROLOGY / CLASSICAL (temporal rule fidelity)
- C1 rule fidelity — dasha sequence/period lengths, transit (gochara) rules incl. vedha (the bg
  Venus-gochara gap from W1 was a missing-house bug — check ka_graha_sancara consumes the COMPLETE
  transit rule set, now that bg_transit_rules was fixed), muhurta election rules. Hand-check a
  representative period/transit.
- C2 canonical-or-floor; C4 cross-system coherence; C5 spot re-derivation acharya-grade.
- DEGENERATE-DISTRIBUTION watch (C/B overlap): the historic all-Jupiter kala_convergence collapse was
  an L3 bug — for any attribution column that should vary (dasha lord, transit planet), confirm the
  CODE can't collapse it to one value (a hardcoded `dict.get(k, default)` style). This is a code check
  even pre-regen.

Per-asset VERDICT: PASS / FIX-REQUIRED + severity + evidence + fix.

## §3 — Deliverables + gate
DELIVER: the D9 data-confirm result (closed or reopened); the Wave 4 L3 findings register (9 assets ×
Axis A + C × pass/fail + evidence + severity) appended to PRE_REGEN_AUDIT_FINDINGS_REGISTER, fix-list
extract; any contamination fixes + grep-widening committed on the audit branch with the guard green.
STOP for native review before Wave 5 (L4 Phala).
GUARDRAILS: branch only — main untouched; never merge while a guard test is red; HUMAN-grade Axis A per
writer (grep-trust forbidden this wave); no fabricated values/citations/rules; acharya-grade Axis C;
native 482012f1 read-only, destructive checks only on 1c826d5a. Any VULNERABLE A1 finding is a blocker —
fix before the wave closes (don't carry birth-time contamination forward).

## §4 — Forward note
Wave 5 = L4 Phala (ph_): l4_anchors is native-hardcoded (confirmed) — but it's NATIVE-ONLY-BY-DESIGN, so
classify carefully (safe-but-tag, not VULNERABLE) and watch the OTHER ph_ writers (rectification,
muhurta, outlook, mitigation, nimitta, phaladesa, pratikara, sodhana, sankrama, pramana) for real
contamination + the LEL-citation discipline (C2-002 class). After L4: consolidate full register → FIX
PLAN (all blocker/major CODE fixes) → rebuild job image → main==prod re-proof → regenerate all layers
all charts → post-regen B7 isolation spot-check. The L2 minors (F-W3-001..005) + any L3/L4 minors fold
into the consolidated fix plan.
