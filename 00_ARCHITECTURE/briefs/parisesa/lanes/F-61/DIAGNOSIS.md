# F-61 Diagnosis — graha_saptavargaja_bala_component never aggregated (CL-02, S5 MŪLA)

Status: **CONFIRMED-LIVE, RESOLVED (not ESCALATE)** — the DIAGNOSIS-INCOMPLETE gap in the
original finding is closed. The writer/file/line responsible has been located and read.

## 1. Live reproduction

`mcp__marsys-jis-direct__ganita_strength_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa',
offset:0})` confirms `graha_saptavargaja_bala_component` is a served category
(`content.categories[]`); the default 50-row page trimmed past an actual saptavargaja row, so
ground truth was pulled by direct SQL (raw JSON + SQL results saved to `repro_raw.json`):

- `chart_facts` rows with `fact_category='graha_saptavargaja_bala_component'`: **every** sampled
  row (all grahas, all 5 ayanamshas present) has `fact_value_num=null`,
  `fact_value_text=null`, and a `fact_value_jsonb` pointer
  (`{source_table:'chart_divisionals', source_category:'varga_saptavargaja_bala_component',
  constituent_fact_ids:[6 UUIDs], note:...}`).
- Resolving the 6 `constituent_fact_ids` for SUN / lahiri_chitrapaksha against
  `chart_divisionals` by raw `id`: D1=7.5(Sama), D2=30(Own), D3=3.75(Shatru),
  D9=22.5(Adhi_Mitra), D12=7.5(Sama), D60=22.5(Adhi_Mitra) — **sums to 93.75**, matching the
  audit finding exactly. Per-varga data is real, non-null, individually correct. Not
  ALREADY-FIXED.

## 2. Claim decomposition — all four sub-claims verified true

- (a) `fact_value_num`/`fact_value_text` null for every graha, every call — **TRUE**, confirmed
  in the SQL sample (10/10 rows null across both JUP and MAR, all 5 ayanamshas).
- (b) jsonb pointer to 6 `chart_divisionals` UUIDs served instead of a value — **TRUE**, and the
  pointer field is literally named `constituent_fact_ids` while holding `chart_divisionals.id`
  values, not `chart_facts.fact_id` values — a naming/contract mismatch in its own right.
- (c) per-varga values individually correct, sum to a legitimate classical total — **TRUE**,
  reproduced for SUN = 93.75.
- (d) no MCP-only path resolves the pointers — **TRUE by construction**: `_get_divisional_constituent_ids`
  (below) selects `chart_divisionals.id` directly, and no `ganita_*` MCP tool accepts a raw
  `chart_divisionals.id` as a lookup key (`ganita_chart_facts_get`'s `divisional_chart` param
  resolves by varga + fact_id, not raw row id, and only one varga at a time).

## 3. Mechanism — file:line (the core task, now closed)

**Writer:** `platform/python-sidecar/ga_writers/ga_structural_writer.py`
**Function:** `_build_shadbala_extension_rows` (GA8), lines **1425–1448**.
**Helper:** `_get_divisional_constituent_ids`, lines **1683–1706**.

```python
# lines 1425-1448
# graha_saptavargaja_bala_component (V): resolvable reference to GA6 chart_divisionals rows
for g_name in CLASSICAL_GRAHAS:
    subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
    constituent_ids = (
        _get_divisional_constituent_ids(conn, chart_id, ayanamsha_id, "varga_saptavargaja_bala_component", subject)
        if conn is not None else []
    )
    rows.append(_base_row(
        "graha_saptavargaja_bala_component", subject, "saptavargaja_score",
        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
        value_num=None,
        value_jsonb={
            "source_table": "chart_divisionals",
            "source_category": "varga_saptavargaja_bala_component",
            "constituent_fact_ids": constituent_ids,
            "note": f"chart_divisionals rows for {subject} across saptavarga set ({ayanamsha_id})",
        },
        verif=UNVERIFIED_DEFAULT,
        source=f"pyjhora_adapter.ga6_reference/{eng_ver}",
        citation_human=(
            f"{g_name} saptavargaja bala component: see chart_divisionals "
            f"varga_saptavargaja_bala_component ({ayanamsha_id})."
        ),
    ))
```

```python
# lines 1683-1706
def _get_divisional_constituent_ids(
    conn, chart_id, ayanamsha_id, fact_category, graha_suffix,
) -> list[str]:
    """Return chart_divisionals.id UUIDs for all rows matching category + graha suffix. ..."""
    with conn.cursor(row_factory=_rows.tuple_row) as cur:
        cur.execute(
            """SELECT id::text FROM chart_divisionals
               WHERE chart_id = %s AND ayanamsha_id = %s
                 AND fact_category = %s
                 AND split_part(fact_subject, '.', 2) = %s
               ORDER BY fact_subject""",
            (chart_id, ayanamsha_id, fact_category, graha_suffix),
        )
        return [row[0] for row in cur.fetchall()]
```

