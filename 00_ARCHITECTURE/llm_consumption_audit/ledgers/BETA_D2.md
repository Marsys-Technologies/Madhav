---
artifact: BETA_D2 (Elevation Campaign v2.1 — Stream β, Lane D2: Gaṇita completions)
version: 1.0
status: LANE COMPLETE (code delivered + tested; authoritative live rebuild deferred to integration)
lane: β.D2 — sahams (EL-19) + per-dosha bhaṅga beyond NBRY (EL-18)
branch: elev/beta-D2-saham-bhanga  (flattened from charter's elev/beta/D2-saham-bhanga — D/F ref conflict; proxy-logged)
base: elev/beta @ 43116c42
charts: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek) · 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan)
baseline_ref: ~/elev-v2-shared/ledgers/ELEVATION_V2_BASELINE.md (git tag elev-v2-run-start, db_snapshot 1784938159545)
authored: 2026-07-25 (autonomous overnight; Native-Proxy per charter §10)
---

# β.D2 Run Ledger — sahams + bhaṅga

## Headline

Both register items were **already implemented in the elev/beta codebase**; the live DB
(built 2026-07-14/15) is stale relative to that code. This lane's true work was: (1) prove it,
(2) close the ONE genuine unreachable-code bug behind EL-18 (Manglik), (3) guard both with
committed tests, (4) hand the authoritative live rebuild to integration (a sibling lane was
concurrently rebuilding the same writer). **No classical rule or citation was fabricated
(B.3/B.10). No saham compute was re-derived (reused the grounded L1 writer).**

---

## EL-19 — Sahams (Arabic-parts-style points)

**G0 reproduce-or-reclassify.** Register premise ("REACHABLE-BUT-EMPTY, never computed") is
**FALSE**, disproven against the live DB.

- **Root reality:** sahams ARE computed by `ga_writers/ga_sensitive_writer.py::_build_saham_rows`
  (`_SAHAM_FORMULAS`, lines 143-214: 70+ Tājaka sahams incl. Puṇya, **Dhana**, Vidyā, Yaśas
  (Mahatmya), Mitra, Bhrātṛ (Bandhu), Gaurava, Pitṛ, Mātṛ, Putra, Āyus (Jeeva), Karma, Roga
  (Aroga), Kali, …), **day/night formula variants** selected by `is_day_birth`, all 5 canonical
  ayanamshas, written to fact_category **`saham_position`** — 2800 rows/chart on BOTH canonical
  charts (built 2026-07-14/15), `verification_pass_status='two_pass_verified'`, cited
  `"Tajik Neelakanthi Ch.2"` (Tājaka Nīlakaṇṭhī). Served today via retrieval
  `address_resolver.ts` `saham('CODE')` addressing (queries `saham_position`).
- **Day/night for Abhisek:** `day_birth=1` — correct (Sun in 10th house, born 10:43 IST = day birth).
- **Recompute proof (charter verify bar "recompute exactly from L1 inputs"):** independently
  recomputed from L1 graha longitudes, exact to <1e-6°, BOTH charts:
  - Puṇya (day) = Moon − Sun + Lagna. Abhisek: 327.055230 − 291.962617 + 12.431150 = **47.523762°**
    == stored `47.5237624469805`. ✓
  - Dhana (day) = Jupiter − Sun + Lagna. Abhisek: 249.787497 − 291.962617 + 12.431150 (mod 360) =
    **330.256029°** == stored `330.256029337033`. ✓
  - Both recompute exactly on Abhinandan too (regression test, live DB).
- **Why the census/tool see it as empty:** the census probe and `ganita_special_lagnas_get` query
  the **bare category name `saham`** (0 rows); the data lives under **`saham_position`**. This is a
  serving-layer alias gap, NOT a compute gap.

**Ruling (Native-Proxy §10):** do NOT re-derive or duplicate the sahams (B.10 + charter's explicit
"reuse not re-derive"; native EL-32 doctrine: aliases belong on INPUT at the serving layer, canonical
on OUTPUT — duplicating storage would be the opposite of intent). The `saham`-name reachability fix
lands in `platform-mcp/src/tools/register_p1_aliases.ts` + `platform/src/lib/retrieval/**` — both
**outside β.D2 ownership**.

