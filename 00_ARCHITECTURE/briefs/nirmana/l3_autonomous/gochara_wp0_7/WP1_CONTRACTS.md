---
artifact: WP1_CONTRACTS
version: "1.0"
status: DESIGN_FOR_WP6_IMPLEMENTATION
date: 2026-09-23
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md (NATIVE_RATIFIED_PLAN) §4.1, §4.3–4.7, §5.3, §5.5 + GOCHARA_RULING_SHEET_v1_0.md N-4a(b″), N-7, N-10, N-12, N-14
scope: "WP1 only — contracts as design documents + golden-case fixtures. No code, no migration files placed under platform/migrations (WP6 owns implementation); the SQL below is in-document draft for WP6 to lift verbatim."
---

# WP1 — Contracts (convention vector, target resolution, ledger, coverage, publication)

Run: `l3/gochara-autonomous-wp0-7` @ `fd13ec0a6` (pin `c58e86662` is an ancestor; see E-002).
Everything below is pinned here so WP2–WP7 read one document, not five conversations.
The plan (`GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md`) is the source of truth; where this
document states a choice the plan left open, the choice is marked **WP1 decision** with
its reasoning.

---

## 1. Convention vector — `kala_gochara_convention` (reference table)

Per plan §4.1 (D-1, N-4, F-14, F-15), the canonical vector every ledger row, coverage
row and publication manifest references by one `convention_id`:

