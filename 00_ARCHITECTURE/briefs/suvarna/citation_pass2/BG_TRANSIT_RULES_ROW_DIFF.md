# bg_transit_rules: row diff for Citation Pass 2 (decision OS-2026-10-05-CITATIONS), form (b)

Natural key: (graha, rule_type, primary_house). Seed: `platform/python-sidecar/brahmagyan/l0_transit.py` (`BG_TRANSIT_RULES`, 69 writer-owned rows; the table also holds 7 migration-owned `double_transit` rows, untouched).

| | before | after |
|---|---|---|
| writer-owned seed rows | 69 | 69 |
| table rows (with 7 migration-owned) | 76 | 76 |
| added | | 0 |
| removed | | 0 |
| changed | | 6 |

Changed columns: `classical_citation` and `rule_notes` only. `rule_type`, `primary_house`, `vedha_house`, `phala`, `graha` and the row `id` are unchanged on all six rows, and the three Rahu + three Ketu rows still carry a vedha house (3->9, 6->12, 11->5).

**Form (b), ruled by SS via Pravaha.** The citation still STARTS with `UNSOURCED` (for the vedha partner) and then carries the K1 transit result (verse, machine locus, excerpt). The vedha loader (`services/gochara_rules/vedha_derive.py::pairs_from_rows`) accepts it: tested on the rebuilt table (36 classical pairs + 3 Rahu + 3 Ketu node rows, census 42, the same pair mapping as before). The citation text sits INSIDE the loader's `pairs_content_digest`, which is the L0 binding of the AM-16 input vector (`services/gochara_kernel/input_vector.py:74`): that digest changes when the rebuild runs. `ka_vedha_gochara` derives its stamps from the `UNSOURCED` prefix, so the six rows stay `unsourced`. The census reads the split text through a declared `split_citation` (branch `suvarna/engine-ldgr-split-citation`): the transit result must resolve to a corpus chunk, any other UNSOURCED text stays a placeholder.

## Changed rows

### ketu / favourable / house 3 (vedha_house 9)
- **classical_citation** before: `UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-PG323:C1, name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus). Retained per B.10 (writers emit, serve-time governs; never silently dropped) and Gochara N-14 (no graha-drishti cast from the nodes) — see KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.5.`
- **classical_citation** after: `UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG321:C1] "Sun ... in the 6th, 3rd and 10th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (3) happiness"`
- **rule_notes** before: `Ketu 3rd from Moon — paurushabala enterprise; less potent than Rahu here. L0 repair item 3: vedha_house retained, disposition unsourced (never a claimed-cited nullification).`
- **rule_notes** after: `Ketu 3rd from Moon — paurushabala enterprise; less potent than Rahu here. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.`

### ketu / favourable / house 6 (vedha_house 12)
- **classical_citation** before: `UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-PG323:C1, name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus). Retained per B.10 (writers emit, serve-time governs; never silently dropped) and Gochara N-14 (no graha-drishti cast from the nodes) — see KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.5.`
- **classical_citation** after: `UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG321:C1] "Sun ... in the 6th, 3rd and 10th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (6) happiness"`
- **rule_notes** before: `Ketu 6th from Moon — moksha-karak in ari-bhava aids liberation from obstacles. L0 repair item 3: vedha_house retained, disposition unsourced (never a claimed-cited nullification).`
- **rule_notes** after: `Ketu 6th from Moon — moksha-karak in ari-bhava aids liberation from obstacles. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.`

### ketu / favourable / house 11 (vedha_house 5)
- **classical_citation** before: `UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-PG323:C1, name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus). Retained per B.10 (writers emit, serve-time governs; never silently dropped) and Gochara N-14 (no graha-drishti cast from the nodes) — see KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.5.`
- **classical_citation** after: `UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG321:C1] "all planets in the 11th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (11) happiness"`
- **rule_notes** before: `Ketu 11th from Moon — gains oriented toward karmic fulfilment. L0 repair item 3: vedha_house retained, disposition unsourced (never a claimed-cited nullification).`
- **rule_notes** after: `Ketu 11th from Moon — gains oriented toward karmic fulfilment. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.`

### rahu / favourable / house 3 (vedha_house 9)
- **classical_citation** before: `UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-PG323:C1, name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus). Retained per B.10 (writers emit, serve-time governs; never silently dropped) and Gochara N-14 (no graha-drishti cast from the nodes) — see KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.5.`
- **classical_citation** after: `UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG331:C1] "Sun ... in the 6th, 3rd and 10th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (3) happiness"`
- **rule_notes** before: `Rahu 3rd from Moon — gain and initiative. L0 repair item 3: vedha_house retained, disposition unsourced (never a claimed-cited nullification).`
- **rule_notes** after: `Rahu 3rd from Moon — gain and initiative. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.`

### rahu / favourable / house 6 (vedha_house 12)
- **classical_citation** before: `UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-PG323:C1, name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus). Retained per B.10 (writers emit, serve-time governs; never silently dropped) and Gochara N-14 (no graha-drishti cast from the nodes) — see KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.5.`
- **classical_citation** after: `UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG331:C1] "Sun ... in the 6th, 3rd and 10th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (6) happiness"`
- **rule_notes** before: `Rahu 6th from Moon — ari-bhava placement aids in enemy removal. L0 repair item 3: vedha_house retained, disposition unsourced (never a claimed-cited nullification).`
- **rule_notes** after: `Rahu 6th from Moon — ari-bhava placement aids in enemy removal. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.`

### rahu / favourable / house 11 (vedha_house 5)
- **classical_citation** before: `UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-PG323:C1, name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus). Retained per B.10 (writers emit, serve-time governs; never silently dropped) and Gochara N-14 (no graha-drishti cast from the nodes) — see KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.5.`
- **classical_citation** after: `UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG331:C1] "all planets in the 11th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (11) happiness"`
- **rule_notes** before: `Rahu 11th from Moon — labha amplified; shadow planet in gain house. L0 repair item 3: vedha_house retained, disposition unsourced (never a claimed-cited nullification).`
- **rule_notes** after: `Rahu 11th from Moon — labha amplified; shadow planet in gain house. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.`
