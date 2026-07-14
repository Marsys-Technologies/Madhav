---
artifact: NIGHT1_LANE3_DETECTOR_REGISTRY
type: IMPLEMENTATION BRIEF (Sonnet-executable, self-contained)
version: 1.0
status: READY
campaign: Doctrine Campaign D-1 / Night-1
lane: L3 — detector-registry extension (house-lord yogas + per-varga NBRY + dosha cancellation checks)
depends_on_lanes: LANE1 (dosha-family work touches the modularized ga_structural — merge after Lane 1), LANE2 (merged — valence/lordship helpers may be reused; hard ordering per CONDUCTOR)
register_rows: CR-56 (CRIT), CR-22/CR-35 (confirmed by CR-56), CR-59 (CRIT, escalated CR-34), CR-72 (CRIT), CR-73, CR-74, CR-43 (dosha half), CR-23 (governance-deferred — grounds stored, not adjudicated)
design_ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §2 (detector registry plane), §4 (detector families paragraph)
---

# LANE 3 — Detector registry: house-lord yoga family, per-varga NBRY, dosha cancellation-checks

## 0. Why (design §4, quoted)

> Detector families (dhana / raja / Budha-Āditya / Sarasvatī / Lakṣmī / Vipareeta — CR-56) ship as registry modules with mandatory cancellation-checks (fixes the CR-72/73 "no negative-condition check" class at the doctrine level).

And §2's disposition: "Detector families (dhana/raja/NBRY-per-varga…) → **Registered modules inside the existing yoga writer** — asset unchanged, internals become plugins."

CR-56 is the register's #1 acharya-grade blocker ("Three consecutive readings on two charts have now had to hand-derive the yoga layer").

## 1. Exact scope — three deliverables, one asset

Asset **`ga_yoga` — unchanged asset_id, unchanged DAG position**. Files:
- `platform/python-sidecar/ga_writers/ga_yoga_writer.py` (detectors + registry)
- possibly new sibling modules `ga_writers/ga_yoga_detectors/*.py` if the file grows unwieldy (keep `ga_yoga_writer` as the import face)
- `platform/python-sidecar/ga_writers/ga_structural_writer.py` (or its Lane-1 package) — **dosha cancellation gate only** (§1.3)
- one migration for `brahma_yoga_catalog` seed rows (§5)

### 1.0 Verified current state (read before writing code)