| field | value |
|---|---|
| `zodiac` | `sidereal` |
| `ayanamsha` | `lahiri_chitrapaksha` |
| `sidereal_method` | `swe_flg_sidereal` (D-1: Swiss's own sidereal mode, `FLG_SIDEREAL` + `SIDM_LAHIRI`; NOT `tropical − get_ayanamsa_ut`, which differs by nutation in longitude of date, +16.516″ on 2020-01-01 / −5.523″ on 2026-01-01 — pinned at WP0) |
| `node_model` | `mean` (N-4, ruled) |
| `node_source` | `swiss_mean_node_flg_sidereal` (N-4a(b″): `swe.MEAN_NODE` under `FLG_SIDEREAL`, one L0-owned implementation; no regression model, no consumer-side copy) |
| `epoch_convention` | `noon_ut_knot_abscissa` (F-15: substrate knots are noon UT; a midnight abscissa showed a spurious 332.3″) |
| `ephemeris_mode` | `flg_swieph` (the *requested* backend — a method field) |
| `ephemeris_backend` | recorded **from the returned `retflag` of a probe `swe.calc_ut`, never from the requested flag** (F-14): `swieph` when `retflag & 2`, `moshier` when `retflag & 4` — see §10 |
| `time_scale` | `UT→TT via swe.deltat` |
| `house_system` | `whole_sign` (for sign-level targets; M-5 ratified: whole-sign residence is primary, cusp-point contact is a labelled KP-school variant only, never blended) |

**WP1 decision — a reference TABLE, not embedded jsonb.** `kala_gochara_convention`
with one row per distinct vector:

- **Join-ability.** Contacts, coverage and publication rows each carry a single
  `convention_id uuid` FK. "Which contacts were computed under the mean-node
  convention?" is one indexed join; over embedded jsonb it is a JSON-path scan per row.
- **Referential integrity.** The FK guarantees no ledger row references a convention
  that does not exist; a typo'd jsonb blob is undetectable until someone compares.
- **Id stability.** The natural id is `sha256` over the canonical vector fields
  (§1.1), computable identically by any reimplementation — including one that has
  never seen this database.
- **Single point of change.** A tolerance or method change inserts ONE new row
  (new `convention_id`); every downstream row keeps pointing at the old one. With
  embedded jsonb, history rewrites itself in place.

**Comparability rule (pinned, plan §4.1):** two rows with different `convention_id`s
are **never compared**; no tolerance is ever quoted across them. A comparison whose
two sides carry different convention ids is `NOT_RUN` with reason
`different_convention`, never PASS and never a number.

### 1.1 Convention id derivation (canonical, reimplementable)

```text
vector = {
  "zodiac":            "sidereal",
  "ayanamsha":         "lahiri_chitrapaksha",
  "sidereal_method":   "swe_flg_sidereal",
  "node_model":        "mean",
  "node_source":       "swiss_mean_node_flg_sidereal",
  "epoch_convention":  "noon_ut_knot_abscissa",
  "time_scale":        "ut_to_tt_swe_deltat",
  "house_system":      "whole_sign",
  "ephemeris_mode":    "flg_swieph",
}
canonical = json.dumps(vector, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
convention_id = "sha256:" + sha256(canonical.encode("utf-8")).hexdigest()
```

`ephemeris_backend` (the retflag-derived actual) is deliberately **not** hashed into
`convention_id`: it is an environmental observation, not a method choice, and hashing
it would make ids unstable when a host lacks the `.se1` files. It is recorded on the
convention row (`ephemeris_backend` + probe `retflag`, §10) and per contact/publication
row, and the F-14 gate (§10) already forbids gate-grade comparison on a Moshier actual.
**A tolerance or method change always implies a new `convention_id`** (N-7 condition;
also §9) — the new vector hashes differently, end of story.

### 1.2 SQL draft (for WP6; do NOT place in platform/migrations from WP1)

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS kala_gochara_convention (
  convention_id     TEXT PRIMARY KEY,          -- "sha256:<hex>" per §1.1
  -- WP1 type note: the id is TEXT, not uuid-typed — the natural id IS the full
  -- sha256 hex; coercing to uuid would truncate it and break independent
  -- reimplementation of the id from the vector alone. Same for contact_id (§3.1).
  zodiac            TEXT NOT NULL,
  ayanamsha         TEXT NOT NULL,
  sidereal_method   TEXT NOT NULL,
  node_model        TEXT NOT NULL,
  node_source       TEXT NOT NULL,
  epoch_convention  TEXT NOT NULL,
  time_scale        TEXT NOT NULL,
  house_system      TEXT NOT NULL,
  ephemeris_mode    TEXT NOT NULL,             -- requested backend (method field)
  ephemeris_backend TEXT,                      -- from probe retflag, never requested flag
  probe_retflag     INTEGER,                   -- raw retflag of the registration probe calc
  se1_checksums     JSONB,                     -- {sepl_18, semo_18, seas_18} sha256 at registration
  method_version    TEXT NOT NULL,             -- kernel/projection method version (semver)
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE kala_gochara_convention IS
  'Gochara convention vector, one row per distinct vector; natural id = sha256 of the '
  'canonical vector fields (WP1_CONTRACTS.md §1.1). Two rows with different ids are '
  'never compared; a tolerance/method change inserts a new row, never edits one.';

COMMIT;
```

Immutability: convention rows are insert-only (WP6 enforces: no UPDATE/DELETE; a
correction is a new row). `method_version` is part of the contact id (§3.2) so a
method change regenerates ids even when the vector's astrophysics is unchanged.

---

## 2. Target-resolution contract (plan §5.3, VERBATIM + executable logic)

Reproduced verbatim from plan §5.3 (rows counted on the canonical chart `[L]`; the
column lists are the contract — do not paraphrase them downstream):

| target_type | rows | today | resolution rule (deterministic; cite both facts) | object kind | unresolvable → `target_resolution_state` |
|---|---|---|---|---|---|
| `karaka` | 44 | degree | `graha_position[subject=graha].longitude_sidereal`; Rāhu/Ketu → `RAH_MEAN`/`KET_MEAN` (N-4) | point | `unavailable` if the fact is absent |
| `dasha_lord_portfolio` | 44 | degree | same as karaka | point | same |
| `lord` (`1L`…`12L`) | 52 | none | house N sign = whole-sign offset from `LAGNA` `graha_sign_attributes.sign_num`; sign → lord by the fixed classical rulership table (L0 reference row cited); lord → its `graha_position` row | point | `unqualified` (rulership row missing) |
| `bhava` (`1`…`12`) | 68 | sign | whole-sign span from `LAGNA`; **no point is invented** from a cusp (`bhava_cusps` exists — using it is M-5) | **interval** (residence) | n/a |
| `mechanism_node` (`jupiter:double_transit:h11`) | 93 | via w-modules | graha + rule + house → house sign span; relation = sign-ingress / residence | **interval** | `unqualified` if the rule's operand is not wired (M-4) |
| `arudha` (fact_id of the `sign` row) | 68 | none | sibling `arudha_pada[subject].longitude_sidereal` **is a cusp placeholder (F-20)** → treat as the sign span of `fact_value_text`; a degree-level ārūḍha is M-5/M-6 | **interval** | n/a |
| `yoga_constituent` (yoga id) | 220 | none | `ga_yoga_firings[fired=true].constituent_fact_ids` → each constituent `graha_position` row; one `independence_group` per yoga (H-6); `bhanga_active=true` (`neecha_bhanga_raja_yoga`) carried as a qualifier, not a weight | point(s) | **166 rows resolvable (11 ids); 54 rows (`ardhachandra`, `chatra`) `unavailable` today (F-21)** |
| `sensitive_degree` (fact_id into `sensitive_degree_check`) | 176 | none | the check row has **no longitude**; the sensitivity is a property of its subject graha's degree → resolve to that graha's `graha_position` row **only when the check is positive** (`papa_kartari`, `shubha_kartari`, `pushkara`: 22 rows) and merge into the graha's own `independence_group`; **154 rows cite a negative result and must not be targets (F-19)** | point (qualifier) | negative-result rows: removed at G-R (N-12); if retained pending ruling, `inapplicable` |

**Consequence for scope (verbatim):** after this contract, point-resolvable targets are
44 + 44 + 52 + 166 + 22 = **328 rows**, interval targets 68 + 93 + 68 = **229**, and
**208 rows are honest nulls** (154 negative-result + 54 dangling) that today masquerade
as targets the engine "evaluated".

### 2.1 Pinned vocabulary: `target_resolution_state`

Closed enum, stored by R-6 (WP3c) on `gochara_resonance_map` and on every contact row
(§3): **`{resolved, unavailable, unqualified}`**.

- `resolved` — the contract produced a point or an interval.
- `unavailable` — the cited input fact/relation is absent (`karaka` fact missing;
  dangling yoga id with no live `ga_yoga_firings` row; overlay beyond its horizon).
- `unqualified` — the resolution chain exists but cannot be completed honestly
  (rulership row missing; mechanism operand unwired; kakṣyā with no resolvable bindu).

`inapplicable` from the plan's sensitive_degree row is **not** a stored state: N-12 is
ruled, so negative-result sensitive rows are removed at the resonance layer (WP3c R-1)
and produce **zero target rows** — there is nothing to store a state on. The three
negative predicates (`not_gandanta`, `mrityu_bhaga not_fired`, `not_pushkara`,
`kartari none`) and positive set (`papa_kartari`, `shubha_kartari`, `pushkara`) are
pinned in the WP3c acceptance tests.

### 2.2 Executable resolution logic (per type)

Fact-subject vocabulary note (from `enrichment.py:19-39`, live-verified): L1
`chart_facts.graha_position.fact_subject` carries 3-letter abbreviations
(`SUN, MOON, MAR, MER, JUP, VEN, SAT`) with nodes as `RAH_MEAN`/`KET_MEAN`, plus
`LAGNA`. The resolution code translates at the query boundary only.

1. **`karaka`** — input: `target_ref` = graha name. Let s = map(target_ref). Look up
   `chart_facts WHERE fact_category='graha_position' AND fact_subject=s AND
   fact_key='longitude_sidereal'`. Present → point target at that degree. Absent →
   `target_resolution_state='unavailable'` (no degree fabricated).
2. **`dasha_lord_portfolio`** — identical to `karaka` (`target_ref` = daśā lord graha;
   `writer.py:409-414` fetches vimshottari level-1 lords).
3. **`lord` (N = house number)** — sign(N) = whole_sign_offset(lagna_sign, N) where
   lagna_sign = `graha_sign_attributes[LAGNA].sign_num` and whole_sign_offset adds
   N−1 signs (the convention `enrichment.py:193-217` and `primitives._offset_sign`
   both use). lord_graha = fixed classical rulership table (Aries→Mars …
   Pisces→Jupiter; an L0 reference row is cited by the writer). Then resolve
   lord_graha as `karaka`. Missing rulership row → `unqualified`. (R-4 implements
   this in WP3c; today `enrichment.py` resolves none of it.)
4. **`bhava` (N)** — interval target: sign span [30·(s−1), 30·s) for
   s = whole_sign_offset(lagna_sign, N). Never a point; `bhava_cusps` is not read
   (M-5: cusp anchoring is a labelled KP-school variant only).
5. **`mechanism_node`** — parse `target_ref` = `{graha}:{rule_type}:h{house}`. The rule
   row (`bg_transit_rules`) supplies the mechanism's operand wiring. Resolve house H's
   whole-sign span from LAGNA as in (4). If the rule's operand is not wired
   (M-4 operand audit fails) → `unqualified`. Relations on interval targets are
   sign-ingress / residence only.
6. **`arudha`** — input: fact_id of the `arudha_pada` `sign` row. Read
   `fact_value_text` (the sign). Emit the sign span of that sign. The sibling
   `longitude_sidereal` is **never** read as a degree — every live value is exactly
   30·(sign−1), a cusp placeholder (F-20); resolving it to a degree would fabricate
   exact contacts at cusps (a §6 stop condition).
7. **`yoga_constituent`** — input: `target_ref` = yoga_canonical_id. Look up
   `ga_yoga_firings WHERE chart_id=… AND fired=true AND yoga_canonical_id=…`. No live
   firing row → `unavailable` (F-21: `ardhachandra`, `chatra` today; never a silent
   skip). Present → expand `constituent_fact_ids`, resolve each constituent's
   `graha_position` row to a point; **one `independence_group` per yoga id** (H-6);
   `bhanga_active=true` is carried as a qualifier, not a weight.
8. **`sensitive_degree`** — input: fact_id into `sensitive_degree_check`. Read the
   check row's result value. **Positive** (`papa_kartari`, `shubha_kartari`,
   `pushkara`) → resolve to the subject graha's own `graha_position` degree and merge
   into that graha's `independence_group` (the check row has no longitude of its own).
   **Negative** (`not_gandanta`, `mrityu_bhaga not_fired`, `not_pushkara`,
   `kartari none`) → **no target at all** (F-19; R-1 at WP3c).
9. **`gulika_mandi_distance`** (M-6, Phaladīpikā Adh. XVII śl.26, served chunk
   `PG220:C1`) — emitted only for the classes the chapter names (`bereavement`,
   `illness_acute`). Let e = occupied sign of the 8th-house lord (resolve house 8's
   whole-sign sign from LAGNA as in (3), take its classical lord, then that graha's
   occupied sign) and m = Māndi's sign (`sensitive_point_gulika_mandi[MANDI].sign`).
   N = forward zodiacal distance e→m (0 when they tenant the same sign). Target =
   the whole-sign interval of the sign N removed from Māndi in the same forward
   direction (N=0 → Māndi's own sign). Transit agent: Saturn (carried as
   `target_qualifier='agent:Saturn'`). Any missing operand fact → `unavailable`;
   missing/incomplete `reference_signs` → `unqualified` (R-4 convention). Shared
   arithmetic: `services/gochara_grammar/derived_points.py`
   (`mandi_distance_target_sign_num`) — the single source imported by BOTH the
   resonance writer and `enrichment.py`.
10. **`yamakantaka_difference`** (M-6, `PG214:C1` śl.6-8, `PG217:C1` śl.14) — same
   class scoping as (9). Whole-sign difference rāśis: A−B mod 12 (0 read as 12,
   Pisces), target = whole-sign interval of the resulting sign. Formulas (ref —
   minuend − subtrahend, agent, citation): `lagna_lord_minus_yamakantaka` —
   lagna-lord − Y, Jupiter, `PG214:C1 śl.6; PG217:C1 śl.14`;
   `sun_minus_yamakantaka` — Sun − Y, Jupiter, `PG214:C1 śl.7`;
   `yamakantaka_minus_mandi` — Y − Māndi, Saturn, `PG214:C1 śl.7`;
   `panchama_tara_lord_minus_yamakantaka` — 5th-star-lord − Y, Jupiter,
   `PG214:C1 śl.8`. Y = Yamakaṇṭaka's sign
   (`sensitive_point_gulika_mandi[YAMAKANTAKA].sign`, persisted native-only by
   `ga_sensitive_writer` — no day-table fallback; absent for charts where the
   native value is unavailable → `unavailable`). 5th-star-lord = Vimśottari lord
   of the 5th nakṣatra from the natal Moon nakṣatra (natal counts as 1), resolved
   to that graha's occupied sign. Same state discipline and shared-module rule as
   (9) (`difference_sign_num`, `fifth_star_lord`). **Declared coarser:** the
   verses' "figures" carry degree precision and name navāṃśa refinement and
   trikona positions; with sign-grain served operands only the whole-sign
   difference is honestly computable, so navāṃśa/trikona are named here and NOT
   emitted in v1 — never fabricate a midpoint point.
11. **`bhava_arudha`** (M-6) — the ārūḍha of house N for each numeric house in the
   event class's `signature_model`, emitted for all classes. `target_ref` is the
   clean symbolic `BHAVA_ARUDHA_A{N}` (natural-key stable, mirroring `NL` for
   lords). Resolve via the `arudha_pada` `sign` row of subject `ARUDHA_A{N}`:
   present and a valid sign → whole-sign interval of that sign (`resolved`);
   absent or invalid → `unavailable`. The sibling `longitude_sidereal` cusp
   placeholder is never read as a degree (same F-20 discipline as (6)).
   `uncited_extension=True` — the ārūḍha primitive is real, but its linkage to
   THIS event class is this writer's own synthesis.

**M-5 note (ratified):** whole-sign residence is the primary object for bhava, arudha
and mechanism-node targets; cusp-point contact is admitted only as a KP-school variant
carrying an explicit school label, never blended into the Parāśari projection. Interval
targets produce residence spans and ingress episodes, never point contacts.

**N-14 note (ratified):** Rāhu/Ketu cast **no dṛṣṭi** — not the 7th either; the
served `SPECIAL_DRISHTI_DEG` entries for Rāhu/Ketu (`primitives.py:193-194`, currently
Jupiter's `[120,180,240]` with a BPHS Ch.26 citation the corpus refutes, F-29) are
dropped from `drishti_contact` families. The nodes remain full gochara **agents and
targets**: conjunction, sign-ingress, nakṣatra-ingress, kakṣyā-cell crossing and
returns from/to them stay in the relation set, and `RAH_MEAN`/`KET_MEAN` remain point
targets per the karaka rule.

### 2.3 Golden-case fixtures

Machine-readable companion:
`platform/python-sidecar/tests/l3/gochara/fixtures/wp1_target_resolution.json` —
one case per §5.3 row (8 cases) plus the three negative cases (negative sensitive
check → zero targets; cusp-placeholder arudha → no point contact; dangling yoga id →
`unavailable`), plus the M-6 cases (one golden per §2.2 items 9-11 row —
`gulika_mandi_distance`, the four `yamakantaka_difference` formulas,
`bhava_arudha` — and their `unavailable` variants: missing Māndi/Yamakaṇṭaka
sensitive fact, missing Moon-nakṣatra fact, missing arudha sign fact, invalid
sign value). Every case is `"derivation": "hand-specified"` with a one-line note;
chart ids are synthetic (`wp1-synth-…`), never a real chart.

---

## 3. Contact ledger — `kala_gochara_contacts` (N-7)

Field-for-field per plan §4.3's group table. One row per episode, per chart, per
generation. Natural key `(chart_id, generation, contact_id)`.

### 3.1 SQL draft (for WP6; do NOT place in platform/migrations from WP1)

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS kala_gochara_contacts (
  -- identity
  chart_id          UUID NOT NULL,
  generation        TEXT NOT NULL,              -- '4.0', '4.1', ... (never g4_*)
  contact_id        TEXT NOT NULL,              -- "sha256:<hex>" per §3.2
  independence_group TEXT NOT NULL,             -- H-6: one physical contact via several
                                                --   targets/rules counts once
  -- geometry
  body              TEXT NOT NULL,              -- Title-case graha agent
  relation          TEXT NOT NULL,              -- conjunction|drishti_contact|
                                                --   sign_ingress|nakshatra_ingress|
                                                --   kakshya_cell_crossing|return
  aspect_deg        NUMERIC,                    -- dṛṣṭi angle for drishti_contact; else 0
  target_type       TEXT NOT NULL,              -- §5.3 target_type (target_kind)
  target_ref        TEXT NOT NULL,              -- resonance-map ref (graha/house/fact_id/yoga id)
  target_fact_id    TEXT,                       -- L1 chart_facts.fact_id or NULL
  target_resolution_state TEXT NOT NULL
                    CHECK (target_resolution_state IN ('resolved','unavailable','unqualified')),
  target_longitude_deg NUMERIC,                 -- reference copy; L1 is authority (§N.5)
  -- time
  t_in              TIMESTAMPTZ NOT NULL,
  t_exact           TIMESTAMPTZ NOT NULL,
  t_out             TIMESTAMPTZ NOT NULL,
  bracket_seconds   INTEGER NOT NULL,           -- declared per relation class (§9)
  tolerance_arcsec  NUMERIC NOT NULL,           -- declared per relation class (§9)
  truncated_at_horizon TEXT CHECK (truncated_at_horizon IN ('start','end') OR truncated_at_horizon IS NULL),
  -- motion
  branch            TEXT NOT NULL CHECK (branch IN ('direct','retrograde','station')),
  station_flag      BOOLEAN NOT NULL DEFAULT FALSE,
  exact_crossing    BOOLEAN NOT NULL DEFAULT TRUE,
  orb_max_deg       NUMERIC NOT NULL,
  orb_source        TEXT NOT NULL,              -- §7 orb-table row id
  dwell_days        NUMERIC,
  -- qualification (F04/F06/F12)
  epistemic_class   TEXT NOT NULL,
  completeness_state TEXT NOT NULL,             -- six F06 states; unqualified propagated
                                                --   from near_station_unresolved, never a
                                                --   silent boolean (§4.2)
  operator_role     TEXT NOT NULL,
  claim_grain       TEXT NOT NULL,
  time_basis        TEXT NOT NULL,
  comparable_with   TEXT NOT NULL CHECK (comparable_with IN
                    ('self','same_convention_same_inputs',
                     'same_convention_newer_inputs','different_convention')),
  -- provenance
  convention_id     TEXT NOT NULL REFERENCES kala_gochara_convention(convention_id),
  ephemeris_backend JSONB NOT NULL,             -- {backend, retflag, se1_checksums{...}}
  evidence_fact_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  classical_citation TEXT,
  uncited_extension BOOLEAN NOT NULL DEFAULT FALSE,
  corpus_verifiable BOOLEAN,                    -- §5.4: cited text resolves in served corpus; §6.1 (N-21): nāḍī-only attestation ⇒ false
  input_generation_vector_id TEXT NOT NULL,     -- -> kala_gochara_publication.manifest_id
  build_id          TEXT NOT NULL,
  computed_at       TIMESTAMPTZ NOT NULL,

  PRIMARY KEY (chart_id, generation, contact_id)
);

-- Covering indexes (WP6 measures serving-query latency with these in place, §4.5):
CREATE INDEX IF NOT EXISTS idx_kgc_serve ON kala_gochara_contacts
  (chart_id, generation, body, t_exact) INCLUDE
  (relation, target_type, target_ref, contact_id, independence_group,
   completeness_state, comparable_with);
CREATE INDEX IF NOT EXISTS idx_kgc_independence ON kala_gochara_contacts
  (chart_id, generation, independence_group);
CREATE INDEX IF NOT EXISTS idx_kgc_target ON kala_gochara_contacts
  (chart_id, generation, target_type, target_ref);

COMMENT ON TABLE kala_gochara_contacts IS
  'Gochara contact ledger (N-7): one row per episode per chart per generation. '
  'Natural key (chart_id, generation, contact_id). contact_id = sha256 over the '
  'canonical serialization at WP1_CONTRACTS.md §3.2 — stable under horizon '
  're-partitioning. Overlay state at the contact instant is deliberately NOT stored '
  'here; the projection recomputes it from interval sets (§4.3).';

COMMIT;
```

### 3.2 `contact_id` — exact canonical serialization

Pinned so an independent reimplementation produces **identical ids** (the §10 identity
test depends on it):

```text
payload = {
  "chart_id":     str(chart_id),                 # lowercase uuid text
  "convention_id": str(convention_id),            # "sha256:<hex>" from §1.1
  "body":         str(body),                     # "Saturn", "Moon", ...
  "target_kind":  str(target_type),              # §5.3 vocabulary, e.g. "karaka"
  "target_identity":
      "fact:" + target_fact_id                   # when target_fact_id is not None
      else "ref:" + target_ref,                  # when it is (unambiguous prefix, no collision)
  "relation":     str(relation),                 # §3.1 relation vocabulary
  "aspect_deg":   round(float(aspect_deg) % 360.0, 4),
  "t_exact":      floor_to_minute_utc_iso(t_exact),
  "method_version": str(method_version),
}
canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
contact_id = "sha256:" + sha256(canonical.encode("utf-8")).hexdigest()
```

where `floor_to_minute_utc_iso(t)` = convert `t` to Unix epoch seconds, floor to the
60-second boundary (`math.floor(epoch / 60) * 60`), render as UTC ISO-8601
`YYYY-MM-DDTHH:MM:00Z`. Floor (not round) so the id never changes under a ±30 s jitter
and re-partitioning a horizon differently cannot move an id across a minute boundary.

`method_version` is hashed in per plan §4.3 — a tolerance or method change implies a
new `convention_id` anyway (§1), and hashing `method_version` is the second lock: the
id changes if either the convention or the method changes, so an id never silently
survives a change to the row it names.

### 3.3 Deliberate non-decisions

- **Overlay state is NOT copied onto the contact row** (plan §4.3, verbatim intent):
  Vedha/Moorti/quality-gate state at `t_exact` is recomputed by the projection from
  interval sets, so §10's "overlay at instant" proof is a recomputation identity, not
  a stored copy that could drift. Contact rows therefore never carry
  `quality_gates`-style fields.
- **H-6 (pinned):** one physical contribution reached through multiple targets or
  rules counts **once**, via `independence_group`. Every row carrying the same
  physical (body, t_exact±ε, target-degree) event shares one `independence_group`
  value; the duplication proof (§10) asserts the activity is unchanged against WP2's
  hand-specified oracle — never "unchanged vs the system's own prior output".
- Rows with no citable source stay `unqualified` — not silently dropped, not silently
  promoted (WP3c exit gate).

---

## 4. Search-coverage manifest — `kala_gochara_coverage` (plan §4.4)

One row per (chart, generation, partition), where partition = body × target_type, or
event_class for the projection. Every no-window / no-contact answer served carries
this object (Strategy §3; L3-Q08).

### 4.1 SQL draft (for WP6)

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS kala_gochara_coverage (
  chart_id            UUID NOT NULL,
  generation          TEXT NOT NULL,
  partition_kind      TEXT NOT NULL
                      CHECK (partition_kind IN ('body_target','event_class','moon_on_demand')),
  partition_key       TEXT NOT NULL,   -- e.g. 'saturn:karaka' | 'marriage' |
                                       --   'moon:interval:<start>/<end>'
  convention_id       TEXT NOT NULL REFERENCES kala_gochara_convention(convention_id),
  requested_horizon   TSTZRANGE NOT NULL,
  completed_horizon   TSTZRANGE NOT NULL,   -- H-3: reported exactly, never silently
                                            --   truncated into the requested range
  resolution          NUMERIC NOT NULL,     -- ε (arcsec) used for this partition
  relations_searched  TEXT[] NOT NULL,
  targets_requested   INTEGER NOT NULL,
  targets_resolved    INTEGER NOT NULL,
  targets_unresolved  INTEGER NOT NULL,
  target_resolution_state_counts JSONB NOT NULL,  -- {"resolved":n,"unavailable":n,
                                                  --  "unqualified":n}
  unavailable_inputs  JSONB NOT NULL DEFAULT '{}'::jsonb,  -- e.g. {"vedha_overlay":
                                     --  {"reason":"beyond_overlay_horizon","span":[...]}}
  unsearched_reason   TEXT,          -- NULL when fully searched; else the honest reason
  build_id            TEXT NOT NULL,
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, partition_kind, partition_key)
);

CREATE INDEX IF NOT EXISTS idx_kgcov_chart ON kala_gochara_coverage
  (chart_id, generation, partition_kind);

COMMENT ON TABLE kala_gochara_coverage IS
  'Search-coverage manifest (plan §4.4): requested vs completed horizon, resolution, '
  'relations searched, target resolution states, unavailable inputs, unsearched '
  'reason. Moon on-demand partitions are first-class (partition_kind=moon_on_demand): '
  'a Moon search writes a coverage record for the requested interval even though '
  'Moon contacts are not persisted by default (R7).';

COMMIT;
```

Invariants: `targets_resolved + targets_unresolved = targets_requested`;
`target_resolution_state_counts` sums to `targets_unresolved` across the non-resolved
states; `completed_horizon` ⊄ `requested_horizon` only with a non-NULL
`unsearched_reason` (H-3). A `moon_on_demand` row is written for every Moon search
even when the answer is zero contacts — otherwise L3-Q08 cannot be answered for
Moon-dependent classes (plan §4.2).

---

## 5. Publication model — `kala_gochara_publication` (plan §4.7, N-10)

### 5.1 Generation label

The family's product generation going forward is **`'4.0'`** — bare string, **never a
`g4_*` prefix**: the serving code routes `g3_*`/`'3.0'` to the century writer's
provenance and a `g4_` prefix matches neither branch while a bare `'4.0'` currently
falls through to the **v1** branch — both wrong (plan §4.7). P-1 (WP7 packet) adds the
manifest-driven branch; this family does not work around the gap by relabeling.

### 5.2 SQL draft (for WP6)

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS kala_gochara_publication (
  manifest_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id          UUID NOT NULL,
  generation        TEXT NOT NULL,              -- '4.0', '4.1', ...
  writer_asset_id   TEXT NOT NULL,              -- 'ka_gochara'
  convention_id     TEXT NOT NULL REFERENCES kala_gochara_convention(convention_id),
  input_generation_vector JSONB NOT NULL,       -- §5.3
  ephemeris_backend JSONB NOT NULL,             -- {backend, retflag, se1_checksums} from
                                                --   the build's retflag(s), never requested
  horizon           TSTZRANGE NOT NULL,
  row_counts        JSONB NOT NULL,             -- {contacts:n, coverage:n, windows:n}
  content_digest    TEXT NOT NULL,              -- sha256 over the canonical row set
  status            TEXT NOT NULL DEFAULT 'candidate'
                    CHECK (status IN ('candidate','published','superseded','rolled_back')),
  published_at      TIMESTAMPTZ,
  superseded_at     TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (chart_id, generation)
);

CREATE INDEX IF NOT EXISTS idx_kgpub_chart ON kala_gochara_publication
  (chart_id, status, generation);

COMMENT ON TABLE kala_gochara_publication IS
  'Publication manifest (N-10): one row per (chart, generation). A generation is '
  'immutable once published; a rebuild while candidate replaces the candidate; after '
  'publication a rebuild is a NEW generation label. The writer refuses '
  'delete-then-insert against a published generation (WP6 gate).';

COMMIT;
```

### 5.3 Input generation vector (plan §5.5, pinned field-for-field)

`input_generation_vector` pins, per publication:

| key | pins |
|---|---|
| `resonance` | `computed_at` + row count of `gochara_resonance_map` for this chart |
| `ga_yoga_firings` | build id |
| `chart_facts` | build ids **for the categories the target contract reads** (§5.2: graha_position, graha_sign_attributes, ashtakavarga_kakshya_boundary, arudha_pada, sensitive_degree_check, chart_dashas, ashtakavarga_*) |
| `ephemeris_daily` | `substrate_version` |
| `overlays` | Vedha / Moorti / Sade-Sati build ids |
| `bg_transit_rules` | **content digest** (sha256 over canonical row set) — NOT a count; a count cannot catch an in-place edit of a threshold row (75 rows) |
| `bg_transit_av_gates` | **content digest** (same reason; 8 rows) |
| `convention_id` | the §1.1 id |

A rebuild whose vector differs from a published one is **always a new candidate,
never an in-place refill** (§4.7). The dangling-yoga drift (F-21) is exactly the
failure this vector makes visible: R-3 re-validates yoga targets at build time and
pins the firing set here, so a yoga id that later stops firing is caught as a vector
diff, not silently served stale.

### 5.4 Lifecycle (pinned)

- `candidate` — mutable: delete-then-insert scoped to (chart × generation) is legal
  **within** a candidate (§N.3 idempotency), overwriting the candidate's rows.
- `published` — **immutable**. Any rebuild after publication is a new generation
  label (`'4.1'`, …) with its own manifest. **The writer refuses delete-then-insert
  against a `published` generation** — WP6 implements the refusal and writes the test
  that proves it (plan §4.7; N-7 condition). This is how replace-not-accrete and
  immutability coexist.
- `superseded` — a later generation published for the same chart.
- `rolled_back` — authority re-pointed to `'3.0'` (whose rows are never touched);
  the `'4.0'` manifest is marked `rolled_back`, not deleted.
- **Authority flip (WP10, out of scope here):** writes `evidence_ref = manifest_id`
  into `kala_gochara_authority` (existing column; 527's table is **unchanged** — no
  schema change is designed here, and none may be). Absent authority row ⇒
  `unpublished`, served as a coverage object (N-10 P-1d); the `'v1'` COALESCE
  fall-through is removed from every reader by P-1, not by this family.

---

## 6. `comparable_with` — closed enum (pinned at WP1, N-7 condition)

Free text is forbidden; the column is a CHECK-constrained enum (§3.1). Per-value
semantics:

| value | meaning | may be compared? |
|---|---|---|
| `self` | the same contact row compared to its own recomputation (identity / determinism test, e.g. the §10 re-partition and two-date rebuild proofs) | yes — byte/id equality expected |
| `same_convention_same_inputs` | another build (or another implementation) over the same convention id and an input generation vector whose every pinned field is identical | yes — within the declared ε (§9); gate-grade only under the §10 F-14 condition |
| `same_convention_newer_inputs` | same convention id, but at least one input-generation-vector field differs (e.g. yoga firings re-built, an overlay extended) | only as a *diff report* — deltas are classified against the changed input (WP4), never quoted as agreement within ε |
| `different_convention` | different `convention_id` (any field of §1.1 differs) | **never** — the comparison is `NOT_RUN`, reason `different_convention`; no tolerance is quoted across conventions |

Anything not in this table (free text, NULL, "mostly comparable") is a schema
violation, not a value.

### 6.1 Vocabulary note — N-21 standing rule (nāḍī attestation)

**Nāḍī attestation ⇒ `testimony`, never weight, without primary corroboration.**
A configuration whose only attestation is a nāḍī-source row (e.g.
`nadi_navamsa_patel`) is recorded as typed testimony — the non-scoring epistemic
class ruled at N-15 — and is excluded from every scoring weight set. On the stamp
columns this means: `corpus_verifiable=false` until a primary (non-nāḍī) text
carrying the composite is cited on the row, and `source_qualification` can never
be `verse_cited` from a nāḍī row alone. The N-15 Sade-Sati testimony block
(citations PG1334/PG786/PG1333, MEDIUM provenance) is the worked example of this
rule; which primary text carries the composite remains `[U]`.

---

## 7. Orb table + stated source (plan §4.2, §4.5; M-1 direction ruled)

**Doctrinal direction (cited):** BPHS ch.26 ślokas 6–8, dṛṣṭi-koṇa — strength
graduated by separation — verified at `bphs_vol1_rsanthanam_djvu.txt:16514-16529`
(plan §1.4 M-1 ruling; the classical warrant for orb-scaled activity). Degree-exact
contact with an orb is **practice** (`[P]`), so every numeric orb below is declared
with `uncited_extension=true` and an `orb_source` — unstated silence is not
acceptable (WP1 exit gate).

| orb_id | relation class | body class | orb_max_deg | source | uncited_extension |
|---|---|---|---|---|---|
| `orb_conj_slow` | conjunction | Sun…Saturn | 1.0 | practice pending M-1's WP8 evidence (decay shape + values evidence-gated); doctrinal direction BPHS ch.26 śl.6–8 | true |
| `orb_conj_moon` | conjunction | Moon | 3.0 | practice pending M-1; wider because the Moon's knot-to-knot spline curvature is highest | true |
| `orb_drishti_slow` | dṛṣṭi_contact | Mars/Jupiter/Saturn (per-graha angles per `SPECIAL_DRISHTI_DEG` minus nodes, N-14) | 1.0 | practice pending M-1; BPHS ch.26 śl.6–8 supplies the graduated-by-separation *shape*, not numbers | true |
| `orb_drishti_moon` | dṛṣṭi_contact | Moon | 3.0 | practice pending M-1 | true |
| `orb_return_slow` | return | Sun…Saturn | 0.5 | practice | true |
| `orb_return_moon` | return | Moon | 2.0 | practice | true |
| `orb_kakshya` | kakṣyā_cell_crossing | all | 0.1 | serves the served primitive's default (`primitives.py` `kakshya_cell_crossing(orb_deg=0.1)`); equal-eighths grid from L1 after H-1a | true |
| `orb_ingress` | sign_ingress / nakṣatra_ingress / residence | all | n/a | boundary-exact: episodes are rooted at the span edge; residence spans carry no orb | false (span semantics, M-5) |
| `orb_legacy_box` | **activity baseline until M-1 rules** | all | ±5 **days** around `t_exact`, reproduced **span-aware** over `t_in/t_out` (plan §4.5, E8) | the legacy semantics the projection must reproduce factor-by-factor before any M-1 change; this is the status quo ante, not a classical claim | true (declared as reproduction, not doctrine) |

N-14 applies to the relation set itself: Rāhu/Ketu appear in `orb_conj_*`,
`orb_return_*`, `orb_kakshya`, `orb_ingress` (agents and targets) and are **absent**
from `orb_drishti_*` (no nodal dṛṣṭi at all — not the 7th). Every contact row's
`orb_source` names one `orb_id` from this table.

---

## 8. Kakṣyā lord order + stated source (H-1a context; M-7 pending)

**The order the served code uses** (read from both places it lives — they agree):

1. **Saturn** (kakṣyā 1: 0°00′–3°45′)
2. **Jupiter** (2: 3°45′–7°30′)
3. **Mars** (3: 7°30′–11°15′)
4. **Sun** (4: 11°15′–15°00′)
5. **Venus** (5: 15°00′–18°45′)
6. **Mercury** (6: 18°45′–22°30′)
7. **Moon** (7: 22°30′–26°15′)
8. **Lagna** (8: 26°15′–30°00′)

Sources in code: the served-path fixture `_KAKSHYA_LORD_ORDER` at
`services/gochara_grammar/primitives.py:625` (applied cyclically from Saturn when the
L1 grid is unreachable — the F-09 served-path case), and the L1 writer's
`KAKSHYA_LORDS` at `ga_writers/ga_strength_writer.py:89-91`, which writes the same
order into `chart_facts.ashtakavarga_kakshya_boundary` (`fact_subject=KAKSHYA_{1..8}`,
`fact_key='lord'`) — the L1 grid is the same equal-eighths 3.75° division (F-27), so
H-1a's provenance swap changes the citation, not the numbers.

**Honest source statement (exit-gate item):** the served citation
(`citations.py:53`, `"BPHS Ch.66 — Kakṣyā …"`) is **not corpus-verifiable** — per plan
G-9/F-27, BPHS ch.66 exists in the corpus but carries no kakṣyā passage, and the 14
corpus rows on kakṣyā sit in `saravali`, `uttara_kalamrita`, `bphs_jaimini` and
`nadi_navamsa_patel`, none in `bphs` proper. This checkout has **no read access to
`classical_text_chunks`** (the only provisioned Postgres connection is refused), so
the *exact order* above could not be verified against an admitted text here.
**Declared: `uncited_extension=true` for the order as a doctrinal claim; the order as
served-software fact is verified (two independent code sites agree).** Corpus
verification of the order against Sārāvalī / Uttara Kālāmṛta is **owed at WP8 (M-7)**,
which the M-7 ruling already gates on G-10. Until then every kakṣyā contact row
carries `uncited_extension=true` unless H-1a has sourced the boundary from L1 (which
fixes provenance of the *grid*, not the doctrine — F-27's honest statement stands).

---

## 9. Tolerances (pinned per relation class)

Plan §4.2's rule, adopted verbatim in intent: "a dṛṣṭi exact and a conjunction exact do
not share one ε" — the floors are pinned per relation class even where equal today.

Declared values and their justification from the plan's own measurements (Appendix C,
real Swiss files, `retflag 258`): stored knots reproduce Swiss to **0.002″**;
kernel-vs-oracle residuals ≤ **0.96″** (slow bodies, incl. the Saturn 270° triple
pass); Moon residuals ≈ **1.5 s** of time.

| relation class | body class | `tolerance_arcsec` | `bracket_seconds` | justification |
|---|---|---|---|---|
| exact separation roots — `conjunction`, `drishti_contact`, `return` | slow (Sun…Saturn) | **2.0** | **300** | ≈2× the worst observed slow-body residual (0.96″); 300 s ≈ the largest observed time residual (185.6 s, Saturn 2019-01-17) rounded up to a clean bracket |
| exact separation roots — same classes | Moon | **5.0** | **60** | the Moon moves ~0.5″/s and has the highest knot-to-knot spline curvature among the nine bodies; 5″ ≈ 10 s of lunar motion, ≥6× the observed ~1.5 s residual; bracket 60 s ≈ 2× the observed time residual |
| boundary roots — `sign_ingress`, `nakshatra_ingress`, `kakshya_cell_crossing` | slow | **2.0** | **300** | same geometry as exact roots (a separation root against a fixed boundary degree) |
| boundary roots — same | Moon | **5.0** | **60** | as above |

The classes are pinned **separately** even where the numbers currently coincide:
conjunction and dṛṣṭi exacts do not share one ε by construction, so M-1's WP8
dṛṣṭi-koṇa evidence can tighten one class without silently re-pinning the other.

**Rule (N-7 condition, pinned):** a tolerance change or a method change **always
implies a new `convention_id`** (the vector differs → §1.1 hashes differently), and
`method_version` in the contact id (§3.2) changes besides. There is no path by which
a row keeps its `contact_id` while its ε or its method moved.

---

## 10. F-14 gate condition (ephemeris backend honesty)

Pinned as the gate every Swiss comparison in this family runs under (plan §4.2, §10
"Boundary / precision" row; F-14 was the vacuous-detector finding):

1. **After every `swe.calc_ut` call** in a test, gate or build, read the **returned
   `retflag`** and record `ephemeris_backend` from it — `swieph` if `retflag & 2`,
   `moshier` if `retflag & 4` — **never from the requested flag** (`FLG_SWIEPH` in
   the request proves nothing about what Swiss actually used).
2. **Gate-grade comparisons assert `retflag & 2` (SWIEPH)** on both sides before any
   number is quoted.
3. **If `retflag & 4` (Moshier fallback), the comparison is `NOT_RUN`, never PASS** —
   a "kernel vs Swiss" run on Moshier is Moshier-vs-Moshier and cannot fail (F-14,
   measured: Moshier true-node error −65.3″…+58.1″ over 55,152 noon knots).
4. **Record the three `.se1` checksums alongside every gate result** that used them
   (provisioning a gate provisions its own `.se1` copy; `/private/tmp/se1` is not
   durable):

   | file | sha256 |
   |---|---|
   | `sepl_18.se1` | `ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66` |
   | `semo_18.se1` | `1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7` |
   | `seas_18.se1` | `a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2` |

5. The probe model to copy is `bg_sky_calendar.py:230-240` (fail-closed with a real
   probe); the anti-model is the serialization decorator that locks without
   configuring the path (F-31). A gate run that cannot name its backend is vacuous
   and reports `NOT_RUN`, not PASS (§N.8 earned-signal).

---

## 11. Honest note — cost/baseline artifacts unreachable from this branch (E-001)

`KALA_COST_PROFILE_v1_0.md` and `KALA_BASELINE_v1_0.md` are **unreachable from this
branch**: they exist only on the setup worktree's branch (`l3/kala-setup-phase01`,
commits `bb7857b07`, `de2a7f269`), on neither `main` nor this branch. This was
verified and escalated as **E-001** in `ESCALATIONS.md` at the root of this working
branch (evidence: `git log --all` returns only the two setup-branch commits for both
paths). Per the execution prompt's WP1 exit-gate instruction, **WP4 proceeds with
freshly-produced numbers from this run's own pre-declared synthetic workload**, using
the family's historically-measured best completed run (**58.2 min**, live-measured)
only as a recorded external figure — never assuming the missing files' prior content,
and never the unverified 20–25 h anecdote. The §10 "Value" row's
assert-presence-or-NOT_RUN test stands as the standing state until a human decides
whether the setup session lands those artifacts on `main` (E-001 records the
decision needed).