**Deliverable:** committed recompute-proof regression test
`platform/python-sidecar/tests/test_el19_saham_recompute.py` — 5 tests, GREEN against live DB
(Puṇya + Dhana recompute exactly on both charts; Tājaka Nīlakaṇṭhī citation + two_pass_verified
asserted).

**Handoff to α (EL-41 receipt flip):** the `ganita_special_lagnas_get` special-lagnas handler and
census should either (a) treat requested category `saham` as an INPUT ALIAS for `saham_position`,
or (b) emit the per-category receipt for `saham` sourced from `saham_position`. Data is confirmed
present + correct + grounded on both charts; the receipt flip `empty_with_reason → served` needs
only that one serving-side alias.

### Evidence block — EL-19
```
el_id: EL-19
status: VERIFIED-CLOSED (compute present, grounded, two-chart recompute-exact) +
        PARKED-HONEST (bare-`saham`-name serving reachability — α-owned; handoff filed)
before_payload_ref: baseline Probe 7 (ganita_special_lagnas_get saham silently absent) +
        live: chart_facts saham=0 rows, saham_position=2800 rows/chart
after_payload_ref: test_el19_saham_recompute.py GREEN (5 passed, live DB) — Punya/Dhana exact both charts
probes_run: SQL category counts; hand + automated recompute (Punya, Dhana); provenance/verif-tier check
charts: 482012f1 (2800 saham_position rows), 1c826d5a (2800 saham_position rows)
deploy_revision: n/a (no prod deploy; compute pre-existing)
image_sha: n/a
verifier_notes: "never computed" premise disproven. No re-derivation. Serving-alias fix is α/serving,
        outside β.D2 ownership — precise handoff filed to α. §N.5 respected (address_resolver already
        references saham_position; no drift introduced).
```

---

## EL-18 — Per-dosha bhaṅga / cancellation beyond Neecha-Bhaṅga

**G0 reproduce-or-reclassify.** The named set is largely **already implemented on elev/beta**; the
live DB predates it. One genuine bug found + fixed.

### State of each named target (verified against elev/beta code + live catalog)
| Target | State | Grounding |
|---|---|---|
| Neecha-Bhaṅga (NBRY) | ✓ implemented | `ga_yoga_writer::_build_nbry_firing`, per-varga D1/D9, `grounds_jsonb` ledger, BPHS Ch.39 + Phaladīpikā Ch.7 (live) |
| Kemadruma bhaṅga | ✓ implemented | `ga_structural_writer::_detect_kemadruma`/`_cancel_kemadruma` — real kendra-support cancellation, `brahma_dosha_catalog.kemadruma` (BPHS); landed #735, 2026-07-24 (post-dates last build) |
| Śakaṭa bhaṅga | ✓ implemented (formation-exclusion) | `ga_yoga_writer` `shakata_dur_yoga` excludes when Jupiter in kendra from lagna (`brahma_dosha_catalog.shakata` bhanga, Saravali/BPHS). Does NOT form for either canonical chart → honest absence |
| **Kuja/Manglik** | **✗ was unreachable — FIXED this lane** | see below |

### The Manglik bug (root cause), and the fix
- `_cancel_manglik` (BPHS ch.81 tradition: own/exalt, Jupiter aspect on Mars-house, Jupiter/Venus
  in kendra, sign-specific pairs `_MANGLIK_SIGN_SPECIFIC_CANCEL`) has existed + been registered in
  `DOSHA_CANCELLATIONS` since 2026-07-16 (commit 3c0c49ed) — but was **unreachable dead code**.
- **Why:** the generic `_evaluate_catalog_rule` implements no handler for `manglik`'s formation
  shape `{"houses":[1,2,4,7,8,12],"planet":"mars","reference":["lagna","moon","venus"]}`, so it
  returned `(False, "rule_format_unimplemented")` → the dosha never formed → cancellation never ran.
  **Empirically confirmed 2026-07-25** (probe against the live module): both `manglik` and
  `kuja_dosha_lagna_7th` → `(False, 'rule_format_unimplemented')`.