**What's happening:** the writer was authored as a deliberate "pointer, not restated value" row
— `value_num=None` is explicit, not accidental — citing §N.5 (L1-authority: don't restate,
reference) in its own comment ("the resolvable L1-authority references for cross-table
constituent_fact_ids (§N.5)"). But two things make this a genuine defect rather than a correct
application of §N.5:

1. **§N.5's own contract requires the reference resolve back to `chart_facts.fact_id`**
   ("`constituent_facts_array` in MSR signals resolves back to `chart_facts.fact_id` — these
   MUST resolve"). `_get_divisional_constituent_ids` selects `chart_divisionals.id` (the raw
   table row id), not a `chart_facts.fact_id`. No MCP-exposed tool takes that id as input, so the
   "reference" is unresolvable by any consumer that isn't running raw SQL — a broken citation,
   not a valid one.
2. **The `fact_key` is literally `saptavargaja_score`.** A `_score` key promises a computed
   scalar. Nothing in the codebase ever sums the 6-7 per-varga `chart_divisionals.fact_value_num`
   values into that scalar — the aggregation step the fact_key names was simply never written.
   This is a naming/contract violation independent of the §N.5 citation-shape issue.

No separate "null-writing" bug needs to be found — this is that code, doing exactly what it says
(store null + pointer, never sum). The missing piece is a straightforward aggregation: sum the
`fact_value_num` of the `constituent_ids`' rows and set `value_num=<sum>` (with the existing
jsonb pointer retained as supporting evidence/citation, ideally re-keyed to `chart_facts.fact_id`
values instead of raw `chart_divisionals.id`).

## 4. Sibling census

**One exact sibling found**, same file, same defect shape (`value_num=None` + jsonb pointer to
raw `chart_divisionals.id`, key claims to be an "aggregated" total):

- **`vimsopaka_bala_per_graha.vimsopaka_total`** — `_build_vimsopaka_ext_rows`,
  `ga_structural_writer.py` lines **1643–1678**. Its own docstring (line 1652) says "GA8 writes
  `vimsopaka_bala_per_graha` as **the aggregated summary** from GA6" — an explicit claim of
  aggregation that the code directly below it does not perform (`value_num=None`, pointer to 15
  `chart_divisionals.id` UUIDs across the shodasavarga set, `source_category:
  'varga_vimsopaka_contribution'`). Live-reproduced in `repro_raw.json` sql_2: identical null
  pattern confirmed for JUP/MAR across all 5 ayanamshas.

**Checked and NOT affected** (same file, same "pointer to chart_divisionals" family, but
correctly implemented):

- `graha_in_house_composite_strength.bphs_weighted` (`_build_composite_strength_rows`, line
  ~3462) also emits `value_num=None` on a miss (line 3537), but this is the honest
  canonical-or-floor pattern: it computes a real weighted value from `constituent_facts_array`
  pointing to `chart_facts.fact_id` (via `_load_shadbala_and_bhava_fact_ids`, correctly
  resolvable) whenever the inputs exist, and only floors with a `reason` when a genuine GA3
  input is missing. Not a sibling defect — this is what F-61's fix should look like.

**Not checked in this pass** (flagged, not ruled out): the other Saptavarga-family categories
(`graha_vimsopaka_dasavarga/shadvarga/shodasavarga` — GA3-level, separate from the GA8
`vimsopaka_bala_per_graha` rollup) were listed in `ganita_strength_get`'s categories but not
individually re-derived; they appeared with populated `fact_value_num` in earlier exploration and
are presumptively fine, but were not directly SQL-verified in this lane.

## 5. Blast radius

- **§N.5 (L1 is the authority over L2+ derivations)** — applies, but in an inverted way: this is
  an *intra-L1* citation (GA8 referencing GA6, both L1 Gaṇita), and the writer's own comment
  invokes §N.5 to justify not restating the value. The defect is that the reference doesn't meet
  §N.5's own resolvability bar (fact_id, not raw table id) — so the fix should both (a) compute
  the honest sum and (b) fix the constituent-id citation to point at `chart_facts.fact_id`
  values consistent with how `_build_composite_strength_rows` does it correctly two groups later
  in the same file.
- **§N.8 (Earned-Signal Principle)** — applies directly and is the sharper framing for
  PRATINIDHI. A `fact_key` named `saptavargaja_score` with a docstring literally saying "the
  aggregated summary" is a status/label asserting a computation that no code path performs — the
  same defect class as the orchestrator no-op-completion predicate and the two `bo_pramana_mapa`
  flags in §N.8's own confirmed-instances list. It is not a rendering bug or a wiring gap; it's
  an unearned label on a `fact_key`, and per §N.8's own audit question ("what code path would
  have to run — and fail — for the signal to correctly read false?") — none exists. This is
  Confirmed Instance #5 for §N.8's list, one layer up (GA8 structural writer, not MSR/orchestrator).
- Fix shape (informational, not prescriptive — PRATINIDHI's call): a small aggregator reading the
  `constituent_ids`' `fact_value_num` from `chart_divisionals`, summing them into `value_num`,
  and re-emitting `constituent_facts_array` pointing at real `chart_facts.fact_id`s rather than
  `chart_divisionals.id`s — applies identically to both `graha_saptavargaja_bala_component` and
  its `vimsopaka_bala_per_graha` sibling.
