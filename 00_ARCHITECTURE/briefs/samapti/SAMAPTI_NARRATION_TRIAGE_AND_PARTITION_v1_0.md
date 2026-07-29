---
artifact: SAMAPTI_NARRATION_TRIAGE_AND_PARTITION
canonical_id: SAMAPTI_NARRATION_TRIAGE_AND_PARTITION
version: 1.0
status: READY-FOR-VERIFICATION
created: 2026-07-30
lane: A8-NAR-TRIAGE
track: SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §6 (T3)
governs: >
  The six B-NAR-* narration fix lanes (B-NAR-BO / GA / MI / PH / KA / TS). §4 of this document
  is the AUTHORITATIVE file-ownership partition for those lanes. No B-NAR lane may edit a file
  this partition does not assign to it. Where §4 and the queue's inline `scope:` list disagree,
  §4 governs and the disagreement is called out explicitly in §4.3.
baseline: origin/main @ cdb6fc3b3d37e3b586f188649c59e57c251ed935
chart_under_test: 482012f1-710e-4a25-994a-93821f5871aa
sources:
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_FIX_LEDGER_v1_0.md (v1.2)
  - 00_ARCHITECTURE/narration_audit/NARRATION_DETERMINISM_AUDIT_v1_0.md (seed audit F1–F29 — UNTRACKED, see §6.1)
  - 00_ARCHITECTURE/briefs/samapti/SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §6
---

# SAMĀPTI · A8-NAR-TRIAGE — Narration triage + conflict-free lane partition

This lane **triages only. It fixes nothing.** Every fix belongs to a B-NAR-* lane.

Three deliverables:
1. **§1** — the "already closed" items, confirmed against `origin/main` by SHA (three asked for; a
   fourth found).
2. **§2/§3** — adversarial verdicts on the 7 PLAUSIBLE P2 items, and on seed F18.
3. **§4** — the file-ownership partition. **One file → exactly one lane.**

---

## §1 — VERIFY-FIRST: already-closed items

All cited SHAs were tested for existence (`git cat-file -t`) and ancestry
(`git merge-base --is-ancestor <sha> origin/main`). Content was re-derived at the cited symbol —
never taken from the commit message.

| Item | PR | SHA (full, verified) | Ancestor of `origin/main`? | Content re-derived on `origin/main` | Verdict |
|---|---|---|---|---|---|
| **SV-3** — `ga_structural_writer` unpinned `fact_key` (P0-N1) | #864 | `fdd6912cc3bc67ca1c26269f8c53b27bdab59a6a` | **YES** | `_load_shadbala_and_bhava_fact_ids` now carries `AND fact_key = 'rupa'` on `graha_shadbala_total` and `AND fact_key = 'total'` on `house_bhava_bala_total`, with a P0-N1 docstring naming the fix. Regression test present: `platform/python-sidecar/ga_writers/__tests__/test_ga_structural_shadbala_fact_key_pin.py` | **VERIFIED-FIXED** |
| **SV-4** — migration-339 `narration_model` OpenAI allowlist drift (P0-N2) | #862 | `81509e0772a7137d43b2bca7f04fd0ca78890822` | **YES** | New `platform/supabase/migrations/469_phala_phaladesa_narration_model_allowlist_drift.sql` DROPs + re-ADDs the CHECK to exactly `{gemini-pro, gemini-ultra, gemini-2.0-flash, deepseek-chat, deepseek-r1}`, guarded by a pre-flight `RAISE EXCEPTION` if any row already holds a value about to be forbidden | **VERIFIED-FIXED (code)** — see §1.1 |
| **P1-e** — `services/ph_phaladesa/engine.py:39` OpenAI allowlist hole | #837 | `c3ea4128f4626a0a5859adfa3a3fc43cfbc9441f` (SHA absent from the queue; resolved via `git log --grep='#837'`) | **YES** | `PERMITTED_NARRATION_MODELS` = `{gemini-pro, gemini-ultra, gemini-2.0-flash, deepseek-chat, deepseek-r1}`. `gpt-4o` / `gpt-4-turbo` **absent**. `BANNED_MODEL_PREFIXES` still bans `claude-`/`anthropic/` | **VERIFIED-FIXED** |
| **`mi_darshana.py:159`** — P2 item **NOT** on the VERIFY-FIRST list; found already closed | #839 | `d76588ffee0c806ca1e8a427521207afb1f4cacb` | **YES** | The P0-10 PR swept the sibling truthiness pattern in the same file. `channel_propensity` is now explicitly `is not None`-tested, with `prior_propensity` used only when genuinely missing, and an in-code comment naming it "P2 mislabel/drift fix (same file as P0-10, same truthiness pattern)" | **VERIFIED-FIXED — removed from B-NAR-MI** |

**Commands + real output.**

```
$ git rev-parse origin/main
cdb6fc3b3d37e3b586f188649c59e57c251ed935

$ git cat-file -t fdd6912c && git log -1 --format='%H %s' fdd6912c
commit
fdd6912cc3bc67ca1c26269f8c53b27bdab59a6a fix(ga_structural): pin fact_key on shadbala/bhava_bala
  selection (P0-N1) + fleet-wide vocabulary audit + fresh-chart CI smoke (#864)
$ git merge-base --is-ancestor fdd6912c origin/main && echo YES
YES

$ git cat-file -t 81509e07 && git log -1 --format='%H %s' 81509e07
commit
81509e0772a7137d43b2bca7f04fd0ca78890822 fix(security): close migration-339 narration_model
  OpenAI-allowlist drift (P0-N2) (#862)
$ git merge-base --is-ancestor 81509e07 origin/main && echo YES
YES

$ git log origin/main --oneline --grep='#837'
c3ea4128 fix(suddhavaca/ph-nimitta-engine): honest 'mixed' fallback for direction
  + close OpenAI allowlist hole (P0-11) (#837)

$ git merge-base --is-ancestor d76588ff origin/main && echo YES
YES
$ git log -1 --format='%H %s' d76588ff
d76588ffee0c806ca1e8a427521207afb1f4cacb fix(suddhavaca/mi-darshana): P0-10 D4_GRADE_INVERSION
  — preserve computed grade=0.0 (#839)
```

**None of these is re-opened.** No B-NAR lane carries any of them.

### §1.1 — SV-4 honest caveat (not a re-open)

Migration 469 is committed to `main`. Whether it is **applied in production** cannot be verified
from a git worktree. That is SAṂGATI check **§8.5**'s job. Recorded here so §8.5 has a concrete
target: the highest applied `platform/supabase/migrations/` number must be ≥ **469**. The
*code-side* claim is fully closed; only the *applied-state* claim is out of this lane's reach.

---

## §2 — Adversarial verification of the 7 PLAUSIBLE P2 items

Each item was handed to a sub-auditor instructed to **refute** it, with the standing note that
REJECTED is a valuable outcome. Because the describing census is lost (§6.1), each auditor had to
**re-derive** the finding from the bare `file:line` pointer before attacking it.

| # | Item (`file:line`) | Verdict | Basis |
|---|---|---|---|
| 1 | `mi_bhavisya.py:161` (seed F25) | **CONFIRMED — escalate severity** | §2.1 |
| 2 | `bo_cdlm_summary.py:348` | **CONFIRMED — escalate severity; root cause is a *different* file** | §2.2 |
| 3 | `ka_kala_darshana.py:180` (seed F27) | **REJECTED — unreachable** (a *different*, reachable defect found in the same file) | §2.3 |
| 4 | `register_p1_ganita.ts:374` | **REJECTED — unreachable; zero files need editing** | §2.4 |
| 5 | `ga_sensitive_writer.py:2677` | **CONFIRMED** | §2.5 |
| 6 | `mi_darshana.py:360` | **CONFIRMED — but it IS the SV-5 `verdict_note` item under a pre-fix line number. Promotion, NOT a second finding** | §2.6 |
| 7 | `mi_bhavisya.py:103` (seed F28 family) | **REJECTED — `NOT NULL` makes it unreachable** | §2.7 |

