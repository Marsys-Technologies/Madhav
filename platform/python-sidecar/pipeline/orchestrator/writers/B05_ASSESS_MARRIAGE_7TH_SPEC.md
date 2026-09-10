# B-05: assess_marriage — Direct Natal D1 7th-House/7th-Lord/Karaka Join Spec
# For: A-16 (TypeScript engineer)
# Source: B-05 Classical Spec Pack — EKAVĀKYATĀ Stream B

---

## Preamble

A-16 must add a direct natal D1 7th-house analysis block to `assess_marriage`. The join must read
from L1 data only (never recompute). Two L1 tables are involved:

- `chart_divisionals` — produced by `ga_vargas_writer.py` (GA6). Holds `varga_house_lord` and
  `varga_house_occupant` rows for all 30 vargas.
- `chart_facts` — produced by `ga_structural_writer.py` (GA8). Holds `graha_dignity_per_varga`
  rows (one per graha per varga per ayanamsha).

Both are already queried by `register_d8_assess_domain.ts`; the new join adds two targeted
sub-queries scoped to the 7th house and its significators.

---

## §1 — Fact Keys (verified from source)

### 1.1 — 7th House Lord Identity (from `chart_divisionals`)

```
table:        chart_divisionals
fact_category: varga_house_lord
fact_subject:  D1.H7
fact_key:      lord
fact_value_text: <lord_name>   -- e.g. 'Venus' (for Aries lagna, 7H = Libra, lord = Venus)
graha field:   <lord_name>
```

Query pattern (parameterized):
```sql
SELECT fact_id, graha AS lord_name, fact_value_text, fact_subject
FROM chart_divisionals
WHERE chart_id = $1
  AND ayanamsha_id = $2
  AND fact_category = 'varga_house_lord'
  AND fact_subject = 'D1.H7'
  AND fact_key = 'lord'
LIMIT 1
```

Source: `ga_writers/ga_vargas_writer.py`, `_build_house_lord_occupant_rows()`, lines 1169-1171.
`fact_subject` is always `{vid}.H{house}` — for D1, 7th house: `'D1.H7'`.

### 1.2 — 7th House Occupant in D1 (which grahas actually sit in the 7th)

```
table:        chart_divisionals
fact_category: varga_house_occupant
fact_key:      house
fact_value_num: 7.0   -- house number
fact_subject:  D1.<SUBJECT_CODE>   -- e.g. 'D1.SAT' for Saturn
```

Query pattern:
```sql
SELECT fact_id, graha, fact_subject, fact_value_num AS house_in_d1
FROM chart_divisionals
WHERE chart_id = $1
  AND ayanamsha_id = $2
  AND fact_category = 'varga_house_occupant'
  AND fact_value_num = 7.0
  AND fact_subject LIKE 'D1.%'
```

Note: For the native (Abhisek Mohanty, Aries lagna), Saturn occupies the 7th house in D1
(exalted Saturn in Libra). This query returns ALL occupants, not just Saturn.

### 1.3 — 7th Lord Dignity in D1 (from `chart_facts`)

After resolving the 7th lord from §1.1 (e.g. `Venus`), look up that graha's dignity in D1.

```
table:        chart_facts
fact_category: graha_dignity_per_varga
fact_subject:  D1_VEN          -- '{varga}_{PLANET_TO_SUBJECT_CODE}'
fact_key:      dignity_state
fact_value_text: 'exalted' | 'own' | 'debilitated' | 'neutral'
fact_value_jsonb: { "varga": "D1", "sign": "<sign>", "house": <house>, "ayanamsha_id": "..." }
```

Planet subject codes (from `brahmagyan/graha_vocabulary.py`, `PLANET_TO_SUBJECT`):
- Venus  → `VEN`
- Saturn → `SAT`
- Mars   → `MAR`
- Jupiter → `JUP`
- Mercury → `MER`
- Sun    → `SUN`
- Moon   → `MOON`

Query pattern (for Venus as 7th lord):
```sql
SELECT fact_id, fact_value_text AS dignity, fact_value_jsonb
FROM chart_facts
WHERE chart_id = $1
  AND ayanamsha_id = $2
  AND fact_category = 'graha_dignity_per_varga'
  AND fact_subject = 'D1_VEN'
  AND fact_key = 'dignity_state'
LIMIT 1
```