- **Fix (surgical, grounded, additive):** added bespoke `_detect_manglik` (formation read literally
  from `brahma_dosha_catalog.manglik.formation_rule_jsonb`: Mars in 1/2/4/7/8/12 from lagna, and
  from Moon and from Venus) and registered `"manglik": _detect_manglik` in `BESPOKE_DOSHA_DETECTORS`.
  This makes the existing BPHS-cited `_cancel_manglik` reachable. Corrected the misleading in-code
  comment that claimed "no bespoke detector needed". **No new cancellation math; no fabrication.**

### End-to-end verification (charter bar: "spot-check ≥1 bhaṅga verdict end to end: rule → citation → applied condition → result"), both charts, deterministic:
- **Abhisek 482012f1** — Mars in 7th (Libra). Forms (from lagna). Cancellation grounds: none
  (not own/exalt; Jupiter h9 does not aspect house 7; neither Jupiter nor Venus in kendra; Libra
  not a house-7 sign-specific pair). → `bhanga_active=False` — honest "Manglik present, uncancelled."
  citation_ref `bphs:manglik:own_exalt_or_jupiter_aspect_or_sign_specific_cancels`.
- **Abhinandan 1c826d5a** — Mars in 12th (Pisces), also 1st-from-Venus. Forms. Grounds:
  `jupiter_in_kendra_h10` (Jupiter in 10th = kendra) AND `sign_specific_cancel:mars_h12_Pisces`
  (Mars in Pisces in the 12th — the classical BPHS ch.81 sign-specific pair). → `bhanga_active=True`,
  Manglik cancelled. Two independent grounds, both cited.

### Rebuild — DEFERRED TO INTEGRATION (not performed by this lane)
The `~/elev-v2-shared/locks/db-rebuild` lock was held by sibling lane **β.D**, concurrently
rebuilding the SAME writer (`ga_sensitive/ga_structural/ga_vargas`) for both charts. Rebuilding
ga_structural from β.D2's isolated branch (elev/beta base + manglik, WITHOUT β.D's EL-30/40/47
fixes) would have clobbered β.D's concurrent prod output (charter finding #15). **Ruling:** the
authoritative live rebuild belongs to the integration phase, on the merged head carrying BOTH
lanes' ga_structural changes. Ready-to-run script committed:
`platform/python-sidecar/scripts/rebuild_el18_manglik_ga_structural.py` (both charts, per-chart, FROZEN
orchestrator; re-assert FORENSIC 7/7 after). FORENSIC risk is nil for the anchors: ga_structural
does not produce the 7 FORENSIC anchors (ga_positions/ga_panchanga do), so a ga_structural-only
rebuild cannot move them.

### Doshas left honestly uncancelled/undetected (B.10 — disclosed, not fabricated)
- Per-house `kuja_dosha_*` catalog rows (`kuja_dosha_lagna_1st/2nd/4th/7th/8th`,
  `kuja_dosha_lagna_12th`, `kuja_dosha_from_moon`, `kemadruma_compat_kuja`) also fail the generic
  evaluator's shape and are NOT separately wired. **Intentional:** the canonical `manglik` entry
  (Mars in 1/2/4/7/8/12 from lagna/Moon/Venus + full BPHS-ch.81 cancellation) is the authoritative
  Kuja/Manglik verdict; wiring the redundant per-house variants would create the multi-authority
  smell the codebase explicitly avoids (cf. kala_sarpa comment). Left as honest absence.
- "Both-partners-Manglik" cancellation — a synastry-only ground; correctly out-of-scope for a
  single natal chart and disclosed in `_cancel_manglik`'s citation_human (not silently dropped).
- Kemadruma's 4th catalog ground ("Moon aspected by a benefic") remains an honest floor in
  `_cancel_kemadruma` (positional grounds computed; aspect ground not fabricated) — pre-existing.