---

## Exit-gate self-review (pass 2) — 2026-09-23

Independently re-read against the plan after drafting (fresh read, not the writing
pass). Checks and outcomes:

1. **§5.3 table verbatim** — re-diffed cell-by-cell against plan §5.3 (target_type /
   rows / today / resolution rule / object kind / unresolvable → state, all 8 rows +
   the scope-consequence sentence). VERBATIM PASS; no paraphrase of any column list.
2. **Every target type has a stated resolution or an honest state** — §2.2 items 1–8
   each state executable logic; the three negative cases (zero targets / no point
   contact / `unavailable`) have expected outputs in the fixture file. PASS.
3. **`comparable_with` pinned** — §6 closed enum of exactly the four instructed
   values, CHECK-constrained in §3.1, free text forbidden, `different_convention`
   comparisons defined as `NOT_RUN`. PASS.
4. **Orb table and kakṣyā order each cite something** — §7 cites BPHS ch.26 śl.6–8
   (`bphs_vol1:16514-16529`) as doctrinal direction with all numerics declared
   `uncited_extension=true`; §8 states the served order from both code sites and
   honestly marks the doctrine `uncited_extension=true` with WP8/M-7 verification
   owed (corpus unreachable from this checkout — no DB access). PASS, with the
   honest limit recorded rather than papered over.
5. **`contact_id` serialization** — §3.2 pins the exact payload keys, sorted-keys
   compact JSON, utf-8, sha256 hex, minute-floor time quantization, and the
   `fact:`/`ref:` identity prefix; an independent implementation can reproduce ids
   byte-for-byte. PASS.
6. **F-14 gate** — §10 pins retflag-derived backend, `retflag & 2` assertion,
   `NOT_RUN` on Moshier, and the three `.se1` checksums copied verbatim from the
   plan and re-checked character-for-character. PASS.
7. **Corrections made in this pass** — (a) §9's heading was split across two lines
   by a stray wrap (broken Markdown), repaired; (b) the previous placeholder
   "recorded separately" tail section replaced with this actual record; (c) added
   explicit note that `convention_id`/`contact_id` are `TEXT` natural ids
   (`"sha256:<hex>"`) rather than uuid-typed — a uuid would truncate the natural id
   and break independent reimplementation (§1.2, §3.1).
8. **No `must_not_touch` file modified** — verified via `git status --short` at the
   end of the run (reported in the run's final message; only WP1's own two files are
   new).
