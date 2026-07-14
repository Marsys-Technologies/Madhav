---
artifact: CLAUDECODE_BRIEF_D1_5_JUDGMENT_SUBSTRATE_REWORK
type: CLAUDECODE_BRIEF (governing scope for one execution session)
version: 1.0
status: ACTIVE
authored_by: Cowork (Opus), native-ratified 2026-07-14
authority: >
  Per CLAUDE.md §C item 0, the may_touch / must_not_touch declarations in §4 OVERRIDE all other
  scope guidance for the duration of this session. ACTIVE is the standing authorization to
  commit/merge/deploy/rebuild WITHIN §4 scope. Set status: COMPLETE only per §5.
supersedes: >
  CLAUDECODE_BRIEF_LLM_CONSUMPTION_REMEDIATION v1.0 (2026-07-12) — that program closed with the
  Night-1 D-1 campaign (merge 4bebb622). Preserved in git history. Do not execute it.
governing_gate: POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md §K.2 (12 MCP assertions)
native_rulings:
  - DR-1 (2026-07-14) — dual-lordship valence: TRIKOṆA PURIFIES. Register §K.1.
  - SCOPE (2026-07-14) — D-1.5 rework ONLY. D-2 (Vidhi Engine) is NOT authorized this session.
---

# D-1.5 — Judgment-Substrate Rework

## §0 — Why this session exists

D-1 shipped: merge `4bebb622`, deployed, both charts rebuilt. **Build health was verified and is
genuinely good.** Judgment health was not verified — and it did not move.

Re-verification against the **live deployed MCP** (build `b97b6eb0`, 2026-07-14):

| D-1 claimed delivered | Live reality on the consuming surface |
|---|---|
| L2 `ga_vichara` — functional-lordship valence | **Shipped and INVERTED.** 9L Jupiter → H2 = `malefic`. A `trikona_link` = `malefic`. |
| L3 detector registry — Dhana / Rāja / NBRY / Budha-Āditya / Sarasvatī / Vipareeta | **Unreachable.** `yoga_fires` empty. `bearing_yogas: []`. The tool's own description still says these *"will never fire from this tool regardless of chart data."* |
| L4 MSR elevation — subject-bearing headlines | Headline still `"bhava significance link: lord aspects = neutral_link"`. No graha. No house. |
| L5 density — new `ganita_vichara_get` face | **Not on the MCP surface.** Not discoverable, not callable. |
| CR-33 yoga-narrator contradiction (absorbed into D-1) | **Reproduces verbatim.** Śaśa denied while its own row sits in the same response page. |

**482012f1 wealth verdict: `convergent_moderate`, composite `1.15` — byte-identical to pre-campaign.**

**What DID land** (verified live, do not re-do): **CR-55** weakest_graha = Venus, self-citing · **CR-81**
class_prior live · **CR-82** tier ceiling lifted (supporting 95.7→88.1%, chart_defining 0.2→1.5%) ·
**CR-87** natal constants de-hardcoded (code-fixed; *not independently verified — see W6*).

## §1 — The governing lesson (CR-96)

Night-1's hard-won gate was *"verify against the database, not agent reports."* It worked — it caught real
bugs before they shipped.

**This session's gate is one level up: verify against the CONSUMING SURFACE, not the database.**

`ga_vichara` has 5,497 rows in `chart_facts` and no serving face. The yoga detectors are merged to `main`
and produce zero `yoga_fires`. **A row that no MCP face serves does not exist as far as a reading is
concerned.** Three of D-1's four failures would each have been caught pre-merge by a single MCP call.

**Therefore: every acceptance criterion in this brief is an MCP tool-call assertion. None is a SQL
assertion. Do not report a work item complete on the basis of a DB query.**

---

## §2 — Work items

### W1 — Fix `compute_valence` precedence · CR-90 · CRIT · blocks D-2

`platform/python-sidecar/ga_writers/ga_vichara_writer.py`

Line **251** declares `_PRECEDENCE: "trikona > dusthana"`. Lines **285-314** evaluate the
`dusthana_lord → wealth → strong_malefic` cell (rule 1) **before** the `trikona_lord → wealth → benefic`
cell (rule 2). Any graha owning both a trikoṇa and a dusthāna therefore hits the malefic rule first.