Source: `ga_writers/ga_structural_writer.py`, lines 4881-4897 (`_build_dignity_per_varga` block).
`fact_subject` is always `{varga_prefix}{PLANET_TO_SUBJECT}` where `varga_prefix = f"{varga}_"`.

### 1.4 — 7th Lord Dignity in D9 (Navamsha — marriage varga)

Same as §1.3 but with `D9` prefix:

```sql
SELECT fact_id, fact_value_text AS dignity, fact_value_jsonb
FROM chart_facts
WHERE chart_id = $1
  AND ayanamsha_id = $2
  AND fact_category = 'graha_dignity_per_varga'
  AND fact_subject = 'D9_VEN'    -- replace VEN with the resolved 7th lord code
  AND fact_key = 'dignity_state'
LIMIT 1
```

### 1.5 — Venus Dignity in D1 and D9 (7th Kāraka — always Venus)

Venus is the permanent natural kāraka for the 7th house/marriage, irrespective of which graha is
the 7th lord.

```sql
-- Venus in D1
SELECT fact_id, fact_value_text AS dignity, fact_value_jsonb
FROM chart_facts
WHERE chart_id = $1
  AND ayanamsha_id = $2
  AND fact_category = 'graha_dignity_per_varga'
  AND fact_subject = 'D1_VEN'
  AND fact_key = 'dignity_state'
LIMIT 1

-- Venus in D9
SELECT fact_id, fact_value_text AS dignity, fact_value_jsonb
FROM chart_facts
WHERE chart_id = $1
  AND ayanamsha_id = $2
  AND fact_category = 'graha_dignity_per_varga'
  AND fact_subject = 'D9_VEN'
  AND fact_key = 'dignity_state'
LIMIT 1
```

### 1.6 — Saturn Dignity in D1 (7th Occupant for the native)

Saturn is in the 7th house for this chart (exalted in Libra). Always query Saturn as a fixed
occupant regardless of the lord result:

```sql
SELECT fact_id, fact_value_text AS dignity, fact_value_jsonb
FROM chart_facts
WHERE chart_id = $1
  AND ayanamsha_id = $2
  AND fact_category = 'graha_dignity_per_varga'
  AND fact_subject = 'D1_SAT'
  AND fact_key = 'dignity_state'
LIMIT 1
```

Expected result for the canonical chart (`482012f1-...`, lahiri_chitrapaksha):
`fact_value_text = 'exalted'`, `fact_value_jsonb->>'sign' = 'Libra'`.
This is the exit-test assertion for A-16.

---

## §2 — Query Pattern for assess_marriage Handler

The join should be added as a new `fetchMarriage7thNatal` async function in
`register_d8_assess_domain.ts`, following the same pattern as `fetchVargaDignity` (lines 165-195
of that file).