### Evidence block — EL-18
```
el_id: EL-18
status: PREPARED-FOR-NATIVE (code fix complete + unit-tested + offline end-to-end verified both charts;
        authoritative live rebuild deferred to integration to avoid clobbering sibling lane β.D)
before_payload_ref: baseline + live: ganita_yoga_firings_get shows bhanga_na_reason floors; NO manglik
        row in dosha_label (chart A, built 2026-07-15); _evaluate_catalog_rule(manglik)→rule_format_unimplemented
after_payload_ref: test_el18_manglik_bhanga.py GREEN (7 passed); offline verdicts — A: bhanga_active=False,
        B: bhanga_active=True (grounds jupiter_in_kendra_h10;sign_specific_cancel:mars_h12_Pisces)
probes_run: empirical _evaluate_catalog_rule probe; _detect_manglik + _cancel_manglik on both charts;
        Lane-3 registry (18) + NBRY/D9 (52) regression GREEN
charts: 482012f1 (Manglik uncancelled), 1c826d5a (Manglik cancelled) — both grounded BPHS ch.81
deploy_revision: n/a (rebuild deferred to integration; script committed)
image_sha: n/a
verifier_notes: fix is additive + makes existing grounded rule reachable; no fabricated doctrine.
        Live-DB landing pending the integrated ga_structural rebuild (both lanes' changes present).
```

**ADDENDUM (Stream-Conductor, 2026-07-25, integration phase) — live rebuild landed, VERIFIED-CLOSED.**
`rebuild_el18_manglik_ga_structural.py` was run from the fully-merged `elev/beta` head (both β.D's
EL-30/40/47 fixes and this lane's Manglik fix present in `ga_structural`), after fixing a real bug
found at execution time (`build_runs.scope='per_chart'` violates the live `CHECK` constraint —
corrected to the established `'asset_set'` convention every precedent dispatch script uses; this
script had never actually been executed before, per its own deferred-to-integration design).
**Live SQL confirms both charts exactly as predicted:** 482012f1 → `fires=true, bhanga_active=false`
(Manglik uncancelled); 1c826d5a → `fires=false, bhanga_active=true` (cancelled, BPHS ch.81). FORENSIC
7/7 re-confirmed PASS both charts post-rebuild. `ka_gochara_sweep`/`ka_gochara_resonance` verified
untouched throughout (binding native ruling). **Disposition updated: `VERIFIED-CLOSED`** — supersedes
the `PREPARED-FOR-NATIVE` status above, which was accurate pending this integration step. Full
integration-rebuild account: `~/elev-v2-shared/proxy/beta.md`.

---

## Files changed (β.D2)
- `platform/python-sidecar/ga_writers/ga_structural_writer.py` — add `_MANGLIK_HOUSES` + `_detect_manglik`;
  register `"manglik"` in `BESPOKE_DOSHA_DETECTORS`; correct misleading comment + `_cancel_manglik` docstring.
- `platform/python-sidecar/tests/test_el18_manglik_bhanga.py` — NEW (7 tests, pure unit).
- `platform/python-sidecar/tests/test_el19_saham_recompute.py` — NEW (5 tests, DB-optional).
- `platform/python-sidecar/scripts/rebuild_el18_manglik_ga_structural.py` — NEW (integration rebuild script).
- `00_ARCHITECTURE/llm_consumption_audit/ledgers/BETA_D2.md` — this ledger.

## Native-Proxy rulings (also in ~/elev-v2-shared/proxy/beta.md, prefix [LANE-D2])
1. Branch name flattened `elev/beta/D2-…` → `elev/beta-D2-…` (git D/F ref conflict; PR base unchanged).
2. G0 re-scope: EL-19 sahams already computed/grounded/served (no re-derivation); EL-18 cancellation
   math already present, Manglik unreachable due to formation-shape gap → surgical detector fix.
3. Rebuild deferred to integration (sibling lane β.D holds the lock rebuilding the same writer;
   compete-rebuild would clobber their fixes).

## FORENSIC
Not re-asserted by this lane (no rebuild performed — deferred to integration). The eventual
ga_structural-only rebuild cannot move the 7 anchors (produced by ga_positions/ga_panchanga).
Integration MUST re-assert FORENSIC 7/7 on both charts after running the rebuild script.