**Score: 4 CONFIRMED (one of which is a re-identification of an already-known item, not a new
finding), 3 REJECTED.** Two rejections retire work outright; the third (§2.3) redirects a lane onto a
different, reachable defect in the same file. Two confirmations escalate above their filed severity.

### §2.1 — `mi_bhavisya.py:161` (seed F25) → **CONFIRMED**, severity escalated GAP → **P1-class**

The original auditor could not confirm this because no surface exposed
`mimamsa_predictions.driving_signals`. That blocker is now **discharged** — the column was read
directly from production.

Code (exact line, no drift):

```python
driving = msr_by_domain.get(domain) or [
    {"signal_id": sid, "strength": 1.0, "family_id": _signal_family_key(msr_signals[sid])}
    for sid in list(msr_signals.keys())[:5]
]
```

Live evidence, chart `482012f1-…`: **53 of 142 predictions (37%)** carry `driving_signals` in which
**zero of 265 signal references** is tagged to the prediction's own domain.

| pred_domain | n_preds | signal refs | domain-matched | **MIS**matched | strength range |
|---|---|---|---|---|---|
| **transition** | **50** | 250 | **0** | **250** | 1.0 – 1.0 |
| **general** | **3** | 15 | **0** | **15** | 1.0 – 1.0 |
| career | 30 | 150 | 150 | 0 | 2.403 – 2.485 |
| spirituality | 50 | 250 | 250 | 0 | 2.161 |
| relationship | 5 | 25 | 25 | 0 | 2.161 |
| character | 3 | 15 | 15 | 0 | 2.485 – 2.809 |
| health | 1 | 5 | 5 | 0 | 0.69 – 1.2 |

Root cause is a **vocabulary disagreement between two subsystems**, so the fallback is *guaranteed*,
not merely possible:
- `bodha_msr_signals.domains_affected_array` vocabulary = `{career, character, health, relationship, spirituality, wealth}`
- `phala_anchors.domain` vocabulary = `{career, character, general, health, relationship, spirituality, transition}`
- `transition` and `general` are **structurally absent** from the MSR side → `msr_by_domain.get(...)`
  is always `None` for them → the `or` branch fires 100% of the time.

Secondary defect in the same expression: the literal `"strength": 1.0` **overwrites real salience**
(true values 2.81 / 2.81 / 2.72 / 2.51 / 2.49) — a **D3_HARDCODED_DRIFT** riding inside the
D1_MISSELECT.

Refutations attempted and defeated: *(i)* "it's documented, so intended" — the *branch* is
documented at `:158-160`, but the finding is that the *output* is unflagged; the emitted dict has
only `signal_id`/`strength`/`family_id`, and `platform/migrations/347_mimamsa_bhavisya.sql:20`
declares `driving_signals jsonb NOT NULL` with no companion provenance column. *(ii)* "`strength:
1.0` is itself the tell" — not a contract, and already ambiguous: the live `health` bucket spans
0.69–1.2, straddling 1.0. *(iii)* "cosmetic provenance only" — **no**: consumed by
`mi_gunanaka.py:108,130`, `mi_pariksha.py:404,446`, and served at
`platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts:88`, so 53 predictions'
attribution mass is routed to `character`-family signals. *(iv)* "the vocabularies always
intersect" — directly disproven above.

**Why escalate:** this corrupts the L5 attribution/calibration substrate, not a narration string.
The queue lists it as one P2 line item; it is the heaviest finding in the whole T3 band.

**Recommended split** (the full fix is restructure-scale and crosses layers):
- **B-NAR-MI now:** tag the fallback (`match_mode: 'domain' | 'chartwide_fallback'`) and preserve
  real salience instead of `1.0`. Honest, in-lane, one function.
- **Reconciling the L4-anchor vs L2-MSR domain vocabularies** so `transition`/`general` can match at
  all: **out of scope** — file as a costed spec. Do **not** let B-NAR-MI attempt it.

### §2.2 — `bo_cdlm_summary.py:348` → **CONFIRMED**, and the fix is in a *different file*

Line 348 exact, inside `_build_clusters`:

```python
outcome = (
    "reinforcing" if marker.startswith("positive") else
    "conflicting" if marker in ("inverse", "neutral") else
    "mixed"
)
```

The whole classification chain is **dead code**, because its only input —
`bodha_cdlm_cells.domain_relationship_class` — is hardcoded `NULL` by its **sole producer**:
`bo_sangati.py` *computes* the class at `:292-298`
(`positive_strong|positive_moderate|positive_weak|neutral|inverse`), names the column in
`_CELL_INSERT` at `:68`, and then **supplies a literal `NULL`** at value slot 48. Verified by
mechanical 59-column/59-value alignment; the `NULL, NULL, NULL,` triple covering slots 47–49 is at
`bo_sangati.py:~88`.

Live: `bodha_cdlm_cells` → **225 cells, 100% `domain_relationship_class IS NULL`** (yet
`net_linkage_strength` spans 0.604 – 1546.26, i.e. ≥2 distinct real classes).
`bodha_cdlm_pattern_clusters` → **15 rows** (3 charts × 5 ayanamshas), **all**
`pattern_marker_type='unclassified_linkage_cluster'` / `predicted_outcome_class='mixed'`.

**D6_COVERAGE_GAP, live on every chart**, with a latent **D2_MISLABEL** inside it (`"neutral"`
bucketed as `"conflicting"` — a valence inversion; latent only because `net == 0` exact-float is
effectively unreachable, prod min net = 0.604).

Refutations defeated: *(i)* "never served" — served via
`platform/src/lib/retrieval/registry/layers/L2_bodha/query_cdlm_summary.ts:57-61` (`TIER_TABLE`
`:37`) and raw at `query_domain_reading.ts:456`. *(ii)* "a DB CHECK forces the vocabulary" —
`predicted_outcome_class` is bare `TEXT`, **no CHECK** (`platform/migrations/325_l2_bodha_enriched_schema.sql:371`,
`platform/supabase/migrations/226_bodha_spec_tables.sql:337`). *(iii)* "a later line corrects it" —
no `UPDATE … domain_relationship_class` anywhere in the repo. *(iv)* "documented deferral" —
`bo_cdlm_summary.py:418-423` documents what *is* deferred (`evolution_gradients`) and is silent on
this.

**Bonus find, load-bearing for CI honesty:** an existing gate already asserts against this —
`platform/python-sidecar/tests/l2/test_b6_eval_harness.py:468-481` requires **< 10%** of CDLM cells
to be missing `domain_relationship_class`; production is at **100%**. The gate is DB-gated and
evidently **not running in CI**. Flagged to A7-N8-AUDIT / B-N8-LINT as a detector that exists but
does not fire (§6.4).

**Partition consequence:** the fix needs `bo_sangati.py` **and** `bo_cdlm_summary.py`. Both are
already B-NAR-BO under this partition (`bo_sangati.py` also carries seed F21) — **no cross-lane
conflict**. This is the partition working as designed.

### §2.3 — `ka_kala_darshana.py:180` (seed F27) → **REJECTED (unreachable)**

F27's Python operator-precedence analysis is **correct**: lines 181-183 are adjacent f-string
literals that parse into one `JoinedStr`, so `A if orb_strength else f"confidence: {conf_str}"`
governs the whole concatenation and a falsy `orb_strength` would drop rarity + mode.

**It dies on reachability.** Every DAG-reachable producer guarantees a truthy value — all four
window generators in `platform/python-sidecar/services/ka_sangam/engine.py`, invoked from
`ka_sangam.py:643/667/695/728`:

| Mode | Guarantee | Site |
|---|---|---|
| A | `if orb_s < HIGH_CONFIDENCE_ORB_THRESHOLD: continue` | `engine.py:985`, emit `:1056` |
| B | same gate + a `magnitude` gate | `engine.py:1165/1168`, emit `:1228` |
| C | `'orb_strength': 1.0` literal | `engine.py:1358` |
| D | `'orb_strength': 1.0,  # sign-level: no angular orb` | `engine.py:1482` |

`HIGH_CONFIDENCE_ORB_THRESHOLD = 0.45` (`engine.py:782`, pinned by `tests/l3/test_ka_sangam.py:657`).
`ka_sangam.py:929-932` is the **sole** orchestrator-side `INSERT INTO kala_convergence` carrying the
column; **no `UPDATE kala_convergence` exists anywhere in the repo**.