```typescript
interface Marriage7thNatalRow {
  lord_d1: string | null            // 7th lord name from chart_divisionals (e.g. 'Venus')
  lord_d1_fact_id: string | null
  lord_dignity_d1: string | null    // 7th lord's dignity in D1
  lord_dignity_d1_fact_id: string | null
  lord_dignity_d9: string | null    // 7th lord's dignity in D9 (navamsha)
  lord_dignity_d9_fact_id: string | null
  venus_dignity_d1: string | null   // Venus karaka dignity in D1
  venus_dignity_d1_fact_id: string | null
  venus_dignity_d9: string | null   // Venus karaka dignity in D9
  venus_dignity_d9_fact_id: string | null
  saturn_in_7th_d1: boolean         // whether Saturn occupies the 7th in D1
  saturn_dignity_d1: string | null  // Saturn dignity in D1 (present when saturn_in_7th_d1)
  saturn_dignity_d1_fact_id: string | null
  occupants_d1: Array<{ graha: string; fact_id: string }> // all D1 7th-house occupants
}

async function fetchMarriage7thNatal(
  chart_id: string,
  ayanamsha_id: string,
): Promise<{ data: Marriage7thNatalRow; fact_ids: string[] }> {
  // Step 1: resolve 7th lord from chart_divisionals
  const lordRow = await query<{ fact_id: string; graha: string }>(
    `SELECT fact_id, graha
     FROM chart_divisionals
     WHERE chart_id = $1 AND ayanamsha_id = $2
       AND fact_category = 'varga_house_lord'
       AND fact_subject = 'D1.H7' AND fact_key = 'lord'
     LIMIT 1`,
    [chart_id, ayanamsha_id],
  )
  const lord = lordRow.rows[0]?.graha ?? null
  const lordFactId = lordRow.rows[0]?.fact_id ?? null

  // Step 2: 7th-house occupants in D1
  const occupantRows = await query<{ fact_id: string; graha: string }>(
    `SELECT fact_id, graha
     FROM chart_divisionals
     WHERE chart_id = $1 AND ayanamsha_id = $2
       AND fact_category = 'varga_house_occupant'
       AND fact_value_num = 7.0
       AND fact_subject LIKE 'D1.%'`,
    [chart_id, ayanamsha_id],
  )
  const occupants = occupantRows.rows.map(r => ({ graha: r.graha, fact_id: r.fact_id }))
  const saturnIn7th = occupants.some(o => o.graha === 'Saturn')

  // Step 3: dignity lookups from chart_facts — lord in D1+D9, Venus in D1+D9, Saturn in D1
  // Resolve PLANET_TO_SUBJECT code for the lord (same mapping as graha_vocabulary.py)
  const GRAHA_TO_SUBJECT: Record<string, string> = {
    'Sun': 'SUN', 'Moon': 'MOON', 'Mars': 'MAR', 'Mercury': 'MER',
    'Jupiter': 'JUP', 'Venus': 'VEN', 'Saturn': 'SAT',
    'Rahu': 'RAH_MEAN', 'Ketu': 'KET_MEAN',
  }
  const lordSubj = lord ? (GRAHA_TO_SUBJECT[lord] ?? lord.toUpperCase()) : null

  const dignityKeys = [
    lordSubj ? `D1_${lordSubj}` : null,
    lordSubj ? `D9_${lordSubj}` : null,
    'D1_VEN', 'D9_VEN',
    'D1_SAT',
  ].filter(Boolean) as string[]

  const dignityRes = await query<{
    fact_id: string; fact_subject: string; fact_value_text: string | null
  }>(
    `SELECT fact_id, fact_subject, fact_value_text
     FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2
       AND fact_category = 'graha_dignity_per_varga'
       AND fact_key = 'dignity_state'
       AND fact_subject = ANY($3)`,
    [chart_id, ayanamsha_id, dignityKeys],
  )
  const bySubj: Record<string, { dignity: string | null; fact_id: string }> = {}
  for (const r of dignityRes.rows) {
    bySubj[r.fact_subject] = { dignity: r.fact_value_text, fact_id: r.fact_id }
  }

  const fact_ids: string[] = [
    lordFactId,
    ...occupants.map(o => o.fact_id),
    ...Object.values(bySubj).map(v => v.fact_id),
  ].filter(Boolean) as string[]

  return {
    data: {
      lord_d1: lord,
      lord_d1_fact_id: lordFactId,
      lord_dignity_d1:        lordSubj ? (bySubj[`D1_${lordSubj}`]?.dignity ?? null) : null,
      lord_dignity_d1_fact_id: lordSubj ? (bySubj[`D1_${lordSubj}`]?.fact_id ?? null) : null,
      lord_dignity_d9:        lordSubj ? (bySubj[`D9_${lordSubj}`]?.dignity ?? null) : null,
      lord_dignity_d9_fact_id: lordSubj ? (bySubj[`D9_${lordSubj}`]?.fact_id ?? null) : null,
      venus_dignity_d1:       bySubj['D1_VEN']?.dignity ?? null,
      venus_dignity_d1_fact_id: bySubj['D1_VEN']?.fact_id ?? null,
      venus_dignity_d9:       bySubj['D9_VEN']?.dignity ?? null,
      venus_dignity_d9_fact_id: bySubj['D9_VEN']?.fact_id ?? null,
      saturn_in_7th_d1: saturnIn7th,
      saturn_dignity_d1: bySubj['D1_SAT']?.dignity ?? null,
      saturn_dignity_d1_fact_id: bySubj['D1_SAT']?.fact_id ?? null,
      occupants_d1: occupants,
    },
    fact_ids: Array.from(new Set(fact_ids)),
  }
}
```

---

## §3 — Response Field Names

The result of `fetchMarriage7thNatal` is surfaced in the `assess_marriage` response under a new
top-level key `natal_7th_join`:

