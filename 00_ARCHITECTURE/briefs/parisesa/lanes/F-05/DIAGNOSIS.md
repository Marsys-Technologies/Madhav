---
lane: F-05
stream: S5 MŪLA
class: CL-02 dead-backend
status: CONFIRMED-LIVE
---

# F-05 DIAGNOSIS — `ref_tantric_remedies_get` always empty (dead-backend, CL-02)

## 1. Live reproduction

Live-called `mcp__marsys-jis-direct__ref_tantric_remedies_get` twice (2026-08-16):
`{}` and `{planet: "Saturn"}`. Both returned `returned_count: 0`, `remedies: []`, with an
honest `empty_reason` string (`"No tantric-category remedies matched (deity=any, planet=…)."`).
Raw JSON saved to `lanes/F-05/repro_raw.json`. **Not fixed** — claim reproduces live.

DB side (tantric absent from `brahma_remedy_corpus.remedy_type` GROUP BY: ayurvedic 1,
behavioral 9, charity 67, gemstone 22, homa 10, japa 24, mantra 67, puja 76, vrata 33,
yantra 23 — tantric absent) already confirmed by `CL02_CENSUS.md` F-05 row; not re-run.

## 2. Claim decomposition

- **(a) Query logic correct.** `register_d7_channel.ts` `queryTantricRemediesCapability`
  (definition starts line 1670, handler line 1712, `WHERE` clause line 1721) matches
  `(LOWER(remedy_type) = 'tantric' OR LOWER(category) = 'tantric')` against
  `brahma_remedy_corpus` — case-insensitive on both plausible columns, plus optional
  `deity ILIKE` / `planet` filters, and an honest `empty_reason` on zero rows. This is not
  a query bug; the query does exactly what it should against the table it's given.
- **(b) `tantric.yaml` exists as content.** Confirmed at
  `platform/python-sidecar/brahmagyan/remedy_corpus/tantric.yaml`.
- **(c) Only loaded by a zero-caller function.** `load_remedies()` is defined in
  `platform/python-sidecar/brahmagyan/l0_remedy_loader.py:221`. Repo-wide grep for
  `load_remedies` (`.py`/`.ts`/`.sh`/`.md`) finds exactly two live hits, both inside
  `l0_remedy_loader.py` itself (its own `def` and its own `__main__` block calling itself),
  plus one mention in an ARCHIVED brief
  (`99_ARCHIVE/BRIEFS_RETIRED/CLAUDECODE_BRIEF_L0FR_STREAM_F_v1_0.md`). **Zero production
  callers.**
- **(d) Registered writer never emits `'tantric'` despite declaring it valid.** The string
  `tantric` appears exactly once in `l0_remedy_corpus.py` — line 51, inside the
  `VALID_REMEDY_TYPES` set declaration. None of the file's row-generating functions
  (`gen_planet_matrix()`, `DOSHA_REMEDIES`, `_gen_nakshatra_mantra_rows()`,
  `gen_expansion_remedies()`, `sweep_classical_text_chunks()`, `build_all_remedies()`)
  produce a `tantric`-typed row. The orchestrator-registered writer
  `platform/python-sidecar/pipeline/orchestrator/writers/bg_remedies.py`
  (`@register('bg_remedies')`) imports and calls `build_all_remedies()` /
  `seed_remedy_corpus()` from `l0_remedy_corpus.py` — never touches
  `l0_remedy_loader.py` or the YAML directory at all. All four sub-claims confirmed.

## 3. Mechanism, file:line

- `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1670` — capability def;
  `:1712` handler start; `:1721` the `WHERE` conditions array (query logic, correct).
- `platform/python-sidecar/brahmagyan/l0_remedy_loader.py:221` — `load_remedies()`, zero
  production callers (confirmed by grep, not just corpus claim).
- `platform/python-sidecar/brahmagyan/l0_remedy_corpus.py:49-52` — `VALID_REMEDY_TYPES`
  declares `"tantric"`; no downstream function ever emits it.
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_remedies.py:21,34,47` — the
  actual registered `bg_remedies` writer, delegating solely to `l0_remedy_corpus.py`.

## 4. Sibling census — is tantric.yaml uniquely orphaned?

**No — broader than the corpus claim implied. ALL 12 YAML files in `remedy_corpus/` are
orphaned**, not just `tantric.yaml`:

```
ayurvedic.yaml  behavioral.yaml  charity.yaml  gemstones.yaml  mantras.yaml
puja.yaml       supplemental.yaml  supplemental_b.yaml  supplemental_c.yaml
tantric.yaml    vastu.yaml       vrata.yaml       yantras.yaml
```

Repo-wide grep for the `remedy_corpus/` YAML directory path (`Path(__file__).parent /
'remedy_corpus'`, `yaml_dir.glob('*.yaml')`) finds it referenced **only** inside
`l0_remedy_loader.py` — the same dead `load_remedies()` path. The registered production
writer `bg_remedies.py` never opens this directory; its three data buckets (108 matrix rows,
102 dosha-linked rows, 54 legacy rows) are 100% hardcoded Python literals in
`l0_remedy_corpus.py`, not YAML-sourced.

**Fix-shape implication:** this is not "wire one orphaned file into an otherwise-live
ingestion path" — the entire YAML-loader path (`l0_remedy_loader.py` + all 12 corpus YAMLs)
is disconnected from production. The narrower fix (wire `tantric.yaml` alone) is still valid
for closing F-05 specifically, but a full YAML-loader revival would also surface 11 sibling
content files currently contributing zero rows to `brahma_remedy_corpus`. Flagging this as
a scope decision for the S-stage spec, not resolving it here.

## 5. Blast radius — governance gate

`remedy_review_queue` is a real table (`platform/supabase/migrations/081_l0fr_schema.sql`,
"review queue for tantric/uncertain remedies"). `l0_remedy_loader.py::insert_to_review_queue()`
is the only writer to it — tantric rows whose `source_text` fails
`is_acceptable_tantric_source()` (an allow-listed classical-source pattern: Mantra
Mahodadhi, Tantrasāra, Śaktisaṅgama Tantra, BPHS, Phaladeepika, etc.) or are missing
`REQUIRED_TANTRIC_COLUMNS` (`source_text`, `source_chapter`, `source_verse`,
`classical_attestation_text`) get queued for review instead of inserted directly.

**Dependency for the fix:** wiring `tantric.yaml` (or the full YAML loader) into the
production seeding pipeline is not a pure data change — any row that fails the
Phase-3 tantric careful-inclusion gate must land in `remedy_review_queue` and go through
whatever human review workflow exists for that table before it reaches
`brahma_remedy_corpus`. The fix must preserve this gate, not bypass it by inserting
`tantric.yaml` rows directly.