Live damage on 482012f1: 9L Jupiter (own sign, co-owns 12) aspecting H2 → `malefic` — the chart's single
most benefic wealth link, marked harmful. 3L Mercury (co-owns 6) on a `trikona_link` → `malefic`.

**Native ruling DR-1: TRIKOṆA PURIFIES.** Trikoṇa ownership dominates. A graha owning a trikoṇa is benefic
toward the wealth houses even where it co-owns a dusthāna. `strong_malefic` is reserved for grahas with
**no trikoṇa ownership at all**.

**This is not new doctrine.** The doctrine was already correct in the file; the execution inverted it.
Reorder the evaluation to honor the declared precedence.

*Out of scope:* kendrādhipati-doṣa, the full per-lagna functional-benefic scheme. Considered and declined
as too large for D-1.5; revisit at D-2.

### W2 — One valence engine, not two · CR-91 · CRIT · blocks D-2

`ga_vichara`'s valence pass iterates **lord-LINK** signals only (`bhava_significance_link`,
`lord_aspects_lord`). It never fires on the raw `aspect_parashari_given` population.

Consequence: **the CR-54 type specimen — Mars (8L) 8th aspect on H2 at strength 1.00, the chart's core
wealth-destruction mechanism — is still `valence: neutral`, `valence_source: keyword_heuristic_v1`.** The
served surface now carries two engines that disagree, and the most important row is covered by neither.

Extend the valence pass to the raw-aspect population — dusthāna-lord aspects on the wealth/lagna axis
especially. Retire `keyword_heuristic_v1` for lord and aspect signals once `ga_vichara_v1` covers them.

### W3 — Wire the L3 detectors to the serving faces · CR-92 / CR-56 / CR-59 · CRIT · blocks D-2

**This is the campaign's #1 stated priority, reported as delivered, and not present.**

**First, diagnose — do not assume.** Determine whether the D-1 detectors populated at all:
- Rows written → **serving-wiring gap**: connect them to `ganita_yogas_get.yoga_fires` and
  `judgment_query.bearing_yogas`.
- Nothing written → **writer bug**: root-cause it.

Report which it was.

**In the same commit, update the `ganita_yogas_get` tool description.** It currently declares that Dhana
Yoga, Neecha Bhanga and the house-lord Rāja family *"are NOT evaluated by any live path in this build …
they will never fire from this tool regardless of chart data."* A description that declares a gap the code
has closed is itself a defect — the consuming LLM reads the description.

Target detections on 482012f1 (all hand-verified from L1 longitudes; all currently dark):

- **Dhana Yoga** — 2L Venus + 9L Jupiter conjunct in the 9th, in Jupiter's own sign (Sagittarius).
- **Budha-Āditya** — Sun 22°11′ + Mercury 1°09′ in H10; 21° apart → **non-combust → fires**.
- **Śaśa Yoga** — Saturn exalted in the 7th (kendra). *Already present in `yoga_label`; the narrator denies it.*
- **Per-varga NBRY** — Saturn (D9 Aries: exaltation-lord Sun in D9 lagna Cancer, a kendra; Saturn itself in
  a D9 kendra) and Venus (D9 Virgo: dispositor Mercury in D9 Capricorn = 7th = kendra).
  **Record grounds only — do not rule.** CR-23 remains deferred by standing native decision.

### W4 — Yoga verdict-narrator self-contradiction · CR-93 / CR-33 · HIGH

`ganita_yogas_get(v3)` returns `"No Pancha Mahapurusha yoga is formed in this chart"` and
`"Sasa … is not formed … per its absence from the yoga_label rows served"` — **while the `sasa` row
(fact `37759e67555cd771`, group `pancha_mahapurusha`) is in that same served page.** Śaśa is genuinely
formed on this chart.

Count the served `yoga_label` / `yoga_fires` rows in the verdict builder. Never assert "not formed" from
absence-in-page.

CR-33 was filed 2026-07-13, absorbed into D-1, and is unchanged. **Verify this fix against the tool
response, not the writer.**

### W5 — Honesty flags + missing face · CR-94 / CR-95 · MED-HIGH