```json
{
  "natal_7th_join": {
    "lord_d1": "Venus",
    "lord_d1_fact_id": "<uuid>",
    "lord_dignity_d1": "neutral",
    "lord_dignity_d1_fact_id": "<uuid>",
    "lord_dignity_d9": "...",
    "lord_dignity_d9_fact_id": "<uuid>",
    "venus_dignity_d1": "neutral",
    "venus_dignity_d1_fact_id": "<uuid>",
    "venus_dignity_d9": "...",
    "venus_dignity_d9_fact_id": "<uuid>",
    "saturn_in_7th_d1": true,
    "saturn_dignity_d1": "exalted",
    "saturn_dignity_d1_fact_id": "<uuid>",
    "occupants_d1": [
      { "graha": "Saturn", "fact_id": "<uuid>" }
    ],
    "fact_ids": ["<uuid>", "<uuid>", "..."],
    "note": "Direct natal D1 7th-house join: 7th lord identity + dignity (D1/D9) + Venus karaka (D1/D9) + Saturn occupant dignity — all from L1 chart_divisionals / chart_facts. No recomputation (§N.5)."
  }
}
```

The `natal_7th_join` block is non-fatal: if the query fails, return:
```json
{ "natal_7th_join": { "available": false, "error": "<message>", "fact_ids": [] } }
```

Add `natal_7th_join.fact_ids` to the main `fact_ids` accumulator so the response's grounding
set covers these rows.

Add a checklist unit in `reading_checklist_units` (in `register_d8_assess_domain.ts`) for the
`relationship` domain:
```typescript
{ unit: 'natal_7th_lord_join', state: data ? 'served' : 'not_computed',
  detail: 'Direct D1 7th lord + Venus karaka + D9 dignity (natal_7th_join)' }
```

---

## §4 — Exit Test for A-16

The exit test assertion (to be added to the integration test or smoke gate) is:

```
ASSERTION: assess_marriage response for chart_id=482012f1-710e-4a25-994a-93821f5871aa
           (ayanamsha_id=lahiri_chitrapaksha) MUST contain:

  natal_7th_join.saturn_in_7th_d1  === true
  natal_7th_join.saturn_dignity_d1 === "exalted"
  natal_7th_join.lord_d1           === "Venus"
  natal_7th_join.fact_ids.length   > 0

FORENSIC GROUNDING: The 7 FORENSIC birth anchors place Lagna=Aries (all ayanamshas).
Aries lagna → 7H = Libra → 7th lord = Venus. Saturn is exalted in Libra and occupies
the 7th house. These are L1 chart_facts/chart_divisionals values; if the assertion fails,
a real L1 data problem exists — do NOT patch the test.
```

---

## §5 — Integration Points in register_d8_assess_domain.ts

1. Add `fetchMarriage7thNatal` function (§2 above) alongside `fetchVargaDignity`.
2. Call it only when `domain === 'relationship'` (inside `runAssessDomain`, before the return):
   ```typescript
   const natal7th = domain === 'relationship'
     ? await fetchMarriage7thNatal(chart_id, ayanamsha_id).catch(e => ({ data: null, fact_ids: [], error: String(e) }))
     : null
   ```
3. Add `natal_7th_join` to the returned `content` object (§3 above).
4. Union `natal7th.fact_ids` into the main fact_ids set if it exists.
5. Add the `natal_7th_lord_join` checklist unit (§3 above) to `reading_checklist_units`.

---

## §6 — Source Verification Notes (for A-16 engineer)

These fact_key patterns were verified by reading the actual writer source, not inferred:

| Fact | Table | fact_category | fact_subject pattern | fact_key | fact_value field |
|---|---|---|---|---|---|
| 7th house lord identity | chart_divisionals | `varga_house_lord` | `D1.H7` | `lord` | `fact_value_text` |
| 7th house occupants | chart_divisionals | `varga_house_occupant` | `D1.%` | `house` | `fact_value_num = 7.0` |
| Graha dignity per varga | chart_facts | `graha_dignity_per_varga` | `{varga}_{SUBJECT}` | `dignity_state` | `fact_value_text` |

Subject codes: `SUN MOON MAR MER JUP VEN SAT RAH_MEAN KET_MEAN`
(source: `brahmagyan/graha_vocabulary.py` `norm_graha()`)

The `graha_dignity_per_varga` rows live in `chart_facts`, NOT in `chart_divisionals`.
`chart_divisionals` has `varga_dignity` (a parallel dignity table in the divisionals schema),
but `chart_facts` / `graha_dignity_per_varga` is what `fetchVargaDignity` already uses and what
A-16 must also use for the 7th-lord query. Both tables have a `fact_id` field for §N.5 grounding.