Live, whole-table: **83,012 rows; 83,012 non-null; min 0.7; max 1.0; 0 NULL; 0 zero.** F27's "every
observed value = 1.0" understated it — the *floor across the entire table* is 0.7.

Further, the ternary is a **deliberate `None`-guard**, not a precedence slip:
`f"{orb_strength:.2f}"` raises `TypeError` on `None`, and the sibling line 165 uses the same
defensive idiom correctly.

The only falsy-producing path is dead legacy that destroys the table first:
`brahmagyan/kala/convergence.py:527-540` inserts omitting `orb_strength` (nullable column,
`CHECK (orb_strength >= 0 AND orb_strength <= 1)` at
`platform/supabase/migrations/244_l3_ka_sangam.sql:6`, so NULL passes) — but `seed_convergence` has
**zero callers** outside its own `__main__` (`:700`), calls `conn.commit()` itself (a hard
`WriterBase` violation per CLAUDE.md §N.2, so it can never be a DAG writer), and `DELETE`s all
83,012 `ka_sangam` rows first (`:523`).

**Verdict: REJECTED.** One lane's worth of work saved. Demote to latent-only; no fix required.

**But the same function holds a *reachable* defect the census missed.**
`ka_kala_darshana.py:168`:

```python
mode_label = 'daśā-aligned' if mode == 'A' else 'independent sweep'
```

Modes **C** (subsystem / sade-sati sign-ingress, `engine.py:1355`) and **D** (AV-bindu ingress,
`engine.py:1479`) are both real and both DB-legal —
`platform/supabase/migrations/361_kala_convergence_domain.sql:28-31` widened
`kala_convergence_mode_check` to `('A','B','C','D')` — yet both narrate as "independent sweep",
which is **Mode B's** meaning. **D2_MISLABEL, reachable, one-line, same file.**

**This is now the finding that justifies opening `ka_kala_darshana.py` in B-NAR-KA** — logged as
**NEW-KA-1**. F27 itself is closed REJECTED.

### §2.4 — `register_p1_ganita.ts:374` → **REJECTED (unreachable)**

Line 374 has not drifted; it is the head of the `formed` narration branch in
`buildPanchaMahapurushaVerdict`. The strongest constructible finding was that
`:376` asserts *"the own/exaltation-in-kendra condition is satisfied"* with no `positionsAvailable`
guard and no `KENDRA_HOUSES.has(pos.house)` re-check, so it could narrate a confirmed-sounding
verdict from a `requires_pass` catalog row (D7 + a §N.6-part-1 D2 overlay).

Refuted on four independent grounds:
1. **The sentence restates the rule that actually fired, not a re-derivation.** Live
   `brahma_yoga_catalog.formation_rule_jsonb` for all five entries is exactly
   `{"requires":[{"planet":X,"dignity":["own","exalted"],"house_class":"kendra"}]}` —
   "own/exaltation-in-kendra" *is* the rule.
2. **`requires_pass` is a naming artifact here, not an unverified row.**
   `ga_structural_writer.py:6019` returns `True, "requires_pass"` only *after* every structured
   sub-requirement was evaluated against per-chart facts; empty `requires` fails closed
   (`:5891-5893`), non-list fails closed (`:5907-5908`), unimplemented sub-key/house_class/exclude
   shapes hard-fail (`:2091-2118`, `:5911-5945`). The "decorative stub" caveat at `:2704` applies to
   the **dosha** catalog's free-text `requires`, not these entries.
3. **Firings-authoritative agreement is 10/10 in production.** `ga_yoga_firings` shows `sasa
   fired=true` (all 5 ayanamshas, chart `482012f1`, strength 1.566) and `malavya fired=true` (all 5,
   chart `cb73cd3d`); every Mahapurusha `yoga_label` row anywhere in `chart_facts` corresponds to
   `fired=true`.
4. **Neither truncation path can fabricate.** Positions fetch is `limit:200` against 86
   `graha_position` rows per ayanamsha; the grounding fetch is `limit:500` against a max union of 14
   rows — the Y-12 fabrication class is genuinely closed. A thrown fetch aborts the whole block
   (`:1024-1026`), and a genuinely empty position set carries the explicit caveat at `:406-410`.

Every state that would falsify `:376` requires either an L1 self-contradiction between a fired
`yoga_label` row and the served `graha_position` (a §N.5 **halt-worthy build bug**, not a narration
bug) or a torn build that §N.3's delete-then-insert-in-transaction standard forbids.

**Verdict: REJECTED. Zero files need editing.** One residual worth a single line of the TS lane
owner's attention (**not** a correctness defect): `per_yoga[].statement` carries no
`single_pass`/`catalog_only` qualifier even though the same `verdict` object reports
`catalog_only_rows_in_page` (`:1050`) and a `firings_pointer.note`. That is a §N.6 presentation-
integration nicety, and it is explicitly **optional**.

### §2.5 — `ga_sensitive_writer.py:2677` → **CONFIRMED**

Line exact, no drift. The comment block immediately above it documents the **M-11 fix** that
condemned exactly this pattern — and then the code keeps it:

```python
# M-11 fix: read the correct "sensitive_points" key (was "upagrahas", never
# populated by compute_chart — always empty, so these silently fell back
# to the hand-rolled Saturn+6/Saturn+8 constants every build).
gulika_long = all_longs.get("SAT", 0.0) + 6.0
mandi_long  = all_longs.get("SAT", 0.0) + 8.0
```

**D3_HARDCODED_DRIFT** with a D7 consequence: the seed flows into `_build_aprakasha_rows`
(`:2737-2738` → `:1961-1962`, `pidaa = gulika_long`, `vighni = (mandi_long + 20.0) % 360.0`) and is
served as `aprakasha_position/PIDAA` / `VIGHNI` narrated *"BPHS Ch.8: Pidaa = Gulika longitude"* with
**ordinary (non-`floored`) verification status** — a hand-rolled constant shipped under a classical
attribution.

The decisive evidence is that **all three sibling builders in the same file were rewritten for
precisely this error path and this one was not**:

| Sibling | Behaviour on adapter error | Site |
|---|---|---|
| `_build_upagraha_rows` | *"floor rather than serve a fabricated/unverified constant"* | `:615-628` |
| `_build_saturn_derived_rows` | `is not None` guard; emits `verification_pass_status="floored"` + `[EXTERNAL_COMPUTATION_REQUIRED]`; provenance text reads *"delegated, **not a hand-rolled Saturn+6° proxy**"* | `:681-703`, `:693`, `:728-729` |
| `_build_gulika_mandi_sensitive_rows` | falls back to the classical day-segment formula, named honestly in provenance | `:2279-2292` |
| **line 2677 (this finding)** | **keeps the rejected Saturn+6°/+8° proxy** | — |

Refutations defeated: *(i)* "upstream always populates it" — normally yes
(`pyjhora_adapter/compute.py:88/:138`, `sensitive_points.py:77-87`), **but the error path at
`sensitive_points.py:88-89` writes `out[name] = {"error": ...}`, which is a dict and so passes the
`isinstance` check at `:2680` while carrying no `longitude_deg`** — the seed survives. *(ii)* "never
narrated" — false; `aprakasha_position` is a served category
(`platform/src/lib/retrieval/registry/layers/L1_ganita/get_positions.ts:89`, `:141`). *(iii)* "a
later line corrects it" — no reassignment exists between `:2677` and `:2738`, and
`_build_gulika_mandi_sensitive_rows` writes a *different* category with its own locals.

**Two concrete triggers, both in-block:**
(a) Any build where `drik.upagraha_longitude` raises for `gulika`/`maandi` — it is a sunrise/sunset
day-segment solve, so a polar-latitude birth place or any rise-set failure does it. Observable
signature: **within one build**, `saturn_derived_point/GULIKA_LAHIRI` and `MANDI` are correctly
`floored` while `aprakasha_position/PIDAA` / `VIGHNI` ship `SAT+6°` and `SAT+8°+20°` as ordinary
verified longitudes.
(b) `if v:` truthiness at `:2682`/`:2686` (the siblings use `is not None`) discards a legitimate
`longitude_deg == 0.0` — i.e. 0°00′ Aries.