- Fired yogas land in **`ga_yoga_firings`** via `build_ga_yoga_substep` (per-ayanamsha), which loads `brahma_yoga_catalog` and evaluates `formation_rule_jsonb` through `_evaluate_yoga`/`_evaluate_catalog_rule`. Catalog currently covers Nabhasa/PMP/Chandra-adhi families only (CR-35).
- A **registry precedent already exists**: the Y-5 generic bhanga evaluator — registered handlers like `_bhanga_neecha_handler` (ga_yoga_writer.py ~:1805) keyed by yoga id. Extend this pattern; do not invent a competing one.
- **NBRY engine already goes beyond D1** (this postdates the register's CR-34 evidence): `detect_neecha_bhanga(positions, varga=…)` (:1717) is varga-generic, and `evaluate_nbry(d1_positions, d9_positions)` (:1765) ALREADY runs D1 + D9 (`findings.extend(detect_neecha_bhanga(d9_positions, varga="D9"))`), loading D9 via `_load_d9_positions` (:1889, honest degradation to D1-only if D9 unavailable). Rules 1–4 fire; rule 5 floored per B.10.
- Separately, `ga_structural_writer._build_dosha_rows` (:2043) + `_build_yoga_rows` (:1933) emit **`dosha_label` / `yoga_label`** rows into `chart_facts` by evaluating catalog `formation_rule_jsonb` via `_evaluate_catalog_rule` (:4766) — which returns `True, "requires_pass"` for rule shapes it can't fully evaluate. Those are the CR-72 decorative stubs (all 22 dosha labels on 482012f1 share ONE constituent fact and "fire" on requires_pass).

### 1.1 Deliverable A — house-lord yoga detector family (CR-56)

Add a **detector registry** to the yoga writer: `YOGA_DETECTORS: dict[str, DetectorSpec]` where each entry is a module-level, pure, unit-testable detector:

```python
@dataclass
class DetectorSpec:
    yoga_id: str                    # matches brahma_yoga_catalog.canonical_id
    detect: Callable[..., DetectorFinding | None]   # (chart_state) -> finding or None
    cancellation: Callable[..., CancellationVerdict]  # MANDATORY — even if verdict is "no classical cancellation rule; NULL"
    citation_ref: str; citation_human: str
```

`build_ga_yoga_substep` runs the registry AFTER the catalog pass; detector findings write `ga_yoga_firings` rows exactly like catalog firings (same columns, same `constituent_bala_v1` strength rule — quoted from the writer's own rails: "No fabricated strength … normalized shadbala of constituent grahas; never a per-yoga invented formula, B.10"; `bhanga_active` NULL-with-`bhanga_na_reason` where no classical cancellation rule is implemented).

Detectors to ship (each with formation rule + cancellation check + citation + fixture test; house lordships derived per-lagna from the sign-lord table, positions from the same chart-state the writer already loads):

| Detector | Formation (v1 rule to encode) | Mandatory cancellation/negative check |
|---|---|---|
| `dhana_yoga_house_lords` | any pairing among lords of {1,2,5,9,11} by (a) conjunction, (b) mutual aspect, (c) parivartana — where the pair includes 2L or 11L, and the meeting house is not 6/8/12 | either lord debilitated-without-stored-NBRY, or combust (from `graha_special_state_rollup` facts) → yoga fires with `bhanga_active=true` + reason, or is demoted — never silently dropped, never silently served at full strength |
| `raja_yoga_kendra_trikona` | kendra-lord × trikona-lord conjunction/mutual-aspect/parivartana | same debility/combustion check; dusthana meeting-house check |
| `budha_aditya` | Sun + Mercury in one house | Mercury combust within its combustion orb → CANCELLED (this is the classical negative condition; 482012f1: 21° apart → non-combust → FIRES) |
| `sarasvati_yoga` | Jupiter, Venus, Mercury each in kendra/trikona/2nd, Jupiter in own/exalted/friendly sign | any of the three debilitated/combust |
| `lakshmi_yoga` | 9L in own/exaltation in kendra/trikona + Venus strong (own/exalted, not combust) | Venus debilitated/combust |
| `vipareeta_raja_yoga` | a dusthana lord (6/8/12) placed in a dusthana (classical harsha/sarala/vimala mapping) | the dusthana lord conjunct/aspected by a non-dusthana lord (classical dilution), or exalted-in-dusthana nuance — record which ground checked |

Formation rules: seed each as a `brahma_yoga_catalog` row (migration §5) so citations/name flow the existing path, with `formation_rule_jsonb` carrying `{"detector": "<yoga_id>"}` — the writer routes catalog rows with a `detector` key to the registry instead of `_evaluate_catalog_rule`. This keeps ONE catalog (no parallel yoga universe) while making the rule real instead of `requires_pass`.

### 1.2 Deliverable B — per-varga NBRY, grounds stored per verdict (CR-59, CR-34, CR-23-deferred)

1. **Verify-first task**: the engine already evaluates D9. Reproduce the CR-59 symptom on current code: run `evaluate_nbry` with 482012f1's stored D1+D9 positions (facts cited in CR-59: `f764a762` D9 Saturn debilitated; `4814c825` D9 Sun Cancer H1; `856875fd` D9 Mercury Capricorn H7). Expected per CR-59: Saturn-D9 NBRY fires (exaltation-lord Sun in D9 kendra-from-lagna + Saturn itself in D9 kendra) and Venus-D9 NBRY fires (dispositor Mercury in D9 kendra). If current code already fires both, the residual defect is **storage/serving vintage** — document that in your lane report and proceed to (2)–(3); if it does not fire, fix the rule functions (`nbry_rule_1..4`) for the varga-scoped call path.
2. **Grounds-checked-per-verdict storage** (the CR-59 fix direction: "store grounds-checked per verdict", and the CR-23 input): every NBRY evaluation — fired OR not — must persist WHICH grounds were checked and each ground's boolean, e.g. `{"planet":"venus","varga":"D9","grounds":[{"rule_id":"nbry_rule_1_dispositor_kendra","checked":true,"fired":true,"detail":…}, …]}`. Put it in the `ga_yoga_firings` row's jsonb for fired cases; for non-fired debilitated grahas emit a `chart_facts`-side or firings-side "evaluated, not fired" record ONLY if a natural home exists — otherwise attach the grounds ledger of non-fired evaluations to the writer's `WriterResult.notes` path AND to the fired rows' jsonb (minimum bar: any NBRY verdict served downstream must be traceable to its checked grounds). **Do NOT adjudicate the CR-23 doctrine disagreement** (detector vs classical two-ground derivation on Jupiter) — that is DEFERRED-EXPLICIT for a native ruling; your job is to make the grounds visible so the ruling can happen.
3. **D9 minimum satisfied**; extending to further vargas (D10, D2…) is allowed only if it costs nothing structurally (the function is already varga-generic) — do not chase exhaustive varga coverage tonight.

### 1.3 Deliverable C — dosha cancellation-checks + label-stub gating (CR-72/73/74, CR-43-dosha-half)

Doctrine rule this deliverable installs (register CR-73): **no dosha may fire without its negative/cancelling condition being evaluated.**

In `_build_dosha_rows` (Lane-1's modularized home — coordinate: this is the ONE shared file section between Lanes 1 and 3; Lane 1 moves it verbatim, Lane 3 then modifies it — never edit it in both lanes):

1. **Kill the decorative path**: a `dosha_label` row may only be emitted when `_evaluate_catalog_rule` returns a REAL evaluation. When it returns `(True, "requires_pass")` — i.e. the rule shape wasn't actually evaluated against this chart — the row must NOT be written as a firing. Options (pick 1): drop the row, or write it with an explicit `value_jsonb: {"catalog_only": true, "fires": null}` so serving can gate it (CR-43's "separate catalog rows from fired rows"). Same treatment for `yoga_label` rows on the requires_pass path (CR-43's yoga half).
2. **Cancellation registry**: `DOSHA_CANCELLATIONS: dict[str, Callable]` keyed by dosha canonical_id. A dosha that has a registered cancellation check runs it before emitting; if the cancelling condition holds, the dosha does not fire (emit an "evaluated, cancelled-by" jsonb record instead). Ship at minimum:
   - `kemadruma`: cancelled by any of — graha (non-Sun) in 2nd-from-Moon, 12th-from-Moon (Anapha), both (Durudhara), or graha in kendra from Moon/lagna (per the classical exception list; cite each). **482012f1 fixture: Mercury in 12th-from-Moon → Anapha fires → Kemadruma must NOT fire** (CR-73's proof case, facts eb51fdc4 vs 0e838f88).
   - `daridra`: not fired when 11L exalted / 2L-9L dhana structure fires (CR-73's second specimen: "daridra fires despite an exalted 11L, own-sign dhana-kāraka, and 2L in the 9th"). Encode the cancelling condition from the classical daridra definition (11L/2L strength), cite it.
   - `kala_sarpa`: the genuinely-computed `kala_sarpa_per_varga` fact is the ONLY authority (CR-74: D1 verdict `fires:false` on 482012f1 — Mars+Saturn in H7 break the hemming). The label row must agree with the computed per-varga fact or not exist. Do not build a second KS detector — wire the label to the existing computed fact.
   - Every other dosha in the catalog without an implemented cancellation check: keep the honest-NULL pattern the yoga writer already uses (`bhanga_na_reason`-equivalent: `cancellation_na_reason: "no classical cancellation rule implemented"`) — visible honesty, not silent firing. Combined with (1), an unevaluable dosha now neither fires nor pretends.

## 2. Contract constraints

Asset contract unchanged (`ga_yoga` stays a heavy per-ayanamsha writer registered in `pipeline/orchestrator/writers/ga_yoga.py`; `ga_structural` per Lane 1). All §N.2 rails hold: `ctx.db_conn`, never commit, no `asset_throughput`, delete-then-insert idempotency scoped `(chart_id, ayanamsha_id)`. **No orchestrator edits.** New detector code is deterministic-only (§N.4).

## 3. Migration (§5 of LANE2 has the full convention — same rules)

One migration, next free number after Lane 2's (coordinate via CONDUCTOR; migrations are the one serialized artifact across lanes — if Lane 2 took 367, take 368): seed `brahma_yoga_catalog` rows for the 6 detectors (canonical_id, name_en, classical_citations, `formation_rule_jsonb: {"detector": …}`, `cancellation_conditions` text) with `ON CONFLICT (canonical_id) DO NOTHING` — check the table's actual unique key first. Additive-only; no ALTERs of existing rows. `migration-guard` review required.

## 4. Tests (fixture-first — the register hands you the fixtures)

Pure-function tests with hand-built position dicts (the NBRY tests in the repo show the shape):
- Dhana: Venus-as-2L + Jupiter-as-9L conjunct in H9 own-sign (482012f1 shape, CR-56) → fires; same pair in H8 → does not; 2L combust → fires-with-bhanga or demoted (assert whichever you implemented).
- Budha-Āditya: Sun 22°11′ + Mercury 1°09′ Capricorn (21° apart) → fires non-combust; Mercury at 2° from Sun → cancelled.
- Vipareeta: 8L in 12th → fires; 8L in 12th conjunct 9L → recorded dilution.
- NBRY D9: the CR-59 Saturn + Venus specimens → both fire, grounds arrays present with per-rule booleans.
- Kemadruma×Anapha mutual exclusion (CR-73 specimen); daridra cancellation; kala_sarpa label==computed-fact agreement.
- Registry hygiene: every `YOGA_DETECTORS` entry has a non-None `cancellation` callable; every detector's catalog row exists (test reads the migration seed list).

## 5. Acceptance criteria

- [ ] On 482012f1 (dev-DB writer run or CONDUCTOR rebuild): `ga_yoga_firings` contains fired rows for `dhana_yoga_house_lords`, `budha_aditya`, `sarasvati_yoga` (grounds per CR-71: "Saraswati structure fires"), NBRY-D9 for Saturn and Venus with grounds jsonb; and `bearing_yogas`-class surfaces stop being derivable-empty at the data layer (CR-3's join is serving-side, but the rows must now exist to join).
- [ ] On 482012f1: NO kemadruma firing, NO daridra firing, NO kala_sarpa D1 firing; the 18-varga KS facts untouched.
- [ ] Zero `dosha_label`/`yoga_label` rows that "fire" on `requires_pass` without an explicit `catalog_only`/`fires:null` marker.
- [ ] Strength on every new firing row is `constituent_bala_v1` or NULL — grep your diff for any invented multiplier (B.10).
- [ ] All new detectors carry classical citations (writer rail: "Classical citations required on every yoga").
- [ ] Full sidecar suite zero new failures; migration-guard sign-off.
- [ ] On 1c826d5a (Abhinandan): writer runs clean; no assertion assumes 482012f1's placements outside `CANONICAL_CHART_ID` guards.

## 6. Known traps

- **CR-33/CR-43**: a verdict-builder must never assert "not formed" from absence-in-page, and catalog presence ≠ firing. Your `catalog_only` marker exists precisely so serving can honor this — don't undermine it by writing ambiguous rows.
- **CR-23 is a governance gate, not code**: store grounds; do not "fix" the Jupiter disagreement either direction.
- **B.10 twice over**: no invented strength formulas; no invented cancellation doctrine — every cancellation rule carries a citation or the honest-NULL reason.
- **Lane-1 collision**: `_build_dosha_rows`/`_build_yoga_rows` move in Lane 1. Rebase on Lane 1's merge BEFORE touching them; if Lane 1 slipped, implement Deliverables A+B first and hold C.
- **Kemadruma's own bhanga logic**: the writer header says it is "left untouched, not duplicated" — your kemadruma cancellation must integrate with whatever exists, not add a second evaluator. Read the existing code path first.

## 7. Anti-scope

No MSR/salience (Lane 4 will rank these firings). No serving-plane TS (Lane 5 gates catalog rows at the tool). No KP engine (CR-75 DEFERRED-EXPLICIT). No vedha completion (CR-21 deferred). No new asset. No orchestrator change. No chart rebuilds/deploys (CONDUCTOR).

## 8. Done-definition / handback

Worktree branch: detectors + registry + NBRY grounds + dosha gating + migration + tests, green. Report: detector list with citation refs, the NBRY verify-first finding (did current code already fire the D9 specimens?), 482012f1 fixture results, §5 checklist.