- `judgment_flags: ["zero_rows_returned"]` is served on a **32-row** response; `coverage.served: 0`;
  `pagination.total: null`. Wire all three to the real served count. These flags are exactly what a
  consuming LLM is instructed to trust when judging whether a payload is meaningful.
- **`ganita_vichara_get` is absent from the MCP surface.** Register and expose the face — or strike it from
  the D-1 close-report's delivered list. Either is acceptable. The current state (claimed delivered, not
  callable) is not.

### W6 — Verify CR-87 cross-chart · verification, not build

De-hardcoding one native's natal constants out of shared convergence code was the most important
correctness fix of Night-1 — and it has **not been independently verified**. Prove it: **Abhinandan
(`1c826d5a`) must now score differently from Abhisek (`482012f1`)** on the tara-bala, sade-sati and
panchanga currents. Add a permanent regression guard asserting this.

---

## §3 — Acceptance gate

Authoritative: register **§K.2**. All twelve are **MCP calls against the deployed connector**, on 482012f1
after rebuild.

**Valence** — 1. no `trikona_link` carries malefic/strong_malefic · 2. 9L Jupiter → H2 is `benefic`,
`valence_source='ga_vichara_v1'` · 3. Mars(8L) 8th-aspect-on-H2 is `strong_malefic`, `ga_vichara_v1` ·
4. zero `keyword_heuristic_v1` on lord/aspect signals · 5. unit: `{trikona_lord, dusthana_lord}` aspecting
a wealth house → benefic (DR-1).

**Detectors** — 6. `yoga_fires` non-empty · 7. `judgment_query(wealth).bearing_yogas` contains **Dhana
Yoga** naming Venus + Jupiter · 8. `judgment_query(career).bearing_yogas` contains **Budha-Āditya** ·
9. Śaśa reported **FORMED** · 10. per-varga NBRY served for Saturn (D9 Aries) + Venus (D9 Virgo) with
grounds recorded.

**Honesty** — 11. tool description no longer declares the gap; no `zero_rows_returned` on a non-empty page;
`coverage.served` matches row count · 12. `ganita_vichara_get` discoverable and callable.

### The proof that actually matters

Re-run the 482012f1 **wealth reading through the tools alone**. The verdict must **move off
`convergent_moderate` / composite `1.15`** — the value it has held byte-identically across this entire
campaign — and `bearing_yogas` must carry the Dhana Yoga.

**If the number does not move, D-1.5 did not happen, regardless of what the build reports.**

---

## §4 — Scope

**may_touch**
- `platform/python-sidecar/ga_writers/ga_vichara_writer.py`
- `platform/python-sidecar/ga_writers/` — yoga/NBRY detector registry + its serving wiring
- `platform/python-sidecar/bodha_writers/bo_laksana.py` — valence-source fallback retirement only
- MCP serving faces for `ganita_yogas_get`, `judgment_query`, `ganita_vichara_get` — **including tool descriptions**
- tests + fixtures for all of the above
- `00_ARCHITECTURE/llm_consumption_audit/POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` — status updates only

**must_not_touch**
- The **FROZEN orchestrator contract** (`WriterBase`, `@register`, `ctx.db_conn`) — CLAUDE.md §N.2.
  If a writer seems to need a contract change → **STOP and raise with the native.**
- **Anything in D-2 / D-3 / D-4 scope** — Vidhi Engine, CGM mechanism object, Kāla Taraṅga, Three-Lock
  convergence, calibration ignition. **D-2 is NOT authorized this session** (native ruling, 2026-07-14).
- `ka_*` convergence internals beyond the CR-87 verification in W6.
- The `dosha_label` surface (CR-72/73/74). Real, and arguably the true peer of the valence fix — but
  **not this session.**
- **CR-23** (NBRY doctrine ruling) — deferred by standing native decision. Detectors record grounds; they
  do not rule.

---

## §5 — Session close

Emit the SESSION_CLOSE artifact per CLAUDE.md §H.

Set `status: COMPLETE` in this file's frontmatter **only when all twelve §3 assertions are GREEN against
the deployed connector** — not when the code merges, not when the DB has rows, not when an agent reports
success.

If an assertion cannot be made green, say so plainly and leave `status: ACTIVE`. **A half-passed gate
reported as complete is the exact failure this session exists to correct.**