Also noted: `pidaa` is assigned **without `% 360.0`** at `:1961`, so the fallback can emit 360–366°,
which native values (always in `[0,360)`) cannot and no constraint rejects.

**Fix size:** one-function. Seed as `None`; `if v:` → `if v is not None:`; floor `PIDAA`/`VIGHNI` in
`_build_aprakasha_rows` mirroring `:697-703`; add the missing `% 360.0`.
**Files:** `ga_sensitive_writer.py` only (`:2677-2687` + `_build_aprakasha_rows` `:1942-1978`) plus a
new test. **B-NAR-GA already owns this file — no partition change.**

**One settling query left for the lane** (the auditor's DB tunnel dropped): compare
`aprakasha_position/PIDAA.longitude_sidereal` against `graha_position/SAT.longitude_sidereal + 6` for
`482012f1-…` / `cb73cd3d-…`, and check whether `saturn_derived_point/GULIKA_LAHIRI` is `floored`. If
GULIKA_LAHIRI holds a real value the fabrication is **dormant-but-reachable**; if it is floored, the
fabrication is **live in production today**. The verdict does not depend on the answer — only the
urgency does.

### §2.6 — `mi_darshana.py:360` → **CONFIRMED, but it IS the SV-5 item. Do not double-count.**

**The ledger's `mi_darshana` line numbers are PRE-fix**, not post-fix. Proof: the same ledger block
cites `mi_darshana.py:159` for the `channel_propensity` truthiness bug, and pre-fix `:159` is exactly
`prop = float(r.get("channel_propensity") or r.get("prior_propensity") or 0.5)` — which now sits at
`:164`. (This independently corroborates §1's fourth row.)

At `d76588ff^` (pre-fix), line 360 verbatim:

```python
359    if grade >= 6.0:
360        verdict_note = "Strong evidence across traditions."
```

Post-fix on `origin/main` the same statement is at **`:377`**, guard at `:376`.

**So `mi_darshana.py:360` and the parked SV-5 `verdict_note` tradition-blindness item are ONE
finding.** Three confirmations: (1) pre-fix `:360` *is* that line, character-for-character; (2) PR
#839's own commit message names it — *"P2 PLAUSIBLE item at `mi_darshana.py:360` (verdict_note claims
'Strong evidence across traditions' based on grade alone, independent of whether
tradition_concordance actually has any data) is left unfixed"*; (3) `CURRENT_STATE_v1_0.md:127` lists
it **once**.

**And it upgrades PLAUSIBLE → CONFIRMED with a structural trigger.** The adversarial pass found the
kill shot: `tradition_concordance` is **guaranteed empty for 6 of the 13 legal event domains**.

| Source | Values |
|---|---|
| `brahma_event_ontology.domain` — `NOT NULL CHECK` (`platform/supabase/migrations/388_brahma_ghatana_ontology.sql:14-16`) | **13**: career, wealth, relationship, **progeny**, health, **education**, **family**, **residence**, **travel**, spirituality, character, **transition**, general |
| `bodha_triangulation.question_class`, written as `question_class: domain` from `bo_sangati.KNOWN_DOMAINS` (`bo_sangati.py:46-49`, `:148`, `:169`) | **7**: career, wealth, health, relationship, spirituality, character, general |

The 6 bolded domains can **never** have a triangulation row, so `trad_by_class.get(domain)` at `:362`
misses by construction → `tradition_concordance = {}` → and `:377` still asserts cross-tradition
strength. Secondary D6 on the same line: the first disjunct
`trad_by_class.get(event_class_id)` is **unreachable for 100% of rows**, because `bo_sangati.py:169`
only ever stores a *domain* string in `question_class`.

The narrated claim is served: `query_insights.ts:103-108` returns `statement` from
`mimamsa_insight_units`; `query_insight_embeddings.ts` also joins for it. Partial mitigant only —
`verdict_content` (carrying `tradition_concordance`) lands in `provenance_chain`, which
`query_insights.ts:105` does select, so a diligent caller can see `{}` beside the contradicting
sentence. That makes it self-contradicting rather than undetectable; it does not make the prose true,
and `statement` is the field that gets read.

**Consequence for B-NAR-MI: the lane's finding count is unchanged** — one item, now CONFIRMED with a
named trigger instead of PLAUSIBLE. Scope stays `one-function` (branch on both axes: grade **and**
tradition-presence) with an L5-only rebuild. **The root-cause fix — widening
`bo_sangati.KNOWN_DOMAINS` to the 13-value ontology enum — is restructure-scale, pulls an L2→L5
rebuild, and is explicitly OUT of B-NAR-MI's scope** (§6.3). `bo_sangati.py` belongs to B-NAR-BO
under this partition, so the partition already prevents the cross-reach; B-NAR-BO is likewise
instructed not to attempt it.

### §2.7 — `mi_bhavisya.py:103` → **REJECTED (unreachable)**

Line 103 verbatim: `salience = float(r["computed_salience"] or 1.0)`. **Not** the same defect as F28
(`:152`) nor as F25 (`:161`) — same `or`-default *shape*, different field, different table, and the
opposite constraint story.

The NULL half is **impossible by schema**: `computed_salience NUMERIC NOT NULL`
(`platform/supabase/migrations/226_bodha_spec_tables.sql:54`,
`platform/migrations/325_l2_bodha_enriched_schema.sql:107`; no later `ALTER` relaxes it). The line
even uses bracket access, not `.get()`, so "absent key" is impossible too. The F28-family
"fabricated default for a missing value" framing is therefore **dead for every chart, not just this
one**.

The 0.0 half has **no live instances and no plausible path**: 49,608 `bodha_msr_signals` rows,
`null=0`, `zero=0`, `min=0.227023`, `max=2.809404`. The salience formula
(`bodha_writers/formulas.py:553-575`) is a pure product whose factors are all floored strictly above
zero — `DIGNITY_SCORE` ≥ 0.10 (`:50-58`), `_av_multiplier` ≥ 0.70 (`:80-89`),
`VERIFICATION_RESCALE` ≥ 0.60 (`:486-490`), `VARGA_WEIGHT` ≥ 0.75 (`:493-496`), `bala_gate`
explicitly `max(0.30, …)` (`bo_laksana.py:1862`).

**Decisive corroboration — the live `strength: 1.0` values do not come from this line.** 710
driving-signal entries for the canonical chart, **265 with `strength` exactly `1.0`**. Since no
signal has salience NULL or 0, those 265 cannot originate at `:103`; they originate at the hardcoded
literal in the fallback comprehension at `:162` — i.e. **F25 (§2.1)**. `:103` is the decoy; F25 is
the real defect in this file.

**Verdict: REJECTED as filed.** A latent, unproven D4 truthiness variant survives re-framing but has
no demonstrated or provable trigger. **Recommendation: fold the one-line hardening
(`_raw = r["computed_salience"]; salience = float(_raw) if _raw is not None else 1.0`) into the F25
fix as a free rider** — same file, same function, same PR, zero marginal cost. Do **not** open a
lane for it.

Incidental corroboration of F28's own disposition: `phala_anchors.magnitude` **is** nullable with a
4-value CHECK (`platform/supabase/migrations/330_phala_anchors_and_drop_kala_timeline.sql:42`), so
F28 is schema-*reachable* — but 286/286 anchors across all charts carry a non-NULL magnitude, and all
142 canonical predictions read `magnitude_expected = 'minor'` (zero `'moderate'`). **F28's
"trigger not reproduced" disposition holds.** See §6.8 for why every anchor is `'minor'` — that turned
out to be a different, real defect.

---

## §3 — Seed F18: the ledger's disposition does **not** hold

`SUDDHA_VACA_FIX_LEDGER §P3` records seed F18 as **CANNOT-REPRODUCE** ("register text
unconfirmable"), and this lane's own instruction was to *confirm it remains* CANNOT-REPRODUCE.

**It does not. F18 is REPRODUCIBLE on `origin/main` today, and is already shipping.** Reported per
prime directive §1.1 (truth over completion) — a lane instruction cannot make a false disposition
true.

`platform/python-sidecar/services/ph_phaladesa/engine.py:53`

```python
_ALL_DOMAINS = ('career', 'wealth', 'health', 'relationship', 'spirituality', 'character', 'transition')
```

`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:69-74`

```python
_DOMAIN_LABEL: dict[str, str] = {
    'career': 'career and profession', 'wealth': 'wealth and finances',
    'health': 'health and vitality', 'relationship': 'relationships and marriage',
    'spirituality': 'spirituality and dharma', 'character': 'character and psychology',
    'general': 'general life-arc',
}
```

- `_ALL_DOMAINS − _DOMAIN_LABEL.keys()` = **{`transition`}** — emitted but unlabelled.
- `_DOMAIN_LABEL.keys() − _ALL_DOMAINS` = **{`general`}** — labelled but never emitted (dead config).
- Six keys intersect exactly. **The register's characterization is correct in full.**

Emission is unconditional (`engine.py:254-256`,
`return [derive_phaladesa_record(domain, ctx) for domain in _ALL_DOMAINS]`); the lookup at
`ph_phaladesa.py:79` uses a bare-slug default.

**Live proof the raw slug is already served** — `phala_phaladesa`, canonical chart, 7 rows (= exactly
`_ALL_DOMAINS`, no `general` row), all `narration_status = 'ready'`:
- `transition` → `"The transition domain rests on 50 predictive anchor(s)…"` ← **raw slug**
- every other row → a proper label, e.g. `wealth` → `"…for the wealth and finances domain…"`

**Not already-fixed:** `git log -S"_DOMAIN_LABEL" -- .../ph_phaladesa.py` returns exactly one commit,
`fc995882` — the commit that *introduced* the map. Nothing has amended it since.

**Why the earlier pass likely mis-called it:** the register's *engine* line citations have drifted
(cites engine `:50` for `_ALL_DOMAINS`, actually **`:53`**; cites `:253` for
`derive_phaladesa_for_chart`, actually **`:254`** with the comprehension at `:256`). The *writer*
citations (`:69-74`, `:79`) are exact. A line-number mismatch was read as an unconfirmable finding.

**Disposition: F18 → CONFIRMED, assigned to B-NAR-PH.** Cosmetic severity stands (the sentence is
truthful, the label is non-canonical). A `ph_phaladesa` re-run is needed for the fix to reach the 7
already-`ready` rows — folded into **C1-REBUILD**, not a separate rebuild.

**Shared root cause worth recording:** `general` is a live `phala_anchors.domain` value that never
survives into a phaladesa record because `_ALL_DOMAINS` alone drives emission and
`_ANCHOR_TO_PHALADESA_DOMAIN` (`ph_phaladesa.py:53-57`) maps only `financial`/`spiritual`/
`psychological`. **The same L4-anchor-vs-consumer vocabulary drift sits behind both F18 and F25
(§2.1)** — two independent findings, one underlying cause. Flagged for the costed spec in §6.3.

---

## §4 — THE PARTITION (authoritative)

### §4.0 — The rule

> **One file → exactly one lane.** A B-NAR lane may edit *only* files listed against it below. If a
> lane discovers it needs a file owned by another lane, it **stops and reports a residual** — it does
> not reach across. This is the whole reason the six lanes can run concurrently.

Test files follow the same rule (§4.4). Neither the source nor the test partition contains any file
twice — verified mechanically in §4.5.

### §4.1 — B-NAR-BO · Bodha writers

| File | Findings | Notes |
|---|---|---|
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_bimba.py` | P2 `:253` | |
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py` | P2 `:1387` | |
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py` | P2 `:1251` | |
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna.py` | P2 `:102` | `_grade_to_status` |
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_cdlm_summary.py` | P2 `:348` **CONFIRMED §2.2** | dead classification chain |
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_sangati.py` | seed **F21** `:292` + **root cause of `:348`** (`_CELL_INSERT` slot 48) | **added by this triage** — not in the queue's inline scope |
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py` | seed **F20** `:326` (`_infer_valence` benefic-before-malefic) | **added by this triage.** Confirmed still open: `:327` scans `_BENEFIC_VALUE_SUBSTRINGS` first, `:330` malefic only on no-hit. The P0-5/6 fix (#838) touched `_build_strength_lookup` only |

`rebuild_required: true` → deferred to **C1-REBUILD**.

### §4.2 — B-NAR-GA · Gaṇita writers + the stale gate allowlist

| File | Findings | Notes |
|---|---|---|
| `platform/python-sidecar/ga_writers/gates.py` | **P1-f** `:144` | `valid_statuses = {"single","two_pass_verified","classical_match","divergent_flagged"}` — confirmed present verbatim. Architecturally significant: a gate that mis-grades. §N.5 applies |
| `platform/python-sidecar/ga_writers/ga_sade_sati_writer.py` | P2 `:974` | |
| `platform/python-sidecar/ga_writers/ga_sensitive_writer.py` | P2 `:2677` **CONFIRMED (§2.5)** | fix spans `:2677-2687` **and** `_build_aprakasha_rows` `:1942-1978` — one file, one lane. Run the §2.5 settling query first to establish whether the fabrication is live or dormant |

**`ga_nakshatra.py` is NOT in this lane** — see §4.3.
`rebuild_required: true` → **C1-REBUILD**. §N.5 (L1 is authority over L2+) binds this lane.

### §4.3 — The one queue collision this triage had to resolve: `ga_nakshatra.py`

The queue creates a genuine two-lane claim on a single file:
- **B-N8-FIX** owns `ga_nakshatra.py:87` (`"verification_pass_status": "PASS"` hardcoded on every row
  with zero verification logic — confirmed present verbatim; the purest §N.8 violation in the corpus).
- **B-NAR-GA** is scoped `ga_nakshatra.py:289` and explicitly told *"NOT `ga_nakshatra.py:87` — that
  is an §N.8 violation, routed to B-N8-FIX."*

The two lanes sit on **different dependency chains** (`B-N8-FIX ← A7-N8-AUDIT`;
`B-NAR-GA ← A8-NAR-TRIAGE`) and would therefore run **concurrently on the same file** — exactly the
merge conflict this design exists to prevent. Line distance does not help: git conflicts on files,
and both lanes would rebase onto each other.

**Resolution (this triage's ruling, and the only place §4 overrides the queue):**

> **`ga_nakshatra.py` → B-N8-FIX, exclusively.** The P2 narration finding at `:289`
> (`agree_cnt = total_ay if len(unique) == 1 else 0`) rides along in **B-N8-FIX's** PR, carrying its
> narration acceptance criterion with it. **B-NAR-GA must not open this file.**

Rationale: the `:87` §N.8 defect is the higher-severity, architecturally-significant one and must not
be blocked, rebased, or delayed by a P2 mislabel; a P2 rider is cheap for the lane already inside the
file. The reverse assignment would subordinate the §N.8 fix to a cosmetic one.

**Routed to DVA as a scope question (§4 of the Conductor manual), with this as the recommended
default so nothing blocks.** Same-file riders also apply, with no collision, to `bo_chart_gestalt.py`
and `bo_pramana_mapa.py` — both wholly B-N8-FIX, neither claimed by any B-NAR lane.

### §4.4 — B-NAR-MI · Mīmāṃsā writers

| File | Findings | Notes |
|---|---|---|
| `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` | **SV-5** `verdict_note` tradition-blindness — post-fix `:376-377`, and **P2 `:360` is the SAME item under a pre-fix line number (§2.6). ONE finding, not two.** Now **CONFIRMED**, not PLAUSIBLE, with a structural trigger | **`:159` REMOVED — already fixed in #839** (§1). Fix keys on both axes (grade **and** `tradition_concordance` presence) at `:361-363` + `:376-381`. Secondary D6 same line: `trad_by_class.get(event_class_id)` is unreachable for 100% of rows. **Do NOT widen `bo_sangati.KNOWN_DOMAINS`** — that is the out-of-scope root cause (§6.3) |
| `platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py` | P2 `:81` | `verdict = row.get("composite_verdict") or ""` |
| `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py` | P2 `:382` | |
| `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py` | seed **F25** `:161` **CONFIRMED, escalated (§2.1)**. P2 `:103` **REJECTED (§2.7)** — fold its one-line hardening in as a free rider. Seed **F28** `:152` remains **trigger-not-reproduced** | scope-limited per §2.1: tag the fallback (`match_mode`) + preserve real salience. **Do NOT attempt the cross-layer vocabulary reconciliation (§6.3)** |
| `platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py` | P3 `:337` `'UUID' object is not subscriptable` in snapshot-publish | plus F25 consumer duty at `:108/:130` |
| `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` | F25 consumer `:404/:446/:487` | **added by this triage** — must honour the new `match_mode` flag |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts` | F25 serving surface `:88` | **CARVE-OUT from B-NAR-TS.** Owned by **MI**, not TS, because it is the serve half of one atomic fix. **B-NAR-TS must not open this file** |

`rebuild_required: true` → **C1-REBUILD**.

### §4.5 — B-NAR-PH · Phala writers and engines

| File | Findings | Notes |
|---|---|---|
| `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py` | **P1-b** `:121` (`contradiction = rec.contradiction_summary_jsonb` fetched, never consumed) + seed **F18** `:69` **CONFIRMED (§3)** | two findings, one file, one lane |
| `platform/python-sidecar/services/ph_sodhana/engine.py` | P2 `:38`, `:136` | |
| `platform/python-sidecar/brahmagyan/phala/l4_anchors.py` | P2 `:211` | |
| `platform/python-sidecar/brahmagyan/mimamsa/answer_quality.py` | P2 `:180` (`_check_b11_compliance`) | **path is under `brahmagyan/mimamsa/`** but the queue assigns it to PH. Assignment kept (unique claim ⇒ conflict-free). **B-NAR-MI must not open it** |
| `platform/python-sidecar/services/ph_rectification/engine.py` | P3 `:253` `_DASHA_LORD_NATAL_SIGN_INDEX` | verify the "sourced from chart_facts, embedded as constant" justification actually holds |
| `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py` | seed **F4** `:730` + seed **F17** `:728` | **added by this triage.** Both confirmed still open verbatim: `:728` `dasha_consensus_count=0, # U1: … 0 for now`; `:730` `ayanamsha_robustness=3, # default; real value comes from kala_convergence row` — the comment is false, `_load_convergence` never SELECTs it, and the engine turns `3` into a fixed `0.92` multiplier applied to **every** posterior |
| `platform/python-sidecar/services/ph_nimitta/engine.py` | **NEW-PH-1** `:157` + call sites `:557`/`:663` (§6.8) | **added by this triage.** `compute_magnitude` does `ry = float(rarity_years or 1.0)` → `rarity_score = min(1.0, ry/10.0) = 0.1`, and two of three anchor-construction paths call `compute_magnitude(None, es)`, so `combined = 0.1 × es ≤ 0.1 < 0.20` **always** returns `'minor'`. Explains the live 142/142 `magnitude_expected='minor'`. **No conflict:** the P0-11 fix to this file is already merged (#837) |

**Cross-arc caution:** the fix ledger warns of file-adjacency risk between `ph_nimitta.py` (this
lane) and PARISHODHANA's work on the same subsystem. `services/ph_nimitta/engine.py` is **already
fixed** (P0-11, #837) and is **not** in this lane. If PARISHODHANA has live `ph_nimitta.py` work,
that is a §7 cross-arc question for DVA, not a within-swarm conflict.

`rebuild_required: true` → **C1-REBUILD**.

### §4.6 — B-NAR-KA · Kāla writers + domain vocabulary

| File | Findings | Notes |
|---|---|---|
| `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py` | **P1-c** `:226`/`:232` obstruction narration + **the twice-parked stale domain vocabulary** (`finance`/`spiritual` vs canonical `wealth`/`spirituality`) | **TWO defects, one file — fix together, verify separately.** The vocabulary defect is PARKED-HONEST **twice** and can fail a live build. **Close it here.** |
| `platform/python-sidecar/pipeline/orchestrator/writers/ka_kala_darshana.py` | **NEW-KA-1** `:168` `mode_label` mislabels Modes C and D as "independent sweep" (§2.3) | **F27 `:180` is REJECTED (§2.3) — do not fix it.** NEW-KA-1 is the reachable finding that justifies this file |
| `platform/python-sidecar/brahmagyan/kala/l3_snapshot.py` | P2 `:519` | |
| `platform/python-sidecar/brahmagyan/kala/l3_timeline.py` | P2 `:270` | `if "benefic" in pl_nature:` |
| `platform/python-sidecar/brahmagyan/phala/muhurta.py` | P2 `:355` | path under `brahmagyan/phala/`; assigned KA per the queue. **B-NAR-PH must not open it** |
| `platform/python-sidecar/services/gochara_grammar/primitives.py` | P2 `:788` `"bindu_count_resolved": False` | |
| `platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py` | seed **F8** `:234` + seed **F19** `:226` | **added by this triage.** Both confirmed verbatim: `:234` passes composite `f"{md_planet}/{ad_planet}"` into `_build_parva_narrative`, missing `_PLANET_THEMES` and always falling back to `['transformation']` (`:390`/`:397`); `:226` `ad_dominant = … else dominant_class` inherits the parent MD's class, where the PD sibling at `:301` correctly returns `None` |

`rebuild_required: true` → **C1-REBUILD**.

### §4.7 — B-NAR-TS · TypeScript serve layer

| File | Findings | Notes |
|---|---|---|
| `platform-mcp/src/tools/retrieval/kala_temporal.ts` | **P1-d** `:377`/`:380` | `:377` `active_convergences: convergenceWindows.filter(`, `:380` `active_obstructions: darshana?.obstruction_summary` — date-range-scoped not today-scoped + empty-array truthiness |
| `platform-mcp/src/resources/capabilities.ts` | P2 `:72` `## Available Tools (21 total)` | hardcoded count. **Path disambiguated** — NOT `platform/src/lib/providers/capabilities.ts` (a provider-feature interface, unrelated) |
| `platform/src/lib/retrieval/envelope.ts` | P2 `:1416` | **the canonical authored source** |
| `platform-mcp/src/generated/envelope.ts` | mechanical mirror of the above | **GENERATED — DO NOT HAND-EDIT.** Edit the canonical file, then `npm run codegen:envelope` in `platform-mcp/`; `npm run codegen:check` is the CI drift gate. Both files land in **this lane's** PR |
| `platform-mcp/src/resources/vidhi_registry_resource.ts` | P2 `:71` `'~37 versioned retrieval primitives'` | hardcoded count in a description string |
| `platform-mcp/src/server.ts` | P2 `:687` `const REGISTERED_TOOL_COUNT = 88` | **path disambiguated** (only `server.ts` long enough). The constant's own comment already admits it is hand-maintained and non-authoritative. **Note for the lane: `:687` says 88 while `capabilities.ts:72` says 21 — two hardcoded tool counts that disagree with each other and with `tools/list`. One cluster, one fix strategy** |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | P2 `:893` | cited line is a `to_char(pa.window_end, …)` SQL fragment — **line may have drifted; re-derive in-function** |
| `platform-mcp/src/tools/register_p1_ganita.ts` | P2 `:374` **REJECTED (§2.4)** | **Zero edits required.** Retained in the partition solely so the lane knows it is *claimed and closed*, not overlooked. One **optional** §N.6 nicety: `per_yoga[].statement` carries no `single_pass`/`catalog_only` qualifier |
| `platform-mcp/src/tools/registry_bridge.ts` | seed **F11** | **added by this triage.** Line drifted `:3430` → `dignityTier` now at **`:3471`**, the mislabelling clause at **`:3549-3557`** (`t1 === 'strong' ? 'natal strength undercut by navamsha stress' : 'natal weakness tempered by navamsha support'`). Live trigger: Venus D1 `neutral` / D9 `debilitated` narrates as "natal weakness tempered by navamsha support" — labels a *neutral* dignity a weakness **and inverts the direction** (D9 debilitated is a worsening). **Cross-arc:** PARISHODHANA #827/#828 already merged into this file |
| `platform-mcp/src/resources/chart_snapshot.ts` | seed **F24** `:258` | **added by this triage.** Confirmed: `:255` `const labels = ['Maha','Antar','Pratyantar']`, `:258` prints `labels[i]` by array index, ignoring each row's authoritative `level_n` |

`rebuild_required: false` — serve-side, **redeploy only**. Verify by live-probing the changed
narration on the deployed MCP after merge.
**Carve-out reminder:** `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts`
belongs to **B-NAR-MI** (§4.4), not this lane.

### §4.8 — Test-file partition

Same rule. A lane may edit a test file **only** if that file tests exclusively files the lane owns.
Otherwise it creates a **new** lane-prefixed file. No shared narration test file exists today
(`git ls-tree origin/main | grep -iE "test.*(narration|suddha|nar_)"` → empty), so the risk is
purely forward-looking.

| Lane | New test files | Pre-existing test files it may edit |
|---|---|---|
| B-NAR-BO | `test_nar_bo_*.py` | `platform/python-sidecar/tests/l2/test_bo_wp22_empty_shells.py` (fixture `:114` + vocabulary assertion `:144`, per §2.2) |
| B-NAR-GA | `test_nar_ga_*.py` | — |
| B-NAR-MI | `test_nar_mi_*.py` | `platform/python-sidecar/tests/test_mi_darshana.py` (added by #839 — tests `mi_darshana.py` exclusively); `platform/python-sidecar/tests/test_mi_bhavisya_irreplaceable_outcome_guard.py` (tests `mi_bhavisya.py` exclusively) |
| B-NAR-PH | `test_nar_ph_*.py` | — |
| B-NAR-KA | `test_nar_ka_*.py` | — |
| B-NAR-TS | `*_nar_ts.test.ts` | — |

Both pre-existing MI test files were checked to test **only** files B-NAR-MI owns, so they satisfy
the rule. No other lane has a pre-existing test file it may touch.

`platform/python-sidecar/tests/l2/test_b6_eval_harness.py` is **not** assigned to a B-NAR lane — it
is the never-firing gate flagged in §6.4, and belongs to the §N.8 track.

**Migrations:** no B-NAR lane is expected to need one. If one does, the number is allocated by the
**Conductor at merge time** per Conductor manual §5 — never at authoring time.

### §4.9 — Mechanical conflict check

Every file above, sorted, with its owning lane. **42 entries, 42 distinct paths, no path appears
twice.** Per-lane counts: BO 8 · GA 3 · KA 7 · MI 7 · PH 7 · TS 10.

```
B-NAR-BO  platform/python-sidecar/pipeline/orchestrator/writers/bo_bimba.py
B-NAR-BO  platform/python-sidecar/pipeline/orchestrator/writers/bo_cdlm_summary.py
B-NAR-BO  platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py
B-NAR-BO  platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py
B-NAR-BO  platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna.py
B-NAR-BO  platform/python-sidecar/pipeline/orchestrator/writers/bo_sangati.py
B-NAR-BO  platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py
B-NAR-BO  platform/python-sidecar/tests/l2/test_bo_wp22_empty_shells.py
B-NAR-GA  platform/python-sidecar/ga_writers/ga_sade_sati_writer.py
B-NAR-GA  platform/python-sidecar/ga_writers/ga_sensitive_writer.py
B-NAR-GA  platform/python-sidecar/ga_writers/gates.py
B-NAR-KA  platform/python-sidecar/brahmagyan/kala/l3_snapshot.py
B-NAR-KA  platform/python-sidecar/brahmagyan/kala/l3_timeline.py
B-NAR-KA  platform/python-sidecar/brahmagyan/phala/muhurta.py
B-NAR-KA  platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py
B-NAR-KA  platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py
B-NAR-KA  platform/python-sidecar/pipeline/orchestrator/writers/ka_kala_darshana.py
B-NAR-KA  platform/python-sidecar/services/gochara_grammar/primitives.py
B-NAR-MI  platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py
B-NAR-MI  platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py
B-NAR-MI  platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py
B-NAR-MI  platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py
B-NAR-MI  platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py
B-NAR-MI  platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py
B-NAR-MI  platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts
B-NAR-PH  platform/python-sidecar/brahmagyan/mimamsa/answer_quality.py
B-NAR-PH  platform/python-sidecar/brahmagyan/phala/l4_anchors.py
B-NAR-PH  platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py
B-NAR-PH  platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py
B-NAR-PH  platform/python-sidecar/services/ph_nimitta/engine.py
B-NAR-PH  platform/python-sidecar/services/ph_rectification/engine.py
B-NAR-PH  platform/python-sidecar/services/ph_sodhana/engine.py
B-NAR-TS  platform-mcp/src/generated/envelope.ts
B-NAR-TS  platform-mcp/src/resources/capabilities.ts
B-NAR-TS  platform-mcp/src/resources/chart_snapshot.ts
B-NAR-TS  platform-mcp/src/resources/vidhi_registry_resource.ts
B-NAR-TS  platform-mcp/src/server.ts
B-NAR-TS  platform-mcp/src/tools/register_p1_ganita.ts
B-NAR-TS  platform-mcp/src/tools/register_p1_synthesis.ts
B-NAR-TS  platform-mcp/src/tools/registry_bridge.ts
B-NAR-TS  platform-mcp/src/tools/retrieval/kala_temporal.ts
B-NAR-TS  platform/src/lib/retrieval/envelope.ts
```

Also checked against the **other** SAMĀPTI lanes' declared scopes: `B-N8-FIX`
(`bo_pramana_mapa.py`, `ga_nakshatra.py`, `bo_chart_gestalt.py`), `B-N8-SWEEPFIX`
(`pipeline/orchestrator/{runner,staleness,dag_edge_guard,kala_derivation_completeness_guard,service_probes}.py`),
`B-COCKPIT-INCOMPLETE` (`src/lib/build/plan.ts`, `src/app/api/cockpit/**`, `src/components/**`),
`B-MIGGUARD`, `B-MIG474-COMMENT`. **The only intersection anywhere was `ga_nakshatra.py`, resolved in
§4.3.**

---

## §5 — Findings NOT in any B-NAR lane

| Finding | Disposition | Owner |
|---|---|---|
| SV-3, SV-4, P1-e | **VERIFIED-FIXED** (§1) | closed |
| `mi_darshana.py:159` | **VERIFIED-FIXED** (§1) | closed |
| **P1-a** `bo_pramana_mapa.py:224/228/262/278` | routed to T4 — §N.8, not narration. Confirmed present verbatim: `:224` `lel_zero_leak = trap1_count == 0`, `:228` `pillars_pass = msr_count > 0`, `:262` `"divergent_flagged_count": 0`, `:278` `"trap2_narration_leak_count": 0` | **B-N8-FIX** |
| `ga_nakshatra.py:87` **and `:289`** | §N.8 + P2 rider, whole file | **B-N8-FIX** (§4.3) |
| `bo_chart_gestalt.py:210` | verdict stored in a writer whose docstring bans it | **B-N8-FIX** |
| seed **F27** `ka_kala_darshana.py:180` | **REJECTED — unreachable** (§2.3) | terminal; no lane |
| `bo_laksana_rerank` `writer_timeout_seconds=600` | **NOT-APPLICABLE** to narration — self-healed by the orchestrator's `RR-fix` reconciliation. Record, do not chase | terminal; no lane |
| **SV-6 / SV-7** | **retired as identifiers** per brief §6.6, replaced by named findings | terminal |
| Cross-layer L4-anchor ⇄ L2-MSR ⇄ phaladesa **domain-vocabulary reconciliation** | **costed spec, out of scope** — the shared root cause of F25 (§2.1) and F18 (§3) | §6.3 |

---

## §6 — Residuals

### §6.1 — The describing census is LOST (highest-impact residual)

`SUDDHA_VACA_FIX_LEDGER`'s frontmatter names `NARRATION_SURFACE_CENSUS_v1_0.md` (Wave 1, workflow
run `wf_a58675cc-700`) as the source for every "New CONFIRMED" / "New PLAUSIBLE" finding. **It does
not exist.**

```
$ for b in $(git for-each-ref --format='%(refname)' refs/remotes refs/heads); do
    git ls-tree -r --name-only $b | grep -i NARRATION_SURFACE_CENSUS; done
(no output — not in any ref)
$ git log --all --diff-filter=A --name-only | grep -i NARRATION_SURFACE_CENSUS
(no output — never committed)
$ find /Users/Dev -maxdepth 8 -iname '*NARRATION_SURFACE_CENSUS*'
(no output — not on disk)
```

**Consequence:** for ~24 "New CONFIRMED" P2 items, the *only* surviving information is the bare
`file:line`. Every B-NAR lane must **re-derive** its findings from the pointer, and cannot rely on a
prior description. This is why §2's auditors were told to reconstruct before attacking — and it is
why two of them found the *real* defect to be materially different from, or larger than, the
pointer implied (§2.2, §2.3).

Second-order residual: the seed audit itself
(`00_ARCHITECTURE/narration_audit/NARRATION_DETERMINISM_AUDIT_v1_0.md`, F1–F29, the source for
F4/F8/F11/F17/F18/F19/F20/F21/F24/F25/F27/F28) is **UNTRACKED** in the working tree and is one
`git clean` from sharing the census's fate. **Recommend A1-PRESERVE or a docs lane commit it
verbatim.** This lane did not commit it — it is not in scope, and it is not this lane's file.

### §6.2 — Eight brief-named seed findings had no lane

Brief §6.4 lists "plus seed F4/F8/F11/F17/F19/F20/F21/F24" in the P2 band, but **none of the eight
appears in any B-NAR-* `scope:` list in the queue.** All eight were verified still present on
`origin/main` and are now assigned (§4.1 F20/F21, §4.5 F4/F17, §4.6 F8/F19, §4.7 F11/F24). Without
this triage step they would have been silently dropped.

### §6.3 — The cross-layer domain-vocabulary drift (costed spec, not a lane)

Three subsystems disagree on their domain vocabularies:

| Source | Vocabulary |
|---|---|
| `bodha_msr_signals.domains_affected_array` | `career, character, health, relationship, spirituality, wealth` |
| `phala_anchors.domain` | `career, character, general, health, relationship, spirituality, transition` |
| `_ALL_DOMAINS` (phaladesa engine) | `career, wealth, health, relationship, spirituality, character, transition` |

No two agree. `wealth` exists in MSR but is never an anchor domain; `transition`/`general` exist as
anchor domains but never in MSR; `general` exists in the phaladesa *label map* but is never emitted.
This single drift is the root cause of **F25** (§2.1), **F18** (§3), and the `ka_bhavishya_lekha`
stale-vocabulary defect in §4.6. **Recommend a costed spec, not a fix in any B-NAR lane** — the
in-lane fixes are the honest local mitigations (flag the fallback; add the missing label), and each
lane is instructed not to attempt the reconciliation.

### §6.4 — A detector that exists but never fires

`platform/python-sidecar/tests/l2/test_b6_eval_harness.py:468-481` requires **< 10%** of
`bodha_cdlm_cells` to be missing `domain_relationship_class`. Production is at **100%** (§2.2). The
gate is DB-gated and evidently not running in CI — an unearned green in the §N.8 sense. **Routed to
A7-N8-AUDIT / B-N8-LINT**, not to a B-NAR lane.

### §6.5 — Four seed PLAUSIBLE findings the ledger dropped entirely

The ledger's P2 seed list carries F20/F21/F24 but silently omits **F22, F23, F26, F29**. All four
were verified still present at their cited lines on `origin/main`:

| Seed | `file:line` | Line on `origin/main` | Owning lane if adopted |
|---|---|---|---|
| F22 | `ka_bhavishya_lekha.py:234` | `f"{tier_desc}. Effective convergence: {eff_score:.2f}. "` | B-NAR-KA (already owns the file) |
| F23 | `ka_bhavishya_lekha.py:208` | `deny = f"No observable {domain} event within ±21 days of {peak_str} despite favorable circumstances"` | B-NAR-KA (already owns the file) |
| F26 | `ph_nimitta.py:428` | `event_class_by_domain.setdefault(r['domain'], str(r['event_class_id']))` | B-NAR-PH (already owns the file) |
| F29 | `chart_snapshot.ts:98` | `const val = row.value_text ?? (row.value_number !== null ? String(row.value_number) : '?')` | B-NAR-TS (already owns the file) |

Each lands in a file its lane **already owns**, so adopting them adds **zero** conflict risk.
Offered as **optional riders**: verify adversarially, then fix or REJECT. Flagged rather than
silently inherited — the ledger's omission may have been deliberate.

### §6.6 — Ledger/brief disagreement on PLAUSIBLE membership

The ledger marks seed **F20/F21/F24** PLAUSIBLE; brief §6.4 folds them into the P2 set and names a
*different* 7 as PLAUSIBLE. This triage carried the **brief's** 7 (they are what the queue's scope
names) and additionally instructs the lanes owning F20/F21/F24 to **verify before fixing** — so
neither reading loses a check. No item was silently promoted from PLAUSIBLE to CONFIRMED.

### §6.7 — Not conclusively triaged

- `register_p1_synthesis.ts:893` — the cited line is a `to_char(pa.window_end, …)` SQL fragment with
  no evident narration defect. **Line number probably drifted.** Not resolved here; B-NAR-TS must
  re-derive in-function and may legitimately return REJECTED.
- `bo_bimba.py:253` (`g = _parse_graha_from_signal(cfg)`) and `l3_snapshot.py:519` (`summary += (`)
  are plausible-looking but were not individually re-derived — they are CONFIRMED-per-ledger and
  their owning lanes must re-derive from the pointer per §6.1.
- **SV-4 applied-state** — code closed, production application unverifiable from a worktree
  (§1.1). Belongs to SAṂGATI §8.5.
- **`ga_sensitive_writer.py:2677` live-vs-dormant** — the §2.5 verdict is CONFIRMED either way, but
  whether the fabricated `SAT+6°`/`SAT+8°` value is *shipping today* or only *reachable* was left
  unsettled when the auditor's DB tunnel dropped. The settling query is written out in §2.5 for the
  B-NAR-GA owner to run first. Urgency depends on the answer; the verdict does not.

### §6.8 — NEW-PH-1: `compute_magnitude` can only ever return `'minor'`

Found while refuting `mi_bhavisya.py:103` (§2.7), and materially larger than the item that surfaced
it. `platform/python-sidecar/services/ph_nimitta/engine.py:157`:

```python
ry = float(rarity_years or 1.0)
es = float(effective_score or 0.5)
rarity_score = min(1.0, ry / 10.0)
```

Two of the three anchor-construction paths (`:557`, `:663`) call `compute_magnitude(None, es)`, so
`ry = 1.0` → `rarity_score = 0.1`, and the combined score `0.1 × es` cannot exceed `0.1`, which is
below the `0.20` `'moderate'` threshold. **The function is structurally incapable of returning
anything but `'minor'` on those paths.**

Live corroboration: **286/286 `phala_anchors` carry `magnitude`, and all 142 canonical
`mimamsa_predictions` read `magnitude_expected = 'minor'` — zero `'moderate'`.** This is the real
reason seed F28's `'moderate'` default never fires: not because the engine reliably assigns a
*correct* magnitude, but because it assigns a *constant* one. F28's disposition
("trigger not reproduced") is therefore right for the wrong reason, and that is worth recording.

Assigned to **B-NAR-PH** (§4.5). The file is not claimed by any other lane and its P0-11 fix is
already merged (#837), so this adds no conflict. Flagged as a **D3_HARDCODED_DRIFT with a
verdict-flattening consequence** — arguably above P2, and the B-NAR-PH owner should say so if it
agrees.

---

*End of SAMAPTI_NARRATION_TRIAGE_AND_PARTITION_v1_0.md — lane A8-NAR-TRIAGE. This lane fixed
nothing. Baseline `origin/main @ cdb6fc3b`.*
