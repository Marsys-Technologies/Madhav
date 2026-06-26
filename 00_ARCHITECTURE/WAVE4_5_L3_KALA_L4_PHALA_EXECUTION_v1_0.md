---
artifact: WAVE4_5_L3_KALA_L4_PHALA_EXECUTION_v1_0.md
canonical_id: WAVE4_5_L3_L4_EXECUTION
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
parent: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0.md
purpose: >
  Final two audit waves in one session: D9 data-confirm, then Wave 4 (L3 Kāla, 9 ka_) and Wave 5
  (L4 Phala, 9 ph_). L3 + L4 both take birth-TIME inputs → HIGHEST contamination-risk waves; Axis A is
  human-grade per writer, never grep-trust. INTERNAL GATE: L3 must fully close (all VULNERABLE A1 sites
  fixed + guard green) BEFORE L4 begins, so any new grep-evasion shape L3 surfaces is caught before L4
  is audited against it. One consolidated findings handoff at the end (native reviews L3+L4 together).
audience: Claude Code (Antigravity)
---

# Waves 4 + 5 — L3 Kāla + L4 Phala (one session, internal gate)

## §0 — State + why these two are the risk peak
Branch `audit/pre-regen-wave0` (kept; main untouched). L0/L1/L2 audited, all contamination-clean after
fixes. L3 (temporal: dashas/transits/muhurta) and L4 (applied/prediction) both consume birth DATE/TIME
directly — the exact class where L1's two GREP-INVISIBLE escapes lived (local alias `BIRTH_IST`;
unconditional `{**NATIVE_BIRTH}`). For EVERY ka_ and ph_ writer, trace the actual birth-param flow BY
HAND. The green guard proves nothing here.

## §1 — D9 DATA-CONFIRM (fast — close the F-W2-001 dismissal first)
F-W2-001 (ga_vargas D9) was dismissed as a false positive (`(sign_idx×9 + pada) % 12` claimed ≡
trikona-start rule, math-proof comment only). Confirm with DATA, not a comment: for the NATIVE chart,
pick 3 grahas whose D1 sign spans the modalities — one MOVABLE/chara, one FIXED/sthira, one
DUAL/dvisvabhava. For each compute the D9 navamsha sign TWO ways — (a) code `(sign_idx×9 + pada) % 12`,
(b) classical trikona-start (movable→starts same sign, fixed→starts 9th, dual→starts 5th; cite BPHS) —
and show they match.
- ALL match → dismissal CONFIRMED, record in register, D9 closed.
- ANY mismatch → F-W2-001 is a REAL blocker: reopen, fix routing, re-flag every L2 varga-consumer, HALT
  and report before any further wave.

## §2 — WAVE 4: L3 Kāla (9 ka_ assets)
Assets (verify DAG order vs asset_registry.depends_on; upstream-first):
ka_kala_darshana, ka_kalasutra, ka_graha_sancara (transits), ka_sangam, ka_yojaka, ka_jivana_parva
(life-periods), ka_bhavishya_lekha (predictions), ka_vighnakara, ka_muhurta_seva (electional; service —
confirm asset_kind).

### Axis A — CODE (HUMAN-GRADE birth-param read — the high-risk axis)
For EACH ka_ writer trace: where does birth date/time/lat/lon/tz come from? Does ANY path fall back to
a native value (NATIVE_BIRTH, BIRTH_IST/LAT/LON, hardcoded 1984-02-05, `{**NATIVE_BIRTH}` spread,
default `chart_id=CANONICAL_CHART_ID`) when building a NON-native chart?
- A1 classify CHART-INDEPENDENT / NATIVE-ONLY / CORRECTLY-GUARDED / VULNERABLE. VULNERABLE (non-native
  temporal data from native birth) = BLOCKER → fix with resolve_birth_params guard. EXPECT to find some
  (ga_dashas/ga_tajaka risk class). Scrutinize ka_graha_sancara, ka_muhurta_seva, ka_bhavishya_lekha,
  ka_jivana_parva, ka_kala_darshana, ka_kalasutra hardest.
- If a NEW evasion shape appears → widen the grep guard + record it (this is why the L3→L4 gate exists).
- A2 idempotency (no accretion); A3 FROZEN contract (no direct commit/rollback/close, no _telemetry);
  A6 determinism; A7 errors halt/record; A4 no value-restating; A5 derivation ledger/citation.

### Axis C — temporal rule fidelity
C1: dasha sequence/period lengths; gochara transit rules incl. vedha (confirm ka_graha_sancara now
consumes the COMPLETE transit rule set after W1 fixed the bg Venus-gochara missing-houses gap); muhurta
election rules. C2 canonical-or-floor; C4 cross-system coherence; C5 acharya-grade spot re-derivation.
DEGENERATE-DISTRIBUTION watch (code check, valid pre-regen): the historic all-Jupiter kala_convergence
collapse was an L3 bug — for any attribution column that should vary (dasha lord, transit planet),
confirm the code can't pin it to one value (a `dict.get(k, default)` constant). 

### Axis B — POST-REGEN ONLY. Note L3 B-priorities (B3 degenerate-distribution, B6 referential) as
post-regen acceptance items; do not audit current ka_ data now.

## §3 — INTERNAL GATE (L3 → L4)
Before starting L4: every L3 VULNERABLE A1 site is FIXED, any new evasion shape is in the widened grep,
the contamination guard is GREEN, and the L3 findings are written to the register + committed on the
branch. Only then proceed to §4. (This is the one hard stop inside the session — it ensures L4 is
audited against an up-to-date guard.)

## §4 — WAVE 5: L4 Phala (9 ph_ assets + l4_anchors status)
Assets: ph_phaladesa, ph_pratikara, ph_nimitta, ph_suddha_sodhana, ph_sankrama, ph_rectification,
ph_sodhana, ph_pramana, ph_muhurta. (verify DAG order; upstream-first.)
ALSO confirm `brahmagyan/phala/l4_anchors.py` status: it is NATIVE-HARDCODED (native chart state baked
in) and is a ROUTER module, NOT a @register orchestrated asset. Classify it NATIVE-ONLY-BY-DESIGN
(safe-from-leakage — it can't run for a non-native chart) and TAG as a de-native candidate; do NOT
treat it as VULNERABLE. Confirm it has no path that a non-native chart_id could reach.

### Axis A — CODE (human-grade, same rigor as L3)
- A1 per ph_ writer: birth-param flow by hand; the ph_ writers (rectification, muhurta, phaladesa,
  nimitta, sankrama, sodhana, suddha_sodhana, pramana, pratikara) take birth-time + dasha inputs —
  same contamination class. Classify; VULNERABLE = blocker → resolve_birth_params. ph_rectification +
  ph_muhurta are prime suspects (electional/time-based). Widen grep if a new shape appears.
- A2/A3/A6/A7 as before; A4 no value-restating (ph_ reads L1/L2/L3 — references not restatements);
  A5 derivation ledger.
- A5 SPECIAL — LEL-citation discipline (the C2-002 class): any ph_ asset that surfaces life-event /
  LEL-derived content in a PUBLIC field must not leak raw LEL citations (the l4_anchors leak we fixed).
  Check ph_pramana / ph_phaladesa / anything reading LEL for the same exposure pattern.

### Axis C — applied/prediction fidelity
C1 phala (result) rules trace to a classical source; C2 canonical-or-floor; C5 acharya-grade spot
re-derivation. The prediction/falsifiability framing (ph_pramana) — confirm it's scaffolding-only per
the L4 design (scoring lives in L5), not fabricated outcome claims.

### Axis B — POST-REGEN ONLY (note priorities; don't audit current ph_ data).

## §5 — Deliverables + consolidated handoff
DELIVER (one consolidated report for native review of L3+L4 together):
1. D9 data-confirm result (closed / reopened).
2. Wave 4 L3 register (9 ka_ × Axis A + C × verdict + evidence + severity) + fixes committed.
3. Wave 5 L4 register (9 ph_ + l4_anchors classification × Axis A + C × verdict) + fixes committed.
4. The widened grep guard (any new shapes from L3/L4) — GREEN.
5. A CAMPAIGN-COMPLETE rollup: the full L0–L4 findings register consolidated, every blocker/major CODE
   finding across all waves listed as the input to the FIX PLAN (next step after this session).
STOP for native review. After native sign-off, the next artifact is the consolidated FIX PLAN →
land all blocker/major code fixes → rebuild job image → main==prod re-proof → regenerate all layers/
charts → post-regen B7 isolation spot-check.

## §6 — Guardrails
Branch only — main untouched; never merge while a guard test is red. HUMAN-grade Axis A per writer
(grep-trust forbidden across BOTH waves). L3→L4 internal gate is a hard stop. Any VULNERABLE A1 = blocker,
fixed before its wave closes — never carry birth-time contamination forward. No fabricated values/
citations/rules; acharya-grade Axis C. Native 482012f1 read-only; destructive checks only on 1c826d5a.
l4_anchors = NATIVE-ONLY-BY-DESIGN (tag, don't "fix" as contamination).
